# Iron Court Governments Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. **The author chose Native execution** (superpowers:executing-plans, one fresh reviewer at the end).

**Goal:** Give every Chaos Dwarf court a government - one of six lore-backed types, each bending one court rule and carrying a small bundle - that starts from the house's own, drifts on the player's court toward the leading party's government through a Petitions-tab choice, and can be forced by the player for influence, loyalty and a cooldown.

**Architecture:** All model code goes in `zzz_derpy_iron_court.lua` as a data table `IC.GOVS` plus `IC.tune(faction_key, key)`, which answers the court's government override or `IC.TUNE[key]`; only the call sites of overridden keys switch to it. The government's state rides in court save field 14. The panel adds a government line and a Change Doctrine button to the Crown's box, a sixth mission-style picker, and a petition row kind; the generator adds six bundles, two events, loc and MCT entries.

**Tech Stack:** Lua 5.1 (game scripts), Python 3 generators (`tools/gen_iron_court.py`, `tools/gen_ic_ui.py`), the stub harness `tools/_iron_court_harness.lua`, the mutation runner `tools/mutate_iron_court.py`, RPFM for packing (`tools/deploy_iron_court.py`).

**Spec:** `docs/superpowers/specs/2026-10-02-iron-court-governments-design.md`

## Global Constraints

- No emojis anywhere (code, comments, docs, loc).
- Player-facing text: plain words. "influence", never "standing"; "party", never "house"; no cap/accrue/rep/AI/HUD jargon. Rule lines terse, CA style, no dashes in loc rule lines.
- Every model change the panel makes goes through `ICUI.send` -> `IC.MP_OPS` -> `IC.after_op` (multiplayer safe). The default of an unanswered choice happens in the model's turn, never in the panel.
- Lua 5.1 with the game's miscompile: in a function with over 255 constants, no number literal on the LEFT of an arithmetic operator (`py tools/check_lua_literal_left.py`).
- A model function never calls loc inside a turn handler (turn-1 CTD); names are resolved in the panel.
- Run every tool from the workspace root `G:\Modding for resources` (the mutation runner reports a false "harness not green" from `tools/`).
- Harness: `& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua` (stops on first failure); `IC_TEST_ALL=1` runs every check.
- Every new check is watched failing for its own reason before the code that passes it is written.
- Spec numbers (copied): drift share 30, balanced pull every 2 turns, pressure line 6, choice 3 turns, accept +10 / -10, hold 300 x (1 + holds), hold -8, force 400, force -15 / +5, cooldown 15, grace = `grace_turns`.

## Rulings against the spec

1. **The override values live in `IC.GOVS`, not in `IC.TUNE`.** A preset already moves the base numbers (`term_turns`, `influence_trickle`, `favour_*_cost`); an override relative to the base is written `{mul = x}` and follows the preset, so a second set of tunables would only drift from the first. The drift, choice and force numbers do live in `IC.TUNE`, and three of them (`gov_pressure_line`, `gov_hold_cost`, `gov_force_cost`) are in `IC.TUNE_ORDER`, the presets and the Custom page.
2. **Relative overrides where the base is a preset knob:** Conclave term `{mul = 0.6}` (10 -> 6), Forge trickle `{mul = 0.6}` (5 -> 3), Convoy gift and secure `{mul = 0.67}` (600 -> 402, 2500 -> 1675). Fixed values elsewhere, as the spec's table.
3. **Governments off means nothing at all**: no start assigned, no bundle, no override, no pressure, no choice. Turning it on assigns the start at the court's next turn.
4. **The harness runs with governments off by default** (`IC.governments_on` replaced by a harness switch `IC_GOVS_ON`), because its test faction `F` is Uzkulak, which starts on the Convoy Concern and would move every favour price the existing checks pin. Government checks set `IC_GOVS_ON = true` and clear it. One check restores the real function to test the setting itself.
5. **Influence is paid from the Crown's spare influence**: each Crown man's influence above his own office's bar, richest first, so paying never unseats anyone.
6. **The choice record carries the party that pushed it**, for the Record line and the Hold penalty; it never decides a lapse, since either party of the Convoy backs it. Field 14 has eight values.

## Review Focus

1. **A save from before governments** (no field 14): the court loads with no government, gets its start at its next turn, and is offered no choice that turn. Pinned in Task 3.
2. **Paying never unseats an officer**: Hold and Change Doctrine spend only influence above each man's seat bar, and refuse rather than dip into it. Pinned in Task 5.
3. **An unanswered choice settles identically on every machine**: the 3-turn default runs inside `IC.turn`, with no panel involved. Pinned in Task 5.
4. **The Governments setting turned off mid-campaign**: the bundle comes off, the overrides stop, a pending choice is dropped, at the next load or turn. Pinned in Task 3.
5. **The pushing party secedes or loses the lead while its choice waits**: the choice lapses with no effect, unless the other party of a two-party government still leads. Pinned in Task 5.

---

### Task 1: The government table and `IC.tune`

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua` (after `IC.TUNE_ORDER`/`IC.PRESETS`, around line 700; new TUNE keys inside `IC.TUNE`)
- Test: `tools/_iron_court_harness.lua` (append checks before the final summary)

**Interfaces:**
- Produces: `IC.GOV_ORDER` (array of six slugs), `IC.GOVS[slug] = {parties = {...}, over = {[tune key] = number | {mul = x}}}`, `IC.START_GOV[faction_key] = slug`, `IC.governments_on() -> bool`, `IC.gov_row(faction_key) -> row | nil`, `IC.tune(faction_key, key) -> value`, `IC.gov_for_party(slug) -> gov slug | nil`, `IC.gov_bundle(slug) -> "derpy_ic_gov_" .. slug`.

- [ ] **Step 1: Harness switch.** Directly after the harness loads the four shipped scripts (search `dofile` near the top of `tools/_iron_court_harness.lua`), add:

```lua
-- GOVERNMENTS OFF UNLESS A CHECK ASKS (plan 2026-10-02, ruling 4): F is
-- Uzkulak, which starts on the Convoy Concern, and its overrides would move
-- every favour price the checks before governments pin.
IC_REAL_GOVERNMENTS_ON = IC.governments_on
IC.governments_on = function() return IC_GOVS_ON == true end
```

(This errors until Step 4 defines `IC.governments_on`; write it with the checks in Step 2 and run them together.)

- [ ] **Step 2: Write the failing checks** (append to the harness):

```lua
check("governments: each override answers for its own court only", function()
    IC.state = {}
    IC_GOVS_ON = true
    make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a"})
    IC.add_house(F, IC.CROWN)
    IC.court(F).gov = "conclave"
    local other = "cr_chd_house_of_azeros"
    IC.state[other] = nil
    assert(IC.tune(F, "renew_wait") == 1, "the Conclave's re-seat wait is " .. tostring(IC.tune(F, "renew_wait")))
    assert(IC.tune(F, "term_turns") == math.floor(IC.TUNE.term_turns * 0.6 + 0.5),
        "the Conclave's term is " .. tostring(IC.tune(F, "term_turns")))
    assert(IC.tune(other, "renew_wait") == IC.TUNE.renew_wait, "a court with no government was overridden")
    assert(IC.tune(F, "secede_share") == IC.TUNE.secede_share, "a key no government names was overridden")
    -- A TABLE KNOB IS SCALED ENTRY BY ENTRY.
    IC.court(F).gov = "legion"
    local b = IC.tune(F, "battle_influence")
    assert(b.heroic_victory == math.floor(IC.TUNE.battle_influence.heroic_victory * 1.5 + 0.5),
        "the Legion's heroic victory is worth " .. tostring(b.heroic_victory))
    assert(IC.TUNE.battle_influence.heroic_victory == 50, "the override wrote into IC.TUNE itself")
    IC_GOVS_ON = nil
    assert(IC.tune(F, "battle_influence") == IC.TUNE.battle_influence, "governments off still overrode")
end)

check("governments: the table is whole and every party maps to at most one government", function()
    assert(#IC.GOV_ORDER == 6, #IC.GOV_ORDER .. " governments")
    local seen = {}
    for _, g in ipairs(IC.GOV_ORDER) do
        local row = IC.GOVS[g]
        assert(row and #row.parties >= 1 and next(row.over), g .. " is not a whole row")
        for _, p in ipairs(row.parties) do
            assert(not seen[p], p .. " backs two governments")
            assert(p ~= IC.CROWN and p ~= "hearth", g .. " is backed by " .. p .. ", which has no lore basis")
            seen[p] = g
        end
        for key in pairs(row.over) do
            assert(IC.TUNE[key] ~= nil, g .. " overrides " .. key .. ", which IC.TUNE does not have")
        end
    end
    assert(IC.gov_for_party("forge") == "forge" and IC.gov_for_party("ledger") == "convoy"
           and IC.gov_for_party(IC.CROWN) == nil and IC.gov_for_party("hearth") == nil,
        "the party map is wrong")
    for fk, g in pairs(IC.START_GOV) do
        assert(IC.GOVS[g], fk .. " starts on " .. tostring(g) .. ", which is no government")
        assert(IC.origin_for_faction(fk), fk .. " starts a government but is not a court faction")
    end
end)
```

- [ ] **Step 3: Run to verify they fail**

Run: `& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua`
Expected: FAIL at load, "attempt to index ... governments_on" or "attempt to call a nil value (field 'tune')".

- [ ] **Step 4: Implement.** In `IC.TUNE` (beside `grace_turns`), add:

```lua
    -- GOVERNMENTS (spec 2026-10-02 sections 5-7).
    gov_drift_share     = 30,   -- a rival this big pulls the government its way
    gov_balance_turns   = 2,    -- a court nobody leads drifts to the Conclave this slowly
    gov_pressure_line   = 6,    -- pressure that asks the player to choose
    gov_choice_turns    = 3,    -- an unanswered choice is Accept after this
    gov_accept_gain     = 10,
    gov_accept_loss     = -10,
    gov_hold_cost       = 300,  -- times one more than the holds so far
    gov_hold_loyalty    = -8,
    gov_force_cost      = 400,
    gov_force_loss      = -15,
    gov_force_gain      = 5,
    gov_force_cooldown  = 15,
```

and beside the other switches (`all_cards = true,`): `governments = true, gov_drift = true,`. Append to `IC.TUNE_ORDER` (at its end, so an older save reads defaults): `"governments", "gov_drift", "gov_pressure_line", "gov_hold_cost", "gov_force_cost",`. Add to each preset: gentle `gov_pressure_line = 8, gov_hold_cost = 200, gov_force_cost = 300,`; harsh `5, 400, 500`; ruthless `4, 500, 600` (same keys). Then after `IC.PRESETS`:

```lua
-- THE GOVERNMENTS (spec 2026-10-02-iron-court-governments-design.md section 3).
-- Lore: no king; the Sorcerer-Prophets sit in council, and the strongest voice
-- is the eldest. Each government bends ONE court rule: `over` names IC.TUNE
-- keys, a number replacing the value and {mul = x} scaling it (a table knob
-- entry by entry), rounded. Read through IC.tune, never IC.TUNE, wherever a key
-- here is read. No Crown and no Hearth government: no lore basis.
IC.GOV_ORDER = {"conclave", "priest", "forge", "legion", "chain", "convoy"}
IC.GOVS = {
    conclave = {parties = {"tower"},
                over = {term_turns = {mul = 0.6}, renew_wait = 1}},
    priest   = {parties = {"temple"},
                over = {rank_influence = 6, battle_influence = {mul = 0.75}}},
    forge    = {parties = {"forge"},
                over = {governor_income = 8, gov_rank_income_per = 1,
                        influence_trickle = {mul = 0.6}}},
    legion   = {parties = {"legion"},
                over = {battle_influence = {mul = 1.5}, loyalty_battle_won = 5,
                        influence_trickle = 0}},
    chain    = {parties = {"chain"},
                over = {plot_murder_cost = {mul = 0.65}, plot_purge_cost = {mul = 0.65},
                        plot_provoke_cost = {mul = 0.65}, plot_fail_loyalty = 20}},
    convoy   = {parties = {"road", "ledger"},
                over = {favour_gift_cost = {mul = 0.67}, favour_secure_cost = {mul = 0.67},
                        plot_embezzle_loyalty = 12}},
}

-- WHERE A HOUSE STARTS (spec section 4). A faction not here takes its court's
-- own at its first turn (IC.start_gov). Uzkulak and the Kraken are inference.
IC.START_GOV = {
    wh3_dlc23_chd_astragoth = "priest",
    wh3_dlc23_chd_conclave = "conclave",
    wh3_dlc23_chd_legion_of_azgorh = "legion",
    wh3_dlc23_chd_zhatan = "legion",
    cr_chd_house_of_khorakk = "chain",
    cr_chd_house_of_azeros = "forge",
    cr_chd_house_of_bzaark = "forge",
    cr_chd_snakebeards_artificers = "forge",
    cr_chd_fists_of_hashut = "legion",
    cr_chd_slaves_of_the_black_dwarf = "legion",
    cr_chd_house_of_baal = "priest",
    cr_chd_horns_of_hashut = "priest",
    cr_chd_warfleet_of_uzkulak = "convoy",
    cr_chd_black_kraken_armada = "convoy",
}

function IC.governments_on() return IC.TUNE.governments ~= false end

function IC.gov_bundle(slug) return "derpy_ic_gov_" .. slug end

function IC.gov_for_party(slug)
    for _, g in ipairs(IC.GOV_ORDER) do
        for _, p in ipairs(IC.GOVS[g].parties) do
            if p == slug then return g end
        end
    end
    return nil
end

-- IC.state, not IC.court: asking a price must never create a court.
function IC.gov_row(faction_key)
    if not IC.governments_on() then return nil end
    local court = faction_key and IC.state[faction_key]
    return court and IC.GOVS[court.gov or ""] or nil
end

function IC.tune(faction_key, key)
    local base = IC.TUNE[key]
    local row = IC.gov_row(faction_key)
    local o = row and row.over[key]
    if o == nil then return base end
    if type(o) == "number" then return o end
    if type(base) == "table" then
        local out = {}
        for k, v in pairs(base) do out[k] = math.floor(v * o.mul + 0.5) end
        return out
    end
    return math.floor(base * o.mul + 0.5)
end
```

- [ ] **Step 5: Run to verify they pass**

Run: `& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua`
Expected: `iron court harness: ok (864 checks)`.

### Task 2: Read every overridden knob through `IC.tune`

**Files:**
- Modify: `zzz_derpy_iron_court.lua`, `zzz_derpy_iron_court_ui.lua`, `zzz_derpy_iron_court_parties.lua`, `zzz_derpy_iron_court_ui_map.lua` (every read of an overridden key)
- Test: `tools/_iron_court_harness.lua`

**Interfaces:**
- Consumes: `IC.tune`, `IC.GOVS` (Task 1).
- Produces: `IC.plot_cost(key, faction_key)` and `IC.favour_cost(key, faction_key)` (new optional second argument; nil faction answers the base price).

- [ ] **Step 1: Write the failing checks**

```lua
check("governments: no overridden knob is read straight off IC.TUNE", function()
    -- THE ONE WAY AN OVERRIDE SILENTLY DOES NOTHING: a read left on IC.TUNE.
    local keys = {}
    for _, g in ipairs(IC.GOV_ORDER) do
        for key in pairs(IC.GOVS[g].over) do keys[key] = true end
    end
    local dir = "Modding Files/pack/script/campaign/mod/"
    for _, file in ipairs({"zzz_derpy_iron_court.lua", "zzz_derpy_iron_court_ui.lua",
                           "zzz_derpy_iron_court_parties.lua", "zzz_derpy_iron_court_ui_map.lua"}) do
        local fh = assert(io.open(dir .. file, "r"))
        local text = fh:read("*a")
        fh:close()
        for key in pairs(keys) do
            assert(not string.find(text, "IC%.TUNE%." .. key .. "[^%w_]"),
                file .. " still reads IC.TUNE." .. key)
        end
    end
end)

check("governments: the Slave-Lords' plots and the Convoy's favours are priced by the court", function()
    IC.state = {}
    IC_GOVS_ON = true
    make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a"})
    IC.add_house(F, IC.CROWN)
    IC.court(F).gov = "chain"
    assert(IC.plot_cost("murder", F) == math.floor(IC.TUNE.plot_murder_cost * 0.65 + 0.5),
        "murder costs " .. tostring(IC.plot_cost("murder", F)))
    assert(IC.plot_cost("murder") == IC.TUNE.plot_murder_cost, "no court named still discounted")
    IC.court(F).gov = "convoy"
    assert(IC.favour_cost("gift", F) == math.floor(IC.TUNE.favour_gift_cost * 0.67 + 0.5),
        "a gift costs " .. tostring(IC.favour_cost("gift", F)))
    IC_GOVS_ON = nil
end)
```

- [ ] **Step 2: Run to verify they fail**

Run: harness. Expected: FAIL "zzz_derpy_iron_court.lua still reads IC.TUNE.term_turns" (or another key).

- [ ] **Step 3: Implement.** List the sites:

Run: `grep -n "IC\.TUNE\.\(term_turns\|renew_wait\|rank_influence\|battle_influence\|governor_income\|gov_rank_income_per\|influence_trickle\|loyalty_battle_won\|plot_fail_loyalty\|favour_gift_cost\|favour_secure_cost\|plot_embezzle_loyalty\|plot_murder_cost\|plot_purge_cost\|plot_provoke_cost\)\b" "Modding Files/pack/script/campaign/mod/"zzz_derpy_iron_court*.lua`

Replace each `IC.TUNE.<key>` with `IC.tune(<faction>, "<key>")`, where `<faction>` is the faction variable in scope (`faction_key` in the model, `faction` or `ICUI.player()` in the panel). A site with no faction in scope reads the player's: `IC.tune(ICUI.player(), "<key>")` in the panel. Then change the two price helpers:

```lua
function IC.plot_cost(key, faction_key)
    local plot = IC.plot_by_key(key)
    -- A PARTY-ONLY MOVE has no IC.PLOTS row; its price is on the tune.
    if not plot then return IC.tune(faction_key, "plot_" .. tostring(key) .. "_cost") or 0 end
    return IC.tune(faction_key, plot.cost) or 0
end
```

`IC.favour_cost(key)` the same way (read it first: `grep -n "^function IC.favour_cost" -A6 zzz_derpy_iron_court.lua`), with `IC.tune(faction_key, ...)` for its `IC.TUNE[...]`. Then pass the faction at every caller: `grep -n "IC.plot_cost(\|IC.favour_cost(" "Modding Files/pack/script/campaign/mod/"zzz_derpy_iron_court*.lua` (13 plot sites today) - each gets its in-scope faction as the second argument.

- [ ] **Step 4: Run to verify they pass, and nothing else moved**

Run: `$env:IC_TEST_ALL=1; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua`
Expected: `ok (866 checks)`. Governments are off in the harness, so every pre-existing price check still passes; a failure there is a call site given the wrong faction.

### Task 3: Saved state, start, bundle and the off switch

**Files:**
- Modify: `zzz_derpy_iron_court.lua`: `new_court` (~line 885), `IC.pack` (the final `join({...}, "|")`, ~line 1269), `IC.unpack` (after field 13, ~line 1418), `IC.settle_switches` (~line 858), `IC.turn` (~line 5205), `IC.LOG_KINDS`.
- Test: harness.

**Interfaces:**
- Consumes: Task 1.
- Produces: court fields `gov` (slug|nil), `gov_pressure` (int), `gov_toward` (slug|nil), `gov_cool` (turn), `gov_holds` (int), `gov_ask` ({gov, ends, party}|nil); `IC.start_gov(faction_key) -> slug`, `IC.gov_top(faction_key) -> slug|nil, share`, `IC.apply_gov_bundle(faction_key) -> slug|nil`, `IC.gov_step(faction_key)` (called by `IC.turn`; Task 4 fills in the drift).

- [ ] **Step 1: Write the failing checks**

```lua
check("governments: a house starts on its own, any other on its leading party's", function()
    IC_GOVS_ON = true
    IC.state = {}
    turn = 1
    make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "forge")
    IC.gov_step(F)
    assert(IC.court(F).gov == "convoy", "Uzkulak started on " .. tostring(IC.court(F).gov))
    -- NO LORE BASIS: the leading rival's government.
    local S = "cr_chd_skullstack"
    IC.state[S] = nil
    make_faction(S, IC.CHD_SUBCULTURE, {}, {"prov_b"})
    IC.add_house(S, IC.CROWN)
    IC.add_house(S, "forge")
    IC.add_house(S, "legion")
    IC.court(S).houses.forge.weight = 40
    IC.court(S).houses.legion.weight = 10
    IC.gov_step(S)
    assert(IC.court(S).gov == "forge", "Skullstack started on " .. tostring(IC.court(S).gov))
    -- NOBODY WITH A GOVERNMENT LEADS: the Conclave.
    IC.state[S] = nil
    IC.add_house(S, IC.CROWN)
    IC.add_house(S, "hearth")
    IC.court(S).houses.hearth.weight = 40
    IC.gov_step(S)
    assert(IC.court(S).gov == "conclave", "a Hearth-led court started on " .. tostring(IC.court(S).gov))
    assert(applied[IC.gov_bundle("conclave")], "its bundle was not applied")
    IC_GOVS_ON = nil
end)

check("governments: the state survives a save, and an older save starts afresh", function()
    IC_GOVS_ON = true
    IC.state = {}
    make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a"})
    IC.add_house(F, IC.CROWN)
    local court = IC.court(F)
    court.gov, court.gov_pressure, court.gov_toward = "forge", 4, "legion"
    court.gov_cool, court.gov_holds = 30, 2
    court.gov_ask = {gov = "legion", ends = 12, party = "legion"}
    IC.save(F)
    IC.state = {}
    local back = IC.load(F)
    assert(back.gov == "forge" and back.gov_pressure == 4 and back.gov_toward == "legion"
           and back.gov_cool == 30 and back.gov_holds == 2, "the government did not survive a save")
    assert(back.gov_ask and back.gov_ask.gov == "legion" and back.gov_ask.ends == 12
           and back.gov_ask.party == "legion", "the pending choice did not survive a save")
    -- A SAVE FROM BEFORE: thirteen fields.
    local packed = saved["derpy_ic_" .. F]
    local old = string.match(packed, "^(.*)|[^|]*$")
    IC.unpack(F, old)
    assert(IC.court(F).gov == nil and (IC.court(F).gov_pressure or 0) == 0 and IC.court(F).gov_ask == nil,
        "an older save read a government out of nothing")
    IC_GOVS_ON = nil
end)

check("governments: the setting off takes the bundle away and drops a waiting choice", function()
    IC.state = {}
    IC_GOVS_ON = true
    make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a"})
    IC.add_house(F, IC.CROWN)
    IC.court(F).gov = "forge"
    IC.court(F).gov_ask = {gov = "legion", ends = 99, party = "legion"}
    IC.apply_gov_bundle(F)
    assert(applied[IC.gov_bundle("forge")], "the fixture wore no bundle")
    IC_GOVS_ON = false
    IC.settle_switches(F)
    assert(not applied[IC.gov_bundle("forge")], "the setting off left the bundle on")
    assert(IC.court(F).gov_ask == nil, "the setting off left a choice waiting")
    assert(IC.tune(F, "governor_income") == IC.TUNE.governor_income, "the setting off left the override on")
    IC_GOVS_ON = nil
end)

check("governments: the real setting is IC.TUNE.governments", function()
    local was = IC.governments_on
    IC.governments_on = IC_REAL_GOVERNMENTS_ON
    local saved_v = IC.TUNE.governments
    IC.TUNE.governments = false
    assert(IC.governments_on() == false, "the setting off reads on")
    IC.TUNE.governments = true
    assert(IC.governments_on() == true, "the setting on reads off")
    IC.TUNE.governments = saved_v
    IC.governments_on = was
end)
```

- [ ] **Step 2: Run to verify they fail**

Expected: FAIL "attempt to call field 'gov_step' (a nil value)".

- [ ] **Step 3: Implement.** In `new_court()` add `gov_pressure = 0, gov_cool = 0, gov_holds = 0,` (gov, gov_toward, gov_ask stay nil). In `IC.pack`, before the final `return join({...`, add:

```lua
    -- THE GOVERNMENT (spec 2026-10-02 section 8): "-" for nothing, as above.
    local ask = court.gov_ask
    local gov = string.format("%s,%d,%s,%d,%d,%s,%d,%s", court.gov or "-",
        court.gov_pressure or 0, court.gov_toward or "-", court.gov_cool or 0,
        court.gov_holds or 0, ask and ask.gov or "-", ask and ask.ends or 0,
        ask and ask.party or "-")
```

and append `gov` as the 14th element of the joined list (after `join(sent, ";")`). In `IC.unpack`, after field 13:

```lua
    -- Field 14 is optional: a save from before governments has none, and the
    -- court takes its start at its next turn (spec 2026-10-02 section 8).
    local g = split(fields[14] or "", ",")
    court.gov = IC.GOVS[g[1] or ""] and g[1] or nil
    court.gov_pressure = tonumber(g[2]) or 0
    court.gov_toward = IC.GOVS[g[3] or ""] and g[3] or nil
    court.gov_cool = tonumber(g[4]) or 0
    court.gov_holds = tonumber(g[5]) or 0
    if IC.GOVS[g[6] or ""] then
        court.gov_ask = {gov = g[6], ends = tonumber(g[7]) or 0,
                         party = (g[8] and g[8] ~= "-") and g[8] or nil}
    end
```

Add the model functions (after `IC.apply_control_bundle`):

```lua
-- THE PARTY THAT LEADS THE COURT, Crown included, and its share. Ties go to
-- the first in IC.present_houses' order, the same on every machine.
function IC.gov_top(faction_key)
    local top, best = nil, -1
    for _, slug in ipairs(IC.present_houses(faction_key)) do
        local s = IC.share(faction_key, slug)
        if s > best then top, best = slug, s end
    end
    return top, math.max(best, 0)
end

-- WHERE A COURT STARTS: its house's own, else its strongest rival's, else the
-- Conclave - lore's own picture of Chaos Dwarf rule with nobody leading.
function IC.start_gov(faction_key)
    if IC.START_GOV[faction_key] then return IC.START_GOV[faction_key] end
    local best, best_share = nil, -1
    for _, slug in ipairs(IC.present_houses(faction_key)) do
        if slug ~= IC.CROWN then
            local s = IC.share(faction_key, slug)
            if s > best_share then best, best_share = slug, s end
        end
    end
    return (best and IC.gov_for_party(best)) or "conclave"
end

function IC.apply_gov_bundle(faction_key)
    local want = IC.governments_on() and IC.court(faction_key).gov or nil
    for _, g in ipairs(IC.GOV_ORDER) do
        cm:remove_effect_bundle(IC.gov_bundle(g), faction_key)
    end
    if want then cm:apply_effect_bundle(IC.gov_bundle(want), faction_key, -1) end
    return want
end

-- ONCE A TURN, every court: the start, then (player courts) the drift.
function IC.gov_step(faction_key)
    if not IC.governments_on() then return IC.apply_gov_bundle(faction_key) end
    local court = IC.court(faction_key)
    if not court.gov then court.gov = IC.start_gov(faction_key) end
    if IC.gov_turn then IC.gov_turn(faction_key) end
    return IC.apply_gov_bundle(faction_key)
end
```

In `IC.settle_switches`, add: `if not IC.governments_on() then IC.court(faction_key).gov_ask = nil; IC.apply_gov_bundle(faction_key) end`. In `IC.turn`, add `IC.gov_step(faction_key)` on the line before `IC.tick_pressure(faction_key)`. In `IC.LOG_KINDS` add `gov = true, gov_ask = true, gov_hold = true, gov_force = true, gov_lapse = true,`.

- [ ] **Step 4: Run to verify they pass**

Expected: `ok (870 checks)` with `IC_TEST_ALL=1`.

### Task 4: Drift (player courts)

**Files:**
- Modify: `zzz_derpy_iron_court.lua` (after `IC.gov_step`).
- Test: harness.

**Interfaces:**
- Consumes: Task 3 (`IC.gov_top`, court fields), `IC.grace_left()`, `IC.is_human`, `IC.feed`, `IC.log`.
- Produces: `IC.gov_pull(faction_key) -> want slug|nil, top slug|nil, step int`; `IC.gov_turn(faction_key)`; event slug `gov_pressure` (Task 7 adds its row).

- [ ] **Step 1: Write the failing checks**

```lua
local GOV_HUMANS = cm.get_human_factions
local function gov_done()
    IC_GOVS_ON = nil
    cm.get_human_factions = GOV_HUMANS
end

local function gov_court(weights, gov)
    IC.state = {}
    IC_GOVS_ON = true
    turn = IC.TUNE.grace_turns + 5
    cm.get_human_factions = function() return {F} end
    make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a"})
    for slug, w in pairs(weights) do
        IC.add_house(F, slug)
        IC.court(F).houses[slug].weight = w
    end
    IC.court(F).gov = gov or "convoy"
    return IC.court(F)
end

check("governments: a leading rival builds pressure toward its own, and a new leader restarts it", function()
    local court = gov_court({crown = 10, forge = 60, legion = 10})
    IC.gov_turn(F)
    assert(court.gov_toward == "forge" and court.gov_pressure == 1, "pressure "
        .. tostring(court.gov_pressure) .. " toward " .. tostring(court.gov_toward))
    IC.gov_turn(F)
    assert(court.gov_pressure == 2, "the second turn built " .. court.gov_pressure)
    court.houses.forge.weight, court.houses.legion.weight = 10, 60
    IC.gov_turn(F)
    assert(court.gov_toward == "legion" and court.gov_pressure == 1, "a new leader did not restart the count")
    gov_done()
end)

check("governments: the Crown or the Hearth leading builds nothing and resets nothing", function()
    local court = gov_court({crown = 60, forge = 15})
    court.gov_toward, court.gov_pressure = "forge", 3
    IC.gov_turn(F)
    assert(court.gov_pressure == 3 and court.gov_toward == "forge", "the Crown leading moved the pressure")
    court.houses.hearth = nil
    IC.add_house(F, "hearth")
    court.houses.hearth.weight = 200
    IC.gov_turn(F)
    assert(court.gov_pressure == 3, "the Hearth leading moved the pressure")
    gov_done()
end)

check("governments: a court nobody leads drifts to the Conclave, slowly", function()
    -- THE CROWN SMALLEST, so a rival leads, and no rival at the drift share.
    local court = gov_court({crown = 10, forge = 22, legion = 22, chain = 23, temple = 23})
    for _ = 1, 4 do
        turn = turn + 1
        IC.gov_turn(F)
    end
    assert(court.gov_toward == "conclave", "a balanced court pulled toward " .. tostring(court.gov_toward))
    assert(court.gov_pressure == 2, "four balanced turns built " .. tostring(court.gov_pressure))
    gov_done()
end)

check("governments: no drift in the grace period, in a cooldown, for the AI, or with drift off", function()
    local court = gov_court({crown = 10, forge = 60})
    turn = 1
    IC.gov_turn(F)
    assert(court.gov_pressure == 0, "pressure in the grace period")
    turn = IC.TUNE.grace_turns + 5
    court.gov_cool = turn + 3
    IC.gov_turn(F)
    assert(court.gov_pressure == 0, "pressure in a cooldown")
    court.gov_cool = 0
    cm.get_human_factions = function() return {} end
    IC.gov_turn(F)
    assert(court.gov_pressure == 0, "an AI court drifted")
    cm.get_human_factions = function() return {F} end
    IC.TUNE.gov_drift = false
    IC.gov_turn(F)
    IC.TUNE.gov_drift = true
    assert(court.gov_pressure == 0, "drift off still drifted")
    gov_done()
end)

check("governments: at the line the court asks, once", function()
    local court = gov_court({crown = 10, forge = 60})
    for _ = 1, IC.TUNE.gov_pressure_line do IC.gov_turn(F) end
    assert(court.gov_ask and court.gov_ask.gov == "forge" and court.gov_ask.party == "forge",
        "no choice at the line")
    assert(court.gov_ask.ends == turn + IC.TUNE.gov_choice_turns, "the choice ends " .. court.gov_ask.ends)
    local p = court.gov_pressure
    IC.gov_turn(F)
    assert(court.gov_pressure == p, "pressure kept building over a waiting choice")
    gov_done()
end)
```

- [ ] **Step 2: Run to verify they fail**

Expected: FAIL "attempt to call field 'gov_turn' (a nil value)".

- [ ] **Step 3: Implement**

```lua
-- WHAT THE COURT IS PULLING TOWARD NOW, ignoring the clock: the leading
-- rival's government at gov_drift_share, the Conclave when no rival is that
-- big, nothing when the Crown leads or the leader has no government. `step` is
-- this turn's pressure: the Conclave's pull comes every gov_balance_turns.
function IC.gov_pull(faction_key)
    local top, share = IC.gov_top(faction_key)
    if not top or top == IC.CROWN then return nil, top, 0 end
    if share >= IC.TUNE.gov_drift_share then
        return IC.gov_for_party(top), top, 1
    end
    local now = cm:model():turn_number()
    return "conclave", nil, (now % IC.TUNE.gov_balance_turns == 0) and 1 or 0
end

function IC.gov_drift_on(faction_key)
    return IC.governments_on() and IC.TUNE.gov_drift ~= false
        and IC.is_human(faction_key) and IC.grace_left() == 0
end

-- THE DRIFT (spec section 5). Player courts only; frozen in the grace period,
-- a cooldown, or while a choice waits.
function IC.gov_turn(faction_key)
    local court = IC.court(faction_key)
    if IC.gov_expire then IC.gov_expire(faction_key) end
    local now = cm:model():turn_number()
    if not IC.gov_drift_on(faction_key) or now < (court.gov_cool or 0)
       or court.gov_ask then
        return false
    end
    local want, top, step = IC.gov_pull(faction_key)
    if not want or want == court.gov then return false end
    if court.gov_toward ~= want then court.gov_toward, court.gov_pressure = want, 0 end
    court.gov_pressure = (court.gov_pressure or 0) + step
    if court.gov_pressure >= IC.TUNE.gov_pressure_line then
        court.gov_ask = {gov = want, ends = now + IC.TUNE.gov_choice_turns, party = top}
        IC.log(faction_key, "gov_ask", top, want, court.gov_pressure)
        IC.feed(faction_key, "gov_pressure")
    end
    return true
end
```

Note the Hearth case: `IC.gov_for_party("hearth")` is nil, so `want` is nil and nothing moves.

- [ ] **Step 4: Run to verify they pass**

Expected: `ok (875 checks)`. (`IC.feed` with an unknown slug returns false until Task 7 adds the event: harmless.)

### Task 5: The choice - Accept, Hold, the default and the lapse; the Crown's purse

**Files:**
- Modify: `zzz_derpy_iron_court.lua` (after `IC.gov_turn`; `IC.crown_purse` after `IC.member_weight`, where `real_faction` is in scope; the MP ops after `IC.MP_OPS.fill`).
- Test: harness.

**Interfaces:**
- Consumes: Tasks 3-4, `IC.move_loyalty`, `IC.office_by_slug`, `IC.tier_influence`, `IC.house_of_character`, `IC.standing`.
- Produces: `IC.crown_purse(faction_key) -> total, men` (men = `{cqi, spare}` richest first), `IC.spend_crown(faction_key, cost) -> ok, short`, `IC.gov_change(faction_key, to, gain, loss, kind)`, `IC.gov_accept(faction_key) -> ok, why`, `IC.gov_hold_price(faction_key) -> int`, `IC.gov_hold(faction_key) -> ok, why, short`, `IC.gov_expire(faction_key) -> "accepted"|"lapsed"|nil`; MP ops `gov_accept`, `gov_hold`.

- [ ] **Step 1: Write the failing checks**

```lua
local function gov_purse_court()
    local court = gov_court({crown = 10, forge = 60})
    local f = IC.court(F)
    local rich = make_character(901, ANY_SEAT, IC.CROWN)
    local seated = make_character(902, ANY_SEAT, IC.CROWN)
    make_faction(F, IC.CHD_SUBCULTURE, {rich, seated}, {"prov_a"})
    -- 902 HOLDS A TIER-4 SEAT: its bar is not his to spend; 100 above it is.
    local office = nil
    for _, o in ipairs(IC.OFFICES) do if o.tier == 4 then office = o break end end
    court.offices[office.slug] = 902
    local bar = IC.tier_influence(4)
    court.standing[901], court.standing[902] = 250, bar + 100
    return court, bar
end

check("governments: the purse is the Crown's spare influence, never a seat's bar", function()
    local court, bar = gov_purse_court()
    local total, men = IC.crown_purse(F)
    assert(total == 350, "the purse holds " .. total)
    assert(#men == 2 and men[1].cqi == 901 and men[2].cqi == 902, "not richest first")
    local ok, short = IC.spend_crown(F, total + 1)
    assert(not ok and short == 1 and court.standing[902] == bar + 100, "an overdraft was paid, or touched a bar")
    assert(IC.spend_crown(F, total), "the whole purse was refused")
    assert(court.standing[902] == bar and court.standing[901] == 0, "a seat's bar was spent: "
        .. court.standing[902])
    gov_done()
end)

check("governments: Accept changes the government and moves both parties' loyalty", function()
    local court = gov_court({crown = 10, forge = 60, road = 10})
    court.gov_ask = {gov = "forge", ends = turn + 3, party = "forge"}
    local f0, r0 = court.houses.forge.loyalty, court.houses.road.loyalty
    assert(IC.gov_accept(F), "Accept refused")
    assert(court.gov == "forge" and court.gov_ask == nil and court.gov_pressure == 0, "not changed")
    assert(court.houses.forge.loyalty == math.min(100, f0 + IC.TUNE.gov_accept_gain), "the new party gained nothing")
    assert(court.houses.road.loyalty == math.max(0, r0 + IC.TUNE.gov_accept_loss), "the old party lost nothing")
    assert(applied[IC.gov_bundle("forge")] and not applied[IC.gov_bundle("convoy")], "the bundle did not follow")
    gov_done()
end)

check("governments: Hold costs more each time, halves the pressure and angers the pusher", function()
    local court = gov_purse_court()
    court.standing[901] = 5000
    court.gov_pressure = IC.TUNE.gov_pressure_line
    court.gov_ask = {gov = "forge", ends = turn + 3, party = "forge"}
    local first = IC.gov_hold_price(F)
    local f0 = court.houses.forge.loyalty
    assert(IC.gov_hold(F), "Hold refused")
    assert(court.gov == "convoy" and court.gov_ask == nil, "Hold changed the government")
    assert(court.gov_pressure == math.floor(IC.TUNE.gov_pressure_line / 2), "pressure " .. court.gov_pressure)
    assert(court.houses.forge.loyalty == f0 + IC.TUNE.gov_hold_loyalty, "the pusher lost nothing")
    assert(IC.gov_hold_price(F) == 2 * first, "the second hold costs " .. IC.gov_hold_price(F))
    court.standing[901] = 0
    court.gov_ask = {gov = "forge", ends = turn + 3, party = "forge"}
    local ok, why = IC.gov_hold(F)
    assert(not ok and why == "gov_purse" and court.gov_ask, "an empty purse held anyway")
    gov_done()
end)

check("governments: an unanswered choice is Accept at its end, inside the turn", function()
    local court = gov_court({crown = 10, forge = 60})
    court.gov_ask = {gov = "forge", ends = turn, party = "forge"}
    IC.turn(F)
    assert(court.gov == "forge" and court.gov_ask == nil, "the court did not decide at the choice's end")
    gov_done()
end)

check("governments: a choice the court no longer pulls toward lapses", function()
    local court = gov_court({crown = 10, forge = 60, legion = 10})
    court.gov_ask = {gov = "forge", ends = turn + 3, party = "forge"}
    court.houses.forge = nil                     -- seceded: the Legion leads now
    assert(IC.gov_expire(F) == "lapsed" and court.gov_ask == nil and court.gov == "convoy",
        "a choice outlived the court's pull")
    court = gov_court({crown = 70, forge = 20})
    court.gov_ask = {gov = "forge", ends = turn + 3, party = "forge"}
    assert(IC.gov_expire(F) == "lapsed", "a choice outlived the Crown taking the lead")
    -- EITHER PARTY BACKS A TWO-PARTY GOVERNMENT (spec section 3): Road leaving
    -- while the Ledger still leads leaves the Convoy's choice standing.
    court = gov_court({crown = 10, road = 40, ledger = 40}, "forge")
    court.gov_ask = {gov = "convoy", ends = turn + 3, party = "road"}
    court.houses.road = nil
    assert(IC.gov_expire(F) == nil and court.gov_ask, "a Convoy choice lapsed with the Ledger still leading")
    gov_done()
end)

check("governments: the choice's answers go through the multiplayer ops", function()
    assert(IC.MP_OPS.gov_accept and IC.MP_OPS.gov_hold, "no op for the choice")
    local court = gov_court({crown = 10, forge = 60})
    court.gov_ask = {gov = "forge", ends = turn + 3, party = "forge"}
    assert(IC.mp_send(F, "gov_accept", ""), "the op was refused")
    assert(court.gov == "forge", "the op did not accept")
    gov_done()
end)
```

- [ ] **Step 2: Run to verify they fail**

Expected: FAIL "attempt to call field 'crown_purse' (a nil value)".

- [ ] **Step 3: Implement.** After `IC.member_weight`:

```lua
-- WHAT THE CROWN'S MEN CAN SPARE (plan ruling 5): each man's influence above
-- his own seat's bar, richest first, so paying never unseats anybody.
function IC.crown_purse(faction_key)
    local court, men, total, bar = IC.court(faction_key), {}, 0, {}
    for office_slug, cqi in pairs(court.offices) do
        local office = IC.office_by_slug(office_slug)
        if office then bar[cqi] = math.max(bar[cqi] or 0, IC.tier_influence(office.tier)) end
    end
    local ok, list = pcall(function() return real_faction(faction_key):character_list() end)
    if not ok or not list then return 0, men end
    for i = 0, list:num_items() - 1 do
        pcall(function()
            local man = list:item_at(i)
            if man and not man:is_null_interface() and man:is_alive()
               and IC.house_of_character(man, faction_key) == IC.CROWN then
                local cqi = man:command_queue_index()
                local spare = IC.standing(faction_key, cqi) - (bar[cqi] or 0)
                if spare > 0 then
                    men[#men + 1] = {cqi = cqi, spare = spare}
                    total = total + spare
                end
            end
        end)
    end
    table.sort(men, function(a, b)
        if a.spare ~= b.spare then return a.spare > b.spare end
        return a.cqi < b.cqi
    end)
    return total, men
end

function IC.spend_crown(faction_key, cost)
    local total, men = IC.crown_purse(faction_key)
    if total < cost then return false, cost - total end
    local left, court = cost, IC.court(faction_key)
    for _, m in ipairs(men) do
        if left <= 0 then break end
        local take = math.min(m.spare, left)
        court.standing[m.cqi] = IC.standing(faction_key, m.cqi) - take
        left = left - take
    end
    return true
end
```

After `IC.gov_turn`:

```lua
-- ONE CHANGE, for Accept and for a forced doctrine alike.
function IC.gov_change(faction_key, to, gain, loss, kind)
    local court = IC.court(faction_key)
    local from = court.gov
    for _, p in ipairs(from and IC.GOVS[from] and IC.GOVS[from].parties or {}) do
        IC.move_loyalty(faction_key, p, loss)
    end
    for _, p in ipairs(IC.GOVS[to].parties) do IC.move_loyalty(faction_key, p, gain) end
    court.gov, court.gov_pressure, court.gov_toward, court.gov_ask = to, 0, nil, nil
    IC.apply_gov_bundle(faction_key)
    IC.log(faction_key, kind or "gov", nil, to, 0)
    IC.feed(faction_key, "gov_changed")
end

function IC.gov_accept(faction_key)
    local ask = IC.court(faction_key).gov_ask
    if not ask then return false, "no choice" end
    IC.gov_change(faction_key, ask.gov, IC.TUNE.gov_accept_gain, IC.TUNE.gov_accept_loss, "gov")
    IC.save(faction_key)
    return true
end

function IC.gov_hold_price(faction_key)
    return IC.TUNE.gov_hold_cost * (1 + (IC.court(faction_key).gov_holds or 0))
end

function IC.gov_hold(faction_key)
    local court = IC.court(faction_key)
    local ask = court.gov_ask
    if not ask then return false, "no choice" end
    local price = IC.gov_hold_price(faction_key)
    local ok, short = IC.spend_crown(faction_key, price)
    if not ok then return false, "gov_purse", short end
    court.gov_holds = (court.gov_holds or 0) + 1
    court.gov_pressure = math.floor(IC.TUNE.gov_pressure_line / 2)
    court.gov_ask = nil
    if ask.party then IC.move_loyalty(faction_key, ask.party, IC.TUNE.gov_hold_loyalty) end
    IC.log(faction_key, "gov_hold", ask.party, ask.gov, price)
    IC.save(faction_key)
    return true
end

-- THE CHOICE'S END, inside the court's turn so every machine settles it the
-- same: a choice the court no longer pulls toward lapses, an unanswered one
-- at its end is Accept. No test of ask.party: either party of a two-party
-- government backs it (spec section 3), and the pull already answers that.
function IC.gov_expire(faction_key)
    local court = IC.court(faction_key)
    local ask = court.gov_ask
    if not ask then return nil end
    local want = IC.gov_pull(faction_key)
    if ask.gov == court.gov or want ~= ask.gov then
        court.gov_ask = nil
        IC.log(faction_key, "gov_lapse", ask.party, ask.gov, 0)
        return "lapsed"
    end
    if cm:model():turn_number() >= ask.ends then
        IC.gov_accept(faction_key)
        return "accepted"
    end
    return nil
end
```

After `IC.MP_OPS.fill`:

```lua
IC.MP_OPS.gov_accept = function(fk, arg)       -- nothing
    return answer(fk, "gov_accept", arg, IC.gov_accept(fk))
end
IC.MP_OPS.gov_hold = function(fk, arg)         -- nothing
    return answer(fk, "gov_hold", arg, IC.gov_hold(fk))
end
```

- [ ] **Step 4: Run to verify they pass**

Expected: `ok (881 checks)`.

### Task 6: Forcing a doctrine

**Files:**
- Modify: `zzz_derpy_iron_court.lua` (after `IC.gov_expire`; op after `IC.MP_OPS.gov_hold`).
- Test: harness.

**Interfaces:**
- Consumes: Task 5.
- Produces: `IC.can_force_gov(faction_key, to) -> ok, why, n` (why in `"gov_off" | "gov_same" | "gov_cool" | "gov_purse" | "no such government"`, n = turns left or influence short), `IC.gov_force(faction_key, to) -> ok, why, n`; MP op `doctrine` (arg = government slug).

- [ ] **Step 1: Write the failing check**

```lua
check("governments: a forced doctrine costs influence, moves loyalty both ways and cools down", function()
    local court = gov_purse_court()
    court.standing[901] = 5000
    IC.add_house(F, "road")
    local r0, f0 = court.houses.road.loyalty, court.houses.forge.loyalty
    local ok, why = IC.can_force_gov(F, "convoy")
    assert(not ok and why == "gov_same", "the current government was offered: " .. tostring(why))
    local purse = IC.crown_purse(F)
    assert(IC.gov_force(F, "forge"), "a forced doctrine was refused")
    assert(court.gov == "forge" and IC.crown_purse(F) == purse - IC.TUNE.gov_force_cost, "not changed, or not paid")
    assert(court.houses.road.loyalty == math.max(0, r0 + IC.TUNE.gov_force_loss), "the dropped party lost nothing")
    assert(court.houses.forge.loyalty == math.min(100, f0 + IC.TUNE.gov_force_gain), "the new party gained nothing")
    local ok2, why2, left = IC.can_force_gov(F, "legion")
    assert(not ok2 and why2 == "gov_cool" and left == IC.TUNE.gov_force_cooldown, "no cooldown: " .. tostring(why2))
    court.gov_cool = 0
    court.standing[901] = 0
    local ok3, why3 = IC.can_force_gov(F, "legion")
    assert(not ok3 and why3 == "gov_purse", "an empty purse forced a doctrine")
    gov_done()
    assert(select(2, IC.can_force_gov(F, "legion")) == "gov_off", "governments off still forced")
    assert(IC.MP_OPS.doctrine, "no op for a forced doctrine")
end)
```

- [ ] **Step 2: Run to verify it fails**

Expected: FAIL "attempt to call field 'can_force_gov' (a nil value)".

- [ ] **Step 3: Implement**

```lua
function IC.can_force_gov(faction_key, to)
    if not IC.governments_on() then return false, "gov_off" end
    if not IC.GOVS[to or ""] then return false, "no such government" end
    local court = IC.court(faction_key)
    if to == court.gov then return false, "gov_same" end
    local now = cm:model():turn_number()
    if now < (court.gov_cool or 0) then return false, "gov_cool", court.gov_cool - now end
    local total = IC.crown_purse(faction_key)
    if total < IC.TUNE.gov_force_cost then
        return false, "gov_purse", IC.TUNE.gov_force_cost - total
    end
    return true
end

function IC.gov_force(faction_key, to)
    local ok, why, n = IC.can_force_gov(faction_key, to)
    if not ok then return false, why, n end
    IC.spend_crown(faction_key, IC.TUNE.gov_force_cost)
    IC.gov_change(faction_key, to, IC.TUNE.gov_force_gain, IC.TUNE.gov_force_loss, "gov_force")
    IC.court(faction_key).gov_cool = cm:model():turn_number() + IC.TUNE.gov_force_cooldown
    IC.save(faction_key)
    return true
end
```

and `IC.MP_OPS.doctrine = function(fk, arg) return answer(fk, "doctrine", arg, IC.gov_force(fk, fields(arg)[1])) end`.

- [ ] **Step 4: Run to verify it passes**

Expected: `ok (882 checks)`.

### Task 7: Data - bundles, events, loc, MCT

**Files:**
- Modify: `tools/gen_iron_court.py` (a `GOVERNMENTS` list after `CONTROL_BANDS`; its bundle and loc rows in the same loop shape as `CONTROL_BANDS` at ~line 1329; two rows appended at the END of `EVENTS`), `zzz_derpy_iron_court.lua` (`IC.EVENTS` gets `gov_changed = {2629, true, true}, gov_pressure = {2630, true, true},`), `Modding Files/pack/script/mct/settings/derpy_iron_court.lua` (`SWITCHES`, `NUMBERS`, `PRESET_VALUES`; and the `rivals_max` tip now reads that a fifth party "rises under a dead house, or joins a rising if every house is alive").
- Test: `py tools/gen_iron_court.py --check`, `--selftest`; harness.

**Interfaces:**
- Consumes: `IC.GOV_ORDER` slugs, `IC.gov_bundle` naming (`derpy_ic_gov_<slug>`).
- Produces: bundles `derpy_ic_gov_<slug>`, loc `effect_bundles_localised_title_derpy_ic_gov_<slug>` / `_description_`, `derpy_ic_gov_name_<slug>` and `derpy_ic_gov_rule_<slug>` (panel text), events 2629/2630.

- [ ] **Step 1: Write the failing generator check.** In `gen_iron_court.check()`, add:

```python
    # GOVERNMENTS: the model's six and the generator's six are one list.
    lua = io.open(os.path.join(ROOT, "Modding Files", "pack", "script", "campaign",
                  "mod", "zzz_derpy_iron_court.lua"), encoding="utf-8").read()
    m = re.search(r"IC\.GOV_ORDER\s*=\s*\{([^}]*)\}", lua)
    model_govs = re.findall(r'"(\w+)"', m.group(1)) if m else []
    if model_govs != [g[0] for g in GOVERNMENTS]:
        out.append("IC.GOV_ORDER is %s and GOVERNMENTS is %s"
                   % (model_govs, [g[0] for g in GOVERNMENTS]))
```

(`ROOT` is the workspace root; if the file has no such name, use `os.path.dirname(os.path.dirname(os.path.abspath(__file__)))` as `check_gov_rank_constants` does.)

- [ ] **Step 2: Run it to verify it fails**

Run: `py tools/gen_iron_court.py --check`
Expected: FAIL "name 'GOVERNMENTS' is not defined".

- [ ] **Step 3: Implement.** After `CONTROL_BANDS`:

```python
# THE GOVERNMENTS (spec 2026-10-02 section 3), in IC.GOV_ORDER's order. Slug,
# name, the rule as the player reads it, the bundle's flavour line, effects.
GOVERNMENTS = [
    ("conclave", "The Conclave",
     "Office terms are shorter. A man may take a seat again after 1 turn.",
     "No one rules Zharr-Naggrund. Its Sorcerer-Prophets sit in council.",
     [(E_RESEARCH, 5, BOON)]),
    ("priest", "Rule of the High Priest",
     "Each rank a man gains is worth double influence. Battles are worth less.",
     "The eldest voice is the strongest, and it speaks for Hashut.",
     [(E_GROWTH, 2, BOON)]),
    ("forge", "Rule of the Daemonsmiths",
     "Governors earn more income. Idle men earn less influence.",
     "The priest-artificers rule from the forges.",
     [(E_ARMAMENTS, 10, BOON)]),
    ("legion", "Command of the Legion",
     "Battles are worth more influence and loyalty. Idle men earn none.",
     "Standing in the court is won in the field.",
     [(E_UPKEEP, 5, BOON)]),
    ("chain", "Rule of the Slave-Lords",
     "Murder, Purge and Provoke cost less. A failed move costs double loyalty.",
     "Fear holds the court as the chain holds the slave.",
     [(E_PB_LABOUR, 10, BOON)]),
    ("convoy", "The Convoy Concern",
     "Gifts and oaths cost less gold. Embezzling angers the parties twice as much.",
     "Everything in the Dark Lands has a price.",
     [(E_GDP, 5, BOON)]),
]
```

Emit them where `CONTROL_BANDS` bundles are emitted (~line 1329), with `bundle_key("gov", slug)`, the same effect-row and loc-row shape the bands use, plus loc `derpy_ic_gov_name_<slug>` = name and `derpy_ic_gov_rule_<slug>` = rule. Run `py tools/gen_iron_court.py --check`; if the effect-scope check refuses `E_PB_LABOUR` at faction scope, use the faction-to-force scope the generator's own party governor bundle uses for it (read `E_PB_LABOUR`'s tuple, line ~61). Append to `EVENTS`, at the end:

```python
    ("gov_changed", True, "chd/faction", "Positive",
     "A New Government",
     "The court has a new government. Its rule bends the court's own, and its "
     "party expects much of it.",
     "The Court Changes"),
    ("gov_pressure", True, "chd/faction", "Neutral",
     "The Court Pulls Another Way",
     "A party leads the court and asks for its own government. Accept it, or "
     "pay to hold the one you have, on the Petitions tab.",
     "A Choice Waits"),
```

MCT: in `SWITCHES` add

```lua
    {"governments", "Governments", "systems",
     "Each court has a government that bends one of its rules. Off, no court has "
     .. "one, and no government's effects apply.", true},
    {"gov_drift", "Governments drift with the court", "systems",
     "A party that leads the court for long enough asks for its own government. "
     .. "Off, a government changes only when you change it.", true},
```

in `NUMBERS`

```lua
    {"gov_pressure_line", "Turns before a leading party asks for its government", 6, 2, 12, 1,
     "How many turns a rival party must lead the court before it asks for its own "
     .. "government."},
    {"gov_hold_cost", "Influence to keep your government", 300, 100, 1000, 50,
     "What refusing a party's government costs the first time. Each refusal "
     .. "after that costs this much more."},
    {"gov_force_cost", "Influence to change your government", 400, 100, 1500, 50,
     "What changing your government by your own choice costs."},
```

and the same three keys in each `PRESET_VALUES` entry as in `IC.PRESETS` (Task 1). If the two switches belong in `IC.LIVE_TUNE` (read it: `grep -n "IC.LIVE_TUNE" -A8 zzz_derpy_iron_court.lua`), add them there.

- [ ] **Step 4: Run the gates**

Run: `py tools/gen_iron_court.py --check; py tools/gen_iron_court.py --selftest; py tools/gen_iron_court.py` (writes the TSVs), then the harness with `IC_TEST_ALL=1`.
Expected: `ok: 53 bundles ...`, selftest ok, harness ok. `py tools/import_iron_court.py` also passes its preset/registration comparison.

### Task 8: The panel - government line, Change Doctrine, the petition row, the Record

**Files:**
- Modify: `tools/gen_ic_ui.py` (`PANEL_LAYOUT` in the Crown box, `CROWN_CELLS`, `BTN_CELLS`, the button emission branch), `zzz_derpy_iron_court_ui.lua` (`PANEL_XY`, the Crown box draw at ~line 4035, `ICUI.MISSION_PICKS`, `ICUI.mission_rows`, `ICUI.on_pick_click`, `ICUI.draw_petitions`, `ICUI.on_petition_click`, `ICUI.PETITION_BTN`, `ICUI.ANSWERS`, `ICUI.SOUNDS`, the click listener, the reason sentences, the Record line text, the Help page), `tools/gen_ic_ui.py`'s `PETITION_BTN_CELL` (`hold` on `ic_row_f`).
- Test: harness (fake panel), `py tools/gen_ic_ui.py --check` / `--selftest`, `py tools/preview_iron_court.py --check`.

**Interfaces:**
- Consumes: Tasks 3-7 (`IC.court(f).gov`, `gov_ask`, `gov_pressure`, `gov_toward`, `IC.gov_hold_price`, `IC.can_force_gov`, ops `gov_accept` / `gov_hold` / `doctrine`, loc `derpy_ic_gov_name_<slug>` / `_rule_<slug>`).
- Produces: components `ic_gov` (text) and `ic_gov_btn` (button); picker kind `"doctrine"`; petition row kind `"gov"`.

- [ ] **Step 1: Write the failing checks** (fake panel; `with_fake_root` builds every `PANEL_XY` name):

```lua
check("governments: the Crown's box names the government and its pull", function()
    local court = gov_court({crown = 10, forge = 60})
    court.gov_toward, court.gov_pressure = "forge", 2
    with_fake_root(function(hud, panel)
        ICUI.view = "court"
        ICUI.refresh()
        local line = panel.children.ic_gov
        assert(line and line.visible and line.text:find(ICUI.gov_name("convoy"), 1, true),
            "the government line reads " .. tostring(line and line.text))
        assert(line.tooltip:find(ICUI.gov_name("forge"), 1, true)
               and line.tooltip:find(tostring(IC.TUNE.gov_pressure_line - 2), 1, true),
            "the tooltip does not say where the court is heading: " .. tostring(line.tooltip))
        assert(panel.children.ic_gov_btn.visible, "no Change Doctrine button")
    end)
    gov_done()
end)

check("governments: Change Doctrine opens a picker of the other five and sends the choice", function()
    local court = gov_purse_court()
    court.standing[901] = 5000
    with_fake_root(function(hud, panel)
        ICUI.view = "court"
        ICUI.refresh()
        map_click("ic_gov_btn")
        assert(ICUI.pick and ICUI.pick.kind == "doctrine", "no doctrine picker")
        local rows, keys = ICUI.mission_rows(F)
        assert(#rows == 5, #rows .. " rows")
        for i = 1, #rows do assert(keys[i] ~= "convoy", "the current government is offered") end
        ICUI.pick_rows = keys
        ICUI.on_pick_click({string = "ic_row_e"}, F)
    end)
    assert(court.gov ~= "convoy", "the picker's click changed nothing")
    gov_done()
end)

check("governments: a waiting choice is a petition with Accept and Hold", function()
    local court = gov_purse_court()
    court.standing[901] = 5000
    court.gov_ask = {gov = "forge", ends = turn + 2, party = "forge"}
    with_fake_root(function(hud, panel)
        ICUI.view = "petitions"
        ICUI.refresh()
        assert(ICUI.petition_rows[1] and ICUI.petition_rows[1].kind == "gov", "the choice is not the first petition")
        -- HOLD, through the send path.
        ICUI.send(F, "gov_hold", "")
    end)
    assert(court.gov_ask == nil and court.gov == "convoy" and court.gov_holds == 1, "Hold did not hold")
    gov_done()
end)
```

(Adjust `on_pick_click`'s fake context to the shape `ICUI.clicked_index` reads - look at an existing picker check: `grep -n "on_pick_click" tools/_iron_court_harness.lua`.)

- [ ] **Step 2: Run to verify they fail**

Expected: FAIL "the government line reads nil".

- [ ] **Step 3: Implement the layout.** In `gen_ic_ui.py`, after `_LEFT_BOTTOM`/`_LEADER_BOTTOM` and before `CROWN_RULE_W`:

```python
# THE GOVERNMENT (spec 2026-10-02 section 8): one row under both halves - its
# name on the left half's width, Change Doctrine at the right half's right end.
_GOV_Y = max(_LEFT_BOTTOM, _LEADER_BOTTOM) + 8
GOV_BTN_W = 220
PANEL_LAYOUT["ic_gov"] = (_CROWN_X, _GOV_Y + 4, _CROWN_LEFT_W, _CTL_H)
PANEL_LAYOUT["ic_gov_btn"] = (_CROWN_RIGHT_X + _CROWN_RIGHT_W - GOV_BTN_W, _GOV_Y, GOV_BTN_W, 34)
_GOV_BOTTOM = _GOV_Y + 34
```

Use `max(_LEFT_BOTTOM, _LEADER_BOTTOM, _GOV_BOTTOM)` wherever `CROWN_H` and `ic_crown_rule_v` use `max(_LEFT_BOTTOM, _LEADER_BOTTOM)` (keep the vertical rule ending at the old bottom: it divides the halves, not the government row). Add `"ic_gov", "ic_gov_btn"` to `CROWN_CELLS`, `"ic_gov_btn"` to `BTN_CELLS`, and `"ic_gov_btn"` to the emission tuple `("ic_page_prev", "ic_page_next", "ic_fill", ...)`. Add `"hold": "ic_row_f"` to `PETITION_BTN_CELL`. Run `py tools/gen_ic_ui.py --check`: it prints any overlap (the box grew 42px) and the `PANEL_XY` values the Lua must carry; copy `ic_gov`, `ic_gov_btn` and the changed `ic_crown_box` / rules into `PANEL_XY` in `zzz_derpy_iron_court_ui.lua`. If the grown box overruns what sits below it, the check names it; move that cell down by the same 42px in `PANEL_LAYOUT` and re-run.

- [ ] **Step 4: Implement the panel Lua.**

```lua
-- THE GOVERNMENT, in words (spec 2026-10-02). Loc first, as the panel always reads it.
function ICUI.gov_name(slug)
    return loc("derpy_ic_gov_name_" .. tostring(slug), tostring(slug))
end
function ICUI.gov_rule(slug)
    return loc("derpy_ic_gov_rule_" .. tostring(slug), "")
end

function ICUI.gov_tip(faction, court)
    local lines = {ICUI.gov_rule(court.gov),
        loc("effect_bundles_localised_description_" .. IC.gov_bundle(court.gov), "")}
    if court.gov_toward and (court.gov_pressure or 0) > 0 and not court.gov_ask then
        lines[#lines + 1] = string.format("The court pulls toward %s. In %d more turns it asks.",
            ICUI.gov_name(court.gov_toward),
            math.max(0, IC.TUNE.gov_pressure_line - court.gov_pressure))
    end
    local left = (court.gov_cool or 0) - cm:model():turn_number()
    if left > 0 then
        lines[#lines + 1] = string.format("Your last change holds for %d more turns.", left)
    end
    return table.concat(lines, "\n")
end

function ICUI.draw_gov(panel, faction, court)
    local on = IC.governments_on() and court.gov ~= nil
    local line, btn = comp("ic_gov", panel), comp("ic_gov_btn", panel)
    show(line, on)
    show(btn, on)
    if not on then return end
    set_text(line, string.format("[[img:%s]][[/img]]%s", ICUI.BAND_ICON, ICUI.gov_name(court.gov)))
    pcall(function() line:SetTooltipText(ICUI.gov_tip(faction, court), "", true) end)
    set_text(btn, "Change Doctrine")
    pcall(function() btn:SetTooltipText(string.format(
        "Choose another government. It costs %d influence from your own party.",
        IC.TUNE.gov_force_cost), "", true) end)
end
```

Call `ICUI.draw_gov(panel, faction, court)` in `ICUI.draw_court` after the FX lines loop, and hide both on every other view (add them where the Crown box's other cells are shown/hidden - `ICUI.CONTROL_KEYS` / `ICUI.COLUMN_KEYS` - by appending `"ic_gov", "ic_gov_btn"` to `ICUI.CONTROL_KEYS`).

The picker: add `doctrine = {"Government", "Its rule", "Cost", "Loyalty", ""},` to `ICUI.MISSION_PICKS`, and in `ICUI.mission_rows` a branch:

```lua
    elseif kind == "doctrine" then
        local court = IC.court(faction)
        for _, g in ipairs(IC.GOV_ORDER) do
            if g ~= court.gov then
                local may, why, n = IC.can_force_gov(faction, g)
                local mine = IC.court(faction).houses
                local hit = {}
                for _, p in ipairs(IC.GOVS[court.gov] and IC.GOVS[court.gov].parties or {}) do
                    if mine[p] then hit[#hit + 1] = string.format("%s %d", ICUI.house_name(p, faction), IC.TUNE.gov_force_loss) end
                end
                for _, p in ipairs(IC.GOVS[g].parties) do
                    if mine[p] then hit[#hit + 1] = string.format("%s +%d", ICUI.house_name(p, faction), IC.TUNE.gov_force_gain) end
                end
                lines[#lines + 1] = {ICUI.gov_name(g), ICUI.gov_rule(g),
                    string.format("%d influence", IC.TUNE.gov_force_cost), table.concat(hit, ", "),
                    may and "Choose" or ICUI.red(ICUI.mission_refusal(why, n)),
                    tip = (not may) and ICUI.reason_text(why, n) or nil}
                keys[#lines] = may and g or nil
            end
        end
```

In `ICUI.on_pick_click`, before the final `else`: `elseif ICUI.pick.kind == "doctrine" then ICUI.send(faction, "doctrine", chosen)`. In the click listener: `elseif id == "ic_gov_btn" and comp(ICUI.PANEL) then ICUI.pick = {kind = "doctrine"}; ICUI.scroll.pick = 0; ICUI.notice = nil; ICUI.refresh()`. Add reason sentences for `gov_same` ("That is your government already."), `gov_cool` ("Your last change still holds for %d turns."), `gov_purse` ("Your party is %d influence short. Influence a man needs for his seat is not spent."), `gov_off` ("Governments are switched off."), and `mission_refusal` codes `gov_cool` -> `"Wait %d"`, `gov_purse` -> `"Short"`.

The petition row (first, before the demand) in `ICUI.draw_petitions`:

```lua
    local ask = IC.governments_on() and court.gov_ask or nil
    if ask then
        local price = IC.gov_hold_price(faction)
        local can_hold = IC.crown_purse(faction) >= price
        lines[#lines + 1] = {
            ask.party and ICUI.house_name(ask.party, faction) or "The Court",
            string.format("Asks for %s - %s", ICUI.gov_name(ask.gov),
                          turns(math.max(0, ask.ends - now))),
            "", "", B.accept, can_hold and B.hold or ICUI.red(B.hold),
            tip = string.format("Accept: +%d loyalty for its party, %d for your government's. "
                .. "Hold: %d influence, %d loyalty for its party.",
                IC.TUNE.gov_accept_gain, IC.TUNE.gov_accept_loss, price, IC.TUNE.gov_hold_loyalty),
            icon = ask.party and ICUI.crest(ask.party) or nil, icon_kind = "crest", plate = ask.party,
        }
        ICUI.petition_rows[#lines] = {kind = "gov", slug = ask.party}
    end
```

`ICUI.PETITION_BTN` gains `hold = "Hold"`. In `ICUI.on_petition_click`: `elseif p.kind == "gov" then op, arg = (yes and "gov_accept" or "gov_hold"), ""`. The petition count for the tab marker (`s.petitions`, ~line 1385) adds 1 when `court.gov_ask`. `ICUI.ANSWERS.gov_accept = confirmed(true, false, "gov_accept")`, `ICUI.ANSWERS.gov_hold = confirmed(true, false, "gov_hold")`, and `ICUI.ANSWERS.doctrine` closes the picker the way `ICUI.ANSWERS.appoint` does (read it first). `ICUI.SOUNDS` gains `gov_accept = "UI_CAM_HUD_Diplomacy_Response_Deal_Accepted", gov_hold = "UI_CAM_HUD_Diplomacy_Response_Deal_Declined", doctrine = "UI_CLICK_Begin_Ritual"` (all in the sound registry; `gen_iron_court --check` holds them).

The Record: where `ICUI` turns a log entry into a sentence (`grep -n "e.kind == \"offer\"" zzz_derpy_iron_court_ui.lua`, ~line 4803), add `gov` ("The court took a new government: %s."), `gov_force` ("You changed the government to %s."), `gov_ask` ("%s asked for %s."), `gov_hold` ("You kept your government against %s, for %d influence."), `gov_lapse` ("%s no longer asks for %s."), with `ICUI.gov_name(e.key)` and the party name from `e.slug`. The Help page: a "Governments" topic in `ICUI.HELP` (~line 5233) with three lines: what a government is, how the court asks, what Change Doctrine costs.

- [ ] **Step 5: Run the gates**

Run: harness `IC_TEST_ALL=1`; `py tools/gen_ic_ui.py --check`; `py tools/gen_ic_ui.py --selftest`; `py tools/preview_iron_court.py --check`; `py tools/gen_iron_court.py --check`.
Expected: all ok (harness 885 checks).

### Task 9: Mutants, build, deploy, docs, repo

**Files:**
- Modify: `tools/mutate_iron_court.py` (a governments block appended to `MUTANTS`), `docs/sessions/HANDOFF_20261002_IRON_COURT_GOVERNMENTS.md` (new), `docs/SESSION_INDEX.md` (one line), `tools/sync_iron_court_repo.py` (the new handoff and spec in its lists), `repos/derpy-iron-court/CHANGELOG.md`, `README.md` (a Governments section), `docs/DEVELOPMENT.md` (counts).

- [ ] **Step 1: Write the mutants** (path alias `M` = model, `U` = panel), one per rule, each a plausible mistake:

```python
    # ---- governments (2026-10-02) ----------------------------------------
    ("an override answering for every court", M,
     """    local court = faction_key and IC.state[faction_key]
    return court and IC.GOVS[court.gov or ""] or nil""",
     """    for _, c in pairs(IC.state) do if IC.GOVS[c.gov or ""] then return IC.GOVS[c.gov] end end
    return nil"""),
    ("a table knob scaled into IC.TUNE itself", M,
     """        local out = {}
        for k, v in pairs(base) do out[k] = math.floor(v * o.mul + 0.5) end
        return out""",
     """        for k, v in pairs(base) do base[k] = math.floor(v * o.mul + 0.5) end
        return base"""),
    ("the Crown leading builds pressure", M,
     """    if not top or top == IC.CROWN then return nil, top, 0 end""",
     """    if not top then return nil, top, 0 end"""),
    ("a new leader keeps the old count", M,
     """    if court.gov_toward ~= want then court.gov_toward, court.gov_pressure = want, 0 end""",
     """    court.gov_toward = want"""),
    ("drift in the grace period", M,
     """        and IC.is_human(faction_key) and IC.grace_left() == 0""",
     """        and IC.is_human(faction_key)"""),
    ("an AI court drifts", M,
     """        and IC.is_human(faction_key) and IC.grace_left() == 0""",
     """        and IC.grace_left() == 0"""),
    ("pressure builds over a waiting choice", M,
     """    if not IC.gov_drift_on(faction_key) or now < (court.gov_cool or 0)
       or court.gov_ask then""",
     """    if not IC.gov_drift_on(faction_key) or now < (court.gov_cool or 0) then"""),
    ("the purse spends a seat's bar", M,
     """                local spare = IC.standing(faction_key, cqi) - (bar[cqi] or 0)""",
     """                local spare = IC.standing(faction_key, cqi)"""),
    ("Hold costs the same every time", M,
     """    return IC.TUNE.gov_hold_cost * (1 + (IC.court(faction_key).gov_holds or 0))""",
     """    return IC.TUNE.gov_hold_cost"""),
    ("an unanswered choice never settles", M,
     """    if cm:model():turn_number() >= ask.ends then""",
     """    if false then"""),
    ("a choice outlives the court's pull", M,
     """    if ask.gov == court.gov or want ~= ask.gov then""",
     """    if ask.gov == court.gov then"""),
    ("a forced doctrine with no cooldown", M,
     """    IC.court(faction_key).gov_cool = cm:model():turn_number() + IC.TUNE.gov_force_cooldown""",
     """"""),
    ("the setting off leaves the bundle on", M,
     """    local want = IC.governments_on() and IC.court(faction_key).gov or nil""",
     """    local want = IC.court(faction_key).gov"""),
    ("an older save reads a government out of nothing", M,
     """    court.gov = IC.GOVS[g[1] or ""] and g[1] or nil""",
     """    court.gov = g[1] or "conclave\""""),
    ("the doctrine picker offers the current government", U,
     """            if g ~= court.gov then""",
     """            if true then"""),
]
```

(Append inside the list, before its closing `]`.)

- [ ] **Step 2: Run them**

Run: `py tools/mutate_iron_court.py "governments" "override" "pressure" "purse" "Hold" "choice" "doctrine" "older save" "Crown leading" "AI court drifts" "grace period"`
Expected: `N mutants, 0 unexplained`. A survivor means a missing assertion: add it to the owning task's check, watch it catch the mutant, re-run.

- [ ] **Step 3: Full gates and build**

Run, from the workspace root: `luac -p` on the four Lua files; `py tools/check_lua_api.py`; `py tools/check_lua_literal_left.py`; `py tools/check_lua_undeclared.py`; `py tools/import_iron_court.py`; then `py tools/deploy_iron_court.py` (RPFM must be open; with the game running use `--wait` in the background).
Expected: every gate green; "deployed ... byte-identical to the build". Read the live pack back (`tools/read_pack_index.py`) and confirm `IC.GOVS` and `derpy_ic_gov_` are in it.

- [ ] **Step 4: Docs and repo.** Write `docs/sessions/HANDOFF_20261002_IRON_COURT_GOVERNMENTS.md` (what was built, gates, the in-game looks owed: the bundle shows in Faction Effects, the Crown box row fits at 1600 and 2560, the petition row, a forced change's event card, an older save loading), one line in `docs/SESSION_INDEX.md`, add the handoff and the spec to `tools/sync_iron_court_repo.py`'s lists, run it, add a CHANGELOG entry and a README "Governments" section in the repo, update DEVELOPMENT.md's counts. Push only when the author asks.
