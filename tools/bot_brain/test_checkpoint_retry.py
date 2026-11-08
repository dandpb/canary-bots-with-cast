"""Exercise the real checkpoint/SQL retry bodies with deterministic server faults."""

import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def function(path, signature):
    source = (ROOT / path).read_text()
    start = source.index(signature)
    opening = source.index("{", start)
    depth = 1
    end = opening + 1
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[start:end]


CPP = r"""
#include <atomic>
#include <cassert>
#include <chrono>
#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>
#include <thread>
#include <vector>
#include <mysql/errmsg.h>
#include "game/scheduling/serial_save_queue.hpp"
#define FMT_HEADER_ONLY
#include <fmt/format.h>
struct Logger {
 template<class... T> void error(T&&...) {}
 template<class... T> void warn(T&&...) {}
 template<class... T> void info(T&&...) {}
};
Logger& g_logger() { static Logger logger; return logger; }
namespace test_clock { template<class R,class P> void sleep_for(std::chrono::duration<R,P>) {} }
struct DatabaseException:std::runtime_error { using runtime_error::runtime_error; };
struct Model {
 int committed=0, staged=0, attempts=0, firstWrites=0;
 unsigned error=0;
 unsigned transports=0,deadlocks=0; unsigned long connection=1;
 enum Fault { Once, Always, Syntax, Connection, Begin, LostCommit, None, Missing,
              MixedStatement, PriorRecovery, TransparentRecovery } fault=Once;
} state;
int mysql_query(Model*, const char* query) {
 if (std::string(query)=="increment") { ++state.staged; ++state.firstWrites; }
 if(std::string(query)=="recover") {
  if(state.fault==Model::PriorRecovery && state.transports++==0) {
   state.committed=state.staged;state.error=2013;return 1;
  }
  if(state.fault==Model::TransparentRecovery && state.transports++==0) {
   state.committed=state.staged;++state.connection;
  }
 }
 if(std::string(query)=="failure" && state.fault==Model::MixedStatement && state.transports++==0) {
  state.committed=state.staged;state.error=2013;return 1;
 }
 if(std::string(query)=="failure" &&
    (state.fault==Model::MixedStatement || state.fault==Model::PriorRecovery || state.fault==Model::TransparentRecovery)
    && state.deadlocks++==0) {
  state.error=1213;state.staged=state.committed;return 1;
 }
 if (std::string(query)=="failure" &&
     (state.fault==Model::Always || state.fault==Model::Syntax || state.fault==Model::Connection ||
      (state.fault==Model::Once && state.attempts==1))) {
   state.error=state.fault==Model::Syntax?1064:state.fault==Model::Connection?2013:1213;
   if(state.error==1213) state.staged=state.committed;
   return 1;
 }
 state.error=0; return 0;
}
unsigned mysql_errno(Model*) { return state.error; }
unsigned long mysql_thread_id(Model*) { return state.connection; }
const char* mysql_error(Model*) { return "injected database error"; }
struct Row { template<class T> T getNumber(const char*) { return 1; } };
class Database {
public:
 static Database& getInstance() { static Database db; return db; }
 bool retryQuery(std::string_view query,int retries);
 bool executeQuery(std::string_view query) {
   bool result=retryQuery(query,10);
   state.error=0; // Subsequent client APIs need not retain the failed query errno.
   return result;
 }
 std::shared_ptr<Row> storeQuery(std::string_view) {
   return state.fault==Model::Missing?nullptr:std::make_shared<Row>();
 }
 struct TransactionContext { const Database* owner; uint64_t connectionId; uint64_t recoveryEpoch; };
 TransactionContext transactionContext() const;
 bool canRetryDeadlock(const TransactionContext&) const;
 unsigned getLastExecuteError() const;
private:
 static bool isRecoverableError(unsigned);
 Model* handle=&state;
 static thread_local std::pair<const Database*,unsigned> lastExecuteError_;
 static thread_local uint64_t recoveryEpoch_;
};
thread_local std::pair<const Database*,unsigned> Database::lastExecuteError_{nullptr,0};
thread_local uint64_t Database::recoveryEpoch_=0;
struct DBTransaction {
 template<class F> static bool executeWithinTransaction(const F& callback) {
   ++state.attempts; state.staged=state.committed;
   if(state.fault==Model::Begin) return false;
   try {
     bool result=callback(); state.committed=state.staged;
     return state.fault==Model::LostCommit?false:result;
   } catch(const std::exception&) {state.staged=state.committed;return false;}
 }
};
struct PlayerSaveSnapshot {
 unsigned guid=7;
 std::vector<std::string> statements{"increment","failure","finish"};
 std::string loginOnly="login-only";
};
struct IOLoginData { static bool persistPlayerSave(const PlayerSaveSnapshot&); };
"""

MAIN = r"""
int main() {
 PlayerSaveSnapshot snapshot;
 state.fault=Model::Once;
 assert(IOLoginData::persistPlayerSave(snapshot));
 assert(state.attempts==2 && state.firstWrites==2 && state.committed==1);
 state={};state.fault=Model::Always;
 SerialSaveQueue<PlayerSaveSnapshot> queue;
 auto request=queue.request(snapshot.guid,snapshot);
 auto work=queue.take(snapshot.guid);assert(work);
 bool persisted=IOLoginData::persistPlayerSave(work->value);
 assert(!persisted);
 queue.finish(snapshot.guid,work->generation,persisted);
 assert(queue.find(snapshot.guid) && !request.completed.get());
 assert(state.attempts==5 && state.committed==0);
 state={};state.fault=Model::Syntax;
 assert(!IOLoginData::persistPlayerSave(snapshot));
 assert(state.attempts==1 && state.committed==0);
 state={};state.fault=Model::Connection;
 assert(!IOLoginData::persistPlayerSave(snapshot));
 assert(state.attempts==1 && state.committed==0);
 state={};state.fault=Model::Begin;
 assert(!IOLoginData::persistPlayerSave(snapshot));
 assert(state.attempts==1 && state.committed==0);
 state={};state.fault=Model::LostCommit;
 assert(!IOLoginData::persistPlayerSave(snapshot));
 assert(state.attempts==1 && state.committed==1);
 state={};state.fault=Model::None;
 assert(IOLoginData::persistPlayerSave(snapshot));
 assert(state.attempts==1 && state.committed==1);
 state={};state.fault=Model::Missing;
 assert(!IOLoginData::persistPlayerSave(snapshot));
 assert(state.attempts==1 && state.committed==0);
 for(auto mode:{Model::MixedStatement,Model::PriorRecovery,Model::TransparentRecovery}) {
  state={};state.fault=mode;
  auto mixed=snapshot;
  if(mode!=Model::MixedStatement) mixed.statements={"increment","recover","failure","finish"};
  assert(!IOLoginData::persistPlayerSave(mixed));
  assert(state.attempts==1 && state.committed==1);
 }
 state={};state.fault=Model::Once;
 assert(IOLoginData::persistPlayerSave(snapshot));
 assert(state.attempts==2 && state.committed==1);
}
"""


def main():
    source = CPP + function(
        "src/database/database.cpp", "bool Database::isRecoverableError("
    )
    source += function("src/database/database.cpp", "bool Database::retryQuery(")
    source += function(
        "src/database/database.cpp", "unsigned int Database::getLastExecuteError("
    )
    source += function(
        "src/database/database.cpp",
        "Database::TransactionContext Database::transactionContext(",
    )
    source += function("src/database/database.cpp", "bool Database::canRetryDeadlock(")
    source += function("src/io/iologindata.cpp", "bool IOLoginData::persistPlayerSave(")
    source += MAIN
    source = source.replace("std::this_thread::sleep_for", "test_clock::sleep_for")
    with tempfile.TemporaryDirectory(prefix="checkpoint-retry-") as directory:
        path = Path(directory)
        (path / "test.cpp").write_text(source)
        command = [
            os.environ.get("BOT_TEST_CXX", "g++"),
            "-std=c++20",
            "-O0",
            "-I",
            str(ROOT / "src"),
        ]
        if os.environ.get("BOT_TEST_INCLUDES"):
            command += ["-I", os.environ["BOT_TEST_INCLUDES"]]
        subprocess.run(
            command + [str(path / "test.cpp"), "-o", str(path / "test")], check=True
        )
        subprocess.run([str(path / "test")], check=True)
    print(
        "PASS checkpoint deadlock atomic retry, bounds, fatal/unknown commit handling"
    )


if __name__ == "__main__":
    main()
