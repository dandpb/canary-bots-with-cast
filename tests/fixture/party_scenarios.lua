-- Only loaded through the private QA command adapter, never a normal datapack.
assert(configManager.getString(configKeys.SERVER_NAME)=="Canary party QA")
local q=PartyScenario or {kills={},damage={},deaths={},spawns={}}
local names={"Party Leader A","Party Leader B","Grizzle Alyronia","Sever Heartspear","Galdon Whitehoof"}
local death=CreatureEvent("PartyAcceptanceMonsterDeath")
function death.onDeath(creature,corpse,killer)
 q.kills[#q.kills+1]={id=creature:getId(),name=creature:getName(),at=Game.monotonicMs(),killer=killer and killer:getName() or "unknown"}
 return true
end
death:register()
local damage=CreatureEvent("PartyAcceptanceDamage")
function damage.onHealthChange(creature,attacker,primary,primaryType,secondary,secondaryType,origin)
 if attacker then q.damage[#q.damage+1]={target=creature:getId(),attacker=attacker:getName(),primary=primary,secondary=secondary,at=Game.monotonicMs()} end
 return primary,primaryType,secondary,secondaryType
end
damage:register()
local playerDeath=CreatureEvent("PartyAcceptancePlayerDeath")
function playerDeath.onDeath(creature)
 q.deaths[#q.deaths+1]={name=creature:getName(),at=Game.monotonicMs()};return true
end
playerDeath:register()
for _,name in ipairs(names) do assert(Player(name)):registerEvent("PartyAcceptancePlayerDeath") end

function q.snapshot()
 local players={}
 for _,name in ipairs(names) do
  local p=Player(name)
  if p then
   local pos=p:getPosition();local follow=p:getFollowCreature()
   players[#players+1]={name=name,guid=p:getGuid(),hp=p:getHealth(),hpmax=p:getMaxHealth(),xp=p:getExperience(),
    position={pos.x,pos.y,pos.z},health_potions=p:getItemCount(266),mana_potions=p:getItemCount(268),
    bank=p:getBankBalance(),money=p:getMoney(),follow=follow and follow:getName() or ""}
  else players[#players+1]={name=name,offline=true} end
 end
 return {players=players,kills=q.kills,damage=q.damage,deaths=q.deaths,spawns=q.spawns,native=PartyQA("inspect"),brain=Game.botCommand("_global","brain status")}
end

function q.cleanup()
 local removed={}
 for _,spawn in ipairs(q.spawns) do
  local monster=Monster(spawn.id)
  if monster then removed[#removed+1]=spawn.id;monster:remove() end
 end
 return removed
end
function q.reset()
 local removed=q.cleanup()
 q.kills={};q.damage={};q.deaths={};q.spawns={}
 return removed
end
function q.baseline()
 for _,name in ipairs(names) do
  local p=assert(Player(name));local xp=p:getExperience()
  if xp>98800 then p:removeExperience(xp-98800) elseif xp<98800 then p:addExperience(98800-xp) end
  p:addHealth(p:getMaxHealth()-p:getHealth());p:addMana(p:getMaxMana()-p:getMana())
  if p:getGuid()>=65000 then
   for _,id in ipairs({266,268}) do local n=p:getItemCount(id);if n>0 then assert(p:removeItem(id,n)) end;assert(p:addItem(id,20)) end
   p:setBankBalance(100000)
  end
 end
 return q.snapshot()
end

local function place(p,base,index)
 local target=Position(base.x+index,base.y,base.z)
 if p:getPosition()~=target then
  local moved=false
  for radius=0,3 do
   for dx=-radius,radius do for dy=-radius,radius do
    if not moved then
     local candidate=Position(target.x+dx,target.y+dy,target.z);local tile=Tile(candidate)
     if tile and not tile:getTopCreature() and tile:queryAdd(p)==RETURNVALUE_NOERROR then moved=p:teleportTo(candidate) end
    end
   end end
   if moved then break end
  end
  assert(moved,"fixture placement "..p:getName())
 end
 p:setFollowCreature(nil);p:setTarget(nil)
end
function q.placeHunt()
 for i,name in ipairs(names) do place(assert(Player(name)),Position(32366,32175,7),i-1) end
 -- Normal native following, without teleporting along the route.
 assert(Player(names[1]):setFollowCreature(Player(names[3])))
 assert(Player(names[2]):setFollowCreature(Player(names[1])))
 return q.snapshot()
end
function q.wave()
 local pos=assert(Player(names[3])):getPosition();local ids={}
 for _,offset in ipairs({{1,-1},{-1,-1},{2,0},{-2,0}}) do
  local monster=Game.createMonster("Wolf",Position(pos.x+offset[1],pos.y+offset[2],pos.z),true,false)
  if monster then
   monster:registerEvent("PartyAcceptanceMonsterDeath");monster:registerEvent("PartyAcceptanceDamage")
   local at=monster:getPosition()
   q.spawns[#q.spawns+1]={id=monster:getId(),name=monster:getName(),hp=monster:getHealth(),position={at.x,at.y,at.z}}
   ids[#ids+1]=monster:getId()
  end
 end
 assert(#ids>0,"walkable non-PZ combat fixture required")
 return ids
end
function q.placeSupply()
 -- The global NPC name lookup is ambiguous: this world contains duplicate
 -- Xodets on several floors. Start at the declared Thais rendezvous and let
 -- the production brainShop/route select and reach its actual local shop.
 for i,name in ipairs(names) do place(assert(Player(name)),Position(32366,32241,7),i-1) end
 for _,name in ipairs({names[3],names[4],names[5]}) do
  local p=assert(Player(name))
  for _,id in ipairs({266,268,236,237,238,239,7642,7643,23373,23374,23375}) do local n=p:getItemCount(id);if n>0 then assert(p:removeItem(id,n)) end end
  assert(p:addItem(266,1));assert(p:addItem(268,1));p:setBankBalance(100000)
 end
 return q.snapshot()
end
return q
