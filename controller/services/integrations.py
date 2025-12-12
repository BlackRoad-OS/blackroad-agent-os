"""
Platform Integrations Configuration

This module provides configuration and client factories for various platform integrations
used by BlackRoad Agent OS. All credentials are loaded from environment variables.

Supported Platforms:
- Cloud Providers: Railway, Cloudflare, DigitalOcean, Vercel, AWS, GCP, Azure
- Container: Docker, Kubernetes, Podman
- Version Control: GitHub, GitLab, Bitbucket
- Authentication: Clerk, Auth0, Firebase Auth
- Payments: Stripe, Paddle
- Productivity: Asana, Notion, Linear, Jira
- AI/ML: HuggingFace, OpenAI, Anthropic, Mistral, Ollama
- Mobile Dev: Working Copy, Pyto, Shellfish
- Networking: Cloudflare Tunnel, Tailscale, WireGuard, Warp

Security Note: Never hardcode credentials. Always use environment variables.
"""
import os
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, SecretStr
import structlog

logger = structlog.get_logger()


class IntegrationStatus(str, Enum):
    """Status of an integration"""
    CONFIGURED = "configured"
    MISSING_CREDENTIALS = "missing_credentials"
    NOT_CONFIGURED = "not_configured"
    ERROR = "error"


class IntegrationConfig(BaseModel):
    """Base configuration for an integration"""
    name: str
    enabled: bool = False
    status: IntegrationStatus = IntegrationStatus.NOT_CONFIGURED
    required_env_vars: list[str] = []
    optional_env_vars: list[str] = []
    documentation_url: Optional[str] = None


# =============================================================================
# CLOUD PROVIDERS
# =============================================================================

class RailwayConfig(BaseModel):
    """Railway deployment platform configuration"""
    token: Optional[SecretStr] = None
    project_id: Optional[str] = None
    environment: str = "production"

    @classmethod
    def from_env(cls) -> "RailwayConfig":
        return cls(
            token=SecretStr(os.environ.get("RAILWAY_TOKEN", "")) if os.environ.get("RAILWAY_TOKEN") else None,
            project_id=os.environ.get("RAILWAY_PROJECT_ID"),
            environment=os.environ.get("RAILWAY_ENVIRONMENT", "production"),
        )

    @property
    def is_configured(self) -> bool:
        return self.token is not None


class CloudflareConfig(BaseModel):
    """Cloudflare platform configuration (Workers, Pages, Tunnel)"""
    api_token: Optional[SecretStr] = None
    account_id: Optional[str] = None
    zone_id: Optional[str] = None
    tunnel_token: Optional[SecretStr] = None
    tunnel_id: Optional[str] = None

    @classmethod
    def from_env(cls) -> "CloudflareConfig":
        return cls(
            api_token=SecretStr(os.environ.get("CLOUDFLARE_API_TOKEN", "")) if os.environ.get("CLOUDFLARE_API_TOKEN") else None,
            account_id=os.environ.get("CLOUDFLARE_ACCOUNT_ID"),
            zone_id=os.environ.get("CLOUDFLARE_ZONE_ID"),
            tunnel_token=SecretStr(os.environ.get("CLOUDFLARE_TUNNEL_TOKEN", "")) if os.environ.get("CLOUDFLARE_TUNNEL_TOKEN") else None,
            tunnel_id=os.environ.get("CLOUDFLARE_TUNNEL_ID"),
        )

    @property
    def is_configured(self) -> bool:
        return self.api_token is not None and self.account_id is not None


class DigitalOceanConfig(BaseModel):
    """DigitalOcean (Droplets, Spaces, Apps) configuration"""
    api_token: Optional[SecretStr] = None
    spaces_access_key: Optional[SecretStr] = None
    spaces_secret_key: Optional[SecretStr] = None
    spaces_region: str = "nyc3"
    app_id: Optional[str] = None

    @classmethod
    def from_env(cls) -> "DigitalOceanConfig":
        return cls(
            api_token=SecretStr(os.environ.get("DIGITALOCEAN_TOKEN", "")) if os.environ.get("DIGITALOCEAN_TOKEN") else None,
            spaces_access_key=SecretStr(os.environ.get("DO_SPACES_ACCESS_KEY", "")) if os.environ.get("DO_SPACES_ACCESS_KEY") else None,
            spaces_secret_key=SecretStr(os.environ.get("DO_SPACES_SECRET_KEY", "")) if os.environ.get("DO_SPACES_SECRET_KEY") else None,
            spaces_region=os.environ.get("DO_SPACES_REGION", "nyc3"),
            app_id=os.environ.get("DO_APP_ID"),
        )

    @property
    def is_configured(self) -> bool:
        return self.api_token is not None


class VercelConfig(BaseModel):
    """Vercel deployment platform configuration"""
    token: Optional[SecretStr] = None
    org_id: Optional[str] = None
    project_id: Optional[str] = None
    team_id: Optional[str] = None

    @classmethod
    def from_env(cls) -> "VercelConfig":
        return cls(
            token=SecretStr(os.environ.get("VERCEL_TOKEN", "")) if os.environ.get("VERCEL_TOKEN") else None,
            org_id=os.environ.get("VERCEL_ORG_ID"),
            project_id=os.environ.get("VERCEL_PROJECT_ID"),
            team_id=os.environ.get("VERCEL_TEAM_ID"),
        )

    @property
    def is_configured(self) -> bool:
        return self.token is not None


# =============================================================================
# VERSION CONTROL
# =============================================================================

class GitHubConfig(BaseModel):
    """GitHub platform configuration"""
    token: Optional[SecretStr] = None
    app_id: Optional[str] = None
    app_private_key: Optional[SecretStr] = None
    webhook_secret: Optional[SecretStr] = None
    organization: Optional[str] = None

    @classmethod
    def from_env(cls) -> "GitHubConfig":
        return cls(
            token=SecretStr(os.environ.get("GITHUB_TOKEN", "")) if os.environ.get("GITHUB_TOKEN") else None,
            app_id=os.environ.get("GITHUB_APP_ID"),
            app_private_key=SecretStr(os.environ.get("GITHUB_APP_PRIVATE_KEY", "")) if os.environ.get("GITHUB_APP_PRIVATE_KEY") else None,
            webhook_secret=SecretStr(os.environ.get("GITHUB_WEBHOOK_SECRET", "")) if os.environ.get("GITHUB_WEBHOOK_SECRET") else None,
            organization=os.environ.get("GITHUB_ORG"),
        )

    @property
    def is_configured(self) -> bool:
        return self.token is not None or self.app_id is not None


# =============================================================================
# AUTHENTICATION PROVIDERS
# =============================================================================

class ClerkConfig(BaseModel):
    """Clerk authentication platform configuration"""
    secret_key: Optional[SecretStr] = None
    publishable_key: Optional[str] = None
    jwt_key: Optional[SecretStr] = None
    webhook_secret: Optional[SecretStr] = None

    @classmethod
    def from_env(cls) -> "ClerkConfig":
        return cls(
            secret_key=SecretStr(os.environ.get("CLERK_SECRET_KEY", "")) if os.environ.get("CLERK_SECRET_KEY") else None,
            publishable_key=os.environ.get("CLERK_PUBLISHABLE_KEY"),
            jwt_key=SecretStr(os.environ.get("CLERK_JWT_KEY", "")) if os.environ.get("CLERK_JWT_KEY") else None,
            webhook_secret=SecretStr(os.environ.get("CLERK_WEBHOOK_SECRET", "")) if os.environ.get("CLERK_WEBHOOK_SECRET") else None,
        )

    @property
    def is_configured(self) -> bool:
        return self.secret_key is not None


# =============================================================================
# PAYMENT PROVIDERS
# =============================================================================

class StripeConfig(BaseModel):
    """Stripe payment platform configuration"""
    secret_key: Optional[SecretStr] = None
    publishable_key: Optional[str] = None
    webhook_secret: Optional[SecretStr] = None
    connect_client_id: Optional[str] = None

    @classmethod
    def from_env(cls) -> "StripeConfig":
        return cls(
            secret_key=SecretStr(os.environ.get("STRIPE_SECRET_KEY", "")) if os.environ.get("STRIPE_SECRET_KEY") else None,
            publishable_key=os.environ.get("STRIPE_PUBLISHABLE_KEY"),
            webhook_secret=SecretStr(os.environ.get("STRIPE_WEBHOOK_SECRET", "")) if os.environ.get("STRIPE_WEBHOOK_SECRET") else None,
            connect_client_id=os.environ.get("STRIPE_CONNECT_CLIENT_ID"),
        )

    @property
    def is_configured(self) -> bool:
        return self.secret_key is not None


# =============================================================================
# PRODUCTIVITY TOOLS
# =============================================================================

class AsanaConfig(BaseModel):
    """Asana project management configuration"""
    access_token: Optional[SecretStr] = None
    workspace_gid: Optional[str] = None
    project_gid: Optional[str] = None

    @classmethod
    def from_env(cls) -> "AsanaConfig":
        return cls(
            access_token=SecretStr(os.environ.get("ASANA_ACCESS_TOKEN", "")) if os.environ.get("ASANA_ACCESS_TOKEN") else None,
            workspace_gid=os.environ.get("ASANA_WORKSPACE_GID"),
            project_gid=os.environ.get("ASANA_PROJECT_GID"),
        )

    @property
    def is_configured(self) -> bool:
        return self.access_token is not None


class NotionConfig(BaseModel):
    """Notion workspace configuration"""
    api_key: Optional[SecretStr] = None
    database_id: Optional[str] = None
    workspace_id: Optional[str] = None

    @classmethod
    def from_env(cls) -> "NotionConfig":
        return cls(
            api_key=SecretStr(os.environ.get("NOTION_API_KEY", "")) if os.environ.get("NOTION_API_KEY") else None,
            database_id=os.environ.get("NOTION_DATABASE_ID"),
            workspace_id=os.environ.get("NOTION_WORKSPACE_ID"),
        )

    @property
    def is_configured(self) -> bool:
        return self.api_key is not None


# =============================================================================
# CONTAINER & ORCHESTRATION
# =============================================================================

class DockerConfig(BaseModel):
    """Docker configuration"""
    host: str = "unix:///var/run/docker.sock"
    tls_verify: bool = False
    cert_path: Optional[str] = None
    registry_url: Optional[str] = None
    registry_username: Optional[str] = None
    registry_password: Optional[SecretStr] = None

    @classmethod
    def from_env(cls) -> "DockerConfig":
        return cls(
            host=os.environ.get("DOCKER_HOST", "unix:///var/run/docker.sock"),
            tls_verify=os.environ.get("DOCKER_TLS_VERIFY", "").lower() == "true",
            cert_path=os.environ.get("DOCKER_CERT_PATH"),
            registry_url=os.environ.get("DOCKER_REGISTRY_URL"),
            registry_username=os.environ.get("DOCKER_REGISTRY_USERNAME"),
            registry_password=SecretStr(os.environ.get("DOCKER_REGISTRY_PASSWORD", "")) if os.environ.get("DOCKER_REGISTRY_PASSWORD") else None,
        )

    @property
    def is_configured(self) -> bool:
        return True  # Docker is typically available by default


# =============================================================================
# NETWORKING & TUNNELS
# =============================================================================

class WarpConfig(BaseModel):
    """Cloudflare Warp configuration"""
    enabled: bool = False
    token: Optional[SecretStr] = None
    organization: Optional[str] = None

    @classmethod
    def from_env(cls) -> "WarpConfig":
        return cls(
            enabled=os.environ.get("WARP_ENABLED", "").lower() == "true",
            token=SecretStr(os.environ.get("WARP_TOKEN", "")) if os.environ.get("WARP_TOKEN") else None,
            organization=os.environ.get("WARP_ORGANIZATION"),
        )

    @property
    def is_configured(self) -> bool:
        return self.enabled


class TailscaleConfig(BaseModel):
    """Tailscale VPN configuration"""
    auth_key: Optional[SecretStr] = None
    api_key: Optional[SecretStr] = None
    tailnet: Optional[str] = None

    @classmethod
    def from_env(cls) -> "TailscaleConfig":
        return cls(
            auth_key=SecretStr(os.environ.get("TAILSCALE_AUTH_KEY", "")) if os.environ.get("TAILSCALE_AUTH_KEY") else None,
            api_key=SecretStr(os.environ.get("TAILSCALE_API_KEY", "")) if os.environ.get("TAILSCALE_API_KEY") else None,
            tailnet=os.environ.get("TAILSCALE_TAILNET"),
        )

    @property
    def is_configured(self) -> bool:
        return self.auth_key is not None or self.api_key is not None


# =============================================================================
# MOBILE DEVELOPMENT TOOLS
# =============================================================================

class ShellfishConfig(BaseModel):
    """Shellfish SSH client configuration (iOS)"""
    sync_enabled: bool = False
    server_url: Optional[str] = None

    @classmethod
    def from_env(cls) -> "ShellfishConfig":
        return cls(
            sync_enabled=os.environ.get("SHELLFISH_SYNC_ENABLED", "").lower() == "true",
            server_url=os.environ.get("SHELLFISH_SERVER_URL"),
        )

    @property
    def is_configured(self) -> bool:
        return self.sync_enabled


class WorkingCopyConfig(BaseModel):
    """Working Copy Git client configuration (iOS)"""
    callback_url: Optional[str] = None
    sync_enabled: bool = False

    @classmethod
    def from_env(cls) -> "WorkingCopyConfig":
        return cls(
            callback_url=os.environ.get("WORKING_COPY_CALLBACK_URL"),
            sync_enabled=os.environ.get("WORKING_COPY_SYNC_ENABLED", "").lower() == "true",
        )

    @property
    def is_configured(self) -> bool:
        return self.sync_enabled


class PytoConfig(BaseModel):
    """Pyto Python IDE configuration (iOS)"""
    sync_enabled: bool = False
    scripts_path: Optional[str] = None

    @classmethod
    def from_env(cls) -> "PytoConfig":
        return cls(
            sync_enabled=os.environ.get("PYTO_SYNC_ENABLED", "").lower() == "true",
            scripts_path=os.environ.get("PYTO_SCRIPTS_PATH"),
        )

    @property
    def is_configured(self) -> bool:
        return self.sync_enabled


# =============================================================================
# AI/ML PROVIDERS (extends planner_config.py)
# =============================================================================

class HuggingFaceConfig(BaseModel):
    """HuggingFace configuration for models and inference"""
    api_token: Optional[SecretStr] = None
    inference_endpoint: Optional[str] = None
    model_id: str = "mistralai/Mistral-7B-Instruct-v0.2"
    cache_dir: Optional[str] = None

    @classmethod
    def from_env(cls) -> "HuggingFaceConfig":
        return cls(
            api_token=SecretStr(os.environ.get("HF_API_TOKEN", "")) if os.environ.get("HF_API_TOKEN") else None,
            inference_endpoint=os.environ.get("HF_INFERENCE_ENDPOINT"),
            model_id=os.environ.get("HF_MODEL_ID", "mistralai/Mistral-7B-Instruct-v0.2"),
            cache_dir=os.environ.get("HF_CACHE_DIR"),
        )

    @property
    def is_configured(self) -> bool:
        return self.api_token is not None


# =============================================================================
# INTEGRATIONS MANAGER
# =============================================================================

class IntegrationsManager:
    """
    Central manager for all platform integrations.

    Provides a unified interface to check integration status,
    load configurations, and get client instances.
    """

    def __init__(self):
        self._configs: Dict[str, Any] = {}
        self._load_all_configs()

    def _load_all_configs(self):
        """Load all integration configurations from environment"""
        # Cloud Providers
        self._configs["railway"] = RailwayConfig.from_env()
        self._configs["cloudflare"] = CloudflareConfig.from_env()
        self._configs["digitalocean"] = DigitalOceanConfig.from_env()
        self._configs["vercel"] = VercelConfig.from_env()

        # Version Control
        self._configs["github"] = GitHubConfig.from_env()

        # Authentication
        self._configs["clerk"] = ClerkConfig.from_env()

        # Payments
        self._configs["stripe"] = StripeConfig.from_env()

        # Productivity
        self._configs["asana"] = AsanaConfig.from_env()
        self._configs["notion"] = NotionConfig.from_env()

        # Container
        self._configs["docker"] = DockerConfig.from_env()

        # Networking
        self._configs["warp"] = WarpConfig.from_env()
        self._configs["tailscale"] = TailscaleConfig.from_env()

        # Mobile Dev
        self._configs["shellfish"] = ShellfishConfig.from_env()
        self._configs["working_copy"] = WorkingCopyConfig.from_env()
        self._configs["pyto"] = PytoConfig.from_env()

        # AI/ML
        self._configs["huggingface"] = HuggingFaceConfig.from_env()

    def get_config(self, name: str) -> Optional[Any]:
        """Get configuration for a specific integration"""
        return self._configs.get(name)

    def get_status(self) -> Dict[str, IntegrationStatus]:
        """Get status of all integrations"""
        status = {}
        for name, config in self._configs.items():
            if hasattr(config, "is_configured"):
                status[name] = IntegrationStatus.CONFIGURED if config.is_configured else IntegrationStatus.MISSING_CREDENTIALS
            else:
                status[name] = IntegrationStatus.NOT_CONFIGURED
        return status

    def get_configured_integrations(self) -> list[str]:
        """Get list of configured integrations"""
        return [
            name for name, config in self._configs.items()
            if hasattr(config, "is_configured") and config.is_configured
        ]

    def get_integration_info(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed info about all integrations"""
        info = {}
        for name, config in self._configs.items():
            is_configured = hasattr(config, "is_configured") and config.is_configured
            info[name] = {
                "configured": is_configured,
                "status": IntegrationStatus.CONFIGURED.value if is_configured else IntegrationStatus.MISSING_CREDENTIALS.value,
            }
        return info

    def reload(self):
        """Reload all configurations from environment"""
        self._load_all_configs()
        logger.info("integrations_reloaded", configured=len(self.get_configured_integrations()))


# Global instance
integrations = IntegrationsManager()


def get_integration_status() -> Dict[str, Any]:
    """Get current status of all integrations"""
    return integrations.get_integration_info()
