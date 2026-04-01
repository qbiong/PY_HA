"""
Virtual Filesystem - 可插拔存储后端

Harness 内置能力之一:
- 虚拟文件系统
- 多存储后端支持
- 上下文持久化
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field


class FileInfo(BaseModel):
    """文件信息"""

    path: str = Field(..., description="文件路径")
    content: str | bytes = Field(..., description="文件内容")
    metadata: dict[str, Any] = Field(default_factory=dict, description="元数据")
    created_at: float = Field(default=0.0, description="创建时间")
    updated_at: float = Field(default=0.0, description="更新时间")


class StorageBackend(ABC):
    """
    存储后端抽象 - 定义统一的存储接口

    支持多种存储后端:
    - 本地文件系统
    - Redis
    - 数据库
    - 云存储
    """

    @abstractmethod
    async def read(self, path: str) -> FileInfo | None:
        """读取文件"""
        pass

    @abstractmethod
    async def write(self, path: str, content: str | bytes, metadata: dict[str, Any] | None = None) -> FileInfo:
        """写入文件"""
        pass

    @abstractmethod
    async def delete(self, path: str) -> bool:
        """删除文件"""
        pass

    @abstractmethod
    async def list_files(self, prefix: str = "") -> list[str]:
        """列出文件"""
        pass

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """检查文件是否存在"""
        pass


class LocalStorage(StorageBackend):
    """本地文件系统存储后端"""

    def __init__(self, base_path: Path | str) -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, path: str) -> Path:
        """解析路径"""
        return self.base_path / path

    async def read(self, path: str) -> FileInfo | None:
        """读取文件"""
        import time
        full_path = self._resolve_path(path)
        if not full_path.exists():
            return None
        content = full_path.read_text(encoding="utf-8")
        stat = full_path.stat()
        return FileInfo(
            path=path,
            content=content,
            created_at=stat.st_ctime,
            updated_at=stat.st_mtime,
        )

    async def write(self, path: str, content: str | bytes, metadata: dict[str, Any] | None = None) -> FileInfo:
        """写入文件"""
        import time
        full_path = self._resolve_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            full_path.write_bytes(content)
        else:
            full_path.write_text(content, encoding="utf-8")
        now = time.time()
        return FileInfo(
            path=path,
            content=content,
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
        )

    async def delete(self, path: str) -> bool:
        """删除文件"""
        full_path = self._resolve_path(path)
        if not full_path.exists():
            return False
        full_path.unlink()
        return True

    async def list_files(self, prefix: str = "") -> list[str]:
        """列出文件"""
        files = []
        for p in self.base_path.rglob("*"):
            if p.is_file():
                rel_path = str(p.relative_to(self.base_path))
                if rel_path.startswith(prefix):
                    files.append(rel_path)
        return files

    async def exists(self, path: str) -> bool:
        """检查文件是否存在"""
        return self._resolve_path(path).exists()


class VirtualFS:
    """
    虚拟文件系统 - 提供统一的文件访问接口

    核心功能:
    1. 多后端支持
    2. 文件缓存
    3. 权限控制
    4. 上下文存储
    """

    def __init__(self, backend: StorageBackend | None = None) -> None:
        self._backend = backend or LocalStorage(Path(".py_ha_fs"))
        self._cache: dict[str, FileInfo] = {}

    def set_backend(self, backend: StorageBackend) -> None:
        """设置存储后端"""
        self._backend = backend

    async def read(self, path: str, use_cache: bool = True) -> FileInfo | None:
        """读取文件"""
        if use_cache and path in self._cache:
            return self._cache[path]
        result = await self._backend.read(path)
        if result is not None and use_cache:
            self._cache[path] = result
        return result

    async def write(self, path: str, content: str | bytes) -> FileInfo:
        """写入文件"""
        result = await self._backend.write(path, content)
        self._cache[path] = result
        return result

    async def delete(self, path: str) -> bool:
        """删除文件"""
        result = await self._backend.delete(path)
        if result:
            self._cache.pop(path, None)
        return result

    async def list_files(self, prefix: str = "") -> list[str]:
        """列出文件"""
        return await self._backend.list_files(prefix)

    async def exists(self, path: str) -> bool:
        """检查文件是否存在"""
        return await self._backend.exists(path)

    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()