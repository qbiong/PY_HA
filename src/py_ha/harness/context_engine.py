"""
上下文工程 - Harness 核心能力

解决 Context Rot 问题:
- 长对话中上下文质量退化
- Token 消耗过大
- 关键信息被淹没

核心策略:
1. 压缩 (Compression): 精简冗余信息
2. 摘要 (Summarization): 提取关键信息
3. 卸载 (Offloading): 转存到外部存储
4. 分层 (Layering): 按重要性分层加载

使用示例:
    engine = ContextEngine()

    # 压缩上下文
    compressed = engine.compress(long_context)

    # 生成摘要
    summary = engine.summarize(document)

    # 智能裁剪（保留关键信息）
    pruned = engine.prune_context(context, max_tokens=4000)
"""

from typing import Any
from pydantic import BaseModel, Field
import re
import time


class ContextLayer(BaseModel):
    """上下文层级"""

    name: str = Field(..., description="层级名称")
    content: str = Field(..., description="内容")
    priority: int = Field(default=50, description="优先级 (0-100)")
    token_count: int = Field(default=0, description="Token 数量")
    compressible: bool = Field(default=True, description="是否可压缩")
    category: str = Field(default="general", description="分类")


class CompressionResult(BaseModel):
    """压缩结果"""

    original_length: int = Field(..., description="原始长度")
    compressed_length: int = Field(..., description="压缩后长度")
    compression_ratio: float = Field(..., description="压缩比例")
    content: str = Field(..., description="压缩后内容")
    removed_sections: list[str] = Field(default_factory=list, description="移除的部分")


class SummarizationResult(BaseModel):
    """摘要结果"""

    summary: str = Field(..., description="摘要内容")
    key_points: list[str] = Field(default_factory=list, description="关键点")
    entities: list[str] = Field(default_factory=list, description="实体")
    topics: list[str] = Field(default_factory=list, description="主题")


class ContextEngine:
    """
    上下文引擎

    Harness 核心能力之一:
    1. 上下文压缩 - 减少 Token 消耗
    2. 智能摘要 - 提取关键信息
    3. 上下文裁剪 - 移除低价值信息
    4. 分层管理 - 按优先级加载

    使用示例:
        engine = ContextEngine()

        # 压缩长文本
        result = engine.compress(long_text)
        print(f"压缩比例: {result.compression_ratio:.2%}")

        # 生成摘要
        summary = engine.summarize(document)

        # 智能裁剪
        pruned = engine.prune(context, max_tokens=4000)
    """

    def __init__(self, max_context_tokens: int = 8000) -> None:
        self.max_context_tokens = max_context_tokens

        # 压缩规则
        self._compression_rules = [
            # (pattern, replacement)
            (r'\n{3,}', '\n\n'),  # 多个空行压缩为两个
            (r' {2,}', ' '),       # 多个空格压缩为一个
            (r'#\s*#+\s*', '# '),  # 多个#号
            (r'\*{3,}', '**'),     # 多个*号
            (r'_{3,}', '__'),      # 多个_号
        ]

        # 低价值模式（可移除）
        self._low_value_patterns = [
            r'^\s*#*\s*TODO.*$',
            r'^\s*#*\s*FIXME.*$',
            r'^\s*#*\s*XXX.*$',
            r'^\s*#\s*Type: ignore.*$',
        ]

        # 关键信息模式（不可移除）
        self._key_patterns = [
            r'^\s*#\s*[A-Z].*$',     # 大写标题
            r'class\s+\w+',          # 类定义
            r'def\s+\w+',            # 函数定义
            r'async\s+def\s+\w+',    # 异步函数
            r'import\s+\w+',         # 导入
            r'from\s+\w+\s+import',  # 从...导入
        ]

        # 统计
        self._stats = {
            "total_compressions": 0,
            "total_summarizations": 0,
            "total_tokens_saved": 0,
        }

    def compress(self, content: str, aggressive: bool = False) -> CompressionResult:
        """
        压缩上下文

        Args:
            content: 原始内容
            aggressive: 是否激进压缩

        Returns:
            CompressionResult: 压缩结果
        """
        original_length = len(content)
        removed_sections = []

        # 应用压缩规则
        compressed = content
        for pattern, replacement in self._compression_rules:
            compressed = re.sub(pattern, replacement, compressed, flags=re.MULTILINE)

        # 激进模式：移除低价值内容
        if aggressive:
            lines = compressed.split('\n')
            filtered_lines = []
            for line in lines:
                is_low_value = any(
                    re.match(pattern, line, re.IGNORECASE)
                    for pattern in self._low_value_patterns
                )
                if is_low_value:
                    removed_sections.append(line.strip())
                else:
                    filtered_lines.append(line)
            compressed = '\n'.join(filtered_lines)

        # 移除行尾空白
        compressed = '\n'.join(line.rstrip() for line in compressed.split('\n'))

        # 移除开头和结尾的空白
        compressed = compressed.strip()

        compressed_length = len(compressed)
        compression_ratio = 1 - (compressed_length / original_length) if original_length > 0 else 0

        self._stats["total_compressions"] += 1
        self._stats["total_tokens_saved"] += (original_length - compressed_length) // 4

        return CompressionResult(
            original_length=original_length,
            compressed_length=compressed_length,
            compression_ratio=compression_ratio,
            content=compressed,
            removed_sections=removed_sections,
        )

    def summarize(self, content: str, max_length: int = 500) -> SummarizationResult:
        """
        生成摘要

        Args:
            content: 原始内容
            max_length: 最大长度

        Returns:
            SummarizationResult: 摘要结果
        """
        key_points = []
        entities = set()
        topics = set()

        lines = content.split('\n')

        # 提取关键行
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 检查是否是关键信息
            for pattern in self._key_patterns:
                if re.search(pattern, line):
                    key_points.append(line[:100])
                    break

            # 提取实体（类名、函数名等）
            class_matches = re.findall(r'class\s+(\w+)', line)
            func_matches = re.findall(r'def\s+(\w+)', line)
            entities.update(class_matches)
            entities.update(func_matches)

            # 提取主题（标题）
            if line.startswith('#'):
                topic = re.sub(r'^#+\s*', '', line)
                if topic:
                    topics.add(topic[:50])

        # 生成摘要
        summary_lines = []

        if topics:
            summary_lines.append("## 主要主题")
            summary_lines.extend(f"- {t}" for t in list(topics)[:5])

        if entities:
            summary_lines.append("\n## 关键实体")
            summary_lines.extend(f"- {e}" for e in list(entities)[:10])

        if key_points:
            summary_lines.append("\n## 关键内容")
            summary_lines.extend(f"- {p}" for p in key_points[:10])

        summary = '\n'.join(summary_lines)

        # 限制长度
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."

        self._stats["total_summarizations"] += 1

        return SummarizationResult(
            summary=summary,
            key_points=key_points[:10],
            entities=list(entities)[:20],
            topics=list(topics)[:10],
        )

    def prune_context(
        self,
        content: str,
        max_tokens: int | None = None,
        preserve_sections: list[str] | None = None,
    ) -> str:
        """
        智能裁剪上下文

        保留关键信息，移除低价值内容

        Args:
            content: 原始内容
            max_tokens: 最大 Token 数
            preserve_sections: 必须保留的章节

        Returns:
            裁剪后的内容
        """
        max_tokens = max_tokens or self.max_context_tokens
        preserve_sections = preserve_sections or []

        # 估算 token 数（简化：1 token ≈ 4 chars）
        max_chars = max_tokens * 4

        if len(content) <= max_chars:
            return content

        lines = content.split('\n')
        result_lines = []
        current_length = 0
        in_preserve_section = False

        for line in lines:
            line_length = len(line) + 1  # +1 for newline

            # 检查是否进入/离开保留章节
            for section in preserve_sections:
                if section in line:
                    in_preserve_section = True
                    break
                elif in_preserve_section and line.startswith('#'):
                    in_preserve_section = False

            # 保留章节必须完整保留
            if in_preserve_section:
                result_lines.append(line)
                current_length += line_length
                continue

            # 检查是否是关键信息
            is_key = any(
                re.search(pattern, line)
                for pattern in self._key_patterns
            )

            # 检查是否是低价值信息
            is_low_value = any(
                re.match(pattern, line, re.IGNORECASE)
                for pattern in self._low_value_patterns
            )

            # 决策
            if is_low_value:
                continue
            elif is_key or current_length + line_length <= max_chars:
                result_lines.append(line)
                current_length += line_length
            elif current_length < max_chars * 0.9:
                # 接近限制但还没到，尝试添加
                result_lines.append(line)
                current_length += line_length

        return '\n'.join(result_lines)

    def extract_key_info(self, content: str) -> dict[str, Any]:
        """
        提取关键信息

        Args:
            content: 原始内容

        Returns:
            关键信息字典
        """
        key_info = {
            "classes": [],
            "functions": [],
            "imports": [],
            "constants": [],
            "comments": [],
            "headings": [],
        }

        for line in content.split('\n'):
            line = line.strip()

            # 类定义
            class_match = re.match(r'class\s+(\w+)', line)
            if class_match:
                key_info["classes"].append(class_match.group(1))

            # 函数定义
            func_match = re.match(r'(?:async\s+)?def\s+(\w+)', line)
            if func_match:
                key_info["functions"].append(func_match.group(1))

            # 导入
            import_match = re.match(r'(?:from\s+\S+\s+)?import\s+(.+)', line)
            if import_match:
                key_info["imports"].append(import_match.group(1))

            # 常量
            const_match = re.match(r'^([A-Z_]+)\s*=', line)
            if const_match:
                key_info["constants"].append(const_match.group(1))

            # 注释
            comment_match = re.match(r'#\s*(.+)', line)
            if comment_match and not line.startswith('# Type:'):
                key_info["comments"].append(comment_match.group(1)[:50])

            # 标题
            heading_match = re.match(r'^(#+)\s+(.+)', line)
            if heading_match:
                key_info["headings"].append(heading_match.group(2))

        return key_info

    def estimate_tokens(self, content: str) -> int:
        """
        估算 Token 数量

        简化估算：英文约 1 token = 4 chars，中文约 1 token = 2 chars

        Args:
            content: 内容

        Returns:
            估算的 token 数
        """
        # 统计中文字符
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
        other_chars = len(content) - chinese_chars

        return chinese_chars // 2 + other_chars // 4

    def create_layered_context(
        self,
        content: str,
        layers_config: list[dict[str, Any]] | None = None,
    ) -> list[ContextLayer]:
        """
        创建分层上下文

        Args:
            content: 原始内容
            layers_config: 层级配置

        Returns:
            上下文层级列表
        """
        layers_config = layers_config or [
            {"name": "critical", "priority": 100, "patterns": [r'^\s*class\s+', r'^\s*def\s+']},
            {"name": "important", "priority": 80, "patterns": [r'^\s*import\s+', r'^\s*from\s+']},
            {"name": "normal", "priority": 50, "patterns": [r'.*']},
        ]

        layers = []

        for config in layers_config:
            pattern_matches = []
            for line in content.split('\n'):
                for pattern in config["patterns"]:
                    if re.search(pattern, line):
                        pattern_matches.append(line)
                        break

            if pattern_matches:
                layer_content = '\n'.join(pattern_matches)
                layers.append(ContextLayer(
                    name=config["name"],
                    content=layer_content,
                    priority=config["priority"],
                    token_count=self.estimate_tokens(layer_content),
                ))

        return sorted(layers, key=lambda l: l.priority, reverse=True)

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return self._stats.copy()


class ContextRotDetector:
    """
    Context Rot 检测器

    检测上下文是否退化:
    1. 重复信息过多
    2. 关键信息被稀释
    3. Token 消耗过大
    """

    def __init__(
        self,
        max_context_tokens: int = 8000,
        repetition_threshold: float = 0.3,
    ) -> None:
        self.max_context_tokens = max_context_tokens
        self.repetition_threshold = repetition_threshold

    def detect_rot(self, content: str) -> dict[str, Any]:
        """
        检测 Context Rot

        Args:
            content: 上下文内容

        Returns:
            检测结果
        """
        issues = []

        # 检查 Token 数量
        engine = ContextEngine()
        token_count = engine.estimate_tokens(content)

        if token_count > self.max_context_tokens:
            issues.append({
                "type": "excessive_tokens",
                "severity": "high",
                "message": f"Token 数量 ({token_count}) 超过限制 ({self.max_context_tokens})",
            })

        # 检查重复内容
        lines = content.split('\n')
        unique_lines = set(lines)
        repetition_ratio = 1 - len(unique_lines) / len(lines) if lines else 0

        if repetition_ratio > self.repetition_threshold:
            issues.append({
                "type": "excessive_repetition",
                "severity": "medium",
                "message": f"重复内容比例 ({repetition_ratio:.1%}) 超过阈值 ({self.repetition_threshold:.1%})",
            })

        # 检查空白比例
        blank_count = sum(1 for line in lines if not line.strip())
        blank_ratio = blank_count / len(lines) if lines else 0

        if blank_ratio > 0.5:
            issues.append({
                "type": "excessive_whitespace",
                "severity": "low",
                "message": f"空白行比例 ({blank_ratio:.1%}) 过高",
            })

        return {
            "healthy": len(issues) == 0,
            "token_count": token_count,
            "repetition_ratio": repetition_ratio,
            "issues": issues,
            "recommendations": self._generate_recommendations(issues),
        }

    def _generate_recommendations(self, issues: list[dict]) -> list[str]:
        """生成优化建议"""
        recommendations = []

        for issue in issues:
            if issue["type"] == "excessive_tokens":
                recommendations.append("建议压缩或裁剪上下文")
            elif issue["type"] == "excessive_repetition":
                recommendations.append("建议移除重复内容")
            elif issue["type"] == "excessive_whitespace":
                recommendations.append("建议压缩空白行")

        return recommendations


def create_context_engine(max_tokens: int = 8000) -> ContextEngine:
    """创建上下文引擎"""
    return ContextEngine(max_context_tokens=max_tokens)