"""
Workflow Pipeline v2.0 - 重新设计的工作流系统

核心理念：
1. 所有代码变更必须经过完整的质量保证流程
2. GAN对抗机制集成到所有开发工作流
3. 意图识别作为入口，智能路由到对应工作流

工作流类型：
1. IntentPipeline - 意图识别入口，路由分发
2. DevelopmentPipeline - 统一开发流程（含对抗）
3. BugFixPipeline - Bug修复流程（含对抗）
4. InquiryPipeline - 问题咨询流程（无代码变更）
5. ManagementPipeline - 项目管理流程（无代码变更）

质量保证环节（所有代码变更必经）：
- 需求识别
- 架构规划
- 代码编写
- 对抗优化（GAN）
- 单元测试
- 集成测试
"""

from typing import Any, Callable
from pydantic import BaseModel, Field
from enum import Enum
import time

from harnessgenj.workflow.dependency import (
    DependencyGraph,
    TaskNode,
    TaskStatus as DependencyTaskStatus,
)


class StageStatus(Enum):
    """阶段状态"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"
    UNDER_REVIEW = "under_review"
    REVIEW_FAILED = "review_failed"


class QualityGateType(Enum):
    """质量门禁类型"""

    REQUIREMENT_COMPLETE = "requirement_complete"
    DESIGN_APPROVED = "design_approved"
    CODE_REVIEW_PASSED = "code_review_passed"
    UNIT_TEST_PASSED = "unit_test_passed"
    INTEGRATION_TEST_PASSED = "integration_test_passed"
    COVERAGE_THRESHOLD = "coverage_threshold"


class AdversarialConfig(BaseModel):
    """对抗审查配置"""

    enabled: bool = Field(default=True, description="是否启用对抗审查")
    intensity: str = Field(default="normal", description="审查强度: normal | aggressive")
    max_rounds: int = Field(default=3, description="最大对抗轮次")
    auto_fix: bool = Field(default=True, description="是否自动修复")


class QualityGate(BaseModel):
    """质量门禁"""

    name: str = Field(..., description="门禁名称")
    gate_type: QualityGateType = Field(..., description="门禁类型")
    description: str = Field(default="", description="门禁描述")
    required: bool = Field(default=True, description="是否必须通过")
    threshold: float | None = Field(default=None, description="通过阈值")


class WorkflowStage(BaseModel):
    """工作流阶段"""

    name: str = Field(..., description="阶段名称")
    description: str = Field(default="", description="阶段描述")
    role: str = Field(..., description="负责角色")
    inputs: list[str] = Field(default_factory=list, description="所需输入")
    outputs: list[str] = Field(default_factory=list, description="产出输出")
    quality_gates: list[QualityGate] = Field(default_factory=list, description="质量门禁")
    dependencies: list[str] = Field(default_factory=list, description="依赖的前置阶段")
    adversarial_config: AdversarialConfig | None = Field(default=None, description="对抗配置")

    # 执行状态
    status: StageStatus = Field(default=StageStatus.PENDING, description="状态")
    started_at: float | None = Field(default=None, description="开始时间")
    completed_at: float | None = Field(default=None, description="完成时间")
    result: dict[str, Any] | None = Field(default=None, description="执行结果")

    def can_start(self, completed_stages: set[str]) -> bool:
        """检查是否可以开始"""
        return all(dep in completed_stages for dep in self.dependencies)

    def start(self) -> None:
        """开始阶段"""
        self.status = StageStatus.RUNNING
        self.started_at = time.time()

    def complete(self, result: dict[str, Any]) -> None:
        """完成阶段"""
        self.status = StageStatus.COMPLETED
        self.completed_at = time.time()
        self.result = result

    def fail(self, error: str) -> None:
        """阶段失败"""
        self.status = StageStatus.FAILED
        self.completed_at = time.time()
        self.result = {"error": error}


class WorkflowPipeline:
    """
    工作流流水线

    支持依赖管理、质量门禁、对抗审查
    """

    def __init__(self, name: str = "default_pipeline", description: str = "") -> None:
        self.name = name
        self.description = description
        self._stages: dict[str, WorkflowStage] = {}
        self._stage_order: list[str] = []
        self._artifacts: dict[str, Any] = {}
        self._callbacks: dict[str, list[Callable]] = {}
        self._dependency_graph = DependencyGraph()

    def add_stage(self, stage: WorkflowStage) -> bool:
        """添加阶段"""
        if not self._dependency_graph.add_task(
            task_id=stage.name,
            dependencies=stage.dependencies,
            name=stage.description,
            metadata={
                "role": stage.role,
                "inputs": stage.inputs,
                "outputs": stage.outputs,
            },
        ):
            return False

        self._stages[stage.name] = stage
        self._stage_order.append(stage.name)
        return True

    def remove_stage(self, name: str) -> bool:
        """移除阶段"""
        if name not in self._stages:
            return False
        self._dependency_graph.remove_task(name)
        del self._stages[name]
        self._stage_order.remove(name)
        return True

    def get_stage(self, name: str) -> WorkflowStage | None:
        """获取阶段"""
        return self._stages.get(name)

    def list_stages(self) -> list[WorkflowStage]:
        """列出所有阶段"""
        return [self._stages[name] for name in self._stage_order]

    def get_ready_stages(self) -> list[WorkflowStage]:
        """获取可以执行的阶段"""
        completed = {
            name for name, stage in self._stages.items()
            if stage.status == StageStatus.COMPLETED
        }
        ready = []
        for name in self._stage_order:
            stage = self._stages[name]
            if stage.status == StageStatus.PENDING and stage.can_start(completed):
                ready.append(stage)
        return ready

    def has_circular_dependency(self) -> bool:
        """检测是否存在循环依赖"""
        return self._dependency_graph.has_cycle()

    def get_execution_order(self) -> list[str]:
        """获取拓扑排序后的执行顺序"""
        return self._dependency_graph.topological_sort()

    def to_mermaid(self, title: str | None = None) -> str:
        """生成 Mermaid 可视化图表"""
        return self._dependency_graph.to_mermaid(title or self.name)

    def store_artifact(self, name: str, content: Any) -> None:
        """存储交付物"""
        self._artifacts[name] = {"content": content, "timestamp": time.time()}

    def get_artifact(self, name: str) -> Any | None:
        """获取交付物"""
        artifact = self._artifacts.get(name)
        return artifact["content"] if artifact else None

    def get_status(self) -> dict[str, Any]:
        """获取流水线状态"""
        stages = self.list_stages()
        total = len(stages)
        completed = sum(1 for s in stages if s.status == StageStatus.COMPLETED)
        running = sum(1 for s in stages if s.status == StageStatus.RUNNING)
        failed = sum(1 for s in stages if s.status == StageStatus.FAILED)

        return {
            "pipeline_name": self.name,
            "description": self.description,
            "total_stages": total,
            "completed": completed,
            "running": running,
            "failed": failed,
            "progress": f"{completed}/{total}",
            "progress_percent": (completed / total * 100) if total > 0 else 0,
            "artifacts_count": len(self._artifacts),
        }

    def reset(self) -> None:
        """重置流水线"""
        for stage in self._stages.values():
            stage.status = StageStatus.PENDING
            stage.started_at = None
            stage.completed_at = None
            stage.result = None
        self._artifacts.clear()
        self._dependency_graph.reset()

    def get_dependency_graph(self) -> DependencyGraph:
        """获取底层依赖图"""
        return self._dependency_graph

    def analyze_stage_impact(self, stage_name: str) -> dict[str, Any]:
        """分析修改阶段的影响范围"""
        return self._dependency_graph.analyze_impact(stage_name)


# ==================== 质量门禁工厂 ====================

def create_standard_quality_gates() -> dict[str, list[QualityGate]]:
    """创建标准质量门禁集"""
    return {
        "requirements": [
            QualityGate(name="需求完整性", gate_type=QualityGateType.REQUIREMENT_COMPLETE,
                       description="需求描述完整，包含验收标准", required=True),
        ],
        "design": [
            QualityGate(name="架构评审", gate_type=QualityGateType.DESIGN_APPROVED,
                       description="技术方案经过评审确认", required=True),
        ],
        "development": [
            QualityGate(name="代码审查", gate_type=QualityGateType.CODE_REVIEW_PASSED,
                       description="代码通过对抗审查", required=True),
        ],
        "unit_test": [
            QualityGate(name="单元测试", gate_type=QualityGateType.UNIT_TEST_PASSED,
                       description="所有单元测试通过", required=True),
            QualityGate(name="覆盖率阈值", gate_type=QualityGateType.COVERAGE_THRESHOLD,
                       description="测试覆盖率达到阈值", required=True, threshold=80.0),
        ],
        "integration_test": [
            QualityGate(name="集成测试", gate_type=QualityGateType.INTEGRATION_TEST_PASSED,
                       description="所有集成测试通过", required=True),
        ],
    }


# ==================== 工作流工厂函数 ====================

def create_intent_pipeline() -> WorkflowPipeline:
    """
    创建意图识别流水线

    作为入口工作流，识别用户意图并路由到对应工作流

    流程: 输入接收 → 意图识别 → 实体提取 → 工作流路由
    """
    pipeline = WorkflowPipeline(
        name="intent_pipeline",
        description="意图识别与工作流路由"
    )

    pipeline.add_stage(WorkflowStage(
        name="receive_input",
        description="接收用户输入",
        role="project_manager",
        inputs=["user_message"],
        outputs=["raw_input"],
        dependencies=[],
    ))

    pipeline.add_stage(WorkflowStage(
        name="identify_intent",
        description="意图识别",
        role="project_manager",
        inputs=["raw_input"],
        outputs=["intent_type", "confidence", "entities"],
        dependencies=["receive_input"],
    ))

    pipeline.add_stage(WorkflowStage(
        name="extract_entities",
        description="实体提取",
        role="project_manager",
        inputs=["raw_input", "intent_type"],
        outputs=["feature_name", "module_name", "issue_description"],
        dependencies=["identify_intent"],
    ))

    pipeline.add_stage(WorkflowStage(
        name="route_workflow",
        description="工作流路由",
        role="project_manager",
        inputs=["intent_type", "entities"],
        outputs=["target_workflow", "priority", "task_id"],
        dependencies=["extract_entities"],
    ))

    return pipeline


def create_development_pipeline(
    intensity: str = "normal",
    max_adversarial_rounds: int = 3,
    coverage_threshold: float = 80.0,
) -> WorkflowPipeline:
    """
    创建统一开发流水线

    所有代码变更必须经过的完整质量保证流程：
    需求识别 → 架构规划 → 代码编写 → 对抗优化 → 单元测试 → 集成测试

    Args:
        intensity: 对抗审查强度 ("normal" | "aggressive")
        max_adversarial_rounds: 最大对抗轮次
        coverage_threshold: 测试覆盖率阈值

    Returns:
        配置完整的开发流水线
    """
    pipeline = WorkflowPipeline(
        name="development_pipeline",
        description="统一开发流水线（含GAN对抗）"
    )

    # 对抗配置
    adversarial_cfg = AdversarialConfig(
        enabled=True,
        intensity=intensity,
        max_rounds=max_adversarial_rounds,
        auto_fix=True,
    )

    # 质量门禁
    quality_gates = create_standard_quality_gates()

    # 阶段1: 需求识别
    pipeline.add_stage(WorkflowStage(
        name="requirements",
        description="需求识别与分析",
        role="product_manager",
        inputs=["user_request", "intent_result"],
        outputs=["requirements", "user_stories", "acceptance_criteria"],
        quality_gates=quality_gates.get("requirements", []),
        dependencies=[],
    ))

    # 阶段2: 架构规划
    pipeline.add_stage(WorkflowStage(
        name="design",
        description="架构规划与技术设计",
        role="architect",
        inputs=["requirements", "user_stories"],
        outputs=["architecture", "design_doc", "tech_decisions"],
        quality_gates=quality_gates.get("design", []),
        dependencies=["requirements"],
    ))

    # 阶段3: 代码编写
    pipeline.add_stage(WorkflowStage(
        name="development",
        description="代码编写与实现",
        role="developer",
        inputs=["design_doc", "requirements"],
        outputs=["code", "implementation_notes"],
        quality_gates=quality_gates.get("development", []),
        dependencies=["design"],
        adversarial_config=adversarial_cfg,
    ))

    # 阶段4: 对抗优化（GAN）
    pipeline.add_stage(WorkflowStage(
        name="adversarial_review",
        description="对抗性代码审查（GAN）",
        role="code_reviewer" if intensity == "normal" else "bug_hunter",
        inputs=["code"],
        outputs=["review_result", "issues_found", "quality_score"],
        quality_gates=[
            QualityGate(name="对抗审查通过", gate_type=QualityGateType.CODE_REVIEW_PASSED,
                       description="代码通过对抗审查", required=True),
        ],
        dependencies=["development"],
        adversarial_config=adversarial_cfg,
    ))

    # 阶段5: 修复与优化（条件执行）
    pipeline.add_stage(WorkflowStage(
        name="fix_and_optimize",
        description="问题修复与优化",
        role="developer",
        inputs=["code", "issues_found", "review_result"],
        outputs=["optimized_code", "fix_notes"],
        dependencies=["adversarial_review"],
    ))

    # 阶段6: 单元测试
    pipeline.add_stage(WorkflowStage(
        name="unit_test",
        description="单元测试编写与执行",
        role="tester",
        inputs=["optimized_code", "acceptance_criteria"],
        outputs=["unit_tests", "coverage_report", "test_results"],
        quality_gates=[
            QualityGate(name="单元测试通过", gate_type=QualityGateType.UNIT_TEST_PASSED,
                       description="所有单元测试通过", required=True),
            QualityGate(name="覆盖率达标", gate_type=QualityGateType.COVERAGE_THRESHOLD,
                       description=f"覆盖率≥{coverage_threshold}%", required=True,
                       threshold=coverage_threshold),
        ],
        dependencies=["fix_and_optimize"],
    ))

    # 阶段7: 集成测试
    pipeline.add_stage(WorkflowStage(
        name="integration_test",
        description="集成测试验证",
        role="tester",
        inputs=["optimized_code", "unit_tests", "architecture"],
        outputs=["integration_results", "e2e_results"],
        quality_gates=quality_gates.get("integration_test", []),
        dependencies=["unit_test"],
    ))

    # 阶段8: 完成验收
    pipeline.add_stage(WorkflowStage(
        name="acceptance",
        description="完成验收",
        role="project_manager",
        inputs=["integration_results", "coverage_report", "quality_score"],
        outputs=["acceptance_result", "release_ready"],
        dependencies=["integration_test"],
    ))

    return pipeline


def create_bugfix_pipeline(
    intensity: str = "aggressive",
    max_adversarial_rounds: int = 3,
    coverage_threshold: float = 80.0,
) -> WorkflowPipeline:
    """
    创建Bug修复流水线

    Bug修复同样需要完整的质量保证流程：
    问题分析 → 方案设计 → 代码修复 → 对抗验证 → 回归测试 → 集成验证

    Args:
        intensity: 对抗审查强度 (默认 aggressive，更严格)
        max_adversarial_rounds: 最大对抗轮次
        coverage_threshold: 回归测试覆盖率阈值

    Returns:
        配置完整的Bug修复流水线
    """
    pipeline = WorkflowPipeline(
        name="bugfix_pipeline",
        description="Bug修复流水线（含GAN对抗）"
    )

    # 对抗配置（Bug修复使用更严格的审查）
    adversarial_cfg = AdversarialConfig(
        enabled=True,
        intensity=intensity,
        max_rounds=max_adversarial_rounds,
        auto_fix=True,
    )

    # 质量门禁
    quality_gates = create_standard_quality_gates()

    # 阶段1: 问题分析
    pipeline.add_stage(WorkflowStage(
        name="analysis",
        description="问题分析与定位",
        role="developer",
        inputs=["bug_report", "context"],
        outputs=["root_cause", "affected_modules", "fix_strategy"],
        dependencies=[],
    ))

    # 阶段2: 修复方案设计
    pipeline.add_stage(WorkflowStage(
        name="fix_design",
        description="修复方案设计",
        role="architect",
        inputs=["root_cause", "affected_modules"],
        outputs=["fix_plan", "risk_assessment", "rollback_plan"],
        quality_gates=quality_gates.get("design", []),
        dependencies=["analysis"],
    ))

    # 阶段3: 代码修复
    pipeline.add_stage(WorkflowStage(
        name="fix_implementation",
        description="代码修复实现",
        role="developer",
        inputs=["fix_plan", "root_cause"],
        outputs=["fixed_code", "change_summary"],
        dependencies=["fix_design"],
        adversarial_config=adversarial_cfg,
    ))

    # 阶段4: 对抗验证（严格）
    pipeline.add_stage(WorkflowStage(
        name="adversarial_verification",
        description="对抗性验证（BugHunter）",
        role="bug_hunter",
        inputs=["fixed_code", "bug_report"],
        outputs=["verification_result", "edge_cases", "quality_score"],
        quality_gates=quality_gates.get("development", []),
        dependencies=["fix_implementation"],
        adversarial_config=adversarial_cfg,
    ))

    # 阶段5: 边界修复
    pipeline.add_stage(WorkflowStage(
        name="edge_fix",
        description="边界情况修复",
        role="developer",
        inputs=["fixed_code", "edge_cases"],
        outputs=["final_code", "edge_fix_notes"],
        dependencies=["adversarial_verification"],
    ))

    # 阶段6: 回归测试
    pipeline.add_stage(WorkflowStage(
        name="regression_test",
        description="回归测试",
        role="tester",
        inputs=["final_code", "affected_modules"],
        outputs=["regression_results", "coverage_report"],
        quality_gates=[
            QualityGate(name="回归测试通过", gate_type=QualityGateType.UNIT_TEST_PASSED,
                       description="所有回归测试通过", required=True),
            QualityGate(name="覆盖率达标", gate_type=QualityGateType.COVERAGE_THRESHOLD,
                       description=f"覆盖率≥{coverage_threshold}%", required=True,
                       threshold=coverage_threshold),
        ],
        dependencies=["edge_fix"],
    ))

    # 阶段7: 集成验证
    pipeline.add_stage(WorkflowStage(
        name="integration_verification",
        description="集成环境验证",
        role="tester",
        inputs=["final_code", "regression_results"],
        outputs=["integration_results", "verification_sign_off"],
        quality_gates=quality_gates.get("integration_test", []),
        dependencies=["regression_test"],
    ))

    # 阶段8: 修复完成
    pipeline.add_stage(WorkflowStage(
        name="fix_completion",
        description="修复完成确认",
        role="project_manager",
        inputs=["integration_results", "verification_sign_off"],
        outputs=["fix_complete", "lessons_learned"],
        dependencies=["integration_verification"],
    ))

    return pipeline


def create_inquiry_pipeline() -> WorkflowPipeline:
    """
    创建问题咨询流水线

    无代码变更，仅提供信息查询和解答

    流程: 问题理解 → 信息检索 → 答案生成
    """
    pipeline = WorkflowPipeline(
        name="inquiry_pipeline",
        description="问题咨询流水线"
    )

    pipeline.add_stage(WorkflowStage(
        name="understand_question",
        description="问题理解",
        role="project_manager",
        inputs=["user_question"],
        outputs=["question_type", "search_scope"],
        dependencies=[],
    ))

    pipeline.add_stage(WorkflowStage(
        name="retrieve_info",
        description="信息检索",
        role="project_manager",
        inputs=["question_type", "search_scope"],
        outputs=["relevant_docs", "code_context"],
        dependencies=["understand_question"],
    ))

    pipeline.add_stage(WorkflowStage(
        name="generate_answer",
        description="答案生成",
        role="project_manager",
        inputs=["question_type", "relevant_docs", "code_context"],
        outputs=["answer", "references"],
        dependencies=["retrieve_info"],
    ))

    return pipeline


def create_management_pipeline() -> WorkflowPipeline:
    """
    创建项目管理流水线

    无代码变更，用于进度追踪、资源管理等

    流程: 状态收集 → 分析报告 → 决策建议
    """
    pipeline = WorkflowPipeline(
        name="management_pipeline",
        description="项目管理流水线"
    )

    pipeline.add_stage(WorkflowStage(
        name="collect_status",
        description="状态收集",
        role="project_manager",
        inputs=["request"],
        outputs=["team_status", "task_status", "metrics"],
        dependencies=[],
    ))

    pipeline.add_stage(WorkflowStage(
        name="analyze",
        description="分析报告",
        role="project_manager",
        inputs=["team_status", "task_status", "metrics"],
        outputs=["progress_report", "risk_analysis", "recommendations"],
        dependencies=["collect_status"],
    ))

    pipeline.add_stage(WorkflowStage(
        name="decide",
        description="决策建议",
        role="project_manager",
        inputs=["progress_report", "risk_analysis"],
        outputs=["action_items", "resource_adjustments"],
        dependencies=["analyze"],
    ))

    return pipeline


# ==================== 工作流注册表 ====================

WORKFLOW_REGISTRY: dict[str, Callable] = {
    "intent_pipeline": create_intent_pipeline,
    "development_pipeline": create_development_pipeline,
    "bugfix_pipeline": create_bugfix_pipeline,
    "inquiry_pipeline": create_inquiry_pipeline,
    "management_pipeline": create_management_pipeline,
}


def get_workflow(name: str, **kwargs: Any) -> WorkflowPipeline | None:
    """
    获取工作流实例

    Args:
        name: 工作流名称
        **kwargs: 传递给工作流工厂的参数

    Returns:
        工作流实例，如果不存在返回 None
    """
    factory = WORKFLOW_REGISTRY.get(name)
    if factory:
        return factory(**kwargs)
    return None


def list_workflows() -> list[dict[str, str]]:
    """列出所有可用工作流"""
    return [
        {"name": "intent_pipeline", "description": "意图识别与工作流路由"},
        {"name": "development_pipeline", "description": "统一开发流水线（含GAN对抗）"},
        {"name": "bugfix_pipeline", "description": "Bug修复流水线（含GAN对抗）"},
        {"name": "inquiry_pipeline", "description": "问题咨询流水线"},
        {"name": "management_pipeline", "description": "项目管理流水线"},
    ]


# ==================== 向后兼容 ====================

def create_standard_pipeline() -> WorkflowPipeline:
    """向后兼容：创建标准开发流水线"""
    return create_development_pipeline()


def create_feature_pipeline() -> WorkflowPipeline:
    """向后兼容：创建功能开发流水线"""
    return create_development_pipeline()


def create_adversarial_pipeline(intensity: str = "normal", max_rounds: int = 3) -> WorkflowPipeline:
    """向后兼容：创建对抗性流水线"""
    return create_development_pipeline(intensity=intensity, max_adversarial_rounds=max_rounds)