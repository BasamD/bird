import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    RTSP_URL = os.getenv('RTSP_URL', 'rtsp://admin:admin@192.168.1.79:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif')

    YOLO_MODEL_PATH = os.getenv('YOLO_MODEL_PATH', 'yolov8n.pt')
    DETECTION_INTERVAL_MS = int(os.getenv('DETECTION_INTERVAL_MS', '500'))
    CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.25'))
    BIRD_CLASS_ID = int(os.getenv('BIRD_CLASS_ID', '14'))

    ROI_X1 = float(os.getenv('ROI_X1', '0.25'))
    ROI_Y1 = float(os.getenv('ROI_Y1', '0.34'))
    ROI_X2 = float(os.getenv('ROI_X2', '0.62'))
    ROI_Y2 = float(os.getenv('ROI_Y2', '0.72'))
    MIN_AREA_RATIO = float(os.getenv('MIN_AREA_RATIO', '0.002'))

    ABSENCE_GRACE_PERIOD_SEC = int(os.getenv('ABSENCE_GRACE_PERIOD_SEC', '5'))
    VISIT_COOLDOWN_SEC = int(os.getenv('VISIT_COOLDOWN_SEC', '15'))
    MAX_CAPTURES_PER_VISIT = int(os.getenv('MAX_CAPTURES_PER_VISIT', '5'))
    CAPTURE_INTERVAL_SEC = int(os.getenv('CAPTURE_INTERVAL_SEC', '3'))
    VISIT_EXTENSION_WINDOW_SEC = int(os.getenv('VISIT_EXTENSION_WINDOW_SEC', '60'))

    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', '300'))
    OPENAI_TIMEOUT_SEC = int(os.getenv('OPENAI_TIMEOUT_SEC', '30'))
    OPENAI_MAX_RETRIES = int(os.getenv('OPENAI_MAX_RETRIES', '3'))

    SUPABASE_URL = os.getenv('VITE_SUPABASE_URL', '')
    SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', os.getenv('VITE_SUPABASE_ANON_KEY', ''))

    STORAGE_BUCKET = os.getenv('STORAGE_BUCKET', 'bird-captures')
    IMAGE_MAX_DIMENSION = int(os.getenv('IMAGE_MAX_DIMENSION', '1920'))
    IMAGE_QUALITY = int(os.getenv('IMAGE_QUALITY', '85'))

    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    HEALTH_CHECK_INTERVAL_SEC = int(os.getenv('HEALTH_CHECK_INTERVAL_SEC', '10'))

    @classmethod
    def validate(cls):
        if not cls.OPENAI_API_KEY:
            print("WARNING: OPENAI_API_KEY not set")
        if not cls.SUPABASE_URL:
            raise ValueError("VITE_SUPABASE_URL must be set")
        if not cls.SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY or VITE_SUPABASE_ANON_KEY must be set")
        return True
