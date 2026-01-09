from enum import Enum
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import uuid

class VisitState(Enum):
    IDLE = "idle"
    BIRD_PRESENT = "bird_present"
    BIRD_ABSENT = "bird_absent"
    VISIT_COMPLETE = "visit_complete"

class Visit:
    def __init__(self, session_id: str):
        self.id = str(uuid.uuid4())
        self.session_id = session_id
        self.start_time = datetime.now(timezone.utc)
        self.end_time: Optional[datetime] = None
        self.captures: List[Dict[str, Any]] = []
        self.status = "active"
        self.species: Optional[str] = None
        self.species_confidence: Optional[str] = None
        self.summary: Optional[str] = None
        self.bird_count = 1

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': int((self.end_time - self.start_time).total_seconds()) if self.end_time else None,
            'status': self.status,
            'species': self.species,
            'species_confidence': self.species_confidence,
            'summary': self.summary,
            'bird_count': self.bird_count
        }

class VisitStateMachine:
    def __init__(self, session_id: str, config, logger):
        self.session_id = session_id
        self.config = config
        self.logger = logger
        self.state = VisitState.IDLE
        self.current_visit: Optional[Visit] = None
        self.absence_start_time: Optional[datetime] = None
        self.cooldown_start_time: Optional[datetime] = None
        self.last_capture_time: Optional[datetime] = None

    def process_detection(self, bird_detected: bool, detections: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        now = datetime.now(timezone.utc)

        if self.state == VisitState.IDLE:
            if bird_detected and self._cooldown_elapsed(now):
                return self._start_visit(detections, now)

        elif self.state == VisitState.BIRD_PRESENT:
            if bird_detected:
                if self._should_capture(now):
                    return self._capture_photo(detections, now)
            else:
                self._enter_absence(now)

        elif self.state == VisitState.BIRD_ABSENT:
            if bird_detected:
                self._resume_presence(now)
            elif self._absence_timeout_elapsed(now):
                return self._complete_visit(now)

        elif self.state == VisitState.VISIT_COMPLETE:
            if self._cooldown_elapsed(now):
                self.state = VisitState.IDLE
                if bird_detected:
                    return self._start_visit(detections, now)

        return None

    def _start_visit(self, detections: List[Dict[str, Any]], now: datetime) -> Dict[str, Any]:
        self.current_visit = Visit(self.session_id)
        self.state = VisitState.BIRD_PRESENT
        self.last_capture_time = now

        self.logger.set_correlation_id(self.current_visit.id)
        self.logger.info(f"Visit started: {self.current_visit.id}")

        return {
            'action': 'start_visit',
            'visit': self.current_visit,
            'capture': True,
            'detections': detections
        }

    def _capture_photo(self, detections: List[Dict[str, Any]], now: datetime) -> Dict[str, Any]:
        if len(self.current_visit.captures) >= self.config.MAX_CAPTURES_PER_VISIT:
            return None

        self.last_capture_time = now

        return {
            'action': 'capture',
            'visit': self.current_visit,
            'capture': True,
            'detections': detections
        }

    def _enter_absence(self, now: datetime):
        self.state = VisitState.BIRD_ABSENT
        self.absence_start_time = now
        self.logger.debug(f"Bird absent, grace period started")

    def _resume_presence(self, now: datetime):
        self.state = VisitState.BIRD_PRESENT
        self.absence_start_time = None
        self.logger.debug(f"Bird returned during grace period")

    def _complete_visit(self, now: datetime) -> Dict[str, Any]:
        self.current_visit.end_time = now
        self.current_visit.status = "analyzing"
        self.state = VisitState.VISIT_COMPLETE
        self.cooldown_start_time = now
        self.absence_start_time = None

        self.logger.info(f"Visit completed: {self.current_visit.id}, duration: {(now - self.current_visit.start_time).total_seconds():.1f}s")

        visit_to_analyze = self.current_visit
        self.current_visit = None

        return {
            'action': 'complete_visit',
            'visit': visit_to_analyze,
            'capture': False
        }

    def _should_capture(self, now: datetime) -> bool:
        if not self.last_capture_time:
            return True

        elapsed = (now - self.last_capture_time).total_seconds()
        return elapsed >= self.config.CAPTURE_INTERVAL_SEC

    def _absence_timeout_elapsed(self, now: datetime) -> bool:
        if not self.absence_start_time:
            return False

        elapsed = (now - self.absence_start_time).total_seconds()
        return elapsed >= self.config.ABSENCE_GRACE_PERIOD_SEC

    def _cooldown_elapsed(self, now: datetime) -> bool:
        if not self.cooldown_start_time:
            return True

        elapsed = (now - self.cooldown_start_time).total_seconds()
        return elapsed >= self.config.VISIT_COOLDOWN_SEC

    def get_state_info(self) -> Dict[str, Any]:
        return {
            'state': self.state.value,
            'current_visit_id': self.current_visit.id if self.current_visit else None,
            'captures_count': len(self.current_visit.captures) if self.current_visit else 0
        }
