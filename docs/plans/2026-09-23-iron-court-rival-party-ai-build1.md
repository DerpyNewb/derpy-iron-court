# Iron Court Rival Party AI - Build 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rival parties in the player's Iron Court act on their own, at most one court event a
turn. Build 1 covers intrigue against the player (warned for serious moves), feuds between
parties, and passive experience for governors, all shown on the party card's mood button.

**Architecture:** A new file, `zzz_derpy_iron_court_parties.lua`, loads after the model and
before the panel.
- It holds a motive table (`IC.PARTY_ACTS`), a chooser (`IC.party_turn`), and its own saved
  value (`derpy_ic_agenda_<faction>`) for the pending warned move and the feuds.
- The model gains one hook line in `IC.turn`, six `IC.EVENTS` entries and six `IC.LOG_KINDS`.
- The panel shows the agenda on the mood button and in its tooltip.

**Tech Stack:** Lua 5.1.5 (game runtime), stock-Lua harness `tools/_iron_court_harness.lua`,
Python generators `tools/gen_iron_court.py` / `tools/gen_ic_ui.py`, mutation runner
`tools/mutate_iron_court.py`, deploy `tools/deploy_iron_court.py` (needs RPFM open, game
closed).

**Spec:** `docs/superpowers/specs/2026-09-23-iron-court-rival-party-ai-design.md`

## Global Constraints

- Player court only: `IC.party_turn` returns at once when `not IC.is_human(faction_key)`.
- At most one court event per turn. A warned move landing, or being dropped, takes that
  turn's slot. Feud endings and governor experience are upkeep, not events.
- Party moves reuse the player's costs and odds: `IC.plot_cost(key)`, `IC.TUNE.plot_chance_<key>`,
  `plot_chance_per_10`, `plot_chance_min`, `plot_chance_max`.
- Loyalty lines: rumour and discredit at 55 or below, unseat and recall at 25 or below, murder
  at 10 or below. Unseat, recall and murder are warned one turn ahead.
- Murder never targets a legendary lord (`IC.is_legend`) or the faction leader.
- A feud murder runs at a quarter of the base odds, only once the feud is 5 or more turns old.
- Governor experience is 750 raw points a turn (`cm:add_agent_experience(lookup, 750)`), with
  no `by_level`.
- **No emojis.** Never the word "rung". Player text says party, influence, office, overseer.
- Anchor mutants on code lines, never comment lines.
- Never diff, build or deploy while `mutate_iron_court.py` is running: it writes mutants
  into the shipped Lua.
- The workspace is not a git repo. There are no commit steps; the checkpoint after each task is
  the harness run.
- Lua is checked with `& "C:\Program Files (x86)\Lua\5.1\luac.exe" -p <file>` and run with
  `& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua` from the workspace
  root.

**Deviations from the spec,** forced by what the code turned out to be. Tell the author at
handoff.
1. **No new `ic_party_agenda` line.** `PARTY_H` is derived from the panel (3 rows of cards), and
   the card is full: `ic_party_t2` ends at y=208 and `ic_party_off` starts at y=210. The agenda
   shows as the mood button's word (`SCHEMING`, `FEUDING`) and as the first paragraph of its
   tooltip, which names the target.
2. **Feud state lives in the agenda saved value,** not in court fields 17-19, so `IC.pack` and
   `IC.unpack` stay untouched.
3. **No roster marker.** The target is named in the mood tooltip. The event card cannot name
   him, because it is loc-keyed.
4. **Event indices by build.** Build 1 appends six events at 2612-2617. Build 2 appends its own
   after them.
5. **A feud rest.** After a feud ends, both parties wait `party_feud_rest` (5) turns before a new
   one. Without it, two equal parties re-feud the turn a feud expires.

---

## File map

| File | Change |
|---|---|
| `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_parties.lua` | **Create.** Knobs, agenda save and load, the chooser, intrigue, warned moves, feuds, governor experience |
| `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua` | Hook line in `IC.turn`; 6 `IC.EVENTS`; 6 `IC.LOG_KINDS` |
| `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua` | `ICUI.card_mood`, `ICUI.agenda_tip`, 6 `intrigue_text` branches, the card draw calls them |
| `tools/_iron_court_harness.lua` | Load the new file after the model; `party_court` fixture; checks |
| `tools/mutate_iron_court.py` | `P` target; mutants |
| `tools/gen_iron_court.py` | 6 `EVENTS` tuples (cards and loc) |
| `tools/gen_ic_ui.py` | Mood fixture strings `SCHEMING`, `FEUDING` |
| `tools/deploy_iron_court.py`, `tools/import_iron_court.py` | Ship and gate the new file |

---

### Task 1: Wire the new file, its saved value, events and log kinds

**Files:**
- Create: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_parties.lua`
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua` (the `IC.LOG_KINDS`
  table near line 523, the `IC.EVENTS` table near line 552, `IC.turn` near line 3590)
- Modify: `tools/_iron_court_harness.lua` (after the model `chunk()` near line 842)
- Modify: `tools/mutate_iron_court.py:40-41`, `tools/deploy_iron_court.py:50-55`,
  `tools/import_iron_court.py:20-22`
- Modify: `tools/gen_iron_court.py` (append to `EVENTS` after the `"dissolved"` tuple)

**Interfaces:**
- Produces:
  - `IC.agenda(faction_key) -> {plot = nil|{slug, move, actor, target, key, turn}, feuds = {[slug] = rec}, calm = {[slug] = turn}}`
    where `rec = {a, b, cause, key, since, ends}` and `feuds[rec.a] == feuds[rec.b] == rec`;
  - `IC.save_agenda(faction_key)`;
  - `IC.agenda_state` (table, reset by tests);
  - `IC.party_turn(faction_key) -> nil|string`;
  - `IC.PARTY_ACTS` (array);
  - the `IC.TUNE.party_*` knobs and `IC.TUNE.governor_xp`.

- [ ] **Step 1: Write the failing checks**

Add these after the last `check(...)` in `tools/_iron_court_harness.lua`, before the final
summary block. The `party_court` fixture is also used by Tasks 2-6.

```lua
-- A PLAYER COURT OF THREE: the Crown (a rich man 301 and a poor one 302), legion
-- (311) and forge (321). Weights differ so no two rivals are equal unless a
-- check says so, and every man holds 1000 influence except the Crown's two.
local function party_court(loyalty)
    IC.state = {}
    IC.agenda_state = {}
    saved["derpy_ic_" .. F] = nil
    saved["derpy_ic_agenda_" .. F] = nil
    turn = 10
    rng(nil)
    cm.get_human_factions = function() return {F} end
    local men = {
        make_character(301, ANY_SEAT, IC.CROWN),
        make_character(302, ANY_SEAT, IC.CROWN),
        make_character(311, ANY_SEAT, "legion"),
        make_character(321, ANY_SEAT, "forge"),
    }
    local f = make_faction(F, IC.CHD_SUBCULTURE, men, {"prov_a", "prov_b"})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    IC.add_house(F, "forge")
    local court = IC.court(F)
    court.houses["legion"].weight = 20
    court.houses["forge"].weight = 40
    endow(F, 1000)
    court.standing[301] = 800
    court.standing[302] = 100
    for slug, n in pairs(loyalty or {}) do court.houses[slug].loyalty = n end
    shown = {}
    return f, men
end

local function cards_of(slug)
    local n = 0
    for _, s in ipairs(shown) do
        if s.index == IC.EVENTS[slug][1] then n = n + 1 end
    end
    return n
end

check("an AI court's parties never act", function()
    party_court({legion = 5})
    cm.get_human_factions = function() return {} end
    assert(IC.party_turn(F) == nil, "an AI court ran a party event")
    assert(saved["derpy_ic_agenda_" .. F] == nil, "an AI court saved an agenda")
end)

check("a court of loyal parties has a quiet turn", function()
    party_court({legion = 80, forge = 80})
    assert(IC.party_turn(F) == nil, "a loyal court acted")
    assert(#shown == 0, "a quiet turn raised a card")
    cm.get_human_factions = function() return {} end
end)

check("the agenda survives a reload", function()
    party_court({})
    local a = IC.agenda(F)
    a.plot = {slug = "legion", move = "unseat", actor = 311, target = 301,
              key = "muster", turn = 10}
    local rec = {a = "legion", b = "forge", cause = "seat", key = "banners",
                 since = 8, ends = 18}
    a.feuds.legion, a.feuds.forge = rec, rec
    a.calm.chain = 14
    IC.save_agenda(F)
    IC.agenda_state = {}
    local b = IC.agenda(F)
    assert(b.plot and b.plot.move == "unseat" and b.plot.target == 301
           and b.plot.key == "muster", "the warned move was lost")
    assert(b.feuds.legion and b.feuds.legion == b.feuds.forge,
           "a feud reloaded as two records, or none")
    assert(b.feuds.forge.ends == 18 and b.feuds.forge.key == "banners",
           "the feud's end or seat was lost")
    assert(b.calm.chain == 14, "a party's rest was lost")
    cm.get_human_factions = function() return {} end
end)

check("every turn gives the parties their turn", function()
    party_court({})
    local called, real = 0, IC.party_turn
    IC.party_turn = function() called = called + 1 end
    IC.turn(F)
    IC.party_turn = real
    assert(called == 1, "IC.turn ran the parties " .. called .. " times")
    cm.get_human_factions = function() return {} end
end)
```

- [ ] **Step 2: Run the harness to see it fail**

Run: `& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua`
Expected: `FAIL an AI court's parties never act: ... attempt to call field 'party_turn' (a nil value)`

- [ ] **Step 3: Create the new file with knobs, the agenda and an empty chooser**

Create `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_parties.lua`:

```lua
-- Rival parties that act on their own: at most one court event a turn, in the
-- player's court only. Design:
-- docs/superpowers/specs/2026-09-23-iron-court-rival-party-ai-design.md
-- Loads after zzz_derpy_iron_court.lua ("." sorts before "_") and before the
-- panel. Defines functions only: nothing here may touch the campaign at load.

local T = IC.TUNE
T.party_act_floor       = 10   -- a motive below this is no event at all
T.party_intrigue_line   = 55   -- rumour and discredit at or below this loyalty
T.party_feud_turns      = 10
T.party_feud_murder_age = 5
T.party_feud_seat       = 20   -- motive to feud over a stolen seat
T.party_feud_equal_motive = 12 -- motive to feud with an equal
T.party_feud_equal      = 5    -- share points apart that count as equal
T.party_feud_apart      = 10   -- an equals feud ends past this gap
T.party_feud_rest       = 5    -- turns before a party feuds again
T.party_feud_motive     = 15   -- motive for a feuding party's move
T.party_murder_odds_div = 4
T.governor_xp           = 750

IC.agenda_state = {}

local function split(text, sep)
    local out = {}
    if not text or text == "" then return out end
    for piece in string.gmatch(text, "([^" .. sep .. "]+)") do
        out[#out + 1] = piece
    end
    return out
end

-- plot = {slug, move, actor, target, key, turn}: one warned move, court-wide.
-- feuds[slug] = rec for BOTH parties of a pair, rec = {a, b, cause, key, since, ends}.
-- calm[slug] = the turn a party may feud again.
function IC.agenda(faction_key)
    local a = IC.agenda_state[faction_key]
    if a then return a end
    a = {plot = nil, feuds = {}, calm = {}}
    local packed = cm:get_saved_value("derpy_ic_agenda_" .. faction_key)
    if packed and packed ~= "" then
        local parts = {}
        for field in string.gmatch(packed .. "|", "([^|]*)|") do
            parts[#parts + 1] = field
        end
        local p = split(parts[1] or "", ",")
        if #p >= 6 then
            a.plot = {slug = p[1], move = p[2], actor = tonumber(p[3]),
                      target = tonumber(p[4]),
                      key = p[5] ~= "-" and p[5] or nil,
                      turn = tonumber(p[6]) or 0}
        end
        for _, entry in ipairs(split(parts[2] or "", ";")) do
            local b = split(entry, ",")
            if #b >= 6 then
                local rec = {a = b[1], b = b[2], cause = b[3],
                             key = b[4] ~= "-" and b[4] or nil,
                             since = tonumber(b[5]) or 0,
                             ends = tonumber(b[6]) or 0}
                a.feuds[rec.a], a.feuds[rec.b] = rec, rec
            end
        end
        for _, entry in ipairs(split(parts[3] or "", ";")) do
            local b = split(entry, ",")
            if #b >= 2 then a.calm[b[1]] = tonumber(b[2]) end
        end
    end
    IC.agenda_state[faction_key] = a
    return a
end

function IC.save_agenda(faction_key)
    local a = IC.agenda(faction_key)
    local plot = ""
    if a.plot then
        local p = a.plot
        plot = string.format("%s,%s,%d,%d,%s,%d", p.slug, p.move, p.actor,
                             p.target, p.key or "-", p.turn or 0)
    end
    local feuds, calm = {}, {}
    for slug, rec in pairs(a.feuds) do
        if slug == rec.a then
            feuds[#feuds + 1] = string.format("%s,%s,%s,%s,%d,%d", rec.a,
                rec.b, rec.cause, rec.key or "-", rec.since, rec.ends)
        end
    end
    for slug, n in pairs(a.calm) do
        calm[#calm + 1] = slug .. "," .. tostring(n)
    end
    table.sort(feuds)
    table.sort(calm)
    cm:set_saved_value("derpy_ic_agenda_" .. faction_key,
        plot .. "|" .. table.concat(feuds, ";") .. "|"
        .. table.concat(calm, ";"))
end

-- Each entry: {key, can(fk, slug) -> target|nil, motive(fk, slug, target) -> int,
-- act(fk, slug, target)}. Filled by the sections below.
IC.PARTY_ACTS = {}

function IC.party_turn(faction_key)
    if not IC.is_human(faction_key) then return nil end
    local picks = {}
    for _, slug in ipairs(IC.present_houses(faction_key)) do
        if slug ~= IC.CROWN then
            for _, act in ipairs(IC.PARTY_ACTS) do
                local target = act.can(faction_key, slug)
                if target then
                    local m = math.floor(act.motive(faction_key, slug, target))
                    if m >= T.party_act_floor then
                        picks[#picks + 1] = {act = act, slug = slug,
                                             target = target, motive = m}
                    end
                end
            end
        end
    end
    local done = nil
    if #picks > 0 then
        table.sort(picks, function(x, y)
            if x.motive ~= y.motive then return x.motive > y.motive end
            if x.slug ~= y.slug then return x.slug < y.slug end
            return x.act.key < y.act.key
        end)
        local top = math.min(3, #picks)
        local total = 0
        for i = 1, top do total = total + picks[i].motive end
        local roll = cm:random_number(total, 1)
        local chosen = picks[top]
        for i = 1, top do
            roll = roll - picks[i].motive
            if roll <= 0 then chosen = picks[i]; break end
        end
        chosen.act.act(faction_key, chosen.slug, chosen.target)
        done = chosen.act.key
    end
    IC.save_agenda(faction_key)
    IC.save(faction_key)
    return done
end
```

- [ ] **Step 4: Load it in the harness**

In `tools/_iron_court_harness.lua`, directly after `assert(IC, "the file must define IC")`
(near line 842), add:

```lua
local PARTIES_FILE = (arg and arg[3])
    or "Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_parties.lua"
local parties_chunk, parties_err = loadfile(PARTIES_FILE)
assert(parties_chunk, "could not load " .. PARTIES_FILE .. ": " .. tostring(parties_err))
parties_chunk()
assert(IC.party_turn, "the parties file must define IC.party_turn")
```

- [ ] **Step 5: Hook `IC.turn` and add the events and log kinds in the model**

In `zzz_derpy_iron_court.lua`, `IC.turn`, replace:

```lua
    if not IC.feed_held then IC.flush_feed() end
    local warned = IC.tick_secession(faction_key)
```

with:

```lua
    if not IC.feed_held then IC.flush_feed() end
    if IC.party_turn then IC.party_turn(faction_key) end
    local warned = IC.tick_secession(faction_key)
```

In `IC.LOG_KINDS`, replace `    pressed = true, dissolve = true,` with:

```lua
    pressed = true, dissolve = true,
    party_warn = true, party_dropped = true, party_unseat = true,
    party_recall = true, feud = true, feud_end = true,
```

In `IC.EVENTS`, after `    dissolved    = {2611, true, true},` add:

```lua
    party_plot_warn    = {2612, true, true},
    party_plot_ok      = {2613, true, true},
    party_plot_fail    = {2614, true, true},
    party_plot_dropped = {2615, true, true},
    party_feud         = {2616, true, true},
    party_feud_end     = {2617, true, true},
```

- [ ] **Step 6: Add the six cards to the generator**

In `tools/gen_iron_court.py`, append to `EVENTS` after the `"dissolved"` tuple, in this order:

```python
    ("party_plot_warn", True, "chd/army_morale_down", "Negative",
     "A Party Moves Against You",
     "One of the court's parties is preparing to strike at the Crown next turn. "
     "Open the Iron Court: their card names the man and the move, and what "
     "would stop it.",
     "WARNING"),
    ("party_plot_ok", True, "chd/army_morale_down", "Negative",
     "The Court Strikes at the Crown",
     "A party's move against the Crown has landed. The court record says who "
     "did it and what it cost you.",
     "STRUCK"),
    ("party_plot_fail", True, "chd/diplomacy", "Positive",
     "A Plot Is Foiled",
     "A party tried to move against the Crown and failed. What it spent is "
     "gone, and the court record names them.",
     "FOILED"),
    ("party_plot_dropped", True, "chd/diplomacy", "Neutral",
     "A Plot Comes to Nothing",
     "The move a party was preparing against the Crown has fallen apart "
     "before it could land.",
     "ABANDONED"),
    ("party_feud", True, "chd/faction", "Neutral",
     "A Feud in the Court",
     "Two parties have turned on each other. While the feud lasts they strike "
     "at each other rather than at you.",
     "FEUD"),
    ("party_feud_end", True, "chd/faction", "Neutral",
     "A Feud Ends",
     "A feud between two parties is over. Either may turn its attention back "
     "to the Crown.",
     "FEUD OVER"),
```

- [ ] **Step 7: Put the new file in every tool's file list**

- `tools/mutate_iron_court.py`: after `U = os.path.join(MOD, "zzz_derpy_iron_court_ui.lua")` add
  `P = os.path.join(MOD, "zzz_derpy_iron_court_parties.lua")`.
- `tools/deploy_iron_court.py` `SCRIPTS`: add
  ```python
      ("Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_parties.lua",
       "script/campaign/mod/zzz_derpy_iron_court_parties.lua"),
  ```
- `tools/import_iron_court.py`: after `UI_LUA = ...` add
  `PARTIES_LUA = "Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_parties.lua"`
  and change `SCRIPTS = [MODEL_LUA, UI_LUA]` to `SCRIPTS = [MODEL_LUA, UI_LUA, PARTIES_LUA]`.

- [ ] **Step 8: Run everything**

Run:
```powershell
& "C:\Program Files (x86)\Lua\5.1\luac.exe" -p "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court_parties.lua"
& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua
py tools\gen_iron_court.py --check
py tools\gen_iron_court.py --selftest
```

Expected:
- **Harness:** fails only on "every kind the model writes, the panel can describe", because the
  six new log kinds have no sentence yet. Task 6 adds them. Confirm with `$env:IC_TEST_ALL=1`
  that this is the only failure.
- **Generator:** `ok: ... 584 loc rows` (566 + 6 cards x 3 strings).

---

### Task 2: Governors earn experience

**Files:**
- Modify: `zzz_derpy_iron_court_parties.lua`
- Test: `tools/_iron_court_harness.lua`

**Interfaces:**
- Consumes: `party_court`, `lord_levels` (a harness global: `{lookup, level, by_level}` per call).
- Produces: `IC.governor_xp(faction_key) -> int` (governors paid); called first in `IC.party_turn`.

- [ ] **Step 1: Write the failing check**

```lua
check("a governor earns experience every turn, as raw points", function()
    party_court({legion = 80, forge = 80})
    IC.court(F).govs["prov_a"] = 302
    lord_levels = {}
    IC.party_turn(F)
    assert(#lord_levels == 1, #lord_levels .. " experience grants for one governor")
    assert(lord_levels[1].lookup == "cqi:302", "the grant went to "
           .. tostring(lord_levels[1].lookup))
    assert(lord_levels[1].level == IC.TUNE.governor_xp
           and lord_levels[1].by_level ~= true,
           "the grant was not " .. IC.TUNE.governor_xp .. " raw points")
    cm.get_human_factions = function() return {} end
    lord_levels = {}
    IC.party_turn(F)
    assert(#lord_levels == 0, "an AI court's governor was given experience")
end)
```

- [ ] **Step 2: Run and see it fail**

Expected: `FAIL a governor earns experience ...: 0 experience grants for one governor`

- [ ] **Step 3: Implement**

Add above `IC.party_turn` in the parties file:

```lua
-- Rank is half of every office's bar; a governor serves at home and would
-- otherwise never climb. One log line lists every governor's rank, so a
-- garrison commander or pool lord that refuses experience shows as a rank that
-- never moves.
function IC.governor_xp(faction_key)
    local given = {}
    for _province, cqi in pairs(IC.court(faction_key).govs) do
        local man = IC.character_by_cqi(faction_key, cqi)
        if man then
            pcall(function()
                cm:add_agent_experience(cm:char_lookup_str(man), T.governor_xp)
            end)
            local rank = "?"
            pcall(function() rank = tostring(man:rank()) end)
            given[#given + 1] = tostring(cqi) .. "@r" .. rank
        end
    end
    table.sort(given)
    if #given > 0 then
        IC.say("IRON COURT: governors given " .. T.governor_xp .. " xp in "
               .. faction_key .. ": " .. table.concat(given, " "))
    end
    return #given
end
```

In `IC.party_turn`, after `if not IC.is_human(faction_key) then return nil end`, add
`    IC.governor_xp(faction_key)`.

- [ ] **Step 4: Run the harness**

Expected: only the Task 6 "every kind" failure remains (check with `IC_TEST_ALL=1`).

---

### Task 3: Intrigue against the player (unwarned moves)

**Files:**
- Modify: `zzz_derpy_iron_court_parties.lua`
- Test: `tools/_iron_court_harness.lua`

**Interfaces:**
- Consumes: `IC.PARTY_ACTS`, `party_court`, `cards_of`.
- Produces:
  - `IC.PARTY_MOVES` (array of `{key, line, warned}`);
  - `IC.party_move_by_key(key)`;
  - `IC.party_plotter(fk, slug) -> cqi, influence`;
  - `IC.party_target(fk, slug, move, enemy) -> cqi, key`;
  - `IC.party_strike(fk, slug, move, actor, target, key, odds_div) -> bool`;
  - an `IC.PARTY_ACTS` entry with `key = "intrigue"`.

- [ ] **Step 1: Write the failing checks**

```lua
check("a restless party discredits the Crown's richest man, and pays for it", function()
    party_court({legion = 40, forge = 80})
    local cost = IC.plot_cost("discredit")
    assert(IC.party_turn(F) == "intrigue", "a restless party did nothing")
    local court = IC.court(F)
    assert(court.standing[311] == 1000 - cost, "the plotter paid "
           .. tostring(1000 - court.standing[311]) .. ", not " .. cost)
    assert(court.standing[301] == 800 - IC.TUNE.plot_discredit_standing,
           "the Crown's richest man was not the one discredited")
    assert(court.standing[302] == 100, "the wrong Crown man was hit")
    assert(cards_of("party_plot_ok") == 1, "no card for a landed move")
    local e = court.log[#court.log]
    assert(e.kind == "discredit" and e.slug == "legion" and e.key == IC.CROWN,
           "the record reads " .. tostring(e.kind) .. " by " .. tostring(e.slug))
    cm.get_human_factions = function() return {} end
end)

check("a party too poor to discredit spreads rumours instead", function()
    party_court({legion = 40, forge = 80})
    IC.court(F).standing[311] = IC.plot_cost("rumour")
    assert(IC.party_turn(F) == "intrigue")
    assert(IC.court(F).standing[301] == 800 - IC.TUNE.plot_rumour_damage,
           "a poor party did not fall back to rumours")
    cm.get_human_factions = function() return {} end
end)

check("only one party acts in a turn", function()
    party_court({legion = 40, forge = 40})
    IC.party_turn(F)
    local spent = 0
    if IC.court(F).standing[311] < 1000 then spent = spent + 1 end
    if IC.court(F).standing[321] < 1000 then spent = spent + 1 end
    assert(spent == 1, spent .. " parties acted in one turn")
    cm.get_human_factions = function() return {} end
end)

check("a failed move costs the party and tells the player", function()
    party_court({legion = 40, forge = 80})
    rng({1, 100})
    IC.party_turn(F)
    assert(IC.court(F).standing[311] == 1000 - IC.plot_cost("discredit"),
           "a failed move was free")
    assert(IC.court(F).standing[301] == 800, "a failed move still landed")
    assert(cards_of("party_plot_fail") == 1, "no card for a foiled move")
    assert(IC.court(F).log[#IC.court(F).log].kind == "plot_failed")
    cm.get_human_factions = function() return {} end
end)
```

- [ ] **Step 2: Run and see them fail**

Expected: `FAIL a restless party discredits ...: a restless party did nothing`

- [ ] **Step 3: Implement the moves, targets and resolution**

Add after `IC.PARTY_ACTS = {}` in the parties file:

```lua
-- Most severe first: a party takes the worst move its loyalty allows and its
-- plotter can pay for.
IC.PARTY_MOVES = {
    {key = "murder",    line = 10, warned = true},
    {key = "unseat",    line = 25, warned = true},
    {key = "recall",    line = 25, warned = true},
    {key = "discredit", line = T.party_intrigue_line},
    {key = "rumour",    line = T.party_intrigue_line},
}

function IC.party_move_by_key(key)
    for _, move in ipairs(IC.PARTY_MOVES) do
        if move.key == key then return move end
    end
    return nil
end

local function men_of(faction_key, slug)
    local out = {}
    local faction = cm:get_faction(faction_key)
    if not faction or faction:is_null_interface() then return out end
    local list = faction:character_list()
    for i = 0, list:num_items() - 1 do
        local man = list:item_at(i)
        if man and not man:is_null_interface()
                and IC.house_of_character(man, faction_key) == slug then
            out[#out + 1] = man
        end
    end
    return out
end

local function richest(faction_key, slug, keep)
    local best, best_n
    for _, man in ipairs(men_of(faction_key, slug)) do
        local cqi = man:command_queue_index()
        local n = IC.standing(faction_key, cqi)
        if (not keep or keep(man, cqi))
                and (not best or n > best_n or (n == best_n and cqi < best)) then
            best, best_n = cqi, n
        end
    end
    return best, best_n or 0
end

function IC.party_plotter(faction_key, slug)
    return richest(faction_key, slug, function(_man, cqi)
        return IC.may_speak(faction_key, cqi)
    end)
end

-- The Crown's office this party claims, else its highest-tier seat.
local function crown_seat(faction_key, slug)
    local court = IC.court(faction_key)
    local best, best_tier
    for i = 1, #IC.OFFICES do
        local office = IC.OFFICES[i]
        local cqi = court.offices[office.slug]
        if cqi and IC.house_of_cqi(faction_key, cqi) == IC.CROWN then
            if office.affinity == slug then return cqi, office.slug end
            if not best or office.tier < best_tier then
                best, best_tier = office.slug, office.tier
            end
        end
    end
    if best then return court.offices[best], best end
    return nil
end

local function crown_governor(faction_key)
    local court = IC.court(faction_key)
    local keys = {}
    for province in pairs(court.govs) do keys[#keys + 1] = province end
    table.sort(keys)
    for _, province in ipairs(keys) do
        local cqi = court.govs[province]
        if IC.house_of_cqi(faction_key, cqi) == IC.CROWN then
            return cqi, province
        end
    end
    return nil
end

function IC.party_target(faction_key, slug, move, enemy)
    if move == "unseat" then
        if enemy ~= IC.CROWN then return nil end
        return crown_seat(faction_key, slug)
    elseif move == "recall" then
        if enemy ~= IC.CROWN then return nil end
        return crown_governor(faction_key)
    elseif move == "murder" then
        local ruler = IC.faction_leader_cqi(faction_key)
        local cqi = richest(faction_key, enemy, function(man, c)
            return not IC.is_legend(man) and c ~= ruler
        end)
        return cqi
    end
    local cqi = richest(faction_key, enemy)
    return cqi
end

-- The player's own numbers: cost, base odds, 1 point per 10 influence of edge.
function IC.party_strike(faction_key, slug, move, actor, target, key, odds_div)
    local cost = IC.plot_cost(move)
    IC.add_standing(faction_key, actor, -cost)
    local base = T["plot_chance_" .. move] or 0
    if odds_div then base = math.floor(base / odds_div) end
    local edge = math.floor((IC.standing(faction_key, actor)
                             - IC.standing(faction_key, target)) / 10)
                 * T.plot_chance_per_10
    local chance = math.max(T.plot_chance_min,
                            math.min(T.plot_chance_max, base + edge))
    local victim_house = IC.house_of_cqi(faction_key, target)
    local at_crown = victim_house == IC.CROWN
    if cm:random_number(100, 1) > chance then
        IC.log(faction_key, "plot_failed", slug, victim_house, cost)
        if at_crown then IC.feed(faction_key, "party_plot_fail") end
        return false
    end
    if move == "rumour" then
        IC.add_standing(faction_key, target, -T.plot_rumour_damage)
    elseif move == "discredit" then
        IC.add_standing(faction_key, target, -T.plot_discredit_standing)
        local house = IC.court(faction_key).houses[victim_house or ""]
        if house then
            house.weight = math.max(1, (house.weight or 0)
                                    - T.plot_discredit_weight)
        end
    elseif move == "unseat" then
        IC.dismiss(faction_key, key, true)
        IC.court(faction_key).terms[key] = nil
        IC.apply_office_bundles(faction_key)
    elseif move == "recall" then
        IC.release_governor(faction_key, key)
    elseif move == "murder" then
        local victim = IC.character_by_cqi(faction_key, target)
        if victim then cm:kill_character(cm:char_lookup_str(victim), false) end
    end
    local kind = (move == "unseat" or move == "recall")
                 and ("party_" .. move) or move
    IC.log(faction_key, kind, slug, victim_house, cost)
    if at_crown then IC.feed(faction_key, "party_plot_ok") end
    return true
end

IC.PARTY_ACTS[#IC.PARTY_ACTS + 1] = {
    key = "intrigue",
    can = function(faction_key, slug)
        local house = IC.court(faction_key).houses[slug]
        if not house or (house.loyalty or 0) > T.party_intrigue_line then
            return nil
        end
        if IC.agenda(faction_key).feuds[slug] then return nil end
        local actor, purse = IC.party_plotter(faction_key, slug)
        if not actor then return nil end
        for _, move in ipairs(IC.PARTY_MOVES) do
            if house.loyalty <= move.line and purse >= IC.plot_cost(move.key) then
                local target, key = IC.party_target(faction_key, slug,
                                                    move.key, IC.CROWN)
                if target then
                    return {move = move, actor = actor, target = target,
                            key = key}
                end
            end
        end
        return nil
    end,
    motive = function(faction_key, slug, _t)
        local court = IC.court(faction_key)
        local claimed = 0
        for i = 1, #IC.OFFICES do
            local cqi = court.offices[IC.OFFICES[i].slug]
            if IC.OFFICES[i].affinity == slug and cqi
                    and IC.house_of_cqi(faction_key, cqi) == IC.CROWN then
                claimed = claimed + 1
            end
        end
        return (T.party_intrigue_line + 1 - court.houses[slug].loyalty)
               + 10 * claimed
    end,
    act = function(faction_key, slug, t)
        if t.move.warned then
            IC.party_warn(faction_key, slug, t)
        else
            IC.party_strike(faction_key, slug, t.move.key, t.actor, t.target, t.key)
        end
    end,
}
```

- [ ] **Step 4: Add a stub `IC.party_warn` so the table compiles** (Task 4 replaces it)

```lua
function IC.party_warn(_faction_key, _slug, _t) end
```

- [ ] **Step 5: Run the harness**

Expected: the four new checks pass. Only the "every kind" failure remains.

---

### Task 4: Warned moves (store, land, drop)

**Files:**
- Modify: `zzz_derpy_iron_court_parties.lua`
- Test: `tools/_iron_court_harness.lua`

**Interfaces:**
- Consumes: `IC.party_strike`, `IC.party_move_by_key`, `IC.agenda`.
- Produces: `IC.party_warn(fk, slug, t)`, `IC.plot_void(fk, p) -> nil|string`,
  `IC.land_plot(fk) -> "landed"|"dropped"`.

- [ ] **Step 1: Write the failing checks**

```lua
local function legion_office()
    for i = 1, #IC.OFFICES do
        if IC.OFFICES[i].affinity == "legion" then return IC.OFFICES[i].slug end
    end
end

check("a party at 25 warns a turn before it strikes a Crown seat", function()
    party_court({legion = 20, forge = 80})
    local office = legion_office()
    IC.court(F).offices[office] = 301
    IC.party_turn(F)
    local p = IC.agenda(F).plot
    assert(p and p.move == "unseat" and p.target == 301 and p.key == office,
           "no warned unseat of the claimed office")
    assert(IC.court(F).offices[office] == 301, "the seat went before the warning ran")
    assert(cards_of("party_plot_warn") == 1, "no warning card")
    turn = 11
    assert(IC.party_turn(F) == "landed", "the warned move did not land")
    assert(IC.court(F).offices[office] == nil, "the Crown man kept the seat")
    assert(IC.agenda(F).plot == nil, "the warned move stayed pending")
    assert(IC.court(F).log[#IC.court(F).log].kind == "party_unseat")
    cm.get_human_factions = function() return {} end
end)

check("a warned move is dropped when the party is placated", function()
    party_court({legion = 20, forge = 80})
    local office = legion_office()
    IC.court(F).offices[office] = 301
    IC.party_turn(F)
    IC.court(F).houses["legion"].loyalty = 60
    turn = 11
    assert(IC.party_turn(F) == "dropped", "a placated party still struck")
    assert(IC.court(F).offices[office] == 301, "the seat went anyway")
    assert(cards_of("party_plot_dropped") == 1, "no card for a dropped move")
    cm.get_human_factions = function() return {} end
end)

check("a warned move is dropped when its target has moved", function()
    party_court({legion = 20, forge = 80})
    local office = legion_office()
    IC.court(F).offices[office] = 301
    IC.party_turn(F)
    IC.court(F).offices[office] = 302
    turn = 11
    assert(IC.party_turn(F) == "dropped", "the move followed a man out of his seat")
    assert(IC.court(F).offices[office] == 302, "the new holder was struck")
    cm.get_human_factions = function() return {} end
end)

check("a murder is warned and never aimed at a legend", function()
    party_court({legion = 5, forge = 80})
    local court = IC.court(F)
    factions[F]._characters[1]._unique = true
    IC.party_turn(F)
    local p = IC.agenda(F).plot
    assert(p and p.move == "murder", "a party at 5 did not plan a murder")
    assert(p.target == 302, "the murder was aimed at " .. tostring(p.target))
    cm.get_human_factions = function() return {} end
end)

check("a governor can be recalled by a warned move", function()
    party_court({legion = 20, forge = 80})
    IC.court(F).govs["prov_a"] = 302
    IC.party_turn(F)
    local p = IC.agenda(F).plot
    assert(p and p.move == "recall" and p.key == "prov_a", "no warned recall")
    turn = 11
    IC.party_turn(F)
    assert(IC.court(F).govs["prov_a"] == nil, "the governor stayed")
    cm.get_human_factions = function() return {} end
end)
```

`IC.is_legend` reads `character_details():is_unique()`, which the stub answers from `_unique`
(model near line 3230), so setting `_unique` makes 301 a legend.

- [ ] **Step 2: Run and see them fail**

Expected: `FAIL a party at 25 warns ...: no warned unseat of the claimed office`

- [ ] **Step 3: Implement**

Replace the stub `IC.party_warn` with:

```lua
function IC.party_warn(faction_key, slug, t)
    IC.agenda(faction_key).plot = {
        slug = slug, move = t.move.key, actor = t.actor, target = t.target,
        key = t.key, turn = cm:model():turn_number(),
    }
    IC.log(faction_key, "party_warn", slug, t.move.key, 0)
    IC.feed(faction_key, "party_plot_warn")
end

-- Why a warned move no longer lands, or nil when it still does.
function IC.plot_void(faction_key, p)
    local court = IC.court(faction_key)
    local house = court.houses[p.slug]
    if not house then return "gone" end
    local move = IC.party_move_by_key(p.move)
    if not move or (house.loyalty or 0) > move.line then return "placated" end
    if not IC.character_by_cqi(faction_key, p.actor) then return "plotter dead" end
    if IC.standing(faction_key, p.actor) < IC.plot_cost(p.move) then
        return "poor"
    end
    local victim = IC.character_by_cqi(faction_key, p.target)
    if not victim then return "target dead" end
    if IC.house_of_character(victim, faction_key) ~= IC.CROWN then
        return "moved"
    end
    if p.move == "unseat" and court.offices[p.key] ~= p.target then
        return "moved"
    end
    if p.move == "recall" and court.govs[p.key] ~= p.target then
        return "moved"
    end
    return nil
end

function IC.land_plot(faction_key)
    local a = IC.agenda(faction_key)
    local p = a.plot
    a.plot = nil
    if IC.plot_void(faction_key, p) then
        IC.log(faction_key, "party_dropped", p.slug, p.move, 0)
        IC.feed(faction_key, "party_plot_dropped")
        return "dropped"
    end
    IC.party_strike(faction_key, p.slug, p.move, p.actor, p.target, p.key)
    return "landed"
end
```

In `IC.party_turn`, after `IC.governor_xp(faction_key)`, add:

```lua
    if IC.agenda(faction_key).plot then
        local done = IC.land_plot(faction_key)
        IC.save_agenda(faction_key)
        IC.save(faction_key)
        return done
    end
```

- [ ] **Step 4: Run the harness**

Expected: all Task 3 and Task 4 checks pass. Only the "every kind" failure remains.

---

### Task 5: Feuds

**Files:**
- Modify: `zzz_derpy_iron_court_parties.lua`
- Test: `tools/_iron_court_harness.lua`

**Interfaces:**
- Consumes: `IC.party_plotter`, `IC.party_target`, `IC.party_strike`, `IC.agenda`.
- Produces:
  - `IC.feud_target(fk, slug) -> nil|{with, cause, key}`;
  - `IC.end_feuds(fk) -> int`, called in `IC.party_turn` before a pending move lands;
  - `IC.PARTY_ACTS` entries `"feud"` and `"feud_move"`.

- [ ] **Step 1: Write the failing checks**

```lua
check("a stolen seat starts a feud", function()
    party_court({legion = 80, forge = 80})
    local office = legion_office()
    IC.court(F).offices[office] = 321
    assert(IC.party_turn(F) == "feud", "no feud over a stolen seat")
    local rec = IC.agenda(F).feuds["legion"]
    assert(rec and rec.a == "legion" and rec.b == "forge" and rec.cause == "seat"
           and rec.key == office, "the feud is not legion's over its seat")
    assert(IC.agenda(F).feuds["forge"] == rec, "only one side knows of the feud")
    assert(rec.ends == 10 + IC.TUNE.party_feud_turns)
    assert(cards_of("party_feud") == 1, "no card for a feud")
    cm.get_human_factions = function() return {} end
end)

check("two rivals of equal size feud", function()
    party_court({legion = 80, forge = 80})
    IC.court(F).houses["forge"].weight = 20
    assert(IC.party_turn(F) == "feud", "equal rivals did not feud")
    assert(IC.agenda(F).feuds["legion"].cause == "equal")
    cm.get_human_factions = function() return {} end
end)

check("a feuding party strikes its enemy, never the Crown", function()
    party_court({legion = 20, forge = 80})
    local office = legion_office()
    IC.court(F).offices[office] = 321
    local rec = {a = "legion", b = "forge", cause = "seat", key = office,
                 since = 10, ends = 20}
    IC.agenda(F).feuds.legion, IC.agenda(F).feuds.forge = rec, rec
    assert(IC.party_turn(F) == "feud_move", "the feud did not move")
    assert(IC.court(F).standing[301] == 800, "a feuding party hit the Crown")
    assert(IC.agenda(F).plot == nil, "a feuding party warned the Crown")
    assert(IC.court(F).standing[311] < 1000 or IC.court(F).standing[321] < 1000,
           "nobody in the feud paid for a move")
    cm.get_human_factions = function() return {} end
end)

check("a feud ends when the seat changes hands, then rests", function()
    party_court({legion = 80, forge = 80})
    local office = legion_office()
    IC.court(F).offices[office] = 321
    IC.party_turn(F)
    IC.court(F).offices[office] = 302
    turn = 11
    IC.party_turn(F)
    assert(IC.agenda(F).feuds["legion"] == nil, "the feud outlived its cause")
    assert(cards_of("party_feud_end") == 1, "no card for a feud ending")
    assert(IC.agenda(F).calm["legion"] == 11 + IC.TUNE.party_feud_rest,
           "the parties are not resting")
    cm.get_human_factions = function() return {} end
end)

check("a feud ends when its time is up", function()
    party_court({legion = 80, forge = 80})
    IC.court(F).houses["forge"].weight = 20
    IC.party_turn(F)
    turn = 10 + IC.TUNE.party_feud_turns
    IC.party_turn(F)
    assert(IC.agenda(F).feuds["legion"] == nil, "a feud ran past its end turn")
    cm.get_human_factions = function() return {} end
end)
```

- [ ] **Step 2: Run and see them fail**

Expected: `FAIL a stolen seat starts a feud: no feud over a stolen seat`

- [ ] **Step 3: Implement**

Add to the parties file, after the intrigue entry:

```lua
function IC.feud_target(faction_key, slug)
    local a = IC.agenda(faction_key)
    local now = cm:model():turn_number()
    local function free(s)
        return not a.feuds[s] and (a.calm[s] or 0) <= now
    end
    if not free(slug) then return nil end
    local court = IC.court(faction_key)
    for i = 1, #IC.OFFICES do
        local office = IC.OFFICES[i]
        local cqi = court.offices[office.slug]
        if office.affinity == slug and cqi then
            local holder = IC.house_of_cqi(faction_key, cqi)
            if holder and holder ~= slug and holder ~= IC.CROWN
                    and court.houses[holder] and free(holder) then
                return {with = holder, cause = "seat", key = office.slug}
            end
        end
    end
    local mine = IC.share(faction_key, slug)
    for _, other in ipairs(IC.present_houses(faction_key)) do
        if other ~= slug and other ~= IC.CROWN and free(other)
                and math.abs(IC.share(faction_key, other) - mine)
                    <= T.party_feud_equal then
            return {with = other, cause = "equal"}
        end
    end
    return nil
end

IC.PARTY_ACTS[#IC.PARTY_ACTS + 1] = {
    key = "feud",
    can = function(faction_key, slug) return IC.feud_target(faction_key, slug) end,
    motive = function(_fk, _slug, t)
        return t.cause == "seat" and T.party_feud_seat or T.party_feud_equal_motive
    end,
    act = function(faction_key, slug, t)
        local now = cm:model():turn_number()
        local rec = {a = slug, b = t.with, cause = t.cause, key = t.key,
                     since = now, ends = now + T.party_feud_turns}
        local a = IC.agenda(faction_key)
        a.feuds[slug], a.feuds[t.with] = rec, rec
        IC.log(faction_key, "feud", slug, t.with, 0)
        IC.feed(faction_key, "party_feud")
    end,
}

IC.PARTY_ACTS[#IC.PARTY_ACTS + 1] = {
    key = "feud_move",
    can = function(faction_key, slug)
        local rec = IC.agenda(faction_key).feuds[slug]
        if not rec then return nil end
        local enemy = rec.a == slug and rec.b or rec.a
        local actor, purse = IC.party_plotter(faction_key, slug)
        if not actor then return nil end
        local order = {"discredit", "rumour"}
        if cm:model():turn_number() - rec.since >= T.party_feud_murder_age then
            order = {"murder", "discredit", "rumour"}
        end
        for _, move in ipairs(order) do
            if purse >= IC.plot_cost(move) then
                local target = IC.party_target(faction_key, slug, move, enemy)
                if target then
                    return {move = move, actor = actor, target = target}
                end
            end
        end
        return nil
    end,
    motive = function() return T.party_feud_motive end,
    act = function(faction_key, slug, t)
        IC.party_strike(faction_key, slug, t.move, t.actor, t.target, nil,
                        t.move == "murder" and T.party_murder_odds_div or nil)
    end,
}

-- Upkeep, not an event: every feud whose cause is gone, whose time is up, or
-- whose party has left ends here.
function IC.end_feuds(faction_key)
    local a = IC.agenda(faction_key)
    local court = IC.court(faction_key)
    local now = cm:model():turn_number()
    local ended = {}
    for slug, rec in pairs(a.feuds) do
        if slug == rec.a then
            local over = now >= rec.ends
                or not court.houses[rec.a] or not court.houses[rec.b]
            if not over and rec.cause == "seat" then
                local holder = court.offices[rec.key or ""]
                over = not holder or IC.house_of_cqi(faction_key, holder) ~= rec.b
            elseif not over and rec.cause == "equal" then
                over = math.abs(IC.share(faction_key, rec.a)
                                - IC.share(faction_key, rec.b)) > T.party_feud_apart
            end
            if over then ended[#ended + 1] = rec end
        end
    end
    for _, rec in ipairs(ended) do
        a.feuds[rec.a], a.feuds[rec.b] = nil, nil
        a.calm[rec.a] = now + T.party_feud_rest
        a.calm[rec.b] = now + T.party_feud_rest
        IC.log(faction_key, "feud_end", rec.a, rec.b, 0)
        IC.feed(faction_key, "party_feud_end")
    end
    return #ended
end
```

In `IC.party_turn`, directly after `IC.governor_xp(faction_key)`, add
`    IC.end_feuds(faction_key)`.

- [ ] **Step 4: Run the harness**

Expected: all feud checks pass. Only the "every kind" failure remains. If "the parties are not
resting" fails with an off-by-one, the `calm` check reads `(a.calm[s] or 0) <= now`, so a party
may feud again on the turn its rest ends.

---

### Task 6: The panel - mood word, agenda tooltip, record sentences

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua`
  - `ICUI.mood` (near line 1222); add `ICUI.card_mood` and `ICUI.agenda_tip` after it
  - the party card draw near line 2768
  - `ICUI.intrigue_text` (near line 3345)
- Modify: `tools/gen_ic_ui.py:4136`
- Test: `tools/_iron_court_harness.lua`

**Interfaces:**
- Consumes: `IC.agenda`, `IC.party_move_by_key`, `ICUI.character_name`, `ICUI.office_name`,
  `ICUI.house_name`, and `loc` (a UI-file local).
- Produces: `ICUI.card_mood(faction, house, slug) -> string`,
  `ICUI.agenda_tip(faction, slug) -> string`.

- [ ] **Step 1: Write the failing checks**

```lua
check("the party card says a party is scheming or feuding", function()
    party_court({legion = 20, forge = 80})
    local house = IC.court(F).houses["legion"]
    assert(ICUI.card_mood(F, house, "legion") == ICUI.mood(house, "legion"),
           "a party with no agenda changed its word")
    IC.agenda(F).plot = {slug = "legion", move = "unseat", actor = 311,
                         target = 301, key = legion_office(), turn = 10}
    assert(ICUI.card_mood(F, house, "legion") == "SCHEMING")
    local tip = ICUI.agenda_tip(F, "legion")
    assert(string.find(tip, "next turn", 1, true), "the tip does not say when: " .. tip)
    assert(string.find(tip, "struck from his seat", 1, true), "the tip does not say what: " .. tip)
    house.clock = 2
    assert(ICUI.card_mood(F, house, "legion") == "SECEDES 2",
           "a countdown was hidden behind the agenda")
    house.clock = 0
    IC.agenda(F).plot = nil
    local rec = {a = "legion", b = "forge", cause = "equal", since = 10, ends = 20}
    IC.agenda(F).feuds.legion, IC.agenda(F).feuds.forge = rec, rec
    assert(ICUI.card_mood(F, IC.court(F).houses["forge"], "forge") == "FEUDING")
    assert(string.find(ICUI.agenda_tip(F, "forge"), "until turn 20", 1, true))
    assert(ICUI.agenda_tip(F, IC.CROWN) == "", "the Crown was given an agenda")
    cm.get_human_factions = function() return {} end
end)
```

The existing "every kind the model writes, the panel can describe" check covers the six new log
kinds.

- [ ] **Step 2: Run and see it fail**

Expected: `FAIL the party card says ...: attempt to call field 'card_mood' (a nil value)`

- [ ] **Step 3: Implement the two functions**

After the end of `ICUI.mood` in the UI file, add:

```lua
-- A countdown outranks the agenda: SECEDES 3 is the number the player acts on.
function ICUI.card_mood(faction, house, slug)
    local word = ICUI.mood(house, slug)
    if slug == IC.CROWN or not IC.agenda or (house.clock or 0) > 0 then
        return word
    end
    local a = IC.agenda(faction)
    if a.plot and a.plot.slug == slug then return "SCHEMING" end
    if a.feuds[slug] then return "FEUDING" end
    return word
end

-- The event card cannot name anyone; this tooltip is where the target is named.
function ICUI.agenda_tip(faction, slug)
    if slug == IC.CROWN or not IC.agenda then return "" end
    local a = IC.agenda(faction)
    local p = a.plot
    if p and p.slug == slug then
        local man = IC.character_by_cqi(faction, p.target)
        local who = man and ICUI.character_name(man) or "one of your men"
        local what
        if p.move == "unseat" then
            what = string.format("%s struck from his seat as %s", who,
                                 ICUI.office_name(p.key))
        elseif p.move == "recall" then
            what = string.format("%s recalled from %s", who,
                                 loc("provinces_onscreen_" .. tostring(p.key),
                                     tostring(p.key)))
        else
            what = string.format("an accident at the forge for %s", who)
        end
        local move = IC.party_move_by_key(p.move)
        return string.format("MOVING AGAINST YOU: %s, next turn. Raise their "
            .. "loyalty above %d, or deal with their plotter, to stop it.",
            what, move and move.line or 0)
    end
    local rec = a.feuds[slug]
    if rec then
        local enemy = rec.a == slug and rec.b or rec.a
        return string.format("FEUDING with %s (%s) until turn %d. While it "
            .. "lasts they strike at each other, not at you.",
            ICUI.house_name(enemy, faction),
            rec.cause == "seat" and "a stolen seat" or "rivals of equal size",
            rec.ends)
    end
    return ""
end
```

- [ ] **Step 4: Use them on the card**

In the party card draw, replace
`    set_text(comp("ic_party_mood", card), ICUI.mood(house, slug))` with
`    set_text(comp("ic_party_mood", card), ICUI.card_mood(faction, house, slug))`

and replace

```lua
            mood:SetTooltipText(ICUI.secession_tip(faction, court, slug),
                                "", true)
```

with

```lua
            local agenda = ICUI.agenda_tip(faction, slug)
            local tip = ICUI.secession_tip(faction, court, slug)
            mood:SetTooltipText(agenda ~= "" and (agenda .. "\n\n" .. tip) or tip,
                                "", true)
```

- [ ] **Step 5: Add the six record sentences**

In `ICUI.intrigue_text`, before the `elseif e.kind == "unseat" then` branch, add:

```lua
    elseif e.kind == "party_warn" then
        return string.format("%s is preparing to move against the Crown.", house)
    elseif e.kind == "party_dropped" then
        return string.format("%s's move against the Crown comes to nothing.", house)
    elseif e.kind == "party_unseat" then
        return string.format("%s spends %d influence, and a Crown officer loses "
                             .. "his seat.", house, e.n or 0)
    elseif e.kind == "party_recall" then
        return string.format("%s spends %d influence to have a Crown governor "
                             .. "called home.", house, e.n or 0)
    elseif e.kind == "feud" then
        return string.format("%s begins a feud with %s.", house,
                             ICUI.house_name(e.key))
    elseif e.kind == "feud_end" then
        return string.format("The feud between %s and %s is over.", house,
                             ICUI.house_name(e.key))
```

- [ ] **Step 6: Measure the new words**

In `tools/gen_ic_ui.py`, replace
`            "ic_party_mood": ["SECEDES 99", "PLOTTING", "RESTLESS", "LOYAL"],` with
`            "ic_party_mood": ["SECEDES 99", "PLOTTING", "RESTLESS", "LOYAL", "SCHEMING", "FEUDING"],`

- [ ] **Step 7: Run everything**

Run:
```powershell
& "C:\Program Files (x86)\Lua\5.1\luac.exe" -p "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court_ui.lua"
& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua
py tools\gen_ic_ui.py --check
```

Expected:
- the harness is green (all checks, including "every kind");
- `gen_ic_ui.py --check` prints `ok: 7 files, 224 components`.

---

### Task 7: Mutants for every rule

**Files:**
- Modify: `tools/mutate_iron_court.py` (append to `MUTANTS` before the closing `]`)

- [ ] **Step 1: Append the mutants**

```python
    # ---- rival parties that act on their own -------------------------------
    ("the parties given no turn", M,
     "    if IC.party_turn then IC.party_turn(faction_key) end\n",
     ""),
    ("an AI court's parties acting", P,
     "    if not IC.is_human(faction_key) then return nil end\n    IC.governor_xp",
     "    IC.governor_xp"),
    ("two events in one turn", P,
     "        chosen.act.act(faction_key, chosen.slug, chosen.target)",
     "        for i = 1, #picks do picks[i].act.act(faction_key, picks[i].slug, picks[i].target) end"),
    ("a motive under the floor still acting", P,
     "                    if m >= T.party_act_floor then",
     "                    if m >= 0 then"),
    ("a governor's experience given by level", P,
     "                cm:add_agent_experience(cm:char_lookup_str(man), T.governor_xp)",
     "                cm:add_agent_experience(cm:char_lookup_str(man), T.governor_xp, true)"),
    ("a loyal party plotting", P,
     "        if not house or (house.loyalty or 0) > T.party_intrigue_line then",
     "        if not house then"),
    ("a move taken above its loyalty line", P,
     "            if house.loyalty <= move.line and purse >= IC.plot_cost(move.key) then",
     "            if purse >= IC.plot_cost(move.key) then"),
    ("a move the plotter cannot afford", P,
     "            if house.loyalty <= move.line and purse >= IC.plot_cost(move.key) then",
     "            if house.loyalty <= move.line then"),
    ("a party move that costs nothing", P,
     "    IC.add_standing(faction_key, actor, -cost)",
     ""),
    ("a failed party move landing anyway", P,
     "    if cm:random_number(100, 1) > chance then",
     "    if false then"),
    ("the Crown's poorest man discredited", P,
     "                and (not best or n > best_n or (n == best_n and cqi < best)) then",
     "                and (not best or n < best_n or (n == best_n and cqi < best)) then"),
    ("a legend murdered", P,
     "            return not IC.is_legend(man) and c ~= ruler",
     "            return c ~= ruler"),
    ("a serious move without warning", P,
     "        if t.move.warned then",
     "        if false then"),
    ("a warned move landing the same turn", P,
     "    if IC.agenda(faction_key).plot then\n        local done = IC.land_plot(faction_key)",
     "    if false then\n        local done = IC.land_plot(faction_key)"),
    ("a placated party striking anyway", P,
     "    if not move or (house.loyalty or 0) > move.line then return \"placated\" end",
     "    if not move then return \"placated\" end"),
    ("a warned move following a man out of his seat", P,
     "    if p.move == \"unseat\" and court.offices[p.key] ~= p.target then",
     "    if false then"),
    ("a stolen seat starting no feud", P,
     "            if holder and holder ~= slug and holder ~= IC.CROWN",
     "            if false and holder ~= slug and holder ~= IC.CROWN"),
    ("equals never feuding", P,
     "                    <= T.party_feud_equal then",
     "                    < 0 then"),
    ("a feuding party still plotting against the Crown", P,
     "        if IC.agenda(faction_key).feuds[slug] then return nil end",
     ""),
    ("a feud murder at full odds", P,
     "                        t.move == \"murder\" and T.party_murder_odds_div or nil)",
     "                        nil)"),
    ("a feud outliving its seat", P,
     "                over = not holder or IC.house_of_cqi(faction_key, holder) ~= rec.b",
     "                over = false"),
    ("a feud with no end turn", P,
     "            local over = now >= rec.ends",
     "            local over = false"),
    ("no rest after a feud", P,
     "        return not a.feuds[s] and (a.calm[s] or 0) <= now",
     "        return not a.feuds[s]"),
    ("the feud half of the agenda not saved", P,
     "        if slug == rec.a then\n            feuds[#feuds + 1]",
     "        if false then\n            feuds[#feuds + 1]"),
    ("a countdown hidden behind the agenda", U,
     "    if slug == IC.CROWN or not IC.agenda or (house.clock or 0) > 0 then",
     "    if slug == IC.CROWN or not IC.agenda then"),
```

- [ ] **Step 2: Run the runner's self-test, then the new mutants**

Run:
```powershell
py tools\mutate_iron_court.py --selftest
py tools\mutate_iron_court.py "parties given" "AI court's parties" "two events" "under the floor" "by level" "loyal party plotting" "above its loyalty" "cannot afford" "costs nothing" "landing anyway" "poorest man" "legend murdered" "without warning" "same turn" "placated party" "out of his seat" "no feud" "never feuding" "still plotting" "full odds" "outliving" "no end turn" "no rest" "not saved" "hidden behind"
```

Expected:
- `selftest ok: 253 mutants all anchored ...` (228 + 25);
- the filtered run reports `25 mutants, 0 unexplained`.

A survivor means a check is missing: write it into the matching task's checks before going on.
"a feud murder at full odds" is the likeliest survivor, because no check forces a feud murder.
If it survives, add this check to Task 5's set:

```lua
check("a feud murder runs at a quarter of the odds", function()
    party_court({legion = 80, forge = 80})
    killed = {}
    local rec = {a = "legion", b = "forge", cause = "equal", since = 1, ends = 99}
    IC.agenda(F).feuds.legion, IC.agenda(F).feuds.forge = rec, rec
    IC.court(F).houses["forge"].weight = 20
    local quarter = math.floor(IC.TUNE.plot_chance_murder / IC.TUNE.party_murder_odds_div)
    rng({1, quarter + 1})
    IC.party_turn(F)
    assert(#killed == 0, "a feud murder landed on a roll above a quarter of the odds")
    cm.get_human_factions = function() return {} end
end)
```

`killed` is the harness global listing every `cm:kill_character` lookup. Forge acts (a tie
goes to the alphabetically first party), and its plotter's edge against legion's 311 is -25.
So the quartered chance clamps to `plot_chance_min` (5), and the full odds give 15: a roll of
11 lands only under the mutant.

- [ ] **Step 3: Full suite**

Run: `py tools\mutate_iron_court.py`
Expected: `253 mutants, 0 unexplained`.

---

### Task 8: Measure the pace, gate, deploy, write up

**Files:**
- Create (scratchpad, not shipped): `<scratchpad>/party_sim.lua`
- Modify: `docs/sessions/HANDOFF_20260923_IRON_COURT_AI_LIVE_CHECK.md` (add §4),
  `docs/SESSION_INDEX.md` (edit the spec's line)

- [ ] **Step 1: Build the simulation**

Copy the harness and append a 60-turn runner on the player-shaped court from §3g of the handoff:

```powershell
Copy-Item tools\_iron_court_harness.lua "$env:TEMP\claude\g--Modding-for-resources\5b3ea388-e646-42c2-af47-c02fb3edf714\scratchpad\party_sim.lua"
```

Append:

```lua
-- ===================== PARTY PACE SIMULATION =====================
local function sim(label, turns)
    IC.state, IC.agenda_state = {}, {}
    saved["derpy_ic_cr_chd_sim"], saved["derpy_ic_agenda_cr_chd_sim"] = nil, nil
    turn = 1
    local FK = "cr_chd_sim"
    cm.get_human_factions = function() return {FK} end
    local roster = {
        {1,"crown","field"},{2,"crown","field"},{3,"tower","field"},{4,"road","field"},
        {5,"crown","colonel"},{6,"crown","colonel"},{7,"crown","colonel"},
        {8,"tower","colonel"},{9,"road","colonel"},{10,"crown","colonel"},
        {11,"crown","home"},{12,"tower","home"},
    }
    local men = {}
    for i = 1, #roster do
        local m = make_character(roster[i][1], ANY_SEAT, roster[i][2])
        if roster[i][3] ~= "home" then m._force = true end
        if roster[i][3] == "colonel" then m._agent = "colonel" end
        men[i] = m
    end
    make_faction(FK, IC.CHD_SUBCULTURE, men, {"prov_a","prov_b","prov_c","prov_d","prov_e"})
    for _, s in ipairs({"crown", "tower", "road"}) do IC.add_house(FK, s) end
    IC.register()
    local seq, n = {}, 0
    for i = 1, 4000 do n = (n * 1103515245 + 12345) % 2147483648; seq[i] = n % 100 + 1 end
    rng(seq)
    local counts, quiet = {}, 0
    local real = IC.party_turn
    IC.party_turn = function(fk)
        local done = real(fk)
        if done then counts[done] = (counts[done] or 0) + 1 else quiet = quiet + 1 end
        return done
    end
    for t = 1, turns do
        turn = t
        IC.turn(FK)
        if t % 3 == 0 then
            for i = 1, 4 do IC.add_standing(FK, i, IC.TUNE.battle_influence.decisive_victory) end
        end
    end
    IC.party_turn = real
    local parts = {}
    for k, v in pairs(counts) do parts[#parts + 1] = k .. "=" .. v end
    table.sort(parts)
    local left = {}
    for s in pairs(IC.court(FK).houses) do left[#left + 1] = s end
    table.sort(left)
    print(string.format("%s: quiet %d/%d | %s | parties left: %s", label, quiet,
                        turns, table.concat(parts, " "), table.concat(left, ",")))
end
sim("player-shaped, 60 turns", 60)
```

- [ ] **Step 2: Run it and judge the pace**

Run: `& "C:\Program Files (x86)\Lua\5.1\lua.exe" "<scratchpad>\party_sim.lua"`

**Target:**
- roughly half the turns quiet;
- no party lost only to party intrigue;
- feuds a minority of events.

**If a target misses, tune in this order:**
1. `party_act_floor` (raise it for more quiet turns);
2. `party_feud_equal_motive` (lower it for fewer equals feuds);
3. `party_feud_rest`.

After a change, rerun the harness and this simulation. Record the final numbers for the write-up.

- [ ] **Step 3: All gates**

```powershell
foreach ($f in "zzz_derpy_iron_court.lua","zzz_derpy_iron_court_ui.lua","zzz_derpy_iron_court_parties.lua") { & "C:\Program Files (x86)\Lua\5.1\luac.exe" -p "Modding Files\pack\script\campaign\mod\$f" }
py tools\check_lua_api.py "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court_parties.lua"
py tools\check_lua_undeclared.py "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court.lua" "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court_parties.lua" "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court_ui.lua"
py tools\gen_iron_court.py --selftest
py tools\gen_iron_court.py
py tools\gen_ic_ui.py --check
py tools\preview_iron_court.py --check
py tools\mutate_iron_court.py --selftest
```

Expected:
- every tool exits 0;
- `check_lua_undeclared` run over the three files together reports `0 with undeclared names`.
  The UI file alone reports 13 pre-existing `EX.`/`IC.` field names, which are not findings.
- `gen_iron_court.py` (no flag) writes the TSVs with 584 loc rows.

- [ ] **Step 4: Deploy**

1. Confirm the game is closed and RPFM is up:
   ```powershell
   try { (Invoke-WebRequest http://127.0.0.1:45127/sessions -TimeoutSec 4 -UseBasicParsing).StatusCode } catch { "RPFM: " + $_.Exception.Message }; if (Get-Process Warhammer3 -ErrorAction SilentlyContinue) { "GAME RUNNING" } else { "game closed" }
   ```
2. Diff each deployed Iron Court Lua against the mirror, both ways, with
   `tools/read_pack_index.py` `read(pack, "zzz_derpy_iron_court")`. The parties file is new, so
   it is absent from the deployed pack. Every other difference must be an edit from this plan.
3. Run `py tools\deploy_iron_court.py`.
4. Verify:
   - SHA-256 of `Modding Files\Modpacks\derpy_iron_court.pack` equals the `data\` copy;
   - `used_mods.txt` still lists `derpy_iron_court.pack`;
   - `read(pack, "zzz_derpy_iron_court_parties.lua")` returns the file, containing
     `function IC.party_turn`.

- [ ] **Step 5: Write it up**

- **Handoff:** add `## 4. Rival parties, build 1 - DEPLOYED` to
  `docs/sessions/HANDOFF_20260923_IRON_COURT_AI_LIVE_CHECK.md`. Cover:
  - what shipped;
  - the five deviations above;
  - the simulation numbers;
  - the harness and mutant counts, pack size and SHA;
  - what the author should look for in game:
    - a `IRON COURT: governors given 750 xp ...` line each turn, where a governor whose rank
      never rises is a refusal;
    - SCHEMING and FEUDING on party cards;
    - the six new cards.
- **Index:** in `docs/SESSION_INDEX.md`, extend the spec's line with
  `build 1 (intrigue, feuds, governor xp) DEPLOYED 2026-09-23; build 2 (demands, offers) waits on the author's in-game test of governor xp and troops`.

---

## Self-review notes

- **Spec coverage:** §1 architecture is Tasks 1 and 3; §2 intrigue is Tasks 3 and 4; §3b
  governor experience is Task 2; §4 feuds is Task 5; §5b events is Task 1; §7 panel is Task 6
  (with deviation 1); §9 testing is Tasks 1-8. §3 demands, §5 offers and save fields 20-22 are
  Build 2 and not in this plan.
- **Names are consistent across tasks:**
  - `IC.agenda`, `IC.save_agenda`, `IC.party_turn`, `IC.PARTY_ACTS`, `IC.PARTY_MOVES`,
    `IC.party_move_by_key`;
  - `IC.party_plotter`, `IC.party_target`, `IC.party_strike`, `IC.party_warn`, `IC.plot_void`,
    `IC.land_plot`;
  - `IC.feud_target`, `IC.end_feuds`, `IC.governor_xp`;
  - `ICUI.card_mood`, `ICUI.agenda_tip`;
  - agenda records use `ends`, never `until`, which is a Lua keyword.
- **`IC.party_turn`'s final order,** after Tasks 2, 4 and 5:
  1. `is_human` guard;
  2. `IC.governor_xp`;
  3. `IC.end_feuds`;
  4. the pending warned move lands or drops and returns;
  5. otherwise score, choose and act;
  6. save.
