import json
import os
import sys
import urllib.parse
import urllib.request


def main():
    with open("/output/input.json") as handle:
        data = json.load(handle)

    namespace = data.get("namespace")
    if not namespace:
        print("namespace trigger input missing", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("PLATFORM_API_KEY")
    base_url = os.environ.get("APP_BASE_URL")
    if not api_key or not base_url:
        print("PLATFORM_API_KEY or APP_BASE_URL missing", file=sys.stderr)
        sys.exit(1)

    url = f"{base_url}/api/users/members?namespace={urllib.parse.quote(namespace)}"
    request = urllib.request.Request(
        url, headers={"X-Api-Key": api_key, "Accept": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode())

    options = []
    for member in payload.get("members", []):
        options.append(
            {
                "id": member.get("uid"),
                "label": member.get("displayName")
                or member.get("email")
                or member.get("uid"),
                "email": member.get("email") or "",
                "role": member.get("role") or "member",
                "avatarUrl": member.get("avatarUrl") or "",
            }
        )

    with open("/output/result.json", "w") as handle:
        json.dump({"options": options}, handle)
    print(f"Fetched {len(options)} member(s) from {namespace}")


if __name__ == "__main__":
    main()
