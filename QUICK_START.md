# Bird Tracker - Quick Start Guide

## One-Click Setup

After downloading this project, simply double-click `START_BIRD_TRACKER.cmd` to:

1. Check Python and npm are installed
2. Install all Python requirements automatically
3. Install npm dependencies if needed
4. Build the dashboard
5. Start bird detection scripts
6. Launch the dashboard in your browser at http://localhost:8080

### If the window closes immediately

If the CMD window disappears without doing anything:

1. First, run `TEST_SETUP.cmd` to check your system
2. This will show you exactly what's missing
3. Or right-click `START_BIRD_TRACKER.cmd` and select "Edit" to see if there are any obvious path issues

The most common issues are:
- Python or Node.js not installed
- Not running from the correct folder (must be in project root)
- Antivirus blocking the script

## Prerequisites

Before running, make sure you have:

- **Python 3.8+** installed ([download here](https://www.python.org/downloads/))
- **Node.js** installed ([download here](https://nodejs.org/))
- **OpenAI API key** (optional but recommended for species identification)

## Setting Up Your OpenAI API Key

For species identification, you need an OpenAI API key:

1. Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. When you run `START_BIRD_TRACKER.cmd`, it will ask for your API key
3. Or set it permanently as an environment variable: `OPENAI_API_KEY=your-key-here`

Without an API key, the system will still detect birds but won't identify species.

## Configuration

Edit `scripts/config.py` to configure:

- **RTSP_URL**: Your camera's RTSP stream URL
- **ROI_NORM**: Region of interest (feeder area) as normalized coordinates
- **CAPTURE_GAP_SEC**: Minimum seconds between captures (default: 15)
- **CONF_THRESH**: YOLO confidence threshold (default: 0.25)

## What Runs

The startup script launches three processes:

1. **Bird Counter** - Connects to camera, detects birds in real-time, captures images
2. **Bird Analyzer** - Watches for new images, analyzes them with AI, identifies species
3. **Dashboard Server** - Hosts the web dashboard at http://localhost:8080

## File Structure

```
project/
├── START_BIRD_TRACKER.cmd    # One-click startup script
├── scripts/
│   ├── pilot_bird_counter_fixed.py      # Real-time bird detection
│   ├── pilot_analyze_captures_fixed.py  # Image analysis
│   ├── config.py                        # Configuration
│   └── requirements.txt                 # Python dependencies
├── public/
│   ├── metrics.json                     # Bird visit data
│   ├── dashboard.html                   # Generated dashboard
│   ├── pilot_captures/                  # Captured images
│   └── pilot_reports/                   # Analysis reports
└── src/                                 # React dashboard source

```

## Dashboard Features

The dashboard displays:

- **Total bird visits** count
- **Species breakdown** with counts
- **Visit history** with timestamps, species, and photos
- **Auto-refresh** every 30 seconds

Click on "report" or "photo" links to view detailed analysis.

## Troubleshooting

### Python not found
- Install Python from https://www.python.org/downloads/
- Make sure to check "Add Python to PATH" during installation

### npm not found
- Install Node.js from https://nodejs.org/

### No birds detected
- Check your RTSP_URL in `config.py`
- Adjust ROI_NORM coordinates to match your feeder location
- Lower CONF_THRESH if detection is too strict

### OpenAI errors
- Verify your API key is correct
- Check you have credits in your OpenAI account

## Stopping the System

To stop everything:

1. Press Ctrl+C in the main window (stops dashboard server)
2. Close the "Bird Counter" window
3. Close the "Bird Analyzer" window

Or simply close all three command windows.

## Next Steps

- Monitor the dashboard at http://localhost:8080
- Check `public/pilot_captures/` for captured images
- Review `public/pilot_reports/` for detailed analysis reports
- Check `pilot_logs/` for debug information
