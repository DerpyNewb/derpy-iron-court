# Iron Court Civil Missions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Two new Intrigue moves in a fifth "Missions" column: Send an Envoy (one of four five-turn works in a province you hold) and Send Diplomats (a better regard from a faction you have met), each paid and resolved on the click like the four errands.

**Architecture:** Both are ordinary `IC.PLOTS` rows with `aimed = false` and a new `target` field ("province" / "faction"). `IC.may_target` gains a branch per target kind, so the pickers and the click ask one rule. `IC.plot` applies an effect bundle to the province (the four bundles are generated DB rows, their values read out of `IC.TUNE`) or CA's diplomatic bonus. The panel gets three new picker kinds that draw places and factions in the existing row pool, chained into the existing "who carries this out?" picker. The grid, the feed texts and the move loc all derive from `IC.PLOTS` / `IC.PLOT_CATS` already.

**Tech Stack:** Lua 5.1 (campaign script), Python 3 generators (`tools/gen_iron_court.py`, `tools/gen_ic_ui.py`), the Lua harness `tools/_iron_court_harness.lua`, the mutation runner `tools/mutate_iron_court.py`.

**Spec:** `docs/superpowers/specs/2026-09-29-iron-court-civil-missions-design.md`.

## Global Constraints

- The workspace is NOT git. There are no commits: every checkpoint is the harness run green plus the gates it names.
- No emojis anywhere. Never write the word "rung". Player text in plain words: no "standing", "cap", "rep", "AI", "HUD" in any string the player reads.
- The Iron Court Lua files, the harness, the generators and `mutate_iron_court.py` are LF. Edit with the Edit tool or byte-safe Python; never `sed -i`. A patch script with a backslash or a regex goes through the Write tool, never a heredoc.
- Harness: `"/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua` - stops at the first FAIL (`IC_TEST_ALL=1` runs all), ends `iron court harness: ok (N checks)`. Note N before Task 1 (805 if the party map plan ran first, 789 if not); each task below says how many checks it adds. New checks go ABOVE `check("no parties' turn failed anywhere in the run"`.
- The harness sets `IC.TUNE.grace_turns = 0` where it loads the model.
- Never edit any file while `tools/mutate_iron_court.py` runs; never run another gate beside it.
- A loc call from a listener or turn handler is a turn-1 CTD. Nothing in the model resolves a display name; the Log resolves names at draw time.
- Every new number is an `IC.TUNE` knob, NOT an MCT setting and NOT in `IC.TUNE_ORDER`, so no save string changes for any of them (spec section 3).
- Keys fail silently. Every CA key below (effects, scopes, icons, the bundle target) was read out of the vanilla cache or CA's ui packs on 2026-09-29; do not retype one from memory.
- `SetText(text, "")`, never `SetStateText`. `SetVisible` takes a boolean.
- Build only with RPFM open. After a build, if `Warhammer3.exe` is not running, deploy to data/ without asking: `py tools/deploy_iron_court.py` backs up, copies and byte-compares.

## Rulings against the spec (made while planning; ledger them at execution)

1. **The refusal for a province or faction that is no longer there is `lost`, not `gone`.** `gone` is taken: `ICUI.reason_text` already words it "The man or party that offer named is gone." for the petitions.
2. **The Log names the acting PARTY, not the man.** A log entry stores the actor's party slug, the target key and the price (`IC.log`); it has never stored a character, and every existing move line reads "{party} ...". The spec's "{man} went to {province}" becomes "{party} spends N influence sending an envoy to {province}: ...".
3. **A failed mission logs `plot_key .. ":" .. target`** as its key, so the Record can say where it failed. An errand's failure keeps logging its bare key and an aimed move's the target party - neither contains a `:`.
4. **The envoy magnitudes live ONCE, in `IC.TUNE`.** The bundle's value is a DB row the generator writes; `gen_iron_court.py` reads `IC.TUNE.envoy_*` and `IC.ENVOY_TASKS` out of the shipped Lua (as it already reads `rebel_units` and `IC.PLOTS`), so the card text and the effect cannot disagree.
5. **Raw materials keeps the spec's borrowed scope, by name.** The generator's check 2 refuses any (effect, scope) pair CA does not ship, and `(wh3_dlc23_pooled_resource_chd_raw_material_efficiency, province_to_province_own_unseen)` is not one - measured 2026-09-29: CA's only province-bundle scope for it is `province_to_province_own_factionwide`, which would reach every province. The spec chose the borrowed scope knowingly and lists it as in-game look 3; the check gains a one-entry `BORROWED_SCOPES` exemption and still refuses every other unshipped pair.
6. **A bundle's icon is checked to exist.** Nothing checked `ui_icon`, and a wrong one draws a blank square with no error. The four envoy icons and the existing `chd_conclave_influence.png` were all found under `ui/campaign ui/effect_bundles/` in CA's ui packs on 2026-09-29.
7. **The two card icons**, which the spec does not name: Envoy `ui/campaign ui/ancillaries/wh3_dlc23_anc_follower_veteran_overseer.png` (an overseer sent to a province), Diplomats `ui/campaign ui/ancillaries/wh3_main_anc_cathay_diplomat.png` (CA ships no Chaos Dwarf diplomat). Both exist; the author may swap either.
8. **The mission pickers do not sort.** The picker's sort modes are a character list's (name, influence, rank, party, available); a province or faction row carries none of them. The mission pickers get their own headers, no sort arrows and no lit column, and list in a fixed order: provinces in `IC.seats` order, tasks in `IC.ENVOY_TASKS` order, factions by display name.
9. **A dead faction is left off the Diplomats list** rather than drawn refused: `factions_met` keeps the dead, and a column of "No" rows for them is noise. `IC.may_target` still refuses one (`lost`) if the click ever names it.
10. **The help page gets its own Missions line** rather than lengthening the Errands line, and the "must not be leading an army" line names missions too.

## Review Focus

1. **A province lost between choosing it and the click** must be refused `lost`, never reach `cm:apply_effect_bundle_to_faction_province` with a nil region. Test in Task 1 ("an envoy is refused...").
2. **The same task sent twice** must be refused with the turns left, and the price NOT paid for the refused second send. Test in Task 1.
3. **A failed send** must pay the price, apply nothing and rest nobody. Tests in Tasks 1 and 2.
4. **A save written before this build** must load with nobody resting, and a save made mid-rest must still refuse the faction after loading. Test in Task 2.
5. **The longest vanilla province key** must still fit the multiplayer message. Test in Task 1.

---

### Task 1: Send an Envoy - the model

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua` (`IC.TUNE` ~line 527; `IC.LOG_KINDS` ~line 864; `IC.PLOT_CATS` ~line 4190; `IC.PLOTS` ~line 4205; new helpers before `IC.may_target` ~line 4520; `IC.may_target`; `IC.can_plot` ~line 4594; `IC.plot` ~line 4681)
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua` (`ICUI.intrigue_text` ~line 4866, one arm)
- Modify: `tools/_iron_court_harness.lua` (records ~line 18; region stub ~line 309; `apply_effect_bundle_to_faction_province` stub ~line 861; new checks)

**Interfaces:**
- Produces (Lua): `IC.ENVOY_TASKS` (`{code, name, knob, fmt, bundle, icon}` x4, display order); `IC.envoy_task(code) -> task|nil`; `IC.envoy_effect(task) -> "+20% armaments"`; `IC.envoy_split(target) -> province_key|nil, task|nil`; `IC.envoy_running(faction_key, province_key, bundle) -> turns_left|nil`; `IC.may_send_envoy(faction_key, target) -> ok, why, turns`; `IC.may_target` and `IC.can_plot` now return a third value (`short`) on `running` / `resting`. `IC.TUNE`: `mission_turns`, `plot_envoy_cost`, `plot_chance_envoy`, `envoy_ctl`, `envoy_arm`, `envoy_raw`, `envoy_lab`. Plot row `envoy` with `target = "province"`.
- Produces (harness): `prov_bundles` (`[province key] = {[bundle] = turns}`), filled by the bundle stub for any positive duration; regions answer `faction_province_has_effect_bundle`, `faction_province_effect_bundles`, `public_order`.

- [ ] **Step 1: The harness stubs**

In `tools/_iron_court_harness.lua`, beside `local province_applied = {}` (~line 18):

```lua
-- WHAT A TIMED PROVINCE BUNDLE LEFT BEHIND: [province key] = {[bundle] = turns}.
-- Filled by apply_effect_bundle_to_faction_province for any positive duration and
-- read back by the region's faction_province_* calls, so a second envoy to the
-- same work sees the first one running.
local prov_bundles = {}
```

Replace the `apply_effect_bundle_to_faction_province` stub (~line 861):

```lua
    -- -1 IS INDEFINITE (the governors); a count of turns is a civil mission
    -- (spec 2026-09-29). Zero is neither - CA's duration() reads 0 as infinite.
    apply_effect_bundle_to_faction_province = function(_, bundle, region, turns)
        assert(turns == -1 or (type(turns) == "number" and turns > 0),
            "turns must be -1 or a positive count, got " .. tostring(turns))
        province_applied[bundle] = (province_applied[bundle] or 0) + 1
        if turns > 0 then
            -- province_name() IS A KEY (CA: "Key of the province containing
            -- the region"); the region stub has no province() at all.
            assert(type(region) == "table" and region.province_name, "a region interface")
            local p = region:province_name()
            prov_bundles[p] = prov_bundles[p] or {}
            prov_bundles[p][bundle] = turns
        end
    end,
```

In the region stub's `item_at` body (the per-province region, ~line 312), beside `has_effect_bundle`:

```lua
                        -- THE FACTION PROVINCE'S TIMED BUNDLES, off prov_bundles.
                        faction_province_has_effect_bundle = function(_, b)
                            return (prov_bundles[key] or {})[b] ~= nil
                        end,
                        faction_province_effect_bundles = function()
                            local out = {}
                            for b, n in pairs(prov_bundles[key] or {}) do
                                out[#out + 1] = {key = function() return b end,
                                                 duration = function() return n end}
                            end
                            return {num_items = function() return #out end,
                                    item_at = function(_, i) return out[i + 1] end}
                        end,
                        -- CONTROL, off f._order[province]; 0 if a check set none.
                        public_order = function() return (f._order or {})[key] or 0 end,
```

- [ ] **Step 2: Write the failing checks**

Above the final check:

```lua
check("an envoy puts the chosen work on that province for mission_turns", function()
    IC.state = {}
    prov_bundles = {}
    turn = 1
    local man = make_character(1301, ANY_SEAT, "crown")
    make_faction(F, IC.CHD_SUBCULTURE, {man}, {"prov_a", "prov_b"})
    IC.add_house(F, IC.CROWN)
    IC.court(F).standing[1301] = 1000
    rng({1})
    assert(IC.plot(F, "envoy", 1301, "prov_b:arm"), "the envoy was refused")
    rng(nil)
    assert(prov_bundles.prov_b and prov_bundles.prov_b.derpy_ic_envoy_arm == IC.TUNE.mission_turns,
        "prov_b holds " .. tostring(prov_bundles.prov_b and prov_bundles.prov_b.derpy_ic_envoy_arm))
    assert(not prov_bundles.prov_a, "the work went to the wrong province")
    assert(IC.court(F).standing[1301] == 1000 - IC.TUNE.plot_envoy_cost, "the price was not paid")
    -- THE RECORD SAYS WHERE AND WHAT.
    local last = IC.court(F).log[#IC.court(F).log]
    assert(last.kind == "envoy" and last.key == "prov_b:arm", "logged " .. tostring(last.key))
    local line = ICUI.intrigue_text(last)
    assert(line:find("prov_b", 1, true) and line:find("+20% armaments", 1, true)
           and line:find("for " .. IC.TUNE.mission_turns .. " turns", 1, true), line)
    -- A MALFORMED KEY STILL SAYS SOMETHING (the every-move check passes "legion").
    assert(ICUI.intrigue_text({turn = 1, kind = "envoy", slug = "crown", key = "legion", n = 1}))
end)

check("an envoy is refused for work already running, a lost province, a bad task, a general",
function()
    IC.state = {}
    prov_bundles = {}
    turn = 1
    local man = make_character(1311, ANY_SEAT, "crown")
    local general = make_character(1312, ANY_SEAT, "crown")
    general._force = true
    make_faction(F, IC.CHD_SUBCULTURE, {man, general}, {"prov_a"})
    IC.add_house(F, IC.CROWN)
    IC.court(F).standing[1311] = 1000
    IC.court(F).standing[1312] = 1000
    prov_bundles.prov_a = {derpy_ic_envoy_ctl = 3}
    local ok, why, left = IC.may_target(F, "envoy", "prov_a:ctl")
    assert(not ok and why == "running" and left == 3, tostring(why) .. " " .. tostring(left))
    -- AND THE CLICK REFUSES THE SAME, WITHOUT TAKING THE PRICE.
    ok, why, left = IC.plot(F, "envoy", 1311, "prov_a:ctl")
    assert(not ok and why == "running" and left == 3, "the click said " .. tostring(why))
    assert(IC.court(F).standing[1311] == 1000, "a refused envoy was charged")
    -- ANOTHER TASK IN THE SAME PROVINCE IS FREE.
    assert(IC.may_target(F, "envoy", "prov_a:raw"), "one task running blocked the others")
    assert(select(2, IC.may_target(F, "envoy", "prov_z:ctl")) == "lost", "a province not held")
    assert(select(2, IC.may_target(F, "envoy", "prov_a:xyz")) == "no such task", "an unknown task")
    assert(select(2, IC.may_target(F, "envoy", "prov_a")) == "no such task", "a target with no task")
    assert(select(2, IC.can_plot(F, "envoy", 1312, "prov_a:raw")) == "commands",
        "a general was sent on a mission")
end)

check("a failed envoy pays and puts nothing on the province", function()
    IC.state = {}
    prov_bundles = {}
    turn = 1
    local man = make_character(1321, ANY_SEAT, "crown")
    make_faction(F, IC.CHD_SUBCULTURE, {man}, {"prov_a"})
    IC.add_house(F, IC.CROWN)
    IC.court(F).standing[1321] = 1000
    rng({100})
    local ok, how = IC.plot(F, "envoy", 1321, "prov_a:lab")
    rng(nil)
    assert(ok and how == "failed", "the roll did not fail: " .. tostring(how))
    assert(not prov_bundles.prov_a, "a failed envoy still did the work")
    assert(IC.court(F).standing[1321] == 1000 - IC.TUNE.plot_envoy_cost, "a failure was free")
    -- RULING 3: the Record can say where it failed.
    local last = IC.court(F).log[#IC.court(F).log]
    assert(last.kind == "plot_failed" and last.key == "envoy:prov_a:lab",
        "a failed mission logged " .. tostring(last.key))
end)

check("an envoy to the longest vanilla province crosses the multiplayer wire", function()
    IC.state = {}
    prov_bundles = {}
    turn = 1
    -- 56 characters; the spec's measured longest, and the cqi at its widest.
    local province = "wh3_main_combi_province_southlands_worlds_edge_mountains"
    local id = IC.MP_TAG .. "|plot|envoy|4294967295|" .. province .. ":ctl"
    assert(#id <= IC.MP_MAX, #id .. " characters, over " .. IC.MP_MAX)
    -- AND THE TARGET SURVIVES fields()' SPLIT ON "|" AND envoy_split's ON ":",
    -- through the same op a second machine runs.
    local man = make_character(1331, ANY_SEAT, "crown")
    make_faction(F, IC.CHD_SUBCULTURE, {man}, {province})
    IC.add_house(F, IC.CROWN)
    IC.court(F).standing[1331] = 1000
    rng({1})
    local done = IC.MP_OPS.plot(F, "envoy|1331|" .. province .. ":ctl")
    rng(nil)
    assert(done, "the envoy was refused over the wire")
    assert(prov_bundles[province] and prov_bundles[province].derpy_ic_envoy_ctl,
        "the work did not reach " .. province)
end)
```

- [ ] **Step 3: Run the harness, verify it fails**

Expected: FAIL on "an envoy puts the chosen work..." with `the envoy was refused` (no `envoy` move yet: `no such plot`).

- [ ] **Step 4: The knobs, the category, the move and the tasks**

`IC.TUNE`, after `    plot_chance_circuit   = 80,`:

```lua

    -- THE CIVIL MISSIONS (spec 2026-09-29 section 3). NOT MCT settings and not
    -- in IC.TUNE_ORDER. The envoy_* values are ALSO the bundles' effect values:
    -- tools/gen_iron_court.py reads them out of this file.
    mission_turns         = 5,    -- how long an envoy's work lasts
    plot_envoy_cost       = 120,
    plot_chance_envoy     = 80,
    envoy_ctl             = 6,    -- control
    envoy_arm             = 20,   -- % armaments
    envoy_raw             = 20,   -- % raw materials
    envoy_lab             = 15,   -- % fewer labourers lost
    plot_diplomats_cost   = 100,
    plot_chance_diplomats = 75,
    diplomats_bonus       = 4,    -- CA's own -6..+6 scale
    diplomats_rest        = 5,    -- turns before the same faction again
```

`IC.PLOT_CATS`, after `    {key = "errand", name = "Errands"},`:

```lua
    {key = "mission", name = "Missions"},
```

`IC.PLOTS`, after the `circuit` entry (before the table's closing `}`):

```lua
    -- THE CIVIL MISSIONS (spec 2026-09-29): aimed at a PLACE, not a man.
    -- `target` says which kind; IC.may_target reads it, and the panel opens the
    -- matching picker. The four envoy tasks are IC.ENVOY_TASKS.
    {key = "envoy", name = "Send an Envoy", aimed = false, target = "province",
     icon = "ui/campaign ui/ancillaries/wh3_dlc23_anc_follower_veteran_overseer.png",
     cat = "mission",
     cost = "plot_envoy_cost",
     effect = string.format(
         "One of your provinces, for %d turns: control, armaments, raw materials "
         .. "or labour.", IC.TUNE.mission_turns),
     blurb = "A man of the Tower goes to see the work done himself."},
```

After `function IC.plot_by_key(key) ... end` (~line 4474):

```lua
-- THE ENVOY'S FOUR TASKS (spec 2026-09-29 section 2.1), in display order. The
-- bundle's VALUE is IC.TUNE[knob]: tools/gen_iron_court.py reads both out of
-- this file, so the text and the effect are one number. `icon` is the bundle's,
-- under ui/campaign ui/effect_bundles/.
IC.ENVOY_TASKS = {
    {code = "ctl", name = "Control", knob = "envoy_ctl", fmt = "+%d control",
     bundle = "derpy_ic_envoy_ctl", icon = "wh3_dlc23_edict_chd_smoke_stacks.png"},
    {code = "arm", name = "Armaments", knob = "envoy_arm", fmt = "+%d%% armaments",
     bundle = "derpy_ic_envoy_arm", icon = "wh3_dlc23_edict_chd_higher_quotas.png"},
    {code = "raw", name = "Raw materials", knob = "envoy_raw", fmt = "+%d%% raw materials",
     bundle = "derpy_ic_envoy_raw", icon = "chd_toz_district_industry.png"},
    {code = "lab", name = "Labour", knob = "envoy_lab", fmt = "-%d%% labourers lost",
     bundle = "derpy_ic_envoy_lab", icon = "public_order_jubilant.png"},
}

function IC.envoy_task(code)
    for i = 1, #IC.ENVOY_TASKS do
        if IC.ENVOY_TASKS[i].code == code then return IC.ENVOY_TASKS[i] end
    end
    return nil
end

function IC.envoy_effect(task)
    return string.format(task.fmt, IC.TUNE[task.knob])
end

-- "province:code" -> the province key and the task; either is nil when the
-- target is malformed. Province keys never hold a ":".
function IC.envoy_split(target)
    local province, code = string.match(tostring(target or ""), "^(.+):(%a+)$")
    return province, IC.envoy_task(code)
end

-- THE TURNS LEFT on a bundle already on the faction province, or nil.
function IC.envoy_running(faction_key, province_key, bundle)
    local region = IC.held_region(faction_key, province_key)
    if not region then return nil end
    local left = nil
    pcall(function()
        if not region:faction_province_has_effect_bundle(bundle) then return end
        left = 0
        local list = region:faction_province_effect_bundles()
        for i = 0, list:num_items() - 1 do
            local b = list:item_at(i)
            if b:key() == bundle then left = b:duration() end
        end
    end)
    return left
end

function IC.may_send_envoy(faction_key, target)
    local province, task = IC.envoy_split(target)
    if not province then return false, "no such task" end
    local held = false
    for _, p in ipairs(IC.seats(faction_key)) do
        if p == province then held = true end
    end
    if not held then return false, "lost" end
    if not task then return false, "no such task" end
    local left = IC.envoy_running(faction_key, province, task.bundle)
    if left then return false, "running", left end
    return true
end
```

- [ ] **Step 5: The rule and the effect**

`IC.may_target`, replace its first three lines' tail - after `if not plot then return false, "no such plot" end` and BEFORE `if not IC.plot_is_aimed(plot_key) then return true end`:

```lua
    -- A CIVIL MISSION'S TARGET IS A PLACE (spec 2026-09-29): the third argument
    -- is a "province:code" or a faction key, not a cqi, and a refusal that waits
    -- on turns returns them third.
    if plot.target == "province" then return IC.may_send_envoy(faction_key, cqi) end
```

`IC.can_plot`, its first two lines become:

```lua
    local ok, why, short = IC.may_target(faction_key, plot_key, target)
    if not ok then return false, why, short end
```

`IC.plot`: after `local court = IC.court(faction_key)` add `local plot = IC.plot_by_key(plot_key)`. In the failure branch, replace

```lua
        IC.log(faction_key, "plot_failed", slug,
               IC.plot_is_aimed(plot_key) and against or plot_key, cost)
```

with

```lua
        -- A MISSION'S LINE carries where it went (plan ruling 3); an errand's
        -- its own key, an aimed move's the party it was aimed at.
        IC.log(faction_key, "plot_failed", slug,
               IC.plot_is_aimed(plot_key) and against
               or (plot.target and (plot_key .. ":" .. tostring(target)))
               or plot_key, cost)
```

A branch after the `circuit` one:

```lua
    elseif plot_key == "envoy" then
        local province, task = IC.envoy_split(target)
        cm:apply_effect_bundle_to_faction_province(task.bundle,
            IC.held_region(faction_key, province), IC.TUNE.mission_turns)
```

and the success log line `IC.log(faction_key, plot_key, slug, against, cost)` becomes:

```lua
    -- A MISSION'S TARGET IS ITS PLACE, which is what its Record line names.
    IC.log(faction_key, plot_key, slug, plot.target and target or against, cost)
```

`IC.LOG_KINDS`, after `pledge = true, audience = true, circuit = true,`: `envoy = true, diplomats = true,`.

- [ ] **Step 6: The Record's line** (plan ruling 2: it names the party)

In `zzz_derpy_iron_court_ui.lua`, `ICUI.intrigue_text`, an arm beside `circuit`'s:

```lua
    elseif e.kind == "envoy" then
        local province, task = IC.envoy_split(e.key)
        if not province or not task then
            return string.format("%s sends an envoy. %d influence spent.", house, e.n or 0)
        end
        return string.format("%s spends %d influence sending an envoy to %s: %s "
            .. "for %d turns.", house, e.n or 0,
            loc("provinces_onscreen_" .. province, province), IC.envoy_effect(task),
            IC.TUNE.mission_turns)
```

- [ ] **Step 7: Run the harness, verify it passes**

Expected: `ok (N+4 checks)`.

---

### Task 2: Send Diplomats - the model and the save

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua` (`new_court` ~line 844; `IC.pack` ~line 1140; `IC.unpack` ~line 1224; `IC.PLOTS`; `IC.may_target`; `IC.plot`)
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua` (`ICUI.intrigue_text`, one arm)
- Modify: `tools/_iron_court_harness.lua` (the faction stub in `make_faction` ~line 245; new checks)

**Interfaces:**
- Consumes: Task 1's `target` field and the three-value `may_target`.
- Produces: plot row `diplomats` (`target = "faction"`); `IC.may_send_diplomats(faction_key, target) -> ok, why, turns`; `court.sent` (`[faction key] = turn sent`), saved as the court string's field 13. Harness faction stub: `is_rebel` (`f._rebel`), `is_human`, `at_war_with` (`f._wars[key]`), `diplomatic_attitude_towards`.

- [ ] **Step 1: The harness faction stub**

In `make_faction`'s faction table, beside `diplomatic_standing_with`:

```lua
        -- THE REGARD ON THE DIPLOMACY SCREEN. A faction KEY, as every CA use
        -- passes it (faction:name() in ogre contracts and the web of power).
        -- Answers what the bonuses applied between the two sum to.
        diplomatic_attitude_towards = function(_self, other)
            assert(type(other) == "string", "diplomatic_attitude_towards takes a faction key")
            return standing_of(name, other)
        end,
        -- AN INTERFACE, as CA's own calls pass it (episode_chaos_invasion).
        at_war_with = function(_self, other)
            assert(type(other) == "table" and other.name, "at_war_with takes a faction interface")
            return (f._wars or {})[other:name()] == true
        end,
        is_rebel = function() return f._rebel == true end,
        is_human = function() return IC.is_human(name) end,
```

(`import_iron_court.check_character_stub` holds every stub method against CA's member index; all four are CA members.)

- [ ] **Step 2: Write the failing checks**

```lua
local THEM = "wh3_main_emp_empire"

-- A FACTION `me` HAS MET, registered by make_faction so cm:get_faction finds
-- it. Returns its stub, for the check to set _rebel or _dead on.
local function met_faction(me, key)
    local them = make_faction(key, "wh_main_sc_emp_empire", {}, {})
    me._met = me._met or {}
    me._met[#me._met + 1] = key
    return them
end

check("diplomats raise a met faction's regard, then rest it", function()
    IC.state = {}
    bonuses = {}
    turn = 3
    local man = make_character(1401, ANY_SEAT, "crown")
    local me = make_faction(F, IC.CHD_SUBCULTURE, {man}, {"prov_a"})
    met_faction(me, THEM)
    IC.add_house(F, IC.CROWN)
    IC.court(F).standing[1401] = 1000
    rng({1})
    assert(IC.plot(F, "diplomats", 1401, THEM), "the diplomats were refused")
    rng(nil)
    -- (TARGET, PLAYER, n): their regard for you (spec 4.2).
    assert(#bonuses == 1 and bonuses[1].a == THEM and bonuses[1].b == F
           and bonuses[1].n == IC.TUNE.diplomats_bonus, "the bonus call was wrong")
    assert(IC.court(F).sent[THEM] == 3, "no rest was set")
    -- THE RECORD NAMES THE FACTION (plan ruling 2: and the party that sent).
    local line = ICUI.intrigue_text(IC.court(F).log[#IC.court(F).log])
    assert(line:find(THEM, 1, true) and line:find("regard", 1, true), line)
    local ok, why, left = IC.may_target(F, "diplomats", THEM)
    assert(not ok and why == "resting" and left == IC.TUNE.diplomats_rest,
        tostring(why) .. " " .. tostring(left))
    -- ONE TURN SHORT is still resting; the turn it ends is free.
    turn = 3 + IC.TUNE.diplomats_rest - 1
    assert(select(2, IC.may_target(F, "diplomats", THEM)) == "resting", "rested one turn short")
    turn = 3 + IC.TUNE.diplomats_rest
    assert(IC.may_target(F, "diplomats", THEM), "still resting after the rest")
    turn = 1
end)

check("a failed send pays, moves nobody and rests nobody", function()
    IC.state = {}
    bonuses = {}
    turn = 1
    local man = make_character(1411, ANY_SEAT, "crown")
    local me = make_faction(F, IC.CHD_SUBCULTURE, {man}, {"prov_a"})
    met_faction(me, THEM)
    IC.add_house(F, IC.CROWN)
    IC.court(F).standing[1411] = 1000
    rng({100})
    local ok, how = IC.plot(F, "diplomats", 1411, THEM)
    rng(nil)
    assert(ok and how == "failed", "the roll did not fail")
    assert(#bonuses == 0, "a failed send still moved them")
    assert(IC.court(F).sent[THEM] == nil, "a failed send rested the faction")
    assert(IC.court(F).standing[1411] == 1000 - IC.TUNE.plot_diplomats_cost, "a failure was free")
end)

check("diplomats are refused for the unmet, rebels, players, the dead and yourself",
function()
    IC.state = {}
    turn = 1
    local me = make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a"})
    IC.add_house(F, IC.CROWN)
    local function why(key) return select(2, IC.may_target(F, "diplomats", key)) end
    make_faction("wh3_main_ksl_kislev", "wh3_main_sc_ksl_kislev", {}, {})
    assert(why("wh3_main_ksl_kislev") == "unmet", "an unmet faction: " .. tostring(why("wh3_main_ksl_kislev")))
    met_faction(me, "wh2_main_rebels")._rebel = true
    assert(why("wh2_main_rebels") == "rebel", "a rebel: " .. tostring(why("wh2_main_rebels")))
    met_faction(me, "wh3_main_cth_cathay")
    local saved = cm.get_human_factions
    cm.get_human_factions = function() return {F, "wh3_main_cth_cathay"} end
    local human = why("wh3_main_cth_cathay")
    cm.get_human_factions = saved
    assert(human == "player", "another player: " .. tostring(human))
    met_faction(me, "wh3_main_dae_daemon_prince")._dead = true
    assert(why("wh3_main_dae_daemon_prince") == "lost", "the dead")
    assert(why(F) == "lost", "yourself")
    assert(why("no_such_faction") == "lost", "a faction that is not there")
end)

check("who is resting survives a save, and an older save rests nobody", function()
    IC.state = {}
    turn = 10
    make_faction(F, IC.CHD_SUBCULTURE, {}, {"prov_a"})
    IC.add_house(F, IC.CROWN)
    IC.court(F).sent = {[THEM] = 8, ["wh_old_faction"] = 2}
    local packed = IC.pack(F)
    local back = IC.unpack(F, packed)
    assert(back.sent[THEM] == 8, "the rest was lost on save")
    -- PRUNED: a rest that ended turns ago is not carried forward.
    assert(back.sent["wh_old_faction"] == nil, "an ended rest was saved")
    -- AN OLDER SAVE: twelve fields, no thirteenth.
    local old = string.gsub(packed, "|[^|]*$", "")
    assert(select(2, string.gsub(old, "|", "")) == 11, "the fixture is not a twelve-field save")
    local legacy = IC.unpack(F, old)
    assert(legacy.sent and next(legacy.sent) == nil, "an older save rests somebody")
    turn = 1
end)
```

- [ ] **Step 3: Run the harness, verify it fails**

Expected: FAIL on "diplomats raise a met faction's regard..." - `the diplomats were refused` (`no such plot`).

- [ ] **Step 4: Implement**

`new_court`, after `news = {},`: `sent     = {},   -- [faction key] = turn diplomats went (spec 2026-09-29)`.

`IC.PLOTS`, after the `envoy` entry:

```lua
    {key = "diplomats", name = "Send Diplomats", aimed = false, target = "faction",
     icon = "ui/campaign ui/ancillaries/wh3_main_anc_cathay_diplomat.png",
     cat = "mission",
     cost = "plot_diplomats_cost",
     effect = string.format(
         "A faction you have met regards you better. Not again there for %d turns.",
         IC.TUNE.diplomats_rest),
     blurb = "Gifts, threats and a long table. Other courts can be taught to like you."},
```

After `IC.may_send_envoy`:

```lua
-- ANY FACTION YOU HAVE MET that is alive, not a rebel, not a player and not
-- resting from the last send (spec 2026-09-29 section 4.1).
function IC.may_send_diplomats(faction_key, target)
    if not target or target == faction_key then return false, "lost" end
    local them = cm:get_faction(target)
    if not them or them:is_null_interface() or them:is_dead() then
        return false, "lost"
    end
    local met = false
    pcall(function()
        local list = cm:get_faction(faction_key):factions_met()
        for i = 0, list:num_items() - 1 do
            if list:item_at(i):name() == target then met = true end
        end
    end)
    if not met then return false, "unmet" end
    if them:is_rebel() then return false, "rebel" end
    if them:is_human() then return false, "player" end
    local sent = IC.court(faction_key).sent[target]
    if sent then
        local left = sent + IC.TUNE.diplomats_rest - cm:model():turn_number()
        if left > 0 then return false, "resting", left end
    end
    return true
end
```

`IC.may_target`, after the `province` line: `if plot.target == "faction" then return IC.may_send_diplomats(faction_key, cqi) end`.

`IC.plot`, a branch after the `envoy` one:

```lua
    elseif plot_key == "diplomats" then
        -- (TARGET, PLAYER): their regard for you. The rest is set on SUCCESS
        -- only - a failed send bought nothing, and resting too would charge twice.
        cm:apply_dilemma_diplomatic_bonus(target, faction_key, IC.TUNE.diplomats_bonus)
        court.sent[target] = cm:model():turn_number()
```

`IC.pack`: before the final `return join({...})`:

```lua
    -- WHERE DIPLOMATS WENT (spec 2026-09-29 section 4.3): only the rests still
    -- running, so the field never outgrows diplomats_rest turns of sending.
    local sent = {}
    local now = cm:model():turn_number()
    for key, t in pairs(court.sent or {}) do
        if t + IC.TUNE.diplomats_rest > now then
            sent[#sent + 1] = key .. "," .. tostring(t)
        end
    end
    table.sort(sent)
```

and the last line of that `join({...}, "|")` - field 13 goes on the SAME line, which is the line Task 5's mutant anchors on:

```lua
                 join(stalled, ";"), join(news, ";"), join(sent, ";")}, "|")
```

replacing

```lua
                 join(stalled, ";"), join(news, ";")}, "|")
```

`IC.unpack`, after the field-12 loop:

```lua
    -- Field 13 is optional: a save from before the missions rests nobody.
    for _, entry in ipairs(split(fields[13] or "", ";")) do
        local b = split(entry, ",")
        local t = tonumber(b[2])
        if b[1] and t then court.sent[b[1]] = t end
    end
```

`ICUI.intrigue_text`, an arm after the `envoy` one:

```lua
    elseif e.kind == "diplomats" then
        return string.format("%s spends %d influence sending diplomats to %s. "
            .. "Their regard for you rose.", house, e.n or 0,
            loc("factions_screen_name_" .. tostring(e.key), tostring(e.key)))
```

- [ ] **Step 5: Run the harness, verify it passes**

Expected: `ok (N+8 checks)`.

---

### Task 3: The four bundles (data)

**Files:**
- Modify: `tools/gen_iron_court.py` (effect tuples ~line 40; `ALL_EFFECTS` ~line 88; `EFFECT_TEXT` ~line 333; `EFFECT_SHORT` ~line 366; `EFFECT_PERCENT` ~line 387; `EFFECT_TEXT_TR` ~line 404; `emit()` in `build()` ~line 1207; after `model_moves()` ~line 1165; `check()` item 2 ~line 2098 and a new item; `selftest()`)

**Interfaces:**
- Consumes: Task 1's `IC.ENVOY_TASKS` and `IC.TUNE.envoy_*`, read out of the shipped Lua.
- Produces: bundles `derpy_ic_envoy_ctl|arm|raw|lab` (target `province`, CA icons), their junctions and loc; `model_tune(name) -> int`; `model_envoy_tasks() -> [(code, name, knob, bundle, icon)]`; `BORROWED_SCOPES`.

- [ ] **Step 1: The effects**

After `E_HOBGOBLIN` (~line 86):

```python
# THE ENVOY'S FOUR (spec 2026-09-29 section 6): CA's province-bundle shape, every
# effect province_to_province_own_unseen - the scope CA's Higher Quotas and Smoke
# Stacks edicts and its mood bundles give them. Signs measured off the vanilla
# cache 2026-09-29: labour loss is the one where less is better.
E_ENVOY_CTL = ("wh_main_effect_public_order_edict",
               "province_to_province_own_unseen", True)
E_ENVOY_ARM = ("wh3_dlc23_pooled_resource_chd_armaments_modifier",
               "province_to_province_own_unseen", True)
E_ENVOY_RAW = ("wh3_dlc23_pooled_resource_chd_raw_material_efficiency",
               "province_to_province_own_unseen", True)
E_ENVOY_LAB = ("wh3_dlc23_pooled_resource_chd_increased_labour_loss",
               "province_to_province_own_unseen", False)
ENVOY_EFFECT = {"ctl": E_ENVOY_CTL, "arm": E_ENVOY_ARM,
                "raw": E_ENVOY_RAW, "lab": E_ENVOY_LAB}
ENVOY_BLURB = {
    "ctl": "An envoy of the court is keeping order here.",
    "arm": "An envoy of the court is driving the forges here.",
    "raw": "An envoy of the court is working the mines here harder.",
    "lab": "An envoy of the court is seeing that fewer labourers are worked to death here.",
}
# ONE PAIR CA DOES NOT SHIP, KEPT ON PURPOSE (plan ruling 5). CA's only province
# bundle scope for raw materials is province_to_province_own_factionwide - every
# province - so the edict's scope is borrowed. Only the game can say it moves
# (spec section 8, look 3); check 2 refuses every OTHER unshipped pair.
BORROWED_SCOPES = {
    (E_ENVOY_RAW[0], E_ENVOY_RAW[1]):
        "spec 2026-09-29 section 6: the edict scope, borrowed for one province",
}
```

`ALL_EFFECTS` gains `E_ENVOY_CTL, E_ENVOY_ARM, E_ENVOY_RAW, E_ENVOY_LAB` at its end.

`EFFECT_TEXT` gains (CA's wording, read 2026-09-29 by `read_vanilla_loc`; check 15 re-reads it):

```python
    E_ENVOY_CTL[0]: "Control: %+n",
    E_ENVOY_LAB[0]: "%n% Labour loss per turn (minimum of 5)",
```

`EFFECT_TEXT_TR` gains `E_ENVOY_CTL[0]: ("public_order_effect", "Control"),`. `EFFECT_SHORT` gains `E_ENVOY_CTL[0]: "Control",` and `E_ENVOY_LAB[0]: "Labour loss",`. `EFFECT_PERCENT` gains `E_ENVOY_CTL[0]: False,`.

- [ ] **Step 2: Read the tasks and knobs out of the Lua**

After `model_moves()`:

```python
def _model_lua():
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "Modding Files", "pack", "script", "campaign", "mod",
        "zzz_derpy_iron_court.lua")
    return io.open(path, encoding="utf-8").read()


# RAISES RATHER THAN FALLING BACK, like model_moves: these feed build(), and a
# silent default is a bundle whose value is not the card's.
def model_tune(name):
    """IC.TUNE[name] as the shipped Lua declares it."""
    m = re.search(r"\n\s+%s\s*=\s*(\d+)\s*," % re.escape(name), _model_lua())
    if not m:
        raise RuntimeError("the model Lua declares no IC.TUNE.%s" % name)
    return int(m.group(1))


def model_envoy_tasks():
    """[(code, name, knob, bundle, icon)] from IC.ENVOY_TASKS, in its order."""
    block = re.search(r"IC\.ENVOY_TASKS = \{(.*?)\n\}", _model_lua(), re.S)
    if not block:
        raise RuntimeError("the model Lua declares no IC.ENVOY_TASKS")
    tasks = re.findall(
        r'\{code = "(\w+)", name = "([^"]+)", knob = "(\w+)", fmt = "[^"]*",\s*'
        r'bundle = "(\w+)", icon = "([^"]+)"\}', block.group(1))
    if len(tasks) != 4:
        raise RuntimeError("IC.ENVOY_TASKS parsed to %d tasks, not 4" % len(tasks))
    return tasks
```

- [ ] **Step 3: Emit the bundles**

`emit()` gains `icon=None` as its last parameter and writes `"ui_icon": icon or BUNDLE_ICON,`. In `build()`, after the `gov_house` loop:

```python
    # THE ENVOY'S FOUR (spec 2026-09-29 section 6): one province, for
    # IC.TUNE.mission_turns, in CA's province-bundle shape. The value is the
    # model's own knob (plan ruling 4).
    for code, name, knob, bundle, icon in model_envoy_tasks():
        emit(bundle, "Envoy: " + name, ENVOY_BLURB[code], "province",
             [(ENVOY_EFFECT[code], model_tune(knob), BOON)], icon=icon)
```

- [ ] **Step 4: The two checks**

In `check()` item 2, the refusal line becomes:

```python
        for effect in ALL_EFFECTS:
            if ((effect[0], effect[1]) not in pairs
                    and (effect[0], effect[1]) not in BORROWED_SCOPES):
```

and a new item after item 4:

```python
    # 4b. EVERY BUNDLE'S ICON EXISTS (plan ruling 6). ui_icon is a bare name
    #     under ui/campaign ui/effect_bundles/; a wrong one draws a blank square
    #     with no error, and nothing checked it before 2026-09-29.
    try:
        import gen_iron_court_emitter as _EU
        assets = _EU._game_assets()
    except Exception as exc:
        out.append("game ui assets unreadable, cannot verify bundle icons: %r" % (exc,))
    else:
        for row in tables["effect_bundles"]:
            path = "ui/campaign ui/effect_bundles/" + row["ui_icon"]
            if path.lower() not in assets and path not in assets:
                out.append("bundle %s wears an icon the game does not have: %s"
                           % (row["key"], row["ui_icon"]))
```

and in `selftest()`, after the `ALL_EFFECTS[3]` "invented effect key" case (~line 2880), two cases in the file's own `injected(fault, restore, needle)` shape. `BUNDLE_ICON` is swapped through `globals()` because `selftest()` is a function and a `global` statement after any read of the name is a SyntaxError:

```python
    # A BUNDLE ICON THE GAME DOES NOT SHIP (plan ruling 6). emit() reads the
    # module's BUNDLE_ICON at build time, and check() builds afresh.
    _icon = BUNDLE_ICON
    globals()["BUNDLE_ICON"] = "no_such_icon.png"
    injected("a bundle icon the game does not ship",
             lambda: globals().__setitem__("BUNDLE_ICON", _icon),
             "an icon the game does not have")

    # THE BORROWED SCOPE IS EXEMPT BY PAIR, NOT BY EFFECT (plan ruling 5): the
    # same effect on any other unshipped scope is still refused.
    _i = ALL_EFFECTS.index(E_ENVOY_RAW)
    ALL_EFFECTS[_i] = (E_ENVOY_RAW[0], "province_to_region_own_unseen_TYPO", True)
    injected("the borrowed scope's exemption stretched to another scope",
             lambda: ALL_EFFECTS.__setitem__(_i, E_ENVOY_RAW), "not shipped by CA")
```

- [ ] **Step 5: Generate and gate**

Run: `py tools/gen_iron_court.py --check` then `py tools/gen_iron_court.py --selftest`
Expected: no findings; `selftest: ok`.
Run: `py tools/check_effect_bundle_loc.py`; `py tools/check_effect_signs.py`
Expected: the first clean; the second lists `derpy_ic_envoy_lab` at `-15.0` as a BENEFIT (is_positive_value_good false) - read the row against its blurb and confirm, as the report asks.
Run the harness. Expected: unchanged count, ok.

---

### Task 4: The panel

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua` (`ICUI.intrigue_text` ~line 4676; `ICUI.plot_label` ~line 4895; the help page lines ~line 5241; `ICUI.TARGET_REFUSAL` / `ICUI.PICK_HEADERS` ~line 5608; `ICUI.reason_text` ~line 5620; `ICUI.pick_title` ~line 5748; `ICUI.draw_picker` ~line 5935; `ICUI.on_pick_click` ~line 6210; the header block in the dispatcher ~line 6309; `ICUI.on_plot_click` ~line 6730)
- Modify: `tools/_iron_court_harness.lua` (new checks)

**Interfaces:**
- Consumes: Tasks 1-2's model functions.
- Produces: pick kinds `envoy_province` (`{kind, plot}`), `envoy_task` (`{kind, plot, province}`), `diplomats_faction` (`{kind, plot}`); `ICUI.MISSION_PICKS` (kind -> five header captions); `ICUI.mission_place(plot_key, target) -> text`; `ICUI.mission_rows(faction) -> lines, keys`; `ICUI.mission_refusal(why, turns) -> label`.

- [ ] **Step 1: Write the failing checks**

```lua
-- THE ACTION CELLS AND FIRST CELLS OF EVERY DRAWN ROW, markup stripped.
local function picker_rows(panel)
    local out = {}
    for i = 1, ICUI.MAX_ROWS do
        local row = panel.children[ICUI.ROW .. "_" .. i]
        if row and row.visible and row.children.ic_row_a.text ~= "" then
            out[#out + 1] = {a = plain(row.children.ic_row_a.text),
                             d = plain(row.children.ic_row_d.text),
                             e = plain(row.children.ic_row_e.text)}
        end
    end
    return out
end

check("the Envoy walks province, then task, then the man who goes", function()
    IC.state = {}
    prov_bundles = {}
    turn = 1
    local man = make_character(1501, ANY_SEAT, "crown")
    make_faction(F, IC.CHD_SUBCULTURE, {man}, {"prov_a", "prov_b"})
    IC.add_house(F, IC.CROWN)
    IC.court(F).standing[1501] = 1000
    prov_bundles.prov_b = {derpy_ic_envoy_arm = 2}
    ICUI.pick = nil
    -- THE ROW OR CARD A CLICK LANDED ON, as the card-click checks set it: the
    -- fake tree has no parent chain for clicked_index to read.
    local at = nil
    local saved_idx = ICUI.clicked_index
    ICUI.clicked_index = function() return at end
    local ok, err = pcall(with_fake_panel, function(panel)
        ICUI.view = "intrigue"
        ICUI.refresh()
        -- THE ENVOY'S CARD opens the province list.
        for i, move in pairs(ICUI.plot_keys) do if move.plot == "envoy" then at = i end end
        assert(at, "no Envoy card on the grid")
        ICUI.on_plot_click({component = {}})
        assert(ICUI.pick and ICUI.pick.kind == "envoy_province", "the card opened " .. tostring(ICUI.pick and ICUI.pick.kind))
        local rows = picker_rows(panel)
        assert(#rows == 2 and rows[1].a == "prov_a" and rows[2].a == "prov_b", "the provinces listed")
        assert(rows[2].d:find("Armaments 2", 1, true), "prov_b's running work reads " .. rows[2].d)
        -- PROVINCE -> TASK.
        at = 2
        ICUI.on_pick_click({component = {}}, F)
        assert(ICUI.pick.kind == "envoy_task" and ICUI.pick.province == "prov_b", "no task list for prov_b")
        ICUI.refresh()
        rows = picker_rows(panel)
        assert(#rows == 4, #rows .. " tasks")
        assert(rows[2].a == "Armaments" and rows[2].e == "Running 2", "the running task reads " .. rows[2].e)
        assert(rows[1].e == "Choose", "a free task reads " .. rows[1].e)
        -- A REFUSED TASK DOES NOTHING ON CLICK.
        at = 2
        assert(not ICUI.on_pick_click({component = {}}, F), "a running task answered the click")
        assert(ICUI.pick.kind == "envoy_task", "a running task was taken")
        -- TASK -> MAN, the target written the way the model splits it.
        at = 1
        ICUI.on_pick_click({component = {}}, F)
        assert(ICUI.pick.kind == "plot" and ICUI.pick.plot == "envoy" and ICUI.pick.key == "prov_b:ctl",
            "the man's picker carries " .. tostring(ICUI.pick.key))
        assert(ICUI.pick_title():find("prov_b", 1, true), ICUI.pick_title())
    end)
    ICUI.clicked_index = saved_idx
    ICUI.pick = nil
    assert(ok, err)
end)

check("Diplomats list the factions met, refused ones say why", function()
    IC.state = {}
    turn = 1
    local man = make_character(1511, ANY_SEAT, "crown")
    local me = make_faction(F, IC.CHD_SUBCULTURE, {man}, {"prov_a"})
    IC.add_house(F, IC.CROWN)
    me._met = {"wh3_main_emp_empire", "wh2_main_rebels", "wh3_main_dae_daemon_prince"}
    make_faction("wh3_main_emp_empire", "wh_main_sc_emp_empire", {}, {})
    make_faction("wh2_main_rebels", "wh_main_sc_grn_orcs", {}, {})._rebel = true
    make_faction("wh3_main_dae_daemon_prince", "wh3_main_sc_dae_daemons", {}, {})._dead = true
    IC.court(F).sent = {["wh3_main_emp_empire"] = 1}
    ICUI.pick = {kind = "diplomats_faction", plot = "diplomats"}
    local ok, err = pcall(with_fake_panel, function(panel)
        ICUI.refresh()
        local rows = picker_rows(panel)
        -- THE DEAD ARE LEFT OFF (ruling 9); the rest are drawn, refused or not.
        assert(#rows == 2, #rows .. " factions listed")
        local by = {}
        for _, r in ipairs(rows) do by[r.a] = r.e end
        assert(by["wh3_main_emp_empire"] == "Rest " .. IC.TUNE.diplomats_rest, tostring(by["wh3_main_emp_empire"]))
        assert(by["wh2_main_rebels"] == "Rebel", tostring(by["wh2_main_rebels"]))
        assert(plain(panel.children.ic_hdr_a.text) == ICUI.MISSION_PICKS.diplomats_faction[1],
            "the headers are the character list's")
        assert(not panel.children.ic_hsort_a.visible, "a sort arrow over a list that does not sort")
    end)
    ICUI.pick = nil
    assert(ok, err)
end)

check("every mission refusal has a sentence and a label", function()
    for _, why in ipairs({"running", "resting", "lost", "unmet", "rebel", "player", "no such task"}) do
        local text = ICUI.reason_text(why, 3)
        assert(text ~= "That cannot be done right now.", why .. " has no sentence")
        assert(not text:find("%d", 1, true), why .. " printed a raw format")
    end
    assert(ICUI.mission_refusal("running", 3) == "Running 3")
    assert(ICUI.mission_refusal("resting", 2) == "Rest 2")
    assert(ICUI.mission_refusal("rebel") == "Rebel" and ICUI.mission_refusal("player") == "Player")
    assert(ICUI.mission_refusal("lost") == "No")
end)

check("a failed mission's Record line names where it went", function()
    local line = ICUI.intrigue_text({turn = 1, kind = "plot_failed", slug = "crown",
                                     key = "envoy:prov_a:lab", n = 120})
    assert(line:find("Send an Envoy", 1, true) and line:find("prov_a", 1, true), line)
    line = ICUI.intrigue_text({turn = 1, kind = "plot_failed", slug = "crown",
                               key = "diplomats:wh3_main_emp_empire", n = 100})
    assert(line:find("Send Diplomats", 1, true)
           and line:find("wh3_main_emp_empire", 1, true), line)
    -- AN ERRAND'S FAILURE still reads as it did (its key has no ":").
    line = ICUI.intrigue_text({turn = 1, kind = "plot_failed", slug = "crown",
                               key = "circuit", n = 110})
    assert(line:find("Ride the Circuit", 1, true), line)
end)
```

- [ ] **Step 2: Run the harness, verify it fails**

Expected: FAIL on "the Envoy walks..." with `the card opened plot` (the card routes to the man's picker today).

- [ ] **Step 3: Routing and chaining**

`ICUI.on_plot_click`, replace the `if IC.plot_is_aimed(move.plot) then ... end` block with:

```lua
    -- A MISSION ASKS FOR ITS PLACE FIRST (spec 2026-09-29 section 5): a
    -- province, then a task; or a faction. Then the man, as every move.
    local plot = IC.plot_by_key(move.plot)
    if plot and plot.target == "province" then
        ICUI.pick = {kind = "envoy_province", plot = move.plot}
    elseif plot and plot.target == "faction" then
        ICUI.pick = {kind = "diplomats_faction", plot = move.plot}
    elseif IC.plot_is_aimed(move.plot) then
        ICUI.pick = {kind = "plot_target", plot = move.plot}
    else
        ICUI.pick = {kind = "plot", plot = move.plot, key = nil}
    end
```

`ICUI.on_pick_click`, two branches before the final `else` (the `gov` one):

```lua
    elseif ICUI.pick.kind == "envoy_province" then
        -- THE FIRST OF THREE QUESTIONS: `chosen` is the province key.
        ICUI.pick = {kind = "envoy_task", plot = ICUI.pick.plot, province = chosen}
        ICUI.scroll.pick = 0
        ICUI.notice = nil
        return true
    elseif ICUI.pick.kind == "envoy_task" or ICUI.pick.kind == "diplomats_faction" then
        -- `chosen` IS THE TARGET the model splits: "province:code", or a faction.
        ICUI.pick = {kind = "plot", plot = ICUI.pick.plot, key = chosen}
        ICUI.scroll.pick = 0
        ICUI.notice = nil
        return true
```

- [ ] **Step 4: The rows**

Beside `ICUI.PICK_HEADERS`:

```lua
-- THE MISSION PICKERS' OWN HEADERS (plan ruling 8): a place or a faction per
-- row, not a man, and no sort - so no arrows and no lit column either.
ICUI.MISSION_PICKS = {
    envoy_province    = {"Province", "Overseer", "Control", "Under way", ""},
    envoy_task        = {"Task", "What it does", "", "", ""},
    diplomats_faction = {"Faction", "At war", "Regard", "", ""},
}

-- A REFUSED ROW'S BUTTON, from the model's own refusal.
function ICUI.mission_refusal(why, turns)
    if why == "running" then return string.format("Running %d", turns or 0) end
    if why == "resting" then return string.format("Rest %d", turns or 0) end
    if why == "rebel" then return "Rebel" end
    if why == "player" then return "Player" end
    return "No"
end

-- WHERE A MISSION GOES, in words: "Gash Kadrak, Armaments", or a faction's name.
function ICUI.mission_place(plot_key, target)
    if plot_key == "envoy" then
        local province, task = IC.envoy_split(target)
        if not province then return tostring(target) end
        local name = loc("provinces_onscreen_" .. province, province)
        return task and (name .. ", " .. task.name) or name
    end
    return loc("factions_screen_name_" .. tostring(target), tostring(target))
end

-- THE ROWS OF THE OPEN MISSION PICKER, and the key each row sends (nil when
-- refused). Every refusal is the model's: IC.may_target is asked with the
-- exact target the click would send.
function ICUI.mission_rows(faction)
    local kind, plot = ICUI.pick.kind, ICUI.pick.plot
    local lines, keys = {}, {}
    local function add(cells, target)
        local may, why, turns = true, nil, nil
        if target then may, why, turns = IC.may_target(faction, plot, target) end
        cells[5] = may and "Choose" or ICUI.red(ICUI.mission_refusal(why, turns))
        cells.tip = (not may) and ICUI.reason_text(why, turns) or nil
        lines[#lines + 1] = cells
        keys[#lines] = may and (cells.key or target) or nil
    end
    if kind == "envoy_province" then
        local court = IC.court(faction)
        for _, province in ipairs(IC.seats(faction)) do
            local cqi = court.govs[province]
            local holder = cqi and IC.character_by_cqi(faction, cqi) or nil
            local region = IC.held_region(faction, province)
            local order = 0
            if region then pcall(function() order = region:public_order() end) end
            local running = {}
            for _, task in ipairs(IC.ENVOY_TASKS) do
                local left = IC.envoy_running(faction, province, task.bundle)
                if left then running[#running + 1] = task.name .. " " .. left end
            end
            -- A PROVINCE IS NOT REFUSED: its tasks are, one list on.
            add({loc("provinces_onscreen_" .. province, province),
                 ICUI.gov_holder_text(faction, province, holder, cqi),
                 tostring(order),
                 #running > 0 and table.concat(running, ", ") or "None",
                 key = province}, nil)
        end
    elseif kind == "envoy_task" then
        for _, task in ipairs(IC.ENVOY_TASKS) do
            add({task.name, IC.envoy_effect(task) .. string.format(" for %d turns",
                 IC.TUNE.mission_turns), "", "",
                 icon = "ui/campaign ui/effect_bundles/" .. task.icon, icon_kind = "crest"},
                ICUI.pick.province .. ":" .. task.code)
        end
    elseif kind == "diplomats_faction" then
        local me = cm:get_faction(faction)
        local met = {}
        pcall(function()
            local list = me:factions_met()
            for i = 0, list:num_items() - 1 do
                local them = cm:get_faction(list:item_at(i):name())
                -- THE DEAD ARE LEFT OFF (plan ruling 9).
                if them and not them:is_null_interface() and not them:is_dead() then
                    met[#met + 1] = {key = them:name(), faction = them,
                                     name = loc("factions_screen_name_" .. them:name(), them:name())}
                end
            end
        end)
        table.sort(met, function(a, b)
            if a.name ~= b.name then return a.name < b.name end
            return a.key < b.key
        end)
        for _, m in ipairs(met) do
            local war, regard = false, 0
            pcall(function() war = me:at_war_with(m.faction) end)
            pcall(function() regard = m.faction:diplomatic_attitude_towards(faction) end)
            add({m.name, war and "At war" or "At peace",
                 string.format("%d", math.floor((regard or 0) + 0.5)), ""}, m.key)
        end
    end
    return lines, keys
end
```

`ICUI.draw_picker`, right after `ICUI.pick_rows = {}`:

```lua
    -- THE MISSION PICKERS draw places and factions, not men (spec 2026-09-29).
    if ICUI.MISSION_PICKS[ICUI.pick.kind] then
        local rows, keys = ICUI.mission_rows(faction)
        ICUI.pick_rows = keys
        if #rows == 0 then rows[1] = {"Nowhere to send.", "", "", "", ""} end
        ICUI.fill_rows(panel, rows, "pick")
        return ""
    end
```

In the dispatcher's header block (~line 6309), replace `if ICUI.pick then headers = ICUI.HEADERS[view] or ICUI.PICK_HEADERS end` with:

```lua
    local mission = ICUI.pick and ICUI.MISSION_PICKS[ICUI.pick.kind]
    if ICUI.pick then headers = mission or ICUI.HEADERS[view] or ICUI.PICK_HEADERS end
```

and add `and not mission` to both the `local active = ...` expression and the `local sortable = ...` expression in the loop below it.

- [ ] **Step 5: Titles, labels, sentences, the Record, the help page**

`ICUI.pick_title`, before the `plot_target` branch:

```lua
    local plot = ICUI.pick.plot and IC.plot_by_key(ICUI.pick.plot)
    if ICUI.pick.kind == "envoy_province" then
        return string.format("%s - to which province?", plot.name)
    elseif ICUI.pick.kind == "envoy_task" then
        return string.format("%s - what does he do in %s?", plot.name,
            loc("provinces_onscreen_" .. ICUI.pick.province, ICUI.pick.province))
    elseif ICUI.pick.kind == "diplomats_faction" then
        return string.format("%s - to whom?", plot.name)
    end
```

`ICUI.plot_label`, after `if not target then return plot.name end`:

```lua
    if plot.target then
        return string.format("%s: %s", plot.name, ICUI.mission_place(plot_key, target))
    end
```

`ICUI.reason_text`, before the final `return`:

```lua
    elseif why == "running" then
        return string.format("That work is already under way there, for another "
            .. "%d turn%s.", spare or 0, spare == 1 and "" or "s")
    elseif why == "resting" then
        return string.format("Your diplomats were there too recently. Send again "
            .. "in %d turn%s.", spare or 0, spare == 1 and "" or "s")
    elseif why == "lost" then
        return "That province or faction is no longer there to send to."
    elseif why == "unmet" then
        return "You have not met them. Diplomats need somewhere to go."
    elseif why == "rebel" then
        return "Rebels keep no court to send diplomats to."
    elseif why == "player" then
        return "That is another player. Talk to them yourself."
    elseif why == "no such task" then
        return "No such task."
```

(Insert as `elseif` arms inside the existing chain, before its closing `end`.)

`ICUI.intrigue_text` (the success lines went in with Tasks 1 and 2), the top of the `plot_failed` arm:

```lua
    elseif e.kind == "plot_failed" then
        -- A MISSION'S LINE carries where it went (plan ruling 3).
        local mission, where = string.match(e.key or "", "^(%a+):(.+)$")
        local sent = mission and IC.plot_by_key(mission)
        if sent then
            return string.format("%s to %s comes to nothing for %s. %d influence spent.",
                sent.name, ICUI.mission_place(mission, where), house, e.n or 0)
        end
```

(the existing errand and aimed lines follow unchanged).

Help page (Intrigue section), after the Errands line:

```lua
        "{@bullet}Missions: {@envoy}send an envoy to work in one of your provinces for a few turns, or {@diplomats}send diplomats to a faction you have met.",
```

and the Crown line becomes `"{@crown}Only Crown men can act, and a man sent on an errand or a mission must not be leading an army.",`. (`ICUI.help_icon` falls back to a move's own icon, so `{@envoy}` and `{@diplomats}` need no table entry.)

- [ ] **Step 6: Run the harness, verify it passes**

Expected: `ok (N+12 checks)`.

---

### Task 5: Fit, preview, mutants, gates, build, docs

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua` (card text only, if the fit check asks)
- Modify: `tools/mutate_iron_court.py` (`MUTANTS`)
- Modify: `docs/sessions/PATCH_NOTES_20260925_IRON_COURT.md`, the current Iron Court handoff (a new section), `docs/SESSION_INDEX.md`

- [ ] **Step 1: The five-column grid**

Run: `py tools/gen_ic_ui.py` then `py tools/gen_ic_ui.py --check`.
Expected: the grid is now 5 x 4 at 364px cards. Any card whose name, effect or blurb no longer fits is reported by the card-cell check (20d). Fix a finding by shortening THAT move's wording in `IC.PLOTS` (plain words, same meaning, same numbers), never by loosening the check. Re-run until clean, then `py tools/gen_ic_ui.py --selftest` (about 11 minutes).
Run: `py tools/preview_iron_court.py`, open `ic_intrigue.png`: five columns, the Missions header, both new cards with their icons, nothing clipped.

- [ ] **Step 2: Mutants**

Append to `MUTANTS` (each anchor must match exactly once):

```python
    # THE CIVIL MISSIONS (plan 2026-09-29).
    ("an envoy's work on the wrong province", M,
     """            IC.held_region(faction_key, province), IC.TUNE.mission_turns)""",
     """            IC.held_region(faction_key, IC.seats(faction_key)[1]), IC.TUNE.mission_turns)"""),
    ("an envoy's work forever", M,
     """            IC.held_region(faction_key, province), IC.TUNE.mission_turns)""",
     """            IC.held_region(faction_key, province), -1)"""),
    ("the same work sent twice", M,
     """    if left then return false, "running", left end""",
     """"""),
    ("a lost province still sent to", M,
     """    if not held then return false, "lost" end""",
     """"""),
    ("an unknown task sent", M,
     """    if not task then return false, "no such task" end
    local left""",
     """    local left"""),
    # NOT the return line: "if not ok then return false, why, short end" is
    # already in the model twice before can_plot gains a third.
    ("a refusal's turns dropped by can_plot", M,
     """    local ok, why, short = IC.may_target(faction_key, plot_key, target)""",
     """    local ok, why = IC.may_target(faction_key, plot_key, target)"""),
    ("a failed mission logged without its place", M,
     """               or (plot.target and (plot_key .. ":" .. tostring(target)))""",
     """               or (plot.target and plot_key)"""),
    ("a mission's success logged without its place", M,
     """    IC.log(faction_key, plot_key, slug, plot.target and target or against, cost)""",
     """    IC.log(faction_key, plot_key, slug, against, cost)"""),
    ("the diplomatic bonus the wrong way round", M,
     """        cm:apply_dilemma_diplomatic_bonus(target, faction_key, IC.TUNE.diplomats_bonus)""",
     """        cm:apply_dilemma_diplomatic_bonus(faction_key, target, IC.TUNE.diplomats_bonus)"""),
    ("diplomats never resting", M,
     """        court.sent[target] = cm:model():turn_number()""",
     """"""),
    ("the rest one turn long", M,
     """        local left = sent + IC.TUNE.diplomats_rest - cm:model():turn_number()""",
     """        local left = sent + IC.TUNE.diplomats_rest + 1 - cm:model():turn_number()"""),
    ("diplomats to the unmet", M,
     """    if not met then return false, "unmet" end""",
     """"""),
    ("diplomats to rebels", M,
     """    if them:is_rebel() then return false, "rebel" end""",
     """"""),
    ("diplomats to another player", M,
     """    if them:is_human() then return false, "player" end""",
     """"""),
    ("diplomats to the dead", M,
     """    if not them or them:is_null_interface() or them:is_dead() then""",
     """    if not them or them:is_null_interface() then"""),
    ("the rest not saved", M,
     """                 join(stalled, ";"), join(news, ";"), join(sent, ";")}, "|")""",
     """                 join(stalled, ";"), join(news, ";")}, "|")"""),
    ("an ended rest saved", M,
     """        if t + IC.TUNE.diplomats_rest > now then""",
     """        if true then"""),
    ("the Envoy's card opening the man's picker", U,
     """    if plot and plot.target == "province" then""",
     """    if false then"""),
    ("a running task's row clickable", U,
     """        keys[#lines] = may and (cells.key or target) or nil""",
     """        keys[#lines] = cells.key or target"""),
    ("the dead listed for diplomats", U,
     """                if them and not them:is_null_interface() and not them:is_dead() then""",
     """                if them and not them:is_null_interface() then"""),
    ("sort arrows over a mission list", U,
     """    if ICUI.pick then headers = mission or ICUI.HEADERS[view] or ICUI.PICK_HEADERS end""",
     """    if ICUI.pick then headers = ICUI.HEADERS[view] or ICUI.PICK_HEADERS end"""),
    ("the task target written wrong", U,
     """                ICUI.pick.province .. ":" .. task.code)""",
     """                ICUI.pick.province .. "|" .. task.code)"""),
    ("a failed mission's Record line losing its place", U,
     """        local mission, where = string.match(e.key or "", "^(%a+):(.+)$")""",
     """        local mission, where = nil, nil"""),
```

Run: `py tools/mutate_iron_court.py "envoy" "work" "task" "lost province" "refusal's turns" "mission" "diplomat" "rest" "Envoy's card" "running task" "dead" "sort arrows" "Record line"`.
Expected: every one `caught`, `0 unexplained`. A survivor is a missing check: write the check that catches it (watched failing against the mutant first), never delete the mutant.

- [ ] **Step 3: Full gates**

In order, nothing beside the mutation run:
- the harness -> `ok (N+12 checks)`
- `luac -p` on the Iron Court Lua files; `py tools/check_lua_api.py` on them; `py tools/check_lua_literal_left.py` on them; `py tools/check_lua_undeclared.py` on them
- `py tools/gen_iron_court.py --check` and `--selftest`; `py tools/check_effect_bundle_loc.py`; `py tools/check_effect_signs.py`
- `py tools/gen_ic_ui.py --check` (and `--selftest` if Step 1 changed any wording since its last run)
- `py tools/import_iron_court.py` -> `verify ok`
- `py tools/preview_iron_court.py --check`
- `py tools/mutate_iron_court.py` (full, in the background) -> `N mutants, 0 unexplained`
- `py tools/sync_iron_court_repo.py --selftest`

- [ ] **Step 4: Build and deploy**

With RPFM open: `py tools/deploy_iron_court.py`. With the game shut it deploys and byte-compares. Record the build name (the first eight hex digits of the pack's md5, uppercased).

- [ ] **Step 5: Docs**

- Patch notes, New: `[*][b]Civil missions.[/b] A Missions column on the Intrigue tab. Send an Envoy to one of your provinces for five turns of better control, armaments, raw materials or fewer labourers lost; or Send Diplomats to a faction you have met to improve how they regard you.` Header: the build that carries it, deployed, not pushed.
- Handoff: the build name, the ten rulings above, the check and mutant counts, and the five in-game looks the spec's section 8 owes (the bundle in the province's effects with its turns; the control breakdown's label - if it names an edict, the control row moves to `wh_main_effect_public_order_faction` and its bundle to the governor's faction target; armaments and raw materials move; the labour figure moves; the diplomacy screen shows the modifier).
- `docs/SESSION_INDEX.md`: the civil missions spec line changes from DESIGN to BUILT with the build name.
