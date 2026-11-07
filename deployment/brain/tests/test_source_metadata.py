"""Build-time source identity using fresh throwaway Git/CMake fixtures only."""

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def run(*args, cwd):
    return subprocess.run(
        args, cwd=cwd, check=True, capture_output=True, text=True
    ).stdout


def test_build_metadata_refreshes_clean_dirty_commit_and_missing_git(tmp_path):
    source = tmp_path / "source"
    build = tmp_path / "build"
    source.mkdir()
    (source / "CMakeLists.txt").write_text(
        "cmake_minimum_required(VERSION 3.22)\nproject(metadata_probe LANGUAGES CXX)\n"
        f'include("{ROOT}/cmake/SourceMetadata.cmake")\n'
        "add_executable(bot_engine probe.cpp)\n"
        "target_compile_features(bot_engine PRIVATE cxx_std_20)\n"
        f'target_include_directories(bot_engine PRIVATE "{ROOT}/src")\n'
        "canary_target_source_metadata(bot_engine)\n"
    )
    (source / "probe.cpp").write_text(r"""
#include "gitmetadata.h"
#include "creatures/players/bot/bot_brain_channel.hpp"
#include <iostream>
int main() {
    botbrain::Session session;
    const nlohmann::json request = {{"version",1},{"type","telemetry_admit"},
        {"world","w"},{"bot_id",7},{"nonce","n"}};
    auto reply = session.admit(request, "w", 7, GIT_HEAD_SHA1, GIT_IS_DIRTY != 0, [] {
        return nlohmann::json{{"world","w"},{"captured_ms",1000},{"bot",{{"id",7}}}};
    });
    std::cout << reply.dump();
}
""")
    run("git", "init", cwd=source)
    run("git", "add", ".", cwd=source)
    run(
        "git",
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@local",
        "commit",
        "-m",
        "fixture",
        cwd=source,
    )
    sha = run("git", "rev-parse", "HEAD", cwd=source).strip()
    run("cmake", "-S", str(source), "-B", str(build), "-G", "Ninja", cwd=source)

    def rebuild():
        run("cmake", "--build", str(build), "--target", "bot_engine", cwd=source)
        return json.loads(run(str(build / "bot_engine"), cwd=source))

    clean = rebuild()
    assert (clean["source"], clean["source_dirty"], clean["fault"]) == (sha, False, "")
    # No reconfigure: even an untracked edit must change admission eligibility.
    marker = source / "untracked"
    marker.write_text("dirty")
    dirty = rebuild()
    assert (dirty["source"], dirty["source_dirty"], dirty["fault"]) == (
        sha,
        True,
        "source_unqualified",
    )
    marker.unlink()
    assert rebuild() == clean
    run(
        "git",
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@local",
        "commit",
        "--allow-empty",
        "-m",
        "next",
        cwd=source,
    )
    changed = rebuild()
    assert changed["source"] != sha
    assert changed["source"] == run("git", "rev-parse", "HEAD", cwd=source).strip()
    assert not changed["source_dirty"]
    # Git failure must replace cached identity with fail-closed values.
    (source / ".git").rename(tmp_path / "hidden-git")
    missing = rebuild()
    assert (missing["source"], missing["source_dirty"], missing["fault"]) == (
        "unknown",
        True,
        "source_unqualified",
    )
