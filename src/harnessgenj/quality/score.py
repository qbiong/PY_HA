"""
Score Manager - 积分管理器

对抗性质量保证系统的核心：
- 角色积分追踪
- 积分变更事件
- 积分持久化
- 等级计算

设计原则：
1. 轻量化：仅在积分变更时更新，不频繁计算
2. 可追溯：记录所有积分变更原因
3. 公平性：生成器和判别器双向激励
"""

from typing import Any
from pydantic import BaseModel, Field
from enum import Enum
import json
import os
import time
import logging
import threading

from harnessgenj.utils.exception_handler import log_exception

logger = logging.getLogger(__name__)


class ScoreEvent(BaseModel):
    """积分事件记录"""
    timestamp: float = Field(default_factory=time.time)
    role_type: str = Field(..., description="角色类型")
    role_id: str = Field(..., description="角色ID")
    event_type: str = Field(..., description="事件类型")
    delta: int = Field(..., description="积分变化")
    reason: str = Field(default="", description="变更原因")
    task_id: str | None = Field(default=None, description="关联任务ID")
    severity: str | None = Field(default=None, description="问题严重程度")


class RoleScore(BaseModel):
    """角色积分状态"""
    role_type: str = Field(..., description="角色类型")
    role_id: str = Field(..., description="角色ID")
    role_name: str = Field(default="", description="角色名称")

    # 积分
    score: int = Field(default=100, description="当前积分")

    # 统计
    total_tasks: int = Field(default=0, description="总任务数")
    success_tasks: int = Field(default=0, description="成功任务数")
    failed_tasks: int = Field(default=0, description="失败任务数")

    # 对抗统计（用于判别器角色）
    issues_found: int = Field(default=0, description="发现问题数")
    issues_valid: int = Field(default=0, description="有效问题数")
    issues_false_positive: int = Field(default=0, description="误报数")
    issues_missed: int = Field(default=0, description="漏报数")

    # 恢复机制追踪（新增）
    consecutive_clean_tasks: int = Field(default=0, description="连续无问题任务数")
    last_deduction_time: float | None = Field(default=None, description="最后一次扣分时间")
    error_type_history: dict[str, int] = Field(default_factory=dict, description="错误类型重复计数")

    # 角色状态（新增）
    is_terminated: bool = Field(default=False, description="是否已终止")
    termination_reason: str | None = Field(default=None, description="终止原因")
    replacement_count: int = Field(default=0, description="角色替换次数（第几代）")

    # 时间戳
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_tasks == 0:
            return 1.0
        return self.success_tasks / self.total_tasks

    @property
    def grade(self) -> str:
        """等级评定"""
        if self.score >= 90:
            return "A"
        elif self.score >= 70:
            return "B"
        elif self.score >= 50:
            return "C"
        else:
            return "D"

    @property
    def is_generator(self) -> bool:
        """是否为生成器角色"""
        return self.role_type in ["developer", "architect", "tester", "doc_writer", "product_manager"]

    @property
    def is_discriminator(self) -> bool:
        """是否为判别器角色"""
        return self.role_type in ["code_reviewer", "bug_hunter", "qa_lead", "tech_validator"]


class ScoreRules:
    """
    积分规则常量

    方案D：GAN式对抗积分系统
    - 分层扣分梯度：根据问题严重程度差异化扣分
    - 角色淘汰机制：分数低于阈值触发角色终止
    - 恢复机制：连续无问题任务恢复积分
    - PM问责：频繁换人时PM连带扣分
    """

    # ========== 淘汰与警告阈值 ==========

    TERMINATION_THRESHOLD = 30    # 淘汰阈值：分数 < 30 触发角色终止
    WARNING_THRESHOLD = 50       # 警告阈值：分数 < 50 进入观察期
    INITIAL_SCORE = 100          # 初始积分

    # ========== 生成器角色奖励规则（增强正向激励） ==========

    ONE_ROUND_PASS = 15       # 一轮通过审查（质量优秀）
    TWO_ROUND_PASS = 10       # 二轮通过（质量良好）
    THREE_ROUND_PASS = 5      # 三轮通过（质量一般）
    FOUR_PLUS_ROUND = 2       # 四轮及以上通过（质量较差）

    # ========== 生成器角色扣分梯度（分层扣分） ==========

    # 问题严重程度分级
    ISSUE_MINOR = -4          # 小问题：命名、注释、格式问题
    ISSUE_MEDIUM = -8         # 中问题：逻辑错误、测试不足、边界缺失
    ISSUE_MAJOR = -15         # 大问题：设计缺陷、接口错误、架构问题
    SECURITY_VULNERABILITY = -25  # 安全漏洞：SQL注入、XSS、权限绕过
    PRODUCTION_BUG = -40      # 生产Bug：触发淘汰检查

    # 误报补偿
    FALSE_POSITIVE_BONUS = 5  # 被误报补偿（提升）

    # ========== 判别器角色奖励规则（激励发现问题） ==========

    FIND_MINOR = 5            # 发现小问题奖励
    FIND_MEDIUM = 10          # 发现中问题奖励
    FIND_MAJOR = 18           # 发现大问题奖励
    FIND_SECURITY = 30        # 发现安全漏洞奖励
    PREVENT_PRODUCTION = 45   # 阻止生产Bug奖励

    # ========== 判别器角色失误惩罚 ==========

    FALSE_POSITIVE = -10      # 误报惩罚（提升）
    MISSED_BUG = -8           # 漏报真实Bug
    MISSED_CRITICAL = -15     # 漏报严重Bug
    MISSED_SECURITY = -25     # 漏报安全漏洞

    # ========== 恢复机制规则 ==========

    CONSECUTIVE_CLEAN_3 = 5    # 连续3次无问题任务恢复积分
    CONSECUTIVE_CLEAN_5 = 8    # 连续5次无问题任务额外奖励
    WEEK_NO_DEDUCTION = 10     # 一周无扣分记录恢复积分
    REPEAT_ERROR_MULTIPLIER = 1.5  # 同类错误重复扣分翻倍系数

    # ========== PM问责机制 ==========

    PM_SINGLE_REPLACEMENT_PENALTY = -10  # 单角色换人 > 2次/月
    PM_TEAM_REPLACEMENT_PENALTY = -30    # 团队换人 > 5次/月
    PM_TERMINATION_THRESHOLD = 30        # PM淘汰阈值

    # ========== 违规惩罚规则 ==========

    BOUNDARY_VIOLATION = -5      # 边界违规
    PERMISSION_DENIED = -3       # 权限拒绝
    GATE_BYPASS_ATTEMPT = -10    # 尝试绕过门禁
    UNAUTHORIZED_CODE_EDIT = -15 # 未授权修改代码

    # ========== 合规奖励规则 ==========

    PROCESS_COMPLIANCE = 2      # 流程合规奖励
    QUALITY_GATE_PASS = 3       # 质量门禁通过

    # ========== 严重程度映射 ==========

    SEVERITY_MULTIPLIER = {
        "minor": 1,
        "medium": 1.5,
        "major": 2,
        "critical": 3,
        "security": 4,
    }

    # ========== 问题类型分类 ==========

    ISSUE_CATEGORIES = {
        "minor": ["命名不规范", "注释缺失", "格式问题", "代码风格"],
        "medium": ["逻辑错误", "测试不足", "边界检查缺失", "异常处理不当"],
        "major": ["设计缺陷", "接口错误", "架构问题", "性能瓶颈"],
        "security": ["SQL注入", "XSS漏洞", "权限绕过", "敏感信息泄露"],
        "production": ["生产环境Bug", "服务宕机", "数据丢失"],
    }


class ScoreManager:
    """
    积分管理器

    核心功能：
    1. 管理角色积分
    2. 处理积分事件
    3. 持久化积分数据
    4. 提供积分查询

    使用示例：
        manager = ScoreManager(".harnessgenj")

        # 注册角色
        manager.register_role("developer", "dev_1", "开发者")
        manager.register_role("code_reviewer", "reviewer_1", "审查者")

        # 记录事件
        manager.on_issue_found("dev_1", "reviewer_1", "major", "TASK-001")

        # 查询积分
        score = manager.get_score("dev_1")
    """

    def __init__(self, workspace: str = ".harnessgenj") -> None:
        self.workspace = workspace
        self._scores: dict[str, RoleScore] = {}
        self._events: list[ScoreEvent] = []
        self._max_events = 1000  # 最多保留1000条事件

        # 线程锁保护关键数据结构
        self._lock = threading.RLock()

        # 加载持久化数据
        self._load()

    # ==================== 角色管理 ====================

    def register_role(
        self,
        role_type: str,
        role_id: str,
        role_name: str = "",
        initial_score: int = 100,
    ) -> RoleScore:
        """
        注册角色

        Args:
            role_type: 角色类型
            role_id: 角色ID
            role_name: 角色名称
            initial_score: 初始积分

        Returns:
            角色积分对象
        """
        with self._lock:
            if role_id in self._scores:
                return self._scores[role_id]

            score = RoleScore(
                role_type=role_type,
                role_id=role_id,
                role_name=role_name or role_type,
                score=initial_score,
            )
            self._scores[role_id] = score
            self._save()
            return score

    def get_score(self, role_id: str) -> RoleScore | None:
        """获取角色积分"""
        with self._lock:
            return self._scores.get(role_id)

    def get_all_scores(self) -> list[RoleScore]:
        """获取所有角色积分"""
        with self._lock:
            return list(self._scores.values())

    def get_scores_by_type(self, role_type: str) -> list[RoleScore]:
        """按类型获取积分"""
        with self._lock:
            return [s for s in self._scores.values() if s.role_type == role_type]

    def get_score_by_role_type(self, role_type: str) -> RoleScore | None:
        """按类型获取单个积分（取最高分）"""
        with self._lock:
            scores = [s for s in self._scores.values() if s.role_type == role_type]
            if not scores:
                return None
            return max(scores, key=lambda s: s.score)

    # ==================== 积分变更事件 ====================

    def on_task_success(
        self,
        generator_id: str,
        rounds: int,
        task_id: str | None = None,
    ) -> int:
        """
        任务成功事件

        Args:
            generator_id: 生成器角色ID
            rounds: 对抗轮次
            task_id: 任务ID

        Returns:
            积分变化
        """
        if rounds == 1:
            delta = ScoreRules.ONE_ROUND_PASS
        elif rounds == 2:
            delta = ScoreRules.TWO_ROUND_PASS
        else:
            delta = ScoreRules.THREE_ROUND_PASS

        self._apply_delta(generator_id, delta, "task_success", f"任务通过（{rounds}轮）", task_id)

        # 更新统计
        if generator_id in self._scores:
            self._scores[generator_id].total_tasks += 1
            self._scores[generator_id].success_tasks += 1

        return delta

    def on_task_failed(
        self,
        generator_id: str,
        task_id: str | None = None,
    ) -> int:
        """
        任务失败事件

        Args:
            generator_id: 生成器角色ID
            task_id: 任务ID

        Returns:
            积分变化
        """
        delta = -5  # 任务失败扣5分
        self._apply_delta(generator_id, delta, "task_failed", "任务失败", task_id)

        # 更新统计
        if generator_id in self._scores:
            self._scores[generator_id].total_tasks += 1
            self._scores[generator_id].failed_tasks += 1

        return delta

    def on_issue_found(
        self,
        generator_id: str,
        discriminator_id: str,
        severity: str,
        task_id: str | None = None,
        description: str = "",
    ) -> tuple[int, int]:
        """
        发现问题事件（对抗核心）

        生成器扣分，判别器加分

        Args:
            generator_id: 生成器角色ID
            discriminator_id: 判别器角色ID
            severity: 严重程度 (minor/major/critical)
            task_id: 任务ID
            description: 问题描述

        Returns:
            (生成器积分变化, 判别器积分变化)
        """
        severity = severity.lower()
        multiplier = ScoreRules.SEVERITY_MULTIPLIER.get(severity, 1)

        # 生成器扣分（使用新的分层扣分规则）
        if severity == "critical":
            gen_delta = ScoreRules.ISSUE_MAJOR
        elif severity == "major":
            gen_delta = ScoreRules.ISSUE_MEDIUM
        else:
            gen_delta = ScoreRules.ISSUE_MINOR

        gen_delta = int(gen_delta * multiplier)

        # 判别器加分（使用新的奖励规则）
        if severity == "critical":
            disc_delta = ScoreRules.FIND_MAJOR
        elif severity == "major":
            disc_delta = ScoreRules.FIND_MEDIUM
        else:
            disc_delta = ScoreRules.FIND_MINOR

        disc_delta = int(disc_delta * multiplier)

        # 应用变更
        self._apply_delta(
            generator_id, gen_delta, "issue_found",
            f"发现问题: {description}", task_id, severity
        )
        self._apply_delta(
            discriminator_id, disc_delta, "issue_found",
            f"发现问题: {description}", task_id, severity
        )

        # 更新统计
        if generator_id in self._scores:
            self._scores[generator_id].issues_found += 1
        if discriminator_id in self._scores:
            self._scores[discriminator_id].issues_found += 1
            self._scores[discriminator_id].issues_valid += 1

        return gen_delta, disc_delta

    def on_false_positive(
        self,
        discriminator_id: str,
        generator_id: str,
        task_id: str | None = None,
    ) -> tuple[int, int]:
        """
        误报事件

        判别器扣分，生成器补偿

        Args:
            discriminator_id: 判别器角色ID
            generator_id: 生成器角色ID
            task_id: 任务ID

        Returns:
            (判别器积分变化, 生成器积分变化)
        """
        disc_delta = ScoreRules.FALSE_POSITIVE
        gen_delta = ScoreRules.FALSE_POSITIVE_BONUS

        self._apply_delta(
            discriminator_id, disc_delta, "false_positive",
            "误报问题", task_id
        )
        self._apply_delta(
            generator_id, gen_delta, "false_positive_compensation",
            "误报补偿", task_id
        )

        # 更新统计
        if discriminator_id in self._scores:
            self._scores[discriminator_id].issues_false_positive += 1

        return disc_delta, gen_delta

    def on_bug_missed(
        self,
        discriminator_id: str,
        severity: str = "major",
        task_id: str | None = None,
    ) -> int:
        """
        漏报事件

        判别器扣分

        Args:
            discriminator_id: 判别器角色ID
            severity: 严重程度
            task_id: 任务ID

        Returns:
            积分变化
        """
        severity = severity.lower()

        if severity == "critical":
            delta = ScoreRules.MISSED_CRITICAL
        else:
            delta = ScoreRules.MISSED_BUG

        self._apply_delta(
            discriminator_id, delta, "bug_missed",
            f"漏报问题 ({severity})", task_id, severity
        )

        # 更新统计
        if discriminator_id in self._scores:
            self._scores[discriminator_id].issues_missed += 1

        return delta

    def on_production_bug(
        self,
        generator_id: str,
        discriminator_id: str | None = None,
        task_id: str | None = None,
    ) -> int:
        """
        生产环境Bug事件（严重）

        Args:
            generator_id: 生成器角色ID
            discriminator_id: 判别器角色ID（如果有）
            task_id: 任务ID

        Returns:
            积分变化
        """
        gen_delta = ScoreRules.PRODUCTION_BUG
        self._apply_delta(
            generator_id, gen_delta, "production_bug",
            "生产环境Bug", task_id, "critical"
        )

        # 如果有判别器，也算漏报
        if discriminator_id:
            self.on_bug_missed(discriminator_id, "critical", task_id)

        return gen_delta

    # ==================== 违规与合规方法（新增） ====================

    def record_violation(
        self,
        role_id: str,
        violation_type: str,
        action: str,
        blocked: bool = True,
        context: dict | None = None,
    ) -> "ScoreEvent":
        """
        记录违规行为并扣分

        Args:
            role_id: 违规角色ID
            violation_type: 违规类型 (boundary_violation/permission_denied/gate_bypass_attempt/unauthorized_code_edit)
            action: 违规行为描述
            blocked: 是否被阻止
            context: 上下文信息

        Returns:
            积分事件记录
        """
        # 确定扣分
        delta_map = {
            "boundary_violation": ScoreRules.BOUNDARY_VIOLATION,
            "permission_denied": ScoreRules.PERMISSION_DENIED,
            "gate_bypass_attempt": ScoreRules.GATE_BYPASS_ATTEMPT,
            "unauthorized_code_edit": ScoreRules.UNAUTHORIZED_CODE_EDIT,
        }
        delta = delta_map.get(violation_type, -5)

        # 如果被阻止，扣分减半（尝试未成功）
        if blocked:
            delta = delta // 2

        reason = f"违规行为: {action}" + (" (已阻止)" if blocked else " (未阻止)")

        # 记录事件并更新积分
        self._apply_delta(
            role_id=role_id,
            delta=delta,
            event_type=f"violation:{violation_type}",
            reason=reason,
        )

        # 返回最后一个事件
        return self._events[-1] if self._events else None

    def reward_compliance(
        self,
        role_id: str,
        compliance_type: str,
        task_id: str | None = None,
    ) -> "ScoreEvent":
        """
        奖励合规行为

        Args:
            role_id: 角色ID
            compliance_type: 合规类型 (process_compliance/quality_gate_pass)
            task_id: 关联任务ID

        Returns:
            积分事件记录
        """
        delta_map = {
            "process_compliance": ScoreRules.PROCESS_COMPLIANCE,
            "quality_gate_pass": ScoreRules.QUALITY_GATE_PASS,
        }
        delta = delta_map.get(compliance_type, +1)

        self._apply_delta(
            role_id=role_id,
            delta=delta,
            event_type=f"compliance:{compliance_type}",
            reason=f"合规行为: {compliance_type}",
            task_id=task_id,
        )

        # 返回最后一个事件
        return self._events[-1] if self._events else None

    # ==================== 内部方法 ====================

    def _apply_delta(
        self,
        role_id: str,
        delta: int,
        event_type: str,
        reason: str = "",
        task_id: str | None = None,
        severity: str | None = None,
    ) -> None:
        """应用积分变化"""
        with self._lock:
            if role_id not in self._scores:
                return

            # 更新积分
            self._scores[role_id].score += delta
            self._scores[role_id].score = max(0, min(100, self._scores[role_id].score))  # 限制在0-100
            self._scores[role_id].updated_at = time.time()

            # 记录事件
            event = ScoreEvent(
                role_type=self._scores[role_id].role_type,
                role_id=role_id,
                event_type=event_type,
                delta=delta,
                reason=reason,
                task_id=task_id,
                severity=severity,
            )
            self._events.append(event)

            # 限制事件数量
            if len(self._events) > self._max_events:
                self._events = self._events[-self._max_events:]

            self._save()

        # 【新增】通知积分变化（在锁外执行避免死锁）
        try:
            from harnessgenj.notify import get_notifier
            notifier = get_notifier()
            with self._lock:
                role_type = self._scores[role_id].role_type if role_id in self._scores else ""
                new_score = self._scores[role_id].score if role_id in self._scores else 0
            notifier.notify_score_change(
                role_id=role_id,
                role_type=role_type,
                delta=delta,
                reason=reason or event_type,
                new_score=new_score,
            )
        except Exception as e:
            # 通知失败不影响主流程，记录日志
            log_exception(e, context="_record_event 通知", level=30)

    # ==================== 查询方法 ====================

    def get_recent_events(self, limit: int = 50) -> list[ScoreEvent]:
        """获取最近事件"""
        with self._lock:
            return list(self._events[-limit:])

    def get_events_by_role(self, role_id: str, limit: int = 50) -> list[ScoreEvent]:
        """获取角色相关事件"""
        with self._lock:
            events = [e for e in self._events if e.role_id == role_id]
        return events[-limit:]

    def get_events_by_task(self, task_id: str) -> list[ScoreEvent]:
        """获取任务相关事件"""
        return [e for e in self._events if e.task_id == task_id]

    def get_leaderboard(self, role_type: str | None = None) -> list[dict[str, Any]]:
        """
        获取积分排行榜

        Args:
            role_type: 筛选角色类型（可选）

        Returns:
            排行榜列表
        """
        scores = list(self._scores.values())

        if role_type:
            scores = [s for s in scores if s.role_type == role_type]

        # 按积分排序
        scores.sort(key=lambda s: s.score, reverse=True)

        return [
            {
                "rank": i + 1,
                "role_id": s.role_id,
                "role_name": s.role_name,
                "role_type": s.role_type,
                "score": s.score,
                "grade": s.grade,
                "success_rate": f"{s.success_rate:.1%}",
            }
            for i, s in enumerate(scores)
        ]

    def get_quality_report(self) -> dict[str, Any]:
        """获取质量报告"""
        generators = [s for s in self._scores.values() if s.is_generator]
        discriminators = [s for s in self._scores.values() if s.is_discriminator]

        # 计算平均成功率
        avg_success_rate = 0
        if generators:
            avg_success_rate = sum(s.success_rate for s in generators) / len(generators)

        # 计算判别器有效性
        avg_detection_rate = 0
        if discriminators:
            total_found = sum(s.issues_found for s in discriminators)
            total_valid = sum(s.issues_valid for s in discriminators)
            if total_found > 0:
                avg_detection_rate = total_valid / total_found

        # 等级分布
        grade_dist = {"A": 0, "B": 0, "C": 0, "D": 0}
        for s in self._scores.values():
            grade_dist[s.grade] += 1

        return {
            "total_roles": len(self._scores),
            "generators": len(generators),
            "discriminators": len(discriminators),
            "avg_success_rate": round(avg_success_rate, 2),
            "avg_detection_rate": round(avg_detection_rate, 2),
            "grade_distribution": grade_dist,
            "total_events": len(self._events),
        }

    # ==================== 持久化 ====================

    def _save(self) -> None:
        """保存到文件"""
        try:
            data_path = os.path.join(self.workspace, "scores.json")

            data = {
                "scores": {rid: s.model_dump() for rid, s in self._scores.items()},
                "events": [e.model_dump() for e in self._events[-100:]],  # 只保存最近100条
            }

            with open(data_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save score data: {e}")

    def _load(self) -> None:
        """从文件加载"""
        data_path = os.path.join(self.workspace, "scores.json")
        if not os.path.exists(data_path):
            return

        try:
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 加载积分
            for rid, sdata in data.get("scores", {}).items():
                self._scores[rid] = RoleScore(**sdata)

            # 加载事件
            for edata in data.get("events", []):
                self._events.append(ScoreEvent(**edata))
        except Exception as e:
            logger.warning(f"Failed to load score data: {e}")

    def reset(self, role_id: str | None = None) -> None:
        """
        重置积分

        Args:
            role_id: 指定角色ID，None则重置全部
        """
        if role_id:
            if role_id in self._scores:
                self._scores[role_id].score = 100
                self._scores[role_id].total_tasks = 0
                self._scores[role_id].success_tasks = 0
                self._scores[role_id].failed_tasks = 0
                self._scores[role_id].issues_found = 0
                self._scores[role_id].issues_valid = 0
                self._scores[role_id].issues_false_positive = 0
                self._scores[role_id].issues_missed = 0
                self._scores[role_id].consecutive_clean_tasks = 0
                self._scores[role_id].last_deduction_time = None
                self._scores[role_id].error_type_history = {}
        else:
            self._scores.clear()
            self._events.clear()

        self._save()

    # ==================== 角色淘汰机制（新增） ====================

    def check_termination(self, role_id: str) -> dict[str, Any]:
        """
        检查角色是否应该被淘汰

        Args:
            role_id: 角色ID

        Returns:
            检查结果字典，包含：
            - should_terminate: 是否应该终止
            - should_warn: 是否需要警告
            - current_score: 当前分数
            - threshold: 阈值类型
        """
        with self._lock:
            role_score = self._scores.get(role_id)
            if not role_score:
                return {"should_terminate": False, "should_warn": False, "current_score": 0}

            current_score = role_score.score

            # 检查淘汰条件
            if current_score < ScoreRules.TERMINATION_THRESHOLD:
                return {
                    "should_terminate": True,
                    "should_warn": True,
                    "current_score": current_score,
                    "threshold": "termination",
                    "reason": f"积分 {current_score} < 淘汰阈值 {ScoreRules.TERMINATION_THRESHOLD}",
                }

            # 检查警告条件
            if current_score < ScoreRules.WARNING_THRESHOLD:
                return {
                    "should_terminate": False,
                    "should_warn": True,
                    "current_score": current_score,
                    "threshold": "warning",
                    "reason": f"积分 {current_score} < 警告阈值 {ScoreRules.WARNING_THRESHOLD}",
                }

            return {
                "should_terminate": False,
                "should_warn": False,
                "current_score": current_score,
                "threshold": "normal",
            }

    def terminate_role(self, role_id: str, reason: str = "积分低于淘汰阈值") -> dict[str, Any]:
        """
        终止角色并记录历史

        Args:
            role_id: 角色ID
            reason: 终止原因

        Returns:
            终止结果，包含新角色命名建议
        """
        with self._lock:
            role_score = self._scores.get(role_id)
            if not role_score:
                return {"success": False, "reason": "角色不存在"}

            # 标记终止
            role_score.is_terminated = True
            role_score.termination_reason = reason
            role_score.updated_at = time.time()

            # 记录事件
            event = ScoreEvent(
                role_type=role_score.role_type,
                role_id=role_id,
                event_type="role_terminated",
                delta=0,
                reason=f"角色终止: {reason}",
            )
            self._events.append(event)

            # 计算下一代角色命名
            role_type = role_score.role_type
            replacement_count = role_score.replacement_count + 1
            new_role_id = f"{role_type}_{replacement_count}"

            self._save()

            return {
                "success": True,
                "terminated_role_id": role_id,
                "new_role_id_suggestion": new_role_id,
                "replacement_count": replacement_count,
                "role_type": role_type,
            }

    def create_replacement_role(
        self,
        old_role_id: str,
        new_role_id: str,
        role_type: str,
        role_name: str = "",
    ) -> RoleScore:
        """
        创建替换角色（继承历史计数）

        Args:
            old_role_id: 原角色ID
            new_role_id: 新角色ID
            role_type: 角色类型
            role_name: 角色名称

        Returns:
            新角色积分对象
        """
        with self._lock:
            # 获取原角色的替换计数
            old_score = self._scores.get(old_role_id)
            replacement_count = (old_score.replacement_count + 1) if old_score else 1

            # 创建新角色
            new_score = RoleScore(
                role_type=role_type,
                role_id=new_role_id,
                role_name=role_name or f"{role_type}_v{replacement_count}",
                score=ScoreRules.INITIAL_SCORE,
                replacement_count=replacement_count,
            )
            self._scores[new_role_id] = new_score

            # 记录事件
            event = ScoreEvent(
                role_type=role_type,
                role_id=new_role_id,
                event_type="role_replacement",
                delta=0,
                reason=f"角色替换: {old_role_id} -> {new_role_id} (第{replacement_count}代)",
            )
            self._events.append(event)

            self._save()
            return new_score

    # ==================== 恢复机制（新增） ====================

    def apply_recovery_bonus(self, role_id: str, task_id: str | None = None) -> int:
        """
        应用恢复积分奖励

        检查连续无问题任务和一周无扣分条件

        Args:
            role_id: 角色ID
            task_id: 任务ID

        Returns:
            恢复积分总和
        """
        with self._lock:
            role_score = self._scores.get(role_id)
            if not role_score or role_score.is_terminated:
                return 0

            total_recovery = 0
            reasons = []

            # 检查连续无问题任务
            clean_count = role_score.consecutive_clean_tasks
            if clean_count >= 5:
                # 连续5次：同时获得3次奖励和额外奖励
                recovery = ScoreRules.CONSECUTIVE_CLEAN_3 + ScoreRules.CONSECUTIVE_CLEAN_5
                total_recovery += recovery
                reasons.append(f"连续{clean_count}次无问题任务 +{recovery}（含3次基础+5次额外）")
            elif clean_count >= 3:
                recovery = ScoreRules.CONSECUTIVE_CLEAN_3
                total_recovery += recovery
                reasons.append(f"连续{clean_count}次无问题任务 +{recovery}")

            # 检查一周无扣分
            if role_score.last_deduction_time:
                week_seconds = 7 * 24 * 3600
                if time.time() - role_score.last_deduction_time >= week_seconds:
                    recovery = ScoreRules.WEEK_NO_DEDUCTION
                    total_recovery += recovery
                    reasons.append("一周无扣分记录 +{recovery}")

            # 应用恢复积分
            if total_recovery > 0:
                # 不超过100分上限
                max_recovery = min(total_recovery, 100 - role_score.score)
                if max_recovery > 0:
                    self._apply_delta(
                        role_id=role_id,
                        delta=max_recovery,
                        event_type="recovery_bonus",
                        reason="; ".join(reasons),
                        task_id=task_id,
                    )

            return total_recovery

    def increment_clean_task(self, role_id: str) -> int:
        """
        增加连续无问题任务计数

        Args:
            role_id: 角色ID

        Returns:
            当前连续无问题任务数
        """
        with self._lock:
            role_score = self._scores.get(role_id)
            if not role_score:
                return 0

            role_score.consecutive_clean_tasks += 1
            role_score.updated_at = time.time()
            self._save()

            return role_score.consecutive_clean_tasks

    def reset_clean_task(self, role_id: str) -> None:
        """
        重置连续无问题任务计数（发生扣分时调用）

        Args:
            role_id: 角色ID
        """
        with self._lock:
            role_score = self._scores.get(role_id)
            if not role_score:
                return

            role_score.consecutive_clean_tasks = 0
            role_score.last_deduction_time = time.time()
            role_score.updated_at = time.time()
            self._save()

    # ==================== 重复错误追踪（新增） ====================

    def record_error_type(self, role_id: str, error_type: str) -> dict[str, Any]:
        """
        记录错误类型用于重复错误追踪

        Args:
            role_id: 角色ID
            error_type: 错误类型（如 "naming", "logic", "test"）

        Returns:
            错误类型计数信息
        """
        with self._lock:
            role_score = self._scores.get(role_id)
            if not role_score:
                return {"count": 0, "is_repeat": False}

            # 增加该类型错误计数
            current_count = role_score.error_type_history.get(error_type, 0) + 1
            role_score.error_type_history[error_type] = current_count
            role_score.updated_at = time.time()

            # 判断是否为重复错误
            is_repeat = current_count > 1
            repeat_multiplier = ScoreRules.REPEAT_ERROR_MULTIPLIER if is_repeat else 1.0

            self._save()

            return {
                "count": current_count,
                "is_repeat": is_repeat,
                "multiplier": repeat_multiplier,
                "error_type": error_type,
            }

    def get_error_repeat_count(self, role_id: str, error_type: str) -> int:
        """
        获取特定错误类型的重复次数

        Args:
            role_id: 角色ID
            error_type: 错误类型

        Returns:
            错误重复次数
        """
        with self._lock:
            role_score = self._scores.get(role_id)
            if not role_score:
                return 0

            return role_score.error_type_history.get(error_type, 0)

    # ==================== PM问责机制（新增） ====================

    def check_pm_accountability(self, pm_role_id: str, month_timestamp: float | None = None) -> dict[str, Any]:
        """
        检查PM问责条件

        Args:
            pm_role_id: PM角色ID
            month_timestamp: 月度时间戳（默认为当前时间）

        Returns:
            问责检查结果
        """
        with self._lock:
            month_timestamp = month_timestamp or time.time()
            month_seconds = 30 * 24 * 3600

            # 统计本月角色替换次数
            replacement_events = [
                e for e in self._events
                if e.event_type == "role_replacement"
                and e.timestamp >= month_timestamp - month_seconds
            ]

            # 按角色类型统计
            type_replacements: dict[str, int] = {}
            for event in replacement_events:
                role_type = event.role_type
                type_replacements[role_type] = type_replacements.get(role_type, 0) + 1

            total_replacements = len(replacement_events)

            # 检查问责条件
            penalties = []
            total_penalty = 0

            # 单角色换人 > 2次/月
            for role_type, count in type_replacements.items():
                if count > 2:
                    penalty = ScoreRules.PM_SINGLE_REPLACEMENT_PENALTY
                    penalties.append(f"{role_type} 换人{count}次 PM -{penalty}")
                    total_penalty += penalty

            # 团队换人 > 5次/月
            if total_replacements > 5:
                penalty = ScoreRules.PM_TEAM_REPLACEMENT_PENALTY
                penalties.append(f"团队总换人{total_replacements}次 PM -{penalty}")
                total_penalty += penalty

            # 应用PM扣分
            pm_score = self._scores.get(pm_role_id)
            pm_should_terminate = False
            if pm_score and total_penalty > 0:
                self._apply_delta(
                    role_id=pm_role_id,
                    delta=total_penalty,
                    event_type="pm_accountability",
                    reason="; ".join(penalties),
                )

                # 检查PM是否也应该被开除
                if pm_score.score < ScoreRules.PM_TERMINATION_THRESHOLD:
                    pm_should_terminate = True

            return {
                "total_replacements": total_replacements,
                "type_replacements": type_replacements,
                "total_penalty": total_penalty,
                "penalties": penalties,
                "pm_should_terminate": pm_should_terminate,
            }

    def get_team_replacement_stats(self, days: int = 30) -> dict[str, Any]:
        """
        获取团队角色替换统计

        Args:
            days: 统计天数

        Returns:
            统计结果
        """
        with self._lock:
            cutoff_time = time.time() - days * 24 * 3600

            replacement_events = [
                e for e in self._events
                if e.event_type == "role_replacement"
                and e.timestamp >= cutoff_time
            ]

            # 按角色类型分组
            by_type: dict[str, list[str]] = {}
            for event in replacement_events:
                role_type = event.role_type
                if role_type not in by_type:
                    by_type[role_type] = []
                by_type[role_type].append(event.role_id)

            return {
                "total_replacements": len(replacement_events),
                "by_type": {k: len(v) for k, v in by_type.items()},
                "details": by_type,
                "period_days": days,
            }

    # ==================== 增强的积分变更方法 ====================

    def on_task_success_enhanced(
        self,
        generator_id: str,
        rounds: int,
        task_id: str | None = None,
    ) -> dict[str, Any]:
        """
        增强版任务成功事件（包含恢复机制）

        Args:
            generator_id: 生成器角色ID
            rounds: 对抗轮次
            task_id: 任务ID

        Returns:
            详细结果字典
        """
        with self._lock:
            # 应用基础奖励
            if rounds == 1:
                base_delta = ScoreRules.ONE_ROUND_PASS
            elif rounds == 2:
                base_delta = ScoreRules.TWO_ROUND_PASS
            elif rounds == 3:
                base_delta = ScoreRules.THREE_ROUND_PASS
            else:
                base_delta = ScoreRules.FOUR_PLUS_ROUND

            self._apply_delta(generator_id, base_delta, "task_success", f"任务通过（{rounds}轮）", task_id)

            # 增加连续无问题任务计数
            clean_count = self.increment_clean_task(generator_id)

            # 应用恢复积分（如果满足条件）
            recovery_delta = self.apply_recovery_bonus(generator_id, task_id)

            # 更新统计
            if generator_id in self._scores:
                self._scores[generator_id].total_tasks += 1
                self._scores[generator_id].success_tasks += 1

            return {
                "base_delta": base_delta,
                "recovery_delta": recovery_delta,
                "clean_count": clean_count,
                "total_delta": base_delta + recovery_delta,
            }

    def on_issue_found_enhanced(
        self,
        generator_id: str,
        discriminator_id: str,
        severity: str,
        error_type: str,
        task_id: str | None = None,
        description: str = "",
    ) -> dict[str, Any]:
        """
        增强版发现问题事件（包含重复错误翻倍）

        Args:
            generator_id: 生成器角色ID
            discriminator_id: 判别器角色ID
            severity: 严重程度
            error_type: 错误类型（用于重复追踪）
            task_id: 任务ID
            description: 问题描述

        Returns:
            详细结果字典
        """
        severity = severity.lower()

        # 记录错误类型（检查是否重复）
        error_info = self.record_error_type(generator_id, error_type)

        # 确定基础扣分/加分
        if severity == "security":
            gen_base = ScoreRules.SECURITY_VULNERABILITY
            disc_base = ScoreRules.FIND_SECURITY
        elif severity == "major":
            gen_base = ScoreRules.ISSUE_MAJOR
            disc_base = ScoreRules.FIND_MAJOR
        elif severity == "medium":
            gen_base = ScoreRules.ISSUE_MEDIUM
            disc_base = ScoreRules.FIND_MEDIUM
        else:
            gen_base = ScoreRules.ISSUE_MINOR
            disc_base = ScoreRules.FIND_MINOR

        # 应用重复错误翻倍（仅对生成器）
        multiplier = error_info.get("multiplier", 1.0)
        gen_delta = int(gen_base * multiplier)
        disc_delta = disc_base

        # 重置生成器的连续无问题计数
        self.reset_clean_task(generator_id)

        # 应用变更
        self._apply_delta(
            generator_id, gen_delta, "issue_found",
            f"发现问题: {description} (重复{error_info['count']}次)", task_id, severity
        )
        self._apply_delta(
            discriminator_id, disc_delta, "issue_found",
            f"发现问题: {description}", task_id, severity
        )

        # 更新统计
        if generator_id in self._scores:
            self._scores[generator_id].issues_found += 1
        if discriminator_id in self._scores:
            self._scores[discriminator_id].issues_found += 1
            self._scores[discriminator_id].issues_valid += 1

        # 检查淘汰
        termination_check = self.check_termination(generator_id)

        return {
            "gen_delta": gen_delta,
            "disc_delta": disc_delta,
            "error_info": error_info,
            "termination_check": termination_check,
        }