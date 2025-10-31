"""
Utility functions for seat occupancy detection
"""

import cv2
import numpy as np
import json
import os
from typing import List, Tuple, Dict


def calculate_iou(box1: Tuple[int, int, int, int], box2: Tuple[int, int, int, int]) -> float:
    """
    Calculate Intersection over Union (IoU) between two bounding boxes

    Args:
        box1, box2: Bounding boxes in format (x1, y1, x2, y2)

    Returns:
        IoU value between 0 and 1
    """
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2

    # Calculate intersection area
    x_left = max(x1_1, x1_2)
    y_top = max(y1_1, y1_2)
    x_right = min(x2_1, x2_2)
    y_bottom = min(y2_1, y2_2)

    if x_right < x_left or y_bottom < y_top:
        return 0.0

    intersection_area = (x_right - x_left) * (y_bottom - y_top)

    # Calculate union area
    box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
    box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
    union_area = box1_area + box2_area - intersection_area

    return intersection_area / union_area if union_area > 0 else 0.0


def point_in_polygon(point: Tuple[int, int], polygon: List[Tuple[int, int]]) -> bool:
    """
    Check if a point is inside a polygon using ray casting algorithm

    Args:
        point: (x, y) coordinates
        polygon: List of (x, y) coordinates defining the polygon

    Returns:
        True if point is inside polygon, False otherwise
    """
    x, y = point
    n = len(polygon)
    inside = False

    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside


def box_in_zone(box: Tuple[int, int, int, int], zone: List[Tuple[int, int]],
                min_overlap: float = 0.3) -> bool:
    """
    Check if a bounding box overlaps with a seat zone

    Args:
        box: Bounding box (x1, y1, x2, y2)
        zone: List of points defining the seat zone polygon
        min_overlap: Minimum overlap ratio to consider as "in zone"

    Returns:
        True if box overlaps with zone above threshold
    """
    x1, y1, x2, y2 = box

    # Check if center of box is in zone
    center_x = (x1 + x2) // 2
    center_y = (y1 + y2) // 2

    if point_in_polygon((center_x, center_y), zone):
        return True

    # Check if any corner is in zone
    corners = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
    in_zone_count = sum(1 for corner in corners if point_in_polygon(corner, zone))

    return (in_zone_count / 4) >= min_overlap


def draw_polygon(image: np.ndarray, points: List[Tuple[int, int]],
                 color: Tuple[int, int, int], thickness: int = 2) -> None:
    """
    Draw a polygon on the image

    Args:
        image: Image to draw on
        points: List of (x, y) coordinates
        color: BGR color tuple
        thickness: Line thickness
    """
    points_array = np.array(points, dtype=np.int32)
    cv2.polylines(image, [points_array], isClosed=True, color=color, thickness=thickness)


def fill_polygon(image: np.ndarray, points: List[Tuple[int, int]],
                 color: Tuple[int, int, int], alpha: float = 0.3) -> None:
    """
    Fill a polygon with semi-transparent color

    Args:
        image: Image to draw on
        points: List of (x, y) coordinates
        color: BGR color tuple
        alpha: Transparency (0-1)
    """
    overlay = image.copy()
    points_array = np.array(points, dtype=np.int32)
    cv2.fillPoly(overlay, [points_array], color)
    cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0, image)


def save_zones(zones: Dict, filepath: str = 'seat_zones.json') -> None:
    """
    Save seat zones to JSON file

    Args:
        zones: Dictionary of seat zones
        filepath: Path to save file
    """
    with open(filepath, 'w') as f:
        json.dump(zones, f, indent=4)
    print(f"Seat zones saved to {filepath}")


def load_zones(filepath: str = 'seat_zones.json') -> Dict:
    """
    Load seat zones from JSON file

    Args:
        filepath: Path to JSON file

    Returns:
        Dictionary of seat zones
    """
    if not os.path.exists(filepath):
        return {}

    with open(filepath, 'r') as f:
        zones = json.load(f)

    # Convert string keys back and ensure points are tuples
    converted_zones = {}
    for seat_name, points in zones.items():
        converted_zones[seat_name] = [tuple(p) for p in points]

    return converted_zones


def draw_text_with_background(image: np.ndarray, text: str, position: Tuple[int, int],
                               font_scale: float = 0.6, thickness: int = 2,
                               text_color: Tuple[int, int, int] = (255, 255, 255),
                               bg_color: Tuple[int, int, int] = (0, 0, 0)) -> None:
    """
    Draw text with a background rectangle for better visibility

    Args:
        image: Image to draw on
        text: Text to display
        position: (x, y) position for text
        font_scale: Font scale
        thickness: Text thickness
        text_color: Text color (BGR)
        bg_color: Background color (BGR)
    """
    font = cv2.FONT_HERSHEY_SIMPLEX
    x, y = position

    # Get text size
    (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)

    # Draw background rectangle
    cv2.rectangle(image,
                  (x - 5, y - text_height - 5),
                  (x + text_width + 5, y + baseline + 5),
                  bg_color, -1)

    # Draw text
    cv2.putText(image, text, (x, y), font, font_scale, text_color, thickness)


def format_stats(occupied_count: int, total_count: int, fps: float) -> List[str]:
    """
    Format statistics for display

    Args:
        occupied_count: Number of occupied seats
        total_count: Total number of seats
        fps: Current FPS

    Returns:
        List of formatted strings
    """
    occupancy_rate = (occupied_count / total_count * 100) if total_count > 0 else 0

    stats = [
        f"Occupied Seats: {occupied_count}/{total_count}",
        f"Occupancy Rate: {occupancy_rate:.1f}%",
        f"Empty Seats: {total_count - occupied_count}",
        f"FPS: {fps:.1f}"
    ]

    return stats
