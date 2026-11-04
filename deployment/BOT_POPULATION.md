# Selecting a smaller bot population

`botPlayersOnline` is the total number of native bots loaded at startup, including
the selected AI companions. Characters outside that population retain their
database records, inventory, XP and saved state.

To keep a population near the levels of existing companions, configure their
character GUIDs in `config.lua`:

```lua
botPlayersOnline = 100
botPopulationReferenceBots = "65045,65004,65003"
```

Use GUIDs that belong to the configured bot account and are not deleted. This
does not enable the AI bridge or select its pilots; retain the matching server
and worker configurations described in [brain/README.md](brain/README.md).

At each startup the server reads current character levels from the database.
Every reference bot is included. Remaining slots go to bots with the smallest
absolute level difference from any reference; equal distances are resolved by
GUID. For example, references at levels 11, 13 and 90 give level 14 a distance
of 1 and level 40 a distance of 27. Repeated GUIDs count once. There are at most
`botPlayersOnline` loaded bots, or the available pool size if smaller.

An invalid/missing reference or a target smaller than the number of distinct
references stops bot loading with a `Population selection stopped` error. The
server does not silently load a different population. An empty or whitespace-only
`botPopulationReferenceBots` preserves the original stratified selection. When
references are configured, they take precedence over the single-bot performance
test override.

This is a startup selection, not continuous level matching. Build and deploy the
matching game binary and `libbot_engine.so`, then restart the game service after
changing it. The normal 50-bot startup batches and hibernation remain in effect;
hibernating bots are registered members of the population. A later restart can
select a different set as characters gain levels.
