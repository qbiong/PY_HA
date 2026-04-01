"""
Core Layer - Agent Specification & Loader

类比 JVM 的:
- Bytecode Specification (Agent规范)
- Class Loader (Agent加载器)
"""

from py_ha.core.spec import AgentSpec, ToolSpec, CapabilitySpec
from py_ha.core.loader import AgentLoader, ModuleRegistry

__all__ = [
    "AgentSpec",
    "ToolSpec",
    "CapabilitySpec",
    "AgentLoader",
    "ModuleRegistry",
]