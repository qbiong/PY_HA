"""
Agent Loader - 动态加载Agent定义和工具模块

类比 JVM Class Loader:
- 动态加载Agent定义
- 验证Agent规范
- 注册和管理模块
"""

from pathlib import Path
from typing import Any

from py_ha.core.spec import AgentSpec, AgentManifest


class ModuleRegistry:
    """
    模块注册表 - 管理所有已加载的Agent和工具

    类似 JVM 的方法区，存储所有已加载的类型定义
    """

    def __init__(self) -> None:
        self._agents: dict[str, AgentSpec] = {}
        self._tools: dict[str, Any] = {}
        self._manifests: dict[str, AgentManifest] = {}

    def register_agent(self, spec: AgentSpec) -> None:
        """注册Agent规范"""
        if spec.name in self._agents:
            raise ValueError(f"Agent '{spec.name}' already registered")
        self._agents[spec.name] = spec

    def get_agent(self, name: str) -> AgentSpec | None:
        """获取Agent规范"""
        return self._agents.get(name)

    def register_tool(self, name: str, tool: Any) -> None:
        """注册工具"""
        self._tools[name] = tool

    def get_tool(self, name: str) -> Any | None:
        """获取工具"""
        return self._tools.get(name)

    def list_agents(self) -> list[str]:
        """列出所有已注册的Agent"""
        return list(self._agents.keys())

    def list_tools(self) -> list[str]:
        """列出所有已注册的工具"""
        return list(self._tools.keys())


class AgentLoader:
    """
    Agent加载器 - 动态加载和验证Agent定义

    类似 JVM Class Loader 的职责:
    1. Loading: 从各种来源加载Agent定义
    2. Linking: 验证、准备Agent规范
    3. Initialization: 初始化Agent实例
    """

    def __init__(self, registry: ModuleRegistry | None = None) -> None:
        self.registry = registry or ModuleRegistry()

    def load_from_spec(self, spec: AgentSpec) -> AgentSpec:
        """
        从AgentSpec对象加载

        执行验证和注册流程
        """
        self._validate_spec(spec)
        self.registry.register_agent(spec)
        return spec

    def load_from_file(self, path: Path | str) -> AgentSpec:
        """
        从文件加载Agent定义

        支持 JSON/YAML 格式
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Agent file not found: {path}")

        # 根据文件扩展名选择解析方式
        content = path.read_text(encoding="utf-8")
        if path.suffix == ".json":
            import json
            data = json.loads(content)
        elif path.suffix in (".yaml", ".yml"):
            import yaml
            data = yaml.safe_load(content)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")

        spec = AgentSpec(**data)
        return self.load_from_spec(spec)

    def load_manifest(self, path: Path | str) -> AgentManifest:
        """
        加载Agent清单 - 多Agent协作配置
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Manifest file not found: {path}")

        content = path.read_text(encoding="utf-8")
        if path.suffix == ".json":
            import json
            data = json.loads(content)
        elif path.suffix in (".yaml", ".yml"):
            import yaml
            data = yaml.safe_load(content)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")

        manifest = AgentManifest(**data)
        # 注册所有Agent
        for spec in manifest.agents:
            self.load_from_spec(spec)
        self.registry._manifests[path.stem] = manifest
        return manifest

    def _validate_spec(self, spec: AgentSpec) -> None:
        """
        验证Agent规范

        类似 JVM 的验证阶段，确保规范正确性
        """
        # 检查必要字段
        if not spec.name:
            raise ValueError("Agent name is required")

        # 检查工具名称唯一性
        tool_names = [t.name for t in spec.tools]
        if len(tool_names) != len(set(tool_names)):
            raise ValueError("Duplicate tool names in Agent spec")

        # 检查能力名称唯一性
        cap_names = [c.name for c in spec.capabilities]
        if len(cap_names) != len(set(cap_names)):
            raise ValueError("Duplicate capability names in Agent spec")