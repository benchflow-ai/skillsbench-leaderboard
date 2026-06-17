# SkillsBench AgentBeats Leaderboard

Standalone AgentBeats leaderboard repository for SkillsBench. This repo is the
AgentBeats-facing surface; the source SkillsBench and BenchFlow repos remain
unchanged on `main`.

## Scope

The maintainer self-run scenario defaults to `deploy-smoke-v1`:

- `citation-check`
- `court-form-filling`
- `dialogue-parser`
- `offer-letter-generator`
- `powerlifting-coef-calc`

This remains the minimal public deployment gate for proving the SkillsBench
green agent, worker, A2A participant boundary, result shape, and leaderboard
queries.

The current AgentBeats promotion target is `skillsbench-v1.1`:

- `task_sets/skillsbench-v1.1.json`: 87 public tasks generated from
  `benchflow-ai/skillsbench@ffc7b000b40aa8a9bed9091c95d700c0f83c1e63`.
- `prebuilt_images/skillsbench-v1.1.json`: digest-pinned public `linux/amd64`
  task environment images for all 87 task ids.
- `deploy_bundles/skillsbench-v1.1.json`: runtime source revision
  `cbfa8765b1d47503680e37d1fe06c01efb56e145`, runtime image digests, task-set
  digest, and 87 prebuilt task image refs in one reviewable bundle.

`green-agent.json5` is the registered AgentBeats green manifest. It embeds the
worker process, defaults to `skillsbench-v1.1`, shards the 87-task set across
seven shards, and carries the same 87-image map as
`prebuilt_images/skillsbench-v1.1.json`. The workflow can still inject a smaller
task set, such as `smoke`, for maintainer evidence runs.

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
- `scenario-standard-v1.json5`: legacy staged full-mode scenario retained for
  comparison; `skillsbench-v1.1` is the current promotion target.
- `.github/workflows/quick-submit.yml`: AgentBeats Quick Submit entrypoint. It
  calls the official AgentBeats leaderboard template runner required by the live
  Quick Submit service.
- `.github/workflows/run-agent-under-test-smoke.yml`: maintainer one-task smoke
  for proving the configurable purple image without changing the default
  five-task deployment smoke.
- `.github/workflows/run-scenario.yml`: maintainer self-run workflow with
  SkillsBench-specific task-set and result-shape checks.
- `task_sets/deploy-smoke-v1.json`: canonical five-task task-set manifest.
- `task_sets/smoke.json`: one-task public-readiness smoke manifest used by
  evidence validation.
- `task_sets/standard-v1.json`: legacy generated full public task-set manifest.
- `task_sets/skillsbench-v1.1.json`: generated 87-task public task-set
  manifest for the next AgentBeats deployment.
- `prebuilt_images/deploy-smoke-v1.json`: digest-pinned task environment images.
- `prebuilt_images/standard-v1.json`: legacy generated full public task-image
  map.
- `prebuilt_images/skillsbench-v1.1.json`: full digest-pinned task-image map
  for `skillsbench-v1.1`.
- `deploy_bundles/skillsbench-v1.1.json`: deploy-ready bundle tying the runtime
  source revision, runtime image digests, task-set digest, and 87 prebuilt task
  images.
- `queries/*.sql`: DuckDB leaderboard queries. The first column is the
  AgentBeats purple-agent UUID.
- `results/`: merged public result JSON files read by AgentBeats.
- `submissions/`: submitted scenario/provenance files.

## Runtime Images

Current public digest-pinned images:

- green with embedded worker:
  `ghcr.io/benchflow-ai/skillsbench-agentbeats-worker@sha256:21047d9bb768b5aaf0cff83cf9891b8c297db3d43485448625098da8cce87037`
- standalone worker:
  `ghcr.io/benchflow-ai/skillsbench-agentbeats-worker@sha256:21047d9bb768b5aaf0cff83cf9891b8c297db3d43485448625098da8cce87037`
- standalone green:
  `ghcr.io/benchflow-ai/skillsbench-agentbeats-green@sha256:70a5096a071c7bcfa6ea733c7d304aca62d8ba2d52f003c140c4e0cf1cc8f29d`
- purple baseline:
  `ghcr.io/benchflow-ai/skillsbench-agentbeats-purple@sha256:f3f994b10a3d62d94c544e4f77268909fafd14a7b38985302c237698227f358b`
- purple agent-under-test:
  `ghcr.io/benchflow-ai/skillsbench-agentbeats-purple@sha256:f3f994b10a3d62d94c544e4f77268909fafd14a7b38985302c237698227f358b`
- task environments:
  `prebuilt_images/skillsbench-v1.1.json`
- deploy bundle:
  `deploy_bundles/skillsbench-v1.1.json`

The five `deploy-smoke-v1` task environment refs and all 87
`skillsbench-v1.1` task environment refs are public, digest-pinned entries under
the shared `ghcr.io/benchflow-ai/skillsbench-task-env` GHCR package. The
`skillsbench-v1.1` worker path verifies that every referenced prebuilt image is
present and usable before running public-readiness evaluations.

The refreshed `skillsbench-v1.1` prebuilt map combines new images for the 16
changed task environments from source workflow run
`https://github.com/benchflow-ai/skillsbench/actions/runs/27652719005` with the
previously verified images for unchanged tasks. That source workflow failed only
on the unchanged `earthquake-phase-association` task while downloading an
external SeisBench model; its task digest and retained image digest did not
change.

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
- current task set: `skillsbench-v1.1`
- deploy bundle: `deploy_bundles/skillsbench-v1.1.json`
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

The current v1.1 runtime images and task manifests were built from
branch-scoped source work, not from direct changes to official `main` branches:

- `benchflow-ai/skillsbench:codex/skillsbench-agentbeats-v1-1-update`
- `benchflow-ai/skillsbench-leaderboard:agentbeats/sync-skillsbench-v1.1`

A2A is the AgentBeats participant protocol boundary. ACP remains BenchFlow's
coding-agent transport.

## skillsbench-v1.1 Full Mode

Full public task-set updates should originate from `benchflow-ai/skillsbench`,
not manual edits in this repo. The v1.1 source branch generated the public
task-set manifest, built the runtime images, built all task environment images,
and exported a deploy bundle for review.

- `task_sets/skillsbench-v1.1.json`
- `task_sets/skillsbench-v1.1.source.json`
- `prebuilt_images/skillsbench-v1.1.json`
- `deploy_bundles/skillsbench-v1.1.json`

Current v1.1 verification target:

- JSON files parse.
- `task_sets/skillsbench-v1.1.json` has 87 public tasks.
- No `tasks_excluded/` ids are present.
- `task_set: "skillsbench-v1.1"` selects the generated public task set.
- `num_shards` and `shard_index` deterministically split the selected task ids.
- All 87 prebuilt task environment refs are digest-pinned and public.
- The registered green manifest embeds the worker and carries the 87-image map.
- No full 87-task AgentBeats scoring run has been run yet.

The green, worker, purple, and task environment images have been built and
published from the source branch. The remaining production gate is to provision
durable private-proof storage and run the registered AgentBeats smoke/scoring
path with `skillsbench-v1.1`.

## Current Deployment State

Deploy-ready now:

- `deploy-smoke-v1` five-task AgentBeats adoption.
- Official Quick Submit path through
  `RDI-Foundation/agentbeats-leaderboard-template/.github/workflows/quick-submit-runner.yml@v2`.
- BenchFlow-owned runtime images and the shared five-task task-env package refs.
- Leaderboard queries for flat and nested AgentBeats result payloads.

Configured for full AgentBeats submission, but not fully deploy-verified:

- `skillsbench-v1.1` task-set manifest with 87 public tasks.
- Digest-pinned prebuilt image map for all 87 task environment images.
- Embedded-green source branch support for `task_set: "skillsbench-v1.1"`,
  deterministic sharding, durable private proof, and prebuilt image verification.
- Generic purple agent-under-test support for `openhands`, `opencode`,
  `claude-code`, `codex`, `gemini-cli`, `terminus`, and `pi` in one image.
- `green-agent.json5` as the AgentBeats-registered full-mode manifest for 87
  public tasks and seven shards.

Explicit full-submission status:

- 87 public tasks are configured for the green AgentBeats manifest.
- Existing proof covers the five-task AgentBeats adoption path, the one-task
  generic-purple path, and one-task v1.1 workflow smoke runs from the current
  branch.
- A complete 87-task AgentBeats evaluation has not been run.
- Submit full mode only after durable private-proof storage is provisioned and
  the registered AgentBeats IDs are confirmed against the digest-pinned
  manifests.

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

Run the current v1.1 one-task public-readiness smoke from this branch:

```bash
gh workflow run run-scenario.yml \
  --repo benchflow-ai/skillsbench-leaderboard \
  --ref agentbeats/sync-skillsbench-v1.1 \
  -f task_set=smoke \
  -f num_shards=1 \
  -f green_agent_id=019e4ecb-4b5b-7481-b6f4-85ad93336437 \
  -f purple_agent_id=019e4ed1-d333-7133-807f-5f22c04d5eef \
  -f require_durable_private_proof=false
```

Latest current-branch smoke evidence on the refreshed v1.1 artifacts:

- workflow commit:
  `171b1e1bc4e6b9084c1a00f36a2a85657d2b1159`
- non-durable workflow run:
  `https://github.com/benchflow-ai/skillsbench-leaderboard/actions/runs/27658062720`
- non-durable submission branch:
  `submission-benchflow-ai-20260617-005232`
- durable Supabase S3 workflow run:
  `https://github.com/benchflow-ai/skillsbench-leaderboard/actions/runs/27658063549`
- durable submission branch:
  `submission-benchflow-ai-20260617-005111`
- durable private proof:
  `submissions/benchflow-ai-20260617-005111-private-proof-manifest-refs.json`
  records a `90d` retained `s3://agentbeats-private-proof/...` proof manifest
  ref, and the referenced Supabase Storage object was verified with the S3 API.
- result status:
  both runs produced one flattened `citation-check` row for
  `task_set: "smoke"` with the expected `verifier_error` non-score outcome and
  digest-pinned worker/purple image provenance.

For public-readiness runs, set `require_durable_private_proof=true` and provide
a durable `private_proof_uri_prefix` using `s3://`, `gs://`, or `r2://`. The
self-run workflow copies worker proof manifests out of the running
SkillsBench container before teardown, publishes the proof directory to that
private storage prefix, and uploads only
`private-proof-manifest-refs.json` with the shard artifacts. The summary job
also commits those refs under
`submissions/*-private-proof-manifest-refs.json` for durable evidence assembly.

Supported proof publishing configuration:

- `s3://...`: configure `SKILLSBENCH_PRIVATE_PROOF_AWS_ACCESS_KEY_ID` and
  `SKILLSBENCH_PRIVATE_PROOF_AWS_SECRET_ACCESS_KEY`, or the standard
  `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` secrets. Optionally set
  `SKILLSBENCH_PRIVATE_PROOF_AWS_REGION`. For S3-compatible storage such as
  Supabase Storage, also set `SKILLSBENCH_PRIVATE_PROOF_S3_ENDPOINT_URL`.
- `r2://...`: configure the same S3-compatible credentials plus
  `SKILLSBENCH_PRIVATE_PROOF_R2_ENDPOINT_URL` or `R2_ENDPOINT_URL`.
- `gs://...`: configure GitHub OIDC to GCP Workload Identity and set repository
  variables `SKILLSBENCH_GCP_PROJECT_ID`, `SKILLSBENCH_GCP_WIF_PROVIDER`, and
  `SKILLSBENCH_PRIVATE_PROOF_GCP_SERVICE_ACCOUNT`. The service account must be
  able to write objects under the configured private GCS proof prefix.

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
smoke at one shard. `skillsbench-v1.1` full-mode submissions must carry their
own `task_set: "skillsbench-v1.1"` and `num_shards: 7` assessment config,
matching the Terminal-Bench-style pattern for larger task sets.

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

- `green-agent.json5` on `main` uses the digest-pinned v1.1 worker image and
  embedded 87-image prebuilt map from `deploy_bundles/skillsbench-v1.1.json`.
- `task_sets/skillsbench-v1.1.json` has 87 public tasks and task-set digest
  `sha256:3c9432bb1a4bd1b66ddbc175bb1f43bf546f7de663d1b2aa0327a88bff7ecd39`.
- Official `main` self-run succeeds with registered green and purple IDs.
- Generated result has exactly five public flattened rows.
- Public rows have `score_eligible: true`, `infra_failure_type: null`, and
  `agent_transport: "a2a"`.
- Public rows do not expose hidden tests, solutions, credentials, raw logs,
  local paths, or private proof.
- Durable private proof storage is configured with an `s3://`, `r2://`, or
  `gs://` prefix, and durable runs commit only
  `submissions/*-private-proof-manifest-refs.json`.
- DuckDB queries return the registered purple AgentBeats UUID as the first
  column.
- Generated result branch is merged into `main` so AgentBeats can read
  `results/*.json`.
- AgentBeats green registration points to
  `https://github.com/benchflow-ai/skillsbench-leaderboard`.
- After merge, AgentBeats UI reads the updated leaderboard `main` commit and
  renders overall, category, and difficulty leaderboard rows.
- Quick Submit GitHub App connection is approved for
  `benchflow-ai/skillsbench-leaderboard`; rerun a live submit smoke after
  manifest updates.
- `skillsbench-v1.1` full adoption remains prepared but not fully verified
  until a durable registered-ID smoke and the canonical 87-task scoring run pass
  with the published green/worker image.
