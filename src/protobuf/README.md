# protobuf

## Overview
Contains Protocol Buffer (`.proto`) schemas and CMake code-generation rules for client appearance metadata (`appearances.proto`) and recursive key-value store serialization (`kv.proto`).

## Interface
- `Canary.protobuf.appearances` (`[appearances.proto:Appearances]`, `[appearances.proto:Appearance]`, `[appearances.proto:AppearanceFlags]`, `[appearances.proto:FrameGroup]`, `[appearances.proto:SpriteInfo]`, `[appearances.proto:SpriteAnimation]`, `[appearances.proto:SpritePhase]`, `[appearances.proto:Box]`, `[appearances.proto:Coordinate]`, `[appearances.proto:SpecialMeaningAppearanceIds]`): Proto2 messages and enums (`[appearances.proto:PLAYER_ACTION]`, `[appearances.proto:ITEM_CATEGORY]`, `[appearances.proto:PLAYER_PROFESSION]`, `[appearances.proto:ANIMATION_LOOP_TYPE]`, `[appearances.proto:HOOK_TYPE]`, `[appearances.proto:FIXED_FRAME_GROUP]`) describing object, outfit, effect, and missile appearances and flags (`AppearanceFlagBank`, `AppearanceFlagWrite`, `AppearanceFlagWriteOnce`, `AppearanceFlagLight`, `AppearanceFlagHeight`, `AppearanceFlagShift`, `AppearanceFlagClothes`, `AppearanceFlagDefaultAction`, `AppearanceFlagMarket`, `AppearanceFlagNPC`, `AppearanceFlagAutomap`, `AppearanceFlagHook`, `AppearanceFlagLenshelp`, `AppearanceFlagChangedToExpire`, `AppearanceFlagCyclopedia`, `AppearanceFlagUpgradeClassification`, `AppearanceFlagSkillWheelGem`).
- `Canary.protobuf.kv` (`[kv.proto:ValueWrapper]`, `[kv.proto:ArrayType]`, `[kv.proto:KeyValuePair]`, `[kv.proto:MapType]`): Proto3 schema representing recursive typed key-value data (`str_value`, `int_value`, `double_value`, `array_value`, `map_value`, `bool_value`).
- `protobuf` CMake Target (`[CMakeLists.txt:protobuf]`): Compiles generated C++ protobuf sources and links `protobuf::libprotobuf`.

## Invariants
- `kv.proto` enforces single-active-type semantics on `ValueWrapper` via its `oneof value` union (`[kv.proto:ValueWrapper]`).
- `appearances.proto` uses `proto2` syntax with explicit field tags matching the Tibia client `appearances.dat` wire format (`[appearances.proto:Appearances]`).

## Side Effects
- Build-time C++ header/source generation (`appearances.pb.h`/`cc`, `kv.pb.h`/`cc`) in `${CMAKE_CURRENT_BINARY_DIR}` via `protobuf_generate` (`[CMakeLists.txt:protobuf_generate]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
