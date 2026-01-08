# Bird Feeder Tracker

Automated bird feeder monitoring system with AI-powered species identification and real-time web dashboard.

## One-Click Setup

After downloading this project:

### Windows
Double-click **`START_BIRD_TRACKER.cmd`**

If it closes immediately, run **`TEST_SETUP.cmd`** first to diagnose the issue.

### Mac/Linux
Run **`./START_BIRD_TRACKER.sh`**

That's it! The startup script will:
- Check and install all Python requirements
- Install npm dependencies if needed
- Build the dashboard
- Start bird detection scripts
- Launch the web dashboard in your browser at http://localhost:8080

## Prerequisites

- **Python 3.8+** ([download](https://www.python.org/downloads/))
- **Node.js 16+** ([download](https://nodejs.org/))
- **OpenAI API key** (optional but recommended for species identification)
- **Network camera with RTSP support**

## Quick Configuration

Before running, edit **`scripts/config.py`** to set your camera URL:

```python
RTSP_URL = "rtsp://username:password@ip:port/path"
ROI_NORM = (0.25, 0.34, 0.62, 0.72)  # Region where feeder is located
OPENAI_API_KEY = "sk-..."  # Or set as environment variable
```

## What This Does

This system:
- Connects to your RTSP camera and watches for birds in real-time
- Detects birds automatically using YOLOv8 AI
- Captures high-quality photos when birds visit
- Identifies species using OpenAI GPT-4o-mini
- Displays everything on a beautiful web dashboard with visit history

## Fixed Scripts

The original Python scripts had **16+ critical bugs**. This project uses the fixed versions:
- ✅ OpenAI API calls (completely broken)
- ✅ Thread safety issues (race conditions)
- ✅ Security vulnerabilities (exposed API keys)
- ✅ Cross-platform compatibility (Windows-only paths)
- ✅ Image processing bugs (false positives, missing detections)
- ✅ Error handling (crashes on common errors)

**See `scripts/BUGFIXES.md` for full details.**

## Documentation

- **[QUICK_START.md](QUICK_START.md)** - Simple user guide for getting started
- **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** - Complete technical documentation
- **[scripts/SETUP_GUIDE.md](scripts/SETUP_GUIDE.md)** - Detailed setup instructions
- **[scripts/BUGFIXES.md](scripts/BUGFIXES.md)** - List of bugs that were fixed
- **[scripts/SUMMARY.md](scripts/SUMMARY.md)** - Project summary

## File Structure

```
START_BIRD_TRACKER.cmd          # Windows one-click startup
START_BIRD_TRACKER.sh           # Mac/Linux one-click startup
scripts/
  ├── pilot_bird_counter_fixed.py      # Real-time detection
  ├── pilot_analyze_captures_fixed.py  # Image analysis
  ├── config.py                        # Configuration
  └── requirements.txt                 # Python dependencies
public/
  ├── metrics.json                     # Bird visit data (JSON)
  ├── dashboard.html                   # Generated HTML dashboard
  ├── pilot_captures/                  # Captured images (organized by date)
  └── pilot_reports/                   # Analysis reports (organized by date)
src/
  └── App.tsx                          # React dashboard source
dist/
  └── ...                              # Built React app
```

## How It Works

1. **Bird Counter** (`pilot_bird_counter_fixed.py`) connects to your camera via RTSP
2. YOLOv8 AI detects birds in real-time within the configured region
3. When a bird visits, it captures a high-quality photo
4. **Bird Analyzer** (`pilot_analyze_captures_fixed.py`) processes new images
5. OpenAI GPT-4o-mini identifies the species and provides a description
6. Results are saved to `metrics.json` and `public/pilot_reports/`
7. Dashboard displays everything with photos, species counts, and visit history
8. Dashboard auto-refreshes every 30 seconds

## Manual Setup (if not using startup script)

```bash
# Install Python requirements
cd scripts
pip install -r requirements.txt

# Set API key
export OPENAI_API_KEY="your-key-here"  # Mac/Linux
set OPENAI_API_KEY=your-key-here       # Windows

# Run Python scripts
python pilot_bird_counter_fixed.py     # Terminal 1
python pilot_analyze_captures_fixed.py --watch  # Terminal 2

# Install npm dependencies and build
npm install
npm run build

# Serve dashboard
cd public
python -m http.server 8080  # Open http://localhost:8080
```

## Dashboard Features

- Total bird visits counter
- Species breakdown with counts (sorted by frequency)
- Visit history table with timestamps, species, and photos
- Links to detailed analysis reports for each visit
- Auto-refresh every 30 seconds
- Responsive design for desktop and mobile
- Image fallback for missing photos

## Stopping the System

**Windows**: Close all three command windows (main + Bird Counter + Bird Analyzer)

**Mac/Linux**: Press Ctrl+C in the terminal, or: `kill <PID>` (PIDs shown at startup)

## Troubleshooting

### Camera Not Connecting
- Verify RTSP URL in VLC: Media → Open Network Stream
- Check username/password are correct
- Ensure camera is on the same network
- Try different subtype values (0 or 1)

### No Birds Detected
- Watch the live preview window - is the feeder visible?
- Adjust `ROI_NORM` in `config.py` to cover the feeder area
- Try lowering `CONF_THRESH` to 0.15-0.20
- Ensure good lighting

### OpenAI Errors
- Verify API key: https://platform.openai.com/api-keys
- Check account has credits
- System works without OpenAI but won't identify species

### Dashboard Not Loading
- Check port 8080 is not in use
- Verify build completed: `npm run build`
- Check browser console for errors
- Ensure `public/metrics.json` exists

### High CPU Usage
- Increase `DETECTION_INTERVAL` to 1.0 in `config.py`
- Use smaller YOLO model: `yolov8n.pt`
- Reduce `VIEW_SCALE` to 0.4

## Cost Estimate

- **OpenAI API**: ~$0.01 per 100 bird identifications (GPT-4o-mini)
- **Storage**: ~500KB per captured image
- **Compute**: Minimal (runs on most laptops)

## Tips

- Test for 30 minutes before leaving overnight
- Best results with good lighting (daylight or artificial)
- Position camera so feeder fills 40-70% of frame
- Check `pilot_logs/` for detailed debug information
- Monitor API usage to avoid unexpected costs

---

Built with YOLOv8, OpenAI GPT-4o-mini, React, TailwindCSS, and Vite
