"""
Tests for Core Layer
"""

import pytest

from py_ha.core import AgentSpec, ToolSpec, CapabilitySpec, AgentLoader, ModuleRegistry


class TestAgentSpec:
    """测试 AgentSpec 规范"""

    def test_create_basic_spec(self) -> None:
        """创建基本Agent规范"""
        spec = AgentSpec(
            name="test-agent",
            description="A test agent",
        )
        assert spec.name == "test-agent"
        assert spec.description == "A test agent"
        assert spec.version == "1.0.0"
        assert spec.tools == []
        assert spec.capabilities == []

    def test_create_spec_with_tools(self) -> None:
        """创建带工具的Agent规范"""
        tool = ToolSpec(
            name="web_search",
            description="Search the web",
            parameters={"query": {"type": "string"}},
        )
        spec = AgentSpec(
            name="research-agent",
            tools=[tool],
        )
        assert len(spec.tools) == 1
        assert spec.tools[0].name == "web_search"

    def test_create_spec_with_capabilities(self) -> None:
        """创建带能力的Agent规范"""
        cap = CapabilitySpec(
            name="planning",
            enabled=True,
            config={"max_steps": 10},
        )
        spec = AgentSpec(
            name="planning-agent",
            capabilities=[cap],
        )
        assert len(spec.capabilities) == 1
        assert spec.capabilities[0].name == "planning"


class TestAgentLoader:
    """测试 AgentLoader 加载器"""

    def test_load_from_spec(self) -> None:
        """从规范加载Agent"""
        registry = ModuleRegistry()
        loader = AgentLoader(registry)

        spec = AgentSpec(name="loaded-agent")
        loaded = loader.load_from_spec(spec)

        assert loaded.name == "loaded-agent"
        assert registry.get_agent("loaded-agent") is not None

    def test_register_duplicate_agent(self) -> None:
        """重复注册Agent"""
        registry = ModuleRegistry()
        loader = AgentLoader(registry)

        spec = AgentSpec(name="duplicate-agent")
        loader.load_from_spec(spec)

        # 再次注册应该失败
        with pytest.raises(ValueError, match="already registered"):
            loader.load_from_spec(spec)

    def test_list_agents(self) -> None:
        """列出已注册的Agent"""
        registry = ModuleRegistry()
        loader = AgentLoader(registry)

        for name in ["agent-1", "agent-2", "agent-3"]:
            loader.load_from_spec(AgentSpec(name=name))

        agents = registry.list_agents()
        assert len(agents) == 3
        assert "agent-1" in agents


class TestModuleRegistry:
    """测试模块注册表"""

    def test_register_tool(self) -> None:
        """注册工具"""
        registry = ModuleRegistry()
        registry.register_tool("test_tool", lambda: "result")

        tool = registry.get_tool("test_tool")
        assert tool is not None
        assert tool() == "result"

    def test_list_tools(self) -> None:
        """列出工具"""
        registry = ModuleRegistry()
        registry.register_tool("tool-1", None)
        registry.register_tool("tool-2", None)

        tools = registry.list_tools()
        assert len(tools) == 2