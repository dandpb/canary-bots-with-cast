"""Exercise real intent admission and cross-floor navigation budget boundaries.

Uses the production protocol validator, intent admission, plannerReplan,
startFloorChange and the early cross-floor goTo branch. A C++ compiler and
nlohmann headers are required; no game, database, Docker, or provider is used.
Run: python3 tools/bot_brain/test_navigation_objective.py --include /path/to/include
"""

import argparse
import os
import subprocess
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--include", type=Path, default=os.environ.get("CANARY_TEST_INCLUDE")
)
args = parser.parse_args()
candidates = (
    [args.include]
    if args.include
    else [
        Path("/tmp/canary-test-deps/include"),
        root / "vcpkg_installed/x64-linux/include",
        Path("/usr/include"),
    ]
)
include = next(
    (path for path in candidates if path and (path / "nlohmann/json.hpp").is_file()),
    None,
)
if include is None:
    raise SystemExit(
        "Set --include or CANARY_TEST_INCLUDE to headers containing nlohmann/json.hpp"
    )

brain_source = (root / "src/creatures/players/bot/bot_brain.cpp").read_text()
tick_source = (root / "src/creatures/players/bot/bot_tick.cpp").read_text()
nav_source = (root / "src/creatures/players/bot/bot_nav.cpp").read_text()


def function_source(text: str, signature: str, indentation: str = "") -> str:
    start = text.index(signature)
    return text[
        start : text.index(f"\n{indentation}}}\n", start) + len(indentation) + 3
    ]


intent_start = brain_source.index('\t\t\tif (type != "intent")')
intent_start = brain_source.index(
    '\t\t\tconst auto id = packet.at("action_id")', intent_start
)
intent_end = brain_source.index("\n\t\t} catch (const std::exception &)", intent_start)
admission = brain_source[intent_start:intent_end]
outcome = function_source(brain_source, "\tJson brainOutcome(", "\t")
remember = function_source(brain_source, "\tvoid rememberOutcome(", "\t")
start_floor_change = function_source(tick_source, "void BotEngine::startFloorChange(")
wide_helper = function_source(nav_source, "bool BotEngine::goToWide(")
replan = function_source(nav_source, "void BotEngine::plannerReplan(").replace(
    "void BotEngine::plannerReplan(", "void BotEngine::plannerReplanActual(", 1
)
go_start = nav_source.index("bool BotEngine::goTo(")
go_end = nav_source.index(
    "\t// Allow A* to path onto the destination FC tile", go_start
)
go_to = nav_source[go_start:go_end] + "\treturn false;\n}\n"

source = r"""
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <deque>
#include <iostream>
#include <memory>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>
#include "creatures/players/bot/bot_brain_protocol.hpp"
using Json=nlohmann::json;
static int64_t nowMs=1000;
int64_t OTSYS_TIME() { return nowMs; }
struct Position { uint16_t x=0,y=0;uint8_t z=7;bool operator==(const Position&) const = default; };
bool isAtPosition(Position a,Position b,int32_t range) {
 return a.z==b.z && std::max(std::abs(int32_t(a.x)-b.x),std::abs(int32_t(a.y)-b.y))<=range;
}
struct Creature { bool getMonster() { return false; }int getHealth() { return 1; }uint32_t getID() { return 9; } };
struct Party {};
struct Player {
 bool chaseMode=true;std::vector<int> listWalkDir{1,1};Position position{32372,32103,7};
 Position getPosition() { return position; }uint64_t getExperience() { return 100; }
 std::shared_ptr<Party> getParty() { return nullptr; }
 void setChaseMode(bool value) { chaseMode=value; }void setFollowCreature(std::nullptr_t) {}
 void stopWalk() { listWalkDir.clear(); }void stopEventWalk() {}
 void setAttackedCreature(std::shared_ptr<Creature>) {}
 void setBotAllowFcPos(Position) {}void clearBotAllowFcPos() {}
};
enum class FloorChangeState { NONE,SCANNING };
enum class BotAIState { IDLE,TRAVELING,HUNTING };
struct ZTransition {};
struct BotState {
 uint32_t guid=1,huntScriptId=0,huntTargetId=0;bool hasWalkTarget=false,followingCityRoute=false;
 BotAIState state=BotAIState::IDLE;Position currentPos{32372,32103,7},fcTargetPos;
 FloorChangeState fcState=FloorChangeState::NONE;bool fcGoDown=false;
 std::vector<ZTransition> fcTransitions;size_t fcTransIdx=0;uint8_t fcPreZ=0,fcAttempts=0;
 int64_t fcStartTime=0;std::unordered_set<uint32_t> huntIgnoredMonsters;
 std::shared_ptr<Player> player=std::make_shared<Player>();auto getPlayer() { return player; }
};
struct ZPlannedHop { struct Portal { Position pos;bool goesDown=false; } portal; };
struct CountingCounterMap:std::unordered_map<uint32_t,uint8_t> {
 int erasures=0;
 size_t erase(uint32_t guid) { ++erasures;return std::unordered_map<uint32_t,uint8_t>::erase(guid); }
} s_fcConsecutiveFailures;
std::unordered_map<uint32_t,int> s_plannerLeg,s_zLegPlan,s_plannedHop;
std::unordered_map<uint32_t,ZPlannedHop> s_plannedFc;
std::unordered_map<uint64_t,int64_t> s_zPortalBlacklist;
std::unordered_set<uint32_t> s_plannerForceFresh;
bool zGraphReady_=false;
struct Town { Position getTemplePosition() { return {32369,32241,7}; } };
struct Towns { std::shared_ptr<Town> getTown(uint32_t) { return std::make_shared<Town>(); } };
struct FakeGame {
 struct Map { Towns towns; } map;
 std::shared_ptr<Creature> getCreatureByID(uint32_t) { return nullptr; }
};
FakeGame& g_game() { static FakeGame game;return game; }
namespace botbrain {
 struct Session {
  std::unordered_map<std::string,Json> outcomes;std::deque<Json> offers;
  std::string actionId,action="follow";int64_t started=0,targetUntil=0,lastMove=0;
  uint64_t xp=0;uint32_t potions=0,generation=0,script=0,target=0;
  std::array<uint16_t,3> home{};double danger=0;int supplyStep=0;
 };
 void retainTarget(uint32_t,const std::shared_ptr<Creature>&) {}
}
struct Channel { std::vector<Json> sent;void send(const Json& packet) { sent.push_back(packet); } };
struct Runtime { std::string world="qa",mode="active";uint32_t autonomous=1;
 std::unordered_map<uint32_t,botbrain::Session> sessions;
 std::shared_ptr<Channel> channel=std::make_shared<Channel>(); };
std::unordered_map<uint32_t,bool> brainPreviousChase;
std::unordered_map<uint32_t,int> brainCombat,activeHunts_;
std::unordered_map<std::string,uint32_t> activeSpawnGroups_;
struct HuntScript { uint32_t id;std::string spawnGroup; };
std::vector<HuntScript> huntScripts_{{77,"wasps"}};
constexpr int ApproachingShop=0;
using Direction=int;
struct FindPathParams { bool fullPathSearch=false,clearSight=true,allowDiagonal=false,keepDistance=true;
 int32_t maxSearchDist=0,minTargetDist=0,maxTargetDist=0; };
struct FrozenPathingConditionCall { explicit FrozenPathingConditionCall(Position) {} };
struct BotAStarNodes { static constexpr int32_t BOT_MAX_NODES=4096; };
constexpr int32_t PATH_WIDE_DIST=200;
int astarCalls=0;
bool isWalkOnFcTile(Position) { return false; }
bool botGetPathMatchingCond(const std::shared_ptr<Player>&,Position,std::vector<Direction>&,
 FrozenPathingConditionCall,const FindPathParams& fpp,int32_t maxNodes) {
 ++astarCalls;assert(maxNodes==4096 && fpp.maxSearchDist==200);return false;
}
namespace fmt { template<class... T> std::string format(const char*,T&&...) { return {}; } }
"""
source += outcome + remember
source += r"""
struct BotEngine {
 Runtime runtime;Runtime* brain_=&runtime;BotState bot;Json current;
 bool owned=true;int replans=0;
 bool brainOwns(uint32_t) { return owned; }
 Json observeBrain(BotState&) { return current; }
 uint32_t brainPotions(const std::shared_ptr<Player>&) { return 40; }
 uint32_t findNearestTown(Position) { return 8; }
 void finishBrain(BotState&,const char*,const char*) {}
 bool zPlanNextHop(BotState&,const Position&,ZPlannedHop&) { return false; }
 void startFloorChange(BotState&,bool,const Position&);
 bool goTo(BotState&,const Position&,int32_t);
 bool goToWide(BotState&,const Position&,int32_t);
 void castLog(BotState&,const std::string&) {}
 void botStartAutoWalk(BotState&,const std::shared_ptr<Player>& player,const std::vector<Direction>& dirs) {
  player->listWalkDir=dirs;
 }
 void plannerReplanActual(BotState&,const std::shared_ptr<Player>&);
 void plannerReplan(BotState& b,const std::shared_ptr<Player>& player) { ++replans;plannerReplanActual(b,player); }
 void accept(const std::vector<Json>& packets) {
  const auto guid=bot.guid;auto* bot=&this->bot;auto& session=brain_->sessions[guid];const auto now=nowMs;
  for(const auto& packet:packets) {
"""
source += admission
source += r"""
  }
 }
};
"""
source += start_floor_change + replan + go_to + wide_helper
source += r"""
Json offer(BotEngine& engine) {
 auto& session=engine.brain_->sessions[1];
 Json actions=Json::array();
 for(const auto& pair:std::vector<std::pair<std::string,std::string>>{
  {"hunt:77","hunt"},{"retreat","retreat"},{"resupply","resupply"},{"follow","follow"},
  {"hold","hold"},{"continue","continue"},{"target:9","target"}})
  actions.push_back({{"id",pair.first},{"action",pair.second},{"ttl_ms",5000}});
 engine.current={{"world","qa"},{"lease","qa:1:"+std::to_string(session.generation)},
  {"objective_generation",session.generation},{"sequence",session.offers.size()+1},
  {"captured_ms",nowMs},{"party",nullptr},{"autonomous",true},
  {"bot",{{"id",1},{"alive",true},{"position",{32372,32103,7}}}},{"actions",actions}};
 session.offers.push_back(engine.current);return engine.current;
}
Json intent(const Json& observation,const std::string& candidate,const std::string& id="new") {
 return {{"version",1},{"type","intent"},{"world","qa"},{"bot_id",1},{"action_id",id},
  {"lease",observation.at("lease")},{"objective_generation",observation.at("objective_generation")},
  {"observation_sequence",observation.at("sequence")},{"candidate_id",candidate},{"expires_ms",nowMs+4000}};
}
void reset() {
 nowMs=1000;s_fcConsecutiveFailures.clear();s_fcConsecutiveFailures.erasures=0;
 s_fcConsecutiveFailures[1]=5;s_fcConsecutiveFailures[2]=4;
 s_plannerLeg={{1,1},{2,2}};s_zLegPlan={{1,1},{2,2}};s_plannedHop={{1,1},{2,2}};
 s_zPortalBlacklist={{42,999999}};astarCalls=0;
 s_plannedFc.clear();s_plannerForceFresh.clear();brainPreviousChase.clear();brainCombat.clear();
 activeHunts_.clear();activeSpawnGroups_.clear();
}
int main(int argc,char** argv) {
 assert(argc==2);std::string scenario=argv[1];reset();BotEngine engine;
 auto observation=offer(engine);auto& session=engine.brain_->sessions[1];
 if(scenario=="new_hunt" || scenario=="new_retreat" || scenario=="new_resupply" || scenario=="new_follow") {
  const auto action=scenario.substr(4);const auto candidate=action=="hunt"?"hunt:77":action;
  auto packet=intent(observation,candidate);
  engine.accept({packet});
  assert(engine.brain_->channel->sent.back().at("status")=="accepted");
  assert(s_fcConsecutiveFailures.erasures==1 && !s_fcConsecutiveFailures.count(1));
  assert(engine.replans==1 && s_plannerForceFresh.count(1));
  assert(!s_plannerLeg.count(1) && !s_zLegPlan.count(1) && !s_plannedHop.count(1));
  assert(s_plannerLeg.at(2)==2 && s_zLegPlan.at(2)==2 && s_plannedHop.at(2)==2);
  assert(!s_plannerForceFresh.count(2) && s_fcConsecutiveFailures.at(2)==4);
  assert(s_zPortalBlacklist.size()==1 && s_zPortalBlacklist.at(42)==999999);
  assert(engine.bot.player->listWalkDir.empty());
  // Exhaustion within this objective is retained on ticks and duplicate acknowledgement.
  s_fcConsecutiveFailures[1]=5;engine.accept({});engine.accept({packet});
  assert(s_fcConsecutiveFailures[1]==5 && s_fcConsecutiveFailures.erasures==1 && engine.replans==1);
  assert(!engine.goTo(engine.bot,{32369,32241,8},2));
  assert(s_fcConsecutiveFailures[1]==5 && s_fcConsecutiveFailures.erasures==1);
  // A different accepted ID grants one new per-bot budget.
  auto next=offer(engine);engine.accept({intent(next,candidate,"next")});
  assert(s_fcConsecutiveFailures.erasures==2 && engine.replans==2);
 } else if(scenario=="duplicate") {
  auto packet=intent(observation,"retreat","old");packet["observation_sequence"]=999;
  session.outcomes["old"]={{"status","accepted"}};engine.accept({packet});
  assert(engine.brain_->channel->sent.back().at("status")=="accepted");
  assert(s_fcConsecutiveFailures[1]==5 && s_fcConsecutiveFailures.erasures==0 && engine.replans==0);
 } else if(scenario=="continue" || scenario=="hold" || scenario=="target") {
  engine.accept({intent(observation,scenario=="target"?"target:9":scenario)});
  assert(engine.brain_->channel->sent.back().at("status")!=("rejected"));
  assert(s_fcConsecutiveFailures[1]==5 && s_fcConsecutiveFailures.erasures==0 && engine.replans==0);
 } else if(scenario=="invalid" || scenario=="stale" || scenario=="invalid_observation" || scenario=="unowned") {
  auto packet=intent(observation,"retreat");
  if(scenario=="invalid") packet["unexpected"]=true;
  if(scenario=="stale") packet["expires_ms"]=nowMs-1;
  if(scenario=="invalid_observation") packet["observation_sequence"]=999;
  if(scenario=="unowned") engine.owned=false;
  engine.accept({packet});
  assert(engine.brain_->channel->sent.back().at("status")=="rejected");
  assert(s_fcConsecutiveFailures[1]==5 && s_fcConsecutiveFailures.erasures==0 && engine.replans==0);
 } else if(scenario=="generic_refused") {
  assert(!engine.goTo(engine.bot,{32369,32241,8},2));
  assert(engine.bot.fcState==FloorChangeState::NONE && s_fcConsecutiveFailures[1]==5);
 } else if(scenario=="generic_started") {
  s_fcConsecutiveFailures[1]=0;
  assert(engine.goTo(engine.bot,{32369,32241,8},2));
  assert(engine.bot.fcState==FloorChangeState::SCANNING && s_fcConsecutiveFailures.erasures==0);
 } else if(scenario=="new_objective_preserves_wide_cooldown") {
  const Position target{32369,32241,7};
  assert(!engine.goToWide(engine.bot,target,2) && astarCalls==1);
  engine.accept({intent(observation,"retreat")});
  assert(engine.replans==1 && s_fcConsecutiveFailures.erasures==1);
  assert(!engine.goToWide(engine.bot,target,2) && astarCalls==1);
  nowMs+=15001;assert(!engine.goToWide(engine.bot,target,2) && astarCalls==2);
 } else { assert(false); }
 std::cout<<"PASS: "<<scenario<<"\n";
}
"""

scenarios = (
    "new_hunt",
    "new_retreat",
    "new_resupply",
    "new_follow",
    "duplicate",
    "continue",
    "hold",
    "target",
    "invalid",
    "stale",
    "invalid_observation",
    "unowned",
    "generic_refused",
    "generic_started",
    "new_objective_preserves_wide_cooldown",
)
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory)
    (path / "navigation_objective.cpp").write_text(source)
    subprocess.run(
        [
            "g++",
            "-std=c++20",
            "-O0",
            "-I",
            str(include),
            "-I",
            str(root / "src"),
            str(path / "navigation_objective.cpp"),
            "-o",
            str(path / "navigation_objective"),
        ],
        check=True,
    )
    failed = []
    for scenario in scenarios:
        result = subprocess.run(
            [str(path / "navigation_objective"), scenario],
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
        raise SystemExit(f"Failed navigation-objective cases: {', '.join(failed)}")
