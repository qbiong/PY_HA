"""
测试 Shutdown Protocol 关闭审批协议

测试内容:
1. ShutdownRequest 创建和发送
2. ShutdownResponse 响应处理
3. 未完成任务拒绝关闭
4. 完成任务同意关闭
5. 超时处理
"""

import pytest
import tempfile
import json
from pathlib import Path

from harnessgenj.workflow.shutdown_protocol import (
    ShutdownProtocol,
    ShutdownRequest,
    ShutdownResponse,
    ShutdownStatus,
    create_shutdown_protocol,
    request_shutdown,
)


class TestShutdownRequest:
    """测试 ShutdownRequest"""

    def test_create_shutdown_request(self):
        """测试创建 Shutdown 请求"""
        request = request_shutdown(
            agent_id="worker_1",
            requester_id="coordinator",
            reason="任务完成，关闭 Worker",
        )

        assert request.agent_id == "worker_1"
        assert request.requester_id == "coordinator"
        assert request.reason == "任务完成，关闭 Worker"
        assert request.timeout_seconds == 30.0

    def test_shutdown_request_to_dict(self):
        """测试请求转换为字典"""
        request = ShutdownRequest(
            agent_id="worker_1",
            requester_id="coordinator",
            reason="测试关闭",
        )

        data = request.to_dict()

        assert data["type"] == "shutdown_request"
        assert data["agent_id"] == "worker_1"
        assert data["requester_id"] == "coordinator"
        assert data["reason"] == "测试关闭"

    def test_shutdown_request_with_custom_timeout(self):
        """测试自定义超时"""
        request = ShutdownRequest(
            agent_id="worker_1",
            requester_id="coordinator",
            reason="关闭",
            timeout_seconds=60.0,
        )

        assert request.timeout_seconds == 60.0


class TestShutdownResponse:
    """测试 ShutdownResponse"""

    def test_create_approved_response(self):
        """测试创建批准响应"""
        response = ShutdownResponse(
            request_id="shutdown-123",
            agent_id="worker_1",
            approved=True,
            reason="可以关闭",
        )

        assert response.approved == True
        assert response.reason == "可以关闭"
        assert response.pending_tasks == []

    def test_create_rejected_response(self):
        """测试创建拒绝响应"""
        response = ShutdownResponse(
            request_id="shutdown-123",
            agent_id="worker_1",
            approved=False,
            reason="有未完成任务",
            pending_tasks=["TASK-001", "TASK-002"],
        )

        assert response.approved == False
        assert response.reason == "有未完成任务"
        assert len(response.pending_tasks) == 2

    def test_response_to_dict(self):
        """测试响应转换为字典"""
        response = ShutdownResponse(
            request_id="shutdown-123",
            agent_id="worker_1",
            approved=True,
            reason="同意关闭",
        )

        data = response.to_dict()

        assert data["type"] == "shutdown_response"
        assert data["approved"] == True
        assert data["reason"] == "同意关闭"


class TestShutdownProtocolBasics:
    """测试 ShutdownProtocol 基础功能"""

    def test_create_protocol(self):
        """测试创建协议实例"""
        protocol = create_shutdown_protocol()

        assert protocol.is_shutdown_requested() == False
        assert protocol.is_shutdown_approved() == False
        assert protocol.get_current_request() is None

    def test_create_protocol_with_pending_tasks(self):
        """测试带未完成任务的协议"""
        protocol = create_shutdown_protocol(
            pending_tasks=["TASK-001", "TASK-002"],
        )

        assert protocol.has_pending_tasks() == True
        assert len(protocol.get_pending_tasks()) == 2

    def test_set_pending_tasks(self):
        """测试设置未完成任务"""
        protocol = create_shutdown_protocol()
        protocol.set_pending_tasks(["TASK-003"])

        assert protocol.has_pending_tasks() == True
        assert protocol.get_pending_tasks() == ["TASK-003"]


class TestShutdownRequestFlow:
    """测试 Shutdown 请求流程"""

    def test_create_and_send_request(self):
        """测试创建并发送请求"""
        protocol = create_shutdown_protocol()

        request = protocol.create_request(
            agent_id="worker_1",
            requester_id="coordinator",
            reason="关闭测试",
        )

        assert request.agent_id == "worker_1"

        # 发送请求（无邮箱）
        result = protocol.send_request(request)
        assert result == True

    def test_handle_request_without_pending_tasks(self):
        """测试处理请求（无未完成任务）"""
        protocol = create_shutdown_protocol()

        request = ShutdownRequest(
            agent_id="worker_1",
            requester_id="coordinator",
            reason="关闭",
        )

        response = protocol.handle_request(request)

        assert response.approved == True
        assert response.reason == "可以关闭"
        assert protocol.is_shutdown_approved() == True

    def test_handle_request_with_pending_tasks(self):
        """测试处理请求（有未完成任务）"""
        protocol = create_shutdown_protocol(
            pending_tasks=["TASK-001", "TASK-002"],
        )

        request = ShutdownRequest(
            agent_id="worker_1",
            requester_id="coordinator",
            reason="关闭",
        )

        response = protocol.handle_request(request)

        assert response.approved == False
        assert "未完成任务" in response.reason
        assert len(response.pending_tasks) == 2
        assert protocol.is_shutdown_approved() == False


class TestShutdownProtocolWithMailbox:
    """测试带邮箱的 Shutdown 协议"""

    def test_send_request_to_mailbox(self):
        """测试发送请求到邮箱"""
        with tempfile.TemporaryDirectory() as tmpdir:
            protocol = create_shutdown_protocol(mailbox_path=tmpdir)

            request = protocol.create_request(
                agent_id="worker_1",
                requester_id="coordinator",
                reason="关闭",
            )

            result = protocol.send_request(request)
            assert result == True

            # 验证邮箱文件
            mailbox_file = Path(tmpdir) / "shutdown_requests.json"
            assert mailbox_file.exists()

            with open(mailbox_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            assert len(data) == 1
            assert data[0]["agent_id"] == "worker_1"

    def test_send_response_to_mailbox(self):
        """测试发送响应到邮箱"""
        with tempfile.TemporaryDirectory() as tmpdir:
            protocol = create_shutdown_protocol(mailbox_path=tmpdir)

            request = ShutdownRequest(
                agent_id="worker_1",
                requester_id="coordinator",
                reason="关闭",
            )

            response = protocol.handle_request(request)
            result = protocol.send_response(response)

            assert result == True

            # 验证响应文件
            response_file = Path(tmpdir) / f"shutdown_response_{request.request_id}.json"
            assert response_file.exists()

    def test_check_for_request(self):
        """测试检查邮箱中的请求"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 写入请求
            mailbox_file = Path(tmpdir) / "shutdown_requests.json"
            request_data = {
                "type": "shutdown_request",
                "request_id": "shutdown-test-123",
                "agent_id": "worker_1",
                "requester_id": "coordinator",
                "reason": "关闭",
                "timeout_seconds": 30.0,
                "created_at": 1700000000.0,
            }

            mailbox_file.parent.mkdir(parents=True, exist_ok=True)
            with open(mailbox_file, "w", encoding="utf-8") as f:
                json.dump([request_data], f)

            # 检查请求
            protocol = create_shutdown_protocol(mailbox_path=tmpdir)
            request = protocol.check_for_request()

            assert request is not None
            assert request.agent_id == "worker_1"


class TestShutdownProtocolHistory:
    """测试 Shutdown 协议历史记录"""

    def test_request_history(self):
        """测试请求历史记录"""
        protocol = create_shutdown_protocol()

        request = protocol.create_request(
            agent_id="worker_1",
            requester_id="coordinator",
            reason="关闭",
        )

        protocol.handle_request(request)

        history = protocol.get_request_history()

        assert len(history) >= 2
        # 有创建请求和处理的记录

    def test_clear_request(self):
        """测试清除请求"""
        protocol = create_shutdown_protocol()

        request = ShutdownRequest(
            agent_id="worker_1",
            requester_id="coordinator",
            reason="关闭",
        )

        protocol.handle_request(request)
        assert protocol.is_shutdown_requested() == True

        protocol.clear_request()
        assert protocol.is_shutdown_requested() == False
        assert protocol.get_current_request() is None


class TestShutdownStatus:
    """测试 ShutdownStatus"""

    def test_shutdown_status_values(self):
        """测试状态值"""
        assert ShutdownStatus.PENDING.value == "pending"
        assert ShutdownStatus.APPROVED.value == "approved"
        assert ShutdownStatus.REJECTED.value == "rejected"
        assert ShutdownStatus.TIMEOUT.value == "timeout"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])