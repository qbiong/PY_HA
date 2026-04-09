"""
MCP 工具基类和注册表

提供 MCP 工具的抽象基类和注册机制。
"""

from abc import ABC, abstractmethod
from typing import Any, ClassVar
from pydantic import BaseModel, Field

from harnessgenj.mcp.protocol import MCPToolResult, MCPToolInfo


class MCPTool(ABC, BaseModel):
    """
    MCP 工具基类

    所有 MCP 工具都应继承此类并实现 execute 方法。

    使用示例:
        class MemoryStoreTool(MCPTool):
            name = "memory_store"
            description = "存储内容到记忆系统"
            input_schema = {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "存储键"},
                    "content": {"type": "string", "description": "存储内容"},
                },
                "required": ["key", "content"],
            }

            def execute(self, params: dict, harness) -> MCPToolResult:
                key = params["key"]
                content = params["content"]
                harness.memory.store_knowledge(key, content)
                return MCPToolResult.text_result(f"已存储: {key}")
    """

    name: ClassVar[str] = Field(description="工具名称")
    description: ClassVar[str] = Field(description="工具描述")
    input_schema: ClassVar[dict[str, Any]] = Field(
        default_factory=dict,
        description="输入参数 JSON Schema",
    )
    category: ClassVar[str] = Field(default="general", description="工具类别")

    class Config:
        arbitrary_types_allowed = True

    @abstractmethod
    def execute(self, params: dict[str, Any], harness: Any) -> MCPToolResult:
        """
        执行工具逻辑

        Args:
            params: 工具参数
            harness: Harness 实例

        Returns:
            MCPToolResult: 执行结果
        """
        pass

    def get_info(self) -> MCPToolInfo:
        """获取工具信息"""
        return MCPToolInfo(
            name=self.name,
            description=self.description,
            inputSchema=self.input_schema,
        )

    def validate_params(self, params: dict[str, Any]) -> list[str]:
        """
        验证参数

        Args:
            params: 工具参数

        Returns:
            错误消息列表，空列表表示验证通过
        """
        errors = []
        if not self.input_schema:
            return errors

        properties = self.input_schema.get("properties", {})
        required = self.input_schema.get("required", [])

        # 检查必需参数
        for req in required:
            if req not in params:
                errors.append(f"缺少必需参数: {req}")

        # 检查参数类型
        for key, value in params.items():
            if key in properties:
                prop = properties[key]
                expected_type = prop.get("type")
                if expected_type and not self._check_type(value, expected_type):
                    errors.append(f"参数 {key} 类型错误，期望: {expected_type}")

        return errors

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """检查值类型"""
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
        }
        expected = type_map.get(expected_type)
        if expected is None:
            return True
        return isinstance(value, expected)


class ToolRegistry:
    """
    工具注册表

    管理所有注册的 MCP 工具。
    """

    def __init__(self) -> None:
        self._tools: dict[str, MCPTool] = {}

    def register(self, tool: MCPTool) -> None:
        """注册工具"""
        self._tools[tool.name] = tool

    def get(self, name: str) -> MCPTool | None:
        """获取工具"""
        return self._tools.get(name)

    def list_tools(self) -> list[MCPTool]:
        """列出所有工具"""
        return list(self._tools.values())

    def list_tool_infos(self) -> list[MCPToolInfo]:
        """列出所有工具信息"""
        return [tool.get_info() for tool in self._tools.values()]

    def has_tool(self, name: str) -> bool:
        """检查工具是否存在"""
        return name in self._tools


# 全局工具注册表
_global_registry = ToolRegistry()


def register_tool(tool: MCPTool) -> None:
    """注册工具到全局注册表"""
    _global_registry.register(tool)


def get_tool(name: str) -> MCPTool | None:
    """从全局注册表获取工具"""
    return _global_registry.get(name)


def list_tools() -> list[MCPTool]:
    """列出全局注册表中的所有工具"""
    return _global_registry.list_tools()


def get_registry() -> ToolRegistry:
    """获取全局工具注册表"""
    return _global_registry