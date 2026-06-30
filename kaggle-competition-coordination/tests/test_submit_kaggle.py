"""Behavior test for scripts/submit_kaggle.py.

A real submission needs KAGGLE creds, a competition you have joined, and a
reachable predictions file URL, so the full path is gated behind
TEST_KAGGLE_SUBMIT=1. Without creds: verifies the no-credentials guard exits
non-zero with a clear message, then skips.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "scripts", "submit_kaggle.py")
FIXTURE = os.path.join(HERE, "fixtures", "submit_kaggle.input.json")


def _run_script(tmp, extra_env):
    shutil.copy(FIXTURE, os.path.join(tmp, "input.json"))
    env = dict(os.environ)
    env.update(extra_env)
    env["OUTPUT_DIR"] = tmp
    return subprocess.run(
        [sys.executable, SCRIPT], capture_output=True, text=True, env=env
    )


def run():
    has_creds = os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY")
    wants_live = os.environ.get("TEST_KAGGLE_SUBMIT") == "1"
    with tempfile.TemporaryDirectory() as tmp:
        if not has_creds:
            proc = _run_script(tmp, {"KAGGLE_USERNAME": "", "KAGGLE_KEY": ""})
            if proc.returncode == 1 and "KAGGLE_USERNAME or KAGGLE_KEY missing" in proc.stderr:
                return "skip: needs KAGGLE_USERNAME + KAGGLE_KEY (guard path verified)"
            return f"fail: guard path rc={proc.returncode} stderr={proc.stderr.strip()}"
        if not wants_live:
            return "skip: needs TEST_KAGGLE_SUBMIT=1 + a joined competition + reachable submissionFileUrl"
        proc = _run_script(tmp, {})
        if proc.returncode != 0:
            return f"fail: rc={proc.returncode} stderr={proc.stderr.strip()}"
        with open(os.path.join(tmp, "result.json"), encoding="utf-8") as handle:
            data = json.load(handle)
        if "competitionRef" not in data or "publicScore" not in data:
            return "fail: result.json missing competitionRef/publicScore"
        return f"pass: submitted, publicScore={data.get('publicScore')}"


if __name__ == "__main__":
    print(run())
