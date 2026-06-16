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
- `participant-agent-under-test.json5`: generic configurable purple
  agent-under-test manifest. It is one image with config-selected harness,
  model, provider, base URL, timeout, and secret fields.
- `scenario-agent-under-test-smoke.json5`: separate one-task
  `dialogue-parser` real-model smoke scenario for the generic purple image.
- `scenario-standard-v1.json5`: branch full-mode scenario for all public
  `standard-v1` tasks using runtime-first task builds and seven shards.
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
- `task_sets/skillsbench-v1.1.json`: generated 87-task public task-set
  manifest for the next AgentBeats deployment.
- `prebuilt_images/deploy-smoke-v1.json`: digest-pinned task environment images.
- `prebuilt_images/standard-v1.json`: generated full public task-image map.
- `prebuilt_images/skillsbench-v1.1.json`: full digest-pinned task-image map
  for `skillsbench-v1.1`.
- `deploy_bundles/skillsbench-v1.1.json`: deploy-ready bundle tying the source
  revision, runtime image digests, task-set digest, and 87 prebuilt task images.
- `queries/*.sql`: DuckDB leaderboard queries. The first column is the
  AgentBeats purple-agent UUID.
- `results/`: merged public result JSON files read by AgentBeats.
- `submissions/`: submitted scenario/provenance files.

## Runtime Images

Current public digest-pinned images:

- green with embedded worker:
  `ghcr.io/benchflow-ai/skillsbench-agentbeats-worker@sha256:c305b974356603499594a5f34c883d164ad7684eaf6fd71c21c0c2ea30c33f94`
- standalone worker:
  `ghcr.io/benchflow-ai/skillsbench-agentbeats-worker@sha256:c305b974356603499594a5f34c883d164ad7684eaf6fd71c21c0c2ea30c33f94`
- standalone green:
  `ghcr.io/benchflow-ai/skillsbench-agentbeats-green@sha256:44ad6ce284909737b8eae5ff1ba043cc0ad7b6244c811590b7ce60159b9fa30e`
- purple baseline:
  `ghcr.io/benchflow-ai/skillsbench-agentbeats-purple@sha256:07b930f8c412bb21e0c9027158a0336baaf495b7597fd9b9d91623feebaca8ce`
- purple agent-under-test:
  `ghcr.io/benchflow-ai/skillsbench-agentbeats-purple@sha256:07b930f8c412bb21e0c9027158a0336baaf495b7597fd9b9d91623feebaca8ce`
- task environments:
  `prebuilt_images/skillsbench-v1.1.json`
- deploy bundle:
  `deploy_bundles/skillsbench-v1.1.json`

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

BenchFlow-owned registration target:

- source repo: `https://github.com/benchflow-ai/skillsbench`
- leaderboard repo: `https://github.com/benchflow-ai/skillsbench-leaderboard`
- green manifest: `green-agent.json5`
- standard-v1 scenario: `scenario-standard-v1.json5`
- generic purple manifest: `participant-agent-under-test.json5`
- green ID used by existing smoke evidence: `019e4ecb-4b5b-7481-b6f4-85ad93336437`
- purple baseline ID used by existing smoke evidence:
  `019e4ed1-d333-7133-807f-5f22c04d5eef`

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

The runtime-first green/worker image has been built and published from the
source branch. The remaining production gate is to run representative shard
smoke checks before switching the live default beyond `deploy-smoke-v1`.

## Current Deployment State

Deploy-ready now:

- `deploy-smoke-v1` five-task AgentBeats adoption.
- Official Quick Submit path through
  `RDI-Foundation/agentbeats-leaderboard-template/.github/workflows/quick-submit-runner.yml@v2`.
- BenchFlow-owned runtime images and the shared five-task task-env package refs.
- Leaderboard queries for flat and nested AgentBeats result payloads.

Configured for full AgentBeats submission, but not fully deploy-verified:

- `standard-v1` task-set manifest with 94 public tasks.
- Runtime-first source branch support for `tasks: "all"`, `task_set:
  "standard-v1"`, deterministic sharding, and cache-optional task startup.
- Optional `standard-v1` prebuilt image cache map in shared-package digest-ref
  format.
- Generic purple agent-under-test support for `openhands`, `opencode`,
  `claude-code`, `codex`, `gemini-cli`, `terminus`, and `pi` in one image.
- `scenario-standard-v1.json5` as the full-mode scenario for 94 public tasks
  and seven shards. It omits the 94-image cache map by default so runtime
  builds from the baked task tree remain the correctness path.

Explicit full-submission status:

- 94 public tasks x 7 configurable harnesses is configured.
- Existing proof covers the five-task AgentBeats smoke path and a one-task
  generic-purple path.
- A complete 94-task x 7-harness AgentBeats evaluation has not been run.
- Submit full mode as configured/staged until representative shard evidence or
  the full run is available.

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

The checked-in Quick Submit workflow keeps the default five-task deployment
smoke at one shard. Standard-v1 full-mode scenarios must carry their own
`num_shards: 7` assessment config, matching the Terminal-Bench-style pattern for
larger task sets.

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
- `standard-v1` full adoption remains prepared but not fully verified until a
  representative runtime-first shard smoke passes with the published
  green/worker image. Full adoption does not require all 94 task environment
  image refs to be pre-published.
