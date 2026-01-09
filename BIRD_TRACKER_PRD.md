# Bird Feeder Tracking System - Product Requirements Document (PRD)

## Executive Summary

A real-time bird tracking system that monitors an RTSP camera feed, detects birds using YOLO AI, identifies species using OpenAI Vision API, and displays results on a live dashboard. This system replaces a problematic Windows-based implementation with a robust, cloud-native solution.

---

## Critical Configuration

### RTSP Camera Stream
```
rtsp://admin:admin@192.168.1.79:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif
```

### API Keys
```
OPENAI_API_KEY=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

VITE_SUPABASE_URL=https://0ec90b57d6e95fcbda19832f.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJib2x0IiwicmVmIjoiMGVjOTBiNTdkNmU5NWZjYmRhMTk4MzJmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg4ODE1NzQsImV4cCI6MTc1ODg4MTU3NH0.9I8-U0x86Ak8t2DGaIk0HfvTSLsAyzdnz-Nw00mMkKw
```

---

## Problems with Current Implementation

### 1. Bird Capture Logic - CRITICAL ISSUES

#### State Machine Complexity
**Problem:** Multiple interacting timers and state variables create race conditions:
- `bird_present` (boolean)
- `last_capture_time` (timestamp)
- `last_bird_detection_time` (timestamp)
- `unique_count` (counter)
- `CAPTURE_GAP_SEC = 15` (prevents captures within 15s)
- `BIRD_ABSENCE_TIMEOUT = 5` (marks bird as gone after 5s)
- `DETECTION_INTERVAL = 0.5` (only detect every 0.5s)

**Impact:**
- Bird lands → detected → leaves before 5s → marked as present still
- Bird lands → captured → leaves → returns 10s later → ignored (gap not elapsed)
- Multiple birds swap places → counted as one visit
- Fast-moving birds → missed completely

**Solution Needed:** Simple event-based state machine with clear transitions.

#### Duplicate Detection Across Sessions
**Problem:** Uses SHA1 hash of image bytes to deduplicate
- Same bird in similar pose → different hash
- Different birds in same location → different hash but same "visit"
- No temporal deduplication across restarts
- Race condition between counter and analyzer scripts

**Impact:**
- Same bird visit counted multiple times
- Database grows with duplicate entries
- Species counts become inaccurate

**Solution Needed:** Time-window based deduplication with persistent state.

#### Region of Interest (ROI) Filtering
**Problem:** Hardcoded normalized coordinates
```python
ROI_NORM = (0.25, 0.34, 0.62, 0.72)  # x1, y1, x2, y2 as fraction of frame
MIN_AREA_RATIO = 0.002  # Filter out detections < 0.2% of ROI area
```

**Impact:**
- Birds outside ROI ignored
- Small birds filtered out
- Camera angle changes break detection
- No visual feedback about ROI boundaries

**Solution Needed:** Configurable ROI with visual overlay, adaptive area thresholds.

#### Capture Timing Logic
**Problem:** Multiple conflicting timing rules:
```python
# Must satisfy ALL:
1. Bird detected in current frame
2. (now - last_capture_time) >= 15 seconds
3. Bird not already marked as present
4. (now - last_bird_detection_time) < 5 seconds (for state reset)
```

**Scenarios that fail:**
1. **Quick visit:** Bird stays 3 seconds → leaves → captured but too short for good photo
2. **Long visit:** Bird stays 2 minutes → only 1 photo taken (first detection)
3. **Multiple birds:** 2 birds feeding together → counted as 1 visit
4. **Bird returns:** Bird leaves and returns 10s later → ignored (gap hasn't elapsed)

**Solution Needed:** Configurable capture strategy with multiple photos per visit.

### 2. Logging Issues

**Problems:**
1. **Multiple log files** in different locations:
   - `pilot_logs/pilot_counter_YYYY-MM-DD.log`
   - `pilot_logs/pilot_analyzer_YYYY-MM-DD.log`
   - `startup_log.txt` (startup script)
   - No correlation between logs

2. **Inconsistent log levels:**
   - Console: INFO
   - File: DEBUG
   - No structured format (JSON, key-value)

3. **No error aggregation:**
   - OpenAI errors scattered
   - RTSP connection failures not summarized
   - No health check endpoint

4. **File rotation issues:**
   - Rotating file handler can lose logs during rotation
   - No log retention policy
   - Logs not indexed or searchable

**Solution Needed:** Centralized structured logging to Supabase with log levels, correlation IDs, and real-time viewing.

### 3. Dashboard Issues

**Problems:**
1. **Static HTML with meta refresh:**
   ```html
   <meta http-equiv='refresh' content='30'>
   ```
   - Refreshes entire page every 30s
   - No real-time updates
   - Loses scroll position
   - Annoying user experience

2. **Relative path issues:**
   - Dashboard served from `public/`
   - Images and reports in subdirectories
   - Paths break depending on server location
   - No CDN or proper asset serving

3. **No error states:**
   - Doesn't show when system is down
   - No indication if camera is offline
   - No indication if OpenAI API is failing
   - No health status

4. **Limited functionality:**
   - Can't edit species identification
   - Can't mark false positives
   - Can't retrigger analysis
   - No filtering or search
   - No date range selection

**Solution Needed:** React-based real-time dashboard with WebSocket updates, proper state management, error handling, and admin features.

### 4. System Architecture Issues

**Problems:**
1. **Two separate Python scripts:**
   - `pilot_bird_counter_fixed.py` - Captures images
   - `pilot_analyze_captures_fixed.py` - Analyzes images
   - Communication via filesystem (brittle)
   - No coordination
   - Race conditions

2. **Windows batch file startup:**
   - Requires Windows
   - Opens multiple CMD windows
   - No process management
   - No graceful shutdown
   - Can't restart individual components

3. **File-based state:**
   - `metrics.json` - Single point of failure
   - Concurrent write issues
   - No atomic updates
   - Lost on crash

4. **No health monitoring:**
   - Scripts can crash silently
   - No alerting
   - No auto-restart
   - No performance metrics

**Solution Needed:** Single unified service with proper state management, health checks, and cloud deployment.

---

## System Requirements

### Core Functionality

#### 1. Bird Detection Service

**Inputs:**
- RTSP stream URL
- YOLO model (yolov8n.pt)
- Detection configuration

**Processing:**
1. Connect to RTSP stream with auto-reconnect
2. Run YOLO detection every 500ms (configurable)
3. Filter by:
   - Class ID = 14 (bird)
   - Confidence > 0.25 (configurable)
   - ROI boundaries (configurable)
   - Minimum area > 0.2% of ROI (configurable)

**Outputs:**
- Detection events with bounding boxes
- Frame captures (JPEG)
- Detection metadata (timestamp, confidence, position)

**Error Handling:**
- RTSP connection lost → retry with exponential backoff (2s, 4s, 8s, max 60s)
- Frame read failure → log and skip frame
- YOLO model error → log and continue
- Detect continuous failures (10 consecutive) → alert and mark unhealthy

#### 2. Visit Tracking Logic - NEW DESIGN

**Visit State Machine:**

```
States:
- IDLE: No bird detected
- BIRD_PRESENT: Bird detected, capturing
- BIRD_ABSENT: Bird was present, now gone, grace period
- VISIT_COMPLETE: Visit ended, ready for next

Transitions:
IDLE → BIRD_PRESENT:
  - When: Bird detected
  - Action: Start new visit, capture first photo, start visit timer

BIRD_PRESENT → BIRD_PRESENT:
  - When: Bird still detected
  - Action: If >3s since last capture, take another photo (max 5 photos per visit)

BIRD_PRESENT → BIRD_ABSENT:
  - When: No bird detected
  - Action: Start absence timer (5s grace period)

BIRD_ABSENT → BIRD_PRESENT:
  - When: Bird detected within grace period
  - Action: Resume visit, reset absence timer

BIRD_ABSENT → VISIT_COMPLETE:
  - When: Absence timer expires (5s)
  - Action: End visit, trigger analysis, start cooldown (15s)

VISIT_COMPLETE → IDLE:
  - When: Cooldown expires (15s)
  - Action: Ready for next visit
```

**Visit Data Structure:**
```json
{
  "visit_id": "uuid-v4",
  "session_id": "service-start-uuid",
  "start_time": "2026-01-09T13:30:00.000Z",
  "end_time": "2026-01-09T13:31:45.000Z",
  "duration_seconds": 105,
  "captures": [
    {
      "capture_id": "uuid-v4",
      "timestamp": "2026-01-09T13:30:00.000Z",
      "image_path": "s3://bucket/2026-01-09/visit_abc123/capture_001.jpg",
      "detections": [
        {
          "bbox": [100, 150, 300, 400],
          "confidence": 0.89,
          "class_id": 14,
          "class_name": "bird"
        }
      ]
    }
  ],
  "analysis": {
    "status": "completed",
    "species_guess": "House Sparrow",
    "species_confidence": "high",
    "summary": "Adult house sparrow feeding on seeds",
    "bird_count": 1,
    "analyzed_at": "2026-01-09T13:31:50.000Z",
    "best_capture_id": "uuid-v4"
  },
  "status": "completed"
}
```

**Deduplication Rules:**
1. Within same session: Use visit state machine (no duplicates by design)
2. Across sessions: If new visit starts <60s after previous visit ended → extend previous visit
3. Across days: Reset counter at midnight local time

#### 3. Species Identification Service

**Inputs:**
- Visit captures (1-5 images)
- Detection bounding boxes

**Processing:**
1. Select best image:
   - Largest bird (by bbox area)
   - Highest confidence
   - Clearest (least motion blur - future enhancement)

2. Crop and prepare:
   - Expand bbox by 10% margin
   - Resize to max 512px (preserve aspect ratio)
   - Convert to JPEG base64

3. Call OpenAI Vision API:
   - Model: `gpt-4o-mini`
   - Prompt: "Analyze this bird feeder image. Return JSON with: birds_present (bool), count (int), species_guess (string), confidence (low/medium/high), summary (string). Provide your best species guess; use 'unknown' only if truly uncertain."
   - Timeout: 30s
   - Max tokens: 300

4. Retry logic:
   - 3 attempts with exponential backoff (2s, 4s, 8s)
   - Rate limit handling (429) → retry after delay
   - Auth errors (401) → fail immediately, alert
   - Other errors → retry then mark as failed

**Outputs:**
- Species identification
- Confidence level
- Natural language summary
- Bird count (if multiple)

**Fallback:**
- If API fails → species = "unknown", summary = error message
- Visit still recorded with YOLO-only data

#### 4. Data Persistence

**Database:** Supabase PostgreSQL

**Schema:**

```sql
-- Visits table
CREATE TABLE visits (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL,
  start_time TIMESTAMPTZ NOT NULL,
  end_time TIMESTAMPTZ,
  duration_seconds INTEGER,
  status VARCHAR(20) NOT NULL, -- active, analyzing, completed, failed
  species VARCHAR(100),
  species_confidence VARCHAR(10), -- low, medium, high
  summary TEXT,
  bird_count INTEGER DEFAULT 1,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_visits_start_time ON visits(start_time DESC);
CREATE INDEX idx_visits_status ON visits(status);
CREATE INDEX idx_visits_species ON visits(species);

-- Captures table
CREATE TABLE captures (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  visit_id UUID NOT NULL REFERENCES visits(id) ON DELETE CASCADE,
  timestamp TIMESTAMPTZ NOT NULL,
  image_url TEXT NOT NULL,
  thumbnail_url TEXT,
  detections JSONB NOT NULL, -- Array of detection objects
  is_best_capture BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_captures_visit ON captures(visit_id);
CREATE INDEX idx_captures_timestamp ON captures(timestamp DESC);

-- Species counts (materialized view, updated hourly)
CREATE TABLE species_stats (
  species VARCHAR(100) PRIMARY KEY,
  total_visits INTEGER NOT NULL DEFAULT 0,
  last_seen TIMESTAMPTZ,
  first_seen TIMESTAMPTZ,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- System logs
CREATE TABLE system_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  level VARCHAR(10) NOT NULL, -- DEBUG, INFO, WARNING, ERROR, CRITICAL
  component VARCHAR(50) NOT NULL, -- detector, analyzer, api, database
  message TEXT NOT NULL,
  metadata JSONB,
  correlation_id UUID
);

CREATE INDEX idx_logs_timestamp ON system_logs(timestamp DESC);
CREATE INDEX idx_logs_level ON system_logs(level);
CREATE INDEX idx_logs_component ON system_logs(component);

-- System health
CREATE TABLE system_health (
  component VARCHAR(50) PRIMARY KEY,
  status VARCHAR(20) NOT NULL, -- healthy, degraded, unhealthy
  last_check TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  message TEXT,
  metadata JSONB
);
```

**RLS Policies:**
```sql
-- Public read access to visits and captures
ALTER TABLE visits ENABLE ROW LEVEL SECURITY;
ALTER TABLE captures ENABLE ROW LEVEL SECURITY;
ALTER TABLE species_stats ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read visits" ON visits FOR SELECT TO anon USING (true);
CREATE POLICY "Allow public read captures" ON captures FOR SELECT TO anon USING (true);
CREATE POLICY "Allow public read species_stats" ON species_stats FOR SELECT TO anon USING (true);

-- Service role only for writes
CREATE POLICY "Service role can insert visits" ON visits FOR INSERT TO service_role WITH CHECK (true);
CREATE POLICY "Service role can update visits" ON visits FOR UPDATE TO service_role USING (true);
```

#### 5. Real-Time Dashboard

**Technology Stack:**
- React 18 with TypeScript
- Supabase Realtime subscriptions
- TailwindCSS for styling
- Recharts for statistics
- React Query for data fetching

**Features:**

**Live View:**
- Current camera frame (updated every 1s)
- Active visit status
- Detection overlay (bounding boxes)
- Visit timer
- Species identification in progress

**Recent Visits:**
- Last 20 visits
- Thumbnail + species + time
- Click to view details
- Status indicators (analyzing, completed, failed)

**Statistics:**
- Today: X visits, Y species
- This week/month: charts
- Top species: bar chart
- Visit frequency: timeline
- Average visit duration

**System Health:**
- Camera status (connected/disconnected)
- Detection service (active/stopped)
- API status (operational/degraded/down)
- Last error messages

**Admin Features:**
- Manual species override
- Mark false positive
- Retrigger analysis
- Export data (CSV/JSON)
- System logs viewer

**Real-Time Updates:**
```typescript
// Subscribe to new visits
supabase
  .channel('visits')
  .on('postgres_changes',
    { event: 'INSERT', schema: 'public', table: 'visits' },
    (payload) => {
      // Update UI with new visit
    }
  )
  .subscribe()

// Subscribe to visit updates (species identified)
supabase
  .channel('visits')
  .on('postgres_changes',
    { event: 'UPDATE', schema: 'public', table: 'visits' },
    (payload) => {
      // Update UI with species info
    }
  )
  .subscribe()
```

#### 6. Logging & Monitoring

**Structured Logging:**

```typescript
interface LogEntry {
  timestamp: string;
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  component: 'detector' | 'analyzer' | 'api' | 'database';
  message: string;
  metadata?: {
    visit_id?: string;
    capture_id?: string;
    error?: string;
    duration_ms?: number;
    [key: string]: any;
  };
  correlation_id?: string;
}
```

**Log to Supabase:**
- All logs stored in `system_logs` table
- Retention: 30 days
- Search and filter in dashboard
- Alert on ERROR/CRITICAL

**Health Checks:**

```typescript
interface HealthCheck {
  camera: {
    status: 'connected' | 'disconnected' | 'reconnecting';
    last_frame: string; // timestamp
    fps: number;
  };
  detector: {
    status: 'running' | 'stopped' | 'error';
    detections_per_minute: number;
    last_detection: string; // timestamp
  };
  analyzer: {
    status: 'running' | 'stopped' | 'error';
    queue_size: number;
    avg_processing_time_ms: number;
  };
  api: {
    openai_status: 'operational' | 'degraded' | 'down';
    recent_errors: number;
    avg_response_time_ms: number;
  };
  database: {
    status: 'connected' | 'disconnected';
    write_lag_ms: number;
  };
}
```

**Expose health endpoint:**
- `GET /api/health` returns JSON health status
- Update every 10 seconds
- Store in Supabase for historical tracking

---

## Configuration

**Environment Variables:**

```bash
# Camera
RTSP_URL=rtsp://admin:admin@192.168.1.79:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif
CAMERA_FPS=30

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
VISIT_EXTENSION_WINDOW_SEC=60

# OpenAI
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=300
OPENAI_TIMEOUT_SEC=30
OPENAI_MAX_RETRIES=3

# Supabase
SUPABASE_URL=https://0ec90b57d6e95fcbda19832f.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...
SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>

# Storage
STORAGE_PROVIDER=supabase # or s3, local
STORAGE_BUCKET=bird-captures
STORAGE_PATH_PATTERN={date}/{visit_id}/{capture_id}.jpg

# System
LOG_LEVEL=INFO
HEALTH_CHECK_INTERVAL_SEC=10
SESSION_ID=<auto-generated-uuid-on-start>
```

---

## Deployment Architecture

### Recommended: Cloud Deployment

**Option 1: Single Service (Recommended for MVP)**

```
┌─────────────────────────────────────────┐
│         Cloud VM / Container            │
│  ┌───────────────────────────────────┐  │
│  │   Python Service (FastAPI)        │  │
│  │   - RTSP Reader Thread            │  │
│  │   - Detection Thread              │  │
│  │   - Analysis Worker Queue         │  │
│  │   - Health Check Endpoint         │  │
│  └───────────────────────────────────┘  │
│                 │                        │
│                 ▼                        │
│  ┌───────────────────────────────────┐  │
│  │   Supabase Client                 │  │
│  │   - Write visits/captures         │  │
│  │   - Write logs                    │  │
│  │   - Update health status          │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
                 │
                 ▼
      ┌──────────────────┐
      │   Supabase       │
      │   - PostgreSQL   │
      │   - Storage      │
      │   - Realtime     │
      └──────────────────┘
                 │
                 ▼
      ┌──────────────────┐
      │   React Dashboard│
      │   (Vercel/Netlify)│
      └──────────────────┘
```

**Tech Stack:**
- **Backend:** Python + FastAPI + OpenCV + Ultralytics
- **Queue:** Python Queue for analysis tasks
- **Database:** Supabase PostgreSQL
- **Storage:** Supabase Storage (or S3)
- **Frontend:** React + Vite + Supabase JS
- **Deployment:**
  - Backend: DigitalOcean Droplet / AWS EC2 / Railway
  - Frontend: Vercel / Netlify

**Process Management:**
- Use systemd (Linux) or supervisor
- Auto-restart on crash
- Log rotation
- Graceful shutdown

---

## Development Phases

### Phase 1: Core Detection (Week 1)
- RTSP connection with auto-reconnect
- YOLO detection loop
- New visit state machine
- Write to Supabase
- Basic health checks
- Console logging

**Deliverable:** Service that detects birds and logs to database

### Phase 2: Species Identification (Week 2)
- OpenAI Vision integration
- Image cropping and preparation
- Retry logic
- Store analysis results
- Error handling

**Deliverable:** Complete visit tracking with species ID

### Phase 3: Dashboard v1 (Week 3)
- React app setup
- Live visit feed
- Recent visits list
- Basic statistics
- Supabase Realtime integration

**Deliverable:** Working dashboard showing visits

### Phase 4: Advanced Features (Week 4)
- Admin features (override, mark false positive)
- Advanced statistics and charts
- System logs viewer
- Export data
- Performance optimizations

**Deliverable:** Production-ready system

---

## Success Metrics

1. **Reliability:**
   - Camera uptime > 99%
   - Zero crashes per week
   - Automatic recovery from errors < 30s

2. **Accuracy:**
   - Bird detection rate > 95% (vs manual review)
   - False positive rate < 5%
   - Species ID accuracy > 80% (for common species)

3. **Performance:**
   - Detection latency < 1s
   - Analysis latency < 10s
   - Dashboard loads < 2s

4. **User Experience:**
   - Real-time updates < 1s delay
   - Mobile responsive
   - No page refreshes needed

---

## Risk Mitigation

### High Priority Risks

1. **RTSP Connection Loss**
   - Mitigation: Auto-reconnect with exponential backoff, alert after 5 minutes down

2. **OpenAI API Failures**
   - Mitigation: Retry logic, fallback to "unknown" species, continue operation

3. **Database Connection Loss**
   - Mitigation: Queue writes in memory, retry on reconnect, alert immediately

4. **Storage Full**
   - Mitigation: Automatic cleanup of old images (>30 days), alert at 80% full

5. **Multiple Birds Confusion**
   - Mitigation: Clear documentation that system tracks "visits" not individual birds

---

## Future Enhancements

1. **Multiple bird tracking:** Track individual birds within a visit
2. **Behavior analysis:** Feeding patterns, time-of-day preferences
3. **Audio detection:** Use microphone for bird calls
4. **Weather correlation:** Link visits to weather conditions
5. **Migration tracking:** Seasonal species patterns
6. **Mobile app:** Push notifications for rare species
7. **Community features:** Share sightings, compare with other feeders
8. **ML model fine-tuning:** Train on your specific birds for better accuracy

---

## Appendix: What Went Wrong - Detailed Analysis

### A. The State Machine Hell

Original logic had 4 interdependent variables:
```python
bird_present = False          # Is bird there now?
last_capture_time = 0.0      # When did we last capture?
last_bird_detection_time = 0.0  # When did we last see a bird?
unique_count = 0             # How many visits today?
```

**Issue 1: Race between detection and state**
```python
# Frame 1: Bird detected
detected_birds = 1
last_bird_detection_time = now
bird_present = False  # Still False!

# Frame 2: No bird (bird left)
detected_birds = 0
# But bird_present is still False, so no capture happened!
```

**Issue 2: Absence timeout logic**
```python
if detected_birds > 0:
    last_bird_detection_time = now
    if not bird_present:
        if (now - last_capture_time) >= CAPTURE_GAP_SEC:
            # Capture!
            bird_present = True
else:
    if bird_present and ((now - last_bird_detection_time) >= BIRD_ABSENCE_TIMEOUT):
        bird_present = False
```
Problem: If bird leaves before 5 seconds, `bird_present` is set to True then immediately back to False. If bird leaves after 6 seconds, `bird_present` stays True until next check. Inconsistent!

### B. The Duplicate Disaster

**Original approach:**
1. Capture image → compute SHA1 hash
2. Check if hash exists in metrics.json
3. If exists, skip; if not, process

**Problems:**
1. Same bird, different pose → different hash → duplicate entry
2. Different lighting/time → different hash → duplicate entry
3. metrics.json corrupted → all history lost
4. Two scripts reading/writing metrics.json → race condition
5. Image file deleted → can't compute hash → can't deduplicate

**Real scenario that happened:**
- Bird visits at 1:00 PM, captured
- Bird visits at 1:00:10 PM (same bird, same place)
- Gap timer hasn't elapsed (15s)
- Detection ignored ✓
- Bird visits at 1:00:30 PM
- Gap timer elapsed
- Bird in slightly different position
- Photo taken, hash computed → different hash
- Recorded as new visit ✗
- Result: Same bird = 2 visits

### C. The Logging Nightmare

**Multiple log destinations:**
```
pilot_logs/
  pilot_counter_2026-01-09.log    (Detection script)
  pilot_analyzer_2026-01-09.log   (Analysis script)
startup_log.txt                    (Batch script)
public/metrics.json               (State, not really a log)
```

**When something went wrong:**
1. User sees: "It's not working"
2. Check startup_log.txt → "OpenAI API key found" (looks good!)
3. Check pilot_counter log → "Bird detected" (looks good!)
4. Check pilot_analyzer log → "API call failed: 401 Unauthorized" (AHA!)
5. But wait, startup said key was found...
6. Turns out: Env variable had trailing whitespace
7. Counter script trimmed it, analyzer didn't
8. Took 2 hours to debug

**No correlation:**
- Log says "Failed to analyze bird_5_1234567890.jpg"
- Which visit was that?
- What species did we think it was?
- Was it a false positive?
- Can't tell without manually searching other logs

### D. The Dashboard Deadlock

**Original design:**
```html
<meta http-equiv='refresh' content='30'>
```

**Problem sequence:**
1. User opens dashboard
2. Sees 3 visits
3. Bird lands at :15 seconds after page load
4. Visit #4 created
5. User waits... waiting...
6. At :30 seconds, page refreshes
7. Now sees 4 visits
8. User thinks: "Why did it take 30 seconds?"

**Worse problem:**
1. Dashboard auto-refreshes every 30s
2. Analysis script updates metrics.json
3. Both use relative paths
4. Dashboard served from `public/`
5. Images stored in `public/pilot_captures/2026-01-09/`
6. Reports stored in `public/pilot_reports/2026-01-09/`
7. User clicks image link
8. Browser navigates to image
9. URL is now: `http://localhost:8080/pilot_captures/2026-01-09/bird_1.jpg`
10. Page refreshes (meta tag!)
11. Tries to load dashboard from: `http://localhost:8080/pilot_captures/2026-01-09/dashboard.html`
12. 404 error
13. User stuck

---

## Conclusion

This PRD addresses every major issue from the original implementation:

1. **State machine** → Clean visit lifecycle with clear states
2. **Duplicates** → Time-window + session-based deduplication
3. **Logging** → Structured logs to database with correlation IDs
4. **Dashboard** → Real-time React app with WebSocket updates
5. **Architecture** → Single service with proper health monitoring
6. **Deployment** → Cloud-native, auto-restart, monitoring

Start with Phase 1, get core detection working, then iterate. Use this PRD as your north star.
