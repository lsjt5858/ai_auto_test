# 通用 Skill 接入与测试说明

## 1. 这份文档解决什么问题

这份文档不再只讨论“固定 3 个 Skill 怎么测”，而是回答一个更通用的问题：

“未来可能会有很多个 Skill，而且每个 Skill 在测试前都可能需要先传参数、建立连接、初始化上下文，这种情况下框架该怎么设计？”

答案是：

- 不要按 Skill 数量设计框架
- 要按“通用接入流程”设计框架
- 把每个 Skill 都当成同一种被测对象
- 把 Skill 的差异放到配置和数据里，而不是写死在代码里

你可以把这份文档理解为：

- Skill 测试通用接入规范
- Skill 测试步骤说明
- Skill 测试框架抽象方案

---

## 2. 先说结论：不是测 3 个 Skill，而是要做一套通用能力

如果未来会有很多个 Skill，那么框架核心不应该是：

- `test_skill_a.py`
- `test_skill_b.py`
- `test_skill_c.py`

而应该是抽出一套统一能力：

1. 读取 Skill 配置
2. 注入前置参数
3. 建立连接或初始化上下文
4. 调用 Skill
5. 获取返回结果
6. 执行统一评估
7. 输出统一报告

也就是说，以后不管有多少个 Skill，本质都走同一条链路：

`参数准备 -> 初始化连接 -> 执行 Skill -> 获取结果 -> 自动断言 -> 报告输出`

这才是你真正要做的“通用技能”。

---

## 3. 你这个场景里，真正的通用能力有哪些

未来 Skill 越多，越不能每个都单独写死。

建议先抽出下面几类通用能力。

## 3.1 Skill 配置读取能力

每个 Skill 可能有不同的：

- `skill_name`
- 入口地址
- 鉴权方式
- 前置参数
- 初始化参数
- 默认上下文
- 评估策略

所以一定要把这些内容做成配置，而不是写死在测试代码里。

## 3.2 参数注入能力

你刚刚提到一个重点：

“要先提供一些参数，然后才能连接 Skill，才能使用 Skill 中的一些服务。”

这说明测试前其实存在一个前置阶段。

这类参数可能包括：

- 环境参数
- 用户身份参数
- token
- app_id
- tenant_key
- workspace_id
- session_id
- knowledge_base_id
- tool_config
- skill_config
- prompt 模板参数

所以框架必须支持“测试前置参数注入”。

## 3.3 Skill 初始化能力

有些 Skill 不是直接问一句话就能测，它可能先要：

- 建立会话
- 创建上下文
- 注册租户
- 绑定知识库
- 初始化连接
- 加载插件
- 启动某个服务

所以框架里要有一层通用的 `setup/init` 能力。

## 3.4 通用调用能力

不管 Skill 是：

- 问答型
- 检索型
- 动作型
- 工具型

最终都应该通过统一客户端去调用。

这样你的测试文件才不会乱。

## 3.5 通用评估能力

不同 Skill 可以选不同断言组合，但评估入口应该统一。

例如统一支持：

- `exact_match`
- `keyword`
- `regex`
- `semantic_similarity`
- `llm_judge`
- `tool_call_check`
- `retrieval_check`

## 3.6 通用报告能力

最终不管测哪个 Skill，报告里都应该能统一看到：

- Skill 名称
- 前置参数
- 初始化信息
- 输入问题
- 实际返回
- 期望结果
- 断言明细
- 得分
- 失败原因

---

## 4. 未来很多个 Skill 时，推荐的整体设计思路

核心原则只有一句话：

不要按 Skill 写框架，要按 Skill 生命周期写框架。

一个 Skill 的测试生命周期一般可以抽成下面 5 个阶段：

1. `prepare`：准备参数
2. `connect`：建立连接
3. `setup`：初始化依赖资源
4. `execute`：执行 Skill
5. `evaluate`：评估结果

如果你的框架围绕这 5 个阶段来设计，那么以后接入第 10 个、第 20 个 Skill，也不会乱。

---

## 5. 最推荐的框架抽象

这里是最关键的部分。

建议你把每个 Skill 抽象成一种标准对象，而不是特殊脚本。

## 5.1 一个 Skill 至少要有这些信息

```text
skill_name
skill_type
base_url
auth_type
init_required
required_params
default_headers
setup_steps
execute_mode
assert_type
score_threshold
enabled
```

解释一下：

- `skill_name`：Skill 名称
- `skill_type`：问答型、检索型、动作型、工具型
- `base_url`：调用地址
- `auth_type`：鉴权方式
- `init_required`：是否需要初始化
- `required_params`：测试前必须提供的参数
- `setup_steps`：连接后要做哪些准备动作
- `execute_mode`：执行方式
- `assert_type`：用哪些评估策略
- `score_threshold`：通过阈值

## 5.2 Skill 的通用执行模型

你可以把每个 Skill 的执行过程统一理解成：

```text
加载 Skill 配置
    ->
校验前置参数
    ->
建立连接
    ->
执行初始化
    ->
发起 Skill 请求
    ->
获取结构化响应
    ->
执行评估
    ->
输出测试结果
```

这条链路建议固定下来。

---

## 6. 你提到的“先给参数才能连 Skill”该怎么做

这部分要单独讲，因为这是很多 AI Skill 测试框架最容易漏掉的地方。

## 6.1 为什么要把前置参数设计成一等公民

很多 Skill 的测试，并不是：

- 直接 question -> answer

而是：

- 先给环境参数
- 再给身份参数
- 再建立连接
- 再初始化依赖资源
- 然后才能真正执行 Skill

所以测试前置参数不能只是“顺手传一下”，而应该变成框架里的正式阶段。

## 6.2 前置参数分 4 类最清晰

### 第一类：环境参数

例如：

- `base_url`
- `env`
- `region`
- `workspace_id`

### 第二类：鉴权参数

例如：

- `token`
- `api_key`
- `app_id`
- `app_secret`

### 第三类：业务参数

例如：

- `tenant_key`
- `knowledge_base_id`
- `user_id`
- `session_id`
- `conversation_id`

### 第四类：Skill 特有参数

例如：

- `skill_id`
- `skill_version`
- `plugin_config`
- `tool_config`
- `prompt_vars`

## 6.3 推荐的处理方式

不要在测试函数里到处拼参数。

推荐做法是统一走：

- `config/` 读取静态配置
- `data/` 读取 case 参数
- `fixture` 负责组装运行态参数
- `client.py` 负责真正发送

这样以后新 Skill 来了，你只需要补配置和数据，不需要重写主流程。

---

## 7. Skill 测试前的通用步骤

不管以后多少个 Skill，测试前建议固定走下面这些步骤。

## 7.1 第一步：定义 Skill 元数据

先确认每个 Skill 的元信息：

- Skill 名称是什么
- Skill 是问答型还是动作型
- 有没有独立入口
- 是否需要初始化
- 必填参数有哪些
- 使用哪些服务
- 如何判断通过

如果这些都不清楚，后面脚本很容易反复推翻。

## 7.2 第二步：准备 Skill 配置

建议给每个 Skill 一份配置。

例如：

```yaml
skill_name: kb_qa
skill_type: qa
base_url: https://xxx/api/query
auth_type: bearer
init_required: true
required_params:
  - tenant_key
  - token
  - knowledge_base_id
setup_steps:
  - create_session
  - bind_kb
assert_type: keyword+llm_judge
score_threshold: 0.8
```

## 7.3 第三步：准备测试输入数据

测试数据不只要有问题，还要有运行参数。

推荐字段：

```text
case_id
skill_name
scenario
input_params
question
expected_answer
keywords
forbidden_words
expected_tool
expected_action
assert_type
score_threshold
enabled
priority
```

其中：

- `input_params` 很重要
- 它就是你说的“先提供的一些参数”

## 7.4 第四步：执行前参数校验

在真正连 Skill 之前，先校验：

- 必填参数有没有缺失
- 参数格式对不对
- token 是否为空
- 资源 ID 是否合法
- 环境配置是否完整

这一层要尽量前置，否则后面失败很难排查。

## 7.5 第五步：建立连接

连接阶段可能包括：

- 创建客户端
- 注入 headers
- 注入 token
- 绑定租户
- 获取 session

这一步建议做成统一方法，而不是每个 Skill 自己写一套。

## 7.6 第六步：执行 setup 初始化

如果 Skill 依赖外部服务，建议把初始化动作标准化。

例如：

- 创建会话
- 绑定知识库
- 注册插件
- 打开某个功能开关
- 准备上下文变量

## 7.7 第七步：执行 Skill

这时才开始真正测试：

- 发送问题
- 传业务参数
- 调用 Skill
- 获取结果

## 7.8 第八步：统一评估

执行完以后，根据 Skill 配置自动选择评估方式。

例如：

- 问答型 Skill：`keyword + semantic_similarity + llm_judge`
- 动作型 Skill：`exact_match + tool_call_check + llm_judge`
- 检索型 Skill：`retrieval_check + keyword`

## 7.9 第九步：结果落报告

Allure 中建议固定挂这些信息：

- `skill_name`
- `input_params`
- `setup_steps`
- `question`
- `actual_response`
- `expected_answer`
- `assertions`
- `score`
- `reason`

---

## 8. 推荐的数据设计：一个 Skill 一条配置，多条 case

这里非常重要。

以后 Skill 越多，最容易混乱的是：

- 到底哪些是 Skill 级配置
- 哪些是 case 级数据

建议你强制分开。

## 8.1 Skill 级配置

Skill 级配置放“公共能力”：

- Skill 名称
- 调用地址
- 鉴权方式
- 是否需要初始化
- 默认断言方式
- 默认阈值
- 必填参数列表

## 8.2 Case 级数据

Case 级数据放“具体测试内容”：

- 当前问题
- 当前输入参数
- 当前期望答案
- 当前期望动作
- 当前 case 的优先级

## 8.3 这样分开的好处

- 新增 Skill 时，只要加一份配置
- 新增 case 时，只要补数据
- 公共能力不会散落在测试脚本里

---

## 9. 推荐目录结构

如果按通用 Skill 框架来做，建议目录这样设计：

```text
ai_auto_test_project/
├── config/
│   ├── settings.py
│   └── skills/
│       ├── kb_qa.yaml
│       ├── report_query.yaml
│       └── ticket_create.yaml
├── data/
│   ├── skill_cases.xlsx
│   └── feishu_sync/
├── core/
│   ├── client.py
│   ├── loader.py
│   ├── skill_manager.py
│   ├── setup_manager.py
│   └── evaluator.py
├── evaluators/
│   ├── exact_match.py
│   ├── keyword_match.py
│   ├── semantic_similarity.py
│   ├── llm_judge.py
│   ├── tool_call_check.py
│   └── retrieval_check.py
├── testcases/
│   ├── test_skill_smoke.py
│   ├── test_skill_regression.py
│   └── test_skill_routing.py
└── reports/
```

注意这里的变化：

- 不再按每个 Skill 写一个测试文件作为主入口
- 而是按测试类型来组织

这样未来 Skill 增多时更稳。

---

## 10. 为什么推荐按“测试类型”而不是按“Skill 名称”组织测试文件

如果未来 Skill 很多，按 Skill 名称拆文件会越来越乱。

例如以后可能出现：

- `test_skill_a.py`
- `test_skill_b.py`
- `test_skill_c.py`
- `test_skill_d.py`

最后文件会越来越多，不利于维护。

更推荐按测试目标拆：

### `test_skill_smoke.py`

测：

- 每个 Skill 是否可连通
- 参数注入后是否可正常工作
- 关键返回结构是否存在

### `test_skill_routing.py`

测：

- 问题是否被路由到正确 Skill
- 是否误触发其他 Skill

### `test_skill_regression.py`

测：

- 核心回归问题
- 历史失败问题
- 高优业务问题

这样以后接入第 20 个 Skill，也还是这几个测试入口。

---

## 11. 一个新 Skill 接入测试框架时，具体步骤怎么做

下面这部分可以理解为“新 Skill 接入 SOP”。

## 11.1 第 1 步：拿到 Skill 信息

你要先向开发或产品确认：

- Skill 名称
- Skill 作用
- 调用入口
- 依赖哪些服务
- 是否要初始化
- 需要哪些前置参数
- 返回结构是什么
- 如何判断成功

## 11.2 第 2 步：补一份 Skill 配置

在 `config/skills/` 下新增一个 yaml。

例如：

```yaml
skill_name: report_query
skill_type: qa
base_url: https://xxx/api/query
auth_type: bearer
init_required: true
required_params:
  - token
  - user_id
  - workspace_id
setup_steps:
  - create_session
assert_type: keyword+semantic_similarity+llm_judge
score_threshold: 0.8
```

## 11.3 第 3 步：补测试数据

在总表中增加该 Skill 的 case。

例如：

```text
case_id: REPORT_001
skill_name: report_query
input_params: {"user_id":"u001","workspace_id":"w001"}
question: 怎么查看日报？
expected_answer: 在报表中心查看日报。
keywords: 报表中心, 日报
assert_type: keyword+llm_judge
score_threshold: 0.8
enabled: true
```

## 11.4 第 4 步：确认 setup 逻辑

如果这个 Skill 要先初始化，那么要定义清楚：

- 是不是要先建 session
- 是不是要先绑知识库
- 是不是要先准备工具配置

不要把这些逻辑塞在测试 case 里。

应该放到统一的 `setup_manager.py`。

## 11.5 第 5 步：跑冒烟

第一次接入新 Skill，不要直接跑全部 case。

先跑 3 到 5 条冒烟问题：

- 1 条标准 case
- 1 条边界 case
- 1 条异常 case

## 11.6 第 6 步：补评估策略

如果这个 Skill 是新类型，可能要新增评估器。

例如：

- 工具调用校验器
- 检索结果校验器
- 结构化字段校验器

但入口仍然统一走 `evaluator.py`。

## 11.7 第 7 步：纳入回归

冒烟通过以后，再把它纳入：

- 每日回归
- 发版前回归
- 历史缺陷回归

---

## 12. 以你说的场景举个最贴切的例子

你说的是：

“先提供一些参数，然后才能连接 Skill，才能使用 Skill 中的一些服务，才能进行测试。”

那么这条链路可以直接抽成：

### 第一步：输入运行参数

例如：

```json
{
  "token": "xxx",
  "tenant_key": "t001",
  "workspace_id": "w001",
  "skill_id": "report_query",
  "knowledge_base_id": "kb1001"
}
```

### 第二步：校验运行参数

框架先检查：

- token 是否存在
- workspace_id 是否存在
- skill_id 是否存在
- knowledge_base_id 是否符合当前 Skill 要求

### 第三步：建立 Skill 连接

例如：

- 创建 client
- 注入 headers
- 获取 session

### 第四步：初始化 Skill 依赖服务

例如：

- 绑定知识库
- 加载报表服务
- 打开插件

### 第五步：发起测试问题

例如：

- “帮我查看本月销售报表”

### 第六步：获取返回结果

例如：

- 返回回答内容
- 返回触发的服务
- 返回调用链路

### 第七步：统一评估

例如：

- 是否命中目标 Skill
- 是否调用了正确服务
- 回答是否正确
- LLM 评分是否达标

这就是你要的通用流程。

---

## 13. 建议你优先做的 4 个通用模块

如果要真正落框架，我建议先做这 4 个通用模块。

## 13.1 `skill_manager.py`

职责：

- 加载 Skill 配置
- 识别当前 Skill 的必填参数
- 返回统一 Skill 定义

## 13.2 `setup_manager.py`

职责：

- 执行连接前后的初始化动作
- 创建 session
- 绑定依赖资源
- 准备上下文

## 13.3 `client.py`

职责：

- 统一发请求
- 统一处理 headers
- 统一处理 token
- 统一处理超时和重试

## 13.4 `evaluator.py`

职责：

- 根据 Skill 配置决定用什么评估策略
- 聚合多个断言结果
- 输出统一评分和失败原因

---

## 14. 这种设计下，测试步骤应该怎么写

如果以后任何一个 Skill 要测，建议固定成下面的步骤。

1. 读取 Skill 配置
2. 读取 case 数据
3. 合并运行参数
4. 校验参数完整性
5. 执行连接
6. 执行 setup 初始化
7. 调用 Skill
8. 获取标准化响应
9. 执行评估
10. 生成 Allure 报告

你会发现，这 10 步对任何 Skill 都成立。

---

## 15. Allure 报告里建议固定展示什么

为了让很多个 Skill 也能统一看报告，建议固定展示这些字段：

- `skill_name`
- `skill_type`
- `required_params`
- `input_params`
- `setup_steps`
- `request_payload`
- `actual_response`
- `expected_answer`
- `assert_type`
- `assert_result`
- `score`
- `reason`

这样你后面看报告时，不需要先去猜这个 Skill 是怎么跑起来的。

---

## 16. 给你的最简理解版本

你现在可以把“Skill 测试框架”简单理解成下面这件事：

不是去为每个 Skill 写一份特殊代码，而是搭一个通用流水线：

`输入参数 -> 连接 Skill -> 初始化服务 -> 执行请求 -> 统一评估`

以后来了新 Skill，只需要：

- 加一份 Skill 配置
- 加一些测试数据
- 必要时补一个 setup 步骤

而不是重写整套框架。

---

## 17. 最推荐的落地方向

如果你是第一次做，我建议你当前就按下面方式理解和推进：

- 框架按“通用 Skill 生命周期”设计
- Skill 差异放在配置里
- 运行参数放在测试数据里
- 初始化逻辑放在 `setup_manager.py`
- 执行逻辑放在 `client.py`
- 评估逻辑放在 `evaluator.py`

这样未来 Skill 增多时，框架才不会崩。

---

## 18. 下一步我建议怎么做

如果你认可这个思路，下一步最值得做的不是继续写方案，而是把通用骨架先搭出来。

我建议直接落下面这些文件：

- `core/skill_manager.py`
- `core/setup_manager.py`
- `core/client.py`
- `core/evaluator.py`
- `config/skills/demo_skill.yaml`
- `testcases/test_skill_smoke.py`
- `testcases/test_skill_regression.py`

这样你后面不管来多少个 Skill，都可以按统一方式接入。
