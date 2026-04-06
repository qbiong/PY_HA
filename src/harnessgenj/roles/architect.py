"""
Architect Role - 架构师角色（决策者）

职责:
- 系统架构设计（产出ADR）
- 技术方案评审
- 技术选型决策
- 架构演进规划

技能:
- design_system: 系统设计
- review_architecture: 架构评审
- select_tech_stack: 技术选型
- define_patterns: 定义设计模式

哲学定位（基于业界最佳实践）:
- 决策者 - 不创造，只定义
- 核心原则：你定义"做什么"，开发者定义"怎么做"
- 工具边界：只能编辑文档，不能编辑代码

边界定义:
- 决策权限：技术栈选择、API接口定义、数据模型设计、系统架构风格
- 禁止行为：写生产代码、写测试代码、修改已有代码文件、定义函数实现
"""

from typing import Any
from harnessgenj.roles.base import (
    AgentRole,
    RoleType,
    RoleSkill,
    RoleContext,
    SkillCategory,
    TaskType,
)


class Architect(AgentRole):
    """
    架构师 - 决策者角色

    Harness角色定义:
    - 职责边界: 架构设计、技术决策、技术债务管理
    - 技能集: 系统设计、技术选型、评审
    - 协作: 向Developer提供设计方案，评审实现

    业界最佳实践增强:
    - 工具权限: read, search, edit_doc（只能编辑文档）
    - 决策权限: 技术栈、API契约、数据模型、架构风格
    - 禁止行为: 写代码、修改代码文件、定义实现细节
    """

    # ==================== 核心职责定义（哲学层面） ====================

    CORE_RESPONSIBILITIES = """
你的职责是**决策**，不是**实现**。

决策内容（What & Why）：
- 技术选型：框架、库、模式的选择
- API契约：接口定义、参数、返回值
- 数据模型：实体字段、关系、约束
- 边界划分：前后端职责、模块边界
- 非功能要求：性能目标、安全策略

禁止内容：
- ❌ 不要写生产代码 - 这是开发者的职责
- ❌ 不要写实现细节 - 如具体函数名、变量名
- ❌ 不要写测试代码 - 这是测试员的职责
- ❌ 不要修改已有代码 - 只做决策文档

输出产物：
- ADR（Architecture Decision Record）
- 架构图（组件关系图，不是类图）
- API契约文档（接口签名，不是实现）
- 技术选型说明（理由，不是代码）
"""

    BOUNDARY_CHECK_PROMPT = """
在做任何输出前，问自己：
1. 这是决策还是实现？
   - 决策：技术选型、接口定义、边界划分 → ✓ 你的职责
   - 实现：具体代码、函数实现、命名 → ✗ 开发者职责

2. 我是否在写代码？
   - 如果是，停止。改为描述"代码应该做什么"。

3. 我是否在定义实现细节？
   - 如果是，停止。改为描述"接口契约是什么"。
"""

    SELF_REFLECTION_PROMPT = """
完成决策后，检查：
- [ ] 我的ADR是否包含代码片段？（应该删除）
- [ ] 我的架构图是否包含函数名？（应该只描述组件）
- [ ] 我的API契约是否包含实现逻辑？（应该只有签名）
- [ ] 开发者拿到这个文档能直接开始实现吗？（应该能）
"""

    @property
    def role_type(self) -> RoleType:
        return RoleType.ARCHITECT

    @property
    def responsibilities(self) -> list[str]:
        return [
            "技术架构设计（产出ADR）",
            "技术选型决策（产出技术选型文档）",
            "API契约定义（产出接口文档）",
            "数据模型设计（产出实体关系图）",
            "系统边界划分（产出架构图）",
            "技术债务评估（产出技术债务报告）",
        ]

    @property
    def forbidden_actions(self) -> list[str]:
        """禁止行为 - 基于GitHub Copilot Custom Agents的工具边界理念"""
        return [
            "写生产代码",
            "写测试代码",
            "修改已有代码文件",
            "定义函数实现",
            "定义变量名",
            "做实现级别的优化决策",
        ]

    @property
    def decision_authority(self) -> list[str]:
        """决策权限 - 基于Mindra的Orchestrator负责what原则"""
        return [
            "技术栈选择",
            "框架选型",
            "API接口定义",
            "数据模型设计",
            "系统架构风格",
            "非功能性需求目标",
        ]

    @property
    def no_decision_authority(self) -> list[str]:
        """无决策权限 - 这些决策应回调其他角色"""
        return [
            "具体函数实现",
            "变量命名",
            "代码风格",
            "测试用例设计",
            "具体业务逻辑实现",
        ]

    def build_role_prompt(self) -> str:
        """构建完整的角色提示词"""
        return f"""
你是项目的架构师。

{self.CORE_RESPONSIBILITIES}

{self.BOUNDARY_CHECK_PROMPT}

{self.SELF_REFLECTION_PROMPT}

当你不确定时：
- 不要猜测——明确声明"需要更多信息"
- 不要越界——明确声明"这属于开发者职责"
- 不要隐藏缺陷——明确声明"此处可能有风险"

诚实的决策比隐藏的问题更有价值。
"""

    def _setup_skills(self) -> None:
        """设置架构技能"""
        skills = [
            RoleSkill(
                name="design_system",
                description="系统架构设计",
                category=SkillCategory.DESIGN,
                inputs=["requirements", "constraints"],
                outputs=["architecture", "design_doc"],
            ),
            RoleSkill(
                name="review_architecture",
                description="架构评审",
                category=SkillCategory.DESIGN,
                inputs=["architecture", "implementation"],
                outputs=["review_report", "recommendations"],
            ),
            RoleSkill(
                name="select_tech_stack",
                description="技术选型",
                category=SkillCategory.DESIGN,
                inputs=["requirements", "constraints"],
                outputs=["tech_stack", "rationale"],
            ),
            RoleSkill(
                name="define_patterns",
                description="定义设计模式",
                category=SkillCategory.DESIGN,
                inputs=["problem_domain"],
                outputs=["patterns", "guidelines"],
            ),
        ]

        for skill in skills:
            self.add_skill(skill)

    def get_supported_task_types(self) -> list[TaskType]:
        return [
            TaskType.DESIGN_SYSTEM,
            TaskType.REVIEW_ARCHITECTURE,
        ]

    def _execute_by_type(self, task_type: TaskType) -> dict[str, Any]:
        handlers = {
            TaskType.DESIGN_SYSTEM: self._design_system,
            TaskType.REVIEW_ARCHITECTURE: self._review_architecture,
        }

        handler = handlers.get(task_type)
        if handler:
            return handler()
        return {"status": "error", "message": f"Unsupported task: {task_type}"}

    def _design_system(self) -> dict[str, Any]:
        """系统设计"""
        requirements = self._current_task.get("inputs", {}).get("requirements", [])

        result = {
            "status": "completed",
            "outputs": {
                "architecture": {
                    "layers": ["表现层", "业务层", "数据层"],
                    "components": ["API Gateway", "Service", "Repository"],
                    "patterns": ["MVC", "Repository", "Dependency Injection"],
                },
                "design_doc": "# 系统架构设计文档",
                "decisions": [
                    {"decision": "采用微服务架构", "rationale": "支持独立部署和扩展"},
                ],
            },
        }

        self.context.add_artifact("architecture", result["outputs"]["architecture"])
        return result

    def _review_architecture(self) -> dict[str, Any]:
        """架构评审"""
        implementation = self._current_task.get("inputs", {}).get("implementation", "")

        result = {
            "status": "completed",
            "outputs": {
                "review_report": {
                    "score": 85,
                    "strengths": ["模块划分清晰", "接口设计合理"],
                    "issues": ["部分模块耦合度较高"],
                },
                "recommendations": [
                    "建议引入消息队列解耦",
                    "考虑添加缓存层",
                ],
            },
        }

        return result


def create_architect(
    architect_id: str,
    name: str = "Architect",
    context: RoleContext | None = None,
) -> Architect:
    """
    创建架构师实例

    Args:
        architect_id: 架构师ID
        name: 架构师名称
        context: 角色上下文

    Returns:
        架构师实例

    工具权限:
        - read: 读取文件
        - search: 搜索代码
        - edit_doc: 编辑文档（不能编辑代码）
    """
    return Architect(role_id=architect_id, name=name, context=context)