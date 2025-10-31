# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Real-time seat occupancy detection system using YOLOv5, OpenCV, and webcam for classroom/transport monitoring. Implementation of the vision component from the research paper "Hybrid Multi-Sensor Approach to Intelligent Seat Monitoring" (Dheerendra Pratap et al., Sharda University).

**Key Technologies**: YOLOv5s (person detection), PyTorch, OpenCV, Flask (web interface)

## Essential Commands

### Setup & Verification
```bash
# Install dependencies (creates venv, installs packages)
./setup.sh

# Or manual installation
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Verify environment (checks Python, dependencies, CUDA, webcam, downloads YOLOv5 weights)
python3 test_setup.py
```

### Calibration (Required before first run)
```bash
# Fully automatic: detect chairs and start detection
python3 main.py --auto-calibrate

# Guided auto-detection: review and approve suggestions
python3 calibrate.py --auto

# Manual: click 4 corners per seat
python3 calibrate.py
```

**Calibration outputs**: `seat_zones.json` (polygon coordinates for each seat)

### Running Detection
```bash
# Standard detection (requires existing seat_zones.json)
python3 main.py

# Web interface on localhost:5000
python3 web_server.py

# Web interface with auto-calibration if zones missing
python3 web_server.py --auto-calibrate

# Web interface accessible on network
python3 web_server.py --host 0.0.0.0 --port 8080
```

**Runtime controls** (main.py):
- `q`: quit
- `r`: start/stop recording (saves to `output/recording_YYYYMMDD_HHMMSS.mp4`)
- `h`: show help

**Calibration controls**:
- `a`: trigger auto-detect
- `n`: skip to next seat
- `c`: clear current/suggestions
- `s`: save and exit
- `q`: quit without saving

### Testing Individual Modules
```bash
# Standalone auto-calibration
python3 auto_calibrator.py --camera 0 --output seat_zones.json

# Test specific camera ID
python3 -c "import cv2; cap=cv2.VideoCapture(1); print('OK' if cap.isOpened() else 'FAIL')"

# Check GPU availability
python3 -c "import torch; print(torch.cuda.is_available())"
```

## Architecture

### Pipeline Flow
1. **Initialization**: Load `seat_zones.json` → Load YOLOv5 via `torch.hub` → Initialize webcam
2. **Input**: Capture 1280×720 frames at ~30 FPS
3. **Detection**: YOLOv5 person detection (COCO class 0) with GPU/CPU inference
4. **Mapping**: `SeatMapper.update_occupancy()` maps bounding boxes to seat polygons using overlap ratio
5. **Visualization**: Draw color-coded zones (green=empty, red=occupied), person boxes, statistics
6. **Output**: Display annotated frame, optionally record to MP4

### Core Modules

**main.py** (370 lines)
- `SeatOccupancyDetector` class: Main detection loop
- Integrates YOLOv5 inference, seat mapping, visualization, recording
- Auto-calibration integration via `--auto-calibrate` flag

**seat_mapper.py** (91 lines)
- `SeatMapper` class: Maps person detections to seat zones
- `update_occupancy()`: Core logic using `box_in_zone()` with configurable overlap threshold
- Tracks occupancy state per seat, provides statistics

**auto_calibrator.py** (328 lines)
- `AutoCalibrator` class: Automatic chair detection (COCO class 56)
- Collects detections over 30 frames, clusters stable positions using IoU
- Generates rectangular seat zones with padding

**calibrate.py** (276 lines)
- `SeatCalibrator` class: Interactive calibration UI
- Mouse-driven polygon definition (4 corners per seat)
- Hybrid mode: auto-detect + manual approval
- Saves to `seat_zones.json`

**seat_utils.py** (226 lines)
- Geometry: `point_in_polygon()`, `box_in_zone()`, `calculate_iou()`
- Drawing: `draw_polygon()`, `fill_polygon()`, `draw_text_with_background()`
- Persistence: `save_zones()`, `load_zones()` (JSON serialization)

**web_server.py** (500+ lines)
- Flask web interface with real-time MJPEG streaming
- REST API endpoints: `/api/stats`, `/api/recording/start`, `/api/calibrate/auto`
- Server-Sent Events (SSE) for live statistics streaming
- Control panel: recording, zone reload, auto-calibration

**config.py**
- Single source of truth for all parameters
- Key settings: `MODEL_NAME='yolov5s'`, `CONFIDENCE_THRESHOLD=0.5`, `MIN_OVERLAP_RATIO=0.3`
- Auto-calibration tuning: `AUTO_CALIB_CONFIDENCE`, `AUTO_CALIB_FRAMES`, `AUTO_CALIB_STABILITY`, `AUTO_CALIB_IOU_THRESHOLD`, `AUTO_CALIB_PADDING`

### Key Design Patterns

**Seat Zone Representation**: JSON dict of `{"seat_1": [[x1,y1], [x2,y2], [x3,y3], [x4,y4]], ...}` defining quadrilaterals

**Detection-to-Seat Mapping**:
- For each person bbox, check overlap with all seat polygons
- `box_in_zone()` uses center point + corner points; triggers if `(corners_in_zone / 4) >= MIN_OVERLAP_RATIO`
- Person assigned to first matching seat (no double-assignment)

**Auto-Calibration Strategy**:
- Detect chairs (class 56) over 30 frames
- Cluster detections by IoU threshold (0.3) to find stable positions
- Keep clusters appearing in ≥15 frames
- Generate rectangular zones with 10px padding

**YOLOv5 Integration**: Loaded via `torch.hub.load('ultralytics/yolov5', 'yolov5s')` on first run (downloads ~14MB model to `yolov5s.pt`)

## Development Practices

### Modifying Detection Parameters
- **Accuracy**: Adjust `CONFIDENCE_THRESHOLD` (0.5 default) or switch to `yolov5m`/`yolov5l` in config.py
- **Overlap sensitivity**: Change `MIN_OVERLAP_RATIO` (0.3 = 25% overlap required)
- **Auto-calibration**: Tune `AUTO_CALIB_CONFIDENCE` (lower for fewer chairs), `AUTO_CALIB_IOU_THRESHOLD` (higher for fewer duplicates)

### Adding New Features
- **New sensors**: Extend `SeatMapper` to accept additional inputs (thermal, Wi-Fi CSI)
- **Tracking**: Replace frame-by-frame detection with DeepSORT/ByteTrack for persistent IDs
- **Analytics**: Log occupancy to database, add time-series analysis

### Testing Workflow
1. Run `python3 test_setup.py` after environment changes
2. Use `calibrate.py --auto` to verify auto-detection on new hardware
3. Test main.py with demo scenarios: empty → partial → full occupancy
4. Record backup videos (`r` key) for offline testing

### File Structure Notes
- `output/`: Auto-created for recordings
- `seat_zones.json`: Generated by calibration, gitignored by default
- `yolov5s.pt`: 14MB model weights, downloaded on first run
- `static/`: CSS/JS for web interface
- `templates/`: Jinja2 HTML templates for Flask
- `venv/`: Python virtual environment (not committed)

## Common Issues

**"No seat zones found"**: Run `python3 calibrate.py` or `python3 main.py --auto-calibrate` first

**GPU not detected**: Falls back to CPU automatically; install CUDA-enabled PyTorch for 30+ FPS (`pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118`)

**Webcam not accessible**: Try different `WEBCAM_ID` values (0, 1, 2) in config.py

**Auto-calibration finds no chairs**: Lower `AUTO_CALIB_CONFIDENCE` to 0.3, increase `AUTO_CALIB_FRAMES` to 60, ensure chairs are fully visible

**Poor detection accuracy**: Improve lighting, recalibrate zones to fully cover seats, adjust `CONFIDENCE_THRESHOLD`

**Web interface video not loading**: Verify webcam access, check `WEBCAM_ID`, look for Flask errors in terminal

## Project Context

- **Based on**: Research paper proposing multi-sensor system (camera + thermal + Wi-Fi CSI + LiDAR)
- **This implementation**: Camera-only module achieving ~90-95% accuracy (paper reports 93.7% for YOLOv5)
- **Target deployment**: Jetson Nano or desktop/laptop with webcam
- **Use cases**: Classroom monitoring, bus/train seat tracking, demo for academic submission
- **Extensibility**: Modular design ready for sensor fusion and edge deployment
