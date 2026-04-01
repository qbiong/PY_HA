"""
Tests for Memory Module - JVM-style Memory Management
"""

import pytest
import time

from py_ha.memory import (
    MemoryManager,
    MemoryHeap,
    EdenMemory,
    SurvivorMemory,
    OldMemory,
    PermanentMemory,
    GarbageCollector,
    HotspotDetector,
    AutoAssembler,
)
from py_ha.memory.heap import MemoryEntry, MemoryRegion
from py_ha.memory.gc import GCAlgorithm, GCResult


class TestMemoryHeap:
    """测试分代记忆堆"""

    def test_create_heap(self) -> None:
        """创建记忆堆"""
        heap = MemoryHeap(
            eden_size=100,
            survivor_size=50,
            old_size=200,
        )
        assert heap.eden.max_size == 100
        assert heap.survivor_0.max_size == 50
        assert heap.old.max_size == 200

    def test_allocate_to_eden(self) -> None:
        """分配到Eden区"""
        heap = MemoryHeap(eden_size=100)
        entry = heap.allocate("test content", importance=50)

        assert entry is not None
        assert entry.region == MemoryRegion.EDEN
        assert heap.eden.size() == 1

    def test_allocate_large_to_old(self) -> None:
        """大对象直接进Old"""
        heap = MemoryHeap(
            eden_size=100,
            old_size=200,
            large_entry_threshold=100,
        )

        # 大内容直接进Old
        large_content = "x" * 150  # 超过阈值
        entry = heap.allocate(large_content, importance=50)

        assert entry is not None
        assert entry.region == MemoryRegion.OLD

    def test_allocate_high_importance_to_old(self) -> None:
        """高重要性直接进Old"""
        heap = MemoryHeap(eden_size=100, old_size=200)

        entry = heap.allocate("important content", importance=95)

        assert entry is not None
        assert entry.region == MemoryRegion.OLD

    def test_get_entry(self) -> None:
        """获取条目"""
        heap = MemoryHeap()
        entry = heap.allocate("test", importance=50)

        retrieved = heap.get_entry(entry.id)
        assert retrieved is not None
        assert retrieved.id == entry.id


class TestMemoryEntry:
    """测试记忆条目"""

    def test_create_entry(self) -> None:
        """创建条目"""
        entry = MemoryEntry(
            id="test-id",
            content="test content",
            importance=50,
        )
        assert entry.importance == 50
        assert entry.age == 0
        assert entry.references == 0

    def test_entry_alive(self) -> None:
        """存活判断"""
        entry = MemoryEntry(
            id="test-id",
            content="test content",
            importance=50,
        )

        # 刚创建的条目，最近访问过 -> 存活
        assert entry.is_alive()

        # 模拟旧条目 (超过1小时未访问)
        entry.last_accessed = time.time() - 4000
        entry.importance = 30  # 低重要性
        entry.references = 0   # 无引用
        assert not entry.is_alive()

        # 高重要性 -> 存活
        entry.importance = 80
        assert entry.is_alive()

        # 有引用 -> 存活
        entry.importance = 20
        entry.references = 5
        assert entry.is_alive()

    def test_entry_touch(self) -> None:
        """更新访问"""
        entry = MemoryEntry(id="test-id", content="test")
        old_time = entry.last_accessed

        time.sleep(0.01)
        entry.touch()

        assert entry.references == 1
        assert entry.last_accessed > old_time


class TestGarbageCollector:
    """测试垃圾收集器"""

    def test_minor_gc(self) -> None:
        """Minor GC测试"""
        heap = MemoryHeap(eden_size=10, survivor_size=5, old_size=20)
        gc = GarbageCollector()

        # 填充Eden
        for i in range(10):
            heap.allocate(f"content {i}", importance=30)

        assert heap.eden.size() == 10

        # 执行Minor GC
        result = gc.minor_gc(heap)

        assert result.gc_type == "minor"
        assert result.algorithm == GCAlgorithm.COPYING
        # 大部分低重要性内容被清除
        assert heap.eden.size() == 0

    def test_major_gc(self) -> None:
        """Major GC测试"""
        heap = MemoryHeap(eden_size=10, old_size=20)
        gc = GarbageCollector()

        # 直接分配到Old
        for i in range(15):
            large_content = "x" * 600  # 大内容进Old
            heap.allocate(large_content, importance=30)

        assert heap.old.size() > 0

        # 执行Major GC
        result = gc.major_gc(heap)

        assert result.gc_type == "major"
        assert result.algorithm == GCAlgorithm.MARK_COMPACT

    def test_full_gc(self) -> None:
        """Full GC测试"""
        heap = MemoryHeap(eden_size=10, old_size=20)
        gc = GarbageCollector()

        # 填充各区域
        for i in range(10):
            heap.allocate(f"eden content {i}", importance=30)
        for i in range(5):
            heap.allocate("x" * 600, importance=30)  # 进Old

        # 执行Full GC
        result = gc.full_gc(heap)

        assert result.gc_type == "full"

    def test_auto_gc(self) -> None:
        """自动GC测试"""
        heap = MemoryHeap(eden_size=5, old_size=10)
        gc = GarbageCollector()

        # 未满时不触发
        heap.allocate("content", importance=30)
        result = gc.auto_gc(heap)
        assert result is None

        # Eden满时触发Minor GC
        for i in range(5):
            heap.allocate(f"content {i}", importance=30)
        result = gc.auto_gc(heap)
        assert result is not None
        assert result.gc_type == "minor"


class TestHotspotDetector:
    """测试热点检测器"""

    def test_record_tool_call(self) -> None:
        """记录工具调用"""
        detector = HotspotDetector(compile_threshold=10)

        for i in range(15):
            detector.record_tool_call("test_tool", execution_time=0.1)

        assert detector.is_hotspot("test_tool")

    def test_hotspot_detection(self) -> None:
        """热点检测"""
        detector = HotspotDetector(compile_threshold=10)

        # 记录调用
        for i in range(15):
            detector.record_tool_call("hot_tool", execution_time=0.1)

        # 少量调用
        for i in range(3):
            detector.record_tool_call("cold_tool", execution_time=0.1)

        hotspots = detector.detect_hotspots()

        assert len(hotspots) >= 1
        assert "hot_tool" in [h.name for h in hotspots]
        assert "cold_tool" not in [h.name for h in hotspots]

    def test_back_edge_detection(self) -> None:
        """回边检测 (循环)"""
        detector = HotspotDetector(
            compile_threshold=100,
            back_edge_threshold=5,
        )

        # 模拟循环调用
        for i in range(3):
            detector.record_tool_call("loop_tool", execution_time=0.1, is_repeated=True)

        hotspots = detector.detect_hotspots()
        # 应检测到OSR热点
        for h in hotspots:
            if h.name == "loop_tool":
                assert h.suggested_strategy in ("inline", "osr")

    def test_get_stats(self) -> None:
        """获取统计"""
        detector = HotspotDetector()

        for i in range(5):
            detector.record_tool_call("tool1")
            detector.record_knowledge_reference("knowledge1")

        stats = detector.get_stats()
        assert stats["total_calls"] == 10
        assert stats["tool_counters"] == 1
        assert stats["knowledge_counters"] == 1


class TestAutoAssembler:
    """测试自动装配器"""

    def test_create_inline_template(self) -> None:
        """创建内联模板"""
        from py_ha.memory.hotspot import HotspotInfo, CallCounter

        assembler = AutoAssembler(max_inline_size=1000)

        counter = CallCounter(name="test_knowledge", call_count=150)
        hotspot = HotspotInfo(
            name="test_knowledge",
            hotness_score=100.0,
            call_count=150,
            threshold_reached=True,
            suggested_strategy="inline",
        )

        knowledge_base = {"test_knowledge": "This is important knowledge content"}

        template = assembler.assemble(hotspot, knowledge_base)

        assert template is not None
        assert template.strategy == "inline"
        assert len(template.inlined_knowledge) > 0

    def test_escape_analysis(self) -> None:
        """逃逸分析"""
        assembler = AutoAssembler()

        # 无依赖 -> 不逃逸
        result = assembler.perform_escape_analysis("local_context", dependencies=[])
        assert result.escape_level == "no_escape"
        assert result.can_inline is True

        # 多依赖 -> 全局逃逸
        result = assembler.perform_escape_analysis("global_context", dependencies=["dep1", "dep2", "dep3", "dep4"])
        assert result.escape_level == "global_escape"
        assert result.can_inline is False

    def test_cache_management(self) -> None:
        """缓存管理"""
        from py_ha.memory.hotspot import HotspotInfo, CallCounter

        assembler = AutoAssembler(cache_size=5)

        # 创建多个模板
        for i in range(7):
            hotspot = HotspotInfo(
                name=f"hotspot_{i}",
                hotness_score=100.0,
                call_count=150,
                threshold_reached=True,
                suggested_strategy="inline",
            )
            assembler.assemble(hotspot)

        # 缓存应该被限制
        assert len(assembler._template_cache) <= assembler.cache_size

    def test_dead_content_elimination(self) -> None:
        """死代码消除"""
        from py_ha.memory.hotspot import HotspotInfo

        assembler = AutoAssembler()

        # 创建一些模板
        for i in range(5):
            hotspot = HotspotInfo(
                name=f"hotspot_{i}",
                threshold_reached=True,
                suggested_strategy="cache",
            )
            assembler.assemble(hotspot)

        # 设置低使用次数 (模板名称会添加 _cached 后缀)
        for name, template in assembler._template_cache.items():
            template.usage_count = 1 if "hotspot_0" in name else 10

        eliminated = assembler.eliminate_dead_content(threshold=5)
        # 检查是否有包含 hotspot_0 的模板被清除
        assert any("hotspot_0" in name for name in eliminated)


class TestMemoryManager:
    """测试记忆管理器"""

    def test_create_manager(self) -> None:
        """创建管理器"""
        manager = MemoryManager(
            eden_size=100,
            old_size=200,
            compile_threshold=50,
        )
        assert manager.heap.eden.max_size == 100
        assert manager.hotspot_detector.compile_threshold == 50

    def test_allocate_memory(self) -> None:
        """分配记忆"""
        manager = MemoryManager()

        entry = manager.allocate_memory("test content", importance=50)
        assert entry is not None
        assert entry.region == MemoryRegion.EDEN

    def test_store_conversation(self) -> None:
        """存储对话"""
        manager = MemoryManager()

        entry = manager.store_conversation("Hello", role="user", importance=60)
        assert entry is not None
        assert entry.metadata["role"] == "user"

    def test_invoke_gc(self) -> None:
        """触发GC"""
        manager = MemoryManager(eden_size=5)

        # 填充Eden
        for i in range(6):
            manager.allocate_memory(f"content {i}", importance=30)

        # 触发Minor GC
        result = manager.invoke_gc_minor()
        assert result.gc_type == "minor"

    def test_hotspot_workflow(self) -> None:
        """热点检测与装配流程"""
        manager = MemoryManager(compile_threshold=5)

        # 记录工具使用
        for i in range(10):
            manager.record_tool_usage("frequent_tool", execution_time=0.1)

        # 检测热点
        hotspots = manager.detect_hotspots()
        assert len(hotspots) > 0
        assert "frequent_tool" in [h.name for h in hotspots]

        # 自动装配
        templates = manager.auto_assemble()
        assert len(templates) > 0

    def test_execution_stack(self) -> None:
        """执行栈"""
        manager = MemoryManager()

        # 压入任务
        frame = manager.push_task("task1")
        assert frame is not None
        assert manager.stack.depth() == 1

        # 设置局部变量
        frame.set_local("key", "value")
        assert frame.get_local("key") == "value"

        # 弹出任务
        manager.pop_task()
        assert manager.stack.depth() == 0

    def test_progress_counter(self) -> None:
        """进度计数器"""
        manager = MemoryManager()

        manager.set_task_progress("test_task", total_steps=10)

        for i in range(5):
            manager.advance_progress()

        assert manager.get_progress() == 50.0

    def test_meta_space(self) -> None:
        """元空间"""
        manager = MemoryManager()

        # 定义知识
        manager.define_knowledge("key_fact", "Important fact")
        manager.store_important_knowledge("permanent_fact", "Never forget this")

        # 获取知识
        knowledge = manager.get_knowledge("key_fact")
        assert knowledge == "Important fact"

        # 检查Permanent存储
        perm_entry = manager.heap.permanent.get_knowledge("permanent_fact")
        assert perm_entry is not None
        assert perm_entry.importance == 100

    def test_health_report(self) -> None:
        """健康报告"""
        manager = MemoryManager(eden_size=10, old_size=20)

        # 初始健康
        health = manager.get_health_report()
        assert health["status"] == "healthy"

        # 填充内存
        for i in range(9):
            manager.allocate_memory(f"content {i}", importance=30)

        health = manager.get_health_report()
        # Eden接近满
        assert health["eden_pressure"] > 0.8

    def test_auto_optimize(self) -> None:
        """自动优化"""
        manager = MemoryManager(eden_size=5, compile_threshold=5)

        # 填充内存
        for i in range(6):
            manager.allocate_memory(f"content {i}", importance=30)

        # 记录热点
        for i in range(10):
            manager.record_tool_usage("hot_tool", execution_time=0.1)

        # 自动优化
        actions = manager.optimize_if_needed()
        assert "gc" in actions or "assembled" in actions

    def test_memory_status(self) -> None:
        """记忆状态"""
        manager = MemoryManager()

        status = manager.get_memory_status()

        assert "heap" in status
        assert "stack" in status
        assert "progress" in status
        assert "meta_space" in status
        assert "gc" in status
        assert "hotspot" in status
        assert "assembler" in status


class TestPermanentMemory:
    """测试永久代"""

    def test_store_knowledge(self) -> None:
        """存储核心知识"""
        permanent = PermanentMemory()

        entry = permanent.store_knowledge("system_prompt", "You are an AI assistant")
        assert entry.importance == 100
        assert entry.region == MemoryRegion.PERMANENT

    def test_knowledge_never_gc(self) -> None:
        """知识不被GC"""
        permanent = PermanentMemory()
        gc = GarbageCollector()

        permanent.store_knowledge("important", "Never forget")

        # 尝试GC
        result = gc.mark_sweep_collector.collect(None, permanent)

        # Permanent不应该被清除
        assert permanent.get_knowledge("important") is not None