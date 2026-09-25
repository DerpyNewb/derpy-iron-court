-- Step-level probe of ICUI.draw_actions (deployed build 7ef8f281). Runs the
-- deployed body line for line with a string-library check after every engine
-- call, then opens the court. Trace to derpy_ic_trace2.txt, io only.
local f = io.open("derpy_ic_trace2.txt", "w")
local function log(s) f:write(s, "\n"); f:flush() end
local function healthy()
    local a, b = pcall(function()
        return ("abc"):sub(2, 2) == "b" and ("xy"):find("y") == 2
    end)
    return (a and b) and true or false
end
local first = nil
local function step(label)
    local h = healthy()
    log((h and "ok    " or "BROKEN") .. " " .. label)
    if not h and not first then first = label end
end
local function comp(name, parent)
    local c = find_uicomponent(parent or core:get_ui_root(), name)
    if is_uicomponent(c) then return c end
    return nil
end
local function set_text(c, text)
    if not c then return end
    pcall(function() c:SetText(tostring(text), "") end)
end
local function where(c)
    local x, y, w, h = "?", "?", "?", "?"
    pcall(function() x, y = c:Position() end)
    pcall(function() w, h = c:Dimensions() end)
    return x .. "," .. y .. " " .. w .. "x" .. h
end

log("start healthy=" .. tostring(healthy()))
if not healthy() then f:close(); return "already broken before the probe" end
if ICUI.PANEL and find_uicomponent(core:get_ui_root(), ICUI.PANEL) then
    pcall(ICUI.close)
end

local original = ICUI.draw_actions
ICUI.draw_actions = function(panel, faction, court, px, py)
    step("enter px=" .. tostring(px) .. " (" .. type(px) .. ") py=" .. tostring(py)
         .. " panel=" .. tostring(panel))
    local slug = ICUI.sel
    local rival = slug and slug ~= IC.CROWN and court.houses[slug] ~= nil
    step("rival=" .. tostring(rival))
    local nxt = comp("ic_page_next", panel)
    step("comp ic_page_next -> " .. tostring(nxt))
    local paged = nxt ~= nil and nxt:Visible()
    step("Visible -> " .. tostring(paged))
    for _, key in ipairs({"ic_act_provoke", "ic_act_secure", "ic_act_purge",
                          "ic_act_hint"}) do
        local c = comp(key, panel)
        step("comp " .. key .. " -> " .. tostring(c))
        local home = paged and ICUI.ACT_PAGED_XY[key] or ICUI.PANEL_XY[key]
        if c and home then
            log("       before " .. where(c) .. " target " .. (px + home[1]) .. ","
                .. (py + home[2]) .. " " .. home[3] .. "x" .. home[4])
            c:MoveTo(px + home[1], py + home[2])
            step("MoveTo " .. key .. " now " .. where(c))
            ICUI.resize(c, home[3], home[4])
            step("resize " .. key .. " now " .. where(c))
        end
    end
    for _, key in ipairs(ICUI.ACT_KEYS) do
        local c = comp(key, panel)
        step("loop2 comp " .. key .. " -> " .. tostring(c))
        if c then
            c:SetVisible(rival)
            step("SetVisible " .. key)
        end
    end
    local hint = comp("ic_act_hint", panel)
    step("comp ic_act_hint -> " .. tostring(hint))
    set_text(hint, slug == IC.CROWN and ICUI.ACT_HINT[2] or ICUI.ACT_HINT[1])
    step("SetText hint")
    if hint then hint:SetVisible(not rival) end
    step("SetVisible hint")
end

local ok, err = pcall(ICUI.open)
ICUI.draw_actions = original
log("open ok=" .. tostring(ok) .. " err=" .. tostring(err) .. " first=" .. tostring(first))
f:close()
return first or "no break"
