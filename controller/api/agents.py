"""
Agent API Routes - Manage and query agents
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends

from models import Agent, AgentStatus
from core.registry import registry
from core.auth import get_current_user, get_optional_user, TokenPayload

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("", response_model=list[Agent])
async def list_agents(
    status: Optional[AgentStatus] = None,
    role: Optional[str] = None,
    current_user: TokenPayload = Depends(get_current_user),
):
    """List all registered agents with optional filters (requires authentication)"""
    agents = registry.get_all()

    if status:
        agents = [a for a in agents if a.status == status]
    if role:
        agents = [a for a in agents if role in a.roles]

    return agents


@router.get("/online", response_model=list[Agent])
async def list_online_agents(
    current_user: TokenPayload = Depends(get_current_user),
):
    """List all online agents (requires authentication)"""
    return registry.get_online()


@router.get("/available", response_model=list[Agent])
async def list_available_agents(
    current_user: TokenPayload = Depends(get_current_user),
):
    """List agents that are online and not busy (requires authentication)"""
    return registry.get_available()


@router.get("/{agent_id}", response_model=Agent)
async def get_agent(
    agent_id: str,
    current_user: TokenPayload = Depends(get_current_user),
):
    """Get a specific agent by ID (requires authentication)"""
    agent = registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return agent


@router.get("/{agent_id}/workspaces")
async def get_agent_workspaces(
    agent_id: str,
    current_user: TokenPayload = Depends(get_current_user),
):
    """Get workspaces on a specific agent (requires authentication)"""
    agent = registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return agent.workspaces or []


@router.post("/{agent_id}/ping")
async def ping_agent(
    agent_id: str,
    current_user: TokenPayload = Depends(get_current_user),
):
    """Send a ping to an agent (requires authentication)"""
    success = await registry.send_to_agent(agent_id, {"type": "ping"})
    if not success:
        raise HTTPException(status_code=503, detail=f"Agent {agent_id} not reachable")
    return {"status": "sent"}


@router.delete("/{agent_id}")
async def remove_agent(
    agent_id: str,
    current_user: TokenPayload = Depends(get_current_user),
):
    """Remove an agent from the registry (requires authentication)"""
    agent = registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    await registry.unregister(agent_id)
    return {"status": "removed", "agent_id": agent_id}
