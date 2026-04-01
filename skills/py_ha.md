# py_ha - Harness Engineering Skill

py_ha是一个基于 Harness Engineering 理念构建的 AI Agent 协作框架，通过角色驱动和工作流驱动实现高效的开发协作。

## 安装

```bash
pip install py-ha
```

## 核心能力

### 1. 快速开发功能

当用户请求开发新功能时：

```python
from py_ha import Harness

harness = Harness()
result = harness.develop("功能描述")
```

### 2. 快速修复Bug

当用户报告Bug时：

```python
from py_ha import Harness

harness = Harness()
result = harness.fix_bug("Bug描述")
```

### 3. 组建开发团队

```python
from py_ha import Harness

harness = Harness("项目名")
harness.setup_team({
    "developer": "开发人员名称",
    "tester": "测试人员名称",
    "product_manager": "产品经理名称",
})
```

### 4. 需求分析

```python
harness.analyze("需求描述")
```

### 5. 架构设计

```python
harness.design("系统描述")
```

## 角色系统

py_ha 提供以下角色：

| 角色 | 职责 |
|------|------|
| Developer | 功能开发、Bug修复、代码审查 |
| Tester | 测试编写、测试执行、Bug报告 |
| ProductManager | 需求分析、用户故事、优先级 |
| Architect | 架构设计、技术选型 |
| DocWriter | 文档编写、知识库维护 |
| ProjectManager | 任务协调、进度追踪 |

## 工作流

### 功能开发流程
需求分析 → 开发实现 → 测试验证

### Bug修复流程
Bug分析 → 代码修复 → 验证测试

### 完整开发流程
需求分析 → 架构设计 → 开发实现 → 测试验证 → 文档编写 → 发布评审

## 使用示例

### 示例1: 开发用户登录功能

```python
from py_ha import Harness

harness = Harness("用户系统")
harness.develop("实现用户登录功能，支持用户名密码和手机验证码两种方式")
```

### 示例2: 修复支付Bug

```python
from py_ha import Harness

harness = Harness()
harness.fix_bug("订单支付时偶现超时问题")
```

### 示例3: 分析需求

```python
from py_ha import Harness

harness = Harness("电商平台")
harness.setup_team()
harness.analyze("用户需要一个仪表盘来查看销售数据和趋势分析")
```

## CLI 使用

```bash
# 安装后可直接使用
py-ha develop "实现用户注册功能"
py-ha fix "登录页面验证码无法显示"
py-ha team
py-ha status
py-ha interactive
```

## 记忆系统

保存和召回重要信息：

```python
# 记忆重要信息
harness.remember("project_goal", "构建电商平台", important=True)

# 回忆信息
goal = harness.recall("project_goal")
```

## 项目报告

```python
# 执行开发任务后
harness.develop("功能1")
harness.develop("功能2")
harness.fix_bug("Bug1")

# 生成报告
print(harness.get_report())
```

## 进阶使用

### 自定义工作流

```python
from py_ha import Harness, WorkflowPipeline, WorkflowStage

harness = Harness()

# 创建自定义流水线
pipeline = WorkflowPipeline("custom_pipeline")
pipeline.add_stage(WorkflowStage(
    name="custom_stage",
    description="自定义阶段",
    role="developer",
    inputs=["input1"],
    outputs=["output1"],
))

harness.coordinator.register_workflow("custom", pipeline)
```

### 直接使用角色

```python
from py_ha import Developer

dev = Developer(role_id="dev_1", name="小李")

# 查看技能
print([s.name for s in dev.list_skills()])

# 分配任务
dev.assign_task({
    "type": "implement_feature",
    "description": "实现用户登录",
})

# 执行任务
result = dev.execute_task()
```