# Test summary

Run all: `python tests/run_tests.py` (from the workflow folder).

| Script | Status | Asserted shape | How to fully run |
|--------|--------|----------------|------------------|
| `fetch_competitions.py` | skipped — needs `KAGGLE_USERNAME` + `KAGGLE_KEY` (no-credentials guard path verified now) | `result.json.competitions` is a list | `KAGGLE_USERNAME=<u> KAGGLE_KEY=<k> python tests/run_tests.py` |
| `submit_kaggle.py` | skipped — needs `KAGGLE_USERNAME` + `KAGGLE_KEY` + `TEST_KAGGLE_SUBMIT=1` (no-credentials guard path verified now) | `result.json` has `competitionRef` + `publicScore` | `KAGGLE_USERNAME=<u> KAGGLE_KEY=<k> TEST_KAGGLE_SUBMIT=1 python tests/run_tests.py` (requires a competition you have joined and a reachable `submissionFileUrl` in `fixtures/submit_kaggle.input.json`) |

## What was verified now (no credentials)
- Both scripts compile (`py_compile`).
- Both scripts' no-credentials guard exits `1` with `KAGGLE_USERNAME or KAGGLE_KEY missing` — exercised live by `run_tests.py`.

## What is NOT yet verified
- Live Kaggle list/submit behavior (needs real creds + network).
- That the `kaggle==1.6.17` image builds and that the steps run end-to-end on the
  platform — exercised only by an actual workflow run.

## Inline JS steps (not in this folder)
`fetch_members`, `prepare`, `collect_profiles` are inline glue in the `.wd.json`
(not pinned package files), so they are syntax-checked (`node --check`) but not
given persisted behavior tests, per the authoring rules (the `tests/` folder is
for pinned package code).
