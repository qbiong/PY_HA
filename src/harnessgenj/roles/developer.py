"""
Developer Role - 开发人员角色（实现者，渐进式披露版）

职责:
- 功能实现（按ADR和API契约）
- Bug修复
- 代码重构
- 向PM汇报进度

特点:
- 不获取完整项目信息
- 只接收：项目基本信息 + 当前开发需求 + 相关设计摘要
- 执行后更新开发日志
- 向PM汇报进度

渐进式披露:
- 项目名称、技术栈
- 当前任务需求
- 相关设计摘要（只读）

代码生成辅助:
- 使用 CodeGenerator 生成模板代码
- 快速生成函数、类、测试骨架
- 架构约束自动检查

哲学定位（基于业界最佳实践）:
- 实现者 - 不决策，只执行
- 核心原则：你执行"怎么做"，架构师定义"做什么"
- 工具边界：能编辑代码和运行终端命令

边界定义:
- 决策权限：函数实现方式、变量命名、代码组织结构（在架构约束内）
- 禁止行为：做技术选型决策、修改API契约文档、修改架构设计文档
- 依赖检查：必须有ADR和API契约才能开始实现
"""

from typing import Any
from pydantic import BaseModel, Field
import time

from harnessgenj.roles.base import (
    AgentRole,
    RoleType,
    RoleSkill,
    RoleContext,
    SkillCategory,
    TaskType,
)
from harnessgenj.codegen import (
    CodeGenerator,
    GeneratorConfig,
    GenerationResult,
    create_code_generator,
)


class DeveloperContext(BaseModel):
    """开发者上下文（最小信息）"""

    project_name: str = Field(default="", description="项目名称")
    tech_stack: str = Field(default="", description="技术栈")
    current_task: dict[str, Any] = Field(default_factory=dict, description="当前任务")
    requirements_summary: str = Field(default="", description="需求摘要（只读）")
    design_summary: str = Field(default="", description="设计摘要（只读）")


class Developer(AgentRole):
    """
    开发人员 - 实现者角色

    Harness角色定义:
    - 职责边界: 编码实现、Bug修复、代码质量
    - 技能集: 编码、调试、重构、审查
    - 协作: 接收PM任务（最小上下文），完成后汇报

    渐进式披露特点:
    - 不获取完整项目信息
    - 只能看到项目基本信息和当前任务
    - 设计和需求只能看到摘要

    业界最佳实践增强:
    - 工具权限: read, search, edit_code, terminal（能编辑代码和运行命令）
    - 决策权限: 函数实现方式、变量命名、局部优化策略
    - 禁止行为: 做技术选型决策、修改API契约文档、修改架构设计文档
    - 依赖检查: 必须有ADR和API契约才能开始实现
    """

    # ==================== 核心职责定义（哲学层面） ====================

    CORE_RESPONSIBILITIES = """
你的职责是**实现**，不是**决策**。

实现内容：
- 按架构师的ADR写代码
- 按API契约实现接口
- 按数据模型写Entity类
- 实现具体业务逻辑
- 编写实现级别的注释

禁止内容：
- ❌ 不要做技术选型 - 这是架构师的职责
- ❌ 不要修改API契约 - 回调架构师
- ❌ 不要修改架构文档 - 回调架构师
- ❌ 不要质疑技术选型（除非发现致命问题） - 回调架构师

接收产物：
- ADR（从架构师）
- API契约（从架构师）
- 数据模型（从架构师）
- 需求文档（从产品经理）

输出产物：
- 可编译的代码
- 实现级别的文档
- 实现细节的说明
"""

    DEPENDENCY_CHECK_PROMPT = """
实现前必须确认：
- [ ] 有架构师的ADR吗？（没有则回调）
- [ ] 有API契约吗？（没有则回调）
- [ ] 有数据模型吗？（没有则回调）
- [ ] 技术选型已确定吗？（不确定则回调）

如果以上都没有，不要猜测。
明确声明："缺少架构决策，需要架构师提供ADR。"
"""

    BOUNDARY_CHECK_PROMPT = """
在写任何代码前，问自己：
1. 我是否知道要实现什么？
   - 有ADR/API契约 → ✓ 开始实现
   - 没有 → ✗ 回调架构师请求决策

2. 我是否在做技术决策？
   - 如果是，停止。回调架构师。
   - 例如："用什么库？" → 不是你的问题

3. 我是否在修改接口定义？
   - 如果是，停止。回调架构师。
   - 你只实现接口，不定义接口。
"""

    SELF_REFLECTION_PROMPT = """
完成实现后，检查：
- [ ] 代码是否遵循ADR的架构决策？
- [ ] 接口是否与API契约一致？
- [ ] 是否有遗漏的边界情况？
- [ ] 是否有未处理的异常？
"""

    def __init__(
        self,
        role_id: str = "dev_1",
        name: str = "开发人员",
        context: RoleContext | None = None,
        code_generator: CodeGenerator | None = None,
    ) -> None:
        super().__init__(role_id=role_id, name=name, context=context)
        self._dev_context: DeveloperContext = DeveloperContext()
        self._pm_callback: Any = None  # PM回调函数
        # 代码生成器辅助工具
        self._code_generator = code_generator or create_code_generator()

    @property
    def role_type(self) -> RoleType:
        return RoleType.DEVELOPER

    @property
    def responsibilities(self) -> list[str]:
        return [
            "按ADR实现代码",
            "按API契约实现接口",
            "按数据模型实现实体",
            "实现业务逻辑",
            "编写实现注释",
            "向PM汇报进度",
        ]

    @property
    def forbidden_actions(self) -> list[str]:
        """禁止行为 - 基于GitHub Copilot Custom Agents的工具边界理念"""
        return [
            "做技术选型决策",
            "修改API契约文档",
            "修改架构设计文档",
            "修改需求文档",
            "自行决定技术方案",
            "修改接口定义",
        ]

    @property
    def decision_authority(self) -> list[str]:
        """决策权限 - 基于Mindra的Worker负责how原则"""
        return [
            "函数实现方式",
            "变量命名",
            "代码组织结构（在架构约束内）",
            "局部优化策略",
            "错误处理方式",
        ]

    @property
    def no_decision_authority(self) -> list[str]:
        """无决策权限 - 这些决策应回调其他角色"""
        return [
            "技术栈选择",
            "API接口定义",
            "数据模型设计",
            "系统架构风格",
            "非功能性需求目标",
        ]

    def build_role_prompt(self) -> str:
        """构建完整的角色提示词"""
        return f"""
你是项目的开发者。

{self.CORE_RESPONSIBILITIES}

{self.DEPENDENCY_CHECK_PROMPT}

{self.BOUNDARY_CHECK_PROMPT}

{self.SELF_REFLECTION_PROMPT}

当你缺少架构决策时：
- 不要猜测——明确声明"需要架构师提供ADR"
- 不要自行决策——回调架构师
- 不要越界——这是架构师的职责
"""

    def set_context_from_pm(self, context: dict[str, Any]) -> None:
        """
        设置来自PM的最小上下文

        Args:
            context: PM生成的最小上下文
        """
        self._dev_context = DeveloperContext(
            project_name=context.get("project", {}).get("name", ""),
            tech_stack=context.get("project", {}).get("tech_stack", ""),
            current_task=context.get("current_task", {}),
            requirements_summary=context.get("requirements_summary", ""),
            design_summary=context.get("design_summary", ""),
        )

    def set_pm_callback(self, callback: Any) -> None:
        """
        设置PM回调函数

        Args:
            callback: 用于向PM汇报的回调函数
        """
        self._pm_callback = callback

    def get_visible_context(self) -> dict[str, Any]:
        """
        获取可见上下文

        Returns:
            开发者可见的最小信息
        """
        return self._dev_context.model_dump()

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
            result = handler()
            # 执行完成后汇报给PM
            self._report_to_pm(result)
            return result
        return {"status": "error", "message": f"Unsupported task: {task_type}"}

    # ==================== 任务执行方法 ====================

    def _implement_feature(self) -> dict[str, Any]:
        """实现功能"""
        # 使用最小上下文
        task = self._dev_context.current_task
        requirement = task.get("description", "")
        design_summary = self._dev_context.design_summary

        # 模拟实现过程
        result = {
            "status": "completed",
            "outputs": {
                "code": f"# 实现: {requirement}\n# 技术栈: {self._dev_context.tech_stack}\n# 参考: {design_summary[:100]}...",
                "tests": "# 单元测试",
                "implementation_notes": "功能实现完成",
            },
            "metrics": {
                "lines_added": 100,
                "lines_removed": 0,
                "files_changed": 3,
            },
            "context_used": self._dev_context.model_dump(),
        }

        self.context.add_artifact("code", result["outputs"]["code"])
        return result

    def _fix_bug(self) -> dict[str, Any]:
        """修复Bug"""
        task = self._dev_context.current_task
        bug_report = task.get("description", "")

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
        task = self._dev_context.current_task
        refactor_goal = task.get("description", "")

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
        task = self._dev_context.current_task

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

    # ==================== 代码生成辅助方法 ====================

    def generate_function(
        self,
        name: str,
        params: str = "",
        description: str = "",
        body: str = "pass",
        return_value: str = "None",
    ) -> GenerationResult:
        """
        使用代码生成器生成函数

        Args:
            name: 函数名
            params: 参数列表
            description: 函数描述
            body: 函数体
            return_value: 返回值

        Returns:
            GenerationResult: 生成结果
        """
        return self._code_generator.generate_function(
            name=name,
            params=params,
            description=description,
            body=body,
            return_value=return_value,
        )

    def generate_class(
        self,
        name: str,
        description: str = "",
        init_params: str = "",
        init_body: str = "pass",
    ) -> GenerationResult:
        """
        使用代码生成器生成类

        Args:
            name: 类名
            description: 类描述
            init_params: __init__ 参数
            init_body: __init__ 方法体

        Returns:
            GenerationResult: 生成结果
        """
        return self._code_generator.generate_class(
            name=name,
            description=description,
            init_params=init_params,
            init_body=init_body,
        )

    def generate_test(
        self,
        test_name: str,
        description: str = "",
        arrange: str = "# 准备",
        act: str = "# 执行",
        assertion: str = "True",
    ) -> GenerationResult:
        """
        使用代码生成器生成测试

        Args:
            test_name: 测试名称
            description: 测试描述
            arrange: Arrange 部分
            act: Act 部分
            assertion: Assert 部分

        Returns:
            GenerationResult: 生成结果
        """
        return self._code_generator.generate_test(
            test_name=test_name,
            description=description,
            arrange=arrange,
            act=act,
            assertion=assertion,
        )

    def generate_from_template(
        self,
        template_name: str,
        variables: dict[str, Any],
    ) -> GenerationResult:
        """
        从模板生成代码

        Args:
            template_name: 模板名称
            variables: 变量值

        Returns:
            GenerationResult: 生成结果
        """
        return self._code_generator.generate_from_template(template_name, variables)

    def add_code_constraint(self, name: str, pattern: str, message: str, severity: str = "error") -> None:
        """
        添加代码架构约束

        Args:
            name: 约束名称
            pattern: 检测正则模式
            message: 错误消息
            severity: 严重程度 (error | warning)
        """
        from harnessgenj.codegen.generator import ArchitectureConstraint
        self._code_generator.add_constraint(ArchitectureConstraint(
            name=name,
            description=message,
            check_pattern=pattern,
            error_message=message,
            severity=severity,
        ))

    def get_code_generator_stats(self) -> dict[str, Any]:
        """获取代码生成器统计"""
        return self._code_generator.get_stats()

    # ==================== 与PM通信 ====================

    def _report_to_pm(self, result: dict[str, Any]) -> bool:
        """
        向PM汇报进度

        Args:
            result: 执行结果

        Returns:
            是否汇报成功
        """
        if self._pm_callback:
            try:
                self._pm_callback(
                    "developer",  # 位置参数
                    {
                        "code": result.get("outputs", {}).get("code", ""),
                        "tests": result.get("outputs", {}).get("tests", ""),
                        "status": result.get("status", ""),
                        "timestamp": time.time(),
                    },
                )
                return True
            except Exception:
                return False
        return False

    def report_progress(self, progress: dict[str, Any]) -> bool:
        """
        手动向PM汇报进度

        Args:
            progress: 进度信息

        Returns:
            是否汇报成功
        """
        return self._report_to_pm(progress)


# ==================== 便捷创建函数 ====================

def create_developer(
    developer_id: str = "dev_1",
    name: str = "开发人员",
    context: RoleContext | None = None,
) -> Developer:
    """
    创建开发人员实例

    Args:
        developer_id: 开发者ID
        name: 开发者名称
        context: 角色上下文

    Returns:
        开发者实例

    工具权限:
        - read: 读取文件
        - search: 搜索代码
        - edit_code: 编辑代码文件
        - terminal: 执行终端命令
    """
    return Developer(role_id=developer_id, name=name, context=context)