"""
Producer - 任务生产者

类似生产者-消费者模型中的生产者:
- 任务创建
- 任务分解
- 任务发布
- 结果接收
"""

from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel, Field
from enum import Enum
import time

from py_ha.kernel.task import Task, TaskStatus, TaskPriority, TaskResult
from py_ha.kernel.kernel import TaskKernel


class ProducerRole(Enum):
    """
    生产者角色类型

    - MANAGER: 管理者，接收用户请求，分解任务
    - PLANNER: 规划者，制定执行计划
    - COORDINATOR: 协调者，分配子任务
    - DECOMPOSER: 分解者，将大任务分解为小任务
    """

    MANAGER = "manager"
    PLANNER = "planner"
    COORDINATOR = "coordinator"
    DECOMPOSER = "decomposer"


class ProducerConfig(BaseModel):
    """生产者配置"""

    id: str = Field(..., description="生产者ID")
    role: ProducerRole = Field(..., description="角色类型")
    name: str = Field(..., description="名称")
    max_pending_tasks: int = Field(default=100, description="最大待处理任务数")
    auto_decompose: bool = Field(default=True, description="是否自动分解任务")


class ProducerStats(BaseModel):
    """生产者统计"""

    tasks_created: int = Field(default=0, description="创建任务数")
    tasks_completed: int = Field(default=0, description="完成任务数")
    tasks_failed: int = Field(default=0, description="失败任务数")
    avg_decomposition_time: float = Field(default=0.0, description="平均分解时间")


class Producer:
    """
    任务生产者 - 创建和发布任务

    职责:
    1. 任务创建: 定义任务内容、优先级、依赖
    2. 任务分解: 将复杂任务分解为子任务
    3. 任务发布: 将任务提交到队列
    4. 结果接收: 接收任务完成通知

    角色类型:
    - Manager: 管理型，接收用户请求，创建主任务
    - Planner: 规划型，将任务分解为执行计划
    - Coordinator: 协调型，分配子任务给不同执行者
    """

    def __init__(
        self,
        kernel: TaskKernel,
        config: ProducerConfig | None = None,
    ) -> None:
        self.kernel = kernel

        # 配置
        if config is None:
            import uuid
            config = ProducerConfig(
                id=str(uuid.uuid4()),
                role=ProducerRole.MANAGER,
                name="default_producer",
            )
        self.config = config

        # 待处理任务
        self._pending_tasks: dict[str, Task] = {}
        self._completed_tasks: dict[str, TaskResult] = {}

        # 回调
        self._completion_callbacks: list[Any] = []

        # 统计
        self._stats = ProducerStats()

        # 注册事件回调
        kernel.register_callback("task_completed", self._on_task_completed)
        kernel.register_callback("task_failed", self._on_task_failed)

    def create_task(
        self,
        name: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.NORMAL,
        task_type: str = "general",
        dependencies: list[str] | None = None,
        required_tools: list[str] | None = None,
        estimated_time: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> Task:
        """
        创建任务 - 类似进程创建

        Args:
            name: 任务名称
            description: 任务描述
            priority: 优先级
            task_type: 任务类型
            dependencies: 依赖任务ID列表
            required_tools: 所需工具
            estimated_time: 预估时间
            metadata: 元数据

        Returns:
            创建的任务
        """
        task = self.kernel.register_task(
            name=name,
            description=description,
            priority=priority,
            dependencies=dependencies,
            required_tools=required_tools,
            metadata=metadata,
            created_by=self.config.id,
        )

        task.type = task_type
        task.estimated_time = estimated_time

        # 记录待处理
        self._pending_tasks[task.id] = task
        self._stats.tasks_created += 1

        return task

    def publish_task(self, task: Task) -> str:
        """
        发布任务 - 将任务状态设为READY

        Args:
            task: 任务对象

        Returns:
            任务ID
        """
        # 确保任务已注册
        if self.kernel.queue.get_task(task.id) is None:
            self.kernel.register_task_object(task)

        # 检查依赖
        if task.dependencies:
            # 检查依赖是否都存在
            for dep_id in task.dependencies:
                dep_task = self.kernel.queue.get_task(dep_id)
                if dep_task is None:
                    raise ValueError(f"Dependency task not found: {dep_id}")

            # 如果依赖未完成，任务将保持CREATED状态
            if not self.kernel.dependency_graph.check_dependencies_met(task.id):
                return task.id

        # 更新状态为READY
        self.kernel.queue.update_task_status(task.id, TaskStatus.READY, "Published by producer")

        return task.id

    def create_and_publish(
        self,
        name: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.NORMAL,
        **kwargs: Any,
    ) -> Task:
        """
        创建并发布任务

        Args:
            name: 任务名称
            description: 任务描述
            priority: 优先级

        Returns:
            创建的任务
        """
        task = self.create_task(name, description, priority, **kwargs)
        self.publish_task(task)
        return task

    def decompose_task(
        self,
        parent_task: Task,
        subtask_definitions: list[dict[str, Any]],
    ) -> list[Task]:
        """
        分解任务 - 将大任务分解为子任务

        Args:
            parent_task: 父任务
            subtask_definitions: 子任务定义列表

        Returns:
            创建的子任务列表
        """
        start_time = time.time()
        subtasks = []

        for i, definition in enumerate(subtask_definitions):
            # 创建子任务
            subtask = self.create_task(
                name=f"{parent_task.name}_sub_{i+1}",
                description=definition.get("description", ""),
                priority=parent_task.priority,
                task_type=definition.get("type", "subtask"),
                required_tools=definition.get("required_tools", []),
                estimated_time=definition.get("estimated_time", 0),
                metadata={"parent_task_id": parent_task.id, **definition.get("metadata", {})},
            )

            # 添加对父任务的引用
            parent_task.metadata.setdefault("subtask_ids", []).append(subtask.id)

            subtasks.append(subtask)

        # 更新父任务状态
        parent_task.metadata["subtask_count"] = len(subtasks)
        parent_task.metadata["decomposed"] = True

        # 更新统计
        elapsed = time.time() - start_time
        n = self._stats.tasks_created
        self._stats.avg_decomposition_time = (
            (self._stats.avg_decomposition_time * (n - 1) + elapsed) / n
        ) if n > 0 else elapsed

        return subtasks

    def create_task_chain(
        self,
        task_definitions: list[dict[str, Any]],
    ) -> list[Task]:
        """
        创建任务链 - 任务按顺序执行

        Args:
            task_definitions: 任务定义列表 (按顺序)

        Returns:
            创建的任务列表
        """
        tasks = []
        prev_task_id = None

        for definition in task_definitions:
            dependencies = []
            if prev_task_id:
                dependencies = [prev_task_id]

            task = self.create_task(
                name=definition.get("name", "task"),
                description=definition.get("description", ""),
                priority=definition.get("priority", TaskPriority.NORMAL),
                dependencies=dependencies,
                required_tools=definition.get("required_tools", []),
                metadata=definition.get("metadata", {}),
            )

            tasks.append(task)
            prev_task_id = task.id

        return tasks

    def create_parallel_tasks(
        self,
        task_definitions: list[dict[str, Any]],
        merge_task_definition: dict[str, Any] | None = None,
    ) -> list[Task]:
        """
        创建并行任务 - 多个任务并行执行，可选合并任务

        Args:
            task_definitions: 任务定义列表
            merge_task_definition: 合并任务定义 (等待所有并行任务完成)

        Returns:
            创建的任务列表
        """
        tasks = []

        # 创建并行任务
        for definition in task_definitions:
            task = self.create_task(
                name=definition.get("name", "parallel_task"),
                description=definition.get("description", ""),
                priority=definition.get("priority", TaskPriority.NORMAL),
                required_tools=definition.get("required_tools", []),
                metadata={**definition.get("metadata", {}), "parallel_group": True},
            )
            tasks.append(task)

        # 创建合并任务
        if merge_task_definition:
            parallel_task_ids = [t.id for t in tasks]
            merge_task = self.create_task(
                name=merge_task_definition.get("name", "merge_task"),
                description=merge_task_definition.get("description", ""),
                priority=merge_task_definition.get("priority", TaskPriority.NORMAL),
                dependencies=parallel_task_ids,
                required_tools=merge_task_definition.get("required_tools", []),
                metadata={**merge_task_definition.get("metadata", {}), "is_merge": True},
            )
            tasks.append(merge_task)

        return tasks

    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功取消
        """
        task = self.kernel.queue.get_task(task_id)
        if task is None or task.created_by != self.config.id:
            return False

        return self.kernel.cancel_task(task_id)

    def get_task_status(self, task_id: str) -> TaskStatus | None:
        """获取任务状态"""
        task = self.kernel.queue.get_task(task_id)
        return task.status if task else None

    def get_pending_tasks(self) -> list[Task]:
        """获取待处理任务"""
        return list(self._pending_tasks.values())

    def get_completed_results(self) -> dict[str, TaskResult]:
        """获取已完成任务结果"""
        return self._completed_tasks.copy()

    def on_completion(self, callback: Any) -> None:
        """注册完成回调"""
        self._completion_callbacks.append(callback)

    def _on_task_completed(self, event: dict[str, Any]) -> None:
        """任务完成回调"""
        task_id = event.get("task_id")
        if task_id in self._pending_tasks:
            task = self._pending_tasks.pop(task_id)
            if task.result:
                self._completed_tasks[task_id] = task.result
            self._stats.tasks_completed += 1

            # 触发回调
            for callback in self._completion_callbacks:
                try:
                    callback(task_id, task.result)
                except Exception:
                    pass

    def _on_task_failed(self, event: dict[str, Any]) -> None:
        """任务失败回调"""
        task_id = event.get("task_id")
        if task_id in self._pending_tasks:
            self._pending_tasks.pop(task_id)
            self._stats.tasks_failed += 1

    def get_stats(self) -> ProducerStats:
        """获取统计信息"""
        return self._stats


class TaskFactory:
    """
    任务工厂 - 快速创建常见类型的任务
    """

    def __init__(self, producer: Producer) -> None:
        self.producer = producer

    def create_research_task(
        self,
        topic: str,
        depth: str = "normal",
    ) -> Task:
        """创建研究任务"""
        priority = TaskPriority.HIGH if depth == "deep" else TaskPriority.NORMAL

        return self.producer.create_and_publish(
            name=f"Research: {topic}",
            description=f"Conduct research on {topic}",
            priority=priority,
            task_type="research",
            required_tools=["web_search", "summarize"],
            metadata={"topic": topic, "depth": depth},
        )

    def create_analysis_task(
        self,
        data_source: str,
        analysis_type: str,
    ) -> Task:
        """创建分析任务"""
        return self.producer.create_and_publish(
            name=f"Analysis: {analysis_type}",
            description=f"Perform {analysis_type} analysis on {data_source}",
            task_type="analysis",
            required_tools=["code_execute", "data_process"],
            metadata={"data_source": data_source, "analysis_type": analysis_type},
        )

    def create_workflow_task(
        self,
        workflow_name: str,
        steps: list[str],
    ) -> list[Task]:
        """创建工作流任务链"""
        definitions = [
            {
                "name": f"{workflow_name}_step_{i+1}",
                "description": step,
                "metadata": {"workflow": workflow_name, "step": i+1},
            }
            for i, step in enumerate(steps)
        ]
        return self.producer.create_task_chain(definitions)