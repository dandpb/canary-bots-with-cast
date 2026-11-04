"""Replay the real brain movement entry point with a blocked creature walk queue.

This compiles the production follow/retreat branch and production stall detector,
with a fake clock and engine boundaries. No game, map, database or provider needed.
Run: python3 tools/bot_brain/test_movement.py
"""
from pathlib import Path
import re
import subprocess
import tempfile

root = Path(__file__).resolve().parents[2]
brain = (root / "src/creatures/players/bot/bot_brain.cpp").read_text()
nav = (root / "src/creatures/players/bot/bot_nav.cpp").read_text()
header = (root / "src/creatures/players/bot/bot_engine_impl.hpp").read_text()
movement = brain[brain.index("bool BotEngine::brainPartyMove("):]
movement = movement[:movement.index('\n\tif (session.action == "resupply")')] + "\nreturn false;\n}\n"
detector = nav[nav.index("bool BotEngine::plannerWalkBlocked("):]
detector = detector[:detector.index('// Throw away every cached routing decision')]
threshold = re.search(r"PLANNER_STUCK_MS\s*=\s*(\d+)", header)[1]
source = r'''
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <deque>
#include <iostream>
#include <memory>
#include <string>
#include <unordered_map>
static int64_t nowMs=1000;
int64_t botMonoMs(){ return nowMs; }
int64_t OTSYS_TIME(){ return nowMs; }
struct Position {
 int x=0,y=0,z=7;
 bool operator==(const Position&) const = default;
 static int getDiagonalDistance(Position a,Position b){return std::max(std::abs(a.x-b.x),std::abs(a.y-b.y));}
};
struct Player;
struct Party {std::shared_ptr<Player> getLeader(){return nullptr;}};
struct Player {
 std::deque<int> listWalkDir;
 void setChaseMode(bool){} void setFollowCreature(std::nullptr_t){} void stopEventWalk(){}
 std::shared_ptr<Party> getParty(){return nullptr;}
};
struct BotState {uint32_t guid=1,pendingWalkPauseEventId=0;Position currentPos;
 std::shared_ptr<Player> player=std::make_shared<Player>();
 auto getPlayer(){return player;}
};
struct Session {std::string action="retreat",actionId="goal";int64_t started=0,lastMove=0;};
struct Runtime {uint32_t autonomous=1;std::unordered_map<uint32_t,Session> sessions{{1,Session{}}};};
struct PlannerStuck {Position lastPos;size_t lastQueue=0;int64_t sinceMs=0;};
static std::unordered_map<uint32_t,PlannerStuck> s_plannerStuck;
class BotEngine {
public:
 Runtime runtime;Runtime* brain_=&runtime;int plans=0,replans=0,completed=0;
 bool brainOwns(uint32_t){return true;} bool brainSafetyPause(BotState&){return false;}
 void finishBrain(BotState&,const char*,const char*){completed++;runtime.sessions[1].actionId.clear();}
 bool planScopedWalk(BotState&,const Position&,int){plans++;return true;}
 bool goToWithDoors(BotState&,const Position&,int){plans++;return true;}
 bool tryFollowLeaderTrail(BotState&,std::shared_ptr<Player>){return false;}
 void castLog(BotState&,const std::string&){}
 bool plannerWalkBlocked(BotState&,const std::shared_ptr<Player>&);
 void plannerReplan(BotState&,const std::shared_ptr<Player>& p){replans++;p->listWalkDir.clear();}
 bool brainPartyMove(BotState&,const Position&);
};
'''
source += f"constexpr int64_t PLANNER_STUCK_MS={threshold};\n" + detector + movement
source += r'''
int main(){
 Position home{30,30,6};
 {BotEngine e;BotState b;b.player->listWalkDir={1,1};s_plannerStuck.clear();nowMs=1000;
  e.brainPartyMove(b,home);assert(e.plans==0);nowMs+=PLANNER_STUCK_MS+1;
  e.brainPartyMove(b,home);assert(e.replans==1 && e.plans==1);}
 {BotEngine e;BotState b;b.player->listWalkDir={1,1};s_plannerStuck.clear();nowMs=1000;
  e.brainPartyMove(b,home);nowMs+=PLANNER_STUCK_MS+1;b.currentPos.x++;
  e.brainPartyMove(b,home);assert(e.replans==0 && e.plans==0);}
 {BotEngine e;BotState b;b.pendingWalkPauseEventId=99;nowMs=10000;
  e.brainPartyMove(b,home);assert(e.plans==0 && e.replans==0);}
 {BotEngine e;BotState b;b.currentPos=home;nowMs=10000;
  e.brainPartyMove(b,home);assert(e.completed==1 && e.plans==0);}
 std::cout<<"PASS: blocked walk recovers, progressing walk and pending pause wait, arrival stops movement\n";
}
'''
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory)
    (path / "movement.cpp").write_text(source)
    subprocess.run(["g++", "-std=c++20", "-O0", str(path / "movement.cpp"), "-o", str(path / "movement")], check=True)
    subprocess.run([str(path / "movement")], check=True)
