---
name: byted-bytehouse-ai-query
description: ByteHouse AI 查询技能，支持自然语言转SQL（Text2SQL）、知识库关联增强、SQL执行、表结构查询、多模态向量化和向量检索，用于ByteHouse数据库的自然语言查询、SQL生成与执行。
---

# byted-bytehouse-ai-query

## 描述

ByteHouse AI Query Skill，提供 Text2SQL 接口能力，支持将自然语言转换为 SQL 并执行查询。

**核心能力**：
1. **Text2SQL** - 将自然语言描述的查询需求转换为 ByteHouse SQL 语句
2. **List Tables** - 列出数据库中的表
3. **Execute SQL** - 执行 SQL 查询并返回结果
4. **知识库管理** - 创建知识库、添加知识库内容、查询知识库，Text2SQL自动关联知识库提升准确率
5. **多模态向量化** - 支持文本、图片、视频的向量化存储和混合检索

## 📁 文件说明

- **SKILL.md** - 本文件，技能主文档
- **init_config.py** - 初始化配置文件脚本
- **text2sql.py** - Text2SQL 转换脚本（自动关联知识库）
- **list_tables.py** - 列出数据库中的表
- **execute_sql.py** - 执行 SQL 查询脚本
- **create_knowledge_base.py** - 创建知识库脚本
- **add_content_to_kb.py** - 向知识库添加内容脚本
- **search_knowledge_base.py** - 查询知识库内容脚本
- **upload_file_to_kb.py** - 上传文件到知识库脚本(pdf/md/docx/xlsx)
- **embedding.py** - 多模态向量化脚本
- **search_client.py** - 向量检索客户端脚本(使用ByteHouse向量检索)
- **export_config.sh** - 配置导出环境变量脚本（从~/.bytehouse_config.json读取）

## 使用说明

1. 用户在没有提供连接配置的情况下直接提问，默认使用playground集群：通过脚本`init_config.py`初始化配置文件，再执行`export_config.sh`导出到环境变量，再执行查询
2. 用户给出库表的情况下，优先使用客户给出的库表进行查询
3. 不要直接输出敏感信息，如密码、Key等，确实需要输出时，需要Mask处理
4. 结果呈现：目前操作执行归属哪个集群、默认展示前5条符合查询条件的结果。返回异常：目前操作执行归属哪个集群、原因分析：具体的原因分析、使用建议。风险预警：目前操作执行归属哪个集群、风险提示：涉及的xx操作可能带来风险、能的风险详情：具体带来的风险解释、用户操作确认：向用户再次确认操作
5. 用户询问任何数据或者资产相关的问题，总是执行SQL查询后返回结果，不要根据上下文猜答案


## 前置条件

- Python 3.8+
- uv (已安装在 `/root/.local/bin/uv`)
- ByteHouse连接信息（需自行配置环境变量）

## 配置信息

### ByteHouse连接配置

执行`scripts/init_config.py`初始化配置文件`~/.bytehouse_config.json`。

如果用户提供了ByteHouse连接信息，也保存到该文件，避免重复向用户请求连接配置信息。当用户切换ByteHouse集群时，一并修改该文件。

**每次开始执行前，从`~/.bytehouse_config.json`读取ByteHouse连接信息，导出到环境变量**

```bash
# 基础配置（从~/.bytehouse_config.json读取，导出到环境变量）
source scripts/export_config.sh

# 知识库配置（可选）
export KB_ID="<知识库ID>"                     # 可选，指定Text2SQL使用的知识库ID

# 火山引擎方舟 API 配置（可选，不填时默认使用自带API KEY和模型）
export BH_ARK_API_KEY="<火山引擎方舟API密钥>"
export BH_ARK_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"
export BH_EMBEDDING_MODEL="doubao-embedding-vision-251215"
```
如果不配置KB_ID，系统会自动创建一个新的知识库并自动关联使用，知识库ID保存在 `~/.bytehouse_kb_config.json`

## 🚀 快速开始

### 1. 初始化配置文件，导出到环境变量

```bash
# 初始化配置文件
python3 scripts/init_config.py

# 从配置文件读取配置，导出到环境变量
source scripts/export_config.sh
```

### 2. 列出数据库和表

```bash
# 列出所有数据库
python3 scripts/list_tables.py --databases

# 列出指定数据库的表
python3 scripts/list_tables.py --database tpcds
```

### 3. 使用 Text2SQL

```bash
# 执行 Text2SQL
python3 scripts/text2sql.py "get count of all call centers" "tpcds.call_center"
```

返回：
```sql
SELECT COUNT(*) AS call_center_count FROM tpcds.call_center;
```

### 4. 执行 SQL 查询

```bash
python3 scripts/execute_sql.py "SELECT * FROM tpcds.call_center LIMIT 5"
python3 scripts/execute_sql.py "SELECT count(*) FROM tpcds.store_sales" --format pretty
```

### 5. 完整流程：Text2SQL + Execute

```bash
# 1. 先获取 SQL
SQL=$(python3 text2sql.py "get count of call centers" "tpcds.call_center")

# 2. 执行 SQL
python3 scripts/execute_sql.py "$SQL"
```

### 6. 知识库使用

```bash
# 手动创建知识库（可选，系统会自动创建）
python3 scripts/create_knowledge_base.py  # 不指定名称，默认使用当前Claw的名字（如"ArkClaw Text2SQL 知识库"）

# 向知识库添加内容（可以添加表结构、业务规则等）
python3 scripts/add_content_to_kb.py "store_sales表是销售数据表，包含字段ss_sold_date_sk（销售日期）、ss_item_sk（商品ID）、ss_quantity（销售数量）、ss_amount（销售金额）"
python3 scripts/add_content_to_kb.py --file ./table_schema.md  # 从文件批量添加

# 查询知识库内容
python3 scripts/search_knowledge_base.py "销售表字段"

# 上传文件到知识库
python3 scripts/upload_file_to_kb.py --file ./xxxx_schema.md

# Text2SQL会自动使用知识库内容提升转换准确率
python3 scripts/text2sql.py "查询2023年销售总金额" "tpcds.store_sales"
```

### 7. 多模态向量化

需要向量化多模态内容（文本、图片、视频），请使用以下脚本：
- [`scripts/embedding.py`](scripts/embedding.py) - 多模态向量化模块
- [`scripts/multimodal_search_client.py`](scripts/multimodal_search_client.py) - ByteHouse 检索客户端

```python
from scripts import ByteHouseMultimodalSearch

# 初始化客户端
search = ByteHouseMultimodalSearch(connection_type="http")

# 创建表
search.create_multimodal_table("my_index")

# 插入文档
search.insert_document("my_index", doc_id=1, content_type="text", 
                      content="ByteHouse 多模态检索", title="介绍")

# 向量检索（需要过滤0维向量，否则会报错）
query_embedding = search.embedding.encode_text("云原生数据仓库")
results = search.vector_search("my_index", query_embedding=query_embedding, top_k=10)
```

🔗 参考文档

- [ByteHouse 向量检索SQL文档](https://www.volcengine.com/docs/6464/1208707)
- [火山引擎多模态向量化API文档](https://www.volcengine.com/docs/82379/1409291)



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
