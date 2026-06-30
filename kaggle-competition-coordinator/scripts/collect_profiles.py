import json
import os
import sys
import urllib.request


def main():
    with open("/output/input.json") as handle:
        data = json.load(handle)

    spawned = ((data.get("steps") or {}).get("spawn_profiles") or {}).get("spawned", [])

    api_key = os.environ.get("PLATFORM_API_KEY")
    base_url = os.environ.get("APP_BASE_URL")
    if not api_key or not base_url:
        print("PLATFORM_API_KEY or APP_BASE_URL missing", file=sys.stderr)
        sys.exit(1)

    profiles = []
    for entry in spawned:
        instance_id = entry.get("instanceId")
        if not instance_id:
            continue
        try:
            request = urllib.request.Request(
                f"{base_url}/api/processes/{instance_id}",
                headers={"X-Api-Key": api_key, "Accept": "application/json"},
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                instance = json.loads(response.read().decode())
        except Exception as error:
            print(f"Failed to fetch instance {instance_id}: {error}", file=sys.stderr)
            continue

        trigger_payload = instance.get("triggerPayload") or {}
        step = (instance.get("variables") or {}).get("provide_profile") or {}
        params = step.get("paramValues") or step
        profiles.append(
            {
                "userId": trigger_payload.get("userId"),
                "email": trigger_payload.get("email", ""),
                "strengths": params.get("strengths", ""),
                "weaknesses": params.get("weaknesses", ""),
                "interests": params.get("interests", ""),
                "currentLoad": params.get("currentLoad", ""),
            }
        )

    summary = f"Collected {len(profiles)} of {len(spawned)} profiles"
    with open("/output/result.json", "w") as handle:
        json.dump(
            {
                "profiles": profiles,
                "profileCount": len(profiles),
                "totalSpawned": len(spawned),
                "summary": summary,
            },
            handle,
        )
    print(summary)


if __name__ == "__main__":
    main()
