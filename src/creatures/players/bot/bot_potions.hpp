#pragma once

#include <cstdint>

namespace botsupplies {

	struct PotionDef {
		uint16_t id;
		uint32_t level;
		bool heals;
		bool restoresMana;
		uint32_t vocMask;
	};
	constexpr uint32_t VOC_SORC = 1u << 1, VOC_DRUID = 1u << 2, VOC_PAL = 1u << 3, VOC_KNIGHT = 1u << 4;
	constexpr uint32_t VOC_ANY = 0;

	// Server item IDs, weakest to strongest; shared with normal emergency consumable use.
	constexpr PotionDef kPotions[] = {
		{ 266, 0, true, false, VOC_ANY },
		{ 268, 0, false, true, VOC_ANY },
		{ 236, 50, true, false, VOC_PAL | VOC_KNIGHT },
		{ 237, 50, false, true, VOC_ANY },
		{ 238, 80, false, true, VOC_SORC | VOC_DRUID | VOC_PAL },
		{ 239, 80, true, false, VOC_KNIGHT },
		{ 7642, 80, true, true, VOC_PAL },
		{ 7643, 130, true, false, VOC_KNIGHT },
		{ 23373, 130, false, true, VOC_SORC | VOC_DRUID },
		{ 23374, 130, true, true, VOC_PAL },
		{ 23375, 200, true, false, VOC_KNIGHT },
	};

	constexpr uint32_t vocBit(uint8_t baseVoc) {
		return baseVoc >= 1 && baseVoc <= 4 ? (1u << baseVoc) : 0u;
	}

} // namespace botsupplies
