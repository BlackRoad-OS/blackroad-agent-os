"""
Authentication Module - Token-based authentication for API and WebSocket connections
"""
import os
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional
from functools import wraps

from fastapi import HTTPException, Security, Depends, WebSocket, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import structlog

logger = structlog.get_logger()

# Security scheme for REST API
security = HTTPBearer(auto_error=False)


class AuthConfig(BaseModel):
    """Authentication configuration"""
    # API secret key for signing tokens
    api_secret_key: str
    # Shared token for agent authentication
    agent_auth_token: str
    # Token expiration time in hours
    token_expiration_hours: int = 24
    # Enable authentication (can be disabled for development)
    auth_enabled: bool = True

    @classmethod
    def from_env(cls) -> "AuthConfig":
        """Load configuration from environment variables"""
        api_secret = os.environ.get("API_SECRET_KEY", "")
        agent_token = os.environ.get("AGENT_AUTH_TOKEN", "")
        auth_enabled = os.environ.get("AUTH_ENABLED", "true").lower() != "false"

        # Generate default keys for development if not set
        if not api_secret:
            if auth_enabled:
                logger.warning("API_SECRET_KEY not set - generating temporary key (NOT FOR PRODUCTION)")
            api_secret = secrets.token_hex(32)

        if not agent_token:
            if auth_enabled:
                logger.warning("AGENT_AUTH_TOKEN not set - generating temporary token (NOT FOR PRODUCTION)")
            agent_token = secrets.token_hex(32)

        return cls(
            api_secret_key=api_secret,
            agent_auth_token=agent_token,
            token_expiration_hours=int(os.environ.get("TOKEN_EXPIRATION_HOURS", "24")),
            auth_enabled=auth_enabled,
        )


class TokenPayload(BaseModel):
    """JWT-like token payload"""
    sub: str  # Subject (user/agent ID)
    type: str  # Token type: "api" or "agent"
    exp: datetime  # Expiration time
    iat: datetime  # Issued at


# Global config instance
_auth_config: Optional[AuthConfig] = None


def get_auth_config() -> AuthConfig:
    """Get or create auth config singleton"""
    global _auth_config
    if _auth_config is None:
        _auth_config = AuthConfig.from_env()
    return _auth_config


def generate_token(subject: str, token_type: str = "api") -> str:
    """
    Generate a simple signed token.
    Format: {payload_base64}.{signature}
    """
    import base64
    import json

    config = get_auth_config()

    payload = TokenPayload(
        sub=subject,
        type=token_type,
        exp=datetime.utcnow() + timedelta(hours=config.token_expiration_hours),
        iat=datetime.utcnow(),
    )

    # Encode payload
    payload_json = payload.model_dump_json()
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode()

    # Create signature
    signature = hmac.new(
        config.api_secret_key.encode(),
        payload_b64.encode(),
        hashlib.sha256
    ).hexdigest()

    return f"{payload_b64}.{signature}"


def verify_token(token: str) -> Optional[TokenPayload]:
    """
    Verify and decode a token.
    Returns payload if valid, None otherwise.
    """
    import base64
    import json

    config = get_auth_config()

    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None

        payload_b64, signature = parts

        # Verify signature
        expected_sig = hmac.new(
            config.api_secret_key.encode(),
            payload_b64.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            logger.warning("token_signature_invalid")
            return None

        # Decode payload
        payload_json = base64.urlsafe_b64decode(payload_b64).decode()
        payload_data = json.loads(payload_json)

        # Parse dates
        payload_data["exp"] = datetime.fromisoformat(payload_data["exp"])
        payload_data["iat"] = datetime.fromisoformat(payload_data["iat"])

        payload = TokenPayload(**payload_data)

        # Check expiration
        if payload.exp < datetime.utcnow():
            logger.warning("token_expired", subject=payload.sub)
            return None

        return payload

    except Exception as e:
        logger.warning("token_verification_failed", error=str(e))
        return None


def verify_agent_token(token: str) -> bool:
    """
    Verify an agent authentication token.
    Agents use a simple shared secret for authentication.
    """
    config = get_auth_config()
    return hmac.compare_digest(token, config.agent_auth_token)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[TokenPayload]:
    """
    FastAPI dependency for authenticated endpoints.
    Returns the token payload if valid.
    """
    config = get_auth_config()

    # If auth is disabled, return a dummy payload
    if not config.auth_enabled:
        return TokenPayload(
            sub="anonymous",
            type="api",
            exp=datetime.utcnow() + timedelta(hours=24),
            iat=datetime.utcnow(),
        )

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[TokenPayload]:
    """
    FastAPI dependency for optionally authenticated endpoints.
    Returns None if no valid token provided.
    """
    config = get_auth_config()

    if not config.auth_enabled:
        return TokenPayload(
            sub="anonymous",
            type="api",
            exp=datetime.utcnow() + timedelta(hours=24),
            iat=datetime.utcnow(),
        )

    if not credentials:
        return None

    return verify_token(credentials.credentials)


async def authenticate_websocket(websocket: WebSocket, token: Optional[str] = None) -> bool:
    """
    Authenticate a WebSocket connection.
    Token can be passed as query parameter or in first message.
    """
    config = get_auth_config()

    if not config.auth_enabled:
        return True

    if not token:
        # Try to get token from query parameters
        token = websocket.query_params.get("token")

    if not token:
        return False

    # Try agent token first
    if verify_agent_token(token):
        return True

    # Try API token
    payload = verify_token(token)
    if payload:
        return True

    return False


async def authenticate_agent_websocket(websocket: WebSocket) -> tuple[bool, Optional[str]]:
    """
    Authenticate an agent WebSocket connection.
    Returns (success, agent_token) tuple.
    """
    config = get_auth_config()

    if not config.auth_enabled:
        return True, None

    # Get token from query parameter
    token = websocket.query_params.get("token")

    if not token:
        logger.warning("agent_connection_no_token", client=websocket.client)
        return False, None

    if verify_agent_token(token):
        return True, token

    logger.warning("agent_connection_invalid_token", client=websocket.client)
    return False, None


def require_auth(func):
    """Decorator for routes that require authentication"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Get current user from kwargs or raise
        user = kwargs.get("current_user")
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )
        return await func(*args, **kwargs)
    return wrapper


# Rate limiting (simple in-memory implementation)
_rate_limit_store: dict[str, list[datetime]] = {}
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 100  # per window


def check_rate_limit(client_ip: str) -> bool:
    """
    Check if a client has exceeded the rate limit.
    Returns True if request is allowed, False if rate limited.
    """
    now = datetime.utcnow()
    window_start = now - timedelta(seconds=RATE_LIMIT_WINDOW)

    if client_ip not in _rate_limit_store:
        _rate_limit_store[client_ip] = []

    # Clean old entries
    _rate_limit_store[client_ip] = [
        t for t in _rate_limit_store[client_ip]
        if t > window_start
    ]

    # Check limit
    if len(_rate_limit_store[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
        logger.warning("rate_limit_exceeded", client_ip=client_ip)
        return False

    # Add current request
    _rate_limit_store[client_ip].append(now)
    return True
