"""Opt-in real MariaDB deadlock test; creates only private, disposable resources."""

import argparse
import os
import secrets
import subprocess
import tempfile
import time
from pathlib import Path

from test_checkpoint_retry import ROOT, function

CPP = r"""
#include <atomic>
#include <barrier>
#include <cassert>
#include <chrono>
#include <concepts>
#include <cstdlib>
#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>
#include <thread>
#include <vector>
#include <mysql/mysql.h>
#define FMT_HEADER_ONLY
#include <fmt/format.h>
struct Logger {
 template<class... T> void error(T&&...) {}
 template<class... T> void warn(T&&...) {}
 template<class... T> void info(T&&...) {}
};
Logger& g_logger() { static Logger logger; return logger; }
struct DatabaseException:std::runtime_error { using runtime_error::runtime_error; };
struct Row {
 unsigned long long value;
 template<class T> T getNumber(const char*) { return static_cast<T>(value); }
};
std::atomic<unsigned> deadlocks{0};
class Database {
public:
 Database() {
  handle=mysql_init(nullptr); assert(handle);
  assert(mysql_real_connect(handle,std::getenv("CHECKPOINT_DB_HOST"),"checkpoint",
   std::getenv("CHECKPOINT_DB_PASSWORD"),"checkpoint",3306,nullptr,0));
  assert(executeQuery("SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ"));
 }
 ~Database() { mysql_close(handle); }
 static Database& getInstance() { thread_local Database db; return db; }
 bool retryQuery(std::string_view,int);
 bool executeQuery(std::string_view query) {
  bool success=retryQuery(query,10);
  if(!success && mysql_errno(handle)==1213) ++deadlocks;
  mysql_free_result(mysql_store_result(handle));
  return success;
 }
 std::shared_ptr<Row> storeQuery(const std::string& query) {
  if(mysql_query(handle,query.c_str())) return nullptr;
  auto result=mysql_store_result(handle); if(!result) return nullptr;
  auto values=mysql_fetch_row(result);
  auto row=values?std::make_shared<Row>(Row{std::stoull(values[0])}):nullptr;
  mysql_free_result(result); return row;
 }
 bool beginTransaction() { return executeQuery("BEGIN"); }
 bool rollback() { return mysql_rollback(handle)==0; }
 bool commit() { return mysql_commit(handle)==0; }
 unsigned getLastExecuteError() const;
private:
 static bool isRecoverableError(unsigned) { return false; }
 MYSQL* handle;
 static thread_local std::pair<const Database*,unsigned> lastExecuteError_;
};
thread_local std::pair<const Database*,unsigned> Database::lastExecuteError_{nullptr,0};
struct PlayerSaveSnapshot {
 unsigned guid;
 std::vector<std::string> statements;
 std::string loginOnly;
};
struct IOLoginData { static bool persistPlayerSave(const PlayerSaveSnapshot&); };
"""

MAIN = r"""
int main() {
 mysql_library_init(0,nullptr,nullptr);
 auto& db=Database::getInstance();
 assert(db.executeQuery("CREATE TABLE players(id INT PRIMARY KEY,save INT,experience BIGINT) ENGINE=InnoDB"));
 assert(db.executeQuery("CREATE TABLE player_items(player_id INT,sid INT,itemtype INT,PRIMARY KEY(player_id,sid)) ENGINE=InnoDB"));
 for(int round=0;round<5;++round) {
  // Reset the physical B-tree too; delete-marked records change gap boundaries.
  assert(db.executeQuery("TRUNCATE TABLE player_items"));
  assert(db.executeQuery("DELETE FROM players"));
  assert(db.executeQuery("INSERT INTO players VALUES(101,1,100),(102,1,100),(103,1,100),(104,1,100)"));
  std::barrier ready(4); bool saved[4]={false,false,false,false};
  auto worker=[&](int i) {
   Database::getInstance();
   unsigned id=101+i;
   PlayerSaveSnapshot snapshot{id,{
    fmt::format("UPDATE players SET experience=200 WHERE id={}",id),
    fmt::format("DELETE FROM player_items WHERE player_id={}",id),
    "DO SLEEP(0.25)",
    fmt::format("INSERT INTO player_items VALUES({},1,999)",id)},""};
   ready.arrive_and_wait();
   saved[i]=IOLoginData::persistPlayerSave(snapshot);
  };
  std::vector<std::thread> threads;
  for(int i=0;i<4;++i) threads.emplace_back(worker,i);
  for(auto& thread:threads) thread.join();
  for(bool success:saved) assert(success);
  assert(db.storeQuery("SELECT COUNT(*) FROM players WHERE experience=200")->getNumber<int>("count")==4);
  assert(db.storeQuery("SELECT COUNT(*) FROM player_items WHERE itemtype=999")->getNumber<int>("count")==4);
 }
 assert(deadlocks>=15);
 fmt::print("PASS 20 real checkpoints, {} induced deadlocks, XP/inventory atomic\n",deadlocks.load());
}
"""


def client():
    source = (
        CPP
        + function("src/database/database_definitions.hpp", "enum TransactionStates_t")
        + ";\n"
    )
    source += function("src/database/database.hpp", "class DBTransaction {") + ";\n"
    source += function("src/database/database.cpp", "bool Database::retryQuery(")
    source += function(
        "src/database/database.cpp", "unsigned int Database::getLastExecuteError("
    )
    source += function("src/io/iologindata.cpp", "bool IOLoginData::persistPlayerSave(")
    source += MAIN
    includes = Path(os.environ["BOT_TEST_INCLUDES"])
    libraries = includes.parent / "lib"
    with tempfile.TemporaryDirectory(prefix="checkpoint-mariadb-") as directory:
        path = Path(directory)
        (path / "test.cpp").write_text(source)
        subprocess.run(
            [
                os.environ.get("BOT_TEST_CXX", "g++"),
                "-std=c++20",
                "-O0",
                "-I",
                str(includes),
                str(path / "test.cpp"),
                str(libraries / "libmariadbclient.a"),
                "-L",
                str(libraries),
                "-lssl",
                "-lcrypto",
                "-lz",
                "-ldl",
                "-pthread",
                "-o",
                str(path / "test"),
            ],
            check=True,
        )
        subprocess.run([str(path / "test")], check=True, timeout=30)


def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def disposable_database():
    image = os.environ["BOT_TEST_BUILD_IMAGE"]
    db_image = subprocess.check_output(
        ["docker", "image", "inspect", "mariadb:11.4", "--format", "{{.Id}}"], text=True
    ).strip()
    identity = "canary-checkpoint-qa-" + secrets.token_hex(6)
    database = identity + "-database"
    created = False
    with tempfile.TemporaryDirectory(prefix="checkpoint-db-env-") as directory:
        password = secrets.token_hex(24)
        env = Path(directory) / "database.env"
        env.write_text(
            "MARIADB_DATABASE=checkpoint\nMARIADB_USER=checkpoint\n"
            + f"MARIADB_PASSWORD={password}\nMARIADB_ROOT_PASSWORD={password}\n"
        )
        env.chmod(0o600)
        client_env = Path(directory) / "client.env"
        client_env.write_text(
            f"CHECKPOINT_DB_HOST=checkpoint-db\nCHECKPOINT_DB_PASSWORD={password}\n"
        )
        client_env.chmod(0o600)
        run(
            "docker",
            "network",
            "create",
            "--internal",
            identity,
            stdout=subprocess.DEVNULL,
        )
        try:
            run(
                "docker",
                "run",
                "-d",
                "--rm",
                "--pull",
                "never",
                "--name",
                database,
                "--network",
                identity,
                "--network-alias",
                "checkpoint-db",
                "--env-file",
                str(env),
                "--tmpfs",
                "/var/lib/mysql",
                db_image,
                stdout=subprocess.DEVNULL,
            )
            created = True
            for _ in range(100):
                ready = subprocess.run(
                    [
                        "docker",
                        "exec",
                        database,
                        "sh",
                        "-ec",
                        'MYSQL_PWD="$MARIADB_ROOT_PASSWORD" mariadb -h127.0.0.1 -uroot checkpoint -e "SELECT 1"',
                    ],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                if ready.returncode == 0:
                    break
                time.sleep(0.2)
            else:
                raise TimeoutError("disposable MariaDB startup")
            run(
                "docker",
                "run",
                "--rm",
                "--pull",
                "never",
                "--network",
                identity,
                "--env-file",
                str(client_env),
                "-e",
                "BOT_TEST_INCLUDES=/opt/installed/x64-linux/include",
                "-v",
                str(ROOT) + ":/source:ro",
                "--entrypoint",
                "python3",
                image,
                "/source/tools/bot_brain/test_checkpoint_deadlock_db.py",
                "--client",
            )
        finally:
            try:
                evidence = os.environ.get("BOT_TEST_EVIDENCE")
                if created and evidence:
                    logs = subprocess.run(
                        ["docker", "logs", database],
                        check=False,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                    )
                    (Path(evidence) / (identity + ".log")).write_bytes(logs.stdout)
            finally:
                try:
                    if created:
                        subprocess.run(
                            ["docker", "rm", "-f", database],
                            check=False,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE,
                        )
                finally:
                    run("docker", "network", "rm", identity, stdout=subprocess.DEVNULL)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", action="store_true")
    args = parser.parse_args()
    client() if args.client else disposable_database()
