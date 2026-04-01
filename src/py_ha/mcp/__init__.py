"""
MCP Server Module - Model Context Protocol Integration

将 py_ha 框架核心能力暴露为 MCP Tools，供 Claude Code、OpenClaude 等平台使用。

使用方式:
1. 作为独立 MCP Server 运行
2. 通过配置文件加载到 Claude Code 等平台
"""

from py_ha.mcp.server import PyHAMCPServer, create_mcp_server

__all__ = ["PyHAMCPServer", "create_mcp_server"]