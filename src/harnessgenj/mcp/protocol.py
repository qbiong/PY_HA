"""
MCP 协议实现

实现 JSON-RPC 2.0 协议，用于 MCP Server 与客户端通信。

协议规范：
- 请求格式：{"jsonrpc": "2.0", "method": "...", "params": {...}, "id": 1}
- 响应格式：{"jsonrpc": "2.0", "result": {...}, "id": 1}
- 错误格式：{"jsonrpc": "2.0", "error": {...}, "id": 1}
"""

from typing import Any
from pydantic import BaseModel, Field
from enum import Enum


class MCPErrorCode(int, Enum):
    """MCP 错误码"""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    SERVER_ERROR = -32000


class MCPError(BaseModel):
    """MCP 错误信息"""
    code: int = Field(description="错误码")
    message: str = Field(description="错误消息")
    data: dict[str, Any] | None = Field(default=None, description="额外错误数据")


class MCPRequest(BaseModel):
    """MCP 请求"""
    jsonrpc: str = Field(default="2.0", description="JSON-RPC 版本")
    method: str = Field(description="方法名")
    params: dict[str, Any] = Field(default_factory=dict, description="参数")
    id: str | int | None = Field(default=None, description="请求ID")

    def is_notification(self) -> bool:
        """是否为通知（无需响应）"""
        return self.id is None


class MCPResponse(BaseModel):
    """MCP 响应"""
    jsonrpc: str = Field(default="2.0", description="JSON-RPC 版本")
    result: dict[str, Any] | None = Field(default=None, description="结果")
    error: MCPError | None = Field(default=None, description="错误")
    id: str | int | None = Field(default=None, description="请求ID")

    @classmethod
    def success(cls, result: dict[str, Any], request_id: str | int | None) -> "MCPResponse":
        """创建成功响应"""
        return cls(result=result, id=request_id)

    @classmethod
    def error_response(
        cls,
        code: int,
        message: str,
        request_id: str | int | None,
        data: dict[str, Any] | None = None,
    ) -> "MCPResponse":
        """创建错误响应"""
        return cls(
            error=MCPError(code=code, message=message, data=data),
            id=request_id,
        )


class MCPToolInfo(BaseModel):
    """MCP 工具信息"""
    name: str = Field(description="工具名称")
    description: str = Field(description="工具描述")
    inputSchema: dict[str, Any] = Field(description="输入参数 Schema")


class MCPToolResult(BaseModel):
    """MCP 工具执行结果"""
    content: list[dict[str, Any]] = Field(description="结果内容")
    isError: bool = Field(default=False, description="是否为错误")

    @classmethod
    def text_result(cls, text: str, is_error: bool = False) -> "MCPToolResult":
        """创建文本结果"""
        return cls(
            content=[{"type": "text", "text": text}],
            isError=is_error,
        )

    @classmethod
    def error_result(cls, message: str) -> "MCPToolResult":
        """创建错误结果"""
        return cls.text_result(message, is_error=True)


def parse_request(data: dict[str, Any]) -> MCPRequest | MCPError:
    """
    解析 MCP 请求

    Args:
        data: 原始请求数据

    Returns:
        MCPRequest 实例或 MCPError（解析失败时）
    """
    try:
        return MCPRequest(**data)
    except Exception as e:
        return MCPError(
            code=MCPErrorCode.INVALID_REQUEST,
            message=f"Invalid request: {e}",
        )


def validate_request(request: MCPRequest) -> MCPError | None:
    """
    验证 MCP 请求

    Args:
        request: MCP 请求

    Returns:
        验证失败时返回 MCPError，成功返回 None
    """
    if request.jsonrpc != "2.0":
        return MCPError(
            code=MCPErrorCode.INVALID_REQUEST,
            message="Invalid JSON-RPC version",
        )

    if not request.method:
        return MCPError(
            code=MCPErrorCode.INVALID_REQUEST,
            message="Method is required",
        )

    return None