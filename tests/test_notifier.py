"""
测试用户感知通知模块

验证 UserNotifier 的各项功能:
1. 工作流通知
2. 阶段通知
3. 角色任务通知
4. 积分变化通知
5. 问题发现通知
"""

import pytest
import io
from datetime import datetime

from harnessgenj.notify import (
    UserNotifier,
    NotifierLevel,
    VerbosityMode,
    get_notifier,
    set_notifier,
    enable_notifier,
    set_verbosity,
)


class TestUserNotifier:
    """测试 UserNotifier 类"""

    def test_notifier_creation(self):
        """测试通知器创建"""
        output = io.StringIO()
        notifier = UserNotifier(enabled=True, output=output)
        assert notifier.enabled is True
        assert notifier._output == output

    def test_notify_workflow_start(self):
        """测试工作流开始通知"""
        output = io.StringIO()
        notifier = UserNotifier(enabled=True, output=output)
        notifier.notify_workflow_start("feature", ["design", "development", "testing"])

        content = output.getvalue()
        assert "工作流开始" in content
        assert "feature" in content
        assert "design" in content

    def test_notify_stage_start(self):
        """测试阶段开始通知"""
        output = io.StringIO()
        notifier = UserNotifier(enabled=True, output=output)
        notifier.notify_stage_start("development", "developer_1")

        content = output.getvalue()
        assert "阶段" in content
        assert "development" in content
        assert "developer_1" in content

    def test_notify_role_task(self):
        """测试角色任务通知"""
        output = io.StringIO()
        notifier = UserNotifier(enabled=True, output=output)
        notifier.notify_role_task("Developer", "dev_1", "实现登录功能")

        content = output.getvalue()
        assert "Developer" in content
        assert "dev_1" in content
        assert "实现登录功能" in content

    def test_notify_score_change(self):
        """测试积分变化通知"""
        output = io.StringIO()
        notifier = UserNotifier(enabled=True, output=output)
        notifier.notify_score_change(
            role_id="developer_1",
            role_type="Developer",
            delta=10,
            reason="代码审查通过",
            new_score=85,
        )

        content = output.getvalue()
        assert "Score" in content
        assert "+10" in content
        assert "代码审查通过" in content
        assert "85" in content

    def test_notify_score_negative_change(self):
        """测试负积分变化通知"""
        output = io.StringIO()
        notifier = UserNotifier(enabled=True, output=output)
        notifier.notify_score_change(
            role_id="developer_1",
            role_type="Developer",
            delta=-5,
            reason="发现问题",
            new_score=75,
        )

        content = output.getvalue()
        assert "-5" in content
        assert "发现问题" in content

    def test_notify_issues_found(self):
        """测试发现问题通知"""
        output = io.StringIO()
        notifier = UserNotifier(enabled=True, output=output)
        notifier.notify_issues_found(
            ["缺少类型注解", "潜在空指针", "未处理异常"],
            severity="medium"
        )

        content = output.getvalue()
        assert "发现 3 个问题" in content
        assert "缺少类型注解" in content

    def test_notify_stage_complete(self):
        """测试阶段完成通知"""
        output = io.StringIO()
        notifier = UserNotifier(enabled=True, output=output)
        notifier.notify_stage_complete("development", "completed")

        content = output.getvalue()
        assert "completed" in content
        assert "development" in content

    def test_notify_workflow_complete(self):
        """测试工作流完成通知"""
        output = io.StringIO()
        notifier = UserNotifier(enabled=True, output=output)
        notifier._workflow_start_time = datetime.now()
        notifier.notify_workflow_complete("feature", success=True)

        content = output.getvalue()
        assert "工作流完成" in content
        assert "feature" in content

    def test_notify_task_state(self):
        """测试任务状态变化通知"""
        output = io.StringIO()
        notifier = UserNotifier(enabled=True, output=output)
        notifier.notify_task_state("task_12345", "pending", "in_progress")

        content = output.getvalue()
        assert "pending" in content
        assert "in_progress" in content

    def test_disabled_notifier(self):
        """测试禁用通知器"""
        output = io.StringIO()
        notifier = UserNotifier(enabled=False, output=output)
        notifier.notify_workflow_start("feature", ["design"])

        content = output.getvalue()
        assert content == ""

    def test_verbosity_simple_mode(self):
        """测试简洁模式"""
        output = io.StringIO()
        notifier = UserNotifier(enabled=True, output=output, verbosity=VerbosityMode.SIMPLE)
        notifier.notify_role_task("Developer", "dev_1", "测试任务")  # INFO 级别，简洁模式跳过

        content = output.getvalue()
        assert content == ""  # 简洁模式跳过 INFO 级别

    def test_score_changes_tracking(self):
        """测试积分变化追踪"""
        output = io.StringIO()
        notifier = UserNotifier(enabled=True, output=output)
        notifier.notify_score_change("dev_1", "Developer", 10, "通过", 85)
        notifier.notify_score_change("reviewer_1", "CodeReviewer", 5, "发现问题", 55)

        changes = notifier.get_score_changes()
        assert len(changes) == 2
        assert changes[0]["role_id"] == "dev_1"
        assert changes[1]["role_id"] == "reviewer_1"

    def test_notifier_reset(self):
        """测试通知器重置"""
        output = io.StringIO()
        notifier = UserNotifier(enabled=True, output=output)
        notifier._indent = 3
        notifier._score_changes = [{"test": "data"}]

        notifier.reset()
        assert notifier._indent == 0
        assert notifier._score_changes == []


class TestGlobalNotifier:
    """测试全局通知器管理"""

    def test_get_notifier_singleton(self):
        """测试全局通知器单例"""
        notifier1 = get_notifier()
        notifier2 = get_notifier()
        assert notifier1 is notifier2

    def test_set_notifier(self):
        """测试设置全局通知器"""
        custom_notifier = UserNotifier(enabled=False)
        set_notifier(custom_notifier)
        assert get_notifier() is custom_notifier

        # 恢复默认
        set_notifier(UserNotifier())

    def test_enable_notifier(self):
        """测试启用/禁用通知器"""
        notifier = UserNotifier(enabled=True)
        set_notifier(notifier)

        enable_notifier(False)
        assert get_notifier().enabled is False

        enable_notifier(True)
        assert get_notifier().enabled is True

    def test_set_verbosity(self):
        """测试设置详细程度"""
        notifier = UserNotifier(verbosity=VerbosityMode.DETAILED)
        set_notifier(notifier)

        set_verbosity(VerbosityMode.DEBUG)
        assert get_notifier()._verbosity == VerbosityMode.DEBUG


class TestNotifierIntegration:
    """测试通知器集成"""

    def test_full_workflow_output(self):
        """测试完整工作流输出"""
        output = io.StringIO()
        notifier = UserNotifier(enabled=True, output=output)

        # 模拟完整工作流
        notifier.notify_workflow_start("feature", ["design", "development", "review"])
        notifier.notify_stage_start("design", "architect_1")
        notifier.notify_role_task("Architect", "architect_1", "设计架构")
        notifier.notify_stage_complete("design", "completed")
        notifier.notify_stage_start("development", "developer_1")
        notifier.notify_role_task("Developer", "developer_1", "编写代码")
        notifier.notify_score_change("developer_1", "Developer", -5, "发现问题", 75)
        notifier.notify_issues_found(["缺少类型注解"], "medium")
        notifier.notify_stage_complete("development", "completed")
        notifier.notify_workflow_complete("feature", success=True)

        content = output.getvalue()
        assert "工作流开始" in content
        assert "阶段" in content
        assert "Score" in content
        assert "-5" in content
        assert "工作流完成" in content

    def test_workflow_with_score_summary(self):
        """测试带积分总结的工作流"""
        output = io.StringIO()
        notifier = UserNotifier(enabled=True, output=output, verbosity=VerbosityMode.DETAILED)

        notifier._workflow_start_time = datetime.now()
        notifier.notify_score_change("dev_1", "Developer", 10, "通过", 85)
        notifier.notify_score_change("reviewer_1", "CodeReviewer", 5, "发现问题", 55)
        notifier.notify_workflow_complete("feature", success=True)

        content = output.getvalue()
        assert "积分变化汇总" in content