"""
Kernel Module - Operating System Style Task Management

操作系统风格的任务管理核心:
- Task: 任务数据模型
- TaskQueue: 任务队列 (类似进程队列)
- TaskKernel: 任务内核 (生命周期管理)
- Scheduler: 调度器 (任务调度)
- Producer: 生产者角色
- Consumer: 消费者角色
"""

from py_ha.kernel.task import Task, TaskStatus, TaskPriority, TaskResult
from py_ha.kernel.queue import TaskQueue
from py_ha.kernel.kernel import TaskKernel
from py_ha.kernel.scheduler import Scheduler, SchedulingAlgorithm
from py_ha.kernel.producer import Producer, ProducerRole, ProducerConfig
from py_ha.kernel.consumer import Consumer, ConsumerRole

__all__ = [
    # Task
    "Task",
    "TaskStatus",
    "TaskPriority",
    "TaskResult",
    # Queue
    "TaskQueue",
    # Kernel
    "TaskKernel",
    # Scheduler
    "Scheduler",
    "SchedulingAlgorithm",
    # Roles
    "Producer",
    "ProducerRole",
    "ProducerConfig",
    "Consumer",
    "ConsumerRole",
]