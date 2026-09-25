-- Read-only look at the Iron Court in a running game, through the wh3 bridge's
-- eval. Every read is pcall'd and the whole answer is one string, because one
-- error inside an eval wedges the bridge for the rest of the session.
local out = {}
local function put(k, v) out[#out + 1] = k .. "=" .. tostring(v) end
local function try(k, fn)
    local ok, v = pcall(fn)
    if ok then put(k, v) else put(k, "ERR " .. tostring(v)) end
end

-- IC_PROBE_ACTION, set by the sender ahead of this chunk: "open" opens the
-- court first, "close_x" clicks its X the way the player does. Read after.
local action = IC_PROBE_ACTION
IC_PROBE_ACTION = nil
if action == "open" then
    try("open", function() ICUI.open() return "called" end)
elseif action == "close_x" then
    try("click_x", function()
        local c = find_uicomponent(core:get_ui_root(), ICUI.PANEL, "ic_close")
        if not is_uicomponent(c) then return "no X" end
        c:SimulateLClick()
        return "clicked"
    end)
elseif action == "court" then
    try("click_court_tab", function()
        local c = find_uicomponent(core:get_ui_root(), ICUI.PANEL, "ic_tab_court")
        if not is_uicomponent(c) then return "no tab" end
        c:SimulateLClick()
        return "clicked"
    end)
elseif action == "choose" then
    -- The first RIVAL card on the page, clicked the way the player does.
    try("click_rival", function()
        local court = IC.court(ICUI.player())
        local keys, off = ICUI.court_keys or {}, (ICUI.scroll.court or 0)
        for i = off + 1, #keys do
            local slug = keys[i]
            if slug ~= IC.CROWN and court.houses[slug] ~= nil then
                local id = ICUI.PARTY .. "_" .. tostring(i - off)
                local c = find_uicomponent(core:get_ui_root(), ICUI.PANEL, id)
                if not is_uicomponent(c) then return "no card " .. id end
                c:SimulateLClick()
                return "clicked " .. id .. " (" .. tostring(slug) .. ")"
            end
        end
        return "no rival on the page"
    end)
end

try("strings_ok", function()
    return ("abc"):sub(2, 2) == "b" and ("xy"):find("y") == 2
end)
try("icui", function() return type(ICUI) end)
try("gift_label", function() return ICUI.ACT_LABEL.ic_act_gift end)
try("paged_xy", function() return type(ICUI.ACT_PAGED_XY) end)

local panel
try("panel_open", function()
    local c = find_uicomponent(core:get_ui_root(), ICUI.PANEL)
    if is_uicomponent(c) then panel = c end
    return panel ~= nil and panel:Visible()
end)
if panel then
    local function cell(name)
        local c = find_uicomponent(panel, name)
        if not is_uicomponent(c) then return "absent" end
        local x, y = c:Position()
        local w, h = c:Dimensions()
        return string.format("%s|vis=%s|%d,%d,%dx%d", tostring(c:GetStateText()),
            tostring(c:Visible()), x, y, w, h)
    end
    for _, n in ipairs({"ic_influence", "ic_tab_court", "ic_tab_govs",
                        "ic_tab_petitions", "ic_act_provoke", "ic_act_gift",
                        "ic_act_secure", "ic_act_purge", "ic_act_hint", "ic_close"}) do
        try(n, function() return cell(n) end)
    end
    try("sel", function() return ICUI.sel end)
    try("notice", function() return ICUI.notice end)
    try("view", function() return ICUI.view end)
end
try("strings_ok_after", function()
    return ("abc"):sub(2, 2) == "b" and ("xy"):find("y") == 2
end)
return table.concat(out, " ; ")
