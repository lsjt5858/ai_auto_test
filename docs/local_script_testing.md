# 本地脚本测试怎么执行

本地脚本测试用于验证 Skill 目录里的脚本是否可用。它不安装 Skill 到 OpenClaw，也不走 Agent 对话链路。

## 1. 已支持的执行方式

配置文件：

```text
/Users/apple1/AI_Code/ai_auto_test/config/skills/byted-bytehouse-ai-query-local-script.yaml
```

核心配置：

```yaml
base_url: script://临时添加的文件，仅供参考/byted-bytehouse-ai-query/scripts/{script}
execute_mode: script
```

含义：

```text
每条 case 指定要执行哪个 scripts/*.py
框架读取 account.md 中的 BYTEHOUSE_* 参数
把参数注入为环境变量
执行脚本
捕获 stdout/stderr/returncode
按 keywords / regex / rule 判断是否通过
生成 HTML 报告
```

## 2. 本地脚本 case 格式

示例文件：

```text
/Users/apple1/AI_Code/ai_auto_test/data/byted_bytehouse_ai_query_local_script_cases.csv
```

字段：

```text
case_id
skill
script
script_args
input
expected_answer
keywords
forbidden_words
assert_type
score_threshold
priority
```

示例：

```csv
LOCAL_SCRIPT_001,byted-bytehouse-ai-query-local-script,execute_sql.py,"{question}",SELECT 1,1,1,Error,keyword,1.0,P0
```

执行时：

```text
{question} 会被替换成 input 字段
```

实际命令近似为：

```bash
python scripts/execute_sql.py "SELECT 1"
```

## 3. 执行命令

```bash
cd /Users/apple1/AI_Code/ai_auto_test
venv/bin/python run.py \
  --case-file data/byted_bytehouse_ai_query_local_script_cases.csv \
  --runtime-params "临时添加的文件，仅供参考/account.md" \
  -m smoke \
  --html-report reports/local_script_report.html \
  --report-title "Local Script Test Report"
```

报告路径：

```text
/Users/apple1/AI_Code/ai_auto_test/reports/local_script_report.html
```

## 4. 适合测什么

适合：

```text
连接配置是否有效
execute_sql.py 能否执行 SQL
list_tables.py 能否列库/列表
create_knowledge_base.py 是否能创建知识库
add_content_to_kb.py 是否能添加内容
search_knowledge_base.py 是否能检索内容
upload_file_to_kb.py 是否能上传文件
```

不适合：

```text
验证 OpenClaw 是否能识别自然语言意图
验证 OpenClaw 是否能触发 Skill
验证 Agent 平台的参数追问和对话上下文
```

