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
ByteHouse 知识库文件上传脚本
用于上传文件到ByteHouse知识库并自动进行切片处理
支持格式：md, txt, pdf, docx, xlsx, csv等

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
import os.path
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


def generate_upload_url(
    kb_id: int, 
    file_name: str, 
    file_size: int,
    config: dict = None
) -> tuple[str, str, str]:
    """
    生成文件上传预签名URL
    
    Args:
        kb_id: 知识库ID
        file_name: 文件名
        file_size: 文件大小（字节）
        config: 可选的配置 dict，支持:
            - url: 自定义 API URL
            - api_key: 自定义 API Key
    
    Returns:
        (file_id, upload_url, upload_method)
    """
    # 决定使用哪个配置：用户提供的 config > 环境变量
    if config:
        base_url = config.get('url', '')
        auth_token = config.get('api_key', '')
        
        if not base_url:
            print("Error: config.url is required when using custom config", file=sys.stderr)
            sys.exit(1)
        
        url = f"{base_url.rstrip('/')}/matrix/v1/knowledge-base/file/generate-upload-files-url"
    else:
        if not BYTEHOUSE_HOST:
            print("Error: Please set BYTEHOUSE_HOST environment variable or provide --config", file=sys.stderr)
            sys.exit(1)
        
        url = build_kb_api_url(BYTEHOUSE_HOST, 'knowledge-base/file/generate-upload-files-url')
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
        "files": [
            {
                "name": file_name,
                "sizeBytes": file_size
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    
    result = response.json()
    file_info = (result.get('data', []) or [])[0] if isinstance(result.get('data'), list) else {}
    
    file_id = file_info.get('fileID')
    upload_url = file_info.get('url')
    upload_method = file_info.get('method', 'PUT')
    
    if not file_id or not upload_url:
        print(f"Error: Failed to get upload URL from response: {result}", file=sys.stderr)
        sys.exit(1)
    
    return file_id, upload_url, upload_method


def upload_file(upload_url: str, upload_method: str, file_path: str) -> None:
    """上传文件到预签名URL"""
    with open(file_path, 'rb') as f:
        response = requests.request(
            upload_method.upper(),
            upload_url,
            data=f,
            timeout=120
        )
        response.raise_for_status()


def finish_upload(file_id: str, config: dict = None) -> None:
    """完成上传流程"""
    if config:
        base_url = config.get('url', '')
        auth_token = config.get('api_key', '')
        
        if not base_url:
            print("Error: config.url is required when using custom config", file=sys.stderr)
            sys.exit(1)
        
        url = f"{base_url.rstrip('/')}/matrix/v1/knowledge-base/file/complete-upload"
    else:
        if not BYTEHOUSE_HOST:
            print("Error: Please set BYTEHOUSE_HOST environment variable or provide --config", file=sys.stderr)
            sys.exit(1)
        
        url = build_kb_api_url(BYTEHOUSE_HOST, 'knowledge-base/file/complete-upload')
        auth_token = BYTEHOUSE_PASSWORD if BYTEHOUSE_PASSWORD else ""
    
    headers = {
        "Content-Type": "application/json",
    }
    
    # 添加认证
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    payload = {
        "fileID": file_id
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()


def load_file(
    file_id: str,
    chunk_size: int = 512,
    delimiters: list = None,
    enable_image_ocr: bool = False,
    enable_chunk_auto_merge: bool = False,
    config: dict = None
) -> None:
    """加载文件到知识库，启动切片处理"""
    if delimiters is None:
        delimiters = ["#", "##"]
    
    if config:
        base_url = config.get('url', '')
        auth_token = config.get('api_key', '')
        
        if not base_url:
            print("Error: config.url is required when using custom config", file=sys.stderr)
            sys.exit(1)
        
        url = f"{base_url.rstrip('/')}/matrix/v1/knowledge-base/file/load"
    else:
        if not BYTEHOUSE_HOST:
            print("Error: Please set BYTEHOUSE_HOST environment variable or provide --config", file=sys.stderr)
            sys.exit(1)
        
        url = build_kb_api_url(BYTEHOUSE_HOST, 'knowledge-base/file/load')
        auth_token = BYTEHOUSE_PASSWORD if BYTEHOUSE_PASSWORD else ""
    
    headers = {
        "Content-Type": "application/json",
    }
    
    # 添加认证
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    # 构建切片配置
    chunk_settings = {
        "size": chunk_size,
        "delimiters": delimiters
    }
    
    if enable_image_ocr:
        chunk_settings["enableImageOcr"] = True
    
    if enable_chunk_auto_merge:
        chunk_settings["enableChunkAutoMerge"] = True
    
    payload = {
        "fileID": file_id,
        "chunkSettings": chunk_settings
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description='ByteHouse 知识库文件上传工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 上传文件，使用默认配置
  python3 upload_file_to_kb.py --file ./table_schema.md
  
  # 指定知识库ID
  python3 upload_file_to_kb.py --kb-id 123 --file ./business_rules.pdf
  
  # 自定义切片配置
  python3 upload_file_to_kb.py --file ./document.md --chunk-size 1024 --delimiters "#,##,###"
  
  # 启用图片OCR和自动合并
  python3 upload_file_to_kb.py --file ./report.pdf --enable-image-ocr --enable-chunk-auto-merge
  
  # 使用自定义配置
  python3 upload_file_to_kb.py --file ./data.csv --config '{"api_key": "xxx", "url": "https://xxx"}'

环境变量:
  BYTEHOUSE_HOST      - ByteHouse 主机 (如 tenant-xxx-cn-beijing-public.bytehouse.volces.com)
  BYTEHOUSE_PASSWORD  - 密码 (作为 Bearer token)
  KB_ID               - 知识库ID (可选，优先使用)
'''
    )
    
    parser.add_argument('--file', required=True, help='要上传的文件路径')
    parser.add_argument('--kb-id', type=int, help='指定知识库ID，优先级高于环境变量和配置文件')
    parser.add_argument('--chunk-size', type=int, default=512, help='切片大小（字节），默认512')
    parser.add_argument('--delimiters', type=str, default='#,##', help='切片分隔符，逗号分隔，默认"#,##"')
    parser.add_argument('--enable-image-ocr', action='store_true', help='启用图片OCR识别，默认关闭')
    parser.add_argument('--enable-chunk-auto-merge', action='store_true', help='启用切片自动合并，默认关闭')
    parser.add_argument('--config', type=str, help='JSON 格式的配置，包含 api_key, url')
    
    args = parser.parse_args()
    
    # 检查文件是否存在
    if not os.path.isfile(args.file):
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    
    # 解析 config 参数
    config = None
    if args.config:
        try:
            config = json.loads(args.config)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in --config: {e}", file=sys.stderr)
            sys.exit(1)
    
    try:
        # 获取知识库ID
        kb_id = args.kb_id if args.kb_id else get_kb_id()
        
        # 获取文件信息
        file_name = os.path.basename(args.file)
        file_size = os.path.getsize(args.file)
        
        print("=========================================")
        print("ByteHouse 知识库文件上传")
        print("=========================================")
        print(f"知识库ID: {kb_id}")
        print(f"文件: {args.file}")
        print(f"文件名: {file_name}")
        print(f"文件大小: {file_size / 1024:.2f} KB")
        print()
        
        # Step 1: 生成上传URL
        print("Step 1/4: 生成预签名上传URL...")
        file_id, upload_url, upload_method = generate_upload_url(kb_id, file_name, file_size, config)
        print(f"  ✅ 成功，文件ID: {file_id}")
        print(f"  上传URL: {upload_url}")
        print(f"  上传方法: {upload_method}")
        
        # Step 2: 上传文件
        print("\nStep 2/4: 上传文件到对象存储...")
        upload_file(upload_url, upload_method, args.file)
        print("  ✅ 文件上传成功")
        
        # Step 3: 完成上传
        print("\nStep 3/4: 完成上传流程...")
        finish_upload(file_id, config)
        print("  ✅ 上传流程完成")
        
        # Step 4: 加载文件到知识库
        print("\nStep 4/4: 加载文件到知识库（启动切片处理）...")
        delimiters = [d.strip() for d in args.delimiters.split(',')]
        load_file(
            file_id, 
            args.chunk_size, 
            delimiters, 
            args.enable_image_ocr, 
            args.enable_chunk_auto_merge,
            config
        )
        print("  ✅ 文件加载成功，切片处理已启动")
        
        print("\n=========================================")
        print("✅ 所有步骤完成！文件已成功上传到知识库")
        print("=========================================")
        
    except Exception as e:
        print(f"\n❌ 上传失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()