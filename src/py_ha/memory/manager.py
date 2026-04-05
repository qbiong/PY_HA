"""
Memory Manager - JVM-style Memory Management Controller

统一记忆管理器，整合:
- 分代存储: Permanent/Old/Survivor/Eden
- 垃圾回收: 自动清理过期数据
- 热点检测: 识别高频访问数据
- 上下文装配: 渐进式披露
- 文档管理: 所有权控制、版本管理

数据流:
====================

Permanent 区 (核心知识，永不回收):
- 项目配置 (project.json)
- 角色定义 (AGENTS.md)
- 核心知识

Old 区 (文档资产，长期存储):
- requirements.md
- design.md
- progress.md
- development.md
- testing.md

Survivor 区 (当前任务，短期活跃):
- 当前任务上下文
- 任务依赖关系
- 临时状态

Eden 区 (会话消息，可丢弃):
- 用户对话
- AI 响应
"""

from typing import Any
from pydantic import BaseModel, Field
import os
import json
import time

from py_ha.memory.heap import (
    MemoryHeap,
    MemoryEntry,
    MemoryRegion,
)
from py_ha.memory.gc import (
    GarbageCollector,
    GCResult,
)
from py_ha.memory.hotspot import HotspotDetector, HotspotInfo


# ==================== 文档系统定义 ====================

class DocumentType:
    """文档类型常量"""

    REQUIREMENTS = "requirements"
    DESIGN = "design"
    DEVELOPMENT = "development"
    TESTING = "testing"
    PROGRESS = "progress"


# 文档所有权配置（用于渐进式披露）
DOCUMENT_OWNERSHIP = {
    DocumentType.REQUIREMENTS: {
        "owner": "product_manager",
        "visible_to": ["project_manager", "product_manager", "developer"],
        "read_only_for": ["developer"],
    },
    DocumentType.DESIGN: {
        "owner": "architect",
        "visible_to": ["project_manager", "architect", "developer"],
        "read_only_for": ["developer"],
    },
    DocumentType.DEVELOPMENT: {
        "owner": "developer",
        "visible_to": ["project_manager", "developer"],
        "read_only_for": [],
    },
    DocumentType.TESTING: {
        "owner": "tester",
        "visible_to": ["project_manager", "tester", "developer"],
        "read_only_for": ["developer"],
    },
    DocumentType.PROGRESS: {
        "owner": "project_manager",
        "visible_to": ["project_manager", "product_manager", "architect", "developer", "tester"],
        "read_only_for": ["product_manager", "architect", "developer", "tester"],
    },
}

# 文档类型到JVM内存区域的映射
DOCUMENT_REGION_MAP = {
    "project_info": MemoryRegion.PERMANENT,
    "team_config": MemoryRegion.PERMANENT,
    DocumentType.DESIGN: MemoryRegion.OLD,
    DocumentType.REQUIREMENTS: MemoryRegion.SURVIVOR_0,
    DocumentType.PROGRESS: MemoryRegion.SURVIVOR_0,
    DocumentType.DEVELOPMENT: MemoryRegion.EDEN,
    DocumentType.TESTING: MemoryRegion.EDEN,
}

# 区域加载策略（渐进式披露）
REGION_LOAD_STRATEGY = {
    MemoryRegion.PERMANENT: {
        "always_load": True,
        "full_content": True,
        "description": "项目核心信息，始终加载完整内容",
    },
    MemoryRegion.OLD: {
        "always_load": False,
        "full_content": False,
        "description": "长期文档，按需加载摘要",
    },
    MemoryRegion.SURVIVOR_0: {
        "always_load": True,
        "full_content": False,
        "description": "活跃文档，加载摘要",
    },
    MemoryRegion.EDEN: {
        "always_load": False,
        "full_content": False,
        "description": "临时内容，按需加载",
    },
}


def get_document_region(doc_type: str) -> MemoryRegion:
    """获取文档所属的内存区域"""
    return DOCUMENT_REGION_MAP.get(doc_type, MemoryRegion.EDEN)


def get_region_load_strategy(region: MemoryRegion) -> dict[str, Any]:
    """获取区域的加载策略"""
    return REGION_LOAD_STRATEGY.get(region, REGION_LOAD_STRATEGY[MemoryRegion.EDEN])


class ProjectInfo(BaseModel):
    """项目基本信息"""
    name: str = Field(default="", description="项目名称")
    description: str = Field(default="", description="项目描述")
    tech_stack: str = Field(default="", description="技术栈")
    status: str = Field(default="init", description="项目状态")
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


class ProjectStats(BaseModel):
    """项目统计"""
    features_total: int = Field(default=0)
    features_completed: int = Field(default=0)
    bugs_total: int = Field(default=0)
    bugs_fixed: int = Field(default=0)
    progress: int = Field(default=0)


class MemoryManager:
    """
    统一记忆管理器 - JVM 风格

    核心功能:
    1. 分代存储: 不同数据存入不同区域
    2. 垃圾回收: 自动清理过期数据
    3. 热点检测: 识别高频访问数据
    4. 上下文装配: 为 LLM 生成上下文
    5. 持久化: 自动保存到磁盘

    使用示例:
        memory = MemoryManager(".py_ha")

        # 存储项目知识
        memory.store_knowledge("project_name", "电商平台")

        # 存储文档
        memory.store_document("requirements", "# 需求\\n...")

        # 存储当前任务
        memory.store_task("TASK-123", {"desc": "实现登录"})

        # 存储会话消息
        memory.store_message("用户需要一个登录功能", "user")

        # 获取上下文
        context = memory.get_context_for_llm("developer", max_tokens=4000)
    """

    # 文档类型映射到区域
    DOC_REGIONS = {
        "requirements": MemoryRegion.OLD,
        "design": MemoryRegion.OLD,
        "development": MemoryRegion.OLD,
        "testing": MemoryRegion.OLD,
        "progress": MemoryRegion.OLD,
    }

    def __init__(self, workspace: str = ".py_ha") -> None:
        """
        初始化记忆管理器

        Args:
            workspace: 工作空间路径，用于持久化
        """
        self.workspace = workspace

        # 核心组件
        self.heap = MemoryHeap()
        self.gc = GarbageCollector()
        self.hotspot = HotspotDetector()

        # 项目状态
        self.project_info = ProjectInfo()
        self.project_stats = ProjectStats()

        # 当前任务
        self._current_task: dict[str, Any] = {}

        # 确保目录存在
        self._ensure_directories()

        # 加载持久化数据
        self._load()

    def _ensure_directories(self) -> None:
        """确保目录存在"""
        dirs = [
            self.workspace,
            os.path.join(self.workspace, "documents"),
            os.path.join(self.workspace, "summaries"),
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)

    # ==================== 统一存储接口 ====================

    def store_knowledge(self, key: str, content: str, importance: int = 100) -> None:
        """
        存储核心知识 → Permanent 区

        Args:
            key: 知识键
            content: 知识内容
            importance: 重要性 (默认最高)
        """
        self.heap.permanent.store_knowledge(key, content, importance)
        self.hotspot.record_knowledge_reference(key)
        self._save()

    def get_knowledge(self, key: str) -> str | None:
        """获取核心知识"""
        self.hotspot.record_knowledge_reference(key)
        entry = self.heap.permanent.get_knowledge(key)
        return entry.content if entry else None

    def store_document(self, doc_type: str, content: str) -> bool:
        """
        存储项目文档 → Old 区

        Args:
            doc_type: 文档类型 (requirements/design/development/testing/progress)
            content: 文档内容
        """
        # 存储到 Old 区
        entry = MemoryEntry(
            id=doc_type,
            content=content,
            importance=70,
            region=MemoryRegion.OLD,
        )
        self.heap.old.put(entry)

        # 记录热点
        self.hotspot.record_knowledge_reference(doc_type)

        # 持久化到文件
        self._save_document(doc_type, content)

        return True

    def get_document(self, doc_type: str) -> str | None:
        """获取项目文档"""
        self.hotspot.record_knowledge_reference(doc_type)
        entry = self.heap.old.get(doc_type)
        return entry.content if entry else None

    def store_task(self, task_id: str, task_info: dict[str, Any]) -> None:
        """
        存储当前任务 → Survivor 区

        Args:
            task_id: 任务ID
            task_info: 任务信息
        """
        entry = MemoryEntry(
            id=task_id,
            content=json.dumps(task_info),
            importance=80,
            region=MemoryRegion.SURVIVOR_0,
        )
        self.heap.get_active_survivor().put(entry)
        self._current_task = {"task_id": task_id, **task_info}

        # 触发 GC 检查
        self._maybe_gc()

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        """获取任务"""
        entry = self.heap.get_active_survivor().get(task_id)
        if entry:
            return json.loads(entry.content)
        return None

    def get_current_task(self) -> dict[str, Any]:
        """获取当前任务"""
        return self._current_task.copy()

    def clear_task(self, task_id: str) -> bool:
        """清除任务"""
        self.heap.get_active_survivor().remove(task_id)
        if self._current_task.get("task_id") == task_id:
            self._current_task = {}
            # 删除当前任务文件
            current_task_path = os.path.join(self.workspace, "current_task.json")
            if os.path.exists(current_task_path):
                os.remove(current_task_path)
        self._save()
        return True

    def store_message(self, message: str, role: str = "user", importance: int = 50) -> None:
        """
        存储会话消息 → Eden 区

        Args:
            message: 消息内容
            role: 角色 (user/assistant/system)
            importance: 重要性
        """
        self.heap.allocate(message, importance, {"role": role})

        # 触发 GC 检查
        self._maybe_gc()

    def get_recent_messages(self, limit: int = 20) -> list[dict[str, Any]]:
        """获取最近的消息"""
        entries = self.heap.eden.list_entries()[-limit:]
        return [
            {"content": e.content, "role": e.metadata.get("role", "user")}
            for e in entries
        ]

    # ==================== 上下文装配 ====================

    def get_context_for_llm(self, role: str = "developer", max_tokens: int = 4000) -> str:
        """
        为 LLM 装配上下文（渐进式披露）

        流程:
        1. Permanent (核心知识) - 全量注入
        2. Survivor (当前任务) - 注入
        3. Old (文档) - 按热点和相关性注入
        4. Eden (会话) - 最近 N 条

        Args:
            role: 目标角色
            max_tokens: 最大 Token 数

        Returns:
            装配好的上下文字符串
        """
        sections = []
        current_tokens = 0

        # 0. 核心 API 指导（始终注入）
        api_guide = """# py_ha 核心 API 指南

## 初始化（已完成）
```python
from py_ha import Harness
harness = Harness("项目名")  # 默认持久化到 .py_ha/ 目录
```

## 核心方法

### 1. 接收用户请求
```python
# 用户提出需求或Bug
result = harness.receive_request("实现用户登录功能", request_type="feature")  # 功能需求
result = harness.receive_request("登录页面报错", request_type="bug")  # Bug报告
# 返回: {"task_id": "TASK-xxx", "priority": "P1", "assignee": "developer"}
```

### 2. 记忆管理
```python
harness.remember("key", "重要信息", important=True)  # 存储核心知识
harness.recall("key")  # 获取知识
harness.record("开发日志内容", context="开发过程")  # 记录到文档
```

### 3. 对话记录
```python
harness.chat("用户消息")  # 自动记录并识别需求/Bug
harness.chat("AI回复", role="assistant")
```

### 4. 任务完成
```python
harness.complete_task("TASK-xxx", "完成摘要")  # 标记任务完成
```

### 5. 状态查询
```python
status = harness.get_status()  # 获取项目状态
report = harness.get_report()  # 获取项目报告
context = harness.get_context_prompt()  # 获取上下文（每次对话开始时调用）
```

## 自动处理规则
- 用户说"需要/要/添加功能" → 自动调用 receive_request("...", "feature")
- 用户说"bug/问题/错误" → 自动调用 receive_request("...", "bug")
- 所有操作自动持久化，重启后自动恢复

"""
        sections.append(api_guide)
        current_tokens += self._estimate_tokens(api_guide)

        # 1. Permanent - 项目信息
        project_section = f"\n# 项目信息\n- 名称: {self.project_info.name}\n- 技术栈: {self.project_info.tech_stack}\n- 状态: {self.project_info.status}\n"
        sections.append(project_section)
        current_tokens += self._estimate_tokens(project_section)

        # Permanent - 核心知识
        for entry in self.heap.permanent.list_entries():
            if current_tokens < max_tokens * 0.3:
                sections.append(f"\n## {entry.id}\n{entry.content}")
                current_tokens += self._estimate_tokens(entry.content)

        # 2. Survivor - 当前任务
        if self._current_task:
            task_section = f"\n# 当前任务\n- ID: {self._current_task.get('task_id', '')}\n- 描述: {self._current_task.get('request', self._current_task.get('desc', ''))}\n- 状态: {self._current_task.get('status', '')}\n"
            sections.append(task_section)
            current_tokens += self._estimate_tokens(task_section)

        # 3. Old - 按热点加载文档
        hotspots = self.hotspot.detect_hotspots()
        for hotspot in hotspots[:3]:
            if current_tokens < max_tokens * 0.8:
                doc = self.get_document(hotspot.name)
                if doc:
                    summary = doc[:500] + "..." if len(doc) > 500 else doc
                    sections.append(f"\n## {hotspot.name}\n{summary}")
                    current_tokens += self._estimate_tokens(summary)

        # 4. Eden - 最近消息
        if current_tokens < max_tokens * 0.9:
            for msg in self.get_recent_messages(5):
                msg_text = f"\n[{msg['role']}]: {msg['content'][:200]}"
                sections.append(msg_text)
                current_tokens += self._estimate_tokens(msg_text)

        # 5. 项目统计
        stats_section = f"\n# 项目统计\n- 功能: {self.project_stats.features_completed}/{self.project_stats.features_total}\n- Bug: {self.project_stats.bugs_fixed}/{self.project_stats.bugs_total}\n- 进度: {self.project_stats.progress}%\n"
        sections.append(stats_section)

        return "\n".join(sections)

    def get_minimal_context(self) -> str:
        """获取最小上下文（仅项目信息）"""
        return f"# 项目信息\n- 名称: {self.project_info.name}\n- 技术栈: {self.project_info.tech_stack}\n"

    # ==================== GC 和热点检测 ====================

    def _maybe_gc(self) -> GCResult | None:
        """检查并触发 GC"""
        if self.heap.eden.is_full():
            result = self.gc.minor_gc(self.heap)
            self.heap.swap_survivor()
            return result
        if self.heap.old.is_full():
            return self.gc.major_gc(self.heap)
        return None

    def force_gc(self, gc_type: str = "minor") -> GCResult:
        """强制触发 GC"""
        if gc_type == "minor":
            result = self.gc.minor_gc(self.heap)
            self.heap.swap_survivor()
        elif gc_type == "major":
            result = self.gc.major_gc(self.heap)
        else:
            result = self.gc.full_gc(self.heap)
        return result

    def get_hotspots(self) -> list[HotspotInfo]:
        """获取热点数据"""
        return self.hotspot.detect_hotspots()

    # ==================== 统计和状态 ====================

    def update_stats(self, stat_type: str, delta: int = 1) -> None:
        """更新统计"""
        if stat_type == "features_total":
            self.project_stats.features_total += delta
        elif stat_type == "features_completed":
            self.project_stats.features_completed += delta
        elif stat_type == "bugs_total":
            self.project_stats.bugs_total += delta
        elif stat_type == "bugs_fixed":
            self.project_stats.bugs_fixed += delta

        # 重新计算进度
        total = self.project_stats.features_total + self.project_stats.bugs_total
        completed = self.project_stats.features_completed + self.project_stats.bugs_fixed
        self.project_stats.progress = int(completed / total * 100) if total > 0 else 0

        self._save()

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "project": self.project_info.model_dump(),
            "stats": self.project_stats.model_dump(),
            "memory": {
                "eden_size": self.heap.eden.size(),
                "survivor_size": self.heap.get_active_survivor().size(),
                "old_size": self.heap.old.size(),
                "permanent_size": self.heap.permanent.size(),
            },
            "hotspots": len(self.get_hotspots()),
        }

    def get_project_info(self) -> dict[str, Any]:
        """获取项目基本信息"""
        return self.project_info.model_dump()

    def get_document_summary(self, doc_type: str) -> str:
        """获取文档摘要"""
        doc = self.get_document(doc_type)
        if not doc:
            return ""
        # 取前500字符作为摘要
        return doc[:500] + "..." if len(doc) > 500 else doc

    def list_documents(self) -> list[dict[str, Any]]:
        """列出所有文档"""
        doc_dir = os.path.join(self.workspace, "documents")
        if not os.path.exists(doc_dir):
            return []

        result = []
        for doc_type in [DocumentType.REQUIREMENTS, DocumentType.DESIGN,
                         DocumentType.DEVELOPMENT, DocumentType.TESTING, DocumentType.PROGRESS]:
            doc_path = os.path.join(doc_dir, f"{doc_type}.md")
            if os.path.exists(doc_path):
                ownership = DOCUMENT_OWNERSHIP.get(doc_type, {})
                result.append({
                    "type": doc_type,
                    "owner": ownership.get("owner", "project_manager"),
                    "exists": True,
                    "path": doc_path,
                })
        return result

    def get_context_for_role(self, role_type: str) -> dict[str, Any]:
        """
        为角色生成最小必要上下文（渐进式披露）

        Args:
            role_type: 角色类型

        Returns:
            角色特定的上下文
        """
        # 项目基本信息（所有角色都可见）
        context = {
            "project": {
                "name": self.project_info.name,
                "tech_stack": self.project_info.tech_stack,
                "status": self.project_info.status,
            },
            "stats": self.project_stats.model_dump(),
        }

        # 根据角色类型添加特定信息
        if role_type == "project_manager":
            # 项目经理可以看到所有信息
            context["documents"] = {}
            for doc_type in [DocumentType.REQUIREMENTS, DocumentType.DESIGN,
                             DocumentType.DEVELOPMENT, DocumentType.TESTING, DocumentType.PROGRESS]:
                doc = self.get_document(doc_type)
                if doc:
                    context["documents"][doc_type] = doc
            context["full_access"] = True

        elif role_type == "product_manager":
            # 产品经理：需求文档完整 + 其他摘要
            context["requirements"] = self.get_document(DocumentType.REQUIREMENTS) or ""
            context["progress_summary"] = self.get_document_summary(DocumentType.PROGRESS)

        elif role_type == "architect":
            # 架构师：需求摘要 + 设计文档完整
            context["requirements_summary"] = self.get_document_summary(DocumentType.REQUIREMENTS)
            context["design"] = self.get_document(DocumentType.DESIGN) or ""

        elif role_type == "developer":
            # 开发者：最小信息
            context["requirements_summary"] = self.get_document_summary(DocumentType.REQUIREMENTS)
            context["design_summary"] = self.get_document_summary(DocumentType.DESIGN)
            context["development"] = self.get_document(DocumentType.DEVELOPMENT) or ""

        elif role_type == "tester":
            # 测试人员：需求摘要 + 测试文档
            context["requirements_summary"] = self.get_document_summary(DocumentType.REQUIREMENTS)
            context["testing"] = self.get_document(DocumentType.TESTING) or ""
            context["development_summary"] = self.get_document_summary(DocumentType.DEVELOPMENT)

        return context

    def get_project_summary(self) -> str:
        """获取项目总摘要"""
        summary_lines = [
            f"# {self.project_info.name}",
            "",
            f"**状态**: {self.project_info.status}",
            f"**技术栈**: {self.project_info.tech_stack}",
            "",
            "## 进度",
            f"- 功能: {self.project_stats.features_completed}/{self.project_stats.features_total}",
            f"- Bug: {self.project_stats.bugs_fixed}/{self.project_stats.bugs_total}",
            f"- 总进度: {self.project_stats.progress}%",
        ]

        # 添加各文档摘要
        for doc_type in [DocumentType.REQUIREMENTS, DocumentType.DESIGN,
                         DocumentType.DEVELOPMENT, DocumentType.TESTING]:
            doc = self.get_document(doc_type)
            if doc:
                summary_lines.append("")
                summary_lines.append(f"## {doc_type.upper()}")
                summary_lines.append(self.get_document_summary(doc_type)[:200] + "...")

        return "\n".join(summary_lines)

    def get_health_report(self) -> dict[str, Any]:
        """获取健康报告"""
        eden_pressure = self.heap.eden.size() / self.heap.eden.max_size
        old_pressure = self.heap.old.size() / self.heap.old.max_size

        if eden_pressure > 0.9 or old_pressure > 0.9:
            status = "critical"
        elif eden_pressure > 0.7 or old_pressure > 0.7:
            status = "warning"
        else:
            status = "healthy"

        return {"status": status}

    # ==================== 持久化 ====================

    def _save(self) -> None:
        """保存状态"""
        try:
            # 保存项目信息
            project_path = os.path.join(self.workspace, "project.json")
            with open(project_path, "w", encoding="utf-8") as f:
                json.dump({
                    "info": self.project_info.model_dump(),
                    "stats": self.project_stats.model_dump(),
                }, f, ensure_ascii=False, indent=2)

            # 保存当前任务
            if self._current_task:
                current_task_path = os.path.join(self.workspace, "current_task.json")
                with open(current_task_path, "w", encoding="utf-8") as f:
                    json.dump(self._current_task, f, ensure_ascii=False, indent=2)

            # 保存 Permanent 区知识
            knowledge_path = os.path.join(self.workspace, "knowledge.json")
            knowledge_data = {}
            for entry in self.heap.permanent.list_entries():
                knowledge_data[entry.id] = {
                    "content": entry.content,
                    "importance": entry.importance,
                }
            with open(knowledge_path, "w", encoding="utf-8") as f:
                json.dump(knowledge_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _save_document(self, doc_type: str, content: str) -> None:
        """保存文档"""
        try:
            doc_path = os.path.join(self.workspace, "documents", f"{doc_type}.md")
            with open(doc_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception:
            pass

    def _load(self) -> None:
        """加载持久化数据"""
        # 加载项目信息
        project_path = os.path.join(self.workspace, "project.json")
        if os.path.exists(project_path):
            try:
                with open(project_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.project_info = ProjectInfo(**data.get("info", {}))
                self.project_stats = ProjectStats(**data.get("stats", {}))
            except Exception:
                pass

        # 加载当前任务
        current_task_path = os.path.join(self.workspace, "current_task.json")
        if os.path.exists(current_task_path):
            try:
                with open(current_task_path, "r", encoding="utf-8") as f:
                    self._current_task = json.load(f)
            except Exception:
                pass

        # 加载 Permanent 区知识
        knowledge_path = os.path.join(self.workspace, "knowledge.json")
        if os.path.exists(knowledge_path):
            try:
                with open(knowledge_path, "r", encoding="utf-8") as f:
                    knowledge_data = json.load(f)
                for key, value in knowledge_data.items():
                    self.heap.permanent.store_knowledge(
                        key,
                        value.get("content", ""),
                        value.get("importance", 100)
                    )
            except Exception:
                pass

        # 加载文档
        doc_dir = os.path.join(self.workspace, "documents")
        if os.path.exists(doc_dir):
            for doc_type in ["requirements", "design", "development", "testing", "progress"]:
                doc_path = os.path.join(doc_dir, f"{doc_type}.md")
                if os.path.exists(doc_path):
                    try:
                        with open(doc_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        self.store_document(doc_type, content)
                    except Exception:
                        pass

    def reload(self) -> bool:
        """重新加载"""
        self._load()
        return True

    def _estimate_tokens(self, content: str) -> int:
        """估算 Token 数"""
        import re
        if not content:
            return 0

        chinese = len(re.findall(r'[\u4e00-\u9fff]', content))
        other = len(content) - chinese

        return int(chinese / 1.5) + int(other / 4)


# 便捷函数
def create_memory_manager(workspace: str = ".py_ha") -> MemoryManager:
    """创建记忆管理器"""
    return MemoryManager(workspace)