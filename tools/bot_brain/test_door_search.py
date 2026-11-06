"""Exercise the production door-search verdict and bounded-search diagnostics.

The BFS prefix is extracted unchanged through its existing failure return. Only
door reconstruction after success is excluded; this fixture supplies a small map
and house predicate rather than requiring a live game, database, or Docker.
Run: python3 tools/bot_brain/test_door_search.py
"""

import subprocess
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[2]
graph_source = (root / "src/creatures/players/bot/bot_zgraph.cpp").read_text()
header_source = (root / "src/creatures/players/bot/bot_engine_impl.hpp").read_text()
search = graph_source[graph_source.index("bool zFindDoorsOnPathImpl(") :]
search = search[: search.index("\t// Walk back from the target collecting doors")]
search += "\treturn true;\n}\n"
offsets = graph_source[graph_source.index("constexpr int32_t kNbrOffsets[8][2]") :]
offsets = offsets[: offsets.index("\n};") + 3]
tile_key = header_source[header_source.index("static inline uint64_t botTileKey(") :]
tile_key = tile_key[: tile_key.index("\n}") + 2]

source = r"""
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <unordered_map>
#include <unordered_set>
#include <vector>
struct Position {
 uint16_t x=0,y=0; uint8_t z=7;
 Position()=default;
 Position(uint16_t px,uint16_t py,uint8_t pz):x(px),y(py),z(pz) {}
 bool operator==(const Position&) const = default;
};
"""
source += tile_key + "\n" + offsets
source += r"""
struct Grid {
 bool open=true;
 std::unordered_set<uint64_t> cells;
 std::unordered_map<uint64_t,uint32_t> houses;
 void clear(bool isOpen=true) { open=isOpen; cells.clear(); houses.clear(); }
 void add(uint16_t x,uint16_t y) { cells.insert(botTileKey({x,y,7})); }
} grid;
bool zFloodPassableAt(int32_t x,int32_t y,int32_t z) {
 return grid.open || grid.cells.count(botTileKey({uint16_t(x),uint16_t(y),uint8_t(z)}));
}
uint32_t zHouseIdAt(int32_t x,int32_t y,int32_t z) {
 auto it=grid.houses.find(botTileKey({uint16_t(x),uint16_t(y),uint8_t(z)}));
 return it==grid.houses.end()?0:it->second;
}
"""
source += search
source += r"""
struct Observation { bool verdict=false,exhausted=false; uint32_t visited=0,expanded=0; };
Observation inspect(Position from,Position target,int32_t radius,uint32_t budget,
 uint32_t destinationHouse=0,uint32_t originHouse=0) {
 Observation out;
 std::vector<Position> doors{{1,1,7}};
 out.verdict=zFindDoorsOnPathImpl(from,target,radius,budget,destinationHouse,originHouse,
  doors,&out.visited,&out.expanded,&out.exhausted);
 assert(doors.empty());
 const bool withoutDiagnostics=zFindDoorsOnPathImpl(from,target,radius,budget,
  destinationHouse,originHouse,doors);
 assert(withoutDiagnostics==out.verdict);
 // The legacy BFS checks budget at the outer loop, then admits at most eight neighbors.
 assert(out.visited<=budget+7);
 assert(out.expanded<=out.visited);
 return out;
}
int main() {
 const Position start{1000,1000,7};
 // A reachable target remains a successful verdict with and without counters.
 { grid.clear(); auto o=inspect(start,{1004,1000,7},10,10000);
  assert(o.verdict && !o.exhausted && o.visited>0 && o.expanded>0);
  std::cout<<"PASS: reached target; diagnostics preserve true verdict\n";
 }
 // A complete closed island is a negative reachability proof, not budget exhaustion.
 { grid.clear(false);
  for(uint16_t x=999;x<=1001;x++) for(uint16_t y=999;y<=1001;y++) grid.add(x,y);
  auto o=inspect(start,{1010,1000,7},20,10000);
  assert(!o.verdict && !o.exhausted && o.visited==9 && o.expanded==9);
  std::cout<<"PASS: disconnected island exhausts its queue without exhausting budget\n";
 }
 // The unchanged false verdict can also mean the bounded search stopped early.
 { grid.clear(); auto o=inspect(start,{1040,1000,7},60,4);
  assert(!o.verdict && o.exhausted && o.visited>=4 && o.expanded<o.visited);
  std::cout<<"PASS: small budget is reported separately from disconnection (visited="
   <<o.visited<<", expanded="<<o.expanded<<")\n";
 }
 // The observed 138-tile leg can exhaust a 20k-cell BFS even on an entirely open floor.
 { grid.clear(); auto o=inspect(start,{1000,1138,7},200,20000);
  assert(!o.verdict && o.exhausted && o.visited>=20000);
  auto complete=inspect(start,{1000,1138,7},200,170000);
  assert(complete.verdict && !complete.exhausted);
  std::cout<<"PASS: reachable 138-tile leg reports 20k-budget exhaustion (visited="
   <<o.visited<<", expanded="<<o.expanded<<"); larger budget reaches target\n";
 }
 // The existing two-house permission gate remains part of the production BFS.
 { grid.clear(false); for(uint16_t x=1000;x<=1002;x++) grid.add(x,1000);
  grid.houses[botTileKey({1001,1000,7})]=9;
  auto blocked=inspect(start,{1002,1000,7},10,1000);
  assert(!blocked.verdict && !blocked.exhausted);
  assert(inspect(start,{1002,1000,7},10,1000,9,0).verdict);
  assert(inspect(start,{1002,1000,7},10,1000,0,9).verdict);
  std::cout<<"PASS: house crossing remains limited to destination or origin house\n";
 }
}
"""

with tempfile.TemporaryDirectory() as directory:
    path = Path(directory)
    (path / "door_search.cpp").write_text(source)
    subprocess.run(
        [
            "g++",
            "-std=c++20",
            "-O0",
            str(path / "door_search.cpp"),
            "-o",
            str(path / "door_search"),
        ],
        check=True,
    )
    subprocess.run([str(path / "door_search")], check=True)
