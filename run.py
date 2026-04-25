from __future__ import annotations

import argparse
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Run AI automation tests.")
    parser.add_argument("-m", "--marker", help="pytest marker, for example: smoke or regression")
    parser.add_argument("--allure", action="store_true", help="write Allure results to reports/allure-results")
    args = parser.parse_args()

    cmd = [sys.executable, "-m", "pytest"]
    if args.marker:
        cmd.extend(["-m", args.marker])
    if args.allure:
        cmd.extend(["--alluredir", "reports/allure-results"])

    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())

