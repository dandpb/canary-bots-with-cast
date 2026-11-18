#include "server/network/protocol/visual_replay.hpp"

#include <charconv>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string_view>

namespace {
constexpr auto duration = std::chrono::minutes(30);
constexpr size_t queueLimit = 2 * 1024 * 1024;
constexpr size_t packetLimit = 4096;
constexpr size_t tapeLimit = 128 * 1024 * 1024;

// Cast serializer opcodes for world/bootstrap, movement, tiles, combat effects,
// container/inventory changes and stats. Speech, channels and text stay out.
bool visualOpcode(uint8_t opcode) {
	switch (opcode) {
		case 0x0A: case 0x0F: case 0x17: case 0x1A: case 0x32: case 0x43:
		case 0x64: case 0x65: case 0x66: case 0x67: case 0x68: case 0x69:
		case 0x6A: case 0x6B: case 0x6C: case 0x6D: case 0x6E: case 0x6F:
		case 0x70: case 0x71: case 0x72: case 0x78: case 0x79:
		case 0x82: case 0x83: case 0x84: case 0x85: case 0x8C: case 0x8D:
		case 0x8E: case 0x8F: case 0x90: case 0x91: case 0x92: case 0x93:
		case 0xA0: case 0xA1: case 0xA2: case 0xA3: case 0xA4: case 0xA5:
		case 0xA6: case 0xA7: case 0xBE: case 0xBF: case 0xEF:
			return true;
		default:
			return false;
	}
}
}

std::shared_ptr<VisualReplay> VisualReplay::start(uint32_t guid, uint16_t protocol) {
	static const auto target = [] {
		uint32_t value = 0;
		if (const auto* raw = std::getenv("CANARY_VISUAL_REPLAY_BOT")) {
			const std::string_view text(raw);
			const auto [end, error] = std::from_chars(text.data(), text.data() + text.size(), value);
			if (error == std::errc() && end == text.data() + text.size()) {
				return value;
			}
		}
		return uint32_t { 0 };
	}();
	if (target == 0 || guid != target) {
		return {};
	}
	const auto* dir = std::getenv("CANARY_VISUAL_REPLAY_DIR");
	if (!dir || !std::filesystem::path(dir).is_absolute()) {
		return {};
	}
	static std::mutex mutex;
	static std::shared_ptr<VisualReplay> session;
	const std::lock_guard lock(mutex);
	if (session) {
		return {};
	}
	session.reset(new VisualReplay(dir, guid, protocol));
	return session;
}

VisualReplay::VisualReplay(std::filesystem::path directory, uint32_t guid, uint16_t protocol) :
	m_directory(std::move(directory)), m_guid(guid), m_protocol(protocol), m_writer([this] {
		try {
			write();
		} catch (const std::exception &error) {
			std::fprintf(stderr, "[VisualReplay] Bot %u writer stopped: %s\n", m_guid, error.what());
			const std::lock_guard lock(m_mutex);
			closeLocked("write_failure");
		}
	}) { }

VisualReplay::~VisualReplay() {
	finish();
	m_writer.join();
}

void VisualReplay::closeLocked(const char* reason) {
	m_reason = reason;
	m_open.store(false, std::memory_order_relaxed);
	m_ready.notify_one();
}

void VisualReplay::finish() {
	const std::lock_guard lock(m_mutex);
	if (active()) {
		closeLocked("player_removed");
	}
}

void VisualReplay::record(std::span<const uint8_t> payload) {
	if (payload.empty() || !visualOpcode(payload.front())) {
		return;
	}
	const std::lock_guard lock(m_mutex);
	if (!active()) {
		return;
	}
	const auto elapsed = Clock::now() - m_start;
	if (elapsed >= duration) {
		closeLocked("time_limit");
		return;
	}
	if (m_queue.size() >= packetLimit || m_queuedBytes + payload.size() > queueLimit) {
		closeLocked("queue_limit");
		return;
	}
	// Reserve an upper bound for the hex payload, timestamp, and delimiters.
	const auto bytes = 2 * payload.size() + 32;
	if (m_tapeBytes + bytes > tapeLimit) {
		closeLocked("storage_limit");
		return;
	}
	const bool first = m_packets == 0;
	if (first && payload.front() != 0x43) {
		closeLocked("invalid_bootstrap");
		return;
	}
	m_queue.push_back({ std::chrono::duration_cast<std::chrono::milliseconds>(elapsed).count(), { payload.begin(), payload.end() } });
	m_tapeBytes += bytes;
	m_queuedBytes += payload.size();
	++m_packets;
	m_ready.notify_one();
}

void VisualReplay::write() {
	std::error_code error;
	if (!std::filesystem::create_directory(m_directory, error)) {
		std::fprintf(stderr, "[VisualReplay] Bot %u requires a new writable output directory\n", m_guid);
		const std::lock_guard lock(m_mutex);
		closeLocked("directory_unavailable");
		return;
	}
	std::ofstream tape(m_directory / "game.cam", std::ios::binary);
	constexpr std::string_view hex = "0123456789abcdef";
	size_t written = 0;
	int64_t last = 0;
	bool bootstrap = false;
	std::unique_lock lock(m_mutex);
	while (tape) {
		m_ready.wait_until(lock, m_start + duration, [&] { return !m_queue.empty() || !active(); });
		if (active() && Clock::now() >= m_start + duration) {
			closeLocked("time_limit");
		}
		if (m_queue.empty()) {
			break;
		}
		auto packet = std::move(m_queue.front());
		m_queue.pop_front();
		m_queuedBytes -= packet.bytes.size();
		lock.unlock();
		std::string row = "< " + std::to_string(packet.elapsed) + " ";
		row.reserve(row.size() + 2 * packet.bytes.size() + 3);
		if (written == 0 && m_protocol >= 1405) {
			row += "00"; // The OTClient parser consumes the first-packet padding byte.
		}
		for (const auto byte : packet.bytes) {
			row.push_back(hex[byte >> 4]);
			row.push_back(hex[byte & 0xF]);
		}
		row += '\n';
		tape << row;
		bootstrap |= packet.bytes.front() == 0x64;
		last = packet.elapsed;
		++written;
		lock.lock();
	}
	lock.unlock();
	tape.close();
	lock.lock();
	if (!tape) {
		closeLocked("write_failure");
		m_queue.clear();
	}
	const auto* reason = m_reason;
	lock.unlock();
	// A missing or unparsable receipt (e.g. process kill) is incomplete evidence.
	std::ofstream receipt(m_directory / "capture.json", std::ios::binary);
	receipt << "{\"schema\":1,\"bot_id\":" << m_guid << ",\"protocol\":" << m_protocol
	        << ",\"wall_start_ms\":" << std::chrono::duration_cast<std::chrono::milliseconds>(m_wallStart.time_since_epoch()).count()
	        << ",\"last_packet_ms\":" << last << ",\"packets\":" << written
	        << ",\"bootstrap_map\":" << (bootstrap ? "true" : "false")
	        << ",\"reason\":\"" << reason << "\"}\n";
	receipt.close();
	if (!receipt) {
		std::fprintf(stderr, "[VisualReplay] Bot %u could not finalize its receipt\n", m_guid);
	}
}
