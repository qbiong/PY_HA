"""
诊断脚本 - 检测场景1和场景2的问题
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

print("=" * 60)
print("诊断脚本 - 场景2 文档导入问题")
print("=" * 60)

# 创建模拟项目目录
test_project_dir = tempfile.mkdtemp(prefix="hgj_diag_")

# 创建模拟文档
Path(test_project_dir, "README.md").write_text("# Test Project\nThis is a test.")
Path(test_project_dir, "requirements.md").write_text("# Requirements\n1. Feature A\n2. Feature B")
Path(test_project_dir, "design.md").write_text("# Design\nSystem architecture.")

print(f"\n项目目录: {test_project_dir}")
print(f"文件列表: {list(Path(test_project_dir).glob('*.md'))}")

from harnessgenj import Harness

# 从项目目录初始化
harness = Harness.from_project(test_project_dir)

# 检查工作空间
workspace = Path(test_project_dir) / ".harnessgenj"
print(f"\n工作空间: {workspace}")
print(f"工作空间内容: {list(workspace.glob('*')) if workspace.exists() else '不存在'}")

# 检查文档目录
doc_dir = workspace / "documents"
print(f"\n文档目录: {doc_dir}")
print(f"文档目录内容: {list(doc_dir.glob('*.md')) if doc_dir.exists() else '不存在'}")

# 检查 memory 中的文档
print(f"\n=== Memory 状态 ===")
print(f"Old 区条目数: {harness.memory.heap.old.size()}")
print(f"Old 区条目: {[e.id for e in harness.memory.heap.old.list_entries()]}")

# 尝试直接获取文档
requirements = harness.memory.get_document("requirements")
design = harness.memory.get_document("design")

print(f"\n=== 文档获取测试 ===")
print(f"requirements: {requirements[:50] if requirements else 'None'}...")
print(f"design: {design[:50] if design else 'None'}...")

# 检查 Old 区的原始数据
print(f"\n=== Old 区原始数据 ===")
for entry in harness.memory.heap.old.list_entries():
    print(f"  - ID: {entry.id}, Content: {entry.content[:50]}...")

# 检查文件系统中的文档
print(f"\n=== 文件系统检查 ===")
for doc_type in ["requirements", "design", "development", "testing", "progress"]:
    doc_path = doc_dir / f"{doc_type}.md"
    if doc_path.exists():
        content = doc_path.read_text()[:50]
        print(f"  {doc_type}.md: {content}...")
    else:
        print(f"  {doc_type}.md: 不存在")

# 清理
shutil.rmtree(test_project_dir, ignore_errors=True)

print("\n" + "=" * 60)
print("诊断完成")
print("=" * 60)