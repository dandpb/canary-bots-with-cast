-- Fixture-only closed-world persistence audit. No native admission/scoring changes.
-- Game.monotonicMs() is UNIX EPOCH milliseconds in pinned C8.
local M = {}
local ffi = require("ffi")
ffi.cdef[[int open(const char *, int, ...); long write(int, const void *, unsigned long); int close(int);
unsigned char *SHA256(const unsigned char *, size_t, unsigned char *);]]
-- Pinned runtime ships the versioned OpenSSL library, not the development symlink.
local crypto = ffi.load("libcrypto.so.3")
local function sha256(bytes)
    local buffer = ffi.new("unsigned char[32]")
    assert(crypto.SHA256(bytes, #bytes, buffer) ~= nil, "audit hash failed")
    return (ffi.string(buffer, 32):gsub(".", function(c) return string.format("%02x", c:byte()) end))
end
M.sha256 = sha256

function M.new(binding, directory, encode)
    assert(configManager.getString(configKeys.SERVER_NAME) == "Canary M5 free QA")
    local state = { sequence = 0, deaths = 0, phase = "new" }
    local audit_fault = nil -- Private sticky latch; never trust C8 to propagate Lua errors.
    local function latch(reason)
        if not audit_fault then audit_fault = reason end
        state.audit_fault = audit_fault -- Diagnostic only; clearing this cannot clear the latch.
    end
    assert(ffi.os == "Linux" and ffi.arch == "arm64", "pinned Linux ARM64 audit ABI required")
    -- Linux open: WRONLY|CREAT|EXCL|NOFOLLOW|CLOEXEC; private0600, never truncate.
    local fd = ffi.C.open(directory .. "/audit.jsonl", 655553, ffi.new("unsigned int", 384))
    assert(fd >= 0, "fresh exclusive audit required")
    local function absent()
        for _, player in pairs(Game.getPlayers()) do
            if player:getGuid() == binding.bot_id or player:getId() == state.runtime_id then return false end
        end
        return true
    end
    local function emit(kind, extra)
        local player = assert(state.player)
        assert(player:getGuid() == binding.bot_id and player:getId() == state.runtime_id)
        state.sequence = state.sequence + 1
        local row = { version = 1, binding = binding, sequence = state.sequence,
            kind = kind, runtime_id = state.runtime_id, clock = "unix_epoch_ms",
            epoch_ms = Game.monotonicMs(), xp = player:getExperience(), level = player:getLevel(),
            deaths = state.deaths, removed = player:isRemoved() }
        if kind ~= "attached" then row.native_status_json = Game.botCommand("_global", "brain status") end
        for key, value in pairs(extra or {}) do row[key] = value end
        local bytes = encode(row) .. "\n"
        assert(#bytes <= 16384, "oversized audit record")
        local written = 0
        while written < #bytes do
            local chunk = bytes:sub(written + 1)
            local count = tonumber(ffi.C.write(fd, chunk, #chunk))
            assert(count > 0, "audit write failed")
            written = written + count
        end
        return bytes, row.sequence, row
    end
    local function protect(operation, allow_fault)
        return function(...)
            if audit_fault and not allow_fault then error("audit fault latched: " .. audit_fault) end
            local ok, result = pcall(operation, ...)
            if not ok then
                latch("audit callback failed") -- Set BEFORE fallible diagnostics/rethrow.
                -- Best effort poison even an already-written seal. Keep the FD open until
                -- clean process exit so a late callback cannot leave a valid last pair.
                pcall(emit, "audit_fault", { fault = true })
                error(result)
            end
            return result
        end
    end
    state.attach = protect(function(player)
        assert(state.phase == "new" and player:getGuid() == binding.bot_id and not player:isRemoved())
        state.player = player -- Strong shared Player userdata, retained after removal.
        state.runtime_id = player:getId()
        assert(player:registerEvent("M5PersistenceDeath"))
        state.phase = "live"
        emit("attached")
    end)
    state.death = protect(function(player)
        -- A death can occur INSIDE synchronous shutdown. Latch/count before ANY
        -- identity check, serialization, write or error that C8 might swallow.
        latch("death observed")
        state.deaths = state.deaths + 1
        assert((state.phase == "live" or state.phase == "stopping" or state.phase == "sealed")
            and player:getGuid() == binding.bot_id and player:getId() == state.runtime_id)
        emit("death") -- A zero-loss death is disqualifying too.
        return true
    end, true)
    state.think = protect(function()
        if state.phase == "new" then return true end
        if state.phase ~= "live" then return true end
        local request = io.open(directory .. "/stop.request", "rb")
        if not request then emit("heartbeat"); return true end
        local body = request:read(513); assert(request:close())
        assert(body == "q72-stop-v1\n" .. binding.run_id .. "\n" .. binding.stop_nonce .. "\n", "wrong stop request")
        assert(Game.getGameState() == GAME_STATE_NORMAL and not state.player:isRemoved())
        state.phase = "stopping" -- One request, no retry or re-entry.
        local pre, pre_sequence, before = emit("pre_shutdown", { game_state = "normal" })
        logger.info("[M5Persistence] pre " .. binding.stop_nonce)
        assert(Game.setGameState(GAME_STATE_SHUTDOWN)) -- Synchronous callback/removal/saveAll boundary.
        assert(not audit_fault, "audit fault during shutdown")
        assert(Game.getGameState() == GAME_STATE_SHUTDOWN and state.player:isRemoved() and absent())
        assert(state.player:getExperience() == before.xp and state.player:getLevel() == before.level and state.deaths == before.deaths, "shutdown mutated progression")
        emit("post_remove", { game_state = "shutdown", roster_absent = true,
            pre_sequence = pre_sequence, pre_sha256 = sha256(pre) })
        logger.info("[M5Persistence] post " .. binding.stop_nonce)
        state.phase = "sealed"
        -- Deliberately retain the descriptor until process exit: unexpected late
        -- death/fault records invalidate the terminal pair. Host fsync is still required.
        return true
    end)
    return state
end
return M
