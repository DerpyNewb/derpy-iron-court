-- THE IRON COURT'S GOVERNORS MAP (docs/superpowers/specs/2026-09-30-iron-court-
-- governors-map-design.md).
--
-- On the Governors tab the court clears its backdrop over the LIVE campaign map:
-- a pin and a face per province, pinned to its settlement by CA's own
-- ContextWorldSpaceComponent, and a Chaos Dwarf column of Parties, Provinces
-- and the governor picker on the left. Loads after zzz_derpy_iron_court_ui.lua
-- and wraps it.
if not ICUI or not ICUI.comp then return end
local comp, set_text, loc, root, show = ICUI.comp, ICUI.set_text, ICUI.loc, ICUI.root, ICUI.show

-- THE CAPITAL AND OUTLINE RINGS the pins wear, from the party map this replaced.
ICUI.MK_RING_CAPITAL = "ui/derpy_ic/map_ring_capital.png"
ICUI.MK_RING_OUTLINE = "ui/derpy_ic/map_ring_outline.png"

-- THE SETTLEMENT A PROVINCE'S PIN STANDS ON: the province capital if you hold
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

-- THE LEGEND'S ROWS: the court's parties in its own order, then "No governor".
function ICUI.map_rows(faction_key)
    local rows = {}
    for _, slug in ipairs(IC.present_houses(faction_key)) do rows[#rows + 1] = {slug = slug} end
    rows[#rows + 1] = {slug = nil}
    return rows
end

-- WHAT A LEGEND ROW RINGS, and why it rings nothing when it can ring nothing.
function ICUI.map_outline(faction_key, slug)
    if slug == nil then
        local out = {}
        local govs = IC.court(faction_key).govs
        for _, p in ipairs(IC.seats(faction_key)) do
            if not govs[p] then out[#out + 1] = p end
        end
        return out, nil
    end
    if slug == IC.CROWN then return {}, "Your own party cannot secede." end
    if not IC.secession_on() then
        local left = IC.grace_left()
        if IC.TUNE.secession ~= false and left > 0 then
            return {}, string.format("Parties cannot leave for %d more turn%s.",
                                     left, left == 1 and "" or "s")
        end
        return {}, "Secession is switched off. Parties cannot leave."
    end
    return IC.defecting_provinces(faction_key, slug) or {}, nil
end

-- WHAT THE TIPS SHARE, asked once a refresh: the parties each province would go
-- with, each party's share and the settlement levels. The first two walk the
-- whole court (IC.share -> every man's party); asked per pin and per row they
-- froze a mid-game realm for seconds a click.
function ICUI.map_memo(faction_key)
    local memo = {goes = {}, share = {}, levels = IC.province_levels(faction_key)}
    if IC.secession_on() then
        for _, slug in ipairs(IC.present_houses(faction_key)) do
            if slug ~= IC.CROWN then
                for _, p in ipairs(IC.defecting_provinces(faction_key, slug) or {}) do
                    memo.goes[p] = memo.goes[p] or {}
                    table.insert(memo.goes[p], slug)
                end
            end
        end
    end
    return memo
end

function ICUI.map_tip(faction_key, province, row, memo)
    memo = memo or ICUI.map_memo(faction_key)
    local court = IC.court(faction_key)
    local lines = {loc("provinces_onscreen_" .. province, province)}
    local cqi = court.govs[province]
    local man = cqi and IC.character_by_cqi(faction_key, cqi) or nil
    if man then
        local rank = 0
        pcall(function() rank = man:rank() end)
        lines[#lines + 1] = string.format("Governor: %s, rank %d", ICUI.character_name(man), rank)
        local slug = IC.house_of_cqi(faction_key, cqi)
        if slug then
            -- WHAT THIS PROVINCE ADDS TO HIS PARTY: what it adds NOW, since a governorship is earned a step a turn
            -- (IC.grow_governors), and what it grows to while it is.
            local all = memo.levels
            local levels = all[province] or 0
            local now, worth = IC.gov_grown_weight(court, province, all), IC.gov_weight_of(levels)
            if memo.share[slug] == nil then memo.share[slug] = IC.share(faction_key, slug) end
            lines[#lines + 1] = string.format(
                "%s: +%d strength from this province (%d settlement level%s%s), %d%% of the court",
                ICUI.house_name(slug, faction_key), now, levels, levels == 1 and "" or "s",
                now < worth and string.format(", growing to +%d", worth) or "",
                math.floor(memo.share[slug] + 0.5))
        end
    else
        lines[#lines + 1] = "No governor"
    end
    lines[#lines + 1] = string.format("Loyalty: %d", IC.province_loyalty(faction_key, province))
    for _, slug in ipairs(memo.goes[province] or {}) do
        lines[#lines + 1] = string.format("Would leave with %s.",
                                          ICUI.house_name(slug, faction_key))
    end
    -- A ROW CHOOSES; A PIN APPOINTS.
    if row then lines[#lines + 1] = "Click to choose this province."
    else lines[#lines + 1] = man and "Click to replace its governor." or "Click to choose its governor." end
    return table.concat(lines, "\n")
end

-- A SELECTION LEAVES THE MAP: the player saw something and went to act on it.
local function leave_on_select()
    -- THE GOVERNORS VIEW IS SEE-THROUGH, so a click through it can select what
    -- stands under it: leave the player on what they clicked.
    if ICUI.gm_on() then ICUI.close() end
end

-- THE LISTENERS, registered with the court's: the panel file calls
-- ICUI.register from its first tick, and this wraps it.
function ICUI.map_register()
    ICUI.on_map_click = function(context)
        local id = context.string
        if string.match(id or "", "^" .. ICUI.GM_PIN .. "_%d+$") and comp(ICUI.PANEL) then
            ICUI.gm_pin_click(tonumber(string.match(id, "_(%d+)$")))
        elseif ICUI.GM_TOGS[id] and comp(ICUI.PANEL) then
            ICUI.gm_to_page(ICUI.GM_TOGS[id])
        elseif string.match(id or "", "^" .. ICUI.GM_ROW .. "_%d+$") and comp(ICUI.PANEL) then
            ICUI.gm_row_click(tonumber(string.match(id, "_(%d+)$")))
        elseif string.match(id or "", "^ic_gm_sort_%d$") and comp(ICUI.PANEL) then
            ICUI.gm_sort_click(tonumber(string.match(id, "(%d)$")))
        elseif id == "ic_gm_ok" and comp(ICUI.PANEL) then
            ICUI.gm_ok()
        elseif id == "ic_gm_no" and comp(ICUI.PANEL) then
            ICUI.gm_no()
        end
    end
    core:add_listener("ic_map_click", "ComponentLClickUp", true, function(context)
        local ok, err = pcall(ICUI.on_map_click, context)
        if not ok then ICUI.click_failed(context.string, err) end
    end, true)
    core:add_listener("ic_map_char_selected", "CharacterSelected", true,
                      leave_on_select, true)
    core:add_listener("ic_map_settlement_selected", "SettlementSelected", true,
                      leave_on_select, true)
    -- AND THE OTHER VIEWS' LIST (ICUI.list_build), on the same frame tick.
    cm:repeat_real_callback(function()
        pcall(ICUI.gm_scroll_poll)
        pcall(ICUI.list_scroll_poll)
    end, ICUI.GM_SCROLL_MS, "ic_gm_scroll")
    cm:repeat_real_callback(function() pcall(ICUI.gm_zoom_poll) end,
                            ICUI.GM_ZOOM_MS, "ic_gm_zoom")
end

-- THE GOVERNORS VIEW ON THE LIVE MAP. On the Governors tab the court's backdrop
-- clears, the panel lets the map have the mouse, and each held province gets a
-- PIN, a FACE, a party BADGE and two PLATES (the name and the loyalty): five
-- siblings on one settlement context, each anchored at its box's bottom centre,
-- made in the panel's first child so they draw under everything the panel file
-- declares.
ICUI.PATH_GM_PIN = "ui/campaign ui/derpy_ic_gm_pin"
ICUI.PATH_GM_FACE = "ui/campaign ui/derpy_ic_gm_face"
ICUI.PATH_GM_NAME = "ui/campaign ui/derpy_ic_gm_name"
ICUI.PATH_GM_LOYAL = "ui/campaign ui/derpy_ic_gm_loyal"
ICUI.PATH_GM_BADGE = "ui/campaign ui/derpy_ic_gm_badge"
ICUI.GM_PINS = "ic_gm_pins"
ICUI.GM_PIN = "ic_gm_pin"
ICUI.GM_FACE = "ic_gm_face"
ICUI.GM_NAME = "ic_gm_name"
ICUI.GM_LOYAL = "ic_gm_loyal"
ICUI.GM_BADGE = "ic_gm_badge"
-- Must match GM_PIN_W/H, GM_NAME_H, GM_LOYAL_W/H and the layer lists in
-- tools/gen_ic_ui.py (check_gm).
ICUI.GM_PIN_W, ICUI.GM_PIN_H = 180, 146
ICUI.GM_NAME_H = 94
ICUI.GM_LOYAL_W, ICUI.GM_LOYAL_H = 113, 30
-- THE PLATE'S INSIDE, between its two caps: a name is cut to this, not to its
-- box. Must match GM_NAME_W in tools/gen_ic_ui.py.
ICUI.GM_NAME_W = 156
ICUI.GP_ART, ICUI.GP_PARTY, ICUI.GP_CAPITAL, ICUI.GP_OUTLINE = 0, 1, 2, 3
ICUI.GF_PORT, ICUI.GF_CREST = 1, 2
ICUI.GN_PLATE, ICUI.GN_WASH = 0, 1
-- THE GOVERNOR'S PARTY FLAG on the head. Must match GM_BADGE_LAYERS.
ICUI.GB_CREST = 0
-- THE THRONE ROOM, put back on every other view. Must be PANEL_BG (check_gm).
ICUI.GM_BACKDROP = "ui/derpy_ic/panel_bg.png"
ICUI.gm_keys = {}            -- pin index -> province key, as last drawn
for _, n in ipairs({"GM_PIN_W", "GM_PIN_H", "GM_NAME_H", "GM_LOYAL_W", "GM_LOYAL_H",
                    "GM_NAME_W", "GP_ART", "GP_PARTY", "GP_CAPITAL", "GP_OUTLINE",
                    "GF_PORT", "GF_CREST", "GN_PLATE", "GN_WASH", "GB_CREST"}) do
    ICUI.NOT_SCALED[#ICUI.NOT_SCALED + 1] = n
end

-- A PARTY'S RING, or none: "" is truthy in Lua (see ICUI.plate_path).
function ICUI.gm_ring_path(slug)
    if not slug or slug == "" then return ICUI.MASK_NONE end
    return "ui/derpy_ic/gm_ring_" .. slug .. ".png"
end

-- A PARTY'S COLOUR ACROSS THE NAME PLATE'S FACE, or none.
function ICUI.gm_wash_path(slug)
    if not slug or slug == "" then return ICUI.MASK_NONE end
    return "ui/derpy_ic/gm_wash_" .. slug .. ".png"
end

-- THE VIEW IS UP: the court open on its Governors tab.
function ICUI.gm_on()
    -- EVERY OTHER PICKER opens from the Court or Intrigue tabs, and a tab
    -- clears ICUI.pick: on this view a picker is always the governor's, and it
    -- is drawn in the column.
    return (comp(ICUI.PANEL) and ICUI.view == "govs") and true or false
end

-- ONE PROVINCE'S PIN, FACE, PLATES AND BADGE, by the names gm_draw_pins makes
-- them in that order: the badge after the face, so it draws over its edge.
local function gm_names(i)
    return {ICUI.GM_PIN .. "_" .. i, ICUI.GM_FACE .. "_" .. i,
            ICUI.GM_NAME .. "_" .. i, ICUI.GM_LOYAL .. "_" .. i,
            ICUI.GM_BADGE .. "_" .. i}
end

-- ONE PROVINCE'S FIVE OFF THE HOLDER.
local function drop_pair(pins, i)
    for _, name in ipairs(gm_names(i)) do
        local c = comp(name, pins)
        if c then pcall(function() c:Destroy() end) end
    end
end

function ICUI.gm_clear_pins(panel)
    local pins = comp(ICUI.GM_PINS, panel)
    if pins then
        for i in pairs(ICUI.gm_keys) do drop_pair(pins, i) end
    end
    ICUI.gm_keys = {}
end

function ICUI.gm_draw_pins(panel, faction, memo)
    memo = memo or ICUI.map_memo(faction)
    local pins = comp(ICUI.GM_PINS, panel)
    if not pins or not faction then ICUI.gm_clear_pins(panel) return end
    -- THE SCREEN, NOT THE BOX: a pin is placed in screen space, and on a screen
    -- wider than the box a holder at the box would stop short of its edge.
    pins:MoveTo(0, 0)
    ICUI.resize(pins, root():Dimensions())
    local court = IC.court(faction)
    local capital = IC.capital_province(faction)
    local seats = IC.seats(faction)
    -- REPAINTED IN PLACE, NOT REMADE. A pin made from Lua starts at its
    -- holder's corner until the engine places it (check_gm's fade note), so
    -- remaking every pin on every click would flash them all there. Only a pin
    -- whose province moved or went is destroyed.
    local was = ICUI.gm_keys
    ICUI.gm_keys = {}
    for i, province in pairs(was) do
        if seats[i] ~= province then drop_pair(pins, i) end
    end
    for i, province in ipairs(seats) do
        local region = ICUI.map_region(faction, province)
        local cqi = nil
        if region then pcall(function() cqi = region:settlement():cqi() end) end
        local names = gm_names(i)
        local paths = {ICUI.PATH_GM_PIN, ICUI.PATH_GM_FACE, ICUI.PATH_GM_NAME, ICUI.PATH_GM_LOYAL,
                       ICUI.PATH_GM_BADGE}
        if not cqi then
            drop_pair(pins, i)
        else
            local whole = true
            for _, name in ipairs(names) do
                if not comp(name, pins) then whole = false end
            end
            if not whole then
                drop_pair(pins, i)
                -- THE PIN FIRST, so the face and the plates - made after it -
                -- draw over it.
                for k, name in ipairs(names) do pins:CreateComponent(name, paths[k]) end
            end
            local pin, face = comp(names[1], pins), comp(names[2], pins)
            local plate, loyal = comp(names[3], pins), comp(names[4], pins)
            local badge = comp(names[5], pins)
            if pin and face and plate and loyal and badge then
                -- THE RACE'S PIN AND PLATES (DWF.art), over the shared file's own.
                local art = ICUI.ART or {}
                if art.gm_pin then pcall(function() pin:SetImagePath(art.gm_pin, 0) end) end
                if art.gm_name then pcall(function() plate:SetImagePath(art.gm_name, 0) end) end
                if art.gm_loyal then pcall(function() loyal:SetImagePath(art.gm_loyal, 0) end) end
                local at = cco("CcoCampaignSettlement", cqi)
                for _, c in ipairs({pin, face, plate, loyal, badge}) do c:SetContextObject(at) end
                local gov = court.govs[province]
                local slug = gov and IC.house_of_cqi(faction, gov) or nil
                local port = gov and ICUI.portrait_path(gov) or nil
                pin:SetImagePath(ICUI.gm_ring_path(slug), ICUI.GP_PARTY)
                pin:SetImagePath(province == capital and ICUI.MK_RING_CAPITAL
                                 or ICUI.MASK_NONE, ICUI.GP_CAPITAL)
                pin:SetImagePath(ICUI.MASK_NONE, ICUI.GP_OUTLINE)
                face:SetImagePath(port or ICUI.MASK_NONE, ICUI.GF_PORT)
                face:SetImagePath((not port and slug and ICUI.crest(slug)) or ICUI.MASK_NONE,
                                  ICUI.GF_CREST)
                plate:SetImagePath(ICUI.gm_wash_path(slug), ICUI.GN_WASH)
                badge:SetImagePath((slug and ICUI.crest(slug)) or ICUI.MASK_NONE, ICUI.GB_CREST)
                -- ONE LINE ON EACH PLATE, the name cut to the plate's inside; the
                -- pin's tooltip carries it whole.
                set_text(plate, ICUI.cut_text(plate, loc("provinces_onscreen_" .. province, province),
                                              ICUI.GM_NAME_W))
                set_text(loyal, string.format("Loyalty %d%%", IC.province_loyalty(faction, province)))
                pin:SetTooltipText(ICUI.map_tip(faction, province, nil, memo), "", true)
                ICUI.gm_keys[i] = province
            end
        end
    end
end

-- WHAT THE VIEW OWNS, put right after every refresh: on the Governors view the
-- backdrop clears, the panel lets the map have the mouse and the pins draw; on
-- any other view all three go back. A tab, a picker, the Help page and a
-- reopen all pass through refresh, so all of them land here.
function ICUI.gm_sync()
    local panel = comp(ICUI.PANEL)
    if not panel then return end
    local on = ICUI.gm_on()
    -- A VIEW ENTERED AFRESH starts with nothing chosen (the party map's rule).
    if on and not ICUI.gm_was_on then ICUI.gm_reset() end
    ICUI.gm_was_on = on
    local ground = (ICUI.ART or {}).panel_bg or ICUI.GM_BACKDROP
    pcall(function() panel:SetImagePath(on and ICUI.MASK_NONE or ground, 0) end)
    panel:SetInteractive(not on)
    ICUI.gm_show_column(panel, on)
    if not on then
        ICUI.gm_clear_pins(panel)
        ICUI.gm_light(nil)
        return
    end
    -- THE COURT'S LIST FURNITURE, which this view does not draw and which the
    -- last tab may have left showing.
    for _, keys in ipairs({ICUI.HDR_KEYS, ICUI.HSORT_KEYS,
                           {"ic_page_prev", "ic_page_lbl", "ic_page_next"}}) do
        for _, name in ipairs(keys) do show(comp(name, panel), false) end
    end
    for i = 1, ICUI.MAX_ROWS do show(comp(ICUI.ROW .. "_" .. i, panel), false) end
    local faction = ICUI.player()
    local memo = ICUI.map_memo(faction)
    ICUI.gm_draw_pins(panel, faction, memo)
    ICUI.gm_draw_column(panel, faction, memo)
    ICUI.gm_ring(panel, faction)
    ICUI.gm_light(faction)
    -- THE FOOTER'S PLATE, under the footer line while it has something to say.
    local alert, said = comp("ic_alert", panel), false
    if alert then pcall(function() said = alert:Visible() end) end
    show(comp("ic_gm_foot", panel), said == true)
end

-- AFTER the court's own refresh, whatever it drew.
local court_refresh = ICUI.refresh
function ICUI.refresh(...)
    court_refresh(...)
    local ok, err = pcall(ICUI.gm_sync)
    if not ok then IC.warn("IRON COURT: the Governors map failed to draw: " .. tostring(err)) end
end

-- A PIN: the governor picker for its province, drawn in the column.
function ICUI.gm_pin_click(index)
    local faction = ICUI.player()
    local province = ICUI.gm_keys[index]
    if not faction or not province then return end
    -- STILL YOURS: IC.assign_governor does not ask, so a province lost since the
    -- pins drew must not reach it. The view redraws instead.
    if not ICUI.gm_held(faction, province) then ICUI.refresh() return end
    ICUI.gm_open_picker(province)
end

-- THE COLUMN: CA's Hell-Forge side panel on the left, over the map. Its
-- components are the panel's own, declared in derpy_ic_panel.twui.xml and
-- placed by ICUI.layout; its rows are one pool made here, for all three pages.
ICUI.GM_PLATES = {"ic_gm_top", "ic_gm_foot", "ic_gm_col"}
-- SHOWN WITH THE VIEW. ic_gm_foot is not here: it shows with the footer line.
ICUI.GM_KEYS = {"ic_gm_top", "ic_gm_col", "ic_gm_head", "ic_gm_tog_1", "ic_gm_tog_2",
                "ic_gm_tog_lbl_1", "ic_gm_tog_lbl_2", "ic_gm_hint",
                "ic_gm_sort_1", "ic_gm_sort_2", "ic_gm_sort_3", "ic_gm_btns", "ic_gm_ok", "ic_gm_no"}
ICUI.GM_TOGS = {ic_gm_tog_1 = "parties", ic_gm_tog_2 = "provinces"}
ICUI.GM_PAGE_TITLE = {parties = "Parties", provinces = "Provinces", picker = "Candidates"}
-- A TOGGLE'S ART LAYERS: standard, then hover. Must match _panel in gen_ic_ui.py.
ICUI.GM_TOG_ART = {0, 2}
ICUI.NOT_SCALED[#ICUI.NOT_SCALED + 1] = "GM_TOG_ART"
local HF_ROW = "ui/skins/default/dlc23_chd_hell_forge/button_square_extra_large_"
ICUI.GM_ROW_ART = {
    live = {HF_ROW .. "active.png", HF_ROW .. "hover.png"},
    selected = {HF_ROW .. "selected.png", HF_ROW .. "selected_hover.png"},
    inactive = {HF_ROW .. "inactive.png", HF_ROW .. "inactive.png"},
}
local ROUND = "ui/skins/default/button_round_medium_"
ICUI.GM_ROUND_ART = {
    live = {ROUND .. "active.png", ROUND .. "hover.png"},
    selected = {ROUND .. "selected.png", ROUND .. "selected_hover.png"},
}
ICUI.gm_page = "provinces"
ICUI.gm_party = nil                  -- the chosen Parties row, of the whole list
ICUI.gm_rows = {}                    -- entry -> the row table drawn there
ICUI.gm_was_on = false

-- NOTHING CHOSEN: a view entered afresh starts clean.
function ICUI.gm_reset()
    ICUI.gm_party = nil
    ICUI.gm_sel = nil
    ICUI.gm_rescroll()
end

-- THE COURT CLOSED FORGETS THE VIEW, so a reopen on Governors is afresh, and
-- leaves the poll nothing to follow.
local court_close = ICUI.close
function ICUI.close(...)
    ICUI.gm_was_on = false
    ICUI.gm_list_key = nil
    ICUI.gm_light(nil)
    return court_close(...)
end

function ICUI.gm_show_column(panel, on)
    for _, name in ipairs(ICUI.GM_KEYS) do show(comp(name, panel), on) end
    show(comp(ICUI.GM_LIST, panel), on)
    for i = 1, ICUI.GM_ROWS do show(comp(ICUI.GM_ROW .. "_" .. i, panel), on) end
    if not on then show(comp("ic_gm_foot", panel), false) end
end

-- THE COLUMN SCROLLS, by the mouse wheel and a slider. CA's own list, the Great
-- Guilds' proven shape (docs/CUSTOM_UI.md, "Scrolling lists"). A card has six
-- cells, and a row inside a list must have none, so list_box holds one EMPTY row
-- per entry: that gives the list its length, and it is what the engine scrolls.
--
-- DRAWN WHOLE (docs/CUSTOM_UI.md "Drawn whole"). Every entry's card is made once,
-- at its own index, under one holder in list_clip; gm_scroll_poll puts the
-- holder where list_box is, and the holder's one MoveTo carries every card.
-- Nothing is redrawn to scroll: the Exchange measured a redraw at 25-200ms, which
-- freezes a drag and then trails the bar.
--
-- REBUILT, NOT REWOUND: nothing documented scrolls a list from script, and moving
-- list_box by hand is how a list scrolls to somewhere it is not. A new page, a
-- new length or a re-sort makes the list again, at the top, and the cards with
-- it (they are inside it).
ICUI.GM_SCROLL_MS = 16               -- every frame: the cards trail the bar by up to one tick
ICUI.NOT_SCALED[#ICUI.NOT_SCALED + 1] = "GM_SCROLL_MS"
ICUI.GM_HOLDER = "ic_gm_rows"
ICUI.gm_list_gen = 0
ICUI.gm_list_key = nil               -- what the built list is, nil while none is
-- WHAT EACH CARD'S LINES ALREADY SAY. A drawn-whole list rewrites every card on
-- every refresh, and ICUI.cut_text measures once a word. Card lines only - no
-- other code writes them - and emptied whenever the cards are made again.
ICUI.gm_drawn = {}

-- THE NEXT DRAW STARTS THE LIST AGAIN, at the top.
function ICUI.gm_rescroll()
    ICUI.gm_list_gen = ICUI.gm_list_gen + 1
end

function ICUI.gm_list(panel, n)
    local page = ICUI.gm_live_page()
    local key = page .. "|" .. n .. "|" .. ICUI.gm_list_gen
    local list = comp(ICUI.GM_LIST, panel)
    if list and key == ICUI.gm_list_key then
        -- KEPT, AND STILL SCROLLED: the holder belongs where the list has gone.
        ICUI.gm_follow(panel)
        return list
    end
    if list then pcall(function() list:Destroy() end) end
    ICUI.gm_list_key, ICUI.gm_drawn = nil, {}
    pcall(function() panel:CreateComponent(ICUI.GM_LIST, ICUI.PATH_GM_LIST) end)
    list = comp(ICUI.GM_LIST, panel)
    if not list then return nil end
    local px, py = panel:Position()
    local x, y = px + ICUI.OX + ICUI.GM_ROW_X, py + ICUI.OY + ICUI.GM_ROW_Y
    local h = ICUI.GM_ROWS * ICUI.GM_ROW_PITCH
    list:MoveTo(x, y)
    ICUI.resize(list, ICUI.GM_ROW_W + ICUI.GM_SLIDER_GAP + ICUI.GM_SLIDER_W, h)
    local clip, slider = comp("list_clip", list), comp("vslider", list)
    if clip then
        clip:MoveTo(x, y)
        ICUI.resize(clip, ICUI.GM_ROW_W, h)
    end
    if slider then
        slider:MoveTo(x + ICUI.GM_ROW_W + ICUI.GM_SLIDER_GAP, y)
        ICUI.resize(slider, ICUI.GM_SLIDER_W, h)
        -- THE TRAVEL IS A NUMBER, not a size: Resize never reaches it.
        pcall(function() slider:SetProperty("maxValue", h - ICUI.GM_HANDLE_H) end)
        local handle = comp("handle", slider)
        if handle then
            pcall(function() handle:SetProperty("max_height", h - ICUI.GM_HANDLE_H) end)
            ICUI.skin_handle(handle)
        end
        show(slider, n > ICUI.GM_ROWS)
    end
    local box = comp("list_box", list)
    if box then
        for i = 1, n do
            local name = ICUI.GM_SP .. "_" .. i
            pcall(function() box:CreateComponent(name, ICUI.PATH_GM_SP) end)
            local sp = comp(name, box)
            if sp then ICUI.resize(sp, ICUI.GM_ROW_W, ICUI.GM_ROW_PITCH) end
        end
        -- Without it the rows sit stacked at the box's origin.
        pcall(function() box:Layout() end)
    end
    -- THE HOLDER, made straight into the clip window: the Exchange ADOPTS a
    -- holder its panel file declares, and this one has nothing to hand back -
    -- its cards go when the list does. The empty-row file is the right shape:
    -- one component, no image, no children. Over list_box, so the wheel on a
    -- card reaches the list through its parents.
    if clip then
        pcall(function() clip:CreateComponent(ICUI.GM_HOLDER, ICUI.PATH_GM_SP) end)
        local holder = comp(ICUI.GM_HOLDER, clip)
        if holder then
            holder:MoveTo(x, y)
            ICUI.resize(holder, ICUI.GM_ROW_W, math.max(ICUI.GM_ROWS, n) * ICUI.GM_ROW_PITCH)
        end
    end
    ICUI.gm_list_key = key
    return list
end

-- THE CARDS FOLLOW THE LIST: the engine scrolls list_box, and the holder goes
-- where it is. Two reads and at most one move, however long the list.
function ICUI.gm_follow(panel)
    local list = comp(ICUI.GM_LIST, panel)
    local clip = list and comp("list_clip", list)
    local box, holder = clip and comp("list_box", clip), clip and comp(ICUI.GM_HOLDER, clip)
    if not (box and holder) then return end
    local hx, hy = holder:Position()
    local _bx, by = box:Position()
    if hy ~= by then holder:MoveTo(hx, by) end
end

-- THE POLL: there is no scroll event and no Lua wheel event. UI-only and local,
-- so safe in multiplayer. NOTHING IS REDRAWN HERE, and it returns at once with
-- no list built, since it runs for the whole campaign.
function ICUI.gm_scroll_poll()
    if not ICUI.gm_list_key or ICUI.view ~= "govs" then return end
    local panel = comp(ICUI.PANEL)
    if panel then ICUI.gm_follow(panel) end
end

-- EVERY CARD, from the holder's top at its own index, each made and placed once:
-- placed by hand, the holder's MoveTo carries it from then on. With no holder
-- (the list could not be made) the first GM_ROWS cards go into the panel,
-- unscrolled, and are placed every draw. Returns where the cards are and how
-- many of them there are.
function ICUI.gm_make_rows(panel, n)
    local list = comp(ICUI.GM_LIST, panel)
    local holder = list and comp(ICUI.GM_HOLDER, list)
    local host, count, x, y
    if holder then
        host, count = holder, n
        x, y = holder:Position()
    else
        local px, py = panel:Position()
        host, count = panel, math.min(n, ICUI.GM_ROWS)
        x, y = px + ICUI.OX + ICUI.GM_ROW_X, py + ICUI.OY + ICUI.GM_ROW_Y
    end
    for i = 1, count do
        local name = ICUI.GM_ROW .. "_" .. i
        local row = comp(name, host)
        local fresh = not row
        if fresh then
            pcall(function() host:CreateComponent(name, ICUI.path(ICUI.PATH_GM_ROW)) end)
            row = comp(name, host)
        end
        if row and (fresh or host == panel) then
            local rx, ry = x, y + (i - 1) * ICUI.GM_ROW_PITCH
            row:MoveTo(rx, ry)
            ICUI.resize(row, ICUI.GM_ROW_W, ICUI.GM_ROW_H)
            for cname, b in pairs(ICUI.GM_ROW_CHILD_XY) do
                local c = comp(cname, row)
                if c then
                    c:MoveTo(rx + b[1], ry + b[2])
                    ICUI.resize(c, b[3], b[4])
                end
            end
        end
    end
    return host, count
end

-- ONE ROW FROM `r`. A field left nil hides its cell, so a page never shows the
-- last page's leftovers.
function ICUI.gm_fill_row(row, r)
    local art = ICUI.GM_ROW_ART[r.look or "live"] or ICUI.GM_ROW_ART.live
    pcall(function()
        row:SetImagePath(ICUI.themed(art[1]), 0)
        row:SetImagePath(ICUI.themed(art[2]), 1)
    end)
    -- NO PORTRAIT, NO PORTRAIT'S GAP: a Parties row's lines start beside its
    -- crest, as far from it as it is from the frame, and with no loyalty icon
    -- the third line lines up with the other two (the picker's rows too). Placed
    -- from the row's own position each draw, so a scrolled card is right too.
    local xy, rx, ry = ICUI.GM_ROW_CHILD_XY, row:Position()
    local dx = r.face and 0 or (2 * xy.ic_gr_crest[1] + xy.ic_gr_crest[3] - xy.ic_gr_l1[1])
    local shift = {ic_gr_l1 = dx, ic_gr_l2 = dx, ic_gr_icon = dx,
                   ic_gr_l3 = dx + (r.fealty and 0 or xy.ic_gr_l1[1] - xy.ic_gr_l3[1])}
    for cname, d in pairs(shift) do
        local c, b = comp(cname, row), xy[cname]
        if c then
            c:MoveTo(rx + b[1] + d, ry + b[2])
            if cname ~= "ic_gr_icon" then ICUI.resize(c, b[3] - d, b[4]) end
        end
    end
    local id = row:Id()
    for _, key in ipairs({"l1", "l2", "l3"}) do
        local cname = "ic_gr_" .. key
        local c = comp(cname, row)
        if c then
            -- THE SHIFT IS IN THE MEMO: it changes the line's width, and so its cut.
            local want = tostring(r[key] or "") .. "|" .. shift[cname]
            if ICUI.gm_drawn[id .. "/" .. cname] ~= want then
                ICUI.fit_cut(c, r[key] or "")
                ICUI.gm_drawn[id .. "/" .. cname] = want
            end
            show(c, r[key] ~= nil)
        end
    end
    if r.face then
        if r.vacant then ICUI.set_vacant_plate(row, "ic_gr_face")
        else ICUI.set_plate(row, "ic_gr_face", r.plate, r.face) end
    end
    ICUI.set_face(row, "ic_gr_face", r.face)
    ICUI.set_crest(row, "ic_gr_crest", r.crest, ICUI.GM_ROW_CHILD_XY.ic_gr_crest[3])
    ICUI.set_crest(row, "ic_gr_badge", r.badge, ICUI.GM_ROW_CHILD_XY.ic_gr_badge[3])
    ICUI.set_crest(row, "ic_gr_icon", r.fealty, ICUI.GM_ROW_CHILD_XY.ic_gr_icon[3])
    row:SetTooltipText(r.tip or "", "", true)
end

-- EVERY CARD OF THE PAGE. `chosen(r, n)` says whether entry n is the chosen one.
function ICUI.gm_draw_page(panel, rows, chosen)
    ICUI.gm_list(panel, #rows)
    local host, count = ICUI.gm_make_rows(panel, #rows)
    ICUI.gm_rows = {}
    -- THE PANEL'S FALLBACK CARDS outlive a shorter page; the holder's do not.
    for i = 1, (host == panel) and ICUI.GM_ROWS or count do
        local row = comp(ICUI.GM_ROW .. "_" .. i, host)
        local r = i <= count and rows[i] or nil
        if row then
            show(row, r ~= nil)
            if r then
                if (r.look or "live") == "live" and chosen(r, i) then r.look = "selected" end
                ICUI.gm_fill_row(row, r)
                ICUI.gm_rows[i] = r
            end
        end
    end
end

-- THE PARTIES PAGE: the party map's legend, as built - the court's parties in
-- its own order, then "No governor".
function ICUI.gm_party_rows(faction)
    local court = IC.court(faction)
    local out = {}
    for i, r in ipairs(ICUI.map_rows(faction)) do
        local list, why = ICUI.map_outline(faction, r.slug)
        if r.slug then
            -- THE COURT'S OWN TIP; its Crown branch already explains the Crown.
            local tip = ICUI.secession_tip(faction, court, r.slug)
            if why and r.slug ~= IC.CROWN then tip = why end
            out[i] = {l1 = ICUI.house_name(r.slug, faction),
                      l2 = string.format("Governs %d", #IC.provinces_of_house(faction, r.slug)),
                      l3 = (not why) and string.format("Would take %d", #list) or nil,
                      crest = ICUI.crest(r.slug), tip = tip, why = why}
        else
            local n = #list
            out[i] = {l1 = "No governor",
                      l2 = string.format("%d province%s", n, n == 1 and "" or "s"),
                      tip = "Provinces with no governor. Click a pin to appoint one."}
        end
    end
    return out
end

ICUI.gm_sel = nil                    -- the chosen province on the Provinces page
-- THE PROVINCES PAGE'S SORT: the court's own Governors modes (ICUI.SORTS.govs),
-- by column. Map order is what a third click returns to.
ICUI.GM_SORTS = {{"Province", 1}, {"Governor", 2}, {"Loyalty", 4}}
ICUI.NOT_SCALED[#ICUI.NOT_SCALED + 1] = "GM_SORTS"
-- THE CANDIDATES' SORT: the court's own picker modes (ICUI.SORTS.pick), so a sort chosen on either
-- picker holds on both. Who can be appointed, then rank, then Influence.
ICUI.GM_PICK_SORTS = {{"Available", 5}, {"Rank", 3}, {"Influence", 4}}
ICUI.NOT_SCALED[#ICUI.NOT_SCALED + 1] = "GM_PICK_SORTS"

-- THE PAGE'S SORT BUTTONS and the court view they sort, or nil.
function ICUI.gm_sorts(page)
    if page == "provinces" then return ICUI.GM_SORTS, "govs" end
    if page == "picker" then return ICUI.GM_PICK_SORTS, "pick" end
    return nil
end
ICUI.GM_FEALTY = {high = "ui/skins/default/icon_fealty_high.png",
                  medium = "ui/skins/default/icon_fealty_medium.png",
                  low = "ui/skins/default/icon_fealty_low.png"}

-- CA'S LOYALTY ICON for a province: low where it would go with a party that
-- walks out, high above where every province starts, medium between.
function ICUI.gm_fealty(loyalty)
    if loyalty <= IC.TUNE.prov_defect_floor then return ICUI.GM_FEALTY.low end
    if loyalty > IC.TUNE.prov_loyalty_start then return ICUI.GM_FEALTY.high end
    return ICUI.GM_FEALTY.medium
end

-- STILL YOURS: IC.assign_governor does not ask, so every click that names a
-- province asks here first.
function ICUI.gm_held(faction, province)
    for _, p in ipairs(IC.seats(faction)) do if p == province then return true end end
    return false
end

-- THE GOVERNOR PICKER FOR A PROVINCE: the pin's and the check's one way in.
function ICUI.gm_open_picker(province)
    ICUI.pick = {kind = "gov", key = province}
    ICUI.list_rescroll()
    ICUI.notice = nil
    ICUI.gm_rescroll()
    ICUI.gm_pick_sel = nil
    ICUI.refresh()
end

ICUI.gm_pick_sel = nil               -- the chosen man on the picker page

-- THE PAGE ON SCREEN: the picker while one is up, else the page chosen.
function ICUI.gm_live_page()
    if ICUI.pick and ICUI.pick.kind == "gov" then return "picker" end
    return ICUI.gm_page
end

-- THE PICKER PAGE: the court's own governor picker, as cards.
-- A man the click would refuse is drawn inactive, with the refusal first.
function ICUI.gm_picker_rows(faction)
    local rows = {}
    for i, line in ipairs(ICUI.picker_lines(faction, IC.court(faction))) do
        local tip = {}
        if line.why then tip[#tip + 1] = line.why .. "." end
        if line.tip then tip[#tip + 1] = line.tip end
        tip[#tip + 1] = string.format("%d influence. Holds: %s.", line.sort.standing, line.holds)
        rows[i] = {
            key = line.sort.cqi, cqi = ICUI.pick_rows[i],
            l1 = line[1], l2 = line[2],
            l3 = string.format("Rank %d, %d influence", line.sort.rank, line.sort.standing),
            face = line.icon_kind == "porthole" and line.icon or nil,
            plate = line.plate,
            crest = line.icon_kind == "crest" and line.icon or nil,
            badge = line.crest,
            look = ICUI.pick_rows[i] and "live" or "inactive",
            tip = table.concat(tip, "\n"),
        }
    end
    return rows
end

-- THE CHOSEN MAN IS STILL ON THE LIST AND STILL FREE.
local function pick_still_free(rows)
    for _, r in ipairs(rows) do
        if r.cqi and r.cqi == ICUI.gm_pick_sel then return true end
    end
    return false
end

-- THE PROVINCES PAGE: the Governors list, moved, in the order the player asked
-- for.
function ICUI.gm_province_rows(faction, memo)
    memo = memo or ICUI.map_memo(faction)
    local court = IC.court(faction)
    local levels = IC.province_levels(faction)
    local rows, keys = {}, {}
    local seats = IC.seats_named(faction)
    for i = 1, #seats do
        local p = seats[i].key
        local cqi = court.govs[p]
        local holder = cqi and IC.character_by_cqi(faction, cqi) or nil
        local slug = cqi and IC.house_of_cqi(faction, cqi) or nil
        local port = cqi and ICUI.portrait_path(cqi) or nil
        local name = loc("provinces_onscreen_" .. p, seats[i].name)
        local gov = ICUI.gov_holder_text(faction, p, holder, cqi)
        local loyal = IC.province_loyalty(faction, p)
        local tip = ICUI.map_tip(faction, p, true, memo)
        if holder then tip = tip .. "\n" .. ICUI.gov_rank_tip(faction, p, holder) end
        -- WHAT IT ADDS NOW, and what it grows to while a new governor earns it.
        local now, worth = IC.gov_grown_weight(court, p, levels), IC.gov_weight_of(levels[p])
        rows[i] = {
            key = p, l1 = name, l2 = gov,
            l3 = (not cqi) and string.format("%d%%", loyal)
                 or (now < worth) and string.format("%d%%, +%d of %d strength", loyal, now, worth)
                 or string.format("%d%%, +%d strength", loyal, now),
            -- HIS FACE; else his party's crest; else the empty seat.
            face = port or ((not cqi) and ICUI.SILHOUETTE or nil),
            vacant = cqi == nil, plate = slug,
            crest = (cqi and not port and slug) and ICUI.crest(slug) or nil,
            badge = (port and slug) and ICUI.crest(slug) or nil,
            fealty = ICUI.gm_fealty(loyal), tip = tip,
            sort = {province = name, overseer = gov, loyalty = loyal, cqi = cqi or 0, name = p},
        }
        keys[i] = p
    end
    ICUI.sort_rows("govs", rows, keys, #rows)
    return rows, keys
end

-- THE CAMERA TO A PROVINCE'S SETTLEMENT, keeping the player's zoom and bearing
-- (GGUI.pan_to's way).
function ICUI.gm_look_at(faction, province)
    local region = ICUI.map_region(faction, province)
    if not region then return end
    pcall(function()
        local s = region:settlement()
        local x, y = s:display_position_x(), s:display_position_y()
        local _cx, _cy, d, b, h = cm:get_camera_position()
        cm:scroll_camera_from_current(true, 1, {x, y, d, b, h})
    end)
end

-- LIVE OR NOT, in look and in fact: SetDisabled blocks the click, grey_look
-- holds the grey through the engine's own state changes.
function ICUI.gm_enable(c, on)
    if not c then return end
    pcall(function() c:SetDisabled(not on) end)
    pcall(ICUI.grey_look, c, not on)
end

function ICUI.gm_draw_column(panel, faction, memo)
    local page = ICUI.gm_live_page()
    for id, p in pairs(ICUI.GM_TOGS) do
        local tog = comp(id, panel)
        local art = ICUI.GM_ROUND_ART[p == page and "selected" or "live"]
        if tog then
            pcall(function()
                tog:SetImagePath(ICUI.themed(art[1]), ICUI.GM_TOG_ART[1])
                tog:SetImagePath(ICUI.themed(art[2]), ICUI.GM_TOG_ART[2])
            end)
        end
    end
    set_text(comp("ic_gm_tog_lbl_1", panel), ICUI.GM_PAGE_TITLE.parties)
    set_text(comp("ic_gm_tog_lbl_2", panel), ICUI.GM_PAGE_TITLE.provinces)
    set_text(comp("ic_gm_head", panel), ICUI.GM_PAGE_TITLE[page])
    local hint = comp("ic_gm_hint", panel)
    if page == "parties" then
        local rows = ICUI.gm_party_rows(faction)
        ICUI.gm_draw_page(panel, rows, function(_r, n) return n == ICUI.gm_party end)
        local chosen = ICUI.gm_party and rows[ICUI.gm_party]
        show(hint, true)
        if #IC.seats(faction) == 0 then
            set_text(hint, "You hold no provinces.")
        else
            set_text(hint, (chosen and chosen.why) or "Click a party to see what it would take.")
        end
    elseif page == "picker" then
        local rows = ICUI.gm_picker_rows(faction)
        if not pick_still_free(rows) then ICUI.gm_pick_sel = nil end
        ICUI.gm_draw_page(panel, rows, function(r)
            return r.cqi ~= nil and r.cqi == ICUI.gm_pick_sel
        end)
        show(hint, #rows == 0)
        if #rows == 0 then set_text(hint, "No characters in this faction.") end
        ICUI.gm_draw_sorts(panel, page)
    else
        show(hint, false)
        local rows, keys = ICUI.gm_province_rows(faction, memo)
        -- A CHOICE THAT IS NO LONGER HELD is no choice.
        local held = false
        for _, k in ipairs(keys) do if k == ICUI.gm_sel then held = true end end
        if not held then ICUI.gm_sel = nil end
        ICUI.gm_draw_page(panel, rows, function(r) return r.key == ICUI.gm_sel end)
        ICUI.gm_draw_sorts(panel, page)
    end
    -- THE ROUND BUTTONS: the Provinces page's. The cross only for a province
    -- with a governor to release; both dead with nothing chosen. Worked out
    -- first and drawn after, so another page can say what they do there.
    local governed = ICUI.gm_sel ~= nil and IC.court(faction).govs[ICUI.gm_sel] ~= nil
    local btns = page == "provinces"
    local ok_on, no_on = ICUI.gm_sel ~= nil, governed
    local no_shown = ICUI.gm_sel == nil or governed
    local ok_tip = "Choose a governor for this province."
    local no_tip = "Release this province's governor."
    if page == "picker" then
        -- THE PICKER'S: appoint the chosen man, or go back without one.
        btns, ok_on, no_on, no_shown = true, ICUI.gm_pick_sel ~= nil, true, true
        ok_tip, no_tip = "Appoint the chosen man.", "Go back without choosing."
    end
    local sorts = ICUI.gm_sorts(page)
    for i = 1, #ICUI.GM_SORTS do
        -- The picker's hint sits where the buttons do; it shows only on an empty list.
        show(comp("ic_gm_sort_" .. i, panel),
             sorts ~= nil and (page ~= "picker" or #ICUI.gm_rows > 0))
    end
    show(comp("ic_gm_btns", panel), btns)
    show(comp("ic_gm_ok", panel), btns)
    show(comp("ic_gm_no", panel), btns and no_shown)
    ICUI.gm_enable(comp("ic_gm_ok", panel), ok_on)
    ICUI.gm_enable(comp("ic_gm_no", panel), no_on)
    local ok_b, no_b = comp("ic_gm_ok", panel), comp("ic_gm_no", panel)
    if ok_b then ok_b:SetTooltipText(ok_tip, "", true) end
    if no_b then no_b:SetTooltipText(no_tip, "", true) end
end

-- THE PAGE'S SORT BUTTONS: the lit label and the arrow, as the court's headers.
function ICUI.gm_draw_sorts(panel, page)
    local sorts, view = ICUI.gm_sorts(page)
    if not sorts then return end
    for i, s in ipairs(sorts) do
        local c = comp("ic_gm_sort_" .. i, panel)
        if c then
            local active = ICUI.sort[view] == ICUI.sort_for_column(view, s[2])
            set_text(c, active and string.format("[[col:%s]]%s[[/col]]", ICUI.SORT_LIT, s[1]) or s[1])
            pcall(function() c:SetImagePath(ICUI.sort_arrow_path(view, s[2]), 0) end)
        end
    end
end

-- THE RED RINGS: what the chosen party would take.
function ICUI.gm_ring(panel, faction)
    local page = ICUI.gm_live_page()
    local ringed = {}
    if page == "parties" and ICUI.gm_party then
        local r = ICUI.map_rows(faction)[ICUI.gm_party]
        if r then
            for _, p in ipairs((ICUI.map_outline(faction, r.slug))) do ringed[p] = true end
        end
    end
    if page == "provinces" and ICUI.gm_sel then ringed[ICUI.gm_sel] = true end
    if page == "picker" then ringed[ICUI.pick.key] = true end
    local pins = comp(ICUI.GM_PINS, panel)
    for i, province in pairs(ICUI.gm_keys) do
        local pin = pins and comp(ICUI.GM_PIN .. "_" .. i, pins)
        if pin then
            pin:SetImagePath(ringed[province] and ICUI.MK_RING_OUTLINE or ICUI.MASK_NONE,
                             ICUI.GP_OUTLINE)
        end
    end
end

-- CA'S OWN REGION OVERLAY, LIT OVER WHAT THE CHOSEN PARTY GOVERNS. The engine
-- takes no colour: mode 13, TUTORIAL_REGION_HIGHLIGHT, is its one plain
-- highlight, and one set shows at a time. Probed in game: it lights exactly the
-- regions handed to it, land only. "No governor" lights the provinces nobody
-- governs. Called only when the set changes, and turned off only when this lit
-- it, so the player's own overlay is left alone.
ICUI.GM_OVERLAY_MODE = 13
ICUI.NOT_SCALED[#ICUI.NOT_SCALED + 1] = "GM_OVERLAY_MODE"
ICUI.gm_lit = ""
function ICUI.gm_light(faction)
    local regions = {}
    if faction and ICUI.gm_on() and ICUI.gm_live_page() == "parties" and ICUI.gm_party then
        local r = ICUI.map_rows(faction)[ICUI.gm_party]
        if r then
            local mine = {}
            local list = r.slug and IC.provinces_of_house(faction, r.slug)
                         or (ICUI.map_outline(faction, nil))
            for _, p in ipairs(list) do mine[p] = true end
            pcall(function()
                local held = cm:get_faction(faction):region_list()
                for i = 0, held:num_items() - 1 do
                    local reg = held:item_at(i)
                    if mine[reg:province():key()] then regions[#regions + 1] = reg:name() end
                end
            end)
        end
    end
    local key = table.concat(regions, ",")
    if key == ICUI.gm_lit then return end
    pcall(function()
        if #regions > 0 then
            CampaignUI.SetOverlayMode(ICUI.GM_OVERLAY_MODE, 0, unpack(regions))
            CampaignUI.SetOverlayVisible(true)
        else
            CampaignUI.SetOverlayVisible(false)
        end
    end)
    ICUI.gm_lit = key
    ICUI.gm_lit_d = ICUI.gm_cam_d()
end

-- A ZOOM DROPS IT: zoom out and back in and the party's provinces show the
-- plain map. The engine resets the overlay on a zoom, raises no event and has
-- no getter, so the poll re-lights once the camera has come to rest at a
-- distance other than the one it was lit at.
ICUI.GM_ZOOM_MS = 300
ICUI.NOT_SCALED[#ICUI.NOT_SCALED + 1] = "GM_ZOOM_MS"
function ICUI.gm_cam_d()
    local ok, _x, _y, d = pcall(function() return cm:get_camera_position() end)
    if ok and type(d) == "number" then return d end
end

local function moved(a, b) return math.abs(a - b) > 0.01 end

function ICUI.gm_zoom_poll()
    if ICUI.gm_lit == "" then ICUI.gm_last_d = nil return end
    local d = ICUI.gm_cam_d()
    if not d then return end
    local rested = ICUI.gm_last_d and not moved(d, ICUI.gm_last_d)
    ICUI.gm_last_d = d
    if rested and (not ICUI.gm_lit_d or moved(d, ICUI.gm_lit_d)) then
        ICUI.gm_lit = ""
        ICUI.gm_light(ICUI.player())
    end
end

function ICUI.gm_to_page(page)
    ICUI.pick = nil               -- a page switch abandons a picker
    ICUI.notice = nil
    ICUI.gm_page = page
    ICUI.refresh()
end

function ICUI.gm_row_click(n)
    if not ICUI.gm_on() then return end
    if ICUI.gm_live_page() == "picker" then
        local r = ICUI.gm_rows[n]
        if r and r.cqi then
            ICUI.gm_pick_sel = (ICUI.gm_pick_sel ~= r.cqi) and r.cqi or nil
        elseif r then
            -- NOT CHOOSABLE, and it says so; the reason is on its tooltip.
            ICUI.play(ICUI.SOUNDS.refused)
        end
        ICUI.refresh()
        return
    end
    if ICUI.gm_page == "parties" then
        ICUI.gm_party = (ICUI.gm_party ~= n) and n or nil
    elseif ICUI.gm_page == "provinces" then
        local r = ICUI.gm_rows[n]
        if r and r.key then
            if ICUI.gm_sel == r.key then
                ICUI.gm_sel = nil
            else
                ICUI.gm_sel = r.key
                ICUI.gm_look_at(ICUI.player(), r.key)
            end
        end
    end
    ICUI.refresh()
end

function ICUI.gm_sort_click(i)
    if not ICUI.gm_on() then return end
    local sorts, view = ICUI.gm_sorts(ICUI.gm_live_page())
    local s = sorts and sorts[i]
    if not s then return end
    if ICUI.click_column(view, s[2]) then
        ICUI.gm_rescroll()                -- a re-sort starts at the top
        ICUI.refresh()
    end
end

-- THE CHECK: choose who governs the chosen province.
function ICUI.gm_ok()
    if not ICUI.gm_on() then return end
    local faction = ICUI.player()
    if ICUI.gm_live_page() == "picker" then
        local province = ICUI.pick.key
        -- STILL YOURS, AND HE STILL FREE: either can change between the draw
        -- and the click.
        if not ICUI.gm_held(faction, province) then
            ICUI.pick = nil
            ICUI.refresh()
            return
        end
        if not pick_still_free(ICUI.gm_picker_rows(faction)) then
            ICUI.gm_pick_sel = nil
            ICUI.refresh()
            return
        end
        -- SENT, NOT CALLED: the answer is ICUI.ANSWERS.gov, as the court's own
        -- picker's is, and it closes the picker.
        ICUI.send(faction, "gov", province .. "|" .. tostring(ICUI.gm_pick_sel))
        ICUI.refresh()
        return
    end
    if ICUI.gm_page ~= "provinces" or not ICUI.gm_sel then return end
    if not ICUI.gm_held(faction, ICUI.gm_sel) then
        ICUI.gm_sel = nil
        ICUI.refresh()
        return
    end
    ICUI.gm_open_picker(ICUI.gm_sel)
end

-- THE CROSS: release the chosen province's governor.
function ICUI.gm_no()
    if not ICUI.gm_on() then return end
    local faction = ICUI.player()
    if ICUI.gm_live_page() == "picker" then
        -- BACK TO THE PAGE IT CAME FROM, with nothing done.
        ICUI.pick = nil
        ICUI.list_rescroll()
        ICUI.notice = nil
        ICUI.refresh()
        return
    end
    if ICUI.gm_page ~= "provinces" or not ICUI.gm_sel then return end
    if not IC.court(faction).govs[ICUI.gm_sel] then return end
    ICUI.send(faction, "ungov", ICUI.gm_sel)
    ICUI.refresh()
end

local court_register = ICUI.register
function ICUI.register()
    court_register()
    ICUI.map_register()
end
