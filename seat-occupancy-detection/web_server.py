"""
Web server for seat occupancy detection system
Provides web interface with real-time video streaming and statistics

Usage: python3 web_server.py [--auto-calibrate]
Then open http://localhost:5000 in your browser
"""

from flask import Flask, render_template, Response, jsonify, request
from flask_cors import CORS
import cv2
import torch
import numpy as np
import time
from datetime import datetime
import os
import argparse
import json
from threading import Thread, Lock
import queue

import config
import seat_utils as utils
from seat_mapper import SeatMapper, ChairMapper
from auto_calibrator import AutoCalibrator


app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'seat-occupancy-detection-2025'

# Global detector instance
detector = None
detector_lock = Lock()

# SSE queue for real-time updates
sse_queues = []
sse_lock = Lock()


class WebSeatOccupancyDetector:
    """Web-enabled seat occupancy detector"""
    
    def __init__(self, auto_calibrate: bool = False):
        """Initialize the detector"""
        print("=" * 60)
        print("WEB SEAT OCCUPANCY DETECTION SYSTEM")
        print("=" * 60)

        # Load seat zones
        print("\nLoading seat zones...")
        self.seat_zones = utils.load_zones('seat_zones.json')

        if not self.seat_zones:
            if auto_calibrate:
                print("⚠ No seat zones found. Running auto-calibration...")
                self.seat_zones = self._run_auto_calibration()
                if not self.seat_zones:
                    raise ValueError("Auto-calibration failed")
            else:
                print("⚠ Warning: No seat zones found!")
                print("You can run calibration from the web interface or use --auto-calibrate")
                self.seat_zones = {}

        if self.seat_zones:
            print(f"✓ Loaded {len(self.seat_zones)} seat zones")

        # Initialize seat mapper
        self.seat_mapper = SeatMapper(self.seat_zones, config.MIN_OVERLAP_RATIO) if self.seat_zones else None

        # Initialize chair mapper if chair detection is enabled
        self.chair_mapper = None
        if config.ENABLE_CHAIR_DETECTION and self.seat_zones:
            self.chair_mapper = ChairMapper(self.seat_zones, min_overlap=0.5)
            print("✓ Chair detection enabled")

        # Load YOLOv5 model
        print(f"\nLoading YOLOv5 model ({config.MODEL_NAME})...")
        try:
            self.model = torch.hub.load('ultralytics/yolov5', config.MODEL_NAME, pretrained=True)
            self.model.conf = config.CONFIDENCE_THRESHOLD
            self.model.iou = config.IOU_THRESHOLD

            # Detect persons and optionally chairs
            if config.ENABLE_CHAIR_DETECTION:
                self.model.classes = [0, 56]  # Detect persons (0) and chairs (56)
            else:
                self.model.classes = [0]  # Only detect persons

            self.device = config.DEVICE if torch.cuda.is_available() else 'cpu'
            self.model.to(self.device)
            print(f"✓ Model loaded successfully on {self.device.upper()}")
        except Exception as e:
            print(f"✗ Error loading model: {e}")
            raise

        # Initialize webcam
        print("\nInitializing webcam...")
        self.cap = cv2.VideoCapture(config.WEBCAM_ID)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

        if not self.cap.isOpened():
            print("✗ Error: Could not open webcam")
            raise ValueError("Webcam not available")

        print("✓ Webcam initialized")

        # Video writer for recording
        self.video_writer = None
        self.is_recording = False

        # FPS calculation
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()

        # Latest frame and stats
        self.latest_frame = None
        self.latest_stats = {
            'occupied_count': 0,
            'total_seats': len(self.seat_zones),
            'occupancy_rate': 0.0,
            'persons_detected': 0,
            'occupied_seats': [],
            'empty_seats': [name for name in self.seat_zones],
            'fps': 0.0,
            'recording': False,
            'seats': {},
            'chairs_detected': 0,
            'chairs_aligned': 0
        }
        self.frame_lock = Lock()

        # Running flag
        self.running = False

        print("\n" + "=" * 60)
        print("Web server ready! Open http://localhost:5000")
        print("=" * 60 + "\n")

    def _run_auto_calibration(self):
        """Run automatic chair detection"""
        calibrator = AutoCalibrator(
            confidence_threshold=config.AUTO_CALIB_CONFIDENCE,
            num_frames=config.AUTO_CALIB_FRAMES,
            stability_threshold=config.AUTO_CALIB_STABILITY
        )

        seat_zones = calibrator.auto_calibrate(self.cap, visualize=False)

        if seat_zones:
            utils.save_zones(seat_zones, 'seat_zones.json')
            print(f"\n✓ Auto-calibration complete! Saved {len(seat_zones)} seat zones")
        else:
            print("\n✗ Auto-calibration failed to detect any chairs")

        return seat_zones

    def detect_objects(self, frame):
        """Detect persons and chairs in the frame"""
        results = self.model(frame)
        persons = []
        chairs = []
        for *box, conf, cls in results.xyxy[0].cpu().numpy():
            if int(cls) == 0:  # Person class
                persons.append((*box, conf))
            elif int(cls) == 56:  # Chair class
                chair_threshold = config.CHAIR_CONFIDENCE_THRESHOLD if config.ENABLE_CHAIR_DETECTION else config.CONFIDENCE_THRESHOLD
                if conf >= chair_threshold:
                    chairs.append((*box, conf))
        return persons, chairs

    def draw_detections(self, frame, detections):
        """Draw bounding boxes for detected persons"""
        for det in detections:
            x1, y1, x2, y2, conf = det
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            cv2.rectangle(frame, (x1, y1), (x2, y2), config.COLOR_BBOX, 2)
            label = f"Person {conf:.2f}"
            utils.draw_text_with_background(frame, label, (x1, y1 - 10),
                                             font_scale=0.5, thickness=1)

    def draw_chairs(self, frame, chairs):
        """Draw bounding boxes for detected chairs"""
        for det in chairs:
            x1, y1, x2, y2, conf = det
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            cv2.rectangle(frame, (x1, y1), (x2, y2), config.COLOR_CHAIR, 2)
            label = f"Chair {conf:.2f}"
            utils.draw_text_with_background(frame, label, (x1, y1 - 10),
                                             font_scale=0.5, thickness=1,
                                             bg_color=config.COLOR_CHAIR)

    def draw_seat_zones(self, frame):
        """Draw seat zones with occupancy status"""
        if not self.seat_mapper:
            return

        for seat_name, zone_points in self.seat_zones.items():
            is_occupied = self.seat_mapper.is_seat_occupied(seat_name)
            color = config.COLOR_OCCUPIED if is_occupied else config.COLOR_EMPTY
            status = "OCCUPIED" if is_occupied else "EMPTY"

            utils.fill_polygon(frame, zone_points, color, alpha=0.2)
            utils.draw_polygon(frame, zone_points, color, thickness=3)

            center_x = int(np.mean([p[0] for p in zone_points]))
            center_y = int(np.mean([p[1] for p in zone_points]))

            utils.draw_text_with_background(frame, seat_name.upper(),
                                             (center_x - 40, center_y - 10),
                                             font_scale=0.6, thickness=2)
            utils.draw_text_with_background(frame, status,
                                             (center_x - 30, center_y + 15),
                                             font_scale=0.5, thickness=1,
                                             text_color=color)

    def draw_statistics(self, frame):
        """Draw statistics panel on the frame"""
        if not self.seat_mapper:
            return

        occupied, total, rate = self.seat_mapper.get_occupancy_stats()

        panel_height = 200 if config.ENABLE_CHAIR_DETECTION else 150
        panel_width = 300
        panel = np.zeros((panel_height, panel_width, 3), dtype=np.uint8)
        panel[:] = (30, 30, 30)

        stats = [
            f"OCCUPANCY STATISTICS",
            f"",
            f"Occupied: {occupied}/{total}",
            f"Rate: {rate:.1f}%",
            f"Empty: {total - occupied}",
            f"FPS: {self.fps:.1f}"
        ]

        # Add chair statistics if enabled
        if config.ENABLE_CHAIR_DETECTION and self.chair_mapper:
            total_chairs, aligned, misaligned = self.chair_mapper.get_chair_statistics()
            stats.extend([
                f"",
                f"Chairs: {total_chairs}",
                f"Aligned: {aligned}/{len(self.seat_zones)}"
            ])

        y_offset = 25
        for i, stat in enumerate(stats):
            font_scale = 0.7 if i == 0 else 0.6
            thickness = 2 if i == 0 else 1
            color = (0, 255, 255) if i == 0 else (255, 255, 255)

            cv2.putText(panel, stat, (10, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)
            y_offset += 25 if i == 0 else 22

        x_pos = frame.shape[1] - panel_width - 10
        y_pos = 10
        roi = frame[y_pos:y_pos + panel_height, x_pos:x_pos + panel_width]
        blended = cv2.addWeighted(roi, 0.3, panel, 0.7, 0)
        frame[y_pos:y_pos + panel_height, x_pos:x_pos + panel_width] = blended

        if self.is_recording:
            cv2.circle(frame, (30, 30), 10, (0, 0, 255), -1)
            cv2.putText(frame, "REC", (50, 38),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # Draw recalibration warning if needed
        if config.ENABLE_CHAIR_DETECTION and self.chair_mapper and self.chair_mapper.needs_recalibration():
            warning_text = "! RECALIBRATION SUGGESTED"
            cv2.putText(frame, warning_text, (10, frame.shape[0] - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

    def calculate_fps(self):
        """Calculate current FPS"""
        self.frame_count += 1
        elapsed = time.time() - self.start_time

        if elapsed > 1.0:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.start_time = time.time()

    def start_recording(self, frame):
        """Start video recording"""
        if not self.is_recording:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            os.makedirs(config.OUTPUT_DIR, exist_ok=True)
            output_path = os.path.join(config.OUTPUT_DIR, f"recording_{timestamp}.mp4")

            fourcc = cv2.VideoWriter_fourcc(*config.VIDEO_CODEC)
            self.video_writer = cv2.VideoWriter(
                output_path, fourcc, config.FPS,
                (frame.shape[1], frame.shape[0])
            )
            self.is_recording = True
            print(f"✓ Recording started: {output_path}")
            return output_path

    def stop_recording(self):
        """Stop video recording"""
        if self.is_recording and self.video_writer:
            self.video_writer.release()
            self.is_recording = False
            print("✓ Recording stopped")

    def process_frame(self):
        """Process a single frame"""
        ret, frame = self.cap.read()
        if not ret:
            return None

        # Detect objects (persons and chairs)
        persons, chairs = self.detect_objects(frame)

        # Update occupancy with person detections
        if self.seat_mapper:
            self.seat_mapper.update_occupancy(persons)

            # Update chair positions if chair detection is enabled
            if config.ENABLE_CHAIR_DETECTION and self.chair_mapper:
                self.chair_mapper.update_chair_positions(chairs)

            # Get stats
            occupied, total, rate = self.seat_mapper.get_occupancy_stats()

            # Build seat details
            seats_detail = {}
            for seat_name in self.seat_zones:
                is_occupied = self.seat_mapper.is_seat_occupied(seat_name)
                seats_detail[seat_name] = 'occupied' if is_occupied else 'empty'

            occupied_seats = [name for name, status in seats_detail.items() if status == 'occupied']
            empty_seats = [name for name, status in seats_detail.items() if status == 'empty']

            self.latest_stats = {
                'occupied_count': occupied,
                'total_seats': total,
                'occupancy_rate': round(rate, 1),
                'persons_detected': len(persons),
                'occupied_seats': occupied_seats,
                'empty_seats': empty_seats,
                'fps': round(self.fps, 1),
                'recording': self.is_recording,
                'seats': seats_detail # Keep for backward compatibility if needed
            }

            # Add chair statistics if enabled
            if config.ENABLE_CHAIR_DETECTION and self.chair_mapper:
                total_chairs, aligned, misaligned = self.chair_mapper.get_chair_statistics()
                self.latest_stats['chairs_detected'] = total_chairs
                self.latest_stats['chairs_aligned'] = aligned
                self.latest_stats['chairs_misaligned'] = misaligned

        # Draw visualizations
        self.draw_seat_zones(frame)

        # Draw chairs first (background layer)
        if config.ENABLE_CHAIR_DETECTION and chairs:
            self.draw_chairs(frame, chairs)

        # Draw persons on top
        self.draw_detections(frame, persons)

        # Draw statistics panel
        self.draw_statistics(frame)

        # Calculate FPS
        self.calculate_fps()

        # Record if enabled
        if self.is_recording and self.video_writer:
            self.video_writer.write(frame)

        return frame

    def generate_frames(self):
        """Generator for video streaming"""
        while self.running:
            frame = self.process_frame()
            if frame is None:
                break

            # Store latest frame
            with self.frame_lock:
                self.latest_frame = frame.copy()

            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if not ret:
                continue

            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

            # Broadcast stats via SSE
            broadcast_sse_message(json.dumps(self.latest_stats))

            time.sleep(0.01)  # Small delay to prevent overwhelming

    def start(self):
        """Start the detector"""
        self.running = True

    def stop(self):
        """Stop the detector"""
        self.running = False
        if self.is_recording:
            self.stop_recording()
        if self.cap:
            self.cap.release()

    def reload_zones(self):
        """Reload seat zones from file"""
        self.seat_zones = utils.load_zones('seat_zones.json')
        if self.seat_zones:
            self.seat_mapper = SeatMapper(self.seat_zones, config.MIN_OVERLAP_RATIO)
            self.latest_stats['total_seats'] = len(self.seat_zones)
            return True
        return False


def broadcast_sse_message(message):
    """Broadcast message to all SSE clients"""
    with sse_lock:
        dead_queues = []
        for q in sse_queues:
            try:
                q.put_nowait(message)
            except queue.Full:
                dead_queues.append(q)
        
        # Clean up dead queues
        for q in dead_queues:
            sse_queues.remove(q)


@app.route('/')
def index():
    """Redirect or serve a simple message since frontend is now Next.js"""
    return jsonify({
        "status": "online",
        "message": "Seat Occupancy Detection Backend is running",
        "frontend_url": "http://localhost:3000"
    })


@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(detector.generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/stats')
def get_stats():
    """Get current statistics"""
    with detector_lock:
        return jsonify(detector.latest_stats)


@app.route('/api/stream')
def stream():
    """Server-Sent Events stream for real-time updates"""
    def event_stream():
        q = queue.Queue(maxsize=10)
        with sse_lock:
            sse_queues.append(q)
        
        try:
            while True:
                message = q.get()
                yield f"data: {message}\n\n"
        except GeneratorExit:
            with sse_lock:
                sse_queues.remove(q)
    
    return Response(event_stream(), mimetype='text/event-stream')


@app.route('/api/recording/start', methods=['POST'])
def start_recording():
    """Start recording"""
    with detector_lock:
        if not detector.is_recording:
            frame = detector.latest_frame
            if frame is not None:
                path = detector.start_recording(frame)
                return jsonify({'success': True, 'message': 'Recording started', 'path': path})
        return jsonify({'success': False, 'message': 'Already recording'})


@app.route('/api/recording/stop', methods=['POST'])
def stop_recording():
    """Stop recording"""
    with detector_lock:
        if detector.is_recording:
            detector.stop_recording()
            return jsonify({'success': True, 'message': 'Recording stopped'})
        return jsonify({'success': False, 'message': 'Not recording'})


@app.route('/api/calibrate/reload', methods=['POST'])
def reload_calibration():
    """Reload seat zones from file"""
    with detector_lock:
        success = detector.reload_zones()
        if success:
            return jsonify({'success': True, 'message': f'Loaded {len(detector.seat_zones)} seat zones'})
        return jsonify({'success': False, 'message': 'No seat zones found'})


@app.route('/api/calibrate/auto', methods=['POST'])
def auto_calibrate():
    """Run auto-calibration"""
    with detector_lock:
        try:
            # Temporarily stop detection
            was_running = detector.running
            detector.running = False
            time.sleep(0.5)

            # Run calibration
            seat_zones = detector._run_auto_calibration()
            
            if seat_zones:
                detector.seat_zones = seat_zones
                detector.seat_mapper = SeatMapper(seat_zones, config.MIN_OVERLAP_RATIO)
                detector.latest_stats['total_seats'] = len(seat_zones)
                
                # Restart detection
                if was_running:
                    detector.running = True
                
                return jsonify({'success': True, 'message': f'Detected {len(seat_zones)} seats'})
            else:
                if was_running:
                    detector.running = True
                return jsonify({'success': False, 'message': 'No chairs detected'})
        except Exception as e:
            if was_running:
                detector.running = True
            return jsonify({'success': False, 'message': str(e)})


def main():
    """Main entry point"""
    global detector

    parser = argparse.ArgumentParser(description='Web Seat Occupancy Detection System')
    parser.add_argument('--auto-calibrate', action='store_true',
                       help='Automatically detect chairs if seat zones not found')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    args = parser.parse_args()

    try:
        # Initialize detector
        detector = WebSeatOccupancyDetector(auto_calibrate=args.auto_calibrate)
        detector.start()

        # Run Flask app
        print(f"\n🌐 Starting web server on http://{args.host}:{args.port}")
        print("   Press Ctrl+C to stop\n")
        
        app.run(host=args.host, port=args.port, debug=False, threaded=True)

    except KeyboardInterrupt:
        print("\n\nShutting down...")
    except Exception as e:
        print(f"\n✗ Error: {e}")
    finally:
        if detector:
            detector.stop()


if __name__ == "__main__":
    main()
