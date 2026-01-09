# Bird Feeder Tracker

AI-powered bird feeder monitoring system with real-time species identification and web dashboard.

## Features

- **Real-time Bird Detection** - YOLOv8 computer vision on RTSP camera feed
- **AI Species Identification** - OpenAI GPT-4 Vision analyzes each visitor
- **Live Web Dashboard** - React dashboard with real-time updates
- **Visit Tracking** - Smart logic to track unique bird visits
- **Cloud Storage** - Supabase database and image storage
- **Health Monitoring** - System status and error tracking

## Quick Start

**Get running in 5 minutes:** See [QUICKSTART.md](QUICKSTART.md)

### Prerequisites

- Python 3.8+
- Node.js 16+
- RTSP network camera
- OpenAI API key (already configured in `.env`)
- Supabase account (already set up)

### Installation

1. **Configure Supabase service key** (required)
   - Get your service role key from Supabase dashboard
   - Add it to `.env` file (see QUICKSTART.md)

2. **Create storage bucket** (required)
   - Create `bird-captures` bucket in Supabase
   - Make it public (see QUICKSTART.md)

3. **Install backend dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Install frontend dependencies**
   ```bash
   npm install
   ```

### Running

**Backend** (Terminal 1):
```bash
cd backend
python main.py
```

**Frontend** (Terminal 2):
```bash
npm run dev
```

Visit **http://localhost:5173** to see your dashboard!

## Project Structure

```
backend/           - Python backend service
  ├── main.py           - FastAPI server & main entry point
  ├── bird_detector.py  - YOLO bird detection
  ├── species_analyzer.py - OpenAI species identification
  ├── state_machine.py  - Visit tracking logic
  └── config.py         - Configuration management

src/              - React frontend
  └── App.tsx          - Dashboard UI

supabase/         - Database migrations
  └── migrations/      - SQL schema files

.env              - Configuration (API keys, camera URL, settings)
```

## Configuration

All settings are in `.env`:

- **Camera**: `RTSP_URL` - Your camera's RTSP stream URL
- **OpenAI**: `OPENAI_API_KEY` - API key for species identification
- **Supabase**: Database and storage credentials
- **Detection**: Confidence thresholds, ROI, intervals
- **Visit Logic**: Timeouts, cooldowns, capture limits

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - 5-minute setup guide
- **[SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md)** - Detailed setup and troubleshooting
- **[BIRD_TRACKER_PRD.md](BIRD_TRACKER_PRD.md)** - Complete system documentation

## How It Works

1. **Detection**: YOLO model analyzes camera feed for birds in defined ROI
2. **Visit Start**: First detection starts a new visit (unique ID generated)
3. **Capture**: Photos taken at intervals during the visit
4. **Visit End**: Visit ends after bird leaves (5 second grace period)
5. **Analysis**: OpenAI analyzes photos to identify species
6. **Storage**: Data saved to Supabase, images to cloud storage
7. **Dashboard**: Real-time updates via polling

## Important Files to Keep

The following contain your API keys and settings:
- `.env` - OpenAI API key and RTSP camera URL

## Troubleshooting

### Camera not connecting
- Check RTSP URL in `.env`
- Verify camera is on network
- Test with: `ffplay <your-rtsp-url>`

### No detections
- Adjust ROI settings in `.env` to match feeder location
- Lower `CONFIDENCE_THRESHOLD` (try 0.15)
- Check backend logs for errors

### Database errors
- Verify Supabase service role key in `.env`
- Check bucket `bird-captures` exists and is public
- See SETUP_INSTRUCTIONS.md for details

### Dashboard not updating
- Check backend is running on port 8000
- Check browser console for errors
- Verify API calls to localhost:8000/health work

## License

MIT
