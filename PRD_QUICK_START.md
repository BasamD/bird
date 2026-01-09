# Bird Tracker PRD - Quick Start Guide

## What You Have

A complete Product Requirements Document (PRD) for rebuilding your bird tracking system from scratch.

**File:** `BIRD_TRACKER_PRD.md` (comprehensive, 500+ lines)

---

## Your Credentials (Included in PRD)

### RTSP Camera
```
rtsp://admin:admin@192.168.1.79:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif
```

### OpenAI API
```
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
```

### Supabase
```
URL: https://0ec90b57d6e95fcbda19832f.supabase.co
ANON_KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJib2x0IiwicmVmIjoiMGVjOTBiNTdkNmU5NWZjYmRhMTk4MzJmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg4ODE1NzQsImV4cCI6MTc1ODg4MTU3NH0.9I8-U0x86Ak8t2DGaIk0HfvTSLsAyzdnz-Nw00mMkKw
```

---

## Top 3 Issues That Killed This Project

### 1. Bird Capture Logic (60% of problems)
**What was broken:**
- Complex state machine with 4 interacting timers
- Birds detected but not captured (timing windows missed)
- Same bird counted multiple times (duplicate detection failed)
- Multiple birds counted as one visit
- Fast birds completely missed

**The fix:**
- Simple state machine with clear states (see PRD Section 2.2)
- Event-based transitions, not timer-based checks
- Time-window deduplication (60s rule)
- Multiple captures per visit (3-5 photos)

### 2. Logging & Debugging (25% of problems)
**What was broken:**
- 3 different log files in 3 locations
- No way to correlate logs across scripts
- Startup script died silently (we never knew where)
- Can't debug production issues

**The fix:**
- All logs to Supabase database
- Structured JSON logs with correlation IDs
- Real-time log viewer in dashboard
- Health checks exposed via API endpoint

### 3. Dashboard & UX (15% of problems)
**What was broken:**
- Static HTML with 30-second auto-refresh
- Relative path issues broke navigation
- No indication when system is down
- No way to fix wrong species IDs

**The fix:**
- React app with real-time WebSocket updates
- Admin features to override species, mark false positives
- System health indicators
- Export data, view logs, search/filter

---

## Architecture Overview

### Current (Broken)
```
[RTSP Camera]
      ↓
[pilot_bird_counter_fixed.py] ─saves images to─→ [file system]
      ↓                                                  ↓
[metrics.json] ←────reads/writes────→ [pilot_analyze_captures_fixed.py]
      ↓                                                  ↓
[dashboard.html] ←───refreshes every 30s────        [OpenAI API]

Issues: Race conditions, file locks, state corruption, silent failures
```

### Proposed (Robust)
```
[RTSP Camera]
      ↓
[Single Python Service]
      ├─→ [Detection Thread]
      ├─→ [Visit State Machine]
      ├─→ [Analysis Worker Queue]
      └─→ [Health Check API]
            ↓
      [Supabase]
      ├─→ [PostgreSQL] (visits, captures, logs)
      ├─→ [Storage] (images)
      └─→ [Realtime] (WebSocket updates)
            ↓
      [React Dashboard]
      ├─→ Live feed
      ├─→ Visit history
      ├─→ Statistics
      └─→ Admin tools
```

---

## The Visit State Machine (Key Innovation)

This replaces all the broken timing logic:

```
┌─────────┐  Bird detected   ┌──────────────┐
│  IDLE   │ ──────────────→  │ BIRD_PRESENT │
└─────────┘                   └──────────────┘
                                      │
                              Still detected
                              Capture every 3s
                              Max 5 photos
                                      │
                              Bird gone (no detection)
                                      ↓
                              ┌──────────────┐
                              │ BIRD_ABSENT  │
                              │ (5s grace)   │
                              └──────────────┘
                                   ↙      ↘
                    Bird returns      5s elapsed
                         ↙                  ↘
                ┌──────────────┐      ┌────────────────┐
                │ BIRD_PRESENT │      │ VISIT_COMPLETE │
                └──────────────┘      │ (15s cooldown) │
                                      └────────────────┘
                                            ↓
                                      Cooldown done
                                            ↓
                                      ┌─────────┐
                                      │  IDLE   │
                                      └─────────┘
```

**Why this works:**
- Clear states, no ambiguity
- Handles fast visits (bird stays 2s), long visits (2 min), and returns
- Multiple photos per visit = better species ID
- Cooldown prevents spam
- Grace period handles brief occlusions

---

## Database Schema (Core Tables)

### `visits` - The heart of the system
```sql
CREATE TABLE visits (
  id UUID PRIMARY KEY,
  start_time TIMESTAMPTZ NOT NULL,
  end_time TIMESTAMPTZ,
  status VARCHAR(20),  -- active, analyzing, completed, failed
  species VARCHAR(100),
  species_confidence VARCHAR(10),  -- low, medium, high
  summary TEXT,
  bird_count INTEGER
);
```

### `captures` - Photos taken during visits
```sql
CREATE TABLE captures (
  id UUID PRIMARY KEY,
  visit_id UUID REFERENCES visits(id),
  timestamp TIMESTAMPTZ NOT NULL,
  image_url TEXT NOT NULL,
  detections JSONB,  -- Bounding boxes, confidence scores
  is_best_capture BOOLEAN
);
```

### `system_logs` - All logs go here
```sql
CREATE TABLE system_logs (
  id UUID PRIMARY KEY,
  timestamp TIMESTAMPTZ NOT NULL,
  level VARCHAR(10),  -- DEBUG, INFO, WARNING, ERROR, CRITICAL
  component VARCHAR(50),  -- detector, analyzer, api, database
  message TEXT,
  metadata JSONB,
  correlation_id UUID  -- Link logs from same visit
);
```

**Why Supabase?**
- Real-time subscriptions (WebSocket) built-in
- Storage (S3-like) built-in
- Auth built-in (if you want to add user accounts later)
- Free tier generous enough for this project
- PostgreSQL = robust, no corruption issues like JSON files

---

## Development Plan

### Week 1: Core Detection
```bash
# Goal: Service that detects birds and saves to database

Tasks:
1. Setup Supabase project, create tables
2. Python service: RTSP connection + auto-reconnect
3. YOLO detection loop (500ms interval)
4. Visit state machine implementation
5. Write visits/captures to Supabase
6. Console logging

Test: Run service, wave hand in front of camera, see visits in Supabase dashboard
```

### Week 2: Species ID
```bash
# Goal: Complete visit tracking with OpenAI analysis

Tasks:
1. Image cropping and preparation
2. OpenAI Vision API integration
3. Retry logic (3 attempts, exponential backoff)
4. Update visit with species info
5. Error handling (log to system_logs table)

Test: Let bird visit, verify species identified within 10s
```

### Week 3: Dashboard v1
```bash
# Goal: Working dashboard showing visits

Tasks:
1. React + Vite + TypeScript setup
2. Supabase client + Realtime subscriptions
3. Live feed component (active visits)
4. Recent visits list (last 20)
5. Basic statistics (today's count, top species)

Test: Open dashboard, see real-time updates when bird visits
```

### Week 4: Production Ready
```bash
# Goal: Deployed, monitored, production-ready

Tasks:
1. Health check API endpoint
2. System health dashboard component
3. Admin features (override species, mark false positive)
4. Deploy backend (Railway/DigitalOcean)
5. Deploy frontend (Vercel)
6. Setup monitoring/alerts

Test: System runs 24/7 for 1 week without manual intervention
```

---

## Tech Stack Recommendations

### Backend Service
```python
# FastAPI (Python web framework)
# OpenCV (camera/image processing)
# Ultralytics (YOLO)
# OpenAI (species ID)
# Supabase Python client
# Threading (for concurrent processing)

# File: main.py
from fastapi import FastAPI
from threading import Thread

app = FastAPI()

# Detection thread runs continuously
detection_thread = Thread(target=run_detection_loop, daemon=True)
detection_thread.start()

# Health check endpoint
@app.get("/health")
async def health():
    return {
        "camera": camera_status(),
        "detector": detector_status(),
        "analyzer": analyzer_status()
    }
```

### Frontend Dashboard
```typescript
// React + TypeScript
// Supabase JS client
// TailwindCSS (styling)
// Recharts (graphs)
// React Query (data fetching)

// Real-time subscriptions
const { data: visits } = useQuery(['visits'], fetchVisits)

useEffect(() => {
  const subscription = supabase
    .channel('visits')
    .on('postgres_changes',
      { event: '*', schema: 'public', table: 'visits' },
      (payload) => {
        // Update UI instantly
      }
    )
    .subscribe()

  return () => subscription.unsubscribe()
}, [])
```

### Deployment
```yaml
# Backend: Railway.app (or DigitalOcean)
# - Auto-deploy from GitHub
# - Automatic restarts
# - Health checks
# - Log aggregation

# Frontend: Vercel
# - Auto-deploy from GitHub
# - Global CDN
# - Instant rollbacks
# - Preview deployments

# Database: Supabase
# - Managed PostgreSQL
# - Automatic backups
# - Built-in monitoring
```

---

## Configuration Template

Create `.env` file:

```bash
# Camera
RTSP_URL=rtsp://admin:admin@192.168.1.79:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif

# Detection
YOLO_MODEL_PATH=yolov8n.pt
DETECTION_INTERVAL_MS=500
CONFIDENCE_THRESHOLD=0.25
ROI_X1=0.25
ROI_Y1=0.34
ROI_X2=0.62
ROI_Y2=0.72
MIN_AREA_RATIO=0.002

# Visit Logic
ABSENCE_GRACE_PERIOD_SEC=5
VISIT_COOLDOWN_SEC=15
MAX_CAPTURES_PER_VISIT=5
CAPTURE_INTERVAL_SEC=3

# OpenAI
OPENAI_API_KEY=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
OPENAI_MODEL=gpt-4o-mini
OPENAI_TIMEOUT_SEC=30
OPENAI_MAX_RETRIES=3

# Supabase
SUPABASE_URL=https://0ec90b57d6e95fcbda19832f.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJib2x0IiwicmVmIjoiMGVjOTBiNTdkNmU5NWZjYmRhMTk4MzJmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg4ODE1NzQsImV4cCI6MTc1ODg4MTU3NH0.9I8-U0x86Ak8t2DGaIk0HfvTSLsAyzdnz-Nw00mMkKw
SUPABASE_SERVICE_ROLE_KEY=<get-from-supabase-dashboard>

# Storage
STORAGE_BUCKET=bird-captures

# System
LOG_LEVEL=INFO
HEALTH_CHECK_INTERVAL_SEC=10
```

---

## Key Improvements Over Current System

| Issue | Current System | New System |
|-------|---------------|------------|
| **State Management** | 4 interacting timers, race conditions | Clean state machine, event-driven |
| **Duplicate Detection** | SHA1 hash (brittle) | Time-window + session ID (robust) |
| **Logging** | 3 separate files, no correlation | Structured logs in database, searchable |
| **Dashboard** | Static HTML, 30s refresh | React + WebSocket, instant updates |
| **Data Storage** | JSON file (corrupts easily) | PostgreSQL (ACID, reliable) |
| **Error Recovery** | Silent failures, manual restart | Auto-reconnect, health monitoring |
| **Species Override** | Not possible | Admin can fix mistakes |
| **Deployment** | Windows batch file | Cloud service, auto-restart |
| **Monitoring** | None | Health checks, log viewer, alerts |
| **Multiple Photos** | 1 photo per visit (often blurry) | 3-5 photos, best one analyzed |

---

## Next Steps

1. **Read the full PRD** (`BIRD_TRACKER_PRD.md`)
   - Especially Section 2.2 (Visit State Machine)
   - And Appendix (What Went Wrong)

2. **Setup Supabase project**
   - Create new project
   - Run the SQL migrations from PRD
   - Get your service role key

3. **Start with Week 1**
   - Clone a fresh repo
   - Setup Python environment
   - Implement detection loop
   - Test with hand waving

4. **Iterate quickly**
   - Don't try to build everything at once
   - Get detection working first
   - Add features incrementally

---

## Questions to Ask Yourself

Before starting:
- ✅ **Platform?** Linux/Mac/Cloud (not Windows batch files)
- ✅ **Language?** Python for backend (proven, works well)
- ✅ **Database?** Supabase (real-time, storage, managed)
- ✅ **Frontend?** React (real-time updates, admin features)
- ✅ **Deployment?** Cloud service (auto-restart, monitoring)

---

## Files in This Package

1. **BIRD_TRACKER_PRD.md** - Complete PRD (comprehensive)
2. **PRD_QUICK_START.md** - This file (quick reference)
3. **Your old code** - Reference for what NOT to do

---

## Final Advice

**Don't repeat these mistakes:**
1. Don't use multiple scripts communicating via filesystem
2. Don't use JSON files for state (use proper database)
3. Don't use complex timer logic (use state machine)
4. Don't use auto-refresh HTML (use WebSocket)
5. Don't deploy with batch files (use proper service manager)

**Do these things:**
1. Start simple (detection first, then add features)
2. Log everything (structured, to database)
3. Monitor health (health checks, alerts)
4. Test edge cases (fast birds, multiple birds, reconnects)
5. Deploy to cloud (auto-restart, proper monitoring)

Good luck! The PRD has everything you need to build this right.
