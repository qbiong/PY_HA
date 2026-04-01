"""
Task Kernel - 任务内核

类似操作系统内核:
- 任务注册与管理
- 生命周期控制
- 依赖解析
- 闭环验证
- 资源回收
"""

from typing import Any
from pydantic import BaseModel, Field
import time

from py_ha.kernel.task import Task, TaskStatus, TaskPriority, TaskResult, TaskDependencyGraph
from py_ha.kernel.queue import TaskQueue


class KernelStats(BaseModel):
    """内核统计"""

    total_tasks_created: int = Field(default=0, description="总创建任务数")
    total_tasks_completed: int = Field(default=0, description="总完成任务数")
    total_tasks_failed: int = Field(default=0, description="总失败任务数")
    total_tasks_cancelled: int = Field(default=0, description="总取消任务数")
    active_tasks: int = Field(default=0, description="活跃任务数")
    avg_wait_time: float = Field(default=0.0, description="平均等待时间")
    avg_execution_time: float = Field(default=0.0, description="平均执行时间")


class TaskEvent(BaseModel):
    """任务事件"""

    event_id: str = Field(..., description="事件ID")
    task_id: str = Field(..., description="任务ID")
    event_type: str = Field(..., description="事件类型")
    timestamp: float = Field(default_factory=time.time, description="时间戳")
    details: dict[str, Any] = Field(default_factory=dict, description="详情")


class TaskKernel:
    """
    任务内核 - 类似操作系统内核

    核心职责:
    1. 任务注册: 创建和注册新任务
    2. 生命周期管理: 管理任务从创建到完成的全过程
    3. 依赖解析: 解析和管理任务依赖关系
    4. 闭环验证: 确保任务形成闭环
    5. 事件通知: 发布任务状态变更事件
    6. 资源回收: 清理已完成任务
    """

    def __init__(
        self,
        queue: TaskQueue | None = None,
        enable_event_logging: bool = True,
    ) -> None:
        # 任务队列
        self.queue = queue or TaskQueue()

        # 依赖图
        self.dependency_graph = TaskDependencyGraph()

        # 事件日志
        self._events: list[TaskEvent] = []
        self._enable_event_logging = enable_event_logging

        # 事件回调
        self._callbacks: dict[str, list[Any]] = {}

        # 统计
        self._stats = KernelStats()

        # 闭环追踪
        self._pending_closures: dict[str, dict[str, Any]] = {}

    # ==================== 任务注册 ====================

    def register_task(
        self,
        name: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.NORMAL,
        dependencies: list[str] | None = None,
        required_tools: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        created_by: str | None = None,
    ) -> Task:
        """
        注册新任务 - 类似进程创建

        Args:
            name: 任务名称
            description: 任务描述
            priority: 优先级
            dependencies: 依赖任务ID列表
            required_tools: 所需工具
            metadata: 元数据
            created_by: 创建者ID

        Returns:
            创建的任务
        """
        task = Task(
            name=name,
            description=description,
            priority=priority,
            dependencies=dependencies or [],
            required_tools=required_tools or [],
            metadata=metadata or {},
            created_by=created_by,
        )

        # 添加到队列
        self.queue.enqueue(task)

        # 添加到依赖图
        self.dependency_graph.add_task(task)

        # 更新统计
        self._stats.total_tasks_created += 1
        self._stats.active_tasks += 1

        # 记录事件
        self._emit_event(task.id, "task_created", {"name": name, "priority": priority.value})

        return task

    def register_task_object(self, task: Task) -> bool:
        """
        注册任务对象

        Args:
            task: 任务对象

        Returns:
            是否成功注册
        """
        if not self.queue.enqueue(task):
            return False

        self.dependency_graph.add_task(task)
        self._stats.total_tasks_created += 1
        self._stats.active_tasks += 1
        self._emit_event(task.id, "task_created", {"name": task.name})
        return True

    # ==================== 生命周期管理 ====================

    def start_task(self, task_id: str, assigned_to: str | None = None) -> bool:
        """
        开始任务 - 状态: READY → RUNNING

        Args:
            task_id: 任务ID
            assigned_to: 分配给的消费者ID

        Returns:
            是否成功开始
        """
        task = self.queue.get_task(task_id)
        if task is None:
            return False

        # 检查依赖
        if not self.dependency_graph.check_dependencies_met(task_id):
            return False

        # 更新状态
        task.assigned_to = assigned_to
        if not self.queue.update_task_status(task_id, TaskStatus.RUNNING, "Task started"):
            return False

        # 记录闭环追踪
        self._pending_closures[task_id] = {
            "started_at": time.time(),
            "assigned_to": assigned_to,
        }

        self._emit_event(task_id, "task_started", {"assigned_to": assigned_to})
        return True

    def complete_task(self, task_id: str, result: TaskResult) -> bool:
        """
        完成任务 - 状态: RUNNING → DONE

        Args:
            task_id: 任务ID
            result: 执行结果

        Returns:
            是否成功完成
        """
        task = self.queue.get_task(task_id)
        if task is None:
            return False

        task.set_result(result)

        if not self.queue.update_task_status(task_id, TaskStatus.DONE, "Task completed"):
            return False

        # 更新统计
        self._stats.total_tasks_completed += 1
        self._stats.active_tasks -= 1
        self._update_time_stats(task)

        # 闭环验证
        self._verify_closure(task_id, success=True)

        # 解锁依赖此任务的任务
        self._unlock_dependents(task_id)

        self._emit_event(task_id, "task_completed", {"success": result.success})
        return True

    def fail_task(self, task_id: str, error: str, can_retry: bool = True) -> bool:
        """
        失败任务 - 状态: RUNNING → FAILED

        Args:
            task_id: 任务ID
            error: 错误信息
            can_retry: 是否可以重试

        Returns:
            是否成功标记失败
        """
        task = self.queue.get_task(task_id)
        if task is None:
            return False

        task.result = TaskResult(success=False, error=error)

        # 先转换到 FAILED 状态
        if not self.queue.update_task_status(task_id, TaskStatus.FAILED, error):
            return False

        # 检查是否可以重试
        if can_retry and task.retry_count < task.max_retries:
            # 重试：FAILED → READY
            task.retry_count += 1
            self.queue.update_task_status(task_id, TaskStatus.READY, f"Retry {task.retry_count}")
            self._emit_event(task_id, "task_retry", {"retry_count": task.retry_count})
        else:
            # 最终失败
            self._stats.total_tasks_failed += 1
            self._stats.active_tasks -= 1

            # 闭环验证
            self._verify_closure(task_id, success=False)

            self._emit_event(task_id, "task_failed", {"error": error})

        return True

    def block_task(self, task_id: str, reason: str = "") -> bool:
        """
        阻塞任务 - 状态: RUNNING → BLOCKED

        Args:
            task_id: 任务ID
            reason: 阻塞原因

        Returns:
            是否成功阻塞
        """
        if not self.queue.update_task_status(task_id, TaskStatus.BLOCKED, reason):
            return False

        self._emit_event(task_id, "task_blocked", {"reason": reason})
        return True

    def unblock_task(self, task_id: str) -> bool:
        """
        解除阻塞 - 状态: BLOCKED → READY

        Args:
            task_id: 任务ID

        Returns:
            是否成功解除
        """
        if not self.queue.update_task_status(task_id, TaskStatus.READY, "Unblocked"):
            return False

        self._emit_event(task_id, "task_unblocked", {})
        return True

    def cancel_task(self, task_id: str, reason: str = "Cancelled") -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID
            reason: 取消原因

        Returns:
            是否成功取消
        """
        task = self.queue.get_task(task_id)
        if task is None or task.is_terminal():
            return False

        if not self.queue.update_task_status(task_id, TaskStatus.CANCELLED, reason):
            return False

        self._stats.total_tasks_cancelled += 1
        self._stats.active_tasks -= 1

        # 闭环验证
        self._verify_closure(task_id, success=False)

        self._emit_event(task_id, "task_cancelled", {"reason": reason})
        return True

    # ==================== 依赖管理 ====================

    def add_dependency(self, task_id: str, depends_on: str) -> bool:
        """
        添加任务依赖

        Args:
            task_id: 任务ID
            depends_on: 依赖的任务ID

        Returns:
            是否成功添加
        """
        task = self.queue.get_task(task_id)
        dep_task = self.queue.get_task(depends_on)

        if task is None or dep_task is None:
            return False

        # 检查循环依赖
        if self._would_create_cycle(task_id, depends_on):
            return False

        task.add_dependency(depends_on)
        dep_task.add_dependent(task_id)

        self.dependency_graph.add_task(task)
        self.dependency_graph.add_task(dep_task)

        self._emit_event(task_id, "dependency_added", {"depends_on": depends_on})
        return True

    def _would_create_cycle(self, task_id: str, depends_on: str) -> bool:
        """检查是否会产生循环依赖"""
        # 如果 depends_on 已经依赖 task_id，则会形成循环
        visited = set()
        queue = [depends_on]

        while queue:
            current = queue.pop(0)
            if current == task_id:
                return True
            if current in visited:
                continue
            visited.add(current)

            task = self.queue.get_task(current)
            if task:
                queue.extend(task.dependencies)

        return False

    def _unlock_dependents(self, task_id: str) -> None:
        """解锁依赖此任务的任务"""
        dependents = self.dependency_graph.get_dependents(task_id)
        for dep_task in dependents:
            if dep_task.status == TaskStatus.BLOCKED:
                # 检查是否所有依赖都已完成
                if self.dependency_graph.check_dependencies_met(dep_task.id):
                    self.unblock_task(dep_task.id)

    # ==================== 闭环管理 ====================

    def _verify_closure(self, task_id: str, success: bool) -> dict[str, Any]:
        """
        验证任务闭环

        Args:
            task_id: 任务ID
            success: 是否成功

        Returns:
            闭环验证结果
        """
        task = self.queue.get_task(task_id)
        if task is None:
            return {"valid": False, "error": "Task not found"}

        closure_info = self._pending_closures.pop(task_id, {})

        result = {
            "valid": True,
            "task_id": task_id,
            "success": success,
            "created_at": task.created_at,
            "started_at": task.started_at,
            "ended_at": task.ended_at,
            "total_time": task.get_execution_time(),
            "wait_time": task.get_wait_time(),
            "retry_count": task.retry_count,
            "closure_info": closure_info,
        }

        # 触发闭环回调
        self._trigger_callbacks("task_closure", result)

        return result

    def verify_all_closures(self) -> dict[str, Any]:
        """
        验证所有任务闭环

        Returns:
            所有未闭环任务列表
        """
        unclosed = []
        for task_id, info in self._pending_closures.items():
            task = self.queue.get_task(task_id)
            if task and not task.is_terminal():
                unclosed.append({
                    "task_id": task_id,
                    "status": task.status.value,
                    "started_at": info.get("started_at"),
                    "elapsed": time.time() - info.get("started_at", time.time()),
                })

        return {
            "all_closed": len(unclosed) == 0,
            "unclosed_count": len(unclosed),
            "unclosed_tasks": unclosed,
        }

    # ==================== 事件系统 ====================

    def _emit_event(self, task_id: str, event_type: str, details: dict[str, Any]) -> None:
        """发送事件"""
        import uuid
        event = TaskEvent(
            event_id=str(uuid.uuid4()),
            task_id=task_id,
            event_type=event_type,
            details=details,
        )

        if self._enable_event_logging:
            self._events.append(event)

        # 触发回调
        self._trigger_callbacks(event_type, event.model_dump())

    def register_callback(self, event_type: str, callback: Any) -> None:
        """注册事件回调"""
        if event_type not in self._callbacks:
            self._callbacks[event_type] = []
        self._callbacks[event_type].append(callback)

    def _trigger_callbacks(self, event_type: str, data: Any) -> None:
        """触发回调"""
        for callback in self._callbacks.get(event_type, []):
            try:
                callback(data)
            except Exception:
                pass  # 忽略回调错误

    def get_events(self, task_id: str | None = None) -> list[TaskEvent]:
        """获取事件列表"""
        if task_id:
            return [e for e in self._events if e.task_id == task_id]
        return self._events.copy()

    # ==================== 统计与监控 ====================

    def _update_time_stats(self, task: Task) -> None:
        """更新时间统计"""
        # 简化实现：更新平均值
        wait_time = task.get_wait_time()
        exec_time = task.get_execution_time()

        if self._stats.total_tasks_completed > 0:
            n = self._stats.total_tasks_completed
            self._stats.avg_wait_time = (self._stats.avg_wait_time * (n - 1) + wait_time) / n
            self._stats.avg_execution_time = (self._stats.avg_execution_time * (n - 1) + exec_time) / n

    def get_stats(self) -> KernelStats:
        """获取统计信息"""
        self._stats.active_tasks = self.queue.size()
        return self._stats

    def get_health_report(self) -> dict[str, Any]:
        """获取健康报告"""
        stats = self.get_stats()
        queue_stats = self.queue.get_stats()

        # 计算健康状态
        failure_rate = 0.0
        if stats.total_tasks_created > 0:
            failure_rate = stats.total_tasks_failed / stats.total_tasks_created

        if failure_rate > 0.3:
            status = "critical"
        elif failure_rate > 0.1:
            status = "warning"
        else:
            status = "healthy"

        return {
            "status": status,
            "failure_rate": failure_rate,
            "stats": stats.model_dump(),
            "queue": queue_stats.model_dump(),
            "closure_verification": self.verify_all_closures(),
        }

    # ==================== 资源回收 ====================

    def cleanup_completed(self, max_age: float = 3600) -> int:
        """
        清理已完成任务

        Args:
            max_age: 最大保留时间 (秒)

        Returns:
            清理的任务数量
        """
        count = 0
        current_time = time.time()

        for status in [TaskStatus.DONE, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            tasks = self.queue._queues[status]
            to_remove = []

            for task_id, task in tasks.items():
                if task.ended_at and (current_time - task.ended_at) > max_age:
                    to_remove.append(task_id)

            for task_id in to_remove:
                tasks.pop(task_id, None)
                self.queue._task_index.pop(task_id, None)
                self.dependency_graph.remove_task(task_id)
                count += 1

        return count