# HGJ框架优化方案文档

> 生成日期: 2026-04-06
> 更新日期: 2026-04-06
> 版本: v1.2

---

## 第零部分：已完成优化

### v1.2.1 关键修复与测试增强 ✅

#### 1. 触发链修复 ✅

**问题**: `HybridIntegration.trigger_on_write_complete()` 在 BUILTIN 模式下未调用 `TriggerManager`，导致触发链断裂。

**解决方案**:
- 添加 `trigger_manager` 参数到 `HybridIntegration.__init__()`
- 在 BUILTIN 模式下调用 `TriggerManager.trigger(TriggerEvent.ON_WRITE_COMPLETE, ...)`
- 确保 `develop()` → `HybridIntegration` → `TriggerManager` → 角色执行 → `ScoreManager` 数据流完整

**代码变更**:
```python
# hybrid_integration.py
def __init__(
    self,
    config: HybridConfig,
    hooks_integration: HooksIntegration,
    trigger_manager: TriggerManager | None = None,  # 新增
    ...
) -> None:
    self._trigger_manager = trigger_manager

def trigger_on_write_complete(self, ...):
    elif self._active_mode == IntegrationMode.BUILTIN:
        # 新增：调用 TriggerManager
        if self._trigger_manager:
            self._trigger_manager.trigger(
                TriggerEvent.ON_WRITE_COMPLETE,
                {"file_path": file_path, "content": content, "metadata": metadata or {}},
            )
```

#### 2. 初始化顺序修正 ✅

**问题**: `engine.py` 中 `hybrid_integration` 在 `trigger_manager` 之前创建，导致依赖注入失败。

**解决方案**:
- `trigger_manager` 在 `hybrid_integration` 之前创建
- 通过依赖注入传递给 `create_hybrid_integration()`

**代码变更**:
```python
# engine.py
# 第232-248行
self._trigger_manager = create_trigger_manager(self)  # 先创建
self._hybrid_integration = create_hybrid_integration(
    workspace=workspace,
    trigger_manager=self._trigger_manager,  # 传入
    ...
)
```

#### 3. 核心模块全面测试 ✅

| 测试文件 | 测试数量 | 覆盖内容 |
|---------|---------|----------|
| `tests/harness/test_hybrid_integration.py` | 20 | 模式切换、事件触发、自动降级、回调机制 |
| `tests/workflow/test_task_state.py` | 32 | 状态转换、无效转换处理、钩子触发、便捷方法 |
| `tests/integration/test_full_data_flow.py` | 15 | 完整数据流、模块职责边界、跨会话持久化 |

**测试验证结果**:
- 755 个测试全部通过
- 新增 67 个测试用例
- 覆盖触发链、状态机重构、数据流一致性

### v1.2.0 架构重构优化

#### 1. HybridIntegration 职责简化 ✅

**问题**: `HybridIntegration` 中存在直接对抗触发和积分更新逻辑，与 `TriggerManager` 职责重叠。

**解决方案**:
- 移除 `trigger_on_write_complete()` 中的直接对抗触发逻辑
- 移除 `trigger_on_task_complete()` 中的直接积分更新
- 移除 `trigger_on_issue_found()` 中的 `ScoreManager.on_issue_found()` 调用
- 删除 `_trigger_adversarial_for_file()` 方法

**结果**: `HybridIntegration` 现在专注于事件记录和模式切换（Hooks/Builtin/MCP）。

#### 2. TaskStateMachine 职责明确化 ✅

**问题**: `TaskStateMachine` 存储 `description` 和 `metadata`，与 `MemoryManager` 职责重叠。

**解决方案**:
- `TaskInfo` 移除 `description` 字段
- `TaskInfo` 移除 `metadata` 字段
- `create_task()` 移除 `metadata` 和 `description` 参数
- 任务详情统一存储在 `MemoryManager`

**结果**: `TaskStateMachine` 只管理状态流转，`MemoryManager` 是任务数据的唯一数据源。

#### 3. engine.py develop() 触发路径简化 ✅

**问题**: `develop()` 方法末尾存在重复的 `TriggerManager.trigger()` 调用。

**解决方案**:
- 移除行 952-955 的重复触发代码
- 事件触发统一通过 `HybridIntegration.trigger_on_write_complete()`

**结果**: 消除双重触发问题，事件分发路径清晰。

#### 4. 数据流清晰化 ✅

| 数据类型 | 存储位置 |
|---------|----------|
| 任务详情 | MemoryManager |
| 任务状态 | TaskStateMachine |
| 事件记录 | HybridIntegration |
| 对抗审查结果 | TriggerManager |
| 积分记录 | ScoreManager |

#### 5. 测试验证 ✅

- 所有 690 个测试通过（基础验证）
- 验证：触发路径简化、状态机重构、数据流一致性

---

## 第一部分：已修改内容

### 1. Hooks脚本修复

**文件**: `.claude/harnessgenj_hook.py`

#### 1.1 类型导入修复

```python
# 修改前
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# 修改后
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Any  # 新增
```

**原因**: 第69行 `dict[str, Any]` 使用了 `Any` 类型但未导入。

---

#### 1.2 输入获取函数重构

**新增 `get_tool_input()` 函数**:

```python
def get_tool_input() -> dict:
    """获取工具输入参数 - 多来源兼容"""
    result = {}

    # 1. 尝试从 stdin 读取（最可靠）
    if not sys.stdin.isatty():
        try:
            stdin_content = sys.stdin.read().strip()
            if stdin_content:
                result = json.loads(stdin_content)
                if result:
                    return result
        except (json.JSONDecodeError, Exception):
            pass

    # 2. 尝试从 TOOL_INPUT 环境变量获取
    tool_input = os.environ.get("TOOL_INPUT", "")
    if tool_input:
        try:
            return json.loads(tool_input)
        except json.JSONDecodeError:
            pass

    # 3. 尝试从 TOOL_INPUT_JSON 环境变量获取
    tool_input_json = os.environ.get("TOOL_INPUT_JSON", "")
    if tool_input_json:
        try:
            return json.loads(tool_input_json)
        except json.JSONDecodeError:
            pass

    # 4. 尝试从命令行参数获取
    if len(sys.argv) > 2:
        arg = sys.argv[2]
        try:
            return json.loads(arg)
        except json.JSONDecodeError:
            if arg.startswith("/") or arg.startswith("\\") or ":" in arg:
                return {"file_path": arg}
            return {"content": arg}

    return result
```

**新增 `get_tool_content()` 函数**:

```python
def get_tool_content() -> str:
    """获取工具内容 - 专门用于 PreToolUse 安全检查"""
    # 1. 从 stdin 读取
    if not sys.stdin.isatty():
        try:
            return sys.stdin.read()
        except Exception:
            pass

    # 2. 从环境变量获取
    content = os.environ.get("TOOL_INPUT_CONTENT", "")
    if content:
        return content

    # 3. 从 TOOL_INPUT 解析
    tool_input = get_tool_input()
    return tool_input.get("content", tool_input.get("new_string", ""))
```

---

#### 1.3 处理函数增强调试输出

**`handle_post_tool_use()` 修改**:

```python
def handle_post_tool_use() -> int:
    tool_input = get_tool_input()
    tool_name = os.environ.get("TOOL_NAME", "")

    file_path = tool_input.get("file_path", tool_input.get("path", ""))
    content = tool_input.get("content", tool_input.get("new_string", ""))

    # 新增调试输出
    print(f"[HarnessGenJ] PostToolUse 触发: tool={tool_name}, file={file_path}", file=sys.stderr)

    if not file_path:
        print("[HarnessGenJ] PostToolUse: 未获取到文件路径", file=sys.stderr)
        return 0
    
    # ... 其余逻辑不变
```

**`handle_pre_tool_use_security()` 修改**:

```python
def handle_pre_tool_use_security() -> int:
    tool_input = get_tool_input()
    tool_name = os.environ.get("TOOL_NAME", "")

    file_path = tool_input.get("file_path", tool_input.get("path", ""))
    content = get_tool_content()  # 使用新函数

    # 新增调试输出
    if not content:
        print("[HarnessGenJ] PreToolUse: 未获取到内容", file=sys.stderr)
        return 0
    
    # ... 其余逻辑不变
```

---

### 2. settings.json 配置简化

**文件**: `.claude/settings.json`

```json
{
  "permissions": {
    "allow": [...],
    "additionalDirectories": [...]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/harnessgenj_hook.py --security",
            "timeout": 5000
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/harnessgenj_hook.py --post",
            "timeout": 5000
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/harnessgenj_hook.py --flush-state"
          }
        ]
      }
    ]
  }
}
```

**修改项**:

| 项目 | 修改前 | 修改后 |
|------|--------|--------|
| 命令路径 | `python "$CLAUDE_PROJECT_DIR/.claude/harnessgenj_hook.py"` | `python .claude/harnessgenj_hook.py` |
| 参数传递 | `--security "$TOOL_INPUT_CONTENT"` | `--security` (通过 stdin/环境变量传递) |
| 超时设置 | 无 | `"timeout": 5000` |

---

## 第二部分：新需求文档

### 需求1: Hooks输入传递机制优化

**问题描述**:
Claude Code 的 hooks 机制未正确传递工具输入参数，导致 `TOOL_INPUT`、`TOOL_INPUT_CONTENT` 等环境变量为空。

**需求规格**:

```python
# 方案A: 临时文件传递（推荐）
# Claude Code 调用 hooks 前，将工具输入写入临时文件
TOOL_INPUT_FILE = "/tmp/harnessgenj_input_xxx.json"

# hooks 脚本读取
def get_tool_input() -> dict:
    input_file = os.environ.get("TOOL_INPUT_FILE")
    if input_file and Path(input_file).exists():
        return json.loads(Path(input_file).read_text())

# 方案B: stdin 传递（需 Claude Code 支持）
def get_tool_input() -> dict:
    if not sys.stdin.isatty():
        return json.loads(sys.stdin.read())

# 方案C: 简化环境变量
TOOL_NAME=Write
TOOL_FILE_PATH=/path/to/file
TOOL_CONTENT_LENGTH=1234
# 大内容写入临时文件，路径通过 TOOL_CONTENT_FILE 传递
```

**验收标准**:
- Write/Edit 操作后，hooks 能正确获取 file_path 和 content
- 无需重启会话即可生效

---

### 需求2: Hooks配置验证工具

**需求规格**:

```bash
# 命令
harnessgenj validate-hooks

# 检查项
1. settings.json 语法正确性
2. Python 脚本可执行
3. 环境变量传递测试
4. 输出诊断报告
```

**输出示例**:

```
[HGJ] Hooks 配置验证
✓ settings.json 语法正确
✓ harnessgenj_hook.py 可执行
✗ TOOL_INPUT 环境变量未传递
  建议: 使用临时文件传递方案

修复建议:
1. 在 settings.json 中添加: "TOOL_INPUT_FILE": "$TEMP/hgj_input.json"
2. 或联系 Claude Code 支持确认环境变量传递机制
```

---

### 需求3: 知识库结构化改造

**当前问题**: `knowledge.json` 是原始文档堆砌，无结构化条目。

**需求规格**:

```json
{
  "schema_version": "1.0",
  "entries": [
    {
      "id": "bug-shell-injection-001",
      "type": "security_issue",
      "problem": "ShellTool命令注入风险，管道和重定向可被绕过",
      "solution": "使用命令白名单模式，禁用管道和重定向",
      "code_location": {
        "file": "app/src/main/java/com/uvm/android/tools/builtin/ShellTool.java",
        "lines": [93, 118]
      },
      "severity": "critical",
      "tags": ["security", "shell", "injection"],
      "created_at": "2026-04-06T10:00:00Z",
      "verified": false,
      "verification_notes": ""
    }
  ],
  "indexes": {
    "by_type": {
      "security_issue": ["bug-shell-injection-001"]
    },
    "by_file": {
      "ShellTool.java": ["bug-shell-injection-001"]
    },
    "by_tag": {
      "security": ["bug-shell-injection-001"]
    }
  }
}
```

**条目类型定义**:

| 类型 | 必填字段 | 说明 |
|------|----------|------|
| `bug_fix` | problem, solution, code_location | 问题修复记录 |
| `decision_pattern` | rationale, choice, alternatives | 决策模式沉淀 |
| `architecture_change` | before, after, reason | 架构演进追踪 |
| `security_issue` | vulnerability, severity, fix | 安全问题追踪 |
| `test_case` | scenario, expected, actual | 测试用例库 |

**API 设计**:

```python
class KnowledgeBase:
    def add_entry(self, entry: dict) -> str:
        """添加条目，返回 ID"""
        
    def get_entry(self, entry_id: str) -> dict:
        """获取条目"""
        
    def search(self, query: str, filters: dict = None) -> list:
        """搜索条目"""
        
    def get_by_file(self, file_path: str) -> list:
        """按文件路径获取相关条目"""
        
    def get_by_tag(self, tag: str) -> list:
        """按标签获取条目"""
```

---

### 需求4: 任务状态机

**当前问题**: `current_task.json` 长期处于 pending 状态，无状态流转。

**需求规格**:

```python
class TaskStateMachine:
    STATES = ["pending", "in_progress", "reviewing", "completed", "failed", "cancelled"]
    TRANSITIONS = {
        "pending": ["in_progress", "cancelled"],
        "in_progress": ["reviewing", "failed", "cancelled"],
        "reviewing": ["completed", "in_progress", "failed"],
        "completed": [],
        "failed": ["in_progress", "cancelled"],
        "cancelled": []
    }
    
    def transition(self, task_id: str, new_state: str, reason: str = ""):
        """状态转换"""
        current = self.get_state(task_id)
        if new_state not in self.TRANSITIONS.get(current, []):
            raise InvalidTransitionError(current, new_state)
        
        self.update_state(task_id, new_state)
        self.record_event(task_id, "state_change", {
            "from": current,
            "to": new_state,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })
        
        # 触发对应的 hooks
        if new_state == "completed":
            self.trigger_hooks("on_task_complete", task_id)
        elif new_state == "reviewing":
            self.trigger_hooks("on_task_review", task_id)
```

**验收标准**:
- 任务状态正确流转
- 状态变更记录在 events 数组
- 状态变更触发对应的 hooks

---

### 需求5: 积分系统激活

**当前问题**: 所有角色统计数据为 0，events 数组为空。

**需求规格**:

```python
class ScoreManager:
    # 积分规则
    SCORE_RULES = {
        # Generator 积分
        "task_completed_first_try": {"role": "developer", "score": 10},
        "task_completed_second_try": {"role": "developer", "score": 5},
        "issue_false_positive": {"role": "developer", "score": 3},
        "production_bug": {"role": "developer", "score": -20},
        
        # Discriminator 积分
        "issue_found_critical": {"role": "code_reviewer", "score": 10},
        "issue_found_medium": {"role": "code_reviewer", "score": 5},
        "issue_false_positive": {"role": "code_reviewer", "score": -3},
        "issue_missed_critical": {"role": "code_reviewer", "score": -15},
    }
    
    def award_score(self, role_id: str, event_type: str, context: dict = None):
        """奖励积分"""
        rule = self.SCORE_RULES.get(event_type)
        if rule and rule["role"] in role_id:
            self.scores[role_id]["score"] += rule["score"]
            self.record_event(role_id, event_type, context)
    
    def record_event(self, role_id: str, event_type: str, context: dict):
        """记录积分事件"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "role_id": role_id,
            "event_type": event_type,
            "context": context
        }
        self.events.append(event)
        self.persist()
```

**验收标准**:
- 任务完成后 developer 积分增加
- 审查发现问题时 code_reviewer 积分增加
- events 数组有记录

---

### 需求6: 单一入口设计

**当前问题**: 需手动调用 `harness.receive_request()`，无统一入口。

**需求规格**:

```python
class HarnessGateway:
    """统一入口网关"""
    
    def intercept(self, user_message: str) -> str:
        """拦截用户消息，自动路由"""
        # 1. 意图识别
        intent = self.intent_router.identify(user_message)
        
        # 2. 路由到工作流
        workflow = self.workflow_router.route(intent)
        
        # 3. 执行工作流
        result = workflow.execute()
        
        # 4. 触发后处理
        self.trigger_post_processing(result)
        
        return result.response
    
    def trigger_post_processing(self, result):
        """触发后处理 hooks"""
        if result.has_code_changes:
            self.trigger_hooks("on_write_complete", result.files)
        if result.task_completed:
            self.trigger_hooks("on_task_complete", result.task_id)
```

**验收标准**:
- 用户消息自动识别意图
- 自动路由到对应工作流
- 无需手动调用 `receive_request()`

---

### 需求7: 角色自动触发机制

**当前问题**: 角色需手动调用，无自动触发机制。

**需求规格**:

```python
# 事件-角色触发映射
EVENT_ROLE_TRIGGERS = {
    "on_write_complete": ["CodeReviewer"],
    "on_edit_complete": ["CodeReviewer"],
    "on_task_complete": ["BugHunter", "Tester"],
    "on_security_issue": ["CodeReviewer", "BugHunter"],
    "on_architecture_change": ["Architect"],
}

class TriggerManager:
    def trigger_hooks(self, event_type: str, data: dict):
        """触发事件 hooks"""
        roles = EVENT_ROLE_TRIGGERS.get(event_type, [])
        for role in roles:
            self.invoke_role(role, event_type, data)
    
    def invoke_role(self, role_name: str, event_type: str, data: dict):
        """调用角色"""
        role = self.role_factory.create(role_name)
        result = role.execute(event_type, data)
        self.record_role_action(role_name, event_type, result)
```

**验收标准**:
- Write 完成后 CodeReviewer 自动审查
- 任务完成后 BugHunter 自动搜索边界问题
- 角色执行记录到 sessions.json

---

### 需求8: 状态实时持久化

**当前问题**: 状态只在会话结束时更新，可能丢失数据。

**需求规格**:

```python
class StateManager:
    # 持久化触发点
    PERSISTENCE_TRIGGERS = [
        "task_complete",
        "issue_found",
        "decision_made",
        "knowledge_entry_added",
        "role_action_completed",
        "score_changed",
        "session_message_added",
    ]
    
    def __init__(self):
        self._dirty = False
        self._pending_updates = {}
    
    def mark_dirty(self, field: str, value: Any):
        """标记待更新字段"""
        self._pending_updates[field] = value
        self._dirty = True
        
        # 达到阈值立即持久化
        if len(self._pending_updates) >= 5:
            self.flush()
    
    def flush(self):
        """立即持久化"""
        if not self._dirty:
            return
        
        self.state.update(self._pending_updates)
        self.state["last_sync"] = datetime.now().isoformat()
        
        # 原子写入
        temp_file = self.state_path.with_suffix(".tmp")
        temp_file.write_text(json.dumps(self.state, ensure_ascii=False, indent=2))
        temp_file.replace(self.state_path)
        
        self._dirty = False
        self._pending_updates = {}
```

**验收标准**:
- 关键操作后立即持久化
- 异常退出不丢失数据
- 使用原子写入防止损坏

---

## 第三部分：实施路线图

### Phase 1: Hooks修复 (立即)

| 任务 | 工时 | 优先级 |
|------|------|--------|
| Hooks输入传递方案选型 | 2h | P0 |
| 实现临时文件传递方案 | 4h | P0 |
| Hooks验证工具开发 | 4h | P0 |
| 文档更新 | 2h | P1 |

---

### Phase 2: 核心功能激活 (Week 1)

| 任务 | 工时 | 优先级 |
|------|------|--------|
| 知识库结构化改造 | 8h | P1 |
| 任务状态机实现 | 4h | P1 |
| 积分系统激活 | 4h | P1 |
| 单元测试 | 4h | P1 |

---

### Phase 3: 架构增强 (Week 2)

| 任务 | 工时 | 优先级 |
|------|------|--------|
| 单一入口设计 | 8h | P2 |
| 角色自动触发机制 | 4h | P2 |
| 状态实时持久化 | 4h | P2 |
| 集成测试 | 4h | P2 |

---

### Phase 4: 工具链集成 (Week 3+)

| 任务 | 工时 | 优先级 |
|------|------|--------|
| Git pre-commit 集成 | 4h | P3 |
| Git post-commit 集成 | 2h | P3 |
| IDE 插件开发 | 16h | P3 |
| 构建系统集成 | 8h | P3 |

---

## 第四部分：验收清单

### Hooks修复验收

- [ ] Write 操作触发 PostToolUse hook
- [ ] Edit 操作触发 PreToolUse 和 PostToolUse hooks
- [ ] hooks 能正确获取 file_path 和 content
- [ ] 事件文件正确生成到 `.harnessgenj/events/`
- [ ] 积分系统 events 数组正确更新
- [ ] 开发日志正确追加记录

### 核心功能验收

- [ ] 知识库条目包含结构化字段
- [ ] 任务状态正确流转
- [ ] 积分变动记录到 events 数组
- [ ] 角色统计数据非零

### 架构增强验收

- [ ] 用户消息自动路由到工作流
- [ ] Write 完成后 CodeReviewer 自动审查
- [ ] 状态在关键操作后立即持久化

---

*文档版本: v1.0*
*生成日期: 2026-04-06*