"""Exercise the real SQL worker with a controlled connection and dispatcher."""

import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[2]
STUBS = r"""
#include <atomic>
#include <cassert>
#include <chrono>
#include <functional>
#include <future>
#include <latch>
#include <memory>
#include <string>

using DBResult_ptr = std::shared_ptr<int>;
static std::latch connecting(1), releaseConnection(1);
static std::atomic<int> connections = 0;
static std::atomic<int> queries = 0;
static std::atomic<bool> available = false;

struct Database {
    bool connect() {
        if (++connections == 1) {
            connecting.count_down();
            releaseConnection.wait();
            return false;
        }
        return available;
    }
    bool executeQuery(const std::string &) { ++queries; return true; }
    DBResult_ptr storeQuery(const std::string &, bool &success) {
        ++queries;
        success = true;
        return nullptr;
    }
    bool isConnected() const { return available; }
};

struct Dispatcher {
    void addEvent(std::function<void()> callback, const char *) { callback(); }
};
static Dispatcher &g_dispatcher() { static Dispatcher dispatcher; return dispatcher; }
struct Logger { void warn(const char *) {} void info(const char *) {} };
static Logger &g_logger() { static Logger logger; return logger; }
"""

SCENARIO = r"""
int main() {
    using namespace std::chrono_literals;
    BotDatabaseTasks worker;
    constexpr int burst = 1200;
    std::atomic<int> failures = 0;
    std::promise<void> allFailed;
    auto failure = [&](const auto &result, bool ok) {
        assert(!ok && !result);
        if (++failures == burst + 1) allFailed.set_value();
    };
    worker.execute("first", failure);
    connecting.wait();
    for (int i = 0; i < burst; ++i) worker.store("read", failure);
    assert(failures > 0); // Rejected jobs complete while the connection is still blocked.
    releaseConnection.count_down();
    assert(allFailed.get_future().wait_for(1500ms) == std::future_status::ready);
    assert(connections == 1 && queries == 0 && failures == burst + 1);

    available = true;
    std::this_thread::sleep_for(2s);
    std::promise<bool> recovered;
    auto recovery = recovered.get_future();
    worker.execute("after reconnect", [&](const auto &, bool ok) { recovered.set_value(ok); });
    assert(recovery.wait_for(1s) == std::future_status::ready && recovery.get());
    assert(connections == 2 && queries == 1);
}
"""


def main() -> None:
    files = (
        ROOT / "src/database/botdatabasetasks.hpp",
        ROOT / "src/database/botdatabasetasks.cpp",
    )
    worker = "\n".join(
        line
        for path in files
        for line in path.read_text().splitlines()
        if not line.startswith(('#include "', "#pragma once"))
    )
    with TemporaryDirectory(prefix="bot-database-tasks-") as directory:
        source = Path(directory) / "test.cpp"
        binary = source.with_suffix("")
        source.write_text(STUBS + worker + SCENARIO)
        subprocess.run(
            [
                os.environ.get("BOT_TEST_CXX", "c++"),
                "-std=c++20",
                "-pthread",
                str(source),
                "-o",
                str(binary),
            ],
            check=True,
        )
        subprocess.run([str(binary)], check=True, timeout=8)
    print("PASS: SQL queue capacity, prompt failure callbacks and reconnect")


if __name__ == "__main__":
    main()
