# Migrations

## Overview
Component package under `migrations` containing 57 files (`1.lua`..`9.lua`).

## Interface
- Defines 57 script/configuration files (`1.lua` through `9.lua`) [1.lua]
- `onUpdateDatabase()` [1.lua:onUpdateDatabase]
- `onUpdateDatabase()` [10.lua:onUpdateDatabase]
- `onUpdateDatabase()` [11.lua:onUpdateDatabase]
- `onUpdateDatabase()` [12.lua:onUpdateDatabase]
- `onUpdateDatabase()` [13.lua:onUpdateDatabase]
- `onUpdateDatabase()` [14.lua:onUpdateDatabase]
- `onUpdateDatabase()` [15.lua:onUpdateDatabase]
- `onUpdateDatabase()` [16.lua:onUpdateDatabase]
- `onUpdateDatabase()` [17.lua:onUpdateDatabase]
- `onUpdateDatabase()` [18.lua:onUpdateDatabase]
- `onUpdateDatabase()` [19.lua:onUpdateDatabase]
- `onUpdateDatabase()` [2.lua:onUpdateDatabase]
- `onUpdateDatabase()` [20.lua:onUpdateDatabase]
- `onUpdateDatabase()` [21.lua:onUpdateDatabase]
- `onUpdateDatabase()` [22.lua:onUpdateDatabase]
- `onUpdateDatabase()` [23.lua:onUpdateDatabase]
- `onUpdateDatabase()` [24.lua:onUpdateDatabase]
- `onUpdateDatabase()` [25.lua:onUpdateDatabase]
- `onUpdateDatabase()` [26.lua:onUpdateDatabase]
- `onUpdateDatabase()` [27.lua:onUpdateDatabase]
- `onUpdateDatabase()` [28.lua:onUpdateDatabase]
- `onUpdateDatabase()` [29.lua:onUpdateDatabase]
- `onUpdateDatabase()` [3.lua:onUpdateDatabase]
- `onUpdateDatabase()` [30.lua:onUpdateDatabase]

## Invariants
- Database queries require valid schema state and execute sequentially within `onUpdateDatabase` or startup hooks [1.lua:db.query]
- Database queries require valid schema state and execute sequentially within `onUpdateDatabase` or startup hooks [10.lua:db.query]
- Database queries require valid schema state and execute sequentially within `onUpdateDatabase` or startup hooks [11.lua:db.query]
- Database queries require valid schema state and execute sequentially within `onUpdateDatabase` or startup hooks [12.lua:db.query]
- Database queries require valid schema state and execute sequentially within `onUpdateDatabase` or startup hooks [13.lua:db.query]
- Database queries require valid schema state and execute sequentially within `onUpdateDatabase` or startup hooks [14.lua:db.query]
- Database queries require valid schema state and execute sequentially within `onUpdateDatabase` or startup hooks [15.lua:db.query]
- Database queries require valid schema state and execute sequentially within `onUpdateDatabase` or startup hooks [16.lua:db.query]
- Database queries require valid schema state and execute sequentially within `onUpdateDatabase` or startup hooks [17.lua:db.query]
- Database queries require valid schema state and execute sequentially within `onUpdateDatabase` or startup hooks [18.lua:db.query]
- Database queries require valid schema state and execute sequentially within `onUpdateDatabase` or startup hooks [19.lua:db.query]
- Database queries require valid schema state and execute sequentially within `onUpdateDatabase` or startup hooks [2.lua:db.query]

## Side Effects
- Executes SQL DDL/DML statements against the database via `db.query` [1.lua:db.query]
- Executes SQL DDL/DML statements against the database via `db.query` [10.lua:db.query]
- Executes SQL DDL/DML statements against the database via `db.query` [11.lua:db.query]
- Executes SQL DDL/DML statements against the database via `db.query` [12.lua:db.query]
- Executes SQL DDL/DML statements against the database via `db.query` [13.lua:db.query]
- Executes SQL DDL/DML statements against the database via `db.query` [14.lua:db.query]
- Executes SQL DDL/DML statements against the database via `db.query` [15.lua:db.query]
- Executes SQL DDL/DML statements against the database via `db.query` [16.lua:db.query]
- Executes SQL DDL/DML statements against the database via `db.query` [17.lua:db.query]
- Executes SQL DDL/DML statements against the database via `db.query` [18.lua:db.query]
- Executes SQL DDL/DML statements against the database via `db.query` [19.lua:db.query]
- Executes SQL DDL/DML statements against the database via `db.query` [2.lua:db.query]

## Verification
- Run: `ctest --test-dir build --output-on-failure`

### Existing Documentation: Database Migration System

This document provides an overview of the current database migration system for the project. The migration process has been streamlined to ensure that all migration scripts are automatically applied in order, making it easier to maintain database updates.

#### How It Works

The migration system is designed to apply updates to the database schema or data whenever a new server version is started. Migration scripts are stored in the `migrations` directory, and the system will automatically apply any scripts that have not yet been executed.

1. **Retrieve Current Database Version**:
   - The system first retrieves the current version of the database using `getDatabaseVersion()`.
   - This version is used to determine which migration scripts need to be executed.
2. **Migration Files Directory**:
   - All migration scripts are stored in the `migrations` directory.
   - Each migration script is named using a numerical pattern, such as `1.lua`, `2.lua`, etc.
   - The naming convention helps determine the order in which scripts should be applied.
3. **Execute Migration Scripts**:
   - The migration system iterates through the migration directory and applies each migration script that has a version greater than the current database version.
   - Only scripts that have not been applied are executed.
   - The Lua state (`lua_State* L`) is initialized to run each script.
4. **Update Database Version**:
   - After each migration script is successfully applied, the system updates the database version to reflect the applied change.
   - This ensures that the script is not re-applied on subsequent server startups.

#### Example Migration Script

```lua
-- Migration script example (for documentation purposes only)
local query = [[
    ALTER TABLE players ADD COLUMN new_feature_flag TINYINT(1) NOT NULL DEFAULT 0;
]]
db.execute(query)
```
