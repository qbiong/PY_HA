# Claude Code 多 Agent 架构深度分析文档

> 本文档详细分析 Claude Code 的多 Agent 系统设计
> 生成日期：2026-04-10

---

## 目录

1. 架构总览
2. AgentTool 核心设计
3. Agent 类型系统
4. Coordinator 协调器模式
5. Agent 通信机制
6. Team 团队系统
7. Swarm 执行后端
8. 任务管理系统
9. Agent 上下文与隔离
10. 执行流程详解
11. 源码文件索引
12. 设计模式总结

---

## 1. 架构总览

### 1.1 多 Agent 系统定位

Claude Code 的多 Agent 系统是一个**分层协作架构**，支持：

- **单 Agent 执行**：创建独立子代理完成特定任务
- **并行 Agent 执行**：多个 Agent 同时探索不同代码区域
- **Coordinator 协调**：主控 Agent 调度 Workers，综合结果
- **Team 团队模式**：长期存在的协作团队，共享任务列表

### 1.2 核心设计理念

```
┌─────────────────────────────────────────────────────────────┐
│                     用户交互层                               │
│                  (CLI / IDE / Web)                          │
├─────────────────────────────────────────────────────────────┤
│                     主会话 Agent                             │
│              (QueryEngine + ToolUseContext)                 │
├─────────────────────────────────────────────────────────────┤
│                   AgentTool 入口                             │
│           (参数解析 + Agent选择 + 执行调度)                   │
├───────────────────────┬─────────────────────────────────────┤
│    同步执行路径        │         后台/团队执行路径             │
│   (runAgent.ts)       │    (spawnMultiAgent.ts)             │
├───────────────────────┼─────────────────────────────────────┤
│   单次任务 Agent       │         Teammate Agent              │
│   (完成后返回)        │    (持续运行 + 消息通信)            │
├───────────────────────┴─────────────────────────────────────┤
│                   Swarm 执行后端                             │
│        (in-process / tmux / iterm2)                         │
├─────────────────────────────────────────────────────────────┤
│                   通信与协调层                               │
│    (SendMessage + Mailbox + TaskList)                       │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 Agent ID 前缀系统

| 类型 | ID前缀 | 示例 | 描述 |
|------|--------|------|------|
| local_bash | b | b123456 | 本地 Shell 任务 |
| local_agent | a | a789012 | 本地子代理 |
| remote_agent | r | r345678 | 远程代理 |
| in_process_teammate | t | t901234 | 进程内队友 |
| local_workflow | w | w567890 | 本地工作流 |

---

## 2. AgentTool 核心设计

### 2.1 输入参数定义

**文件位置**：`src/tools/AgentTool/AgentTool.tsx`

```typescript
const inputSchema = z.object({
  // 必需参数
  description: z.string().describe(\"3-5词任务描述\"),
  prompt: z.string().describe(\"具体任务内容\"),
  
  // 可选参数
  subagent_type: z.string().optional(),      // Agent类型选择
  model: z.enum([\"sonnet\", \"opus\", \"haiku\"]).optional(),
  run_in_background: z.boolean().optional(), // 后台执行
  name: z.string().optional(),              // 队友名称（团队模式）
  team_name: z.string().optional(),         // 团队上下文
  mode: z.string().optional(),              // 权限模式
  isolation: z.enum([\"worktree\", \"remote\"]).optional(),
  cwd: z.string().optional(),               // 工作目录覆盖
})
```

### 2.2 执行模式选择

**决策逻辑**（AgentTool.tsx:321-355）：

```
输入参数解析
      ↓
┌─────────────────────────────────────┐
│ 是否指定 subagent_type?              │
├─────────────────────────────────────┤
│ NO + Fork实验启用 → Fork子代理       │
│ YES → 选择对应类型Agent              │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│ 是否有 team_name?                    │
├─────────────────────────────────────┤
│ YES → Teammate模式（持续运行）       │
│ NO → 单次任务模式                    │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│ 是否 run_in_background?              │
├─────────────────────────────────────┤
│ YES → 后台任务（通知系统）           │
│ NO → 同步执行（阻塞等待）            │
└─────────────────────────────────────┘
```

### 2.3 Agent 选择流程

```typescript
// 1. 获取可用Agent列表
const agents = await getAvailableAgents()

// 2. 按类型过滤
const agent = agents.find(a => a.type === subagent_type)

// 3. 验证MCP服务器需求
if (agent.requiredMcpServers) {
  for (const server of agent.requiredMcpServers) {
    if (!mcpClients.includes(server)) {
      throw new Error(\"Required MCP server not connected\")
    }
  }
}

// 4. 权限规则过滤
const allowedAgents = filterDeniedAgents(agents, permissionContext)
```

### 2.4 工具池组装

每个 Agent 有独立的工具池，通过以下方式构建：

```typescript
// Agent定义中指定允许的工具
type AgentDef = {
  tools?: string[]           // 工具白名单
  disallowedTools?: string[] // 工具黑名单
}

// 组装逻辑
function assembleAgentToolPool(agentDef, permissionContext) {
  const allTools = getTools(permissionContext)
  
  // 白名单过滤
  if (agentDef.tools) {
    return allTools.filter(t => agentDef.tools.includes(t.name))
  }
  
  // 黑名单过滤
  if (agentDef.disallowedTools) {
    return allTools.filter(t => !agentDef.disallowedTools.includes(t.name))
  }
  
  return allTools
}
```

---

## 3. Agent 类型系统

### 3.1 内置 Agent 类型

**文件位置**：`src/tools/AgentTool/built-in/*.ts`

| 类型 | 文件 | 工具集 | 特点 |
|------|------|--------|------|
| general-purpose | builtInAgents.ts | 全部工具 | 默认类型，多步骤研究/实现 |
| Explore | ExploreAgent.ts | Read, Glob, Grep, Bash(只读) | 快速代码探索，只读模式 |
| Plan | PlanAgent.ts | Read, Glob, Grep, Bash(只读) | 架构规划，生成实施步骤 |
| verification | verificationAgent.ts | 受控工具集 | 测试验证，需GrowthBook开启 |
| claudeCodeGuide | claudeCodeGuideAgent.ts | 专用工具 | Claude Code使用指南 |
| statuslineSetup | statuslineSetupAgent.ts | 专用工具 | 状态栏配置 |

### 3.2 自定义 Agent 定义

**加载路径**：`.claude/agents/*.md`

**定义格式**（Frontmatter + Markdown）：

```markdown
---
name: my-custom-agent
description: 自定义Agent描述
tools: [\"Bash\", \"Read\", \"Edit\", \"Write\"]
model: sonnet
permissionMode: plan
color: blue
mcpServers:
  - my-mcp-server
hooks:
  PreToolUse: ./hooks/pre-tool.sh
memoryScope: project
isolation: worktree
---

Agent的系统提示内容写在这里...
```

### 3.3 Agent 定义加载逻辑

**文件位置**：`src/tools/AgentTool/loadAgentsDir.ts`

```typescript
export async function loadAgentsDir(cwd: string): Promise<AgentDef[]> {
  const agentsDir = join(cwd, \".claude\", \"agents\")
  const files = await glob(\"*.md\", { cwd: agentsDir })
  
  return files.map(file => {
    const content = await readFile(file)
    const frontmatter = parseFrontmatter(content)
    const prompt = extractMarkdownBody(content)
    
    return {
      type: frontmatter.name,
      description: frontmatter.description,
      tools: frontmatter.tools,
      model: frontmatter.model,
      permissionMode: frontmatter.permissionMode,
      color: frontmatter.color,
      mcpServers: frontmatter.mcpServers || [],
      hooks: frontmatter.hooks,
      memoryScope: frontmatter.memoryScope,
      isolation: frontmatter.isolation,
      prompt: prompt,
    }
  })
}
```

### 3.4 Fork 子代理

**文件位置**：`src/tools/AgentTool/forkSubagent.ts`

Fork 是特殊的隐式子代理，特点：

- **触发条件**：省略 `subagent_type` + Fork实验启用
- **上下文继承**：继承父Agent的完整工具池和系统提示
- **缓存共享**：使用相同系统提示，API缓存可共享
- **权限气泡**：`permissionMode: \"bubble\"`，权限请求上浮到父
- **递归保护**：防止嵌套Fork

```typescript
// Fork子代理创建
export async function forkSubagent(input, context) {
  // 检查是否已经在Fork中
  if (context.isForked) {
    throw new Error(\"Cannot fork inside a fork\")
  }
  
  // 继承父的工具池
  const toolPool = context.toolPool
  
  // 继承父的系统提示（缓存共享）
  const systemPrompt = context.systemPrompt
  
  // 创建气泡权限模式
  const permissionContext = {
    ...context.permissionContext,
    mode: \"bubble\"
  }
  
  return runAgent(forkInput, forkContext)
}
```

---

## 4. Coordinator 协调器模式

### 4.1 概述

Coordinator 模式是一种**主控-工作器架构**，用于复杂任务的并行处理和结果综合。

**激活方式**：
```bash
CLAUDE_CODE_COORDINATOR_MODE=1
```

**文件位置**：`src/coordinator/coordinatorMode.ts`

### 4.2 角色定义

| 角色 | 责任 | 可用工具 |
|------|------|----------|
| Coordinator | 任务调度、结果综合、用户交互 | Agent, SendMessage, TaskStop |
| Worker | 执行具体任务、返回结果 | 根据任务类型分配 |

### 4.3 工作流程

```
┌─────────────────────────────────────────────────────────────┐
│                   Phase 1: Research                         │
│                                                             │
│  Coordinator 分析任务 → 拆分为多个研究方向                   │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ Worker A    │  │ Worker B    │  │ Worker C    │          │
│  │ 探索认证模块│  │ 探索数据库  │  │ 探索API     │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│         ↓              ↓              ↓                     │
│     <task-notification> 返回结果                           │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   Phase 2: Synthesis                        │
│                                                             │
│  Coordinator 读取所有 Worker 结果                           │
│  → 综合发现 → 编写实现规格（包含具体路径和修改）            │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   Phase 3: Implementation                   │
│                                                             │
│  Coordinator 根据规格创建实现 Workers                       │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐                          │
│  │ Worker D    │  │ Worker E    │                          │
│  │ 实现认证修改│  │ 实现数据库  │                          │
│  └─────────────┘  └─────────────┘                          │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   Phase 4: Verification                     │
│                                                             │
│  Coordinator 创建验证 Worker                               │
│                                                             │
│  ┌─────────────┐                                          │
│  │ Worker F    │                                          │
│  │ 测试变更    │                                          │
│  └─────────────┘                                          │
└─────────────────────────────────────────────────────────────┘
```

### 4.4 Worker 结果格式

Workers 通过 XML 格式的 `<task-notification>` 返回结果：

```xml
<task-notification>
  <task-id>a123456</task-id>
  <status>completed|failed|killed</status>
  <summary>人类可读的状态摘要</summary>
  <result>
    Agent的最终响应内容...
  </result>
  <usage>
    <total_tokens>15000</total_tokens>
    <tool_uses>25</tool_uses>
    <duration_ms>45000</duration_ms>
  </usage>
</task-notification>
```

### 4.5 Coordinator 系统提示要点

**文件位置**：`src/coordinator/coordinatorMode.ts:111-369`

核心规则：

1. **综合优先**：总是在委托前综合 Workers 的发现
2. **具体委托**：包含文件路径、行号、具体修改内容
3. **禁止懒惰委托**：不写\"based on your findings\"这类模糊指令
4. **继续 vs 创建**：根据上下文重叠度决定用 SendMessage 还是新 Agent
5. **结果引用**：直接引用 Worker 返回的具体内容

### 4.6 Coordinator 工具限制

```typescript
// Coordinator可用工具（COORDINATOR_MODE_ALLOWED_TOOLS）
const coordinatorTools = [
  \"Agent\",        // 创建新Worker
  \"SendMessage\",  // 继续已存在的Worker
  \"TaskStop\",     // 停止运行的Worker
  \"Bash\",         // 基本命令（受限）
  \"Read\",         // 读取结果
]

// Coordinator禁用工具
const disallowedTools = [
  \"Edit\",         // 不直接编辑
  \"Write\",        // 不直接写入
  \"Grep\",         // 不直接搜索
  // ... 其他工具
]
```

---

## 5. Agent 通信机制

### 5.1 SendMessage Tool

**文件位置**：`src/tools/SendMessageTool/SendMessageTool.ts`

**输入参数**：

```typescript
const inputSchema = z.object({
  to: z.string().describe(\"目标Agent名称，\"*\"广播，或\"bridge:<session-id>\"远程\"),
  message: z.string().describe(\"消息内容（纯文本或结构化）\"),
  summary: z.string().describe(\"5-10词摘要，用于UI预览\"),
})
```

**消息路由逻辑**：

```
解析目标地址
      ↓
┌─────────────────────────────────────┐
│ 目标类型判断                         │
├─────────────────────────────────────┤
│ \"*\" → 广播给所有运行中的Agents        │
│ \"bridge:<id>\" → 发送到远程会话       │
│ 具体名称 → 查找对应Agent             │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│ Agent状态检查                        │
├─────────────────────────────────────┤
│ 运行中 → 加入pending消息队列          │
│ 已停止 → 自动恢复并传入消息          │
└─────────────────────────────────────┘
```

### 5.2 结构化消息类型

```typescript
// 关闭请求
type ShutdownRequest = {
  type: \"shutdown_request\"
  reason: string
}

// 关闭响应
type ShutdownResponse = {
  type: \"shutdown_response\"
  approved: boolean
  reason?: string
}

// 方案审批响应
type PlanApprovalResponse = {
  type: \"plan_approval_response\"
  approved: boolean
  feedback?: string
}
```

### 5.3 Mailbox 邓箱系统

**文件位置**：`src/utils/teammateMailbox.ts`

进程分离的 Teammates 使用文件系统进行消息传递：

```
~/.claude/teams/{team_name}/inboxes/{agent_name}.json
```

**Mailbox 结构**：

```typescript
type Mailbox = {
  messages: MailboxMessage[]
  lockfile: string        // 并发写入保护
}

type MailboxMessage = {
  id: string
  from: string
  to: string
  content: string
  timestamp: number
  read: boolean
  type?: \"shutdown_request\" | \"shutdown_response\" | \"plan_approval_response\"
}
```

**读写流程**：

```typescript
// 发送消息
export async function sendMailboxMessage(teamName, agentName, message) {
  const mailboxPath = getMailboxPath(teamName, agentName)
  
  // 获取锁
  await acquireLock(mailboxPath)
  
  // 读取现有消息
  const mailbox = await readMailbox(mailboxPath)
  
  // 添加新消息
  mailbox.messages.push({
    id: generateId(),
    from: sender,
    to: agentName,
    content: message.content,
    timestamp: Date.now(),
    read: false
  })
  
  // 写入
  await writeMailbox(mailboxPath, mailbox)
  
  // 释放锁
  await releaseLock(mailboxPath)
}

// 接收消息
export async function receiveMailboxMessages(teamName, agentName) {
  const mailbox = await readMailbox(getMailboxPath(teamName, agentName))
  return mailbox.messages.filter(m => !m.read)
}
```

### 5.4 关闭协议

Teammate 关闭需要经过审批流程：

```
┌─────────────────────────────────────────────────────────────┐
│                  Shutdown 协议流程                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Coordinator 发送 shutdown_request                      │
│     SendMessage({ to: \"worker\", type: \"shutdown_request\" })│
│                                                             │
│  2. Worker 收到请求，检查当前任务状态                       │
│     - 有未完成任务 → 拒绝                                  │
│     - 任务已完成 → 同意                                    │
│                                                             │
│  3. Worker 发送 shutdown_response                          │
│     SendMessage({ to: \"lead\", type: \"shutdown_response\",   │
                    approved: true/false })                  │
│                                                             │
│  4. Coordinator 收到响应                                   │
│     - approved → 停止 Worker                               │
│     - rejected → 等待或继续                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Team 团队系统

### 6.1 TeamCreate Tool

**文件位置**：`src/tools/TeamCreateTool/TeamCreateTool.ts`

**输入参数**：

```typescript
const inputSchema = z.object({
  team_name: z.string().describe(\"团队唯一标识符\"),
  description: z.string().describe(\"团队描述\"),
  members: z.array(z.object({
    name: z.string(),
    role: z.string(),
    model: z.enum([\"sonnet\", \"opus\", \"haiku\"]),
  })).optional(),
})
```

**Team 文件结构**：

```
~/.claude/teams/{team_name}/
├── team.json        # 团队元数据
├── inboxes/         # 消息邮箱
│   ├── lead.json
│   ├── worker1.json
│   └── worker2.json
└── tasks.json       # 共享任务列表（可选）
```

**team.json 内容**：

```typescript
type Team = {
  team_name: string
  description: string
  lead_agent_id: string     // \"team-lead@teamName\"
  lead_session_id: string
  members: TeamMember[]
  created_at: number
}

type TeamMember = {
  agentId: string           // \"worker@teamName\"
  agentName: string         // \"worker\"
  role: string
  color: string
  status: \"running\" | \"idle\" | \"stopped\"
}
```

### 6.2 Teammate 身份

**文件位置**：`src/tasks/InProcessTeammateTask/types.ts`

```typescript
type TeammateIdentity = {
  agentId: string           // \"researcher@my-team\"
  agentName: string         // \"researcher\"
  teamName: string
  color?: string            // UI显示颜色
  planModeRequired: boolean
  parentSessionId: string   // 父会话ID
}
```

### 6.3 Teammate 创建流程

```typescript
// AgentTool中的team模式处理
if (input.team_name) {
  // 检查团队是否存在
  const team = await loadTeam(input.team_name)
  
  // 创建Teammate身份
  const identity = {
    agentId: `${input.name}@${input.team_name}`,
    agentName: input.name,
    teamName: input.team_name,
    color: agentDef.color,
    planModeRequired: agentDef.permissionMode === \"plan\",
    parentSessionId: context.sessionId
  }
  
  // 创建邮箱
  await createMailbox(input.team_name, input.name)
  
  // 启动Teammate运行器
  await startTeammate(identity, agentDef, prompt)
}
```

### 6.4 TeamDelete Tool

**文件位置**：`src/tools/TeamDeleteTool/TeamDeleteTool.ts`

```typescript
export const TeamDeleteTool = buildTool({
  name: \"TeamDelete\",
  inputSchema: z.object({
    team_name: z.string(),
  }),
  
  async call(input) {
    // 1. 发送shutdown请求给所有成员
    for (const member of team.members) {
      await sendShutdownRequest(member.agentId)
    }
    
    // 2. 等待所有成员关闭
    await waitForShutdown(team.members)
    
    // 3. 删除团队目录
    await rm(teamDir)
  }
})
```

---

## 7. Swarm 执行后端

### 7.1 后端类型

**文件位置**：`src/utils/swarm/backends/types.ts`

| 后端 | 描述 | 适用场景 | 要求 |
|------|------|----------|------|
| in-process | 同进程AsyncLocalStorage隔离 | 资源高效、快速通信 | 无特殊要求 |
| tmux | Terminal multiplexer panes | 独立终端窗口 | tmux安装 |
| iterm2 | iTerm2原生分屏 | macOS用户 | iTerm2 + it2 CLI |

### 7.2 In-Process Runner

**文件位置**：`src/utils/swarm/inProcessRunner.ts`

这是最复杂也是最高效的执行模式：

#### 上下文隔离机制

```typescript
// 使用AsyncLocalStorage实现上下文隔离
const teammateContext = new AsyncLocalStorage<TeammateContext>()
const agentContext = new AsyncLocalStorage<AgentContext>()

// Teammate运行时入口
export async function runInProcessTeammate(identity, agentDef, prompt) {
  return teammateContext.run(identity, async () => {
    return agentContext.run(createAgentContext(identity), async () => {
      // 在隔离上下文中执行Agent逻辑
      await teammateLoop(identity, agentDef)
    })
  })
}
```

#### 持续运行循环

```
┌─────────────────────────────────────────────────────────────┐
│               Teammate 持续运行循环                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  while (!abort) {                                          │
│    // 1. 处理当前任务/Prompt                                │
│    await processPrompt(currentPrompt)                      │
│                                                             │
│    // 2. 运行Agent查询循环                                  │
│    await runAgentQuery()                                   │
│                                                             │
│    // 3. 发送空闲通知                                      │
│    await sendIdleNotification()                            │
│                                                             │
│    // 4. 等待下一条消息                                    │
│    currentPrompt = await waitForMessage()                  │
│                                                             │
│    // 5. 检查shutdown请求                                  │
│    if (isShutdownRequested()) {                            │
│      // 处理关闭协议                                       │
│      if (await handleShutdownRequest()) {                  │
│        break                                               │
│      }                                                     │
│    }                                                       │
│  }                                                         │
└─────────────────────────────────────────────────────────────┘
```

#### 权限处理

```typescript
// In-Process Teammate权限处理
async function handlePermissionRequest(request) {
  // 使用Leader的ToolUseConfirm对话框（带Worker徽章）
  if (bridgeAvailable) {
    // 通过Bridge向Leader请求权限
    const decision = await bridge.requestPermission({
      agentId: identity.agentId,
      request: request,
      badge: identity.color
    })
    return decision
  }
  
  // Mailbox备用方案
  await sendMailboxMessage({
    type: \"permission_request\",
    request: request
  })
  
  // 等待Leader响应
  const response = await waitForPermissionResponse()
  return response
}
```

#### 任务领取

```typescript
// 自动领取共享任务列表中的任务
async function claimAvailableTask() {
  const tasks = await loadSharedTasks(teamName)
  
  // 找到未分配的任务
  const availableTask = tasks.find(t => 
    t.status === \"pending\" && !t.assigned_to
  )
  
  if (availableTask) {
    // 领取任务
    availableTask.assigned_to = identity.agentId
    availableTask.status = \"in_progress\"
    await saveSharedTasks(tasks)
    
    return availableTask
  }
  
  return null
}
```

### 7.3 Tmux Backend

```typescript
// Tmux后端创建独立panes
export async function runTmuxTeammate(identity, agentDef, prompt) {
  // 创建新pane
  const paneId = await tmux.splitWindow()
  
  // 在pane中启动Claude Code
  await tmux.sendKeys(paneId, `claude --teammate ${identity.agentId}`)
  
  // 监听pane输出
  await tmux.monitorPane(paneId)
}
```

### 7.4 iTerm2 Backend

```typescript
// iTerm2原生分屏
export async function runIterm2Teammate(identity, agentDef, prompt) {
  // 使用it2 CLI创建分屏
  const session = await iterm2.splitPane()
  
  // 启动Claude Code
  await iterm2.runCommand(session, `claude --teammate ${identity.agentId}`)
}
```

---

## 8. 任务管理系统

### 8.1 任务状态定义

**文件位置**：`src/utils/tasks.ts`

```typescript
type TaskStatus = 
  | \"pending\"    // 待处理
  | \"in_progress\" // 进行中
  | \"completed\"  // 已完成
  | \"failed\"     // 失败
  | \"killed\"     // 被终止

type TaskStateBase = {
  id: string                // 任务ID（带类型前缀）
  type: TaskType            // 任务类型
  status: TaskStatus
  description: string
  startTime: number
  outputFile: string        // 结果输出文件
  outputOffset: number
}
```

### 8.2 任务工具

| 工具 | 文件位置 | 功能 |
|------|----------|------|
| TaskCreateTool | `src/tools/TaskCreateTool/` | 创建新任务 |
| TaskGetTool | `src/tools/TaskGetTool/` | 获取任务结果 |
| TaskListTool | `src/tools/TaskListTool/` | 列出所有任务 |
| TaskUpdateTool | `src/tools/TaskUpdateTool/` | 更新任务状态 |
| TaskStopTool | `src/tools/TaskStopTool/` | 停止任务 |

### 8.3 任务 ID 生成规则

```typescript
const TASK_ID_PREFIXES = {
  local_bash: \"b\",
  local_agent: \"a\",
  remote_agent: \"r\",
  in_process_teammate: \"t\",
  local_workflow: \"w\",
}

function generateTaskId(type: TaskType): string {
  const prefix = TASK_ID_PREFIXES[type]
  const timestamp = Date.now()
  const random = Math.random().toString(36).slice(2, 8)
  return `${prefix}${timestamp}${random}`
}
```

### 8.4 共享任务列表（Team模式）

```typescript
// Team共享任务文件位置
const sharedTasksPath = `.claude/teams/${teamName}/tasks.json`

// Teammate自动领取任务
async function pollSharedTasks(teamName) {
  while (true) {
    const tasks = await readSharedTasks(teamName)
    const available = tasks.find(t => 
      t.status === \"pending\" && !t.assigned_to
    )
    
    if (available) {
      await claimTask(available)
      await executeTask(available)
    }
    
    await sleep(5000)  // 每5秒检查一次
  }
}
```

---

## 9. Agent 上下文与隔离

### 9.1 AgentContext

**文件位置**：`src/utils/agentContext.ts`

```typescript
// 使用AsyncLocalStorage存储Agent身份
const agentContextStore = new AsyncLocalStorage<AgentContext>()

type AgentContext = {
  agentId: string
  sessionId: string
  parentSessionId?: string
  isSubagent: boolean
  analyticsContext: AnalyticsContext
}

// 获取当前Agent上下文
export function getAgentContext(): AgentContext | undefined {
  return agentContextStore.getStore()
}

// 在Agent上下文中运行
export function runInAgentContext(context, fn) {
  return agentContextStore.run(context, fn)
}
```

### 9.2 TeammateContext

**文件位置**：`src/utils/teammateContext.ts`

```typescript
// Teammate运行时上下文
const teammateContextStore = new AsyncLocalStorage<TeammateContext>()

type TeammateContext = {
  identity: TeammateIdentity
  toolPool: Tool[]
  permissionContext: PermissionContext
  mailboxPath: string
  isRunning: boolean
  pendingMessages: Message[]
  shutdownRequested: boolean
}

// 获取当前Teammate上下文
export function getTeammateContext(): TeammateContext | undefined {
  return teammateContextStore.getStore()
}
```

### 9.3 ToolUseContext 隔离

每个 Agent 有独立的 ToolUseContext，确保：

- **独立权限决策**：不共享父的权限状态
- **独立消息列表**：有自己的消息历史
- **独立工具池**：根据 Agent 定义过滤工具
- **独立 Hook 生命周期**：有自己的 Hook 注册

```typescript
// 为Agent创建隔离的ToolUseContext
function createAgentToolUseContext(parentContext, agentDef, identity) {
  return {
    // 继承必要的全局状态
    appState: parentContext.appState,
    
    // 独立的权限上下文
    permissionContext: createAgentPermissionContext(agentDef, parentContext),
    
    // 独立的消息列表
    messages: [],
    
    // 独立的工具池
    toolPool: assembleAgentToolPool(agentDef, parentContext),
    
    // 独立的查询引擎
    queryEngine: new QueryEngine(),
    
    // Agent身份标记
    agentId: identity.agentId,
    parentSessionId: parentContext.sessionId,
    isSubagent: true
  }
}
```

### 9.4 权限继承模式

```typescript
type PermissionInheritanceMode = 
  | \"inherit\"     // 继承父的权限模式
  | \"bubble\"      // 权限请求上浮到父
  | \"independent\" // 独立权限决策

// 创建Agent权限上下文
function createAgentPermissionContext(agentDef, parentContext) {
  switch (agentDef.permissionMode) {
    case \"inherit\":
      return parentContext.permissionContext
      
    case \"bubble\":
      return {
        ...parentContext.permissionContext,
        mode: \"bubble\",
        bubbleToParent: true
      }
      
    case \"plan\":
      return {
        mode: \"plan\",
        // Plan模式只允许只读操作
      }
      
    default:
      return createIndependentPermissionContext()
  }
}
```

---

## 10. 执行流程详解

### 10.1 runAgent 核心流程

**文件位置**：`src/tools/AgentTool/runAgent.ts`

```
runAgent(input, context)
      ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: 初始化                                             │
├─────────────────────────────────────────────────────────────┤
│ 1. 解析Agent定义和参数                                      │
│ 2. 初始化Agent特定的MCP服务器                               │
│ 3. 准备系统提示和消息                                       │
│ 4. 创建隔离的ToolUseContext                                 │
└─────────────────────────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase 2: 执行                                               │
├─────────────────────────────────────────────────────────────┤
│ 5. 调用query()函数                                          │
│ 6. 进入Agent的消息循环                                      │
│    - 接收模型响应                                           │
│    - 执行tool_use                                           │
│    - 收集tool_result                                        │
│    - 继续循环直到end_turn                                   │
│ 7. 处理进度回调                                             │
└─────────────────────────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase 3: 清理与返回                                         │
├─────────────────────────────────────────────────────────────┤
│ 8. 记录transcript到sidechain JSONL                          │
│ 9. 清理MCP连接                                             │
│ 10. 清理Hook注册                                           │
│ 11. 返回AgentResult                                        │
└─────────────────────────────────────────────────────────────┘
```

### 10.2 同步执行模式

```typescript
// 同步执行 - 阻塞等待结果
async function runSyncAgent(input, context) {
  const agentContext = await prepareAgentContext(input, context)
  
  // 执行查询循环
  const result = await query({
    prompt: input.prompt,
    context: agentContext,
    onProgress: input.onProgress
  })
  
  // 等待完成并返回
  return {
    status: \"completed\",
    response: result.messages[result.messages.length - 1],
    usage: result.usage
  }
}
```

### 10.3 后台执行模式

```typescript
// 后台执行 - 立即返回ID，完成后通知
async function runBackgroundAgent(input, context) {
  const taskId = generateTaskId(\"local_agent\")
  const outputFile = `.claude/tasks/${taskId}.json`
  
  // 创建任务状态
  await updateTaskState(taskId, { status: \"running\" })
  
  // 启动后台执行
  const taskPromise = runAgentInternal(input, context)
    .then(result => {
      // 保存结果
      fs.writeJSON(outputFile, result)
      
      // 更新状态
      updateTaskState(taskId, { status: \"completed\" })
      
      // 发送通知
      sendTaskNotification(taskId, \"completed\")
    })
    .catch(error => {
      updateTaskState(taskId, { status: \"failed\" })
      sendTaskNotification(taskId, \"failed\")
    })
  
  // 注册到任务列表
  registerBackgroundTask(taskId, taskPromise)
  
  // 立即返回ID
  return {
    status: \"async_launched\",
    taskId: taskId
  }
}
```

### 10.4 Teammate 持续运行模式

```typescript
// Teammate模式 - 持续运行，接收消息
async function runTeammateAgent(identity, agentDef, initialPrompt) {
  // 创建Teammate上下文
  const teammateContext = createTeammateContext(identity, agentDef)
  
  // 进入持续运行循环
  while (!teammateContext.abort) {
    // 处理当前任务/Prompt
    if (teammateContext.currentPrompt) {
      await processPrompt(teammateContext)
      teammateContext.currentPrompt = null
    }
    
    // 检查邮箱消息
    const messages = await receiveMailboxMessages(identity)
    for (const msg of messages) {
      if (msg.type === \"shutdown_request\") {
        // 处理关闭请求
        const approved = await handleShutdown(teammateContext)
        if (approved) break
      } else {
        // 处理普通消息
        teammateContext.currentPrompt = msg.content
      }
    }
    
    // 检查共享任务
    const task = await claimAvailableTask(identity.teamName)
    if (task) {
      teammateContext.currentPrompt = task.description
    }
    
    // 空闲等待
    if (!teammateContext.currentPrompt) {
      await sendIdleNotification(identity)
      teammateContext.currentPrompt = await waitForMessage(identity)
    }
  }
  
  // 清理
  await cleanupTeammate(identity)
}
```

### 10.5 Worktree 隔离模式

```typescript
// Worktree隔离 - 在独立Git工作树中执行
async function runWorktreeAgent(input, context) {
  // 创建Worktree
  const worktreePath = await createWorktree({
    branch: `agent-${input.description}`,
    path: `.claude/worktrees/${taskId}`
  })
  
  // 修改工作目录
  input.cwd = worktreePath
  
  // 执行Agent
  const result = await runAgent(input, context)
  
  // 清理Worktree
  if (result.status === \"completed\") {
    await removeWorktree(worktreePath)
  } else {
    // 失败时保留Worktree供检查
    console.log(`Worktree preserved at: ${worktreePath}`)
  }
  
  return result
}
```

---

## 11. 源码文件索引

### 11.1 AgentTool 核心文件

| 文件路径 | 大小估计 | 核心职责 |
|----------|----------|----------|
| `src/tools/AgentTool/AgentTool.tsx` | ~40KB | 工具定义、参数解析、执行调度 |
| `src/tools/AgentTool/runAgent.ts` | ~30KB | 核心执行引擎、查询循环 |
| `src/tools/AgentTool/forkSubagent.ts` | ~15KB | Fork子代理实现 |
| `src/tools/AgentTool/loadAgentsDir.ts` | ~20KB | 自定义Agent加载 |
| `src/tools/AgentTool/agentToolUtils.ts` | ~10KB | 生命周期管理 |
| `src/tools/AgentTool/constants.ts` | ~3KB | ID前缀、默认值 |
| `src/tools/AgentTool/built-in/*.ts` | ~15KB | 内置Agent类型定义 |

### 11.2 Coordinator 相关文件

| 文件路径 | 大小估计 | 核心职责 |
|----------|----------|----------|
| `src/coordinator/coordinatorMode.ts` | ~50KB | Coordinator系统提示、工作流定义 |
| `src/coordinator/*.ts` | ~30KB | 其他协调逻辑 |

### 11.3 通信相关文件

| 文件路径 | 大小估计 | 核心职责 |
|----------|----------|----------|
| `src/tools/SendMessageTool/SendMessageTool.ts` | ~25KB | Agent间消息通信 |
| `src/utils/teammateMailbox.ts` | ~15KB | 文件消息传递系统 |

### 11.4 Team 相关文件

| 文件路径 | 大小估计 | 核心职责 |
|----------|----------|----------|
| `src/tools/TeamCreateTool/TeamCreateTool.ts` | ~15KB | 团队创建 |
| `src/tools/TeamDeleteTool/TeamDeleteTool.ts` | ~10KB | 团队删除 |
| `src/tools/shared/spawnMultiAgent.ts` | ~20KB | Teammate创建逻辑 |

### 11.5 Swarm 执行后端文件

| 文件路径 | 大小估计 | 核心职责 |
|----------|----------|----------|
| `src/utils/swarm/backends/types.ts` | ~5KB | 后端类型定义 |
| `src/utils/swarm/inProcessRunner.ts` | ~100KB | 进程内运行器（核心） |
| `src/utils/swarm/backends/*.ts` | ~30KB | tmux/iterm2实现 |

### 11.6 任务管理文件

| 文件路径 | 大小估计 | 核心职责 |
|----------|----------|----------|
| `src/tasks/LocalAgentTask/LocalAgentTask.tsx` | ~30KB | Agent任务状态管理 |
| `src/tasks/InProcessTeammateTask/types.ts` | ~10KB | Teammate状态定义 |
| `src/utils/tasks.ts` | ~15KB | 任务创建、列表、更新 |
| `src/tools/TaskCreateTool/` | ~10KB | 创建任务工具 |
| `src/tools/TaskGetTool/` | ~8KB | 获取任务工具 |
| `src/tools/TaskListTool/` | ~8KB | 列出任务工具 |
| `src/tools/TaskUpdateTool/` | ~10KB | 更新任务工具 |
| `src/tools/TaskStopTool/` | ~15KB | 停止任务工具 |

### 11.7 上下文与隔离文件

| 文件路径 | 大小估计 | 核心职责 |
|----------|----------|----------|
| `src/utils/agentContext.ts` | ~10KB | AsyncLocalStorage Agent上下文 |
| `src/utils/teammateContext.ts` | ~10KB | Teammate运行时上下文 |

### 11.8 常量定义文件

| 文件路径 | 大小估计 | 核心职责 |
|----------|----------|----------|
| `src/constants/tools.ts` | ~10KB | ALL_AGENT_DISALLOWED_TOOLS等 |

---

## 12. 设计模式总结

### 12.1 核心设计模式

| 模式 | 应用场景 | 实现位置 |
|------|----------|----------|
| **AsyncLocalStorage隔离** | Agent上下文隔离 | agentContext.ts, teammateContext.ts |
| **工厂模式** | Agent定义构建 | loadAgentsDir.ts, builtInAgents.ts |
| **策略模式** | 执行模式选择（同步/后台/Teammate） | AgentTool.tsx |
| **观察者模式** | 任务通知系统 | TaskStateStore |
| **模板方法** | Agent执行流程 | runAgent.ts |
| **责任链** | 权限决策链 | permissions.ts |
| **代理模式** | Mailbox消息传递 | teammateMailbox.ts |
| **命令模式** | SendMessage工具 | SendMessageTool.ts |
| **状态模式** | Teammate运行循环 | inProcessRunner.ts |
| **装饰器模式** | Fork子代理（继承+扩展） | forkSubagent.ts |

### 12.2 关键设计决策

#### 1. 为什么用 AsyncLocalStorage？

- **无需显式传参**：上下文自动传递到嵌套调用
- **类型安全**：编译时保证上下文类型
- **性能高效**：不创建新进程或线程
- **隔离清晰**：每个Agent有独立上下文

#### 2. 为什么用文件系统做 Mailbox？

- **进程无关**：不同Backend都可访问
- **持久化**：消息不因崩溃丢失
- **调试友好**：可直接查看文件内容
- **并发安全**：Lockfile保证写入安全

#### 3. 为什么 Coordinator 不直接编辑代码？

- **角色清晰**：Coordinator是调度者，不是执行者
- **能力分离**：Workers有完整工具，Coordinator受限
- **避免偏见**：Coordinator综合发现，不应带实现偏见
- **审计清晰**：修改记录可追溯到具体Worker

### 12.3 可复用的架构组件

```typescript
// 1. Agent定义接口（可复用）
interface AgentDef {
  type: string
  description: string
  tools?: string[]
  model?: string
  permissionMode?: PermissionMode
  mcpServers?: string[]
  hooks?: HookConfig
  prompt?: string
}

// 2. Agent执行引擎（可复用）
class AgentExecutor {
  async run(input: AgentInput): Promise<AgentResult> {
    const context = await this.prepareContext(input)
    const result = await this.queryLoop(context)
    await this.cleanup(context)
    return result
  }
}

// 3. Teammate运行循环（可复用）
class TeammateLoop {
  async start() {
    while (!this.abort) {
      await this.processCurrentTask()
      await this.checkMessages()
      await this.claimSharedTask()
      await this.waitForNext()
    }
  }
}

// 4. Mailbox消息系统（可复用）
class Mailbox {
  async send(to: string, message: Message): Promise<void>
  async receive(): Promise<Message[]>
  async lock(): Promise<void>
  async unlock(): Promise<void>
}

// 5. Shutdown协议（可复用）
class ShutdownProtocol {
  async requestShutdown(agent: Agent): Promise<void>
  async handleRequest(): Promise<boolean>
  async respond(approved: boolean): Promise<void>
}
```

### 12.4 改造建议

#### 对于轻量级开发工具

建议保留的Agent相关模块：

| 保留 | 简化 | 删除 |
|------|------|------|
| AgentTool核心 | runAgent简化 | Team系统完整版 |
| 基础Agent类型 | 后台任务简化 | Coordinator完整版 |
| AsyncLocalStorage | Mailbox简化 | Swarm多Backend |
| 同步执行 | Fork简化 | iTerm2/tmux后端 |

#### 最小Agent系统实现

```typescript
// 最小Agent系统结构
const minimalAgentSystem = {
  // 核心
  AgentTool: \"~30KB\",       // 工具入口
  runAgent: \"~20KB\",        // 执行引擎（简化）
  agentContext: \"~5KB\",     // 上下文隔离
  
  // 类型
  builtInAgents: \"~10KB\",   // general-purpose + Explore
  
  // 执行
  syncExecution: \"完整保留\",
  backgroundExecution: \"简化版\",
  fork: \"可选保留\",
  
  // 通信
  SendMessage: \"~15KB\",     // 基础消息
  Mailbox: \"~10KB\",         // 文件消息（简化）
  
  // 总计约 100KB
}
```

---

*文档生成日期：2026-04-10*
*基于 Claude Code 源码深度分析*
*用于框架改造参考*
