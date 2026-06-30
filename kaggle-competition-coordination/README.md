# kaggle-competition-coordination

Coordinate a team end-to-end through a Kaggle competition. Parent workflow that
fans profile collection out to each team member, matches competitions to the
team, gets a lead's approval, creates a repo, drafts a written solution
proposal, iterates with a chosen reviewer, submits to Kaggle, and returns the
score to the administrator for a next-steps decision.

Pairs with the child workflow [`kaggle-collect-profile`](../kaggle-collect-profile/)
(register it **first** — the parent spawns it by name).

## Flow

```
fetch_members -> select_team -> prepare -> gather_profiles (spawn N children)
  -> await_profiles (wait deadline) -> collect_profiles
  -> fetch_competitions -> match_competitions -> lead_pick
       approve -> create_repo
                    status 201 -> pick_reviewer -> propose_solution -> review_solution
                                     approve-submit -> provide_submission -> submit_kaggle
                                       -> admin_next_steps
                                            iterate -> propose_solution
                                            finish  -> completed
                                            abandon -> abandoned
                                     revise -> propose_solution
                    else -> repo_failed
       revise -> fetch_competitions
       reject -> abandoned
```

## Executors

| Step | Executor | Why |
|------|----------|-----|
| `fetch_members`, `prepare`, `collect_profiles` | `script` (inline JS, golden image) | deterministic platform-API glue |
| `gather_profiles` | `action` `spawn` (`forEach`) | fan-out one child per member |
| `await_profiles` | `action` `wait` (deadline) | timed collection window |
| `fetch_competitions`, `submit_kaggle` | `script` (pinned, Python, Kaggle CLI) | needs the `kaggle` package -> custom image |
| `match_competitions`, `pick_reviewer`, `propose_solution` | `agent` (L4) | judgment / synthesis |
| `lead_pick`, `review_solution`, `provide_submission`, `admin_next_steps`, `select_team` | `human` | accountability / approval |
| `create_repo` | `action` `http` | built-in side effect |

`lead_pick` uses `selection: 1` over the shortlist `match_competitions` emits.
`review_solution` and `admin_next_steps` use **custom verdicts** (`approve-submit`
/ `iterate` …) so they are `human type: review` steps, **not** CM3/L3 loops
(L3 only keys off literal `approve`/`revise`).

`create_repo` guards on `output.status == 201` because the `http` action never
throws on a non-2xx response.

## Environment contract

| Name | Secret | Scope | Used by | Meaning | How to set | Example |
|------|--------|-------|---------|---------|------------|---------|
| `PLATFORM_API_KEY` | yes | workflow or namespace | `fetch_members`, `collect_profiles` | Mediforce API key for the members + run-output endpoints | Workflow secrets panel | `mf-...` |
| `APP_BASE_URL` | no | workflow or namespace | `fetch_members`, `collect_profiles` | Mediforce base URL | Workflow env or namespace env | `http://127.0.0.1:9003` |
| `KAGGLE_USERNAME` | yes | workflow | `fetch_competitions`, `submit_kaggle` | Kaggle account username | Workflow secrets panel | `janedoe` |
| `KAGGLE_KEY` | yes | workflow | `fetch_competitions`, `submit_kaggle` | Kaggle API key (from kaggle.json) | Workflow secrets panel | `abc123...` |
| `GITHUB_TOKEN` | yes | workflow | `create_repo` | GitHub token with `repo`/`admin:org` create-repo scope for the org | Workflow secrets panel | `ghp_...` |
| `OPENROUTER_API_KEY` | yes | workflow or namespace | agent steps | LLM provider key (Claude via OpenRouter) | Workflow secrets panel | `sk-or-v1-...` |
| `ANTHROPIC_BASE_URL` | no | step env (set in `.wd.json`) | agent steps | Claude-compatible base URL | already set to `https://openrouter.ai/api` | — |

## Agents

All three agent steps use `claude-code-agent`, model `sonnet`, `timeoutMinutes: 15`,
autonomy `L4`, on `mediforce-golden-image`. They reason over the input JSON only —
**no MCP servers, no Tool Catalog, no Agent Definition bindings required**, and no
internet tools (`WebSearch`/`WebFetch`) are granted (competition data comes from
`fetch_competitions`). Each prompt carries a mandatory `/output/result.json`
output contract.

## Docker image (pinned)

`fetch_competitions` and `submit_kaggle` build from
[`Dockerfile`](./Dockerfile) (`FROM mediforce-golden-image` + `pip install
kaggle`), with `scripts/` copied to `/opt/kaggle/scripts/`.

- Build-context invariant: the `dockerfile` field is repo-root-relative
  (`kaggle-competition-coordination/Dockerfile`); the build context is this
  folder, so `COPY scripts/` resolves to `kaggle-competition-coordination/scripts/`
  and the step `command` is `python /opt/kaggle/scripts/<name>.py`.
- **Pinning state: UNPINNED.** Both pinned steps set
  `repo: https://github.com/Griphu/my-workflows` and
  `commit: 0000000000000000000000000000000000000000` (placeholder). Fill the real
  commit SHA after the first commit — see "Pinning" below. **The package is not
  production-ready until the SHA is filled.**

## Output contracts

| Step | result shape (keys read downstream) |
|------|-------------------------------------|
| `fetch_members` | `{ options: [{id,label,email,avatarUrl}] }` |
| `prepare` | `{ teamMembers: [{userId,email,name}], deadline }` |
| `gather_profiles` | `{ spawned: [{instanceId,itemIndex,...}], spawnedCount }` (engine) |
| `collect_profiles` | `{ profiles: [{userId,name,email,strengths,weaknesses,interests,availability,responded}], profileCount, totalSpawned }` |
| `fetch_competitions` | `{ competitions: [{ref,title,category,deadline,tags,description,reward}] }` |
| `match_competitions` | `{ options: [{label,description,value:{ref,title,category,deadline,fitRationale}}], summary }` |
| `lead_pick` | selected option value fields: `ref`, `title`, `category`, `deadline`, `fitRationale` |
| `create_repo` | `{ status, headers, body:{json,text}, url, method }` (http action) |
| `pick_reviewer` | `{ reviewerUserId, reviewerName, rationale }` |
| `propose_solution` | `{ proposal:{approach,modelChoice,dataStrategy,evalMetric,taskSplit[],risks[]}, summary }` |
| `review_solution` | `{ verdict, feedback }` |
| `provide_submission` | `{ submissionFileUrl, submissionMessage }` |
| `submit_kaggle` | `{ competitionRef, publicScore, status, submittedAt, message }` |

## MANUAL platform setup (not done by the package)

1. Create the secrets above in the workflow's secrets panel (`PLATFORM_API_KEY`,
   `KAGGLE_USERNAME`, `KAGGLE_KEY`, `GITHUB_TOKEN`, `OPENROUTER_API_KEY`).
2. Set `APP_BASE_URL` as env if not deployment-default.
3. Ensure `githubOwner` (passed at trigger) is a GitHub **org** the `GITHUB_TOKEN`
   can create repos in. For a personal account, change the `create_repo` URL from
   `/orgs/{owner}/repos` to `/user/repos`.
4. Register `kaggle-collect-profile` **before** this workflow.

## Register

Children first.

```bash
# 1. child
pnpm exec mediforce workflow register \
  --file kaggle-collect-profile/src/kaggle-collect-profile.wd.json --namespace <ns>

# 2. parent
pnpm exec mediforce workflow register \
  --file kaggle-competition-coordination/src/kaggle-competition-coordination.wd.json --namespace <ns>
```

Or import from git (after pushing + filling the SHA; paths are repo-root-relative):

```bash
pnpm exec mediforce workflow import \
  --repo https://github.com/Griphu/my-workflows \
  --path kaggle-competition-coordination/src/kaggle-competition-coordination.wd.json \
  --ref <sha> --namespace <ns>
```

## Pinning (fill the commit SHA — one commit, no loop)

1. Commit the package once. Get the SHA: `git rev-parse HEAD`.
2. Replace the `0000…0000` placeholder in **both** pinned steps' `commit` field
   with that SHA. (Local `register --file` reads the working tree, so no further
   commit is needed to run; the `commit` only needs to point at a reachable
   commit whose `scripts/` + `Dockerfile` are correct.)
3. Re-run the dry-run.

## Known-good trigger input

```json
{
  "leadUserId": "user-abc",
  "durationHours": 24,
  "namespace": "mediforce",
  "githubOwner": "Griphu"
}
```
