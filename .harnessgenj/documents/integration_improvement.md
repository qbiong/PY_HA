# HarnessGenJ 集成改进方案

## 问题分析

### 当前痛点
1. **被动触发** - 需要用户主动在提示词中强调"项目经理角色"
2. **AI忽略指令** - CLAUDE.md是指令而非强制执行，AI经常忽略
3. **Hooks时机有限** - 只在文件操作时触发，无法主动引导

### 根本原因
- Claude Code没有"对话开始时"的Hook
- MCP工具需要主动调用，不会自动触发
- AI对CLAUDE.md的遵循程度取决于模型能力

---

## 改进方案

### 方案1: 智能意图检测Hook（推荐）

**原理**: 在PreToolUse时检测用户意图，自动引导使用框架

**实现**: 新增 `--intent-detection` Hook

```python
# .claude/harnessgenj_hook.py 新增

INTENT_PATTERNS = {
    "develop": [
        r"实现.*功能", r"开发.*模块", r"添加.*特性",
        r"写.*代码", r"创建.*组件", r"构建.*系统"
    ],
    "fix_bug": [
        r"修复.*bug", r"解决.*问题", r"修复.*错误",
        r"调试.*异常", r"修复.*崩溃"
    ],
    "review": [
        r"审查.*代码", r"检查.*质量", r"code review"
    ],
    "project_management": [
        r"项目.*状态", r"任务.*分配", r"进度.*报告",
        r"团队.*协调", r"项目经理"
    ]
}

def detect_user_intent(user_message: str) -> str | None:
    """检测用户意图"""
    import re
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, user_message, re.IGNORECASE):
                return intent
    return None

def suggest_framework_usage(intent: str) -> str:
    """生成框架使用建议"""
    suggestions = {
        "develop": "💡 检测到开发任务，建议使用: harness.develop('需求描述')",
        "fix_bug": "💡 检测到修复任务，建议使用: harness.fix_bug('问题描述')",
        "review": "💡 检测到审查任务，建议使用: harness.quick_review(code)",
        "project_management": "💡 检测到项目管理任务，框架已激活PM角色"
    }
    return suggestions.get(intent, "")
```

**优点**: 无需用户主动提及，自动检测意图
**缺点**: 依赖正则匹配，可能有误判

---

### 方案2: 用户提示词Hook（Claude Code原生支持）

**原理**: 在用户发送消息时，自动注入框架状态

**实现**: 利用 `UserPromptSubmit` Hook（Claude Code支持）

```json
// .claude/settings.json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/harnessgenj_hook.py --inject-context"
          }
        ]
      }
    ]
  }
}
```

```python
def handle_user_prompt_submit() -> int:
    """
    在用户发送消息时注入框架上下文
    
    这样AI每次回复都会看到框架状态
    """
    # 读取框架状态
    status = get_framework_status()
    
    # 注入到系统提示
    context = f"""
[HarnessGenJ 框架状态]
- 项目: {status['project_name']}
- 当前角色: {status['active_role']}
- 积分排行: {status['score_summary']}
- 待处理任务: {status['pending_tasks']}

[提示] 开发任务请使用 harness.develop() 或 MCP工具 task_develop
"""
    # 输出到stderr，AI可以看到
    print(context, file=sys.stderr)
    return 0
```

**优点**: 每次对话自动注入上下文
**缺点**: 增加token消耗

---

### 方案3: 状态文件持久化 + 智能提醒

**原理**: 维护一个框架状态文件，AI每次读取时自动激活

**实现**:

```python
# .harnessgenj/session_context.json
{
  "framework_active": true,
  "current_role": "project_manager",
  "last_activity": "2026-04-10T01:30:00",
  "suggested_action": "等待用户指示下一步任务",
  "pending_reminders": [
    "修复P0问题后需要运行测试验证"
  ]
}
```

```python
def update_session_context(action: str, role: str = None):
    """更新会话上下文"""
    context = {
        "framework_active": True,
        "current_role": role or get_current_role(),
        "last_activity": datetime.now().isoformat(),
        "suggested_action": action,
        "project_status": get_project_status_summary()
    }
    
    with open(".harnessgenj/session_context.json", "w") as f:
        json.dump(context, f, indent=2)
```

**优点**: 状态持久化，跨对话保持
**缺点**: 需要AI主动读取

---

### 方案4: CLAUDE.md 强化（最简单）

**原理**: 让CLAUDE.md更加"强制"和"显眼"

**改进点**:

1. **添加强制触发条件**
```markdown
## ⚠️ 强制触发条件

当用户消息包含以下关键词时，**必须**优先使用框架：

| 关键词 | 必须使用的框架方法 |
|--------|-------------------|
| 实现、开发、添加、创建 | `harness.develop()` |
| 修复、解决、调试 | `harness.fix_bug()` |
| 审查、检查 | `harness.quick_review()` |
| 状态、进度、任务 | `harness.get_status()` |

**违规后果**: 跳过框架直接编码将导致：
- 代码无对抗审查保护
- 无法获得积分奖励
- 可能产生质量隐患
```

2. **添加对话开始提示**
```markdown
## 🚀 每次对话开始时

**自动执行以下初始化代码**:

```python
from harnessgenj import Harness
harness = Harness.get_last_instance() or Harness.from_project(".")
print(harness.get_status())
```

这是**强制要求**，不是可选操作。
```

---

### 方案5: MCP工具作为主要入口（已实现）

**原理**: 利用Claude Code的MCP工具自动发现

**改进点**:

1. 工具描述更加主动:
```python
# mcp/tools/task_tools.py
class TaskDevelopTool(MCPTool):
    name = "task_develop"
    description = """
    🎯 开发新功能（推荐优先使用此工具而非直接编码）
    
    此工具会自动：
    - 执行完整工作流
    - 进行对抗性代码审查
    - 更新项目文档
    - 获得积分奖励
    
    直接编码将跳过这些保护机制。
    """
```

2. 在工具列表中突出显示:
```python
# mcp/server.py
def list_tools():
    # 把开发相关工具放在最前面
    priority_tools = ["task_develop", "task_fix_bug", "system_status"]
    ...
```

---

## 推荐实施方案

### 短期（立即可实施）

1. **强化CLAUDE.md** - 添加强制触发条件和更明确的指令
2. **改进Hooks** - 添加意图检测，在用户输入时提示使用框架

### 中期（需要开发）

1. **UserPromptSubmit Hook** - 在用户发送消息时注入框架上下文
2. **会话状态持久化** - 维护框架状态文件

### 长期（架构优化）

1. **VSCode扩展** - 提供可视化界面和状态栏集成
2. **Claude Code扩展** - 专门的状态显示和快速操作面板

---

## 实施优先级

| 方案 | 难度 | 效果 | 优先级 |
|------|------|------|--------|
| 方案4: CLAUDE.md强化 | 低 | 中 | **P0** |
| 方案1: 意图检测Hook | 中 | 高 | **P1** |
| 方案2: UserPromptSubmit | 中 | 高 | P2 |
| 方案3: 状态持久化 | 低 | 中 | P2 |
| 方案5: MCP工具优化 | 低 | 中 | P1 |