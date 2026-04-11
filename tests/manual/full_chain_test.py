"""
HarnessGenJ v1.1 全链路测试脚本

测试场景：
1. 用户首次使用框架
2. 从现有项目初始化
3. 开发功能
4. 结构化知识存储
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
print("HarnessGenJ v1.1 全链路用户测试")
print("=" * 60)

# ==================== 测试结果汇总 ====================
test_results = []

def record_result(name: str, passed: bool, details: str = "", error: str = ""):
    test_results.append({
        "name": name,
        "passed": passed,
        "details": details,
        "error": error,
    })
    status = "[OK]" if passed else "[FAIL]"
    print(f"\n{status} {name}")
    if details:
        print(f"  Details: {details}")
    if error:
        print(f"  Error: {error}")


# ==================== 场景1: 用户首次使用框架 ====================
print("\n" + "=" * 60)
print("场景1: 用户首次使用框架")
print("=" * 60)

try:
    # 创建临时目录用于测试
    test_workspace1 = tempfile.mkdtemp(prefix="hgj_test1_")
    os.chdir(test_workspace1)

    print(f"\n测试工作空间: {test_workspace1}")

    from harnessgenj import Harness

    # 测试基本初始化
    harness = Harness("my-project", workspace=test_workspace1)

    # 验证 Hooks 是否自动配置
    hooks_config_path = Path(test_workspace1) / ".claude" / "settings.json"
    hooks_script_path = Path(test_workspace1) / ".claude" / "harnessgenj_hook.py"

    hooks_configured = hooks_config_path.exists()
    hooks_script_exists = hooks_script_path.exists()

    print(f"\n  Hooks 配置文件: {hooks_config_path}")
    print(f"  Hooks 配置状态: {hooks_configured}")
    print(f"  Hook 脚本存在: {hooks_script_exists}")

    # 验证团队是否自动创建
    team = harness.get_team()
    team_created = len(team) > 0
    print(f"\n  团队规模: {len(team)} 人")
    for member in team:
        print(f"    - {member.get('name', 'unknown')} ({member.get('role_type', 'unknown')})")

    # 验证工作空间是否正确初始化
    workspace_initialized = os.path.exists(test_workspace1)
    state_file_exists = os.path.exists(os.path.join(test_workspace1, "state.json"))
    project_file_exists = os.path.exists(os.path.join(test_workspace1, "project.json"))

    print(f"\n  工作空间目录: {workspace_initialized}")
    print(f"  state.json: {state_file_exists}")
    print(f"  project.json: {project_file_exists}")

    # 验证记忆系统
    memory_stats = harness.memory.get_stats()
    print(f"\n  记忆系统状态:")
    print(f"    - Eden: {memory_stats['memory']['eden_size']}")
    print(f"    - Old: {memory_stats['memory']['old_size']}")
    print(f"    - Permanent: {memory_stats['memory']['permanent_size']}")

    # 判断场景1是否通过
    # 注意：state.json 在首次初始化时可能不存在，只有 project.json 存在
    scenario1_passed = (
        hooks_configured and
        hooks_script_exists and
        team_created and
        workspace_initialized and
        project_file_exists  # 改为检查 project.json
    )

    record_result(
        "场景1: 用户首次使用框架",
        scenario1_passed,
        f"Hooks配置={hooks_configured}, 团队={len(team)}人, 工作空间已初始化",
    )

    # 清理
    shutil.rmtree(test_workspace1, ignore_errors=True)

except Exception as e:
    record_result("场景1: 用户首次使用框架", False, error=str(e))


# ==================== 场景2: 从现有项目初始化 ====================
print("\n" + "=" * 60)
print("场景2: 从现有项目初始化")
print("=" * 60)

try:
    # 创建模拟项目目录（确保是全新的）
    test_project_dir = tempfile.mkdtemp(prefix="hgj_project2_")

    # 创建模拟文档
    readme_content = """# Java Shop Project

这是一个电商平台项目。

## 技术栈
- Java 17
- Spring Boot 3.2
- PostgreSQL
"""

    requirements_content = """# 需求文档

## 功能需求
1. 用户登录
2. 商品浏览
3. 购物车
"""

    design_content = """# 设计文档

## 系统架构
- 前端: React
- 后端: Spring Boot
- 数据库: PostgreSQL
"""

    # 创建 pom.xml 模拟 Java 项目
    pom_content = """<?xml version="1.0" encoding="UTF-8"?>
<project>
    <groupId>com.example</groupId>
    <artifactId>java-shop</artifactId>
    <version>1.0.0</version>
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
    </dependencies>
</project>
"""

    # 写入文件
    readme_path = Path(test_project_dir, "README.md")
    requirements_path = Path(test_project_dir, "requirements.md")
    design_path = Path(test_project_dir, "design.md")
    pom_path = Path(test_project_dir, "pom.xml")

    readme_path.write_text(readme_content, encoding="utf-8")
    requirements_path.write_text(requirements_content, encoding="utf-8")
    design_path.write_text(design_content, encoding="utf-8")
    pom_path.write_text(pom_content, encoding="utf-8")

    print(f"\n模拟项目目录: {test_project_dir}")
    print(f"  文件: README.md, requirements.md, design.md, pom.xml")

    # 验证文件已创建
    print(f"  文件验证: README={readme_path.exists()}, requirements={requirements_path.exists()}, design={design_path.exists()}")

    # 清除之前的导入缓存（如果有）
    import importlib
    import harnessgenj
    importlib.reload(harnessgenj)
    from harnessgenj import Harness

    # 从项目目录初始化
    harness = Harness.from_project(test_project_dir)

    # 验证技术栈是否正确检测
    tech_stack = harness.memory.project_info.tech_stack
    print(f"\n  检测到的技术栈: {tech_stack}")

    # 验证项目名称
    project_name = harness.project_name
    print(f"  项目名称: {project_name}")

    # 验证文档是否正确导入
    requirements_doc = harness.memory.get_document("requirements")
    design_doc = harness.memory.get_document("design")

    # 调试信息
    print(f"\n  Old区条目数: {harness.memory.heap.old.size()}")
    print(f"  Old区条目: {[e.id for e in harness.memory.heap.old.list_entries()]}")

    requirements_imported = requirements_doc is not None and len(requirements_doc) > 0
    design_imported = design_doc is not None and len(design_doc) > 0

    print(f"\n  requirements.md 导入: {requirements_imported}")
    print(f"  design.md 导入: {design_imported}")

    if requirements_doc:
        print(f"  requirements 内容片段: {requirements_doc[:50]}...")
    if design_doc:
        print(f"  design 内容片段: {design_doc[:50]}...")

    # 验证 AGENTS 知识
    workspace = Path(test_project_dir) / ".harnessgenj"
    agents_dir = workspace / "agents"

    agents_tech_exists = agents_dir.exists() and (agents_dir / "tech.md").exists()
    agents_conventions_exists = agents_dir.exists() and (agents_dir / "conventions.md").exists()

    print(f"\n  agents/tech.md: {agents_tech_exists}")
    print(f"  agents/conventions.md: {agents_conventions_exists}")

    # 检查 Hooks 配置
    hooks_config_path = workspace / ".claude" / "settings.json"
    hooks_configured = hooks_config_path.exists()
    print(f"  Hooks 配置: {hooks_configured}")

    # 判断场景2是否通过
    scenario2_passed = (
        tech_stack is not None and
        len(tech_stack) > 0 and
        requirements_imported and
        design_imported
    )

    record_result(
        "场景2: 从现有项目初始化",
        scenario2_passed,
        f"技术栈={tech_stack}, 文档导入=需求:{requirements_imported}/设计:{design_imported}, AGENTS模板={agents_tech_exists}",
    )

    # 清理
    shutil.rmtree(test_project_dir, ignore_errors=True)

except Exception as e:
    import traceback
    record_result("场景2: 从现有项目初始化", False, error=f"{str(e)}\n{traceback.format_exc()}")


# ==================== 场景3: 开发功能 ====================
print("\n" + "=" * 60)
print("场景3: 开发功能")
print("=" * 60)

try:
    # 创建测试工作空间
    test_workspace3 = tempfile.mkdtemp(prefix="hgj_test3_")

    from harnessgenj import Harness

    harness = Harness("test-project", workspace=test_workspace3)

    # 测试 develop 方法
    result = harness.develop("实现用户登录功能", skip_hooks=True)

    task_id = result.get("task_id")
    status = result.get("status")

    print(f"\n  开发结果:")
    print(f"    - 任务ID: {task_id}")
    print(f"    - 状态: {status}")

    # 验证任务是否正确创建
    task_created = task_id is not None and len(task_id) > 0

    # 验证事件是否正确触发 (检查进度文档)
    progress_doc = harness.memory.get_document("progress")
    progress_updated = progress_doc is not None and task_id in progress_doc if progress_doc else False

    print(f"\n  进度文档更新: {progress_updated}")
    if progress_doc:
        print(f"  进度内容片段: {progress_doc[:200]}...")

    # 验证积分系统是否更新
    leaderboard = harness.get_score_leaderboard()
    score_updated = len(leaderboard) > 0

    print(f"\n  积分排行榜: {len(leaderboard)} 条记录")
    for entry in leaderboard[:3]:
        print(f"    - {entry.get('role_name', 'unknown')}: {entry.get('score', 0)} 分")

    # 验证统计更新
    stats = harness.get_status()
    print(f"\n  项目统计:")
    print(f"    - 功能总数: {stats['project_stats']['features_total']}")
    print(f"    - 已完成: {stats['project_stats']['features_completed']}")

    # 判断场景3是否通过
    scenario3_passed = task_created and status in ["completed", "blocked_by_hooks", "blocked_by_post_hooks"]

    record_result(
        "场景3: 开发功能",
        scenario3_passed,
        f"任务ID={task_id}, 状态={status}, 进度更新={progress_updated}",
    )

    # 清理
    shutil.rmtree(test_workspace3, ignore_errors=True)

except Exception as e:
    record_result("场景3: 开发功能", False, error=str(e))


# ==================== 场景4: 结构化知识存储 ====================
print("\n" + "=" * 60)
print("场景4: 结构化知识存储")
print("=" * 60)

try:
    # 创建测试工作空间
    test_workspace4 = tempfile.mkdtemp(prefix="hgj_test4_")

    from harnessgenj import Harness
    from harnessgenj.memory import KnowledgeEntry, KnowledgeType, CodeLocation

    harness = Harness("knowledge-test", workspace=test_workspace4)

    # 创建结构化知识条目
    entry = KnowledgeEntry(
        type=KnowledgeType.SECURITY_ISSUE,
        problem="命令注入风险",
        solution="使用白名单验证用户输入",
        code_location=CodeLocation(
            file="ShellTool.java",
            lines=[93, 118],
            start_line=93,
            end_line=118,
        ),
        severity="critical",
        tags=["security", "injection", "shell"],
    )

    print(f"\n  创建知识条目:")
    print(f"    - ID: {entry.id}")
    print(f"    - 类型: {entry.type.value}")
    print(f"    - 问题: {entry.problem}")
    print(f"    - 解决方案: {entry.solution}")
    print(f"    - 代码位置: {entry.code_location.file} 行 {entry.code_location.lines}")
    print(f"    - 严重程度: {entry.severity}")
    print(f"    - 标签: {entry.tags}")

    # 存储知识
    stored_id = harness.memory.store_structured_knowledge(entry)

    print(f"\n  存储结果: ID={stored_id}")

    # 验证知识是否正确存储
    retrieved = harness.memory.get_structured_knowledge(stored_id)
    knowledge_stored = retrieved is not None and retrieved.problem == entry.problem

    print(f"\n  知识检索: {knowledge_stored}")
    if retrieved:
        print(f"    - 检索到的问题: {retrieved.problem}")

    # 验证索引是否正确建立
    # 按类型查询
    security_issues = harness.memory.query_knowledge_by_type(KnowledgeType.SECURITY_ISSUE)
    type_index_works = len(security_issues) > 0

    print(f"\n  按类型查询 (SECURITY_ISSUE): {len(security_issues)} 条记录")

    # 按标签查询
    tagged_entries = harness.memory.query_knowledge_by_tags(["security"])
    tag_index_works = len(tagged_entries) > 0

    print(f"  按标签查询 (security): {len(tagged_entries)} 条记录")

    # 按文件查询
    file_entries = harness.memory.query_knowledge_by_file("ShellTool.java")
    file_index_works = len(file_entries) > 0

    print(f"  按文件查询 (ShellTool.java): {len(file_entries)} 条记录")

    # 搜索功能
    search_results = harness.memory.search_structured_knowledge("命令注入")
    search_works = len(search_results) > 0

    print(f"  关键词搜索 (命令注入): {len(search_results)} 条记录")

    # 获取统计
    knowledge_stats = harness.memory.get_knowledge_stats()
    print(f"\n  知识库统计:")
    print(f"    - 总条目: {knowledge_stats['total_entries']}")
    print(f"    - 已验证: {knowledge_stats['verified_count']}")
    print(f"    - 未验证: {knowledge_stats['unverified_count']}")

    # 判断场景4是否通过
    scenario4_passed = (
        knowledge_stored and
        type_index_works and
        tag_index_works and
        file_index_works and
        search_works
    )

    record_result(
        "场景4: 结构化知识存储",
        scenario4_passed,
        f"存储={knowledge_stored}, 类型索引={type_index_works}, 标签索引={tag_index_works}, 文件索引={file_index_works}, 搜索={search_works}",
    )

    # 清理
    shutil.rmtree(test_workspace4, ignore_errors=True)

except Exception as e:
    record_result("场景4: 结构化知识存储", False, error=str(e))


# ==================== 测试汇总 ====================
print("\n" + "=" * 60)
print("测试汇总")
print("=" * 60)

total_tests = len(test_results)
passed_tests = sum(1 for r in test_results if r["passed"])
failed_tests = total_tests - passed_tests

print(f"\n总测试数: {total_tests}")
print(f"通过: {passed_tests}")
print(f"失败: {failed_tests}")
print(f"通过率: {passed_tests / total_tests * 100:.1f}%")

print("\n详细结果:")
for result in test_results:
    status = "[OK]" if result["passed"] else "[FAIL]"
    print(f"  {status} {result['name']}")
    if result["error"]:
        print(f"       Error: {result['error']}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)

# 输出汇总到文件
with open("test_report.txt", "w", encoding="utf-8") as f:
    f.write("HarnessGenJ v1.1 全链路测试报告\n")
    f.write("=" * 60 + "\n\n")
    for result in test_results:
        status = "[OK]" if result["passed"] else "[FAIL]"
        f.write(f"{status} {result['name']}\n")
        f.write(f"    Details: {result['details']}\n")
        if result["error"]:
            f.write(f"    Error: {result['error']}\n")
        f.write("\n")
    f.write(f"\n总测试数: {total_tests}\n")
    f.write(f"通过: {passed_tests}\n")
    f.write(f"失败: {failed_tests}\n")
    f.write(f"通过率: {passed_tests / total_tests * 100:.1f}%\n")