# Iron Court for Dwarfs - Phase 5: the Book of Grudges Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Dwarf court reads CA's Book of Grudges. Each turn it weighs every faction it has met by the grudge points CA has written on that faction's armies and settlements; reaching 500, 1,000 and 2,000 sours that faction's regard for the court once per line, in order, never reversed and never again after a load; peace, trade or an alliance with a faction the Book names at 1,000 or more writes a "peace" grudge in the Clan Warriors' and the Ancestor Priesthood's books; a rise in the faction's own grudge points (CA pays them when a grudge is settled) is a deed for both parties; and the Court tab shows "The Book names:" with the top three.

**Architecture:** Model code goes in `zzz_derpy_iron_court.lua` as one block before `function IC.turn`: `IC.book_weight` / `IC.book_list` / `IC.book_names` read CA's two pooled resources through `pooled_resource_manager():resource(key)` exactly as CA's `wh3_campaign_grudges.lua` does (lines 875-895), with one sum per faction per turn held in the unsaved `IC._book`, which only the turn path fills. `IC.book_tick` runs at the end of `IC.turn` (caught, like the parties' turn), crosses bands, calls `cm:apply_dilemma_diplomatic_bonus` once per band and keeps the count in `court.book`, saved as field 20. Two listeners join `IC.register`: `ic_book_peace` (`PositiveDiplomaticEvent`) and `ic_deed_grudge` (through the existing `on_deed`, `PooledResourceChanged`). The panel gains one text cell, `ic_book`, under the Crown's box, drawn by `ICUI.draw_book` and cut to fit with `ICUI.fit_cut`.

**Tech Stack:** Lua 5.1, Python 3 (py), RPFM MCP
**Spec:** docs/superpowers/specs/2026-10-04-iron-court-dwarfs-design.md (and the CONTRACT file)

## Global Constraints

- No emojis anywhere. Never the word "rung". Player text in plain words: "regard", "grudge points", never "standing", "cap", "AI".
- **Multiplayer:** every model change happens on an event every machine sees (`FactionTurnStart`, `PositiveDiplomaticEvent`, `PooledResourceChanged`). The panel only READS the Book; it never writes `IC._book`, `court.book` or a grudge. `IC.book_list(fk)` without its `fill` argument is the panel's read and fills nothing.
- **Performance bound** (the weight walk): met factions only (`faction:factions_met()`), never a Dwarf (CA writes no points on one: `grudge_exclusion_cultures`), never a dead faction, never a garrison (`military_force_list(true)`, CA's own skip in `wh3_dlc29_middenland_fervour.lua:212`; CA never writes grudge points on armed citizenry, `wh3_campaign_grudges.lua:861`). CA keeps the points ON the army or settlement, not per Dwarf faction, so a faction's weight is the same number for every Dwarf court: `IC._book = {turn = n, w = {[faction key] = weight}}` holds it once per turn for all of them. A round costs one walk of (armies + regions) x 3 interface calls per distinct met non-Dwarf faction, not one per Dwarf court. Not "at war only": the spec says every met faction.
- No loc call in a model function (turn-1 CTD); faction names are resolved in the panel with `loc("factions_screen_name_" .. key, key)`.
- Lua 5.1 with the game's miscompile: no number literal on the LEFT of an arithmetic operator (`py tools\check_lua_literal_left.py`).
- Run every tool from `G:\Modding for resources`. Harness: `& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua`; one group: `$env:IC_ONLY = "book:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`; every failure: `$env:IC_TEST_ALL = "1"` the same way.
- Every new check is watched failing for its own reason before the code that passes it is written.
- Spec numbers (copied): bands 500 / 1,000 / 2,000; penalties -1 / -2 / -3 (CA's -6..+6 scale); named at 1,000; top three. Contract TUNE keys: `book_bands`, `book_penalty`, `book_named`, `book_top`. Save field 20 `other_faction_key:n` joined by `/`.
- **THE GATES** (the contract's, run at every checkpoint; this is not a git repo):
  ```powershell
  Get-ChildItem "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court*.lua" | ForEach-Object { & "C:\Program Files (x86)\Lua\5.1\luac.exe" -p $_.FullName; if ($LASTEXITCODE) { "LUAC FAIL $($_.Name)" } }
  & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua
  py tools\check_lua_api.py
  py tools\check_lua_literal_left.py
  py tools\check_lua_undeclared.py (Get-ChildItem "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court*.lua").FullName
  py tools\gen_ic_ui.py --check
  py tools\gen_ic_ui.py --selftest
  py tools\gen_iron_court.py --check
  ```
  Expected: no `LUAC FAIL`, `iron court harness: ok (N checks)`, every tool exit 0.

**Verified API** (`py tools\check_lua_api.py --explain <member>` against CA's 9.0 docs, 2026-10-04; event context members are in `scripting_doc.html`'s event table, which `--explain` does not index, so they were read there and each is used by CA's own scripts):

| Call | CA's entry | CA's own use |
|---|---|---|
| `faction:factions_met()` | "return the factions this faction has met" -> `FACTION_LIST_SCRIPT_INTERFACE` | `wh3_campaign_grudges.lua:1298` |
| `faction:military_force_list([optional] bool skip_garrison_armies)` | "All military forces in this faction" -> `MILITARY_FORCE_LIST_SCRIPT_INTERFACE` | `(true)`: `wh3_dlc29_middenland_fervour.lua:212` |
| `faction:region_list()` | "A list of regions owned by the faction" -> `REGION_LIST_SCRIPT_INTERFACE` | `wh3_campaign_grudges.lua:877` |
| `military_force:pooled_resource_manager()`, `region:pooled_resource_manager()` | -> `POOLED_RESOURCE_MANAGER_SCRIPT_INTERFACE` | `:881`, `:889` |
| `pooled_resource_manager:resource(String pooled_resource_key)` | "Pooled resource with the specified record key. Null if not present" -> `POOLED_RESOURCE_SCRIPT_INTERFACE` | `:881` |
| `pooled_resource:is_null_interface()` | -> bool | `:882` |
| `pooled_resource:value()` | "Total value of this pool" -> int32 | `:1270`, `:1510` |
| `list:num_items()`, `list:item_at(i)` | 0-based, "between 0 and (max items - 1)" | everywhere |
| `faction:is_dead()`, `faction:subculture()`, `faction:name()` | bool; "Returns the subculture for the faction" string; key | |
| `cm:apply_dilemma_diplomatic_bonus(string, string, number)` | "Directly applies a diplomatic bonus or penalty between two factions, as if it had come from a dilemma ... integer between -6 and +6" -> nil | CA's five calls put the actor first and the faction whose regard moves second (memory `wh3-dilemma-bonus-argument-order`) |
| `PooledResourceChanged`: `faction()`, `resource()`, `amount()`, `has_faction()` | "the faction that owns the resource"; the resource; "Amount the pooled resource has changed by" | `wh3_campaign_grudges.lua:645-651`, `:1138-1152` |
| `PositiveDiplomaticEvent`: `proposer()`, `recipient()`, `is_peace_treaty()`, `is_trade_agreement()`, `is_alliance()`, `is_military_alliance()`, `is_defensive_alliance()` | as named | `wh3_campaign_grudges.lua:771-775`, `wh3_dlc25_grudge_cycles.lua:655`, `wh3_dlc25_malakai_battles.lua:1519` |

Pool keys, from CA's `book_of_grudges` table (`wh3_campaign_grudges.lua:129-131`): `wh3_dlc25_dwf_grudge_points` (the Dwarf faction's own), `wh3_dlc25_dwf_grudge_points_enemy_armies` (on a military force), `wh3_dlc25_dwf_grudge_points_enemy_settlements` (on a region).

**Rulings against the spec**

1. **A line reached is a line crossed**: 500 crosses the first band, and "a faction above 1,000" means at 1,000 or more. One convention for both, and both boundaries are pinned.
2. **"Named" for the peace grudge reads the SAVED bands, not the live weight.** CA's own `remove_grudge_points_when_form_alliance_with_dwarfs` listens to the same `PositiveDiplomaticEvent` and wipes an ally's points (`wh3_campaign_grudges.lua:769-805`); which listener runs first is not ours to know, so a live read could see zero. A faction is in the Book when its crossed bands reach `book_named`; the Book never forgets, which is the lore.
3. **The bonus is called in the spec's order, `(own, them, n)`**, which by CA's convention moves the named faction's regard for the court. Not mirrored: the spec says once per band. See Review Focus 1.
4. **One "peace" grudge per party per turn**: a deal that is peace and trade at once may raise one event or two, and is one wrong either way.
5. **A faction is weighed once per turn**, at the first Dwarf court's turn start of the round; points gained later in the round count next turn (`ponytail:` comment in the code).
6. **The Book line sits under the Crown's box, not in it**, so the Chaos Dwarf box keeps its height; it is hidden on a Chaos Dwarf court and on every other tab.
7. **The grudge deed's two parties** are written `{party = "legion", also = "temple", tune = "deed_grudge"}`: one optional field read by `IC.deed`, the smallest change to the deed path. `deed_grudge = 3`, the battle deed's value.

**Added to the contract by this plan** (consumed by phase 6, the release pass): `IC.book_list(faction_key, fill)`, `IC.in_book(faction_key, other_key)`, `IC.book_peace(faction_key, other_key)`, `IC._book` (unsaved), `IC.BOOK_ARMY`, `IC.BOOK_SETTLEMENT`, `IC.GRUDGE_POINTS`, `IC.BOOK_WRONGED`, `court.book`, TUNE `deed_grudge`, the DEEDS field `also`, listeners `ic_book_peace` and `ic_deed_grudge`; UI `ic_book`, `ICUI.draw_book`, `ICUI.book_tip`, `ICUI.BOOK_LABEL`, `ICUI.BOOK_EMPTY`; Python `PANEL_LAYOUT["ic_book"]`, `BOOK_GAP`, `CUT_CELLS["ic_book"]`.

## Review Focus

1. **Which side's regard falls.** `(own, them, -n)` follows CA's (actor, affected) order: the named faction comes to like the Dwarfs less. An AI Dwarf court's own regard for that faction does not move. The court's rebel souring (`IC.rebel_sour`, ~4575) calls both ways for exactly this reason. Keep the spec's single call, or mirror it? Pinned as one call in Task 2.
2. **A save from before the Book** (19 fields): loads with no bands crossed, and the next turn fires every band the faction has already reached, once. Pinned in Task 2.
3. **The panel never fills the turn's cache**, so what each machine holds does not depend on whether its player opened the court. Pinned in Task 1 and mutated in Task 6.
4. **The treaty after CA's wipe**: an alliance with a named faction is still a grudge although CA zeroes the faction's points on that same event. Pinned in Task 3.
5. **The Book line's contrast**: it sits on the dimmed backdrop, not on a plate. `make_ic_backdrop.py --check` measures it; if it fails, Task 5 stops for the author instead of re-dimming the backdrop.

---

### Task 1: Weighing the Book

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua` (`IC.TUNE` deeds block ~line 636; a new block directly above `function IC.turn(faction_key)`, ~line 6276)
- Test: `tools/_iron_court_harness.lua` (stubs: above `local function make_character(` ~84, the force table in `make_character` ~121, `make_faction`'s `factions_met` ~292, `military_force_list` ~306, its region table ~365; the fault collector ~1192; checks appended before the final `print(string.format("iron court harness: ok ...`)

**Interfaces:**
- Consumes: `IC.race_key(faction_key)` and `IC.RACES.dwf.subculture` (phases 1-2), `real_faction` (local, ~1916), `IC.warn`.
- Produces: `IC.TUNE.book_bands`, `book_penalty`, `book_named`, `book_top`, `deed_grudge`; `IC.BOOK_ARMY`, `IC.BOOK_SETTLEMENT`, `IC.GRUDGE_POINTS`; `IC._book`; `IC.book_weight(faction_key, other_key) -> number`; `IC.book_list(faction_key, fill) -> {{key =, weight =}, ...}` heaviest first, ties by key, weight > 0 only; `IC.book_names(faction_key, n) -> the first n of book_list`.

- [ ] **Step 1: The stubs.** Directly above `local function make_character(`, add:

```lua
-- A POOLED RESOURCE MANAGER over `pools` ({[key] = value}) (plan 2026-10-04
-- phase 5). CA: resource(key) is "Null if not present" - and the null one here
-- has NO value(), so a caller that forgets is_null_interface() errors instead
-- of reading a zero.
local function fake_prm(pools)
    return {resource = function(_self, key)
        local v = (pools or {})[key]
        if v == nil then return {is_null_interface = function() return true end} end
        return {is_null_interface = function() return false end,
                key = function() return key end,
                value = function() return v end}
    end}
end
```

In `make_character`'s `military_force` table, after the `is_armed_citizenry` entry:

```lua
                -- CA'S GRUDGE POINTS ON THIS ARMY, off c._grudge, under CA's
                -- own key TYPED HERE: a model reading the wrong pool reads nothing.
                pooled_resource_manager = function()
                    return fake_prm({wh3_dlc25_dwf_grudge_points_enemy_armies = c._grudge})
                end,
```

In `make_faction`, replace the `factions_met` body's push with the registered faction when there is one:

```lua
            for _, key in ipairs(f._met or {}) do
                -- THE REAL STUB WHEN THERE IS ONE: CA's list holds whole faction
                -- interfaces, and the Book walks their armies off it.
                out[#out + 1] = factions[key] or {is_null_interface = function() return false end,
                                                  name = function() return key end}
            end
```

Replace `military_force_list` so it honours CA's documented `skip_garrison_armies`, and give the garrison a pool:

```lua
        military_force_list = function(_self, skip_garrisons)
            local out = {}
            for _, c in ipairs(characters) do
                if c._force == true and not (skip_garrisons and c._citizenry == true) then
                    out[#out + 1] = c:military_force()
                end
            end
            if f._garrison_units and not skip_garrisons then
                out[#out + 1] = {
                    is_null_interface = function() return false end,
                    cqi = function() return 0 end,
                    is_armed_citizenry = function() return true end,
                    unit_list = function()
                        return make_unit_list(nil, f._garrison_units)
                    end,
                    -- POINTS CA NEVER WRITES on a garrison, so a Book that
                    -- reads one reads a number the game cannot have.
                    pooled_resource_manager = function()
                        return fake_prm({wh3_dlc25_dwf_grudge_points_enemy_armies = f._garrison_grudge})
                    end,
                }
            end
            return {
                num_items = function() return #out end,
                item_at = function(_, i) return out[i + 1] end,
            }
        end,
```

In the main (non-extra) region table of `region_list`, after `is_province_capital`:

```lua
                        -- CA'S GRUDGE POINTS ON THIS SETTLEMENT, off
                        -- f._grudge_regions[province]; nil is no pool at all.
                        pooled_resource_manager = function()
                            return fake_prm({wh3_dlc25_dwf_grudge_points_enemy_settlements =
                                             (f._grudge_regions or {})[key]})
                        end,
```

In the `IC.warn` collector (~1192), widen the match so a caught Book failure fails the run like a caught parties' turn:

```lua
        if string.find(tostring(text), "parties' turn failed", 1, true)
           or string.find(tostring(text), "the Book failed", 1, true) then
```

- [ ] **Step 2: Write the failing checks** (append before the final summary):

```lua
-- ---------------------------------------------------------------------------
-- THE BOOK OF GRUDGES (plan 2026-10-04 phase 5). DW is a Dwarf court; SK an
-- enemy it has met whose army and settlements carry CA's grudge points.
local DW, SK = "wh_main_dwf_karak_kadrin", "wh2_main_skv_clan_skryre"
local GR, ZG, FAR = "wh_main_grn_greenskins", "wh_main_grn_orcs_of_the_bloody_hand",
                    "wh_main_grn_crooked_moon"

local function grudged(cqi, n)
    local man = make_character(cqi, ANY_SEAT, nil, nil)
    man._force, man._grudge = true, n
    return man
end

local function book_dump(list)
    local out = {}
    for _, e in ipairs(list) do out[#out + 1] = e.key .. "=" .. tostring(e.weight) end
    return "{" .. table.concat(out, ", ") .. "}"
end

-- A FRESH WORLD: no state, no save, no cache, no bonuses. SK's one army carries
-- `army` points, its settlements `regions` ({points, ...}), and a garrison 5000
-- the Book must never read. Returns SK's army, whose _grudge a check moves.
local function book_world(army, regions)
    IC.state = {}
    IC._book = nil
    bonuses = {}
    saved["derpy_ic_" .. DW] = nil
    local man = grudged(9401, army)
    local provs, pts = {}, {}
    for i, n in ipairs(regions or {}) do
        provs[i] = "sk_prov_" .. i
        pts[provs[i]] = n
    end
    local sk = make_faction(SK, "wh2_main_sc_skv_skaven", {man}, provs)
    sk._grudge_regions = pts
    sk._garrison_units, sk._garrison_grudge = {}, 5000
    local dw = make_faction(DW, IC.RACES.dwf.subculture,
                            {make_character(9410, ANY_SEAT, IC.CROWN)}, {"dw_prov"})
    dw._met = {SK}
    for _, p in ipairs({IC.CROWN, "legion", "temple", "forge"}) do IC.add_house(DW, p) end
    return man
end

check("book: the weight is CA's two pools on armies and settlements, never a garrison", function()
    book_world(300, {100, 0})
    turn = 20
    assert(IC.book_weight(DW, SK) == 400, "weight " .. tostring(IC.book_weight(DW, SK)))
    -- A SETTLEMENT WITH NO POOL is a null interface, not a zero.
    factions[SK]._grudge_regions = {}
    assert(IC.book_weight(DW, SK) == 300, "weight " .. tostring(IC.book_weight(DW, SK)))
    assert(IC.book_weight(DW, "no_such_faction") == 0, "a faction that is not there weighs something")
    assert(#IC_PARTY_FAULTS == 0, "the Book failed: " .. tostring(IC_PARTY_FAULTS[1]))
end)

check("book: names the heaviest it has met first, the top n, none at zero", function()
    book_world(600, {})
    make_faction(GR, "wh_main_sc_grn_greenskins", {grudged(9402, 900)}, {})
    make_faction(ZG, "wh_main_sc_grn_greenskins", {grudged(9403, 0)}, {})
    make_faction(FAR, "wh_main_sc_grn_greenskins", {grudged(9404, 5000)}, {})
    factions[DW]._met = {SK, GR, ZG}       -- FAR is never met
    turn = 30
    local top = IC.book_names(DW, 3)
    assert(#top == 2 and top[1].key == GR and top[1].weight == 900
           and top[2].key == SK and top[2].weight == 600, "the Book reads " .. book_dump(top))
    top = IC.book_names(DW, 1)
    assert(#top == 1 and top[1].key == GR, "the top one reads " .. book_dump(top))
    -- THE PANEL READS AND NEVER FILLS: what a machine holds must not depend on
    -- whether its player opened the court.
    assert(IC._book == nil, "a read filled the turn's cache")
    assert(#IC_PARTY_FAULTS == 0, "the Book failed: " .. tostring(IC_PARTY_FAULTS[1]))
end)
```

- [ ] **Step 3: Run to verify they fail**

Run: `$env:IC_ONLY = "book:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: `FAIL book: the weight is CA's two pools on armies and settlements, never a garrison: ...attempt to call field 'book_weight' (a nil value)`.

- [ ] **Step 4: Implement.** In `IC.TUNE`, after `deed_research = 2,`:

```lua
    deed_grudge         = 3,    -- a grudge settled (Dwarf courts; plan 2026-10-04 phase 5)
```

and after `renown_join_line = 15,`:

```lua

    -- THE BOOK OF GRUDGES (spec 2026-10-04 section 6), Dwarf courts only. Not
    -- on the MCT page. A line reached is a line crossed; book_penalty is CA's
    -- -6..+6 dilemma scale, one per band, in order.
    book_bands          = {500, 1000, 2000},
    book_penalty        = {-1, -2, -3},
    book_named          = 1000,  -- a treaty with a faction the Book names this high is a grudge
    book_top            = 3,     -- names on the Court tab
```

Directly above `function IC.turn(faction_key)`:

```lua
-- THE BOOK OF GRUDGES (spec 2026-10-04 section 6), Dwarf courts only. CA keeps
-- grudge points ON the offender's armies and settlements, in two pooled
-- resources (wh3_campaign_grudges.lua:129-131), not per Dwarf faction - so a
-- faction's weight is one number for every Dwarf court.
IC.BOOK_ARMY = "wh3_dlc25_dwf_grudge_points_enemy_armies"
IC.BOOK_SETTLEMENT = "wh3_dlc25_dwf_grudge_points_enemy_settlements"
IC.GRUDGE_POINTS = "wh3_dlc25_dwf_grudge_points"

-- ONE POOL, as CA reads it (remove_grudge_points_for_faction): 0 when the
-- entity has none, since resource() is "Null if not present".
local function book_pool(entity, key)
    local r = entity:pooled_resource_manager():resource(key)
    if r:is_null_interface() then return 0 end
    return r:value()
end

-- ARMIES, NOT GARRISONS (CA never writes points on armed citizenry), then
-- settlements.
local function book_sum(other)
    local total = 0
    local forces = other:military_force_list(true)
    for i = 0, forces:num_items() - 1 do
        total = total + book_pool(forces:item_at(i), IC.BOOK_ARMY)
    end
    local regions = other:region_list()
    for i = 0, regions:num_items() - 1 do
        total = total + book_pool(regions:item_at(i), IC.BOOK_SETTLEMENT)
    end
    return total
end

-- {turn = n, w = {[faction key] = weight}}: unsaved, and FILLED ON THE TURN PATH
-- ONLY (IC.book_list with fill, from IC.book_tick). The panel reads it and never
-- fills it, so what a machine holds never depends on its player opening the
-- court. ponytail: a faction is weighed at the first Dwarf court's turn start of
-- the round; points it gains later in the round count next turn.
IC._book = nil

-- faction_key is the court asking; the number does not depend on it (above).
function IC.book_weight(faction_key, other_key)
    local c = IC._book
    if c and c.turn == cm:model():turn_number() and c.w[other_key] then
        return c.w[other_key]
    end
    local other = real_faction(other_key)
    if not other then return 0 end
    local ok, w = pcall(book_sum, other)
    if not ok then
        IC.warn("IRON COURT: the Book failed to weigh " .. tostring(other_key) .. ": " .. tostring(w))
        return 0
    end
    return w
end

-- ONE MET FACTION: nil to skip it (null, dead, or a Dwarf - CA writes no points
-- on one), else its key and weight.
local function book_weigh(other, now, fill)
    if other:is_null_interface() or other:is_dead()
            or other:subculture() == IC.RACES.dwf.subculture then
        return nil
    end
    local key = other:name()
    local c = IC._book
    local w = c and c.turn == now and c.w[key]
    if not w then
        w = book_sum(other)
        if fill then c.w[key] = w end
    end
    return key, w
end

-- EVERY FACTION THIS COURT HAS MET that carries points, heaviest first, ties by
-- key so every machine sorts alike. `fill` = the turn path; the panel omits it.
function IC.book_list(faction_key, fill)
    local out = {}
    local own = real_faction(faction_key)
    if not own or IC.race_key(faction_key) ~= "dwf" then return out end
    local now = cm:model():turn_number()
    if fill and not (IC._book and IC._book.turn == now) then
        IC._book = {turn = now, w = {}}
    end
    local met = own:factions_met()
    for i = 0, met:num_items() - 1 do
        local ok, key, w = pcall(book_weigh, met:item_at(i), now, fill)
        if not ok then
            IC.warn("IRON COURT: the Book failed to weigh a faction met by "
                    .. faction_key .. ": " .. tostring(key))
        elseif key and w > 0 then
            out[#out + 1] = {key = key, weight = w}
        end
    end
    table.sort(out, function(a, b)
        if a.weight ~= b.weight then return a.weight > b.weight end
        return a.key < b.key
    end)
    return out
end

function IC.book_names(faction_key, n)
    local all, out = IC.book_list(faction_key), {}
    for i = 1, math.min(n or IC.TUNE.book_top, #all) do out[i] = all[i] end
    return out
end
```

- [ ] **Step 5: Run to verify they pass**

Run: `$env:IC_ONLY = "book:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: `iron court harness: ok (2 checks)`. Then the full harness: `iron court harness: ok (N checks)`, N = phase 4's count + 2 (the stub changes break no earlier check; if one fails, the stub change is wrong, not the check).

- [ ] **Step 6: Checkpoint.** Run THE GATES. Expected: all green.

### Task 2: The bands, field 20 and the turn

**Files:**
- Modify: `zzz_derpy_iron_court.lua` (`new_court` ~1140, `IC.pack` ~1557, `IC.unpack` ~1690, the Book block from Task 1, `IC.turn` ~6276)
- Test: `tools/_iron_court_harness.lua`

**Interfaces:**
- Consumes: `IC.book_list(fk, true)` (Task 1), phase 4's field 19 in `IC.pack`.
- Produces: `court.book = {[other_key] = bands crossed}`; `IC.book_tick(faction_key) -> number of bands fired`; save field 20; `IC.turn` calls `IC.book_tick` caught.

- [ ] **Step 1: Write the failing checks**

```lua
check("book: each band fires once, in order, and a fall takes none back", function()
    local man = book_world(499, {})
    turn = 40
    assert(IC.book_tick(DW) == 0 and #bonuses == 0, "499 crossed a band")
    man._grudge = 500
    turn = 41
    assert(IC.book_tick(DW) == 1, "500 did not cross the first band")
    assert(bonuses[1].a == DW and bonuses[1].b == SK and bonuses[1].n == IC.TUNE.book_penalty[1],
        "the first band applied (" .. tostring(bonuses[1].a) .. ", " .. tostring(bonuses[1].b)
        .. ", " .. tostring(bonuses[1].n) .. ")")
    -- THE TURN PATH FILLS THE CACHE, and a later court's read this turn is it.
    assert(IC._book and IC._book.turn == 41 and IC._book.w[SK] == 500, "the turn path filled no cache")
    man._grudge = 50
    assert(IC.book_weight(DW, SK) == 500, "a read this turn walked the map again")
    man._grudge = 500
    turn = 42
    assert(IC.book_tick(DW) == 0 and #bonuses == 1, "the first band fired twice")
    -- A JUMP PAST TWO BANDS fires both, once each, in order.
    man._grudge = 2400
    turn = 43
    assert(IC.book_tick(DW) == 2 and #bonuses == 3, #bonuses .. " bonuses after a jump")
    assert(bonuses[2].n == IC.TUNE.book_penalty[2] and bonuses[3].n == IC.TUNE.book_penalty[3],
        "the bands fired out of order")
    -- NEVER REVERSED: settled down to 100, nothing is applied and nothing is
    -- taken back, and the rise after it fires nothing again.
    man._grudge = 100
    turn = 44
    assert(IC.book_tick(DW) == 0 and #bonuses == 3, "a fall applied something")
    assert(IC.court(DW).book[SK] == #IC.TUNE.book_bands, "a fall took a band back")
    man._grudge = 2400
    turn = 45
    assert(IC.book_tick(DW) == 0 and #bonuses == 3, "a band fired again after a fall and a rise")
end)

check("book: the bands survive a save, and a 19-field save loads with none", function()
    book_world(1200, {})
    turn = 60
    assert(IC.book_tick(DW) == 2, "1200 did not cross two bands")
    IC.save(DW)
    IC.state = {}
    IC._book = nil
    IC.load(DW)
    assert(IC.court(DW).book[SK] == 2, "the bands were not saved")
    turn = 61
    assert(IC.book_tick(DW) == 0 and #bonuses == 2, "a load fired a band again")
    local fields = {}
    for field in string.gmatch(IC.pack(DW) .. "|", "([^|]*)|") do fields[#fields + 1] = field end
    assert(#fields == 20, #fields .. " fields")
    assert(fields[20] == SK .. ":2", "field 20 reads " .. fields[20])
    -- AN OLDER SAVE: the same court cut to its first 19 fields.
    IC.unpack(DW, table.concat(fields, "|", 1, 19))
    assert(next(IC.court(DW).book) == nil, "a 19-field save read bands out of nothing")
    -- A GARBLED ENTRY IS DROPPED and a count past the last band is the last band.
    IC.unpack(DW, table.concat(fields, "|", 1, 19) .. "|" .. SK .. ":9/junk")
    assert(IC.court(DW).book[SK] == #IC.TUNE.book_bands and IC.court(DW).book.junk == nil,
        "field 20 read garbage")
end)

check("book: a Dwarf court's turn reads the Book; a Chaos Dwarf court's never does", function()
    book_world(5000, {})
    turn = 70
    core.listeners["ic_turn"]({faction = function() return factions[DW] end})
    local hit = {}
    for _, b in ipairs(bonuses) do
        if b.b == SK then hit[#hit + 1] = b.n end
    end
    assert(#hit == 3 and hit[1] == IC.TUNE.book_penalty[1] and hit[3] == IC.TUNE.book_penalty[3],
        "a Dwarf court's turn applied " .. #hit .. " bands")
    assert(#IC_PARTY_FAULTS == 0, "the Book failed: " .. tostring(IC_PARTY_FAULTS[1]))
    -- A CHAOS DWARF COURT THAT HAS MET THE SAME FACTION.
    bonuses = {}
    saved["derpy_ic_" .. F] = nil
    IC.state[F] = nil
    make_faction(F, IC.CHD_SUBCULTURE, {make_character(11, ANY_SEAT, IC.CROWN)}, {"prov_a"})
    factions[F]._met = {SK}
    IC.add_house(F, IC.CROWN)
    assert(IC.book_tick(F) == 0 and #IC.book_names(F, 3) == 0, "a Chaos Dwarf court has a Book")
    core.listeners["ic_turn"]({faction = function() return factions[F] end})
    for _, b in ipairs(bonuses) do
        assert(b.b ~= SK, "a Chaos Dwarf court's turn applied a Book band")
    end
end)
```

- [ ] **Step 2: Run to verify they fail**

Run: `$env:IC_ONLY = "book:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: `FAIL book: each band fires once, in order, and a fall takes none back: ...attempt to call field 'book_tick' (a nil value)`.

- [ ] **Step 3: Implement.** In `new_court`, after `votes = {},`:

```lua
        -- THE BOOK (plan 2026-10-04 phase 5): [faction key] = bands crossed.
        book = {},
```

Append to the Book block (after `IC.book_names`):

```lua
-- THE BANDS (spec section 6): reaching book_bands[i] applies book_penalty[i]
-- ONCE, in order, never reversed. court.book[other] is how many are crossed,
-- saved in field 20, so a load never fires one again. (own, them): CA's five
-- calls put the actor first and the faction whose regard moves second, so it
-- is the named faction's regard for the court that falls.
function IC.book_tick(faction_key)
    local court = IC.court(faction_key)
    local bands, penalty = IC.TUNE.book_bands, IC.TUNE.book_penalty
    local fired = 0
    for _, e in ipairs(IC.book_list(faction_key, true)) do
        local had = court.book[e.key] or 0
        local n = had
        while n < #bands and e.weight >= bands[n + 1] do n = n + 1 end
        for i = had + 1, n do
            cm:apply_dilemma_diplomatic_bonus(faction_key, e.key, penalty[i])
            fired = fired + 1
        end
        if n > had then court.book[e.key] = n end
    end
    return fired
end
```

In `IC.pack`, directly before its `return join({`:

```lua
    -- THE BOOK (plan 2026-10-04 phase 5): field 20 is "faction:bands" per named
    -- faction, "/" between them.
    local book = {}
    for key, n in pairs(court.book or {}) do book[#book + 1] = key .. ":" .. tostring(n) end
    table.sort(book)
```

and in that `return join({...}, "|")` list, which phase 4 left ending with field 19 (the grudges), add `join(book, "/")` after field 19 as the last element, so the list has 20 entries.

In `IC.unpack`, directly before `IC.state[faction_key] = court`:

```lua
    -- Field 20 is optional: a save from before the Book has crossed no band. A
    -- count past the last band is the last band.
    for _, pair in ipairs(split(fields[20] or "", "/")) do
        local b = split(pair, ":")
        local n = tonumber(b[2])
        if b[1] and n and n >= 1 then
            court.book[b[1]] = math.min(n, #IC.TUNE.book_bands)
        end
    end
```

In `IC.turn`, directly before its final `IC.save(faction_key)`:

```lua
    -- THE BOOK (plan 2026-10-04 phase 5), caught and said like the parties'
    -- turn: a Book that fails must not cost the court its save.
    local ok_book, err_book = pcall(IC.book_tick, faction_key)
    if not ok_book then
        IC.warn("IRON COURT: the Book failed in " .. faction_key .. ": " .. tostring(err_book))
    end
```

- [ ] **Step 4: Run to verify they pass**

Run: `$env:IC_ONLY = "book:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: `iron court harness: ok (5 checks)`. Full harness: N + 5.

- [ ] **Step 5: Checkpoint.** Run THE GATES. Expected: all green.

### Task 3: A treaty with a named faction is a grudge

**Files:**
- Modify: `zzz_derpy_iron_court.lua` (the Book block; `IC.register` ~7021, after the `ic_turn` listener)
- Test: `tools/_iron_court_harness.lua`

**Interfaces:**
- Consumes: `IC.grudges(fk, slug)`, `IC.grudge_write(fk, slug, "peace")` (phase 4), `court.book` (Task 2), `IC.loaded`, `IC.runs_court`, `IC.save`.
- Produces: `IC.BOOK_WRONGED = {"legion", "temple"}`, `IC.in_book(faction_key, other_key) -> bool`, `IC.book_peace(faction_key, other_key) -> bool` (true when it wrote), listener `ic_book_peace`.

- [ ] **Step 1: Write the failing check**

```lua
check("book: a treaty with a faction named at 1000 is a grudge to the Clan Warriors and the Priesthood", function()
    local man = book_world(999, {})
    local function treaty(kind, proposer, recipient)
        local ctx = {proposer = function() return factions[proposer] end,
                     recipient = function() return factions[recipient] end}
        for _, k in ipairs({"is_peace_treaty", "is_trade_agreement", "is_alliance",
                            "is_military_alliance", "is_defensive_alliance",
                            "is_military_access", "is_non_aggression_pact",
                            "is_vassalage", "is_state_gift"}) do
            ctx[k] = function() return k == kind end
        end
        core.listeners["ic_book_peace"](ctx)
    end
    turn = 80
    IC.book_tick(DW)
    treaty("is_peace_treaty", DW, SK)
    assert(#IC.grudges(DW, "legion") == 0 and #IC.grudges(DW, "temple") == 0, "999 is named")
    man._grudge = 1000
    turn = 81
    IC.book_tick(DW)
    -- MILITARY ACCESS IS NO TREATY THE SPEC NAMES.
    treaty("is_military_access", SK, DW)
    assert(#IC.grudges(DW, "legion") == 0, "military access wrote a grudge")
    -- THE OTHER SIDE PROPOSING is the same wrong.
    treaty("is_trade_agreement", SK, DW)
    for _, p in ipairs({"legion", "temple"}) do
        local g = IC.grudges(DW, p)
        assert(#g == 1 and g[1].code == "peace" and g[1].turn == 81,
            p .. " has " .. #g .. " grudges")
    end
    assert(#IC.grudges(DW, "forge") == 0, "a third party was wronged")
    -- ONE WRONG A TURN: the same deal's second event writes nothing more.
    treaty("is_peace_treaty", DW, SK)
    assert(#IC.grudges(DW, "legion") == 1, "one deal wrote two grudges")
    -- AND IT WAS SAVED by the listener.
    IC.state = {}
    IC.load(DW)
    assert(#IC.grudges(DW, "legion") == 1, "the peace grudge was not saved")
    -- CA WIPES AN ALLY'S POINTS ON THIS SAME EVENT: the Book still names it.
    man._grudge = 0
    turn = 82
    treaty("is_alliance", DW, SK)
    assert(#IC.grudges(DW, "legion") == 2, "an alliance after CA's wipe wrote nothing")
    assert(#IC_PARTY_FAULTS == 0, "the Book failed: " .. tostring(IC_PARTY_FAULTS[1]))
end)
```

- [ ] **Step 2: Run to verify it fails**

Run: `$env:IC_ONLY = "book:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: `FAIL book: a treaty with a faction named at 1000 ...: ...attempt to call field 'ic_book_peace' (a nil value)`.

- [ ] **Step 3: Implement.** Append to the Book block:

```lua
-- A TREATY WITH A FACTION THE BOOK NAMES (spec section 6) wrongs these two.
IC.BOOK_WRONGED = {"legion", "temple"}

-- NAMED = THE SAVED BANDS reach book_named, not the live weight: CA's own
-- listener on the same event wipes an ally's points (wh3_campaign_grudges.lua,
-- remove_grudge_points_when_form_alliance_with_dwarfs), and which runs first is
-- not ours to know. IC.state, not IC.court: asking must never create a court.
function IC.in_book(faction_key, other_key)
    local n = ((IC.state[faction_key] or {}).book or {})[other_key] or 0
    return n > 0 and IC.TUNE.book_bands[n] >= IC.TUNE.book_named
end

-- A "peace" grudge in each wronged party's book, at most one each a turn: a
-- deal that is peace and trade at once is one wrong, however many events.
function IC.book_peace(faction_key, other_key)
    if IC.race_key(faction_key) ~= "dwf" then return false end
    IC.loaded(faction_key)
    if not IC.in_book(faction_key, other_key) then return false end
    local now = cm:model():turn_number()
    local wrote = false
    for _, slug in ipairs(IC.BOOK_WRONGED) do
        local again = false
        for _, g in ipairs(IC.grudges(faction_key, slug)) do
            if g.code == "peace" and g.turn == now then again = true end
        end
        if not again then
            IC.grudge_write(faction_key, slug, "peace")
            wrote = true
        end
    end
    return wrote
end
```

In `IC.register`, directly after the `ic_turn` listener:

```lua
    -- PEACE, TRADE OR AN ALLIANCE WITH A FACTION THE BOOK NAMES (spec 2026-10-04
    -- section 6), from either side of the table.
    core:add_listener("ic_book_peace", "PositiveDiplomaticEvent", true, function(context)
        local ok, err = pcall(function()
            if not (context:is_peace_treaty() or context:is_trade_agreement()
                    or context:is_alliance() or context:is_military_alliance()
                    or context:is_defensive_alliance()) then
                return
            end
            local a, b = context:proposer(), context:recipient()
            for _, pair in ipairs({{a, b}, {b, a}}) do
                local own, them = pair[1], pair[2]
                if IC.runs_court(own) and IC.book_peace(own:name(), them:name()) then
                    IC.save(own:name())
                end
            end
        end)
        if not ok then IC.warn("IRON COURT: the Book failed on a treaty: " .. tostring(err)) end
    end, true)
```

- [ ] **Step 4: Run to verify it passes**

Run: `$env:IC_ONLY = "book:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: `iron court harness: ok (6 checks)`. Full harness: N + 6.

- [ ] **Step 5: Checkpoint.** Run THE GATES. Expected: all green.

### Task 4: The grudge deed

**Files:**
- Modify: `zzz_derpy_iron_court.lua` (`IC.deed` ~1467; `IC.register`, after `on_deed("ic_deed_research", ...)` ~7175), `zzz_derpy_iron_court_dwarf.lua` (the dwf race table's `DEEDS = {`), the Dwarf deed text - THIS PHASE adds the `grudge` deed's line (no earlier phase writes it; phase 2 owns the other Dwarf deed lines in the dwf race's `EVENT_LOC`/deed text - `Select-String -Path "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court*.lua" -Pattern "DEED_TEXT|EVENT_LOC"` finds where they live, and the `grudge` line goes beside them), `tools/gen_iron_court.py` (`check_party_drawn`'s regex)
- Test: `tools/_iron_court_harness.lua`

**Interfaces:**
- Consumes: `on_deed` (local in `IC.register`), `IC.add_renown`, `IC.renown`, `IC.deeds_on`, `ICUI.deeds_tip(faction, court)`, `IC.GRUDGE_POINTS`, `IC.TUNE.deed_grudge` (Task 1).
- Produces: deed code `grudge` on the dwf race; the DEEDS field `also`; listener `ic_deed_grudge`.

- [ ] **Step 1: Write the failing check**

```lua
check("book: the faction's own grudge points rising is a deed for two parties; a fall is none", function()
    book_world(0, {})
    local saved_humans = cm.get_human_factions
    cm.get_human_factions = function() return {DW} end     -- deeds are the player's
    local function points(key, amount, faction_key)
        core.listeners["ic_deed_grudge"]({
            faction = function() return factions[faction_key or DW] end,
            has_faction = function() return true end,
            amount = function() return amount end,
            resource = function()
                return {is_null_interface = function() return false end,
                        key = function() return key end}
            end,
        })
    end
    turn = 90
    IC.fade_renown(DW)
    -- SPENDING THEM ON A RITUAL IS A FALL.
    points("wh3_dlc25_dwf_grudge_points", -200)
    assert(IC.renown(DW, "legion") == 0 and IC.renown(DW, "temple") == 0,
        "spending grudge points was a deed")
    points("wh3_dlc25_dwf_grudge_points_enemy_armies", 40)
    assert(IC.renown(DW, "legion") == 0, "another pool was a deed")
    points("wh3_dlc25_dwf_grudge_points", 120)
    assert(IC.renown(DW, "legion") == IC.TUNE.deed_grudge
           and IC.renown(DW, "temple") == IC.TUNE.deed_grudge,
        "a grudge settled gave legion " .. IC.renown(DW, "legion")
        .. " and temple " .. IC.renown(DW, "temple"))
    assert(IC.renown(DW, "forge") == 0, "a third party grew on a grudge")
    -- AND THE PANEL SAYS SO: both parties' deed text names it.
    local _, said = string.gsub(ICUI.deeds_tip(DW, IC.court(DW)) or "", "grudges settled", "")
    assert(said == 2, "the deeds tooltip names grudges settled " .. said .. " times")
    -- NOT A CHAOS DWARF DEED.
    saved["derpy_ic_" .. F] = nil
    IC.state[F] = nil
    make_faction(F, IC.CHD_SUBCULTURE, {make_character(11, ANY_SEAT, IC.CROWN)}, {"prov_a"})
    for _, p in ipairs({IC.CROWN, "legion", "temple"}) do IC.add_house(F, p) end
    cm.get_human_factions = function() return {F} end
    points("wh3_dlc25_dwf_grudge_points", 120, F)
    assert(IC.renown(F, "legion") == 0 and IC.renown(F, "temple") == 0,
        "a Chaos Dwarf court took a grudge deed")
    cm.get_human_factions = saved_humans
end)
```

- [ ] **Step 2: Run to verify it fails**

Run: `$env:IC_ONLY = "book:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: `FAIL book: the faction's own grudge points rising ...: ...attempt to call field 'ic_deed_grudge' (a nil value)`.

- [ ] **Step 3: Implement.** In the dwf race table's `DEEDS = {` (in `zzz_derpy_iron_court_dwarf.lua`), add:

```lua
        -- A GRUDGE SETTLED (spec 2026-10-04 section 8), for two parties.
        grudge   = {party = "legion", also = "temple", tune = "deed_grudge"},
```

In `IC.deed`, keep its first line as phase 1 left it (the race's DEEDS lookup) and replace the final `return IC.add_renown(...)` with:

```lua
    local n = IC.add_renown(faction_key, party, IC.TUNE[d.tune], code)
    -- A DEED FOR TWO PARTIES (plan 2026-10-04 phase 5): a grudge settled is the
    -- Clan Warriors' and the Ancestor Priesthood's both.
    if d.also then n = n + IC.add_renown(faction_key, d.also, IC.TUNE[d.tune], code) end
    return n
```

In `IC.register`, after `on_deed("ic_deed_research", ...)`:

```lua
    -- A GRUDGE SETTLED (spec 2026-10-04 section 8): CA pays the faction's own
    -- grudge points when one is (wh3_campaign_grudges.lua grudges_pr_key). A
    -- rise only: a ritual spends them, and that is no deed. The key first,
    -- because this event fires for every pooled resource on the map. A Chaos
    -- Dwarf court has no grudge deed, so IC.deed answers 0 for one.
    on_deed("ic_deed_grudge", "PooledResourceChanged", function(context)
        if context:resource():key() ~= IC.GRUDGE_POINTS or context:amount() <= 0 then
            return nil
        end
        return context:faction(), "grudge"
    end)
```

In the Dwarf deed text that `ICUI.deeds_tip` reads for a Dwarf court (phase 3's), set the two values:

```lua
    legion = "your victories and grudges settled",
    temple = "temples to the Ancestors and grudges settled",
```

In `tools/gen_iron_court.py` `check_party_drawn`, widen the party regex so a deed's second party must have its line too:

```python
    named = set(re.findall(r'(?:party|alt|also) = "(\w+)"', block.group(1))) if block else set()
```

- [ ] **Step 4: Run to verify it passes**

Run: `$env:IC_ONLY = "book:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: `iron court harness: ok (7 checks)`. Full harness: N + 7.

- [ ] **Step 5: Checkpoint.** Run THE GATES. Expected: all green (`gen_iron_court.py --check` included: the temple party already has a drawn line from the temple deed).

### Task 5: "The Book names:" on the Court tab

**Files:**
- Modify: `zzz_derpy_iron_court_ui.lua` (`ICUI.PANEL_XY` after `ic_gov_glow` ~365; after `function ICUI.draw_gov` ~4944; `ICUI.draw_court` after `ICUI.draw_gov(panel, faction, court)`; `ICUI.refresh` after `show(comp("ic_gov_glow", panel), false)` ~7790), `tools/gen_ic_ui.py` (after `PANEL_LAYOUT["ic_crown_box"]` ~944; `CUT_CELLS` ~3590), `tools/preview_iron_court.py` (the panel cell loop ~1553, the hidden set ~1327 and ~1438)
- Test: `tools/_iron_court_harness.lua`; `py tools\gen_ic_ui.py --check`; `py tools\make_ic_backdrop.py --check`; `py tools\preview_iron_court.py --race dwf`

**Interfaces:**
- Consumes: `IC.book_names` (Task 1), `IC.race_key`, `ICUI.fit_cut`, `ICUI.house_name`, `loc`, `comp`, `show`.
- Produces: component `ic_book` at `{48, 943, 866, 26}` (1920x1080 base); `ICUI.BOOK_LABEL`, `ICUI.BOOK_EMPTY`, `ICUI.book_tip(faction)`, `ICUI.draw_book(panel, faction)`; Python `BOOK_GAP`, `PANEL_LAYOUT["ic_book"]`, `CUT_CELLS["ic_book"]`.

- [ ] **Step 1: Write the failing check**

```lua
check("book: the Court tab names the Book's top three on a Dwarf court only", function()
    book_world(700, {})
    for i, key in ipairs({GR, ZG, FAR}) do
        make_faction(key, "wh_main_sc_grn_greenskins", {grudged(9420 + i, 1000 * i)}, {})
    end
    factions[DW]._met = {SK, GR, ZG, FAR}
    turn = 100
    with_fake_panel(function(panel)
        cm.get_human_factions = function() return {DW} end
        -- THE CUT IS NOT WHAT THIS CHECK IS ABOUT: a narrow stub face, so the
        -- three keys standing in for names all fit at any panel scale.
        panel.children.ic_book.text_px = 2
        ICUI.view = "court"
        ICUI.refresh()
        local line = panel.children.ic_book
        assert(line.visible, "a Dwarf court's Court tab has no Book line")
        -- THE HARNESS'S LOC IS EMPTY, so each name draws as its key.
        local text = line.text
        assert(string.find(text, ICUI.BOOK_LABEL, 1, true) == 1, "the line reads " .. text)
        local a, b, c = string.find(text, FAR, 1, true), string.find(text, ZG, 1, true),
                        string.find(text, GR, 1, true)
        assert(a and b and c and a < b and b < c, "not the top three, heaviest first: " .. text)
        assert(not string.find(text, SK, 1, true), "a fourth name was drawn: " .. text)
        assert(string.find(line.tooltip, "3000 grudge points", 1, true),
            "the tooltip carries no weights: " .. tostring(line.tooltip))
        assert(IC._book == nil, "drawing the panel filled the turn's cache")
        ICUI.view = "offices"
        ICUI.refresh()
        assert(not panel.children.ic_book.visible, "another tab left the Book on screen")
    end)
    saved["derpy_ic_" .. F] = nil
    IC.state[F] = nil
    make_faction(F, IC.CHD_SUBCULTURE, {make_character(11, ANY_SEAT, IC.CROWN)}, {"prov_a"})
    factions[F]._met = {SK}
    IC.add_house(F, IC.CROWN)
    with_fake_panel(function(panel)
        ICUI.view = "court"
        ICUI.refresh()
        assert(not panel.children.ic_book.visible, "a Chaos Dwarf court drew the Book")
    end)
end)
```

- [ ] **Step 2: Run to verify it fails**

Run: `$env:IC_ONLY = "book:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: `FAIL book: the Court tab names the Book's top three on a Dwarf court only: ...attempt to index local 'line' (a nil value)`.

- [ ] **Step 3: The generator.** In `tools/gen_ic_ui.py`, directly after `PANEL_LAYOUT["ic_crown_box"] = (COL_L_X, CROWN_Y, COL_W, CROWN_H)`:

```python
# THE BOOK OF GRUDGES (plan 2026-10-04 phase 5): "The Book names: ..." on a Dwarf
# court, one line under the Crown's box at the box's inner width. OUTSIDE the
# box so the Chaos Dwarf box keeps its height; the panel hides it on a Chaos
# Dwarf court and on every other tab. Cut to fit (CUT_CELLS): CA's three longest
# faction names run about 1,300px at BODY.
BOOK_GAP = 8
PANEL_LAYOUT["ic_book"] = (_CROWN_X, CROWN_Y + CROWN_H + BOOK_GAP,
                           _CROWN_RIGHT_X + _CROWN_RIGHT_W - _CROWN_X, _CTL_H)
```

and add `"ic_book": "ICUI.fit_cut",` to `CUT_CELLS`.

- [ ] **Step 4: The panel.** In `ICUI.PANEL_XY`, after `ic_gov_glow`:

```lua
    -- THE BOOK OF GRUDGES (plan 2026-10-04 phase 5): a Dwarf court's line,
    -- under the Crown's box. tools/gen_ic_ui.py derives it.
    ic_book          = {48, 943, 866, 26},
```

(If `py tools\gen_ic_ui.py --check` reports a different tuple for `ic_book` - phase 3 may have moved the Crown's box - copy the generator's.) After `function ICUI.draw_gov`:

```lua
-- THE BOOK OF GRUDGES (spec 2026-10-04 section 6), a Dwarf court only: the top
-- names cut to the line, each with its points in the tooltip. A read: it never
-- fills IC._book (multiplayer, see IC.book_list).
ICUI.BOOK_LABEL = "The Book names: "
ICUI.BOOK_EMPTY = "The Book names no enemy yet."

function ICUI.book_tip(faction)
    local b = IC.TUNE.book_bands
    return string.format("At %d, %d and %d grudge points their regard for you falls, once at each.\n"
        .. "Peace, trade or an alliance with a faction at %d or more is a grudge to %s and %s.",
        b[1], b[2], b[3], IC.TUNE.book_named,
        ICUI.house_name("legion", faction), ICUI.house_name("temple", faction))
end

function ICUI.draw_book(panel, faction)
    local line = comp("ic_book", panel)
    local on = IC.race_key(faction) == "dwf"
    show(line, on)
    if not on then return end
    local names, tip = {}, {}
    for i, e in ipairs(IC.book_names(faction, IC.TUNE.book_top)) do
        names[i] = loc("factions_screen_name_" .. e.key, e.key)
        tip[i] = string.format("%s: %d grudge points", names[i], e.weight)
    end
    ICUI.fit_cut(comp("ic_book", panel), #names > 0
                 and (ICUI.BOOK_LABEL .. table.concat(names, ", ")) or ICUI.BOOK_EMPTY)
    tip[#tip + 1] = ICUI.book_tip(faction)
    pcall(function() line:SetTooltipText(table.concat(tip, "\n"), "", true) end)
end
```

In `ICUI.draw_court`, after `ICUI.draw_gov(panel, faction, court)`: `ICUI.draw_book(panel, faction)`. In `ICUI.refresh`, after `show(comp("ic_gov_glow", panel), false)`:

```lua
        -- THE BOOK'S LINE: shown only by draw_book, hidden by name like the
        -- government's row.
        show(comp("ic_book", panel), false)
```

- [ ] **Step 5: Run the check, then write and check the UI**

Run: `$env:IC_ONLY = "book:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: `iron court harness: ok (8 checks)`.
Run: `py tools\gen_ic_ui.py` (no flag: writes the `.twui.xml` with `ic_book`), then `py tools\gen_ic_ui.py --check`, then `py tools\make_ic_backdrop.py --check`.
Expected: `ok: N files, M components` (one component more than before) and the backdrop check green. **If `make_ic_backdrop.py --check` reports `ic_book` below 4.5:1, STOP and show the author the figure**: re-dimming the backdrop moves all 82 measured cells, and a plate under the line is a design choice for the author.

- [ ] **Step 6: The preview.** In `tools/preview_iron_court.py`, add above `def cut_words(`:

```python
def book_line(ui):
    """THE BOOK'S HARD CASE (plan 2026-10-04 phase 5): the label off the Lua,
    then CA's three longest faction screen names out of the shipped loc - a
    picture of three short names answers nothing about a cut cell."""
    import read_vanilla_loc as L
    names = sorted((t for k, t in L.load("factions").items()
                    if k.startswith("factions_screen_name_")
                    and not k.startswith("factions_screen_name_when_rebels_")
                    and not t.startswith("{{")), key=len, reverse=True)[:3]
    label = re.search(r'ICUI\.BOOK_LABEL = "([^"]*)"', ui).group(1)
    return label + ", ".join(names)
```

Directly after the line `hidden = set(("ic_page_prev", "ic_page_lbl", "ic_page_next"))`, using the parsed `--race` value phase 3 added (its variable in `main`):

```python
    # THE BOOK'S LINE (plan 2026-10-04 phase 5): a Dwarf court's only.
    if race == "dwf":
        STRINGS["ic_book"] = book_line(ui)
    else:
        hidden.add("ic_book")
```

In the `if view != "court":` block, after the `ic_gov` guard:

```python
        if not re.search(r'show\(comp\("ic_book", panel\), false\)', ui):
            raise SystemExit("ICUI.refresh no longer hides ic_book by name on a "
                             "tab switch - re-read it before trusting this picture")
        hidden.add("ic_book")
```

In the panel cell loop, replace `s = STRINGS.get(name)` with the cut the Lua makes:

```python
        s = STRINGS.get(name)
        # A CUT CELL DRAWS CUT, as ICUI.fit_cut cuts it (CUT_CELLS).
        if s and name in G.CUT_CELLS:
            s = cut_words(lambda _s, _c=named[("panel", name)]: measure(panel, _c, _s), s, w)
```

Run: `py tools\preview_iron_court.py --check`, then `py tools\preview_iron_court.py --race dwf`, then `py tools\preview_iron_court.py` (Chaos Dwarf).
Expected: exit 0 each; the Dwarf court picture (in `.skilltree_cache/ui_preview/`, the court file phase 3's `--race dwf` writes) shows "The Book names: Crooked Moon Mutinous Gits Waaagh!, The Terrors of the..." under the Crown's box; the Chaos Dwarf `ic_court.png` has no line there.

- [ ] **Step 7: STOP - the author approves the picture.** Show the author the Dwarf court picture and the Chaos Dwarf one beside it. Do not go on to Task 6 until the author approves; a change the author asks for is made here and the picture drawn again.

- [ ] **Step 8: Checkpoint.** Run THE GATES. Expected: all green.

### Task 6: Mutants, build, deploy

**Files:**
- Modify: `tools/mutate_iron_court.py` (a Book block appended inside `MUTANTS`, before its closing `]`), `docs/sessions/HANDOFF_20261004_IRON_COURT_DWARFS_BOOK.md` (new), `docs/SESSION_INDEX.md` (one line)

**Interfaces:**
- Consumes: every name above.
- Produces: 11 mutants named `book: ...`.

- [ ] **Step 1: Write the mutants** (`M` = model, `U` = panel), each a plausible mistake:

```python
    # ---- the Book of Grudges (plan 2026-10-04 phase 5) --------------------
    ("book: a band fired every turn", M,
     """        for i = had + 1, n do""",
     """        for i = 1, n do"""),
    ("book: a band reversed on a fall", M,
     """        local n = had
        while n < #bands and e.weight >= bands[n + 1] do n = n + 1 end
        for i = had + 1, n do
            cm:apply_dilemma_diplomatic_bonus(faction_key, e.key, penalty[i])
            fired = fired + 1
        end
        if n > had then court.book[e.key] = n end""",
     """        local n = 0
        while n < #bands and e.weight >= bands[n + 1] do n = n + 1 end
        for i = had + 1, n do
            cm:apply_dilemma_diplomatic_bonus(faction_key, e.key, penalty[i])
            fired = fired + 1
        end
        for i = n + 1, had do
            cm:apply_dilemma_diplomatic_bonus(faction_key, e.key, -penalty[i])
        end
        court.book[e.key] = n"""),
    ("book: band threshold off by one", M,
     """        while n < #bands and e.weight >= bands[n + 1] do n = n + 1 end""",
     """        while n < #bands and e.weight > bands[n + 1] do n = n + 1 end"""),
    ("book: named threshold off by one", M,
     """    return n > 0 and IC.TUNE.book_bands[n] >= IC.TUNE.book_named""",
     """    return n > 0 and IC.TUNE.book_bands[n] > IC.TUNE.book_named"""),
    ("book: deed on a fall", M,
     """        if context:resource():key() ~= IC.GRUDGE_POINTS or context:amount() <= 0 then""",
     """        if context:resource():key() ~= IC.GRUDGE_POINTS then"""),
    ("book: a deed for one party", M,
     """    if d.also then n = n + IC.add_renown(faction_key, d.also, IC.TUNE[d.tune], code) end""",
     """"""),
    ("book: the panel fills the turn's cache", M,
     """    if fill and not (IC._book and IC._book.turn == now) then""",
     """    if not (IC._book and IC._book.turn == now) then"""),
    ("book: a Chaos Dwarf court reads the Book", M,
     """    if not own or IC.race_key(faction_key) ~= "dwf" then return out end""",
     """    if not own then return out end"""),
    ("book: garrisons weighed", M,
     """    local forces = other:military_force_list(true)""",
     """    local forces = other:military_force_list()"""),
    ("book: a treaty read off the live weight", M,
     """    if not IC.in_book(faction_key, other_key) then return false end""",
     """    if IC.book_weight(faction_key, other_key) < IC.TUNE.book_named then return false end"""),
    ("book: another tab keeps the Book line", U,
     """        show(comp("ic_book", panel), false)""",
     """"""),
```

- [ ] **Step 2: Run them**

Run: `py tools\mutate_iron_court.py --selftest`, then `py tools\mutate_iron_court.py "book:"`
Expected: `selftest ok: ...`, then `11 mutants, 0 unexplained`. A survivor means a missing assertion: add it to the owning task's check, watch it catch the mutant, re-run. Then re-run the generators, since the runner restores the source and not what it wrote: `py tools\gen_ic_ui.py`, `py tools\gen_iron_court.py`, then THE GATES.

- [ ] **Step 3: Build and deploy**

Run (RPFM open): `py tools\deploy_iron_court.py`; with the game running, `py tools\deploy_iron_court.py --wait` in the background.
Expected: every gate green inside the build, "deployed ... byte-identical to the build", a backup in `Modding Files/Backup/`. Read the live pack back with `py tools\read_pack_index.py` and confirm `IC.book_tick`, `ic_book_peace`, `ic_deed_grudge` and the `ic_book` component are in it.

- [ ] **Step 4: Docs.** Write `docs/sessions/HANDOFF_20261004_IRON_COURT_DWARFS_BOOK.md`: what was built, the rulings above, the gate results, and the in-game looks owed to phase 6 (a band firing - the named faction's attitude line on the diplomacy screen, and whether the regard moved on their side, ours or both; a treaty writing a grudge; a grudge settled giving both parties renown; the Book line at 1600x900 and 2560x1440). Add one line to `docs/SESSION_INDEX.md` pointing at it.

- [ ] **Step 5: Checkpoint.** Run THE GATES. Expected: all green.
