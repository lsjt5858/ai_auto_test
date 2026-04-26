# Skill 测试模式说明

这份文档解释当前项目到底在测什么，以及后续要如何扩展到 OpenClaw 端到端测试。

## 1. 当前已经实现的测试模式

当前框架已经实现三种执行模式。

### 1.1 离线评测模式：`sample://`

配置示例：

```yaml
base_url: sample://arkclaw-response
```

执行含义：

```text
不安装 Skill
不登录 OpenClaw
不真实触发 Skill
只读取评测集里的“真实返回举例”
再用 evaluator 校验 expected/rule
```

适合：

- 快速验证评测集字段是否能被框架读取
- 快速验证断言规则是否合理
- 回放历史人工测试结果

不适合：

- 证明 Skill 真正可用
- 证明 OpenClaw 能正确触发 Skill

### 1.2 本地脚本模式：`script://`

配置示例：

```yaml
skill_name: byted-bytehouse-ai-query-online
base_url: script://临时添加的文件，仅供参考/byted-bytehouse-ai-query/scripts/execute_sql.py
script_args:
  - "{question}"
required_params:
  - BYTEHOUSE_HOST
  - BYTEHOUSE_PORT
  - BYTEHOUSE_USER
  - BYTEHOUSE_PASSWORD
```

执行含义：

```text
不安装 Skill 到 OpenClaw
不走 OpenClaw 对话触发链路
直接执行 Skill 目录里的功能脚本
把运行态账号参数注入为环境变量
用 case.input 作为脚本参数
捕获 stdout/stderr
再用 evaluator 校验输出
```

当前 `byted-bytehouse-ai-query-online` 跑的就是这个模式。

更通用的本地脚本测试配置是：

```text
config/skills/byted-bytehouse-ai-query-local-script.yaml
```

示例 case：

```text
data/byted_bytehouse_ai_query_local_script_cases.csv
```

实际执行脚本是：

```text
/Users/apple1/AI_Code/ai_auto_test/临时添加的文件，仅供参考/byted-bytehouse-ai-query/scripts/execute_sql.py
```

真实执行命令形态类似：

```bash
BYTEHOUSE_HOST=...
BYTEHOUSE_PORT=...
BYTEHOUSE_USER=...
BYTEHOUSE_PASSWORD=...
venv/bin/python "临时添加的文件，仅供参考/byted-bytehouse-ai-query/scripts/execute_sql.py" "SELECT 1"
```

适合：

- 单测 Skill 内部脚本能力
- 验证登录信息是否有效
- 验证数据库脚本能否真实读写
- 快速定位问题是脚本问题、账号问题、SQL 问题还是 OpenClaw 触发问题

不适合：

- 验证 OpenClaw 是否正确识别用户意图
- 验证 OpenClaw 是否正确安装/加载 Skill
- 验证 OpenClaw 对话过程中的参数追问、上下文管理和最终回答

### 1.3 HTTP 接口模式

配置示例：

```yaml
base_url: https://example.com/api/skill/run
auth_type: bearer
```

执行含义：

```text
通过 requests.post 调用真实 HTTP 接口
请求体包含 skill_name、question、params
再校验接口返回的 answer/content
```

适合：

- Skill 平台提供了标准 HTTP 执行接口
- CI 里做在线回归

## 2. 当前还没有实现的 OpenClaw 端到端模式

你描述的真实 Skill 测试链路应该是：

```text
安装 Skill 到 OpenClaw
启动或进入 OpenClaw 会话
发送 case.input
OpenClaw 识别并触发对应 Skill
如果缺参数，OpenClaw 追问
框架输入账号/连接参数
OpenClaw 执行 Skill
框架获取最终回答
按 case.expected/rule 评估
生成报告
```

这属于 OpenClaw E2E 测试。当前项目还没有这条链路，因为还缺少 OpenClaw 的自动化入口。

要实现这条链路，需要明确至少一个入口：

```text
1. OpenClaw CLI 命令
2. OpenClaw HTTP API
3. OpenClaw Web UI，可用浏览器自动化驱动
4. OpenClaw 本地 SDK
```

本机当前没有检测到 `openclaw` 命令。

## 3. 两种测试方式应该如何分工

### 本地脚本测试

目标：

```text
验证 Skill 自己的功能脚本是否可用
```

粒度：

```text
脚本级 / 函数级 / SQL 级
```

优点：

```text
快、稳定、容易定位问题
```

当前已实现。

### OpenClaw 端到端测试

目标：

```text
验证用户在 OpenClaw 里说一句话后，Skill 是否被正确触发并完成任务
```

粒度：

```text
用户对话级 / Skill 触发级 / 参数追问级 / 最终回答级
```

优点：

```text
最接近真实使用场景
```

当前尚未实现，需要 OpenClaw 自动化入口。

## 4. 当前正常执行脚本是什么样子

以 `byted-bytehouse-ai-query-online` 为例。

Skill 配置：

```text
config/skills/byted-bytehouse-ai-query-online.yaml
```

Case 文件：

```text
data/byted_bytehouse_ai_query_online_cases.csv
```

运行态参数：

```text
临时添加的文件，仅供参考/account.md
```

执行命令：

```bash
cd /Users/apple1/AI_Code/ai_auto_test
AI_TEST_RUNTIME_PARAMS_FILE="临时添加的文件，仅供参考/account.md" \
AI_TEST_CASE_FILE="data/byted_bytehouse_ai_query_online_cases.csv" \
venv/bin/python -m pytest -m smoke --tb=short --junitxml=reports/bytehouse_ai_query_online_junit.xml
```

框架内部对每条 case 做的事：

```text
读取 CSV 一行 case
  -> 根据 case.skill 找 config/skills/*.yaml
  -> 读取 account.md 里的 BYTEHOUSE_* 参数
  -> 执行 script:// 指向的 execute_sql.py
  -> 把 case.input 作为 SQL 参数传给脚本
  -> 捕获 stdout/stderr/returncode
  -> evaluator 校验 keywords/forbidden_words/rule
  -> pytest 产出结果
```

HTML 报告生成：

```bash
venv/bin/python tools/junit_to_html.py \
  reports/bytehouse_ai_query_online_junit.xml \
  reports/bytehouse_ai_query_online_report.html \
  "ByteHouse AI Query Online Test Report"
```

报告路径：

```text
reports/bytehouse_ai_query_online_report.html
```

新的推荐报告命令：

```bash
venv/bin/python run.py \
  --case-file data/byted_bytehouse_ai_query_local_script_cases.csv \
  --runtime-params "临时添加的文件，仅供参考/account.md" \
  -m smoke \
  --html-report reports/local_script_report.html \
  --report-title "Local Script Test Report"
```

## 5. 下一步如果要做 OpenClaw E2E

需要先补一个新的执行器，例如：

```yaml
skill_name: byted-bytehouse-ai-query-openclaw
base_url: openclaw://byted-bytehouse-ai-query
execute_mode: openclaw
required_params:
  - BYTEHOUSE_HOST
  - BYTEHOUSE_PORT
  - BYTEHOUSE_USER
  - BYTEHOUSE_PASSWORD
```

然后在 `core/client.py` 中实现 `_execute_openclaw`，职责是：

```text
安装 Skill
创建会话
发送问题
处理参数追问
注入运行态参数
等待最终回答
返回 SkillResponse
```

但这一步需要 OpenClaw 的自动化调用方式。如果 OpenClaw 有 CLI/API/Web UI 入口，框架就可以继续接。
