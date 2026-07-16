# SkillsBench skill-eval worker

The compute side of the [Skill Leaderboard](../../docs/skill-leaderboard-design.md).
A runner **you own** (with real Docker) that consumes the submission queue,
**replays the submitter's uploaded trajectories** in the sealed task containers,
runs the verifiers, and writes the results both surfaces render.

Submission model: the user uploads a skill bundle **plus two trajectories** —
their agent solving the suite WITHOUT the skill and WITH it — **plus their
per-task scores**. The Space publishes the claimed lift immediately as
`attestation="self-reported"` (grey, unranked); this worker then replays,
verifies, recomputes rewards from raw test counts, and **replaces the row in
place** with `attestation="replayed"` — the only ranked tier. The worker never
generates trajectories (no LLM calls, no API cost on our side).

```
HF Dataset benchflow/skill-leaderboard        (all paths keyed by submission_id,
                                               the uuid the Space mints at submit)
  queue/<submission_id>.json          ── worker.py claims oldest queued ──┐
  skills/<submission_id>/bundle.zip   ── validate bundle                  │
  trajectories/<submission_id>/       ── fetch no.zip + with.zip          │
                                                                ▼
                     replay ×2 + verify  (87 tasks, 1 trial/condition, --sandbox docker)
                                                                │
                     reward.py  (0.8·pass_frac + 0.2·efficiency, or binary)
                     metrics.compute_lift  (Δ, g, paired CI, significance)
                                                                ▼
  results.parquet  (per-task raw)   board.parquet  (one aggregated row / skill)
                                                                │
                     publish.py  ── transcode (no math) ──▶ website-data/skill-leaderboard.json
                                                             (commit to skillsbench-trajectories;
                                                              website build fetches it)
```

## Why a separate runner (not the Space)

HF Spaces (and HF Jobs) can't run privileged Docker-in-Docker, and each task
replay runs in the task's own Docker container. So the replay+verify runs here —
a cheap VM or a self-hosted CI runner — while the HF Space stays a light
submit/board UI.

## Files

| File | Role |
| --- | --- |
| `worker.py` | poll → claim → replay ×2 → verify → aggregate → write parquets |
| `reward.py` | per-task reward from raw test counts (fractional + efficiency, or official binary) — never taken from the submitter |
| `metrics.py` | **single source of truth** for lift Δ, gain g, task-level CIs, significance (mirrors `website/src/data/leaderboard-data.ts`) |
| `publish.py` | transcode `board.parquet` → website snapshot JSON (no math) |

## Run

```bash
pip install -r requirements.txt
uv tool install "benchflow>=0.6.2,<0.7"     # the `bench` CLI
export HF_TOKEN=hf_...                        # write token for the dataset
export TASKS_DIR=/path/to/skillsbench/tasks   # pinned roster (git tag v1.1)
python worker.py                              # long-running loop

# after results land (or on a schedule / in trajectories-repo CI):
python publish.py --out website-data/skill-leaderboard.json
```

## ⚠ Integration points to confirm against your `bench` CLI

Marked `# ⚠ ADAPT` in `worker.py`:

- **Replay subcommand** — `replay_and_verify` shells out to
  `bench eval replay --trajectory <dir>`; confirm the real subcommand and its
  trajectory format. This is the load-bearing assumption of the whole model.
- **Output layout** — `parse_test_counts` prefers per-task `ctrf.json` under the
  output dir, falls back to pytest log lines; confirm what the verifier emits.
- **Invocation** — `invocation_rate` returns `None` (blank column) until you
  wire a trajectory scan for "did the agent open the skill".

Everything downstream of rewards (metrics, parquet schema, publish, both
surfaces) is independent of these and already consistent.

## Key invariants

- The worker is the **only writer** of `results.parquet` and the **only
  producer of `attestation="replayed"` rows** in `board.parquet`. The Space may
  only write `self-reported` rows (published claims); it must never mint a
  verified badge. If submitters' numbers ever reached the verified tier, the
  trust model would collapse.
- `metrics.py` is the **only** lift/CI math, mirrored byte-for-byte in the
  Space (`integrations/skill-leaderboard-space/metrics.py`) so self-reported
  claims are aggregated identically to verified results — keep the two copies
  in sync. The Space and website just display `board.parquet` — never
  recompute.
- Verification **upgrades in place**: `persist()` drops any existing row with
  the same `submission_id` (the Space's self-reported row) before appending
  the replayed row. `skill_hash` stays a manifest/integrity field — each
  submission is its own row.
- **Name privacy**: `display_name()` mirrors the Space's rule — when the queue
  record has `show_name: false`, write `skill-<submission_id[:8]>`, never the
  real name, or the verification upgrade would leak it.
- `publish.py` does **no math** — pure reshape — so the website can't drift from
  the Space.
