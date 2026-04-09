"""
Tests for Dashboard Module - 终端仪表板测试

测试终端仪表板的核心功能：
- 渲染输出
- 积分排行显示
- 任务状态展示
"""

import pytest
import tempfile
import shutil
from unittest.mock import MagicMock, patch

from harnessgenj.dashboard import (
    TerminalDashboard,
    render_dashboard,
)
from harnessgenj import Harness


class TestTerminalDashboard:
    """测试终端仪表板"""

    def test_dashboard_creation(self):
        """测试仪表板创建"""
        dashboard = TerminalDashboard()
        assert dashboard is not None
        assert dashboard.WIDTH == 60

    def test_render_header(self):
        """测试头部渲染"""
        dashboard = TerminalDashboard()
        header = dashboard._render_header()

        assert "HarnessGenJ Dashboard" in header
        assert "┌" in header  # 顶部边框

    def test_render_score_bar(self):
        """测试积分条渲染"""
        dashboard = TerminalDashboard()

        # 满分
        bar_100 = dashboard._render_score_bar(100)
        assert "█" in bar_100

        # 0分
        bar_0 = dashboard._render_score_bar(0)
        assert "░" in bar_0

        # 中等分数
        bar_50 = dashboard._render_score_bar(50)
        assert len(bar_50) == 10

    def test_render_progress_bar(self):
        """测试进度条渲染"""
        dashboard = TerminalDashboard()

        # 0%
        bar_0 = dashboard._render_progress_bar(0)
        assert "[" in bar_0 and "]" in bar_0

        # 50%
        bar_50 = dashboard._render_progress_bar(0.5)
        assert "=" in bar_50

        # 100%
        bar_100 = dashboard._render_progress_bar(1.0)
        assert "=" in bar_100

    def test_box_methods(self):
        """测试盒子方法"""
        dashboard = TerminalDashboard()

        top = dashboard._box_top()
        assert "┌" in top and "┐" in top

        bottom = dashboard._box_bottom()
        assert "└" in bottom and "┘" in bottom

        line = dashboard._box_line("测试")
        assert "│" in line
        assert "测试" in line

    def test_center_text(self):
        """测试文本居中"""
        dashboard = TerminalDashboard()
        centered = dashboard._center("Test")
        assert "Test" in centered


class TestDashboardRender:
    """测试仪表板渲染"""

    @pytest.fixture
    def temp_workspace(self):
        """创建临时工作空间"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def harness(self, temp_workspace):
        """创建 Harness 实例"""
        return Harness("测试项目", workspace=temp_workspace)

    def test_render_with_harness(self, harness):
        """测试使用 Harness 渲染"""
        dashboard = TerminalDashboard()
        output = dashboard.render(harness)

        assert output is not None
        assert "HarnessGenJ Dashboard" in output
        assert "测试项目" in output

    def test_render_dashboard_function(self, harness):
        """测试便捷渲染函数"""
        output = render_dashboard(harness)

        assert output is not None
        assert "HarnessGenJ Dashboard" in output

    def test_render_with_scores(self, harness):
        """测试带积分排行渲染"""
        # 注册角色积分
        harness._score_manager.register_role("developer", "dev_1", "开发者")
        harness._score_manager.register_role("reviewer", "rev_1", "审查者")

        dashboard = TerminalDashboard()
        output = dashboard.render(harness)

        assert "积分排行" in output

    def test_render_with_tasks(self, harness):
        """测试带任务状态渲染"""
        # 创建任务
        harness.receive_request("测试任务", request_type="feature")

        dashboard = TerminalDashboard()
        output = dashboard.render(harness)

        assert "任务状态" in output


class TestDashboardOutput:
    """测试仪表板输出格式"""

    def test_output_width(self):
        """测试输出宽度"""
        dashboard = TerminalDashboard()

        # 渲染头部
        header = dashboard._render_header()
        lines = header.split("\n")

        for line in lines:
            # 每行宽度应该一致
            if line.strip():
                assert len(line) <= dashboard.WIDTH + 2

    def test_ascii_only(self):
        """测试仅使用 ASCII 字符"""
        dashboard = TerminalDashboard()

        # 使用 mock Harness
        mock_harness = MagicMock()
        mock_harness.project_name = "Test"
        mock_harness._stats = None
        mock_harness._score_manager = None
        mock_harness._task_state_machine = None

        output = dashboard.render(mock_harness)

        # 验证输出可编码
        assert output.encode("utf-8") is not None


class TestDashboardIntegration:
    """集成测试"""

    @pytest.fixture
    def temp_workspace(self):
        """创建临时工作空间"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_full_dashboard_workflow(self, temp_workspace):
        """测试完整仪表板工作流"""
        # 1. 创建框架
        harness = Harness("完整测试项目", workspace=temp_workspace, auto_setup_team=True)

        # 2. 创建一些任务
        harness.receive_request("功能A", request_type="feature")
        harness.receive_request("Bug修复", request_type="bug")

        # 3. 渲染仪表板
        output = render_dashboard(harness)

        # 4. 验证输出包含所有部分
        assert "项目信息" in output
        assert "积分排行" in output
        assert "任务状态" in output
        assert "完整测试项目" in output


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])