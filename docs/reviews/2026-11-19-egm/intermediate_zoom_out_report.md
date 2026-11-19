# Stage 8 · Intermediate zoom out

The fresh reviewer completed the full-target reassessment using the Stage 5–7
reports and the proposed feature guide. They checked the source where the
proposed response would change how someone installs or designs a feature.

1. Fix the fresh WSL mounts and desktop client prerequisites before routing new
   readers to those guides. Keep the existing Lua template in the image and make
   a site-specific override explicit. Pin the desktop client independent of the
   browser packaging. `deployment/wsl/compose.yaml:132`,
   `deployment/wsl/game-entrypoint.py:53`, `deployment/client/README.md:11`.
2. Reuse the existing navigation. Put one feature route at the root, one
   deployment selector in the deployment index, and one M5 run selector in the
   fixture index. Link to owners for defaults and validation. A second full
   set of runbooks would add drift. `README.md:490`,
   `deployment/README.md:6`, `tests/fixture/README.md:11`.
3. Decide whether party membership is part of the Thais test. A client invite
   can make the party survive the player's forced removal. If party membership
   matters, the acceptance test needs a pending invite, removal and the chosen
   close, reject or restore behavior. `design_draft.md:37,67`,
   `src/game/game.cpp:8824`, `src/creatures/players/player.cpp:11533`,
   `src/creatures/players/grouping/party.cpp:168,517`.
4. Establish a local answer for the first `/guia` example. The game has spell
   definitions and a Lua player method for castable instant spells. Use those
   to measure what any retrieval or model path adds. Treat late-response
   authority and admission limits as separate requirements of any async flow.
   `src/lua/functions/creatures/player/player_functions.cpp:3721`,
   `data/scripts/spells/healing/light_healing.lua:22`,
   `deployment/brain/src/canary_brain/protocol.py:60`.

Coverage included the inventory, prior stage reports and selected source for
startup, client compatibility, navigation, QA evidence, party lifecycle and
spell lookup. This did not exercise a running game.
