from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.middleware import PayloadSizeLimitMiddleware
from app.routers.ingest import router as ingest_router

app = FastAPI(
    title="ChurnScope API",
    version="0.1.0",
    description="Interpreter attrition early-warning API for interpretation LSPs.",
)

app.add_middleware(PayloadSizeLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest_router)


@app.get("/health")
def health():
    return {"status": "ok", "ts": datetime.now(timezone.utc).isoformat()}
