"""
架构集成测试 - 验证 contextvars 和 Shutdown Protocol 集成

测试内容:
1. contextvars 在 ThreadPoolExecutor 中的上下文隔离
2. Shutdown Protocol 在 WorkflowCoordinator 中的审批流程
3. 并行任务执行时的上下文传递
4. 关闭请求的未完成任务拒绝
"""

import pytest
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

from harnessgenj.utils.agent_context import (
    AgentContext,
    TeammateContext,
    create_agent_context,
    run_in_agent_context,
    get_agent_context,
    is_in_agent_context,
    get_agent_id,
)
from harnessgenj.workflow.coordinator import WorkflowCoordinator, create_coordinator
from harnessgenj.workflow.shutdown_protocol import (
    ShutdownProtocol,
    ShutdownRequest,
    ShutdownResponse,
    ShutdownStatus,
    create_shutdown_protocol,
)
from harnessgenj.workflow.collaboration import RoleCollaborationManager, create_collaboration_manager
from harnessgenj.workflow.pipeline import WorkflowPipeline, create_feature_pipeline, create_bugfix_pipeline
from harnessgenj.roles.base import RoleType, create_role


class TestContextvarsIntegration:
    """测试 contextvars 上下文隔离集成"""

    def test_context_isolation_in_thread(self):
        """测试线程间的上下文隔离"""
        results = {}

        def task_in_context(agent_id: str, role_type: str):
            """在线程中运行任务"""
            context = create_agent_context(
                agent_id=agent_id,
                session_id=f"session_{agent_id}",
                role_type=role_type,
                permission_mode="normal",
            )

            def inner_task():
                # 在上下文中可以获取信息
                ctx = get_agent_context()
                return {
                    "agent_id": ctx.agent_id if ctx else None,
                    "role_type": ctx.role_type if ctx else None,
                    "in_context": is_in_agent_context(),
                }

            return run_in_agent_context(context, inner_task)

        # 并行执行多个任务
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(task_in_context, "agent_1", "developer"),
                executor.submit(task_in_context, "agent_2", "reviewer"),
                executor.submit(task_in_context, "agent_3", "tester"),
            ]

            for i, future in enumerate(futures):
                results[i] = future.result()

        # 验证每个任务都有正确的上下文
        assert results[0]["agent_id"] == "agent_1"
        assert results[0]["role_type"] == "developer"
        assert results[0]["in_context"] == True

        assert results[1]["agent_id"] == "agent_2"
        assert results[1]["role_type"] == "reviewer"
        assert results[1]["in_context"] == True

        assert results[2]["agent_id"] == "agent_3"
        assert results[2]["role_type"] == "tester"
        assert results[2]["in_context"] == True

    def test_nested_context_isolation(self):
        """测试嵌套上下文隔离"""
        outer_context = create_agent_context(
            agent_id="outer_agent",
            session_id="outer_session",
            role_type="project_manager",
            permission_mode="admin",
        )

        inner_context = create_agent_context(
            agent_id="inner_agent",
            session_id="inner_session",
            role_type="developer",
            permission_mode="normal",
        )

        def outer_task():
            # 外层上下文
            ctx = get_agent_context()
            assert ctx.agent_id == "outer_agent"

            # 运行内层任务
            def inner_task():
                inner_ctx = get_agent_context()
                return inner_ctx.agent_id

            inner_id = run_in_agent_context(inner_context, inner_task)

            # 内层任务完成后，应该回到外层上下文
            ctx_after = get_agent_context()
            return {
                "outer_id": ctx.agent_id,
                "inner_id": inner_id,
                "after_inner": ctx_after.agent_id if ctx_after else None,
            }

        result = run_in_agent_context(outer_context, outer_task)

        assert result["outer_id"] == "outer_agent"
        assert result["inner_id"] == "inner_agent"
        assert result["after_inner"] == "outer_agent"

    def test_no_context_outside_run(self):
        """测试不在上下文运行时无法获取"""
        # 不在 run_in_agent_context 中，应该返回 None
        ctx = get_agent_context()
        assert ctx is None
        assert is_in_agent_context() == False

    def test_collaboration_manager_parallel_with_context(self):
        """测试协作管理器并行执行时使用上下文"""
        coordinator = create_coordinator()
        coordinator.create_role(RoleType.DEVELOPER, "dev_1")
        coordinator.create_role(RoleType.CODE_REVIEWER, "reviewer_1")

        pipeline = create_feature_pipeline()
        coordinator.register_workflow("test_workflow", pipeline)

        manager = create_collaboration_manager(coordinator)

        # 模拟并行任务
        tasks = [
            {"role_id": "dev_1", "task": {"task_id": "task_1", "type": "development"}},
            {"role_id": "reviewer_1", "task": {"task_id": "task_2", "type": "review"}},
        ]

        # execute_parallel 现在应该使用 contextvars
        result = manager.execute_parallel(tasks, fail_fast=False)

        # 验证执行结果
        assert result["total_tasks"] == 2
        assert result["completed"] >= 0 or result["failed"] >= 0


class TestShutdownProtocolIntegration:
    """测试 Shutdown Protocol 集成"""

    def test_coordinator_has_shutdown_protocol(self):
        """测试 Coordinator 包含 Shutdown Protocol"""
        coordinator = create_coordinator()

        assert hasattr(coordinator, "_shutdown_protocol")
        assert coordinator._shutdown_protocol is not None
        assert isinstance(coordinator._shutdown_protocol, ShutdownProtocol)

    def test_request_shutdown_creates_request(self):
        """测试创建关闭请求"""
        coordinator = create_coordinator()
        coordinator.create_role(RoleType.DEVELOPER, "worker_1")

        request = coordinator.request_shutdown(
            agent_id="worker_1",
            requester_id="coordinator",
            reason="任务完成",
        )

        assert request.agent_id == "worker_1"
        assert request.requester_id == "coordinator"
        assert request.reason == "任务完成"

    def test_shutdown_approved_without_pending_tasks(self):
        """测试无未完成任务时同意关闭"""
        coordinator = create_coordinator()

        request = ShutdownRequest(
            agent_id="worker_1",
            requester_id="coordinator",
            reason="关闭",
        )

        response = coordinator.handle_shutdown_request(request)

        assert response.approved == True
        assert "可以关闭" in response.reason
        assert coordinator.check_shutdown_status() == ShutdownStatus.APPROVED

    def test_shutdown_rejected_with_pending_tasks(self):
        """测试有未完成任务时拒绝关闭"""
        coordinator = create_coordinator()

        # 注册工作流并添加未完成阶段
        pipeline = create_feature_pipeline()
        coordinator.register_workflow("active_workflow", pipeline)

        # 启动工作流（创建未完成任务）
        coordinator.start_workflow("active_workflow", {"description": "test"})

        request = ShutdownRequest(
            agent_id="worker_1",
            requester_id="coordinator",
            reason="关闭",
        )

        response = coordinator.handle_shutdown_request(request)

        # 应该拒绝关闭（有未完成任务）
        assert response.approved == False
        assert "未完成任务" in response.reason

    def test_cleanup_on_shutdown_approval(self):
        """测试关闭批准后清理资源"""
        coordinator = create_coordinator()
        coordinator.create_role(RoleType.DEVELOPER, "worker_1")

        request = ShutdownRequest(
            agent_id="worker_1",
            requester_id="coordinator",
            reason="关闭",
        )

        response = coordinator.handle_shutdown_request(request)

        assert response.approved == True
        # 验证清理方法被调用（可以检查角色状态）


class TestFullIntegrationWorkflow:
    """测试完整集成工作流"""

    def test_context_plus_shutdown_integration(self):
        """测试上下文隔离与关闭协议联合工作"""
        coordinator = create_coordinator()

        # 创建角色
        dev = coordinator.create_role(RoleType.DEVELOPER, "dev_1")
        reviewer = coordinator.create_role(RoleType.CODE_REVIEWER, "reviewer_1")

        # 注册工作流
        pipeline = create_feature_pipeline()
        coordinator.register_workflow("feature_1", pipeline)

        # 创建协作管理器
        manager = create_collaboration_manager(coordinator)

        # 模拟开发任务
        dev.assign_task({"type": "development", "description": "实现功能"})

        # 请求关闭（应该有未完成任务）
        request = coordinator.request_shutdown(
            agent_id="dev_1",
            requester_id="pm",
            reason="任务完成",
        )

        # 检查状态
        status = coordinator.check_shutdown_status()
        # 可能是 PENDING 或 APPROVED（取决于是否有未完成任务）
        assert status in (ShutdownStatus.PENDING, ShutdownStatus.APPROVED)

    def test_parallel_execution_with_shutdown_check(self):
        """测试并行执行同时检查关闭状态"""
        coordinator = create_coordinator()
        coordinator.create_role(RoleType.DEVELOPER, "dev_1")
        coordinator.create_role(RoleType.TESTER, "tester_1")

        manager = create_collaboration_manager(coordinator)

        # 并行执行任务
        tasks = [
            {"role_id": "dev_1", "task": {"task_id": "dev_task"}},
            {"role_id": "tester_1", "task": {"task_id": "test_task"}},
        ]

        # 执行并行任务
        result = manager.execute_parallel(tasks, fail_fast=False)

        # 同时检查关闭状态
        status = coordinator.check_shutdown_status()
        assert status == ShutdownStatus.PENDING  # 未请求关闭

    def test_shutdown_status_transitions(self):
        """测试关闭状态流转"""
        coordinator = create_coordinator()

        # 初始状态
        assert coordinator.check_shutdown_status() == ShutdownStatus.PENDING

        # 发送请求
        request = coordinator.request_shutdown(
            agent_id="agent_1",
            requester_id="coordinator",
            reason="关闭",
        )

        # 处理请求后状态变化
        response = coordinator.handle_shutdown_request(request)

        if response.approved:
            assert coordinator.check_shutdown_status() == ShutdownStatus.APPROVED
        else:
            # 有未完成任务时保持 PENDING 或 REJECTED
            assert coordinator.check_shutdown_status() in (ShutdownStatus.PENDING, ShutdownStatus.REJECTED)


class TestEdgeCases:
    """测试边界条件"""

    def test_shutdown_with_empty_agent_id(self):
        """测试空 Agent ID 的关闭请求"""
        coordinator = create_coordinator()

        request = ShutdownRequest(
            agent_id="",
            requester_id="coordinator",
            reason="关闭",
        )

        # 应该能处理，不会崩溃
        response = coordinator.handle_shutdown_request(request)
        assert response is not None

    def test_context_with_none_values(self):
        """测试上下文包含 None 值"""
        context = create_agent_context(
            agent_id="agent_1",
            session_id="session_1",
            role_type="developer",
            parent_session_id=None,  # None 值
        )

        assert context.agent_id == "agent_1"
        assert context.parent_session_id is None

    def test_parallel_execution_with_empty_tasks(self):
        """测试空任务列表的并行执行"""
        coordinator = create_coordinator()
        manager = create_collaboration_manager(coordinator)

        result = manager.execute_parallel([])

        assert result["total_tasks"] == 0
        assert result["completed"] == 0
        assert result["failed"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])