from __future__ import annotations

import html
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: python tools/junit_to_html.py <junit.xml> <report.html> [title]", file=sys.stderr)
        return 2

    junit_path = Path(sys.argv[1])
    report_path = Path(sys.argv[2])
    title = sys.argv[3] if len(sys.argv) > 3 else "Skill Automation Test Report"

    tree = ET.parse(junit_path)
    root = tree.getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    cases = []
    total = failures = errors = skipped = 0
    elapsed = 0.0

    for suite in suites:
        total += int(suite.attrib.get("tests", 0))
        failures += int(suite.attrib.get("failures", 0))
        errors += int(suite.attrib.get("errors", 0))
        skipped += int(suite.attrib.get("skipped", 0))
        elapsed += float(suite.attrib.get("time", 0.0))
        for case in suite.findall("testcase"):
            status = "passed"
            detail = ""
            failure_node = case.find("failure")
            error_node = case.find("error")
            skipped_node = case.find("skipped")
            if failure_node is not None:
                status = "failed"
                detail = failure_node.attrib.get("message", "") or failure_node.text or ""
            elif error_node is not None:
                status = "error"
                detail = error_node.attrib.get("message", "") or error_node.text or ""
            elif skipped_node is not None:
                status = "skipped"
                detail = skipped_node.attrib.get("message", "") or skipped_node.text or ""
            cases.append(
                {
                    "name": case.attrib.get("name", ""),
                    "classname": case.attrib.get("classname", ""),
                    "time": float(case.attrib.get("time", 0.0)),
                    "status": status,
                    "detail": detail,
                }
            )

    passed = total - failures - errors - skipped
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_render(title, total, passed, failures, errors, skipped, elapsed, cases), encoding="utf-8")
    return 0


def _render(title: str, total: int, passed: int, failures: int, errors: int, skipped: int, elapsed: float, cases: list[dict]) -> str:
    rows = "\n".join(
        f"""
        <tr class="{html.escape(case['status'])}">
          <td>{html.escape(case['status'])}</td>
          <td>{html.escape(case['classname'])}</td>
          <td>{html.escape(case['name'])}</td>
          <td>{case['time']:.3f}s</td>
          <td><pre>{html.escape(case['detail'])}</pre></td>
        </tr>
        """
        for case in cases
    )
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #1f2937; }}
    h1 {{ margin-bottom: 4px; }}
    .meta {{ color: #6b7280; margin-bottom: 24px; }}
    .summary {{ display: flex; gap: 12px; margin-bottom: 24px; flex-wrap: wrap; }}
    .card {{ border: 1px solid #d1d5db; border-radius: 8px; padding: 12px 16px; min-width: 110px; }}
    .value {{ font-size: 28px; font-weight: 700; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #e5e7eb; padding: 8px; vertical-align: top; text-align: left; }}
    th {{ background: #f9fafb; }}
    tr.passed td:first-child {{ color: #047857; font-weight: 700; }}
    tr.failed td:first-child, tr.error td:first-child {{ color: #b91c1c; font-weight: 700; }}
    tr.skipped td:first-child {{ color: #92400e; font-weight: 700; }}
    pre {{ white-space: pre-wrap; margin: 0; max-height: 240px; overflow: auto; }}
  </style>
</head>
<body>
  <h1>{html.escape(title)}</h1>
  <div class="meta">Generated at {html.escape(generated_at)} · elapsed {elapsed:.3f}s</div>
  <div class="summary">
    <div class="card"><div>Total</div><div class="value">{total}</div></div>
    <div class="card"><div>Passed</div><div class="value">{passed}</div></div>
    <div class="card"><div>Failed</div><div class="value">{failures}</div></div>
    <div class="card"><div>Errors</div><div class="value">{errors}</div></div>
    <div class="card"><div>Skipped</div><div class="value">{skipped}</div></div>
  </div>
  <table>
    <thead><tr><th>Status</th><th>Class</th><th>Case</th><th>Time</th><th>Detail</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</body>
</html>
"""


if __name__ == "__main__":
    raise SystemExit(main())
