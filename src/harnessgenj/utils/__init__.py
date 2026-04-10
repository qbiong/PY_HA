"""
HarnessGenJ Utils - 工具模块

提供通用工具函数和类：
- agent_context: Agent 上下文隔离（contextvars）
"""

from harnessgenj.utils.agent_context import (
    AgentContext,
    TeammateContext,
    get_agent_context,
    get_agent_id,
    run_in_agent_context,
    create_agent_context,
    get_teammate_context,
    run_in_teammate_context,
    create_teammate_context,
    get_permission_context,
    run_in_permission_context,
    request_permission_from_parent,
    is_in_agent_context,
    is_in_teammate_context,
    get_context_summary,
)

__all__ = [
    # Agent Context
    "AgentContext",
    "TeammateContext",
    "get_agent_context",
    "get_agent_id",
    "run_in_agent_context",
    "create_agent_context",
    # Teammate Context
    "get_teammate_context",
    "run_in_teammate_context",
    "create_teammate_context",
    # Permission Context
    "get_permission_context",
    "run_in_permission_context",
    "request_permission_from_parent",
    # Utility
    "is_in_agent_context",
    "is_in_teammate_context",
    "get_context_summary",
]