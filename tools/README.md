# Tools Subsystem (`tools`)

## Overview
Intermediate blueprint grouping and organizing offline developer tools, data pipeline scripts, and CSV schema validators for the Canary bot subsystem.

## Subdirectories & Boundaries
- `bot_csv`: [`./bot_csv/README.md`](./bot_csv/README.md) - Canonical RFC-4180 CSV writer, cross-file offline schema validator, and MySQL scratch importer for authored bot datasets.
- `cfg_importer`: [`./cfg_importer/README.md`](./cfg_importer/README.md) - Staged ingestion pipeline converting OTClient cavebot 1.3 `.cfg` hunt configs and metadata into authored CSV datasets.
- `bot_brain`: [`./bot_brain/README.md`](./bot_brain/README.md) - Bot startup, navigation and lifecycle regression harnesses.
- `bot_population_generator`: [`./bot_population_generator/README.md`](./bot_population_generator/README.md) - Population and seed-data generation.

## Verification
- Use the verification commands in each tool's guide.
