"""
Automatic Chair Detection and Seat Zone Calibration

This module provides automatic detection of chairs using YOLOv5 and generates
seat zones without manual calibration. It can be used standalone or integrated
with the interactive calibration tool for a hybrid approach.
"""

import cv2
import numpy as np
import torch
from collections import defaultdict
from typing import List, Tuple, Dict, Optional
import config


class AutoCalibrator:
    """Automatic chair detection and zone generation using YOLO."""

    # COCO dataset class ID for chair
    CHAIR_CLASS_ID = 56

    def __init__(self,
                 confidence_threshold: float = 0.4,
                 num_frames: int = 30,
                 stability_threshold: int = 15):
        """
        Initialize the auto-calibrator.

        Args:
            confidence_threshold: Minimum confidence for chair detection (0.0-1.0)
            num_frames: Number of frames to collect detections for stability
            stability_threshold: Minimum frames a chair must appear in to be considered valid
        """
        self.confidence_threshold = confidence_threshold
        self.num_frames = num_frames
        self.stability_threshold = stability_threshold

        # Load YOLOv5 model
        print("Loading YOLOv5 model for chair detection...")
        self.model = torch.hub.load('ultralytics/yolov5', config.MODEL_NAME,
                                    pretrained=True, device=config.DEVICE)
        self.model.conf = self.confidence_threshold
        print(f"Model loaded on {config.DEVICE}")

        # Storage for detections across frames
        self.chair_detections = []

    def detect_chairs_in_frame(self, frame: np.ndarray) -> List[Tuple[int, int, int, int, float]]:
        """
        Detect chairs in a single frame.

        Args:
            frame: Input image as numpy array (BGR format)

        Returns:
            List of chair detections as (x1, y1, x2, y2, confidence)
        """
        results = self.model(frame)
        chairs = []

        # Extract chair detections
        for *box, conf, cls in results.xyxy[0].cpu().numpy():
            if int(cls) == self.CHAIR_CLASS_ID and conf >= self.confidence_threshold:
                x1, y1, x2, y2 = map(int, box)
                chairs.append((x1, y1, x2, y2, float(conf)))

        return chairs

    def collect_detections(self, cap: cv2.VideoCapture,
                          callback=None) -> List[List[Tuple[int, int, int, int, float]]]:
        """
        Collect chair detections over multiple frames for stability.

        Args:
            cap: OpenCV VideoCapture object
            callback: Optional callback function(frame, chairs, frame_num) for visualization

        Returns:
            List of detections per frame
        """
        all_detections = []
        frame_count = 0

        print(f"Collecting chair detections over {self.num_frames} frames...")

        while frame_count < self.num_frames:
            ret, frame = cap.read()
            if not ret:
                print("Warning: Could not read frame from camera")
                break

            chairs = self.detect_chairs_in_frame(frame)
            all_detections.append(chairs)

            # Optional visualization callback
            if callback:
                callback(frame, chairs, frame_count)

            frame_count += 1

        print(f"Collected detections from {frame_count} frames")
        return all_detections

    def cluster_detections(self,
                          all_detections: List[List[Tuple[int, int, int, int, float]]],
                          iou_threshold: float = 0.3) -> List[Dict]:
        """
        Cluster chair detections across frames to identify stable chair positions.

        Args:
            all_detections: List of detections per frame
            iou_threshold: Minimum IoU to consider detections as same chair

        Returns:
            List of clustered chair information with average positions
        """
        # Flatten all detections
        flat_detections = []
        for frame_detections in all_detections:
            flat_detections.extend(frame_detections)

        if not flat_detections:
            print("Warning: No chairs detected")
            return []

        # Cluster detections using simple IoU-based grouping
        clusters = []
        used = set()

        for i, det1 in enumerate(flat_detections):
            if i in used:
                continue

            cluster = [det1]
            used.add(i)

            for j, det2 in enumerate(flat_detections):
                if j in used or j <= i:
                    continue

                iou = self._calculate_iou(det1[:4], det2[:4])
                if iou >= iou_threshold:
                    cluster.append(det2)
                    used.add(j)

            # Only keep clusters that appear in enough frames
            if len(cluster) >= self.stability_threshold:
                clusters.append(cluster)

        # Calculate average position for each cluster
        stable_chairs = []
        for cluster in clusters:
            avg_x1 = int(np.mean([d[0] for d in cluster]))
            avg_y1 = int(np.mean([d[1] for d in cluster]))
            avg_x2 = int(np.mean([d[2] for d in cluster]))
            avg_y2 = int(np.mean([d[3] for d in cluster]))
            avg_conf = float(np.mean([d[4] for d in cluster]))

            stable_chairs.append({
                'bbox': (avg_x1, avg_y1, avg_x2, avg_y2),
                'confidence': avg_conf,
                'detections': len(cluster)
            })

        print(f"Found {len(stable_chairs)} stable chair positions")
        return stable_chairs

    def generate_seat_zones(self, chairs: List[Dict],
                           padding: int = 10) -> Dict[str, List[List[int]]]:
        """
        Generate seat zones from detected chairs.

        Args:
            chairs: List of chair information from clustering
            padding: Extra padding around chair bounding box (pixels)

        Returns:
            Dictionary mapping seat IDs to polygon coordinates
        """
        seat_zones = {}

        for i, chair in enumerate(chairs, start=1):
            x1, y1, x2, y2 = chair['bbox']

            # Add padding
            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = x2 + padding
            y2 = y2 + padding

            # Create polygon (rectangle) from bounding box
            polygon = [
                [x1, y1],  # Top-left
                [x2, y1],  # Top-right
                [x2, y2],  # Bottom-right
                [x1, y2]   # Bottom-left
            ]

            seat_zones[f"seat_{i}"] = polygon

        return seat_zones

    def auto_calibrate(self, cap: cv2.VideoCapture,
                      visualize: bool = True) -> Optional[Dict[str, List[List[int]]]]:
        """
        Full automatic calibration pipeline.

        Args:
            cap: OpenCV VideoCapture object
            visualize: Whether to show detection progress

        Returns:
            Seat zones dictionary or None if detection failed
        """
        print("\n=== Starting Automatic Chair Detection ===")

        # Callback for visualization
        def viz_callback(frame, chairs, frame_num):
            if visualize:
                display_frame = frame.copy()

                # Draw detected chairs
                for x1, y1, x2, y2, conf in chairs:
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(display_frame, f'{conf:.2f}',
                              (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX,
                              0.5, (0, 255, 0), 2)

                # Progress indicator
                progress_text = f"Analyzing: {frame_num+1}/{self.num_frames} frames"
                cv2.putText(display_frame, progress_text, (10, 30),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                cv2.imshow('Auto-Calibration', display_frame)
                cv2.waitKey(1)

        # Step 1: Collect detections
        all_detections = self.collect_detections(cap, viz_callback if visualize else None)

        if not all_detections:
            print("Error: No detections collected")
            return None

        # Step 2: Cluster detections
        stable_chairs = self.cluster_detections(all_detections)

        if not stable_chairs:
            print("Error: No stable chairs found")
            return None

        # Step 3: Generate seat zones
        seat_zones = self.generate_seat_zones(stable_chairs)

        print(f"\n✓ Auto-calibration complete! Generated {len(seat_zones)} seat zones")

        if visualize:
            cv2.destroyWindow('Auto-Calibration')

        return seat_zones

    @staticmethod
    def _calculate_iou(box1: Tuple[int, int, int, int],
                      box2: Tuple[int, int, int, int]) -> float:
        """Calculate Intersection over Union between two boxes."""
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2

        # Calculate intersection
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)

        if x2_i < x1_i or y2_i < y1_i:
            return 0.0

        intersection = (x2_i - x1_i) * (y2_i - y1_i)

        # Calculate union
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0.0


def main():
    """Standalone auto-calibration script."""
    import argparse
    from seat_utils import save_zones

    parser = argparse.ArgumentParser(description='Automatic chair detection and calibration')
    parser.add_argument('--camera', type=int, default=0, help='Camera ID')
    parser.add_argument('--output', type=str, default='seat_zones.json',
                       help='Output file for seat zones')
    parser.add_argument('--no-viz', action='store_true',
                       help='Disable visualization')
    args = parser.parse_args()

    # Open camera
    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print("Error: Could not open camera")
        return

    # Set resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)

    # Run auto-calibration
    calibrator = AutoCalibrator()
    seat_zones = calibrator.auto_calibrate(cap, visualize=not args.no_viz)

    # Save results
    if seat_zones:
        save_zones(seat_zones, args.output)
        print(f"\n✓ Seat zones saved to {args.output}")
    else:
        print("\n✗ Auto-calibration failed")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
