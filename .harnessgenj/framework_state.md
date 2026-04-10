---
name: Framework State
type: reference
---

# HGJ 框架状态

## ⚠️ 强制指令

**所有代码修改必须通过 HGJ 框架执行：**

```python
from harnessgenj import Harness

# 1. 初始化框架
harness = Harness.from_project('.')

# 2. 签发操作许可
result = harness.develop('功能描述')
# 或 result = harness.fix_bug('问题描述')

# 3. 在许可范围内执行代码修改
# ...

# 4. 完成任务
harness.complete_task(result['task_id'], '摘要')
```

## 当前框架状态

- 初始化时间: 2026-04-10
- 项目名称: HarnessGenJ (HGJ)
- 活动任务: 查看 .harnessgenj/session_state.json

## 积分系统

| 操作 | 积分变化 |
|------|----------|
| 使用框架开发 | +10 分 |
| 使用框架修复 Bug | +15 分 |
| 完成代码审查 | +5 分 |
| 绕过框架操作 | -50 分 |

## 角色协作

HGJ 框架支持多角色协作：

| 角色 | 职责 |
|------|------|
| Developer | 编写代码 |
| CodeReviewer | 审查代码质量 |
| BugHunter | 安全审查 |
| ProjectManager | 协调任务 |

## 快速参考

```python
# 查看状态
harness.get_status()

# 查看积分排名
harness.get_score_leaderboard()

# 开发功能
harness.develop('功能描述')

# 修复 Bug
harness.fix_bug('问题描述')

# 快速审查
harness.quick_review(code)
```

## ⚡ 触发词

当用户消息包含以下触发词时，必须立即初始化框架：

- "使用HGJ框架"
- "HGJ框架辅助开发"
- "作为HGJ框架的项目经理"
- "进入HGJ框架"
- "用HGJ"

---

**记住：使用框架 = 获得积分奖励 = 提升职业信誉**