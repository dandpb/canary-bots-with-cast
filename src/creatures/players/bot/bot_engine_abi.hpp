/**
 * Canary - A free and open-source MMORPG server emulator
 * Copyright (C) 2019-present OpenTibiaBR <opentibiabr@outlook.com>
 * Repository: https://github.com/opentibiabr/canary
 * License: https://github.com/opentibiabr/canary/blob/main/LICENSE
 */

#pragma once

// Same tag on executable and library. Check before factories or vtable calls.
#ifndef BOT_ENGINE_ABI_TAG
	#error "Build server and bot_engine together with the CMake ABI contract"
#endif

using BotEngineAbiFunc = const char* (*)();
using PrepareBotEngineFunc = bool (*)(IBotEngine*, char*, size_t);
