# Community Skill Leaderboard — Design

Status: proposed · Owner: TBD · Dataset namespace: `skillsbench@1.1`

A second leaderboard for SkillsBench. Today [`/leaderboard`](../website/src/app/(main)/leaderboard/page.tsx)
answers *"which **agent** is best?"* This adds a sibling board that answers
*"which **community-submitted skill** lifts an agent the most?"* — same lift
math (`Δ`, normalized gain `g`), but the ranked unit is a user-uploaded skill
instead of a model.

The website stays a **pure static consumer**. All compute and state live on
HuggingFace; the site reads a build-time snapshot — the same pipeline the agent
board already uses ([`scripts/generate-results-registry.ts`](../website/scripts/generate-results-registry.ts)
→ snapshot JSON → static page).

## Decisions (locked)

| Question | Choice | Consequence |
| --- | --- | --- |
| How is a submitted skill scored? | **Replay + verify uploaded trajectories** | The submitter runs their own agent on the suite twice (without / with the skill) and uploads the skill bundle **plus both trajectories**. Our worker replays each trajectory inside the sealed task containers and runs the verifiers — no LLM compute on our side; the submitter bears their own agent cost. |
| What is each submission benchmarked against? | **All 87 tasks × 1 trial per condition** | 174 sandboxed replay+verify runs per submission. The task suite, containers and verifiers are pinned by us; the *agent* that produced the trajectories is self-reported in the manifest. |
| Integrity model | **Private skill, public score** | Skill source is never published; only the measured `Δ` + a run manifest are. Trust comes from controlling the replay environment and the verifier, not the source. |
| What shows before the worker verifies (phase 0)? | **Two-tier attestation: self-reported → replayed** | Submissions also carry the submitter's per-task `scores.json`. The Space publishes the claimed lift **immediately** as `attestation="self-reported"` — grey, unranked, clearly badged. The worker later replays + verifies and **replaces the row in place** with `attestation="replayed"`, the only ranked tier. The board is live before the worker exists, without ever presenting a claim as a verified result. |

## Data flow

```
                         ┌─────────────────────── HuggingFace ───────────────────────┐
 user                    │                                                            │
  │  1. upload skill.zip  │   HF Space (Gradio, submit + board UI)                     │
  │     + 2 trajectories  │   ┌──────────────┐   ┌─────────────────────────────────┐  │
  └──────────────────────▶│   │ Gradio submit │──▶│ job queue (HF Dataset: queue/)  │  │
       (web form on site) │   │  tab / API    │   └─────────────────────────────────┘  │
                          │   └──────────────┘              │ worker polls              │
  ◀── 2. job id + status ─┤          ▲                      ▼                           │
                          │          │         ┌─────────────────────────────┐         │
  ◀── 3. poll status ─────┤          └─────────│ worker (external VM):        │         │
                          │   status reads     │  replay ×2 + verify          │         │
                          │                    │  87 tasks × 1 trial, sealed  │         │
                          │                    └─────────────┬───────────────┘         │
                          │                                  ▼                          │
                          │                    ┌─────────────────────────────┐         │
                          │                    │ HF Dataset: skill-leaderboard│        │
                          │                    │  results.parquet (public)    │         │
                          │                    │  skills/<id>/ (PRIVATE)      │         │
                          │                    └─────────────┬───────────────┘         │
                          └──────────────────────────────────┼─────────────────────────┘
                                                              │ nightly / on-complete
                                    ┌─────────────────────────▼──────────────────────┐
                                    │ skillsbench-trajectories repo                   │
                                    │  website-data/skill-leaderboard.json (snapshot) │
                                    └─────────────────────────┬──────────────────────┘
                                                              │ build-time fetch
                                    ┌─────────────────────────▼──────────────────────┐
                                    │ website (static): /skill-leaderboard            │
                                    └─────────────────────────────────────────────────┘
```

Two distinct reads of the data, deliberately:

- **Live status** (queued / running / done, queue position) — the site calls
  the Space API client-side. Cheap, ephemeral, fine if it's briefly unavailable.
- **The board itself** — a build-time snapshot, like everything else on the
  site. The leaderboard is *content*, not a live query; it must not depend on
  the Space being warm.

## Surfaces — two readers, one dataset

The board is rendered in **two places**, both live, both reading the same
aggregated `board.parquet`:

1. **Website board** (`skillsbench.ai/skill-leaderboard`) — the on-brand,
   on-domain surface. Built from a snapshot, exactly like the agent board.
   Source of truth on the site for SEO and brand.
2. **HF Gradio Space** (`huggingface.co/spaces/benchflow/skill-leaderboard`) —
   the Hub-discoverable surface + the submission door (HF OAuth). See
   [`integrations/skill-leaderboard-space/`](../integrations/skill-leaderboard-space/).

```
                          benchflow/skill-leaderboard  (HF Dataset)
                                     board.parquet
                                    /             \
              build-time snapshot /               \ read on load
                                 ▼                  ▼
   website-data/skill-leaderboard.json        HF Gradio Space
                                 │             (reads parquet directly)
                                 ▼
   skillsbench.ai/skill-leaderboard
```

**No-drift rule:** `board.parquet` is the *only* aggregation. The website
snapshot is a pure transcode of it (a publish step in the trajectories repo
converts `board.parquet` → `skill-leaderboard.json`), and the Space reads the
same parquet directly. Neither surface recomputes lift/CI — that lives once in
the worker. Both surfaces cross-link each other so a visitor on either can reach
the other.

The two surfaces differ only in *freshness*: the Space is live (updates when the
dataset commits), the website updates on snapshot refresh + rebuild. That lag is
acceptable and expected — they show the same numbers, the Space just shows them
sooner.

## HuggingFace backend

### One Space — `benchflow/skill-leaderboard` (Gradio) — UI only, no compute

The Space is the submission door + the Hub-side board. Submission validates the
three uploads (skill bundle + two trajectory zips), writes them and a job record
into the dataset, and returns a `job_id`. Status reads come from the same queue
records.

The replay+verify compute does **not** run in the Space: HF Spaces (and HF
Jobs) cannot spawn nested Docker containers, and every task replay needs the
task's own sealed container. The worker is a separate process on hardware we
own (a small VM — see `integrations/skill-eval-worker/README.md`), polling the
queue. Single-worker FIFO to start; the queue dataset is the source of truth,
so the worker is restart-safe.

### One Dataset — `benchflow/skill-leaderboard`

Three areas:

Everything a submission stores is keyed by a **`submission_id`** — a unique id
(uuid) the Space mints at submit time, the primary key across the dataset and
the board. `skill_hash` (sha256 of the bundle) is recorded alongside as the
integrity anchor, but resubmitting the same bundle mints a new id and a new
row.

- `queue/<submission_id>.json` — job records and lifecycle state (one file per
  submission, append-only). Also holds the submitter's **real skill name** when
  they opt out of showing it publicly (never displayed).
- `skills/<submission_id>/` — **private**: the uploaded skill bundle. Never
  served to the site.
- `trajectories/<submission_id>/no.zip`, `…/with.zip` — **private**: the two
  uploaded trajectories the worker replays.
- `scores/<submission_id>/scores.json` — **private**: the submitter's per-task
  rewards (both conditions) backing their self-reported row; the audit trail
  for the claim.
- `results.parquet` — **public**: per-(submission, task, condition) raw scores.
  Worker-only — self-reported submissions never write here.
- `board.parquet` — **public**: one aggregated row per **submission** (`no`,
  `with`, `delta`, `g`, CIs, `significant`, `attestation`, manifest), keyed by
  `submission_id`. Verified rows are computed by the worker from
  `results.parquet`; self-reported rows are written once by the Space at
  submit time (from `scores.json`, same `metrics.py` math) and replaced in
  place on verification. This is the single source both surfaces render (see
  "Surfaces" below).

### Eval worker — per submission (replay + verify)

```
1. fetch skills/<submission_id>/bundle.zip
         + trajectories/<submission_id>/{no,with}.zip
      →  validate (SKILL.md present, size caps, safe archive paths)
2. pin: dataset@v1.1 (87 tasks, git tag), task images, verifiers, seed
3. replay A: bench eval replay --tasks-dir <all 87> --trajectory no/ \
                --sandbox docker                                 # 87 sealed containers
   replay B: bench eval replay ... --trajectory with/            # 87 sealed containers
4. run each task's verifier on the replayed state → CTRF test counts
5. reward.py per task  →  no/with reward in [0,1]
      (0.8·pass_frac + 0.2·efficiency, or binary all-or-nothing)
6. metrics.compute_lift  →  Δ, g, paired CI, significance
      →  results.parquet + board.parquet, status=done
```

174 sandboxed replay+verify runs per submission (87 × 2 conditions × 1 trial) —
container time only, **no LLM calls on our side**; the submitter runs their own
agent to produce the trajectories. What keeps rows comparable is the pinned
dataset tag + our containers + our verifiers; the *agent* axis is self-reported
in the manifest, not enforced.

## The "1 trial" decision — and why it's statistically sound

SkillsBench confidence intervals already come from spread **across the 87
tasks**, not from repeated trials — "Method D":
`CI = 1.96·stdev(per-task means)/√87` (see
[`website/src/data/leaderboard-data.ts`](../website/src/data/leaderboard-data.ts)).
So with 1 trial per task we still get:

- a task-macro mean per condition (mean of 87 per-task rewards),
- a legitimate 95% task-level CI,
- a `Δ` and a normalized gain `g`.

What we lose is per-task trial-variance smoothing — a task whose reward is noisy
run-to-run adds noise. Mitigations:

- Report the CI honestly (the board already renders CIs).
- Flag any skill whose `Δ` is within its CI of zero as **"not significant"**
  rather than ranking it.

Our cost per submission is container replay + verification only — no LLM
tokens. The submitter bears the cost of generating their own two trajectory
sets.

## Metrics (reuse existing definitions exactly)

Per-task reward (computed by `reward.py` from the verifier's raw test counts,
never taken from the submitter):

- default `reward = 0.8·pass_frac + 0.2·efficiency` (Terminal-Bench-style
  fractional scoring; efficiency only modulates within `[0.8·pf, pf]`, so
  correctness always dominates; missing runtime never penalizes);
- `REWARD_BINARY=1` switches to the official all-or-nothing metric.

Over the 87-task suite:

- `no   = mean_t(reward_no[t]) × 100`
- `with = mean_t(reward_with[t]) × 100`
- `delta = with − no` (percentage points) — **primary sort**
- `g = (with − no) / (100 − no) × 100` — normalized gain; fair to skills tested
  on a strong baseline
- `ci` — task-level 95% CI on each condition; `significant = delta − deltaCi > 0`
- `invocation` — fraction of with-skill tasks where the agent actually opened the
  skill (already tracked in the pipeline) — surfaces "skill never fired" cases.

Identical math to the agent board, so the two boards read against each other.

## Trust model — private skill, public score

The skill source is **never published**. To keep a private-source board from
being unfalsifiable, integrity comes from controlling the *replay environment
and the verifier*, not the source:

- The submitter never produces the **number**: the worker replays the uploaded
  trajectories inside our sealed task containers and our verifiers compute the
  test counts; `reward.py` recomputes the reward from raw counts. A submitter
  cannot inflate a score they don't compute.
- What the submitter **does** control is trajectory *generation* — they run
  their own agent. That is one trust notch below running the agent ourselves,
  and the badge wording reflects it: **"verified — replayed"**, not
  "runner-attested".
- Each result row carries a **run manifest**: `submission_id` (the storage
  primary key), `skill_hash` (sha256 of the bundle), `dataset_tag`, `agent`
  (self-reported), `worker_commit`, `seed`, `timestamp`. Published with the
  score; the bundle and trajectories stay private.
- **Optional name privacy** — the submitter chooses whether the skill name is
  shown publicly. When hidden, both surfaces render `skill-<submission_id[:8]>`
  and the real name lives only in the private queue record; the worker applies
  the same rule on verification so the upgrade can't leak it. Author, score and
  manifest are always public.
- **Anti-gaming guards in the worker:**
  - Replay containers have **no network egress** → nothing phones home or
    fetches answers during verification.
  - Skill + trajectory **size caps**, safe-archive checks; reject bundles that
    embed task-specific answers (heuristic: flag task-id strings / verifier
    fixtures).
  - **Cherry-picking** is the model's main residual risk: a submitter can
    regenerate trajectories many times and upload the best pair. Mitigations:
    the paired CI already prices in per-task noise (a lucky pair rarely stays
    significant across 87 tasks); trajectory hashes go in the manifest; V2 adds
    spot-check re-scoring of top rows with an agent we run ourselves.
  - **Re-replay on dispute** — because the `submission_id` pins the exact
    stored bundle + trajectories (with `skill_hash` / trajectory hashes as
    integrity anchors), anyone can request a re-replay of the exact submission.
  - **Dedup (cost, not identity)** — every submission is its own row (unique
    `submission_id`), but the worker may reuse cached verified results when
    the (`skill_hash`, trajectory hashes) triple matches a prior submission —
    no re-spend on identical content.
- **Display** — each row shows a **"verified — replayed"** badge and the
  manifest, with a one-line "source private · trajectories submitter-generated"
  note (vs the agent board's "reproducible from public dataset"). This is the
  honest framing of the weaker trust this corner accepts.

Future-proofing for the path not chosen: keep a `visibility: public | private`
column so a later "public skills" tier can light up a stronger "reproducible"
badge with no schema change.

## Two-tier attestation — self-reported → replayed (phase 0)

So the board can go live before the replay worker does, every submission also
uploads the submitter's per-task `scores.json`
(`{"no": {task: reward…}, "with": {…}}`, rewards in `[0,1]`). The Space
validates it, computes the lift with the **same `metrics.py`** the worker uses
(mirrored into the Space, kept in sync), and publishes the row immediately with
`attestation="self-reported"`.

- **Self-reported rows are claims, not results.** Both surfaces render them
  grey, **never ranked** (rank "—"), with an explicit "self-reported —
  verification pending" badge and an unverified-tier banner. Ranking is
  reserved for `attestation="replayed"`.
- **Full-suite rule.** `scores.json` must score **every task of the pinned
  suite in both conditions** — a claim can't inflate its macro mean by
  cherry-picking a favorable subset. The website form validates the task ids
  against the tasks registry (missing/unknown ids rejected client-side); the
  Space re-enforces count + set equality server-side (`TASK_COUNT`).
- **Upgrade in place.** The job still enters the verification queue. When the
  worker processes it, `persist()` drops the row by `skill_hash` and writes the
  verified row — same schema, new provenance. If verification fails, the row
  stays self-reported.
- **Writer rule (amended).** The worker remains the only writer of
  `results.parquet` and the only producer of `replayed` rows. The Space may
  write **only** `self-reported` board rows. No path exists from a submitter's
  numbers to a verified badge.
- **Same math both tiers.** Because the Space aggregates `scores.json` with the
  worker's exact metrics, verifying a row changes its provenance (and possibly
  its numbers, if the claim was wrong) — never its schema or interpretation.
  Comparing a row's self-reported claim to its later verified score is itself a
  useful honesty signal (V2: surface the discrepancy).

## Frontend

New route, mirroring the existing leaderboard so it inherits the look and the
snapshot pipeline:

```
website/src/app/(main)/skill-leaderboard/
  page.tsx                       # metadata + <SkillLeaderboardClient/>
  skill-leaderboard-client.tsx   # header + board + submit CTA
  submit/page.tsx                # upload form (skill.zip + name/author/desc/domain)
website/src/components/
  SkillLeaderboard.tsx           # table — adapt Leaderboard.tsx columns
  SkillSubmitForm.tsx            # client form → POST to HF Space
  SubmissionStatus.tsx           # poll GET /status/{job_id}, show queue pos/progress
website/src/data/skill-leaderboard-data.ts   # types + dataset descriptor
website/src/data/skill-leaderboard.json      # build-time snapshot (generated)
website/scripts/generate-skill-leaderboard.ts # fetch website-data/skill-leaderboard.json
```

Wire-ups:

- Add `{ href: "/skill-leaderboard", label: "Skill Board" }` to the `navItems`
  in [`website/src/components/Navbar.tsx`](../website/src/components/Navbar.tsx).
- Add a `generate-skill-leaderboard` step to the build script in
  [`website/package.json`](../website/package.json) (same pattern as
  `generate-results`).

**Board layout** — clone [`Leaderboard.tsx`](../website/src/components/Leaderboard.tsx),
swap the columns:

| # | Skill | Author | Without | With | Δ (pp) | Gain g | Invoc. | bar viz |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

- Default sort by **Δ**; toggles for `g` and `With`. Reuse the existing bar/CI
  rendering (`ConditionBar`, the gain-delta bar) verbatim — it already
  visualizes baseline → with.
- A **provenance header chip** (dataset v1.1 · 87 tasks · 1 trial · replayed &
  verified by the SkillsBench runner) so readers know what is controlled — the
  suite and verification — and that the agent column is self-reported.
- Rows within-CI-of-zero render greyed with a "not significant" tag instead of a
  rank number.
- Self-reported rows render greyed with an amber "self-reported" tag, never a
  rank number, sorted below every verified row; a banner above the table counts
  them. Their expanded view shows "self-reported — replay verification
  pending" instead of the verified badge.
- Each row expands to the run manifest + "source private" note + a **"Request
  re-run"** link (verified rows only).

**Submit flow** (`/skill-leaderboard/submit`): drag-drop `skill.zip`, the two
trajectory zips and `scores.json`; fields `name / author / agent / short
description / target domain (optional)`; a "show the skill name publicly"
toggle (off → the row appears as `skill-<submission-id>`); a checkbox
acknowledging "source stays private; the claimed score publishes immediately as
self-reported and is replaced by the verified score"; → `POST /submit` →
`{ submission_id }` (the storage primary key) → status view that polls the
Space by that id. Friendly states: `published (self-reported) · queued for
verification (position N)`, `running task 41/87`, `done → row upgraded to
verified`, `failed (reason — row stays self-reported)`.

## Lifecycle & ops

- **Snapshot refresh** — a scheduled job (nightly, or on worker-completion
  webhook) regenerates `website-data/skill-leaderboard.json` from
  `results.parquet` and commits to the trajectories repo → triggers a site
  rebuild. New skills appear within the refresh window; the board stays off the
  Space's critical path.
- **Versioning** — the board is namespaced to `skillsbench@1.1` like the agent
  board (see [`dataset-versioning.md`](dataset-versioning.md)). When the dataset
  bumps, start a new namespace; the old board stays visible but flagged
  `superseded` (the component already supports this via `supersededBy`).
- **Cost control** — FIFO single worker, content-hash result cache (identical
  bundle+trajectories skip the replay), per-author rate limit, daily job cap.
  ~174 task-runs/submission is the budget knob.
- **Abuse** — size caps, no-egress sandbox, optional lightweight auth (HF login)
  on submit to rate-limit.

## Phasing

0. **Phase 0 (no worker yet)** — Space (submit + board) + dataset; submissions
   publish immediately as `self-reported` (grey, unranked); manual snapshot
   regen (`publish.py`) makes them visible on the website. The board is live
   end-to-end with zero compute on our side.
1. **MVP** — external replay worker comes online and drains the queue: every
   self-reported row is replayed + verified and upgraded to `replayed` in
   place; new submissions verify shortly after they publish. 1 trial per
   condition. *"Request re-replay" and the verified-replayed badge are
   MVP-required, not deferred — they're what keep a private-source board
   credible.*
2. **V2** — automated nightly snapshot + rebuild; "not significant" flagging;
   invocation column; re-replay-on-dispute; claimed-vs-verified discrepancy
   surfacing; **spot-check tier**: re-score top rows with an agent we run
   ourselves (runner-attested badge upgrade).
3. **V3** — optional public-skill tier (stronger badge); per-domain sub-boards.

## Risks

- **Private source + submitter-generated trajectories + 1 trial is the
  weakest-trust / lowest-cost corner** of the decision space. Fine for a
  community board, but the badge wording, the cherry-picking note and the
  "request re-replay" escape hatch are what keep it honest — treat them as
  required.
- The feature leans on the replay worker being the **sole writer** of
  `results.parquet` and the **sole producer of `replayed` rows**, with rewards
  recomputed from raw verifier counts. Submitters' own numbers exist on the
  board only as the clearly-badged, unranked `self-reported` tier — if they
  ever reached the verified tier (or self-reported rows were ranked), the
  trust model collapses. Keep the tier boundary hard.
- **Two writers, one parquet.** The Space (self-reported upserts) and the
  worker (verified upserts) both read-modify-write `board.parquet`. Gradio
  serializes the Space's writes, but a Space write racing a worker commit can
  lose one update. Accepted for single-worker MVP volumes — every row is
  reconstructible from `queue/` + `scores/` + `results.parquet`; revisit if
  either writer scales out.
- **Two live surfaces can drift.** The website board and the HF Space must both
  derive from the single `board.parquet`; never let either compute its own
  numbers or read a different file. The website's lag behind the Space is fine,
  but the *values* must be identical.
