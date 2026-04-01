"""
Human-in-the-loop - 人机交互节点

Harness 内置能力之一:
- 执行审批
- 用户输入获取
- 决策确认
"""

from typing import Any
from pydantic import BaseModel, Field
from enum import Enum


class ApprovalStatus(Enum):
    """审批状态"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"


class ApprovalRequest(BaseModel):
    """审批请求"""

    request_id: str = Field(..., description="请求ID")
    action: str = Field(..., description="需要审批的操作")
    context: dict[str, Any] = Field(default_factory=dict, description="上下文信息")
    status: ApprovalStatus = Field(default=ApprovalStatus.PENDING, description="状态")
    timeout: int = Field(default=300, description="超时时间(秒)")
    created_at: float = Field(default=0.0, description="创建时间")


class ApprovalResponse(BaseModel):
    """审批响应"""

    request_id: str = Field(..., description="请求ID")
    approved: bool = Field(..., description="是否批准")
    feedback: str | None = Field(default=None, description="反馈信息")
    responded_at: float = Field(..., description="响应时间")


class HumanLoop:
    """
    人机交互循环 - 提供审批和交互能力

    核心功能:
    1. 操作审批
    2. 用户输入获取
    3. 决策确认
    4. 超时处理
    """

    def __init__(self, default_timeout: int = 300) -> None:
        self.default_timeout = default_timeout
        self._pending_requests: dict[str, ApprovalRequest] = {}
        self._responses: dict[str, ApprovalResponse] = {}

    async def request_approval(
        self,
        action: str,
        context: dict[str, Any] | None = None,
        timeout: int | None = None,
    ) -> ApprovalRequest:
        """
        发起审批请求

        Args:
            action: 需要审批的操作描述
            context: 上下文信息
            timeout: 超时时间

        Returns:
            ApprovalRequest: 审批请求
        """
        import time
        import uuid

        request = ApprovalRequest(
            request_id=str(uuid.uuid4()),
            action=action,
            context=context or {},
            timeout=timeout or self.default_timeout,
            created_at=time.time(),
        )
        self._pending_requests[request.request_id] = request

        # TODO: 实现实际的审批等待逻辑
        # 当前为简化实现，自动批准
        request.status = ApprovalStatus.APPROVED

        return request

    def respond_approval(self, request_id: str, approved: bool, feedback: str | None = None) -> ApprovalResponse:
        """
        响应审批请求

        Args:
            request_id: 请求ID
            approved: 是否批准
            feedback: 反馈信息

        Returns:
            ApprovalResponse: 审批响应
        """
        import time

        request = self._pending_requests.get(request_id)
        if request is None:
            raise ValueError(f"Request not found: {request_id}")

        response = ApprovalResponse(
            request_id=request_id,
            approved=approved,
            feedback=feedback,
            responded_at=time.time(),
        )
        self._responses[request_id] = response

        # 更新请求状态
        request.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED

        return response

    def get_request(self, request_id: str) -> ApprovalRequest | None:
        """获取审批请求"""
        return self._pending_requests.get(request_id)

    def get_response(self, request_id: str) -> ApprovalResponse | None:
        """获取审批响应"""
        return self._responses.get(request_id)

    async def wait_for_approval(self, request_id: str) -> ApprovalResponse:
        """
        等待审批结果

        Args:
            request_id: 请求ID

        Returns:
            ApprovalResponse: 审批响应
        """
        import asyncio
        import time

        request = self.get_request(request_id)
        if request is None:
            raise ValueError(f"Request not found: {request_id}")

        # 简化实现：检查是否已有响应
        start_time = time.time()
        while time.time() - start_time < request.timeout:
            response = self.get_response(request_id)
            if response is not None:
                return response
            await asyncio.sleep(0.5)

        # 超时
        request.status = ApprovalStatus.TIMEOUT
        return ApprovalResponse(
            request_id=request_id,
            approved=False,
            feedback="Approval timeout",
            responded_at=time.time(),
        )

    def list_pending(self) -> list[ApprovalRequest]:
        """列出所有待审批请求"""
        return [
            r for r in self._pending_requests.values()
            if r.status == ApprovalStatus.PENDING
        ]