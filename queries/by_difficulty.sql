SELECT
  CAST(participants.agent AS VARCHAR) AS id,
  row.difficulty AS "Difficulty",
  ROUND(
    100.0 * SUM(CASE WHEN row.score_eligible AND row.passed THEN 1 ELSE 0 END)
      / NULLIF(SUM(CASE WHEN row.score_eligible THEN 1 ELSE 0 END), 0),
    1
  ) AS "Pass Rate",
  ROUND(AVG(CASE WHEN row.score_eligible THEN row.reward ELSE NULL END), 3) AS "Mean Reward",
  ROUND(SUM(CASE WHEN row.score_eligible THEN COALESCE(row.time_used, 0) ELSE 0 END), 1) AS "Time",
  SUM(CASE WHEN row.score_eligible THEN 1 ELSE 0 END) AS "# Tasks",
  SUM(CASE WHEN NOT row.score_eligible OR row.infra_failure_type IS NOT NULL THEN 1 ELSE 0 END) AS "Infra Failed"
FROM results
CROSS JOIN UNNEST(results.results) AS outer_rows(outer_row)
CROSS JOIN UNNEST(
  CASE
    WHEN outer_row.results IS NOT NULL THEN outer_row.results
    ELSE [outer_row]
  END
) AS rows(row)
WHERE status = 'completed'
  AND participants.agent IS NOT NULL
  AND row.difficulty IS NOT NULL
GROUP BY id, row.difficulty
ORDER BY "Difficulty" ASC, "Pass Rate" DESC NULLS LAST, "Time" ASC, id ASC
