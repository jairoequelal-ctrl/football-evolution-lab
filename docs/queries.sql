-- Generated local DuckDB: artifacts/football.duckdb
SELECT season, team, competition, SUM(goals) AS goals,
       90.0*SUM(goals)/NULLIF(SUM(minutes),0) AS goals_p90
FROM player_match_stats WHERE scope='club'
GROUP BY season,team,competition HAVING SUM(minutes)>=450
ORDER BY goals_p90 DESC;

SELECT body_part, COUNT(*) AS goals
FROM shots WHERE outcome='Goal' GROUP BY body_part;

SELECT team, MIN(date) AS first_covered, MAX(date) AS last_covered,
       COUNT(DISTINCT match_id) AS covered_appearances
FROM player_match_stats GROUP BY team;
