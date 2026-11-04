function onUpdateDatabase()
	logger.info("Updating database to version 63 (online-time counter capacity)")
	-- Preserve existing seeded counters while allowing normal saves to increment them.
	return db.query("ALTER TABLE `players` MODIFY `onlinetime` BIGINT UNSIGNED NOT NULL DEFAULT 0")
end
