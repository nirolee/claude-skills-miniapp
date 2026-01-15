# -*- coding: utf-8 -*-
"""
测试 API 端点
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """测试健康检查"""
    response = requests.get(f"{BASE_URL}/health")
    print(f"[OK] 健康检查: {response.json()}")

def test_list_skills():
    """测试技能列表"""
    response = requests.get(f"{BASE_URL}/api/skills?page=1&page_size=3")
    data = response.json()
    print(f"\n[OK] 技能列表 API:")
    print(f"  - 总数: {data['total']}")
    print(f"  - 当前页: {data['page']}")
    print(f"  - 每页数量: {data['page_size']}")
    print(f"  - 返回技能数: {len(data['items'])}")

    if data['items']:
        skill = data['items'][0]
        print(f"\n[INFO] 第一个技能:")
        print(f"  - ID: {skill['id']}")
        print(f"  - 名称: {skill['name']}")
        print(f"  - 作者: {skill['author']}")
        print(f"  - 分类: {skill['category']}")
        print(f"  - 描述: {skill['description'][:50]}...")

def test_get_skill_detail():
    """测试技能详情"""
    response = requests.get(f"{BASE_URL}/api/skills/1")
    if response.status_code == 200:
        skill = response.json()
        print(f"\n[OK] 技能详情 API (ID=1):")
        print(f"  - 名称: {skill['name']}")
        print(f"  - GitHub: {skill['github_url']}")
        print(f"  - 安装命令: {skill['install_command'][:50]}...")
        print(f"  - 浏览次数: {skill['view_count']}")
    else:
        print(f"\n[ERROR] 技能详情 API 失败: {response.status_code}")

def test_categories():
    """测试分类列表"""
    response = requests.get(f"{BASE_URL}/api/skills/categories/list")
    data = response.json()
    print(f"\n[OK] 分类列表:")
    for cat in data['categories'][:5]:
        print(f"  - {cat['value']}: {cat['label']}")

if __name__ == "__main__":
    try:
        print("[START] 开始测试 API...\n")
        test_health()
        test_list_skills()
        test_get_skill_detail()
        test_categories()
        print("\n\n[SUCCESS] 所有测试完成！")
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
