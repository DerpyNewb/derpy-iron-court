# Iron Court Governors Map Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** On the court's Governors tab, show the live campaign map through the open court:
- a pinned governor portrait on each held province;
- a Chaos Dwarf column on the left (Parties, Provinces, and the governor picker).

A governorship's weight also grows with the settlement levels held in its province.

**Architecture:**
- **Model first.** `IC.refresh_gov_weight` sums each province's held settlement levels and gives its governor's party `max(1, ceil(levels * 0.5))`.
- **Then the view.** On the "govs" view the court panel clears its backdrop and stops taking clicks. A holder, the panel's FIRST child, carries two sibling components per province with identical boxes: the PIN (`derpy_ic_gm_pin`) and the governor's masked FACE (`derpy_ic_gm_face`). Both are pinned by CA's `ContextWorldSpaceComponent`.
- **The column.** New panel components (`ic_gm_*`) and a new row pool (`derpy_ic_gm_row`) replace the Governors list.
- **Removal.** The old party map's separate layer, its marker, the Map tab and the round trip are deleted in Task 6.
- **Where the code lives.** The new view code goes in `zzz_derpy_iron_court_ui_map.lua`, which loads after the panel Lua and wraps it. Tables the scale pass must scale go in the panel Lua, because the pass copies them when that file loads.

**Tech Stack:**
- Lua 5.1: the campaign scripts.
- Python 3 generators: `tools/gen_ic_ui.py` and `tools/gen_iron_court_emitter.py`.
- Test and check tools:
  - the Lua harness, `tools/_iron_court_harness.lua`;
  - the mutation runner, `tools/mutate_iron_court.py`;
  - the headless preview, `tools/preview_iron_court.py`;
  - the pack gate, `tools/import_iron_court.py`.
- Build and deploy: `tools/deploy_iron_court.py`.

**Spec:** `docs/superpowers/specs/2026-09-30-iron-court-governors-map-design.md`.

Evidence:
- The CA survey is summarised in the spec's section 6.
- CA's masked portrait is `kislev_atamans.twui.xml` `drag_icon`:
  - its `maskimage` is the GUID of its own `porthole_mask` componentimage, listed last in every state;
  - read it with `py tools/read_pack_index.py "F:/SteamLibrary/steamapps/common/Total War WARHAMMER III/data/ui3.pack" kislev_atamans.twui.xml`.
- The holder rule is memory `wh3-world-space-ui-pin`.

## Global Constraints

**The workspace**
- It is NOT git, so there are no commits.
- Each checkpoint is the harness run green, plus the gates the step names.
- Before each task, copy every file it edits to the session scratchpad as `<name>_before_govmap_t<N>.<ext>`.
- **The ledger** is `.superpowers/sdd/2026-09-30-iron-court-governors-map/progress.md`, as the party map's plan kept its own. `sdd-workspace` calls `git rev-parse` and cannot resolve it here, so create the folder by hand. Its first line is `# SDD ledger - plan: docs/superpowers/plans/2026-09-30-iron-court-governors-map.md`. Long tool output goes to files in the same folder.

**Words the player reads**
- No emojis anywhere, and never the word "rung".
- Plain words only: no "standing", "cap", "rep", "AI" or "HUD" in any string the player reads.
- The party figure is **weight**; a man's figure is **influence**.

**Editing files**
- The Iron Court Lua files, the harness, `gen_ic_ui.py`, `gen_iron_court_emitter.py` and `mutate_iron_court.py` are LF.
- Edit them with the Edit tool or byte-safe Python, never `sed -i`.
- A patch script that contains a backslash or a regex goes through the Write tool, never a heredoc.

**The harness**
- Run it as `"/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua`.
- It stops at the first FAIL; `IC_TEST_ALL=1` runs all.
- It ends with `iron court harness: ok (N checks)`.
- It starts this plan at 828 checks.
- New checks go ABOVE `check("no parties' turn failed anywhere in the run"`.

**The mutation runner**
- `py tools/mutate_iron_court.py <name substrings>` runs only the matching mutants.
- `--selftest` asserts that every anchor matches exactly once. Run it after any edit that deletes or moves code, because a stale anchor is a finding.
- Never edit any file while it runs, and never run another gate beside it.
- After a run, run `py tools/gen_ic_ui.py` again: the runner restores the Lua, not what the Lua generated.

**Runtime rules**
- A loc call from a listener or a turn handler is a turn-1 CTD. Everything the Governors view writes is written when the view draws or on a click.
- Runtime components ignore `.twui.xml` offsets, dockpoints and dock offsets (measured 2026-09-04):
  - every column component is placed by `ICUI.layout` or `MoveTo`;
  - pins are placed by the engine through `ContextWorldSpaceComponent` and are never moved from Lua.
- Component calls:
  - `SetText(text, "")`, never `SetStateText`;
  - `:Parent()` needs two `UIComponent()` wraps;
  - `SetVisible`, `SetInteractive` and `SetDisabled` take a boolean, never nil;
  - `SetImagePath` takes no third argument.
- Every Chaos Dwarf art path is referenced directly (`ui/skins/default/dlc23_chd_hell_forge/...`), never through a skin swap.

**Build and deploy**
- Build only while RPFM's server is up (`http://127.0.0.1:45127/sessions` answers 200).
  - It may be started headless with `Start-Process "G:\Modding for resources\RPFM\rpfm_server.exe" -WindowStyle Hidden`.
  - Stop it after the build.
- After a build, if `Warhammer3.exe` is not running, deploy to data/ without asking: `py tools/deploy_iron_court.py`.
- Never push to GitHub or upload to the Workshop without asking.

## Rulings against the spec (made while planning; ledger them at execution)

1. **Two sibling components per province, not a masked child.**
   - A mask clips its whole component: CA's `drag_icon` is nothing but the portrait. A runtime-created child cannot be placed inside a pin either, because children land at the parent's origin (measured 2026-09-04).
   - So each province gets two components:
     - a PIN: art, party ring, plate and text; it takes the click;
     - a FACE: dark ground, portrait or crest, and the `porthole_mask`; it takes no click.
   - Both have IDENTICAL boxes and the same settlement context, so the engine anchors them the same way at every zoom.
   - The face is created after its pin, so it draws on top.
2. **The mask sits at the head's offset inside a taller box.** CA's mask always fills its component at 0,0, so whether an offset mask clips correctly is Phase 0 question 5. If it does not, the fallback is the square portrait under an opaque ring whose bezel covers its corners (Task 2, step 12).
3. **Phase 0 builds the real pin and face** rather than the old disc. One in-game look then answers the tracking, click-through and mask questions together.
4. **During Phase 0 the Governors view shows no list.**
   - A pin opens the court's own full-screen governor picker. The backdrop comes back while it is up, and the answer returns to the map.
   - The Map tab keeps working until Task 6.
   - The Phase 0 build is for the author's look.
5. **The close-on-selection listener ships in Phase 0.** A settlement selected through a see-through court must not leave the court over CA's settlement panel.
6. **No per-state tint and no new states** (the spec's party-ring row said `SetState`).
   - The party ring is one generated PNG per party (`ui/derpy_ic/gm_ring_<slug>.png`), painted with `SetImagePath`.
   - A row's selected and inactive looks are CA's art swapped into its two layers, as the court's tabs already do.
   - Why: the emitter writes two states, and the engine moves a button's state itself (see `ICUI.grey_look`'s comment), while `SetImagePath` repaints are proven in game.
7. **One plate, two lines** (the spec says two plates).
   - The pin's own text is `"<province>\n<Loyalty N%>"`, on one stretched `sub_title` plate.
   - The face cannot carry the text, because its mask would clip it, and a child cannot be placed.
   - Whether `\n` breaks the line under `texthbehaviour="Never split"` is Phase 0 question 7. The fallback is one line, `"<province> - 62%"`.
8. **CA's Kislev template carries no `offset_x/y/z`** (spec section 6 was wrong).
   - `template_settlement_overlay` has only `depth_disabled`. CA's `offset_y` appears on 7 layouts, with values from 0.2 to 26 and units unmeasured.
   - The pin keeps the proven marker's shape: its plate sits at the box's bottom, on the settlement.
   - Phase 0 question 6 asks whether the point reads right. If it does not, the lever is `offset_y`.
9. **`ICUI.cut_text(c, text)`** returns the string that `ICUI.fit_cut` would draw, and `fit_cut` calls it. The pin cuts only the name line of its two.
10. **The pins' holder and the view's plates sort below tier -1** (pins at tier -3, plates at -2). `make_ic_backdrop.py` treats every tier -1 name as an always-present opaque plate, and these are shown on one view only.
11. **The old Governors list's checks are deleted in Task 2**, because that list stops drawing there. Task 4's migration table names the successor of each one. The harness is green at the end of every task.
12. **New files for the pin and the face**, rather than the old marker rewritten. The old marker keeps drawing the Map tab until Task 6 deletes both.
13. **Sort** has three cells, each calling `ICUI.click_column("govs", col)` for columns 1, 2 and 4. Map order is what a third click returns to, as today.
14. **The row portrait frame is the court's own `FACE_LAYERS`** (`portrait_frame.png`), not CA's `unit_card_frame`. On first seeing CA's frame in game the author said "make the borders thicker, the character portrait permeates thru the border", and `FRAME_ART` was built for that.
15. **The column opens on Provinces.** The tab is Governors, and the Provinces page is its list.
16. **From Task 5, `ICUI.gm_on()` does not ask about `ICUI.pick`.** Every other picker opens from the Court or Intrigue tabs, and a tab click clears `ICUI.pick`, so on the Governors view a picker is always the governor's, and it draws in the column.

## Review Focus

1. **Leaving the Governors view by any path must restore the panel or destroy it.** The paths are: another tab, the Help button, close, turn end, and a selection through the court. Each must put the backdrop and click-blocking back, or destroy the panel. A panel that stays non-interactive on another tab is a dead zone over the map that nothing explains. From Task 5, a picker opened, answered or abandoned on the view stays on the map, and its checks say so. Tests: Task 2's backdrop check, Task 5's abandon check, Task 6's turn-end check.
2. **A province lost, or a governor killed, between drawing and clicking** must not reach `IC.assign_governor` or show a stale face. The view redraws instead: Task 2's pin check and Task 4's lost-selection check.
3. **A realm with more provinces than the column shows** pages. The selection is a province key, so it stays on the right province after a sort: Task 4's sort check.
4. **A settlement razed or downgraded** changes its province's weight at the next recompute. A province whose every settlement is a ruin still gives 1: Task 1.
5. **The court opened at a compact layout** (a small UI scale) draws the column and its plates inside the screen, and the pins on the screen, not the box: Task 2's wide-screen check and Task 3's compact check.

## Files

| File | Change | Responsibility |
|---|---|---|
| `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua` | modify | the weight rule |
| `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua` | modify | new `PANEL_XY` entries; the column row's tables; `cut_text`; `picker_lines`; the Help line; the Governors list deleted |
| `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui_map.lua` | modify | the Governors view: pins, column, picker, clicks; the old map removed in Task 6 |
| `tools/gen_iron_court_emitter.py` | modify | the `mask` kwarg |
| `tools/gen_ic_ui.py` | modify | the pin, face and row files; the column in the panel; rings; checks |
| `tools/import_iron_court.py` | modify | the `GM_ROW_CHILD_XY` cross-check |
| `tools/preview_iron_court.py` | modify | the old map and Governors list pictures deleted (Task 6); the two Governors view pictures (Task 7) |
| `tools/sync_iron_court_repo.py` | modify | the published file list (Task 6) |
| `docs/CUSTOM_UI.md`, `docs/SESSION_INDEX.md`, `docs/sessions/PATCH_NOTES_20260925_IRON_COURT.md` | modify | Task 7 |
| `docs/sessions/HANDOFF_20260930_IRON_COURT_GOVERNORS_MAP.md` | create | Task 7 |
| `tools/_iron_court_harness.lua` | modify | checks, and the `with_fake_govmap` fixture |
| `tools/mutate_iron_court.py` | modify | mutants |
| `Modding Files/pack/ui/campaign ui/derpy_ic_gm_pin.twui.xml`, `derpy_ic_gm_face.twui.xml`, `derpy_ic_gm_row.twui.xml`, `derpy_ic_gm_row_compact.twui.xml` | generated | |
| `Modding Files/pack/ui/campaign ui/derpy_ic_map.twui.xml`, `derpy_ic_map_marker.twui.xml` | deleted in Task 6 | |

---

### Task 1: Weight from a developed province (model only)

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua`
  - `IC.TUNE` (`weight_per_governor = 3,` at ~line 445)
  - `IC.refresh_gov_weight` (~line 2931)
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua`
  - `ICUI.HELP`, the Governors topic (~line 5245)
  - `ICUI.help_vars` (~line 5301)
- Modify: `tools/_iron_court_harness.lua`
  - the region stub's two `settlement = function()` tables (~lines 351 and 420)
  - new checks
- Modify: `tools/mutate_iron_court.py` (`MUTANTS`)

**Interfaces:**
- Produces (Lua):
  - `IC.TUNE.weight_per_gov_level = 0.5`. It replaces `weight_per_governor`, which is deleted.
  - `IC.province_levels(faction_key) -> {[province_key] = levels}`: one walk of the faction's regions; a missing key means 0.
  - `IC.gov_weight_of(levels) -> integer >= 1`.
  - `ICUI.help_vars(faction).levels_per_weight` (2 at the default).
- Produces (harness):
  - `f._levels = {[province_key] = level}` on a faction stub. The level is the one the player sees, 1-5; `0` or absent is a ruin.
  - `level` on an `f._extra_regions` entry.
  - Both are answered through `region:settlement():primary_slot():building():building_level()` as `level - 1`.

- [ ] **Step 1: Snapshot** the four files to the scratchpad as `*_before_govmap_t1.*`.

- [ ] **Step 2: Give the harness's settlements a primary building**

Above `local function make_faction` (~line 240) add:

```lua
-- A SETTLEMENT'S PRIMARY SLOT, at the level the player sees (1-5). CA's
-- building_level() counts from 0, so level 3 answers 2. No level, or 0, is a
-- ruin: the slot's building is a null interface - and a null interface still
-- answers building_level() with 0 here, so code that forgets to ask
-- is_null_interface() counts a ruin as a village and a check can see it.
local function fake_slot(level)
    return {building = function()
        if not level or level <= 0 then
            return {is_null_interface = function() return true end,
                    building_level = function() return 0 end}
        end
        return {is_null_interface = function() return false end,
                building_level = function() return level - 1 end}
    end}
end
```

The extra region's settlement (~line 351) is:

```lua
settlement = function()
    return {is_null_interface = function() return false end,
            cqi = function() return e.cqi end}
end
```

Add one entry to it:

```lua
                                        primary_slot = function() return fake_slot(e.level) end,
```

Add one entry to the main region's settlement table (~line 420), beside `logical_position_y`:

```lua
                                primary_slot = function() return fake_slot((f._levels or {})[key]) end,
```

- [ ] **Step 3: Write the failing checks** above `check("no parties' turn failed anywhere in the run"`:

```lua
check("a governorship's weight follows its province's settlement levels", function()
    IC.state = {}
    local g = make_character(1901, ANY_SEAT, "legion")
    local f = make_faction(F, IC.CHD_SUBCULTURE, {g}, {"prov_a"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    IC.court(F).govs["prov_a"] = 1901
    local function weight_at(capital, minors)
        f._levels = {prov_a = capital}
        f._extra_regions = {}
        for i, lv in ipairs(minors) do
            f._extra_regions[i] = {province = "prov_a", name = "region_prov_a_" .. i,
                                   cqi = 1950 + i, level = lv}
        end
        IC.refresh_gov_weight(F)
        return IC.court(F).houses.legion.gov_weight
    end
    -- THE SPEC'S TABLE (section 4): 1 -> 1, 7 -> 4, 11 -> 6, 20 -> 10.
    assert(weight_at(1, {}) == 1, "a level-1 village gives " .. weight_at(1, {}))
    assert(weight_at(3, {2, 2}) == 4, "capital 3 and two minors at 2 give " .. weight_at(3, {2, 2}))
    assert(weight_at(5, {3, 3}) == 6, "capital 5 and two minors at 3 give " .. weight_at(5, {3, 3}))
    assert(weight_at(5, {5, 5, 5}) == 10, "four maxed settlements give " .. weight_at(5, {5, 5, 5}))
    -- THE CROWN, which governs nothing here, gets none of it.
    assert(IC.court(F).houses[IC.CROWN].gov_weight == 0, "the Crown took a governorship's weight")
    f._levels, f._extra_regions = nil, nil
end)

check("a ruin counts nothing, and a province of ruins still gives 1", function()
    IC.state = {}
    local g = make_character(1911, ANY_SEAT, "legion")
    local f = make_faction(F, IC.CHD_SUBCULTURE, {g}, {"prov_a"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    IC.court(F).govs["prov_a"] = 1911
    -- CAPITAL 2 AND A RUIN: 2 levels -> 1. A ruin counted as a village would
    -- make it 3 -> 2.
    f._levels = {prov_a = 2}
    f._extra_regions = {{province = "prov_a", name = "region_prov_a_ruin", cqi = 1961, level = 0}}
    IC.refresh_gov_weight(F)
    assert(IC.court(F).houses.legion.gov_weight == 1,
        "capital 2 and a ruin gave " .. IC.court(F).houses.legion.gov_weight)
    -- NOTHING BUT RUINS: never less than 1.
    f._levels = {prov_a = 0}
    IC.refresh_gov_weight(F)
    assert(IC.court(F).houses.legion.gov_weight == 1,
        "a province of ruins gave " .. IC.court(F).houses.legion.gov_weight)
    f._levels, f._extra_regions = nil, nil
end)

check("a settlement lost or upgraded moves its party's weight at the next turn", function()
    IC.state = {}
    IC.home_prov = {}
    turn = 1
    local g = make_character(1921, ANY_SEAT, "legion", "prov_a")
    local f = make_faction(F, IC.CHD_SUBCULTURE, {g}, {"prov_a"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    IC.court(F).govs["prov_a"] = 1921
    f._levels = {prov_a = 3}
    f._extra_regions = {{province = "prov_a", name = "region_prov_a_minor", cqi = 1971, level = 3}}
    IC.turn(F)
    assert(IC.court(F).govs.prov_a == 1921, "the fixture lost its governor in the turn")
    assert(IC.court(F).houses.legion.gov_weight == 3, "6 levels gave " .. IC.court(F).houses.legion.gov_weight)
    -- THE MINOR SETTLEMENT FALLS, and the capital is raised to 5.
    f._extra_regions = nil
    f._levels = {prov_a = 5}
    turn = 2
    IC.turn(F)
    assert(IC.court(F).houses.legion.gov_weight == 3, "5 levels gave " .. IC.court(F).houses.legion.gov_weight)
    f._levels = {prov_a = 1}
    turn = 3
    IC.turn(F)
    assert(IC.court(F).houses.legion.gov_weight == 1, "1 level gave " .. IC.court(F).houses.legion.gov_weight)
    f._levels = nil
    turn = 1
end)

check("an away governor still earns his party the province's weight", function()
    IC.state = {}
    -- A LORD IN THE FIELD, standing in prov_b: only he can be away.
    local g = make_character(1931, ANY_SEAT, "legion", "prov_b")
    g._force = true
    local f = make_faction(F, IC.CHD_SUBCULTURE, {g}, {"prov_a", "prov_b"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    IC.court(F).govs["prov_a"] = 1931
    f._levels = {prov_a = 5, prov_b = 1}
    assert(not IC.governor_active(F, "prov_a"), "the fixture's governor is not away")
    IC.refresh_gov_weight(F)
    assert(IC.court(F).houses.legion.gov_weight == 3,
        "an away governor of 5 levels gave " .. IC.court(F).houses.legion.gov_weight)
    f._levels = nil
end)

check("an AI court's governorship follows its province's levels too", function()
    IC.state = {}
    IC.home_prov = {}
    turn = 1
    local g = make_character(1941, ANY_SEAT, "legion", "prov_a")
    local f = make_faction(F, IC.CHD_SUBCULTURE, {g}, {"prov_a"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    IC.court(F).govs["prov_a"] = 1941
    f._levels = {prov_a = 5}
    f._extra_regions = {{province = "prov_a", name = "region_prov_a_minor", cqi = 1981, level = 2}}
    local saved = cm.get_human_factions
    cm.get_human_factions = function() return {} end
    local ok, err = pcall(function()
        assert(not IC.is_human(F), "the fixture's court is still the player's")
        IC.turn(F)
        assert(IC.court(F).govs.prov_a == 1941, "the AI court's turn replaced its governor")
        -- WHICHEVER PARTY HE IS DEALT TO: an AI court rolls its men at its turn.
        local slug = IC.house_of_cqi(F, 1941)
        assert(slug and IC.court(F).houses[slug].gov_weight == 4,
            "7 levels in an AI court gave " .. tostring(slug and IC.court(F).houses[slug].gov_weight))
    end)
    cm.get_human_factions = saved
    f._levels, f._extra_regions = nil, nil
    assert(ok, err)
end)

check("the Help page states the weight rule with the court's own number", function()
    IC.state = {}
    make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a"})
    IC.add_house(F, IC.CROWN)
    local vars = ICUI.help_vars(F)
    assert(vars.levels_per_weight == 2, "levels per weight reads " .. tostring(vars.levels_per_weight))
    local found = false
    for _, topic in ipairs(ICUI.HELP) do
        for _, line in ipairs(topic.lines or {}) do
            if line:find("{levels_per_weight}", 1, true) then found = true end
            assert(not line:find("weight and loyalty the way a seat does", 1, true),
                "the Help page still says a governorship's weight counts the way a seat does")
        end
    end
    assert(found, "no Help line states the weight rule")
end)
```

- [ ] **Step 4: Run the harness and verify that it fails**

Run: `IC_TEST_ALL=1 "/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | tail -12`

Expected:
- 6 failing and 828 passing;
- the first failure on `a level-1 village gives 3`, the flat weight;
- the Help check failing on `levels per weight reads nil`.

- [ ] **Step 5: The rule in the model**

In `IC.TUNE`, replace `    weight_per_governor = 3,` with:

```lua
    -- A GOVERNORSHIP IS WORTH ITS PROVINCE (author, 2026-09-30): one weight
    -- for every two settlement levels held there, rounded up, never less than
    -- 1 - a level-1 village counts 1, a level-5 capital 5 (IC.gov_weight_of).
    weight_per_gov_level = 0.5,
```

Replace the whole of `IC.refresh_gov_weight` with:

```lua
-- THE SETTLEMENT LEVELS A FACTION HOLDS IN EACH PROVINCE, in one walk of its
-- regions. A settlement's level is its primary building's building_level() + 1:
-- the value counts from 0. A ruin - a null building - counts 0. One pcall per
-- region, so a region that fails to answer costs its own levels and nothing else.
function IC.province_levels(faction_key)
    local out = {}
    local ok_f, faction = pcall(real_faction, faction_key)
    if not ok_f or not faction then return out end
    local ok_l, list = pcall(function() return faction:region_list() end)
    if not ok_l or not list then return out end
    local ok_n, n = pcall(function() return list:num_items() end)
    for i = 0, (ok_n and n or 0) - 1 do
        pcall(function()
            local region = list:item_at(i)
            if not region or region:is_null_interface() then return end
            local key = region:province():key()
            local level = 0
            local b = region:settlement():primary_slot():building()
            if b and not b:is_null_interface() then level = b:building_level() + 1 end
            out[key] = (out[key] or 0) + level
        end)
    end
    return out
end

-- WHAT A GOVERNORSHIP OVER `levels` SETTLEMENT LEVELS ADDS TO ITS PARTY.
function IC.gov_weight_of(levels)
    return math.max(1, math.ceil((levels or 0) * IC.TUNE.weight_per_gov_level))
end

function IC.refresh_gov_weight(faction_key)
    local court = IC.court(faction_key)
    for _, house in pairs(court.houses) do house.gov_weight = 0 end
    local levels = IC.province_levels(faction_key)
    for province_key, cqi in pairs(court.govs) do
        local slug = IC.house_of_cqi(faction_key, cqi)
        local house = slug and court.houses[slug]
        if house then
            house.gov_weight = house.gov_weight + IC.gov_weight_of(levels[province_key])
        end
    end
end
```

`real_faction` is the model's local at ~line 1413, above this function. Verify that `IC.province_levels` does not reproduce the line `                    and region:province():key() == province_key then`: an existing mutant anchors on it, and a second copy stales that anchor. Check with `grep -c`.

- [ ] **Step 6: The Help lines**

In the panel Lua's Governors topic, replace

```lua
        "{@bullet}A governorship counts toward his party's weight and loyalty the way a seat does.",
```

with the two lines

```lua
        "{@bullet}A governorship adds to his party's weight: one for every {levels_per_weight} levels of the settlements you hold in his province, and never less than one.",
        "{@bullet}It counts toward his party's loyalty the way a seat does.",
```

In `ICUI.help_vars`, after the `IC.TUNE` copy loop, add:

```lua
    -- THE WEIGHT RULE IN THE PLAYER'S TERMS: levels per point of weight.
    vars.levels_per_weight = 1 / IC.TUNE.weight_per_gov_level
```

The topic then has 11 lines, and `ICUI.HELP_SLOTS` is 12.

- [ ] **Step 7: Run the harness and verify that it passes**

Run: `IC_TEST_ALL=1 "/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | tail -3`
Expected: `iron court harness: ok (834 checks)`.

- [ ] **Step 8: Mutants.** Append to `MUTANTS` in `tools/mutate_iron_court.py`:

```python
    # WEIGHT FROM A DEVELOPED PROVINCE (plan 2026-09-30 Task 1).
    ("a governorship worth the old flat 3 again", M,
     """            house.gov_weight = house.gov_weight + IC.gov_weight_of(levels[province_key])""",
     """            house.gov_weight = house.gov_weight + 3"""),
    ("a province of ruins giving its party nothing", M,
     """    return math.max(1, math.ceil((levels or 0) * IC.TUNE.weight_per_gov_level))""",
     """    return math.max(0, math.ceil((levels or 0) * IC.TUNE.weight_per_gov_level))"""),
    ("settlement levels rounded down", M,
     """    return math.max(1, math.ceil((levels or 0) * IC.TUNE.weight_per_gov_level))""",
     """    return math.max(1, math.floor((levels or 0) * IC.TUNE.weight_per_gov_level))"""),
    ("settlement levels counted from 0", M,
     """            if b and not b:is_null_interface() then level = b:building_level() + 1 end""",
     """            if b and not b:is_null_interface() then level = b:building_level() end"""),
    ("a ruin counted as a village", M,
     """            if b and not b:is_null_interface() then level = b:building_level() + 1 end""",
     """            if b then level = b:building_level() + 1 end"""),
    ("only one settlement of a province counted", M,
     """            out[key] = (out[key] or 0) + level""",
     """            out[key] = out[key] or level"""),
    ("the Help page's weight rule gone", U,
     """    vars.levels_per_weight = 1 / IC.TUNE.weight_per_gov_level""",
     """    vars.levels_per_weight = nil"""),
```

Run: `py tools/mutate_iron_court.py "flat 3" "ruins giving" "rounded down" "counted from 0" "ruin counted" "one settlement of" "weight rule gone"`
Expected: `7 mutants, 0 unexplained`.

- [ ] **Step 9: Gates and ledger.** Every gate, with its expected result:

| Gate | Expected |
|---|---|
| `luac -p` on the two edited Lua files | parses |
| `py tools/check_lua_api.py` on the two edited Lua files | 0 suspects |
| `py tools/check_lua_literal_left.py` | 0 sites |
| `py tools/check_lua_undeclared.py` | clean |
| `py tools/mutate_iron_court.py --selftest` | all anchored |
| `py tools/import_iron_court.py` | `verify ok` |
| the harness | `ok (834 checks)` |

Then ledger `Task 1: complete (tests: harness -> ok (834 checks))`. There is no build here: the rule ships with Task 2's build.

---

### Task 2: Phase 0 - pins and faces on the live map, then STOP for the author's look

**Files:**
- Modify: `tools/gen_iron_court_emitter.py` (`component()`, the `attrs +=` line with `uniqueguid`)
- Modify: `tools/gen_ic_ui.py`
  - `GUID_PREFIXES` (~line 82)
  - `PANEL_LAYOUT` (~line 179)
  - `TEXT_STYLE` (~line 3041)
  - `_panel_order` (~line 3168)
  - `_panel` (~line 3198)
  - `NOT_GEOMETRY` (~line 3685)
  - a new section after `check_map` (~line 4578)
  - `ui_file_names` (~line 3949)
  - `build_xml` (~line 4620)
  - `check` (~line 4869, beside `check_map`)
  - the pie check (~line 5164)
  - `build_plates` (~line 2600)
  - the selftest (~line 7024, beside the `check_map` asserts)
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua`
  - `PANEL_XY` (~line 214)
  - `ICUI.fit_cut` (~line 3251)
  - `ICUI.draw_govs` (~lines 4359-4446)
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui_map.lua`
  - header line 7
  - `leave_on_select` (~line 381)
  - the `ic_map_click` listener (~line 388)
  - a new section before `local court_register = ICUI.register`
- Modify: `tools/_iron_court_harness.lua` (a new fixture after `map_marker`, ~line 5555; new checks; old-list checks deleted)
- Modify: `tools/mutate_iron_court.py`
- Generated: `Modding Files/pack/ui/campaign ui/derpy_ic_gm_pin.twui.xml` and `derpy_ic_gm_face.twui.xml`, plus `ui/derpy_ic/gm_ring_<slug>.png` and `ui/derpy_ic/gm_face_ground.png`

**Interfaces:**
- Produces (emitter): `EU.C(..., mask=<layer index>)` writes `maskimage="<that layer's componentimage GUID>"` on the component.
- Produces (generator):
  - `GM_PIN_FILE`, `GM_FACE_FILE`, `GM_PIN_W = 150`, `GM_PIN_H = 132`;
  - `gm_ring_path(slug)`;
  - `check_gm(pin_text, face_text, panel_text, lua_text=None) -> [problems]`;
  - `check_masks(files) -> [problems]`;
  - `PANEL_LAYOUT["ic_gm_pins"] = (0, 0, 1920, 1080)`, the panel's first child.
- Produces (panel Lua):
  - `ICUI.PANEL_XY.ic_gm_pins`;
  - `ICUI.cut_text(c, text) -> string`;
  - `ICUI.draw_govs(...)` draws nothing and returns `""`.
- Produces (map Lua):
  - `ICUI.GM_PINS = "ic_gm_pins"`, `ICUI.GM_PIN = "ic_gm_pin"`, `ICUI.GM_FACE = "ic_gm_face"`;
  - `ICUI.PATH_GM_PIN`, `ICUI.PATH_GM_FACE`, `ICUI.GM_PIN_W/H`, `ICUI.GM_BACKDROP`;
  - `ICUI.GP_ART/GP_PARTY/GP_CAPITAL/GP_OUTLINE = 0..3`, `ICUI.GF_PORT = 1`, `ICUI.GF_CREST = 2`;
  - `ICUI.gm_keys[i] = province_key`;
  - `ICUI.gm_ring_path(slug)`;
  - `ICUI.gm_on() -> boolean`;
  - `ICUI.gm_clear_pins(panel)`, `ICUI.gm_draw_pins(panel, faction)`, `ICUI.gm_sync()`, `ICUI.gm_pin_click(i)`;
  - `ICUI.refresh`, wrapped so that `gm_sync` runs after every refresh.
- Produces (harness):
  - `with_fake_govmap(fn(hud, panel, extra, holder), screen)`;
  - `gm_pin(holder, i)` and `gm_face(holder, i)`.

- [ ] **Step 1: Snapshot** every file this task edits to the scratchpad as `*_before_govmap_t2.*`.

- [ ] **Step 2: The emitter's mask.** In `tools/gen_iron_court_emitter.py` `component()`, replace

```python
    attrs += ['uniqueguid="%s"' % c.gid,
              'currentstate="%s"' % c.sid, 'defaultstate="%s"' % c.sid]
```

with

```python
    attrs.append('uniqueguid="%s"' % c.gid)
    # A MASK (CA's kislev_atamans drag_icon): the GUID of this component's OWN
    # mask componentimage, the cig the layer list below writes for that index.
    # Between uniqueguid and currentstate, where CA's file carries it. A GUID
    # naming anything else fails in silence; gen_ic_ui.check_masks holds it.
    if kw.get("mask") is not None:
        attrs.append('maskimage="%s"'
                     % c.gid.replace("-D000-", "-D%03d-" % (kw["mask"] * 2 + 1)))
    attrs += ['currentstate="%s"' % c.sid, 'defaultstate="%s"' % c.sid]
```

Run `py tools/gen_ic_ui.py --check`.
Expected: no drift. A component with no `mask` emits byte-identical XML.

- [ ] **Step 3: Write the failing harness checks**

After the `map_marker` helper (~line 5555), add the fixture:

```lua
-- THE GOVERNORS VIEW ON THE FAKE ROOT (plan 2026-09-30). with_fake_root builds
-- the panel from PANEL_XY, the pins' holder among it; this sizes what the view
-- makes in the holder at runtime - a pin and a face per province, each its
-- file's box, which ICUI.cut_text reads - and records each one's file.
local function with_fake_govmap(fn, screen)
    with_fake_root(function(hud, panel, extra)
        local holder = panel.children[ICUI.GM_PINS or "ic_gm_pins"]
        assert(holder, "the fake panel has no pins' holder: PANEL_XY lacks ic_gm_pins")
        local make = holder.CreateComponent
        function holder:CreateComponent(n, p)
            extra.paths[n] = p
            make(self, n, p)
            local c = self.children[n]
            if c then c.w, c.h = ICUI.GM_PIN_W, ICUI.GM_PIN_H end
        end
        ICUI.register()
        fn(hud, panel, extra, holder)
    end, nil, screen)
end

-- THE i-th PIN AND FACE the Governors view made, or nil.
local function gm_pin(holder, i) return holder.children[ICUI.GM_PIN .. "_" .. i] end
local function gm_face(holder, i) return holder.children[ICUI.GM_FACE .. "_" .. i] end
```

Above `check("no parties' turn failed anywhere in the run"`, add:

```lua
check("the Governors tab pins a pin and a face on each province's settlement", function()
    IC.state = {}
    turn = 1
    local gov = make_character(3101, ANY_SEAT, "legion")
    local bare = make_character(3102, ANY_SEAT, "legion")
    make_faction(F, IC.CHD_SUBCULTURE, {gov, bare}, {"prov_a", "prov_b", "prov_c"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    IC.court(F).govs["prov_a"] = 3101
    IC.court(F).govs["prov_c"] = 3102
    IC_TEST_PORTRAITS = {["3101"] = "ui/portraits/portholes/chd/overseer.png"}
    with_fake_govmap(function(hud, panel, extra, holder)
        ICUI.view = "govs"
        ICUI.pick = nil
        ICUI.open()
        local pa, fa = gm_pin(holder, 1), gm_face(holder, 1)
        local pb, fb = gm_pin(holder, 2), gm_face(holder, 2)
        local pc, fc = gm_pin(holder, 3), gm_face(holder, 3)
        assert(pa and fa and pb and fb and pc and fc, "not a pin and a face per province")
        assert(extra.paths[ICUI.GM_PIN .. "_1"] == ICUI.PATH_GM_PIN,
            "a pin from " .. tostring(extra.paths[ICUI.GM_PIN .. "_1"]))
        assert(extra.paths[ICUI.GM_FACE .. "_1"] == ICUI.PATH_GM_FACE,
            "a face from " .. tostring(extra.paths[ICUI.GM_FACE .. "_1"]))
        -- THE PIN FIRST: the face must draw over it.
        local at = {}
        for k, c in ipairs(holder.order) do at[c.name] = k end
        assert(at[pa.name] < at[fa.name], "prov_a's face was made before its pin, so it draws under it")
        -- ONE CONTEXT FOR BOTH, the settlement's cqi.
        assert(pa.context and pa.context.cco == "CcoCampaignSettlement" and pa.context.id == "700",
            "prov_a's pin was given " .. tostring(pa.context and pa.context.id))
        assert(fa.context and fa.context.cco == "CcoCampaignSettlement" and fa.context.id == "700",
            "prov_a's face is not pinned where its pin is")
        assert(pb.context.id == "701" and fb.context.id == "701", "prov_b's pair is not on its settlement")
        -- GOVERNED: his party's ring and his face, no crest over it.
        assert(pa.images[ICUI.GP_PARTY] == ICUI.gm_ring_path("legion"),
            "prov_a's ring: " .. tostring(pa.images[ICUI.GP_PARTY]))
        assert(fa.images[ICUI.GF_PORT] == "ui/portraits/portholes/chd/overseer.png",
            "prov_a's face: " .. tostring(fa.images[ICUI.GF_PORT]))
        assert(fa.images[ICUI.GF_CREST] == ICUI.MASK_NONE, "a crest drawn over a face that resolved")
        assert(fa.image_resize_at[ICUI.GF_PORT] == nil,
            "the face was set with a resize, which blows the component up to the portrait")
        -- A FACE THAT WILL NOT RESOLVE shows his party's crest instead.
        assert(ICUI.crest("legion"), "the fixture's party has no crest to fall back on")
        assert(fc.images[ICUI.GF_PORT] == ICUI.MASK_NONE and fc.images[ICUI.GF_CREST] == ICUI.crest("legion"),
            "an unresolved face drew " .. tostring(fc.images[ICUI.GF_PORT]) .. " / " .. tostring(fc.images[ICUI.GF_CREST]))
        -- UNGOVERNED: a dark head and no ring.
        assert(pb.images[ICUI.GP_PARTY] == ICUI.MASK_NONE, "an empty seat wears a ring")
        assert(fb.images[ICUI.GF_PORT] == ICUI.MASK_NONE and fb.images[ICUI.GF_CREST] == ICUI.MASK_NONE,
            "an empty seat shows a face")
        -- THE CAPITAL'S RING on the capital's province only.
        assert(pa.images[ICUI.GP_CAPITAL] == ICUI.MK_RING_CAPITAL, "the capital's province wears no ring")
        assert(pb.images[ICUI.GP_CAPITAL] == ICUI.MASK_NONE, "another province wears the capital ring")
        assert(pa.images[ICUI.GP_OUTLINE] == ICUI.MASK_NONE, "a province is ringed with nothing chosen")
        -- TWO LINES OF THE PIN'S OWN TEXT (plan ruling 7): the name, then loyalty.
        assert(pa.text == string.format("prov_a\nLoyalty %d%%", IC.province_loyalty(F, "prov_a")),
            "prov_a's pin reads " .. tostring(pa.text))
        assert(fa.text == "", "the face carries text, which its mask would clip")
        assert(pa.tooltip and pa.tooltip:find("prov_a", 1, true) and pa.tooltip_all_states == true,
            "the pin has no tooltip on every state")
        assert(next(pa.children) == nil and next(fa.children) == nil,
            "a pin grew a child, which the engine would draw at its corner")
        assert(ICUI.gm_keys[1] == "prov_a" and ICUI.gm_keys[2] == "prov_b" and ICUI.gm_keys[3] == "prov_c",
            "the click keys do not follow the pins")
    end)
    IC_TEST_PORTRAITS = nil
end)

check("the Governors view clears the backdrop and lets the map have the mouse; leaving it puts both back",
function()
    IC.state = {}
    make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a", "prov_b"})
    IC.add_house(F, IC.CROWN)
    with_fake_govmap(function(hud, panel, extra, holder)
        ICUI.view = "court"
        ICUI.pick = nil
        ICUI.open()
        assert(panel.interactive == true, "the court does not take the mouse")
        map_click("ic_tab_govs")
        assert(panel.images[0] == ICUI.MASK_NONE, "the throne room still covers the map: " .. tostring(panel.images[0]))
        assert(panel.interactive == false, "the panel still eats every click on the map")
        assert(gm_pin(holder, 1) and gm_pin(holder, 2), "no pins on the Governors tab")
        -- EVERY WAY OUT BUT CLOSE, which destroys the panel with its pins.
        for _, tab in ipairs({"ic_tab_court", "ic_tab_offices", "ic_tab_intrigue",
                              "ic_tab_petitions", "ic_tab_log", "ic_help"}) do
            map_click("ic_tab_govs")
            local pin = gm_pin(holder, 1)
            assert(pin, "no pin to leave behind before " .. tab)
            map_click(tab)
            assert(panel.images[0] == ICUI.GM_BACKDROP, tab .. " left the map showing: " .. tostring(panel.images[0]))
            assert(panel.interactive == true, tab .. " left the panel letting clicks through")
            assert(pin.destroyed and gm_pin(holder, 1) == nil, tab .. " left the pins up")
            if tab == "ic_help" then map_click("ic_help") end
        end
    end)
end)

check("the Governors view hides the court's list, its headers and its pager", function()
    IC.state = {}
    make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    with_fake_govmap(function(hud, panel, extra, holder)
        ICUI.view = "log"
        ICUI.pick = nil
        ICUI.open()
        assert(panel.children[ICUI.ROW .. "_1"].visible, "the fixture's Record drew no row, so this check watches nothing")
        map_click("ic_tab_govs")
        for i = 1, ICUI.MAX_ROWS do
            assert(not panel.children[ICUI.ROW .. "_" .. i].visible, "row " .. i .. " of the last tab's list shows over the map")
        end
        for _, keys in ipairs({ICUI.HDR_KEYS, ICUI.HSORT_KEYS, {"ic_page_prev", "ic_page_lbl", "ic_page_next"}}) do
            for _, name in ipairs(keys) do
                assert(not panel.children[name].visible, name .. " shows over the map")
            end
        end
    end)
end)

check("a pin opens the governor picker for its province, and a lost province redraws instead", function()
    IC.state = {}
    make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a", "prov_b"})
    IC.add_house(F, IC.CROWN)
    with_fake_govmap(function(hud, panel, extra, holder)
        ICUI.view = "govs"
        ICUI.pick = nil
        ICUI.open()
        map_click(ICUI.GM_PIN .. "_2")
        assert(ICUI.pick and ICUI.pick.kind == "gov" and ICUI.pick.key == "prov_b",
            "the pin opened " .. tostring(ICUI.pick and ICUI.pick.key))
        assert(not panel.destroyed, "the pin closed the court")
        -- PHASE 0: the court's own picker, over its own backdrop (plan ruling 4).
        assert(panel.images[0] == ICUI.GM_BACKDROP and panel.interactive == true,
            "the picker opened over a see-through panel")
        ICUI.pick = nil
        ICUI.refresh()
        -- prov_b FALLS between the draw and the click.
        make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a"})
        map_click(ICUI.GM_PIN .. "_2")
        assert(ICUI.pick == nil, "a lost province reached the picker")
        assert(gm_pin(holder, 1) and gm_pin(holder, 2) == nil, "the view did not redraw on the stale click")
    end)
end)

check("selecting a settlement or a character through the Governors view closes the court", function()
    IC.state = {}
    make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a"})
    IC.add_house(F, IC.CROWN)
    local ctx = {character = function() return nil end, garrison_residence = function() return nil end}
    for _, name in ipairs({"ic_map_char_selected", "ic_map_settlement_selected"}) do
        with_fake_govmap(function(hud, panel, extra, holder)
            ICUI.view = "govs"
            ICUI.pick = nil
            ICUI.open()
            core.listeners[name](ctx)
            assert(panel.destroyed, name .. " left the court up over what the player selected")
            assert(hud.visible == true, name .. " left the HUD hidden")
        end)
        -- ON ANY OTHER TAB the court is opaque: nothing was selected through it.
        with_fake_govmap(function(hud, panel, extra, holder)
            ICUI.view = "court"
            ICUI.pick = nil
            ICUI.open()
            core.listeners[name](ctx)
            assert(not panel.destroyed, name .. " closed the court from the Court tab")
        end)
    end
end)

check("the pins' holder is the screen at any screen size, not the court's box", function()
    IC.state = {}
    make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a"})
    IC.add_house(F, IC.CROWN)
    for _, screen in ipairs({{2560, 1080}, {1600, 900}}) do
        with_fake_govmap(function(hud, panel, extra, holder)
            ICUI.view = "govs"
            ICUI.pick = nil
            ICUI.open()
            local at = screen[1] .. "x" .. screen[2]
            assert(holder.x == 0 and holder.y == 0, at .. ": the holder sits at " .. holder.x .. "," .. holder.y)
            assert(holder.w == screen[1] and holder.h == screen[2],
                at .. ": the holder is " .. holder.w .. "x" .. holder.h)
            assert(gm_pin(holder, 1), "no pin at " .. at)
        end, screen)
    end
    ICUI.apply_scale(1920)
end)

check("a refresh repaints the pins in place rather than remaking them", function()
    IC.state = {}
    make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a", "prov_b"})
    IC.add_house(F, IC.CROWN)
    with_fake_govmap(function(hud, panel, extra, holder)
        ICUI.view = "govs"
        ICUI.pick = nil
        ICUI.open()
        local pin, face = gm_pin(holder, 1), gm_face(holder, 1)
        ICUI.refresh()
        -- A PIN MADE FROM LUA STARTS AT THE HOLDER'S CORNER: remade on every
        -- click, every pin would flash there.
        assert(gm_pin(holder, 1) == pin and not pin.destroyed, "a refresh remade prov_a's pin")
        assert(gm_face(holder, 1) == face and not face.destroyed, "a refresh remade prov_a's face")
    end)
end)

check("a pin cuts a province name too long for it, and its tooltip keeps it whole", function()
    IC.state = {}
    make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a"})
    IC.add_house(F, IC.CROWN)
    local long = "The Blasted Wastes of Zharr-Naggrund and Everything Beyond"
    IC_TEST_LOC = {provinces_onscreen_prov_a = long}
    with_fake_govmap(function(hud, panel, extra, holder)
        ICUI.view = "govs"
        ICUI.pick = nil
        ICUI.open()
        local pin = gm_pin(holder, 1)
        local name = string.match(pin.text, "^([^\n]*)\n")
        assert(name and name ~= long and name:sub(-3) == "...", "the name was not cut: " .. tostring(pin.text))
        assert(#name * pin.text_px <= pin.w, "the cut name still overruns the pin: " .. name)
        assert(pin.tooltip:find(long, 1, true), "the tooltip lost the whole name")
    end)
    IC_TEST_LOC = nil
end)
```

Before writing these, check two names: how `IC_TEST_LOC` is read (`grep -n IC_TEST_LOC tools/_iron_court_harness.lua | head -3`), and that `fake_component` records `image_resize_at`. It does (~line 5245).

- [ ] **Step 4: Run the harness and verify that it fails**

Run: `IC_TEST_ALL=1 "/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | grep -c "^FAIL"`
Expected: the 8 new checks fail, on `the fake panel has no pins' holder`, a nil `ICUI.GM_PIN`, or similar. No other check fails.

- [ ] **Step 5: The pins and the face in the generator**

In `GUID_PREFIXES`, after the IC46 line, add:

```python
    # IC47-IC48 - THE GOVERNORS VIEW (spec 2026-09-30): the pin and the face,
    # made once each per province into the panel's first child. Never scaled.
    "derpy_ic_gm_pin.twui.xml":     "IC47",
    "derpy_ic_gm_face.twui.xml":    "IC48",
```

In `PANEL_LAYOUT` (after `"ic_influence"`), add:

```python
    # THE GOVERNORS VIEW'S PINS' HOLDER (spec 2026-09-30), the panel's FIRST
    # child (check_gm): pins made in it draw under everything this file
    # declares. Moved to the screen's corner and sized to the screen at every
    # draw, as the party map's layer was: a pin is placed in screen space.
    "ic_gm_pins": (0, 0, 1920, 1080),
```

In `TEXT_STYLE`, add `"ic_gm_pin": (12, "body_12"),`.

At the top of `_panel_order`'s body, add:

```python
    if name == "ic_gm_pins":
        # FIRST OF ALL (check_gm), and under tier -1 on purpose: make_ic_backdrop
        # takes every tier -1 name for an opaque plate on every view.
        return (-3, name)
```

As the first statement inside `_panel()`'s `for name in sorted(PANEL_LAYOUT, key=_panel_order):` loop, after `_x, _y, w, h = PANEL_LAYOUT[name]`, add:

```python
        if name == "ic_gm_pins":
            # NO ART AND NO CLICKS: the bare map beside a pin must take the click.
            panel.add(EU.C(name, w, h))
            continue
```

In the pie check (~line 5164), add as the loop's first exemption:

```python
        if name.startswith("ic_gm_"):
            # THE GOVERNORS VIEW'S OWN, shown on that view only: the harness
            # holds them gone on every other ("...leaving it puts both back").
            continue
```

After `check_map` (before `def check_rim_slots`), add the section:

```python
# ---------------------------------------------------------------------------
# THE GOVERNORS VIEW'S PINS (spec 2026-09-30 sections 1 and 6). Two files, made
# at runtime into the panel's first child and never scaled (plan ruling 1):
# a PIN - CA's Chaos Dwarf map pin, the party ring, the capital and outline
# rings, one plate with two lines of its own text; it takes the click - and a
# FACE - the governor's portrait or his party's crest, masked round in the
# pin's head; it takes nothing. One box and one settlement context each, so
# the engine anchors the two identically.
GM_PIN_FILE = "derpy_ic_gm_pin.twui.xml"
GM_FACE_FILE = "derpy_ic_gm_face.twui.xml"
GM_PIN_W, GM_PIN_H = 150, 132
GM_PIN_ART = "ui/skins/default/dlc23_chd_narrative_panel/chd_narrative_panel_map_pin.png"
GM_PIN_ART_BOX = (50, 4, 50, 80)        # CA's 50x80, centred across the box
GM_HEAD = (56, 9, 38, 38)               # its head: CA's 38x38 image at 6,5
GM_RING = 46                            # the party ring, 4px, round the head
GM_RING_OUTER = 54                      # the capital and outline rings
GM_PLATE = "ui/skins/default/dlc23_chd_hell_forge/sub_title.png"
GM_PLATE_BOX = (0, 88, 150, 44)         # two lines of body_12
GM_PORT_BOX = (40, 9, 70, 38)           # a porthole at its own aspect across the head
GM_FACE_GROUND = PLATE_DIR + "/gm_face_ground.png"
GM_FACE_GROUND_COLOUR = "#1A1410FF"
GM_MASK = "ui/skins/default/porthole_mask.png"
# THE LAYERS THE LUA PAINTS, IN ORDER. Must match ICUI.GP_* and ICUI.GF_* in
# zzz_derpy_iron_court_ui_map.lua (check_gm). The pin's plate follows its four.
GM_PIN_LAYERS = ["art", "party", "capital", "outline"]
GM_FACE_LAYERS = ["ground", "port", "crest", "mask"]
LAYOUT_TABLES[GM_PIN_FILE] = {"derpy_ic_gm_pin": (0, 0, GM_PIN_W, GM_PIN_H)}
LAYOUT_TABLES[GM_FACE_FILE] = {"derpy_ic_gm_face": (0, 0, GM_PIN_W, GM_PIN_H)}


def gm_ring_path(slug):
    return "%s/gm_ring_%s.png" % (PLATE_DIR, slug)


def _gm_layer(box, path=None, margin=0):
    """An image layer at `box` inside the pin's box."""
    x, y, w, h = box
    return {"path": path or MASK_NONE, "offset": (x, y), "dw": w - GM_PIN_W,
            "dh": h - GM_PIN_H, "margin": margin, "dock": None}


def _gm_ring(size):
    """A `size` square centred on the pin's head."""
    hx, hy, hw, hh = GM_HEAD
    return _gm_layer((hx + (hw - size) / 2.0, hy + (hh - size) / 2.0, size, size))


def _gm_pin():
    root = EU.C("root", GM_PIN_W, GM_PIN_H)
    root.add(EU.C(
        "derpy_ic_gm_pin", GM_PIN_W, GM_PIN_H, interactive=True,
        sound=OPENER_SOUND, callbacks=[MAP_PIN],
        layers=[_gm_layer(GM_PIN_ART_BOX, GM_PIN_ART), _gm_ring(GM_RING),
                _gm_ring(GM_RING_OUTER), _gm_ring(GM_RING_OUTER),
                _gm_layer(GM_PLATE_BOX, GM_PLATE, (0, 12))],
        **style("ic_gm_pin", align="Center", valign="Bottom", tx="0.00,0.00",
                ty="0.00,0.00", leading=0)))
    return root


def _gm_face():
    root = EU.C("root", GM_PIN_W, GM_PIN_H)
    # NOT INTERACTIVE: the pin under it takes the click and the tooltip.
    root.add(EU.C(
        "derpy_ic_gm_face", GM_PIN_W, GM_PIN_H, callbacks=[MAP_PIN],
        layers=[_gm_layer(GM_HEAD, GM_FACE_GROUND), _gm_layer(GM_PORT_BOX),
                _gm_layer(GM_HEAD), _gm_layer(GM_HEAD, GM_MASK)],
        mask=GM_FACE_LAYERS.index("mask")))
    return root


def gm_pin_xml():
    return EU.layout(EU.assign(_gm_pin(), GUID_PREFIXES[GM_PIN_FILE]),
                     "derpy: one Iron Court governor pin, pinned to a settlement by "
                     "CA's ContextWorldSpaceComponent; generated by tools/gen_ic_ui.py.")


def gm_face_xml():
    return EU.layout(EU.assign(_gm_face(), GUID_PREFIXES[GM_FACE_FILE]),
                     "derpy: one Iron Court governor's masked face, pinned beside its "
                     "pin; generated by tools/gen_ic_ui.py.")


def _component_blocks(text):
    """name -> its <components> block, for every component of a file."""
    body = text.split("<components>", 1)[-1]
    out = {}
    for block in re.split(r"(?m)^\t\t<(?=\w)", body)[1:]:
        out[re.match(r"(\w+)", block).group(1)] = block
    return out


def check_masks(files):
    """Every maskimage names a component_image of its own component."""
    out = []
    for fname, text in sorted(files.items()):
        for name, block in sorted(_component_blocks(text).items()):
            m = re.search(r'maskimage="([^"]+)"', block)
            if m and ('<component_image\n\t\t\t\t\tthis="%s"' % m.group(1)) not in block:
                out.append("%s: %s's maskimage %s names no component_image of its "
                           "own, so it masks nothing" % (fname, name, m.group(1)))
    return out


def check_gm(pin_text=None, face_text=None, panel_text=None, lua_text=None):
    """The pins' holder first and inert; CA's pin on both files; the Lua's numbers ours."""
    out = []
    pt = pin_text if pin_text is not None else gm_pin_xml()
    ft = face_text if face_text is not None else gm_face_xml()
    if panel_text is None:
        panel_text = EU.layout(EU.assign(_panel(), GUID_PREFIXES["derpy_ic_panel.twui.xml"]), "")
    tree = panel_text.split("<hierarchy>", 1)[-1].split("</hierarchy>", 1)[0]
    first = re.search(r"<derpy_ic_panel [^>]*>\s*<(\w+)", tree)
    if not first or first.group(1) != "ic_gm_pins":
        out.append("derpy_ic_panel.twui.xml: ic_gm_pins is not the panel's first child, "
                   "so a pin draws over the court")
    holder = _component_blocks(panel_text).get("ic_gm_pins", "")
    if not holder or 'interactive="true"' in holder:
        out.append("derpy_ic_panel.twui.xml: ic_gm_pins is missing or takes clicks, so "
                   "the bare map beside a pin would not")
    for fname, t in ((GM_PIN_FILE, pt), (GM_FACE_FILE, ft)):
        if 'callback_id="%s"' % MAP_PIN["id"] not in t:
            out.append("%s: no %s callback" % (fname, MAP_PIN["id"]))
        if 'context_function_id="%s"' % MAP_PIN["function"] not in t:
            out.append("%s: %s's function is not CA's" % (fname, MAP_PIN["id"]))
        if 'context_object_id="CcoCampaignSettlement"' not in t:
            out.append("%s: not pinned on CcoCampaignSettlement" % fname)
        if 'name="depth_disabled"' not in t:
            out.append("%s: the pin lost depth_disabled" % fname)
        # NO FADE: see check_map - a runtime-made pin starts at y = 0 and fades out.
        if 'callback_id="ContextOpacitySetter"' in t:
            out.append("%s: carries a ContextOpacitySetter - it drew nothing in game" % fname)
        # ROOT AND ONE COMPONENT (plan ruling 1): a child would draw at the corner.
        ids = re.findall(r'\n\t\t\tid="([^"]+)"', t)
        want = ["root", fname.replace(".twui.xml", "")]
        if ids != want:
            out.append("%s: components %r - a pin may have no children" % (fname, ids))
    # ONE BOX FOR BOTH, or the engine anchors them apart: read off the two
    # emitted components, not off the constant both were built from.
    def _box(t, name):
        m = re.search(r'width="(\d+)"\n\t\t\t\t\theight="(\d+)"',
                      _component_blocks(t).get(name, ""))
        return m and (int(m.group(1)), int(m.group(2)))
    if not _box(pt, "derpy_ic_gm_pin") or _box(pt, "derpy_ic_gm_pin") != _box(ft, "derpy_ic_gm_face"):
        out.append("the pin is %r and the face %r, so the engine anchors them apart"
                   % (_box(pt, "derpy_ic_gm_pin"), _box(ft, "derpy_ic_gm_face")))
    if 'interactive="true"' not in pt:
        out.append("%s: the pin takes no click" % GM_PIN_FILE)
    if 'interactive="true"' in ft:
        out.append("%s: the face takes clicks, so the pin under it never gets one"
                   % GM_FACE_FILE)
    if 'maskimage="' not in ft:
        out.append("%s: the face has no maskimage, so it draws square" % GM_FACE_FILE)
    lua = lua_text if lua_text is not None else _lua_map_tables()
    m = re.search(r"ICUI\.GM_PIN_W,\s*ICUI\.GM_PIN_H\s*=\s*(\d+),\s*(\d+)", lua)
    if not m or (int(m.group(1)), int(m.group(2))) != (GM_PIN_W, GM_PIN_H):
        out.append("ICUI.GM_PIN_W/H are not the generator's %dx%d" % (GM_PIN_W, GM_PIN_H))
    m = re.search(r"ICUI\.GP_ART,\s*ICUI\.GP_PARTY,\s*ICUI\.GP_CAPITAL,\s*ICUI\.GP_OUTLINE"
                  r"\s*=\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)", lua)
    if not m or [int(v) for v in m.groups()] != list(range(len(GM_PIN_LAYERS))):
        out.append("ICUI.GP_* do not name the pin's layers 0..3 in order")
    m = re.search(r"ICUI\.GF_PORT,\s*ICUI\.GF_CREST\s*=\s*(\d+),\s*(\d+)", lua)
    if not m or (int(m.group(1)), int(m.group(2))) != (
            GM_FACE_LAYERS.index("port"), GM_FACE_LAYERS.index("crest")):
        out.append("ICUI.GF_PORT/GF_CREST do not name the face's port and crest layers")
    m = re.search(r'ICUI\.GM_BACKDROP\s*=\s*"([^"]+)"', lua)
    if not m or m.group(1) != PANEL_BG:
        out.append("ICUI.GM_BACKDROP is not PANEL_BG, %s: leaving the view would "
                   "put the wrong ground back" % PANEL_BG)
    return out
```

In `build_plates`, after the two `MAP_RING_*` lines, add:

```python
    # THE GOVERNORS VIEW'S PARTY RINGS AND THE FACE'S GROUND (plan ruling 6):
    # one ring per party and per absorbed faction, painted by SetImagePath.
    for p in IC.PARTIES:
        out[gm_ring_path(p[0])] = map_ring_pixels(HOUSE_COLOUR[p[0]], GM_RING, 4)
    for slug in CONFED_SEATS:
        out[gm_ring_path(slug)] = map_ring_pixels(CONFED_COLOUR[slug], GM_RING, 4)
    out[GM_FACE_GROUND] = map_disc_pixels(GM_FACE_GROUND_COLOUR, GM_HEAD[2])
```

Wire the new section into the rest of the generator:
- In `ui_file_names`, add `GM_PIN_FILE, GM_FACE_FILE` after `MARKER_FILE`.
- In `build_xml`, after `out[MARKER_FILE] = marker_xml()`, add `out[GM_PIN_FILE] = gm_pin_xml()` and `out[GM_FACE_FILE] = gm_face_xml()`.
- In `check()`, after `out.extend(check_map(...))`, add:

```python
    # 1c2. The Governors view's pins, the holder they stand in, and every mask.
    out.extend(check_gm(all_files.get(GM_PIN_FILE, ""), all_files.get(GM_FACE_FILE, ""),
                        all_files.get("derpy_ic_panel.twui.xml", "")))
    out.extend(check_masks(all_files))
```

- Append to `NOT_GEOMETRY`:

```python
    "GM_PIN_FILE", "GM_FACE_FILE", "GM_PIN_W", "GM_PIN_H", "GM_PIN_ART", "GM_PIN_ART_BOX",
    "GM_HEAD", "GM_RING", "GM_RING_OUTER", "GM_PLATE", "GM_PLATE_BOX", "GM_PORT_BOX",
    "GM_FACE_GROUND", "GM_FACE_GROUND_COLOUR", "GM_MASK", "GM_PIN_LAYERS", "GM_FACE_LAYERS",
```

In the selftest, beside the `check_map` asserts (~line 7024), add:

```python
    assert not check_gm(), check_gm()
    assert not check_masks({GM_FACE_FILE: gm_face_xml()}), check_masks({GM_FACE_FILE: gm_face_xml()})
    assert any("names no component_image" in e for e in check_masks(
        {GM_FACE_FILE: gm_face_xml().replace('maskimage="IC48', 'maskimage="IC99')})), \
        "a maskimage naming another component went unreported"
    _pn = EU.layout(EU.assign(_panel(), GUID_PREFIXES["derpy_ic_panel.twui.xml"]), "")
    assert any("first child" in e for e in check_gm(
        panel_text=_pn.replace("<ic_gm_pins ", "<ic_gm_pinz ", 1))), \
        "a holder that is not the first child went unreported"
    assert any("takes clicks" in e for e in check_gm(face_text=gm_face_xml().replace(
        'name="standard"', 'name="standard"\n\t\t\t\t\tinteractive="true"', 1))), \
        "a face that takes clicks went unreported"
    assert any("no maskimage" in e for e in check_gm(face_text=re.sub(
        r'\n\t\t\tmaskimage="[^"]+"', "", gm_face_xml()))), \
        "a face with no mask went unreported"
    assert any("GM_BACKDROP" in e for e in check_gm(lua_text=_lua_map_tables().replace(
        "panel_bg.png", "panel_bgx.png"))), "a wrong backdrop path went unreported"
    assert any("anchors them apart" in e for e in check_gm(face_text=gm_face_xml().replace(
        'height="%d"' % GM_PIN_H, 'height="%d"' % (GM_PIN_H - 2)))), \
        "a face boxed apart from its pin went unreported"
```

Keep `_pn` local to the selftest function. If the selftest function defines its checks with a different pattern, match it.

- [ ] **Step 6: The panel Lua**

In `ICUI.PANEL_XY`, after `ic_influence`, add:

```lua
    -- THE GOVERNORS VIEW'S PINS' HOLDER (plan 2026-09-30), the panel's first
    -- child. zzz_derpy_iron_court_ui_map.lua moves it to the screen's corner and
    -- sizes it to the screen at every draw. Must match tools/gen_ic_ui.py.
    ic_gm_pins       = {0, 0, 1920, 1080},
```

Split `ICUI.fit_cut` (plan ruling 9) in four edits:
1. Rename its header, and the guard under it:
   - `function ICUI.fit_cut(c, text)` becomes `function ICUI.cut_text(c, text)`;
   - its `    if not c then return end` becomes `    if not c then return text end`.
2. In its zero-width branch, replace `        set_text(c, text)` + `        return` with `        return text`.
3. Replace `        set_text(c, table.concat(words, " ", 1, kept) .. "...")` + `        return` with `        return table.concat(words, " ", 1, kept) .. "..."`.
4. Replace its last statement, `    set_text(c, string.sub(text, 1, n) .. "...")`, with `    return string.sub(text, 1, n) .. "..."`.

Then, after that function's `end`, add:

```lua

-- THE STRING, RETURNED, for a cell that draws more than the cut line: a pin's
-- name is the first of its two lines (plan 2026-09-30 ruling 9). fit_cut is
-- this, drawn.
function ICUI.fit_cut(c, text)
    if not c then return end
    set_text(c, ICUI.cut_text(c, text))
end
```

Also put the comment block that sat above `fit_cut` above `cut_text`.

Replace the whole of `ICUI.draw_govs` (from `function ICUI.draw_govs(panel, faction, court)` through the `end` after `ICUI.fill_rows(panel, lines, "govs")` + `return ""`) with:

```lua
-- THE GOVERNORS TAB DRAWS NO LIST (spec 2026-09-30): its provinces are pinned
-- on the live map and listed in the column, both drawn by
-- zzz_derpy_iron_court_ui_map.lua after this refresh. gov_keys stays empty, so
-- nothing reads a province off a row of the court's pool.
function ICUI.draw_govs(_panel, _faction, _court)
    ICUI.gov_keys = {}
    return ""
end
```

`ICUI.gov_holder_text` and `ICUI.gov_rank_tip`, just above it, stay: Task 4's rows use them.

- [ ] **Step 7: The map Lua**

Change line 7 to:

```lua
local comp, set_text, loc, root, show = ICUI.comp, ICUI.set_text, ICUI.loc, ICUI.root, ICUI.show
```

Replace `leave_on_select`'s body with:

```lua
local function leave_on_select()
    if comp(ICUI.MAP) then ICUI.map_close() end
    -- THE GOVERNORS VIEW IS SEE-THROUGH, so a click through it can select what
    -- stands under it: leave the player on what they clicked (spec section 2).
    if ICUI.gm_on() then ICUI.close() end
end
```

In the `ic_map_click` listener, after the `ICUI.MARKER` branch, add:

```lua
        elseif string.match(id or "", "^" .. ICUI.GM_PIN .. "_%d+$") and comp(ICUI.PANEL) then
            ICUI.gm_pin_click(tonumber(string.match(id, "_(%d+)$")))
```

Before `local court_register = ICUI.register`, add the section:

```lua
-- ---------------------------------------------------------------------------
-- THE GOVERNORS VIEW ON THE LIVE MAP (docs/superpowers/specs/2026-09-30-iron-
-- court-governors-map-design.md). On the Governors tab the court's backdrop
-- clears, the panel lets the map have the mouse, and each held province gets a
-- PIN and a FACE: two siblings with one box and one settlement context, made in
-- the panel's first child so they draw under everything the panel file declares
-- (plan ruling 1).
ICUI.PATH_GM_PIN = "ui/campaign ui/derpy_ic_gm_pin"
ICUI.PATH_GM_FACE = "ui/campaign ui/derpy_ic_gm_face"
ICUI.GM_PINS = "ic_gm_pins"
ICUI.GM_PIN = "ic_gm_pin"
ICUI.GM_FACE = "ic_gm_face"
-- Must match GM_PIN_W/H, GM_PIN_LAYERS and GM_FACE_LAYERS in tools/gen_ic_ui.py.
ICUI.GM_PIN_W, ICUI.GM_PIN_H = 150, 132
ICUI.GP_ART, ICUI.GP_PARTY, ICUI.GP_CAPITAL, ICUI.GP_OUTLINE = 0, 1, 2, 3
ICUI.GF_PORT, ICUI.GF_CREST = 1, 2
-- THE THRONE ROOM, put back on every other view. Must be PANEL_BG (check_gm).
ICUI.GM_BACKDROP = "ui/derpy_ic/panel_bg.png"
ICUI.gm_keys = {}            -- pin index -> province key, as last drawn
for _, n in ipairs({"GM_PIN_W", "GM_PIN_H", "GP_ART", "GP_PARTY", "GP_CAPITAL",
                    "GP_OUTLINE", "GF_PORT", "GF_CREST"}) do
    ICUI.NOT_SCALED[#ICUI.NOT_SCALED + 1] = n
end

-- A PARTY'S RING, or none: "" is truthy in Lua (see ICUI.plate_path).
function ICUI.gm_ring_path(slug)
    if not slug or slug == "" then return ICUI.MASK_NONE end
    return "ui/derpy_ic/gm_ring_" .. slug .. ".png"
end

-- THE VIEW IS UP: the court open on its Governors tab with no picker over it.
function ICUI.gm_on()
    return (comp(ICUI.PANEL) and ICUI.view == "govs" and ICUI.pick == nil) and true or false
end

-- ONE PROVINCE'S PIN AND FACE OFF THE HOLDER, by the names gm_draw_pins uses.
local function drop_pair(pins, i)
    for _, name in ipairs({ICUI.GM_PIN .. "_" .. i, ICUI.GM_FACE .. "_" .. i}) do
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

function ICUI.gm_draw_pins(panel, faction)
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
    -- holder's corner until the engine places it (check_map's fade note), so
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
        local pin_name, face_name = ICUI.GM_PIN .. "_" .. i, ICUI.GM_FACE .. "_" .. i
        if not cqi then
            drop_pair(pins, i)
        else
            if not (comp(pin_name, pins) and comp(face_name, pins)) then
                drop_pair(pins, i)
                -- THE PIN FIRST, so the face - made after it - draws over it.
                pins:CreateComponent(pin_name, ICUI.PATH_GM_PIN)
                pins:CreateComponent(face_name, ICUI.PATH_GM_FACE)
            end
            local pin, face = comp(pin_name, pins), comp(face_name, pins)
            if pin and face then
                local at = cco("CcoCampaignSettlement", cqi)
                pin:SetContextObject(at)
                face:SetContextObject(at)
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
                -- TWO LINES OF ITS OWN TEXT (plan ruling 7), the name cut to the
                -- pin; the tooltip carries it whole.
                set_text(pin, ICUI.cut_text(pin, loc("provinces_onscreen_" .. province, province))
                         .. "\n" .. string.format("Loyalty %d%%",
                                                  IC.province_loyalty(faction, province)))
                pin:SetTooltipText(ICUI.map_tip(faction, province), "", true)
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
    pcall(function() panel:SetImagePath(on and ICUI.MASK_NONE or ICUI.GM_BACKDROP, 0) end)
    panel:SetInteractive(not on)
    if not on then ICUI.gm_clear_pins(panel) return end
    -- THE COURT'S LIST FURNITURE, which this view does not draw and which the
    -- last tab may have left showing.
    for _, keys in ipairs({ICUI.HDR_KEYS, ICUI.HSORT_KEYS,
                           {"ic_page_prev", "ic_page_lbl", "ic_page_next"}}) do
        for _, name in ipairs(keys) do show(comp(name, panel), false) end
    end
    for i = 1, ICUI.MAX_ROWS do show(comp(ICUI.ROW .. "_" .. i, panel), false) end
    ICUI.gm_draw_pins(panel, ICUI.player())
end

-- AFTER the court's own refresh, whatever it drew.
local court_refresh = ICUI.refresh
function ICUI.refresh(...)
    court_refresh(...)
    local ok, err = pcall(ICUI.gm_sync)
    if not ok then IC.warn("IRON COURT: the Governors map failed to draw: " .. tostring(err)) end
end

-- A PIN: the governor picker for its province. PHASE 0 opens the court's own
-- (plan ruling 4); Task 5 moves it into the column.
function ICUI.gm_pin_click(index)
    local faction = ICUI.player()
    local province = ICUI.gm_keys[index]
    if not faction or not province then return end
    -- STILL YOURS: IC.assign_governor does not ask, so a province lost since the
    -- pins drew must not reach it. The view redraws instead.
    local held = false
    for _, p in ipairs(IC.seats(faction)) do if p == province then held = true end end
    if not held then ICUI.refresh() return end
    ICUI.pick = {kind = "gov", key = province}
    ICUI.scroll.pick = 0
    ICUI.notice = nil
    ICUI.refresh()
end
```

Verify `IC.warn` exists: `grep -n "^function IC.warn" "Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua"`. The old `map_open` already uses it.

- [ ] **Step 8: Generate and run the harness**

Run: `py tools/gen_ic_ui.py && IC_TEST_ALL=1 "/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | grep "^FAIL" > "$SCRATCH/t2_fails.txt"; wc -l < "$SCRATCH/t2_fails.txt"`. Here `$SCRATCH` is the session scratchpad.

Expected:
- the 8 new checks pass;
- the old Governors list's checks fail, because the list is gone;
- no other check fails, except the generic ones triaged in step 9.

- [ ] **Step 9: Retire the old list's checks (plan ruling 11)**

Delete each check below. It tests the court's row pool on the Governors tab, which no longer draws. Its successor is named, and is written in the task given.

| Deleted check (line at planning) | Successor |
|---|---|
| "releasing a governor uses the scrolled row, not the raw one" (~7224) | Task 4: "the cross releases the selected province, whatever page it is on" |
| "a filled seat draws the overseer's face, an empty one draws nothing" (~7985) | Task 4: "a Provinces row draws its governor's face, his crest, or an empty seat" |
| "a face that will not resolve falls back to the house crest" (~8040) | same Task 4 check, and Task 2's pin check (prov_c) |
| "the governors list shows province NAMES, not province keys" (~8859) | Task 4: the same row check, which asserts `provinces_onscreen_` names |
| "an ungoverned province wears no colours behind its silhouette" (~8895) | same Task 4 row check |
| "a sorted governors list opens the province it drew" (~8945) | Task 4: "a sorted Provinces page chooses and appoints the province it drew, and keeps it through a sort" |
| "every province is reachable once the list outruns the pool" (~9058) | Task 4: "every province is reachable once the Provinces page outruns its rows" |
| "a governed province's row is lit, an away one dim, and other views clear it" (~24060) | Task 4 row check: "(away)" in words, since the column has no rim |
| "releasing a governor is answered, and assigning one bursts his row" (~24105) | Task 4: "the cross releases..." asserts the answer. There is no row burst on this view: ruling in the ledger |
| "assigning a governor bursts the row his province is drawn on after the redraw" (~26668) | none. The burst was a row pool effect, and ICUI.confirm plays the sound. Ruling in the ledger |

For every other check in `$SCRATCH/t2_fails.txt`, read it:
- **It fails only on its Governors case** (for example a loop over `ICUI.TAB_VIEW` that expects rows, headers or the pager on `govs`). Drop `govs` from that loop's expectation with the comment `-- NOT GOVERNORS: that view draws the live map (plan 2026-09-30); its own checks hold it.`, and ledger a ruling naming the check.
- **It fails for another reason.** The code is wrong: debug it (superpowers:systematic-debugging) and do not edit the check.

The check "each of the twelve panel clicks sends in multiplayer..." (~21840) needs no change here, and must pass unchanged:
- its `assign_governor` case drives `ICUI.on_pick_click`, which stays;
- its `release_governor` case sets `ICUI.gov_keys` itself and calls `ICUI.on_row_action`, whose Governors branch Task 6 deletes.

Tasks 4 and 5 give the column's cross and check multiplayer checks of their own. Task 6 then removes the `release_governor` case.

Run: `IC_TEST_ALL=1 "/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | tail -3`
Expected: `iron court harness: ok (N checks)`, where N = 834 + 8 - (checks deleted). Record N.

- [ ] **Step 10: Mutants**

Run `py tools/mutate_iron_court.py --selftest`. It stops at the first anchor that no longer matches exactly once.
- **Its code was deleted by this task** (the old `draw_govs` body): delete the mutant, ledger its name, and run the selftest again.
- **It was in `fit_cut`:** re-aim it at the matching `return` line of `ICUI.cut_text`. The mutation stays the same; the anchor gains the `return`.

Repeat until `selftest ok`. Then append:

```python
    # THE GOVERNORS VIEW, PHASE 0 (plan 2026-09-30 Task 2).
    ("the Governors view leaves the throne room over the map", UM,
     """    pcall(function() panel:SetImagePath(on and ICUI.MASK_NONE or ICUI.GM_BACKDROP, 0) end)""",
     """    pcall(function() panel:SetImagePath(ICUI.GM_BACKDROP, 0) end)"""),
    ("another tab leaves the map showing through the court", UM,
     """    pcall(function() panel:SetImagePath(on and ICUI.MASK_NONE or ICUI.GM_BACKDROP, 0) end)""",
     """    pcall(function() panel:SetImagePath(ICUI.MASK_NONE, 0) end)"""),
    ("the Governors view eats every click on the map", UM,
     """    panel:SetInteractive(not on)""",
     """    panel:SetInteractive(true)"""),
    ("another tab lets clicks through the court", UM,
     """    panel:SetInteractive(not on)""",
     """    panel:SetInteractive(false)"""),
    ("another tab leaves the pins up", UM,
     """    if not on then ICUI.gm_clear_pins(panel) return end""",
     """    if not on then return end"""),
    ("the Governors view drawn under a picker", UM,
     """    return (comp(ICUI.PANEL) and ICUI.view == "govs" and ICUI.pick == nil) and true or false""",
     """    return (comp(ICUI.PANEL) and ICUI.view == "govs") and true or false"""),
    ("a face made before its pin", UM,
     """                pins:CreateComponent(pin_name, ICUI.PATH_GM_PIN)
                pins:CreateComponent(face_name, ICUI.PATH_GM_FACE)""",
     """                pins:CreateComponent(face_name, ICUI.PATH_GM_FACE)
                pins:CreateComponent(pin_name, ICUI.PATH_GM_PIN)"""),
    ("a redraw remakes every pin", UM,
     """            if not (comp(pin_name, pins) and comp(face_name, pins)) then""",
     """            if true then"""),
    ("a lost province's pin left standing", UM,
     """        if seats[i] ~= province then drop_pair(pins, i) end""",
     """        if false then drop_pair(pins, i) end"""),
    ("a face pinned nowhere", UM,
     """                face:SetContextObject(at)""",
     """                face:SetContextObject(nil)"""),
    ("the pins' holder left at the box", UM,
     """    pins:MoveTo(0, 0)""",
     """    pins:MoveTo(ICUI.OX, ICUI.OY)"""),
    ("an empty seat's ring left to crash the draw", UM,
     """    if not slug or slug == "" then return ICUI.MASK_NONE end""",
     """    if slug == "" then return ICUI.MASK_NONE end"""),
    ("a crest drawn over a governor's face", UM,
     """                face:SetImagePath((not port and slug and ICUI.crest(slug)) or ICUI.MASK_NONE,""",
     """                face:SetImagePath((slug and ICUI.crest(slug)) or ICUI.MASK_NONE,"""),
    ("a pin's long name not cut", UM,
     """                set_text(pin, ICUI.cut_text(pin, loc("provinces_onscreen_" .. province, province))""",
     """                set_text(pin, (loc("provinces_onscreen_" .. province, province))"""),
    ("the Governors view shows the last tab's rows", UM,
     """    for i = 1, ICUI.MAX_ROWS do show(comp(ICUI.ROW .. "_" .. i, panel), false) end""",
     """    for i = 1, 0 do show(comp(ICUI.ROW .. "_" .. i, panel), false) end"""),
    ("a pin opens a picker for a province already lost", UM,
     """    if not held then ICUI.refresh() return end""",
     """    if false then ICUI.refresh() return end"""),
    ("a selection through the see-through court leaves it up", UM,
     """    if ICUI.gm_on() then ICUI.close() end""",
     """    if false then ICUI.close() end"""),
    ("a selection closes the court from any tab", UM,
     """    if ICUI.gm_on() then ICUI.close() end""",
     """    if comp(ICUI.PANEL) then ICUI.close() end"""),
```

`UM` is the runner's alias for the map Lua. Confirm it with `grep -n "^UM = " tools/mutate_iron_court.py`.

Run: `py tools/mutate_iron_court.py "throne room" "map showing" "eats every" "lets clicks" "pins up" "under a picker" "before its pin" "pinned nowhere" "at the box" "ring left" "crest drawn over" "not cut" "last tab's rows" "already lost" "leaves it up" "from any tab" "remakes every" "left standing"`
Expected: `18 mutants, 0 unexplained`. Then run `py tools/gen_ic_ui.py`.

- [ ] **Step 11: Gates.** Every gate, with its expected result:

| Gate | Expected |
|---|---|
| `py tools/gen_ic_ui.py --check` | no drift |
| `py tools/gen_ic_ui.py --selftest` | ok. Run it in the background with a 600s wait loop; it outlasts the tool timeout. |
| `py tools/preview_iron_court.py --check` | ok. If its reader refuses `maskimage`, ledger that and leave the validator for Task 7. |
| `luac -p` on the two Lua files | parses |
| `py tools/check_lua_api.py` on the two Lua files | 0 suspects |
| `py tools/check_lua_literal_left.py` | 0 sites |
| `py tools/check_lua_undeclared.py` | clean |
| `py tools/import_iron_court.py` | `verify ok`, with 2 more UI files than before |
| the harness | `ok (N checks)` |

- [ ] **Step 12: Build, deploy, and STOP**

1. Start RPFM's server headless if `http://127.0.0.1:45127/sessions` does not answer.
2. Run `py tools/deploy_iron_court.py`.
   Expected: it builds, verifies and prints the build name (the first 8 hex digits of its MD5). If `Warhammer3.exe` is not running, it deploys to data/.
3. Stop the server.
4. Ledger `Task 2: build <NAME> deployed; waiting on the author's look`.

Then STOP and ask the author to open the court on the Governors tab and answer:
1. Do the pins stay on their settlements as the camera moves, at the usual UI scale and at a smaller one?
2. Does the camera drag, edge-scroll, zoom and answer the keys through the court?
3. Does a click on a settlement through the court select it, and does the court then close?
4. Do the game's own map tooltips appear when hovering the bare map?
5. Is the governor's face round inside the pin's head, or square?
6. Does the pin's point read as standing on its settlement at a normal camera height?
7. Does the pin's text show two lines (the province, then "Loyalty N%")?

What each "no" needs, before Task 3 starts:
- **Question 5:** replace the face's mask with the fallback (plan ruling 2):
  - drop `mask=` and the mask layer from `_gm_face`, so the file has three layers;
  - add a fourth pin layer, a 42px opaque ring bezel over the head's corners, drawn after the face by giving it its own pin-sized component created after the face;
  - or simply shrink `GM_PORT_BOX` to the head.
  Ledger the choice.
- **Question 7:** change the pin's text to one line, `"<name> - N%"`, and the check's expected string with it.
- **Question 6:** add `("offset_y", "<value>")` to the pin's and the face's `MAP_PIN` props copy (never to `MAP_PIN` itself, which the old marker shares). Use the value the author judges, starting at CA's 20.
- **Questions 1-3:** the fallback in spec section 5: the Governors tab opens the map layer we have, carrying the same column. This re-plans Tasks 3-6: stop and ask.

Ledger each answer as `Task 2: Phase 0 answer <n>: <answer>`. Task 2 is complete when the author has answered and any fallback is built and green: ledger `Task 2: complete (tests: harness -> ok (N checks))`.

---

### Task 3: The column - plates, row pool, toggles, and the Parties page

**Files:**
- Modify: `tools/gen_ic_ui.py`
  - `GUID_PREFIXES`, `COMPACT_FILES`, the `PANEL_LAYOUT` literal
  - the new `GM_ROW_*` block after `ROW_LAYOUT` (~line 652, BEFORE the scale pass at ~line 3935)
  - `_panel_order`, `_panel`, a new `_gm_row()` after `_row()` (~line 3344)
  - `FILES`, `LAYOUT_TABLES`, `SCALED_SCALARS`, `SCALED_BOX_TABLES`, `NOT_GEOMETRY`
  - the portrait aspect list (~line 4978)
  - `check()`, and the selftest
- Modify: `tools/import_iron_court.py` (the layout cross-check loop, ~line 1283)
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua`
  - `PANEL_XY`
  - a `GM_ROW_*` block beside `ICUI.MAX_ROWS` (~line 127)
  - `ICUI.SCALED`, `ICUI.SCALED_TABLES`, `ICUI.NOT_SCALED`, `ICUI.HAS_COMPACT`
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui_map.lua` (the Governors section and the click listener)
- Modify: `tools/_iron_court_harness.lua`, `tools/mutate_iron_court.py`
- Generated: `derpy_ic_gm_row.twui.xml` and `derpy_ic_gm_row_compact.twui.xml`

**Interfaces:**
- Consumes (Task 2): `ICUI.gm_on`, `ICUI.gm_sync`, `ICUI.gm_keys`, `ICUI.GM_PINS`, `ICUI.GM_PIN`, `ICUI.GP_OUTLINE`, `with_fake_govmap`, `gm_pin`.
- Produces (panel Lua):
  - `ICUI.GM_ROW = "ic_gm_row"`, `ICUI.PATH_GM_ROW`, `ICUI.GM_ROWS = 7`;
  - `ICUI.GM_ROW_X/Y/W/H/PITCH`, `ICUI.GM_ROW_CHILD_XY`, keyed `ic_gr_face`, `ic_gr_crest`, `ic_gr_badge`, `ic_gr_l1`, `ic_gr_l2`, `ic_gr_icon`, `ic_gr_l3`;
  - `PANEL_XY.ic_gm_top/foot/col/head/tog_1/tog_2/tog_lbl_1/tog_lbl_2/hint/prev/page/next`.
- Produces (map Lua):
  - `ICUI.GM_KEYS`, `ICUI.GM_PLATES`, `ICUI.GM_TOGS = {ic_gm_tog_1 = "parties", ic_gm_tog_2 = "provinces"}`, `ICUI.GM_TOG_ART = {0, 2}`;
  - `ICUI.gm_page`, which defaults to `"provinces"`;
  - `ICUI.gm_scroll[page]`, a 0-based page number;
  - `ICUI.gm_party`, a row of the whole Parties list or nil;
  - `ICUI.gm_rows[i]`, the row table drawn in slot i;
  - `ICUI.gm_reset()`;
  - `ICUI.gm_fill_row(row, r)`, where r = `{look, l1, l2, l3, face, vacant, plate, crest, badge, fealty, tip}` and look is `"live"`, `"selected"` or `"inactive"`;
  - `ICUI.gm_draw_page(panel, rows, chosen_fn)`;
  - `ICUI.gm_draw_column(panel, faction)`;
  - `ICUI.gm_ring(panel, faction)`;
  - `ICUI.gm_to_page(page)`, `ICUI.gm_row_click(n)`, `ICUI.gm_step(delta)`;
  - `ICUI.close`, wrapped so that it forgets the view.
- Produces (generator): `GM_ROW_FILE`, `GM_ROW_LAYOUT`, `GM_PLATES`, `check_gm_plates(layout=None)`.

- [ ] **Step 1: Snapshot** every file this task edits to the scratchpad as `*_before_govmap_t3.*`.

- [ ] **Step 2: Extend the fixture and write the failing checks**

In `with_fake_govmap`, just before `ICUI.register()`, add:

```lua
        -- A COLUMN ROW IS MADE WITH ITS CHILDREN, as the row's .twui.xml
        -- declares them, each its file's size so ICUI.fit_cut has a width.
        local panel_make = panel.CreateComponent
        function panel:CreateComponent(n, p)
            panel_make(self, n, p)
            local row = self.children[n]
            if row and p == ICUI.path(ICUI.PATH_GM_ROW) and next(row.children) == nil then
                for k, box in pairs(ICUI.GM_ROW_CHILD_XY) do
                    row:CreateComponent(k)
                    row.children[k].w, row.children[k].h = box[3], box[4]
                end
            end
        end
```

Add the helper under `gm_face`:

```lua
-- THE i-th ROW OF THE COLUMN, or nil.
local function gm_row(panel, i) return panel.children[ICUI.GM_ROW .. "_" .. i] end
```

Add these checks above `check("no parties' turn failed anywhere in the run"`:

```lua
check("the column shows on the Governors view only, the footer's plate with the footer", function()
    IC.state = {}
    make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a"})
    IC.add_house(F, IC.CROWN)
    with_fake_govmap(function(hud, panel, extra, holder)
        ICUI.view = "govs"
        ICUI.pick = nil
        ICUI.open()
        for _, name in ipairs(ICUI.GM_KEYS) do
            assert(panel.children[name].visible, name .. " is hidden on the Governors view")
        end
        assert(gm_row(panel, 1), "no column rows were made")
        -- THE FOOTER'S PLATE ONLY WITH SOMETHING ON IT.
        assert(panel.children.ic_gm_foot.visible == panel.children.ic_alert.visible,
            "the footer's plate shows without the footer, or the footer without its plate")
        ICUI.notice = "Something to say."
        ICUI.refresh()
        assert(panel.children.ic_alert.visible and panel.children.ic_gm_foot.visible,
            "the footer line has no plate under it over the map")
        ICUI.notice = nil
        map_click("ic_tab_court")
        for _, name in ipairs(ICUI.GM_KEYS) do
            assert(not panel.children[name].visible, name .. " shows on the Court tab")
        end
        assert(not panel.children.ic_gm_foot.visible, "the footer's plate shows on the Court tab")
        for i = 1, ICUI.GM_ROWS do
            assert(not gm_row(panel, i).visible, "column row " .. i .. " shows on the Court tab")
        end
    end)
end)

check("the column's toggles light their page and switch it", function()
    IC.state = {}
    make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a"})
    IC.add_house(F, IC.CROWN)
    with_fake_govmap(function(hud, panel, extra, holder)
        ICUI.view = "govs"
        ICUI.pick = nil
        ICUI.gm_page = "provinces"
        ICUI.open()
        local t1, t2 = panel.children.ic_gm_tog_1, panel.children.ic_gm_tog_2
        assert(t2.images[ICUI.GM_TOG_ART[1]] == ICUI.GM_ROUND_ART.selected[1], "Provinces is not lit on its own page")
        assert(t1.images[ICUI.GM_TOG_ART[1]] == ICUI.GM_ROUND_ART.live[1], "Parties is lit off its page")
        assert(panel.children.ic_gm_head.text == "Provinces", "the column heads " .. panel.children.ic_gm_head.text)
        map_click("ic_gm_tog_1")
        assert(ICUI.gm_page == "parties", "the Parties toggle went to " .. tostring(ICUI.gm_page))
        assert(t1.images[ICUI.GM_TOG_ART[1]] == ICUI.GM_ROUND_ART.selected[1]
               and t1.images[ICUI.GM_TOG_ART[2]] == ICUI.GM_ROUND_ART.selected[2],
            "Parties is not lit in both states on its own page")
        assert(t2.images[ICUI.GM_TOG_ART[1]] == ICUI.GM_ROUND_ART.live[1], "Provinces stayed lit")
        assert(panel.children.ic_gm_head.text == "Parties", "the column heads " .. panel.children.ic_gm_head.text)
    end)
end)

check("the Parties page lists every party with what it governs and would take", function()
    IC.state = {}
    turn = 1
    local g1, g2 = make_character(811, ANY_SEAT, "legion"), make_character(812, ANY_SEAT, "legion")
    make_faction(F, IC.CHD_SUBCULTURE, {g1, g2}, {"prov_a", "prov_b", "prov_c"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    IC.court(F).govs["prov_b"] = 811
    IC.court(F).govs["prov_c"] = 812
    with_fake_govmap(function(hud, panel, extra, holder)
        ICUI.view = "govs"
        ICUI.pick = nil
        ICUI.open()
        map_click("ic_gm_tog_1")
        local legion = gm_row(panel, 2)
        assert(legion.visible, "the legion's row is hidden")
        assert(legion.children.ic_gr_l1.text == ICUI.house_name("legion", F), legion.children.ic_gr_l1.text)
        assert(legion.children.ic_gr_l2.text == "Governs 2", legion.children.ic_gr_l2.text)
        local take = #IC.defecting_provinces(F, "legion")
        assert(legion.children.ic_gr_l3.text == string.format("Would take %d", take),
            "the take count reads " .. legion.children.ic_gr_l3.text)
        assert(legion.children.ic_gr_crest.visible and legion.children.ic_gr_crest.images[0] == ICUI.crest("legion"),
            "the legion's row wears no crest")
        assert(not legion.children.ic_gr_face.visible, "a party row draws a portrait")
        local none = gm_row(panel, 3)
        assert(none.children.ic_gr_l1.text == "No governor", none.children.ic_gr_l1.text)
        assert(none.children.ic_gr_l2.text == "1 province", none.children.ic_gr_l2.text)
        assert(not gm_row(panel, 4).visible, "a spare row is drawn")
        assert(not panel.children.ic_gm_next.visible, "a pager for one page")
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
    with_fake_govmap(function(hud, panel, extra, holder)
        ICUI.view = "govs"
        ICUI.pick = nil
        ICUI.open()
        map_click("ic_gm_tog_1")
        map_click(ICUI.GM_ROW .. "_2")
        local want = {}
        for _, p in ipairs(IC.defecting_provinces(F, "legion")) do want[p] = true end
        assert(next(want), "the fixture's legion would take nothing, so this proves nothing")
        for i, p in pairs(ICUI.gm_keys) do
            local ring = gm_pin(holder, i).images[ICUI.GP_OUTLINE]
            assert((ring == ICUI.MK_RING_OUTLINE) == (want[p] == true), p .. " is ringed " .. tostring(ring))
        end
        assert(gm_row(panel, 2).images[0] == ICUI.GM_ROW_ART.selected[1]
               and gm_row(panel, 2).images[1] == ICUI.GM_ROW_ART.selected[2],
            "the chosen row does not look chosen in both states")
        assert(gm_row(panel, 1).images[0] == ICUI.GM_ROW_ART.live[1], "another row looks chosen")
        map_click(ICUI.GM_ROW .. "_2")
        for i in pairs(ICUI.gm_keys) do
            assert(gm_pin(holder, i).images[ICUI.GP_OUTLINE] == ICUI.MASK_NONE, "a second click left a ring")
        end
        assert(gm_row(panel, 2).images[0] == ICUI.GM_ROW_ART.live[1], "a second click left the row chosen")
    end)
end)

check("a party that rings nothing says why, in the hint and on its tooltip", function()
    IC.state = {}
    make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    with_fake_govmap(function(hud, panel, extra, holder)
        ICUI.view = "govs"
        ICUI.pick = nil
        ICUI.open()
        map_click("ic_gm_tog_1")
        assert(panel.children.ic_gm_hint.text == "Click a party to see what it would take.",
            "the hint reads " .. panel.children.ic_gm_hint.text)
        map_click(ICUI.GM_ROW .. "_1")          -- the Crown
        assert(panel.children.ic_gm_hint.text == "Your own house does not secede.",
            "the Crown's hint reads " .. panel.children.ic_gm_hint.text)
        local keep = IC.TUNE.secession
        IC.TUNE.secession = false
        map_click(ICUI.GM_ROW .. "_2")          -- the legion, secession off
        IC.TUNE.secession = keep
        assert(panel.children.ic_gm_hint.text:find("switched off", 1, true),
            "the legion's hint reads " .. panel.children.ic_gm_hint.text)
        assert(gm_row(panel, 2).tooltip:find("switched off", 1, true),
            "the legion's tooltip does not say why: " .. tostring(gm_row(panel, 2).tooltip))
        assert(gm_row(panel, 2).children.ic_gr_l3.visible == false, "a row that takes nothing still counts")
    end)
end)

check("a realm with no province says so on the Parties page", function()
    IC.state = {}
    make_faction(F, IC.CHD_SUBCULTURE, {}, {})
    IC.add_house(F, IC.CROWN)
    with_fake_govmap(function(hud, panel, extra, holder)
        ICUI.view = "govs"
        ICUI.pick = nil
        ICUI.open()
        map_click("ic_gm_tog_1")
        assert(next(ICUI.gm_keys) == nil, "a pin for no province")
        assert(panel.children.ic_gm_hint.text == "You hold no province.", panel.children.ic_gm_hint.text)
    end)
end)

check("a court with more parties than rows pages its Parties page", function()
    IC.state = {}
    turn = 1
    make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a", "prov_b"})
    for _, slug in ipairs(IC.PARTIES) do IC.add_house(F, slug) end
    with_fake_govmap(function(hud, panel, extra, holder)
        ICUI.view = "govs"
        ICUI.pick = nil
        ICUI.open()
        map_click("ic_gm_tog_1")
        local rows = ICUI.map_rows(F)
        assert(#rows > ICUI.GM_ROWS, "the fixture fits one page, so this proves nothing")
        local pages = math.ceil(#rows / ICUI.GM_ROWS)
        assert(panel.children.ic_gm_next.visible, "no pager for " .. #rows .. " rows")
        assert(panel.children.ic_gm_page.text == "Page 1 of " .. pages, panel.children.ic_gm_page.text)
        for _ = 2, pages do map_click("ic_gm_next") end
        assert(panel.children.ic_gm_page.text == "Page " .. pages .. " of " .. pages, panel.children.ic_gm_page.text)
        map_click("ic_gm_next")                  -- past the end: stays
        assert(panel.children.ic_gm_page.text == "Page " .. pages .. " of " .. pages, "Next ran past the last page")
        -- "NO GOVERNOR" IS STILL THE LAST ROW, on the last page.
        local last = gm_row(panel, #rows - (pages - 1) * ICUI.GM_ROWS)
        assert(last.children.ic_gr_l1.text == "No governor", "the last row reads " .. last.children.ic_gr_l1.text)
        -- A CHOICE ON THE LAST PAGE is a row of the whole list.
        map_click(ICUI.GM_ROW .. "_1")
        assert(ICUI.gm_party == (pages - 1) * ICUI.GM_ROWS + 1, "the last page's first row chose " .. tostring(ICUI.gm_party))
        map_click("ic_gm_prev")
        assert(gm_row(panel, 1).images[0] == ICUI.GM_ROW_ART.live[1], "page one's first row wears the other page's choice")
    end)
end)

check("the Governors view reopens with nothing chosen", function()
    IC.state = {}
    local g1 = make_character(831, ANY_SEAT, "legion")
    make_faction(F, IC.CHD_SUBCULTURE, {g1}, {"prov_a", "prov_b"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    IC.court(F).govs["prov_a"] = 831
    with_fake_govmap(function(hud, panel, extra, holder)
        ICUI.view = "govs"
        ICUI.pick = nil
        ICUI.open()
        map_click("ic_gm_tog_1")
        map_click(ICUI.GM_ROW .. "_2")
        assert(ICUI.gm_party == 2, "the fixture chose nothing")
        -- ANOTHER TAB AND BACK.
        map_click("ic_tab_court")
        map_click("ic_tab_govs")
        assert(ICUI.gm_party == nil, "a tab and back kept the choice")
        map_click(ICUI.GM_ROW .. "_2")
        -- CLOSED AND REOPENED.
        ICUI.close()
        ICUI.view = "govs"
        ICUI.gm_sync()
        assert(ICUI.gm_party == nil, "a reopen kept the choice")
    end)
end)

check("in the Governors view every visible text cell sits on a plate", function()
    IC.state = {}
    local g1 = make_character(841, ANY_SEAT, "legion")
    make_faction(F, IC.CHD_SUBCULTURE, {g1}, {"prov_a", "prov_b"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    IC.court(F).govs["prov_a"] = 841
    for _, screen in ipairs({{1920, 1080}, {1600, 900}}) do
        with_fake_govmap(function(hud, panel, extra, holder)
            ICUI.view = "govs"
            ICUI.pick = nil
            ICUI.notice = "Something to say."
            ICUI.open()
            local plates = {}
            for _, name in ipairs(ICUI.GM_PLATES) do
                local p = panel.children[name]
                if p.visible then plates[#plates + 1] = p end
            end
            local function on_plate(c)
                for _, p in ipairs(plates) do
                    if c.x >= p.x and c.y >= p.y and c.x + c.w <= p.x + p.w and c.y + c.h <= p.y + p.h then
                        return true
                    end
                end
                return false
            end
            local function walk(parent, where)
                for _, c in ipairs(parent.order) do
                    if c.visible and c ~= holder then
                        if c.text ~= "" then
                            assert(on_plate(c), screen[1] .. "x" .. screen[2] .. ": " .. where .. c.name
                                .. " at " .. c.x .. "," .. c.y .. " " .. c.w .. "x" .. c.h
                                .. " reads '" .. c.text .. "' over the bare map")
                        end
                        walk(c, where .. c.name .. " > ")
                    end
                end
            end
            walk(panel, "")
            ICUI.notice = nil
        end, screen)
    end
    ICUI.apply_scale(1920)
end)
```

- [ ] **Step 3: Run the harness and verify that it fails**

Run: `IC_TEST_ALL=1 "/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | grep "^FAIL"`
Expected: the 9 new checks fail. The first fails on a nil `ICUI.GM_KEYS` or a missing `ic_gm_*` child.

- [ ] **Step 4: The column in the generator**

Add to `GUID_PREFIXES`:

```python
    # IC49-IC50 - THE GOVERNORS VIEW'S COLUMN ROW and its compact copy.
    "derpy_ic_gm_row.twui.xml":         "IC49",
    "derpy_ic_gm_row_compact.twui.xml": "IC50",
```

Add `"derpy_ic_gm_row.twui.xml"` to the tuple in `COMPACT_FILES`.

In the `PANEL_LAYOUT` literal, after `"ic_gm_pins"`, add:

```python
    # THE GOVERNORS VIEW'S PLATES AND COLUMN (spec 2026-09-30 section 6). Text
    # on a live map has no reliable contrast, so every line this view keeps sits
    # on one of the three plates (check_gm_plates). The column is CA's
    # Hell-Forge side panel at its own 503: opaque 0-443, then its fade.
    "ic_gm_top": (0, 0, 1920, 124),
    "ic_gm_foot": (0, 1014, 1920, 66),
    "ic_gm_col": (0, 124, 503, 890),
    "ic_gm_head": (10, 128, 425, 60),
    "ic_gm_tog_1": (76, 194, 56, 56),
    "ic_gm_tog_2": (312, 194, 56, 56),
    "ic_gm_tog_lbl_1": (44, 252, 120, 26),
    "ic_gm_tog_lbl_2": (280, 252, 120, 26),
    "ic_gm_hint": (16, 286, 412, 26),
    # THE COURT'S PAGER, same sizes, under the seventh row (318 + 7 * 80 = 878).
    "ic_gm_prev": (16, 880, 136, 34),
    "ic_gm_page": (156, 884, 132, 26),
    "ic_gm_next": (292, 880, 136, 34),
```

After `ROW_LAYOUT`'s closing brace (~line 670, which is before the scale pass), add:

```python
# THE GOVERNORS VIEW'S COLUMN ROW (spec 2026-09-30 section 6): ONE pool for the
# column's three pages, as the Intrigue views share one. The body is CA's
# Hell-Forge unit block, which stretches between 16px caps. Must match
# ICUI.GM_ROW_* and ICUI.GM_ROW_CHILD_XY in the panel Lua (import_iron_court).
GM_ROW_FILE = "derpy_ic_gm_row.twui.xml"
GM_ROW_X, GM_ROW_Y, GM_ROW_W, GM_ROW_H, GM_ROW_PITCH = 16, 318, 412, 76, 80
GM_ROWS = 7
GM_ROW_LAYOUT = {
    "ic_gr_face": (10, 9, 104, 57),     # a porthole, PORT_BOX's own shape
    "ic_gr_crest": (10, 20, 36, 36),    # a party's crest, square
    "ic_gr_badge": (90, 46, 24, 24),    # his party's crest on the face's corner
    "ic_gr_l1": (124, 6, 280, 24),
    "ic_gr_l2": (124, 30, 280, 20),
    "ic_gr_icon": (124, 52, 20, 20),    # CA's loyalty icon
    "ic_gr_l3": (148, 52, 256, 20),
}
GM_HF = "ui/skins/default/dlc23_chd_hell_forge/"
GM_ROW_ART = GM_HF + "button_square_extra_large_%s.png"
GM_COL_ART = GM_HF + "side_panerl_bg.png"          # CA's spelling
GM_HEAD_ART = GM_HF + "side_panel_title.png"
GM_TOG_LABEL_ART = "ui/skins/default/dlc23_tower_of_zharr/tab_sub_title.png"
GM_ROUND = "ui/skins/default/button_round_medium_%s.png"
GM_TOG_ICONS = {
    "ic_gm_tog_1": "ui/skins/default/dlc23_tower_of_zharr/icon_button_seat_effects.png",
    "ic_gm_tog_2": "ui/skins/default/icon_provinces.png",
}
GM_PLATES = ["ic_gm_top", "ic_gm_foot", "ic_gm_col"]
```

Add `"GM_ROW_X", "GM_ROW_Y", "GM_ROW_W", "GM_ROW_H", "GM_ROW_PITCH"` to `SCALED_SCALARS` and `"GM_ROW_LAYOUT"` to `SCALED_BOX_TABLES`. Add these to `NOT_GEOMETRY`:

```python
"GM_ROW_FILE", "GM_ROWS", "GM_HF", "GM_ROW_ART", "GM_COL_ART", "GM_HEAD_ART",
"GM_TOG_LABEL_ART", "GM_ROUND", "GM_TOG_ICONS", "GM_PLATES"
```

Add `"ic_gr_l1": (16, "body_16"), "ic_gr_l2": (12, "body_12"), "ic_gr_l3": (12, "body_12"),` to `TEXT_STYLE`.

In `_panel_order`, after the `ic_gm_pins` return, add:

```python
    if name in ("ic_gm_top", "ic_gm_foot", "ic_gm_col"):
        # UNDER EVERYTHING THEY HOLD, and not tier -1: see ic_gm_pins.
        return (-2, name)
```

In `_panel()`, after the `ic_gm_pins` branch, add:

```python
        if name in ("ic_gm_top", "ic_gm_foot", "ic_gm_col"):
            # OPAQUE, AND IT TAKES THE CLICK: over the live map a click on its
            # blank must not fall through and select what stands under it.
            art, margin = ((GM_COL_ART, 0) if name == "ic_gm_col" else (GM_PLATE, (0, 12)))
            panel.add(EU.C(name, w, h, interactive=True, sound=OPENER_SOUND,
                           layers=[_gm_full(art, margin)]))
            continue
        if name == "ic_gm_head":
            panel.add(EU.C(name, w, h, layers=[_gm_full(GM_HEAD_ART, (0, 80))],
                           **dict(TAB_TEXT, size=TITLE[0], fontcat=TITLE[1])))
            continue
        if name in GM_TOG_ICONS:
            # CA'S ROUND TOGGLE, lit by swapping its art into layers 0 and 2
            # (ICUI.GM_TOG_ART), as the court's tabs are lit.
            panel.add(EU.C(name, w, h, interactive=True, sound=OPENER_SOUND,
                           layers=[_gm_full(GM_ROUND % "active"), _gm_inset(GM_TOG_ICONS[name], 12)],
                           hover=[_gm_full(GM_ROUND % "hover"), _gm_inset(GM_TOG_ICONS[name], 12)]))
            continue
        if name.startswith("ic_gm_tog_lbl_"):
            panel.add(EU.C(name, w, h, layers=[_gm_full(GM_TOG_LABEL_ART, (0, 12))], **TAB_TEXT))
            continue
        if name == "ic_gm_hint":
            panel.add(EU.C(name, w, h, **style(name, valign="Center")))
            continue
        if name in ("ic_gm_prev", "ic_gm_next"):
            panel.add(EU.C(name, w, h, interactive=True, sound=OPENER_SOUND,
                           layers=PAGE_LAYERS, hover=PAGE_HOVER, **TAB_TEXT))
            continue
        if name == "ic_gm_page":
            panel.add(EU.C(name, w, h, **style(name, align="Center", valign="Center",
                                                tx="0.00,0.00")))
            continue
```

After `_row()`, add:

```python
def _gm_full(path, margin=0):
    """One layer filling its component."""
    return {"path": path, "offset": (0, 0), "dw": 0, "dh": 0, "margin": margin, "dock": None}


def _gm_inset(path, px):
    """One layer `px` in from every edge."""
    return {"path": path, "offset": (px, px), "dw": -2 * px, "dh": -2 * px,
            "margin": 0, "dock": None}


def _gm_row():
    root = EU.C("root", GM_ROW_W, GM_ROW_H)
    # THE ROW TAKES THE CLICK AND THE TOOLTIP; its cells take neither, so a
    # click anywhere on it reports the row. Its look is CA's art in layers 0
    # (standard) and 1 (hover), swapped by ICUI.gm_fill_row (plan ruling 6).
    row = root.add(EU.C("derpy_ic_gm_row", GM_ROW_W, GM_ROW_H, interactive=True,
                        sound=OPENER_SOUND,
                        layers=[_gm_full(GM_ROW_ART % "active", (0, 16))],
                        hover=[_gm_full(GM_ROW_ART % "hover", (0, 16))]))
    for name in sorted(GM_ROW_LAYOUT):
        _x, _y, w, h = GM_ROW_LAYOUT[name]
        if name == "ic_gr_face":
            # THE COURT'S OWN FACE STACK (plan ruling 14): plate, face, mask, frame.
            row.add(EU.C(name, w, h, layers=FACE_LAYERS, colour_from=FACE_COLOUR_FROM))
        elif name in ("ic_gr_crest", "ic_gr_badge", "ic_gr_icon"):
            row.add(EU.C(name, w, h, layers=PORT_LAYERS))
        else:
            row.add(EU.C(name, w, h, **style(name, valign="Center")))
    return root
```

Add `(GM_ROW_FILE, _gm_row, "The Iron Court - one row of the Governors view's column"),` to `FILES`. Add `LAYOUT_TABLES[GM_ROW_FILE] = dict(GM_ROW_LAYOUT, derpy_ic_gm_row=(0, 0, GM_ROW_W, GM_ROW_H))` right after the `LAYOUT_TABLES` literal. In the portrait aspect list (~line 4978), add `("ic_gr_face", GM_ROW_LAYOUT["ic_gr_face"][2:], PORTHOLE_ASPECT, "porthole"),`.

After `check_gm`, add:

```python
def check_gm_plates(layout=None, panel_text=None):
    """Every text cell the Governors view shows lies inside one of its plates.

    Shown: every ic_gm_ cell, the footer line, and every cell of the top strip,
    which is whatever ends above ic_gm_top's bottom edge - derived, so a cell
    added to the strip later is held here without an edit. The rows are held
    by their pool: the pool must lie inside the column.
    """
    lay = layout or PANEL_LAYOUT
    text = panel_text if panel_text is not None else EU.layout(
        EU.assign(_panel(), GUID_PREFIXES["derpy_ic_panel.twui.xml"]), "")
    has_text = set(n for n, b in _component_blocks(text).items() if "<component_text" in b)
    plates = [lay[n] for n in GM_PLATES]

    def inside(b, p):
        return (b[0] >= p[0] and b[1] >= p[1] and b[0] + b[2] <= p[0] + p[2]
                and b[1] + b[3] <= p[1] + p[3])
    top = lay["ic_gm_top"]
    out = []
    for name, box in sorted(lay.items()):
        shown = (name.startswith("ic_gm_") or name == "ic_alert"
                 or box[1] + box[3] <= top[1] + top[3])
        if shown and name in has_text and not any(inside(box, p) for p in plates):
            out.append("%s %r reads over the bare map in the Governors view: no plate "
                       "of %s contains it" % (name, box, ", ".join(GM_PLATES)))
    col = lay["ic_gm_col"]
    pool = (GM_ROW_X, GM_ROW_Y, GM_ROW_W, GM_ROW_PITCH * (GM_ROWS - 1) + GM_ROW_H)
    if not inside(pool, col):
        out.append("the column's %d rows %r run outside the column %r" % (GM_ROWS, pool, col))
    if GM_ROW_Y + GM_ROW_PITCH * (GM_ROWS - 1) + GM_ROW_H > lay["ic_gm_prev"][1]:
        out.append("the column's last row runs under its pager")
    return out
```

In `check()`, after the `check_masks` line, add `out.extend(check_gm_plates())`. In the selftest, add:

```python
    assert not check_gm_plates(), check_gm_plates()
    _moved = dict(PANEL_LAYOUT, ic_gm_hint=(16, 1040, 412, 26))
    assert any("ic_gm_hint" in e for e in check_gm_plates(_moved)), \
        "a column line off every plate went unreported"
```

`_moved` puts the hint at y 1040, x 16: inside the footer's x range, but past the column's bottom and between the column and the footer. If that still lands inside `ic_gm_foot` (y 1014-1080), use `(700, 600, 412, 26)` instead, which is the bare map. Confirm the negative fires.

- [ ] **Step 5: The importer's two cross-checks.** In `tools/import_iron_court.py`:
- add `("GM_ROW_CHILD_XY", U3.GM_ROW_LAYOUT),` to the `for lua_name, gen_table in (...)` tuple (~line 1283);
- add `"GM_ROW_CHILD_XY": g.GM_ROW_LAYOUT,` to the `gen_tables` dict in `check_scaled` (~line 441).

Without the second, `check_scaled` refuses: "ICUI.GM_ROW_CHILD_XY is scaled and nothing in the generator answers for it". The five `GM_ROW_*` scalars match by name and need no entry.

- [ ] **Step 6: The panel Lua's tables**

Beside `ICUI.MAX_ROWS = 12`, add:

```lua
-- THE GOVERNORS VIEW'S COLUMN ROW (spec 2026-09-30): one pool for the column's
-- three pages. Declared HERE, not in the map file, so the scale pass - which
-- copies its tables when this file loads - scales them. Must match GM_ROW_*
-- in tools/gen_ic_ui.py (import_iron_court compares GM_ROW_CHILD_XY).
ICUI.GM_ROW = "ic_gm_row"
ICUI.PATH_GM_ROW = "ui/campaign ui/derpy_ic_gm_row"
ICUI.GM_ROWS = 7
ICUI.GM_ROW_X, ICUI.GM_ROW_Y, ICUI.GM_ROW_W, ICUI.GM_ROW_H, ICUI.GM_ROW_PITCH = 16, 318, 412, 76, 80
ICUI.GM_ROW_CHILD_XY = {
    ic_gr_face  = {10, 9, 104, 57},
    ic_gr_crest = {10, 20, 36, 36},
    ic_gr_badge = {90, 46, 24, 24},
    ic_gr_l1    = {124, 6, 280, 24},
    ic_gr_l2    = {124, 30, 280, 20},
    ic_gr_icon  = {124, 52, 20, 20},
    ic_gr_l3    = {148, 52, 256, 20},
}
```

In `ICUI.PANEL_XY`, after `ic_gm_pins`, add the same twelve `ic_gm_*` boxes as the generator's step 4 literal, as `name = {x, y, w, h},` lines.

Then:
- add `"GM_ROW_X", "GM_ROW_Y", "GM_ROW_W", "GM_ROW_H", "GM_ROW_PITCH"` to `ICUI.SCALED`;
- add `"GM_ROW_CHILD_XY"` to `ICUI.SCALED_TABLES`;
- add `"GM_ROWS"` to `ICUI.NOT_SCALED`;
- add `[ICUI.PATH_GM_ROW] = true` to `ICUI.HAS_COMPACT`.

- [ ] **Step 7: The column in the map Lua**

After `ICUI.gm_pin_click`, add:

```lua
-- ---------------------------------------------------------------------------
-- THE COLUMN (spec 2026-09-30 sections 1 and 6): CA's Hell-Forge side panel on
-- the left, over the map. Its components are the panel's own, declared in
-- derpy_ic_panel.twui.xml and placed by ICUI.layout; its rows are one pool made
-- here, for all three pages.
ICUI.GM_PLATES = {"ic_gm_top", "ic_gm_foot", "ic_gm_col"}
-- SHOWN WITH THE VIEW. ic_gm_foot is not here: it shows with the footer line.
ICUI.GM_KEYS = {"ic_gm_top", "ic_gm_col", "ic_gm_head", "ic_gm_tog_1", "ic_gm_tog_2",
                "ic_gm_tog_lbl_1", "ic_gm_tog_lbl_2", "ic_gm_hint",
                "ic_gm_prev", "ic_gm_page", "ic_gm_next"}
ICUI.GM_TOGS = {ic_gm_tog_1 = "parties", ic_gm_tog_2 = "provinces"}
ICUI.GM_PAGE_TITLE = {parties = "Parties", provinces = "Provinces"}
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
ICUI.gm_page = "provinces"           -- plan ruling 15
ICUI.gm_scroll = {parties = 0, provinces = 0, picker = 0}
ICUI.gm_party = nil                  -- the chosen Parties row, of the whole list
ICUI.gm_rows = {}                    -- slot -> the row table drawn there
ICUI.gm_was_on = false

-- NOTHING CHOSEN: a view entered afresh starts clean.
function ICUI.gm_reset()
    ICUI.gm_party = nil
    ICUI.gm_scroll = {parties = 0, provinces = 0, picker = 0}
end

-- THE COURT CLOSED FORGETS THE VIEW, so a reopen on Governors is afresh.
local court_close = ICUI.close
function ICUI.close(...)
    ICUI.gm_was_on = false
    return court_close(...)
end

function ICUI.gm_show_column(panel, on)
    for _, name in ipairs(ICUI.GM_KEYS) do show(comp(name, panel), on) end
    for i = 1, ICUI.GM_ROWS do show(comp(ICUI.GM_ROW .. "_" .. i, panel), on) end
    if not on then show(comp("ic_gm_foot", panel), false) end
end

-- THE ROW POOL, made the first time and placed every time, from the box's
-- origin, as ICUI.layout places the court's.
function ICUI.gm_make_rows(panel)
    local px, py = panel:Position()
    px, py = px + ICUI.OX, py + ICUI.OY
    for i = 1, ICUI.GM_ROWS do
        local name = ICUI.GM_ROW .. "_" .. i
        if not comp(name, panel) then
            panel:CreateComponent(name, ICUI.path(ICUI.PATH_GM_ROW))
        end
        local row = comp(name, panel)
        if row then
            local x = px + ICUI.GM_ROW_X
            local y = py + ICUI.GM_ROW_Y + (i - 1) * ICUI.GM_ROW_PITCH
            row:MoveTo(x, y)
            ICUI.resize(row, ICUI.GM_ROW_W, ICUI.GM_ROW_H)
            for cname, b in pairs(ICUI.GM_ROW_CHILD_XY) do
                local c = comp(cname, row)
                if c then
                    c:MoveTo(x + b[1], y + b[2])
                    ICUI.resize(c, b[3], b[4])
                end
            end
        end
    end
end

-- ONE ROW FROM `r`. A field left nil hides its cell, so a page never shows the
-- last page's leftovers.
function ICUI.gm_fill_row(row, r)
    local art = ICUI.GM_ROW_ART[r.look or "live"] or ICUI.GM_ROW_ART.live
    pcall(function()
        row:SetImagePath(art[1], 0)
        row:SetImagePath(art[2], 1)
    end)
    for _, key in ipairs({"l1", "l2", "l3"}) do
        local c = comp("ic_gr_" .. key, row)
        if c then
            ICUI.fit_cut(c, r[key] or "")
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

-- ONE PAGE OF `rows` INTO THE POOL, with the pager. `chosen(r, n)` says whether
-- row n of the whole list is the chosen one.
function ICUI.gm_draw_page(panel, rows, chosen)
    local page = ICUI.gm_page
    local pages = math.max(1, math.ceil(#rows / ICUI.GM_ROWS))
    ICUI.gm_scroll[page] = math.max(0, math.min(ICUI.gm_scroll[page] or 0, pages - 1))
    local at = ICUI.gm_scroll[page] * ICUI.GM_ROWS
    ICUI.gm_rows = {}
    for i = 1, ICUI.GM_ROWS do
        local row = comp(ICUI.GM_ROW .. "_" .. i, panel)
        local r = rows[at + i]
        if row then
            show(row, r ~= nil)
            if r then
                if (r.look or "live") == "live" and chosen(r, at + i) then r.look = "selected" end
                ICUI.gm_fill_row(row, r)
                ICUI.gm_rows[i] = r
            end
        end
    end
    for _, name in ipairs({"ic_gm_prev", "ic_gm_page", "ic_gm_next"}) do
        show(comp(name, panel), pages > 1)
    end
    set_text(comp("ic_gm_prev", panel), "Previous")
    set_text(comp("ic_gm_next", panel), "Next")
    set_text(comp("ic_gm_page", panel),
             string.format("Page %d of %d", ICUI.gm_scroll[page] + 1, pages))
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
                      tip = "Provinces with no governor. Click one's pin to choose a governor."}
        end
    end
    return out
end

function ICUI.gm_draw_column(panel, faction)
    ICUI.gm_make_rows(panel)
    local page = ICUI.gm_page
    for id, p in pairs(ICUI.GM_TOGS) do
        local tog = comp(id, panel)
        local art = ICUI.GM_ROUND_ART[p == page and "selected" or "live"]
        if tog then
            pcall(function()
                tog:SetImagePath(art[1], ICUI.GM_TOG_ART[1])
                tog:SetImagePath(art[2], ICUI.GM_TOG_ART[2])
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
            set_text(hint, "You hold no province.")
        else
            set_text(hint, (chosen and chosen.why) or "Click a party to see what it would take.")
        end
    else
        show(hint, false)
        -- THE PROVINCES PAGE is Task 4's; until then it lists nothing.
        ICUI.gm_draw_page(panel, {}, function() return false end)
    end
end

-- THE RED RINGS: what the chosen party would take.
function ICUI.gm_ring(panel, faction)
    local ringed = {}
    if ICUI.gm_page == "parties" and ICUI.gm_party then
        local r = ICUI.map_rows(faction)[ICUI.gm_party]
        if r then
            for _, p in ipairs((ICUI.map_outline(faction, r.slug))) do ringed[p] = true end
        end
    end
    local pins = comp(ICUI.GM_PINS, panel)
    for i, province in pairs(ICUI.gm_keys) do
        local pin = pins and comp(ICUI.GM_PIN .. "_" .. i, pins)
        if pin then
            pin:SetImagePath(ringed[province] and ICUI.MK_RING_OUTLINE or ICUI.MASK_NONE,
                             ICUI.GP_OUTLINE)
        end
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
    if ICUI.gm_page == "parties" then
        local at = (ICUI.gm_scroll.parties or 0) * ICUI.GM_ROWS + n
        ICUI.gm_party = (ICUI.gm_party ~= at) and at or nil
    end
    ICUI.refresh()
end

-- A PAGE ON: gm_draw_page clamps it to the list.
function ICUI.gm_step(delta)
    local page = ICUI.gm_page
    ICUI.gm_scroll[page] = math.max(0, (ICUI.gm_scroll[page] or 0) + delta)
    ICUI.refresh()
end
```

Edit `ICUI.gm_sync` in three places, and the click listener in one:
1. After `local on = ICUI.gm_on()`, add:

   ```lua
       -- A VIEW ENTERED AFRESH starts with nothing chosen (the party map's rule).
       if on and not ICUI.gm_was_on then ICUI.gm_reset() end
       ICUI.gm_was_on = on
   ```

2. After `panel:SetInteractive(not on)`, add `    ICUI.gm_show_column(panel, on)`.
3. Replace the last line, `    ICUI.gm_draw_pins(panel, ICUI.player())`, with:

   ```lua
       local faction = ICUI.player()
       ICUI.gm_draw_pins(panel, faction)
       ICUI.gm_draw_column(panel, faction)
       ICUI.gm_ring(panel, faction)
       -- THE FOOTER'S PLATE, under the footer line while it has something to say.
       local alert, said = comp("ic_alert", panel), false
       if alert then pcall(function() said = alert:Visible() end) end
       show(comp("ic_gm_foot", panel), said == true)
   ```

4. In the `ic_map_click` listener, after the `ICUI.GM_PIN` branch, add:

   ```lua
           elseif ICUI.GM_TOGS[id] and comp(ICUI.PANEL) then
               ICUI.gm_to_page(ICUI.GM_TOGS[id])
           elseif string.match(id or "", "^" .. ICUI.GM_ROW .. "_%d+$") and comp(ICUI.PANEL) then
               ICUI.gm_row_click(tonumber(string.match(id, "_(%d+)$")))
           elseif (id == "ic_gm_prev" or id == "ic_gm_next") and comp(ICUI.PANEL) then
               ICUI.gm_step(id == "ic_gm_next" and 1 or -1)
   ```

- [ ] **Step 8: Generate and run the harness**

Run: `py tools/gen_ic_ui.py && IC_TEST_ALL=1 "/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | tail -4`
Expected: `iron court harness: ok (N + 9 checks)`.

If the text-on-plate check reports a court cell (a top-strip cell that sits partly below y 124), read its box:
- if it belongs to the strip, widen `ic_gm_top`'s height in both files;
- if it does not, the Governors view must hide it: add it to the cells `gm_sync` hides, and ledger a ruling.

- [ ] **Step 9: Mutants**

Run `py tools/mutate_iron_court.py --selftest` and fix any stale anchor the way Task 2's step 10 says. Then append:

```python
    # THE GOVERNORS VIEW'S COLUMN (plan 2026-09-30 Task 3).
    ("the column left up on another tab", UM,
     """    for _, name in ipairs(ICUI.GM_KEYS) do show(comp(name, panel), on) end""",
     """    for _, name in ipairs(ICUI.GM_KEYS) do show(comp(name, panel), true) end"""),
    ("the column's rows left up on another tab", UM,
     """    for i = 1, ICUI.GM_ROWS do show(comp(ICUI.GM_ROW .. "_" .. i, panel), on) end""",
     """    for i = 1, ICUI.GM_ROWS do show(comp(ICUI.GM_ROW .. "_" .. i, panel), true) end"""),
    ("the footer line with no plate over the map", UM,
     """    show(comp("ic_gm_foot", panel), said == true)""",
     """    show(comp("ic_gm_foot", panel), false)"""),
    ("a view entered afresh keeps the last choice", UM,
     """    if on and not ICUI.gm_was_on then ICUI.gm_reset() end""",
     """    if false then ICUI.gm_reset() end"""),
    ("a closed court remembers the view", UM,
     """    ICUI.gm_was_on = false
    return court_close(...)""",
     """    return court_close(...)"""),
    ("a toggle lit off its page", UM,
     """        local art = ICUI.GM_ROUND_ART[p == page and "selected" or "live"]""",
     """        local art = ICUI.GM_ROUND_ART["live"]"""),
    ("a toggle lit in one state only", UM,
     """                tog:SetImagePath(art[2], ICUI.GM_TOG_ART[2])""",
     """                tog:SetImagePath(ICUI.GM_ROUND_ART.live[2], ICUI.GM_TOG_ART[2])"""),
    ("a chosen party's row not marked", UM,
     """                if (r.look or "live") == "live" and chosen(r, at + i) then r.look = "selected" end""",
     """                if false then r.look = "selected" end"""),
    ("a row's look set in one state only", UM,
     """        row:SetImagePath(art[2], 1)""",
     """        row:SetImagePath(ICUI.GM_ROW_ART.live[2], 1)"""),
    ("a spare row left showing", UM,
     """            show(row, r ~= nil)""",
     """            show(row, true)"""),
    ("a party's choice by slot, not by row of the list", UM,
     """        local at = (ICUI.gm_scroll.parties or 0) * ICUI.GM_ROWS + n""",
     """        local at = n"""),
    ("a second click on a party does not clear it", UM,
     """        ICUI.gm_party = (ICUI.gm_party ~= at) and at or nil""",
     """        ICUI.gm_party = at"""),
    ("the chosen party rings nothing", UM,
     """            for _, p in ipairs((ICUI.map_outline(faction, r.slug))) do ringed[p] = true end""",
     """            for _, p in ipairs({}) do ringed[p] = true end"""),
    ("a party that takes nothing still counts", UM,
     """                      l3 = (not why) and string.format("Would take %d", #list) or nil,""",
     """                      l3 = string.format("Would take %d", #list),"""),
    ("the hint forgets why a party rings nothing", UM,
     """            set_text(hint, (chosen and chosen.why) or "Click a party to see what it would take.")""",
     """            set_text(hint, "Click a party to see what it would take.")"""),
    ("the pager runs past the last page", UM,
     """    ICUI.gm_scroll[page] = math.max(0, math.min(ICUI.gm_scroll[page] or 0, pages - 1))""",
     """    ICUI.gm_scroll[page] = math.max(0, ICUI.gm_scroll[page] or 0)"""),
    ("a pager shown for one page", UM,
     """        show(comp(name, panel), pages > 1)""",
     """        show(comp(name, panel), true)"""),
    ("the column's rows placed at the screen's corner, not the box's", UM,
     """    px, py = px + ICUI.OX, py + ICUI.OY
    for i = 1, ICUI.GM_ROWS do""",
     """    for i = 1, ICUI.GM_ROWS do"""),
```

Run them by name. Expected: `18 mutants, 0 unexplained`.
- The last mutant needs a box offset to be seen. The 1600x900 case of the text-on-plate check gives OX = 0, so if it survives, add a 2560x1080 screen to that check's list: that gives OX = 320, and the rows then fall outside the column. Record the change in the ledger.
- Then run `py tools/gen_ic_ui.py`.

- [ ] **Step 10: Gates.** Every gate, with its expected result:

| Gate | Expected |
|---|---|
| `py tools/gen_ic_ui.py --check` | no drift |
| `py tools/gen_ic_ui.py --selftest` | ok. Run it in the background. |
| `py tools/preview_iron_court.py --check` | ok |
| `luac -p` | parses |
| `check_lua_api.py` | 0 suspects |
| `check_lua_literal_left.py` | 0 sites |
| `check_lua_undeclared.py` | clean |
| `py tools/import_iron_court.py` | `verify ok`, with two more UI files |
| the harness | ok |

Ledger `Task 3: complete (tests: harness -> ok (N checks))`. There is no build: Task 4 builds.

---

### Task 4: The Provinces page - rows, sort, selection, camera, the round buttons, and the weight on the tooltip

**Files:**
- Modify: `tools/gen_ic_ui.py` (`PANEL_LAYOUT`, `_panel`)
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua` (`PANEL_XY`)
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui_map.lua`
  - `ICUI.map_tip`
  - `ICUI.gm_pin_click`
  - the column section
  - the listener
- Modify: `tools/_iron_court_harness.lua`
  - `fake_component` gains `SetDisabled`
  - the main settlement stub gains `display_position_x/y`
  - the old marker tooltip check is updated
  - new checks
- Modify: `tools/mutate_iron_court.py`

**Interfaces:**
- Consumes:
  - Task 1: `IC.province_levels`, `IC.gov_weight_of`.
  - Task 3: `ICUI.gm_draw_page`, `ICUI.gm_fill_row`, `ICUI.gm_rows`, `ICUI.gm_ring`, `ICUI.gm_row_click`, `ICUI.gm_page`, `ICUI.gm_scroll`, `ICUI.GM_KEYS`, `gm_row(panel, i)`.
- Produces (map Lua):
  - `ICUI.gm_sel`, the chosen province key or nil;
  - `ICUI.GM_SORTS = {{"Province", 1}, {"Governor", 2}, {"Loyalty", 4}}`;
  - `ICUI.GM_FEALTY` and `ICUI.gm_fealty(loyalty) -> path`;
  - `ICUI.gm_held(faction, province) -> boolean`;
  - `ICUI.gm_province_rows(faction) -> rows, keys`, where each row also carries `key`;
  - `ICUI.gm_look_at(faction, province)`;
  - `ICUI.gm_enable(c, on)`;
  - `ICUI.gm_open_picker(province)`: the pin's and the check's one way into the governor picker;
  - `ICUI.map_tip(faction, province, row)`: `row` swaps the pin's click line for "Click to choose this province.";
  - `ICUI.gm_ok()`, `ICUI.gm_no()`, `ICUI.gm_sort_click(i)`.
- Produces (panel): `ic_gm_sort_1..3`, `ic_gm_btns`, `ic_gm_ok`, `ic_gm_no`.

- [ ] **Step 1: Snapshot** every file this task edits to the scratchpad as `*_before_govmap_t4.*`.

- [ ] **Step 2: The fixture's new answers**

In `fake_component`, after `SetInteractive`, add:

```lua
    -- SetDisabled blocks the click in game; recorded so a check can see a
    -- button that looks live and is not.
    function c:SetDisabled(on)
        IC_NEED_BOOL("SetDisabled on " .. tostring(self.name), on); self.disabled = on end
```

In the main region's settlement table (~line 420), beside `logical_position_y`, add:

```lua
                                -- WHERE THE CAMERA GOES for this settlement: a
                                -- different x per region, so a check can tell them apart.
                                display_position_x = function() return 300 + i end,
                                display_position_y = function() return 400 end,
```

`i` there is the 0-based province index, so the second province answers x = 301.

Confirm that `check_character_stub` in `import_iron_court.py` does not police the settlement stub: it holds the character's and the faction's methods. If it does, both names are documented on `SETTLEMENT_SCRIPT_INTERFACE`; `check_lua_api.py --explain display_position_x` shows the entry.

In `with_fake_govmap`, before its `ICUI.register()`, add:

```lua
    -- MAP ORDER ON THE PROVINCES PAGE: these checks name rows by position, and
    -- the sort and the page are session state an earlier check may have moved.
    ICUI.sort.govs, ICUI.sort_desc.govs = 1, false
    ICUI.gm_page = "provinces"
```

- [ ] **Step 3: Write the failing checks**

Update the old map check "a marker's tooltip names the province, its governor, party and loyalty" (~line 27620). Where it asserts the `Party: ` line, assert the weight line instead:

```lua
        -- WHAT THE PROVINCE ADDS TO HIS PARTY (spec 2026-09-30 section 4).
        assert(tip:find(ICUI.house_name("legion", F) .. ": +1 weight from this province", 1, true),
            "the tooltip does not say what the province adds: " .. tip)
```

Use the local that check already names its tooltip text with. The `+1` is the fixture's weight: its provinces have no `_levels`, so they count 0 levels, which is 1 weight.

Add, above `check("no parties' turn failed anywhere in the run"`:

```lua
check("a Provinces row draws its governor's face, his crest, or an empty seat", function()
    IC.state = {}
    local seen = make_character(3201, ANY_SEAT, "legion")
    local bare = make_character(3202, ANY_SEAT, "legion")
    local away = make_character(3203, ANY_SEAT, "legion", "prov_elsewhere")
    away._force = true
    make_faction(F, IC.CHD_SUBCULTURE, {seen, bare, away}, {"prov_a", "prov_b", "prov_c", "prov_d"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    IC.court(F).govs["prov_a"] = 3201
    IC.court(F).govs["prov_c"] = 3202
    IC.court(F).govs["prov_d"] = 3203
    IC_TEST_PORTRAITS = {["3201"] = "ui/portraits/portholes/chd/overseer.png"}
    IC_TEST_LOC = {provinces_onscreen_prov_a = "The Plain of Zharr"}
    with_fake_govmap(function(hud, panel, extra, holder)
        ICUI.view = "govs"
        ICUI.pick = nil
        ICUI.open()
        assert(ICUI.gm_page == "provinces", "the column opened on " .. tostring(ICUI.gm_page))
        local a, b, c, d = gm_row(panel, 1), gm_row(panel, 2), gm_row(panel, 3), gm_row(panel, 4)
        -- A NAME, NOT A KEY.
        assert(a.children.ic_gr_l1.text == "The Plain of Zharr", "row 1 reads " .. a.children.ic_gr_l1.text)
        assert(a.children.ic_gr_l2.text == ICUI.character_name(seen), "row 1's governor reads " .. a.children.ic_gr_l2.text)
        -- HIS FACE, ON HIS PARTY'S PLATE, WITH HIS PARTY'S CREST ON ITS CORNER.
        assert(a.children.ic_gr_face.visible and a.children.ic_gr_face.images[ICUI.FACE_INDEX]
               == "ui/portraits/portholes/chd/overseer.png", "row 1 draws no face")
        assert(a.children.ic_gr_face.images[ICUI.PLATE_INDEX] == ICUI.plate_path("legion"), "row 1's face has no party plate")
        assert(a.children.ic_gr_badge.visible and a.children.ic_gr_badge.images[0] == ICUI.crest("legion"),
            "row 1 wears no party crest")
        -- +N WEIGHT, THE MODEL'S OWN FIGURE.
        local w = IC.gov_weight_of(IC.province_levels(F).prov_a)
        assert(a.children.ic_gr_l3.text == string.format("%d%%, +%d weight", IC.province_loyalty(F, "prov_a"), w),
            "row 1's last line reads " .. a.children.ic_gr_l3.text)
        assert(a.children.ic_gr_icon.visible and a.children.ic_gr_icon.images[0]
               == ICUI.gm_fealty(IC.province_loyalty(F, "prov_a")), "row 1 has no loyalty icon")
        -- AN EMPTY SEAT: the silhouette on NO plate, "None assigned", no weight.
        assert(b.children.ic_gr_face.images[ICUI.FACE_INDEX] == ICUI.SILHOUETTE, "an empty seat draws " .. tostring(b.children.ic_gr_face.images[ICUI.FACE_INDEX]))
        assert(b.children.ic_gr_face.images[ICUI.PLATE_INDEX] == ICUI.MASK_NONE, "an empty seat wears a colour")
        assert(b.children.ic_gr_l2.text == "None assigned", "an empty seat's governor reads " .. b.children.ic_gr_l2.text)
        assert(not b.children.ic_gr_l3.text:find("weight", 1, true), "an empty seat adds weight: " .. b.children.ic_gr_l3.text)
        assert(not b.children.ic_gr_badge.visible, "an empty seat wears a party crest")
        -- A FACE THAT WILL NOT RESOLVE: his party's crest in its place.
        assert(not c.children.ic_gr_face.visible, "an unresolved face still draws")
        assert(c.children.ic_gr_crest.visible and c.children.ic_gr_crest.images[0] == ICUI.crest("legion"),
            "an unresolved face has no crest in its place")
        -- AWAY, IN WORDS.
        assert(d.children.ic_gr_l2.text:find("(away)", 1, true), "an away governor reads " .. d.children.ic_gr_l2.text)
        -- WHAT HIS RANK ADDS rides on the tooltip.
        -- "he adds +", NOT "rank": map_tip's own governor line already says "rank N".
        assert(a.tooltip:find("he adds +", 1, true), "row 1's tooltip does not say what his rank adds")
        -- A ROW IS CHOSEN, NOT APPOINTED: the pin's "Click to replace" is wrong here.
        assert(a.tooltip:find("Click to choose this province.", 1, true)
               and not a.tooltip:find("Click to replace", 1, true), "row 1's tooltip reads: " .. a.tooltip)
    end)
    IC_TEST_PORTRAITS, IC_TEST_LOC = nil, nil
end)

check("choosing a province moves the camera to it, keeping the zoom, and rings its pin; again clears it", function()
    IC.state = {}
    make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a", "prov_b"})
    IC.add_house(F, IC.CROWN)
    local was_cam, was_pos = cm.scroll_camera_from_current, cm.get_camera_position
    local moved = {}
    cm.get_camera_position = function() return 10, 20, 30, 0.5, 40 end
    cm.scroll_camera_from_current = function(_, correct, time, pos) moved[#moved + 1] = pos end
    local ok, err = pcall(with_fake_govmap, function(hud, panel, extra, holder)
        ICUI.view = "govs"
        ICUI.pick = nil
        ICUI.open()
        map_click(ICUI.GM_ROW .. "_2")
        assert(ICUI.gm_sel == "prov_b", "the second row chose " .. tostring(ICUI.gm_sel))
        assert(#moved == 1, #moved .. " camera moves for one choice")
        local p = moved[1]
        assert(p[1] == 301 and p[2] == 400, "the camera went to " .. p[1] .. "," .. p[2])
        assert(p[3] == 30 and p[4] == 0.5 and p[5] == 40, "the camera's zoom and bearing were not kept")
        assert(gm_pin(holder, 2).images[ICUI.GP_OUTLINE] == ICUI.MK_RING_OUTLINE, "the chosen province's pin is not ringed")
        assert(gm_pin(holder, 1).images[ICUI.GP_OUTLINE] == ICUI.MASK_NONE, "another pin is ringed")
        assert(gm_row(panel, 2).images[0] == ICUI.GM_ROW_ART.selected[1], "the chosen row does not look chosen")
        map_click(ICUI.GM_ROW .. "_2")
        assert(ICUI.gm_sel == nil, "a second click kept the choice")
        assert(#moved == 1, "clearing the choice moved the camera")
        assert(gm_pin(holder, 2).images[ICUI.GP_OUTLINE] == ICUI.MASK_NONE, "a cleared choice left its ring")
    end)
    cm.scroll_camera_from_current, cm.get_camera_position = was_cam, was_pos
    assert(ok, err)
end)

check("the round buttons: disabled with nothing chosen, hidden on Parties, the cross only for a governed province",
function()
    IC.state = {}
    local g = make_character(3211, ANY_SEAT, "legion")
    make_faction(F, IC.CHD_SUBCULTURE, {g}, {"prov_a", "prov_b"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    IC.court(F).govs["prov_a"] = 3211
    with_fake_govmap(function(hud, panel, extra, holder)
        ICUI.view = "govs"
        ICUI.pick = nil
        ICUI.open()
        local ok_b, no_b = panel.children.ic_gm_ok, panel.children.ic_gm_no
        assert(ok_b.visible and ok_b.disabled == true, "the check is live with nothing chosen")
        assert(no_b.visible and no_b.disabled == true, "the cross is live with nothing chosen")
        map_click("ic_gm_ok")
        assert(ICUI.pick == nil, "a disabled check opened a picker")
        -- A GOVERNED PROVINCE: both live.
        map_click(ICUI.GM_ROW .. "_1")
        assert(ok_b.disabled == false and no_b.visible and no_b.disabled == false,
            "a governed province's buttons are not both live")
        -- AN EMPTY ONE: nothing to release, so no cross.
        map_click(ICUI.GM_ROW .. "_2")
        assert(ok_b.disabled == false, "an empty province cannot be given a governor")
        assert(not no_b.visible, "the cross offers to release nobody")
        -- THE PARTIES PAGE has neither.
        map_click("ic_gm_tog_1")
        assert(not ok_b.visible and not no_b.visible and not panel.children.ic_gm_btns.visible,
            "the round buttons show on the Parties page")
        for i = 1, 3 do assert(not panel.children["ic_gm_sort_" .. i].visible, "a sort shows on the Parties page") end
    end)
end)

check("the check opens the governor picker for the chosen province", function()
    IC.state = {}
    make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a", "prov_b"})
    IC.add_house(F, IC.CROWN)
    with_fake_govmap(function(hud, panel, extra, holder)
        ICUI.view = "govs"
        ICUI.pick = nil
        ICUI.open()
        map_click(ICUI.GM_ROW .. "_2")
        map_click("ic_gm_ok")
        assert(ICUI.pick and ICUI.pick.kind == "gov" and ICUI.pick.key == "prov_b",
            "the check opened " .. tostring(ICUI.pick and ICUI.pick.key))
    end)
end)

check("the cross releases the selected province, whatever page it is on", function()
    IC.state = {}
    local provinces, men = {}, {}
    for i = 1, ICUI.GM_ROWS + 2 do
        provinces[i] = "prov_" .. string.char(96 + i)
        men[i] = make_character(3300 + i, ANY_SEAT, "legion")
    end
    make_faction(F, IC.CHD_SUBCULTURE, men, provinces)
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    for i, p in ipairs(provinces) do IC.court(F).govs[p] = 3300 + i end
    local last = provinces[#provinces]
    with_fake_govmap(function(hud, panel, extra, holder)
        ICUI.view = "govs"
        ICUI.pick = nil
        ICUI.open()
        map_click("ic_gm_next")
        -- PAGE TWO'S SECOND ROW is the ninth province.
        map_click(ICUI.GM_ROW .. "_2")
        assert(ICUI.gm_sel == last, "page two's second row chose " .. tostring(ICUI.gm_sel))
        map_click("ic_gm_no")
        assert(IC.court(F).govs[last] == nil, "the cross did not release " .. last)
        assert(IC.court(F).govs[provinces[2]] == 3302, "the cross released page one's second row")
        -- ANSWERED, and the row redrawn empty.
        assert(gm_row(panel, 2).children.ic_gr_l2.text == "None assigned", "the released row still names a governor")
    end)
end)

check("a sorted Provinces page chooses and appoints the province it drew, and keeps it through a sort", function()
    IC.state = {}
    make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a", "prov_b", "prov_c"})
    IC.add_house(F, IC.CROWN)
    IC_TEST_LOC = {provinces_onscreen_prov_a = "Cinder", provinces_onscreen_prov_b = "Ash",
                   provinces_onscreen_prov_c = "Basalt"}
    with_fake_govmap(function(hud, panel, extra, holder)
        ICUI.view = "govs"
        ICUI.pick = nil
        ICUI.sort.govs, ICUI.sort_desc.govs = 1, false
        ICUI.open()
        map_click("ic_gm_sort_1")                  -- by Province: Ash, Basalt, Cinder
        assert(gm_row(panel, 1).children.ic_gr_l1.text == "Ash", "the first row reads " .. gm_row(panel, 1).children.ic_gr_l1.text)
        assert(panel.children.ic_gm_sort_1.text:find("Province", 1, true)
               and panel.children.ic_gm_sort_1.text ~= "Province", "the sorted column is not lit")
        map_click(ICUI.GM_ROW .. "_1")
        assert(ICUI.gm_sel == "prov_b", "the first row chose " .. tostring(ICUI.gm_sel))
        -- RE-SORTED UNDER IT: the choice is a province, not a row.
        map_click("ic_gm_sort_1")                  -- descending: Cinder, Basalt, Ash
        assert(ICUI.gm_sel == "prov_b", "a sort moved the choice to " .. tostring(ICUI.gm_sel))
        assert(gm_row(panel, 3).images[0] == ICUI.GM_ROW_ART.selected[1], "the chosen province's new row does not look chosen")
        assert(gm_pin(holder, 2).images[ICUI.GP_OUTLINE] == ICUI.MK_RING_OUTLINE, "a sort moved the ring")
        map_click("ic_gm_ok")
        assert(ICUI.pick and ICUI.pick.key == "prov_b", "the check after a sort opened " .. tostring(ICUI.pick and ICUI.pick.key))
        -- AND THE THIRD CLICK IS MAP ORDER AGAIN.
        ICUI.pick = nil
        map_click("ic_gm_sort_1")
        assert(ICUI.sort.govs == 1, "the third click did not hand back map order")
    end)
    IC_TEST_LOC = nil
    ICUI.sort.govs, ICUI.sort_desc.govs = 1, false
end)

check("every province is reachable once the Provinces page outruns its rows", function()
    IC.state = {}
    local provinces = {}
    for i = 1, ICUI.GM_ROWS * 2 + 1 do provinces[i] = "prov_" .. string.char(96 + i) end
    make_faction(F, IC.CHD_SUBCULTURE, {}, provinces)
    IC.add_house(F, IC.CROWN)
    with_fake_govmap(function(hud, panel, extra, holder)
        ICUI.view = "govs"
        ICUI.pick = nil
        ICUI.open()
        local seen = {}
        for page = 1, 3 do
            for i = 1, ICUI.GM_ROWS do
                local r = ICUI.gm_rows[i]
                if r then seen[r.key] = true end
            end
            if page < 3 then map_click("ic_gm_next") end
        end
        for _, p in ipairs(provinces) do assert(seen[p], p .. " is on no page") end
        assert(panel.children.ic_gm_page.text == "Page 3 of 3", panel.children.ic_gm_page.text)
    end)
end)

check("a chosen province that is lost clears the choice and releases nothing", function()
    IC.state = {}
    local g = make_character(3221, ANY_SEAT, "legion")
    make_faction(F, IC.CHD_SUBCULTURE, {g}, {"prov_a", "prov_b"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    IC.court(F).govs["prov_b"] = 3221
    with_fake_govmap(function(hud, panel, extra, holder)
        ICUI.view = "govs"
        ICUI.pick = nil
        ICUI.open()
        map_click(ICUI.GM_ROW .. "_2")
        assert(ICUI.gm_sel == "prov_b", "the fixture chose nothing")
        make_faction(F, IC.CHD_SUBCULTURE, {g}, {"prov_a"})
        map_click("ic_gm_ok")
        assert(ICUI.pick == nil, "a lost province reached the picker")
        assert(ICUI.gm_sel == nil, "the lost province is still chosen")
    end)
end)

check("a province's loyalty icon follows its loyalty", function()
    assert(ICUI.gm_fealty(IC.TUNE.prov_defect_floor) == ICUI.GM_FEALTY.low, "at the defection floor")
    assert(ICUI.gm_fealty(IC.TUNE.prov_loyalty_start) == ICUI.GM_FEALTY.medium, "at the starting loyalty")
    assert(ICUI.gm_fealty(IC.TUNE.prov_loyalty_start + 1) == ICUI.GM_FEALTY.high, "above the starting loyalty")
    assert(ICUI.GM_FEALTY.low ~= ICUI.GM_FEALTY.medium and ICUI.GM_FEALTY.medium ~= ICUI.GM_FEALTY.high,
        "two bands share one icon")
end)

check("a pin's tooltip says what its province adds to its party", function()
    IC.state = {}
    local g = make_character(3231, ANY_SEAT, "legion")
    local f = make_faction(F, IC.CHD_SUBCULTURE, {g}, {"prov_a"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    IC.court(F).govs["prov_a"] = 3231
    f._levels = {prov_a = 3}
    f._extra_regions = {{province = "prov_a", name = "region_prov_a_minor", cqi = 1990, level = 4}}
    IC.refresh_gov_weight(F)
    local tip = ICUI.map_tip(F, "prov_a")
    local want = string.format("%s: +4 weight from this province (7 settlement levels), %d%% of the court",
                               ICUI.house_name("legion", F), math.floor(IC.share(F, "legion") + 0.5))
    assert(tip:find(want, 1, true), "the tooltip reads: " .. tip)
    f._levels, f._extra_regions = nil, nil
end)

check("the column's cross sends its release in multiplayer and waits for the trigger", function()
    IC.state = {}
    turn = 1
    local f = make_faction(F, IC.CHD_SUBCULTURE, {make_character(3251, ANY_SEAT, "legion")}, {"prov_a"})
    f._cqi = 41
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    IC.court(F).govs["prov_a"] = 3251
    cm.get_human_factions = function() return {F} end
    IC.register()
    local ran, was = 0, IC.release_governor
    IC.release_governor = function() ran = ran + 1 return true end
    local ok, err = pcall(with_fake_govmap, function(hud, panel, extra, holder)
        ICUI.view = "govs"
        ICUI.pick = nil
        ICUI.open()
        map_click(ICUI.GM_ROW .. "_1")
        with_mp(F, function(sent)
            map_click("ic_gm_no")
            assert(ran == 0, "the cross released before its trigger came back")
            assert(#sent == 1, "the cross sent " .. #sent .. " triggers")
            deliver(sent[1])
            assert(ran == 1, "the cross's trigger reached the model " .. ran .. " times")
        end)
    end)
    IC.release_governor = was
    cm.get_human_factions = function() return {} end
    assert(ok, err)
end)
```

- [ ] **Step 4: Run the harness and verify that it fails**

Run: `IC_TEST_ALL=1 "/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | grep "^FAIL"`

Expected:
- the 11 new checks fail;
- the updated marker tooltip check fails on "does not say what the province adds".

- [ ] **Step 5: The generator and the panel's new cells**

In `PANEL_LAYOUT`, after `"ic_gm_hint"`, add the following. Add the same six boxes to `ICUI.PANEL_XY`:

```python
    # THE PROVINCES PAGE'S SORT, in the hint's slot: the hint is the Parties
    # page's and these are the Provinces page's, never both on screen.
    "ic_gm_sort_1": (16, 286, 132, 26),
    "ic_gm_sort_2": (156, 286, 132, 26),
    "ic_gm_sort_3": (296, 286, 132, 26),
    # CA'S ACCEPT AND CANCEL on the Hell-Forge's own button plate.
    "ic_gm_btns": (0, 920, 444, 90),
    "ic_gm_ok": (150, 937, 56, 56),
    "ic_gm_no": (238, 937, 56, 56),
```

In `_panel()`, after the `ic_gm_page` branch, add:

```python
        if name.startswith("ic_gm_sort_"):
            # THE COURT'S ARROW AT THE END OF ITS LABEL; the label is lit from
            # Lua while its column sorts, as the court's headers are.
            panel.add(EU.C(name, w, h, interactive=True, sound=SORT_SOUND,
                           layers=[{"path": SORT_ARROW_DOWN, "offset": (w - 21, (h - 18) / 2.0),
                                    "dw": 17 - w, "dh": 18 - h, "margin": 0, "dock": None}],
                           **style(name, valign="Center")))
            continue
        if name == "ic_gm_btns":
            panel.add(EU.C(name, w, h, layers=[_gm_full(GM_HF + "button_holder_back.png")]))
            continue
        if name in ("ic_gm_ok", "ic_gm_no"):
            icon = ("ui/skins/default/icon_check.png" if name == "ic_gm_ok"
                    else "ui/skins/default/icon_cross.png")
            # THE TOOLTIP IS WRITTEN FROM LUA, per page; the round button's own
            # states are CA's, and the disabled look is ICUI.grey_look.
            panel.add(EU.C(name, w, h, interactive=True, sound=OPENER_SOUND,
                           layers=[_gm_full(GM_ROUND % "active"), _gm_inset(icon, 12)],
                           hover=[_gm_full(GM_ROUND % "hover"), _gm_inset(icon, 12)]))
            continue
```

- [ ] **Step 6: The Provinces page in the map Lua**

In `ICUI.map_tip`, replace

```lua
        local slug = IC.house_of_cqi(faction_key, cqi)
        if slug then lines[#lines + 1] = "Party: " .. ICUI.house_name(slug, faction_key) end
```

with

```lua
        local slug = IC.house_of_cqi(faction_key, cqi)
        if slug then
            -- WHAT THIS PROVINCE ADDS TO HIS PARTY (spec 2026-09-30 section 4).
            local levels = IC.province_levels(faction_key)[province] or 0
            lines[#lines + 1] = string.format(
                "%s: +%d weight from this province (%d settlement level%s), %d%% of the court",
                ICUI.house_name(slug, faction_key), IC.gov_weight_of(levels), levels,
                levels == 1 and "" or "s", math.floor(IC.share(faction_key, slug) + 0.5))
        end
```

Change its signature to `function ICUI.map_tip(faction_key, province, row)`, and replace its last line

```lua
    lines[#lines + 1] = man and "Click to replace its governor." or "Click to choose its governor."
```

with

```lua
    -- A ROW CHOOSES; A PIN APPOINTS.
    if row then lines[#lines + 1] = "Click to choose this province."
    else lines[#lines + 1] = man and "Click to replace its governor." or "Click to choose its governor." end
```

In `ICUI.gm_pin_click`, replace

```lua
    local held = false
    for _, p in ipairs(IC.seats(faction)) do if p == province then held = true end end
    if not held then ICUI.refresh() return end
    ICUI.pick = {kind = "gov", key = province}
    ICUI.scroll.pick = 0
    ICUI.notice = nil
    ICUI.refresh()
```

with

```lua
    if not ICUI.gm_held(faction, province) then ICUI.refresh() return end
    ICUI.gm_open_picker(province)
```

Re-aim Task 2's mutant "a pin opens a picker for a province already lost" at the new first line, with the replacement `    if false then ICUI.refresh() return end`.

Add to `ICUI.GM_KEYS`: `"ic_gm_sort_1", "ic_gm_sort_2", "ic_gm_sort_3", "ic_gm_btns", "ic_gm_ok", "ic_gm_no"`.

After `ICUI.gm_party_rows`, add:

```lua
ICUI.gm_sel = nil                    -- the chosen province on the Provinces page
-- THE PROVINCES PAGE'S SORT: the court's own Governors modes (ICUI.SORTS.govs),
-- by column. Map order is what a third click returns to (plan ruling 13).
ICUI.GM_SORTS = {{"Province", 1}, {"Governor", 2}, {"Loyalty", 4}}
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
    ICUI.scroll.pick = 0
    ICUI.notice = nil
    ICUI.refresh()
end

-- THE PROVINCES PAGE: the Governors list, moved (spec section 1), in the order
-- the player asked for.
function ICUI.gm_province_rows(faction)
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
        local tip = ICUI.map_tip(faction, p, true)
        if holder then tip = tip .. "\n" .. ICUI.gov_rank_tip(faction, p, holder) end
        rows[i] = {
            key = p, l1 = name, l2 = gov,
            l3 = cqi and string.format("%d%%, +%d weight", loyal, IC.gov_weight_of(levels[p]))
                 or string.format("%d%%", loyal),
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
```

In `ICUI.gm_draw_column`, replace the `else` branch (the "Task 4's; until then it lists nothing" one) with:

```lua
    else
        show(hint, false)
        local rows, keys = ICUI.gm_province_rows(faction)
        -- A CHOICE THAT IS NO LONGER HELD is no choice.
        local held = false
        for _, k in ipairs(keys) do if k == ICUI.gm_sel then held = true end end
        if not held then ICUI.gm_sel = nil end
        ICUI.gm_draw_page(panel, rows, function(r) return r.key == ICUI.gm_sel end)
        for i, s in ipairs(ICUI.GM_SORTS) do
            local c = comp("ic_gm_sort_" .. i, panel)
            if c then
                local active = ICUI.sort.govs == ICUI.sort_for_column("govs", s[2])
                set_text(c, active and string.format("[[col:%s]]%s[[/col]]", ICUI.SORT_LIT, s[1]) or s[1])
                pcall(function() c:SetImagePath(ICUI.sort_arrow_path("govs", s[2]), 0) end)
            end
        end
    end
    -- THE ROUND BUTTONS: the Provinces page's. The cross only for a province
    -- with a governor to release; both dead with nothing chosen. Worked out
    -- first and drawn after, so another page can say what they do there.
    local governed = ICUI.gm_sel ~= nil and IC.court(faction).govs[ICUI.gm_sel] ~= nil
    local btns = page == "provinces"
    local ok_on, no_on = ICUI.gm_sel ~= nil, governed
    local no_shown = ICUI.gm_sel == nil or governed
    local ok_tip = "Choose who governs the chosen province."
    local no_tip = "Release the chosen province's governor."
    for i = 1, #ICUI.GM_SORTS do show(comp("ic_gm_sort_" .. i, panel), page == "provinces") end
    show(comp("ic_gm_btns", panel), btns)
    show(comp("ic_gm_ok", panel), btns)
    show(comp("ic_gm_no", panel), btns and no_shown)
    ICUI.gm_enable(comp("ic_gm_ok", panel), ok_on)
    ICUI.gm_enable(comp("ic_gm_no", panel), no_on)
    local ok_b, no_b = comp("ic_gm_ok", panel), comp("ic_gm_no", panel)
    if ok_b then ok_b:SetTooltipText(ok_tip, "", true) end
    if no_b then no_b:SetTooltipText(no_tip, "", true) end
```

In `ICUI.gm_ring`, after the Parties block, add:

```lua
    if ICUI.gm_page == "provinces" and ICUI.gm_sel then ringed[ICUI.gm_sel] = true end
```

In `ICUI.gm_reset`, add `    ICUI.gm_sel = nil`.

In `ICUI.gm_row_click`, before the `end` that closes its `if ICUI.gm_page == "parties"` block, add:

```lua
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
```

Add:

```lua
function ICUI.gm_sort_click(i)
    local s = ICUI.GM_SORTS[i]
    if not s or not ICUI.gm_on() or ICUI.gm_page ~= "provinces" then return end
    if ICUI.click_column("govs", s[2]) then
        ICUI.gm_scroll.provinces = 0
        ICUI.refresh()
    end
end

-- THE CHECK: choose who governs the chosen province.
function ICUI.gm_ok()
    if not ICUI.gm_on() then return end
    local faction = ICUI.player()
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
    if ICUI.gm_page ~= "provinces" or not ICUI.gm_sel then return end
    if not IC.court(faction).govs[ICUI.gm_sel] then return end
    ICUI.send(faction, "ungov", ICUI.gm_sel)
    ICUI.refresh()
end
```

In the listener, after the `ic_gm_prev`/`ic_gm_next` branch, add:

```lua
        elseif string.match(id or "", "^ic_gm_sort_%d$") and comp(ICUI.PANEL) then
            ICUI.gm_sort_click(tonumber(string.match(id, "(%d)$")))
        elseif id == "ic_gm_ok" and comp(ICUI.PANEL) then
            ICUI.gm_ok()
        elseif id == "ic_gm_no" and comp(ICUI.PANEL) then
            ICUI.gm_no()
```

- [ ] **Step 7: Generate and run the harness**

Run: `py tools/gen_ic_ui.py && IC_TEST_ALL=1 "/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | tail -4`
Expected: `ok (N checks)`, with the 11 new checks counted in.

- [ ] **Step 8: Mutants**

Run `py tools/mutate_iron_court.py --selftest`: re-aim the map_tip `Party:` mutants, if any, at the weight line. Then append:

```python
    # THE PROVINCES PAGE (plan 2026-09-30 Task 4).
    ("a province's weight on its tooltip from the flat rule", UM,
     """                ICUI.house_name(slug, faction_key), IC.gov_weight_of(levels), levels,""",
     """                ICUI.house_name(slug, faction_key), 3, levels,"""),
    ("a Provinces row tells the player a click appoints", UM,
     """        local tip = ICUI.map_tip(faction, p, true)""",
     """        local tip = ICUI.map_tip(faction, p)"""),
    ("a Provinces row with no weight figure", UM,
     """            l3 = cqi and string.format("%d%%, +%d weight", loyal, IC.gov_weight_of(levels[p]))""",
     """            l3 = cqi and string.format("%d%%", loyal)"""),
    ("an empty seat drawn with no silhouette", UM,
     """            face = port or ((not cqi) and ICUI.SILHOUETTE or nil),""",
     """            face = port,"""),
    ("an unresolved face with no crest in its place", UM,
     """            crest = (cqi and not port and slug) and ICUI.crest(slug) or nil,""",
     """            crest = nil,"""),
    ("a governor's face with no party crest on it", UM,
     """            badge = (port and slug) and ICUI.crest(slug) or nil,""",
     """            badge = nil,"""),
    ("the Provinces page ignores the sort", UM,
     """    ICUI.sort_rows("govs", rows, keys, #rows)
    return rows, keys""",
     """    return rows, keys"""),
    ("a lost province stays chosen", UM,
     """        if not held then ICUI.gm_sel = nil end""",
     """        if false then ICUI.gm_sel = nil end"""),
    ("a chosen province's row not marked", UM,
     """        ICUI.gm_draw_page(panel, rows, function(r) return r.key == ICUI.gm_sel end)""",
     """        ICUI.gm_draw_page(panel, rows, function(r) return false end)"""),
    ("the chosen province's pin not ringed", UM,
     """    if ICUI.gm_page == "provinces" and ICUI.gm_sel then ringed[ICUI.gm_sel] = true end""",
     """    if false then ringed[ICUI.gm_sel] = true end"""),
    ("choosing a province leaves the camera where it was", UM,
     """                ICUI.gm_look_at(ICUI.player(), r.key)""",
     """                local _ = r.key"""),
    ("the camera's zoom thrown away", UM,
     """        cm:scroll_camera_from_current(true, 1, {x, y, d, b, h})""",
     """        cm:scroll_camera_from_current(true, 1, {x, y, 14.7, 0, 12})"""),
    ("a second click on a province does not clear it", UM,
     """            if ICUI.gm_sel == r.key then
                ICUI.gm_sel = nil""",
     """            if false then
                ICUI.gm_sel = nil"""),
    ("the check live with nothing chosen", UM,
     """    local ok_on, no_on = ICUI.gm_sel ~= nil, governed""",
     """    local ok_on, no_on = true, governed"""),
    ("the cross live for an empty province", UM,
     """    local ok_on, no_on = ICUI.gm_sel ~= nil, governed""",
     """    local ok_on, no_on = ICUI.gm_sel ~= nil, ICUI.gm_sel ~= nil"""),
    ("the cross offered for an empty province", UM,
     """    local no_shown = ICUI.gm_sel == nil or governed""",
     """    local no_shown = true"""),
    ("the round buttons shown on the Parties page", UM,
     """    show(comp("ic_gm_ok", panel), btns)""",
     """    show(comp("ic_gm_ok", panel), true)"""),
    ("a dead button only looks dead", UM,
     """    pcall(function() c:SetDisabled(not on) end)""",
     """    local _ = on"""),
    ("a disabled check still opens a picker", UM,
     """    if ICUI.gm_page ~= "provinces" or not ICUI.gm_sel then return end
    if not ICUI.gm_held(faction, ICUI.gm_sel) then""",
     """    if ICUI.gm_page ~= "provinces" then return end
    if not ICUI.gm_held(faction, ICUI.gm_sel) then"""),
    ("the check sends a lost province to the picker", UM,
     """    if not ICUI.gm_held(faction, ICUI.gm_sel) then
        ICUI.gm_sel = nil""",
     """    if false then
        ICUI.gm_sel = nil"""),
    ("the sort lands mid-list after a re-sort", UM,
     """        ICUI.gm_scroll.provinces = 0""",
     """        ICUI.gm_scroll.provinces = ICUI.gm_scroll.provinces"""),
    ("the loyalty icon high at the start", UM,
     """    if loyalty > IC.TUNE.prov_loyalty_start then return ICUI.GM_FEALTY.high end""",
     """    if loyalty >= IC.TUNE.prov_loyalty_start then return ICUI.GM_FEALTY.high end"""),
    ("the loyalty icon never low", UM,
     """    if loyalty <= IC.TUNE.prov_defect_floor then return ICUI.GM_FEALTY.low end""",
     """    if false then return ICUI.GM_FEALTY.low end"""),
```

Run them by name. Expected: `23 mutants, 0 unexplained`.
- "the sort lands mid-list after a re-sort" needs the sort check to start on page two. If it survives, add a page-two start to "a sorted Provinces page..." (give it `ICUI.GM_ROWS + 2` provinces and a `map_click("ic_gm_next")` before the first sort, asserting page 1 after it). Ledger the change.
- Then run `py tools/gen_ic_ui.py`.

- [ ] **Step 9: Gates.** Every gate, with its expected result:

| Gate | Expected |
|---|---|
| `py tools/gen_ic_ui.py --check` | no drift |
| `py tools/gen_ic_ui.py --selftest` | ok. Run it in the background with a 600s wait loop; it outlasts the tool timeout. |
| `py tools/preview_iron_court.py --check` | ok |
| `luac -p` on the Iron Court UI and map Lua files | parses |
| `py tools/check_lua_api.py` on the same files | 0 suspects |
| `py tools/check_lua_literal_left.py` | 0 sites |
| `py tools/check_lua_undeclared.py` | clean |
| `py tools/import_iron_court.py` | `verify ok` |
| the harness | `ok (N checks)` |

- [ ] **Step 10: Build and deploy**
  1. Start RPFM's server headless if `http://127.0.0.1:45127/sessions` does not answer: `Start-Process "G:\Modding for resources\RPFM\rpfm_server.exe" -WindowStyle Hidden`.
  2. Run `py tools/deploy_iron_court.py`. Expected:
     - it builds, verifies and prints the build name (the first 8 hex digits of its MD5);
     - if `Warhammer3.exe` is not running, it deploys to data/.
  3. Stop the server.
  4. Ledger `Task 4: complete (tests: harness -> ok (N checks); build <NAME> deployed)`.

  No STOP here: the build is for the author to play with while Task 5 proceeds. Name it in the ledger.

---

### Task 5: The governor picker in the column

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua`
  - `ICUI.draw_picker` is split: `ICUI.picker_lines` is extracted from it.
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui_map.lua`
  - `gm_on`
  - `gm_open_picker`
  - `gm_draw_page`
  - `gm_step`
  - `gm_draw_column`
  - `gm_ring`
  - `gm_row_click`
  - `gm_ok`
  - `gm_no`
  - `gm_sort_click`
- Modify: `tools/_iron_court_harness.lua`
  - Task 2's pin check is inverted.
  - New checks are added.
  - A multiplayer check for the column's check button.
- Modify: `tools/mutate_iron_court.py`

**Interfaces:**
- Consumes:
  - Task 2: `ICUI.gm_pin_click`, `gm_pin(holder, i)`.
  - Task 3: `ICUI.gm_scroll.picker`, `ICUI.GM_ROW_ART.inactive`, `ICUI.GM_PAGE_TITLE`, `gm_row(panel, i)`.
  - Task 4: `ICUI.gm_open_picker(province)`, `ICUI.gm_held`, `ICUI.gm_enable`, and the button block's locals `btns`, `ok_on`, `no_on`, `no_shown`, `ok_tip`, `no_tip`.
- Produces (panel Lua):
  - `ICUI.picker_lines(faction, court) -> lines`. It fills `ICUI.pick_rows` in parallel.
  - Each line also carries `why` (the refusal word, unreddened; nil when he may be chosen) and `holds` (what he holds, or "None").
- Produces (map Lua):
  - `ICUI.gm_live_page() -> "parties" | "provinces" | "picker"`;
  - `ICUI.gm_pick_sel`, the chosen man's cqi or nil;
  - `ICUI.gm_picker_rows(faction) -> rows`. Each row carries `key` (his cqi, always) and `cqi` (his cqi if he may be chosen, else nil).

**Ruling 16 (ledger it):** `ICUI.gm_on()` stops asking about `ICUI.pick`.
- Every picker other than the governor's is opened from the Court or Intrigue tabs (`zzz_derpy_iron_court_ui.lua` lines 6380-7053, read 2026-09-30).
- A tab click clears `ICUI.pick`, so on the Governors view a picker is always the governor's.
- Task 2's mutant "the Governors view drawn under a picker" is deleted with the test it mutated.

- [ ] **Step 1: Snapshot** the four files to the scratchpad as `*_before_govmap_t5.*`.

- [ ] **Step 2: Invert Task 2's pin check**

In "a pin opens the governor picker for its province, and a lost province redraws instead", replace

```lua
        -- PHASE 0: the court's own picker, over its own backdrop (plan ruling 4).
        assert(panel.images[0] == ICUI.GM_BACKDROP and panel.interactive == true,
            "the picker opened over a see-through panel")
```

with

```lua
        -- IN THE COLUMN, ON THE MAP (spec section 3; Task 5 ends plan ruling 4).
        assert(panel.images[0] == ICUI.MASK_NONE and panel.interactive == false,
            "the picker put the backdrop back over the map")
```

- [ ] **Step 3: Write the failing checks**

Add above `check("no parties' turn failed anywhere in the run"`:

```lua
-- THE PICKER PAGE'S ROW FOR A MAN, whichever slot the sort put him in.
local function gm_pick_row(panel, cqi)
    for i = 1, ICUI.GM_ROWS do
        local r = ICUI.gm_rows[i]
        if r and r.key == cqi then return gm_row(panel, i), r end
    end
    return nil
end

check("a pin opens the governor picker in the column, over the map, with the court's own men", function()
    IC.state = {}
    local free = make_character(3401, ANY_SEAT, "legion")
    local busy = make_character(3402, ANY_SEAT, "legion")
    local bare = make_character(3403, ANY_SEAT, "legion")
    make_faction(F, IC.CHD_SUBCULTURE, {free, busy, bare}, {"prov_a", "prov_b"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    IC.court(F).govs["prov_b"] = 3402
    IC_TEST_PORTRAITS = {["3401"] = "ui/portraits/portholes/chd/free.png"}
    with_fake_govmap(function(hud, panel, extra, holder)
        ICUI.view = "govs"
        ICUI.pick = nil
        ICUI.open()
        map_click(ICUI.GM_PIN .. "_1")
        assert(ICUI.gm_live_page() == "picker", "the pin opened " .. ICUI.gm_live_page())
        assert(panel.children.ic_gm_head.text == ICUI.GM_PAGE_TITLE.picker, "the head reads " .. panel.children.ic_gm_head.text)
        -- THE QUESTION, NAMING THE PROVINCE (spec section 3), on the section line.
        assert((panel.children.ic_lbl_section.text or ""):find("Choose who governs prov_a", 1, true),
            "the section line reads " .. tostring(panel.children.ic_lbl_section.text))
        -- NOT THE COURT'S FULL-SCREEN LIST.
        assert(not panel.children[ICUI.ROW .. "_1"].visible, "the court's own picker shows over the map")
        -- THE PROVINCE BEING CHOSEN FOR is ringed on the map.
        assert(gm_pin(holder, 1).images[ICUI.GP_OUTLINE] == ICUI.MK_RING_OUTLINE, "the province being chosen for is not ringed")
        -- A FREE MAN: his face, his party, his rank and influence.
        local row = gm_pick_row(panel, 3401)
        assert(row and row.visible, "the free man has no card")
        assert(row.children.ic_gr_l1.text:find(ICUI.character_name(free), 1, true), "his card reads " .. row.children.ic_gr_l1.text)
        assert(row.children.ic_gr_l2.text == ICUI.house_name("legion", F), "his party reads " .. row.children.ic_gr_l2.text)
        assert(row.children.ic_gr_l3.text == string.format("Rank %d, %d influence", free:rank(), IC.standing(F, 3401)),
            "his last line reads " .. row.children.ic_gr_l3.text)
        assert(row.children.ic_gr_face.images[ICUI.FACE_INDEX] == "ui/portraits/portholes/chd/free.png", "his card has no face")
        assert(row.children.ic_gr_badge.visible and row.children.ic_gr_badge.images[0] == ICUI.crest("legion"), "his face wears no crest")
        assert(row.images[0] == ICUI.GM_ROW_ART.live[1], "a free man's card does not look live")
        -- A MAN WITH NO FACE: his party's crest in its place.
        local plain = gm_pick_row(panel, 3403)
        assert(plain and plain.children.ic_gr_crest.visible and plain.children.ic_gr_crest.images[0] == ICUI.crest("legion"),
            "a man with no face has no crest in its place")
        -- A BUSY MAN: drawn inactive, the reason first, and not choosable.
        local held, r = gm_pick_row(panel, 3402)
        assert(held and held.images[0] == ICUI.GM_ROW_ART.inactive[1], "a busy man's card does not look inactive")
        assert(held.tooltip:find("^Busy%.") , "a busy man's tooltip does not open with why: " .. held.tooltip)
        assert(held.tooltip:find(IC.standing(F, 3402) .. " influence. Holds: prov_b.", 1, true),
            "a busy man's tooltip does not carry his influence and what he holds: " .. held.tooltip)
        for i = 1, ICUI.GM_ROWS do
            if ICUI.gm_rows[i] == r then map_click(ICUI.GM_ROW .. "_" .. i) end
        end
        assert(ICUI.gm_pick_sel == nil, "a busy man was chosen")
    end)
    IC_TEST_PORTRAITS = nil
end)

check("the check appoints the chosen man, and the answer returns to the page the picker came from", function()
    for _, from in ipairs({"provinces", "parties"}) do
        IC.state = {}
        local man = make_character(3411, ANY_SEAT, "legion")
        make_faction(F, IC.CHD_SUBCULTURE, {man}, {"prov_a", "prov_b"})
        IC.add_house(F, IC.CROWN)
        IC.add_house(F, "legion")
        with_fake_govmap(function(hud, panel, extra, holder)
            ICUI.view = "govs"
            ICUI.pick = nil
            ICUI.open()
            if from == "parties" then map_click("ic_gm_tog_1") end
            map_click(ICUI.GM_PIN .. "_2")
            local ok_b = panel.children.ic_gm_ok
            assert(ok_b.visible and ok_b.disabled == true, from .. ": the check is live with no man chosen")
            assert(panel.children.ic_gm_no.visible and panel.children.ic_gm_no.disabled == false,
                from .. ": the cross cannot go back")
            map_click("ic_gm_ok")
            assert(IC.court(F).govs.prov_b == nil, from .. ": a dead check appointed someone")
            local row = gm_pick_row(panel, 3411)
            for i = 1, ICUI.GM_ROWS do
                if gm_row(panel, i) == row then map_click(ICUI.GM_ROW .. "_" .. i) end
            end
            assert(ICUI.gm_pick_sel == 3411, from .. ": the card chose " .. tostring(ICUI.gm_pick_sel))
            assert(row.images[0] == ICUI.GM_ROW_ART.selected[1], from .. ": the chosen card does not look chosen")
            assert(ok_b.disabled == false, from .. ": the check is dead with a man chosen")
            map_click("ic_gm_ok")
            assert(IC.court(F).govs.prov_b == 3411, from .. ": the check did not appoint him")
            assert(ICUI.pick == nil and ICUI.gm_live_page() == from,
                from .. ": the answer landed on " .. ICUI.gm_live_page())
            assert(panel.images[0] == ICUI.MASK_NONE, from .. ": the answer put the backdrop back")
            -- THE PIN REDRAWN in the new governor's party colour (spec section 3).
            assert(gm_pin(holder, 2).images[ICUI.GP_PARTY] == ICUI.gm_ring_path("legion"),
                from .. ": the pin still wears " .. tostring(gm_pin(holder, 2).images[ICUI.GP_PARTY]))
        end)
    end
end)

check("the cross, a toggle and a tab each abandon the picker", function()
    IC.state = {}
    make_faction(F, IC.CHD_SUBCULTURE, {make_character(3421, ANY_SEAT, "legion")}, {"prov_a"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    with_fake_govmap(function(hud, panel, extra, holder)
        ICUI.view = "govs"
        ICUI.pick = nil
        ICUI.open()
        map_click(ICUI.GM_PIN .. "_1")
        map_click("ic_gm_no")
        assert(ICUI.pick == nil and ICUI.gm_live_page() == "provinces", "the cross left " .. ICUI.gm_live_page())
        assert(IC.court(F).govs.prov_a == nil, "the cross appointed someone")
        map_click(ICUI.GM_PIN .. "_1")
        map_click("ic_gm_tog_1")
        assert(ICUI.pick == nil and ICUI.gm_live_page() == "parties", "the toggle left " .. ICUI.gm_live_page())
        map_click(ICUI.GM_PIN .. "_1")
        map_click("ic_tab_offices")
        assert(ICUI.pick == nil and ICUI.view == "offices", "the tab left the picker up")
        assert(panel.images[0] == ICUI.GM_BACKDROP and panel.interactive == true, "the tab left the map showing")
    end)
end)

check("a man who stops being free, or a province lost, between the draw and the check appoints nobody", function()
    IC.state = {}
    local man = make_character(3431, ANY_SEAT, "legion")
    make_faction(F, IC.CHD_SUBCULTURE, {man}, {"prov_a", "prov_b"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    with_fake_govmap(function(hud, panel, extra, holder)
        ICUI.view = "govs"
        ICUI.pick = nil
        ICUI.open()
        map_click(ICUI.GM_PIN .. "_1")
        map_click(ICUI.GM_ROW .. "_1")
        assert(ICUI.gm_pick_sel == 3431, "the fixture chose nobody")
        -- HE TAKES prov_b behind the panel's back.
        IC.court(F).govs.prov_b = 3431
        map_click("ic_gm_ok")
        assert(IC.court(F).govs.prov_a == nil, "a man no longer free was appointed")
        assert(ICUI.gm_pick_sel == nil and ICUI.gm_live_page() == "picker", "the stale choice was kept, or the picker shut")
        IC.court(F).govs.prov_b = nil
        ICUI.refresh()
        map_click(ICUI.GM_ROW .. "_1")
        -- prov_a FALLS between the draw and the click.
        make_faction(F, IC.CHD_SUBCULTURE, {man}, {"prov_b"})
        map_click("ic_gm_ok")
        assert(IC.court(F).govs.prov_a == nil, "a lost province was given a governor")
        assert(ICUI.pick == nil, "the picker stayed up for a province no longer held")
    end)
end)

check("a picker with more men than cards pages, and a new pin opens it on page one with nobody chosen", function()
    IC.state = {}
    local men = {}
    for i = 1, ICUI.GM_ROWS + 2 do men[i] = make_character(3440 + i, ANY_SEAT, "legion") end
    make_faction(F, IC.CHD_SUBCULTURE, men, {"prov_a", "prov_b"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    with_fake_govmap(function(hud, panel, extra, holder)
        ICUI.view = "govs"
        ICUI.pick = nil
        ICUI.open()
        map_click(ICUI.GM_PIN .. "_1")
        assert(panel.children.ic_gm_page.text == "Page 1 of 2", panel.children.ic_gm_page.text)
        map_click("ic_gm_next")
        -- ITS OWN PAGE COUNT: the Provinces page under it has one page.
        assert(panel.children.ic_gm_page.text == "Page 2 of 2", "next landed on " .. panel.children.ic_gm_page.text)
        map_click(ICUI.GM_ROW .. "_1")
        assert(ICUI.gm_pick_sel ~= nil, "page two's first card chose nobody")
        map_click(ICUI.GM_PIN .. "_2")
        assert(ICUI.pick.key == "prov_b", "the second pin opened " .. tostring(ICUI.pick.key))
        assert(panel.children.ic_gm_page.text == "Page 1 of 2", "a new pin opened on " .. panel.children.ic_gm_page.text)
        assert(ICUI.gm_pick_sel == nil, "a new pin kept the last man chosen")
    end)
end)

check("the column's check sends its appointment in multiplayer and waits for the trigger", function()
    IC.state = {}
    turn = 1
    local f = make_faction(F, IC.CHD_SUBCULTURE, {make_character(3461, ANY_SEAT, "legion")}, {"prov_a"})
    f._cqi = 41
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    cm.get_human_factions = function() return {F} end
    IC.register()
    local ran, was = 0, IC.assign_governor
    IC.assign_governor = function() ran = ran + 1 return true end
    local ok, err = pcall(with_fake_govmap, function(hud, panel, extra, holder)
        ICUI.view = "govs"
        ICUI.pick = nil
        ICUI.open()
        map_click(ICUI.GM_PIN .. "_1")
        map_click(ICUI.GM_ROW .. "_1")
        with_mp(F, function(sent)
            map_click("ic_gm_ok")
            assert(ran == 0, "the check appointed before its trigger came back")
            assert(ICUI.pick, "the picker shut before the answer came")
            assert(#sent == 1, "the check sent " .. #sent .. " triggers")
            deliver(sent[1])
            assert(ran == 1, "the check's trigger reached the model " .. ran .. " times")
            assert(ICUI.pick == nil, "the picker stayed up after its answer")
        end)
    end)
    IC.assign_governor = was
    cm.get_human_factions = function() return {} end
    assert(ok, err)
end)
```

- [ ] **Step 4: Run the harness and verify that it fails**

Run: `IC_TEST_ALL=1 "/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | grep "^FAIL"`

Expected:
- the six new checks fail;
- the inverted pin check fails;

- [ ] **Step 5: Extract `ICUI.picker_lines`**

In `zzz_derpy_iron_court_ui.lua`, replace the head of `ICUI.draw_picker`

```lua
function ICUI.draw_picker(panel, faction, court)
    local lines = {}
    ICUI.pick_rows = {}
    -- THE MISSION PICKERS draw places and factions, not men (spec 2026-09-29).
    if ICUI.MISSION_PICKS[ICUI.pick.kind] then
        local rows, keys = ICUI.mission_rows(faction)
        ICUI.pick_rows = keys
        if #rows == 0 then rows[1] = {"Nowhere to send.", "", "", "", ""} end
        ICUI.fill_rows(panel, rows, "pick")
        return ""
    end
```

with

```lua
function ICUI.draw_picker(panel, faction, court)
    -- THE MISSION PICKERS draw places and factions, not men (spec 2026-09-29).
    if ICUI.MISSION_PICKS[ICUI.pick.kind] then
        local rows, keys = ICUI.mission_rows(faction)
        ICUI.pick_rows = keys
        if #rows == 0 then rows[1] = {"Nowhere to send.", "", "", "", ""} end
        ICUI.fill_rows(panel, rows, "pick")
        return ""
    end
    local lines = ICUI.picker_lines(faction, court)
    if #lines == 0 then
        lines[1] = {"No characters in this faction.", "", "", "", ""}
    end
    ICUI.fill_rows(panel, lines, "pick")
    return ""
end

-- THE MEN A CHARACTER PICKER LISTS, one line each, with ICUI.pick_rows filled
-- beside them. The full-screen picker draws these and so does the Governors
-- column (plan 2026-09-30 Task 5), so who may be chosen is decided once.
function ICUI.picker_lines(faction, court)
    local lines = {}
    ICUI.pick_rows = {}
```

Replace its tail

```lua
    ICUI.sort_rows("pick", lines, ICUI.pick_rows, #lines)

    if #lines == 0 then
        lines[1] = {"No characters in this faction.", "", "", "", ""}
    end
    ICUI.fill_rows(panel, lines, "pick")
    return ""
end
```

with

```lua
    ICUI.sort_rows("pick", lines, ICUI.pick_rows, #lines)
    return lines
end
```

Replace

```lua
        lines[#lines].sort.ready = ICUI.pick_rows[#lines] ~= nil
        if not roster and not ICUI.pick_rows[#lines] then
```

with

```lua
        lines[#lines].sort.ready = ICUI.pick_rows[#lines] ~= nil
        -- THE REFUSAL IN WORDS, before it is reddened, and what he holds: the
        -- Governors column's tooltip opens with both.
        lines[#lines].why = (not ICUI.pick_rows[#lines]) and action or nil
        lines[#lines].holds = holds
        if not roster and not ICUI.pick_rows[#lines] then
```

Run: `"/c/Program Files (x86)/Lua/5.1/luac.exe" -p "Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua"`
Expected: exit 0.

Then run `py tools/mutate_iron_court.py --selftest`. Any mutant whose anchor was the old head or tail of `draw_picker` is now stale: re-aim it at the same text in its new place.

- [ ] **Step 6: The picker page in the map Lua**

Replace `ICUI.gm_on`'s body with:

```lua
    -- EVERY OTHER PICKER opens from the Court or Intrigue tabs, and a tab
    -- clears ICUI.pick: on this view a picker is always the governor's, and it
    -- is drawn in the column (plan ruling 16).
    return (comp(ICUI.PANEL) and ICUI.view == "govs") and true or false
```

Also:
- change its comment line to `-- THE VIEW IS UP: the court open on its Governors tab.`;
- delete Task 2's mutant "the Governors view drawn under a picker".

In `ICUI.GM_PAGE_TITLE`, add `picker = "Candidates"`. It is the page's name. The question, naming the province, is the section line's, so the province is written once.

In `zzz_derpy_iron_court_ui.lua`'s `ICUI.pick_title`, change the governor picker's line from `"Choose an overseer for %s"` to `"Choose who governs %s"`, which is spec section 3's heading. Nothing else reads the old wording (grep, 2026-09-30).

In `ICUI.gm_open_picker`, before `ICUI.refresh()`, add:

```lua
    ICUI.gm_scroll.picker = 0
    ICUI.gm_pick_sel = nil
```

After `ICUI.gm_open_picker`, add:

```lua
ICUI.gm_pick_sel = nil               -- the chosen man on the picker page

-- THE PAGE ON SCREEN: the picker while one is up, else the page chosen.
function ICUI.gm_live_page()
    if ICUI.pick and ICUI.pick.kind == "gov" then return "picker" end
    return ICUI.gm_page
end

-- THE PICKER PAGE: the court's own governor picker, as cards (spec section 3).
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
```

In `ICUI.gm_draw_page` and in `ICUI.gm_step`, replace `local page = ICUI.gm_page` with `local page = ICUI.gm_live_page()`. That gives the picker its own page count.

In `ICUI.gm_draw_column`:
1. Replace `local page = ICUI.gm_page` with `local page = ICUI.gm_live_page()`.
2. Before the Provinces branch's opening lines,

   ```lua
       else
           show(hint, false)
           local rows, keys = ICUI.gm_province_rows(faction)
   ```

   insert:

   ```lua
       elseif page == "picker" then
           local rows = ICUI.gm_picker_rows(faction)
           if not pick_still_free(rows) then ICUI.gm_pick_sel = nil end
           ICUI.gm_draw_page(panel, rows, function(r)
               return r.cqi ~= nil and r.cqi == ICUI.gm_pick_sel
           end)
           show(hint, #rows == 0)
           if #rows == 0 then set_text(hint, "No characters in this faction.") end
   ```

3. After `local no_tip = "Release the chosen province's governor."`, add:

   ```lua
       if page == "picker" then
           -- THE PICKER'S: appoint the chosen man, or go back without one.
           btns, ok_on, no_on, no_shown = true, ICUI.gm_pick_sel ~= nil, true, true
           ok_tip, no_tip = "Appoint the chosen man.", "Go back without choosing."
       end
   ```

The toggles light the page on screen, so neither is lit while the picker is up. A toggle is also how the player leaves the picker (`gm_to_page` clears `ICUI.pick`).

In `ICUI.gm_ring`:
1. Add `local page = ICUI.gm_live_page()` as its first line.
2. Change `ICUI.gm_page == "parties"` and `ICUI.gm_page == "provinces"` to `page == "parties"` and `page == "provinces"`.
3. After them, add:

   ```lua
       if page == "picker" then ringed[ICUI.pick.key] = true end
   ```

Re-aim the two gm_ring mutants from Tasks 3 and 4 at the `page ==` lines.

In `ICUI.gm_row_click`, after `if not ICUI.gm_on() then return end`, add:

```lua
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
```

In `ICUI.gm_ok`, after `local faction = ICUI.player()`, add:

```lua
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
```

In `ICUI.gm_no`, after `local faction = ICUI.player()`, add:

```lua
    if ICUI.gm_live_page() == "picker" then
        -- BACK TO THE PAGE IT CAME FROM, with nothing done.
        ICUI.pick = nil
        ICUI.scroll.pick = 0
        ICUI.notice = nil
        ICUI.refresh()
        return
    end
```

In `ICUI.gm_sort_click`, replace `ICUI.gm_page ~= "provinces"` with `ICUI.gm_live_page() ~= "provinces"`. A hidden cell still reports a click.

- [ ] **Step 7: Generate and run the harness**

Run: `py tools/gen_ic_ui.py && IC_TEST_ALL=1 "/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | tail -4`
Expected: `ok (N checks)`, with the six new checks counted in. Every existing picker check passes unchanged, because the extraction changed no line the full-screen picker draws.

- [ ] **Step 8: Mutants**

Run `py tools/mutate_iron_court.py --selftest`, then append:

```python
    # THE PICKER IN THE COLUMN (plan 2026-09-30 Task 5).
    ("the governor picker drawn full-screen again", UM,
     """    if ICUI.pick and ICUI.pick.kind == "gov" then return "picker" end
    return ICUI.gm_page""",
     """    return ICUI.gm_page"""),
    ("a man the click refuses drawn live", UM,
     """            look = ICUI.pick_rows[i] and "live" or "inactive",""",
     """            look = "live","""),
    ("the refusal not first on the tooltip", UM,
     """        if line.why then tip[#tip + 1] = line.why .. "." end""",
     """        if false then tip[#tip + 1] = line.why .. "." end"""),
    ("what he holds left off the tooltip", UM,
     '        tip[#tip + 1] = string.format("%d influence. Holds: %s.", line.sort.standing, line.holds)',
     '        local _ = line.holds'),
    ("a refused man choosable", UM,
     """        if r and r.cqi then
            ICUI.gm_pick_sel = (ICUI.gm_pick_sel ~= r.cqi) and r.cqi or nil""",
     """        if r and r.key then
            ICUI.gm_pick_sel = (ICUI.gm_pick_sel ~= r.key) and r.key or nil"""),
    ("the check live with no man chosen", UM,
     """        btns, ok_on, no_on, no_shown = true, ICUI.gm_pick_sel ~= nil, true, true""",
     """        btns, ok_on, no_on, no_shown = true, true, true, true"""),
    ("the picker's cross dead", UM,
     """        btns, ok_on, no_on, no_shown = true, ICUI.gm_pick_sel ~= nil, true, true""",
     """        btns, ok_on, no_on, no_shown = true, ICUI.gm_pick_sel ~= nil, false, true"""),
    ("the check appoints a man no longer free", UM,
     """        if not pick_still_free(ICUI.gm_picker_rows(faction)) then""",
     """        if false then"""),
    ("the check gives a lost province a governor", UM,
     """        if not ICUI.gm_held(faction, province) then
            ICUI.pick = nil""",
     """        if false then
            ICUI.pick = nil"""),
    ("a stale choice drawn as chosen", UM,
     """        if not pick_still_free(rows) then ICUI.gm_pick_sel = nil end""",
     """        if false then ICUI.gm_pick_sel = nil end"""),
    ("the picker's cross leaves the picker up", UM,
     """        -- BACK TO THE PAGE IT CAME FROM, with nothing done.
        ICUI.pick = nil""",
     """        -- BACK TO THE PAGE IT CAME FROM, with nothing done.
        local _ = ICUI.pick"""),
    ("a new pin keeps the last man chosen", UM,
     """    ICUI.gm_scroll.picker = 0
    ICUI.gm_pick_sel = nil""",
     """    ICUI.gm_scroll.picker = 0"""),
    ("a new pin opens on the last picker's page", UM,
     """    ICUI.gm_scroll.picker = 0
    ICUI.gm_pick_sel = nil""",
     """    ICUI.gm_pick_sel = nil"""),
    ("the province being chosen for not ringed", UM,
     """    if page == "picker" then ringed[ICUI.pick.key] = true end""",
     """    if false then ringed[ICUI.pick.key] = true end"""),
    ("the picker shares the Provinces page's scroll", UM,
     """    local page = ICUI.gm_live_page()
    local pages = math.max(1, math.ceil(#rows / ICUI.GM_ROWS))""",
     """    local page = ICUI.gm_page
    local pages = math.max(1, math.ceil(#rows / ICUI.GM_ROWS))"""),
```

Append these inside the existing mutant list, before its closing `]`.

Run them by name. Expected: `15 mutants, 0 unexplained`. Then run `py tools/gen_ic_ui.py`.

- [ ] **Step 9: Gates.** Every gate, with its expected result:

| Gate | Expected |
|---|---|
| `py tools/gen_ic_ui.py --check` | no drift |
| `py tools/gen_ic_ui.py --selftest` | ok. Run it in the background with a 600s wait loop; it outlasts the tool timeout. |
| `py tools/preview_iron_court.py --check` | ok |
| `luac -p` on the Iron Court UI and map Lua files (the UI file changed: `picker_lines`) | parses |
| `py tools/check_lua_api.py` on the same files | 0 suspects |
| `py tools/check_lua_literal_left.py` | 0 sites |
| `py tools/check_lua_undeclared.py` | clean |
| `py tools/import_iron_court.py` | `verify ok` |
| the harness | `ok (N checks)` |

- [ ] **Step 10: Build and deploy**
  1. Start RPFM's server headless if `http://127.0.0.1:45127/sessions` does not answer: `Start-Process "G:\Modding for resources\RPFM\rpfm_server.exe" -WindowStyle Hidden`.
  2. Run `py tools/deploy_iron_court.py`. Expected:
     - it builds, verifies and prints the build name (the first 8 hex digits of its MD5);
     - if `Warhammer3.exe` is not running, it deploys to data/.
  3. Stop the server.
  4. Ledger `Task 5: complete (tests: harness -> ok (N checks); build <NAME> deployed)`.

---

### Task 6: Remove the old party map, the Map tab and the Governors list

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua`
  - the tab cells and the Map tab's label;
  - `ICUI.SECTION.govs`;
  - the Governors Help topic;
  - `ICUI.gov_keys`, `ICUI.draw_govs`, `ICUI.gov_row`;
  - the Governors branch of `ICUI.on_row_action`;
  - the governor burst in `picked`.
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui_map.lua`: everything of the old map is deleted.
- Modify: `tools/gen_ic_ui.py`: the map layer file, the marker file, the Map tab and `check_map` are deleted.
- Modify: `tools/preview_iron_court.py`: the old map picture and the old Governors list picture are deleted. Task 7 draws the new one.
- Modify: `tools/sync_iron_court_repo.py`: the published file list.
- Modify: `tools/_iron_court_harness.lua`: the old map's fixture, and its checks migrated or deleted.
- Modify: `tools/mutate_iron_court.py`
- Delete: `Modding Files/pack/ui/campaign ui/derpy_ic_map.twui.xml` and `Modding Files/pack/ui/campaign ui/derpy_ic_map_marker.twui.xml`

**Interfaces:**
- Consumes: everything Tasks 2-5 produced.
- It deletes nothing they use. What survives of the old map file:
  - `ICUI.MK_RING_CAPITAL` and `ICUI.MK_RING_OUTLINE`;
  - `ICUI.map_region`, `ICUI.map_rows`, `ICUI.map_outline` and `ICUI.map_tip`;
  - the `ic_map_click` listener, which keeps its name (the harness's `map_click` fires it) and carries only the `ic_gm_*` branches;
  - `leave_on_select` and its two selection listeners.
- The generator keeps `MAP_PIN`, `MAP_RING`, `MAP_RING_CAPITAL(_COLOUR)`, `MAP_RING_OUTLINE(_COLOUR)`, `_map_supersample`, `map_ring_pixels` and `_lua_map_tables`: the pin and the ring PNGs use them.
- Produces: nothing new.

- [ ] **Step 1: Snapshot** every file this task edits, and the two `.twui.xml` files it deletes, to the scratchpad as `*_before_govmap_t6.*`.

- [ ] **Step 2: Write the failing checks**

Add above `check("no parties' turn failed anywhere in the run"`:

```lua
check("the tab strip has no Map tab and no gap where it stood", function()
    assert(ICUI.PANEL_XY.ic_tab_map == nil, "PANEL_XY still places a Map tab")
    local tabs = {}
    for id in pairs(ICUI.TAB_VIEW) do tabs[#tabs + 1] = ICUI.PANEL_XY[id] end
    table.sort(tabs, function(a, b) return a[1] < b[1] end)
    local first = tabs[2][1] - (tabs[1][1] + tabs[1][3])
    for i = 2, #tabs do
        local gap = tabs[i][1] - (tabs[i - 1][1] + tabs[i - 1][3])
        assert(gap == first, string.format("a %dpx gap before the tab at x %d, where the rest have %d",
                                           gap, tabs[i][1], first))
    end
    -- EVERY ATTENTION MARKER ON ITS OWN TAB'S RIGHT-HAND SKULL, 34px in from its end.
    for view, mark in pairs(ICUI.MARKS) do
        local tab, m = ICUI.PANEL_XY["ic_tab_" .. view], ICUI.PANEL_XY[mark]
        assert(m[1] == tab[1] + tab[3] - 34, mark .. " is not on its tab's skull")
    end
end)

check("the Help tells the player how to choose a governor on the map", function()
    local found = false
    for _, topic in ipairs(ICUI.HELP) do
        for _, line in ipairs(topic.lines) do
            if line:find("pin", 1, true) and line:find("Governors tab", 1, true) then found = true end
        end
    end
    assert(found, "no Help line says how the Governors tab's map is used")
end)

check("the old party map is gone: no layer, no marker file, no listener of its own", function()
    assert(ICUI.map_open == nil and ICUI.MAP == nil and ICUI.PATH_MARKER == nil,
        "the old map's code is still loaded")
    for _, n in ipairs({"derpy_ic_map.twui.xml", "derpy_ic_map_marker.twui.xml"}) do
        local f = io.open("Modding Files/pack/ui/campaign ui/" .. n, "rb")
        if f then f:close() end
        assert(f == nil, n .. " is still in the pack's folder, and the build would ship it")
    end
    assert(core.listeners["ic_map_turn_end"] == nil, "the old map's turn-end listener is still registered")
end)

check("ending the turn on the Governors view closes the court, pins and all, and a reopen starts afresh",
function()
    IC.state = {}
    local f = make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a", "prov_b"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    with_fake_govmap(function(hud, panel, extra, holder)
        ICUI.view = "govs"
        ICUI.pick = nil
        ICUI.open()
        map_click("ic_gm_tog_1")
        map_click(ICUI.GM_ROW .. "_1")
        assert(ICUI.gm_party == 1, "the fixture chose no party")
        core.listeners["ic_turn_end"]({faction = function() return f end})
        assert(panel.destroyed, "the turn ended with the court up over the map")
        assert(hud.visible == true, "the turn ended with the HUD still hidden")
        assert(ICUI.gm_was_on == false, "the closed court still counts the view as up")
        ICUI.open()
        assert(ICUI.gm_party == nil, "a reopen after the turn kept the last choice")
    end)
end)
```

- [ ] **Step 3: Run the harness and verify that it fails**

Run: `IC_TEST_ALL=1 "/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | grep "^FAIL"`

Expected:
- the tab-strip check fails on "PANEL_XY still places a Map tab";
- the Help check fails;
- the old-map check fails;
- the turn-end check passes already. It holds the court's own `ic_turn_end`, which does not change, and it becomes the old map turn-end check's successor in Step 7.

- [ ] **Step 4: The generator**

In `tools/gen_ic_ui.py`:
1. **GUID prefixes.** In `GUID_PREFIXES`, delete the `derpy_ic_map.twui.xml` (IC45) and `derpy_ic_map_marker.twui.xml` (IC46) entries. In their place, leave the comment `# IC45 and IC46 were the old party map's, retired 2026-09-30. Never reuse a prefix: a stale file in a player's data/ would collide.`
2. **The tabs.** In `PANEL_LAYOUT`, delete `"ic_tab_map"` and the two comment lines above it. Then:
   - `"ic_tab_intrigue": (750, 62, 240, 32)`;
   - `"ic_tab_petitions": (994, 62, 240, 32)`;
   - `"ic_tab_log": (1238, 62, 240, 32)`;
   - `"ic_mark_petitions": (994 + 240 - 34, 64, 28, 28)`.
3. **The tab's label.** Delete the line `_bar["ic_tab_map"] = ["Map"]`.
4. **The map section.**
   - Delete: `MAP_FILE`, `MARKER_FILE`, `MAP_DISC`, `MAP_CREST`, `MAP_NAME_W`, `MAP_NAME_H`, `MARKER_W`, `MARKER_H`, `MAP_DISC_NONE`, `MAP_LAYOUT`, `MAP_ROW_X/Y/W/H`, `MAP_ROWS`, `MAP_ROW_CHILD`, both `LAYOUT_TABLES[...]` lines for the two files, `map_disc_path`, `map_disc_pixels`, `_map_layer`, `MARKER_LAYERS`, `_map_marker`, `_map_layer_file`, `map_xml`, `marker_xml` and `check_map`.
   - Keep: `MAP_RING`, `MAP_RING_CAPITAL`, `MAP_RING_OUTLINE`, both `*_COLOUR`s, `MAP_PIN`, `_map_supersample`, `map_ring_pixels` and `_lua_map_tables`.
   - Rewrite the section's head comment:

     ```python
     # ---------------------------------------------------------------------------
     # WHAT THE GOVERNORS MAP BORROWED FROM THE PARTY MAP IT REPLACED (plan
     # 2026-09-30 Task 6): CA's world-space pin, and the two rings the pins wear.
     ```
5. **The old rail.** Delete `PARTY_SEL_RAIL` and its comment. `check_map` was its only reader.
6. **The discs.** In `build_plates`, delete the three `map_disc_path` lines. `write_plates()` then prunes the old `map_disc_*.png` files by itself.
7. **Classification.** In `NOT_GEOMETRY`, delete every name step 4 or step 5 deleted. `_classify` then fails on any that remain.
8. **The file lists.** In `ui_file_names`, drop `MAP_FILE, MARKER_FILE`. In `build_xml`, delete the two lines that write them.
9. **The checks.** In `check()`, delete the `check_map()` call. In `selftest()`, delete every negative that calls `check_map`.
10. **Stray references.** Run `grep -n -E "check_map|MAP_FILE|MARKER|map_disc|MAP_LAYOUT|MAP_ROW|PARTY_SEL_RAIL|ic_tab_map" tools/gen_ic_ui.py`.
    - Expected: only comments that name the retired prefixes.
    - Re-point any other comment that cites `check_map` at `check_gm`, or delete it.

Then look at, and delete, the two old files:

```bash
ls -l "Modding Files/pack/ui/campaign ui/derpy_ic_map.twui.xml" "Modding Files/pack/ui/campaign ui/derpy_ic_map_marker.twui.xml"
rm "Modding Files/pack/ui/campaign ui/derpy_ic_map.twui.xml" "Modding Files/pack/ui/campaign ui/derpy_ic_map_marker.twui.xml"
```

`deploy_iron_court.py` builds a fresh pack from the folder, so a file left on disk is a file shipped.

- [ ] **Step 5: The panel Lua**

In `zzz_derpy_iron_court_ui.lua`:
1. **The tabs.** In `ICUI.PANEL_XY`:
   - delete `ic_tab_map       = {750, 62, 240, 32},`;
   - set `ic_tab_intrigue  = {750, 62, 240, 32},`, `ic_tab_petitions = {994, 62, 240, 32},` and `ic_tab_log       = {1238, 62, 240, 32},`;
   - set `ic_mark_petitions = {1200, 64, 28, 28},`.
2. **The label.** Delete `    set_text(comp("ic_tab_map", panel), "Map")`.
3. **The section label.** Replace `ICUI.SECTION.govs`'s string with `"Your provinces on the map, and who governs each"`.
4. **Help.** In the Governors Help topic, after its first line, add:

   ```lua
           "{@province}On the Governors tab the court opens onto the map. Click a province's pin to choose its governor, or choose it in the list and click the check.",
   ```

   That makes 12 lines, which is `ICUI.HELP_SLOTS`. If the Help's own fit checks refuse the line, shorten it; never drop a line to make room.
5. **The old list's remnants.** Delete:
   - `ICUI.gov_keys = {}` and its comment;
   - the Task 2 stub `ICUI.draw_govs`;
   - `ICUI.gov_row` and its comment.
6. **The view dispatch.** In `ICUI.refresh`'s dispatch, replace

   ```lua
           elseif view == "govs" then
               warn = ICUI.draw_govs(panel, faction, court)
   ```

   with

   ```lua
           elseif view == "govs" then
               -- THE LIVE MAP, drawn by zzz_derpy_iron_court_ui_map.lua once this
               -- has run (ICUI.gm_sync).
               warn = ""
   ```

7. **The row action.** In `ICUI.on_row_action`, delete its Governors branch: from `    if ICUI.view ~= "govs" then return end` through the `    ICUI.refresh()` before the function's closing `end`. The function then ends after its Petitions branch.
8. **`picked`.** Replace

   ```lua
           local filled, governed = nil, nil
           if op == "appoint" then filled = string.match(arg or "", "^([^|]*)") end
           if op == "gov" then governed = string.match(arg or "", "^([^|]*)") end
   ```

   with

   ```lua
           local filled = nil
           if op == "appoint" then filled = string.match(arg or "", "^([^|]*)") end
   ```

   Then:
   - delete the `local filled_row = nil` block with its three comment lines and its `if governed then ... end`;
   - delete the `elseif filled_row then` branch, which is its two lines;
   - in the comment `found after a redraw like a governor's row`, delete `like a governor's row`.

   A governor's answer then plays through `ICUI.confirm`, as Task 2's deletion table ruled.
9. **Leftover readers.** Run `grep -n -E "gov_keys|gov_row|draw_govs|ic_tab_map" "Modding Files/pack/script/campaign/mod/"*.lua tools/_iron_court_harness.lua`.
   - Expected: no hits.

- [ ] **Step 6: The map Lua**

In `zzz_derpy_iron_court_ui_map.lua`, delete in full:
- the constants `ICUI.MAP`, `PATH_MAP`, `PATH_MARKER`, `MARKER`, `MAP_PINS`, `MARKER_W`, `MAP_TAB`, `MK_PLATE`/`MK_CREST`/`MK_CAPITAL`/`MK_OUTLINE`, `MAP_XY`, `MAP_ROW`, `MAP_ROW_X`..`MAP_ROWS`, `MAP_ROW_CHILD`, `MAP_ROW_SEL` and `map_keys`;
- the `NOT_SCALED` loop over those names (the GM section's own appends stay);
- the functions `map_disc`, `map_layout`, `map_marker`, `map_draw`, `map_ring`, `map_pages`, `map_legend`, `map_marker_click`, `map_close` and `map_open`;
- `ICUI.map_chosen`, `ICUI.map_page` and `ICUI.map_return`;
- the `ICUI.open` wrapper that clears `map_return`;
- the `ICUI.ANSWERS.gov` wrapper;
- in `leave_on_select`, the line `if comp(ICUI.MAP) then ICUI.map_close() end`;
- in the `ic_map_click` listener, the branches for:
  - `ICUI.MAP_TAB`;
  - `ic_map_close`;
  - `ICUI.MAP_ROW`;
  - `ICUI.MARKER`;
  - `ic_close` with `map_return`;
  - `ICUI.TAB_VIEW` with `map_return`;
  - `ic_map_prev`/`ic_map_next`.

  The first branch left becomes `if`.
- the `ic_map_turn_end` listener and its comment.

Replace the file's head comment with:

```lua
-- THE IRON COURT'S GOVERNORS MAP (docs/superpowers/specs/2026-09-30-iron-court-
-- governors-map-design.md).
--
-- On the Governors tab the court clears its backdrop over the LIVE campaign map:
-- a pin and a face per province, pinned to its settlement by CA's own
-- ContextWorldSpaceComponent, and a Chaos Dwarf column of Parties, Provinces
-- and the governor picker on the left. Loads after zzz_derpy_iron_court_ui.lua
-- and wraps it.
```

Then run:

```bash
grep -n -E "ICUI\.(MAP|PATH_MAP|PATH_MARKER|MARKER|MAP_PINS|MARKER_W|MAP_TAB|MK_PLATE|MK_CREST|MK_CAPITAL|MK_OUTLINE|MAP_XY|MAP_ROW[A-Z_]*|map_disc|map_layout|map_marker|map_draw|map_chosen|map_page|map_ring|map_pages|map_legend|map_return|map_marker_click|map_close|map_open)\b" "Modding Files/pack/script/campaign/mod/"*.lua
```

Expected: no hits. Then run `luac -p` on both Lua files: both parse.

- [ ] **Step 7: The harness**

1. **The load check.** Replace `assert(ICUI.map_open, "the party map file must define ICUI.map_open")` with `assert(ICUI.gm_sync, "the Governors map file must define ICUI.gm_sync")`.
2. **The cell list.** In the cell list near line 4419, delete `"ic_tab_map",` and its comment line.
3. **The old fixture.** Delete `with_fake_map` with its comment, and `map_marker` with its comment. Keep `map_click`, and change its comment's "the court's and the map's" to "the court's and the Governors map's".
4. **The old checks.** Migrate or delete each old party-map check:

| Old check (line at planning) | Fate |
|---|---|
| "the Map tab opens the party map: one pinned marker per province, HUD hidden" (~27080) | delete. Successor: Task 2 "the Governors tab pins a pin and a face on each province's settlement" |
| "a province's marker stands on its capital settlement, else the first held one" (~27119) | keep. It tests `map_region`, which the pins use. Rename it "a province's pin stands on its capital settlement, else the first held one" |
| "closing the party map returns to the court on Governors and gives the HUD back" (~27135) | delete: there is no layer to close |
| "the legend lists every party with what it governs and would take" (~27483) | delete. Successor: Task 3 "the Parties page lists every party with what it governs and would take" |
| "choosing a party rings exactly what it would take, and again clears it" (~27512, the one that calls `with_fake_map`) | delete. Successor: Task 3's check of the same name, which calls `with_fake_govmap` |
| "rows that can ring nothing say why: the Crown, secession off, the grace period" (~27542) | keep: it tests `map_outline` |
| "a realm with no province opens an empty map that says so" (~27565) | delete. Successor: Task 3 "a realm with no province says so on the Parties page" |
| "a court with more parties than rows pages its legend" (~27579) | delete. Successor: Task 3 "a court with more parties than rows pages its Parties page" |
| "an absorbed faction's party draws its own disc" (~27611) | replace with "an absorbed faction's party wears its own ring on the pins" (below) |
| "a marker's tooltip names the province, its governor, party and loyalty" (~27620, with Task 4's weight line) | replace with "a pin's tooltip names the province, its governor, what it adds to his party, and its loyalty" (below) |
| "a marker opens its overseer picker, and an answered choice returns to the map" (~27640) | delete. Successor: Task 5 "the check appoints the chosen man, and the answer returns to the page the picker came from" |
| "closing the court opened from a marker returns to the map; a tab stays" (~27666) | delete: the round trip is gone |
| "replacing a governor records the one who left" (~27688) | keep: it tests the model |
| "a province lost since the map drew never reaches the picker" (~27706) | delete. Successors: Task 2's pin check and Task 5 "a man who stops being free, or a province lost..." |
| "selecting an army or settlement leaves the map with the HUD back" (~27720) | delete. Successor: Task 2 "selecting a settlement or a character through the Governors view closes the court" |
| "ending the turn closes the map and forgets a pending return" (~27737) | delete. Successor: this task's "ending the turn on the Governors view closes the court, pins and all..." |
| "a marker cuts a province name too long for it, and its tooltip keeps it whole" (~27757) | delete. Successor: Task 2's long-name check |
| "the court's Map tab from a marker's picker forgets the way back" (~27781) | delete: there is no way back to forget |
| "a court close spends the way back even when the court is still up" (~27796) | delete |
| "a row that rings nothing says why, in the hint and on its tooltip" (~27811) | delete. Successor: Task 3 "a party that rings nothing says why, in the hint and on its tooltip" |
| "a marker's tooltip names the party it would go with, and only that one" (~27831) | replace with "a pin's tooltip names the party its province would go with, and only that one" (below) |
| "markers and legend swatches wear their party's crest" (~27852) | delete. Successors: Task 2's pin check (the crest fallback) and Task 3's Parties check |
| "the map reopens with nothing chosen" (~27874) | delete. Successor: Task 3 "the Governors view reopens with nothing chosen" |
| "another faction's turn end leaves the player's map up" (~27896) | delete: its listener is deleted |
| "a court that fails to open after a marker click forgets the way back" (~27909) | delete |
| "markers stand in their own holder, under the legend" (~27924) | delete. Successors: `check_gm` (the holder is the panel's first child) and Task 2's screen-size check |
| "the court's opener shutting a marker's picker forgets the way back" (~27940) | delete |
| the `release_governor` case of "each of the twelve panel clicks sends in multiplayer and waits for its trigger" (~21840) | delete that one case: it drove `ICUI.on_row_action`'s Governors branch, which Step 5 deletes. Successor: Task 4 "the column's cross sends its release in multiplayer and waits for the trigger" |

The three replacements go where their originals stood:

```lua
check("an absorbed faction's party wears its own ring on the pins", function()
    local slug = IC.ORIGINS[1].slug
    assert(ICUI.gm_ring_path(slug) == "ui/derpy_ic/gm_ring_" .. slug .. ".png", ICUI.gm_ring_path(slug))
    -- THE FILE EXISTS: the generator writes one per absorbed faction.
    local f = io.open("Modding Files/pack/ui/derpy_ic/gm_ring_" .. slug .. ".png", "rb")
    assert(f, "no ring was generated for " .. slug)
    f:close()
end)

check("a pin's tooltip names the province, its governor, what it adds to his party, and its loyalty", function()
    IC.state = {}
    local g = make_character(831, ANY_SEAT, "legion")
    make_faction(F, IC.CHD_SUBCULTURE, {g}, {"prov_a", "prov_b"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    IC.court(F).govs["prov_a"] = 831
    with_fake_govmap(function(hud, panel, extra, holder)
        ICUI.view = "govs"
        ICUI.pick = nil
        ICUI.open()
        local tip = gm_pin(holder, 1).tooltip or ""
        assert(tip:find("prov_a", 1, true), tip)
        assert(tip:find(ICUI.character_name(g), 1, true), "no governor in: " .. tip)
        assert(tip:find(ICUI.house_name("legion", F) .. ": +1 weight from this province", 1, true),
            "no weight in: " .. tip)
        assert(tip:find("Loyalty: " .. IC.province_loyalty(F, "prov_a"), 1, true), tip)
        assert(tip:find("replace", 1, true), "a governed province does not say a click replaces: " .. tip)
        local none = gm_pin(holder, 2).tooltip or ""
        assert(none:find("No governor", 1, true), none)
    end)
end)

check("a pin's tooltip names the party its province would go with, and only that one", function()
    IC.state = {}
    turn = 1
    local g = make_character(861, ANY_SEAT, "legion")
    make_faction(F, IC.CHD_SUBCULTURE, {g}, {"prov_a", "prov_b", "prov_c"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    IC.court(F).govs["prov_b"] = 861
    with_fake_govmap(function(hud, panel, extra, holder)
        ICUI.view = "govs"
        ICUI.pick = nil
        ICUI.open()
        local takes = {}
        for _, p in ipairs(IC.defecting_provinces(F, "legion")) do takes[p] = true end
        assert(next(takes), "the fixture's legion would take nothing, so this proves nothing")
        local line = "Would go with " .. ICUI.house_name("legion", F)
        for i, p in pairs(ICUI.gm_keys) do
            local tip = gm_pin(holder, i).tooltip or ""
            assert((tip:find(line, 1, true) ~= nil) == (takes[p] == true), p .. ": " .. tip)
        end
    end)
end)
```

Finally, run `grep -n -E "with_fake_map|map_marker\(|ICUI\.MARKER|ICUI\.MAP\b|map_open|map_close|map_return|gov_keys" tools/_iron_court_harness.lua`.
- Expected: no hits.

- [ ] **Step 8: The preview**

In `tools/preview_iron_court.py`, delete:
- `OUT_MAP` and `OUT_GOVS`;
- `"govs"` from `VIEWS`;
- `map_words()`;
- the `if view == "map":` block;
- the `if view == "govs":` block;
- the selftest's two map assertions;
- `__main__`'s "THE MAP ONCE" block.

`DEMO_GOVS` stays: the court view's party card counts from it.

Then run `grep -n -E 'MAP_|MARKER|map_words|OUT_MAP|OUT_GOVS|view == "govs"|view == "map"' tools/preview_iron_court.py`.
- Expected: no hits. Task 7 draws the new Governors view.

- [ ] **Step 9: The published file list**

In `tools/sync_iron_court_repo.py`:
- delete the two `derpy_ic_map*.twui.xml` lines;
- add `_UI + "derpy_ic_gm_pin.twui.xml"` and `_UI + "derpy_ic_gm_face.twui.xml"` in their place;
- add `"gm_row"` to the `("panel", "card", "row", "party", "plot")` tuple, which lists the files with compact copies.

Run: `py tools/sync_iron_court_repo.py --selftest`
Expected: ok. Do not run it without a flag: that copies into the public repo's folder, which is Task 7's, after the author has seen the build.

- [ ] **Step 10: Generate and run the harness**

Run: `py tools/gen_ic_ui.py && IC_TEST_ALL=1 "/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | tail -4`
Expected: `ok (N checks)`. N is the Task 5 count, plus 4 new, minus the 21 deleted outright; the 3 replaced checks keep their place. Record N.

- [ ] **Step 11: Mutants**

Run `py tools/mutate_iron_court.py --selftest` until it reports ok. For each stale anchor it stops on:
- **The code was deleted by this task** (any old map function, the Map tab, `draw_govs`, `gov_row`, the gov burst, the `ANSWERS.gov` wrapper): delete the mutant, and ledger its name in one `Task 6: deleted mutants: ...` line.
- **The code moved** (the `ic_map_click` listener's surviving branches, which lost their `elseif`): re-aim it.

Mutants on `map_region`, `map_rows`, `map_outline` and `map_tip` must still match unchanged: those functions were not touched.

Then append:

```python
    # THE MAP TAB, REMOVED (plan 2026-09-30 Task 6).
    ("the Map tab back in the strip", U,
     """    ic_tab_intrigue  = {750, 62, 240, 32},""",
     """    ic_tab_map       = {750, 62, 240, 32},
    ic_tab_intrigue  = {994, 62, 240, 32},"""),
    ("a tab left where the Map tab's gap was", U,
     """    ic_tab_log       = {1238, 62, 240, 32},""",
     """    ic_tab_log       = {1482, 62, 240, 32},"""),
    ("the Petitions marker left on the old tab", U,
     """    ic_mark_petitions = {1200, 64, 28, 28},""",
     """    ic_mark_petitions = {1444, 64, 28, 28},"""),
```

Run them by name. Expected: `3 mutants, 0 unexplained`. Then run `py tools/gen_ic_ui.py`.

- [ ] **Step 12: Gates.** Every gate, with its expected result:

| Gate | Expected |
|---|---|
| `py tools/gen_ic_ui.py --check` | no drift |
| `py tools/gen_ic_ui.py --selftest` | ok. Run it in the background with a 600s wait loop; it outlasts the tool timeout. |
| `py tools/preview_iron_court.py --check` | ok |
| `py tools/preview_iron_court.py --selftest` | ok |
| `py tools/make_ic_backdrop.py --check` | ok: the tabs moved, and their labels are measured cells |
| `luac -p` on the three Iron Court UI and model Lua files | parses |
| `py tools/check_lua_api.py` on the same files | 0 suspects |
| `py tools/check_lua_literal_left.py` | 0 sites |
| `py tools/check_lua_undeclared.py` | clean |
| `py tools/import_iron_court.py` | `verify ok`, with 2 fewer UI files than Task 5's |
| the harness | `ok (N checks)` |

- [ ] **Step 13: Build and deploy**
  1. Start RPFM's server headless if `http://127.0.0.1:45127/sessions` does not answer.
  2. Run `py tools/deploy_iron_court.py`. Expected:
     - it builds, verifies and prints the build name;
     - if `Warhammer3.exe` is not running, it deploys to data/.
  3. Check that the built pack has neither old file: `py tools/read_pack_index.py "<the built pack>" | grep -c derpy_ic_map` prints 0.
  4. Stop the server.
  5. Ledger `Task 6: complete (tests: harness -> ok (N checks); build <NAME> deployed)`.

---

### Task 7: The Governors view's pictures, the docs, the full mutation run, the build and the handoff

**Files:**
- Modify: `tools/preview_iron_court.py`
  - `gm_hidden`;
  - the `gm_provinces` and `gm_picker` views;
  - every other view hides the column.
- Modify: `docs/CUSTOM_UI.md`: a new section, "Pinning UI to the campaign map".
- Create: `docs/sessions/HANDOFF_20260930_IRON_COURT_GOVERNORS_MAP.md`
- Modify:
  - `docs/SESSION_INDEX.md`;
  - `docs/sessions/PATCH_NOTES_20260925_IRON_COURT.md`;
  - the memory file `wh3-world-space-ui-pin.md`.

**Interfaces:**
- Consumes:
  - the generator's names: `GM_PIN_FILE`, `GM_FACE_FILE`, `GM_ROW_FILE`, `GM_PIN_W/H`, `GM_PLATE_BOX`, `GM_PIN_LAYERS`, `GM_FACE_LAYERS`, `gm_ring_path`, `GM_ROW_X/Y/W/H/PITCH`, `GM_ROWS`, `GM_ROW_LAYOUT`, `GM_ROW_ART`, `GM_ROUND`, `MAP_RING_CAPITAL`, `MAP_RING_OUTLINE`, `plate_path`, `MASK_NONE`, `SIL_PATH`, `sigil_path`;
  - the map Lua's strings: `GM_PAGE_TITLE`, the fealty paths, and the row and picker formats.
- Produces: `preview_iron_court.gm_hidden(G, view, n_rows) -> set`, and two new pictures, `ic_gm_provinces*.png` and `ic_gm_picker*.png`.

- [ ] **Step 1: Snapshot** `tools/preview_iron_court.py`, `docs/CUSTOM_UI.md`, `docs/SESSION_INDEX.md` and the patch-notes file to the scratchpad as `*_before_govmap_t7.*`.

- [ ] **Step 2: Write the failing preview selftest**

In `selftest()`, before its closing `print`, add:

```python
    # THE GOVERNORS VIEW'S COLUMN IS ITS OWN. Every other picture hides every
    # ic_gm_ cell - PANEL_LAYOUT carries them for all views, and the static pass
    # draws whatever is not hidden - and the Governors pictures hide only what
    # ICUI.gm_draw_column hides on that page.
    _G = _gen()
    _gm = set(n for n in _G.PANEL_LAYOUT if n.startswith("ic_gm_"))
    assert _gm, "PANEL_LAYOUT has no ic_gm_ cells: Task 3 is not in"
    for _v in VIEWS:
        if not _v.startswith("gm_"):
            assert gm_hidden(_G, _v, 0) >= _gm, "%s draws the Governors column" % _v
    _prov = gm_hidden(_G, "gm_provinces", _G.GM_ROWS)
    assert "ic_gm_col" not in _prov and "ic_gm_sort_1" not in _prov and "ic_gm_hint" in _prov
    assert "ic_gm_next" in _prov, "one page of provinces draws a pager"
    _pick = gm_hidden(_G, "gm_picker", _G.GM_ROWS + 1)
    assert "ic_gm_sort_1" in _pick and "ic_gm_next" not in _pick
    # AND THE MAP SHOWS THROUGH: the court's backdrop is not drawn on this view.
    _out = os.path.join(PG.CACHE, "selftest_gm.png")
    render(path=_out, view="gm_provinces")
    from PIL import Image
    assert Image.open(_out).convert("RGBA").getpixel((1800, 600)) == GM_MAP_FILL, (
        "the Governors picture drew the backdrop over the map")
```

Run: `py tools/preview_iron_court.py --selftest`
Expected: FAIL on `NameError: gm_hidden`.

- [ ] **Step 3: The preview**

Near `OUT_PETITIONS`, add:

```python
# THE GOVERNORS VIEW (plan 2026-09-30): the column over the live map, as two
# pictures, one per page shape. The map is a flat stand-in - a shut game has no
# campaign map to draw - and the pins stand on it in a sheet, not on
# settlements, which is the engine's job.
OUT_GM = os.path.join(PG.CACHE, "ic_gm_provinces.png")
OUT_GM_PICK = os.path.join(PG.CACHE, "ic_gm_picker.png")
GM_MAP_FILL = (46, 52, 38, 255)
```

Add `"gm_provinces", "gm_picker"` to the end of `VIEWS`.

After `pick_lines`, add:

```python
def gm_hidden(G, view, n_rows):
    """The ic_gm_ cells this picture leaves undrawn, as the Lua leaves them.

    Off the Governors view, all of them (ICUI.gm_show_column). On it: the footer's
    plate, which shows with the footer line and the demo has none; the hint,
    which the Provinces page hides and the picker shows only for an empty list;
    the sort, which is the Provinces page's alone; and the pager when the page
    holds the whole list (ICUI.gm_draw_page).
    """
    gm = set(n for n in G.PANEL_LAYOUT if n.startswith("ic_gm_"))
    if view not in ("gm_provinces", "gm_picker"):
        return gm
    out = {"ic_gm_foot", "ic_gm_hint"}
    if view == "gm_picker":
        out |= {"ic_gm_sort_1", "ic_gm_sort_2", "ic_gm_sort_3"}
    if n_rows <= G.GM_ROWS:
        out |= {"ic_gm_prev", "ic_gm_page", "ic_gm_next"}
    return out


# THE PROVINCES PAGE'S DEMO: DEMO_GOVS, plus the worst row the page can be
# handed - the longest province, governed by a long name who is away - and the
# settlement levels each province holds, so "+N weight" is the model's figure.
GM_DEMO_LEVELS = (9, 4, 0, 6, 2, 5, 3)


def gm_province_rows():
    return list(DEMO_GOVS) + [(DEMO_LONG_PROVINCE, "Dazminus Deathdealer", "temple", True, 25)]
```

In `render`:
1. Add `gm = view.startswith("gm_")` as its first line after `ui = lua("ui")`.
2. In the `extra=` list handed to `PG.extract_art`, add the art only the Lua names:

   ```python
           + [G.GM_ROW_ART % s for s in ("active", "hover", "selected", "selected_hover", "inactive")]
           + [G.GM_ROUND % s for s in ("active", "hover", "selected", "selected_hover")]
           + re.findall(r'"(ui/skins/default/icon_fealty_\w+\.png)"', lua("ui_map"))
   ```

3. After `card_doc = ...`, add:

   ```python
       gm_pin_doc, gm_face_doc = doc_of(G.GM_PIN_FILE), doc_of(G.GM_FACE_FILE)
       gm_row_doc = doc_of(G.GM_ROW_FILE)
   ```

   Then add `(gm_pin_doc, "gmpin"), (gm_face_doc, "gmface"), (gm_row_doc, "gmrow")` to the tuple the `named` loop walks.
4. Replace `canvas = Image.new("RGBA", (G.PANEL_W, G.PANEL_H), (0, 0, 0, 255))` with:

   ```python
       canvas = Image.new("RGBA", (G.PANEL_W, G.PANEL_H), GM_MAP_FILL if gm else (0, 0, 0, 255))
   ```

5. Replace the panel's paste with:

   ```python
       # ON THE GOVERNORS VIEW THE BACKDROP IS CLEARED (ICUI.gm_sync), so the
       # panel's own image 0 is left undrawn and the map shows through.
       paste(panel, named[("panel", "derpy_ic_panel")], 0, 0, G.PANEL_W, G.PANEL_H,
             repaint={0: None} if gm else None)
   ```

6. Change `_lit_tab = "offices" if _base == "pick" else view` to:

   ```python
       _lit_tab = "offices" if _base == "pick" else ("govs" if gm else view)
   ```

7. In the section-label chain, before its final `else:`, add:

   ```python
           elif view == "gm_provinces":
               STRINGS["ic_lbl_section"] = re.search(
                   r'govs\s*=\s*"([^"]*)"', _block(ui, "ICUI.SECTION")).group(1)
           elif view == "gm_picker":
               # ICUI.pick_title's governor line, for the province being chosen for.
               STRINGS["ic_lbl_section"] = re.search(
                   r'"(Choose who governs )%s"', ui).group(1) + DEMO_GOVS[2][0]
   ```

8. After `hidden = set(("ic_page_prev", "ic_page_lbl", "ic_page_next"))`, add:

   ```python
       _gm_n = (len(gm_province_rows()) if view == "gm_provinces"
                else len(pick_lines(False)) if view == "gm_picker" else 0)
       hidden |= gm_hidden(G, view, _gm_n)
   ```

9. In `STRINGS`, add the column's words, read off the map Lua so a reworded label reaches the picture:

   ```python
       _mlua = lua("ui_map")
       _titles = dict(re.findall(r'(\w+) = "([^"]+)"', _block(_mlua, "ICUI.GM_PAGE_TITLE")))
       STRINGS.update({
           "ic_gm_head": _titles["picker" if view == "gm_picker" else "provinces"],
           "ic_gm_tog_lbl_1": _titles["parties"],
           "ic_gm_tog_lbl_2": _titles["provinces"],
           "ic_gm_sort_1": "Province", "ic_gm_sort_2": "Governor", "ic_gm_sort_3": "Loyalty",
           "ic_gm_page": "Page 1 of %d" % max(1, -(-_gm_n // G.GM_ROWS)),
           "ic_gm_prev": "Previous", "ic_gm_next": "Next",
       })
   ```

   `_block` expects a top-level table. If `ICUI.GM_PAGE_TITLE` is a one-line table and `_block` does not match it, read it with `re.search(r'ICUI\.GM_PAGE_TITLE = \{([^}]*)\}', _mlua)` instead. Only the reader changes.
10. In the static pass, light the Provinces toggle on its page. Replace `lit = {0: TAB_SELECTED} if name == "ic_tab_" + _lit_tab else None` with:

    ```python
            lit = {0: TAB_SELECTED} if name == "ic_tab_" + _lit_tab else None
            if name == "ic_gm_tog_2" and view == "gm_provinces":
                lit = {0: G.GM_ROUND % "selected"}
    ```

11. After the static pass's loop, and before `if view in ("pick", "pick_ready"):`, add the two views:

```python
    # ---- the Governors view: the column's rows, then pins on the map -------
    if gm:
        def grow(i, r):
            """One row of the column's pool, as ICUI.gm_fill_row fills it."""
            rx, ry = G.GM_ROW_X, G.GM_ROW_Y + i * G.GM_ROW_PITCH
            paste(gm_row_doc, named[("gmrow", "derpy_ic_gm_row")], rx, ry,
                  G.GM_ROW_W, G.GM_ROW_H, repaint={0: G.GM_ROW_ART % r["look"]})
            for key in sorted(G.GM_ROW_LAYOUT):
                cx, cy, cw, ch = G.GM_ROW_LAYOUT[key]
                comp = named[("gmrow", key)]
                x, y = rx + cx, ry + cy
                if key == "ic_gr_face":
                    if r.get("face"):
                        paste(gm_row_doc, comp, x, y, cw, ch, repaint={
                            0: G.MASK_NONE if r.get("vacant") else G.plate_path(r.get("plate")),
                            1: r["face"], 2: None})
                elif key in ("ic_gr_crest", "ic_gr_badge", "ic_gr_icon"):
                    art = {"ic_gr_crest": r.get("crest"), "ic_gr_badge": r.get("badge"),
                           "ic_gr_icon": r.get("fealty")}[key]
                    if art:
                        paste(gm_row_doc, comp, x, y, cw, ch, repaint={0: art})
                else:
                    s = r.get(key[len("ic_gr_"):])
                    if s:
                        s = cut_words(lambda _s: measure(gm_row_doc, comp, _s), s, cw)
                        text(gm_row_doc, comp, s, x, y, cw, ch)

        fealty = dict(re.findall(r'(high|medium|low) = "(ui/skins/default/icon_fealty_\w+\.png)"',
                                 lua("ui_map")))
        tune = _tune(lua("model"))
        rate = float(tune["weight_per_gov_level"])
        floor, start = int(tune["prov_defect_floor"]), int(tune["prov_loyalty_start"])

        def band(loyal):
            return fealty["low" if loyal <= floor else "high" if loyal > start else "medium"]

        drawn = 0
        if view == "gm_provinces":
            rows = gm_province_rows()
            for i, (prov, who, slug, away, loyal) in enumerate(rows[:G.GM_ROWS]):
                levels = GM_DEMO_LEVELS[i % len(GM_DEMO_LEVELS)]
                weight = max(1, -(-int(levels * rate * 100) // 100))
                grow(i, {
                    "look": "selected" if i == 1 else "active",
                    "l1": prov,
                    "l2": (who + " (away)") if (who and away) else (who or "None assigned"),
                    "l3": ("%d%%, +%d weight" % (loyal, weight)) if who else "%d%%" % loyal,
                    "face": DEMO_FACES[i % len(DEMO_FACES)] if who else G.SIL_PATH,
                    "vacant": who is None, "plate": slug,
                    "badge": G.sigil_path(slug) if who else None,
                    "fealty": band(loyal)})
                drawn += 1
        else:
            rows = pick_lines(False)
            _kw = _kind_words(ui)
            for i, (name, trade, house, rank, standing, holds, refusal, kind) in \
                    enumerate(rows[:G.GM_ROWS]):
                slug, party_name = court[house][0], court[house][1]
                grow(i, {
                    "look": "inactive" if refusal else ("selected" if i == 0 else "active"),
                    "l1": "%s%s - %s" % ((_kw[kind] + " ") if _kw else "", name, trade),
                    "l2": party_name,
                    "l3": "Rank %d, %d influence" % (rank, standing),
                    "face": DEMO_FACES[i % len(DEMO_FACES)], "plate": slug,
                    "badge": G.sigil_path(slug)})
                drawn += 1

        # THE PINS, in a sheet right of the column: one per demo province, the
        # first a capital, the second ringed as chosen. The FACE IS SQUARE HERE:
        # TWUI Studio's rasteriser has no maskimage, so the porthole_mask layer
        # is left undrawn rather than drawn as a white disc over the face. In
        # game it is round (Phase 0 question 5; see the handoff).
        pin = named[("gmpin", "derpy_ic_gm_pin")]
        face = named[("gmface", "derpy_ic_gm_face")]
        px0, py0 = G.GM_ROW_X + G.GM_ROW_W + 120, 180
        bx, by, bw, bh = G.GM_PLATE_BOX
        for i, (prov, who, slug, away, loyal) in enumerate(gm_province_rows()):
            x = px0 + (i % 4) * (G.GM_PIN_W + 150)
            y = py0 + (i // 4) * (G.GM_PIN_H + 140)
            paste(gm_pin_doc, pin, x, y, G.GM_PIN_W, G.GM_PIN_H, repaint={
                G.GM_PIN_LAYERS.index("party"): G.gm_ring_path(slug),
                G.GM_PIN_LAYERS.index("capital"): G.MAP_RING_CAPITAL if i == 0 else None,
                G.GM_PIN_LAYERS.index("outline"): G.MAP_RING_OUTLINE if i == 1 else None})
            # AN EMPTY SEAT IS THE DARK GROUND ALONE: gm_draw_pins clears both the
            # port and the crest layer for it.
            paste(gm_face_doc, face, x, y, G.GM_PIN_W, G.GM_PIN_H, repaint={
                G.GM_FACE_LAYERS.index("port"): DEMO_FACES[i % len(DEMO_FACES)] if who else None,
                G.GM_FACE_LAYERS.index("crest"): None,
                G.GM_FACE_LAYERS.index("mask"): None})
            name = cut_words(lambda _s: measure(gm_pin_doc, pin, _s), prov, bw)
            text(gm_pin_doc, pin, name, x + bx, y + by, bw, bh // 2)
            text(gm_pin_doc, pin, "Loyalty %d%%" % loyal, x + bx, y + by + bh // 2, bw, bh // 2)
        draw.text((px0, G.PANEL_H - 40), "Map stand-in. Faces are square here and "
                  "round in game: the preview cannot draw a maskimage.",
                  fill=(255, 248, 215, 255), font=font(14))

        out = path or sized(OUT_GM_PICK if view == "gm_picker" else OUT_GM, box_w)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        canvas.convert("RGB").save(out)
        return out, n_art, missing, drawn
```

`court` is `demo_court(G)`, bound above. If `cut_words` or `_kind_words` takes other arguments than the pick view passes, match the pick view's calls; the pick view above is the reference.

- [ ] **Step 4: Run the preview and look at it**

Run: `py tools/preview_iron_court.py --selftest && py tools/preview_iron_court.py`
Expected:
- `selftest ok`;
- every view is written at 1600, 1920 and 2560, with the two new ones at each size;
- no `PROBLEM:` lines;
- no `art not found` lines for any path under `ui/skins/default/`.

Open `ic_gm_provinces.png`, `ic_gm_picker.png` and their 1600 copies with the Read tool, and answer in the ledger, one line each:
1. Does every cell's text sit on its plate, with no text on the bare map stand-in except the pins' own?
2. Does the chosen row read as chosen, and an inactive man's card as inactive?
3. Does the longest province cut on a word inside its row, and inside its pin's plate?
4. Is there dead space in the column below the pager, or does the column end where its rows do?
5. Does the court picture (`ic_court.png`) show no Governors column? This is what `gm_hidden` fixed.

A "no" to 1-3 or 5 is a finding: fix it where the plan's own code or layout caused it, then re-run. A "no" to 4 is a design question for the author: ledger it and carry it to the handoff.

- [ ] **Step 5: `docs/CUSTOM_UI.md`**

After the section "Your panel does not block the map until you say so", add a new section, `## Pinning UI to the campaign map`. Keep it to the facts this work measured, each with its source:
- `ContextWorldSpaceComponent` on `CcoCampaignSettlement`, function `Position`, with `depth_disabled`. It is CA's own, from `dlc25_black_towers.twui.xml`'s `template_black_tower_slot` and `kislev_atamans.twui.xml`. Kislev's template carries no `offset_x/y/z`.
- **No `ContextOpacitySetter`.** CA's fade reads the component's own screen y, and a pin made from Lua starts at its holder's corner, y = 0: it drew nothing in game (build A06C68A6, 2026-09-29).
- **The holder is the panel's FIRST child and takes no clicks.** Children draw in declaration order, and a runtime pin is the last child.
- **A pin is repainted in place, never remade per refresh.** A new one starts at the corner until the engine places it.
- **A runtime child lands at its parent's origin** (measured 2026-09-04). Two sibling components with identical boxes and the same context therefore anchor alike. That is how the pin carries a masked face that is not its child.
- **`maskimage`**:
  - it is a component-level attribute, between `uniqueguid` and `currentstate`;
  - its value is the GUID of the component's own mask `componentimage`, listed last in every state (CA's `drag_icon` in `kislev_atamans.twui.xml`);
  - it clips the WHOLE component;
  - what Phase 0 question 5 found: copy it from the ledger's `Task 2: Phase 0 answer 5` line, with the build name.
- **Letting the map have the mouse:** `SetInteractive(false)` on the panel and a cleared image 0. Say what Phase 0 questions 2-4 found, from the ledger.

Add one line for it to the table in `CLAUDE.md`'s `docs/CUSTOM_UI.md` row: append `, **pinning UI to the campaign map - ContextWorldSpaceComponent, no fade, the holder, and maskimage**` inside that row's description.

- [ ] **Step 6: Memory**

Update `C:\Users\GAYAO-Family\.claude\projects\g--Modding-for-resources\memory\wh3-world-space-ui-pin.md`:
- add the `maskimage` rule and the Phase 0 answers, with the build name;
- keep it one fact per file: if the mask answer is a fact of its own, write `wh3-twui-maskimage.md` instead and link the two with `[[...]]`;
- add its line to the UI hub, `index-ui.md`.

- [ ] **Step 7: The full mutation run**

Nothing else may run while this does, and no file may be edited.

Run it in the background: `py tools/mutate_iron_court.py > "$LEDGER_DIR/mutants_full.txt" 2>&1`. `$LEDGER_DIR` is this plan's `.superpowers/sdd/2026-09-30-iron-court-governors-map/`. Wait on it with a 600s loop until the process exits.

Expected: the last line reports `0 unexplained`.
- **A survivor from this plan** (its name is in Tasks 1-6): either its check is too weak, which is a finding (strengthen the check; watch it fail on the mutant; re-run that mutant by name), or it is equivalent (ledger a ruling naming why).
- **A survivor from before this plan:** re-run it alone. If it survives there too, this plan weakened a check that used to hold it. Find which, and restore the check.

Then run `py tools/gen_ic_ui.py`, because the runner restores the Lua and not what the Lua generated.

- [ ] **Step 8: Gates.** Every gate, with its expected result:

| Gate | Expected |
|---|---|
| `py tools/gen_ic_ui.py --check` | no drift |
| `py tools/gen_ic_ui.py --selftest` | ok. Run it in the background with a 600s wait loop. |
| `py tools/preview_iron_court.py --check` | ok |
| `py tools/preview_iron_court.py --selftest` | ok |
| `py tools/make_ic_backdrop.py --check` | ok |
| `luac -p` on the four Iron Court Lua files | parses |
| `py tools/check_lua_api.py` on the same files | 0 suspects |
| `py tools/check_lua_literal_left.py` | 0 sites |
| `py tools/check_lua_undeclared.py` | clean |
| `py tools/import_iron_court.py` | `verify ok` |
| `py tools/sync_iron_court_repo.py --selftest` | ok |
| the harness, `IC_TEST_ALL=1` | `ok (N checks)`, no FAIL |

- [ ] **Step 9: Build and deploy**
  1. Start RPFM's server headless if `http://127.0.0.1:45127/sessions` does not answer: `Start-Process "G:\Modding for resources\RPFM\rpfm_server.exe" -WindowStyle Hidden`.
  2. Run `py tools/deploy_iron_court.py`. Expected:
     - it builds, verifies and prints the build name;
     - if `Warhammer3.exe` is not running, it deploys to data/.
  3. Stop the server.
  4. Do not push to GitHub, and do not run `sync_iron_court_repo.py` without a flag: both wait for the author.

- [ ] **Step 10: The handoff, the index and the patch notes**

1. **The handoff.** Write `docs/sessions/HANDOFF_20260930_IRON_COURT_GOVERNORS_MAP.md` in the party map handoff's shape (`HANDOFF_20260930_IRON_COURT_PARTY_MAP.md`):
   1. what the Governors view does now;
   2. every `Ruling:` line in the ledger, each with what it costs if wrong;
   3. the Phase 0 answers;
   4. the gates, with their numbers;
   5. owed in game: what the harness cannot see (the pins at a second UI scale, the camera move, the round buttons' grey look, the picker's inactive cards, and Step 4's question 4 if the author has not answered it);
   6. the build name.
2. **The index.** In `docs/SESSION_INDEX.md`:
   - change the spec's line from "DESIGN ... awaiting the author's review" to "BUILT and deployed as `<NAME>`, not pushed";
   - add one line for this plan;
   - add one line for the handoff.

   One line each, in the index's own style. No paragraph.
3. **The patch notes.** In `docs/sessions/PATCH_NOTES_20260925_IRON_COURT.md`:
   - replace the party map's New line (build 1C3AEB24) with these lines, one short phrase each:
     - `[*][b]Governors on the map.[/b] The Governors tab opens onto the campaign map: each province shows its governor, its loyalty and his party.`
     - `[*][b]Choose governors from the map.[/b] Click a province to choose its governor, or pick it in the list.`
     - `[*][b]Bigger provinces, more weight.[/b] A governor's party gains more weight from a province with more settlement levels.`
   - delete the Map tab, which is gone;
   - add to the prose paragraph which build carries these lines, and that the party map's builds (1C3AEB24 and the two before it) never shipped a Map tab to players.

   Plain words (weight, influence, loyalty), no emojis, and never "rung".

- [ ] **Step 11: Complete the plan.** Ledger `Task 7: complete (tests: harness -> ok (N checks); mutants: <M>, 0 unexplained; build <NAME> deployed)`. Then run the final whole-work review the executing skill prescribes, with this plan's Review Focus handed to the reviewer verbatim.
