-- THE IRON COURT'S PARTY MAP (docs/superpowers/specs/2026-09-29-iron-court-party-map-design.md).
--
-- CA's Gardens of Morr technique: a marker per province, pinned to its settlement
-- by ContextWorldSpaceComponent on CcoCampaignSettlement.Position, laid over the
-- LIVE campaign map. Loads after zzz_derpy_iron_court_ui.lua and calls into it.
if not ICUI or not ICUI.comp then return end
local comp, set_text, loc, root = ICUI.comp, ICUI.set_text, ICUI.loc, ICUI.root

-- The layer is named for its file's root, as the court's panel is.
ICUI.MAP = "derpy_ic_map"
ICUI.PATH_MAP = "ui/campaign ui/derpy_ic_map"
ICUI.PATH_MARKER = "ui/campaign ui/derpy_ic_map_marker"
ICUI.MARKER = "ic_map_mk"
ICUI.MAP_TAB = "ic_tab_map"
-- The marker's layers. Must match MARKER_LAYERS in tools/gen_ic_ui.py (check_map).
ICUI.MK_PLATE, ICUI.MK_CREST, ICUI.MK_CAPITAL, ICUI.MK_OUTLINE = 0, 1, 2, 3
ICUI.MK_RING_CAPITAL = "ui/derpy_ic/map_ring_capital.png"
ICUI.MK_RING_OUTLINE = "ui/derpy_ic/map_ring_outline.png"
-- THE LEGEND. Must match MAP_LAYOUT / MAP_ROW_* / MAP_ROW_CHILD (check_map).
ICUI.MAP_XY = {
    ic_map_legend = {16, 16, 455, 556},
    ic_map_title  = {32, 26, 360, 30},
    ic_map_close  = {411, 20, 48, 48},
    ic_map_prev   = {24, 470, 136, 34},
    ic_map_page   = {164, 474, 159, 26},
    ic_map_next   = {327, 470, 136, 34},
    ic_map_hint_1 = {32, 512, 423, 24},
    ic_map_hint_2 = {32, 536, 423, 24},
}
ICUI.MAP_ROW = "ic_map_row"
ICUI.MAP_ROW_X, ICUI.MAP_ROW_Y, ICUI.MAP_ROW_W, ICUI.MAP_ROW_H, ICUI.MAP_ROWS = 24, 76, 439, 56, 7
ICUI.MAP_ROW_CHILD = {
    ic_map_sw   = {8, 8, 36, 36},
    ic_map_name = {56, 2, 375, 24},
    ic_map_gov  = {56, 28, 170, 22},
    ic_map_take = {232, 28, 200, 22},
}
ICUI.MAP_ROW_SEL = 0          -- the row's chosen frame
ICUI.map_keys = {}            -- marker index -> province key, as last drawn
-- NEVER SCALED (plan ruling 7): the map has no compact copy, and a legend of
-- 455px fits every screen. Declared so the scale pass's classification knows.
for _, n in ipairs({"MK_PLATE", "MK_CREST", "MK_CAPITAL", "MK_OUTLINE", "MAP_XY",
                    "MAP_ROW_X", "MAP_ROW_Y", "MAP_ROW_W", "MAP_ROW_H", "MAP_ROWS",
                    "MAP_ROW_CHILD", "MAP_ROW_SEL"}) do
    ICUI.NOT_SCALED[#ICUI.NOT_SCALED + 1] = n
end

function ICUI.map_disc(slug)
    -- "" is truthy in Lua: see ICUI.plate_path.
    if not slug or slug == "" then slug = "none" end
    return "ui/derpy_ic/map_disc_" .. slug .. ".png"
end

-- THE SETTLEMENT A PROVINCE'S MARKER STANDS ON: the province capital if you hold
-- it, else the first region you hold there. IC.held_region keeps its own choice -
-- the governor bundles use it, and a faction-province bundle does not care.
function ICUI.map_region(faction_key, province_key)
    local first, capital = nil, nil
    pcall(function()
        local f = cm:get_faction(faction_key)
        if not f then return end
        local list = f:region_list()
        for i = 0, list:num_items() - 1 do
            local r = list:item_at(i)
            if r and not r:is_null_interface() and r:province():key() == province_key then
                first = first or r
                if not capital and r:is_province_capital() then capital = r end
            end
        end
    end)
    return capital or first
end

function ICUI.map_layout(layer)
    for name, box in pairs(ICUI.MAP_XY) do
        local c = comp(name, layer)
        if c then c:MoveTo(box[1], box[2]) end
    end
    for i = 1, ICUI.MAP_ROWS do
        local row = comp(ICUI.MAP_ROW .. "_" .. i, layer)
        if row then
            local x = ICUI.MAP_ROW_X
            local y = ICUI.MAP_ROW_Y + (i - 1) * ICUI.MAP_ROW_H
            row:MoveTo(x, y)
            for name, box in pairs(ICUI.MAP_ROW_CHILD) do
                local c = comp(name, row)
                if c then c:MoveTo(x + box[1], y + box[2]) end
            end
            row:SetVisible(false)
        end
    end
end

function ICUI.map_draw(faction_key, layer)
    set_text(comp("ic_map_title", layer), "The realm - who governs where")
    local capital = IC.capital_province(faction_key)
    ICUI.map_keys = {}
    for i, province in ipairs(IC.seats(faction_key)) do
        local region = ICUI.map_region(faction_key, province)
        local cqi = nil
        if region then pcall(function() cqi = region:settlement():cqi() end) end
        if cqi then
            local name = ICUI.MARKER .. "_" .. i
            layer:CreateComponent(name, ICUI.PATH_MARKER)
            local m = comp(name, layer)
            if m then
                -- THE ID FORM FORTIFIED CAMPS ATTESTS: the settlement's cqi.
                m:SetContextObject(cco("CcoCampaignSettlement", cqi))
                local slug = IC.province_party(faction_key, province)
                m:SetImagePath(ICUI.map_disc(slug), ICUI.MK_PLATE)
                m:SetImagePath(slug and ICUI.crest(slug) or ICUI.MASK_NONE, ICUI.MK_CREST)
                m:SetImagePath(province == capital and ICUI.MK_RING_CAPITAL
                               or ICUI.MASK_NONE, ICUI.MK_CAPITAL)
                m:SetImagePath(ICUI.MASK_NONE, ICUI.MK_OUTLINE)
                -- ITS OWN TEXT: a marker has no children (ruling 9).
                set_text(m, loc("provinces_onscreen_" .. province, province))
                ICUI.map_keys[i] = province
            end
        end
    end
end

function ICUI.map_close()
    local layer = comp(ICUI.MAP)
    if layer then pcall(function() layer:DestroyChildren() layer:Destroy() end) end
    ICUI.map_keys = {}
    ICUI.show_hud(true)
end

function ICUI.map_open()
    local faction = ICUI.player()
    if not faction then return end
    -- NEVER OVER THE COURT: close() gives the HUD back, so the hide below is
    -- the only one on record. Two hides in a row would lose the first's record.
    -- AND ONE LAYER, EVER: a second open replaces the first.
    if comp(ICUI.PANEL) then ICUI.close(true) end
    if comp(ICUI.MAP) then ICUI.map_close() end
    -- THE HUD FIRST (ruling 8): show_hud hides every visible root child but the
    -- court, and a layer created before it would hide itself.
    ICUI.show_hud(false)
    local ok, err = pcall(function()
        root():CreateComponent(ICUI.MAP, ICUI.PATH_MAP)
        local layer = comp(ICUI.MAP)
        if not layer then error("CreateComponent made no map layer") end
        layer:MoveTo(0, 0)
        -- THE SCREEN'S SIZE, not the file's 1920x1080: CA's Gardens root is a
        -- ScreenSizedComponent, and markers are this layer's children. Through
        -- ICUI.resize, whose `false` keeps CA's default of scaling the children
        -- with it off the legend.
        ICUI.resize(layer, root():Dimensions())
        ICUI.map_layout(layer)
        ICUI.map_draw(faction, layer)
    end)
    if not ok then
        -- map_close gives the HUD back: a map that failed is not a blank screen.
        ICUI.map_close()
        IC.warn("IRON COURT: the party map failed to open: " .. tostring(err))
    end
end

-- THE LISTENERS, registered with the court's (ruling 10): the panel file calls
-- ICUI.register from its first tick, and this wraps it.
function ICUI.map_register()
    core:add_listener("ic_map_click", "ComponentLClickUp", true, function(context)
        local id = context.string
        if id == ICUI.MAP_TAB then
            ICUI.map_open()             -- which closes the court
        elseif id == "ic_map_close" then
            ICUI.map_close()
            ICUI.view = "govs"
            ICUI.open()
        end
    end, true)
end

local court_register = ICUI.register
function ICUI.register()
    court_register()
    ICUI.map_register()
end
