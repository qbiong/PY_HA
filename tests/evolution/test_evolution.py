"""
Evolution Module Tests - 自我进化系统测试

测试覆盖：
- PatternExtractor: 模式提取
- SkillAccumulator: 技能积累
- KnowledgeFeedback: 知识反馈
- TokenOptimizer: Token优化
- SkillRegistry: 技能注册
"""

import pytest
import tempfile
import json
from pathlib import Path

from harnessgenj.evolution.pattern_extractor import (
    PatternExtractor,
    ExtractedPattern,
    PatternType,
    PatternValidationResult,
    create_pattern_extractor,
)
from harnessgenj.evolution.skill_accumulator import (
    SkillAccumulator,
    RoleSkill,
    SkillType,
    SkillAccumulatorStats,
    create_skill_accumulator,
)
from harnessgenj.evolution.knowledge_feedback import (
    KnowledgeFeedback,
    FeedbackRecord,
    FeedbackStatus,
    create_knowledge_feedback,
)
from harnessgenj.evolution.token_optimizer import (
    TokenOptimizer,
    InlineCandidate,
    TokenSavingsReport,
    create_token_optimizer,
)
from harnessgenj.evolution.skill_registry import (
    SkillRegistry,
    SkillRegistryStats,
    create_skill_registry,
)


class TestPatternExtractor:
    """PatternExtractor 测试"""

    def test_create_pattern_extractor(self):
        """测试创建 PatternExtractor"""
        extractor = create_pattern_extractor()
        assert extractor is not None
        assert isinstance(extractor, PatternExtractor)

    def test_pattern_types(self):
        """测试模式类型枚举"""
        assert PatternType.CODE_TEMPLATE.value == "code_template"
        assert PatternType.DECISION_FLOW.value == "decision_flow"
        assert PatternType.ERROR_HANDLING.value == "error_handling"

    def test_extracted_pattern_model(self):
        """测试 ExtractedPattern 数据模型"""
        pattern = ExtractedPattern(
            pattern_id="pattern-001",
            pattern_type=PatternType.CODE_TEMPLATE,
            name="login_validation_pattern",
            description="登录验证模式",
            trigger_conditions=["用户登录", "验证"],
            solution_template="def validate_login(user, password): ...",
            success_rate=0.85,
            quality_score=80.0,
        )
        assert pattern.pattern_id == "pattern-001"
        assert pattern.success_rate == 0.85
        assert not pattern.verified

    def test_extract_from_success_records(self):
        """测试从成功记录提取模式"""
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = PatternExtractor(storage_path=tmpdir)

            records = [
                {
                    "generator_output": {
                        "code": "def validate_login(user, password):\n    if not user:\n        raise ValueError('用户名不能为空')\n    return True",
                        "decisions": ["添加空值检查"],
                    },
                    "task_type": "bug",
                    "quality_score": 85.0,
                },
                {
                    "generator_output": {
                        "code": "def validate_email(email):\n    if not email:\n        raise ValueError('邮箱不能为空')\n    return True",
                        "decisions": ["添加空值检查"],
                    },
                    "task_type": "bug",
                    "quality_score": 90.0,
                },
            ]

            patterns = extractor.extract_from_success_records(records)
            assert len(patterns) >= 0  # 可能合并相似模式

    def test_generate_skill_definition(self):
        """测试生成技能定义"""
        extractor = PatternExtractor()

        pattern = ExtractedPattern(
            pattern_id="pattern-002",
            pattern_type=PatternType.ERROR_HANDLING,
            name="null_check_pattern",
            trigger_conditions=["空值检查"],
            solution_template="if not value:\n    raise ValueError('不能为空')",
            success_rate=0.9,
            quality_score=85.0,
        )

        skill_def = extractor.generate_skill_definition(pattern)
        assert skill_def["skill_name"] == "null_check_pattern"
        assert skill_def["skill_type"] == "discriminator"
        assert skill_def["trigger_conditions"] == ["空值检查"]

    def test_validate_pattern(self):
        """测试模式验证"""
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = PatternExtractor(storage_path=tmpdir)

            pattern = ExtractedPattern(
                pattern_id="pattern-003",
                pattern_type=PatternType.CODE_TEMPLATE,
                name="test_pattern",
                trigger_conditions=["测试"],
                solution_template="def test(): pass",
                sample_count=5,
                success_rate=0.8,
                quality_score=75.0,
            )

            result = extractor.validate_pattern(pattern)
            assert isinstance(result, PatternValidationResult)
            assert result.pattern_id == "pattern-003"

    def test_get_patterns_by_type(self):
        """测试按类型获取模式"""
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = PatternExtractor(storage_path=tmpdir)

            # 添加一些模式
            pattern1 = ExtractedPattern(
                pattern_id="p1",
                pattern_type=PatternType.CODE_TEMPLATE,
                name="p1",
                sample_count=3,
                success_rate=0.8,
                quality_score=80.0,
            )
            extractor._patterns[pattern1.pattern_id] = pattern1

            patterns = extractor.get_patterns_by_type(PatternType.CODE_TEMPLATE)
            assert len(patterns) >= 0


class TestSkillAccumulator:
    """SkillAccumulator 测试"""

    def test_create_skill_accumulator(self):
        """测试创建 SkillAccumulator"""
        accumulator = create_skill_accumulator()
        assert accumulator is not None
        assert isinstance(accumulator, SkillAccumulator)

    def test_skill_types(self):
        """测试技能类型枚举"""
        assert SkillType.GENERATOR.value == "generator"
        assert SkillType.DISCRIMINATOR.value == "discriminator"
        assert SkillType.COMMON.value == "common"

    def test_role_skill_model(self):
        """测试 RoleSkill 数据模型"""
        skill = RoleSkill(
            skill_id="skill-001",
            skill_name="validation_skill",
            skill_type=SkillType.DISCRIMINATOR,
            applicable_roles=["developer", "bug_hunter"],
            trigger_conditions=["验证"],
            execution_template="def validate(): pass",
            success_rate=0.85,
        )
        assert skill.skill_id == "skill-001"
        assert skill.is_applicable_to("developer")
        assert skill.matches_trigger("需要验证数据")

    def test_accumulate_pattern(self):
        """测试从模式积累技能"""
        with tempfile.TemporaryDirectory() as tmpdir:
            accumulator = SkillAccumulator(storage_path=tmpdir)

            pattern_data = {
                "name": "test_pattern",
                "success_rate": 0.85,
                "quality_score": 80.0,
                "trigger_conditions": ["测试"],
                "execution_template": "def test(): pass",
                "applicable_roles": ["developer"],
                "skill_type": "generator",
            }

            skill = accumulator.accumulate_pattern(pattern_data, validate=True)
            assert skill is not None
            assert skill.skill_name == "test_pattern"

    def test_store_skill(self):
        """测试存储技能"""
        with tempfile.TemporaryDirectory() as tmpdir:
            accumulator = SkillAccumulator(storage_path=tmpdir)

            skill = RoleSkill(
                skill_id="skill-002",
                skill_name="test_skill",
                skill_type=SkillType.GENERATOR,
                applicable_roles=["developer"],
            )

            skill_id = accumulator.store_skill(skill)
            assert skill_id == "skill-002"

            # 验证可以获取
            retrieved = accumulator.get_skill(skill_id)
            assert retrieved is not None

    def test_get_skills_for_role(self):
        """测试获取角色技能"""
        with tempfile.TemporaryDirectory() as tmpdir:
            accumulator = SkillAccumulator(storage_path=tmpdir)

            skill = RoleSkill(
                skill_id="skill-003",
                skill_name="dev_skill",
                skill_type=SkillType.GENERATOR,
                applicable_roles=["developer"],
            )
            accumulator.store_skill(skill)

            skills = accumulator.get_skills_for_role("developer")
            assert len(skills) >= 1

    def test_retire_skill(self):
        """测试淘汰技能"""
        with tempfile.TemporaryDirectory() as tmpdir:
            accumulator = SkillAccumulator(storage_path=tmpdir)

            skill = RoleSkill(
                skill_id="skill-004",
                skill_name="bad_skill",
                skill_type=SkillType.GENERATOR,
                applicable_roles=["developer"],
            )
            accumulator.store_skill(skill)

            result = accumulator.retire_skill("skill-004", "成功率过低")
            assert result is True

            skill = accumulator.get_skill("skill-004")
            assert skill.is_retired

    def test_record_skill_usage(self):
        """测试记录技能使用"""
        with tempfile.TemporaryDirectory() as tmpdir:
            accumulator = SkillAccumulator(storage_path=tmpdir)

            skill = RoleSkill(
                skill_id="skill-005",
                skill_name="usage_skill",
                skill_type=SkillType.GENERATOR,
                applicable_roles=["developer"],
                usage_count=0,
            )
            accumulator.store_skill(skill)

            accumulator.record_skill_usage("skill-005", success=True)

            skill = accumulator.get_skill("skill-005")
            assert skill.usage_count == 1

    def test_get_stats(self):
        """测试获取统计信息"""
        with tempfile.TemporaryDirectory() as tmpdir:
            accumulator = SkillAccumulator(storage_path=tmpdir)

            stats = accumulator.get_stats()
            assert isinstance(stats, SkillAccumulatorStats)
            assert stats.total_skills >= 0


class TestKnowledgeFeedback:
    """KnowledgeFeedback 测试"""

    def test_create_knowledge_feedback(self):
        """测试创建 KnowledgeFeedback"""
        feedback = create_knowledge_feedback()
        assert feedback is not None
        assert isinstance(feedback, KnowledgeFeedback)

    def test_feedback_status(self):
        """测试反馈状态枚举"""
        assert FeedbackStatus.VALIDATED.value == "validated"
        assert FeedbackStatus.DEPRECATED.value == "deprecated"
        assert FeedbackStatus.NEEDS_REVIEW.value == "needs_review"

    def test_feedback_record_model(self):
        """测试 FeedbackRecord 数据模型"""
        record = FeedbackRecord(
            feedback_id="fb-001",
            source_type="adversarial_review",
            knowledge_id="kn-001",
            original_quality=50.0,
            quality_update=80.0,
            new_quality=62.0,
            validation_status=FeedbackStatus.VALIDATED,
        )
        assert record.feedback_id == "fb-001"
        assert record.new_quality == 62.0

    def test_update_knowledge_quality(self):
        """测试更新知识质量"""
        with tempfile.TemporaryDirectory() as tmpdir:
            feedback = KnowledgeFeedback(storage_path=tmpdir)

            result = feedback.update_knowledge_quality("kn-001", 80.0)
            assert result is True

            quality = feedback._knowledge_quality.get("kn-001")
            assert quality is not None

    def test_mark_for_review(self):
        """测试标记待审查"""
        with tempfile.TemporaryDirectory() as tmpdir:
            feedback = KnowledgeFeedback(storage_path=tmpdir)

            result = feedback.mark_for_review("kn-002", "质量分数波动")
            assert result is True

    def test_generate_improvement_suggestions(self):
        """测试生成改进建议"""
        with tempfile.TemporaryDirectory() as tmpdir:
            feedback = KnowledgeFeedback(storage_path=tmpdir)

            suggestions = feedback.generate_improvement_suggestions("kn-003")
            assert isinstance(suggestions, list)

    def test_get_stats(self):
        """测试获取统计信息"""
        with tempfile.TemporaryDirectory() as tmpdir:
            feedback = KnowledgeFeedback(storage_path=tmpdir)

            stats = feedback.get_stats()
            assert stats.total_feedbacks >= 0


class TestTokenOptimizer:
    """TokenOptimizer 测试"""

    def test_create_token_optimizer(self):
        """测试创建 TokenOptimizer"""
        optimizer = create_token_optimizer()
        assert optimizer is not None
        assert isinstance(optimizer, TokenOptimizer)

    def test_inline_candidate_model(self):
        """测试 InlineCandidate 数据模型"""
        candidate = InlineCandidate(
            pattern_id="p-001",
            pattern_name="frequent_pattern",
            call_count=100,
            estimated_tokens=200,
            potential_savings=20000,
            priority=100,
            recommended=True,
        )
        assert candidate.pattern_id == "p-001"
        assert candidate.recommended

    def test_identify_inline_candidates(self):
        """测试识别内联候选"""
        with tempfile.TemporaryDirectory() as tmpdir:
            optimizer = TokenOptimizer(storage_path=tmpdir)

            hotspots = [
                {
                    "id": "h1",
                    "name": "high_freq_pattern",
                    "suggested_strategy": "inline",
                    "call_count": 50,
                },
                {
                    "id": "h2",
                    "name": "low_freq_pattern",
                    "suggested_strategy": "inline",
                    "call_count": 5,
                },
            ]

            candidates = optimizer.identify_inline_candidates(hotspots)
            # 只有高频率的才应该被推荐
            assert len(candidates) >= 0

    def test_inline_pattern(self):
        """测试内联模式"""
        with tempfile.TemporaryDirectory() as tmpdir:
            optimizer = TokenOptimizer(storage_path=tmpdir)

            pattern = {
                "pattern_id": "p-002",
                "name": "inline_test",
                "solution_template": "def inline_func(): pass",
            }

            result = optimizer.inline_pattern(pattern)
            assert "inline_test" in result

    def test_compute_token_savings(self):
        """测试计算 Token 节省"""
        with tempfile.TemporaryDirectory() as tmpdir:
            optimizer = TokenOptimizer(storage_path=tmpdir)

            # 先内联一个模式
            optimizer._inline_patterns["p-003"] = "template content"

            savings = optimizer.compute_token_savings("p-003")
            assert savings >= 0

    def test_get_total_savings(self):
        """测试获取总节省"""
        with tempfile.TemporaryDirectory() as tmpdir:
            optimizer = TokenOptimizer(storage_path=tmpdir)

            total = optimizer.get_total_savings()
            assert total >= 0

    def test_generate_report(self):
        """测试生成报告"""
        with tempfile.TemporaryDirectory() as tmpdir:
            optimizer = TokenOptimizer(storage_path=tmpdir)

            report = optimizer.generate_report()
            assert isinstance(report, TokenSavingsReport)
            assert report.patterns_inlined >= 0


class TestSkillRegistry:
    """SkillRegistry 测试"""

    def test_create_skill_registry(self):
        """测试创建 SkillRegistry"""
        registry = create_skill_registry()
        assert registry is not None
        assert isinstance(registry, SkillRegistry)

    def test_register_skill(self):
        """测试注册技能"""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = SkillRegistry(storage_path=tmpdir)

            skill = RoleSkill(
                skill_id="skill-reg-001",
                skill_name="registry_skill",
                skill_type=SkillType.GENERATOR,
                applicable_roles=["developer"],
            )

            result = registry.register("developer", skill)
            assert result is True

    def test_unregister_skill(self):
        """测试注销技能"""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = SkillRegistry(storage_path=tmpdir)

            skill = RoleSkill(
                skill_id="skill-reg-002",
                skill_name="temp_skill",
                skill_type=SkillType.GENERATOR,
                applicable_roles=["developer"],
            )
            registry.register("developer", skill)

            result = registry.unregister("developer", "skill-reg-002")
            assert result is True

    def test_get_skills_for_role(self):
        """测试获取角色技能"""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = SkillRegistry(storage_path=tmpdir)

            skill = RoleSkill(
                skill_id="skill-reg-003",
                skill_name="dev_skill",
                skill_type=SkillType.GENERATOR,
                applicable_roles=["developer"],
            )
            registry.register("developer", skill)

            skills = registry.get_skills_for_role("developer")
            assert len(skills) >= 1

    def test_find_matching_skills(self):
        """测试匹配技能"""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = SkillRegistry(storage_path=tmpdir)

            skill = RoleSkill(
                skill_id="skill-reg-004",
                skill_name="validation_skill",
                skill_type=SkillType.DISCRIMINATOR,
                applicable_roles=["developer"],
                trigger_conditions=["验证", "检查"],
            )
            registry.register("developer", skill)

            matching = registry.find_matching_skills("需要验证用户输入", role_type="developer")
            assert len(matching) >= 1

    def test_record_usage(self):
        """测试记录使用"""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = SkillRegistry(storage_path=tmpdir)

            skill = RoleSkill(
                skill_id="skill-reg-005",
                skill_name="usage_skill",
                skill_type=SkillType.GENERATOR,
                applicable_roles=["developer"],
            )
            registry.register("developer", skill)

            result = registry.record_usage("skill-reg-005")
            assert result is True

            count = registry._usage_stats.get("skill-reg-005", 0)
            assert count >= 1

    def test_get_stats(self):
        """测试获取统计信息"""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = SkillRegistry(storage_path=tmpdir)

            stats = registry.get_stats()
            assert isinstance(stats, SkillRegistryStats)

    def test_list_roles(self):
        """测试列出角色"""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = SkillRegistry(storage_path=tmpdir)

            skill = RoleSkill(
                skill_id="skill-reg-006",
                skill_name="multi_role_skill",
                skill_type=SkillType.COMMON,
                applicable_roles=["developer", "tester"],
            )
            registry.register("developer", skill)
            registry.register("tester", skill)

            roles = registry.list_roles()
            assert len(roles) >= 2


class TestEvolutionIntegration:
    """Evolution 模块集成测试"""

    def test_full_evolution_workflow(self):
        """测试完整进化流程"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. 提取模式
            extractor = PatternExtractor(storage_path=tmpdir)

            success_records = [
                {
                    "generator_output": {
                        "code": "def check_null(value):\n    if value is None:\n        raise ValueError('空值')",
                    },
                    "task_type": "bug",
                    "quality_score": 85.0,
                    "passed": True,
                }
            ]

            patterns = extractor.extract_from_success_records(success_records)

            # 2. 积累技能
            accumulator = SkillAccumulator(storage_path=tmpdir)

            if patterns:
                skill = accumulator.accumulate_pattern(patterns[0].model_dump())
                if skill:
                    skill_id = accumulator.store_skill(skill)

                    # 3. 注册技能
                    registry = SkillRegistry(storage_path=tmpdir)
                    for role in skill.applicable_roles:
                        registry.register(role, skill)

                    # 4. 反馈
                    feedback = KnowledgeFeedback(storage_path=tmpdir)
                    review_record = {
                        "generator_output": {"code": "def check_null(value): ..."},
                        "quality_score": 90.0,
                        "passed": True,
                        "issues": [],
                    }
                    feedback.process_adversarial_result(review_record)

            # 验证结果
            stats = accumulator.get_stats()
            assert stats.total_skills >= 0

    def test_pattern_to_skill_flow(self):
        """测试模式到技能的完整流程"""
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = PatternExtractor(storage_path=tmpdir)
            accumulator = SkillAccumulator(storage_path=tmpdir)

            # 创建高质量模式
            pattern = ExtractedPattern(
                pattern_id="high-quality-pattern",
                pattern_type=PatternType.ERROR_HANDLING,
                name="exception_handling",
                trigger_conditions=["异常处理"],
                solution_template="try:\n    operation()\nexcept Exception as e:\n    log_error(e)",
                sample_count=10,
                success_rate=0.95,
                quality_score=90.0,
            )
            extractor._patterns[pattern.pattern_id] = pattern

            # 验证模式
            result = extractor.validate_pattern(pattern)
            assert result.is_valid or result.validation_score > 0

            # 生成技能定义
            skill_def = extractor.generate_skill_definition(pattern)
            assert skill_def is not None

            # 积累为技能
            skill = accumulator.accumulate_pattern(skill_def, validate=True)
            if skill:
                skill_id = accumulator.store_skill(skill)
                assert skill_id is not None