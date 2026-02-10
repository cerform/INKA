import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from packages.core.logging import request_id_ctx_var, actor_id_ctx_var

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_ctx_var.set(request_id)
        
        # In a real app, actor_id would come from auth dependency
        actor_id_ctx_var.set("")
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
