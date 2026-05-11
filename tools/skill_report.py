from __future__ import annotations

import html
import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


def main() -> int:
    if len(sys.argv) < 4:
        print("Usage: python tools/skill_report.py <case_results.jsonl> <junit.xml> <report.html> [title]", file=sys.stderr)
        return 2
    case_results = Path(sys.argv[1])
    junit_path = Path(sys.argv[2])
    report_path = Path(sys.argv[3])
    title = sys.argv[4] if len(sys.argv) > 4 else "Skill Automation Report"

    records = _load_records(case_results)
    junit_status = _load_junit_status(junit_path)
    for record in records:
        record["status"] = junit_status.get(record["case_id"], _status_from_evaluation(record))

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_render(title, records), encoding="utf-8")
    return 0


def _load_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _load_junit_status(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    statuses: dict[str, str] = {}
    for suite in suites:
        for case in suite.findall("testcase"):
            name = case.attrib.get("name", "")
            case_id = _case_id_from_pytest_name(name)
            if case.find("failure") is not None or case.find("error") is not None:
                statuses[case_id] = "failed"
            elif case.find("skipped") is not None:
                statuses[case_id] = "skipped"
            else:
                statuses[case_id] = "passed"
    return statuses


def _case_id_from_pytest_name(name: str) -> str:
    if "[" in name and name.endswith("]"):
        return name.rsplit("[", 1)[1][:-1]
    return name


def _status_from_evaluation(record: dict[str, Any]) -> str:
    evaluation = record.get("evaluation", {})
    return "passed" if evaluation.get("passed") else "failed"


def _render(title: str, records: list[dict[str, Any]]) -> str:
    total = len(records)
    counts = Counter(record.get("status", "unknown") for record in records)
    passed = counts.get("passed", 0)
    failed = counts.get("failed", 0)
    skipped = counts.get("skipped", 0)
    pass_rate = (passed / total * 100) if total else 0
    by_suite = defaultdict(Counter)
    for record in records:
        suite = record.get("skill_name") or "unknown"
        by_suite[suite][record.get("status", "unknown")] += 1

    suite_rows = "\n".join(_suite_row(name, counter) for name, counter in sorted(by_suite.items()))
    case_rows = "\n".join(_case_row(record, index) for index, record in enumerate(records, 1))
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>{_e(title)}</title>
  <style>
    :root {{ --green:#78c943; --red:#e25544; --gray:#a3a3a3; --dark:#303030; --blue:#2477bd; --amber:#f7b955; }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif; color:#222; background:#fff; }}
    aside {{ position:fixed; left:0; top:0; bottom:0; width:230px; background:#303030; color:#fff; padding:24px 22px; }}
    aside h1 {{ font-size:34px; margin:0 0 40px; }}
    aside nav div {{ padding:14px 0; color:#d6d6d6; font-size:17px; }}
    main {{ margin-left:230px; padding:30px; }}
    .grid {{ display:grid; grid-template-columns: minmax(580px, 1fr) minmax(360px, 0.7fr); gap:22px; }}
    .panel {{ border:1px solid #ddd; background:#fff; }}
    .overview {{ height:270px; display:flex; align-items:center; justify-content:space-around; }}
    .title {{ font-size:30px; margin-bottom:6px; }}
    .muted {{ color:#888; }}
    .total {{ text-align:center; }}
    .total .num {{ font-size:64px; line-height:1; }}
    .donut {{ width:178px; height:178px; border-radius:50%; background:conic-gradient(var(--green) 0 {pass_rate:.2f}%, #aaa {pass_rate:.2f}% 100%); display:flex; align-items:center; justify-content:center; }}
    .donut span {{ background:white; width:126px; height:126px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:32px; }}
    .section-title {{ font-size:28px; padding:22px; border-bottom:1px solid #eee; }}
    .suite {{ display:grid; grid-template-columns: 1fr 420px; gap:20px; align-items:center; padding:14px 22px; border-bottom:1px solid #eee; }}
    .bar {{ height:24px; display:flex; background:#eee; border-radius:4px; overflow:hidden; }}
    .passbar {{ background:var(--green); color:#fff; text-align:center; font-weight:600; }}
    .failbar {{ background:#aaa; color:#fff; text-align:center; font-weight:600; }}
    table {{ width:100%; border-collapse:collapse; margin-top:22px; }}
    th,td {{ border:1px solid #e6e6e6; padding:10px; vertical-align:top; text-align:left; }}
    th {{ background:#f7f7f7; }}
    .status-passed {{ color:#087f4f; font-weight:700; }}
    .status-failed {{ color:#b42318; font-weight:700; }}
    .status-skipped {{ color:#7a5d00; font-weight:700; }}
    .badge {{ display:inline-block; padding:3px 8px; border-radius:999px; font-size:12px; font-weight:700; color:#fff; }}
    .badge-passed {{ background:var(--green); }}
    .badge-failed {{ background:var(--red); }}
    .badge-skipped {{ background:var(--amber); }}
    .badge-unknown {{ background:var(--gray); }}
    details summary {{ cursor:pointer; color:#1f5e9d; font-weight:600; }}
    pre {{ white-space:pre-wrap; max-height:360px; overflow:auto; margin:8px 0 0; background:#fafafa; padding:10px; border:1px solid #eee; }}
    .sidepanel {{ height:270px; display:flex; align-items:center; justify-content:center; color:#777; font-size:20px; }}
    .case-card {{ background:#fcfcfc; border:1px solid #eee; margin-top:12px; padding:14px; }}
    .case-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:12px; }}
    .case-block {{ border:1px solid #e8e8e8; background:#fff; padding:12px; }}
    .case-block h4 {{ margin:0 0 8px; font-size:14px; color:#555; }}
    .case-text {{ white-space:pre-wrap; max-height:260px; overflow:auto; line-height:1.55; }}
    .reason {{ margin-top:10px; padding:10px; border-left:4px solid #ddd; background:#fff; }}
    .reason.failed {{ border-left-color:var(--red); }}
    .reason.passed {{ border-left-color:var(--green); }}
    .assertions {{ margin-top:12px; }}
    .assertions table {{ margin-top:8px; }}
    .mini {{ font-size:12px; color:#777; }}
    .mono {{ font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }}
    .input-preview,.output-preview {{ max-width:420px; max-height:96px; overflow:hidden; white-space:pre-wrap; line-height:1.45; }}
  </style>
</head>
<body>
  <aside>
    <h1>Skill Report</h1>
    <nav>
      <div>Overview</div>
      <div>Suites</div>
      <div>Cases</div>
      <div>Details</div>
    </nav>
  </aside>
  <main>
    <div class="grid">
      <section class="panel overview">
        <div>
          <div class="title">{_e(title)}</div>
          <div class="muted">{_e(generated_at)}</div>
          <div class="total"><div class="num">{total}</div><div class="muted">test cases</div></div>
        </div>
        <div class="donut"><span>{pass_rate:.2f}%</span></div>
      </section>
      <section class="panel sidepanel">TREND: history can be added later</section>
    </div>
    <section class="panel" style="margin-top:22px;">
      <div class="section-title">SUITES <span class="muted">{len(by_suite)} items total · passed {passed} · failed {failed} · skipped {skipped}</span></div>
      {suite_rows}
    </section>
    <section class="panel" style="margin-top:22px; padding:22px;">
      <div class="section-title" style="padding:0 0 16px;">CASE DETAILS</div>
      <table>
        <thead><tr><th>Status</th><th>Case ID</th><th>Skill</th><th>Input</th><th>Output</th><th>Score</th><th>Pass 判断</th><th>Details</th></tr></thead>
        <tbody>{case_rows}</tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""


def _suite_row(name: str, counter: Counter) -> str:
    passed = counter.get("passed", 0)
    failed = counter.get("failed", 0)
    total = sum(counter.values()) or 1
    pass_width = passed / total * 100
    fail_width = failed / total * 100
    return f"""<div class="suite">
      <div>{_e(name)}</div>
      <div class="bar"><div class="passbar" style="width:{pass_width:.2f}%">{passed or ""}</div><div class="failbar" style="width:{fail_width:.2f}%">{failed or ""}</div></div>
    </div>"""


def _case_row(record: dict[str, Any], index: int) -> str:
    status = record.get("status", "unknown")
    evaluation = record.get("evaluation", {})
    response = record.get("response", {})
    actual_answer = response.get("answer", "")
    expected_answer = record.get("expected_answer", "")
    reason = evaluation.get("reason", "")
    assertions = evaluation.get("assertions", [])
    raw_detail = {
        "case_id": record.get("case_id"),
        "status": status,
        "input": record.get("question"),
        "expected_answer": expected_answer,
        "actual_answer": actual_answer,
        "evaluation": evaluation,
        "context": record.get("context"),
        "raw_case": record.get("raw_case"),
        "response_raw": response.get("raw", {}),
    }
    score = evaluation.get("score", "")
    if isinstance(score, float):
        score = f"{score:.2f}"
    threshold = record.get("score_threshold", "")
    status_badge = f'<span class="badge badge-{_e(status)}">{_e(status)}</span>'
    details_html = _case_detail_html(record, actual_answer, expected_answer, assertions, reason, raw_detail, status)
    return f"""<tr>
      <td class="status-{_e(status)}">{status_badge}</td>
      <td>{_e(record.get("case_id", ""))}</td>
      <td>{_e(record.get("skill_name", ""))}<br><span class="muted">{_e(record.get("execute_mode", ""))}</span></td>
      <td><div class="input-preview">{_e(record.get("question", ""))}</div></td>
      <td><div class="output-preview">{_e(_short(actual_answer, 360))}</div></td>
      <td><span class="mono">{_e(str(score))}</span><br><span class="mini">threshold: {_e(str(threshold))}</span></td>
      <td>{_e(_short(reason or ("passed" if status == "passed" else ""), 260))}</td>
      <td><details><summary>查看详情</summary>{details_html}</details></td>
    </tr>"""


def _case_detail_html(
    record: dict[str, Any],
    actual_answer: Any,
    expected_answer: Any,
    assertions: list[dict[str, Any]],
    reason: Any,
    raw_detail: dict[str, Any],
    status: str,
) -> str:
    assertion_rows = "\n".join(_assertion_row(item) for item in assertions) or "<tr><td colspan=\"4\">无断言明细</td></tr>"
    command = record.get("response", {}).get("raw", {}).get("command", "")
    context = record.get("context", {})
    return f"""
      <div class="case-card">
        <div><b>Case:</b> {_e(record.get("case_id", ""))} · <b>Assert:</b> {_e(record.get("assert_type", ""))}</div>
        <div class="reason {_e(status)}"><b>通过/失败依据：</b>{_e(reason or ("passed" if status == "passed" else ""))}</div>
        <div class="case-grid">
          <div class="case-block">
            <h4>输入 Input</h4>
            <div class="case-text">{_e(record.get("question", ""))}</div>
          </div>
          <div class="case-block">
            <h4>期望 Expected</h4>
            <div class="case-text">{_e(expected_answer)}</div>
          </div>
          <div class="case-block">
            <h4>实际输出 Actual</h4>
            <div class="case-text">{_e(actual_answer)}</div>
          </div>
          <div class="case-block">
            <h4>执行上下文 Context</h4>
            <pre>{_e(json.dumps(context, ensure_ascii=False, indent=2, default=str))}</pre>
          </div>
        </div>
        <div class="assertions">
          <b>断言明细 Assertions</b>
          <table>
            <thead><tr><th>Type</th><th>Passed</th><th>Score</th><th>Detail</th></tr></thead>
            <tbody>{assertion_rows}</tbody>
          </table>
        </div>
        <div class="case-grid">
          <div class="case-block">
            <h4>执行命令 Command</h4>
            <pre>{_e(json.dumps(command, ensure_ascii=False, indent=2, default=str))}</pre>
          </div>
          <div class="case-block">
            <h4>原始明细 Raw Detail</h4>
            <pre>{_e(json.dumps(raw_detail, ensure_ascii=False, indent=2, default=str))}</pre>
          </div>
        </div>
      </div>
    """


def _assertion_row(item: dict[str, Any]) -> str:
    score = item.get("score", "")
    if isinstance(score, float):
        score = f"{score:.2f}"
    passed = item.get("passed")
    status = "passed" if passed else "failed"
    return f"""<tr>
      <td>{_e(item.get("type", ""))}</td>
      <td><span class="badge badge-{status}">{_e(status)}</span></td>
      <td class="mono">{_e(str(score))}</td>
      <td>{_e(item.get("detail", ""))}</td>
    </tr>"""


def _short(value: Any, limit: int) -> str:
    text = str(value or "")
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def _e(value: Any) -> str:
    return html.escape(str(value or ""))


if __name__ == "__main__":
    raise SystemExit(main())
