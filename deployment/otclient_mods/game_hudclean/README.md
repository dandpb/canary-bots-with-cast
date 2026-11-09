# Game HUD Clean Module (`game_hudclean`)

## Overview

OTClient module (`game_hudclean`) that declutters the client interface by masking unassigned action bar slots when bars are locked and stripping action bar background strips and panel lock stubs in extended view mode (`mode == 2`).

## Interface

- `[game_hudclean.otmod:Module]` — Sandboxed autoload OTClient module definition (`autoload: true`, `sandboxed: true`, `scripts: [ hudclean ]`, `@onLoad: init()`, `@onUnload: terminate()`).
- `[hudclean.lua:init]` — Installs monkey-patch wrappers on `game_actionbar` and `game_interface`, connects `onGameStart` to `g_game`, and schedules `maskAll` via `addEvent` if `g_game.isOnline()` is true.
- `[hudclean.lua:terminate]` — Disconnects `onGameStart` from `g_game`, restores chrome via `applyChrome(false)`, restores all action-bar slots via `unmaskAll()`, and removes monkey-patches via `uninstall()`.
- `[hudclean.lua:onGameStart]` — Event handler connected to `g_game.onGameStart` that schedules `maskAll` via `addEvent`.
- `[hudclean.lua:refresh]` — Public helper invoking `maskAll()` to re-apply slot masking across all 9 action bars.
- `[hudclean.lua:status]` — Public helper logging current view mode (`modules.game_interface.currentViewMode`), chrome stash state (`chromeStash`), and installed patch count (`table.size(WRAPPER)`) via `pinfo`.

## Invariants

- `[hudclean.lua:STRIP_BARS]` / `[hudclean.lua:BAR_COUNT]` — Only action bars 1 through 3 (`STRIP_BARS = 3`) are targeted for background image stripping; action bars 1 through 9 (`BAR_COUNT = 9`) are scanned for slot masking.
- `[hudclean.lua:slotIds]` — Action bar slot widget IDs must match `^(%d+)%.(%d+)$` (`barId.buttonId`) and the widget must not be destroyed.
- `[hudclean.lua:isAssigned]` — Fails open (`return true`) if `api` or `api.getMapping` is missing or if `pcall(api.getMapping, barId, buttonId)` errors; otherwise returns true iff `entry ~= nil and entry.actionsetting ~= nil`.
- `[hudclean.lua:applySlot]` — Unassigned slots on locked bars are hidden in-place using `widget:setOpacity(0)` and `widget:setEnabled(false)` (rather than `setVisible(false)`) to preserve layout geometry while blocking mouse events; unlocked or assigned slots get `setOpacity(1)` and `setEnabled(true)`.
- `[hudclean.lua:maskSlot]` — Captures `barId, buttonId` via `slotIds` before calling stock `updateButton` or `clearButton` so the recreated/updated child (`barId .. '.' .. buttonId`) is re-masked afterwards.
- `[hudclean.lua:applyChrome]` — Stashes each target widget's original `getImageSource()` or `getOpacity()` in `chromeStash` only when `nil`, making repeated `applyChrome(true)` calls idempotent without overwriting original values.
- `[hudclean.lua:uninstall]` — Restores `target[fnName] = ORIGINAL[key]` only if `target[fnName] == wrapper`, preventing stale closures from overwriting freshly reloaded module functions.

## Side Effects

- `[hudclean.lua:installPatches]` — Monkey-patches `modules.game_actionbar.updateVisibleWidgets`, `modules.game_actionbar.changeLockStatus`, `modules.game_actionbar.setupActionBar`, `modules.game_actionbar.updateButton`, `modules.game_actionbar.clearButton`, and `modules.game_interface.setupViewMode`.
- `[hudclean.lua:applySlot]` / `[hudclean.lua:unmaskAll]` — Mutates action bar slot widgets across bars 1..9 via `widget:setOpacity(1 or 0)` and `widget:setEnabled(true or false)`.
- `[hudclean.lua:applyChrome]` — In extended view (`mode == 2`), clears background strips on action bars 1..3 via `widget:setImageSource('')` and sets opacity to `0` on `lockLeftPanel`, `lockRightPanel`, `lockPanel` (`LOCK_STUB_IDS`), and `interface.getBottomSplitter()`; restores stashed image sources and opacities when `on == false`.
- `[hudclean.lua:init]` — Connects/disconnects `g_game.onGameStart` callback and schedules deferred execution on the event dispatcher via `addEvent`.

## Verification

- Run: `ctest --test-dir build --output-on-failure`
