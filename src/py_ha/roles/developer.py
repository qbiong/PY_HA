"""
Developer Role - 开发人员角色

职责:
- 功能实现
- Bug修复
- 代码重构
- 代码审查

技能:
- implement_feature: 实现功能
- fix_bug: 修复Bug
- refactor_code: 重构代码
- review_code: 代码审查
- debug: 调试
- write_code: 编写代码
"""

from typing import Any
from py_ha.roles.base import (
    AgentRole,
    RoleType,
    RoleSkill,
    RoleContext,
    SkillCategory,
    TaskType,
)


class Developer(AgentRole):
    """
    开发人员 - 负责代码实现

    Harness角色定义:
    - 职责边界: 编码实现、Bug修复、代码质量
    - 技能集: 编码、调试、重构、审查
    - 协作: 接收PM需求，交付Tester测试
    """

    @property
    def role_type(self) -> RoleType:
        return RoleType.DEVELOPER

    @property
    def responsibilities(self) -> list[str]:
        return [
            "功能开发与实现",
            "Bug诊断与修复",
            "代码重构与优化",
            "代码审查与改进",
            "技术文档编写",
            "单元测试编写",
        ]

    def _setup_skills(self) -> None:
        """设置开发技能"""
        skills = [
            RoleSkill(
                name="implement_feature",
                description="实现新功能",
                category=SkillCategory.CODING,
                inputs=["requirement", "design"],
                outputs=["code", "tests"],
            ),
            RoleSkill(
                name="fix_bug",
                description="修复Bug",
                category=SkillCategory.CODING,
                inputs=["bug_report", "codebase"],
                outputs=["fixed_code", "test_case"],
            ),
            RoleSkill(
                name="refactor_code",
                description="重构代码",
                category=SkillCategory.CODING,
                inputs=["code", "refactor_goal"],
                outputs=["refactored_code"],
            ),
            RoleSkill(
                name="review_code",
                description="代码审查",
                category=SkillCategory.CODING,
                inputs=["code"],
                outputs=["review_comments", "approved"],
            ),
            RoleSkill(
                name="debug",
                description="调试代码",
                category=SkillCategory.CODING,
                inputs=["error_info", "code"],
                outputs=["root_cause", "fix"],
            ),
            RoleSkill(
                name="write_unit_test",
                description="编写单元测试",
                category=SkillCategory.TESTING,
                inputs=["code", "test_requirements"],
                outputs=["test_code", "coverage"],
            ),
        ]

        for skill in skills:
            self.add_skill(skill)

    def get_supported_task_types(self) -> list[TaskType]:
        return [
            TaskType.IMPLEMENT_FEATURE,
            TaskType.FIX_BUG,
            TaskType.REFACTOR,
            TaskType.CODE_REVIEW,
        ]

    def _execute_by_type(self, task_type: TaskType) -> dict[str, Any]:
        """执行开发任务"""
        handlers = {
            TaskType.IMPLEMENT_FEATURE: self._implement_feature,
            TaskType.FIX_BUG: self._fix_bug,
            TaskType.REFACTOR: self._refactor_code,
            TaskType.CODE_REVIEW: self._review_code,
        }

        handler = handlers.get(task_type)
        if handler:
            return handler()
        return {"status": "error", "message": f"Unsupported task: {task_type}"}

    # ==================== 任务执行方法 ====================

    def _implement_feature(self) -> dict[str, Any]:
        """实现功能"""
        requirement = self._current_task.get("inputs", {}).get("requirement", "")
        design = self._current_task.get("inputs", {}).get("design", "")

        # 模拟实现过程
        result = {
            "status": "completed",
            "outputs": {
                "code": f"# 实现代码: {requirement}",
                "tests": "# 单元测试",
                "implementation_notes": "功能实现完成",
            },
            "metrics": {
                "lines_added": 100,
                "lines_removed": 0,
                "files_changed": 3,
            },
        }

        self.context.add_artifact("code", result["outputs"]["code"])
        return result

    def _fix_bug(self) -> dict[str, Any]:
        """修复Bug"""
        bug_report = self._current_task.get("inputs", {}).get("bug_report", "")

        result = {
            "status": "completed",
            "outputs": {
                "fixed_code": f"# Bug修复: {bug_report}",
                "test_case": "# 回归测试",
                "root_cause": "问题根因分析",
            },
            "metrics": {
                "fix_time": "30min",
                "affected_files": 1,
            },
        }

        self.context.add_artifact("bug_fix", result["outputs"]["fixed_code"])
        return result

    def _refactor_code(self) -> dict[str, Any]:
        """重构代码"""
        refactor_goal = self._current_task.get("inputs", {}).get("refactor_goal", "")

        result = {
            "status": "completed",
            "outputs": {
                "refactored_code": f"# 重构后代码: {refactor_goal}",
                "refactor_summary": "重构完成",
            },
            "metrics": {
                "complexity_reduction": "20%",
                "duplication_removed": "15%",
            },
        }

        return result

    def _review_code(self) -> dict[str, Any]:
        """代码审查"""
        code = self._current_task.get("inputs", {}).get("code", "")

        result = {
            "status": "completed",
            "outputs": {
                "review_comments": [
                    {"line": 10, "comment": "建议使用更清晰的变量名"},
                    {"line": 25, "comment": "可以提取为独立函数"},
                ],
                "approved": True,
                "suggestions": ["添加类型注解", "增加文档字符串"],
            },
        }

        return result


# ==================== 便捷创建函数 ====================

def create_developer(
    developer_id: str,
    name: str = "Developer",
    context: RoleContext | None = None,
) -> Developer:
    """创建开发人员实例"""
    return Developer(role_id=developer_id, name=name, context=context)