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
#include <string_view>
#include <unordered_map>
#include <vector>
#include <fcntl.h>
#include <sys/file.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/un.h>
#include <unistd.h>

class Creature;

namespace botbrain {

	void retainTarget(uint32_t guid, const std::shared_ptr<Creature> &target);

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
			return sendEncoded(encoded);
		}

		bool sendEncoded(std::string_view encoded) const {
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

	class TelemetryOutbox {
	public:
		explicit TelemetryOutbox(size_t maxFrames = 64, size_t maxBytes = 64 * 1024) :
			maxFrames_(maxFrames), maxBytes_(maxBytes) { }

		void beginTick() {
			attemptsRemaining_ = 2;
			blockedThisTick_ = false;
		}

		bool enqueue(const nlohmann::json &packet) {
			if (!isTelemetry(packet)) {
				return false;
			}
			const auto encoded = packet.dump();
			if (encoded.size() > 32768 || pending_.size() >= maxFrames_ || encoded.size() > maxBytes_ - pendingBytes_) {
				++overflowFrames_;
				return false;
			}
			pending_.push_back({ packet.at("sequence").get<uint64_t>(), encoded });
			pendingBytes_ += encoded.size();
			return true;
		}

		// A successful admission is distinct from a successful kernel send.
		bool publish(Channel &channel, const nlohmann::json &packet) {
			if (!isTelemetry(packet)) {
				return false;
			}
			flush(channel);
			const bool admitted = enqueue(packet);
			if (admitted) {
				flush(channel);
			}
			return admitted;
		}

		size_t flush(Channel &channel) {
			size_t attempts = 0;
			while (!pending_.empty() && attemptsRemaining_ > 0 && !blockedThisTick_) {
				--attemptsRemaining_;
				++attempts;
				const auto &frame = pending_.front();
				if (!channel.sendEncoded(frame.encoded)) {
					blockedThisTick_ = true;
					break;
				}
				acceptedSequence_ = frame.sequence;
				pendingBytes_ -= frame.encoded.size();
				pending_.pop_front();
			}
			return attempts;
		}

		void discard() {
			discardedFrames_ += pending_.size();
			pending_.clear();
			pendingBytes_ = 0;
		}

		size_t pendingFrames() const {
			return pending_.size();
		}
		size_t pendingBytes() const {
			return pendingBytes_;
		}
		uint64_t acceptedSequence() const {
			return acceptedSequence_;
		}
		uint64_t overflowFrames() const {
			return overflowFrames_;
		}
		uint64_t discardedFrames() const {
			return discardedFrames_;
		}

		nlohmann::json status(const std::string &world, uint32_t guid, int64_t captured, uint64_t issued) const {
			return telemetryStatus(world, guid, captured, issued, acceptedSequence_, pending_.size(), pendingBytes_, overflowFrames_, discardedFrames_);
		}

	private:
		struct Frame {
			uint64_t sequence;
			std::string encoded;
		};
		static bool isTelemetry(const nlohmann::json &packet) {
			return packet.is_object() && packet.contains("type") && packet["type"] == "telemetry";
		}
		std::deque<Frame> pending_;
		size_t maxFrames_, maxBytes_, pendingBytes_ = 0;
		uint64_t acceptedSequence_ = 0, overflowFrames_ = 0, discardedFrames_ = 0;
		size_t attemptsRemaining_ = 2;
		bool blockedThisTick_ = false;
	};

	struct Session {
		std::deque<nlohmann::json> offers;
		nlohmann::json messages = nlohmann::json::array();
		std::unordered_map<std::string, nlohmann::json> outcomes;
		std::string lease, action = "follow", actionId;
		std::array<uint16_t, 3> home {};
		uint32_t leader = 0, generation = 0, script = 0, shop = 0, potions = 0;
		uint32_t target = 0;
		int64_t targetUntil = 0;
		uint8_t supplyStep = 0;
		uint64_t sequence = 0, xp = 0;
		uint64_t telemetrySequence = 0, deaths = 0;
		TelemetryOutbox delivery;
		// One admission for this session lifetime; never evicted or replaced by retries.
		nlohmann::json admission;

		template <typename Snapshot>
		nlohmann::json admit(const nlohmann::json &request, const std::string &world, uint32_t guid, const std::string &source, bool dirty, Snapshot snapshot) {
			if (request.size() != 5 || request.value("version", nlohmann::json()) != 1
			    || request.value("type", nlohmann::json()) != "telemetry_admit"
			    || request.value("world", nlohmann::json()) != world
			    || request.value("bot_id", nlohmann::json()) != guid
			    || !request.contains("nonce") || !request["nonce"].is_string()
			    || request["nonce"].get<std::string>().empty() || request["nonce"].get<std::string>().size() > 80) {
				throw std::runtime_error("invalid admission identity");
			}
			if (!admission.is_null()) {
				if (admission.at("nonce") != request.at("nonce") || admission.at("world") != world || admission.at("bot_id") != guid) {
					throw std::runtime_error("admission conflict");
				}
				return admission;
			}
			const nlohmann::json initial = snapshot();
			if (initial.at("world") != world || initial.at("bot").at("id") != guid) {
				throw std::runtime_error("invalid admission observation");
			}
			const auto captured = initial.at("captured_ms").get<int64_t>();
			if (offers.size() >= 12) {
				offers.pop_front();
			}
			offers.push_back(initial);
			auto event = telemetry(world, guid, ++telemetrySequence, captured, deaths, "alive");
			event["run_nonce"] = request.at("nonce");
			const bool queued = delivery.enqueue(event);
			std::string fault;
			if (dirty || source.empty() || source == "unknown") {
				fault = "source_unqualified";
			} else if (!queued || delivery.overflowFrames() || delivery.discardedFrames()) {
				fault = "telemetry_loss";
			}
			admission = { { "version", 1 }, { "type", "telemetry_admitted" }, { "world", world }, { "bot_id", guid }, { "nonce", request.at("nonce") }, { "begin_sequence", telemetrySequence }, { "captured_ms", captured }, { "deaths", deaths }, { "observation", initial }, { "source", source }, { "source_dirty", dirty }, { "fault", fault } };
			return admission;
		}

		bool unavailableReported = false;

		nlohmann::json fence(const nlohmann::json &request, Channel &channel, const std::string &world, uint32_t guid, int64_t captured, bool available) {
			if (admission.is_null() || request.size() != 6 || request.value("version", nlohmann::json()) != 1
			    || request.value("type", nlohmann::json()) != "telemetry_fence"
			    || request.value("world", nlohmann::json()) != world || admission.at("world") != world
			    || request.value("bot_id", nlohmann::json()) != guid || admission.at("bot_id") != guid
			    || request.value("admission_nonce", nlohmann::json()) != admission.at("nonce")
			    || !request.contains("nonce") || !request["nonce"].is_string()
			    || request["nonce"].get<std::string>().empty() || request["nonce"].get<std::string>().size() > 80) {
				throw std::runtime_error("invalid fence identity");
			}
			delivery.flush(channel);
			auto reply = delivery.status(world, guid, captured, telemetrySequence);
			reply["fence_nonce"] = request.at("nonce");
			reply["fault"] = available && !unavailableReported ? "" : "bot_unavailable";
			return reply;
		}

		int64_t lastTelemetry = 0;
		int64_t lastDeliveryStatus = 0;
		int64_t lastPublish = 0, started = 0, lastMessage = 0, lastMove = 0, lastShopScan = 0;
		size_t waypoint = 0;
		uint32_t skipped = 0;
		double danger = 0;
	};

	struct Runtime {
		std::unique_ptr<Channel> channel;
		std::string mode = "disabled", world;
		std::vector<uint32_t> roster;
		uint32_t autonomous = 0;
		bool keepAwake = false;
		std::unordered_map<uint32_t, Session> sessions;
		int64_t heartbeat = 0;
		int64_t lastHello = 0;
		uint64_t messageSequence = 0;

		void beginTelemetryTick() {
			for (const auto guid : roster) {
				sessions[guid].delivery.beginTick();
			}
		}

		void flushTelemetry() {
			if (!channel) {
				return;
			}
			for (const auto guid : roster) {
				if (auto session = sessions.find(guid); session != sessions.end()) {
					session->second.delivery.flush(*channel);
				}
			}
		}

		void sendDeliveryStatus(bool force = false) {
			if (!channel) {
				return;
			}
			for (auto &[guid, session] : sessions) {
				const auto captured = std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();
				if (!force && captured - session.lastDeliveryStatus < 1000) {
					continue;
				}
				session.lastDeliveryStatus = captured;
				channel->send(session.delivery.status(world, guid, captured, session.telemetrySequence));
			}
		}

		~Runtime() {
			for (auto &entry : sessions) {
				entry.second.delivery.discard();
			}
			try {
				sendDeliveryStatus(true);
			} catch (...) {
				// Teardown cannot wait or throw into an unloading engine. Missing status
				// remains unqualified by the worker's delivery gate.
			}
		}

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
			autonomous = config.value("autonomous_bot", 0U);
			keepAwake = config.value("keep_awake", false);
			if (autonomous && std::find(roster.begin(), roster.end(), autonomous) == roster.end()) {
				throw std::runtime_error("autonomous bot must belong to the pilot roster");
			}
			world = std::to_string(getpid()) + "-" + std::to_string(std::chrono::steady_clock::now().time_since_epoch().count());
			channel = std::make_unique<Channel>(config.at("socket_directory").get<std::string>());
		}
	};

} // namespace botbrain
