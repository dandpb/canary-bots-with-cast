"""Compile the real direct-command boundary and uncached BFS wrapper."""

import subprocess
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[2]
command = (root / "src/creatures/players/bot/bot_command.cpp").read_text()
graph = (root / "src/creatures/players/bot/bot_zgraph.cpp").read_text()
block = command[command.index("\t\tif (directMode) {") :]
block = block[: block.index("\n\t\tstd::vector<botnav::ZRouteHop> hops;")]
wrapper = graph[graph.index("bool BotEngine::tracePlannerDoors(") :]
wrapper = wrapper[: wrapper.index("\n}\n") + 3]
source = r"""
#include <cassert>
#include <cstdint>
#include <iostream>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>
struct Position { uint16_t x=0,y=0; uint8_t z=7; };
struct Player { std::string getName() { return "fixture"; } };
int bfsCalls=0;
uint32_t zHouseIdAt(uint16_t,uint16_t,uint8_t) { return 0; }
bool zFindDoorsOnPathImpl(const Position&,const Position&,int32_t,uint32_t,
 uint32_t,uint32_t,std::vector<Position>& out,uint32_t* visited,
 uint32_t* expanded,bool* exhausted) {
 ++bfsCalls; out.clear(); *visited=123; *expanded=99; *exhausted=true; return false;
}
namespace fmt { template<class... T> std::string format(const char*,T&&...) { return "formatted"; } }
struct Logger { template<class... T> void info(const char*,T&&...) {} };
Logger& g_logger() { static Logger logger; return logger; }
class BotEngine {
public:
 static constexpr int32_t PLANNER_LEG_RADIUS=200;
 static constexpr uint32_t PLANNER_LEG_BUDGET=20000;
 std::unordered_map<int,int> s_doorPathCache{{7,11}};
 uint64_t s_doorPathHits=13,s_doorPathMisses=17;
 std::vector<std::pair<bool,int32_t>> searches;
 bool tracePlannerDoors(const Position&,const Position&,std::vector<Position>&,
  uint32_t&,uint32_t&,bool&);
 bool botTraceLegPath(const std::shared_ptr<Player>&,const Position&,
  const Position& to,int32_t arrival,std::vector<Position>& tiles,bool wide,
  std::string* note) {
  searches.emplace_back(wide,arrival); tiles={to}; *note="fixture"; return true;
 }
 std::string diagnose(Position from,Position to) {
  const bool directMode=true;
  auto mover=std::make_shared<Player>();
"""
source += block
source += '\nreturn "unexpected";\n}\n};\n'
source += wrapper
source += r"""
int main() {
 BotEngine engine;
 const auto before=engine.s_doorPathCache;
 auto same=engine.diagnose({32372,32103,7},{32369,32241,7});
 assert(!same.empty() && bfsCalls==1 && engine.searches.size()==4);
 assert(engine.searches[0]==std::make_pair(false,0));
 assert(engine.searches[1]==std::make_pair(false,2));
 assert(engine.searches[2]==std::make_pair(true,0));
 assert(engine.searches[3]==std::make_pair(true,2));
 assert(engine.s_doorPathCache==before && engine.s_doorPathHits==13 && engine.s_doorPathMisses==17);
 std::cout<<"PASS: direct trace preserves planner cache and compares four existing search profiles\n";
 engine.searches.clear(); bfsCalls=0;
 auto cross=engine.diagnose({32427,32170,7},{32427,32170,8});
 assert(cross=="route direct: source and target must be on the same floor");
 assert(bfsCalls==0 && engine.searches.empty() && engine.s_doorPathCache==before);
 std::cout<<"PASS: cross-floor direct trace stops before BFS or XY-only A*\n";
}
"""
with tempfile.TemporaryDirectory(prefix="canary-direct-trace-") as temporary:
    directory = Path(temporary)
    cpp = directory / "test.cpp"
    binary = directory / "test"
    cpp.write_text(source)
    subprocess.run(
        ["g++", "-std=c++20", "-O1", str(cpp), "-o", str(binary)], check=True
    )
    subprocess.run([str(binary)], check=True)
