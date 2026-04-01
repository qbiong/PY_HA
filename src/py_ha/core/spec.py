"""
Agent Specification - Agent行为描述规范

类比 JVM Bytecode: 定义统一的中间表示层
所有Agent都通过这个规范来描述其行为、能力和工具依赖
"""

from typing import Any
from pydantic import BaseModel, Field


class ToolSpec(BaseModel):
    """工具规范 - 定义Agent可使用的工具"""

    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    parameters: dict[str, Any] = Field(default_factory=dict, description="工具参数规范")
    required: list[str] = Field(default_factory=list, description="必需参数列表")


class CapabilitySpec(BaseModel):
    """能力规范 - 定义Agent的核心能力"""

    name: str = Field(..., description="能力名称")
    enabled: bool = Field(default=True, description="是否启用")
    config: dict[str, Any] = Field(default_factory=dict, description="能力配置")


class AgentSpec(BaseModel):
    """
    Agent规范 - Agent的完整行为描述

    这是整个框架的核心抽象，所有Agent都需要通过这个规范来定义。
    类似于 JVM 中的 Class 文件格式，这是一个标准化的描述格式。

    Attributes:
        name: Agent唯一标识
        version: Agent版本号
        description: Agent功能描述
        tools: Agent可使用的工具列表
        capabilities: Agent具备的能力列表
        system_prompt: Agent的系统提示词
        max_tokens: 最大token限制
        timeout: 执行超时时间
    """

    name: str = Field(..., description="Agent唯一标识", min_length=1, max_length=64)
    version: str = Field(default="1.0.0", description="Agent版本号")
    description: str = Field(default="", description="Agent功能描述")
    tools: list[ToolSpec] = Field(default_factory=list, description="工具列表")
    capabilities: list[CapabilitySpec] = Field(default_factory=list, description="能力列表")
    system_prompt: str = Field(default="", description="系统提示词")
    max_tokens: int = Field(default=4096, description="最大token限制", ge=1)
    timeout: int = Field(default=300, description="执行超时时间(秒)", ge=1)

    model_config = {"extra": "allow"}  # 允许扩展字段


class AgentManifest(BaseModel):
    """
    Agent清单 - 多Agent协调的描述

    用于定义多个Agent之间的协作关系
    """

    agents: list[AgentSpec] = Field(default_factory=list, description="Agent列表")
    coordinator: str | None = Field(default=None, description="协调Agent名称")
    delegation_rules: dict[str, list[str]] = Field(
        default_factory=dict,
        description="任务委托规则: agent_name -> [target_agents]"
    )