#include <gtest/gtest.h>
#include "game/scheduling/serial_save_queue.hpp"

namespace {
struct Character { int xp = 4200; int skill = 10; int charges = 100; int storage = 0; };
using Queue = SerialSaveQueue<std::shared_ptr<Character>>;
}

TEST(BotSaveQueue, SavesSkillsItemsAndStorageWithoutExperienceChanges) {
	Queue queue;
	auto player = std::make_shared<Character>();
	player->skill = 12; player->charges = 90; player->storage = 7;
	auto requested = queue.request(1, player);
	ASSERT_TRUE(requested.start);
	auto work = queue.take(1);
	ASSERT_TRUE(work);
	EXPECT_EQ(work->value->xp, 4200);
	EXPECT_EQ(work->value->skill, 12);
	EXPECT_EQ(work->value->charges, 90);
	EXPECT_EQ(work->value->storage, 7);
	EXPECT_FALSE(queue.finish(1, work->generation, true));
	EXPECT_TRUE(requested.completed.get());
	EXPECT_FALSE(queue.find(1));
}

TEST(BotSaveQueue, OldSaveCannotClearNewGenerationOrStartASecondWriter) {
	Queue queue;
	auto first = queue.request(1, std::make_shared<Character>());
	auto old = queue.take(1);
	auto newer = std::make_shared<Character>(); newer->skill = 50;
	auto second = queue.request(1, newer);
	EXPECT_FALSE(second.start);
	EXPECT_TRUE(queue.finish(1, old->generation, true));
	EXPECT_EQ(first.completed.wait_for(std::chrono::milliseconds(0)), std::future_status::timeout);
	EXPECT_EQ(queue.find(1).value(), newer);
	auto latest = queue.take(1);
	EXPECT_EQ(latest->value->skill, 50);
	EXPECT_FALSE(queue.finish(1, latest->generation, true));
	EXPECT_TRUE(first.completed.get());
	EXPECT_TRUE(second.completed.get());
}

TEST(BotSaveQueue, FailureRetainsPlayerForReconnectAndGeneralSaveRetry) {
	Queue queue;
	auto player = std::make_shared<Character>();
	std::weak_ptr<Character> weak = player;
	auto first = queue.request(1, player);
	player.reset();
	auto work = queue.take(1);
	EXPECT_FALSE(queue.finish(1, work->generation, false));
	work.reset();
	EXPECT_FALSE(first.completed.get());
	ASSERT_FALSE(weak.expired());
	auto retained = queue.snapshot();
	ASSERT_EQ(retained.size(), 1);
	auto retry = queue.request(1, retained.front());
	EXPECT_TRUE(retry.start);
	auto next = queue.take(1);
	EXPECT_FALSE(queue.finish(1, next->generation, true));
	EXPECT_TRUE(retry.completed.get());
}

TEST(BotSaveQueue, FailedOlderGenerationImmediatelyProcessesNewerRequest) {
	Queue queue;
	queue.request(1, std::make_shared<Character>());
	auto old = queue.take(1);
	auto latest = queue.request(1, std::make_shared<Character>());
	EXPECT_TRUE(queue.finish(1, old->generation, false));
	auto next = queue.take(1);
	EXPECT_FALSE(queue.finish(1, next->generation, true));
	EXPECT_TRUE(latest.completed.get());
}

TEST(BotSaveQueue, SeparateCharactersCanSaveIndependently) {
	Queue queue;
	EXPECT_TRUE(queue.request(1, std::make_shared<Character>()).start);
	EXPECT_TRUE(queue.request(2, std::make_shared<Character>()).start);
	ASSERT_TRUE(queue.take(1)); ASSERT_TRUE(queue.take(2));
	EXPECT_EQ(queue.snapshot().size(), 2);
}
