"""Exercise production bounded-door-search admission, cache, and wide fallback.

The consumer, cache implementation, and cooldown-limited goToWide are extracted
from production. Only the map search and creature boundaries are supplied by the
fixture. The old helper signature gains an unused optional output in this fixture
so its unchanged body can demonstrate the missing-cause failure at runtime.
Run: python3 tools/bot_brain/test_exhausted_planner.py
"""

import subprocess
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[2]
nav_source = (root / "src/creatures/players/bot/bot_nav.cpp").read_text()
graph_source = (root / "src/creatures/players/bot/bot_zgraph.cpp").read_text()
header_source = (root / "src/creatures/players/bot/bot_engine_impl.hpp").read_text()


def function_source(text: str, signature: str) -> str:
    start = text.index(signature)
    return text[start : text.index("\n}\n", start) + 3]


consumer_start = nav_source.index("\tbool needHops = false;")
consumer_end = nav_source.index("\t// ---- Step 6: portal graph", consumer_start)
consumer = nav_source[consumer_start:consumer_end]
door_helper = function_source(graph_source, "bool BotEngine::plannerLegDoors(")
wide_helper = function_source(nav_source, "bool BotEngine::goToWide(")
budget_helper = function_source(nav_source, "static int64_t plannerWpStuckMs(")
prototype_start = header_source.index("\tbool plannerLegDoors(")
prototype = header_source[
    prototype_start : header_source.index(";", prototype_start) + 1
]
entry_start = header_source.index("\tstruct DoorPathEntry {")
entry = header_source[entry_start : header_source.index("\n\t};", entry_start) + 5]
if "budgetExhausted" not in prototype:
    prototype = prototype[:-2] + ", bool* budgetExhausted = nullptr);"
    signature_end = door_helper.index(") {")
    door_helper = (
        door_helper[:signature_end]
        + ", bool* budgetExhausted"
        + door_helper[signature_end:]
    )

source = r"""
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <memory>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>
static int64_t nowMs=1000;
int64_t OTSYS_TIME() { return nowMs; }
struct Position {
 uint16_t x=0,y=0; uint8_t z=7;
 bool operator==(const Position&) const = default;
};
uint64_t botTileKey(Position p) { return (uint64_t(p.x)<<24)|(uint64_t(p.y)<<8)|p.z; }
struct Player { std::vector<int> listWalkDir;
 void setBotAllowFcPos(Position) {} void clearBotAllowFcPos() {} };
struct BotState { uint32_t guid=1,pendingWalkPauseEventId=0; Position currentPos{32372,32103,7};
 std::shared_ptr<Player> player=std::make_shared<Player>();auto getPlayer() { return player; } };
enum class WaypointType { DOOR,STAND };
struct Waypoint { Position pos; WaypointType type;
 Waypoint(Position p,WaypointType t):pos(p),type(t) {} };
struct PlannerLeg { Position forTarget;uint8_t z=7;std::vector<Waypoint> wps;size_t idx=0;uint32_t skipCount=0; };
struct WaypointFollowConfig { std::string logPrefix; int64_t globalTimeoutMs=0,perWpStuckMs=0;
 int32_t zChangeGraceMs=0;bool trackMovementProgress=false,wideSearchOnFail=false; };
struct WaypointFollowResult { bool inProgress=true; };
using Direction=int;
struct FindPathParams { bool fullPathSearch=false,clearSight=true,allowDiagonal=false,keepDistance=true;
 int32_t maxSearchDist=0,minTargetDist=0,maxTargetDist=0; };
struct FrozenPathingConditionCall { explicit FrozenPathingConditionCall(Position) {} };
struct BotAStarNodes { static constexpr int32_t BOT_MAX_NODES=4096; };
constexpr int32_t PATH_WIDE_DIST=200,PLANNER_LEG_RADIUS=200;
constexpr uint32_t PLANNER_LEG_BUDGET=20000;
constexpr int64_t DOOR_PATH_TTL_MS=60000;
constexpr size_t DOOR_PATH_CACHE_MAX=512;
@DOOR_ENTRY@
std::unordered_map<uint64_t,DoorPathEntry> s_doorPathCache;
uint64_t s_doorPathHits=0,s_doorPathMisses=0;
std::unordered_map<uint32_t,PlannerLeg> s_plannerLeg;
std::unordered_map<uint32_t,int> s_routeProgress;
std::unordered_set<uint32_t> s_plannerForceFresh;
bool bfsReachable=false,bfsExhausted=true,astarSuccess=true,includeDoor=false;
int bfsCalls=0,astarCalls=0,graphCalls=0,chunkCalls=0,walkCalls=0,doorFollowCalls=0;
uint32_t zHouseIdAt(int32_t,int32_t,int32_t) { return 0; }
bool zFindDoorsOnPathImpl(const Position&,const Position&,int32_t radius,uint32_t budget,
 uint32_t,uint32_t,std::vector<Position>& doors,uint32_t* visited=nullptr,
 uint32_t* expanded=nullptr,bool* exhausted=nullptr) {
 ++bfsCalls;assert(radius==200 && budget==20000);doors.clear();
 if(includeDoor) doors.push_back({32380,32130,7});
 if(visited) *visited=bfsExhausted?20002:9;
 if(expanded) *expanded=bfsExhausted?19829:9;
 if(exhausted) *exhausted=bfsExhausted;
 return bfsReachable;
}
bool isWalkOnFcTile(Position) { return false; }
bool botGetPathMatchingCond(const std::shared_ptr<Player>&,Position,std::vector<Direction>& dirs,
 FrozenPathingConditionCall,const FindPathParams& fpp,int32_t maxNodes) {
 ++astarCalls;assert(maxNodes==4096 && fpp.maxSearchDist==200);
 assert(fpp.fullPathSearch && fpp.allowDiagonal && !fpp.keepDistance && !fpp.clearSight);
 assert(fpp.minTargetDist==0 && fpp.maxTargetDist==2);
 dirs=astarSuccess?std::vector<int>{1,1,1}:std::vector<int>{};return astarSuccess;
}
namespace fmt { template<class... T> std::string format(const char*,T&&...) { return {}; } }
"""
source += budget_helper
source += r"""
struct BotEngine {
 @DOOR_PROTOTYPE@
 bool goToWide(BotState&,const Position&,int32_t);
 bool goToClosest(BotState&,const Position&,int32_t) { ++chunkCalls;return false; }
 void botStartAutoWalk(BotState&,const std::shared_ptr<Player>& player,const std::vector<Direction>& dirs) {
  ++walkCalls;player->listWalkDir=dirs;
 }
 void castLog(BotState&,const std::string&) {}
 WaypointFollowResult followWaypoints(BotState&,const std::vector<Waypoint>&,size_t&,uint32_t&,
  const WaypointFollowConfig&) { ++doorFollowCalls;return {}; }
 void logPlannerLegSpent(BotState&,size_t,size_t,const char*) {}
 bool plannerLegRebuildExhausted(BotState&,const Position&) { return false; }
 bool consume(BotState& bot,const Position& target,int32_t maxDist=2) {
  auto player=bot.getPlayer();const bool sameFloor=bot.currentPos.z==target.z,haveHop=false;
  const int32_t cheb=std::max(std::abs(int32_t(bot.currentPos.x)-target.x),
   std::abs(int32_t(bot.currentPos.y)-target.y));const bool nearTarget=cheb<=maxDist+8;
"""
source += consumer
source += r"""
  ++graphCalls;return false; // Only the graph dispatch boundary is outside this fixture.
 }
};
"""
source += door_helper + wide_helper
source += r"""
void reset() {
 s_doorPathCache.clear();s_doorPathHits=0;s_doorPathMisses=0;s_plannerLeg.clear();
 s_routeProgress.clear();s_plannerForceFresh.clear();
 nowMs=1000;bfsReachable=false;bfsExhausted=true;astarSuccess=true;includeDoor=false;
 bfsCalls=0;astarCalls=0;graphCalls=0;chunkCalls=0;walkCalls=0;doorFollowCalls=0;
}
int main(int argc,char** argv) {
 assert(argc==2);std::string scenario=argv[1];reset();BotEngine engine;BotState bot;
 const Position target{32369,32241,7};
 if(scenario=="budget_unknown_rescued") {
  assert(engine.consume(bot,target));
  assert(bfsCalls==1 && astarCalls==1 && graphCalls==0 && walkCalls==1);
 } else if(scenario=="frontier_unreachable") {
  bfsExhausted=false;assert(!engine.consume(bot,target));
  assert(bfsCalls==1 && astarCalls==0 && graphCalls==1);
 } else if(scenario=="cached_budget_cause") {
  astarSuccess=false;assert(!engine.consume(bot,target));
  assert(astarCalls==1 && graphCalls==1);
  nowMs+=15001;bfsExhausted=false;astarSuccess=true;
  assert(engine.consume(bot,target));
  assert(bfsCalls==1 && s_doorPathHits==1 && astarCalls==2 && graphCalls==1);
 } else if(scenario=="cached_frontier_cause") {
  bfsExhausted=false;assert(!engine.consume(bot,target));
  bfsExhausted=true;assert(!engine.consume(bot,target));
  assert(bfsCalls==1 && s_doorPathHits==1 && astarCalls==0 && graphCalls==2);
 } else if(scenario=="failed_wide_cooldown") {
  astarSuccess=false;assert(!engine.consume(bot,target));
  assert(astarCalls==1 && graphCalls==1 && walkCalls==0 && chunkCalls==0);
  assert(!engine.consume(bot,target));assert(astarCalls==1 && graphCalls==2);
  nowMs+=15001;assert(!engine.consume(bot,target));
  assert(astarCalls==2 && graphCalls==3 && bfsCalls==1 && chunkCalls==0);
 } else if(scenario=="successful_wide_clears_cooldown") {
  assert(engine.consume(bot,target));assert(astarCalls==1 && graphCalls==0);
  bot.player->listWalkDir.clear();nowMs++;astarSuccess=false;
  assert(!engine.consume(bot,target));
  assert(astarCalls==2 && graphCalls==1 && bfsCalls==1);
 } else if(scenario=="force_fresh_cause") {
  bfsExhausted=false;assert(!engine.consume(bot,target));
  bfsExhausted=true;s_plannerForceFresh.insert(1);
  assert(engine.consume(bot,target));
  assert(bfsCalls==2 && s_doorPathHits==0 && astarCalls==1 && graphCalls==1);
  assert(!s_plannerForceFresh.count(1));
 } else if(scenario=="legacy_bool_api") {
  std::vector<Position> doors;assert(!engine.plannerLegDoors(bot.currentPos,target,doors));
  assert(bfsCalls==1 && astarCalls==0);
 } else if(scenario=="cache_cause_output") {
  std::vector<Position> doors;bool exhausted=false;
  assert(!engine.plannerLegDoors(bot.currentPos,target,doors,false,&exhausted));
  assert(exhausted);exhausted=false;bfsExhausted=false;
  assert(!engine.plannerLegDoors(bot.currentPos,target,doors,false,&exhausted));
  assert(exhausted && bfsCalls==1 && s_doorPathHits==1);
 } else if(scenario=="floor_mismatch_output") {
  std::vector<Position> doors;bool exhausted=true;auto other=target;other.z=8;
  assert(!engine.plannerLegDoors(bot.currentPos,other,doors,false,&exhausted));
  assert(!exhausted && bfsCalls==0);
 } else if(scenario=="reachable_clear") {
  bfsReachable=true;bfsExhausted=false;assert(engine.consume(bot,target));
  assert(bfsCalls==1 && astarCalls==1 && graphCalls==0);
 } else if(scenario=="reachable_door") {
  bfsReachable=true;bfsExhausted=false;includeDoor=true;assert(engine.consume(bot,target));
  assert(doorFollowCalls==1 && astarCalls==0 && graphCalls==0);
 } else { assert(false); }
 std::cout<<"PASS: "<<scenario<<"\n";
}
"""
source = source.replace("@DOOR_ENTRY@", entry).replace("@DOOR_PROTOTYPE@", prototype)

scenarios = (
    "budget_unknown_rescued",
    "frontier_unreachable",
    "cached_budget_cause",
    "cached_frontier_cause",
    "failed_wide_cooldown",
    "successful_wide_clears_cooldown",
    "force_fresh_cause",
    "legacy_bool_api",
    "cache_cause_output",
    "floor_mismatch_output",
    "reachable_clear",
    "reachable_door",
)
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory)
    (path / "exhausted_planner.cpp").write_text(source)
    subprocess.run(
        [
            "g++",
            "-std=c++20",
            "-O0",
            str(path / "exhausted_planner.cpp"),
            "-o",
            str(path / "exhausted_planner"),
        ],
        check=True,
    )
    failed = []
    for scenario in scenarios:
        result = subprocess.run(
            [str(path / "exhausted_planner"), scenario],
            check=False,
            cwd=path,
            capture_output=True,
            text=True,
        )
        if result.returncode:
            failed.append(scenario)
            print(f"FAIL: {scenario}: {result.stderr.strip()}")
        else:
            print(result.stdout.strip())
    if failed:
        raise SystemExit(f"Failed exhausted-planner cases: {', '.join(failed)}")
