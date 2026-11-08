# enums

## Overview
Defines shared strongly-typed and unscoped C++ enumerations used across account management, item attributes and containers, exaltation forge actions, Lua script variants, object categories, and player systems (blessings, cyclopedia, status icons, and Wheel of Destiny).

## Interface
- Account Enumerations: `CoinTransactionType` & `CoinType` (`[account_coins.hpp:CoinTransactionType]`, `[account_coins.hpp:CoinType]`), `AccountErrors_t` (`[account_errors.hpp:AccountErrors_t]`), `GroupType` (`[account_group_type.hpp:GroupType]`), and `AccountType` (`[account_type.hpp:AccountType]`).
- Container & Item Enumerations: `ContainerSpecial_t` (`[container_type.hpp:ContainerSpecial_t]`), `ItemAttribute_t`, `ItemDecayState_t`, & `ItemAnimation_t` (`[item_attribute.hpp:ItemAttribute_t]`, `[item_attribute.hpp:ItemDecayState_t]`, `[item_attribute.hpp:ItemAnimation_t]`), and `ObjectCategory_t` (`[object_category.hpp:ObjectCategory_t]`).
- Forge & Lua Enumerations: `ForgeAction_t` (`[forge_conversion.hpp:ForgeAction_t]`) and `LuaVariantType_t` (`[lua_variant_type.hpp:LuaVariantType_t]`).
- Player Blessings & Icons: `Blessings` (`[player_blessings.hpp:Blessings]`), `PlayerIcon`, & `IconBakragore` (`[player_icons.hpp:PlayerIcon]`, `[player_icons.hpp:IconBakragore]`).
- Player Cyclopedia & House Auctions: `CyclopediaBadge_t`, `CyclopediaTitle_t`, `Summary_t`, `CyclopediaMapData_t`, `CyclopediaHouseState`, `HouseAuctionType`, `BidSuccessMessage`, `BidErrorMessage`, `TransferErrorMessage`, & `AcceptTransferErrorMessage` (`[player_cyclopedia.hpp:CyclopediaBadge_t]`, `[player_cyclopedia.hpp:CyclopediaTitle_t]`, `[player_cyclopedia.hpp:Summary_t]`, `[player_cyclopedia.hpp:CyclopediaMapData_t]`, `[player_cyclopedia.hpp:CyclopediaHouseState]`, `[player_cyclopedia.hpp:HouseAuctionType]`, `[player_cyclopedia.hpp:BidSuccessMessage]`, `[player_cyclopedia.hpp:BidErrorMessage]`, `[player_cyclopedia.hpp:TransferErrorMessage]`, `[player_cyclopedia.hpp:AcceptTransferErrorMessage]`).
- Player Wheel of Destiny: `WheelGemAction_t`, `WheelImproveGemGrade_t`, `WheelFragmentType_t`, `WheelGemAffinity_t`, `WheelGemQuality_t`, `WheelGemBasicModifier_t`, & `WheelGemSupremeModifier_t` (`[player_wheel.hpp:WheelGemAction_t]`, `[player_wheel.hpp:WheelImproveGemGrade_t]`, `[player_wheel.hpp:WheelFragmentType_t]`, `[player_wheel.hpp:WheelGemAffinity_t]`, `[player_wheel.hpp:WheelGemQuality_t]`, `[player_wheel.hpp:WheelGemBasicModifier_t]`, `[player_wheel.hpp:WheelGemSupremeModifier_t]`).

## Invariants
- `PlayerIcon::Count` must remain the final enumerator in `PlayerIcon` (`[player_icons.hpp:PlayerIcon]`).
- `OBJECTCATEGORY_FIRST` and `OBJECTCATEGORY_LAST` bound the valid range of `ObjectCategory_t` (`[object_category.hpp:ObjectCategory_t]`).
- `WheelGemBasicModifier_t` skips ordinal `32` (`Vocation_Mana_Capacity` is reserved/invalid) by explicitly assigning `Vocation_Mana_FireResistance = 33` (`[player_wheel.hpp:WheelGemBasicModifier_t]`).

## Side Effects
- None

## Verification
- Run: `ctest --test-dir build --output-on-failure`
