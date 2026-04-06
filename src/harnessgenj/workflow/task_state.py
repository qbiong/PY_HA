"""
Task State Machine - 任务状态机

实现任务状态流转管理：
1. 状态转换验证
2. 状态变更事件记录
3. 状态变更钩子触发
4. 状态历史追踪

状态流转图：
    pending → in_progress → reviewing → completed
        ↓          ↓            ↓
    cancelled   failed ←──────┘
                    ↓
                in_progress (retry)

使用示例:
    from harnessgenj.workflow.task_state import TaskStateMachine, TaskState

    machine = TaskStateMachine()

    # 创建任务
    machine.create_task("TASK-001", {"description": "实现登录功能"})

    # 状态转换
    machine.transition("TASK-001", TaskState.IN_PROGRESS, "开始开发")
    machine.transition("TASK-001", TaskState.REVIEWING, "提交审查")
    machine.transition("TASK-001", TaskState.COMPLETED, "审查通过")
"""

from typing import Any, Callable
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
import time
import threading


class TaskState(str, Enum):
    """任务状态"""

    PENDING = "pending"           # 待处理
    IN_PROGRESS = "in_progress"   # 进行中
    REVIEWING = "reviewing"       # 审查中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"             # 失败
    CANCELLED = "cancelled"       # 已取消


class StateChangeEvent(BaseModel):
    """状态变更事件"""

    task_id: str
    from_state: TaskState
    to_state: TaskState
    reason: str = ""
    timestamp: float = Field(default_factory=time.time)
    operator: str = "system"
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskInfo(BaseModel):
    """任务状态信息（仅存储状态流转数据，任务详情由 MemoryManager 管理）"""

    task_id: str
    state: TaskState = TaskState.PENDING
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    state_history: list[StateChangeEvent] = Field(default_factory=list)

    def add_event(self, event: StateChangeEvent) -> None:
        """添加状态变更事件"""
        self.state_history.append(event)
        self.updated_at = time.time()


class InvalidTransitionError(Exception):
    """无效状态转换错误"""

    def __init__(self, task_id: str, from_state: TaskState, to_state: TaskState, allowed: list[TaskState]):
        self.task_id = task_id
        self.from_state = from_state
        self.to_state = to_state
        self.allowed = allowed
        super().__init__(
            f"Invalid transition for task {task_id}: "
            f"cannot go from {from_state.value} to {to_state.value}. "
            f"Allowed: {[s.value for s in allowed]}"
        )


class TaskStateMachine:
    """
    任务状态机

    管理任务的生命周期状态转换：
    - 验证状态转换合法性
    - 记录状态变更历史
    - 触发状态变更钩子
    - 提供状态查询接口

    设计原则：
    1. 严格的状态转换验证
    2. 完整的审计追踪
    3. 灵活的钩子系统
    4. 线程安全
    """

    # 状态转换矩阵：定义每个状态可以转换到哪些状态
    TRANSITIONS: dict[TaskState, list[TaskState]] = {
        TaskState.PENDING: [
            TaskState.IN_PROGRESS,
            TaskState.CANCELLED,
        ],
        TaskState.IN_PROGRESS: [
            TaskState.REVIEWING,
            TaskState.FAILED,
            TaskState.CANCELLED,
        ],
        TaskState.REVIEWING: [
            TaskState.COMPLETED,
            TaskState.IN_PROGRESS,  # 需要修改后重新审查
            TaskState.FAILED,
        ],
        TaskState.COMPLETED: [],  # 终态，不可转换
        TaskState.FAILED: [
            TaskState.IN_PROGRESS,  # 重试
            TaskState.CANCELLED,
        ],
        TaskState.CANCELLED: [],  # 终态，不可转换
    }

    def __init__(self) -> None:
        """初始化状态机"""
        self._tasks: dict[str, TaskInfo] = {}
        self._lock = threading.RLock()

        # 状态变更钩子
        self._on_state_change_hooks: dict[str, list[Callable[[StateChangeEvent], None]]] = {
            "on_enter_pending": [],
            "on_enter_in_progress": [],
            "on_enter_reviewing": [],
            "on_enter_completed": [],
            "on_enter_failed": [],
            "on_enter_cancelled": [],
            "on_any_change": [],
        }

        # 统计
        self._stats = {
            "total_tasks": 0,
            "by_state": {state.value: 0 for state in TaskState},
            "total_transitions": 0,
        }

    # ==================== 任务管理 ====================

    def create_task(
        self,
        task_id: str,
    ) -> TaskInfo:
        """
        创建任务状态记录

        注意：此方法仅创建状态记录，任务详情（metadata、description）由 MemoryManager 管理。

        Args:
            task_id: 任务ID

        Returns:
            创建的任务状态信息
        """
        with self._lock:
            if task_id in self._tasks:
                return self._tasks[task_id]

            task = TaskInfo(
                task_id=task_id,
                state=TaskState.PENDING,
            )

            # 记录创建事件
            event = StateChangeEvent(
                task_id=task_id,
                from_state=TaskState.PENDING,
                to_state=TaskState.PENDING,
                reason="任务创建",
                metadata={"initial": True},
            )
            task.add_event(event)

            self._tasks[task_id] = task

            # 更新统计
            self._stats["total_tasks"] += 1
            self._stats["by_state"][TaskState.PENDING.value] += 1

            # 触发钩子
            self._trigger_hooks("on_enter_pending", event)
            self._trigger_hooks("on_any_change", event)

            return task

    def get_task(self, task_id: str) -> TaskInfo | None:
        """获取任务信息"""
        return self._tasks.get(task_id)

    def get_state(self, task_id: str) -> TaskState | None:
        """获取任务状态"""
        task = self._tasks.get(task_id)
        return task.state if task else None

    def task_exists(self, task_id: str) -> bool:
        """检查任务是否存在"""
        return task_id in self._tasks

    # ==================== 状态转换 ====================

    def transition(
        self,
        task_id: str,
        new_state: TaskState,
        reason: str = "",
        operator: str = "system",
        metadata: dict[str, Any] | None = None,
    ) -> TaskInfo:
        """
        执行状态转换

        Args:
            task_id: 任务ID
            new_state: 目标状态
            reason: 转换原因
            operator: 操作者
            metadata: 元数据

        Returns:
            更新后的任务信息

        Raises:
            KeyError: 任务不存在
            InvalidTransitionError: 无效的状态转换
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                raise KeyError(f"Task not found: {task_id}")

            current_state = task.state

            # 验证转换合法性
            allowed = self.TRANSITIONS.get(current_state, [])
            if new_state not in allowed:
                raise InvalidTransitionError(task_id, current_state, new_state, allowed)

            # 创建状态变更事件
            event = StateChangeEvent(
                task_id=task_id,
                from_state=current_state,
                to_state=new_state,
                reason=reason,
                operator=operator,
                metadata=metadata or {},
            )

            # 更新任务状态
            task.state = new_state
            task.add_event(event)

            # 更新统计
            self._stats["by_state"][current_state.value] -= 1
            self._stats["by_state"][new_state.value] += 1
            self._stats["total_transitions"] += 1

            # 触发钩子
            hook_name = f"on_enter_{new_state.value}"
            self._trigger_hooks(hook_name, event)
            self._trigger_hooks("on_any_change", event)

            return task

    def can_transition(self, task_id: str, new_state: TaskState) -> bool:
        """
        检查是否可以执行状态转换

        Args:
            task_id: 任务ID
            new_state: 目标状态

        Returns:
            是否可以转换
        """
        task = self._tasks.get(task_id)
        if not task:
            return False

        allowed = self.TRANSITIONS.get(task.state, [])
        return new_state in allowed

    def get_allowed_transitions(self, task_id: str) -> list[TaskState]:
        """
        获取允许的转换目标

        Args:
            task_id: 任务ID

        Returns:
            允许转换到的状态列表
        """
        task = self._tasks.get(task_id)
        if not task:
            return []

        return self.TRANSITIONS.get(task.state, []).copy()

    # ==================== 便捷方法 ====================

    def start(self, task_id: str, operator: str = "system") -> TaskInfo:
        """开始任务（pending → in_progress）"""
        return self.transition(task_id, TaskState.IN_PROGRESS, "开始任务", operator)

    def submit_review(self, task_id: str, operator: str = "system") -> TaskInfo:
        """提交审查（in_progress → reviewing）"""
        return self.transition(task_id, TaskState.REVIEWING, "提交审查", operator)

    def complete(self, task_id: str, reason: str = "任务完成", operator: str = "system") -> TaskInfo:
        """完成任务（reviewing → completed）"""
        return self.transition(task_id, TaskState.COMPLETED, reason, operator)

    def reject(self, task_id: str, reason: str = "", operator: str = "system") -> TaskInfo:
        """拒绝任务（reviewing → in_progress，需要修改）"""
        return self.transition(task_id, TaskState.IN_PROGRESS, f"审查未通过: {reason}", operator)

    def fail(self, task_id: str, reason: str = "", operator: str = "system") -> TaskInfo:
        """标记失败（in_progress/reviewing → failed）"""
        return self.transition(task_id, TaskState.FAILED, reason, operator)

    def retry(self, task_id: str, operator: str = "system") -> TaskInfo:
        """重试任务（failed → in_progress）"""
        return self.transition(task_id, TaskState.IN_PROGRESS, "重试任务", operator)

    def cancel(self, task_id: str, reason: str = "", operator: str = "system") -> TaskInfo:
        """取消任务"""
        current_state = self.get_state(task_id)
        if current_state is None:
            raise KeyError(f"Task not found: {task_id}")

        return self.transition(task_id, TaskState.CANCELLED, reason, operator)

    # ==================== 钩子系统 ====================

    def on_enter_state(
        self,
        state: TaskState,
        callback: Callable[[StateChangeEvent], None],
    ) -> None:
        """
        注册状态进入钩子

        Args:
            state: 目标状态
            callback: 回调函数
        """
        hook_name = f"on_enter_{state.value}"
        if hook_name in self._on_state_change_hooks:
            self._on_state_change_hooks[hook_name].append(callback)

    def on_any_change(self, callback: Callable[[StateChangeEvent], None]) -> None:
        """
        注册任意状态变更钩子

        Args:
            callback: 回调函数
        """
        self._on_state_change_hooks["on_any_change"].append(callback)

    def _trigger_hooks(self, hook_name: str, event: StateChangeEvent) -> None:
        """触发钩子"""
        hooks = self._on_state_change_hooks.get(hook_name, [])
        for hook in hooks:
            try:
                hook(event)
            except Exception:
                pass  # 忽略钩子错误

    # ==================== 查询 ====================

    def get_tasks_by_state(self, state: TaskState) -> list[TaskInfo]:
        """按状态获取任务"""
        return [t for t in self._tasks.values() if t.state == state]

    def get_pending_tasks(self) -> list[TaskInfo]:
        """获取待处理任务"""
        return self.get_tasks_by_state(TaskState.PENDING)

    def get_active_tasks(self) -> list[TaskInfo]:
        """获取进行中的任务"""
        return self.get_tasks_by_state(TaskState.IN_PROGRESS)

    def get_reviewing_tasks(self) -> list[TaskInfo]:
        """获取审查中的任务"""
        return self.get_tasks_by_state(TaskState.REVIEWING)

    def get_completed_tasks(self) -> list[TaskInfo]:
        """获取已完成的任务"""
        return self.get_tasks_by_state(TaskState.COMPLETED)

    def get_failed_tasks(self) -> list[TaskInfo]:
        """获取失败的任务"""
        return self.get_tasks_by_state(TaskState.FAILED)

    def get_history(self, task_id: str) -> list[StateChangeEvent]:
        """获取任务状态历史"""
        task = self._tasks.get(task_id)
        return task.state_history if task else []

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            **self._stats,
            "tasks_count": len(self._tasks),
        }

    # ==================== 批量操作 ====================

    def list_all_tasks(self) -> list[TaskInfo]:
        """列出所有任务"""
        return list(self._tasks.values())

    def clear_completed(self, max_age_hours: float = 24) -> int:
        """
        清理已完成的任务

        Args:
            max_age_hours: 最大保留时间（小时）

        Returns:
            清理的任务数量
        """
        with self._lock:
            to_remove = []
            now = time.time()
            max_age_seconds = max_age_hours * 3600

            for task_id, task in self._tasks.items():
                if task.state == TaskState.COMPLETED:
                    if now - task.updated_at > max_age_seconds:
                        to_remove.append(task_id)

            for task_id in to_remove:
                del self._tasks[task_id]
                self._stats["by_state"][TaskState.COMPLETED.value] -= 1

            return len(to_remove)


# ==================== 便捷函数 ====================

def create_task_state_machine() -> TaskStateMachine:
    """创建任务状态机实例"""
    return TaskStateMachine()