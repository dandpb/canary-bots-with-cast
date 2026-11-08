"""Exercise the real planned-floor handoff and its refusal after repeated failures."""

import subprocess
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[2]
tick = (root / "src/creatures/players/bot/bot_tick.cpp").read_text()
nav = (root / "src/creatures/players/bot/bot_nav.cpp").read_text()
start = tick[tick.index("void BotEngine::startFloorChange(") :]
start = start[: start.index("\n// Called wherever the FC machine")]
tail = nav[nav.index("\ts_plannedFc[bot.guid] = hop;") :]
tail = tail[: tail.index("\n}\n") + 3]
fallback = nav[
    nav.index(
        "\tif (bot.currentPos.z != target.z && bot.fcState == FloorChangeState::NONE && !isFollowingWaypoints)"
    ) :
]
fallback = fallback[: fallback.index("\n\t}\n") + 3]
source = r"""
#include <cassert>
#include <cstdint>
#include <unordered_map>
#include <vector>
int64_t OTSYS_TIME() { return 1000; }
struct Position { int z=10; };
enum class FloorChangeState { NONE, SCANNING };
struct Portal { Position pos; bool goesDown=false; };
struct ZPlannedHop { Portal portal; };
struct BotState {
  uint32_t guid=1; Position currentPos; FloorChangeState fcState=FloorChangeState::NONE;
  bool fcGoDown=false; Position fcTargetPos; std::vector<int> fcTransitions;
  int fcTransIdx=0, fcPreZ=0, fcAttempts=0; int64_t fcStartTime=0;
};
std::unordered_map<uint32_t, int> s_fcConsecutiveFailures;
std::unordered_map<uint32_t, ZPlannedHop> s_plannedFc, s_plannedHop;
std::unordered_map<uint32_t, int> s_zLegPlan;
class BotEngine {
 public: bool zGraphReady_=false;
 bool zPlanNextHop(BotState&, const Position&, ZPlannedHop&) { return false; }
 void startFloorChange(BotState&, bool, const Position&);
 bool handoff(BotState& bot, const Position& target, const ZPlannedHop& hop) {
"""
source += (
    tail
    + "\n bool fallback(BotState& bot, const Position& target) { bool isFollowingWaypoints=false;\n"
    + fallback
    + "\nreturn false; }\n};\n"
    + start
)
source += r"""
int main() {
  BotEngine engine; BotState bot; Position target{7}; ZPlannedHop hop;
  s_fcConsecutiveFailures[bot.guid]=5;
  assert(!engine.handoff(bot, target, hop));
  assert(bot.fcState == FloorChangeState::NONE);
  assert(s_plannedFc.count(bot.guid)==0);
  assert(!engine.fallback(bot, target));
  s_fcConsecutiveFailures.erase(bot.guid);
  assert(engine.fallback(bot, target));
  assert(bot.fcState == FloorChangeState::SCANNING);
  bot.fcState = FloorChangeState::NONE;
  assert(engine.handoff(bot, target, hop));
  assert(bot.fcState == FloorChangeState::SCANNING);
}
"""
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory)
    (path / "test.cpp").write_text(source)
    subprocess.run(
        ["g++", "-std=c++20", str(path / "test.cpp"), "-o", str(path / "test")],
        check=True,
    )
    subprocess.run([str(path / "test")], check=True)
