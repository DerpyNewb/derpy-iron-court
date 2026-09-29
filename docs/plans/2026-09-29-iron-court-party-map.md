# Iron Court Party Map Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Map tab that closes the court and pins a party-coloured marker to each held province's capital settlement on the live campaign map, with a legend that rings what a chosen party would take and markers that open their province's overseer picker.

**Architecture:** CA's Gardens of Morr technique: plain UI components carrying `ContextWorldSpaceComponent` on `CcoCampaignSettlement.Position`, each given its settlement with `SetContextObject(cco("CcoCampaignSettlement", settlement:cqi()))`. Two new generated layouts (a root-level map layer holding the legend, and a marker created into it once per province) and one new Lua file that loads after the panel file and calls into it. Nothing in the model changes; the one action the map can take, appointing a governor, is the court's existing `gov` action.

**Tech Stack:** Lua 5.1 (campaign script), Python 3 generators (`tools/gen_ic_ui.py`, `tools/gen_iron_court_emitter.py`), the Lua harness `tools/_iron_court_harness.lua`, the mutation runner `tools/mutate_iron_court.py`, the preview `tools/preview_iron_court.py`.

**Spec:** `docs/superpowers/specs/2026-09-29-iron-court-party-map-design.md`. Evidence: CA's `ui/campaign ui/dlc25_black_towers.twui.xml` in `ui3.pack` (dump it with `py tools/read_pack_index.py "<data>/ui3.pack" dlc25_black_towers.twui.xml`), and memory `wh3-world-space-ui-pin`.

## Global Constraints

- The workspace is NOT git. There are no commits: every checkpoint step is the harness run green plus the gates it names.
- No emojis anywhere. Never write the word "rung". Player text in plain words: no "standing", "cap", "rep", "AI", "HUD" in any string the player reads.
- The Iron Court Lua files, the harness, `gen_ic_ui.py` and `mutate_iron_court.py` are LF. Edit with the Edit tool or byte-safe Python; never `sed -i`. A patch script containing a backslash or a regex goes through the Write tool, never a heredoc.
- Harness: `"/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua` - stops at the first FAIL (`IC_TEST_ALL=1` runs all), ends `iron court harness: ok (N checks)`. It starts this plan at 789 checks. New checks go ABOVE `check("no parties' turn failed anywhere in the run"`.
- The harness sets `IC.TUNE.grace_turns = 0` where it loads the model; a check about the grace period sets it itself (`in_grace()`).
- Never edit any file while `tools/mutate_iron_court.py` runs; never run another gate beside it.
- A loc call from a listener or turn handler is a turn-1 CTD. Every string the map writes is written when the map opens or on a click, never from `FactionTurnStart`/`FactionTurnEnd`.
- Runtime components ignore `.twui.xml` offsets and dockpoints: every legend component is positioned with `MoveTo`. Markers are positioned by the engine through `ContextWorldSpaceComponent` and never moved from Lua.
- `SetText(text, "")`, never `SetStateText` (the importer refuses it).
- `:Parent()` returns an address: `UIComponent(UIComponent(c:Parent()))`, never one wrap (the importer refuses it).
- `SetVisible` takes a boolean, never nil.
- Build only with RPFM open (`http://127.0.0.1:45127/sessions` answers 200). After a build, if `Warhammer3.exe` is not running, deploy to data/ without asking: `py tools/deploy_iron_court.py` backs up, copies and byte-compares.
- CA's two callbacks, copied VERBATIM from `template_black_tower_slot`:
  - `ContextWorldSpaceComponent`, object `CcoCampaignSettlement`, function `Position`, property `depth_disabled` = `1`
  - `ContextOpacitySetter`, function `(pos = self.Position.y) => {pos | CampaignRoot.IsTacticalViewActive => 1 | pos < 0 => 0 | pos < 50 => pos/50.0 | 1}`, properties `propagate` = `` and `update_constant` = ``

## Rulings against the spec (made while planning; ledger them at execution)

1. **Phase 0 is the smallest real slice, checked by the author in game** (Task 1), not a throwaway script through the WH3 bridge. The bridge is not loaded in the sessions that build, and the slice is code that ships anyway. Cost if it fails: one tab, two layouts and a Lua file, all removed for the schematic fallback.
2. **The Lua file is `zzz_derpy_iron_court_ui_map.lua`, not `..._map.lua`.** `script/campaign/mod/` loads in name order and `_map` sorts before `_ui`, which would run before `ICUI` exists. `_ui.lua` sorts before `_ui_map.lua` (`.` is below `_`).
3. **No Esc handling.** The court has none, and no shortcut event is verified in CA's docs. The ways out are the legend's close button, a selection, and ending the turn.
4. **A governed province's marker opens the picker to REPLACE its governor.** The Governors tab releases on that click; the map opens the picker for both, because `IC.assign_governor` overwrites and the spec's click is "choose its governor". The tooltip line says so, and `IC.assign_governor` now writes the replaced man's leaving to the Record (Task 3).
5. **The two rings are generated art, not CA paths.** A brass ring and a red ring made by the same generator as the discs; no CA file had the right shape at 60px, and generated art needs no extraction.
6. **The legend sits at the top-left corner, 16px in,** not "under the top bar": the map hides the HUD, so there is no top bar to sit under.
7. **The map layouts are never scaled and have no compact copies,** like the opener: a 455px legend fits every supported screen.
8. **The map hides the HUD BEFORE it creates its layer,** so `ICUI.show_hud` needs no exemption and no change. `show_hud(false)` hides every visible root child but the court panel, and a layer created first would hide itself. Two hides in a row would REPLACE the first's record with an empty one and strand the HUD, so `map_open` closes the court and any existing map (both restore) before it hides; and the only other way into the court, the opener button, is in the HUD the map hides.
9. **A marker is ONE component with no children.** CA's `template_black_tower_slot` is a plain 56x170 holder carrying the two callbacks, with its art in children docked inside it. Ours cannot dock children: the engine ignores offsets and dockpoints on runtime-created components (measured 2026-09-04; the comment in `gen_iron_court_emitter._state` and `docs/CUSTOM_UI.md`), and there is no `MoveTo` for a child of something the engine moves every frame. So the disc, crest, both rings and the name's dark plate are image LAYERS of the marker, placed by image offsets inside its box, and the name is the marker's own text, bottom-aligned.
10. **The listeners register through `ICUI.register`,** wrapped by the map file, not from a second `cm:add_first_tick_callback`. The panel file registers from the first tick; the harness's stub keeps ONE first-tick function, so a second would silently replace the court's.
11. **Cancelling the picker is the court's close button,** which returns to the map; a tab click stays in the court (Task 3).
12. **The legend PAGES.** The spec's "one row per party in court (six at most)" is wrong: `rivals_max` reaches 5 on the hardest setting, a Crown split seats more of the nine parties, and every absorbed Chaos Dwarf faction adds its house on top (`IC.MAX_SEATS` = 9 + 12). Seven fixed rows would silently drop parties. Seven row slots stay, with the court's own pager under them (Previous / "Page N of M" / Next, the same plate and captions), shown only when the rows run past one page. "No governor" is always the last row.

## Review Focus

1. **Opening the map twice** must leave ONE layer, and the HUD must still come back after the map and then the court both close. Test in Task 1 ("closing the party map returns to the court...", which opens it twice).
2. **A province lost between drawing the map and clicking its marker** must not reach `IC.assign_governor`, which does not check ownership. Test in Task 3.
3. **Ending the turn in the court opened from the map** must clear the "return to the map" flag, or the next ordinary close of the court opens the map. Test in Task 4.
4. **A player holding no province** gets an empty map with a legend that says so, and no error. Test in Task 2.
5. **More parties than the legend has rows** must page, with "No governor" still reachable and a choice made on page two framed and ringed there. Test in Task 2 ("a court with more parties than rows pages its legend").

---

### Task 1: Phase 0 - the Map tab, the layer and pinned markers (in-game probe)

**Files:**
- Modify: `tools/gen_iron_court_emitter.py` (`component()` - the `colour_from` block ~line 280)
- Modify: `tools/gen_ic_ui.py` (`GUID_PREFIXES` ~line 82; `PANEL_LAYOUT` tab entries ~lines 204-229; `build_plates()` ~line 2593; new map section after `check_burst` ~line 4260; `ui_file_names()` ~line 3925; `build_xml()` ~line 4311; `check()` ~line 4528; `NOT_GEOMETRY` ~line 3666; the tab-caption measure `_bar[...]` ~line 5847; `selftest()` ~line 6702)
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua` (`ICUI.PANEL_XY` tab entries ~lines 258-268; tab captions ~line 6274; exports at the end of the file)
- Create: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui_map.lua`
- Modify: `tools/_iron_court_harness.lua` (region stub ~line 309; loader ~line 3829; new helper `with_fake_map`; new checks)
- Modify: `tools/import_iron_court.py` (`SCRIPTS` line 25), `tools/deploy_iron_court.py` (`SCRIPTS` ~line 65), `tools/mutate_iron_court.py` (file aliases ~line 40), `tools/sync_iron_court_repo.py` (manifest)

**Interfaces:**
- Produces (Lua, all on `ICUI`): `comp, set_text, loc, show, root` (exports of the panel file's locals); `MAP = "ic_map"`, `PATH_MAP`, `PATH_MARKER`, `MARKER = "ic_map_mk"`, `MAP_TAB = "ic_tab_map"`, `MK_PLATE, MK_CREST, MK_CAPITAL, MK_OUTLINE` (0-3), `MK_RING_CAPITAL`, `MK_RING_OUTLINE`, `MAP_XY` (legend component -> {x, y, w, h}), `MAP_ROW`, `MAP_ROWS`, `MAP_ROW_X/Y/W/H`, `MAP_ROW_CHILD`, `MAP_ROW_SEL`, `map_keys` (marker index -> province key), `map_disc(slug) -> path`, `map_region(faction_key, province_key) -> region|nil`, `map_open()`, `map_close()`, `map_layout(layer)`, `map_draw(faction_key, layer)`, `map_register()` (called from the wrapped `ICUI.register`; later tasks add their listeners INSIDE it).
- Produces (Python): `MAP_FILE`, `MARKER_FILE`, `map_disc_path(slug)`, `map_disc_pixels(hexcol)`, `map_ring_pixels(hexcol)`, `MAP_RING_CAPITAL`, `MAP_RING_OUTLINE`, `MAP_PIN`, `MAP_FADE`, `MAP_LAYOUT`, `MAP_ROW_CHILD`, `MARKER_LAYERS`, `map_xml()`, `marker_xml()`, `check_map()`; emitter kwarg `callbacks=[...]`.
- Produces (harness): `with_fake_map(fn)` - `fn(hud, panel, extra, layer)` where `layer()` is the live map layer or nil; `map_click(id)` - fires every click listener the way the engine does.

- [ ] **Step 1: Snapshot the generated layouts**

The emitter change in Step 5 must not alter one byte of the existing fifteen files.

Run: `py -c "import hashlib,glob; [print(hashlib.md5(open(p,'rb').read()).hexdigest(), p) for p in sorted(glob.glob('Modding Files/pack/ui/campaign ui/derpy_ic_*.twui.xml'))]" > "$TMP/ic_twui_before.txt"; cat "$TMP/ic_twui_before.txt" | wc -l`
Expected: `15`. (`$TMP` is the session scratchpad.)

- [ ] **Step 2: Extend the harness region stub**

In `tools/_iron_court_harness.lua`, `region_list = function()` inside the faction stub (~line 309): regions may now come with extra non-capital regions listed FIRST, and every region answers `is_province_capital()` and `settlement():cqi()`. Replace the `region_list = function()` entry's opening and the `item_at` head:

```lua
        -- One region per province, which is the shape IC.seats dedupes over,
        -- plus f._extra_regions ({province, name, cqi}) listed FIRST: a minor
        -- region ahead of its province's capital is the case the party map's
        -- marker has to get right. (home_region answers item 0, so it is the
        -- extra region while one is set - same province, so the capital
        -- province does not change.)
        region_list = function()
            local extra = f._extra_regions or {}
            return {
                num_items = function() return #extra + #provinces end,
                item_at = function(_, i)
                    if i < #extra then
                        local e = extra[i + 1]
                        return {
                            is_null_interface = function() return false end,
                            name = function() return e.name end,
                            province_name = function() return e.province end,
                            is_province_capital = function() return false end,
                            province = function()
                                return {is_null_interface = function() return false end,
                                        key = function() return e.province end}
                            end,
                            settlement = function()
                                return {is_null_interface = function() return false end,
                                        cqi = function() return e.cqi end}
                            end,
                        }
                    end
                    i = i - #extra
                    local key = provinces[i + 1]
```

(the rest of the existing `item_at` body stays as it is). Inside that body's returned table, beside `province = function()`, add:

```lua
                        -- THE PROVINCE CAPITAL unless f._not_capital says otherwise.
                        is_province_capital = function()
                            return not (f._not_capital or {})[key]
                        end,
```

and inside its `settlement = function()` table, beside `logical_position_x`, add:

```lua
                                cqi = function() return 700 + i end,
```

- [ ] **Step 3: Load the map file in the harness and add `with_fake_map`**

After the panel file loads (`assert(ICUI, "the panel file must define ICUI")`, ~line 3834), add:

```lua
local MAP_FILE = (arg and arg[4])
    or "Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui_map.lua"
local map_chunk, map_err = loadfile(MAP_FILE)
assert(map_chunk, "could not load the party map file: " .. tostring(map_err))
map_chunk()
assert(ICUI.map_open, "the party map file must define ICUI.map_open")
```

After `with_fake_panel` (~line 5395), add:

```lua
-- THE PARTY MAP'S LAYER ON THE FAKE ROOT. with_fake_root answers the panel and
-- the HUD; this adds the map layer (with the legend's components, as its
-- .twui.xml declares them) and markers created inside it. `layer()` hands back
-- the live layer, nil once destroyed.
--
-- AND A COURT THAT IS REALLY GONE. with_fake_root keeps answering the panel
-- after close() destroyed it, so a reopen there only refreshes and never runs
-- open()'s own work - the HUD hide included. The map's round trips close and
-- reopen the court, so here a destroyed panel is gone and a new one is built.
local function with_fake_map(fn)
    with_fake_root(function(hud, panel, extra)
        local r = extra.root
        local court_create = r.CreateComponent
        local layer = nil
        function r:CreateComponent(name, path)
            if name == ICUI.PANEL then panel.destroyed = nil end
            if name ~= ICUI.MAP then return court_create(self, name, path) end
            extra.paths[name] = path
            layer = fake_component(ICUI.MAP)
            layer.parent = r
            for n in pairs(ICUI.MAP_XY) do layer:CreateComponent(n) end
            for i = 1, ICUI.MAP_ROWS do
                layer:CreateComponent(ICUI.MAP_ROW .. "_" .. i)
                local row = layer.children[ICUI.MAP_ROW .. "_" .. i]
                for n in pairs(ICUI.MAP_ROW_CHILD) do row:CreateComponent(n) end
            end
            local make = layer.CreateComponent
            function layer:CreateComponent(n, p)
                extra.paths[n] = p
                return make(self, n, p)
            end
            r.children[name] = layer
            r.order[#r.order + 1] = layer
        end
        local find = find_uicomponent
        find_uicomponent = function(parent, name)
            if parent == nil or parent == r then
                if name == ICUI.MAP then
                    return (layer and not layer.destroyed) and layer or false
                end
                if name == ICUI.PANEL and panel.destroyed then return false end
            end
            return find(parent, name)
        end
        ICUI.register()
        local ok, err = pcall(fn, hud, panel, extra, function()
            return (layer and not layer.destroyed) and layer or nil
        end)
        find_uicomponent = find
        if not ok then error(err, 0) end
    end)
end

-- A CLICK, as the engine reports it: every ComponentLClickUp listener sees it.
-- core.listeners keeps one function per name, so the court's and the map's are
-- fired by name, the court's first.
local function map_click(id)
    for _, name in ipairs({"ic_click", "ic_map_click"}) do
        local fire = core.listeners[name]
        if fire then fire({string = id}) end
    end
end
```

- [ ] **Step 4: Write the failing checks**

Above the final check:

```lua
check("the Map tab opens the party map: one pinned marker per province, HUD hidden",
function()
    IC.state = {}
    turn = 1
    local gov = make_character(801, ANY_SEAT, "legion")
    make_faction(F, IC.CHD_SUBCULTURE, {gov}, {"prov_a", "prov_b"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    IC.court(F).govs["prov_a"] = 801
    with_fake_map(function(hud, panel, extra, layer)
        ICUI.open()
        map_click(ICUI.MAP_TAB)
        assert(panel.destroyed, "the court stayed open under the map")
        local l = layer()
        assert(l, "no map layer was created")
        assert(extra.paths[ICUI.MAP] == ICUI.PATH_MAP, "the layer came from " .. tostring(extra.paths[ICUI.MAP]))
        assert(l.resized and l.w == extra.root.w and l.h == extra.root.h,
            "the layer kept its file's size, not the screen's")
        assert(l.visible == true, "the map hid its own layer")
        assert(hud.visible == false, "the HUD shows over the party map")
        local a, b = l.children[ICUI.MARKER .. "_1"], l.children[ICUI.MARKER .. "_2"]
        assert(a and b, "not one marker per province")
        assert(extra.paths[ICUI.MARKER .. "_1"] == ICUI.PATH_MARKER, "a marker from the wrong file")
        -- PINNED: the settlement's own context, the id form Fortified Camps attests.
        assert(a.context and a.context.cco == "CcoCampaignSettlement" and a.context.id == "700",
            "the first marker was given " .. tostring(a.context and a.context.id))
        assert(b.context.id == "701", "the second marker was given " .. tostring(b.context.id))
        assert(a.images[ICUI.MK_PLATE] == ICUI.map_disc("legion"), "prov_a's plate: " .. tostring(a.images[ICUI.MK_PLATE]))
        assert(b.images[ICUI.MK_PLATE] == ICUI.map_disc(nil), "ungoverned prov_b's plate: " .. tostring(b.images[ICUI.MK_PLATE]))
        assert(a.images[ICUI.MK_CAPITAL] == ICUI.MK_RING_CAPITAL, "the capital's province wears no ring")
        assert(b.images[ICUI.MK_CAPITAL] == ICUI.MASK_NONE, "another province wears the capital ring")
        -- THE NAME IS THE MARKER'S OWN TEXT (ruling 9); the loc stub answers
        -- nothing, so the province key is the fallback.
        assert(a.text == "prov_a", "the name reads " .. tostring(a.text))
        assert(next(a.children) == nil, "a marker grew a child, which the engine would draw at its corner")
        assert(ICUI.map_keys[1] == "prov_a" and ICUI.map_keys[2] == "prov_b", "the click keys do not follow the markers")
    end)
end)

check("a province's marker stands on its capital settlement, else the first held one",
function()
    IC.state = {}
    local f = make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a", "prov_b"})
    -- A MINOR REGION OF prov_a LISTED FIRST: a first-found search answers it,
    -- the map must not.
    f._extra_regions = {{province = "prov_a", name = "region_prov_a_minor", cqi = 950}}
    local r = ICUI.map_region(F, "prov_a")
    assert(r and r:name() == "region_prov_a", "prov_a's marker stands on " .. tostring(r and r:name()))
    -- NO CAPITAL HELD: the first region of the province.
    f._not_capital = {prov_b = true}
    local s = ICUI.map_region(F, "prov_b")
    assert(s and s:name() == "region_prov_b", "prov_b fell back to " .. tostring(s and s:name()))
    f._extra_regions, f._not_capital = nil, nil
end)

check("closing the party map returns to the court on Governors and gives the HUD back",
function()
    IC.state = {}
    make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a"})
    IC.add_house(F, IC.CROWN)
    with_fake_map(function(hud, panel, extra, layer)
        -- THE WAY A PLAYER GETS THERE: the court, then its Map tab.
        ICUI.open()
        ICUI.view = "intrigue"
        map_click(ICUI.MAP_TAB)
        -- AND A SECOND OPEN over the first: one layer, not two stacked.
        local first = layer()
        ICUI.map_open()
        assert(layer() and layer() ~= first, "the second open did not replace the first")
        assert(first.destroyed, "the first layer is still on the root under the second")
        assert(hud.visible == false, "the HUD came back while the map was up")
        map_click("ic_map_close")
        assert(not layer(), "the map layer outlived its close button")
        assert(not panel.destroyed, "the court did not come back")
        assert(ICUI.view == "govs", "the court came back on " .. tostring(ICUI.view))
        assert(hud.visible == false, "the HUD shows over the court")
        ICUI.close()
        assert(hud.visible == true, "the HUD stayed hidden after the map and the court both closed")
        assert(extra.menu.visible == true and extra.icons.visible == true,
            "a sibling of the HUD stayed hidden")
        assert(extra.asleep.visible == false, "a panel that was already closed was opened")
    end)
end)
```

- [ ] **Step 5: Run the harness, verify it fails**

Run: `"/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua`
Expected: FAIL at load: `could not load the party map file` (the file does not exist yet).

- [ ] **Step 6: Emitter - general callbacks**

In `tools/gen_iron_court_emitter.py`, `component()`, replace the whole `cc = kw.get("colour_from")` block (from `cc = kw.get("colour_from")` through its closing `% (_esc(cc["object"]), _esc(cc["function"]), cc["index"]))`) with:

```python
    # CALLBACKS. colour_from is the one with a shorthand; `callbacks` takes any
    # other as {"id", "object"?, "function"?, "props": [(name, value)]} - the party
    # map's markers carry CA's ContextWorldSpaceComponent and ContextOpacitySetter
    # this way. The colour setter's output is byte-identical to before.
    cbs = []
    cc = kw.get("colour_from")
    if cc:
        cbs.append({"id": "ContextColourSetter", "object": cc["object"],
                    "function": cc["function"],
                    "props": [("colour_index0", str(cc["index"]))]})
    cbs.extend(kw.get("callbacks") or [])
    if cbs:
        out += '\t\t\t<callbackwithcontextlist>\n'
        for cb in cbs:
            out += '\t\t\t\t<callback_with_context\n\t\t\t\t\tcallback_id="%s"' % cb["id"]
            if cb.get("object"):
                out += '\n\t\t\t\t\tcontext_object_id="%s"' % _esc(cb["object"])
            if cb.get("function"):
                out += '\n\t\t\t\t\tcontext_function_id="%s"' % _esc(cb["function"])
            props = cb.get("props") or []
            if not props:
                out += '/>\n'
                continue
            out += '>\n\t\t\t\t\t<child_m_user_properties>\n'
            for name, value in props:
                out += ('\t\t\t\t\t\t<property\n\t\t\t\t\t\t\tname="%s"\n'
                        '\t\t\t\t\t\t\tvalue="%s"/>\n' % (_esc(name), _esc(value)))
            out += '\t\t\t\t\t</child_m_user_properties>\n\t\t\t\t</callback_with_context>\n'
        out += '\t\t\t</callbackwithcontextlist>\n'
```

- [ ] **Step 7: Generator - the tab slot, the art and the two files**

In `tools/gen_ic_ui.py`:

(a) `GUID_PREFIXES`, after `"derpy_ic_plot_compact.twui.xml": "IC44",`:

```python
    # IC45-IC46 - THE PARTY MAP (spec 2026-09-29): the root-level layer with the
    # legend, and the marker created into it once per province. Never scaled.
    "derpy_ic_map.twui.xml":        "IC45",
    "derpy_ic_map_marker.twui.xml": "IC46",
```

(b) `PANEL_LAYOUT`: the Map tab after Governors; Intrigue, Petitions and Record each move one slot right, and Petitions' mark with it. Replace the four tab entries and the petitions mark with:

```python
    "ic_tab_govs": (506, 62, 240, 32),
    # THE PARTY MAP (spec 2026-09-29): after Governors, its sibling. Not a view -
    # its click closes the court (zzz_derpy_iron_court_ui_map.lua).
    "ic_tab_map": (750, 62, 240, 32),
    "ic_tab_intrigue": (994, 62, 240, 32),
    "ic_tab_petitions": (1238, 62, 240, 32),
    "ic_tab_log": (1482, 62, 240, 32),
```

keeping each entry's existing comment above it, and `"ic_mark_petitions": (1238 + 240 - 34, 64, 28, 28),`.

(c) The tab caption measure, beside `_bar["ic_tab_petitions"] = ["Petitions"]`: `_bar["ic_tab_map"] = ["Map"]`.

(d) The map section, after `check_burst`:

```python
# ---------------------------------------------------------------------------
# THE PARTY MAP (spec 2026-09-29-iron-court-party-map-design.md). Two files, both
# created at runtime and never scaled (ruling 7). The layer is a root child that
# holds the legend; each marker is created inside it, one per province, and
# pinned to its settlement by CA's own world-space callback.
MAP_FILE = "derpy_ic_map.twui.xml"
MARKER_FILE = "derpy_ic_map_marker.twui.xml"
MAP_DISC = 48                       # the plate
MAP_CREST = 28
MAP_RING = 60                       # both rings, around the plate
MAP_NAME_W, MAP_NAME_H = 200, 24
MARKER_W, MARKER_H = MAP_NAME_W, MAP_RING + MAP_NAME_H
MAP_DISC_NONE = "#6B5A3AFF"         # bronze: a province with no governor
MAP_RING_CAPITAL = PLATE_DIR + "/map_ring_capital.png"
MAP_RING_OUTLINE = PLATE_DIR + "/map_ring_outline.png"
MAP_RING_CAPITAL_COLOUR = "#C9A45AFF"
MAP_RING_OUTLINE_COLOUR = "#D0342AFF"
# CA'S TWO CALLBACKS, VERBATIM from dlc25_black_towers.twui.xml's
# template_black_tower_slot. check_map() holds the emitted file to these.
MAP_PIN = {"id": "ContextWorldSpaceComponent", "object": "CcoCampaignSettlement",
           "function": "Position", "props": [("depth_disabled", "1")]}
MAP_FADE = {"id": "ContextOpacitySetter",
            "function": ("(pos = self.Position.y) => {pos | CampaignRoot.IsTacticalViewActive"
                         " => 1 | pos < 0 => 0 | pos < 50 => pos/50.0 | 1}"),
            "props": [("propagate", ""), ("update_constant", "")]}
# THE LEGEND, top-left (ruling 6). Must match ICUI.MAP_XY and ICUI.MAP_ROW_* in
# zzz_derpy_iron_court_ui_map.lua; check_map() holds the two together.
MAP_LAYOUT = {
    "ic_map_legend": (16, 16, 455, 556),
    "ic_map_title": (32, 26, 360, 30),
    "ic_map_close": (411, 20, 48, 48),
    # THE COURT'S PAGER, same sizes (ruling 12): 136 holds "Previous", 159 holds
    # "Page 99 of 99". Under the seventh row (76 + 7 * 56 = 468).
    "ic_map_prev": (24, 470, 136, 34),
    "ic_map_page": (164, 474, 159, 26),
    "ic_map_next": (327, 470, 136, 34),
    "ic_map_hint_1": (32, 512, 423, 24),
    "ic_map_hint_2": (32, 536, 423, 24),
}
MAP_ROW_X, MAP_ROW_Y, MAP_ROW_W, MAP_ROW_H, MAP_ROWS = 24, 76, 439, 56, 7
MAP_ROW_CHILD = {
    "ic_map_sw": (8, 8, 36, 36),
    "ic_map_name": (56, 2, 375, 24),
    "ic_map_gov": (56, 28, 170, 22),
    "ic_map_take": (232, 28, 200, 22),
}


def map_disc_path(slug):
    return "%s/map_disc_%s.png" % (PLATE_DIR, slug or "none")


def _map_supersample(size, inside_fn):
    """Coverage of each pixel by a shape, 4x4 supersampled: 0..16."""
    rows = []
    for y in range(size):
        row = []
        for x in range(size):
            n = 0
            for sy in range(4):
                for sx in range(4):
                    if inside_fn(x + (sx + 0.5) / 4.0, y + (sy + 0.5) / 4.0):
                        n += 1
            row.append(n)
        rows.append(row)
    return rows


def map_disc_pixels(hexcol, size=MAP_DISC):
    """A round plate in one colour with a darker 3px rim."""
    r, g, b = int(hexcol[1:3], 16), int(hexcol[3:5], 16), int(hexcol[5:7], 16)
    c = size / 2.0
    rad = size / 2.0 - 0.5
    cover = _map_supersample(size, lambda x, y: ((x - c) ** 2 + (y - c) ** 2) ** 0.5 <= rad)
    rim = _map_supersample(size, lambda x, y: rad - 3 < ((x - c) ** 2 + (y - c) ** 2) ** 0.5 <= rad)
    out = []
    for y in range(size):
        row = bytearray()
        for x in range(size):
            k = 0.55 if rim[y][x] * 2 > cover[y][x] > 0 else 1.0
            row += bytearray((int(r * k), int(g * k), int(b * k), cover[y][x] * 255 // 16))
        out.append(bytes(row))
    return out


def map_ring_pixels(hexcol, size=MAP_RING, width=4):
    """A ring of `width` px at the edge of a `size` square, transparent inside."""
    r, g, b = int(hexcol[1:3], 16), int(hexcol[3:5], 16), int(hexcol[5:7], 16)
    c = size / 2.0
    outer = size / 2.0 - 0.5
    cover = _map_supersample(
        size, lambda x, y: outer - width < ((x - c) ** 2 + (y - c) ** 2) ** 0.5 <= outer)
    return [bytes(bytearray(v for n in row for v in (r, g, b, n * 255 // 16)))
            for row in cover]


def _map_layer(path, size):
    """A square image of `size`, centred across the marker, its centre MAP_RING/2 down."""
    return {"path": path, "offset": ((MARKER_W - size) / 2.0, (MAP_RING - size) / 2.0),
            "dw": size - MARKER_W, "dh": size - MARKER_H, "margin": 0, "dock": None}


# THE MARKER'S LAYERS THE LUA REPAINTS, IN ORDER. Must match
# ICUI.MK_PLATE/CREST/CAPITAL/OUTLINE. The name's plate follows them and is
# never repainted.
MARKER_LAYERS = ["plate", "crest", "capital", "outline"]


def _map_marker():
    # ONE COMPONENT, NO CHILDREN (plan ruling 9). CA's slot docks its art in
    # children; a runtime child ignores its offset and draws at the corner of
    # something the engine moves every frame. So the art is image layers placed
    # by their own offsets, and the name is the marker's own text, on a dark
    # plate at the bottom so it reads over any terrain. Written from Lua, never a
    # live ContextTextLabel, which would re-render over it.
    root = EU.C("root", MARKER_W, MARKER_H)
    root.add(EU.C(
        "derpy_ic_map_marker", MARKER_W, MARKER_H, interactive=True,
        sound=OPENER_SOUND, callbacks=[MAP_PIN, MAP_FADE],
        layers=[_map_layer(map_disc_path(None), MAP_DISC),
                _map_layer(MASK_NONE, MAP_CREST),
                _map_layer(MASK_NONE, MAP_RING),
                _map_layer(MASK_NONE, MAP_RING),
                {"path": plate_path(None), "offset": (0, MAP_RING), "dw": 0,
                 "dh": MAP_NAME_H - MARKER_H, "margin": 0, "dock": None}],
        **style("ic_mk_name", align="Center", valign="Bottom",
                tx="0.00,0.00", ty="0.00,0.00")))
    return root


def _map_layer_file():
    root = EU.C("root", 1920, 1080)
    layer = root.add(EU.C("derpy_ic_map", 1920, 1080))
    # THE LAYER ITSELF IS NOT INTERACTIVE: the bare map around the legend must
    # still take clicks and drags. THE LEGEND IS - a click on its blank plate
    # would otherwise fall through and select whatever stands under it.
    x, y, w, h = MAP_LAYOUT["ic_map_legend"]
    layer.add(EU.C("ic_map_legend", w, h, image=plate_path(None), interactive=True))
    x, y, w, h = MAP_LAYOUT["ic_map_title"]
    layer.add(EU.C("ic_map_title", w, h, **style("ic_map_title", valign="Center")))
    x, y, w, h = MAP_LAYOUT["ic_map_close"]
    layer.add(EU.C("ic_map_close", w, h, interactive=True, sound=OPENER_SOUND,
                   layers=CLOSE_LAYERS, hover=CLOSE_HOVER, tooltip="Back to the court"))
    for key in ("ic_map_prev", "ic_map_next"):
        x, y, w, h = MAP_LAYOUT[key]
        layer.add(EU.C(key, w, h, interactive=True, sound=OPENER_SOUND,
                       layers=PAGE_LAYERS, hover=PAGE_HOVER, **TAB_TEXT))
    x, y, w, h = MAP_LAYOUT["ic_map_page"]
    layer.add(EU.C("ic_map_page", w, h, **style("ic_map_page", align="Center",
                                                   valign="Center", tx="0.00,0.00")))
    for key in ("ic_map_hint_1", "ic_map_hint_2"):
        x, y, w, h = MAP_LAYOUT[key]
        layer.add(EU.C(key, w, h, **style(key, valign="Center")))
    for i in range(1, MAP_ROWS + 1):
        row = layer.add(EU.C(
            "ic_map_row_%d" % i, MAP_ROW_W, MAP_ROW_H, interactive=True,
            sound=OPENER_SOUND,
            layers=[{"path": MASK_NONE, "offset": (0, 0), "dw": 0, "dh": 0,
                     "margin": TEXTURE_MIN_MARGIN[PARTY_SELECTED], "dock": None}]))
        cx, cy, cw, ch = MAP_ROW_CHILD["ic_map_sw"]
        row.add(EU.C("ic_map_sw", cw, ch, layers=[
            {"path": map_disc_path(None), "offset": (0, 0), "dw": 0, "dh": 0,
             "margin": 0, "dock": None},
            {"path": MASK_NONE, "offset": (6, 6), "dw": -12, "dh": -12,
             "margin": 0, "dock": None}]))
        for key in ("ic_map_name", "ic_map_gov", "ic_map_take"):
            cx, cy, cw, ch = MAP_ROW_CHILD[key]
            row.add(EU.C(key, cw, ch, **style(key, valign="Center")))
    return root


def map_xml():
    return EU.layout(EU.assign(_map_layer_file(), GUID_PREFIXES[MAP_FILE]),
                     "derpy: the Iron Court's party map layer and legend. Created at "
                     "runtime at the ui root; generated by tools/gen_ic_ui.py.")


def marker_xml():
    return EU.layout(EU.assign(_map_marker(), GUID_PREFIXES[MARKER_FILE]),
                     "derpy: one Iron Court party map marker, pinned to a settlement "
                     "by CA's ContextWorldSpaceComponent; generated by tools/gen_ic_ui.py.")


def _lua_map_tables():
    ui = os.path.join(ROOT, "Modding Files", "pack", "script", "campaign", "mod",
                      "zzz_derpy_iron_court_ui_map.lua")
    return io.open(ui, encoding="utf-8").read()


def check_map(marker_text=None, lua_text=None):
    """CA's callbacks verbatim on the marker, and the Lua's numbers equal to ours."""
    out = []
    t = marker_text if marker_text is not None else marker_xml()
    for cb in (MAP_PIN, MAP_FADE):
        if 'callback_id="%s"' % cb["id"] not in t:
            out.append("%s: no %s callback" % (MARKER_FILE, cb["id"]))
        if cb.get("function") and 'context_function_id="%s"' % EU._esc(cb["function"]) not in t:
            out.append("%s: %s's function is not CA's" % (MARKER_FILE, cb["id"]))
    if 'context_object_id="CcoCampaignSettlement"' not in t:
        out.append("%s: the pin is not on CcoCampaignSettlement" % MARKER_FILE)
    if 'name="depth_disabled"' not in t:
        out.append("%s: the pin lost depth_disabled" % MARKER_FILE)
    # ROOT AND MARKER, NOTHING ELSE (ruling 9): a child would draw at the corner.
    ids = re.findall(r'\n\t\t\tid="([^"]+)"', t)
    if ids != ["root", "derpy_ic_map_marker"]:
        out.append("%s: components %r - the marker may have no children" % (MARKER_FILE, ids))
    lua = lua_text if lua_text is not None else _lua_map_tables()
    for i, name in enumerate(MARKER_LAYERS):
        if not re.search(r"ICUI\.MK_%s\b[^\n]*" % name.upper(), lua):
            out.append("the map Lua declares no ICUI.MK_%s" % name.upper())
    m = re.search(r"ICUI\.MK_PLATE,\s*ICUI\.MK_CREST,\s*ICUI\.MK_CAPITAL,\s*"
                  r"ICUI\.MK_OUTLINE\s*=\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)", lua)
    if not m or [int(v) for v in m.groups()] != list(range(len(MARKER_LAYERS))):
        out.append("ICUI.MK_* do not name the marker's layers 0..3 in order")
    for key, box in MAP_LAYOUT.items():
        got = re.search(r"\b%s\s*=\s*\{\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\s*\}" % key, lua)
        if not got or tuple(int(v) for v in got.groups()) != box:
            out.append("ICUI.MAP_XY.%s is not %r" % (key, box))
    for key, box in MAP_ROW_CHILD.items():
        got = re.search(r"\b%s\s*=\s*\{\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\s*\}" % key, lua)
        if not got or tuple(int(v) for v in got.groups()) != box:
            out.append("ICUI.MAP_ROW_CHILD.%s is not %r" % (key, box))
    rows = re.search(r"ICUI\.MAP_ROW_X,\s*ICUI\.MAP_ROW_Y,\s*ICUI\.MAP_ROW_W,\s*"
                     r"ICUI\.MAP_ROW_H,\s*ICUI\.MAP_ROWS\s*=\s*(\d+),\s*(\d+),\s*(\d+),"
                     r"\s*(\d+),\s*(\d+)", lua)
    if not rows or tuple(int(v) for v in rows.groups()) != (
            MAP_ROW_X, MAP_ROW_Y, MAP_ROW_W, MAP_ROW_H, MAP_ROWS):
        out.append("ICUI.MAP_ROW_* are not the generator's")
    return out
```

(e) `build_plates()`, before `out[MASK_NONE] = mask_pixels()`:

```python
    # THE PARTY MAP'S PLATES AND RINGS (spec 2026-09-29): a disc per party and
    # per absorbed faction, one for no governor, and the two rings.
    out[map_disc_path(None)] = map_disc_pixels(MAP_DISC_NONE)
    for p in IC.PARTIES:
        out[map_disc_path(p[0])] = map_disc_pixels(HOUSE_COLOUR[p[0]])
    for slug in CONFED_SEATS:
        out[map_disc_path(slug)] = map_disc_pixels(CONFED_COLOUR[slug])
    out[MAP_RING_CAPITAL] = map_ring_pixels(MAP_RING_CAPITAL_COLOUR)
    out[MAP_RING_OUTLINE] = map_ring_pixels(MAP_RING_OUTLINE_COLOUR)
```

(f) Register: `ui_file_names()` returns the two new names beside `BURST_FILE`; `build_xml()` adds `out[MAP_FILE] = map_xml()` and `out[MARKER_FILE] = marker_xml()` beside the burst line; `check()` adds `out.extend(check_map(all_files.get(MARKER_FILE, "")))` beside `check_burst`; add `"MAP_FILE", "MARKER_FILE", "MAP_DISC", "MAP_CREST", "MAP_RING", "MAP_NAME_W", "MAP_NAME_H", "MARKER_W", "MARKER_H", "MAP_DISC_NONE", "MAP_RING_CAPITAL", "MAP_RING_OUTLINE", "MAP_RING_CAPITAL_COLOUR", "MAP_RING_OUTLINE_COLOUR", "MAP_PIN", "MAP_FADE", "MAP_LAYOUT", "MAP_ROW_X", "MAP_ROW_Y", "MAP_ROW_W", "MAP_ROW_H", "MAP_ROWS", "MAP_ROW_CHILD", "MARKER_LAYERS"` to `NOT_GEOMETRY`. (`style()` falls back to `BODY` for a name with no `TEXT_STYLE` entry, so the new text cells need none.) `write_plates()` prunes anything under `ui/derpy_ic/` that is not in `art_paths()`; the new art is safe because `art_paths()` starts from `set(build_plates())` - confirm that line is still there.

(g) `selftest()`, beside the burst selftest:

```python
    assert not check_map(), check_map()
    assert check_map(marker_xml().replace("ContextWorldSpaceComponent", "ContextX")), \
        "check_map passed a marker with no world-space pin"
    assert check_map(lua_text=_lua_map_tables().replace("ic_map_close  = {411", "ic_map_close  = {412")), \
        "check_map passed a legend the Lua places elsewhere"
    assert any("no children" in e for e in check_map(map_xml())), \
        "check_map passed a marker file with children in it"
```

- [ ] **Step 8: Panel Lua - the tab and the exports**

In `zzz_derpy_iron_court_ui.lua`:

`ICUI.PANEL_XY`, the tabs and the petitions mark, to match (b):

```lua
    ic_tab_govs      = {506, 62, 240, 32},
    ic_tab_map       = {750, 62, 240, 32},
    ic_tab_intrigue  = {994, 62, 240, 32},
    ic_tab_petitions = {1238, 62, 240, 32},
    ic_tab_log       = {1482, 62, 240, 32},
```

and `ic_mark_petitions = {1444, 64, 28, 28},`.

Beside `set_text(comp("ic_tab_govs", panel), "Governors")`: `set_text(comp("ic_tab_map", panel), "Map")`.

`ICUI.show_hud` is NOT touched (ruling 8).

At the very end of the file:

```lua
-- FOR zzz_derpy_iron_court_ui_map.lua, which loads after this file:
-- script/campaign/mod loads in name order, and "_ui." sorts before "_ui_map".
ICUI.comp, ICUI.set_text, ICUI.loc, ICUI.show, ICUI.root = comp, set_text, loc, show, root
```

- [ ] **Step 9: The map Lua**

Create `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui_map.lua`:

```lua
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
        -- ScreenSizedComponent, and markers are this layer's children.
        layer:SetCanResizeWidth(true)
        layer:SetCanResizeHeight(true)
        layer:Resize(root():Dimensions())
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
```

- [ ] **Step 10: Register the file with the tools**

- `tools/import_iron_court.py`: `MAP_LUA = "Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui_map.lua"` beside `UI_LUA`; `SCRIPTS = [MODEL_LUA, UI_LUA, PARTIES_LUA, MCT_LUA, MAP_LUA]`.
- `tools/deploy_iron_court.py` `SCRIPTS`: add `("Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui_map.lua", "script/campaign/mod/zzz_derpy_iron_court_ui_map.lua"),`. Then `grep -n "ui_file_names\|twui" tools/deploy_iron_court.py`: if its layout list is typed rather than read from `gen_ic_ui.ui_file_names()`, add both new files to it.
- `tools/mutate_iron_court.py`: `UM = os.path.join(MOD, "zzz_derpy_iron_court_ui_map.lua")` beside `U`.
- `tools/sync_iron_court_repo.py` `manifest()`: `_MOD + "zzz_derpy_iron_court_ui_map.lua",` after the panel file; `_UI + "derpy_ic_map.twui.xml",` and `_UI + "derpy_ic_map_marker.twui.xml",` beside `derpy_ic_burst.twui.xml`.

- [ ] **Step 11: Generate, and prove the old files did not move**

Run: `py tools/gen_ic_ui.py` then the md5 command of Step 1 into `$TMP/ic_twui_after.txt`, then `diff <(grep -v "_map" "$TMP/ic_twui_after.txt") "$TMP/ic_twui_before.txt"`.
Expected: `derpy_ic_map.twui.xml` and `derpy_ic_map_marker.twui.xml` written; the diff shows ONLY `derpy_ic_panel.twui.xml` and `derpy_ic_panel_compact.twui.xml` (the new tab and the moved tabs). Any other file that changed means the emitter's callback block is not byte-identical: fix the emitter, not the file.

- [ ] **Step 12: Run the harness and the generator gates**

Run: `"/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua`
Expected: `iron court harness: ok (792 checks)`.
Run: `py tools/gen_ic_ui.py --check` then `py tools/gen_ic_ui.py --selftest`
Expected: `ok: 17 files, ...` and `selftest: ok`.

- [ ] **Step 13: Gates, build, deploy**

Run: `luac -p` on the five Iron Court Lua files; `py tools/check_lua_api.py` on them (0 suspects in these files); `py tools/check_lua_literal_left.py` on them; `py tools/import_iron_court.py` (verify only) -> `verify ok`; `py tools/preview_iron_court.py --check`.
Before building, note the file count the last deploy verified (the handoff records it). Then, with RPFM open: `py tools/deploy_iron_court.py`. Expected: `verified N file(s)` where N is that count plus 2 layouts, 1 script, 2 rings and one disc per party, per absorbed faction and for no governor (`1 + len(IC.PARTIES) + len(CONFED_SEATS)`); and, with the game shut, `deployed ... byte-identical to the build`. A different N means a file went missing or a stray one went in: find it before going on.

- [ ] **Step 14: STOP - the author's in-game check**

Report the build and ask the author to load a Chaos Dwarf campaign, open the court and click **Map**, then:
1. Does a coloured disc with a name sit ON each of your province capitals (not beside them)?
2. Pan and zoom the camera: do the markers stay on their settlements?
3. Near the top of the screen, do markers fade out?
4. Can you still drag the camera and click an army or settlement on bare map beside a marker?
5. Does the close button bring the court back, with the HUD back after the court closes?

Ledger the answers.
- **1 or 2 fail** (no marker, or markers that stay put while the camera moves): stop, report, and take the spec's section 10 (schematic) as a new plan.
- **1 lands offset but moves with the camera**: the engine places some point of the box other than the disc's centre on the settlement. CA's slot declares no anchor, so this plan declares none; the fix is CA's own attribute, `component_anchor_point` (used 10 times in the same CA file, e.g. `"0.50,1.00"`). Add to the emitter's `component()`, after the `soundcategory` block:
  ```python
      if kw.get("anchor"):
          attrs.append('component_anchor_point="%.2f,%.2f"' % kw["anchor"])
  ```
  and pass `anchor=(0.5, (MAP_RING / 2.0) / MARKER_H)` (the disc's centre) to the marker in `_map_marker()`; rebuild and ask again.
- **3 fails**: note it; it is cosmetic.
- **4 fails** (the map swallows clicks): stop and report - some part of the layer takes the mouse in a way this plan did not intend.

Tasks 2-5 start only after this answer.

---

### Task 2: The legend, and choosing a party

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui_map.lua`
- Modify: `tools/_iron_court_harness.lua`

**Interfaces:**
- Consumes: Task 1's `ICUI.map_*`, `ICUI.MAP_ROW*`, `ICUI.MK_*`.
- Produces: `ICUI.map_rows(faction_key) -> {{slug = slug|nil}, ...}` (court order, then `slug = nil` for "No governor"); `ICUI.map_outline(faction_key, slug) -> province_list, why|nil`; `ICUI.map_chosen` (a row of the whole legend, or nil); `ICUI.map_page` (0-based); `ICUI.map_pages(rows) -> n`; `ICUI.map_legend(faction_key, layer)`; `ICUI.map_ring(faction_key, layer)`.

- [ ] **Step 1: Write the failing checks**

```lua
check("the legend lists every party with what it governs and would take", function()
    IC.state = {}
    turn = 1
    local g1, g2 = make_character(811, ANY_SEAT, "legion"), make_character(812, ANY_SEAT, "legion")
    make_faction(F, IC.CHD_SUBCULTURE, {g1, g2}, {"prov_a", "prov_b", "prov_c"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    IC.court(F).govs["prov_b"] = 811
    IC.court(F).govs["prov_c"] = 812
    with_fake_map(function(hud, panel, extra, layer)
        ICUI.map_open()
        local l = layer()
        local rows = ICUI.map_rows(F)
        assert(#rows == 3 and rows[1].slug == IC.CROWN and rows[2].slug == "legion"
               and rows[3].slug == nil, "the legend's rows are not the court, then no governor")
        local legion = l.children[ICUI.MAP_ROW .. "_2"]
        assert(legion.visible == true, "the legion's row is hidden")
        assert(legion.children.ic_map_gov.text == "Governs 2", legion.children.ic_map_gov.text)
        local take = #IC.defecting_provinces(F, "legion")
        assert(legion.children.ic_map_take.text == string.format("Would take %d", take),
            "the take count reads " .. legion.children.ic_map_take.text)
        assert(legion.children.ic_map_sw.images[0] == ICUI.map_disc("legion"), "the legion's swatch")
        local none = l.children[ICUI.MAP_ROW .. "_3"]
        assert(none.children.ic_map_name.text == "No governor", none.children.ic_map_name.text)
        assert(none.children.ic_map_gov.text == "1 province", none.children.ic_map_gov.text)
        assert(l.children[ICUI.MAP_ROW .. "_4"].visible == false, "a spare row is drawn")
    end)
end)

check("choosing a party rings exactly what it would take, and again clears it", function()
    IC.state = {}
    turn = 1
    local g1 = make_character(821, ANY_SEAT, "legion")
    make_faction(F, IC.CHD_SUBCULTURE, {g1}, {"prov_a", "prov_b", "prov_c"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    IC.court(F).govs["prov_b"] = 821
    with_fake_map(function(hud, panel, extra, layer)
        ICUI.map_open()
        local l = layer()
        map_click(ICUI.MAP_ROW .. "_2")
        local want = {}
        for _, p in ipairs(IC.defecting_provinces(F, "legion")) do want[p] = true end
        assert(next(want), "the fixture's legion would take nothing, so this proves nothing")
        for i, p in pairs(ICUI.map_keys) do
            local ring = l.children[ICUI.MARKER .. "_" .. i].images[ICUI.MK_OUTLINE]
            assert((ring == ICUI.MK_RING_OUTLINE) == (want[p] == true),
                p .. " is ringed " .. tostring(ring))
        end
        assert(l.children[ICUI.MAP_ROW .. "_2"].images[ICUI.MAP_ROW_SEL] == ICUI.PARTY_SELECTED,
            "the chosen row wears no frame")
        map_click(ICUI.MAP_ROW .. "_2")
        for i in pairs(ICUI.map_keys) do
            assert(l.children[ICUI.MARKER .. "_" .. i].images[ICUI.MK_OUTLINE] == ICUI.MASK_NONE,
                "a second click left a ring")
        end
    end)
end)

check("rows that can ring nothing say why: the Crown, secession off, the grace period",
function()
    IC.state = {}
    make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    local list, why = ICUI.map_outline(F, IC.CROWN)
    assert(#list == 0 and why == "Your own house does not secede.", tostring(why))
    in_grace(function()
        turn = 4
        local l2, w2 = ICUI.map_outline(F, "legion")
        assert(#l2 == 0 and w2:find("7 more turns", 1, true), tostring(w2))
    end)
    local keep = IC.TUNE.secession
    IC.TUNE.secession = false
    local l3, w3 = ICUI.map_outline(F, "legion")
    IC.TUNE.secession = keep
    assert(#l3 == 0 and w3:find("switched off", 1, true), tostring(w3))
    -- "No governor" rings the ungoverned.
    local l4 = ICUI.map_outline(F, nil)
    assert(#l4 == 1 and l4[1] == "prov_a", "no governor rings " .. #l4)
end)

check("a realm with no province opens an empty map that says so", function()
    IC.state = {}
    make_faction(F, IC.CHD_SUBCULTURE, {}, {})
    IC.add_house(F, IC.CROWN)
    with_fake_map(function(hud, panel, extra, layer)
        ICUI.map_open()
        local l = layer()
        assert(l, "no layer for a realm with no province")
        assert(next(ICUI.map_keys) == nil, "a marker for no province")
        assert(l.children.ic_map_hint_1.text == "You hold no province.",
            l.children.ic_map_hint_1.text)
    end)
end)

check("a court with more parties than rows pages its legend", function()
    IC.state = {}
    turn = 1
    make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a", "prov_b"})
    for _, slug in ipairs(IC.PARTIES) do IC.add_house(F, slug) end
    with_fake_map(function(hud, panel, extra, layer)
        ICUI.map_open()
        local l = layer()
        local rows = ICUI.map_rows(F)
        assert(#rows > ICUI.MAP_ROWS, "the fixture fits one page, so this proves nothing")
        assert(l.children.ic_map_next.visible == true, "no pager for " .. #rows .. " rows")
        assert(l.children.ic_map_page.text == "Page 1 of 2", l.children.ic_map_page.text)
        map_click("ic_map_next")
        assert(l.children.ic_map_page.text == "Page 2 of 2", l.children.ic_map_page.text)
        -- "NO GOVERNOR" IS STILL THE LAST ROW, now on page two.
        local last = l.children[ICUI.MAP_ROW .. "_" .. (#rows - ICUI.MAP_ROWS)]
        assert(last.children.ic_map_name.text == "No governor",
            "the last row on page two reads " .. last.children.ic_map_name.text)
        -- A CHOICE ON PAGE TWO is the legend's row, framed on page two only.
        map_click(ICUI.MAP_ROW .. "_1")
        assert(ICUI.map_chosen == ICUI.MAP_ROWS + 1,
            "page two's first row chose row " .. tostring(ICUI.map_chosen))
        assert(l.children[ICUI.MAP_ROW .. "_1"].images[ICUI.MAP_ROW_SEL] == ICUI.PARTY_SELECTED,
            "the choice on page two wears no frame")
        map_click("ic_map_prev")
        assert(l.children[ICUI.MAP_ROW .. "_1"].images[ICUI.MAP_ROW_SEL] == ICUI.MASK_NONE,
            "page one's first row wears page two's frame")
        map_click("ic_map_prev")
        assert(l.children.ic_map_page.text == "Page 1 of 2", "Previous ran off the first page")
    end)
end)

check("an absorbed faction's party draws its own disc", function()
    local slug = IC.ORIGINS[1].slug
    assert(ICUI.map_disc(slug) == "ui/derpy_ic/map_disc_" .. slug .. ".png")
    -- THE FILE EXISTS: the generator writes one per absorbed faction.
    local f = io.open("Modding Files/pack/ui/derpy_ic/map_disc_" .. slug .. ".png", "rb")
    assert(f, "no disc was generated for " .. slug)
    f:close()
end)
```

If `IC.ORIGINS[1].slug` is not in `gen_ic_ui.CONFED_SEATS`, pick the first origin that is (print both lists to see).

- [ ] **Step 2: Run the harness, verify it fails**

Expected: FAIL on "the legend lists every party..." with `attempt to call field 'map_rows' (a nil value)`.

- [ ] **Step 3: Implement**

In the map file, before `function ICUI.map_close()`:

```lua
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
    if slug == IC.CROWN then return {}, "Your own house does not secede." end
    if not IC.secession_on() then
        local left = IC.grace_left()
        if IC.TUNE.secession ~= false and left > 0 then
            return {}, string.format("No party can break with you for %d more turn%s.",
                                     left, left == 1 and "" or "s")
        end
        return {}, "Secession is switched off: no party can break with you."
    end
    return IC.defecting_provinces(faction_key, slug) or {}, nil
end

ICUI.map_chosen = nil        -- a row of the whole legend, or nil
ICUI.map_page = 0            -- 0-based

function ICUI.map_ring(faction_key, layer)
    local ringed = {}
    local rows = ICUI.map_rows(faction_key)
    local chosen = ICUI.map_chosen and rows[ICUI.map_chosen]
    local why = nil
    if chosen then
        local list
        list, why = ICUI.map_outline(faction_key, chosen.slug)
        for _, p in ipairs(list) do ringed[p] = true end
    end
    for i, province in pairs(ICUI.map_keys) do
        local m = comp(ICUI.MARKER .. "_" .. i, layer)
        if m then
            m:SetImagePath(ringed[province] and ICUI.MK_RING_OUTLINE or ICUI.MASK_NONE,
                           ICUI.MK_OUTLINE)
        end
    end
    for i = 1, ICUI.MAP_ROWS do
        local row = comp(ICUI.MAP_ROW .. "_" .. i, layer)
        if row then
            -- map_chosen is a ROW of the whole legend, not a slot on this page.
            local at = ICUI.map_page * ICUI.MAP_ROWS + i
            row:SetImagePath(at == ICUI.map_chosen and ICUI.PARTY_SELECTED or ICUI.MASK_NONE,
                             ICUI.MAP_ROW_SEL)
        end
    end
    if next(ICUI.map_keys) == nil then
        set_text(comp("ic_map_hint_1", layer), "You hold no province.")
        set_text(comp("ic_map_hint_2", layer), "")
    else
        set_text(comp("ic_map_hint_1", layer), "Click a party to see what it would take.")
        set_text(comp("ic_map_hint_2", layer), why or "Click a province to choose its governor.")
    end
end

function ICUI.map_pages(rows)
    return math.max(1, math.ceil(#rows / ICUI.MAP_ROWS))
end

function ICUI.map_legend(faction_key, layer)
    local court = IC.court(faction_key)
    local rows = ICUI.map_rows(faction_key)
    -- THE PAGER (ruling 12), the court's own words, only past one page.
    local pages = ICUI.map_pages(rows)
    ICUI.map_page = math.min(ICUI.map_page, pages - 1)
    for _, name in ipairs({"ic_map_prev", "ic_map_page", "ic_map_next"}) do
        local c = comp(name, layer)
        if c then c:SetVisible(pages > 1) end
    end
    set_text(comp("ic_map_prev", layer), "Previous")
    set_text(comp("ic_map_next", layer), "Next")
    set_text(comp("ic_map_page", layer),
             string.format("Page %d of %d", ICUI.map_page + 1, pages))
    for i = 1, ICUI.MAP_ROWS do
        local row = comp(ICUI.MAP_ROW .. "_" .. i, layer)
        local r = rows[ICUI.map_page * ICUI.MAP_ROWS + i]
        if row then
            row:SetVisible(r ~= nil)
            if r then
                local sw = comp("ic_map_sw", row)
                if sw then
                    sw:SetImagePath(ICUI.map_disc(r.slug), 0)
                    sw:SetImagePath(r.slug and ICUI.crest(r.slug) or ICUI.MASK_NONE, 1)
                end
                if r.slug then
                    set_text(comp("ic_map_name", row), ICUI.house_name(r.slug, faction_key))
                    set_text(comp("ic_map_gov", row), string.format("Governs %d",
                             #IC.provinces_of_house(faction_key, r.slug)))
                    local list, why = ICUI.map_outline(faction_key, r.slug)
                    set_text(comp("ic_map_take", row), why and "" or
                             string.format("Would take %d", #list))
                    -- THE COURT'S OWN TIP; its Crown branch already explains the
                    -- Crown. The grace period and secession-off say why instead.
                    local tip = ICUI.secession_tip(faction_key, court, r.slug)
                    if why and r.slug ~= IC.CROWN then tip = why end
                    row:SetTooltipText(tip, "", true)
                else
                    local n = #ICUI.map_outline(faction_key, nil)
                    set_text(comp("ic_map_name", row), "No governor")
                    set_text(comp("ic_map_gov", row), string.format("%d province%s",
                             n, n == 1 and "" or "s"))
                    set_text(comp("ic_map_take", row), "")
                    row:SetTooltipText("Provinces with no governor. Click one's marker to "
                                       .. "choose a governor.", "", true)
                end
            end
        end
    end
end
```

In `ICUI.map_open`, inside the `pcall`, after `ICUI.map_draw(faction, layer)`: `ICUI.map_chosen, ICUI.map_page = nil, 0`, `ICUI.map_legend(faction, layer)`, `ICUI.map_ring(faction, layer)`.

In `ICUI.map_register`'s `ic_map_click` listener, two branches after the `ic_map_close` one:

```lua
        elseif string.match(id or "", "^" .. ICUI.MAP_ROW .. "_%d+$") then
            local layer = comp(ICUI.MAP)
            if layer then
                local n = ICUI.map_page * ICUI.MAP_ROWS + tonumber(string.match(id, "_(%d+)$"))
                ICUI.map_chosen = (ICUI.map_chosen ~= n) and n or nil
                ICUI.map_ring(ICUI.player(), layer)
            end
        elseif id == "ic_map_prev" or id == "ic_map_next" then
            local layer = comp(ICUI.MAP)
            if layer then
                local faction = ICUI.player()
                local last = ICUI.map_pages(ICUI.map_rows(faction)) - 1
                local step = (id == "ic_map_next") and 1 or -1
                ICUI.map_page = math.max(0, math.min(last, ICUI.map_page + step))
                ICUI.map_legend(faction, layer)
                ICUI.map_ring(faction, layer)
            end
```

- [ ] **Step 4: Run the harness, verify it passes**

Expected: `iron court harness: ok (798 checks)`.

---

### Task 3: Hover, and the click round trip

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui_map.lua`
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua` (`IC.assign_governor` ~line 2699)
- Modify: `tools/_iron_court_harness.lua`

**Interfaces:**
- Consumes: Task 1-2's map functions; the panel's `ICUI.open`, `ICUI.close`, `ICUI.pick` (`{kind = "gov", key = province}`, the shape the Governors row click sets), `ICUI.ANSWERS.gov(arg, done, why, spare)`, `ICUI.character_name`, `ICUI.house_name`, `IC.house_of_cqi`.

**Why the model changes:** the court's own Governors tab never appoints over a sitting governor - a click on a governed row releases him. The map's marker click opens the picker for a governed province too (ruling 4), and `IC.assign_governor` overwrites in silence, so the Record would show the new man arriving and never the old one leaving. Releasing costs nothing, so there is no exploit here, only a missing line.

**Ruling 11 (cancel):** the picker has no cancel button; its ways out are the court's close button and a tab. Close is the cancel and returns to the map (spec section 6); a tab click is the player choosing the court, and stays there.
- Produces: `ICUI.map_tip(faction_key, province_key) -> string`; `ICUI.map_marker_click(index)`; `ICUI.map_return` (true while the court was opened from a marker).

- [ ] **Step 1: Write the failing checks**

```lua
check("a marker's tooltip names the province, its governor, party and loyalty", function()
    IC.state = {}
    local g = make_character(831, ANY_SEAT, "legion")
    make_faction(F, IC.CHD_SUBCULTURE, {g}, {"prov_a", "prov_b"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    IC.court(F).govs["prov_a"] = 831
    with_fake_map(function(hud, panel, extra, layer)
        ICUI.map_open()
        local tip = layer().children[ICUI.MARKER .. "_1"].tooltip or ""
        assert(tip:find("prov_a", 1, true), tip)
        assert(tip:find(ICUI.character_name(g), 1, true), "no governor in: " .. tip)
        assert(tip:find(ICUI.house_name("legion", F), 1, true), "no party in: " .. tip)
        assert(tip:find("Loyalty: " .. IC.province_loyalty(F, "prov_a"), 1, true), tip)
        assert(tip:find("replace", 1, true), "a governed province does not say a click replaces: " .. tip)
        local none = layer().children[ICUI.MARKER .. "_2"].tooltip or ""
        assert(none:find("No governor", 1, true), none)
    end)
end)

check("a marker opens its overseer picker, and an answered choice returns to the map",
function()
    IC.state = {}
    local g = make_character(841, ANY_SEAT, "legion")
    make_faction(F, IC.CHD_SUBCULTURE, {g}, {"prov_a", "prov_b"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    with_fake_map(function(hud, panel, extra, layer)
        ICUI.map_open()
        map_click(ICUI.MARKER .. "_2")
        assert(not layer(), "the map stayed up under the picker")
        assert(find_uicomponent(nil, ICUI.PANEL), "no court for the picker")
        assert(ICUI.pick and ICUI.pick.kind == "gov" and ICUI.pick.key == "prov_b",
            "the picker is " .. tostring(ICUI.pick and ICUI.pick.key))
        -- A REFUSAL STAYS IN THE PICKER with its notice, as it does today.
        ICUI.ANSWERS.gov("prov_b|841", false, "no such character")
        assert(not layer() and not panel.destroyed, "a refusal left the picker")
        assert(ICUI.map_return, "a refusal forgot the way back to the map")
        -- THE ANSWER, as after_op delivers it.
        ICUI.ANSWERS.gov("prov_b|841", true)
        assert(layer(), "an answered choice did not return to the map")
        assert(not find_uicomponent(nil, ICUI.PANEL), "the court stayed open over the map")
        assert(ICUI.map_return == nil, "the return flag outlived its return")
    end)
end)

check("closing the court opened from a marker returns to the map; a tab stays", function()
    IC.state = {}
    make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a"})
    IC.add_house(F, IC.CROWN)
    -- The harness's cm:callback runs its function at once, and map_click fires
    -- the court's listener first - so the court is shut when the map reopens,
    -- which is the order the deferral buys in game.
    with_fake_map(function(hud, panel, extra, layer)
        ICUI.map_open()
        map_click(ICUI.MARKER .. "_1")
        map_click("ic_close")
        assert(layer(), "closing the court did not return to the map")
        assert(panel.destroyed, "the court stayed open over the map")
        -- A TAB: the player chose the court.
        map_click(ICUI.MARKER .. "_1")
        map_click("ic_tab_offices")
        assert(ICUI.map_return == nil, "a tab click kept the map waiting")
        map_click("ic_close")
        assert(not layer(), "the map came back after the player chose the court")
    end)
end)

check("replacing a governor records the one who left", function()
    IC.state = {}
    turn = 1
    local a, b = make_character(851, ANY_SEAT, "legion"), make_character(852, ANY_SEAT, "legion")
    make_faction(F, IC.CHD_SUBCULTURE, {a, b}, {"prov_a"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    IC.assign_governor(F, "prov_a", 851)
    IC.assign_governor(F, "prov_a", 851)      -- the same man again: nobody left
    IC.assign_governor(F, "prov_a", 852)
    local off = 0
    for _, e in ipairs(IC.court(F).log or {}) do
        if e.kind == "gov_off" and e.key == "prov_a" then off = off + 1 end
    end
    assert(off == 1, "the Record shows " .. off .. " governors leaving prov_a, not 1")
    assert(IC.court(F).govs["prov_a"] == 852, "the new governor did not take the seat")
end)

check("a province lost since the map drew never reaches the picker", function()
    IC.state = {}
    local f = make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a", "prov_b"})
    IC.add_house(F, IC.CROWN)
    with_fake_map(function(hud, panel, extra, layer)
        ICUI.map_open()
        -- prov_b falls between the draw and the click.
        make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a"})
        map_click(ICUI.MARKER .. "_2")
        assert(not (ICUI.pick and ICUI.pick.key == "prov_b"), "a lost province reached the picker")
        assert(layer(), "the map closed on a stale click instead of redrawing")
    end)
end)
```

If `make_faction` with the same key does not replace the faction the stub answers, lose the province by removing it from the faction's `provinces` list instead (read `make_faction` to see which field holds it).

- [ ] **Step 2: Run the harness, verify it fails**

Expected: FAIL on the tooltip check (`tooltip` is nil: nothing sets it yet).

- [ ] **Step 3: Implement**

In the map file, before `function ICUI.map_close()`:

```lua
function ICUI.map_tip(faction_key, province)
    local court = IC.court(faction_key)
    local lines = {loc("provinces_onscreen_" .. province, province)}
    local cqi = court.govs[province]
    local man = cqi and IC.character_by_cqi(faction_key, cqi) or nil
    if man then
        local rank = 0
        pcall(function() rank = man:rank() end)
        lines[#lines + 1] = string.format("Governor: %s, rank %d", ICUI.character_name(man), rank)
        local slug = IC.house_of_cqi(faction_key, cqi)
        if slug then lines[#lines + 1] = "Party: " .. ICUI.house_name(slug, faction_key) end
    else
        lines[#lines + 1] = "No governor"
    end
    lines[#lines + 1] = string.format("Loyalty: %d", IC.province_loyalty(faction_key, province))
    if IC.secession_on() then
        for _, slug in ipairs(IC.present_houses(faction_key)) do
            if slug ~= IC.CROWN then
                for _, p in ipairs(IC.defecting_provinces(faction_key, slug) or {}) do
                    if p == province then
                        lines[#lines + 1] = string.format("Would go with %s if they walked out.",
                                                          ICUI.house_name(slug, faction_key))
                    end
                end
            end
        end
    end
    lines[#lines + 1] = man and "Click to replace its governor." or "Click to choose its governor."
    return table.concat(lines, "\n")
end

ICUI.map_return = nil

function ICUI.map_marker_click(index)
    local faction = ICUI.player()
    local province = ICUI.map_keys[index]
    if not faction or not province then return end
    -- STILL YOURS: IC.assign_governor does not ask, so a province lost since the
    -- map drew must not reach it. The map redraws instead.
    local held = false
    for _, p in ipairs(IC.seats(faction)) do if p == province then held = true end end
    if not held then ICUI.map_open() return end
    ICUI.map_close()
    ICUI.map_return = true
    ICUI.view = "govs"
    ICUI.open()
    if not comp(ICUI.PANEL) then ICUI.map_return = nil return end
    ICUI.pick = {kind = "gov", key = province}
    ICUI.scroll.pick = 0
    ICUI.refresh()
end

-- AN ANSWERED CHOICE RETURNS TO THE MAP, in multiplayer when the answer arrives.
local court_gov_answer = ICUI.ANSWERS.gov
ICUI.ANSWERS.gov = function(arg, done, why, spare)
    court_gov_answer(arg, done, why, spare)
    if done and ICUI.map_return then
        ICUI.map_return = nil
        ICUI.map_open()                 -- which closes the court
    end
end
```

In `ICUI.map_draw`, after `set_text(m, ...)`: `m:SetTooltipText(ICUI.map_tip(faction_key, province), "", true)`.

In `ICUI.map_register`'s `ic_map_click` listener, three new branches after the row branch:

```lua
        elseif string.match(id or "", "^" .. ICUI.MARKER .. "_%d+$") then
            ICUI.map_marker_click(tonumber(string.match(id, "_(%d+)$")))
        elseif id == "ic_close" and ICUI.map_return then
            -- AFTER the court's own listener has closed it: deferred, because
            -- the order the two listeners run in is not guaranteed.
            ICUI.map_return = nil
            cm:callback(function()
                if not comp(ICUI.PANEL) then ICUI.map_open() end
            end, 0)
        elseif ICUI.TAB_VIEW[id] then
            ICUI.map_return = nil      -- a tab: the player chose the court
```

In `zzz_derpy_iron_court.lua`, `IC.assign_governor`, before `court.govs[province_key] = cqi`:

```lua
    -- THE MAN HE REPLACES LEAVES ON THE RECORD. The Governors tab never appoints
    -- over a sitting governor; the party map's picker does (plan 2026-09-29).
    local was = court.govs[province_key]
    if was and was ~= cqi then
        IC.log(faction_key, "gov_off", IC.house_of_cqi(faction_key, was), province_key, 0)
    end
```

- [ ] **Step 4: Run the harness, verify it passes**

Expected: `iron court harness: ok (803 checks)`.

---

### Task 4: Leaving the map - selection and turn end

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui_map.lua`
- Modify: `tools/_iron_court_harness.lua`

**Interfaces:**
- Consumes: `ICUI.map_close`, `ICUI.map_return`.
- Produces: listeners `ic_map_turn_end`, `ic_map_char_selected`, `ic_map_settlement_selected`.

- [ ] **Step 1: Write the failing checks**

```lua
check("selecting an army or settlement leaves the map with the HUD back", function()
    IC.state = {}
    make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a"})
    IC.add_house(F, IC.CROWN)
    for _, name in ipairs({"ic_map_char_selected", "ic_map_settlement_selected"}) do
        with_fake_map(function(hud, panel, extra, layer)
            ICUI.map_open()
            local fire = core.listeners[name]
            assert(fire, "no " .. name .. " listener")
            fire({character = function() return nil end,
                  garrison_residence = function() return nil end})
            assert(not layer(), name .. " left the map up")
            assert(hud.visible == true, name .. " left the HUD hidden")
        end)
    end
end)

check("ending the turn closes the map and forgets a pending return", function()
    IC.state = {}
    local f = make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a"})
    IC.add_house(F, IC.CROWN)
    with_fake_map(function(hud, panel, extra, layer)
        ICUI.map_open()
        map_click(ICUI.MARKER .. "_1")
        assert(ICUI.map_return, "the fixture never left the map through a marker")
        core.listeners["ic_map_turn_end"]({faction = function() return f end})
        assert(ICUI.map_return == nil, "the turn ended with the map still waiting")
        -- OPENED OVER THE STILL-OPEN COURT: map_open closes it first, or the
        -- second HUD hide would replace the court's record of the first.
        ICUI.map_open()
        assert(panel.destroyed, "the map opened over the court")
        core.listeners["ic_map_turn_end"]({faction = function() return f end})
        assert(not layer(), "the turn ended with the map still up")
        assert(hud.visible == true, "the turn ended with the HUD still hidden")
    end)
end)
```

- [ ] **Step 2: Run the harness, verify it fails**

Expected: FAIL `no ic_map_char_selected listener`.

- [ ] **Step 3: Implement**

Above `function ICUI.map_register()`:

```lua
-- A SELECTION LEAVES THE MAP: the player saw something and went to act on it.
local function leave_on_select()
    if comp(ICUI.MAP) then ICUI.map_close() end
end
```

and at the end of `ICUI.map_register`, after the `ic_map_click` listener:

```lua
    core:add_listener("ic_map_char_selected", "CharacterSelected", true,
                      leave_on_select, true)
    core:add_listener("ic_map_settlement_selected", "SettlementSelected", true,
                      leave_on_select, true)
    -- THE TURN ENDS WITH NOTHING PINNED AND NOTHING WAITING (the court's own
    -- ic_turn_end closes the court).
    core:add_listener("ic_map_turn_end", "FactionTurnEnd", true, function(context)
        local faction = context:faction()
        if not faction or faction:is_null_interface() then return end
        if faction:name() ~= ICUI.player() then return end
        ICUI.map_return = nil
        if comp(ICUI.MAP) then pcall(ICUI.map_close) end
    end, true)
```

- [ ] **Step 4: Run the harness, verify it passes**

Expected: `iron court harness: ok (805 checks)`.

---

### Task 5: Mutants, the preview, gates, build, docs

**Files:**
- Modify: `tools/mutate_iron_court.py` (the `MUTANTS` list, before its closing `]`)
- Modify: `tools/preview_iron_court.py` (`render()` and the `__main__` jobs)
- Modify: `docs/sessions/PATCH_NOTES_20260925_IRON_COURT.md`, `docs/sessions/HANDOFF_20260929_IRON_COURT_FULL_SWEEP.md` (a new section), `docs/SESSION_INDEX.md` (the spec line: BUILT), `repos/derpy-iron-court/docs/DEVELOPMENT.md` counts at the next push only

- [ ] **Step 1: Mutants**

Append to `MUTANTS` (each anchor must match exactly once; run the runner on a name to check):

```python
    # THE PARTY MAP (plan 2026-09-29).
    ("the map marker given no settlement", UM,
     """                m:SetContextObject(cco("CcoCampaignSettlement", cqi))""",
     """"""),
    ("every marker on the first province's settlement", UM,
     """        if region then pcall(function() cqi = region:settlement():cqi() end) end""",
     """        if region then pcall(function() cqi = 700 end) end"""),
    ("a marker on the first region rather than the capital", UM,
     """    return capital or first""",
     """    return first"""),
    ("the capital ring on every province", UM,
     """                m:SetImagePath(province == capital and ICUI.MK_RING_CAPITAL""",
     """                m:SetImagePath(true and ICUI.MK_RING_CAPITAL"""),
    ("a marker with no name", UM,
     """                set_text(m, loc("provinces_onscreen_" .. province, province))""",
     """"""),
    ("the map opened over the court", UM,
     """    if comp(ICUI.PANEL) then ICUI.close(true) end
    if comp(ICUI.MAP) then ICUI.map_close() end""",
     """    if comp(ICUI.MAP) then ICUI.map_close() end"""),
    ("a second map layer stacked on the first", UM,
     """    if comp(ICUI.PANEL) then ICUI.close(true) end
    if comp(ICUI.MAP) then ICUI.map_close() end""",
     """    if comp(ICUI.PANEL) then ICUI.close(true) end"""),
    ("the map leaving the HUD up", UM,
     """    ICUI.show_hud(false)
    local ok, err = pcall(function()""",
     """    local ok, err = pcall(function()"""),
    ("the map hiding its own layer", UM,
     """    ICUI.show_hud(false)
    local ok, err = pcall(function()
        root():CreateComponent(ICUI.MAP, ICUI.PATH_MAP)
        local layer = comp(ICUI.MAP)
        if not layer then error("CreateComponent made no map layer") end""",
     """    local ok, err = pcall(function()
        root():CreateComponent(ICUI.MAP, ICUI.PATH_MAP)
        local layer = comp(ICUI.MAP)
        if not layer then error("CreateComponent made no map layer") end
        ICUI.show_hud(false)"""),
    ("the layer left at its file's size", UM,
     """        layer:Resize(root():Dimensions())""",
     """"""),
    ("the map listeners never registered", UM,
     """    court_register()
    ICUI.map_register()""",
     """    court_register()"""),
    ("the close button leaving the court shut", UM,
     """            ICUI.view = "govs"
            ICUI.open()""",
     """            ICUI.view = "govs\""""),
    ("the legend forgetting no governor", UM,
     """    rows[#rows + 1] = {slug = nil}""",
     """"""),
    ("a party ringing everything", UM,
     """        for _, p in ipairs(list) do ringed[p] = true end""",
     """        for _, p in pairs(ICUI.map_keys) do ringed[p] = true end"""),
    ("a second click keeping the choice", UM,
     """                ICUI.map_chosen = (ICUI.map_chosen ~= n) and n or nil""",
     """                ICUI.map_chosen = n"""),
    ("the legend never paging", UM,
     """        local r = rows[ICUI.map_page * ICUI.MAP_ROWS + i]""",
     """        local r = rows[i]"""),
    ("the pager never shown", UM,
     """        if c then c:SetVisible(pages > 1) end""",
     """        if c then c:SetVisible(false) end"""),
    ("Previous running off the first page", UM,
     """                ICUI.map_page = math.max(0, math.min(last, ICUI.map_page + step))""",
     """                ICUI.map_page = ICUI.map_page + step"""),
    ("a choice on page two framed on page one", UM,
     """            local at = ICUI.map_page * ICUI.MAP_ROWS + i""",
     """            local at = i"""),
    ("a row click choosing a slot, not a row", UM,
     """                local n = ICUI.map_page * ICUI.MAP_ROWS + tonumber(string.match(id, "_(%d+)$"))""",
     """                local n = tonumber(string.match(id, "_(%d+)$"))"""),
    ("the Crown's row ringing its provinces", UM,
     """    if slug == IC.CROWN then return {}, "Your own house does not secede." end""",
     """"""),
    ("the grace period ringing a threat", UM,
     """    if not IC.secession_on() then
        local left = IC.grace_left()""",
     """    if IC.TUNE.secession == false then
        local left = IC.grace_left()"""),
    ("no word for a realm with no province", UM,
     """        set_text(comp("ic_map_hint_1", layer), "You hold no province.")""",
     """        set_text(comp("ic_map_hint_1", layer), "")"""),
    ("a lost province reaching the picker", UM,
     """    if not held then ICUI.map_open() return end""",
     """"""),
    ("an answered choice staying in the court", UM,
     """    if done and ICUI.map_return then""",
     """    if false then"""),
    ("a refusal returning to the map", UM,
     """    if done and ICUI.map_return then""",
     """    if ICUI.map_return then"""),
    ("a closed court leaving the map closed", UM,
     """            cm:callback(function()
                if not comp(ICUI.PANEL) then ICUI.map_open() end""",
     """            cm:callback(function()
                if false then ICUI.map_open() end"""),
    ("a tab click keeping the map waiting", UM,
     """            ICUI.map_return = nil      -- a tab: the player chose the court""",
     """"""),
    ("a replaced governor leaving no record", M,
     """    if was and was ~= cqi then""",
     """    if false then"""),
    ("the same governor recorded leaving", M,
     """    if was and was ~= cqi then""",
     """    if was then"""),
    ("a selection leaving the map up", UM,
     """local function leave_on_select()
    if comp(ICUI.MAP) then ICUI.map_close() end
end""",
     """local function leave_on_select()
end"""),
    ("the turn end forgetting nothing", UM,
     """        ICUI.map_return = nil
        if comp(ICUI.MAP) then pcall(ICUI.map_close) end""",
     """        if comp(ICUI.MAP) then pcall(ICUI.map_close) end"""),
    ("a governed marker promising a new governor", UM,
     """    lines[#lines + 1] = man and "Click to replace its governor." or "Click to choose its governor.\"""",
     """    lines[#lines + 1] = "Click to choose its governor.\""""),
```

Run: `py tools/mutate_iron_court.py "map" "marker" "HUD" "layer" "legend" "pager" "Previous" "page" "slot" "ringing" "choice" "province reaching" "refusal returning" "closed court" "tab click" "governor" "selection" "turn end"`
Expected: every one `caught`, `0 unexplained`. A survivor is a missing check: write the check that catches it (failing first against the mutant), never delete the mutant. Mutants from other plans whose anchors moved (the tabs in `ICUI.PANEL_XY`) are stale anchors: retarget them.

- [ ] **Step 2: The preview's map picture**

In `tools/preview_iron_court.py` `render()`, add `"derpy_ic_map.twui.xml"` and `"derpy_ic_map_marker.twui.xml"` to the docs read into `named` (tags `"map"` and `"marker"`), and a `view == "map"` branch that, on the 1920 canvas: pastes `ic_map_legend` at its `MAP_LAYOUT` box; writes the title and both hints; draws one row per party of `demo_court(G)` plus "No governor" at `MAP_ROW_Y + (i-1) * MAP_ROW_H` with the swatch repainted `{0: G.map_disc_path(slug), 1: G.sigil_path(slug)}`, the name, "Governs N" and "Would take N"; and draws a sheet of markers to the right of the legend (one per party and one ungoverned, 220px apart from x 520, y 40) repainted `{0: G.map_disc_path(slug), 1: G.sigil_path(slug), 2: G.MAP_RING_CAPITAL if first else G.MASK_NONE, 3: G.MAP_RING_OUTLINE if second else G.MASK_NONE}` with the demo province names under them. Add `OUT_MAP = os.path.join(PG.CACHE, "ic_map.png")` beside the other outputs, and in `__main__` render `("map", 1920)` once after the jobs loop (the map is never scaled). Follow the file's existing `paste`/`text`/`cell` idiom exactly - read the party card branch (~line 1700) and copy its shape. `--check` must still pass; `--selftest` gains `assert "ic_map_legend" in G.MAP_LAYOUT`.

Run: `py tools/preview_iron_court.py` and open `ic_map.png`. Review: every name fits its cell, the swatch crest sits inside its disc, the rings frame the plate. Fix at the generator's numbers, not the picture.

- [ ] **Step 3: Full gates**

Run in order, nothing beside the mutation run:
- `"/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua` -> `ok (805 checks)`
- `luac -p` on the five Lua files; `py tools/check_lua_api.py` on them; `py tools/check_lua_literal_left.py` on them
- `py tools/gen_ic_ui.py --check`; `py tools/gen_ic_ui.py --selftest` (about 11 minutes)
- `py tools/import_iron_court.py` -> `verify ok`
- `py tools/preview_iron_court.py --check`
- `py tools/mutate_iron_court.py` (full, background) -> `N mutants, 0 unexplained`
- `py tools/sync_iron_court_repo.py --selftest`

- [ ] **Step 4: Build and deploy**

With RPFM open: `py tools/deploy_iron_court.py`. With the game shut it deploys and byte-compares; record the md5 of `data/derpy_iron_court.pack` (its first eight hex digits are the build name, `md5sum ... | tr a-f A-F`).

- [ ] **Step 5: Docs**

- Patch notes, New: `[*][b]The party map.[/b] A Map tab lays your court over the campaign map: each province wears its governing party's colour, choosing a party in the legend rings what it would take if it walked out, and clicking a province chooses its governor.` Header: which build carries it, deployed, not pushed.
- Handoff: a new section in `HANDOFF_20260929_IRON_COURT_FULL_SWEEP.md` (or a new handoff file if that one has grown past its day): the build name, the eight rulings above, Task 1's in-game answers, the checks and mutant counts, and the in-game looks still owed (spec section 8).
- `docs/SESSION_INDEX.md`: the party map spec line changes from DESIGN to BUILT with the build name.
