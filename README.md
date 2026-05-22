# SkillsBench AgentBeats Leaderboard

Standalone AgentBeats leaderboard repository for SkillsBench. This repo is the
AgentBeats-facing surface; the source SkillsBench and BenchFlow repos remain
unchanged on `main`.

## Scope

The checked-in scenario defaults to `deploy-smoke-v1`:

- `citation-check`
- `court-form-filling`
- `dialogue-parser`
- `offer-letter-generator`
- `powerlifting-coef-calc`

This remains the minimal public deployment gate for proving the SkillsBench
green agent, worker, A2A participant boundary, result shape, and leaderboard
queries.

The broader `standard-v1` task set is staged for runtime-first full mode:

- `task_sets/standard-v1.json`: all 94 public direct children of
  `benchflow-ai/skillsbench:tasks/` at the source revision used for this sync.
- `prebuilt_images/standard-v1.json`: optional cache refs under the shared
  `ghcr.io/benchflow-ai/skillsbench-task-env` package. They are not required
  for full-mode correctness.

The four `benchflow-ai/skillsbench:tasks_excluded/` tasks are intentionally not
included in `standard-v1`: `diff-transformer_impl`, `mhc-layer-impl`,
`scheduling-email-assistant`, and `speaker-diarization-subtitles`.

Full mode should follow the Terminal-Bench-style runtime-first path: the green
image embeds the worker and pre-bakes the SkillsBench task tree, the worker
discovers selected tasks from local `tasks/*/task.toml`, shards by
`num_shards`/`shard_index`, and builds/starts each
`tasks/<id>/environment/Dockerfile` at assessment time. Prebuilt task images
remain cache-only acceleration.

## Files

- `scenario.json5`: Amber scenario for the five-task worker-backed run.
- `green-agent.json5`: SkillsBench green-agent component manifest.
- `worker.json5`: SkillsBench worker component manifest.
- `participant-placeholder.json5`: baseline purple participant manifest.
- `.github/workflows/quick-submit.yml`: AgentBeats Quick Submit entrypoint. It
  calls the official AgentBeats leaderboard template runner required by the live
  Quick Submit service.
- `.github/workflows/run-scenario.yml`: maintainer self-run workflow with
  SkillsBench-specific task-set and result-shape checks.
- `task_sets/deploy-smoke-v1.json`: canonical five-task task-set manifest.
- `task_sets/standard-v1.json`: generated full public task-set manifest.
- `prebuilt_images/deploy-smoke-v1.json`: digest-pinned task environment images.
- `prebuilt_images/standard-v1.json`: generated full public task-image map.
- `queries/*.sql`: DuckDB leaderboard queries. The first column is the
  AgentBeats purple-agent UUID.
- `results/`: merged public result JSON files read by AgentBeats.
- `submissions/`: submitted scenario/provenance files.

## Runtime Images

Current public digest-pinned images:

- green with embedded worker:
  `ghcr.io/benchflow-ai/skillsbench-agentbeats-worker@sha256:21d157ffd06f06ff38bcd5e56a15d92d958ad88ff7f1db9db1afc5ae90eb0b9a`
- standalone worker:
  `ghcr.io/benchflow-ai/skillsbench-agentbeats-worker@sha256:21d157ffd06f06ff38bcd5e56a15d92d958ad88ff7f1db9db1afc5ae90eb0b9a`
- purple baseline:
  `ghcr.io/benchflow-ai/skillsbench-agentbeats-purple@sha256:0ffaa273363680d0f4383087541562dffe2d75fcb22395815647df4cf58384f2`
- task environments:
  `prebuilt_images/deploy-smoke-v1.json`

The five `deploy-smoke-v1` task environment refs are public, digest-pinned
entries under the shared `ghcr.io/benchflow-ai/skillsbench-task-env` GHCR
package. The `standard-v1` image map follows the same shared-package format,
but it is an optional cache map. Missing or unresolved cache refs must fall
back to runtime builds from the baked local task Dockerfiles.

## Official Self-Run Evidence

The official five-task self-run has completed on this repo's `main` branch:

- workflow run:
  `https://github.com/benchflow-ai/skillsbench-leaderboard/actions/runs/26305709308`
- workflow commit:
  `d90627cfa37cf4e73263dc900ca593bf37e6ecbd`
- submission branch:
  `submission-benchflow-ai-20260522-185007`
- merged PR:
  `https://github.com/benchflow-ai/skillsbench-leaderboard/pull/1`
- result file:
  `results/benchflow-ai-20260522-185007.json`
- provenance file:
  `submissions/benchflow-ai-20260522-185007-provenance.json`

The submitted result contains exactly five flattened public rows for
`deploy-smoke-v1`, all with `score_eligible: true`,
`infra_failure_type: null`, and `agent_transport: "a2a"`. The result is merged
into `main`, so AgentBeats can read it from `results/*.json`.

## AgentBeats Registration

Live AgentBeats registration status as of 2026-05-22:

- green page: `https://agentbeats.dev/Yiminnn/skillsbench-agentbeats`
- green ID: `019e4ecb-4b5b-7481-b6f4-85ad93336437`
- purple baseline page:
  `https://agentbeats.dev/Yiminnn/skillsbench-baseline-purple`
- purple baseline ID: `019e4ed1-d333-7133-807f-5f22c04d5eef`
- registered repo and leaderboard repo:
  `https://github.com/benchflow-ai/skillsbench-leaderboard`
- registered Amber manifest:
  `https://raw.githubusercontent.com/benchflow-ai/skillsbench-leaderboard/54f98e9488ad82f3c8f84a8cdf6a2b9edb7dc29b/green-agent.json5`

AgentBeats has read the merged result at commit `4acc96c` and shows
leaderboard rows for `Yiminnn/skillsbench-baseline-purple` across the overall,
category, and difficulty query tabs.

Live Quick Submit has also been proven for the current five-task smoke:

- Quick Submit PR:
  `https://github.com/benchflow-ai/skillsbench-leaderboard/pull/3`
- workflow run:
  `https://github.com/benchflow-ai/skillsbench-leaderboard/actions/runs/26310163922`
- merged result:
  `results/019e515b-26ad-7510-983f-f8f9f2db5ac6.json`
- merged provenance:
  `submissions/019e515b-26ad-7510-983f-f8f9f2db5ac6-provenance.json`

That run used the official AgentBeats Quick Submit runner and produced five
score-eligible A2A task rows with no infra failure.

## Source Branches

The runtime images were built from branch-scoped source work, not from direct
changes to official `main` branches:

- `benchflow-ai/skillsbench:codex/agentbeats-green-agent-runtime`
- `benchflow-ai/benchflow:codex/agentbeats-a2a-adapter-audit`

A2A is the AgentBeats participant protocol boundary. ACP remains BenchFlow's
coding-agent transport.

## standard-v1 Full Mode

Full public task-set updates should originate from `benchflow-ai/skillsbench`,
not manual edits in this repo. The runtime-first source branch reads
`tasks/*/task.toml`, skips `tasks_excluded/` and any explicit denylist, and
updates the public task-set manifest. It does not require all task environment
images to be pre-published before `standard-v1` can be deploy-ready.

- `task_sets/standard-v1.json`
- optional `prebuilt_images/standard-v1.json` cache entries

Current runtime-first verification target:

- JSON files parse.
- `task_sets/standard-v1.json` has 94 public tasks.
- No `tasks_excluded/` ids are present.
- `task_set: "standard-v1"` or `tasks: "all"` selects public tasks from the
  baked source tree.
- `num_shards` and `shard_index` deterministically split the selected task ids.
- Cache refs are optional and are used only when they resolve.
- No full all-task AgentBeats evaluation has been run.

The remaining production gate is to build/publish a new runtime-first green
image from the source branch, then run representative shard smoke checks.

## Current Deployment State

Deploy-ready now:

- `deploy-smoke-v1` five-task AgentBeats adoption.
- Official Quick Submit path through
  `RDI-Foundation/agentbeats-leaderboard-template/.github/workflows/quick-submit-runner.yml@v2`.
- BenchFlow-owned runtime images and the shared five-task task-env package refs.
- Leaderboard queries for flat and nested AgentBeats result payloads.

Prepared but not fully deploy-verified:

- `standard-v1` task-set manifest with 94 public tasks.
- Runtime-first source branch support for `tasks: "all"`, `task_set:
  "standard-v1"`, deterministic sharding, and cache-optional task startup.
- Optional `standard-v1` prebuilt image cache map in shared-package digest-ref
  format.

The checked-in `scenario.json5` still includes a separate `skillsbench_worker`
component and binding. The live Quick Submit path uses `green-agent.json5`,
where the green component embeds the worker because AgentBeats-generated Quick
Submit scenarios include gateway + green + purple, not a custom worker
component. The separate worker in `scenario.json5` is therefore redundant for
Quick Submit, but remains useful for local/self-run compatibility until a later
cleanup removes or splits that path.

## Self-Run

Run the official five-task smoke from `main`:

```bash
gh workflow run run-scenario.yml \
  --repo benchflow-ai/skillsbench-leaderboard \
  --ref main \
  -f num_shards=1 \
  -f green_agent_id=019e4ecb-4b5b-7481-b6f4-85ad93336437 \
  -f purple_agent_id=019e4ed1-d333-7133-807f-5f22c04d5eef \
  -f require_durable_private_proof=false
```

Do not pass `task_set` for the deployment smoke. The checked-in scenario already
defaults to `deploy-smoke-v1`.

## Quick Submit

Quick Submit requirements from AgentBeats:

- `.github/workflows/quick-submit.yml` must exist on `main`.
- The AgentBeats GitHub App must be installed on this repo.
- AgentBeats must create a `quick-submit-<uuid>` PR containing a strict JSON
  scenario under `submissions/*<uuid>*.json`.
- The workflow retrieves temporary AgentBeats backend secrets through OIDC.

This repo uses the official AgentBeats reusable Quick Submit runner:

```yaml
uses: RDI-Foundation/agentbeats-leaderboard-template/.github/workflows/quick-submit-runner.yml@v2
```

The live AgentBeats green registration points at this repo, and the AgentBeats
GitHub App is connected for `benchflow-ai/skillsbench-leaderboard`. Quick
Submit PR #3 proved that AgentBeats can create a `quick-submit-<uuid>` PR, run
`.github/workflows/quick-submit.yml`, retrieve temporary backend secrets
through OIDC, and merge result/provenance. The green agent intentionally
exposes no Quick Submit secrets; it embeds the worker process in the same
container for the live AgentBeats Quick Submit path.

Rerun a live submit smoke only after changing the registered component
manifests or runtime image digests.

## Leaderboard Queries

AgentBeats reads `results/*.json` with DuckDB. Validate locally:

```bash
uv run --with duckdb python - <<'PY'
from pathlib import Path
import duckdb

agent_id = "019e4ed1-d333-7133-807f-5f22c04d5eef"
con = duckdb.connect(":memory:")
try:
    con.execute("CREATE TABLE results AS SELECT * FROM read_json_auto('results/*.json', filename = true)")
    for name in ["overall", "by_category", "by_difficulty"]:
        rows = con.execute((Path("queries") / f"{name}.sql").read_text()).fetchall()
        if not rows or not any(row and str(row[0]) == agent_id for row in rows):
            raise SystemExit(f"{name} query failed registered-id check: {rows}")
    print("queries verified")
finally:
    con.close()
PY
```

## Official Deployment Checklist

- `scenario.json5` on `main` uses this repo's raw manifest URLs pinned to a
  verified commit.
- Official `main` self-run succeeds with registered green and purple IDs.
- Generated result has exactly five public flattened rows.
- Public rows have `score_eligible: true`, `infra_failure_type: null`, and
  `agent_transport: "a2a"`.
- Public rows do not expose hidden tests, solutions, credentials, raw logs,
  local paths, or private proof.
- DuckDB queries return the registered purple AgentBeats UUID as the first
  column.
- Generated result branch is merged into `main` so AgentBeats can read
  `results/*.json`.
- AgentBeats green registration points to
  `https://github.com/benchflow-ai/skillsbench-leaderboard`.
- AgentBeats UI has read commit `4acc96c` and renders overall, category, and
  difficulty leaderboard rows.
- Quick Submit GitHub App connection is approved for
  `benchflow-ai/skillsbench-leaderboard`; rerun a live submit smoke after
  manifest updates.
- `standard-v1` full adoption remains prepared but not fully verified until the
  94 task image refs are actually published/verified under
  `ghcr.io/benchflow-ai/skillsbench-task-env`.
