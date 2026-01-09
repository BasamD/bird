# Startup Logging Guide

## Problem Solved

The startup script was closing before you could see what went wrong. Now **everything is logged to a file**.

## How It Works

Every time you run `START_BIRD_TRACKER.cmd`, it automatically creates/updates:

```
startup_log.txt
```

This file contains:
- ✅ Timestamp of when you ran it
- ✅ Every command executed
- ✅ All output from Python, npm, etc.
- ✅ Error messages (if any)
- ✅ What directory it's in at each step
- ✅ When the server starts/stops

## Viewing the Log

### Option 1: Quick View (Recommended)
```cmd
VIEW_LOG.cmd
```
This displays the entire log file in your terminal.

### Option 2: Open in Notepad
```cmd
notepad startup_log.txt
```

### Option 3: Just Double-Click
Double-click `startup_log.txt` in File Explorer.

## Keeping the Window Open

If the startup window closes before you can read it:

```cmd
KEEP_WINDOW_OPEN.cmd
```

This runs the normal startup script but **forces the window to stay open** at the end, so you can review what happened.

## What the Log Shows

### Example Log (Successful Startup)

```
================================
Bird Tracker Startup Log
Date: 01/09/2026 10:30:45 AM
================================

Changing to project directory...
Project directory: C:\Users\YourName\bird-tracker

[1/8] Checking for Python...
Python found:
Python 3.11.5
C:\Python311\python.exe

[2/8] Checking for npm...
npm found:
10.2.3

[3/8] Installing Python requirements...
Changing to scripts directory...
Current directory: C:\Users\YourName\bird-tracker\scripts
Installing: opencv-python, ultralytics, openai, numpy, python-dotenv
This may take 30-60 seconds...
[pip output...]
Python packages installed successfully

[4/8] Checking OpenAI API key...
OpenAI API key found

[5/8] npm dependencies already installed

[6/8] Initializing metrics file...
metrics.json already exists

[7/8] Building dashboard...
[vite build output...]
Dashboard built successfully

[8/9] Starting bird detection scripts...
Current scripts directory: C:\Users\YourName\bird-tracker\scripts
Checking Python scripts before launching...
Launching Bird Counter in new window...
Launching Bird Analyzer in new window...
Bird detection scripts launched successfully

[9/9] Starting dashboard server...
Dashboard directory: C:\Users\YourName\bird-tracker
Serving from: C:\Users\YourName\bird-tracker\public

================================
STARTUP COMPLETE!
================================
Current serving directory: C:\Users\YourName\bird-tracker\public

Opening browser to http://localhost:8080
Starting HTTP server on port 8080...
Serving HTTP on :: port 8080 (http://[::]:8080/) ...
```

### Example Log (Error)

```
================================
Bird Tracker Startup Log
Date: 01/09/2026 10:35:22 AM
================================

Changing to project directory...
Project directory: C:\Users\YourName\bird-tracker

[1/8] Checking for Python...
Python found:
Python 3.11.5

[2/8] Checking for npm...

ERROR: npm is NOT installed or not in PATH
```

The log stops at the error, showing exactly what went wrong.

## Common Scenarios

### Scenario 1: Window Closes Immediately

**What to do:**
1. Open `startup_log.txt`
2. Look at the last few lines
3. That's where it failed
4. See TROUBLESHOOTING.md for solutions

### Scenario 2: Want to See Full Output

**What to do:**
1. Run `KEEP_WINDOW_OPEN.cmd` instead
2. Window stays open at the end
3. Press any key when done reading
4. Or check `startup_log.txt` for the full log

### Scenario 3: Something Broke Mid-Way

**What to do:**
1. Open `startup_log.txt`
2. Find the last successful step
3. The next section shows the error
4. Copy the error and see TROUBLESHOOTING.md

### Scenario 4: Need to Send Log to Someone

**What to do:**
1. Open `startup_log.txt`
2. Copy all contents (Ctrl+A, Ctrl+C)
3. Paste into email/message
4. Include the entire log for best help

## Log File Location

The log is always in the same folder as the startup script:

```
your-project/
├── START_BIRD_TRACKER.cmd
├── startup_log.txt          ← HERE
├── VIEW_LOG.cmd
└── KEEP_WINDOW_OPEN.cmd
```

## Log File Management

### Does It Overwrite?
**YES** - Each time you run `START_BIRD_TRACKER.cmd`, it creates a fresh log. The old one is replaced.

### Want to Keep Old Logs?
Before running again, rename the current log:
```cmd
copy startup_log.txt startup_log_backup.txt
```

### Log Too Big?
Just delete it. A new one will be created next time:
```cmd
del startup_log.txt
```

## Quick Reference

| File | Purpose |
|------|---------|
| `START_BIRD_TRACKER.cmd` | Main startup script (creates log) |
| `startup_log.txt` | Full log of what happened |
| `VIEW_LOG.cmd` | Quick way to view the log |
| `KEEP_WINDOW_OPEN.cmd` | Run startup but keep window open |

## Tips

1. **Always check the log first** when something goes wrong
2. **Look at the last 10-20 lines** - that's usually where the error is
3. **The log shows everything** - even if the window closed
4. **Use KEEP_WINDOW_OPEN.cmd** if you want to watch it in real-time
5. **The log includes timestamps** so you know when it ran

## Examples of What You'll See

### Successful Package Install
```
[3/8] Installing Python requirements...
Changing to scripts directory...
Current directory: C:\...\scripts
Installing: opencv-python, ultralytics, openai, numpy, python-dotenv
This may take 30-60 seconds...
Requirement already satisfied: opencv-python in ...
Requirement already satisfied: ultralytics in ...
[... more packages ...]
Python packages installed successfully
```

### Failed Package Install
```
[3/8] Installing Python requirements...
Changing to scripts directory...
Current directory: C:\...\scripts
Installing: opencv-python, ultralytics, openai, numpy, python-dotenv
This may take 30-60 seconds...
ERROR: Could not find a version that satisfies the requirement opencv-python
ERROR: Failed to install Python packages
```

### Script Launch
```
[8/9] Starting bird detection scripts...
Current scripts directory: C:\...\scripts
Checking Python scripts before launching...
Launching Bird Counter in new window...
Launching Bird Analyzer in new window...
Bird detection scripts launched successfully
```

### Server Running
```
[9/9] Starting dashboard server...
Dashboard directory: C:\...\bird-tracker
Serving from: C:\...\bird-tracker\public
Opening browser to http://localhost:8080
Starting HTTP server on port 8080...
Serving HTTP on :: port 8080 (http://[::]:8080/) ...
127.0.0.1 - - [09/Jan/2026 10:30:50] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [09/Jan/2026 10:30:51] "GET /metrics.json HTTP/1.1" 200 -
```

## Bottom Line

**You'll never lose information again** because everything is logged to `startup_log.txt`.

If the window closes before you can read it - no problem! Just open the log file.
