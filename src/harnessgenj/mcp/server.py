"""
MCP Server 核心实现

提供 MCP Server 的主要功能，包括：
- 工具注册和管理
- 请求处理
- JSON-RPC 协议支持
- stdio 通信
"""

import sys
import json
import asyncio
from typing import Any
from pathlib import Path

from pydantic import BaseModel

from harnessgenj.mcp.config import MCPServerConfig
from harnessgenj.mcp.protocol import (
    MCPRequest,
    MCPResponse,
    MCPError,
    MCPErrorCode,
    MCPToolInfo,
    parse_request,
    validate_request,
)
from harnessgenj.mcp.tools import (
    ToolRegistry,
    MCPTool,
    get_registry,
)
from harnessgenj.mcp.tools.memory_tools import MEMORY_TOOLS
from harnessgenj.mcp.tools.task_tools import TASK_TOOLS
from harnessgenj.mcp.tools.system_tools import SYSTEM_TOOLS
from harnessgenj.mcp.tools.storage_tools import STORAGE_TOOLS


class MCPServer:
    """
    MCP Server 实现

    实现 MCP (Model Context Protocol) 服务器，允许 Claude Code 等客户端
    通过标准输入输出与 HarnessGenJ 框架交互。

    使用示例:
        # 作为模块使用
        from harnessgenj import Harness
        from harnessgenj.mcp import MCPServer

        harness = Harness.from_project(".")
        server = MCPServer(harness=harness)
        server.start()

        # 通过命令行启动
        python -m harnessgenj.mcp.server
    """

    def __init__(
        self,
        config: MCPServerConfig | None = None,
        harness: Any = None,
    ) -> None:
        """
        初始化 MCP Server

        Args:
            config: 服务器配置
            harness: Harness 实例（如果为 None，会尝试获取最后创建的实例）
        """
        self.config = config or MCPServerConfig()
        self._harness = harness
        self._registry = get_registry()
        self._running = False

        # 注册所有内置工具
        self._register_builtin_tools()

    def _register_builtin_tools(self) -> None:
        """注册内置工具"""
        # 内存工具
        for tool in MEMORY_TOOLS:
            self._registry.register(tool)

        # 任务工具
        for tool in TASK_TOOLS:
            self._registry.register(tool)

        # 系统工具
        for tool in SYSTEM_TOOLS:
            self._registry.register(tool)

        # 存储工具
        for tool in STORAGE_TOOLS:
            self._registry.register(tool)

    def _get_harness(self) -> Any:
        """获取 Harness 实例"""
        if self._harness is not None:
            return self._harness

        # 尝试获取最后创建的实例
        from harnessgenj import Harness
        instance = Harness.get_last_instance()
        if instance is not None:
            return instance

        # 创建新实例
        return Harness("MCP-Server-Project")

    def register_tool(self, tool: MCPTool) -> None:
        """
        注册自定义工具

        Args:
            tool: MCP 工具实例
        """
        self._registry.register(tool)

    def list_tools(self) -> list[MCPToolInfo]:
        """列出所有可用工具"""
        return self._registry.list_tool_infos()

    def handle_request(self, request_data: dict[str, Any]) -> MCPResponse:
        """
        处理 MCP 请求

        Args:
            request_data: 原始请求数据

        Returns:
            MCP 响应
        """
        # 解析请求
        parsed = parse_request(request_data)
        if isinstance(parsed, MCPError):
            return MCPResponse.error_response(
                parsed.code,
                parsed.message,
                None,
            )

        request = parsed

        # 验证请求
        error = validate_request(request)
        if error:
            return MCPResponse.error_response(
                error.code,
                error.message,
                request.id,
            )

        # 处理不同方法
        method = request.method

        if method == "initialize":
            return self._handle_initialize(request)
        elif method == "tools/list":
            return self._handle_tools_list(request)
        elif method == "tools/call":
            return self._handle_tools_call(request)
        else:
            return MCPResponse.error_response(
                MCPErrorCode.METHOD_NOT_FOUND,
                f"未知方法: {method}",
                request.id,
            )

    def _handle_initialize(self, request: MCPRequest) -> MCPResponse:
        """处理初始化请求"""
        return MCPResponse.success(
            {
                "protocolVersion": "2024-11-05",
                "capabilities": self.config.capabilities,
                "serverInfo": {
                    "name": self.config.server_name,
                    "version": self.config.version,
                },
            },
            request.id,
        )

    def _handle_tools_list(self, request: MCPRequest) -> MCPResponse:
        """处理工具列表请求"""
        tools = self.list_tools()
        return MCPResponse.success(
            {"tools": [t.model_dump() for t in tools]},
            request.id,
        )

    def _handle_tools_call(self, request: MCPRequest) -> MCPResponse:
        """处理工具调用请求"""
        params = request.params
        tool_name = params.get("name")
        tool_params = params.get("arguments", {})

        if not tool_name:
            return MCPResponse.error_response(
                MCPErrorCode.INVALID_PARAMS,
                "缺少工具名称",
                request.id,
            )

        # 获取工具
        tool = self._registry.get(tool_name)
        if tool is None:
            return MCPResponse.error_response(
                MCPErrorCode.METHOD_NOT_FOUND,
                f"工具不存在: {tool_name}",
                request.id,
            )

        # 验证参数
        errors = tool.validate_params(tool_params)
        if errors:
            return MCPResponse.error_response(
                MCPErrorCode.INVALID_PARAMS,
                "; ".join(errors),
                request.id,
            )

        # 执行工具
        try:
            harness = self._get_harness()
            result = tool.execute(tool_params, harness)

            return MCPResponse.success(
                {"content": result.content, "isError": result.isError},
                request.id,
            )
        except Exception as e:
            return MCPResponse.error_response(
                MCPErrorCode.INTERNAL_ERROR,
                f"工具执行错误: {e}",
                request.id,
            )

    def start(self) -> None:
        """
        启动 MCP Server（stdio 模式）

        通过标准输入输出与客户端通信。
        """
        self._running = True

        # 输出初始化信息到 stderr（不影响 stdout 的 JSON-RPC 通信）
        print(f"[MCP] {self.config.server_name} v{self.config.version} 已启动", file=sys.stderr)
        print(f"[MCP] 已注册 {len(self._registry.list_tools())} 个工具", file=sys.stderr)

        # 主循环：读取 stdin，处理请求，写入 stdout
        for line in sys.stdin:
            if not self._running:
                break

            line = line.strip()
            if not line:
                continue

            try:
                request_data = json.loads(line)
                response = self.handle_request(request_data)
                print(json.dumps(response.model_dump(exclude_none=True)))
                sys.stdout.flush()
            except json.JSONDecodeError as e:
                error_response = MCPResponse.error_response(
                    MCPErrorCode.PARSE_ERROR,
                    f"JSON 解析错误: {e}",
                    None,
                )
                print(json.dumps(error_response.model_dump(exclude_none=True)))
                sys.stdout.flush()
            except Exception as e:
                error_response = MCPResponse.error_response(
                    MCPErrorCode.INTERNAL_ERROR,
                    f"内部错误: {e}",
                    None,
                )
                print(json.dumps(error_response.model_dump(exclude_none=True)))
                sys.stdout.flush()

    def stop(self) -> None:
        """停止 MCP Server"""
        self._running = False
        print("[MCP] Server 已停止", file=sys.stderr)


def create_mcp_server(
    harness: Any = None,
    config: MCPServerConfig | None = None,
) -> MCPServer:
    """
    创建 MCP Server 实例

    Args:
        harness: Harness 实例
        config: 服务器配置

    Returns:
        MCPServer 实例
    """
    return MCPServer(config=config, harness=harness)


# 命令行入口
if __name__ == "__main__":
    server = MCPServer()
    server.start()