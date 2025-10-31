"""
Interactive seat zone calibration tool

Usage: python3 calibrate.py [--auto]
- Click to define corners of each seat zone (4 points per seat)
- Press 'a' to auto-detect chairs (hybrid mode)
- Press 'n' to move to next seat
- Press 's' to save and exit
- Press 'c' to clear current seat
- Press 'q' to quit without saving
"""

import cv2
import numpy as np
from typing import List, Tuple, Dict, Optional
import config
import seat_utils as utils
from auto_calibrator import AutoCalibrator


class SeatCalibrator:
    def __init__(self, auto_mode: bool = False):
        self.cap = cv2.VideoCapture(config.WEBCAM_ID)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

        self.zones: Dict[str, List[Tuple[int, int]]] = {}
        self.suggested_zones: Optional[Dict[str, List[List[int]]]] = None
        self.current_points: List[Tuple[int, int]] = []
        self.current_seat_number = 1
        self.frame = None
        self.auto_mode = auto_mode

        # Instructions text
        self.instructions = [
            "Press 'a' to auto-detect chairs",
            "Click 4 corners to define seat zone",
            "Press 'n' for next seat",
            "Press 'c' to clear current seat",
            "Press 's' to save and exit",
            "Press 'q' to quit without saving"
        ]

    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse click events"""
        if event == cv2.EVENT_LBUTTONDOWN:
            # If in suggestion mode, check if clicking on a suggested zone
            if self.suggested_zones:
                clicked_seat = self._get_clicked_suggested_seat(x, y)
                if clicked_seat:
                    print(f"✓ Approved {clicked_seat}")
                    self.zones[clicked_seat] = [tuple(p) for p in self.suggested_zones[clicked_seat]]
                    del self.suggested_zones[clicked_seat]

                    # If all suggestions accepted, clear suggestion mode
                    if not self.suggested_zones:
                        print("\n✓ All suggested zones approved!")
                        self.suggested_zones = None
                    return

            # Normal manual point selection mode
            if len(self.current_points) < 4:
                self.current_points.append((x, y))
                print(f"Point {len(self.current_points)}/4 added: ({x}, {y})")

                # Auto-save when 4 points are defined
                if len(self.current_points) == 4:
                    seat_name = f"seat_{self.current_seat_number}"
                    self.zones[seat_name] = self.current_points.copy()
                    print(f"\n✓ {seat_name} defined successfully!")
                    print(f"Ready for seat_{self.current_seat_number + 1}")
                    self.current_seat_number += 1
                    self.current_points.clear()

    def _get_clicked_suggested_seat(self, x: int, y: int) -> Optional[str]:
        """Check if a click is inside a suggested zone."""
        for seat_name, points in self.suggested_zones.items():
            if utils.point_in_polygon((x, y), points):
                return seat_name
        return None

    def draw_interface(self, frame):
        """Draw the calibration interface"""
        display_frame = frame.copy()

        # Draw suggested zones (if in suggestion mode)
        if self.suggested_zones:
            for seat_name, points in self.suggested_zones.items():
                # Draw with dashed effect (alternating solid/transparent)
                utils.fill_polygon(display_frame, points, (0, 255, 255), alpha=0.15)
                utils.draw_polygon(display_frame, points, (0, 255, 255), thickness=2)

                # Draw seat label
                center_x = int(np.mean([p[0] for p in points]))
                center_y = int(np.mean([p[1] for p in points]))
                cv2.putText(display_frame, f"{seat_name} (click to approve)",
                          (center_x - 80, center_y),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

        # Draw existing confirmed zones
        for seat_name, points in self.zones.items():
            utils.fill_polygon(display_frame, points, config.COLOR_OCCUPIED, alpha=0.2)
            utils.draw_polygon(display_frame, points, config.COLOR_OCCUPIED, thickness=2)

            # Draw seat label
            center_x = int(np.mean([p[0] for p in points]))
            center_y = int(np.mean([p[1] for p in points]))
            cv2.putText(display_frame, seat_name, (center_x - 30, center_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Draw current points being defined
        for i, point in enumerate(self.current_points):
            cv2.circle(display_frame, point, 5, (0, 255, 255), -1)
            cv2.putText(display_frame, str(i + 1), (point[0] + 10, point[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

        # Draw lines between current points
        if len(self.current_points) > 1:
            for i in range(len(self.current_points) - 1):
                cv2.line(display_frame, self.current_points[i],
                         self.current_points[i + 1], (0, 255, 255), 2)

        # Close the polygon if 4 points are defined (temporary preview)
        if len(self.current_points) == 4:
            cv2.line(display_frame, self.current_points[-1],
                     self.current_points[0], (0, 255, 255), 2)

        # Draw instructions panel
        panel_height = 220
        panel = np.zeros((panel_height, display_frame.shape[1], 3), dtype=np.uint8)

        y_offset = 30

        # Show mode status
        if self.suggested_zones:
            mode_text = f"SUGGESTION MODE: Click zones to approve ({len(self.suggested_zones)} pending)"
            cv2.putText(panel, mode_text,
                       (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        else:
            cv2.putText(panel, f"Defining: seat_{self.current_seat_number}",
                       (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        y_offset += 30

        cv2.putText(panel, f"Points: {len(self.current_points)}/4",
                    (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        y_offset += 25

        cv2.putText(panel, f"Total zones confirmed: {len(self.zones)}",
                    (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        y_offset += 35

        for instruction in self.instructions:
            cv2.putText(panel, instruction, (10, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            y_offset += 20

        # Combine frame and panel
        display_frame = np.vstack([display_frame, panel])

        return display_frame

    def run_auto_detection(self):
        """Run automatic chair detection and show suggestions."""
        print("\n--- Running Automatic Chair Detection ---")

        calibrator = AutoCalibrator(
            confidence_threshold=config.AUTO_CALIB_CONFIDENCE,
            num_frames=config.AUTO_CALIB_FRAMES,
            stability_threshold=config.AUTO_CALIB_STABILITY
        )

        suggested = calibrator.auto_calibrate(self.cap, visualize=True)

        if suggested:
            self.suggested_zones = suggested
            print(f"\n✓ Found {len(suggested)} chairs!")
            print("Click on each suggested zone (yellow) to approve it.")
            print("Press 'c' to reject all suggestions and start manual calibration.")
        else:
            print("\n✗ Auto-detection failed. Falling back to manual calibration.")

    def run(self):
        """Run the calibration interface"""
        print("=" * 60)
        print("SEAT ZONE CALIBRATION TOOL")
        print("=" * 60)
        print("\nStarting webcam...")

        if not self.cap.isOpened():
            print("Error: Could not open webcam")
            return

        cv2.namedWindow('Seat Calibration')
        cv2.setMouseCallback('Seat Calibration', self.mouse_callback)

        print("\nWebcam ready!")
        if self.auto_mode:
            print("Auto-detection mode enabled. Running chair detection...")
            self.run_auto_detection()
        else:
            print("Press 'a' to auto-detect chairs, or click 4 corners to define zones manually.")
        print(f"Defining seat_1...\n")

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Could not read frame")
                break

            self.frame = frame
            display_frame = self.draw_interface(frame)

            cv2.imshow('Seat Calibration', display_frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord('a'):
                # Trigger auto-detection
                if not self.suggested_zones:
                    self.run_auto_detection()
                else:
                    print("Already in suggestion mode. Accept or clear suggestions first.")

            elif key == ord('n'):
                # Move to next seat (skip current)
                if len(self.current_points) > 0:
                    print(f"Skipping incomplete seat_{self.current_seat_number}")
                    self.current_points.clear()
                self.current_seat_number += 1
                print(f"\nMoving to seat_{self.current_seat_number}")

            elif key == ord('c'):
                # Clear suggestions or current seat
                if self.suggested_zones:
                    print(f"Rejected {len(self.suggested_zones)} suggestions")
                    self.suggested_zones = None
                elif self.current_points:
                    print(f"Cleared {len(self.current_points)} points")
                    self.current_points.clear()
                elif self.zones:
                    last_seat = f"seat_{self.current_seat_number - 1}"
                    if last_seat in self.zones:
                        del self.zones[last_seat]
                        self.current_seat_number -= 1
                        print(f"Removed {last_seat}")

            elif key == ord('s'):
                # Save and exit
                if len(self.zones) > 0:
                    utils.save_zones(self.zones, 'seat_zones.json')
                    print(f"\n✓ Saved {len(self.zones)} seat zones")
                    break
                else:
                    print("\nNo zones defined. Define at least one seat zone before saving.")

            elif key == ord('q'):
                # Quit without saving
                print("\nExiting without saving...")
                break

        self.cap.release()
        cv2.destroyAllWindows()
        print("\nCalibration complete!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Seat zone calibration tool')
    parser.add_argument('--auto', action='store_true',
                       help='Start with automatic chair detection')
    args = parser.parse_args()

    calibrator = SeatCalibrator(auto_mode=args.auto)
    calibrator.run()
