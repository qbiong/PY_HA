# py_ha 项目上下文

## 项目概述

py_ha 是一个 Harness Engineering 框架，用于 AI Agent 协作开发。

**核心能力**：
- **AI 对话自动记录**：只需调用 `record()` 或 `chat()`，自动识别内容类型并持久化
- 角色驱动协作（开发者、测试员、产品经理、架构师、项目经理）
- 工作流驱动开发（需求→设计→开发→测试→发布）
- JVM 风格记忆管理
- 渐进式披露（每个角色只获取必要信息）

## 当前项目状态

**项目名称**: 待配置
**技术栈**: 待配置
**当前阶段**: 初始化

## AI 自动记录（核心功能）

### 一行代码自动持久化

```python
from py_ha import Harness

harness = Harness("项目名称", persistent=True)
harness.setup_team()

# AI 对话时自动记录（智能识别内容类型）
harness.record("用户需要一个登录功能")       # → requirements.md
harness.record("发现登录页面验证码异常")      # → testing.md
harness.record("已完成登录模块开发")          # → progress.md
harness.record("正在实现用户认证逻辑")        # → development.md
```

### 自动识别规则

| 关键词 | 记录位置 | 说明 |
|--------|----------|------|
| 需求、功能、需要、添加、新增、实现、开发、设计 | requirements.md | 需求文档 |
| bug、问题、错误、异常、失败、修复、fix、报错 | testing.md | 测试/Bug报告 |
| 完成、已、进度、状态、更新、通过、成功 | progress.md | 进度报告 |
| 其他内容 | development.md | 开发日志 |

### chat() 方法自动记录

```python
# 用户消息自动记录
harness.chat("我需要添加一个搜索功能")  # → 自动调用 record()

# AI 回复自动记录
harness.chat("好的，我来实现搜索模块", role="assistant")  # → 自动调用 record()

# 禁用自动记录（仅存储到会话历史）
harness.chat("临时讨论", auto_record=False)
```

## 使用方式

### 快速开发

```python
from py_ha import Harness

harness = Harness("项目名称")
harness.setup_team()

# 一键开发功能（自动记录到 requirements.md + development.md）
result = harness.develop("功能描述")

# 一键修复 Bug（自动记录到 testing.md + development.md）
result = harness.fix_bug("Bug 描述")
```

### 项目管理

```python
from py_ha import ProjectStateManager, DocumentType

state = ProjectStateManager(".py_ha")
state.initialize("项目名称", "技术栈")

# 更新需求文档
state.update_document(DocumentType.REQUIREMENTS, "内容", "product_manager")

# 为开发者生成最小上下文
context = state.get_context_for_role("developer")
```

### 记忆管理

```python
from py_ha import MemoryManager

manager = MemoryManager()

# 存储重要知识（永不回收）
manager.store_important_knowledge("key", "value")

# 触发 GC 清理
manager.invoke_gc_minor()
```

## 工作流程

当用户请求开发功能时，按以下流程执行：

1. **需求分析** → 产品经理角色分析需求
2. **架构设计** → 架构师角色设计方案
3. **开发实现** → 开发者角色编码
4. **测试验证** → 测试员角色测试
5. **文档编写** → 文档管理员记录

## 可用工具

| 工具 | 说明 | 自动记录 |
|------|------|----------|
| `harness.record(内容)` | 智能记录（自动识别类型） | ✓ |
| `harness.chat(消息)` | 对话（默认自动记录） | ✓ |
| `harness.develop(需求)` | 一键开发功能 | ✓ |
| `harness.fix_bug(描述)` | 一键修复 Bug | ✓ |
| `harness.remember(key, value)` | 存储记忆 | ✓ |
| `harness.recall(key)` | 回忆信息 | - |

## 角色职责

| 角色 | 职责 |
|------|------|
| ProductManager | 需求分析、用户故事、验收标准 |
| Architect | 系统设计、技术选型、架构评审 |
| Developer | 编码实现、Bug修复、代码审查 |
| Tester | 测试编写、测试执行、Bug报告 |
| DocWriter | 文档编写、知识库维护 |
| ProjectManager | 任务协调、进度追踪 |

## 项目目录

```
.py_ha/
├── project.json     # 项目信息
├── documents/       # 项目文档
│   ├── requirements.md   # 需求文档
│   ├── design.md        # 设计文档
│   ├── development.md   # 开发日志
│   ├── testing.md       # 测试报告
│   └── progress.md      # 进度报告
└── sessions.json    # 会话历史
```