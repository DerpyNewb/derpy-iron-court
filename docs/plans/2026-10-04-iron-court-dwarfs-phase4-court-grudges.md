# Iron Court for Dwarfs - Phase 4: grudges inside the court Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give every Dwarf court a book of grudges per party: each wrong the ruler does them (the Slayer Oath, Cast Out, the Insult, Bar Them from the Hall, Recall Governors, an early dismissal, a broken oath, a refused demand, and phase 5's peace with a named foe) writes a grudge that costs -1 loyalty a turn, never fades, four at most per party; Pay the Weregild (gold) or a seat they claim settles the oldest; every Dwarf party has a +1 "Kin of the Karak" term and secedes half again as slowly; the Iron Law makes the three oath moves a third cheaper and a broken oath dearer; AI Dwarf rulers pay weregild in their rotation; the books ride save field 19. A Chaos Dwarf court is unchanged in every rule, number, save string and picture.

**Architecture:** The book is `court.grudges[slug] = {{code, turn}, ...}` in the model, written by `IC.grudge_write` (a no-op off the Dwarf race) at each existing site that already charges the wrong's one-off loyalty, and read as terms by `IC.loyalty_terms`, which the drift and the loyalty tooltip already share. The secession countdowns and the Iron Law are `IC.tune` layers (race under government), so no rule is restated. Pay the Weregild is one more `IC.PLOTS` row carrying `race = "dwf"`, `gold = true` and `sure = true`; it rides the existing `plot` MP op. The intrigue grid becomes one grid per race, chosen when the panel opens, so the Chaos Dwarf grid keeps its sixteen cards.

**Tech Stack:** Lua 5.1, Python 3 (py), RPFM MCP

**Spec:** docs/superpowers/specs/2026-10-04-iron-court-dwarfs-design.md (and the CONTRACT file)

## Global Constraints

- Phases 1-3 are done per `docs/superpowers/plans/2026-10-04-iron-court-dwarfs-CONTRACT.md`: `IC.RACES`, `IC.RACE_ORDER`, `IC.race_key`, `IC.R`, `IC._race_cache`, `IC.key`, `IC.office_by_slug(slug, faction_key)`, the Dwarf race table in `zzz_derpy_iron_court_dwarf.lua` (scraped as `DWF.X`), the harness loading that file, and `tools/preview_iron_court.py --race dwf`. Line numbers below are today's (before phases 1-3); find each site by the quoted text.
- Names exactly as the contract: `IC.GRUDGE_CODES`, `IC.grudges`, `IC.grudge_write`, `IC.grudge_settle`, save field 19, TUNE `grudge_loyalty`, `grudge_max`, `kin_loyalty`, `plot_weregild_cost`, `plot_weregild_loyalty`, plot key `weregild`.
- Not a git repo. Every "Checkpoint" runs THE GATES, from the workspace root `G:\Modding for resources` (the mutation runner reports a false "harness not green" from `tools/`):
  ```powershell
  & "C:\Program Files (x86)\Lua\5.1\luac.exe" -p "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court.lua" "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court_dwarf.lua" "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court_parties.lua" "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court_ui.lua" "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court_ui_map.lua"
  $env:IC_TEST_ALL = 1; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_TEST_ALL
  py tools\check_lua_api.py
  py tools\check_lua_literal_left.py
  py tools\check_lua_undeclared.py
  py tools\gen_ic_ui.py --check
  py tools\gen_ic_ui.py --selftest
  py tools\gen_iron_court.py --check
  ```
  Expected: luac silent; the harness prints `iron court harness: ok (N checks)` with no `FAIL` line; every tool exits 0.
- Running only this phase's checks: `$env:IC_ONLY = "grudges:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`. Every check this plan adds is named `grudges: ...` and nothing before it is.
- Every new check is watched failing for its own reason before the code that passes it is written.
- Lua 5.1 with the game's miscompile: no number literal on the LEFT of an arithmetic operator in shipped Lua (`check_lua_literal_left.py`). A model function never calls loc (turn-1 CTD): every model label is plain English, resolved nowhere.
- Every model change the panel makes goes through `ICUI.send` -> `IC.MP_OPS` -> `IC.after_op`. Weregild uses the existing `plot` op; no new op.
- Player text in plain words: no emojis, never "rung", "standing", "cap", "AI" or "HUD" in loc, card or tooltip text. Rule lines terse, no dashes in loc rule lines.
- `zzz_derpy_iron_court_dwarf.lua` keeps column-0 `}` closers on every `DWF.X = {` table (the scrapers read `DWF\.X = \{(.*?)\n\}`).
- The harness block this plan adds is ONE `do ... end` (the main chunk is at 142+ of Lua's 200 locals), inserted immediately above `-- THE PREVIEW'S DEMO (plan 2026-10-02 laws, Task 10)`. Task 1 creates it; later tasks insert their checks directly above its closing line `end -- GRUDGES (plan 2026-10-04 phase 4)`.
- Spec numbers (copied): -1 loyalty per grudge per turn, never fading, 4 per party; Kin of the Karak +1 per party; secession countdown x1.5; weregild loyalty 4 (contract). Chosen here: weregild 1000 gold; the Iron Law's discount `{mul = 0.67}` ("a third less", the Convoy Concern's precedent) and a broken oath -10.

## Rulings against the spec and contract

1. **Pay the Weregild sits in the party column (`cat = "house"`, shown under "Against a Party"), not Bonds.** Measured with `gen_ic_ui.py`: Bonds already holds 4 moves, the grid's depth. A fifth makes the depth 5 and the card 138px tall, where the fourth blurb line ends at y 140 and the price row starts at y 106 - `check_plot_cells` refuses it, for every race, Chaos Dwarf included. The party column holds 2 (Bar Them from the Hall, Recall Governors), and weregild is aimed the same way they are: at the man who speaks for a party. The contract's `category bond` is the one deviation; the preview in Task 7 puts it in front of the author, who may overrule.
2. **The weregild is certain** (`sure = true`, no `plot_chance_weregild`): a blood-price is paid, not attempted, and a missed payment would need a gold-spent failure sentence nothing else has. The harness check "every move has odds" accepts `sure` and nothing else.
3. **A grudge is written exactly where the wrong already takes its one-off loyalty hit, and only when the move lands.** A failed attempt costs `plot_fail_loyalty` as today and writes nothing. A term ending, a quiet replacement, a free release of a governor and anything a rival party does to another (`IC.party_strike`) write nothing: none of them is the ruler's wrong.
4. **The Crown keeps no book** (you cannot wrong your own house); **Kin of the Karak is on every party, the Crown included** ("every party", spec section 5).
5. **A book is kept by party slot and outlives the party.** `IC.remove_house` does not clear it. That is what lets Cast Out the Clan write at all (the grudge is written just before the party is removed), and a returning Clan Warriors remembers.
6. **A broken oath is the Blood-Oath ended by your own Insult** (the provoke branch's `oath_broken` "provoked"). An oath ended by a death breaks nothing: the guide's own rule is "The oath holds while both men live." The Insult then writes two grudges, `insult` and `oath`: two wrongs.
7. **The x1.5 scales exactly two keys: `secede_turns` and `plot_provoke_clock`** (the countdown a party starts, and the countdown an Insult sets). Not scaled: `secede_share`, `secede_loyalty`, `secede_break` (thresholds, not counts), `warn_turns` (the "soon" card, and the Crown's split count), `secede_step` (seconds between a secession's animation steps).
8. **A seat settles one grudge only when the appointment pays `loyalty_appointed`** (a renewal does not) **and the office's affinity is the man's own party.**
9. **New TUNE keys are not MCT settings** (the contract marks none) and are not in `IC.TUNE_ORDER`.
10. **An AI Dwarf ruler pays weregild right after `IC.ai_placate`, every turn its court is due, whatever `parties_act` says**: it is the ruler's act, not a party's. It pays the party with the most grudges, lowest loyalty first, ties in `IC.present_houses` order (the same on every machine).
11. **The Help page gets no grudge topic in this phase.** The loyalty tooltip names each grudge and how to settle it, and the weregild card says what it does; a Help topic per race is phase 6's call.

## Review Focus

1. **A Chaos Dwarf court is untouched**: every writer leaves its books empty, no Kin term, no x1.5, its `chain` government keeps its own rule, its intrigue grid is the sixteen cards it was, and its save string gains only an empty field 19. Pinned in Tasks 1-4 and 6 (every writer check runs both races).
2. **A grudge never fades and a full book stays full**: 50 turns of `IC.turn` with the saves in between leave four grudges, the same four. Pinned in Task 3; mutants in Task 8.
3. **An older save** (18 fields) loads with empty books and every other field intact. Pinned in Task 2.
4. **The weregild is paid in gold, never influence**, refused on a Chaos Dwarf court even when an op names it, and crosses the multiplayer wire like any move. Pinned in Task 4.
5. **The race layer composes with the government layer**: a Dwarf court on the Iron Law gets both the oath discount and the x1.5. Pinned in Task 3.

---

### Task 1: The race layer of `IC.tune` - secession half again as long

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua` - `IC.tune` (today 917-929), `IC.tick_secession` (5024-5036), the provoke branch of `IC.plot` (5873-5889)
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_dwarf.lua` - the Dwarf race table's `tune`
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua` - `ICUI.plot_effect` (5976-5980), `ICUI.act_tip` (4152-4153)
- Test: `tools/_iron_court_harness.lua` (new block above `-- THE PREVIEW'S DEMO (plan 2026-10-02 laws, Task 10)`)

**Interfaces:**
- Consumes: `IC.R`, `IC.RACES`, `IC.gov_row` (phase 1).
- Produces: `IC.tune_layer(base, o) -> value` (new; one layer of `IC.tune`); `IC.tune(faction_key, key)` layered TUNE -> race -> government; `DWF.tune = {secede_turns = {mul = 1.5}, plot_provoke_clock = {mul = 1.5}}`. Harness helpers inside the block: `D`, `court_man`, `grudge_court`, `landing`, `grudge_lines`.

- [ ] **Step 1: Write the harness block and the failing checks.** Insert immediately above the line `-- THE PREVIEW'S DEMO (plan 2026-10-02 laws, Task 10)`:

```lua
do -- GRUDGES INSIDE THE COURT (plan 2026-10-04 phase 4). One block, so its
   -- helpers are not more of the main chunk's 200 locals.
local D = "wh_main_dwf_karak_kadrin"

-- A MAN OF THIS RACE'S PARTY. A Dwarf's trade is a Dwarf background, keyed
-- with the race's infix (contract: IC.key), which make_character cannot stamp.
local function court_man(race_key, cqi, party)
    if race_key == "chd" then return make_character(cqi, ANY_SEAT, party) end
    local c = make_character(cqi, ANY_SEAT, nil)
    c._traits[IC.key("bg", IC.RACES.dwf.BACKGROUNDS[party][1], D)] = true
    return c
end

-- THE CROWN (7001, who acts) AND THE CLAN WARRIORS (7002, who speaks for
-- them, and 7003), on Karak Kadrin or on Uzkulak. An AI court on turn 34 with
-- a full treasury, unless a check says otherwise.
local function grudge_court(race_key)
    IC.state, IC.agenda_state, IC._race_cache = {}, {}, {}
    turn = 34
    cm.get_human_factions = function() return {} end
    local key = race_key == "dwf" and D or F
    local men = {court_man(race_key, 7001, IC.CROWN), court_man(race_key, 7002, "legion"),
                 court_man(race_key, 7003, "legion")}
    local f = make_faction(key, IC.RACES[race_key].subculture, men, {"prov_a"})
    f._gold = 100000
    IC.add_house(key, IC.CROWN)
    IC.add_house(key, "legion")
    for _, cqi in ipairs({7001, 7002, 7003}) do IC.court(key).standing[cqi] = 5000 end
    return key, f
end

-- EVERY ROLL LANDS: 1 beats every chance plot_chance can produce.
local function landing(fn)
    local roll = cm.random_number
    cm.random_number = function() return 1 end
    local ok, err = pcall(fn)
    cm.random_number = roll
    if not ok then error(err, 0) end
end

-- HOW MANY GRUDGE LINES THE BREAKDOWN DRAWS for a party, and what they sum to.
local function grudge_lines(key, slug)
    local n, sum = 0, 0
    for _, t in ipairs(IC.loyalty_terms(key, slug)) do
        if string.find(t.label, "^Grudge: ") then n, sum = n + 1, sum + t.n end
    end
    return n, sum
end

check("grudges: the race layer of IC.tune scales the two secession countdowns for Dwarfs only", function()
    local k = grudge_court("dwf")
    for _, key in ipairs({"secede_turns", "plot_provoke_clock"}) do
        local want = math.floor(IC.TUNE[key] * 1.5 + 0.5)
        assert(IC.tune(k, key) == want, key .. " is " .. tostring(IC.tune(k, key))
            .. " on a Dwarf court, not " .. want)
        assert(IC.tune(F, key) == IC.TUNE[key], key .. " was scaled on a Chaos Dwarf court")
        assert(IC.tune(nil, key) == IC.TUNE[key], key .. " was scaled with no court named")
    end
    for _, key in ipairs({"secede_share", "secede_loyalty", "secede_break", "warn_turns"}) do
        assert(IC.tune(k, key) == IC.TUNE[key], key .. " was scaled; only the countdowns are")
    end
    assert(IC.TUNE.secede_turns == IC.TUNE_DEFAULTS.secede_turns, "the race layer wrote into IC.TUNE")
end)

check("grudges: a Dwarf party's secession countdown runs half again as long, and the Insult says so", function()
    local was = IC.TUNE.secede_turns
    -- THE DEFAULT AND GENTLE'S 7: a scale, not a fixed number.
    for _, base in ipairs({was, 7}) do
        IC.TUNE.secede_turns = base
        for _, rk in ipairs({"dwf", "chd"}) do
            local k = grudge_court(rk)
            IC.court(k).houses.legion.loyalty = 10
            IC.tick_secession(k)
            local want = rk == "dwf" and math.floor(base * 1.5 + 0.5) or base
            local got = IC.court(k).houses.legion.clock
            IC.TUNE.secede_turns = was
            assert(got == want, rk .. " counted " .. tostring(got) .. " from " .. base .. ", not " .. want)
            IC.TUNE.secede_turns = base
        end
    end
    IC.TUNE.secede_turns = was
    for _, rk in ipairs({"dwf", "chd"}) do
        local k = grudge_court(rk)
        landing(function() assert(IC.plot(k, "provoke", 7001, "7002")) end)
        local want = rk == "dwf" and math.floor(IC.TUNE.plot_provoke_clock * 1.5 + 0.5)
                     or IC.TUNE.plot_provoke_clock
        assert(IC.court(k).houses.legion.clock == want, rk .. "'s Insult set "
            .. tostring(IC.court(k).houses.legion.clock) .. ", not " .. want)
    end
    local text = ICUI.plot_effect(IC.plot_by_key("provoke"), D)
    assert(string.find(text, "to " .. math.floor(IC.TUNE.plot_provoke_clock * 1.5 + 0.5) .. " turns", 1, true),
        "a Dwarf court's Insult promises: " .. text)
    text = ICUI.plot_effect(IC.plot_by_key("provoke"), F)
    assert(string.find(text, "to " .. IC.TUNE.plot_provoke_clock .. " turns", 1, true),
        "a Chaos Dwarf court's Provoke promises: " .. text)
end)

check("grudges: no secession countdown is read straight off IC.TUNE", function()
    -- THE ONE WAY THE RACE LAYER SILENTLY DOES NOTHING: a read left on IC.TUNE.
    -- IC.PLOTS' effect lines are built once at load from the base number and
    -- ICUI.plot_effect rewords them per court, so that block is cut out first.
    local dir = "Modding Files/pack/script/campaign/mod/"
    for _, file in ipairs({"zzz_derpy_iron_court.lua", "zzz_derpy_iron_court_dwarf.lua",
                           "zzz_derpy_iron_court_parties.lua", "zzz_derpy_iron_court_ui.lua",
                           "zzz_derpy_iron_court_ui_map.lua"}) do
        local fh = assert(io.open(dir .. file, "r"))
        local text = fh:read("*a")
        fh:close()
        local a = string.find(text, "\nIC.PLOTS = {", 1, true)
        if a then
            local b = string.find(text, "\n}", a + 1, true)
            text = string.sub(text, 1, a) .. string.sub(text, b)
        end
        for key in pairs(IC.RACES.dwf.tune) do
            assert(not string.find(text, "IC%.TUNE%." .. key .. "[^%w_]"),
                file .. " reads IC.TUNE." .. key .. ", which the race layer never reaches")
        end
    end
end)

end -- GRUDGES (plan 2026-10-04 phase 4)
```

- [ ] **Step 2: Run to verify they fail**

Run: `$env:IC_ONLY = "grudges:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: `FAIL grudges: the race layer of IC.tune scales the two secession countdowns for Dwarfs only: ... secede_turns is 5 on a Dwarf court, not 8` (or, if phase 1 left `IC.RACES.dwf.tune` nil, `attempt to index field 'tune'` from the third check), exit 1.

- [ ] **Step 3: Implement the layer.** Replace `IC.tune` (whatever phase 1 left; today 917-929) with the two functions below. Keep the three lines starting `        local out = {}` byte-identical: the mutant "a table knob scaled into IC.TUNE itself" is anchored on them.

```lua
-- ONE LAYER OF IC.tune: a number replaces, {mul = x} scales - a table knob
-- entry by entry - rounded.
function IC.tune_layer(base, o)
    if o == nil then return base end
    if type(o) == "number" then return o end
    if type(base) == "table" then
        local out = {}
        for k, v in pairs(base) do out[k] = math.floor(v * o.mul + 0.5) end
        return out
    end
    return math.floor(base * o.mul + 0.5)
end

-- IC.TUNE, THEN THE COURT'S RACE, THEN ITS GOVERNMENT (spec 2026-10-04 section
-- 9.2). The race layer is under every government: a Dwarf party's secession
-- counts run half again as long whoever rules.
function IC.tune(faction_key, key)
    local race = faction_key and IC.R(faction_key)
    local base = IC.tune_layer(IC.TUNE[key], race and race.tune and race.tune[key])
    local row = IC.gov_row(faction_key)
    return IC.tune_layer(base, row and row.over[key])
end
```

In `zzz_derpy_iron_court_dwarf.lua`, find the Dwarf race's tune (`grep -n "tune" "Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_dwarf.lua"`) and set it to:

```lua
-- KINSHIP (spec 2026-10-04 section 5): a Dwarf party is slow to leave its
-- karak. Exactly the two countdowns; plan 2026-10-04 phase 4 ruling 7 names
-- what is not scaled and why.
DWF.tune = {
    secede_turns       = {mul = 1.5},
    plot_provoke_clock = {mul = 1.5},
}
```

(If phase 2 wrote `tune = {}` inside the race table's constructor instead of a `DWF.tune = {` line, put the two entries there; the column-0 `}` rule applies either way.)

- [ ] **Step 4: Implement the read sites.** In `IC.tick_secession`, replace

```lua
                house.clock = IC.TUNE.secede_turns
```

with

```lua
                house.clock = IC.tune(faction_key, "secede_turns")
```

and

```lua
                elseif house.clock == math.min(IC.TUNE.warn_turns,
                                               IC.TUNE.secede_turns - 1) then
```

with

```lua
                elseif house.clock == math.min(IC.TUNE.warn_turns,
                                               IC.tune(faction_key, "secede_turns") - 1) then
```

In `IC.plot`'s provoke branch, replace

```lua
            if IC.TUNE.secession ~= false
               and (now <= 0 or now > IC.TUNE.plot_provoke_clock) then
                house.clock = IC.TUNE.plot_provoke_clock
```

with

```lua
            -- THE RACE'S COUNT (plan 2026-10-04 phase 4): a Dwarf party
            -- insulted counts half again as long.
            local count = IC.tune(faction_key, "plot_provoke_clock")
            if IC.TUNE.secession ~= false
               and (now <= 0 or now > count) then
                house.clock = count
```

In `zzz_derpy_iron_court_ui.lua`, replace `ICUI.plot_effect`'s first line

```lua
    if plot.key ~= "embezzle" then return plot.effect end
```

with

```lua
    -- THE INSULT'S COUNT IS THE COURT'S RACE'S (plan 2026-10-04 phase 4).
    if plot.key == "provoke" then
        return (string.gsub(plot.effect, "to %d+ turns",
            "to " .. IC.tune(faction, "plot_provoke_clock") .. " turns", 1))
    end
    if plot.key ~= "embezzle" then return plot.effect end
```

and in `ICUI.act_tip` replace

```lua
        lines[2] = IC.TUNE.secession == false and plot.effect_no_secession
                   or plot.effect
```

with

```lua
        lines[2] = IC.TUNE.secession == false and plot.effect_no_secession
                   or ICUI.plot_effect(plot, faction)
```

- [ ] **Step 5: Run to verify they pass**

Run: `$env:IC_ONLY = "grudges:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: `iron court harness: ok (3 checks)`.

- [ ] **Step 6: Checkpoint.** Run THE GATES. Expected: all green; the full harness count is phase 3's plus 3.

### Task 2: The book - codes, terms, kinship, the Record, save field 19

**Files:**
- Modify: `zzz_derpy_iron_court.lua` - `IC.TUNE` (after `party_intrigue_line = 55,`, today 614), `new_court` (1140-1173), `IC.LOG_KINDS` (1179-1212), new functions after `IC.log` (after 1244), `IC.loyalty_terms` (after the Blood-Oath term, 4194-4199), `IC.pack` (1557-1679), `IC.unpack` (after field 18, 1861-1885)
- Modify: `zzz_derpy_iron_court_ui.lua` - `ICUI.intrigue_text` (after the `pledge` branch, today 5855-5857)
- Test: harness block

**Interfaces:**
- Consumes: `IC.race_key` (phase 1).
- Produces: `IC.GRUDGE_CODES` (contract), `IC.GRUDGE_WORDS[code] -> plain words` (new), `IC.grudges(faction_key, slug) -> {{code, turn}, ...}` oldest first, `IC.grudge_write(faction_key, slug, code) -> bool`, `IC.grudge_settle(faction_key, slug, how) -> {code, turn} | nil`, court field `grudges`, log kinds `grudge` (key = code) and `grudge_settled` (key = code, n = 1 for a seat, 0 for weregild), TUNE `grudge_loyalty`, `grudge_max`, `kin_loyalty`. Phase 5 consumes `IC.grudge_write(fk, slug, "peace")`.

- [ ] **Step 1: Write the failing checks** (above `end -- GRUDGES (plan 2026-10-04 phase 4)`):

```lua
check("grudges: a book holds four, each its own loyalty line, and the Crown keeps none", function()
    local k = grudge_court("dwf")
    for i = 1, IC.TUNE.grudge_max + 2 do
        turn = 30 + i
        IC.grudge_write(k, "legion", IC.GRUDGE_CODES[i])
    end
    local book = IC.grudges(k, "legion")
    assert(#book == IC.TUNE.grudge_max, "the book holds " .. #book)
    assert(book[1].code == IC.GRUDGE_CODES[1] and book[1].turn == 31
           and book[#book].code == IC.GRUDGE_CODES[IC.TUNE.grudge_max],
        "a full book took a new grudge over an old one")
    local n, sum = grudge_lines(k, "legion")
    assert(n == IC.TUNE.grudge_max and sum == IC.TUNE.grudge_max * IC.TUNE.grudge_loyalty,
        n .. " grudge lines summing to " .. sum)
    local first
    for _, t in ipairs(IC.loyalty_terms(k, "legion")) do
        if string.find(t.label, "^Grudge: ") then first = first or t end
    end
    assert(first.label == "Grudge: " .. IC.GRUDGE_WORDS[IC.GRUDGE_CODES[1]] .. ", turn 31",
        "the line reads " .. first.label)
    assert(first.note and first.note ~= "", "the first grudge does not say how to settle it")
    assert(not IC.grudge_write(k, IC.CROWN, "dismiss") and #IC.grudges(k, IC.CROWN) == 0,
        "the Crown keeps a book against its own ruler")
    assert(not IC.grudge_write(k, "forge", "dismiss"), "a party not in the court was written")
    assert(not IC.grudge_write(k, "legion", "no_such_wrong"), "an unknown wrong was written")
    local c = grudge_court("chd")
    assert(not IC.grudge_write(c, "legion", "dismiss") and #IC.grudges(c, "legion") == 0,
        "a Chaos Dwarf court keeps a book")
end)

check("grudges: Kin of the Karak is +1 for every party of a Dwarf court and nobody else's", function()
    for _, rk in ipairs({"dwf", "chd"}) do
        local k = grudge_court(rk)
        for _, slug in ipairs({IC.CROWN, "legion"}) do
            local kin
            for _, t in ipairs(IC.loyalty_terms(k, slug)) do
                if t.label == "Kin of the Karak" then kin = t end
            end
            if rk == "dwf" then
                assert(kin and kin.n == IC.TUNE.kin_loyalty, slug .. " has no kinship on a Dwarf court")
            else
                assert(not kin, slug .. " is Kin of the Karak on a Chaos Dwarf court")
            end
        end
    end
end)

check("grudges: the books survive a save, and an 18-field save reads none", function()
    local k = grudge_court("dwf")
    IC.add_house(k, "forge")
    turn = 12; IC.grudge_write(k, "legion", "castout")
    turn = 19; IC.grudge_write(k, "legion", "demand")
    turn = 21; IC.grudge_write(k, "forge", "slayer")
    IC.save(k)
    IC.state = {}
    IC.load(k)
    local l, f2 = IC.grudges(k, "legion"), IC.grudges(k, "forge")
    assert(#l == 2 and l[1].code == "castout" and l[1].turn == 12
           and l[2].code == "demand" and l[2].turn == 19, "the Clan Warriors' book came back wrong")
    assert(#f2 == 1 and f2[1].code == "slayer" and f2[1].turn == 21, "the Forgewrights' book came back wrong")
    local fields = {}
    for field in string.gmatch(saved["derpy_ic_" .. k] .. "|", "([^|]*)|") do
        fields[#fields + 1] = field
    end
    assert(#fields >= 19 and string.find(fields[19], "legion:castout.12;demand.19", 1, true),
        "field 19 reads " .. tostring(fields[19]))
    IC.unpack(k, table.concat(fields, "|", 1, 18))
    assert(#IC.grudges(k, "legion") == 0 and #IC.grudges(k, "forge") == 0,
        "an 18-field save read a grudge out of nothing")
    assert(IC.court(k).houses.legion and IC.court(k).houses.forge, "an 18-field save lost its parties")
end)

check("grudges: a written and a settled grudge each have a line in the Record", function()
    local k = grudge_court("dwf")
    local w = ICUI.intrigue_text({turn = 3, kind = "grudge", slug = "legion", key = "castout", n = 0})
    assert(w and string.find(w, IC.GRUDGE_WORDS.castout, 1, true), "the written line reads " .. tostring(w))
    local p = ICUI.intrigue_text({turn = 3, kind = "grudge_settled", slug = "legion", key = "recall", n = 0})
    local s = ICUI.intrigue_text({turn = 3, kind = "grudge_settled", slug = "legion", key = "recall", n = 1})
    assert(p and s and p ~= s and string.find(p, "weregild", 1, true) and string.find(s, "seat", 1, true),
        "the settled lines read " .. tostring(p) .. " / " .. tostring(s))
    IC.grudge_write(k, "legion", "insult")
    local last = IC.court(k).log[#IC.court(k).log]
    assert(last.kind == "grudge" and last.slug == "legion" and last.key == "insult",
        "writing a grudge left no line in the Record")
    IC.grudge_settle(k, "legion", "seat")
    last = IC.court(k).log[#IC.court(k).log]
    assert(last.kind == "grudge_settled" and last.key == "insult" and last.n == 1,
        "settling a grudge left no line in the Record")
end)
```

- [ ] **Step 2: Run to verify they fail**

Run: `$env:IC_ONLY = "grudges:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: `FAIL grudges: a book holds four, ...: ... attempt to compare nil with number` (no `IC.TUNE.grudge_max`), exit 1.

- [ ] **Step 3: Implement the model.** In `IC.TUNE`, directly after `party_intrigue_line = 55,`:

```lua

    -- GRUDGES (spec 2026-10-04 Dwarfs section 5), Dwarf courts only. Not on
    -- the MCT page. A grudge is a loyalty line that never fades; a party's
    -- book holds grudge_max. Kinship is every Dwarf party's term.
    grudge_loyalty      = -1,
    grudge_max          = 4,
    kin_loyalty         = 1,
```

In `new_court`, after `votes = {},`:

```lua
        -- GRUDGES (spec 2026-10-04 section 5): [party] = {{code, turn}, ...},
        -- oldest first. Kept by party slot: a party that leaves keeps its book.
        grudges = {},
```

In `IC.LOG_KINDS`, after the line `died = true, stall_end = true,`:

```lua
    -- GRUDGES (spec 2026-10-04 section 5): key is the grudge's code; a settled
    -- one's n is 1 for a seat, 0 for the weregild.
    grudge = true, grudge_settled = true,
```

After `IC.log` (after its closing `end`, today 1244):

```lua
-- GRUDGES INSIDE THE COURT (spec 2026-10-04 Dwarfs section 5). A wrong the
-- ruler does a party, written where the wrong already takes its one-off
-- loyalty. Contract order; "peace" is phase 5's (a pact with a faction the
-- Book of Grudges names).
IC.GRUDGE_CODES = {"slayer", "castout", "insult", "bar", "recall", "dismiss", "oath", "demand", "peace"}

-- WHAT EACH LINE OF THE BREAKDOWN CALLS IT. Plain English and no loc: the
-- terms are built inside the turn (ICUI.loyalty_tip resolves nothing either).
IC.GRUDGE_WORDS = {
    slayer  = "Driven to the Slayer Oath",
    castout = "Cast Out",
    insult  = "An Insult to the Clan",
    bar     = "Barred from the Hall",
    recall  = "Governors recalled",
    dismiss = "Dismissed before his term",
    oath    = "An oath broken",
    demand  = "A demand refused",
    peace   = "A pact with a named foe",
}

-- IC.state, not IC.court: asking must never create a court.
function IC.grudges(faction_key, slug)
    local court = faction_key and IC.state[faction_key]
    return court and court.grudges and court.grudges[slug or ""] or {}
end

-- A DWARF COURT'S, A RIVAL PARTY'S, A WRONG WE KNOW, AND ROOM IN THE BOOK.
-- A full book takes nothing more; the wrong still costs its one-off loyalty.
function IC.grudge_write(faction_key, slug, code)
    if IC.race_key(faction_key) ~= "dwf" or not IC.GRUDGE_WORDS[code or ""] then return false end
    if not slug or slug == IC.CROWN then return false end
    local court = IC.court(faction_key)
    if not court.houses[slug] then return false end
    court.grudges = court.grudges or {}
    local book = court.grudges[slug] or {}
    if #book >= IC.TUNE.grudge_max then return false end
    book[#book + 1] = {code = code, turn = cm:model():turn_number()}
    court.grudges[slug] = book
    IC.log(faction_key, "grudge", slug, code, 0)
    return true
end

-- THE OLDEST GOES FIRST. `how` is "weregild" or "seat", for the Record.
function IC.grudge_settle(faction_key, slug, how)
    local book = IC.grudges(faction_key, slug)
    if #book == 0 then return nil end
    local g = table.remove(book, 1)
    IC.log(faction_key, "grudge_settled", slug, g.code, how == "seat" and 1 or 0)
    return g
end
```

In `IC.loyalty_terms`, directly after the Blood-Oath block (the `end` closing `if house.oath_mine and house.oath_theirs then`) and before `local lead = IC.leader_trait(faction_key, slug)`:

```lua

    -- GRUDGES AND KINSHIP (spec 2026-10-04 Dwarfs section 5): a line per
    -- grudge in the party's book, and the kinship every party of a Dwarf
    -- court shares. The first grudge carries the way out as its note.
    local dwarf = IC.race_key(faction_key) == "dwf"
    if dwarf then
        for i, g in ipairs(IC.grudges(faction_key, slug)) do
            terms[#terms + 1] = {
                label = string.format("Grudge: %s, turn %d",
                                      IC.GRUDGE_WORDS[g.code] or g.code, g.turn),
                note = i == 1 and "A grudge never fades. Pay the Weregild, or seat "
                    .. "their man in an office they claim." or nil,
                n = IC.TUNE.grudge_loyalty}
        end
        terms[#terms + 1] = {label = "Kin of the Karak", n = IC.TUNE.kin_loyalty}
    end
```

In `IC.pack`, directly after `table.sort(votes)`:

```lua
    -- GRUDGES (spec 2026-10-04 section 5): field 19 is "slug:code.turn;code.turn"
    -- per party, "/" between parties, oldest first. Empty on every Chaos Dwarf court.
    local grudges = {}
    for slug, book in pairs(court.grudges or {}) do
        local g = {}
        for i = 1, #book do g[i] = book[i].code .. "." .. tostring(book[i].turn) end
        if #g > 0 then grudges[#grudges + 1] = slug .. ":" .. table.concat(g, ";") end
    end
    table.sort(grudges)
```

and in its return list replace `join(laws, ";"), join(votes, ";")}, "|")` with `join(laws, ";"), join(votes, ";"), join(grudges, "/")}, "|")`.

In `IC.unpack`, directly after the field-18 loop (the `end` after `court.votes[b[1]] = v`) and before `IC.state[faction_key] = court`:

```lua
    -- Field 19 is optional: a save from before grudges has none (spec
    -- 2026-10-04 section 5). A wrong this build does not know is dropped.
    for _, entry in ipairs(split(fields[19] or "", "/")) do
        local slug, list = string.match(entry, "^([%w_]+):(.+)$")
        if slug then
            local book = {}
            for _, g in ipairs(split(list, ";")) do
                local code, t = string.match(g, "^([%w_]+)%.(%d+)$")
                if code and IC.GRUDGE_WORDS[code] then
                    book[#book + 1] = {code = code, turn = tonumber(t)}
                end
            end
            if #book > 0 then court.grudges[slug] = book end
        end
    end
```

- [ ] **Step 4: Implement the Record lines.** In `ICUI.intrigue_text`, directly after the `pledge` branch's `return` statement (before `elseif e.kind == "audience" then`):

```lua
    -- GRUDGES (plan 2026-10-04 phase 4). e.key is the grudge's code.
    elseif e.kind == "grudge" then
        return string.format("%s writes a grudge in its book: %s.", house,
                             IC.GRUDGE_WORDS[e.key or ""] or tostring(e.key))
    elseif e.kind == "grudge_settled" then
        return string.format("%s strikes a grudge from its book: %s, %s.", house,
                             IC.GRUDGE_WORDS[e.key or ""] or tostring(e.key),
                             e.n == 1 and "for a seat it claims" or "for the weregild")
```

- [ ] **Step 5: Run to verify they pass**

Run: `$env:IC_ONLY = "grudges:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: `iron court harness: ok (7 checks)`.

- [ ] **Step 6: Checkpoint.** Run THE GATES. Expected: all green, including the existing "every kind the model writes, the panel can describe" and the record-branch pairing check (both walk `IC.LOG_KINDS`).

### Task 3: The writers, and the Iron Law

**Files:**
- Modify: `zzz_derpy_iron_court.lua` - `IC.TUNE` (after the Task 2 block), `IC.plot` branches murder (5968-5973), provoke (5873-5894), purge (5895-5902), unseat (5915-5919), recall (5920-5925); `IC.dismiss` (5552-5558); `IC.gov_row` (910-915) only if it still indexes `IC.GOVS` directly
- Modify: `zzz_derpy_iron_court_parties.lua` - `IC.settle_demand` refused branch (849-853)
- Modify: `zzz_derpy_iron_court_dwarf.lua` - `DWF.GOVS.chain.over`
- Modify: `tools/gen_iron_court.py` - the Dwarf race's Iron Law row (rule text)
- Modify: `tools/mutate_iron_court.py` - the existing mutant "an override answering for every court", only if `IC.gov_row` changes
- Test: harness block

**Interfaces:**
- Consumes: Task 2's `IC.grudge_write`; phase 2's `DWF.GOVS`, `RACES["dwf"]` GOVERNMENTS in `gen_iron_court.py`.
- Produces: TUNE `oath_broken_loyalty` (new, 0); the Iron Law override `{plot_oath_cost = {mul = 0.67}, plot_patron_cost = {mul = 0.67}, plot_pledge_cost = {mul = 0.67}, oath_broken_loyalty = -10}`; `IC.gov_row(faction_key)` reading the court's race's `GOVS`.

- [ ] **Step 1: Write the failing checks:**

```lua
-- EVERY WRONG THE SPEC NAMES, as the act that does it. The middle number is
-- how many grudges the one act writes: an Insult that breaks an oath is two.
local function seat_legion(k)
    local office = IC.R(k).OFFICES[1].slug
    IC.court(k).offices[office] = 7002
    return office
end
local WRITERS = {
    {"slayer",  1, function(k) assert(IC.plot(k, "murder", 7001, "7002")) end},
    {"castout", 1, function(k) assert(IC.plot(k, "purge", 7001, "7002")) end},
    {"insult",  1, function(k) assert(IC.plot(k, "provoke", 7001, "7002")) end},
    {"bar",     1, function(k) seat_legion(k); assert(IC.plot(k, "unseat", 7001, "7002")) end},
    {"recall",  1, function(k)
        IC.court(k).govs.prov_a = 7002
        assert(IC.plot(k, "recall", 7001, "7002"))
    end},
    {"dismiss", 1, function(k) assert(IC.dismiss(k, seat_legion(k))) end},
    {"oath",    2, function(k)
        local house = IC.court(k).houses.legion
        house.oath_mine, house.oath_theirs = 7001, 7002
        assert(IC.plot(k, "provoke", 7001, "7002"))
    end},
    {"demand",  1, function(k)
        IC.agenda(k).demand = {slug = "legion", kind = "office", cqi = 7002,
                               key = IC.R(k).OFFICES[1].slug, was = 0, ends = turn + 5}
        assert(IC.refuse_demand(k))
    end},
    {"peace",   1, function(k) IC.grudge_write(k, "legion", "peace") end},
}
for _, w in ipairs(WRITERS) do
    check("grudges: " .. w[1] .. " writes its grudge on a Dwarf court and none on a Chaos Dwarf court", function()
        for _, rk in ipairs({"dwf", "chd"}) do
            local k = grudge_court(rk)
            landing(function() w[3](k) end)
            local book, mine = IC.grudges(k, "legion"), 0
            for _, g in ipairs(book) do
                if g.code == w[1] then
                    mine = mine + 1
                    assert(g.turn == 34, w[1] .. " was dated turn " .. tostring(g.turn))
                end
            end
            if rk == "dwf" then
                assert(mine == 1 and #book == w[2], w[1] .. " left " .. mine .. " of its own and "
                    .. #book .. " in all on a Dwarf court")
            else
                assert(#book == 0, w[1] .. " wrote " .. #book .. " on a Chaos Dwarf court")
            end
        end
    end)
end

check("grudges: the Iron Law makes oath moves a third cheaper and a broken oath dearer", function()
    IC_GOVS_ON = true
    local ok, err = pcall(function()
        local k = grudge_court("dwf")
        IC.court(k).gov = "chain"
        for _, key in ipairs({"oath", "patron", "pledge"}) do
            local base = IC.TUNE["plot_" .. key .. "_cost"]
            assert(IC.plot_cost(key, k) == math.floor(base * 0.67 + 0.5),
                key .. " costs " .. IC.plot_cost(key, k) .. " under the Iron Law")
        end
        assert(IC.plot_cost("murder", k) == IC.TUNE.plot_murder_cost,
            "the Iron Law kept the Slave-Lords' murder discount")
        assert(IC.tune(k, "secede_turns") == math.floor(IC.TUNE.secede_turns * 1.5 + 0.5),
            "the government layer hid the race layer")
        local extra = IC.tune(k, "oath_broken_loyalty")
        assert(extra < 0, "a broken oath costs nothing extra under the Iron Law")
        local house = IC.court(k).houses.legion
        house.oath_mine, house.oath_theirs, house.loyalty = 7001, 7002, 80
        landing(function() assert(IC.plot(k, "provoke", 7001, "7002")) end)
        assert(house.loyalty == 80 - IC.TUNE.plot_provoke_loyalty + extra,
            "the broken oath left them at " .. house.loyalty)
        local c = grudge_court("chd")
        IC.court(c).gov = "chain"
        assert(IC.plot_cost("oath", c) == IC.TUNE.plot_oath_cost,
            "a Chaos Dwarf chain government discounted the oath")
        assert(IC.tune(c, "oath_broken_loyalty") == 0, "a Chaos Dwarf broken oath costs extra")
    end)
    IC_GOVS_ON = nil
    if not ok then error(err, 0) end
end)

check("grudges: a grudge never fades, fifty turns on", function()
    local k = grudge_court("dwf")
    cm.get_human_factions = function() return {k} end
    local keep_s, keep_a = IC.TUNE.secession, IC.TUNE.parties_act
    IC.TUNE.secession, IC.TUNE.parties_act = false, false
    for _, code in ipairs({"castout", "recall", "demand", "bar"}) do IC.grudge_write(k, "legion", code) end
    IC.save(k)
    local ok, err = pcall(function()
        for _ = 1, 50 do
            turn = turn + 1
            IC.turn(k)
        end
    end)
    IC.TUNE.secession, IC.TUNE.parties_act = keep_s, keep_a
    cm.get_human_factions = function() return {} end
    if not ok then error(err, 0) end
    local book = IC.grudges(k, "legion")
    assert(#book == 4, #book .. " grudges are left after fifty turns")
    for i, code in ipairs({"castout", "recall", "demand", "bar"}) do
        assert(book[i].code == code and book[i].turn == 34, "grudge " .. i .. " changed")
    end
    local n, sum = grudge_lines(k, "legion")
    assert(n == 4 and sum == 4 * IC.TUNE.grudge_loyalty, "fifty turns on, the breakdown draws " .. n)
end)
```

- [ ] **Step 2: Run to verify they fail**

Run: `$env:IC_ONLY = "grudges:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: `FAIL grudges: slayer writes its grudge on a Dwarf court and none on a Chaos Dwarf court: ... slayer left 0 of its own and 0 in all on a Dwarf court`, exit 1.

- [ ] **Step 3: Implement the writers.** In `IC.TUNE`, after the Task 2 block:

```lua
    -- WHAT A BROKEN OATH COSTS ON TOP OF THE INSULT THAT BROKE IT. Nothing,
    -- except under the Dwarfs' Iron Law (DWF.GOVS.chain). Read through IC.tune.
    oath_broken_loyalty = 0,
```

In `IC.plot`, murder branch, after `IC.move_loyalty(faction_key, against, -IC.TUNE.plot_murder_loyalty)`:

```lua
        IC.grudge_write(faction_key, against, "slayer")
```

Provoke branch, after `IC.move_loyalty(faction_key, against, -IC.TUNE.plot_provoke_loyalty)`:

```lua
        IC.grudge_write(faction_key, against, "insult")
```

and replace

```lua
            if house.oath_mine then
                house.oath_mine, house.oath_theirs = nil, nil
                IC.log(faction_key, "oath_broken", against or "", "provoked", 0)
            end
```

with

```lua
            if house.oath_mine then
                house.oath_mine, house.oath_theirs = nil, nil
                IC.log(faction_key, "oath_broken", against or "", "provoked", 0)
                -- A SECOND WRONG, and under the Iron Law a dearer one (spec
                -- 2026-10-04 sections 2.3 and 5).
                IC.grudge_write(faction_key, against, "oath")
                IC.move_loyalty(faction_key, against, IC.tune(faction_key, "oath_broken_loyalty"))
            end
```

Purge branch, replace `        IC.remove_house(faction_key, against)` (the first line of `elseif plot_key == "purge" then`) with

```lua
        -- BEFORE THE PARTY GOES: its book outlives it (plan ruling 5).
        IC.grudge_write(faction_key, against, "castout")
        IC.remove_house(faction_key, against)
```

Unseat branch, after `IC.move_loyalty(faction_key, against, -IC.TUNE.plot_unseat_loyalty)`: `        IC.grudge_write(faction_key, against, "bar")`. Recall branch, after `IC.move_loyalty(faction_key, against, -IC.TUNE.plot_recall_loyalty)`: `        IC.grudge_write(faction_key, against, "recall")`.

In `IC.dismiss`, replace

```lua
    if not quiet then
        IC.move_loyalty(faction_key, slug, IC.TUNE.loyalty_dismissed)
```

with

```lua
    if not quiet then
        IC.move_loyalty(faction_key, slug, IC.TUNE.loyalty_dismissed)
        IC.grudge_write(faction_key, slug, "dismiss")
```

In `zzz_derpy_iron_court_parties.lua`, `IC.settle_demand`, after `IC.move_loyalty(faction_key, d.slug, -T.party_demand_refused)`:

```lua
        IC.grudge_write(faction_key, d.slug, "demand")
```

- [ ] **Step 4: Implement the Iron Law.** In `zzz_derpy_iron_court_dwarf.lua`, in `DWF.GOVS`, replace the `chain` row's `over = {...}` (phase 2's) with:

```lua
                over = {plot_oath_cost = {mul = 0.67}, plot_patron_cost = {mul = 0.67},
                        plot_pledge_cost = {mul = 0.67}, oath_broken_loyalty = -10}},
```

(Swear on the Ancestors is `oath`, Stand His Patron `patron`, Oath on the Anvil `pledge`: spec 2.4 lists the moves in `IC.PLOTS` order.) If phase 2 gave the Dwarf race a `DWF.START_GOV`, leave it.

Read `IC.gov_row`: `grep -n "^function IC.gov_row" -A6 "Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua"`. If its body still reads `IC.GOVS[court.gov or ""]`, replace

```lua
    local court = faction_key and IC.state[faction_key]
    return court and IC.GOVS[court.gov or ""] or nil
```

with

```lua
    local court = faction_key and IC.state[faction_key]
    return court and (IC.R(faction_key).GOVS or IC.GOVS)[court.gov or ""] or nil
```

and in `tools/mutate_iron_court.py` set the old string of the mutant `"an override answering for every court"` to those two new lines (its new string is unchanged). If phase 1 already reads the race's `GOVS`, change neither.

In `tools/gen_iron_court.py`, find the Iron Law row (`grep -n '"The Iron Law"' tools/gen_iron_court.py`) and set its rule string (the element after the name) to:

```python
     "Swear on the Ancestors, Oath on the Anvil and Stand His Patron cost a third "
     "less. A broken oath costs 10 more loyalty.",
```

- [ ] **Step 5: Run to verify they pass**

Run: `$env:IC_ONLY = "grudges:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: `iron court harness: ok (18 checks)`.

- [ ] **Step 6: Checkpoint.** Run THE GATES. Expected: all green; `gen_iron_court.py --check` passes with the new rule line (its `check_governments()` holds the order, not the text).

### Task 4: Settlement - Pay the Weregild, and a seat they claim

**Files:**
- Modify: `zzz_derpy_iron_court.lua` - `IC.TUNE` (after Task 3's key), `IC.LOG_KINDS`, `IC.plots_in` (5218-5224), `IC.PLOTS` (after the `recall` row, 5298-5305), `IC.may_target` (5650-5722), `IC.can_plot` (5729-5757), `IC.plot_chance` (5798-5803), `IC.plot` (5821-5830 and the branches), `IC.plot_costs_seat` (5987-5996), `IC.appoint` (5525-5527)
- Modify: `zzz_derpy_iron_court_dwarf.lua` - `DWF.PLOT_KEYS` only if phase 2 made it a list
- Modify: `zzz_derpy_iron_court_ui.lua` - `ICUI.intrigue_text` (the weregild line)
- Modify: `tools/gen_ic_ui.py` - `plot_counts` (1156-1167)
- Modify: `tools/_iron_court_harness.lua` - `grid_plots` (1252-1259), the check "every move has odds, a picture and a sentence" (~17958-17985), the check "every move has one place to be clicked, and no column is empty" (~17947)
- Test: harness block

**Interfaces:**
- Consumes: Tasks 2-3.
- Produces: TUNE `plot_weregild_cost = 1000`, `plot_weregild_loyalty = 4`; `IC.PLOTS` row `weregild` (`race = "dwf"`, `gold = true`, `sure = true`, `cat = "house"`); `IC.plot_for_race(plot, race_key) -> bool` (new); `IC.plots_in(cat, race_key)` (race_key optional, defaults to `"chd"`); refusal codes `"no grudge"` and (on a gold move) `"gold", short`; log kind `weregild`; `gen_ic_ui.plot_counts(race="chd")`; harness `grid_plots(race)`. Task 6 consumes `plot.gold`, `IC.plot_for_race`, `IC.plots_in(cat, "dwf")`, `plot_counts("dwf")`.

- [ ] **Step 1: Write the failing checks:**

```lua
check("grudges: Pay the Weregild settles the oldest grudge, in gold, and only on a Dwarf court", function()
    local k, f = grudge_court("dwf")
    for i, code in ipairs({"castout", "recall", "demand"}) do
        turn = 10 * i
        IC.grudge_write(k, "legion", code)
    end
    turn = 40
    local was = IC.court(k).houses.legion.loyalty
    local standing = IC.standing(k, 7001)
    treasury_calls = {}
    assert(IC.plot(k, "weregild", 7001, "7002"), "the weregild was refused")
    local book = IC.grudges(k, "legion")
    assert(#book == 2 and book[1].code == "recall" and book[2].code == "demand",
        "the weregild did not settle the oldest grudge")
    assert(#treasury_calls == 1 and treasury_calls[1].amount == -IC.TUNE.plot_weregild_cost,
        "the treasury moved by " .. tostring(treasury_calls[1] and treasury_calls[1].amount))
    assert(IC.standing(k, 7001) == standing, "the weregild was paid out of his influence")
    assert(IC.court(k).houses.legion.loyalty == was + IC.TUNE.plot_weregild_loyalty,
        "the Clan Warriors sit at " .. IC.court(k).houses.legion.loyalty)
    assert(IC.plot_chance(k, "weregild", 7001, "7002") == nil, "the weregild rolls")
    f._gold = IC.TUNE.plot_weregild_cost - 1
    local ok, why, short = IC.plot(k, "weregild", 7001, "7002")
    assert(not ok and why == "gold" and short == 1, "a poor court was answered " .. tostring(why))
    f._gold = 100000
    IC.court(k).grudges.legion = nil
    ok, why = IC.plot(k, "weregild", 7001, "7002")
    assert(not ok and why == "no grudge", "a party with no grudge was paid: " .. tostring(why))
    local c = grudge_court("chd")
    ok, why = IC.plot(c, "weregild", 7001, "7002")
    assert(not ok and why == "no such plot", "a Chaos Dwarf court paid a weregild: " .. tostring(why))
    assert(IC.plot_costs_seat(k, "weregild", 7001) == nil, "a gold move costs a man his seat")
end)

check("grudges: seating their man in an office they claim settles one grudge", function()
    local k = grudge_court("dwf")
    turn = 10; IC.grudge_write(k, "legion", "castout")
    turn = 20; IC.grudge_write(k, "legion", "recall")
    turn = 30
    local claimed, other
    for _, o in ipairs(IC.R(k).OFFICES) do
        if o.affinity == "legion" and not claimed then claimed = o.slug end
        if o.affinity ~= "legion" and not other then other = o.slug end
    end
    assert(IC.appoint(k, other, 7003), "the unclaimed seat was refused")
    assert(#IC.grudges(k, "legion") == 2, "a seat they do not claim settled a grudge")
    assert(IC.appoint(k, claimed, 7002), "the claimed seat was refused")
    local book = IC.grudges(k, "legion")
    assert(#book == 1 and book[1].code == "recall", "the claimed seat did not settle the oldest")
end)

check("grudges: Pay the Weregild crosses the wire like any move", function()
    local k, f = grudge_court("dwf")
    f._cqi = 77
    IC.grudge_write(k, "legion", "castout")
    cm.get_human_factions = function() return {k} end
    IC.register()
    local ok, err = pcall(function()
        with_mp(k, function(sent)
            IC.mp_send(k, "plot", "weregild|7001|7002")
            assert(#IC.grudges(k, "legion") == 1, "settled before the trigger came back")
            assert(sent[1], "nothing was sent")
            deliver(sent[1])
            assert(#IC.grudges(k, "legion") == 0, "the trigger came back and nothing was settled")
        end)
    end)
    cm.get_human_factions = function() return {} end
    if not ok then error(err, 0) end
end)
```

- [ ] **Step 2: Run to verify they fail**

Run: `$env:IC_ONLY = "grudges:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: `FAIL grudges: Pay the Weregild settles the oldest grudge, ...: ... the weregild was refused`, exit 1.

- [ ] **Step 3: Implement the move.** In `IC.TUNE`, after `oath_broken_loyalty = 0,`:

```lua
    -- PAY THE WEREGILD (spec 2026-10-04 section 5): gold from the treasury,
    -- never a man's influence, and certain. No plot_chance_weregild: it never rolls.
    plot_weregild_cost    = 1000,
    plot_weregild_loyalty = 4,
```

In `IC.LOG_KINDS`, extend the Task 2 line to `grudge = true, grudge_settled = true, weregild = true,`.

Replace `IC.plots_in` with:

```lua
-- WHETHER A RACE'S COURT HAS A MOVE: no `race` is every race's; a race's
-- PLOT_KEYS list, where one is set, names its moves (contract).
function IC.plot_for_race(plot, race_key)
    if plot.race and plot.race ~= race_key then return false end
    local r = IC.RACES[race_key or ""]
    if not (r and r.PLOT_KEYS) then return true end
    for _, key in ipairs(r.PLOT_KEYS) do
        if key == plot.key then return true end
    end
    return false
end

-- A CATEGORY'S MOVES FOR ONE RACE; the Chaos Dwarf grid when none is named,
-- which is the grid the panel lays out at load.
function IC.plots_in(cat, race_key)
    local out = {}
    for i = 1, #IC.PLOTS do
        local p = IC.PLOTS[i]
        if p.cat == cat and IC.plot_for_race(p, race_key or "chd") then out[#out + 1] = p end
    end
    return out
end
```

In `IC.PLOTS`, directly after the `recall` row (its closing `blurb = "The Tower takes back its provinces."},`):

```lua
    -- PAY THE WEREGILD (spec 2026-10-04 Dwarfs section 5): Dwarf courts only,
    -- GOLD from the treasury, and SURE - a blood-price is paid, not tried. In
    -- the party column, not Bonds: plan 2026-10-04 phase 4 ruling 1.
    {key = "weregild", name = "Pay the Weregild", race = "dwf", gold = true, sure = true,
     icon = "ui/campaign ui/skills/wh_dlc06_character_abilities_oath_stone.png",
     cat = "house",
     cost = "plot_weregild_cost",
     effect = string.format(
         "Settles their oldest grudge. +%d loyalty. Paid from the treasury.",
         IC.TUNE.plot_weregild_loyalty),
     blurb = "Gold for the wrong, weighed out."},
```

(`blurb` stays the last field: the preview and the generator read it as the tail of the row. The icon is CA's, found in the installed ui packs on 2026-10-04 with `tools/read_pack_index.py`.)

In `IC.may_target`, directly after `if not plot then return false, "no such plot" end`:

```lua
    -- ANOTHER RACE'S MOVE does not exist here, whoever sends it.
    if not IC.plot_for_race(plot, IC.race_key(faction_key)) then
        return false, "no such plot"
    end
```

and directly after the `own party` refusal (`if IC.house_of_character(victim, faction_key) == IC.CROWN then return false, "own party" end`):

```lua
    if plot_key == "weregild" then
        local slug = IC.house_of_character(victim, faction_key)
        if #IC.grudges(faction_key, slug) == 0 then return false, "no grudge" end
    end
```

In `IC.can_plot`, replace the aimed branch's tail

```lua
    local cost = IC.plot_cost(plot_key, faction_key)
    local has = IC.standing(faction_key, actor_cqi)
    if has < cost then return false, "standing", cost - has end
    return true
end
```

with

```lua
    local cost = IC.plot_cost(plot_key, faction_key)
    -- A GOLD MOVE is the treasury's to pay, not his (plan 2026-10-04 phase 4).
    if IC.plot_by_key(plot_key).gold then
        local gold = IC.treasury(faction_key)
        if gold < cost then return false, "gold", cost - gold end
        return true
    end
    local has = IC.standing(faction_key, actor_cqi)
    if has < cost then return false, "standing", cost - has end
    return true
end
```

In `IC.plot_chance`, directly after its `if not IC.can_plot(...) then return nil end`:

```lua
    -- A SURE MOVE never rolls (the weregild).
    if IC.plot_by_key(plot_key).sure then return nil end
```

In `IC.plot`, replace

```lua
    local chance = IC.plot_chance(faction_key, plot_key, actor_cqi, target)
    IC.add_standing(faction_key, actor_cqi, -cost)
```

with

```lua
    local chance = IC.plot_chance(faction_key, plot_key, actor_cqi, target)
    if plot.gold then
        cm:treasury_mod(faction_key, -cost)
    else
        IC.add_standing(faction_key, actor_cqi, -cost)
    end
```

and add a branch before `elseif plot_key == "murder" then`:

```lua
    elseif plot_key == "weregild" then
        IC.grudge_settle(faction_key, against, "weregild")
        IC.move_loyalty(faction_key, against, IC.TUNE.plot_weregild_loyalty)
```

In `IC.plot_costs_seat`, as its first line:

```lua
    local plot = IC.plot_by_key(plot_key)
    if plot and plot.gold then return nil end
```

In `IC.appoint`, replace

```lua
    if not renewal then
        IC.move_loyalty(faction_key, slug, IC.TUNE.loyalty_appointed)
    end
```

with

```lua
    if not renewal then
        IC.move_loyalty(faction_key, slug, IC.TUNE.loyalty_appointed)
        -- A SEAT THEIR PARTY CLAIMS settles one grudge (spec 2026-10-04
        -- section 5); a renewal pays no loyalty and settles nothing.
        if slug == office.affinity then IC.grudge_settle(faction_key, slug, "seat") end
    end
```

If phase 2 gave the Dwarf race a `PLOT_KEYS` list (`grep -n "PLOT_KEYS" "Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_dwarf.lua"`), append `"weregild"` to it; with no list there is nothing to do.

- [ ] **Step 4: The Record line.** In `ICUI.intrigue_text`, directly above Task 2's `elseif e.kind == "grudge" then`:

```lua
    elseif e.kind == "weregild" then
        return string.format("%s pays %d gold in weregild to %s.", house, e.n or 0,
                             ICUI.logged_name(e.key, e.kw))
```

- [ ] **Step 5: Keep the existing checks and the generator on the Chaos Dwarf grid.** In the harness, replace `grid_plots` with:

```lua
local function grid_plots(race)
    local declared, out = {}, {}
    for c = 1, #IC.PLOT_CATS do declared[IC.PLOT_CATS[c].key] = true end
    for i = 1, #IC.PLOTS do
        local p = IC.PLOTS[i]
        if declared[p.cat] and IC.plot_for_race(p, race or "chd") then out[#out + 1] = p end
    end
    return out
end
```

In the check "every move has one place to be clicked, and no column is empty", after `for _, plot in ipairs(grid_plots()) do in_grid[plot.key] = true end` add `for _, plot in ipairs(grid_plots("dwf")) do in_grid[plot.key] = true end`. In the check "every move has odds, a picture and a sentence", replace

```lua
        assert(type(base) == "number",
            plot.key .. " has no plot_chance_ entry, so it can never miss")
        assert(base > 0 and base <= 100,
            plot.key .. " rolls against " .. tostring(base))
```

with

```lua
        -- A SURE MOVE (the weregild) never rolls, and says so with `sure`;
        -- any other move without odds is the bug this guards.
        assert(plot.sure or type(base) == "number",
            plot.key .. " has no plot_chance_ entry, so it can never miss")
        assert(plot.sure or (base > 0 and base <= 100),
            plot.key .. " rolls against " .. tostring(base))
```

In `tools/gen_ic_ui.py`, replace `plot_counts` with:

```python
def plot_counts(race="chd"):
    """How many moves each category holds for one race, in plot_cats() order.

    Read out of IC.PLOTS' own `cat` fields. A move with `race = "x"` counts for
    race x only, so the Chaos Dwarf grid stays the one PLOT_COUNTS lays out
    (plan 2026-10-04 phase 4). A category with no moves counts 0 and draws no
    column, which is what keeps this honest when one is emptied.
    """
    src = _model_src()
    blk = src[src.index("IC.PLOTS = {"):]
    blk = blk[:blk.index(chr(10) + "}")]
    cats = [c for c, _n in plot_cats()]
    got = []
    for chunk in re.split(chr(10) + r"    \{", blk)[1:]:
        r = re.search(r'race\s*=\s*"(\w+)"', chunk)
        if r and r.group(1) != race:
            continue
        got.append(re.search(r'cat\s*=\s*"(\w+)"', chunk).group(1))
    return [got.count(c) for c in cats]
```

- [ ] **Step 6: Run to verify they pass**

Run: `$env:IC_ONLY = "grudges:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: `iron court harness: ok (21 checks)`. Then `py tools\gen_iron_court.py --check`: the new move's two result lines (`Pay the Weregild - Success!` / `- Failure`) come from `model_moves()` with no edit.

- [ ] **Step 7: Checkpoint.** Run THE GATES. Expected: all green; `gen_ic_ui.py --check` still matches the Lua's load-time `PLOT_COUNTS` (both the Chaos Dwarf grid, sixteen cards).

### Task 5: AI Dwarf rulers pay weregild in their rotation

**Files:**
- Modify: `zzz_derpy_iron_court_parties.lua` - new `IC.ai_weregild` after `IC.ai_placate` (1253-1271); `IC.party_turn` (1282)
- Test: harness block

**Interfaces:**
- Consumes: Task 4 (`IC.can_plot`, `IC.plot` with `weregild`), `IC.party_leader`, `IC.candidates`, `IC.present_houses`.
- Produces: `IC.ai_weregild(faction_key) -> slug | nil` (new).

- [ ] **Step 1: Write the failing check:**

```lua
check("grudges: an AI Dwarf ruler pays weregild in its turn, when the treasury allows", function()
    local k, f = grudge_court("dwf")
    turn = 10; IC.grudge_write(k, "legion", "castout")
    turn = 30
    local due, acts = IC.party_turn_due, IC.TUNE.parties_act
    IC.party_turn_due = function() return true end
    IC.TUNE.parties_act = false
    f._gold = IC.TUNE.plot_weregild_cost - 1
    local ok, err = pcall(IC.party_turn, k)
    local poor = #IC.grudges(k, "legion")
    f._gold = 100000
    if ok then ok, err = pcall(IC.party_turn, k) end
    IC.party_turn_due, IC.TUNE.parties_act = due, acts
    assert(ok, err)
    assert(poor == 1, "a poor AI ruler paid a weregild")
    assert(#IC.grudges(k, "legion") == 0, "a rich AI ruler did not pay the weregild")
    local c = grudge_court("chd")
    assert(IC.ai_weregild(c) == nil, "a Chaos Dwarf AI ruler tried to pay a weregild")
end)
```

- [ ] **Step 2: Run to verify it fails**

Run: `$env:IC_ONLY = "grudges:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: `FAIL grudges: an AI Dwarf ruler pays weregild ...: ... a rich AI ruler did not pay the weregild`, exit 1.

- [ ] **Step 3: Implement.** After `IC.ai_placate`'s closing `end`:

```lua
-- AN AI DWARF RULER PAYS WEREGILD (spec 2026-10-04 section 5): to the party
-- with the most grudges, lowest loyalty first, ties in present_houses' order,
-- through IC.plot - so every rule a player meets, the gold among them, holds.
function IC.ai_weregild(faction_key)
    if IC.race_key(faction_key) ~= "dwf" then return nil end
    local court = IC.court(faction_key)
    local worst, most, low
    for _, slug in ipairs(IC.present_houses(faction_key)) do
        local n = #IC.grudges(faction_key, slug)
        local loyalty = court.houses[slug] and court.houses[slug].loyalty or 0
        if n > 0 and (not worst or n > most or (n == most and loyalty < low)) then
            worst, most, low = slug, n, loyalty
        end
    end
    if not worst then return nil end
    local target = IC.party_leader(faction_key, worst)
    if not target then return nil end
    for _, cand in ipairs(IC.candidates(faction_key)) do
        if IC.can_plot(faction_key, "weregild", cand.cqi, tostring(target)) then
            IC.plot(faction_key, "weregild", cand.cqi, tostring(target))
            return worst
        end
    end
    return nil
end
```

In `IC.party_turn`, replace `    if not human then IC.ai_placate(faction_key) end` with:

```lua
    if not human then
        IC.ai_placate(faction_key)
        IC.ai_weregild(faction_key)
    end
```

- [ ] **Step 4: Run to verify it passes**

Run: `$env:IC_ONLY = "grudges:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: `iron court harness: ok (22 checks)`.

- [ ] **Step 5: Checkpoint.** Run THE GATES. Expected: all green, including "no parties' turn failed anywhere in the run".

### Task 6: The panel - grudge lines, the weregild card, one grid per race

**Files:**
- Modify: `zzz_derpy_iron_court_ui.lua` - after the `ICUI.PLOT_XY` loop (today 866-877), before `function ICUI.apply_scale(bw)` (8975), `ICUI.open` (before `local scaled, why = pcall(ICUI.apply_scale, bw)`, 8014), `ICUI.draw_intrigue` (6050-6053), `ICUI.pick_title` (7053-7059), the picker's refusal words (7376-7392), `ICUI.TARGET_REFUSAL` (6723-6729), `ICUI.reason_text` (6835-6838)
- Modify: `tools/gen_ic_ui.py` - new `check_plot_depths()` beside `check_plot_cells()` (1296), its call in `check()` (7079), `selftest()` (8500)
- Modify: `tools/preview_iron_court.py` - `Move` (203-204), `read_plots` (234-262), `plot_cards` (638-656), its call in `render` (1989), the art list in `render` (967-978)
- Test: harness block

**Interfaces:**
- Consumes: Task 4 (`plot.gold`, `IC.plot_for_race`, `IC.plots_in(cat, race)`, `plot_counts(race)`), phase 3's `render(..., race)` in the preview.
- Produces: `ICUI.PLOT_GRIDS[race] = {xy, at, counts}` and `ICUI.use_plot_grid(race_key)` (new); `gen_ic_ui.check_plot_depths()`; preview `plot_cards(G, race="chd")`, `Move.race`, `Move.gold`.

- [ ] **Step 1: Write the failing checks:**

```lua
check("grudges: the loyalty breakdown names each grudge and the kinship", function()
    local k = grudge_court("dwf")
    turn = 34
    IC.grudge_write(k, "legion", "castout")
    cm.get_human_factions = function() return {k} end
    local tip = bare(plain(ICUI.loyalty_tip(k, IC.court(k), "legion")))
    cm.get_human_factions = function() return {} end
    if os.getenv("IC_SHOW_TIP") then print(tip) end
    assert(string.find(tip, "Grudge: Cast Out, turn 34: -1", 1, true), tip)
    assert(string.find(tip, "Kin of the Karak: +1", 1, true), tip)
    assert(string.find(tip, "Pay the Weregild", 1, true), "the breakdown never says how to settle it")
end)

check("grudges: a Dwarf court's intrigue grid carries Pay the Weregild at a gold price", function()
    local k, f = grudge_court("dwf")
    IC.grudge_write(k, "legion", "castout")
    ICUI.use_plot_grid("dwf")
    local ok, err = pcall(function()
        assert(#ICUI.PLOT_XY == #grid_plots("dwf") and #grid_plots("dwf") == #grid_plots() + 1,
            "the Dwarf grid has " .. #ICUI.PLOT_XY .. " cells")
        with_fake_panel(function(panel)
            cm.get_human_factions = function() return {k} end
            ICUI.view, ICUI.pick, ICUI.scroll.intrigue = "intrigue", nil, 0
            ICUI.refresh()
            local at
            for i, move in pairs(ICUI.plot_keys) do
                if move and move.plot == "weregild" then at = i end
            end
            assert(at, "no card carries the weregild")
            local card = panel.children[ICUI.PLOT .. "_" .. at]
            assert(card.visible, "the weregild's card is hidden")
            assert(card.children.ic_plot_cost.text == ICUI.gold(IC.TUNE.plot_weregild_cost),
                "the weregild's price reads " .. card.children.ic_plot_cost.text)
            f._gold = 0
            ICUI.refresh()
            assert(is_red(card.children.ic_plot_cost.text), "an empty treasury drew the weregild affordable")
            ICUI.pick = {kind = "plot", plot = "weregild", key = "7002"}
            local title = ICUI.pick_title()
            ICUI.pick = nil
            assert(string.find(title, ICUI.gold(IC.TUNE.plot_weregild_cost), 1, true)
                   and not string.find(title, "influence", 1, true), "the picker says " .. title)
        end)
        assert(ICUI.TARGET_REFUSAL["no grudge"] and ICUI.reason_text("no grudge") ~= "",
            "a party with no grudge is refused in no words")
    end)
    ICUI.use_plot_grid("chd")
    cm.get_human_factions = function() return {} end
    if not ok then error(err, 0) end
    assert(#ICUI.PLOT_XY == #grid_plots(), "the Chaos Dwarf grid did not come back")
    for i = 1, #ICUI.plot_at do
        assert(ICUI.plot_at[i].key ~= "weregild", "the Chaos Dwarf grid carries the weregild")
    end
end)

check("grudges: the panel opens on its own race's move grid", function()
    local k = grudge_court("dwf")
    local ok, err = pcall(with_fake_root, function()
        cm.get_human_factions = function() return {k} end
        ICUI.open()
        local found = false
        for i = 1, #ICUI.plot_at do
            if ICUI.plot_at[i].key == "weregild" then found = true end
        end
        ICUI.close()
        assert(found, "a Dwarf player's panel opened on the Chaos Dwarf grid")
    end)
    ICUI.use_plot_grid("chd")
    if not ok then error(err, 0) end
end)
```

- [ ] **Step 2: Run to verify they fail**

Run: `$env:IC_ONLY = "grudges:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: the first passes (the tooltip already prints `IC.loyalty_terms`, Task 2); `FAIL grudges: a Dwarf court's intrigue grid ...: ... attempt to call field 'use_plot_grid' (a nil value)`, exit 1.

- [ ] **Step 3: Implement the per-race grid.** In `zzz_derpy_iron_court_ui.lua`, directly after the `ICUI.PLOT_XY` loop's closing `end` (today 877):

```lua

-- ONE GRID PER RACE (plan 2026-10-04 phase 4). A move with `race` is in its
-- race's grid only, so the Chaos Dwarf grid above stays the sixteen cards it
-- was and the Dwarf grid has Pay the Weregild in the party column. Same card
-- size for both: gen_ic_ui.check_plot_depths holds every race's columns to
-- PLOT_DEPTH. ICUI.use_plot_grid picks one when the panel opens.
ICUI.PLOT_GRIDS = {}
for _, rk in ipairs(IC.RACE_ORDER) do
    local g = {xy = {}, at = {}, counts = {}}
    for col = 1, ICUI.PLOT_COLS do
        local moves = IC.plots_in(IC.PLOT_CATS[col].key, rk)
        g.counts[col] = #moves
        for row = 1, #moves do
            g.xy[#g.xy + 1] = {
                ICUI.plot_col_x(col - 1),
                ICUI.PLOTS_Y + (row - 1) * (ICUI.PLOT_H + ICUI.CARD_GAP_Y),
            }
            g.at[#g.xy] = moves[row]
        end
    end
    ICUI.PLOT_GRIDS[rk] = g
end
```

Directly before `function ICUI.apply_scale(bw)`:

```lua
-- THE PLAYER'S RACE'S MOVE GRID, as the 1920 layout apply_scale scales from,
-- and as the cells themselves until it does. Written in place, so nothing
-- holding ICUI.PLOT_XY holds a stale one, and trimmed, so a Chaos Dwarf grid
-- after a Dwarf one keeps no seventeenth cell.
function ICUI.use_plot_grid(race_key)
    local g = ICUI.PLOT_GRIDS[race_key or ""] or ICUI.PLOT_GRIDS.chd
    local xy = {}
    for i, p in ipairs(g.xy) do xy[i] = {p[1], p[2]} end
    ICUI.BASE.PLOT_XY = xy
    for k in pairs(ICUI.PLOT_XY) do
        if not xy[k] then ICUI.PLOT_XY[k] = nil end
    end
    for i, p in ipairs(xy) do ICUI.PLOT_XY[i] = {p[1], p[2]} end
    ICUI.plot_at, ICUI.PLOT_COUNTS = g.at, g.counts
end
```

In `ICUI.open`, directly before `local scaled, why = pcall(ICUI.apply_scale, bw)`:

```lua
        -- THE PLAYER'S OWN MOVES, before anything is scaled or built.
        ICUI.use_plot_grid(IC.race_key(ICUI.player()) or "chd")
```

- [ ] **Step 4: Implement the gold price and the words.** In `ICUI.draw_intrigue`, replace

```lua
            local price = ICUI.cost(IC.plot_cost(plot.key, faction))
            local purse = IC.is_civil_mission(plot.key) and richest_civil
                          or richest
            local afford = purse >= IC.plot_cost(plot.key, faction)
```

with

```lua
            -- A GOLD MOVE (the weregild) is priced in the treasury, not in a
            -- courtier's influence (plan 2026-10-04 phase 4).
            local cost = IC.plot_cost(plot.key, faction)
            local price = plot.gold and ICUI.gold(cost) or ICUI.cost(cost)
            local purse = plot.gold and IC.treasury(faction)
                          or IC.is_civil_mission(plot.key) and richest_civil
                          or richest
            local afford = purse >= cost
```

In `ICUI.pick_title`, inside `if ICUI.pick.kind == "plot" then`, before its `return`:

```lua
        if plot and plot.gold then
            return string.format("Who carries this out? %s - pays %s gold from the treasury",
                ICUI.plot_label(ICUI.pick.plot, ICUI.pick.key),
                ICUI.gold(IC.plot_cost(ICUI.pick.plot, ICUI.player())))
        end
```

In the picker's plotting refusals, after the `standing` branch (`action = string.format("Short %s", ICUI.cost(short_by or 0))`):

```lua
                elseif why_not == "gold" then
                    action = string.format("Short %s", ICUI.gold(short_by or 0))
```

In `ICUI.TARGET_REFUSAL`, add `["no grudge"] = "No Grudge",`. In `ICUI.reason_text`, directly before `elseif why == "content" then`:

```lua
    elseif why == "no grudge" then
        return "Their book holds no grudge to settle."
```

- [ ] **Step 5: The generator and the preview.** In `tools/gen_ic_ui.py`, directly after `check_plot_cells()`'s function:

```python
def check_plot_depths():
    """Every race's move grid fits the card height PLOT_DEPTH was derived for.

    The Chaos Dwarf grid sets the card (PLOT_COUNTS); a race's own move adds a
    card to one column of that race's grid only, and a column deeper than
    PLOT_DEPTH would draw its last card under the pager (plan 2026-10-04 phase 4).
    """
    out = []
    for race in ("chd", "dwf"):
        for (key, _n), n in zip(PLOT_CATS, plot_counts(race)):
            if n > PLOT_DEPTH:
                out.append("the %s grid's %s column holds %d moves; cards are sized for %d"
                           % (race, key, n, PLOT_DEPTH))
    return out
```

In `check()`, after `out.extend(check_plot_cells())`: `    out.extend(check_plot_depths())`. In `selftest()`, directly after `selftest_compact()`:

```python
    # THE DWARF GRID CARRIES THE WEREGILD AND THE CHAOS DWARF GRID DOES NOT, and
    # a column past the depth is reported (plan 2026-10-04 phase 4).
    global PLOT_DEPTH
    _h = [c for c, _n in PLOT_CATS].index("house")
    assert plot_counts("dwf")[_h] == plot_counts("chd")[_h] + 1, "the weregild is not in the Dwarf party column"
    assert plot_counts("chd") == PLOT_COUNTS, "the Chaos Dwarf grid moved"
    assert check_plot_depths() == [], check_plot_depths()
    _depth, PLOT_DEPTH = PLOT_DEPTH, 2
    _got = check_plot_depths()
    PLOT_DEPTH = _depth
    assert any("dwf grid's house column" in e for e in _got), "check_plot_depths cannot fail"
```

In `tools/preview_iron_court.py`, replace the `Move` definition with

```python
Move = collections.namedtuple(
    "Move", "key name blurb cost aimed icon cat effect race gold",
    defaults=(None, False))
```

In `read_plots`, replace the `out.append(Move(...))` with

```python
        # A RACE'S OWN MOVE, and one paid in gold (plan 2026-10-04 phase 4).
        race = re.search(r'race = "(\w+)"', chunk)
        out.append(Move(key, name, blurb, cost, "aimed = false" not in chunk,
                        icon, cat, effect, race.group(1) if race else None,
                        "gold = true" in chunk))
```

Replace `plot_cards` with

```python
def plot_cards(G, race="chd"):
    """One Card per move of this race's grid, in ICUI.draw_intrigue's order.

    The same read_plots() source as before - a move added to the model draws here
    with no edit - split into the four cells a card has rather than concatenated
    into one widened column. A gold move (the weregild) is priced with the
    treasury's icon; the demo court's treasury is not modelled, so it draws
    affordable.
    """
    ui = bare(lua("ui"))
    cost_icon = re.search(r'ICUI\.COST_ICON = "([^"]+)"', ui).group(1)
    gold_icon = re.search(r'ICUI\.GOLD_ICON = "([^"]+)"', ui).group(1)
    out = []
    for p in read_plots():
        if p.race and p.race != race:
            continue
        purse = DEMO_PURSE if p.aimed else DEMO_PURSE_CIVIL
        afford = p.gold or purse >= p.cost
        price = "[[img:%s]][[/img]]%d" % (gold_icon if p.gold else cost_icon, p.cost)
        # THE SAME CONCATENATION fill_plot makes, in the same order: what the
        # move does first, what it feels like second.
        out.append(Card(p.name, p.effect + " " + p.blurb,
                        price if afford else red(price), afford,
                        p.icon, p.cat))
    return out
```

In `render`, change `moves = plot_cards(G)` to pass the race phase 3 gave `render` (`grep -n "def render" tools/preview_iron_court.py` names it), e.g. `moves = plot_cards(G, race)`; and in its `PG.extract_art(... extra=...)` list add the treasury icon beside `cost_icon`: define `gold_icon = re.search(r'ICUI\.GOLD_ICON = "([^"]+)"', ui).group(1)` next to `cost_icon` and put `gold_icon` after `cost_icon` in `extra`.

- [ ] **Step 6: Run to verify they pass**

Run: `$env:IC_ONLY = "grudges:"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: `iron court harness: ok (25 checks)`. Then `py tools\gen_ic_ui.py --check`, `py tools\gen_ic_ui.py --selftest`, `py tools\preview_iron_court.py --check`, `py tools\preview_iron_court.py --selftest`: all exit 0. `gen_ic_ui.py --check`'s text fit (20d) now measures the weregild card too; a failure there is the effect line or blurb too long for four lines - shorten the blurb, not the effect.

- [ ] **Step 7: Checkpoint.** Run THE GATES. Expected: all green.

### Task 7: Preview for the author - STOP for approval

**Files:**
- Read only: `.skilltree_cache/ui_preview/` (the preview's output), the harness's printed tooltip.

**Interfaces:**
- Consumes: Task 6.
- Produces: nothing; the author's approval or a list of changes.

- [ ] **Step 1: Render the Dwarf intrigue tab.**

Run: `py tools\preview_iron_court.py --race dwf`
Expected: `wrote ...ic_intrigue...png` lines for 1600, 1920 and 2560 with no `PROBLEM:` line. Also run `py tools\preview_iron_court.py` (Chaos Dwarf) and confirm its intrigue picture is unchanged against the copy in `Modding Files/source/iron_court_preview/` that phase 3 approved.

- [ ] **Step 2: Print the grudge lines as the player reads them.**

Run: `$env:IC_ONLY = "grudges: the loyalty breakdown"; $env:IC_SHOW_TIP = 1; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY; Remove-Item Env:IC_SHOW_TIP`
Expected: the tooltip text (the party's header, `Grudge: Cast Out, turn 34: -1`, `Kin of the Karak: +1`, the note block), then `iron court harness: ok (1 checks)`.

- [ ] **Step 3: STOP.** Show the author the three Dwarf intrigue pictures (the weregild card in the party column, its gold price) and the printed tooltip, and name ruling 1 (party column, not Bonds, and why) and the chosen numbers (1000 gold, +4 loyalty, the Iron Law's -10). Do not start Task 8 until the author approves. Every change the author asks for goes back to the task that owns it, and Steps 1-3 run again.

### Task 8: Mutants, build, deploy, record

**Files:**
- Modify: `tools/mutate_iron_court.py` (a grudges block appended inside `MUTANTS`, before its closing `]`)
- Create: `docs/sessions/HANDOFF_20261004_IRON_COURT_DWARFS_PHASE4.md`
- Modify: `docs/SESSION_INDEX.md` (one line)

**Interfaces:**
- Consumes: Tasks 1-7.
- Produces: six mutants named `grudge: ...`.

- [ ] **Step 1: Write the mutants** (`M` is the model path alias):

```python
    # ---- grudges inside the court (plan 2026-10-04 phase 4) -------------
    ("grudge: the race guard dropped", M,
     """    if IC.race_key(faction_key) ~= "dwf" or not IC.GRUDGE_WORDS[code or ""] then return false end""",
     """    if not IC.GRUDGE_WORDS[code or ""] then return false end"""),
    ("grudge: the cap removed", M,
     """    if #book >= IC.TUNE.grudge_max then return false end""",
     """"""),
    ("grudge: the fade added", M,
     """        for i, g in ipairs(IC.grudges(faction_key, slug)) do""",
     """        for i, g in ipairs(IC.grudges(faction_key, slug)) do if cm:model():turn_number() - g.turn > 20 then break end"""),
    ("grudge: the newest settled, not the oldest", M,
     """    local g = table.remove(book, 1)""",
     """    local g = table.remove(book)"""),
    ("grudge: kinship on every race", M,
     """    local dwarf = IC.race_key(faction_key) == "dwf\"""",
     """    local dwarf = true"""),
    ("grudge: the countdown read off IC.TUNE", M,
     """                house.clock = IC.tune(faction_key, "secede_turns")""",
     """                house.clock = IC.TUNE.secede_turns"""),
```

- [ ] **Step 2: Run them**

Run: `py tools\mutate_iron_court.py "grudge:"`
Expected: `6 mutants, 0 unexplained`. A survivor means a missing assertion: add it to the owning task's check, watch it catch the mutant, re-run. A stale anchor is a finding, not a skip. Then re-run the generators (`py tools\gen_iron_court.py`, `py tools\gen_ic_ui.py`): the runner restores the source, not what the source wrote.

- [ ] **Step 3: Gates, build, deploy.** Run THE GATES, then `py tools\import_iron_court.py`, then `py tools\deploy_iron_court.py` (RPFM must be open; with Warhammer3.exe running, `--wait` in the background).
Expected: every gate green; the deploy reports the pack byte-identical to the build in data/ and the Workshop folder, with its backup under `Modding Files/Backup/`. Read the live pack back with `py tools\read_pack_index.py "<the deployed pack>" zzz_derpy_iron_court.lua` and confirm `IC.GRUDGE_CODES` and `weregild` are in it.

- [ ] **Step 4: Record.** Write `docs/sessions/HANDOFF_20261004_IRON_COURT_DWARFS_PHASE4.md`: what was built, the eleven rulings, the gates and the mutant count, and the in-game looks owed - a Dwarf campaign: An Insult to the Clan writes a grudge line in the party's loyalty tooltip, Pay the Weregild settles it and charges the treasury, a claimed seat settles one, a Dwarf party's countdown reads the longer count; a Chaos Dwarf campaign shows none of it; an older save loads. Add one line to `docs/SESSION_INDEX.md` pointing at it. Push nothing.
