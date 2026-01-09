# Start Here - Troubleshooting Startup Issues

## Problem

You're seeing nothing in the CMD window or log file when running START_BIRD_TRACKER.cmd.

## Solution: Use the Diagnostic Scripts

I've created several test scripts to help identify the problem.

## Step 1: Verify CMD Scripts Work

**Run this first:**
```cmd
TEST_BASIC.cmd
```

**What it does:**
- Tests if CMD scripts work at all on your system
- Tests if files can be created
- Shows current directory
- Keeps window open

**Expected output:**
```
================================
BASIC TEST
================================

If you can see this, CMD scripts work!

Current directory: C:\...\your-project
Script location: C:\...\your-project\
Creating test.txt file...
SUCCESS: test.txt was created
test.txt cleaned up

================================
Test Complete
================================

Press any key to continue . . .
```

**If you see nothing:**
- The .cmd file isn't running at all
- Try: Right-click → "Run as Administrator"
- Try: Open CMD first, then drag the .cmd file into it

## Step 2: Test Logging System

**Run this:**
```cmd
TEST_LOG.cmd
```

**What it does:**
- Tests if the logging system works
- Creates `test_startup_log.txt`
- Shows output on screen

**Expected output:**
```
Testing logging system...
Step 1: Testing basic echo
Step 2: Current directory is C:\...
Step 3: Checking Python

================================
Test completed!
================================
Check test_startup_log.txt to see if logging worked

Press any key to continue . . .
```

**Then check:**
- Does `test_startup_log.txt` exist?
- Open it - does it have content?

## Step 3: Test Requirements

**Run this:**
```cmd
START_SIMPLE.cmd
```

**What it does:**
- Checks if Python is installed
- Checks if npm is installed
- Checks if scripts directory exists
- Creates `startup_log.txt`
- Shows everything on screen
- Keeps window open

**This is the most useful diagnostic tool!**

**Expected output:**
```
================================
Bird Tracker - SIMPLE VERSION
================================
...
[Step 1] Changing to project directory...
[Step 2] Checking for Python...
[Step 3] Checking for npm...
[Step 4] Checking scripts directory...
...
```

**If Python or npm are missing:**
- The script will tell you clearly
- Install the missing software
- Run again

## Step 4: Run Full Startup (Window Stays Open)

**Run this:**
```cmd
KEEP_WINDOW_OPEN.cmd
```

**What it does:**
- Runs the full START_BIRD_TRACKER.cmd
- Forces window to stay open
- You can see all output
- Even if it succeeds, window stays open

## What's Wrong?

### Symptom: Window flashes and disappears

**Cause:** Script error or missing requirement

**Solution:**
1. Run `START_SIMPLE.cmd`
2. It will show you the exact error
3. Window stays open

### Symptom: Nothing happens when double-clicking

**Cause:** File association issue

**Solution:**
1. Right-click the .cmd file
2. Choose "Open" or "Run as Administrator"
3. Or: Open CMD first, then run the script:
   ```cmd
   cd C:\path\to\project
   START_SIMPLE.cmd
   ```

### Symptom: No log files created

**Cause:** Script never ran, or file permission issue

**Solution:**
1. Run `TEST_BASIC.cmd` to verify file creation works
2. Try running as Administrator
3. Check antivirus isn't blocking

### Symptom: Empty log file

**Cause:** Script failed before first log write

**Solution:**
1. Run `START_SIMPLE.cmd`
2. The `pause` commands will keep window open
3. You'll see exactly where it fails

## Files Reference

| File | Purpose | Window Stays Open? |
|------|---------|-------------------|
| `TEST_BASIC.cmd` | Test if CMD works at all | ✅ Yes |
| `TEST_LOG.cmd` | Test logging system | ✅ Yes |
| `START_SIMPLE.cmd` | Test requirements, show errors | ✅ Yes |
| `KEEP_WINDOW_OPEN.cmd` | Run full startup, keep window open | ✅ Yes |
| `START_BIRD_TRACKER.cmd` | Normal startup | ❌ Closes on error |
| `VIEW_LOG.cmd` | View the log file | ✅ Yes |

## Recommended Order

Run these in order until one fails:

1. **TEST_BASIC.cmd** - Does CMD work?
2. **TEST_LOG.cmd** - Does logging work?
3. **START_SIMPLE.cmd** - Are requirements met?
4. **KEEP_WINDOW_OPEN.cmd** - Does full startup work?

## Getting Help

If you're still stuck, run **START_SIMPLE.cmd** and report:

1. **Everything shown in the window** (take a screenshot or copy the text)
2. **Contents of startup_log.txt** (if it exists)
3. **Your Python version:**
   ```cmd
   python --version
   ```
4. **Your npm version:**
   ```cmd
   npm --version
   ```

## Quick Fix Checklist

- [ ] Ran TEST_BASIC.cmd - window stays open, shows success
- [ ] Ran TEST_LOG.cmd - creates test_startup_log.txt
- [ ] Ran START_SIMPLE.cmd - shows Python and npm versions
- [ ] Python is installed and in PATH
- [ ] npm/Node.js is installed and in PATH
- [ ] scripts directory exists and has .py files
- [ ] Running from correct directory (where the .cmd files are)
- [ ] startup_log.txt is being created

## Bottom Line

**START_SIMPLE.cmd is your best friend.** It shows everything and keeps the window open.

Run it first to see what's actually happening.
