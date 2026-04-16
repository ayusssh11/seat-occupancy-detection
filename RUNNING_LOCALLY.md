# Running Seat Occupancy Detection Locally

This guide shows you how to run the seat occupancy detection system on your local machine using a webcam.

## Prerequisites

- Python 3.8+
- Node.js 18+ and npm
- Webcam (built-in or USB)
- (Optional) CUDA-capable GPU for better performance
- Git (for cloning the repository)

---

## Initial Setup (New Machine)

If this is your first time setting up the project, follow these steps:

### Step 1: Clone and Navigate
```bash
git clone https://github.com/himanshu-cloudsufi/seat-occupancy-detection.git
cd seat-occupancy-detection
```

### Step 2: Backend Setup (Python)
```bash
# Navigate to backend directory
cd seat-occupancy-detection

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip3 install -r requirements.txt
```

### Step 3: Frontend Setup (Next.js)
```bash
# From the project root
cd ../frontend

# Install dependencies
npm install
```

### Step 4: Verify Installation
```bash
# Test backend setup
cd ../seat-occupancy-detection
source venv/bin/activate
python3 test_setup.py
```

---

## Quick Start (Existing Setup)

If you've already completed the initial setup, use these commands:

### Step 1: Navigate to Project Directory

```bash
cd /path/to/seat-occupancy-detection
```

### Step 2: Activate Virtual Environment

```bash
source venv/bin/activate
```

You should see `(venv)` appear in your terminal prompt.

### Step 3: Verify Installation (Optional)

```bash
python3 test_setup.py
```

---

## Running the System

The project now consists of two parts that must run simultaneously.

### Part 1: Start the Backend API
This handles the webcam feed and YOLOv5 detection.

```bash
cd seat-occupancy-detection
source venv/bin/activate
python3 web_server.py
```
The API will start on **http://localhost:5000**.

### Part 2: Start the Modern Dashboard
This provides the premium user interface.

```bash
cd frontend
npm run dev
```
Open your browser to: **http://localhost:3000**

---

## Legacy Running Options (OpenCV Only)

If you prefer to run without the web dashboard:

### Option A: Auto-Calibrate + Detect (Local Window)
```bash
cd seat-occupancy-detection
source venv/bin/activate
python3 main.py --auto-calibrate
```

### Option B: Manual Calibration
```bash
python3 calibrate.py
python3 main.py
```

---

## Command Reference

| Command | Description |
|---------|-------------|
| `python3 test_setup.py` | Verify environment and dependencies |
| `python3 calibrate.py` | Manual seat zone calibration |
| `python3 calibrate.py --auto` | Hybrid auto + manual calibration |
| `python3 main.py` | Run detection (requires existing zones) |
| `python3 main.py --auto-calibrate` | Auto-calibrate then run detection |
| `python3 web_server.py` | Launch web interface |
| `python3 auto_calibrator.py` | Standalone chair detection utility |

---

## Configuration

All settings can be adjusted in `config.py`:

### Model Settings

```python
MODEL_NAME = 'yolov5s'           # Options: yolov5s, yolov5m, yolov5l
CONFIDENCE_THRESHOLD = 0.5        # Detection confidence (0.0-1.0)
IOU_THRESHOLD = 0.45              # Non-max suppression threshold
```

### Camera Settings

```python
WEBCAM_ID = 0                     # Try 0, 1, 2 if webcam not detected
FRAME_WIDTH = 1280                # Resolution width
FRAME_HEIGHT = 720                # Resolution height
FPS = 30                          # Target frame rate
```

### Detection Parameters

```python
MIN_OVERLAP_RATIO = 0.3           # 30% overlap to consider seat occupied
ENABLE_CHAIR_DETECTION = True     # Show chair bounding boxes
CHAIR_CONFIDENCE_THRESHOLD = 0.4  # Chair detection confidence
```

### Auto-Calibration Tuning

```python
AUTO_CALIB_CONFIDENCE = 0.4       # Chair detection threshold
AUTO_CALIB_FRAMES = 30            # Frames to analyze (1 sec at 30 FPS)
AUTO_CALIB_STABILITY = 15         # Min frames chair must appear
AUTO_CALIB_PADDING = 10           # Padding around chairs (pixels)
AUTO_CALIB_IOU_THRESHOLD = 0.3    # IoU for clustering detections
```

---

## Troubleshooting

### Environment Issues

#### Virtual Environment Not Activated

**Problem:** `ModuleNotFoundError: No module named 'torch'`

**Solution:**
```bash
source venv/bin/activate
```

Verify by checking for `(venv)` in your terminal prompt.

#### Dependencies Missing

**Problem:** Import errors or missing packages

**Solution:**
```bash
pip install -r requirements.txt
```

---

### Webcam Issues

#### Webcam Not Detected

**Problem:** `Error: Could not open webcam`

**Test webcam access:**
```bash
python3 -c "import cv2; cap=cv2.VideoCapture(0); print('✓ OK' if cap.isOpened() else '✗ FAIL')"
```

**Solutions:**
1. Try different webcam IDs in `config.py`:
   ```python
   WEBCAM_ID = 1  # or 2, 3
   ```

2. Check webcam permissions (macOS):
   - System Preferences → Security & Privacy → Camera
   - Allow Terminal/iTerm access

3. Test with other apps (FaceTime, Zoom) to verify webcam works

#### Permission Denied (macOS)

Grant camera access to Terminal:
```bash
tccutil reset Camera
```
Then restart Terminal and try again.

---

### Performance Issues

#### Slow FPS (< 10 FPS)

**Check GPU availability:**
```bash
python3 -c "import torch; print('GPU:', torch.cuda.is_available())"
```

**If GPU not available:**

1. **Install CUDA-enabled PyTorch:**
   ```bash
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```

2. **Or reduce resolution in `config.py`:**
   ```python
   FRAME_WIDTH = 640
   FRAME_HEIGHT = 480
   ```

3. **Or use smaller model:**
   ```python
   MODEL_NAME = 'yolov5n'  # Nano model (faster but less accurate)
   ```

#### High CPU Usage

- Close unnecessary applications
- Ensure GPU is being used (check `config.py`: `DEVICE = 'cuda'`)
- Lower frame rate: `FPS = 15`

---

### Calibration Issues

#### Auto-Calibration Finds No Chairs

**Problem:** `No chairs detected. Try lowering confidence threshold.`

**Solutions:**

1. **Lower confidence in `config.py`:**
   ```python
   AUTO_CALIB_CONFIDENCE = 0.3  # Down from 0.4
   ```

2. **Increase analysis frames:**
   ```python
   AUTO_CALIB_FRAMES = 60  # Up from 30
   ```

3. **Improve lighting:** Ensure chairs are well-lit and fully visible

4. **Use hybrid mode:**
   ```bash
   python3 calibrate.py --auto
   ```
   Then manually draw zones if auto-detection misses seats

#### Duplicate Zones

**Problem:** Multiple zones detected for the same chair

**Solution in `config.py`:**
```python
AUTO_CALIB_IOU_THRESHOLD = 0.5  # Up from 0.3 (more aggressive merging)
```

#### Zones Too Small/Large

**Solution in `config.py`:**
```python
AUTO_CALIB_PADDING = 20  # Larger zones (up from 10)
# or
AUTO_CALIB_PADDING = 5   # Smaller zones (down from 10)
```

---

### Detection Issues

#### Poor Detection Accuracy

**Solutions:**

1. **Improve lighting conditions**
   - Avoid backlighting (windows behind seats)
   - Ensure even lighting across all seats

2. **Recalibrate seat zones**
   - Make sure zones fully cover each seat
   - Zones should not overlap

3. **Adjust confidence threshold in `config.py`:**
   ```python
   CONFIDENCE_THRESHOLD = 0.4  # Lower for more detections
   # or
   CONFIDENCE_THRESHOLD = 0.6  # Higher to reduce false positives
   ```

4. **Use larger model (slower but more accurate):**
   ```python
   MODEL_NAME = 'yolov5m'  # Medium model
   # or
   MODEL_NAME = 'yolov5l'  # Large model
   ```

#### False Positives (Empty Seat Marked Occupied)

**Solutions:**
- Increase overlap threshold in `config.py`:
  ```python
  MIN_OVERLAP_RATIO = 0.4  # Up from 0.3 (requires more overlap)
  ```
- Remove objects from seats (bags, backpacks may be detected as people)
- Recalibrate zones to be more precise

---

## File Outputs

### Generated Files

| File | Description | Location |
|------|-------------|----------|
| `seat_zones.json` | Seat zone coordinates | Project root |
| `recording_TIMESTAMP.mp4` | Recorded videos | `output/` directory |
| `yolov5s.pt` | YOLOv5 model weights | Downloaded to cache |

### Example `seat_zones.json`

```json
{
    "seat_1": [
        [318, 272],
        [632, 272],
        [632, 601],
        [318, 601]
    ],
    "seat_2": [
        [650, 280],
        [964, 280],
        [964, 609],
        [650, 609]
    ]
}
```

Each seat is defined by 4 corner points (clockwise from top-left).

---

## Advanced Usage

### Standalone Chair Detection

Test auto-calibration without running full detection:

```bash
python3 auto_calibrator.py --camera 0 --output my_zones.json
```

### Custom Webcam Settings

Test different webcam configurations:

```bash
# Test webcam 1 with custom resolution
python3 -c "
import cv2
cap = cv2.VideoCapture(1)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
print(f'Resolution: {int(cap.get(3))}x{int(cap.get(4))}')
cap.release()
"
```

### Headless Mode (No Display)

For servers or remote systems without display:

Modify `main.py` line 377:
```python
# Comment out:
# cv2.imshow('Seat Occupancy Detection', frame)

# Add:
cv2.imwrite(f'frame_{self.frame_count}.jpg', frame)  # Save frames instead
```

---

## Tips for Best Results

### Camera Placement

1. **Height:** Mount camera 1.5-2m above ground
2. **Angle:** 30-45° downward angle for best seat visibility
3. **Coverage:** Ensure all seats are visible without obstruction
4. **Stability:** Use tripod or secure mount (no movement)

### Environment

1. **Lighting:** Consistent, even lighting (avoid shadows)
2. **Background:** Clear background behind seats
3. **Arrangement:** Seats in organized rows/columns work best

### Calibration Best Practices

1. **Empty seats:** Calibrate with all seats empty
2. **Consistent view:** Don't move camera after calibration
3. **Full coverage:** Zones should fully cover seat area
4. **No overlap:** Adjacent zones should not overlap

---

## Quick Troubleshooting Checklist

Before asking for help, verify:

- [ ] Virtual environment is activated (`source venv/bin/activate`)
- [ ] All dependencies installed (`python3 test_setup.py` passes)
- [ ] Webcam accessible (test with FaceTime/Zoom)
- [ ] Seat zones exist (`seat_zones.json` in project directory)
- [ ] Camera permissions granted (macOS: System Preferences)
- [ ] No other apps using the webcam simultaneously
- [ ] Config settings are appropriate for your setup

---

## Getting Help

1. **Check logs:** Look for error messages in terminal
2. **Run diagnostics:** `python3 test_setup.py`
3. **Review config:** Verify `config.py` settings match your hardware
4. **Consult README:** Main documentation at repo root
5. **Check Issues:** [GitHub Issues](https://github.com/himanshu-cloudsufi/seat-occupancy-detection/issues)

---

## Deactivate Environment

When you're done, deactivate the virtual environment:

```bash
deactivate
```

The `(venv)` prefix will disappear from your terminal prompt.

---

## Next Steps

- Try the [Google Colab version](https://colab.research.google.com/github/himanshu-cloudsufi/seat-occupancy-detection/blob/main/seat-occupancy-detection/seat_occupancy_colab.ipynb) for browser-based demos
- Explore the web interface with `python3 web_server.py`
- Adjust detection parameters in `config.py` for your environment
- Record demo videos with the `r` key for presentations

Good luck with your local setup! 🚀
