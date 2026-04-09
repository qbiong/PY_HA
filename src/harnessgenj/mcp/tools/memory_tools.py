"""
内存管理工具

提供与 MemoryManager 交互的 MCP 工具。
"""

from typing import Any, ClassVar

from harnessgenj.mcp.tools import MCPTool
from harnessgenj.mcp.protocol import MCPToolResult


class MemoryStoreTool(MCPTool):
    """存储内容到记忆系统"""

    name: ClassVar[str] = "memory_store"
    description: ClassVar[str] = "存储内容到记忆系统，持久化保存知识"
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "存储键名"},
            "content": {"type": "string", "description": "存储内容"},
            "importance": {"type": "integer", "description": "重要性 (0-100)", "default": 50},
        },
        "required": ["key", "content"],
    }
    category: ClassVar[str] = "memory"

    def execute(self, params: dict[str, Any], harness: Any) -> MCPToolResult:
        key = params["key"]
        content = params["content"]
        importance = params.get("importance", 50)

        try:
            harness.memory.store_knowledge(key, content, importance)
            return MCPToolResult.text_result(f"✅ 已存储知识: {key}")
        except Exception as e:
            return MCPToolResult.error_result(f"存储失败: {e}")


class MemoryRetrieveTool(MCPTool):
    """从记忆系统检索内容"""

    name: ClassVar[str] = "memory_retrieve"
    description: ClassVar[str] = "从记忆系统检索已存储的内容"
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "检索键名"},
        },
        "required": ["key"],
    }
    category: ClassVar[str] = "memory"

    def execute(self, params: dict[str, Any], harness: Any) -> MCPToolResult:
        key = params["key"]

        try:
            content = harness.memory.get_knowledge(key)
            if content:
                return MCPToolResult.text_result(f"📦 {key}:\n{content}")
            else:
                return MCPToolResult.text_result(f"❌ 未找到: {key}")
        except Exception as e:
            return MCPToolResult.error_result(f"检索失败: {e}")


class MemoryStatusTool(MCPTool):
    """获取记忆系统状态"""

    name: ClassVar[str] = "memory_status"
    description: ClassVar[str] = "获取记忆系统的当前状态和统计信息"
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {},
    }
    category: ClassVar[str] = "memory"

    def execute(self, params: dict[str, Any], harness: Any) -> MCPToolResult:
        try:
            stats = harness.memory.get_stats()
            result = f"""📊 记忆系统状态
━━━━━━━━━━━━━━━━━━━━━━
项目: {stats.get('project', 'Unknown')}
功能总数: {stats['stats'].get('features_total', 0)}
已完成: {stats['stats'].get('features_completed', 0)}
Bug总数: {stats['stats'].get('bugs_total', 0)}
已修复: {stats['stats'].get('bugs_fixed', 0)}
进度: {stats['stats'].get('progress', 0)}%

内存区域:
- Eden: {stats['memory'].get('eden_size', 0)}
- Old: {stats['memory'].get('old_size', 0)}
"""
            return MCPToolResult.text_result(result)
        except Exception as e:
            return MCPToolResult.error_result(f"获取状态失败: {e}")


class MemoryGCTool(MCPTool):
    """执行内存垃圾回收"""

    name: ClassVar[str] = "memory_gc"
    description: ClassVar[str] = "执行记忆系统的垃圾回收，清理过期内容"
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "force": {"type": "boolean", "description": "是否强制执行", "default": False},
        },
    }
    category: ClassVar[str] = "memory"

    def execute(self, params: dict[str, Any], harness: Any) -> MCPToolResult:
        try:
            # 触发 GC
            if hasattr(harness.memory, 'gc'):
                harness.memory.gc.collect()
                return MCPToolResult.text_result("✅ 内存垃圾回收完成")
            else:
                return MCPToolResult.text_result("⚠️ GC 模块未启用")
        except Exception as e:
            return MCPToolResult.error_result(f"GC 执行失败: {e}")


class MemoryStoreDocumentTool(MCPTool):
    """存储文档到记忆系统"""

    name: ClassVar[str] = "memory_store_document"
    description: ClassVar[str] = "存储项目文档（需求、设计、开发日志等）"
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "doc_type": {
                "type": "string",
                "description": "文档类型 (requirements/design/development/testing/progress)",
            },
            "content": {"type": "string", "description": "文档内容"},
        },
        "required": ["doc_type", "content"],
    }
    category: ClassVar[str] = "memory"

    def execute(self, params: dict[str, Any], harness: Any) -> MCPToolResult:
        doc_type = params["doc_type"]
        content = params["content"]

        try:
            harness.memory.store_document(doc_type, content)
            return MCPToolResult.text_result(f"✅ 已存储文档: {doc_type}")
        except Exception as e:
            return MCPToolResult.error_result(f"存储文档失败: {e}")


class MemoryGetDocumentTool(MCPTool):
    """获取项目文档"""

    name: ClassVar[str] = "memory_get_document"
    description: ClassVar[str] = "获取已存储的项目文档"
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "doc_type": {
                "type": "string",
                "description": "文档类型 (requirements/design/development/testing/progress)",
            },
        },
        "required": ["doc_type"],
    }
    category: ClassVar[str] = "memory"

    def execute(self, params: dict[str, Any], harness: Any) -> MCPToolResult:
        doc_type = params["doc_type"]

        try:
            content = harness.memory.get_document(doc_type)
            if content:
                return MCPToolResult.text_result(f"📄 {doc_type}:\n{content[:1000]}...")
            else:
                return MCPToolResult.text_result(f"❌ 未找到文档: {doc_type}")
        except Exception as e:
            return MCPToolResult.error_result(f"获取文档失败: {e}")


# 导出所有内存工具
MEMORY_TOOLS = [
    MemoryStoreTool(),
    MemoryRetrieveTool(),
    MemoryStatusTool(),
    MemoryGCTool(),
    MemoryStoreDocumentTool(),
    MemoryGetDocumentTool(),
]