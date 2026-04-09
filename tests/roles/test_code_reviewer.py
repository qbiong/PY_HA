"""
Tests for CodeReviewer Role - 代码审查者角色测试

测试代码审查者的核心功能：
- 代码审查
- 问题发现
- 规范检查
- 审查报告生成
"""

import pytest

from harnessgenj.roles.code_reviewer import (
    CodeReviewer,
    ReviewResult,
    create_code_reviewer,
)
from harnessgenj.roles.base import RoleContext, RoleType, TaskType, SkillCategory
from harnessgenj.quality.record import IssueRecord, IssueSeverity


class TestCodeReviewerCreation:
    """测试代码审查者创建"""

    def test_create_default(self):
        """使用默认参数创建"""
        reviewer = CodeReviewer()
        assert reviewer is not None
        assert reviewer.role_id == "reviewer_1"
        assert reviewer.name == "代码审查者"
        assert reviewer.role_type == RoleType.CODE_REVIEWER

    def test_create_with_custom_params(self):
        """使用自定义参数创建"""
        reviewer = CodeReviewer(
            role_id="reviewer_custom",
            name="高级审查者",
        )
        assert reviewer.role_id == "reviewer_custom"
        assert reviewer.name == "高级审查者"

    def test_create_with_context(self):
        """使用上下文创建"""
        context = RoleContext()
        reviewer = CodeReviewer(context=context)
        assert reviewer.context is not None

    def test_create_with_factory(self):
        """使用工厂函数创建"""
        reviewer = create_code_reviewer(reviewer_id="reviewer_factory", name="工厂审查者")
        assert reviewer.role_id == "reviewer_factory"
        assert reviewer.name == "工厂审查者"


class TestCodeReviewerResponsibilities:
    """测试代码审查者职责"""

    def test_responsibilities_list(self):
        """测试职责列表"""
        reviewer = CodeReviewer()
        responsibilities = reviewer.responsibilities

        assert len(responsibilities) == 6
        assert "代码质量审查（产出问题列表）" in responsibilities
        assert "安全漏洞检测（产出安全报告）" in responsibilities

    def test_forbidden_actions(self):
        """测试禁止行为"""
        reviewer = CodeReviewer()
        forbidden = reviewer.forbidden_actions

        assert len(forbidden) == 5
        assert "直接修改代码" in forbidden
        assert "给出完整修复代码" in forbidden

    def test_role_type(self):
        """测试角色类型"""
        reviewer = CodeReviewer()
        assert reviewer.role_type == RoleType.CODE_REVIEWER


class TestCodeReviewerSkills:
    """测试代码审查者技能"""

    def test_skills_setup(self):
        """测试技能设置"""
        reviewer = CodeReviewer()
        skills = reviewer.list_skills()

        assert len(skills) == 4

        skill_names = [s.name for s in skills]
        assert "review_code" in skill_names
        assert "detect_bugs" in skill_names
        assert "check_security" in skill_names


class TestReviewResult:
    """测试审查结果"""

    def test_review_result_creation(self):
        """测试审查结果创建"""
        result = ReviewResult(
            passed=True,
            score=85.0,
            summary="代码质量良好",
        )

        assert result.passed is True
        assert result.score == 85.0
        assert result.summary == "代码质量良好"
        assert result.issues == []
        assert result.suggestions == []

    def test_review_result_with_issues(self):
        """测试带问题的审查结果"""
        issues = [
            IssueRecord(
                issue_id="ISS-001",
                severity=IssueSeverity.MAJOR,
                description="缺少空值检查",
                location="main.py:42",
                found_by="reviewer_1",
            ),
        ]

        result = ReviewResult(
            passed=False,
            issues=issues,
            score=60.0,
            summary="发现1个主要问题",
        )

        assert result.passed is False
        assert len(result.issues) == 1
        assert result.issues[0].severity == IssueSeverity.MAJOR


class TestCodeReviewerTaskExecution:
    """测试任务执行"""

    def test_supported_task_types(self):
        """测试支持的任务类型"""
        reviewer = CodeReviewer()
        task_types = reviewer.get_supported_task_types()

        assert TaskType.CODE_REVIEW in task_types

    def test_review_method(self):
        """测试代码审查方法"""
        reviewer = CodeReviewer()

        code = '''
def calculate(x, y):
    return x / y

def process(data):
    result = data.value
    return result
'''

        result = reviewer.review(code)

        assert result is not None
        assert isinstance(result, ReviewResult)

    def test_quick_review(self):
        """测试快速审查"""
        reviewer = CodeReviewer()

        code = "def test(): pass"
        passed, issues = reviewer.quick_review(code)

        assert isinstance(passed, bool)
        assert isinstance(issues, list)

    def test_execute_by_type_review(self):
        """测试按类型执行 - 代码审查"""
        reviewer = CodeReviewer()
        reviewer._current_task = {
            "inputs": {
                "code": "def test(): pass"
            }
        }

        result = reviewer._execute_by_type(TaskType.CODE_REVIEW)

        assert result["status"] == "completed"

    def test_execute_by_type_unsupported(self):
        """测试不支持的任务类型"""
        reviewer = CodeReviewer()
        reviewer._current_task = {"inputs": {}}

        # IMPLEMENT_FEATURE 不在 CodeReviewer 支持的任务类型中
        result = reviewer._execute_by_type(TaskType.IMPLEMENT_FEATURE)

        assert result["status"] == "error"
        assert "Unsupported task" in result["message"]


class TestCodeReviewerPrompts:
    """测试角色提示词"""

    def test_build_role_prompt(self):
        """测试构建角色提示词"""
        reviewer = CodeReviewer()

        prompt = reviewer.build_role_prompt()

        assert "你的职责是**质疑**" in prompt
        assert "不要直接修改代码" in prompt

    def test_prompt_contains_philosophy(self):
        """测试提示词包含哲学定位"""
        reviewer = CodeReviewer()

        prompt = reviewer.build_role_prompt()

        assert "法官" in prompt or "诊断" in prompt


class TestCodeReviewerIntegration:
    """集成测试"""

    def test_full_review_workflow(self):
        """测试完整审查工作流"""
        # 1. 创建审查者
        reviewer = CodeReviewer()

        # 2. 设置审查目标
        code = '''
class UserService:
    def __init__(self, db):
        self.db = db

    def get_user(self, user_id):
        return self.db.query(user_id)

    def update_user(self, user_id, data):
        user = self.get_user(user_id)
        user.update(data)
        return user
'''

        # 3. 执行审查
        result = reviewer.review(code)

        # 4. 验证结果结构
        assert result is not None
        assert isinstance(result, ReviewResult)

    def test_get_last_review(self):
        """测试获取上次审查结果"""
        reviewer = CodeReviewer()

        # 先执行一次审查
        reviewer.review("def test(): pass")

        # 获取上次审查
        last = reviewer.get_last_review()
        assert last is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])