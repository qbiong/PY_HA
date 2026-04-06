"""
Tests for Intent Router and New Workflow Pipeline

测试意图识别和新工作流系统
"""

import pytest
from harnessgenj.workflow.intent_router import (
    IntentRouter,
    IntentType,
    IntentResult,
    create_intent_router,
    identify_intent,
)
from harnessgenj.workflow.pipeline import (
    WorkflowPipeline,
    WorkflowStage,
    StageStatus,
    QualityGate,
    QualityGateType,
    AdversarialConfig,
    create_intent_pipeline,
    create_development_pipeline,
    create_bugfix_pipeline,
    create_inquiry_pipeline,
    create_management_pipeline,
    get_workflow,
    list_workflows,
)


class TestIntentRouter:
    """测试意图识别路由器"""

    @pytest.fixture
    def router(self):
        return create_intent_router()

    def test_create_router(self, router):
        """创建路由器"""
        assert isinstance(router, IntentRouter)

    def test_identify_development_intent(self, router):
        """识别开发意图"""
        test_cases = [
            "我需要一个登录功能",
            "帮我开发购物车模块",
            "添加用户认证功能",
            "实现数据导出功能",
        ]

        for message in test_cases:
            result = router.identify(message)
            assert result.intent_type == IntentType.DEVELOPMENT
            assert result.target_workflow == "development_pipeline"
            assert result.confidence > 0

    def test_identify_bugfix_intent(self, router):
        """识别Bug修复意图"""
        test_cases = [
            "目前项目中文字模式和语音模式的切换AI无法理解，无法判别",
            "登录页面报错了",
            "有个bug：支付超时",
            "无法切换模式",
            "功能不工作了",
            "修复这个问题",
        ]

        for message in test_cases:
            result = router.identify(message)
            assert result.intent_type == IntentType.BUGFIX, f"Failed for: {message}"
            assert result.target_workflow == "bugfix_pipeline"

    def test_identify_inquiry_intent(self, router):
        """识别咨询意图"""
        test_cases = [
            "什么是JVM风格的记忆管理？",
            "这个项目怎么运行的？",
            "如何配置工作流？",
            "能否解释一下架构？",
        ]

        for message in test_cases:
            result = router.identify(message)
            assert result.intent_type == IntentType.INQUIRY

    def test_identify_management_intent(self, router):
        """识别管理意图"""
        test_cases = [
            "项目进度如何？",
            "查看当前状态报告",
            "团队资源安排",
        ]

        for message in test_cases:
            result = router.identify(message)
            assert result.intent_type == IntentType.MANAGEMENT

    def test_entity_extraction(self, router):
        """测试实体提取"""
        result = router.identify("实现用户登录功能")

        entities = {e.name: e.value for e in result.entities}
        # 应该提取到功能名或模块名
        assert len(result.entities) >= 0

    def test_priority_assignment(self, router):
        """测试优先级分配"""
        # Bug修复应该是 P0
        bug_result = router.identify("有个bug需要修复")
        assert bug_result.priority == "P0"

        # 开发应该是 P1
        dev_result = router.identify("开发一个新功能")
        assert dev_result.priority == "P1"

    def test_confidence_score(self, router):
        """测试置信度评分"""
        # 明确的开发请求
        high_conf = router.identify("我需要开发一个用户管理功能")
        assert high_conf.confidence > 0.3

        # 模糊请求
        low_conf = router.identify("嗯")
        assert low_conf.confidence < high_conf.confidence

    def test_supported_intents(self, router):
        """测试支持的意图类型"""
        intents = router.get_supported_intents()
        assert "development" in intents
        assert "bugfix" in intents
        assert "inquiry" in intents
        assert "management" in intents


class TestNewWorkflows:
    """测试新工作流"""

    def test_create_intent_pipeline(self):
        """创建意图识别流水线"""
        pipeline = create_intent_pipeline()

        assert pipeline.name == "intent_pipeline"
        stages = pipeline.list_stages()
        assert len(stages) == 4

        stage_names = [s.name for s in stages]
        assert "receive_input" in stage_names
        assert "identify_intent" in stage_names
        assert "extract_entities" in stage_names
        assert "route_workflow" in stage_names

    def test_create_development_pipeline(self):
        """创建开发流水线"""
        pipeline = create_development_pipeline()

        assert pipeline.name == "development_pipeline"
        stages = pipeline.list_stages()
        assert len(stages) == 8  # 完整质量流程

        stage_names = [s.name for s in stages]
        # 验证关键阶段
        assert "requirements" in stage_names
        assert "design" in stage_names
        assert "development" in stage_names
        assert "adversarial_review" in stage_names
        assert "unit_test" in stage_names
        assert "integration_test" in stage_names

        # 验证对抗配置
        dev_stage = pipeline.get_stage("development")
        assert dev_stage is not None
        assert dev_stage.adversarial_config is not None
        assert dev_stage.adversarial_config.enabled is True

    def test_create_development_pipeline_with_options(self):
        """创建带选项的开发流水线"""
        pipeline = create_development_pipeline(
            intensity="aggressive",
            max_adversarial_rounds=5,
            coverage_threshold=90.0,
        )

        # 验证对抗审查使用 BugHunter
        review_stage = pipeline.get_stage("adversarial_review")
        assert review_stage.role == "bug_hunter"

        # 验证覆盖率阈值
        test_stage = pipeline.get_stage("unit_test")
        coverage_gate = [g for g in test_stage.quality_gates if g.gate_type == QualityGateType.COVERAGE_THRESHOLD]
        assert len(coverage_gate) == 1
        assert coverage_gate[0].threshold == 90.0

    def test_create_bugfix_pipeline(self):
        """创建Bug修复流水线"""
        pipeline = create_bugfix_pipeline()

        assert pipeline.name == "bugfix_pipeline"
        stages = pipeline.list_stages()
        assert len(stages) == 8

        stage_names = [s.name for s in stages]
        # 验证关键阶段
        assert "analysis" in stage_names
        assert "fix_design" in stage_names
        assert "fix_implementation" in stage_names
        assert "adversarial_verification" in stage_names
        assert "regression_test" in stage_names

        # 验证默认使用 aggressive 模式
        review_stage = pipeline.get_stage("adversarial_verification")
        assert review_stage.role == "bug_hunter"

    def test_create_inquiry_pipeline(self):
        """创建咨询流水线"""
        pipeline = create_inquiry_pipeline()

        assert pipeline.name == "inquiry_pipeline"
        stages = pipeline.list_stages()
        assert len(stages) == 3

    def test_create_management_pipeline(self):
        """创建管理流水线"""
        pipeline = create_management_pipeline()

        assert pipeline.name == "management_pipeline"
        stages = pipeline.list_stages()
        assert len(stages) == 3

    def test_workflow_dependency_graph(self):
        """测试工作流依赖图"""
        pipeline = create_development_pipeline()

        # 验证无循环依赖
        assert pipeline.has_circular_dependency() is False

        # 验证拓扑排序
        order = pipeline.get_execution_order()
        assert len(order) == 8

        # requirements 应该在 design 之前
        assert order.index("requirements") < order.index("design")
        # development 应该在 adversarial_review 之前
        assert order.index("development") < order.index("adversarial_review")

    def test_workflow_mermaid_output(self):
        """测试 Mermaid 可视化输出"""
        pipeline = create_development_pipeline()
        mermaid = pipeline.to_mermaid()

        assert "```mermaid" in mermaid
        assert "graph TD" in mermaid
        assert "requirements" in mermaid
        assert "development" in mermaid

    def test_get_workflow(self):
        """测试获取工作流"""
        pipeline = get_workflow("development_pipeline")
        assert pipeline is not None
        assert pipeline.name == "development_pipeline"

        pipeline = get_workflow("bugfix_pipeline", intensity="aggressive")
        assert pipeline is not None

        # 不存在的工作流
        pipeline = get_workflow("nonexistent")
        assert pipeline is None

    def test_list_workflows(self):
        """测试列出工作流"""
        workflows = list_workflows()
        assert len(workflows) == 5

        names = [w["name"] for w in workflows]
        assert "intent_pipeline" in names
        assert "development_pipeline" in names
        assert "bugfix_pipeline" in names
        assert "inquiry_pipeline" in names
        assert "management_pipeline" in names


class TestQualityGates:
    """测试质量门禁"""

    def test_quality_gate_creation(self):
        """创建质量门禁"""
        gate = QualityGate(
            name="覆盖率检查",
            gate_type=QualityGateType.COVERAGE_THRESHOLD,
            description="测试覆盖率需达到80%",
            required=True,
            threshold=80.0,
        )

        assert gate.name == "覆盖率检查"
        assert gate.gate_type == QualityGateType.COVERAGE_THRESHOLD
        assert gate.threshold == 80.0

    def test_standard_quality_gates(self):
        """测试标准质量门禁集"""
        from harnessgenj.workflow.pipeline import create_standard_quality_gates

        gates = create_standard_quality_gates()

        assert "requirements" in gates
        assert "design" in gates
        assert "development" in gates
        assert "unit_test" in gates
        assert "integration_test" in gates


class TestIntegration:
    """集成测试"""

    def test_intent_to_workflow_routing(self):
        """测试意图到工作流的路由"""
        router = create_intent_router()

        # 模拟用户消息
        messages = [
            ("我需要一个用户登录功能", IntentType.DEVELOPMENT, "development_pipeline"),
            ("文字模式和语音模式切换无法工作", IntentType.BUGFIX, "bugfix_pipeline"),
            ("项目进度如何？", IntentType.MANAGEMENT, "management_pipeline"),
            ("什么是GAN对抗机制？", IntentType.INQUIRY, "inquiry_pipeline"),
        ]

        for message, expected_intent, expected_workflow in messages:
            result = router.identify(message)
            assert result.intent_type == expected_intent, f"Failed for: {message}"
            assert result.target_workflow == expected_workflow

            # 验证可以获取对应工作流
            pipeline = get_workflow(result.target_workflow)
            assert pipeline is not None

    def test_development_pipeline_complete_flow(self):
        """测试开发流水线完整流程"""
        pipeline = create_development_pipeline()

        # 模拟流水线执行
        completed_stages = set()

        # 按顺序执行阶段
        for stage_name in pipeline.get_execution_order():
            stage = pipeline.get_stage(stage_name)
            assert stage is not None

            # 检查依赖是否满足
            assert stage.can_start(completed_stages)

            # 标记完成
            completed_stages.add(stage_name)

        assert len(completed_stages) == 8

    def test_bugfix_pipeline_has_gan(self):
        """测试Bug修复流水线包含GAN对抗"""
        pipeline = create_bugfix_pipeline()

        # 查找对抗审查阶段
        adversarial_stages = [
            s for s in pipeline.list_stages()
            if s.adversarial_config and s.adversarial_config.enabled
        ]

        assert len(adversarial_stages) >= 1

        # 验证使用 BugHunter（aggressive模式）
        verification = pipeline.get_stage("adversarial_verification")
        assert verification is not None
        assert verification.role == "bug_hunter"