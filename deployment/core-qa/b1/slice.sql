-- B1 read-only DB slice, method b1-fixture-slice-v2 (B1_FIXTURE.md): the three pilots and every character created in QA (id >= 66100).
-- Run: docker exec -i canary-qa-b1-database-1 mariadb -ucanary -N -B canary < b1/slice.sql > <out>.tsv
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY;
SELECT 'fixture', k, v FROM qa_b1_fixture ORDER BY k;
SELECT 'humans', (SELECT COUNT(*) FROM accounts WHERE id >= 65001), (SELECT COUNT(*) FROM players WHERE id >= 66100);
SELECT 'player', id, account_id, name, vocation, level, experience, health, healthmax, mana, manamax, cap, maglevel, skill_fist, skill_club, skill_sword, skill_axe, skill_dist, skill_shielding, skill_fishing, town_id, posx, posy, posz, balance FROM players WHERE id IN (65001, 65003, 65004) OR id >= 66100 ORDER BY id;
SELECT 'slot', player_id, pid, itemtype, count FROM player_items WHERE (player_id IN (65001, 65003, 65004) OR player_id >= 66100) AND pid BETWEEN 1 AND 11 ORDER BY player_id, pid;
SELECT 'stock', p.id, t.itemtype, COALESCE(SUM(i.count), 0) FROM players AS p CROSS JOIN (SELECT 236 AS itemtype UNION ALL SELECT 237 UNION ALL SELECT 266 UNION ALL SELECT 268 UNION ALL SELECT 3031 UNION ALL SELECT 3035 UNION ALL SELECT 3043) AS t LEFT JOIN player_items AS i ON i.player_id = p.id AND i.itemtype = t.itemtype WHERE p.id IN (65001, 65003, 65004) OR p.id >= 66100 GROUP BY p.id, t.itemtype ORDER BY p.id, t.itemtype;
SELECT 'deaths', p.id, COUNT(d.player_id) FROM players AS p LEFT JOIN player_deaths AS d ON d.player_id = p.id WHERE p.id IN (65001, 65003, 65004) OR p.id >= 66100 GROUP BY p.id ORDER BY p.id;
SELECT 'death', player_id, time, level, killed_by, is_player, mostdamage_by, mostdamage_is_player FROM player_deaths WHERE player_id IN (65001, 65003, 65004) OR player_id >= 66100 ORDER BY player_id, time, killed_by;
COMMIT;
