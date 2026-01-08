# Bird Visit Dashboard

A web-based dashboard for monitoring backyard bird visits captured by your camera system.

## ⚠️ Important: Scripts Have Been Fixed

The original Python scripts had **16+ critical bugs** that caused crashes, security issues, and detection problems.

**What was fixed:**
- ✅ OpenAI API calls (completely broken)
- ✅ Thread safety issues (race conditions)
- ✅ Security vulnerabilities (exposed API keys)
- ✅ Cross-platform compatibility (Windows-only paths)
- ✅ Image processing bugs (false positives, missing detections)
- ✅ Error handling (crashes on common errors)

**See `scripts/BUGFIXES.md` for full details.**

## Overview

This dashboard displays bird visit data collected by the Python scripts in the `scripts/` folder. The dashboard auto-refreshes every 30 seconds to show the latest visits.

## Setup Instructions

### 1. Python Scripts (Local Machine)

The Python scripts run on your local machine with the camera. They:
- Capture images from your RTSP camera
- Detect birds using YOLO
- Analyze images with OpenAI
- Generate metrics and reports

**IMPORTANT: Use the Fixed Scripts**

The original scripts had 16+ critical bugs. Use the fixed versions in `scripts/`:
- ✅ `pilot_bird_counter_fixed.py` (real-time capture)
- ✅ `pilot_analyze_captures_fixed.py` (batch analysis)
- ✅ `config.py` (centralized configuration)

**Quick Setup:**

```bash
cd scripts
pip install -r requirements.txt
export OPENAI_API_KEY="your-key-here"
python pilot_bird_counter_fixed.py
```

See `scripts/SETUP_GUIDE.md` for complete instructions and `scripts/BUGFIXES.md` for what was fixed.

### 2. Web Dashboard

The web dashboard reads `metrics.json` and displays the data in a modern interface.

**To make images visible in the dashboard:**

Since your Python scripts save images to a local directory (e.g., `C:\env\vision\pilot_captures`), you have two options:

#### Option A: Copy files to public folder (Simple)
Copy your metrics and image folders into the `public/` directory:
```bash
# Copy metrics file
cp C:\env\vision\dashboard\metrics.json public/

# Copy image folders
cp -r C:\env\vision\pilot_captures public/
cp -r C:\env\vision\pilot_reports public/
```

Then the paths in metrics.json will resolve correctly.

#### Option B: Serve files with a static server (Better for production)
Set up a simple file server to serve your image directories, or configure your Python scripts to save directly to the `public/` folder.

### 3. Running the Dashboard

```bash
npm install
npm run dev
```

The dashboard will be available at http://localhost:5173

## Features

- Real-time bird visit tracking with auto-refresh
- Species identification and counting
- Image thumbnails with fallback icons for missing images
- Detailed visit table with links to full reports
- Responsive design for desktop and mobile
- Error handling for missing data or images

## Troubleshooting

**Images not loading?**
- Ensure image files are accessible in the `public/` folder
- Check that paths in `metrics.json` match your folder structure
- Look for 404 errors in browser console

**No data showing?**
- Verify `metrics.json` exists in `public/` folder
- Check that the file is valid JSON
- Look for errors in browser console

**Python scripts not working?**
- Verify all dependencies are installed: `pip install opencv-python ultralytics openai`
- Check that paths in the scripts match your system
- Review log files in the LOG_ROOT directory
