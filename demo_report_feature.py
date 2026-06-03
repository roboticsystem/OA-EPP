#!/usr/bin/env python3
"""
演示开发日志报告功能的测试脚本
"""
import requests
import sys
import json

API_BASE = "http://127.0.0.1:8010"

def print_title(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_separator():
    print("-" * 60)

def test_login():
    """测试登录"""
    print_title("1. 登录教师后台")
    try:
        r = requests.post(
            f"{API_BASE}/api/teacher/login",
            json={"password": "admin123"}
        )
        if r.ok:
            data = r.json()
            print("✅ 登录成功！")
            return data.get("token")
        else:
            print(f"❌ 登录失败: {r.status_code}")
            print(r.text)
            return None
    except Exception as e:
        print(f"❌ 登录错误: {e}")
        return None

def test_audit_logs(token):
    """测试审计日志"""
    print_title("2. 查询审计日志")
    try:
        r = requests.get(
            f"{API_BASE}/api/teacher/report/logs",
            headers={"Authorization": f"Bearer {token}"}
        )
        if r.ok:
            data = r.json()
            print(f"✅ 查询成功！共 {data.get('total', 0)} 条记录")
            print(f"   当前页面: {data.get('page', 1)} / {max(1, (data.get('total', 0) + 19) // 20)}")
            if data.get("logs"):
                print("\n   最新记录:")
                for log in data.get("logs", [])[:3]:
                    print(f"    - [{log.get('created_at', '')}] {log.get('action', '')}")
        else:
            print(f"❌ 查询失败: {r.status_code}")
            print(r.text)
    except Exception as e:
        print(f"❌ 查询错误: {e}")

def test_get_classes(token):
    """测试获取班级列表"""
    print_title("3. 获取班级列表")
    try:
        r = requests.get(
            f"{API_BASE}/api/teacher/report/classes",
            headers={"Authorization": f"Bearer {token}"}
        )
        if r.ok:
            data = r.json()
            if data:
                print(f"✅ 获取成功！共 {len(data)} 个班级")
                for cls in data:
                    print(f"    - {cls}")
            else:
                print("ℹ️  暂无班级数据")
            return data
        else:
            print(f"❌ 获取失败: {r.status_code}")
            print(r.text)
            return []
    except Exception as e:
        print(f"❌ 获取错误: {e}")
        return []

def test_get_settings(token):
    """测试获取课程设置"""
    print_title("4. 获取课程设置")
    try:
        r = requests.get(
            f"{API_BASE}/api/teacher/report/settings",
            headers={"Authorization": f"Bearer {token}"}
        )
        if r.ok:
            settings = r.json()
            print("✅ 获取成功！")
            print(f"   课程名称: {settings.get('course_name', '')}")
            print(f"   学期: {settings.get('semester', '')}")
        else:
            print(f"❌ 获取失败: {r.status_code}")
            print(r.text)
    except Exception as e:
        print(f"❌ 获取错误: {e}")

def test_api_docs():
    """测试API文档"""
    print_title("5. API文档")
    print(f"✅ API文档地址: {API_BASE}/api/docs")
    print("   在浏览器中打开可查看所有新增API接口")
    print("\n   新增API路由:")
    print("    - /api/teacher/report/*")

def main():
    print("\n")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║            开发日志报告功能演示                            ║")
    print("║            Development Log Report Demo                    ║")
    print("╚═══════════════════════════════════════════════════════════╝")

    # 测试登录
    token = test_login()
    if not token:
        print("\n❌ 无法继续测试，请检查服务器是否正常运行")
        return

    # 测试其他功能
    print_separator()
    test_get_settings(token)

    print_separator()
    test_get_classes(token)

    print_separator()
    test_audit_logs(token)

    print_separator()
    test_api_docs()

    print("\n" + "=" * 60)
    print("✅ 演示完成！")
    print("=" * 60)
    print("\n📝 功能说明:")
    print("   1. 打开浏览器访问 http://127.0.0.1:8010/teacher")
    print("   2. 使用密码 admin123 登录")
    print("   3. 在页面中可以看到新增的4个功能模块：")
    print("      - 📊 开发日志报告")
    print("      - 📦 批量导出")
    print("      - 💬 教师评语管理")
    print("      - 📋 审计日志")

if __name__ == "__main__":
    main()
