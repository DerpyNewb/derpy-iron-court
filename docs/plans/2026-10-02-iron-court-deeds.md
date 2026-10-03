# Iron Court Deeds Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The player's deeds give the matching court party fading renown that counts as party weight, so the governments mirror how the player plays. An absent party with enough renown is drawn in by the next lord recruited. The panel shows all of it.

**Architecture:** Model work goes in `zzz_derpy_iron_court.lua`:

- a renown table per court, saved as new fields 15 and 16;
- `IC.deed` and `IC.add_renown`;
- `IC.fade_renown` in `IC.turn`;
- `IC.house_weight` adding renown;
- six new event listeners, plus a line in the existing `ic_battle`;
- `IC.deed_join`, consulted from the existing `ic_born` listener;
- a one-time `gov_intro` card in `IC.gov_step`.

Drift is untouched: renown reaches it through `IC.share`. The panel (`zzz_derpy_iron_court_ui.lua`) reads the model. The generator adds two events and seven secondary loc lines. MCT adds one live switch.

**Tech Stack:** Lua 5.1 (game scripts and harness), Python 3 (generators, gates, mutation runner), RPFM MCP (pack build).

**Spec:** `docs/superpowers/specs/2026-10-02-iron-court-deeds-design.md`

## Global Constraints

- The workspace is **not a git repo**. Each "Commit" step below is a **ledger line** in `.superpowers/sdd/2026-10-02-iron-court-deeds/progress.md`, never a git command.
- **CRLF is preserved.** Every court Lua file and `tools/_iron_court_harness.lua` is CRLF. Edit them with the Edit tool, or with the exact-anchor CRLF patcher `scratchpad/icp.py`. **Never `sed -i`**: Git Bash sed strips CRLF.
- **Patch scripts containing backslashes go through the Write tool, never a heredoc.**
- **Lua 5.1.5.** Run `luac -p` on every edited Lua file. A number literal never goes on the LEFT of an arithmetic operator (`check_lua_literal_left.py`).
- **`IC.TUNE_ORDER` is append-only.** A new MCT key is three edits (`IC.TUNE`, `IC.TUNE_ORDER`, MCT `SWITCHES`), plus `IC.LIVE_TUNE` and the harness `LIVE` list for a live switch.
- **`IC.EVENTS` and the generator's `EVENTS` are appended in the same order**, because the generator derives the index from position. New ids: `gov_intro` 2631, `party_drawn` 2632.
- **Player text:**
  - "Reputation", never "standing";
  - no cap, accrue, rep or AI jargon in loc, tooltips or MCT;
  - never the word "rung";
  - no emojis.
- **Renown is player courts only:** `IC.deeds_on(faction_key)` is `IC.TUNE.deeds ~= false and IC.is_human(faction_key)`.
- **Keys from CA's DB, verified 2026-10-02:**
  - temple buildings `wh3_dlc23_chd_tower_temple_of_hashut_1` and `wh3_dlc23_special_great_temple_of_hashut_chd`;
  - captive option record `wh3_dlc23_captive_option_enslave_chaos_dwarfs`, outcome `enslave_slaves_only`. `enslave_replenishment_only` is recruiting captives, and does NOT count.
- **The harness runs from the workspace root:** `IC_TEST_ALL=1 "/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua > .superpowers/sdd/2026-10-02-iron-court-deeds/h.log 2>&1; tail -1 .superpowers/sdd/2026-10-02-iron-court-deeds/h.log`. Baseline: `iron court harness: ok (893 checks)`.
- **The mutation runner** runs from the workspace root: `py tools/mutate_iron_court.py "deed:"`. Its anchors must match the shipped Lua exactly, and its quotes are escaped as `\"`.

## Review Focus

1. **A battle during the AI's turn** (the player defends) scores renown, counting toward the cap since the player's last turn start. The cap resets only in the player's own `IC.turn`. Test in Task 2.
2. **A save made mid-turn and reloaded** must not reset the per-turn limit. `renown_got` is saved in field 15. Test in Task 1 (round-trip includes `got`).
3. **A party drawn in, then dissolved or seceded,** loses its house row, and its renown fades as an absent party's would. It must not be drawn in again the same turn by a stale line. Test in Task 3: after `IC.remove_house`, renown is capped at the line again by `add_renown`, and `deed_waiting` needs a lord.
4. **The switch flipped off mid-campaign:** existing renown keeps fading and keeps counting as weight until it is gone, and no party is drawn in. Test in Task 5.
5. **An old save (14 fields) loads with no renown and no intro flag,** and still shows the intro once. Test in Task 4.

---

### Task 1: Renown in the model (weight, fade, save, Record entry)

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua`. Anchors:
  - `local function new_court()` (around line 1003);
  - `IC.LOG_KINDS = {` (around 1032);
  - the GOVERNMENTS block in `IC.TUNE` (around line 616);
  - `function IC.house_weight` (around 1239);
  - `function IC.pack` (its `return join({...})`, around line 1402);
  - the end of `function IC.unpack` (`IC.state[faction_key] = court`, around 1566);
  - `function IC.turn` (after `IC.reconcile_houses(faction_key)`, around 5585).
- Test: `tools/_iron_court_harness.lua`. Insert the new checks just before `check("governments: a leading rival builds pressure toward its own, and a new leader restarts it"`, after the `gov_court` helper.

**Interfaces:**
- Produces:
  - `IC.DEEDS[code] = {party = slug, tune = key, alt = slug|nil}` for codes `battle, hellforge, rite, temple, slaves, raze, convoy, research`;
  - `IC.deeds_on(faction_key) -> boolean`;
  - `IC.renown(faction_key, party) -> number`;
  - `IC.add_renown(faction_key, party, n, code) -> number added`;
  - `IC.deed(faction_key, code) -> number added`;
  - `IC.fade_renown(faction_key)`;
  - court fields `renown = {}`, `renown_got = {}`, `gov_intro = nil|true`, `confed_turn = 0`;
  - log kind `deed` (slug = party, key = code, n = sum this turn) and log kind `drawn`;
  - `IC.TUNE` keys `deeds = true`, `deed_battle = 3`, `deed_hellforge = 4`, `deed_rite = 4`, `deed_temple = 2`, `deed_slaves = 3`, `deed_raze = 3`, `deed_convoy = 5`, `deed_research = 2`, `renown_fade_pct = 10`, `renown_turn_cap = 8`, `renown_join_line = 20`.

- [ ] **Step 1: Write the failing checks.** Insert into the harness before the anchor named above:

```lua
-- A PLAYER COURT FOR THE DEEDS (spec 2026-10-02 deeds), past its grace period.
local function deed_court(weights)
    local court = gov_court(weights or {crown = 10, legion = 10})
    court.renown, court.renown_got = {}, {}
    return court
end

check("deeds: a deed adds its renown to its party, and renown is party weight", function()
    local court = deed_court({crown = 10, legion = 10})
    local before = IC.house_weight(F, "legion")
    assert(IC.deed(F, "battle") == IC.TUNE.deed_battle, "a battle added nothing")
    assert(IC.renown(F, "legion") == IC.TUNE.deed_battle, "renown " .. IC.renown(F, "legion"))
    assert(IC.house_weight(F, "legion") == before + IC.TUNE.deed_battle,
        "renown is not weight: " .. IC.house_weight(F, "legion") .. " from " .. before)
    assert(IC.renown(F, "crown") == 0, "the Crown took renown")
    gov_done()
end)

check("deeds: the Ledger takes a convoy only when there is no Road", function()
    local court = deed_court({crown = 10, ledger = 10})
    IC.deed(F, "convoy")
    assert(IC.renown(F, "ledger") == IC.TUNE.deed_convoy and IC.renown(F, "road") == 0,
        "no Road: the convoy went to " .. tostring(next(court.renown)))
    court = deed_court({crown = 10, ledger = 10, road = 10})
    IC.deed(F, "convoy")
    assert(IC.renown(F, "road") == IC.TUNE.deed_convoy and IC.renown(F, "ledger") == 0,
        "with a Road the Ledger took the convoy")
    gov_done()
end)

check("deeds: a party gains at most renown_turn_cap in one turn, and the cap is saved", function()
    local court = deed_court({crown = 10, legion = 10})
    for _ = 1, 10 do IC.deed(F, "battle") end
    assert(IC.renown(F, "legion") == IC.TUNE.renown_turn_cap,
        "ten battles gave " .. IC.renown(F, "legion"))
    IC.save(F)
    IC.state = {}
    IC.load(F)
    assert(IC.deed(F, "battle") == 0, "a reload reset the turn's limit")
    gov_done()
end)

check("deeds: renown fades by renown_fade_pct a turn, at least 1, and ends at nothing", function()
    local court = deed_court({crown = 10, legion = 10})
    court.renown.legion, court.renown.forge = 50, 1
    court.renown_got.legion = 8
    IC.fade_renown(F)
    assert(court.renown.legion == 50 - math.floor(50 * IC.TUNE.renown_fade_pct / 100),
        "50 faded to " .. tostring(court.renown.legion))
    assert(court.renown.forge == nil, "1 renown did not fade away")
    assert(not court.renown_got.legion, "the turn's limit was not reset")
    gov_done()
end)

check("deeds: an absent party's renown stops at the join line", function()
    local court = deed_court({crown = 10})
    for _ = 1, 20 do court.renown_got = {}; IC.deed(F, "battle") end
    assert(IC.renown(F, "legion") == IC.TUNE.renown_join_line,
        "an absent Legion banked " .. IC.renown(F, "legion"))
    gov_done()
end)

check("deeds: AI courts score nothing", function()
    local court = deed_court({crown = 10, legion = 10})
    cm.get_human_factions = function() return {"someone_else"} end
    assert(IC.deed(F, "battle") == 0 and IC.renown(F, "legion") == 0, "an AI court took renown")
    gov_done()
end)

check("deeds: one Record entry per party, deed and turn, summed", function()
    local court = deed_court({crown = 10, legion = 10})
    court.log = {}
    IC.deed(F, "battle")
    IC.deed(F, "battle")
    assert(#court.log == 1 and court.log[1].kind == "deed" and court.log[1].slug == "legion"
           and court.log[1].key == "battle" and court.log[1].n == 2 * IC.TUNE.deed_battle,
        "the Record holds " .. #court.log .. " entries")
    gov_done()
end)

check("deeds: the save round-trips renown, the turn's gains, the intro and the confederation turn", function()
    local court = deed_court({crown = 10, legion = 10})
    court.renown = {legion = 12, forge = 20}
    court.renown_got = {legion = 3}
    court.gov_intro, court.confed_turn = true, 17
    IC.save(F)
    IC.state = {}
    local back = IC.load(F)
    assert(back.renown.legion == 12 and back.renown.forge == 20, "renown lost")
    assert(back.renown_got.legion == 3, "the turn's gains lost")
    assert(back.gov_intro == true and back.confed_turn == 17, "intro or confederation turn lost")
    -- A SAVE FROM BEFORE DEEDS: fourteen fields.
    local packed = IC.pack(F)
    local cut = {}
    for field in string.gmatch(packed .. "|", "([^|]*)|") do cut[#cut + 1] = field end
    IC.unpack(F, table.concat(cut, "|", 1, 14))
    assert(next(IC.court(F).renown) == nil and not IC.court(F).gov_intro
           and IC.court(F).confed_turn == 0, "an old save did not load empty")
    gov_done()
end)
```

- [ ] **Step 2: Run the harness to verify they fail.**

Run: the harness command from Global Constraints.
Expected: FAIL on every `deeds:` check with `attempt to call field 'deed' (a nil value)` (or `renown`/`fade_renown`). 893 others pass.

- [ ] **Step 3: Write the model code.**

In `IC.TUNE`, after `gov_drift           = true,`:

```lua

    -- DEEDS (spec 2026-10-02 deeds). Renown a deed gives its party, how fast it
    -- fades, the most one party gains in a turn, and where an absent party is
    -- drawn in. Not on the MCT page; gov_drift_share is the precedent.
    deeds               = true,
    deed_battle         = 3,
    deed_hellforge      = 4,
    deed_rite           = 4,
    deed_temple         = 2,
    deed_slaves         = 3,
    deed_raze           = 3,
    deed_convoy         = 5,
    deed_research       = 2,
    renown_fade_pct     = 10,
    renown_turn_cap     = 8,
    renown_join_line    = 20,
```

In `new_court()`, after `gov_holds = 0,`:

```lua
        -- DEEDS (spec 2026-10-02 deeds): [party] = renown, [party] = renown
        -- gained since this court's turn began.
        renown = {},
        renown_got = {},
        confed_turn = 0,  -- the turn this court last took in a confederation
```

In `IC.LOG_KINDS`, after `doctrine_force = true, doctrine_lapse = true,`:

```lua
    -- DEEDS (spec 2026-10-02 deeds): renown a party took, and a party drawn in.
    deed = true, drawn = true,
```

Replace `IC.house_weight`'s return:

```lua
    return house.weight + (house.gov_weight or 0)
        + IC.member_weight(faction_key, slug)
```

with:

```lua
    -- RENOWN IS WEIGHT (spec 2026-10-02 deeds section 2), kept out of
    -- house.weight because that number is office bookkeeping.
    local renown = (IC.court(faction_key).renown or {})[slug or ""] or 0
    return house.weight + (house.gov_weight or 0)
        + IC.member_weight(faction_key, slug) + renown
```

After `function IC.house_weight ... end`, add:

```lua
-- WHAT EACH DEED MOVES (spec 2026-10-02 deeds section 2). `alt` takes the deed
-- when `party` is not in the court and `alt` is.
IC.DEEDS = {
    battle    = {party = "legion", tune = "deed_battle"},
    hellforge = {party = "forge",  tune = "deed_hellforge"},
    rite      = {party = "temple", tune = "deed_rite"},
    temple    = {party = "temple", tune = "deed_temple"},
    slaves    = {party = "chain",  tune = "deed_slaves"},
    raze      = {party = "chain",  tune = "deed_raze"},
    convoy    = {party = "road",   tune = "deed_convoy", alt = "ledger"},
    research  = {party = "tower",  tune = "deed_research"},
}

function IC.deeds_on(faction_key)
    return IC.TUNE.deeds ~= false and IC.is_human(faction_key)
end

function IC.renown(faction_key, party)
    return (IC.court(faction_key).renown or {})[party or ""] or 0
end

-- ONE ENTRY PER PARTY, DEED AND TURN: a busy turn adds to the last entry rather
-- than burying the Record.
function IC.log_deed(faction_key, party, code, n)
    local log = IC.court(faction_key).log or {}
    local last = log[#log]
    if last and last.kind == "deed" and last.slug == party and last.key == code
       and last.turn == cm:model():turn_number() then
        last.n = (last.n or 0) + n
        return true
    end
    return IC.log(faction_key, "deed", party, code, n)
end

-- AT MOST renown_turn_cap A TURN, and an absent party stops at the join line:
-- there it waits for a lord (IC.deed_join).
function IC.add_renown(faction_key, party, n, code)
    local court = IC.court(faction_key)
    court.renown = court.renown or {}
    court.renown_got = court.renown_got or {}
    local got = court.renown_got[party] or 0
    n = math.min(n or 0, math.max(0, IC.TUNE.renown_turn_cap - got))
    local have = court.renown[party] or 0
    if not court.houses[party] then
        n = math.min(n, math.max(0, IC.TUNE.renown_join_line - have))
    end
    if n <= 0 then return 0 end
    court.renown[party] = have + n
    court.renown_got[party] = got + n
    IC.log_deed(faction_key, party, code, n)
    return n
end

function IC.deed(faction_key, code)
    local d = IC.DEEDS[code or ""]
    if not d or not IC.deeds_on(faction_key) then return 0 end
    local court = IC.court(faction_key)
    local party = d.party
    if d.alt and not court.houses[party] and court.houses[d.alt] then party = d.alt end
    return IC.add_renown(faction_key, party, IC.TUNE[d.tune], code)
end

-- AT THIS COURT'S TURN START, every court: renown_fade_pct, at least 1, and
-- the turn's limit begins again.
function IC.fade_renown(faction_key)
    local court = IC.court(faction_key)
    for party, n in pairs(court.renown or {}) do
        local left = n - math.max(1, math.floor(n * IC.TUNE.renown_fade_pct / 100))
        court.renown[party] = left > 0 and left or nil
    end
    court.renown_got = {}
end
```

In `IC.pack`, before `return join({`:

```lua
    -- DEEDS (spec 2026-10-02 deeds): field 15 is "party,renown,got" per party,
    -- field 16 is "intro,confed_turn".
    local renown = {}
    for party, n in pairs(court.renown or {}) do
        renown[#renown + 1] = string.format("%s,%d,%d", party, n,
                                            (court.renown_got or {})[party] or 0)
    end
    table.sort(renown)
    local deeds = string.format("%d,%d", court.gov_intro and 1 or 0, court.confed_turn or 0)
```

Change the end of the `join({...}` list from `join(sent, ";"), gov}, "|")` to `join(sent, ";"), gov, join(renown, ";"), deeds}, "|")`.

In `IC.unpack`, before `IC.state[faction_key] = court`:

```lua
    -- Fields 15 and 16 are optional: a save from before deeds has no renown,
    -- has not shown the introduction, and took no confederation.
    for _, entry in ipairs(split(fields[15] or "", ";")) do
        local b = split(entry, ",")
        local n = tonumber(b[2])
        if b[1] and n and n > 0 then
            court.renown[b[1]] = n
            local got = tonumber(b[3]) or 0
            if got > 0 then court.renown_got[b[1]] = got end
        end
    end
    local d = split(fields[16] or "", ",")
    court.gov_intro = (tonumber(d[1]) == 1) or nil
    court.confed_turn = tonumber(d[2]) or 0
```

In `IC.turn`, after `IC.reconcile_houses(faction_key)`:

```lua
    -- BEFORE ANYTHING READS A SHARE THIS TURN (spec 2026-10-02 deeds).
    IC.fade_renown(faction_key)
```

- [ ] **Step 4: Run the harness to verify it passes.**

Run: `luac -p` on the model, then the harness command.
Expected: `iron court harness: ok (901 checks)`. If an older check that pins a packed string or a field count fails, it needs the two new fields. Update its expected value and ledger a `Ruling:`.

- [ ] **Step 5: Commit.** Add a ledger line: `Task 1: complete (harness → N checks ok)`.

---

### Task 2: The deed listeners

**Files:**
- Modify: `zzz_derpy_iron_court.lua`, inside `function IC.register()`:
  - `ic_confed`: stamp `confed_turn`;
  - `ic_battle`: score the battle once per battle;
  - six new listeners after `ic_battle`.
- Test: the harness, after Task 1's checks.

**Interfaces:**
- Consumes: `IC.deed(faction_key, code)`; `court.confed_turn`.
- Produces:
  - `IC.battle_once(faction_key, battle) -> boolean`;
  - `IC.deed_of_ritual(category) -> "hellforge"|"rite"|nil`;
  - `IC.TEMPLE_BUILDINGS[key] = true`;
  - `IC.ENSLAVE_RECORD`, `IC.ENSLAVE_OUTCOME`;
  - listeners `ic_deed_ritual`, `ic_deed_building`, `ic_deed_captives`, `ic_deed_raze`, `ic_deed_convoy`, `ic_deed_research`.

- [ ] **Step 1: Write the failing checks.**

```lua
-- A FAKE CHAOS DWARF FACTION OBJECT for the deed listeners' contexts.
local function deed_faction()
    return cm:get_faction(F)
end

check("deeds: a battle scores once however many of your generals won it", function()
    deed_court({crown = 10, legion = 10})
    local a = make_character(91, ANY_SEAT, "crown")
    local b = make_character(92, ANY_SEAT, "crown")
    make_faction(F, IC.CHD_SUBCULTURE, {a, b}, {})
    a._won, b._won = true, true
    IC.register()
    local battle = fake_battle("heroic_victory", "crushing_defeat")
    battle.has_attacker = function() return true end
    battle.attacker = function() return a end
    battle.has_defender = function() return true end
    battle.defender = function() return make_character(500, ANY_SEAT, "crown") end
    for _, man in ipairs({a, b}) do
        core.listeners["ic_battle"]({character = function() return man end,
                                     pending_battle = function() return battle end})
    end
    assert(IC.renown(F, "legion") == IC.TUNE.deed_battle,
        "two winning generals scored " .. IC.renown(F, "legion"))
    gov_done()
end)

check("deeds: the Hell-Forge, the Tower and the temples each score their party", function()
    local court = deed_court({crown = 10, forge = 10, temple = 10})
    IC.register()
    local function ritual(cat)
        core.listeners["ic_deed_ritual"]({
            performing_faction = deed_faction,
            ritual = function() return {ritual_category = function() return cat end} end})
    end
    ritual("HELLFORGE_CAPS_MELEE_INFANTRY")
    assert(IC.renown(F, "forge") == IC.TUNE.deed_hellforge, "the Hell-Forge scored nothing")
    ritual("DISTRICTS_SORCERY_T2")
    assert(IC.renown(F, "temple") == IC.TUNE.deed_rite, "a Tower rite scored nothing")
    ritual("TOZ_TIER_4")
    assert(IC.renown(F, "temple") == 2 * IC.TUNE.deed_rite, "the fourth tier scored nothing")
    ritual("STANDARD_RITUAL")
    assert(IC.renown(F, "temple") == 2 * IC.TUNE.deed_rite and IC.renown(F, "forge") == IC.TUNE.deed_hellforge,
        "an unrelated ritual scored")
    court.renown, court.renown_got = {}, {}
    core.listeners["ic_deed_building"]({building = function() return {
        name = function() return "wh3_dlc23_chd_tower_temple_of_hashut_1" end,
        faction = deed_faction} end})
    assert(IC.renown(F, "temple") == IC.TUNE.deed_temple, "a temple of Hashut scored nothing")
    core.listeners["ic_deed_building"]({building = function() return {
        name = function() return "wh3_dlc23_chd_tower_temple_guardhouse_1" end,
        faction = deed_faction} end})
    assert(IC.renown(F, "temple") == IC.TUNE.deed_temple, "the guardhouse scored as a temple")
    gov_done()
end)

check("deeds: Tower rites on a confederation turn score nothing", function()
    local court = deed_court({crown = 10, temple = 10})
    court.confed_turn = turn
    IC.register()
    core.listeners["ic_deed_ritual"]({performing_faction = deed_faction,
        ritual = function() return {ritual_category = function() return "DISTRICTS_INDUSTRY_T1" end} end})
    assert(IC.renown(F, "temple") == 0, "a confederation's re-performed rite scored")
    gov_done()
end)

check("deeds: slaves taken and settlements razed score the Chain; recruiting captives does not", function()
    deed_court({crown = 10, chain = 10})
    local man = make_character(93, ANY_SEAT, "crown")
    make_faction(F, IC.CHD_SUBCULTURE, {man}, {})
    IC.register()
    local function captives(outcome, record)
        core.listeners["ic_deed_captives"]({character = function() return man end,
            get_outcome_key = function() return outcome end,
            get_record_key = function() return record end})
    end
    captives("enslave_replenishment_only", "wh3_dlc23_captive_option_recruit_chaos_dwarfs")
    assert(IC.renown(F, "chain") == 0, "recruiting captives scored")
    captives("enslave_slaves_only", "wh3_dlc23_captive_option_enslave_chaos_dwarfs")
    assert(IC.renown(F, "chain") == IC.TUNE.deed_slaves, "enslaving scored nothing")
    core.listeners["ic_deed_raze"]({character = function() return man end})
    assert(IC.renown(F, "chain") == IC.TUNE.deed_slaves + IC.TUNE.deed_raze, "razing scored nothing")
    gov_done()
end)

check("deeds: a convoy and a technology score the Road and the Tower", function()
    deed_court({crown = 10, road = 10, tower = 10})
    IC.register()
    core.listeners["ic_deed_convoy"]({faction = deed_faction})
    core.listeners["ic_deed_research"]({faction = deed_faction})
    assert(IC.renown(F, "road") == IC.TUNE.deed_convoy, "a convoy scored nothing")
    assert(IC.renown(F, "tower") == IC.TUNE.deed_research, "research scored nothing")
    gov_done()
end)

check("deeds: a battle in the enemy's turn still scores", function()
    local court = deed_court({crown = 10, legion = 10})
    local man = make_character(94, ANY_SEAT, "crown")
    make_faction(F, IC.CHD_SUBCULTURE, {man}, {})
    man._won = true
    IC.register()
    core.listeners["ic_battle"]({character = function() return man end,
        pending_battle = function() return fake_battle("crushing_defeat", "close_victory") end})
    assert(IC.renown(F, "legion") == IC.TUNE.deed_battle, "a defence scored nothing")
    gov_done()
end)

check("deeds: a confederation stamps the turn it happened", function()
    local court = deed_court({crown = 10})
    IC.register()
    pcall(core.listeners["ic_confed"], {confederation = deed_faction,
        faction = function() return make_faction("wh3_dlc23_chd_legion_of_azgorh",
                                                  IC.CHD_SUBCULTURE, {}, {}) end})
    assert(IC.court(F).confed_turn == turn, "confed_turn " .. tostring(IC.court(F).confed_turn))
    gov_done()
end)
```

- [ ] **Step 2: Run the harness to verify they fail.**

Expected: FAIL on the seven new checks. `ic_deed_ritual` and the other new listeners are nil, so calling them errors. The battle check reports 0 renown, and the confederation check reports `confed_turn 0`.

- [ ] **Step 3: Write the listeners.**

Before `function IC.register()`, add:

```lua
-- THE DEEDS' DISCRIMINATORS (spec 2026-10-02 deeds section 2). Keys read out of
-- CA's db 2026-10-02: the guardhouse chain is military and is not a temple, and
-- recruiting captives (enslave_replenishment_only) is not taking slaves.
IC.TEMPLE_BUILDINGS = {
    wh3_dlc23_chd_tower_temple_of_hashut_1 = true,
    wh3_dlc23_special_great_temple_of_hashut_chd = true,
}
IC.ENSLAVE_RECORD = "wh3_dlc23_captive_option_enslave_chaos_dwarfs"
IC.ENSLAVE_OUTCOME = "enslave_slaves_only"

function IC.deed_of_ritual(category)
    category = tostring(category or "")
    if string.find(category, "HELLFORGE_CAPS", 1, true) then return "hellforge" end
    if string.find(category, "DISTRICTS_", 1, true) == 1 or category == "TOZ_TIER_4" then
        return "rite"
    end
    return nil
end

-- ONCE PER BATTLE: CharacterCompletedBattle fires for every character in it.
-- Keyed on the two commanders; a battle the interface cannot name scores.
IC.battles_seen, IC.battles_turn = {}, nil
function IC.battle_once(faction_key, battle)
    local now = cm:model():turn_number()
    if IC.battles_turn ~= now then IC.battles_seen, IC.battles_turn = {}, now end
    local a, d
    pcall(function()
        if battle:has_attacker() then a = battle:attacker():command_queue_index() end
        if battle:has_defender() then d = battle:defender():command_queue_index() end
    end)
    if not a and not d then return true end
    local key = faction_key .. ":" .. tostring(a) .. ":" .. tostring(d)
    if IC.battles_seen[key] then return false end
    IC.battles_seen[key] = true
    return true
end
```

In `ic_confed`, right after `if not IC.runs_court(host) then return end` and before the `origin_for_faction` early return, because CA re-performs the joiner's seats whatever its origin:

```lua
        -- CA RE-PERFORMS THE JOINER'S TOWER SEATS THIS TURN: no deed for them.
        IC.loaded(host:name())
        IC.court(host:name()).confed_turn = cm:model():turn_number()
```

In `ic_battle`, after `IC.add_standing(faction_key, character:command_queue_index(), gain)`:

```lua
        if IC.battle_once(faction_key, battle) and IC.deed(faction_key, "battle") > 0 then
            IC.save(faction_key)
        end
```

After the `ic_battle` listener's closing `end, true)`, add:

```lua
    -- THE DEEDS (spec 2026-10-02 deeds). Each reads its faction and its deed,
    -- or nothing; a failure is said and drops nothing else.
    local function on_deed(name, event, read)
        core:add_listener(name, event, true, function(context)
            local ok, err = pcall(function()
                local faction, code = read(context)
                if not faction or faction:is_null_interface() or not code then return end
                if not IC.runs_court(faction) then return end
                local faction_key = faction:name()
                IC.loaded(faction_key)
                if IC.deed(faction_key, code) > 0 then IC.save(faction_key) end
            end)
            if not ok then IC.warn("IRON COURT: " .. name .. " failed: " .. tostring(err)) end
        end, true)
    end
    on_deed("ic_deed_ritual", "RitualCompletedEvent", function(context)
        local faction = context:performing_faction()
        IC.loaded(faction:name())
        local code = IC.deed_of_ritual(context:ritual():ritual_category())
        if code == "rite" and IC.court(faction:name()).confed_turn
                == cm:model():turn_number() then
            return nil
        end
        return faction, code
    end)
    on_deed("ic_deed_building", "BuildingCompleted", function(context)
        local building = context:building()
        return building:faction(), IC.TEMPLE_BUILDINGS[building:name()] and "temple" or nil
    end)
    on_deed("ic_deed_captives", "CharacterPostBattleCaptureOption", function(context)
        local yes = context:get_outcome_key() == IC.ENSLAVE_OUTCOME
                    or context:get_record_key() == IC.ENSLAVE_RECORD
        return context:character():faction(), yes and "slaves" or nil
    end)
    on_deed("ic_deed_raze", "CharacterRazedSettlement", function(context)
        return context:character():faction(), "raze"
    end)
    -- NOT ScriptEventCaravanCompleted too: CA re-raises this same context.
    on_deed("ic_deed_convoy", "CaravanCompleted", function(context)
        return context:faction(), "convoy"
    end)
    on_deed("ic_deed_research", "ResearchCompleted", function(context)
        return context:faction(), "research"
    end)
```

- [ ] **Step 4: Run.** Run `luac -p`, then the harness. Expected: `ok (908 checks)`. Then run `py tools/check_lua_api.py "Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua"`. Expected: `0 suspect call(s)`. `check_lua_api` covers `cm:`/`core:` only, so the context methods are not checked; Task 7 owes them in game.

- [ ] **Step 5: Commit.** Add a ledger line.

---

### Task 3: The party drawn in

**Files:**
- Modify: `zzz_derpy_iron_court.lua`:
  - `IC.EVENTS`: append `party_drawn`;
  - add `IC.deed_waiting` and `IC.deed_join` after `IC.background_for`;
  - the `ic_born` listener.
- Modify: `tools/gen_iron_court.py`:
  - `EVENTS`: append `party_drawn` after `gov_pressure`;
  - a new `PARTY_DRAWN` dict;
  - its loc in the event loop's file section, next to the existing event loc emission (after the `for ... in EVENTS` loop that appends the `_secondary` loc).
- Test: the harness.

**Interfaces:**
- Consumes: `IC.renown`, `IC.deeds_on`, `IC.add_house(faction_key, slug)`, `IC.name_party`, `IC.roll_party_traits`, `IC.can_lead`, `IC.fixed_history`, `IC.bg_of_character`, `IC.BACKGROUNDS`.
- Produces:
  - `IC.deed_waiting(faction_key) -> party slug|nil`;
  - `IC.deed_room(faction_key) -> boolean`;
  - `IC.deed_join(character, faction_key) -> background slug|nil`;
  - event `party_drawn` (2632);
  - loc `event_feed_strings_text_derpy_ic_event_party_drawn_<party>` for `legion, forge, temple, chain, road, ledger, tower`.

Ruling, recorded now: the spec says an empty party "is removed by the existing orphan sweep". That sweep (`IC.prune_confed`) only removes confederation origins. Rival parties may exist empty. The spec's requirement still holds by construction, because the party is added only in the same call that gives the recruit its background. If this is wrong it costs nothing: an empty drawn party is impossible either way.

- [ ] **Step 1: Write the failing checks.**

```lua
check("deeds: an absent party at the line takes the next ordinary lord", function()
    local court = deed_court({crown = 10})
    court.renown.legion = IC.TUNE.renown_join_line
    local lord = make_character(95, ANY_SEAT, nil)
    make_faction(F, IC.CHD_SUBCULTURE, {lord}, {})
    local bg = IC.deed_join(lord, F)
    assert(bg and IC.PARTY_OF_BG[bg] == "legion", "the lord was given " .. tostring(bg))
    assert(court.houses.legion and court.houses.legion.head, "the Legion did not enter, named")
    assert(IC.renown(F, "legion") == IC.TUNE.renown_join_line, "its renown did not come with it")
    gov_done()
end)

check("deeds: a legend or a lord with a history is not drawn", function()
    local court = deed_court({crown = 10})
    court.renown.legion = IC.TUNE.renown_join_line
    local saved_lead, saved_fixed = IC.can_lead, IC.fixed_history
    IC.can_lead = function() return false end
    assert(IC.deed_join(make_character(96, ANY_SEAT, nil), F) == nil and not court.houses.legion,
        "a man who cannot lead was drawn")
    IC.can_lead = function() return true end
    IC.fixed_history = function() return {origin = "x"} end
    assert(IC.deed_join(make_character(97, ANY_SEAT, nil), F) == nil and not court.houses.legion,
        "a lord with a fixed history was drawn")
    IC.can_lead, IC.fixed_history = saved_lead, saved_fixed
    gov_done()
end)

check("deeds: a full court holds the absent party at the line", function()
    local weights = {crown = 10}
    local n = 0
    for _, p in ipairs({"forge", "temple", "chain", "road", "ledger", "tower", "hearth"}) do
        if n < IC.TUNE.rivals_max then weights[p] = 10; n = n + 1 end
    end
    local court = deed_court(weights)
    court.renown.legion = IC.TUNE.renown_join_line
    assert(IC.deed_waiting(F) == nil, "a full court still called the Legion in")
    assert(IC.deed_room(F) == false, "a full court reads as having room")
    gov_done()
end)

check("deeds: of two parties at the line the one with more renown comes first", function()
    local court = deed_court({crown = 10})
    court.renown.legion = IC.TUNE.renown_join_line
    court.renown.forge = IC.TUNE.renown_join_line + 5
    assert(IC.deed_waiting(F) == "forge", "waiting: " .. tostring(IC.deed_waiting(F)))
    gov_done()
end)

check("deeds: a party drawn in and then gone stops at the line again", function()
    local court = deed_court({crown = 10, legion = 10})
    court.renown.legion = 40
    IC.remove_house(F, "legion")
    court.renown_got = {}
    assert(IC.deed(F, "battle") == 0, "a gone party above the line still gained")
    gov_done()
end)

check("deeds: a lord created while a party waits joins it through ic_born", function()
    local court = deed_court({crown = 10})
    court.renown.legion = IC.TUNE.renown_join_line
    local lord = make_character(98, ANY_SEAT, nil)
    make_faction(F, IC.CHD_SUBCULTURE, {lord}, {})
    court.rolled = true
    IC.register()
    core.listeners["ic_born"]({character = function() return lord end})
    assert(IC.house_of_character(lord, F) == "legion",
        "the new lord sits with " .. tostring(IC.house_of_character(lord, F)))
    gov_done()
end)
```

- [ ] **Step 2: Run to verify they fail.** Expected: FAIL with `attempt to call field 'deed_join' (a nil value)` or `deed_waiting`. The "gone party" check may already pass, because Task 1's line cap covers it. If it passes before any code change, it is a regression pin for Review Focus 3; ledger that, and keep it.

- [ ] **Step 3: Write the code.**

In `IC.EVENTS`, after `gov_pressure       = {2630, true, true},`:

```lua
    -- DEEDS (spec 2026-10-02 deeds): the introduction, and a party your deeds
    -- drew in (the secondary line names the deed, per party).
    gov_intro          = {2631, true, true},
    party_drawn        = {2632, true, true},
```

Task 3 adds both events, `gov_intro` included, so the position-derived indices stay aligned. Task 4 only raises `gov_intro`.

After `function IC.background_for ... end`, add:

```lua
-- ROOM FOR ONE MORE: fewer rival parties than rivals_max (spec 2026-10-02
-- deeds section 3).
function IC.deed_room(faction_key)
    local court, rivals = IC.court(faction_key), 0
    for i = 1, #IC.PARTIES do
        local p = IC.PARTIES[i]
        if p ~= IC.CROWN and court.houses[p] then rivals = rivals + 1 end
    end
    return rivals < IC.TUNE.rivals_max
end

-- THE ABSENT PARTY AT THE JOIN LINE with the most renown; IC.PARTIES order
-- breaks a tie.
function IC.deed_waiting(faction_key)
    if not IC.deeds_on(faction_key) or not IC.deed_room(faction_key) then return nil end
    local court = IC.court(faction_key)
    local best, most = nil, 0
    for i = 1, #IC.PARTIES do
        local p = IC.PARTIES[i]
        local n = IC.renown(faction_key, p)
        if p ~= IC.CROWN and not court.houses[p] and IC.BACKGROUNDS[p]
           and n >= IC.TUNE.renown_join_line and n > most then
            best, most = p, n
        end
    end
    return best
end

-- A NEW LORD WHO CAN SPEAK FOR A PARTY, with no history of his own, joins the
-- waiting party; it enters in the same call, so it never stands empty.
function IC.deed_join(character, faction_key)
    if not IC.can_lead(character) or IC.fixed_history(character) then return nil end
    if IC.bg_of_character(character) then return nil end
    local party = IC.deed_waiting(faction_key)
    if not party or not IC.add_house(faction_key, party) then return nil end
    IC.name_party(faction_key, party)
    IC.roll_party_traits(faction_key, party)
    IC.log(faction_key, "drawn", party, nil, IC.renown(faction_key, party))
    IC.feed(faction_key, "party_drawn",
            "event_feed_strings_text_derpy_ic_event_party_drawn_" .. party)
    IC.save(faction_key)
    local list = IC.BACKGROUNDS[party]
    return list[cm:random_number(#list, 1)]
end
```

In `ic_born`, replace:

```lua
            IC.stamp_bg(character, IC.background_for(character, faction_key))
```

with:

```lua
            IC.stamp_bg(character, IC.deed_join(character, faction_key)
                                   or IC.background_for(character, faction_key))
```

In `tools/gen_iron_court.py` `EVENTS`, after the `gov_pressure` tuple:

```python
    # DEEDS (spec 2026-10-02 deeds). gov_intro is raised once per player court;
    # party_drawn names its deed in a per-party secondary line (PARTY_DRAWN).
    ("gov_intro", True, "chd/faction", "Neutral",
     "Your Deeds Move the Court",
     "Your court has a government, shown in the Crown's box. What you do moves "
     "it. Victories raise the Legion, the Hell-Forge raises the Daemonsmiths, "
     "the Tower's rites and temples raise the Temple, slaves raise the "
     "Slave-Lords, convoys raise the Road, and research raises the Tower. A "
     "party that grows strong enough asks for its own government.",
     "The Court Watches You"),
    ("party_drawn", True, "chd/faction", "Positive",
     "A Party Comes to Court",
     "Your deeds have drawn a new party into your court, and the next lord you "
     "raised has joined it. It holds weight now, and it will expect seats.",
     "The Court Grows"),
```

After the `EVENTS` list, add:

```python
# THE SECONDARY LINE party_drawn PASSES, one per party a deed can draw in.
PARTY_DRAWN = {
    "legion": "Your victories drew the Legion to court.",
    "forge": "The Hell-Forge's work drew the Daemonsmiths to court.",
    "temple": "The Tower's rites drew the Temple to court.",
    "chain": "Your slave-taking drew the Slave-Lords to court.",
    "road": "Your convoys drew the Road to court.",
    "ledger": "Your convoys drew the Ledger to court.",
    "tower": "Your research drew the Tower to court.",
}
```

Right after the event loop's `_secondary` loc append (the `if secondary is not None:` block that ends the per-event loc), add at the loop's indentation **after** the loop:

```python
    for party, text in sorted(PARTY_DRAWN.items()):
        loc.append({"key": "event_feed_strings_text_derpy_ic_event_party_drawn_" + party,
                    "text": text, "tooltip": "false"})
```

Add one generator check to `check()` (next to `check_governments`), named `check_party_drawn`:

```python
def check_party_drawn():
    """Every party IC.DEEDS can name has a party_drawn line (spec 2026-10-02 deeds)."""
    block = re.search(r"IC\.DEEDS = \{(.*?)\n\}", _model_lua(), re.S)
    named = set(re.findall(r'(?:party|alt) = "(\w+)"', block.group(1))) if block else set()
    missing = sorted(named - set(PARTY_DRAWN))
    return ["party_drawn has no line for %s" % p for p in missing] + (
        [] if named else ["the model Lua declares no IC.DEEDS"])
```

Call it wherever `check_governments()` is called, the same way.

- [ ] **Step 4: Run.** Run `luac -p`, then the harness (expected `ok (914 checks)`), then `py tools/gen_iron_court.py --check` and `py tools/gen_iron_court.py --selftest`. Expected: both `ok`, with the loc count up by 2 titles + 2 primaries + 2 secondaries + 7 lines. If the selftest pins an exact loc count, update that formula and ledger a `Ruling:`.

- [ ] **Step 5: Commit.** Add a ledger line.

---

### Task 4: The introduction card

**Files:**
- Modify: `zzz_derpy_iron_court.lua` `IC.gov_step`.
- Test: the harness.

**Interfaces:**
- Consumes: `IC.EVENTS.gov_intro` (Task 3); `court.gov_intro` (Task 1).
- Produces: `court.gov_intro = true` after the first player `gov_step` with governments on.

Ruling, recorded now: the spec says the card fires "when its first government is set". A court that already has a government (the author's current test save) would then never see it. The card fires at the first `gov_step` where the flag is unset, whether or not this is the start. The spec's "once per human court, including an old save" holds. If this is wrong, a court that already had a government sees one extra card.

- [ ] **Step 1: Write the failing checks.**

```lua
check("deeds: the introduction is raised once per player court, an old save included", function()
    local court = deed_court({crown = 10})
    local raised = 0
    local saved_feed = IC.feed
    IC.feed = function(_, slug) if slug == "gov_intro" then raised = raised + 1 end return true end
    court.gov = nil
    IC.gov_step(F)
    IC.gov_step(F)
    assert(raised == 1, "a new court raised the introduction " .. raised .. " times")
    -- A SAVE THAT ALREADY HAD A GOVERNMENT, from before the flag.
    court.gov, court.gov_intro = "conclave", nil
    IC.gov_step(F)
    assert(raised == 2 and court.gov_intro, "a court with a government never saw it")
    -- AN AI COURT never does.
    court.gov_intro = nil
    cm.get_human_factions = function() return {"someone_else"} end
    IC.gov_step(F)
    assert(raised == 2, "an AI court raised the introduction")
    IC.feed = saved_feed
    gov_done()
end)
```

- [ ] **Step 2: Run to verify it fails.** Expected: FAIL with `a new court raised the introduction 0 times`.

- [ ] **Step 3: Write the code.** In `IC.gov_step`, replace:

```lua
    elseif IC.gov_turn then
        IC.gov_turn(faction_key)
    end
    return IC.apply_gov_bundle(faction_key)
```

with:

```lua
    elseif IC.gov_turn then
        IC.gov_turn(faction_key)
    end
    -- ONCE PER PLAYER COURT, a court that already had a government included
    -- (spec 2026-10-02 deeds section 4).
    if not court.gov_intro and IC.is_human(faction_key) then
        court.gov_intro = true
        IC.feed(faction_key, "gov_intro")
    end
    return IC.apply_gov_bundle(faction_key)
```

- [ ] **Step 4: Run.** Run `luac -p`, then the harness. Expected: `ok (915 checks)`. If an older governments check counts feed calls exactly, give it the new card and ledger a `Ruling:`.

- [ ] **Step 5: Commit.** Add a ledger line.

---

### Task 5: The live switch

**Files:**
- Modify: `zzz_derpy_iron_court.lua`:
  - `IC.TUNE_ORDER`: append `"deeds"`;
  - `IC.LIVE_TUNE`: append `"deeds"`.
- Modify: `Modding Files/pack/script/mct/settings/derpy_iron_court.lua`, `SWITCHES`: add after the `gov_drift` entry.
- Modify: `tools/_iron_court_harness.lua`, the `LIVE` list (around line 21395): append `"deeds"`.
- Test: the harness.

**Interfaces:**
- Consumes: `IC.deeds_on` (already reads `IC.TUNE.deeds`).
- Produces: MCT option `deeds`, live.

- [ ] **Step 1: Write the failing checks.** Append `"deeds"` to the harness `LIVE` list. Then add:

```lua
check("deeds: switched off, no renown is gained, none is drawn in, and what is held fades", function()
    local court = deed_court({crown = 10, legion = 10})
    court.renown.legion, court.renown.forge = 30, IC.TUNE.renown_join_line
    IC.TUNE.deeds = false
    assert(IC.deed(F, "battle") == 0, "switched off, a battle still scored")
    assert(IC.deed_waiting(F) == nil, "switched off, a party was still called in")
    assert(IC.house_weight(F, "legion") >= 30, "switched off, held renown stopped counting")
    IC.fade_renown(F)
    assert(court.renown.legion < 30, "switched off, renown stopped fading")
    IC.TUNE.deeds = true
    gov_done()
end)
```

- [ ] **Step 2: Run to verify it fails.** Expected: the mid-campaign live-switch check fails, because `deeds` is in `LIVE` but not in `IC.LIVE_TUNE` or `TUNE_ORDER`, and so does the MCT-page check. The new check may pass already, since `deeds_on` reads the switch. Ledger that as a pin.

- [ ] **Step 3: Write the wiring.** In `IC.TUNE_ORDER`, change the last line to:

```lua
    "governments", "gov_drift", "gov_pressure_line", "gov_hold_cost", "gov_force_cost",
    "deeds",
```

In `IC.LIVE_TUNE`:

```lua
IC.LIVE_TUNE = {"parties_act", "secession", "pressure", "crown_split",
                "all_cards", "detailed_log", "governments", "gov_drift", "deeds"}
```

In the MCT `SWITCHES`, after the `gov_drift` entry:

```lua
    {"deeds", "Your deeds move the court", "systems",
     "Victories, the Hell-Forge, the Tower's rites, slaves, convoys and research "
     .. "give the matching party renown, which counts toward its share and fades "
     .. "each turn. A party not in your court that earns enough sends the next lord "
     .. "you recruit. Off, nothing new is earned and nobody is drawn in; renown "
     .. "already earned fades away.", true},
```

The comment above `IC.LIVE_TUNE` and the harness `LIVE` comment count the switches ("THE SIX", "eight"). Update their numbers to match.

- [ ] **Step 4: Run.** Run `luac -p` on both Lua files, then the harness (expected `ok (916 checks)`), then `py tools/import_iron_court.py --check`, the gate that refuses a setting nothing reads. If that flag is not this tool's gate flag, read its docstring first: tools/*.py have no `--help`, and an unknown flag can BUILD. Expected: exit 0.

- [ ] **Step 5: Commit.** Add a ledger line.

---

### Task 6: What the player sees

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua`:
  - `ICUI.gov_tip` (around 3982): the moving test becomes `ICUI.gov_moving`, plus the deeds block;
  - `ICUI.draw_gov`: the drift segment;
  - the party card nums tooltip (around 3583): a renown line;
  - the dial crest tooltip (around 3199): a renown line;
  - the Record text (around 4926): `deed`, `drawn`;
  - the Help "Governments" topic (around 5307): two lines.
- Modify: `tools/preview_iron_court.py`: the `ic_gov` demo text (around 1190).
- Test: the harness.

**Interfaces:**
- Consumes: `IC.renown`, `IC.deeds_on`, `IC.deed_room`, `IC.DEEDS`, `IC.TUNE.renown_join_line`, `ICUI.gov_icon`, `ICUI.house_name(slug, faction)`.
- Produces:
  - `ICUI.gov_moving(faction, court) -> boolean`;
  - `ICUI.DEED_TEXT[party]`;
  - `ICUI.deeds_tip(faction, court) -> string|nil`;
  - `ICUI.renown_line(faction, slug) -> string` ("" at 0).

- [ ] **Step 1: Write the failing checks.** Add these after the existing "governments: the Crown's box names the government and its pull" check:

```lua
check("deeds: the government line shows the drift only while the court moves", function()
    local court = deed_court({crown = 10, forge = 60})
    with_fake_panel(function(panel)
        ICUI.view = "court"
        court.gov_toward, court.gov_pressure = nil, 0
        ICUI.refresh()
        local line = panel.children.ic_gov
        assert(not string.find(line.text, ICUI.gov_icon("forge"), 1, true),
            "a settled court shows a drift: " .. line.text)
        court.gov_toward, court.gov_pressure = "forge", 3
        ICUI.refresh()
        assert(string.find(line.text, "[[img:" .. ICUI.gov_icon("forge") .. "]]", 1, true)
               and string.find(line.text, string.format("%d/%d", 3, IC.TUNE.gov_pressure_line), 1, true),
            "a moving court does not show where: " .. line.text)
    end)
    gov_done()
end)

check("deeds: the government tooltip says what moves the court, and who would come", function()
    local court = deed_court({crown = 10, legion = 10})
    court.renown.legion, court.renown.forge = 12, 7
    local tip = ICUI.gov_tip(F, court)
    assert(string.find(tip, ICUI.DEED_TEXT.legion, 1, true) and string.find(tip, "renown 12", 1, true),
        "the Legion's line is missing: " .. tip)
    assert(string.find(tip, string.format("at %d", IC.TUNE.renown_join_line), 1, true),
        "the absent Forge's line is missing: " .. tip)
    local saved = IC.deed_room
    IC.deed_room = function() return false end
    tip = ICUI.gov_tip(F, court)
    assert(string.find(tip, "your court is full", 1, true), "a full court is not said: " .. tip)
    IC.deed_room = saved
    IC.TUNE.deeds = false
    assert(not string.find(ICUI.gov_tip(F, court), ICUI.DEED_TEXT.legion, 1, true),
        "switched off, the tooltip still promises deeds")
    IC.TUNE.deeds = true
    gov_done()
end)

check("deeds: a party's renown is on its card and its crest", function()
    local court = deed_court({crown = 10, legion = 10})
    court.renown.legion = 9
    assert(string.find(ICUI.renown_line(F, "legion"), "9", 1, true), "no renown line")
    assert(ICUI.renown_line(F, "crown") == "", "a party with none shows a line")
    gov_done()
end)

check("deeds: the Record says what a deed and a drawn party did", function()
    local court = deed_court({crown = 10, legion = 10})
    local a = ICUI.log_text and ICUI.log_text(F, {kind = "deed", slug = "legion", key = "battle", n = 6})
    local b = ICUI.log_text and ICUI.log_text(F, {kind = "drawn", slug = "legion", n = 20})
    assert(a and string.find(a, "+6", 1, true), "deed Record line: " .. tostring(a))
    assert(b and b ~= "", "drawn Record line: " .. tostring(b))
    gov_done()
end)
```

Before running, find the Record's text function: `grep -n 'e.kind == "doctrine_force"' -B40 "Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua" | grep -n "^.*function ICUI"`. If it is not `ICUI.log_text(faction, e)`, change the two calls above to the real name and signature, and ledger a `Ruling:`.

- [ ] **Step 2: Run to verify they fail.** Expected: FAIL on the four checks: `DEED_TEXT` nil, `renown_line` nil, no drift segment, and the Record falling through to its default.

- [ ] **Step 3: Write the panel code.** In `ICUI.gov_tip`, replace the `if court.gov_toward and ... end` block with:

```lua
    if ICUI.gov_moving(faction, court) then
        local _, top = IC.gov_pull(faction)
        local per = top and 1 or IC.TUNE.gov_balance_turns
        lines[#lines + 1] = string.format("The court leans toward %s. If nothing "
            .. "changes, it asks for it in %d turns.", ICUI.gov_name(court.gov_toward),
            math.max(0, IC.TUNE.gov_pressure_line - court.gov_pressure) * per)
    end
    local deeds = ICUI.deeds_tip(faction, court)
    if deeds then lines[#lines + 1] = deeds end
```

Above `function ICUI.gov_tip`, add:

```lua
-- MOVING: pressure building toward the government the court still pulls to.
function ICUI.gov_moving(faction, court)
    local now = cm:model():turn_number()
    local want = IC.gov_pull(faction)
    return court.gov_toward ~= nil and (court.gov_pressure or 0) > 0 and not court.gov_ask
       and want == court.gov_toward and IC.gov_drift_on(faction)
       and now >= (court.gov_cool or 0)
end

-- WHAT EACH PARTY GROWS ON (spec 2026-10-02 deeds section 4).
ICUI.DEED_TEXT = {
    legion = "your victories",
    forge  = "the Hell-Forge's rituals",
    temple = "the Tower's rites and temples of Hashut",
    chain  = "slaves taken and settlements razed",
    road   = "convoys",
    ledger = "convoys, when there is no Road",
    tower  = "research",
}

function ICUI.deeds_tip(faction, court)
    if not IC.deeds_on(faction) then return nil end
    local here, away = {}, {}
    for _, p in ipairs(IC.PARTIES) do
        local text, n = ICUI.DEED_TEXT[p], IC.renown(faction, p)
        if text and court.houses[p] then
            here[#here + 1] = string.format("%s - %s - renown %d",
                                            ICUI.house_name(p, faction), text, n)
        elseif text and n > 0 then
            away[#away + 1] = IC.deed_room(faction)
                and string.format("%s would come at %d renown (now %d).",
                                  ICUI.party_label(p), IC.TUNE.renown_join_line, n)
                or string.format("%s would come, but your court is full.",
                                 ICUI.party_label(p))
        end
    end
    local out = {"What moves your court:"}
    for _, l in ipairs(here) do out[#out + 1] = l end
    for _, l in ipairs(away) do out[#out + 1] = l end
    return table.concat(out, "\n")
end

-- AN ABSENT PARTY HAS NO HOUSE NAME YET: the generic label.
ICUI.PARTY_LABEL = {legion = "The Legion", forge = "The Forge", temple = "The Temple",
                    chain = "The Chain", road = "The Road", ledger = "The Ledger",
                    tower = "The Tower"}
function ICUI.party_label(p) return ICUI.PARTY_LABEL[p] or tostring(p) end

function ICUI.renown_line(faction, slug)
    local n = IC.renown(faction, slug)
    if n <= 0 then return "" end
    return string.format("Renown from your deeds: %d. It fades each turn.", n)
end
```

Before using `ICUI.PARTY_LABEL`, grep the UI and parties files for an existing generic party label (`grep -n '"The Legion"\|PARTY_NAME\|party_label' "Modding Files/pack/script/campaign/mod/"*.lua`). If one exists, use it instead and delete `ICUI.PARTY_LABEL` (audit-before-adding rule).

In `ICUI.draw_gov`, replace:

```lua
    set_text(line, string.format("[[img:%s]][[/img]]Government: %s", ICUI.gov_icon(court.gov),
                                 ICUI.gov_name(court.gov)))
```

with:

```lua
    local text = string.format("[[img:%s]][[/img]]Government: %s", ICUI.gov_icon(court.gov),
                               ICUI.gov_name(court.gov))
    -- WHERE IT IS GOING, only while it goes (spec 2026-10-02 deeds section 4).
    if ICUI.gov_moving(faction, court) then
        text = text .. string.format("  ->  [[img:%s]][[/img]]%d/%d", ICUI.gov_icon(court.gov_toward),
                                     court.gov_pressure, IC.TUNE.gov_pressure_line)
    end
    set_text(line, text)
```

`gen_ic_ui`'s inline-icon sweep reads one line at a time, so each `[[img:%s]]` must share its line with `ICUI.gov_icon(`, as above.

At the party card, change `nums:SetTooltipText(ICUI.loyalty_tip(faction, court, slug) .. since, "", true)` to:

```lua
            local renown = ICUI.renown_line(faction, slug)
            nums:SetTooltipText(ICUI.loyalty_tip(faction, court, slug) .. since
                .. (renown ~= "" and ("\n\n" .. renown) or ""), "", true)
```

At the dial crest, change the `string.format("%s\n%d%% influence, %d loyalty - %s", ...)` call to append the line:

```lua
            local renown = ICUI.renown_line(faction, slug)
            crest:SetTooltipText(string.format("%s\n%d%% influence, %d loyalty - %s",
                                               name, math.floor(share + 0.5),
                                               house.loyalty or 0,
                                               ICUI.mood(house, slug))
                                 .. (renown ~= "" and ("\n" .. renown) or ""),
                                 "", true)
```

In the Record text, after the `doctrine_lapse` branch, add:

```lua
    elseif e.kind == "deed" then
        return string.format("%s grew on %s: +%d renown.", house,
                             ICUI.DEED_TEXT[e.slug or ""] or "your deeds", e.n or 0)
    elseif e.kind == "drawn" then
        return string.format("Your deeds drew %s into the court.", house)
```

Here `house` is the local the surrounding branches already use for the entry's party name.

In the Help "Governments" topic, after the `Change Doctrine` line, add:

```lua
        "{@party}What you do moves your parties. Victories raise the Legion, the Hell-Forge the Forge, the Tower's rites and temples the Temple, slaves and razing the Chain, convoys the Road, and research the Tower. Renown counts toward a party's share and fades each turn.",
        "{@bullet}A party not in your court that earns {renown_join_line} renown sends the next lord you recruit, if your court has room.",
```

In `tools/preview_iron_court.py`, change the `ic_gov` demo to the longest form the line can take:

```python
        "ic_gov": ("[[img:%s]][[/img]]Government: %s  ->  [[img:%s]][[/img]]%d/%d"
                   % (gov_icons[longest_gov[0]], longest_gov[1],
                      gov_icons["conclave"], 5, 6)),
```

- [ ] **Step 4: Run.**
  - Run `luac -p` on the UI file, then the harness. Expected: `ok (920 checks)`.
  - Then run `py tools/gen_ic_ui.py --check`, `py tools/gen_ic_ui.py --selftest` (slow, about 10 minutes; run it in the background), and `py tools/preview_iron_court.py --check`. Expected: all ok.
  - Then render `py tools/preview_iron_court.py` and crop the Crown's box from `.skilltree_cache/ui_preview/ic_court.png` and `ic_court_1600.png`, around y 820-960. View both. The line must not run into Change Doctrine at 1600. If it does, drop `Government: ` from the text only while the drift segment shows. Ledger that as a `Ruling:` and re-render.

- [ ] **Step 5: Commit.** Add a ledger line.

---

### Task 7: Mutants, gates, build, deploy, docs

**Files:**
- Modify: `tools/mutate_iron_court.py`: add `deed:` mutants after the last `gov:` mutant.
- Modify: `docs/sessions/HANDOFF_20261002_IRON_COURT_GOVERNMENTS.md` (a new section 8), `docs/SESSION_INDEX.md` (update the deeds line), `tools/sync_iron_court_repo.py` (list the deeds spec and plan).

- [ ] **Step 1: Add the mutants.** Use the runner's tuple shape `(name, M|U, anchor, replacement)`, with every `"` inside an anchor written `\"`. If a triple-quoted anchor contains a backslash, write the file edit with the Write tool.

```python
    # ---- deeds (2026-10-02) ---------------------------------------------------
    ("deed: renown is not weight", M,
     """        + IC.member_weight(faction_key, slug) + renown""",
     """        + IC.member_weight(faction_key, slug)"""),
    ("deed: renown never fades", M,
     """        local left = n - math.max(1, math.floor(n * IC.TUNE.renown_fade_pct / 100))""",
     """        local left = n"""),
    ("deed: no limit to a turn's renown", M,
     """    n = math.min(n or 0, math.max(0, IC.TUNE.renown_turn_cap - got))""",
     """    n = n or 0"""),
    ("deed: an absent party banks past the line", M,
     """    if not court.houses[party] then
        n = math.min(n, math.max(0, IC.TUNE.renown_join_line - have))""",
     """    if false then
        n = math.min(n, math.max(0, IC.TUNE.renown_join_line - have))"""),
    ("deed: the Ledger never takes a convoy", M,
     """    if d.alt and not court.houses[party] and court.houses[d.alt] then party = d.alt end""",
     """"""),
    ("deed: AI courts score", M,
     """    return IC.TUNE.deeds ~= false and IC.is_human(faction_key)""",
     """    return IC.TUNE.deeds ~= false"""),
    ("deed: a battle scores per general", M,
     """    if IC.battles_seen[key] then return false end""",
     """"""),
    ("deed: a confederation's rites score", M,
     """        if code == \"rite\" and IC.court(faction:name()).confed_turn""",
     """        if false and IC.court(faction:name()).confed_turn"""),
    ("deed: recruiting captives counts as slaves", M,
     """        local yes = context:get_outcome_key() == IC.ENSLAVE_OUTCOME""",
     """        local yes = true or context:get_outcome_key() == IC.ENSLAVE_OUTCOME"""),
    ("deed: a full court still draws a party", M,
     """    if not IC.deeds_on(faction_key) or not IC.deed_room(faction_key) then return nil end""",
     """    if not IC.deeds_on(faction_key) then return nil end"""),
    ("deed: the smaller waiting party comes first", M,
     """           and n >= IC.TUNE.renown_join_line and n > most then""",
     """           and n >= IC.TUNE.renown_join_line and most == 0 then"""),
    ("deed: a legend is drawn", M,
     """    if not IC.can_lead(character) or IC.fixed_history(character) then return nil end""",
     """    if IC.fixed_history(character) then return nil end"""),
    ("deed: the introduction every turn", M,
     """        court.gov_intro = true
        IC.feed(faction_key, \"gov_intro\")""",
     """        IC.feed(faction_key, \"gov_intro\")"""),
    ("deed: the Record gets an entry per deed", M,
     """    if last and last.kind == \"deed\" and last.slug == party and last.key == code""",
     """    if false and last.kind == \"deed\" and last.slug == party and last.key == code"""),
    ("deed: a settled court shows a drift", U,
     """    if ICUI.gov_moving(faction, court) then
        text = text""",
     """    if true then
        text = text"""),
```

- [ ] **Step 2: Run the mutants.** Run `py tools/mutate_iron_court.py "deed:" > .superpowers/sdd/2026-10-02-iron-court-deeds/mut.log 2>&1; tail -3 .superpowers/sdd/2026-10-02-iron-court-deeds/mut.log`. Expected: `15 mutants, 0 unexplained`.
  - A survivor means the harness check meant to catch it does not measure it. Strengthen that check until the mutant is caught; never delete the mutant.
  - A `STALE ANCHOR` means the anchor and the shipped Lua differ. Re-aim it.
  - Then run `py tools/mutate_iron_court.py "gov:"` (37 mutants), because Task 6 moved `gov_tip` lines that some `gov:` anchors target. Re-aim any that went stale.

- [ ] **Step 3: Run every gate.**
  - `luac -p` on all four court Lua files and the MCT file.
  - `py tools/check_lua_api.py` on the model and the UI.
  - `py tools/check_lua_literal_left.py`.
  - `py tools/check_lua_undeclared.py` (compare against its pre-change output in the governments ledger).
  - `py tools/gen_iron_court.py --check` and `--selftest`.
  - `py tools/gen_ic_ui.py --check` (the selftest already ran in Task 6).
  - `py tools/preview_iron_court.py --check`.
  - The harness.

  Expected: all clean.

- [ ] **Step 4: Regenerate, build and deploy.**
  - Run `py tools/gen_iron_court.py`, then `py tools/gen_ic_ui.py`.
  - Check RPFM is open: `Invoke-WebRequest http://127.0.0.1:45127/sessions -TimeoutSec 4 -UseBasicParsing`. If it is closed, say so and stop.
  - Check the game: `tasklist //FI "IMAGENAME eq Warhammer3.exe"`.
    - Shut: run `py tools/deploy_iron_court.py`.
    - Running: run it in the background with `--wait`.
  - Expected: `verified N file(s) in the saved pack` and `deployed ... byte-identical`.
  - Then read the deployed pack back with `tools/read_pack_index.read`. The model Lua must contain `IC.DEEDS`, the UI Lua `ICUI.deeds_tip`, and the MCT file `"deeds"`.
  - The Iron Court has no Workshop folder, so there is no Workshop copy to make.

- [ ] **Step 5: Docs.** Write a new handoff section `## 8. Deeds move the court (2026-10-02, later)`. It covers:
  - what was built;
  - the rulings from the ledger;
  - the harness and mutant counts;
  - what is owed in game:
    - the captive outcome key;
    - `ResearchCompleted` firing for the player;
    - a convoy counting once;
    - the intro card;
    - a party drawn in by a recruit;
    - the drift segment at the player's resolution;
    - the switch flipped.

  Update the deeds line in `docs/SESSION_INDEX.md` from "SPEC only" to built, pointing at the handoff section. Add the deeds spec and plan paths to `tools/sync_iron_court_repo.py`'s file list, next to the governments spec and plan. Do not commit or push the repo.

- [ ] **Step 6: Commit.** Add a ledger line for Task 7.
