-- Runtime tables used by the shipped engine but absent from migration 62.
-- Authored hunts/routes remain CSV; this adds persistence and telemetry only.
CREATE TABLE IF NOT EXISTS bot_state_persistence (
    guid INT UNSIGNED NOT NULL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    ai_state TINYINT UNSIGNED NOT NULL DEFAULT 1,
    hunt_script_id INT UNSIGNED NULL,
    hunt_phase TINYINT UNSIGNED NULL,
    waypoint_idx INT UNSIGNED NULL,
    kill_count INT UNSIGNED NULL,
    travel_dest_town_id INT UNSIGNED NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS bot_startup_config (
    config_key VARCHAR(64) NOT NULL PRIMARY KEY,
    config_value TEXT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS bot_nav_events (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    event_type VARCHAR(64) NOT NULL,
    hunt_script_id INT UNSIGNED NOT NULL DEFAULT 0,
    hunt_script_name VARCHAR(255) NOT NULL DEFAULT '',
    route_town_id INT NOT NULL DEFAULT 0,
    route_type VARCHAR(64) NOT NULL DEFAULT '',
    town_name VARCHAR(255) NULL,
    bot_name VARCHAR(255) NOT NULL DEFAULT '',
    context TEXT NULL,
    event_count BIGINT UNSIGNED NOT NULL DEFAULT 0,
    first_seen TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY event_identity (event_type, hunt_script_id, route_town_id, route_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS bot_test_commands (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    command VARCHAR(64) NOT NULL,
    executed TINYINT NOT NULL DEFAULT 0,
    executed_at BIGINT UNSIGNED NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- The native loader uses uint32_t; signed SMALLINT rejects values above 32767.
ALTER TABLE player_charms
    MODIFY charm_points INT UNSIGNED NOT NULL DEFAULT 0,
    MODIFY minor_charm_echoes INT UNSIGNED NOT NULL DEFAULT 0,
    MODIFY max_charm_points INT UNSIGNED NOT NULL DEFAULT 0,
    MODIFY max_minor_charm_echoes INT UNSIGNED NOT NULL DEFAULT 0;

-- Seeded bot counters already reach signed INT_MAX; saving must preserve them.
ALTER TABLE players MODIFY onlinetime BIGINT UNSIGNED NOT NULL DEFAULT 0;
