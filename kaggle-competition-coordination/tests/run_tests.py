#!/usr/bin/env python3
"""Run every test_*.py in this folder. Skips (does not fail) tests whose
required secrets/env are absent. Exits non-zero only on a real failure.

Usage:
  python tests/run_tests.py
  KAGGLE_USERNAME=... KAGGLE_KEY=... python tests/run_tests.py
  KAGGLE_USERNAME=... KAGGLE_KEY=... TEST_KAGGLE_SUBMIT=1 python tests/run_tests.py
"""
import glob
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(path):
    spec = importlib.util.spec_from_file_location(os.path.basename(path)[:-3], path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    results = []
    for path in sorted(glob.glob(os.path.join(HERE, "test_*.py"))):
        name = os.path.basename(path)
        try:
            status = _load(path).run()
        except Exception as exc:  # noqa: BLE001 - report any crash as a failure
            status = f"fail: {exc}"
        print(f"{name}: {status}")
        results.append(status)

    counts = {kind: sum(1 for r in results if r.startswith(kind)) for kind in ("pass", "skip", "fail")}
    print(f"\n{len(results)} test(s): pass {counts['pass']}, skip {counts['skip']}, fail {counts['fail']}")
    return 1 if counts["fail"] else 0


if __name__ == "__main__":
    sys.exit(main())
