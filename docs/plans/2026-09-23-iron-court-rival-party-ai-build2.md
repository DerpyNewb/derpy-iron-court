# Iron Court Rival Party AI, Build 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rival parties in the player's court make demands, issued as real missions, and loyal
parties make offers the player can accept from the party card's list.

**Architecture:**
- Everything is added to `zzz_derpy_iron_court_parties.lua` as two new entries in `IC.PARTY_ACTS`
  (`demand`, `offer`) plus their upkeep.
- Demand and offer state is stored in the existing agenda saved value, which grows from three
  `|` parts to five.
- A demand is a string-issued mission with one `SCRIPTED` objective. The Lua decides every
  outcome, and the three mission events serve only as a backstop.
- The panel reuses the mood button and the favour list it already opens. No new component is
  added.

**Tech Stack:** Lua 5.1 (game scripts and the stock-Lua harness), Python 3 (the generators and
the mutation runner), RPFM for the pack (controller only).

**Spec:** `docs/superpowers/specs/2026-09-23-iron-court-rival-party-ai-design.md`, sections 3
(demands), 5 (offers), 5b, 7 and 9. Build 1 shipped sections 2, 3b and 4. Its plan is
`docs/superpowers/plans/2026-09-23-iron-court-rival-party-ai-build1.md`, and its write-up is §4
of `docs/sessions/HANDOFF_20260923_IRON_COURT_AI_LIVE_CHECK.md`.

## Global Constraints

- **Player court only.** `IC.party_turn` already returns at once when
  `not IC.is_human(faction_key)`. Nothing here may bypass it.
- **At most one court event a turn.** A demand being issued and an offer being made are events.
  A demand being met, refused or voided, and an offer lapsing, are upkeep and do not take the
  slot. Upkeep runs at the top of `IC.party_turn`, after `IC.end_feuds`.
- **Demands:**
  - loyalty 26 to 74 inclusive;
  - one live demand court-wide;
  - motive `max(0, share / 10 - (offices + provinces held)) * 8`;
  - +12 loyalty when met (on top of `loyalty_appointed`), -10 when refused or run out, nothing
    when void;
  - 5 turns.
- **The demand mission:**
  - `cm:trigger_custom_mission_from_string` with issuer `CLAN_ELDERS` and `turn_limit 5`;
  - one objective: `type SCRIPTED`, `script_key derpy_ic_demand`,
    `override_text mission_text_text_<key>`;
  - payload `text_display derpy_ic_demand_reward`;
  - keys `derpy_ic_demand_office` and `derpy_ic_demand_province`.
- **DB tables:** `missions_tables` version **0** (19 columns). `campaign_payload_ui_details_tables`
  version **2** (4 columns). Both versions are pinned against `read_vanilla_cache.version()`.
- **Offers:**
  - loyalty 75 or above; one open offer per party; it lasts 3 turns;
  - accepting costs 3 loyalty with every other rival party (never the Crown, never the giver);
  - gold is `floor(share x 60)`;
  - backing is +100 influence to the Crown man closest below a vacant office's bar, within 100
    of it and past its rank bar;
  - calm sets another party's `clock = 0` and gives it +10 loyalty;
  - troops are 2 units of the party's own type, granted to a Crown lord's army with 2 free
    slots.
- **Events** `party_demand` 2619, `party_demand_refused` 2620 and `party_offer` 2621 are appended
  after `party_feud_murder` (2618), in `IC.EVENTS` and in `tools/gen_iron_court.py` `EVENTS`.
- **Loyalty is written only through `IC.move_loyalty`.** `import_iron_court.py` refuses to pack
  any other writer.
- **No localisation call from the parties file.** It runs inside a turn handler, where a loc
  call crashes the game at turn 1. Names are resolved in the UI file at draw time only.
- **No emojis.** Never the word "rung". Player text says party, influence, office, overseer.
- **Mutant anchors** go on code lines, never on comment lines.
- **Never diff, build or deploy while `mutate_iron_court.py` is running.** It writes mutants
  into the shipped Lua.
- **The workspace is not a git repo.** There are no commit steps. The checkpoint after each task
  is the harness run.
- **Commands.** Lua is checked with
  `& "C:\Program Files (x86)\Lua\5.1\luac.exe" -p <file>` and run with
  `& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua`, from the workspace
  root in PowerShell.

**Deviations from the spec.** Tell the author at handoff.

1. **Offer and demand state lives in the agenda saved value,** `derpy_ic_agenda_<faction>`,
   not in court fields 20-22. `IC.pack` stays untouched, as in Build 1.
2. **ACCEPT and DECLINE are rows at the top of the party's favour list.** The party card's
   button already opens that list, and the card has no room for two more buttons. The mood
   button reads OFFERING, and its tooltip says what is offered.
3. **The Lua owns every demand outcome.** `IC.party_turn` settles met, refused, void and expiry
   itself and then closes the mission. `MissionSucceeded`, `MissionFailed` and
   `MissionCancelled` settle only a demand still open. Settling twice is impossible, because
   the record is cleared before any engine call.
4. **Demand missions cannot be cancelled by hand** (`can_be_manually_cancelled false`).
   Cancelling would otherwise be a free refusal.
5. **The Intrigue tab's alert line names a warned move first.** This was deferred from Build 1's
   final review.
6. **Bridge probes are not run.** The wh3 bridge is not registered in the session. The author
   checks in game that a demand mission renders and completes, and that troops arrive.

## Files

| File | Change |
|---|---|
| `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_parties.lua` | knobs, agenda fields, demands, offers, upkeep, three mission listeners |
| `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua` | `IC.LOG_KINDS` +6, `IC.EVENTS` +3 |
| `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua` | record sentences, card words, tooltip, favour-list rows, click routing, refusal sentences, Intrigue alert |
| `tools/gen_iron_court.py` | 3 events, 2 `missions` rows, 1 payload record, their loc, a key-parity check |
| `tools/gen_ic_ui.py` | two mood words in the measured fixture |
| `tools/_iron_court_harness.lua` | act filter, four engine stubs, checks |
| `tools/mutate_iron_court.py` | one mutant per rule |

---

### Task 1: State, knobs, events and record sentences

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_parties.lua` (knobs block
  lines 7-19, `IC.agenda` lines 32-69, `IC.save_agenda` lines 71-94)
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua` (`IC.LOG_KINDS` near
  line 523, `IC.EVENTS` near line 576)
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua`
  (`ICUI.intrigue_text`, after the `feud_end` branch near line 3518)
- Modify: `tools/gen_iron_court.py` (`EVENTS`, after the `party_feud_murder` tuple)
- Test: `tools/_iron_court_harness.lua`

**Interfaces:**
- Produces:
  - `IC.agenda(fk)` also returns `demand` (nil or
    `{slug, kind = "office"|"gov", cqi, key, was, ends}`) and `offers` (a table keyed by party
    slug, `{kind = "gold"|"backing"|"calm"|"troops", n, target, ends}`). `target` is a cqi
    number or a party slug, and it reads back from a save as a string.
  - The knobs `T.party_demand_low`, `_high`, `_met`, `_refused`, `_turns` and
    `T.party_offer_line`, `_turns`, `_envy`, `_gold_per_share`, `_backing`, `_calm`, `_units`.
  - In the harness: `use_acts(keep)`, `BUILD1_ACTS`, `ALL_ACTS`, `party_court(loyalty, acts)`,
    and the globals `missions_issued`, `missions_closed` and `units_granted`.

- [ ] **Step 1: The harness act filter, stubs and failing checks**

In `tools/_iron_court_harness.lua`, directly after
`assert(IC.party_turn, "the parties file must define IC.party_turn")` (near line 850), add:

```lua
-- BUILD 1'S THREE ACTS BY DEFAULT. Every check written before demands and
-- offers existed was written for a court where only these can fire; a check
-- that means the others names them through use_acts or party_court.
local ALL_ACTS = IC.PARTY_ACTS
local BUILD1_ACTS = {intrigue = true, feud = true, feud_move = true}
local function use_acts(keep)
    IC.PARTY_ACTS = {}
    for _, act in ipairs(ALL_ACTS) do
        if keep == "all" or keep[act.key] then
            IC.PARTY_ACTS[#IC.PARTY_ACTS + 1] = act
        end
    end
end
use_acts(BUILD1_ACTS)
```

Next to `treasury_calls = {}` (near line 387), add:

```lua
-- Every mission issued, every one closed, and every unit granted.
missions_issued = {}
missions_closed = {}
units_granted = {}
```

In the `cm` stub table, directly after the `treasury_mod` entry (near line 569), add:

```lua
    trigger_custom_mission_from_string = function(_self, faction_key, text)
        missions_issued[#missions_issued + 1] = {faction = faction_key, text = text}
    end,
    complete_scripted_mission_objective = function(_self, faction_key, key,
                                                   script, ok)
        missions_closed[#missions_closed + 1] = {faction = faction_key, key = key,
                                                 script = script, ok = ok}
    end,
    cancel_custom_mission = function(_self, faction_key, key)
        missions_closed[#missions_closed + 1] = {faction = faction_key, key = key,
                                                 cancelled = true}
    end,
    grant_unit_to_character = function(_self, lookup, unit)
        units_granted[#units_granted + 1] = {lookup = lookup, unit = unit}
    end,
```

Change the fixture's first two lines from

```lua
local function party_court(loyalty)
    IC.state = {}
```

to

```lua
local function party_court(loyalty, acts)
    use_acts(acts or BUILD1_ACTS)
    IC.state = {}
```

Then append these checks after the last parties check, before the final
`if #failures > 0 then` block, with exactly one blank line before that block:

```lua
check("the agenda keeps a demand and open offers across a reload", function()
    party_court({})
    local a = IC.agenda(F)
    a.demand = {slug = "legion", kind = "gov", cqi = 311, key = "prov_a",
                was = 301, ends = 15}
    a.offers.forge = {kind = "backing", n = 100, target = 302, ends = 13}
    a.offers.legion = {kind = "calm", n = 10, target = "forge", ends = 12}
    a.offers.chain = {kind = "gold", n = 3030, ends = 13}
    IC.save_agenda(F)
    IC.agenda_state = {}
    local b = IC.agenda(F)
    local d = b.demand
    assert(d and d.slug == "legion" and d.kind == "gov" and d.cqi == 311
           and d.key == "prov_a" and d.was == 301 and d.ends == 15,
           "the demand did not survive: " .. tostring(saved["derpy_ic_agenda_" .. F]))
    local o = b.offers.forge
    assert(o and o.kind == "backing" and o.n == 100
           and tonumber(o.target) == 302 and o.ends == 13,
           "the backing offer did not survive")
    assert(b.offers.legion and b.offers.legion.target == "forge",
           "the calm offer lost its party")
    assert(b.offers.chain and b.offers.chain.target == nil
           and b.offers.chain.n == 3030, "a gold offer grew a target")
    cm.get_human_factions = function() return {} end
end)

check("an agenda saved before demands and offers still loads", function()
    party_court({})
    saved["derpy_ic_agenda_" .. F] = "legion,unseat,311,301,muster,10|"
        .. "legion,forge,seat,banners,8,18|chain,14"
    IC.agenda_state = {}
    local a = IC.agenda(F)
    assert(a.plot and a.plot.move == "unseat", "the old plot was lost")
    assert(a.feuds.legion and a.calm.chain == 14, "the old feud or rest was lost")
    assert(a.demand == nil, "an old save grew a demand")
    assert(next(a.offers) == nil, "an old save grew an offer")
    cm.get_human_factions = function() return {} end
end)
```

- [ ] **Step 2: Run and see it fail**

Run: `& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua`

Expected: `FAIL the agenda keeps a demand and open offers across a reload: ...`, which fails on
indexing `offers`, a nil field.

- [ ] **Step 3: Knobs and agenda fields**

In the parties file, after `T.governor_xp           = 750`, add:

```lua
T.party_demand_low      = 26   -- demands from this loyalty...
T.party_demand_high     = 74   -- ...to this one
T.party_demand_met      = 12   -- on top of loyalty_appointed
T.party_demand_refused  = 10
T.party_demand_turns    = 5
T.party_offer_line      = 75   -- offers at or above this loyalty
T.party_offer_turns     = 3
T.party_offer_envy      = 3    -- every OTHER rival party, when one is accepted
T.party_offer_gold_per_share = 60
T.party_offer_backing   = 100
T.party_offer_calm      = 10
T.party_offer_units     = 2
```

Replace the comment block and first line of `IC.agenda` from
`-- plot = {slug, move, actor, target, key, turn}: one warned move, court-wide.` through
`    a = {plot = nil, feuds = {}, calm = {}}` with:

```lua
-- plot = {slug, move, actor, target, key, turn}: one warned move, court-wide.
-- feuds[slug] = rec for BOTH parties of a pair, rec = {a, b, cause, key, since, ends}.
-- calm[slug] = the turn a party may feud again.
-- demand = {slug, kind, cqi, key, was, ends}: one live demand, court-wide. `was`
-- is who held the post when it was made (0 for nobody).
-- offers[slug] = {kind, n, target, ends}. A target is a cqi or a party slug and
-- reads back from a save as a string.
function IC.agenda(faction_key)
    local a = IC.agenda_state[faction_key]
    if a then return a end
    a = {plot = nil, feuds = {}, calm = {}, demand = nil, offers = {}}
```

In the same function, after the `for _, entry in ipairs(split(parts[3] or "", ";")) do ... end`
loop and before the `end` that closes `if packed and packed ~= "" then`, add:

```lua
        local d = split(parts[4] or "", ",")
        if #d >= 6 then
            a.demand = {slug = d[1], kind = d[2], cqi = tonumber(d[3]),
                        key = d[4], was = tonumber(d[5]) or 0,
                        ends = tonumber(d[6]) or 0}
        end
        for _, entry in ipairs(split(parts[5] or "", ";")) do
            local o = split(entry, ",")
            if #o >= 5 then
                a.offers[o[1]] = {kind = o[2], n = tonumber(o[3]) or 0,
                                  target = o[4] ~= "-" and o[4] or nil,
                                  ends = tonumber(o[5]) or 0}
            end
        end
```

In `IC.save_agenda`, replace

```lua
    table.sort(feuds)
    table.sort(calm)
    cm:set_saved_value("derpy_ic_agenda_" .. faction_key,
        plot .. "|" .. table.concat(feuds, ";") .. "|"
        .. table.concat(calm, ";"))
```

with

```lua
    local demand = ""
    if a.demand then
        local d = a.demand
        demand = string.format("%s,%s,%d,%s,%d,%d", d.slug, d.kind, d.cqi,
                               d.key, d.was or 0, d.ends)
    end
    local offers = {}
    for slug, o in pairs(a.offers) do
        offers[#offers + 1] = string.format("%s,%s,%d,%s,%d", slug, o.kind, o.n,
            o.target ~= nil and tostring(o.target) or "-", o.ends)
    end
    table.sort(feuds)
    table.sort(calm)
    table.sort(offers)
    cm:set_saved_value("derpy_ic_agenda_" .. faction_key,
        plot .. "|" .. table.concat(feuds, ";") .. "|"
        .. table.concat(calm, ";") .. "|" .. demand .. "|"
        .. table.concat(offers, ";"))
```

- [ ] **Step 4: Log kinds, events, sentences, generator events**

In the model, `IC.LOG_KINDS`, after `party_recall = true, feud = true, feud_end = true,` add the
line:

```lua
    demand = true, demand_met = true, demand_refused = true, demand_void = true,
    offer = true, offer_taken = true,
```

In the model, `IC.EVENTS`, after `party_feud_murder  = {2618, true, true},` add:

```lua
    party_demand       = {2619, true, true},
    party_demand_refused = {2620, true, true},
    party_offer        = {2621, true, true},
```

In the UI file's `ICUI.intrigue_text`, directly after the `feud_end` branch (the one that
returns `"The feud between %s and %s is over."`), add:

```lua
    elseif e.kind == "demand" then
        return string.format("%s demands a post for one of their men.", house)
    elseif e.kind == "demand_met" then
        return string.format("The Crown grants %s's demand.", house)
    elseif e.kind == "demand_refused" then
        return string.format("%s's demand goes unmet, and they will remember it.",
                             house)
    elseif e.kind == "demand_void" then
        return string.format("%s's demand lapses: the man or the party is gone.",
                             house)
    elseif e.kind == "offer" then
        return string.format("%s offers the Crown a favour.", house)
    elseif e.kind == "offer_taken" then
        return string.format("The Crown accepts %s's offer, and the other "
                             .. "parties notice.", house)
```

In `tools/gen_iron_court.py`, append to `EVENTS` directly after the `party_feud_murder` tuple:

```python
    ("party_demand", True, "chd/diplomacy", "Neutral",
     "A Party Makes a Demand",
     "One of the court's parties demands a post for one of its men. Their card "
     "names the man and the post. Grant it and their loyalty rises; refuse it, "
     "or let the time run out, and it falls.",
     "DEMAND"),
    ("party_demand_refused", True, "chd/army_morale_down", "Negative",
     "A Demand Refused",
     "A party's demand went unmet. They will remember it, and their loyalty "
     "has fallen.",
     "REFUSED"),
    ("party_offer", True, "chd/diplomacy", "Positive",
     "A Party Offers a Favour",
     "A loyal party offers the Crown something for nothing. Their card says "
     "what. Click it to accept or decline, but the offer will not wait long, "
     "and the other parties will notice if you take it.",
     "OFFER"),
```

- [ ] **Step 5: Run everything**

Run:
```powershell
foreach ($f in "zzz_derpy_iron_court.lua","zzz_derpy_iron_court_ui.lua","zzz_derpy_iron_court_parties.lua") { & "C:\Program Files (x86)\Lua\5.1\luac.exe" -p "Modding Files\pack\script\campaign\mod\$f" }
& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua
py tools\gen_iron_court.py --selftest
py tools\gen_iron_court.py
```

Expected:
- the harness is green;
- `gen_iron_court.py` reports **596 loc rows**, which is 587 plus 3 events with 3 lines each,
  and writes the TSVs.

---

### Task 2: Demands - what a party asks for, and issuing it

**Files:**
- Modify: the parties file (new section after `IC.governor_xp`, before `IC.party_turn`)
- Modify: `tools/gen_iron_court.py` (`build()`, `TSV_META`, `check()`, a new
  `check_demand_keys()`)
- Test: `tools/_iron_court_harness.lua`

**Interfaces:**
- Consumes: `IC.candidates(fk)`, which returns `{cqi, rank, slug, busy, character}`;
  `IC.can_appoint(fk, office_slug, cqi)`; `IC.seats(fk)`, which returns a sorted list of
  province keys; `IC.offices_of_house`; `IC.provinces_of_house`; `IC.share`.
- Produces:
  - `IC.DEMAND_KEYS` = `{office = "derpy_ic_demand_office", gov = "derpy_ic_demand_province"}`;
  - `IC.DEMAND_SCRIPT_KEY` and `IC.DEMAND_REWARD`;
  - `IC.demand_target(fk, slug)`, which returns `{kind, cqi, key, was}` or nil;
  - `IC.demand_string(kind)`;
  - `IC.issue_demand(fk, slug, t)`, which returns a boolean;
  - the `demand` entry in `IC.PARTY_ACTS`.

- [ ] **Step 1: Write the failing checks**

Append after Task 1's checks:

```lua
local function act_named(key)
    for _, act in ipairs(ALL_ACTS) do
        if act.key == key then return act end
    end
    error("no party act " .. key)
end

check("a party in the demand band asks for the office it claims", function()
    party_court({legion = 50, forge = 90}, {demand = true})
    missions_issued = {}
    assert(IC.party_turn(F) == "demand", "no demand was made")
    local d = IC.agenda(F).demand
    assert(d and d.slug == "legion" and d.kind == "office" and d.cqi == 311
           and d.key == "warden" and d.was == 0
           and d.ends == 10 + IC.TUNE.party_demand_turns,
           "the demand is not legion's man for the warden's seat")
    local issued = missions_issued[1]
    assert(issued and issued.faction == F, "no mission went to the player")
    for _, want in ipairs({"key derpy_ic_demand_office;", "issuer CLAN_ELDERS;",
                           "turn_limit " .. IC.TUNE.party_demand_turns .. ";",
                           "type SCRIPTED;", "script_key derpy_ic_demand;",
                           "override_text mission_text_text_derpy_ic_demand_office;",
                           "text_display derpy_ic_demand_reward;"}) do
        assert(string.find(issued.text, want, 1, true),
               "the mission lacks " .. want .. ": " .. issued.text)
    end
    assert(cards_of("party_demand") == 1, "no demand card")
    cm.get_human_factions = function() return {} end
end)

check("a demand falls back to a province, never one a rival holds", function()
    party_court({legion = 50}, {demand = true})
    local court = IC.court(F)
    court.standing[311] = 50          -- under every office's influence bar
    court.govs.prov_a = 321           -- forge's man holds the first province
    local t = IC.demand_target(F, "legion")
    assert(t and t.kind == "gov" and t.key == "prov_b" and t.cqi == 311
           and t.was == 0, "the rival-held province was asked for, or none")
    court.govs.prov_a = 301           -- now the Crown's man holds it
    t = IC.demand_target(F, "legion")
    assert(t and t.key == "prov_a" and t.was == 301,
           "a Crown-held province was not asked for")
    cm.get_human_factions = function() return {} end
end)

check("demands come only from the loyalty band, one at a time", function()
    party_court({}, {demand = true})
    local demand = act_named("demand")
    local house = IC.court(F).houses["legion"]
    for loyalty, want in pairs({[25] = false, [26] = true, [74] = true,
                                [75] = false}) do
        house.loyalty = loyalty
        assert((demand.can(F, "legion") ~= nil) == want,
               "legion at loyalty " .. loyalty .. " got the wrong answer")
    end
    house.loyalty = 50
    IC.agenda(F).demand = {slug = "forge", kind = "office", cqi = 321,
                           key = "forge", was = 0, ends = 15}
    assert(demand.can(F, "legion") == nil,
           "a second demand was allowed while one is live")
    cm.get_human_factions = function() return {} end
end)

check("a demand's motive is its share against the posts it holds", function()
    party_court({legion = 50}, {demand = true})
    local demand = act_named("demand")
    local court = IC.court(F)
    local share = IC.share(F, "legion")
    assert(math.floor(demand.motive(F, "legion")) == math.floor(share / 10 * 8),
           "the motive is not share / 10 x 8")
    court.offices.warden = 311
    assert(math.floor(demand.motive(F, "legion"))
           == math.floor((share / 10 - 1) * 8), "a held office was not counted")
    court.offices.muster, court.offices.banners = 311, 311
    court.govs.prov_a, court.govs.prov_b = 311, 311
    assert(demand.motive(F, "legion") == 0,
           "a party holding more than its share has a motive below zero")
    cm.get_human_factions = function() return {} end
end)

check("a party with no free man demands nothing", function()
    party_court({legion = 50}, {demand = true})
    IC.court(F).govs.prov_a = 311     -- legion's only man already holds a post
    assert(IC.demand_target(F, "legion") == nil,
           "a demand named a man who already holds a post")
    cm.get_human_factions = function() return {} end
end)

check("a mission the engine refuses leaves no demand behind", function()
    party_court({legion = 50}, {demand = true})
    local real = cm.trigger_custom_mission_from_string
    cm.trigger_custom_mission_from_string = function() error("parse error", 0) end
    IC.party_turn(F)
    cm.trigger_custom_mission_from_string = real
    assert(IC.agenda(F).demand == nil,
           "a demand the engine never issued is on the books")
    assert(cards_of("party_demand") == 0, "a card for a demand nobody issued")
    cm.get_human_factions = function() return {} end
end)
```

- [ ] **Step 2: Run and see it fail**

Expected: `FAIL a party in the demand band asks for the office it claims: no party act demand`,
raised by `act_named`, or the `== "demand"` assertion, depending on order.

- [ ] **Step 3: Implement**

In the parties file, after the end of `IC.governor_xp` and before `function IC.party_turn`, add:

```lua
-- DEMANDS. One live demand court-wide, issued as a real mission so the player
-- sees it in the objectives panel. The mission's text is loc and cannot name
-- anyone; the party card's tooltip names the man and the post.
IC.DEMAND_KEYS = {office = "derpy_ic_demand_office",
                  gov = "derpy_ic_demand_province"}
IC.DEMAND_SCRIPT_KEY = "derpy_ic_demand"
IC.DEMAND_REWARD = "derpy_ic_demand_reward"

-- This party's men who hold no post, richest first.
local function free_men(faction_key, slug)
    local out = {}
    for _, cand in ipairs(IC.candidates(faction_key)) do
        if cand.slug == slug and not cand.busy then out[#out + 1] = cand.cqi end
    end
    table.sort(out, function(x, y)
        local sx, sy = IC.standing(faction_key, x), IC.standing(faction_key, y)
        if sx ~= sy then return sx > sy end
        return x < y
    end)
    return out
end

-- A vacant office one of its free men can take now, the offices it claims
-- first; else a province with no overseer or a Crown one.
function IC.demand_target(faction_key, slug)
    local men = free_men(faction_key, slug)
    if #men == 0 then return nil end
    local court = IC.court(faction_key)
    local claimed, other = {}, {}
    for i = 1, #IC.OFFICES do
        local office = IC.OFFICES[i]
        if not court.offices[office.slug] then
            local list = office.affinity == slug and claimed or other
            list[#list + 1] = office.slug
        end
    end
    for _, list in ipairs({claimed, other}) do
        for _, office_slug in ipairs(list) do
            for _, cqi in ipairs(men) do
                if IC.can_appoint(faction_key, office_slug, cqi) then
                    return {kind = "office", cqi = cqi, key = office_slug, was = 0}
                end
            end
        end
    end
    for _, province in ipairs(IC.seats(faction_key)) do
        local holder = court.govs[province]
        if not holder or IC.house_of_cqi(faction_key, holder) == IC.CROWN then
            return {kind = "gov", cqi = men[1], key = province, was = holder or 0}
        end
    end
    return nil
end

function IC.demand_string(kind)
    local key = IC.DEMAND_KEYS[kind]
    return "mission{key " .. key .. ";issuer CLAN_ELDERS;turn_limit "
        .. T.party_demand_turns .. ";primary_objectives_and_payload{"
        .. "objective{type SCRIPTED;script_key " .. IC.DEMAND_SCRIPT_KEY
        .. ";override_text mission_text_text_" .. key .. ";}"
        .. "payload{text_display " .. IC.DEMAND_REWARD .. ";}}}"
end

function IC.issue_demand(faction_key, slug, t)
    local a = IC.agenda(faction_key)
    a.demand = {slug = slug, kind = t.kind, cqi = t.cqi, key = t.key,
                was = t.was or 0,
                ends = cm:model():turn_number() + T.party_demand_turns}
    -- Saved before the engine call: a mission can raise its own events from
    -- inside the call that creates it.
    IC.save_agenda(faction_key)
    local ok, err = pcall(function()
        cm:trigger_custom_mission_from_string(faction_key,
                                              IC.demand_string(t.kind))
    end)
    if not ok then
        a.demand = nil
        IC.save_agenda(faction_key)
        IC.say("IRON COURT: demand not issued in " .. faction_key .. ": "
               .. tostring(err))
        return false
    end
    IC.log(faction_key, "demand", slug, t.key, 0)
    IC.feed(faction_key, "party_demand")
    IC.say("IRON COURT: " .. slug .. " demands " .. t.kind .. " " .. t.key
           .. " for cqi " .. tostring(t.cqi) .. " in " .. faction_key)
    return true
end

IC.PARTY_ACTS[#IC.PARTY_ACTS + 1] = {
    key = "demand",
    can = function(faction_key, slug)
        local house = IC.court(faction_key).houses[slug]
        if not house then return nil end
        local loyalty = house.loyalty or 0
        if loyalty < T.party_demand_low or loyalty > T.party_demand_high then
            return nil
        end
        if IC.agenda(faction_key).demand then return nil end
        return IC.demand_target(faction_key, slug)
    end,
    motive = function(faction_key, slug, _t)
        local held = #IC.offices_of_house(faction_key, slug)
                     + #IC.provinces_of_house(faction_key, slug)
        return math.max(0, IC.share(faction_key, slug) / 10 - held) * 8
    end,
    act = function(faction_key, slug, t) IC.issue_demand(faction_key, slug, t) end,
}
```

Also change the file's header comment line
`-- panel. Defines functions only: nothing here may touch the campaign at load.` to
`-- panel. Defines functions and three mission listeners; nothing here may touch the campaign at load.`

- [ ] **Step 4: The DB rows**

In `tools/gen_iron_court.py`:

1. **Add after `EVENTS`:**
   ```python
   # THE DEMAND MISSIONS. Issued from Lua as a mission string (IC.demand_string);
   # the string route still needs a missions row per key. Field for field the
   # Great Guilds bounty row, except: SCRIPTED because the string supplies the
   # objective, a real picture (chd/generic is not one), and no manual cancel -
   # a cancel is a void, and a void costs nothing, so it would be a free refusal.
   DEMAND_REWARD = "derpy_ic_demand_reward"
   DEMAND_REWARD_TEXT = "The party's loyalty rises."
   DEMANDS = [
       ("derpy_ic_demand_office", "A Party Demands an Office",
        "One of the court's parties wants one of its men seated in a vacant "
        "office. Their party card names the man and the office. Seat him before "
        "the time runs out and their loyalty rises; let it run out, or give the "
        "office to someone else, and it falls.",
        "The office is filled as they asked, and the party is satisfied.",
        "Seat the party's man in the office they named (see their party card)."),
       ("derpy_ic_demand_province", "A Party Demands a Province",
        "One of the court's parties wants one of its men made overseer of a "
        "province. Their party card names the man and the province. Appoint him "
        "before the time runs out and their loyalty rises; let it run out, or "
        "give the province to someone else, and it falls.",
        "The province has the overseer they asked for, and the party is satisfied.",
        "Make the party's man overseer of the province they named (see their "
        "party card)."),
   ]
   ```
2. **In `build()`, just before the `return {...}`, add:**
   ```python
       missions = []
       for key, title, desc, done, objective in DEMANDS:
           missions.append({
               "key": key, "mission_type": "SCRIPTED",
               "localised_title": title, "localised_description": desc,
               "ui_image": "chd/diplomacy", "ui_icon": "rom_event_mission.png",
               "generate": "false", "prioritised": "false",
               "event_category": "Quest", "set_piece_battle": "",
               "location_x": "0", "location_y": "0",
               "quest_mission": "false", "quest_mission_final": "false",
               "trigger_radius": "0.0000", "quest_character": "",
               "sticky_by_default": "false",
               "localised_mission_completed_text": done,
               "can_be_manually_cancelled": "false",
           })
           for field, text in (("title", title), ("description", desc),
                               ("mission_completed_text", done)):
               loc.append({"key": "missions_localised_%s_%s" % (field, key),
                           "text": text, "tooltip": "false"})
           loc.append({"key": "mission_text_text_" + key, "text": objective,
                       "tooltip": "false"})
       payload_ui = [{"component": DEMAND_REWARD,
                      "icon": "ui/skins/default/icon_check.png",
                      "state": "positive", "sort_order": "0"}]
       loc.append({"key": "campaign_payload_ui_details_description_" + DEMAND_REWARD,
                   "text": DEMAND_REWARD_TEXT, "tooltip": "false"})
   ```
3. **In the returned dict, before `"loc": loc`, add:**
   ```python
               "missions": missions,
               "campaign_payload_ui_details": payload_ui,
   ```
4. **In `TSV_META`, before `"loc": ("Loc", 1),`, add:**
   ```python
       # Versions pinned against CA's own shipped files by check_demand_keys().
       # missions declared 6 once and crashed the game at load (docs/MISSIONS.md).
       "missions": ("missions_tables", 0),
       "campaign_payload_ui_details": ("campaign_payload_ui_details_tables", 2),
   ```
5. **Add after `check_factions()`:**
   ```python
   def check_demand_keys():
       """The Lua and the DB must name the same missions, and the tables must be
       the versions CA's own files declare. A key is an unvalidated string: a
       mismatch issues a mission with no row, which fails in silence."""
       out = []
       root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
       lua = io.open(os.path.join(root, "Modding Files", "pack", "script",
                                  "campaign", "mod",
                                  "zzz_derpy_iron_court_parties.lua"),
                     encoding="utf-8").read()
       for key in [d[0] for d in DEMANDS] + [DEMAND_REWARD, "derpy_ic_demand"]:
           if '"%s"' % key not in lua:
               out.append("the parties Lua never names %s" % key)
       import read_vanilla_cache as R
       for table in ("missions", "campaign_payload_ui_details"):
           if not R.have(table):
               out.append("%s not cached - run tools/fetch_vanilla_tables.py %s"
                          % (table, table))
           elif R.version(table) != TSV_META[table][1]:
               out.append("%s is version %d in CA's files, TSV_META says %d"
                          % (table, R.version(table), TSV_META[table][1]))
           else:
               _rows, fields = R.load(table)
               built = build()[table][0]
               if list(built.keys()) != fields:
                   out.append("%s columns %s differ from CA's %s"
                              % (table, list(built.keys()), fields))
       return out
   ```
   Then in `check()`, after `out.extend(check_factions())`, add
   `out.extend(check_demand_keys())`.
   - If `import read_vanilla_cache` fails because `tools/` is not on `sys.path`, use the same
     import the file already uses for the vanilla cache. `_cache_table` shows how.

- [ ] **Step 5: Run everything**

Run:
```powershell
& "C:\Program Files (x86)\Lua\5.1\luac.exe" -p "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court_parties.lua"
& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua
py tools\gen_iron_court.py --selftest
py tools\gen_iron_court.py
py tools\import_iron_court.py
```

Expected:
- the harness is green;
- `gen_iron_court.py` reports **605 loc rows** (596 + 8 mission lines + 1 reward line), and
  writes `missions.tsv` and `campaign_payload_ui_details.tsv`;
- `import_iron_court.py` prints `verify ok` and lists both new tables. This is its dry run, and
  it opens no pack.

---

### Task 3: Demands - settling them

**Files:**
- Modify: the parties file (after Task 2's section; `IC.party_turn`)
- Test: `tools/_iron_court_harness.lua`

**Interfaces:**
- Consumes: Task 2's `IC.DEMAND_KEYS` and `IC.DEMAND_SCRIPT_KEY`; `IC.move_loyalty`;
  `IC.appoint`; `IC.assign_governor`; `IC.release_governor`; `IC.remove_house`.
- Produces:
  - `IC.demand_state(fk, d)`, which returns `"met"`, `"refused"`, `"void"` or nil;
  - `IC.settle_demand(fk, outcome, ended)`, which returns a boolean;
  - `IC.check_demand(fk)`, which returns the outcome or nil;
  - the listeners `ic_demand_succeeded`, `ic_demand_failed` and `ic_demand_cancelled`.

- [ ] **Step 1: Write the failing checks**

```lua
local function legion_demand(kind, key, was)
    party_court({legion = 50, forge = 90}, {demand = true})
    missions_issued, missions_closed = {}, {}
    IC.agenda(F).demand = {slug = "legion", kind = kind, cqi = 311, key = key,
                           was = was or 0, ends = 15}
    return IC.court(F).houses["legion"]
end

local function mission_event(key)
    return {
        faction = function() return {name = function() return F end} end,
        mission = function()
            return {mission_record_key = function() return key end}
        end,
    }
end

check("a met demand raises the party's loyalty and completes the mission", function()
    local house = legion_demand("office", "warden")
    assert(IC.appoint(F, "warden", 311), "the fixture could not seat him")
    local before = house.loyalty
    turn = 11
    assert(IC.check_demand(F) == "met", "the seated man did not meet the demand")
    assert(house.loyalty == before + IC.TUNE.party_demand_met,
           "loyalty went " .. before .. " -> " .. house.loyalty)
    assert(IC.agenda(F).demand == nil, "a met demand is still live")
    local closed = missions_closed[#missions_closed]
    assert(closed and closed.key == "derpy_ic_demand_office"
           and closed.script == "derpy_ic_demand" and closed.ok == true,
           "the mission was not completed")
    cm.get_human_factions = function() return {} end
end)

check("an office given to another man refuses the demand", function()
    local house = legion_demand("office", "warden")
    assert(IC.appoint(F, "warden", 301), "the fixture could not seat the Crown's man")
    local before = house.loyalty
    assert(IC.check_demand(F) == "refused", "the seat went elsewhere and nothing happened")
    assert(house.loyalty == before - IC.TUNE.party_demand_refused,
           "loyalty went " .. before .. " -> " .. house.loyalty)
    assert(cards_of("party_demand_refused") == 1, "no refusal card")
    local closed = missions_closed[#missions_closed]
    assert(closed and closed.ok == false, "the mission was not failed")
    cm.get_human_factions = function() return {} end
end)

check("a demand nobody answers is refused when its turns run out", function()
    local house = legion_demand("office", "warden")
    turn = 14
    assert(IC.check_demand(F) == nil, "a demand ran out a turn early")
    turn = 15
    local before = house.loyalty
    assert(IC.check_demand(F) == "refused", "a demand outlived its turns")
    assert(house.loyalty == before - IC.TUNE.party_demand_refused,
           "running out cost nothing")
    cm.get_human_factions = function() return {} end
end)

check("a province the Crown's man holds waits for the player", function()
    legion_demand("gov", "prov_a", 301)
    IC.court(F).govs.prov_a = 301
    assert(IC.check_demand(F) == nil, "the Crown's own overseer refused the demand")
    IC.release_governor(F, "prov_a")
    assert(IC.check_demand(F) == nil, "an empty province refused the demand")
    IC.assign_governor(F, "prov_a", 311)
    assert(IC.check_demand(F) == "met", "the named man governing did not meet it")
    cm.get_human_factions = function() return {} end
end)

check("a province given to another man refuses the demand", function()
    legion_demand("gov", "prov_a", 0)
    IC.assign_governor(F, "prov_a", 302)
    assert(IC.check_demand(F) == "refused", "another overseer did not refuse it")
    cm.get_human_factions = function() return {} end
end)

check("a dead man or a departed party voids the demand, at no cost", function()
    local house = legion_demand("office", "warden")
    local before = house.loyalty
    cm:kill_character("cqi:311", false)
    assert(IC.check_demand(F) == "void", "a dead man's demand did not void")
    assert(house.loyalty == before, "a void demand moved loyalty")
    local closed = missions_closed[#missions_closed]
    assert(closed and closed.cancelled, "the mission was not cancelled")
    legion_demand("office", "warden")
    IC.remove_house(F, "legion")
    assert(IC.check_demand(F) == "void", "a departed party's demand did not void")
    cm.get_human_factions = function() return {} end
end)

check("the engine failing the mission refuses the demand once", function()
    local house = legion_demand("office", "warden")
    local before = house.loyalty
    core.listeners["ic_demand_failed"](mission_event("derpy_ic_demand_office"))
    assert(house.loyalty == before - IC.TUNE.party_demand_refused,
           "the engine's failure cost nothing")
    assert(#missions_closed == 0, "a mission the engine ended was closed again")
    core.listeners["ic_demand_failed"](mission_event("derpy_ic_demand_office"))
    assert(house.loyalty == before - IC.TUNE.party_demand_refused,
           "one failure was charged twice")
    assert(cards_of("party_demand_refused") == 1, "two refusal cards")
    cm.get_human_factions = function() return {} end
end)

check("another mission's event leaves the demand alone", function()
    legion_demand("office", "warden")
    core.listeners["ic_demand_cancelled"](mission_event("derpy_gg_bounty_brass"))
    core.listeners["ic_demand_failed"](mission_event("derpy_ic_demand_province"))
    assert(IC.agenda(F).demand, "another mission's event settled the demand")
    cm.get_human_factions = function() return {} end
end)

check("the party turn settles a demand before it chooses", function()
    legion_demand("office", "warden")
    IC.appoint(F, "warden", 311)
    turn = 11
    IC.party_turn(F)
    assert(IC.agenda(F).demand == nil, "the party turn left a met demand live")
    cm.get_human_factions = function() return {} end
end)
```

- [ ] **Step 2: Run and see it fail**

Expected: `FAIL a met demand raises ...: attempt to call field 'check_demand' (a nil value)`.

- [ ] **Step 3: Implement**

After Task 2's `IC.PARTY_ACTS` demand entry, add:

```lua
-- Where a live demand stands: "met", "refused" or "void", or nil while it waits.
function IC.demand_state(faction_key, d)
    local court = IC.court(faction_key)
    if not court.houses[d.slug] then return "void" end
    if not IC.character_by_cqi(faction_key, d.cqi) then return "void" end
    local holder
    if d.kind == "office" then
        holder = court.offices[d.key]
    else
        holder = court.govs[d.key]
    end
    if holder == d.cqi then return "met" end
    if holder and holder ~= d.was then return "refused" end
    if cm:model():turn_number() >= d.ends then return "refused" end
    return nil
end

-- Idempotent: the record is cleared before anything else, so the mission
-- event the engine raises from inside the calls below finds nothing left to
-- settle. `ended` means the engine has already closed the mission.
function IC.settle_demand(faction_key, outcome, ended)
    local a = IC.agenda(faction_key)
    local d = a.demand
    if not d then return false end
    a.demand = nil
    IC.save_agenda(faction_key)
    local mission = IC.DEMAND_KEYS[d.kind]
    if outcome == "met" then
        IC.move_loyalty(faction_key, d.slug, T.party_demand_met)
        IC.log(faction_key, "demand_met", d.slug, d.key, 0)
    elseif outcome == "refused" then
        IC.move_loyalty(faction_key, d.slug, -T.party_demand_refused)
        IC.log(faction_key, "demand_refused", d.slug, d.key, 0)
        IC.feed(faction_key, "party_demand_refused")
    else
        IC.log(faction_key, "demand_void", d.slug, d.key, 0)
    end
    if not ended then
        pcall(function()
            if outcome == "void" then
                cm:cancel_custom_mission(faction_key, mission)
            else
                cm:complete_scripted_mission_objective(faction_key, mission,
                    IC.DEMAND_SCRIPT_KEY, outcome == "met")
            end
        end)
    end
    IC.say("IRON COURT: " .. d.slug .. "'s demand for " .. d.key .. " "
           .. outcome .. " in " .. faction_key)
    IC.save(faction_key)
    return true
end

-- Upkeep, not an event.
function IC.check_demand(faction_key)
    local d = IC.agenda(faction_key).demand
    if not d then return nil end
    local outcome = IC.demand_state(faction_key, d)
    if outcome then IC.settle_demand(faction_key, outcome) end
    return outcome
end

-- The engine's own word on a demand: a turn limit running out fails the
-- mission. Only a demand still open is settled here.
local function demand_event(outcome)
    return function(context)
        local faction_key, key
        pcall(function() faction_key = context:faction():name() end)
        pcall(function() key = context:mission():mission_record_key() end)
        if not faction_key or not key then return end
        if key ~= IC.DEMAND_KEYS.office and key ~= IC.DEMAND_KEYS.gov then
            return
        end
        local d = IC.agenda(faction_key).demand
        if d and IC.DEMAND_KEYS[d.kind] == key then
            IC.settle_demand(faction_key, outcome, true)
        end
    end
end

core:add_listener("ic_demand_succeeded", "MissionSucceeded", true,
                  demand_event("met"), true)
core:add_listener("ic_demand_failed", "MissionFailed", true,
                  demand_event("refused"), true)
core:add_listener("ic_demand_cancelled", "MissionCancelled", true,
                  demand_event("void"), true)
```

In `IC.party_turn`, after `    IC.end_feuds(faction_key)`, add `    IC.check_demand(faction_key)`.

- [ ] **Step 4: Run everything**

Run `luac -p` on the parties file, then the harness. Expected: green.

---

### Task 4: Offers

**Files:**
- Modify: the parties file (after Task 3's section; `IC.party_turn`)
- Test: `tools/_iron_court_harness.lua`

**Interfaces:**
- Consumes: `IC.office_rank(slug)`; `IC.tier_influence(tier)`; `IC.candidates`;
  `IC.present_houses`; `IC.move_loyalty`; `IC.add_standing`; `cm:treasury_mod`;
  `cm:grant_unit_to_character`.
- Produces:
  - `IC.PARTY_TROOPS`, `IC.TROOPS_DEFAULT` and `IC.troop_key(slug)`;
  - `IC.backing_target(fk)`, `IC.calm_target(fk, slug)` and `IC.troops_target(fk)`;
  - `IC.offer_options(fk, slug)`, which returns a list of `{kind, n, target}`;
  - `IC.can_accept_offer(fk, slug)`, which returns ok and a reason (`"no offer"`,
    `"lapsed"`, `"gone"` or `"room"`);
  - `IC.accept_offer(fk, slug)` and `IC.decline_offer(fk, slug)`, which return ok and a
    reason;
  - `IC.expire_offers(fk)`;
  - the `offer` entry in `IC.PARTY_ACTS`.

**Fixture numbers**, from `party_court`:
- the shares are Crown 19.19, legion 30.30 and forge 50.51;
- Crown man 301 holds 800 influence and 302 holds 100;
- every man is rank 30;
- nobody has an army unless a check sets `_force = true` on him (`men[1]` is 301);
- `rng(nil)` makes every `cm:random_number` return its minimum.

- [ ] **Step 1: Write the failing checks**

```lua
check("a loyal party offers what the court has room for", function()
    local _f, men = party_court({legion = 60, forge = 90}, {offer = true})
    local function kinds()
        local out = {}
        for _, o in ipairs(IC.offer_options(F, "forge")) do out[#out + 1] = o.kind end
        return table.concat(out, ",")
    end
    local opts = IC.offer_options(F, "forge")
    assert(kinds() == "gold,backing", "forge could offer " .. kinds())
    assert(opts[1].n == math.floor(IC.share(F, "forge")
                                   * IC.TUNE.party_offer_gold_per_share),
           "the gold is not share x " .. IC.TUNE.party_offer_gold_per_share)
    -- 302 holds 100 influence: 100 short of the tier-3 bar, and past its rank.
    assert(opts[2].target == 302, "the backing went to " .. tostring(opts[2].target))
    IC.court(F).houses["legion"].clock = 3
    men[1]._force, men[1]._units = true, {}
    assert(kinds() == "gold,backing,calm,troops", "forge could offer " .. kinds())
    cm.get_human_factions = function() return {} end
end)

check("a loyal party's offer is the turn's event", function()
    party_court({legion = 60, forge = 90}, {offer = true})
    assert(IC.party_turn(F) == "offer", "no offer was made")
    local o = IC.agenda(F).offers.forge
    assert(o and o.kind == "gold"
           and o.ends == 10 + IC.TUNE.party_offer_turns, "not forge's gold offer")
    assert(cards_of("party_offer") == 1, "no offer card")
    cm.get_human_factions = function() return {} end
end)

check("offers come only at the line, one per party", function()
    party_court({}, {offer = true})
    local offer = act_named("offer")
    local house = IC.court(F).houses["forge"]
    house.loyalty = 74
    assert(offer.can(F, "forge") == nil, "an offer below the line")
    house.loyalty = 75
    assert(offer.can(F, "forge") ~= nil, "no offer at the line")
    assert(math.floor(offer.motive(F, "forge"))
           == math.floor(1 + IC.share(F, "forge") / 5),
           "the motive is not (loyalty - 74) + share / 5")
    IC.agenda(F).offers.forge = {kind = "gold", n = 1, ends = 13}
    assert(offer.can(F, "forge") == nil, "a second offer from one party")
    cm.get_human_factions = function() return {} end
end)

check("accepting gold pays it, and every other party resents it", function()
    local f = party_court({legion = 60, forge = 90}, {offer = true})
    f._gold = 0
    treasury_calls = {}
    IC.agenda(F).offers.forge = {kind = "gold", n = 3030, ends = 13}
    local crown = IC.court(F).houses[IC.CROWN].loyalty
    assert(IC.accept_offer(F, "forge"), "the offer was refused")
    assert(treasury_calls[1] and treasury_calls[1].amount == 3030,
           "the gold never arrived")
    assert(IC.court(F).houses["legion"].loyalty == 60 - IC.TUNE.party_offer_envy,
           "the other party did not resent it")
    assert(IC.court(F).houses["forge"].loyalty == 90, "the giver paid envy")
    assert(IC.court(F).houses[IC.CROWN].loyalty == crown, "the Crown envied itself")
    assert(IC.agenda(F).offers.forge == nil, "an accepted offer is still open")
    cm.get_human_factions = function() return {} end
end)

check("backing, calm and troops each deliver", function()
    local _f, men = party_court({legion = 20, forge = 90}, {offer = true})
    local court = IC.court(F)
    IC.agenda(F).offers.forge = {kind = "backing", n = 100, target = 302, ends = 13}
    assert(IC.accept_offer(F, "forge"))
    assert(court.standing[302] == 200, "the backing gave " .. court.standing[302])

    court.houses["legion"].clock = 3
    IC.agenda(F).offers.forge = {kind = "calm", n = 10, target = "legion", ends = 13}
    assert(IC.accept_offer(F, "forge"))
    assert(court.houses["legion"].clock == 0, "the countdown still runs")
    -- +10 calm, then the envy every other party pays.
    assert(court.houses["legion"].loyalty
           == 20 - IC.TUNE.party_offer_envy + 10 - IC.TUNE.party_offer_envy,
           "legion sits at " .. court.houses["legion"].loyalty)

    men[1]._force, men[1]._units = true, {}
    units_granted = {}
    IC.agenda(F).offers.forge = {kind = "troops", n = 2, target = 301, ends = 13}
    assert(IC.accept_offer(F, "forge"))
    assert(#units_granted == 2, #units_granted .. " units granted")
    for _, g in ipairs(units_granted) do
        assert(g.lookup == "cqi:301"
               and g.unit == "wh3_dlc23_chd_inf_chaos_dwarf_blunderbusses",
               "granted " .. g.unit .. " to " .. g.lookup)
    end
    cm.get_human_factions = function() return {} end
end)

check("an offer that no longer fits is refused, and says why", function()
    local _f, men = party_court({legion = 60, forge = 90}, {offer = true})
    local offers = IC.agenda(F).offers
    assert(select(2, IC.accept_offer(F, "forge")) == "no offer")
    offers.forge = {kind = "gold", n = 1, ends = 13}
    turn = 13
    assert(select(2, IC.accept_offer(F, "forge")) == "lapsed")
    turn = 10
    offers.forge = {kind = "calm", n = 10, target = "chain", ends = 13}
    assert(select(2, IC.accept_offer(F, "forge")) == "gone")
    men[1]._force = true
    men[1]._units = {}
    for i = 1, 19 do men[1]._units[i] = "wh3_dlc23_chd_inf_chaos_dwarf_warriors" end
    offers.forge = {kind = "troops", n = 2, target = 301, ends = 13}
    assert(select(2, IC.accept_offer(F, "forge")) == "room")
    assert(offers.forge, "a refused offer was thrown away")
    cm.get_human_factions = function() return {} end
end)

check("an offer lapses after its turns, and declining costs nothing", function()
    party_court({legion = 60, forge = 90}, {})
    local offers = IC.agenda(F).offers
    offers.forge = {kind = "gold", n = 1, ends = 13}
    turn = 12
    IC.party_turn(F)
    assert(offers.forge, "an offer lapsed a turn early")
    turn = 13
    IC.party_turn(F)
    assert(IC.agenda(F).offers.forge == nil, "an offer outlived its turns")
    assert(#shown == 0, "a lapsed offer raised a card")
    offers = IC.agenda(F).offers
    offers.forge = {kind = "gold", n = 1, ends = 20}
    assert(IC.decline_offer(F, "forge"))
    assert(offers.forge == nil, "a declined offer is still open")
    assert(IC.court(F).houses["legion"].loyalty == 60, "declining cost loyalty")
    offers.legion = {kind = "gold", n = 1, ends = 20}
    IC.remove_house(F, "legion")
    IC.party_turn(F)
    assert(IC.agenda(F).offers.legion == nil, "a departed party's offer stayed")
    cm.get_human_factions = function() return {} end
end)

check("with every act open, a turn still raises one event", function()
    party_court({legion = 40, forge = 90}, "all")
    IC.party_turn(F)
    assert(#shown == 1, #shown .. " cards in one turn")
    cm.get_human_factions = function() return {} end
end)
```

- [ ] **Step 2: Run and see it fail**

Expected: `FAIL a loyal party offers what the court has room for: attempt to call field 'offer_options' (a nil value)`.

- [ ] **Step 3: Implement**

After Task 3's listeners, add:

```lua
-- OFFERS. A loyal party gives the Crown something; the player takes it from
-- the party's favour list, and every other party resents it.
IC.PARTY_TROOPS = {
    temple = "wh3_dlc23_chd_inf_infernal_guard_fireglaives",
    forge  = "wh3_dlc23_chd_inf_chaos_dwarf_blunderbusses",
    chain  = "wh3_dlc23_chd_inf_hobgoblin_cutthroats",
    legion = "wh3_dlc23_chd_inf_infernal_guard",
    ledger = "wh3_dlc23_chd_inf_chaos_dwarf_warriors",
    tower  = "wh3_dlc23_chd_inf_chaos_dwarf_warriors_great_weapons",
    road   = "wh3_dlc23_chd_cav_hobgoblin_wolf_raiders_bows",
    hearth = "wh3_dlc23_chd_inf_chaos_dwarf_warriors",
}
-- A confederated house's slug is not one of the eight.
IC.TROOPS_DEFAULT = "wh3_dlc23_chd_inf_chaos_dwarf_warriors"
-- ponytail: the engine's army size, fixed at 20; read it if CA ever exposes it.
local ARMY_UNITS = 20

function IC.troop_key(slug)
    return IC.PARTY_TROOPS[slug] or IC.TROOPS_DEFAULT
end

-- The free Crown man nearest below a vacant office's influence bar, within
-- the backing of it and already past its rank bar.
function IC.backing_target(faction_key)
    local court = IC.court(faction_key)
    local best, best_gap
    for _, cand in ipairs(IC.candidates(faction_key)) do
        if cand.slug == IC.CROWN and not cand.busy then
            local has = IC.standing(faction_key, cand.cqi)
            for i = 1, #IC.OFFICES do
                local office = IC.OFFICES[i]
                local gap = IC.tier_influence(office.tier) - has
                if not court.offices[office.slug]
                        and cand.rank >= IC.office_rank(office.slug)
                        and gap > 0 and gap <= T.party_offer_backing
                        and (not best or gap < best_gap
                             or (gap == best_gap and cand.cqi < best)) then
                    best, best_gap = cand.cqi, gap
                end
            end
        end
    end
    return best
end

function IC.calm_target(faction_key, slug)
    local court = IC.court(faction_key)
    for _, other in ipairs(IC.present_houses(faction_key)) do
        local house = court.houses[other]
        if other ~= slug and other ~= IC.CROWN and house
                and (house.clock or 0) > 0 then
            return other
        end
    end
    return nil
end

local function army_units(man)
    local n
    pcall(function()
        local force = man:military_force()
        if not force:is_null_interface() and not force:is_armed_citizenry() then
            n = force:unit_list():num_items()
        end
    end)
    return n
end

function IC.troops_target(faction_key)
    local best
    for _, cand in ipairs(IC.candidates(faction_key)) do
        if cand.slug == IC.CROWN and cand.character then
            local n = army_units(cand.character)
            if n and n <= ARMY_UNITS - T.party_offer_units
                    and (not best or cand.cqi < best) then
                best = cand.cqi
            end
        end
    end
    return best
end

-- Everything this party could offer now, gold first because it is always there.
function IC.offer_options(faction_key, slug)
    local out = {{kind = "gold", n = math.floor(IC.share(faction_key, slug)
                                                * T.party_offer_gold_per_share)}}
    local man = IC.backing_target(faction_key)
    if man then
        out[#out + 1] = {kind = "backing", n = T.party_offer_backing, target = man}
    end
    local calm = IC.calm_target(faction_key, slug)
    if calm then
        out[#out + 1] = {kind = "calm", n = T.party_offer_calm, target = calm}
    end
    local lord = IC.troops_target(faction_key)
    if lord then
        out[#out + 1] = {kind = "troops", n = T.party_offer_units, target = lord}
    end
    return out
end

IC.PARTY_ACTS[#IC.PARTY_ACTS + 1] = {
    key = "offer",
    can = function(faction_key, slug)
        local house = IC.court(faction_key).houses[slug]
        if not house or (house.loyalty or 0) < T.party_offer_line then
            return nil
        end
        if IC.agenda(faction_key).offers[slug] then return nil end
        return IC.offer_options(faction_key, slug)
    end,
    motive = function(faction_key, slug, _t)
        return (IC.court(faction_key).houses[slug].loyalty
                - (T.party_offer_line - 1))
               + IC.share(faction_key, slug) / 5
    end,
    act = function(faction_key, slug, options)
        local pick = options[cm:random_number(#options, 1)] or options[1]
        IC.agenda(faction_key).offers[slug] = {
            kind = pick.kind, n = pick.n, target = pick.target,
            ends = cm:model():turn_number() + T.party_offer_turns}
        IC.log(faction_key, "offer", slug, pick.kind, pick.n)
        IC.feed(faction_key, "party_offer")
    end,
}

-- Returns ok, why. The codes are the panel's to turn into sentences.
function IC.can_accept_offer(faction_key, slug)
    local o = IC.agenda(faction_key).offers[slug or ""]
    if not o then return false, "no offer" end
    if cm:model():turn_number() >= o.ends then return false, "lapsed" end
    local court = IC.court(faction_key)
    if not court.houses[slug] then return false, "gone" end
    if o.kind == "backing" then
        if not IC.character_by_cqi(faction_key, tonumber(o.target)) then
            return false, "gone"
        end
    elseif o.kind == "calm" then
        if not court.houses[o.target or ""] then return false, "gone" end
    elseif o.kind == "troops" then
        local lord = IC.character_by_cqi(faction_key, tonumber(o.target))
        local n = lord and army_units(lord)
        if not n then return false, "gone" end
        if n > ARMY_UNITS - o.n then return false, "room" end
    end
    return true
end

function IC.accept_offer(faction_key, slug)
    local ok, why = IC.can_accept_offer(faction_key, slug)
    if not ok then return false, why end
    local a = IC.agenda(faction_key)
    local o = a.offers[slug]
    a.offers[slug] = nil
    local court = IC.court(faction_key)
    if o.kind == "gold" then
        cm:treasury_mod(faction_key, o.n)
    elseif o.kind == "backing" then
        IC.add_standing(faction_key, tonumber(o.target), o.n)
    elseif o.kind == "calm" then
        court.houses[o.target].clock = 0
        IC.move_loyalty(faction_key, o.target, o.n)
    elseif o.kind == "troops" then
        local lord = IC.character_by_cqi(faction_key, tonumber(o.target))
        local lookup = cm:char_lookup_str(lord)
        for _ = 1, o.n do
            cm:grant_unit_to_character(lookup, IC.troop_key(slug))
        end
    end
    for _, other in ipairs(IC.present_houses(faction_key)) do
        if other ~= slug and other ~= IC.CROWN then
            IC.move_loyalty(faction_key, other, -T.party_offer_envy)
        end
    end
    IC.log(faction_key, "offer_taken", slug, o.kind, o.n)
    IC.save_agenda(faction_key)
    IC.save(faction_key)
    return true
end

function IC.decline_offer(faction_key, slug)
    local a = IC.agenda(faction_key)
    if not a.offers[slug or ""] then return false, "no offer" end
    a.offers[slug] = nil
    IC.save_agenda(faction_key)
    return true
end

-- Upkeep, not an event: offers past their turns, or from a party that left.
function IC.expire_offers(faction_key)
    local a = IC.agenda(faction_key)
    local court = IC.court(faction_key)
    local now = cm:model():turn_number()
    local gone = 0
    for slug, o in pairs(a.offers) do
        if now >= o.ends or not court.houses[slug] then
            a.offers[slug] = nil
            gone = gone + 1
        end
    end
    return gone
end
```

In `IC.party_turn`, after Task 3's `    IC.check_demand(faction_key)`, add
`    IC.expire_offers(faction_key)`.

- [ ] **Step 4: Run everything**

Run `luac -p` on the parties file, then the harness. Expected: green.

---

### Task 5: The panel

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua`:
  - `ICUI.card_mood` and `ICUI.agenda_tip` (near line 1245);
  - `ICUI.draw_intrigue` (near line 3699);
  - `ICUI.reason_text` (near line 3843);
  - `ICUI.draw_favours` (near line 3907);
  - `ICUI.on_pick_click` (near line 4285).
- Modify: `tools/gen_ic_ui.py:4136`
- Test: `tools/_iron_court_harness.lua`

**Interfaces:**
- Consumes: Task 3's `IC.agenda(fk).demand`; Task 4's `offers`, `IC.can_accept_offer`,
  `IC.accept_offer`, `IC.decline_offer` and `IC.troop_key`; the UI-file local `loc`;
  `ICUI.character_name`, `ICUI.office_name` and `ICUI.house_name`.
- Produces: `ICUI.plot_what(faction, p)`, `ICUI.offer_what(faction, slug, o)` and
  `ICUI.plot_alert(faction)`. Also the new mood words `DEMANDING` and `OFFERING`, and the
  favour-list row keys `"offer_accept"` and `"offer_decline"`.

- [ ] **Step 1: Write the failing checks**

Read `with_fake_panel` (harness near line 4896) and the check "choosing a favour sends it, and
a refusal keeps the list open" before writing these. They show how a drawn row's cells are read
(`panel.children[ICUI.ROW .. "_" .. i].children.ic_row_e.text`), how `plain()` strips markup,
and how a click is simulated through `ICUI.clicked_index`.

```lua
check("the card names a demand and an offer, a warned move first", function()
    party_court({legion = 50, forge = 90})
    local court = IC.court(F)
    local legion, forge = court.houses["legion"], court.houses["forge"]
    local a = IC.agenda(F)
    a.demand = {slug = "legion", kind = "office", cqi = 311, key = "warden",
                was = 0, ends = 15}
    a.offers.forge = {kind = "gold", n = 3030, ends = 13}
    assert(ICUI.card_mood(F, legion, "legion") == "DEMANDING")
    assert(ICUI.card_mood(F, forge, "forge") == "OFFERING")
    local rec = {a = "legion", b = "forge", cause = "equal", since = 10, ends = 20}
    a.feuds.legion, a.feuds.forge = rec, rec
    assert(ICUI.card_mood(F, legion, "legion") == "DEMANDING",
           "a feud hid the demand")
    assert(ICUI.card_mood(F, forge, "forge") == "FEUDING", "an offer hid the feud")
    a.plot = {slug = "legion", move = "unseat", actor = 311, target = 301,
              key = legion_office(), turn = 10}
    assert(ICUI.card_mood(F, legion, "legion") == "SCHEMING",
           "a demand hid a warned move")
    cm.get_human_factions = function() return {} end
end)

check("the tooltip names the demanded man and post, and every offer", function()
    party_court({legion = 50, forge = 90})
    local a = IC.agenda(F)
    a.demand = {slug = "legion", kind = "office", cqi = 311, key = "warden",
                was = 0, ends = 15}
    local tip = ICUI.agenda_tip(F, "legion")
    assert(string.find(tip, "as " .. ICUI.office_name("warden"), 1, true),
           "the office is not named: " .. tip)
    assert(string.find(tip, "5 turns left", 1, true), "no time left: " .. tip)
    a.demand = {slug = "legion", kind = "gov", cqi = 311, key = "prov_a",
                was = 0, ends = 11}
    tip = ICUI.agenda_tip(F, "legion")
    assert(string.find(tip, "overseer of", 1, true)
           and string.find(tip, "1 turn left", 1, true),
           "the province demand reads: " .. tip)
    local cases = {
        {o = {kind = "gold", n = 3030, ends = 13}, want = "3030 gold"},
        {o = {kind = "backing", n = 100, target = "302", ends = 13},
         want = ICUI.character_name(IC.character_by_cqi(F, 302))},
        {o = {kind = "calm", n = 10, target = "legion", ends = 13},
         want = ICUI.house_name("legion", F)},
        {o = {kind = "troops", n = 2, target = "301", ends = 13},
         want = ICUI.character_name(IC.character_by_cqi(F, 301))},
    }
    for _, case in ipairs(cases) do
        a.offers.forge = case.o
        tip = ICUI.agenda_tip(F, "forge")
        assert(string.find(tip, "OFFERS: ", 1, true)
               and string.find(tip, case.want, 1, true),
               "the " .. case.o.kind .. " offer reads: " .. tip)
    end
    cm.get_human_factions = function() return {} end
end)

check("the favour list puts an open offer first, and its buttons work", function()
    local f = party_court({legion = 60, forge = 90})
    f._gold = 0
    IC.agenda(F).offers.forge = {kind = "gold", n = 3030, ends = 13}
    with_fake_panel(function(panel)
        ICUI.pick = {kind = "favour", slug = "forge"}
        ICUI.scroll.pick = 0
        ICUI.refresh()
        local row1 = panel.children[ICUI.ROW .. "_1"]
        local row2 = panel.children[ICUI.ROW .. "_2"]
        assert(row1 and plain(row1.children.ic_row_e.text) == "ACCEPT",
               "row 1 is not the offer")
        assert(row2 and plain(row2.children.ic_row_e.text) == "DECLINE",
               "row 2 is not the refusal")
        assert(ICUI.pick_rows[1] == "offer_accept"
               and ICUI.pick_rows[2] == "offer_decline", "the rows are not wired")
    end)
    local saved_idx = ICUI.clicked_index
    ICUI.clicked_index = function() return 1 end
    ICUI.pick = {kind = "favour", slug = "forge"}
    ICUI.pick_rows = {"offer_accept"}
    ICUI.scroll.pick = 0
    assert(ICUI.on_pick_click({component = {}}, F), "the click was not handled")
    ICUI.clicked_index = saved_idx
    assert(IC.agenda(F).offers.forge == nil, "ACCEPT did not take the offer")
    assert(f._gold == 3030, "ACCEPT did not pay")
    ICUI.pick = nil
    cm.get_human_factions = function() return {} end
end)

check("the Intrigue alert names a warned move before any clock", function()
    party_court({legion = 20, forge = 90})
    IC.court(F).houses["forge"].clock = 2
    IC.agenda(F).plot = {slug = "legion", move = "unseat", actor = 311,
                         target = 301, key = legion_office(), turn = 10}
    local line = ICUI.plot_alert(F)
    assert(line and string.find(line, "next turn", 1, true)
           and string.find(line, ICUI.office_name(legion_office()), 1, true),
           "the alert reads: " .. tostring(line))
    with_fake_panel(function(panel)
        local warn = ICUI.draw_intrigue(panel, F, IC.court(F))
        assert(string.sub(warn, 1, #line) == line,
               "the warned move did not lead the alert: " .. warn)
    end)
    cm.get_human_factions = function() return {} end
end)
```

- [ ] **Step 2: Run and see it fail**

Expected: `FAIL the card names a demand and an offer, a warned move first`, because the card
still reads `RESTLESS`.

- [ ] **Step 3: Card words and tooltip**

Replace `ICUI.card_mood` and `ICUI.agenda_tip` whole, from
`-- A countdown outranks the agenda: SECEDES 3 is the number the player acts on.` through the
`end` of `ICUI.agenda_tip`, with:

```lua
-- A countdown outranks the agenda: SECEDES 3 is the number the player acts on.
-- Then the most urgent thing the party is doing: a move landing next turn, a
-- demand with a deadline, a feud, an offer.
function ICUI.card_mood(faction, house, slug)
    local word = ICUI.mood(house, slug)
    if slug == IC.CROWN or not IC.agenda or (house.clock or 0) > 0 then
        return word
    end
    local a = IC.agenda(faction)
    if a.plot and a.plot.slug == slug then return "SCHEMING" end
    if a.demand and a.demand.slug == slug then return "DEMANDING" end
    if a.feuds[slug] then return "FEUDING" end
    if a.offers[slug] then return "OFFERING" end
    return word
end

local function turns_left(n)
    return string.format("%d turn%s left", n, n == 1 and "" or "s")
end

-- What a warned move will do, with the victim named.
function ICUI.plot_what(faction, p)
    local man = IC.character_by_cqi(faction, p.target)
    local who = man and ICUI.character_name(man) or "one of your men"
    if p.move == "unseat" then
        return string.format("%s struck from his seat as %s", who,
                             ICUI.office_name(p.key))
    elseif p.move == "recall" then
        return string.format("%s recalled from %s", who,
                             loc("provinces_onscreen_" .. tostring(p.key),
                                 tostring(p.key)))
    end
    return string.format("an accident at the forge for %s", who)
end

-- What an offer gives, with the man, party or army named.
function ICUI.offer_what(faction, slug, o)
    if o.kind == "gold" then
        return string.format("%d gold", o.n)
    elseif o.kind == "backing" then
        local man = IC.character_by_cqi(faction, tonumber(o.target))
        return string.format("%d influence for %s", o.n,
                             man and ICUI.character_name(man) or "one of your men")
    elseif o.kind == "calm" then
        return string.format("to calm %s: their countdown stops and their "
            .. "loyalty rises by %d", ICUI.house_name(o.target, faction), o.n)
    end
    local lord = IC.character_by_cqi(faction, tonumber(o.target))
    return string.format("%d %s for %s's army", o.n,
        loc("land_units_onscreen_name_" .. IC.troop_key(slug), "warriors"),
        lord and ICUI.character_name(lord) or "one of your lords")
end

-- The event cards cannot name anyone; this tooltip is where names go. One
-- paragraph per thing the party is doing, most urgent first.
function ICUI.agenda_tip(faction, slug)
    if slug == IC.CROWN or not IC.agenda then return "" end
    local a = IC.agenda(faction)
    local now = cm:model():turn_number()
    local parts = {}
    local p = a.plot
    if p and p.slug == slug then
        local move = IC.party_move_by_key(p.move)
        local plotter = IC.character_by_cqi(faction, p.actor)
        parts[#parts + 1] = string.format("MOVING AGAINST YOU: %s, next turn. "
            .. "Raise their loyalty above %d, or deal with %s, to stop it.",
            ICUI.plot_what(faction, p), move and move.line or 0,
            plotter and ICUI.character_name(plotter) or "their plotter")
    end
    local d = a.demand
    if d and d.slug == slug then
        local man = IC.character_by_cqi(faction, d.cqi)
        local who = man and ICUI.character_name(man) or "their man"
        local what
        if d.kind == "office" then
            what = string.format("seat %s as %s", who, ICUI.office_name(d.key))
        else
            what = string.format("make %s overseer of %s", who,
                loc("provinces_onscreen_" .. tostring(d.key), tostring(d.key)))
        end
        parts[#parts + 1] = string.format("DEMANDS: %s, %s. Grant it and their "
            .. "loyalty rises by %d; refuse it, or let it run out, and it falls "
            .. "by %d.", what, turns_left(d.ends - now),
            IC.TUNE.party_demand_met, IC.TUNE.party_demand_refused)
    end
    local rec = a.feuds[slug]
    if rec then
        local enemy = rec.a == slug and rec.b or rec.a
        parts[#parts + 1] = string.format("FEUDING with %s (%s) until turn %d. "
            .. "While it lasts they strike at each other, not at you.",
            ICUI.house_name(enemy, faction),
            rec.cause == "seat" and "a stolen seat" or "rivals of equal size",
            rec.ends)
    end
    local o = a.offers[slug]
    if o then
        parts[#parts + 1] = string.format("OFFERS: %s, %s. Click here to accept "
            .. "or decline. Accepting costs %d loyalty with every other party.",
            ICUI.offer_what(faction, slug, o), turns_left(o.ends - now),
            IC.TUNE.party_offer_envy)
    end
    return table.concat(parts, "\n\n")
end

-- The warned move, for the Intrigue tab's one alert line.
function ICUI.plot_alert(faction)
    if not IC.agenda then return nil end
    local p = IC.agenda(faction).plot
    if not p then return nil end
    return string.format("%s moves against you next turn: %s.",
                         ICUI.house_name(p.slug, faction), ICUI.plot_what(faction, p))
end
```

- [ ] **Step 4: The Intrigue alert**

In `ICUI.draw_intrigue`, directly before `    ICUI.fill_rows(panel, {}, "intrigue")`, add:

```lua
    -- A WARNED MOVE LANDS NEXT TURN, sooner than any clock can run out, so it
    -- speaks first and the clocks join the count.
    local plot_line = ICUI.plot_alert(faction)
    if plot_line then
        if urgent then others = others + 1 end
        urgent = plot_line
    end
```

- [ ] **Step 5: The favour list, the click and the refusals**

In `ICUI.draw_favours`, directly before `    for i = 1, #IC.FAVOURS do`, add:

```lua
    -- AN OPEN OFFER FIRST: it is the one thing on this list the party gives.
    -- The first cell stays empty, because it is the price column and an offer
    -- costs the player nothing but envy.
    local offer = IC.agenda and IC.agenda(faction).offers[slug]
    if offer then
        local may, why = IC.can_accept_offer(faction, slug)
        local action = "ACCEPT"
        if not may then
            action = (why == "room" and "NO ROOM")
                     or (why == "lapsed" and "LAPSED") or "GONE"
        end
        lines[#lines + 1] = {"", string.format("They offer %s. Accepting costs "
            .. "%d loyalty with every other party.",
            ICUI.offer_what(faction, slug, offer), IC.TUNE.party_offer_envy),
            "", "", action}
        ICUI.pick_rows[#lines] = may and "offer_accept" or false
        lines[#lines + 1] = {"", "Turn the offer down. It costs nothing.",
                             "", "", "DECLINE"}
        ICUI.pick_rows[#lines] = "offer_decline"
    end
```

In `ICUI.on_pick_click`, replace

```lua
    elseif ICUI.pick.kind == "favour" then
        done, why, spare = IC.favour(faction, chosen, ICUI.pick.slug)
```

with

```lua
    elseif ICUI.pick.kind == "favour" then
        if chosen == "offer_accept" then
            done, why, spare = IC.accept_offer(faction, ICUI.pick.slug)
        elseif chosen == "offer_decline" then
            done, why, spare = IC.decline_offer(faction, ICUI.pick.slug)
        else
            done, why, spare = IC.favour(faction, chosen, ICUI.pick.slug)
        end
```

In `ICUI.reason_text`, directly before the final `    end` of the `elseif` chain (the line
after `return "No such office."`), add:

```lua
    elseif why == "no offer" then
        return "That offer is no longer open."
    elseif why == "lapsed" then
        return "That offer has lapsed."
    elseif why == "room" then
        return "That army has no room for more troops."
    elseif why == "gone" then
        return "The man or party that offer named is gone."
```

- [ ] **Step 6: Measure the new words**

In `tools/gen_ic_ui.py`, replace
`            "ic_party_mood": ["SECEDES 99", "PLOTTING", "RESTLESS", "LOYAL", "SCHEMING", "FEUDING"],`
with
`            "ic_party_mood": ["SECEDES 99", "PLOTTING", "RESTLESS", "LOYAL", "SCHEMING", "FEUDING", "DEMANDING", "OFFERING"],`

- [ ] **Step 7: Run everything**

```powershell
& "C:\Program Files (x86)\Lua\5.1\luac.exe" -p "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court_ui.lua"
& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua
py tools\gen_ic_ui.py --check
py tools\check_lua_api.py "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court_ui.lua"
```

Expected: the harness is green, and `gen_ic_ui.py --check` prints `ok: 7 files, 224 components`.

---

### Task 6: Mutants for every rule

**Files:**
- Modify: `tools/mutate_iron_court.py` (append to `MUTANTS` before its closing `]`)

The suite is 269 mutants today, with 0 unexplained.

Write one mutant for each rule below. Follow the file's existing style:
- `(name, target, anchor, replacement)`, where target is `M`, `P` or `U`;
- each anchor is a code line (never a comment) that matches exactly once in its target file;
- two mutants may share an anchor;
- the name is a short phrase naming the fault, like "a demand from a party below the band".

Each mutant must break exactly its named rule, and a check aimed at that rule must kill it.
One killed by an unrelated Lua error proves nothing. If disabling a condition with `if false then`
would cause an error or fall through to a later return, replace the `return` with `return nil`
instead, as Build 1's drop mutants do.

**Demands (parties file, P):**
1. the band's low edge (`loyalty < T.party_demand_low`) allowing 25;
2. the band's high edge allowing 75;
3. the one-live-demand guard removed;
4. claimed offices not preferred: the `claimed` list is searched after `other`;
5. a rival-held province allowed: the Crown-or-empty test removed;
6. a man who fails `IC.can_appoint` named anyway;
7. the posts held not subtracted in the motive;
8. the motive's clamp at 0 removed;
9. a failed mission call keeping the demand: `a.demand = nil` removed in the `not ok` branch;
10. no `party_demand` card when a demand is issued;
11. `demand_state` never met: the `holder == d.cqi` test disabled;
12. `demand_state` never refusing a post given elsewhere;
13. `demand_state` treating the Crown's own holder (`was`) as a refusal;
14. `demand_state` with no expiry;
15. a dead man's demand not voided;
16. a departed party's demand not voided;
17. no loyalty when a demand is met;
18. no loyalty lost when a demand is refused;
19. no card on a refusal;
20. an ended mission closed again: the `if not ended then` guard removed;
21. the listener settling any mission key: the key filter removed;
22. `IC.check_demand` not called in `IC.party_turn`.

**Offers (P):**
23. an offer below the line;
24. a second offer from one party;
25. the gold not scaled by share;
26. backing for a man past the bar, or further than the backing from it (the `gap > 0` or
    `gap <= T.party_offer_backing` half removed; one mutant for each half);
27. backing for a man below the office's rank bar;
28. calm with no countdown running;
29. troops to an army without room;
30. a lapsed offer accepted;
31. troops accepted into a full army;
32. gold not paid on accept;
33. backing not paid;
34. calm leaving the countdown running;
35. envy charged to the giver;
36. envy charged to the Crown;
37. no envy at all;
38. an accepted offer left open;
39. offers never lapsing: the `now >= o.ends` test disabled;
40. a departed party's offer kept;
41. `IC.expire_offers` not called in `IC.party_turn`.

**Panel (U):**
42. `DEMANDING` never shown;
43. `OFFERING` never shown;
44. a demand shown over a warned move (the two tests swapped);
45. the demand tooltip not naming the office;
46. the offer row wired as refused (`pick_rows` false) while it can be accepted;
47. ACCEPT routed to the favour instead of `IC.accept_offer`;
48. the warned move not leading the Intrigue alert.

- [ ] **Step 1: Append the mutants**
- [ ] **Step 2: Self-test, then the new mutants by name**

Run `py tools\mutate_iron_court.py --selftest`. Expected: every mutant anchored.

Then run the new mutants by a substring of their names, for example
`py tools\mutate_iron_court.py "demand" "offer" "envy" "backing" "calm" "troops" "DEMANDING" "OFFERING" "Intrigue alert"`.
Expected: all caught.

A survivor means a check is missing. Add one to the harness, among the Build 2 checks, that
fails under the mutant and passes on the real code. Never weaken, delete or re-aim a mutant, and
never change production Lua to kill one. If a survivor reveals a real bug, stop and report it.

- [ ] **Step 3: Full suite**

Run: `py tools\mutate_iron_court.py` with a long timeout.

Expected: `<N> mutants, 0 unexplained`, where N is 269 plus the ones added. Afterwards, run the
harness plain once, and byte-compare the three shipped Lua files with the pre-run snapshot. The
runner restores each mutation.

---

### Task 7: Measure the pace, run every gate

**Files:**
- Create (scratchpad, not shipped): `<scratchpad>/party_sim_b2.lua`

- [ ] **Step 1: The simulation**

Copy the harness to the scratchpad as `party_sim_b2.lua`. Append Build 1's player-shaped
60-turn runner: the code block in `docs/superpowers/plans/2026-09-23-iron-court-rival-party-ai-build1.md`,
Task 8 Step 1.

Make two changes to it:
- call `use_acts("all")` at the start of `sim`;
- report demands met, refused and void from the court log's `demand_met`, `demand_refused` and
  `demand_void` kinds.

Run three seeds, 0, 7 and 99, as Build 1 did.

The simulation fills no offices and answers no demand. Every demand therefore runs out, which is
the worst case. **Report, do not tune:**
- the quiet turns;
- the event mix;
- the demand outcomes;
- which parties are left at turn 60, and for any party lost, whether refused demands drove it
  out.

The pace is the author's call once they have played it.

- [ ] **Step 2: All gates**

```powershell
foreach ($f in "zzz_derpy_iron_court.lua","zzz_derpy_iron_court_ui.lua","zzz_derpy_iron_court_parties.lua") { & "C:\Program Files (x86)\Lua\5.1\luac.exe" -p "Modding Files\pack\script\campaign\mod\$f" }
& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua
py tools\check_lua_api.py "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court_parties.lua"
py tools\check_lua_undeclared.py
py tools\gen_iron_court.py --selftest
py tools\gen_iron_court.py
py tools\gen_ic_ui.py --check
py tools\preview_iron_court.py --check
py tools\import_iron_court.py
py tools\mutate_iron_court.py --selftest
```

Expected:
- every command exits 0;
- `check_lua_undeclared` with no arguments reports 0 across the folder;
- 605 loc rows;
- `import_iron_court.py` prints `verify ok`.

**Deploy and write-up are the controller's,** after the final whole-branch review. They follow
the same steps as Build 1:
1. the game closed and RPFM up;
2. the both-ways diff of the deployed Lua;
3. `py tools\gen_iron_court.py` then `py tools\deploy_iron_court.py`;
4. SHA-256 equal in both copies, the `used_mods.txt` tick, and a read-back that finds the
   `missions` and `campaign_payload_ui_details` tables;
5. handoff §5 and the SESSION_INDEX line.

---

## Self-review notes

**Spec coverage:**
- §3 demands: Tasks 2 and 3.
- §5 offers: Task 4.
- §5b events: Task 1.
- §7 agenda texts and ACCEPT/DECLINE: Task 5, with deviations 2 and 5.
- §8 knobs: Task 1.
- §9 testing: Tasks 1-7.
- §6 save fields 20-22: replaced by the agenda value (deviation 1).
- §9 bridge probes: the author's in-game check (deviation 6).

**Names are consistent across tasks:**
- `IC.DEMAND_KEYS`, `IC.DEMAND_SCRIPT_KEY`, `IC.DEMAND_REWARD`;
- `IC.demand_target`, `IC.demand_string`, `IC.issue_demand`, `IC.demand_state`,
  `IC.settle_demand`, `IC.check_demand`;
- `IC.PARTY_TROOPS`, `IC.TROOPS_DEFAULT`, `IC.troop_key`;
- `IC.backing_target`, `IC.calm_target`, `IC.troops_target`, `IC.offer_options`;
- `IC.can_accept_offer`, `IC.accept_offer`, `IC.decline_offer`, `IC.expire_offers`;
- `ICUI.plot_what`, `ICUI.offer_what`, `ICUI.plot_alert`;
- `"offer_accept"`, `"offer_decline"`.

**`IC.party_turn`'s final order:**
1. the `is_human` guard;
2. `IC.governor_xp`;
3. `IC.end_feuds`;
4. `IC.check_demand`;
5. `IC.expire_offers`;
6. a warned move lands or drops, and returns;
7. otherwise score, choose and act (intrigue, feud, feud_move, demand, offer);
8. save.

**The act filter.** Build 1's checks see only Build 1's acts, through `use_acts(BUILD1_ACTS)`.
They were written for a court where a party at the default loyalty of 55 does nothing, and at
55 every rival is now in the demand band. The interplay check
"with every act open, a turn still raises one event" runs `"all"`.
