# Changelog

All notable changes to HarnessGenJ will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.6] - 2026-04-08

### Added
- **用户感知通知模块 (UserNotifier)**: 实时输出框架运行状态，增强用户感知
  - 工作流开始/结束通知
  - 阶段执行状态通知
  - 角色任务处理通知
  - **GAN积分变化实时通知**: 积分更新时立即输出到 stderr
  - 问题发现通知
- **详细模式输出**: 输出完整的工作流执行过程和积分变化汇总
- **简洁模式**: 只输出关键节点信息
- **调试模式**: 包含详细调试信息

### Changed
- `ScoreManager._apply_delta()` 现在会触发积分变化通知
- `WorkflowCoordinator.execute_stage()` 现在会输出阶段状态
- `AdversarialWorkflow.execute_adversarial_review()` 现在会输出审查过程
- `Engine.develop()` 现在会输出工作流开始/完成通知

### Output Example
```
[HGJ] ═══════════════════════════════════════════════════════
[HGJ] [12:34:56] 🚀 工作流开始: feature
[HGJ]    阶段: requirement → design → development → testing
[HGJ]   ▶ 阶段 'development' 开始
[HGJ]     角色: developer_1
[HGJ]    [Developer] developer_1 正在处理: Stage: development
[HGJ]      📊 [Score] Developer +10 (一轮通过) → 85
[HGJ]  ✅ 工作流完成: feature (耗时 1.2s)
[HGJ] ═══════════════════════════════════════════════════════
```

## [1.2.5] - 2026-04-08

### Fixed
- **Hooks脚本调用实际代码审查**: `trigger_adversarial_review()` 现在会调用 `Harness.quick_review()` 执行实际代码审查
- Hooks脚本发现问题时会同时更新 Developer 和 CodeReviewer 积分
- 审查结果会记录到开发日志中

### Added
- 新增 5 个 Hooks 脚本审查功能测试用例

## [1.2.4] - 2026-04-08

### Fixed
- **Hooks模式触发TriggerManager**: `hybrid_integration.py:296-302` 现在即使 Hooks 模式也会触发 TriggerManager
- **GAN对抗机制激活**: `develop()` 方法现在集成 `AdversarialWorkflow` 进行代码审查
- **任务状态流转**: 任务创建后状态正确流转 pending → in_progress → reviewing → completed
- **角色协作消息订阅**: 角色现在正确订阅消息总线，协作机制生效
- **双向积分激励**: 审查执行后积分规则正确触发

### Added
- 新增 `test_gan_activation.py` 测试文件，包含 10 个测试用例

## [1.2.3] - 2026-04-06

### Added
- 主动文档维护系统 (DocumentMaintenanceManager)
- 需求检测器 (RequirementDetector)
- 确认管理器 (ConfirmationManager)

## [1.2.2] - 2026-04-05

### Added
- Chat 模式增强功能
- 质量追踪系统 (QualityTracker)
- 失败模式检测

## [1.2.1] - 2026-04-04

### Fixed
- 修复触发链路断裂问题

### Added
- 首次接入引导增强

## [1.2.0] - 2026-04-03

### Changed
- **架构重构优化**: 解决模块职责冗余问题

## [1.1.1] - 2026-04-02

### Added
- 首次接入引导系统

## [1.1.0] - 2026-04-01

### Added
- 初始版本发布
- 角色驱动协作系统
- JVM风格记忆管理
- GAN对抗审查机制