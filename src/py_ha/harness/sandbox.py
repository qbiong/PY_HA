"""
Code Sandbox - 安全代码执行环境

Harness 内置能力之一:
- 代码沙箱执行
- 安全隔离
- 资源限制
"""

from typing import Any
from pydantic import BaseModel, Field


class ExecutionEnvironment(BaseModel):
    """执行环境配置"""

    timeout: int = Field(default=30, description="执行超时时间(秒)")
    max_memory: int = Field(default=128, description="最大内存使用(MB)")
    allowed_modules: list[str] = Field(default_factory=list, description="允许的模块")
    network_access: bool = Field(default=False, description="是否允许网络访问")


class CodeResult(BaseModel):
    """代码执行结果"""

    success: bool = Field(..., description="是否成功")
    output: Any = Field(default=None, description="执行输出")
    error: str | None = Field(default=None, description="错误信息")
    execution_time: float = Field(default=0.0, description="执行时间(秒)")
    memory_used: float = Field(default=0.0, description="内存使用(MB)")


class CodeSandbox:
    """
    代码沙箱 - 安全执行代码

    核心功能:
    1. 代码执行
    2. 安全隔离
    3. 资源限制
    4. 结果捕获
    """

    def __init__(self, env: ExecutionEnvironment | None = None) -> None:
        self.env = env or ExecutionEnvironment()

    async def execute(self, code: str, language: str = "python") -> CodeResult:
        """
        执行代码

        Args:
            code: 要执行的代码
            language: 编程语言

        Returns:
            CodeResult: 执行结果
        """
        import time
        start_time = time.time()

        # TODO: 实现真正的沙箱执行
        # 当前为简化实现，实际需要:
        # 1. 进程隔离
        # 2. 资源限制
        # 3. 模块白名单
        # 4. 网络隔离

        try:
            # 创建受限执行环境
            local_vars: dict[str, Any] = {}
            global_vars: dict[str, Any] = {"__builtins__": {}}

            # 执行代码
            exec(code, global_vars, local_vars)

            # 获取结果
            output = local_vars.get("result", None)

            execution_time = time.time() - start_time
            return CodeResult(
                success=True,
                output=output,
                execution_time=execution_time,
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return CodeResult(
                success=False,
                error=str(e),
                execution_time=execution_time,
            )

    def validate_code(self, code: str) -> list[str]:
        """
        验证代码安全性

        检查潜在的危险操作
        """
        issues = []
        dangerous_patterns = [
            "import os",
            "import sys",
            "import subprocess",
            "eval(",
            "exec(",
            "__import__",
            "open(",
        ]

        for pattern in dangerous_patterns:
            if pattern in code:
                issues.append(f"Potentially dangerous pattern found: {pattern}")

        return issues

    async def execute_file(self, path: str) -> CodeResult:
        """执行文件中的代码"""
        from pathlib import Path

        code_path = Path(path)
        if not code_path.exists():
            return CodeResult(success=False, error=f"File not found: {path}")

        code = code_path.read_text(encoding="utf-8")

        # 验证代码
        issues = self.validate_code(code)
        if issues:
            return CodeResult(
                success=False,
                error=f"Code validation failed: {issues}",
            )

        return await self.execute(code)