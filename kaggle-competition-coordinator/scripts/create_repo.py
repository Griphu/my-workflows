import json
import os
import re
import sys

import requests


def main():
    with open("/output/input.json") as handle:
        data = json.load(handle)

    owner = data.get("githubOwner")
    competition = (data.get("steps") or {}).get("review_competitions") or {}
    ref = competition.get("competitionRef") or competition.get("ref")
    if not owner or not ref:
        print("githubOwner or selected competition ref missing", file=sys.stderr)
        sys.exit(1)

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("GH_TOKEN missing", file=sys.stderr)
        sys.exit(1)

    slug = re.sub(r"[^a-z0-9-]+", "-", ref.lower()).strip("-")
    name = f"kaggle-{slug}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    body = {
        "name": name,
        "private": True,
        "description": f"Kaggle competition: {competition.get('title', ref)}",
    }

    response = requests.post(
        f"https://api.github.com/orgs/{owner}/repos",
        json=body,
        headers=headers,
        timeout=30,
    )
    if response.status_code == 404:
        # owner is a user account, not an org
        response = requests.post(
            "https://api.github.com/user/repos",
            json=body,
            headers=headers,
            timeout=30,
        )
    if response.status_code != 201:
        print(
            f"GitHub repo create failed: {response.status_code} {response.text}",
            file=sys.stderr,
        )
        sys.exit(1)

    repo = response.json()
    with open("/output/result.json", "w") as handle:
        json.dump(
            {
                "repoUrl": repo.get("html_url"),
                "repoName": repo.get("full_name"),
                "cloneUrl": repo.get("clone_url"),
            },
            handle,
        )
    print(f"Created repo {repo.get('full_name')}")


if __name__ == "__main__":
    main()
