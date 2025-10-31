"""
Main seat occupancy detection script using YOLOv5 and webcam

Usage: python3 main.py [--auto-calibrate]
Options:
  --auto-calibrate    Run automatic chair detection if zones not found
Make sure to run calibrate.py first to define seat zones!
"""

import cv2
import torch
import numpy as np
import time
from datetime import datetime
import os
import argparse

import config
import seat_utils as utils
from seat_mapper import SeatMapper, ChairMapper
from auto_calibrator import AutoCalibrator


class SeatOccupancyDetector:
    def __init__(self, auto_calibrate: bool = False):
        """Initialize the seat occupancy detection system"""
        print("=" * 60)
        print("SEAT OCCUPANCY DETECTION SYSTEM")
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
                print("Please run 'python3 calibrate.py' first to define seat zones.")
                print("Or use 'python3 main.py --auto-calibrate' to detect chairs automatically.")
                raise ValueError("Seat zones not configured")

        print(f"✓ Loaded {len(self.seat_zones)} seat zones")

        # Initialize seat mapper
        self.seat_mapper = SeatMapper(self.seat_zones, config.MIN_OVERLAP_RATIO)

        # Initialize chair mapper if chair detection is enabled
        self.chair_mapper = None
        if config.ENABLE_CHAIR_DETECTION:
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

            # Set device
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

        # Statistics
        self.detection_history = []

        print("\n" + "=" * 60)
        print("System ready! Press 'q' to quit, 'r' to start/stop recording")
        print("=" * 60 + "\n")

    def _run_auto_calibration(self):
        """Run automatic chair detection and save zones."""
        # Open webcam temporarily for calibration
        cap = cv2.VideoCapture(config.WEBCAM_ID)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

        if not cap.isOpened():
            print("✗ Error: Could not open webcam for calibration")
            return None

        # Run auto-calibration
        calibrator = AutoCalibrator(
            confidence_threshold=config.AUTO_CALIB_CONFIDENCE,
            num_frames=config.AUTO_CALIB_FRAMES,
            stability_threshold=config.AUTO_CALIB_STABILITY
        )

        seat_zones = calibrator.auto_calibrate(cap, visualize=True)
        cap.release()

        if seat_zones:
            # Save zones
            utils.save_zones(seat_zones, 'seat_zones.json')
            print(f"\n✓ Auto-calibration complete! Saved {len(seat_zones)} seat zones")
        else:
            print("\n✗ Auto-calibration failed to detect any chairs")

        return seat_zones

    def detect_objects(self, frame):
        """
        Detect persons and chairs in the frame using YOLOv5

        Args:
            frame: Input frame

        Returns:
            Tuple of (persons, chairs) where each is a list of detections
            [(x1, y1, x2, y2, confidence), ...]
        """
        # Run inference
        results = self.model(frame)

        # Extract detections by class
        persons = []
        chairs = []
        for *box, conf, cls in results.xyxy[0].cpu().numpy():
            if int(cls) == 0:  # Person class
                persons.append((*box, conf))
            elif int(cls) == 56:  # Chair class
                # Apply separate confidence threshold for chairs if configured
                chair_threshold = config.CHAIR_CONFIDENCE_THRESHOLD if config.ENABLE_CHAIR_DETECTION else config.CONFIDENCE_THRESHOLD
                if conf >= chair_threshold:
                    chairs.append((*box, conf))

        return persons, chairs

    def draw_detections(self, frame, detections):
        """
        Draw bounding boxes for detected persons

        Args:
            frame: Frame to draw on
            detections: List of detections
        """
        for det in detections:
            x1, y1, x2, y2, conf = det
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), config.COLOR_BBOX, 2)

            # Draw confidence
            label = f"Person {conf:.2f}"
            utils.draw_text_with_background(frame, label, (x1, y1 - 10),
                                             font_scale=0.5, thickness=1)

    def draw_chairs(self, frame, chairs):
        """
        Draw bounding boxes for detected chairs

        Args:
            frame: Frame to draw on
            chairs: List of chair detections
        """
        for det in chairs:
            x1, y1, x2, y2, conf = det
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

            # Draw bounding box in orange
            cv2.rectangle(frame, (x1, y1), (x2, y2), config.COLOR_CHAIR, 2)

            # Draw confidence
            label = f"Chair {conf:.2f}"
            utils.draw_text_with_background(frame, label, (x1, y1 - 10),
                                             font_scale=0.5, thickness=1,
                                             bg_color=config.COLOR_CHAIR)

    def draw_seat_zones(self, frame):
        """
        Draw seat zones with occupancy status

        Args:
            frame: Frame to draw on
        """
        for seat_name, zone_points in self.seat_zones.items():
            is_occupied = self.seat_mapper.is_seat_occupied(seat_name)

            # Choose color based on occupancy
            color = config.COLOR_OCCUPIED if is_occupied else config.COLOR_EMPTY
            status = "OCCUPIED" if is_occupied else "EMPTY"

            # Draw filled polygon
            utils.fill_polygon(frame, zone_points, color, alpha=0.2)

            # Draw border
            utils.draw_polygon(frame, zone_points, color, thickness=3)

            # Draw seat label
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
        """
        Draw statistics panel on the frame

        Args:
            frame: Frame to draw on
        """
        occupied, total, rate = self.seat_mapper.get_occupancy_stats()

        # Create semi-transparent panel
        panel_height = 200 if config.ENABLE_CHAIR_DETECTION else 150
        panel_width = 300
        panel = np.zeros((panel_height, panel_width, 3), dtype=np.uint8)
        panel[:] = (30, 30, 30)

        # Add statistics
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

        # Overlay panel on frame
        x_pos = frame.shape[1] - panel_width - 10
        y_pos = 10
        roi = frame[y_pos:y_pos + panel_height, x_pos:x_pos + panel_width]
        blended = cv2.addWeighted(roi, 0.3, panel, 0.7, 0)
        frame[y_pos:y_pos + panel_height, x_pos:x_pos + panel_width] = blended

        # Draw recording indicator
        if self.is_recording:
            cv2.circle(frame, (30, 30), 10, (0, 0, 255), -1)
            cv2.putText(frame, "REC", (50, 38),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # Draw recalibration warning if needed
        if config.ENABLE_CHAIR_DETECTION and self.chair_mapper and self.chair_mapper.needs_recalibration():
            warning_text = "! RECALIBRATION SUGGESTED"
            cv2.putText(frame, warning_text, (10, frame.shape[0] - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

    def start_recording(self, frame):
        """Start video recording"""
        if not self.is_recording:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(config.OUTPUT_DIR, f"recording_{timestamp}.mp4")

            fourcc = cv2.VideoWriter_fourcc(*config.VIDEO_CODEC)
            self.video_writer = cv2.VideoWriter(
                output_path, fourcc, config.FPS,
                (frame.shape[1], frame.shape[0])
            )

            self.is_recording = True
            print(f"✓ Recording started: {output_path}")

    def stop_recording(self):
        """Stop video recording"""
        if self.is_recording and self.video_writer:
            self.video_writer.release()
            self.is_recording = False
            print("✓ Recording stopped")

    def calculate_fps(self):
        """Calculate current FPS"""
        self.frame_count += 1
        elapsed = time.time() - self.start_time

        if elapsed > 1.0:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.start_time = time.time()

    def run(self):
        """Main detection loop"""
        try:
            while True:
                # Read frame
                ret, frame = self.cap.read()
                if not ret:
                    print("Error: Could not read frame")
                    break

                # Detect objects (persons and chairs)
                persons, chairs = self.detect_objects(frame)

                # Update occupancy with person detections
                self.seat_mapper.update_occupancy(persons)

                # Update chair positions if chair detection is enabled
                if config.ENABLE_CHAIR_DETECTION and self.chair_mapper:
                    self.chair_mapper.update_chair_positions(chairs)

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
                if self.is_recording:
                    self.video_writer.write(frame)

                # Display frame
                cv2.imshow('Seat Occupancy Detection', frame)

                # Handle key presses
                key = cv2.waitKey(1) & 0xFF

                if key == ord('q'):
                    print("\nShutting down...")
                    break
                elif key == ord('r'):
                    if not self.is_recording:
                        self.start_recording(frame)
                    else:
                        self.stop_recording()
                elif key == ord('h'):
                    self.print_help()

        except KeyboardInterrupt:
            print("\n\nInterrupted by user")

        finally:
            self.cleanup()

    def print_help(self):
        """Print help information"""
        print("\n" + "=" * 60)
        print("KEYBOARD SHORTCUTS")
        print("=" * 60)
        print("q - Quit the application")
        print("r - Start/Stop recording")
        print("h - Show this help")
        print("=" * 60 + "\n")

    def cleanup(self):
        """Clean up resources"""
        print("\nCleaning up...")

        if self.is_recording:
            self.stop_recording()

        if self.cap:
            self.cap.release()

        cv2.destroyAllWindows()

        # Print final statistics
        occupied, total, rate = self.seat_mapper.get_occupancy_stats()
        print("\n" + "=" * 60)
        print("FINAL STATISTICS")
        print("=" * 60)
        print(f"Total Seats: {total}")
        print(f"Occupied: {occupied}")
        print(f"Empty: {total - occupied}")
        print(f"Occupancy Rate: {rate:.1f}%")
        print("=" * 60)
        print("\nThank you for using Seat Occupancy Detection System!")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Seat Occupancy Detection System')
    parser.add_argument('--auto-calibrate', action='store_true',
                       help='Automatically detect chairs if seat zones not found')
    args = parser.parse_args()

    try:
        detector = SeatOccupancyDetector(auto_calibrate=args.auto_calibrate)
        detector.run()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nPlease ensure:")
        print("1. You have run 'python3 calibrate.py' to define seat zones")
        print("   Or use 'python3 main.py --auto-calibrate' for automatic detection")
        print("2. Your webcam is connected and accessible")
        print("3. All dependencies are installed (pip install -r requirements.txt)")


if __name__ == "__main__":
    main()
