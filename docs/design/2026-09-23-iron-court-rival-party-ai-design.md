# Iron Court - rival parties that act on their own (design)

**Date:** 2026-09-23
**Status:** design approved section by section in chat; awaiting the author's review of this file.
**Scope:** the **player's court only**. AI factions' courts do not run any of this: they cannot
answer a demand or counter a plot, the same reason pressure is player-only (`IC.tick_pressure`).

## 0. Why

Today a rival party is a loyalty score with rules. It never chooses anything. "PLOTTING" on a
party card is only the label for loyalty 25 or below. This adds a small brain that picks **at
most one court event a turn** out of four behaviours: intrigue against the player, demands,
feuds between parties and offers. It also adds passive experience for governors, requested
alongside, because rank is half of every office's bar.

## 1. Architecture

- **New file:** `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_parties.lua`.
  - Loads after the model (`zzz_derpy_iron_court.lua`; `.` sorts before `_`) and before the UI
    (`_parties` < `_ui`).
  - It extends `IC` and does not redefine any model function.
- **Hook:** `IC.turn` gains one line, `if IC.party_turn then IC.party_turn(faction_key) end`,
  after `IC.tick_pressure` and `IC.flush_feed` and before `IC.tick_secession`. A plot or demand
  this turn can then still save or break a party before its countdown moves.
- **Player only:** `IC.party_turn` returns at once when `not IC.is_human(faction_key)`.
- **The motive table:** `IC.PARTY_ACTS`, one entry per action. Each entry has three fields:
  - `can(fk, slug)` returns false or a target;
  - `motive(fk, slug, target)` returns a number;
  - `act(fk, slug, target)` performs the action.
- **Choosing the turn's event:** score every rival party (never `IC.CROWN`) against every entry.
  - Drop candidates below `IC.TUNE.party_act_floor`.
  - Choose among the top 3 by weighted `cm:random_number`.
  - If nothing clears the floor, the turn is quiet.
- **Who pays:** the acting man is the party's **richest man by influence** among those who
  `IC.may_speak`. Costs and odds are the player's own (`IC.plot_cost`, `plot_chance_*`,
  `plot_chance_per_10`, clamped by `plot_chance_min`/`plot_chance_max`).
- **Reused as they are:** `IC.add_standing`, `IC.move_loyalty`, `IC.dismiss`,
  `IC.release_governor`, `IC.feed`, `IC.log`, `IC.save`, `IC.share`, `IC.offices_of_house`,
  `IC.provinces_of_house`, `IC.party_lords`, `IC.character_by_cqi`, `IC.is_legend`.
- **Needs its own path:** the player-side move path (`IC.plot`) is **not** called for party
  moves.
  - `IC.may_plot_as` requires a Crown actor.
  - `IC.may_target` refuses a Crown target.
  - The party path uses the same numbers through `IC.party_move(fk, slug, move, target)`.

## 2. Intrigue against the player

- **Who can act:** a rival party at loyalty <= 55.
- **The motive:** `(56 - loyalty)`, plus 10 for each office it claims that a Crown man holds.
- **Targets:** always a Crown man.
  - Rumours and discredit go for the Crown man with most influence.
  - Unseating goes for the Crown holder of an office this party claims by affinity, else the
    Crown's highest-tier seat.
  - A recall goes for a Crown governor.
  - Murder goes for a non-legendary Crown man, never `IC.is_legend`.

| Loyalty | Move | Effect | Warned |
|---|---|---|---|
| <= 55 | rumour | target -`plot_rumour_damage` (120) influence | no |
| <= 55 | discredit | target -`plot_discredit_standing` (90); Crown weight -`plot_discredit_weight` (8), floor 1 | no |
| <= 25 | unseat | ONE Crown office, `IC.dismiss(fk, office, true)` | yes |
| <= 25 | recall | ONE Crown governor, `IC.release_governor` | yes |
| <= 10 | murder | `cm:kill_character`; existing death rules apply | yes |

- **The odds:** `plot_chance_<move> + floor((plotter - target) / 10) * plot_chance_per_10`,
  clamped. The influence is spent whether the move lands or fails.
- **A warned move:**
  - It is stored as `court.party_plot = {slug, move, actor, target, key}`, where `key` is the
    office or province. It lands at the **next** `IC.party_turn` and takes that turn's event
    slot.
  - A card fires at once and the target is marked on the panel.
  - **Dropped without effect** when:
    - the actor is dead;
    - the party has left the court;
    - the party's loyalty is now above the move's line;
    - the actor can no longer afford it;
    - the target is dead;
    - the target no longer holds that office or governs that province.
- **Failure:** the influence is spent, the "plot foiled" card fires, and it is recorded in the
  court record.
- **New events:** `party_plot_warn`, `party_plot_ok`, `party_plot_fail`.

## 3. Demands

- **Who can demand:** a rival party at loyalty 26-74.
- **The motive:** `(its share / 10) - (offices + provinces it holds)`, clamped at 0, times 8.
- **One demand live court-wide:** `court.demand = {slug, kind, cqi, key, until}`.
- **The kinds:**
  - **office:** a vacant office whose influence and rank bars one of the party's free men clears
    (`IC.can_appoint` true). Prefer the office the party claims.
  - **governorship:** a province whose post is free or held by a Crown man, and a free man of
    the party's to hold it.
- **As a mission:**
  - issued with `cm:trigger_custom_mission_from_string`, `issuer CLAN_ELDERS`, `turn_limit 5`;
  - one objective, `type SCRIPTED`, `script_key derpy_ic_demand`;
  - keys `derpy_ic_demand_office` and `derpy_ic_demand_province`;
  - this is the Great Guilds bounty template.
- **Checked each `IC.party_turn`,** before any new event is chosen:

| Outcome | Condition | Effect |
|---|---|---|
| met | the named man holds that office or governs that province | `cm:complete_scripted_mission_objective(..., true)`; party +`party_demand_met` (12) loyalty in the `MissionSucceeded` handler, on top of `loyalty_appointed` |
| refused | the deadline passes (the game fails it), or that office or province went to anyone else (`cm:complete_scripted_mission_objective(..., false)`) | the mission fails; party -`party_demand_refused` (10) in the `MissionFailed` handler; card `party_demand_refused` |
| void | the man dies or the party leaves the court | `cm:cancel_custom_mission`, no loyalty change |

- **Handlers:** `MissionSucceeded`, `MissionFailed` and `MissionCancelled` are matched on
  `context:mission():mission_record_key()` for the two keys, then clear `court.demand`. They are
  mission events, not dilemma choices, so
  [[wh3-dilemma-choice-listener-crashes-custom-dilemma]] does not apply.
- **Text is loc-keyed and cannot name the man or office.** The mission reads "The <party> demand
  an office" or "...a governorship". The specifics are drawn on the party card (section 7).
- **New events:** `party_demand`, `party_demand_refused`.
- **DB, from `tools/gen_iron_court.py`:**
  - 2 `missions` rows. Table version **0**, 19 columns, pinned with `read_vanilla_cache.version()`:
    declaring 6 crashed the game at load once (`docs/MISSIONS.md`).
  - Their loc, and `mission_text_text_derpy_ic_demand_*`.

## 3b. Governors earn experience

- **The amount:** each `IC.party_turn` start, every governor in `court.govs` gains
  `IC.TUNE.governor_xp` (750) raw points via `cm:add_agent_experience(lookup, 750)`.
- **The pace**, from CA's `character_xp_per_level` table (rank 5 = 5,200, 12 = 21,900,
  20 = 48,700, 30 = 88,450): from rank 1, rank 5 in about 7 turns, rank 12 in about 29, rank 20
  in about 65.
- **Scope:** player court only.
- **Unknown:** whether a **garrison commander** or a **lord in the recruitment pool** can gain
  experience.
  - The build includes a bridge probe: add experience to one of each and read `rank()` before and
    after.
  - If either refuses, those governors get `governor_income` again (a second 5 influence)
    instead, so the post still pays.

## 4. Feuds

- **What starts one:** either cause, at most one feud per party.
  - **A stolen seat:** a man of Party A holds an office Party B claims by affinity, with B in the
    court.
  - **Rivals of equal size:** two rival parties within 5 share points.
- **The motive:** 20 for a stolen seat, 12 for equals. A feud starting is that turn's event;
  card `party_feud`.
- **State:** per-party `feud_with`, `feud_until` (start + 10), `feud_since`.
- **During a feud,** the party's intrigue motive is aimed at its enemy and **never at the
  player**:
  - rumour or discredit against the enemy's richest man (discredit's weight loss falls on the
    enemy party);
  - murder at `plot_chance_murder / 4` (10%), only when the feud is at least 5 turns old and the
    target is not a legend.
- **What ends one:** the cause ends (the seat changes hands, or the shares are more than 10 apart
  for the equal cause), `feud_until` passes, or either party leaves. Card `party_feud_end`.
- **Player levers:** appointments, and the existing intrigue moves against either side. No new
  button.

## 5. Offers

- **Who offers:** a rival party at loyalty >= 75.
- **The motive:** `(loyalty - 74) + share / 5`.
- **Limits:** one open offer per party. It lasts 3 turns: `offer_kind`, `offer_n`, `offer_until`.
- **Accepting** costs 3 loyalty with every **other** rival party
  (`IC.TUNE.party_offer_envy`). Declining or letting it lapse costs nothing.

| Offer | Grant | Available when |
|---|---|---|
| gold | 60 x share gold, `cm:treasury_mod` | always |
| backing | +100 influence to the Crown man closest to (within 100 of) a vacant office's influence bar | such a man exists |
| calm | another party's `clock = 0`, +10 loyalty | a secession countdown is running |
| troops | 2 units to a Crown lord's army with >= 2 free slots, `cm:grant_unit_to_character` | such an army exists |

- **Troop keys by party** (present in this workspace's exported data; re-verify against
  `main_units` in the build):

| Party | Unit key |
|---|---|
| temple | `wh3_dlc23_chd_inf_infernal_guard_fireglaives` |
| forge | `wh3_dlc23_chd_inf_chaos_dwarf_blunderbusses` |
| chain | `wh3_dlc23_chd_inf_hobgoblin_cutthroats` |
| legion | `wh3_dlc23_chd_inf_infernal_guard` |
| ledger | `wh3_dlc23_chd_inf_chaos_dwarf_warriors` |
| tower | `wh3_dlc23_chd_inf_chaos_dwarf_warriors_great_weapons` |
| road | `wh3_dlc23_chd_cav_hobgoblin_wolf_raiders_bows` |
| hearth | `wh3_dlc23_chd_inf_chaos_dwarf_warriors` |

- **Troops need a bridge probe.** `grant_unit_to_character` is documented ("only created if
  there is room"), but it is unmeasured here. If it fails live, the troops entry is removed and
  the other three stay.
- **New event:** `party_offer`. Accepting is logged to the court record.

## 5b. Event cards

- **Nine new events,** appended to `IC.EVENTS` and to `tools/gen_iron_court.py`'s `EVENTS` in the
  same order: `party_plot_warn`, `party_plot_ok`, `party_plot_fail`, `party_demand`,
  `party_demand_refused`, `party_feud`, `party_feud_end`, `party_offer`, then one spare for a
  dropped warned plot, `party_plot_dropped`.
- **Indices 2612-2620.** The list is positional: `EVENT_INDEX_BASE` + position must equal the
  Lua index.
- **Held while the panel is open.** `IC.feed` raises at once unless the panel is open, and the
  queue flushes when the panel closes, so a card raised in `IC.party_turn` after `IC.flush_feed`
  is shown the same turn.

## 6. Save

- **Per-party fields** are appended after field 16 (`stored`):
  17 `feud_with` (party index, 0 = none), 18 `feud_until`, 19 `feud_since`, 20 `offer_kind`
  (index, 0 = none), 21 `offer_n`, 22 `offer_until`.
  - Party and offer indices, not strings, because the pack format is `%d`.
- **Court-level records** go in one new saved value, `derpy_ic_agenda_<faction>`, for
  `party_plot` and `demand`, so the court string's layout is untouched.
- **Old saves** load with every new field empty.

## 7. Panel

- **One agenda line per party card,** `ic_party_agenda`. It shows the most urgent of:
  - `MOVING AGAINST <man> - next turn`
  - `DEMANDS: seat <man> as <office> - N turns`
  - `DEMANDS: <province> for <man> - N turns`
  - `FEUD: <party>`
  - `OFFERS: <gold / backing for <man> / calm for <party> / 2 <unit>>`
- **ACCEPT and DECLINE** appear only with an offer.
- **The targeted Crown man** gets a marker on his roster row.
- **Generation:** all components come from `tools/gen_ic_ui.py`.
  - The longest agenda string is added to its text-fit fixtures.
  - `ic_party_agenda` goes into `CUT_CELLS` only if it cannot fit.
  - `tools/preview_iron_court.py` draws the hardest case.

## 8. New knobs (`IC.TUNE`)

`party_act_floor` (10), `party_demand_met` (12), `party_demand_refused` (10),
`party_demand_turns` (5), `party_feud_turns` (10), `party_feud_murder_age` (5),
`party_offer_turns` (3), `party_offer_envy` (3), `party_offer_gold_per_share` (60),
`party_offer_backing` (100), `party_offer_calm` (10), `governor_xp` (750).

## 9. Testing

- **Harness** (`tools/_iron_court_harness.lua` also loads the new file):
  - one check per rule: each move's loyalty line, the warned-move landing and each drop
    condition, a demand's three outcomes, feud start (both causes) and end (each condition), each
    offer's effect and the envy cost, governor experience, and the one-event-a-turn cap;
  - AI courts run none of it.
- **Mutants:** `tools/mutate_iron_court.py` gains a `P` target for the new file, with one mutant
  per rule. Every anchor goes on a code line.
- **Bridge probes**, one-shot, game running:
  - experience on a garrison commander and on a pool lord;
  - `grant_unit_to_character` on a Crown army;
  - a string-issued `derpy_ic_demand_office` renders and completes.
- **Simulation:** 60 turns on the player-shaped court (current harness plus an appended runner,
  as in 3g). It reports events per turn, the share of quiet turns, and the parties that survive.
  Target: roughly half the turns quiet, and no party lost only to party intrigue.
- **Gates:**
  - `luac -p`, `check_lua_api.py` and `check_lua_undeclared.py` on all three files;
  - `gen_iron_court.py --check`/`--selftest`, `gen_ic_ui.py --check`, `preview_iron_court.py --check`;
  - the both-ways diff against the deployed pack, then `deploy_iron_court.py` with the game
    closed.

## 10. Delivery

- **Build 1:** intrigue, feuds, governor experience, the agenda line (plot and feud texts only),
  save fields 17-19. No new DB rows.
- **Build 2:** demands (missions, handlers, DB rows and loc), offers (fields 20-22, the
  ACCEPT/DECLINE buttons), and the remaining agenda texts.

Each build is deployed and playable on its own.

## 11. Out of scope

- Parties acting in AI courts.
- Demands that name a rival to dismiss, and tribute demands (not chosen).
- A "back a side" button for feuds.
- Dynamic names inside mission or event-card text: the engine reads those as fixed loc keys.
