#!/usr/bin/env python3
"""Offline source-body regression; no SQL, Docker, service, or full repository build.

Run normally for the working tree, or --source-ref <commit> to test a baseline.
Only Player/callback infrastructure is stubbed; storage method bodies, header and
SerialSaveQueue are compiled from the selected source. The queue interleaving is
deterministic and models dispatcher acknowledgements between serialized commits.
"""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--source-ref")
args = parser.parse_args()

def source(path):
    if args.source_ref:
        return subprocess.check_output(["git", "show", f"{args.source_ref}:{path}"], cwd=ROOT, text=True)
    return (ROOT / path).read_text()

body = source("src/creatures/players/components/player_storage.cpp")
header = source("src/creatures/players/components/player_storage.hpp")

def method(anchor):
    start = body.index(anchor)
    brace = body.index("{", start)
    depth, end = 1, brace + 1
    while depth:
        depth += (body[end] == "{") - (body[end] == "}")
        end += 1
    return body[start:end]

PRELUDE = r"""#include <array>
#include <utility>
#include <ranges>
#include <iostream>
#include <cassert>
#define private public
#include "player_storage.hpp"
#undef private
#include "serial_save_queue.hpp"
struct Look {int lookType,addons;};
struct Player {std::vector<Look> outfits,familiars; const char* getName(){return "stub";} Player& getPlayer(){return *this;}};
constexpr unsigned PSTRG_RESERVED_RANGE_START=100000,PSTRG_RESERVED_RANGE_SIZE=1000,PSTRG_OUTFITS_RANGE_START=100010,PSTRG_OUTFITS_RANGE_SIZE=10,PSTRG_FAMILIARS_RANGE_START=100030,PSTRG_FAMILIARS_RANGE_SIZE=10;
bool isStorageKeyInRange(unsigned k,unsigned s,unsigned n){return k>=s&&k<s+n;}
bool isInPassThrough(unsigned){return false;}
struct Service {template<class... T> void warn(T...){ } int getDispatcherCycle(){return 0;} template<class... T> void eventOnStorageUpdate(T&&...){ } template<class... T> void executeCallback(T&&...){ }};
Service service; Service& g_logger(){return service;} Service& g_dispatcher(){return service;} Service& g_events(){return service;} Service& g_callbacks(){return service;}
enum class EventCallback_t {playerOnStorageUpdate};
"""
MAIN = r"""
using Delta = PlayerStorage::PlayerStorageDelta;
void require(bool ok, const char* message) { if (!ok) { std::cerr << message << '\n'; std::exit(1); } }
int main(){
 Player p; PlayerStorage storage(p); SerialSaveQueue<Delta> queue;
 storage.add(42,1,true); auto a=queue.request(7,storage.delta()); require(a.start,"start A"); auto A=queue.take(7).value();
 storage.add(42,2,true); auto b=queue.request(7,storage.delta()); require(!b.start,"coalesced B");
 storage.add(42,1,true);
 int durable=A.value.upserts.at(42);
 storage.acknowledge(A.value);
 require(queue.finish(7,A.generation,true),"newer B must run");
 auto B=queue.take(7).value(); durable=B.value.upserts.at(42);
 storage.acknowledge(B.value); require(!queue.finish(7,B.generation,true),"B completes");
 auto next=storage.delta();
 std::cout<<"memory="<<storage.get(42)<<" durable="<<durable<<" next_upserts="<<next.upserts.size()<<'\n';
 require(next.upserts.contains(42) && next.upserts.at(42)==1,"FAIL upsert ABA lost pending value 1");
 storage.acknowledge(next); require(storage.delta().upserts.empty(),"normal upsert ack clears");
 storage.remove(42); auto deletion=storage.delta();
 storage.add(42,2,true); auto insertion=storage.delta(); storage.remove(42);
 storage.acknowledge(deletion); storage.acknowledge(insertion);
 require(storage.delta().deletions.size()==1,"delete/reinsert/delete ABA lost deletion");
 storage.acknowledge(storage.delta()); require(storage.delta().deletions.empty(),"normal deletion ack clears");
 storage.add(42,1,true); auto stale=storage.delta();
 storage.clearDirty(); storage.add(42,1,true); storage.acknowledge(stale);
 require(storage.delta().upserts.contains(42),"clearDirty recycled revision");
 storage.ingest({}); storage.add(42,1,true); storage.acknowledge(stale);
 require(storage.delta().upserts.contains(42),"ingest recycled revision");
 storage.acknowledge(Delta{}); require(storage.delta().upserts.contains(42),"empty ack clears dirty");
 auto missing=storage.delta();
 // Compile baseline too, where revisions did not yet exist.
#ifdef HAS_REVISIONS
 missing.revisions.clear();
 storage.acknowledge(missing); require(storage.delta().upserts.contains(42),"missing revision must fail closed");
 storage.acknowledge(storage.delta());
 storage.remove(42); missing=storage.delta(); missing.revisions.clear(); storage.acknowledge(missing);
 require(storage.delta().deletions.size()==1,"missing deletion revision must fail closed");
 storage.acknowledge(storage.delta());
 // Reserved ranges use upsertKey: same value should preserve revision, new value changes it.
 storage.upsertKey(43,1); auto reserved=storage.delta(); storage.upsertKey(43,1);
 require(storage.delta().revisions.at(43)==reserved.revisions.at(43),"unchanged reserved key changed revision");
 storage.upsertKey(43,2); storage.upsertKey(43,1); storage.acknowledge(reserved);
 require(storage.delta().upserts.contains(43),"reserved key ABA lost update");
#endif
 // Regeneration of a materialized reserved key must replace its tombstone.
 p.outfits.push_back({50,3}); storage.prepareForPersist();
 constexpr auto reservedKey=PSTRG_OUTFITS_RANGE_START+1;
 storage.acknowledge(storage.delta());
 require(storage.remove(reservedKey),"materialized reserved key must exist");
 auto staleDeletion=storage.delta();
 storage.prepareForPersist();
 auto regenerated=storage.delta();
 require(regenerated.upserts.contains(reservedKey),"regenerated key missing upsert");
 require(regenerated.deletions.empty(),"FAIL regenerated reserved key retains tombstone");
 storage.acknowledge(staleDeletion);
 require(storage.delta().upserts.contains(reservedKey),"stale deletion ack cleared new revision");
 storage.acknowledge(regenerated);
 require(storage.delta().upserts.empty() && storage.delta().deletions.empty(),"ack regeneration leaves next deletion");
 std::cout<<"PASS real PlayerStorage bodies: ABA upsert/deletion, normal/empty/missing ack, lifecycle reset, reserved keys, SerialSaveQueue\n";
}
"""
methods = ["PlayerStorage::PlayerStorage(", "void PlayerStorage::add(",
           "int32_t PlayerStorage::get(", "bool PlayerStorage::has(",
           "bool PlayerStorage::remove(", "void PlayerStorage::ingest(",
           "void PlayerStorage::clearDirty(", "void PlayerStorage::upsertKey(",
           "void PlayerStorage::prepareForPersist(", "void PlayerStorage::getReservedRange(",
           "PlayerStorage::PlayerStorageDelta PlayerStorage::delta(",
           "void PlayerStorage::acknowledge("]
with tempfile.TemporaryDirectory(prefix="storage-ack-", dir=os.environ.get("TMPDIR")) as temporary:
    scratch = Path(temporary)
    (scratch / "player_storage.hpp").write_text(header)
    (scratch / "serial_save_queue.hpp").write_text(source("src/game/scheduling/serial_save_queue.hpp"))
    cpp = scratch / "regression.cpp"
    cpp.write_text(PRELUDE + "\n".join(method(anchor) for anchor in methods) + MAIN)
    binary = scratch / "regression"
    flags = ["-DHAS_REVISIONS"] if "std::map<uint32_t, uint64_t> revisions;" in header else []
    subprocess.run(["g++", "-std=c++20", "-O0", *flags, str(cpp), "-o", str(binary)], check=True, timeout=60)
    subprocess.run([str(binary)], check=True, timeout=10)
