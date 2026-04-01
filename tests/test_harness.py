"""
Tests for Harness Layer
"""

import pytest

from py_ha.harness import (
    PlanningTool,
    TodoList,
    SubagentManager,
    SubagentConfig,
    VirtualFS,
    LocalStorage,
    CodeSandbox,
    HumanLoop,
)


class TestPlanningTool:
    """测试规划工具"""

    def test_create_plan(self) -> None:
        """创建规划"""
        planning = PlanningTool()
        todo = planning.create_plan("test-plan")

        assert planning.get_plan("test-plan") is not None

    def test_add_todos(self) -> None:
        """添加Todo"""
        todo = TodoList()
        item = todo.add("Task 1", priority=5)

        assert item.content == "Task 1"
        assert item.priority == 5
        assert item.status == "pending"

    def test_update_status(self) -> None:
        """更新状态"""
        todo = TodoList()
        item = todo.add("Task 1")

        result = todo.update_status(item.id, "completed")
        assert result is True
        assert todo.get(item.id).status == "completed"

    def test_get_next_ready(self) -> None:
        """获取下一个可执行项"""
        todo = TodoList()
        item1 = todo.add("Task 1")
        item2 = todo.add("Task 2", dependencies=[item1.id])

        # Task 1 可以执行
        next_item = todo.get_next_ready()
        assert next_item.id == item1.id

        # 完成 Task 1
        todo.update_status(item1.id, "completed")

        # Task 2 现在可以执行
        next_item = todo.get_next_ready()
        assert next_item.id == item2.id


class TestSubagentManager:
    """测试子代理管理器"""

    def test_register_subagent(self) -> None:
        """注册子代理"""
        manager = SubagentManager()
        config = SubagentConfig(
            name="research-agent",
            description="Research subagent",
        )
        manager.register(config)

        assert manager.get_subagent("research-agent") is not None
        assert "research-agent" in manager.list_subagents()

    @pytest.mark.asyncio
    async def test_delegate_task(self) -> None:
        """委托任务"""
        manager = SubagentManager()

        task = await manager.delegate("Research AI trends")

        assert task.status == "completed"
        assert task.result is not None


class TestVirtualFS:
    """测试虚拟文件系统"""

    @pytest.mark.asyncio
    async def test_write_and_read(self) -> None:
        """写入和读取"""
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorage(Path(tmpdir))
            fs = VirtualFS(storage)

            # 写入文件
            await fs.write("test.txt", "Hello World")

            # 读取文件
            content = await fs.read("test.txt")
            assert content is not None
            assert content.content == "Hello World"

    @pytest.mark.asyncio
    async def test_exists(self) -> None:
        """检查文件存在"""
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorage(Path(tmpdir))
            fs = VirtualFS(storage)

            await fs.write("test.txt", "content")

            assert await fs.exists("test.txt") is True
            assert await fs.exists("nonexistent.txt") is False


class TestCodeSandbox:
    """测试代码沙箱"""

    @pytest.mark.asyncio
    async def test_execute_simple_code(self) -> None:
        """执行简单代码"""
        sandbox = CodeSandbox()
        code = "result = 1 + 1"

        result = await sandbox.execute(code)

        assert result.success is True

    def test_validate_dangerous_code(self) -> None:
        """验证危险代码"""
        sandbox = CodeSandbox()
        dangerous_code = "import os; os.system('rm -rf /')"

        issues = sandbox.validate_code(dangerous_code)

        assert len(issues) > 0


class TestHumanLoop:
    """测试人机交互"""

    @pytest.mark.asyncio
    async def test_request_approval(self) -> None:
        """请求审批"""
        human_loop = HumanLoop()

        request = await human_loop.request_approval("Delete file?")

        assert request.action == "Delete file?"
        assert request.status.value in ["pending", "approved"]

    def test_respond_approval(self) -> None:
        """响应审批"""
        human_loop = HumanLoop()

        # 创建请求
        import asyncio
        request = asyncio.run(human_loop.request_approval("Action?"))

        # 响应审批
        response = human_loop.respond_approval(request.request_id, approved=True)

        assert response.approved is True
        assert human_loop.get_request(request.request_id).status.value == "approved"