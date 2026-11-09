"""Exercise production planned-portal consumption and cached-hop admission.

Waypoint producer prefixes, the FC consumer, and the hop-cache gate are extracted
unchanged from production. Produced and injected results distinguish a consumed
cursor from an action actually performed at the terminal waypoint. No game,
database, or Docker is required.
Run: python3 tools/bot_brain/test_planned_portal.py
"""

import subprocess
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[2]
tick_source = (root / "src/creatures/players/bot/bot_tick.cpp").read_text()
nav_source = (root / "src/creatures/players/bot/bot_nav.cpp").read_text()
header_source = (root / "src/creatures/players/bot/bot_engine_impl.hpp").read_text()
waypoint_source = (root / "src/creatures/players/bot/bot_waypoint.cpp").read_text()
result_definition = header_source[
    header_source.index("\tstruct WaypointFollowResult {") :
]
result_definition = result_definition[: result_definition.index("\n\t};") + 5]
planner_hop_definition = header_source[header_source.index("\tstruct PlannerHop {") :]
planner_hop_definition = planner_hop_definition[
    : planner_hop_definition.index("\n\t};") + 5
]
consumer_start = tick_source.index("\t\t\t\t\t// Did the transition already happen?")
consumer_end = tick_source.index(
    "\n\t\t\t\t}\n\t\t\t}\n\n\t\t\tif (bot.fcTransIdx", consumer_start
)
consumer = tick_source[consumer_start:consumer_end]
cache_start = nav_source.index("\tauto hopIt = s_plannedHop.find(bot.guid);")
cache_end = nav_source.index("\n\tconst bool sameFloor", cache_start)
cache_gate = nav_source[cache_start:cache_end]
creation_start = nav_source.index("\t\tPlannerHop ph;", cache_end)
creation_end = nav_source.index(".first;", creation_start) + len(".first;")
hop_creation = nav_source[creation_start:creation_end]
arrival_start = waypoint_source.index("\t\tif (arrived) {")
arrival_end = waypoint_source.index(
    "\t\t\t// ---- BOT_NAV_REALISM Phase 10", arrival_start
)
arrival_producer = waypoint_source[arrival_start:arrival_end] + "\n}\n"
skip_start = waypoint_source.index("\t\tif (wpElapsed > config.perWpStuckMs)")
skip_end = waypoint_source.index("\n\t\t// Navigation:", skip_start)
skip_producer = waypoint_source[skip_start:skip_end]
grace_start = waypoint_source.index("\t\t\t\tif (lastTickAtOrNearWp &&")
grace_end = waypoint_source.index("\n\t\t\t}\n\t\t\treturn result;", grace_start)
grace_producer = waypoint_source[grace_start:grace_end]
teleport_start = waypoint_source.index(
    "\t\tif (waypoint.type == WaypointType::TELEPORT)"
)
teleport_end = waypoint_source.index("\t\t\t// The importer emits", teleport_start)
teleport_producer = waypoint_source[teleport_start:teleport_end] + "\n}\n"


def function_source(text: str, signature: str) -> str:
    """Keep the complete production function, including its final closing brace."""
    start = text.index(signature)
    end = text.index("\n}\n", start) + 3
    return text[start:end]


start_floor_change = function_source(tick_source, "void BotEngine::startFloorChange(")
give_up = function_source(tick_source, "bool BotEngine::fcGiveUpOnPlannedTrans(")
reset_floor_change = function_source(tick_source, "void BotEngine::resetFloorChange(")
handoff_start = nav_source.index("\ts_plannedFc[bot.guid] = hop;", cache_end)
handoff_end = nav_source.index("\n}", handoff_start)
handoff = nav_source[handoff_start:handoff_end]

source = r"""
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <memory>
#include <optional>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>
int64_t OTSYS_TIME() { return 1000; }
struct Position {
 uint16_t x=0,y=0; uint8_t z=7;
 bool operator==(const Position&) const = default;
};
uint64_t key(Position p) { return (uint64_t(p.x)<<24)|(uint64_t(p.y)<<8)|p.z; }
enum class FloorChangeState { NONE, SCANNING, WALKING_TO, VERIFYING };
struct Player { std::vector<int> listWalkDir; void stopEventWalk() {} };
struct ZTransition { Position pos; std::string type; int value; };
struct BotState { uint32_t guid=1,pathFailCount=0; Position currentPos{32420,32165,7},fcTargetPos,lastPos;
 uint8_t fcPreZ=7,fcAttempts=0; size_t fcTransIdx=0; int64_t fcStartTime=0;
 bool fcGoDown=false; std::vector<ZTransition> fcTransitions;
 FloorChangeState fcState=FloorChangeState::WALKING_TO;
 std::shared_ptr<Player> player=std::make_shared<Player>();
 auto getPlayer() { return player; }
};
struct Portal { Position pos{32427,32170,7}; bool goesDown=true; };
struct ZPlannedHop { Portal portal; int64_t plannedAt=0; };
@PLANNER_HOP_DEFINITION@
enum class WaypointType { STAND,DOOR,HOLE,LADDER,LEVITATE_UP,LEVITATE_DOWN,NPC_INTERACT,TELEPORT };
struct Waypoint { Position pos; WaypointType type=WaypointType::STAND; };
const char* waypointTypeName(WaypointType) { return "waypoint"; }
struct ZLegPlan { std::vector<Waypoint> wps; size_t idx=0; uint32_t skipCount=0; };
struct WaypointFollowConfig {
 std::string logPrefix; int64_t globalTimeoutMs=0,perWpStuckMs=0;
 int32_t zChangeGraceMs=0; bool trackMovementProgress=false;
};
@RESULT_DEFINITION@
namespace fmt { template<class... T> std::string format(const char*,T&&...) { return {}; } }
std::unordered_map<uint32_t,ZPlannedHop> s_plannedFc;
std::unordered_map<uint32_t,PlannerHop> s_plannedHop;
std::unordered_map<uint32_t,ZLegPlan> s_zLegPlan;
std::unordered_map<uint64_t,int64_t> blacklisted;
uint32_t s_zHopFail=0;
std::unordered_map<uint32_t,uint8_t> s_fcConsecutiveFailures,s_fcPlannedApproachFails,s_fcBlockerRetries;
struct FollowerZHopSession { bool portalResolved=false; };
std::unordered_map<uint32_t,FollowerZHopSession> s_followerZHopSession;
bool zGraphReady_=false;
std::unordered_map<uint32_t,int> s_npcApproachStart;
int64_t zPortalBlacklistStamp(Position p) {
 auto it=blacklisted.find(key(p));return it==blacklisted.end()?0:it->second;
}
bool zPortalBlacklisted(Position p) { return zPortalBlacklistStamp(p)!=0; }
void zBlacklistPortal(Position p,const char*) { blacklisted[key(p)]=200000; }
struct BotEngine {
 WaypointFollowResult injected; size_t nextIndex=0; int followCalls=0,actionCalls=0;
 ZLegPlan& ensureZLegPlan(BotState& bot,const Position&,const Portal&) {
  if(!s_zLegPlan.count(bot.guid))
   s_zLegPlan[bot.guid]={{{{32424,32170,7}},{{32427,32170,7}}},0,0};
  return s_zLegPlan.at(bot.guid);
 }
 WaypointFollowResult followWaypoints(BotState&,const std::vector<Waypoint>&,
  size_t& index,uint32_t&,const WaypointFollowConfig&) {
  ++followCalls; index=nextIndex; return injected;
 }
 bool zPlanNextHop(BotState&,const Position&,ZPlannedHop&) { return false; }
 bool fcGiveUpOnPlannedTrans(BotState&,const ZTransition&,uint8_t,const char*);
 void resetFloorChange(BotState&);
 void startFloorChange(BotState&,bool,const Position&);
 void castLog(BotState&,const std::string&) {}
 void castLogError(BotState&,const std::string&) {}
 bool handleActionWaypoint(BotState&,const Waypoint& waypoint) {
  // Count boundary invocations, not successful transitions. VERIFYING judges the latter.
  ++actionCalls;
  return waypoint.type==WaypointType::LADDER || waypoint.type==WaypointType::DOOR;
 }
 void castLevitateSpell(BotState&,const Waypoint&) {}
 Position safeTeleportLanding(BotState&,Position target,std::nullptr_t,std::nullptr_t,const char*) { return target; }
 void recordTeleport(const std::shared_ptr<Player>&,Position,bool) { ++actionCalls; }
#define BOT_TELEPORT(...) recordTeleport(__VA_ARGS__)
 WaypointFollowResult produceArrival(BotState& bot,ZLegPlan& leg) {
  auto player=bot.getPlayer();auto& waypoints=leg.wps;auto& waypointIdx=leg.idx;
  auto& skipCount=leg.skipCount;auto& waypoint=waypoints.at(waypointIdx);auto& wp=waypoint.pos;
  WaypointFollowConfig config;WaypointFollowResult result;const bool arrived=true;
"""
source += arrival_producer
source += r"""
  return result;
 }
 WaypointFollowResult produceTimeout(BotState& bot,ZLegPlan& leg,WaypointFollowResult result={}) {
  auto& waypoints=leg.wps;auto& waypointIdx=leg.idx;auto& skipCount=leg.skipCount;
  WaypointFollowConfig config;config.perWpStuckMs=15000;const int64_t wpElapsed=15001;
  while(waypointIdx<waypoints.size()) {
   auto& waypoint=waypoints.at(waypointIdx);auto& wp=waypoint.pos;
"""
source += skip_producer
source += r"""
   break;
  }
  result.inProgress=waypointIdx<waypoints.size();return result;
 }
 WaypointFollowResult produceGrace(BotState& bot,ZLegPlan& leg) {
  auto& waypoints=leg.wps;auto& waypointIdx=leg.idx;auto& skipCount=leg.skipCount;
  auto& graceWp=waypoints.at(waypointIdx);auto& gwp=graceWp.pos;
  const bool lastTickAtOrNearWp=true;WaypointFollowConfig config;WaypointFollowResult result;
"""
source += grace_producer
source += r"""
  return result;
 }
 WaypointFollowResult produceTeleport(BotState& bot,ZLegPlan& leg) {
  auto player=bot.getPlayer();auto& waypoints=leg.wps;auto& waypointIdx=leg.idx;
  auto& waypoint=waypoints.at(waypointIdx);auto& wp=waypoint.pos;
  WaypointFollowConfig config;WaypointFollowResult result;
"""
source += teleport_producer
source += r"""
  return result;
 }
 void consume(BotState& bot) {
  auto plannedIt=s_plannedFc.find(bot.guid);
  assert(plannedIt!=s_plannedFc.end());
  const auto& hop=plannedIt->second.portal;
"""
source += consumer
source += r"""
 }
 bool cacheAvailable(BotState& bot,const Position& target) {
"""
source += cache_gate
source += r"""
  return haveHop;
 }
 void createFreshHop(BotState& bot,const Position& target) {
  std::vector<ZPlannedHop> hops(1);auto hopIt=s_plannedHop.end();
"""
source += hop_creation
source += r"""
 }
 bool handoffToFc(BotState& bot,const Position& target,const ZPlannedHop& hop) {
  auto player=bot.getPlayer();
"""
source += handoff
source += r"""
 }
};
"""
source += start_floor_change + give_up + reset_floor_change
source += r"""
void reset() {
 s_plannedFc.clear();s_plannedHop.clear();s_zLegPlan.clear();blacklisted.clear();s_zHopFail=0;
 s_fcConsecutiveFailures.clear();s_fcPlannedApproachFails.clear();s_fcBlockerRetries.clear();
 s_followerZHopSession.clear();
 s_plannedFc[1]={};
 s_zLegPlan[1]={{{{32424,32170,7}},{{32427,32170,7}}},0,0};
}
int main(int argc,char** argv) {
 assert(argc==2); std::string scenario=argv[1]; reset(); BotState bot; BotEngine engine;
 if(scenario=="produced_terminal_action") {
  auto& leg=s_zLegPlan.at(1);leg.idx=1;leg.wps[1].type=WaypointType::LADDER;
  engine.injected=engine.produceArrival(bot,leg);engine.nextIndex=leg.idx;
  assert(engine.actionCalls==1 && engine.injected.lastReachedIndex==1);
  assert(engine.injected.inProgress && engine.injected.advanced && leg.idx==2);
  engine.consume(bot);assert(bot.fcState==FloorChangeState::VERIFYING);
 } else if(scenario=="produced_terminal_timeout") {
  auto& leg=s_zLegPlan.at(1);leg.idx=1;
  engine.injected=engine.produceTimeout(bot,leg);engine.nextIndex=leg.idx;
  assert(!engine.injected.lastReachedIndex && !engine.injected.advanced && leg.idx==2);
  engine.consume(bot);assert(bot.fcState!=FloorChangeState::VERIFYING);
 } else if(scenario=="produced_prior_arrival_timeout") {
  auto& leg=s_zLegPlan.at(1);leg.wps[0].type=WaypointType::DOOR;
  auto prior=engine.produceArrival(bot,leg);
  assert(prior.lastReachedIndex==0 && leg.idx==1);
  engine.injected=engine.produceTimeout(bot,leg,prior);engine.nextIndex=leg.idx;
  assert(engine.injected.lastReachedIndex==0 && engine.injected.advanced && leg.idx==2);
  engine.consume(bot);assert(bot.fcState!=FloorChangeState::VERIFYING);
 } else if(scenario=="produced_grace_arrival") {
  auto& leg=s_zLegPlan.at(1);leg.idx=1;bot.currentPos.z=8;
  leg.wps[1].type=WaypointType::HOLE;
  auto result=engine.produceGrace(bot,leg);
  assert(result.lastReachedIndex==1 && result.advanced && leg.idx==2 && engine.actionCalls==1);
 } else if(scenario=="produced_teleport_action") {
  auto& leg=s_zLegPlan.at(1);leg.idx=1;leg.wps[1].type=WaypointType::TELEPORT;
  auto result=engine.produceTeleport(bot,leg);
  assert(result.lastReachedIndex==1 && leg.idx==2 && engine.actionCalls==1);
 } else if(scenario=="terminal_skip") {
  engine.nextIndex=2;engine.injected.inProgress=false;
  engine.consume(bot);
  assert(bot.fcState!=FloorChangeState::VERIFYING);
 } else if(scenario=="prior_arrival_terminal_skip") {
  engine.nextIndex=2;engine.injected.inProgress=false;engine.injected.advanced=true;
  engine.injected.lastReachedIndex=0;
  engine.consume(bot);
  assert(bot.fcState!=FloorChangeState::VERIFYING);
 } else if(scenario=="terminal_action") {
  engine.nextIndex=2;engine.injected.inProgress=true;engine.injected.advanced=true;
  engine.injected.lastReachedIndex=1;
  engine.consume(bot);
  assert(bot.fcState==FloorChangeState::VERIFYING && s_zLegPlan.count(1)==0);
 } else if(scenario=="floor_changed") {
  bot.currentPos.z=8;engine.nextIndex=0;
  engine.consume(bot);
  assert(bot.fcState==FloorChangeState::VERIFYING && engine.followCalls==0);
 } else if(scenario=="aborted") {
  engine.nextIndex=2;engine.injected.inProgress=false;engine.injected.aborted=true;
  engine.consume(bot);
  assert(bot.fcState!=FloorChangeState::VERIFYING);
 } else if(scenario=="bounded_abort_retries") {
  engine.nextIndex=2;engine.injected.inProgress=false;engine.injected.aborted=true;
  for(uint8_t attempt=1;attempt<=3;attempt++) {
   engine.consume(bot);
   if(attempt<3) {
    assert(bot.fcState==FloorChangeState::WALKING_TO);
    assert(s_plannedFc.count(1) && s_fcPlannedApproachFails.at(1)==attempt);
    assert(blacklisted.empty() && s_fcConsecutiveFailures[1]==0);
   } else {
    assert(bot.fcState==FloorChangeState::NONE && !s_plannedFc.count(1));
    assert(!s_fcPlannedApproachFails.count(1));
    assert(blacklisted.count(key(Portal{}.pos)) && s_fcConsecutiveFailures[1]==1);
    assert(s_zHopFail==1);
   }
  }
 } else if(scenario=="refused_handoff") {
  bot.fcState=FloorChangeState::NONE;s_fcConsecutiveFailures[1]=5;
  assert(!engine.handoffToFc(bot,{32369,32241,7},ZPlannedHop{}));
  assert(bot.fcState==FloorChangeState::NONE && bot.player->listWalkDir.empty());
 } else if(scenario=="accepted_handoff") {
  bot.fcState=FloorChangeState::NONE;
  assert(engine.handoffToFc(bot,{32369,32241,7},ZPlannedHop{}));
  assert(bot.fcState==FloorChangeState::SCANNING);
 } else if(scenario=="blacklisted_cache") {
  s_plannedHop[1]={};const auto target=s_plannedHop.at(1).forTarget;
  blacklisted[key(s_plannedHop.at(1).hop.portal.pos)]=100000;
  assert(!engine.cacheAvailable(bot,target));
  assert(!s_plannedHop.count(1) && !s_zLegPlan.count(1));
 } else if(scenario=="fresh_soft_fallback_cache") {
  const Position target{32369,32241,7};blacklisted[key(Portal{}.pos)]=100000;
  engine.createFreshHop(bot,target);
  assert(s_plannedHop.at(1).blacklistStamp==100000);
  assert(engine.cacheAvailable(bot,target));
  assert(s_plannedHop.count(1) && s_zLegPlan.count(1));
 } else if(scenario=="renewed_blacklist_cache") {
  const Position target{32369,32241,7};blacklisted[key(Portal{}.pos)]=100000;
  engine.createFreshHop(bot,target);blacklisted[key(Portal{}.pos)]=200000;
  assert(!engine.cacheAvailable(bot,target));
  assert(!s_plannedHop.count(1) && !s_zLegPlan.count(1));
 } else if(scenario=="expired_blacklist_cache") {
  const Position target{32369,32241,7};blacklisted[key(Portal{}.pos)]=100000;
  engine.createFreshHop(bot,target);blacklisted.erase(key(Portal{}.pos));
  assert(!engine.cacheAvailable(bot,target));
  assert(!s_plannedHop.count(1) && !s_zLegPlan.count(1));
 } else if(scenario=="valid_cache") {
  s_plannedHop[1]={};const auto target=s_plannedHop.at(1).forTarget;
  assert(engine.cacheAvailable(bot,target));
  assert(s_plannedHop.count(1) && s_zLegPlan.count(1));
 } else if(scenario=="changed_target") {
  s_plannedHop[1]={};auto target=s_plannedHop.at(1).forTarget;target.x++;
  assert(!engine.cacheAvailable(bot,target));
  assert(!s_plannedHop.count(1) && !s_zLegPlan.count(1));
 } else if(scenario=="changed_floor") {
  s_plannedHop[1]={};const auto target=s_plannedHop.at(1).forTarget;bot.currentPos.z=8;
  assert(!engine.cacheAvailable(bot,target));
  assert(!s_plannedHop.count(1) && !s_zLegPlan.count(1));
 } else { assert(false); }
 std::cout<<"PASS: "<<scenario<<"\n";
}
"""

source = source.replace("@RESULT_DEFINITION@", result_definition)
source = source.replace("@PLANNER_HOP_DEFINITION@", planner_hop_definition)

scenarios = (
    "produced_terminal_action",
    "produced_terminal_timeout",
    "produced_prior_arrival_timeout",
    "produced_grace_arrival",
    "produced_teleport_action",
    "terminal_skip",
    "prior_arrival_terminal_skip",
    "terminal_action",
    "floor_changed",
    "aborted",
    "bounded_abort_retries",
    "refused_handoff",
    "accepted_handoff",
    "blacklisted_cache",
    "fresh_soft_fallback_cache",
    "renewed_blacklist_cache",
    "expired_blacklist_cache",
    "valid_cache",
    "changed_target",
    "changed_floor",
)
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory)
    (path / "planned_portal.cpp").write_text(source)
    subprocess.run(
        [
            "g++",
            "-std=c++20",
            "-O0",
            str(path / "planned_portal.cpp"),
            "-o",
            str(path / "planned_portal"),
        ],
        check=True,
    )
    failed = []
    for scenario in scenarios:
        result = subprocess.run(
            [str(path / "planned_portal"), scenario],
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
        raise SystemExit(f"Failed planned-portal cases: {', '.join(failed)}")
