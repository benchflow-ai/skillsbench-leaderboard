# Prebuilt Task Environment Images

These maps bind SkillsBench public task ids to digest-pinned task environment
images for AgentBeats public self-runs.

The worker consumes this as `SKILLSBENCH_WORKER_PREBUILT_IMAGES` so public
AgentBeats runs use existing images instead of trying to build task Dockerfiles
inside the Amber Docker gateway.

Each value must be a public `linux/amd64` image reference pinned with
`@sha256:<digest>`. Keep `tasks_excluded/` out of these maps unless a separate
non-public/debug scenario explicitly enables excluded tasks.

For `standard-v1` fast-prep branches, this file may be contract-correct before
every referenced digest has been published and anonymously verified under the
BenchFlow-owned GHCR package. Treat that state as prepared input for the
publisher/verification workflow, not deploy proof.

For full adoption, use the shared package:

```text
ghcr.io/benchflow-ai/skillsbench-task-env
```

Use tags such as `standard-v1-citation-check` for publication, then pin the
leaderboard map by digest.
