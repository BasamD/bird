# How to Start the Bird Tracker

## Quick Reference

There are several startup scripts available. Here's which one to use:

### 🚀 Normal Use
**`START_BIRD_TRACKER.cmd`** - The main startup script
- Use this once everything is working
- Fastest startup
- Opens 3 windows: Main Dashboard, Bird Counter, Bird Analyzer

### 🔍 Troubleshooting
**`START_WITH_LOGGING.cmd`** - Startup with detailed logging
- **Use this if START_BIRD_TRACKER.cmd closes immediately**
- Shows detailed progress at each step
- Creates a `startup_log.txt` file
- Won't close on errors - will pause so you can see what went wrong

### 🧪 Testing
**`TEST_STARTUP.cmd`** - Test all components
- Tests Python, packages, YOLO model, OpenCV
- Good for checking if everything is installed correctly
- Won't start the actual application

**`DIAGNOSE.cmd`** - Quick diagnostic check
- Fastest way to check if all dependencies are installed
- Shows what's working and what's missing

## First Time Setup

1. Run `DIAGNOSE.cmd` to check your installation
2. If everything passes, run `START_WITH_LOGGING.cmd`
3. Once you confirm it works, use `START_BIRD_TRACKER.cmd` for normal use

## What to Expect

When the tracker starts successfully, you'll see:
1. **Main Dashboard Window** - Shows the web server running on http://localhost:8080
2. **Bird Counter Window** - Shows live webcam feed with bird detection
3. **Bird Analyzer Window** - Processes captured images with AI
4. **Browser** - Opens automatically to http://localhost:8080

## Common Issues

### Window closes immediately
→ Run `START_WITH_LOGGING.cmd` instead

### "Python not found"
→ Install Python 3.8+ from https://python.org
→ Make sure "Add to PATH" is checked during installation

### "YOLO model failed to load"
→ Normal on first run - it will download automatically
→ Requires internet connection (about 6MB download)

### "Failed to open RTSP stream"
→ Check your camera IP address in `scripts/config.py`
→ The script will keep retrying every 2 seconds
→ You can still see the dashboard without a camera

### No webcam feed showing
→ Check your RTSP_URL in `scripts/config.py`
→ Make sure your camera is powered on and connected
→ The frame grabber will retry automatically

## Camera Configuration

Edit `scripts/config.py` to change your camera settings:

```python
RTSP_URL = "rtsp://admin:admin@YOUR_IP:554/..."
```

## Stopping the Tracker

To stop everything:
1. Press `Ctrl+C` in the Main Dashboard window, or close it
2. Close the Bird Counter window
3. Close the Bird Analyzer window

## Log Files

Logs are saved in:
- `pilot_logs/` - Bird detection logs
- `startup_log.txt` - Startup diagnostics (when using START_WITH_LOGGING.cmd)

## Captured Data

- Bird images: `public/pilot_captures/YYYY-MM-DD/`
- AI reports: `public/pilot_reports/YYYY-MM-DD/`
- Metrics: `public/metrics.json`
