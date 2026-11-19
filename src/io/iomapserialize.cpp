/**
 * Canary - A free and open-source MMORPG server emulator
 * Copyright (©) 2019–present OpenTibiaBR <opentibiabr@outlook.com>
 * Repository: https://github.com/opentibiabr/canary
 * License: https://github.com/opentibiabr/canary/blob/main/LICENSE
 * Contributors: https://github.com/opentibiabr/canary/graphs/contributors
 * Website: https://docs.opentibiabr.com/
 */

#include "io/iomapserialize.hpp"

#include "config/configmanager.hpp"
#include "creatures/players/player.hpp"
#include "io/functions/iologindata_save_player.hpp"
#include "io/iologindata.hpp"
#include "io/iomarket.hpp"
#include "game/game.hpp"
#include "game/scheduling/dispatcher.hpp"
#include "game/scheduling/save_manager.hpp"
#include "items/bed.hpp"
#include "kv/kv.hpp"

#include <array>
#include <charconv>
#include <limits>
#include <random>

namespace {
	std::mutex houseAuctionMutex;
	constexpr std::string_view houseDepotPrefix = "house:depot:";

	std::map<uint32_t, uint32_t> loadHouseDepotTransfers() {
		bool read = false;
		auto &db = g_database();
		const auto rows = db.storeQuery(fmt::format("SELECT `config`, `value` FROM `server_config` WHERE `config` LIKE '{}%'", houseDepotPrefix), read);
		if (!read) throw std::runtime_error("Could not load pending house depot transfers");
		std::map<uint32_t, uint32_t> pending;
		if (!rows) return pending;
		do {
			const auto key = rows->getString("config");
			const auto owner = rows->getString("value");
			uint32_t houseId = 0;
			uint32_t playerId = 0;
			const auto readId = [](std::string_view value, uint32_t &id) {
				const auto result = std::from_chars(value.data(), value.data() + value.size(), id);
				return result.ec == std::errc {} && result.ptr == value.data() + value.size() && id != 0;
			};
			if (!key.starts_with(houseDepotPrefix) || !readId(std::string_view(key).substr(houseDepotPrefix.size()), houseId)
			    || !readId(owner, playerId) || !pending.emplace(houseId, playerId).second) {
				throw std::runtime_error("Invalid pending house depot transfer: " + key);
			}
		} while (rows->next());
		return pending;
	}

	struct HouseAuctionBalance {
		IOMapSerialize::AuctionBalanceChange change;
		std::shared_ptr<Player> player;
		uint64_t balance = 0;
	};

	void publishHouseAuction(const std::shared_ptr<House> &house, HouseAuctionState auction, const std::array<HouseAuctionBalance, 2> &balances) {
		for (const auto &entry : balances) {
			if (entry.player) {
				entry.player->setBankBalance(entry.balance);
				entry.player->sendResourceBalance(RESOURCE_BANK, entry.balance);
			}
		}
		house->setAuctionState(std::move(auction));
	}

	void reconcileHouseAuction(const std::shared_ptr<House> &house, HouseAuctionState auction, std::array<HouseAuctionBalance, 2> balances,
	                          std::string receiptKey, std::string receiptToken) {
		g_dispatcher().scheduleEvent(1000, [house, auction = std::move(auction), balances = std::move(balances),
		                                      key = std::move(receiptKey), token = std::move(receiptToken)]() mutable {
			std::unique_lock auctionLock(houseAuctionMutex, std::try_to_lock);
			bool committed = false;
			const bool inspected = auctionLock.owns_lock() && DBTransaction::executeWithinTransaction([&] {
				auto &db = g_database();
				bool read = false;
				const auto row = db.storeQuery(fmt::format("SELECT `value` FROM `server_config` WHERE `config` = {} FOR UPDATE", db.escapeString(key)), read);
				committed = row && row->getString("value") == token;
				return read;
			});
			if (!inspected) {
				reconcileHouseAuction(house, std::move(auction), std::move(balances), std::move(key), std::move(token));
				return;
			}
			if (committed) {
				bool canPublish = true;
				for (auto &entry : balances) {
					if (!entry.player) continue;
					const auto balance = entry.player->getBankBalance();
					const auto amount = entry.change.amount;
					if (entry.change.debit ? balance < amount : balance > std::numeric_limits<uint64_t>::max() - amount) {
						canPublish = false;
						break;
					}
					entry.balance = entry.change.debit ? balance - amount : balance + amount;
				}
				if (!canPublish) {
					g_logger().error("HOUSE_AUCTION_BALANCE_CONFLICT house={}", house->getId());
					reconcileHouseAuction(house, std::move(auction), std::move(balances), std::move(key), std::move(token));
					return;
				}
				publishHouseAuction(house, std::move(auction), balances);
			}
			for (const auto &entry : balances) {
				if (entry.change.guid) IOMarket::setPlayerFillPending(entry.change.guid, false);
			}
			house->setPendingAuctionSettlement(false);
		}, "IOMapSerialize::reconcileHouseAuction");
	}
}

bool IOMapSerialize::settleHouseAuction(const std::shared_ptr<House> &house, HouseAuctionState auction,
                                       AuctionBalanceChange first, AuctionBalanceChange second,
                                       std::optional<StartupHouseOwnership> startupOwner) {
	std::unique_lock auctionLock(houseAuctionMutex, std::try_to_lock);
	if (!auctionLock.owns_lock() || house->hasPendingAuctionSettlement()) return false;
	if (auction.internalBid > std::numeric_limits<int32_t>::max() || auction.highestBid > std::numeric_limits<int32_t>::max()
	    || auction.bidEndDate > std::numeric_limits<int32_t>::max() || auction.reservedRent > std::numeric_limits<int32_t>::max()) return false;
	if (first.guid && first.guid == second.guid) return false;
	if ((!first.guid && first.amount) || (!second.guid && second.amount)) return false;
	if (second.guid && (!first.guid || second.guid < first.guid)) std::swap(first, second);
	std::array<HouseAuctionBalance, 2> balances {HouseAuctionBalance {first}, HouseAuctionBalance {second}};
	std::array<std::optional<Player::PlayerLock>, 2> playerLocks;
	for (size_t i = 0; i < balances.size(); ++i) {
		auto &entry = balances[i];
		const auto guid = entry.change.guid;
		if (!guid) continue;
		if (IOMarket::playerHasPendingFill(guid) || g_saveManager().hasPendingLogout(guid)) return false;
		entry.player = g_game().getPlayerByGUID(guid);
		if (entry.player) playerLocks[i].emplace(entry.player);
	}

	const auto receiptKey = fmt::format("house:auction:{}", house->getId());
	const auto receiptToken = fmt::format("{}-{:08x}", KV::generateUUID(), std::random_device{}());
	const auto expected = house->getAuctionState();
	const DBTransaction::ScopedReceipt receipt(receiptKey, receiptToken);
	const auto outcome = DBTransaction::executeWithOutcome([&] {
		auto &db = g_database();
		bool read = false;
		const auto current = db.storeQuery(fmt::format(
			"SELECT `owner`, `new_owner`, `rent`, `bidder`, `highest_bid`, `internal_bid`, `bid_end_date`, `state`, `transfer_status` FROM `houses` WHERE `id` = {} FOR UPDATE", house->getId()), read);
		if (!read || (!current && (startupOwner || expected.state != CyclopediaHouseState::Available || expected.bidder))) return false;
		if (current && (current->getNumber<int32_t>("new_owner") != (startupOwner ? startupOwner->scheduledOwner : -1)
		                || current->getNumber<uint32_t>("bidder") != expected.bidder
		                || current->getNumber<uint64_t>("highest_bid") != expected.highestBid
		                || current->getNumber<uint64_t>("internal_bid") != expected.internalBid
		                || current->getNumber<uint32_t>("bid_end_date") != expected.bidEndDate
		                || current->getNumber<uint16_t>("state") != magic_enum::enum_integer(expected.state)
		                || current->getNumber<bool>("transfer_status") != expected.transferAccepted
		                || (house->hasAuctionEscrow() && current->getNumber<uint32_t>("rent") != expected.reservedRent))) return false;
		if (startupOwner && startupOwner->owner && !db.storeQuery(fmt::format("SELECT `id` FROM `players` WHERE `id` = {} FOR UPDATE", startupOwner->owner))) return false;
		if (startupOwner && startupOwner->formerOwner) {
			if (current->getNumber<uint32_t>("owner") != startupOwner->formerOwner) return false;
			if (!db.executeQuery(fmt::format("INSERT INTO `server_config` (`config`, `value`) VALUES ('{}{}', '{}')", houseDepotPrefix, house->getId(), startupOwner->formerOwner))) return false;
		}
		for (auto &entry : balances) {
			const auto &change = entry.change;
			if (!change.guid) continue;
			const auto row = db.storeQuery(fmt::format("SELECT `balance` FROM `players` WHERE `id` = {} FOR UPDATE", change.guid));
			if (!row) return false;
			const auto previous = entry.player ? entry.player->getBankBalance() : row->getNumber<uint64_t>("balance");
			if (change.debit ? previous < change.amount : previous > std::numeric_limits<uint64_t>::max() - change.amount) return false;
			entry.balance = change.debit ? previous - change.amount : previous + change.amount;
			if (!db.executeQuery(fmt::format("UPDATE `players` SET `balance` = {} WHERE `id` = {}", entry.balance, change.guid))) return false;
		}
		const auto owner = startupOwner ? startupOwner->owner : house->getOwner();
		const auto ownerUpdate = startupOwner ? "`owner` = VALUES(`owner`), `new_owner` = -1, `paid` = 0, `warnings` = 0, " : "";
		const bool holdsEscrow = auction.bidder && (auction.state == CyclopediaHouseState::Available || auction.transferAccepted);
		const auto rent = holdsEscrow ? auction.reservedRent : house->getRent();
		return db.executeQuery(fmt::format(
			"INSERT INTO `houses` (`id`, `owner`, `name`, `town_id`, `rent`, `size`, `beds`, `bidder`, `bidder_name`, `highest_bid`, `internal_bid`, `bid_end_date`, `state`, `transfer_status`) "
			"VALUES ({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}) ON DUPLICATE KEY UPDATE {}"
			"`rent` = VALUES(`rent`), `bidder` = VALUES(`bidder`), `bidder_name` = VALUES(`bidder_name`), `highest_bid` = VALUES(`highest_bid`), `internal_bid` = VALUES(`internal_bid`), "
			"`bid_end_date` = VALUES(`bid_end_date`), `state` = VALUES(`state`), `transfer_status` = VALUES(`transfer_status`)",
			house->getId(), owner, db.escapeString(house->getName()), house->getTownId(), rent, house->getSize(), house->getBedCount(),
			auction.bidder, db.escapeString(auction.bidderName), auction.highestBid, auction.internalBid, auction.bidEndDate,
			magic_enum::enum_integer(auction.state), auction.transferAccepted, ownerUpdate));
	});
	if (outcome == DBTransaction::Outcome::Committed) {
		publishHouseAuction(house, std::move(auction), balances);
		if (startupOwner) house->setOwner(startupOwner->owner, false);
		return !startupOwner || house->getOwner() == startupOwner->owner;
	}
	if (outcome != DBTransaction::Outcome::Uncertain) return false;

	g_logger().error("HOUSE_AUCTION_UNCERTAIN house={}", house->getId());
	// Loading stops before logins or map writes; the next start reads the durable outcome.
	if (startupOwner) return false;
	house->setPendingAuctionSettlement(true);
	for (const auto &entry : balances) {
		if (entry.change.guid) IOMarket::setPlayerFillPending(entry.change.guid, true);
	}
	for (auto &lock : playerLocks) lock.reset();
	auctionLock.unlock();
	for (const auto &entry : balances) {
		if (entry.player && entry.player->isOnline()) {
			entry.player->sendTextMessage(MESSAGE_EVENT_ADVANCE, "A house payment is being reconciled. Check the house and your balance before retrying.");
			entry.player->removePlayer(true);
		}
	}
	reconcileHouseAuction(house, std::move(auction), std::move(balances), receiptKey, receiptToken);
	return false;
}

void IOMapSerialize::loadHouseItems(Map* map) {
	Benchmark bm_context;

	const auto pendingTransfers = loadHouseDepotTransfers();
	bool read = false;
	DBResult_ptr result = Database::getInstance().storeQuery("SELECT `house_id`, `data` FROM `tile_store`", read);
	if (!read && !pendingTransfers.empty()) throw std::runtime_error("Could not load tiles for pending house depot transfers");
	if (!result) {
		return;
	}

	do {
		const auto houseId = result->getNumber<uint32_t>("house_id");
		const bool strict = pendingTransfers.contains(houseId);
		const auto valid = [houseId, strict](bool ok) {
			if (!ok && strict) throw std::runtime_error(fmt::format("Unreadable stored tiles for pending house depot transfer {}", houseId));
			return ok;
		};
		unsigned long attrSize;
		const char* attr = result->getStream("data", attrSize);

		PropStream propStream;
		propStream.init(attr, attrSize);

		uint16_t x, y;
		uint8_t z;
		if (!valid(propStream.read<uint16_t>(x) && propStream.read<uint16_t>(y) && propStream.read<uint8_t>(z))) {
			continue;
		}

		std::shared_ptr<Tile> tile = map->getTile(x, y, z);
		if (!valid(tile != nullptr)) {
			continue;
		}
		const auto houseTile = std::dynamic_pointer_cast<HouseTile>(tile);
		if (strict) valid(houseTile && houseTile->getHouse()->getId() == houseId);

		uint32_t item_count;
		if (!valid(propStream.read<uint32_t>(item_count))) {
			continue;
		}

		while (item_count--) {
			if (!strict && houseTile) {
				const auto &house = houseTile->getHouse();
				auto isTransferOnRestart = g_configManager().getBoolean(TOGGLE_HOUSE_TRANSFER_ON_SERVER_RESTART);
				if (!isTransferOnRestart && house->getOwner() == 0) {
					g_logger().trace("Skipping load item from house id: {}, position: {}, house does not have owner", house->getId(), house->getEntryPosition().toString());
					house->clearHouseInfo(false);
					continue;
				}
			}

			valid(loadItem(propStream, tile, true, strict));
		}
	} while (result->next());

	for (const auto &bed : bedsToCheck) {
		const auto &next = bed->getNextBedItem();
		const bool isComplete = next && (bed->isBedComplete(next) || next->isBedComplete(bed));
		if (!isComplete) {
			const Position &pos = bed->getPosition();
			g_logger().warn("[BedFix] House bug detected at {}, correcting bed.", pos);

			bed->forceClearSleeper();
			if (next && next->getNextBedItem() == bed) {
				next->forceClearSleeper();
			}
		}
	}

	bedsToCheck.clear();

	g_logger().info("Loaded house items in {} milliseconds", bm_context.duration());
}

bool IOMapSerialize::saveHouseItems() {
	bool success = DBTransaction::executeWithinTransaction([]() {
		return SaveHouseItemsGuard();
	});

	if (!success) {
		g_logger().error("[{}] Error occurred saving houses", __FUNCTION__);
	}

	return success;
}

bool IOMapSerialize::SaveHouseItemsGuard() {
	Database &db = Database::getInstance();

	// clear old tile data
	if (!db.executeQuery("DELETE FROM `tile_store`")) {
		return false;
	}

	DBInsert stmt("INSERT INTO `tile_store` (`house_id`, `data`) VALUES ");
	for (const auto &[_, house] : g_game().map.houses.getHouses()) {
		if (!addHouseTiles(stmt, *house)) return false;
	}
	return stmt.execute();
}

bool IOMapSerialize::addHouseTiles(DBInsert &rows, const House &house) {
	auto &db = g_database();
	PropWriteStream stream;
	for (const auto &tile : house.getTiles()) {
		saveTile(stream, tile);
		size_t size = 0;
		const char* attributes = stream.getStream(size);
		if (size && !rows.addRow(fmt::format("{},{}", house.getId(), db.escapeBlob(attributes, size)))) return false;
		stream.clear();
	}
	return true;
}

void IOMapSerialize::completeStartupHouseDepotTransfers(Houses &houses) {
	for (const auto &[houseId, formerOwner] : loadHouseDepotTransfers()) {
		const auto house = houses.getHouse(houseId);
		const auto key = fmt::format("'{}{}'", houseDepotPrefix, houseId);
		if (!house || !DBTransaction::executeWithinTransaction([&] {
			auto &db = g_database();
			const auto row = db.storeQuery(fmt::format("SELECT `value` FROM `server_config` WHERE `config` = {} FOR UPDATE", key));
			if (!row || row->getString("value") != std::to_string(formerOwner)) return false;
			House::StartupDepotRecipients recipients;
			if (!house->stageStartupDepotTransfer(formerOwner, recipients)) return false;
			for (const auto &[_, player] : recipients) {
				if (!IOLoginDataSave::appendPlayerInbox(player)) return false;
			}
			if (!db.executeQuery(fmt::format("DELETE FROM `tile_store` WHERE `house_id` = {}", houseId))) return false;
			DBInsert rows("INSERT INTO `tile_store` (`house_id`, `data`) VALUES ");
			return addHouseTiles(rows, *house) && rows.execute()
			    && db.executeQuery(fmt::format("DELETE FROM `house_lists` WHERE `house_id` = {}", houseId))
			    && db.executeQuery(fmt::format("DELETE FROM `server_config` WHERE `config` = {}", key));
		})) {
			throw std::runtime_error(fmt::format("Could not complete depot transfer for house {}. Restart to recover from persisted state.", houseId));
		}
	}
}

bool IOMapSerialize::loadContainer(PropStream &propStream, const std::shared_ptr<Container> &container, bool strict) {
	while (container->serializationCount > 0) {
		if (!loadItem(propStream, container, false, strict)) {
			g_logger().warn("Deserialization error for container item: {}", container->getID());
			return false;
		}
		container->serializationCount--;
	}

	uint8_t endAttr;
	if (!propStream.read<uint8_t>(endAttr) || endAttr != 0) {
		g_logger().warn("Deserialization error for container item: {}", container->getID());
		return false;
	}
	return true;
}

bool IOMapSerialize::loadItem(PropStream &propStream, const std::shared_ptr<Cylinder> &parent, bool isHouseItem, bool strict) {
	uint16_t id;
	if (!propStream.read<uint16_t>(id)) {
		return false;
	}

	std::shared_ptr<Tile> tile = nullptr;
	if (parent->getParent() == nullptr) {
		tile = parent->getTile();
	}

	const ItemType &iType = Item::items[id];
	if (iType.isBed() || iType.movable || !tile || iType.isCarpet() || iType.isTrashHolder()) {
		// create a new item
		auto item = Item::CreateItem(id);
		if (item) {
			if (item->unserializeAttr(propStream)) {
				// Remove only not movable and not sleeper bed
				auto bed = item->getBed();
				if (isHouseItem && iType.isBed() && bed && bed->getSleeper() == 0 && !iType.movable) {
					return strict;
				}
				std::shared_ptr<Container> container = item->getContainer();
				if (container && !loadContainer(propStream, container, strict)) {
					return false;
				}

				parent->internalAddThing(item);
				item->startDecaying();
			} else {
				g_logger().warn("Deserialization error in {}", id);

				return false;
			}

			if (const auto &bed = item->getBed()) {
				if (bed->getSleeper() != 0) {
					bedsToCheck.push_back(bed);
				}
			}
		} else if (strict) return false;
	} else {
		// Stationary items like doors/beds/blackboards/bookcases
		std::shared_ptr<Item> item = nullptr;
		if (const TileItemVector* items = tile->getItemList()) {
			for (auto &findItem : *items) {
				if (findItem->getID() == id) {
					item = findItem;
					break;
				} else if (iType.m_transformOnUse && findItem->getID() == iType.m_transformOnUse) {
					item = findItem;
					break;
				} else if (iType.isDoor() && findItem->getDoor()) {
					item = findItem;
					break;
				} else if (iType.isBed() && findItem->getBed()) {
					item = findItem;
					break;
				}
			}
		}

		if (item) {
			if (item->unserializeAttr(propStream)) {
				std::shared_ptr<Container> container = item->getContainer();
				if (container && !loadContainer(propStream, container, strict)) {
					return false;
				}

				if (!g_game().transformItem(item, id) && strict) return false;
			} else {
				g_logger().warn("Deserialization error in {}", id);
				if (strict) return false;
			}
		} else {
			if (strict) return false;
			// The map changed since the last save, just read the attributes
			auto dummy = Item::CreateItem(id);
			if (dummy) {
				dummy->unserializeAttr(propStream);
				std::shared_ptr<Container> container = dummy->getContainer();
				if (container) {
					if (!loadContainer(propStream, container)) {
						return false;
					}
				} else if (std::shared_ptr<BedItem> bedItem = std::dynamic_pointer_cast<BedItem>(dummy)) {
					uint32_t sleeperGUID = bedItem->getSleeper();
					if (sleeperGUID != 0) {
						g_game().removeBedSleeper(sleeperGUID);
					}
				}
			}
		}
	}
	return true;
}

void IOMapSerialize::saveItem(PropWriteStream &stream, const std::shared_ptr<Item> &item) {
	const auto &container = item->getContainer();

	// Write ID & props
	stream.write<uint16_t>(item->getID());
	item->serializeAttr(stream);

	if (container) {
		// Hack our way into the attributes
		stream.write<uint8_t>(ATTR_CONTAINER_ITEMS);
		stream.write<uint32_t>(container->size());
		for (auto it = container->getReversedItems(), end = container->getReversedEnd(); it != end; ++it) {
			saveItem(stream, *it);
		}
	}

	stream.write<uint8_t>(0x00); // attr end
}

void IOMapSerialize::saveTile(PropWriteStream &stream, const std::shared_ptr<Tile> &tile) {
	const TileItemVector* tileItems = tile->getItemList();
	if (!tileItems) {
		return;
	}

	std::list<std::shared_ptr<Item>> items;
	uint16_t count = 0;
	for (auto &item : *tileItems) {
		if (item->getID() == ITEM_BATHTUB_FILLED_NOTMOVABLE) {
			std::shared_ptr<Item> tub = Item::CreateItem(ITEM_BATHTUB_FILLED);
			items.push_front(tub);
			++count;
			continue;
		} else if (!item->isSavedToHouses()) {
			continue;
		}

		items.push_front(item);
		++count;
	}

	if (!items.empty()) {
		const Position &tilePosition = tile->getPosition();
		stream.write<uint16_t>(tilePosition.x);
		stream.write<uint16_t>(tilePosition.y);
		stream.write<uint8_t>(tilePosition.z);

		stream.write<uint32_t>(count);
		for (const std::shared_ptr<Item> &item : items) {
			saveItem(stream, item);
		}
	}
}

bool IOMapSerialize::loadHouseInfo() {
	Database &db = Database::getInstance();

	bool read = false;
	DBResult_ptr result = db.storeQuery("SELECT `id`, `owner`, `new_owner`, `rent`, `bidder`, `bidder_name`, `highest_bid`, `internal_bid`, `bid_end_date`, `state`, `transfer_status` FROM `houses`", read);
	if (!read) throw std::runtime_error("Could not load persisted house auctions");
	if (!result) {
		return true;
	}

	do {
		auto houseId = result->getNumber<uint32_t>("id");
		const auto house = g_game().map.houses.getHouse(houseId);
		if (!house) {
			continue;
		}

		auto owner = result->getNumber<uint32_t>("owner");
		auto newOwner = result->getNumber<int32_t>("new_owner");
		uint32_t bidder = result->getNumber<uint32_t>("bidder");
		std::string bidderName = result->getString("bidder_name");
		uint32_t highestBid = result->getNumber<uint32_t>("highest_bid");
		uint32_t internalBid = result->getNumber<uint32_t>("internal_bid");
		uint32_t bidEndDate = result->getNumber<uint32_t>("bid_end_date");
		auto state = static_cast<CyclopediaHouseState>(result->getNumber<uint16_t>("state"));
		auto transferStatus = result->getNumber<bool>("transfer_status");
		const auto reservedRent = bidder && (state == CyclopediaHouseState::Available || transferStatus) ? result->getNumber<uint32_t>("rent") : 0;
		const auto timeNow = std::chrono::duration_cast<std::chrono::seconds>(std::chrono::system_clock::now().time_since_epoch()).count();

		// Transfer house owner
		auto isTransferOnRestart = g_configManager().getBoolean(TOGGLE_HOUSE_TRANSFER_ON_SERVER_RESTART);
		if (isTransferOnRestart && newOwner >= 0) {
			if (bidder && (state == CyclopediaHouseState::Available || transferStatus)) {
				throw std::runtime_error(fmt::format("House {} has both a scheduled owner change and auction escrow", houseId));
			}
			HouseAuctionState auction;
			if (newOwner) auction.state = CyclopediaHouseState::Rented;
			house->setAuctionState({bidder, bidderName, highestBid, internalBid, bidEndDate, state, transferStatus, reservedRent});
			const auto destination = static_cast<uint32_t>(newOwner);
			const StartupHouseOwnership ownership {destination, owner == destination ? 0 : owner, newOwner};
			if (!settleHouseAuction(house, std::move(auction), {}, {}, ownership)) {
				throw std::runtime_error(fmt::format("Could not settle scheduled ownership change for house {}", houseId));
			}
			continue;
		} else if (state == CyclopediaHouseState::Available && timeNow > bidEndDate && bidder > 0) {
			g_logger().debug("[BID] - Setting house id '{}' owner to player GUID '{}'", houseId, bidder);
			const auto refund = highestBid < internalBid ? internalBid - highestBid : 0;
			HouseAuctionState auction;
			auction.state = CyclopediaHouseState::Rented;
			house->setAuctionState({bidder, bidderName, highestBid, internalBid, bidEndDate, state, transferStatus, reservedRent});
			if (!settleHouseAuction(house, std::move(auction), {bidder, refund}, {}, StartupHouseOwnership {bidder})) {
				throw std::runtime_error(fmt::format("Could not settle auction for house {}", houseId));
			}
			continue;
		} else if (state == CyclopediaHouseState::Transfer && timeNow > bidEndDate && bidder > 0) {
			g_logger().debug("[TRANSFER] - Removing house id '{}' from owner GUID '{}' and transfering to new owner GUID '{}'", houseId, owner, bidder);
			HouseAuctionState auction;
			auction.state = CyclopediaHouseState::Rented;
			const auto newHouseOwner = transferStatus ? bidder : owner;
			const auto credit = transferStatus ? AuctionBalanceChange {owner, internalBid} : AuctionBalanceChange {};
			if (transferStatus && !owner) throw std::runtime_error(fmt::format("House {} has transfer escrow without a seller", houseId));
			house->setAuctionState({bidder, bidderName, highestBid, internalBid, bidEndDate, state, transferStatus, reservedRent});
			const StartupHouseOwnership ownership {newHouseOwner, transferStatus && isTransferOnRestart ? owner : 0};
			if (!settleHouseAuction(house, std::move(auction), credit, {}, ownership)) {
				throw std::runtime_error(fmt::format("Could not settle transfer for house {}", houseId));
			}
			continue;
		} else if (state == CyclopediaHouseState::MoveOut && timeNow > bidEndDate) {
			g_logger().debug("[MOVE OUT] - Removing house id '{}' owner", houseId);
			house->setAuctionState({bidder, bidderName, highestBid, internalBid, bidEndDate, state, transferStatus, reservedRent});
			const StartupHouseOwnership ownership {0, isTransferOnRestart ? owner : 0};
			if (!settleHouseAuction(house, {}, {}, {}, ownership)) {
				throw std::runtime_error(fmt::format("Could not complete move-out for house {}", houseId));
			}
			continue;
		} else {
			house->setOwner(owner, false);
			house->setState(state);
		}
		house->setAuctionState({bidder, std::move(bidderName), highestBid, internalBid, bidEndDate, house->getState(), transferStatus, reservedRent});
	} while (result->next());

	result = db.storeQuery("SELECT `house_id`, `listid`, `list` FROM `house_lists`");
	if (result) {
		do {
			const auto &house = g_game().map.houses.getHouse(result->getNumber<uint32_t>("house_id"));
			if (house) {
				auto listId = result->getNumber<uint32_t>("listid");
				auto list = result->getString("list");
				house->setAccessList(listId, list);
			}
		} while (result->next());
	}
	return true;
}

bool IOMapSerialize::saveHouseInfo() {
	std::unique_lock auctionLock(houseAuctionMutex, std::try_to_lock);
	if (!auctionLock.owns_lock()) return false;
	for (const auto &[_, house] : g_game().map.houses.getHouses()) {
		if (house->hasPendingAuctionSettlement()) return false;
	}
	bool success = DBTransaction::executeWithinTransaction([]() {
		return SaveHouseInfoGuard();
	});

	if (!success) {
		g_logger().error("[{}] Error occurred saving houses info", __FUNCTION__);
	}

	return success;
}

bool IOMapSerialize::SaveHouseInfoGuard() {
	Database &db = Database::getInstance();

	std::ostringstream query;
	DBInsert houseUpdate("INSERT INTO `houses` (`id`, `owner`, `paid`, `warnings`, `name`, `town_id`, `rent`, `size`, `beds`, `bidder`, `bidder_name`, `highest_bid`, `internal_bid`, `bid_end_date`, `state`, `transfer_status`) VALUES ");
	houseUpdate.upsert({ "owner", "paid", "warnings", "name", "town_id", "rent", "size", "beds", "bidder", "bidder_name", "highest_bid", "internal_bid", "bid_end_date", "state", "transfer_status" });

	for (const auto &[key, house] : g_game().map.houses.getHouses()) {
		auto stateValue = magic_enum::enum_integer(house->getState());
		std::string values = fmt::format("{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}", house->getId(), house->getOwner(), house->getPaidUntil(), house->getPayRentWarnings(), db.escapeString(house->getName()), house->getTownId(), house->getRent(), house->getSize(), house->getBedCount(), house->getBidder(), db.escapeString(house->getBidderName()), house->getHighestBid(), house->getInternalBid(), house->getBidEndDate(), std::to_string(stateValue), (house->getTransferStatus() ? 1 : 0));

		if (!houseUpdate.addRow(values)) {
			return false;
		}
	}

	if (!houseUpdate.execute()) {
		return false;
	}

	DBInsert listUpdate("INSERT INTO `house_lists` (`house_id` , `listid` , `list`, `version`) VALUES ");
	listUpdate.upsert({ "list", "version" });
	auto version = getTimeUsNow();

	for (const auto &[key, house] : g_game().map.houses.getHouses()) {
		std::string listText;
		if (house->getAccessList(GUEST_LIST, listText) && !listText.empty()) {
			query << house->getId() << ',' << GUEST_LIST << ',' << db.escapeString(listText) << ',' << version;
			if (!listUpdate.addRow(query)) {
				return false;
			}

			listText.clear();
		}

		if (house->getAccessList(SUBOWNER_LIST, listText) && !listText.empty()) {
			query << house->getId() << ',' << SUBOWNER_LIST << ',' << db.escapeString(listText) << ',' << version;
			if (!listUpdate.addRow(query)) {
				return false;
			}

			listText.clear();
		}

		for (const std::shared_ptr<Door> &door : house->getDoors()) {
			if (door->getAccessList(listText) && !listText.empty()) {
				query << house->getId() << ',' << door->getDoorId() << ',' << db.escapeString(listText) << ',' << version;
				if (!listUpdate.addRow(query)) {
					return false;
				}

				listText.clear();
			}
		}
	}

	if (!listUpdate.execute()) {
		return false;
	}

	if (!db.executeQuery(fmt::format("DELETE FROM `house_lists` WHERE `version` < {}", version))) {
		return false;
	}

	return true;
}
