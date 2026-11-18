-- Loaded as otclientrc.lua only in a fresh, private playback profile.
local mode = g_app.getStartupOptions():match("%s%-%-bot%-replay=(%a+)%f[%s%z]")
if mode ~= "watch" and mode ~= "frames" then
  return
end

if not g_app.getStartupOptions():find("%s%-%-user%-dir=") then
  error("Replay requires an explicit private --user-dir")
end

local started, captureEvent, mapSeen
local function capture()
  if not g_game.isOnline() then
    return
  end
  local elapsed = g_clock.millis() - started
  if elapsed > lastPacketMs then
    return
  end
  g_app.doScreenshot(string.format("/frames/frame-%07d.png", elapsed))
  captureEvent = scheduleEvent(capture, 125)
end

if mode == "frames" then
  if g_resources.directoryExists("/frames") or not g_resources.makeDir("/frames") then
    error("Replay frames require a new empty profile")
  end
  if not g_resources.writeFileContents("/frames/tape-sha256.txt", tapeSha) then
    error("Unable to bind the output frames to the game tape")
  end
  connect(g_game, {
    onMapKnown = function()
      if started and not mapSeen then
        mapSeen = true
        captureEvent = scheduleEvent(capture, 100)
      end
    end,
    onGameEnd = function()
      if captureEvent then
        removeEvent(captureEvent)
      end
    end,
  })
end

scheduleEvent(function()
  if g_game.isOnline() then
    error("Close the live game before opening a replay")
  end
  g_game.setClientVersion(1500)
  g_game.setProtocolVersion(g_game.getClientProtocolVersion(1500))
  if not modules.game_things.isLoaded() then
    error("Replay requires OTClient assets for protocol 1500")
  end
  started = g_clock.millis()
  g_game.playRecord("game.cam")
end, 100)
