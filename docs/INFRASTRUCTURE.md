# BlackRoad Agent OS - Infrastructure Configuration

This document describes infrastructure architecture and setup guides.
**Note:** All sensitive credentials must be stored in environment variables or secret managers - never in code.

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     BLACKROAD AGENT OS                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  Controller  │◄───│  Cloudflare  │◄───│   Railway    │      │
│  │  (Mac/Cloud) │    │   Tunnel     │    │   (Deploy)   │      │
│  └──────┬───────┘    └──────────────┘    └──────────────┘      │
│         │                                                       │
│         │ WebSocket (WSS)                                       │
│         ▼                                                       │
│  ┌──────────────┐    ┌──────────────┐                          │
│  │   Agent 1    │    │   Agent 2    │    ... more Pi agents    │
│  │  (Primary)   │    │ (Secondary)  │                          │
│  └──────────────┘    └──────────────┘                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Cloudflare Tunnel Setup

### Configuration
Cloudflare Tunnel provides secure, authenticated access to the controller without exposing ports.

Required environment variables:
```bash
CLOUDFLARE_ACCOUNT_ID=<your-account-id>
CLOUDFLARE_TUNNEL_ID=<your-tunnel-id>
CLOUDFLARE_TUNNEL_TOKEN=<your-tunnel-token>
```

### Tunnel Token
The tunnel runs with a token-based configuration (no local config file needed):
```bash
cloudflared --no-autoupdate tunnel run --token $CLOUDFLARE_TUNNEL_TOKEN
```

### Systemd Service (on Pi)
Location: `/etc/systemd/system/cloudflared.service`
```ini
[Unit]
Description=cloudflared
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/cloudflared --no-autoupdate tunnel run --token ${CLOUDFLARE_TUNNEL_TOKEN}
EnvironmentFile=/etc/cloudflared/env
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

Commands:
```bash
# Enable on boot
sudo systemctl enable cloudflared

# Start/stop/restart
sudo systemctl start cloudflared
sudo systemctl stop cloudflared
sudo systemctl restart cloudflared

# Check status
sudo systemctl status cloudflared
```

### Ingress Routes (configure in Cloudflare dashboard)
```yaml
ingress:
  - hostname: agent.your-domain.com
    service: http://localhost:8000
  - hostname: api.your-domain.com
    service: http://localhost:8000
  - service: http_status:404
```

## Platform Deployments

### Railway Projects
Configure via Railway dashboard or CLI.

| Project Type | Purpose |
|--------------|---------|
| operating-system | Main OS services |
| core | Core components |
| web | Web interfaces |
| api | API services |
| docs | Documentation |
| operator | Operator services |

### Deployment Commands
```bash
# List all projects
railway list

# Link to project
railway link

# Deploy current directory
railway up

# View logs
railway logs
```

## Raspberry Pi Agent Setup

### Primary Agent Setup
```bash
# Set environment variables
export AGENT_ID="agent-primary"
export CONTROLLER_URL="wss://api.your-domain.com/ws/agent"
export AGENT_TOKEN="<secure-token>"  # Required for authentication
export AGENT_ROLES="web,worker"
export AGENT_TAGS="production"
```

### Secondary Agent Setup
```bash
export AGENT_ID="agent-secondary"
export CONTROLLER_URL="wss://api.your-domain.com/ws/agent"
export AGENT_TOKEN="<secure-token>"
export AGENT_ROLES="worker"
export AGENT_TAGS="staging"
```

**Security Note:** Always change default credentials and use strong, unique passwords for each agent.

## GitHub Repositories

### Organization Structure

| Repository | Description |
|------------|-------------|
| blackroad-agent-os | Main agent orchestration system |
| blackroad-os-core | Core OS components |
| blackroad-os-infra | Infrastructure configs |
| blackroad-os-web | Web interfaces |
| blackroad-os-api | API services |
| blackroad-os-docs | Documentation |

### SSH Deploy Keys
Each Pi should have an SSH key added to GitHub for GitOps sync:
```bash
# Generate key on Pi
ssh-keygen -t ed25519 -C "agent@github"

# Add to GitHub (replace with your repo)
gh repo deploy-key add ~/.ssh/id_ed25519.pub -R YourOrg/your-repo
```

## Environment Variables Reference

### Controller (.env)
```bash
# Server
PORT=8000

# Authentication (REQUIRED)
API_SECRET_KEY=<generate-secure-key>
AGENT_AUTH_TOKEN=<shared-agent-token>

# CORS (configure for your domains)
CORS_ORIGINS=https://app.your-domain.com,https://api.your-domain.com

# LLM Provider (auto-detected if not set)
# PLANNER_PROVIDER=anthropic|openai|mistral|ollama|stub

# Anthropic
ANTHROPIC_API_KEY=<your-key>

# OpenAI
OPENAI_API_KEY=<your-key>

# Mistral
MISTRAL_API_KEY=<your-key>

# HuggingFace / Open Source Models
HF_API_TOKEN=<your-token>

# Ollama (local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

### Agent (on each Pi)
```bash
AGENT_ID=<unique-agent-id>
CONTROLLER_URL=wss://api.your-domain.com/ws/agent
AGENT_TOKEN=<auth-token>
AGENT_ROLES=web,worker
AGENT_TAGS=production
```

## GitOps Sync

### Service Configuration
Located on each Pi at `/etc/systemd/system/`:
- `gitops-sync.service` - Sync service
- `gitops-sync.timer` - 5-minute interval

### Sync Script
`/usr/local/bin/gitops-sync.sh` - Pulls all repos in ~/blackroad/

### Monitored Repos
- blackroad-agent-os
- blackroad-os-core
- blackroad-os-infra
- blackroad-os-web
- blackroad-os-api

## Network Architecture

```
Internet
    │
    ▼
Cloudflare Edge (*.your-domain.com)
    │
    ▼ (Tunnel: encrypted connection)
    │
Primary Agent (192.168.x.x)
    │
    ├── Controller (port 8000) ◄── WebSocket ──┐
    │                                          │
    │                                          │
Local Network (192.168.x.0/24)                 │
    │                                          │
    ├── Primary agent ─────────────────────────┤
    │                                          │
    └── Secondary agent ───────────────────────┘
```

## Useful Commands

### Cloudflare
```bash
# Check tunnel status on Pi
sudo systemctl status cloudflared

# View tunnel logs
sudo journalctl -u cloudflared -f

# Restart tunnel
sudo systemctl restart cloudflared
```

### Railway
```bash
# Check auth
railway whoami

# List projects
railway list

# Deploy
railway up
```

### Agent Management
```bash
# Check controller health
curl http://localhost:8000/health

# List connected agents (requires auth header in production)
curl -H "Authorization: Bearer $API_TOKEN" http://localhost:8000/api/agents

# Submit a task (requires auth header in production)
curl -X POST http://localhost:8000/api/tasks \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"request": "check uptime", "skip_approval": true}'
```

## Secrets Management

**CRITICAL:** Never commit secrets to git. Use:
1. Environment variables with `.env` files (gitignored)
2. Secret managers (Doppler, Vault, AWS Secrets Manager)
3. Platform secret storage (Railway, Cloudflare, GitHub Secrets)

### Required Secrets
| Secret | Purpose | Storage Location |
|--------|---------|------------------|
| API_SECRET_KEY | JWT signing | Controller .env |
| AGENT_AUTH_TOKEN | Agent authentication | Controller + Agent .env |
| ANTHROPIC_API_KEY | LLM planning | Controller .env |
| OPENAI_API_KEY | LLM planning | Controller .env |
| CLOUDFLARE_API_TOKEN | Tunnel management | GitHub Secrets |
| CLOUDFLARE_TUNNEL_TOKEN | Tunnel auth | Pi systemd env |

### Generating Secure Tokens
```bash
# Generate a secure API secret key
openssl rand -base64 32

# Generate agent auth token
openssl rand -hex 32
```
