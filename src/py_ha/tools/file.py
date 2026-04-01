"""
File Tools - 文件操作工具

提供文件读写能力
"""

from pathlib import Path
from typing import Any

from py_ha.tools.base import BaseTool, ToolResult


class FileReadTool(BaseTool):
    """
    文件读取工具

    功能:
    1. 读取文件内容
    2. 支持多种编码
    """

    @property
    def name(self) -> str:
        return "file_read"

    @property
    def description(self) -> str:
        return "Read file content from the filesystem"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path to read",
                },
                "encoding": {
                    "type": "string",
                    "description": "File encoding",
                    "default": "utf-8",
                },
            },
            "required": ["path"],
        }

    async def execute(self, path: str, encoding: str = "utf-8", **kwargs: Any) -> ToolResult:
        """
        读取文件

        Args:
            path: 文件路径
            encoding: 编码格式

        Returns:
            ToolResult: 文件内容
        """
        try:
            file_path = Path(path)
            if not file_path.exists():
                return ToolResult(
                    success=False,
                    error=f"File not found: {path}",
                )

            content = file_path.read_text(encoding=encoding)
            return ToolResult(
                success=True,
                output=content,
                metadata={
                    "path": path,
                    "size": len(content),
                    "encoding": encoding,
                },
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
            )


class FileWriteTool(BaseTool):
    """
    文件写入工具

    功能:
    1. 写入文件内容
    2. 自动创建目录
    """

    @property
    def name(self) -> str:
        return "file_write"

    @property
    def description(self) -> str:
        return "Write content to a file"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path to write",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write",
                },
                "encoding": {
                    "type": "string",
                    "description": "File encoding",
                    "default": "utf-8",
                },
                "overwrite": {
                    "type": "boolean",
                    "description": "Whether to overwrite existing file",
                    "default": True,
                },
            },
            "required": ["path", "content"],
        }

    async def execute(
        self,
        path: str,
        content: str,
        encoding: str = "utf-8",
        overwrite: bool = True,
        **kwargs: Any,
    ) -> ToolResult:
        """
        写入文件

        Args:
            path: 文件路径
            content: 文件内容
            encoding: 编码格式
            overwrite: 是否覆盖

        Returns:
            ToolResult: 写入结果
        """
        try:
            file_path = Path(path)

            # 检查文件是否存在
            if file_path.exists() and not overwrite:
                return ToolResult(
                    success=False,
                    error=f"File already exists: {path}",
                )

            # 创建目录
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # 写入文件
            file_path.write_text(content, encoding=encoding)

            return ToolResult(
                success=True,
                output=f"File written: {path}",
                metadata={
                    "path": path,
                    "size": len(content),
                    "encoding": encoding,
                },
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
            )