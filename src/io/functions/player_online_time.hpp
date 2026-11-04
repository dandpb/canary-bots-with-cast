#pragma once

#include <cstdint>
#include <ctime>

namespace player_persistence {

inline std::int64_t onlineSeconds(std::time_t login, std::time_t now) {
	// Headless bots do not pass through the normal player-login timestamp setup.
	if (login <= 0 || now <= login) {
		return 0;
	}
	return static_cast<std::int64_t>(now) - static_cast<std::int64_t>(login);
}

}
