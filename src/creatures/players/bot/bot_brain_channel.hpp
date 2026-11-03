/**
 * Canary - A free and open-source MMORPG server emulator
 * License: https://github.com/opentibiabr/canary/blob/main/LICENSE
 */
#pragma once

#include "creatures/players/bot/bot_brain_protocol.hpp"
#include <array>
#include <cstring>
#include <cstdlib>
#include <chrono>
#include <deque>
#include <filesystem>
#include <fstream>
#include <memory>
#include <unordered_map>
#include <vector>
#include <fcntl.h>
#include <sys/file.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/un.h>
#include <unistd.h>

namespace botbrain {

	class Channel {
	public:
		explicit Channel(const std::string &directory) {
			if (directory.empty() || directory.size() > 80 || !std::filesystem::path(directory).is_absolute()
			    || std::filesystem::is_symlink(directory)) {
				throw std::runtime_error("invalid brain socket directory");
			}
			std::filesystem::create_directories(directory);
			chmod(directory.c_str(), 0700);
			path_ = directory + "/server.sock";
			worker_ = directory + "/worker.sock";
			lock_ = open((directory + "/server.lock").c_str(), O_CREAT | O_RDWR | O_NOFOLLOW | O_CLOEXEC, 0600);
			if (lock_ < 0 || flock(lock_, LOCK_EX | LOCK_NB) < 0) {
				if (lock_ >= 0) {
					close(lock_);
				}
				throw std::runtime_error("brain socket already owned");
			}
			fd_ = socket(AF_UNIX, SOCK_DGRAM | SOCK_NONBLOCK | SOCK_CLOEXEC, 0);
			sockaddr_un address {};
			address.sun_family = AF_UNIX;
			std::copy(path_.begin(), path_.end(), address.sun_path);
			struct stat status { };
			if (lstat(path_.c_str(), &status) == 0 && !S_ISSOCK(status.st_mode)) {
				close(fd_);
				close(lock_);
				throw std::runtime_error("brain endpoint is not a socket");
			}
			unlink(path_.c_str());
			if (fd_ < 0 || bind(fd_, reinterpret_cast<sockaddr*>(&address), sizeof(address)) < 0) {
				if (fd_ >= 0) {
					close(fd_);
				}
				close(lock_);
				throw std::runtime_error("cannot bind brain socket");
			}
			chmod(path_.c_str(), 0660);
			struct stat owner { };
			if (stat(directory.c_str(), &owner) == 0 && geteuid() == 0) {
				if (chown(path_.c_str(), owner.st_uid, owner.st_gid) != 0) {
					close(fd_);
					close(lock_);
					unlink(path_.c_str());
					throw std::runtime_error("cannot share brain socket with worker owner");
				}
			}
		}
		~Channel() {
			close(fd_);
			unlink(path_.c_str());
			close(lock_);
		}
		Channel(const Channel &) = delete;
		Channel &operator=(const Channel &) = delete;

		bool send(const nlohmann::json &packet) const {
			const auto encoded = packet.dump();
			if (encoded.size() > 32768) {
				return false;
			}
			sockaddr_un destination {};
			destination.sun_family = AF_UNIX;
			std::copy(worker_.begin(), worker_.end(), destination.sun_path);
			return sendto(fd_, encoded.data(), encoded.size(), MSG_DONTWAIT | MSG_NOSIGNAL, reinterpret_cast<sockaddr*>(&destination), sizeof(destination)) == static_cast<ssize_t>(encoded.size());
		}

		std::vector<nlohmann::json> receive() const {
			std::vector<nlohmann::json> packets;
			for (int count = 0; count < 12; ++count) {
				std::array<char, 32769> buffer {};
				sockaddr_un sender {};
				socklen_t length = sizeof(sender);
				const ssize_t size = recvfrom(fd_, buffer.data(), buffer.size(), MSG_DONTWAIT, reinterpret_cast<sockaddr*>(&sender), &length);
				if (size < 0) {
					break;
				}
				if (size > 32768 || std::string(sender.sun_path, strnlen(sender.sun_path, sizeof(sender.sun_path))) != worker_) {
					continue;
				}
				auto packet = nlohmann::json::parse(buffer.data(), buffer.data() + size, nullptr, false);
				if (!packet.is_discarded() && packet.is_object()) {
					packets.push_back(std::move(packet));
				}
			}
			return packets;
		}

	private:
		int fd_ = -1, lock_ = -1;
		std::string path_, worker_;
	};

	struct Session {
		std::deque<nlohmann::json> offers;
		nlohmann::json messages = nlohmann::json::array();
		std::unordered_map<std::string, nlohmann::json> outcomes;
		std::string lease, action = "follow", actionId;
		uint32_t leader = 0, generation = 0, script = 0, shop = 0, potions = 0;
		uint32_t target = 0;
		int64_t targetUntil = 0;
		uint8_t supplyStep = 0;
		uint64_t sequence = 0, xp = 0;
		int64_t lastPublish = 0, started = 0, lastMessage = 0, lastMove = 0, lastShopScan = 0;
		size_t waypoint = 0;
		uint32_t skipped = 0;
		double danger = 0;
	};

	struct Runtime {
		std::unique_ptr<Channel> channel;
		std::string mode = "disabled", world;
		std::vector<uint32_t> roster;
		std::unordered_map<uint32_t, Session> sessions;
		int64_t heartbeat = 0;
		int64_t lastHello = 0;
		uint64_t messageSequence = 0;

		Runtime() {
			const char* environment = std::getenv("CANARY_BRAIN_CONFIG");
			std::ifstream file(environment ? environment : "data/bot/brain.json");
			if (!file) {
				return;
			}
			auto config = nlohmann::json::parse(file, nullptr, false);
			if (config.is_discarded() || !config.is_object()) {
				throw std::runtime_error("invalid brain configuration");
			}
			mode = config.value("mode", "disabled");
			if (mode == "disabled") {
				return;
			}
			if (mode != "shadow" && mode != "active") {
				throw std::runtime_error("invalid brain mode");
			}
			roster = config.at("bots").get<std::vector<uint32_t>>();
			if (roster.empty() || roster.size() > 3) {
				throw std::runtime_error("brain supports one to three pilots");
			}
			world = std::to_string(getpid()) + "-" + std::to_string(std::chrono::steady_clock::now().time_since_epoch().count());
			channel = std::make_unique<Channel>(config.at("socket_directory").get<std::string>());
		}
	};

} // namespace botbrain
