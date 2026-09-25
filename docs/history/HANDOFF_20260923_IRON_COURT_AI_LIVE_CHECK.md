# Iron Court - the AI fix read against live saves, and what it still gets wrong

**Date:** 2026-09-23
**Status:** Diagnosed from live saves, then fixed, built and DEPLOYED (§3b). Not yet seen in game.

Follows `HANDOFF_20260922_IRON_COURT_GOVERNOR_BAR_AND_AI_LOYALTY.md`, whose "Still open" list this
session worked through. That handoff's own "Closed 2026-09-23" block records the same outcomes in
brief.

## 1. Housekeeping closed from the 2026-09-22 list

- **All 7 stale mutation anchors re-aimed, none retired.** Every one had gone stale because the
  2026-09-21 comment pass deleted comment lines inside the anchor; the code under them had not
  moved. The tooltip mutant also had a reworded sentence and still used the pre-Ambition
  `IC.share(court, slug)`; it now uses `IC.share(faction, slug)` so the mutant is a plausible
  mistake rather than a crash. `tools/mutate_iron_court.py` now carries a line saying to anchor on
  code lines only.
- **Four `.bak` files moved out of the pack mirror** to
  `Modding Files/Backup/pack_mirror_bak/script/campaign/mod/`: the Iron Court UI
  `.bak_pre_listenerfix_20260922` plus three August ToZ backups. `pack/script/campaign/mod/` holds
  no `.bak` now.
- **`docs/IRON_COURT_VS_ROME2.md`** header, §2.7, §2.11 and §5 now say Ambition and Military
  Doctrine are built 2026-09-20, deployed 2026-09-22, **not yet seen live**. Values were checked
  against the shipped Lua first (75/100/125 rolled 25/50/25, 100 standing per weight, save field 8,
  `wh3_dlc23_edict_chd_armaments` at +2). The two feature handoffs stay unwritten: both plans gate
  them on the in-game checks.

| Gate | Result |
|---|---|
| `py tools/mutate_iron_court.py` | 207 mutants, 0 unexplained |
| `py tools/mutate_iron_court.py --selftest` | ok, 207 anchored |
| the 7 re-aimed mutants, filtered run | 8 caught (one name matches two) |

## 2. The live check - the AI fix is PARTLY working

### Where the evidence came from

The deployed pack is dated 2026-09-22 21:24. Only `script_log_220926_2128.txt` (turns 19-22) and
`_2208.txt` (turn 23) ran it; everything earlier ran the old pack. The log records **that** a party
seceded but never the state behind it, so the state was read out of the saves with the new
`tools/read_save_values.py` - see §4.

### What worked

At the end of turn 19 (old code) no AI court had a governor and none had more than one office
filled. One fixed turn later: Conclave 5 offices / 4 provinces, Legion of Azgorh 6 / 2, and so on
across every court. Unsnubbed parties hold or rise; Legion of Azgorh's `ledger` came back from 13
with a clock running to 33 and off the clock.

### The three post-deploy secessions were inherited damage

Horns of Hashut `hearth` (loyalty 6), Astragoth `temple` (5) and Slaves of the Black Dwarf `chain`
(5, clock already at 2) all entered the first fixed turn on the edge. One turn could not save them.

### What is still broken: every falling party is a snubbed one

| AI court | party | t20 | t21 | t22 |
|---|---|---|---|---|
| Conclave | legion | 36 | 29 | 21 |
| qb3 | hearth | 39 | 33 | 27 |
| Black Kraken | chain | 43 | 37 | 31 |
| Bzaark | chain | 39 | 35 | 31 |
| Baal | hearth | 25 | 23 | 21 |

Second-wave AI secessions expected around turns 25-28 in this campaign.

**Mechanism.** Pass 2 of `IC.ai_fill_offices` gives a claimed seat to an outsider when the
claimant cannot seat its own man. The court logs in the save show the outsider is almost always a
**Crown** man, often in a court whose Crown is already at or near 100, so his +2 is wasted while
the claimant takes `loyalty_snubbed = -6` at once and `loyalty_affinity_snub = -2`/turn per
claimed office. `legion` claims 3 offices, so an unseated legion runs -1 -6 = -7 before traits,
which is what Conclave measured.

**Why the claimant cannot seat its own man - two cases:**

1. **The party is empty.** `IC.roll_court` rolls `rivals_min..rivals_max` parties at random and
   `IC.roll_background` deals backgrounds evenly across whatever parties are present, so a small
   faction carries parties nobody belongs to. Astragoth's `temple` seceded as "a party of 0".
   Evidence for Conclave `legion`, Black Kraken `chain` and Bzaark `chain`: none got a province,
   and `ai_fill_governors` always serves the party with the fewest posts, so they had no free man.
2. **Its men fail the rank bar**, which the 2026-09-22 fix deliberately kept on the AI. Baal
   `hearth` has two men, both governors, and still lost `fields` to a Crown man.

**The sim that rejected "never seat an outsider in a claimed seat" (3 of 9 against 7) had neither
case in it** - every simulated party had men who could hold its seats.

### Script errors

Both Iron Court scripts load in every post-deploy session. The only script error is VCO's
`vco-disable-ca-wincons.lua`, pre-existing and not ours. No crash dumps since 2026-09-18, no
`bad_mods_report.txt`.

## 3b. BUILT the same session (supersedes §3)

The author's answers: a party that cannot be dealt a lord gets **"another lord in store"**, and
existing saves are **repaired on load**.

Found while building: **every AI rival party was born empty.** `IC.turn` stamped backgrounds
(`stamp_court`) before rolling the court (`reconcile_houses` -> `roll_court`), so on an AI
faction's first turn every starting man went to the Crown. `IC.seed` had the right order and a
comment warning about it, but only the player's court goes through `seed`.

Four changes to `zzz_derpy_iron_court.lua`:

1. **`IC.turn` rolls the court first**: `IC.roll_court` before `IC.stamp_court`. Idempotent.
2. **`IC.leaderless_bg`, called from `IC.background_for`**: a lord (`is_lordly`, not a legend,
   not `NOT_DWARF`) is dealt to a rival party with no leader before anywhere else. Covers campaign
   start, hiring and recruitment, since all four callers go through `background_for`.
   `background_for` also returns nil for a man who already has a background, so the leader test
   and two random draws no longer run over every man every turn.
3. **`IC.ensure_leaders`**, called in `IC.turn` after `reconcile_houses` and in the first-tick
   player init: a rival party with no leader gets one lord made with `cm:spawn_character_to_pool`
   (random pick from `IC.STORE_LORDS`: overseer and the four sorcerer-prophets, i.e.
   `IC.REBEL_GENERALS` minus its convoy and hobgoblin-army variants), and
   `cm:force_add_trait_to_character_details` gives him one of the party's backgrounds. A pooled lord
   is not in `character_list` (CA's Lokhir and Vampire bloodline scripts count theirs by hand), so
   `house.stored`, **save field 16**, stops a new one every turn; it clears once the party has a
   leader. Empty name strings, as CA's Be'lakor script passes, let the engine name him. The spawn
   is pcall'd and logs `IRON COURT: <party> in <faction> has no leader - ...` either way.
4. **`ai_fill_offices` pass 2 only for a seat whose claimant is not in this court.** Re-measured
   over 60 turns on the current code: last session's roster keeps **9 of 9** against 7; a live-like
   roster (Crown holds the men, two empty parties, rank-barred men) keeps `legion` to t55 instead of
   losing it at t13. Last session's "affine-only keeps 3 of 9" was measured before pressure was
   made player-only and no longer holds.

Harness 464 -> 468: the claimed seat stays empty while its party sits in court; an AI court's
first turn deals its lords to its rivals; a lord goes to a leaderless party first; a leaderless
party gets one lord in store with its background, once, surviving a reload, cleared when led. Two
existing checks re-aimed: "every courtier is his own faction's man" now asserts a seated party of
this court (it had passed only because the rng stub picks the Crown), and the ambition roll-band
fixture lost the two draws an already-stamped man no longer makes. Six new mutants, all caught.

**Fixture trap, again:** the first-turn check survived its own mutant until it cleared
`saved["derpy_ic_" .. F]`. `IC.turn` starts with `IC.load`, and the harness's saved-value table
outlives `IC.state = {}`, so an earlier check's saved court (rivals and all) came back.

### Verified and deployed

| Gate | Result |
|---|---|
| `luac -p`, `check_lua_api.py`, `check_lua_undeclared.py` on the model | clean |
| harness | ok, 468 checks |
| `mutate_iron_court.py` | 213 mutants; the one stale anchor ("the split's count left out of the save", on the line field 16 extended) re-aimed and caught; `--selftest` ok, all 213 anchored |
| packed vs mirror, both ways, before the build | model: only my replaced lines differ; UI: identical |
| `py tools/deploy_iron_court.py` | 8,516,548 bytes, 1705 files verified, deployed |
| SHA-256 `Modpacks/` vs `data/` | identical, `f507d563b601ce7a...` |
| read back from the deployed pack | all four changes present; `used_mods.txt` still ticks it |

**Not seen in game.** What to look for on loading the Azeros save:
- `IRON COURT: <party> in <faction> has no leader - a <subtype> waits in the lord pool` in the
  script log, once per leaderless party: the player's at first tick, each AI court at its turn. A
  `no lord made: ...` line instead means the pool call failed, and nothing else will say so.
- The lord in your recruitment pool. Recruited, he should carry the party's background trait and
  appear on its card as leader.
- AI courts: no new `snub_on` in the court log. **An outsider already sitting in a claimed seat
  keeps it until his five-turn term ends**; nothing evicts him, so the -2/turn runs until then.

### 3c. Governors: only a lord in the field can be "away" - DEPLOYED 09:10

The author's screenshot of the Governors tab showed six of seven overseers "(away)". Read live
through the wh3 bridge (file IPC, see below):

| governor kind | `character_type` | force | region | why "away" |
|---|---|---|---|---|
| 4 overseers | `colonel` | garrison | a settlement in ANOTHER province | a garrison commander never leaves his settlement |
| sorcerer-prophet, `derpy_gordak` | `general` | none | **none** | back in the lord pool: no place on the map |

- `IC.governor_active` now returns true for anyone `IC.kind_of_character` does not call
  `"general"` (a general WITH a force): colonels are `"retainer"`, pool lords `"lord"`, heroes
  `"hero"`.
- `IC.governor_edict` asks the assigned province for such a governor, via the new
  `IC.province_edict`. Measured live: **every region of a province reports the same edict**, so any
  region the faction holds there answers.
- Harness 468 -> 469. Ten Doctrine/presence fixtures now set `_force = true`: they are about a
  lord standing in or leaving his province, and the stub's default character has no army. The
  region stub reads a new file-level `province_edicts`. Three new mutants, 216 in all, 0
  unexplained. Deployed 09:10: 8,517,770 bytes, 1705 files verified, SHA-256 identical in
  `Modpacks/` and `data/` (`882c1637240bae5c...`), the fix read back out of the deployed pack.

**Pool lords and `character_list` - both readings were half right.** A lord who went BACK to the
pool (army disbanded, wounded) stays in `character_list` with no region and no force; that is what
the two pool governors were. A lord freshly made with `cm:spawn_character_to_pool` is NOT in it:
the live game logged `road ... a wh3_dlc23_chd_sorcerer_prophet_fire waits in the lord pool`, and a
walk of the list right after found no new lord and `road` still leaderless with `stored = true`.
He leads once recruited.

**Driving the wh3 bridge without its MCP tools.** The mod polls `wh3_mcp_command.json` in the game
folder; write `{"command":"eval","params":{"code":...}}` there and read `wh3_mcp_result.json`.
`wh3-mcp/tools/send-eval.mjs` hardcodes the C: install path, so write the files yourself for F:.
The mod pcalls each eval and returns `{status, result: {values}}`; wrap the probe in your own
pcall anyway.

### 3d. The repair on load, rebuilt to what the author chose - DEPLOYED 09:3x

**Correction.** The author picked "Repair on load", described as *an idle generic lord moved over
from the Crown*. The first build only made a lord in the pool, and a freshly pooled lord is not in
`character_list`, so the logs showed `road in cr_chd_house_of_azeros has no leader - ... waits in
the lord pool` at load and `road` stayed leaderless on its card. That was a deviation from the
answer, not an engine surprise.

`IC.ensure_leaders` now tries **`IC.idle_crown_lord` first**: a lordly man whose house is the
Crown, holding no office or province, not the faction leader, not a legend, no fixed history, not
`NOT_DWARF`, lowest standing first. His `derpy_ic_bg_` trait is swapped for one of the party's (the
`correct_history` idiom, no message) and it logs `IRON COURT: <party> in <faction> had no leader -
cqi N moved over from the Crown`. Only when no such man exists is a lord made in the pool. A
`taken` set stops one man being given to two parties in a pass if the engine reads the trait late.

Harness 469 -> 470. Two fixtures had to change, and both are worth knowing:
- "a generic lord's rolled past is left alone" seated only the Crown, so `IC.turn` rolled
  leaderless rivals around its one lord and the repair moved him. It now seats `road` (his trade's
  party) and clears the saved court.
- **The repair masked the ordering bug**: with backgrounds stamped before the roll, every man went
  to the Crown and the repair moved them straight back out, so "an AI court's first turn deals its
  lords to its rival parties" passed and its mutant SURVIVED. Its three lords now hold offices
  first, which the repair will not touch, so a rival leader can only come from the deal.

Four new mutants (officeholder moved, legend picked, best man given first, old trade kept), 220
in all, 0 unexplained. Deployed: 8,520,259 bytes, 1705 files, SHA-256 identical in both places
(`e6c4bd0984cb89f9...`).

**Mutation runs write into the mirror.** A diff of the mirror against the deployed pack taken
while `mutate_iron_court.py` is running shows whatever mutant is applied. Never diff, build or
deploy while it runs.

### 3e. Overseers as a last resort, and an empty party dissolves - DEPLOYED 10:4x

The 10:10 session's logs showed two things the 3d build could not fix:

- **Azeros `road` still had no leader.** Every lord in the court is legendary except `tower`'s,
  and the only idle lord-types were three garrison-commander overseers, which 3d did not count.
  `road` had its lord in store (field 16 = 1 in the save) and so logged nothing further.
- **An empty party seceded from rising qb3** with 0 provinces and 0 men. All it did was rename
  another rising (the rebel pool was full, so `IC.rebel_faction()` fell back to live qb1) and
  start a war between the two.

The author: overseers **"Yes, as a last resort"**; an empty split **"Dissolve with event log"**.

- `IC.idle_crown_lord` now ranks lords (tier 1) before colonels (tier 2), then lowest standing.
  So an idle Crown overseer is moved over only when no field or pool lord qualifies.
- `IC.party_leader` falls back to `IC.party_colonel`: the highest-standing colonel of the party who
  may speak. He is not in `IC.party_lords`, so he never leads a rising.
- A colonel is tested with `character_type("colonel")` (`IC.is_colonel`), not "non-general with a
  force", which also matches a hero with an army.
- **Colonels do hold the background trait:** overseer 4888 governs steel_plains and the court log
  has `gov_on,tower,...` for him. `stamp_court` stamps every man in `character_list` each turn,
  colonels included, so the three idle overseers carry backgrounds.
- `tick_secession`: a party with no members and no `defecting_provinces` goes to `IC.dissolve`
  (record entry `dissolve`, the kind `prune_confed` already writes; card `dissolved`, event 2611;
  a `dissolves - nobody in it and no province to take` log line) instead of `IC.secede`. An empty
  party that would take a province still secedes.

Harness 470 -> 472. Seven new mutants, and three stale anchors re-aimed (the refused-thrall
fallback, legend picked, best idle lord first); 227 in all, 0 unexplained. The generator has to
be run to write TSVs before deploying: `deploy_iron_court.py` refuses on a row-count mismatch
(it did, 11 vs 12 events). Deployed: 8,524,047 bytes, 1705 files, SHA-256 identical in both places
(`0a6e223f823c0c6b...`).

**What to look for on the next load:** `IRON COURT: road in cr_chd_house_of_azeros had no leader
- cqi N moved over from the Crown`, where N is an overseer. A rising with nobody left logs `...
dissolves - ...` and shows a "A Party Dissolves" card.

### 3f. Party names: Chaos Dwarf words, one shape - DEPLOYED with 3g

The author flagged "Ninth Stair Company" as ridiculous: the tail-first shape (`IC.NAME_SUFFIX`,
heads 1-9) read as a mercenary band. `IC.NAME_SUFFIX` is gone; every name is `<Head> of <tail>`.
Heads are now Cult, Covenant, Conclave, Sons, Chosen, Keepers, Circle, Kin. The tails were
rewritten in Chaos Dwarf terms (Hashut's Breath, the Hell-Forge, the Great Ziggurat, the Lammasu,
Gash Kadrak, Zharr-Naggrund...). Only Chaos Dwarf factions hold a court (subculture gate), so
there is one vocabulary. `IC.party_name` wraps `house.head`/`house.tail` modulo the list length,
so a save rolled against the old 14-head list still names every party, with a new name. Harness
checks every head against every tail of every party, including the 30-character limit and no word
repeated between head and tail. The suffix mutant was re-aimed at the wrap. 227 mutants, 0
unexplained. A rising already named keeps its stored name.

### 3g. Influence came in too slowly - earnings raised, DEPLOYED 11:5x

Author, turn 32: "the office seats are unfulfilled". The turn-32 save had **2 of 14 seats filled
and 12 of 24 men at 0 influence**. Four governors held exactly `governor_income` x turns governed
(4752/4753 = 90 over 18 turns, 4888 = 60 over 12, 7828 = 40 over 8): they had earned nothing
else in 32 turns. Field lords sat at 58-134 (about 2-4 a turn, from battles only). Cqi 2414, seated
almost every turn since turn 4, had 828, because the office wage feeds whoever holds the seat.
Causes:
- **The trickle went to almost nobody.** `IC.trickle_for` withheld it from anyone with a military
  force, and a **garrison commander's garrison is a force**, so every colonel earned 0 forever.
- Battles (4-25) and settlements (12) were small against the 100/200/300/400 bars.
- Intrigue moves spend the same influence.
- The AI is exempt from the influence bar, which is why AI courts fill and the player's did not.

The author chose "Raise earnings" over halving the bars: colonels earn the stay-at-home trickle
(`IC.is_colonel` checked before the force test), `influence_trickle` 2 -> 5, `battle_influence`
doubled to 50/30/16/8, `settlement_influence` 12 -> 24. The bars are unchanged.

**Measured before shipping** (current harness plus an appended simulation, one decisive win per
field lord every 3 turns; the old rates reproduce the live 58-134):

| Court, turn | men over 100 | over 200 | over 300 | over 400 | biggest share move |
|---|---:|---:|---:|---:|---|
| player-shaped (12 men), t32, old | 4 | 0 | 0 | 0 | |
| player-shaped, t32, new | 12 | 4 | 4 | 0 | Crown +4 |
| player-shaped, t60, new | 12 | 12 | 12 | 4 | Crown +5 |
| AI (10 men), t60, new | - | - | - | - | +1, every party kept |

The share side effect is small because `member_weight` divides influence by 100. Harness 472 ->
473 ("a garrison commander earns the stay-at-home trickle"), one new mutant, 228 in all, 0
unexplained. Deployed with 3f: 8,524,562 bytes, SHA-256 `a9920dc5958a531e...` in both copies.
Not yet seen in game: expect every governor and garrison commander to gain 5 a turn from the next
turn.

## 3. Approved by the author (as first proposed)

The author answered "yes" to both, and added a requirement that reshapes the second:

1. **AI only: never give a claimed seat to an outsider while the claiming party sits in this
   court.** Seats claimed by a party absent from the court still go to anyone. Covers both cases
   above; Baal `hearth` would then climb on its two provinces.
2. **Author, 2026-09-23: "at the start of the campaign my faction has parties with no leaders ...
   the party ALWAYS should have a party leader, any lord type if possible."** So the fix for
   empty parties is not "an empty AI party disbands at zero" (what was first proposed) but **no
   party is ever leaderless, player or AI** - a party's existence should be backed by at least one
   man, a lord where one exists. Where to do it is open: `IC.roll_court` (roll no more rivals than
   there are men to lead them), `IC.roll_background` (deal the emptiest party first, lords first),
   or both, plus what an existing save does with a party that is already empty.

Measure both against the model **with empty parties and rank-barred men in the fixture** before
keeping either - the previous sim's blind spot is exactly those two cases.

## 4. Rival parties, build 1 - DEPLOYED 18:0x

Spec `docs/superpowers/specs/2026-09-23-iron-court-rival-party-ai-design.md`, plan
`docs/superpowers/plans/2026-09-23-iron-court-rival-party-ai-build1.md`. Player court only.

**What shipped.** A new script, `zzz_derpy_iron_court_parties.lua`, hooked into `IC.turn` after
the feed flush and before secession. Each turn, in this order:
1. every governor gains 750 raw experience (`cm:add_agent_experience`, no `by_level`);
2. feuds whose cause, time or party is gone end;
3. a move warned last turn lands or is dropped, and that is the turn's one event;
4. otherwise one act runs, picked by motive among the top three: intrigue against the Crown,
   starting a feud, or a feud move against the enemy party.

- **Intrigue lines.** Rumour and discredit are open at loyalty 55 or below. Unseat and recall
  open at 25, murder at 10.
- **Warnings.** Unseat, recall and murder are warned a turn ahead. The mood button says
  SCHEMING, and its tooltip names the target, the move and the plotter.
- **Feuds.** A feud starts over a stolen seat or between equals. It aims the party's intrigue at
  its enemy instead of the Crown, and the mood button says FEUDING.
- **Feud murders.** Allowed once a feud is 5 turns old, at a quarter of the whole chance: 10% at
  even influence.
- **Murder limits.** Murder never hits a legend or the faction leader. The leader is checked
  again when a warned murder lands.
- **New events.** Seven, at 2612-2618. Six new court-record kinds.

**Deviations from the spec**, all ruled during the build:
1. **No new agenda line on the card.** The card is full. The mood button's word and its
   tooltip carry the agenda.
2. **Feud state lives in its own saved value,** `derpy_ic_agenda_<faction>`. `IC.pack` is
   untouched, so old saves load.
3. **No roster marker.** The tooltip names the target, because an event card is loc-keyed and
   cannot name anyone.
4. **Event indices by build.** Build 2 appends after 2618, not at the spec's 2612-2620 order.
5. **A feud rest.** Both parties wait 5 turns before a new feud.
6. **`party_feud_murder` (2618) is new.** A feud murder kills one of the player's own men, and
   the spec gave it no card. The whole-build review found it killing silently.

**Pace, measured.** A 60-turn simulation of a player-shaped court: 12 men, 3 parties, no offices
filled.
- **Quiet turns:** 50, 52 and 54 of 60, on three random seeds. The plan targeted about half.
- **Feuds:** 20-33% of events.
- **Party losses:** none to intrigue. Build 1 never moves loyalty. One party left in most seeds,
  from trait-driven loyalty drift with no appointments.

Default tuning was kept. A party at loyalty 55 has an intrigue motive of 1, under the floor of 10,
so it does nothing, which is intended. Only a floor of 1 moves the number (45 of 60 quiet), and it
breaks the floor's meaning. **Expect a quiet court until parties fall below about 45 loyalty, or
until Build 2's demands and offers.**

**Gates.**

| Gate | Result |
|---|---|
| Harness | 514 checks (499 before the final review's fixes) |
| Mutants | 269, 0 unexplained |
| Loc rows | 587 |
| luac, API check, undeclared-name check (whole folder), generator self-test, UI layout, TWUI reader | all pass |

The live pack's Iron Court Lua was confirmed identical to the pre-build mirror before building,
so every difference in the new pack is this build's. Built with `deploy_iron_court.py --no-copy`
while the game was running. The read-back found all three scripts byte-equal to the mirror, and
the new event in both the DB and the loc.

| Copy | Size | SHA-256 |
|---|---:|---|
| `Modding Files/Modpacks/derpy_iron_court.pack` | 8,555,779 | `0e5409edadb8bd6f...` |
| `data/derpy_iron_court.pack` | 8,555,779 | `0e5409edadb8bd6f...` (copied at 18:0x once the game closed; ticked in `used_mods.txt`) |

The copy is the pack built above, not a rebuild: by then the mirror held half of Build 2, so
`deploy_iron_court.py` was not run. The 3f/3g pack it replaced (`a9920dc5...`) was kept in the
session scratchpad.

**What to look for in game:**
- **Governor experience:** an `IRON COURT: governors given 750 xp in <faction>: cqi@rN ...` line
  each turn. A governor whose rank never rises means the engine refused the call.
- **Party cards:** SCHEMING and FEUDING on the mood button, with the target and plotter named in
  its tooltip.
- **New cards:** the seven new event cards (warn, struck, foiled, abandoned, feud, feud over,
  blood between parties).

**Left for later, with reasons:**
- **The placated test runs after the turn's loyalty drift,** so a party raised to exactly 26 can
  drift to 25 and still strike.
- **A faction that stops being human keeps its pending plot.** The plot lands when the faction is
  human again. This is hotseat only.
- **No pcall around `IC.party_turn`,** because `IC.turn` has none anywhere.
- **Feud scoring is costly.** It calls `IC.share` about 116k `has_trait` times a turn at 60 men
  and 5 parties, measured in the harness. Measure it in game before caching.
- **A pending warned move does not appear on the Intrigue tab's alert line.** That is Build 2
  UI. (Done in §5.)

## 5. Rival parties, build 2 - DEPLOYED 18:48

Plan `docs/superpowers/plans/2026-09-23-iron-court-rival-party-ai-build2.md`. Player court only.
It adds two more acts to §4's list, and two upkeep lines after the feud endings: demands settle,
then offers lapse.

**Demands.** A party at loyalty 26-74 asks for an office or a province for one of its men.
- **One live demand per court.** It is issued as a SCRIPTED mission through the string route
  (`derpy_ic_demand_office` / `derpy_ic_demand_province`), with 5 turns to meet it.
- **Met:** the man holds the post. The party gains 12 loyalty on top of the normal appointment
  bonus.
- **Refused:** the post goes to someone else, or the time runs out. The party loses 10 loyalty
  and a card is raised.
- **Void:** the man or the party is gone, or the province is no longer yours. This costs nothing,
  and the mission is cancelled.
- **Motive.** It rises with how far the party's posts fall short of its share.
- **The Lua settles every outcome.** The engine's mission events are only a backstop. Two guards
  come from the final review:
  - an engine expiry re-reads the court, so a demand you met on its last turn still counts as met;
  - an event on the turn a demand is issued is ignored, so a late event from the previous demand
    cannot refuse the new one.
- `can_be_manually_cancelled` is false.

**Offers.** A party at 75 or above offers one gift, lapsing after 3 turns:
- **gold:** 60 per point of its share;
- **backing:** 100 influence for a Crown man within 100 of an office's bar and past its rank bar;
- **calm:** +10 loyalty for a party whose countdown is running, and the countdown stops;
- **troops:** 2 units of the party's own kind into a lord's army with room, out of 20.

Accepting one costs 3 loyalty with every other rival party, but never the Crown or the giver. A
calmed party is envious too, so calm nets +7.

The offer appears as two rows at the top of the favour list that the card's button opens. The first
row leads with the price, and the button column reads ACCEPT, or NO ROOM, LAPSED or GONE. The
second row declines.

**Panel.**
- **Mood word:** SCHEMING > DEMANDING > FEUDING > OFFERING, after the countdown. The tooltip carries
  a paragraph for each, with the office and the lord named.
- **Intrigue alert:** a warned move now leads the line. The "(N more houses moving.)" clause
  counts other parties with a countdown running, not lines.

**Events.** 2619 `party_demand`, 2620 `party_demand_refused`, 2621 `party_offer`. Six new court-record
kinds. 605 loc rows.

**Deviations from the spec**, all ruled during the build:
1. State lives in the agenda saved value (`plot|feuds|calm|demand|offers`), not in court fields
   20-22. A Build 1 save with three parts loads.
2. ACCEPT and DECLINE are favour-list rows, not a new card button.
3. The Lua owns demand outcomes, as above.
4. Backing also needs the man past the office's rank bar, not only near its influence bar. Backing
   that cannot seat anyone would be a gift that does nothing.
5. A lost province voids its demand. The spec voided only for a gone man or party.

**Pace, measured.** The same 60-turn simulation with every act on. It fills no office and answers
no demand, so it is the worst case.
- **Quiet turns:** 37, 42 and 43 of 60.
- **Demands:** 4, 4 and 3, all run out as refusals.
- **Offers:** none. Loyalty never reached 75 without player action.
- **Secession:** one party seceded in every seed, from loyalty drift rather than refusals.
- Tuning was not changed. **The pace is the author's call once played.**

**Gates.**

| Gate | Result |
|---|---|
| Harness | 559 checks (514 at Build 1) |
| Mutants | 326, 0 unexplained |
| Loc rows | 605 |
| luac, API check, undeclared names (whole folder), generator self-test, UI layout, TWUI reader, import verify | all pass |

The live pack's Iron Court Lua (Build 1) was confirmed identical to the pre-build baseline before
building. It was built with `--no-copy` and then copied once the game closed. The read-back found:
- the three scripts byte-equal to the mirror;
- both demand keys in `missions`;
- the reward in `campaign_payload_ui_details`;
- the new events and loc.

| Copy | Size | SHA-256 |
|---|---:|---|
| `Modding Files/Modpacks/derpy_iron_court.pack` | 8,588,187 | `c0f27cd10c1dcc5a...` |
| `data/derpy_iron_court.pack` | 8,588,187 | `c0f27cd10c1dcc5a...` (ticked in `used_mods.txt`) |

**What to look for in game.** Nothing here was probed through the bridge:
- **The demand mission** draws in the objectives panel with its text and reward line, and
  completes when you seat the man.
- **Seat the man on the "1 turn left" turn.** It must count as met: +12, with no refusal card.
- **Let a demand run out,** then watch the next demand of the same kind. It must not be refused on
  arrival.
- **Troops arrive** in the lord's army. If `cm:grant_unit_to_character` fails live, the troops
  option comes out (spec section 5).
- **The mood words** DEMANDING and OFFERING, and the two offer rows in the favour list.
- **Governor experience,** carried over from §4.

### 5a. Governors who cannot gain experience are paid instead - DEPLOYED 21:2x

**The live logs answered the spec's open question** (sessions 18:51 and 19:16, turns 38-41).
Seven of the player's nine governors read `r0` after three 750-point grants, and CA's
`add_agent_experience` wrapper accepted every call without complaint. The two lords with armies
climbed. CA documents rank as 1-based, so a steady 0 is a man the engine will not level: a garrison
commander or a lord in the recruitment pool.

**The fix.** `IC.governor_xp` still makes the grant. When the rank it reads afterwards is exactly
`"0"`, it pays that governor a second `governor_income` (5) through `IC.add_standing`, as spec
§3b planned. The log line marks him `cqi@r0+inf`.

**Checks.**
- Harness: 560 checks, with the new check "a governor who cannot gain experience is paid influence
  instead".
- Mutants: 328. The two new ones, "never paid" and "every governor paid", are both caught by that
  check. The full suite was not re-run: the self-test anchors all 328, and the change touches only
  this function.
- Pack: 8,588,591 bytes, SHA-256 `9171c143bde78bc1...` in both copies.

**In game:** the next `governors given` line should show `+inf` on the `r0` governors, and each
should gain 10 influence a turn from the post instead of 5.

**Left for later, with reasons:**
- **The Great Guilds pays out on a met demand.** `zzz_derpy_guilds.lua` rewards any completed
  mission. Both mods are the author's, so this is the author's call.
- **An office demand whose man is discredited below the bar** is still charged at expiry. That is
  a design question, not a bug.
- **Unknown flags now refused by `tools/mutate_iron_court.py`.** `--help` used to fall through to
  the full suite, and a run killed midway leaves a mutant in the shipped Lua.

## Do not re-derive

- **A `.save` is readable offline.** ESF (magic `cb ab`) plus one LZMA block. The props
  (`46 05 5d 00 00 04 00`) and the u32 uncompressed size sit in `COMPRESSED_DATA_INFO` just before
  the string table; the block is the u8 array (tag `0x46`, big-endian 7-bit varint length) ending
  right before that. Decompressed (~259 MB at turn 20), saved values are text,
  `key:::type:::len:::value;;;`. Every AI court is in there.
- **Anchor that regex on the `:::` markers.** A leading `[^;:]+` key pattern backtracks over the
  whole body and did not finish in 300 s; anchored, it takes ~2 s.
- **The harness stops at the first failing check** unless `IC_TEST_ALL=1` is set. A mutant
  "caught" by a fixture guard (e.g. `the fixture seats N men`) says nothing about whether the check
  written for that rule still bites - rerun with `IC_TEST_ALL=1` and read every FAIL. Both
  member-count mutants were checked this way and the dedicated "heroes counted" check does fail.
- **An `Auto-save.N` is written when turn N ends, before the AI turns run.** Post-deploy AI
  behaviour first shows in `Auto-save.20`, not `.19`.
- **`gov_on;-;...` in a court log** means the governor's party resolved to nil (no background, or
  not a Chaos Dwarf character), not a missing field.

## Still open

1. **Live check of §3b** - the three things listed under "Verified and deployed". Then re-read the
   AI courts a few turns on with `py tools/read_save_values.py <save>` and compare with §2's table.
2. **Black Kraken's party set changed wholesale between the turn-19 and turn-20 saves**
   (`hearth`/`temple`/`road` -> `chain`/`forge`, Crown 5 -> 74) with no secession or dissolve line
   in the log. Not explained. `IC.reconcile_houses` removes non-parties and `IC.prune_confed`
   dissolves confed houses whose men are gone; neither obviously accounts for it.
3. Everything in the 2026-09-22 handoff's items 1-2 beyond the AI courts: Ambition and Military
   Doctrine have still not been checked in game.
4. The two feature handoffs for Ambition and Military Doctrine, after (3).
5. **The rebel pool can run out.** With qb1, qb2, qb3 and invasion all alive, `IC.rebel_faction()`
   falls back to live qb1, renaming a rising that already exists. §3e stops the empty case, not
   a real fifth rising.
6. Live check of §3e: the overseer moved into `road`, and whether a colonel leader draws on the
   party card (portrait via `CcoCampaignCharacter.PortraitPath`; silhouette if none).
7. **Rival parties, builds 1 and 2 (§4, §5):** both are deployed. Check them in game against the
   two "What to look for" lists.
