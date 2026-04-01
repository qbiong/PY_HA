"""
Storage Module - Lightweight File-based Storage

轻量化存储系统，无需Redis/数据库配置:
- MarkdownStorage: 使用Markdown文件存储
- JsonStorage: 使用JSON文件存储
- MemoryStorage: 内存存储 (默认)
"""

from py_ha.storage.markdown import MarkdownStorage, MarkdownKnowledgeBase
from py_ha.storage.json_store import JsonStorage
from py_ha.storage.memory import MemoryStorage
from py_ha.storage.manager import StorageManager, StorageType, create_storage

__all__ = [
    "MarkdownStorage",
    "MarkdownKnowledgeBase",
    "JsonStorage",
    "MemoryStorage",
    "StorageManager",
    "StorageType",
    "create_storage",
]