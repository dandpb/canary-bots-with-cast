#pragma once

#include <cstdint>
#include <optional>
#include <string>

namespace IOStoreOrders {
	struct Order {
		uint64_t id;
		uint32_t playerGuid;
		uint32_t accountId;
		uint32_t offerId;
		bool transferable;
		uint32_t amount;
		std::string detail;
		std::string state;
	};

	struct Reservation {
		uint64_t id = 0;
		const char* status = "refused";
	};

	Reservation reserve(uint32_t playerGuid, uint32_t accountId, uint32_t offerId, bool transferable, uint32_t amount, const std::string &detail);
	std::optional<Order> get(uint64_t id);
	bool claim(uint64_t id, uint32_t playerGuid);
	bool finish(uint64_t id, uint32_t playerGuid);
	const char* resolve(uint64_t id, bool refund);
}
