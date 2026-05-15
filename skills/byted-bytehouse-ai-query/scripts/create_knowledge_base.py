#!/usr/bin/env python3
# Copyright (c) 2025 Beijing Volcano Engine Technology Co., Ltd. and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
ByteHouse 知识库创建脚本
用于创建ByteHouse知识库并返回知识库ID

配置方式：设置以下环境变量
- BYTEHOUSE_HOST: ByteHouse 主机地址 (如 tenant-xxx-cn-beijing-public.bytehouse.volces.com)
- BYTEHOUSE_PASSWORD: 密码 (用作 Bearer token)
"""

import os
import requests
import json
import sys
import argparse

# 从环境变量读取默认配置
BYTEHOUSE_HOST = os.environ.get('BYTEHOUSE_HOST', '')
BYTEHOUSE_PASSWORD = os.environ.get('BYTEHOUSE_PASSWORD', '')
KB_CONFIG_PATH = os.path.expanduser('~/.bytehouse_kb_config.json')
IDENTITY_PATH = '/root/.openclaw/workspace/IDENTITY.md'


def build_kb_api_url(host: str, endpoint: str) -> str:
    """构建知识库API URL"""
    if not host:
        print("Error: BYTEHOUSE_HOST environment variable is required", file=sys.stderr)
        sys.exit(1)
    
    # 处理 host - 可能是 host:port 格式
    if host.startswith('http'):
        base_url = host.rstrip('/')
    else:
        base_url = f"https://{host}"
    
    return f"{base_url}/matrix/v1/{endpoint.lstrip('/')}"


def create_knowledge_base(name: str, config: dict = None) -> int:
    """
    创建ByteHouse知识库
    
    Args:
        name: 知识库名称
        config: 可选的配置 dict，支持:
            - url: 自定义 API URL
            - api_key: 自定义 API Key
    
    Returns:
        创建成功的知识库ID
    """
    # 决定使用哪个配置：用户提供的 config > 环境变量
    if config:
        base_url = config.get('url', '')
        auth_token = config.get('api_key', '')
        
        if not base_url:
            print("Error: config.url is required when using custom config", file=sys.stderr)
            sys.exit(1)
        
        url = f"{base_url.rstrip('/')}/matrix/v1/knowledge-base"
    else:
        if not BYTEHOUSE_HOST:
            print("Error: Please set BYTEHOUSE_HOST environment variable or provide --config", file=sys.stderr)
            sys.exit(1)
        
        url = build_kb_api_url(BYTEHOUSE_HOST, 'knowledge-base')
        auth_token = BYTEHOUSE_PASSWORD if BYTEHOUSE_PASSWORD else ""
    
    headers = {
        "Content-Type": "application/json",
    }
    
    # 添加认证
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    if not name:
        name = get_claw_name()
        # kb_name加上时间戳
        import time
        name += f"_{int(time.time())}"
    
    # 构建请求 payload
    payload = {
        "name": name
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=15)
    print(response.text)
    response.raise_for_status()
    
    result = response.json()
    kb_id = result.get('id') or (result.get('data', {}).get('id') if isinstance(result.get('data'), dict) else None)

    if not kb_id:
        print(f"Error: Failed to get knowledge base ID from response: {result}", file=sys.stderr)
        sys.exit(1)
    
    # 保存知识库ID到配置文件
    save_kb_config(kb_id)
    
    return kb_id


def get_claw_name() -> str:
    """从IDENTITY.md获取当前Claw的名字"""
    default_name = "ByteHouse Text2SQL 知识库"
    
    if not os.path.exists(IDENTITY_PATH):
        return default_name
    
    try:
        with open(IDENTITY_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找Name字段
        import re
        match = re.search(r'- \*\*Name:\*\*\s*(\w+)', content)
        if match:
            claw_name = match.group(1)
            return f"{claw_name} Text2SQL 知识库"
        else:
            return default_name
    except Exception:
        return default_name


def save_kb_config(kb_id: int):
    """保存知识库ID到配置文件"""
    config = {}
    if os.path.exists(KB_CONFIG_PATH):
        try:
            with open(KB_CONFIG_PATH, 'r') as f:
                config = json.load(f)
        except:
            pass
    
    config['kb_id'] = kb_id
    
    with open(KB_CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)


def load_kb_config() -> dict:
    """加载知识库配置"""
    if os.path.exists(KB_CONFIG_PATH):
        try:
            with open(KB_CONFIG_PATH, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description='ByteHouse 知识库创建工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python3 create_knowledge_base.py "我的SQL知识库"
  python3 create_knowledge_base.py "自定义知识库" --config '{"api_key": "xxx", "url": "https://xxx"}'

环境变量:
  BYTEHOUSE_HOST      - ByteHouse 主机 (如 tenant-xxx-cn-beijing-public.bytehouse.volces.com)
  BYTEHOUSE_PASSWORD  - 密码 (作为 Bearer token)

自定义 Config (通过 --config 参数):
  api_key - 自定义 API Key
  url     - 自定义 API URL
'''
    )
    
    parser.add_argument('name', nargs='?', help='知识库名称（可选，默认从IDENTITY.md获取）')
    parser.add_argument('--config', type=str, help='JSON 格式的配置，包含 api_key, url')
    
    args = parser.parse_args()
    
    # 解析 config 参数
    config = None
    if args.config:
        try:
            config = json.loads(args.config)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in --config: {e}", file=sys.stderr)
            sys.exit(1)
    
    import time
    # 获取知识库名称
    kb_name = args.name if args.name else get_claw_name()  + f"_{int(time.time())}"
    
    try:
        kb_id = create_knowledge_base(kb_name, config)
        print(f"知识库创建成功！知识库名称: {kb_name}")
        print(f"知识库ID: {kb_id}")
        print(f"配置已保存到: {KB_CONFIG_PATH}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()