"""
Storage Manager - 统一存储管理

提供简单的API，自动选择存储后端:
- 默认使用内存存储 (无需配置)
- 可选文件存储 (持久化)
"""

from pathlib import Path
from typing import Any
from enum import Enum

from py_ha.storage.markdown import MarkdownStorage, MarkdownKnowledgeBase
from py_ha.storage.json_store import JsonStorage, TaskStateStorage, ContextStorage
from py_ha.storage.memory import MemoryStorage, MemoryKnowledgeBase


class StorageType(Enum):
    """存储类型"""

    MEMORY = "memory"       # 内存存储 (默认，无需配置)
    FILE = "file"           # 文件存储 (持久化)
    MARKDOWN = "markdown"   # Markdown存储 (人类可读)


class StorageManager:
    """
    存储管理器 - 统一管理所有存储

    设计原则:
    - 默认内存存储，无需任何配置
    - 可选持久化，一行配置即可
    - 统一API，切换透明
    """

    def __init__(
        self,
        storage_type: StorageType = StorageType.MEMORY,
        base_path: Path | str = ".py_ha",
    ) -> None:
        self.storage_type = storage_type
        self.base_path = Path(base_path)

        # 知识分类映射 (记录每个key对应的category)
        self._knowledge_categories: dict[str, str] = {}

        # 根据类型初始化存储
        if storage_type == StorageType.MEMORY:
            self._storage = MemoryStorage()
            self._knowledge_base = MemoryKnowledgeBase()
            self._task_storage = MemoryStorage()
            self._context_storage = MemoryStorage()
        else:
            # 文件存储
            self._storage = JsonStorage(self.base_path / "data")
            self._knowledge_base = MarkdownKnowledgeBase(self.base_path / "knowledge")
            self._task_storage = TaskStateStorage(self.base_path / "data" / "tasks")
            self._context_storage = ContextStorage(self.base_path / "data" / "contexts")

            # 如果是markdown存储，创建额外结构
            if storage_type == StorageType.MARKDOWN:
                self._markdown = MarkdownStorage(self.base_path)

    # ==================== 通用存储 ====================

    def save(self, key: str, data: Any) -> bool:
        """保存数据"""
        return self._storage.save(key, data)

    def load(self, key: str) -> Any | None:
        """加载数据"""
        return self._storage.load(key)

    def delete(self, key: str) -> bool:
        """删除数据"""
        return self._storage.delete(key)

    def exists(self, key: str) -> bool:
        """检查数据是否存在"""
        return self._storage.exists(key)

    def list_keys(self) -> list[str]:
        """列出所有键"""
        return self._storage.list_keys()

    # ==================== 知识库 ====================

    def save_knowledge(self, key: str, content: str, metadata: dict[str, Any] | None = None) -> bool:
        """保存知识"""
        category = metadata.get("category", "general") if metadata else "general"
        # 记录分类映射
        self._knowledge_categories[key] = category

        if isinstance(self._knowledge_base, MemoryKnowledgeBase):
            return self._knowledge_base.save(key, content, metadata)
        else:
            from py_ha.storage.markdown import KnowledgeEntry
            entry = KnowledgeEntry(
                id=key,
                title=key,
                content=content,
                metadata=metadata or {},
            )
            return self._knowledge_base.save(entry, category)

    def load_knowledge(self, key: str) -> str | None:
        """加载知识"""
        if isinstance(self._knowledge_base, MemoryKnowledgeBase):
            return self._knowledge_base.load(key)
        else:
            # 使用映射获取正确的category
            category = self._knowledge_categories.get(key, "general")
            entry = self._knowledge_base.load(key, category=category)
            return entry.content if entry else None

    def search_knowledge(self, query: str) -> list[dict[str, Any]]:
        """搜索知识"""
        return self._knowledge_base.search(query)

    def list_knowledge(self) -> list[str]:
        """列出所有知识键"""
        if isinstance(self._knowledge_base, MemoryKnowledgeBase):
            return self._knowledge_base.list_all()
        return [e.id for e in self._knowledge_base.list_all()]

    # ==================== 任务状态 ====================

    def save_task_state(self, task_id: str, state: dict[str, Any]) -> bool:
        """保存任务状态"""
        return self._task_storage.save(f"task_{task_id}", state)

    def load_task_state(self, task_id: str) -> dict[str, Any] | None:
        """加载任务状态"""
        return self._task_storage.load(f"task_{task_id}")

    def list_tasks(self) -> list[str]:
        """列出所有任务ID"""
        keys = self._task_storage.list_keys()
        return [k.replace("task_", "") for k in keys if k.startswith("task_")]

    # ==================== 上下文 ====================

    def save_context(self, context_id: str, context: dict[str, Any]) -> bool:
        """保存上下文"""
        return self._context_storage.save(f"ctx_{context_id}", context)

    def load_context(self, context_id: str) -> dict[str, Any] | None:
        """加载上下文"""
        return self._context_storage.load(f"ctx_{context_id}")

    def list_contexts(self) -> list[str]:
        """列出所有上下文ID"""
        keys = self._context_storage.list_keys()
        return [k.replace("ctx_", "") for k in keys if k.startswith("ctx_")]

    # ==================== 统计与清理 ====================

    def get_stats(self) -> dict[str, Any]:
        """获取存储统计"""
        return {
            "storage_type": self.storage_type.value,
            "data_count": len(self.list_keys()),
            "knowledge_count": len(self.list_knowledge()),
            "task_count": len(self.list_tasks()),
            "context_count": len(self.list_contexts()),
            "base_path": str(self.base_path) if self.storage_type != StorageType.MEMORY else "memory",
        }

    def clear_all(self) -> dict[str, int]:
        """清空所有存储"""
        return {
            "data": len(self.list_keys()),
            "knowledge": len(self.list_knowledge()),
            "tasks": len(self.list_tasks()),
            "contexts": len(self.list_contexts()),
        }

    # ==================== 便捷方法 ====================

    def is_persistent(self) -> bool:
        """是否持久化存储"""
        return self.storage_type != StorageType.MEMORY

    def get_storage_info(self) -> str:
        """获取存储信息"""
        if self.storage_type == StorageType.MEMORY:
            return "Memory Storage (no persistence)"
        else:
            return f"File Storage at {self.base_path}"


def create_storage(
    persistent: bool = False,
    base_path: str = ".py_ha",
) -> StorageManager:
    """
    创建存储管理器 - 便捷函数

    Args:
        persistent: 是否持久化 (默认False，使用内存)
        base_path: 存储路径

    Returns:
        StorageManager实例

    Examples:
        # 内存存储 (默认)
        storage = create_storage()

        # 持久化存储
        storage = create_storage(persistent=True)
    """
    storage_type = StorageType.FILE if persistent else StorageType.MEMORY
    return StorageManager(storage_type=storage_type, base_path=base_path)