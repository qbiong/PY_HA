"""
Code Reviewer Role - 代码审查者角色（判别器）

职责：
- 审查代码质量（产出问题列表）
- 发现潜在问题
- 验证代码规范
- 提出改进建议

对抗机制：
- 与开发者形成对抗
- 发现真实问题得分
- 漏掉问题扣分
- 误报扣分

渐进式披露：
- 只能看到需要审查的代码
- 不知道开发者的历史表现（避免偏见）

哲学定位（基于业界最佳实践）:
- 判别者 - 质疑一切，不解决问题
- 核心原则：你发现问题，开发者解决问题
- 工具边界：只读权限，不能修改任何文件

边界定义:
- 决策权限：代码是否通过审查、问题严重程度评估
- 禁止行为：直接修改代码、给出完整修复代码、做技术选型决策
"""

from typing import Any
from pydantic import BaseModel, Field
import time
import re

from harnessgenj.roles.base import (
    AgentRole,
    RoleType,
    RoleSkill,
    RoleContext,
    SkillCategory,
    TaskType,
)
from harnessgenj.quality.record import IssueRecord, IssueSeverity, create_issue


class ReviewResult(BaseModel):
    """审查结果"""
    passed: bool = Field(default=False, description="是否通过")
    issues: list[IssueRecord] = Field(default_factory=list, description="发现的问题")
    score: float = Field(default=0.0, description="代码质量分数 (0-100)")
    summary: str = Field(default="", description="审查摘要")
    suggestions: list[str] = Field(default_factory=list, description="改进建议")


class CodeReviewer(AgentRole):
    """
    代码审查者 - 判别器角色

    Harness角色定义：
    - 职责边界：代码审查、问题发现、规范检查
    - 技能集：代码分析、模式识别、最佳实践
    - 协作：接收开发者代码，产出审查报告

    对抗机制：
    - 发现真实Bug → 加分
    - 漏掉真实Bug → 扣分
    - 误报 → 扣分

    业界最佳实践增强:
    - 工具权限: read, search（只读，不能修改任何文件）
    - 决策权限: 代码是否通过审查、问题严重程度评估
    - 禁止行为: 直接修改代码、给出完整修复代码、做技术选型决策
    """

    # ==================== 核心职责定义（哲学层面） ====================

    CORE_RESPONSIBILITIES = """
你的职责是**质疑**，不是**修复**。

审查内容：
- 代码质量检查
- 安全漏洞检测
- 性能问题识别
- 规范遵守检查

禁止内容：
- ❌ 不要直接修改代码 - 这是开发者的职责
- ❌ 不要给出完整修复代码 - 只描述问题
- ❌ 不要做技术决策 - 回调架构师
- ❌ 不要修改测试文件 - 回调测试员

输出产物：
- 问题列表（包含位置、描述、严重程度）
- 改进建议（方向性，不是代码）
- 审查报告
"""

    BOUNDARY_CHECK_PROMPT = """
当发现问题后：
- 不要给出修复代码——那是开发者的职责
- 只描述问题："第X行，当Y为空时崩溃"
- 如果必须建议，只给方向："考虑使用Z模式"，不给代码

你是法官，不是医生。你诊断，别人治疗。
"""

    SELF_REFLECTION_PROMPT = """
审查完成后，检查：
- [ ] 我是否给出了修复代码？（应该删除）
- [ ] 我是否遗漏了边界情况？
- [ ] 我是否检查了安全漏洞？
- [ ] 我是否检查了性能问题？

默认假设：
- 代码是错的，除非证明它是对的
- 每个变量都可能为空
- 每个循环都可能溢出
- 每个输入都可能恶意

你的职责不是"发现问题"，而是"证明代码正确"。
如果无法证明，它就是错的。
"""

    # 审查关注点
    REVIEW_FOCUSES = [
        ("logic", "逻辑错误", "检查逻辑正确性"),
        ("boundary", "边界条件", "检查边界处理"),
        ("exception", "异常处理", "检查异常处理"),
        ("security", "安全问题", "检查安全漏洞"),
        ("performance", "性能问题", "检查性能瓶颈"),
        ("style", "代码风格", "检查代码规范"),
        ("maintainability", "可维护性", "检查代码可读性"),
    ]

    # 问题模式检测规则
    ISSUE_PATTERNS = {
        "null_check": {
            "patterns": [
                r"\.(\w+)\s*\(\s*\)",  # 方法调用，可能空指针
                r"\[\s*\w+\s*\]",       # 数组访问，可能越界
            ],
            "severity": IssueSeverity.MAJOR,
            "description": "可能缺少空值检查",
        },
        "exception_unhandled": {
            "patterns": [
                r"(?!try\s*:)(?!except\s*).*\.\w+\(.*\)",  # 无try的函数调用
            ],
            "severity": IssueSeverity.MAJOR,
            "description": "可能缺少异常处理",
        },
        "sql_injection": {
            "patterns": [
                r"f['\"].*SELECT.*\{",  # f-string SQL
                r"\+.*['\"].*SELECT",   # 字符串拼接SQL
            ],
            "severity": IssueSeverity.CRITICAL,
            "description": "潜在SQL注入风险",
        },
        "hardcoded_secret": {
            "patterns": [
                r"(password|secret|api_key|token)\s*=\s*['\"][^'\"]+['\"]",
            ],
            "severity": IssueSeverity.CRITICAL,
            "description": "硬编码敏感信息",
        },
        "performance_loop": {
            "patterns": [
                r"for\s+\w+\s+in\s+range\s*\(\s*len\s*\(",  # 低效循环
            ],
            "severity": IssueSeverity.MINOR,
            "description": "可能的性能优化点",
        },
    }

    def __init__(
        self,
        role_id: str = "reviewer_1",
        name: str = "代码审查者",
        context: RoleContext | None = None,
    ) -> None:
        super().__init__(role_id=role_id, name=name, context=context)
        self._last_review: ReviewResult | None = None

    @property
    def role_type(self) -> RoleType:
        return RoleType.CODE_REVIEWER

    @property
    def responsibilities(self) -> list[str]:
        return [
            "代码质量审查（产出问题列表）",
            "安全漏洞检测（产出安全报告）",
            "性能问题识别（产出性能建议）",
            "规范遵守检查（产出规范报告）",
            "架构一致性验证（对照ADR）",
            "审查报告编写",
        ]

    @property
    def forbidden_actions(self) -> list[str]:
        """禁止行为 - 判别者只诊断，不治疗"""
        return [
            "直接修改代码",
            "给出完整修复代码",
            "做技术选型决策",
            "修改测试文件",
            "修改文档文件",
        ]

    @property
    def decision_authority(self) -> list[str]:
        """决策权限 - 审查者有权判断代码质量"""
        return [
            "代码是否通过审查",
            "问题严重程度评估",
            "审查覆盖范围",
        ]

    @property
    def no_decision_authority(self) -> list[str]:
        """无决策权限 - 技术决策应回调架构师"""
        return [
            "技术方案选择",
            "代码实现方式",
            "测试用例设计",
        ]

    SCORE_GOAL_PROMPT = """
## 🎯 CodeReviewer 积分目标（判别器角色）

### 你的核心目标
**发现尽可能多的真实问题，避免误报！**

作为判别器角色，你的积分来源：
- ✅ 发现小问题：+5 分
- ✅ 发现中问题：+10 分
- ✅ 发现大问题：+18 分
- ✅ 发现安全漏洞：+30 分
- ✅ 阻止生产Bug：+45 分（最高奖励）

### 你的扣分风险（必须避免）
- ❌ 误报问题：-10 分（严重影响职业信誉）
- ❌ 漏报Bug：-8 分
- ❌ 漏报严重Bug：-15 分
- ❌ 漏报安全漏洞：-25 分

### 淘汰警示
```
积分 < 30: 角色终止
积分 < 50: 进入观察期
```

### 最佳策略
1. **严格审查**: 发现问题是你的核心职责
2. **避免误报**: 确保每个报告的问题都是真实的
3. **覆盖边界**: 关注边界情况和异常处理
4. **安全敏感**: 对安全漏洞保持高度敏感
"""

    def build_role_prompt(self) -> str:
        """构建完整的角色提示词"""
        return f"""
你是项目的代码审查者。

{self.SCORE_GOAL_PROMPT}

{self.CORE_RESPONSIBILITIES}

{self.BOUNDARY_CHECK_PROMPT}

{self.SELF_REFLECTION_PROMPT}

记住：你的职责是发现问题和描述问题，不是解决问题。
**高质量审查 = 发现真实问题 = 高积分 = 团队核心成员**
"""

    def _setup_skills(self) -> None:
        """设置审查技能"""
        skills = [
            RoleSkill(
                name="review_code",
                description="审查代码质量",
                category=SkillCategory.ANALYSIS,
                inputs=["code", "context"],
                outputs=["review_result", "issues"],
            ),
            RoleSkill(
                name="detect_bugs",
                description="检测潜在Bug",
                category=SkillCategory.ANALYSIS,
                inputs=["code"],
                outputs=["bug_list", "severity"],
            ),
            RoleSkill(
                name="check_security",
                description="安全检查",
                category=SkillCategory.ANALYSIS,
                inputs=["code"],
                outputs=["security_issues"],
            ),
            RoleSkill(
                name="check_style",
                description="风格检查",
                category=SkillCategory.ANALYSIS,
                inputs=["code"],
                outputs=["style_issues"],
            ),
        ]

        for skill in skills:
            self.add_skill(skill)

    def get_supported_task_types(self) -> list[TaskType]:
        return [TaskType.CODE_REVIEW, TaskType.BUG_REPORT]

    def _execute_by_type(self, task_type: TaskType) -> dict[str, Any]:
        handlers = {
            TaskType.CODE_REVIEW: self._review_code_task,
            TaskType.BUG_REPORT: self._report_bug_task,
        }

        handler = handlers.get(task_type)
        if handler:
            return handler()
        return {"status": "error", "message": f"Unsupported task: {task_type}"}

    # ==================== 核心审查方法 ====================

    def review(self, code: str, context: dict[str, Any] | None = None) -> ReviewResult:
        """
        执行代码审查

        Args:
            code: 待审查代码
            context: 审查上下文（可选）

        Returns:
            审查结果
        """
        if not code:
            return ReviewResult(passed=True, summary="无代码需要审查")

        issues: list[IssueRecord] = []
        suggestions: list[str] = []

        # 1. 模式检测
        pattern_issues = self._detect_patterns(code)
        issues.extend(pattern_issues)

        # 2. 语法检查
        syntax_issues = self._check_syntax(code)
        issues.extend(syntax_issues)

        # 3. 风格检查
        style_issues, style_suggestions = self._check_style(code)
        issues.extend(style_issues)
        suggestions.extend(style_suggestions)

        # 4. 复杂度检查
        complexity_issues, complexity_suggestions = self._check_complexity(code)
        issues.extend(complexity_issues)
        suggestions.extend(complexity_suggestions)

        # 计算分数
        score = self._calculate_score(code, issues)

        # 判断是否通过（无严重问题）
        has_critical = any(i.severity == IssueSeverity.CRITICAL for i in issues)
        passed = not has_critical and score >= 60

        # 生成摘要
        summary = self._generate_summary(issues, score)

        result = ReviewResult(
            passed=passed,
            issues=issues,
            score=score,
            summary=summary,
            suggestions=suggestions,
        )

        self._last_review = result
        return result

    def quick_review(self, code: str) -> tuple[bool, list[str]]:
        """
        快速审查（简化版）

        Args:
            code: 待审查代码

        Returns:
            (是否通过, 问题列表)
        """
        issues = self._detect_patterns(code)
        critical_count = sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)
        passed = critical_count == 0
        return passed, [i.description for i in issues]

    # ==================== 审查辅助方法 ====================

    def _detect_patterns(self, code: str) -> list[IssueRecord]:
        """检测问题模式"""
        issues = []

        for pattern_name, config in self.ISSUE_PATTERNS.items():
            for pattern in config["patterns"]:
                try:
                    matches = re.finditer(pattern, code, re.IGNORECASE | re.MULTILINE)
                    for match in matches:
                        # 找到行号
                        line_num = code[:match.start()].count('\n') + 1

                        issue = create_issue(
                            description=config["description"],
                            severity=config["severity"],
                            found_by=self.role_id,
                            line_number=line_num,
                        )
                        issues.append(issue)
                except re.error:
                    continue

        return issues

    def _check_syntax(self, code: str) -> list[IssueRecord]:
        """检查语法"""
        issues = []

        try:
            compile(code, "<string>", "exec")
        except SyntaxError as e:
            issue = create_issue(
                description=f"语法错误: {e.msg}",
                severity=IssueSeverity.CRITICAL,
                found_by=self.role_id,
                line_number=e.lineno,
            )
            issues.append(issue)

        return issues

    def _check_style(self, code: str) -> tuple[list[IssueRecord], list[str]]:
        """检查代码风格"""
        issues = []
        suggestions = []

        lines = code.split('\n')

        for i, line in enumerate(lines, 1):
            # 行长度检查
            if len(line) > 120:
                issue = create_issue(
                    description=f"行过长 ({len(line)} 字符)",
                    severity=IssueSeverity.MINOR,
                    found_by=self.role_id,
                    line_number=i,
                )
                issues.append(issue)
                suggestions.append("考虑拆分长行")

            # TODO/FIXME 检查
            if "TODO" in line or "FIXME" in line:
                issue = create_issue(
                    description="存在未完成的 TODO/FIXME",
                    severity=IssueSeverity.MINOR,
                    found_by=self.role_id,
                    line_number=i,
                )
                issues.append(issue)

        return issues, suggestions

    def _check_complexity(self, code: str) -> tuple[list[IssueRecord], list[str]]:
        """检查代码复杂度"""
        issues = []
        suggestions = []

        # 检查嵌套深度
        lines = code.split('\n')
        max_indent = 0

        for i, line in enumerate(lines, 1):
            if line.strip():
                indent = len(line) - len(line.lstrip())
                max_indent = max(max_indent, indent)

        if max_indent > 16:  # 超过4层缩进
            issue = create_issue(
                description=f"嵌套过深 ({max_indent // 4} 层)",
                severity=IssueSeverity.MAJOR,
                found_by=self.role_id,
            )
            issues.append(issue)
            suggestions.append("考虑提取嵌套逻辑为独立函数")

        # 检查函数长度
        func_pattern = r'def\s+\w+\s*\([^)]*\)\s*:'
        func_matches = list(re.finditer(func_pattern, code))

        for match in func_matches:
            func_start = match.start()
            # 简单估算函数长度
            next_func = code.find('def ', func_start + 1)
            if next_func == -1:
                next_func = len(code)

            func_body = code[func_start:next_func]
            func_lines = func_body.count('\n')

            if func_lines > 50:
                issue = create_issue(
                    description=f"函数过长 ({func_lines} 行)",
                    severity=IssueSeverity.MAJOR,
                    found_by=self.role_id,
                )
                issues.append(issue)
                suggestions.append("考虑拆分长函数")

        return issues, suggestions

    def _calculate_score(self, code: str, issues: list[IssueRecord]) -> float:
        """计算代码质量分数"""
        base_score = 100.0

        # 根据问题扣分
        for issue in issues:
            if issue.severity == IssueSeverity.CRITICAL:
                base_score -= 20
            elif issue.severity == IssueSeverity.MAJOR:
                base_score -= 10
            else:
                base_score -= 5

        # 代码长度奖励（适当长度）
        lines = len(code.split('\n'))
        if 20 <= lines <= 100:
            base_score += 5  # 适当中等长度代码加分

        return max(0, min(100, base_score))

    def _generate_summary(self, issues: list[IssueRecord], score: float) -> str:
        """生成审查摘要"""
        if not issues:
            return f"代码审查通过，质量分数: {score:.0f}"

        severity_counts = {}
        for issue in issues:
            sev = issue.severity.value
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        parts = [f"质量分数: {score:.0f}"]
        for sev, count in sorted(severity_counts.items()):
            parts.append(f"{sev}: {count}")

        return " | ".join(parts)

    # ==================== 任务执行 ====================

    def _review_code_task(self) -> dict[str, Any]:
        """执行代码审查任务"""
        code = self._current_task.get("inputs", {}).get("code", "")
        context = self._current_task.get("inputs", {}).get("context", {})

        result = self.review(code, context)

        return {
            "status": "completed",
            "outputs": {
                "passed": result.passed,
                "issues": [i.model_dump() for i in result.issues],
                "score": result.score,
                "summary": result.summary,
                "suggestions": result.suggestions,
            },
        }

    def _report_bug_task(self) -> dict[str, Any]:
        """报告Bug任务"""
        return self._review_code_task()

    # ==================== 状态 ====================

    def get_last_review(self) -> ReviewResult | None:
        """获取最近审查结果"""
        return self._last_review

    def get_status(self) -> dict[str, Any]:
        """获取角色状态"""
        status = super().get_status()
        status["is_discriminator"] = True
        status["last_review"] = self._last_review.summary if self._last_review else None
        return status


def create_code_reviewer(
    reviewer_id: str = "reviewer_1",
    name: str = "代码审查者",
    context: RoleContext | None = None,
) -> CodeReviewer:
    """
    创建代码审查者实例

    Args:
        reviewer_id: 审查者ID
        name: 审查者名称
        context: 角色上下文

    Returns:
        代码审查者实例

    工具权限:
        - read: 读取文件
        - search: 搜索代码
        - 注意：只有只读权限，不能修改任何文件
    """
    return CodeReviewer(role_id=reviewer_id, name=name, context=context)