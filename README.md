# SkillsBench AgentBeats Leaderboard

Standalone AgentBeats leaderboard repository for the initial five-task
SkillsBench deployment smoke. This repo is the AgentBeats-facing surface; the
source SkillsBench and BenchFlow repos remain unchanged on `main`.

## Scope

The checked-in scenario defaults to `deploy-smoke-v1`:

- `citation-check`
- `court-form-filling`
- `dialogue-parser`
- `offer-letter-generator`
- `powerlifting-coef-calc`

This is not the full `standard-v1` launch. It is the minimal public deployment
gate for proving the SkillsBench green agent, worker, A2A participant boundary,
result shape, and leaderboard queries.

## Files

- `scenario.json5`: Amber scenario for the five-task worker-backed run.
- `green-agent.json5`: SkillsBench green-agent component manifest.
- `worker.json5`: SkillsBench worker component manifest.
- `participant-placeholder.json5`: baseline purple participant manifest.
- `.github/workflows/run-scenario.yml`: maintainer self-run workflow.
- `.github/workflows/quick-submit.yml`: AgentBeats Quick Submit entrypoint.
- `.github/workflows/quick-submit-runner.yml`: repo-local runner for the
  minimal SkillsBench adoption. It preserves the flattened public row contract
  and prebuilt task-image checks used by the self-run workflow.
- `task_sets/deploy-smoke-v1.json`: canonical five-task task-set manifest.
- `prebuilt_images/deploy-smoke-v1.json`: digest-pinned task environment images.
- `queries/*.sql`: DuckDB leaderboard queries. The first column is the
  AgentBeats purple-agent UUID.
- `results/`: merged public result JSON files read by AgentBeats.
- `submissions/`: submitted scenario/provenance files.

## Runtime Images

Current public digest-pinned images:

- green:
  `ghcr.io/yiminnn/skillsbench-agentbeats-green@sha256:6148aab94ee1868157429815e6ceb718f445dce047e07d5081c50f9c75ffe803`
- worker:
  `ghcr.io/yiminnn/skillsbench-agentbeats-worker@sha256:21d157ffd06f06ff38bcd5e56a15d92d958ad88ff7f1db9db1afc5ae90eb0b9a`
- task environments:
  `prebuilt_images/deploy-smoke-v1.json`

The image namespace can be republished under `ghcr.io/benchflow-ai` later, but
that is not required for the five-task AgentBeats deployment as long as these
digests remain public.

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

## Source Branches

The runtime images were built from branch-scoped source work, not from direct
changes to official `main` branches:

- `benchflow-ai/skillsbench:codex/agentbeats-green-agent-runtime`
- `benchflow-ai/benchflow:codex/agentbeats-a2a-adapter-audit`

A2A is the AgentBeats participant protocol boundary. ACP remains BenchFlow's
coding-agent transport.

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

This repo keeps Quick Submit self-contained for the minimal SkillsBench
adoption:

```yaml
uses: ./.github/workflows/quick-submit-runner.yml
```

Local staging already proved that the SkillsBench scenario compiles from
`submissions/*.json` when manifests use branch-hosted raw GitHub URLs. Live
Quick Submit still requires the AgentBeats green registration to point at this
repo and the AgentBeats GitHub App/backend-created PR path. Until AgentBeats
creates a `quick-submit-<uuid>` PR and backend secret record, the Quick Submit
runner cannot complete a live submission by design.

## Leaderboard Queries

AgentBeats reads `results/*.json` with DuckDB. Validate locally:

```bash
uv run python - <<'PY'
from pathlib import Path
import duckdb

result = Path("/tmp/skillsbench-agentbeats-official-run/submission/result.json")
agent_id = "019e4ed1-d333-7133-807f-5f22c04d5eef"
con = duckdb.connect(":memory:")
try:
    con.execute("CREATE TABLE results AS SELECT * FROM read_json_auto(?, filename = true)", [str(result)])
    for name in ["overall", "by_category", "by_difficulty"]:
        rows = con.execute((Path("queries") / f"{name}.sql").read_text()).fetchall()
        if not rows or not any(row and row[0] == agent_id for row in rows):
            raise SystemExit(f"{name} query failed registered-id check: {rows}")
    print("queries verified")
finally:
    con.close()
PY
```

## Official Deployment Checklist

- `scenario.json5` on `main` uses this repo's raw manifest URLs.
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
- Quick Submit is live-tested, or any remaining AgentBeats-side blocker is
  documented with the exact workflow/PR/error evidence.
