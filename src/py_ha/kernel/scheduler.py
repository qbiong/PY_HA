"""
Scheduler - 任务调度器

类似操作系统进程调度器:
- 任务调度算法
- 资源分配
- 负载均衡
- 优先级管理
"""

from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel, Field
from enum import Enum
import time

from py_ha.kernel.task import Task, TaskStatus, TaskPriority
from py_ha.kernel.queue import TaskQueue
from py_ha.kernel.kernel import TaskKernel


class SchedulingAlgorithm(Enum):
    """
    调度算法 - 类似操作系统调度算法

    - FIFO: 先进先出 (First In First Out)
    - PRIORITY: 优先级调度
    - ROUND_ROBIN: 时间片轮转
    - FAIR: 公平调度
    - SHORTEST_JOB_FIRST: 最短作业优先
    """

    FIFO = "fifo"
    PRIORITY = "priority"
    ROUND_ROBIN = "round_robin"
    FAIR = "fair"
    SHORTEST_JOB_FIRST = "sjf"


class SchedulerStats(BaseModel):
    """调度器统计"""

    total_scheduled: int = Field(default=0, description="总调度次数")
    total_preemptions: int = Field(default=0, description="总抢占次数")
    avg_wait_time: float = Field(default=0.0, description="平均等待时间")
    avg_turnaround_time: float = Field(default=0.0, description="平均周转时间")
    cpu_utilization: float = Field(default=0.0, description="CPU利用率")


class BaseScheduler(ABC):
    """
    调度器基类 - 定义调度接口
    """

    @abstractmethod
    def select_next(self, queue: TaskQueue) -> Task | None:
        """
        选择下一个执行的任务

        Args:
            queue: 任务队列

        Returns:
            选中的任务
        """
        pass

    @abstractmethod
    def should_preempt(self, current_task: Task, queue: TaskQueue) -> bool:
        """
        是否应该抢占当前任务

        Args:
            current_task: 当前执行的任务
            queue: 任务队列

        Returns:
            是否抢占
        """
        pass


class FIFOScheduler(BaseScheduler):
    """
    FIFO调度器 - 先进先出

    最简单的调度算法，按任务到达顺序执行
    """

    def select_next(self, queue: TaskQueue) -> Task | None:
        return queue.dequeue(TaskStatus.READY)

    def should_preempt(self, current_task: Task, queue: TaskQueue) -> bool:
        return False  # FIFO不支持抢占


class PriorityScheduler(BaseScheduler):
    """
    优先级调度器 - 按优先级调度

    高优先级任务优先执行，支持抢占
    """

    def __init__(self, preemptive: bool = True) -> None:
        self.preemptive = preemptive

    def select_next(self, queue: TaskQueue) -> Task | None:
        return queue.dequeue_by_priority()

    def should_preempt(self, current_task: Task, queue: TaskQueue) -> bool:
        if not self.preemptive:
            return False

        # 检查是否有更高优先级任务
        for priority in [TaskPriority.CRITICAL, TaskPriority.HIGH]:
            if priority.value < current_task.priority.value:
                if queue._priority_ready[priority]:
                    return True

        return False


class RoundRobinScheduler(BaseScheduler):
    """
    时间片轮转调度器

    每个任务执行一个时间片后切换
    """

    def __init__(self, time_slice: float = 1.0) -> None:
        self.time_slice = time_slice
        self._current_task_start: float = 0

    def select_next(self, queue: TaskQueue) -> Task | None:
        task = queue.dequeue_by_priority()
        if task:
            self._current_task_start = time.time()
        return task

    def should_preempt(self, current_task: Task, queue: TaskQueue) -> bool:
        # 时间片用完则抢占
        elapsed = time.time() - self._current_task_start
        return elapsed >= self.time_slice


class FairScheduler(BaseScheduler):
    """
    公平调度器

    确保每个消费者获得公平的执行机会
    """

    def __init__(self) -> None:
        self._consumer_usage: dict[str, int] = {}

    def select_next(self, queue: TaskQueue) -> Task | None:
        # 选择使用次数最少的消费者的任务
        ready_tasks = queue.get_ready_tasks()
        if not ready_tasks:
            return None

        # 按消费者使用次数排序
        ready_tasks.sort(key=lambda t: self._consumer_usage.get(t.assigned_to or "", 0))

        task = ready_tasks[0]
        queue._queues[TaskStatus.READY].pop(task.id)
        queue._task_index.pop(task.id, None)
        queue._update_stats()

        return task

    def should_preempt(self, current_task: Task, queue: TaskQueue) -> bool:
        return False


class Scheduler:
    """
    任务调度器 - 类似操作系统进程调度器

    职责:
    1. 任务调度: 从就绪队列选择任务执行
    2. 资源分配: 分配Consumer给任务
    3. 负载均衡: 均衡Consumer负载
    4. 优先级管理: 按优先级调度
    5. 抢占调度: 支持任务抢占
    """

    def __init__(
        self,
        kernel: TaskKernel,
        algorithm: SchedulingAlgorithm = SchedulingAlgorithm.PRIORITY,
    ) -> None:
        self.kernel = kernel
        self.algorithm = algorithm

        # 创建具体调度器
        self._scheduler = self._create_scheduler(algorithm)

        # 消费者管理
        self._consumers: dict[str, dict[str, Any]] = {}  # consumer_id -> info
        self._consumer_tasks: dict[str, str] = {}  # consumer_id -> task_id

        # 统计
        self._stats = SchedulerStats()

    def _create_scheduler(self, algorithm: SchedulingAlgorithm) -> BaseScheduler:
        """创建具体调度器"""
        schedulers = {
            SchedulingAlgorithm.FIFO: FIFOScheduler(),
            SchedulingAlgorithm.PRIORITY: PriorityScheduler(),
            SchedulingAlgorithm.ROUND_ROBIN: RoundRobinScheduler(),
            SchedulingAlgorithm.FAIR: FairScheduler(),
        }
        return schedulers.get(algorithm, PriorityScheduler())

    def register_consumer(
        self,
        consumer_id: str,
        capabilities: list[str] | None = None,
        max_concurrent: int = 1,
    ) -> None:
        """
        注册消费者 - 类似操作系统注册处理器

        Args:
            consumer_id: 消费者ID
            capabilities: 能力列表 (可执行的任务类型)
            max_concurrent: 最大并发任务数
        """
        self._consumers[consumer_id] = {
            "id": consumer_id,
            "capabilities": capabilities or [],
            "max_concurrent": max_concurrent,
            "current_tasks": 0,
            "total_completed": 0,
            "status": "idle",
            "registered_at": time.time(),
        }

    def unregister_consumer(self, consumer_id: str) -> None:
        """注销消费者"""
        self._consumers.pop(consumer_id, None)
        self._consumer_tasks.pop(consumer_id, None)

    def get_idle_consumers(self) -> list[str]:
        """获取空闲消费者"""
        idle = []
        for consumer_id, info in self._consumers.items():
            if info["current_tasks"] < info["max_concurrent"]:
                idle.append(consumer_id)
        return idle

    def select_consumer(self, task: Task) -> str | None:
        """
        选择合适的消费者执行任务

        基于能力匹配和负载均衡

        Args:
            task: 任务

        Returns:
            消费者ID
        """
        idle_consumers = self.get_idle_consumers()
        if not idle_consumers:
            return None

        # 检查能力匹配
        task_type = task.type
        task_tools = set(task.required_tools)

        best_consumer = None
        best_score = -1

        for consumer_id in idle_consumers:
            info = self._consumers[consumer_id]
            capabilities = set(info["capabilities"])

            # 计算匹配分数
            score = 0

            # 工具匹配
            if task_tools:
                tool_match = len(task_tools & capabilities)
                score += tool_match * 10

            # 负载均衡 - 选择负载最低的
            score -= info["current_tasks"] * 5

            if score > best_score:
                best_score = score
                best_consumer = consumer_id

        return best_consumer

    def schedule(self) -> list[dict[str, Any]]:
        """
        执行调度 - 分配任务给消费者

        Returns:
            调度结果列表 [{"task_id": ..., "consumer_id": ...}]
        """
        results = []

        # 获取空闲消费者
        idle_consumers = self.get_idle_consumers()
        if not idle_consumers:
            return results

        # 检查依赖满足的就绪任务
        ready_tasks = []
        for task in self.kernel.queue.get_ready_tasks():
            if self.kernel.dependency_graph.check_dependencies_met(task.id):
                ready_tasks.append(task)

        # 按优先级排序
        ready_tasks.sort(key=lambda t: t.priority.value)

        # 分配任务
        for task in ready_tasks:
            consumer_id = self.select_consumer(task)
            if consumer_id is None:
                break  # 没有空闲消费者

            # 开始任务
            if self.kernel.start_task(task.id, consumer_id):
                # 更新消费者状态
                self._consumers[consumer_id]["current_tasks"] += 1
                self._consumers[consumer_id]["status"] = "busy"
                self._consumer_tasks[consumer_id] = task.id

                results.append({
                    "task_id": task.id,
                    "task_name": task.name,
                    "consumer_id": consumer_id,
                    "priority": task.priority.value,
                })

                self._stats.total_scheduled += 1

        return results

    def task_completed(self, consumer_id: str, task_id: str) -> None:
        """
        任务完成通知

        Args:
            consumer_id: 消费者ID
            task_id: 任务ID
        """
        if consumer_id in self._consumers:
            info = self._consumers[consumer_id]
            info["current_tasks"] = max(0, info["current_tasks"] - 1)
            info["total_completed"] += 1
            if info["current_tasks"] == 0:
                info["status"] = "idle"

        self._consumer_tasks.pop(consumer_id, None)

    def preempt(self) -> dict[str, Any] | None:
        """
        抢占调度 - 中断当前任务，调度更高优先级任务

        Returns:
            抢占结果
        """
        # 找到当前运行的任务
        running_tasks = self.kernel.queue.get_running_tasks()
        if not running_tasks:
            return None

        # 检查是否需要抢占
        for task in running_tasks:
            if self._scheduler.should_preempt(task, self.kernel.queue):
                # 阻塞当前任务
                self.kernel.block_task(task.id, "Preempted")
                self._stats.total_preemptions += 1

                return {
                    "preempted_task_id": task.id,
                    "reason": "Higher priority task arrived",
                }

        return None

    def get_consumer_status(self) -> dict[str, Any]:
        """获取消费者状态"""
        return {
            "total_consumers": len(self._consumers),
            "idle_consumers": len(self.get_idle_consumers()),
            "busy_consumers": len([c for c in self._consumers.values() if c["status"] == "busy"]),
            "consumers": {
                cid: {
                    "status": info["status"],
                    "current_tasks": info["current_tasks"],
                    "total_completed": info["total_completed"],
                }
                for cid, info in self._consumers.items()
            },
        }

    def get_stats(self) -> SchedulerStats:
        """获取统计信息"""
        return self._stats

    def get_queue_status(self) -> dict[str, Any]:
        """获取队列状态"""
        return self.kernel.queue.get_status_distribution()

    def rebalance(self) -> list[dict[str, Any]]:
        """
        负载均衡 - 重新分配任务

        Returns:
            重分配结果
        """
        results = []

        # 获取负载不均衡的消费者
        busy_consumers = [c for c in self._consumers.values() if c["current_tasks"] > 1]
        idle_consumers = self.get_idle_consumers()

        if not busy_consumers or not idle_consumers:
            return results

        # 迁移任务
        for busy_info in busy_consumers:
            if not idle_consumers:
                break

            consumer_id = busy_info["id"]
            task_id = self._consumer_tasks.get(consumer_id)

            if task_id:
                # 迁移到空闲消费者
                new_consumer = idle_consumers.pop(0)
                task = self.kernel.queue.get_task(task_id)

                if task:
                    task.assigned_to = new_consumer
                    self._consumer_tasks[new_consumer] = task_id
                    self._consumer_tasks.pop(consumer_id, None)

                    results.append({
                        "task_id": task_id,
                        "from_consumer": consumer_id,
                        "to_consumer": new_consumer,
                    })

        return results