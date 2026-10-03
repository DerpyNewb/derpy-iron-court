# Iron Court Laws Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The player's court passes laws, four categories of five options each, by a vote of its men. Each man votes his party's line with his own influence. The player and the parties propose, push support levels, win men and overrule. The Laws tab shows a Bannerlord-style policy board and decision screen.

**Architecture:** Model work goes in `zzz_derpy_iron_court.lua`:

- a law catalogue, `IC.LAW_ORDER` / `IC.LAWS`;
- a vote engine: voters, party line, tally, prices;
- player ops, plus resolution and party pushes in a new `IC.law_turn` step of `IC.turn`;
- save fields 17 and 18;
- a live switch;
- five MP ops.

The parties file adds one `IC.PARTY_ACTS` entry, a party proposing. The generator builds 20 faction bundles from CA effects, plus loc and three events. The panel adds a seventh tab with two screens, each drawn from new components:

- the board: 20 law cards from a new card file, and a detail pane;
- the decision screen: a support bar, two sides of party blocks from a new block file, and the Crown's hand.

**Tech Stack:** Lua 5.1 (game scripts and harness), Python 3 (generators, gates, mutation runner, preview), RPFM MCP (pack build).

**Spec:** `docs/superpowers/specs/2026-10-02-iron-court-laws-design.md`. Its section 4 is the approved redesign. The approved pictures are `.skilltree_cache/ui_preview/ic_law_board.png` and `ic_law_vote.png`; the throwaway script that drew them is `scratchpad/law_mock2.py`, and its coordinates are the starting layout.

## Global Constraints

- The workspace is **not a git repo**. Each "Commit" step below is a **ledger line** in `.superpowers/sdd/2026-10-02-iron-court-laws/progress.md`, never a git command.
- **CRLF is preserved.** Every court Lua file and `tools/_iron_court_harness.lua` is CRLF. Edit them with the Edit tool, or with the exact-anchor CRLF patcher `scratchpad/icp.py` (`from icp import edit, before, after, _read, _write, MODEL, UI, PARTIES, MCT, HARNESS, GEN, GENUI, MUT`; `import *` does NOT bring the underscored names). **Never `sed -i`**: Git Bash sed strips CRLF.
- **Patch scripts containing backslashes go through the Write tool, never a heredoc.** A heredoc ate `\n` twice in this session.
- **Lua 5.1.5.** Run `luac -p` on every edited Lua file. A number literal never goes on the LEFT of an arithmetic operator (`check_lua_literal_left.py`). Never `string.find(s, p, 1, true)`: the plain flag breaks the game's string library, and `check_lua_api.py` flags it.
- **No floats in the save or the tally.** Multipliers are percent integers (`law_push_mult = {150, 200, 300}`), and every weight goes through `math.floor`.
- **`IC.TUNE_ORDER` is append-only.** `laws` is appended after `deeds`. It also goes in `IC.LIVE_TUNE`, the MCT `SWITCHES`, and the harness `LIVE` list. Every other law number is an `IC.TUNE` constant and stays OFF `TUNE_ORDER` and the MCT page.
- **`IC.EVENTS` and the generator's `EVENTS` are appended in the same order.** New ids: `law_proposed` 2633, `law_passed` 2634, `law_failed` 2635.
- **Save fields 17 and 18 are new and optional.** Field 17 holds `category,option` entries plus one `rest,turn` entry; field 18 holds the open votes, eight fields each, the last `answered` as 1 or 0. Inside a vote, the `won` and `push` lists use `/` between pairs and `:` inside a pair, because `,` `;` `|` are taken. An empty list is `-`, because `split` drops empty fields.
- **Player courts only:** `IC.laws_on(faction_key)` is `IC.TUNE.laws ~= false and IC.is_human(faction_key)`.
- **Player text:**
  - "Reputation", never "standing";
  - no cap, accrue, rep or AI jargon in loc, tooltips or MCT;
  - never the word "rung";
  - no emojis.
  - "influence" is the player's word for a man's points.
- **Effect keys** are all CA 9.0 keys, checked against the vanilla cache on 2026-10-02:
  - all 39 `(effect, scope)` pairs ship in CA's junction tables;
  - every `is_positive_value_good` matches the spec's "good" column.
  - The CA wordings Task 6 pins are the exact `effects_description_*` strings read that day, including the trailing space on the Conclave Influence one and `%n` (not `%+n`) on the K'daai one.
- **The harness runs from the workspace root:** `IC_TEST_ALL=1 "/c/Program Files (x86)/Lua/5.1/lua.exe" tools/_iron_court_harness.lua > .superpowers/sdd/2026-10-02-iron-court-laws/h.log 2>&1; tail -1 .superpowers/sdd/2026-10-02-iron-court-laws/h.log`. Baseline: `iron court harness: ok (925 checks)`.
- **The mutation runner** runs from the workspace root: `py tools/mutate_iron_court.py "law:"`. Its anchors must match the shipped Lua exactly, and its quotes are escaped as `\"`.
- **Deploy** with `py tools/deploy_iron_court.py` (add `--wait` if `Warhammer3.exe` is running). It needs RPFM open at 127.0.0.1:45127. The Iron Court lives in `data/` only, with no Workshop folder. Per standing rule, deploy to `data/` whenever the game is shut: back up, copy, verify.

## Review Focus

1. **A vote whose proposer party is removed** (it seceded or dissolved) before `ends` must still resolve. A fail moves no loyalty on a missing house, and the board must not crash naming a departed proposer. Test in Task 4: remove the proposer, run `IC.law_turn` at `ends`, and expect the vote gone with a `law_fail` Record line and no error.
2. **The Crown changing its stance after pushing.** Its push level stays and now multiplies the new side. A switch to `abstain` leaves Crown men abstaining and unmultiplied. Test in Task 3.
3. **A man won, who then changes party** (a split or secession moves him) still votes the side he was won to. A man won who then dies stops counting. Test in Task 2: a won man whose party is removed still counts for his won side; a won man with `_dead` counts for nothing.
4. **The switch flipped off with a vote open and a non-start law in force.** The votes drop, every law bundle comes off, and `court.laws` is kept. Flipped on again, the in-force bundle comes back with no vote. Test in Task 4.
5. **An old save (16 fields)** loads with the start options and no votes. A save that names a law the build no longer has falls back to the start option and does not keep a dangling key. Test in Task 4.

---

## File Structure

| File | Change |
|---|---|
| `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua` | catalogue, vote engine, ops, `IC.law_turn`, save, switch, MP ops, Record kinds, events |
| `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_parties.lua` | `T.law_party_motive`, one `IC.PARTY_ACTS` entry |
| `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua` | tab, board, pane, decision screen, clicks, Record sentences, Help topic, answers |
| `Modding Files/pack/script/mct/settings/derpy_iron_court.lua` | `laws` switch |
| `tools/gen_iron_court.py` | 20 bundles, effect constants and wordings, loc, events, `check_laws()` |
| `tools/gen_ic_ui.py` | tab cells, board and vote cells, two new files, scaling, checks |
| `Modding Files/pack/ui/campaign ui/derpy_ic_law*.twui.xml` (generated) | created: the law card and the party block, each with its `_compact` twin |
| `tools/preview_iron_court.py` | `law_board` and `law_vote` pictures |
| `tools/_iron_court_harness.lua` | every check below |
| `tools/mutate_iron_court.py` | `law:` mutants |
| `tools/import_iron_court.py`, `tools/deploy_iron_court.py`, `tools/sync_iron_court_repo.py` | the two new twui files, the spec and plan |

---

### Task 1: The catalogue, the switch, the record and the save

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua`. Anchors:
  - the DEEDS block in `IC.TUNE`, ending `    renown_join_line    = 15,`;
  - `IC.TUNE_ORDER`, its last line `    "deeds",`;
  - `IC.LIVE_TUNE = {...}`, ending `"gov_drift", "deeds"}`;
  - `local function new_court()`, its line `        confed_turn = 0,  -- the turn this court last took in a confederation`;
  - `IC.LOG_KINDS`, its line `    deed = true, drawn = true,`;
  - `IC.EVENTS`, its last entry `    party_drawn        = {2632, true, true},`;
  - `function IC.pack`, its `return join({...` statement;
  - `function IC.unpack`, its line `    IC.state[faction_key] = court`;
  - `function IC.settle_switches`, its last line `    if not IC.governments_on() then IC.apply_gov_bundle(faction_key) end`;
  - `function IC.refresh_live_tune`, its line `       or off.gov_drift then`.
- Modify: `Modding Files/pack/script/mct/settings/derpy_iron_court.lua`, after the `deeds` entry in `SWITCHES`.
- Test: `tools/_iron_court_harness.lua`. Insert the new checks just before `check("no parties' turn failed anywhere in the run"`. Also change the `LIVE` list.

**Interfaces:**
- Produces:
  - `IC.TUNE` keys:
    - `laws = true`, `law_propose_cost = 150`, `law_party_share = 15`, `law_party_rest = 6`, `law_vote_turns = 2`;
    - `law_loyal_line = 60`, `law_disloyal_line = 40`;
    - `law_push_cost = {100, 250, 500}`, `law_push_mult = {150, 200, 300}`, `law_push_margin = 10`;
    - `law_win_rate = 50`, `law_win_ambition = {cautious = 150, steady = 100, ambitious = 75}`;
    - `law_overrule_cost = 500`, `law_overrule_loyalty = -10`;
    - `law_pass_gain = 5`, `law_pass_loss = -5`, `law_fail_loss = -5`.
  - `IC.LAW_ORDER = {"labour", "tribute", "worship", "war"}`.
  - `IC.LAWS[category] = {icon = <bare png>, order = {5 option slugs, start first}, opts = {[option] = {icon = <bare png>, pro = {slugs}, con = {slugs}}}}`.
  - `IC.LAW_SIDES = {aye = true, nay = true, abstain = true}`.
  - Functions:
    - `IC.laws_on(faction_key) -> boolean`;
    - `IC.law_bundle(category, option) -> "derpy_ic_law_<category>_<option>"`;
    - `IC.law_opt(category, option) -> row|nil`;
    - `IC.law_in_force(faction_key, category) -> option`;
    - `IC.law_stance(category, option, party) -> "aye"|"nay"|nil`;
    - `IC.apply_law_bundles(faction_key)`.
  - Court fields:
    - `laws = {}`, as `[category] = option`, holding only what differs from the start;
    - `votes = {}`, as `[category] = {option, proposer, ends, stance, won = {[cqi] = side}, push = {[party] = level}, answered = true|nil}`;
    - `law_rest` = the turn of the last party proposal, or nil.
  - Log kinds `law_propose`, `law_pass`, `law_fail`, `law_win`, `law_push`, `law_overrule`. Each takes `slug` = a party, `key` = `"<category>.<option>"` and `n` = a price or 0.
  - `IC.EVENTS`: `law_proposed` 2633, `law_passed` 2634, `law_failed` 2635.

- [ ] **Step 1: Write the failing checks.** Insert into the harness before the anchor named above:

```lua
-- A PLAYER COURT FOR THE LAWS (spec 2026-10-02 laws), past its grace period.
-- `men` is {{party, influence}, ...}; man i is cqi 9000 + i.
local function law_court(men, weights)
    local court = gov_court(weights or {crown = 10, legion = 10, ledger = 10, forge = 10})
    court.laws, court.votes, court.law_rest = {}, {}, nil
    local chars = {}
    for i, m in ipairs(men or {}) do
        chars[#chars + 1] = make_character(9000 + i, ANY_SEAT, m[1], nil, m[3])
        court.standing[9000 + i] = m[2]
    end
    make_faction(F, IC.CHD_SUBCULTURE, chars, {})
    return court, chars
end

-- AN OPEN LABOUR VOTE on `option` (default the Ash Harvest: the Legion is for
-- it, the Ledger against).
local function law_vote(court, option, stance, proposer)
    court.votes.labour = {option = option or "ash", proposer = proposer or "legion",
                          ends = turn + IC.TUNE.law_vote_turns, stance = stance or "aye",
                          won = {}, push = {}}
    return court.votes.labour
end

check("laws: every category has five options, its start first, and every option a bundle name", function()
    assert(#IC.LAW_ORDER == 4, #IC.LAW_ORDER .. " categories")
    for _, cat in ipairs(IC.LAW_ORDER) do
        local c = IC.LAWS[cat]
        assert(c and #c.order == 5, cat .. " has " .. (c and #c.order or 0) .. " options")
        local start = c.opts[c.order[1]]
        assert(not start.pro and not start.con, cat .. "'s start option has a party behind it")
        for _, opt in ipairs(c.order) do
            assert(c.opts[opt] and c.opts[opt].icon, cat .. "." .. opt .. " has no row or icon")
            assert(IC.law_bundle(cat, opt) == "derpy_ic_law_" .. cat .. "_" .. opt, "bundle name")
        end
    end
end)

check("laws: every rival party is for one option and against one, and the Crown only against Open Roads", function()
    local pro, con = {}, {}
    for _, cat in ipairs(IC.LAW_ORDER) do
        for _, opt in ipairs(IC.LAWS[cat].order) do
            local o = IC.LAWS[cat].opts[opt]
            for _, p in ipairs(o.pro or {}) do pro[p] = (pro[p] or 0) + 1 end
            for _, p in ipairs(o.con or {}) do con[p] = (con[p] or 0) + 1 end
        end
    end
    for _, p in ipairs(IC.PARTIES) do
        if p ~= IC.CROWN then
            assert(pro[p] and con[p], p .. " is for " .. tostring(pro[p]) .. " and against " .. tostring(con[p]))
        end
    end
    assert(not pro.crown and con.crown == 1 and IC.law_stance("tribute", "roads", "crown") == "nay",
        "the Crown's stances are wrong")
end)

check("laws: the start option is in force until a law passes, and an unknown saved law reads as the start", function()
    local court = law_court({})
    assert(IC.law_in_force(F, "labour") == "measure", "start " .. IC.law_in_force(F, "labour"))
    court.laws.labour = "ash"
    assert(IC.law_in_force(F, "labour") == "ash", "a passed law is not in force")
    court.laws.labour = "gone"
    assert(IC.law_in_force(F, "labour") == "measure", "an unknown law is in force")
    gov_done()
end)

check("laws: a player court wears exactly one law bundle per category, an AI court none", function()
    local court = law_court({})
    court.laws.war = "gunnery"
    applied = {}
    IC.apply_law_bundles(F)
    for _, cat in ipairs(IC.LAW_ORDER) do
        local n = 0
        for _, opt in ipairs(IC.LAWS[cat].order) do
            if applied[IC.law_bundle(cat, opt)] then n = n + 1 end
        end
        assert(n == 1, cat .. " wears " .. n .. " bundles")
    end
    assert(applied[IC.law_bundle("war", "gunnery")] and not applied[IC.law_bundle("war", "levy")],
        "the passed law's bundle is not the one worn")
    cm.get_human_factions = function() return {} end
    applied = {}
    IC.apply_law_bundles(F)
    assert(next(applied) == nil, "an AI court wears " .. tostring(next(applied)))
    gov_done()
end)

check("laws: laws and open votes survive a save, and an old save loads the starts with no votes", function()
    local court = law_court({})
    court.laws.war, court.law_rest = "gunnery", turn - 2
    local v = law_vote(court, "ash", "nay", "legion")
    v.won[9001], v.won[77] = "nay", "aye"
    v.push.crown, v.push.legion = 2, 1
    v.answered = true
    IC.save(F)
    local packed = cm:get_saved_value("derpy_ic_" .. F)
    IC.state = {}
    IC.load(F)
    local back = IC.court(F)
    assert(back.laws.war == "gunnery" and back.law_rest == turn - 2, "the laws did not round-trip")
    local w = back.votes.labour
    assert(w and w.option == "ash" and w.proposer == "legion" and w.stance == "nay"
        and w.ends == turn + IC.TUNE.law_vote_turns, "the vote did not round-trip")
    assert(w.won[9001] == "nay" and w.won[77] == "aye" and w.push.crown == 2 and w.push.legion == 1,
        "won or push did not round-trip")
    assert(w.answered == true, "answered did not round-trip")
    cm:set_saved_value("derpy_ic_" .. F, first_fields(packed, 16))
    IC.state = {}
    IC.load(F)
    assert(next(IC.court(F).laws) == nil and next(IC.court(F).votes) == nil, "an old save holds laws")
    assert(IC.law_in_force(F, "war") == "levy", "an old save is not on the start")
    gov_done()
end)

check("laws: a vote with nobody won and nobody pushing survives a save", function()
    local court = law_court({})
    law_vote(court, "lash", "abstain", "chain")
    IC.save(F)
    IC.state = {}
    IC.load(F)
    local w = IC.court(F).votes.labour
    assert(w and w.stance == "abstain" and next(w.won) == nil and next(w.push) == nil
        and not w.answered, "an empty won or push list, or an unanswered vote, did not load as saved")
    gov_done()
end)

check("laws: switched off, the votes drop and the bundles come off; on, the law in force returns", function()
    local court = law_court({})
    court.laws.labour = "ash"
    law_vote(court, "lash")
    local saved = IC.TUNE.laws
    IC.TUNE.laws = false
    applied = {[IC.law_bundle("labour", "ash")] = 1}
    IC.settle_switches(F)
    assert(next(court.votes) == nil, "a vote survived the switch")
    assert(not applied[IC.law_bundle("labour", "ash")], "a law bundle stayed on")
    assert(court.laws.labour == "ash", "the switch forgot the law in force")
    IC.TUNE.laws = true
    IC.settle_switches(F)
    assert(applied[IC.law_bundle("labour", "ash")], "switched on, the law in force did not return")
    IC.TUNE.laws = saved
    gov_done()
end)
```

And in the harness `LIVE` list, append `"laws"`:

```lua
local LIVE = {"parties_act", "secession", "pressure", "crown_split", "all_cards",
              "detailed_log", "governments", "gov_drift", "deeds", "laws"}
```

- [ ] **Step 2: Run the harness and watch the new checks fail.**

Run: the harness command from Global Constraints, then `grep -c "^FAIL laws:" .superpowers/sdd/2026-10-02-iron-court-laws/h.log`.
Expected: 7 `FAIL laws:` lines (`IC.LAW_ORDER` is nil), plus the existing LIVE-list check failing on `laws`.

- [ ] **Step 3: Implement.** In `IC.TUNE`, after `    renown_join_line    = 15,`:

```lua

    -- THE LAWS (spec 2026-10-02 laws). Constants: only `laws` is a switch, and
    -- only it is in IC.TUNE_ORDER. Multipliers are percent, never floats.
    laws                = true,
    law_propose_cost    = 150,
    law_party_share     = 15,   -- % of the court a party needs to propose
    law_party_rest      = 6,    -- turns between two party proposals
    law_vote_turns      = 2,
    law_loyal_line      = 60,   -- a party with no stance votes with you from here
    law_disloyal_line   = 40,   -- ...and against you below here
    law_push_cost       = {100, 250, 500},   -- reaching each support level
    law_push_mult       = {150, 200, 300},   -- its weight, percent
    law_push_margin     = 10,   -- % of all voting influence that is "close"
    law_win_rate        = 50,   -- % of a man's influence his vote costs
    law_win_ambition    = {cautious = 150, steady = 100, ambitious = 75},
    law_overrule_cost   = 500,
    law_overrule_loyalty = -10,
    law_pass_gain       = 5,
    law_pass_loss       = -5,
    law_fail_loss       = -5,
```

In `IC.TUNE_ORDER`, replace `    "deeds",` with:

```lua
    "deeds",
    "laws",
```

Replace the `IC.LIVE_TUNE` assignment's last line, `"all_cards", "detailed_log", "governments", "gov_drift", "deeds"}`, with `"all_cards", "detailed_log", "governments", "gov_drift", "deeds", "laws"}`. In the comment above it, change `The MCT page names the same\n-- nine.` to `ten`, and add a sentence: `Laws off drops open votes and takes every law bundle off; the laws in force stay in the save.`

After `function IC.gov_bundle(slug) ... end` (the line `function IC.gov_bundle(slug) return "derpy_ic_doctrine_" .. slug end`), insert the catalogue:

```lua

-- THE LAWS (spec 2026-10-02 laws section 2). One option per category is in
-- force; the first of each `order` is its start and has no effects. `icon` is
-- a bare name under ui/campaign ui/effect_bundles/: the bundle wears it
-- (gen_iron_court reads it from here) and so does the panel. `pro` and `con`
-- are the parties for and against.
IC.LAW_ORDER = {"labour", "tribute", "worship", "war"}
IC.LAWS = {
    labour = {icon = "chd_labour.png",
              order = {"measure", "lash", "kept", "quota", "ash"},
              opts = {
        measure = {icon = "chd_workload.png"},
        lash    = {icon = "dlc23_region_action_set_example.png", pro = {"chain"}, con = {"hearth"}},
        kept    = {icon = "slaves.png", pro = {"hearth"}, con = {"chain"}},
        quota   = {icon = "wh3_dlc23_edict_chd_higher_quotas.png", pro = {"forge"}, con = {"hearth"}},
        ash     = {icon = "wh3_dlc23_edict_chd_smoke_stacks.png", pro = {"legion"}, con = {"ledger"}},
    }},
    tribute = {icon = "edict_collect_tribute.png",
               order = {"tithe", "roads", "tariff", "mines", "charter"},
               opts = {
        tithe   = {icon = "edict_collect_tribute.png"},
        roads   = {icon = "convoy_icon.png", pro = {"road"}, con = {"crown"}},
        tariff  = {icon = "trade_agreement.png", pro = {"ledger"}, con = {"road"}},
        mines   = {icon = "chd_raw_materials.png", pro = {"forge"}, con = {"road"}},
        charter = {icon = "wh3_dlc23_edict_chd_architects.png", pro = {"road"}, con = {"legion"}},
    }},
    worship = {icon = "chd_conclave_influence.png",
               order = {"rites", "fires", "seats", "lore", "licence"},
               opts = {
        rites   = {icon = "chd_conclave_influence.png"},
        fires   = {icon = "wh3_dlc23_unit_passive_burning_bright.png", pro = {"temple"}, con = {"tower"}},
        seats   = {icon = "chd_toz_tier.png", pro = {"tower"}, con = {"temple"}},
        lore    = {icon = "loremaster.png", pro = {"tower"}, con = {"hearth"}},
        licence = {icon = "hellforged.png", pro = {"forge"}, con = {"temple"}},
    }},
    war = {icon = "edict_levy_conscripts.png",
           order = {"levy", "hellforge", "legions", "grudge", "gunnery"},
           opts = {
        levy      = {icon = "edict_levy_conscripts.png"},
        hellforge = {icon = "chd_armaments.png", pro = {"forge"}, con = {"legion"}},
        legions   = {icon = "chd_toz_district_t3_military.png", pro = {"legion"}, con = {"forge"}},
        grudge    = {icon = "wh3_dlc23_unit_passive_oath_of_contempt.png", pro = {"legion"}, con = {"ledger"}},
        gunnery   = {icon = "artillery.png", pro = {"forge"}, con = {"hearth"}},
    }},
}
IC.LAW_SIDES = {aye = true, nay = true, abstain = true}

function IC.laws_on(faction_key)
    return IC.TUNE.laws ~= false and IC.is_human(faction_key)
end

function IC.law_bundle(category, option)
    return "derpy_ic_law_" .. category .. "_" .. option
end

function IC.law_opt(category, option)
    local c = IC.LAWS[category or ""]
    return c and c.opts[option or ""] or nil
end

-- IC.state, not IC.court: asking what is in force must never create a court.
function IC.law_in_force(faction_key, category)
    local court = faction_key and IC.state[faction_key]
    local held = court and court.laws and court.laws[category]
    if IC.law_opt(category, held) then return held end
    return IC.LAWS[category].order[1]
end

function IC.law_stance(category, option, party)
    local o = IC.law_opt(category, option)
    for _, p in ipairs(o and o.pro or {}) do if p == party then return "aye" end end
    for _, p in ipairs(o and o.con or {}) do if p == party then return "nay" end end
    return nil
end

-- ONE BUNDLE PER CATEGORY on a player court with laws on, none otherwise. All
-- off first, as the government's bundle does, so a swap never wears two.
function IC.apply_law_bundles(faction_key)
    local on = IC.laws_on(faction_key)
    for _, cat in ipairs(IC.LAW_ORDER) do
        for _, opt in ipairs(IC.LAWS[cat].order) do
            cm:remove_effect_bundle(IC.law_bundle(cat, opt), faction_key)
        end
        if on then
            cm:apply_effect_bundle(IC.law_bundle(cat, IC.law_in_force(faction_key, cat)),
                                   faction_key, -1)
        end
    end
end
```

In `new_court()`, after `        confed_turn = 0,  -- the turn this court last took in a confederation`:

```lua
        -- THE LAWS (spec 2026-10-02 laws): [category] = option where it is not
        -- the start, and [category] = the open vote. law_rest stays nil until a
        -- party proposes.
        laws = {},
        votes = {},
```

In `IC.LOG_KINDS`, after `    deed = true, drawn = true,`:

```lua
    -- THE LAWS (spec 2026-10-02 laws). key is "category.option".
    law_propose = true, law_pass = true, law_fail = true,
    law_win = true, law_push = true, law_overrule = true,
```

In `IC.EVENTS`, after `    party_drawn        = {2632, true, true},`:

```lua
    -- THE LAWS (spec 2026-10-02 laws).
    law_proposed       = {2633, true, true},
    law_passed         = {2634, true, true},
    law_failed         = {2635, true, true},
```

In `IC.pack`, just before the `return join({` statement:

```lua
    -- THE LAWS (spec 2026-10-02 laws): field 17 is "category,option" per law
    -- away from its start, and "rest,turn"; field 18 is the open votes, as
    -- "category,option,proposer,ends,stance,won,push" with won as cqi:side and
    -- push as party:level, "/" between pairs and "-" for none, then answered as
    -- 1 or 0.
    local laws = {}
    for cat, opt in pairs(court.laws or {}) do laws[#laws + 1] = cat .. "," .. opt end
    table.sort(laws)
    if (court.law_rest or 0) > 0 then laws[#laws + 1] = "rest," .. tostring(court.law_rest) end
    local votes = {}
    for cat, v in pairs(court.votes or {}) do
        local won, push = {}, {}
        for cqi, side in pairs(v.won or {}) do won[#won + 1] = tostring(cqi) .. ":" .. side end
        for party, level in pairs(v.push or {}) do push[#push + 1] = party .. ":" .. tostring(level) end
        table.sort(won)
        table.sort(push)
        votes[#votes + 1] = string.format("%s,%s,%s,%d,%s,%s,%s,%d", cat, v.option,
            v.proposer or IC.CROWN, v.ends or 0, v.stance or "abstain",
            #won > 0 and table.concat(won, "/") or "-",
            #push > 0 and table.concat(push, "/") or "-", v.answered and 1 or 0)
    end
    table.sort(votes)
```

and change the end of the `return join({...` list from `gov, join(renown, ";"), deeds}, "|")` to `gov, join(renown, ";"), deeds, join(laws, ";"), join(votes, ";")}, "|")`.

In `IC.unpack`, just before `    IC.state[faction_key] = court`:

```lua
    -- Fields 17 and 18 are optional: a save from before laws holds the start
    -- options and no votes. A law this build no longer has is dropped.
    for _, entry in ipairs(split(fields[17] or "", ";")) do
        local b = split(entry, ",")
        if b[1] == "rest" then
            court.law_rest = tonumber(b[2])
        elseif IC.law_opt(b[1], b[2]) and b[2] ~= IC.LAWS[b[1]].order[1] then
            court.laws[b[1]] = b[2]
        end
    end
    for _, entry in ipairs(split(fields[18] or "", ";")) do
        local b = split(entry, ",")
        if #b >= 7 and IC.law_opt(b[1], b[2]) then
            local v = {option = b[2], proposer = b[3], ends = tonumber(b[4]) or 0,
                       stance = IC.LAW_SIDES[b[5]] and b[5] or "abstain", won = {}, push = {},
                       answered = (b[8] == "1") or nil}
            if b[6] ~= "-" then
                for _, pair in ipairs(split(b[6], "/")) do
                    local p = split(pair, ":")
                    local cqi = tonumber(p[1])
                    if cqi and (p[2] == "aye" or p[2] == "nay") then v.won[cqi] = p[2] end
                end
            end
            if b[7] ~= "-" then
                for _, pair in ipairs(split(b[7], "/")) do
                    local p = split(pair, ":")
                    local level = tonumber(p[2])
                    if p[1] and level and level >= 1 and level <= #IC.TUNE.law_push_cost then
                        v.push[p[1]] = level
                    end
                end
            end
            court.votes[b[1]] = v
        end
    end
```

At the end of `IC.settle_switches`, after `    if not IC.governments_on() then IC.apply_gov_bundle(faction_key) end`:

```lua
    -- LAWS OFF DROPS THE OPEN VOTES; on or off, the bundles follow the switch.
    -- The laws in force stay in the save (spec 2026-10-02 laws section 5).
    if IC.TUNE.laws == false then IC.court(faction_key).votes = {} end
    IC.apply_law_bundles(faction_key)
```

In `IC.refresh_live_tune`, replace `       or off.gov_drift then` with:

```lua
       or off.gov_drift or off.laws ~= nil then
```

(`off.laws` is `false` when the switch was turned ON, and its bundles go back on now, not at the next turn.)

In the MCT file's `SWITCHES`, after the `deeds` entry:

```lua
    {"laws", "Laws", "systems",
     "Your court passes laws by a vote of its men: four kinds, five laws each. "
     .. "You and the parties propose them, and you can push, win men or overrule. "
     .. "Off, no law applies and open votes end; the laws in force come back when "
     .. "you turn it on.", true},
```

- [ ] **Step 4: Run the harness and watch it pass.**

Run: `luac -p` on the model and the MCT file, then the harness command.
Expected: both files parse; `iron court harness: ok (932 checks)`. Seven new checks; the LIVE check now passes with `laws`.

- [ ] **Step 5: Ledger.** Append `Task 1: complete (...)` with the harness result.

---

### Task 2: The vote engine: voters, party line, tally

**Files:**
- Modify: the model. Insert after `function IC.apply_law_bundles` (Task 1).
- Test: the harness, after Task 1's checks.

**Interfaces:**
- Consumes: Task 1's catalogue and court fields.
- Produces:
  - `IC.law_voters(faction_key) -> {{cqi, party, n}}`, every living man with influence above 0 and a party, richest first, ties by cqi;
  - `IC.law_line(faction_key, vote, category, party) -> side|nil, why`. `why` is one of `"crown"`, `"for"`, `"against"`, `"loyal"`, `"disloyal"`, `"torn"`, `"no_stance"`;
  - `IC.law_mult(level) -> percent`, where level nil or 0 gives 100;
  - `IC.law_tally(faction_key, category, vote?) -> {aye, nay, abstain, men = {{cqi, party, n, side, why, w}}}`. `w` is the weighted vote; an abstaining man adds his `n` to `abstain`;
  - `IC.law_passes(t) -> boolean`, true only when `t.aye > t.nay`;
  - `IC.law_project(faction_key, category, option) -> tally`, the tally with the Crown voting aye and nobody won or pushing;
  - `IC.character_by_cqi(faction_key, cqi) -> character|nil`, a man of the court by cqi. The panel uses it; CA's `cm:get_character_by_cqi` returns `false` and the harness has no stub for it.

- [ ] **Step 1: Write the failing checks.**

```lua
check("laws: each man votes his party's line, and a party with no stance votes by its loyalty", function()
    local court = law_court({{"crown", 100}, {"legion", 80}, {"ledger", 60}, {"forge", 40}})
    local v = law_vote(court, "ash", "aye")
    court.houses.forge.loyalty = IC.TUNE.law_loyal_line
    local t = IC.law_tally(F, "labour")
    assert(t.aye == 220 and t.nay == 60 and t.abstain == 0,
        "loyal: aye " .. t.aye .. " nay " .. t.nay .. " abstain " .. t.abstain)
    court.houses.forge.loyalty = IC.TUNE.law_disloyal_line - 1
    t = IC.law_tally(F, "labour")
    assert(t.aye == 180 and t.nay == 100, "disloyal: aye " .. t.aye .. " nay " .. t.nay)
    court.houses.forge.loyalty = IC.TUNE.law_disloyal_line
    t = IC.law_tally(F, "labour")
    assert(t.aye == 180 and t.nay == 60 and t.abstain == 40, "torn: abstain " .. t.abstain)
    v.stance = "nay"
    court.houses.forge.loyalty = IC.TUNE.law_disloyal_line - 1
    t = IC.law_tally(F, "labour")
    assert(t.aye == 120 and t.nay == 160, "a disloyal party did not vote against a Crown voting nay")
    gov_done()
end)

check("laws: an abstaining Crown casts nothing, and a party with no stance abstains with it", function()
    local court = law_court({{"crown", 100}, {"legion", 80}, {"forge", 40}})
    law_vote(court, "ash", "abstain")
    court.houses.forge.loyalty = 90
    local t = IC.law_tally(F, "labour")
    assert(t.aye == 80 and t.nay == 0 and t.abstain == 140, "aye " .. t.aye .. " abstain " .. t.abstain)
    court.houses.forge.loyalty = 10
    t = IC.law_tally(F, "labour")
    assert(t.nay == 0, "a disloyal party voted against an abstaining Crown")
    gov_done()
end)

check("laws: a man's weight is his influence; no influence casts no vote; a legend votes with the Crown", function()
    local court = law_court({{"legion", 0}, {"legion", 33}, {"legion", 50, true}})
    law_vote(court, "ash", "nay")
    local t = IC.law_tally(F, "labour")
    local seen = {}
    for _, m in ipairs(t.men) do seen[m.cqi] = m end
    assert(not seen[9001], "a man with no influence voted")
    assert(seen[9002] and seen[9002].w == 33 and seen[9002].side == "aye", "the Legion man's vote")
    assert(seen[9003] and seen[9003].party == IC.CROWN and seen[9003].side == "nay",
        "the legend did not vote with the Crown")
    assert(t.aye == 33 and t.nay == 50, "aye " .. t.aye .. " nay " .. t.nay)
    gov_done()
end)

check("laws: a tie fails, and the voters list is richest first", function()
    local court = law_court({{"legion", 60}, {"ledger", 60}, {"legion", 90}})
    law_vote(court, "ash", "abstain")
    local t = IC.law_tally(F, "labour")
    assert(t.aye == 150 and t.nay == 60 and IC.law_passes(t), "a win failed")
    court.standing[9003] = 0
    t = IC.law_tally(F, "labour")
    assert(t.aye == t.nay and not IC.law_passes(t), "a tie passed")
    local v = IC.law_voters(F)
    assert(v[1].n >= v[#v].n and v[1].cqi == 9001, "the voters are not richest first, ties by cqi")
    gov_done()
end)

check("laws: a man who dies mid-vote stops counting, and a won man keeps his side if his party leaves", function()
    local court, chars = law_court({{"legion", 70}, {"ledger", 40}, {"ledger", 25}})
    local v = law_vote(court, "ash", "aye")
    v.won[9003] = "aye"
    chars[1]._dead = true
    local t = IC.law_tally(F, "labour")
    assert(t.aye == 25 and t.nay == 40, "the dead man or the won man: aye " .. t.aye .. " nay " .. t.nay)
    IC.remove_house(F, "ledger")
    t = IC.law_tally(F, "labour")
    local m3 = nil
    for _, m in ipairs(t.men) do if m.cqi == 9003 then m3 = m end end
    assert(m3 and m3.side == "aye" and m3.why == "won", "a won man lost his side with his party")
    gov_done()
end)

check("laws: a party's support level multiplies its line-voting men and not men won away", function()
    local court = law_court({{"legion", 100}, {"legion", 40}, {"ledger", 50}})
    local v = law_vote(court, "ash", "nay")
    v.push.legion = 2
    v.won[9002] = "nay"
    local t = IC.law_tally(F, "labour")
    assert(t.aye == math.floor(100 * IC.TUNE.law_push_mult[2] / 100), "aye " .. t.aye)
    assert(t.nay == 50 + 40, "the won man was multiplied, or lost: nay " .. t.nay)
    gov_done()
end)

check("laws: the projection is the tally with the Crown for it and nobody bought", function()
    local court = law_court({{"crown", 100}, {"legion", 80}, {"ledger", 60}})
    law_vote(court, "lash", "nay").won[9002] = "nay"
    local p = IC.law_project(F, "labour", "ash")
    assert(p.aye == 180 and p.nay == 60, "projection aye " .. p.aye .. " nay " .. p.nay)
    assert(court.votes.labour.option == "lash", "the projection touched the open vote")
    gov_done()
end)
```

- [ ] **Step 2: Run the harness and watch the 7 new checks fail.**

Expected: 7 `FAIL laws:` lines (`IC.law_tally` is nil). Nothing else fails.

- [ ] **Step 3: Implement.** After `IC.apply_law_bundles`:

```lua
-- THE VOTERS (spec section 3.3): every living man of the court with influence
-- and a party, richest first.
function IC.law_voters(faction_key)
    local out = {}
    local faction = real_faction(faction_key)
    local ok, list = pcall(function() return faction:character_list() end)
    if not ok or not list then return out end
    for i = 0, list:num_items() - 1 do
        pcall(function()
            local man = list:item_at(i)
            if man and not man:is_null_interface() and man:is_alive() then
                local cqi = man:command_queue_index()
                local n = IC.standing(faction_key, cqi)
                local party = IC.house_of_character(man, faction_key)
                if n > 0 and party then out[#out + 1] = {cqi = cqi, party = party, n = n} end
            end
        end)
    end
    table.sort(out, function(a, b)
        if a.n ~= b.n then return a.n > b.n end
        return a.cqi < b.cqi
    end)
    return out
end

-- HIS PARTY'S LINE: the side its men vote, or nil, and why.
function IC.law_line(faction_key, vote, category, party)
    if party == IC.CROWN then
        if vote.stance == "abstain" then return nil, "crown" end
        return vote.stance, "crown"
    end
    local s = IC.law_stance(category, vote.option, party)
    if s then return s, s == "aye" and "for" or "against" end
    if vote.stance == "abstain" then return nil, "no_stance" end
    local house = IC.court(faction_key).houses[party]
    local loyalty = house and house.loyalty or IC.TUNE.loyalty_start
    if loyalty >= IC.TUNE.law_loyal_line then return vote.stance, "loyal" end
    if loyalty < IC.TUNE.law_disloyal_line then
        return vote.stance == "aye" and "nay" or "aye", "disloyal"
    end
    return nil, "torn"
end

function IC.law_mult(level)
    if not level or level <= 0 then return 100 end
    return IC.TUNE.law_push_mult[level] or 100
end

-- THE TALLY (spec sections 3.3 and 3.4). A man won votes his won side at his
-- own influence; a man voting his party's line is multiplied by its level.
function IC.law_tally(faction_key, category, vote)
    vote = vote or (IC.court(faction_key).votes or {})[category]
    local t = {aye = 0, nay = 0, abstain = 0, men = {}}
    if not vote then return t end
    local lines = {}
    for _, m in ipairs(IC.law_voters(faction_key)) do
        if not lines[m.party] then
            lines[m.party] = {IC.law_line(faction_key, vote, category, m.party)}
        end
        local side, why = lines[m.party][1], lines[m.party][2]
        local w = m.n
        local won = vote.won and vote.won[m.cqi]
        if won then
            side, why = won, "won"
        elseif side then
            w = math.floor(m.n * IC.law_mult((vote.push or {})[m.party]) / 100)
        end
        t.men[#t.men + 1] = {cqi = m.cqi, party = m.party, n = m.n, side = side, why = why, w = w}
        if side then t[side] = t[side] + w else t.abstain = t.abstain + m.n end
    end
    return t
end

function IC.law_passes(t) return t.aye > t.nay end

-- WHAT THE COURT WOULD SAY TODAY (spec section 4.1): the Crown for it, nobody
-- won, nobody pushing.
function IC.law_project(faction_key, category, option)
    return IC.law_tally(faction_key, category,
                        {option = option, stance = "aye", won = {}, push = {}})
end

function IC.character_by_cqi(faction_key, cqi)
    local faction = real_faction(faction_key)
    local ok, list = pcall(function() return faction:character_list() end)
    if not ok or not list then return nil end
    for i = 0, list:num_items() - 1 do
        local man = list:item_at(i)
        if man and not man:is_null_interface() and man:command_queue_index() == cqi then
            return man
        end
    end
    return nil
end
```

- [ ] **Step 4: Run the harness and watch it pass.**

Expected: `iron court harness: ok (939 checks)`.

- [ ] **Step 5: Ledger.**

---

### Task 3: Paying: the party purse, winning men, support levels, overrule

**Files:**
- Modify: the model.
  - Replace `function IC.crown_purse` and `function IC.spend_crown` (around line 5617) with the generalised pair.
  - Insert the law prices and ops after `IC.law_project`.
- Test: the harness.

**Interfaces:**
- Consumes: Task 2's `IC.law_tally` and `IC.law_line`.
- Produces:
  - `IC.party_purse(faction_key, slug) -> total, men`, the old `crown_purse` body for any party;
  - `IC.spend_party(faction_key, slug, cost) -> true | false, short`;
  - `IC.crown_purse` and `IC.spend_crown` stay, as one-line calls into the new pair;
  - `IC.law_vote_of(faction_key, category) -> vote|nil`, nil when laws are off for this court;
  - `IC.law_win_price(faction_key, category, cqi) -> price | nil, why`. `why` is one of `"law_none"`, `"law_abstain"`, `"law_no_man"`, `"law_crown_man"`, `"law_won"`, `"law_with_you"`;
  - `IC.law_win(faction_key, category, cqi) -> true | false, why, n`;
  - `IC.law_push_price(vote, party, level) -> cost`, the difference from the level already bought;
  - `IC.law_can_push(faction_key, category, level) -> true | false, why, n`. `why` is one of `"law_none"`, `"law_abstain"`, `"law_pushed"`, `"no such level"`, `"law_purse"`;
  - `IC.law_push(faction_key, category, level) -> true | false, why, n`;
  - `IC.law_set_stance(faction_key, category, stance) -> true | false, why`. It also sets `vote.answered`;
  - `IC.law_overrule(faction_key, category, pass) -> true | false, why, n`;
  - `IC.law_settle(faction_key, category, passed)`, the pass or fail described in Task 4. It is defined here because overrule needs it.

- [ ] **Step 1: Write the failing checks.**

```lua
check("laws: a party's purse is its men's influence above their seat bars, and spending never unseats", function()
    local court = law_court({{"legion", 300}, {"legion", 0}})
    local office = nil
    for _, o in ipairs(IC.OFFICES) do if o.tier == 4 then office = o break end end
    court.offices[office.slug] = 9002
    local bar = IC.tier_influence(4)
    court.standing[9002] = bar + 50
    local total, men = IC.party_purse(F, "legion")
    assert(total == 350 and men[1].cqi == 9001, "the Legion's purse holds " .. total)
    local ok, short = IC.spend_party(F, "legion", 351)
    assert(not ok and short == 1, "an overdraft was paid")
    assert(IC.spend_party(F, "legion", 350) and court.standing[9002] == bar and court.standing[9001] == 0,
        "a seat's bar was spent")
    assert(IC.crown_purse(F) == IC.party_purse(F, IC.CROWN), "the Crown's purse is not the party purse")
    gov_done()
end)

check("laws: a man's price is half his influence, by ambition, doubled when his party is against you", function()
    local court = law_court({{"crown", 2000}, {"ledger", 200}, {"forge", 200}, {"legion", 100}})
    law_vote(court, "ash", "aye")
    court.houses.forge.loyalty = 50
    court.ambition[9002] = "cautious"
    local cautious = math.floor(200 * IC.TUNE.law_win_rate * IC.TUNE.law_win_ambition.cautious / 10000)
    assert(IC.law_win_price(F, "labour", 9002) == 2 * cautious,
        "a cautious Ledger man costs " .. tostring(IC.law_win_price(F, "labour", 9002)))
    court.ambition[9003] = "ambitious"
    assert(IC.law_win_price(F, "labour", 9003)
        == math.floor(200 * IC.TUNE.law_win_rate * IC.TUNE.law_win_ambition.ambitious / 10000),
        "a torn Forge man was doubled, or misprized")
    local p, why = IC.law_win_price(F, "labour", 9001)
    assert(p == nil and why == "law_crown_man", "a Crown man can be won")
    p, why = IC.law_win_price(F, "labour", 9004)
    assert(p == nil and why == "law_with_you", "a man already voting your way can be won")
    gov_done()
end)

check("laws: winning a man moves his vote, costs the Crown's own weight, and works once", function()
    local court = law_court({{"crown", 1000}, {"ledger", 200}})
    law_vote(court, "ash", "aye")
    local price = IC.law_win_price(F, "labour", 9002)
    local before = IC.law_tally(F, "labour")
    assert(IC.law_win(F, "labour", 9002), "the win was refused")
    local after = IC.law_tally(F, "labour")
    assert(after.aye == before.aye - price + 200 and after.nay == before.nay - 200,
        "aye " .. before.aye .. " -> " .. after.aye .. ", nay " .. before.nay .. " -> " .. after.nay)
    local ok, why = IC.law_win(F, "labour", 9002)
    assert(not ok and why == "law_won", "a man was won twice")
    court.standing[9001] = 0
    court.votes.labour.won = {}
    ok, why = IC.law_win(F, "labour", 9002)
    assert(not ok and why == "law_purse", "an empty purse won a man: " .. tostring(why))
    gov_done()
end)

check("laws: support levels cost the difference, never lower, and the Crown cannot push while abstaining", function()
    local court = law_court({{"crown", 5000}})
    local v = law_vote(court, "ash", "aye")
    local c = IC.TUNE.law_push_cost
    assert(IC.law_push_price(v, IC.CROWN, 2) == c[2], "level 2 from nothing")
    local purse = IC.crown_purse(F)
    assert(IC.law_push(F, "labour", 1) and v.push.crown == 1 and IC.crown_purse(F) == purse - c[1],
        "level 1 was not bought at its price")
    assert(IC.law_push_price(v, IC.CROWN, 3) == c[3] - c[1], "the raise is not the difference")
    assert(IC.law_push(F, "labour", 3) and IC.crown_purse(F) == purse - c[3], "the raise to 3 cost wrong")
    local ok, why = IC.law_push(F, "labour", 2)
    assert(not ok and why == "law_pushed", "a level was lowered")
    v.stance = "abstain"
    v.push.crown = nil
    ok, why = IC.law_push(F, "labour", 1)
    assert(not ok and why == "law_abstain", "an abstaining Crown pushed")
    gov_done()
end)

check("laws: a Crown that pushed and then changes its stance keeps its level on the new side", function()
    local court = law_court({{"crown", 1000}, {"ledger", 50}})
    local v = law_vote(court, "ash", "aye")
    assert(IC.law_push(F, "labour", 2), "the push was refused")
    local spare = court.standing[9001]
    assert(IC.law_set_stance(F, "labour", "nay") and v.stance == "nay" and v.answered,
        "the stance did not change, or the vote was not marked answered")
    local t = IC.law_tally(F, "labour")
    assert(t.nay == 50 + math.floor(spare * IC.TUNE.law_push_mult[2] / 100), "the level did not follow: nay " .. t.nay)
    assert(IC.law_set_stance(F, "labour", "abstain"), "abstain refused")
    t = IC.law_tally(F, "labour")
    assert(t.abstain == spare and t.aye == 0, "an abstaining Crown was multiplied or counted")
    assert(not IC.law_set_stance(F, "labour", "maybe"), "a made-up stance was taken")
    gov_done()
end)

check("laws: overrule decides now either way, and the losing parties lose loyalty", function()
    local court = law_court({{"crown", 2000}, {"legion", 100}, {"ledger", 100}})
    law_vote(court, "ash", "aye")
    local l0, d0 = court.houses.legion.loyalty, court.houses.ledger.loyalty
    assert(IC.law_overrule(F, "labour", false), "overrule refused")
    assert(court.votes.labour == nil and IC.law_in_force(F, "labour") == "measure", "a failed overrule passed it")
    -- The Legion lost the overrule and proposed the law that failed: both hits.
    assert(court.houses.legion.loyalty
        == math.max(0, l0 + IC.TUNE.law_overrule_loyalty + IC.TUNE.law_fail_loss)
        and court.houses.ledger.loyalty == d0, "the wrong party paid for the overrule")
    law_vote(court, "ash", "aye")
    d0 = court.houses.ledger.loyalty
    assert(IC.law_overrule(F, "labour", true) and IC.law_in_force(F, "labour") == "ash", "a passing overrule failed")
    assert(court.houses.ledger.loyalty
        == math.max(0, d0 + IC.TUNE.law_overrule_loyalty + IC.TUNE.law_pass_loss),
        "the Ledger did not pay for losing an overruled vote")
    court.standing[9001] = 0
    law_vote(court, "lash", "aye")
    local ok, why = IC.law_overrule(F, "labour", true)
    assert(not ok and why == "law_purse" and court.votes.labour, "an empty purse overruled")
    gov_done()
end)
```

- [ ] **Step 2: Run the harness and watch the 6 new checks fail.**

Expected: 6 `FAIL laws:` lines (`IC.party_purse` is nil). The governments purse check still passes.

- [ ] **Step 3: Implement.** Replace `function IC.crown_purse(faction_key) ... end` and `function IC.spend_crown(faction_key, cost) ... end` with:

```lua
-- WHAT A PARTY'S MEN CAN SPARE (plan ruling 5; spec 2026-10-02 laws section
-- 3.4): each man's influence above his own seat's bar, richest first, so
-- paying never unseats anybody.
function IC.party_purse(faction_key, slug)
    local court, men, total, bar = IC.court(faction_key), {}, 0, {}
    for office_slug, cqi in pairs(court.offices) do
        local office = IC.office_by_slug(office_slug)
        if office then bar[cqi] = math.max(bar[cqi] or 0, IC.tier_influence(office.tier)) end
    end
    local faction = real_faction(faction_key)
    local ok, list = pcall(function() return faction:character_list() end)
    if not ok or not list then return 0, men end
    for i = 0, list:num_items() - 1 do
        pcall(function()
            local man = list:item_at(i)
            if man and not man:is_null_interface() and man:is_alive()
               and IC.house_of_character(man, faction_key) == slug then
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

function IC.spend_party(faction_key, slug, cost)
    local total, men = IC.party_purse(faction_key, slug)
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

function IC.crown_purse(faction_key) return IC.party_purse(faction_key, IC.CROWN) end
function IC.spend_crown(faction_key, cost) return IC.spend_party(faction_key, IC.CROWN, cost) end
```

After `IC.law_project`:

```lua
function IC.law_vote_of(faction_key, category)
    if not IC.laws_on(faction_key) then return nil end
    return (IC.court(faction_key).votes or {})[category]
end

local function law_key(category, vote) return category .. "." .. vote.option end

-- A MAN'S PRICE (spec section 3.4), or nil and why he cannot be won.
function IC.law_win_price(faction_key, category, cqi)
    local vote = IC.law_vote_of(faction_key, category)
    if not vote then return nil, "law_none" end
    if vote.stance == "abstain" then return nil, "law_abstain" end
    local man = nil
    for _, m in ipairs(IC.law_tally(faction_key, category, vote).men) do
        if m.cqi == cqi then man = m end
    end
    if not man then return nil, "law_no_man" end
    if man.party == IC.CROWN then return nil, "law_crown_man" end
    if vote.won[cqi] then return nil, "law_won" end
    if man.side == vote.stance then return nil, "law_with_you" end
    local amb = IC.TUNE.law_win_ambition[IC.ambition_slug(faction_key, cqi) or "steady"] or 100
    local price = math.floor(man.n * IC.TUNE.law_win_rate * amb / 10000)
    local s = IC.law_stance(category, vote.option, man.party)
    if s and s ~= vote.stance then price = price * 2 end
    return math.max(1, price)
end

function IC.law_win(faction_key, category, cqi)
    local price, why = IC.law_win_price(faction_key, category, cqi)
    if not price then return false, why end
    local ok, short = IC.spend_crown(faction_key, price)
    if not ok then return false, "law_purse", short end
    local vote = IC.law_vote_of(faction_key, category)
    vote.won[cqi] = vote.stance
    local party = nil
    for _, m in ipairs(IC.law_tally(faction_key, category, vote).men) do
        if m.cqi == cqi then party = m.party end
    end
    IC.log(faction_key, "law_win", party, law_key(category, vote), price)
    IC.save(faction_key)
    return true
end

function IC.law_push_price(vote, party, level)
    local cost = IC.TUNE.law_push_cost
    local had = (vote.push or {})[party]
    return cost[level] - (had and cost[had] or 0)
end

function IC.law_can_push(faction_key, category, level)
    local vote = IC.law_vote_of(faction_key, category)
    if not vote then return false, "law_none" end
    if not IC.TUNE.law_push_cost[level or 0] then return false, "no such level" end
    if vote.stance == "abstain" then return false, "law_abstain" end
    if level <= (vote.push[IC.CROWN] or 0) then return false, "law_pushed" end
    local price = IC.law_push_price(vote, IC.CROWN, level)
    local total = IC.crown_purse(faction_key)
    if total < price then return false, "law_purse", price - total end
    return true
end

function IC.law_push(faction_key, category, level)
    local ok, why, n = IC.law_can_push(faction_key, category, level)
    if not ok then return false, why, n end
    local vote = IC.law_vote_of(faction_key, category)
    local price = IC.law_push_price(vote, IC.CROWN, level)
    IC.spend_crown(faction_key, price)
    vote.push[IC.CROWN] = level
    IC.log(faction_key, "law_push", IC.CROWN, law_key(category, vote), level)
    IC.save(faction_key)
    return true
end

function IC.law_set_stance(faction_key, category, stance)
    local vote = IC.law_vote_of(faction_key, category)
    if not vote then return false, "law_none" end
    if not IC.LAW_SIDES[stance or ""] then return false, "no such stance" end
    vote.stance = stance
    vote.answered = true
    IC.save(faction_key)
    return true
end

-- THE END OF A VOTE (spec section 3.5), by tally or by overrule.
function IC.law_settle(faction_key, category, passed)
    local court = IC.court(faction_key)
    local vote = court.votes[category]
    if not vote then return nil end
    court.votes[category] = nil
    local key = law_key(category, vote)
    if passed then
        if vote.option == IC.LAWS[category].order[1] then
            court.laws[category] = nil
        else
            court.laws[category] = vote.option
        end
        for slug in pairs(court.houses) do
            local s = IC.law_stance(category, vote.option, slug)
            if s == "aye" then IC.move_loyalty(faction_key, slug, IC.TUNE.law_pass_gain)
            elseif s == "nay" then IC.move_loyalty(faction_key, slug, IC.TUNE.law_pass_loss) end
        end
        IC.apply_law_bundles(faction_key)
        IC.log(faction_key, "law_pass", vote.proposer, key, 0)
        IC.feed(faction_key, "law_passed")
    else
        if vote.proposer ~= IC.CROWN then
            IC.move_loyalty(faction_key, vote.proposer, IC.TUNE.law_fail_loss)
        end
        IC.log(faction_key, "law_fail", vote.proposer, key, 0)
        IC.feed(faction_key, "law_failed")
    end
    return passed
end

function IC.law_overrule(faction_key, category, pass)
    local vote = IC.law_vote_of(faction_key, category)
    if not vote then return false, "law_none" end
    local ok, short = IC.spend_crown(faction_key, IC.TUNE.law_overrule_cost)
    if not ok then return false, "law_purse", short end
    local losing = pass and "nay" or "aye"
    local court = IC.court(faction_key)
    local slugs = {}
    for slug in pairs(court.houses) do slugs[#slugs + 1] = slug end
    table.sort(slugs)
    for _, slug in ipairs(slugs) do
        if slug ~= IC.CROWN and IC.law_line(faction_key, vote, category, slug) == losing then
            IC.move_loyalty(faction_key, slug, IC.TUNE.law_overrule_loyalty)
        end
    end
    IC.log(faction_key, "law_overrule", IC.CROWN, law_key(category, vote), pass and 1 or 0)
    IC.law_settle(faction_key, category, pass)
    IC.save(faction_key)
    return true
end
```

A start option that passes back clears `court.laws[category]`, since field 17 holds only laws away from the start.

- [ ] **Step 4: Run the harness and watch it pass.**

Expected: `iron court harness: ok (945 checks)`. The governments checks that call `IC.crown_purse` / `IC.spend_crown` still pass.

- [ ] **Step 5: Ledger.**

---

### Task 4: Proposing, resolution in the turn, and the party's two moves

**Files:**
- Modify: the model.
  - Insert `IC.law_can_propose`, `IC.law_open`, `IC.law_propose`, `IC.law_party_pick`, `IC.law_party_push` and `IC.law_turn` after `IC.law_overrule`.
  - In `function IC.turn`, insert `IC.law_turn(faction_key)` just before `    IC.gov_step(faction_key)`.
- Modify: the parties file.
  - After `T.party_feud_equal_motive = 12 -- motive to feud with an equal`, add `T.law_party_motive = 14   -- motive to put a law to the court`.
  - Append a `PARTY_ACTS` entry after the `feud` entry (the block starting `IC.PARTY_ACTS[#IC.PARTY_ACTS + 1] = {\n    key = "feud",`).
- Test: the harness.

**Interfaces:**
- Consumes: Tasks 1 to 3.
- Produces:
  - `IC.law_can_propose(faction_key, category, option) -> true | false, why, n`. `why` is one of `"laws_off"`, `"no such law"`, `"law_open"`, `"law_same"`, `"law_purse"`;
  - `IC.law_open(faction_key, category, option, proposer, stance)`;
  - `IC.law_propose(faction_key, category, option) -> true | false, why, n`;
  - `IC.law_party_pick(faction_key, slug) -> {category, option} | nil`;
  - `IC.law_party_push(faction_key, category) -> number of steps taken`;
  - `IC.law_turn(faction_key)`;
  - `PARTY_ACTS` entry `key = "law"`.

- [ ] **Step 1: Write the failing checks.**

```lua
check("laws: the player proposes for a fee, the Crown votes aye, and the card waits two turns", function()
    local court = law_court({{"crown", 1000}})
    local purse = IC.crown_purse(F)
    assert(IC.law_propose(F, "labour", "ash"), "the proposal was refused")
    local v = court.votes.labour
    assert(v and v.stance == "aye" and v.proposer == IC.CROWN and v.ends == turn + IC.TUNE.law_vote_turns,
        "the vote opened wrong")
    assert(IC.crown_purse(F) == purse - IC.TUNE.law_propose_cost, "the fee was not paid")
    local ok, why = IC.law_propose(F, "labour", "lash")
    assert(not ok and why == "law_open", "two votes in one category")
    ok, why = IC.law_propose(F, "tribute", "tithe")
    assert(not ok and why == "law_same", "the law in force was proposed")
    court.standing[9001] = 0
    ok, why = IC.law_propose(F, "war", "gunnery")
    assert(not ok and why == "law_purse", "an empty purse proposed")
    gov_done()
end)

check("laws: at its end a vote passes or fails in the turn, moves loyalty and swaps the bundle", function()
    local court = law_court({{"crown", 100}, {"legion", 300}, {"ledger", 50}})
    law_vote(court, "ash", "abstain", "legion")
    local l0, d0 = court.houses.legion.loyalty, court.houses.ledger.loyalty
    turn = turn + IC.TUNE.law_vote_turns
    IC.law_turn(F)
    assert(court.votes.labour == nil and IC.law_in_force(F, "labour") == "ash", "the vote did not pass")
    assert(court.houses.legion.loyalty == math.min(100, l0 + IC.TUNE.law_pass_gain)
        and court.houses.ledger.loyalty == math.max(0, d0 + IC.TUNE.law_pass_loss), "pass loyalty")
    assert(applied[IC.law_bundle("labour", "ash")] and not applied[IC.law_bundle("labour", "measure")],
        "the bundle did not swap")
    law_vote(court, "lash", "nay", "legion")
    court.votes.labour.ends = turn
    l0 = court.houses.legion.loyalty
    IC.law_turn(F)
    assert(IC.law_in_force(F, "labour") == "ash", "a failed vote changed the law")
    assert(court.houses.legion.loyalty == math.max(0, l0 + IC.TUNE.law_fail_loss), "the proposer lost nothing")
    gov_done()
end)

check("laws: a vote whose proposer has left still resolves", function()
    local court = law_court({{"crown", 100}, {"ledger", 300}})
    court.houses.chain = {weight = 1, loyalty = 50}
    law_vote(court, "lash", "abstain", "chain")
    IC.remove_house(F, "chain")
    court.votes.labour.ends = turn
    IC.law_turn(F)
    local last = court.log[#court.log]
    assert(court.votes.labour == nil and last.kind == "law_fail" and last.slug == "chain",
        "a departed proposer's vote did not resolve")
    gov_done()
end)

check("laws: a party proposes only what it is for, with share, in a free category, after its rest", function()
    local court = law_court({{"legion", 100}}, {crown = 10, legion = 90})
    turn = IC.TUNE.law_party_rest + 10
    local pick = IC.law_party_pick(F, "legion")
    assert(pick and IC.law_stance(pick.category, pick.option, "legion") == "aye", "a pick it is not for")
    court.law_rest = turn - 1
    assert(IC.law_party_pick(F, "legion") == nil, "it proposed during its rest")
    court.law_rest = turn - IC.TUNE.law_party_rest
    court.houses.legion.weight = 0
    court.houses.crown.weight = 1000
    assert(IC.law_party_pick(F, "legion") == nil, "a party under the share line proposed")
    court.houses.legion.weight = 900
    for _, cat in ipairs(IC.LAW_ORDER) do law_vote(court, "ash"); court.votes[cat] = court.votes.labour end
    assert(IC.law_party_pick(F, "legion") == nil, "it proposed into a category with a vote open")
    cm.get_human_factions = function() return {} end
    court.votes = {}
    assert(IC.law_party_pick(F, "legion") == nil, "an AI court's party proposed")
    gov_done()
end)

check("laws: a party's proposal opens abstaining and starts the court's rest", function()
    local court = law_court({{"legion", 100}}, {crown = 10, legion = 90})
    local act = nil
    -- ALL_ACTS: the harness keeps only build 1's acts in IC.PARTY_ACTS.
    for _, a in ipairs(ALL_ACTS) do if a.key == "law" then act = a end end
    assert(act, "no law act")
    act.act(F, "legion", {category = "war", option = "legions"})
    local v = court.votes.war
    assert(v and v.stance == "abstain" and v.proposer == "legion" and court.law_rest == turn,
        "the party's vote opened wrong")
    gov_done()
end)

check("laws: a party with a stake pushes one step a turn when losing or close, if it can pay", function()
    local court = law_court({{"crown", 1000}, {"legion", 400}, {"ledger", 300}})
    local v = law_vote(court, "ash", "nay", "legion")
    IC.law_party_push(F, "labour")
    assert(v.push.legion == 1 and not v.push.ledger, "the losing Legion did not push, or the Ledger did")
    assert(court.standing[9002] == 400 - IC.TUNE.law_push_cost[1], "the Legion did not pay")
    IC.law_party_push(F, "labour")
    assert(v.push.legion == 2, "the Legion did not push again next turn")
    court.standing[9002] = 10
    IC.law_party_push(F, "labour")
    assert(v.push.legion == 2, "a party pushed with an empty purse")
    gov_done()
end)

check("laws: a party with no stance never pushes, and a party well ahead does not", function()
    local court = law_court({{"crown", 10}, {"legion", 900}, {"forge", 500}})
    local v = law_vote(court, "ash", "aye", "legion")
    court.houses.forge.loyalty = 10
    IC.law_party_push(F, "labour")
    assert(not v.push.forge, "a party voting by loyalty pushed")
    assert(not v.push.legion, "a party far ahead pushed")
    gov_done()
end)
```

- [ ] **Step 2: Run the harness and watch the 7 new checks fail.**

Expected: 7 `FAIL laws:` lines (`IC.law_propose` is nil).

- [ ] **Step 3: Implement.** After `IC.law_overrule`:

```lua
function IC.law_can_propose(faction_key, category, option)
    if not IC.laws_on(faction_key) then return false, "laws_off" end
    if not IC.law_opt(category, option) then return false, "no such law" end
    if (IC.court(faction_key).votes or {})[category] then return false, "law_open" end
    if IC.law_in_force(faction_key, category) == option then return false, "law_same" end
    local total = IC.crown_purse(faction_key)
    if total < IC.TUNE.law_propose_cost then
        return false, "law_purse", IC.TUNE.law_propose_cost - total
    end
    return true
end

function IC.law_open(faction_key, category, option, proposer, stance)
    IC.court(faction_key).votes[category] = {option = option, proposer = proposer,
        ends = cm:model():turn_number() + IC.TUNE.law_vote_turns,
        stance = stance, won = {}, push = {}}
    IC.log(faction_key, "law_propose", proposer, category .. "." .. option, 0)
    IC.feed(faction_key, "law_proposed")
end

function IC.law_propose(faction_key, category, option)
    local ok, why, n = IC.law_can_propose(faction_key, category, option)
    if not ok then return false, why, n end
    IC.spend_crown(faction_key, IC.TUNE.law_propose_cost)
    IC.law_open(faction_key, category, option, IC.CROWN, "aye")
    IC.save(faction_key)
    return true
end

-- WHAT A PARTY WOULD PUT TO THE COURT (spec section 3.2), picked with
-- cm:random_number so every machine picks the same.
function IC.law_party_pick(faction_key, slug)
    if not IC.laws_on(faction_key) then return nil end
    local court = IC.court(faction_key)
    local now = cm:model():turn_number()
    if now - (court.law_rest or 0) < IC.TUNE.law_party_rest then return nil end
    if IC.share(faction_key, slug) < IC.TUNE.law_party_share then return nil end
    local list = {}
    for _, cat in ipairs(IC.LAW_ORDER) do
        if not court.votes[cat] then
            for _, opt in ipairs(IC.LAWS[cat].order) do
                if opt ~= IC.law_in_force(faction_key, cat)
                   and IC.law_stance(cat, opt, slug) == "aye" then
                    list[#list + 1] = {category = cat, option = opt}
                end
            end
        end
    end
    if #list == 0 then return nil end
    return list[cm:random_number(#list, 1)]
end

-- THE PARTIES WITH A STAKE PUSH (spec section 3.4): one step each, in slug
-- order, when their side is losing or within the margin and they can pay.
function IC.law_party_push(faction_key, category)
    local court = IC.court(faction_key)
    local vote = court.votes[category]
    if not vote then return 0 end
    local slugs = {}
    for slug in pairs(court.houses) do
        if slug ~= IC.CROWN and IC.law_stance(category, vote.option, slug) then
            slugs[#slugs + 1] = slug
        end
    end
    table.sort(slugs)
    local steps = 0
    for _, slug in ipairs(slugs) do
        local side = IC.law_stance(category, vote.option, slug)
        local other = side == "aye" and "nay" or "aye"
        local level = (vote.push[slug] or 0) + 1
        if IC.TUNE.law_push_cost[level] then
            local t = IC.law_tally(faction_key, category, vote)
            local margin = math.floor((t.aye + t.nay + t.abstain) * IC.TUNE.law_push_margin / 100)
            local price = IC.law_push_price(vote, slug, level)
            if t[side] - t[other] <= margin and IC.spend_party(faction_key, slug, price) then
                vote.push[slug] = level
                IC.log(faction_key, "law_push", slug, category .. "." .. vote.option, level)
                steps = steps + 1
            end
        end
    end
    return steps
end

-- ONCE A TURN, player courts (spec section 3.5): votes at their end resolve,
-- the rest are pushed, and the bundles are worn.
function IC.law_turn(faction_key)
    if not IC.laws_on(faction_key) then return nil end
    local court = IC.court(faction_key)
    local now = cm:model():turn_number()
    for _, cat in ipairs(IC.LAW_ORDER) do
        local vote = court.votes[cat]
        if vote and now >= vote.ends then
            IC.law_settle(faction_key, cat, IC.law_passes(IC.law_tally(faction_key, cat, vote)))
        elseif vote then
            IC.law_party_push(faction_key, cat)
        end
    end
    IC.apply_law_bundles(faction_key)
end
```

In `IC.turn`, replace `    IC.gov_step(faction_key)` with:

```lua
    -- BEFORE THE GOVERNMENT (spec 2026-10-02 laws section 3.5).
    IC.law_turn(faction_key)
    IC.gov_step(faction_key)
```

In the parties file, after the `feud` entry's closing `}`:

```lua

-- PUTTING A LAW TO THE COURT (spec 2026-10-02 laws section 3.2). It opens with
-- the Crown abstaining, and the panel's marker waits for the player's answer.
IC.PARTY_ACTS[#IC.PARTY_ACTS + 1] = {
    key = "law",
    can = function(faction_key, slug) return IC.law_party_pick(faction_key, slug) end,
    motive = function() return T.law_party_motive end,
    act = function(faction_key, slug, t)
        IC.law_open(faction_key, t.category, t.option, slug, "abstain")
        IC.court(faction_key).law_rest = cm:model():turn_number()
    end,
}
```

- [ ] **Step 4: Run the harness and watch it pass.**

Expected: `iron court harness: ok (952 checks)`. In particular, `no parties' turn failed anywhere in the run` stays green. The new act runs inside every `IC.turn` the harness drives.

- [ ] **Step 5: Ledger.**

---

### Task 5: The five multiplayer ops

**Files:**
- Modify: the model. After `IC.MP_OPS.doctrine = function(fk, arg) ... end`.
- Test: the harness. The MP routing check `each of the twelve actions waits for its trigger...` (around line 21691): add five case rows and raise the count from 15 to 20.

**Interfaces:**
- Consumes: Tasks 3 and 4's ops.
- Produces the wire args:
  - `law_propose` takes `"category|option"`;
  - `law_stance` takes `"category|aye|nay|abstain"`;
  - `law_win` takes `"category|cqi"`;
  - `law_push` takes `"category|level"`;
  - `law_overrule` takes `"category|1"` to pass or `"category|0"` to fail.

- [ ] **Step 1: Write the failing check.** In the routing check's case table, after `        {"doctrine", "legion", "gov_force", 1, {"legion"}},`, add:

```lua
        {"law_propose", "labour|ash", "law_propose", 2, {"labour", "ash"}},
        {"law_stance", "labour|nay", "law_set_stance", 2, {"labour", "nay"}},
        {"law_win", "labour|9002", "law_win", 2, {"labour", 9002}},
        {"law_push", "labour|2", "law_push", 2, {"labour", 2}},
        {"law_overrule", "labour|1", "law_overrule", 2, {"labour", true}},
```

and change `assert(n_ops == 15, "IC.MP_OPS holds " .. n_ops .. " actions; the panel has fifteen")` to `assert(n_ops == 20, "IC.MP_OPS holds " .. n_ops .. " actions; the panel has twenty")`. Read the check's loop body before running it. If it compares args with `==`, the boolean `true` for overrule and the number `9002` are what the op must pass. Rename the check's title count to match.

- [ ] **Step 2: Run the harness and watch it fail.**

Expected: one FAIL on the routing check (`IC.MP_OPS holds 15 actions`).

- [ ] **Step 3: Implement.** After `IC.MP_OPS.doctrine`:

```lua
-- THE LAWS (spec 2026-10-02 laws section 5). Every one is re-checked by the
-- model function it calls.
IC.MP_OPS.law_propose = function(fk, arg)      -- category|option
    local f = fields(arg)
    return answer(fk, "law_propose", arg, IC.law_propose(fk, f[1], f[2]))
end
IC.MP_OPS.law_stance = function(fk, arg)       -- category|aye|nay|abstain
    local f = fields(arg)
    return answer(fk, "law_stance", arg, IC.law_set_stance(fk, f[1], f[2]))
end
IC.MP_OPS.law_win = function(fk, arg)          -- category|cqi
    local f = fields(arg)
    return answer(fk, "law_win", arg, IC.law_win(fk, f[1], tonumber(f[2])))
end
IC.MP_OPS.law_push = function(fk, arg)         -- category|level
    local f = fields(arg)
    return answer(fk, "law_push", arg, IC.law_push(fk, f[1], tonumber(f[2])))
end
IC.MP_OPS.law_overrule = function(fk, arg)     -- category|1 pass, category|0 fail
    local f = fields(arg)
    return answer(fk, "law_overrule", arg, IC.law_overrule(fk, f[1], f[2] == "1"))
end
```

- [ ] **Step 4: Run the harness and watch it pass.**

Expected: `iron court harness: ok (952 checks)`. The count is unchanged, because this check was extended rather than added.

- [ ] **Step 5: Ledger.**

---

### Task 6: The data: bundles, effect wordings, loc, events

**Files:**
- Modify: `tools/gen_iron_court.py`:
  - effect constants after `E_ENVOY_LAB = (...)`;
  - `ALL_EFFECTS`, `EFFECT_TEXT`, `EFFECT_TEXT_TR`, `EFFECT_SHORT` and `EFFECT_PERCENT`;
  - `effect_line`;
  - a `LAWS` table after `GOVERNMENTS`;
  - `build()`, after the government loop;
  - `EVENTS`, after the `party_drawn` entry;
  - `check_laws()` beside `check_governments()`, called from `check()` where `check_governments()` is.
- Test: `py tools/gen_iron_court.py --check` and `--selftest`, and the harness's event-alignment invariant.

**Interfaces:**
- Consumes: the model's `IC.LAW_ORDER` and `IC.LAWS`, read by regex in `check_laws()`.
- Produces:
  - bundles `derpy_ic_law_<category>_<option>` (20), each with the model's icon;
  - loc entries:
    - `derpy_ic_law_cat_<category>`, the category name;
    - `derpy_ic_law_name_<category>_<option>`, the law name;
    - `derpy_ic_law_fx<i>_<category>_<option>` for i = 1..3, the CA effect lines;
    - the bundle's own `derpy_ic_effects_<bundle>`, the short lines joined by `", "`, which the cards split;
  - three events.

- [ ] **Step 1: Write the failing gate.** Add `check_laws()` and call it from `check()`:

```python
def check_laws():
    """The model's laws and this file's are one catalogue, in one order, each
    option's bundle built and wearing the model's picture (spec 2026-10-02 laws)."""
    lua = _model_lua()
    out = []
    m = re.search(r"IC\.LAW_ORDER\s*=\s*\{([^}]*)\}", lua)
    model_cats = re.findall(r'"(\w+)"', m.group(1)) if m else []
    mine = [c[0] for c in LAWS]
    if model_cats != mine:
        out.append("IC.LAW_ORDER is %s and LAWS is %s" % (model_cats, mine))
    built = {r["key"]: r for r in build()["effect_bundles"]}
    loc = {r["key"]: r["text"] for r in build()["loc"]}
    block = re.search(r"IC\.LAWS = \{(.*?)\n\}", lua, re.S)
    body = block.group(1) if block else ""
    for cat, _name, _icon, options in LAWS:
        cm = re.search(r"\n    %s = \{.*?order = \{([^}]*)\}" % cat, body, re.S)
        order = re.findall(r'"(\w+)"', cm.group(1)) if cm else []
        if order != [o[0] for o in options]:
            out.append("%s: the model's order is %s, here %s" % (cat, order, [o[0] for o in options]))
        for opt, name, _blurb, effects in options:
            key = "derpy_ic_law_%s_%s" % (cat, opt)
            im = re.search(r"\n\s+%s\s*=\s*\{icon = \"([^\"]+)\"" % opt, body)
            row = built.get(key)
            if not row:
                out.append("no bundle %s" % key)
            elif not im or row["ui_icon"] != im.group(1):
                out.append("%s wears %s, not the model's %s"
                           % (key, row["ui_icon"], im.group(1) if im else None))
            if loc.get("derpy_ic_law_name_%s_%s" % (cat, opt)) != name:
                out.append("no name loc for %s" % key)
            if len(effects) > 3:
                out.append("%s has %d effects; a card holds three" % (key, len(effects)))
            if opt == options[0][0] and effects:
                out.append("%s is its category's start and has effects" % key)
    return out
```

- [ ] **Step 2: Run the gate and watch it fail.**

Run: `py tools/gen_iron_court.py --check`
Expected: a `NameError` on `LAWS`, or the check reports `IC.LAW_ORDER is [...] and LAWS is []`.

- [ ] **Step 3: Implement.** Effect constants after `E_ENVOY_LAB`. Reuse `E_WORKLOAD`, which is the same pair:

```python
# THE LAWS (spec 2026-10-02 laws section 2). Every pair below ships in CA's
# junction tables and every flag matches CA's, read 2026-10-02.
E_LAW_CAPTIVES = ("wh_main_effect_force_all_campaign_captives", "faction_to_force_own_unseen", True)
E_LAW_RUSH = ("wh3_dlc23_effect_rush_construction_cost", "faction_to_province_own", False)
E_LAW_LAB_LD = ("wh3_dlc23_effect_force_stat_leadership_chd_labourers", "faction_to_force_own", True)
E_LAW_LAB_UPKEEP = ("wh3_dlc23_effect_upkeep_chd_labourers", "faction_to_force_own", False)
E_LAW_LAB_RANK = ("wh3_dlc23_effect_recruitment_rank_chd_labourers", "faction_to_force_own", True)
E_LAW_RAW_USED = ("wh3_dlc23_pooled_resources_chd_raw_materials_consumed_mod", "faction_to_province_own", False)
E_LAW_RAZE = ("wh_main_effect_force_all_campaign_razing_income", "faction_to_faction_own_unseen", True)
E_LAW_SACK = ("wh_main_effect_force_all_campaign_sacking_income", "faction_to_faction_own_unseen", True)
E_LAW_CONVOYS = ("wh3_dlc23_effect_technology_chd_convoy_mod_active_convoys", "faction_to_faction_own_unseen", True)
E_LAW_AMBUSH = ("wh3_main_effect_caravan_scouts", "faction_to_character_own_unseen", False)
E_LAW_VASSAL = ("wh_main_effect_modify_vassal_income", "faction_to_faction_own_unseen", True)
E_LAW_TARIFF = ("wh3_dlc23_effect_chd_convoy_trade_tariff_scripted", "faction_to_faction_own_unseen", True)
E_LAW_REFINERY = ("wh3_dlc23_effect_economy_gpd_manufacture", "faction_to_region_own_unseen", True)
E_LAW_CARGO_VALUE = ("wh3_main_effect_caravan_cargo_value", "faction_to_character_own_unseen", True)
E_LAW_MINES = ("wh_main_effect_technology_economy_gdp_mod_mining_dwarfs", "faction_to_region_own_unseen", True)
E_LAW_GOODS = ("wh_main_effect_economy_trade_good_commodity_mod", "faction_to_faction_own_unseen", True)
E_LAW_CARGO_CAP = ("wh3_main_effect_caravan_cargo_capacity", "faction_to_character_own_unseen", True)
E_LAW_OVR_RANK = ("wh3_dlc23_faction_xp_increase_generals_chd_convoy_overseers", "faction_to_faction_own", True)
E_LAW_OVR_XP = ("wh3_dlc23_effect_force_army_campaign_experience_chd_convoy_overseer_per_turn", "faction_to_character_own_unseen", True)
E_LAW_CHD_DIPLO = ("wh3_dlc23_faction_political_diplomacy_mod_chaos_dwarfs", "faction_to_faction_own_unseen", True)
E_LAW_INFLUENCE = ("wh3_dlc23_effect_pooled_resource_conclave_influence_mod_all_sources", "faction_to_faction_own_unseen", True)
E_LAW_CORRUPT = ("wh3_main_effect_corruption_chaos_adjacent_provinces", "faction_to_province_own", True)
E_LAW_TOZ_SEAT = ("wh3_dlc23_effect_toz_chd_conclave_influence_spent_slot_claimed_mod", "faction_to_faction_own_unseen", False)
E_LAW_WOM = ("wh3_dlc23_effect_ability_wom_cost_pct_lore_of_hashut_spells", "faction_to_force_own", False)
E_LAW_COOLDOWN = ("wh3_dlc23_effect_ability_cooldown_lore_of_hashut", "faction_to_force_own", False)
E_LAW_MISCAST = ("wh_main_effect_character_stat_miscast", "faction_to_character_own", False)
E_LAW_KDAAI = ("wh3_dlc23_effect_physical_resist_chd_kdaai", "faction_to_force_own_unseen", True)
E_LAW_TEMPLE_TIME = ("wh3_dlc23_effect_building_construction_time_mod_chd_temple_of_hashut", "faction_to_region_own_unseen", False)
E_LAW_HF_COST = ("wh3_dlc23_chd_ritual_unit_cap_cost_mod_all_toz", "faction_to_faction_own_unseen", False)
E_LAW_HF_CAP = ("wh3_dlc23_effect_chd_hellforge_cap_mod_all", "faction_to_faction_own_unseen", True)
E_LAW_INF_COST = ("wh3_dlc23_effect_force_recruit_cost_chd_chaos_dwarf_infantry", "faction_to_force_own_unseen", False)
E_LAW_INF_RANK = ("wh3_dlc23_effect_force_recruit_rank_chd_chaos_dwarf_infantry", "faction_to_force_own_unseen", True)
E_LAW_ART_UPKEEP = ("wh3_dlc23_effect_upkeep_chd_artillery_warmachines", "faction_to_force_own", False)
E_LAW_DWARF_XP = ("wh3_dlc23_effect_xp_gain_increase_dwarfs", "faction_to_force_own", True)
E_LAW_HOB_UPKEEP = ("wh3_dlc23_effect_upkeep_cost_reduction_chd_labourer_hobgoblin_infantry", "faction_to_force_own_unseen", False)
E_LAW_ART_EXPL = ("wh3_dlc23_effect_force_stat_explosive_damage_chd_artillery", "faction_to_force_own_unseen", True)
E_LAW_ART_RANGE = ("wh3_dlc23_effect_force_stat_range_chd_artillery", "faction_to_force_own_unseen", True)
E_LAW_RANGED_COST = ("wh3_dlc23_effect_recruitment_cost_chd_ranged", "faction_to_province_own", False)
LAW_EFFECTS = [E_LAW_CAPTIVES, E_LAW_RUSH, E_LAW_LAB_LD, E_LAW_LAB_UPKEEP, E_LAW_LAB_RANK,
               E_LAW_RAW_USED, E_LAW_RAZE, E_LAW_SACK, E_LAW_CONVOYS, E_LAW_AMBUSH, E_LAW_VASSAL,
               E_LAW_TARIFF, E_LAW_REFINERY, E_LAW_CARGO_VALUE, E_LAW_MINES, E_LAW_GOODS,
               E_LAW_CARGO_CAP, E_LAW_OVR_RANK, E_LAW_OVR_XP, E_LAW_CHD_DIPLO, E_LAW_INFLUENCE,
               E_LAW_CORRUPT, E_LAW_TOZ_SEAT, E_LAW_WOM, E_LAW_COOLDOWN, E_LAW_MISCAST, E_LAW_KDAAI,
               E_LAW_TEMPLE_TIME, E_LAW_HF_COST, E_LAW_HF_CAP, E_LAW_INF_COST, E_LAW_INF_RANK,
               E_LAW_ART_UPKEEP, E_LAW_DWARF_XP, E_LAW_HOB_UPKEEP, E_LAW_ART_EXPL, E_LAW_ART_RANGE,
               E_LAW_RANGED_COST]
```

Append `+ LAW_EFFECTS` to the `ALL_EFFECTS = [...]` expression.

`EFFECT_TEXT` entries. These are CA's exact `effects_description_*` strings with any `{{tr:}}` resolved, and check 15 re-reads them:

```python
    E_LAW_CAPTIVES[0]: "Casualties captured post-battle: %+n%",
    E_LAW_RUSH[0]: "Rush Construction Labour cost: %+n%",
    E_LAW_LAB_LD[0]: "Leadership: %+n for Labourer units",
    E_LAW_LAB_UPKEEP[0]: "Upkeep: %+n% for Labourers units",
    E_LAW_LAB_RANK[0]: "Recruit rank: %+n for Labourer units",
    E_LAW_RAW_USED[0]: "Raw Materials consumed per turn by buildings: %+n%",
    E_LAW_RAZE[0]: "Income from razing settlements: %+n%",
    E_LAW_SACK[0]: "Income from sacking settlements: %+n%",
    E_LAW_CONVOYS[0]: "Maximum number of active Convoys: %+n",
    E_LAW_AMBUSH[0]: "Chance of Caravan intercept battle being an ambush: %+n%",
    E_LAW_VASSAL[0]: "Tribute from [[img:icon_vassal]][[/img]]vassals: %+n%",
    E_LAW_TARIFF[0]: "Income from trade tariffs: %+n% for every completed Convoy route",
    E_LAW_REFINERY[0]: "Income from Refinery buildings: %+n%",
    E_LAW_CARGO_VALUE[0]: "Sale value of cargo: %+n%",
    E_LAW_MINES[0]: "Income from Iron Mines, Gold Mines and Stone Quarries: %+n%",
    E_LAW_GOODS[0]: "Tradable resources produced: %+n%",
    E_LAW_CARGO_CAP[0]: "Maximum Caravan cargo capacity: %+n%",
    E_LAW_OVR_RANK[0]: "Lord recruit rank: %+n for Convoy Overseer",
    E_LAW_OVR_XP[0]: "Experience per turn: %+n for Convoy Overseers",
    E_LAW_CHD_DIPLO[0]: "Diplomatic relations: %+n with Chaos Dwarfs",
    E_LAW_INFLUENCE[0]: "Conclave Influence gained from all sources: %+n% ",
    E_LAW_CORRUPT[0]: "Chaos Undivided corruption in adjacent provinces: %+n",
    E_LAW_TOZ_SEAT[0]: "Conclave Influence cost for Tower of Zharr Seats: %+n%",
    E_LAW_WOM[0]: "Winds of Magic cost: %+n% for Lore of Hashut spells",
    E_LAW_COOLDOWN[0]: "Cooldown: %+n% to Lore of Hashut spells",
    E_LAW_MISCAST[0]: "Miscast base chance: %+n%",
    E_LAW_KDAAI[0]: "Physical resistance: %n% for all K'daai units",
    E_LAW_TEMPLE_TIME[0]: "Construction time: %+n for Temple of Hashut buildings",
    E_LAW_HF_COST[0]: "Armaments cost: %+n% for all unit capacity upgrades in the Hell-Forge",
    E_LAW_HF_CAP[0]: "Maximum active Hell-Forge Forgecraft Options: %+n",
    E_LAW_INF_COST[0]: "Recruitment cost: %+n% for Chaos Dwarf Infantry units",
    E_LAW_INF_RANK[0]: "Recruit rank: %+n for Chaos Dwarf Infantry",
    E_LAW_ART_UPKEEP[0]: "Upkeep: %+n% for Artillery and War Machine units",
    E_LAW_DWARF_XP[0]: "Double experience gain for units when fighting against Dwarfs",
    E_LAW_HOB_UPKEEP[0]: "Upkeep: %+n% for Labourers and Hobgoblin Infantry units",
    E_LAW_ART_EXPL[0]: "Explosive missile damage: %+n% for Iron Daemon and Artillery units",
    E_LAW_ART_RANGE[0]: "Range: %+n% for Iron Daemon and Artillery units",
    E_LAW_RANGED_COST[0]: "Recruitment cost: %+n% for all Missile Infantry, Artillery and War Machine units",
```

`EFFECT_TEXT_TR` entries:

```python
    E_LAW_AMBUSH[0]: ("wh3_campaign_notification_caravan", "Caravan"),
    E_LAW_CARGO_CAP[0]: ("wh3_campaign_notification_caravan", "Caravan"),
```

`EFFECT_SHORT` entries, each at most 20 characters:

```python
    E_LAW_CAPTIVES[0]: "Captives",
    E_LAW_RUSH[0]: "Rush cost",
    E_LAW_LAB_LD[0]: "Labourer leadership",
    E_LAW_LAB_UPKEEP[0]: "Labourer upkeep",
    E_LAW_LAB_RANK[0]: "Labourer rank",
    E_LAW_RAW_USED[0]: "Raw Materials used",
    E_LAW_RAZE[0]: "Razing income",
    E_LAW_SACK[0]: "Sacking income",
    E_LAW_CONVOYS[0]: "Active Convoys",
    E_LAW_AMBUSH[0]: "Convoy ambush",
    E_LAW_VASSAL[0]: "Vassal tribute",
    E_LAW_TARIFF[0]: "Convoy tariffs",
    E_LAW_REFINERY[0]: "Refinery income",
    E_LAW_CARGO_VALUE[0]: "Cargo value",
    E_LAW_MINES[0]: "Mine income",
    E_LAW_GOODS[0]: "Trade goods",
    E_LAW_CARGO_CAP[0]: "Cargo capacity",
    E_LAW_OVR_RANK[0]: "Overseer rank",
    E_LAW_OVR_XP[0]: "Overseer XP a turn",
    E_LAW_CHD_DIPLO[0]: "Chaos Dwarf relations",
    E_LAW_INFLUENCE[0]: "Conclave Influence",
    E_LAW_CORRUPT[0]: "Nearby corruption",
    E_LAW_TOZ_SEAT[0]: "Tower seat cost",
    E_LAW_WOM[0]: "Hashut spell cost",
    E_LAW_COOLDOWN[0]: "Hashut cooldown",
    E_LAW_MISCAST[0]: "Miscast",
    E_LAW_KDAAI[0]: "K'daai resistance",
    E_LAW_TEMPLE_TIME[0]: "Temple build time",
    E_LAW_HF_COST[0]: "Forge cap cost",
    E_LAW_HF_CAP[0]: "Forgecraft options",
    E_LAW_INF_COST[0]: "Infantry cost",
    E_LAW_INF_RANK[0]: "Infantry rank",
    E_LAW_ART_UPKEEP[0]: "Artillery upkeep",
    E_LAW_DWARF_XP[0]: "XP against Dwarfs",
    E_LAW_HOB_UPKEEP[0]: "Labour upkeep",
    E_LAW_ART_EXPL[0]: "Artillery explosive",
    E_LAW_ART_RANGE[0]: "Artillery range",
    E_LAW_RANGED_COST[0]: "Ranged cost",
```

"Chaos Dwarf relations" is 21 characters. If check 15's length test refuses it, it becomes "CHD relations"; that is a ruling for the ledger.

`EFFECT_PERCENT` entries, for the flat ones:

```python
    E_LAW_LAB_LD[0]: False, E_LAW_LAB_RANK[0]: False, E_LAW_CONVOYS[0]: False,
    E_LAW_OVR_RANK[0]: False, E_LAW_OVR_XP[0]: False, E_LAW_CHD_DIPLO[0]: False,
    E_LAW_CORRUPT[0]: False, E_LAW_TEMPLE_TIME[0]: False, E_LAW_HF_CAP[0]: False,
    E_LAW_INF_RANK[0]: False,
```

`effect_line` also substitutes CA's unsigned `%n`, which the K'daai text uses:

```python
def effect_line(effect, magnitude, intent):
    """One tooltip line: CA's wording with this row's signed value in it. CA
    writes %+n for a signed value and, on a few effects, %n for a bare one."""
    text = EFFECT_TEXT[effect[0]]
    v = signed_value(effect, magnitude, intent)
    return text.replace("%+n", "%+d" % v).replace("%n", "%d" % v)
```

The `LAWS` table after `GOVERNMENTS`. Each row is `(category, name, icon, [(option, name, blurb, effects)])`. Magnitudes and intents are derived from the spec's signed values and the "good" column: a positive value on a good-true effect is a BOON; on a good-false (cost) effect, a negative value is the BOON. The icon field is informational; the bundle reads the model's.

```python
# THE LAWS (spec 2026-10-02 laws section 2), in IC.LAW_ORDER's order and each
# category's IC.LAWS order. check_laws() holds the two together.
LAWS = [
    ("labour", "Labour", "chd_labour.png", [
        ("measure", "The Measure", "The overseers work the stock as they always have.", []),
        ("lash", "The Lash", "More are taken and they are driven hard, and they break.",
         [(E_LAW_CAPTIVES, 15, BOON), (E_LAW_RUSH, 30, BOON), (E_LAW_LAB_LD, 4, MALUS)]),
        ("kept", "The Kept Stock", "The stock is fed and kept, and fewer are taken.",
         [(E_LAW_LAB_UPKEEP, 50, BOON), (E_LAW_LAB_RANK, 2, BOON), (E_LAW_CAPTIVES, 10, MALUS)]),
        ("quota", "The Furnace Quota", "Every forge has its quota, and the stock pays for it.",
         [(E_WORKLOAD, 15, BOON), (E_LAW_RAW_USED, 15, BOON), (E_LAW_LAB_UPKEEP, 25, MALUS)]),
        ("ash", "The Ash Harvest", "What cannot be held is burned, and its people with it.",
         [(E_LAW_RAZE, 25, BOON), (E_LAW_SACK, 15, BOON), (E_LAW_CAPTIVES, 10, MALUS)]),
    ]),
    ("tribute", "Tribute", "edict_collect_tribute.png", [
        ("tithe", "The Crown's Tithe", "The Crown takes its tithe, as it always has.", []),
        ("roads", "Open Roads", "The roads are opened to more convoys, and the vassals pay less.",
         [(E_LAW_CONVOYS, 1, BOON), (E_LAW_AMBUSH, 25, BOON), (E_LAW_VASSAL, 20, MALUS)]),
        ("tariff", "The Ledger's Tariff", "Every route pays the Ledger, and the cargo is worth less.",
         [(E_LAW_TARIFF, 5, BOON), (E_LAW_REFINERY, 10, BOON), (E_LAW_CARGO_VALUE, 10, MALUS)]),
        ("mines", "The Mines Before All", "The mines come first, and the convoys carry less.",
         [(E_LAW_MINES, 15, BOON), (E_LAW_GOODS, 10, BOON), (E_LAW_CARGO_CAP, 15, MALUS)]),
        ("charter", "The Overseers' Charter", "The convoy overseers are chartered, and the other houses resent it.",
         [(E_LAW_OVR_RANK, 3, BOON), (E_LAW_OVR_XP, 100, BOON), (E_LAW_CHD_DIPLO, 10, MALUS)]),
    ]),
    ("worship", "Worship", "chd_conclave_influence.png", [
        ("rites", "The Rites Kept", "The rites are kept, as they always have been.", []),
        ("fires", "The Fires Fed", "Hashut's fires are fed without stint, and building waits on them.",
         [(E_LAW_INFLUENCE, 10, BOON), (E_LAW_CORRUPT, 1, BOON), (E_LAW_RUSH, 15, MALUS)]),
        ("seats", "Seats Bought in the Tower", "Seats in the Tower are sold, and the priests' favour cools.",
         [(E_LAW_TOZ_SEAT, 25, BOON), (E_LAW_INFLUENCE, 10, MALUS)]),
        ("lore", "The Lore Taught", "The Lore of Hashut is taught more widely, and more carelessly.",
         [(E_LAW_WOM, 10, BOON), (E_LAW_COOLDOWN, 10, BOON), (E_LAW_MISCAST, 15, MALUS)]),
        ("licence", "The Daemonsmiths' Licence", "The Daemonsmiths are licensed, and the priests resent it.",
         [(E_LAW_KDAAI, 10, BOON), (E_LAW_TEMPLE_TIME, 1, BOON), (E_LAW_INFLUENCE, 10, MALUS)]),
    ]),
    ("war", "War", "edict_levy_conscripts.png", [
        ("levy", "The Levy", "The levy is raised as it always has been.", []),
        ("hellforge", "The Hell-Forge Unbound", "The Hell-Forge works without leave, and the infantry pays for it.",
         [(E_LAW_HF_COST, 10, BOON), (E_LAW_HF_CAP, 1, BOON), (E_LAW_INF_COST, 10, MALUS)]),
        ("legions", "Standing Legions", "The legions stand ready, and the guns wait.",
         [(E_LAW_INF_RANK, 1, BOON), (E_LAW_INF_COST, 10, BOON), (E_LAW_ART_UPKEEP, 10, MALUS)]),
        ("grudge", "The Old Grudge", "The old grudge against the Dwarfs is fed, and the labour pays for it.",
         [(E_LAW_DWARF_XP, 100, BOON), (E_LAW_HOB_UPKEEP, 10, MALUS)]),
        ("gunnery", "The Gunnery Doctrine", "The guns come first, and every shooter costs more.",
         [(E_LAW_ART_EXPL, 10, BOON), (E_LAW_ART_RANGE, 5, BOON), (E_LAW_RANGED_COST, 15, MALUS)]),
    ]),
]


def model_law_icons():
    """{(category, option): bare effect_bundles picture} from IC.LAWS."""
    block = re.search(r"IC\.LAWS = \{(.*?)\n\}", _model_lua(), re.S)
    out = {}
    if not block:
        return out
    for cm in re.finditer(r"\n    (\w+) = \{icon = \"[^\"]+\",\s*\n\s*order = \{[^}]*\},\s*\n\s*opts = \{(.*?)\n    \}\}",
                          block.group(1), re.S):
        for om in re.finditer(r"(\w+)\s*=\s*\{icon = \"([^\"]+)\"", cm.group(2)):
            out[(cm.group(1), om.group(1))] = om.group(2)
    return out
```

In `build()`, after the government loop (after its `derpy_ic_doctrine_rule_` loc append):

```python
    # ONE PER LAW (spec 2026-10-02 laws), and the model puts one per category on
    # a player faction. The start options have no effects: a bundle so the
    # Faction Effects panel still names the law in force.
    law_icons = model_law_icons()
    for cat, cat_name, _icon, options in LAWS:
        loc.append({"key": "derpy_ic_law_cat_" + cat, "text": cat_name, "tooltip": "false"})
        for opt, name, blurb, effects in options:
            key = "derpy_ic_law_%s_%s" % (cat, opt)
            emit(key, name, blurb, "faction", effects, icon=law_icons.get((cat, opt)))
            loc.append({"key": "derpy_ic_law_name_%s_%s" % (cat, opt), "text": name,
                        "tooltip": "false"})
            for i, (e, m, intent) in enumerate(effects, start=1):
                loc.append({"key": "derpy_ic_law_fx%d_%s_%s" % (i, cat, opt),
                            "text": effect_line(e, m, intent), "tooltip": "false"})
```

`EVENTS`, after the `party_drawn` entry:

```python
    # THE LAWS (spec 2026-10-02 laws).
    ("law_proposed", True, "chd/faction", "Neutral",
     "A Law Before the Court",
     "A law has been put to the court. Its men will vote by their parties' lines, "
     "and you can push, win men or overrule on the Laws tab.",
     "The Court Will Vote"),
    ("law_passed", True, "chd/faction", "Positive",
     "A Law Passes",
     "The court has voted, and a new law is in force. Its parties are pleased, and "
     "those against it are not.",
     "The Law Is Changed"),
    ("law_failed", True, "chd/faction", "Negative",
     "A Law Fails",
     "The court has voted the law down. The law in force stands.",
     "The Law Stands"),
```

Before trusting the three-icon field, read the `party_drawn` entry: "Negative" must be a feed tone the generator accepts. If `check()` refuses it, use "Neutral", and ledger that as a ruling.

- [ ] **Step 4: Regenerate and run every gate.**

Run:
- `py tools/gen_iron_court.py` (writes the TSVs);
- `py tools/gen_iron_court.py --check`;
- `py tools/gen_iron_court.py --selftest`;
- the harness;
- `py tools/check_effect_signs.py`.

Expected:
- `--check` and `--selftest` print no findings.
- The loc count rises from 981 by 20 x 3 (bundle title, description, short) + 20 names + 4 categories + 57 effect lines + 3 x 3 event lines = 150.
- The harness event-alignment invariant passes with the 3 new events.
- `check_effect_signs` lists every MALUS row above among its rows. Read each against the spec's table and record "read: N rows, all intended" in the ledger.

- [ ] **Step 5: Ledger.**

---

### Task 7: The panel's new pieces: tab, board cells, vote cells, two new files

This task builds the components and their Lua mirrors with nothing drawn into them yet. Tasks 8 and 9 fill them. The registration list is long because the panel is held to its generator at every box width. Every item below is a place the agent's survey found that refuses an unregistered cell.

**Files:**
- Modify: `tools/gen_ic_ui.py`. Anchors:
  - `PANEL_LAYOUT`: `    "ic_tab_log": (1238, 62, 240, 32),` and `    "ic_mark_petitions": (994 + 240 - 34, 64, 28, 28),`;
  - `GUID_PREFIXES = {` (around line 82), `COMPACT_FILES = dict(` (127), `FILES = [` (3898) and `LAYOUT_TABLES = {` (3915);
  - after `def _card():` (3756), for the two builders;
  - `SCALED_SCALARS` (4024), `SCALED_BOX_TABLES` (4045), `SCALED_GRIDS` (4049) and `NOT_GEOMETRY` (4056);
  - the pie check's exemptions (around 5879-5930, `if name == "ic_zig_bg": continue`);
  - `BTN_CELLS` (3149);
  - `TEXT_STYLE` (3245);
  - `check_card_cells` calls (19z, 6578);
  - `_bar["ic_tab_petitions"] = ["Petitions"]` (20g2, 6912).
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua`. Anchors:
  - `ICUI.PANEL_XY` (316-326), whose existing lines must not be re-padded, because mutants match them;
  - `ICUI.CARD = "derpy_ic_card"` (18);
  - after the `ICUI.CARD_XY` loop (534-552);
  - `ICUI.layout()`'s `pool(ICUI.PLOT, ...)` line (1704-1753);
  - `ICUI.open` (7096-7107);
  - `ICUI.HAS_COMPACT` (7890);
  - `ICUI.SCALED` (7822), `ICUI.SCALED_TABLES` (7836) and `ICUI.NOT_SCALED` (7843-7863);
  - `ICUI.TAB_VIEW` (2006-2013);
  - `ICUI.scroll` (811);
  - `ICUI.MARKS` (1541);
  - the tab labels in refresh (`set_text(comp("ic_tab_petitions", panel), "Petitions")`, 6708);
  - the pool visibility block in refresh (6800-6817).
- Modify: `tools/import_iron_court.py`: `gen_tables` in `check_scaled` (445-455), and the literal-table tuple at 1296.
- Modify: `tools/_iron_court_harness.lua`:
  - `build_fake_panel` (5466-5540), for two new pools;
  - the layout want-list (4542-4694);
  - the compact-path checks (9613-9630 and 9666-9670);
  - the tab list check (5905-5916).
- Modify: `tools/sync_iron_court_repo.py:111`: add `"law"` and `"lawblock"` to the name tuple.

**Interfaces:**
- Produces, in the generator:
  - cells `ic_tab_laws` and `ic_mark_laws`;
  - the board cells `ic_law_head_<1-4>`, `ic_law_hicon_<1-4>`, `ic_law_htext_<1-4>`, `ic_law_pane`, `ic_law_p_icon`, `ic_law_p_name`, `ic_law_p_sub`, `ic_law_p_fxh`, `ic_law_p_fx<1-3>`, `ic_law_p_forh`, `ic_law_p_for`, `ic_law_p_conh`, `ic_law_p_con`, `ic_law_p_nowh`, `ic_law_p_now`, `ic_law_p_line<1-5>`, `ic_law_p_price` and `ic_law_p_btn`;
  - the vote cells `ic_lv_top`, `ic_lv_icon`, `ic_lv_name`, `ic_lv_fx`, `ic_lv_by`, `ic_lv_turns`, `ic_lv_back`, `ic_lv_aye`, `ic_lv_abs`, `ic_lv_nay`, `ic_lv_bar`, `ic_lv_seg_<1-12>`, `ic_lv_segc_<1-12>`, `ic_lv_side_<1-2>`, `ic_lv_sicon_<1-2>`, `ic_lv_shead_<1-2>`, `ic_lv_stag_<1-2>`, `ic_lv_screst_<1-2>`, `ic_lv_smore_<1-2>`, `ic_lv_abstain`, `ic_lv_hand`, `ic_lv_sideh`, `ic_lv_st_<1-3>`, `ic_lv_supph`, `ic_lv_lvl_<1-3>`, `ic_lv_overh` and `ic_lv_over_<1-2>`;
  - files `derpy_ic_law.twui.xml` (IC56, compact IC58) and `derpy_ic_lawblock.twui.xml` (IC57, compact IC59).
- Produces, in the panel Lua:
  - `ICUI.LAW`, `ICUI.PATH_LAW`, `ICUI.LAWBLOCK` and `ICUI.PATH_LAWBLOCK`;
  - `ICUI.LAW_W/H`, `ICUI.LAWS_X/Y`, `ICUI.LAW_GAP_X/Y`, `ICUI.LAW_CHILD_XY`, `ICUI.LAW_XY` (20 points, column-major: card `i` is category `ceil(i/5)`, option `(i-1)%5+1`), `ICUI.LAW_GLOW_INDEX = 2` and `ICUI.LAW_SEL_INDEX = 3`;
  - `ICUI.LB_W/H`, `ICUI.LB_X/Y`, `ICUI.LB_SIDE_DX`, `ICUI.LB_GAP`, `ICUI.LB_PER_SIDE = 4`, `ICUI.LB_MEN = 4`, `ICUI.LB_CHILD_XY` and `ICUI.LB_XY` (8 points: 1-4 the aye side, 5-8 the nay side);
  - `ICUI.LAW_SEGS = 12` and `ICUI.LAW_LINES = 5`;
  - `ICUI.LAW_BOARD_KEYS` and `ICUI.LAW_VOTE_KEYS` (sorted panel-cell names);
  - `ICUI.LAW_GLOW` and `ICUI.BTN_ART`;
  - view `laws`, and screen state `ICUI.law_cat` (nil means the board).

- [ ] **Step 1: Write the failing checks.** In the harness:
  - in the tab list check (5905), add `"ic_tab_laws"` to `tabs`;
  - in the layout want-list (4564), add `"ic_tab_laws",` beside `"ic_tab_petitions",`, plus the law cells:

```lua
        -- THE LAWS TAB (spec 2026-10-02 laws section 4).
        "ic_law_pane", "ic_law_p_icon", "ic_law_p_name", "ic_law_p_sub", "ic_law_p_fxh",
        "ic_law_p_fx1", "ic_law_p_fx2", "ic_law_p_fx3", "ic_law_p_forh", "ic_law_p_for",
        "ic_law_p_conh", "ic_law_p_con", "ic_law_p_nowh", "ic_law_p_now",
        "ic_law_p_line1", "ic_law_p_line2", "ic_law_p_line3", "ic_law_p_line4", "ic_law_p_line5",
        "ic_law_p_price", "ic_law_p_btn",
        "ic_lv_top", "ic_lv_icon", "ic_lv_name", "ic_lv_fx", "ic_lv_by", "ic_lv_turns", "ic_lv_back",
        "ic_lv_aye", "ic_lv_abs", "ic_lv_nay", "ic_lv_bar", "ic_lv_abstain", "ic_lv_hand",
        "ic_lv_sideh", "ic_lv_supph", "ic_lv_overh", "ic_lv_over_1", "ic_lv_over_2",
```

and after the list (where `want` is turned into a set), the looped names:

```lua
    for i = 1, 4 do
        want[#want + 1] = "ic_law_head_" .. i
        want[#want + 1] = "ic_law_hicon_" .. i
        want[#want + 1] = "ic_law_htext_" .. i
    end
    for i = 1, ICUI.LAW_SEGS do
        want[#want + 1] = "ic_lv_seg_" .. i
        want[#want + 1] = "ic_lv_segc_" .. i
    end
    for i = 1, 2 do
        for _, p in ipairs({"ic_lv_side_", "ic_lv_sicon_", "ic_lv_shead_", "ic_lv_stag_",
                            "ic_lv_screst_", "ic_lv_smore_"}) do want[#want + 1] = p .. i end
    end
    for i = 1, 3 do
        want[#want + 1] = "ic_lv_st_" .. i
        want[#want + 1] = "ic_lv_lvl_" .. i
    end
```

Read the want-list check first: if `want` is a set rather than an array, add with `want[name] = true` instead. Then add a new check after it:

```lua
check("laws: twenty law cards and eight party blocks, each with every cell", function()
    assert(#ICUI.LAW_XY == 20, #ICUI.LAW_XY .. " law cards")
    assert(#ICUI.LB_XY == 2 * ICUI.LB_PER_SIDE, #ICUI.LB_XY .. " blocks")
    local n = 0
    for _ in pairs(ICUI.LAW_CHILD_XY) do n = n + 1 end
    assert(n == 7, n .. " law card cells")
    n = 0
    for _ in pairs(ICUI.LB_CHILD_XY) do n = n + 1 end
    assert(n == 8 + 3 * ICUI.LB_MEN, n .. " block cells")
    local cat, opt = ICUI.law_at(7)
    assert(cat == "tribute" and opt == "roads", "card 7 is " .. tostring(cat) .. "." .. tostring(opt))
    assert(ICUI.MARKS.laws == "ic_mark_laws" and ICUI.TAB_VIEW.ic_tab_laws == "laws", "tab or marker")
end)
```

`ICUI.law_at` is defined in Task 8. This check stays red until then; record it as expected in the ledger and confirm it turns green in Task 8.

- [ ] **Step 2: Run the harness and the UI gate, and watch both fail.**

Run: the harness; `py tools/gen_ic_ui.py --check`.
Expected:
- the harness fails the tab list check and the layout want-list on unknown cells, plus the new check;
- the gate passes, because nothing is registered yet.

- [ ] **Step 3: The generator.** In `PANEL_LAYOUT`, after `"ic_tab_log"` and after `"ic_mark_petitions"` respectively:

```python
    "ic_tab_laws": (1482, 62, 240, 32),
```
```python
    "ic_mark_laws": (1482 + 240 - 34, 64, 28, 28),
```

After `PANEL_LAYOUT.update(help_layout())`:

```python
# THE LAWS TAB (spec 2026-10-02 laws section 4; the approved pictures are
# .skilltree_cache/ui_preview/ic_law_board.png and ic_law_vote.png). The board:
# four column heads over LAW_GRID's twenty cards, and the chosen law's pane.
LAW_W, LAW_H = 306, 150
LAWS_X, LAWS_Y = 18, 186
LAW_GAP_X, LAW_GAP_Y = 12, 8
LAW_COLS, LAW_ROWS = 4, 5
LAW_LAYOUT = {
    "ic_law_name": (20, 14, 242, 22),
    "ic_law_icon": (20, 44, 52, 52),
    "ic_law_fx1": (84, 46, 204, 18),
    "ic_law_fx2": (84, 66, 204, 18),
    "ic_law_fx3": (84, 86, 204, 18),
    "ic_law_foot": (20, 114, 266, 20),
    "ic_law_mark": (266, 10, 28, 28),
}


def law_grid():
    """Column-major, so card i is category ceil(i/5): ICUI.law_at reads it so."""
    return [(LAWS_X + c * (LAW_W + LAW_GAP_X), LAWS_Y + r * (LAW_H + LAW_GAP_Y))
            for c in range(LAW_COLS) for r in range(LAW_ROWS)]


LAW_GRID = law_grid()
for _i in range(LAW_COLS):
    _x = LAWS_X + _i * (LAW_W + LAW_GAP_X)
    PANEL_LAYOUT["ic_law_head_%d" % (_i + 1)] = (_x, 132, LAW_W, 46)
    PANEL_LAYOUT["ic_law_hicon_%d" % (_i + 1)] = (_x + 10, 137, 36, 36)
    PANEL_LAYOUT["ic_law_htext_%d" % (_i + 1)] = (_x + 54, 142, LAW_W - 64, 26)
_PX = LAWS_X + LAW_COLS * (LAW_W + LAW_GAP_X) + 6
_PW = 1902 - _PX
PANEL_LAYOUT.update({
    "ic_law_pane": (_PX, 132, _PW, 836),
    "ic_law_p_icon": (_PX + 24, 156, 88, 88),
    "ic_law_p_name": (_PX + 128, 160, _PW - 150, 30),
    "ic_law_p_sub": (_PX + 128, 198, _PW - 150, 26),
    "ic_law_p_fxh": (_PX + 24, 270, _PW - 48, 26),
    "ic_law_p_forh": (_PX + 24, 420, _PW - 48, 26),
    "ic_law_p_for": (_PX + 24, 454, _PW - 48, 26),
    "ic_law_p_conh": (_PX + 24, 514, _PW - 48, 26),
    "ic_law_p_con": (_PX + 24, 548, _PW - 48, 26),
    "ic_law_p_nowh": (_PX + 24, 612, _PW - 48, 26),
    "ic_law_p_now": (_PX + 24, 646, _PW - 48, 26),
    "ic_law_p_price": (_PX + 24, 852, _PW - 48, 26),
    "ic_law_p_btn": (_PX + (_PW - 240) // 2, 896, 240, 40),
})
for _i in range(3):
    PANEL_LAYOUT["ic_law_p_fx%d" % (_i + 1)] = (_PX + 24, 304 + 30 * _i, _PW - 48, 26)
LAW_LINES = 5
for _i in range(LAW_LINES):
    PANEL_LAYOUT["ic_law_p_line%d" % (_i + 1)] = (_PX + 24, 684 + 32 * _i, _PW - 48, 26)

# THE VOTE: the top plate, the support bar (twelve segments and their crests,
# placed at draw time), two sides of LB_GRID's party blocks, and the hand.
LAW_SEGS = 12
LB_W, LB_H = 880, 104
LB_X, LB_Y, LB_SIDE_DX, LB_GAP = 38, 396, 950, 4
LB_PER_SIDE, LB_MEN = 4, 4
LB_LAYOUT = {
    "ic_lb_crest": (0, 0, 52, 52),
    "ic_lb_name": (64, 2, 480, 22),
    "ic_lb_level": (64, 28, 480, 20),
    "ic_lb_more": (560, 28, 230, 20),
    "ic_lb_total": (800, 4, 80, 22),
}
for _i in range(3):
    LB_LAYOUT["ic_lb_pip_%d" % (_i + 1)] = (700 + 30 * _i, 8, 24, 14)
for _i in range(LB_MEN):
    LB_LAYOUT["ic_lb_face_%d" % (_i + 1)] = (64 + 200 * _i, 54, 70, 38)
    LB_LAYOUT["ic_lb_man_%d" % (_i + 1)] = (138 + 200 * _i, 54, 122, 18)
    LB_LAYOUT["ic_lb_win_%d" % (_i + 1)] = (138 + 200 * _i, 76, 122, 24)


def lb_grid():
    """Aye side first, then nay; ICUI.LB_XY reads it so."""
    return [(LB_X + s * LB_SIDE_DX, LB_Y + k * (LB_H + LB_GAP))
            for s in range(2) for k in range(LB_PER_SIDE)]


LB_GRID = lb_grid()
PANEL_LAYOUT.update({
    "ic_lv_top": (18, 132, 1884, 94),
    "ic_lv_icon": (36, 141, 76, 76),
    "ic_lv_name": (128, 144, 900, 30),
    "ic_lv_fx": (128, 182, 1000, 26),
    "ic_lv_by": (1180, 148, 500, 26),
    "ic_lv_turns": (1180, 182, 500, 26),
    "ic_lv_back": (1700, 160, 180, 38),
    "ic_lv_aye": (18, 236, 600, 26),
    "ic_lv_abs": (760, 236, 400, 26),
    "ic_lv_nay": (1302, 236, 600, 26),
    "ic_lv_bar": (18, 266, 1884, 34),
    "ic_lv_abstain": (18, 870, 1884, 26),
    "ic_lv_hand": (18, 906, 1884, 96),
    "ic_lv_sideh": (36, 916, 300, 26),
    "ic_lv_supph": (560, 916, 400, 26),
    "ic_lv_overh": (1440, 916, 440, 26),
    "ic_lv_over_1": (1440, 948, 216, 38),
    "ic_lv_over_2": (1664, 948, 216, 38),
})
for _i in range(LAW_SEGS):
    PANEL_LAYOUT["ic_lv_seg_%d" % (_i + 1)] = (18, 266, 34, 34)
    PANEL_LAYOUT["ic_lv_segc_%d" % (_i + 1)] = (18, 268, 30, 30)
for _i in range(2):
    _sx = 18 + 950 * _i
    PANEL_LAYOUT["ic_lv_side_%d" % (_i + 1)] = (_sx, 312, 934, 548)
    PANEL_LAYOUT["ic_lv_sicon_%d" % (_i + 1)] = (_sx + 20, 326, 52, 52)
    PANEL_LAYOUT["ic_lv_shead_%d" % (_i + 1)] = (_sx + 86, 332, 590, 30)
    PANEL_LAYOUT["ic_lv_stag_%d" % (_i + 1)] = (_sx + 682, 336, 180, 20)
    PANEL_LAYOUT["ic_lv_screst_%d" % (_i + 1)] = (_sx + 870, 324, 44, 44)
    PANEL_LAYOUT["ic_lv_smore_%d" % (_i + 1)] = (_sx + 20, 830, 880, 24)
for _i in range(3):
    PANEL_LAYOUT["ic_lv_st_%d" % (_i + 1)] = (36 + 158 * _i, 948, 150, 38)
    PANEL_LAYOUT["ic_lv_lvl_%d" % (_i + 1)] = (560 + 268 * _i, 948, 260, 38)
```

In `_panel()`'s per-name dispatch, build the new cells by kind, before its final text branch:

- **Plates, built like `ic_crown_box` (`layers=CARD_LAYERS`, not interactive):** `ic_law_head_N`, `ic_law_pane`, `ic_lv_top`, `ic_lv_side_N`, `ic_lv_hand`.
- **One-image cells (`layers=PORT_LAYERS`):** `ic_law_hicon_N`, `ic_law_p_icon`, `ic_lv_icon`, `ic_lv_sicon_N`, `ic_lv_segc_N`, `ic_lv_seg_N`.
- **Plate under a crest (`layers=FACE_LAYERS, colour_from=FACE_COLOUR_FROM`, as `ic_card_port`):** `ic_lv_screst_N`.
- **The bar base:** `ic_lv_bar`, a one-layer cell on `plate_path(None)`, the grey plate. It is drawn exactly like `ic_dial_rim`'s layer list, with that path.
- **Buttons, built exactly as `ic_gov_btn`:** `ic_law_p_btn`, `ic_lv_back`, `ic_lv_st_N`, `ic_lv_lvl_N`, `ic_lv_over_N`. Add every one to `BTN_CELLS`.
- **Everything else:** text, as `_panel()` builds `ic_leader_lbl`.

In `TEXT_STYLE`:
- give `ic_law_p_name`, `ic_lv_name` and `ic_lv_shead_N` the style key `ic_leader_name` uses;
- give `ic_law_htext_N`, `ic_law_p_fxh`, `ic_law_p_forh`, `ic_law_p_conh`, `ic_law_p_nowh`, `ic_lv_aye`, `ic_lv_abs`, `ic_lv_nay`, `ic_lv_sideh`, `ic_lv_supph` and `ic_lv_overh` the key `ic_leader_lbl` uses;
- the rest take `BODY` by default.

The two files' builders, after `_card()`:

```python
# THE LAW CARD (spec 2026-10-02 laws section 4.1): the card plate, then two
# swapped slots - LAW_GLOW_INDEX the chosen card's red row art, LAW_SEL_INDEX
# the gold frame on the law in force - each MASK_NONE until the Lua paints it,
# the trick PARTY_LAYERS plays with PARTY_SELECTED.
LAW_GLOW = GM_ROW_ART % "selected"
LAW_GLOW_INDEX = len(CARD_LAYERS)
LAW_SEL_INDEX = LAW_GLOW_INDEX + 1
LAW_LAYERS = CARD_LAYERS + [
    {"path": MASK_NONE, "offset": (0, 0), "dw": 0, "dh": 0, "margin": 0, "dock": None},
    {"path": MASK_NONE, "offset": (0, 0), "dw": 0, "dh": 0,
     "margin": TEXTURE_MIN_MARGIN[PARTY_SELECTED], "dock": None}]


def _law():
    root = EU.C("root", LAW_W, LAW_H)
    card = root.add(EU.C("derpy_ic_law", LAW_W, LAW_H, interactive=True, sound=OPENER_SOUND,
                         layers=LAW_LAYERS))
    for name in sorted(LAW_LAYOUT):
        _x, _y, w, h = LAW_LAYOUT[name]
        if name == "ic_law_icon":
            card.add(EU.C(name, w, h, layers=PORT_LAYERS))
        elif name == "ic_law_mark":
            card.add(EU.C(name, w, h, layers=MARK_LAYERS))
        else:
            card.add(EU.C(name, w, h, align="Left", valign="Center", tx=LABEL_TX, ty=LABEL_TY,
                          **style(name)))
    return root


# THE PARTY BLOCK (spec section 4.2): no plate of its own, it sits on its side.
def _lawblock():
    root = EU.C("root", LB_W, LB_H)
    block = root.add(EU.C("derpy_ic_lawblock", LB_W, LB_H))
    for name in sorted(LB_LAYOUT):
        _x, _y, w, h = LB_LAYOUT[name]
        if name == "ic_lb_crest" or name.startswith("ic_lb_face_"):
            block.add(EU.C(name, w, h, layers=FACE_LAYERS, colour_from=FACE_COLOUR_FROM))
        elif name.startswith("ic_lb_pip_"):
            block.add(EU.C(name, w, h, layers=PORT_LAYERS))
        elif name.startswith("ic_lb_win_"):
            block.add(EU.C(name, w, h, interactive=True, sound=OPENER_SOUND, layers=BTN_LAYERS,
                           hover=BTN_HOVER, align="Center", valign="Center", tx="0.00,0.00",
                           ty="0.00,0.00", leading=0, **style(name)))
        else:
            block.add(EU.C(name, w, h, align="Left", valign="Center", tx=LABEL_TX, ty=LABEL_TY,
                           **style(name)))
    return root
```

If `_party()`'s root uses different `interactive`/`sound` arguments for a whole-card click, copy `_party()`'s; it is the whole-card-click donor. Then register:

- `GUID_PREFIXES`:

  ```python
      "derpy_ic_law.twui.xml": "IC56", "derpy_ic_lawblock.twui.xml": "IC57",
      "derpy_ic_law_compact.twui.xml": "IC58", "derpy_ic_lawblock_compact.twui.xml": "IC59",
  ```

- `COMPACT_FILES`: add `"derpy_ic_law.twui.xml", "derpy_ic_lawblock.twui.xml"` to its tuple.
- `FILES`:

  ```python
      ("derpy_ic_law.twui.xml", _law, "The Iron Court - one law card"),
      ("derpy_ic_lawblock.twui.xml", _lawblock, "The Iron Court - one party on a vote"),
  ```

- `LAYOUT_TABLES`: add `"derpy_ic_law.twui.xml": LAW_LAYOUT, "derpy_ic_lawblock.twui.xml": LB_LAYOUT,`.
- `SCALED_SCALARS`: add `LAW_W, LAW_H, LAWS_X, LAWS_Y, LAW_GAP_X, LAW_GAP_Y, LB_W, LB_H, LB_X, LB_Y, LB_SIDE_DX, LB_GAP`. Read the list's syntax first; it may hold names as strings.
- `SCALED_BOX_TABLES`: add `"LAW_LAYOUT", "LB_LAYOUT"`.
- `SCALED_GRIDS`: add `"LAW_GRID", "LB_GRID"`.
- `NOT_GEOMETRY`: add `"LAW_COLS", "LAW_ROWS", "LAW_SEGS", "LAW_LINES", "LB_PER_SIDE", "LB_MEN", "LAW_LAYERS", "LAW_GLOW", "LAW_GLOW_INDEX", "LAW_SEL_INDEX", "_PX", "_PW", "_sx", "_x"`. Add whatever else `_classify` names; each one is a module-level number this step introduced.
- Pie check: next to `if name == "ic_zig_bg": continue`, add:

  ```python
            # THE LAWS TAB'S CELLS draw on the laws view only (spec 2026-10-02 laws).
            if name.startswith(("ic_law_", "ic_lv_")):
                continue
  ```

- 19z: add `check_card_cells(LAW_LAYOUT, LAW_W, LAW_H, "law card")` and `check_card_cells(LB_LAYOUT, LB_W, LB_H, "party block")`.
- 20g2: add `_bar["ic_tab_laws"] = ["Laws"]`.
- A check that the Lua's button art is the generator's, beside 21b:

  ```python
      # THE LIT BUTTON'S UNLIT ART (spec 2026-10-02 laws): ICUI.BTN_ART must be
      # what BTN_LAYERS draws in slot 0, or an unlit stance button repaints wrong.
      _ba = re.search(r'ICUI\.BTN_ART = "([^"]+)"', ui_lua)
      if not _ba or _ba.group(1) != BTN_LAYERS[0]["path"]:
          out.append("ICUI.BTN_ART is %s, not BTN_LAYERS slot 0 %s"
                     % (_ba.group(1) if _ba else None, BTN_LAYERS[0]["path"]))
  ```

  Use whatever name `check()` already gives the panel Lua's text in place of `ui_lua`.
- `check_scale_sweep`: add the two grids to its grids tuple and `frames`, as the card's are.

- [ ] **Step 4: The Lua mirrors.** In the UI file, after `ICUI.PATH_PLOT`'s line:

```lua
-- THE LAWS TAB (spec 2026-10-02 laws section 4): a law card and a party block,
-- each its own file and each instanced at open.
ICUI.LAW = "derpy_ic_law"
ICUI.PATH_LAW = "ui/campaign ui/derpy_ic_law"
ICUI.LAWBLOCK = "derpy_ic_lawblock"
ICUI.PATH_LAWBLOCK = "ui/campaign ui/derpy_ic_lawblock"
```

After the `ICUI.CARD_XY` loop:

```lua
-- THE LAW CARDS AND THE PARTY BLOCKS (gen_ic_ui LAW_* and LB_*).
ICUI.LAW_W, ICUI.LAW_H = 306, 150
ICUI.LAWS_X, ICUI.LAWS_Y = 18, 186
ICUI.LAW_GAP_X, ICUI.LAW_GAP_Y = 12, 8
ICUI.LAW_CHILD_XY = {
    ic_law_name = {20, 14, 242, 22},
    ic_law_icon = {20, 44, 52, 52},
    ic_law_fx1  = {84, 46, 204, 18},
    ic_law_fx2  = {84, 66, 204, 18},
    ic_law_fx3  = {84, 86, 204, 18},
    ic_law_foot = {20, 114, 266, 20},
    ic_law_mark = {266, 10, 28, 28},
}
ICUI.LAW_GLOW_INDEX, ICUI.LAW_SEL_INDEX = 2, 3
ICUI.LAW_XY = {}
for col = 0, 3 do
    for row = 0, 4 do
        ICUI.LAW_XY[#ICUI.LAW_XY + 1] = {ICUI.LAWS_X + col * (ICUI.LAW_W + ICUI.LAW_GAP_X),
                                         ICUI.LAWS_Y + row * (ICUI.LAW_H + ICUI.LAW_GAP_Y)}
    end
end
ICUI.LB_W, ICUI.LB_H = 880, 104
ICUI.LB_X, ICUI.LB_Y, ICUI.LB_SIDE_DX, ICUI.LB_GAP = 38, 396, 950, 4
ICUI.LB_PER_SIDE, ICUI.LB_MEN = 4, 4
ICUI.LB_CHILD_XY = {
    ic_lb_crest = {0, 0, 52, 52},
    ic_lb_name  = {64, 2, 480, 22},
    ic_lb_level = {64, 28, 480, 20},
    ic_lb_more  = {560, 28, 230, 20},
    ic_lb_total = {800, 4, 80, 22},
    ic_lb_pip_1 = {700, 8, 24, 14},
    ic_lb_pip_2 = {730, 8, 24, 14},
    ic_lb_pip_3 = {760, 8, 24, 14},
    ic_lb_face_1 = {64, 54, 70, 38},  ic_lb_man_1 = {138, 54, 122, 18},  ic_lb_win_1 = {138, 76, 122, 24},
    ic_lb_face_2 = {264, 54, 70, 38}, ic_lb_man_2 = {338, 54, 122, 18},  ic_lb_win_2 = {338, 76, 122, 24},
    ic_lb_face_3 = {464, 54, 70, 38}, ic_lb_man_3 = {538, 54, 122, 18},  ic_lb_win_3 = {538, 76, 122, 24},
    ic_lb_face_4 = {664, 54, 70, 38}, ic_lb_man_4 = {738, 54, 122, 18},  ic_lb_win_4 = {738, 76, 122, 24},
}
ICUI.LB_XY = {}
for side = 0, 1 do
    for k = 0, ICUI.LB_PER_SIDE - 1 do
        ICUI.LB_XY[#ICUI.LB_XY + 1] = {ICUI.LB_X + side * ICUI.LB_SIDE_DX,
                                       ICUI.LB_Y + k * (ICUI.LB_H + ICUI.LB_GAP)}
    end
end
ICUI.LAW_SEGS, ICUI.LAW_LINES = 12, 5
ICUI.LAW_GLOW = "<GM_ROW_ART % 'selected', the literal path>"
ICUI.BTN_ART = "<BTN_LAYERS[0]['path'], the literal path>"
```

Replace the two `<...>` placeholders with the literal paths. Print them first with `py -c "import sys; sys.path.insert(0,'tools'); import gen_ic_ui as G; print(G.GM_ROW_ART % 'selected', G.BTN_LAYERS[0]['path'])"`. The import check 8b parses the child tables as literals, so keep them literal.

Add to `ICUI.PANEL_XY`, as new lines only, every new panel cell with its 1920 box from Step 3. Write them out literally: 8b compares literals. To produce them without typing errors:

```bash
py -c "
import sys; sys.path.insert(0, 'tools'); import gen_ic_ui as G
for k in sorted(G.PANEL_LAYOUT):
    if k.startswith(('ic_law_', 'ic_lv_')) or k in ('ic_tab_laws', 'ic_mark_laws'):
        x, y, w, h = G.PANEL_LAYOUT[k]; print('    %s = {%d, %d, %d, %d},' % (k, x, y, w, h))
"
```

The board and vote key lists, after `ICUI.PANEL_XY`:

```lua
-- THE LAWS TAB'S STATIC CELLS, by prefix: the board's on the board, the vote's
-- on the vote, nothing of either on any other view.
ICUI.LAW_BOARD_KEYS, ICUI.LAW_VOTE_KEYS = {}, {}
for name in pairs(ICUI.PANEL_XY) do
    if string.sub(name, 1, 7) == "ic_law_" then
        ICUI.LAW_BOARD_KEYS[#ICUI.LAW_BOARD_KEYS + 1] = name
    elseif string.sub(name, 1, 6) == "ic_lv_" then
        ICUI.LAW_VOTE_KEYS[#ICUI.LAW_VOTE_KEYS + 1] = name
    end
end
table.sort(ICUI.LAW_BOARD_KEYS)
table.sort(ICUI.LAW_VOTE_KEYS)
```

Then the rest of the registration:

- `ICUI.TAB_VIEW`: add `    ic_tab_laws      = "laws",`.
- `ICUI.scroll`: add `laws = 0,` after `petitions = 0,`.
- `ICUI.MARKS`: add `laws = "ic_mark_laws"`.
- The tab labels: add `set_text(comp("ic_tab_laws", panel), "Laws")` after the Petitions one.
- `ICUI.open`: after the plot pool loop:

  ```lua
      for i = 1, #ICUI.LAW_XY do
          panel:CreateComponent(ICUI.LAW .. "_" .. i, ICUI.path(ICUI.PATH_LAW))
      end
      for i = 1, #ICUI.LB_XY do
          panel:CreateComponent(ICUI.LAWBLOCK .. "_" .. i, ICUI.path(ICUI.PATH_LAWBLOCK))
      end
  ```

- `ICUI.layout()`: after `pool(ICUI.PLOT, ...)`:

  ```lua
      pool(ICUI.LAW, ICUI.LAW_XY, ICUI.LAW_W, ICUI.LAW_H, ICUI.LAW_CHILD_XY)
      pool(ICUI.LAWBLOCK, ICUI.LB_XY, ICUI.LB_W, ICUI.LB_H, ICUI.LB_CHILD_XY)
  ```

- `ICUI.HAS_COMPACT`: add `[ICUI.PATH_LAW] = true, [ICUI.PATH_LAWBLOCK] = true,`.
- `ICUI.SCALED`: add `"LAW_W", "LAW_H", "LAWS_X", "LAWS_Y", "LAW_GAP_X", "LAW_GAP_Y", "LB_W", "LB_H", "LB_X", "LB_Y", "LB_SIDE_DX", "LB_GAP"`.
- `ICUI.SCALED_TABLES`: add `"LAW_CHILD_XY", "LB_CHILD_XY", "LAW_XY", "LB_XY"`.
- `ICUI.NOT_SCALED`: add `"LAW_GLOW_INDEX", "LAW_SEL_INDEX", "LB_PER_SIDE", "LB_MEN", "LAW_SEGS", "LAW_LINES"`.
- Visibility, in refresh's pool block after the plot lines:

  ```lua
      -- THE LAWS TAB (spec 2026-10-02 laws section 4): the board, or a vote.
      local laws_view = view == "laws"
      local on_vote = laws_view and ICUI.law_screen(faction) == "vote"
      for i = 1, #ICUI.LAW_XY do
          show(comp(ICUI.LAW .. "_" .. i, panel), laws_view and not on_vote)
      end
      for _, name in ipairs(ICUI.LAW_BOARD_KEYS) do show(comp(name, panel), laws_view and not on_vote) end
      for i = 1, #ICUI.LB_XY do show(comp(ICUI.LAWBLOCK .. "_" .. i, panel), false) end
      for _, name in ipairs(ICUI.LAW_VOTE_KEYS) do show(comp(name, panel), on_vote) end
  ```

  The blocks start hidden; Task 9's draw shows the ones it fills. Read refresh's own locals first: if the faction key is named differently there, use that name. `ICUI.law_screen` is defined in Task 8. Until then, stub it at the top of the laws section as `function ICUI.law_screen() return "board" end`; Task 8 replaces it.

In `import_iron_court.py`'s `gen_tables` (445-455), add:

```python
        "LAW_CHILD_XY": g.LAW_LAYOUT, "LB_CHILD_XY": g.LB_LAYOUT,
        "LAW_XY": {str(i + 1): p for i, p in enumerate(g.LAW_GRID)},
        "LB_XY": {str(i + 1): p for i, p in enumerate(g.LB_GRID)},
```

and add `"LAW_CHILD_XY", "LB_CHILD_XY"` to the literal-table tuple at 1296, with each one's generator table, following the tuple's own shape.

In the harness `build_fake_panel`, after the plot pool:

```lua
    for i = 1, #ICUI.LAW_XY do
        local card = child(panel, ICUI.LAW .. "_" .. i)
        for name, xy in pairs(ICUI.LAW_CHILD_XY) do child(card, name).w = xy[3] end
    end
    for i = 1, #ICUI.LB_XY do
        local block = child(panel, ICUI.LAWBLOCK .. "_" .. i)
        for name, xy in pairs(ICUI.LB_CHILD_XY) do child(block, name).w = xy[3] end
    end
```

In the compact-path checks, add `ICUI.PATH_LAW` and `ICUI.PATH_LAWBLOCK` to the path list, and `{ICUI.LAW .. "_1", ICUI.PATH_LAW}` and `{ICUI.LAWBLOCK .. "_1", ICUI.PATH_LAWBLOCK}` to the pairs.

- [ ] **Step 5: Regenerate and run every gate.**

Run:
- `py tools/gen_ic_ui.py` (writes the twui);
- `py tools/gen_ic_ui.py --check`;
- `py tools/import_iron_court.py`;
- `luac -p` on the UI file;
- the harness;
- `py tools/check_lua_literal_left.py`;
- `py tools/gen_ic_ui.py --selftest` in the background (about 10 minutes); read its tail before Step 6.

Expected:
- `--check` prints no findings;
- the import gate prints `verify ok`;
- the harness is green except the new block check, which waits on `ICUI.law_at`. Ledger it.
- `--selftest` passes, including `selftest_compact` on the two new files.

Every refusal names one more registration point; each is a ruling only if it changes a value, not if it adds a name to a list.

- [ ] **Step 6: Ledger.**

---

### Task 8: The law board

**Files:**
- Modify: the UI file:
  - a laws section after `ICUI.gov_fx` (around 3983);
  - the refresh dispatcher (6921-6926, `elseif view == "petitions" then`);
  - `ICUI.register`'s click branches (7577-7633);
  - `ICUI.attention` (1402-1415) and `ICUI.court_state` (1387-1391);
  - `ICUI.reason_text` (5931);
  - `ICUI.ANSWERS` (after 7429);
  - `ICUI.answer_text` (7370);
  - `ICUI.answer_party` (7357);
  - `ICUI.SOUNDS` (2833);
  - `ICUI.intrigue_text` (4768, after the `drawn` branch);
  - `ICUI.HELP` (5314, a twelfth topic after "Governments").
- Test: the harness.

**Interfaces:**
- Consumes: the model's `IC.law_*` and Task 7's components.
- Produces:
  - `ICUI.law_at(i) -> category, option`;
  - `ICUI.law_name(category, option)`, `ICUI.law_cat_name(category)`, `ICUI.law_icon(category, option)`, `ICUI.law_title("category.option")`, `ICUI.law_short(category, option) -> {lines}`;
  - `ICUI.law_screen(faction) -> "board"|"vote"`, which clears a stale `ICUI.law_cat`;
  - `ICUI.law_sel = {category, option}`, `ICUI.law_btn`;
  - `ICUI.draw_laws`, `ICUI.draw_law_board`, `ICUI.draw_law_pane`;
  - `ICUI.law_parties`, `ICUI.law_party_lines`, `ICUI.law_refusal`;
  - clicks `derpy_ic_law_N` and `ic_law_p_btn`.

- [ ] **Step 1: Write the failing checks.**

```lua
check("laws: the board shows each law's card, the law in force framed and the chosen one lit", function()
    local court = law_court({{"crown", 1000}, {"legion", 80}})
    court.laws.war = "gunnery"
    with_fake_panel(function(panel)
        ICUI.view, ICUI.law_cat, ICUI.law_sel = "laws", nil, {"labour", "lash"}
        ICUI.refresh()
        local gun = panel.children[ICUI.LAW .. "_20"]
        local levy = panel.children[ICUI.LAW .. "_16"]
        local lash = panel.children[ICUI.LAW .. "_2"]
        assert(gun.images[ICUI.LAW_SEL_INDEX] == ICUI.PARTY_SELECTED, "the law in force is not framed")
        assert(levy.images[ICUI.LAW_SEL_INDEX] == ICUI.MASK_NONE, "the old law is still framed")
        assert(lash.images[ICUI.LAW_GLOW_INDEX] == ICUI.LAW_GLOW, "the chosen card is not lit")
        assert(gun.children.ic_law_foot.text == "In force", "foot " .. tostring(gun.children.ic_law_foot.text))
        assert(levy.children.ic_law_foot.text == "The old way", "the start option's foot")
        assert(string.find(lash.children.ic_law_foot.text, ICUI.crest("chain"), 1, true),
            "the Lash's foot shows no Chain crest")
        assert(panel.children.ic_law_p_name.text == ICUI.law_name("labour", "lash"), "the pane names the wrong law")
        assert(panel.children.ic_law_p_btn.text == "Propose", "the pane's button: " .. tostring(panel.children.ic_law_p_btn.text))
        assert(panel.children.ic_lv_top.visible == false and panel.children[ICUI.LAW .. "_1"].visible,
            "the board did not show, or the vote did")
    end)
    gov_done()
end)

check("laws: the pane's projection is the model's, and its party lines name each party's vote", function()
    local court = law_court({{"crown", 300}, {"legion", 100}, {"ledger", 100}})
    with_fake_panel(function(panel)
        ICUI.view, ICUI.law_cat, ICUI.law_sel = "laws", nil, {"labour", "ash"}
        ICUI.refresh()
        local p = IC.law_project(F, "labour", "ash")
        local all = p.aye + p.nay + p.abstain
        local want = string.format("Aye %d%%", ICUI.pct(p.aye, all))
        assert(string.find(panel.children.ic_law_p_now.text, want, 1, true), panel.children.ic_law_p_now.text)
        local seen = false
        for k = 1, ICUI.LAW_LINES do
            local t = panel.children["ic_law_p_line" .. k].text or ""
            if string.find(t, ICUI.house_name("ledger", F) .. ": nay", 1, true) then seen = true end
        end
        assert(seen, "no pane line says the Ledger votes nay")
    end)
    gov_done()
end)

check("laws: clicking a card chooses it, and Propose sends the law and opens its vote", function()
    local court = law_court({{"crown", 1000}})
    ICUI.register()
    local click = core.listeners["ic_click"]
    with_fake_panel(function(panel)
        ICUI.view, ICUI.law_cat, ICUI.law_sel = "laws", nil, nil
        ICUI.refresh()
        click({string = ICUI.LAW .. "_9", component = panel.children[ICUI.LAW .. "_9"]})
        assert(ICUI.law_sel[1] == "tribute" and ICUI.law_sel[2] == "mines", "card 9 chose "
            .. tostring(ICUI.law_sel[1]) .. "." .. tostring(ICUI.law_sel[2]))
        click({string = "ic_law_p_btn", component = panel.children.ic_law_p_btn})
        assert(court.votes.tribute and court.votes.tribute.option == "mines", "Propose did not open the vote")
        assert(ICUI.law_cat == "tribute", "the vote screen did not open")
    end)
    gov_done()
end)

check("laws: the marker lights while a party's proposal waits for your answer, and only then", function()
    local court = law_court({{"crown", 1000}})
    local a = ICUI.attention(F)
    assert(not a.laws, "the marker lit with no vote")
    law_vote(court, "ash", "abstain", "legion")
    a = ICUI.attention(F)
    assert(a.laws and a.any, "a waiting party proposal did not light the marker")
    IC.law_set_stance(F, "labour", "abstain")
    assert(not ICUI.attention(F).laws, "an answered proposal still lights the marker")
    court.votes.labour = nil
    IC.law_propose(F, "labour", "ash")
    assert(not ICUI.attention(F).laws, "the player's own proposal lights the marker")
    gov_done()
end)

check("laws: the Record says what each law move did", function()
    local cases = {
        {kind = "law_propose", slug = "legion", key = "labour.ash", want = "put"},
        {kind = "law_propose", slug = "crown", key = "labour.ash", want = "You put"},
        {kind = "law_pass", slug = "legion", key = "labour.ash", want = "passed"},
        {kind = "law_fail", slug = "legion", key = "labour.ash", want = "voted down"},
        {kind = "law_win", slug = "ledger", key = "labour.ash", n = 60, want = "60 influence"},
        {kind = "law_push", slug = "crown", key = "labour.ash", n = 2, want = "strongly"},
        {kind = "law_push", slug = "legion", key = "labour.ash", n = 3, want = "fully"},
        {kind = "law_overrule", slug = "crown", key = "labour.ash", n = 1, want = "overruled"},
    }
    for _, c in ipairs(cases) do
        local s = ICUI.intrigue_text({kind = c.kind, slug = c.slug, key = c.key, n = c.n or 0, turn = 1})
        assert(s and string.find(s, c.want, 1, true), c.kind .. ": " .. tostring(s))
        assert(string.find(s, ICUI.law_title(c.key), 1, true), c.kind .. " does not name the law: " .. s)
    end
end)
```

`string.find(s, p, 1, true)` is allowed here: the harness runs on stock `lua.exe`, and the ban covers shipped Lua only. Before using it, check that the harness already does this, as the deeds checks do.

- [ ] **Step 2: Run the harness and watch the five new checks fail.**

Expected: 5 `FAIL laws:` lines. The board shows nothing and `ICUI.pct` is nil.

- [ ] **Step 3: Implement.** The laws section, after `ICUI.gov_fx`:

```lua
-- THE LAWS TAB (spec 2026-10-02 laws section 4). The board, or the vote on
-- ICUI.law_cat. Loc read at draw time only, never from a turn handler.
ICUI.law_sel = nil
ICUI.law_cat = nil
ICUI.law_btn = nil
ICUI.LAW_LEVEL = {"slightly favours", "strongly favours", "fully pushes"}
ICUI.LAW_LEVEL_BTN = {"Slightly favour", "Strongly favour", "Fully push"}
ICUI.LAW_STANCES = {"aye", "nay", "abstain"}
ICUI.LAW_STANCE_BTN = {"Support", "Oppose", "Abstain"}
ICUI.LAW_WHY = {crown = "your own men", ["for"] = "it is for this law",
                against = "it is against this law", loyal = "loyal to you",
                disloyal = "disloyal", torn = "undecided", no_stance = "you abstain",
                won = "won by you"}
ICUI.PIP_ON = ICUI.TAB_PLATE[0].on
ICUI.PIP_OFF = "ui/derpy_ic/house_plate_none.png"

function ICUI.law_at(i)
    local cat = IC.LAW_ORDER[math.floor((i - 1) / 5) + 1]
    return cat, cat and IC.LAWS[cat].order[(i - 1) % 5 + 1] or nil
end

function ICUI.law_name(category, option)
    return loc("derpy_ic_law_name_" .. tostring(category) .. "_" .. tostring(option), tostring(option))
end

function ICUI.law_cat_name(category)
    return loc("derpy_ic_law_cat_" .. tostring(category), tostring(category))
end

function ICUI.law_icon(category, option)
    local o = IC.law_opt(category, option)
    return "ui/campaign ui/effect_bundles/" .. (o and o.icon or IC.LAWS[category].icon)
end

function ICUI.law_title(key)
    local cat, opt = string.match(tostring(key), "^(%w+)%.(%w+)$")
    if not cat or not IC.law_opt(cat, opt) then return tostring(key) end
    return ICUI.law_name(cat, opt)
end

function ICUI.law_short(category, option)
    local out = {}
    local text = loc("derpy_ic_effects_" .. IC.law_bundle(category, option), "")
    for piece in string.gmatch(text, "([^,]+)") do
        out[#out + 1] = (string.gsub(piece, "^%s+", ""))
    end
    return out
end

function ICUI.pct(n, all)
    if not all or all <= 0 then return 0 end
    return math.floor(n * 100 / all + 0.5)
end

-- THE SCREEN, and a vote that has ended since the screen opened goes back to
-- the board.
function ICUI.law_screen(faction)
    if ICUI.law_cat and not IC.law_vote_of(faction, ICUI.law_cat) then ICUI.law_cat = nil end
    return ICUI.law_cat and "vote" or "board"
end

function ICUI.law_default(faction)
    for _, cat in ipairs(IC.LAW_ORDER) do
        if not IC.law_vote_of(faction, cat) then
            for _, opt in ipairs(IC.LAWS[cat].order) do
                if opt ~= IC.law_in_force(faction, cat) then return {cat, opt} end
            end
        end
    end
    return {IC.LAW_ORDER[1], IC.LAWS[IC.LAW_ORDER[1]].order[1]}
end

function ICUI.law_refusal(why, n)
    if why == "law_purse" then return "Short " .. tostring(n or 0) end
    if why == "law_same" then return "In force" end
    if why == "law_open" then return "Vote open" end
    if why == "law_abstain" then return "Take a side" end
    return "No"
end

function ICUI.law_foot(faction, cat, opt, vote)
    if IC.law_in_force(faction, cat) == opt then return "In force" end
    if vote and vote.option == opt then
        local left = math.max(0, vote.ends - cm:model():turn_number())
        return string.format("Vote open: %d turn%s", left, left == 1 and "" or "s")
    end
    local o = IC.law_opt(cat, opt)
    if not o.pro then return "The old way" end
    return string.format("For [[img:%s]][[/img]]   Against [[img:%s]][[/img]]", ICUI.crest(o.pro[1]), ICUI.crest(o.con[1]))
end

function ICUI.law_parties(faction, slugs)
    local out = {}
    for _, slug in ipairs(slugs or {}) do
        local name = ICUI.house_name(slug, faction)
        if not IC.court(faction).houses[slug] then name = name .. " - not in your court" end
        out[#out + 1] = string.format("[[img:%s]][[/img]]%s", ICUI.crest(slug), name)
    end
    return #out > 0 and table.concat(out, "   ") or "Nobody"
end

function ICUI.law_party_lines(faction, cat, vote)
    local out = {}
    for _, slug in ipairs(IC.present_houses(faction)) do
        local side, why = IC.law_line(faction, vote, cat, slug)
        out[#out + 1] = string.format("[[img:%s]][[/img]]%s: %s - %s", ICUI.crest(slug), ICUI.house_name(slug, faction), side or "abstains", ICUI.LAW_WHY[why] or tostring(why))
    end
    if #out > ICUI.LAW_LINES then
        local extra = #out - ICUI.LAW_LINES + 1
        for k = #out, ICUI.LAW_LINES, -1 do out[k] = nil end
        out[ICUI.LAW_LINES] = string.format("and %d more parties", extra)
    end
    return out
end

function ICUI.draw_law_pane(panel, faction, cat, opt)
    ICUI.set_crest(panel, "ic_law_p_icon", ICUI.law_icon(cat, opt))
    set_text(comp("ic_law_p_name", panel), ICUI.law_name(cat, opt))
    set_text(comp("ic_law_p_sub", panel), string.format("%s law. In force: %s.",
        ICUI.law_cat_name(cat), ICUI.law_name(cat, IC.law_in_force(faction, cat))))
    set_text(comp("ic_law_p_fxh", panel), "Effects")
    for k = 1, 3 do
        local line = loc(string.format("derpy_ic_law_fx%d_%s_%s", k, cat, opt), "")
        if k == 1 and line == "" then line = "None. This is the old way." end
        set_text(comp("ic_law_p_fx" .. k, panel), line)
    end
    local o = IC.law_opt(cat, opt)
    set_text(comp("ic_law_p_forh", panel), "Favoured by")
    set_text(comp("ic_law_p_for", panel), ICUI.law_parties(faction, o.pro))
    set_text(comp("ic_law_p_conh", panel), "Opposed by")
    set_text(comp("ic_law_p_con", panel), ICUI.law_parties(faction, o.con))
    local p = IC.law_project(faction, cat, opt)
    local all = p.aye + p.nay + p.abstain
    set_text(comp("ic_law_p_nowh", panel), "If it went to the court now")
    set_text(comp("ic_law_p_now", panel), all > 0
        and string.format("Aye %d%%  -  Nay %d%%  -  %d%% would abstain",
            ICUI.pct(p.aye, all), ICUI.pct(p.nay, all), ICUI.pct(p.abstain, all))
        or "Nobody at court has influence to vote.")
    local lines = ICUI.law_party_lines(faction, cat, {option = opt, stance = "aye", won = {}, push = {}})
    for k = 1, ICUI.LAW_LINES do set_text(comp("ic_law_p_line" .. k, panel), lines[k] or "") end
    local btn = comp("ic_law_p_btn", panel)
    local vote = IC.law_vote_of(faction, cat)
    if vote then
        set_text(comp("ic_law_p_price", panel), string.format("A %s vote is open: %s.",
            ICUI.law_cat_name(cat), ICUI.law_name(cat, vote.option)))
        set_text(btn, "Go to the vote")
        ICUI.law_btn = {kind = "vote", category = cat}
    else
        local ok, why, n = IC.law_can_propose(faction, cat, opt)
        set_text(comp("ic_law_p_price", panel), string.format("Proposing costs [[img:%s]][[/img]]%d influence from your own party's men.", ICUI.COST_ICON, IC.TUNE.law_propose_cost))
        set_text(btn, ok and "Propose" or ICUI.red(ICUI.law_refusal(why, n)))
        ICUI.law_btn = ok and {kind = "propose", category = cat, option = opt} or nil
    end
end

function ICUI.draw_law_board(panel, faction)
    local sel = ICUI.law_sel
    if not sel or not IC.law_opt(sel[1], sel[2]) then sel = ICUI.law_default(faction) end
    ICUI.law_sel = sel
    for i, cat in ipairs(IC.LAW_ORDER) do
        ICUI.set_crest(panel, "ic_law_hicon_" .. i, "ui/campaign ui/effect_bundles/" .. IC.LAWS[cat].icon)
        set_text(comp("ic_law_htext_" .. i, panel), ICUI.law_cat_name(cat))
    end
    for i = 1, #ICUI.LAW_XY do
        local card = comp(ICUI.LAW .. "_" .. i, panel)
        local cat, opt = ICUI.law_at(i)
        if card and cat then
            local vote = IC.law_vote_of(faction, cat)
            set_text(comp("ic_law_name", card), ICUI.law_name(cat, opt))
            ICUI.set_crest(card, "ic_law_icon", ICUI.law_icon(cat, opt))
            local fx = ICUI.law_short(cat, opt)
            if #fx == 0 then fx = {"No effects"} end
            for k = 1, 3 do set_text(comp("ic_law_fx" .. k, card), fx[k] or "") end
            set_text(comp("ic_law_foot", card), ICUI.law_foot(faction, cat, opt, vote))
            show(comp("ic_law_mark", card), vote ~= nil and vote.option == opt)
            local chosen = sel[1] == cat and sel[2] == opt
            local force = IC.law_in_force(faction, cat) == opt
            pcall(function()
                card:SetImagePath(chosen and ICUI.LAW_GLOW or ICUI.MASK_NONE, ICUI.LAW_GLOW_INDEX)
                card:SetImagePath(force and ICUI.PARTY_SELECTED or ICUI.MASK_NONE, ICUI.LAW_SEL_INDEX)
            end)
        end
    end
    ICUI.draw_law_pane(panel, faction, sel[1], sel[2])
    return ""
end

function ICUI.draw_laws(panel, faction)
    if ICUI.law_screen(faction) == "vote" then
        return ICUI.draw_law_vote(panel, faction, ICUI.law_cat)
    end
    return ICUI.draw_law_board(panel, faction)
end
```

Until Task 9, `ICUI.draw_law_vote` is the stub `function ICUI.draw_law_vote() return "" end`. Delete the Task 7 `ICUI.law_screen` stub. `ICUI.TAB_PLATE` and `ICUI.COST_ICON` are defined before this section; if `TAB_PLATE` sits later in the file, move `PIP_ON` into the vote draw. Every `[[img:%s]]` line names `ICUI.crest(` or `ICUI.COST_ICON` on the same line, which the gate's `_via` rule needs. If the gate refuses `ICUI.COST_ICON` as an indirection, add it to `_via` in `gen_ic_ui.py`.

The dispatcher, after the petitions branch:

```lua
        elseif view == "laws" then
            warn = ICUI.draw_laws(panel, faction)
```

The tab click (`ICUI.TAB_VIEW[id]` branch) also resets the screen: add `ICUI.law_cat = nil` beside `ICUI.notice = nil`.

The clicks, in `ICUI.register` before the `ic_row_e` branch:

```lua
        elseif string.match(id, "^" .. ICUI.LAW .. "_%d+$") and comp(ICUI.PANEL) then
            local cat, opt = ICUI.law_at(tonumber(string.match(id, "_(%d+)$")) or 0)
            if cat then
                ICUI.law_sel, ICUI.notice = {cat, opt}, nil
                ICUI.refresh()
            end
        elseif id == "ic_law_p_btn" and comp(ICUI.PANEL) then
            local b = ICUI.law_btn
            if b and b.kind == "vote" then
                ICUI.law_cat = b.category
            elseif b then
                ICUI.send(ICUI.player(), "law_propose", b.category .. "|" .. b.option)
            end
            ICUI.refresh()
```

The answers. In `ICUI.answer_party`, first line:

```lua
    if string.sub(op or "", 1, 4) == "law_" then return nil, {} end
```

In `ICUI.answer_text`, before its final `return nil`:

```lua
    elseif op == "law_propose" then
        return "Proposed. The court will vote on it."
    elseif op == "law_stance" then
        return "Your side is chosen."
    elseif op == "law_win" then
        return "Won over. He votes with you on this law."
    elseif op == "law_push" then
        return "Your party pushes harder."
    elseif op == "law_overrule" then
        return "Overruled. The court has its answer, and the losing parties resent it."
```

After `ICUI.ANSWERS.gov_hold = ...`:

```lua
-- THE LAWS (spec 2026-10-02 laws). A proposal opens its vote screen.
local law_proposed = confirmed(true, false, "law_propose")
ICUI.ANSWERS.law_propose = function(arg, done, why, spare)
    law_proposed(arg, done, why, spare)
    if done then ICUI.law_cat = string.match(arg or "", "^(%w+)|") end
end
ICUI.ANSWERS.law_stance = confirmed(true, false, "law_stance")
ICUI.ANSWERS.law_win = confirmed(true, false, "law_win")
ICUI.ANSWERS.law_push = confirmed(true, false, "law_push")
ICUI.ANSWERS.law_overrule = confirmed(true, false, "law_overrule")
```

In `ICUI.SOUNDS`, add `law_propose`, `law_stance`, `law_win`, `law_push` and `law_overrule`, each with the value `gov_hold` has there. The generator's sound-name check reads this table.

In `ICUI.reason_text`, before its fallback:

```lua
    elseif why == "laws_off" then
        return "Laws are switched off in the settings."
    elseif why == "law_open" then
        return "A vote on this kind of law is already open."
    elseif why == "law_same" then
        return "That law is already in force."
    elseif why == "law_purse" then
        return string.format("Your own party's men are %d influence short of that.", spare or 0)
    elseif why == "law_none" then
        return "That vote is over."
    elseif why == "law_abstain" then
        return "Take a side first. The Crown cannot push or buy votes while it abstains."
    elseif why == "law_no_man" then
        return "He no longer has a vote."
    elseif why == "law_crown_man" then
        return "He is your own man and already votes with you."
    elseif why == "law_won" then
        return "He is already won over."
    elseif why == "law_with_you" then
        return "He already votes with you."
    elseif why == "law_pushed" then
        return "You already push that hard."
```

The marker. In `ICUI.court_state`, beside `s.petitions = ...`:

```lua
    -- A PARTY'S LAW THE PLAYER HAS NOT ANSWERED (spec 2026-10-02 laws 3.2).
    s.laws = 0
    for _, cat in ipairs(IC.LAW_ORDER) do
        local v = IC.law_vote_of(faction, cat)
        if v and v.proposer ~= IC.CROWN and not v.answered then s.laws = s.laws + 1 end
    end
```

Use whatever `court_state` names the faction key. In `ICUI.attention`'s `out`, add `laws = s.laws > 0,`. Extend `out.any` with `or out.laws`. Two mutants anchor on the `out.any` line verbatim: re-aim them in Task 10. In `ICUI.opener_tip`'s waiting lines, add one for `s.laws > 0`, in the wording the others use: "A law from a party waits for your answer."

The Record, after the `drawn` branch of `ICUI.intrigue_text`:

```lua
    elseif e.kind == "law_propose" then
        if e.slug == IC.CROWN then
            return string.format("You put %s to the court.", ICUI.law_title(e.key))
        end
        return string.format("%s put %s to the court.", house, ICUI.law_title(e.key))
    elseif e.kind == "law_pass" then
        return string.format("The court passed %s.", ICUI.law_title(e.key))
    elseif e.kind == "law_fail" then
        return string.format("The court voted down %s.", ICUI.law_title(e.key))
    elseif e.kind == "law_win" then
        return string.format("You won a man of %s over on %s, for %d influence.",
            house, ICUI.law_title(e.key), e.n or 0)
    elseif e.kind == "law_push" then
        local level = ICUI.LAW_LEVEL[e.n or 0] or "favours"
        if e.slug == IC.CROWN then
            return string.format("The Crown %s its side on %s.", level, ICUI.law_title(e.key))
        end
        return string.format("%s %s its side on %s.", house, level, ICUI.law_title(e.key))
    elseif e.kind == "law_overrule" then
        return string.format("You overruled the court: %s %s.", ICUI.law_title(e.key),
            (e.n == 1) and "passed" or "failed")
```

The Help topic, after the "Governments" topic. Pick the topic icon from `ICUI.HELP_ICONS`, using the one the Governments topic uses:

```lua
    {title = "Laws", icon = "crown", lines = {
        "{@crown}Four kinds of law hold the realm, and one of each is in force. Only a vote of the court changes one.",
        "{@bullet}Choose a law on the Laws tab to read it, and propose it for {@influence}{law_propose_cost}.",
        "{@party}Every man votes with his own influence, as his party does: for, against, or by its loyalty to you.",
        "{@loyalty}A party with no stake votes with you from {law_loyal_line} loyalty, and against you below {law_disloyal_line}.",
        "{@turns}A vote runs {law_vote_turns} turns. Parties put their own laws to the court, and the tab is marked until you answer.",
        "{@influence}Push your side slightly, strongly or fully, for {@influence}{law_push_1}, {law_push_2} or {law_push_3}.",
        "{@bullet}A pushed party's men count for more. Parties with a stake push too, when they are losing.",
        "{@influence}Win a man over for about half his influence. A cautious man costs more, a man against you double.",
        "{@influence}Pass now or Fail now decides the vote for {@influence}{law_overrule_cost}. The losing parties resent it.",
        "{@bullet}Everything you pay comes from your own party's men, and their votes shrink with it.",
    }},
```

In `ICUI.help_vars`, after `vars.tiers = #IC.TIERS`:

```lua
    -- THE THREE SUPPORT LEVELS, by name (spec 2026-10-02 laws).
    for i = 1, #IC.TUNE.law_push_cost do vars["law_push_" .. i] = IC.TUNE.law_push_cost[i] end
```

Help lines must fit one row; the gate measures them. A line that fails is split, which is a ruling for the ledger. With twelve topics, `HELP_SLOTS` (12) is exactly full.

- [ ] **Step 4: Run every gate.**

Run: `luac -p` on the UI file; `py tools/check_lua_api.py`; `py tools/check_lua_undeclared.py` (baseline unchanged); `py tools/check_lua_literal_left.py`; `py tools/gen_ic_ui.py --check`; `py tools/import_iron_court.py`; the harness.
Expected: all clean. Harness: Task 7's block check and these five turn green.

- [ ] **Step 5: Ledger.**

---

### Task 9: The vote screen

**Files:**
- Modify: the UI file:
  - replace the `ICUI.draw_law_vote` stub;
  - add click branches in `ICUI.register`.
- Test: the harness.

**Interfaces:**
- Consumes: Tasks 2 to 5 and Tasks 7 and 8.
- Produces:
  - `ICUI.law_groups(vote, t) -> {aye = {...}, nay = {...}, abstain = {...}}`. Each group is `{party, side, w, n, won, men = {{cqi, n, w}...}}`, heaviest first;
  - `ICUI.draw_law_vote(panel, faction, category)`;
  - `ICUI.lb_men[block][k] = cqi`;
  - clicks `ic_lv_back`, `ic_lv_st_N`, `ic_lv_lvl_N`, `ic_lv_over_N`, `ic_lb_win_N`.

- [ ] **Step 1: Write the failing checks.**

```lua
check("laws: the vote screen splits the court into sides of party blocks, heaviest first", function()
    local court = law_court({{"crown", 300}, {"legion", 500}, {"legion", 100}, {"ledger", 200}, {"forge", 90}})
    law_vote(court, "ash", "aye", "legion")
    court.houses.forge.loyalty = 50
    with_fake_panel(function(panel)
        ICUI.view, ICUI.law_cat = "laws", "labour"
        ICUI.refresh()
        local b1 = panel.children[ICUI.LAWBLOCK .. "_1"]
        local b5 = panel.children[ICUI.LAWBLOCK .. "_" .. (ICUI.LB_PER_SIDE + 1)]
        assert(b1.visible and b1.children.ic_lb_name.text == ICUI.house_name("legion", F),
            "the heaviest aye block is not the Legion")
        assert(b1.children.ic_lb_total.text == "600", "the Legion's total " .. tostring(b1.children.ic_lb_total.text))
        assert(b5.visible and b5.children.ic_lb_name.text == ICUI.house_name("ledger", F), "the nay side")
        assert(not panel.children[ICUI.LAWBLOCK .. "_3"].visible, "an empty block shows")
        assert(string.find(panel.children.ic_lv_abstain.text, ICUI.house_name("forge", F), 1, true),
            "the abstaining Forge is not named")
        assert(panel.children[ICUI.LAW .. "_1"].visible == false, "the board shows under the vote")
    end)
    gov_done()
end)

check("laws: a block shows four men at most, prices winnable men, and sums the rest", function()
    local men = {{"crown", 2000}}
    for i = 1, 6 do men[#men + 1] = {"ledger", 100 + i} end
    local court = law_court(men)
    law_vote(court, "ash", "aye", "crown")
    with_fake_panel(function(panel)
        ICUI.view, ICUI.law_cat = "laws", "labour"
        ICUI.refresh()
        local b = panel.children[ICUI.LAWBLOCK .. "_" .. (ICUI.LB_PER_SIDE + 1)]
        assert(b.children.ic_lb_win_1.visible and string.find(b.children.ic_lb_win_1.text, "Win", 1, true),
            "the richest Ledger man has no Win button")
        assert(ICUI.lb_men[ICUI.LB_PER_SIDE + 1][1] == 9007, "the block's first man is not the richest")
        assert(string.find(b.children.ic_lb_more.text, "+2", 1, true), "the two men past four are not summed: "
            .. tostring(b.children.ic_lb_more.text))
        local crown = panel.children[ICUI.LAWBLOCK .. "_1"]
        assert(not crown.children.ic_lb_win_1.visible, "a Crown man has a Win button")
    end)
    gov_done()
end)

check("laws: the hand lights your stance and paid levels, and its buttons send the five ops", function()
    local court = law_court({{"crown", 3000}, {"ledger", 200}})
    local v = law_vote(court, "ash", "aye", "legion")
    ICUI.register()
    local click = core.listeners["ic_click"]
    with_fake_panel(function(panel)
        ICUI.view, ICUI.law_cat = "laws", "labour"
        ICUI.refresh()
        assert(panel.children.ic_lv_st_1.images[0] == ICUI.PIP_ON, "Support is not lit")
        click({string = "ic_lv_lvl_2", component = panel.children.ic_lv_lvl_2})
        assert(v.push.crown == 2, "Strongly favour did not push")
        assert(string.find(panel.children.ic_lv_lvl_1.text, "paid", 1, true), "level 1 is not marked paid")
        click({string = "ic_lv_st_2", component = panel.children.ic_lv_st_2})
        assert(v.stance == "nay", "Oppose did not change the stance")
        ICUI.clicked_index = function() return ICUI.LB_PER_SIDE + 1, ICUI.LAWBLOCK .. "_" .. (ICUI.LB_PER_SIDE + 1) end
        click({string = "ic_lv_st_1", component = panel.children.ic_lv_st_1})
        click({string = "ic_lb_win_1", component = {}})
        assert(v.won[9002] == "aye", "Win him did not win the Ledger man")
        click({string = "ic_lv_over_2", component = panel.children.ic_lv_over_2})
        assert(court.votes.labour == nil and IC.law_in_force(F, "labour") == "measure", "Fail now did not fail it")
        assert(ICUI.law_cat == nil, "the screen did not go back to the board")
    end)
    ICUI.clicked_index = ICUI_CLICKED_INDEX
    gov_done()
end)
```

Before the first check, save `local ICUI_CLICKED_INDEX = ICUI.clicked_index` at harness top level, beside `law_court`. Read how the existing plot-click check restores `clicked_index`, and do what it does.

- [ ] **Step 2: Run the harness and watch the three new checks fail.**

Expected: 3 `FAIL laws:` lines.

- [ ] **Step 3: Implement.** Replace the stub:

```lua
-- THE VOTE (spec section 4.2): each side's parties as blocks, heaviest first.
-- A party's won men are a group of their own on the side they were won to.
function ICUI.law_groups(vote, t)
    local by, out = {}, {aye = {}, nay = {}, abstain = {}}
    for _, m in ipairs(t.men) do
        local side = m.side or "abstain"
        local key = m.party .. "|" .. side .. "|" .. (m.why == "won" and "won" or "")
        local g = by[key]
        if not g then
            g = {party = m.party, side = side, w = 0, n = 0, won = m.why == "won", men = {}}
            by[key] = g
            out[side][#out[side] + 1] = g
        end
        g.w, g.n = g.w + m.w, g.n + m.n
        g.men[#g.men + 1] = m
    end
    for _, list in pairs(out) do
        table.sort(list, function(a, b)
            if a.w ~= b.w then return a.w > b.w end
            return a.party < b.party
        end)
        for _, g in ipairs(list) do
            table.sort(g.men, function(a, b)
                if a.n ~= b.n then return a.n > b.n end
                return a.cqi < b.cqi
            end)
        end
    end
    return out
end

local function mult_text(level)
    local m = IC.law_mult(level)
    if m % 100 == 0 then return string.format("x%d", m / 100) end
    return string.format("x%.1f", m / 100)
end

function ICUI.fill_law_block(block, faction, cat, vote, g, index)
    ICUI.lb_men[index] = {}
    ICUI.set_plate(block, "ic_lb_crest", g.party)
    ICUI.set_face(block, "ic_lb_crest", ICUI.crest(g.party))
    set_text(comp("ic_lb_name", block), ICUI.house_name(g.party, faction))
    local level = g.won and 0 or ((vote.push or {})[g.party] or 0)
    local words
    if g.won then
        words = "Won over by you"
    elseif level > 0 then
        words = string.format("%s it  %s", ICUI.LAW_LEVEL[level], mult_text(level))
        words = string.upper(string.sub(words, 1, 1)) .. string.sub(words, 2)
    else
        words = "Votes for it"
    end
    set_text(comp("ic_lb_level", block), words)
    for p = 1, 3 do
        ICUI.set_crest(block, "ic_lb_pip_" .. p, p <= level and ICUI.PIP_ON or ICUI.PIP_OFF)
    end
    set_text(comp("ic_lb_total", block), tostring(g.w))
    for k = 1, ICUI.LB_MEN do
        local m = g.men[k]
        show(comp("ic_lb_face_" .. k, block), m ~= nil)
        show(comp("ic_lb_man_" .. k, block), m ~= nil)
        local win = comp("ic_lb_win_" .. k, block)
        if m then
            local man = IC.character_by_cqi(faction, m.cqi)
            ICUI.set_plate(block, "ic_lb_face_" .. k, g.party)
            ICUI.set_face(block, "ic_lb_face_" .. k, ICUI.portrait_path(m.cqi))
            local name = man and ICUI.character_name(man) or ""
            name = string.match(name, "^(%S+)") or name
            set_text(comp("ic_lb_man_" .. k, block), string.format("%s - %d", name, m.n))
            local price = IC.law_win_price(faction, cat, m.cqi)
            show(win, price ~= nil)
            if price then
                set_text(win, string.format("Win: [[img:%s]][[/img]]%d", ICUI.COST_ICON, price))
                ICUI.lb_men[index][k] = m.cqi
            end
        else
            show(win, false)
        end
    end
    local more = #g.men - ICUI.LB_MEN
    set_text(comp("ic_lb_more", block), more > 0 and string.format("+%d more", more) or "")
end

function ICUI.draw_law_bar(panel, groups, t)
    local bar = comp("ic_lv_bar", panel)
    if not bar then return end
    local bx, by = bar:Position()
    local bw, bh = bar:Dimensions()
    local all = t.aye + t.nay + t.abstain
    local segs = {}
    for _, g in ipairs(groups.aye) do segs[#segs + 1] = {g.party, g.w, true} end
    for _, g in ipairs(groups.nay) do segs[#segs + 1] = {g.party, g.w, false} end
    local lx, rx = bx, bx + bw
    for i = 1, ICUI.LAW_SEGS do
        local seg, crest = comp("ic_lv_seg_" .. i, panel), comp("ic_lv_segc_" .. i, panel)
        local s = segs[i]
        local w = (s and all > 0) and math.floor(bw * s[2] / all) or 0
        show(seg, w > 0)
        show(crest, w > bh)
        if w > 0 then
            local x = s[3] and lx or (rx - w)
            if s[3] then lx = lx + w else rx = rx - w end
            seg:MoveTo(x, by)
            ICUI.resize(seg, w, bh)
            pcall(function() seg:SetImagePath("ui/derpy_ic/house_plate_" .. s[1] .. ".png", 0) end)
            if w > bh then
                crest:MoveTo(x + math.floor((w - bh) / 2) + 2, by + 2)
                ICUI.set_crest(panel, "ic_lv_segc_" .. i, ICUI.crest(s[1]), bh - 4)
            end
        end
    end
end

function ICUI.draw_law_vote(panel, faction, cat)
    local vote = IC.law_vote_of(faction, cat)
    if not vote then return "" end
    local t = IC.law_tally(faction, cat, vote)
    local groups = ICUI.law_groups(vote, t)
    local left = math.max(0, vote.ends - cm:model():turn_number())
    local old = IC.law_in_force(faction, cat)
    ICUI.set_crest(panel, "ic_lv_icon", ICUI.law_icon(cat, vote.option))
    set_text(comp("ic_lv_name", panel), ICUI.law_name(cat, vote.option))
    set_text(comp("ic_lv_fx", panel), table.concat(ICUI.law_short(cat, vote.option), ", "))
    set_text(comp("ic_lv_by", panel), "Proposed by "
        .. (vote.proposer == IC.CROWN and "you" or ICUI.house_name(vote.proposer, faction)))
    set_text(comp("ic_lv_turns", panel), string.format("%d turn%s left", left, left == 1 and "" or "s"))
    set_text(comp("ic_lv_back", panel), "Back to the laws")
    local all = t.aye + t.nay + t.abstain
    set_text(comp("ic_lv_aye", panel), string.format("Aye %d%%  (%d)", ICUI.pct(t.aye, all), t.aye))
    set_text(comp("ic_lv_abs", panel), string.format("Abstaining %d%%", ICUI.pct(t.abstain, all)))
    set_text(comp("ic_lv_nay", panel), string.format("Nay %d%%  (%d)", ICUI.pct(t.nay, all), t.nay))
    ICUI.draw_law_bar(panel, groups, t)
    ICUI.lb_men = {}
    local heads = {"Enact " .. ICUI.law_name(cat, vote.option), "Keep " .. ICUI.law_name(cat, old)}
    local icons = {ICUI.law_icon(cat, vote.option), ICUI.law_icon(cat, old)}
    for s = 1, 2 do
        local side = s == 1 and "aye" or "nay"
        local mine = vote.stance == side
        ICUI.set_crest(panel, "ic_lv_sicon_" .. s, icons[s])
        set_text(comp("ic_lv_shead_" .. s, panel), heads[s])
        set_text(comp("ic_lv_stag_" .. s, panel), mine and "The Crown's side" or "")
        show(comp("ic_lv_screst_" .. s, panel), mine)
        if mine then
            ICUI.set_plate(panel, "ic_lv_screst_" .. s, IC.CROWN)
            ICUI.set_face(panel, "ic_lv_screst_" .. s, ICUI.crest(IC.CROWN))
        end
        local list = groups[side]
        for k = 1, ICUI.LB_PER_SIDE do
            local index = (s - 1) * ICUI.LB_PER_SIDE + k
            local block = comp(ICUI.LAWBLOCK .. "_" .. index, panel)
            show(block, list[k] ~= nil)
            if block and list[k] then ICUI.fill_law_block(block, faction, cat, vote, list[k], index) end
        end
        local rest, w = 0, 0
        for k = ICUI.LB_PER_SIDE + 1, #list do rest, w = rest + 1, w + list[k].w end
        set_text(comp("ic_lv_smore_" .. s, panel),
            rest > 0 and string.format("and %d more parties, %d influence", rest, w) or "")
    end
    local abst = {}
    for _, g in ipairs(groups.abstain) do
        abst[#abst + 1] = string.format("%s (%d)", ICUI.house_name(g.party, faction), g.n)
    end
    set_text(comp("ic_lv_abstain", panel), #abst > 0 and ("Abstaining: " .. table.concat(abst, ", ")
        .. ". A party with no stake votes with you only from "
        .. IC.TUNE.law_loyal_line .. " loyalty.") or "Nobody abstains.")
    set_text(comp("ic_lv_sideh", panel), "Your side")
    set_text(comp("ic_lv_supph", panel), "Your support")
    set_text(comp("ic_lv_overh", panel), "Decide it now")
    for i = 1, 3 do
        local b = comp("ic_lv_st_" .. i, panel)
        set_text(b, ICUI.LAW_STANCE_BTN[i])
        pcall(function() b:SetImagePath(vote.stance == ICUI.LAW_STANCES[i] and ICUI.PIP_ON or ICUI.BTN_ART, 0) end)
    end
    local cur = (vote.push or {})[IC.CROWN] or 0
    for l = 1, 3 do
        local b = comp("ic_lv_lvl_" .. l, panel)
        local label
        if l <= cur then
            label = ICUI.LAW_LEVEL_BTN[l] .. " (paid)"
        else
            local ok = IC.law_can_push(faction, cat, l)
            label = string.format("%s [[img:%s]][[/img]]%d", ICUI.LAW_LEVEL_BTN[l], ICUI.COST_ICON, IC.law_push_price(vote, IC.CROWN, l))
            if not ok then label = ICUI.red(label) end
        end
        set_text(b, label)
        pcall(function() b:SetImagePath(l <= cur and ICUI.PIP_ON or ICUI.BTN_ART, 0) end)
    end
    local can = IC.crown_purse(faction) >= IC.TUNE.law_overrule_cost
    for i, word in ipairs({"Pass now", "Fail now"}) do
        local label = string.format("%s [[img:%s]][[/img]]%d", word, ICUI.COST_ICON, IC.TUNE.law_overrule_cost)
        set_text(comp("ic_lv_over_" .. i, panel), can and label or ICUI.red(label))
    end
    return ""
end
```

`ICUI.lb_men = {}` also goes at the top of the laws section, so a click before the first draw finds a table. The blocks are shown by this draw, after Task 7's refresh hid them all.

The clicks, after Task 8's:

```lua
        elseif id == "ic_lv_back" and comp(ICUI.PANEL) then
            ICUI.law_cat, ICUI.notice = nil, nil
            ICUI.refresh()
        elseif string.match(id, "^ic_lv_st_%d$") and comp(ICUI.PANEL) and ICUI.law_cat then
            local i = tonumber(string.match(id, "(%d)$"))
            ICUI.send(ICUI.player(), "law_stance", ICUI.law_cat .. "|" .. ICUI.LAW_STANCES[i])
            ICUI.refresh()
        elseif string.match(id, "^ic_lv_lvl_%d$") and comp(ICUI.PANEL) and ICUI.law_cat then
            ICUI.send(ICUI.player(), "law_push", ICUI.law_cat .. "|" .. string.match(id, "(%d)$"))
            ICUI.refresh()
        elseif string.match(id, "^ic_lv_over_%d$") and comp(ICUI.PANEL) and ICUI.law_cat then
            local pass = string.match(id, "(%d)$") == "1"
            ICUI.send(ICUI.player(), "law_overrule", ICUI.law_cat .. "|" .. (pass and "1" or "0"))
            ICUI.refresh()
        elseif string.match(id, "^ic_lb_win_%d$") and comp(ICUI.PANEL) and ICUI.law_cat then
            local block = ICUI.clicked_index(context)
            local k = tonumber(string.match(id, "(%d)$"))
            local cqi = block and ICUI.lb_men[block] and ICUI.lb_men[block][k]
            if cqi then ICUI.send(ICUI.player(), "law_win", ICUI.law_cat .. "|" .. tostring(cqi)) end
            ICUI.refresh()
```

`ICUI.refresh` runs `ICUI.law_screen`, which takes an overruled category back to the board.

- [ ] **Step 4: Run every gate.**

Run: the same set as Task 8 Step 4, plus `py tools/gen_ic_ui.py --check` for checks 21b, 24 and 25 on the new `SetImagePath` and `set_*` sites.
Expected: all clean; the three new checks green. A 21b/25 finding on `seg:SetImagePath`, or on the button `SetImagePath`, is fixed by routing it through `ICUI.set_crest` (one slot, slot 0) and recorded as a ruling.

- [ ] **Step 5: Ledger.**

---

### Task 10: The preview pictures, mutants, sweep and ship

**Files:**
- Modify: `tools/preview_iron_court.py`.
- Modify: `tools/mutate_iron_court.py`.
- Modify: `docs/SESSION_INDEX.md`, `docs/sessions/HANDOFF_20261002_IRON_COURT_GOVERNMENTS.md` (a section 9 for laws), `tools/sync_iron_court_repo.py` (the spec and plan), and `CLAUDE.md`'s `preview_iron_court.py` entry, one clause only.

- [ ] **Step 1: The two pictures.** Port `scratchpad/law_mock2.py`'s `LAW_DRAW` into `preview_iron_court.py` as two views:
  - add `"law_board"` and `"law_vote"` to `VIEWS`;
  - add `OUT_LAW_BOARD` and `OUT_LAW_VOTE` beside `OUT_PETITIONS`;
  - draw from the real generator's `PANEL_LAYOUT`, `LAW_GRID`/`LAW_LAYOUT` and `LB_GRID`/`LB_LAYOUT`, with the instances pasted from the two new twui files (`doc_of("derpy_ic_law.twui.xml")`, `doc_of("derpy_ic_lawblock.twui.xml")`), not from the mock's stand-ins;
  - read card text from the shipped model and loc tables where the mock typed it: the names, the short effects (via `gen_iron_court.build()`'s loc) and the icons (from `IC.LAWS`);
  - `hidden` drops every `ic_law_*`/`ic_lv_*` cell on every other view, and the vote cells on the board and the board cells on the vote. Read those conditions off the Lua's own `show(...)` lines, by regex, as the ziggurat's is read;
  - `STRINGS` gets `"ic_tab_laws": "Laws"`, and the lit tab is `laws` on both views;
  - the demo is the hard case: the longest law name in a card, the longest party name in a block, a side with five parties so the "and N more" line draws, and a party with six men so "+2 more" draws.

Run: `py tools/preview_iron_court.py --check`, then `py tools/preview_iron_court.py`.
Expected: no findings; `ic_law_board.png`, `ic_law_board_1600.png`, `ic_law_vote.png` and `ic_law_vote_1600.png` are written. Look at all four. Compare the 1920 pair against the approved mocks; anything that clips, overlaps or reads worse at 1600 is a finding to fix in Task 7's layout, ledgered.

- [ ] **Step 2: The mutants.** Append under a `law:` prefix, each a plausible mistake, with anchors copied exactly from the shipped Lua:

```python
    ("law: a tie passes", M,
     """function IC.law_passes(t) return t.aye > t.nay end""",
     """function IC.law_passes(t) return t.aye >= t.nay end"""),
    ("law: a man with no influence votes", M,
     """                if n > 0 and party then out[#out + 1] = {cqi = cqi, party = party, n = n} end""",
     """                if n >= 0 and party then out[#out + 1] = {cqi = cqi, party = party, n = n} end"""),
    ("law: a won man is multiplied too", M,
     """        if won then
            side, why = won, "won"
        elseif side then""",
     """        if won then
            side, why = won, "won"
        end
        if side then"""),
    ("law: a disloyal party votes with the Crown", M,
     """        return vote.stance == "aye" and "nay" or "aye", "disloyal\"""",
     """        return vote.stance, "disloyal\""""),
    ("law: the loyal line is above, not at", M,
     """    if loyalty >= IC.TUNE.law_loyal_line then return vote.stance, "loyal" end""",
     """    if loyalty > IC.TUNE.law_loyal_line then return vote.stance, "loyal" end"""),
    ("law: a raise pays the full price", M,
     """    return cost[level] - (had and cost[had] or 0)""",
     """    return cost[level]"""),
    ("law: a level can be lowered", M,
     """    if level <= (vote.push[IC.CROWN] or 0) then return false, "law_pushed" end""",
     """    if level == (vote.push[IC.CROWN] or 0) then return false, "law_pushed" end"""),
    ("law: an abstaining Crown pushes", M,
     """    if vote.stance == "abstain" then return false, "law_abstain" end
    if level""",
     """    if level"""),
    ("law: a man against you is not doubled", M,
     """    if s and s ~= vote.stance then price = price * 2 end""",
     """"""),
    ("law: a Crown man can be won", M,
     """    if man.party == IC.CROWN then return nil, "law_crown_man" end""",
     """"""),
    ("law: the overrule angers the winners", M,
     """    local losing = pass and "nay" or "aye\"""",
     """    local losing = pass and "aye" or "nay\""""),
    ("law: a failed party proposal costs nothing", M,
     """        if vote.proposer ~= IC.CROWN then
            IC.move_loyalty(faction_key, vote.proposer, IC.TUNE.law_fail_loss)
        end""",
     """"""),
    ("law: a party proposes during its rest", M,
     """    if now - (court.law_rest or 0) < IC.TUNE.law_party_rest then return nil end""",
     """"""),
    ("law: a party proposes what it is against", M,
     """                   and IC.law_stance(cat, opt, slug) == "aye" then""",
     """                   and IC.law_stance(cat, opt, slug) ~= nil then"""),
    ("law: a party pushes while well ahead", M,
     """            if t[side] - t[other] <= margin and IC.spend_party(faction_key, slug, price) then""",
     """            if IC.spend_party(faction_key, slug, price) then"""),
    ("law: the purse spends a seat's bar", M,
     """                local spare = IC.standing(faction_key, cqi) - (bar[cqi] or 0)
                if spare > 0 then
                    men[#men + 1] = {cqi = cqi, spare = spare}""",
     """                local spare = IC.standing(faction_key, cqi)
                if spare > 0 then
                    men[#men + 1] = {cqi = cqi, spare = spare}"""),
    ("law: switched off, the votes stay", M,
     """    if IC.TUNE.laws == false then IC.court(faction_key).votes = {} end""",
     """"""),
    ("law: an AI court wears a law", M,
     """function IC.laws_on(faction_key)
    return IC.TUNE.laws ~= false and IC.is_human(faction_key)""",
     """function IC.laws_on(faction_key)
    return IC.TUNE.laws ~= false"""),
    ("law: the answer is not remembered", M,
     """    vote.stance = stance
    vote.answered = true""",
     """    vote.stance = stance"""),
    ("law: the marker ignores the answer", U,
     """        if v and v.proposer ~= IC.CROWN and not v.answered then s.laws = s.laws + 1 end""",
     """        if v and v.proposer ~= IC.CROWN then s.laws = s.laws + 1 end"""),
    ("law: the board frames the chosen card, not the law in force", U,
     """                card:SetImagePath(force and ICUI.PARTY_SELECTED or ICUI.MASK_NONE, ICUI.LAW_SEL_INDEX)""",
     """                card:SetImagePath(chosen and ICUI.PARTY_SELECTED or ICUI.MASK_NONE, ICUI.LAW_SEL_INDEX)"""),
    ("law: a block shows a Win button on every man", U,
     """            show(win, price ~= nil)""",
     """            show(win, true)"""),
```

The two `out.any` mutants (around 3884-3907) still match if Task 8 appended `or out.laws` at the end of that line. If not, re-aim their anchors to the new line; that is a ruling.

Run: `py tools/mutate_iron_court.py "law:"`, and `py tools/mutate_iron_court.py "out.any"` (or whatever names those two carry).
Expected: every mutant killed, no stale anchor. A survivor means a check is too weak: strengthen the check (red against the mutant, green without it), never the mutant. Each survivor fixed is ledgered.

Then run `py tools/gen_iron_court.py --check` and the harness again. The runner restores the source but not what it wrote, so regenerate the TSVs and twui if any mutant touched a generator input.

- [ ] **Step 3: The full sweep.**

Run, in order:
- the harness;
- `py tools/gen_iron_court.py --check` and `--selftest`;
- `py tools/gen_ic_ui.py --check`, and `--selftest` in the background;
- `py tools/preview_iron_court.py --check`;
- `py tools/import_iron_court.py`;
- `py tools/check_lua_api.py`, `check_lua_literal_left.py` and `check_lua_undeclared.py` (baseline unchanged);
- `py tools/check_effect_signs.py`;
- `py tools/check_effect_bundle_loc.py`;
- `luac -p` on all five court Lua files.

Expected: every one clean; harness `ok (961 checks)`: 925, plus 7 (Task 1), 7 (Task 2), 6 (Task 3), 7 (Task 4), 0 (Task 5 widens existing checks), 1 (Task 7), 5 (Task 8) and 3 (Task 9). Record the real number; a difference from 961 is a ledger note that names which task's count moved, not a failure.

- [ ] **Step 4: Deploy.** If `Warhammer3.exe` is not running and RPFM is open: `py tools/deploy_iron_court.py`. It backs up, builds, copies to `data/` and reads the pack back. If the game is running: `py tools/deploy_iron_court.py --wait`. If RPFM is closed, say so and stop the deploy; never text-edit a pack.
Expected: the deploy prints the pack size and its read-back verification, including the two new twui files and their compacts.

- [ ] **Step 5: Docs and repo.**
  - Add a section 9 "Laws" to the governments handoff: what shipped, the rulings ledgered, and what is owed in game:
    - the Tower seat cost at -25;
    - captives at -10;
    - the two scripted convoy effects;
    - the Hell-Forge cost effect beside the caps pack;
    - the gold frame's offset on a law card;
    - the support bar at a court of nine parties.
  - Add one line to `docs/SESSION_INDEX.md` for laws built.
  - Add the spec and plan to `tools/sync_iron_court_repo.py`'s list, as the deeds pair is, and run the sync. Do not commit or push without being asked.

- [ ] **Step 6: Ledger.**
