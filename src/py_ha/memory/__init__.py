"""
Memory Module - JVM-style Memory Management for Agent Memory

严格实现 JVM 的三大核心机制:
1. 分代记忆管理 (类似 Heap 分代)
2. 记忆回收机制 (类似 GC 算法)
3. 热点自动装配 (类似 JIT 编译)
"""

from py_ha.memory.manager import MemoryManager
from py_ha.memory.heap import MemoryHeap, EdenMemory, SurvivorMemory, OldMemory, PermanentMemory
from py_ha.memory.gc import GarbageCollector, GCAlgorithm
from py_ha.memory.hotspot import HotspotDetector
from py_ha.memory.assembler import AutoAssembler

__all__ = [
    "MemoryManager",
    "MemoryHeap",
    "EdenMemory",
    "SurvivorMemory",
    "OldMemory",
    "PermanentMemory",
    "GarbageCollector",
    "GCAlgorithm",
    "HotspotDetector",
    "AutoAssembler",
]