"""
Seat mapping module - maps detected persons to seat zones
"""

import numpy as np
from typing import List, Tuple, Dict
import seat_utils as utils


class SeatMapper:
    def __init__(self, seat_zones: Dict[str, List[Tuple[int, int]]], min_overlap: float = 0.3):
        """
        Initialize seat mapper

        Args:
            seat_zones: Dictionary of seat zones {seat_name: [(x,y), ...]}
            min_overlap: Minimum overlap ratio to consider seat occupied
        """
        self.seat_zones = seat_zones
        self.min_overlap = min_overlap
        self.occupancy_state = {seat: False for seat in seat_zones.keys()}

    def update_occupancy(self, detections: List[Tuple[int, int, int, int, float]]) -> Dict[str, bool]:
        """
        Update seat occupancy based on person detections

        Args:
            detections: List of bounding boxes [(x1, y1, x2, y2, confidence), ...]

        Returns:
            Dictionary of seat occupancy {seat_name: is_occupied}
        """
        # Reset all seats to empty
        self.occupancy_state = {seat: False for seat in self.seat_zones.keys()}

        # Check each detection against each seat zone
        for detection in detections:
            x1, y1, x2, y2, conf = detection
            bbox = (int(x1), int(y1), int(x2), int(y2))

            # Check which seat this person is in
            for seat_name, zone in self.seat_zones.items():
                if utils.box_in_zone(bbox, zone, self.min_overlap):
                    self.occupancy_state[seat_name] = True
                    break  # Assign person to first matching seat

        return self.occupancy_state

    def get_occupancy_stats(self) -> Tuple[int, int, float]:
        """
        Get occupancy statistics

        Returns:
            (occupied_count, total_count, occupancy_rate)
        """
        total = len(self.occupancy_state)
        occupied = sum(1 for is_occupied in self.occupancy_state.values() if is_occupied)
        rate = (occupied / total * 100) if total > 0 else 0.0

        return occupied, total, rate

    def get_empty_seats(self) -> List[str]:
        """
        Get list of empty seat names

        Returns:
            List of empty seat names
        """
        return [seat for seat, is_occupied in self.occupancy_state.items() if not is_occupied]

    def get_occupied_seats(self) -> List[str]:
        """
        Get list of occupied seat names

        Returns:
            List of occupied seat names
        """
        return [seat for seat, is_occupied in self.occupancy_state.items() if is_occupied]

    def is_seat_occupied(self, seat_name: str) -> bool:
        """
        Check if a specific seat is occupied

        Args:
            seat_name: Name of the seat

        Returns:
            True if occupied, False otherwise
        """
        return self.occupancy_state.get(seat_name, False)


class ChairMapper:
    """Maps detected chairs to predefined seat zones for validation and tracking"""

    def __init__(self, seat_zones: Dict[str, List[Tuple[int, int]]], min_overlap: float = 0.5):
        """
        Initialize chair mapper

        Args:
            seat_zones: Dictionary of seat zones {seat_name: [(x,y), ...]}
            min_overlap: Minimum overlap ratio to consider chair aligned with seat
        """
        self.seat_zones = seat_zones
        self.min_overlap = min_overlap
        self.chair_state = {seat: False for seat in seat_zones.keys()}
        self.total_chairs_detected = 0
        self.aligned_chairs = 0

    def update_chair_positions(self, chairs: List[Tuple[int, int, int, int, float]]) -> Dict[str, bool]:
        """
        Update chair positions and check alignment with seat zones

        Args:
            chairs: List of chair bounding boxes [(x1, y1, x2, y2, confidence), ...]

        Returns:
            Dictionary of chair alignment {seat_name: has_chair}
        """
        # Reset state
        self.chair_state = {seat: False for seat in self.seat_zones.keys()}
        self.total_chairs_detected = len(chairs)
        self.aligned_chairs = 0

        # Map chairs to seat zones
        for chair in chairs:
            x1, y1, x2, y2, conf = chair
            bbox = (int(x1), int(y1), int(x2), int(y2))

            # Check which seat zone this chair aligns with
            for seat_name, zone in self.seat_zones.items():
                if utils.box_in_zone(bbox, zone, self.min_overlap):
                    self.chair_state[seat_name] = True
                    self.aligned_chairs += 1
                    break  # Assign chair to first matching seat

        return self.chair_state

    def get_chair_statistics(self) -> Tuple[int, int, int]:
        """
        Get chair detection statistics

        Returns:
            (total_detected, aligned_with_zones, misaligned)
        """
        misaligned = self.total_chairs_detected - self.aligned_chairs
        return self.total_chairs_detected, self.aligned_chairs, misaligned

    def get_seats_with_chairs(self) -> List[str]:
        """
        Get list of seat names that have chairs detected

        Returns:
            List of seat names with aligned chairs
        """
        return [seat for seat, has_chair in self.chair_state.items() if has_chair]

    def get_seats_without_chairs(self) -> List[str]:
        """
        Get list of seat names without chairs detected

        Returns:
            List of seat names without chairs (potential missing/moved chairs)
        """
        return [seat for seat, has_chair in self.chair_state.items() if not has_chair]

    def needs_recalibration(self, threshold: float = 0.5) -> bool:
        """
        Check if recalibration might be needed based on chair alignment

        Args:
            threshold: Minimum ratio of seats with aligned chairs

        Returns:
            True if less than threshold of seats have aligned chairs
        """
        if len(self.seat_zones) == 0:
            return False

        alignment_ratio = self.aligned_chairs / len(self.seat_zones)
        return alignment_ratio < threshold
