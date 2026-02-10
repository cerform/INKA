import logging
import sys
import uuid
from contextvars import ContextVar
from pythonjsonlogger import jsonlogger

request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="")
actor_id_ctx_var: ContextVar[str] = ContextVar("actor_id", default="")

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['request_id'] = request_id_ctx_var.get()
        log_record['actor_id'] = actor_id_ctx_var.get()
        if not log_record.get('timestamp'):
            from datetime import datetime
            log_record['timestamp'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname

def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s')
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    
    # Silence noise
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.error").handlers = []
    
logger = logging.getLogger(__name__)
