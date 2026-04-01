"""
Project Manager Role - 项目经理角色

职责:
- 任务协调
- 进度追踪
- 资源分配
- 风险管理

技能:
- coordinate: 协调任务
- track_progress: 进度追踪
- allocate_resources: 资源分配
- manage_risks: 风险管理
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


class ProjectManager(AgentRole):
    """
    项目经理 - 负责任务协调

    Harness角色定义:
    - 职责边界: 任务分配、进度管理、风险管理
    - 技能集: 协调、追踪、资源管理
    - 协作: 协调所有角色，追踪整体进度
    """

    @property
    def role_type(self) -> RoleType:
        return RoleType.PROJECT_MANAGER

    @property
    def responsibilities(self) -> list[str]:
        return [
            "任务分配与协调",
            "进度追踪与报告",
            "资源分配与管理",
            "风险识别与应对",
            "团队沟通协调",
            "里程碑管理",
        ]

    def _setup_skills(self) -> None:
        """设置管理技能"""
        skills = [
            RoleSkill(
                name="coordinate",
                description="协调任务",
                category=SkillCategory.MANAGEMENT,
                inputs=["tasks", "team"],
                outputs=["assignments", "schedule"],
            ),
            RoleSkill(
                name="track_progress",
                description="进度追踪",
                category=SkillCategory.MANAGEMENT,
                inputs=["tasks", "milestones"],
                outputs=["progress_report", "blockers"],
            ),
            RoleSkill(
                name="allocate_resources",
                description="资源分配",
                category=SkillCategory.MANAGEMENT,
                inputs=["requirements", "availability"],
                outputs=["resource_plan"],
            ),
            RoleSkill(
                name="manage_risks",
                description="风险管理",
                category=SkillCategory.MANAGEMENT,
                inputs=["project_context"],
                outputs=["risk_register", "mitigation_plan"],
            ),
        ]

        for skill in skills:
            self.add_skill(skill)

    def get_supported_task_types(self) -> list[TaskType]:
        return [
            TaskType.COORDINATE,
            TaskType.TRACK_PROGRESS,
        ]

    def _execute_by_type(self, task_type: TaskType) -> dict[str, Any]:
        handlers = {
            TaskType.COORDINATE: self._coordinate,
            TaskType.TRACK_PROGRESS: self._track_progress,
        }

        handler = handlers.get(task_type)
        if handler:
            return handler()
        return {"status": "error", "message": f"Unsupported task: {task_type}"}

    def _coordinate(self) -> dict[str, Any]:
        """协调任务"""
        tasks = self._current_task.get("inputs", {}).get("tasks", [])

        result = {
            "status": "completed",
            "outputs": {
                "assignments": [
                    {"task": t, "assignee": f"role_{i}", "deadline": "2024-01-01"}
                    for i, t in enumerate(tasks[:5])
                ],
                "schedule": {
                    "sprint": "Sprint 1",
                    "duration": "2 weeks",
                    "start_date": "2024-01-01",
                },
            },
        }

        return result

    def _track_progress(self) -> dict[str, Any]:
        """进度追踪"""
        result = {
            "status": "completed",
            "outputs": {
                "progress_report": {
                    "total_tasks": 20,
                    "completed": 12,
                    "in_progress": 5,
                    "blocked": 3,
                    "completion_rate": "60%",
                },
                "blockers": [
                    {"task": "TASK-005", "reason": "等待外部依赖"},
                ],
                "recommendations": [
                    "建议增加资源处理阻塞任务",
                ],
            },
        }

        return result


def create_project_manager(
    pm_id: str,
    name: str = "ProjectManager",
    context: RoleContext | None = None,
) -> ProjectManager:
    """创建项目经理实例"""
    return ProjectManager(role_id=pm_id, name=name, context=context)