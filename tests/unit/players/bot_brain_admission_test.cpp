#include <gtest/gtest.h>
#include "creatures/players/bot/bot_brain_channel.hpp"

using nlohmann::json;

static json request() {
	return { { "version", 1 }, { "type", "telemetry_admit" }, { "world", "world-a" }, { "bot_id", 7 }, { "nonce", "attempt-a" } };
}
static json snapshot() {
	return { { "world", "world-a" }, { "captured_ms", 1000 }, { "bot", { { "id", 7 } } } };
}

TEST(BotBrainAdmission, LostReplyRetryKeepsOriginalCutAndDeaths) {
	botbrain::Session session;
	session.telemetrySequence = 219;
	session.deaths = 2;
	auto first = session.admit(request(), "world-a", 7, "source", false, snapshot);
	EXPECT_EQ(first.at("begin_sequence"), 220);
	EXPECT_EQ(first.at("deaths"), 2);
	EXPECT_EQ(session.delivery.pendingFrames(), 1);
	++session.deaths;
	++session.telemetrySequence; // a later death must not alter the cut
	auto retry = session.admit(request(), "world-a", 7, "source", false, []() -> json { throw std::runtime_error("recaptured"); });
	EXPECT_EQ(first, retry);
	EXPECT_EQ(session.offers.size(), 1U);
	EXPECT_EQ(session.offers.front(), snapshot());
	EXPECT_EQ(session.telemetrySequence, 221);
	EXPECT_EQ(session.delivery.pendingFrames(), 1);
}

TEST(BotBrainAdmission, RejectsWrongIdentityWithoutAllocatingAndPinsSource) {
	for (const auto &field : { "world", "bot_id", "nonce" }) {
		botbrain::Session session;
		auto bad = request();
		bad[field] = field == std::string("bot_id") ? json(9) : json("");
		EXPECT_THROW(session.admit(bad, "world-a", 7, "source", false, snapshot), std::runtime_error);
		EXPECT_EQ(session.telemetrySequence, 0);
	}
	botbrain::Session session;
	auto first = session.admit(request(), "world-a", 7, "source", false, snapshot);
	EXPECT_EQ(first.at("source"), "source");
	auto conflict = request();
	conflict["nonce"] = "another";
	EXPECT_THROW(session.admit(conflict, "world-a", 7, "source", false, snapshot), std::runtime_error);
	EXPECT_EQ(session.telemetrySequence, 1);
}

TEST(BotBrainAdmission, OverflowAndDirtySourceCannotQualify) {
	botbrain::Session session;
	session.delivery = botbrain::TelemetryOutbox(0);
	auto result = session.admit(request(), "world-a", 7, "source", false, snapshot);
	EXPECT_EQ(result.at("fault"), "telemetry_loss");
	EXPECT_EQ(session.telemetrySequence, 1);
	botbrain::Session dirty;
	EXPECT_EQ(dirty.admit(request(), "world-a", 7, "source", true, snapshot).at("fault"), "source_unqualified");
}

TEST(BotBrainAdmission, BoundaryAndDeathUseRealChannelInFifoOrder) {
	// The session scratch path may exceed sockaddr_un. Resolve an open scratch
	// directory through procfs, keeping all created files under TMPDIR.
	const char* root = std::getenv("TMPDIR");
	ASSERT_NE(root, nullptr);
	std::string pattern = std::string(root) + "/native-admission-XXXXXX";
	ASSERT_NE(mkdtemp(pattern.data()), nullptr);
	const int directory = open(pattern.c_str(), O_RDONLY | O_DIRECTORY | O_CLOEXEC);
	ASSERT_GE(directory, 0);
	const auto ipc = "/proc/self/fd/" + std::to_string(directory) + "/ipc";
	{
		botbrain::Channel channel(ipc);
		const int worker = socket(AF_UNIX, SOCK_DGRAM | SOCK_NONBLOCK | SOCK_CLOEXEC, 0);
		ASSERT_GE(worker, 0);
		sockaddr_un address {};
		address.sun_family = AF_UNIX;
		const auto path = ipc + "/worker.sock";
		std::copy(path.begin(), path.end(), address.sun_path);
		ASSERT_EQ(bind(worker, reinterpret_cast<sockaddr*>(&address), sizeof(address)), 0);
		botbrain::Session session;
		session.telemetrySequence = 219;
		session.delivery.enqueue(botbrain::telemetry("world-a", 7, 219, 900, 0, "alive"));
		auto admitted = session.admit(request(), "world-a", 7, "source", false, snapshot);
		// A death after the cut, before the reply is received, uses the same queue.
		session.delivery.publish(channel, botbrain::telemetry("world-a", 7, ++session.telemetrySequence, 1100, ++session.deaths, "dead"));
		session.delivery.beginTick();
		session.delivery.flush(channel);
		for (unsigned sequence = 219; sequence <= 221; ++sequence) {
			std::array<char, 32768> data {};
			const auto size = recv(worker, data.data(), data.size(), 0);
			ASSERT_GT(size, 0);
			const auto event = json::parse(data.data(), data.data() + size);
			EXPECT_EQ(event.at("sequence"), sequence);
			if (sequence == 220) {
				EXPECT_EQ(event.at("run_nonce"), admitted.at("nonce"));
			}
		}
		EXPECT_EQ(session.delivery.acceptedSequence(), 221U);
		EXPECT_EQ(session.delivery.overflowFrames(), 0U);
		close(worker);
		unlink(path.c_str());
	}
	close(directory);
	std::filesystem::remove_all(pattern);
}
