import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CAPTURE_ROOT = Path(os.getenv("CAPTURE_ROOT", BASE_DIR / "pilot_captures"))
REPORT_ROOT = Path(os.getenv("REPORT_ROOT", BASE_DIR / "pilot_reports"))
LOG_ROOT = Path(os.getenv("LOG_ROOT", BASE_DIR / "pilot_logs"))
DASHBOARD_DIR = Path(os.getenv("DASHBOARD_DIR", BASE_DIR / "public"))

METRICS_FILE = DASHBOARD_DIR / "metrics.json"
DASHBOARD_FILE = DASHBOARD_DIR / "dashboard.html"

RTSP_URL = os.getenv(
    "RTSP_URL",
    "rtsp://admin:admin@192.168.1.79:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif"
)

MODEL_PATH = os.getenv("MODEL_PATH", "yolov8n.pt")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

CONF_THRESH = float(os.getenv("CONF_THRESH", "0.25"))
ROI_NORM = tuple(map(float, os.getenv("ROI_NORM", "0.25,0.34,0.62,0.72").split(",")))
DETECT_RESIZE_WIDTH = int(os.getenv("DETECT_RESIZE_WIDTH", "960"))
BIRD_CLASS_ID = 14
MIN_AREA_RATIO = float(os.getenv("MIN_AREA_RATIO", "0.002"))

CAPTURE_GAP_SEC = int(os.getenv("CAPTURE_GAP_SEC", "15"))
BIRD_ABSENCE_TIMEOUT = int(os.getenv("BIRD_ABSENCE_TIMEOUT", "5"))
DETECTION_INTERVAL = float(os.getenv("DETECTION_INTERVAL", "0.5"))
VIEW_SCALE = float(os.getenv("VIEW_SCALE", "0.6"))

DUP_SECONDS = int(os.getenv("DUP_SECONDS", "15"))
