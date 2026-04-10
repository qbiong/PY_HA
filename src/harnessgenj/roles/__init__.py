"""
Roles Module - Agent角色定义

Harness Engineering 核心理念：用真实团队角色替代抽象概念

基于业界最佳实践增强:
- Microsoft Multi-Agent Reference Architecture: 分离关注点原则
- GitHub Copilot Custom Agents: 工具边界强化行为边界
- Mindra Orchestrator-Worker: Orchestrator负责what，Worker负责how
- AgentForgeHub: 角色定义四要素（responsibilities, capabilities, inputs, outputs）

生成器角色（产出）:
- Developer: 开发人员，负责编码实现（工具: read, search, edit_code, terminal）
  - 方案C增强：支持动态配置，可创建 FrontendDeveloper/BackendDeveloper/FullStackDeveloper 实例
- Tester: 测试人员，负责测试编写（工具: read, search, edit_code, terminal）
- ProductManager: 产品经理，负责需求管理（工具: read, search, edit_doc）
- Architect: 架构师，负责技术方案（工具: read, search, edit_doc）
- DocWriter: 文档管理员，负责文档编写（工具: read, search, edit_doc）
- ProjectManager: 项目经理，负责任务协调（工具: read, search, edit_doc）

判别器角色（对抗）:
- CodeReviewer: 代码审查者，负责代码质量审查（工具: read, search - 只读）
- BugHunter: 漏洞猎手，负责深度漏洞挖掘（工具: read, search - 只读）
"""

from harnessgenj.roles.base import (
    AgentRole,
    RoleType,
    RoleSkill,
    RoleContext,
    TaskType,
    SkillCategory,
    RoleCategory,
    ToolPermission,
    BoundaryCheckResult,
    ROLE_TOOL_PERMISSIONS,
    create_role,
)
from harnessgenj.roles.developer import (
    Developer,
    DeveloperConfig,
    DeveloperContext,
    create_developer,
    create_frontend_developer,
    create_backend_developer,
    create_fullstack_developer,
)
from harnessgenj.roles.tester import Tester, create_tester
from harnessgenj.roles.product_manager import ProductManager, create_product_manager
from harnessgenj.roles.architect import Architect, create_architect
from harnessgenj.roles.doc_writer import DocWriter, create_doc_writer
from harnessgenj.roles.project_manager import ProjectManager, create_project_manager
from harnessgenj.roles.code_reviewer import CodeReviewer, create_code_reviewer
from harnessgenj.roles.bug_hunter import BugHunter, create_bug_hunter

__all__ = [
    # 基类
    "AgentRole",
    "RoleType",
    "RoleSkill",
    "RoleContext",
    "TaskType",
    "SkillCategory",
    "RoleCategory",
    "create_role",
    # 新增：工具权限和边界检查
    "ToolPermission",
    "BoundaryCheckResult",
    "ROLE_TOOL_PERMISSIONS",
    # 生成器角色
    "Developer",
    "DeveloperConfig",  # 方案C：动态配置
    "DeveloperContext",
    "Tester",
    "ProductManager",
    "Architect",
    "DocWriter",
    "ProjectManager",
    # 判别器角色
    "CodeReviewer",
    "BugHunter",
    # 便捷函数
    "create_developer",
    "create_frontend_developer",  # 方案C：前端开发便捷函数
    "create_backend_developer",    # 方案C：后端开发便捷函数
    "create_fullstack_developer",  # 方案C：全栈开发便捷函数
    "create_tester",
    "create_product_manager",
    "create_architect",
    "create_doc_writer",
    "create_project_manager",
    "create_code_reviewer",
    "create_bug_hunter",
]