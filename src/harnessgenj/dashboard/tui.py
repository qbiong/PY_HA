"""
Terminal Dashboard - 终端仪表板实现

轻量级 ASCII 终端仪表板，零外部依赖。
"""

import time
from datetime import datetime
from typing import Any


class TerminalDashboard:
    """
    终端仪表板

    提供项目状态可视化展示：
    - 项目基本信息
    - 角色积分排行
    - 任务进度
    - 工作流状态
    """

    WIDTH = 60
    BOX_CHAR = {
        "h": "─",
        "v": "│",
        "tl": "┌",
        "tr": "┐",
        "bl": "└",
        "br": "┘",
    }

    def __init__(self) -> None:
        """初始化仪表板"""
        self._last_render = ""

    def render(self, harness: Any) -> str:
        """
        渲染仪表板

        Args:
            harness: Harness 实例

        Returns:
            渲染后的字符串
        """
        lines = []

        # 1. 头部
        lines.append(self._render_header())

        # 2. 项目状态
        lines.append(self._render_project_status(harness))

        # 3. 积分排行
        lines.append(self._render_scores(harness))

        # 4. 任务状态
        lines.append(self._render_tasks(harness))

        # 5. 底部
        lines.append(self._render_footer())

        self._last_render = "\n".join(lines)
        return self._last_render

    def _render_header(self) -> str:
        """渲染头部"""
        lines = []
        lines.append(self._box_top())
        lines.append(self._box_line(self._center("HarnessGenJ Dashboard")))
        lines.append(self._box_line(f"  📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"))
        lines.append(self._box_separator())
        return "\n".join(lines)

    def _render_project_status(self, harness: Any) -> str:
        """渲染项目状态"""
        lines = []

        # 项目信息
        lines.append(self._box_line("  📦 项目信息"))
        lines.append(self._box_line(f"     名称: {harness.project_name}"))
        lines.append(self._box_line(f"     工作空间: {getattr(harness, 'workspace', 'N/A')}"))

        # 统计信息
        stats = getattr(harness, '_stats', None)
        if stats:
            lines.append(self._box_line(""))
            lines.append(self._box_line("  📊 统计"))
            lines.append(self._box_line(f"     功能开发: {getattr(stats, 'features_developed', 0)}"))
            lines.append(self._box_line(f"     Bug修复: {getattr(stats, 'bugs_fixed', 0)}"))
            lines.append(self._box_line(f"     代码审查: {getattr(stats, 'reviews_passed', 0)}"))

        lines.append(self._box_separator())
        return "\n".join(lines)

    def _render_scores(self, harness: Any) -> str:
        """渲染积分排行"""
        lines = []
        lines.append(self._box_line("  🏆 积分排行"))

        score_manager = getattr(harness, '_score_manager', None)
        if score_manager:
            leaderboard = score_manager.get_leaderboard()
            for i, entry in enumerate(leaderboard[:5]):  # 显示前5名
                role_id = entry.get("role_id", "unknown")
                score = entry.get("score", 0)
                bar = self._render_score_bar(score)
                lines.append(self._box_line(f"     {i+1}. {role_id[:15]:<15} {bar} {score}"))
        else:
            lines.append(self._box_line("     暂无积分数据"))

        lines.append(self._box_separator())
        return "\n".join(lines)

    def _render_tasks(self, harness: Any) -> str:
        """渲染任务状态"""
        lines = []
        lines.append(self._box_line("  📋 任务状态"))

        task_state = getattr(harness, '_task_state_machine', None)
        if task_state:
            stats = task_state.get_stats()
            total = stats.get("total_tasks", 0)
            completed = stats.get("completed", 0)
            in_progress = stats.get("in_progress", 0)
            pending = stats.get("pending", 0)

            lines.append(self._box_line(f"     总任务: {total}"))
            lines.append(self._box_line(f"     ✅ 完成: {completed}"))
            lines.append(self._box_line(f"     🔄 进行中: {in_progress}"))
            lines.append(self._box_line(f"     ⏳ 待处理: {pending}"))

            # 进度条
            if total > 0:
                progress = completed / total
                bar = self._render_progress_bar(progress)
                lines.append(self._box_line(f"     进度: {bar} {progress:.0%}"))
        else:
            lines.append(self._box_line("     暂无任务数据"))

        return "\n".join(lines)

    def _render_footer(self) -> str:
        """渲染底部"""
        return self._box_bottom()

    def _render_score_bar(self, score: int, width: int = 10) -> str:
        """渲染积分条"""
        # 积分范围 0-150，映射到 width
        ratio = min(1.0, score / 100)
        filled = int(width * ratio)
        bar = "█" * filled + "░" * (width - filled)
        return bar

    def _render_progress_bar(self, progress: float, width: int = 20) -> str:
        """渲染进度条"""
        filled = int(width * progress)
        bar = "=" * filled + ">" + " " * (width - filled - 1)
        return f"[{bar}]"

    def _box_top(self) -> str:
        """盒子顶部"""
        return self.BOX_CHAR["tl"] + self.BOX_CHAR["h"] * (self.WIDTH - 2) + self.BOX_CHAR["tr"]

    def _box_bottom(self) -> str:
        """盒子底部"""
        return self.BOX_CHAR["bl"] + self.BOX_CHAR["h"] * (self.WIDTH - 2) + self.BOX_CHAR["br"]

    def _box_line(self, text: str) -> str:
        """盒子行"""
        # 截断或填充
        text = text[: self.WIDTH - 4]
        padding = self.WIDTH - 4 - len(text)
        return self.BOX_CHAR["v"] + " " + text + " " * padding + " " + self.BOX_CHAR["v"]

    def _box_separator(self) -> str:
        """盒子分隔线"""
        return self.BOX_CHAR["v"] + " " + "─" * (self.WIDTH - 4) + " " + self.BOX_CHAR["v"]

    def _center(self, text: str) -> str:
        """居中文本"""
        padding = (self.WIDTH - 4 - len(text)) // 2
        return " " * padding + text + " " * padding


def render_dashboard(harness: Any) -> str:
    """
    渲染仪表板（便捷函数）

    Args:
        harness: Harness 实例

    Returns:
        渲染后的字符串
    """
    dashboard = TerminalDashboard()
    return dashboard.render(harness)


def print_dashboard(harness: Any) -> None:
    """
    打印仪表板到终端

    Args:
        harness: Harness 实例
    """
    dashboard = TerminalDashboard()
    print(dashboard.render(harness))