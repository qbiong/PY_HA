"""
TUI Dashboard Module - 终端仪表板模块

提供轻量级的终端可视化界面：
- ASCII 艺术渲染
- 项目状态概览
- 积分排行榜
- 任务进度展示
- 零外部依赖
"""

from harnessgenj.dashboard.tui import TerminalDashboard, render_dashboard

__all__ = [
    "TerminalDashboard",
    "render_dashboard",
]