# Bird Tracker - Quick Start (5 Minutes)

Get your bird tracking system running in 5 minutes!

## Step 1: Get Service Role Key (1 minute)

1. Go to https://supabase.com/dashboard/project/vaaumrjhueoprnjstfmq/settings/api
2. Find "Project API keys" section
3. Copy the **service_role** key (the long one, NOT the anon key)
4. Open `.env` file in this project
5. Replace `<get-from-supabase-dashboard>` with your key:
   ```
   SUPABASE_SERVICE_ROLE_KEY=eyJhbGc... (your actual key)
   ```

## Step 2: Create Storage Bucket (30 seconds)

1. Go to https://supabase.com/dashboard/project/vaaumrjhueoprnjstfmq/storage/buckets
2. Click "New bucket"
3. Name: `bird-captures`
4. Public bucket: **ON** ✓
5. Click "Create bucket"

## Step 3: Install Backend (2 minutes)

```bash
cd backend
pip install -r requirements.txt
```

This installs: opencv, YOLO, OpenAI, Supabase, FastAPI

## Step 4: Start Backend (5 seconds)

```bash
python main.py
```

You should see:
```
INFO: Bird detector initialized successfully
INFO: Camera connected successfully
INFO: Starting detection loop
```

**Leave this running!** Open a new terminal for next step.

## Step 5: Start Dashboard (1 minute)

In a **new terminal**:

```bash
npm run dev
```

Visit: **http://localhost:5173**

## Step 6: Test It! (30 seconds)

1. Wave your hand in front of the camera (where your bird feeder is)
2. Watch the backend console - you'll see "Bird detected"
3. After 5 seconds: "Visit completed"
4. Dashboard updates automatically!
5. After ~10 seconds: OpenAI analyzes the "bird" (your hand)

## What You Should See

### Backend Console:
```
INFO: Visit started: abc-123-def-456
INFO: Captured photo 1/5 for visit abc-123
INFO: Visit completed: abc-123, duration: 7.2s
INFO: Starting analysis for visit abc-123
INFO: Analysis complete: unknown (low confidence)
```

### Dashboard (http://localhost:5173):
- Top row shows 4 green health indicators
- "Visits Today" increases to 1
- New visit appears in "Recent Visits"
- Click the visit to see captured photos

### Supabase Dashboard:
- Go to Table Editor → `visits` → You'll see your visit!
- Go to `captures` → You'll see your photos!
- Go to Storage → `bird-captures` → Your images are there!

## Troubleshooting

### Backend Error: "Camera not connected"

Your RTSP URL might be wrong. Test it:
```bash
ffplay rtsp://admin:admin@192.168.1.79:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif
```

If that doesn't work, check:
- Camera IP address (is it still 192.168.1.79?)
- Camera credentials (admin/admin)
- Camera is on the same network

### Backend Error: "Failed to write to database"

Your service role key is wrong. Double-check:
1. Copied the **service_role** key (not anon key)
2. No extra spaces before/after in `.env` file
3. Key starts with `eyJhbG...`

### Dashboard Shows "Connection Error"

Backend isn't running. Make sure:
1. Backend is running (`python main.py`)
2. No errors in backend console
3. Port 8000 isn't blocked

### No Detections Happening

ROI (Region of Interest) might not match your feeder location. In `.env`, try:
```
# Use full frame
ROI_X1=0.0
ROI_Y1=0.0
ROI_X2=1.0
ROI_Y2=1.0

# Lower confidence
CONFIDENCE_THRESHOLD=0.15
```

Restart backend after changing `.env`.

## Next Steps

1. **Let it run** for a few hours to collect real bird data
2. **Adjust ROI** to focus on your feeder
3. **Review species IDs** - OpenAI is pretty good but not perfect
4. **Check health** at http://localhost:8000/health

## Files You Need to Know

- **`.env`** - All configuration (camera URL, API keys, thresholds)
- **`backend/main.py`** - Start here to modify backend logic
- **`src/App.tsx`** - Start here to modify dashboard
- **`SETUP_INSTRUCTIONS.md`** - Detailed troubleshooting
- **`BIRD_TRACKER_PRD.md`** - Complete system documentation

## Production Deployment

When ready to deploy 24/7:

**Backend**: Deploy to Railway.app (free tier, auto-restart, logs)
**Frontend**: Deploy to Vercel (free tier, instant updates, CDN)

See `SETUP_INSTRUCTIONS.md` for deployment instructions.

## That's It!

You now have a fully functional AI-powered bird tracking system. Enjoy watching your feathered friends!

---

**Need help?** Check `SETUP_INSTRUCTIONS.md` for detailed troubleshooting.

**Want to understand how it works?** Read `IMPLEMENTATION_COMPLETE.md`.

**Want ALL the details?** Read `BIRD_TRACKER_PRD.md` (comprehensive).
