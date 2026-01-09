# Debug Steps for Startup Script

## Problem: Nothing shows in cmd window or log file

This means the script is failing very early, possibly before the logging even starts.

## Test Scripts Created

I've created test scripts to help diagnose the issue:

### 1. START_SIMPLE.cmd (Recommended)
**What it does:**
- Simplified version of the full startup
- Shows ALL output on screen
- Keeps window open with `pause` commands
- Creates a log file
- Checks Python, npm, and scripts directory
- Does NOT start the actual bird tracker

**How to use:**
```cmd
START_SIMPLE.cmd
```

**What to expect:**
- Window stays open
- You'll see each step
- Press any key to continue between steps
- Creates `startup_log.txt`
- Tells you if basic requirements are met

### 2. TEST_LOG.cmd
**What it does:**
- Very simple logging test
- Just tests if file logging works
- Creates `test_startup_log.txt`

**How to use:**
```cmd
TEST_LOG.cmd
```

### 3. KEEP_WINDOW_OPEN.cmd
**What it does:**
- Runs the full START_BIRD_TRACKER.cmd
- Forces window to stay open at the end

**How to use:**
```cmd
KEEP_WINDOW_OPEN.cmd
```

## Step-by-Step Diagnosis

### Step 1: Test Basic Logging
```cmd
TEST_LOG.cmd
```

**Expected result:**
- Window appears and stays open
- You see "Step 1", "Step 2", "Step 3"
- Press any key to close
- File `test_startup_log.txt` is created

**If this fails:**
- You're in the wrong directory
- Your system has restricted file permissions
- Try running as Administrator

### Step 2: Test Basic Requirements
```cmd
START_SIMPLE.cmd
```

**Expected result:**
- Window appears
- Shows Python version (if installed)
- Shows npm version (if installed)
- Lists files in scripts directory
- Keeps window open
- Creates `startup_log.txt`

**If Python check fails:**
- Python is not installed
- Python is not in PATH
- Solution: Install Python from python.org

**If npm check fails:**
- Node.js is not installed
- npm is not in PATH
- Solution: Install Node.js from nodejs.org

### Step 3: Run Full Startup (Keep Window Open)
```cmd
KEEP_WINDOW_OPEN.cmd
```

**Expected result:**
- Runs the full startup
- Window stays open even if it succeeds
- You can read all output
- Creates `startup_log.txt`

### Step 4: Check the Log File
After running any of the above:

```cmd
notepad startup_log.txt
```

Or:
```cmd
VIEW_LOG.cmd
```

## Common Issues

### Issue 1: Window Flashes and Closes Immediately

**Cause:** Script has a syntax error or is hitting an error before any output

**Solution:**
1. Run `START_SIMPLE.cmd` instead
2. It will show you exactly where it fails
3. Window stays open with `pause` commands

### Issue 2: No Log File Created

**Possible causes:**
- Script never ran
- File permissions issue
- Wrong directory

**Solution:**
1. Right-click `START_BIRD_TRACKER.cmd`
2. Choose "Edit" (opens in Notepad)
3. Look at line 4: `set "LOGFILE=%~dp0startup_log.txt"`
4. This should create the log in the same folder as the script

### Issue 3: Log File is Empty

**Cause:** Script fails before first write to log

**Solution:**
1. Run `TEST_LOG.cmd` to verify logging works at all
2. If that works, the problem is in the main script
3. Check if Python/npm are missing

### Issue 4: Script Runs But Nothing Happens

**Cause:** Script is waiting for input you can't see

**Solution:**
1. Run `KEEP_WINDOW_OPEN.cmd`
2. This shows all output and prompts
3. Look for prompts asking for API keys or other input

## Quick Diagnostic Checklist

Run these commands in order and note where it fails:

```cmd
REM Test 1: Does basic logging work?
TEST_LOG.cmd

REM Test 2: Are Python and npm installed?
START_SIMPLE.cmd

REM Test 3: Does full startup work?
KEEP_WINDOW_OPEN.cmd

REM Test 4: Can you view the log?
VIEW_LOG.cmd
```

## Manual Command Test

If all the above fail, try running commands manually:

```cmd
REM Open Command Prompt
REM Navigate to project directory
cd /d C:\path\to\your\project

REM Test Python
python --version

REM Test npm
npm --version

REM Test file creation
echo test > test.txt

REM Check if file was created
dir test.txt
```

## What to Report

If you're still stuck, please report:

1. **Which test script did you run?**
   - TEST_LOG.cmd
   - START_SIMPLE.cmd
   - KEEP_WINDOW_OPEN.cmd
   - START_BIRD_TRACKER.cmd

2. **What happened?**
   - Window flashed and closed
   - Window stayed open with error
   - Nothing happened at all

3. **What files were created?**
   - startup_log.txt exists? (yes/no)
   - test_startup_log.txt exists? (yes/no)
   - If yes, what's inside?

4. **Python and npm installed?**
   ```cmd
   python --version
   npm --version
   ```

5. **Contents of startup_log.txt** (if it exists)
   - Copy and paste the entire file

## Expected Behavior (When Working)

### TEST_LOG.cmd
```
Testing logging system...
Step 1: Testing basic echo
Step 2: Current directory is C:\...\project
Step 3: Checking Python

================================
Test completed!
================================
Check test_startup_log.txt to see if logging worked

Press any key to continue . . .
```

### START_SIMPLE.cmd
```
================================
Bird Tracker - SIMPLE VERSION
================================

This version shows everything on screen
and keeps the window open.

Press any key to continue . . .

Creating log file: C:\...\project\startup_log.txt
Log file created successfully

[Step 1] Changing to project directory...
Current directory: C:\...\project

[Step 2] Checking for Python...
Python 3.11.5
C:\Python311\python.exe
Python found successfully

[Step 3] Checking for npm...
10.2.3
npm found successfully

[Step 4] Checking scripts directory...
scripts directory found

Files in scripts directory:
config.py
pilot_bird_counter_fixed.py
pilot_analyze_captures_fixed.py
[... more files ...]

================================
All basic checks passed!
================================

Next steps:
1. Check startup_log.txt
2. If everything looks good, run START_BIRD_TRACKER.cmd

Log saved to: C:\...\project\startup_log.txt

Press any key to continue . . .
```

## Bottom Line

**Start with START_SIMPLE.cmd** - it will tell you exactly what's wrong and keep the window open so you can read it.
