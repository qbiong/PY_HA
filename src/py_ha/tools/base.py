"""
Base Tool - 工具基础抽象

定义所有工具的标准接口
"""

from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    """工具执行结果"""

    success: bool = Field(..., description="是否成功")
    output: Any = Field(default=None, description="输出结果")
    error: str | None = Field(default=None, description="错误信息")
    metadata: dict[str, Any] = Field(default_factory=dict, description="元数据")


class BaseTool(ABC):
    """
    工具基类 - 所有工具的抽象接口

    工具需要实现:
    1. name: 工具名称
    2. description: 工具描述
    3. parameters: 参数规范
    4. execute: 执行逻辑
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        """参数规范 (JSON Schema 格式)"""
        pass

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """
        执行工具

        Args:
            kwargs: 工具参数

        Returns:
            ToolResult: 执行结果
        """
        pass

    def to_spec(self) -> dict[str, Any]:
        """转换为工具规范"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class ToolRegistry:
    """
    工具注册表 - 管理所有可用工具

    功能:
    1. 工具注册
    2. 工具发现
    3. 工具调用
    """

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """注册工具"""
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        """获取工具"""
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        """列出所有工具"""
        return list(self._tools.keys())

    def get_specs(self) -> list[dict[str, Any]]:
        """获取所有工具规范"""
        return [tool.to_spec() for tool in self._tools.values()]

    async def call(self, name: str, **kwargs: Any) -> ToolResult:
        """
        调用工具

        Args:
            name: 工具名称
            kwargs: 工具参数

        Returns:
            ToolResult: 执行结果
        """
        tool = self.get(name)
        if tool is None:
            return ToolResult(
                success=False,
                error=f"Tool not found: {name}",
            )
        return await tool.execute(**kwargs)