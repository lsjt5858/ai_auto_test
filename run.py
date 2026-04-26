from __future__ import annotations

import argparse
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Run AI automation tests.")
    parser.add_argument("-m", "--marker", help="pytest marker, for example: smoke or regression")
    parser.add_argument("--case-file", help="case file path, csv or json")
    parser.add_argument("--case-dir", help="case directory path; all csv/json files will be loaded")
    parser.add_argument("--runtime-params", help="runtime params json file, for login and skill connection params")
    parser.add_argument("--allure", action="store_true", help="write Allure results to reports/allure-results")
    args = parser.parse_args()

    env = None
    if args.case_file or args.case_dir or args.runtime_params:
        import os

        env = os.environ.copy()
        if args.case_file:
            env["AI_TEST_CASE_FILE"] = args.case_file
        if args.case_dir:
            env["AI_TEST_CASE_DIR"] = args.case_dir
        if args.runtime_params:
            env["AI_TEST_RUNTIME_PARAMS_FILE"] = args.runtime_params

    cmd = [sys.executable, "-m", "pytest"]
    if args.marker:
        cmd.extend(["-m", args.marker])
    if args.allure:
        cmd.extend(["--alluredir", "reports/allure-results"])

    return subprocess.call(cmd, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
