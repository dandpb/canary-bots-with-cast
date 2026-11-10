-- B1 companion playtest only (CORE_QA_PROFILE=b1, project canary-qa-b1). Never stage 1, never production.
-- Declared fixture of v4 2.4 for the three pilots: level 20, the vocation's normal HP/mana/cap, a simplified
-- skill set (skills 50, magic level 4), the B1 starter loadout of the B1 equipment.csv, Thais (town 8) temple,
-- 20 potions and 100 platinum coins (10000 gp) each. B1_FIXTURE.md has the numbers and their sources.
-- No account, no password, no human character: Daniel creates his own through MyAAC.
--
-- Runs once, from runtime/b1/initdb (b1_fixture.py prepare-initdb copies it there as 900_b1_seed_companions.sql),
-- which only compose.b1.yaml binds, on the fresh canary-qa-b1_database volume, after 000..099. That the
-- database is the fresh B1 one comes from the operational gate (B1 profile, binds and a new volume, see
-- B1_FIXTURE.md). This guard is the second line: before any write it compares the pilots with their exact
-- 02_players.sql rows and the tables a fresh init leaves, and refuses any drift and any reapplication.

DELIMITER //
BEGIN NOT ATOMIC
  IF DATABASE() IS NULL OR DATABASE() <> 'canary' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'b1 seed: not the canary QA database; refused';
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'qa_b1_fixture') <> 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'b1 seed: the B1 marker already exists; reapplication refused';
  END IF;
  IF (SELECT COUNT(*) FROM accounts WHERE id >= 65001) <> 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'b1 seed: database has human accounts; refused';
  END IF;
  IF (SELECT COUNT(*) FROM players WHERE id >= 66100) <> 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'b1 seed: database has human characters; refused';
  END IF;
  -- Preimage: every column of each pilot exactly as database/bots/02_players.sql inserts it.
  IF (SELECT COUNT(*) FROM players WHERE
        `id` = 65001 AND `name` = 'Grizzle Alyronia' AND `group_id` = 1 AND `account_id` = 65000 AND `level` = 8
        AND `vocation` = 4 AND `health` = 290 AND `healthmax` = 290 AND `experience` = 4200 AND `lookbody` = 75
        AND `lookfeet` = 88 AND `lookhead` = 80 AND `looklegs` = 4 AND `looktype` = 433 AND `lookaddons` = 0
        AND `maglevel` = 100 AND `mana` = 125 AND `manamax` = 125 AND `manaspent` = 0 AND `soul` = 100
        AND `town_id` = 6 AND `posx` = 32681 AND `posy` = 31685 AND `posz` = 7 AND `conditions` = ''
        AND `cap` = 645 AND `sex` = 0 AND `pronoun` = 0 AND `lastlogin` = 0 AND `lastip` = 0 AND `save` = 1
        AND `skull` = 0 AND `skulltime` = 0 AND `lastlogout` = 0 AND `blessings` = 0 AND `blessings1` = 1
        AND `blessings2` = 1 AND `blessings3` = 1 AND `blessings4` = 1 AND `blessings5` = 1 AND `blessings6` = 1
        AND `blessings7` = 1 AND `blessings8` = 1 AND `onlinetime` = 10686367010 AND `deletion` = 0
        AND `balance` = 100000000000 AND `offlinetraining_time` = 43200 AND `offlinetraining_skill` = -1
        AND `stamina` = 2520 AND `skill_fist` = 100 AND `skill_fist_tries` = 0 AND `skill_club` = 100
        AND `skill_club_tries` = 0 AND `skill_sword` = 100 AND `skill_sword_tries` = 0 AND `skill_axe` = 100
        AND `skill_axe_tries` = 0 AND `skill_dist` = 100 AND `skill_dist_tries` = 0 AND `skill_shielding` = 100
        AND `skill_shielding_tries` = 0 AND `skill_fishing` = 100 AND `skill_fishing_tries` = 0
        AND `skill_critical_hit_chance` = 0 AND `skill_critical_hit_chance_tries` = 0
        AND `skill_critical_hit_damage` = 0 AND `skill_critical_hit_damage_tries` = 0
        AND `skill_life_leech_chance` = 0 AND `skill_life_leech_chance_tries` = 0 AND `skill_life_leech_amount` = 0
        AND `skill_life_leech_amount_tries` = 0 AND `skill_mana_leech_chance` = 0
        AND `skill_mana_leech_chance_tries` = 0 AND `skill_mana_leech_amount` = 0
        AND `skill_mana_leech_amount_tries` = 0 AND `skill_criticalhit_chance` = 0
        AND `skill_criticalhit_damage` = 0 AND `skill_lifeleech_chance` = 0 AND `skill_lifeleech_amount` = 0
        AND `skill_manaleech_chance` = 0 AND `skill_manaleech_amount` = 0 AND `manashield` = 0
        AND `max_manashield` = 0 AND `xpboost_stamina` = 0 AND `xpboost_value` = 0 AND `marriage_status` = 0
        AND `marriage_spouse` = -1 AND `bonus_rerolls` = 0 AND `prey_wildcard` = 0 AND `task_points` = 0
        AND `quickloot_fallback` = 0 AND `lookmountbody` = 45 AND `lookmountfeet` = 82 AND `lookmounthead` = 9
        AND `lookmountlegs` = 66 AND `lookfamiliarstype` = 0 AND `isreward` = 1 AND `istutorial` = 0
        AND `forge_dusts` = 0 AND `forge_dust_level` = 100 AND `randomize_mount` = 0 AND `boss_points` = 0
        AND `animus_mastery` = '') <> 1 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'b1 seed: pilot 65001 differs from its 02_players.sql row; refused';
  END IF;
  IF (SELECT COUNT(*) FROM players WHERE
        `id` = 65003 AND `name` = 'Sever Heartspear' AND `group_id` = 1 AND `account_id` = 65000 AND `level` = 11
        AND `vocation` = 3 AND `health` = 285 AND `healthmax` = 285 AND `experience` = 13000 AND `lookbody` = 46
        AND `lookfeet` = 85 AND `lookhead` = 23 AND `looklegs` = 124 AND `looktype` = 1293 AND `lookaddons` = 0
        AND `maglevel` = 100 AND `mana` = 240 AND `manamax` = 240 AND `manaspent` = 0 AND `soul` = 100
        AND `town_id` = 10 AND `posx` = 33194 AND `posy` = 32853 AND `posz` = 8 AND `conditions` = ''
        AND `cap` = 670 AND `sex` = 0 AND `pronoun` = 0 AND `lastlogin` = 0 AND `lastip` = 0 AND `save` = 1
        AND `skull` = 0 AND `skulltime` = 0 AND `lastlogout` = 0 AND `blessings` = 0 AND `blessings1` = 1
        AND `blessings2` = 1 AND `blessings3` = 1 AND `blessings4` = 1 AND `blessings5` = 1 AND `blessings6` = 1
        AND `blessings7` = 1 AND `blessings8` = 1 AND `onlinetime` = 0 AND `deletion` = 0
        AND `balance` = 100000000000 AND `offlinetraining_time` = 43200 AND `offlinetraining_skill` = -1
        AND `stamina` = 2520 AND `skill_fist` = 100 AND `skill_fist_tries` = 0 AND `skill_club` = 100
        AND `skill_club_tries` = 0 AND `skill_sword` = 100 AND `skill_sword_tries` = 0 AND `skill_axe` = 100
        AND `skill_axe_tries` = 0 AND `skill_dist` = 100 AND `skill_dist_tries` = 0 AND `skill_shielding` = 100
        AND `skill_shielding_tries` = 0 AND `skill_fishing` = 100 AND `skill_fishing_tries` = 0
        AND `skill_critical_hit_chance` = 0 AND `skill_critical_hit_chance_tries` = 0
        AND `skill_critical_hit_damage` = 0 AND `skill_critical_hit_damage_tries` = 0
        AND `skill_life_leech_chance` = 0 AND `skill_life_leech_chance_tries` = 0 AND `skill_life_leech_amount` = 0
        AND `skill_life_leech_amount_tries` = 0 AND `skill_mana_leech_chance` = 0
        AND `skill_mana_leech_chance_tries` = 0 AND `skill_mana_leech_amount` = 0
        AND `skill_mana_leech_amount_tries` = 0 AND `skill_criticalhit_chance` = 0
        AND `skill_criticalhit_damage` = 0 AND `skill_lifeleech_chance` = 0 AND `skill_lifeleech_amount` = 0
        AND `skill_manaleech_chance` = 0 AND `skill_manaleech_amount` = 0 AND `manashield` = 0
        AND `max_manashield` = 0 AND `xpboost_stamina` = 0 AND `xpboost_value` = 0 AND `marriage_status` = 0
        AND `marriage_spouse` = -1 AND `bonus_rerolls` = 0 AND `prey_wildcard` = 0 AND `task_points` = 0
        AND `quickloot_fallback` = 0 AND `lookmountbody` = 23 AND `lookmountfeet` = 9 AND `lookmounthead` = 109
        AND `lookmountlegs` = 120 AND `lookfamiliarstype` = 0 AND `isreward` = 1 AND `istutorial` = 0
        AND `forge_dusts` = 0 AND `forge_dust_level` = 100 AND `randomize_mount` = 0 AND `boss_points` = 0
        AND `animus_mastery` = '') <> 1 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'b1 seed: pilot 65003 differs from its 02_players.sql row; refused';
  END IF;
  IF (SELECT COUNT(*) FROM players WHERE
        `id` = 65004 AND `name` = 'Galdon Whitehoof' AND `group_id` = 1 AND `account_id` = 65000 AND `level` = 13
        AND `vocation` = 2 AND `health` = 245 AND `healthmax` = 245 AND `experience` = 23200 AND `lookbody` = 6
        AND `lookfeet` = 70 AND `lookhead` = 67 AND `looklegs` = 127 AND `looktype` = 1713 AND `lookaddons` = 2
        AND `maglevel` = 100 AND `mana` = 450 AND `manamax` = 450 AND `manaspent` = 0 AND `soul` = 100
        AND `town_id` = 6 AND `posx` = 32197 AND `posy` = 32296 AND `posz` = 7 AND `conditions` = ''
        AND `cap` = 590 AND `sex` = 1 AND `pronoun` = 0 AND `lastlogin` = 0 AND `lastip` = 0 AND `save` = 1
        AND `skull` = 0 AND `skulltime` = 0 AND `lastlogout` = 0 AND `blessings` = 0 AND `blessings1` = 1
        AND `blessings2` = 1 AND `blessings3` = 1 AND `blessings4` = 1 AND `blessings5` = 1 AND `blessings6` = 1
        AND `blessings7` = 1 AND `blessings8` = 1 AND `onlinetime` = 12468764151 AND `deletion` = 0
        AND `balance` = 100000000000 AND `offlinetraining_time` = 43200 AND `offlinetraining_skill` = -1
        AND `stamina` = 2520 AND `skill_fist` = 100 AND `skill_fist_tries` = 0 AND `skill_club` = 100
        AND `skill_club_tries` = 0 AND `skill_sword` = 100 AND `skill_sword_tries` = 0 AND `skill_axe` = 100
        AND `skill_axe_tries` = 0 AND `skill_dist` = 100 AND `skill_dist_tries` = 0 AND `skill_shielding` = 100
        AND `skill_shielding_tries` = 0 AND `skill_fishing` = 100 AND `skill_fishing_tries` = 0
        AND `skill_critical_hit_chance` = 0 AND `skill_critical_hit_chance_tries` = 0
        AND `skill_critical_hit_damage` = 0 AND `skill_critical_hit_damage_tries` = 0
        AND `skill_life_leech_chance` = 0 AND `skill_life_leech_chance_tries` = 0 AND `skill_life_leech_amount` = 0
        AND `skill_life_leech_amount_tries` = 0 AND `skill_mana_leech_chance` = 0
        AND `skill_mana_leech_chance_tries` = 0 AND `skill_mana_leech_amount` = 0
        AND `skill_mana_leech_amount_tries` = 0 AND `skill_criticalhit_chance` = 0
        AND `skill_criticalhit_damage` = 0 AND `skill_lifeleech_chance` = 0 AND `skill_lifeleech_amount` = 0
        AND `skill_manaleech_chance` = 0 AND `skill_manaleech_amount` = 0 AND `manashield` = 0
        AND `max_manashield` = 0 AND `xpboost_stamina` = 0 AND `xpboost_value` = 0 AND `marriage_status` = 0
        AND `marriage_spouse` = -1 AND `bonus_rerolls` = 0 AND `prey_wildcard` = 0 AND `task_points` = 0
        AND `quickloot_fallback` = 0 AND `lookmountbody` = 34 AND `lookmountfeet` = 57 AND `lookmounthead` = 49
        AND `lookmountlegs` = 76 AND `lookfamiliarstype` = 0 AND `isreward` = 1 AND `istutorial` = 0
        AND `forge_dusts` = 0 AND `forge_dust_level` = 100 AND `randomize_mount` = 0 AND `boss_points` = 0
        AND `animus_mastery` = '') <> 1 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'b1 seed: pilot 65004 differs from its 02_players.sql row; refused';
  END IF;
  -- A fresh init gives the pilots no items, depot, inbox, deaths or online row, and only the storage of
  -- 03_player_storage.sql (299, 133 and 300 rows).
  IF (SELECT COUNT(*) FROM player_items WHERE player_id IN (65001, 65003, 65004)) <> 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'b1 seed: pilots already have items; refused';
  END IF;
  IF (SELECT COUNT(*) FROM player_depotitems WHERE player_id IN (65001, 65003, 65004)) <> 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'b1 seed: pilots already have depot items; refused';
  END IF;
  IF (SELECT COUNT(*) FROM player_inboxitems WHERE player_id IN (65001, 65003, 65004)) <> 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'b1 seed: pilots already have inbox items; refused';
  END IF;
  IF (SELECT COUNT(*) FROM player_deaths WHERE player_id IN (65001, 65003, 65004)) <> 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'b1 seed: pilots already have deaths; refused';
  END IF;
  IF (SELECT COUNT(*) FROM players_online WHERE player_id IN (65001, 65003, 65004)) <> 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'b1 seed: pilots are online; refused';
  END IF;
  IF (SELECT COUNT(*) FROM player_storage WHERE player_id = 65001) <> 299 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'b1 seed: pilot 65001 storage differs from 03_player_storage.sql; refused';
  END IF;
  IF (SELECT COUNT(*) FROM player_storage WHERE player_id = 65003) <> 133 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'b1 seed: pilot 65003 storage differs from 03_player_storage.sql; refused';
  END IF;
  IF (SELECT COUNT(*) FROM player_storage WHERE player_id = 65004) <> 300 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'b1 seed: pilot 65004 storage differs from 03_player_storage.sql; refused';
  END IF;
END//
DELIMITER ;

-- Every write comes after the guard. The marker table (DDL commits on its own) is created empty here; its row
-- is written in the transaction below, so a failed check leaves no marker row and no pilot change.
CREATE TABLE `qa_b1_fixture` (
  `k` varchar(64) NOT NULL,
  `v` varchar(255) NOT NULL,
  PRIMARY KEY (`k`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

START TRANSACTION;

INSERT INTO `qa_b1_fixture` (`k`, `v`) VALUES ('fixture', 'b1-companions-v2');

-- Level 20 = 98800 exp; HP/mana/cap = level-1 base + 7 levels of vocation None + 12 of the vocation.
-- Skills 50 and magic level 4: a simplified QA fixture, not a natural progression. Balance is left as seeded:
-- bot_market_funding.lua sets it to 100000000000 for every bot at each start anyway.
UPDATE `players` SET `level` = 20, `experience` = 98800, `health` = 365, `healthmax` = 365, `mana` = 95, `manamax` = 95,
  `cap` = 770, `maglevel` = 4, `skill_fist` = 50, `skill_club` = 50, `skill_sword` = 50, `skill_axe` = 50,
  `skill_dist` = 50, `skill_shielding` = 50, `skill_fishing` = 50, `town_id` = 8, `posx` = 32369, `posy` = 32241, `posz` = 7
  WHERE `id` = 65001 AND `name` = 'Grizzle Alyronia' AND `vocation` = 4 AND `account_id` = 65000;
UPDATE `players` SET `level` = 20, `experience` = 98800, `health` = 305, `healthmax` = 305, `mana` = 215, `manamax` = 215,
  `cap` = 710, `maglevel` = 4, `skill_fist` = 50, `skill_club` = 50, `skill_sword` = 50, `skill_axe` = 50,
  `skill_dist` = 50, `skill_shielding` = 50, `skill_fishing` = 50, `town_id` = 8, `posx` = 32369, `posy` = 32241, `posz` = 7
  WHERE `id` = 65003 AND `name` = 'Sever Heartspear' AND `vocation` = 3 AND `account_id` = 65000;
UPDATE `players` SET `level` = 20, `experience` = 98800, `health` = 245, `healthmax` = 245, `mana` = 395, `manamax` = 395,
  `cap` = 590, `maglevel` = 4, `skill_fist` = 50, `skill_club` = 50, `skill_sword` = 50, `skill_axe` = 50,
  `skill_dist` = 50, `skill_shielding` = 50, `skill_fishing` = 50, `town_id` = 8, `posx` = 32369, `posy` = 32241, `posz` = 7
  WHERE `id` = 65004 AND `name` = 'Galdon Whitehoof' AND `vocation` = 2 AND `account_id` = 65000;

-- Inventory = the level-20 row of the B1 equipment.csv (what equipBot re-equips) in the hands equipBot uses
-- (weapon left = 6, shield right = 5), a backpack (sid 103) with the potions and 100 platinum coins.
INSERT INTO `player_items` (`player_id`, `pid`, `sid`, `itemtype`, `count`, `attributes`) VALUES
  (65001, 1, 101, 3351, 1, ''), (65001, 3, 103, 2854, 1, ''), (65001, 4, 104, 3357, 1, ''),
  (65001, 5, 105, 3409, 1, ''), (65001, 6, 106, 3264, 1, ''), (65001, 7, 107, 3557, 1, ''),
  (65001, 8, 108, 3552, 1, ''), (65001, 103, 201, 266, 14, ''), (65001, 103, 202, 268, 6, ''),
  (65001, 103, 203, 3035, 100, ''),
  (65003, 1, 101, 3352, 1, ''), (65003, 3, 103, 2854, 1, ''), (65003, 4, 104, 3359, 1, ''),
  (65003, 5, 105, 3409, 1, ''), (65003, 6, 106, 3277, 1, ''), (65003, 7, 107, 3372, 1, ''),
  (65003, 8, 108, 3552, 1, ''), (65003, 103, 201, 266, 10, ''), (65003, 103, 202, 268, 10, ''),
  (65003, 103, 203, 3035, 100, ''),
  (65004, 1, 101, 3355, 1, ''), (65004, 3, 103, 2854, 1, ''), (65004, 4, 104, 3361, 1, ''),
  (65004, 5, 105, 3412, 1, ''), (65004, 6, 106, 3066, 1, ''), (65004, 7, 107, 3362, 1, ''),
  (65004, 8, 108, 3552, 1, ''), (65004, 103, 201, 266, 6, ''), (65004, 103, 202, 268, 14, ''),
  (65004, 103, 203, 3035, 100, '');

-- The result, checked: any difference stops the init (and the database container) before COMMIT.
DELIMITER //
BEGIN NOT ATOMIC
  IF (SELECT COUNT(*) FROM players WHERE `level` = 20 AND `experience` = 98800 AND `town_id` = 8 AND `posx` = 32369
        AND `posy` = 32241 AND `posz` = 7 AND `maglevel` = 4 AND `skill_fist` = 50 AND `skill_club` = 50
        AND `skill_sword` = 50 AND `skill_axe` = 50 AND `skill_dist` = 50 AND `skill_shielding` = 50 AND `skill_fishing` = 50
        AND `health` = `healthmax` AND `mana` = `manamax` AND `balance` = 100000000000
        AND ((`id` = 65001 AND `healthmax` = 365 AND `manamax` = 95 AND `cap` = 770)
          OR (`id` = 65003 AND `healthmax` = 305 AND `manamax` = 215 AND `cap` = 710)
          OR (`id` = 65004 AND `healthmax` = 245 AND `manamax` = 395 AND `cap` = 590))) <> 3 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'b1 seed: pilot rows differ from the declared fixture';
  END IF;
  IF (SELECT COUNT(*) FROM player_items WHERE player_id IN (65001, 65003, 65004)) <> 30 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'b1 seed: pilot item rows differ from the declared fixture';
  END IF;
  IF (SELECT COALESCE(SUM(`count`), 0) FROM player_items WHERE player_id IN (65001, 65003, 65004) AND itemtype IN (266, 268)) <> 60 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'b1 seed: pilot potions differ from the declared fixture';
  END IF;
  IF (SELECT COALESCE(SUM(`count`), 0) FROM player_items WHERE player_id IN (65001, 65003, 65004) AND itemtype = 3035) <> 300 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'b1 seed: pilot coins differ from the declared fixture';
  END IF;
  IF (SELECT COUNT(*) FROM player_items WHERE player_id IN (65001, 65003, 65004) AND itemtype IN (236, 237, 3031, 3043)) <> 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'b1 seed: pilots carry undeclared potions or coins';
  END IF;
  IF (SELECT COUNT(*) FROM qa_b1_fixture) <> 1 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'b1 seed: marker rows differ';
  END IF;
END//
DELIMITER ;
COMMIT;
