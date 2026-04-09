"""
系统工具

提供系统状态和信息查询的 MCP 工具。
"""

from typing import Any, ClassVar

from harnessgenj.mcp.tools import MCPTool
from harnessgenj.mcp.protocol import MCPToolResult


class SystemStatusTool(MCPTool):
    """获取系统状态"""

    name: ClassVar[str] = "system_status"
    description: ClassVar[str] = "获取 HarnessGenJ 框架的整体状态"
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {},
    }
    category: ClassVar[str] = "system"

    def execute(self, params: dict[str, Any], harness: Any) -> MCPToolResult:
        try:
            status = harness.get_status()
            result = f"""📊 HarnessGenJ 状态
━━━━━━━━━━━━━━━━━━━━━━
项目: {status.get('project', 'Unknown')}

团队:
  规模: {status.get('team', {}).get('size', 0)} 人

统计:
  功能开发: {status.get('stats', {}).get('features_developed', 0)}
  Bug修复: {status.get('stats', {}).get('bugs_fixed', 0)}
  工作流完成: {status.get('stats', {}).get('workflows_completed', 0)}

持久化:
  启用: {status.get('persistence', {}).get('enabled', False)}
  工作空间: {status.get('persistence', {}).get('workspace', 'N/A')}
"""
            return MCPToolResult.text_result(result)
        except Exception as e:
            return MCPToolResult.error_result(f"获取状态失败: {e}")


class SystemHealthTool(MCPTool):
    """获取系统健康度"""

    name: ClassVar[str] = "system_health"
    description: ClassVar[str] = "获取系统健康度分析和改进建议"
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {},
    }
    category: ClassVar[str] = "system"

    def execute(self, params: dict[str, Any], harness: Any) -> MCPToolResult:
        try:
            analysis = harness.get_system_analysis()
            health_score = analysis.get('system_health_score', 0)

            result = f"""🏥 系统健康度分析
━━━━━━━━━━━━━━━━━━━━━━
健康度得分: {health_score:.1f}/100

分析任务数: {analysis.get('total_tasks_analyzed', 0)}

生成器薄弱点:
"""
            for weakness in analysis.get('generator_weaknesses', [])[:3]:
                result += f"  - {weakness.get('role_id')}: {weakness.get('weakness_type')} (频率: {weakness.get('frequency')})\n"

            result += "\n改进建议:\n"
            for suggestion in analysis.get('improvement_actions', [])[:5]:
                result += f"  - {suggestion}\n"

            return MCPToolResult.text_result(result)
        except Exception as e:
            return MCPToolResult.error_result(f"健康度分析失败: {e}")


class SystemScoreboardTool(MCPTool):
    """获取积分排行"""

    name: ClassVar[str] = "system_scoreboard"
    description: ClassVar[str] = "获取角色积分排行榜"
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "role_type": {"type": "string", "description": "筛选角色类型（可选）"},
        },
    }
    category: ClassVar[str] = "system"

    def execute(self, params: dict[str, Any], harness: Any) -> MCPToolResult:
        role_type = params.get("role_type")

        try:
            leaderboard = harness.get_score_leaderboard(role_type)

            result = "🏆 积分排行榜\n━━━━━━━━━━━━━━━━━━━━━━\n"

            for i, entry in enumerate(leaderboard[:10], 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                result += f"{medal} {entry.get('role_name', 'Unknown')}: {entry.get('score', 0)} 分 ({entry.get('grade', 'N/A')})\n"

            return MCPToolResult.text_result(result)
        except Exception as e:
            return MCPToolResult.error_result(f"获取排行失败: {e}")


class SystemReportTool(MCPTool):
    """生成项目报告"""

    name: ClassVar[str] = "system_report"
    description: ClassVar[str] = "生成项目进度报告"
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {},
    }
    category: ClassVar[str] = "system"

    def execute(self, params: dict[str, Any], harness: Any) -> MCPToolResult:
        try:
            report = harness.get_report()
            return MCPToolResult.text_result(report)
        except Exception as e:
            return MCPToolResult.error_result(f"生成报告失败: {e}")


class SystemReviewTool(MCPTool):
    """快速代码审查"""

    name: ClassVar[str] = "system_review"
    description: ClassVar[str] = "对代码进行快速审查"
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "待审查的代码"},
            "use_hunter": {"type": "boolean", "description": "是否使用 BugHunter", "default": False},
        },
        "required": ["code"],
    }
    category: ClassVar[str] = "system"

    def execute(self, params: dict[str, Any], harness: Any) -> MCPToolResult:
        code = params["code"]
        use_hunter = params.get("use_hunter", False)

        try:
            passed, issues = harness.quick_review(code, use_hunter=use_hunter)

            if passed:
                return MCPToolResult.text_result("✅ 代码审查通过，未发现问题")
            else:
                result = "⚠️ 代码审查发现问题:\n"
                for issue in issues:
                    result += f"  - {issue}\n"
                return MCPToolResult.text_result(result)
        except Exception as e:
            return MCPToolResult.error_result(f"审查失败: {e}")


# 导出所有系统工具
SYSTEM_TOOLS = [
    SystemStatusTool(),
    SystemHealthTool(),
    SystemScoreboardTool(),
    SystemReportTool(),
    SystemReviewTool(),
]