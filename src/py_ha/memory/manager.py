"""
Memory Manager - JVM-style Memory Management Controller

整合所有记忆管理组件:
- MemoryHeap: 分代记忆堆
- GarbageCollector: 垃圾收集器
- HotspotDetector: 热点检测器
- AutoAssembler: 自动装配器
- ExecutionStack: 执行栈 (类似 JVM 栈)
- ProgressCounter: 进度计数器 (类似 JVM PC)
- MetaSpace: 元空间 (类似 JVM Metaspace)
"""

from typing import Any
from pydantic import BaseModel, Field
import time

from py_ha.memory.heap import (
    MemoryHeap,
    MemoryEntry,
    MemoryRegion,
)
from py_ha.memory.gc import (
    GarbageCollector,
    GCResult,
    GCAlgorithm,
)
from py_ha.memory.hotspot import HotspotDetector, HotspotInfo
from py_ha.memory.assembler import AutoAssembler, AssemblyTemplate


class StackFrame(BaseModel):
    """
    栈帧 - 类似 JVM 栈帧

    JVM 栈帧包含:
    - 局部变量表
    - 操作数栈
    - 动态链接
    - 返回地址

    Agent 对应:
    - 局部上下文
    - 操作状态
    - 任务链接
    - 返回结果
    """

    frame_id: str = Field(..., description="帧ID")
    task_name: str = Field(..., description="任务名称")
    local_context: dict[str, Any] = Field(default_factory=dict, description="局部上下文")
    operand_stack: list[Any] = Field(default_factory=list, description="操作数栈")
    return_address: str | None = Field(default=None, description="返回地址")
    created_at: float = Field(default_factory=time.time, description="创建时间")

    def push_operand(self, value: Any) -> None:
        """压入操作数"""
        self.operand_stack.append(value)

    def pop_operand(self) -> Any | None:
        """弹出操作数"""
        return self.operand_stack.pop() if self.operand_stack else None

    def set_local(self, key: str, value: Any) -> None:
        """设置局部变量"""
        self.local_context[key] = value

    def get_local(self, key: str, default: Any = None) -> Any:
        """获取局部变量"""
        return self.local_context.get(key, default)


class ExecutionStack:
    """
    执行栈 - 类似 JVM 虚拟机栈

    JVM 栈特性:
    - 每个方法调用创建一个栈帧
    - 方法返回弹出栈帧
    - 栈深度有限制

    Agent 对应:
    - 每个任务创建一个栈帧
    - 任务完成弹出栈帧
    - 局部上下文隔离
    """

    def __init__(self, max_depth: int = 100) -> None:
        self.max_depth = max_depth
        self._frames: list[StackFrame] = []

    def push_frame(self, task_name: str) -> StackFrame | None:
        """
        压入栈帧 - 类似 JVM 方法调用

        Args:
            task_name: 任务名称

        Returns:
            新栈帧 (栈溢出时返回None)
        """
        if len(self._frames) >= self.max_depth:
            return None  # StackOverflow

        import uuid
        frame = StackFrame(
            frame_id=str(uuid.uuid4()),
            task_name=task_name,
            return_address=self._frames[-1].frame_id if self._frames else None,
        )
        self._frames.append(frame)
        return frame

    def pop_frame(self) -> StackFrame | None:
        """
        弹出栈帧 - 类似 JVM 方法返回

        Returns:
            弹出的栈帧
        """
        return self._frames.pop() if self._frames else None

    def current_frame(self) -> StackFrame | None:
        """获取当前栈帧"""
        return self._frames[-1] if self._frames else None

    def get_frame(self, frame_id: str) -> StackFrame | None:
        """获取指定栈帧"""
        for frame in self._frames:
            if frame.frame_id == frame_id:
                return frame
        return None

    def depth(self) -> int:
        """栈深度"""
        return len(self._frames)

    def is_overflow(self) -> bool:
        """是否栈溢出"""
        return len(self._frames) >= self.max_depth

    def clear(self) -> int:
        """清空栈"""
        count = len(self._frames)
        self._frames.clear()
        return count


class ProgressCounter(BaseModel):
    """
    进度计数器 - 类似 JVM 程序计数器

    JVM PC Register:
    - 记录当前执行位置
    - 每条指令更新

    Agent 对应:
    - 记录当前任务进度
    - 每个步骤更新
    """

    current_step: int = Field(default=0, ge=0, description="当前步骤")
    total_steps: int = Field(default=0, ge=0, description="总步骤")
    current_task: str | None = Field(default=None, description="当前任务")
    history: list[str] = Field(default_factory=list, description="执行历史")

    def advance(self) -> int:
        """前进一步"""
        self.current_step += 1
        return self.current_step

    def set_task(self, task: str, total_steps: int) -> None:
        """设置当前任务"""
        self.current_task = task
        self.total_steps = total_steps
        self.current_step = 0

    def record_history(self, action: str) -> None:
        """记录执行历史"""
        self.history.append(f"{self.current_step}: {action}")

    def progress_percent(self) -> float:
        """进度百分比"""
        if self.total_steps <= 0:
            return 0.0
        return (self.current_step / self.total_steps) * 100


class MetaSpace(BaseModel):
    """
    元空间 - 类似 JVM Metaspace

    JVM Metaspace:
    - 存储类信息
    - 方法区替代
    - 不受 GC 管理

    Agent 对应:
    - 存储 Agent 定义
    - 存储工具规范
    - 存储核心配置
    """

    agent_specs: dict[str, Any] = Field(default_factory=dict, description="Agent规范")
    tool_specs: dict[str, Any] = Field(default_factory=dict, description="工具规范")
    knowledge_defs: dict[str, str] = Field(default_factory=dict, description="知识定义")
    config: dict[str, Any] = Field(default_factory=dict, description="配置")

    def register_agent(self, name: str, spec: Any) -> None:
        """注册Agent规范"""
        self.agent_specs[name] = spec

    def get_agent(self, name: str) -> Any | None:
        """获取Agent规范"""
        return self.agent_specs.get(name)

    def register_tool(self, name: str, spec: Any) -> None:
        """注册工具规范"""
        self.tool_specs[name] = spec

    def get_tool(self, name: str) -> Any | None:
        """获取工具规范"""
        return self.tool_specs.get(name)

    def define_knowledge(self, key: str, content: str) -> None:
        """定义知识"""
        self.knowledge_defs[key] = content

    def get_knowledge(self, key: str) -> str | None:
        """获取知识"""
        return self.knowledge_defs.get(key)

    def set_config(self, key: str, value: Any) -> None:
        """设置配置"""
        self.config[key] = value

    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置"""
        return self.config.get(key, default)


class MemoryManager:
    """
    记忆管理器 - JVM-style 记忆管理总控制器

    整合所有记忆管理组件，提供统一的记忆管理接口:

    组件对应:
    - MemoryHeap → JVM Heap (分代记忆)
    - ExecutionStack → JVM Stack (执行栈)
    - ProgressCounter → JVM PC Register (进度计数)
    - MetaSpace → JVM Metaspace (元空间)
    - GarbageCollector → JVM GC (记忆回收)
    - HotspotDetector → JIT Hotspot Detection (热点检测)
    - AutoAssembler → JIT Compiler (自动装配)
    """

    def __init__(
        self,
        # Heap 参数 (类似 JVM Heap 参数)
        eden_size: int = 1000,
        survivor_size: int = 500,
        old_size: int = 5000,
        permanent_size: int = 10000,
        survivor_ratio: int = 8,
        promotion_threshold: int = 15,
        large_entry_threshold: int = 500,
        # Stack 参数 (类似 JVM Stack 参数)
        stack_max_depth: int = 100,
        # GC 参数 (类似 JVM GC 参数)
        reference_threshold: int = 0,
        compact_threshold: float = 0.8,
        target_pause_time: float = 0.5,
        # JIT 参数 (类似 JVM JIT 参数)
        compile_threshold: int = 100,
        back_edge_threshold: int = 50,
        max_inline_size: int = 1000,
        cache_size: int = 100,
    ) -> None:
        # 核心组件
        self.heap = MemoryHeap(
            eden_size=eden_size,
            survivor_size=survivor_size,
            old_size=old_size,
            permanent_size=permanent_size,
            survivor_ratio=survivor_ratio,
            promotion_threshold=promotion_threshold,
            large_entry_threshold=large_entry_threshold,
        )

        self.stack = ExecutionStack(max_depth=stack_max_depth)
        self.progress_counter = ProgressCounter()
        self.meta_space = MetaSpace()

        # GC 组件
        self.gc = GarbageCollector(
            promotion_threshold=promotion_threshold,
            reference_threshold=reference_threshold,
            compact_threshold=compact_threshold,
            target_pause_time=target_pause_time,
        )

        # JIT 组件
        self.hotspot_detector = HotspotDetector(
            compile_threshold=compile_threshold,
            back_edge_threshold=back_edge_threshold,
        )

        self.auto_assembler = AutoAssembler(
            max_inline_size=max_inline_size,
            cache_size=cache_size,
        )

        # 配置
        self.config = {
            "eden_size": eden_size,
            "survivor_size": survivor_size,
            "old_size": old_size,
            "promotion_threshold": promotion_threshold,
            "compile_threshold": compile_threshold,
        }

        # 统计
        self._stats = {
            "total_allocations": 0,
            "total_gc_invocations": 0,
            "total_hotspot_detections": 0,
            "total_assemblies": 0,
            "start_time": time.time(),
        }

    # ==================== 记忆分配 ====================

    def allocate_memory(
        self,
        content: str,
        importance: int = 50,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryEntry | None:
        """
        分配记忆 - 类似 JVM 对象分配

        Args:
            content: 内容
            importance: 重要性 (0-100)
            metadata: 元数据

        Returns:
            分配的记忆条目
        """
        entry = self.heap.allocate(content, importance, metadata)
        if entry:
            self._stats["total_allocations"] += 1

            # 检查是否需要自动GC
            self.gc.auto_gc(self.heap)

        return entry

    def get_memory(self, id: str) -> MemoryEntry | None:
        """获取记忆条目"""
        entry = self.heap.get_entry(id)
        if entry:
            # 记录热点
            self.hotspot_detector.record_knowledge_reference(id)
        return entry

    # ==================== GC 控制 ====================

    def invoke_gc_minor(self) -> GCResult:
        """
        触发 Minor GC - 类似 JVM System.gc() 或自动触发

        收集新生代 (Eden + Survivor)
        """
        result = self.gc.minor_gc(self.heap)
        self._stats["total_gc_invocations"] += 1
        return result

    def invoke_gc_major(self) -> GCResult:
        """
        触发 Major GC - 收集老年代
        """
        result = self.gc.major_gc(self.heap)
        self._stats["total_gc_invocations"] += 1
        return result

    def invoke_gc_full(self) -> GCResult:
        """
        触发 Full GC - 收集全部区域
        """
        result = self.gc.full_gc(self.heap)
        self._stats["total_gc_invocations"] += 1
        return result

    def auto_gc(self) -> GCResult | None:
        """
        自动GC - 根据内存压力自动触发
        """
        result = self.gc.auto_gc(self.heap)
        if result:
            self._stats["total_gc_invocations"] += 1
        return result

    # ==================== 热点检测与装配 ====================

    def detect_hotspots(self) -> list[HotspotInfo]:
        """
        检测热点 - 类似 JIT 扫描热点方法
        """
        hotspots = self.hotspot_detector.detect_hotspots()
        self._stats["total_hotspot_detections"] = len(hotspots)
        return hotspots

    def auto_assemble(self) -> list[AssemblyTemplate]:
        """
        自动装配 - 类似 JIT 编译热点方法

        检测热点并自动装配
        """
        hotspots = self.detect_hotspots()
        templates = []

        for hotspot in hotspots:
            template = self.auto_assembler.assemble(
                hotspot,
                knowledge_base=self.meta_space.knowledge_defs,
            )
            if template:
                templates.append(template)
                self._stats["total_assemblies"] += 1

        return templates

    def get_assembled_template(self, name: str) -> AssemblyTemplate | None:
        """获取已装配的模板"""
        return self.auto_assembler.get_template(name)

    # ==================== 执行栈管理 ====================

    def push_task(self, task_name: str) -> StackFrame | None:
        """
        压入任务栈帧 - 类似 JVM 方法调用
        """
        return self.stack.push_frame(task_name)

    def pop_task(self) -> StackFrame | None:
        """
        弹出任务栈帧 - 类似 JVM 方法返回
        """
        return self.stack.pop_frame()

    def current_task(self) -> StackFrame | None:
        """获取当前任务栈帧"""
        return self.stack.current_frame()

    # ==================== 进度管理 ====================

    def set_task_progress(self, task: str, total_steps: int) -> None:
        """设置任务进度"""
        self.progress_counter.set_task(task, total_steps)

    def advance_progress(self) -> int:
        """前进一步"""
        return self.progress_counter.advance()

    def get_progress(self) -> float:
        """获取进度百分比"""
        return self.progress_counter.progress_percent()

    # ==================== 元空间管理 ====================

    def register_agent_spec(self, name: str, spec: Any) -> None:
        """注册Agent规范到元空间"""
        self.meta_space.register_agent(name, spec)

    def define_knowledge(self, key: str, content: str) -> None:
        """
        定义核心知识 - 存入 Permanent 区

        高重要性知识，永不回收
        """
        self.meta_space.define_knowledge(key, content)
        # 同时存入 Permanent Memory
        self.heap.permanent.store_knowledge(key, content, importance=100)

    def get_knowledge(self, key: str) -> str | None:
        """获取知识"""
        # 先从热点检测器记录引用
        self.hotspot_detector.record_knowledge_reference(key)
        return self.meta_space.get_knowledge(key)

    # ==================== 综合状态 ====================

    def get_memory_status(self) -> dict[str, Any]:
        """
        获取记忆状态 - 类似 JVM 内存状态报告
        """
        return {
            "heap": self.heap.get_stats(),
            "stack": {
                "depth": self.stack.depth(),
                "max_depth": self.stack.max_depth,
                "overflow": self.stack.is_overflow(),
            },
            "progress": {
                "current_step": self.progress_counter.current_step,
                "total_steps": self.progress_counter.total_steps,
                "percent": self.progress_counter.progress_percent(),
            },
            "meta_space": {
                "agents_count": len(self.meta_space.agent_specs),
                "tools_count": len(self.meta_space.tool_specs),
                "knowledge_count": len(self.meta_space.knowledge_defs),
            },
            "gc": self.gc.get_collector_stats(),
            "hotspot": self.hotspot_detector.get_stats(),
            "assembler": self.auto_assembler.get_stats(),
            "runtime_stats": self._stats,
        }

    def get_health_report(self) -> dict[str, Any]:
        """
        获取健康报告 - 综合评估记忆管理状态
        """
        heap_stats = self.heap.get_stats()

        # 计算内存压力
        eden_pressure = heap_stats["eden_size"] / heap_stats["eden_max"]
        old_pressure = heap_stats["old_size"] / heap_stats["old_max"]

        # 判断状态
        if eden_pressure > 0.9 or old_pressure > 0.9:
            status = "critical"
        elif eden_pressure > 0.7 or old_pressure > 0.7:
            status = "warning"
        else:
            status = "healthy"

        return {
            "status": status,
            "eden_pressure": eden_pressure,
            "old_pressure": old_pressure,
            "gc_count": heap_stats["minor_gc_count"] + heap_stats["major_gc_count"] + heap_stats["full_gc_count"],
            "hotspots_count": len(self.hotspot_detector.detect_hotspots()),
            "assembled_count": len(self.auto_assembler._template_cache),
            "recommendations": self._generate_recommendations(status, eden_pressure, old_pressure),
        }

    def _generate_recommendations(self, status: str, eden_pressure: float, old_pressure: float) -> list[str]:
        """生成优化建议"""
        recommendations = []

        if eden_pressure > 0.8:
            recommendations.append("建议触发 Minor GC 清理 Eden 区")

        if old_pressure > 0.8:
            recommendations.append("建议触发 Major GC 清理 Old 区")

        if status == "critical":
            recommendations.append("建议触发 Full GC 全面清理")

        hotspots = self.hotspot_detector.detect_hotspots()
        if len(hotspots) > 10:
            recommendations.append(f"检测到 {len(hotspots)} 个热点，建议自动装配优化")

        return recommendations

    # ==================== 便捷方法 ====================

    def store_conversation(self, message: str, role: str = "user", importance: int = 50) -> MemoryEntry | None:
        """
        存储对话消息 - 便捷方法

        Args:
            message: 消息内容
            role: 角色 (user/assistant/tool)
            importance: 重要性

        Returns:
            存储的记忆条目
        """
        metadata = {"role": role, "timestamp": time.time()}
        return self.allocate_memory(message, importance, metadata)

    def store_important_knowledge(self, key: str, content: str) -> None:
        """
        存储重要知识 - 便捷方法

        存入 Permanent 区，永不回收
        """
        self.define_knowledge(key, content)

    def record_tool_usage(self, tool_name: str, execution_time: float = 0.0) -> None:
        """
        记录工具使用 - 便捷方法

        用于热点检测
        """
        self.hotspot_detector.record_tool_call(tool_name, execution_time)

    def optimize_if_needed(self) -> dict[str, Any]:
        """
        自动优化 - 类似 JVM 的自适应优化

        根据当前状态自动执行:
        1. GC (如果内存压力大)
        2. 热点装配 (如果有热点)
        """
        health = self.get_health_report()
        actions = {}

        # 自动GC
        if health["status"] in ("warning", "critical"):
            gc_result = self.auto_gc()
            if gc_result:
                actions["gc"] = gc_result.model_dump()

        # 自动装配热点
        hotspots = self.detect_hotspots()
        if hotspots:
            templates = self.auto_assemble()
            actions["assembled"] = len(templates)

        return actions