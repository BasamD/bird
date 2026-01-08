# Setup Guide for Fixed Bird Detection Scripts

## Prerequisites

- Python 3.8 or higher
- OpenAI API key
- RTSP camera (optional, for live capture)
- YOLO model file (auto-downloads on first run)

## Installation

### 1. Install Dependencies

```bash
cd scripts
pip install -r requirements.txt
```

This will install:
- opencv-python: For image processing and camera capture
- ultralytics: For YOLO bird detection
- openai: For species identification
- numpy: Required by OpenCV

### 2. Configure Environment

Create a `.env` file or set environment variables:

```bash
# Required
export OPENAI_API_KEY="sk-your-api-key-here"

# Optional (defaults provided)
export CAPTURE_ROOT="../pilot_captures"
export REPORT_ROOT="../pilot_reports"
export LOG_ROOT="../pilot_logs"
export DASHBOARD_DIR="../public"

# Camera settings
export RTSP_URL="rtsp://user:pass@192.168.1.79:554/cam/realmonitor?channel=1&subtype=0"

# Detection tuning
export CONF_THRESH="0.25"           # Lower = more sensitive
export MIN_AREA_RATIO="0.002"       # Filter tiny detections
export ROI_NORM="0.25,0.34,0.62,0.72"  # x1,y1,x2,y2 normalized

# Behavior
export CAPTURE_GAP_SEC="15"         # Min seconds between captures
export BIRD_ABSENCE_TIMEOUT="5"     # Seconds to consider bird gone
export DETECTION_INTERVAL="0.5"     # Seconds between YOLO runs
```

### 3. Verify Installation

```bash
# Test imports
python -c "import cv2, ultralytics, openai; print('All imports OK')"

# Test OpenAI
python -c "from pilot_bird_counter_fixed import load_openai_client; c, k = load_openai_client(); print('OpenAI:', 'OK' if c else 'MISSING KEY')"

# Test config
python -c "import config; print('Config loaded OK')"
```

## Usage

### Option 1: Live Camera Capture (Real-time)

```bash
python pilot_bird_counter_fixed.py
```

This will:
- Connect to your RTSP camera
- Show live video with detections
- Capture images when birds are detected
- Analyze with OpenAI automatically
- Generate reports and update dashboard
- Press 'q' to quit

### Option 2: Analyze Existing Images

```bash
# Single pass (process all images once)
python pilot_analyze_captures_fixed.py --root /path/to/images

# Watch mode (continuously monitor folder)
python pilot_analyze_captures_fixed.py --root /path/to/images --watch
```

This will:
- Scan the folder for new .jpg files
- Run YOLO detection on each image
- Analyze birds with OpenAI
- Generate HTML reports
- Update metrics.json and dashboard

## Configuration Tips

### Adjusting Detection Sensitivity

**If missing small birds:**
```bash
export CONF_THRESH="0.20"           # Lower threshold
export MIN_AREA_RATIO="0.001"       # Accept smaller boxes
```

**If too many false positives:**
```bash
export CONF_THRESH="0.35"           # Higher threshold
export MIN_AREA_RATIO="0.005"       # Filter more aggressively
```

### Adjusting Region of Interest (ROI)

The ROI focuses detection on the feeder area. Adjust based on your camera view:

```bash
# Format: x1,y1,x2,y2 (normalized 0-1)
# Current: center-bottom area
export ROI_NORM="0.25,0.34,0.62,0.72"

# Example: focus on left side
export ROI_NORM="0.1,0.3,0.5,0.8"

# Example: full frame (slower but catches everything)
export ROI_NORM="0.0,0.0,1.0,1.0"
```

### Capture Timing

```bash
# Capture more frequently (more images, more disk space)
export CAPTURE_GAP_SEC="5"          # Min 5 seconds between captures
export BIRD_ABSENCE_TIMEOUT="2"     # Bird gone after 2 seconds

# Capture less frequently (fewer duplicates)
export CAPTURE_GAP_SEC="30"         # Min 30 seconds between captures
export BIRD_ABSENCE_TIMEOUT="10"    # Bird gone after 10 seconds
```

## Troubleshooting

### "OpenAI disabled" in logs

**Cause:** OPENAI_API_KEY not set or invalid

**Fix:**
```bash
export OPENAI_API_KEY="sk-your-actual-key"
python -c "import os; print('Key set:', bool(os.getenv('OPENAI_API_KEY')))"
```

### "Failed to open RTSP stream"

**Causes:**
1. Wrong URL format
2. Camera offline
3. Network issues
4. Wrong credentials

**Fix:**
```bash
# Test with VLC or ffplay first
ffplay "rtsp://user:pass@ip:port/path"

# Check credentials
# Check camera is accessible: ping <camera-ip>
```

### "No module named 'cv2'"

**Fix:**
```bash
pip install opencv-python
```

### Images not detected / False positives

**Debug:**
```bash
# Enable debug logging
export LOG_LEVEL="DEBUG"
python pilot_analyze_captures_fixed.py --root ./test --watch
# Check logs in pilot_logs/ folder
```

### Dashboard not updating

**Check:**
1. Is metrics.json being created in public/ folder?
2. Are paths correct in config.py?
3. Check browser console for errors
4. Verify dashboard refresh is working (meta tag)

### Out of memory errors

**Fix:**
```bash
# Reduce detection image size
export DETECT_RESIZE_WIDTH="640"    # Default: 960

# Reduce view scale (doesn't affect detection)
export VIEW_SCALE="0.4"             # Default: 0.6
```

## Best Practices

### For Production Use

1. **Run as a service:**
```bash
# Create systemd service on Linux
sudo nano /etc/systemd/system/bird-counter.service
```

2. **Monitor disk usage:**
```bash
# Set up log rotation
# Periodically archive old captures
```

3. **Backup metrics:**
```bash
# Regular backup of metrics.json
cp public/metrics.json public/metrics.backup.json
```

4. **API rate limiting:**
- OpenAI has rate limits
- Consider batching analysis
- Use caching for duplicate images

### For Development

1. **Test with sample images first:**
```bash
# Create test folder
mkdir test_images
# Add some bird photos
python pilot_analyze_captures_fixed.py --root test_images
```

2. **Use debug logging:**
```python
# In scripts, logger level is already DEBUG for file output
# Check LOG_ROOT/pilot_*.log files
```

3. **Monitor performance:**
```bash
# Use htop or similar to monitor CPU/memory
# Adjust DETECTION_INTERVAL if CPU usage too high
```

## Architecture Overview

```
┌─────────────────────────────────────────┐
│ Camera (RTSP Stream)                    │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ Frame Grabber Thread                    │
│ (Continuous frame capture)              │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ Main Detection Loop                     │
│ - YOLO detection on ROI                 │
│ - Area filtering                        │
│ - Uniqueness logic                      │
│ - Save captures                         │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ Analysis Queue                          │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ Analysis Worker Thread                  │
│ - Crop to bird region                   │
│ - OpenAI species identification         │
│ - Generate HTML report                  │
│ - Update metrics/dashboard              │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ Output Files                            │
│ - metrics.json                          │
│ - dashboard.html                        │
│ - Individual reports                    │
│ - Captured images                       │
└─────────────────────────────────────────┘
```

## Performance Benchmarks

Typical performance on modest hardware:
- Detection: ~30-50ms per frame
- OpenAI analysis: ~2-5 seconds per image
- Total capture to dashboard: ~5-10 seconds
- CPU usage: 10-30% on quad-core
- Memory: ~500MB-1GB

## Security Notes

1. **Never commit API keys** to version control
2. **Use environment variables** for all secrets
3. **Restrict camera access** to local network
4. **Secure dashboard** if exposing publicly
5. **Monitor API usage** to avoid unexpected charges

## Support

For issues:
1. Check logs in LOG_ROOT folder
2. Review BUGFIXES.md for known issues
3. Verify environment variables are set
4. Test with sample images first
5. Check OpenAI API status
