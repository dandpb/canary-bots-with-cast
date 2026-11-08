# Database (`database`)

## Overview
Groups database seeding schemas, runtime compatibility migrations, and population dumps for the Canary server.

## Subdirectories & Boundaries
- `bots`: [`./bots/README.md`](./bots/README.md) - Seeds the Canary MySQL/MariaDB database with bot runtime DDL, the `@god` and bot accounts (`account_id = 65000`), 997 bot players, outfit/mount storage grants, market item prices, house ownership/furniture, and runtime compatibility tables.
