"""
MCP Server 配置

定义 MCP Server 的配置选项。
"""

from typing import Any
from pydantic import BaseModel, Field


class MCPServerConfig(BaseModel):
    """MCP Server 配置"""
    server_name: str = Field(default="harnessgenj", description="服务器名称")
    version: str = Field(default="1.2.8", description="服务器版本")
    capabilities: dict[str, bool] = Field(
        default_factory=lambda: {"tools": True, "resources": False, "prompts": False},
        description="服务器能力",
    )
    max_concurrent_requests: int = Field(default=10, description="最大并发请求数")
    timeout_seconds: float = Field(default=30.0, description="请求超时时间")


class MCPToolConfig(BaseModel):
    """MCP 工具配置"""
    enabled: bool = Field(default=True, description="是否启用")
    timeout_seconds: float = Field(default=10.0, description="工具执行超时")
    max_retries: int = Field(default=3, description="最大重试次数")