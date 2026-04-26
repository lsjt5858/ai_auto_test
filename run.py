from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Run AI automation tests.")
    parser.add_argument("-m", "--marker", help="pytest marker, for example: smoke or regression")
    parser.add_argument("--case-file", help="case file path, csv or json")
    parser.add_argument("--case-dir", help="case directory path; all csv/json files will be loaded")
    parser.add_argument("--runtime-params", help="runtime params json file, for login and skill connection params")
    parser.add_argument("--allure", action="store_true", help="write Allure results to reports/allure-results")
    parser.add_argument("--allure-report", nargs="?", const="reports/allure-report", help="generate Allure HTML report when allure CLI is installed")
    parser.add_argument("--html-report", nargs="?", const="reports/skill_report.html", help="write a directly viewable HTML report")
    parser.add_argument("--junitxml", default="", help="junit xml output path")
    parser.add_argument("--report-title", default="Skill Automation Report", help="HTML report title")
    args = parser.parse_args()

    import os

    env = os.environ.copy()
    if args.case_file:
        env["AI_TEST_CASE_FILE"] = args.case_file
    if args.case_dir:
        env["AI_TEST_CASE_DIR"] = args.case_dir
    if args.runtime_params:
        env["AI_TEST_RUNTIME_PARAMS_FILE"] = args.runtime_params

    case_results = "reports/current/case_results.jsonl"
    env["AI_TEST_CASE_RESULTS_FILE"] = case_results

    cmd = [sys.executable, "-m", "pytest"]
    if args.marker:
        cmd.extend(["-m", args.marker])
    if args.allure or args.allure_report:
        cmd.extend(["--alluredir", "reports/allure-results"])
    junitxml = args.junitxml or ("reports/current/junit.xml" if args.html_report else "")
    if junitxml:
        Path(junitxml).parent.mkdir(parents=True, exist_ok=True)
        cmd.extend(["--junitxml", junitxml])

    code = subprocess.call(cmd, env=env)
    if args.html_report:
        subprocess.call(
            [
                sys.executable,
                "tools/skill_report.py",
                case_results,
                junitxml,
                args.html_report,
                args.report_title,
            ]
        )
    if args.allure_report:
        allure_bin = shutil.which("allure")
        if allure_bin:
            subprocess.call([allure_bin, "generate", "reports/allure-results", "-o", args.allure_report, "--clean"])
        else:
            print("Allure CLI not found. Install Allure CLI to generate the full Allure UI report.", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
