"""
Hooks Common - 公共 Hook 函数模板

此模块提供生成 Claude Code Hook 脚本所需的公共函数模板。
生成的 Hook 脚本是独立运行的，不依赖 HarnessGenJ 框架。

使用场景：
- hooks_auto_setup.py: 生成完整版 Hook 脚本
- cli.py: 生成简化版 Hook 脚本（可选）

函数模板特点：
- 独立实现，不依赖框架导入
- 从环境变量和命令行参数获取信息
- 自包含异常处理
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Any


# ==================== Hook 脚本模板函数 ====================
# 以下函数将被嵌入到生成的 Hook 脚本中

def log_exception(e: Exception, context: str = "", level: int = 30) -> None:
    """
    记录异常信息到 stderr（独立实现，不依赖框架）

    Args:
        e: 异常对象
        context: 上下文描述
        level: 日志级别 (30=WARNING, 40=ERROR)
    """
    level_str = "ERROR" if level >= 40 else "WARNING" if level >= 30 else "INFO"
    print(f"[HarnessGenJ {level_str}] [{context}] {type(e).__name__}: {e}", file=sys.stderr)


def get_project_root() -> Path:
    """
    获取项目根目录

    Returns:
        项目根目录路径
    """
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if project_dir:
        return Path(project_dir)
    script_path = Path(__file__).resolve()
    return script_path.parent.parent


def get_tool_input() -> dict:
    """
    获取工具输入参数

    从环境变量 TOOL_INPUT 或命令行参数获取。

    Returns:
        工具输入参数字典
    """
    # 尝试从环境变量获取
    tool_input = os.environ.get("TOOL_INPUT", "{}")
    try:
        return json.loads(tool_input)
    except json.JSONDecodeError:
        pass

    # 尝试从命令行参数获取
    if len(sys.argv) > 2:
        try:
            return json.loads(sys.argv[2])
        except json.JSONDecodeError:
            pass

    return {}


def append_to_development_log(content: str, context: str = "Hooks") -> bool:
    """
    追加内容到开发日志

    Args:
        content: 要追加的内容
        context: 上下文标签

    Returns:
        是否成功写入
    """
    try:
        workspace = get_project_root() / ".harnessgenj"
        dev_log_path = workspace / "documents" / "development.md"
        dev_log_path.parent.mkdir(parents=True, exist_ok=True)

        if not dev_log_path.exists():
            dev_log_path.write_text(
                "# 开发日志\n\n此文件由 HarnessGenJ Hooks 自动维护。\n\n---\n",
                encoding="utf-8"
            )

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"\n## [{timestamp}] [{context}]\n\n{content}\n\n---\n"
        with open(dev_log_path, "a", encoding="utf-8") as f:
            f.write(entry)
        return True
    except Exception as e:
        log_exception(e, context="write_to_development_log", level=30)
        return False


def handle_post_tool_use() -> int:
    """
    处理 PostToolUse 事件

    自动记录文件操作到开发日志。

    Returns:
        退出码 (0=成功)
    """
    tool_input = get_tool_input()
    tool_name = os.environ.get("TOOL_NAME", "")

    file_path = tool_input.get("file_path", tool_input.get("path", ""))
    content = tool_input.get("content", tool_input.get("new_string", ""))

    if not file_path:
        return 0

    action = "创建" if tool_name == "Write" else "修改"
    record_content = f"{action}文件: `{file_path}`"

    # 记录代码文件的行数
    if file_path.endswith(('.java', '.kt', '.py', '.js', '.ts', '.tsx', '.go', '.rs')):
        if content:
            lines = content.count('\n') + 1
            record_content += f" ({lines} 行)"

    append_to_development_log(record_content, context=f"PostToolUse:{tool_name}")
    return 0


def handle_pre_tool_use_security() -> int:
    """
    处理 PreToolUse 安全检查

    检测敏感信息泄露风险。

    Returns:
        退出码 (0=通过, 非零=警告)
    """
    content = ""
    if len(sys.argv) > 2:
        content = sys.argv[2]
    if not content:
        tool_input = get_tool_input()
        content = tool_input.get("content", tool_input.get("new_string", ""))

    if not content:
        return 0

    # 高风险关键词
    high_risk_patterns = [
        "password", "secret", "api_key", "token",
        "credential", "private_key", "access_key"
    ]
    warnings = []
    content_lower = content.lower()

    for pattern in high_risk_patterns:
        if pattern in content_lower and ("=" in content or ":" in content):
            warnings.append(f"可能包含敏感信息: {pattern}")

    if warnings:
        print(f"[HarnessGenJ Security Warning] {', '.join(warnings)}", file=sys.stderr)
        return 0  # 仅警告，不阻止

    return 0


def trigger_adversarial_review(file_path: str, content: str) -> dict[str, Any]:
    """
    触发对抗性审查（记录到积分系统并通过事件系统通知）

    Args:
        file_path: 文件路径
        content: 文件内容

    Returns:
        审查结果
    """
    result = {
        "file": file_path,
        "review_triggered": False,
        "issues": [],
    }

    # 检查是否是代码文件
    code_extensions = ['.py', '.java', '.kt', '.js', '.ts', '.tsx', '.go', '.rs']
    if not any(file_path.endswith(ext) for ext in code_extensions):
        return result

    # 记录到开发日志
    lines = content.count('\n') + 1 if content else 0
    log_content = f"Code file changed: `{file_path}` ({lines} lines)"
    append_to_development_log(log_content, context="AdversarialTrigger")

    # 写入事件文件，供 TriggerManager 消费
    try:
        workspace = get_project_root() / ".harnessgenj"
        events_dir = workspace / "events"
        events_dir.mkdir(parents=True, exist_ok=True)

        event_id = f"event_{datetime.now().strftime('%Y%m%d_%H%M%S')}_on_code_change"
        event_file = events_dir / f"{event_id}.json"

        event_data = {
            "event_type": "on_code_change",
            "timestamp": datetime.now().isoformat(),
            "file_path": file_path,
            "content_preview": content[:500] if content else "",
            "lines": lines,
        }

        with open(event_file, "w", encoding="utf-8") as f:
            json.dump(event_data, f, ensure_ascii=False, indent=2)

        result["review_triggered"] = True
        result["event_file"] = str(event_file)
    except Exception as e:
        log_exception(e, context="trigger_adversarial_review", level=30)

    return result


# ==================== 模板生成函数 ====================

def get_hook_functions_template() -> str:
    """
    获取 Hook 函数模板字符串

    用于生成独立运行的 Hook 脚本。

    Returns:
        Hook 函数模板（Python 代码字符串）
    """
    return '''
def log_exception(e: Exception, context: str = "", level: int = 30) -> None:
    """记录异常信息到 stderr（独立实现，不依赖框架）"""
    level_str = "ERROR" if level >= 40 else "WARNING" if level >= 30 else "INFO"
    print(f"[HarnessGenJ {level_str}] [{context}] {type(e).__name__}: {e}", file=sys.stderr)


def get_project_root() -> Path:
    """获取项目根目录"""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if project_dir:
        return Path(project_dir)
    script_path = Path(__file__).resolve()
    return script_path.parent.parent


def get_tool_input() -> dict:
    """获取工具输入参数"""
    tool_input = os.environ.get("TOOL_INPUT", "{}")
    try:
        return json.loads(tool_input)
    except json.JSONDecodeError:
        pass
    if len(sys.argv) > 2:
        try:
            return json.loads(sys.argv[2])
        except json.JSONDecodeError:
            pass
    return {}


def append_to_development_log(content: str, context: str = "Hooks") -> bool:
    """追加内容到开发日志"""
    try:
        workspace = get_project_root() / ".harnessgenj"
        dev_log_path = workspace / "documents" / "development.md"
        dev_log_path.parent.mkdir(parents=True, exist_ok=True)

        if not dev_log_path.exists():
            dev_log_path.write_text(
                "# 开发日志\\n\\n此文件由 HarnessGenJ Hooks 自动维护。\\n\\n---\\n",
                encoding="utf-8"
            )

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"\\n## [{timestamp}] [{context}]\\n\\n{content}\\n\\n---\\n"
        with open(dev_log_path, "a", encoding="utf-8") as f:
            f.write(entry)
        return True
    except Exception as e:
        log_exception(e, context="write_to_development_log", level=30)
        return False


def handle_post_tool_use() -> int:
    """处理 PostToolUse 事件"""
    tool_input = get_tool_input()
    tool_name = os.environ.get("TOOL_NAME", "")

    file_path = tool_input.get("file_path", tool_input.get("path", ""))
    content = tool_input.get("content", tool_input.get("new_string", ""))

    if not file_path:
        return 0

    action = "创建" if tool_name == "Write" else "修改"
    record_content = f"{action}文件: `{file_path}`"

    if file_path.endswith(('.java', '.kt', '.py', '.js', '.ts', '.tsx', '.go', '.rs')):
        if content:
            lines = content.count('\\n') + 1
            record_content += f" ({lines} 行)"

    append_to_development_log(record_content, context=f"PostToolUse:{tool_name}")
    return 0


def handle_pre_tool_use_security() -> int:
    """处理 PreToolUse 安全检查"""
    content = ""
    if len(sys.argv) > 2:
        content = sys.argv[2]
    if not content:
        tool_input = get_tool_input()
        content = tool_input.get("content", tool_input.get("new_string", ""))

    if not content:
        return 0

    high_risk_patterns = ["password", "secret", "api_key", "token", "credential", "private_key"]
    warnings = []
    content_lower = content.lower()

    for pattern in high_risk_patterns:
        if pattern in content_lower and ("=" in content or ":" in content):
            warnings.append(f"可能包含敏感信息: {pattern}")

    if warnings:
        print(f"[HarnessGenJ Security Warning] {', '.join(warnings)}", file=sys.stderr)

    return 0
'''


def get_adversarial_trigger_template() -> str:
    """
    获取对抗审查触发函数模板

    Returns:
        对抗审查函数模板字符串
    """
    return '''
def trigger_adversarial_review(file_path: str, content: str) -> dict:
    """触发对抗性审查"""
    result = {"file": file_path, "review_triggered": False, "issues": []}

    code_extensions = ['.py', '.java', '.kt', '.js', '.ts', '.tsx', '.go', '.rs']
    if not any(file_path.endswith(ext) for ext in code_extensions):
        return result

    lines = content.count('\\n') + 1 if content else 0
    log_content = f"Code file changed: `{file_path}` ({lines} lines)"
    append_to_development_log(log_content, context="AdversarialTrigger")

    try:
        workspace = get_project_root() / ".harnessgenj"
        events_dir = workspace / "events"
        events_dir.mkdir(parents=True, exist_ok=True)

        from datetime import datetime
        event_id = f"event_{datetime.now().strftime('%Y%m%d_%H%M%S')}_on_code_change"
        event_file = events_dir / f"{event_id}.json"

        event_data = {
            "event_type": "on_code_change",
            "timestamp": datetime.now().isoformat(),
            "file_path": file_path,
            "content_preview": content[:500] if content else "",
            "lines": lines,
        }

        with open(event_file, "w", encoding="utf-8") as f:
            json.dump(event_data, f, ensure_ascii=False, indent=2)

        result["review_triggered"] = True
        result["event_file"] = str(event_file)
    except Exception as e:
        log_exception(e, context="trigger_adversarial_review", level=30)

    return result
'''