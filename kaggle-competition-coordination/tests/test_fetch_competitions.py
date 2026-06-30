"""Behavior test for scripts/fetch_competitions.py.

With KAGGLE creds present: runs the script against the fixture and asserts
result.json carries a competitions[] list. Without creds: verifies the
no-credentials guard exits non-zero with a clear message, then skips.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "scripts", "fetch_competitions.py")
FIXTURE = os.path.join(HERE, "fixtures", "fetch_competitions.input.json")


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
    with tempfile.TemporaryDirectory() as tmp:
        if not has_creds:
            proc = _run_script(tmp, {"KAGGLE_USERNAME": "", "KAGGLE_KEY": ""})
            if proc.returncode == 1 and "KAGGLE_USERNAME or KAGGLE_KEY missing" in proc.stderr:
                return "skip: needs KAGGLE_USERNAME + KAGGLE_KEY (guard path verified)"
            return f"fail: guard path rc={proc.returncode} stderr={proc.stderr.strip()}"
        proc = _run_script(tmp, {})
        if proc.returncode != 0:
            return f"fail: rc={proc.returncode} stderr={proc.stderr.strip()}"
        with open(os.path.join(tmp, "result.json"), encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data.get("competitions"), list):
            return "fail: result.json missing competitions[]"
        return f"pass: competitions[] present ({len(data['competitions'])} items)"


if __name__ == "__main__":
    print(run())
