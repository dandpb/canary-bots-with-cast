#!/usr/bin/env python3
"""Compile only the accepted-navigation reset block against stubs, plus negative control.

No game, database, provider or repository build. Tests the source branch immediately
before accepted outcome, not a similarly named reset elsewhere in the file.
"""
import os
from pathlib import Path
import re
import resource
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
source = (ROOT / "src/creatures/players/bot/bot_brain.cpp").read_text()
anchor = source.index('if (action == "resupply") {', source.index('void BotEngine::tickBrain()'))
accepted = source.index('auto outcome = brainOutcome(brain_->world, guid, id, "accepted", "objective_started");', anchor)
region = source[anchor:accepted]
match = re.search(r'if \(action == "hunt".*?\n\t\t\t}', region, re.S)
assert match, "accepted-navigation reset branch absent"
block = match.group(0)
assert not region[match.end():].strip(), "reset is not immediately before accepted outcome"
assert block.count('plannerReplan(*bot, bot->getPlayer());') == 1
assert block.count('s_fcConsecutiveFailures.erase(guid);') == 1
negative = block.replace(' || action == "retreat"', '', 1)
assert negative != block, "negative control could not remove retreat admission"
prelude = r"""
#include <cassert>
#include <string>
#include <unordered_map>
struct Bot { int player=7; int* getPlayer() { return &player; } };
std::unordered_map<unsigned,int> s_fcConsecutiveFailures;
int replans=0;
void plannerReplan(Bot&,int*) { ++replans; }
void accept(const std::string& action) {
 Bot value; Bot* bot=&value; unsigned guid=11;
"""
tail = r"""
}
int main() {
 for (const auto* action : {"hunt", "resupply", "retreat", "follow", "hold", "target", "continue"}) {
  replans=0; s_fcConsecutiveFailures={{11,5},{12,5}};
  accept(action);
  bool navigation=std::string(action)=="hunt" || std::string(action)=="resupply" || std::string(action)=="retreat" || std::string(action)=="follow";
  assert(replans==(navigation ? 1 : 0));
  assert(s_fcConsecutiveFailures.contains(11)==!navigation);
  assert(s_fcConsecutiveFailures.at(12)==5);
 }
}
"""
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
with tempfile.TemporaryDirectory(prefix="accepted-navigation-", dir=os.environ.get("TMPDIR")) as directory:
 scratch=Path(directory)
 for label, body, expected in [("current",block,0),("without_retreat",negative,None)]:
  cpp=scratch/(label+".cpp"); exe=scratch/label
  cpp.write_text(prelude+body+tail)
  subprocess.run(["g++","-std=c++20","-O0",str(cpp),"-o",str(exe)],check=True,timeout=30)
  result=subprocess.run([str(exe)],capture_output=True,timeout=10)
  if expected == 0:
   assert result.returncode == 0, "current accepted-navigation source failed"
  else:
   assert result.returncode != 0, "removing retreat must fail"
  print(label+": "+("PASS" if expected == 0 else "EXPECTED_REJECTION"),flush=True)
