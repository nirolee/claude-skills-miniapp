#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 GitHub Token 配置"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ 找到 .env 文件: {env_path}")
else:
    print(f"❌ 未找到 .env 文件: {env_path}")

# 检查 Token
token = os.getenv('GITHUB_TOKEN', '')
if token:
    print(f"✅ GitHub Token 已配置")
    print(f"   Token 前缀: {token[:10]}...")
    print(f"   Token 长度: {len(token)} 字符")

    # 验证 Token 格式
    if token.startswith('ghp_') and len(token) == 40:
        print("✅ Token 格式正确（classic token）")
    elif token.startswith('github_pat_') and len(token) > 80:
        print("✅ Token 格式正确（fine-grained token）")
    else:
        print("⚠️ Token 格式可能不正确")
        print(f"   预期格式: ghp_xxxx (40字符) 或 github_pat_xxxx (>80字符)")
else:
    print("❌ 未配置 GitHub Token")
    print("   请在 .env 文件中添加: GITHUB_TOKEN=your_token")
