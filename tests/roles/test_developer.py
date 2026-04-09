"""
Tests for Developer Role - 开发人员角色测试

测试开发人员的核心功能：
- 代码实现
- Bug修复
- 代码重构
- 代码审查
- 代码生成辅助
"""

import pytest
import tempfile
import shutil

from harnessgenj.roles.developer import (
    Developer,
    DeveloperContext,
    create_developer,
)
from harnessgenj.roles.base import RoleContext, RoleType, TaskType, SkillCategory
from harnessgenj.codegen import GenerationResult


class TestDeveloperCreation:
    """测试开发人员创建"""

    def test_create_default(self):
        """使用默认参数创建"""
        dev = Developer()
        assert dev is not None
        assert dev.role_id == "dev_1"
        assert dev.name == "开发人员"
        assert dev.role_type == RoleType.DEVELOPER

    def test_create_with_custom_params(self):
        """使用自定义参数创建"""
        dev = Developer(
            role_id="dev_custom",
            name="高级开发人员",
        )
        assert dev.role_id == "dev_custom"
        assert dev.name == "高级开发人员"

    def test_create_with_context(self):
        """使用上下文创建"""
        context = RoleContext()
        dev = Developer(context=context)
        assert dev.context is not None

    def test_create_with_factory(self):
        """使用工厂函数创建"""
        dev = create_developer(developer_id="dev_factory", name="工厂开发人员")
        assert dev.role_id == "dev_factory"
        assert dev.name == "工厂开发人员"


class TestDeveloperResponsibilities:
    """测试开发人员职责"""

    def test_responsibilities_list(self):
        """测试职责列表"""
        dev = Developer()
        responsibilities = dev.responsibilities

        assert len(responsibilities) == 6
        assert "按ADR实现代码" in responsibilities
        assert "按API契约实现接口" in responsibilities
        assert "实现业务逻辑" in responsibilities

    def test_forbidden_actions(self):
        """测试禁止行为"""
        dev = Developer()
        forbidden = dev.forbidden_actions

        assert len(forbidden) == 6
        assert "做技术选型决策" in forbidden
        assert "修改API契约文档" in forbidden
        assert "修改架构设计文档" in forbidden

    def test_decision_authority(self):
        """测试决策权限"""
        dev = Developer()
        authority = dev.decision_authority

        assert len(authority) == 5
        assert "函数实现方式" in authority
        assert "变量命名" in authority

    def test_no_decision_authority(self):
        """测试无决策权限"""
        dev = Developer()
        no_authority = dev.no_decision_authority

        assert len(no_authority) == 5
        assert "技术栈选择" in no_authority
        assert "API接口定义" in no_authority


class TestDeveloperSkills:
    """测试开发人员技能"""

    def test_skills_setup(self):
        """测试技能设置"""
        dev = Developer()
        skills = dev.list_skills()

        assert len(skills) == 6

        skill_names = [s.name for s in skills]
        assert "implement_feature" in skill_names
        assert "fix_bug" in skill_names
        assert "refactor_code" in skill_names
        assert "review_code" in skill_names
        assert "debug" in skill_names
        assert "write_unit_test" in skill_names

    def test_skill_categories(self):
        """测试技能分类"""
        dev = Developer()
        skills = dev.list_skills()

        coding_skills = [s for s in skills if s.category == SkillCategory.CODING]
        testing_skills = [s for s in skills if s.category == SkillCategory.TESTING]

        assert len(coding_skills) == 5
        assert len(testing_skills) == 1


class TestDeveloperContext:
    """测试开发人员上下文"""

    def test_dev_context_creation(self):
        """测试上下文创建"""
        context = DeveloperContext(
            project_name="测试项目",
            tech_stack="Python + FastAPI",
            current_task={"description": "实现登录功能"},
            requirements_summary="需求摘要",
            design_summary="设计摘要",
        )

        assert context.project_name == "测试项目"
        assert context.tech_stack == "Python + FastAPI"
        assert context.current_task["description"] == "实现登录功能"
        assert context.requirements_summary == "需求摘要"
        assert context.design_summary == "设计摘要"

    def test_set_context_from_pm(self):
        """测试从项目经理设置上下文"""
        dev = Developer()

        dev.set_context_from_pm({
            "project": {
                "name": "电商平台",
                "tech_stack": "Python + FastAPI",
            },
            "current_task": {
                "description": "实现购物车功能",
            },
            "requirements_summary": "需求摘要",
            "design_summary": "设计摘要",
        })

        visible = dev.get_visible_context()
        assert visible["project_name"] == "电商平台"
        assert visible["tech_stack"] == "Python + FastAPI"
        assert visible["current_task"]["description"] == "实现购物车功能"

    def test_visible_context_is_minimal(self):
        """测试可见上下文是最小化的"""
        dev = Developer()
        dev.set_context_from_pm({
            "project": {"name": "项目", "tech_stack": "Python"},
            "current_task": {"description": "任务"},
        })

        visible = dev.get_visible_context()
        # 验证只有最小信息可见
        assert "project_name" in visible
        assert "tech_stack" in visible
        assert "current_task" in visible


class TestDeveloperTaskExecution:
    """测试任务执行"""

    def test_supported_task_types(self):
        """测试支持的任务类型"""
        dev = Developer()
        task_types = dev.get_supported_task_types()

        assert TaskType.IMPLEMENT_FEATURE in task_types
        assert TaskType.FIX_BUG in task_types
        assert TaskType.REFACTOR in task_types
        assert TaskType.CODE_REVIEW in task_types

    def test_implement_feature(self):
        """测试实现功能"""
        dev = Developer()
        dev.set_context_from_pm({
            "project": {"name": "测试项目", "tech_stack": "Python"},
            "current_task": {"description": "实现用户认证"},
            "design_summary": "使用JWT认证",
        })

        dev._current_task = {"inputs": {}}
        result = dev._implement_feature()

        assert result["status"] == "completed"
        assert "code" in result["outputs"]
        assert "tests" in result["outputs"]

    def test_fix_bug(self):
        """测试修复Bug"""
        dev = Developer()
        dev.set_context_from_pm({
            "project": {"name": "项目", "tech_stack": "Python"},
            "current_task": {"description": "修复空指针异常"},
        })

        dev._current_task = {"inputs": {}}
        result = dev._fix_bug()

        assert result["status"] == "completed"
        assert "fixed_code" in result["outputs"]
        assert "test_case" in result["outputs"]
        assert "root_cause" in result["outputs"]

    def test_refactor_code(self):
        """测试重构代码"""
        dev = Developer()
        dev.set_context_from_pm({
            "project": {"name": "项目", "tech_stack": "Python"},
            "current_task": {"description": "优化性能"},
        })

        dev._current_task = {"inputs": {}}
        result = dev._refactor_code()

        assert result["status"] == "completed"
        assert "refactored_code" in result["outputs"]

    def test_review_code(self):
        """测试代码审查"""
        dev = Developer()
        dev.set_context_from_pm({
            "project": {"name": "项目", "tech_stack": "Python"},
            "current_task": {"description": "审查代码"},
        })

        dev._current_task = {"inputs": {}}
        result = dev._review_code()

        assert result["status"] == "completed"
        assert "review_comments" in result["outputs"]
        assert "approved" in result["outputs"]

    def test_execute_by_type_implement(self):
        """测试按类型执行 - 实现功能"""
        dev = Developer()
        dev._current_task = {"inputs": {}}
        dev.set_context_from_pm({
            "project": {"name": "项目", "tech_stack": "Python"},
            "current_task": {"description": "任务"},
        })

        result = dev._execute_by_type(TaskType.IMPLEMENT_FEATURE)

        assert result["status"] == "completed"

    def test_execute_by_type_unsupported(self):
        """测试不支持的任务类型"""
        dev = Developer()
        dev._current_task = {"inputs": {}}

        # ANALYZE_REQUIREMENT 不在 Developer 支持的任务类型中
        result = dev._execute_by_type(TaskType.ANALYZE_REQUIREMENT)

        assert result["status"] == "error"
        assert "Unsupported task" in result["message"]


class TestDeveloperCodeGeneration:
    """测试代码生成辅助"""

    def test_generate_function(self):
        """测试函数生成"""
        dev = Developer()

        result = dev.generate_function(
            name="calculate_sum",
            params="a, b",
            description="计算两个数的和",
            body="return a + b",
            return_value="a + b",
        )

        assert result.success is True
        assert "def calculate_sum" in result.code
        assert "a, b" in result.code
        assert "return a + b" in result.code

    def test_generate_class(self):
        """测试类生成"""
        dev = Developer()

        result = dev.generate_class(
            name="UserService",
            description="用户服务类",
            init_params="self, db",
            init_body="self.db = db",
        )

        assert result.success is True
        assert "class UserService" in result.code
        assert "def __init__" in result.code

    def test_generate_test(self):
        """测试用例生成"""
        dev = Developer()

        result = dev.generate_test(
            test_name="user_login",
            description="测试用户登录",
            arrange="user = User()",
            act="result = user.login()",
            assertion="result is True",
        )

        assert result.success is True
        assert "def test_user_login" in result.code

    def test_add_code_constraint(self):
        """测试添加代码约束"""
        dev = Developer()

        dev.add_code_constraint(
            name="no_eval",
            pattern=r"eval\s*\(",
            message="禁止使用 eval()",
            severity="error",
        )

        stats = dev.get_code_generator_stats()
        assert stats["constraints_count"] >= 1


class TestDeveloperPMCallback:
    """测试PM回调机制"""

    def test_set_pm_callback(self):
        """测试设置PM回调"""
        dev = Developer()

        callback_calls = []

        def callback(role_type, artifact):
            callback_calls.append({"role_type": role_type, "artifact": artifact})

        dev.set_pm_callback(callback)
        assert dev._pm_callback is not None

    def test_report_to_pm(self):
        """测试向PM汇报"""
        dev = Developer()

        callback_calls = []

        def callback(role_type, artifact):
            callback_calls.append({"role_type": role_type, "artifact": artifact})

        dev.set_pm_callback(callback)
        dev.set_context_from_pm({
            "project": {"name": "项目", "tech_stack": "Python"},
            "current_task": {"description": "任务"},
        })
        dev._current_task = {"inputs": {}}

        # 通过 _execute_by_type 执行，这样会自动汇报
        dev._execute_by_type(TaskType.IMPLEMENT_FEATURE)

        assert len(callback_calls) == 1
        assert callback_calls[0]["role_type"] == "developer"

    def test_report_progress_manual(self):
        """测试手动汇报进度"""
        dev = Developer()

        callback_calls = []

        def callback(role_type, artifact):
            callback_calls.append({"role_type": role_type, "artifact": artifact})

        dev.set_pm_callback(callback)

        result = dev.report_progress({"status": "in_progress", "progress": 50})

        assert result is True
        assert len(callback_calls) == 1

    def test_report_without_callback(self):
        """测试无回调时汇报"""
        dev = Developer()

        result = dev.report_progress({"status": "in_progress"})
        assert result is False


class TestDeveloperRolePrompt:
    """测试角色提示词"""

    def test_build_role_prompt(self):
        """测试构建角色提示词"""
        dev = Developer()

        prompt = dev.build_role_prompt()

        assert "你的职责是**实现**，不是**决策**" in prompt
        # 验证关键内容存在
        assert "ADR" in prompt or "架构师" in prompt
        # 验证包含关键提示
        assert "实现" in prompt and "决策" in prompt

    def test_prompt_contains_boundary(self):
        """测试提示词包含边界定义"""
        dev = Developer()

        prompt = dev.build_role_prompt()

        assert "ADR" in prompt
        assert "API契约" in prompt or "API" in prompt
        assert "架构师" in prompt


class TestDeveloperIntegration:
    """集成测试"""

    def test_full_workflow(self):
        """测试完整工作流"""
        # 1. 创建开发者
        dev = Developer()

        # 2. 设置PM回调（使用关键字参数）
        artifacts = []
        def callback(role_type, artifact):
            artifacts.append(artifact)
        dev.set_pm_callback(callback)

        # 3. 设置上下文
        dev.set_context_from_pm({
            "project": {"name": "电商平台", "tech_stack": "Python + FastAPI"},
            "current_task": {"description": "实现购物车功能"},
            "requirements_summary": "用户购物车需求",
            "design_summary": "使用Redis存储购物车数据",
        })

        # 4. 执行实现
        dev._current_task = {"inputs": {}}
        result = dev._execute_by_type(TaskType.IMPLEMENT_FEATURE)

        # 5. 验证结果
        assert result["status"] == "completed"
        assert len(artifacts) == 1

        # 6. 验证上下文使用
        assert result["context_used"]["project_name"] == "电商平台"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])