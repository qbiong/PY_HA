"""
Harness Layer - Built-in Capabilities

类比 JVM 的 JDK 内置工具:
- 预定义能力，开箱即用
- 可插拔，可扩展
- 标准化接口
"""

from py_ha.harness.planning import PlanningTool, TodoList
from py_ha.harness.subagent import SubagentManager, SubagentTask, SubagentConfig
from py_ha.harness.filesystem import VirtualFS, StorageBackend, LocalStorage
from py_ha.harness.sandbox import CodeSandbox
from py_ha.harness.human_loop import HumanLoop, ApprovalRequest

__all__ = [
    "PlanningTool",
    "TodoList",
    "SubagentManager",
    "SubagentTask",
    "SubagentConfig",
    "VirtualFS",
    "StorageBackend",
    "LocalStorage",
    "CodeSandbox",
    "HumanLoop",
    "ApprovalRequest",
]