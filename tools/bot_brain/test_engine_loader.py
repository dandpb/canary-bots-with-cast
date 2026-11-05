#!/usr/bin/env python3
"""Exercise the real dlopen loader with disposable libraries, without a game/DB.

Run in the native build image (vcpkg includes under /opt/installed/x64-linux).
Only logging is replaced. The engine fixture implements the real IBotEngine.
"""
import os
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INCLUDES = Path(os.environ.get("BOT_TEST_INCLUDES", "/opt/installed/x64-linux/include"))


def run(*args):
    subprocess.run([str(arg) for arg in args], check=True)


with tempfile.TemporaryDirectory(prefix="canary-loader-test-") as directory:
    scratch = Path(directory)
    logger = scratch / "lib/logging/logger.hpp"
    logger.parent.mkdir(parents=True)
    logger.write_text("""#pragma once
struct TestLogger {
 template<class... T> void info(T&&...) {};
 template<class... T> void error(T&&...) {};
 template<class... T> void warn(T&&...) {};
};
inline TestLogger& g_logger() { static TestLogger logger; return logger; }
""")
    prelude = scratch / "prelude.hpp"
    prelude.write_text("#include <bits/stdc++.h>\n#include <fmt/format.h>\n")
    interface = (ROOT / "src/creatures/players/bot/bot_engine_interface.hpp").read_text()
    methods = []
    for declaration in re.findall(r"^\s*virtual (.+?) = 0;", interface, re.MULTILINE):
        if "loadHuntData(" in declaration:
            body = '{\n#ifdef THROW_INIT\n throw FixtureError();\n#endif\n}'
        elif declaration.startswith("void "):
            body = "{}"
        elif "countActiveBots(" in declaration:
            body = "{ return 7; }"
        else:
            body = "{ return {}; }"
        methods.append(declaration + " override " + body)
    fixture = scratch / "fixture.cpp"
    fixture.write_text("""#include "creatures/players/bot/bot_engine_interface.hpp"
class FixtureError : public std::exception {
 public: const char* what() const noexcept override { return "init exception"; }
 ~FixtureError() override {}
};
class Fixture final : public IBotEngine { public:
""" + "\n".join(methods) + """
};
#ifndef MISSING_ABI
extern "C" const char* botEngineAbiTag() {
#ifdef BAD_ABI
 return "incompatible";
#else
 return BOT_ENGINE_ABI_TAG;
#endif
}
#endif
extern "C" bool prepareBotEngine(IBotEngine*, char*, size_t) {
#ifdef THROW_DATA
 throw std::runtime_error("parse exception");
#endif
#ifdef BAD_DATA
 return false;
#else
 return true;
#endif
}
extern "C" IBotEngine* createBotEngine() {
#ifdef THROW_FACTORY
 throw std::runtime_error("factory exception");
#endif
#ifdef BAD_ABI
 std::abort(); // ABI must be checked before the factory.
#endif
#ifdef NULL_FACTORY
 return nullptr;
#else
 return new Fixture;
#endif
}
#ifndef MISSING_DESTROY
extern "C" void destroyBotEngine(IBotEngine* engine) { delete engine; }
#endif
""")
    main = ROOT / "tests/fixture/bot_engine_loader_main.cpp"
    flags = [os.environ.get("BOT_TEST_CXX", "g++"), '-DBOT_ENGINE_ABI_TAG="loader-test-v1"', "-std=c++23", "-g", "-O1", "-fno-gnu-unique",
             "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
             "-include", prelude, "-I", scratch, "-I", ROOT / "src", "-I", INCLUDES]
    variants = {"good": None, "abi": "BAD_ABI", "missingabi": "MISSING_ABI",
                "symbols": "MISSING_DESTROY", "factory": "NULL_FACTORY", "data": "BAD_DATA",
                "throwfactory": "THROW_FACTORY", "throwdata": "THROW_DATA", "throwinit": "THROW_INIT"}
    for name, define in variants.items():
        run(*flags, *(["-D" + define] if define else []), "-shared", "-fPIC", fixture,
            "-o", scratch / (name + ".so"))
    (scratch / "invalid.so").write_text("not an ELF shared library")
    executable = scratch / "test-loader"
    run(*flags, main, ROOT / "src/creatures/players/bot/bot_engine_loader.cpp",
        "-ldl", "-o", executable)
    run(executable, scratch)
