import threading
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
from datetime import datetime, timezone

from config import Config
from bird_detector import BirdDetector
from species_analyzer import SpeciesAnalyzer
from logger import StructuredLogger

app = FastAPI(title="Bird Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Config.validate()

supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_ROLE_KEY)
logger = StructuredLogger(supabase, 'api')

detector = BirdDetector(supabase, Config)
analyzer = SpeciesAnalyzer(supabase, Config)

def run_detector():
    if detector.initialize():
        detector.run()

def run_analyzer_worker():
    logger.info("Starting analyzer worker")

    while True:
        try:
            visits = supabase.table('visits').select('id').eq('status', 'analyzing').limit(10).execute()

            for visit in visits.data:
                analyzer.analyze_visit(visit['id'])

            time.sleep(5)

        except Exception as e:
            logger.error(f"Analyzer worker error: {e}")
            time.sleep(10)

detector_thread = threading.Thread(target=run_detector, daemon=True)
analyzer_thread = threading.Thread(target=run_analyzer_worker, daemon=True)

detector_thread.start()
analyzer_thread.start()

logger.info("Bird Tracker API started")

@app.get("/")
async def root():
    return {
        "service": "Bird Tracker API",
        "status": "running",
        "session_id": detector.session_id if detector else None
    }

@app.get("/health")
async def health_check():
    try:
        health_records = supabase.table('system_health').select('*').execute()

        health_status = {}
        for record in health_records.data:
            health_status[record['component']] = {
                'status': record['status'],
                'message': record['message'],
                'last_check': record['last_check'],
                'metadata': record.get('metadata', {})
            }

        visits_today = supabase.table('visits').select('id', count='exact').gte(
            'start_time',
            datetime.now(timezone.utc).replace(hour=0, minute=0, second=0).isoformat()
        ).execute()

        return {
            "overall_status": "healthy" if all(h['status'] in ['healthy', 'connected'] for h in health_status.values()) else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": health_status,
            "metrics": {
                "visits_today": visits_today.count if visits_today.count else 0,
                "session_id": detector.session_id if detector else None
            }
        }

    except Exception as e:
        return {
            "overall_status": "unhealthy",
            "error": str(e)
        }

@app.get("/visits/recent")
async def get_recent_visits(limit: int = 20):
    try:
        visits = supabase.table('visits').select('*').order('start_time', desc=True).limit(limit).execute()
        return {"visits": visits.data}
    except Exception as e:
        logger.error(f"Failed to fetch recent visits: {e}")
        return {"error": str(e)}

@app.get("/visits/{visit_id}")
async def get_visit(visit_id: str):
    try:
        visit = supabase.table('visits').select('*').eq('id', visit_id).single().execute()
        captures = supabase.table('captures').select('*').eq('visit_id', visit_id).order('timestamp').execute()

        return {
            "visit": visit.data,
            "captures": captures.data
        }
    except Exception as e:
        logger.error(f"Failed to fetch visit {visit_id}: {e}")
        return {"error": str(e)}

@app.get("/stats/species")
async def get_species_stats():
    try:
        stats = supabase.table('species_stats').select('*').order('total_visits', desc=True).execute()
        return {"species": stats.data}
    except Exception as e:
        logger.error(f"Failed to fetch species stats: {e}")
        return {"error": str(e)}

@app.get("/stats/today")
async def get_today_stats():
    try:
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0).isoformat()

        visits = supabase.table('visits').select('species', count='exact').gte('start_time', today_start).execute()

        species_count = len(set(v['species'] for v in visits.data if v.get('species') and v['species'] != 'unknown'))

        return {
            "total_visits": visits.count if visits.count else 0,
            "unique_species": species_count,
            "date": datetime.now(timezone.utc).date().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to fetch today stats: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
