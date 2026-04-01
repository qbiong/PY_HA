"""
Roles Module - Agent角色定义

Harness Engineering 核心理念：用真实团队角色替代抽象概念

角色定义:
- Developer: 开发人员，负责编码实现
- Tester: 测试人员，负责质量保证
- ProductManager: 产品经理，负责需求管理
- Architect: 架构师，负责技术方案
- DocWriter: 文档管理员，负责文档编写
- ProjectManager: 项目经理，负责任务协调
"""

from py_ha.roles.base import (
    AgentRole,
    RoleType,
    RoleSkill,
    RoleContext,
    TaskType,
    SkillCategory,
    create_role,
)
from py_ha.roles.developer import Developer, create_developer
from py_ha.roles.tester import Tester, create_tester
from py_ha.roles.product_manager import ProductManager, create_product_manager
from py_ha.roles.architect import Architect, create_architect
from py_ha.roles.doc_writer import DocWriter, create_doc_writer
from py_ha.roles.project_manager import ProjectManager, create_project_manager

__all__ = [
    # 基类
    "AgentRole",
    "RoleType",
    "RoleSkill",
    "RoleContext",
    "TaskType",
    "SkillCategory",
    "create_role",
    # 具体角色
    "Developer",
    "Tester",
    "ProductManager",
    "Architect",
    "DocWriter",
    "ProjectManager",
    # 便捷函数
    "create_developer",
    "create_tester",
    "create_product_manager",
    "create_architect",
    "create_doc_writer",
    "create_project_manager",
]