# Bird Tracker - Setup Instructions

This is a comprehensive bird feeder tracking system with AI-powered species identification, real-time monitoring, and a beautiful dashboard.

## System Architecture

- **Backend**: Python service with RTSP camera connection, YOLO bird detection, OpenAI species identification
- **Database**: Supabase PostgreSQL with real-time subscriptions
- **Frontend**: React dashboard with live updates
- **Storage**: Supabase Storage for captured images

## Prerequisites

1. Python 3.8+ installed
2. Node.js 16+ installed
3. RTSP camera accessible on network
4. OpenAI API key
5. Supabase account (free tier is sufficient)

## Step 1: Supabase Setup

### 1.1 Get Service Role Key

1. Go to https://supabase.com/dashboard
2. Open your project: `vaaumrjhueoprnjstfmq`
3. Navigate to Settings → API
4. Copy the `service_role` key (NOT the anon key)
5. Update `.env` file:
   ```bash
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
   ```

### 1.2 Create Storage Bucket

1. In Supabase dashboard, go to Storage
2. Create a new bucket named `bird-captures`
3. Set it to **Public** (so images are accessible)
4. Click "Save"

### 1.3 Verify Database

The database tables have already been created via migration. You should see these tables in your Supabase SQL Editor:
- `visits`
- `captures`
- `species_stats`
- `system_logs`
- `system_health`

## Step 2: Backend Setup

### 2.1 Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This will install:
- opencv-python (camera streaming)
- ultralytics (YOLO detection)
- openai (species identification)
- supabase (database client)
- fastapi (API server)

### 2.2 Download YOLO Model

The YOLO model will download automatically on first run. It downloads `yolov8n.pt` (nano model, ~6MB).

### 2.3 Configure Environment

Edit the `.env` file in the root directory:

```bash
# Update these values:
RTSP_URL=rtsp://admin:admin@192.168.1.79:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif
OPENAI_API_KEY=your-openai-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

**ROI Configuration**: Adjust these if your feeder is in a different part of the frame:
- `ROI_X1`, `ROI_Y1`: Top-left corner (0-1 normalized)
- `ROI_X2`, `ROI_Y2`: Bottom-right corner (0-1 normalized)

### 2.4 Start the Backend

```bash
cd backend
python main.py
```

You should see:
```
INFO: Bird detector initialized successfully
INFO: Camera connected successfully
INFO: Starting detection loop
```

The backend runs on `http://localhost:8000`

## Step 3: Frontend Setup

### 3.1 Install Dependencies

```bash
npm install
```

### 3.2 Start Development Server

```bash
npm run dev
```

The dashboard will be available at `http://localhost:5173`

## Step 4: Verify Everything Works

### 4.1 Check Health Status

Visit http://localhost:8000/health

You should see:
```json
{
  "overall_status": "healthy",
  "components": {
    "camera": { "status": "connected" },
    "detector": { "status": "healthy" },
    "analyzer": { "status": "healthy" },
    "database": { "status": "healthy" }
  }
}
```

### 4.2 Check Dashboard

Open http://localhost:5173

You should see:
- System health indicators at top (all green)
- Real-time visits feed (will be empty initially)
- Species leaderboard (will be empty initially)

### 4.3 Test Bird Detection

1. Wave your hand in front of the camera (in the ROI area)
2. Watch the console output - you should see: `INFO: Bird detected` (it will detect you as a bird!)
3. After 5 seconds, you should see: `INFO: Visit completed`
4. The dashboard should update automatically with the new visit
5. After ~10 seconds, OpenAI will analyze the image and update the species

## Troubleshooting

### Camera Not Connecting

**Error**: `Failed to connect to camera after 10 attempts`

**Solutions**:
1. Verify RTSP URL is correct:
   ```bash
   ffplay rtsp://admin:admin@192.168.1.79:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif
   ```
2. Check network connectivity to camera
3. Verify camera credentials are correct
4. Try changing `subtype=0` to `subtype=1` (lower resolution stream)

### No Birds Detected

**Problem**: Camera works but no detections

**Solutions**:
1. Adjust ROI coordinates in `.env` to match your feeder location
2. Lower confidence threshold: `CONFIDENCE_THRESHOLD=0.15`
3. Increase minimum area: `MIN_AREA_RATIO=0.001`
4. Check console for "Bird detected" messages

### OpenAI API Failures

**Error**: `Failed to analyze visit: 401 Unauthorized`

**Solutions**:
1. Verify API key is correct and active
2. Check OpenAI account has credits
3. System will continue working without species ID (will show "unknown")

### Database Connection Issues

**Error**: `Failed to write to database`

**Solutions**:
1. Verify Supabase service role key is correct
2. Check internet connection
3. Verify database tables exist (run migration again if needed)

### Images Not Showing in Dashboard

**Problem**: Visits appear but no images

**Solutions**:
1. Verify storage bucket `bird-captures` exists and is public
2. Check browser console for CORS errors
3. Verify `STORAGE_BUCKET=bird-captures` in `.env`

## Configuration Tips

### Adjust Detection Sensitivity

For more sensitive detection (catches smaller/farther birds):
```bash
CONFIDENCE_THRESHOLD=0.15
MIN_AREA_RATIO=0.001
```

For less sensitive (only large/close birds):
```bash
CONFIDENCE_THRESHOLD=0.50
MIN_AREA_RATIO=0.005
```

### Adjust Visit Logic

For shorter visits (fast birds):
```bash
ABSENCE_GRACE_PERIOD_SEC=3
VISIT_COOLDOWN_SEC=10
```

For longer visits (slow feeders):
```bash
ABSENCE_GRACE_PERIOD_SEC=10
VISIT_COOLDOWN_SEC=30
```

### Performance Tuning

For lower CPU usage:
```bash
DETECTION_INTERVAL_MS=1000  # 1 detection per second instead of 2
```

For faster response:
```bash
DETECTION_INTERVAL_MS=250  # 4 detections per second
```

## API Endpoints

- `GET /` - Service info
- `GET /health` - System health status
- `GET /visits/recent?limit=20` - Recent visits
- `GET /visits/{visit_id}` - Visit details with captures
- `GET /stats/species` - Species statistics
- `GET /stats/today` - Today's statistics

## Dashboard Features

- **Real-time Updates**: Automatically updates when new birds are detected
- **System Health**: Shows status of all components
- **Visit History**: Click any visit to see detailed information and photos
- **Species Leaderboard**: See which species visit most often
- **Statistics**: Daily visit counts and unique species

## Production Deployment

For 24/7 operation:

### Backend (Python Service)

Deploy to:
- Railway.app (recommended, easiest)
- DigitalOcean Droplet
- AWS EC2
- Any Linux server with Python

Use `systemd` or `supervisor` for auto-restart.

### Frontend (React Dashboard)

Deploy to:
- Vercel (recommended, free)
- Netlify
- Any static hosting

Just run `npm run build` and deploy the `dist` folder.

## Next Steps

1. Let it run for a day to collect data
2. Review species identifications and accuracy
3. Adjust ROI and thresholds as needed
4. Add more cameras (run multiple backend instances)
5. Explore the data in Supabase SQL Editor for custom queries

## Support

Check these files for more details:
- `BIRD_TRACKER_PRD.md` - Complete product requirements
- `PRD_QUICK_START.md` - Quick reference guide
- Backend code in `backend/` folder
- Frontend code in `src/` folder

Enjoy tracking your backyard birds!
