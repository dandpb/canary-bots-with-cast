# Stage 5 · Initial zoom out

Both fresh-context reviewers completed. The skeptical architect inspected entry
points, runtime boundaries and evidence. The inventive catalyst investigated
trade-offs in setup and the proposed guided walk. They sampled the high-level
documents and verified claims in local code.

| Finding | Initial assessment | Evidence |
| --- | --- | --- |
| A fresh WSL checkout does not own all the files Compose reads | Major. The documented setup makes local files, while the rendered mounts include fixed paths and an additional template override. Use one runtime root and preflight the actual bind sources. | `deployment/brain/SETUP.pt-BR.md:20,51`, `deployment/wsl/compose.yaml:132,160`, `deployment/wsl/setup.py:8,24` |
| Readers have to assemble an installation from unrelated pages | Major. Provide a selector in the existing deployment index for generic Compose, MyAAC/cast, WSL, Core QA, desktop and browser. | `README.md:204,282`, `deployment/README.md:4`, `docker/docker-compose.yml:60`, `deployment/core-qa/compose.yaml:42` |
| Desktop asset instructions mix protocol families | Major. The guide places legacy files under 1100 while selecting 1500. Pin a supported client build and document its actual layout. | `deployment/client/README.md:11,47`, `src/core.hpp:18`, `deployment/browser/package_client.py:199` |
| No feature-to-owner map | Major. The root lists bot behavior and directory names. Explain the shared core plus one selected datapack and route players and operators to the feature owner. | `README.md:14,490`, `src/canary_server.cpp:378`, `config.lua.dist:6` |
| Historical observations read as current | Major. Label the deployment and Brain evaluations by revision and environment. Preserve the original evidence. | `deployment/DEPLOYMENT_STATUS.md:46`, `deployment/brain/EVALUATION.md:47,65`, `data/scripts/globalevents/bot_manager.lua:417,514` |
| The Thais guide ties a walking test to real party membership | Advisory. A standalone guide session would remove party recovery complexity. It would also lose the party interface. Retain a real party if that interaction is a requirement. | `design_draft.md:9,36,63`, `src/creatures/players/bot/bot_brain.cpp:938` |
| Map data sounds fresher and broader than it is | Minor. The default shows persisted bot positions with filtering and caching. Explain that at the entry point. | `deployment/web/plugins/worldmap/README.md:5`, `deployment/web/plugins/worldmap/config.php:12`, `deployment/web/plugins/worldmap/pages/worldmap.php:30` |

The catalyst found no architectural trade-off requiring a redesign of the
native admission, completion fence or persistence witness.
