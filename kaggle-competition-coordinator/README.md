# Kaggle Competition Coordinator

Coordinates a team through a Kaggle competition end-to-end:

1. **Gather profiles** — fan out a `gather-profile` child workflow to every selected
   member; each self-reports strengths, weaknesses, interests, and current load.
2. **Match competitions** — list open Kaggle competitions (Kaggle CLI) and rank them
   against the team profile (agent).
3. **Lead approval** — the competition lead picks one competition and approves entering
   it (or rejects to search again).
4. **Create repo + propose** — create a private GitHub repo, then an agent drafts a
   solution proposal.
5. **Reviewer loop** — an agent auto-selects a best-fit reviewer (by expertise, interest,
   and load — not necessarily the lead), who runs an approve/revise loop on the proposal.
6. **Submit + feedback + next steps** — upload the team's submission file, submit to
   Kaggle, poll for the validation score, then the lead decides: iterate, pick a new
   competition, or conclude.

This is a **coordination** workflow: it does not train models. The submittable file is
produced by the team and uploaded at the `provide_submission` step.

## Package contents

| Path | What |
|------|------|
| `src/kaggle-competition-coordinator.wd.json` | Parent workflow |
| `src/gather-profile.wd.json` | Child workflow (one run per member) |
| `Dockerfile` | Custom image: `mediforce-golden-image` + `kaggle` + `requests` + the scripts |
| `scripts/*.py` | The six deterministic step scripts, baked into the image |
| `index.json` | Git-import manifest |

## Workflows

Two Workflow Definitions are registered. **`gather-profile` must be registered in the
same namespace** so the parent's `spawn_profiles` step can launch it by name.

## Roles

| Role | Used by |
|------|---------|
| `competition-lead` | `select_members`, `review_competitions`, `provide_submission`, `next_steps` (also acts as the competition administrator for the final decision) |
| `reviewer` | `review_proposal` — resolved at runtime via `assignedTo` from `select_reviewer`, not pre-assigned |
| `team-member` | `provide_profile` in the child (assigned per member via the spawn payload `userId`) |

## Docker image

`Dockerfile` (at the package root) builds from `mediforce-golden-image` and adds the
Kaggle CLI, `requests`, and the scripts under `/opt/kaggle-coordinator/scripts/`. Every
`script` step runs in build mode (`dockerfile` + `repo` + `commit`). The
`match_competitions`, `select_reviewer`, and `propose_solution` agent steps run on the
stock `mediforce-golden-image` (LLM only — no Kaggle/GitHub access needed).

**Build context.** `docker-image-builder` clones the whole repo but uses the **Dockerfile's
own directory** as the build context, and resolves the `dockerfile` field relative to the
**repo root**. This package lives in the `kaggle-competition-coordinator/` subfolder of the
`my-workflows` repo, so the steps set:

- `dockerfile: kaggle-competition-coordinator/Dockerfile` (repo-root-relative)
- The Dockerfile sits next to `scripts/`, so `COPY scripts/ …` resolves inside the context.

Pinned to `repo: https://github.com/Griphu/my-workflows.git` @
`commit: bb27a2b1c4174dc42f0780648d739c4993a4fb24`.

## Environment contract

| Name | Secret | Scope | Used by | Meaning | How to set | Example |
|------|--------|-------|---------|---------|------------|---------|
| `PLATFORM_API_KEY` | yes | workflow | `fetch_members`, `collect_profiles` | Platform API key for member + instance reads | Workflow secrets panel | `mf-...` |
| `APP_BASE_URL` | no | workflow | `fetch_members`, `collect_profiles` | Mediforce base URL | Workflow or namespace env | `http://127.0.0.1:9003` |
| `KAGGLE_USERNAME` | yes | workflow | `fetch_competitions`, `submit_to_kaggle` | Kaggle account username | Workflow secrets panel | `janedoe` |
| `KAGGLE_KEY` | yes | workflow | `fetch_competitions`, `submit_to_kaggle` | Kaggle API token | Workflow secrets panel | `abcd1234...` |
| `GITHUB_TOKEN` | yes | workflow | `create_repo` | GitHub PAT with `repo` scope (mapped to `GH_TOKEN` env) | Workflow secrets panel | `ghp_...` |
| `OPENROUTER_API_KEY` | yes | workflow | agent steps | LLM provider key (Claude via OpenRouter) | Workflow secrets panel | `sk-or-v1-...` |
| `ANTHROPIC_BASE_URL` | no | workflow | agent steps | Claude-compatible API base URL | Workflow or namespace env | `https://openrouter.ai/api` |

Optional script tuning (env, non-secret): `KAGGLE_POLL_SECONDS` (default `600`),
`KAGGLE_POLL_INTERVAL` (default `20`), `SUBMISSION_FILE` (override the uploaded-file path).

## Agents, MCPs, skills

- **Agents:** `match_competitions`, `select_reviewer`, `propose_solution` use the default
  `claude-code-agent` plugin with inline prompts and `model: sonnet`. No Agent Definition
  binding required.
- **MCPs:** none. Kaggle is reached through the CLI in a `script` step, not an MCP.
- **Skills:** none.

## Output contracts

| Step | `result.json` shape |
|------|---------------------|
| `fetch_members` | `{ options: [{ id, label, email, role, avatarUrl }] }` |
| `prepare` | `{ teamMembers: [{ userId, email }], deadline }` |
| `collect_profiles` | `{ profiles: [{ userId, email, strengths, weaknesses, interests, currentLoad }], profileCount, totalSpawned, summary }` |
| `fetch_competitions` | `{ competitions: [{ ref, title, deadline, category, reward, description }], count }` |
| `match_competitions` (agent) | `{ options: [{ label, description, value: { competitionRef, title, deadline, category } }], summary }` |
| `select_reviewer` (agent) | `{ reviewerId, reviewerEmail, rationale }` |
| `propose_solution` (agent) | `{ proposal, summary }` |
| `create_repo` | `{ repoUrl, repoName, cloneUrl }` |
| `submit_to_kaggle` | `{ submitted, competitionRef, scored, publicScore?, privateScore?, status?, fileName?, message? }` |

`review_competitions` (selection: 1) outputs the selected competition value object, read
downstream as `${steps.review_competitions.competitionRef}`.

## Known-good input (parent trigger)

```json
{
  "namespace": "appsilon",
  "profileDurationHours": 24,
  "githubOwner": "Griphu",
  "competitionHint": "tabular"
}
```

## Runtime assumptions to verify on the platform

The schema validates and the scripts pass syntax/behaviour checks in isolation, but these
depend on platform/runtime shapes that are **not** provable offline — confirm with a real
run:

- **`collect_profiles`** reads each child's `triggerPayload.userId` / `triggerPayload.email`
  and `variables.provide_profile` from `GET /api/processes/{id}`. Verify the instance
  response exposes `triggerPayload`.
- **`provide_submission` → `submit_to_kaggle`** — the script searches the
  `provide_submission` step output (`files`/`uploads`/`path`), `SUBMISSION_FILE`, and
  `/output/submission.csv` / `/workspace/submission.csv` for the uploaded file. Confirm
  where the `file-upload` component exposes attachments to a downstream container and set
  `SUBMISSION_FILE` if it differs.
- **Kaggle polling** — `competition_submissions(...)[0].publicScore` is read until set or
  `KAGGLE_POLL_SECONDS` elapses. Some competitions score slowly; raise the timeout if a run
  reports `scored: false`.
- `wait_for_profiles` uses a fixed `deadline`; the `wait` action does not poll a condition.

## Register

`gather-profile` first (the parent spawns it by name), then the parent:

```bash
pnpm exec mediforce workflow register \
  --file src/gather-profile.wd.json --namespace <ns>

pnpm exec mediforce workflow register \
  --file src/kaggle-competition-coordinator.wd.json --namespace <ns>
```

Import from git (public GitHub only; paths are repo-root-relative):

```bash
pnpm exec mediforce workflow import \
  --repo https://github.com/Griphu/my-workflows.git \
  --path kaggle-competition-coordinator/src/kaggle-competition-coordinator.wd.json \
  --ref bb27a2b1c4174dc42f0780648d739c4993a4fb24 --namespace <ns>
```

## Pinning — done

Pinned to `https://github.com/Griphu/my-workflows.git` @
`bb27a2b1c4174dc42f0780648d739c4993a4fb24` in all four `script` steps.

If you change any baked script or the Dockerfile, re-commit and update the `commit` in each
`script` step to the new SHA (the `dockerfile`/`repo` fields stay the same), then re-run the
dry-run. `git commit --amend --no-edit` keeps the build context byte-identical, so an amend
that only folds in the SHA-filled `.wd.json` leaves the pin valid.
