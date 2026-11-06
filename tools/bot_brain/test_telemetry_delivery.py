"""Qualify native telemetry delivery against real isolated Unix datagram sockets.

Run: python3 tools/bot_brain/test_telemetry_delivery.py --include /path/to/include
CANARY_TEST_INCLUDE may supply the nlohmann include directory. The compatibility
adapter only exposes the old direct-send behavior, allowing a runtime RED before
the native outbox exists; once present, every outbox operation uses production.
No game, Docker, provider, or database is used.
"""

import argparse
import os
import subprocess
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--include", type=Path, default=os.environ.get("CANARY_TEST_INCLUDE")
)
parser.add_argument("--case")
args = parser.parse_args()
include = args.include or Path(
    "/home/daniel/m5/telemetry-channel-header-20261106-df5bb452/include"
)
if not (include / "nlohmann/json.hpp").is_file():
    raise SystemExit(
        "Set --include or CANARY_TEST_INCLUDE to headers containing nlohmann/json.hpp"
    )
native = (
    "class TelemetryOutbox"
    in (root / "src/creatures/players/bot/bot_brain_channel.hpp").read_text()
)
brain_source = (root / "src/creatures/players/bot/bot_brain.cpp").read_text()
tick_source = (root / "src/creatures/players/bot/bot_tick.cpp").read_text()
periodic_publish = next(
    line.strip()
    for line in brain_source.splitlines()
    if "++session.telemetrySequence, now, session.deaths, phase, brainOwns(guid)"
    in line
)
death_publish = next(
    line.strip()
    for line in tick_source.splitlines()
    if "++session.telemetrySequence, botMonoMs(), session.deaths" in line
)
tick_calls = [
    brain_source.find("\tbrain_->flushTelemetry();"),
    brain_source.find("\tbrain_->sendDeliveryStatus();"),
]
tick_tail = ""
if native:
    assert min(tick_calls) >= 0
    tick_tail = brain_source[
        min(tick_calls) : brain_source.index(
            "\tif (brainTickMicroseconds.size()", min(tick_calls)
        )
    ]

source = r"""
#include <cassert>
#include <cerrno>
#include <iostream>
#include "creatures/players/bot/bot_brain_channel.hpp"
#if !HAS_NATIVE_OUTBOX
namespace botbrain {
 // The old publisher calls Channel::send immediately and ignores failures.
 class TelemetryOutbox {
  uint64_t accepted_=0;
 public:
  TelemetryOutbox(size_t=64,size_t=65536) {}
  void beginTick() {}
  bool publish(Channel& channel,const nlohmann::json& frame) {
   const bool sent=channel.send(frame);if(sent) accepted_=frame.at("sequence").get<uint64_t>();return sent;
  }
  bool enqueue(const nlohmann::json&) { return false; }
  size_t flush(Channel&) { return 0; }
  void discard() {}
  size_t pendingFrames() const { return 0; }size_t pendingBytes() const { return 0; }
  uint64_t acceptedSequence() const { return accepted_; }
  uint64_t overflowFrames() const { return 0; }uint64_t discardedFrames() const { return 0; }
  nlohmann::json status(const std::string&,uint32_t,int64_t,uint64_t) const { return {}; }
 };
}
#endif
using Json=nlohmann::json;
int64_t botMonoMs() { return 1001; }
#if HAS_NATIVE_OUTBOX
void finishTick(botbrain::Runtime* brain_) {
@TICK_TAIL@
}
void publishPeriodic(botbrain::Runtime* brain_,uint32_t guid,int64_t now) {
 auto& session=brain_->sessions[guid];const std::string phase="alive";auto brainOwns=[](uint32_t){return false;};
@PERIODIC_PUBLISH@
}
void publishDeath(botbrain::Runtime* brain_,uint32_t guid) {
 auto& session=brain_->sessions[guid];++session.deaths;
@DEATH_PUBLISH@
}
#endif
Json frame(uint64_t sequence,uint32_t guid=65001,std::string world="delivery-test") {
 return botbrain::telemetry(world,guid,sequence,sequence*1000,0,"alive",false);
}
struct Sockets {
 std::string directory;std::unique_ptr<botbrain::Channel> channel;int receiver=-1;
 explicit Sockets(std::string path):directory(std::move(path)) {
  std::filesystem::create_directories(directory);
  channel=std::make_unique<botbrain::Channel>(directory);bindReceiver();
 }
 void closeReceiver() { if(receiver>=0) close(receiver);receiver=-1;unlink((directory+"/worker.sock").c_str()); }
 void bindReceiver() {
  closeReceiver();receiver=socket(AF_UNIX,SOCK_DGRAM|SOCK_NONBLOCK|SOCK_CLOEXEC,0);assert(receiver>=0);
  sockaddr_un address{};address.sun_family=AF_UNIX;const auto path=directory+"/worker.sock";
  std::copy(path.begin(),path.end(),address.sun_path);
  assert(bind(receiver,reinterpret_cast<sockaddr*>(&address),sizeof(address))==0);
 }
 void saturate() {
  for(size_t i=0;i<10000;i++) {
   errno=0;if(!channel->send({{"type","padding"},{"data",std::string(1077,'x')}})) {
    assert(errno==EAGAIN || errno==EWOULDBLOCK);return;
   }
  }
  assert(false && "isolated receiver did not saturate");
 }
 std::vector<Json> drain() {
  std::vector<Json> packets;
  for(size_t i=0;i<20000;i++) {
   std::array<char,32769> bytes{};const auto size=recv(receiver,bytes.data(),bytes.size(),MSG_DONTWAIT);
   if(size<0) {assert(errno==EAGAIN || errno==EWOULDBLOCK);return packets;}
   packets.push_back(Json::parse(bytes.data(),bytes.data()+size));
  }
  assert(false && "isolated receiver failed to drain");return packets;
 }
 ~Sockets() { closeReceiver();channel.reset();std::filesystem::remove_all(directory); }
};
std::vector<uint64_t> sequences(const std::vector<Json>& packets) {
 std::vector<uint64_t> result;
 for(const auto& packet:packets) if(packet.value("type","")=="telemetry") result.push_back(packet.at("sequence"));
 return result;
}
int main(int argc,char** argv) {
 assert(argc==3);const std::string scenario=argv[1];Sockets sockets(argv[2]);botbrain::TelemetryOutbox box;
 if(scenario=="fifo_pressure") {
  assert(box.publish(*sockets.channel,frame(219)));assert(box.acceptedSequence()==219);
  sockets.saturate();box.beginTick();assert(box.publish(*sockets.channel,frame(220)));
  assert(box.publish(*sockets.channel,frame(221)));
  assert(box.pendingFrames()==2 && box.acceptedSequence()==219);
  assert((sequences(sockets.drain())==std::vector<uint64_t>{219}));
  box.beginTick();assert(box.flush(*sockets.channel)==2);
  assert((sequences(sockets.drain())==std::vector<uint64_t>{220,221}));
  assert(box.pendingFrames()==0 && box.pendingBytes()==0 && box.acceptedSequence()==221);
 } else if(scenario=="first_error_stops_tick") {
  sockets.saturate();box.beginTick();assert(box.publish(*sockets.channel,frame(1)));
  sockets.drain();assert(box.flush(*sockets.channel)==0);
  assert(sequences(sockets.drain()).empty() && box.pendingFrames()==1);
  box.beginTick();assert(box.flush(*sockets.channel)==1 && box.acceptedSequence()==1);
 } else if(scenario=="shared_budget") {
  box.beginTick();assert(box.publish(*sockets.channel,frame(1)));
  assert(box.enqueue(frame(2)) && box.enqueue(frame(3)));
  assert(box.flush(*sockets.channel)==1 && box.pendingFrames()==1);
  assert(box.flush(*sockets.channel)==0);
  assert((sequences(sockets.drain())==std::vector<uint64_t>{1,2}));
  box.beginTick();assert(box.flush(*sockets.channel)==1);
  assert((sequences(sockets.drain())==std::vector<uint64_t>{3}));
 } else if(scenario=="multiple_publish_budget") {
  box.beginTick();assert(box.publish(*sockets.channel,frame(1)));
  assert(box.publish(*sockets.channel,frame(2)) && box.publish(*sockets.channel,frame(3)));
  assert(box.acceptedSequence()==2 && box.pendingFrames()==1 && box.flush(*sockets.channel)==0);
  assert((sequences(sockets.drain())==std::vector<uint64_t>{1,2}));
  box.beginTick();assert(box.flush(*sockets.channel)==1 && box.acceptedSequence()==3);
 } else if(scenario=="frame_overflow") {
  botbrain::TelemetryOutbox limited(2,65536);
  assert(limited.enqueue(frame(1)) && limited.enqueue(frame(2)));
  assert(!limited.enqueue(frame(3)) && limited.overflowFrames()==1 && limited.pendingFrames()==2);
  limited.beginTick();assert(limited.flush(*sockets.channel)==2);
  assert((sequences(sockets.drain())==std::vector<uint64_t>{1,2}));
  limited.beginTick();assert(limited.publish(*sockets.channel,frame(4)));
  assert(limited.overflowFrames()==1 && limited.acceptedSequence()==4);
 } else if(scenario=="byte_overflow") {
  const auto bytes=frame(1).dump().size();botbrain::TelemetryOutbox limited(64,bytes+1);
  assert(limited.enqueue(frame(1)) && limited.pendingBytes()==bytes);
  assert(!limited.enqueue(frame(2)) && limited.pendingFrames()==1 && limited.pendingBytes()==bytes);
  assert(limited.overflowFrames()==1);
 } else if(scenario=="immutable_frame") {
  auto packet=frame(1);assert(box.enqueue(packet));packet["sequence"]=999;packet["phase"]="dead";
  box.beginTick();assert(box.flush(*sockets.channel)==1);auto received=sockets.drain();
  assert(received.size()==1 && received[0].at("sequence")==1 && received[0].at("phase")=="alive");
 } else if(scenario=="initial_status") {
  auto status=box.status("delivery-test",65001,123456,0);
  assert(status.size()==11 && status.at("type")=="telemetry_status");
  for(const auto* field:{"issued_sequence","accepted_sequence","pending_frames","pending_bytes","overflow_frames","discarded_frames"}) {
   assert(status.at(field).is_number_integer() && status.at(field)==0);
  }
 } else if(scenario=="rebind") {
  sockets.closeReceiver();assert(box.publish(*sockets.channel,frame(1)) && box.pendingFrames()==1);
  sockets.bindReceiver();assert(box.flush(*sockets.channel)==0);
  box.beginTick();assert(box.flush(*sockets.channel)==1);
  assert((sequences(sockets.drain())==std::vector<uint64_t>{1}));
 } else if(scenario=="last_tail_status") {
  sockets.saturate();assert(box.publish(*sockets.channel,frame(220)));
  const auto pending=box.status("delivery-test",65001,123456,220);
  assert(pending.size()==11 && pending.at("type")=="telemetry_status");
  assert(pending.at("issued_sequence")==220 && pending.at("accepted_sequence")==0);
  assert(pending.at("pending_frames")==1 && pending.at("pending_bytes")==frame(220).dump().size());
  assert(pending.at("overflow_frames")==0 && pending.at("discarded_frames")==0);
  sockets.drain();assert(sockets.channel->send(pending));
  auto received=sockets.drain();assert(received.size()==1 && received[0]==pending);
  box.beginTick();assert(box.flush(*sockets.channel)==1);
  auto complete=box.status("delivery-test",65001,123457,220);
  assert(complete.at("accepted_sequence")==220 && complete.at("pending_frames")==0 && complete.at("pending_bytes")==0);
 } else if(scenario=="discard_sticky") {
  assert(box.enqueue(frame(1)) && box.enqueue(frame(2)));box.discard();
  assert(box.discardedFrames()==2 && box.pendingFrames()==0 && box.pendingBytes()==0);
  box.discard();assert(box.discardedFrames()==2);
  assert(box.publish(*sockets.channel,frame(3)) && box.discardedFrames()==2);
 } else if(scenario=="telemetry_only") {
  const Json hello={{"version",1},{"type","hello"},{"world","delivery-test"}};
  assert(!box.publish(*sockets.channel,hello) && box.pendingFrames()==0);
  assert(box.overflowFrames()==0 && box.discardedFrames()==0);
  assert(sockets.channel->send(hello));auto received=sockets.drain();assert(received.size()==1 && received[0]==hello);
 } else if(scenario=="per_session_budget") {
  std::array<botbrain::TelemetryOutbox,3> boxes;size_t attempts=0;
  for(size_t bot=0;bot<boxes.size();bot++) {
   for(uint64_t seq=1;seq<=3;seq++) assert(boxes[bot].enqueue(frame(seq,65001+bot)));
   boxes[bot].beginTick();attempts+=boxes[bot].flush(*sockets.channel);
   assert(boxes[bot].acceptedSequence()==2 && boxes[bot].pendingFrames()==1);
  }
  assert(attempts==6 && sockets.drain().size()==6);
 } else if(scenario=="native_publishers") {
#if HAS_NATIVE_OUTBOX
  const auto config=sockets.directory+"/config.json";
  Json configuration={{"mode","shadow"},{"bots",{65001}},{"socket_directory",sockets.directory}};
  std::ofstream(config)<<configuration.dump();sockets.channel.reset();
  setenv("CANARY_BRAIN_CONFIG",config.c_str(),1);
  {
   botbrain::Runtime runtime;sockets.closeReceiver();runtime.beginTelemetryTick();
   publishPeriodic(&runtime,65001,1000);publishDeath(&runtime,65001);
   auto& session=runtime.sessions.at(65001);
   assert(session.telemetrySequence==2 && session.deaths==1 && session.delivery.pendingFrames()==2);
   assert(session.delivery.acceptedSequence()==0);
   sockets.bindReceiver();runtime.beginTelemetryTick();finishTick(&runtime);
   auto packets=sockets.drain();assert(packets.size()==3);
   assert(packets[0].at("type")=="telemetry" && packets[0].at("sequence")==1 && packets[0].at("deaths")==0);
   assert(packets[1].at("type")=="telemetry" && packets[1].at("sequence")==2 && packets[1].at("deaths")==1);
   assert(packets[2].at("type")=="telemetry_status" && packets[2].at("accepted_sequence")==2 && packets[2].at("pending_frames")==0);
  }
  unsetenv("CANARY_BRAIN_CONFIG");
#else
  assert(false && "old native publishers do not retain either failed frame");
#endif
 } else if(scenario=="runtime_flush_status") {
#if HAS_NATIVE_OUTBOX
  const auto config=sockets.directory+"/config.json";
  Json configuration={{"mode","shadow"},{"bots",{65001,65002,65003}},{"socket_directory",sockets.directory}};
  std::ofstream(config)<<configuration.dump();
  sockets.channel.reset();setenv("CANARY_BRAIN_CONFIG",config.c_str(),1);
  {
   botbrain::Runtime runtime;
   for(const auto guid:runtime.roster) {
    auto& session=runtime.sessions[guid];session.telemetrySequence=1;
    assert(session.delivery.enqueue(botbrain::telemetry(runtime.world,guid,1,1000,0,"alive")));
   }
   runtime.beginTelemetryTick();
   const auto before=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();
   finishTick(&runtime);auto packets=sockets.drain();assert(packets.size()==6);
   for(size_t i=0;i<3;i++) {
    assert(packets[i].at("type")=="telemetry" && packets[i].at("bot_id")==65001+i);
    const auto found=std::find_if(packets.begin()+3,packets.end(),[&](const auto& packet){return packet.at("bot_id")==65001+i;});
    assert(found!=packets.end());const auto& status=*found;
    assert(status.at("type")=="telemetry_status");
    assert(status.at("issued_sequence")==1 && status.at("accepted_sequence")==1 && status.at("pending_frames")==0);
    assert(status.at("captured_ms").get<int64_t>()>=before);
   }
  }
  unsetenv("CANARY_BRAIN_CONFIG");
#else
  assert(false && "old Runtime has no bounded flush/status phase");
#endif
 } else if(scenario=="runtime_destructor" || scenario=="runtime_destructor_removed_roster") {
#if HAS_NATIVE_OUTBOX
  // A separate directory avoids binding a second publisher over the existing fixture.
  const auto config=sockets.directory+"/config.json";
  Json configuration={{"mode","shadow"},{"bots",{65001}},{"socket_directory",sockets.directory}};
  std::ofstream(config)<<configuration.dump();
  sockets.channel.reset();setenv("CANARY_BRAIN_CONFIG",config.c_str(),1);
  {
   botbrain::Runtime runtime;auto& session=runtime.sessions[65001];session.telemetrySequence=1;
   assert(session.delivery.enqueue(botbrain::telemetry(runtime.world,65001,1,1000,0,"alive")));
   if(scenario=="runtime_destructor_removed_roster") runtime.roster.clear();
  }
  unsetenv("CANARY_BRAIN_CONFIG");auto packets=sockets.drain();
  assert(packets.size()==1 && packets[0].at("type")=="telemetry_status");
  assert(packets[0].at("issued_sequence")==1 && packets[0].at("accepted_sequence")==0);
  assert(packets[0].at("pending_frames")==0 && packets[0].at("pending_bytes")==0 && packets[0].at("discarded_frames")==1);
#else
  assert(false && "old Runtime does not publish discarded-tail status");
#endif
 } else { assert(false); }
 std::cout<<"PASS: "<<scenario<<"\n";
}
"""
source = source.replace("@TICK_TAIL@", tick_tail)
source = source.replace("@PERIODIC_PUBLISH@", periodic_publish).replace(
    "@DEATH_PUBLISH@", death_publish
)

scenarios = (
    "fifo_pressure",
    "first_error_stops_tick",
    "shared_budget",
    "multiple_publish_budget",
    "frame_overflow",
    "byte_overflow",
    "immutable_frame",
    "initial_status",
    "rebind",
    "last_tail_status",
    "discard_sticky",
    "telemetry_only",
    "per_session_budget",
    "native_publishers",
    "runtime_flush_status",
    "runtime_destructor",
    "runtime_destructor_removed_roster",
)
if args.case:
    if args.case not in scenarios:
        raise SystemExit("unknown test case")
    scenarios = (args.case,)
with tempfile.TemporaryDirectory(prefix="brain-outbox-build-") as directory:
    temporary = Path(directory)
    (temporary / "delivery.cpp").write_text(source)
    subprocess.run(
        [
            "g++",
            "-std=c++20",
            "-O0",
            f"-DHAS_NATIVE_OUTBOX={int(native)}",
            "-I",
            str(include),
            "-I",
            str(root / "src"),
            str(temporary / "delivery.cpp"),
            "-o",
            str(temporary / "delivery"),
        ],
        check=True,
    )
    failures = []
    for scenario in scenarios:
        result = subprocess.run(
            [str(temporary / "delivery"), scenario, str(temporary / scenario)],
            check=False,
            cwd=temporary,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode:
            failures.append(scenario)
            print(f"FAIL: {scenario}: {result.stderr.strip()}")
        else:
            print(result.stdout.strip())
    if failures:
        raise SystemExit(f"Failed telemetry-delivery cases: {', '.join(failures)}")
