"""测试可能的 API 端点"""
import requests
import json

def test_api_endpoints():
    base_url = "https://skillsmp.com"

    # 可能的 API 端点
    endpoints = [
        "/api/skills",
        "/api/skills/list",
        "/api/skills/search",
        "/api/v1/skills",
        "/zh/api/skills",
        "/zh/api/skills/list",
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://skillsmp.com/zh',
        'Origin': 'https://skillsmp.com',
    }

    print("=== 测试 API 端点 ===\n")

    for endpoint in endpoints:
        url = base_url + endpoint
        print(f"尝试: {url}")

        try:
            # GET 请求
            response = requests.get(url, headers=headers, timeout=10)
            print(f"  状态码: {response.status_code}")

            if response.status_code == 200:
                print(f"  [OK] 成功! 内容类型: {response.headers.get('content-type')}")

                # 尝试解析 JSON
                try:
                    data = response.json()
                    print(f"  JSON 键: {list(data.keys()) if isinstance(data, dict) else type(data)}")

                    # 保存响应
                    filename = endpoint.replace('/', '_') + '.json'
                    with open(f'D:/niro/claude-skills-miniapp/backend/scripts/{filename}', 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    print(f"  已保存到: {filename}")
                except:
                    print(f"  响应不是 JSON，前 200 字符: {response.text[:200]}")

            elif response.status_code == 404:
                print(f"  [404] 未找到")
            elif response.status_code == 403:
                print(f"  [403] 禁止访问 - 可能需要认证或特殊头")
            else:
                print(f"  [WARN] 状态码 {response.status_code}")

        except requests.exceptions.Timeout:
            print(f"  [TIMEOUT] 超时")
        except Exception as e:
            print(f"  [ERROR] 错误: {e}")

        print()

    # 测试搜索参数
    print("=== 测试带参数的请求 ===\n")

    search_endpoints = [
        "/api/skills?limit=100",
        "/api/skills?page=1&pageSize=100",
        "/zh/api/skills?limit=100",
    ]

    for endpoint in search_endpoints:
        url = base_url + endpoint
        print(f"尝试: {url}")

        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"  状态码: {response.status_code}")

            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"  [OK] 成功! 返回数据")
                    if isinstance(data, dict):
                        print(f"     键: {list(data.keys())}")
                        if 'items' in data:
                            print(f"     items 数量: {len(data['items'])}")
                        if 'total' in data:
                            print(f"     total: {data['total']}")
                except:
                    pass
        except Exception as e:
            print(f"  [ERROR] 错误: {e}")

        print()

    # 检查 robots.txt 和 sitemap
    print("=== 检查 robots.txt 和 sitemap ===\n")

    for path in ['/robots.txt', '/sitemap.xml', '/sitemap-0.xml']:
        url = base_url + path
        print(f"检查: {url}")
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                print(f"  [OK] 存在")
                content = response.text[:500]
                print(f"  内容预览:\n{content}\n")

                # 保存
                filename = path.replace('/', '_')
                with open(f'D:/niro/claude-skills-miniapp/backend/scripts/{filename}', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print(f"  已保存到: {filename}")
            else:
                print(f"  [ERROR] 不存在 ({response.status_code})")
        except Exception as e:
            print(f"  [ERROR] 错误: {e}")
        print()

if __name__ == "__main__":
    test_api_endpoints()
