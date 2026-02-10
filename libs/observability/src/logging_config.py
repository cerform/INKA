import logging
import json
import uuid
from datetime import datetime
from pythonjsonlogger import jsonlogger
from packages.core.config import settings

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get('timestamp'):
            now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            log_record['timestamp'] = now
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname
        
        # Add tracking and business context
        log_record['request_id'] = getattr(record, 'request_id', None)
        log_record['actor_id'] = getattr(record, 'actor_id', None)
        log_record['role'] = getattr(record, 'role', None)
        log_record['action'] = getattr(record, 'action', None)
        log_record['entity'] = getattr(record, 'entity', None)
        log_record['latency_ms'] = getattr(record, 'latency_ms', None)

def setup_logging():
    logger = logging.getLogger()
    log_handler = logging.StreamHandler()
    formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s')
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)
    logger.setLevel(logging.INFO)
    
    # Silence overly verbose loggers
    logging.getLogger("python-telegram-bot").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

# Context filter to add request/actor IDs automatically
class ContextFilter(logging.Filter):
    def __init__(self):
        super().__init__()
        self.request_id = None
        self.actor_id = None

    def filter(self, record):
        record.request_id = self.request_id
        record.actor_id = self.actor_id
        return True
