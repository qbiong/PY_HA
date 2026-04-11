"""
Test Score System - 积分系统测试

测试方案D积分系统优化：
- 分层扣分梯度
- 角色淘汰机制
- 恢复机制
- PM问责机制
"""

import pytest
import time
import tempfile
import os
from pathlib import Path

from harnessgenj.quality.score import (
    ScoreManager,
    ScoreRules,
    RoleScore,
    ScoreEvent,
)


class TestScoreRules:
    """测试积分规则常量"""

    def test_termination_threshold(self):
        """测试淘汰阈值"""
        assert ScoreRules.TERMINATION_THRESHOLD == 30
        assert ScoreRules.WARNING_THRESHOLD == 50
        assert ScoreRules.INITIAL_SCORE == 100

    def test_generator_rewards(self):
        """测试生成器奖励"""
        assert ScoreRules.ONE_ROUND_PASS == 15
        assert ScoreRules.TWO_ROUND_PASS == 10
        assert ScoreRules.THREE_ROUND_PASS == 5
        assert ScoreRules.FOUR_PLUS_ROUND == 2

    def test_generator_deductions(self):
        """测试生成器扣分梯度"""
        assert ScoreRules.ISSUE_MINOR == -4
        assert ScoreRules.ISSUE_MEDIUM == -8
        assert ScoreRules.ISSUE_MAJOR == -15
        assert ScoreRules.SECURITY_VULNERABILITY == -25
        assert ScoreRules.PRODUCTION_BUG == -40

    def test_discriminator_rewards(self):
        """测试判别器奖励"""
        assert ScoreRules.FIND_MINOR == 5
        assert ScoreRules.FIND_MEDIUM == 10
        assert ScoreRules.FIND_MAJOR == 18
        assert ScoreRules.FIND_SECURITY == 30
        assert ScoreRules.PREVENT_PRODUCTION == 45

    def test_recovery_rules(self):
        """测试恢复机制规则"""
        assert ScoreRules.CONSECUTIVE_CLEAN_3 == 5
        assert ScoreRules.CONSECUTIVE_CLEAN_5 == 8
        assert ScoreRules.WEEK_NO_DEDUCTION == 10
        assert ScoreRules.REPEAT_ERROR_MULTIPLIER == 1.5

    def test_pm_accountability(self):
        """测试PM问责规则"""
        assert ScoreRules.PM_SINGLE_REPLACEMENT_PENALTY == -10
        assert ScoreRules.PM_TEAM_REPLACEMENT_PENALTY == -30


class TestRoleScore:
    """测试角色积分状态"""

    def test_role_score_creation(self):
        """测试角色积分创建"""
        role_score = RoleScore(
            role_type="developer",
            role_id="dev_1",
            role_name="Developer",
        )
        assert role_score.score == 100
        assert role_score.consecutive_clean_tasks == 0
        assert role_score.is_terminated == False
        assert role_score.replacement_count == 0

    def test_role_score_grade(self):
        """测试等级评定"""
        role_score = RoleScore(role_type="developer", role_id="dev_1")

        role_score.score = 95
        assert role_score.grade == "A"

        role_score.score = 75
        assert role_score.grade == "B"

        role_score.score = 55
        assert role_score.grade == "C"

        role_score.score = 25
        assert role_score.grade == "D"


class TestScoreManager:
    """测试积分管理器"""

    @pytest.fixture
    def score_manager(self, tmp_path):
        """创建积分管理器"""
        workspace = str(tmp_path / ".harnessgenj")
        os.makedirs(workspace, exist_ok=True)
        return ScoreManager(workspace)

    def test_register_role(self, score_manager):
        """测试注册角色"""
        role_score = score_manager.register_role("developer", "dev_1", "Developer")

        assert role_score.role_id == "dev_1"
        assert role_score.role_type == "developer"
        assert role_score.score == 100

    def test_check_termination_normal(self, score_manager):
        """测试正常状态不触发淘汰"""
        score_manager.register_role("developer", "dev_1", "Developer")
        score_manager._scores["dev_1"].score = 80

        result = score_manager.check_termination("dev_1")

        assert result["should_terminate"] == False
        assert result["should_warn"] == False
        assert result["threshold"] == "normal"

    def test_check_termination_warning(self, score_manager):
        """测试警告状态"""
        score_manager.register_role("developer", "dev_1", "Developer")
        score_manager._scores["dev_1"].score = 40

        result = score_manager.check_termination("dev_1")

        assert result["should_terminate"] == False
        assert result["should_warn"] == True
        assert result["threshold"] == "warning"

    def test_check_termination_terminate(self, score_manager):
        """测试淘汰状态"""
        score_manager.register_role("developer", "dev_1", "Developer")
        score_manager._scores["dev_1"].score = 25

        result = score_manager.check_termination("dev_1")

        assert result["should_terminate"] == True
        assert result["should_warn"] == True
        assert result["threshold"] == "termination"

    def test_terminate_role(self, score_manager):
        """测试终止角色"""
        score_manager.register_role("developer", "dev_1", "Developer")

        result = score_manager.terminate_role("dev_1", "积分低于淘汰阈值")

        assert result["success"] == True
        assert result["new_role_id_suggestion"] == "developer_1"
        assert score_manager._scores["dev_1"].is_terminated == True

    def test_create_replacement_role(self, score_manager):
        """测试创建替换角色"""
        score_manager.register_role("developer", "dev_1", "Developer")
        score_manager.terminate_role("dev_1", "积分低于淘汰阈值")

        new_role = score_manager.create_replacement_role(
            "dev_1", "dev_2", "developer", "Developer v2"
        )

        assert new_role.role_id == "dev_2"
        assert new_role.replacement_count == 1
        assert new_role.score == 100

    def test_increment_clean_task(self, score_manager):
        """测试增加连续无问题任务计数"""
        score_manager.register_role("developer", "dev_1", "Developer")

        count = score_manager.increment_clean_task("dev_1")
        assert count == 1

        count = score_manager.increment_clean_task("dev_1")
        assert count == 2

    def test_reset_clean_task(self, score_manager):
        """测试重置连续无问题任务计数"""
        score_manager.register_role("developer", "dev_1", "Developer")
        score_manager.increment_clean_task("dev_1")
        score_manager.increment_clean_task("dev_1")

        score_manager.reset_clean_task("dev_1")

        assert score_manager._scores["dev_1"].consecutive_clean_tasks == 0
        assert score_manager._scores["dev_1"].last_deduction_time is not None

    def test_record_error_type(self, score_manager):
        """测试记录错误类型"""
        score_manager.register_role("developer", "dev_1", "Developer")

        # 第一次记录
        result1 = score_manager.record_error_type("dev_1", "naming")
        assert result1["count"] == 1
        assert result1["is_repeat"] == False

        # 第二次记录（重复）
        result2 = score_manager.record_error_type("dev_1", "naming")
        assert result2["count"] == 2
        assert result2["is_repeat"] == True
        assert result2["multiplier"] == 1.5


class TestRecoveryMechanism:
    """测试恢复机制"""

    @pytest.fixture
    def score_manager(self, tmp_path):
        """创建积分管理器"""
        workspace = str(tmp_path / ".harnessgenj")
        os.makedirs(workspace, exist_ok=True)
        return ScoreManager(workspace)

    def test_consecutive_clean_recovery_3(self, score_manager):
        """测试连续3次无问题恢复"""
        score_manager.register_role("developer", "dev_1", "Developer")
        score_manager._scores["dev_1"].score = 70

        # 连续3次无问题
        for _ in range(3):
            score_manager.increment_clean_task("dev_1")

        recovery = score_manager.apply_recovery_bonus("dev_1")

        assert recovery >= 5

    def test_consecutive_clean_recovery_5(self, score_manager):
        """测试连续5次无问题额外恢复"""
        score_manager.register_role("developer", "dev_1", "Developer")
        score_manager._scores["dev_1"].score = 60

        # 连续5次无问题
        for _ in range(5):
            score_manager.increment_clean_task("dev_1")

        recovery = score_manager.apply_recovery_bonus("dev_1")

        assert recovery >= 13  # 5 + 8


class TestEnhancedMethods:
    """测试增强版方法"""

    @pytest.fixture
    def score_manager(self, tmp_path):
        """创建积分管理器"""
        workspace = str(tmp_path / ".harnessgenj")
        os.makedirs(workspace, exist_ok=True)
        return ScoreManager(workspace)

    def test_on_task_success_enhanced(self, score_manager):
        """测试增强版任务成功事件"""
        score_manager.register_role("developer", "dev_1", "Developer")

        result = score_manager.on_task_success_enhanced("dev_1", 1)

        assert result["base_delta"] == 15
        assert result["clean_count"] == 1

    def test_on_issue_found_enhanced(self, score_manager):
        """测试增强版发现问题事件"""
        score_manager.register_role("developer", "dev_1", "Developer")
        score_manager.register_role("code_reviewer", "reviewer_1", "Reviewer")

        result = score_manager.on_issue_found_enhanced(
            "dev_1", "reviewer_1", "major", "logic_error"
        )

        assert result["gen_delta"] == -15
        assert result["disc_delta"] == 18
        assert result["error_info"]["count"] == 1

    def test_on_issue_found_repeat_error(self, score_manager):
        """测试重复错误翻倍"""
        score_manager.register_role("developer", "dev_1", "Developer")
        score_manager.register_role("code_reviewer", "reviewer_1", "Reviewer")

        # 第一次错误
        result1 = score_manager.on_issue_found_enhanced(
            "dev_1", "reviewer_1", "major", "logic_error"
        )

        # 第二次同类错误（翻倍）
        result2 = score_manager.on_issue_found_enhanced(
            "dev_1", "reviewer_1", "major", "logic_error"
        )

        assert result2["error_info"]["is_repeat"] == True


class TestPMAccountability:
    """测试PM问责机制"""

    @pytest.fixture
    def score_manager(self, tmp_path):
        """创建积分管理器"""
        workspace = str(tmp_path / ".harnessgenj")
        os.makedirs(workspace, exist_ok=True)
        return ScoreManager(workspace)

    def test_check_pm_accountability_no_violation(self, score_manager):
        """测试PM问责无违规"""
        score_manager.register_role("project_manager", "pm_1", "PM")

        result = score_manager.check_pm_accountability("pm_1")

        assert result["total_penalty"] == 0
        assert result["pm_should_terminate"] == False

    def test_check_pm_accountability_with_replacements(self, score_manager):
        """测试PM问责有替换"""
        score_manager.register_role("project_manager", "pm_1", "PM")
        score_manager.register_role("developer", "dev_1", "Developer")

        # 模拟角色替换事件（需要3次替换才会触发PM问责）
        for i in range(3):
            score_manager.terminate_role(f"dev_{i+1}" if i > 0 else "dev_1", "积分低于淘汰阈值")
            score_manager.create_replacement_role(
                f"dev_{i+1}" if i > 0 else "dev_1",
                f"dev_{i+2}",
                "developer",
                f"Developer v{i+2}"
            )

        result = score_manager.check_pm_accountability("pm_1")

        # 单角色类型替换次数 >= 3 次 > 2次/月
        assert result["total_replacements"] >= 3
        # 检查是否有处罚（developer类型替换了3次）
        assert "developer" in result["type_replacements"]
        assert result["type_replacements"]["developer"] >= 3

    def test_get_team_replacement_stats(self, score_manager):
        """测试获取团队替换统计"""
        score_manager.register_role("developer", "dev_1", "Developer")

        # 模拟替换
        score_manager.terminate_role("dev_1", "积分低于淘汰阈值")
        score_manager.create_replacement_role("dev_1", "dev_2", "developer", "Developer v2")

        stats = score_manager.get_team_replacement_stats()

        assert stats["total_replacements"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])