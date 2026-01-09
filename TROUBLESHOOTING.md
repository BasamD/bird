# Troubleshooting Guide

## Logging to File

**NEW:** The startup script now logs everything to `startup_log.txt`

Every time you run `START_BIRD_TRACKER.cmd`, it creates a detailed log file showing:
- Timestamps for when it started
- Every step of the process
- All output from commands (Python, npm, etc.)
- Any errors that occurred
- When the server stopped

**To view the log:**
```cmd
VIEW_LOG.cmd
```

Or just open `startup_log.txt` in Notepad.

**If the window closes too fast:**
```cmd
KEEP_WINDOW_OPEN.cmd
```
This wrapper keeps the window open even after the script finishes.

## START_BIRD_TRACKER.cmd Window Closes Immediately

The startup script has been **completely rewritten** with verbose logging and file logging. Now you'll see:

1. **Detailed progress** at every step
2. **Clear error messages** if something fails
3. **Window stays open** when errors occur (automatic `pause`)
4. **Helpful instructions** for fixing each issue

### What Changed

**Before**: Window closed immediately on error
**After**: Shows exactly where it failed and how to fix it

### New Features

✅ Shows Python and npm locations
✅ Displays what packages are being installed
✅ Clear error boxes with solutions
✅ Progress indicators (1/8, 2/8, etc.)
✅ Windows stay open on errors

## Diagnostic Tool

Run this to check your entire setup:

```cmd
DIAGNOSE_STARTUP.cmd
```

This will check:
1. Python installation and location
2. pip functionality
3. Node.js and npm
4. Python packages (opencv, ultralytics, openai, etc.)
5. Project files
6. npm dependencies
7. OpenAI API key

**Press Enter** after each check to proceed to the next.

## Common Issues and Fixes

### Issue 1: Python Not Found

**Error Message:**
```
ERROR: Python is NOT installed or not in PATH
```

**Solution:**
1. Install Python from https://www.python.org/downloads/
2. **Important:** Check "Add Python to PATH" during installation
3. Restart your terminal/CMD
4. Run `DIAGNOSE_STARTUP.cmd` to verify

### Issue 2: npm Not Found

**Error Message:**
```
ERROR: npm is NOT installed or not in PATH
```

**Solution:**
1. Install Node.js from https://nodejs.org/
2. Restart your terminal/CMD
3. Run `DIAGNOSE_STARTUP.cmd` to verify

### Issue 3: Python Packages Failed to Install

**Error Message:**
```
ERROR: Failed to install Python packages
```

**Solutions:**
- **Try as Administrator**: Right-click START_BIRD_TRACKER.cmd → Run as Administrator
- **Update pip**:
  ```cmd
  python -m pip install --upgrade pip
  ```
- **Manual install**:
  ```cmd
  cd scripts
  pip install -r requirements.txt
  ```
- **Check internet**: Make sure you're connected to the internet

### Issue 4: OpenAI API Calls Failing

**Error Message:**
```
401 Unauthorized or invalid_api_key
```

**Solution:**
The API key is already hardcoded in multiple locations, but if it's expired:

1. Get a new key from https://platform.openai.com/api-keys
2. Update these files:
   - `.env` (line 2)
   - `scripts/config.py` (line 24-27)

### Issue 5: Camera Not Connecting

**Error Message:**
```
Failed to connect to RTSP camera
```

**Solutions:**
1. Check camera is powered on
2. Verify RTSP URL in `scripts/config.py` (line 17-20)
3. Test camera access from VLC media player
4. Check network connection to camera

### Issue 6: Bird Windows Close Immediately

The new script launches Bird Counter and Bird Analyzer in separate windows with error handling:

- Window title: `[DO NOT CLOSE]`
- Shows clear headers
- Displays error messages if script crashes
- Stays open on errors

**To check what went wrong:**
Look at the window content - it will show the error and stay open

## Log Files

Logs are saved in `pilot_logs/` directory:

```
pilot_logs/
├── bird_counter_YYYY-MM-DD.log
└── bird_analyzer_YYYY-MM-DD.log
```

These contain detailed information about:
- Camera connection attempts
- Bird detections
- OpenAI API calls
- Any errors that occurred

## Manual Testing

### Test OpenAI API Key

```cmd
cd scripts
python test_openai.py
```

This will:
- Load the API key
- Make a test call to OpenAI
- Show if the key is working
- Display helpful error messages

### Test Python Scripts Individually

**Test Bird Counter:**
```cmd
cd scripts
python pilot_bird_counter_fixed.py
```

**Test Bird Analyzer:**
```cmd
cd scripts
python pilot_analyze_captures_fixed.py --watch
```

Press `Ctrl+C` to stop each script.

## Getting More Information

### Verbose Mode

The main startup script is already verbose. For even more details, check the log files in `pilot_logs/`.

### Script Locations

| Script | Purpose |
|--------|---------|
| `START_BIRD_TRACKER.cmd` | Main startup script (FIXED with verbose logging) |
| `DIAGNOSE_STARTUP.cmd` | Check all requirements (NEW) |
| `START_BIRD_TRACKER_VERBOSE.cmd` | Alternative verbose version |
| `DIAGNOSE.cmd` | System diagnostics |

## Still Having Issues?

1. **Run diagnostic**: `DIAGNOSE_STARTUP.cmd`
2. **Check logs**: `pilot_logs/` folder
3. **Test API key**: `python scripts/test_openai.py`
4. **Try manual steps**: See Quick Start Guide

## What the Fixed Script Does

### Step-by-Step Process

```
1. Change to project directory (with error check)
2. Enable delayed expansion (with error check)
3. Check Python installation (shows location)
4. Check npm installation (shows version)
5. Install Python packages (shows progress)
6. Check/ask for OpenAI API key
7. Install npm dependencies (if needed)
8. Create metrics.json (if missing)
9. Build dashboard
10. Launch Bird Counter (new window with error handling)
11. Launch Bird Analyzer (new window with error handling)
12. Start HTTP server (shows URL)
```

**Each step has:**
- Clear progress indicator
- Detailed error messages
- Instructions to fix issues
- Automatic pause on errors

## Quick Reference

### ✅ Good Signs
- "Python found: Python 3.x.x"
- "npm found: x.x.x"
- "Python packages installed successfully"
- "Bird detection scripts launched successfully"
- Browser opens to http://localhost:8080

### ❌ Bad Signs
- Window closes immediately → Run DIAGNOSE_STARTUP.cmd
- "ERROR: Python is NOT installed" → Install Python
- "ERROR: npm is NOT installed" → Install Node.js
- "401 Unauthorized" → Check OpenAI API key
- Red error boxes → Read the message and follow instructions

## File Structure Reference

```
project/
├── START_BIRD_TRACKER.cmd         ← Main startup (FIXED - verbose logging)
├── DIAGNOSE_STARTUP.cmd           ← NEW diagnostic tool
├── TROUBLESHOOTING.md             ← This file
├── .env                           ← OpenAI API key
├── scripts/
│   ├── config.py                  ← Config with API key
│   ├── requirements.txt           ← Python dependencies
│   ├── pilot_bird_counter_fixed.py
│   ├── pilot_analyze_captures_fixed.py
│   └── test_openai.py             ← NEW API key tester
└── pilot_logs/                    ← Log files
    ├── bird_counter_YYYY-MM-DD.log
    └── bird_analyzer_YYYY-MM-DD.log
```

## Success Indicators

When everything is working, you'll see:

1. ✅ Python found with version
2. ✅ npm found with version
3. ✅ Python packages installed (shows progress)
4. ✅ API key found or entered
5. ✅ npm dependencies installed
6. ✅ Dashboard built
7. ✅ Two new windows open (Bird Counter, Bird Analyzer)
8. ✅ Browser opens to dashboard
9. ✅ HTTP server running on port 8080

The dashboard should show bird visits as they occur!
