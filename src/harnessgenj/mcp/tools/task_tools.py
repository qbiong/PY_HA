"""
任务管理工具

提供与任务系统交互的 MCP 工具。
"""

from typing import Any, ClassVar

from harnessgenj.mcp.tools import MCPTool
from harnessgenj.mcp.protocol import MCPToolResult


class TaskCreateTool(MCPTool):
    """创建新任务"""

    name: ClassVar[str] = "task_create"
    description: ClassVar[str] = "创建新的开发任务或 Bug 修复任务"
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "request": {"type": "string", "description": "任务请求描述"},
            "request_type": {
                "type": "string",
                "description": "任务类型 (feature/bug/task)",
                "default": "feature",
            },
        },
        "required": ["request"],
    }
    category: ClassVar[str] = "task"

    def execute(self, params: dict[str, Any], harness: Any) -> MCPToolResult:
        request = params["request"]
        request_type = params.get("request_type", "feature")

        try:
            result = harness.receive_request(request, request_type=request_type)
            if result.get("success"):
                return MCPToolResult.text_result(
                    f"✅ 任务已创建\n"
                    f"任务ID: {result['task_id']}\n"
                    f"优先级: {result['priority']}\n"
                    f"类别: {result['category']}"
                )
            else:
                return MCPToolResult.error_result(f"创建失败: {result.get('error')}")
        except Exception as e:
            return MCPToolResult.error_result(f"创建任务失败: {e}")


class TaskCompleteTool(MCPTool):
    """完成任务"""

    name: ClassVar[str] = "task_complete"
    description: ClassVar[str] = "标记任务为已完成"
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "description": "任务ID"},
            "summary": {"type": "string", "description": "完成摘要"},
        },
        "required": ["task_id"],
    }
    category: ClassVar[str] = "task"

    def execute(self, params: dict[str, Any], harness: Any) -> MCPToolResult:
        task_id = params["task_id"]
        summary = params.get("summary", "")

        try:
            success = harness.complete_task(task_id, summary)
            if success:
                return MCPToolResult.text_result(f"✅ 任务已完成: {task_id}")
            else:
                return MCPToolResult.error_result(f"❌ 任务完成失败: {task_id}")
        except Exception as e:
            return MCPToolResult.error_result(f"完成任务失败: {e}")


class TaskDevelopTool(MCPTool):
    """开发功能"""

    name: ClassVar[str] = "task_develop"
    description: ClassVar[str] = "开发新功能（完整开发流程）"
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "feature_request": {"type": "string", "description": "功能需求描述"},
            "use_tdd": {"type": "boolean", "description": "是否使用 TDD 模式", "default": False},
        },
        "required": ["feature_request"],
    }
    category: ClassVar[str] = "task"

    def execute(self, params: dict[str, Any], harness: Any) -> MCPToolResult:
        feature_request = params["feature_request"]
        use_tdd = params.get("use_tdd", False)

        try:
            result = harness.develop(feature_request, use_tdd=use_tdd)
            status = result.get("status", "unknown")
            task_id = result.get("task_id", "N/A")

            if status == "completed":
                return MCPToolResult.text_result(
                    f"✅ 功能开发完成\n"
                    f"任务ID: {task_id}\n"
                    f"需求: {feature_request[:50]}..."
                )
            else:
                return MCPToolResult.text_result(
                    f"⚠️ 开发状态: {status}\n"
                    f"任务ID: {task_id}"
                )
        except Exception as e:
            return MCPToolResult.error_result(f"开发失败: {e}")


class TaskFixBugTool(MCPTool):
    """修复 Bug"""

    name: ClassVar[str] = "task_fix_bug"
    description: ClassVar[str] = "修复 Bug（完整修复流程）"
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "bug_description": {"type": "string", "description": "Bug 描述"},
        },
        "required": ["bug_description"],
    }
    category: ClassVar[str] = "task"

    def execute(self, params: dict[str, Any], harness: Any) -> MCPToolResult:
        bug_description = params["bug_description"]

        try:
            result = harness.fix_bug(bug_description)
            status = result.get("status", "unknown")
            task_id = result.get("task_id", "N/A")

            if status == "completed":
                return MCPToolResult.text_result(
                    f"✅ Bug 已修复\n"
                    f"任务ID: {task_id}\n"
                    f"问题: {bug_description[:50]}..."
                )
            else:
                return MCPToolResult.text_result(
                    f"⚠️ 修复状态: {status}\n"
                    f"任务ID: {task_id}"
                )
        except Exception as e:
            return MCPToolResult.error_result(f"修复失败: {e}")


class TaskStatusTool(MCPTool):
    """获取任务状态"""

    name: ClassVar[str] = "task_status"
    description: ClassVar[str] = "获取当前任务状态"
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {},
    }
    category: ClassVar[str] = "task"

    def execute(self, params: dict[str, Any], harness: Any) -> MCPToolResult:
        try:
            current_task = harness.memory.get_current_task()
            if current_task:
                return MCPToolResult.text_result(
                    f"📋 当前任务:\n"
                    f"ID: {current_task.get('task_id', 'N/A')}\n"
                    f"请求: {current_task.get('request', 'N/A')[:100]}\n"
                    f"状态: {current_task.get('status', 'N/A')}\n"
                    f"优先级: {current_task.get('priority', 'N/A')}"
                )
            else:
                return MCPToolResult.text_result("📋 当前无进行中的任务")
        except Exception as e:
            return MCPToolResult.error_result(f"获取状态失败: {e}")


class TaskHistoryTool(MCPTool):
    """获取任务历史"""

    name: ClassVar[str] = "task_history"
    description: ClassVar[str] = "获取任务状态变更历史"
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "description": "任务ID"},
        },
        "required": ["task_id"],
    }
    category: ClassVar[str] = "task"

    def execute(self, params: dict[str, Any], harness: Any) -> MCPToolResult:
        task_id = params["task_id"]

        try:
            history = harness.get_task_history(task_id)
            if history:
                lines = [f"📜 任务 {task_id} 历史:"]
                for event in history:
                    lines.append(
                        f"  - {event.get('timestamp', 'N/A')}: "
                        f"{event.get('from_state', '?')} → {event.get('to_state', '?')}"
                    )
                return MCPToolResult.text_result("\n".join(lines))
            else:
                return MCPToolResult.text_result(f"❌ 未找到任务历史: {task_id}")
        except Exception as e:
            return MCPToolResult.error_result(f"获取历史失败: {e}")


# 导出所有任务工具
TASK_TOOLS = [
    TaskCreateTool(),
    TaskCompleteTool(),
    TaskDevelopTool(),
    TaskFixBugTool(),
    TaskStatusTool(),
    TaskHistoryTool(),
]