# Quick Start Guide

## 30-Second Setup

```bash
# 1. Install dependencies
cd scripts
pip install -r requirements.txt

# 2. Set API key
export OPENAI_API_KEY="sk-your-key-here"

# 3. Run the script
python pilot_bird_counter_fixed.py
```

That's it! The script will:
- Connect to your camera
- Detect birds automatically
- Save images and generate reports
- Update the dashboard in real-time

Press 'q' to quit.

---

## Common Commands

### Real-time Camera Capture
```bash
python pilot_bird_counter_fixed.py
```

### Analyze Existing Images
```bash
# Single pass
python pilot_analyze_captures_fixed.py --root /path/to/images

# Watch mode (continuous)
python pilot_analyze_captures_fixed.py --root /path/to/images --watch
```

### Run Tests
```bash
python test_logic.py
```

---

## Quick Configuration

Set environment variables to customize behavior:

```bash
# Camera
export RTSP_URL="rtsp://user:pass@192.168.1.79:554/cam/..."

# Paths (optional, defaults to ../pilot_*)
export CAPTURE_ROOT="/path/to/captures"
export REPORT_ROOT="/path/to/reports"
export DASHBOARD_DIR="/path/to/public"

# Detection tuning
export CONF_THRESH="0.25"           # Lower = more sensitive
export MIN_AREA_RATIO="0.002"       # Filter tiny detections
```

---

## Troubleshooting

### "OpenAI disabled"
```bash
export OPENAI_API_KEY="sk-your-key"
```

### "Failed to open RTSP stream"
Check camera URL and credentials. Test with:
```bash
ffplay "rtsp://user:pass@ip:port/path"
```

### "No module named 'cv2'"
```bash
pip install opencv-python
```

### Detection not working well
Adjust sensitivity:
```bash
# More sensitive (catch more birds, more false positives)
export CONF_THRESH="0.20"
export MIN_AREA_RATIO="0.001"

# Less sensitive (fewer false positives, might miss birds)
export CONF_THRESH="0.35"
export MIN_AREA_RATIO="0.005"
```

---

## What's Next?

- 📖 Read `SETUP_GUIDE.md` for detailed instructions
- 🐛 See `BUGFIXES.md` to understand what was fixed
- 📊 Check `SUMMARY.md` for the complete analysis
- 🧪 Run `test_logic.py` to validate your setup

---

## File Overview

| File | Purpose |
|------|---------|
| `pilot_bird_counter_fixed.py` | Real-time camera capture |
| `pilot_analyze_captures_fixed.py` | Batch image analysis |
| `config.py` | Configuration system |
| `requirements.txt` | Python dependencies |
| `test_logic.py` | Logic tests |
| `SETUP_GUIDE.md` | Complete setup guide |
| `BUGFIXES.md` | All bugs fixed |
| `SUMMARY.md` | Executive summary |

---

## Support

Having issues? Check these in order:
1. Logs in `../pilot_logs/pilot_*.log`
2. `SETUP_GUIDE.md` troubleshooting section
3. `BUGFIXES.md` known issues
4. Run `test_logic.py` to identify problems
