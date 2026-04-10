"""
测试 Agent Context 上下文隔离

测试内容:
1. AgentContext 创建和运行
2. contextvars 上下文隔离
3. TeammateContext 支持
4. 权限上下文隔离
"""

import pytest
from harnessgenj.utils.agent_context import (
    AgentContext,
    TeammateContext,
    get_agent_context,
    get_agent_id,
    run_in_agent_context,
    create_agent_context,
    get_teammate_context,
    run_in_teammate_context,
    create_teammate_context,
    get_permission_context,
    run_in_permission_context,
    request_permission_from_parent,
    is_in_agent_context,
    is_in_teammate_context,
    get_context_summary,
)


class TestAgentContextBasics:
    """测试 AgentContext 基础功能"""

    def test_create_agent_context(self):
        """测试创建 AgentContext"""
        ctx = create_agent_context(
            agent_id="developer_1",
            session_id="session_123",
            role_type="developer",
        )

        assert ctx.agent_id == "developer_1"
        assert ctx.session_id == "session_123"
        assert ctx.role_type == "developer"
        assert ctx.is_subagent == False
        assert ctx.permission_mode == "inherit"

    def test_create_subagent_context(self):
        """测试创建子代理上下文"""
        ctx = create_agent_context(
            agent_id="worker_1",
            session_id="session_456",
            role_type="worker",
            parent_session_id="session_123",
            permission_mode="bubble",
        )

        assert ctx.is_subagent == True
        assert ctx.parent_session_id == "session_123"
        assert ctx.permission_mode == "bubble"

    def test_agent_context_with_permissions(self):
        """测试带权限的上下文"""
        ctx = create_agent_context(
            agent_id="developer_1",
            session_id="session_123",
            permitted_files={"src/main.py": {"operation": "write"}},
        )

        assert ctx.permitted_files == {"src/main.py": {"operation": "write"}}


class TestContextVarsIsolation:
    """测试 contextvars 上下文隔离"""

    def test_get_agent_context_outside(self):
        """测试在上下文外获取"""
        assert get_agent_context() is None
        assert get_agent_id() == "main"
        assert is_in_agent_context() == False

    def test_run_in_agent_context(self):
        """测试在上下文中运行"""
        ctx = create_agent_context(
            agent_id="developer_1",
            session_id="session_123",
        )

        def check_context():
            current = get_agent_context()
            assert current is not None
            assert current.agent_id == "developer_1"
            assert get_agent_id() == "developer_1"
            assert is_in_agent_context() == True
            return "success"

        result = run_in_agent_context(ctx, check_context)
        assert result == "success"

        # 退出上下文后
        assert get_agent_context() is None
        assert get_agent_id() == "main"

    def test_nested_context_isolation(self):
        """测试嵌套上下文隔离"""
        outer_ctx = create_agent_context(
            agent_id="outer_agent",
            session_id="session_outer",
        )

        inner_ctx = create_agent_context(
            agent_id="inner_agent",
            session_id="session_inner",
            parent_session_id="session_outer",
        )

        def outer_fn():
            assert get_agent_id() == "outer_agent"

            def inner_fn():
                assert get_agent_id() == "inner_agent"
                inner_current = get_agent_context()
                assert inner_current.is_subagent == True
                return "inner_result"

            inner_result = run_in_agent_context(inner_ctx, inner_fn)
            assert inner_result == "inner_result"

            # 回到 outer 上下文
            assert get_agent_id() == "outer_agent"
            return "outer_result"

        result = run_in_agent_context(outer_ctx, outer_fn)
        assert result == "outer_result"


class TestTeammateContext:
    """测试 TeammateContext"""

    def test_create_teammate_context(self):
        """测试创建 TeammateContext"""
        agent_ctx = create_agent_context(
            agent_id="teammate_1",
            session_id="session_team",
        )

        teammate_ctx = create_teammate_context(
            agent_context=agent_ctx,
            team_name="my_team",
            mailbox_path="/path/to/mailbox",
        )

        assert teammate_ctx.team_name == "my_team"
        assert teammate_ctx.identity.agent_id == "teammate_1"
        assert teammate_ctx.is_running == True
        assert teammate_ctx.shutdown_requested == False

    def test_run_in_teammate_context(self):
        """测试在 Teammate 上下文中运行"""
        agent_ctx = create_agent_context(
            agent_id="worker_1",
            session_id="session_worker",
        )

        teammate_ctx = create_teammate_context(
            agent_context=agent_ctx,
            team_name="test_team",
        )

        def check_teammate():
            assert is_in_teammate_context() == True
            current = get_teammate_context()
            assert current.team_name == "test_team"
            return "teammate_success"

        result = run_in_teammate_context(teammate_ctx, check_teammate)
        assert result == "teammate_success"

        # 退出上下文
        assert is_in_teammate_context() == False


class TestPermissionContext:
    """测试权限上下文"""

    def test_run_in_permission_context(self):
        """测试权限上下文"""
        perm_ctx = {
            "mode": "strict",
            "allowed_tools": ["Read", "Write"],
        }

        def check_permission():
            current = get_permission_context()
            assert current is not None
            assert current["mode"] == "strict"
            return "perm_success"

        result = run_in_permission_context(perm_ctx, check_permission)
        assert result == "perm_success"

    def test_permission_bubble_mode(self):
        """测试气泡权限模式"""
        agent_ctx = create_agent_context(
            agent_id="worker_1",
            session_id="session_worker",
            parent_session_id="session_parent",
            permission_mode="bubble",
        )

        def request_perm():
            response = request_permission_from_parent({"tool": "Edit"})
            assert response["approved"] == True
            assert response["reason"] == "Bubbled to parent"
            return response

        result = run_in_agent_context(agent_ctx, request_perm)
        assert result["parent_session_id"] == "session_parent"


class TestContextSummary:
    """测试上下文摘要"""

    def test_summary_outside_context(self):
        """测试上下文外摘要"""
        summary = get_context_summary()

        assert summary["in_agent_context"] == False
        assert summary["in_teammate_context"] == False
        assert summary["agent_id"] == "main"

    def test_summary_in_agent_context(self):
        """测试 Agent 上下文摘要"""
        ctx = create_agent_context(
            agent_id="developer_1",
            session_id="session_123",
            role_type="developer",
        )

        def get_summary():
            return get_context_summary()

        summary = run_in_agent_context(ctx, get_summary)

        assert summary["in_agent_context"] == True
        assert summary["agent_id"] == "developer_1"
        assert summary["role_type"] == "developer"
        assert summary["is_subagent"] == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])