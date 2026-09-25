# The Iron Court: MCT and Multiplayer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give The Iron Court an MCT settings page (a difficulty preset, six switches, fourteen
Custom numbers, frozen into the save) and make every panel action safe in a multiplayer
campaign.

**Architecture:** The settings live in the model file as `IC.TUNE_ORDER` (append-only),
`IC.TUNE_DEFAULTS` (derived from `IC.TUNE`) and `IC.PRESETS`. `IC.freeze_tune()` runs first
thing at every first tick: it unpacks `derpy_ic_tuned` from the save if present, otherwise
reads MCT (never in multiplayer), and applies the result over `IC.TUNE`. Every panel action
goes through `IC.mp_send`. In single player that runs the op at once. In multiplayer it sends
a `UITrigger` that `IC.mp_receive` applies on every machine. The model answers through the
`IC.after_op` hook, which the panel sets.

**Tech Stack:** Lua 5.1.5 (game scripts and the harness `tools/_iron_court_harness.lua`),
Python 3 (`tools/import_iron_court.py`, `tools/deploy_iron_court.py`,
`tools/mutate_iron_court.py`), RPFM's MCP server (deploy only), MCT (`groovy_mct.pack`,
optional at runtime).

**Spec:** `docs/superpowers/specs/2026-09-25-iron-court-mct-multiplayer-design.md` (read its
"Amended 2026-09-25, while planning" block first: the freeze is at first tick, the hook carries
`arg`, two labels changed).

## Global Constraints

- Lua 5.1.5, matching the game. In a function with more than 255 constants, a number literal
  on the LEFT of an arithmetic operator is miscompiled in game, so keep literals on the right.
  The gate runs `check_lua_literal_left.py`.
- Paths in bash: `cd "/g/Modding for resources"`; Lua is
  `"/c/Program Files (x86)/Lua/5.1/lua.exe"`. The harness must run from the workspace root.
- **Not a git repository.** No commits and no worktree. Task 1 step 1 backs up every file this
  plan edits; that backup replaces both.
- Edit files with the Edit and Write tools only. `sed -i` rewrites CRLF files as LF, and a Bash
  heredoc halves backslashes.
- Never edit any file while `tools/mutate_iron_court.py` is running: it writes mutations into
  the SHIPPED Lua and restores them afterwards.
- `.pack`, `.loc` and DB tables are binary: only RPFM touches them. Deploy only with the game
  CLOSED and RPFM OPEN. Back up the live pack in `data/` first, then verify the saved pack.
  The pack lives in the game's `data/` folder, not the Workshop.
- No emojis anywhere, and never the word "rung".
- Player text uses plain words: party, influence, office, overseer, Crown. Never "standing" (use
  "Reputation" if it is ever needed), and no cap/accrue/rep/AI/HUD jargon in MCT text.
- Do not touch `repos/derpy-iron-court`, and do not sync or push any public repo. The user
  decides when repos move.
- Wire tag `IC.MP_TAG = "ic1"`, ceiling `IC.MP_MAX = 100` characters. Refuse and log, never
  apply locally, on a missing cqi, an unknown op or an over-long message.
- `cm:get_local_faction_name(true)` only, the forced form. The unforced form throws in
  multiplayer.
- `IC.TUNE_ORDER` is append-only: a new key goes at the END, never in the middle.
- MCT is not read in multiplayer: every machine uses the defaults.
- Every switch defaults to ON and every number defaults to today's value, so a campaign
  without MCT plays exactly as it does now.
- Preset values, copied verbatim from the spec:

  | key | gentle | default | harsh | ruthless | slider (step) |
  |---|---|---|---|---|---|
  | loyalty_start | 65 | 55 | 50 | 45 | 30 to 80 |
  | loyalty_drift_none | 0 | -1 | -2 | -3 | -5 to 0 |
  | secede_loyalty | 15 | 20 | 25 | 30 | 0 to 40 |
  | secede_share | 30 | 25 | 20 | 15 | 5 to 50 |
  | secede_turns | 7 | 5 | 4 | 3 | 1 to 10 |
  | pressure_below | 5 | 10 | 15 | 20 | 0 to 30 |
  | influence_trickle | 7 | 5 | 4 | 3 | 0 to 20 |
  | settlement_influence | 30 | 24 | 20 | 16 | 0 to 60 |
  | favour_gift_cost | 400 | 600 | 800 | 1000 | 100 to 3000 (50) |
  | favour_secure_cost | 1800 | 2500 | 3200 | 4000 | 500 to 10000 (100) |
  | party_intrigue_line | 45 | 55 | 60 | 65 | 20 to 80 |
  | rivals_min | 2 | 2 | 3 | 3 | 1 to 4 |
  | rivals_max | 3 | 4 | 4 | 4 | 1 to 4 |
  | term_turns | 5 | 5 | 5 | 5 | 2 to 10 |

## Review Focus

These are the five inputs the spec implies, and no other test here exercises, most likely to
bite a player. Each has a pinning test in the task named.

1. **A saved `derpy_ic_tuned` that is garbled or from a later build** (an unreadable field, or
   more fields than this build knows). An unreadable field keeps its default, including a
   switch, which must not read as OFF, and extra fields are ignored. Task 1, "a garbled or
   newer saved string keeps the defaults it cannot read".
2. **MCT installed but this mod's page failed to register** (the settings file errored, so
   `get_mod_by_key` answers nil). The defaults apply, with no error. Task 1, "MCT without this
   mod's page reads as the defaults".
3. **A save from before this build, loaded with a non-default preset set in MCT.** The preset
   applies from that load and is then fixed, and parties already seated keep their loyalty.
   Task 1, "an old save takes the settings on load and keeps its parties' loyalty".
4. **A trigger whose number field is garbled** (`ic1|appoint|warden|abc`). The model refuses it
   as it would any bad pick: no Lua error, no change, and the panel is told no. Task 4, "a
   trigger with a garbled number is refused by the model, not by an error".
5. **A mixed multiplayer campaign where this machine's player is not the first human** (for
   example a Dwarf player beside a Chaos Dwarf host). The panel reads this machine's faction
   and never the host's court. Task 5, "the panel's player is this machine's, read the forced
   way".

---

## File Structure

| File | Change | Responsibility |
|---|---|---|
| `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua` | modify | the settings block after `IC.TUNE`, `IC.warn`, `IC.runs_court`, the four switch guards, the multiplayer transport before `IC.register`, the `ic_mp` listener, the `hold_feed` guard, `IC.first_tick` |
| `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_parties.lua` | modify | drop the `party_intrigue_line` definition (now in `IC.TUNE`), the `parties_act` guard, one `IC.warn` |
| `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua` | modify | `ICUI.player` forced, `ICUI.after_op` and `ICUI.ANSWERS`, the eleven call sites become `IC.mp_send` |
| `Modding Files/pack/script/mct/settings/derpy_iron_court.lua` | create | the MCT page |
| `tools/_iron_court_harness.lua` | modify | faction stub cqi, `IC.warn` collector, helpers, 40 new checks |
| `tools/import_iron_court.py` | modify | the MCT file in `SCRIPTS`, `check_mp_routing`, `check_tune_reads`, `--selftest` |
| `tools/deploy_iron_court.py` | modify | the MCT file in `SCRIPTS` |
| `tools/mutate_iron_court.py` | modify | the MCT file path `S`, new mutants, three re-aimed anchors |
| `tools/sync_iron_court_repo.py` | modify | the MCT file, spec, plan and handoff in the manifest (no sync run) |
| `docs/sessions/HANDOFF_20260925_IRON_COURT_MCT_MULTIPLAYER.md` | create | the write-up |
| `docs/SESSION_INDEX.md` | modify | one line |

All new harness checks go **immediately above** the line
`check("no parties' turn failed anywhere in the run", function()`. That check and the boolean
check after it must stay last. Each task's checks go below the previous task's.

---

### Task 1: Settings core: defaults, presets, reading, packing, freezing at first tick

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua` (the `IC.TUNE` literal ending near line 486; the first-tick callback at the end of the file)
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_parties.lua:9`
- Test: `tools/_iron_court_harness.lua`

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces:
  - `IC.TUNE_ORDER` (array of 20 key strings, append-only)
  - `IC.TUNE_DEFAULTS` (key -> value)
  - `IC.PRESETS` (`gentle`/`harsh`/`ruthless` -> table of the 14 numbers)
  - `IC.PRESET_CUSTOM = "custom"`
  - `IC.is_mp() -> boolean`
  - `IC.read_mct_or_defaults() -> table`
  - `IC.pack_tune(t) -> string`
  - `IC.unpack_tune(s) -> table`
  - `IC.apply_tune(t)`
  - `IC.freeze_tune() -> table`
  - `IC.first_tick()`
  - New `IC.TUNE` keys: `party_intrigue_line = 55`, and `parties_act`, `ai_courts`,
    `secession`, `pressure`, `crown_split`, `detailed_log`, all `true`.
  - Harness helpers: `stub_mct(values, mod_key)` and `with_mct(mct, fn)`.

- [ ] **Step 1: Back up every file this plan edits, and prove the baseline is green**

```bash
cd "/g/Modding for resources"
B="Modding Files/source/iron_court_bak_pre_mctmp_20260925"
mkdir -p "$B"
cp -p "Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua" \
      "Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_parties.lua" \
      "Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua" \
      tools/_iron_court_harness.lua tools/import_iron_court.py tools/deploy_iron_court.py \
      tools/mutate_iron_court.py tools/sync_iron_court_repo.py "$B/"
ls "$B" | wc -l
"/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | tail -1
py tools/mutate_iron_court.py --selftest 2>&1 | tail -1
```

Expected: `8`, then `iron court harness: ok (587 checks)`, then `selftest ok: 367 mutants all anchored, ...` (whatever count it prints, it must say `selftest ok`).

- [ ] **Step 2: Write the failing checks**

Insert immediately above `check("no parties' turn failed anywhere in the run", function()` in `tools/_iron_court_harness.lua`:

```lua
-- ---------------------------------------------------------------------------
-- SETTINGS (MCT) AND MULTIPLAYER, 2026-09-25.
-- docs/superpowers/specs/2026-09-25-iron-court-mct-multiplayer-design.md
-- ---------------------------------------------------------------------------

-- AN MCT HOLDING `values`: option key -> what get_finalized_setting answers. An
-- option not named is absent, which is what a missing registration looks like.
-- `mod_key` is the page it answers for; any other key answers nil.
local function stub_mct(values, mod_key)
    local mod = {
        get_option_by_key = function(_, key)
            if values[key] == nil then return nil end
            return {get_finalized_setting = function() return values[key] end}
        end,
    }
    return {
        get_mod_by_key = function(_, key)
            if key == (mod_key or "derpy_iron_court") then return mod end
            return nil
        end,
    }
end

-- fn with get_mct answering `mct` (nil: MCT is not installed). Afterwards every
-- setting goes back to its default and the save forgets the frozen copy, so no
-- later check plays on a preset.
local function with_mct(mct, fn)
    get_mct = mct and function() return mct end or nil
    local ok, err = pcall(fn)
    get_mct = nil
    saved["derpy_ic_tuned"] = nil
    IC.apply_tune(IC.TUNE_DEFAULTS)
    if not ok then error(err, 0) end
end

check("the settings pack and unpack whole", function()
    local t = {}
    for k, v in pairs(IC.TUNE_DEFAULTS) do t[k] = v end
    t.loyalty_start, t.loyalty_drift_none, t.parties_act = 71, -4, false
    local back = IC.unpack_tune(IC.pack_tune(t))
    for _, key in ipairs(IC.TUNE_ORDER) do
        assert(back[key] == t[key], key .. " came back " .. tostring(back[key])
            .. ", packed as " .. tostring(t[key]))
    end
end)

check("an older save one setting short keeps the new one on its default", function()
    -- THE APPEND-ONLY RULE, from the reading side: a save written before the
    -- last key existed has one field fewer, and that key must come back as its
    -- default and not as nil.
    local last = IC.TUNE_ORDER[#IC.TUNE_ORDER]
    local short = string.match(IC.pack_tune(IC.TUNE_DEFAULTS), "^(.*)|[^|]*$")
    local back = IC.unpack_tune(short)
    assert(back[last] == IC.TUNE_DEFAULTS[last],
        last .. " came back " .. tostring(back[last]) .. " from a save without it")
end)

check("a partial settings table packs its defaults, never zeros", function()
    -- 0 IS OFF for a switch and a real number for a price, so a missing key
    -- written as 0 switches things off in every save that lacks it.
    assert(IC.pack_tune({}) == IC.pack_tune(IC.TUNE_DEFAULTS),
        "an empty table packed as " .. IC.pack_tune({}))
end)

check("a garbled or newer saved string keeps the defaults it cannot read", function()
    -- REVIEW FOCUS 1. The first field (a number) and the parties_act field (a
    -- switch) are unreadable, and one field too many is on the end.
    local parts = {}
    for piece in string.gmatch(IC.pack_tune(IC.TUNE_DEFAULTS), "[^|]+") do
        parts[#parts + 1] = piece
    end
    local first = IC.TUNE_ORDER[1]
    local switch_at = nil
    for i = 1, #IC.TUNE_ORDER do
        if IC.TUNE_ORDER[i] == "parties_act" then switch_at = i end
    end
    parts[1] = "junk"
    parts[switch_at] = "junk"
    parts[#parts + 1] = "99"
    local back = IC.unpack_tune(table.concat(parts, "|"))
    assert(back[first] == IC.TUNE_DEFAULTS[first],
        first .. " read " .. tostring(back[first]) .. " from an unreadable field")
    assert(back.parties_act == true,
        "an unreadable switch read as " .. tostring(back.parties_act) .. ", not its default")
end)

check("without MCT the settings are the defaults", function()
    with_mct(nil, function()
        local t = IC.read_mct_or_defaults()
        for _, key in ipairs(IC.TUNE_ORDER) do
            assert(t[key] == IC.TUNE_DEFAULTS[key], key .. " read " .. tostring(t[key]))
        end
    end)
end)

check("MCT without this mod's page reads as the defaults", function()
    -- REVIEW FOCUS 2: the settings file failed to load, so MCT holds no page
    -- called derpy_iron_court.
    with_mct(stub_mct({preset = "harsh"}, "some_other_mod"), function()
        local t = IC.read_mct_or_defaults()
        assert(t.loyalty_start == IC.TUNE_DEFAULTS.loyalty_start,
            "read " .. tostring(t.loyalty_start) .. " with no page registered")
    end)
end)

check("each difficulty sets its fourteen numbers", function()
    for name, preset in pairs(IC.PRESETS) do
        with_mct(stub_mct({preset = name}), function()
            local t = IC.read_mct_or_defaults()
            for key, v in pairs(preset) do
                assert(t[key] == v, name .. " read " .. key .. " = " .. tostring(t[key])
                    .. ", the preset says " .. v)
            end
        end)
    end
    -- AND THE TABLE IS THE SPEC'S, one value per difficulty.
    assert(IC.PRESETS.gentle.loyalty_start == 65 and IC.PRESETS.harsh.loyalty_start == 50
        and IC.PRESETS.ruthless.loyalty_start == 45,
        "the preset table has drifted from the design")
end)

check("every difficulty names exactly the fourteen numbers", function()
    local numbers = {}
    for _, key in ipairs(IC.TUNE_ORDER) do
        if type(IC.TUNE_DEFAULTS[key]) == "number" then numbers[key] = true end
    end
    for name, preset in pairs(IC.PRESETS) do
        for key in pairs(numbers) do
            assert(preset[key] ~= nil, name .. " leaves " .. key .. " unset")
        end
        for key in pairs(preset) do
            assert(numbers[key], name .. " sets " .. key .. ", which is not a number setting")
        end
    end
end)

check("a difficulty ignores the sliders and Custom reads them", function()
    with_mct(stub_mct({preset = "harsh", loyalty_start = 70}), function()
        local v = IC.read_mct_or_defaults().loyalty_start
        assert(v == 50, "harsh read the slider: " .. tostring(v))
    end)
    with_mct(stub_mct({preset = "default", loyalty_start = 70}), function()
        local v = IC.read_mct_or_defaults().loyalty_start
        assert(v == IC.TUNE_DEFAULTS.loyalty_start, "default read the slider: " .. tostring(v))
    end)
    with_mct(stub_mct({preset = "custom", loyalty_start = 70}), function()
        local t = IC.read_mct_or_defaults()
        assert(t.loyalty_start == 70, "custom ignored the slider: " .. tostring(t.loyalty_start))
        assert(t.secede_turns == IC.TUNE_DEFAULTS.secede_turns,
            "an unset slider read " .. tostring(t.secede_turns))
    end)
end)

check("the switches are read on every difficulty", function()
    for _, name in ipairs({"default", "gentle", "custom"}) do
        with_mct(stub_mct({preset = name, parties_act = false}), function()
            assert(IC.read_mct_or_defaults().parties_act == false,
                name .. " ignored the parties_act switch")
        end)
    end
end)

check("a setting of the wrong type falls back to its default", function()
    with_mct(stub_mct({preset = "custom", loyalty_start = true, parties_act = 1}), function()
        local t = IC.read_mct_or_defaults()
        assert(t.loyalty_start == IC.TUNE_DEFAULTS.loyalty_start,
            "a slider answering a boolean read " .. tostring(t.loyalty_start))
        assert(t.parties_act == true,
            "a checkbox answering a number read " .. tostring(t.parties_act))
    end)
end)

check("fewest rival parties above most is clamped down to it", function()
    with_mct(stub_mct({preset = "custom", rivals_min = 4, rivals_max = 2}), function()
        local t = IC.read_mct_or_defaults()
        assert(t.rivals_min == 2 and t.rivals_max == 2,
            "read " .. t.rivals_min .. " to " .. t.rivals_max)
    end)
end)

check("multiplayer never reads MCT", function()
    cm.is_multiplayer = function() return true end
    local ok, err = pcall(with_mct, stub_mct({preset = "ruthless", parties_act = false}),
        function()
            local t = IC.read_mct_or_defaults()
            assert(t.loyalty_start == IC.TUNE_DEFAULTS.loyalty_start,
                "multiplayer read the preset: " .. tostring(t.loyalty_start))
            assert(t.parties_act == true, "multiplayer read a switch")
        end)
    cm.is_multiplayer = nil
    if not ok then error(err, 0) end
end)

check("a multiplayer check that errors reads as single player", function()
    cm.is_multiplayer = function() error("no model yet") end
    local mp = IC.is_mp()
    cm.is_multiplayer = nil
    assert(mp == false, "an erroring is_multiplayer read as " .. tostring(mp))
end)

check("the settings freeze once and a reload keeps them", function()
    with_mct(stub_mct({preset = "harsh"}), function()
        saved["derpy_ic_tuned"] = nil
        IC.freeze_tune()
        assert(IC.TUNE.loyalty_start == 50, "the freeze applied " .. IC.TUNE.loyalty_start)
        assert(type(saved["derpy_ic_tuned"]) == "string", "nothing was written into the save")
        -- THE PLAYER CHANGES MCT AND RELOADS. A new session starts on the
        -- defaults, and the save must win over what MCT now says.
        get_mct = function() return stub_mct({preset = "gentle"}) end
        IC.apply_tune(IC.TUNE_DEFAULTS)
        IC.freeze_tune()
        assert(IC.TUNE.loyalty_start == 50, "a reload re-read MCT: " .. IC.TUNE.loyalty_start)
    end)
end)

check("a new campaign rolls the player's court on the frozen numbers", function()
    -- THE TIMING. A new campaign rolls the player's court at first tick and
    -- fires no FactionTurnStart until turn 1 ends, so a freeze taken at the
    -- turn start rolled every player's court on the defaults.
    with_mct(stub_mct({preset = "custom", rivals_min = 1, rivals_max = 1}), function()
        IC.state = {}
        saved["derpy_ic_tuned"] = nil
        saved["derpy_ic_" .. F] = nil
        rng(nil)
        cm.get_human_factions = function() return {F} end
        make_faction(F, IC.CHD_SUBCULTURE, {make_character(801, ANY_SEAT, nil, nil)}, {})
        local ok, err = pcall(IC.first_tick)
        cm.get_human_factions = function() return {} end
        assert(ok, "the first tick raised: " .. tostring(err))
        local n = 0
        for _ in pairs(IC.court(F).houses) do n = n + 1 end
        assert(n == 2, "the court rolled " .. n .. " parties; the Crown and exactly one "
            .. "rival were set, so the roll ran before the freeze")
    end)
end)

check("an old save takes the settings on load and keeps its parties' loyalty", function()
    -- REVIEW FOCUS 3. A save from before this build holds a court and no
    -- derpy_ic_tuned; the load freezes the player's MCT choice and must not
    -- rewrite the loyalty of a party already seated.
    IC.state = {}
    make_faction(F, IC.CHD_SUBCULTURE, {}, {})
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    IC.court(F).houses.legion.loyalty = 33
    with_mct(stub_mct({preset = "harsh"}), function()
        saved["derpy_ic_tuned"] = nil
        IC.freeze_tune()
        assert(IC.TUNE.secede_turns == 4, "the old save did not take the preset")
        assert(IC.court(F).houses.legion.loyalty == 33,
            "applying the settings rewrote a seated party's loyalty to "
            .. IC.court(F).houses.legion.loyalty)
    end)
end)

check("the settings move the loyalty rumour and discredit start at", function()
    -- THE ONE LOAD-TIME COPY: the parties file copies party_intrigue_line into
    -- two moves when it loads, so apply_tune has to write it through.
    local t = {}
    for k, v in pairs(IC.TUNE_DEFAULTS) do t[k] = v end
    t.party_intrigue_line = 40
    IC.apply_tune(t)
    local lines = {}
    for _, move in ipairs(IC.PARTY_MOVES) do lines[move.key] = move.line end
    IC.apply_tune(IC.TUNE_DEFAULTS)
    assert(lines.discredit == 40 and lines.rumour == 40,
        "discredit " .. tostring(lines.discredit) .. ", rumour " .. tostring(lines.rumour))
    assert(lines.murder == 10, "a fixed line moved with the setting: " .. tostring(lines.murder))
end)
```

- [ ] **Step 3: Run the harness and watch all eighteen fail**

```bash
cd "/g/Modding for resources"
IC_TEST_ALL=1 "/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | grep -E "^FAIL|failing"
```

Expected: 18 `FAIL` lines, one per new check, each about a nil field (`unpack_tune`, `pack_tune`, `read_mct_or_defaults`, `apply_tune`, `freeze_tune`, `is_mp`, `first_tick`, `TUNE_DEFAULTS` or `PRESETS`), then `18 failing, 587 passing`.

- [ ] **Step 4: Move `party_intrigue_line` into `IC.TUNE` and add the six switches**

In `zzz_derpy_iron_court.lua`, replace:

```lua
    splinter_loyalty    = 25,
    splinter_weight     = 5,
}
```

with:

```lua
    splinter_loyalty    = 25,
    splinter_weight     = 5,

    -- Rumour and discredit at or below this loyalty. Defined here, not in the
    -- parties file, since 2026-09-25, so the settings below can freeze it.
    party_intrigue_line = 55,

    -- THE SIX SWITCHES (the MCT page's Systems and Debug). All on: a campaign
    -- without MCT plays exactly as it did before they existed.
    parties_act         = true,
    ai_courts           = true,
    secession           = true,
    pressure            = true,
    crown_split         = true,
    detailed_log        = true,
}
```

In `zzz_derpy_iron_court_parties.lua`, delete this line (line 9):

```lua
T.party_intrigue_line   = 55   -- rumour and discredit at or below this loyalty
```

- [ ] **Step 5: Add the settings block**

In `zzz_derpy_iron_court.lua`, replace:

```lua
IC.AMBITION_ORDER = {"cautious", "steady", "ambitious"}
```

with:

```lua
-- ---------------------------------------------------------------------------
-- SETTINGS. Fourteen numbers and six switches belong to the player, through MCT.
-- Each is read ONCE, frozen into the save as derpy_ic_tuned, and applied over
-- IC.TUNE, so every IC.TUNE.x read in this mod is unchanged and a save plays
-- on the numbers it started with whatever MCT says later.
--
-- REGISTERED THREE TIMES: in IC.TUNE above, in IC.TUNE_ORDER below, and in
-- script/mct/settings/derpy_iron_court.lua. The court harness holds all three
-- against each other, and the packing gate refuses a setting nothing reads.
--
-- A NEW KEY IS APPENDED, NEVER INSERTED. unpack_tune walks this list by
-- position against the saved string, so a key put anywhere but the end moves
-- every value after it onto the wrong setting in every existing save.
IC.TUNE_ORDER = {
    "loyalty_start", "loyalty_drift_none", "secede_loyalty", "secede_share",
    "secede_turns", "pressure_below", "influence_trickle", "settlement_influence",
    "favour_gift_cost", "favour_secure_cost", "party_intrigue_line",
    "rivals_min", "rivals_max", "term_turns",
    "parties_act", "ai_courts", "secession", "pressure", "crown_split",
    "detailed_log",
}

-- Today's values, taken off IC.TUNE before anything can change it.
IC.TUNE_DEFAULTS = {}
for _i = 1, #IC.TUNE_ORDER do
    IC.TUNE_DEFAULTS[IC.TUNE_ORDER[_i]] = IC.TUNE[IC.TUNE_ORDER[_i]]
end

-- The difficulty dropdown. Default is IC.TUNE_DEFAULTS and so is not listed,
-- and Custom reads the sliders. A preset names numbers only: the switches are
-- the player's on every difficulty.
IC.PRESET_CUSTOM = "custom"
IC.PRESETS = {
    gentle = {
        loyalty_start = 65, loyalty_drift_none = 0, secede_loyalty = 15,
        secede_share = 30, secede_turns = 7, pressure_below = 5,
        influence_trickle = 7, settlement_influence = 30,
        favour_gift_cost = 400, favour_secure_cost = 1800,
        party_intrigue_line = 45, rivals_min = 2, rivals_max = 3, term_turns = 5,
    },
    harsh = {
        loyalty_start = 50, loyalty_drift_none = -2, secede_loyalty = 25,
        secede_share = 20, secede_turns = 4, pressure_below = 15,
        influence_trickle = 4, settlement_influence = 20,
        favour_gift_cost = 800, favour_secure_cost = 3200,
        party_intrigue_line = 60, rivals_min = 3, rivals_max = 4, term_turns = 5,
    },
    ruthless = {
        loyalty_start = 45, loyalty_drift_none = -3, secede_loyalty = 30,
        secede_share = 15, secede_turns = 3, pressure_below = 20,
        influence_trickle = 3, settlement_influence = 16,
        favour_gift_cost = 1000, favour_secure_cost = 4000,
        party_intrigue_line = 65, rivals_min = 3, rivals_max = 4, term_turns = 5,
    },
}

-- AN ENGINE CALL THAT ERRORS READS AS SINGLE PLAYER: locking a single-player
-- campaign out of its own settings over a failed call is the worse failure.
function IC.is_mp()
    local ok, v = pcall(function() return cm:is_multiplayer() end)
    return ok and v == true
end

function IC.read_mct_or_defaults()
    local t = {}
    for k, v in pairs(IC.TUNE_DEFAULTS) do t[k] = v end
    -- BEFORE MCT IS EVEN ASKED: two machines holding different settings would
    -- freeze two different courts into two saves at the first tick.
    if IC.is_mp() then return t end
    local ok, mct = pcall(function() return get_mct and get_mct() end)
    if not ok or not mct then return t end
    pcall(function()
        local mod = mct:get_mod_by_key("derpy_iron_court")
        if not mod then return end
        -- TYPE-CHECKED, NOT NIL-CHECKED. MCT hands back whatever the option
        -- holds, and a mis-registered option answers the wrong shape.
        local function read(key)
            local opt = mod:get_option_by_key(key)
            if not opt then return nil end
            local v = opt:get_finalized_setting()
            if type(v) == type(IC.TUNE_DEFAULTS[key]) then return v end
            return nil
        end
        local preset = "default"
        local popt = mod:get_option_by_key("preset")
        local pv = popt and popt:get_finalized_setting()
        if type(pv) == "string" and pv ~= "" then preset = pv end
        -- THE SWITCHES ON EVERY DIFFICULTY, the numbers under Custom only.
        for _, key in ipairs(IC.TUNE_ORDER) do
            local custom_number = type(IC.TUNE_DEFAULTS[key]) == "number"
                and preset == IC.PRESET_CUSTOM
            if type(IC.TUNE_DEFAULTS[key]) == "boolean" or custom_number then
                local v = read(key)
                if v ~= nil then t[key] = v end
            end
        end
        for key, v in pairs(IC.PRESETS[preset] or {}) do t[key] = v end
    end)
    -- cm:random_number(max, min) with min above max is no roll at all.
    if t.rivals_min > t.rivals_max then t.rivals_min = t.rivals_max end
    return t
end

function IC.pack_tune(t)
    local parts = {}
    for i = 1, #IC.TUNE_ORDER do
        local key = IC.TUNE_ORDER[i]
        local v = t[key]
        -- A KEY THE TABLE DOES NOT HOLD IS ITS DEFAULT, NEVER 0: for a switch
        -- 0 is OFF, and a table built before the key existed is exactly what an
        -- older save hands this.
        if v == nil then v = IC.TUNE_DEFAULTS[key] end
        if v == true then v = 1 elseif v == false then v = 0 end
        parts[i] = tostring(v)
    end
    return table.concat(parts, "|")
end

function IC.unpack_tune(packed)
    local t, i = {}, 1
    for k, v in pairs(IC.TUNE_DEFAULTS) do t[k] = v end
    for chunk in string.gmatch(packed or "", "[^|]+") do
        local key = IC.TUNE_ORDER[i]
        local n = tonumber(chunk)
        -- AN UNREADABLE FIELD STAYS ON ITS DEFAULT - a switch included, which
        -- must not read as off - and a field past the end is a later build's.
        if key and n ~= nil then
            if type(IC.TUNE_DEFAULTS[key]) == "boolean" then
                t[key] = n ~= 0
            else
                t[key] = n
            end
        end
        i = i + 1
    end
    return t
end

function IC.apply_tune(t)
    for i = 1, #IC.TUNE_ORDER do
        local key = IC.TUNE_ORDER[i]
        if t[key] ~= nil then IC.TUNE[key] = t[key] end
    end
    -- THE ONE COPY TAKEN AT LOAD: the parties file copies this line into the
    -- two intrigue moves, so it is written through to them here.
    for _, move in ipairs(IC.PARTY_MOVES or {}) do
        if move.key == "discredit" or move.key == "rumour" then
            move.line = IC.TUNE.party_intrigue_line
        end
    end
end

-- THE SETTINGS, FROZEN INTO THE SAVE ONCE. First thing at every first tick. A
-- save holding derpy_ic_tuned plays on it; one without (a new campaign, or a
-- save from before this build) reads MCT now and keeps the answer for good.
-- MCT has already read the player's choices by then, in its own LoadingGame
-- callback (groovy_mct.pack, registry/main.lua, Registry:load).
function IC.freeze_tune()
    local packed = cm:get_saved_value("derpy_ic_tuned")
    local t
    if type(packed) == "string" and packed ~= "" then
        t = IC.unpack_tune(packed)
    else
        t = IC.read_mct_or_defaults()
        cm:set_saved_value("derpy_ic_tuned", IC.pack_tune(t))
    end
    IC.apply_tune(t)
    return t
end

IC.AMBITION_ORDER = {"cautious", "steady", "ambitious"}
```

- [ ] **Step 6: Name the first tick and freeze first**

In `zzz_derpy_iron_court.lua`, replace:

```lua
cm:add_first_tick_callback(function()
    IC.register()
    IC.rebel_rename_all()
```

with:

```lua
-- THE MODEL'S FIRST TICK, named so the harness can drive it: the harness's cm
-- keeps only the last first-tick callback added, which is the panel's.
function IC.first_tick()
    -- FIRST: a new campaign rolls the player's court below, on these numbers.
    IC.freeze_tune()
    IC.register()
    IC.rebel_rename_all()
```

Then replace the last lines of the file:

```lua
            IC.stamp_court(human[i])
            IC.reconcile_houses(human[i])
            IC.ensure_leaders(human[i])
        end
    end
end)
```

with:

```lua
            IC.stamp_court(human[i])
            IC.reconcile_houses(human[i])
            IC.ensure_leaders(human[i])
        end
    end
end

cm:add_first_tick_callback(function() IC.first_tick() end)
```

- [ ] **Step 7: Run the harness and watch it pass**

```bash
cd "/g/Modding for resources"
"/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | tail -3
"/c/Program Files (x86)/Lua/5.1/luac.exe" -p "Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua" "Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_parties.lua" && echo parses
```

Expected: `iron court harness: ok (605 checks)` and `parses`. If "a new campaign rolls the player's court" fails with a house count other than 2, print the slugs in `IC.court(F).houses`. If a house other than the Crown and the one rival came from `IC.reconcile_houses` or `IC.ensure_leaders`, the fixture needs a courtier the reconcile keeps. Do not change the assertion.

- [ ] **Step 8: Record the checkpoint**

No commit (not a git repo). Note in the ledger: `Task 1: harness 605 green`.

---

### Task 2: The six switches, and failures that are always written

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua` (`IC.say` near line 151; the no-leader line near 1244; the rebel-army line near 2522; `IC.is_chd` near 943; `IC.tick_pressure` near 2198; `IC.splinter` near 2721; `IC.tick_secession` near 2789; the parties' turn failure line near 3628; `IC.register` near 3951)
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_parties.lua` (`IC.issue_demand` near 618; `IC.party_turn` near 1030)
- Test: `tools/_iron_court_harness.lua`

**Interfaces:**
- Consumes (Task 1): `IC.TUNE_DEFAULTS`, `IC.pack_tune`, `IC.freeze_tune`, `IC.apply_tune`, and the six `IC.TUNE` switches.
- Produces:
  - `IC.warn(text)`: always written.
  - `IC.say(text)`: silent when `IC.TUNE.detailed_log == false`.
  - `IC.runs_court(faction_interface) -> boolean`.
  - Harness helper `with_frozen(changes, fn)`.
  - The harness's `IC_PARTY_FAULTS` collector now wraps `IC.warn`.

- [ ] **Step 1: Write the failing checks**

Insert below Task 1's checks (still above `check("no parties' turn failed anywhere in the run", ...)`):

```lua
-- SETTINGS AS A SAVE HOLDS THEM: `changes` over the defaults, packed into
-- derpy_ic_tuned and frozen through IC.freeze_tune - never by writing IC.TUNE
-- directly, which is how a switch that was never registered passed its test
-- in the Great Guilds (2026-09-12).
local function with_frozen(changes, fn)
    local t = {}
    for k, v in pairs(IC.TUNE_DEFAULTS) do t[k] = v end
    for k, v in pairs(changes) do t[k] = v end
    saved["derpy_ic_tuned"] = IC.pack_tune(t)
    IC.freeze_tune()
    local ok, err = pcall(fn)
    saved["derpy_ic_tuned"] = nil
    IC.apply_tune(IC.TUNE_DEFAULTS)
    if not ok then error(err, 0) end
end

check("with parties_act off a party starts nothing new", function()
    -- THE SAME COURT ACTS WITH THE SETTING ON, measured first, so the off case
    -- is not passing on a court that would never have acted.
    party_court({legion = 5}, "all")
    local acted = IC.party_turn(F)
    assert(acted, "the fixture's court does not act even with the setting on")
    with_frozen({parties_act = false}, function()
        party_court({legion = 5}, "all")
        local done = IC.party_turn(F)
        local a = IC.agenda(F)
        assert(done == nil, "a party acted with parties_act off: " .. tostring(done))
        assert(a.plot == nil and a.demand == nil, "something new was opened")
    end)
    use_acts(BUILD1_ACTS)
    cm.get_human_factions = function() return {} end
end)

check("with ai_courts off an AI court is never rolled or run", function()
    IC.state = {}
    saved["derpy_ic_" .. F] = nil
    cm.get_human_factions = function() return {} end
    local f = make_faction(F, IC.CHD_SUBCULTURE,
                           {make_character(901, ANY_SEAT, nil, nil)}, {"prov_a"})
    IC.register()
    with_frozen({ai_courts = false}, function()
        core.listeners["ic_turn"]({faction = function() return f end})
        assert(not IC.court_rolled(F), "an AI court was rolled with ai_courts off")
    end)
    -- AND ON, the same listener rolls it, so the off case is not passing on a
    -- listener that never runs.
    core.listeners["ic_turn"]({faction = function() return f end})
    assert(IC.court_rolled(F), "the fixture's AI court is not rolled with the setting on")
end)

check("with ai_courts off an AI man earns nothing from a settlement and a player's still does", function()
    IC.state = {}
    local man = make_character(902, ANY_SEAT, nil, nil)
    make_faction(F, IC.CHD_SUBCULTURE, {man}, {})
    IC.add_house(F, IC.CROWN)
    IC.register()
    with_frozen({ai_courts = false}, function()
        cm.get_human_factions = function() return {} end
        core.listeners["ic_took"]({character = function() return man end})
        assert(IC.standing(F, 902) == 0,
            "an AI man earned " .. IC.standing(F, 902) .. " with ai_courts off")
        cm.get_human_factions = function() return {F} end
        core.listeners["ic_took"]({character = function() return man end})
        assert(IC.standing(F, 902) == IC.TUNE.settlement_influence,
            "a player's man earned " .. IC.standing(F, 902) .. " with ai_courts off")
    end)
    cm.get_human_factions = function() return {} end
end)

check("with secession off an angry party never starts its countdown", function()
    cm.get_human_factions = function() return {F} end
    local on = angry_court()
    IC.tick_secession(F)
    assert((on.houses.legion.clock or 0) > 0, "the fixture starts no countdown with the setting on")
    with_frozen({secession = false}, function()
        local court = angry_court()
        shown = {}
        for _ = 1, IC.TUNE.secede_turns + 2 do IC.tick_secession(F) end
        assert(court.houses.legion, "the legion seceded with secession off")
        assert((court.houses.legion.clock or 0) == 0,
            "a countdown ran: " .. tostring(court.houses.legion.clock))
        assert(#shown == 0, #shown .. " warning card(s) raised with secession off")
    end)
    cm.get_human_factions = function() return {} end
end)

check("with pressure off a weak Crown presses nobody", function()
    local function weak_court()
        IC.state = {}
        make_faction(F, IC.CHD_SUBCULTURE, {}, {})
        IC.add_house(F, IC.CROWN)
        IC.add_house(F, "forge")
        IC.add_house(F, "chain")
        local court = IC.court(F)
        court.houses[IC.CROWN].weight = 5
        court.houses["forge"].weight = 30
        court.houses["chain"].weight = 65
        return court
    end
    cm.get_human_factions = function() return {F} end
    local on = weak_court()
    rng({1})
    IC.tick_pressure(F)
    rng(nil)
    assert(on.houses["chain"].pressed, "the fixture presses nobody with the setting on")
    with_frozen({pressure = false}, function()
        local court = weak_court()
        court.houses["chain"].pressed = true   -- a press left over from before
        rng({1})
        local chance = IC.tick_pressure(F)
        rng(nil)
        assert(chance == 0, "the pressure rolled at " .. tostring(chance))
        assert(not court.houses["chain"].pressed, "the biggest party is pressed with pressure off")
    end)
    cm.get_human_factions = function() return {} end
end)

check("with crown_split off the Crown never splits", function()
    crown_at(0)
    assert(split_out(F), "the fixture's Crown does not split with the setting on")
    with_frozen({crown_split = false}, function()
        crown_at(0)
        local slug = split_out(F)
        assert(slug == nil, "the Crown split into " .. tostring(slug) .. " with crown_split off")
    end)
end)

check("with detailed_log off routine lines stop and failures are still written", function()
    with_frozen({detailed_log = false}, function()
        logged = {}
        IC.say("IRON COURT: a routine line")
        IC.warn("IRON COURT: a failure line")
        local routine, failure = false, false
        for i = 1, #logged do
            if string.find(logged[i], "a routine line", 1, true) then routine = true end
            if string.find(logged[i], "a failure line", 1, true) then failure = true end
        end
        assert(not routine, "a routine line was written with the detailed log off")
        assert(failure, "a failure was silenced with the detailed log")
        -- AND THE FAILURE THE TURN CATCHES, through the real turn.
        party_court({legion = 40, forge = 80})
        local was = IC.party_turn
        IC.party_turn = function() error("the parties broke") end
        logged = {}
        local ok = pcall(IC.turn, F)
        IC.party_turn = was
        IC_PARTY_FAULTS = {}
        cm.get_human_factions = function() return {} end
        local said = false
        for i = 1, #logged do
            if string.find(logged[i], "parties' turn failed", 1, true) then said = true end
        end
        assert(ok and said, "the parties' turn failure was not written with the detailed log off")
    end)
end)
```

- [ ] **Step 2: Run and watch them fail**

```bash
cd "/g/Modding for resources"
IC_TEST_ALL=1 "/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | grep -E "^FAIL|failing"
```

Expected: 7 `FAIL` lines. Six are `with ... off` assertions (for example "a party acted with parties_act off", "an AI court was rolled with ai_courts off"). The detailed_log check fails on "attempt to call field 'warn'". The summary reads `7 failing, 605 passing`.

- [ ] **Step 3: Split the log into `IC.say` and `IC.warn`**

In `zzz_derpy_iron_court.lua`, replace:

```lua
-- CA's `out` is a callable table, not a function. Keep the call isolated from turns.
function IC.say(text)
    if out then pcall(function() out(tostring(text)) end) end
end
```

with:

```lua
-- CA's `out` is a callable table, not a function. Keep the call isolated from turns.
-- IC.warn is a FAILURE and is always written. IC.say is the routine log, and the
-- detailed_log setting silences it - so a caught error must never go through it.
function IC.warn(text)
    if out then pcall(function() out(tostring(text)) end) end
end

function IC.say(text)
    if IC.TUNE and IC.TUNE.detailed_log == false then return end
    IC.warn(text)
end
```

Replace:

```lua
                IC.say("IRON COURT: " .. tostring(slug) .. " in " .. faction_key
                       .. " has no leader - " .. (ok and ("a " .. subtype
```

with:

```lua
                -- A LORD THAT COULD NOT BE MADE is a failure; one waiting is not.
                local log = ok and IC.say or IC.warn
                log("IRON COURT: " .. tostring(slug) .. " in " .. faction_key
                       .. " has no leader - " .. (ok and ("a " .. subtype
```

Replace `        IC.say("IRON COURT: the rebel army did not spawn - " .. tostring(err))` with `        IC.warn("IRON COURT: the rebel army did not spawn - " .. tostring(err))`.

Replace `            IC.say("IRON COURT: the parties' turn failed in " .. faction_key` with `            IC.warn("IRON COURT: the parties' turn failed in " .. faction_key`.

In `zzz_derpy_iron_court_parties.lua`, replace `        IC.say("IRON COURT: demand not issued in " .. faction_key .. ": "` with `        IC.warn("IRON COURT: demand not issued in " .. faction_key .. ": "`.

- [ ] **Step 4: Point the harness's failure collector at `IC.warn`**

In `tools/_iron_court_harness.lua`, replace:

```lua
IC_PARTY_FAULTS = {}
do
    local say = IC.say
    IC.say = function(text)
        if string.find(tostring(text), "parties' turn failed", 1, true) then
            IC_PARTY_FAULTS[#IC_PARTY_FAULTS + 1] = tostring(text)
        end
        return say(text)
    end
end
```

with:

```lua
IC_PARTY_FAULTS = {}
do
    -- IC.warn, WHICH IC.say ALSO GOES THROUGH, so this sees both logs. The
    -- failure line is IC.warn's since 2026-09-25 and has to be watched whatever
    -- the detailed_log setting says.
    local warn = IC.warn
    IC.warn = function(text)
        if string.find(tostring(text), "parties' turn failed", 1, true) then
            IC_PARTY_FAULTS[#IC_PARTY_FAULTS + 1] = tostring(text)
        end
        return warn(text)
    end
end
```

- [ ] **Step 5: `ai_courts`, one predicate for the turn and the five event listeners**

In `zzz_derpy_iron_court.lua`, replace:

```lua
function IC.is_chd(faction)
    if not faction or faction:is_null_interface() then return false end
    return faction:subculture() == IC.CHD_SUBCULTURE
end
```

with:

```lua
function IC.is_chd(faction)
    if not faction or faction:is_null_interface() then return false end
    return faction:subculture() == IC.CHD_SUBCULTURE
end

-- A CHAOS DWARF FACTION WHOSE COURT THIS CAMPAIGN RUNS. With the ai_courts
-- setting off, a player's only: an AI court is never rolled, ticked or fed.
function IC.runs_court(faction)
    if not IC.is_chd(faction) then return false end
    if IC.TUNE.ai_courts then return true end
    return IC.is_human(faction:name())
end
```

First confirm the line below occurs exactly 5 times, all inside `IC.register`:

```bash
cd "/g/Modding for resources"
grep -n "        if not IC.is_chd(faction) then return end" "Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua"
```

Expected: 5 lines, all between `function IC.register()` and the first-tick function. Then replace all 5 (Edit with `replace_all: true`) `        if not IC.is_chd(faction) then return end` with `        if not IC.runs_court(faction) then return end`. Also replace `        if not IC.is_chd(host) then return end` with `        if not IC.runs_court(host) then return end`.

- [ ] **Step 6: The `pressure`, `crown_split` and `secession` guards**

Replace:

```lua
    if not IC.is_human(faction_key) then
        for _slug, house in pairs(court.houses) do house.pressed = nil end
```

with:

```lua
    -- AND NOBODY'S AT ALL with the pressure setting off.
    if not IC.TUNE.pressure or not IC.is_human(faction_key) then
        for _slug, house in pairs(court.houses) do house.pressed = nil end
```

Replace:

```lua
function IC.splinter(faction_key)
    local court = IC.court(faction_key)
    local crown = court.houses[IC.CROWN]
```

with:

```lua
function IC.splinter(faction_key)
    -- THE crown_split SETTING OFF: the Crown never splits, and gives no notice.
    if not IC.TUNE.crown_split then return nil end
    local court = IC.court(faction_key)
    local crown = court.houses[IC.CROWN]
```

Replace:

```lua
function IC.tick_secession(faction_key)
    local court = IC.court(faction_key)
    local own = IC.CROWN
```

with:

```lua
function IC.tick_secession(faction_key)
    local court = IC.court(faction_key)
    -- THE secession SETTING OFF: no countdown runs, so nothing is warned and
    -- nobody leaves. A clock already running from before is stopped.
    if not IC.TUNE.secession then
        for _slug, house in pairs(court.houses) do house.clock = 0 end
        return {}
    end
    local own = IC.CROWN
```

- [ ] **Step 7: The `parties_act` guard**

In `zzz_derpy_iron_court_parties.lua`, replace:

```lua
        IC.save(faction_key)
        return done
    end
    local picks = {}
```

with:

```lua
        IC.save(faction_key)
        return done
    end
    -- THE parties_act SETTING OFF: what is already open settles above, and
    -- nothing new - no scheme, feud, demand or offer - is started.
    if not T.parties_act then
        IC.save_agenda(faction_key)
        IC.save(faction_key)
        return nil
    end
    local picks = {}
```

- [ ] **Step 8: Run and watch it pass**

```bash
cd "/g/Modding for resources"
"/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | tail -3
"/c/Program Files (x86)/Lua/5.1/luac.exe" -p "Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua" "Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_parties.lua" && echo parses
```

Expected: `iron court harness: ok (612 checks)` and `parses`.

- [ ] **Step 9: Record the checkpoint**

Ledger: `Task 2: harness 612 green`.

---

### Task 3: The MCT settings page

**Files:**
- Create: `Modding Files/pack/script/mct/settings/derpy_iron_court.lua`
- Test: `tools/_iron_court_harness.lua`

**Interfaces:**
- Consumes (Task 1): `IC.TUNE_ORDER`, `IC.TUNE_DEFAULTS`, `IC.PRESETS`, `IC.PRESET_CUSTOM`.
- Produces:
  - The MCT page `derpy_iron_court`.
  - Option keys: `preset` (dropdown `gentle`/`default`/`harsh`/`ruthless`/`custom`,
    default `default`), plus the 20 `IC.TUNE_ORDER` keys (checkboxes for the booleans,
    sliders for the numbers).
  - Harness helper `load_mct_file(in_campaign) -> opts, registered_key`.

- [ ] **Step 1: Write the failing checks**

Insert below Task 2's checks:

```lua
-- THE REAL SETTINGS FILE, run against a recording MCT. What it registers is held
-- against IC.TUNE, IC.TUNE_ORDER and IC.PRESETS - the other places a setting has
-- to be named before its control does anything.
local MCT_FILE = "Modding Files/pack/script/mct/settings/derpy_iron_court.lua"
local function load_mct_file(in_campaign)
    local opts = {}
    local option_methods = {
        set_text = function() end,
        set_tooltip_text = function() end,
        add_option_set_callback = function() end,
        set_assigned_section = function(o, s) o.section = s end,
        slider_set_min_max = function(o, lo, hi) o.lo, o.hi = lo, hi end,
        slider_set_step_size = function(o, step) o.step = step end,
        set_default_value = function(o, v) o.default = v end,
        set_locked = function(o, on) o.locked = on end,
        add_dropdown_value = function(o, key, _text, _tip, is_default)
            o.values[#o.values + 1] = key
            if is_default then o.default = key end
        end,
        get_finalized_setting = function(o) return o.default end,
        get_selected_setting = function(o) return o.default end,
    }
    local mod = setmetatable({}, {__index = function() return function() end end})
    mod.add_new_option = function(_, key, kind)
        local o = setmetatable({key = key, kind = kind, values = {}},
                               {__index = option_methods})
        opts[key] = o
        return o
    end
    mod.get_option_by_key = function(_, key) return opts[key] end
    get_mct = function()
        return {register_mod = function(_, key) mod.registered = key return mod end}
    end
    __lib_type_campaign = "campaign"
    __game_mode = in_campaign and "campaign" or "frontend"
    local chunk, err = loadfile(MCT_FILE)
    local ok = chunk ~= nil
    if ok then ok, err = pcall(chunk) end
    get_mct, __game_mode, __lib_type_campaign = nil, nil, nil
    assert(ok, "the MCT settings file did not run: " .. tostring(err))
    return opts, mod.registered
end

check("every setting is registered in MCT, in the save order and with its default", function()
    local opts, registered = load_mct_file(false)
    assert(registered == "derpy_iron_court", "the page registers as "
        .. tostring(registered) .. ", and IC.read_mct_or_defaults asks for derpy_iron_court")
    local ordered = {}
    for _, key in ipairs(IC.TUNE_ORDER) do
        ordered[key] = true
        local o = opts[key]
        local d = IC.TUNE_DEFAULTS[key]
        assert(d ~= nil, key .. " is in IC.TUNE_ORDER with no default in IC.TUNE")
        assert(o, key .. " is in IC.TUNE_ORDER and not on the MCT page")
        local want = type(d) == "boolean" and "checkbox" or "slider"
        assert(o.kind == want, key .. " is a " .. tostring(o.kind) .. " and its default wants a " .. want)
        assert(o.default == d, key .. " defaults to " .. tostring(o.default)
            .. " in MCT and " .. tostring(d) .. " in IC.TUNE")
        assert(o.section, key .. " has no section, so MCT files it where the player may never look")
    end
    for key in pairs(opts) do
        assert(key == "preset" or ordered[key],
            key .. " is on the MCT page and in no IC.TUNE_ORDER, so it changes nothing")
    end
end)

check("every difficulty's numbers sit inside their sliders", function()
    local opts = load_mct_file(false)
    local p = opts["preset"]
    assert(p and p.kind == "dropdown", "the page has no difficulty dropdown")
    assert(p.default == "default", "the difficulty defaults to " .. tostring(p.default))
    local listed, n_presets = {}, 0
    for _, v in ipairs(p.values) do listed[v] = true end
    for name in pairs(IC.PRESETS) do
        n_presets = n_presets + 1
        assert(listed[name], name .. " is a difficulty MCT does not offer")
    end
    assert(listed["default"] and listed[IC.PRESET_CUSTOM], "Default or Custom is missing")
    assert(#p.values == n_presets + 2, "MCT offers a difficulty IC.PRESETS does not define")
    local function on_slider(o, v, what)
        local step = o.step or 1
        assert(v >= o.lo and v <= o.hi, what .. " = " .. v .. " is outside "
            .. o.lo .. " to " .. o.hi)
        assert((v - o.lo) % step == 0, what .. " = " .. v .. " is off the slider's step of " .. step)
    end
    for name, preset in pairs(IC.PRESETS) do
        for key, v in pairs(preset) do on_slider(opts[key], v, name .. " " .. key) end
    end
    for _, key in ipairs(IC.TUNE_ORDER) do
        if opts[key].kind == "slider" then
            on_slider(opts[key], IC.TUNE_DEFAULTS[key], "the default " .. key)
        end
    end
end)

check("in a campaign every setting on the page is locked", function()
    -- MCT HAS NO CAMPAIGN GATING OF ITS OWN; the lock is the only notice the
    -- player gets that a change made now does nothing to this save.
    local opts = load_mct_file(true)
    for key, o in pairs(opts) do
        assert(o.locked == true, key .. " can be changed in a running campaign")
    end
end)
```

- [ ] **Step 2: Run and watch them fail**

```bash
cd "/g/Modding for resources"
IC_TEST_ALL=1 "/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | grep -E "^FAIL|failing"
```

Expected: 3 `FAIL` lines, each "the MCT settings file did not run: cannot open ...", then `3 failing, 612 passing`.

- [ ] **Step 3: Write the settings file**

Create `Modding Files/pack/script/mct/settings/derpy_iron_court.lua`:

```lua
-- MCT registration for The Iron Court.
--
-- MCT loads every .lua under script/mct/settings/, so this file runs only when
-- MCT is installed, and in MCT's own environment: it cannot see IC, and calls
-- nothing in the mod. The campaign reads these values once, at the first tick
-- of a new campaign (or the first load of a save from before this page
-- existed), and freezes them into the save - see IC.freeze_tune. In
-- multiplayer it does not read them at all.
--
-- EVERY KEY HERE IS REGISTERED TWICE MORE, in IC.TUNE and IC.TUNE_ORDER in
-- zzz_derpy_iron_court.lua. The court harness runs this file and refuses a key
-- missing from either, a default that disagrees, and a preset off its slider.

local mct = get_mct and get_mct()
if not mct then return end

local m = mct:register_mod("derpy_iron_court")
m:set_title("The Iron Court")
m:set_author("derpy")
m:set_description("Parties vie for the offices of your court. These values are "
    .. "read once, when a campaign starts, and are then fixed for the life of "
    .. "that save - change them from the main menu before starting a new one. "
    .. "They are not used in multiplayer, where every player gets the defaults.")

-- MCT HAS NO CAMPAIGN GATING OF ITS OWN: set_context_specific is an empty
-- function. The copy frozen into the save is the real defence; the lock is the
-- notice.
local IN_CAMPAIGN = __game_mode == __lib_type_campaign
local LOCK_REASON = "Fixed for the life of a campaign. Change it from the main "
    .. "menu before starting a new one."

m:add_new_section("preset", "Difficulty")
m:add_new_section("systems", "Systems")
m:add_new_section("numbers", "Custom numbers")
m:add_new_section("debug", "Debug")

-- ----------------------------------------------------------------- difficulty --
-- ONE DROPDOWN THAT OWNS THE NUMBERS. Pick anything but Custom and it sets all
-- fourteen and greys them. The switches are read on every difficulty.
local o_preset = m:add_new_option("preset", "dropdown")
o_preset:set_text("Difficulty")
o_preset:set_tooltip_text("How loyal the parties are and how quickly they turn. "
    .. "Choose Custom to set each number yourself. The switches under Systems are "
    .. "yours on every difficulty.")
o_preset:set_assigned_section("preset")
o_preset:add_dropdown_value("gentle", "Gentle",
    "Parties start more loyal, cool more slowly and give longer warning before "
    .. "they leave. Gifts cost less, and influence comes faster.", false)
o_preset:add_dropdown_value("default", "Default",
    "The Iron Court as designed.", true)
o_preset:add_dropdown_value("harsh", "Harsh",
    "Parties start less loyal and leave sooner, a weak Crown loses its rivals "
    .. "sooner, and influence and favours cost more.", false)
o_preset:add_dropdown_value("ruthless", "Ruthless",
    "Every party is a threat. Loyalty falls fast, a party gives three turns of "
    .. "warning before it leaves, and every favour is dear.", false)
o_preset:add_dropdown_value("custom", "Custom",
    "Set every number under Custom numbers yourself.", false)
o_preset:set_default_value("default")

-- ------------------------------------------------------------------- systems --
-- key, label, section, tooltip. Every switch defaults to on.
local SWITCHES = {
    {"parties_act", "Rival parties act on their own", "systems",
     "Parties scheme, feud, make demands and offer deals without being asked. "
     .. "Off, they do none of this; overseers still gain experience and anything "
     .. "already under way still settles."},
    {"ai_courts", "Other Chaos Dwarf factions have courts", "systems",
     "Chaos Dwarf factions you do not play run courts of their own, and theirs "
     .. "can split. Off, only your court runs."},
    {"secession", "Parties can secede", "systems",
     "A powerful, angry party counts down and then leaves, taking provinces with "
     .. "it. Off, no party ever leaves."},
    {"pressure", "A weak Crown pushes rivals out", "systems",
     "When your own party's share of the court falls too low, the biggest rival "
     .. "party is pushed to leave. Off, it never is."},
    {"crown_split", "Your own party can split", "systems",
     "A Crown whose loyalty runs out splits into a new party. Off, it never does."},
    {"detailed_log", "Detailed log", "debug",
     "Writes the court's routine events to script_log.txt. Failures are always "
     .. "written."},
}

for i = 1, #SWITCHES do
    local key, label, section, tip = unpack(SWITCHES[i])
    local o = m:add_new_option(key, "checkbox")
    o:set_text(label)
    o:set_tooltip_text(tip)
    o:set_default_value(true)
    o:set_assigned_section(section)
    if IN_CAMPAIGN then o:set_locked(true, LOCK_REASON) end
end

-- ------------------------------------------------------------------- numbers --
-- key, label, default, min, max, step, tooltip. The defaults are IC.TUNE's.
local NUMBERS = {
    {"loyalty_start", "Starting loyalty", 55, 30, 80, 1,
     "The loyalty a party has when it first takes its place at court."},
    {"loyalty_drift_none", "Loyalty change each turn for a party with no office",
     -1, -5, 0, 1,
     "What a party that holds no office loses every turn."},
    {"secede_loyalty", "Loyalty at which a party threatens to leave", 20, 0, 40, 1,
     "A party big enough to leave starts counting down at or below this loyalty."},
    {"secede_share", "Share of the court a party needs to leave", 25, 5, 50, 1,
     "The share of the court, in percent, a party must hold before it can leave."},
    {"secede_turns", "Turns of warning before a party leaves", 5, 1, 10, 1,
     "How many turns the countdown runs."},
    {"pressure_below", "Crown share below which rivals are pushed out", 10, 0, 30, 1,
     "When your own party's share of the court falls below this, the biggest "
     .. "rival party can be pushed to leave."},
    {"influence_trickle", "Influence a man earns each turn", 5, 0, 20, 1,
     "The influence a man earns every turn while he is not leading an army."},
    {"settlement_influence", "Influence for taking a settlement", 24, 0, 60, 1,
     "The influence a lord earns for taking a settlement."},
    {"favour_gift_cost", "Price of Send a Gift", 600, 100, 3000, 50,
     "Gold for one gift to a party."},
    {"favour_secure_cost", "Price of Secure Loyalty", 2500, 500, 10000, 100,
     "Gold to hold a party back from leaving for a few turns."},
    {"party_intrigue_line", "Loyalty at which parties start scheming", 55, 20, 80, 1,
     "A party at or below this loyalty spreads rumours about your men and "
     .. "discredits them."},
    {"rivals_min", "Fewest rival parties", 2, 1, 4, 1,
     "The fewest rival parties a new court starts with."},
    {"rivals_max", "Most rival parties", 4, 1, 4, 1,
     "The most rival parties a new court starts with. Four at most: there are "
     .. "four rebel banners for a party to rise under."},
    {"term_turns", "Office term, in turns", 5, 2, 10, 1,
     "How many turns an appointment runs. Dismissing a man before his term is up "
     .. "angers his party."},
}

for i = 1, #NUMBERS do
    local key, label, def, lo, hi, step, tip = unpack(NUMBERS[i])
    local o = m:add_new_option(key, "slider")
    o:set_text(label)
    o:set_tooltip_text(tip)
    o:slider_set_min_max(lo, hi)
    o:slider_set_step_size(step)
    o:set_default_value(def)
    o:set_assigned_section("numbers")
end

-- ------------------------------------------------------- locking the numbers --
-- LAST: get_option_by_key answers nil for an option not yet registered, and the
-- loop below would then lock nothing. Every number belongs to the difficulty
-- unless it is Custom.
local CUSTOM_ONLY = "Set by the difficulty above. Choose Custom to edit it."

local function relock(custom)
    for i = 1, #NUMBERS do
        local o = m:get_option_by_key(NUMBERS[i][1])
        if o then
            if IN_CAMPAIGN then
                o:set_locked(true, LOCK_REASON)
            elseif not custom then
                o:set_locked(true, CUSTOM_ONLY)
            else
                o:set_locked(false)
            end
        end
    end
    if IN_CAMPAIGN then o_preset:set_locked(true, LOCK_REASON) end
end

-- The callback fires BEFORE the value is finalized, so it reads the selected one.
o_preset:add_option_set_callback(function(opt)
    if IN_CAMPAIGN then return end
    relock(opt:get_selected_setting() == "custom")
end)
core:add_listener("derpy_ic_mct_ready", "MctFinalized", true, function()
    relock(o_preset:get_finalized_setting() == "custom")
end, false)
relock(o_preset:get_finalized_setting() == "custom")
```

- [ ] **Step 4: Run and watch them pass**

```bash
cd "/g/Modding for resources"
"/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | tail -3
"/c/Program Files (x86)/Lua/5.1/luac.exe" -p "Modding Files/pack/script/mct/settings/derpy_iron_court.lua" && echo parses
```

Expected: `iron court harness: ok (615 checks)` and `parses`.

- [ ] **Step 5: Record the checkpoint**

Ledger: `Task 3: harness 615 green`.

---

### Task 4: The multiplayer transport

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua` (`IC.hold_feed` near line 593; insert the transport directly above `function IC.register()`; the first listener inside `IC.register`)
- Test: `tools/_iron_court_harness.lua` (the `make_faction` stub, and new checks)

**Interfaces:**
- Consumes (Tasks 1-2): `IC.is_mp()`, `IC.warn(text)`.
- Produces:
  - `IC.MP_TAG = "ic1"`, `IC.MP_MAX = 100`.
  - `IC.MP_OPS[op](faction_key, arg)`, returning the model's `done, why, spare`.
  - `IC.faction_by_cqi(cqi) -> faction_key | nil`.
  - `IC.mp_send(faction_key, op, arg)`.
  - `IC.mp_receive(id, cqi) -> faction_key | nil`.
  - The listener `ic_mp` on `UITrigger`.
  - The hook contract `IC.after_op(faction_key, op, arg, done, why, spare)`: optional,
    called at the end of every op.
  - The eleven op names and their wire arguments:

    | op | arg |
    |---|---|
    | `appoint` | `office\|cqi` |
    | `dismiss` | `office` |
    | `gov` | `province\|cqi` |
    | `ungov` | `province` |
    | `plot` | `plot\|actor_cqi\|target` |
    | `favour` | `favour\|party` |
    | `hire` | `office\|index` |
    | `grant` | `""` |
    | `refuse` | `""` |
    | `accept` | `party` |
    | `decline` | `party` |

  - Harness helpers: `with_mp(local_faction, fn(sent))` and `deliver(msg)`; the faction stub
    gains `command_queue_index()` backed by `f._cqi`.

- [ ] **Step 1: Give the faction stub its command queue index**

In `tools/_iron_court_harness.lua`, inside `make_faction`, replace:

```lua
        treasury = function() return f._gold or 0 end,
```

with:

```lua
        treasury = function() return f._gold or 0 end,
        -- THE CQI A UITrigger CARRIES. Documented on FACTION_SCRIPT_INTERFACE;
        -- a check that sends sets _cqi, everything else answers 0.
        command_queue_index = function() return f._cqi end,
```

and in the same table replace `        _gold = 0,` with:

```lua
        _gold = 0,
        _cqi = 0,
```

- [ ] **Step 2: Write the failing checks**

Insert below Task 3's checks:

```lua
-- MULTIPLAYER FOR THE LENGTH OF fn. `local_faction` is what the forced
-- local-faction read answers on this machine (the unforced one throws, as the
-- engine's does). Every trigger sent is kept in `sent` for the check to
-- deliver, or not, through the real ic_mp listener.
local function with_mp(local_faction, fn)
    local sent = {}
    cm.is_multiplayer = function() return true end
    cm.get_local_faction_name = function(_, force)
        if force ~= true then error("unforced local-faction read in multiplayer") end
        return local_faction
    end
    CampaignUI = {TriggerCampaignScriptEvent = function(cqi, id)
        sent[#sent + 1] = {cqi = cqi, id = id}
    end}
    local ok, err = pcall(fn, sent)
    cm.is_multiplayer, cm.get_local_faction_name, CampaignUI = nil, nil, nil
    if not ok then error(err, 0) end
end

-- THE TRIGGER COMING BACK, as it does on every machine, through the listener
-- IC.register installed.
local function deliver(msg)
    core.listeners["ic_mp"]({
        trigger = function() return msg.id end,
        faction_cqi = function() return msg.cqi end,
    })
end

check("in single player an action runs at once and its answer comes straight back", function()
    local calls = 0
    local was_f, was_a = IC.favour, IC.after_op
    IC.favour = function() calls = calls + 1 return false, "gold", 300 end
    local got = {}
    IC.after_op = function(...) got[#got + 1] = {...} end
    local ok, err = pcall(IC.mp_send, F, "favour", "gift|legion")
    IC.favour, IC.after_op = was_f, was_a
    assert(ok, "mp_send raised: " .. tostring(err))
    assert(calls == 1, "the action ran " .. calls .. " times")
    local a = got[1]
    assert(a and a[1] == F and a[2] == "favour" and a[3] == "gift|legion"
        and a[4] == false and a[5] == "gold" and a[6] == 300,
        "the answer arrived as " .. (a and table.concat({tostring(a[1]), tostring(a[2]),
        tostring(a[3]), tostring(a[4]), tostring(a[5]), tostring(a[6])}, ", ") or "nothing"))
end)

check("each of the eleven actions waits for its trigger, then reaches the model as the panel called it", function()
    -- {op, wire argument, model function, argument count, what the panel passes}
    local cases = {
        {"appoint", "warden|501", "appoint", 2, {"warden", 501}},
        {"dismiss", "warden", "dismiss", 1, {"warden"}},
        {"gov", "prov_a|501", "assign_governor", 2, {"prov_a", 501}},
        {"ungov", "prov_a", "release_governor", 1, {"prov_a"}},
        {"plot", "bribe|501|502", "plot", 3, {"bribe", 501, "502"}},
        {"plot", "feast|501|", "plot", 3, {"feast", 501, nil}},
        {"favour", "gift|legion", "favour", 2, {"gift", "legion"}},
        {"hire", "warden|2", "hire", 2, {"warden", 2}},
        {"grant", "", "grant_demand", 0, {}},
        {"refuse", "", "refuse_demand", 0, {}},
        {"accept", "legion", "accept_offer", 1, {"legion"}},
        {"decline", "legion", "decline_offer", 1, {"legion"}},
    }
    local n_ops = 0
    for _ in pairs(IC.MP_OPS) do n_ops = n_ops + 1 end
    assert(n_ops == 11, "IC.MP_OPS holds " .. n_ops .. " actions; the panel has eleven")
    IC.state = {}
    local f = make_faction(F, IC.CHD_SUBCULTURE, {}, {})
    f._cqi = 41
    cm.get_human_factions = function() return {F} end
    IC.register()
    local failed = nil
    for _, c in ipairs(cases) do
        local op, arg, name, n, want = c[1], c[2], c[3], c[4], c[5]
        local got = nil
        local was = IC[name]
        IC[name] = function(...) got = {n = select("#", ...), ...} return true end
        local ok, err = pcall(with_mp, "someone_else", function(sent)
            IC.mp_send(F, op, arg)
            assert(got == nil, op .. " ran on the sending machine before its trigger came back")
            assert(#sent == 1, op .. " sent " .. #sent .. " triggers")
            assert(sent[1].cqi == 41, op .. " was sent for cqi " .. tostring(sent[1].cqi))
            deliver(sent[1])
            assert(got, op .. " came back and never reached IC." .. name)
            assert(got[1] == F, op .. " acted for " .. tostring(got[1]))
            for i = 1, n do
                assert(got[i + 1] == want[i] and type(got[i + 1]) == type(want[i]),
                    op .. " argument " .. i .. " arrived as " .. type(got[i + 1]) .. " "
                    .. tostring(got[i + 1]) .. "; the panel passes " .. type(want[i]) .. " "
                    .. tostring(want[i]))
            end
        end)
        IC[name] = was
        if not ok then failed = err break end
    end
    cm.get_human_factions = function() return {} end
    if failed then error(failed, 0) end
end)

check("in multiplayer a dismissal waits for its trigger and then empties the office", function()
    IC.state = {}
    turn = 1
    local f = make_faction(F, IC.CHD_SUBCULTURE, {make_character(501, ANY_SEAT, "forge")}, {})
    f._cqi = 41
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "forge")
    cm.get_human_factions = function() return {F} end
    IC.register()
    local office = IC.OFFICES[1].slug
    IC.court(F).offices[office] = 501
    local ok, err = pcall(with_mp, "someone_else", function(sent)
        IC.mp_send(F, "dismiss", office)
        assert(IC.court(F).offices[office] == 501, "dismissed before the trigger came back")
        deliver(sent[1])
        assert(IC.court(F).offices[office] == nil, "the trigger came back and he is still seated")
    end)
    cm.get_human_factions = function() return {} end
    if not ok then error(err, 0) end
end)

check("a trigger that is not ours, or from nobody we know, changes nothing", function()
    IC.state = {}
    local f = make_faction(F, IC.CHD_SUBCULTURE, {}, {})
    f._cqi = 41
    cm.get_human_factions = function() return {F} end
    IC.register()
    local called = 0
    local was = IC.dismiss
    IC.dismiss = function() called = called + 1 return true end
    local ok, err = pcall(with_mp, "someone_else", function()
        deliver({cqi = 999, id = "ic1|dismiss|warden"})    -- nobody we know
        deliver({cqi = 41, id = "gg1|dismiss|warden"})     -- another mod's
        deliver({cqi = 41, id = "ic1|nope|warden"})        -- no such action
        assert(IC.mp_receive("gg1|buy|x", 41) == nil, "another mod's trigger was claimed")
    end)
    IC.dismiss = was
    cm.get_human_factions = function() return {} end
    if not ok then error(err, 0) end
    assert(called == 0, "a stray trigger dismissed " .. called .. " time(s)")
end)

check("an action too long for one trigger is refused, not applied on this machine", function()
    IC.state = {}
    local f = make_faction(F, IC.CHD_SUBCULTURE, {}, {})
    f._cqi = 41
    local called = 0
    local was = IC.plot
    IC.plot = function() called = called + 1 return true end
    logged = {}
    local ok, err = pcall(with_mp, "someone_else", function(sent)
        IC.mp_send(F, "plot", "bribe|501|" .. string.rep("x", 100))
        assert(#sent == 0, #sent .. " over-long trigger(s) went out")
    end)
    IC.plot = was
    if not ok then error(err, 0) end
    assert(called == 0, "the refused action ran on this machine")
    local said = false
    for i = 1, #logged do
        if string.find(logged[i], "not sent", 1, true) then said = true end
    end
    assert(said, "the refusal was silent")
end)

check("an action for a faction with no command queue index is refused, not applied here", function()
    local called = 0
    local was = IC.dismiss
    IC.dismiss = function() called = called + 1 return true end
    local ok, err = pcall(with_mp, "someone_else", function(sent)
        IC.mp_send("no_such_faction_key", "dismiss", "warden")
        assert(#sent == 0, "a trigger went out with no cqi to carry")
    end)
    IC.dismiss = was
    if not ok then error(err, 0) end
    assert(called == 0, "the unsendable action ran on this machine")
end)

check("a trigger with a garbled number is refused by the model, not by an error", function()
    -- REVIEW FOCUS 4.
    IC.state = {}
    turn = 1
    local f = make_faction(F, IC.CHD_SUBCULTURE, {make_character(501, ANY_SEAT, "forge")}, {})
    f._cqi = 41
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "forge")
    endow(F)
    cm.get_human_factions = function() return {F} end
    IC.register()
    local office = IC.OFFICES[1].slug
    local got = {}
    local was = IC.after_op
    IC.after_op = function(...) got[#got + 1] = {...} end
    logged = {}
    local ok, err = pcall(with_mp, "someone_else", function()
        deliver({cqi = 41, id = "ic1|appoint|" .. office .. "|abc"})
    end)
    IC.after_op = was
    cm.get_human_factions = function() return {} end
    if not ok then error(err, 0) end
    for i = 1, #logged do
        assert(not string.find(logged[i], "UITrigger failed", 1, true),
            "the garbled trigger raised: " .. logged[i])
    end
    assert(IC.court(F).offices[office] == nil, "a garbled cqi was appointed")
    assert(got[1] and got[1][4] == false, "the refusal never reached the panel")
end)

check("in multiplayer the open panel holds no event card", function()
    -- The panel is open on one machine and not the other, so a hold would raise
    -- the model's event calls at two different times.
    party_court({legion = 40})
    local ok, err = pcall(with_mp, F, function()
        IC.hold_feed(true)
        assert(IC.feed_held == false, "the feed was held in multiplayer")
        IC.feed(F, "secede_warn")
        assert(#shown == 1, "the card waited behind one machine's panel")
    end)
    IC.hold_feed(false)
    IC.feed_held = false
    IC.feed_queue = {}
    cm.get_human_factions = function() return {} end
    if not ok then error(err, 0) end
end)
```

- [ ] **Step 3: Run and watch them fail**

```bash
cd "/g/Modding for resources"
IC_TEST_ALL=1 "/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | grep -E "^FAIL|failing"
```

Expected: 8 `FAIL` lines. Most fail on "attempt to call field 'mp_send'", "attempt to call field 'mp_receive'" or "attempt to index field 'MP_OPS'". The "holds no event card" check fails on "the feed was held in multiplayer". The summary reads `8 failing, 615 passing`.

- [ ] **Step 4: No feed hold in multiplayer**

In `zzz_derpy_iron_court.lua`, replace:

```lua
function IC.hold_feed(on)
    IC.feed_held = on and true or false
```

with:

```lua
function IC.hold_feed(on)
    -- NOT IN MULTIPLAYER. The panel is open on one machine and not the other,
    -- so a hold would raise the model's event calls at two different times.
    -- The cards show when they are raised, behind the panel or not.
    if IC.is_mp() then return 0 end
    IC.feed_held = on and true or false
```

- [ ] **Step 5: The transport and the eleven ops**

In `zzz_derpy_iron_court.lua`, replace:

```lua
function IC.register()
    core:add_listener("ic_turn", "FactionTurnStart", true, function(context)
```

with:

```lua
-- ---------------------------------------------------------------------------
-- MULTIPLAYER. A change to the campaign made on one machine and not the others
-- is a desync, so nothing the panel does changes the model straight off a click.
-- It goes through IC.mp_send, which in multiplayer broadcasts with
-- CampaignUI.TriggerCampaignScriptEvent. CA delivers the UITrigger to every
-- machine in one order, and IC.mp_receive runs the same op on all of them. The
-- Great Guilds' transport, copied so this mod depends on no other.
--
-- SINGLE PLAYER RUNS THE SAME OPS, called at once instead of broadcast, so every
-- op is exercised by ordinary play and only the round trip is not.
--
-- NO OP RELOADS THE COURT. The first tick loads every human court on every
-- machine, and IC.load replaces the court from the save, which would drop
-- anything this turn has not saved yet.
--
-- NOT YET TRIED IN A TWO-PLAYER CAMPAIGN.
IC.MP_TAG = "ic1"
-- The only committed ceiling on a trigger string: MCT's MultiplayerCommunicator.
IC.MP_MAX = 100
IC.MP_OPS = {}

-- CQI -> HUMAN FACTION. Only a human can send one of these.
function IC.faction_by_cqi(cqi)
    if not cqi then return nil end
    local found = nil
    pcall(function()
        local humans = cm:get_human_factions()
        for i = 1, #humans do
            local f = cm:get_faction(humans[i])
            if f and not f:is_null_interface() and f:command_queue_index() == cqi then
                found = humans[i]
                return
            end
        end
    end)
    return found
end

function IC.mp_send(faction_key, op, arg)
    if not faction_key or not IC.MP_OPS[op] then
        IC.warn("IRON COURT: action " .. tostring(op) .. " for "
                .. tostring(faction_key) .. " not sent")
        return
    end
    arg = tostring(arg or "")
    if not IC.is_mp() then
        IC.MP_OPS[op](faction_key, arg)
        return
    end
    local id = IC.MP_TAG .. "|" .. op .. "|" .. arg
    -- REFUSE, NEVER FALL BACK. Applied here instead, the change would reach this
    -- machine only - the fault this section exists to prevent.
    if #id > IC.MP_MAX then
        IC.warn("IRON COURT: " .. op .. " is " .. #id .. " characters, over "
                .. IC.MP_MAX .. " - not sent")
        return
    end
    local cqi = nil
    pcall(function()
        local f = cm:get_faction(faction_key)
        if f and not f:is_null_interface() then cqi = f:command_queue_index() end
    end)
    if not cqi then
        IC.warn("IRON COURT: no command queue index for " .. tostring(faction_key)
                .. " - " .. op .. " not sent")
        return
    end
    local ok, err = pcall(function() CampaignUI.TriggerCampaignScriptEvent(cqi, id) end)
    if not ok then IC.warn("IRON COURT: " .. op .. " not sent: " .. tostring(err)) end
end

-- THE RECEIVING END. Returns the faction it acted for, and nil for anything not
-- ours: every other mod's UITrigger comes through the same event, silently.
function IC.mp_receive(id, cqi)
    if type(id) ~= "string" then return nil end
    local op, arg = string.match(id, "^" .. IC.MP_TAG .. "|([^|]*)|(.*)$")
    if not op then return nil end
    local fn = IC.MP_OPS[op]
    if not fn then
        IC.warn("IRON COURT: unknown action " .. op .. " received")
        return nil
    end
    local faction_key = IC.faction_by_cqi(cqi)
    if not faction_key then
        IC.warn("IRON COURT: " .. op .. " from unknown faction cqi " .. tostring(cqi))
        return nil
    end
    fn(faction_key, arg)
    return faction_key
end

-- The argument's `|`-separated fields, an empty one kept as "".
local function fields(arg)
    local out = {}
    for piece in string.gmatch((arg or "") .. "|", "([^|]*)|") do out[#out + 1] = piece end
    return out
end

-- AND THE ANSWER, to whoever asked. The panel sets IC.after_op; the model never
-- names the panel. Returns what the model said.
local function answer(faction_key, op, arg, done, why, spare)
    if IC.after_op then IC.after_op(faction_key, op, arg, done, why, spare) end
    return done, why, spare
end

-- A number crosses the wire as its decimal string and comes back through
-- tonumber. A plot's target stays the string the panel passes, and an empty
-- one is nil, as the panel passes it when a plot has no target.
IC.MP_OPS.appoint = function(fk, arg)          -- office|cqi
    local f = fields(arg)
    return answer(fk, "appoint", arg, IC.appoint(fk, f[1], tonumber(f[2])))
end
IC.MP_OPS.dismiss = function(fk, arg)          -- office
    return answer(fk, "dismiss", arg, IC.dismiss(fk, fields(arg)[1]))
end
IC.MP_OPS.gov = function(fk, arg)              -- province|cqi
    local f = fields(arg)
    return answer(fk, "gov", arg, IC.assign_governor(fk, f[1], tonumber(f[2])))
end
IC.MP_OPS.ungov = function(fk, arg)            -- province
    return answer(fk, "ungov", arg, IC.release_governor(fk, fields(arg)[1]))
end
IC.MP_OPS.plot = function(fk, arg)             -- plot|actor cqi|target
    local f = fields(arg)
    local target = f[3]
    if target == "" then target = nil end
    return answer(fk, "plot", arg, IC.plot(fk, f[1], tonumber(f[2]), target))
end
IC.MP_OPS.favour = function(fk, arg)           -- favour|party
    local f = fields(arg)
    return answer(fk, "favour", arg, IC.favour(fk, f[1], f[2]))
end
IC.MP_OPS.hire = function(fk, arg)             -- office|index
    local f = fields(arg)
    return answer(fk, "hire", arg, IC.hire(fk, f[1], tonumber(f[2])))
end
IC.MP_OPS.grant = function(fk, arg)
    return answer(fk, "grant", arg, IC.grant_demand(fk))
end
IC.MP_OPS.refuse = function(fk, arg)
    return answer(fk, "refuse", arg, IC.refuse_demand(fk))
end
IC.MP_OPS.accept = function(fk, arg)           -- party
    return answer(fk, "accept", arg, IC.accept_offer(fk, fields(arg)[1]))
end
IC.MP_OPS.decline = function(fk, arg)          -- party
    return answer(fk, "decline", arg, IC.decline_offer(fk, fields(arg)[1]))
end

function IC.register()
    -- THE MULTIPLAYER TRANSPORT'S RECEIVING END - see IC.mp_send. Registered and
    -- silent in single player, where nothing is ever broadcast.
    core:add_listener("ic_mp", "UITrigger", true, function(context)
        local ok, err = pcall(function()
            IC.mp_receive(context:trigger(), context:faction_cqi())
        end)
        if not ok then IC.warn("IRON COURT: UITrigger failed: " .. tostring(err)) end
    end, true)

    core:add_listener("ic_turn", "FactionTurnStart", true, function(context)
```

- [ ] **Step 6: Run and watch it pass**

```bash
cd "/g/Modding for resources"
"/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | tail -3
"/c/Program Files (x86)/Lua/5.1/luac.exe" -p "Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua" && echo parses
py tools/check_lua_api.py "Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua"; echo "api exit $?"
```

Expected: `iron court harness: ok (623 checks)`, `parses`, `api exit 0`. If the garbled-number check reports "UITrigger failed", `IC.can_appoint` raised on a nil cqi. The fix goes in the model's guard, where `IC.character_by_cqi` is called with nil, and never in the test.

- [ ] **Step 7: Record the checkpoint**

Ledger: `Task 4: harness 623 green`.

---

### Task 5: The panel: routing, the local player, and the answer hook

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua` (`ICUI.player` near line 1210; `ICUI.on_petition_click` near 4449; `ICUI.on_pick_click` near 4761; `ICUI.on_office_click` near 5294; `ICUI.on_row_action` near 5324; `ICUI.on_act_click` near 5392; insert `ICUI.after_op` directly above `function ICUI.toggle()`)
- Test: `tools/_iron_court_harness.lua`

**Interfaces:**
- Consumes (Task 4): `IC.mp_send(faction_key, op, arg)`, the eleven op names and wire arguments, the hook contract `IC.after_op(faction_key, op, arg, done, why, spare)`, `IC.is_mp()`. Test helpers `with_mp` and `deliver`.
- Produces: `ICUI.player() -> faction_key` (forced local read, first human as fallback), `ICUI.ANSWERS[op](arg, done, why, spare)`, `ICUI.after_op(...)`, and `IC.after_op = ICUI.after_op`.

- [ ] **Step 1: Write the failing checks**

Insert below Task 4's checks:

```lua
check("the panel's player is this machine's, read the forced way", function()
    -- REVIEW FOCUS 5: this machine's player is not the first human - here a
    -- Dwarf beside a Chaos Dwarf host - and must never be shown the host's court.
    local DWARF = "wh_main_dwf_dwarfs"
    cm.get_human_factions = function() return {F, DWARF} end
    cm.get_local_faction_name = function(_, force)
        if force ~= true then error("unforced local-faction read in multiplayer") end
        return DWARF
    end
    local me = ICUI.player()
    cm.get_local_faction_name = function() error("no local faction yet") end
    local fallback = ICUI.player()
    cm.get_local_faction_name = nil
    cm.get_human_factions = function() return {} end
    assert(me == DWARF, "the panel read " .. tostring(me) .. ", the first human's court")
    assert(fallback == F, "a failed read did not fall back to the first human: " .. tostring(fallback))
end)

check("each of the eleven panel clicks sends in multiplayer and waits for its trigger", function()
    IC.state = {}
    turn = 1
    local f = make_faction(F, IC.CHD_SUBCULTURE,
                           {make_character(501, ANY_SEAT, "forge")}, {"prov_a"})
    f._cqi = 41
    f._gold = 99999
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "legion")
    cm.get_human_factions = function() return {F} end
    IC.register()
    local office = IC.OFFICES[1].slug
    local ctx = {component = {}}
    local saved_idx, saved_check, saved_view = ICUI.clicked_index, ICUI.act_check, ICUI.view
    ICUI.clicked_index = function() return 1 end
    ICUI.act_check = function() return true end
    local function petition(kind, yes)
        return function()
            ICUI.pick = nil
            ICUI.view = "petitions"
            ICUI.petition_rows = {[1] = kind == "demand" and {kind = "demand"}
                                         or {kind = "offer", slug = "legion"}}
            ICUI.scroll.petitions = 0
            ICUI.on_petition_click(ctx, yes)
        end
    end
    local function pick(p, row)
        return function()
            ICUI.pick = p
            ICUI.pick_rows = {[1] = row}
            ICUI.scroll.pick = 0
            ICUI.on_pick_click(ctx, F)
        end
    end
    local clicks = {
        {"grant_demand", petition("demand", true)},
        {"refuse_demand", petition("demand", false)},
        {"accept_offer", petition("offer", true)},
        {"decline_offer", petition("offer", false)},
        {"appoint", pick({kind = "office", key = office}, 501)},
        {"hire", pick({kind = "office", key = office}, {hire = 1})},
        {"plot", pick({kind = "plot", plot = "bribe", key = "502"}, 501)},
        {"assign_governor", pick({kind = "gov", key = "prov_a"}, 501)},
        {"dismiss", function()
            ICUI.pick = nil
            IC.court(F).offices[office] = 501
            ICUI.on_office_click(ctx)
        end},
        {"release_governor", function()
            ICUI.pick = nil
            ICUI.view = "govs"
            ICUI.gov_keys = {"prov_a"}
            ICUI.scroll.govs = 0
            IC.court(F).govs["prov_a"] = 501
            ICUI.on_row_action(ctx)
        end},
        {"favour", function()
            ICUI.pick = nil
            ICUI.sel = "legion"
            ICUI.on_act_click("ic_act_gift")
        end},
    }
    local failed = nil
    for _, c in ipairs(clicks) do
        local name, click = c[1], c[2]
        local ran = 0
        local was = IC[name]
        IC[name] = function() ran = ran + 1 return true end
        local ok, err = pcall(with_mp, F, function(sent)
            click()
            assert(ran == 0, "the " .. name .. " click changed the campaign before its "
                .. "trigger came back")
            assert(#sent == 1, "the " .. name .. " click sent " .. #sent .. " triggers")
            deliver(sent[1])
            assert(ran == 1, "the " .. name .. " trigger came back and reached the model "
                .. ran .. " times")
        end)
        IC[name] = was
        if not ok then failed = err break end
    end
    ICUI.clicked_index, ICUI.act_check, ICUI.view = saved_idx, saved_check, saved_view
    ICUI.pick, ICUI.sel, ICUI.notice = nil, nil, nil
    cm.get_human_factions = function() return {} end
    if failed then error(failed, 0) end
end)

check("in multiplayer a picker waits for the answer and closes when it comes", function()
    IC.state = {}
    turn = 1
    local f = make_faction(F, IC.CHD_SUBCULTURE, {make_character(501, ANY_SEAT, "forge")}, {})
    f._cqi = 41
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "forge")
    endow(F)
    cm.get_human_factions = function() return {F} end
    IC.register()
    local office = IC.OFFICES[1].slug
    ICUI.pick = {kind = "office", key = office}
    ICUI.pick_rows = {[1] = 501}
    ICUI.scroll.pick = 0
    ICUI.notice = nil
    local saved_idx, saved_refresh = ICUI.clicked_index, ICUI.refresh
    local refreshed = 0
    ICUI.clicked_index = function() return 1 end
    ICUI.refresh = function() refreshed = refreshed + 1 end
    local ok, err = pcall(with_mp, F, function(sent)
        ICUI.on_pick_click({component = {}}, F)
        assert(IC.court(F).offices[office] == nil, "appointed before the trigger came back")
        assert(ICUI.pick, "the picker closed before the answer came")
        deliver(sent[1])
        assert(IC.court(F).offices[office] == 501, "the trigger came back and nobody was appointed")
        assert(ICUI.pick == nil, "the answer did not close the picker")
        assert(refreshed >= 1, "the answer never redrew the panel, and no click is waiting to")
    end)
    ICUI.clicked_index, ICUI.refresh = saved_idx, saved_refresh
    ICUI.pick = nil
    cm.get_human_factions = function() return {} end
    if not ok then error(err, 0) end
end)

check("in multiplayer the other machine applies the answer and draws nothing", function()
    IC.state = {}
    turn = 1
    local G = "wh3_dlc23_chd_zhatan"
    local f = make_faction(F, IC.CHD_SUBCULTURE, {make_character(501, ANY_SEAT, "forge")}, {})
    f._cqi = 41
    make_faction(G, IC.CHD_SUBCULTURE, {}, {})._cqi = 42
    IC.add_house(F, IC.CROWN)
    IC.add_house(F, "forge")
    endow(F)
    cm.get_human_factions = function() return {F, G} end
    IC.register()
    local office = IC.OFFICES[1].slug
    local mine = {kind = "office", key = "a_picker_of_my_own"}
    ICUI.pick, ICUI.notice = mine, "mine"
    sounds = {}
    local ok, err = pcall(with_mp, G, function()
        deliver({cqi = 41, id = "ic1|appoint|" .. office .. "|501"})
    end)
    local pick, notice = ICUI.pick, ICUI.notice
    ICUI.pick, ICUI.notice = nil, nil
    cm.get_human_factions = function() return {} end
    if not ok then error(err, 0) end
    assert(IC.court(F).offices[office] == 501, "the other machine did not apply the appointment")
    assert(pick == mine and notice == "mine",
        "this machine's panel was answered for another player's click")
    assert(#sounds == 0, "this machine played " .. #sounds .. " confirmation(s) for another "
        .. "player's click")
end)
```

- [ ] **Step 2: Run and watch them fail**

```bash
cd "/g/Modding for resources"
IC_TEST_ALL=1 "/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | grep -E "^FAIL|failing"
```

Expected: 3 `FAIL` lines:
- "the panel read wh3_... , the first human's court"
- "the grant_demand click changed the campaign before its trigger came back"
- "appointed before the trigger came back"

The summary reads `3 failing, 624 passing`.

The fourth check, "the other machine applies the answer and draws nothing", **passes now,
and that is expected**. No answer hook exists yet, so nothing can draw. It guards the hook's
multiplayer filter once Step 4 adds the hook, and the Task 7 mutant "mp: every machine
answering every click" is what proves it can fail. Ledger this.

- [ ] **Step 3: The forced local player**

In `zzz_derpy_iron_court_ui.lua`, replace:

```lua
function ICUI.player()
    local human = cm:get_human_factions()
    return human and human[1] or nil
end
```

with:

```lua
-- THIS MACHINE'S PLAYER, read the forced way: unforced, get_local_faction_name
-- throws in multiplayer. The first human is the fallback when the read fails,
-- and in single player that is the same faction.
function ICUI.player()
    local ok, me = pcall(function() return cm:get_local_faction_name(true) end)
    if ok and type(me) == "string" and me ~= "" then return me end
    local human = cm:get_human_factions()
    return human and human[1] or nil
end
```

- [ ] **Step 4: The answer hook**

Replace:

```lua
function ICUI.toggle()
```

with:

```lua
-- ---------------------------------------------------------------------------
-- THE MODEL'S ANSWER TO A PANEL ACTION (IC.after_op). In single player
-- IC.mp_send runs the action at once, so this fires inside the click and the
-- click's own refresh follows it. In multiplayer it fires when the UITrigger
-- comes back, on every machine: only this machine's player draws anything, and
-- it refreshes for itself because no click is waiting to.
-- ---------------------------------------------------------------------------
ICUI.ANSWERS = {}

-- A yes or a no that confirms with a sound, and a refusal that says why.
local function confirmed(yes, demand)
    return function(_arg, done, why, spare)
        -- A DEMAND THE TURN HAD ALREADY DECIDED, and reason_text's "gone" is
        -- worded for an offer.
        if demand and why == "gone" then why = "no demand" end
        if done then
            ICUI.notice = nil
            -- THE GOOD SOUND FOR A YES and the bad one for a no, which is what
            -- a refusal is to the party that asked.
            ICUI.confirm(nil, yes)
        else
            ICUI.notice = ICUI.reason_text(why, spare)
        end
    end
end
ICUI.ANSWERS.grant = confirmed(true, true)
ICUI.ANSWERS.refuse = confirmed(false, true)
ICUI.ANSWERS.accept = confirmed(true, false)
ICUI.ANSWERS.decline = confirmed(false, false)
ICUI.ANSWERS.favour = confirmed(true, false)

-- The four pickers.
local function picked(op)
    return function(arg, done, why, spare)
        -- The picker stays OPEN on a refusal. Closing it would drop the player
        -- back on a list with no idea why nothing changed.
        if not done then
            ICUI.notice = ICUI.reason_text(why, spare)
            return
        end
        -- THE SEAT THIS FILLED, off the wire: in multiplayer the picker that
        -- sent this may have closed by now.
        local filled = nil
        if op == "appoint" or op == "hire" then filled = string.match(arg or "", "^([^|]*)") end
        ICUI.pick = nil
        ICUI.scroll.pick = 0
        -- A PLOT THAT RESOLVED IS STILL OWED AN ANSWER. `done` means the move
        -- happened, not that it worked: IC.plot hands back "landed" or "failed"
        -- in the slot a refusal uses for its reason.
        if why == "failed" then
            ICUI.notice = "It did not work. The influence is spent, and they "
                          .. "know perfectly well who tried."
            ICUI.confirm(nil, false)
        else
            ICUI.notice = nil
            -- THE CARD THAT JUST CHANGED, when a seat is what changed.
            ICUI.confirm(filled and ICUI.office_card(filled) or nil, true)
        end
    end
end
for _, op in ipairs({"appoint", "hire", "plot", "gov"}) do ICUI.ANSWERS[op] = picked(op) end

-- THE BAD SOUND, deliberately. Sacking a man is not a win: it empties a seat
-- you were getting something from and insults the party he came from.
ICUI.ANSWERS.dismiss = function(arg)
    for slot, office in ipairs(IC.OFFICES) do
        if office.slug == arg then
            ICUI.confirm(comp(ICUI.CARD .. "_" .. slot, comp(ICUI.PANEL)), false)
        end
    end
    ICUI.notice = nil
end

function ICUI.after_op(faction_key, op, arg, done, why, spare)
    local mp = IC.is_mp()
    if mp and faction_key ~= ICUI.player() then return end
    local answer = ICUI.ANSWERS[op]
    if answer then answer(arg, done, why, spare) end
    if mp then ICUI.refresh() end
end
IC.after_op = ICUI.after_op

function ICUI.toggle()
```

- [ ] **Step 5: Route the petitions**

Replace:

```lua
    local done, why, spare
    if p.kind == "demand" then
        if yes then
            done, why, spare = IC.grant_demand(faction)
        else
            done, why, spare = IC.refuse_demand(faction)
        end
        -- A DEMAND THE TURN HAD ALREADY DECIDED, and reason_text's "gone" is
        -- worded for an offer.
        if why == "gone" then why = "no demand" end
    elseif yes then
        done, why, spare = IC.accept_offer(faction, p.slug)
    else
        done, why, spare = IC.decline_offer(faction, p.slug)
    end
    if done then
        ICUI.notice = nil
        -- THE GOOD SOUND FOR A YES and the bad one for a no, which is what a
        -- refusal is to the party that asked.
        ICUI.confirm(nil, yes)
    else
        ICUI.notice = ICUI.reason_text(why, spare)
    end
    ICUI.refresh()
end
```

with:

```lua
    -- SENT, NOT CALLED: see IC.mp_send. The answer is ICUI.ANSWERS'.
    local op
    if p.kind == "demand" then
        op = yes and "grant" or "refuse"
    else
        op = yes and "accept" or "decline"
    end
    IC.mp_send(faction, op, p.kind == "demand" and "" or p.slug)
    ICUI.refresh()
end
```

- [ ] **Step 6: Route the four pickers**

Replace:

```lua
    local done, why, spare
    if type(chosen) == "table" then
        -- A man who does not exist yet. Only the office picker offers these.
        done, why, spare = IC.hire(faction, ICUI.pick.key, chosen.hire)
    elseif ICUI.pick.kind == "office" then
        done, why, spare = IC.appoint(faction, ICUI.pick.key, chosen)
    elseif ICUI.pick.kind == "plot_target" then
```

with:

```lua
    -- SENT, NOT CALLED: see IC.mp_send. The answer (the picker closed, the
    -- notice, the sound) is ICUI.ANSWERS'. In single player it has already run
    -- when mp_send returns; in multiplayer it runs when the trigger comes back.
    if type(chosen) == "table" then
        -- A man who does not exist yet. Only the office picker offers these.
        IC.mp_send(faction, "hire", ICUI.pick.key .. "|" .. tostring(chosen.hire))
    elseif ICUI.pick.kind == "office" then
        IC.mp_send(faction, "appoint", ICUI.pick.key .. "|" .. tostring(chosen))
    elseif ICUI.pick.kind == "plot_target" then
```

Then replace:

```lua
    elseif ICUI.pick.kind == "plot" then
        done, why, spare = IC.plot(faction, ICUI.pick.plot, chosen, ICUI.pick.key)
    else
        done, why, spare = IC.assign_governor(faction, ICUI.pick.key, chosen)
    end
    if done then
        -- THE SEAT THIS FILLED, read BEFORE the picker is cleared: once
        -- ICUI.pick is nil there is nothing left saying which card to light.
        local filled = (ICUI.pick.kind == "office") and ICUI.pick.key or nil
        ICUI.pick = nil
        ICUI.scroll.pick = 0
        -- A PLOT THAT RESOLVED IS STILL OWED AN ANSWER. `done` means the move
        -- happened; it does not mean it worked. IC.plot hands back "landed" or
        -- "failed" in the slot a refusal uses for its reason, and a miss that
        -- said nothing would read as a button that did nothing.
        if why == "failed" then
            ICUI.notice = "It did not work. The influence is spent, and they "
                          .. "know perfectly well who tried."
            ICUI.confirm(nil, false)
        else
            ICUI.notice = nil
            -- THE CARD THAT JUST CHANGED, when a seat is what changed. The
            -- panel is about to redraw the whole ziggurat and the only
            -- difference will be one name in the middle of fourteen cards.
            ICUI.confirm(filled and ICUI.office_card(filled) or nil, true)
        end
    else
        -- The picker stays OPEN on a refusal. Closing it would drop the player
        -- back on a list with no idea why nothing changed.
        ICUI.notice = ICUI.reason_text(why, spare)
    end
    return true
end
```

with:

```lua
    elseif ICUI.pick.kind == "plot" then
        IC.mp_send(faction, "plot", ICUI.pick.plot .. "|" .. tostring(chosen) .. "|"
                   .. (ICUI.pick.key or ""))
    else
        IC.mp_send(faction, "gov", ICUI.pick.key .. "|" .. tostring(chosen))
    end
    return true
end
```

- [ ] **Step 7: Route the dismissal, the release and the favour**

Replace:

```lua
    if court.offices[office.slug] then
        IC.dismiss(faction, office.slug)
        -- THE BAD SOUND, deliberately. Sacking a man is not a win: it empties a
        -- seat you were getting something from and insults the party he came
        -- from. The confirmation should not congratulate the player for it.
        ICUI.confirm(comp(ICUI.CARD .. "_" .. slot, comp(ICUI.PANEL)), false)
        ICUI.notice = nil
    else
```

with:

```lua
    if court.offices[office.slug] then
        -- SENT, NOT CALLED; the bad sound is ICUI.ANSWERS.dismiss.
        IC.mp_send(faction, "dismiss", office.slug)
    else
```

Replace:

```lua
    if court.govs[province_key] then
        IC.release_governor(faction, province_key)
    else
```

with:

```lua
    if court.govs[province_key] then
        IC.mp_send(faction, "ungov", province_key)
    else
```

Replace:

```lua
    else
        local done, reason, spare = IC.favour(faction, move.favour, slug)
        if done then
            ICUI.notice = nil
            ICUI.confirm(nil, true)
        else
            ICUI.notice = ICUI.reason_text(reason, spare)
        end
    end
    ICUI.refresh()
end
```

with:

```lua
    else
        -- SENT, NOT CALLED; the answer is ICUI.ANSWERS.favour.
        IC.mp_send(faction, "favour", move.favour .. "|" .. slug)
    end
    ICUI.refresh()
end
```

- [ ] **Step 8: Run and watch it pass, the existing click checks included**

```bash
cd "/g/Modding for resources"
"/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | tail -3
"/c/Program Files (x86)/Lua/5.1/luac.exe" -p "Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua" && echo parses
grep -n -E "IC\.(appoint|dismiss|assign_governor|release_governor|plot|favour|hire|grant_demand|refuse_demand|accept_offer|decline_offer)\(" "Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua"
```

Expected: `iron court harness: ok (627 checks)`, `parses`, and no grep output. The older click checks are the single-player regression suite and must all still pass unchanged. Two examples: "a refused pick explains itself and keeps the picker open", and the scroll-offset pick check. If one fails, the answer path differs from what the click did before. Fix `ICUI.ANSWERS`, never the older check.

- [ ] **Step 9: Record the checkpoint**

Ledger: `Task 5: harness 627 green`.

---

### Task 6: Packing gate, deploy list, repo manifest

**Files:**
- Modify: `tools/import_iron_court.py` (constants near line 21; new checks after `check_loyalty_writers`; `verify()` near line 748; `__main__` near line 1610)
- Modify: `tools/deploy_iron_court.py` (`SCRIPTS` near line 48)
- Modify: `tools/sync_iron_court_repo.py` (`_DOCS` and `manifest()`)

**Interfaces:**
- Consumes: the shipped Lua from Tasks 1-5 and the MCT file from Task 3.
- Produces: `check_mp_routing(ui_src) -> [str]`, `check_tune_reads(model_src, sources) -> [str]`, `py tools/import_iron_court.py --selftest`, and `MCT_LUA` in the gate's `SCRIPTS`.

- [ ] **Step 1: Write the failing selftest**

In `tools/import_iron_court.py`, insert directly above `def verify():`:

```python
def _selftest():
    """Each check added for MCT and multiplayer reports a planted fault and
    passes the clean shape. A check nobody has watched fail proves nothing."""
    assert check_mp_routing('IC.mp_send(faction, "appoint", k)') == []
    assert check_mp_routing('-- IC.appoint(faction, k, cqi)\nlocal s = "IC.plot("') == []
    assert check_mp_routing("IC.plot_chance(f, k) IC.favour_cost(k) IC.hire_settlement(f)") == []
    bad = check_mp_routing("IC.appoint(faction, k, cqi)\nIC.decline_offer(f, s)")
    assert len(bad) == 1 and "IC.appoint" in bad[0] and "IC.decline_offer" in bad[0], bad
    model = 'IC.TUNE_ORDER = {\n    "alpha", "beta", "gamma",\n}\nlocal x = IC.TUNE.alpha\n'
    parties = "local y = T.beta -- IC.TUNE.gamma is only mentioned here\n"
    bad = check_tune_reads(model, [model, parties])
    assert len(bad) == 1 and "gamma" in bad[0], bad
    quoted = model + 'local z = "gamma"\n'
    assert check_tune_reads(quoted, [quoted, parties]) == []
    assert check_tune_reads("local nothing = 1", []) != []
    print("import_iron_court selftest: ok")
```

And at the top of the `if __name__ == "__main__":` block, before `bad = verify()`:

```python
    if "--selftest" in sys.argv[1:]:
        _selftest()
        sys.exit(0)
```

- [ ] **Step 2: Run it and watch it fail**

```bash
cd "/g/Modding for resources"
py tools/import_iron_court.py --selftest
```

Expected: `NameError: name 'check_mp_routing' is not defined`.

- [ ] **Step 3: Write the two checks and the MCT path**

In `tools/import_iron_court.py`, replace:

```python
SCRIPTS = [MODEL_LUA, UI_LUA, PARTIES_LUA]
```

with:

```python
MCT_LUA = "Modding Files/pack/script/mct/settings/derpy_iron_court.lua"
SCRIPTS = [MODEL_LUA, UI_LUA, PARTIES_LUA, MCT_LUA]
```

Insert directly above `def _selftest():`:

```python
# THE ELEVEN PANEL ACTIONS. Called straight off a click they change the campaign
# on the clicking machine only, which in multiplayer is a desync.
DIRECT_ACTION = re.compile(
    r"\bIC\.(appoint|dismiss|assign_governor|release_governor|plot|favour|hire|"
    r"grant_demand|refuse_demand|accept_offer|decline_offer)\s*\(")


def check_mp_routing(ui_src):
    """The panel changes the campaign only through IC.mp_send.

    A model change made on one machine and not the others is a desync, so every
    panel action is sent as a UITrigger and applied on every machine when it
    comes back. One call site left calling the model directly plays perfectly in
    single player and desyncs the first time it is clicked in multiplayer - a
    campaign nobody here can run, so nothing in play would ever show it.
    Comments and strings are blanked first: the panel describes the calls it no
    longer makes.
    """
    body = _CLU._blank(ui_src)
    hits = sorted(set(m.group(1) for m in DIRECT_ACTION.finditer(body)))
    if not hits:
        return []
    return ["the panel calls %s directly - in multiplayer that changes one machine "
            "only; send it through IC.mp_send" % ", ".join("IC." + h for h in hits)]


TUNE_ORDER_BLOCK = re.compile(r"IC\.TUNE_ORDER\s*=\s*\{(.*?)\n\}", re.S)
REGISTRATION_BLOCKS = re.compile(r"IC\.(TUNE_ORDER|PRESETS)\s*=\s*\{.*?\n\}", re.S)


def check_tune_reads(model_src, sources):
    """Every setting on the MCT page is read by name somewhere it does something.

    A setting is registered three times - the MCT page, IC.TUNE, IC.TUNE_ORDER -
    and the court harness holds those against each other. This is the fourth
    hit: a read. Without one the control renders, toggles, freezes into the save
    and changes nothing, which is how the Great Guilds shipped one (2026-09-12).
    `sources` are the campaign scripts' texts, the model's included; the two
    registration blocks are cut out first, since they name every key.
    """
    m = TUNE_ORDER_BLOCK.search(model_src)
    if not m:
        return ["the model declares no IC.TUNE_ORDER, so no setting was checked"]
    keys = re.findall(r'"(\w+)"', m.group(1))
    if not keys:
        return ["IC.TUNE_ORDER names no setting, so no setting was checked"]
    text = "\n".join(re.sub(r"--[^\n]*", "", REGISTRATION_BLOCKS.sub("", s))
                     for s in sources)
    out = []
    for key in keys:
        if not re.search(r'\bTUNE\.%s\b|\bT\.%s\b|"%s"' % (key, key, key), text):
            out.append("the setting %s is on the MCT page and read nowhere - its "
                       "control would change nothing" % key)
    return out
```

- [ ] **Step 4: Run the selftest and watch it pass**

```bash
cd "/g/Modding for resources"
py tools/import_iron_court.py --selftest
```

Expected: `import_iron_court selftest: ok`.

- [ ] **Step 5: Wire both checks into `verify()`**

In `verify()`, directly below the `# 0c. LOYALTY HAS ONE WRITER.` block (after its `problems.extend(check_loyalty_writers(...))`), insert:

```python
    # 0d. THE PANEL CHANGES THE CAMPAIGN ONLY THROUGH IC.mp_send. See
    #     check_mp_routing: a direct call is a multiplayer desync nothing in
    #     single-player play would ever show.
    if os.path.isfile(UI_LUA):
        problems.extend(check_mp_routing(io.open(UI_LUA, encoding="utf-8").read()))

    # 0e. EVERY SETTING IS READ, and the page that offers them ships. See
    #     check_tune_reads.
    if not os.path.isfile(MCT_LUA):
        problems.append("the MCT settings file is missing, so the pack would ship "
                        "with no settings page")
    if os.path.isfile(MODEL_LUA):
        srcs = [io.open(p, encoding="utf-8").read()
                for p in (MODEL_LUA, PARTIES_LUA, UI_LUA) if os.path.isfile(p)]
        problems.extend(check_tune_reads(srcs[0], srcs))
```

In the `__main__` block, replace:

```python
    for path in SCRIPTS:
        print("  %-42s -> script/campaign/mod/%s"
              % (os.path.basename(path), os.path.basename(path)))
```

with:

```python
    for path in SCRIPTS:
        print("  %-42s -> %s" % (os.path.basename(path),
                                 path.split("Modding Files/pack/", 1)[1]))
```

- [ ] **Step 6: Ship the MCT file**

In `tools/deploy_iron_court.py`, replace:

```python
    ("Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_parties.lua",
     "script/campaign/mod/zzz_derpy_iron_court_parties.lua"),
]
```

with:

```python
    ("Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_parties.lua",
     "script/campaign/mod/zzz_derpy_iron_court_parties.lua"),
    # MCT loads every .lua under script/mct/settings/. Listed here, it is also in
    # the post-save check below, which asks the saved pack for every SCRIPTS path.
    ("Modding Files/pack/script/mct/settings/derpy_iron_court.lua",
     "script/mct/settings/derpy_iron_court.lua"),
]
```

- [ ] **Step 7: Add the new files to the repo manifest (no sync run)**

In `tools/sync_iron_court_repo.py`, inside `manifest()`, replace:

```python
        _MOD + "zzz_derpy_iron_court_ui.lua",
    ] + [_UI + "derpy_ic_%s%s.twui.xml" % (n, c)
```

with:

```python
        _MOD + "zzz_derpy_iron_court_ui.lua",
        "Modding Files/pack/script/mct/settings/derpy_iron_court.lua",
    ] + [_UI + "derpy_ic_%s%s.twui.xml" % (n, c)
```

In `_DOCS`, add after the `2026-09-24-iron-court-ui-scale-design.md` line:

```python
    ("docs/superpowers/specs/2026-09-25-iron-court-mct-multiplayer-design.md", "docs/design/"),
```

after the `2026-09-24-iron-court-ui-scale.md` plan line:

```python
    ("docs/superpowers/plans/2026-09-25-iron-court-mct-multiplayer.md", "docs/plans/"),
```

and add `"HANDOFF_20260925_IRON_COURT_MCT_MULTIPLAYER.md",` after `"HANDOFF_20260924_IRON_COURT_UI_SCALE.md",`. (The handoff is written in Task 8. Until then, the selftest may report it missing; that is expected and is fixed by Task 8.)

- [ ] **Step 8: Run the gate, the selftests and the harness**

```bash
cd "/g/Modding for resources"
py tools/import_iron_court.py --selftest
py tools/import_iron_court.py 2>&1 | tail -12
py tools/sync_iron_court_repo.py --selftest 2>&1 | tail -3
```

Expected:
- `import_iron_court selftest: ok`.
- `verify ok - ...` with `derpy_iron_court.lua -> script/mct/settings/derpy_iron_court.lua` in the listing, and no `REFUSING` line.
- The sync selftest passes, or fails only because the Task 8 handoff file does not exist yet. Ledger that as a ruling if so.
- The workspace is never copied to the repo: do not run `sync_iron_court_repo.py` without `--selftest` or `--check`.

- [ ] **Step 9: Record the checkpoint**

Ledger: `Task 6: gate verify ok; import selftest ok`.

---

### Task 7: Mutants for every new guard

**Files:**
- Modify: `tools/mutate_iron_court.py` (path constants near line 40; three existing mutants; the end of `MUTANTS`)

**Interfaces:**
- Consumes: the exact code lines written in Tasks 1-5. Every anchor below is copied from them.
- Produces: new mutants named `mct: ...` and `mp: ...`. The three re-aimed mutants keep their names.

- [ ] **Step 1: Find the anchors the plan has moved**

```bash
cd "/g/Modding for resources"
py tools/mutate_iron_court.py --selftest 2>&1 | tail -3
```

Expected: an `AssertionError` naming one stale mutant, either `ACCEPT on an offer routed to decline_offer`, `REFUSE on an offer routed to accept_offer` or `an AI court pressed like a player's` ("anchor matches 0 times, not 1").

- [ ] **Step 2: Re-aim the three stale mutants**

In `tools/mutate_iron_court.py`, replace:

```python
    ("ACCEPT on an offer routed to decline_offer", U,
     """        done, why, spare = IC.accept_offer(faction, p.slug)""",
     """        done, why, spare = IC.decline_offer(faction, p.slug)"""),
```

with the version below. It uses single-quoted Python strings because a triple-quoted string
that ends on a `"` breaks the literal (this happened on 2026-09-25):

```python
    ("ACCEPT on an offer routed to decline_offer", U,
     '        op = yes and "accept" or "decline"',
     '        op = yes and "decline" or "decline"'),
```

and replace:

```python
    ("REFUSE on an offer routed to accept_offer", U,
     """        done, why, spare = IC.decline_offer(faction, p.slug)""",
     """        done, why, spare = IC.accept_offer(faction, p.slug)"""),
```

with:

```python
    ("REFUSE on an offer routed to accept_offer", U,
     '        op = yes and "accept" or "decline"',
     '        op = yes and "accept" or "accept"'),
```

and replace:

```python
    ("an AI court pressed like a player's", M,
     """    if not IC.is_human(faction_key) then
        for _slug, house in pairs(court.houses) do house.pressed = nil end
        return 0
    end
    local chance = IC.control_pressure(faction_key)""",
     """    local chance = IC.control_pressure(faction_key)"""),
```

with:

```python
    ("an AI court pressed like a player's", M,
     """    if not IC.TUNE.pressure or not IC.is_human(faction_key) then
        for _slug, house in pairs(court.houses) do house.pressed = nil end
        return 0
    end
    local chance = IC.control_pressure(faction_key)""",
     """    if not IC.TUNE.pressure then
        for _slug, house in pairs(court.houses) do house.pressed = nil end
        return 0
    end
    local chance = IC.control_pressure(faction_key)"""),
```

- [ ] **Step 3: Add the settings file's path**

Replace:

```python
P = os.path.join(MOD, "zzz_derpy_iron_court_parties.lua")
```

with:

```python
P = os.path.join(MOD, "zzz_derpy_iron_court_parties.lua")
S = os.path.join(ROOT, "Modding Files", "pack", "script", "mct", "settings",
                 "derpy_iron_court.lua")
```

- [ ] **Step 4: Append the new mutants**

Use the Edit tool (never a Bash heredoc). Replace the end of `MUTANTS`:

```python
    ("a dead officer's term left in the save", M,
     """                court.terms[office_slug] = nil
            end""",
     """            end"""),
]
```

with:

```python
    ("a dead officer's term left in the save", M,
     """                court.terms[office_slug] = nil
            end""",
     """            end"""),

    # ---- MCT: the settings, frozen into the save (2026-09-25) ---------------
    ("mct: multiplayer reading MCT after all", M,
     "    if IC.is_mp() then return t end",
     "    if false then return t end"),
    ("mct: an erroring multiplayer check read as multiplayer", M,
     "    return ok and v == true",
     "    return (not ok) or v == true"),
    ("mct: an older save's missing key left nil", M,
     """    for k, v in pairs(IC.TUNE_DEFAULTS) do t[k] = v end
    for chunk in string.gmatch(packed or "", "[^|]+") do""",
     """    for chunk in string.gmatch(packed or "", "[^|]+") do"""),
    ("mct: a partial table packed as zeros", M,
     "        if v == nil then v = IC.TUNE_DEFAULTS[key] end",
     "        if v == nil then v = 0 end"),
    ("mct: an unreadable saved field read as zero", M,
     "        local n = tonumber(chunk)",
     "        local n = tonumber(chunk) or 0"),
    ("mct: the sliders read under every difficulty", M,
     "                and preset == IC.PRESET_CUSTOM",
     "                and true"),
    ("mct: the switches read under Custom only", M,
     '            if type(IC.TUNE_DEFAULTS[key]) == "boolean" or custom_number then',
     "            if custom_number then"),
    ("mct: a setting's type never checked", M,
     "            if type(v) == type(IC.TUNE_DEFAULTS[key]) then return v end",
     "            if v ~= nil then return v end"),
    ("mct: fewest rivals left above most", M,
     "    if t.rivals_min > t.rivals_max then t.rivals_min = t.rivals_max end",
     "    local _ = t.rivals_min"),
    ("mct: the intrigue line left where it loaded", M,
     "            move.line = IC.TUNE.party_intrigue_line",
     "            move.line = move.line"),
    ("mct: a reload re-reading MCT", M,
     '    if type(packed) == "string" and packed ~= "" then',
     "    if false then"),
    ("mct: the court rolled before the freeze", M,
     """    IC.freeze_tune()
    IC.register()""",
     """    IC.register()"""),
    ("mct: parties acting with parties_act off", P,
     "    if not T.parties_act then",
     "    if false then"),
    ("mct: AI courts run with ai_courts off", M,
     "    if IC.TUNE.ai_courts then return true end",
     "    return true"),
    ("mct: the settlement listener deaf to ai_courts", M,
     """        if not IC.runs_court(faction) then return end
        IC.add_standing(faction:name(), character:command_queue_index(),
                        IC.TUNE.settlement_influence)""",
     """        if not IC.is_chd(faction) then return end
        IC.add_standing(faction:name(), character:command_queue_index(),
                        IC.TUNE.settlement_influence)"""),
    ("mct: secession with secession off", M,
     "    if not IC.TUNE.secession then",
     "    if false then"),
    ("mct: pressure with pressure off", M,
     "    if not IC.TUNE.pressure or not IC.is_human(faction_key) then",
     "    if not IC.is_human(faction_key) then"),
    ("mct: the Crown splitting with crown_split off", M,
     "    if not IC.TUNE.crown_split then return nil end",
     "    if false then return nil end"),
    ("mct: routine lines written with the detailed log off", M,
     "    if IC.TUNE and IC.TUNE.detailed_log == false then return end",
     "    if false then return end"),
    ("mct: the parties' turn failure silenced with the routine log", M,
     """            IC.warn("IRON COURT: the parties' turn failed in " .. faction_key""",
     """            IC.say("IRON COURT: the parties' turn failed in " .. faction_key"""),
    ("mct: a switch left off the settings page", S,
     '    {"parties_act", "Rival parties act on their own", "systems",',
     '    {"parties_act_gone", "Rival parties act on their own", "systems",'),
    ("mct: the switches editable mid-campaign", S,
     """    o:set_assigned_section(section)
    if IN_CAMPAIGN then o:set_locked(true, LOCK_REASON) end""",
     """    o:set_assigned_section(section)"""),

    # ---- MP: every panel action through one transport (2026-09-25) ---------
    ("mp: an unsendable action applied on this machine", M,
     """    if not cqi then
        IC.warn("IRON COURT: no command queue index for " .. tostring(faction_key)
                .. " - " .. op .. " not sent")
        return
    end""",
     """    if not cqi then
        IC.MP_OPS[op](faction_key, arg)
        return
    end"""),
    ("mp: the length ceiling dropped", M,
     "    if #id > IC.MP_MAX then",
     "    if false then"),
    ("mp: another mod's trigger read as ours", M,
     """    local op, arg = string.match(id, "^" .. IC.MP_TAG .. "|([^|]*)|(.*)$")""",
     """    local op, arg = string.match(id, "^%w+|([^|]*)|(.*)$")"""),
    ("mp: a trigger from nobody acted on for the first human", M,
     "    local faction_key = IC.faction_by_cqi(cqi)",
     "    local faction_key = IC.faction_by_cqi(cqi) or (cm:get_human_factions() or {})[1]"),
    ("mp: a cqi left a string on the wire", M,
     """    return answer(fk, "appoint", arg, IC.appoint(fk, f[1], tonumber(f[2])))""",
     """    return answer(fk, "appoint", arg, IC.appoint(fk, f[1], f[2]))"""),
    ("mp: an empty plot target sent as an empty string", M,
     """    if target == "" then target = nil end""",
     "    local _ = target"),
    ("mp: the answer never reaching the panel", M,
     "    if IC.after_op then IC.after_op(faction_key, op, arg, done, why, spare) end",
     "    local _ = IC.after_op"),
    ("mp: the feed held in multiplayer", M,
     "    if IC.is_mp() then return 0 end",
     "    if false then return 0 end"),
    ("mp: the panel reading the first human again", U,
     "    local ok, me = pcall(function() return cm:get_local_faction_name(true) end)",
     "    local ok, me = false, nil"),
    ("mp: the unforced local-faction read", U,
     "    local ok, me = pcall(function() return cm:get_local_faction_name(true) end)",
     "    local ok, me = pcall(function() return cm:get_local_faction_name() end)"),
    ("mp: every machine answering every click", U,
     "    if mp and faction_key ~= ICUI.player() then return end",
     "    local _ = mp"),
    ("mp: an answer that never redraws in multiplayer", U,
     "    if mp then ICUI.refresh() end",
     "    local _ = mp"),
    ("mp: a dismissal called straight at the model", U,
     """        IC.mp_send(faction, "dismiss", office.slug)""",
     """        IC.dismiss(faction, office.slug)"""),
    ("mp: the favour paid straight off the click", U,
     """        IC.mp_send(faction, "favour", move.favour .. "|" .. slug)""",
     """        IC.favour(faction, move.favour, slug)"""),
    ("mp: a refused pick closing the picker", U,
     """        if not done then
            ICUI.notice = ICUI.reason_text(why, spare)
            return
        end""",
     """        if not done then
            ICUI.notice = ICUI.reason_text(why, spare)
        end"""),
]
```

- [ ] **Step 5: Prove every anchor applies**

```bash
cd "/g/Modding for resources"
py tools/mutate_iron_court.py --selftest 2>&1 | tail -3
```

Expected: `selftest ok: <N> mutants all anchored, ...`, where N is the Task 1 baseline count plus
37 (22 `mct:` and 15 `mp:`).

If a new anchor "matches 2 times": widen it with the line above it, copied from the shipped file, and never loosen the replacement. The most likely case is `    return ok and v == true`, if the model already contains that line elsewhere.

If a mutant name is not unique: that is fine, because the runner keys on position and not on name.

- [ ] **Step 6: Run the new and re-aimed mutants**

Do not edit anything while this runs.

```bash
cd "/g/Modding for resources"
py tools/mutate_iron_court.py "mct:" "mp:" "ACCEPT on an offer" "REFUSE on an offer" "AI court pressed" 2>&1 | tail -8
```

Expected: `40 mutants, 0 unexplained` (37 new and 3 re-aimed). A `SURVIVOR` means the harness does not test that rule. In that case, add the missing assertion to the owning task's check, watch it catch the mutant, and ledger it. Never delete the mutant. If a survivor turns out to be genuinely equivalent code, ledger a ruling and remove only that mutant.

- [ ] **Step 7: Run the full mutation suite**

Do not edit anything while this runs (about 7 minutes; run it in the background).

```bash
cd "/g/Modding for resources"
OUT="Modding Files/source/iron_court_bak_pre_mctmp_20260925/mutants_full.txt"
py tools/mutate_iron_court.py > "$OUT" 2>&1; tail -3 "$OUT"
```

Expected: `<N> mutants, 0 unexplained`. Afterwards, re-run the harness (`ok (627 checks)`) to confirm the tree was restored.

- [ ] **Step 8: Record the checkpoint**

Ledger: `Task 7: <N> mutants, 0 unexplained`.

---

### Task 8: Build, deploy, verify, write up

**Files:**
- Create: `docs/sessions/HANDOFF_20260925_IRON_COURT_MCT_MULTIPLAYER.md`
- Modify: `docs/SESSION_INDEX.md` (one line)
- Modify: `C:\Users\GAYAO-Family\.claude\projects\g--Modding-for-resources\memory\wh3-mct-has-no-campaign-gating.md`
- Deploy: `F:\SteamLibrary\steamapps\common\Total War WARHAMMER III\data\derpy_iron_court.pack`

**Interfaces:**
- Consumes: everything above, all green.
- Produces: the deployed pack, the handoff, the index line, the corrected memory.

- [ ] **Step 1: The gate, once more, from clean**

```bash
cd "/g/Modding for resources"
py tools/import_iron_court.py 2>&1 | grep -E "REFUSING|verify ok"
py tools/import_iron_court.py --selftest
py tools/check_lua_api.py "Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua" \
    "Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_parties.lua" \
    "Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua" \
    "Modding Files/pack/script/mct/settings/derpy_iron_court.lua"; echo "api exit $?"
```

Expected: `verify ok - ...`, `import_iron_court selftest: ok`, `api exit 0`. The gate
already runs the literal-left and undeclared-global checks over all four scripts.

- [ ] **Step 2: Game closed, RPFM open**

```powershell
Get-Process -Name Warhammer3 -ErrorAction SilentlyContinue | Select-Object -First 1
Invoke-WebRequest http://127.0.0.1:45127/sessions -TimeoutSec 4 -UseBasicParsing | Select-Object -ExpandProperty StatusCode
```

Expected: no process line, then `200`. If the game is running or RPFM is closed, stop and tell the user. Never deploy around either.

- [ ] **Step 3: Back up the live pack**

```bash
D="/f/SteamLibrary/steamapps/common/Total War WARHAMMER III/data"
cp -p "$D/derpy_iron_court.pack" "$D/derpy_iron_court.pack.bak_pre_mctmp_20260925"
ls -la "$D/derpy_iron_court.pack.bak_pre_mctmp_20260925"
```

Expected: the backup exists at the same size as the live pack.

- [ ] **Step 4: Build and deploy**

```bash
cd "/g/Modding for resources"
py tools/deploy_iron_court.py 2>&1 | tail -8
```

Expected: `gates green`, `script/mct/settings/derpy_iron_court.lua` among the added paths, `verified <n> file(s) in the saved pack`, and `deployed ...\data\derpy_iron_court.pack (<bytes> bytes)`.

- [ ] **Step 5: Verify the deployed scripts byte for byte**

```bash
cd "/g/Modding for resources"
py -c "
import sys; sys.path.insert(0, 'tools'); import read_pack_index as R
pack = 'F:/SteamLibrary/steamapps/common/Total War WARHAMMER III/data/derpy_iron_court.pack'
pairs = [('script/campaign/mod/zzz_derpy_iron_court.lua', 'Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua'),
         ('script/campaign/mod/zzz_derpy_iron_court_parties.lua', 'Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_parties.lua'),
         ('script/campaign/mod/zzz_derpy_iron_court_ui.lua', 'Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua'),
         ('script/mct/settings/derpy_iron_court.lua', 'Modding Files/pack/script/mct/settings/derpy_iron_court.lua')]
for dest, src in pairs:
    got = [d for p, c, d in R.read(pack, dest) if p == dest]
    want = open(src, 'rb').read()
    print(('OK  ' if got and got[0] == want else 'BAD ') + dest)
"
```

Expected: four `OK` lines.

- [ ] **Step 6: Write the handoff**

Create `docs/sessions/HANDOFF_20260925_IRON_COURT_MCT_MULTIPLAYER.md` with these sections, filled in from this run's real output:

1. **What shipped.** The MCT page (four sections, a difficulty preset, six switches, fourteen Custom numbers). The freeze at first tick. The multiplayer transport. The forced local player. No feed hold in multiplayer. Give the deployed pack size, and the harness and mutant counts.
2. **What single player sees.** With MCT absent or left on Default, nothing changes. A save from before this build takes the player's MCT settings the first time it is loaded, and keeps them.
3. **The timing correction.** Why the freeze moved from the first turn start to first tick: the new-game turn-1 evidence, and MCT's `LoadingGame` read in `Registry:load`. **The Great Guilds has the same gap** (it freezes at the first `FactionTurnStart`, so turn 1 plays on defaults). It is noted for its own fix, not made here.
4. **Not tried in a two-player campaign.** What a first two-machine run must check: each of the eleven actions from each machine; the other machine's panel staying quiet; `script_log.txt` on both machines free of `UITrigger failed` and `not sent`.
5. **In game, single player, to check.**
   1. Load the current save. Appoint, dismiss, plot, send a gift, and answer a petition. Each should confirm and redraw exactly as before.
   2. If MCT is installed, the page shows four sections, locked in campaign with the reason.
   3. A new campaign on Harsh rolls three or four rival parties at loyalty 50.
6. **Rulings** made during execution, copied from the ledger.

- [ ] **Step 7: One index line, and the corrected memory**

Append ONE line to `docs/SESSION_INDEX.md` in the Iron Court section, in the style of its neighbours:

```markdown
- 2026-09-25 Iron Court MCT + multiplayer: `sessions/HANDOFF_20260925_IRON_COURT_MCT_MULTIPLAYER.md` - settings frozen at FIRST TICK (MCT reads in LoadingGame; a new game fires no turn-1 FactionTurnStart), eleven panel actions via ic1 UITrigger; not tried two-machine
```

In the memory file `wh3-mct-has-no-campaign-gating.md`, replace the sentence that begins "Take that snapshot at the first `FactionTurnStart`, **not** at first tick" (through "...with a correct-looking panel beside it saying otherwise.") with:

```markdown
Take that snapshot at FIRST TICK. MCT's campaign registry reads the player's settings in its
own `LoadingGame` callback (`groovy_mct.pack`, `script/groovy/modules/mct/systems/registry/main.lua`,
`Registry:load`), and LoadingGame runs before any first tick. The earlier advice here, "at the
first `FactionTurnStart`, not first tick", was WRONG in a costly way: a new campaign fires no
`FactionTurnStart` until turn 1 ends, so turn 1 plays on the defaults, and anything rolled at
first tick (the Iron Court's court) is rolled on them. Corrected 2026-09-25. The Great Guilds
still snapshots at the turn start.
```

Update that memory's `description:` line to mention first tick, and its line in `index-lua.md` if that line quotes the old advice.

- [ ] **Step 8: Final run of everything**

```bash
cd "/g/Modding for resources"
"/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua 2>&1 | tail -1
py tools/mutate_iron_court.py --selftest 2>&1 | tail -1
py tools/sync_iron_court_repo.py --selftest 2>&1 | tail -1
```

Expected: `iron court harness: ok (627 checks)`, `selftest ok: ...`, and the sync selftest passing now that the handoff exists.

- [ ] **Step 9: Report**

Tell the user:
- the pack is deployed to `data/` and must be enabled as before;
- the three in-game single-player checks from the handoff;
- the public repo has NOT been synced (its README and DEVELOPMENT guide need a "not yet tried in a two-player campaign" line when they choose to sync);
- the Guilds turn-1 gap.
