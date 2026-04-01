"""
Harness - 主入口，整合所有层

Harness 是用户的主要交互入口:
- 加载 Agent
- 配置执行环境
- 运行任务
- 管理生命周期
"""

from typing import Any

from py_ha.core import AgentSpec, AgentLoader, ModuleRegistry
from py_ha.runtime.orchestrator import TaskOrchestrator, ExecutionStrategy, ExecutionResult
from py_ha.runtime.context import ContextManager, AgentContext


class Harness:
    """
    AI Agent Harness - 主框架入口

    整合所有层的能力，提供统一的使用接口:
    1. Core层: Agent加载和注册
    2. Runtime层: 执行引擎和上下文管理
    3. Harness层: 内置能力和工具
    """

    def __init__(
        self,
        strategy: ExecutionStrategy = ExecutionStrategy.SEQUENTIAL,
        eviction_threshold: int = 3000,
    ) -> None:
        # Core层组件
        self.registry = ModuleRegistry()
        self.loader = AgentLoader(self.registry)

        # Runtime层组件
        self.context_manager = ContextManager(eviction_threshold=eviction_threshold)
        self.orchestrator = TaskOrchestrator(strategy=strategy)

        # 运行状态
        self._running: bool = False

    def load_agent(self, spec: AgentSpec) -> AgentSpec:
        """加载Agent"""
        return self.loader.load_from_spec(spec)

    def load_agent_from_file(self, path: str) -> AgentSpec:
        """从文件加载Agent"""
        return self.loader.load_from_file(path)

    async def run(
        self,
        spec: AgentSpec | str,
        task: str,
        context_id: str | None = None,
    ) -> ExecutionResult:
        """
        运行Agent任务

        Args:
            spec: Agent规范或已注册的Agent名称
            task: 任务描述
            context_id: 上下文ID (可选，用于恢复)

        Returns:
            ExecutionResult: 执行结果
        """
        # 获取Agent规范
        if isinstance(spec, str):
            loaded_spec = self.registry.get_agent(spec)
            if loaded_spec is None:
                return ExecutionResult(
                    success=False,
                    error=f"Agent '{spec}' not found",
                )
            spec = loaded_spec

        # 创建或获取上下文
        if context_id is None:
            import uuid
            context_id = str(uuid.uuid4())

        context = self.context_manager.get_context(context_id)
        if context is None:
            context = self.context_manager.create_context(
                context_id,
                max_tokens=spec.max_tokens,
            )

        # 添加任务消息
        context.add_message("user", task)

        # 执行任务
        self._running = True
        try:
            result = await self.orchestrator.execute(spec, task, context)
            if result.success:
                context.add_message("assistant", str(result.output))
            return result
        finally:
            self._running = False

    def list_agents(self) -> list[str]:
        """列出所有已注册的Agent"""
        return self.registry.list_agents()

    def list_tools(self) -> list[str]:
        """列出所有已注册的工具"""
        return self.registry.list_tools()

    def save_context(self, context_id: str) -> Any:
        """保存上下文状态"""
        return self.context_manager.save_snapshot(context_id)

    def restore_context(self, snapshot: Any) -> str:
        """恢复上下文状态"""
        ctx = self.context_manager.restore_snapshot(snapshot)
        return ctx.context_id