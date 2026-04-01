"""
Task - 任务数据模型

类似操作系统中的进程控制块 (PCB):
- 任务ID、状态、优先级
- 资源需求、依赖关系
- 执行时间、结果
"""

from typing import Any
from pydantic import BaseModel, Field
from enum import Enum
import time
import uuid


class TaskStatus(Enum):
    """
    任务状态 - 类似进程状态

    状态转换:
    CREATED → READY → RUNNING → DONE
                    ↓         ↑
                BLOCKED → READY
                    ↓
                FAILED
    """

    CREATED = "created"       # 已创建
    READY = "ready"           # 就绪 (等待调度)
    RUNNING = "running"       # 执行中
    BLOCKED = "blocked"       # 阻塞 (等待资源/依赖)
    DONE = "done"             # 完成
    FAILED = "failed"         # 失败
    CANCELLED = "cancelled"   # 已取消


class TaskPriority(Enum):
    """
    任务优先级 - 类似进程优先级

    调度器根据优先级决定执行顺序
    """

    CRITICAL = 0    # 最高优先级
    HIGH = 1        # 高优先级
    NORMAL = 2      # 普通优先级 (默认)
    LOW = 3         # 低优先级
    BACKGROUND = 4  # 后台任务


class TaskResult(BaseModel):
    """
    任务执行结果
    """

    success: bool = Field(..., description="是否成功")
    output: Any = Field(default=None, description="输出结果")
    error: str | None = Field(default=None, description="错误信息")
    execution_time: float = Field(default=0.0, description="执行时间")
    memory_used: int = Field(default=0, description="内存使用")
    metadata: dict[str, Any] = Field(default_factory=dict, description="元数据")


class Task(BaseModel):
    """
    任务 - 类似操作系统的进程控制块 (PCB)

    包含任务的所有信息:
    - 基本属性: ID, 名称, 描述
    - 状态管理: 当前状态, 状态历史
    - 优先级: 调度优先级
    - 资源需求: 需要的工具、知识
    - 依赖关系: 前置任务
    - 执行信息: 创建时间、开始时间、结束时间
    - 结果: 执行结果
    """

    # 基本属性
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="任务ID")
    name: str = Field(..., description="任务名称")
    description: str = Field(default="", description="任务描述")
    type: str = Field(default="general", description="任务类型")

    # 状态管理
    status: TaskStatus = Field(default=TaskStatus.CREATED, description="当前状态")
    status_history: list[dict[str, Any]] = Field(default_factory=list, description="状态历史")

    # 优先级
    priority: TaskPriority = Field(default=TaskPriority.NORMAL, description="优先级")

    # 资源需求
    required_tools: list[str] = Field(default_factory=list, description="所需工具")
    required_knowledge: list[str] = Field(default_factory=list, description="所需知识")
    estimated_time: float = Field(default=0.0, description="预估时间")
    max_retries: int = Field(default=3, description="最大重试次数")

    # 依赖关系
    dependencies: list[str] = Field(default_factory=list, description="依赖任务ID列表")
    dependents: list[str] = Field(default_factory=list, description="依赖此任务的任务ID列表")

    # 执行信息
    created_at: float = Field(default_factory=time.time, description="创建时间")
    started_at: float | None = Field(default=None, description="开始时间")
    ended_at: float | None = Field(default=None, description="结束时间")
    created_by: str | None = Field(default=None, description="创建者 (Producer ID)")
    assigned_to: str | None = Field(default=None, description="分配给 (Consumer ID)")

    # 重试计数
    retry_count: int = Field(default=0, description="重试次数")

    # 结果
    result: TaskResult | None = Field(default=None, description="执行结果")

    # 元数据
    metadata: dict[str, Any] = Field(default_factory=dict, description="元数据")

    def transition_to(self, new_status: TaskStatus, reason: str = "") -> bool:
        """
        状态转换 - 类似进程状态切换

        Args:
            new_status: 新状态
            reason: 转换原因

        Returns:
            是否转换成功
        """
        # 定义合法的状态转换
        valid_transitions = {
            TaskStatus.CREATED: [TaskStatus.READY, TaskStatus.CANCELLED],
            TaskStatus.READY: [TaskStatus.RUNNING, TaskStatus.CANCELLED],
            TaskStatus.RUNNING: [TaskStatus.DONE, TaskStatus.FAILED, TaskStatus.BLOCKED],
            TaskStatus.BLOCKED: [TaskStatus.READY, TaskStatus.FAILED, TaskStatus.CANCELLED],
            TaskStatus.FAILED: [TaskStatus.READY, TaskStatus.DONE],  # 重试或放弃
            TaskStatus.DONE: [],  # 终态
            TaskStatus.CANCELLED: [],  # 终态
        }

        if new_status not in valid_transitions.get(self.status, []):
            return False

        # 记录状态历史
        self.status_history.append({
            "from": self.status.value,
            "to": new_status.value,
            "reason": reason,
            "timestamp": time.time(),
        })

        self.status = new_status

        # 更新时间戳
        if new_status == TaskStatus.RUNNING:
            self.started_at = time.time()
        elif new_status in (TaskStatus.DONE, TaskStatus.FAILED, TaskStatus.CANCELLED):
            self.ended_at = time.time()

        return True

    def is_terminal(self) -> bool:
        """是否处于终态"""
        return self.status in (TaskStatus.DONE, TaskStatus.FAILED, TaskStatus.CANCELLED)

    def is_ready_to_run(self) -> bool:
        """是否可以运行 (状态为READY)"""
        return self.status == TaskStatus.READY

    def can_retry(self) -> bool:
        """
        是否可以重试

        检查条件:
        1. 任务处于失败或执行中状态 (正在失败)
        2. 重试次数未达上限
        """
        if self.retry_count >= self.max_retries:
            return False
        # 允许在 FAILED 或 RUNNING 状态时检查重试
        return self.status in (TaskStatus.FAILED, TaskStatus.RUNNING)

    def get_execution_time(self) -> float:
        """获取执行时间"""
        if self.started_at is None:
            return 0.0
        if self.ended_at is None:
            return time.time() - self.started_at
        return self.ended_at - self.started_at

    def get_wait_time(self) -> float:
        """获取等待时间 (从创建到开始执行)"""
        if self.started_at is None:
            return time.time() - self.created_at
        return self.started_at - self.created_at

    def set_result(self, result: TaskResult) -> None:
        """设置执行结果"""
        self.result = result

    def add_dependency(self, task_id: str) -> None:
        """添加依赖任务"""
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)

    def add_dependent(self, task_id: str) -> None:
        """添加依赖此任务的任务"""
        if task_id not in self.dependents:
            self.dependents.append(task_id)


class TaskDependencyGraph:
    """
    任务依赖图 - 管理任务之间的依赖关系

    类似操作系统的进程依赖管理
    """

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}

    def add_task(self, task: Task) -> None:
        """添加任务到图中"""
        self._tasks[task.id] = task

    def remove_task(self, task_id: str) -> None:
        """从图中移除任务"""
        self._tasks.pop(task_id, None)

    def get_task(self, task_id: str) -> Task | None:
        """获取任务"""
        return self._tasks.get(task_id)

    def check_dependencies_met(self, task_id: str) -> bool:
        """
        检查任务依赖是否满足

        Args:
            task_id: 任务ID

        Returns:
            所有依赖是否都已完成
        """
        task = self.get_task(task_id)
        if task is None:
            return False

        for dep_id in task.dependencies:
            dep_task = self.get_task(dep_id)
            if dep_task is None or dep_task.status != TaskStatus.DONE:
                return False

        return True

    def get_ready_tasks(self) -> list[Task]:
        """
        获取所有就绪任务 (依赖已满足，状态为READY)

        Returns:
            就绪任务列表
        """
        ready = []
        for task in self._tasks.values():
            if task.status == TaskStatus.READY and self.check_dependencies_met(task.id):
                ready.append(task)
        return ready

    def get_dependents(self, task_id: str) -> list[Task]:
        """获取依赖指定任务的所有任务"""
        task = self.get_task(task_id)
        if task is None:
            return []
        return [self._tasks[tid] for tid in task.dependents if tid in self._tasks]

    def topological_sort(self) -> list[str]:
        """
        拓扑排序 - 获取任务的执行顺序

        Returns:
            排序后的任务ID列表
        """
        # Kahn's algorithm
        in_degree = {tid: 0 for tid in self._tasks}
        for task in self._tasks.values():
            for dep_id in task.dependencies:
                if dep_id in in_degree:
                    in_degree[task.id] += 1

        # 找入度为0的节点
        queue = [tid for tid, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            task = self._tasks[current]
            for dependent_id in task.dependents:
                if dependent_id in in_degree:
                    in_degree[dependent_id] -= 1
                    if in_degree[dependent_id] == 0:
                        queue.append(dependent_id)

        return result