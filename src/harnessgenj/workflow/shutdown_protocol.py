"""
Shutdown Protocol - Agent 关闭审批协议

参考 Claude Code 的 Shutdown 协议设计，实现：
- shutdown_request: Coordinator 发送关闭请求
- shutdown_response: Worker 响应关闭请求
- 未完成任务拒绝关闭
- 完成任务同意关闭

使用示例：
    from harnessgenj.workflow.shutdown_protocol import (
        ShutdownProtocol,
        ShutdownRequest,
        ShutdownResponse,
    )

    # 发送关闭请求
    protocol = ShutdownProtocol()
    request = ShutdownRequest(agent_id="worker_1", reason="任务完成")
    response = await protocol.request_shutdown(request)

    # 处理关闭请求（Worker 端）
    if protocol.has_pending_tasks():
        protocol.respond_shutdown(approved=False, reason="有未完成任务")
    else:
        protocol.respond_shutdown(approved=True, reason="可以关闭")
"""

from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime
from enum import Enum
import time
import json
from pathlib import Path


class ShutdownStatus(Enum):
    """Shutdown 状态"""

    PENDING = "pending"      # 等待响应
    APPROVED = "approved"    # 已批准
    REJECTED = "rejected"    # 已拒绝
    TIMEOUT = "timeout"      # 超时


class ShutdownRequest(BaseModel):
    """Shutdown 请求"""

    request_id: str = Field(default_factory=lambda: f"shutdown-{int(time.time())}-{hash(str(time.time())) % 10000:04d}")
    agent_id: str
    requester_id: str        # 发送请求的 Agent ID
    reason: str              # 关闭原因
    timeout_seconds: float = 30.0  # 超时时间
    created_at: float = Field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "type": "shutdown_request",
            "request_id": self.request_id,
            "agent_id": self.agent_id,
            "requester_id": self.requester_id,
            "reason": self.reason,
            "timeout_seconds": self.timeout_seconds,
            "created_at": self.created_at,
        }


class ShutdownResponse(BaseModel):
    """Shutdown 响应"""

    request_id: str          # 对应的请求 ID
    agent_id: str            # 响应的 Agent ID
    approved: bool           # 是否批准关闭
    reason: Optional[str] = None  # 响应原因
    pending_tasks: list[str] = Field(default_factory=list)  # 未完成任务
    responded_at: float = Field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "type": "shutdown_response",
            "request_id": self.request_id,
            "agent_id": self.agent_id,
            "approved": self.approved,
            "reason": self.reason,
            "pending_tasks": self.pending_tasks,
            "responded_at": self.responded_at,
        }


class ShutdownProtocol:
    """
    Shutdown 协议实现

    流程：
    1. Coordinator 发送 shutdown_request
    2. Worker 收到请求，检查任务状态
    3. Worker 发送 shutdown_response
    4. Coordinator 根据响应决定是否关闭
    """

    def __init__(
        self,
        mailbox_path: Optional[str] = None,
        pending_tasks: list[str] = None,
    ):
        """
        初始化 Shutdown 协议

        Args:
            mailbox_path: 邮箱路径（用于持久化）
            pending_tasks: 当前未完成任务列表
        """
        self._mailbox_path = mailbox_path
        self._pending_tasks = pending_tasks or []
        self._shutdown_requested = False
        self._shutdown_approved = False
        self._current_request: Optional[ShutdownRequest] = None
        self._request_history: list[dict[str, Any]] = []

    # ==================== Request Side (Coordinator) ====================

    def create_request(
        self,
        agent_id: str,
        requester_id: str,
        reason: str,
        timeout_seconds: float = 30.0,
    ) -> ShutdownRequest:
        """
        创建 Shutdown 请求

        Args:
            agent_id: 目标 Agent ID
            requester_id: 发送请求的 Agent ID
            reason: 关闭原因
            timeout_seconds: 超时时间

        Returns:
            ShutdownRequest 实例
        """
        request = ShutdownRequest(
            agent_id=agent_id,
            requester_id=requester_id,
            reason=reason,
            timeout_seconds=timeout_seconds,
        )

        self._request_history.append({
            "action": "create_request",
            "request_id": request.request_id,
            "target": agent_id,
            "reason": reason,
            "timestamp": time.time(),
        })

        return request

    def send_request(
        self,
        request: ShutdownRequest,
        mailbox_path: Optional[str] = None,
    ) -> bool:
        """
        发送 Shutdown 请求到邮箱

        Args:
            request: Shutdown 请求
            mailbox_path: 邮箱路径（可选）

        Returns:
            是否成功发送
        """
        path = mailbox_path or self._mailbox_path
        if not path:
            # 无邮箱路径，模拟发送
            self._request_history.append({
                "action": "send_request",
                "request_id": request.request_id,
                "status": "sent_without_mailbox",
                "timestamp": time.time(),
            })
            return True

        mailbox_file = Path(path) / "shutdown_requests.json"

        try:
            # 读取现有请求
            requests = []
            if mailbox_file.exists():
                with open(mailbox_file, "r", encoding="utf-8") as f:
                    requests = json.load(f)

            # 添加新请求
            requests.append(request.to_dict())

            # 写入
            mailbox_file.parent.mkdir(parents=True, exist_ok=True)
            with open(mailbox_file, "w", encoding="utf-8") as f:
                json.dump(requests, f, ensure_ascii=False, indent=2)

            self._request_history.append({
                "action": "send_request",
                "request_id": request.request_id,
                "status": "sent",
                "mailbox": str(mailbox_file),
                "timestamp": time.time(),
            })

            return True

        except Exception as e:
            self._request_history.append({
                "action": "send_request",
                "request_id": request.request_id,
                "status": "failed",
                "error": str(e),
                "timestamp": time.time(),
            })
            return False

    def wait_for_response(
        self,
        request: ShutdownRequest,
        timeout_seconds: Optional[float] = None,
    ) -> Optional[ShutdownResponse]:
        """
        等待 Shutdown 响应

        Args:
            request: Shutdown 请求
            timeout_seconds: 超时时间

        Returns:
            ShutdownResponse 或 None（超时）
        """
        timeout = timeout_seconds or request.timeout_seconds
        start_time = time.time()
        path = self._mailbox_path

        if not path:
            # 模拟等待
            return None

        response_file = Path(path) / f"shutdown_response_{request.request_id}.json"

        while time.time() - start_time < timeout:
            if response_file.exists():
                try:
                    with open(response_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    return ShutdownResponse(**data)
                except Exception:
                    pass

            time.sleep(0.5)

        # 超时
        self._request_history.append({
            "action": "wait_for_response",
            "request_id": request.request_id,
            "status": "timeout",
            "timeout_seconds": timeout,
            "timestamp": time.time(),
        })

        return None

    # ==================== Response Side (Worker) ====================

    def check_for_request(
        self,
        mailbox_path: Optional[str] = None,
    ) -> Optional[ShutdownRequest]:
        """
        检查是否有 Shutdown 请求

        Args:
            mailbox_path: 邮箱路径（可选）

        Returns:
            ShutdownRequest 或 None
        """
        path = mailbox_path or self._mailbox_path
        if not path:
            return None

        mailbox_file = Path(path) / "shutdown_requests.json"

        if not mailbox_file.exists():
            return None

        try:
            with open(mailbox_file, "r", encoding="utf-8") as f:
                requests = json.load(f)

            if requests:
                # 取最新请求
                latest = requests[-1]
                return ShutdownRequest(**latest)

        except Exception:
            pass

        return None

    def has_pending_tasks(self) -> bool:
        """
        检查是否有未完成任务

        Returns:
            是否有未完成任务
        """
        return len(self._pending_tasks) > 0

    def get_pending_tasks(self) -> list[str]:
        """
        获取未完成任务列表

        Returns:
            未完成任务 ID 列表
        """
        return self._pending_tasks.copy()

    def set_pending_tasks(self, tasks: list[str]) -> None:
        """
        设置未完成任务列表

        Args:
            tasks: 任务 ID 列表
        """
        self._pending_tasks = tasks.copy()

    def handle_request(
        self,
        request: ShutdownRequest,
    ) -> ShutdownResponse:
        """
        处理 Shutdown 请求

        Args:
            request: Shutdown 请求

        Returns:
            ShutdownResponse
        """
        self._shutdown_requested = True
        self._current_request = request

        if self.has_pending_tasks():
            # 有未完成任务，拒绝关闭
            response = ShutdownResponse(
                request_id=request.request_id,
                agent_id=request.agent_id,
                approved=False,
                reason=f"有 {len(self._pending_tasks)} 个未完成任务",
                pending_tasks=self._pending_tasks,
            )
        else:
            # 无未完成任务，同意关闭
            response = ShutdownResponse(
                request_id=request.request_id,
                agent_id=request.agent_id,
                approved=True,
                reason="可以关闭",
            )
            self._shutdown_approved = True

        self._request_history.append({
            "action": "handle_request",
            "request_id": request.request_id,
            "approved": response.approved,
            "reason": response.reason,
            "timestamp": time.time(),
        })

        return response

    def send_response(
        self,
        response: ShutdownResponse,
        mailbox_path: Optional[str] = None,
    ) -> bool:
        """
        发送 Shutdown 响应

        Args:
            response: Shutdown 响应
            mailbox_path: 邮箱路径（可选）

        Returns:
            是否成功发送
        """
        path = mailbox_path or self._mailbox_path
        if not path:
            return True

        response_file = Path(path) / f"shutdown_response_{response.request_id}.json"

        try:
            response_file.parent.mkdir(parents=True, exist_ok=True)
            with open(response_file, "w", encoding="utf-8") as f:
                json.dump(response.to_dict(), f, ensure_ascii=False, indent=2)

            return True

        except Exception:
            return False

    # ==================== Utility Methods ====================

    def is_shutdown_requested(self) -> bool:
        """检查是否收到 Shutdown 请求"""
        return self._shutdown_requested

    def is_shutdown_approved(self) -> bool:
        """检查 Shutdown 是否已批准"""
        return self._shutdown_approved

    def get_current_request(self) -> Optional[ShutdownRequest]:
        """获取当前 Shutdown 请求"""
        return self._current_request

    def get_request_history(self) -> list[dict[str, Any]]:
        """获取请求历史"""
        return self._request_history.copy()

    def clear_request(self) -> None:
        """清除当前请求"""
        request_file = Path(self._mailbox_path or "") / "shutdown_requests.json"
        if request_file.exists() and self._current_request:
            try:
                with open(request_file, "r", encoding="utf-8") as f:
                    requests = json.load(f)

                # 移除已处理的请求
                requests = [
                    r for r in requests
                    if r.get("request_id") != self._current_request.request_id
                ]

                with open(request_file, "w", encoding="utf-8") as f:
                    json.dump(requests, f, ensure_ascii=False, indent=2)

            except Exception:
                pass

        self._shutdown_requested = False
        self._current_request = None


# ==================== Convenience Functions ====================

def create_shutdown_protocol(
    mailbox_path: Optional[str] = None,
    pending_tasks: list[str] = None,
) -> ShutdownProtocol:
    """
    创建 Shutdown 协议实例

    Args:
        mailbox_path: 邮箱路径
        pending_tasks: 未完成任务列表

    Returns:
        ShutdownProtocol 实例
    """
    return ShutdownProtocol(
        mailbox_path=mailbox_path,
        pending_tasks=pending_tasks or [],
    )


def request_shutdown(
    agent_id: str,
    requester_id: str,
    reason: str,
) -> ShutdownRequest:
    """
    创建 Shutdown 请求（便捷函数）

    Args:
        agent_id: 目标 Agent ID
        requester_id: 发送请求的 Agent ID
        reason: 关闭原因

    Returns:
        ShutdownRequest 实例
    """
    protocol = ShutdownProtocol()
    return protocol.create_request(
        agent_id=agent_id,
        requester_id=requester_id,
        reason=reason,
    )


# ==================== Export ====================

__all__ = [
    # Classes
    "ShutdownStatus",
    "ShutdownRequest",
    "ShutdownResponse",
    "ShutdownProtocol",
    # Functions
    "create_shutdown_protocol",
    "request_shutdown",
]