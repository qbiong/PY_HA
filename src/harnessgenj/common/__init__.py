"""
Common Module - 公共类型和工具

此模块提供框架公共的类型定义和工具函数，避免重复定义。

子模块：
- knowledge_types: 统一知识类型定义
"""

from harnessgenj.common.knowledge_types import (
    KnowledgeType,
    KnowledgeEntry,
    CodeLocation,
    KnowledgeIndex,
)

__all__ = [
    "KnowledgeType",
    "KnowledgeEntry",
    "CodeLocation",
    "KnowledgeIndex",
]