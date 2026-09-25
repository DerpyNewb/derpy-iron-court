-- Finds which Iron Court function breaks the game's string library.
-- Wraps every function in ICUI and IC with a tripwire, opens the court once,
-- and names the innermost wrapped function that returned with strings broken.
-- Writes to derpy_ic_trace.txt with io only: the bridge's own JSON reply is
-- built on string.sub and dies with it.
local f = io.open("derpy_ic_trace.txt", "w")
local function log(s) f:write(s, "\n"); f:flush() end
local function healthy()
    local a, b = pcall(function()
        return ("abc"):sub(2, 2) == "b" and ("xy"):find("y") == 2
    end)
    return (a and b) and true or false
end
log("start healthy=" .. tostring(healthy()))
if not healthy() then f:close(); return "already broken before the probe" end
if not ICUI or not IC then f:close(); return "ICUI or IC not reachable" end
if ICUI.PANEL and find_uicomponent(core:get_ui_root(), ICUI.PANEL) then
    pcall(ICUI.close)
end

local saved, broke, depth, calls = {}, nil, 0, 0
local function pack(...) return {n = select("#", ...), ...} end
local function wrap(tname, t)
    for k, v in pairs(t) do
        if type(v) == "function" then
            saved[#saved + 1] = {t, k, v}
            local name = tname .. "." .. tostring(k)
            t[k] = function(...)
                if broke then return v(...) end
                calls = calls + 1
                depth = depth + 1
                local was = healthy()
                if depth <= 4 then log(depth .. " > " .. name) end
                local r = pack(pcall(v, ...))
                depth = depth - 1
                if not broke and was and not healthy() then
                    broke = name
                    log("BROKE inside " .. name .. " (depth " .. (depth + 1) .. ")")
                end
                if not r[1] then error(r[2], 0) end
                return unpack(r, 2, r.n)
            end
        end
    end
end
wrap("ICUI", ICUI)
wrap("IC", IC)
log("wrapped " .. #saved .. " functions")

local ok, err = pcall(ICUI.open)
log("open ok=" .. tostring(ok) .. " err=" .. tostring(err))

for i = 1, #saved do saved[i][1][saved[i][2]] = saved[i][3] end
log("restored; calls=" .. calls .. " end healthy=" .. tostring(healthy())
    .. " broke=" .. tostring(broke))
f:close()
return broke or "no break"
