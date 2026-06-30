#!/usr/bin/env python3
"""Fetch active Kaggle competitions and write them to result.json.

Reads (optional) filters from input.json - none are required today; the file is
read so future filters (category, search term) can be added without changing the
step contract. Requires KAGGLE_USERNAME and KAGGLE_KEY in the environment.

Output contract (result.json):
  {
    "competitions": [
      { "ref", "title", "category", "deadline", "tags", "description", "reward" }
    ],
    "summary": "<one line>"
  }
"""
import json
import os
import sys

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/output")
INPUT_PATH = os.path.join(OUTPUT_DIR, "input.json")
RESULT_PATH = os.path.join(OUTPUT_DIR, "result.json")


def load_input():
    try:
        with open(INPUT_PATH, encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return {}


def main():
    if not os.environ.get("KAGGLE_USERNAME") or not os.environ.get("KAGGLE_KEY"):
        print("KAGGLE_USERNAME or KAGGLE_KEY missing", file=sys.stderr)
        return 1

    load_input()  # reserved for future filters

    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()

    competitions = []
    for comp in api.competitions_list():
        deadline = getattr(comp, "deadline", "")
        competitions.append(
            {
                "ref": getattr(comp, "ref", None),
                "title": getattr(comp, "title", None),
                "category": getattr(comp, "category", None),
                "deadline": str(deadline) if deadline else None,
                "tags": [str(tag) for tag in (getattr(comp, "tags", None) or [])],
                "description": getattr(comp, "description", None),
                "reward": getattr(comp, "reward", None),
            }
        )

    result = {
        "competitions": competitions,
        "summary": f"Fetched {len(competitions)} active competition(s)",
    }
    with open(RESULT_PATH, "w", encoding="utf-8") as handle:
        json.dump(result, handle)
    print(result["summary"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
