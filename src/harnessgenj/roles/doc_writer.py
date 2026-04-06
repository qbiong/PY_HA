"""
Doc Writer Role - 文档管理员角色（文档化者）

职责:
- 技术文档编写（产出技术文档）
- API文档维护
- 用户手册编写
- 文档版本管理

技能:
- write_doc: 编写文档
- update_doc: 更新文档
- generate_api_doc: 生成API文档
- create_user_guide: 创建用户指南

哲学定位（基于业界最佳实践）:
- 文档化者 - 记录一切，不创造任何
- 核心原则：你记录"已有的"，不创造"新的"
- 工具边界：只能编辑文档，不能编辑代码

边界定义:
- 决策权限：文档结构、文档格式、文档发布时间
- 禁止行为：写代码、修改需求、修改架构、创造新技术方案
"""

from typing import Any
from harnessgenj.roles.base import (
    AgentRole,
    RoleType,
    RoleSkill,
    RoleContext,
    SkillCategory,
    TaskType,
)


class DocWriter(AgentRole):
    """
    文档管理员 - 文档化者角色

    Harness角色定义:
    - 职责边界: 文档编写、维护、版本管理
    - 技能集: 技术写作、API文档、用户指南
    - 协作: 收集各角色产出，整理成文档

    业界最佳实践增强:
    - 工具权限: read, search, edit_doc（只能编辑文档）
    - 决策权限: 文档结构、文档格式、文档发布时间
    - 禁止行为: 写代码、修改需求、修改架构、创造新技术方案
    """

    # ==================== 核心职责定义（哲学层面） ====================

    CORE_RESPONSIBILITIES = """
你的职责是**记录**，不是**创造**。

文档内容：
- 技术文档编写
- API文档维护
- 用户手册编写
- 文档版本管理

禁止内容：
- ❌ 不要写代码 - 这是开发者的职责
- ❌ 不要修改需求 - 这是产品经理的职责
- ❌ 不要修改架构 - 这是架构师的职责
- ❌ 不要创造新的技术方案 - 回调架构师

输出产物：
- 技术文档
- API文档
- 用户手册
- 更新日志
"""

    BOUNDARY_CHECK_PROMPT = """
在编写文档时：
- 记录"已有的内容"，不创造"新的内容"
- 整理"他人的产出"，不生成"自己的产出"
- 维护"文档版本"，不修改"文档内容来源"
"""

    SELF_REFLECTION_PROMPT = """
完成文档后，检查：
- [ ] 文档是否准确反映了实际代码/功能？
- [ ] 是否与需求文档一致？
- [ ] 是否与架构文档一致？
- [ ] 用户能否理解这份文档？
"""

    @property
    def role_type(self) -> RoleType:
        return RoleType.DOC_WRITER

    @property
    def responsibilities(self) -> list[str]:
        return [
            "技术文档编写（产出技术文档）",
            "API文档维护（产出API文档）",
            "用户手册编写（产出用户手册）",
            "文档版本管理（产出版本记录）",
            "更新日志编写（产出CHANGELOG）",
        ]

    @property
    def forbidden_actions(self) -> list[str]:
        """禁止行为 - 文档化者只记录，不创造"""
        return [
            "写代码",
            "修改需求",
            "修改架构",
            "创造新技术方案",
        ]

    @property
    def decision_authority(self) -> list[str]:
        """决策权限 - 文档管理员有权决定文档形式"""
        return [
            "文档结构",
            "文档格式",
            "文档发布时间",
        ]

    @property
    def no_decision_authority(self) -> list[str]:
        """无决策权限 - 内容决策应回调对应角色"""
        return [
            "技术方案",
            "需求范围",
            "代码实现",
        ]

    def build_role_prompt(self) -> str:
        """构建完整的角色提示词"""
        return f"""
你是项目的文档管理员。

{self.CORE_RESPONSIBILITIES}

{self.BOUNDARY_CHECK_PROMPT}

{self.SELF_REFLECTION_PROMPT}

记住：你的职责是记录"已有的"，不创造"新的"。
"""

    def _setup_skills(self) -> None:
        """设置文档技能"""
        skills = [
            RoleSkill(
                name="write_doc",
                description="编写文档",
                category=SkillCategory.DOCUMENTATION,
                inputs=["content", "template"],
                outputs=["document"],
            ),
            RoleSkill(
                name="update_doc",
                description="更新文档",
                category=SkillCategory.DOCUMENTATION,
                inputs=["document", "changes"],
                outputs=["updated_document"],
            ),
            RoleSkill(
                name="generate_api_doc",
                description="生成API文档",
                category=SkillCategory.DOCUMENTATION,
                inputs=["code", "annotations"],
                outputs=["api_documentation"],
            ),
            RoleSkill(
                name="create_user_guide",
                description="创建用户指南",
                category=SkillCategory.DOCUMENTATION,
                inputs=["features", "workflows"],
                outputs=["user_guide"],
            ),
        ]

        for skill in skills:
            self.add_skill(skill)

    def get_supported_task_types(self) -> list[TaskType]:
        return [
            TaskType.WRITE_DOC,
            TaskType.UPDATE_DOC,
        ]

    def _execute_by_type(self, task_type: TaskType) -> dict[str, Any]:
        handlers = {
            TaskType.WRITE_DOC: self._write_doc,
            TaskType.UPDATE_DOC: self._update_doc,
        }

        handler = handlers.get(task_type)
        if handler:
            return handler()
        return {"status": "error", "message": f"Unsupported task: {task_type}"}

    def _write_doc(self) -> dict[str, Any]:
        """编写文档"""
        content = self._current_task.get("inputs", {}).get("content", "")

        result = {
            "status": "completed",
            "outputs": {
                "document": {
                    "title": "技术文档",
                    "sections": ["概述", "使用说明", "API参考", "FAQ"],
                    "content": f"# 文档内容\n\n{content}",
                    "format": "markdown",
                },
            },
        }

        self.context.add_artifact("document", result["outputs"]["document"])
        return result

    def _update_doc(self) -> dict[str, Any]:
        """更新文档"""
        changes = self._current_task.get("inputs", {}).get("changes", "")

        result = {
            "status": "completed",
            "outputs": {
                "updated_document": {
                    "version": "1.1.0",
                    "changes": changes,
                    "updated_at": "2024-01-01",
                },
            },
        }

        return result


def create_doc_writer(
    writer_id: str,
    name: str = "DocWriter",
    context: RoleContext | None = None,
) -> DocWriter:
    """
    创建文档管理员实例

    Args:
        writer_id: 文档管理员ID
        name: 文档管理员名称
        context: 角色上下文

    Returns:
        文档管理员实例

    工具权限:
        - read: 读取文件
        - search: 搜索代码
        - edit_doc: 编辑文档（不能编辑代码）
    """
    return DocWriter(role_id=writer_id, name=name, context=context)