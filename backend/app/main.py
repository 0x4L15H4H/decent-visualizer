from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.config import get_settings
from app.routers import beans, health, shots

settings = get_settings()

app = FastAPI()

# Parse the comma-separated origin list. Credentialed CORS cannot use a
# wildcard, so an explicit, non-empty list is required.
allow_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
if not allow_origins:
    raise RuntimeError("CORS_ORIGINS must list at least one explicit origin")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compress responses. The shot measurement time-series is large and highly
# repetitive, so gzip cuts VM egress (a scarce GCP free-tier resource) by ~5-10x.
app.add_middleware(GZipMiddleware, minimum_size=500)

app.include_router(health.router, prefix="/api")
app.include_router(shots.router, prefix="/api")
app.include_router(beans.router, prefix="/api")
