"""
HarnessGenJ MCP 模块

提供 MCP (Model Context Protocol) Server 实现，允许 Claude Code 等客户端
通过标准协议与 HarnessGenJ 框架交互。

主要组件:
- MCPServer: MCP 服务器实现
- MCPTool: 工具基类
- 协议层: JSON-RPC 请求/响应处理

使用示例:
    # 作为模块启动
    from harnessgenj.mcp import MCPServer
    server = MCPServer()
    server.start()

    # 命令行启动
    python -m harnessgenj.mcp.server
"""

from harnessgenj.mcp.config import MCPServerConfig, MCPToolConfig
from harnessgenj.mcp.protocol import (
    MCPRequest,
    MCPResponse,
    MCPError,
    MCPErrorCode,
    MCPToolInfo,
    MCPToolResult,
    parse_request,
    validate_request,
)
from harnessgenj.mcp.server import MCPServer, create_mcp_server
from harnessgenj.mcp.tools import (
    MCPTool,
    ToolRegistry,
    register_tool,
    get_tool,
    list_tools,
    get_registry,
)

__all__ = [
    # 配置
    "MCPServerConfig",
    "MCPToolConfig",
    # 协议
    "MCPRequest",
    "MCPResponse",
    "MCPError",
    "MCPErrorCode",
    "MCPToolInfo",
    "MCPToolResult",
    "parse_request",
    "validate_request",
    # 服务器
    "MCPServer",
    "create_mcp_server",
    # 工具
    "MCPTool",
    "ToolRegistry",
    "register_tool",
    "get_tool",
    "list_tools",
    "get_registry",
]