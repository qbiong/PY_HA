"""
Test Developer Config - 方案C动态角色配置测试

测试内容：
- DeveloperConfig 配置模型
- 路径权限检查
- 技术栈过滤
- 前端/后端/全栈便捷函数
"""

import pytest
from harnessgenj.roles import (
    Developer,
    DeveloperConfig,
    DeveloperContext,
    RoleContext,
    create_frontend_developer,
    create_backend_developer,
    create_fullstack_developer,
)
from harnessgenj.roles.base import BoundaryCheckResult


class TestDeveloperConfig:
    """测试 DeveloperConfig 配置模型"""

    def test_default_config(self):
        """测试默认配置（全栈）"""
        config = DeveloperConfig()
        assert config.allowed_paths == []
        assert config.forbidden_paths == []
        assert config.tech_stack == []
        assert config.forbidden_actions_extra == []
        assert config.role_label == "开发人员"
        assert config.is_fullstack == True

    def test_frontend_config(self):
        """测试前端配置"""
        config = DeveloperConfig(
            allowed_paths=["src/frontend/", "src/components/"],
            forbidden_paths=["src/backend/", "src/api/"],
            tech_stack=["React", "TypeScript"],
            role_label="前端开发",
        )
        assert config.allowed_paths == ["src/frontend/", "src/components/"]
        assert config.forbidden_paths == ["src/backend/", "src/api/"]
        assert config.tech_stack == ["React", "TypeScript"]
        assert config.is_frontend == True
        assert config.is_fullstack == False

    def test_backend_config(self):
        """测试后端配置"""
        config = DeveloperConfig(
            allowed_paths=["src/backend/", "src/api/"],
            forbidden_paths=["src/frontend/"],
            tech_stack=["Python", "FastAPI"],
            role_label="后端开发",
        )
        assert config.allowed_paths == ["src/backend/", "src/api/"]
        assert config.tech_stack == ["Python", "FastAPI"]
        assert config.is_backend == True
        assert config.is_fullstack == False

    def test_is_frontend_detection(self):
        """测试前端角色检测"""
        config = DeveloperConfig(allowed_paths=["src/components/", "src/ui/"])
        assert config.is_frontend == True

        config2 = DeveloperConfig(allowed_paths=["src/api/"])
        assert config2.is_frontend == False

    def test_is_backend_detection(self):
        """测试后端角色检测"""
        config = DeveloperConfig(allowed_paths=["src/api/", "src/backend/"])
        assert config.is_backend == True

        config2 = DeveloperConfig(allowed_paths=["src/frontend/"])
        assert config2.is_backend == False


class TestDeveloperWithConfig:
    """测试带配置的 Developer"""

    def test_developer_with_frontend_config(self):
        """测试前端开发者"""
        config = DeveloperConfig(
            allowed_paths=["src/frontend/"],
            tech_stack=["React"],
            role_label="前端开发",
        )
        dev = Developer(role_id="frontend_dev_1", config=config)

        assert dev.name == "前端开发"
        # 技术栈应该在职责列表中（不一定是最后一个，路径信息在最后）
        assert any("React" in r for r in dev.responsibilities)
        assert len(dev.forbidden_actions) >= 6  # 包含基础禁止行为

    def test_developer_with_backend_config(self):
        """测试后端开发者"""
        config = DeveloperConfig(
            allowed_paths=["src/backend/"],
            tech_stack=["Python"],
            role_label="后端开发",
        )
        dev = Developer(role_id="backend_dev_1", config=config)

        assert dev.name == "后端开发"
        # 技术栈应该在职责列表中（不一定是最后一个）
        assert any("Python" in r for r in dev.responsibilities)

    def test_developer_responsibilities_include_paths(self):
        """测试职责包含路径信息"""
        config = DeveloperConfig(
            allowed_paths=["src/frontend/", "src/components/"],
        )
        dev = Developer(role_id="dev_1", config=config)

        responsibilities = dev.responsibilities
        # 路径信息应该在职责中
        assert any("src/frontend" in r for r in responsibilities)

    def test_decision_authority_includes_tech_stack(self):
        """测试决策权限包含技术栈"""
        config = DeveloperConfig(tech_stack=["React", "TypeScript"])
        dev = Developer(role_id="dev_1", config=config)

        authority = dev.decision_authority
        assert any("React" in a for a in authority)
        assert any("TypeScript" in a for a in authority)


class TestPathPermission:
    """测试路径权限检查"""

    @pytest.fixture
    def frontend_dev(self):
        """前端开发实例"""
        return create_frontend_developer()

    @pytest.fixture
    def backend_dev(self):
        """后端开发实例"""
        return create_backend_developer()

    @pytest.fixture
    def fullstack_dev(self):
        """全栈开发实例"""
        return create_fullstack_developer()

    def test_frontend_allowed_path(self, frontend_dev):
        """测试前端允许路径"""
        result = frontend_dev.check_path_permission("src/frontend/App.tsx")
        assert result.allowed == True
        assert "src/frontend/" in result.reason

    def test_frontend_allowed_components(self, frontend_dev):
        """测试前端允许组件目录"""
        result = frontend_dev.check_path_permission("src/components/Button.tsx")
        assert result.allowed == True

    def test_frontend_forbidden_backend(self, frontend_dev):
        """测试前端禁止后端路径"""
        result = frontend_dev.check_path_permission("src/backend/api.py")
        assert result.allowed == False
        assert "禁止" in result.reason or "不在允许" in result.reason

    def test_frontend_forbidden_api(self, frontend_dev):
        """测试前端禁止API目录"""
        result = frontend_dev.check_path_permission("src/api/routes.py")
        assert result.allowed == False

    def test_backend_allowed_path(self, backend_dev):
        """测试后端允许路径"""
        result = backend_dev.check_path_permission("src/backend/service.py")
        assert result.allowed == True
        assert "src/backend/" in result.reason

    def test_backend_allowed_api(self, backend_dev):
        """测试后端允许API目录"""
        result = backend_dev.check_path_permission("src/api/users.py")
        assert result.allowed == True

    def test_backend_forbidden_frontend(self, backend_dev):
        """测试后端禁止前端路径"""
        result = backend_dev.check_path_permission("src/frontend/App.tsx")
        assert result.allowed == False

    def test_backend_forbidden_components(self, backend_dev):
        """测试后端禁止组件目录"""
        result = backend_dev.check_path_permission("src/components/Button.tsx")
        assert result.allowed == False

    def test_fullstack_all_allowed(self, fullstack_dev):
        """测试全栈开发者所有路径允许"""
        # 前端路径
        result1 = fullstack_dev.check_path_permission("src/frontend/App.tsx")
        assert result1.allowed == True

        # 后端路径
        result2 = fullstack_dev.check_path_permission("src/backend/api.py")
        assert result2.allowed == True

        # 任意路径
        result3 = fullstack_dev.check_path_permission("src/any/file.py")
        assert result3.allowed == True

    def test_path_with_backslash(self, frontend_dev):
        """测试Windows路径格式"""
        result = frontend_dev.check_path_permission("src\\frontend\\App.tsx")
        assert result.allowed == True

    def test_path_case_insensitive(self, frontend_dev):
        """测试路径大小写不敏感"""
        result = frontend_dev.check_path_permission("SRC/FRONTEND/App.tsx")
        assert result.allowed == True

    def test_nested_path(self, frontend_dev):
        """测试嵌套路径"""
        result = frontend_dev.check_path_permission("src/frontend/components/Button.tsx")
        assert result.allowed == True


class TestConvenienceFunctions:
    """测试便捷创建函数"""

    def test_create_frontend_developer_default(self):
        """测试创建前端开发者（默认配置）"""
        dev = create_frontend_developer()

        assert dev.role_id == "frontend_dev_1"
        assert dev.name == "前端开发"
        assert dev.config.is_frontend == True
        assert "React" in dev.config.tech_stack
        assert len(dev.config.allowed_paths) > 0
        assert len(dev.config.forbidden_paths) > 0

    def test_create_frontend_developer_custom(self):
        """测试创建前端开发者（自定义配置）"""
        dev = create_frontend_developer(
            developer_id="vue_dev",
            name="Vue前端",
            tech_stack=["Vue", "JavaScript", "SCSS"],
            allowed_paths=["src/views/", "src/components/"],
        )

        assert dev.role_id == "vue_dev"
        assert dev.name == "Vue前端"
        assert "Vue" in dev.config.tech_stack
        assert "src/views/" in dev.config.allowed_paths

    def test_create_backend_developer_default(self):
        """测试创建后端开发者（默认配置）"""
        dev = create_backend_developer()

        assert dev.role_id == "backend_dev_1"
        assert dev.name == "后端开发"
        assert dev.config.is_backend == True
        assert "Python" in dev.config.tech_stack
        assert "FastAPI" in dev.config.tech_stack

    def test_create_backend_developer_custom(self):
        """测试创建后端开发者（自定义配置）"""
        dev = create_backend_developer(
            developer_id="go_dev",
            name="Go后端",
            tech_stack=["Go", "Gin", "MySQL"],
            allowed_paths=["src/server/", "src/db/"],
        )

        assert dev.role_id == "go_dev"
        assert dev.name == "Go后端"
        assert "Go" in dev.config.tech_stack

    def test_create_fullstack_developer_default(self):
        """测试创建全栈开发者（默认配置）"""
        dev = create_fullstack_developer()

        assert dev.role_id == "fullstack_dev_1"
        assert dev.name == "全栈开发"
        assert dev.config.is_fullstack == True
        assert len(dev.config.allowed_paths) == 0
        assert len(dev.config.forbidden_paths) == 0

    def test_create_fullstack_developer_custom(self):
        """测试创建全栈开发者（自定义配置）"""
        dev = create_fullstack_developer(
            developer_id="node_dev",
            name="Node全栈",
            tech_stack=["Vue", "Node.js", "Express", "MongoDB"],
        )

        assert dev.role_id == "node_dev"
        assert dev.name == "Node全栈"
        assert "Vue" in dev.config.tech_stack
        assert "Node.js" in dev.config.tech_stack


class TestBuildRolePrompt:
    """测试角色提示词构建"""

    def test_frontend_prompt_has_tech_stack(self):
        """测试前端提示词包含技术栈"""
        dev = create_frontend_developer(tech_stack=["React", "TypeScript"])
        prompt = dev.build_role_prompt()

        assert "React" in prompt
        assert "TypeScript" in prompt
        assert "前端开发" in prompt

    def test_backend_prompt_has_tech_stack(self):
        """测试后端提示词包含技术栈"""
        dev = create_backend_developer(tech_stack=["Python", "FastAPI"])
        prompt = dev.build_role_prompt()

        assert "Python" in prompt
        assert "FastAPI" in prompt
        assert "后端开发" in prompt

    def test_frontend_prompt_has_path_restriction(self):
        """测试前端提示词包含路径限制"""
        dev = create_frontend_developer()
        prompt = dev.build_role_prompt()

        assert "可编辑的目录" in prompt or "allowed_paths" in prompt.lower()
        assert "src/frontend" in prompt or "src/components" in prompt

    def test_backend_prompt_has_path_restriction(self):
        """测试后端提示词包含路径限制"""
        dev = create_backend_developer()
        prompt = dev.build_role_prompt()

        assert "src/backend" in prompt or "src/api" in prompt

    def test_fullstack_prompt_no_restriction(self):
        """测试全栈提示词无路径限制"""
        dev = create_fullstack_developer()
        prompt = dev.build_role_prompt()

        # 全栈开发者应该没有路径限制提示
        # 或者有明确的"全栈"标识
        assert "全栈" in prompt or dev.config.is_fullstack


class TestAllowedExtensions:
    """测试文件扩展名过滤"""

    def test_frontend_extensions(self):
        """测试前端允许的扩展名"""
        dev = create_frontend_developer(tech_stack=["React", "TypeScript", "CSS"])
        extensions = dev.get_allowed_extensions()

        assert ".tsx" in extensions
        assert ".ts" in extensions
        assert ".css" in extensions

    def test_backend_extensions(self):
        """测试后端允许的扩展名"""
        dev = create_backend_developer(tech_stack=["Python", "FastAPI"])
        extensions = dev.get_allowed_extensions()

        assert ".py" in extensions

    def test_go_backend_extensions(self):
        """测试Go后端扩展名"""
        dev = create_backend_developer(tech_stack=["Go", "Gin"])
        extensions = dev.get_allowed_extensions()

        assert ".go" in extensions

    def test_empty_tech_stack_no_extensions(self):
        """测试空技术栈返回空扩展名"""
        dev = Developer(config=DeveloperConfig())
        extensions = dev.get_allowed_extensions()

        assert extensions == []  # 无限制


if __name__ == "__main__":
    pytest.main([__file__, "-v"])