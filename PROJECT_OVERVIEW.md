# Bird Feeder Tracker - Complete Project Overview

## What This Project Does

This is an automated bird feeder monitoring system that:

1. **Connects to your camera** via RTSP to watch your bird feeder in real-time
2. **Detects birds automatically** using YOLOv8 AI object detection
3. **Captures photos** when new birds visit
4. **Identifies species** using OpenAI's GPT-4o-mini vision model
5. **Displays everything** on a beautiful web dashboard with visit history

## Quick Start (One Command!)

### Windows
Double-click `START_BIRD_TRACKER.cmd`

### Mac/Linux
Run `./START_BIRD_TRACKER.sh`

That's it! The script handles everything automatically.

## System Architecture

### Components

#### 1. Bird Counter (`pilot_bird_counter_fixed.py`)
- Connects to RTSP camera stream
- Runs YOLOv8 detection every 0.5 seconds
- Shows live preview window with detected birds
- Captures images when new birds arrive (15+ second gap)
- Queues images for AI analysis

#### 2. Bird Analyzer (`pilot_analyze_captures_fixed.py`)
- Watches for new captured images
- Runs YOLO detection to verify birds
- Crops bird region and sends to OpenAI
- Receives species identification and summary
- Generates HTML reports
- Updates dashboard metrics

#### 3. Web Dashboard (React + TypeScript)
- Modern, responsive interface
- Real-time metrics display
- Species breakdown with counts
- Visit history with photos and reports
- Auto-refreshes every 30 seconds
- Built with Vite, React, TailwindCSS

### Data Flow

```
Camera (RTSP)
    ↓
Bird Counter (YOLO Detection)
    ↓
Image Capture → public/pilot_captures/
    ↓
Bird Analyzer (YOLO + OpenAI)
    ↓
Reports → public/pilot_reports/
    ↓
Metrics → public/metrics.json
    ↓
Web Dashboard → Display
```

## File Structure

```
project/
├── START_BIRD_TRACKER.cmd          # Windows startup script
├── START_BIRD_TRACKER.sh           # Mac/Linux startup script
├── QUICK_START.md                  # User guide
├── PROJECT_OVERVIEW.md             # This file
│
├── scripts/                        # Python backend
│   ├── pilot_bird_counter_fixed.py      # Real-time detection
│   ├── pilot_analyze_captures_fixed.py  # Image analysis
│   ├── config.py                        # Configuration
│   ├── requirements.txt                 # Python deps
│   └── test_logic.py                    # Testing utilities
│
├── src/                            # React dashboard source
│   ├── App.tsx                     # Main dashboard component
│   ├── main.tsx                    # React entry point
│   └── index.css                   # Styles
│
├── public/                         # Generated output
│   ├── metrics.json                # Bird visit data (JSON)
│   ├── dashboard.html              # Generated dashboard
│   ├── pilot_captures/             # Captured bird images
│   │   └── YYYY-MM-DD/            # Organized by date
│   │       └── bird_*.jpg
│   └── pilot_reports/              # Analysis reports
│       └── YYYY-MM-DD/            # Organized by date
│           └── bird_*.html
│
├── dist/                           # Built React app
├── pilot_logs/                     # Application logs
│
├── package.json                    # npm dependencies
├── tsconfig.json                   # TypeScript config
├── vite.config.ts                  # Vite build config
└── tailwind.config.js              # TailwindCSS config
```

## Configuration

All settings are in `scripts/config.py`:

### Camera Settings
- **RTSP_URL**: Your camera's RTSP stream URL
  - Format: `rtsp://username:password@ip:port/path`
  - Example: `rtsp://admin:admin@192.168.1.79:554/cam/realmonitor?channel=1&subtype=0`

### Detection Settings
- **ROI_NORM**: Region of interest (normalized 0-1)
  - Format: `(x1, y1, x2, y2)`
  - Default: `(0.25, 0.34, 0.62, 0.72)` - center area of frame
  - Tip: Only detect birds in feeder area to reduce false positives

- **CONF_THRESH**: YOLO confidence threshold (0-1)
  - Default: `0.25`
  - Lower = more detections (more false positives)
  - Higher = fewer detections (may miss birds)

- **MIN_AREA_RATIO**: Minimum bird size as % of ROI
  - Default: `0.002` (0.2%)
  - Filters out tiny detections

### Capture Settings
- **CAPTURE_GAP_SEC**: Minimum seconds between captures
  - Default: `15`
  - Prevents duplicate photos of same bird

- **BIRD_ABSENCE_TIMEOUT**: Seconds to wait before bird "leaves"
  - Default: `5`
  - Resets detection state

- **DETECTION_INTERVAL**: Seconds between YOLO checks
  - Default: `0.5`
  - Lower = more CPU usage, faster detection

### Display Settings
- **VIEW_SCALE**: Preview window scale factor
  - Default: `0.6` (60% of original size)
  - Adjust for your screen size

### AI Settings
- **OPENAI_API_KEY**: Your OpenAI API key
  - Required for species identification
  - Get from: https://platform.openai.com/api-keys

- **MODEL_PATH**: YOLO model file
  - Default: `yolov8n.pt` (nano model - fast)
  - Alternatives: `yolov8s.pt`, `yolov8m.pt` (more accurate, slower)

## Requirements

### System Requirements
- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **4GB+ RAM** (YOLO model)
- **Network camera** with RTSP support

### Python Dependencies
```
opencv-python>=4.8.0      # Video processing
ultralytics>=8.0.0        # YOLOv8 detection
openai>=1.0.0            # Species identification
numpy>=1.24.0            # Numerical operations
```

### npm Dependencies
```
react, react-dom          # UI framework
@supabase/supabase-js    # Backend (unused in this setup)
lucide-react             # Icons
vite                     # Build tool
tailwindcss              # Styling
typescript               # Type safety
```

## Usage

### Starting the System
1. Download/clone the project
2. Run `START_BIRD_TRACKER.cmd` (Windows) or `./START_BIRD_TRACKER.sh` (Mac/Linux)
3. Enter OpenAI API key when prompted (or skip)
4. Dashboard opens automatically at http://localhost:8080

### Monitoring
- **Live Preview**: Watch the "Bird Counter" window for real-time detection
- **Dashboard**: View visit history and species counts
- **Logs**: Check `pilot_logs/` for detailed debug info
- **Reports**: Browse `public/pilot_reports/` for individual visit analysis

### Stopping
- Press Ctrl+C in main window
- Close all command/terminal windows
- Or on Linux: `kill <PID>` (PIDs shown at startup)

## How It Works

### 1. Bird Detection
- YOLOv8 scans the configured ROI every 0.5 seconds
- When a bird is detected with confidence > 0.25:
  - Checks minimum size threshold
  - Draws bounding box on preview
  - Updates detection state

### 2. Visit Logic
- New visit triggered when:
  - Bird detected after 5+ seconds of absence
  - Or 15+ seconds since last capture
- Captures full-resolution image
- Increments daily unique count

### 3. AI Analysis
- Analyzer picks up new image
- Runs YOLO to verify bird and get bounding box
- Crops to bird region (+ 10% margin)
- Resizes to 512px for OpenAI
- Sends to GPT-4o-mini with prompt:
  - "Analyze this bird feeder image"
  - "Return JSON with: birds_present, count, species_guess, summary"
- Parses response and extracts species

### 4. Metrics Update
- Computes SHA1 hash of image as unique ID
- Checks for duplicates in existing metrics
- Normalizes species name (singular, lowercase)
- Creates visit entry with:
  - Timestamp
  - Species (raw and normalized)
  - Summary text
  - Links to photo and report
- Updates species counts
- Saves to `metrics.json`
- Regenerates dashboard HTML

### 5. Dashboard Display
- React app fetches `metrics.json`
- Displays total visits
- Shows species breakdown (sorted by count)
- Lists all visits in table with:
  - Timestamp
  - Species (hover for raw identification)
  - Summary
  - Links to photo and detailed report
- Auto-refreshes every 30 seconds

## Customization

### Adjusting Detection Region
1. Run the counter: `python scripts/pilot_bird_counter_fixed.py`
2. Observe the live preview
3. Note where your feeder is in the frame
4. Edit `config.py` ROI_NORM to match:
   - Values are 0-1 normalized coordinates
   - (x1, y1) = top-left corner
   - (x2, y2) = bottom-right corner
   - Example: Left half = (0, 0, 0.5, 1)

### Changing Capture Frequency
- More frequent: Lower `CAPTURE_GAP_SEC` (e.g., 10)
- Less frequent: Raise `CAPTURE_GAP_SEC` (e.g., 30)

### Improving Species Accuracy
- Use better YOLO model: Change `MODEL_PATH` to `yolov8s.pt` or `yolov8m.pt`
- Adjust OpenAI prompt in the code
- Increase image quality (modify crop/resize in `openai_analyze_image`)

### Custom Dashboard
- Edit `src/App.tsx` to modify layout/styling
- Run `npm run build` to rebuild
- Or just edit `public/dashboard.html` directly (generated file)

## Troubleshooting

### No Camera Connection
- Verify RTSP_URL is correct
- Test URL in VLC: Media → Open Network Stream
- Check camera is on same network
- Try different subtype (0 or 1)

### No Birds Detected
- Check live preview window - is feeder visible?
- Adjust ROI_NORM to cover feeder area
- Lower CONF_THRESH to 0.15-0.20
- Ensure feeder area is well-lit

### OpenAI Errors
- Verify API key is correct: https://platform.openai.com/api-keys
- Check account has credits
- Monitor rate limits (60 requests/min for free tier)

### Dashboard Shows Wrong Data
- Delete `public/metrics.json` and restart
- Check `public/pilot_reports/` for analysis results
- Review `pilot_logs/` for errors

### High CPU Usage
- Increase DETECTION_INTERVAL (e.g., 1.0)
- Use smaller YOLO model (yolov8n.pt)
- Reduce VIEW_SCALE
- Lower camera resolution in RTSP URL

## Tips & Best Practices

1. **Initial Setup**: Run for 30 minutes to verify detection works before leaving overnight
2. **API Costs**: OpenAI costs ~$0.01 per 100 images (GPT-4o-mini)
3. **Storage**: Expect ~500KB per capture, plan disk space accordingly
4. **Lighting**: Best results in daylight or with good artificial lighting
5. **Positioning**: Mount camera to have feeder fill 40-70% of frame
6. **Testing**: Use `scripts/test_logic.py` to test detection on sample images

## Advanced Features

### Running in Background (Linux)
```bash
# Start all processes as daemons
nohup python3 scripts/pilot_bird_counter_fixed.py > counter.log 2>&1 &
nohup python3 scripts/pilot_analyze_captures_fixed.py --watch > analyzer.log 2>&1 &
cd public && nohup python3 -m http.server 8080 > server.log 2>&1 &
```

### Automatic Startup (Windows)
1. Create shortcut to `START_BIRD_TRACKER.cmd`
2. Move to: `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`

### Remote Access
Forward port 8080 on your router to access dashboard from anywhere.

### Data Export
`metrics.json` is standard JSON - import to Excel, Python pandas, etc.

## Credits

- **YOLOv8** by Ultralytics - Object detection
- **OpenAI GPT-4o-mini** - Species identification
- **React** - Dashboard framework
- **TailwindCSS** - Styling
- **Lucide** - Icons

## License

This is an educational/personal project. Modify as needed!

## Support

For issues:
1. Check `pilot_logs/` for error messages
2. Review configuration in `scripts/config.py`
3. Test camera connection independently (VLC, etc.)
4. Verify Python/npm versions meet requirements
