"""
BlackRoad Agent OS - Controller Service

Central orchestration service for managing Raspberry Pi agents.
"""
import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import structlog
import uvicorn

from api import agents_router, tasks_router, websocket_router
from api.websocket import dispatch_loop
from core.registry import registry
from core.auth import get_auth_config, check_rate_limit, generate_token
from services.audit import audit, AuditEventType, AuditEvent

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("controller_starting", version="0.1.0")

    # Log system start
    audit.log(AuditEvent(
        event_type=AuditEventType.SYSTEM_STARTED,
        actor_type="system",
        action="start",
        details={"version": "0.1.0"},
    ))

    # Start background tasks
    dispatch_task = asyncio.create_task(dispatch_loop())
    health_task = asyncio.create_task(health_check_loop())

    yield

    # Cleanup
    dispatch_task.cancel()
    health_task.cancel()

    try:
        await dispatch_task
    except asyncio.CancelledError:
        pass

    try:
        await health_task
    except asyncio.CancelledError:
        pass

    # Log system stop
    audit.log(AuditEvent(
        event_type=AuditEventType.SYSTEM_STOPPED,
        actor_type="system",
        action="stop",
    ))

    logger.info("controller_stopped")


async def health_check_loop():
    """Background loop to check agent health"""
    while True:
        await asyncio.sleep(30)
        try:
            await registry.check_health()
        except Exception as e:
            logger.error("health_check_error", error=str(e))


# Create FastAPI app
app = FastAPI(
    title="BlackRoad Agent OS",
    description="Distributed agent orchestration system for Raspberry Pi machines",
    version="0.1.0",
    lifespan=lifespan,
)

# Get CORS origins from environment (comma-separated list)
cors_origins = os.environ.get("CORS_ORIGINS", "").split(",")
cors_origins = [origin.strip() for origin in cors_origins if origin.strip()]

# Default to restrictive CORS in production, allow all in development
if not cors_origins:
    # Check if we're in development mode
    if os.environ.get("ENV", "development") == "development":
        cors_origins = ["*"]
    else:
        # Production default: only allow same-origin
        cors_origins = [
            "https://agent.blackroad.ai",
            "https://api.blackroad.ai",
            "https://app.blackroad.ai",
        ]

# CORS middleware for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting to all requests"""
    client_ip = request.client.host if request.client else "unknown"

    # Skip rate limiting for health checks
    if request.url.path in ["/health", "/"]:
        return await call_next(request)

    if not check_rate_limit(client_ip):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Rate limit exceeded. Please try again later."}
        )

    return await call_next(request)


# Include routers
app.include_router(agents_router)
app.include_router(tasks_router)
app.include_router(websocket_router)


@app.get("/")
async def root():
    """Root endpoint with system info"""
    auth_config = get_auth_config()
    return {
        "name": "BlackRoad Agent OS",
        "version": "0.1.0",
        "agents": len(registry.get_all()),
        "agents_online": len(registry.get_online()),
        "auth_enabled": auth_config.auth_enabled,
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    from services.planner_config import PlannerConfig
    config = PlannerConfig.from_env()
    auth_config = get_auth_config()

    return {
        "status": "healthy",
        "planner": {
            "provider": config.provider.value,
        },
        "agents": {
            "total": len(registry.get_all()),
            "online": len(registry.get_online()),
            "available": len(registry.get_available()),
        },
        "security": {
            "auth_enabled": auth_config.auth_enabled,
            "cors_origins": cors_origins if cors_origins != ["*"] else "all (development)",
        },
    }


@app.post("/auth/token")
async def create_auth_token(request: Request):
    """
    Generate an API token for authenticated access.
    In production, this should validate credentials first.
    """
    auth_config = get_auth_config()

    if not auth_config.auth_enabled:
        return {"token": "auth_disabled", "message": "Authentication is disabled"}

    # In a real implementation, validate credentials here
    # For now, generate a token with a default subject
    body = await request.json() if request.headers.get("content-type") == "application/json" else {}
    subject = body.get("subject", "api_user")

    token = generate_token(subject, "api")

    return {
        "token": token,
        "type": "Bearer",
        "expires_in": auth_config.token_expiration_hours * 3600,
    }


# Mount static files for UI (if exists)
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info",
    )
