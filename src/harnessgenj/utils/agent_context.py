"""
Agent Context - Python contextvars 实现 Agent 上下文隔离

参考 Claude Code 的 AsyncLocalStorage 设计，使用 Python contextvars 实现：
- Agent 上下文隔离（每个 Agent 有独立的上下文）
- Teammate 上下文隔离（持续运行的 Teammate）
- 权限上下文隔离（独立的权限决策）

使用示例：
    from harnessgenj.utils.agent_context import agent_context, run_in_agent_context

    # 在 Agent 上下文中运行
    run_in_agent_context({'agent_id': 'developer_1', 'session_id': 'xxx'}, lambda: execute_task())

    # 获取当前 Agent 上下文
    context = get_agent_context()
"""

from contextvars import ContextVar, Token
from typing import Any, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime
import time


@dataclass
class AgentContext:
    """Agent 运行时上下文"""

    agent_id: str
    session_id: str
    role_type: str = "agent"
    parent_session_id: Optional[str] = None
    is_subagent: bool = False
    created_at: float = field(default_factory=time.time)

    # 权限上下文
    permission_mode: str = "inherit"  # inherit | bubble | independent
    permitted_files: dict[str, Any] = field(default_factory=dict)

    # 工具池配置
    allowed_tools: list[str] = field(default_factory=list)
    disallowed_tools: list[str] = field(default_factory=list)

    # 任务信息
    current_task_id: Optional[str] = None
    task_description: Optional[str] = None

    # 统计信息
    tool_uses: int = 0
    messages_sent: int = 0


@dataclass
class TeammateContext:
    """Teammate 持续运行上下文"""

    identity: AgentContext
    team_name: str
    mailbox_path: str = ""
    is_running: bool = True
    shutdown_requested: bool = False
    shutdown_approved: bool = False

    # 消息队列
    pending_messages: list[dict[str, Any]] = field(default_factory=list)

    # 空闲状态
    is_idle: bool = False
    last_activity: float = field(default_factory=time.time)


# ==================== Context Variables ====================

# Agent 上下文（类似 AsyncLocalStorage<AgentContext>）
_agent_context: ContextVar[Optional[AgentContext]] = ContextVar('agent_context', default=None)

# Teammate 上下文（持续运行模式）
_teammate_context: ContextVar[Optional[TeammateContext]] = ContextVar('teammate_context', default=None)

# 权限上下文（独立决策）
_permission_context: ContextVar[Optional[dict[str, Any]]] = ContextVar('permission_context', default=None)


# ==================== Agent Context Functions ====================

def get_agent_context() -> Optional[AgentContext]:
    """
    获取当前 Agent 上下文

    Returns:
        当前 Agent 上下文，如果不在 Agent 上下文中则返回 None
    """
    return _agent_context.get()


def get_agent_id() -> str:
    """
    获取当前 Agent ID

    Returns:
        Agent ID，如果不在 Agent 上下文中则返回 "main"
    """
    ctx = get_agent_context()
    return ctx.agent_id if ctx else "main"


def run_in_agent_context(
    context: AgentContext,
    fn: Callable[[], Any],
) -> Any:
    """
    在 Agent 上下文中运行函数

    Args:
        context: Agent 上下文
        fn: 要执行的函数

    Returns:
        函数执行结果
    """
    token = _agent_context.set(context)
    try:
        return fn()
    finally:
        _agent_context.reset(token)


def create_agent_context(
    agent_id: str,
    session_id: str,
    role_type: str = "agent",
    parent_session_id: Optional[str] = None,
    permission_mode: str = "inherit",
    permitted_files: Optional[dict[str, Any]] = None,
) -> AgentContext:
    """
    创建 Agent 上下文

    Args:
        agent_id: Agent ID
        session_id: 会话 ID
        role_type: 角色类型
        parent_session_id: 父会话 ID（子代理）
        permission_mode: 权限模式
        permitted_files: 许可文件

    Returns:
        AgentContext 实例
    """
    return AgentContext(
        agent_id=agent_id,
        session_id=session_id,
        role_type=role_type,
        parent_session_id=parent_session_id,
        permission_mode=permission_mode,
        permitted_files=permitted_files or {},
        is_subagent=parent_session_id is not None,
    )


# ==================== Teammate Context Functions ====================

def get_teammate_context() -> Optional[TeammateContext]:
    """
    获取当前 Teammate 上下文

    Returns:
        当前 Teammate 上下文，如果不在 Teammate 上下文中则返回 None
    """
    return _teammate_context.get()


def run_in_teammate_context(
    context: TeammateContext,
    fn: Callable[[], Any],
) -> Any:
    """
    在 Teammate 上下文中运行函数

    Args:
        context: Teammate 上下文
        fn: 要执行的函数

    Returns:
        函数执行结果
    """
    token = _teammate_context.set(context)
    try:
        return fn()
    finally:
        _teammate_context.reset(token)


def create_teammate_context(
    agent_context: AgentContext,
    team_name: str,
    mailbox_path: str = "",
) -> TeammateContext:
    """
    创建 Teammate 上下文

    Args:
        agent_context: Agent 上下文
        team_name: 团队名称
        mailbox_path: 邮箱路径

    Returns:
        TeammateContext 实例
    """
    return TeammateContext(
        identity=agent_context,
        team_name=team_name,
        mailbox_path=mailbox_path,
    )


# ==================== Permission Context Functions ====================

def get_permission_context() -> Optional[dict[str, Any]]:
    """
    获取当前权限上下文

    Returns:
        权限上下文字典
    """
    return _permission_context.get()


def run_in_permission_context(
    context: dict[str, Any],
    fn: Callable[[], Any],
) -> Any:
    """
    在权限上下文中运行函数

    Args:
        context: 权限上下文
        fn: 要执行的函数

    Returns:
        函数执行结果
    """
    token = _permission_context.set(context)
    try:
        return fn()
    finally:
        _permission_context.reset(token)


# ==================== Bubble Permission Mode ====================

def request_permission_from_parent(
    request: dict[str, Any],
) -> dict[str, Any]:
    """
    气泡权限模式 - 向父请求权限

    Args:
        request: 权限请求

    Returns:
        权限决策结果
    """
    ctx = get_agent_context()

    if not ctx or not ctx.parent_session_id:
        # 没有父会话，独立决策
        return {"approved": True, "reason": "No parent session"}

    if ctx.permission_mode == "bubble":
        # 气泡模式：权限请求上浮到父
        # 实际实现需要通过消息系统传递给父 Agent
        # 这里返回模拟结果
        return {
            "approved": True,
            "reason": "Bubbled to parent",
            "parent_session_id": ctx.parent_session_id,
        }

    return {"approved": True, "reason": "Direct approval"}


# ==================== Utility Functions ====================

def is_in_agent_context() -> bool:
    """检查是否在 Agent 上下文中"""
    return get_agent_context() is not None


def is_in_teammate_context() -> bool:
    """检查是否在 Teammate 上下文中"""
    return get_teammate_context() is not None


def get_context_summary() -> dict[str, Any]:
    """
    获取当前上下文摘要

    Returns:
        上下文摘要信息
    """
    agent_ctx = get_agent_context()
    teammate_ctx = get_teammate_context()

    return {
        "in_agent_context": agent_ctx is not None,
        "in_teammate_context": teammate_ctx is not None,
        "agent_id": agent_ctx.agent_id if agent_ctx else "main",
        "role_type": agent_ctx.role_type if agent_ctx else "main",
        "is_subagent": agent_ctx.is_subagent if agent_ctx else False,
        "team_name": teammate_ctx.team_name if teammate_ctx else None,
        "is_idle": teammate_ctx.is_idle if teammate_ctx else False,
    }


# ==================== Export ====================

__all__ = [
    # Classes
    "AgentContext",
    "TeammateContext",
    # Agent Context Functions
    "get_agent_context",
    "get_agent_id",
    "run_in_agent_context",
    "create_agent_context",
    # Teammate Context Functions
    "get_teammate_context",
    "run_in_teammate_context",
    "create_teammate_context",
    # Permission Context Functions
    "get_permission_context",
    "run_in_permission_context",
    "request_permission_from_parent",
    # Utility Functions
    "is_in_agent_context",
    "is_in_teammate_context",
    "get_context_summary",
]