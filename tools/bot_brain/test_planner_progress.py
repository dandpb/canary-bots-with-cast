"""Exercise production waypoint timeout gates with a fake clock and moving bot.

The global and waypoint gates are extracted unchanged from bot_waypoint.cpp.
No game, database, Docker, map assets, or provider calls are required.
Run: python3 tools/bot_brain/test_planner_progress.py
"""

import re
import subprocess
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[2]
waypoint_source = (root / "src/creatures/players/bot/bot_waypoint.cpp").read_text()
nav_source = (root / "src/creatures/players/bot/bot_nav.cpp").read_text()
header_source = (root / "src/creatures/players/bot/bot_engine_impl.hpp").read_text()
timer_definition = header_source[header_source.index("\tstruct RouteWaypointTimer {") :]
timer_definition = timer_definition[: timer_definition.index("\n\t};") + 5]
global_gate = waypoint_source[
    waypoint_source.index("\t// Global stuck timeout:") : waypoint_source.index(
        "\t// Z-change grace:"
    )
]
waypoint_gate = waypoint_source[
    waypoint_source.index(
        "\t\t// If still walking toward this waypoint, wait"
    ) : waypoint_source.index("\t\t// Navigation: determine maxDist")
]
budget_helper = nav_source[nav_source.index("static int64_t plannerWpStuckMs(") :]
budget_helper = budget_helper[: budget_helper.index("\n}\n") + 3]
planner_configs = re.findall(
    r"cfg\.globalTimeoutMs\s*=.*?cfg\.zChangeGraceMs\s*=.*?;",
    nav_source,
    re.DOTALL,
)
assert len(planner_configs) == 3, "Expected the three scoped planner call sites"

source = r"""
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <deque>
#include <iostream>
#include <memory>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>
static int64_t nowMs = 1000;
int64_t OTSYS_TIME() { return nowMs; }
struct Position {
 uint16_t x=0,y=0; uint8_t z=7;
 bool operator==(const Position&) const = default;
 static int32_t getDiagonalDistance(const Position& a,const Position& b) {
  return std::max(std::abs(int32_t(a.x)-b.x),std::abs(int32_t(a.y)-b.y));
 }
};
struct Player { std::deque<int> listWalkDir; };
struct BotState {
 uint32_t guid=1,huntScriptId=0,townId=8,pathFailCount=0; Position currentPos;
 std::shared_ptr<Player> player=std::make_shared<Player>();
 auto getPlayer() { return player; }
};
struct Waypoint { Position pos; int type=0; };
const char* waypointTypeName(int) { return "stand"; }
struct WaypointFollowConfig {
 int64_t globalTimeoutMs=60000,perWpStuckMs=15000;
 int32_t zChangeGraceMs=500; bool wideSearchOnFail=false;
 bool trackMovementProgress=false; std::string logPrefix="ZLEG";
};
@ROUTE_WAYPOINT_TIMER@
struct FakeTile { bool hasFlag(int) { return false; } };
struct FakeMap { std::shared_ptr<FakeTile> getTile(Position) { return nullptr; } };
struct FakeGame { FakeMap map; };
FakeGame& g_game() { static FakeGame game; return game; }
constexpr int TILESTATE_PROTECTIONZONE=1;
namespace fmt { template<class... T> std::string format(const char*,T&&...) { return {}; } }
std::unordered_map<uint32_t,std::pair<size_t,int64_t>> s_routeProgress;
std::unordered_map<uint32_t,RouteWaypointTimer> s_routeWpTimer;
std::vector<int> huntScripts_;
std::string getHuntScriptName(BotState&,const std::vector<int>&) { return {}; }
bool isBotPzLocked(BotState&) { return false; }
struct WaypointFollowResult { bool inProgress=true,advanced=false,aborted=false; };
struct BotEngine {
 void castLog(BotState&,const std::string&) {}
 void castLogError(BotState&,const std::string&) {}
 template<class... T> void trackNavEvent(T&&...) {}
 WaypointFollowResult gates(BotState& bot,const std::vector<Waypoint>& waypoints,
  size_t& waypointIdx,uint32_t& skipCount,const WaypointFollowConfig& config) {
  WaypointFollowResult result;
"""
source += global_gate
source += r"""
  auto player=bot.getPlayer();
  while(waypointIdx<waypoints.size()) {
   const auto& waypoint=waypoints[waypointIdx];
   const auto& wp=waypoint.pos;
"""
source += waypoint_gate
source += r"""
   break; // Navigation is outside this timeout-only fixture.
  }
  result.inProgress=waypointIdx<waypoints.size();
  return result;
 }
};
"""
source += budget_helper
source = source.replace("@ROUTE_WAYPOINT_TIMER@", timer_definition)
source += r"""
struct Hop { struct Portal { Position pos; } portal; };
"""
for context, statements in enumerate(planner_configs):
    source += (
        f"WaypointFollowConfig plannerConfig{context}(BotState& bot,const Position& target) {{\n"
        " Hop hop{{target}}; WaypointFollowConfig cfg;\n"
        + statements
        + "\n return cfg;\n}\n"
    )
source += r"""
WaypointFollowConfig plannerConfig(int context,BotState& bot,const Position& target) {
 switch(context) {
  case 0: return plannerConfig0(bot,target);
  case 1: return plannerConfig1(bot,target);
  default: return plannerConfig2(bot,target);
 }
}
"""
source += r"""
struct Fixture {
 BotEngine engine; BotState bot; std::vector<Waypoint> waypoints{{{32427,32170,7}}};
 size_t index=0; uint32_t skips=0; WaypointFollowConfig config; int context;
 Fixture(int plannerContext=2):context(plannerContext) {
  nowMs=1000; s_routeProgress.clear(); s_routeWpTimer.clear();
  bot.currentPos={32372,32103,7};
  config=plannerConfig(context,bot,waypoints[0].pos);
 }
 WaypointFollowResult tick(int64_t at,Position position,bool queued=false) {
  nowMs=at; bot.currentPos=position;
  bot.player->listWalkDir=queued?std::deque<int>{1,1}:std::deque<int>{};
  config.perWpStuckMs=plannerConfig(context,bot,waypoints[0].pos).perWpStuckMs;
  return engine.gates(bot,waypoints,index,skips,config);
 }
};
int main() {
 // Recorded moving retreat: 41.8 s initially contracts to 27.8 s after 28 s.
 for(int context=0;context<3;context++) { Fixture f(context);
  assert(f.config.trackMovementProgress);
  assert(f.tick(1000,{32372,32103,7}).inProgress);
  assert(f.config.perWpStuckMs==41800);
  auto r=f.tick(29001,{32395,32138,7});
  assert(f.config.perWpStuckMs==27800);
  assert(r.inProgress && !r.aborted && f.index==0);
  std::cout<<"PASS: planner caller "<<context<<" enables progress without skipping a moving retreat\n";
 }
 // Progress must be observed even while the creature's walk queue is nonempty.
 { Fixture f;
  assert(f.tick(1000,{32372,32103,7},true).inProgress);
  assert(f.tick(29001,{32395,32138,7},true).inProgress);
  assert(f.tick(30001,{32395,32138,7}).inProgress);
  assert(s_routeWpTimer.at(1).second==29001);
  std::cout<<"PASS: queued movement advances the progress clock\n";
 }
 // A stationary bot still exhausts its local waypoint timeout.
 { Fixture f;
  assert(f.tick(1000,{32395,32138,7}).inProgress);
  auto r=f.tick(28801,{32395,32138,7});
  assert(!r.inProgress && !r.aborted && f.index==1);
  std::cout<<"PASS: stationary waypoint times out\n";
 }
 // Returning to a previously reached distance cannot keep renewing the clock.
 { Fixture f;
  assert(f.tick(1000,{32372,32103,7}).inProgress);
  assert(f.tick(10000,{32395,32138,7}).inProgress);
  assert(f.tick(20000,{32394,32137,7}).inProgress);
  assert(f.tick(30000,{32395,32138,7}).inProgress);
  auto r=f.tick(37801,{32395,32138,7});
  assert(!r.inProgress && f.index==1);
  std::cout<<"PASS: two-tile oscillation does not renew the progress clock\n";
 }
 // A new target at the same index owns a new per-waypoint progress clock.
 { Fixture f;
  assert(f.tick(1000,{32395,32138,7}).inProgress);
  f.waypoints[0].pos={32450,32138,7};
  assert(f.tick(40000,{32395,32138,7}).inProgress);
  assert(s_routeWpTimer.at(1).second==40000);
  assert(s_routeWpTimer.at(1).target==f.waypoints[0].pos);
  std::cout<<"PASS: retargeting the same index starts a new waypoint clock\n";
 }
 // Authored route callers retain the existing non-progress-tracking behavior.
 { Fixture f; f.config.trackMovementProgress=false;
  assert(f.tick(1000,{32372,32103,7}).inProgress);
  auto r=f.tick(29001,{32395,32138,7});
  assert(!r.inProgress && f.index==1);
  std::cout<<"PASS: default configuration preserves elapsed-only behavior\n";
 }
 // Position progress must never renew the separate hard global timeout.
 { Fixture f;
  assert(f.tick(1000,{32372,32103,7}).inProgress);
  assert(f.tick(29001,{32395,32138,7}).inProgress);
  assert(f.tick(50000,{32400,32145,7}).inProgress);
  auto r=f.tick(61001,{32410,32155,7},true);
  assert(!r.inProgress && r.aborted && f.index==1);
  std::cout<<"PASS: global 60-second timeout remains independent of movement\n";
 }
}
"""

with tempfile.TemporaryDirectory() as directory:
    path = Path(directory)
    (path / "planner_progress.cpp").write_text(source)
    subprocess.run(
        [
            "g++",
            "-std=c++20",
            "-O0",
            str(path / "planner_progress.cpp"),
            "-o",
            str(path / "planner_progress"),
        ],
        check=True,
    )
    subprocess.run([str(path / "planner_progress")], check=True)
