"""
Product Manager Role - 产品经理角色

职责:
- 需求分析与整理
- 用户故事编写
- 优先级排序
- 产品规划

技能:
- analyze_requirement: 需求分析
- write_user_story: 编写用户故事
- prioritize: 优先级排序
- define_acceptance_criteria: 定义验收标准
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


class ProductManager(AgentRole):
    """
    产品经理 - 负责需求管理

    Harness角色定义:
    - 职责边界: 需求分析、优先级、验收标准
    - 技能集: 需求分析、用户故事、优先级
    - 协作: 向Developer交付需求，验收交付物
    """

    @property
    def role_type(self) -> RoleType:
        return RoleType.PRODUCT_MANAGER

    @property
    def responsibilities(self) -> list[str]:
        return [
            "需求收集与分析",
            "用户故事编写",
            "优先级定义与排序",
            "验收标准制定",
            "产品路线规划",
            " stakeholder沟通",
        ]

    def _setup_skills(self) -> None:
        """设置产品技能"""
        skills = [
            RoleSkill(
                name="analyze_requirement",
                description="分析需求",
                category=SkillCategory.ANALYSIS,
                inputs=["user_input", "business_goal"],
                outputs=["requirements", "constraints"],
            ),
            RoleSkill(
                name="write_user_story",
                description="编写用户故事",
                category=SkillCategory.DOCUMENTATION,
                inputs=["requirement"],
                outputs=["user_stories", "acceptance_criteria"],
            ),
            RoleSkill(
                name="prioritize",
                description="优先级排序",
                category=SkillCategory.MANAGEMENT,
                inputs=["requirements", "constraints"],
                outputs=["prioritized_backlog"],
            ),
            RoleSkill(
                name="define_acceptance_criteria",
                description="定义验收标准",
                category=SkillCategory.ANALYSIS,
                inputs=["user_story"],
                outputs=["acceptance_criteria", "test_scenarios"],
            ),
            RoleSkill(
                name="create_roadmap",
                description="创建产品路线图",
                category=SkillCategory.MANAGEMENT,
                inputs=["vision", "constraints"],
                outputs=["roadmap", "milestones"],
            ),
        ]

        for skill in skills:
            self.add_skill(skill)

    def get_supported_task_types(self) -> list[TaskType]:
        return [
            TaskType.ANALYZE_REQUIREMENT,
            TaskType.WRITE_USER_STORY,
            TaskType.PRIORITIZE,
        ]

    def _execute_by_type(self, task_type: TaskType) -> dict[str, Any]:
        handlers = {
            TaskType.ANALYZE_REQUIREMENT: self._analyze_requirement,
            TaskType.WRITE_USER_STORY: self._write_user_story,
            TaskType.PRIORITIZE: self._prioritize,
        }

        handler = handlers.get(task_type)
        if handler:
            return handler()
        return {"status": "error", "message": f"Unsupported task: {task_type}"}

    def _analyze_requirement(self) -> dict[str, Any]:
        """分析需求"""
        user_input = self._current_task.get("inputs", {}).get("user_input", "")

        result = {
            "status": "completed",
            "outputs": {
                "requirements": [
                    {"id": "REQ-001", "description": "核心功能需求"},
                    {"id": "REQ-002", "description": "性能需求"},
                    {"id": "REQ-003", "description": "安全需求"},
                ],
                "constraints": ["技术约束", "时间约束", "资源约束"],
                "analysis_summary": f"需求分析完成: {user_input}",
            },
        }

        self.context.add_artifact("requirements", result["outputs"]["requirements"])
        return result

    def _write_user_story(self) -> dict[str, Any]:
        """编写用户故事"""
        requirement = self._current_task.get("inputs", {}).get("requirement", "")

        result = {
            "status": "completed",
            "outputs": {
                "user_stories": [
                    {
                        "id": "US-001",
                        "as_a": "用户",
                        "i_want_to": "执行某操作",
                        "so_that": "实现某价值",
                        "points": 3,
                    }
                ],
                "acceptance_criteria": [
                    "Given: 前置条件",
                    "When: 执行操作",
                    "Then: 预期结果",
                ],
            },
        }

        self.context.add_artifact("user_stories", result["outputs"]["user_stories"])
        return result

    def _prioritize(self) -> dict[str, Any]:
        """优先级排序"""
        result = {
            "status": "completed",
            "outputs": {
                "prioritized_backlog": [
                    {"id": "US-001", "priority": "P0", "reason": "核心功能"},
                    {"id": "US-002", "priority": "P1", "reason": "重要功能"},
                    {"id": "US-003", "priority": "P2", "reason": "优化功能"},
                ],
            },
        }

        return result


def create_product_manager(
    pm_id: str,
    name: str = "ProductManager",
    context: RoleContext | None = None,
) -> ProductManager:
    """创建产品经理实例"""
    return ProductManager(role_id=pm_id, name=name, context=context)