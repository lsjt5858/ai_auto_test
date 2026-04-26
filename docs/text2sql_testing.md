# Text2SQL 自然语言测试怎么写

Text2SQL 测试用于验证自然语言是否能转换成符合预期的 SQL。

它仍然属于本地脚本测试，因为当前执行的是：

```text
临时添加的文件，仅供参考/byted-bytehouse-ai-query/scripts/text2sql.py
```

不是 OpenClaw Agent 对话触发。

## 1. Skill 配置

```text
/Users/apple1/AI_Code/ai_auto_test/config/skills/byted-bytehouse-ai-query-text2sql.yaml
```

核心配置：

```yaml
base_url: script://临时添加的文件，仅供参考/byted-bytehouse-ai-query/scripts/text2sql.py
execute_mode: script
assert_type: keyword+regex
```

## 2. case 模板

模板文件：

```text
/Users/apple1/AI_Code/ai_auto_test/data/templates/text2sql_cases.csv
```

字段：

```text
case_id
skill
input
script_args
expected_answer
keywords
regex_patterns
forbidden_words
assert_type
score_threshold
priority
```

示例：

```csv
TEXT2SQL_001,byted-bytehouse-ai-query-text2sql,查询 nation 表一共有多少条数据,"{question} TPC_H.nation",SELECT COUNT,SELECT,COUNT|count,Error,keyword+regex,0.8,P0
```

含义：

```text
input 是自然语言问题
script_args 中的 {question} 会替换成 input
TPC_H.nation 是 text2sql.py 需要的表名参数
keywords / regex_patterns 用来校验生成的 SQL
```

## 3. 执行命令

你可以先复制模板为真实评测集：

```bash
cp data/templates/text2sql_cases.csv data/byted_bytehouse_text2sql_cases.csv
```

然后执行：

```bash
venv/bin/python run.py \
  --case-file data/byted_bytehouse_text2sql_cases.csv \
  --runtime-params "临时添加的文件，仅供参考/account.md" \
  -m smoke \
  --html-report reports/text2sql_report.html \
  --report-title "Text2SQL Test Report"
```

## 4. 断言建议

Text2SQL 不建议只做完全相等断言。更推荐：

```text
keywords: SELECT,FROM,目标表名,关键字段
regex_patterns: COUNT|count, LIMIT 5|limit 5
forbidden_words: Error,Traceback,无法生成
```

如果后续接入 LLM 裁判，可以把自然语言、生成 SQL、期望 SQL 交给裁判判断是否等价。

