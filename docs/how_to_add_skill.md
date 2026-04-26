# 如何在当前框架中接入一个新 Skill

本文档说明如何把一个 Skill 目录和评测集接入当前自动化框架。

当前框架的测试模式说明见：

```text
/Users/apple1/AI_Code/ai_auto_test/docs/testing_modes.md
```

## 1. 当前框架核心路径

项目根目录：

```text
/Users/apple1/AI_Code/ai_auto_test
```

核心文件：

```text
config/skills/                         # 每个 Skill 一份配置
data/                                  # 本地评测集
core/client.py                         # 调用层，当前使用 requests
core/loader.py                         # 评测集读取和字段映射
core/skill_manager.py                  # Skill 配置加载
core/setup_manager.py                  # 前置初始化
core/evaluator.py                      # 评估入口
evaluators/                            # 具体评估器
testcases/test_skill_smoke.py          # 冒烟测试入口
testcases/test_skill_regression.py     # 回归测试入口
reports/history/                       # 历史测试报告
```

## 2. 一个 Skill 接入框架需要两类文件

### 第 1 类：Skill 配置

路径：

```text
config/skills/<skill_name>.yaml
```

示例：

```yaml
skill_name: byted-bytehouse-ai-query
skill_type: database_qa
base_url: sample://arkclaw-response
auth_type: none
init_required: false
required_params: []
setup_steps: []
execute_mode: sample
assert_type: rubric
score_threshold: 0.8
enabled: true
```

说明：

- `skill_name` 必须和评测集里的 `skill` 字段一致
- `base_url: sample://...` 表示离线评测，读取评测集中的“真实返回举例”
- 以后有真实 HTTP 入口时，把 `base_url` 改成真实接口地址即可
- 当前接口调用层在 `core/client.py`，使用 `requests.post`

### 第 2 类：评测集

推荐放在：

```text
data/<skill_name>_cases.csv
```

也可以临时放在任意路径，然后用 `AI_TEST_CASE_FILE` 指定。

当前 CSV 支持这些字段：

```text
case_id
skill
对话轮次
input
预期的返回（部分关键信息）
真实返回举例（ArkClaw）
rule
```

字段映射关系：

```text
skill -> skill_name
input -> question
预期的返回（部分关键信息） -> expected_answer
真实返回举例（ArkClaw） -> actual_response
rule -> rule
```

### 第 3 类：运行态参数

登录、连接、token、workspace、tenant 等信息不要写进评测集，应该在每次执行时注入。

模板路径：

```text
/Users/apple1/AI_Code/ai_auto_test/config/runtime_params.example.json
```

你可以复制一份本地文件，例如：

```bash
cp config/runtime_params.example.json config/runtime_params.local.json
```

然后填写真实连接信息：

```json
{
  "skills": {
    "byted-bytehouse-ai-query": {
      "BYTEHOUSE_HOST": "真实地址",
      "BYTEHOUSE_PORT": "8123",
      "BYTEHOUSE_USER": "真实用户名",
      "BYTEHOUSE_PASSWORD": "真实密码",
      "BYTEHOUSE_SECURE": "true",
      "BYTEHOUSE_VERIFY": "true"
    }
  }
}
```

执行时指定：

```bash
venv/bin/python run.py \
  --case-file "临时添加的文件，仅供参考/核心能力测试评测集 - 评测集.csv" \
  --runtime-params config/runtime_params.local.json \
  -m smoke
```

也可以用环境变量注入：

```bash
export BYTEHOUSE_HOST="真实地址"
export BYTEHOUSE_PORT="8123"
export BYTEHOUSE_USER="真实用户名"
export BYTEHOUSE_PASSWORD="真实密码"
venv/bin/python run.py --case-file "data/xxx.csv" -m smoke
```

## 3. 当前 byted-bytehouse-ai-query 怎么跑

Skill 目录：

```text
/Users/apple1/AI_Code/ai_auto_test/临时添加的文件，仅供参考/byted-bytehouse-ai-query
```

Skill 配置：

```text
/Users/apple1/AI_Code/ai_auto_test/config/skills/byted-bytehouse-ai-query.yaml
```

评测集：

```text
/Users/apple1/AI_Code/ai_auto_test/临时添加的文件，仅供参考/核心能力测试评测集 - 评测集.csv
```

运行命令：

```bash
cd /Users/apple1/AI_Code/ai_auto_test
AI_TEST_CASE_FILE="临时添加的文件，仅供参考/核心能力测试评测集 - 评测集.csv" venv/bin/python -m pytest -m smoke --tb=short
```

当前这条命令跑的是“离线评测”：用 CSV 中的 `真实返回举例（ArkClaw）` 作为 Skill 输出，再按 `rule` 做评估。

如果要真实登录并执行，需要再满足两个条件：

1. 在 `config/runtime_params.local.json` 或环境变量中提供连接参数
2. 把 Skill 的 `base_url` 从 `sample://...` 改成真实调用入口，或实现 `script://...` 本地脚本执行模式

当前 `sample://...` 不会真的登录，也不会真的执行数据库操作。

## 4. 新增 byted-bytehouse-data-asset-analyzer 怎么做

Skill 目录：

```text
/Users/apple1/AI_Code/ai_auto_test/临时添加的文件，仅供参考/byted-bytehouse-data-asset-analyzer
```

已新增配置：

```text
/Users/apple1/AI_Code/ai_auto_test/config/skills/byted-bytehouse-data-asset-analyzer.yaml
```

已新增评测集模板：

```text
/Users/apple1/AI_Code/ai_auto_test/data/byted_bytehouse_data_asset_analyzer_cases.csv
```

运行离线契约测试：

```bash
cd /Users/apple1/AI_Code/ai_auto_test
AI_TEST_CASE_FILE="data/byted_bytehouse_data_asset_analyzer_cases.csv" venv/bin/python -m pytest -m smoke --tb=short
```

这一步验证的是：

- 评测集能被框架读取
- Skill 配置能被加载
- 返回结构是否符合 schema/catalog/lineage 的预期
- 评估报告链路是否可用

## 5. 如何判断新 Skill 是否真的可用

对 `byted-bytehouse-data-asset-analyzer`，自动化测试建议分三层：

### 第 1 层：包完整性检查

确认这些文件存在：

```text
SKILL.md
README.md
scripts/data_asset_analyzer.py
```

确认脚本语法可编译：

```bash
python3 -m py_compile "临时添加的文件，仅供参考/byted-bytehouse-data-asset-analyzer/scripts/data_asset_analyzer.py"
```

### 第 2 层：离线契约测试

使用 `data/byted_bytehouse_data_asset_analyzer_cases.csv` 跑 pytest。

这层不连接真实 ByteHouse，只验证预期输出契约和评估链路。

### 第 3 层：在线集成测试

准备真实依赖：

```bash
export BYTEHOUSE_HOST="<ByteHouse-host>"
export BYTEHOUSE_PORT="<ByteHouse-port>"
export BYTEHOUSE_USER="<ByteHouse-user>"
export BYTEHOUSE_PASSWORD="<ByteHouse-password>"
export BYTEHOUSE_SECURE="true"
export BYTEHOUSE_VERIFY="true"
```

然后把 `config/skills/byted-bytehouse-data-asset-analyzer.yaml` 的 `base_url` 从 `sample://...` 改成真实服务入口，或者扩展 `core/client.py` 增加 `script://` 执行模式。

如果该 Skill 只能通过本地脚本执行，推荐下一步实现：

```text
base_url: script://临时添加的文件，仅供参考/byted-bytehouse-data-asset-analyzer/scripts/data_asset_analyzer.py
```

当前 `core/client.py` 已支持 `script://`。它会把运行态参数注入为环境变量，执行脚本并捕获 stdout/stderr，再交给评估器判断。

示例配置：

```yaml
skill_name: byted-bytehouse-data-asset-analyzer
skill_type: data_asset_analyzer
base_url: script://临时添加的文件，仅供参考/byted-bytehouse-data-asset-analyzer/scripts/data_asset_analyzer.py
auth_type: none
init_required: false
required_params:
  - BYTEHOUSE_HOST
  - BYTEHOUSE_PORT
  - BYTEHOUSE_USER
  - BYTEHOUSE_PASSWORD
execute_mode: script
assert_type: rubric
score_threshold: 0.8
enabled: true
```

## 6. 用户指定 case 目录怎么跑

如果一个 Skill 有多份评测集，可以放到同一个目录：

```text
data/byted-bytehouse-ai-query/
├── smoke.csv
├── regression.csv
└── safety.csv
```

执行整个目录：

```bash
venv/bin/python run.py \
  --case-dir data/byted-bytehouse-ai-query \
  --runtime-params config/runtime_params.local.json \
  -m smoke
```

框架会自动读取目录下所有 `.csv` 和 `.json` 文件。

## 7. 如何生成报告

pytest 控制台报告：

```bash
venv/bin/python -m pytest -m smoke --tb=short
```

Allure 原始结果：

```bash
AI_TEST_CASE_FILE="data/byted_bytehouse_data_asset_analyzer_cases.csv" venv/bin/python run.py -m smoke --allure
```

Markdown 总结报告放在：

```text
reports/history/
```
