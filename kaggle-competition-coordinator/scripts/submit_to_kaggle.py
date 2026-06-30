import json
import os
import sys
import time


def find_submission_file(data):
    step = (data.get("steps") or {}).get("provide_submission") or {}
    candidates = []
    for key in ("filePath", "path", "file"):
        if step.get(key):
            candidates.append(step[key])
    for uploaded in step.get("files") or step.get("uploads") or []:
        if isinstance(uploaded, str):
            candidates.append(uploaded)
        elif isinstance(uploaded, dict):
            for key in ("path", "localPath", "name"):
                if uploaded.get(key):
                    candidates.append(uploaded[key])
    env_path = os.environ.get("SUBMISSION_FILE")
    if env_path:
        candidates.append(env_path)
    candidates += ["/output/submission.csv", "/workspace/submission.csv"]
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate
    return None


def main():
    with open("/output/input.json") as handle:
        data = json.load(handle)

    competition = (data.get("steps") or {}).get("review_competitions") or {}
    ref = competition.get("competitionRef") or competition.get("ref")
    if not ref:
        print("selected competition ref missing", file=sys.stderr)
        sys.exit(1)

    if not os.environ.get("KAGGLE_USERNAME") or not os.environ.get("KAGGLE_KEY"):
        print("KAGGLE_USERNAME or KAGGLE_KEY missing", file=sys.stderr)
        sys.exit(1)

    submission_file = find_submission_file(data)
    if not submission_file:
        print(
            "Submission file not found. Set SUBMISSION_FILE or place it at "
            "/output/submission.csv",
            file=sys.stderr,
        )
        sys.exit(1)

    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()

    message = (competition.get("title") or ref) + " — submitted via Mediforce"
    api.competition_submit(submission_file, message, ref)
    print(f"Submitted {submission_file} to {ref}; polling for score...")

    poll_seconds = int(os.environ.get("KAGGLE_POLL_SECONDS", "600"))
    interval = int(os.environ.get("KAGGLE_POLL_INTERVAL", "20"))
    deadline = time.time() + poll_seconds
    scored = None
    while time.time() < deadline:
        submissions = api.competition_submissions(ref)
        if submissions:
            latest = submissions[0]
            public_score = getattr(latest, "publicScore", None)
            if public_score not in (None, ""):
                scored = {
                    "publicScore": str(public_score),
                    "privateScore": str(getattr(latest, "privateScore", "") or ""),
                    "status": str(getattr(latest, "status", "")),
                    "fileName": getattr(latest, "fileName", ""),
                }
                break
        time.sleep(interval)

    if scored is None:
        result = {
            "submitted": True,
            "competitionRef": ref,
            "scored": False,
            "message": f"Submission accepted but not scored within {poll_seconds}s",
        }
    else:
        result = {"submitted": True, "competitionRef": ref, "scored": True, **scored}

    with open("/output/result.json", "w") as handle:
        json.dump(result, handle)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
