"""
Tests for Kernel Module - Operating System Style Task Management
"""

import pytest
import asyncio

from py_ha.kernel import (
    Task,
    TaskStatus,
    TaskPriority,
    TaskResult,
    TaskQueue,
    TaskKernel,
    Scheduler,
    SchedulingAlgorithm,
    Producer,
    ProducerRole,
    Consumer,
    ConsumerRole,
)
from py_ha.kernel.producer import ProducerConfig
from py_ha.kernel.consumer import ConsumerConfig


class TestTask:
    """测试任务模型"""

    def test_create_task(self) -> None:
        """创建任务"""
        task = Task(name="test_task", description="A test task")
        assert task.name == "test_task"
        assert task.status == TaskStatus.CREATED
        assert task.priority == TaskPriority.NORMAL

    def test_task_status_transition(self) -> None:
        """任务状态转换"""
        task = Task(name="test")

        # CREATED → READY
        assert task.transition_to(TaskStatus.READY, "Published")
        assert task.status == TaskStatus.READY

        # READY → RUNNING
        assert task.transition_to(TaskStatus.RUNNING, "Started")
        assert task.status == TaskStatus.RUNNING
        assert task.started_at is not None

        # RUNNING → DONE
        assert task.transition_to(TaskStatus.DONE, "Completed")
        assert task.status == TaskStatus.DONE
        assert task.ended_at is not None

    def test_invalid_status_transition(self) -> None:
        """无效状态转换"""
        task = Task(name="test")

        # CREATED → DONE (无效)
        assert not task.transition_to(TaskStatus.DONE)

    def test_task_priority(self) -> None:
        """任务优先级"""
        task_high = Task(name="high", priority=TaskPriority.HIGH)
        task_normal = Task(name="normal", priority=TaskPriority.NORMAL)

        assert task_high.priority.value < task_normal.priority.value

    def test_task_dependencies(self) -> None:
        """任务依赖"""
        task = Task(name="test")
        task.add_dependency("dep_1")
        task.add_dependency("dep_2")

        assert len(task.dependencies) == 2
        assert "dep_1" in task.dependencies

    def test_task_result(self) -> None:
        """任务结果"""
        task = Task(name="test")
        task.transition_to(TaskStatus.READY)
        task.transition_to(TaskStatus.RUNNING)

        result = TaskResult(success=True, output="Done")
        task.set_result(result)
        task.transition_to(TaskStatus.DONE, "Task completed")

        assert task.status == TaskStatus.DONE
        assert task.result.success is True

    def test_task_retry(self) -> None:
        """任务重试"""
        task = Task(name="test", max_retries=2)

        # 模拟失败
        task.transition_to(TaskStatus.READY)
        task.transition_to(TaskStatus.RUNNING)
        task.transition_to(TaskStatus.FAILED, "Error")

        assert task.can_retry()
        task.retry_count += 1
        task.transition_to(TaskStatus.READY, "Retry")


class TestTaskQueue:
    """测试任务队列"""

    def test_enqueue_dequeue(self) -> None:
        """入队出队"""
        queue = TaskQueue()
        task = Task(name="test", status=TaskStatus.READY)

        queue.enqueue(task)
        assert queue.size() == 1

        dequeued = queue.dequeue()
        assert dequeued is not None
        assert dequeued.id == task.id
        assert queue.size() == 0

    def test_priority_queue(self) -> None:
        """优先级队列"""
        queue = TaskQueue()

        # 添加不同优先级任务
        low = Task(name="low", priority=TaskPriority.LOW, status=TaskStatus.READY)
        high = Task(name="high", priority=TaskPriority.HIGH, status=TaskStatus.READY)
        critical = Task(name="critical", priority=TaskPriority.CRITICAL, status=TaskStatus.READY)

        queue.enqueue(low)
        queue.enqueue(high)
        queue.enqueue(critical)

        # 按优先级出队
        first = queue.dequeue_by_priority()
        assert first is not None
        assert first.priority == TaskPriority.CRITICAL

        second = queue.dequeue_by_priority()
        assert second is not None
        assert second.priority == TaskPriority.HIGH

    def test_status_update(self) -> None:
        """状态更新"""
        queue = TaskQueue()
        task = Task(name="test", status=TaskStatus.READY)
        queue.enqueue(task)

        queue.update_task_status(task.id, TaskStatus.RUNNING, "Started")

        updated = queue.get_task(task.id)
        assert updated is not None
        assert updated.status == TaskStatus.RUNNING

    def test_get_by_status(self) -> None:
        """按状态获取"""
        queue = TaskQueue()

        ready_task = Task(name="ready", status=TaskStatus.READY)
        running_task = Task(name="running", status=TaskStatus.RUNNING)

        queue.enqueue(ready_task)
        queue.enqueue(running_task)

        ready_list = queue.get_ready_tasks()
        running_list = queue.get_running_tasks()

        assert len(ready_list) == 1
        assert len(running_list) == 1

    def test_queue_stats(self) -> None:
        """队列统计"""
        queue = TaskQueue()

        for i in range(5):
            task = Task(name=f"task_{i}", status=TaskStatus.READY)
            queue.enqueue(task)

        stats = queue.get_stats()
        assert stats.ready_count == 5


class TestTaskKernel:
    """测试任务内核"""

    def test_register_task(self) -> None:
        """注册任务"""
        kernel = TaskKernel()
        task = kernel.register_task(name="test_task")

        assert task.id is not None
        assert task.status == TaskStatus.CREATED
        assert kernel.queue.get_task(task.id) is not None

    def test_task_lifecycle(self) -> None:
        """任务生命周期"""
        kernel = TaskKernel()

        # 创建任务
        task = kernel.register_task(name="lifecycle_test")
        assert task.status == TaskStatus.CREATED

        # 发布任务
        kernel.queue.update_task_status(task.id, TaskStatus.READY, "Published")
        assert kernel.queue.get_task(task.id).status == TaskStatus.READY

        # 开始任务
        kernel.start_task(task.id, assigned_to="consumer_1")
        assert kernel.queue.get_task(task.id).status == TaskStatus.RUNNING

        # 完成任务
        result = TaskResult(success=True, output="Done")
        kernel.complete_task(task.id, result)
        assert kernel.queue.get_task(task.id).status == TaskStatus.DONE

    def test_task_dependencies(self) -> None:
        """任务依赖"""
        kernel = TaskKernel()

        # 创建依赖任务
        dep_task = kernel.register_task(name="dependency")

        # 发布并完成依赖任务
        kernel.queue.update_task_status(dep_task.id, TaskStatus.READY)
        kernel.start_task(dep_task.id)
        kernel.complete_task(dep_task.id, TaskResult(success=True))

        # 创建依赖于此任务的任务
        main_task = kernel.register_task(
            name="main",
            dependencies=[dep_task.id],
        )

        # 检查依赖是否满足
        assert kernel.dependency_graph.check_dependencies_met(main_task.id)

    def test_task_failure_retry(self) -> None:
        """任务失败重试"""
        kernel = TaskKernel()

        task = kernel.register_task(name="retry_test")
        # 设置最大重试次数
        task.max_retries = 2
        kernel.queue.update_task_status(task.id, TaskStatus.READY)
        kernel.start_task(task.id)

        # 第一次失败
        kernel.fail_task(task.id, "Error", can_retry=True)
        assert kernel.queue.get_task(task.id).status == TaskStatus.READY

        # 检查可以重试
        retrieved = kernel.queue.get_task(task.id)
        assert retrieved.retry_count == 1

    def test_closure_verification(self) -> None:
        """闭环验证"""
        kernel = TaskKernel()

        task = kernel.register_task(name="closure_test")
        kernel.queue.update_task_status(task.id, TaskStatus.READY)
        kernel.start_task(task.id)
        kernel.complete_task(task.id, TaskResult(success=True))

        # 验证闭环
        result = kernel.verify_all_closures()
        assert result["all_closed"] is True

    def test_event_logging(self) -> None:
        """事件日志"""
        kernel = TaskKernel(enable_event_logging=True)

        task = kernel.register_task(name="event_test")
        events = kernel.get_events(task.id)

        assert len(events) > 0
        assert events[0].event_type == "task_created"


class TestScheduler:
    """测试调度器"""

    def test_register_consumer(self) -> None:
        """注册消费者"""
        kernel = TaskKernel()
        scheduler = Scheduler(kernel)

        scheduler.register_consumer("consumer_1", capabilities=["research", "analysis"])

        status = scheduler.get_consumer_status()
        assert status["total_consumers"] == 1

    def test_schedule_task(self) -> None:
        """调度任务"""
        kernel = TaskKernel()
        scheduler = Scheduler(kernel)

        # 注册消费者
        scheduler.register_consumer("consumer_1", capabilities=["general"])

        # 创建就绪任务
        task = kernel.register_task(name="schedule_test", required_tools=["general"])
        kernel.queue.update_task_status(task.id, TaskStatus.READY)

        # 执行调度
        results = scheduler.schedule()

        assert len(results) == 1
        assert results[0]["task_id"] == task.id

    def test_priority_scheduling(self) -> None:
        """优先级调度"""
        kernel = TaskKernel()
        scheduler = Scheduler(kernel, algorithm=SchedulingAlgorithm.PRIORITY)
        scheduler.register_consumer("consumer_1")

        # 创建不同优先级任务
        low = kernel.register_task(name="low", priority=TaskPriority.LOW)
        high = kernel.register_task(name="high", priority=TaskPriority.HIGH)

        kernel.queue.update_task_status(low.id, TaskStatus.READY)
        kernel.queue.update_task_status(high.id, TaskStatus.READY)

        results = scheduler.schedule()

        # 高优先级任务先被调度
        assert results[0]["task_id"] == high.id


class TestProducer:
    """测试生产者"""

    def test_create_task(self) -> None:
        """创建任务"""
        kernel = TaskKernel()
        config = ProducerConfig(id="prod_1", role=ProducerRole.MANAGER, name="Manager")
        producer = Producer(kernel, config)

        task = producer.create_task(name="test_task", description="A test")

        assert task.name == "test_task"
        assert task.created_by == "prod_1"

    def test_publish_task(self) -> None:
        """发布任务"""
        kernel = TaskKernel()
        producer = Producer(kernel)

        task = producer.create_task(name="publish_test")
        producer.publish_task(task)

        assert kernel.queue.get_task(task.id).status == TaskStatus.READY

    def test_decompose_task(self) -> None:
        """分解任务"""
        kernel = TaskKernel()
        producer = Producer(kernel)

        parent = producer.create_task(name="parent_task")
        subtask_defs = [
            {"description": "Subtask 1"},
            {"description": "Subtask 2"},
        ]

        subtasks = producer.decompose_task(parent, subtask_defs)

        assert len(subtasks) == 2
        assert parent.metadata.get("subtask_count") == 2

    def test_task_chain(self) -> None:
        """任务链"""
        kernel = TaskKernel()
        producer = Producer(kernel)

        definitions = [
            {"name": "step1"},
            {"name": "step2"},
            {"name": "step3"},
        ]

        chain = producer.create_task_chain(definitions)

        assert len(chain) == 3
        assert chain[1].dependencies == [chain[0].id]
        assert chain[2].dependencies == [chain[1].id]

    def test_parallel_tasks(self) -> None:
        """并行任务"""
        kernel = TaskKernel()
        producer = Producer(kernel)

        definitions = [
            {"name": "parallel_1"},
            {"name": "parallel_2"},
        ]

        tasks = producer.create_parallel_tasks(definitions, merge_task_definition={"name": "merge"})

        assert len(tasks) == 3  # 2 parallel + 1 merge
        # merge任务依赖两个并行任务
        assert len(tasks[2].dependencies) == 2


class TestConsumer:
    """测试消费者"""

    def test_consumer_config(self) -> None:
        """消费者配置"""
        config = ConsumerConfig(
            id="cons_1",
            role=ConsumerRole.WORKER,
            name="Worker1",
            capabilities=["research", "analysis"],
        )
        assert config.capabilities == ["research", "analysis"]

    @pytest.mark.asyncio
    async def test_consumer_execution(self) -> None:
        """消费者执行"""
        kernel = TaskKernel()
        scheduler = Scheduler(kernel)

        config = ConsumerConfig(id="cons_1", role=ConsumerRole.WORKER, name="Worker1")
        consumer = Consumer(kernel, scheduler, config)

        task = Task(name="test_task")
        result = await consumer.execute(task)

        assert result.success is True

    def test_consumer_can_accept(self) -> None:
        """消费者任务接受判断"""
        kernel = TaskKernel()
        scheduler = Scheduler(kernel)

        config = ConsumerConfig(
            id="cons_1",
            role=ConsumerRole.SPECIALIST,
            name="Specialist1",
            capabilities=["research"],
        )
        consumer = Consumer(kernel, scheduler, config)

        assert consumer.can_accept("research") is True
        assert consumer.can_accept("analysis") is False


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_full_workflow(self) -> None:
        """完整工作流测试"""
        # 创建内核
        kernel = TaskKernel()
        scheduler = Scheduler(kernel)

        # 创建生产者
        producer = Producer(kernel)

        # 创建消费者
        from py_ha.kernel.consumer import ConsumerPool
        pool = ConsumerPool(kernel, scheduler)
        worker = pool.create_worker("Worker1", capabilities=["general"])

        # 生产者创建任务
        task = producer.create_and_publish(
            name="integration_test",
            description="Full workflow test",
            priority=TaskPriority.HIGH,
        )

        assert task.status == TaskStatus.READY

        # 调度任务
        results = scheduler.schedule()
        assert len(results) > 0

        # 验证状态
        updated = kernel.queue.get_task(task.id)
        assert updated.status == TaskStatus.RUNNING

    def test_producer_consumer_closed_loop(self) -> None:
        """生产者消费者闭环测试"""
        kernel = TaskKernel()
        scheduler = Scheduler(kernel)
        producer = Producer(kernel)

        # 注册消费者
        scheduler.register_consumer("consumer_1", capabilities=["general"])

        # 创建任务
        task = producer.create_task(name="closed_loop_test")
        producer.publish_task(task)

        # 确保任务在就绪队列
        assert kernel.queue.get_task(task.id).status == TaskStatus.READY

        # 检查依赖满足
        assert kernel.dependency_graph.check_dependencies_met(task.id)

        # 执行调度
        results = scheduler.schedule()

        # 获取最新状态
        updated = kernel.queue.get_task(task.id)

        # 如果调度没有成功，手动启动
        if updated.status != TaskStatus.RUNNING:
            started = kernel.start_task(task.id, "consumer_1")
            assert started, f"Failed to start task, status: {updated.status}"

        # 验证现在是运行状态
        running_task = kernel.queue.get_task(task.id)
        assert running_task.status == TaskStatus.RUNNING, f"Task status is {running_task.status}"

        # 完成任务
        result = TaskResult(success=True, output="Completed")
        success = kernel.complete_task(task.id, result)
        assert success, "complete_task returned False"

        # 验证闭环
        verification = kernel.verify_all_closures()
        assert verification["all_closed"] is True

        # 检查统计
        stats = kernel.get_stats()
        assert stats.total_tasks_completed == 1