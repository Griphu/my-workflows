# kaggle-collect-profile

Child workflow spawned once per team member by
[`kaggle-competition-coordination`](../kaggle-competition-coordination/). One
member self-reports their profile for Kaggle competition planning.

## Flow

```
provide_profile (human, assigned to ${triggerPayload.userId}) -> done
```

## Trigger input (set by the parent spawn payload)

| Field | Type | Required | Meaning |
|-------|------|----------|---------|
| `userId` | string | yes | Member the task is assigned to (`assignedTo`) |
| `name` | string | no | Display name (informational) |
| `email` | string | no | Email (informational) |

## Output contract

The parent reads `variables.provide_profile.paramValues`:

```json
{ "strengths": "...", "weaknesses": "...", "interests": "...", "availability": "high|medium|low" }
```

`availability` is the self-reported workload signal the parent uses to pick a
non-overloaded reviewer.

## Env / secrets

None. Runs on `mediforce-golden-image`, no custom image, no pinning.

## Register

```bash
pnpm exec mediforce workflow register \
  --file kaggle-collect-profile/src/kaggle-collect-profile.wd.json --namespace <ns>
```

Register this **before** the parent — the parent spawns it by name.
