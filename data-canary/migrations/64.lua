function onUpdateDatabase()
	logger.info("Updating database to version 64 (durable Game Store orders)")
	assert(db.query([[
		CREATE TABLE IF NOT EXISTS `store_orders` (
		    `id` bigint unsigned NOT NULL AUTO_INCREMENT,
		    `player_guid` int unsigned NOT NULL,
		    `account_id` int unsigned NOT NULL,
		    `offer_id` int unsigned NOT NULL,
		    `transferable` tinyint unsigned NOT NULL,
		    `amount` int unsigned NOT NULL,
		    `detail` varchar(255) NOT NULL,
		    `state` enum('reserved','delivering','complete','refunded') NOT NULL DEFAULT 'reserved',
		    `active_account_id` int unsigned GENERATED ALWAYS AS (CASE WHEN `state` IN ('reserved','delivering') THEN `account_id` ELSE NULL END) STORED,
		    `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
		    `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
		    PRIMARY KEY (`id`),
		    UNIQUE KEY `store_orders_active_account` (`active_account_id`)
		) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
	]]))
	return true
end
