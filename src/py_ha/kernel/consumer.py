"""
Consumer - 任务消费者

类似生产者-消费者模型中的消费者:
- 任务领取
- 任务执行
- 结果上报
- 状态更新
"""

from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel, Field
from enum import Enum
import asyncio
import time

from py_ha.kernel.task import Task, TaskStatus, TaskPriority, TaskResult
from py_ha.kernel.kernel import TaskKernel
from py_ha.kernel.scheduler import Scheduler


class ConsumerRole(Enum):
    """
    消费者角色类型

    - WORKER: 通用工作者，执行各种任务
    - SPECIALIST: 专家，执行特定类型任务
    - ANALYST: 分析师，执行分析类任务
    - EXECUTOR: 执行者，执行具体操作
    """

    WORKER = "worker"
    SPECIALIST = "specialist"
    ANALYST = "analyst"
    EXECUTOR = "executor"


class ConsumerConfig(BaseModel):
    """消费者配置"""

    id: str = Field(..., description="消费者ID")
    role: ConsumerRole = Field(..., description="角色类型")
    name: str = Field(..., description="名称")
    capabilities: list[str] = Field(default_factory=list, description="能力列表")
    max_concurrent: int = Field(default=1, description="最大并发任务数")
    poll_interval: float = Field(default=0.1, description="轮询间隔")


class ConsumerStats(BaseModel):
    """消费者统计"""

    tasks_executed: int = Field(default=0, description="执行任务数")
    tasks_succeeded: int = Field(default=0, description="成功任务数")
    tasks_failed: int = Field(default=0, description="失败任务数")
    avg_execution_time: float = Field(default=0.0, description="平均执行时间")
    total_execution_time: float = Field(default=0.0, description="总执行时间")


class Consumer:
    """
    任务消费者 - 执行任务

    职责:
    1. 任务领取: 从队列领取任务
    2. 任务执行: 执行任务逻辑
    3. 结果上报: 将结果写入内核
    4. 状态更新: 更新任务状态

    角色类型:
    - Worker: 通用工作者，执行各种任务
    - Specialist: 专家，执行特定类型任务
    - Analyst: 分析师，执行分析类任务
    - Executor: 执行者，执行具体操作
    """

    def __init__(
        self,
        kernel: TaskKernel,
        scheduler: Scheduler,
        config: ConsumerConfig | None = None,
    ) -> None:
        self.kernel = kernel
        self.scheduler = scheduler

        # 配置
        if config is None:
            import uuid
            config = ConsumerConfig(
                id=str(uuid.uuid4()),
                role=ConsumerRole.WORKER,
                name="default_consumer",
            )
        self.config = config

        # 当前执行的任务
        self._current_tasks: dict[str, Task] = {}

        # 统计
        self._stats = ConsumerStats()

        # 运行状态
        self._running = False
        self._task: asyncio.Task | None = None

        # 注册到调度器
        scheduler.register_consumer(
            config.id,
            capabilities=config.capabilities,
            max_concurrent=config.max_concurrent,
        )

    async def start(self) -> None:
        """启动消费者"""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        """停止消费者"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _run_loop(self) -> None:
        """运行循环 - 持续领取和执行任务"""
        while self._running:
            try:
                # 检查是否有分配给自己的任务
                assigned_tasks = self._get_assigned_tasks()

                for task in assigned_tasks:
                    if task.id not in self._current_tasks:
                        # 异步执行任务
                        asyncio.create_task(self._execute_task(task))

                await asyncio.sleep(self.config.poll_interval)

            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(1.0)  # 错误后等待

    def _get_assigned_tasks(self) -> list[Task]:
        """获取分配给自己的任务"""
        tasks = []
        for task in self.kernel.queue.get_running_tasks():
            if task.assigned_to == self.config.id and task.id not in self._current_tasks:
                tasks.append(task)
        return tasks

    async def _execute_task(self, task: Task) -> None:
        """
        执行任务

        Args:
            task: 任务对象
        """
        self._current_tasks[task.id] = task
        start_time = time.time()

        try:
            # 执行任务逻辑
            result = await self.execute(task)

            # 上报结果
            if result.success:
                self.kernel.complete_task(task.id, result)
                self._stats.tasks_succeeded += 1
            else:
                self.kernel.fail_task(task.id, result.error or "Execution failed")
                self._stats.tasks_failed += 1

        except Exception as e:
            # 执行异常
            self.kernel.fail_task(task.id, str(e))
            self._stats.tasks_failed += 1

        finally:
            # 更新统计
            elapsed = time.time() - start_time
            self._stats.total_execution_time += elapsed
            self._stats.tasks_executed += 1

            n = self._stats.tasks_executed
            self._stats.avg_execution_time = (
                (self._stats.avg_execution_time * (n - 1) + elapsed) / n
            )

            # 通知调度器
            self.scheduler.task_completed(self.config.id, task.id)

            # 移除当前任务
            self._current_tasks.pop(task.id, None)

    @abstractmethod
    async def execute(self, task: Task) -> TaskResult:
        """
        执行任务逻辑 - 子类必须实现

        Args:
            task: 任务对象

        Returns:
            执行结果
        """
        # 默认实现 - 返回成功
        return TaskResult(
            success=True,
            output=f"Task '{task.name}' executed by {self.config.name}",
            execution_time=0.0,
        )

    def get_current_tasks(self) -> list[Task]:
        """获取当前执行的任务"""
        return list(self._current_tasks.values())

    def get_stats(self) -> ConsumerStats:
        """获取统计信息"""
        return self._stats

    def is_busy(self) -> bool:
        """是否正在执行任务"""
        return len(self._current_tasks) >= self.config.max_concurrent

    def can_accept(self, task_type: str) -> bool:
        """
        是否可以接受指定类型的任务

        Args:
            task_type: 任务类型

        Returns:
            是否可以接受
        """
        if self.is_busy():
            return False

        # 检查能力匹配
        if self.config.capabilities:
            return task_type in self.config.capabilities or "general" in self.config.capabilities

        return True  # 无能力限制


class WorkerConsumer(Consumer):
    """
    工作者消费者 - 通用任务执行者

    可以执行各种类型的任务
    """

    async def execute(self, task: Task) -> TaskResult:
        """执行任务"""
        # 根据 任务类型执行不同逻辑
        task_type = task.type

        if task_type == "research":
            return await self._execute_research(task)
        elif task_type == "analysis":
            return await self._execute_analysis(task)
        elif task_type == "general":
            return await self._execute_general(task)
        else:
            return TaskResult(
                success=True,
                output=f"Executed task '{task.name}' of type '{task_type}'",
            )

    async def _execute_research(self, task: Task) -> TaskResult:
        """执行研究任务"""
        # TODO: 实现实际研究逻辑
        await asyncio.sleep(0.1)  # 模拟执行
        return TaskResult(
            success=True,
            output=f"Research completed for: {task.description}",
        )

    async def _execute_analysis(self, task: Task) -> TaskResult:
        """执行分析任务"""
        # TODO: 实现实际分析逻辑
        await asyncio.sleep(0.1)
        return TaskResult(
            success=True,
            output=f"Analysis completed for: {task.description}",
        )

    async def _execute_general(self, task: Task) -> TaskResult:
        """执行通用任务"""
        await asyncio.sleep(0.05)
        return TaskResult(
            success=True,
            output=f"General task completed: {task.name}",
        )


class SpecialistConsumer(Consumer):
    """
    专家消费者 - 执行特定类型任务

    只执行符合其能力列表的任务
    """

    async def execute(self, task: Task) -> TaskResult:
        """执行任务"""
        # 检查能力匹配
        if not self.can_accept(task.type):
            return TaskResult(
                success=False,
                error=f"Cannot handle task type: {task.type}",
            )

        # 执行专家逻辑
        await asyncio.sleep(0.1)

        return TaskResult(
            success=True,
            output=f"Specialist '{self.config.name}' completed task '{task.name}'",
            metadata={"specialist": self.config.role.value},
        )


class ConsumerPool:
    """
    消费者池 - 管理多个消费者

    类似线程池，管理一组消费者
    """

    def __init__(
        self,
        kernel: TaskKernel,
        scheduler: Scheduler,
    ) -> None:
        self.kernel = kernel
        self.scheduler = scheduler
        self._consumers: dict[str, Consumer] = {}

    def add_consumer(self, consumer: Consumer) -> None:
        """添加消费者"""
        self._consumers[consumer.config.id] = consumer

    def remove_consumer(self, consumer_id: str) -> None:
        """移除消费者"""
        if consumer_id in self._consumers:
            self._consumers[consumer_id].stop()
            self._consumers.pop(consumer_id)
            self.scheduler.unregister_consumer(consumer_id)

    def create_worker(
        self,
        name: str,
        capabilities: list[str] | None = None,
        max_concurrent: int = 1,
    ) -> WorkerConsumer:
        """创建工作者消费者"""
        import uuid
        config = ConsumerConfig(
            id=str(uuid.uuid4()),
            role=ConsumerRole.WORKER,
            name=name,
            capabilities=capabilities or [],
            max_concurrent=max_concurrent,
        )
        consumer = WorkerConsumer(self.kernel, self.scheduler, config)
        self.add_consumer(consumer)
        return consumer

    def create_specialist(
        self,
        name: str,
        specialty: str,
        max_concurrent: int = 1,
    ) -> SpecialistConsumer:
        """创建专家消费者"""
        import uuid
        config = ConsumerConfig(
            id=str(uuid.uuid4()),
            role=ConsumerRole.SPECIALIST,
            name=name,
            capabilities=[specialty],
            max_concurrent=max_concurrent,
        )
        consumer = SpecialistConsumer(self.kernel, self.scheduler, config)
        self.add_consumer(consumer)
        return consumer

    async def start_all(self) -> None:
        """启动所有消费者"""
        for consumer in self._consumers.values():
            await consumer.start()

    async def stop_all(self) -> None:
        """停止所有消费者"""
        for consumer in self._consumers.values():
            await consumer.stop()

    def get_all_stats(self) -> dict[str, Any]:
        """获取所有消费者统计"""
        return {
            "total_consumers": len(self._consumers),
            "consumers": {
                cid: consumer.get_stats().model_dump()
                for cid, consumer in self._consumers.items()
            },
        }

    def get_busy_count(self) -> int:
        """获取忙碌消费者数量"""
        return sum(1 for c in self._consumers.values() if c.is_busy())

    def get_idle_count(self) -> int:
        """获取空闲消费者数量"""
        return sum(1 for c in self._consumers.values() if not c.is_busy())