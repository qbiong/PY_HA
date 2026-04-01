"""
Tests for Runtime Layer
"""

import pytest

from py_ha.runtime import TaskOrchestrator, ExecutionStrategy, ContextManager, AgentContext
from py_ha.core import AgentSpec


class TestContextManager:
    """测试上下文管理器"""

    def test_create_context(self) -> None:
        """创建上下文"""
        manager = ContextManager()
        ctx = manager.create_context("test-ctx")

        assert ctx.context_id == "test-ctx"
        assert manager.get_context("test-ctx") is not None

    def test_destroy_context(self) -> None:
        """销毁上下文"""
        manager = ContextManager()
        manager.create_context("test-ctx")
        manager.destroy_context("test-ctx")

        assert manager.get_context("test-ctx") is None

    def test_message_management(self) -> None:
        """消息管理"""
        ctx = AgentContext("test-ctx")
        ctx.add_message("user", "Hello")
        ctx.add_message("assistant", "Hi there")

        messages = ctx.get_messages()
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"

    def test_state_management(self) -> None:
        """状态管理"""
        ctx = AgentContext("test-ctx")
        ctx.set_state("key1", "value1")
        ctx.set_state("key2", {"nested": True})

        assert ctx.get_state("key1") == "value1"
        assert ctx.get_state("key2")["nested"] is True
        assert ctx.get_state("nonexistent", "default") == "default"

    def test_snapshot_and_restore(self) -> None:
        """快照与恢复"""
        manager = ContextManager()
        ctx = manager.create_context("test-ctx")
        ctx.add_message("user", "Hello")
        ctx.set_state("key", "value")

        # 创建快照
        snapshot = manager.save_snapshot("test-ctx")
        assert snapshot is not None
        assert len(snapshot.messages) == 1

        # 销毁原上下文
        manager.destroy_context("test-ctx")

        # 从快照恢复
        restored = manager.restore_snapshot(snapshot)
        assert restored.context_id == "test-ctx"
        assert len(restored.get_messages()) == 1
        assert restored.get_state("key") == "value"


class TestTaskOrchestrator:
    """测试任务编排器"""

    def test_create_orchestrator(self) -> None:
        """创建编排器"""
        orchestrator = TaskOrchestrator(
            strategy=ExecutionStrategy.SEQUENTIAL,
            max_concurrent=5,
        )
        assert orchestrator.strategy == ExecutionStrategy.SEQUENTIAL
        assert orchestrator.max_concurrent == 5

    @pytest.mark.asyncio
    async def test_execute_task(self) -> None:
        """执行任务"""
        orchestrator = TaskOrchestrator()
        spec = AgentSpec(name="test-agent")

        result = await orchestrator.execute(spec, "test task")

        assert result.success is True
        assert "test task" in result.output

    def test_decompose_task(self) -> None:
        """任务分解"""
        orchestrator = TaskOrchestrator()
        subtasks = orchestrator.decompose_task("complex task")

        assert len(subtasks) > 0
        assert subtasks[0] == "complex task"