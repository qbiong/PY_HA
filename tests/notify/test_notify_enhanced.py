"""
Notify 模块增强测试

测试新增功能：
- JSON 输出格式
- 进度条渲染
- 输出缓冲
"""

import pytest
import io
import json

from harnessgenj.notify import (
    UserNotifier,
    NotifierLevel,
    VerbosityMode,
    OutputFormat,
)


class TestOutputFormat:
    """测试输出格式"""

    def test_terminal_format(self):
        """测试终端格式输出"""
        output = io.StringIO()
        notifier = UserNotifier(enabled=True, output=output, format=OutputFormat.TERMINAL)
        notifier.notify_workflow_start("test", ["stage1"])

        content = output.getvalue()
        assert "[HGJ]" in content
        assert "工作流开始" in content

    def test_json_format(self):
        """测试 JSON 格式输出"""
        output = io.StringIO()
        notifier = UserNotifier(enabled=True, output=output, format=OutputFormat.JSON)
        notifier.notify_workflow_start("test", ["stage1"])

        content = output.getvalue()
        # 解析 JSON 行
        lines = [l for l in content.strip().split("\n") if l]
        assert len(lines) >= 1

        # 验证 JSON 格式
        parsed = json.loads(lines[0])
        assert "timestamp" in parsed
        assert "level" in parsed
        assert "message" in parsed


class TestProgressTracking:
    """测试进度追踪"""

    def test_progress_bar_render(self):
        """测试进度条渲染"""
        output = io.StringIO()
        notifier = UserNotifier(enabled=True, output=output)

        # 50% 进度
        bar = notifier._render_progress_bar(5, 10)
        assert "50%" in bar
        assert "[" in bar and "]" in bar

    def test_progress_bar_zero(self):
        """测试零进度"""
        notifier = UserNotifier()
        bar = notifier._render_progress_bar(0, 10)
        assert "0%" in bar

    def test_progress_bar_complete(self):
        """测试完成进度"""
        notifier = UserNotifier()
        bar = notifier._render_progress_bar(10, 10)
        assert "100%" in bar

    def test_progress_bar_over(self):
        """测试超额进度（应限制在100%）"""
        notifier = UserNotifier()
        bar = notifier._render_progress_bar(15, 10)
        assert "100%" in bar

    def test_notify_progress(self):
        """测试进度通知"""
        output = io.StringIO()
        notifier = UserNotifier(enabled=True, output=output)
        notifier.notify_progress("测试操作", 5, 10)

        content = output.getvalue()
        assert "测试操作" in content
        assert "50%" in content

    def test_notify_progress_json_format(self):
        """测试 JSON 格式进度通知"""
        output = io.StringIO()
        notifier = UserNotifier(enabled=True, output=output, format=OutputFormat.JSON)
        notifier.notify_progress("测试操作", 5, 10, "处理中")

        content = output.getvalue()
        parsed = json.loads(content.strip())
        assert parsed["operation"] == "测试操作"
        assert parsed["progress"] == 5
        assert parsed["total"] == 10
        assert parsed["percentage"] == 50.0
        assert parsed["message"] == "处理中"

    def test_complete_progress(self):
        """测试完成进度"""
        output = io.StringIO()
        notifier = UserNotifier(enabled=True, output=output)
        notifier._progress["test_op"] = 5
        notifier.complete_progress("test_op")

        assert "test_op" not in notifier._progress
        content = output.getvalue()
        assert "完成" in content

    def test_get_progress(self):
        """测试获取进度"""
        notifier = UserNotifier()
        notifier._progress["test_op"] = 7.5
        assert notifier.get_progress("test_op") == 7.5
        assert notifier.get_progress("nonexistent") is None


class TestOutputBuffer:
    """测试输出缓冲"""

    def test_enable_buffer(self):
        """测试启用缓冲"""
        notifier = UserNotifier()
        notifier.enable_buffer()
        assert notifier._buffer is not None

    def test_get_buffer(self):
        """测试获取缓冲内容"""
        notifier = UserNotifier()
        notifier.enable_buffer()
        notifier._emit("测试消息", NotifierLevel.INFO)

        content = notifier.get_buffer()
        assert "测试消息" in content

    def test_clear_buffer(self):
        """测试清空缓冲"""
        notifier = UserNotifier()
        notifier.enable_buffer()
        notifier._emit("测试消息", NotifierLevel.INFO)
        notifier.clear_buffer()

        content = notifier.get_buffer()
        assert content == ""

    def test_buffer_with_workflow(self):
        """测试缓冲与工作流"""
        notifier = UserNotifier()
        notifier.enable_buffer()
        notifier.notify_workflow_start("test", ["stage1"])
        notifier.notify_workflow_complete("test", True)

        content = notifier.get_buffer()
        assert "工作流开始" in content
        assert "工作流完成" in content


class TestFormatSwitching:
    """测试格式切换"""

    def test_set_format(self):
        """测试设置格式"""
        notifier = UserNotifier()
        assert notifier._format == OutputFormat.TERMINAL

        notifier.set_format(OutputFormat.JSON)
        assert notifier._format == OutputFormat.JSON


class TestProgressIntegration:
    """测试进度集成"""

    def test_workflow_with_progress(self):
        """测试带进度的工作流"""
        output = io.StringIO()
        notifier = UserNotifier(enabled=True, output=output)

        # 模拟工作流
        notifier.notify_workflow_start("develop", ["design", "code", "test"])
        notifier.notify_progress("设计阶段", 1, 3)
        notifier.notify_progress("编码阶段", 2, 3)
        notifier.notify_progress("测试阶段", 3, 3)
        notifier.notify_workflow_complete("develop", True)

        content = output.getvalue()
        assert "工作流开始" in content
        assert "设计阶段" in content
        assert "编码阶段" in content
        assert "测试阶段" in content
        assert "工作流完成" in content

    def test_reset_clears_progress(self):
        """测试重置清除进度"""
        notifier = UserNotifier()
        notifier._progress["op1"] = 5
        notifier._progress["op2"] = 10

        notifier.reset()
        assert len(notifier._progress) == 0