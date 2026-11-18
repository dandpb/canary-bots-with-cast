#pragma once

#include <atomic>
#include <chrono>
#include <condition_variable>
#include <cstdint>
#include <deque>
#include <filesystem>
#include <memory>
#include <mutex>
#include <span>
#include <thread>
#include <vector>

// A single bounded session per server process. No connection or viewer owns it.
class VisualReplay {
public:
	static std::shared_ptr<VisualReplay> start(uint32_t guid, uint16_t protocol);
	~VisualReplay();

	bool active() const { return m_open.load(std::memory_order_relaxed); }
	void record(std::span<const uint8_t> payload);
	void finish();

private:
	using Clock = std::chrono::steady_clock;
	struct Packet {
		int64_t elapsed;
		std::vector<uint8_t> bytes;
	};

	VisualReplay(std::filesystem::path directory, uint32_t guid, uint16_t protocol);
	void write();
	void closeLocked(const char* reason);

	const std::filesystem::path m_directory;
	const uint32_t m_guid;
	const uint16_t m_protocol;
	const Clock::time_point m_start = Clock::now();
	const std::chrono::system_clock::time_point m_wallStart = std::chrono::system_clock::now();
	std::atomic<bool> m_open = true;
	std::mutex m_mutex;
	std::condition_variable m_ready;
	std::deque<Packet> m_queue;
	size_t m_queuedBytes = 0;
	size_t m_tapeBytes = 0;
	size_t m_packets = 0;
	const char* m_reason = "player_removed";
	std::thread m_writer;
};
