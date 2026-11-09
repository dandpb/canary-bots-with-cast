"""Private QA build; source instrumentation never modifies the repository."""

import shutil
import subprocess
from pathlib import Path

root = Path("/review")
if Path("/out/bridge-only").exists():
    subprocess.run(
        [
            "g++",
            "-shared",
            "-fPIC",
            "-std=c++23",
            "-O1",
            "-fno-gnu-unique",
            "-DSPDLOG_COMPILED_LIB",
            "-DSPDLOG_FMT_EXTERNAL",
            "-I/source/src",
            "-I/opt/installed/x64-linux/include",
            "-I/opt/installed/x64-linux/include/luajit-2.1",
            "-I/opt/installed/x64-linux/include/mysql",
            "/review/tests/fixture/party_acceptance.cpp",
            "-o",
            "/out/party_acceptance.so",
        ],
        check=True,
    )
    raise SystemExit(0)
changed = []
for name in ["CMakeLists.txt", "CMakePresets.json"]:
    source = root / name
    destination = Path("/source") / name
    if source.exists():
        data = source.read_bytes().replace(b"\r\n", b"\n")
        if (
            not destination.exists()
            or destination.read_bytes().replace(b"\r\n", b"\n") != data
        ):
            destination.write_bytes(data)
            changed.append(name)
for rel in ["src", "cmake", "tests", "tools/bot_brain"]:
    for p in (root / rel).rglob("*"):
        if not p.is_file() or "__pycache__" in p.parts:
            continue
        dst = Path("/source") / p.relative_to(root)
        if not dst.is_file() or p.read_bytes() != dst.read_bytes():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dst)
            changed.append(str(p.relative_to(root)))
print("CURRENT MAIN SYNC", changed, flush=True)
tick = Path("/source/src/creatures/players/bot/bot_tick.cpp")
source = tick.read_text()
anchor = "void BotEngine::tick() {\n\ttickBrain();"
assert source.count(anchor) == 1
source = source.replace(
    anchor,
    """
namespace {
struct PartyQaSample { double total=0, bridge=0; };
static std::vector<PartyQaSample> partyQaSamples;
struct PartyQaScope {
 std::chrono::steady_clock::time_point start=std::chrono::steady_clock::now();
 double bridge=0;
 ~PartyQaScope() {
  if(partyQaSamples.size()<32768) partyQaSamples.push_back({std::chrono::duration<double,std::micro>(std::chrono::steady_clock::now()-start).count(),bridge});
 }
};
}
extern "C" const char* canaryPartyQaTimings() {
 static std::string text;
 nlohmann::json rows=nlohmann::json::array();
 for(const auto& s:partyQaSamples) rows.push_back({s.total,s.bridge});
 text=rows.dump(); partyQaSamples.clear(); return text.c_str();
}
void BotEngine::tick() {
 PartyQaScope qaScope;
 tickBrain();
 qaScope.bridge=std::chrono::duration<double,std::micro>(std::chrono::steady_clock::now()-qaScope.start).count();""",
)
tick.write_text(source)
subprocess.run(
    ["cmake", "-S/source", "-B/build", "-DCANARY_BUILD_TESTS=ON"], check=True
)
subprocess.run(
    [
        "cmake",
        "--build",
        "/build",
        "--target",
        "canary",
        "bot_engine",
        "canary_ut",
        "-j2",
    ],
    check=True,
)
subprocess.run(["/build/tests/unit/canary_ut"], cwd="/source", check=True)
for artifact in ["canary", "libbot_engine.so"]:
    shutil.copy2("/build/bin/" + artifact, "/out/" + artifact)
subprocess.run(
    [
        "g++",
        "-shared",
        "-fPIC",
        "-std=c++23",
        "-O1",
        "-fno-gnu-unique",
        "-DSPDLOG_COMPILED_LIB",
        "-DSPDLOG_FMT_EXTERNAL",
        "-I/source/src",
        "-I/opt/installed/x64-linux/include",
        "-I/opt/installed/x64-linux/include/luajit-2.1",
        "-I/opt/installed/x64-linux/include/mysql",
        "/review/tests/fixture/party_acceptance.cpp",
        "-o",
        "/out/party_acceptance.so",
    ],
    check=True,
)
