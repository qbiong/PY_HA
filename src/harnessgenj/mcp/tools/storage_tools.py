"""
存储工具

提供与存储系统交互的 MCP 工具。
"""

from typing import Any, ClassVar

from harnessgenj.mcp.tools import MCPTool
from harnessgenj.mcp.protocol import MCPToolResult


class StorageSaveTool(MCPTool):
    """保存内容到存储"""

    name: ClassVar[str] = "storage_save"
    description: ClassVar[str] = "保存内容到项目存储系统"
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "存储键名"},
            "content": {"type": "string", "description": "存储内容"},
        },
        "required": ["key", "content"],
    }
    category: ClassVar[str] = "storage"

    def execute(self, params: dict[str, Any], harness: Any) -> MCPToolResult:
        key = params["key"]
        content = params["content"]

        try:
            harness.storage.save(key, content)
            return MCPToolResult.text_result(f"✅ 已保存: {key}")
        except Exception as e:
            return MCPToolResult.error_result(f"保存失败: {e}")


class StorageLoadTool(MCPTool):
    """从存储加载内容"""

    name: ClassVar[str] = "storage_load"
    description: ClassVar[str] = "从项目存储系统加载内容"
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "存储键名"},
        },
        "required": ["key"],
    }
    category: ClassVar[str] = "storage"

    def execute(self, params: dict[str, Any], harness: Any) -> MCPToolResult:
        key = params["key"]

        try:
            content = harness.storage.load(key)
            if content:
                return MCPToolResult.text_result(f"📦 {key}:\n{content}")
            else:
                return MCPToolResult.text_result(f"❌ 未找到: {key}")
        except Exception as e:
            return MCPToolResult.error_result(f"加载失败: {e}")


class StorageSaveKnowledgeTool(MCPTool):
    """保存知识到存储"""

    name: ClassVar[str] = "storage_save_knowledge"
    description: ClassVar[str] = "保存知识到 AGENTS.md 知识库"
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "知识键名"},
            "value": {"type": "string", "description": "知识内容"},
            "category": {"type": "string", "description": "知识类别", "default": "general"},
        },
        "required": ["key", "value"],
    }
    category: ClassVar[str] = "storage"

    def execute(self, params: dict[str, Any], harness: Any) -> MCPToolResult:
        key = params["key"]
        value = params["value"]
        category = params.get("category", "general")

        try:
            harness.storage.save_knowledge(key, value, category)
            return MCPToolResult.text_result(f"✅ 已保存知识: {key} (类别: {category})")
        except Exception as e:
            return MCPToolResult.error_result(f"保存知识失败: {e}")


class StorageSearchTool(MCPTool):
    """搜索知识库"""

    name: ClassVar[str] = "storage_search"
    description: ClassVar[str] = "搜索 AGENTS.md 知识库"
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索关键词"},
            "limit": {"type": "integer", "description": "返回结果数量", "default": 5},
        },
        "required": ["query"],
    }
    category: ClassVar[str] = "storage"

    def execute(self, params: dict[str, Any], harness: Any) -> MCPToolResult:
        query = params["query"]
        limit = params.get("limit", 5)

        try:
            results = harness.storage.search_knowledge(query, limit=limit)
            if results:
                result_text = f"🔍 搜索结果 ({query}):\n"
                for item in results:
                    result_text += f"  - {item.get('key', 'N/A')}: {item.get('value', '')[:100]}...\n"
                return MCPToolResult.text_result(result_text)
            else:
                return MCPToolResult.text_result(f"❌ 未找到匹配: {query}")
        except Exception as e:
            return MCPToolResult.error_result(f"搜索失败: {e}")


# 导出所有存储工具
STORAGE_TOOLS = [
    StorageSaveTool(),
    StorageLoadTool(),
    StorageSaveKnowledgeTool(),
    StorageSearchTool(),
]