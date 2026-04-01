"""
Harness - Harness Engineering 主入口

提供简洁的 API 来使用 Harness Engineering 框架

核心概念:
- Team: 开发团队，包含多个角色
- Pipeline: 工作流流水线
- Task: 待执行的任务

使用示例:
    from py_ha import Harness

    # 创建 Harness 实例
    harness = Harness()

    # 快速开发功能
    result = harness.develop("实现用户登录功能")

    # 快速修复 Bug
    result = harness.fix_bug("登录页面无法提交表单")
"""

from typing import Any
from pydantic import BaseModel, Field
import time

from py_ha.roles import (
    AgentRole,
    RoleType,
    create_role,
)
from py_ha.workflow import (
    WorkflowCoordinator,
    WorkflowPipeline,
    create_standard_pipeline,
    create_feature_pipeline,
    create_bugfix_pipeline,
)
from py_ha.memory import MemoryManager
from py_ha.storage import create_storage


class HarnessStats(BaseModel):
    """Harness 统计"""

    features_developed: int = Field(default=0, description="开发的功能数")
    bugs_fixed: int = Field(default=0, description="修复的Bug数")
    workflows_completed: int = Field(default=0, description="完成的工作流数")
    team_size: int = Field(default=0, description="团队规模")


class Harness:
    """
    Harness - Harness Engineering 主入口类

    提供简洁的 API 来管理开发团队和工作流

    核心方法:
    - setup_team(): 组建开发团队
    - develop(): 快速开发功能
    - fix_bug(): 快速修复Bug
    - analyze(): 分析需求
    - review(): 代码审查

    使用示例:
        harness = Harness()
        harness.setup_team()  # 创建默认团队
        result = harness.develop("用户登录功能")
    """

    def __init__(self, project_name: str = "Default Project") -> None:
        self.project_name = project_name
        self.coordinator = WorkflowCoordinator()
        self.memory = MemoryManager()
        self.storage = create_storage()
        self._stats = HarnessStats()

        # 注册标准工作流
        self.coordinator.register_workflow("standard", create_standard_pipeline())
        self.coordinator.register_workflow("feature", create_feature_pipeline())
        self.coordinator.register_workflow("bugfix", create_bugfix_pipeline())

    # ==================== 团队管理 ====================

    def setup_team(self, team_config: dict[str, str] | None = None) -> dict[str, Any]:
        """
        组建开发团队

        Args:
            team_config: 团队配置，key=角色类型，value=角色名称
                        默认创建完整团队

        Returns:
            团队信息

        Examples:
            # 默认团队
            harness.setup_team()

            # 自定义团队
            harness.setup_team({
                "developer": "小李",
                "tester": "小张",
            })
        """
        if team_config is None:
            # 默认团队配置
            team_config = {
                "product_manager": "产品经理",
                "architect": "架构师",
                "developer": "开发人员",
                "tester": "测试人员",
                "doc_writer": "文档管理员",
                "project_manager": "项目经理",
            }

        role_type_map = {
            "product_manager": RoleType.PRODUCT_MANAGER,
            "architect": RoleType.ARCHITECT,
            "developer": RoleType.DEVELOPER,
            "tester": RoleType.TESTER,
            "doc_writer": RoleType.DOC_WRITER,
            "project_manager": RoleType.PROJECT_MANAGER,
        }

        created = []
        for role_type_str, name in team_config.items():
            role_type = role_type_map.get(role_type_str)
            if role_type:
                role_id = f"{role_type_str}_1"
                self.coordinator.create_role(role_type, role_id, name)
                created.append({"type": role_type_str, "name": name, "id": role_id})

        self._stats.team_size = len(created)

        return {
            "project": self.project_name,
            "team_size": len(created),
            "members": created,
        }

    def add_role(self, role_type: str, name: str) -> AgentRole:
        """
        添加单个角色

        Args:
            role_type: 角色类型 (developer, tester, product_manager 等)
            name: 角色名称

        Returns:
            创建的角色实例
        """
        role_type_map = {
            "product_manager": RoleType.PRODUCT_MANAGER,
            "architect": RoleType.ARCHITECT,
            "developer": RoleType.DEVELOPER,
            "tester": RoleType.TESTER,
            "doc_writer": RoleType.DOC_WRITER,
            "project_manager": RoleType.PROJECT_MANAGER,
        }

        rt = role_type_map.get(role_type.lower())
        if not rt:
            raise ValueError(f"Unknown role type: {role_type}")

        import uuid
        role_id = f"{role_type}_{uuid.uuid4().hex[:6]}"
        role = self.coordinator.create_role(rt, role_id, name)
        self._stats.team_size += 1

        return role

    def get_team(self) -> list[dict[str, Any]]:
        """获取团队信息"""
        return self.coordinator.list_roles()

    # ==================== 快速开发 ====================

    def develop(self, feature_request: str) -> dict[str, Any]:
        """
        快速开发功能

        一键完成: 需求分析 → 开发实现 → 测试验证

        Args:
            feature_request: 功能需求描述

        Returns:
            开发结果

        Examples:
            result = harness.develop("实现用户登录功能")
        """
        # 确保有足够的角色
        if not self.coordinator.get_roles_by_type(RoleType.PRODUCT_MANAGER):
            self.coordinator.create_role(RoleType.PRODUCT_MANAGER, "pm_auto", "产品经理")
        if not self.coordinator.get_roles_by_type(RoleType.DEVELOPER):
            self.coordinator.create_role(RoleType.DEVELOPER, "dev_auto", "开发人员")
        if not self.coordinator.get_roles_by_type(RoleType.TESTER):
            self.coordinator.create_role(RoleType.TESTER, "test_auto", "测试人员")

        result = self.coordinator.run_workflow(
            "feature",
            {"feature_request": feature_request},
        )

        if result.get("status") == "completed":
            self._stats.features_developed += 1
            self._stats.workflows_completed += 1

            # 保存到记忆
            self.memory.store_conversation(
                f"功能开发: {feature_request}",
                role="system",
                importance=70,
            )

        return {
            "request": feature_request,
            "status": result.get("status"),
            "stages_completed": len(result.get("results", [])),
            "artifacts": result.get("artifacts", []),
        }

    def fix_bug(self, bug_description: str) -> dict[str, Any]:
        """
        快速修复 Bug

        一键完成: Bug分析 → 代码修复 → 验证测试

        Args:
            bug_description: Bug 描述

        Returns:
            修复结果

        Examples:
            result = harness.fix_bug("登录页面无法提交表单")
        """
        # 确保有足够的角色
        if not self.coordinator.get_roles_by_type(RoleType.DEVELOPER):
            self.coordinator.create_role(RoleType.DEVELOPER, "dev_auto", "开发人员")
        if not self.coordinator.get_roles_by_type(RoleType.TESTER):
            self.coordinator.create_role(RoleType.TESTER, "test_auto", "测试人员")

        result = self.coordinator.run_workflow(
            "bugfix",
            {"bug_report": bug_description},
        )

        if result.get("status") == "completed":
            self._stats.bugs_fixed += 1
            self._stats.workflows_completed += 1

            # 保存到记忆
            self.memory.store_conversation(
                f"Bug修复: {bug_description}",
                role="system",
                importance=60,
            )

        return {
            "bug": bug_description,
            "status": result.get("status"),
            "stages_completed": len(result.get("results", [])),
        }

    def analyze(self, requirement: str) -> dict[str, Any]:
        """
        分析需求

        Args:
            requirement: 需求描述

        Returns:
            分析结果
        """
        if not self.coordinator.get_roles_by_type(RoleType.PRODUCT_MANAGER):
            self.coordinator.create_role(RoleType.PRODUCT_MANAGER, "pm_auto", "产品经理")

        pm = self.coordinator.get_roles_by_type(RoleType.PRODUCT_MANAGER)[0]

        pm.assign_task({
            "type": "requirements",
            "description": f"分析需求: {requirement}",
            "inputs": {"user_input": requirement},
        })

        result = pm.execute_task()

        return {
            "requirement": requirement,
            "analysis": result.get("outputs", {}),
        }

    def design(self, system_description: str) -> dict[str, Any]:
        """
        设计系统架构

        Args:
            system_description: 系统描述

        Returns:
            设计结果
        """
        if not self.coordinator.get_roles_by_type(RoleType.ARCHITECT):
            self.coordinator.create_role(RoleType.ARCHITECT, "arch_auto", "架构师")

        arch = self.coordinator.get_roles_by_type(RoleType.ARCHITECT)[0]

        arch.assign_task({
            "type": "design",
            "description": f"设计系统: {system_description}",
            "inputs": {"requirements": system_description},
        })

        result = arch.execute_task()

        return {
            "system": system_description,
            "design": result.get("outputs", {}),
        }

    def review_code(self, code: str) -> dict[str, Any]:
        """
        代码审查

        Args:
            code: 待审查的代码

        Returns:
            审查结果
        """
        if not self.coordinator.get_roles_by_type(RoleType.DEVELOPER):
            self.coordinator.create_role(RoleType.DEVELOPER, "dev_auto", "开发人员")

        dev = self.coordinator.get_roles_by_type(RoleType.DEVELOPER)[0]

        dev.assign_task({
            "type": "code_review",
            "description": "代码审查",
            "inputs": {"code": code},
        })

        result = dev.execute_task()

        return {
            "review": result.get("outputs", {}),
        }

    # ==================== 工作流管理 ====================

    def run_pipeline(self, pipeline_type: str = "feature", **inputs: Any) -> dict[str, Any]:
        """
        运行工作流

        Args:
            pipeline_type: 工作流类型 (standard, feature, bugfix)
            **inputs: 输入参数

        Returns:
            执行结果
        """
        result = self.coordinator.run_workflow(pipeline_type, inputs)

        if result.get("status") == "completed":
            self._stats.workflows_completed += 1

        return result

    def get_pipeline_status(self) -> dict[str, Any]:
        """获取工作流状态"""
        return {
            "stats": self._stats.model_dump(),
            "coordinator_stats": self.coordinator.get_stats().model_dump(),
        }

    # ==================== 记忆与存储 ====================

    def remember(self, key: str, content: str, important: bool = False) -> None:
        """
        记忆重要信息

        Args:
            key: 键名
            content: 内容
            important: 是否重要（重要信息永不清除）
        """
        if important:
            self.memory.store_important_knowledge(key, content)
        else:
            self.memory.store_conversation(content, importance=50)

        self.storage.save_knowledge(key, content)

    def recall(self, key: str) -> str | None:
        """
        回忆信息

        Args:
            key: 键名

        Returns:
            存储的内容
        """
        # 先从存储获取
        content = self.storage.load_knowledge(key)
        if content:
            return content

        # 再从记忆获取
        return self.memory.get_knowledge(key)

    # ==================== 状态报告 ====================

    def get_status(self) -> dict[str, Any]:
        """
        获取整体状态

        Returns:
            状态信息
        """
        return {
            "project": self.project_name,
            "team": {
                "size": self._stats.team_size,
                "members": self.coordinator.list_roles(),
            },
            "stats": self._stats.model_dump(),
            "memory_health": self.memory.get_health_report()["status"],
        }

    def get_report(self) -> str:
        """
        获取项目报告

        Returns:
            格式化的报告字符串
        """
        status = self.get_status()

        report = f"""
# {self.project_name} 项目报告

## 团队
- 规模: {status['team']['size']} 人

## 统计
- 开发功能: {status['stats']['features_developed']} 个
- 修复Bug: {status['stats']['bugs_fixed']} 个
- 完成工作流: {status['stats']['workflows_completed']} 个

## 健康状态
- 记忆系统: {status['memory_health']}
"""
        return report.strip()


# ==================== 便捷函数 ====================

def create_harness(project_name: str = "Default Project") -> Harness:
    """
    创建 Harness 实例

    Args:
        project_name: 项目名称

    Returns:
        Harness 实例
    """
    return Harness(project_name=project_name)