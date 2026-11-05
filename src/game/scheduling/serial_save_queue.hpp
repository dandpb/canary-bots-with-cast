#pragma once

#include <cstdint>
#include <future>
#include <mutex>
#include <optional>
#include <unordered_map>
#include <vector>

// Executable-owned per-character save serialization. Failed values stay retained;
// an older completion cannot release or acknowledge a newer requested generation.
template <typename Value>
class SerialSaveQueue {
public:
	struct Request { bool start; std::shared_future<bool> completed; };
	struct Work { Value value; uint64_t generation; };

	Request request(uint32_t guid, Value value) {
		std::lock_guard lock(mutex_);
		auto& entry = entries_[guid];
		entry.value = std::move(value);
		++entry.generation;
		const bool start = !entry.running;
		if (start) {
			entry.running = true;
			entry.promise = std::make_shared<std::promise<bool>>();
			entry.completed = entry.promise->get_future().share();
		}
		return {start, entry.completed};
	}

	std::optional<Work> take(uint32_t guid) const {
		std::lock_guard lock(mutex_);
		const auto found = entries_.find(guid);
		if (found == entries_.end() || !found->second.running) return std::nullopt;
		return Work {found->second.value, found->second.generation};
	}

	// true means the same worker must save the newer desired value next.
	bool finish(uint32_t guid, uint64_t generation, bool success) {
		std::lock_guard lock(mutex_);
		auto found = entries_.find(guid);
		if (found == entries_.end()) return false;
		auto& entry = found->second;
		if (generation != entry.generation) return true;
		entry.promise->set_value(success);
		if (success) entries_.erase(found);
		else entry.running = false;
		return false;
	}

	std::optional<Value> find(uint32_t guid) const {
		std::lock_guard lock(mutex_);
		const auto found = entries_.find(guid);
		if (found == entries_.end()) return std::nullopt;
		return found->second.value;
	}

	std::vector<Value> snapshot() const {
		std::lock_guard lock(mutex_);
		std::vector<Value> result;
		for (const auto& [_, entry] : entries_) result.push_back(entry.value);
		return result;
	}

private:
	struct Entry {
		Value value {};
		uint64_t generation = 0;
		bool running = false;
		std::shared_ptr<std::promise<bool>> promise;
		std::shared_future<bool> completed;
	};
	mutable std::mutex mutex_;
	std::unordered_map<uint32_t, Entry> entries_;
};
