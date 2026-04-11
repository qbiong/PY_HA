"""
Common Knowledge Types - 统一知识类型定义

此模块提供知识管理系统的公共类型定义，避免多个模块中的重复定义。

使用方式：
- memory/structured_knowledge.py: 从此模块导入
- storage/markdown.py: 从此模块导入
- evolution/pattern_extractor.py: 从此模块导入

统一类型定义：
- KnowledgeType: 知识类型枚举
- KnowledgeEntry: 知识条目基类
- CodeLocation: 代码位置
"""

from typing import Any, Optional
from pydantic import BaseModel, Field
from enum import Enum
import time
import uuid


class KnowledgeType(str, Enum):
    """
    知识类型枚举

    统一的知识类型分类，涵盖所有模块需求。
    """

    # 问题解决类
    BUG_FIX = "bug_fix"                    # Bug 修复记录
    SECURITY_ISSUE = "security_issue"      # 安全问题追踪

    # 设计决策类
    DECISION_PATTERN = "decision_pattern"  # 决策模式沉淀
    ARCHITECTURE_CHANGE = "architecture_change"  # 架构演进追踪

    # 代码资产类
    TEST_CASE = "test_case"                # 测试用例库
    API_REFERENCE = "api_reference"        # API 参考文档

    # 最佳实践类
    BEST_PRACTICE = "best_practice"        # 最佳实践
    LESSON_LEARNED = "lesson_learned"      # 经验教训

    # 自我进化类（v1.5.0 新增）
    SKILL = "skill"                        # 技能定义
    PATTERN = "pattern"                    # 可复用模式

    # 通用类
    GENERAL = "general"                    # 通用知识


class CodeLocation(BaseModel):
    """
    代码位置

    记录知识条目关联的代码位置。
    """

    file_path: str = Field(..., description="文件路径")
    line_start: int = Field(default=0, description="起始行号")
    line_end: int = Field(default=0, description="结束行号")
    function_name: Optional[str] = Field(default=None, description="函数名")
    class_name: Optional[str] = Field(default=None, description="类名")


class KnowledgeEntry(BaseModel):
    """
    知识条目基类

    统一的知识条目数据结构，用于所有知识管理模块。

    字段说明：
    - id: 知识条目唯一标识
    - type: 知识类型（KnowledgeType）
    - problem: 问题描述或触发条件
    - solution: 解决方案或内容
    - code_location: 关联的代码位置
    - quality_score: 质量分数（0-100）
    - verified: 是否已验证
    """

    id: str = Field(default_factory=lambda: f"kn-{uuid.uuid4().hex[:8]}")
    type: KnowledgeType = Field(default=KnowledgeType.GENERAL, description="知识类型")
    title: str = Field(default="", description="标题")
    problem: str = Field(default="", description="问题描述或触发条件")
    solution: str = Field(default="", description="解决方案或内容")
    code_locations: list[CodeLocation] = Field(default_factory=list, description="代码位置列表")
    quality_score: float = Field(default=50.0, ge=0, le=100, description="质量分数")
    severity: str = Field(default="medium", description="严重程度: critical/high/medium/low")
    tags: list[str] = Field(default_factory=list, description="标签")
    verified: bool = Field(default=False, description="是否已验证")
    created_at: float = Field(default_factory=time.time, description="创建时间")
    updated_at: float = Field(default_factory=time.time, description="更新时间")
    metadata: dict[str, Any] = Field(default_factory=dict, description="额外元数据")

    def add_tag(self, tag: str) -> None:
        """添加标签"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = time.time()

    def update_quality(self, score: float) -> None:
        """更新质量分数"""
        self.quality_score = max(0, min(100, score))
        self.updated_at = time.time()

    def mark_verified(self) -> None:
        """标记为已验证"""
        self.verified = True
        self.updated_at = time.time()


class KnowledgeIndex(BaseModel):
    """
    知识索引

    用于快速查找知识条目。
    """

    by_type: dict[str, list[str]] = Field(default_factory=dict, description="按类型索引")
    by_tag: dict[str, list[str]] = Field(default_factory=dict, description="按标签索引")
    by_file: dict[str, list[str]] = Field(default_factory=dict, description="按文件索引")
    by_severity: dict[str, list[str]] = Field(default_factory=dict, description="按严重程度索引")
    by_quality_range: dict[str, list[str]] = Field(default_factory=dict, description="按质量分数范围索引")


# 导出公共类型
__all__ = [
    "KnowledgeType",
    "KnowledgeEntry",
    "CodeLocation",
    "KnowledgeIndex",
]