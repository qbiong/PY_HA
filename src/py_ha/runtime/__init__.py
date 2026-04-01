"""
Runtime Layer - Execution Engine & Context Management

类比 JVM 的:
- Execution Engine (执行引擎)
- Runtime Data Area (运行时数据区)
- Garbage Collector (上下文优化)
"""

from py_ha.runtime.orchestrator import TaskOrchestrator, ExecutionStrategy
from py_ha.runtime.context import ContextManager, AgentContext
from py_ha.runtime.harness import Harness

__all__ = [
    "TaskOrchestrator",
    "ExecutionStrategy",
    "ContextManager",
    "AgentContext",
    "Harness",
]