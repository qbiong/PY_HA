# py_ha 项目上下文

## 项目概述

py_ha 是一个 Harness Engineering 框架，用于 AI Agent 协作开发。

**核心能力**：
- 角色驱动协作（开发者、测试员、产品经理、架构师、项目经理）
- 工作流驱动开发（需求→设计→开发→测试→发布）
- JVM 风格记忆管理
- 渐进式披露（每个角色只获取必要信息）

## 当前项目状态

**项目名称**: 待配置
**技术栈**: 待配置
**当前阶段**: 初始化

## 使用方式

### 快速开发

```python
from py_ha import Harness

harness = Harness("项目名称")
harness.setup_team()

# 一键开发功能
result = harness.develop("功能描述")

# 一键修复 Bug
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

| 工具 | 说明 |
|------|------|
| `harness.develop(需求)` | 一键开发功能 |
| `harness.fix_bug(描述)` | 一键修复 Bug |
| `harness.analyze(需求)` | 需求分析 |
| `harness.design(描述)` | 架构设计 |
| `harness.remember(key, value)` | 存储记忆 |
| `harness.recall(key)` | 回忆信息 |

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
│   ├── requirements.md
│   ├── design.md
│   ├── development.md
│   ├── testing.md
│   └── progress.md
└── sessions.json    # 会话历史
```