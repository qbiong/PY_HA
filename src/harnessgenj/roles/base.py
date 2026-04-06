"""
Agent Role Base - 角色基类定义

Harness Engineering 的核心：角色驱动的Agent协作

每个角色有:
1. 职责范围 (Responsibilities)
2. 技能集 (Skills)
3. 工作流程 (Workflow)
4. 协作接口 (Collaboration)
5. 工具权限 (Tool Permissions) - 业界最佳实践
6. 边界检查 (Boundary Check) - 职责边界强化

设计理念（基于业界最佳实践）：
- Microsoft Multi-Agent Reference Architecture: 分离关注点原则
- GitHub Copilot Custom Agents: 工具边界强化行为边界
- Mindra Orchestrator-Worker: Orchestrator负责what，Worker负责how
- AgentForgeHub: 角色定义四要素（responsibilities, capabilities, inputs, outputs）
"""

from abc import ABC, abstractmethod
from typing import Any, Callable
from pydantic import BaseModel, Field
from enum import Enum
import time


# ==================== 工具权限枚举 ====================

class ToolPermission(Enum):
    """
    工具权限类型 - 定义角色可以使用的工具

    基于GitHub Copilot Custom Agents的设计理念：
    "限制工具访问不是为了不信任，而是为了防止Agent意外越界"
    """
    READ = "read"           # 读取文件
    SEARCH = "search"       # 搜索代码
    EDIT_CODE = "edit_code" # 编辑代码文件
    EDIT_DOC = "edit_doc"   # 编辑文档文件
    TERMINAL = "terminal"   # 执行终端命令
    FETCH = "fetch"         # 网络请求


# ==================== 角色类型枚举 ====================

class RoleType(Enum):
    """角色类型"""

    # 生成器角色（产出）
    DEVELOPER = "developer"              # 开发人员
    TESTER = "tester"                    # 测试人员
    PRODUCT_MANAGER = "product_manager"  # 产品经理
    ARCHITECT = "architect"              # 架构师
    DOC_WRITER = "doc_writer"            # 文档管理员
    PROJECT_MANAGER = "project_manager"  # 项目经理
    # 判别器角色（对抗）
    CODE_REVIEWER = "code_reviewer"      # 代码审查者
    BUG_HUNTER = "bug_hunter"            # 漏洞猎手


class RoleCategory(Enum):
    """角色分类"""

    GENERATOR = "generator"        # 生成器：产出代码/文档
    DISCRIMINATOR = "discriminator"  # 判别器：审查/验证产出


class SkillCategory(Enum):
    """技能分类"""

    CODING = "coding"           # 编码类
    TESTING = "testing"         # 测试类
    ANALYSIS = "analysis"       # 分析类
    DOCUMENTATION = "docs"      # 文档类
    MANAGEMENT = "management"   # 管理类
    DESIGN = "design"           # 设计类


# ==================== 角色工具权限配置 ====================
# 基于GitHub Copilot Custom Agents的设计理念：
# "限制工具访问不是为了不信任，而是为了防止Agent意外越界"

ROLE_TOOL_PERMISSIONS: dict["RoleType", list[ToolPermission]] = {
    # 生成器角色
    RoleType.ARCHITECT: [
        ToolPermission.READ,
        ToolPermission.SEARCH,
        ToolPermission.EDIT_DOC  # 只能编辑文档，不能编辑代码
    ],
    RoleType.DEVELOPER: [
        ToolPermission.READ,
        ToolPermission.SEARCH,
        ToolPermission.EDIT_CODE,
        ToolPermission.TERMINAL  # 能编辑代码和运行命令
    ],
    RoleType.PRODUCT_MANAGER: [
        ToolPermission.READ,
        ToolPermission.SEARCH,
        ToolPermission.EDIT_DOC  # 只能编辑需求文档
    ],
    RoleType.TESTER: [
        ToolPermission.READ,
        ToolPermission.SEARCH,
        ToolPermission.EDIT_CODE,  # 能写测试代码
        ToolPermission.TERMINAL
    ],
    RoleType.DOC_WRITER: [
        ToolPermission.READ,
        ToolPermission.SEARCH,
        ToolPermission.EDIT_DOC  # 只能编辑文档
    ],
    RoleType.PROJECT_MANAGER: [
        ToolPermission.READ,
        ToolPermission.SEARCH,
        ToolPermission.EDIT_DOC  # 只能编辑文档
    ],
    # 判别器角色
    RoleType.CODE_REVIEWER: [
        ToolPermission.READ,
        ToolPermission.SEARCH  # 只读，不能修改任何文件
    ],
    RoleType.BUG_HUNTER: [
        ToolPermission.READ,
        ToolPermission.SEARCH  # 只读，不能修改任何文件
    ],
}


# ==================== 边界检查结果 ====================

class BoundaryCheckResult(BaseModel):
    """
    边界检查结果

    用于判断一个行为是否在角色的职责边界内
    """
    allowed: bool = Field(..., description="是否允许操作")
    reason: str = Field(default="", description="原因说明")
    suggestion: str = Field(default="", description="建议回调的角色")
    action: str = Field(default="", description="检查的行为")


# ==================== 角色技能定义 ====================


class RoleSkill(BaseModel):
    """
    角色技能 - 每个角色具备的具体能力

    技能定义:
    - 名称和描述
    - 执行函数
    - 输入输出规范
    - 依赖关系
    """

    name: str = Field(..., description="技能名称")
    description: str = Field(..., description="技能描述")
    category: SkillCategory = Field(..., description="技能分类")
    inputs: list[str] = Field(default_factory=list, description="所需输入")
    outputs: list[str] = Field(default_factory=list, description="产出输出")
    dependencies: list[str] = Field(default_factory=list, description="依赖的其他技能")
    executor: Callable | None = Field(default=None, description="执行函数", exclude=True)

    def can_execute(self, available_inputs: list[str]) -> bool:
        """检查是否有足够输入执行此技能"""
        return all(inp in available_inputs for inp in self.inputs)

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """执行技能"""
        if self.executor:
            return self.executor(**kwargs)
        return {"status": "no_executor", "skill": self.name}


class TaskType(Enum):
    """任务类型"""

    # 开发任务
    IMPLEMENT_FEATURE = "implement_feature"    # 实现功能
    FIX_BUG = "fix_bug"                        # 修复Bug
    REFACTOR = "refactor"                      # 重构代码
    CODE_REVIEW = "code_review"                # 代码审查

    # 测试任务
    WRITE_TEST = "write_test"                  # 编写测试
    RUN_TEST = "run_test"                      # 执行测试
    BUG_REPORT = "bug_report"                  # Bug报告

    # 产品任务
    ANALYZE_REQUIREMENT = "analyze_requirement"  # 需求分析
    WRITE_USER_STORY = "write_user_story"        # 用户故事
    PRIORITIZE = "prioritize"                    # 优先级排序

    # 架构任务
    DESIGN_SYSTEM = "design_system"            # 系统设计
    REVIEW_ARCHITECTURE = "review_architecture"  # 架构评审

    # 文档任务
    WRITE_DOC = "write_doc"                    # 编写文档
    UPDATE_DOC = "update_doc"                  # 更新文档

    # 管理任务
    COORDINATE = "coordinate"                  # 协调任务
    TRACK_PROGRESS = "track_progress"          # 进度追踪


class RoleContext(BaseModel):
    """
    角色上下文 - 执行任务时的环境信息

    包含:
    - 项目信息
    - 当前任务
    - 协作状态
    - 历史记录
    """

    project_id: str = Field(default="", description="项目ID")
    project_name: str = Field(default="", description="项目名称")
    current_task_id: str | None = Field(default=None, description="当前任务ID")
    working_directory: str = Field(default="", description="工作目录")
    collaborators: dict[str, str] = Field(default_factory=dict, description="协作者列表")
    artifacts: dict[str, Any] = Field(default_factory=dict, description="产出物")
    created_at: float = Field(default_factory=time.time, description="创建时间")

    def add_artifact(self, name: str, content: Any) -> None:
        """添加产出物"""
        self.artifacts[name] = {
            "content": content,
            "created_at": time.time(),
        }

    def get_artifact(self, name: str) -> Any | None:
        """获取产出物"""
        artifact = self.artifacts.get(name)
        return artifact["content"] if artifact else None


class AgentRole(ABC):
    """
    Agent角色基类 - 所有角色的抽象基类

    Harness Engineering 核心概念:
    - 每个角色有明确的职责边界
    - 每个角色有特定的技能集
    - 角色之间通过任务协作
    - 角色产出可追溯的交付物

    业界最佳实践增强:
    - 工具权限边界（基于GitHub Copilot Custom Agents）
    - 职责边界检查（基于Microsoft Multi-Agent Reference Architecture）
    - 决策权限定义（基于Mindra Orchestrator-Worker模式）
    """

    def __init__(
        self,
        role_id: str,
        name: str,
        context: RoleContext | None = None,
    ) -> None:
        self.role_id = role_id
        self.name = name
        self.context = context or RoleContext()
        self._skills: dict[str, RoleSkill] = {}
        self._task_history: list[dict[str, Any]] = []
        self._current_task: dict[str, Any] | None = None

        # 初始化技能
        self._setup_skills()

    @property
    @abstractmethod
    def role_type(self) -> RoleType:
        """角色类型"""
        pass

    @property
    @abstractmethod
    def responsibilities(self) -> list[str]:
        """职责范围"""
        pass

    @property
    def is_discriminator(self) -> bool:
        """是否为判别器角色"""
        return self.role_type in (RoleType.CODE_REVIEWER, RoleType.BUG_HUNTER)

    @property
    def role_category(self) -> RoleCategory:
        """角色分类"""
        return RoleCategory.DISCRIMINATOR if self.is_discriminator else RoleCategory.GENERATOR

    @abstractmethod
    def _setup_skills(self) -> None:
        """设置技能集 - 子类实现"""
        pass

    # ==================== 新增：职责边界定义 ====================

    @property
    def forbidden_actions(self) -> list[str]:
        """
        禁止行为列表

        定义此角色不能执行的操作，违反这些行为将触发边界检查失败。
        基于Microsoft Multi-Agent Reference Architecture的"分离关注点"原则。

        子类应该覆盖此属性来定义具体的禁止行为。
        """
        return []

    @property
    def decision_authority(self) -> list[str]:
        """
        决策权限列表

        定义此角色有权做出的决策类型。
        基于Mindra的"Orchestrator负责what，Worker负责how"原则。

        子类应该覆盖此属性来定义具体的决策权限。
        """
        return []

    @property
    def no_decision_authority(self) -> list[str]:
        """
        无决策权限列表

        定义此角色无权做出的决策类型，这些决策应回调其他角色。

        子类应该覆盖此属性来定义具体的无决策权限。
        """
        return []

    # ==================== 新增：工具权限管理 ====================

    def get_tool_permissions(self) -> list[ToolPermission]:
        """
        获取当前角色的工具权限

        基于GitHub Copilot Custom Agents的设计：
        工具边界强化行为边界，物理上阻止越界行为。

        Returns:
            允许使用的工具列表
        """
        return ROLE_TOOL_PERMISSIONS.get(self.role_type, [])

    def can_use_tool(self, tool: ToolPermission) -> BoundaryCheckResult:
        """
        检查是否有工具权限

        Args:
            tool: 要使用的工具

        Returns:
            边界检查结果
        """
        allowed_tools = self.get_tool_permissions()
        if tool in allowed_tools:
            return BoundaryCheckResult(
                allowed=True,
                reason=f"{self.name} 有 {tool.value} 权限",
                action=f"use {tool.value}"
            )
        else:
            return BoundaryCheckResult(
                allowed=False,
                reason=f"{self.name} 没有 {tool.value} 权限",
                suggestion=self._get_role_with_permission(tool),
                action=f"use {tool.value}"
            )

    def _get_role_with_permission(self, tool: ToolPermission) -> str:
        """获取有指定权限的角色"""
        for role_type, permissions in ROLE_TOOL_PERMISSIONS.items():
            if tool in permissions:
                return role_type.value
        return "project_manager"

    # ==================== 新增：职责边界检查 ====================

    def check_boundary(self, action: str) -> BoundaryCheckResult:
        """
        检查行为是否在职责边界内

        基于Microsoft Multi-Agent Reference Architecture的"分离关注点"原则：
        每个Agent必须有明确且定义清晰的职责，这种清晰性使专注开发成为可能。

        Args:
            action: 要执行的行为描述

        Returns:
            边界检查结果
        """
        # 检查是否在禁止行为中
        for forbidden in self.forbidden_actions:
            if forbidden.lower() in action.lower():
                return BoundaryCheckResult(
                    allowed=False,
                    reason=f"'{action}' 违反职责边界：{forbidden}",
                    suggestion=self._get_handler_for_action(action),
                    action=action
                )

        return BoundaryCheckResult(
            allowed=True,
            reason=f"'{action}' 在职责范围内",
            action=action
        )

    def _get_handler_for_action(self, action: str) -> str:
        """获取应该处理某行为的角色"""
        # 根据关键词判断
        if any(kw in action.lower() for kw in ["代码", "实现", "函数", "类", "code", "implement"]):
            return "developer"
        elif any(kw in action.lower() for kw in ["架构", "设计", "技术选型", "architecture", "design"]):
            return "architect"
        elif any(kw in action.lower() for kw in ["需求", "用户故事", "requirement", "user story"]):
            return "product_manager"
        elif any(kw in action.lower() for kw in ["测试", "用例", "test", "test case"]):
            return "tester"
        elif any(kw in action.lower() for kw in ["文档", "说明", "document", "doc"]):
            return "doc_writer"
        return "project_manager"

    # ==================== 新增：角色提示词构建 ====================

    def build_role_prompt(self) -> str:
        """
        构建角色提示词

        包含职责定义、边界检查、自我反思等内容。
        子类可以覆盖此方法来定制提示词。

        Returns:
            完整的角色提示词
        """
        parts = [
            f"你是项目的{self.name}。",
            "",
            "## 职责范围",
        ]

        for resp in self.responsibilities:
            parts.append(f"- {resp}")

        if self.decision_authority:
            parts.append("")
            parts.append("## 决策权限")
            for auth in self.decision_authority:
                parts.append(f"- {auth}")

        if self.forbidden_actions:
            parts.append("")
            parts.append("## 禁止行为")
            for forbidden in self.forbidden_actions:
                parts.append(f"- ❌ {forbidden}")

        if self.no_decision_authority:
            parts.append("")
            parts.append("## 无决策权限（应回调相应角色）")
            for no_auth in self.no_decision_authority:
                parts.append(f"- {no_auth}")

        return "\n".join(parts)

    # ==================== 技能管理 ====================

    def add_skill(self, skill: RoleSkill) -> None:
        """添加技能"""
        self._skills[skill.name] = skill

    def get_skill(self, name: str) -> RoleSkill | None:
        """获取技能"""
        return self._skills.get(name)

    def list_skills(self) -> list[RoleSkill]:
        """列出所有技能"""
        return list(self._skills.values())

    def has_skill(self, skill_name: str) -> bool:
        """检查是否有某技能"""
        return skill_name in self._skills

    # ==================== 任务执行 ====================

    def can_handle(self, task_type: TaskType) -> bool:
        """
        判断是否能处理某类型任务

        基于角色技能和任务类型匹配
        """
        return task_type in self.get_supported_task_types()

    @abstractmethod
    def get_supported_task_types(self) -> list[TaskType]:
        """获取支持的任务类型"""
        pass

    def assign_task(self, task: dict[str, Any]) -> bool:
        """
        分配任务

        Args:
            task: 任务信息，包含 type, description, inputs 等

        Returns:
            是否接受任务
        """
        task_type = task.get("type")

        # 如果是字符串，尝试转换为 TaskType，转换失败也接受
        if isinstance(task_type, str):
            try:
                task_type = TaskType(task_type)
            except ValueError:
                # 对于未知的任务类型，也接受（更灵活）
                pass

        # 如果是 TaskType，检查是否支持
        if isinstance(task_type, TaskType):
            if not self.can_handle(task_type):
                return False

        self._current_task = {
            **task,
            "type": task_type,
            "assigned_at": time.time(),
            "status": "assigned",
        }
        return True

    def execute_task(self) -> dict[str, Any]:
        """
        执行当前任务

        Returns:
            执行结果
        """
        if not self._current_task:
            return {"status": "error", "message": "No task assigned"}

        task_type = self._current_task.get("type")

        if isinstance(task_type, TaskType):
            result = self._execute_by_type(task_type)
        elif isinstance(task_type, str):
            result = self._execute_by_stage_name(task_type)
        else:
            result = {"status": "error", "message": f"Unknown task type: {task_type}"}

        # 记录历史
        self._task_history.append({
            "task": self._current_task,
            "result": result,
            "completed_at": time.time(),
        })

        self._current_task = None
        return result

    def _execute_by_stage_name(self, stage_name: str) -> dict[str, Any]:
        """
        按阶段名称执行任务 - 默认实现

        子类可以覆盖此方法来支持自定义阶段名称
        """
        return {
            "status": "completed",
            "outputs": {
                "result": f"Stage {stage_name} completed by {self.name}",
            },
        }

    @abstractmethod
    def _execute_by_type(self, task_type: TaskType) -> dict[str, Any]:
        """按类型执行任务 - 子类实现"""
        pass

    # ==================== 协作 ====================

    def handoff_to(self, other_role: "AgentRole", artifact_name: str, artifact_content: Any) -> bool:
        """
        将产出物移交给其他角色

        Harness协作核心：角色间通过交付物协作
        """
        other_role.receive_handoff(self.name, artifact_name, artifact_content)
        return True

    def receive_handoff(self, from_role: str, artifact_name: str, artifact_content: Any) -> None:
        """接收其他角色的移交"""
        self.context.add_artifact(artifact_name, artifact_content)
        self.context.collaborators[from_role] = artifact_name

    def request_review(self, reviewer: "AgentRole", content: Any) -> str:
        """请求其他角色审查"""
        review_id = f"review_{time.time()}"
        reviewer.receive_handoff(self.name, f"review_request_{review_id}", content)
        return review_id

    # ==================== 状态 ====================

    def get_status(self) -> dict[str, Any]:
        """获取角色状态"""
        return {
            "role_id": self.role_id,
            "name": self.name,
            "role_type": self.role_type.value,
            "responsibilities": self.responsibilities,
            "skills": [s.name for s in self._skills.values()],
            "current_task": self._current_task,
            "task_history_count": len(self._task_history),
            "artifacts_count": len(self.context.artifacts),
        }

    def get_task_history(self) -> list[dict[str, Any]]:
        """获取任务历史"""
        return self._task_history.copy()


# ==================== 角色工厂 ====================

def create_role(
    role_type: RoleType,
    role_id: str,
    name: str | None = None,
    context: RoleContext | None = None,
) -> AgentRole:
    """
    创建角色实例

    Args:
        role_type: 角色类型
        role_id: 角色ID
        name: 角色名称
        context: 角色上下文

    Returns:
        角色实例
    """
    from harnessgenj.roles.developer import Developer
    from harnessgenj.roles.tester import Tester
    from harnessgenj.roles.product_manager import ProductManager
    from harnessgenj.roles.architect import Architect
    from harnessgenj.roles.doc_writer import DocWriter
    from harnessgenj.roles.project_manager import ProjectManager
    from harnessgenj.roles.code_reviewer import CodeReviewer
    from harnessgenj.roles.bug_hunter import BugHunter

    role_classes = {
        # 生成器角色
        RoleType.DEVELOPER: Developer,
        RoleType.TESTER: Tester,
        RoleType.PRODUCT_MANAGER: ProductManager,
        RoleType.ARCHITECT: Architect,
        RoleType.DOC_WRITER: DocWriter,
        RoleType.PROJECT_MANAGER: ProjectManager,
        # 判别器角色
        RoleType.CODE_REVIEWER: CodeReviewer,
        RoleType.BUG_HUNTER: BugHunter,
    }

    role_class = role_classes.get(role_type)
    if not role_class:
        raise ValueError(f"Unknown role type: {role_type}")

    return role_class(
        role_id=role_id,
        name=name or role_type.value,
        context=context,
    )