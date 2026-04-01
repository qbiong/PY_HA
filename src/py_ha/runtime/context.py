"""
Context Manager - Agent执行上下文管理

类比 JVM Runtime Data Area:
- 方法区: 存储Agent定义和工具信息
- 堆: 存储对话历史和大数据
- 栈: 存储当前执行状态
- 程序计数器: 追踪执行进度
"""

from typing import Any
from pydantic import BaseModel, Field


class Message(BaseModel):
    """消息结构"""

    role: str = Field(..., description="消息角色: system/user/assistant/tool")
    content: str = Field(..., description="消息内容")
    timestamp: float = Field(default=0.0, description="时间戳")


class ContextSnapshot(BaseModel):
    """上下文快照 - 用于持久化和恢复"""

    context_id: str = Field(..., description="上下文ID")
    messages: list[Message] = Field(default_factory=list, description="消息历史")
    state: dict[str, Any] = Field(default_factory=dict, description="状态数据")
    created_at: float = Field(..., description="创建时间")
    updated_at: float = Field(..., description="更新时间")


class AgentContext:
    """
    Agent执行上下文 - 管理单个Agent的执行状态

    类似 JVM 的栈帧，每个Agent执行都有独立的上下文:
    1. 消息历史管理
    2. 状态追踪
    3. Token计数
    """

    def __init__(self, context_id: str, max_tokens: int = 4096) -> None:
        self.context_id = context_id
        self.max_tokens = max_tokens
        self._messages: list[Message] = []
        self._state: dict[str, Any] = {}
        self._token_count: int = 0

    def add_message(self, role: str, content: str) -> Message:
        """添加消息"""
        import time
        msg = Message(role=role, content=content, timestamp=time.time())
        self._messages.append(msg)
        # 更新token计数 (简化估算)
        self._token_count += len(content) // 4
        return msg

    def get_messages(self) -> list[Message]:
        """获取所有消息"""
        return self._messages.copy()

    def set_state(self, key: str, value: Any) -> None:
        """设置状态"""
        self._state[key] = value

    def get_state(self, key: str, default: Any = None) -> Any:
        """获取状态"""
        return self._state.get(key, default)

    def get_token_count(self) -> int:
        """获取当前token计数"""
        return self._token_count

    def snapshot(self) -> ContextSnapshot:
        """创建上下文快照"""
        import time
        now = time.time()
        return ContextSnapshot(
            context_id=self.context_id,
            messages=self._messages.copy(),
            state=self._state.copy(),
            created_at=now,
            updated_at=now,
        )

    def restore(self, snapshot: ContextSnapshot) -> None:
        """从快照恢复上下文"""
        self.context_id = snapshot.context_id
        self._messages = snapshot.messages.copy()
        self._state = snapshot.state.copy()


class ContextManager:
    """
    上下文管理器 - 管理所有Agent的执行上下文

    类似 JVM Runtime Data Area 的管理者:
    1. 创建和销毁上下文
    2. 上下文隔离
    3. Token优化 (类似GC)
    4. 持久化和恢复
    """

    def __init__(self, eviction_threshold: int = 3000) -> None:
        self._contexts: dict[str, AgentContext] = {}
        self.eviction_threshold = eviction_threshold

    def create_context(self, context_id: str, max_tokens: int = 4096) -> AgentContext:
        """创建新的执行上下文"""
        ctx = AgentContext(context_id=context_id, max_tokens=max_tokens)
        self._contexts[context_id] = ctx
        return ctx

    def get_context(self, context_id: str) -> AgentContext | None:
        """获取上下文"""
        return self._contexts.get(context_id)

    def destroy_context(self, context_id: str) -> None:
        """销毁上下文"""
        self._contexts.pop(context_id, None)

    def evict_old_messages(self, context_id: str, keep_recent: int = 5) -> int:
        """
        消息驱逐 - 类似 JVM GC

        清理旧消息以释放token空间
        """
        ctx = self.get_context(context_id)
        if ctx is None:
            return 0

        messages = ctx._messages
        if len(messages) <= keep_recent:
            return 0

        # 保留最近的消息
        evicted_count = len(messages) - keep_recent
        ctx._messages = messages[-keep_recent:]

        # 重新计算token
        ctx._token_count = sum(len(m.content) // 4 for m in ctx._messages)

        return evicted_count

    def summarize_history(self, context_id: str) -> str:
        """
        历史摘要 - 将长历史压缩为摘要

        类似 JVM 的内存压缩
        """
        ctx = self.get_context(context_id)
        if ctx is None:
            return ""

        # TODO: 实现实际的摘要逻辑 (可调用LLM)
        messages = ctx._messages
        summary = f"Summary of {len(messages)} messages"
        return summary

    def save_snapshot(self, context_id: str) -> ContextSnapshot | None:
        """保存上下文快照"""
        ctx = self.get_context(context_id)
        if ctx is None:
            return None
        return ctx.snapshot()

    def restore_snapshot(self, snapshot: ContextSnapshot) -> AgentContext:
        """从快照恢复上下文"""
        ctx = self.create_context(snapshot.context_id)
        ctx.restore(snapshot)
        return ctx