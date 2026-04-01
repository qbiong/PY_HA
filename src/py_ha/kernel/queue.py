"""
Task Queue - 任务队列

类似操作系统的进程队列:
- 就绪队列 (Ready Queue)
- 执行队列 (Running Queue)
- 阻塞队列 (Blocked Queue)
- 完成队列 (Done Queue)
- 失败队列 (Failed Queue)
"""

from typing import Any
from pydantic import BaseModel, Field
from collections import defaultdict
import time

from py_ha.kernel.task import Task, TaskStatus, TaskPriority


class QueueStats(BaseModel):
    """队列统计信息"""

    ready_count: int = Field(default=0, description="就绪队列长度")
    running_count: int = Field(default=0, description="执行队列长度")
    blocked_count: int = Field(default=0, description="阻塞队列长度")
    done_count: int = Field(default=0, description="完成队列长度")
    failed_count: int = Field(default=0, description="失败队列长度")
    total_processed: int = Field(default=0, description="总处理数")


class TaskQueue:
    """
    任务队列 - 类似操作系统的进程队列

    管理所有任务的状态和调度:
    - 按状态分区
    - 按优先级排序
    - 支持快速查找
    """

    def __init__(self, max_size: int = 10000) -> None:
        self.max_size = max_size

        # 按状态分区的队列
        self._queues: dict[TaskStatus, dict[str, Task]] = {
            TaskStatus.CREATED: {},
            TaskStatus.READY: {},
            TaskStatus.RUNNING: {},
            TaskStatus.BLOCKED: {},
            TaskStatus.DONE: {},
            TaskStatus.FAILED: {},
            TaskStatus.CANCELLED: {},
        }

        # 按优先级的就绪队列 (用于快速调度)
        self._priority_ready: dict[TaskPriority, list[str]] = {
            TaskPriority.CRITICAL: [],
            TaskPriority.HIGH: [],
            TaskPriority.NORMAL: [],
            TaskPriority.LOW: [],
            TaskPriority.BACKGROUND: [],
        }

        # 索引
        self._task_index: dict[str, TaskStatus] = {}

        # 统计
        self._stats = QueueStats()
        self._total_processed = 0

    def enqueue(self, task: Task) -> bool:
        """
        任务入队 - 类似进程入队

        Args:
            task: 任务

        Returns:
            是否成功入队
        """
        if len(self._task_index) >= self.max_size:
            return False

        status = task.status

        # 添加到状态队列
        self._queues[status][task.id] = task
        self._task_index[task.id] = status

        # 如果是就绪状态，添加到优先级队列
        if status == TaskStatus.READY:
            self._priority_ready[task.priority].append(task.id)

        self._update_stats()
        return True

    def dequeue(self, status: TaskStatus = TaskStatus.READY) -> Task | None:
        """
        任务出队 - 类似进程出队

        Args:
            status: 从哪个队列出队

        Returns:
            出队的任务
        """
        queue = self._queues[status]
        if not queue:
            return None

        # 获取第一个任务
        task_id = next(iter(queue))
        task = queue.pop(task_id)

        # 从索引移除
        self._task_index.pop(task_id, None)

        # 从优先级队列移除
        if status == TaskStatus.READY:
            self._remove_from_priority_queue(task_id, task.priority)

        self._update_stats()
        return task

    def dequeue_by_priority(self) -> Task | None:
        """
        按优先级出队 - 最高优先级任务优先

        类似操作系统的优先级调度

        Returns:
            最高优先级的就绪任务
        """
        # 按优先级顺序检查
        for priority in [
            TaskPriority.CRITICAL,
            TaskPriority.HIGH,
            TaskPriority.NORMAL,
            TaskPriority.LOW,
            TaskPriority.BACKGROUND,
        ]:
            if self._priority_ready[priority]:
                task_id = self._priority_ready[priority].pop(0)  # 从列表中弹出
                task = self._queues[TaskStatus.READY].pop(task_id, None)
                if task:
                    self._task_index.pop(task_id, None)
                    self._update_stats()
                    return task

        return None

    def get_task(self, task_id: str) -> Task | None:
        """获取任务"""
        status = self._task_index.get(task_id)
        if status is None:
            return None
        return self._queues[status].get(task_id)

    def update_task_status(
        self,
        task_id: str,
        new_status: TaskStatus,
        reason: str = "",
    ) -> bool:
        """
        更新任务状态 - 类似进程状态切换

        Args:
            task_id: 任务ID
            new_status: 新状态
            reason: 原因

        Returns:
            是否成功更新
        """
        task = self.get_task(task_id)
        if task is None:
            return False

        old_status = task.status

        # 执行状态转换
        if not task.transition_to(new_status, reason):
            return False

        # 移动任务到新队列
        self._queues[old_status].pop(task_id, None)
        self._queues[new_status][task_id] = task
        self._task_index[task_id] = new_status

        # 更新优先级队列
        if old_status == TaskStatus.READY:
            self._remove_from_priority_queue(task_id, task.priority)
        if new_status == TaskStatus.READY:
            self._priority_ready[task.priority].append(task_id)

        # 更新统计
        if new_status in (TaskStatus.DONE, TaskStatus.FAILED):
            self._total_processed += 1

        self._update_stats()
        return True

    def _remove_from_priority_queue(self, task_id: str, priority: TaskPriority) -> None:
        """从优先级队列移除"""
        try:
            self._priority_ready[priority].remove(task_id)
        except ValueError:
            pass

    def get_ready_tasks(self) -> list[Task]:
        """获取所有就绪任务"""
        return list(self._queues[TaskStatus.READY].values())

    def get_running_tasks(self) -> list[Task]:
        """获取所有执行中任务"""
        return list(self._queues[TaskStatus.RUNNING].values())

    def get_blocked_tasks(self) -> list[Task]:
        """获取所有阻塞任务"""
        return list(self._queues[TaskStatus.BLOCKED].values())

    def get_failed_tasks(self) -> list[Task]:
        """获取所有失败任务"""
        return list(self._queues[TaskStatus.FAILED].values())

    def get_done_tasks(self) -> list[Task]:
        """获取所有完成任务"""
        return list(self._queues[TaskStatus.DONE].values())

    def requeue_failed(self, task_id: str) -> bool:
        """
        重试失败任务 - 重新加入就绪队列

        Args:
            task_id: 任务ID

        Returns:
            是否成功重试
        """
        task = self.get_task(task_id)
        if task is None or task.status != TaskStatus.FAILED:
            return False

        if not task.can_retry():
            return False

        task.retry_count += 1
        return self.update_task_status(task_id, TaskStatus.READY, "Retry")

    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功取消
        """
        task = self.get_task(task_id)
        if task is None or task.is_terminal():
            return False

        return self.update_task_status(task_id, TaskStatus.CANCELLED, "Cancelled by user")

    def clear_completed(self) -> int:
        """
        清除已完成/失败/取消的任务

        Returns:
            清除的任务数量
        """
        count = 0
        for status in [TaskStatus.DONE, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            count += len(self._queues[status])
            for task_id in list(self._queues[status].keys()):
                self._task_index.pop(task_id, None)
            self._queues[status].clear()

        self._update_stats()
        return count

    def size(self) -> int:
        """队列总大小"""
        return len(self._task_index)

    def is_empty(self) -> bool:
        """队列是否为空"""
        return len(self._task_index) == 0

    def is_full(self) -> bool:
        """队列是否已满"""
        return len(self._task_index) >= self.max_size

    def _update_stats(self) -> None:
        """更新统计信息"""
        self._stats.ready_count = len(self._queues[TaskStatus.READY])
        self._stats.running_count = len(self._queues[TaskStatus.RUNNING])
        self._stats.blocked_count = len(self._queues[TaskStatus.BLOCKED])
        self._stats.done_count = len(self._queues[TaskStatus.DONE])
        self._stats.failed_count = len(self._queues[TaskStatus.FAILED])
        self._stats.total_processed = self._total_processed

    def get_stats(self) -> QueueStats:
        """获取统计信息"""
        return self._stats

    def get_status_distribution(self) -> dict[str, int]:
        """获取状态分布"""
        return {
            "created": len(self._queues[TaskStatus.CREATED]),
            "ready": len(self._queues[TaskStatus.READY]),
            "running": len(self._queues[TaskStatus.RUNNING]),
            "blocked": len(self._queues[TaskStatus.BLOCKED]),
            "done": len(self._queues[TaskStatus.DONE]),
            "failed": len(self._queues[TaskStatus.FAILED]),
            "cancelled": len(self._queues[TaskStatus.CANCELLED]),
        }

    def get_priority_distribution(self) -> dict[str, int]:
        """获取优先级分布 (就绪队列)"""
        return {
            "critical": len(self._priority_ready[TaskPriority.CRITICAL]),
            "high": len(self._priority_ready[TaskPriority.HIGH]),
            "normal": len(self._priority_ready[TaskPriority.NORMAL]),
            "low": len(self._priority_ready[TaskPriority.LOW]),
            "background": len(self._priority_ready[TaskPriority.BACKGROUND]),
        }