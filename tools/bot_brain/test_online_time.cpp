#include "io/functions/player_online_time.hpp"
#include <cassert>
#include <iostream>

int main() {
	using player_persistence::onlineSeconds;
	assert(onlineSeconds(0, 1793750000) == 0); // Headless bot has no real login.
	assert(onlineSeconds(-1, 1793750000) == 0);
	assert(onlineSeconds(1793750010, 1793750000) == 0); // Clock moved backwards.
	assert(onlineSeconds(1793749900, 1793750000) == 100);
	assert(onlineSeconds(1793750000, 1793750000) == 0);
	std::cout << "PASS: real login duration retained; missing/future login adds no time\n";
}
