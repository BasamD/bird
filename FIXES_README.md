# Bird Tracker Fixes - Data Validation & API Key Issues

## Problems Fixed

### 1. **Invalid OpenAI API Key**
Your OpenAI API key is invalid (returning 401 errors). This was causing all bird identifications to fail.

**Solution:**
- Get a new API key from https://platform.openai.com/api-keys
- Update the `OPENAI_API_KEY` in your `.env` file
- The script now validates the API key at startup and gives a clear error message

### 2. **No Data Validation**
The script was marking images as "processed" even when the data failed to save to `metrics.json` and `dashboard.html`.

**Solution:**
- Added validation to verify data is actually written to disk
- Uses atomic write operations (write to temp file, then move)
- Throws an error if save fails, preventing the image from being marked as processed
- Detailed logging shows exactly where files are being saved

### 3. **Silent Failures**
Errors were being logged but not preventing continued processing with bad data.

**Solution:**
- API key is now validated at startup
- File writes are verified before marking images as processed
- Clear error messages guide you to the problem

## How to Fix Your Setup

### Step 1: Run the Diagnostic Script
```bash
cd C:\bird-main\scripts
python diagnose_setup.py
```

This will check:
- File paths and permissions
- OpenAI API key status
- Current metrics data
- Dashboard file status

### Step 2: Fix Your OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Create a new API key (or verify your existing one works)
3. Open `C:\bird-main\.env`
4. Update this line:
   ```
   OPENAI_API_KEY=your-new-key-here
   ```
5. Save the file

### Step 3: Clear the "Already Processed" Cache
The images are marked as "already processed" but weren't saved to the dashboard. To reprocess them:

**Option A: Delete the metrics file (resets everything)**
```bash
del C:\bird-main\public\metrics.json
```

**Option B: Manually remove just today's entries**
1. Open `C:\bird-main\public\metrics.json`
2. Remove entries from today (2026-01-09) from the "visits" array
3. Update the "total_visits" count
4. Update the "species_counts" as needed

### Step 4: Restart the Analyzer
```bash
cd C:\bird-main
START_BIRD_TRACKER.cmd
```

## What Changed in the Code

### File: `pilot_analyze_captures_fixed.py`

1. **`save_metrics()` function**
   - Now returns `True` or `False` to indicate success
   - Writes to a temp file first
   - Verifies the data was written correctly
   - Atomically moves temp file to final location
   - Detailed error logging with full file paths

2. **`write_dashboard_html()` function**
   - Now returns `True` or `False` to indicate success
   - Writes to a temp file first
   - Verifies file was created and isn't empty
   - Atomically moves temp file to final location
   - Detailed success/error logging

3. **`update_metrics()` function**
   - Checks return values from save functions
   - Throws `RuntimeError` if save fails
   - Prevents image from being marked as processed if data isn't saved

4. **`validate_openai_api_key()` function (NEW)**
   - Tests API key at startup
   - Makes a minimal API call to verify it works
   - Gives clear error messages if key is invalid
   - Disables OpenAI if validation fails (prevents spam errors)

5. **`main()` function**
   - Calls API key validation at startup
   - Shows prominent error message if API key is invalid
   - Warns that bird identification won't work

## Expected Behavior After Fixes

### Startup
```
[INFO] Pilot analyzer starting
[INFO] Folder: C:\bird-main\public\pilot_captures
[INFO] [OpenAI] API key validation successful
[INFO] Watch mode enabled
```

### When Processing an Image
```
[INFO] birds=1 unique_today=1 unique=True report=C:\bird-main\public\pilot_reports\2026-01-09\bird_1.html
[INFO] [metrics] saved successfully: 1 visits, file: C:\bird-main\public\metrics.json
[INFO] [dashboard] written successfully: C:\bird-main\public\dashboard.html
```

### If Save Fails
```
[ERROR] [metrics] FAILED to save metrics to C:\bird-main\public\metrics.json: [Permission denied]
[ERROR] process_one fatal:
RuntimeError: Failed to save data to: metrics.json. Data may be lost!
```

## Verifying the Fix

1. **Check metrics.json has data:**
   ```bash
   type C:\bird-main\public\metrics.json
   ```
   Should show visits, species_counts, etc.

2. **Check dashboard.html is updating:**
   - Open `http://localhost:5173/dashboard.html` in your browser
   - Should show today's date (2026-01-09) visits
   - Should refresh every 30 seconds

3. **Check logs for errors:**
   ```bash
   type C:\bird-main\pilot_logs\pilot_analyzer_2026-01-09.log
   ```

## Still Having Issues?

Run the diagnostic script again:
```bash
python diagnose_setup.py
```

Check for:
- File permission errors
- Disk space issues
- Antivirus blocking file writes
- Path problems (ensure all paths exist and are writable)

The detailed logging will now show exactly where files are being written and why they might be failing.
