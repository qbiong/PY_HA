"""
Tests for BugHunter Role - 漏洞猎手角色测试

测试漏洞猎手的核心功能：
- 漏洞挖掘
- 边界攻击
- 异常场景构造
- 风险评估
"""

import pytest

from harnessgenj.roles.bug_hunter import (
    BugHunter,
    HuntResult,
    create_bug_hunter,
)
from harnessgenj.roles.base import RoleContext, RoleType, TaskType, SkillCategory
from harnessgenj.quality.record import IssueSeverity


class TestBugHunterCreation:
    """测试漏洞猎手创建"""

    def test_create_default(self):
        """使用默认参数创建"""
        hunter = BugHunter()
        assert hunter is not None
        assert hunter.role_id == "hunter_1"
        assert hunter.name == "漏洞猎手"
        assert hunter.role_type == RoleType.BUG_HUNTER

    def test_create_with_custom_params(self):
        """使用自定义参数创建"""
        hunter = BugHunter(
            role_id="hunter_custom",
            name="安全专家",
        )
        assert hunter.role_id == "hunter_custom"
        assert hunter.name == "安全专家"

    def test_create_with_context(self):
        """使用上下文创建"""
        context = RoleContext()
        hunter = BugHunter(context=context)
        assert hunter.context is not None

    def test_create_with_factory(self):
        """使用工厂函数创建"""
        hunter = create_bug_hunter(hunter_id="hunter_factory", name="工厂猎手")
        assert hunter.role_id == "hunter_factory"
        assert hunter.name == "工厂猎手"


class TestBugHunterResponsibilities:
    """测试漏洞猎手职责"""

    def test_responsibilities_list(self):
        """测试职责列表"""
        hunter = BugHunter()
        responsibilities = hunter.responsibilities

        assert len(responsibilities) == 5
        assert "深度漏洞挖掘（产出漏洞报告）" in responsibilities
        assert "边界条件测试（产出边界测试报告）" in responsibilities

    def test_forbidden_actions(self):
        """测试禁止行为"""
        hunter = BugHunter()
        forbidden = hunter.forbidden_actions

        assert len(forbidden) == 5
        assert "直接修复漏洞" in forbidden
        assert "给出防御代码" in forbidden

    def test_role_type(self):
        """测试角色类型"""
        hunter = BugHunter()
        assert hunter.role_type == RoleType.BUG_HUNTER


class TestBugHunterSkills:
    """测试漏洞猎手技能"""

    def test_skills_setup(self):
        """测试技能设置"""
        hunter = BugHunter()
        skills = hunter.list_skills()

        assert len(skills) == 4

        skill_names = [s.name for s in skills]
        assert "hunt_bugs" in skill_names
        assert "fuzz_test" in skill_names
        assert "security_audit" in skill_names


class TestHuntResult:
    """测试漏洞猎取结果"""

    def test_hunt_result_creation(self):
        """测试结果创建"""
        result = HuntResult(
            risk_score=75.0,
            report="发现2个潜在漏洞",
        )

        assert result.risk_score == 75.0
        assert result.report == "发现2个潜在漏洞"
        assert result.vulnerabilities == []
        assert result.attack_surface == {}

    def test_hunt_result_with_vulnerabilities(self):
        """测试带漏洞的结果"""
        from harnessgenj.quality.record import IssueRecord, IssueSeverity

        vulns = [
            IssueRecord(
                issue_id="VULN-001",
                severity=IssueSeverity.CRITICAL,
                description="SQL注入漏洞",
                location="api.py:123",
                found_by="hunter_1",
            ),
        ]

        result = HuntResult(
            vulnerabilities=vulns,
            risk_score=90.0,
            report="发现高危漏洞",
        )

        assert len(result.vulnerabilities) == 1
        assert result.vulnerabilities[0].severity == IssueSeverity.CRITICAL


class TestBugHunterTaskExecution:
    """测试任务执行"""

    def test_supported_task_types(self):
        """测试支持的任务类型"""
        hunter = BugHunter()
        task_types = hunter.get_supported_task_types()

        # BugHunter 支持 RUN_TEST 和 BUG_REPORT
        assert TaskType.RUN_TEST in task_types
        assert TaskType.BUG_REPORT in task_types

    def test_hunt_method(self):
        """测试漏洞猎取方法"""
        hunter = BugHunter()

        code = '''
def process_input(user_input):
    query = f"SELECT * FROM users WHERE id = {user_input}"
    return db.execute(query)
'''

        result = hunter.hunt(code)

        assert result is not None
        assert isinstance(result, HuntResult)

    def test_execute_by_type_run_test(self):
        """测试按类型执行 - 运行测试（漏洞猎取）"""
        hunter = BugHunter()
        hunter._current_task = {
            "inputs": {
                "code": "def test(): pass"
            }
        }

        result = hunter._execute_by_type(TaskType.RUN_TEST)

        assert result["status"] == "completed"

    def test_execute_by_type_unsupported(self):
        """测试不支持的任务类型"""
        hunter = BugHunter()
        hunter._current_task = {"inputs": {}}

        # IMPLEMENT_FEATURE 不在 BugHunter 支持的任务类型中
        result = hunter._execute_by_type(TaskType.IMPLEMENT_FEATURE)

        assert result["status"] == "error"
        assert "Unsupported task" in result["message"]


class TestBugHunterPrompts:
    """测试角色提示词"""

    def test_build_role_prompt(self):
        """测试构建角色提示词"""
        hunter = BugHunter()

        prompt = hunter.build_role_prompt()

        assert "你的职责是**攻击**" in prompt
        assert "不要直接修复漏洞" in prompt

    def test_prompt_contains_attacker_mindset(self):
        """测试提示词包含攻击者思维"""
        hunter = BugHunter()

        prompt = hunter.build_role_prompt()

        assert "怀疑" in prompt or "攻击" in prompt or "欺骗" in prompt


class TestBugHunterStrategies:
    """测试攻击策略"""

    def test_hunt_strategies_exist(self):
        """测试攻击策略存在"""
        hunter = BugHunter()

        strategies = hunter.HUNT_STRATEGIES

        assert "boundary_attack" in strategies
        assert "fuzzing" in strategies
        assert "edge_case" in strategies

    def test_strategy_priorities(self):
        """测试策略优先级"""
        hunter = BugHunter()

        for name, strategy in hunter.HUNT_STRATEGIES.items():
            assert "priority" in strategy
            assert "name" in strategy
            assert "description" in strategy


class TestBugHunterIntegration:
    """集成测试"""

    def test_full_hunt_workflow(self):
        """测试完整猎取工作流"""
        # 1. 创建漏洞猎手
        hunter = BugHunter()

        # 2. 设置攻击目标
        code = '''
class PaymentService:
    def process_payment(self, amount, card_number):
        # 直接使用用户输入
        if amount > 0:
            return self.charge(card_number, amount)
        return False

    def charge(self, card, amount):
        # 无验证的支付处理
        return True
'''

        # 3. 执行漏洞猎取
        result = hunter.hunt(code)

        # 4. 验证结果
        assert result is not None
        assert isinstance(result, HuntResult)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])