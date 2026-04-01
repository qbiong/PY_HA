"""
Code Execute Tool - 代码执行工具

提供代码执行能力
"""

from typing import Any

from py_ha.tools.base import BaseTool, ToolResult
from py_ha.harness.sandbox import CodeSandbox, ExecutionEnvironment


class CodeExecuteTool(BaseTool):
    """
    代码执行工具

    功能:
    1. 执行Python代码
    2. 安全隔离
    """

    def __init__(self, sandbox: CodeSandbox | None = None) -> None:
        self.sandbox = sandbox or CodeSandbox()

    @property
    def name(self) -> str:
        return "code_execute"

    @property
    def description(self) -> str:
        return "Execute Python code in a sandbox"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Execution timeout in seconds",
                    "default": 30,
                },
            },
            "required": ["code"],
        }

    async def execute(self, code: str, timeout: int = 30, **kwargs: Any) -> ToolResult:
        """
        执行代码

        Args:
            code: Python代码
            timeout: 超时时间

        Returns:
            ToolResult: 执行结果
        """
        # 验证代码安全性
        issues = self.sandbox.validate_code(code)
        if issues:
            return ToolResult(
                success=False,
                error=f"Code validation failed: {issues}",
            )

        # 执行代码
        result = await self.sandbox.execute(code)

        return ToolResult(
            success=result.success,
            output=result.output,
            error=result.error,
            metadata={
                "execution_time": result.execution_time,
                "memory_used": result.memory_used,
            },
        )