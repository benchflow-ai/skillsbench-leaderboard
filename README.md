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

The broader `standard-v1` task set is staged for prebuilt-env full mode:

- `task_sets/standard-v1.json`: all 94 public direct children of
  `benchflow-ai/skillsbench:tasks/` at the source revision used for this sync.
- `prebuilt_images/standard-v1.json`: digest refs under the shared
  `ghcr.io/benchflow-ai/skillsbench-task-env` package. A complete, resolving
  map is required before public `standard-v1` Quick Submit runs.

The four `benchflow-ai/skillsbench:tasks_excluded/` tasks are intentionally not
included in `standard-v1`: `diff-transformer_impl`, `mhc-layer-impl`,
`scheduling-email-assistant`, and `speaker-diarization-subtitles`.

Full mode follows the Terminal-Bench-style hybrid path: the green image embeds
the worker and pre-bakes the SkillsBench task tree, each public task must have a
prebuilt task environment image, the worker discovers selected tasks from local
`tasks/*/task.toml`, shards by `num_shards`/`shard_index`, and pulls/runs the
digest-pinned task image. Task images are built outside AgentBeats Quick Submit;
public Quick Submit must not call Docker build for the 94-task set.

## Files

- `scenario.json5`: Amber scenario for the five-task worker-backed run.
- `green-agent.json5`: SkillsBench green-agent component manifest.
- `worker.json5`: SkillsBench worker component manifest.
- `participant-placeholder.json5`: placeholder purple participant manifest.
- `participant-agent-under-test.json5`: generic configurable purple
  agent-under-test manifest. It is one image with config-selected harness,
  model, provider, base URL, timeout, and secret fields.
- `scenario-agent-under-test-smoke.json5`: separate one-task
  `dialogue-parser` real-model smoke scenario for the generic purple image.
- `scenario-standard-v1.json5`: branch full-mode scenario for all public
  `standard-v1` tasks using prebuilt task env images and 20 shards.
- `.github/workflows/quick-submit.yml`: AgentBeats Quick Submit entrypoint. It
  calls the official AgentBeats leaderboard template runner required by the live
  Quick Submit service.
- `.github/workflows/run-agent-under-test-smoke.yml`: maintainer one-task smoke
  for proving the configurable purple image without changing the default
  five-task deployment smoke.
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
  `ghcr.io/benchflow-ai/skillsbench-agentbeats-worker@sha256:54d55c74c5411d18bedbd55376e59bda17e6205d927344bdb074c6f8c3683f05`
- standalone worker:
  `ghcr.io/benchflow-ai/skillsbench-agentbeats-worker@sha256:54d55c74c5411d18bedbd55376e59bda17e6205d927344bdb074c6f8c3683f05`
- standalone green:
  `ghcr.io/benchflow-ai/skillsbench-agentbeats-green@sha256:9e661530fe4cc9d330e1069a89197860bb52bf1f29a635b9ab2f6f3ec872e595`
- purple placeholder:
  `ghcr.io/benchflow-ai/skillsbench-agentbeats-purple@sha256:0ffaa273363680d0f4383087541562dffe2d75fcb22395815647df4cf58384f2`
- purple agent-under-test:
  `ghcr.io/benchflow-ai/skillsbench-agentbeats-purple@sha256:81d2e5c6cca6a97d4842df91ad3193f37142702823d6a24197ecff2d7f1a6536`
- task environments:
  `prebuilt_images/deploy-smoke-v1.json`

The five `deploy-smoke-v1` task environment refs are public, digest-pinned
entries under the shared `ghcr.io/benchflow-ai/skillsbench-task-env` GHCR
package. The `standard-v1` image map follows the same shared-package format,
and is required for public full mode. Missing or unresolved `standard-v1` refs
must fail before the run instead of falling back to Docker builds inside
AgentBeats Quick Submit.

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

BenchFlow-owned registration target:

- source repo: `https://github.com/benchflow-ai/skillsbench`
- leaderboard repo: `https://github.com/benchflow-ai/skillsbench-leaderboard`
- green manifest: `green-agent.json5`
- standard-v1 scenario: `scenario-standard-v1.json5`
- generic purple manifest: `participant-agent-under-test.json5`
- green AgentBeats ID: `019e5799-3aca-7d20-ba8c-2b0bc785ac62`
- generic purple agent-under-test ID:
  `019e5799-ca68-7b33-b1a5-c97b92b6fda1`
- green live manifest URL:
  `https://raw.githubusercontent.com/benchflow-ai/skillsbench-leaderboard/13e1d104695daabf4e83951df207d55e025401f6/green-agent.json5`
- generic purple live manifest URL:
  `https://raw.githubusercontent.com/benchflow-ai/skillsbench-leaderboard/90d5ad958e7c053835a3cd4083e2466f4edba3b8/participant-agent-under-test.json5`

The old smoke-only participant registration has been retired. Keep
older result and submission files that reference historical participant IDs as
provenance only; do not use those IDs for new submissions.

All repo URLs, raw manifest URLs, and runtime image refs in the current
submission surface are BenchFlow-owned or RDI AgentBeats infrastructure refs.
Do not register or submit new SkillsBench AgentBeats runs from a personal fork
or personal GHCR package.

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

The generic purple agent-under-test path has also been exercised through
AgentBeats Quick Submit:

- Quick Submit PR:
  `https://github.com/benchflow-ai/skillsbench-leaderboard/pull/8`
- workflow run:
  `https://github.com/benchflow-ai/skillsbench-leaderboard/actions/runs/26322856816`
- merged result:
  `results/019e536d-6528-77c3-bba6-4d7b7ecf4455.json`
- merged provenance:
  `submissions/019e536d-6528-77c3-bba6-4d7b7ecf4455-provenance.json`

That run proves A2A wiring for the generic purple image. It is not a full
score-quality proof: the standard-v1 result rows are present but score
ineligible.

## Source Branches

The runtime images were built from branch-scoped source work, not from direct
changes to official `main` branches:

- `benchflow-ai/skillsbench:codex/agentbeats-green-agent-runtime`
- `benchflow-ai/skillsbench:codex/agentbeats-seven-agent-standard-v1`
- `benchflow-ai/benchflow:codex/agentbeats-a2a-adapter-audit`

A2A is the AgentBeats participant protocol boundary. ACP remains BenchFlow's
coding-agent transport.

## standard-v1 Full Mode

Full public task-set updates should originate from `benchflow-ai/skillsbench`,
not manual edits in this repo. The source branch reads `tasks/*/task.toml`,
skips `tasks_excluded/` and any explicit denylist, and updates the public
task-set manifest. A separate maintainer workflow builds/publishes task
environment images into the shared `skillsbench-task-env` package outside
AgentBeats Quick Submit, then records digest refs for the leaderboard.

- `task_sets/standard-v1.json`
- required `prebuilt_images/standard-v1.json` digest entries

Current prebuilt-env verification target:

- JSON files parse.
- `task_sets/standard-v1.json` has 94 public tasks.
- No `tasks_excluded/` ids are present.
- `task_set: "standard-v1"` or `tasks: "all"` selects public tasks from the
  baked source tree.
- `num_shards` and `shard_index` deterministically split the selected task ids.
- Every selected task has a digest-pinned prebuilt task env ref.
- The worker verifies prebuilt refs and fails before task execution if required
  refs are missing or unresolved.
- BenchFlow uses AgentBeats-safe Docker cleanup without image/volume removal.
- No full all-task AgentBeats evaluation has been run.

The green/worker image has been built and published from the source branch. The
remaining production gate is to publish/verify all `standard-v1` task env
digests, then run representative shard smoke checks before switching the live
default beyond `deploy-smoke-v1`.

## Current Deployment State

Deploy-ready now:

- `deploy-smoke-v1` five-task AgentBeats adoption.
- Official Quick Submit path through
  `RDI-Foundation/agentbeats-leaderboard-template/.github/workflows/quick-submit-runner.yml@v2`.
- BenchFlow-owned runtime images and the shared five-task task-env package refs.
- Leaderboard queries for flat and nested AgentBeats result payloads.

Configured for full AgentBeats submission, but not fully deploy-verified:

- `standard-v1` task-set manifest with 94 public tasks.
- Source branch support for `tasks: "all"`, `task_set: "standard-v1"`,
  deterministic sharding, and required prebuilt task-env startup.
- `standard-v1` prebuilt image map in shared-package digest-ref format. The map
  must be verified against GHCR before public full-mode deployment.
- Generic purple agent-under-test support for `openhands`, `opencode`,
  `claude-code`, `codex`, `gemini-cli`, `terminus`, and `pi` in one image.
- `scenario-standard-v1.json5` as the full-mode scenario for 94 public tasks
  and 20 shards. The maintainer runner injects the checked-in prebuilt image
  map and rejects incomplete `standard-v1` maps.

Explicit full-submission status:

- 94 public tasks x 7 configurable harnesses is configured.
- Existing proof covers the five-task AgentBeats smoke path and a one-task
  generic-purple path.
- A complete 94-task x 7-harness AgentBeats evaluation has not been run.
- Submit full mode as configured/staged until representative shard evidence or
  the full run is available.

The checked-in `scenario.json5` keeps the five-task smoke path on the pinned
embedded-worker green manifest. The full-mode and generic-purple scenarios use
local manifests on this branch so the maintainer workflow can inject
`standard-v1` prebuilt-image configuration without changing the smoke default.

## Self-Run

Run the official five-task smoke from `main`:

```bash
gh workflow run run-scenario.yml \
  --repo benchflow-ai/skillsbench-leaderboard \
  --ref codex/agentbeats-seven-agent-standard-v1 \
  -f num_shards=1 \
  -f green_agent_id=019e5799-3aca-7d20-ba8c-2b0bc785ac62 \
  -f purple_agent_id=019e5799-ca68-7b33-b1a5-c97b92b6fda1 \
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

The checked-in Quick Submit workflow keeps the default five-task deployment
smoke at one shard. Standard-v1 full-mode scenarios carry their own
`num_shards: 20` assessment config. The self-run workflow caps matrix
concurrency with `max-parallel: 20`; the upstream AgentBeats Quick Submit
runner `@v2` also clamps submitted shard counts to 20.

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

con = duckdb.connect(":memory:")
try:
    con.execute("CREATE TABLE results AS SELECT * FROM read_json_auto('results/*.json', filename = true)")
    for name in ["overall", "by_category", "by_difficulty"]:
        rows = con.execute((Path("queries") / f"{name}.sql").read_text()).fetchall()
        if not rows:
            raise SystemExit(f"{name} query returned no rows")
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
- `standard-v1` full adoption remains prepared but not fully verified until all
  prebuilt task env refs are published/resolving and a representative shard
  smoke passes with the published green/worker image.
