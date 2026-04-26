# 测试报告

当前项目支持两种报告。

## 1. 直接可打开的 HTML 报告

这是当前默认推荐方式，不依赖外部 Allure CLI。

执行示例：

```bash
venv/bin/python run.py \
  --case-file data/byted_bytehouse_ai_query_local_script_cases.csv \
  --runtime-params "临时添加的文件，仅供参考/account.md" \
  -m smoke \
  --html-report reports/local_script_report.html \
  --report-title "Local Script Test Report"
```

报告路径：

```text
reports/local_script_report.html
```

报告包含：

```text
总用例数
通过率
按 Skill 汇总的 suites
每条 case 的 input
实际输出
断言结果
执行命令
失败原因
```

敏感字段会自动脱敏，例如：

```text
PASSWORD
TOKEN
SECRET
API_KEY
AUTHORIZATION
```

## 2. Allure 报告

项目已经接入 `allure-pytest`，可以生成 Allure 原始结果：

```bash
venv/bin/python run.py \
  --case-file data/byted_bytehouse_ai_query_local_script_cases.csv \
  --runtime-params "临时添加的文件，仅供参考/account.md" \
  -m smoke \
  --allure
```

原始结果目录：

```text
reports/allure-results
```

如果本机安装了 Allure CLI，可以直接生成完整 Allure HTML：

```bash
venv/bin/python run.py \
  --case-file data/byted_bytehouse_ai_query_local_script_cases.csv \
  --runtime-params "临时添加的文件，仅供参考/account.md" \
  -m smoke \
  --allure-report reports/allure-report
```

当前本机没有检测到 `allure` 命令，所以完整 Allure UI 需要额外安装 Allure CLI。

