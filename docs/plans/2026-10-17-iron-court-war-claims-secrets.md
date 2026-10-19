# Iron Court War Council, Claims and Secrets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give both Iron Court races a war council (party-proposed war votes, a declaration after preparation turns, overrule for gold or influence, reactions to wars and peace the player makes), claims on newly conquered provinces, and secrets dug up by an Intrigue move and spent once.

**Architecture:** Everything is Lua in the four existing Iron Court files, no new script file. The council reuses the law vote engine under a new vote key `IC.COUNCIL = "council"`, with one helper, `IC.vote_stance`, deciding whether a man's line comes from a law's stances or from the war lines. A war line is the first of a party's ordered `{fact, side}` pairs whose fact holds for the target; the facts are read from CA's diplomacy API, with a per-turn snapshot for the reactions. Claims hang off the existing `GarrisonOccupiedEvent` listener and one hook in `IC.assign_governor`. Secrets are a new move in `IC.PLOTS` plus a picker of uses. New state lives in the court and saves as fields 21 to 23 of `IC.pack`; the council vote rides field 18 with the law votes.

**Tech Stack:** Lua 5.1.5 campaign scripts under `Modding Files/pack/script/campaign/mod/`, the Python generator `tools/gen_iron_court.py`, the UI generator `tools/gen_ic_ui.py`, the importer `tools/import_iron_court.py`, the Lua harness `tools/_iron_court_harness.lua` (run under `lua.exe`), `tools/mutate_iron_court.py`, `tools/preview_iron_court.py`, `tools/check_ic_release.py`, `tools/deploy_iron_court.py` (needs RPFM open and the game shut).

**Spec:** `docs/superpowers/specs/2026-10-17-iron-court-war-claims-secrets-design.md`. Read it first; this plan cites its section numbers and does not repeat its tables.

## Global Constraints

- The workspace is not a git repository. Every "commit" step is a ledger line appended to `docs/superpowers/plans/2026-10-17-iron-court-war-claims-secrets.ledger.md`; Task 0's backups stand in for history.
- Lua 5.1.5. A number literal is never on the LEFT of an arithmetic operator (`x * 2`, never `2 * x`); `tools/check_lua_literal_left.py` finds it. Integer arithmetic only in saves and tallies (`math.floor`).
- `cm:random_number(max, min)` is the only random source. Any loop over `pairs()` whose order reaches the model is sorted first, so every multiplayer machine agrees.
- Every `IC.X = {` and `DWF.X = {` table closes with `}` at column 0 (the generator and importer read them with `^PREFIX\.NAME = \{(.*?)\n\}`). A race table is read through `R = IC.R(faction_key)`, never `IC.X`, outside its column-0 definition.
- Loyalty moves only through `IC.move_loyalty` (the importer's single-writer gate). The panel changes the campaign only through `ICUI.send` and `IC.mp_receive` (the importer's routing gate).
- Every API member used is in CA's 9.0 docs; check with `py tools/check_lua_api.py --explain <member>` before writing it. A harness stub may only add a documented member to `make_faction` or `make_character` (importer gate 0b).
- Keys fail silently: every subculture, faction, event and loc key used was read from CA's files or the generator, never typed from memory. The `R.WAR_FOES` keys in spec 2.2 are verified.
- Player text: plain words; never cap, caps, accrue, rep, AI, HUD or standing (`JARGON`); Dwarf text never carries a Chaos Dwarf word or "guild" (`CHD_WORDS`, `check_dwf`). No emojis, no em or en dashes anywhere. Never the ladder word for a step; use tier, level, step or band.
- Binary files are never edited as text. The importer and deployer are the only way into the pack.
- Back up to `Modding Files/Backup/`, never `data/` or a Workshop folder. The Iron Court is hosted in `data/`: deploy there when the game is shut. GitHub sync and any Workshop upload are NOT part of this plan; they wait for the author.
- Files are LF. `docs/SESSION_INDEX.md` is CRLF; edit it with a script that keeps CRLF. `sed -i` strips CRLF; heredocs eat backslashes (write patch scripts with the Write tool).
- A mutation run leaves generated files mutated: touch every restored file afterwards.
- Render every touched view with `tools/preview_iron_court.py` and look at the pictures before calling a UI task done. The preview cannot draw tooltips; say so where a tooltip carries the information.
- Tools have no `--help`: read a tool's docstring for its flags (some build on an unknown flag).

## Review Focus

The five inputs the spec implies and no happy-path test touches, most likely first. Each has its test in the named task.

1. **Declaring war on one faction pulls its allies in**, raising several `NegativeDiplomaticEvent`s in one moment: each party reacts at most once that turn. Task 3, check `war reaction: one per party per turn`.
2. **A council war declared by `cm:force_declare_war` raises the same event**: the free-war flag is set before the call, so the court does not punish its own decision. Task 3, check `war reaction: the council's own war is free`.
3. **Laws switched off while a council vote is open**: `IC.settle_switches` drops the law votes and must keep the council vote (today it sets `court.votes = {}`). Task 2, check `council: laws off keeps the council vote`.
4. **A claimant who took another post, or died, before his claim is answered or lapses**: he is skipped at grant and at lapse, and the next claim is granted. Task 4, check `claims: lapse skips a busy claimant`.
5. **An old save** (no field 21, 22 or 23, and a field 18 written before council votes existed): loads with no planned war, no claims, no secrets, and its law votes intact. Tasks 2, 4 and 5 each add one round-trip check with the field missing.

## File Structure

| File | Responsibility | Tasks |
|---|---|---|
| `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua` | War facts, lines, council vote, planned war, reactions, claims, secrets, save fields, switches, events, MP ops | 1-5 |
| `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_parties.lua` | The `council` party act; `IC.demand_target` skips a claimed province; `IC.drop_party_business` drops claims and secret | 2, 4, 5 |
| `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_dwarf.lua` | `DWF.WAR_LINES`, `DWF.WAR_FOES`, `DWF.PLOT_KEYS`, `DWF.PLOT_TEXT`, any `DWF.EVENT_LOC`/`HELP_SWAP` lines | 1, 2, 5, 8 |
| `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua` | Petitions rows, marker, war vote screen, council picker, secret picker and button, Record, Help, answers; `ICUI.PANEL_XY` mirror | 7, 8 |
| `Modding Files/pack/script/mct/settings/derpy_iron_court.lua` | The `council` and `claims` switches | 2, 4 |
| `tools/gen_iron_court.py` | The eight new feed events, any Dwarf event text | 6 |
| `tools/gen_ic_ui.py` | `ic_lv_over_3/4`, `ic_act_secret`, `HELP_SLOTS = 14` and the help box, their checks | 7 |
| `tools/preview_iron_court.py` | Pictures of the new views | 9 |
| `tools/import_iron_court.py` | Gate lists that the new code meets | 10 |
| `tools/_iron_court_harness.lua` | Stubs and checks | 1-8 |
| `tools/mutate_iron_court.py` | `war:`, `claim:`, `secret:` mutants | 11 |
| `tools/check_ic_release.py` | Snapshot re-pin | 12 |
| `Modding Files/source/iron_court/*.tsv` | Rewritten by the generator, never by hand | 6, 10, 12 |
| `docs/MY_MODS.md`, `docs/SESSION_INDEX.md`, `docs/knowledge-base/status.md`, the spec's status line | Documents | 12 |

## Running the gates

From `G:\Modding for resources`:

```powershell
& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua
$env:IC_TEST_ALL = "1"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua 2> harness_fail.txt; Remove-Item Env:IC_TEST_ALL
$env:IC_ONLY = "council"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY
foreach ($f in Get-ChildItem "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court*.lua") { & "C:\Program Files (x86)\Lua\5.1\luac.exe" -p $f.FullName }
py tools\check_lua_api.py "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court.lua"
py tools\check_lua_literal_left.py
py tools\check_lua_undeclared.py
py tools\gen_iron_court.py --check
py tools\gen_ic_ui.py --check
```

"Lua gates clean" below means the harness, `luac -p` on every Iron Court file, `check_lua_api.py` on each touched file, `check_lua_literal_left.py` and `check_lua_undeclared.py` all pass. Harness checks are written as `check("<name>", function() ... end)` blocks appended before the harness's final summary, using its existing fixtures (`make_faction`, `make_character`, `endow`, `rng`, `plot_court`, `as_player`). Each new check is watched failing first: write it, run it under `IC_ONLY`, see the failure, then write the code.

The baseline is `iron court harness: ok (1155 checks)`, `gen_iron_court --check` (180 bundles, 314 junctions, 297 traits, 2305 loc), `gen_ic_ui --check` (30 files, 1906 components), mutation selftest 1287 anchored, release snapshot `F5CF88CB`.

---

### Task 0: Backups, baselines, ledger

**Files:**
- Create: `Modding Files/Backup/iron_court_war_20261017/` (copies)
- Create: `docs/superpowers/plans/2026-10-17-iron-court-war-claims-secrets.ledger.md`

- [ ] **Step 1: Back up** the five Lua files above, `derpy_iron_court.lua` (MCT), `tools/gen_iron_court.py`, `tools/gen_ic_ui.py`, `tools/preview_iron_court.py`, `tools/import_iron_court.py`, `tools/_iron_court_harness.lua`, `tools/mutate_iron_court.py`, `tools/check_ic_release.py`, `Modding Files/Modpacks/derpy_iron_court.pack`, `docs/SESSION_INDEX.md`, and the folder `Modding Files/source/iron_court` into `Modding Files/Backup/iron_court_war_20261017/`. Expected: every file listed by `Get-ChildItem`.
- [ ] **Step 2: Record the baselines** with the commands in "Running the gates" plus `py tools\gen_iron_court.py --selftest`, `py tools\import_iron_court.py --selftest` and `py tools\mutate_iron_court.py --selftest`. Expected: the baseline numbers above. If any gate is red, stop: the plan assumes a green start.
- [ ] **Step 3: Create the ledger** with a title line and `Task 0 done:` plus the exact baseline lines.

---

### Task 1: War facts and party lines

**Files:**
- Modify: `zzz_derpy_iron_court.lua` (new block after the laws functions, before `IC.member_weight`; `IC.RACE_FIELDS`; new column-0 tables `IC.WAR_LINES`, `IC.WAR_FOES` beside `IC.LAWS`)
- Modify: `zzz_derpy_iron_court_dwarf.lua` (`DWF.WAR_LINES`, `DWF.WAR_FOES` before `IC.register_race(DWF)`)
- Modify: `tools/_iron_court_harness.lua` (stubs, checks)

**Interfaces:**
- Produces:
  - `IC.COUNCIL = "council"`
  - `IC.WAR_LINES` / `DWF.WAR_LINES`: `{[party slug] = {{fact, side}, ...}}`, exactly spec 2.3; a party with no lines is absent.
  - `IC.WAR_FOES` / `DWF.WAR_FOES`: list of subculture keys, exactly spec 2.2.
  - `IC.war_snapshot(faction_key, fill) -> {turn, near = {[key] = true}, trade = {[key] = true}}`, cached in `IC._war_snap[faction_key]`; rebuilt when `fill` is true or the cached turn is stale. `fill` is passed only on the turn path.
  - `IC.war_note_trade(faction_key, other_key)`: adds a partner to this turn's snapshot.
  - `IC.war_facts(faction_key, target_key, snap) -> {[fact] = true}`; `snap` true reads `trade` and `near` from the snapshot, otherwise live (`near` from the cache, which the panel may fill when empty).
  - `IC.war_line(faction_key, target_key, party, snap) -> side|nil, fact|nil`: first matching pair; nil for the Crown, a confederate house, or no match.
  - `IC.war_candidate(faction_key, target_key) -> ok, why`; `why` one of `"self"`, `"dead"`, `"unmet"`, `"human"`, `"rebel"`, `"at_war"`, `"treaty"`, `"far"`.
  - `IC.war_candidates(faction_key) -> {target keys}`, sorted by key.
  - `IC.war_treaty(faction_key, target_key) -> bool`: ally, vassal, overlord or pact, either direction.

- [ ] **Step 1: Add the harness stubs.** `make_faction` gains documented members answering off fields a check sets: `trade_agreement_with(other)` (`f._trade`), `non_aggression_pact_with(other)` (`f._pacts`), `is_ally_vassal_or_client_state_of(other)` (`f._allies`), `is_known_faction(other)` (`f._met`), `is_quest_battle_faction()` (`f._qb`), `num_regions()` (`#provinces`). Each takes the interface or key the CA doc entry says; read it with `check_lua_api.py --explain` and assert the argument type in the stub, as `at_war_with` does. Regions in `region_list()` gain `adjacent_region_list()` (off `f._adjacent[province]`, a list of region keys) and `owning_faction()`; add a `cm:get_region(key)` stub only if the code needs one (check its doc entry).
- [ ] **Step 2: Write the failing checks:**
  - `war facts: each fact on a stubbed world`: a Chaos Dwarf court F and targets T1 (Dwarf, trading, adjacent, 1 army vs F's 2) and T2 (Greenskin, not adjacent, 3 armies). Assert `war_facts(F, T1)` is exactly `{trade, near, weak, foe}`... and `war_facts(F, T2)` is exactly `{strong, foe}`; a Chaos Dwarf T3 gives `kin`; a Dwarf court with T2 named in the Book (`court.book[T2] = 2`) gives `book` and `foe`.
  - `war facts: near is cached per turn`: change the adjacency after the first call on the same turn; `near` is unchanged with no `fill`; after `cm` advances a turn and `fill` is passed it changes.
  - `war facts: the snapshot holds trade`: snapshot taken with T1 trading; set `f._trade` off; `war_facts(F, T1, true).trade` is still true, `war_facts(F, T1).trade` is nil; `IC.war_note_trade(F, T4)` makes `war_facts(F, T4, true).trade` true.
  - `war lines: first match wins`: Chaos Dwarf temple on T1 (foe) is `"aye","foe"`; temple on T3 (kin) is `"nay","kin"`; ledger on T1 is `"nay","trade"`; tower on any target is nil; the Crown is nil; Dwarf legion on a Book target is `"aye","book"`.
  - `war candidates: every exclusion`: one target per `why` code in the Interfaces list returns that code; a Dwarf court's Book target that is not adjacent is a candidate; `war_candidates` is sorted.
  - `race fields: WAR_LINES and WAR_FOES are required`: registering a race table missing either raises.
- [ ] **Step 3: Implement** the Interfaces. Armies are `military_force_list(true):num_items()` with armed citizenry skipped, as the harness stub models; `weak` and `strong` compare the two counts strictly. `near` walks the court's `region_list()`, each region's `adjacent_region_list()`, and records each `owning_faction():name()` that is not the court itself, null-safe and inside `pcall`, as `IC.book_list` guards. `kin` and `foe` read `them:subculture()` against `R.subculture` and `R.WAR_FOES`. `book` is `IC.in_book`. Add `"WAR_LINES", "WAR_FOES"` to `IC.RACE_FIELDS`.
- [ ] **Step 4: Run the Lua gates.** Expected: harness ok with the new checks counted.
- [ ] **Step 5: Ledger line** `Task 1 done:` with files and the harness count.

---

### Task 2: The council vote and the planned war

**Files:**
- Modify: `zzz_derpy_iron_court.lua` (`IC.TUNE` laws block; `IC.TUNE_ORDER`; `IC.LIVE_TUNE`; `IC.settle_switches`; `IC.law_line`, `IC.law_win_price`, `IC.law_party_push`, `IC.law_vote_of`, `IC.law_overrule`; `IC.pack`/`IC.unpack` fields 18 and 21; `IC.LOG_KINDS`; `IC.EVENTS`; `IC.PLOTS` council move; `IC.may_target`/`IC.can_plot`/`IC.plot` for it; `IC.turn`; `IC.MP_OPS`)
- Modify: `zzz_derpy_iron_court_parties.lua` (the `council` party act after the `law` act)
- Modify: `zzz_derpy_iron_court_dwarf.lua` (`DWF.PLOT_KEYS` gains `"council"`, `DWF.PLOT_TEXT.council`)
- Modify: `Modding Files/pack/script/mct/settings/derpy_iron_court.lua` (switch `council`, "War council", beside `laws`)
- Modify: `tools/_iron_court_harness.lua` (`LIVE` list, checks)
- Modify: `tools/gen_iron_court.py` (`EVENTS`: the six war rows, words from Task 6's table)

**Interfaces:**
- Consumes: Task 1's `IC.war_line`, `IC.war_candidate`, `IC.war_candidates`, `IC.war_treaty`, `IC.COUNCIL`.
- Produces:
  - `IC.TUNE` keys from spec 2.9 (signs: `war_broken_loyalty = -15`, `war_bypass_loyalty = -10`, `war_bypass_gain = 3`, `war_peace_loyalty = 3`) and `council = true`. `council` is appended to the END of `IC.TUNE_ORDER` and to `IC.LIVE_TUNE`.
  - `IC.council_on() -> bool`
  - `IC.war_locked(faction_key) -> bool, why`: `"grace"` while `IC.grace_left() > 0`, `"truce"` while `cm:get_saved_value("derpy_no_early_wars_turns")` is set and `cm:get_saved_value("derpy_no_early_wars_released")` is not.
  - `IC.vote_stance(faction_key, category, option, party, culture) -> side|nil, why|nil`: for `IC.COUNCIL`, `IC.war_line(faction_key, option, party)`; otherwise `IC.man_stance(...)` with `why` `"for"`/`"against"` as `IC.law_line` derives today.
  - `IC.council_can_open(faction_key, target) -> ok, why`: refuses `"council_off"`, `"council_open"` (a vote open), `"council_war"` (a war planned), `"grace"`, `"truce"`, or any `IC.war_candidate` code.
  - `IC.council_open(faction_key, target, proposer, stance)`: writes `court.votes[IC.COUNCIL]` in the law record shape, `ends = now + law_vote_turns`, logs `law_propose` with key `"council." .. target`, raises `war_proposed` with `"factions_screen_name_" .. target` when a party proposed.
  - `IC.council_party_pick(faction_key, slug) -> target|nil` (spec 2.5 conditions; pick with `cm:random_number(#list, 1)` from the sorted candidates whose `war_line` is aye).
  - `IC.council_settle(faction_key, passed, how)`; `how` is `"tally"`, `"overrule"` or `"bypass"`. Passed: plans `court.war = {target, at = now + war_prep_turns, proposer}` unless `how == "bypass"`; swings loyalty with `IC.law_swing` over the parties whose war line is aye (gain) and nay (loss); logs `law_pass`; raises `war_passed` (not on bypass). Failed: proposer party `law_fail_loss`; logs `law_fail`; raises `war_failed`. Sets `court.council_rest = now` when a party had proposed.
  - `IC.council_void(faction_key, why)`: closes the vote; `why` `"gone"` or `"treaty"` (the treaty case charges aye parties `war_bypass_loyalty`); Record kind `war_void`.
  - `IC.council_turn(faction_key)`: target-changed checks (spec 2.6, first bullet), then resolve at `ends` or `IC.law_party_push`-style push, then the planned war (spec 2.6, last bullet). Called from `IC.turn` straight after `IC.law_turn`. Player courts only; `IC.council_on()` gates it.
  - `IC.war_calloff(faction_key, gold) -> ok, why, short`: influence through `IC.spend_crown(law_overrule_cost)`, gold through the treasury against `war_overrule_gold`; aye parties `law_overrule_loyalty`; Record kind `war_called`.
  - `IC.law_overrule(faction_key, category, pass, gold)`: `gold` true pays `war_overrule_gold` from the treasury and is refused (`"law_gold"`) on a law vote; a council vote settles through `IC.council_settle(..., "overrule")`.
  - Court fields: `court.votes[IC.COUNCIL]`, `court.war`, `court.council_rest`, and in memory only `court.war_free = {[target] = turn}`.
  - Save: field 18 accepts category `IC.COUNCIL` with any non-empty option; field 21 is `target,at,proposer` (or empty) then `;rest,<turn>` when `council_rest` is set.
  - Record kinds added to `IC.LOG_KINDS`: `war_planned`, `war_begins`, `war_called`, `war_broken`, `war_void`, `war_unasked`, `war_peace`.
  - `IC.EVENTS` appended in this order: `war_proposed`, `war_passed`, `war_failed`, `war_begins`, `war_broken`, `war_unasked`, each `{index, true, false}` with the next indexes after `law_failed` (2636 to 2641).
  - `IC.PLOTS` entry `{key = "council", name = "Call the War Council", aimed = false, target = "faction", sure = true, field = true, cat = "mission", cost = "plot_council_cost", icon = <a CA icon path verified in ui.pack>, effect = <one line naming the vote and the preparation turns>, blurb = <short>}`. `field = true` lets a man leading an army make it: `IC.is_civil_mission` (today `not IC.plot_is_aimed`) returns false for a plot carrying it, so `IC.can_plot`'s general refusal at the `has_military_force()` line skips it. `IC.may_target` routes `council` to `IC.council_can_open`. `IC.plot` opens the vote with proposer `IC.CROWN`, stance `"aye"`.
  - MP: `law_overrule` takes `category|1|1` (third field `1` = gold); new op `war_calloff` (`1` gold, `0` influence).

- [ ] **Step 1: Write the failing checks:**
  - `council: a party proposes on its line`: court with a Legion at 20% share and a weak adjacent target; `IC.council_party_pick(F, "legion")` returns it; at 14% it returns nil; within `war_party_rest` of `court.council_rest` nil; with a vote open nil; with a war planned nil; during grace nil; with the truce's two saved values set nil and with `_released` set too it returns the target.
  - `council: the party act`: `IC.party_turn` with only the council act eligible opens `court.votes.council` with stance `"abstain"` and proposer `"legion"`, and raises `war_proposed`.
  - `council: the move opens a vote`: a Crown general (leading an army) makes `council` on a candidate; it never rolls (no `random_number(100, ...)` consumed), costs him 150 influence, opens with stance `"aye"` and proposer `"crown"`; a non-candidate is refused with the candidate's code.
  - `council: the tally reads war lines`: on a Dwarf target, Chaos Dwarf temple and legion men vote aye with why `"foe"`, ledger men nay with `"trade"` when trading, tower men vote on loyalty, Crown men the stance. `IC.law_win_price` doubles for a man whose war line opposes the Crown's stance.
  - `council: passed plans the war`: a passing vote at `ends` sets `court.war.at == now + 3`, moves aye parties up and nay parties down by `law_swing`, raises `war_passed`, and no `force_declare_war` is recorded yet.
  - `council: failed charges the proposer`: proposer loses 5; `court.war` nil; `war_failed` raised.
  - `council: the planned war at its turn`: four sub-cases, one per outcome in spec 2.6 (target dead; already at war; treaty: aye parties lose 15 and `war_broken` raised; otherwise one `force_declare_war(F, T, false, false)` recorded, `court.war_free[T]` set before it, `war_begins` raised, `court.war` cleared). A fifth: the truce holding on its turn leaves `court.war` in place with `at` one turn later.
  - `council: a target that changed voids the vote`: target dead, so the vote is void with no loyalty move; target unmet, the same; target at war with you (it declared on you), the same; treaty signed, so the vote is void and aye parties lose 10; target no longer adjacent, so the vote stands.
  - `council: overrule for influence and for gold`: Pass now for influence spends 500 Crown influence and plans the war; Fail now for gold spends 2500 treasury and fails it; losing parties lose 10 each time; gold on a law vote is refused `"law_gold"`; short of gold is refused with the shortfall.
  - `council: call off for influence and for gold`: each clears `court.war`, charges the price, and costs aye parties 10.
  - `council: switch off drops the vote and the war`: `IC.TUNE.council = false` then `IC.settle_switches(F)` clears `court.votes.council` and `court.war`; `IC.council_turn` does nothing.
  - `council: laws off keeps the council vote` (Review Focus 3): `IC.TUNE.laws = false` then `IC.settle_switches(F)` drops every law vote and keeps `court.votes.council`.
  - `council: the save round trip`: pack and unpack keep the council vote (option a faction key with underscores, won and push pairs), `court.war`, `council_rest`; an old string with no field 21 and a law-only field 18 loads with `court.war == nil` and its law votes intact (Review Focus 5).
  - `council: AI courts never vote on war`: an AI court's `IC.turn` opens nothing and its party act never proposes.
  - `council: MP ops re-check`: `IC.mp_receive` with `law_overrule` `council|1|1` and `war_calloff` routes to the model, which refuses a short purse.
  - `council: the MCT page, TUNE_ORDER and LIVE agree` is covered by the existing three-way check once `council` is in all three; run it.
- [ ] **Step 2: Run them under `IC_ONLY=council`**; each fails for the missing function, not a typo.
- [ ] **Step 3: Implement** the Interfaces. `IC.settle_switches`: council off clears `court.votes[IC.COUNCIL]` and `court.war`; laws off clears every key of `court.votes` except `IC.COUNCIL`. `IC.law_overrule` for a council vote charges the losing side by war lines through `IC.law_line` (which now reads `IC.vote_stance`). The party act's motive is `T.war_party_motive`.
- [ ] **Step 4: Add the generator rows** (ledger ruling): the six war rows of Task 6's table go into `tools/gen_iron_court.py` `EVENTS`, appended in `IC.EVENTS` order, words verbatim from that table. Task 6 owns the TSV write and the counts.
- [ ] **Step 5: Run the Lua gates**, plus `py tools\gen_iron_court.py --check` and `py tools\gen_ic_ui.py --check` (the Intrigue grid reads `IC.PLOTS`, so the new move's name and blurb are measured there). Expected: all green.
- [ ] **Step 5: Ledger line.**

---

### Task 3: Wars and peace the player makes

**Files:**
- Modify: `zzz_derpy_iron_court.lua` (`IC.register`: a new `NegativeDiplomaticEvent` listener `ic_war_declared`; the existing `ic_book_peace` listener also calls the peace reaction and `IC.war_note_trade`; `IC.turn` fills the snapshot)
- Modify: `tools/_iron_court_harness.lua`

**Interfaces:**
- Consumes: Task 1's snapshot and lines, Task 2's `court.war`, `court.war_free`, `IC.council_settle`.
- Produces:
  - `IC.war_react(faction_key, target_key, kind) -> bool`; `kind` `"war"` or `"peace"`; spec 2.7 in full, reading lines with `snap = true`.
  - `IC._war_reacted = {[faction_key .. "|" .. slug] = turn}`, in memory.
  - The snapshot is filled in `IC.turn` before `IC.council_turn` (`IC.war_snapshot(faction_key, true)`), and for every player court on the first tick after a load (ledger ruling), so a reaction after a mid-turn load reads a state every machine took at the same moment. Only `fill = true` stores; a no-fill call returns a picture (Task 1 fix round 1).
  - Check `war reaction: a load fills the snapshot`: after the first-tick listener runs, `IC._war_snap[F]` holds this turn's trade partners; ending the trade then firing a war event still charges the Ledger.

- [ ] **Step 1: Write the failing checks** (each fires the listener through `core.listeners[...]` with a context table carrying `is_war`, `proposer`, `recipient`, as the existing `ic_book_peace` check does):
  - `war reaction: a war the court was not asked about`: nay-line parties lose 10, aye-line gain 3, loyalty-only parties unmoved, `war_unasked` raised.
  - `war reaction: the target of an open vote`: the vote closes passed by bypass, nay-line parties lose 10, no `court.war` planned.
  - `war reaction: the planned target`: `court.war` cleared as done, no loyalty move.
  - `war reaction: the council's own war is free` (Review Focus 2): run the planned war's declaration through `IC.council_turn` with a `cm:force_declare_war` stub that fires the listener synchronously; nobody's loyalty moves.
  - `war reaction: one per party per turn` (Review Focus 1): three events in one turn move each party once; the next turn's event moves them again.
  - `war reaction: trade read from the snapshot`: the trade agreement is gone when the event fires (`f._trade` cleared), and the Ledger still loses 10.
  - `war reaction: peace`: peace with a faction the Legion's line is aye on costs it 3, gives the Hearth (nay, `strong`) 3; a Dwarf Book target skips the `book` parties and still writes the Book's own `peace` grudge.
  - `war reaction: not our declaration`: an event whose proposer is the target (it declared on us) moves nothing; an AI court's events move nothing; council off moves nothing.
- [ ] **Step 2: Run them; each fails.**
- [ ] **Step 3: Implement.** The listener is wrapped in `pcall` and warns on failure, as `ic_book_peace` is. A trade agreement event adds the partner through `IC.war_note_trade` for both sides that run a court.
- [ ] **Step 4: Run the Lua gates.**
- [ ] **Step 5: Ledger line.**

---

### Task 4: Claims on conquered land

**Files:**
- Modify: `zzz_derpy_iron_court.lua` (`IC.TUNE` keys of spec 3.5 with `claims = true` appended to `IC.TUNE_ORDER` and `IC.LIVE_TUNE`; the `ic_took` listener; `IC.assign_governor`; `IC.pack`/`IC.unpack` field 22; `IC.LOG_KINDS`; `IC.EVENTS`; `IC.turn`; `IC.settle_switches`; `IC.MP_OPS`)
- Modify: `zzz_derpy_iron_court_parties.lua` (`IC.demand_target` skips a claimed province; `IC.drop_party_business` drops the party's claims)
- Modify: `Modding Files/pack/script/mct/settings/derpy_iron_court.lua` (switch `claims`, "Claims on conquest")
- Modify: `tools/_iron_court_harness.lua` (`LIVE`, a `GarrisonOccupiedEvent` context helper with `character()` and `garrison_residence():region()`, checks)
- Modify: `tools/gen_iron_court.py` (`EVENTS`: the two claim rows, words from Task 6's table; run `gen_iron_court --check` at the gate step)

**Interfaces:**
- Produces:
  - `IC.claims_on() -> bool`
  - `IC.claimants(faction_key, province_key, occupier_cqi) -> {{slug, cqi, why}, ...}`, spec 3.2 including the fill-by-weight rule.
  - `IC.claim_raise(faction_key, province_key, occupier_cqi) -> n`: writes `court.claims[province_key] = {ends, list}` when the province is new and claims are on; raises `claims_laid` with `"provinces_onscreen_" .. province_key`; logs kind `claim` per claimant.
  - `IC.claim_grant(faction_key, province_key, slug) -> ok, why` (calls `IC.assign_governor`, which settles through the hook).
  - `IC.claim_refuse(faction_key, province_key, slug) -> ok, why`.
  - `IC.claims_on_assign(faction_key, province_key, cqi)`: the hook, called last in `IC.assign_governor`.
  - `IC.claims_turn(faction_key)`: void checks, then lapse by share (spec 3.4), raising `claim_taken`. Called from `IC.turn` after `IC.council_turn`.
  - `IC.claims_list(faction_key) -> {{province, slug, cqi, why, ends}, ...}` sorted by province then claim order, for the panel.
  - Record kinds: `claim`, `claim_granted`, `claim_refused`, `claim_passed`, `claim_taken`. `IC.EVENTS` appended: `claims_laid`, `claim_taken` (2642, 2643), each `{index, true, false}`.
  - Save field 22: `province,ends,slug:cqi:why/slug:cqi:why;...`.
  - MP ops: `claim_grant` and `claim_refuse`, arg `province|slug`.

- [ ] **Step 1: Write the failing checks:**
  - `claims: a new province only`: the occupier takes the first region of a province, so claims are raised; a second region of a held province raises none; claims off raises none; an AI court raises none.
  - `claims: three claimants in order`: a Legion occupier with no post, an Old World province that is the Forge's main culture's home, and a third rival by share. The list is legion/conquest (the occupier himself), forge/home, then the largest remaining by share; the occupier holding a post is replaced by his party's richest free man.
  - `claims: by weight fills the slots`: on a province with no home match and a Crown occupier, the three rivals by share fill all three slots; the largest with no free man is passed and the next asked; share ties go to `IC.present_houses` order.
  - `claims: grant`: claimant +8, the others -4, the man governs the province, claims closed.
  - `claims: refuse`: claimant -6, the others stay; on a Dwarf court a `demand` grudge is written.
  - `claims: every route to a governor goes through the hook`: assigning a claimant through `IC.assign_governor` (the Governors tab's call) is a grant; assigning a Crown man passes every claimant over (-4 each).
  - `claims: lapse by share`: unanswered at `ends`, the largest-share claimant is granted and `claim_taken` raised.
  - `claims: lapse skips a busy claimant` (Review Focus 4): the largest claimant took an office first, so the next is granted; a dead one is dropped.
  - `claims: void`: the province lost drops every claim; a purged party's claims go through `IC.drop_party_business`.
  - `claims: demands skip a claimed province`: `IC.demand_target` returns another province (or nil) while claims are open, and the claimed one after they close.
  - `claims: the save round trip`, plus an old save with no field 22.
  - `claims: MP ops re-check`: both ops reach the model and refuse an unknown province.
- [ ] **Step 2: Run them; each fails.**
- [ ] **Step 3: Implement.** In `ic_took`, after the existing influence line, read `context:garrison_residence():region()` inside `pcall`; a province is new when `IC.held_region` finds exactly one region of it, the taken one (count the court's regions in that province). Free men come from `IC.candidates(faction_key)` with `not cand.busy`, richest by `IC.standing`, ties by cqi, the way `free_men` in the parties file orders them. Claims off in `IC.settle_switches` clears `court.claims`.
- [ ] **Step 4: Run the Lua gates.**
- [ ] **Step 5: Ledger line.**

---

### Task 5: Secrets

**Files:**
- Modify: `zzz_derpy_iron_court.lua` (`IC.TUNE` keys of spec 4.3; `IC.PLOTS` entry `dig`; `IC.may_target` refusal `held`; `IC.plot` success branch; `IC.LOG_KINDS` `dig`, `secret_used`; `IC.pack`/`IC.unpack` field 23; `IC.MP_OPS`)
- Modify: `zzz_derpy_iron_court_parties.lua` (`IC.drop_party_business` drops the party's secret)
- Modify: `zzz_derpy_iron_court_dwarf.lua` (`DWF.PLOT_KEYS` gains `"dig"`, `DWF.PLOT_TEXT.dig`)
- Modify: `tools/_iron_court_harness.lua`

**Interfaces:**
- Produces:
  - `IC.PLOTS` entry `{key = "dig", name = "Dig for Secrets", cat = "house", cost = "plot_dig_cost", icon = <CA path verified in ui.pack>, effect = <one line>, blurb = <short>}`, placed after `recall` so the Chaos Dwarf column reads unseat, recall, dig.
  - `court.secrets = {[slug] = turn}`.
  - `IC.secret_uses(faction_key, slug) -> {{code, key, may, why}, ...}`; codes `"vote"` (key = vote category, one entry per open vote where the Crown has taken a side), `"demand"`, `"scheme"`, `"count"`, `"expose"`, listed only when spec 4.2 says they apply; `may` false with `why` `"no_secret"` when none is held.
  - `IC.use_secret(faction_key, slug, code, key) -> ok, why`: spends the secret; effects and loyalty per spec 4.2; Record kind `secret_used` with key `code` (or `"vote." .. key`).
  - Save field 23: `slug,turn;...`.
  - MP op `secret_use`, arg `slug|code|key`.

- [ ] **Step 1: Write the failing checks:**
  - `secrets: dig`: success stores the secret on the target man's party; failure costs `plot_fail_loyalty` and stores nothing; a second dig on that party is refused `"held"`; the move costs 120 and uses `plot_chance_dig` 55 with the usual edge.
  - `secrets: the grid stays four deep`: Chaos Dwarf `house` column has three moves, Dwarf four; `gen_ic_ui.plot_counts()` agrees (read it through the harness's existing grid check, or assert `#IC.plots_in("house", race)`).
  - `secrets: each use`: vote (every man of the party won to the Crown's side in that vote, priced nothing), demand (void, no grant, no refusal loyalty), scheme (plot dropped, `party_dropped` logged), count (`clock == 0`), expose (weight -10, loyalty -10, Dwarf `insult` grudge). Each blackmail use costs the party 5; expose does not add the 5. The secret is gone after each.
  - `secrets: uses listed only when they apply`: no open vote lists no vote use; a vote the Crown abstains on is not listed; another party's demand is not listed.
  - `secrets: lost when the party leaves`: a purge clears `court.secrets[slug]`.
  - `secrets: the save round trip`, plus an old save with no field 23.
  - `secrets: MP op re-checks`: `secret_use` with no secret held is refused.
- [ ] **Step 2: Run them; each fails.**
- [ ] **Step 3: Implement.** The vote use writes `vote.won[cqi] = vote.stance` for every man `IC.law_tally` lists for the party. The demand use clears `IC.agenda(faction_key).demand` through `IC.settle_demand(faction_key, "void")`. The scheme use clears the plot the way `IC.drop_party_business` does and logs `party_dropped`.
- [ ] **Step 4: Run the Lua gates.**
- [ ] **Step 5: Ledger line.**

---

### Task 6: Generator: feed events and move text

**Files:**
- Modify: `tools/gen_iron_court.py` (`EVENTS`; the Dwarf event text table if a Dwarf card needs its own words)
- Modify: `zzz_derpy_iron_court_dwarf.lua` (`DWF.EVENT_LOC` for any event given Dwarf words)
- Regenerate: `Modding Files/source/iron_court/*.tsv`

**Interfaces:**
- Consumes: the eight slugs of Tasks 2 and 4, in `IC.EVENTS` order.
- Produces: one `EVENTS` row per slug, appended in the same order as `IC.EVENTS`, with an image key from the vanilla `chd/` set the existing rows use, a sound of `"Positive"`, `"Negative"` or `"Neutral"`, a title, a primary (the subtitle for when the caller gives no name) and a secondary (full sentences).

- [ ] **Step 1: Write the eight rows.** The words, as the cards will show them (the caller's faction or province name replaces the primary):

| Slug | Title | Primary | Secondary |
|---|---|---|---|
| `war_proposed` | A War Before the Court | The Court Will Vote | A party has put a war to the court. Each party votes with the influence of its men. Open the vote from the Petitions tab to take a side, push it or overrule it. |
| `war_passed` | The Court Votes for War | War Is Coming | The court has voted for war. It will be declared in a few turns, so make your armies ready. You can still call it off from the Petitions tab, at a price. |
| `war_failed` | The Court Votes for Peace | The Peace Holds | The court has voted the war down. If a rival party proposed it, that party loses loyalty. |
| `war_begins` | The Court Goes to War | War Is Declared | The war the court voted for has been declared. |
| `war_broken` | A War Called Off | A Treaty Stands in the Way | You signed a treaty with the faction the court voted to fight, so the war cannot be declared. The parties that wanted it lose loyalty. |
| `war_unasked` | A War the Court Was Not Asked | You Went to War Alone | You declared war without putting it to the court. Parties that opposed this war lose loyalty; parties that wanted it gain a little. |
| `claims_laid` | Claims on New Land | A Province to Govern | Parties claim the governorship of the province you have taken. Answer them on the Petitions tab. Unanswered, the claim of the strongest party is granted. |
| `claim_taken` | The Court Grants a Claim | A Governor Is Named | No answer came, so the court granted the claim of its strongest party. |

  Check each Dwarf card against `CHD_WORDS`: none of these carry a Chaos Dwarf word, so no `DWF.EVENT_LOC` entry is needed unless the generator's check says otherwise.
- [ ] **Step 2: Run** `py tools\gen_iron_court.py --check` and `--selftest`. Expected: green, with the loc count up by the eight events times three strings times two races, plus the two moves' result strings for both races (the generator writes these from `IC.PLOTS` and `DWF.PLOT_KEYS`). Read every new loc row it prints in its diff of counts; a jargon or Chaos Dwarf word finding is fixed in the words, not by an exemption.
- [ ] **Step 3: Write the TSVs** with `py tools\gen_iron_court.py` (no flag writes; read its docstring first to confirm) and record the new counts.
- [ ] **Step 4: Ledger line** with the new counts.

---

### Task 7: Panel layout

**Files:**
- Modify: `tools/gen_ic_ui.py` (vote screen cells, action bar, help page)
- Modify: `zzz_derpy_iron_court_ui.lua` (`ICUI.PANEL_XY` mirror, `ICUI.ACT_KEYS`, `ICUI.HELP_SLOTS`, `ICUI.PLATE_BUTTONS`)
- Regenerate: the panel's `.twui.xml` files the generator writes

**Interfaces:**
- Produces:
  - `ic_lv_over_3` at `(1436, 958, 220, 34)` and `ic_lv_over_4` at `(1664, 958, 220, 34)`, the same component kind and skin as `ic_lv_over_1/2`, hidden by default.
  - `ic_act_secret`, the fifth `ACT_BUTTONS` entry after `ic_act_purge`, its width the measured label "Use a Secret" at BODY plus the two 8px end caps (the rule in the `ACT_BUTTONS` comment), in both homes (`PANEL_LAYOUT` and `ACT_PAGED`).
  - `HELP_SLOTS = 14`; `ic_help_box` grown to `(18, 124, 1884, 592)` and `ic_help_rule` to the new topic column's height, so topic 14 (`144 + 40 * 13`, 32 high) and line 14 (`196 + 34 * 13`, 28 high) sit inside it.

- [ ] **Step 1: Make the changes** and mirror every coordinate into `ICUI.PANEL_XY`; `ICUI.ACT_KEYS`, `ICUI.ACT_LABEL` (`ic_act_secret = "Use a Secret"`, measured by check 20g2), `ICUI.ACT_MOVE` (`ic_act_secret = {secret = true}`, and `ICUI.act_check` learns that kind) and `ICUI.PLATE_BUTTONS` learn the new names.
- [ ] **Step 2: Run** `py tools\gen_ic_ui.py --check` and its selftest. Expected: green; the component count rises by the three new buttons and the four new help cells. Every fit, contrast and overlap check the generator already runs must pass with the new cells in it (the action bar at 1600, 1920 and 2560 in both homes; the help box inside the panel and clear of the alert bar).
- [ ] **Step 3: Run the harness.** The harness's own layout checks read `ICUI.PANEL_XY` against the generator; expected green.
- [ ] **Step 4: Ledger line.**

---

### Task 8: Panel Lua

**Files:**
- Modify: `zzz_derpy_iron_court_ui.lua`
- Modify: `zzz_derpy_iron_court_dwarf.lua` (`DWF.HELP_SWAP` for the two race-specific Help lines)
- Modify: `tools/_iron_court_harness.lua`

**Interfaces:**
- Consumes: every model function of Tasks 2 to 5; Task 7's cells.
- Produces:
  - `ICUI.draw_petitions` rows, in this order after the government ask and before the demand: the council vote (`kind = "council"`), the planned war (`kind = "war"`), then one row per claim (`kind = "claim"`, `province`, `slug`). Button labels: council `"Vote"` (second button hidden); planned war `"Call Off"` on both, the first priced in influence and the second in gold (tooltips name the price and the loyalty cost); claim `"Grant"` and `"Refuse"`. Add the labels to `ICUI.PETITION_BTN` and their cells to the generator's `PETITION_BTN_CELL` so check 20k measures them.
  - `ICUI.on_petition_click`: council opens the vote screen (`ICUI.view = "laws"`, `ICUI.law_cat = IC.COUNCIL`); war sends `war_calloff` (`0`/`1`); claim sends `claim_grant`/`claim_refuse`.
  - `ICUI.court_state`: `s.petitions` also counts an unanswered council vote and every open claim.
  - The vote screen with `ICUI.law_cat == IC.COUNCIL`: icon is the target's flag (`flag_path` then `/mon_64.png`, as `IC.house_icon` builds it), name `"War on <faction>"`, fx `"Declared 3 turns after it passes"` (from `war_prep_turns`), side heads `"Declare war"` and `"Keep the peace"`, block words `"declaring war"` / `"keeping the peace"`, back button `"Back to the petitions"` returning to Petitions, `ic_lv_over_3/4` shown with the gold price (hidden on a law vote). `ICUI.LAW_VERDICT` gains `aye|<fact>` and `nay|<fact>` entries for every fact, a few words each ("for it: an old foe", "against: they trade with you").
  - `ICUI.law_title` names a `council.<faction>` key as `"War on <faction>"`; the Record's lines for every kind in Tasks 2 to 5 (`ICUI.intrigue_text`).
  - The council move's faction picker lists every met faction with its refusal in red, through the existing faction picker (`ICUI.mission_rows` for `target = "faction"`), and shows the projected Aye and Nay shares in the row for a candidate.
  - `ic_act_secret` on the Court tab: refused (red, tooltip pointing at Dig for Secrets) when `IC.court(F).secrets[slug]` is nil; otherwise opens a picker of kind `"secret"` listing `IC.secret_uses` rows (use name, effect, a `"Use"` button), which sends `secret_use`.
  - Help: a 13th topic `"The War Council"` (icon `"crown"`), its lines covering spec 2.1 to 2.8 in the player's terms; three claim lines appended to `Petitions`; two secret lines appended to `Intrigue`. A line that names Chaos Dwarf parties or foes gets a `DWF.HELP_SWAP` replacement naming the Dwarf ones (the Book of Grudges, the Clan Warriors); every `{name}` it uses is an `IC.TUNE` number.
  - `ICUI.answer_text` sentences for every new op's refusal codes.

- [ ] **Step 1: Write the failing UI checks** with the harness's fake panel fixtures (`with_fake_panel`, `build_fake_panel(race)`):
  - `panel: petitions rows for a council vote, a planned war and claims`: the three row kinds appear in order with the words above, and each button sends the op named, through `ICUI.send`.
  - `panel: the petitions marker counts council and claims`.
  - `panel: the war vote screen`: icon path ends `/mon_64.png`, heads and back text as above, gold buttons visible with `2500`; on a law vote the gold buttons are hidden.
  - `panel: the fifth action button`: refused with no secret; with one, it opens the secret picker and its rows match `IC.secret_uses`.
  - `panel: help has 13 topics within 14 slots, and every line fills`: no `{` left after `ICUI.help_fill` for either race.
  - `panel: every new Record kind draws a line`: one log entry per new kind renders a non-empty sentence with no raw key.
- [ ] **Step 2: Run them; each fails.**
- [ ] **Step 3: Implement.** Keep the vote screen one function: branch on `ICUI.law_cat == IC.COUNCIL` at the few lines that differ. Text sized by the engine's measure through the existing `ICUI.fit_*` helpers.
- [ ] **Step 4: Run the Lua gates** and `py tools\gen_ic_ui.py --check` (check 20k measures the new button labels).
- [ ] **Step 5: Ledger line.**

---

### Task 9: Preview and design review

**Files:**
- Modify: `tools/preview_iron_court.py` (and the harness's `IC_DUMP` block if a new view needs its own dump)

- [ ] **Step 1: Add pictures** for the war vote screen (`ic_war_vote.png`), the Petitions list carrying one row of each new kind (`ic_petitions.png`), the secret picker (`ic_secret.png`), the Court tab with five action buttons (in `ic_court.png`), and the War Council Help topic (`ic_help_war.png`). Each draws from the shipped Lua through the harness dump, as the law pictures do, on the hardest court the model can roll (longest names, five rivals).
- [ ] **Step 2: Render both races at 1600, 1920 and 2560** and look at every picture. Fix what reads badly: clipped words, a wrap that lands on one word, a label crowding its neighbour, contrast. Re-render after each fix.
- [ ] **Step 3: Run** `py tools\preview_iron_court.py --check` and the harness. Expected: green.
- [ ] **Step 4: Ledger line** naming the pictures viewed and what was fixed.

---

### Task 10: The importer's gates

**Files:**
- Modify: `tools/import_iron_court.py` (only where a gate's list must learn a new name; each change carries a comment saying why)
- Regenerate: TSVs

- [ ] **Step 1: Run** `py tools\import_iron_court.py --selftest` and the import verify (read the docstring for the flag that verifies without packing). Read every finding.
- [ ] **Step 2: Fix each finding at its cause.** A stub member the gate calls undocumented is removed or replaced with the documented one; a loyalty write outside `IC.move_loyalty` is routed through it; a panel call that changes the campaign without `ICUI.send` is routed; a setting nothing reads is read. A gate list is extended only for a caller that is correct, with the reason in a comment, as `IC.redeal_subtype_trade` was added to `ROLLER_GATES`.
- [ ] **Step 3: Run** the selftest and verify again. Expected: clean.
- [ ] **Step 4: Ledger line.**

---

### Task 11: Mutants

**Files:**
- Modify: `tools/mutate_iron_court.py`

- [ ] **Step 1: Add mutants** under the prefixes `war:`, `claim:` and `secret:`, each a plausible mistake with an anchor in the shipped Lua. At least these:
  - `war:` first-match becomes last-match; `weak` and `strong` swapped; `near` read live in a reaction instead of from the snapshot; the free-war flag set after `force_declare_war`; the one-per-turn guard dropped; the treaty case not charging; `war_prep_turns` added twice; the gold overrule not refused on a law; laws off clearing the council vote; a party proposing during grace; the truce's `_released` read inverted.
  - `claim:` a held province raising claims; the weight step stopping after one; the occupier used while he holds a post; refuse removing every claim; the assign hook skipped; lapse picking the smallest share; lapse not skipping a busy man; the demand skip dropped.
  - `secret:` dig storing on the man's cqi instead of the party; a second dig allowed; a use not spending the secret; expose charging the blackmail 5 too; the vote use pricing the men; secrets surviving a purge.
- [ ] **Step 2: Run** `py tools\mutate_iron_court.py --selftest`, then the three new prefixes only (read the docstring for the flag that selects by prefix). Expected: every mutant caught, none stale. A survivor means a check is missing: add the check (watch it fail on the mutant) rather than delete the mutant.
- [ ] **Step 3: Touch every restored file**, then run the harness once more. Expected: green, the tree byte for byte as before the run.
- [ ] **Step 4: Ledger line** with the anchored count and the per-prefix caught counts.

---

### Task 12: Release, build, deploy, documents

**Files:**
- Modify: `tools/check_ic_release.py` (`SNAPSHOT_MD5`, `SNAPSHOT_SIZE`, the comment above them)
- Modify: `docs/MY_MODS.md`, `docs/SESSION_INDEX.md` (one line), `docs/knowledge-base/status.md`, `docs/knowledge-base/systems.md`, the spec's status line, `CLAUDE.md` and `GEMINI.md` only where they quote a count that changed (the mutant count, the snapshot build)

- [ ] **Step 1: Run** `py tools\check_ic_release.py` (fit and contrast, both races, three resolutions). Expected: 0 findings.
- [ ] **Step 2: Build without copying** (`py tools\deploy_iron_court.py --no-copy`, RPFM open). Then `py tools\check_ic_release.py --pack`. Every finding is snapshot drift; read every moved row and loc line, confirm each is one this plan made, then re-pin `SNAPSHOT_MD5` and `SNAPSHOT_SIZE` to the reviewed build, copy that pack into `Modding Files/Backup/` (the gate finds the snapshot by MD5 there), and run `--pack` again. Expected: 0 findings.
- [ ] **Step 3: Deploy** to `data/` with the game shut (`py tools\deploy_iron_court.py --deploy-only`, or `--wait` if the game is running). Expected: the deployed file byte-identical to the built one.
- [ ] **Step 4: Update the documents.** MY_MODS row (size, build, checks, mutants, one sentence on the three systems); one SESSION_INDEX line for this spec and plan; status.md and systems.md build line. No GitHub sync and no Workshop upload: the author decides those.
- [ ] **Step 5: Write the in-game checklist** into the ledger: the spec's "Owed in game" list, plus the tooltips the preview cannot draw (call-off prices, claim reasons, the secret button's refusal).
- [ ] **Step 6: Ledger line** with the build MD5 and size.
