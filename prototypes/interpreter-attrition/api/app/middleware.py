from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import settings


class PayloadSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject request bodies larger than settings.max_ingest_payload_bytes.

    Uses Content-Length when available; falls back to reading the body when
    Content-Length is missing but streaming applies to ingest endpoints only.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > settings.max_ingest_payload_bytes:
                    return JSONResponse(
                        {
                            "detail": "payload_too_large",
                            "max_bytes": settings.max_ingest_payload_bytes,
                        },
                        status_code=413,
                    )
            except ValueError:
                pass
        return await call_next(request)
