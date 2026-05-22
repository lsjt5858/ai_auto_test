---
name: byted-bytehouse-ai-query
description: ByteHouse AI 查询技能，支持自然语言转SQL（Text2SQL）、知识库关联增强、SQL执行、表结构查询，用于ByteHouse数据库的自然语言查询、SQL生成与执行。
---

# byted-bytehouse-ai-query

## 描述

ByteHouse AI Query Skill，提供 Text2SQL 接口能力，支持将自然语言转换为 SQL 并执行查询。

**核心能力**：
1. **Text2SQL** - 将自然语言描述的查询需求转换为 ByteHouse SQL 语句
2. **List Tables** - 列出数据库中的表
3. **Execute SQL** - 执行 SQL 查询并返回结果
4. **知识库管理** - 创建知识库、添加知识库内容、查询知识库，Text2SQL自动关联知识库提升准确率

## 📁 文件说明

- **SKILL.md** - 本文件，技能主文档
- **text2sql.py** - Text2SQL 转换脚本（自动关联知识库）
- **list_tables.py** - 列出数据库中的表
- **execute_sql.py** - 执行 SQL 查询脚本
- **create_knowledge_base.py** - 创建知识库脚本
- **add_content_to_kb.py** - 向知识库添加内容脚本
- **search_knowledge_base.py** - 查询知识库内容脚本
- **upload_file_to_kb.py** - 上传文件到知识库脚本(pdf/md/docx/xlsx)


## 前置条件

- Python 3.8+
- uv (已安装在 `/root/.local/bin/uv`)
- ByteHouse连接信息（需自行配置环境变量）

## 配置信息

### ByteHouse连接配置

```bash
# 基础配置
export BYTEHOUSE_HOST="<ByteHouse主机>"      # 如 tenant-xxx-cn-beijing-public.bytehouse.volces.com
export BYTEHOUSE_PASSWORD="<密码>"            # 用作 Bearer token (Text2SQL)
export BYTEHOUSE_USER="<用户名>"              # 用于执行 SQL
export BYTEHOUSE_PORT="<端口>"                # 默认 8123

# 知识库配置（可选）
export KB_ID="<知识库ID>"                     # 可选，指定Text2SQL使用的知识库ID
```
如果不配置KB_ID，系统会自动创建一个新的知识库并自动关联使用，知识库ID会保存在 `~/.bytehouse_kb_config.json`

## 🚀 快速开始

### 1. 列出数据库和表

```bash
# 列出所有数据库
python3 list_tables.py --databases

# 列出指定数据库的表
python3 list_tables.py --database tpcds
```

### 2. 使用 Text2SQL

```bash
# 环境变量方式
export BYTEHOUSE_HOST="tenant-xxx-cn-beijing-public.bytehouse.volces.com"
export BYTEHOUSE_PASSWORD="<your-password>"

# 执行 Text2SQL
python3 text2sql.py "get count of all call centers" "tpcds.call_center"
```

返回：
```sql
SELECT COUNT(*) AS call_center_count FROM tpcds.call_center;
```

### 3. 执行 SQL 查询

```bash
python3 execute_sql.py "SELECT * FROM tpcds.call_center LIMIT 5"
python3 execute_sql.py "SELECT count(*) FROM tpcds.store_sales" --format pretty
```

### 4. 完整流程：Text2SQL + Execute

```bash
# 1. 先获取 SQL
SQL=$(python3 text2sql.py "get count of call centers" "tpcds.call_center")

# 2. 执行 SQL
python3 execute_sql.py "$SQL"
```

### 5. 知识库使用

```bash
# 手动创建知识库（可选，系统会自动创建）
python3 create_knowledge_base.py  # 不指定名称，默认使用当前Claw的名字（如"ArkClaw Text2SQL 知识库"）

# 向知识库添加内容（可以添加表结构、业务规则等）
python3 add_content_to_kb.py "store_sales表是销售数据表，包含字段ss_sold_date_sk（销售日期）、ss_item_sk（商品ID）、ss_quantity（销售数量）、ss_amount（销售金额）"
python3 add_content_to_kb.py --file ./table_schema.md  # 从文件批量添加

# 查询知识库内容
python3 search_knowledge_base.py "销售表字段"

# 上传文件到知识库
python3 upload_file_to_kb.py --file ./xxxx_schema.md

# Text2SQL会自动使用知识库内容提升转换准确率
python3 text2sql.py "查询2023年销售总金额" "tpcds.store_sales"
```

## 💻 程序化调用

### Text2SQL + Execute 一体化

```python
import subprocess
import json

def ai_query(natural_language: str, tables: list, config: dict = None) -> str:
    """
    调用 Text2SQL 并执行查询
    
    Args:
        natural_language: 自然语言描述
        tables: 要查询的表名列表
        config: 可选的配置 dict
    
    Returns:
        查询结果
    """
    # 1. 获取 SQL
    cmd = ["python3", "text2sql.py", natural_language] + tables
    if config:
        cmd.extend(["--config", json.dumps(config)])
    
    sql_result = subprocess.run(cmd, capture_output=True, text=True)
    sql = sql_result.stdout.strip()
    
    if not sql:
        return f"Text2SQL failed: {sql_result.stderr}"
    
    # 2. 执行 SQL
    result = subprocess.run(
        ["python3", "execute_sql.py", sql],
        capture_output=True,
        text=True
    )
    
    return result.stdout

# 使用示例
result = ai_query("get count of call centers", ["tpcds.call_center"])
print(result)
```

## API 参考

### Text2SQL 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| systemHints | string | 否 | 系统提示词，默认为 "TEXT2SQL" |
| input | string | **是** | 自然语言查询 |
| knowledgeBaseIDsString | string[] | 否 | 知识库ID列表，默认 ["*"] |
| tables | string[] | **是** | 要查询的表名列表 |
| config | object | 否 | 自定义配置 |
| config.reasoningModel | string | 否 | 自定义模型ID |
| config.reasoningAPIKey | string | 否 | 自定义 API Key |
| config.url | string | 否 | 自定义 API URL |