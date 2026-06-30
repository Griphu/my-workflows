import json
import os
import sys


def main():
    with open("/output/input.json") as handle:
        data = json.load(handle)

    hint = data.get("competitionHint") or ""

    if not os.environ.get("KAGGLE_USERNAME") or not os.environ.get("KAGGLE_KEY"):
        print("KAGGLE_USERNAME or KAGGLE_KEY missing", file=sys.stderr)
        sys.exit(1)

    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()

    kwargs = {"sort_by": "latestDeadline"}
    if hint:
        kwargs["search"] = hint
    competitions_raw = api.competitions_list(**kwargs)

    competitions = []
    for competition in competitions_raw:
        competitions.append(
            {
                "ref": getattr(competition, "ref", None) or str(competition),
                "title": getattr(competition, "title", ""),
                "deadline": str(getattr(competition, "deadline", "")),
                "category": getattr(competition, "category", ""),
                "reward": getattr(competition, "reward", ""),
                "description": getattr(competition, "description", ""),
            }
        )

    with open("/output/result.json", "w") as handle:
        json.dump({"competitions": competitions, "count": len(competitions)}, handle)
    print(f'Fetched {len(competitions)} competitions (hint="{hint}")')


if __name__ == "__main__":
    main()
