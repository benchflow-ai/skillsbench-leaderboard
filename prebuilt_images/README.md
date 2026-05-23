# Prebuilt Task Environment Images

These maps bind SkillsBench public task ids to digest-pinned task environment
images for AgentBeats public self-runs.

The worker consumes this as `SKILLSBENCH_WORKER_PREBUILT_IMAGES`. For public
`standard-v1` runs, `SKILLSBENCH_WORKER_REQUIRE_PREBUILT_IMAGES=true` makes
missing, mutable, or unresolved refs fail before task execution. Do not build
task images inside AgentBeats Quick Submit.

Each value must be a public `linux/amd64` image reference pinned with
`@sha256:<digest>`. Keep `tasks_excluded/` out of these maps unless a separate
non-public/debug scenario explicitly enables excluded tasks.

For `standard-v1`, this file must cover every public task before broad public
scoring is advertised. The map is deploy-ready only after the refs are verified
against GHCR.

For full adoption, use the shared package:

```text
ghcr.io/benchflow-ai/skillsbench-task-env
```

Use tags such as `standard-v1-citation-check` for publication, then pin the map
by digest.
