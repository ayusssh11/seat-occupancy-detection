"""
Configuration file for seat occupancy detection system
"""

# Model configuration
MODEL_NAME = 'yolov5s'  # Using small model for speed
CONFIDENCE_THRESHOLD = 0.5
IOU_THRESHOLD = 0.45

# Auto-detect device (CUDA if available, otherwise CPU)
import torch
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

# Webcam configuration
WEBCAM_ID = 0
CAMERA_WIDTH = 1280  # Alias for consistency
CAMERA_HEIGHT = 720  # Alias for consistency
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
FPS = 30

# Seat zones configuration
# These will be defined interactively using calibrate.py
# Format: {'seat_1': [(x1, y1), (x2, y2), (x3, y3), (x4, y4)], ...}
SEAT_ZONES = {}

# Visualization colors (BGR format for OpenCV)
COLOR_EMPTY = (0, 255, 0)      # Green for empty seats
COLOR_OCCUPIED = (0, 0, 255)   # Red for occupied seats
COLOR_BBOX = (255, 255, 0)     # Cyan for detection boxes
COLOR_ZONE = (255, 165, 0)     # Orange for seat zones
COLOR_CHAIR = (0, 165, 255)    # Orange for chair detection boxes

# Text settings
FONT = 0  # cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.6
FONT_THICKNESS = 2

# Detection parameters
MIN_OVERLAP_RATIO = 0.3  # Minimum overlap to consider seat occupied

# Chair detection settings
ENABLE_CHAIR_DETECTION = True  # Toggle real-time chair detection
CHAIR_CONFIDENCE_THRESHOLD = 0.4  # Confidence threshold for chair detection

# Auto-calibration settings
AUTO_CALIB_CONFIDENCE = 0.4      # Confidence threshold for chair detection
AUTO_CALIB_FRAMES = 30           # Number of frames to analyze (1 second at 30 FPS)
AUTO_CALIB_STABILITY = 15        # Min frames a chair must appear in to be valid
AUTO_CALIB_PADDING = 10          # Padding around detected chairs (pixels)
AUTO_CALIB_IOU_THRESHOLD = 0.3   # IoU threshold for clustering chair detections

# Output settings
SAVE_VIDEO = True
OUTPUT_DIR = 'output'
VIDEO_CODEC = 'mp4v'

# Statistics display position
STATS_X = 10
STATS_Y = 30
STATS_LINE_HEIGHT = 30
