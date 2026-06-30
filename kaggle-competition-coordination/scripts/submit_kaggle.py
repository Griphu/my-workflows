#!/usr/bin/env python3
"""Submit a predictions file to Kaggle and read back the public score.

Reads input.json:
  steps.lead_pick.ref                         -> competition ref
  steps.provide_submission.submissionFileUrl  -> direct download URL to CSV
  steps.provide_submission.submissionMessage  -> submission message (optional)
Requires KAGGLE_USERNAME and KAGGLE_KEY in the environment.

Output contract (result.json):
  { "competitionRef", "publicScore", "status", "submittedAt", "message", "summary" }
"""
import json
import os
import sys
import time
import urllib.request

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/output")
INPUT_PATH = os.path.join(OUTPUT_DIR, "input.json")
RESULT_PATH = os.path.join(OUTPUT_DIR, "result.json")

POLL_ATTEMPTS = 10
POLL_INTERVAL_SECONDS = 6


def get_path(data, dotted):
    cur = data
    for key in dotted.split("."):
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    return cur


def main():
    if not os.environ.get("KAGGLE_USERNAME") or not os.environ.get("KAGGLE_KEY"):
        print("KAGGLE_USERNAME or KAGGLE_KEY missing", file=sys.stderr)
        return 1

    with open(INPUT_PATH, encoding="utf-8") as handle:
        data = json.load(handle)

    competition_ref = get_path(data, "steps.lead_pick.ref")
    file_url = get_path(data, "steps.provide_submission.submissionFileUrl")
    message = get_path(data, "steps.provide_submission.submissionMessage") or "Submitted via Mediforce"
    if not competition_ref or not file_url:
        print("competition ref or submissionFileUrl missing from input", file=sys.stderr)
        return 1

    submission_path = os.path.join(OUTPUT_DIR, "submission.csv")
    urllib.request.urlretrieve(file_url, submission_path)

    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()
    api.competition_submit(submission_path, message, competition_ref)

    public_score = None
    status = "submitted"
    submitted_at = None
    for _ in range(POLL_ATTEMPTS):
        time.sleep(POLL_INTERVAL_SECONDS)
        submissions = api.competition_submissions(competition_ref)
        if not submissions:
            continue
        latest = submissions[0]
        status = str(getattr(latest, "status", "submitted"))
        date = getattr(latest, "date", "")
        submitted_at = str(date) if date else None
        score = getattr(latest, "publicScore", None)
        if score:
            public_score = str(score)
            break
        if status.lower() in ("error", "complete"):
            break

    result = {
        "competitionRef": competition_ref,
        "publicScore": public_score,
        "status": status,
        "submittedAt": submitted_at,
        "message": message,
        "summary": f"Submitted to {competition_ref}; public score {public_score}",
    }
    with open(RESULT_PATH, "w", encoding="utf-8") as handle:
        json.dump(result, handle)
    print(result["summary"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
