"""
Tests for Tester Role - 测试人员角色测试

测试测试人员的核心功能：
- 测试用例设计
- 测试执行
- Bug报告
- 覆盖率分析
"""

import pytest

from harnessgenj.roles.tester import (
    Tester,
    create_tester,
)
from harnessgenj.roles.base import RoleContext, RoleType, TaskType, SkillCategory


class TestTesterCreation:
    """测试测试人员创建"""

    def test_create_default(self):
        """使用默认参数创建"""
        tester = Tester(role_id="tester_1", name="测试人员")
        assert tester is not None
        assert tester.role_id == "tester_1"
        assert tester.name == "测试人员"
        assert tester.role_type == RoleType.TESTER

    def test_create_with_custom_params(self):
        """使用自定义参数创建"""
        tester = Tester(
            role_id="tester_custom",
            name="高级测试工程师",
        )
        assert tester.role_id == "tester_custom"
        assert tester.name == "高级测试工程师"

    def test_create_with_context(self):
        """使用上下文创建"""
        context = RoleContext()
        tester = Tester(role_id="tester_ctx", name="测试员", context=context)
        assert tester.context is not None

    def test_create_with_factory(self):
        """使用工厂函数创建"""
        tester = create_tester(tester_id="tester_factory", name="工厂测试员")
        assert tester.role_id == "tester_factory"
        assert tester.name == "工厂测试员"


class TestTesterResponsibilities:
    """测试测试人员职责"""

    def test_responsibilities_list(self):
        """测试职责列表"""
        tester = Tester(role_id="tester_1", name="测试人员")
        responsibilities = tester.responsibilities

        assert len(responsibilities) == 5
        assert "测试用例设计（产出测试用例）" in responsibilities
        assert "测试执行（产出测试报告）" in responsibilities
        assert "Bug发现与报告（产出Bug报告）" in responsibilities

    def test_forbidden_actions(self):
        """测试禁止行为"""
        tester = Tester(role_id="tester_1", name="测试人员")
        forbidden = tester.forbidden_actions

        assert len(forbidden) == 4
        assert "修改生产代码" in forbidden
        assert "修改需求文档" in forbidden
        assert "修改架构文档" in forbidden

    def test_decision_authority(self):
        """测试决策权限"""
        tester = Tester(role_id="tester_1", name="测试人员")
        authority = tester.decision_authority

        assert len(authority) == 3
        assert "测试用例设计" in authority
        assert "测试范围确定" in authority

    def test_no_decision_authority(self):
        """测试无决策权限"""
        tester = Tester(role_id="tester_1", name="测试人员")
        no_authority = tester.no_decision_authority

        assert len(no_authority) == 3
        assert "功能实现方式" in no_authority
        assert "需求变更" in no_authority


class TestTesterSkills:
    """测试测试人员技能"""

    def test_skills_setup(self):
        """测试技能设置"""
        tester = Tester(role_id="tester_1", name="测试人员")
        skills = tester.list_skills()

        assert len(skills) == 5

        skill_names = [s.name for s in skills]
        assert "write_test" in skill_names
        assert "run_test" in skill_names
        assert "report_bug" in skill_names
        assert "analyze_coverage" in skill_names
        assert "performance_test" in skill_names


class TestTesterTaskExecution:
    """测试任务执行"""

    def test_supported_task_types(self):
        """测试支持的任务类型"""
        tester = Tester(role_id="tester_1", name="测试人员")
        task_types = tester.get_supported_task_types()

        assert TaskType.WRITE_TEST in task_types
        assert TaskType.RUN_TEST in task_types
        assert TaskType.BUG_REPORT in task_types

    def test_write_test(self):
        """测试编写测试用例"""
        tester = Tester(role_id="tester_1", name="测试人员")
        tester._current_task = {
            "inputs": {
                "requirement": "用户登录功能",
            }
        }

        result = tester._write_test()

        assert result["status"] == "completed"
        assert "test_cases" in result["outputs"]

    def test_run_test(self):
        """测试执行测试"""
        tester = Tester(role_id="tester_1", name="测试人员")
        tester._current_task = {
            "inputs": {
                "test_cases": ["test_login"],
            }
        }

        result = tester._run_test()

        assert result["status"] == "completed"
        assert "test_results" in result["outputs"]

    def test_report_bug(self):
        """测试报告Bug"""
        tester = Tester(role_id="tester_1", name="测试人员")
        tester._current_task = {
            "inputs": {
                "test_failure": "登录失败",
            }
        }

        result = tester._report_bug()

        assert result["status"] == "completed"
        assert "bug_report" in result["outputs"]

    def test_execute_by_type_write_test(self):
        """测试按类型执行 - 编写测试"""
        tester = Tester(role_id="tester_1", name="测试人员")
        tester._current_task = {"inputs": {"requirement": "测试功能"}}

        result = tester._execute_by_type(TaskType.WRITE_TEST)

        assert result["status"] == "completed"

    def test_execute_by_type_unsupported(self):
        """测试不支持的任务类型"""
        tester = Tester(role_id="tester_1", name="测试人员")
        tester._current_task = {"inputs": {}}

        # IMPLEMENT_FEATURE 不在 Tester 支持的任务类型中
        result = tester._execute_by_type(TaskType.IMPLEMENT_FEATURE)

        assert result["status"] == "error"
        assert "Unsupported task" in result["message"]


class TestTesterPrompts:
    """测试角色提示词"""

    def test_build_role_prompt(self):
        """测试构建角色提示词"""
        tester = Tester(role_id="tester_1", name="测试人员")

        prompt = tester.build_role_prompt()

        assert "你的职责是**验证**" in prompt
        assert "不要修改生产代码" in prompt

    def test_prompt_contains_philosophy(self):
        """测试提示词包含哲学定位"""
        tester = Tester(role_id="tester_1", name="测试人员")

        prompt = tester.build_role_prompt()

        assert "验证" in prompt
        assert "实现" in prompt


class TestTesterIntegration:
    """集成测试"""

    def test_full_test_workflow(self):
        """测试完整测试工作流"""
        # 1. 创建测试人员
        tester = Tester(role_id="tester_1", name="测试人员")

        # 2. 设置测试目标
        tester._current_task = {
            "inputs": {
                "requirement": "购物车功能",
            }
        }

        # 3. 编写测试用例
        result = tester._write_test()

        # 4. 验证结果
        assert result["status"] == "completed"
        assert "test_cases" in result["outputs"]

    def test_test_case_structure(self):
        """测试测试用例结构"""
        tester = Tester(role_id="tester_1", name="测试人员")
        tester._current_task = {
            "inputs": {
                "requirement": "登录功能",
            }
        }

        result = tester._write_test()
        test_cases = result["outputs"]["test_cases"]

        # 验证测试用例包含必要字段
        assert len(test_cases) > 0
        case = test_cases[0]
        assert "name" in case


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])