import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from supabase import Client

class StructuredLogger:
    def __init__(self, supabase_client: Client, component: str):
        self.supabase = supabase_client
        self.component = component
        self.correlation_id: Optional[str] = None

    def set_correlation_id(self, correlation_id: str):
        self.correlation_id = correlation_id

    def log(self, level: str, message: str, metadata: Optional[Dict[str, Any]] = None):
        timestamp = datetime.now(timezone.utc).isoformat()

        print(f"[{timestamp}] [{level}] [{self.component}] {message}")

        if metadata:
            print(f"  Metadata: {metadata}")

        try:
            log_entry = {
                'timestamp': timestamp,
                'level': level,
                'component': self.component,
                'message': message,
                'metadata': metadata or {},
                'correlation_id': self.correlation_id
            }
            self.supabase.table('system_logs').insert(log_entry).execute()
        except Exception as e:
            print(f"Failed to write log to database: {e}")

    def debug(self, message: str, metadata: Optional[Dict[str, Any]] = None):
        self.log('DEBUG', message, metadata)

    def info(self, message: str, metadata: Optional[Dict[str, Any]] = None):
        self.log('INFO', message, metadata)

    def warning(self, message: str, metadata: Optional[Dict[str, Any]] = None):
        self.log('WARNING', message, metadata)

    def error(self, message: str, metadata: Optional[Dict[str, Any]] = None):
        self.log('ERROR', message, metadata)

    def critical(self, message: str, metadata: Optional[Dict[str, Any]] = None):
        self.log('CRITICAL', message, metadata)
