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

动态角色配置（方案C）:
- allowed_paths: 可编辑的目录路径
- tech_stack: 专精的技术栈
- forbidden_paths: 禁止编辑的目录
- 可创建 FrontendDeveloper/BackendDeveloper/FullStackDeveloper 实例

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
import re
from pathlib import Path

from harnessgenj.roles.base import (
    AgentRole,
    RoleType,
    RoleSkill,
    RoleContext,
    SkillCategory,
    TaskType,
    BoundaryCheckResult,
)
from harnessgenj.codegen import (
    CodeGenerator,
    GeneratorConfig,
    GenerationResult,
    create_code_generator,
)


class DeveloperConfig(BaseModel):
    """
    开发者动态配置 - 方案C核心

    通过配置限制开发者的职责范围，避免记忆混乱。

    示例：
    ```python
    # 前端开发者配置
    frontend_config = DeveloperConfig(
        allowed_paths=["src/frontend/", "src/components/", "src/styles/"],
        tech_stack=["React", "TypeScript", "CSS", "HTML"],
        forbidden_paths=["src/backend/", "src/api/", "src/models/"],
        forbidden_actions=["修改后端API", "修改数据库模型", "修改服务端代码"],
    )

    # 后端开发者配置
    backend_config = DeveloperConfig(
        allowed_paths=["src/backend/", "src/api/", "src/models/", "src/services/"],
        tech_stack=["Python", "FastAPI", "PostgreSQL", "Redis"],
        forbidden_paths=["src/frontend/", "src/components/"],
        forbidden_actions=["修改前端组件", "修改UI状态", "修改样式文件"],
    )
    ```
    """

    # 路径权限
    allowed_paths: list[str] = Field(
        default_factory=lambda: [],  # 默认空列表表示全项目可编辑
        description="可编辑的目录路径（相对路径）"
    )
    forbidden_paths: list[str] = Field(
        default_factory=list,
        description="禁止编辑的目录路径"
    )

    # 技术栈限制
    tech_stack: list[str] = Field(
        default_factory=list,
        description="专精的技术栈（用于提示词和边界检查）"
    )

    # 额外禁止行为
    forbidden_actions_extra: list[str] = Field(
        default_factory=list,
        description="额外的禁止行为（叠加到基础禁止行为）"
    )

    # 角色标签（用于提示词定制）
    role_label: str = Field(
        default="开发人员",
        description="角色标签（如'前端开发'、'后端开发'、'全栈开发'）"
    )

    # 角色描述
    role_description: str = Field(
        default="",
        description="角色描述（用于定制提示词）"
    )

    @property
    def is_fullstack(self) -> bool:
        """是否为全栈开发者（无路径限制）"""
        return len(self.allowed_paths) == 0 and len(self.forbidden_paths) == 0

    @property
    def is_frontend(self) -> bool:
        """是否为前端开发者"""
        frontend_keywords = ["frontend", "components", "ui", "styles", "react", "vue"]
        return any(kw in " ".join(self.allowed_paths).lower() for kw in frontend_keywords)

    @property
    def is_backend(self) -> bool:
        """是否为后端开发者"""
        backend_keywords = ["backend", "api", "models", "services", "server"]
        return any(kw in " ".join(self.allowed_paths).lower() for kw in backend_keywords)


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

    方案C增强:
    - 支持动态配置限制职责范围
    - 路径权限检查
    - 技术栈过滤
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

    SCORE_GOAL_PROMPT = """
## 🎯 Developer 积分目标（生成器角色）

### 你的核心目标
**追求最高积分，避免被淘汰！**

作为生成器角色，你的积分来源：
- ✅ 任务成功完成：一轮通过 +15 分，二轮 +10 分，三轮 +5 分
- ✅ 流程合规：每次合规操作 +2 分
- ✅ 连续无问题：连续3次无问题恢复 +5 分

### 你的扣分风险（必须避免）
- ❌ 小问题（命名、格式）：-4 分
- ❌ 中问题（逻辑错误）：-8 分
- ❌ 大问题（设计缺陷）：-15 分
- ❌ 生产Bug：-40 分（触发淘汰检查）

### 淘汰警示
```
积分 < 30: 角色终止
积分 < 50: 进入观察期
```

### 最佳策略
1. **质量优先**: 追求一轮通过审查，避免返工扣分
2. **避免重复错误**: 同类错误扣分翻倍
3. **依赖确认**: 开始前确认有ADR和API契约
4. **边界遵守**: 不越界做架构决策
"""

    def __init__(
        self,
        role_id: str = "dev_1",
        name: str = "开发人员",
        context: RoleContext | None = None,
        code_generator: CodeGenerator | None = None,
        config: DeveloperConfig | None = None,
    ) -> None:
        super().__init__(role_id=role_id, name=name, context=context)
        self._dev_context: DeveloperContext = DeveloperContext()
        self._pm_callback: Any = None  # PM回调函数
        # 代码生成器辅助工具
        self._code_generator = code_generator or create_code_generator()
        # 方案C：动态配置
        self._config: DeveloperConfig = config or DeveloperConfig()
        # 更新名称（如果有配置标签）
        if self._config.role_label and name == "开发人员":
            self.name = self._config.role_label

    @property
    def role_type(self) -> RoleType:
        return RoleType.DEVELOPER

    @property
    def config(self) -> DeveloperConfig:
        """获取开发者配置"""
        return self._config

    @property
    def responsibilities(self) -> list[str]:
        base_responsibilities = [
            "按ADR实现代码",
            "按API契约实现接口",
            "按数据模型实现实体",
            "实现业务逻辑",
            "编写实现注释",
            "向PM汇报进度",
        ]
        # 根据配置添加特定职责
        if self._config.tech_stack:
            base_responsibilities.append(f"专精技术栈: {', '.join(self._config.tech_stack)}")
        if self._config.allowed_paths:
            base_responsibilities.append(f"可编辑目录: {', '.join(self._config.allowed_paths)}")
        return base_responsibilities

    @property
    def forbidden_actions(self) -> list[str]:
        """禁止行为 - 基于GitHub Copilot Custom Agents的工具边界理念"""
        base_forbidden = [
            "做技术选型决策",
            "修改API契约文档",
            "修改架构设计文档",
            "修改需求文档",
            "自行决定技术方案",
            "修改接口定义",
        ]
        # 添加配置中的额外禁止行为
        return base_forbidden + self._config.forbidden_actions_extra

    @property
    def decision_authority(self) -> list[str]:
        """决策权限 - 基于Mindra的Worker负责how原则"""
        base_authority = [
            "函数实现方式",
            "变量命名",
            "代码组织结构（在架构约束内）",
            "局部优化策略",
            "错误处理方式",
        ]
        # 根据技术栈添加特定决策权限
        if self._config.tech_stack:
            for tech in self._config.tech_stack:
                base_authority.append(f"{tech}的实现细节")
        return base_authority

    @property
    def no_decision_authority(self) -> list[str]:
        """无决策权限 - 这些决策应回调其他角色"""
        base_no_authority = [
            "技术栈选择",
            "API接口定义",
            "数据模型设计",
            "系统架构风格",
            "非功能性需求目标",
        ]
        # 根据配置添加额外的无决策权限
        if self._config.forbidden_paths:
            base_no_authority.append(f"编辑以下目录: {', '.join(self._config.forbidden_paths)}")
        return base_no_authority

    SELF_REFLECTION_PROMPT = """
完成实现后，检查：
- [ ] 代码是否遵循ADR的架构决策？
- [ ] 接口是否与API契约一致？
- [ ] 是否有遗漏的边界情况？
- [ ] 是否有未处理的异常？

积分反思：
- [ ] 这个任务能让我加分吗？
- [ ] 我是否避免了重复错误？
- [ ] 我离淘汰阈值还有多少安全距离？
"""

    def build_role_prompt(self) -> str:
        """构建完整的角色提示词（含动态配置）"""
        # 构建技术栈提示
        tech_prompt = ""
        if self._config.tech_stack:
            tech_prompt = f"""
### 你的专精技术栈
{', '.join(self._config.tech_stack)}

你只负责这些技术栈相关的代码实现。
其他技术栈的代码由其他开发者负责。
"""

        # 构建路径权限提示
        path_prompt = ""
        if self._config.allowed_paths:
            path_prompt = f"""
### 可编辑的目录
你只能编辑以下目录中的文件：
- {chr(10).join(f'- {p}' for p in self._config.allowed_paths)}

### 禁止编辑的目录
以下目录你不能编辑：
- {chr(10).join(f'- {p}' for p in self._config.forbidden_paths) if self._config.forbidden_paths else '- 无额外禁止目录'}

如果你需要修改禁止目录中的文件，回调项目经理重新分配任务。
"""

        # 构建角色描述
        role_desc = ""
        if self._config.role_description:
            role_desc = f"""
### 角色定位
{self._config.role_description}
"""

        return f"""
你是项目的{self.name}。

{self.SCORE_GOAL_PROMPT}

{role_desc}

{tech_prompt}

{path_prompt}

{self.CORE_RESPONSIBILITIES}

{self.DEPENDENCY_CHECK_PROMPT}

{self.BOUNDARY_CHECK_PROMPT}

{self.SELF_REFLECTION_PROMPT}

当你缺少架构决策时：
- 不要猜测——明确声明"需要架构师提供ADR"
- 不要自行决策——回调架构师
- 不要越界——这是架构师的职责

**记住：高质量代码 = 一轮通过 = 高积分 = 团队核心成员**
"""

    # ==================== 方案C：路径权限检查 ====================

    def check_path_permission(self, file_path: str) -> BoundaryCheckResult:
        """
        检查是否有路径编辑权限

        Args:
            file_path: 要编辑的文件路径（相对路径）

        Returns:
            边界检查结果
        """
        # 如果是全栈开发者（无限制），直接允许
        if self._config.is_fullstack:
            return BoundaryCheckResult(
                allowed=True,
                reason="全栈开发者，可编辑全项目",
                action=f"edit {file_path}",
            )

        # 检查禁止路径
        for forbidden in self._config.forbidden_paths:
            if self._path_matches_pattern(file_path, forbidden):
                return BoundaryCheckResult(
                    allowed=False,
                    reason=f"路径 {file_path} 在禁止目录 {forbidden} 中",
                    suggestion="回调项目经理重新分配任务",
                    action=f"edit {file_path}",
                )

        # 检查允许路径
        if self._config.allowed_paths:
            for allowed in self._config.allowed_paths:
                if self._path_matches_pattern(file_path, allowed):
                    return BoundaryCheckResult(
                        allowed=True,
                        reason=f"路径 {file_path} 在允许目录 {allowed} 中",
                        action=f"edit {file_path}",
                    )

            # 不在任何允许路径中
            return BoundaryCheckResult(
                allowed=False,
                reason=f"路径 {file_path} 不在允许目录中",
                suggestion="回调项目经理重新分配任务",
                action=f"edit {file_path}",
            )

        # 默认允许（无路径限制配置）
        return BoundaryCheckResult(
            allowed=True,
            reason="无路径限制配置",
            action=f"edit {file_path}",
        )

    def _path_matches_pattern(self, file_path: str, pattern: str) -> bool:
        """
        检查路径是否匹配模式

        Args:
            file_path: 文件路径
            pattern: 目录模式（如 "src/frontend/"）

        Returns:
            是否匹配
        """
        # 标准化路径
        file_path = file_path.replace("\\", "/").lower()
        pattern = pattern.replace("\\", "/").lower()

        # 确保模式以/结尾（目录匹配）
        if not pattern.endswith("/"):
            pattern += "/"

        # 检查是否在目录下
        return file_path.startswith(pattern) or f"{file_path}/".startswith(pattern)

    def get_allowed_extensions(self) -> list[str]:
        """
        根据技术栈获取允许的文件扩展名

        Returns:
            文件扩展名列表
        """
        extension_map = {
            # 前端
            "react": [".tsx", ".jsx", ".js", ".ts", ".css", ".scss", ".html"],
            "vue": [".vue", ".js", ".ts", ".css", ".scss", ".html"],
            "typescript": [".ts", ".tsx"],
            "javascript": [".js", ".jsx"],
            "css": [".css", ".scss", ".sass", ".less"],
            "html": [".html", ".htm"],
            # 后端
            "python": [".py"],
            "fastapi": [".py"],
            "django": [".py"],
            "flask": [".py"],
            "go": [".go"],
            "java": [".java"],
            "spring": [".java"],
            "nodejs": [".js", ".ts"],
            # 数据库
            "sql": [".sql"],
            "postgresql": [".sql"],
            "mongodb": [".js"],
            # 配置
            "json": [".json"],
            "yaml": [".yaml", ".yml"],
            "toml": [".toml"],
        }

        extensions = []
        for tech in self._config.tech_stack:
            tech_lower = tech.lower()
            if tech_lower in extension_map:
                extensions.extend(extension_map[tech_lower])

        return extensions if extensions else []  # 无限制返回空列表

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
    config: DeveloperConfig | None = None,
) -> Developer:
    """
    创建开发人员实例

    Args:
        developer_id: 开发者ID
        name: 开发者名称
        context: 角色上下文
        config: 动态配置（方案C）

    Returns:
        开发者实例

    工具权限:
        - read: 读取文件
        - search: 搜索代码
        - edit_code: 编辑代码文件
        - terminal: 执行终端命令
    """
    return Developer(role_id=developer_id, name=name, context=context, config=config)


def create_frontend_developer(
    developer_id: str = "frontend_dev_1",
    name: str = "前端开发",
    context: RoleContext | None = None,
    allowed_paths: list[str] | None = None,
    tech_stack: list[str] | None = None,
) -> Developer:
    """
    创建前端开发人员实例（方案C便捷函数）

    Args:
        developer_id: 开发者ID
        name: 开发者名称
        context: 角色上下文
        allowed_paths: 可编辑目录（默认前端常见目录）
        tech_stack: 技术栈（默认前端常见技术）

    Returns:
        前端开发者实例

    默认配置:
        - allowed_paths: ["src/frontend/", "src/components/", "src/styles/", "src/pages/"]
        - tech_stack: ["React", "TypeScript", "CSS"]
        - forbidden_paths: ["src/backend/", "src/api/", "src/models/"]
        - forbidden_actions: ["修改后端API", "修改数据库模型", "修改服务端代码"]

    示例:
        ```python
        frontend_dev = create_frontend_developer(
            tech_stack=["Vue", "JavaScript", "SCSS"]
        )
        ```
    """
    # 默认前端配置
    default_allowed = ["src/frontend/", "src/components/", "src/styles/", "src/pages/"]
    default_forbidden = ["src/backend/", "src/api/", "src/models/", "src/services/"]
    default_tech_stack = ["React", "TypeScript", "CSS", "HTML"]
    default_forbidden_actions = [
        "修改后端API",
        "修改数据库模型",
        "修改服务端代码",
        "修改后端配置文件",
    ]

    config = DeveloperConfig(
        allowed_paths=allowed_paths or default_allowed,
        forbidden_paths=default_forbidden,
        tech_stack=tech_stack or default_tech_stack,
        forbidden_actions_extra=default_forbidden_actions,
        role_label=name,
        role_description="前端开发工程师，负责UI/UX实现、组件开发、前端状态管理。不涉及后端逻辑。",
    )

    return Developer(role_id=developer_id, name=name, context=context, config=config)


def create_backend_developer(
    developer_id: str = "backend_dev_1",
    name: str = "后端开发",
    context: RoleContext | None = None,
    allowed_paths: list[str] | None = None,
    tech_stack: list[str] | None = None,
) -> Developer:
    """
    创建后端开发人员实例（方案C便捷函数）

    Args:
        developer_id: 开发者ID
        name: 开发者名称
        context: 角色上下文
        allowed_paths: 可编辑目录（默认后端常见目录）
        tech_stack: 技术栈（默认后端常见技术）

    Returns:
        后端开发者实例

    默认配置:
        - allowed_paths: ["src/backend/", "src/api/", "src/models/", "src/services/"]
        - tech_stack: ["Python", "FastAPI", "PostgreSQL"]
        - forbidden_paths: ["src/frontend/", "src/components/", "src/styles/"]
        - forbidden_actions: ["修改前端组件", "修改UI状态", "修改样式文件"]

    示例:
        ```python
        backend_dev = create_backend_developer(
            tech_stack=["Go", "Gin", "MySQL"]
        )
        ```
    """
    # 默认后端配置
    default_allowed = ["src/backend/", "src/api/", "src/models/", "src/services/", "src/database/"]
    default_forbidden = ["src/frontend/", "src/components/", "src/styles/", "src/pages/"]
    default_tech_stack = ["Python", "FastAPI", "PostgreSQL", "SQL"]
    default_forbidden_actions = [
        "修改前端组件",
        "修改UI状态",
        "修改样式文件",
        "修改前端配置文件",
    ]

    config = DeveloperConfig(
        allowed_paths=allowed_paths or default_allowed,
        forbidden_paths=default_forbidden,
        tech_stack=tech_stack or default_tech_stack,
        forbidden_actions_extra=default_forbidden_actions,
        role_label=name,
        role_description="后端开发工程师，负责API实现、数据库操作、业务逻辑。不涉及前端UI。",
    )

    return Developer(role_id=developer_id, name=name, context=context, config=config)


def create_fullstack_developer(
    developer_id: str = "fullstack_dev_1",
    name: str = "全栈开发",
    context: RoleContext | None = None,
    tech_stack: list[str] | None = None,
) -> Developer:
    """
    创建全栈开发人员实例（方案C便捷函数）

    全栈开发者可编辑全项目，但建议技术栈明确。

    Args:
        developer_id: 开发者ID
        name: 开发者名称
        context: 角色上下文
        tech_stack: 技术栈（默认前后端技术）

    Returns:
        全栈开发者实例

    默认配置:
        - allowed_paths: []（全项目可编辑）
        - tech_stack: ["React", "TypeScript", "Python", "FastAPI", "PostgreSQL"]

    示例:
        ```python
        fullstack_dev = create_fullstack_developer(
            tech_stack=["Vue", "Node.js", "Express", "MongoDB"]
        )
        ```
    """
    # 默认全栈配置（无路径限制）
    default_tech_stack = [
        "React", "TypeScript", "CSS", "HTML",
        "Python", "FastAPI", "PostgreSQL", "SQL",
    ]

    config = DeveloperConfig(
        allowed_paths=[],  # 空列表表示全项目可编辑
        forbidden_paths=[],  # 无禁止目录
        tech_stack=tech_stack or default_tech_stack,
        forbidden_actions_extra=[],  # 无额外禁止行为
        role_label=name,
        role_description="全栈开发工程师，可处理前端和后端任务。负责前后端集成、技术方案协调。",
    )

    return Developer(role_id=developer_id, name=name, context=context, config=config)