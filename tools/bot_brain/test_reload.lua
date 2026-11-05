-- Lua orchestration preserves the authoritative native handoff and live cache.
Position = function(x,y,z) return {x=x,y=y,z=z} end
local errors, commands, ticks = {}, {}, 0
logger = {info=function() end,warn=function() end,error=function(message) errors[#errors+1]=message end}
db = {query=function() return true end,storeQuery=function() return false end}
addEvent = function(callback) callback() end
local function actor(guid, removed, bot)
 return {getGuid=function() return guid end,getName=function() return "Companion" end,
  isRemoved=function() return removed end,isBotPlayer=function() return bot end}
end
local current, stale, pooled, human = actor(51,false,true), actor(51,true,true), actor(52,true,true), actor(9,false,false)
Game = {
 botPrepareReload=function() return {ok=true,ticket=1,native_handoff=true} end,
 botCancelReload=function() error("successful handoff must not be cancelled") end,
 botReload=function(ticket)
  assert(ticket==1)
  return {ok=true,state_restored=true,message="Restored",bots={
   {guid=51,name="Companion",active=true,hibernated=false},
   {guid=52,name="Pooled",active=true,hibernated=true}}}
 end,
 botCommand=function(_,command) commands[#commands+1]=command; return "Scheduler: OFF" end,
 botStartTickLoop=function() ticks=ticks+1;return true end,
 getPlayers=function() return {current,human} end,
 botIsActive=function() error("normal handoff must preserve native activation state") end,
 loadBotPlayer=function() error("registered Players must not reload from DB") end,
 botForceDeactivateForReload=function() error("Lua must not deactivate before native capture") end,
 botReregisterAll=function() error("native handoff already restored registrations") end,
}
Player = function() return nil end
dofile(arg[1] or "data/scripts/lib/bot_system.lua")
BotPlayers[51],BotPlayers[52]=stale,pooled
local result=BotSystem.executeReload({source="test"})
assert(result.ok and not result.pending, result.message)
assert(#errors==0,table.concat(errors,";"))
assert(BotPlayers[51]==current and BotPlayers[52]==pooled)
assert(BotPlayers[9]==nil and BotActive[51] and BotActive[52])
assert(ticks==1 and not BotSystem._reloadInProgress)
assert(commands[#commands]=="schedule off")
print("PASS: native handoff preserves awake/pooled state and refreshes the live cache")
