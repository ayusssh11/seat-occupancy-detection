# Web Interface Usage Guide

## Overview

The web interface provides a browser-based dashboard for the seat occupancy detection system with real-time video streaming, statistics, and controls.

## Installation

1. Install Flask (if not already installed):
```bash
pip install Flask>=3.0.0
```

Or install all dependencies:
```bash
pip install -r requirements.txt
```

## Running the Web Server

### Basic Usage

Start the web server:
```bash
python3 web_server.py
```

Then open your browser and navigate to:
```
http://localhost:5000
```

### With Auto-Calibration

If you haven't calibrated seat zones yet:
```bash
python3 web_server.py --auto-calibrate
```

### Custom Host and Port

To make the server accessible from other devices on your network:
```bash
python3 web_server.py --host 0.0.0.0 --port 8080
```

Then access from any device on the same network using:
```
http://[your-computer-ip]:8080
```

## Web Interface Features

### 1. Live Video Feed
- Real-time MJPEG video stream with seat zones overlay
- Person detection bounding boxes
- Occupancy status visualization (green = empty, red = occupied)
- Statistics panel on video feed

### 2. Occupancy Statistics Panel
- **Occupied Seats**: Current number of occupied seats
- **Total Seats**: Total number of configured seats
- **Occupancy Rate**: Percentage of seats occupied
- **Empty Seats**: Number of available seats
- **Occupancy Progress Bar**: Visual representation of occupancy level
  - Green: 0-30% occupancy
  - Yellow: 30-70% occupancy
  - Red: 70-100% occupancy

### 3. Seat Status Display
- Individual seat status badges
- Color-coded (green = empty, red = occupied)
- Shows each seat name with icon
- Updates in real-time

### 4. Control Buttons

#### Start/Stop Recording
- Click to start recording the video feed
- Recording saves to `output/recording_YYYYMMDD_HHMMSS.mp4`
- Button changes to "Stop Recording" when active
- Red recording indicator appears on video feed

#### Reload Zones
- Reloads seat zones from `seat_zones.json`
- Use after manually running `python3 calibrate.py`
- Useful for updating seat configurations without restarting server

#### Auto-Calibrate
- Automatically detects chairs and creates seat zones
- Takes approximately 30 seconds
- Captures 30 frames and analyzes chair positions
- Saves zones to `seat_zones.json`

### 5. System Information
- **Status**: Online/Offline indicator
- **FPS**: Frames per second (real-time performance)
- **Recording**: Current recording status
- **Last Update**: Timestamp of last data update

### 6. Real-time Updates
- Uses Server-Sent Events (SSE) for live data streaming
- Automatic reconnection on connection loss
- Updates statistics every frame
- No page refresh required

## Usage Workflow

### First-Time Setup

1. Start the server with auto-calibration:
```bash
python3 web_server.py --auto-calibrate
```

2. Open browser to `http://localhost:5000`

3. Wait for auto-calibration to complete (you'll see a notification)

4. Check the Seat Status panel to verify detected seats

### Regular Use

1. Start the server:
```bash
python3 web_server.py
```

2. Open browser to `http://localhost:5000`

3. Monitor occupancy in real-time

4. Use controls as needed:
   - Start recording to save demos
   - Reload zones after recalibration
   - Run auto-calibrate to detect new configurations

### Manual Calibration

If auto-calibration doesn't detect seats properly:

1. Stop the web server (Ctrl+C)

2. Run manual calibration:
```bash
python3 calibrate.py
```

3. Define seat zones by clicking 4 corners per seat

4. Press 's' to save zones

5. Restart web server:
```bash
python3 web_server.py
```

6. Click "Reload Zones" in the web interface

## API Endpoints

The web server provides these REST API endpoints:

### GET /
Main web interface

### GET /video_feed
MJPEG video stream endpoint

### GET /api/stats
Returns current statistics as JSON:
```json
{
  "occupied": 2,
  "total": 4,
  "rate": 50.0,
  "fps": 30.5,
  "recording": false,
  "seats": {
    "seat_1": "occupied",
    "seat_2": "empty",
    "seat_3": "occupied",
    "seat_4": "empty"
  }
}
```

### GET /api/stream
Server-Sent Events stream for real-time updates

### POST /api/recording/start
Start video recording

### POST /api/recording/stop
Stop video recording

### POST /api/calibrate/reload
Reload seat zones from file

### POST /api/calibrate/auto
Run automatic calibration

## Keyboard Shortcuts

While the web server is running in terminal:
- **Ctrl+C**: Stop the server

## Browser Compatibility

Tested and working on:
- Chrome/Chromium 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance Tips

1. **Better FPS**: Ensure GPU is available (CUDA-enabled)
2. **Lower Latency**: Use wired network connection
3. **Multiple Viewers**: Server can handle multiple browser connections
4. **Recording**: Recording may slightly reduce FPS (1-2 FPS drop)

## Troubleshooting

### Video Feed Not Loading
- Check if webcam is accessible
- Verify `WEBCAM_ID` in `config.py`
- Look for errors in terminal

### No Statistics Appearing
- Ensure seat zones are configured
- Click "Reload Zones" or "Auto-Calibrate"
- Check `seat_zones.json` exists

### Connection Lost
- Web interface will show "Offline" status
- Automatically attempts to reconnect
- Check if server is still running in terminal

### Recording Fails
- Ensure `output/` directory exists (created automatically)
- Check disk space
- Verify video codec is supported

### Poor Detection
- Improve lighting conditions
- Adjust `CONFIDENCE_THRESHOLD` in `config.py`
- Recalibrate seat zones

## Mobile Access

To access from mobile device:

1. Start server with external access:
```bash
python3 web_server.py --host 0.0.0.0
```

2. Find your computer's IP address:
```bash
# On Mac/Linux
ifconfig | grep "inet "

# On Windows
ipconfig
```

3. On mobile browser, navigate to:
```
http://[computer-ip]:5000
```

## Security Notes

- Server binds to all interfaces when using `--host 0.0.0.0`
- Only use on trusted networks
- No authentication is implemented
- For production, add authentication and HTTPS

## Integration with Existing Scripts

The web interface does not interfere with existing scripts:
- `main.py` - Still works as standalone
- `calibrate.py` - Can be used for manual calibration
- `test_setup.py` - System verification still available

Use web interface for demos and monitoring, command-line tools for development.

## Advanced Configuration

Edit `config.py` to customize:
- Video resolution
- Detection confidence threshold
- FPS settings
- Colors and styling

## Example Use Cases

### 1. Live Demo for Presentation
```bash
python3 web_server.py --auto-calibrate
# Open http://localhost:5000 on projector
# Start recording to save demo
```

### 2. Remote Monitoring
```bash
python3 web_server.py --host 0.0.0.0 --port 8080
# Access from tablet/phone on same network
```

### 3. Development and Testing
```bash
# Terminal 1: Run web server
python3 web_server.py

# Terminal 2: Run calibration tool
python3 calibrate.py

# Browser: Click "Reload Zones" after calibration
```

## Support

For issues or questions:
1. Check the terminal output for error messages
2. Verify all dependencies are installed
3. Review `README.md` for general troubleshooting
4. Check browser console (F12) for JavaScript errors
