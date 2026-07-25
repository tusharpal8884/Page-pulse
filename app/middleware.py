import uuid
import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s", "level":"%(levelname)s", "request_id":"%(request_id)s", "message":%(message)s}'
)
logger = logging.getLogger("page_pulse")

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        
        start_time = time.perf_counter()
        
        # Inject request_id into logger contextual details
        extra = {"request_id": request_id}
        logger.info(f'"Processing {request.method} {request.url.path}"', extra=extra)

        response = await call_next(request)
        
        process_time = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        
        logger.info(
            f'"Completed {request.method} {request.url.path} with status {response.status_code} in {process_time}ms"',
            extra=extra
        )
        return response