-- B1 companion playtest only (CORE_QA_PROFILE=b1, project canary-qa-b1). Never stage 1, never production.
-- Declared fixture of v4 2.4 for the three pilots: level 20, the vocation's normal HP/mana/cap, the level-20
-- bot loadout, Thais (town 8) temple, 20 potions each and 10000 gp in the bank. B1_FIXTURE.md has the numbers
-- and their sources. No account, no password, no human character: Daniel creates his own through MyAAC.
--
-- Runs once, from runtime/b1/initdb (b1_fixture.py prepare-initdb copies it there as 900_b1_seed_companions.sql),
-- which only compose.b1.yaml binds, on the fresh canary-qa-b1_database volume, after 000..099 (schema, bot
-- seeds, AUTO_INCREMENT). It refuses (SIGNAL) a database with any human account or character, so it can never
-- change a played database, stage 1's included. Every write names explicit ids; re-running it on the same
-- fresh database gives the same rows.

DELIMITER //
BEGIN NOT ATOMIC
  IF DATABASE() IS NULL OR DATABASE() <> 'canary' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'b1 seed: not the canary QA database; refused';
  END IF;
  IF (SELECT COUNT(*) FROM accounts WHERE id >= 65001) <> 0 OR (SELECT COUNT(*) FROM players WHERE id >= 66100) <> 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'b1 seed: database already has human accounts or characters; refused';
  END IF;
  IF (SELECT COUNT(*) FROM players WHERE (id, name, vocation, account_id) IN (
        (65001, 'Grizzle Alyronia', 4, 65000), (65003, 'Sever Heartspear', 3, 65000),
        (65004, 'Galdon Whitehoof', 2, 65000))) <> 3 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'b1 seed: the three pilot rows of 02_players.sql are not as expected; refused';
  END IF;
  IF (SELECT COUNT(*) FROM player_deaths WHERE player_id IN (65001, 65003, 65004)) <> 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'b1 seed: pilots already have deaths; not a fresh database; refused';
  END IF;
END//
DELIMITER ;

-- Marker read by leader-prep.sql.template and the slice: this database carries the B1 fixture.
CREATE TABLE IF NOT EXISTS `qa_b1_fixture` (
  `k` varchar(64) NOT NULL,
  `v` varchar(255) NOT NULL,
  PRIMARY KEY (`k`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
INSERT INTO `qa_b1_fixture` (`k`, `v`) VALUES ('fixture', 'b1-companions-v1') ON DUPLICATE KEY UPDATE `v` = VALUES(`v`);

-- One transaction for the pilot rows: a failed check ends the client before COMMIT.
START TRANSACTION;

-- Level 20 = 98800 experience; HP/mana/cap = level-1 base + 7 levels of vocation None + 12 of the vocation.
UPDATE `players` SET `level` = 20, `experience` = 98800, `health` = 365, `healthmax` = 365, `mana` = 95, `manamax` = 95,
  `cap` = 770, `town_id` = 8, `posx` = 32369, `posy` = 32241, `posz` = 7, `balance` = 10000
  WHERE `id` = 65001 AND `name` = 'Grizzle Alyronia' AND `vocation` = 4 AND `account_id` = 65000;
UPDATE `players` SET `level` = 20, `experience` = 98800, `health` = 305, `healthmax` = 305, `mana` = 215, `manamax` = 215,
  `cap` = 710, `town_id` = 8, `posx` = 32369, `posy` = 32241, `posz` = 7, `balance` = 10000
  WHERE `id` = 65003 AND `name` = 'Sever Heartspear' AND `vocation` = 3 AND `account_id` = 65000;
UPDATE `players` SET `level` = 20, `experience` = 98800, `health` = 245, `healthmax` = 245, `mana` = 395, `manamax` = 395,
  `cap` = 590, `town_id` = 8, `posx` = 32369, `posy` = 32241, `posz` = 7, `balance` = 10000
  WHERE `id` = 65004 AND `name` = 'Galdon Whitehoof' AND `vocation` = 2 AND `account_id` = 65000;

-- Inventory: the equipment.csv level-20 row per vocation in the hands equipBot uses (weapon left = 6,
-- shield right = 5), a backpack (sid 103) holding the potions. The seed has no pilot items before this.
DELETE FROM `player_items` WHERE `player_id` IN (65001, 65003, 65004);
INSERT INTO `player_items` (`player_id`, `pid`, `sid`, `itemtype`, `count`, `attributes`) VALUES
  (65001, 1, 101, 3365, 1, ''), (65001, 3, 103, 2854, 1, ''), (65001, 4, 104, 3366, 1, ''),
  (65001, 5, 105, 3423, 1, ''), (65001, 6, 106, 3284, 1, ''), (65001, 7, 107, 3363, 1, ''),
  (65001, 8, 108, 3555, 1, ''), (65001, 103, 201, 266, 14, ''), (65001, 103, 202, 268, 6, ''),
  (65003, 1, 101, 3365, 1, ''), (65003, 3, 103, 2854, 1, ''), (65003, 4, 104, 3366, 1, ''),
  (65003, 5, 105, 3423, 1, ''), (65003, 6, 106, 3347, 1, ''), (65003, 7, 107, 3363, 1, ''),
  (65003, 8, 108, 3555, 1, ''), (65003, 103, 201, 266, 10, ''), (65003, 103, 202, 268, 10, ''),
  (65004, 1, 101, 3365, 1, ''), (65004, 3, 103, 2854, 1, ''), (65004, 4, 104, 3388, 1, ''),
  (65004, 5, 105, 3423, 1, ''), (65004, 6, 106, 3069, 1, ''), (65004, 7, 107, 3363, 1, ''),
  (65004, 8, 108, 3555, 1, ''), (65004, 103, 201, 266, 6, ''), (65004, 103, 202, 268, 14, '');

-- The result, checked: any difference stops the init (and the database container) with the message.
DELIMITER //
BEGIN NOT ATOMIC
  IF (SELECT COUNT(*) FROM players WHERE (id, level, experience, health, healthmax, mana, manamax, cap, town_id,
        posx, posy, posz, balance) IN (
        (65001, 20, 98800, 365, 365, 95, 95, 770, 8, 32369, 32241, 7, 10000),
        (65003, 20, 98800, 305, 305, 215, 215, 710, 8, 32369, 32241, 7, 10000),
        (65004, 20, 98800, 245, 245, 395, 395, 590, 8, 32369, 32241, 7, 10000))) <> 3 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'b1 seed: pilot rows differ from the declared fixture';
  END IF;
  IF (SELECT COUNT(*) FROM player_items WHERE player_id IN (65001, 65003, 65004)) <> 27
     OR (SELECT COALESCE(SUM(`count`), 0) FROM player_items WHERE player_id IN (65001, 65003, 65004) AND itemtype IN (266, 268)) <> 60
     OR (SELECT COUNT(*) FROM player_items WHERE player_id IN (65001, 65003, 65004) AND itemtype IN (236, 237, 3031, 3035, 3043)) <> 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'b1 seed: pilot items differ from the declared fixture';
  END IF;
END//
DELIMITER ;
COMMIT;
