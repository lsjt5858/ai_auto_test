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
ByteHouse 知识库查询脚本
用于在ByteHouse知识库中搜索相关内容

配置方式：设置以下环境变量
- BYTEHOUSE_HOST: ByteHouse 主机地址 (如 tenant-xxx-cn-beijing-public.bytehouse.volces.com)
- BYTEHOUSE_PASSWORD: 密码 (用作 Bearer token)
- KB_ID: 知识库ID (可选，如果未设置会从配置文件读取)
"""

import os
import requests
import json
import sys
import argparse
from create_knowledge_base import load_kb_config

# 从环境变量读取默认配置
BYTEHOUSE_HOST = os.environ.get('BYTEHOUSE_HOST', '')
BYTEHOUSE_PASSWORD = os.environ.get('BYTEHOUSE_PASSWORD', '')
KB_ID = os.environ.get('KB_ID', '')


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


def get_kb_id() -> int:
    """获取知识库ID，优先从环境变量，其次从配置文件"""
    if KB_ID:
        try:
            return int(KB_ID)
        except ValueError:
            print(f"Error: KB_ID environment variable is not a valid integer: {KB_ID}", file=sys.stderr)
            sys.exit(1)
    
    # 从配置文件读取
    config = load_kb_config()
    kb_id = config.get('kb_id')
    
    if not kb_id:
        print("Error: No KB_ID found. Please set KB_ID environment variable or create a knowledge base first.", file=sys.stderr)
        print("Hint: Use create_knowledge_base.py to create a new knowledge base.", file=sys.stderr)
        sys.exit(1)
    
    return kb_id


def search_knowledge_base(
    search_query: str, 
    kb_id: int = None, 
    top_k: int = 5,
    min_distance: int = 0,
    config: dict = None
) -> list:
    """
    在知识库中搜索相关内容
    
    Args:
        search_query: 搜索查询文本
        kb_id: 知识库ID，如果不提供会自动获取
        top_k: 返回最相关的前K条结果，默认5
        min_distance: 最小距离阈值，默认0
        config: 可选的配置 dict，支持:
            - url: 自定义 API URL
            - api_key: 自定义 API Key
    
    Returns:
        搜索结果列表
    """
    if kb_id is None:
        kb_id = get_kb_id()
    
    # 决定使用哪个配置：用户提供的 config > 环境变量
    if config:
        base_url = config.get('url', '')
        auth_token = config.get('api_key', '')
        
        if not base_url:
            print("Error: config.url is required when using custom config", file=sys.stderr)
            sys.exit(1)
        
        url = f"{base_url.rstrip('/')}/matrix/v1/knowledge-base/evaluate"
    else:
        if not BYTEHOUSE_HOST:
            print("Error: Please set BYTEHOUSE_HOST environment variable or provide --config", file=sys.stderr)
            sys.exit(1)
        
        url = build_kb_api_url(BYTEHOUSE_HOST, 'knowledge-base/evaluate')
        auth_token = BYTEHOUSE_PASSWORD if BYTEHOUSE_PASSWORD else ""
    
    headers = {
        "Content-Type": "application/json",
    }
    
    # 添加认证
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    # 构建请求 payload
    payload = {
        "knowledgeBaseID": kb_id,
        "search": search_query,
        "topK": top_k,
        "minimumDistance": min_distance
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=15)
    if not response.ok:
        response.raise_for_status()
    result = response.json()
    # 兼容不同返回格式：results可能在根节点或data字段里
    return result.get('results', []) or (result.get('data', {}).get('results', []) if isinstance(result.get('data'), dict) else [])


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description='ByteHouse 知识库查询工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 简单搜索
  python3 search_knowledge_base.py "销售表结构"
  
  # 返回前10条结果
  python3 search_knowledge_base.py "store_sales字段" --top-k 10
  
  # 指定知识库ID
  python3 search_knowledge_base.py "查询语法" --kb-id 123
  
  # 自定义阈值
  python3 search_knowledge_base.py "日期字段" --min-distance 50
  
  # 使用自定义配置
  python3 search_knowledge_base.py "查询" --config '{"api_key": "xxx", "url": "https://xxx"}'

环境变量:
  BYTEHOUSE_HOST      - ByteHouse 主机 (如 tenant-xxx-cn-beijing-public.bytehouse.volces.com)
  BYTEHOUSE_PASSWORD  - 密码 (作为 Bearer token)
  KB_ID               - 知识库ID (可选，优先使用)
'''
    )
    
    parser.add_argument('query', help='搜索查询文本')
    parser.add_argument('--top-k', type=int, default=5, help='返回最相关的前K条结果，默认5')
    parser.add_argument('--min-distance', type=int, default=0, help='最小距离阈值，默认0')
    parser.add_argument('--kb-id', type=int, help='指定知识库ID，优先级高于环境变量和配置文件')
    parser.add_argument('--raw', action='store_true', help='输出原始JSON结果')
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
    
    try:
        kb_id = args.kb_id if args.kb_id else get_kb_id()
        results = search_knowledge_base(args.query, kb_id, args.top_k, args.min_distance, config)
        
        if args.raw:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print(f"搜索结果 (知识库ID: {kb_id}, 查询: \"{args.query}\"):")
            print("=" * 80)
            for i, result in enumerate(results, 1):
                # 兼容相似度字段名：可能是distance或similarityScore
                similarity = result.get('distance') or result.get('similarityScore')
                print(f"\n{i}. 相似度: {similarity:.4f}" if similarity is not None else f"\n{i}. 相似度: N/A")
                print(f"内容: {result.get('content', '').strip()[:200]}..." if len(result.get('content', '')) > 200 else f"内容: {result.get('content', '').strip()}")
                print("-" * 60)
            
            print(f"\n共找到 {len(results)} 条结果")
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()