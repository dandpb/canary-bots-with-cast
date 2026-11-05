-- Retain registered identities without a current avatar; repair only explicit missing rows.
Position=function(x,y,z) return {x=x,y=y,z=z} end
local failures={}
logger={info=function() end,warn=function() end,error=function(message) failures[#failures+1]=message end}
addEvent=function(callback) callback() end
local registered={[51]=true,[53]=true,[54]=true,[56]=true}
local active={[51]=true,[53]=true,[56]=true}
local names={[51]="Awake Companion",[53]="Respawning Companion",[54]="Inactive Companion",[55]="Missing Canonical",[56]="Uncached Companion"}
local world,loads={},{}
local function actor(guid)
 return {getGuid=function() return guid end,getName=function() return names[guid] end,
 isRemoved=function() return false end,isBotPlayer=function() return true end}
end
world[51],world[56]=actor(51),actor(56)
Player=function(name) for guid,p in pairs(world) do if names[guid]==name then return p end end end
local rows={51,53,54,55,56}
db={query=function() return true end,storeQuery=function() return {index=1} end}
result={getNumber=function(c) return rows[c.index] end,getString=function(c) return names[rows[c.index]] end,
 next=function(c) c.index=c.index+1;return rows[c.index]~=nil end,free=function() end}
Game={
 botPrepareReload=function() return {ok=true,ticket=7,native_handoff=true} end,
 botCancelReload=function() end,
 botReload=function()
  local roster={}
  for guid in pairs(registered) do roster[#roster+1]={guid=guid,name=names[guid],active=active[guid]==true,hibernated=false} end
  return {ok=true,state_restored=true,message="Native restored",bots=roster}
 end,
 botCommand=function() return "Scheduler: OFF" end,
 botStartTickLoop=function() return true end,
 botGetState=function(guid) return registered[guid] and 1 or -1 end,
 botIsActive=function(guid) return active[guid]==true end,
 botActivate=function(guid) assert(registered[guid]);active[guid]=true;return true end,
 getPlayers=function() local list={};for _,p in pairs(world) do list[#list+1]=p end;return list end,
 loadBotPlayer=function(name)
  local guid
  for id,n in pairs(names) do if n==name then guid=id end end
  assert(guid)
  loads[guid]=(loads[guid] or 0)+1
  if guid==55 and loads[guid]==1 then return nil end
  registered[guid]=true;world[guid]=actor(guid);return world[guid]
 end,
}
dofile(arg[1] or "data/scripts/lib/bot_system.lua")
local first=BotSystem.executeReload({source="test"})
assert(first.ok and #failures==0,first.message)
assert(registered[53] and active[53] and world[53]==nil,"native identity between avatars was lost")
assert(not active[54] and not registered[55],"normal reload must not alter the roster")
assert(next(loads)==nil,"normal handoff performed an unnecessary DB materialization")
assert(BotPlayers[56]==world[56],"uncached awake reference was lost")
local repaired=BotSystem.executeReload({source="repair",debugCount="off"})
assert(repaired.ok and not BotSystem._reloadInProgress,repaired.message)
assert(registered[55] and active[55] and loads[55]==2,"explicit canonical repair must retry")
assert(active[54],"debug off must restore inactive registrations")
-- Refreshing the helper definitions must keep runtime tables and strong references.
local runtimeNames={"BOT_CONFIG","BotPlayers","BotState","BotActive","BotDebugPinned","BotSystem"}
local preserved={};for _,name in ipairs(runtimeNames) do preserved[name]=_G[name] end
BOT_CONFIG.DEBUG_MODE=true;BotDebugPinned[51]=true
BotState[51]={fixturePhase="walking"};local fixture=BotState[51]
dofile(arg[1] or "data/scripts/lib/bot_system.lua")
for _,name in ipairs(runtimeNames) do assert(_G[name]==preserved[name],"helper refresh replaced "..name) end
assert(BOT_CONFIG.DEBUG_MODE and BotDebugPinned[51] and BotState[51]==fixture and BotPlayers[51]==world[51])
print("PASS: missing-avatar identities, explicit repair and helper refresh preserve state")
