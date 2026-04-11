# 产品经理 - 专注于需求管理 知识文件

> 此文件由 AGENTS.md 自动派生，请勿手动修改
> 更新时间: 2026-04-10 20:43

---

# AGENTS.md - HarnessGenJ 项目知识库

> 此文件存储项目核心知识，AI 助手启动时自动加载

## 项目信息

- **项目名称**: HarnessGenJ (HGJ) - Harness Engineering with JVM-style Generational Memory
- **技术栈**: Python + pytest + FastAPI + Pydantic
- **当前状态**: 开发中 (v1.3.1)
- **代码行数**: ~15,000 行

## 项目简介

HarnessGenJ 是一个 AI Agent 协作框架，核心特性：

1. **角色驱动协作** - Developer/Tester/PM/Architect/CodeReviewer/BugHunter
2. **JVM 风格记忆管理** - Eden/Survivor/Old/Permanent 分代存储
3. **GAN 对抗质量保证** - 生成器-判别器对抗审查机制
4. **MCP Server 支持** - 21 个工具暴露给 Claude Code

## 核心规范

### 框架使用规范（自举模式）

**本项目自身使用 HGJ 框架进行开发！**

```
用户需求 → harness.develop() → 签发许可 → 执行指令 → complete_task()
```

**必须遵守**：
- 所有代码修改必须通过 `harness.develop()` 或 `harness.fix_bug()`
- 禁止直接编辑代码而不经过框架
- 框架会签发操作许可，AI 只能在许可范围内操作

### 代码规范

- 遵循 PEP 8 规范
- 使用 Pydantic BaseModel 进行数据验证
- 所有公共 API 需要类型注解和 docstring
- 测试覆盖率目标: 80%+

### 工作流程

1. **需求接收** → `harness.receive_request("需求描述")`
2. **开发执行** → `harness.develop("需求描述")`
3. **对抗审查** → 自动执行（框架强制）
4. **文档更新** → 自动执行（框架强制）
5. **任务完成** → `harness.complete_task(task_id, "摘要")`

## 目录结构

```
src/harnessgenj/
├── engine.py          # 主入口 Harness 类
├── roles/             # 角色定义
├── workflow/          # 工作流系统
├── memory/            # JVM 风格记忆管理
├── quality/           # 质量保证（积分、对抗）
├── harness/           # 框架核心组件
│   ├── framework_session.py    # 会话权限管理
│   ├── operation_instruction.py # 操作指令协议
│   └── adversarial.py          # 对抗审查
├── mcp/               # MCP Server
└── notify/            # 用户通知
```

## 常用命令

```python
# 初始化框架（每次对话开始）
from harnessgenj import Harness
harness = Harness.from_project(".")

# 开发功能（返回操作指令）
result = harness.develop("功能描述")

# 修复 Bug
result = harness.fix_bug("问题描述")

# 查看状态
harness.get_status()

# 查看积分排行
harness.get_score_leaderboard()
```

## 重要约定

1. **渐进式披露**: 每个角色只获取最小必要信息
2. **持久化优先**: 所有重要操作自动保存到 .harnessgenj/
3. **文档驱动**: 需求/设计/开发/测试都有对应文档
4. **对抗审查**: 所有代码变更经过 CodeReviewer/BugHunter 审查
5. **积分激励**: 使用框架开发获得积分奖励

## 角色边界

| 角色 | 权限 | 禁止 |
|------|------|------|
| Developer | 编辑代码 | 修改架构设计 |
| CodeReviewer | 只读、审查 | 修改代码 |
| BugHunter | 只读、安全审查 | 修改代码 |
| ProjectManager | 编辑文档、协调 | 修改代码 |
| Architect | 编辑设计文档 | 直接修改代码实现 |

---
*此文件由 HarnessGenJ 自动维护 - 自举模式*


## architect

# 架构师 - 专注于系统设计 知识文件

> 此文件由 AGENTS.md 自动派生，请勿手动修改
> 更新时间: 2026-04-10 20:43

---

# AGENTS.md - HarnessGenJ 项目知识库

> 此文件存储项目核心知识，AI 助手启动时自动加载

## 项目信息

- **项目名称**: HarnessGenJ (HGJ) - Harness Engineering with JVM-style Generational Memory
- **技术栈**: Python + pytest + FastAPI + Pydantic
- **当前状态**: 开发中 (v1.3.1)
- **代码行数**: ~15,000 行

## 项目简介

HarnessGenJ 是一个 AI Agent 协作框架，核心特性：

1. **角色驱动协作** - Developer/Tester/PM/Architect/CodeReviewer/BugHunter
2. **JVM 风格记忆管理** - Eden/Survivor/Old/Permanent 分代存储
3. **GAN 对抗质量保证** - 生成器-判别器对抗审查机制
4. **MCP Server 支持** - 21 个工具暴露给 Claude Code

## 核心规范

### 框架使用规范（自举模式）

**本项目自身使用 HGJ 框架进行开发！**

```
用户需求 → harness.develop() → 签发许可 → 执行指令 → complete_task()
```

**必须遵守**：
- 所有代码修改必须通过 `harness.develop()` 或 `harness.fix_bug()`
- 禁止直接编辑代码而不经过框架
- 框架会签发操作许可，AI 只能在许可范围内操作

### 代码规范

- 遵循 PEP 8 规范
- 使用 Pydantic BaseModel 进行数据验证
- 所有公共 API 需要类型注解和 docstring
- 测试覆盖率目标: 80%+

### 工作流程

1. **需求接收** → `harness.receive_request("需求描述")`
2. **开发执行** → `harness.develop("需求描述")`
3. **对抗审查** → 自动执行（框架强制）
4. **文档更新** → 自动执行（框架强制）
5. **任务完成** → `harness.complete_task(task_id, "摘要")`

## 目录结构

```
src/harnessgenj/
├── engine.py          # 主入口 Harness 类
├── roles/             # 角色定义
├── workflow/          # 工作流系统
├── memory/            # JVM 风格记忆管理
├── quality/           # 质量保证（积分、对抗）
├── harness/           # 框架核心组件
│   ├── framework_session.py    # 会话权限管理
│   ├── operation_instruction.py # 操作指令协议
│   └── adversarial.py          # 对抗审查
├── mcp/               # MCP Server
└── notify/            # 用户通知
```

## 常用命令

```python
# 初始化框架（每次对话开始）
from harnessgenj import Harness
harness = Harness.from_project(".")

# 开发功能（返回操作指令）
result = harness.develop("功能描述")

# 修复 Bug
result = harness.fix_bug("问题描述")

# 查看状态
harness.get_status()

# 查看积分排行
harness.get_score_leaderboard()
```

## 重要约定

1. **渐进式披露**: 每个角色只获取最小必要信息
2. **持久化优先**: 所有重要操作自动保存到 .harnessgenj/
3. **文档驱动**: 需求/设计/开发/测试都有对应文档
4. **对抗审查**: 所有代码变更经过 CodeReviewer/BugHunter 审查
5. **积分激励**: 使用框架开发获得积分奖励

## 角色边界

| 角色 | 权限 | 禁止 |
|------|------|------|
| Developer | 编辑代码 | 修改架构设计 |
| CodeReviewer | 只读、审查 | 修改代码 |
| BugHunter | 只读、安全审查 | 修改代码 |
| ProjectManager | 编辑文档、协调 | 修改代码 |
| Architect | 编辑设计文档 | 直接修改代码实现 |

---
*此文件由 HarnessGenJ 自动维护 - 自举模式*


## architect

# 架构师 - 专注于系统设计 知识文件

> 此文件由 AGENTS.md 自动派生，请勿手动修改
> 更新时间: 2026-04-10 20:43

---

# AGENTS.md - HarnessGenJ 项目知识库

> 此文件存储项目核心知识，AI 助手启动时自动加载

## 项目信息

- **项目名称**: HarnessGenJ (HGJ) - Harness Engineering with JVM-style Generational Memory
- **技术栈**: Python + pytest + FastAPI + Pydantic
- **当前状态**: 开发中 (v1.3.1)
- **代码行数**: ~15,000 行

## 项目简介

HarnessGenJ 是一个 AI Agent 协作框架，核心特性：

1. **角色驱动协作** - Developer/Tester/PM/Architect/CodeReviewer/BugHunter
2. **JVM 风格记忆管理** - Eden/Survivor/Old/Permanent 分代存储
3. **GAN 对抗质量保证** - 生成器-判别器对抗审查机制
4. **MCP Server 支持** - 21 个工具暴露给 Claude Code

## 核心规范

### 框架使用规范（自举模式）

**本项目自身使用 HGJ 框架进行开发！**

```
用户需求 → harness.develop() → 签发许可 → 执行指令 → complete_task()
```

**必须遵守**：
- 所有代码修改必须通过 `harness.develop()` 或 `harness.fix_bug()`
- 禁止直接编辑代码而不经过框架
- 框架会签发操作许可，AI 只能在许可范围内操作

### 代码规范

- 遵循 PEP 8 规范
- 使用 Pydantic BaseModel 进行数据验证
- 所有公共 API 需要类型注解和 docstring
- 测试覆盖率目标: 80%+

### 工作流程

1. **需求接收** → `harness.receive_request("需求描述")`
2. **开发执行** → `harness.develop("需求描述")`
3. **对抗审查** → 自动执行（框架强制）
4. **文档更新** → 自动执行（框架强制）
5. **任务完成** → `harness.complete_task(task_id, "摘要")`

## 目录结构

```
src/harnessgenj/
├── engine.py          # 主入口 Harness 类
├── roles/             # 角色定义
├── workflow/          # 工作流系统
├── memory/            # JVM 风格记忆管理
├── quality/           # 质量保证（积分、对抗）
├── harness/           # 框架核心组件
│   ├── framework_session.py    # 会话权限管理
│   ├── operation_instruction.py # 操作指令协议
│   └── adversarial.py          # 对抗审查
├── mcp/               # MCP Server
└── notify/            # 用户通知
```

## 常用命令

```python
# 初始化框架（每次对话开始）
from harnessgenj import Harness
harness = Harness.from_project(".")

# 开发功能（返回操作指令）
result = harness.develop("功能描述")

# 修复 Bug
result = harness.fix_bug("问题描述")

# 查看状态
harness.get_status()

# 查看积分排行
harness.get_score_leaderboard()
```

## 重要约定

1. **渐进式披露**: 每个角色只获取最小必要信息
2. **持久化优先**: 所有重要操作自动保存到 .harnessgenj/
3. **文档驱动**: 需求/设计/开发/测试都有对应文档
4. **对抗审查**: 所有代码变更经过 CodeReviewer/BugHunter 审查
5. **积分激励**: 使用框架开发获得积分奖励

## 角色边界

| 角色 | 权限 | 禁止 |
|------|------|------|
| Developer | 编辑代码 | 修改架构设计 |
| CodeReviewer | 只读、审查 | 修改代码 |
| BugHunter | 只读、安全审查 | 修改代码 |
| ProjectManager | 编辑文档、协调 | 修改代码 |
| Architect | 编辑设计文档 | 直接修改代码实现 |

---
*此文件由 HarnessGenJ 自动维护 - 自举模式*


## conventions

# 代码约定

> 此文件由 HarnessGenJ 自动生成，根据技术栈自动适配
> 请遵循项目既有的代码风格

## 编码风格

- 遵循 PEP 8 规范
- 使用类型注解（Type Hints）
- 函数名使用 snake_case
- 类名使用 PascalCase
- 常量使用 UPPER_SNAKE_CASE

## 代码组织

- 使用模块化设计
- 每个 module 应有明确的职责
- 使用 `__init__.py` 导出公共 API

## 文档

- 函数必须有文档字符串（docstring）
- 使用 Google 或 NumPy 风格的 docstring
- 复杂逻辑需要注释说明

## 类型检查

- 推荐使用 mypy 进行静态类型检查
- 使用 `typing` 模块的泛型类型

## 测试约定

- 所有新功能需要添加测试
- 测试文件放在 `test/` 或 `tests/` 目录
- 测试函数名应描述测试场景
- 使用 AAA 模式（Arrange-Act-Assert）

推荐使用: pytest



## tech

# 技术栈

> 此文件由 HarnessGenJ 自动生成，根据项目文件自动检测
> 检测置信度: 70%

## 主要技术

- **语言**: Python
- **框架**: pytest, Vue, FastAPI, Flask, Django, React
- **包管理器**: poetry

## 版本要求

- **python**: >=3.11

## 数据库

- Redis
- MySQL

## 测试框架

- pytest



## workflow

> priority: 60
> auto_inject: True
> roles: all

# 工作流程

## 标准流程
1. 需求分析 (PM)
2. 架构设计 (Architect)
3. 开发实现 (Developer)
4. 测试验证 (Tester)


---

*自动生成于 2026-04-10 20:43:12*



## conventions

# 代码约定

> 此文件由 HarnessGenJ 自动生成，根据技术栈自动适配
> 请遵循项目既有的代码风格

## 编码风格

- 遵循 PEP 8 规范
- 使用类型注解（Type Hints）
- 函数名使用 snake_case
- 类名使用 PascalCase
- 常量使用 UPPER_SNAKE_CASE

## 代码组织

- 使用模块化设计
- 每个 module 应有明确的职责
- 使用 `__init__.py` 导出公共 API

## 文档

- 函数必须有文档字符串（docstring）
- 使用 Google 或 NumPy 风格的 docstring
- 复杂逻辑需要注释说明

## 类型检查

- 推荐使用 mypy 进行静态类型检查
- 使用 `typing` 模块的泛型类型

## 测试约定

- 所有新功能需要添加测试
- 测试文件放在 `test/` 或 `tests/` 目录
- 测试函数名应描述测试场景
- 使用 AAA 模式（Arrange-Act-Assert）

推荐使用: pytest



## developer

# 开发者 - 专注于代码实现 知识文件

> 此文件由 AGENTS.md 自动派生，请勿手动修改
> 更新时间: 2026-04-10 20:43

---

# AGENTS.md - HarnessGenJ 项目知识库

> 此文件存储项目核心知识，AI 助手启动时自动加载

## 项目信息

- **项目名称**: HarnessGenJ (HGJ) - Harness Engineering with JVM-style Generational Memory
- **技术栈**: Python + pytest + FastAPI + Pydantic
- **当前状态**: 开发中 (v1.3.1)
- **代码行数**: ~15,000 行

## 项目简介

HarnessGenJ 是一个 AI Agent 协作框架，核心特性：

1. **角色驱动协作** - Developer/Tester/PM/Architect/CodeReviewer/BugHunter
2. **JVM 风格记忆管理** - Eden/Survivor/Old/Permanent 分代存储
3. **GAN 对抗质量保证** - 生成器-判别器对抗审查机制
4. **MCP Server 支持** - 21 个工具暴露给 Claude Code

## 核心规范

### 框架使用规范（自举模式）

**本项目自身使用 HGJ 框架进行开发！**

```
用户需求 → harness.develop() → 签发许可 → 执行指令 → complete_task()
```

**必须遵守**：
- 所有代码修改必须通过 `harness.develop()` 或 `harness.fix_bug()`
- 禁止直接编辑代码而不经过框架
- 框架会签发操作许可，AI 只能在许可范围内操作

### 代码规范

- 遵循 PEP 8 规范
- 使用 Pydantic BaseModel 进行数据验证
- 所有公共 API 需要类型注解和 docstring
- 测试覆盖率目标: 80%+

### 工作流程

1. **需求接收** → `harness.receive_request("需求描述")`
2. **开发执行** → `harness.develop("需求描述")`
3. **对抗审查** → 自动执行（框架强制）
4. **文档更新** → 自动执行（框架强制）
5. **任务完成** → `harness.complete_task(task_id, "摘要")`

## 目录结构

```
src/harnessgenj/
├── engine.py          # 主入口 Harness 类
├── roles/             # 角色定义
├── workflow/          # 工作流系统
├── memory/            # JVM 风格记忆管理
├── quality/           # 质量保证（积分、对抗）
├── harness/           # 框架核心组件
│   ├── framework_session.py    # 会话权限管理
│   ├── operation_instruction.py # 操作指令协议
│   └── adversarial.py          # 对抗审查
├── mcp/               # MCP Server
└── notify/            # 用户通知
```

## 常用命令

```python
# 初始化框架（每次对话开始）
from harnessgenj import Harness
harness = Harness.from_project(".")

# 开发功能（返回操作指令）
result = harness.develop("功能描述")

# 修复 Bug
result = harness.fix_bug("问题描述")

# 查看状态
harness.get_status()

# 查看积分排行
harness.get_score_leaderboard()
```

## 重要约定

1. **渐进式披露**: 每个角色只获取最小必要信息
2. **持久化优先**: 所有重要操作自动保存到 .harnessgenj/
3. **文档驱动**: 需求/设计/开发/测试都有对应文档
4. **对抗审查**: 所有代码变更经过 CodeReviewer/BugHunter 审查
5. **积分激励**: 使用框架开发获得积分奖励

## 角色边界

| 角色 | 权限 | 禁止 |
|------|------|------|
| Developer | 编辑代码 | 修改架构设计 |
| CodeReviewer | 只读、审查 | 修改代码 |
| BugHunter | 只读、安全审查 | 修改代码 |
| ProjectManager | 编辑文档、协调 | 修改代码 |
| Architect | 编辑设计文档 | 直接修改代码实现 |

---
*此文件由 HarnessGenJ 自动维护 - 自举模式*


## conventions

# 代码约定

> 此文件由 HarnessGenJ 自动生成，根据技术栈自动适配
> 请遵循项目既有的代码风格

## 编码风格

- 遵循 PEP 8 规范
- 使用类型注解（Type Hints）
- 函数名使用 snake_case
- 类名使用 PascalCase
- 常量使用 UPPER_SNAKE_CASE

## 代码组织

- 使用模块化设计
- 每个 module 应有明确的职责
- 使用 `__init__.py` 导出公共 API

## 文档

- 函数必须有文档字符串（docstring）
- 使用 Google 或 NumPy 风格的 docstring
- 复杂逻辑需要注释说明

## 类型检查

- 推荐使用 mypy 进行静态类型检查
- 使用 `typing` 模块的泛型类型

## 测试约定

- 所有新功能需要添加测试
- 测试文件放在 `test/` 或 `tests/` 目录
- 测试函数名应描述测试场景
- 使用 AAA 模式（Arrange-Act-Assert）

推荐使用: pytest



## tech

# 技术栈

> 此文件由 HarnessGenJ 自动生成，根据项目文件自动检测
> 检测置信度: 70%

## 主要技术

- **语言**: Python
- **框架**: pytest, Vue, FastAPI, Flask, Django, React
- **包管理器**: poetry

## 版本要求

- **python**: >=3.11

## 数据库

- Redis
- MySQL

## 测试框架

- pytest



## workflow

> priority: 60
> auto_inject: True
> roles: all

# 工作流程

## 标准流程
1. 需求分析 (PM)
2. 架构设计 (Architect)
3. 开发实现 (Developer)
4. 测试验证 (Tester)


---

*自动生成于 2026-04-10 20:43:12*



## product_manager

# 产品经理 - 专注于需求管理 知识文件

> 此文件由 AGENTS.md 自动派生，请勿手动修改
> 更新时间: 2026-04-10 20:43

---

# AGENTS.md - HarnessGenJ 项目知识库

> 此文件存储项目核心知识，AI 助手启动时自动加载

## 项目信息

- **项目名称**: HarnessGenJ (HGJ) - Harness Engineering with JVM-style Generational Memory
- **技术栈**: Python + pytest + FastAPI + Pydantic
- **当前状态**: 开发中 (v1.3.1)
- **代码行数**: ~15,000 行

## 项目简介

HarnessGenJ 是一个 AI Agent 协作框架，核心特性：

1. **角色驱动协作** - Developer/Tester/PM/Architect/CodeReviewer/BugHunter
2. **JVM 风格记忆管理** - Eden/Survivor/Old/Permanent 分代存储
3. **GAN 对抗质量保证** - 生成器-判别器对抗审查机制
4. **MCP Server 支持** - 21 个工具暴露给 Claude Code

## 核心规范

### 框架使用规范（自举模式）

**本项目自身使用 HGJ 框架进行开发！**

```
用户需求 → harness.develop() → 签发许可 → 执行指令 → complete_task()
```

**必须遵守**：
- 所有代码修改必须通过 `harness.develop()` 或 `harness.fix_bug()`
- 禁止直接编辑代码而不经过框架
- 框架会签发操作许可，AI 只能在许可范围内操作

### 代码规范

- 遵循 PEP 8 规范
- 使用 Pydantic BaseModel 进行数据验证
- 所有公共 API 需要类型注解和 docstring
- 测试覆盖率目标: 80%+

### 工作流程

1. **需求接收** → `harness.receive_request("需求描述")`
2. **开发执行** → `harness.develop("需求描述")`
3. **对抗审查** → 自动执行（框架强制）
4. **文档更新** → 自动执行（框架强制）
5. **任务完成** → `harness.complete_task(task_id, "摘要")`

## 目录结构

```
src/harnessgenj/
├── engine.py          # 主入口 Harness 类
├── roles/             # 角色定义
├── workflow/          # 工作流系统
├── memory/            # JVM 风格记忆管理
├── quality/           # 质量保证（积分、对抗）
├── harness/           # 框架核心组件
│   ├── framework_session.py    # 会话权限管理
│   ├── operation_instruction.py # 操作指令协议
│   └── adversarial.py          # 对抗审查
├── mcp/               # MCP Server
└── notify/            # 用户通知
```

## 常用命令

```python
# 初始化框架（每次对话开始）
from harnessgenj import Harness
harness = Harness.from_project(".")

# 开发功能（返回操作指令）
result = harness.develop("功能描述")

# 修复 Bug
result = harness.fix_bug("问题描述")

# 查看状态
harness.get_status()

# 查看积分排行
harness.get_score_leaderboard()
```

## 重要约定

1. **渐进式披露**: 每个角色只获取最小必要信息
2. **持久化优先**: 所有重要操作自动保存到 .harnessgenj/
3. **文档驱动**: 需求/设计/开发/测试都有对应文档
4. **对抗审查**: 所有代码变更经过 CodeReviewer/BugHunter 审查
5. **积分激励**: 使用框架开发获得积分奖励

## 角色边界

| 角色 | 权限 | 禁止 |
|------|------|------|
| Developer | 编辑代码 | 修改架构设计 |
| CodeReviewer | 只读、审查 | 修改代码 |
| BugHunter | 只读、安全审查 | 修改代码 |
| ProjectManager | 编辑文档、协调 | 修改代码 |
| Architect | 编辑设计文档 | 直接修改代码实现 |

---
*此文件由 HarnessGenJ 自动维护 - 自举模式*


## conventions

# 代码约定

> 此文件由 HarnessGenJ 自动生成，根据技术栈自动适配
> 请遵循项目既有的代码风格

## 编码风格

- 遵循 PEP 8 规范
- 使用类型注解（Type Hints）
- 函数名使用 snake_case
- 类名使用 PascalCase
- 常量使用 UPPER_SNAKE_CASE

## 代码组织

- 使用模块化设计
- 每个 module 应有明确的职责
- 使用 `__init__.py` 导出公共 API

## 文档

- 函数必须有文档字符串（docstring）
- 使用 Google 或 NumPy 风格的 docstring
- 复杂逻辑需要注释说明

## 类型检查

- 推荐使用 mypy 进行静态类型检查
- 使用 `typing` 模块的泛型类型

## 测试约定

- 所有新功能需要添加测试
- 测试文件放在 `test/` 或 `tests/` 目录
- 测试函数名应描述测试场景
- 使用 AAA 模式（Arrange-Act-Assert）

推荐使用: pytest



## tech

# 技术栈

> 此文件由 HarnessGenJ 自动生成，根据项目文件自动检测
> 检测置信度: 70%

## 主要技术

- **语言**: Python
- **框架**: pytest, Vue, FastAPI, Flask, Django, React
- **包管理器**: poetry

## 版本要求

- **python**: >=3.11

## 数据库

- Redis
- MySQL

## 测试框架

- pytest



## workflow

> priority: 60
> auto_inject: True
> roles: all

# 工作流程

## 标准流程
1. 需求分析 (PM)
2. 架构设计 (Architect)
3. 开发实现 (Developer)
4. 测试验证 (Tester)


---

*自动生成于 2026-04-10 20:43:12*



## tech

# 技术栈

> 此文件由 HarnessGenJ 自动生成，根据项目文件自动检测
> 检测置信度: 70%

## 主要技术

- **语言**: Python
- **框架**: pytest, Vue, FastAPI, Flask, Django, React
- **包管理器**: poetry

## 版本要求

- **python**: >=3.11

## 数据库

- Redis
- MySQL

## 测试框架

- pytest



## tester

# 测试员 - 专注于质量验证 知识文件

> 此文件由 AGENTS.md 自动派生，请勿手动修改
> 更新时间: 2026-04-10 20:43

---

# AGENTS.md - HarnessGenJ 项目知识库

> 此文件存储项目核心知识，AI 助手启动时自动加载

## 项目信息

- **项目名称**: HarnessGenJ (HGJ) - Harness Engineering with JVM-style Generational Memory
- **技术栈**: Python + pytest + FastAPI + Pydantic
- **当前状态**: 开发中 (v1.3.1)
- **代码行数**: ~15,000 行

## 项目简介

HarnessGenJ 是一个 AI Agent 协作框架，核心特性：

1. **角色驱动协作** - Developer/Tester/PM/Architect/CodeReviewer/BugHunter
2. **JVM 风格记忆管理** - Eden/Survivor/Old/Permanent 分代存储
3. **GAN 对抗质量保证** - 生成器-判别器对抗审查机制
4. **MCP Server 支持** - 21 个工具暴露给 Claude Code

## 核心规范

### 框架使用规范（自举模式）

**本项目自身使用 HGJ 框架进行开发！**

```
用户需求 → harness.develop() → 签发许可 → 执行指令 → complete_task()
```

**必须遵守**：
- 所有代码修改必须通过 `harness.develop()` 或 `harness.fix_bug()`
- 禁止直接编辑代码而不经过框架
- 框架会签发操作许可，AI 只能在许可范围内操作

### 代码规范

- 遵循 PEP 8 规范
- 使用 Pydantic BaseModel 进行数据验证
- 所有公共 API 需要类型注解和 docstring
- 测试覆盖率目标: 80%+

### 工作流程

1. **需求接收** → `harness.receive_request("需求描述")`
2. **开发执行** → `harness.develop("需求描述")`
3. **对抗审查** → 自动执行（框架强制）
4. **文档更新** → 自动执行（框架强制）
5. **任务完成** → `harness.complete_task(task_id, "摘要")`

## 目录结构

```
src/harnessgenj/
├── engine.py          # 主入口 Harness 类
├── roles/             # 角色定义
├── workflow/          # 工作流系统
├── memory/            # JVM 风格记忆管理
├── quality/           # 质量保证（积分、对抗）
├── harness/           # 框架核心组件
│   ├── framework_session.py    # 会话权限管理
│   ├── operation_instruction.py # 操作指令协议
│   └── adversarial.py          # 对抗审查
├── mcp/               # MCP Server
└── notify/            # 用户通知
```

## 常用命令

```python
# 初始化框架（每次对话开始）
from harnessgenj import Harness
harness = Harness.from_project(".")

# 开发功能（返回操作指令）
result = harness.develop("功能描述")

# 修复 Bug
result = harness.fix_bug("问题描述")

# 查看状态
harness.get_status()

# 查看积分排行
harness.get_score_leaderboard()
```

## 重要约定

1. **渐进式披露**: 每个角色只获取最小必要信息
2. **持久化优先**: 所有重要操作自动保存到 .harnessgenj/
3. **文档驱动**: 需求/设计/开发/测试都有对应文档
4. **对抗审查**: 所有代码变更经过 CodeReviewer/BugHunter 审查
5. **积分激励**: 使用框架开发获得积分奖励

## 角色边界

| 角色 | 权限 | 禁止 |
|------|------|------|
| Developer | 编辑代码 | 修改架构设计 |
| CodeReviewer | 只读、审查 | 修改代码 |
| BugHunter | 只读、安全审查 | 修改代码 |
| ProjectManager | 编辑文档、协调 | 修改代码 |
| Architect | 编辑设计文档 | 直接修改代码实现 |

---
*此文件由 HarnessGenJ 自动维护 - 自举模式*


## conventions

# 代码约定

> 此文件由 HarnessGenJ 自动生成，根据技术栈自动适配
> 请遵循项目既有的代码风格

## 编码风格

- 遵循 PEP 8 规范
- 使用类型注解（Type Hints）
- 函数名使用 snake_case
- 类名使用 PascalCase
- 常量使用 UPPER_SNAKE_CASE

## 代码组织

- 使用模块化设计
- 每个 module 应有明确的职责
- 使用 `__init__.py` 导出公共 API

## 文档

- 函数必须有文档字符串（docstring）
- 使用 Google 或 NumPy 风格的 docstring
- 复杂逻辑需要注释说明

## 类型检查

- 推荐使用 mypy 进行静态类型检查
- 使用 `typing` 模块的泛型类型

## 测试约定

- 所有新功能需要添加测试
- 测试文件放在 `test/` 或 `tests/` 目录
- 测试函数名应描述测试场景
- 使用 AAA 模式（Arrange-Act-Assert）

推荐使用: pytest



## tech

# 技术栈

> 此文件由 HarnessGenJ 自动生成，根据项目文件自动检测
> 检测置信度: 70%

## 主要技术

- **语言**: Python
- **框架**: pytest, Vue, FastAPI, Flask, Django, React
- **包管理器**: poetry

## 版本要求

- **python**: >=3.11

## 数据库

- Redis
- MySQL

## 测试框架

- pytest



## workflow

> priority: 60
> auto_inject: True
> roles: all

# 工作流程

## 标准流程
1. 需求分析 (PM)
2. 架构设计 (Architect)
3. 开发实现 (Developer)
4. 测试验证 (Tester)


---

*自动生成于 2026-04-10 20:43:12*



## workflow

> priority: 60
> auto_inject: True
> roles: all

# 工作流程

## 标准流程
1. 需求分析 (PM)
2. 架构设计 (Architect)
3. 开发实现 (Developer)
4. 测试验证 (Tester)


---

*自动生成于 2026-04-10 20:43:13*



## conventions

# 代码约定

> 此文件由 HarnessGenJ 自动生成，根据技术栈自动适配
> 请遵循项目既有的代码风格

## 编码风格

- 遵循 PEP 8 规范
- 使用类型注解（Type Hints）
- 函数名使用 snake_case
- 类名使用 PascalCase
- 常量使用 UPPER_SNAKE_CASE

## 代码组织

- 使用模块化设计
- 每个 module 应有明确的职责
- 使用 `__init__.py` 导出公共 API

## 文档

- 函数必须有文档字符串（docstring）
- 使用 Google 或 NumPy 风格的 docstring
- 复杂逻辑需要注释说明

## 类型检查

- 推荐使用 mypy 进行静态类型检查
- 使用 `typing` 模块的泛型类型

## 测试约定

- 所有新功能需要添加测试
- 测试文件放在 `test/` 或 `tests/` 目录
- 测试函数名应描述测试场景
- 使用 AAA 模式（Arrange-Act-Assert）

推荐使用: pytest



## developer

# 开发者 - 专注于代码实现 知识文件

> 此文件由 AGENTS.md 自动派生，请勿手动修改
> 更新时间: 2026-04-10 20:43

---

# AGENTS.md - HarnessGenJ 项目知识库

> 此文件存储项目核心知识，AI 助手启动时自动加载

## 项目信息

- **项目名称**: HarnessGenJ (HGJ) - Harness Engineering with JVM-style Generational Memory
- **技术栈**: Python + pytest + FastAPI + Pydantic
- **当前状态**: 开发中 (v1.3.1)
- **代码行数**: ~15,000 行

## 项目简介

HarnessGenJ 是一个 AI Agent 协作框架，核心特性：

1. **角色驱动协作** - Developer/Tester/PM/Architect/CodeReviewer/BugHunter
2. **JVM 风格记忆管理** - Eden/Survivor/Old/Permanent 分代存储
3. **GAN 对抗质量保证** - 生成器-判别器对抗审查机制
4. **MCP Server 支持** - 21 个工具暴露给 Claude Code

## 核心规范

### 框架使用规范（自举模式）

**本项目自身使用 HGJ 框架进行开发！**

```
用户需求 → harness.develop() → 签发许可 → 执行指令 → complete_task()
```

**必须遵守**：
- 所有代码修改必须通过 `harness.develop()` 或 `harness.fix_bug()`
- 禁止直接编辑代码而不经过框架
- 框架会签发操作许可，AI 只能在许可范围内操作

### 代码规范

- 遵循 PEP 8 规范
- 使用 Pydantic BaseModel 进行数据验证
- 所有公共 API 需要类型注解和 docstring
- 测试覆盖率目标: 80%+

### 工作流程

1. **需求接收** → `harness.receive_request("需求描述")`
2. **开发执行** → `harness.develop("需求描述")`
3. **对抗审查** → 自动执行（框架强制）
4. **文档更新** → 自动执行（框架强制）
5. **任务完成** → `harness.complete_task(task_id, "摘要")`

## 目录结构

```
src/harnessgenj/
├── engine.py          # 主入口 Harness 类
├── roles/             # 角色定义
├── workflow/          # 工作流系统
├── memory/            # JVM 风格记忆管理
├── quality/           # 质量保证（积分、对抗）
├── harness/           # 框架核心组件
│   ├── framework_session.py    # 会话权限管理
│   ├── operation_instruction.py # 操作指令协议
│   └── adversarial.py          # 对抗审查
├── mcp/               # MCP Server
└── notify/            # 用户通知
```

## 常用命令

```python
# 初始化框架（每次对话开始）
from harnessgenj import Harness
harness = Harness.from_project(".")

# 开发功能（返回操作指令）
result = harness.develop("功能描述")

# 修复 Bug
result = harness.fix_bug("问题描述")

# 查看状态
harness.get_status()

# 查看积分排行
harness.get_score_leaderboard()
```

## 重要约定

1. **渐进式披露**: 每个角色只获取最小必要信息
2. **持久化优先**: 所有重要操作自动保存到 .harnessgenj/
3. **文档驱动**: 需求/设计/开发/测试都有对应文档
4. **对抗审查**: 所有代码变更经过 CodeReviewer/BugHunter 审查
5. **积分激励**: 使用框架开发获得积分奖励

## 角色边界

| 角色 | 权限 | 禁止 |
|------|------|------|
| Developer | 编辑代码 | 修改架构设计 |
| CodeReviewer | 只读、审查 | 修改代码 |
| BugHunter | 只读、安全审查 | 修改代码 |
| ProjectManager | 编辑文档、协调 | 修改代码 |
| Architect | 编辑设计文档 | 直接修改代码实现 |

---
*此文件由 HarnessGenJ 自动维护 - 自举模式*


## architect

# 架构师 - 专注于系统设计 知识文件

> 此文件由 AGENTS.md 自动派生，请勿手动修改
> 更新时间: 2026-04-10 20:43

---

# AGENTS.md - HarnessGenJ 项目知识库

> 此文件存储项目核心知识，AI 助手启动时自动加载

## 项目信息

- **项目名称**: HarnessGenJ (HGJ) - Harness Engineering with JVM-style Generational Memory
- **技术栈**: Python + pytest + FastAPI + Pydantic
- **当前状态**: 开发中 (v1.3.1)
- **代码行数**: ~15,000 行

## 项目简介

HarnessGenJ 是一个 AI Agent 协作框架，核心特性：

1. **角色驱动协作** - Developer/Tester/PM/Architect/CodeReviewer/BugHunter
2. **JVM 风格记忆管理** - Eden/Survivor/Old/Permanent 分代存储
3. **GAN 对抗质量保证** - 生成器-判别器对抗审查机制
4. **MCP Server 支持** - 21 个工具暴露给 Claude Code

## 核心规范

### 框架使用规范（自举模式）

**本项目自身使用 HGJ 框架进行开发！**

```
用户需求 → harness.develop() → 签发许可 → 执行指令 → complete_task()
```

**必须遵守**：
- 所有代码修改必须通过 `harness.develop()` 或 `harness.fix_bug()`
- 禁止直接编辑代码而不经过框架
- 框架会签发操作许可，AI 只能在许可范围内操作

### 代码规范

- 遵循 PEP 8 规范
- 使用 Pydantic BaseModel 进行数据验证
- 所有公共 API 需要类型注解和 docstring
- 测试覆盖率目标: 80%+

### 工作流程

1. **需求接收** → `harness.receive_request("需求描述")`
2. **开发执行** → `harness.develop("需求描述")`
3. **对抗审查** → 自动执行（框架强制）
4. **文档更新** → 自动执行（框架强制）
5. **任务完成** → `harness.complete_task(task_id, "摘要")`

## 目录结构

```
src/harnessgenj/
├── engine.py          # 主入口 Harness 类
├── roles/             # 角色定义
├── workflow/          # 工作流系统
├── memory/            # JVM 风格记忆管理
├── quality/           # 质量保证（积分、对抗）
├── harness/           # 框架核心组件
│   ├── framework_session.py    # 会话权限管理
│   ├── operation_instruction.py # 操作指令协议
│   └── adversarial.py          # 对抗审查
├── mcp/               # MCP Server
└── notify/            # 用户通知
```

## 常用命令

```python
# 初始化框架（每次对话开始）
from harnessgenj import Harness
harness = Harness.from_project(".")

# 开发功能（返回操作指令）
result = harness.develop("功能描述")

# 修复 Bug
result = harness.fix_bug("问题描述")

# 查看状态
harness.get_status()

# 查看积分排行
harness.get_score_leaderboard()
```

## 重要约定

1. **渐进式披露**: 每个角色只获取最小必要信息
2. **持久化优先**: 所有重要操作自动保存到 .harnessgenj/
3. **文档驱动**: 需求/设计/开发/测试都有对应文档
4. **对抗审查**: 所有代码变更经过 CodeReviewer/BugHunter 审查
5. **积分激励**: 使用框架开发获得积分奖励

## 角色边界

| 角色 | 权限 | 禁止 |
|------|------|------|
| Developer | 编辑代码 | 修改架构设计 |
| CodeReviewer | 只读、审查 | 修改代码 |
| BugHunter | 只读、安全审查 | 修改代码 |
| ProjectManager | 编辑文档、协调 | 修改代码 |
| Architect | 编辑设计文档 | 直接修改代码实现 |

---
*此文件由 HarnessGenJ 自动维护 - 自举模式*


## conventions

# 代码约定

> 此文件由 HarnessGenJ 自动生成，根据技术栈自动适配
> 请遵循项目既有的代码风格

## 编码风格

- 遵循 PEP 8 规范
- 使用类型注解（Type Hints）
- 函数名使用 snake_case
- 类名使用 PascalCase
- 常量使用 UPPER_SNAKE_CASE

## 代码组织

- 使用模块化设计
- 每个 module 应有明确的职责
- 使用 `__init__.py` 导出公共 API

## 文档

- 函数必须有文档字符串（docstring）
- 使用 Google 或 NumPy 风格的 docstring
- 复杂逻辑需要注释说明

## 类型检查

- 推荐使用 mypy 进行静态类型检查
- 使用 `typing` 模块的泛型类型

## 测试约定

- 所有新功能需要添加测试
- 测试文件放在 `test/` 或 `tests/` 目录
- 测试函数名应描述测试场景
- 使用 AAA 模式（Arrange-Act-Assert）

推荐使用: pytest



## tech

# 技术栈

> 此文件由 HarnessGenJ 自动生成，根据项目文件自动检测
> 检测置信度: 70%

## 主要技术

- **语言**: Python
- **框架**: pytest, Vue, FastAPI, Flask, Django, React
- **包管理器**: poetry

## 版本要求

- **python**: >=3.11

## 数据库

- Redis
- MySQL

## 测试框架

- pytest



## workflow

> priority: 60
> auto_inject: True
> roles: all

# 工作流程

## 标准流程
1. 需求分析 (PM)
2. 架构设计 (Architect)
3. 开发实现 (Developer)
4. 测试验证 (Tester)


---

*自动生成于 2026-04-10 20:43:12*



## conventions

# 代码约定

> 此文件由 HarnessGenJ 自动生成，根据技术栈自动适配
> 请遵循项目既有的代码风格

## 编码风格

- 遵循 PEP 8 规范
- 使用类型注解（Type Hints）
- 函数名使用 snake_case
- 类名使用 PascalCase
- 常量使用 UPPER_SNAKE_CASE

## 代码组织

- 使用模块化设计
- 每个 module 应有明确的职责
- 使用 `__init__.py` 导出公共 API

## 文档

- 函数必须有文档字符串（docstring）
- 使用 Google 或 NumPy 风格的 docstring
- 复杂逻辑需要注释说明

## 类型检查

- 推荐使用 mypy 进行静态类型检查
- 使用 `typing` 模块的泛型类型

## 测试约定

- 所有新功能需要添加测试
- 测试文件放在 `test/` 或 `tests/` 目录
- 测试函数名应描述测试场景
- 使用 AAA 模式（Arrange-Act-Assert）

推荐使用: pytest



## developer

# 开发者 - 专注于代码实现 知识文件

> 此文件由 AGENTS.md 自动派生，请勿手动修改
> 更新时间: 2026-04-10 20:43

---

# AGENTS.md - HarnessGenJ 项目知识库

> 此文件存储项目核心知识，AI 助手启动时自动加载

## 项目信息

- **项目名称**: HarnessGenJ (HGJ) - Harness Engineering with JVM-style Generational Memory
- **技术栈**: Python + pytest + FastAPI + Pydantic
- **当前状态**: 开发中 (v1.3.1)
- **代码行数**: ~15,000 行

## 项目简介

HarnessGenJ 是一个 AI Agent 协作框架，核心特性：

1. **角色驱动协作** - Developer/Tester/PM/Architect/CodeReviewer/BugHunter
2. **JVM 风格记忆管理** - Eden/Survivor/Old/Permanent 分代存储
3. **GAN 对抗质量保证** - 生成器-判别器对抗审查机制
4. **MCP Server 支持** - 21 个工具暴露给 Claude Code

## 核心规范

### 框架使用规范（自举模式）

**本项目自身使用 HGJ 框架进行开发！**

```
用户需求 → harness.develop() → 签发许可 → 执行指令 → complete_task()
```

**必须遵守**：
- 所有代码修改必须通过 `harness.develop()` 或 `harness.fix_bug()`
- 禁止直接编辑代码而不经过框架
- 框架会签发操作许可，AI 只能在许可范围内操作

### 代码规范

- 遵循 PEP 8 规范
- 使用 Pydantic BaseModel 进行数据验证
- 所有公共 API 需要类型注解和 docstring
- 测试覆盖率目标: 80%+

### 工作流程

1. **需求接收** → `harness.receive_request("需求描述")`
2. **开发执行** → `harness.develop("需求描述")`
3. **对抗审查** → 自动执行（框架强制）
4. **文档更新** → 自动执行（框架强制）
5. **任务完成** → `harness.complete_task(task_id, "摘要")`

## 目录结构

```
src/harnessgenj/
├── engine.py          # 主入口 Harness 类
├── roles/             # 角色定义
├── workflow/          # 工作流系统
├── memory/            # JVM 风格记忆管理
├── quality/           # 质量保证（积分、对抗）
├── harness/           # 框架核心组件
│   ├── framework_session.py    # 会话权限管理
│   ├── operation_instruction.py # 操作指令协议
│   └── adversarial.py          # 对抗审查
├── mcp/               # MCP Server
└── notify/            # 用户通知
```

## 常用命令

```python
# 初始化框架（每次对话开始）
from harnessgenj import Harness
harness = Harness.from_project(".")

# 开发功能（返回操作指令）
result = harness.develop("功能描述")

# 修复 Bug
result = harness.fix_bug("问题描述")

# 查看状态
harness.get_status()

# 查看积分排行
harness.get_score_leaderboard()
```

## 重要约定

1. **渐进式披露**: 每个角色只获取最小必要信息
2. **持久化优先**: 所有重要操作自动保存到 .harnessgenj/
3. **文档驱动**: 需求/设计/开发/测试都有对应文档
4. **对抗审查**: 所有代码变更经过 CodeReviewer/BugHunter 审查
5. **积分激励**: 使用框架开发获得积分奖励

## 角色边界

| 角色 | 权限 | 禁止 |
|------|------|------|
| Developer | 编辑代码 | 修改架构设计 |
| CodeReviewer | 只读、审查 | 修改代码 |
| BugHunter | 只读、安全审查 | 修改代码 |
| ProjectManager | 编辑文档、协调 | 修改代码 |
| Architect | 编辑设计文档 | 直接修改代码实现 |

---
*此文件由 HarnessGenJ 自动维护 - 自举模式*


## conventions

# 代码约定

> 此文件由 HarnessGenJ 自动生成，根据技术栈自动适配
> 请遵循项目既有的代码风格

## 编码风格

- 遵循 PEP 8 规范
- 使用类型注解（Type Hints）
- 函数名使用 snake_case
- 类名使用 PascalCase
- 常量使用 UPPER_SNAKE_CASE

## 代码组织

- 使用模块化设计
- 每个 module 应有明确的职责
- 使用 `__init__.py` 导出公共 API

## 文档

- 函数必须有文档字符串（docstring）
- 使用 Google 或 NumPy 风格的 docstring
- 复杂逻辑需要注释说明

## 类型检查

- 推荐使用 mypy 进行静态类型检查
- 使用 `typing` 模块的泛型类型

## 测试约定

- 所有新功能需要添加测试
- 测试文件放在 `test/` 或 `tests/` 目录
- 测试函数名应描述测试场景
- 使用 AAA 模式（Arrange-Act-Assert）

推荐使用: pytest



## tech

# 技术栈

> 此文件由 HarnessGenJ 自动生成，根据项目文件自动检测
> 检测置信度: 70%

## 主要技术

- **语言**: Python
- **框架**: pytest, Vue, FastAPI, Flask, Django, React
- **包管理器**: poetry

## 版本要求

- **python**: >=3.11

## 数据库

- Redis
- MySQL

## 测试框架

- pytest



## workflow

> priority: 60
> auto_inject: True
> roles: all

# 工作流程

## 标准流程
1. 需求分析 (PM)
2. 架构设计 (Architect)
3. 开发实现 (Developer)
4. 测试验证 (Tester)


---

*自动生成于 2026-04-10 20:43:12*



## product_manager

# 产品经理 - 专注于需求管理 知识文件

> 此文件由 AGENTS.md 自动派生，请勿手动修改
> 更新时间: 2026-04-10 20:43

---

# AGENTS.md - HarnessGenJ 项目知识库

> 此文件存储项目核心知识，AI 助手启动时自动加载

## 项目信息

- **项目名称**: HarnessGenJ (HGJ) - Harness Engineering with JVM-style Generational Memory
- **技术栈**: Python + pytest + FastAPI + Pydantic
- **当前状态**: 开发中 (v1.3.1)
- **代码行数**: ~15,000 行

## 项目简介

HarnessGenJ 是一个 AI Agent 协作框架，核心特性：

1. **角色驱动协作** - Developer/Tester/PM/Architect/CodeReviewer/BugHunter
2. **JVM 风格记忆管理** - Eden/Survivor/Old/Permanent 分代存储
3. **GAN 对抗质量保证** - 生成器-判别器对抗审查机制
4. **MCP Server 支持** - 21 个工具暴露给 Claude Code

## 核心规范

### 框架使用规范（自举模式）

**本项目自身使用 HGJ 框架进行开发！**

```
用户需求 → harness.develop() → 签发许可 → 执行指令 → complete_task()
```

**必须遵守**：
- 所有代码修改必须通过 `harness.develop()` 或 `harness.fix_bug()`
- 禁止直接编辑代码而不经过框架
- 框架会签发操作许可，AI 只能在许可范围内操作

### 代码规范

- 遵循 PEP 8 规范
- 使用 Pydantic BaseModel 进行数据验证
- 所有公共 API 需要类型注解和 docstring
- 测试覆盖率目标: 80%+

### 工作流程

1. **需求接收** → `harness.receive_request("需求描述")`
2. **开发执行** → `harness.develop("需求描述")`
3. **对抗审查** → 自动执行（框架强制）
4. **文档更新** → 自动执行（框架强制）
5. **任务完成** → `harness.complete_task(task_id, "摘要")`

## 目录结构

```
src/harnessgenj/
├── engine.py          # 主入口 Harness 类
├── roles/             # 角色定义
├── workflow/          # 工作流系统
├── memory/            # JVM 风格记忆管理
├── quality/           # 质量保证（积分、对抗）
├── harness/           # 框架核心组件
│   ├── framework_session.py    # 会话权限管理
│   ├── operation_instruction.py # 操作指令协议
│   └── adversarial.py          # 对抗审查
├── mcp/               # MCP Server
└── notify/            # 用户通知
```

## 常用命令

```python
# 初始化框架（每次对话开始）
from harnessgenj import Harness
harness = Harness.from_project(".")

# 开发功能（返回操作指令）
result = harness.develop("功能描述")

# 修复 Bug
result = harness.fix_bug("问题描述")

# 查看状态
harness.get_status()

# 查看积分排行
harness.get_score_leaderboard()
```

## 重要约定

1. **渐进式披露**: 每个角色只获取最小必要信息
2. **持久化优先**: 所有重要操作自动保存到 .harnessgenj/
3. **文档驱动**: 需求/设计/开发/测试都有对应文档
4. **对抗审查**: 所有代码变更经过 CodeReviewer/BugHunter 审查
5. **积分激励**: 使用框架开发获得积分奖励

## 角色边界

| 角色 | 权限 | 禁止 |
|------|------|------|
| Developer | 编辑代码 | 修改架构设计 |
| CodeReviewer | 只读、审查 | 修改代码 |
| BugHunter | 只读、安全审查 | 修改代码 |
| ProjectManager | 编辑文档、协调 | 修改代码 |
| Architect | 编辑设计文档 | 直接修改代码实现 |

---
*此文件由 HarnessGenJ 自动维护 - 自举模式*


## conventions

# 代码约定

> 此文件由 HarnessGenJ 自动生成，根据技术栈自动适配
> 请遵循项目既有的代码风格

## 编码风格

- 遵循 PEP 8 规范
- 使用类型注解（Type Hints）
- 函数名使用 snake_case
- 类名使用 PascalCase
- 常量使用 UPPER_SNAKE_CASE

## 代码组织

- 使用模块化设计
- 每个 module 应有明确的职责
- 使用 `__init__.py` 导出公共 API

## 文档

- 函数必须有文档字符串（docstring）
- 使用 Google 或 NumPy 风格的 docstring
- 复杂逻辑需要注释说明

## 类型检查

- 推荐使用 mypy 进行静态类型检查
- 使用 `typing` 模块的泛型类型

## 测试约定

- 所有新功能需要添加测试
- 测试文件放在 `test/` 或 `tests/` 目录
- 测试函数名应描述测试场景
- 使用 AAA 模式（Arrange-Act-Assert）

推荐使用: pytest



## tech

# 技术栈

> 此文件由 HarnessGenJ 自动生成，根据项目文件自动检测
> 检测置信度: 70%

## 主要技术

- **语言**: Python
- **框架**: pytest, Vue, FastAPI, Flask, Django, React
- **包管理器**: poetry

## 版本要求

- **python**: >=3.11

## 数据库

- Redis
- MySQL

## 测试框架

- pytest



## workflow

> priority: 60
> auto_inject: True
> roles: all

# 工作流程

## 标准流程
1. 需求分析 (PM)
2. 架构设计 (Architect)
3. 开发实现 (Developer)
4. 测试验证 (Tester)


---

*自动生成于 2026-04-10 20:43:12*



## tech

# 技术栈

> 此文件由 HarnessGenJ 自动生成，根据项目文件自动检测
> 检测置信度: 70%

## 主要技术

- **语言**: Python
- **框架**: pytest, Vue, FastAPI, Flask, Django, React
- **包管理器**: poetry

## 版本要求

- **python**: >=3.11

## 数据库

- Redis
- MySQL

## 测试框架

- pytest



## tester

# 测试员 - 专注于质量验证 知识文件

> 此文件由 AGENTS.md 自动派生，请勿手动修改
> 更新时间: 2026-04-10 20:43

---

# AGENTS.md - HarnessGenJ 项目知识库

> 此文件存储项目核心知识，AI 助手启动时自动加载

## 项目信息

- **项目名称**: HarnessGenJ (HGJ) - Harness Engineering with JVM-style Generational Memory
- **技术栈**: Python + pytest + FastAPI + Pydantic
- **当前状态**: 开发中 (v1.3.1)
- **代码行数**: ~15,000 行

## 项目简介

HarnessGenJ 是一个 AI Agent 协作框架，核心特性：

1. **角色驱动协作** - Developer/Tester/PM/Architect/CodeReviewer/BugHunter
2. **JVM 风格记忆管理** - Eden/Survivor/Old/Permanent 分代存储
3. **GAN 对抗质量保证** - 生成器-判别器对抗审查机制
4. **MCP Server 支持** - 21 个工具暴露给 Claude Code

## 核心规范

### 框架使用规范（自举模式）

**本项目自身使用 HGJ 框架进行开发！**

```
用户需求 → harness.develop() → 签发许可 → 执行指令 → complete_task()
```

**必须遵守**：
- 所有代码修改必须通过 `harness.develop()` 或 `harness.fix_bug()`
- 禁止直接编辑代码而不经过框架
- 框架会签发操作许可，AI 只能在许可范围内操作

### 代码规范

- 遵循 PEP 8 规范
- 使用 Pydantic BaseModel 进行数据验证
- 所有公共 API 需要类型注解和 docstring
- 测试覆盖率目标: 80%+

### 工作流程

1. **需求接收** → `harness.receive_request("需求描述")`
2. **开发执行** → `harness.develop("需求描述")`
3. **对抗审查** → 自动执行（框架强制）
4. **文档更新** → 自动执行（框架强制）
5. **任务完成** → `harness.complete_task(task_id, "摘要")`

## 目录结构

```
src/harnessgenj/
├── engine.py          # 主入口 Harness 类
├── roles/             # 角色定义
├── workflow/          # 工作流系统
├── memory/            # JVM 风格记忆管理
├── quality/           # 质量保证（积分、对抗）
├── harness/           # 框架核心组件
│   ├── framework_session.py    # 会话权限管理
│   ├── operation_instruction.py # 操作指令协议
│   └── adversarial.py          # 对抗审查
├── mcp/               # MCP Server
└── notify/            # 用户通知
```

## 常用命令

```python
# 初始化框架（每次对话开始）
from harnessgenj import Harness
harness = Harness.from_project(".")

# 开发功能（返回操作指令）
result = harness.develop("功能描述")

# 修复 Bug
result = harness.fix_bug("问题描述")

# 查看状态
harness.get_status()

# 查看积分排行
harness.get_score_leaderboard()
```

## 重要约定

1. **渐进式披露**: 每个角色只获取最小必要信息
2. **持久化优先**: 所有重要操作自动保存到 .harnessgenj/
3. **文档驱动**: 需求/设计/开发/测试都有对应文档
4. **对抗审查**: 所有代码变更经过 CodeReviewer/BugHunter 审查
5. **积分激励**: 使用框架开发获得积分奖励

## 角色边界

| 角色 | 权限 | 禁止 |
|------|------|------|
| Developer | 编辑代码 | 修改架构设计 |
| CodeReviewer | 只读、审查 | 修改代码 |
| BugHunter | 只读、安全审查 | 修改代码 |
| ProjectManager | 编辑文档、协调 | 修改代码 |
| Architect | 编辑设计文档 | 直接修改代码实现 |

---
*此文件由 HarnessGenJ 自动维护 - 自举模式*


## conventions

# 代码约定

> 此文件由 HarnessGenJ 自动生成，根据技术栈自动适配
> 请遵循项目既有的代码风格

## 编码风格

- 遵循 PEP 8 规范
- 使用类型注解（Type Hints）
- 函数名使用 snake_case
- 类名使用 PascalCase
- 常量使用 UPPER_SNAKE_CASE

## 代码组织

- 使用模块化设计
- 每个 module 应有明确的职责
- 使用 `__init__.py` 导出公共 API

## 文档

- 函数必须有文档字符串（docstring）
- 使用 Google 或 NumPy 风格的 docstring
- 复杂逻辑需要注释说明

## 类型检查

- 推荐使用 mypy 进行静态类型检查
- 使用 `typing` 模块的泛型类型

## 测试约定

- 所有新功能需要添加测试
- 测试文件放在 `test/` 或 `tests/` 目录
- 测试函数名应描述测试场景
- 使用 AAA 模式（Arrange-Act-Assert）

推荐使用: pytest



## tech

# 技术栈

> 此文件由 HarnessGenJ 自动生成，根据项目文件自动检测
> 检测置信度: 70%

## 主要技术

- **语言**: Python
- **框架**: pytest, Vue, FastAPI, Flask, Django, React
- **包管理器**: poetry

## 版本要求

- **python**: >=3.11

## 数据库

- Redis
- MySQL

## 测试框架

- pytest



## workflow

> priority: 60
> auto_inject: True
> roles: all

# 工作流程

## 标准流程
1. 需求分析 (PM)
2. 架构设计 (Architect)
3. 开发实现 (Developer)
4. 测试验证 (Tester)


---

*自动生成于 2026-04-10 20:43:12*



## workflow

> priority: 60
> auto_inject: True
> roles: all

# 工作流程

## 标准流程
1. 需求分析 (PM)
2. 架构设计 (Architect)
3. 开发实现 (Developer)
4. 测试验证 (Tester)


---

*自动生成于 2026-04-10 20:43:13*



## product_manager

# 产品经理 - 专注于需求管理 知识文件

> 此文件由 AGENTS.md 自动派生，请勿手动修改
> 更新时间: 2026-04-10 20:43

---

# AGENTS.md - HarnessGenJ 项目知识库

> 此文件存储项目核心知识，AI 助手启动时自动加载

## 项目信息

- **项目名称**: HarnessGenJ (HGJ) - Harness Engineering with JVM-style Generational Memory
- **技术栈**: Python + pytest + FastAPI + Pydantic
- **当前状态**: 开发中 (v1.3.1)
- **代码行数**: ~15,000 行

## 项目简介

HarnessGenJ 是一个 AI Agent 协作框架，核心特性：

1. **角色驱动协作** - Developer/Tester/PM/Architect/CodeReviewer/BugHunter
2. **JVM 风格记忆管理** - Eden/Survivor/Old/Permanent 分代存储
3. **GAN 对抗质量保证** - 生成器-判别器对抗审查机制
4. **MCP Server 支持** - 21 个工具暴露给 Claude Code

## 核心规范

### 框架使用规范（自举模式）

**本项目自身使用 HGJ 框架进行开发！**

```
用户需求 → harness.develop() → 签发许可 → 执行指令 → complete_task()
```

**必须遵守**：
- 所有代码修改必须通过 `harness.develop()` 或 `harness.fix_bug()`
- 禁止直接编辑代码而不经过框架
- 框架会签发操作许可，AI 只能在许可范围内操作

### 代码规范

- 遵循 PEP 8 规范
- 使用 Pydantic BaseModel 进行数据验证
- 所有公共 API 需要类型注解和 docstring
- 测试覆盖率目标: 80%+

### 工作流程

1. **需求接收** → `harness.receive_request("需求描述")`
2. **开发执行** → `harness.develop("需求描述")`
3. **对抗审查** → 自动执行（框架强制）
4. **文档更新** → 自动执行（框架强制）
5. **任务完成** → `harness.complete_task(task_id, "摘要")`

## 目录结构

```
src/harnessgenj/
├── engine.py          # 主入口 Harness 类
├── roles/             # 角色定义
├── workflow/          # 工作流系统
├── memory/            # JVM 风格记忆管理
├── quality/           # 质量保证（积分、对抗）
├── harness/           # 框架核心组件
│   ├── framework_session.py    # 会话权限管理
│   ├── operation_instruction.py # 操作指令协议
│   └── adversarial.py          # 对抗审查
├── mcp/               # MCP Server
└── notify/            # 用户通知
```

## 常用命令

```python
# 初始化框架（每次对话开始）
from harnessgenj import Harness
harness = Harness.from_project(".")

# 开发功能（返回操作指令）
result = harness.develop("功能描述")

# 修复 Bug
result = harness.fix_bug("问题描述")

# 查看状态
harness.get_status()

# 查看积分排行
harness.get_score_leaderboard()
```

## 重要约定

1. **渐进式披露**: 每个角色只获取最小必要信息
2. **持久化优先**: 所有重要操作自动保存到 .harnessgenj/
3. **文档驱动**: 需求/设计/开发/测试都有对应文档
4. **对抗审查**: 所有代码变更经过 CodeReviewer/BugHunter 审查
5. **积分激励**: 使用框架开发获得积分奖励

## 角色边界

| 角色 | 权限 | 禁止 |
|------|------|------|
| Developer | 编辑代码 | 修改架构设计 |
| CodeReviewer | 只读、审查 | 修改代码 |
| BugHunter | 只读、安全审查 | 修改代码 |
| ProjectManager | 编辑文档、协调 | 修改代码 |
| Architect | 编辑设计文档 | 直接修改代码实现 |

---
*此文件由 HarnessGenJ 自动维护 - 自举模式*


## architect

# 架构师 - 专注于系统设计 知识文件

> 此文件由 AGENTS.md 自动派生，请勿手动修改
> 更新时间: 2026-04-10 20:43

---

# AGENTS.md - HarnessGenJ 项目知识库

> 此文件存储项目核心知识，AI 助手启动时自动加载

## 项目信息

- **项目名称**: HarnessGenJ (HGJ) - Harness Engineering with JVM-style Generational Memory
- **技术栈**: Python + pytest + FastAPI + Pydantic
- **当前状态**: 开发中 (v1.3.1)
- **代码行数**: ~15,000 行

## 项目简介

HarnessGenJ 是一个 AI Agent 协作框架，核心特性：

1. **角色驱动协作** - Developer/Tester/PM/Architect/CodeReviewer/BugHunter
2. **JVM 风格记忆管理** - Eden/Survivor/Old/Permanent 分代存储
3. **GAN 对抗质量保证** - 生成器-判别器对抗审查机制
4. **MCP Server 支持** - 21 个工具暴露给 Claude Code

## 核心规范

### 框架使用规范（自举模式）

**本项目自身使用 HGJ 框架进行开发！**

```
用户需求 → harness.develop() → 签发许可 → 执行指令 → complete_task()
```

**必须遵守**：
- 所有代码修改必须通过 `harness.develop()` 或 `harness.fix_bug()`
- 禁止直接编辑代码而不经过框架
- 框架会签发操作许可，AI 只能在许可范围内操作

### 代码规范

- 遵循 PEP 8 规范
- 使用 Pydantic BaseModel 进行数据验证
- 所有公共 API 需要类型注解和 docstring
- 测试覆盖率目标: 80%+

### 工作流程

1. **需求接收** → `harness.receive_request("需求描述")`
2. **开发执行** → `harness.develop("需求描述")`
3. **对抗审查** → 自动执行（框架强制）
4. **文档更新** → 自动执行（框架强制）
5. **任务完成** → `harness.complete_task(task_id, "摘要")`

## 目录结构

```
src/harnessgenj/
├── engine.py          # 主入口 Harness 类
├── roles/             # 角色定义
├── workflow/          # 工作流系统
├── memory/            # JVM 风格记忆管理
├── quality/           # 质量保证（积分、对抗）
├── harness/           # 框架核心组件
│   ├── framework_session.py    # 会话权限管理
│   ├── operation_instruction.py # 操作指令协议
│   └── adversarial.py          # 对抗审查
├── mcp/               # MCP Server
└── notify/            # 用户通知
```

## 常用命令

```python
# 初始化框架（每次对话开始）
from harnessgenj import Harness
harness = Harness.from_project(".")

# 开发功能（返回操作指令）
result = harness.develop("功能描述")

# 修复 Bug
result = harness.fix_bug("问题描述")

# 查看状态
harness.get_status()

# 查看积分排行
harness.get_score_leaderboard()
```

## 重要约定

1. **渐进式披露**: 每个角色只获取最小必要信息
2. **持久化优先**: 所有重要操作自动保存到 .harnessgenj/
3. **文档驱动**: 需求/设计/开发/测试都有对应文档
4. **对抗审查**: 所有代码变更经过 CodeReviewer/BugHunter 审查
5. **积分激励**: 使用框架开发获得积分奖励

## 角色边界

| 角色 | 权限 | 禁止 |
|------|------|------|
| Developer | 编辑代码 | 修改架构设计 |
| CodeReviewer | 只读、审查 | 修改代码 |
| BugHunter | 只读、安全审查 | 修改代码 |
| ProjectManager | 编辑文档、协调 | 修改代码 |
| Architect | 编辑设计文档 | 直接修改代码实现 |

---
*此文件由 HarnessGenJ 自动维护 - 自举模式*


## conventions

# 代码约定

> 此文件由 HarnessGenJ 自动生成，根据技术栈自动适配
> 请遵循项目既有的代码风格

## 编码风格

- 遵循 PEP 8 规范
- 使用类型注解（Type Hints）
- 函数名使用 snake_case
- 类名使用 PascalCase
- 常量使用 UPPER_SNAKE_CASE

## 代码组织

- 使用模块化设计
- 每个 module 应有明确的职责
- 使用 `__init__.py` 导出公共 API

## 文档

- 函数必须有文档字符串（docstring）
- 使用 Google 或 NumPy 风格的 docstring
- 复杂逻辑需要注释说明

## 类型检查

- 推荐使用 mypy 进行静态类型检查
- 使用 `typing` 模块的泛型类型

## 测试约定

- 所有新功能需要添加测试
- 测试文件放在 `test/` 或 `tests/` 目录
- 测试函数名应描述测试场景
- 使用 AAA 模式（Arrange-Act-Assert）

推荐使用: pytest



## tech

# 技术栈

> 此文件由 HarnessGenJ 自动生成，根据项目文件自动检测
> 检测置信度: 70%

## 主要技术

- **语言**: Python
- **框架**: pytest, Vue, FastAPI, Flask, Django, React
- **包管理器**: poetry

## 版本要求

- **python**: >=3.11

## 数据库

- Redis
- MySQL

## 测试框架

- pytest



## workflow

> priority: 60
> auto_inject: True
> roles: all

# 工作流程

## 标准流程
1. 需求分析 (PM)
2. 架构设计 (Architect)
3. 开发实现 (Developer)
4. 测试验证 (Tester)


---

*自动生成于 2026-04-10 20:43:12*



## conventions

# 代码约定

> 此文件由 HarnessGenJ 自动生成，根据技术栈自动适配
> 请遵循项目既有的代码风格

## 编码风格

- 遵循 PEP 8 规范
- 使用类型注解（Type Hints）
- 函数名使用 snake_case
- 类名使用 PascalCase
- 常量使用 UPPER_SNAKE_CASE

## 代码组织

- 使用模块化设计
- 每个 module 应有明确的职责
- 使用 `__init__.py` 导出公共 API

## 文档

- 函数必须有文档字符串（docstring）
- 使用 Google 或 NumPy 风格的 docstring
- 复杂逻辑需要注释说明

## 类型检查

- 推荐使用 mypy 进行静态类型检查
- 使用 `typing` 模块的泛型类型

## 测试约定

- 所有新功能需要添加测试
- 测试文件放在 `test/` 或 `tests/` 目录
- 测试函数名应描述测试场景
- 使用 AAA 模式（Arrange-Act-Assert）

推荐使用: pytest



## developer

# 开发者 - 专注于代码实现 知识文件

> 此文件由 AGENTS.md 自动派生，请勿手动修改
> 更新时间: 2026-04-10 20:43

---

# AGENTS.md - HarnessGenJ 项目知识库

> 此文件存储项目核心知识，AI 助手启动时自动加载

## 项目信息

- **项目名称**: HarnessGenJ (HGJ) - Harness Engineering with JVM-style Generational Memory
- **技术栈**: Python + pytest + FastAPI + Pydantic
- **当前状态**: 开发中 (v1.3.1)
- **代码行数**: ~15,000 行

## 项目简介

HarnessGenJ 是一个 AI Agent 协作框架，核心特性：

1. **角色驱动协作** - Developer/Tester/PM/Architect/CodeReviewer/BugHunter
2. **JVM 风格记忆管理** - Eden/Survivor/Old/Permanent 分代存储
3. **GAN 对抗质量保证** - 生成器-判别器对抗审查机制
4. **MCP Server 支持** - 21 个工具暴露给 Claude Code

## 核心规范

### 框架使用规范（自举模式）

**本项目自身使用 HGJ 框架进行开发！**

```
用户需求 → harness.develop() → 签发许可 → 执行指令 → complete_task()
```

**必须遵守**：
- 所有代码修改必须通过 `harness.develop()` 或 `harness.fix_bug()`
- 禁止直接编辑代码而不经过框架
- 框架会签发操作许可，AI 只能在许可范围内操作

### 代码规范

- 遵循 PEP 8 规范
- 使用 Pydantic BaseModel 进行数据验证
- 所有公共 API 需要类型注解和 docstring
- 测试覆盖率目标: 80%+

### 工作流程

1. **需求接收** → `harness.receive_request("需求描述")`
2. **开发执行** → `harness.develop("需求描述")`
3. **对抗审查** → 自动执行（框架强制）
4. **文档更新** → 自动执行（框架强制）
5. **任务完成** → `harness.complete_task(task_id, "摘要")`

## 目录结构

```
src/harnessgenj/
├── engine.py          # 主入口 Harness 类
├── roles/             # 角色定义
├── workflow/          # 工作流系统
├── memory/            # JVM 风格记忆管理
├── quality/           # 质量保证（积分、对抗）
├── harness/           # 框架核心组件
│   ├── framework_session.py    # 会话权限管理
│   ├── operation_instruction.py # 操作指令协议
│   └── adversarial.py          # 对抗审查
├── mcp/               # MCP Server
└── notify/            # 用户通知
```

## 常用命令

```python
# 初始化框架（每次对话开始）
from harnessgenj import Harness
harness = Harness.from_project(".")

# 开发功能（返回操作指令）
result = harness.develop("功能描述")

# 修复 Bug
result = harness.fix_bug("问题描述")

# 查看状态
harness.get_status()

# 查看积分排行
harness.get_score_leaderboard()
```

## 重要约定

1. **渐进式披露**: 每个角色只获取最小必要信息
2. **持久化优先**: 所有重要操作自动保存到 .harnessgenj/
3. **文档驱动**: 需求/设计/开发/测试都有对应文档
4. **对抗审查**: 所有代码变更经过 CodeReviewer/BugHunter 审查
5. **积分激励**: 使用框架开发获得积分奖励

## 角色边界

| 角色 | 权限 | 禁止 |
|------|------|------|
| Developer | 编辑代码 | 修改架构设计 |
| CodeReviewer | 只读、审查 | 修改代码 |
| BugHunter | 只读、安全审查 | 修改代码 |
| ProjectManager | 编辑文档、协调 | 修改代码 |
| Architect | 编辑设计文档 | 直接修改代码实现 |

---
*此文件由 HarnessGenJ 自动维护 - 自举模式*


## conventions

# 代码约定

> 此文件由 HarnessGenJ 自动生成，根据技术栈自动适配
> 请遵循项目既有的代码风格

## 编码风格

- 遵循 PEP 8 规范
- 使用类型注解（Type Hints）
- 函数名使用 snake_case
- 类名使用 PascalCase
- 常量使用 UPPER_SNAKE_CASE

## 代码组织

- 使用模块化设计
- 每个 module 应有明确的职责
- 使用 `__init__.py` 导出公共 API

## 文档

- 函数必须有文档字符串（docstring）
- 使用 Google 或 NumPy 风格的 docstring
- 复杂逻辑需要注释说明

## 类型检查

- 推荐使用 mypy 进行静态类型检查
- 使用 `typing` 模块的泛型类型

## 测试约定

- 所有新功能需要添加测试
- 测试文件放在 `test/` 或 `tests/` 目录
- 测试函数名应描述测试场景
- 使用 AAA 模式（Arrange-Act-Assert）

推荐使用: pytest



## tech

# 技术栈

> 此文件由 HarnessGenJ 自动生成，根据项目文件自动检测
> 检测置信度: 70%

## 主要技术

- **语言**: Python
- **框架**: pytest, Vue, FastAPI, Flask, Django, React
- **包管理器**: poetry

## 版本要求

- **python**: >=3.11

## 数据库

- Redis
- MySQL

## 测试框架

- pytest



## workflow

> priority: 60
> auto_inject: True
> roles: all

# 工作流程

## 标准流程
1. 需求分析 (PM)
2. 架构设计 (Architect)
3. 开发实现 (Developer)
4. 测试验证 (Tester)


---

*自动生成于 2026-04-10 20:43:12*



## product_manager

# 产品经理 - 专注于需求管理 知识文件

> 此文件由 AGENTS.md 自动派生，请勿手动修改
> 更新时间: 2026-04-10 20:43

---

# AGENTS.md - HarnessGenJ 项目知识库

> 此文件存储项目核心知识，AI 助手启动时自动加载

## 项目信息

- **项目名称**: HarnessGenJ (HGJ) - Harness Engineering with JVM-style Generational Memory
- **技术栈**: Python + pytest + FastAPI + Pydantic
- **当前状态**: 开发中 (v1.3.1)
- **代码行数**: ~15,000 行

## 项目简介

HarnessGenJ 是一个 AI Agent 协作框架，核心特性：

1. **角色驱动协作** - Developer/Tester/PM/Architect/CodeReviewer/BugHunter
2. **JVM 风格记忆管理** - Eden/Survivor/Old/Permanent 分代存储
3. **GAN 对抗质量保证** - 生成器-判别器对抗审查机制
4. **MCP Server 支持** - 21 个工具暴露给 Claude Code

## 核心规范

### 框架使用规范（自举模式）

**本项目自身使用 HGJ 框架进行开发！**

```
用户需求 → harness.develop() → 签发许可 → 执行指令 → complete_task()
```

**必须遵守**：
- 所有代码修改必须通过 `harness.develop()` 或 `harness.fix_bug()`
- 禁止直接编辑代码而不经过框架
- 框架会签发操作许可，AI 只能在许可范围内操作

### 代码规范

- 遵循 PEP 8 规范
- 使用 Pydantic BaseModel 进行数据验证
- 所有公共 API 需要类型注解和 docstring
- 测试覆盖率目标: 80%+

### 工作流程

1. **需求接收** → `harness.receive_request("需求描述")`
2. **开发执行** → `harness.develop("需求描述")`
3. **对抗审查** → 自动执行（框架强制）
4. **文档更新** → 自动执行（框架强制）
5. **任务完成** → `harness.complete_task(task_id, "摘要")`

## 目录结构

```
src/harnessgenj/
├── engine.py          # 主入口 Harness 类
├── roles/             # 角色定义
├── workflow/          # 工作流系统
├── memory/            # JVM 风格记忆管理
├── quality/           # 质量保证（积分、对抗）
├── harness/           # 框架核心组件
│   ├── framework_session.py    # 会话权限管理
│   ├── operation_instruction.py # 操作指令协议
│   └── adversarial.py          # 对抗审查
├── mcp/               # MCP Server
└── notify/            # 用户通知
```

## 常用命令

```python
# 初始化框架（每次对话开始）
from harnessgenj import Harness
harness = Harness.from_project(".")

# 开发功能（返回操作指令）
result = harness.develop("功能描述")

# 修复 Bug
result = harness.fix_bug("问题描述")

# 查看状态
harness.get_status()

# 查看积分排行
harness.get_score_leaderboard()
```

## 重要约定

1. **渐进式披露**: 每个角色只获取最小必要信息
2. **持久化优先**: 所有重要操作自动保存到 .harnessgenj/
3. **文档驱动**: 需求/设计/开发/测试都有对应文档
4. **对抗审查**: 所有代码变更经过 CodeReviewer/BugHunter 审查
5. **积分激励**: 使用框架开发获得积分奖励

## 角色边界

| 角色 | 权限 | 禁止 |
|------|------|------|
| Developer | 编辑代码 | 修改架构设计 |
| CodeReviewer | 只读、审查 | 修改代码 |
| BugHunter | 只读、安全审查 | 修改代码 |
| ProjectManager | 编辑文档、协调 | 修改代码 |
| Architect | 编辑设计文档 | 直接修改代码实现 |

---
*此文件由 HarnessGenJ 自动维护 - 自举模式*


## conventions

# 代码约定

> 此文件由 HarnessGenJ 自动生成，根据技术栈自动适配
> 请遵循项目既有的代码风格

## 编码风格

- 遵循 PEP 8 规范
- 使用类型注解（Type Hints）
- 函数名使用 snake_case
- 类名使用 PascalCase
- 常量使用 UPPER_SNAKE_CASE

## 代码组织

- 使用模块化设计
- 每个 module 应有明确的职责
- 使用 `__init__.py` 导出公共 API

## 文档

- 函数必须有文档字符串（docstring）
- 使用 Google 或 NumPy 风格的 docstring
- 复杂逻辑需要注释说明

## 类型检查

- 推荐使用 mypy 进行静态类型检查
- 使用 `typing` 模块的泛型类型

## 测试约定

- 所有新功能需要添加测试
- 测试文件放在 `test/` 或 `tests/` 目录
- 测试函数名应描述测试场景
- 使用 AAA 模式（Arrange-Act-Assert）

推荐使用: pytest



## tech

# 技术栈

> 此文件由 HarnessGenJ 自动生成，根据项目文件自动检测
> 检测置信度: 70%

## 主要技术

- **语言**: Python
- **框架**: pytest, Vue, FastAPI, Flask, Django, React
- **包管理器**: poetry

## 版本要求

- **python**: >=3.11

## 数据库

- Redis
- MySQL

## 测试框架

- pytest



## workflow

> priority: 60
> auto_inject: True
> roles: all

# 工作流程

## 标准流程
1. 需求分析 (PM)
2. 架构设计 (Architect)
3. 开发实现 (Developer)
4. 测试验证 (Tester)


---

*自动生成于 2026-04-10 20:43:12*



## tech

# 技术栈

> 此文件由 HarnessGenJ 自动生成，根据项目文件自动检测
> 检测置信度: 70%

## 主要技术

- **语言**: Python
- **框架**: pytest, Vue, FastAPI, Flask, Django, React
- **包管理器**: poetry

## 版本要求

- **python**: >=3.11

## 数据库

- Redis
- MySQL

## 测试框架

- pytest



## tester

# 测试员 - 专注于质量验证 知识文件

> 此文件由 AGENTS.md 自动派生，请勿手动修改
> 更新时间: 2026-04-10 20:43

---

# AGENTS.md - HarnessGenJ 项目知识库

> 此文件存储项目核心知识，AI 助手启动时自动加载

## 项目信息

- **项目名称**: HarnessGenJ (HGJ) - Harness Engineering with JVM-style Generational Memory
- **技术栈**: Python + pytest + FastAPI + Pydantic
- **当前状态**: 开发中 (v1.3.1)
- **代码行数**: ~15,000 行

## 项目简介

HarnessGenJ 是一个 AI Agent 协作框架，核心特性：

1. **角色驱动协作** - Developer/Tester/PM/Architect/CodeReviewer/BugHunter
2. **JVM 风格记忆管理** - Eden/Survivor/Old/Permanent 分代存储
3. **GAN 对抗质量保证** - 生成器-判别器对抗审查机制
4. **MCP Server 支持** - 21 个工具暴露给 Claude Code

## 核心规范

### 框架使用规范（自举模式）

**本项目自身使用 HGJ 框架进行开发！**

```
用户需求 → harness.develop() → 签发许可 → 执行指令 → complete_task()
```

**必须遵守**：
- 所有代码修改必须通过 `harness.develop()` 或 `harness.fix_bug()`
- 禁止直接编辑代码而不经过框架
- 框架会签发操作许可，AI 只能在许可范围内操作

### 代码规范

- 遵循 PEP 8 规范
- 使用 Pydantic BaseModel 进行数据验证
- 所有公共 API 需要类型注解和 docstring
- 测试覆盖率目标: 80%+

### 工作流程

1. **需求接收** → `harness.receive_request("需求描述")`
2. **开发执行** → `harness.develop("需求描述")`
3. **对抗审查** → 自动执行（框架强制）
4. **文档更新** → 自动执行（框架强制）
5. **任务完成** → `harness.complete_task(task_id, "摘要")`

## 目录结构

```
src/harnessgenj/
├── engine.py          # 主入口 Harness 类
├── roles/             # 角色定义
├── workflow/          # 工作流系统
├── memory/            # JVM 风格记忆管理
├── quality/           # 质量保证（积分、对抗）
├── harness/           # 框架核心组件
│   ├── framework_session.py    # 会话权限管理
│   ├── operation_instruction.py # 操作指令协议
│   └── adversarial.py          # 对抗审查
├── mcp/               # MCP Server
└── notify/            # 用户通知
```

## 常用命令

```python
# 初始化框架（每次对话开始）
from harnessgenj import Harness
harness = Harness.from_project(".")

# 开发功能（返回操作指令）
result = harness.develop("功能描述")

# 修复 Bug
result = harness.fix_bug("问题描述")

# 查看状态
harness.get_status()

# 查看积分排行
harness.get_score_leaderboard()
```

## 重要约定

1. **渐进式披露**: 每个角色只获取最小必要信息
2. **持久化优先**: 所有重要操作自动保存到 .harnessgenj/
3. **文档驱动**: 需求/设计/开发/测试都有对应文档
4. **对抗审查**: 所有代码变更经过 CodeReviewer/BugHunter 审查
5. **积分激励**: 使用框架开发获得积分奖励

## 角色边界

| 角色 | 权限 | 禁止 |
|------|------|------|
| Developer | 编辑代码 | 修改架构设计 |
| CodeReviewer | 只读、审查 | 修改代码 |
| BugHunter | 只读、安全审查 | 修改代码 |
| ProjectManager | 编辑文档、协调 | 修改代码 |
| Architect | 编辑设计文档 | 直接修改代码实现 |

---
*此文件由 HarnessGenJ 自动维护 - 自举模式*


## conventions

# 代码约定

> 此文件由 HarnessGenJ 自动生成，根据技术栈自动适配
> 请遵循项目既有的代码风格

## 编码风格

- 遵循 PEP 8 规范
- 使用类型注解（Type Hints）
- 函数名使用 snake_case
- 类名使用 PascalCase
- 常量使用 UPPER_SNAKE_CASE

## 代码组织

- 使用模块化设计
- 每个 module 应有明确的职责
- 使用 `__init__.py` 导出公共 API

## 文档

- 函数必须有文档字符串（docstring）
- 使用 Google 或 NumPy 风格的 docstring
- 复杂逻辑需要注释说明

## 类型检查

- 推荐使用 mypy 进行静态类型检查
- 使用 `typing` 模块的泛型类型

## 测试约定

- 所有新功能需要添加测试
- 测试文件放在 `test/` 或 `tests/` 目录
- 测试函数名应描述测试场景
- 使用 AAA 模式（Arrange-Act-Assert）

推荐使用: pytest



## tech

# 技术栈

> 此文件由 HarnessGenJ 自动生成，根据项目文件自动检测
> 检测置信度: 70%

## 主要技术

- **语言**: Python
- **框架**: pytest, Vue, FastAPI, Flask, Django, React
- **包管理器**: poetry

## 版本要求

- **python**: >=3.11

## 数据库

- Redis
- MySQL

## 测试框架

- pytest



## workflow

> priority: 60
> auto_inject: True
> roles: all

# 工作流程

## 标准流程
1. 需求分析 (PM)
2. 架构设计 (Architect)
3. 开发实现 (Developer)
4. 测试验证 (Tester)


---

*自动生成于 2026-04-10 20:43:12*



## workflow

> priority: 60
> auto_inject: True
> roles: all

# 工作流程

## 标准流程
1. 需求分析 (PM)
2. 架构设计 (Architect)
3. 开发实现 (Developer)
4. 测试验证 (Tester)


---

*自动生成于 2026-04-10 20:43:13*



## tech

# 技术栈

> 此文件由 HarnessGenJ 自动生成，根据项目文件自动检测
> 检测置信度: 70%

## 主要技术

- **语言**: Python
- **框架**: pytest, Vue, FastAPI, Flask, Django, React
- **包管理器**: poetry

## 版本要求

- **python**: >=3.11

## 数据库

- Redis
- MySQL

## 测试框架

- pytest



## tester

# 测试员 - 专注于质量验证 知识文件

> 此文件由 AGENTS.md 自动派生，请勿手动修改
> 更新时间: 2026-04-10 20:43

---

# AGENTS.md - HarnessGenJ 项目知识库

> 此文件存储项目核心知识，AI 助手启动时自动加载

## 项目信息

- **项目名称**: HarnessGenJ (HGJ) - Harness Engineering with JVM-style Generational Memory
- **技术栈**: Python + pytest + FastAPI + Pydantic
- **当前状态**: 开发中 (v1.3.1)
- **代码行数**: ~15,000 行

## 项目简介

HarnessGenJ 是一个 AI Agent 协作框架，核心特性：

1. **角色驱动协作** - Developer/Tester/PM/Architect/CodeReviewer/BugHunter
2. **JVM 风格记忆管理** - Eden/Survivor/Old/Permanent 分代存储
3. **GAN 对抗质量保证** - 生成器-判别器对抗审查机制
4. **MCP Server 支持** - 21 个工具暴露给 Claude Code

## 核心规范

### 框架使用规范（自举模式）

**本项目自身使用 HGJ 框架进行开发！**

```
用户需求 → harness.develop() → 签发许可 → 执行指令 → complete_task()
```

**必须遵守**：
- 所有代码修改必须通过 `harness.develop()` 或 `harness.fix_bug()`
- 禁止直接编辑代码而不经过框架
- 框架会签发操作许可，AI 只能在许可范围内操作

### 代码规范

- 遵循 PEP 8 规范
- 使用 Pydantic BaseModel 进行数据验证
- 所有公共 API 需要类型注解和 docstring
- 测试覆盖率目标: 80%+

### 工作流程

1. **需求接收** → `harness.receive_request("需求描述")`
2. **开发执行** → `harness.develop("需求描述")`
3. **对抗审查** → 自动执行（框架强制）
4. **文档更新** → 自动执行（框架强制）
5. **任务完成** → `harness.complete_task(task_id, "摘要")`

## 目录结构

```
src/harnessgenj/
├── engine.py          # 主入口 Harness 类
├── roles/             # 角色定义
├── workflow/          # 工作流系统
├── memory/            # JVM 风格记忆管理
├── quality/           # 质量保证（积分、对抗）
├── harness/           # 框架核心组件
│   ├── framework_session.py    # 会话权限管理
│   ├── operation_instruction.py # 操作指令协议
│   └── adversarial.py          # 对抗审查
├── mcp/               # MCP Server
└── notify/            # 用户通知
```

## 常用命令

```python
# 初始化框架（每次对话开始）
from harnessgenj import Harness
harness = Harness.from_project(".")

# 开发功能（返回操作指令）
result = harness.develop("功能描述")

# 修复 Bug
result = harness.fix_bug("问题描述")

# 查看状态
harness.get_status()

# 查看积分排行
harness.get_score_leaderboard()
```

## 重要约定

1. **渐进式披露**: 每个角色只获取最小必要信息
2. **持久化优先**: 所有重要操作自动保存到 .harnessgenj/
3. **文档驱动**: 需求/设计/开发/测试都有对应文档
4. **对抗审查**: 所有代码变更经过 CodeReviewer/BugHunter 审查
5. **积分激励**: 使用框架开发获得积分奖励

## 角色边界

| 角色 | 权限 | 禁止 |
|------|------|------|
| Developer | 编辑代码 | 修改架构设计 |
| CodeReviewer | 只读、审查 | 修改代码 |
| BugHunter | 只读、安全审查 | 修改代码 |
| ProjectManager | 编辑文档、协调 | 修改代码 |
| Architect | 编辑设计文档 | 直接修改代码实现 |

---
*此文件由 HarnessGenJ 自动维护 - 自举模式*


## architect

# 架构师 - 专注于系统设计 知识文件

> 此文件由 AGENTS.md 自动派生，请勿手动修改
> 更新时间: 2026-04-10 20:43

---

# AGENTS.md - HarnessGenJ 项目知识库

> 此文件存储项目核心知识，AI 助手启动时自动加载

## 项目信息

- **项目名称**: HarnessGenJ (HGJ) - Harness Engineering with JVM-style Generational Memory
- **技术栈**: Python + pytest + FastAPI + Pydantic
- **当前状态**: 开发中 (v1.3.1)
- **代码行数**: ~15,000 行

## 项目简介

HarnessGenJ 是一个 AI Agent 协作框架，核心特性：

1. **角色驱动协作** - Developer/Tester/PM/Architect/CodeReviewer/BugHunter
2. **JVM 风格记忆管理** - Eden/Survivor/Old/Permanent 分代存储
3. **GAN 对抗质量保证** - 生成器-判别器对抗审查机制
4. **MCP Server 支持** - 21 个工具暴露给 Claude Code

## 核心规范

### 框架使用规范（自举模式）

**本项目自身使用 HGJ 框架进行开发！**

```
用户需求 → harness.develop() → 签发许可 → 执行指令 → complete_task()
```

**必须遵守**：
- 所有代码修改必须通过 `harness.develop()` 或 `harness.fix_bug()`
- 禁止直接编辑代码而不经过框架
- 框架会签发操作许可，AI 只能在许可范围内操作

### 代码规范

- 遵循 PEP 8 规范
- 使用 Pydantic BaseModel 进行数据验证
- 所有公共 API 需要类型注解和 docstring
- 测试覆盖率目标: 80%+

### 工作流程

1. **需求接收** → `harness.receive_request("需求描述")`
2. **开发执行** → `harness.develop("需求描述")`
3. **对抗审查** → 自动执行（框架强制）
4. **文档更新** → 自动执行（框架强制）
5. **任务完成** → `harness.complete_task(task_id, "摘要")`

## 目录结构

```
src/harnessgenj/
├── engine.py          # 主入口 Harness 类
├── roles/             # 角色定义
├── workflow/          # 工作流系统
├── memory/            # JVM 风格记忆管理
├── quality/           # 质量保证（积分、对抗）
├── harness/           # 框架核心组件
│   ├── framework_session.py    # 会话权限管理
│   ├── operation_instruction.py # 操作指令协议
│   └── adversarial.py          # 对抗审查
├── mcp/               # MCP Server
└── notify/            # 用户通知
```

## 常用命令

```python
# 初始化框架（每次对话开始）
from harnessgenj import Harness
harness = Harness.from_project(".")

# 开发功能（返回操作指令）
result = harness.develop("功能描述")

# 修复 Bug
result = harness.fix_bug("问题描述")

# 查看状态
harness.get_status()

# 查看积分排行
harness.get_score_leaderboard()
```

## 重要约定

1. **渐进式披露**: 每个角色只获取最小必要信息
2. **持久化优先**: 所有重要操作自动保存到 .harnessgenj/
3. **文档驱动**: 需求/设计/开发/测试都有对应文档
4. **对抗审查**: 所有代码变更经过 CodeReviewer/BugHunter 审查
5. **积分激励**: 使用框架开发获得积分奖励

## 角色边界

| 角色 | 权限 | 禁止 |
|------|------|------|
| Developer | 编辑代码 | 修改架构设计 |
| CodeReviewer | 只读、审查 | 修改代码 |
| BugHunter | 只读、安全审查 | 修改代码 |
| ProjectManager | 编辑文档、协调 | 修改代码 |
| Architect | 编辑设计文档 | 直接修改代码实现 |

---
*此文件由 HarnessGenJ 自动维护 - 自举模式*


## conventions

# 代码约定

> 此文件由 HarnessGenJ 自动生成，根据技术栈自动适配
> 请遵循项目既有的代码风格

## 编码风格

- 遵循 PEP 8 规范
- 使用类型注解（Type Hints）
- 函数名使用 snake_case
- 类名使用 PascalCase
- 常量使用 UPPER_SNAKE_CASE

## 代码组织

- 使用模块化设计
- 每个 module 应有明确的职责
- 使用 `__init__.py` 导出公共 API

## 文档

- 函数必须有文档字符串（docstring）
- 使用 Google 或 NumPy 风格的 docstring
- 复杂逻辑需要注释说明

## 类型检查

- 推荐使用 mypy 进行静态类型检查
- 使用 `typing` 模块的泛型类型

## 测试约定

- 所有新功能需要添加测试
- 测试文件放在 `test/` 或 `tests/` 目录
- 测试函数名应描述测试场景
- 使用 AAA 模式（Arrange-Act-Assert）

推荐使用: pytest



## tech

# 技术栈

> 此文件由 HarnessGenJ 自动生成，根据项目文件自动检测
> 检测置信度: 70%

## 主要技术

- **语言**: Python
- **框架**: pytest, Vue, FastAPI, Flask, Django, React
- **包管理器**: poetry

## 版本要求

- **python**: >=3.11

## 数据库

- Redis
- MySQL

## 测试框架

- pytest



## workflow

> priority: 60
> auto_inject: True
> roles: all

# 工作流程

## 标准流程
1. 需求分析 (PM)
2. 架构设计 (Architect)
3. 开发实现 (Developer)
4. 测试验证 (Tester)


---

*自动生成于 2026-04-10 20:43:12*



## conventions

# 代码约定

> 此文件由 HarnessGenJ 自动生成，根据技术栈自动适配
> 请遵循项目既有的代码风格

## 编码风格

- 遵循 PEP 8 规范
- 使用类型注解（Type Hints）
- 函数名使用 snake_case
- 类名使用 PascalCase
- 常量使用 UPPER_SNAKE_CASE

## 代码组织

- 使用模块化设计
- 每个 module 应有明确的职责
- 使用 `__init__.py` 导出公共 API

## 文档

- 函数必须有文档字符串（docstring）
- 使用 Google 或 NumPy 风格的 docstring
- 复杂逻辑需要注释说明

## 类型检查

- 推荐使用 mypy 进行静态类型检查
- 使用 `typing` 模块的泛型类型

## 测试约定

- 所有新功能需要添加测试
- 测试文件放在 `test/` 或 `tests/` 目录
- 测试函数名应描述测试场景
- 使用 AAA 模式（Arrange-Act-Assert）

推荐使用: pytest



## developer

# 开发者 - 专注于代码实现 知识文件

> 此文件由 AGENTS.md 自动派生，请勿手动修改
> 更新时间: 2026-04-10 20:43

---

# AGENTS.md - HarnessGenJ 项目知识库

> 此文件存储项目核心知识，AI 助手启动时自动加载

## 项目信息

- **项目名称**: HarnessGenJ (HGJ) - Harness Engineering with JVM-style Generational Memory
- **技术栈**: Python + pytest + FastAPI + Pydantic
- **当前状态**: 开发中 (v1.3.1)
- **代码行数**: ~15,000 行

## 项目简介

HarnessGenJ 是一个 AI Agent 协作框架，核心特性：

1. **角色驱动协作** - Developer/Tester/PM/Architect/CodeReviewer/BugHunter
2. **JVM 风格记忆管理** - Eden/Survivor/Old/Permanent 分代存储
3. **GAN 对抗质量保证** - 生成器-判别器对抗审查机制
4. **MCP Server 支持** - 21 个工具暴露给 Claude Code

## 核心规范

### 框架使用规范（自举模式）

**本项目自身使用 HGJ 框架进行开发！**

```
用户需求 → harness.develop() → 签发许可 → 执行指令 → complete_task()
```

**必须遵守**：
- 所有代码修改必须通过 `harness.develop()` 或 `harness.fix_bug()`
- 禁止直接编辑代码而不经过框架
- 框架会签发操作许可，AI 只能在许可范围内操作

### 代码规范

- 遵循 PEP 8 规范
- 使用 Pydantic BaseModel 进行数据验证
- 所有公共 API 需要类型注解和 docstring
- 测试覆盖率目标: 80%+

### 工作流程

1. **需求接收** → `harness.receive_request("需求描述")`
2. **开发执行** → `harness.develop("需求描述")`
3. **对抗审查** → 自动执行（框架强制）
4. **文档更新** → 自动执行（框架强制）
5. **任务完成** → `harness.complete_task(task_id, "摘要")`

## 目录结构

```
src/harnessgenj/
├── engine.py          # 主入口 Harness 类
├── roles/             # 角色定义
├── workflow/          # 工作流系统
├── memory/            # JVM 风格记忆管理
├── quality/           # 质量保证（积分、对抗）
├── harness/           # 框架核心组件
│   ├── framework_session.py    # 会话权限管理
│   ├── operation_instruction.py # 操作指令协议
│   └── adversarial.py          # 对抗审查
├── mcp/               # MCP Server
└── notify/            # 用户通知
```

## 常用命令

```python
# 初始化框架（每次对话开始）
from harnessgenj import Harness
harness = Harness.from_project(".")

# 开发功能（返回操作指令）
result = harness.develop("功能描述")

# 修复 Bug
result = harness.fix_bug("问题描述")

# 查看状态
harness.get_status()

# 查看积分排行
harness.get_score_leaderboard()
```

## 重要约定

1. **渐进式披露**: 每个角色只获取最小必要信息
2. **持久化优先**: 所有重要操作自动保存到 .harnessgenj/
3. **文档驱动**: 需求/设计/开发/测试都有对应文档
4. **对抗审查**: 所有代码变更经过 CodeReviewer/BugHunter 审查
5. **积分激励**: 使用框架开发获得积分奖励

## 角色边界

| 角色 | 权限 | 禁止 |
|------|------|------|
| Developer | 编辑代码 | 修改架构设计 |
| CodeReviewer | 只读、审查 | 修改代码 |
| BugHunter | 只读、安全审查 | 修改代码 |
| ProjectManager | 编辑文档、协调 | 修改代码 |
| Architect | 编辑设计文档 | 直接修改代码实现 |

---
*此文件由 HarnessGenJ 自动维护 - 自举模式*


## conventions

# 代码约定

> 此文件由 HarnessGenJ 自动生成，根据技术栈自动适配
> 请遵循项目既有的代码风格

## 编码风格

- 遵循 PEP 8 规范
- 使用类型注解（Type Hints）
- 函数名使用 snake_case
- 类名使用 PascalCase
- 常量使用 UPPER_SNAKE_CASE

## 代码组织

- 使用模块化设计
- 每个 module 应有明确的职责
- 使用 `__init__.py` 导出公共 API

## 文档

- 函数必须有文档字符串（docstring）
- 使用 Google 或 NumPy 风格的 docstring
- 复杂逻辑需要注释说明

## 类型检查

- 推荐使用 mypy 进行静态类型检查
- 使用 `typing` 模块的泛型类型

## 测试约定

- 所有新功能需要添加测试
- 测试文件放在 `test/` 或 `tests/` 目录
- 测试函数名应描述测试场景
- 使用 AAA 模式（Arrange-Act-Assert）

推荐使用: pytest



## tech

# 技术栈

> 此文件由 HarnessGenJ 自动生成，根据项目文件自动检测
> 检测置信度: 70%

## 主要技术

- **语言**: Python
- **框架**: pytest, Vue, FastAPI, Flask, Django, React
- **包管理器**: poetry

## 版本要求

- **python**: >=3.11

## 数据库

- Redis
- MySQL

## 测试框架

- pytest



## workflow

> priority: 60
> auto_inject: True
> roles: all

# 工作流程

## 标准流程
1. 需求分析 (PM)
2. 架构设计 (Architect)
3. 开发实现 (Developer)
4. 测试验证 (Tester)


---

*自动生成于 2026-04-10 20:43:12*



## product_manager

# 产品经理 - 专注于需求管理 知识文件

> 此文件由 AGENTS.md 自动派生，请勿手动修改
> 更新时间: 2026-04-10 20:43

---

# AGENTS.md - HarnessGenJ 项目知识库

> 此文件存储项目核心知识，AI 助手启动时自动加载

## 项目信息

- **项目名称**: HarnessGenJ (HGJ) - Harness Engineering with JVM-style Generational Memory
- **技术栈**: Python + pytest + FastAPI + Pydantic
- **当前状态**: 开发中 (v1.3.1)
- **代码行数**: ~15,000 行

## 项目简介

HarnessGenJ 是一个 AI Agent 协作框架，核心特性：

1. **角色驱动协作** - Developer/Tester/PM/Architect/CodeReviewer/BugHunter
2. **JVM 风格记忆管理** - Eden/Survivor/Old/Permanent 分代存储
3. **GAN 对抗质量保证** - 生成器-判别器对抗审查机制
4. **MCP Server 支持** - 21 个工具暴露给 Claude Code

## 核心规范

### 框架使用规范（自举模式）

**本项目自身使用 HGJ 框架进行开发！**

```
用户需求 → harness.develop() → 签发许可 → 执行指令 → complete_task()
```

**必须遵守**：
- 所有代码修改必须通过 `harness.develop()` 或 `harness.fix_bug()`
- 禁止直接编辑代码而不经过框架
- 框架会签发操作许可，AI 只能在许可范围内操作

### 代码规范

- 遵循 PEP 8 规范
- 使用 Pydantic BaseModel 进行数据验证
- 所有公共 API 需要类型注解和 docstring
- 测试覆盖率目标: 80%+

### 工作流程

1. **需求接收** → `harness.receive_request("需求描述")`
2. **开发执行** → `harness.develop("需求描述")`
3. **对抗审查** → 自动执行（框架强制）
4. **文档更新** → 自动执行（框架强制）
5. **任务完成** → `harness.complete_task(task_id, "摘要")`

## 目录结构

```
src/harnessgenj/
├── engine.py          # 主入口 Harness 类
├── roles/             # 角色定义
├── workflow/          # 工作流系统
├── memory/            # JVM 风格记忆管理
├── quality/           # 质量保证（积分、对抗）
├── harness/           # 框架核心组件
│   ├── framework_session.py    # 会话权限管理
│   ├── operation_instruction.py # 操作指令协议
│   └── adversarial.py          # 对抗审查
├── mcp/               # MCP Server
└── notify/            # 用户通知
```

## 常用命令

```python
# 初始化框架（每次对话开始）
from harnessgenj import Harness
harness = Harness.from_project(".")

# 开发功能（返回操作指令）
result = harness.develop("功能描述")

# 修复 Bug
result = harness.fix_bug("问题描述")

# 查看状态
harness.get_status()

# 查看积分排行
harness.get_score_leaderboard()
```

## 重要约定

1. **渐进式披露**: 每个角色只获取最小必要信息
2. **持久化优先**: 所有重要操作自动保存到 .harnessgenj/
3. **文档驱动**: 需求/设计/开发/测试都有对应文档
4. **对抗审查**: 所有代码变更经过 CodeReviewer/BugHunter 审查
5. **积分激励**: 使用框架开发获得积分奖励

## 角色边界

| 角色 | 权限 | 禁止 |
|------|------|------|
| Developer | 编辑代码 | 修改架构设计 |
| CodeReviewer | 只读、审查 | 修改代码 |
| BugHunter | 只读、安全审查 | 修改代码 |
| ProjectManager | 编辑文档、协调 | 修改代码 |
| Architect | 编辑设计文档 | 直接修改代码实现 |

---
*此文件由 HarnessGenJ 自动维护 - 自举模式*


## conventions

# 代码约定

> 此文件由 HarnessGenJ 自动生成，根据技术栈自动适配
> 请遵循项目既有的代码风格

## 编码风格

- 遵循 PEP 8 规范
- 使用类型注解（Type Hints）
- 函数名使用 snake_case
- 类名使用 PascalCase
- 常量使用 UPPER_SNAKE_CASE

## 代码组织

- 使用模块化设计
- 每个 module 应有明确的职责
- 使用 `__init__.py` 导出公共 API

## 文档

- 函数必须有文档字符串（docstring）
- 使用 Google 或 NumPy 风格的 docstring
- 复杂逻辑需要注释说明

## 类型检查

- 推荐使用 mypy 进行静态类型检查
- 使用 `typing` 模块的泛型类型

## 测试约定

- 所有新功能需要添加测试
- 测试文件放在 `test/` 或 `tests/` 目录
- 测试函数名应描述测试场景
- 使用 AAA 模式（Arrange-Act-Assert）

推荐使用: pytest



## tech

# 技术栈

> 此文件由 HarnessGenJ 自动生成，根据项目文件自动检测
> 检测置信度: 70%

## 主要技术

- **语言**: Python
- **框架**: pytest, Vue, FastAPI, Flask, Django, React
- **包管理器**: poetry

## 版本要求

- **python**: >=3.11

## 数据库

- Redis
- MySQL

## 测试框架

- pytest



## workflow

> priority: 60
> auto_inject: True
> roles: all

# 工作流程

## 标准流程
1. 需求分析 (PM)
2. 架构设计 (Architect)
3. 开发实现 (Developer)
4. 测试验证 (Tester)


---

*自动生成于 2026-04-10 20:43:12*



## tech

# 技术栈

> 此文件由 HarnessGenJ 自动生成，根据项目文件自动检测
> 检测置信度: 70%

## 主要技术

- **语言**: Python
- **框架**: pytest, Vue, FastAPI, Flask, Django, React
- **包管理器**: poetry

## 版本要求

- **python**: >=3.11

## 数据库

- Redis
- MySQL

## 测试框架

- pytest



## tester

# 测试员 - 专注于质量验证 知识文件

> 此文件由 AGENTS.md 自动派生，请勿手动修改
> 更新时间: 2026-04-10 20:43

---

# AGENTS.md - HarnessGenJ 项目知识库

> 此文件存储项目核心知识，AI 助手启动时自动加载

## 项目信息

- **项目名称**: HarnessGenJ (HGJ) - Harness Engineering with JVM-style Generational Memory
- **技术栈**: Python + pytest + FastAPI + Pydantic
- **当前状态**: 开发中 (v1.3.1)
- **代码行数**: ~15,000 行

## 项目简介

HarnessGenJ 是一个 AI Agent 协作框架，核心特性：

1. **角色驱动协作** - Developer/Tester/PM/Architect/CodeReviewer/BugHunter
2. **JVM 风格记忆管理** - Eden/Survivor/Old/Permanent 分代存储
3. **GAN 对抗质量保证** - 生成器-判别器对抗审查机制
4. **MCP Server 支持** - 21 个工具暴露给 Claude Code

## 核心规范

### 框架使用规范（自举模式）

**本项目自身使用 HGJ 框架进行开发！**

```
用户需求 → harness.develop() → 签发许可 → 执行指令 → complete_task()
```

**必须遵守**：
- 所有代码修改必须通过 `harness.develop()` 或 `harness.fix_bug()`
- 禁止直接编辑代码而不经过框架
- 框架会签发操作许可，AI 只能在许可范围内操作

### 代码规范

- 遵循 PEP 8 规范
- 使用 Pydantic BaseModel 进行数据验证
- 所有公共 API 需要类型注解和 docstring
- 测试覆盖率目标: 80%+

### 工作流程

1. **需求接收** → `harness.receive_request("需求描述")`
2. **开发执行** → `harness.develop("需求描述")`
3. **对抗审查** → 自动执行（框架强制）
4. **文档更新** → 自动执行（框架强制）
5. **任务完成** → `harness.complete_task(task_id, "摘要")`

## 目录结构

```
src/harnessgenj/
├── engine.py          # 主入口 Harness 类
├── roles/             # 角色定义
├── workflow/          # 工作流系统
├── memory/            # JVM 风格记忆管理
├── quality/           # 质量保证（积分、对抗）
├── harness/           # 框架核心组件
│   ├── framework_session.py    # 会话权限管理
│   ├── operation_instruction.py # 操作指令协议
│   └── adversarial.py          # 对抗审查
├── mcp/               # MCP Server
└── notify/            # 用户通知
```

## 常用命令

```python
# 初始化框架（每次对话开始）
from harnessgenj import Harness
harness = Harness.from_project(".")

# 开发功能（返回操作指令）
result = harness.develop("功能描述")

# 修复 Bug
result = harness.fix_bug("问题描述")

# 查看状态
harness.get_status()

# 查看积分排行
harness.get_score_leaderboard()
```

## 重要约定

1. **渐进式披露**: 每个角色只获取最小必要信息
2. **持久化优先**: 所有重要操作自动保存到 .harnessgenj/
3. **文档驱动**: 需求/设计/开发/测试都有对应文档
4. **对抗审查**: 所有代码变更经过 CodeReviewer/BugHunter 审查
5. **积分激励**: 使用框架开发获得积分奖励

## 角色边界

| 角色 | 权限 | 禁止 |
|------|------|------|
| Developer | 编辑代码 | 修改架构设计 |
| CodeReviewer | 只读、审查 | 修改代码 |
| BugHunter | 只读、安全审查 | 修改代码 |
| ProjectManager | 编辑文档、协调 | 修改代码 |
| Architect | 编辑设计文档 | 直接修改代码实现 |

---
*此文件由 HarnessGenJ 自动维护 - 自举模式*


## conventions

# 代码约定

> 此文件由 HarnessGenJ 自动生成，根据技术栈自动适配
> 请遵循项目既有的代码风格

## 编码风格

- 遵循 PEP 8 规范
- 使用类型注解（Type Hints）
- 函数名使用 snake_case
- 类名使用 PascalCase
- 常量使用 UPPER_SNAKE_CASE

## 代码组织

- 使用模块化设计
- 每个 module 应有明确的职责
- 使用 `__init__.py` 导出公共 API

## 文档

- 函数必须有文档字符串（docstring）
- 使用 Google 或 NumPy 风格的 docstring
- 复杂逻辑需要注释说明

## 类型检查

- 推荐使用 mypy 进行静态类型检查
- 使用 `typing` 模块的泛型类型

## 测试约定

- 所有新功能需要添加测试
- 测试文件放在 `test/` 或 `tests/` 目录
- 测试函数名应描述测试场景
- 使用 AAA 模式（Arrange-Act-Assert）

推荐使用: pytest



## tech

# 技术栈

> 此文件由 HarnessGenJ 自动生成，根据项目文件自动检测
> 检测置信度: 70%

## 主要技术

- **语言**: Python
- **框架**: pytest, Vue, FastAPI, Flask, Django, React
- **包管理器**: poetry

## 版本要求

- **python**: >=3.11

## 数据库

- Redis
- MySQL

## 测试框架

- pytest



## workflow

> priority: 60
> auto_inject: True
> roles: all

# 工作流程

## 标准流程
1. 需求分析 (PM)
2. 架构设计 (Architect)
3. 开发实现 (Developer)
4. 测试验证 (Tester)


---

*自动生成于 2026-04-10 20:43:12*



## workflow

> priority: 60
> auto_inject: True
> roles: all

# 工作流程

## 标准流程
1. 需求分析 (PM)
2. 架构设计 (Architect)
3. 开发实现 (Developer)
4. 测试验证 (Tester)


---

*自动生成于 2026-04-10 20:43:13*



## workflow

> priority: 60
> auto_inject: True
> roles: all

# 工作流程

## 标准流程
1. 需求分析 (PM)
2. 架构设计 (Architect)
3. 开发实现 (Developer)
4. 测试验证 (Tester)


---

*自动生成于 2026-04-10 20:43:13*
