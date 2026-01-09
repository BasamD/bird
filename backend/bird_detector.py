import cv2
import time
import uuid
import base64
import numpy as np
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from ultralytics import YOLO
from supabase import Client
from PIL import Image
import io

from config import Config
from logger import StructuredLogger
from state_machine import VisitStateMachine, VisitState

class BirdDetector:
    def __init__(self, supabase_client: Client, config: Config):
        self.supabase = supabase_client
        self.config = config
        self.logger = StructuredLogger(supabase_client, 'detector')
        self.session_id = str(uuid.uuid4())

        self.model: Optional[YOLO] = None
        self.cap: Optional[cv2.VideoCapture] = None
        self.state_machine: Optional[VisitStateMachine] = None
        self.running = False

        self.consecutive_failures = 0
        self.last_detection_time = 0

    def initialize(self) -> bool:
        try:
            self.logger.info(f"Initializing bird detector, session: {self.session_id}")

            self.logger.info(f"Loading YOLO model: {self.config.YOLO_MODEL_PATH}")
            self.model = YOLO(self.config.YOLO_MODEL_PATH)
            self.update_health('detector', 'healthy', 'Model loaded')

            self.logger.info(f"Connecting to RTSP stream...")
            if not self._connect_camera():
                return False

            self.state_machine = VisitStateMachine(self.session_id, self.config, self.logger)

            self.logger.info("Bird detector initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}")
            self.update_health('detector', 'unhealthy', f'Initialization failed: {e}')
            return False

    def _connect_camera(self) -> bool:
        backoff_seconds = 2
        max_backoff = 60
        attempts = 0

        while attempts < 10:
            try:
                self.logger.info(f"Connecting to camera (attempt {attempts + 1})...")
                self.cap = cv2.VideoCapture(self.config.RTSP_URL)

                if self.cap.isOpened():
                    ret, frame = self.cap.read()
                    if ret:
                        self.logger.info("Camera connected successfully")
                        self.update_health('camera', 'connected', 'Streaming')
                        self.consecutive_failures = 0
                        return True

                self.logger.warning(f"Camera connection failed, retrying in {backoff_seconds}s")
                time.sleep(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 2, max_backoff)
                attempts += 1

            except Exception as e:
                self.logger.error(f"Camera connection error: {e}")
                time.sleep(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 2, max_backoff)
                attempts += 1

        self.update_health('camera', 'disconnected', 'Failed to connect after 10 attempts')
        return False

    def run(self):
        self.running = True
        self.logger.info("Starting detection loop")

        while self.running:
            try:
                now_ms = time.time() * 1000

                if (now_ms - self.last_detection_time) < self.config.DETECTION_INTERVAL_MS:
                    time.sleep(0.01)
                    continue

                ret, frame = self.cap.read()

                if not ret:
                    self.consecutive_failures += 1
                    self.logger.warning(f"Frame read failed (failures: {self.consecutive_failures})")

                    if self.consecutive_failures >= 10:
                        self.logger.error("Too many consecutive failures, reconnecting...")
                        self.update_health('camera', 'disconnected', 'Stream lost')
                        if not self._connect_camera():
                            self.logger.critical("Failed to reconnect to camera")
                            time.sleep(10)
                    continue

                self.consecutive_failures = 0
                self.last_detection_time = now_ms

                bird_detected, detections = self._detect_birds(frame)

                result = self.state_machine.process_detection(bird_detected, detections)

                if result:
                    self._handle_state_action(result, frame)

            except KeyboardInterrupt:
                self.logger.info("Shutting down...")
                break
            except Exception as e:
                self.logger.error(f"Error in detection loop: {e}", {'error': str(e)})
                time.sleep(1)

        self.cleanup()

    def _detect_birds(self, frame: np.ndarray) -> Tuple[bool, List[Dict[str, Any]]]:
        height, width = frame.shape[:2]

        roi_x1 = int(width * self.config.ROI_X1)
        roi_y1 = int(height * self.config.ROI_Y1)
        roi_x2 = int(width * self.config.ROI_X2)
        roi_y2 = int(height * self.config.ROI_Y2)

        roi_frame = frame[roi_y1:roi_y2, roi_x1:roi_x2]

        results = self.model(roi_frame, conf=self.config.CONFIDENCE_THRESHOLD, verbose=False)

        detections = []
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])

                if class_id == self.config.BIRD_CLASS_ID:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = float(box.conf[0])

                    bbox_width = x2 - x1
                    bbox_height = y2 - y1
                    bbox_area = bbox_width * bbox_height
                    roi_area = (roi_x2 - roi_x1) * (roi_y2 - roi_y1)
                    area_ratio = bbox_area / roi_area

                    if area_ratio >= self.config.MIN_AREA_RATIO:
                        detections.append({
                            'bbox': [
                                int(x1 + roi_x1),
                                int(y1 + roi_y1),
                                int(x2 + roi_x1),
                                int(y2 + roi_y1)
                            ],
                            'confidence': confidence,
                            'class_id': class_id,
                            'class_name': 'bird',
                            'area_ratio': area_ratio
                        })

        return len(detections) > 0, detections

    def _handle_state_action(self, result: Dict[str, Any], frame: np.ndarray):
        action = result['action']
        visit = result['visit']

        if action == 'start_visit':
            self._create_visit_in_db(visit)

        if result.get('capture'):
            self._capture_and_store(visit, frame, result['detections'])

        if action == 'complete_visit':
            self._finalize_visit(visit)

    def _create_visit_in_db(self, visit):
        try:
            visit_data = visit.to_dict()
            self.supabase.table('visits').insert(visit_data).execute()
            self.logger.info(f"Created visit in database: {visit.id}")
        except Exception as e:
            self.logger.error(f"Failed to create visit in database: {e}")

    def _capture_and_store(self, visit, frame: np.ndarray, detections: List[Dict[str, Any]]):
        try:
            capture_id = str(uuid.uuid4())
            timestamp = datetime.now(timezone.utc)

            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, self.config.IMAGE_QUALITY])
            image_bytes = buffer.tobytes()

            filename = f"{visit.id}/{capture_id}.jpg"

            try:
                self.supabase.storage.from_(self.config.STORAGE_BUCKET).upload(
                    filename,
                    image_bytes,
                    {'content-type': 'image/jpeg'}
                )
                image_url = f"{self.config.SUPABASE_URL}/storage/v1/object/public/{self.config.STORAGE_BUCKET}/{filename}"
            except Exception as storage_error:
                self.logger.warning(f"Storage upload failed, using local fallback: {storage_error}")
                image_url = f"local://{filename}"

            capture_data = {
                'id': capture_id,
                'visit_id': visit.id,
                'timestamp': timestamp.isoformat(),
                'image_url': image_url,
                'detections': detections,
                'is_best_capture': len(visit.captures) == 0
            }

            self.supabase.table('captures').insert(capture_data).execute()
            visit.captures.append(capture_data)

            self.logger.info(f"Captured photo {len(visit.captures)}/{self.config.MAX_CAPTURES_PER_VISIT} for visit {visit.id}")

        except Exception as e:
            self.logger.error(f"Failed to capture and store image: {e}")

    def _finalize_visit(self, visit):
        try:
            visit_data = visit.to_dict()
            self.supabase.table('visits').update(visit_data).eq('id', visit.id).execute()
            self.logger.info(f"Finalized visit: {visit.id}")

        except Exception as e:
            self.logger.error(f"Failed to finalize visit: {e}")

    def update_health(self, component: str, status: str, message: str, metadata: Optional[Dict] = None):
        try:
            health_data = {
                'component': component,
                'status': status,
                'last_check': datetime.now(timezone.utc).isoformat(),
                'message': message,
                'metadata': metadata or {}
            }
            self.supabase.table('system_health').upsert(health_data).execute()
        except Exception as e:
            self.logger.error(f"Failed to update health status: {e}")

    def cleanup(self):
        self.running = False
        if self.cap:
            self.cap.release()
        self.logger.info("Detector cleaned up")
        self.update_health('detector', 'unhealthy', 'Stopped')
        self.update_health('camera', 'disconnected', 'Stopped')
