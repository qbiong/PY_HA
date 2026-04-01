"""
Planning Tool - 任务规划与Todo追踪

Harness 内置能力之一:
- 多任务规划
- Todo列表管理
- 任务进度追踪
"""

from typing import Any
from pydantic import BaseModel, Field


class TodoItem(BaseModel):
    """Todo项"""

    id: str = Field(..., description="Todo ID")
    content: str = Field(..., description="任务内容")
    status: str = Field(default="pending", description="状态: pending/in_progress/completed")
    priority: int = Field(default=0, description="优先级 (0-10)")
    dependencies: list[str] = Field(default_factory=list, description="依赖的Todo ID")


class TodoList(BaseModel):
    """Todo列表"""

    items: list[TodoItem] = Field(default_factory=list, description="Todo项列表")

    def add(self, content: str, priority: int = 0, dependencies: list[str] | None = None) -> TodoItem:
        """添加Todo"""
        import uuid
        item = TodoItem(
            id=str(uuid.uuid4()),
            content=content,
            priority=priority,
            dependencies=dependencies or [],
        )
        self.items.append(item)
        return item

    def get(self, id: str) -> TodoItem | None:
        """获取Todo"""
        for item in self.items:
            if item.id == id:
                return item
        return None

    def update_status(self, id: str, status: str) -> bool:
        """更新状态"""
        item = self.get(id)
        if item is None:
            return False
        if status not in ("pending", "in_progress", "completed"):
            return False
        item.status = status
        return True

    def get_pending(self) -> list[TodoItem]:
        """获取所有待处理项"""
        return [i for i in self.items if i.status == "pending"]

    def get_next_ready(self) -> TodoItem | None:
        """获取下一个可执行的Todo (依赖都已完成)"""
        completed_ids = {i.id for i in self.items if i.status == "completed"}
        for item in self.get_pending():
            if all(d in completed_ids for d in item.dependencies):
                return item
        return None


class PlanningTool:
    """
    规划工具 - 提供任务规划能力

    核心功能:
    1. 任务分解
    2. 依赖管理
    3. 进度追踪
    4. 优先级排序
    """

    def __init__(self) -> None:
        self._todo_lists: dict[str, TodoList] = {}

    def create_plan(self, plan_id: str) -> TodoList:
        """创建新的规划"""
        todo = TodoList()
        self._todo_lists[plan_id] = todo
        return todo

    def get_plan(self, plan_id: str) -> TodoList | None:
        """获取规划"""
        return self._todo_lists.get(plan_id)

    def decompose_task(self, task: str, plan_id: str) -> TodoList:
        """
        分解任务为多个Todo

        TODO: 实现智能任务分解
        """
        plan = self.create_plan(plan_id)
        # 简化实现：将任务拆分为步骤
        steps = ["分析任务", "收集信息", "执行操作", "验证结果", "完成"]
        for i, step in enumerate(steps):
            plan.add(content=f"{step}: {task}", priority=i)
        return plan

    def get_progress(self, plan_id: str) -> dict[str, Any]:
        """获取进度统计"""
        plan = self.get_plan(plan_id)
        if plan is None:
            return {}

        total = len(plan.items)
        completed = len([i for i in plan.items if i.status == "completed"])
        in_progress = len([i for i in plan.items if i.status == "in_progress"])
        pending = len([i for i in plan.items if i.status == "pending"])

        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "progress_percent": (completed / total * 100) if total > 0 else 0,
        }