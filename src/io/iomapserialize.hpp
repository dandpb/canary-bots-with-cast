/**
 * Canary - A free and open-source MMORPG server emulator
 * Copyright (©) 2019–present OpenTibiaBR <opentibiabr@outlook.com>
 * Repository: https://github.com/opentibiabr/canary
 * License: https://github.com/opentibiabr/canary/blob/main/LICENSE
 * Contributors: https://github.com/opentibiabr/canary/graphs/contributors
 * Website: https://docs.opentibiabr.com/
 */

#pragma once

#include "map/map.hpp"

#include <optional>

class DBInsert;

class IOMapSerialize {
public:
	struct AuctionBalanceChange {
		uint32_t guid = 0;
		uint64_t amount = 0;
		bool debit = false;
	};
	struct StartupHouseOwnership {
		uint32_t owner;
		uint32_t formerOwner = 0;
		int32_t scheduledOwner = -1;
	};
	static bool settleHouseAuction(const std::shared_ptr<House> &house, HouseAuctionState auction,
	                               AuctionBalanceChange first, AuctionBalanceChange second,
	                               std::optional<StartupHouseOwnership> startupOwner = std::nullopt);
	static void completeStartupHouseDepotTransfers(Houses &houses);
	static void loadHouseItems(Map* map);
	static bool saveHouseItems();
	static bool loadHouseInfo();
	static bool saveHouseInfo();

private:
	static bool SaveHouseInfoGuard();
	static bool SaveHouseItemsGuard();
	static bool addHouseTiles(DBInsert &rows, const House &house);
	static void saveItem(PropWriteStream &stream, const std::shared_ptr<Item> &item);
	static void saveTile(PropWriteStream &stream, const std::shared_ptr<Tile> &tile);

	static bool loadContainer(PropStream &propStream, const std::shared_ptr<Container> &container, bool strict = false);
	static bool loadItem(PropStream &propStream, const std::shared_ptr<Cylinder> &parent, bool isHouseItem = false, bool strict = false);

	static thread_local inline std::vector<std::shared_ptr<BedItem>> bedsToCheck;
};
