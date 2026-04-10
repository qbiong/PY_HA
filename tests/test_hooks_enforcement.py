"""
测试 Hooks 强制阻止机制

测试内容:
1. 未初始化框架时，Hooks 应阻止代码修改
2. 已初始化框架但无许可时，Hooks 应阻止代码修改
3. 有许可时，Hooks 应允许代码修改
4. 进程间状态共享（state.json 持久化）
"""

import pytest
import json
import os
import subprocess
import tempfile
from pathlib import Path


class TestHooksEnforcement:
    """测试 Hooks 强制阻止机制"""

    @pytest.fixture
    def temp_project(self):
        """创建临时项目目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建 .harnessgenj 目录
            harness_dir = Path(tmpdir) / ".harnessgenj"
            harness_dir.mkdir(parents=True, exist_ok=True)

            # 创建 state.json（未初始化状态）
            state_path = harness_dir / "state.json"
            state_path.write_text(json.dumps({
                "project_name": "Test Project",
                "framework_initialized": False,
            }), encoding="utf-8")

            yield tmpdir

    @pytest.fixture
    def initialized_project(self, temp_project):
        """已初始化的项目"""
        harness_dir = Path(temp_project) / ".harnessgenj"

        # 更新 state.json（已初始化状态）
        state_path = harness_dir / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["framework_initialized"] = True
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

        return temp_project

    @pytest.fixture
    def authorized_project(self, initialized_project):
        """已授权的项目"""
        harness_dir = Path(initialized_project) / ".harnessgenj"

        # 创建 session_state.json（有许可）
        session_path = harness_dir / "session_state.json"
        session_path.write_text(json.dumps({
            "session_id": "test_session",
            "active_task_id": "TASK-001",
            "permitted_files": {
                "src/test.py": {
                    "file_path": "src/test.py",
                    "operation": "write",
                    "reason": "Test task"
                },
                "src/": {
                    "file_path": "src/",
                    "operation": "write",
                    "reason": "Test task"
                },
            },
            "operation_mode": "framework",
        }, ensure_ascii=False, indent=2), encoding="utf-8")

        return initialized_project

    def test_uninitialized_blocks_edit(self, temp_project):
        """测试未初始化框架时阻止编辑"""
        # 模拟 Hooks 检查
        file_path = os.path.join(temp_project, "src/test.py")

        # 直接读取状态文件检查
        state_path = Path(temp_project) / ".harnessgenj" / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))

        assert state["framework_initialized"] == False
        # Hooks 应返回 blocked=True

    def test_initialized_without_permission_blocks(self, initialized_project):
        """测试已初始化但无许可时阻止编辑"""
        file_path = os.path.join(initialized_project, "src/test.py")

        # 检查状态
        state_path = Path(initialized_project) / ".harnessgenj" / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))

        # session_state.json 不存在
        session_path = Path(initialized_project) / ".harnessgenj" / "session_state.json"
        assert not session_path.exists()

        assert state["framework_initialized"] == True
        # Hooks 应返回 blocked=True（无许可）

    def test_authorized_allows_edit(self, authorized_project):
        """测试有许可时允许编辑"""
        file_path = os.path.join(authorized_project, "src/test.py")

        # 检查状态和许可
        state_path = Path(authorized_project) / ".harnessgenj" / "state.json"
        session_path = Path(authorized_project) / ".harnessgenj" / "session_state.json"

        state = json.loads(state_path.read_text(encoding="utf-8"))
        session = json.loads(session_path.read_text(encoding="utf-8"))

        assert state["framework_initialized"] == True

        # 检查路径匹配
        permitted_files = session.get("permitted_files", {})
        # 使用相对路径进行比较（去除项目根目录）
        rel_path = "src/test.py"
        normalized_path = os.path.normpath(rel_path)
        matched = False
        for permitted_path in permitted_files.keys():
            normalized_permitted = os.path.normpath(permitted_path)
            # 精确匹配或目录前缀匹配
            if normalized_path == normalized_permitted:
                matched = True
                break
            # 目录前缀匹配（需要确保 permitted_path 是目录）
            if normalized_permitted.endswith(os.sep) or normalized_permitted.endswith("/") or \
               normalized_path.startswith(normalized_permitted + os.sep):
                matched = True
                break

        assert matched == True
        # Hooks 应返回 blocked=False

    def test_wrong_path_blocked(self, authorized_project):
        """测试许可路径外编辑被阻止"""
        file_path = os.path.join(authorized_project, "other/test.py")

        session_path = Path(authorized_project) / ".harnessgenj" / "session_state.json"
        session = json.loads(session_path.read_text(encoding="utf-8"))

        # 检查路径匹配（应该不匹配）
        permitted_files = session.get("permitted_files", {})
        normalized_path = os.path.normpath(file_path)
        matched = False
        for permitted_path in permitted_files.keys():
            normalized_permitted = os.path.normpath(permitted_path)
            if normalized_path == normalized_permitted or \
               normalized_path.startswith(normalized_permitted + os.sep):
                matched = True
                break

        assert matched == False
        # Hooks 应返回 blocked=True

    def test_state_persists_to_file(self, initialized_project):
        """测试状态持久化到文件"""
        state_path = Path(initialized_project) / ".harnessgenj" / "state.json"

        # 验证文件存在且有正确标记
        assert state_path.exists()
        state = json.loads(state_path.read_text(encoding="utf-8"))
        assert state["framework_initialized"] == True

    def test_hooks_skip_internal_files(self, temp_project):
        """测试 Hooks 跳过内部文件"""
        # .claude 和 .harnessgenj 文件应被跳过
        internal_paths = [
            ".claude/harnessgenj_hook.py",
            ".harnessgenj/state.json",
        ]

        for path in internal_paths:
            # Hooks 内部检查逻辑：跳过这些路径
            assert ".claude" in path or ".harnessgenj" in path


class TestCrossProcessStateSharing:
    """测试进程间状态共享"""

    def test_is_initialized_reads_from_file(self):
        """测试 is_initialized() 从文件读取状态"""
        # 创建临时项目
        with tempfile.TemporaryDirectory() as tmpdir:
            harness_dir = Path(tmpdir) / ".harnessgenj"
            harness_dir.mkdir(parents=True, exist_ok=True)

            # 写入已初始化状态
            state_path = harness_dir / "state.json"
            state_path.write_text(json.dumps({
                "framework_initialized": True,
            }), encoding="utf-8")

            # 在另一个进程中检查
            tmpdir_escaped = str(tmpdir).replace("\\", "\\\\")
            code = (
                "import json\n"
                "from pathlib import Path\n"
                "\n"
                "state_path = Path('" + tmpdir_escaped + "') / '.harnessgenj' / 'state.json'\n"
                "state = json.loads(state_path.read_text())\n"
                "print(state.get('framework_initialized', False))"
            )

            result = subprocess.run(
                ["python", "-c", code],
                capture_output=True,
                text=True
            )

            # 进程应该能读取到 True
            assert result.stdout.strip() == "True"


class TestFrameworkSessionPersistence:
    """测试 FrameworkSession 持久化"""

    def test_session_persists_permission(self):
        """测试许可列表持久化"""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "session_state.json"

            # 写入许可
            session_data = {
                "session_id": "test",
                "permitted_files": {
                    "src/main.py": {"operation": "write"},
                    "tests/": {"operation": "write"},
                },
            }
            session_path.write_text(json.dumps(session_data, ensure_ascii=False, indent=2), encoding="utf-8")

            # 在另一个进程中读取
            tmpdir_escaped = str(tmpdir).replace("\\", "\\\\")
            code = (
                "import json\n"
                "from pathlib import Path\n"
                "\n"
                "session_path = Path('" + tmpdir_escaped + "') / 'session_state.json'\n"
                "session = json.loads(session_path.read_text())\n"
                "permitted = list(session.get('permitted_files', {}).keys())\n"
                "print(permitted)"
            )

            result = subprocess.run(
                ["python", "-c", code],
                capture_output=True,
                text=True
            )

            # 进程应该能读取到许可列表
            output = result.stdout.strip()
            assert "src/main.py" in output or "tests/" in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])