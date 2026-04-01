"""
MCP Server Test - 验证 MCP Server 功能

测试新的 Harness Engineering 工具
"""

import json
from py_ha.mcp.server import create_mcp_server


def test_tool_definitions():
    """测试工具定义"""
    server = create_mcp_server()
    tools = server.get_tools()

    print(f"已定义 {len(tools)} 个 MCP Tools:")
    print("-" * 50)

    for tool in tools:
        print(f"  - {tool['name']}: {tool['description'][:40]}...")


def test_team_management():
    """测试团队管理工具"""
    server = create_mcp_server()

    print("\n" + "=" * 50)
    print("测试团队管理")
    print("=" * 50)

    # 列出团队
    result = server.handle_tool_call("team_list", {})
    print(f"\n[team_list] 团队规模: {result['result']['team_size']}")

    # 添加角色
    result = server.handle_tool_call("team_add_role", {
        "role_type": "developer",
        "name": "新开发人员",
    })
    print(f"[team_add_role] 创建: {result['result']}")


def test_workflow():
    """测试工作流工具"""
    server = create_mcp_server()

    print("\n" + "=" * 50)
    print("测试工作流")
    print("=" * 50)

    # 列出工作流
    result = server.handle_tool_call("workflow_list", {})
    print(f"\n[workflow_list] 可用工作流: {[w['id'] for w in result['result']['workflows']]}")

    # 启动工作流
    result = server.handle_tool_call("workflow_start", {
        "workflow_type": "feature",
        "initial_request": "实现用户登录功能",
    })
    print(f"[workflow_start] 状态: {result['result']['status']}")


def test_quick_operations():
    """测试快速操作"""
    server = create_mcp_server()

    print("\n" + "=" * 50)
    print("测试快速操作")
    print("=" * 50)

    # 快速功能开发
    result = server.handle_tool_call("quick_feature", {
        "feature_request": "实现用户注册功能",
    })
    print(f"\n[quick_feature] 状态: {result['result']['status']}")

    # 快速Bug修复
    result = server.handle_tool_call("quick_bugfix", {
        "bug_description": "登录页面无法提交表单",
    })
    print(f"[quick_bugfix] 状态: {result['result']['status']}")


def test_system_status():
    """测试系统状态"""
    server = create_mcp_server()

    print("\n" + "=" * 50)
    print("测试系统状态")
    print("=" * 50)

    result = server.handle_tool_call("system_status", {})
    print(f"\n[system_status]")
    print(f"  版本: {result['result']['version']}")
    print(f"  团队规模: {result['result']['team']['size']}")


def test_mcp_protocol():
    """测试 MCP 协议"""
    server = create_mcp_server()

    print("\n" + "=" * 50)
    print("测试 MCP 协议")
    print("=" * 50)

    # 测试 initialize
    request = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    response = server._handle_mcp_request(request)
    print(f"\n[initialize] Server: {response['result']['serverInfo']['name']}")

    # 测试 tools/list
    request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    response = server._handle_mcp_request(request)
    print(f"[tools/list] 工具数: {len(response['result']['tools'])}")

    # 测试 tools/call
    request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "team_list",
            "arguments": {},
        },
    }
    response = server._handle_mcp_request(request)
    print(f"[tools/call] 调用成功")


def main():
    print("=" * 50)
    print("py_ha MCP Server 测试")
    print("=" * 50)

    test_tool_definitions()
    test_team_management()
    test_workflow()
    test_quick_operations()
    test_system_status()
    test_mcp_protocol()

    print("\n" + "=" * 50)
    print("所有测试完成!")
    print("=" * 50)


if __name__ == "__main__":
    main()