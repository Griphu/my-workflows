import json
import sys
from datetime import datetime, timedelta, timezone


def main():
    with open("/output/input.json") as handle:
        data = json.load(handle)

    steps = data.get("steps", {})
    rows = (steps.get("select_members") or {}).get("rows", [])
    fetched = (steps.get("fetch_members") or {}).get("options", [])

    included = {
        row.get("itemId")
        for row in rows
        if (row.get("values") or {}).get("include") == "yes"
    }
    team_members = [
        {"userId": member["id"], "email": member.get("email", "")}
        for member in fetched
        if member.get("id") in included
    ]
    if not team_members:
        print("No members selected", file=sys.stderr)
        sys.exit(1)

    hours = data.get("profileDurationHours")
    try:
        hours = float(hours)
    except (TypeError, ValueError):
        print("profileDurationHours must be a number", file=sys.stderr)
        sys.exit(1)
    if hours <= 0:
        print("profileDurationHours must be positive", file=sys.stderr)
        sys.exit(1)

    deadline = (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()

    with open("/output/result.json", "w") as handle:
        json.dump({"teamMembers": team_members, "deadline": deadline}, handle)
    print(f"Selected {len(team_members)} member(s), deadline {deadline}")


if __name__ == "__main__":
    main()
