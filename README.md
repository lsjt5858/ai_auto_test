# AI 测试自动化框架设计方案

## 1. 背景与目标

你当前的角色是测试工程师，目标不是一开始就把所有能力一次性做全，而是先搭出一个可持续演进的 AI 测试自动化框架。

和传统接口自动化相比，AI 应用测试有几个明显特点：

- 输出不完全稳定，不能只依赖强等值断言
- 测试结果需要结合规则、语义、模型裁判等多种评估方式
- 除了功能正确性，还要关注召回、幻觉、安全、稳定性、成本、时延
- 同一个问题通常需要批量数据集驱动执行，而不是单条 case 人工校验

因此，推荐采用一套"传统自动化 + 数据集驱动 + AI 评估器 + 报告分析"的组合式框架。

本方案目标：

- 支持 AI 问答、RAG、Agent、知识库等场景测试
- 支持接口级自动化执行
- 支持结构化测试数据管理
- 支持多种断言方式组合
- 支持离线回归和持续集成
- 支持逐步扩展，不要求第一版过度设计

## 2. 适用场景

这套框架适合以下类型的 AI 产品测试：

- Skill 技能测试
- 通用 LLM 问答
- 企业知识库问答
- RAG 检索增强问答
- 智能客服
- Copilot 类助手
- Agent 工具调用流程
- Prompt 版本回归测试

如果你当前主要是做 Skill、知识库问答或 RAG 系统，这个方案尤其合适。

## 2.1 当前推荐聚焦方向

结合你当前的情况，推荐按下面优先级推进：

1. 先做 `Skill` 技能测试
2. 再扩展到 `Agent` 工具调用测试
3. 最后补齐更广泛的通用 LLM 回归

原因是：

- `Skill` 测试边界更清晰，适合第一次搭框架
- 更容易定义输入、期望行为和断言标准
- 先把单技能的调用、返回、知识命中、评分链路跑通，再扩展到 Agent 会更稳

## 3. 建设原则

建议按以下原则设计框架：

### 3.1 先做 MVP，再做平台化

第一阶段只做最核心闭环：

- 测试数据准备
- 调接口执行
- 自动评估
- 生成报告

不要一开始就做复杂页面、任务调度中心、可视化平台。

### 3.2 测试能力分层

不要把所有逻辑都写进测试用例中。要把"调用能力"、"评估能力"、"数据能力"、"报告能力"拆开。

### 3.3 一条 case，多种断言

AI 输出天然不稳定，建议一条 case 支持多种断言组合：

- 规则断言
- 关键词断言
- 正则断言
- 语义相似度断言
- LLM-as-a-Judge 断言

### 3.4 数据集驱动

AI 测试的核心资产不是脚本，而是数据集。

建议把测试问题、期望答案、参考知识点、评估方式、业务标签统一沉淀到数据文件中。

## 4. 推荐技术栈

如果你是测试工程师，优先推荐 Python 技术栈，原因是上手快、生态成熟、适合数据处理和自动化。

推荐组合如下：

- `Python`：主开发语言
- `pytest`：测试执行框架，支持参数化、Fixture 复用、并发扩展
- `requests` 或 `httpx`：接口调用
- `pydantic`：请求/响应数据建模
- `pandas`：数据集读写与结果分析
- `openpyxl`：Excel 用例支持
- `allure-pytest`：测试报告，适合展示 Prompt、实际输出、期望输出和评分结果
- `python-dotenv`：环境变量管理
- `tenacity`：重试机制
- `loguru` 或 `logging`：日志管理

如果后面要加入向量评估或 embedding 相似度能力，可再补：

- `sentence-transformers`
- `numpy`
- `scikit-learn`

如果后面要引入更成熟的 RAG 评估能力，也可以考虑：

- `ragas`
- `trulens`

## 4.0 技术栈保留策略

你提到“热门技术栈都保留”，这个思路是对的，但第一版不建议把所有技术同时落地。

我建议采用下面的策略：

- `README` 中保留主流技术栈选项，方便后续扩展
- 项目首版只落地一套默认主路径，避免框架过重
- 对每个能力点给出“推荐方案”和“可替代方案”

这样做的好处是：

- 你后续想扩展时不需要重写设计
- 当前第一次搭框架时不会被复杂选型拖住
- 团队后面也更容易讨论升级路径

## 4.0.1 主流技术栈总览

下面是适合 AI 自动化测试的主流技术栈建议，我会在文档中保留它们，但首版只默认启用一部分。

### 测试执行层

- 推荐：`pytest`
- 可选：`unittest`

说明：

- `pytest` 更适合数据驱动、夹具复用、插件扩展
- `unittest` 更偏传统，但在 AI 测试场景不如 `pytest` 灵活

### 接口调用层

- 推荐：`httpx`
- 可选：`requests`

说明：

- `httpx` 更现代，也更适合后续异步扩展
- `requests` 更经典，上手简单

### 报告层

- 推荐：`allure-pytest`
- 可选：`pytest-html`

说明：

- `Allure` 更适合展示 AI 输入输出和评估细节
- `pytest-html` 更轻量，但表达力弱一些

### 数据层

- 推荐：`飞书多维表 + 本地缓存`
- 可选：`Excel/CSV`
- 可选：`JSON/YAML`

说明：

- 你当前优先选择飞书多维表，这很适合团队协作和真实问题沉淀
- 但落地时建议同步到本地缓存，避免测试完全依赖在线表格接口

### 评估层

- 推荐：`关键词/正则 + Embedding 相似度 + LLM-as-a-Judge`
- 可选：`ragas`
- 可选：`trulens`

说明：

- 你已经明确首版三种策略都要保留，这个方向合理
- `ragas` 和 `trulens` 更适合作为第二阶段增强能力，而不是 MVP 必需项

### 数据建模与配置

- 推荐：`pydantic + python-dotenv`
- 可选：`dataclasses + yaml`

## 4.0.2 首版默认推荐路径

虽然 README 保留主流技术栈，但结合你是第一次搭框架，我建议首版默认路线固定为：

- 语言：`Python`
- 执行引擎：`pytest`
- 请求库：`httpx`
- 报告：`allure-pytest`
- 数据源：`飞书多维表 + 本地 json/xlsx 缓存`
- 评估：`关键词/正则 + Embedding 相似度 + LLM-as-a-Judge`
- 配置：`.env + pydantic`

这条路径的优点是：

- 足够主流，后续维护成本低
- 首版就具备 AI 测试最关键的能力
- 对 Skill 测试特别合适
- 后续往 Agent 扩展时不用推倒重来

## 4.1 推荐的首版组合

如果你的目标是先快速做出一版可用的 AI 自动化测试框架，我建议把技术方案明确为：

- 测试引擎：`pytest`
- 测试报告：`allure-pytest`
- AI 质量判定：`LLM-as-a-Judge`
- 补充断言：`关键词/正则 + 语义相似度`
- 数据来源：`飞书多维表优先，本地缓存兜底`

也就是你提到的这条主线：

`Pytest + Allure + LLM-as-a-Judge`

它的优点是：

- 测试工程师容易上手
- 兼容传统接口自动化习惯
- 既能做精确断言，也能做模糊断言
- 既能本地执行，也方便接入 CI/CD
- 适合从知识库问答、RAG 系统逐步扩展到更复杂 AI 场景

## 4.2 基础测试框架层

这一层负责调度、执行、基础断言和报告展示，是整个自动化框架的底盘。

### 4.2.1 引擎：`pytest`

推荐使用 `pytest` 作为执行引擎，原因是：

- 支持 `parametrize`，适合批量跑测试数据集
- 支持 `fixture`，便于复用环境配置、token、会话上下文
- 支持按 marker 分类执行冒烟、回归、专项测试
- 支持并发扩展，例如结合 `pytest-xdist`
- 生态成熟，便于后续接入 Allure 和 CI 流水线

### 4.2.2 断言：精确断言 + 模糊断言

AI 测试不能只靠传统 `assert`，建议采用组合式断言：

- 精确断言：校验 HTTP 状态码、JSON 结构、字段存在性、布尔结果
- 模糊断言：校验关键字命中、正则模式、语义相似度、LLM 裁判断分

建议思路是：

- 底层接口正确性，用传统断言
- 自然语言回答质量，用模糊断言

### 4.2.3 报告：`Allure`

推荐使用 `Allure` 作为报告层，尤其适合 AI 测试，因为它能清晰展示：

- 输入问题或 Prompt
- 实际输出
- 期望输出或参考答案
- 评估策略
- 评分结果
- 失败原因

对测试工程师来说，这种展示方式比单纯看控制台日志直观很多。

## 5. 框架总体分层

建议按 6 层设计：

### 5.1 数据层

职责：

- 管理测试集
- 管理基线答案
- 管理知识片段
- 管理标签和评估配置
- 管理飞书多维表同步后的本地缓存

输入样例字段建议：

- `case_id`
- `module`
- `scenario`
- `question`
- `expected_answer`
- `keywords`
- `forbidden_words`
- `reference_context`
- `assert_type`
- `score_threshold`
- `enabled`
- `skill_name`
- `priority`
- `source`

### 5.2 用例层

职责：

- 按业务场景组织测试
- 驱动数据执行
- 调用底层客户端
- 调用评估器并产出断言结果

在实现上，建议这一层的测试文件保持轻量，主要负责：

- 读取数据
- 调用接口
- 调用评估器
- 写入 Allure 附件
- 做最终断言

建议按场景拆分：

- Skill 技能测试
- 知识库管理
- 检索召回
- 问答生成
- 多轮对话
- Agent 工具调用
- 安全拦截

### 5.3 接口客户端层

职责：

- 统一封装 AI 服务调用
- 统一鉴权、请求头、超时、重试
- 隔离测试代码和业务接口细节

这一层要尽量稳定，避免每个测试文件里重复写请求逻辑。

### 5.4 评估层

职责：

- 对 AI 返回结果做自动判断
- 输出通过/失败、得分、原因

建议至少支持 4 类评估器：

1. 精确规则评估
2. 关键词/正则评估
3. 语义相似度评估
4. LLM 裁判评估

其中最推荐的组合是：

- Skill / 知识库 / RAG 查准率场景：关键词/唯一标识断言
- 问答质量场景：语义相似度 + LLM-as-a-Judge
- 接口正确性场景：精确规则断言

### 5.5 报告层

职责：

- 输出测试结果
- 展示失败样本
- 汇总维度统计
- 支持回归对比

建议同时产出：

- `pytest` 控制台结果
- `allure` 可视化报告
- `csv` 或 `json` 明细结果

### 5.6 配置层

职责：

- 管理环境地址
- 管理 token
- 管理模型版本
- 管理阈值参数

建议通过 `.env` 或 `yaml` 统一管理。

## 6. 推荐目录结构

下面是一个适合 AI 自动化测试项目的目录设计，与你当前想法也比较匹配：

```text
ai_auto_test_project/
├── README.md
├── requirements.txt
├── pytest.ini
├── run.py
├── .env.example
├── config/
│   ├── settings.py              # 配置读取
│   └── env.yaml                 # 非敏感配置
├── data/
│   ├── llm_cases.xlsx           # LLM 问答测试集
│   ├── rag_cases.xlsx           # RAG 测试集
│   ├── kb_cases.xlsx            # 知识库精确断言测试集
│   ├── skill_cases.xlsx         # Skill 技能测试集
│   ├── feishu_sync/             # 从飞书多维表同步下来的数据
│   └── expected/                # 基线答案、上下文等
├── core/
│   ├── client.py                # AI 接口调用封装
│   ├── evaluator.py             # 评估器统一入口
│   ├── assertion.py             # 断言能力
│   ├── loader.py                # 数据加载
│   ├── logger.py                # 日志能力
│   └── models.py                # 数据模型定义
├── evaluators/
│   ├── exact_match.py           # 精确断言
│   ├── keyword_match.py         # 关键词断言
│   ├── regex_match.py           # 正则断言
│   ├── semantic_similarity.py   # 语义相似度
│   └── llm_judge.py             # LLM 裁判
├── testcases/
│   ├── test_0_skill.py          # Skill 能力测试
│   ├── test_1_kb_manage.py      # 知识库增删改查
│   ├── test_2_rag_search.py     # 检索召回测试
│   ├── test_3_llm_chat.py       # 问答质量测试
│   ├── test_4_agent_tool.py     # 工具调用测试
│   └── test_5_safety.py         # 安全与越权测试
├── integrations/
│   └── feishu_bitable.py        # 飞书多维表拉取测试数据
├── prompts/
│   └── judge_prompt.txt         # 裁判模型提示词
├── reports/
│   ├── allure-results/
│   └── history/
└── utils/
    ├── file_util.py
    ├── json_util.py
    └── time_util.py
```

## 7. 核心模块设计说明

### 7.1 `core/client.py`

职责：

- 封装统一请求入口
- 发送问题到 AI 服务
- 返回标准响应对象

建议统一返回结构，例如：

```python
{
    "success": True,
    "request_id": "xxx",
    "answer": "模型最终回答",
    "latency_ms": 1234,
    "tokens": {
        "prompt_tokens": 100,
        "completion_tokens": 200,
        "total_tokens": 300
    },
    "retrievals": [
        {"doc_id": "d1", "score": 0.92, "content": "..."}
    ],
    "tool_calls": []
}
```

这样后续评估器和报告层都能复用。

### 7.2 `core/evaluator.py`

职责：

- 根据 case 配置自动选择评估方式
- 聚合多个评估器输出
- 生成统一结果

建议输出统一评估结果：

```python
{
    "passed": True,
    "score": 0.86,
    "assertions": [
        {"type": "keyword", "passed": True, "detail": "..."},
        {"type": "llm_judge", "passed": True, "detail": "..."}
    ],
    "reason": "答案覆盖了核心知识点"
}
```

### 7.3 `core/loader.py`

职责：

- 从 `xlsx/csv/json` 读取测试数据
- 转换成标准 case 对象
- 支持标签筛选、模块筛选、启停控制

### 7.4 `evaluators/llm_judge.py`

职责：

- 让一个裁判模型根据评分标准评价回答质量
- 输出分数和判定理由

适合评估：

- 回答是否切题
- 是否覆盖关键点
- 是否存在幻觉
- 表达是否清晰

注意：

- 裁判模型本身也有不稳定性
- 建议加评分 rubric
- 建议保留人工抽样复核机制

可以把核心调用逻辑设计成类似下面的形式：

```python
is_pass = llm_judge(
    question="怎么查报表",
    actual_answer="点击右上角进入报表中心即可查看",
    expected_answer="在右上角操作进入报表页面",
)
```

返回值建议不仅有 `True/False`，还包含：

- `score`
- `reason`
- `raw_judge_output`
- `passed`

这样方便在 Allure 里直接展示评估细节。

### 7.5 `core/evaluator.py` 的推荐职责边界

你这次补充的思路非常适合写进统一评估入口，建议 `core/evaluator.py` 负责：

- 根据 `assert_type` 路由到不同评估器
- 支持多种策略组合执行
- 聚合最终得分与判定结果
- 返回统一结构给测试用例层

例如：

- `keyword`
- `regex`
- `semantic_similarity`
- `llm_judge`
- `keyword+llm_judge`
- `semantic_similarity+llm_judge`

## 8. 测试类型如何设计

AI 测试不要只做"问一个问题，看结果像不像"。建议拆成以下几类。

### 8.0 Skill 技能测试

这是你当前最优先的场景，建议第一批用例重点覆盖：

- Skill 是否被正确触发
- Skill 参数是否传递正确
- Skill 返回结构是否完整
- Skill 输出是否符合预期业务口径
- Skill 失败时是否有可解释错误信息

如果一个 Skill 背后还会调用知识库或模型回答，可以继续拆成：

- Skill 调用成功率
- Skill 结果正确率
- Skill 回答质量分
- Skill 超时率
- Skill 异常兜底能力

### 8.1 基础功能测试

验证接口是否可用：

- 接口返回码正确
- 字段结构完整
- 空输入、超长输入、特殊字符处理正常
- session 或 conversation_id 流程正常

这一类更接近传统接口自动化。

### 8.2 知识库管理测试

适合有 RAG/知识库系统的场景：

- 文档上传是否成功
- 文档切片是否完成
- 建库是否成功
- 文档删除后是否不再召回
- 文档更新后回答是否同步变化

### 8.3 检索召回测试

重点不只是回答内容，而是"该不该召回到正确文档"：

- TopK 是否包含目标文档
- 命中文档是否来自正确知识域
- 无关文档是否被错误召回
- 召回分数是否低于阈值时触发拒答

这一层非常关键，能帮助你定位问题出在"检索"还是"生成"。

### 8.4 问答质量测试

重点关注：

- 是否答非所问
- 是否遗漏关键点
- 是否产生幻觉
- 是否遵循指定话术
- 是否符合业务规则

### 8.5 稳定性与性能测试

关注：

- 平均响应时间
- P95 响应时间
- 并发场景下成功率
- 超时率
- 重试后的恢复能力

### 8.6 安全测试

建议覆盖：

- Prompt 注入
- 越权问答
- 敏感词输出
- 数据泄露
- 不当内容生成

## 9. 断言策略建议

AI 测试最重要的是断言策略，建议按场景组合使用。

### 9.1 强断言

适用于稳定输出场景：

- 状态码
- 布尔结果
- 固定字段
- 工具调用次数
- 指定 ID

### 9.2 弱断言

适用于自然语言输出：

- 包含关键词
- 不包含禁用词
- 正则匹配
- 字段长度范围

### 9.3 语义断言

适用于答案表达不固定但语义应一致的场景：

- 参考答案 embedding 相似度
- 关键点覆盖率

### 9.4 LLM 裁判断言

适用于复杂质量判断：

- 是否回答了用户问题
- 是否覆盖必要知识点
- 是否存在错误事实
- 是否满足业务口径

### 9.5 分层判责

建议评估时区分：

- 检索问题
- 生成问题
- 提示词问题
- 数据问题
- 接口问题

这样失败后才容易定位。

## 9.6 三种核心自动化断言策略

你补充的三种策略非常适合作为首版落地标准，我建议在项目里明确为默认策略。

### 策略 A：关键字/正则命中

这是最轻量、最稳定的做法，适合查准率和定向召回测试。

典型思路：

- 在知识库文档里埋一个唯一标识，例如 `[seed:123]`
- 测试时发起问题
- 断言模型回答或召回内容中是否出现该标识

适用场景：

- 知识库是否生效
- 文档是否被召回
- 指定知识片段是否进入答案

优点：

- 快速
- 成本低
- 结果稳定

局限：

- 只能验证是否命中，不能全面衡量回答质量

### 策略 B：语义相似度对比

这是比关键词更智能的一层，适合标准答案相对明确，但表述可能不同的场景。

实现思路：

- 使用 `sentence-transformers` 生成向量
- 计算实际回答与标准答案的余弦相似度
- 当 `Cosine Similarity > 0.85` 时认为通过

适用场景：

- FAQ 问答
- 标准业务话术问答
- 非完全一致但语义应接近的答案判断

优点：

- 比关键词更灵活
- 能容忍措辞差异

局限：

- 对事实性错误不一定敏感
- 阈值需要按业务场景调优

### 策略 C：LLM 充当裁判

这是 AI 自动化测试里最核心的一层，适合评估复杂回答质量。

实现思路：

- 构造专门的评判 Prompt
- 把 `question`、`actual_answer`、`expected_answer` 输入裁判模型
- 让裁判模型返回 `True/False` 或 `1-5 分`、`0-100 分`

适用场景：

- 是否真正回答了问题
- 是否覆盖关键点
- 是否存在幻觉
- 是否符合业务要求

优点：

- 灵活度最高
- 最接近人工评审

局限：

- 成本更高
- 本身存在一定不稳定性
- 需要清晰的评分标准和提示词约束

建议首版组合策略：

- `策略 A` 负责查准率和召回验证
- `策略 B` 负责相似答案判断
- `策略 C` 负责最终质量裁定

## 10. 测试数据集设计建议

建议把数据集作为核心资产管理。

每条测试数据推荐包含：

```text
case_id: C001
module: rag
scenario: 标准知识问答
question: 你们的退款规则是什么？
expected_answer: 用户提交申请后，3个工作日内处理退款。
keywords: 退款, 3个工作日, 申请
forbidden_words: 7天无理由
reference_context: 售后规则文档第3节
assert_type: keyword+llm_judge
score_threshold: 0.75
enabled: true
```

如果是 Skill 测试，建议再额外补充：

```text
skill_name: report_query
tool_input: {"date":"2025-01-01"}
expected_action: 查询报表
expected_tool: report_service
```

建议按以下维度给数据打标签：

- 技能名称
- 业务模块
- 风险等级
- 回归类型
- 是否冒烟
- 是否线上问题复现
- Prompt 版本
- 模型版本

## 11. 执行流程建议

推荐一条标准执行链路：

1. 读取测试集
2. 逐条调用 AI 接口
3. 保存原始请求和响应
4. 执行评估器
5. 生成断言结果
6. 输出报告
7. 对失败样本进行聚类分析

建议每次执行都保留以下信息：

- 原始问题
- 模型原始回答
- 检索结果
- 评估分数
- 判定原因
- 模型版本
- prompt 版本
- 环境信息
- 执行时间

## 12. 持续集成建议

当 MVP 可跑通后，可以接入 CI。

建议分三层：

### 12.1 冒烟集

特点：

- 数量少
- 运行快
- 覆盖主流程

适合每次发版必跑。

### 12.2 回归集

特点：

- 覆盖核心业务场景
- 包含历史缺陷 case
- 包含高风险问题

适合每日定时或版本发布前运行。

### 12.3 专项集

例如：

- 安全集
- 性能集
- RAG 召回专项
- Agent 工具调用专项

## 12.4 数据驱动与 CI/CD 结合

这部分非常值得做成高阶能力，因为 AI 测试的价值很大程度上取决于数据源是否真实、是否持续更新。

### 飞书多维表作为测试用例管理平台

可以把飞书多维表作为测试用例平台，统一管理：

- 真实用户问题
- 标准答案
- 唯一标识
- 业务标签
- 风险等级
- 是否纳入冒烟或回归

再通过 Python 定时拉取数据，转换成 `pytest.mark.parametrize` 的输入源。

这种方式的好处是：

- 测试数据维护门槛低
- 业务和测试可以共同维护
- 能持续沉淀线上真实问题
- 便于构建高价值回归集

落地建议：

- 飞书多维表作为主数据源
- 每次执行前同步到 `data/feishu_sync/`
- 测试执行优先读取本地缓存，避免网络抖动影响稳定性
- 同步脚本失败时，允许回退到最近一次缓存数据

### 自动化回归流水线

当框架成熟后，可以把脚本接入 GitLab、AIME 或其他流水线系统。

推荐流程：

1. 合并请求触发流水线
2. 拉起 AI 自动化测试脚本
3. 运行核心 500 个问题集
4. 汇总召回率、平均得分、失败样本
5. 根据门禁阈值判断是否允许发布

建议门禁示例：

- `LLM 裁判平均得分 < 80`，阻塞发布
- `RAG 召回率 < 90%`，阻塞发布
- `Skill 成功率 < 95%`，阻塞发布
- 冒烟集存在关键失败，阻塞发布

这样 AI 自动化测试就不仅是离线脚本，而是能真正进入发布质量门禁。

## 13. 第一版落地建议

如果你准备开始真正搭框架，建议按下面顺序推进。

### 第一步：先跑通最小闭环

先只做这些：

- 1 个 AI 接口客户端
- 1 个 Excel 测试集
- 2 种评估器
- 2 到 3 个场景测试文件
- 1 份 Allure 报告

### 第二步：优先支持两类关键能力

优先做：

- 关键词/规则断言
- LLM 裁判断言

这是最容易见效的组合。

### 第三步：再补 RAG 定位能力

如果你的系统有检索过程，再加：

- 召回文档校验
- TopK 命中率
- 拒答策略校验

### 第四步：接入 CI

把冒烟集接到流水线中，先建立回归机制。

## 14. 推荐实施路线图

### 阶段 A：方案验证期

目标：

- 框架能跑通
- 能读取测试数据
- 能请求 AI 服务
- 能出基础报告

交付物：

- 项目骨架
- 样例 case
- 初版 README

### 阶段 B：能力完善期

目标：

- 支持多种断言
- 支持 RAG 召回评估
- 支持失败原因分析

交付物：

- evaluator 扩展
- 数据集规范
- 分类报告

### 阶段 C：工程化接入期

目标：

- 接入 CI
- 支持多环境执行
- 支持版本对比回归

交付物：

- pipeline 配置
- 环境配置模板
- 回归执行说明

## 15. 风险与注意事项

在 AI 自动化测试中，下面这些点很常见：

- 不要要求所有自然语言答案完全一致
- 不要只相信 LLM 裁判结果，最好结合规则断言
- 不要忽视测试数据管理，数据集质量决定自动化质量
- 不要把检索问题和生成问题混在一起判断
- 不要只看通过率，要看失败样本分布和变化趋势

## 16. 建议你下一步怎么做

你现在最适合的推进方式是：

1. 先确认你的 AI 产品类型
2. 明确第一批要覆盖的测试场景
3. 按本 README 的目录搭一个最小工程
4. 先做 20 到 30 条高价值测试数据
5. 先跑通关键词断言和 LLM 裁判断言
6. 再决定是否扩展到 RAG、Agent、安全专项

## 17. 我建议的首版范围

如果让我帮你规划第一版，我建议范围如下：

- 语言：`Python`
- 框架：`pytest + httpx + allure`
- 数据：`飞书多维表 + 本地缓存`
- 场景：`Skill 测试 + 知识库问答 + RAG 检索`
- 断言：`规则断言 + 关键词断言 + 语义相似度 + LLM 裁判`
- 报告：`allure + csv 明细`

这个组合最适合测试工程师第一次快速起步，同时也能兼顾你后续扩展到 Agent 的需求。

## 18. 后续可继续补充的内容

等你确认方案后，下一步我可以继续帮你做下面几件事：

- 直接生成项目骨架目录
- 编写 `requirements.txt`
- 编写 `pytest.ini`
- 编写 `run.py`
- 编写 `core/client.py` 和 `core/evaluator.py` 初版
- 设计 Excel 测试数据模板
- 生成 3 个示例测试用例

---

如果你认可这个方向，下一步就可以直接开始进入"搭框架"阶段，我可以继续帮你把这份方案落成一个可运行的 Python 项目骨架。
# ai_auto_test

## 19. 当前项目已落地的 MVP 框架

当前项目已经按“通用 Skill 生命周期”搭建了首版可运行骨架，默认链路为：

```text
读取 case -> 读取 Skill 配置 -> 校验前置参数 -> setup 初始化 -> 执行 Skill -> 统一评估 -> pytest / Allure 报告
```

接口调用层当前使用 `requests`，不再使用 `httpx`。如果某个 Skill 还没有真实 HTTP 入口，可以先把 `base_url` 配成 `sample://...`，框架会读取评测集中的“真实返回举例”做离线评估。

### 19.1 已落地目录

```text
config/
├── settings.py
└── skills/
    └── demo_skill.yaml
core/
├── client.py
├── evaluator.py
├── loader.py
├── models.py
├── setup_manager.py
└── skill_manager.py
evaluators/
├── exact_match.py
├── keyword_match.py
├── regex_match.py
├── semantic_similarity.py
├── llm_judge.py
├── retrieval_check.py
└── tool_call_check.py
data/
└── skill_cases.json
testcases/
├── test_skill_smoke.py
├── test_skill_regression.py
└── test_skill_routing.py
```

### 19.2 本地运行

安装依赖：

```bash
venv/bin/python -m pip install -r requirements.txt
```

运行全部测试：

```bash
venv/bin/python -m pytest
```

只运行冒烟：

```bash
venv/bin/python -m pytest -m smoke
```

使用外部 CSV 评测集：

```bash
AI_TEST_CASE_FILE="临时添加的文件，仅供参考/核心能力测试评测集 - 评测集.csv" venv/bin/python -m pytest -m smoke
```

这类 CSV 支持以下中文字段自动映射：

- `skill` -> `skill_name`
- `input` -> `question`
- `预期的返回（部分关键信息）` -> `expected_answer`
- `真实返回举例（ArkClaw）` -> `actual_response`
- `rule` -> `rule`

生成 Allure 结果：

```bash
venv/bin/python run.py --allure
```

打开 Allure 报告（需要先安装 Allure CLI）：

```bash
brew install allure
allure serve reports/allure-results
```

或生成静态报告目录：

```bash
allure generate reports/allure-results -o reports/allure-report --clean
allure open reports/allure-report
```

### 19.3 新 Skill 接入方式

新增一个 Skill 时，优先只改三类文件：

1. 在根目录 `skills/<skill_name>/` 下放 Skill 代码、脚本和说明文档
2. 在 `config/skills/` 下新增一份 Skill 配置，例如 `report_query.yaml`
3. 在 `data/` 下增加该 Skill 的测试 case 文件

推荐目录规范：

```text
skills/
  <skill_name>/
    scripts/
    README.md
    SKILL.md
config/skills/
  <skill_name>.yaml
data/
  <skill_name>_cases.csv
```

其中 `config/临时添加的文件，仅供参考/` 不参与框架加载，真正生效的只有 `config/skills/`。

如果新 Skill 有特殊初始化动作，再扩展 `core/setup_manager.py`。

如果新 Skill 需要新的判断方式，再扩展 `evaluators/`，并在 `core/evaluator.py` 中注册策略。
