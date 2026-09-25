# Iron Court - governor influence bar removed, deployed, and the AI loyalty gap measured

**Date:** 2026-09-22
**Status:** Both built, deployed and verified offline. Neither has been seen in a live campaign.

## Goal and subsystem

Two things happened, in order.

1. Remove the influence requirement a man had to clear before he could be made overseer of a
   province, then ship it.
2. Answer a player-side observation - "parties are always rebelling for the AI" - which turned
   into a measured finding that the AI cannot manage loyalty at all, and then into four fixes.

## 1. The governor influence bar is gone

`IC.assign_governor` used to refuse a man whose standing was under `IC.TUNE.governor_influence`
(150), with the shortfall handed back for the panel to explain. That bar is deleted.

### Changed files

- `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua`
  - The three-line standing gate in `IC.assign_governor` is gone; a comment in its place says why
    a province is not a seat.
  - `governor_influence = 150` removed from `IC.TUNE`. Nothing else read it, verified by grep
    across `tools/` and `Modding Files/pack/`.
- `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua`
  - `ICUI.pick_cost` returns `0` for a province, so no picker row can draw `SHORT`.
  - `ICUI.pick_title`'s province branch dropped its `- needs %s influence` clause. A
    `needs 0 influence` would have been the shape of a rule with the rule taken out.
- `tools/_iron_court_harness.lua` - three checks inverted rather than deleted:
  - "any house's man may govern" now asserts a man on **0** standing takes a province.
  - "a province asks for standing too, and says how short he is" became "a province asks for no
    standing at all, and still pays a wage", and asserts nothing is deducted.
  - The picker-title check now asserts the title contains no `influence` at all **and** that
    `ICUI.pick_cost("gov", ...)` is 0.

The office bar is untouched. `IC.can_appoint` still enforces `IC.tier_influence(office.tier)` and
the rank bar, and `enforce_bars` still unseats an officer who falls under it.

### What was verified, and how

| Gate | Result |
|---|---|
| `lua.exe tools/_iron_court_harness.lua` | ok, 459 checks |
| `luac.exe -p` on both scripts | parse ok |
| `py tools/check_lua_undeclared.py` | no new findings (the UI file's 13 names are pre-existing and identical in the pre-session backup) |
| `py tools/import_iron_court.py` | verify ok - 43 bundles, 56 junctions, 73 traits, 563 loc, 2 scripts, 7 ui files, 1658 png |
| `py tools/mutate_iron_court.py` | 202 mutants, 7 unexplained - all seven pre-existing stale anchors, none in code touched here |
| `py tools/deploy_iron_court.py` | saved 8,507,095 bytes, 1705 files verified, copied to `data/` |
| SHA-256, `Modpacks/` vs `data/` | identical: `0d99f74bcec353654d9bf8779111483e2c9ca2c984d569ae9f5f3c2168560873` |
| path-set diff against the pre-deploy pack | 1705 both sides, nothing added or dropped |
| `used_mods.txt` | `derpy_iron_court.pack` present, so the mod is ticked |

## 2. The correction found the hard way: the deployed pack was three days stale

The first attempt at shipping the change pushed the two Lua files straight into
`data/derpy_iron_court.pack` over the RPFM MCP server. That worked, but it bypasses
`tools/deploy_iron_court.py` and leaves `Modding Files/Modpacks/` behind. The proper deploy was
re-run afterwards and is what shipped.

Carving the pre-session packed model Lua and diffing **both ways** (the rule in
`pack-lua-carves-out-of-binary`) turned up something bigger:

- packed copy: **313,126 bytes**
- staged copy: **138,502 bytes**
- same 171 functions on both sides

The difference was the whole 2026-09-21 humanize pass - every party and leader trait blurb, the
loyalty-breakdown labels, the intrigue effect strings - plus its comment reduction from 2,325
standalone comment lines to 41. That session's own report states it deliberately touched no pack,
and `.superpowers/sdd/2026-09-21-iron-court-humanize/baseline/zzz_derpy_iron_court.lua` is exactly
313,126 bytes, which confirms the pack was the stale side and the mirror was current.

**So this deploy shipped the humanize copy changes as well as the governor change.** Anyone
comparing player-visible text against an older screenshot should expect it to differ.

## 3. The AI could not manage loyalty - the diagnosis

Everything in this section describes the state **before** the fixes in section 4.

### The observation

In `script_log_220926_2011.txt`, with the player on `cr_chd_house_of_azeros`:

- turn 15 - `tower` secedes from `wh3_dlc23_chd_zhatan`
- turn 18 - `road` **and** `temple` both secede from `wh3_dlc23_chd_conclave`
- turn 18 - `hearth` secedes from `cr_chd_warfleet_of_uzkulak`

The player lost none.

### The mechanism

`IC.turn` runs on `FactionTurnStart` for **every** Chaos Dwarf faction - standing, terms, drift,
bundles and secession clocks all tick for the AI. The AI's entire agency is `IC.ai_fill_offices`.
`IC.favour` and `IC.plot` are reached only from `ICUI.on_pick_click`, so no AI faction can bribe,
gift, secure, pledge, or deliberately appoint an affine house.

Three causes compound:

1. **AI lords earn zero standing per turn.** `IC.trickle_for` returns
   `influence_trickle_general = 0` for any character with a military force and
   `influence_trickle = 2` only for one without. The lowest office bar is 100 standing, the apex
   400. So a lord banks standing only from battles (25/15/8/4), settlements (12) and ranks (3).
2. **Loyalty drifts from turn 1; standing does not.** No seat is `-1`/turn from a start of 55,
   plus trait penalties. `IC.at_breaking_point` (loyalty <= `secede_break` = 0) secedes a party
   immediately and **bypasses the `secede_share >= 25` gate** in `IC.tick_secession`, so the share
   test never protects an AI court.
3. **The AI never governed.** There was no `ai_fill_governors`, and the harness asserted its
   absence on purpose ("the AI never hands out a province"). `court.govs` stayed empty forever: no `+2`/turn
   per province governed, no Military Doctrine loyalty term, and the `grasping` party trait pinned
   at `-2`/turn.

Then when seats do finally fill, `ai_fill_offices` sorts the whole candidate pool by standing with
**no affinity preference**, so most appointments fire `loyalty_snubbed = -6` at the affine house and
`loyalty_affinity_snub = -2`/turn while the outsider sits there - and `term_turns = 5` means
`expire_terms` empties the seats and `ai_fill_offices` re-snubs every five turns.

### The measurement

Simulated against the **shipped** model under the harness stubs - nine parties, fourteen offices,
eight lords with forces and four heroes without, 120 turns:

| AI battle rate | first seat filled | parties left of 9 |
|---|---|---|
| never fights | t50 | 4 |
| a decisive win every 5 turns | t35 | 3 |
| a decisive win every 2 turns | t14 | 4 |
| a decisive win **every** turn | t7 | 4 |

An AI winning a decisive battle every single turn still loses five of its eight non-Crown parties
by turn 55. The peaceful case predicted the first wave at t19; the live log shows t15 and t18.

### A fixture trap worth recording

The first simulation attempt called `endow()` and then `IC.turn()`, and read seats = 0 for 40
turns. That is not the model - `IC.turn` begins with `IC.load(faction_key)`, which rebuilds the
court and discards standing written straight into `IC.state`. Standing after the first
`IC.turn` was **2**, the trickle. Endow after the load, or drive `IC.ai_fill_offices` directly,
as the existing harness checks do.

## Do not re-derive

- **`import_iron_court.py` does not write anything.** It is a verifier and a manifest printer.
  `tools/deploy_iron_court.py` is the thing that builds and copies; `--no-copy` stops at
  `Modding Files/Modpacks/`.
- **The RPFM MCP session loses its schema binding when the server reconnects.** `export_tsv` then
  fails with "There is no Schema for the Game Selected" even though packs are open. Re-run
  `set_game_selected(warhammer_3, rebuild_dependencies=false)` and re-open the pack.
- **The 7 stale mutation anchors in `mutate_iron_court.py` are pre-existing**, not caused by the
  governor change. One was confirmed against the pre-session UI backup: the anchored string is in
  the backup and absent from the current file, so it went stale during earlier work.
- **The 13 undeclared ALL_CAPS names `check_lua_undeclared.py` reports for the UI file are
  expected.** `import_iron_court.py` passes them as `elsewhere`; running the checker on the UI
  file alone reports the same 13 for the pre-session backup.
- **`IC.trickle_for` pays the general rate to characters WITH a force.** The naming reads the
  other way round. `influence_trickle_general = 0`, `influence_trickle = 2`.
- **Read the pack and the mirror both ways before deploying.** This session found the pack stale;
  the 2026-09-02 naval-horde case found the mirror stale. Neither side is reliably authoritative.

## 4. The AI fixes, built and deployed

Four changes to `zzz_derpy_iron_court.lua`, in the order they were found. Each was **measured**
against the shipped model before it was kept, and two candidate fixes were **rejected** by
measurement.

1. **`ai_fill_offices` prefers the claiming party.** Two passes per seat: the affine house first,
   anyone second. Removes the `-6` snub and the `-2`/turn while an outsider sits in a claimed seat.
2. **`IC.ai_fill_governors`,** called from `IC.turn` after the offices. Picks the party holding the
   fewest posts, recomputed **per province** rather than off one sort - handing out the first
   province changes who is neediest for the second.
3. **The office standing bar is the player's rule only.** `IC.can_appoint` skips the
   `tier_influence` test for an AI court and `IC.enforce_bars` returns early for one. The rank bar,
   the term, one-post-per-man and the affinity preference all still bind the AI.
4. **An AI court is exempt from pressure.** `IC.tick_pressure` returns early and clears any
   `pressed` flag carried in from an older save.

### What the measurement rejected

- **Raising `influence_trickle_general`** - the fix named at the end of the last session. Swept at
  0, 1, 2, 3, 5 and 8: survivors plateau at 5 of 9 and the first seat only moves from t29 to t13.
  The blocker is the bar, not the income. **Not shipped.**
- **Never seating an outsider in a claimed seat.** Reads like the kinder rule; an empty seat pays
  nobody, so it measured 3 of 9 against 7. **Not shipped.**
- **Reordering to affine offices -> provinces -> remaining offices.** 5 of 9 against 7 - with more
  offices than men, every man being an officer is already the best outcome. **Not shipped.**

### The measurement, 120 turns, 9 parties, 14 offices, 12 men

| AI battle rate | before | after |
|---|---|---|
| never fights | first seat t50, 4 of 9 left | first seat t1, **7 of 9** |
| a win every 5 turns | t35, 3 of 9 | t1, **7 of 9** |
| a win every 2 turns | t14, 4 of 9 | t1, **7 of 9** |
| a win every turn | t7, 4 of 9 | t1, **7 of 9** |

The two that still leave (t31 and t40) are ordinary drift: each claims two offices, can staff one,
and carries the `-2`/turn for the other. That is the mechanic working, not a fault.

### The correction that mattered most

Pressure, not loyalty, was killing the strongest parties. With the seats filling from turn 1,
`forge` left on **turn 11** and `legion` on **turn 17, both at 100 loyalty** - `IC.tick_secession`
honours `house.pressed` regardless of loyalty or share. The Crown claims **none** of the fourteen
offices, so a court that fills up hands weight to rivals and to nobody else, and Crown control
collapses. The better the AI ran its court, the faster its strongest party was pressed. Fixing
loyalty alone would have made the symptom worse.

### Harness and mutants

- 5 new checks, 459 -> **464**, all green.
- 5 new mutants, 202 -> **207**, all caught. Each is an edit a later reader would think redundant:
  collapsing the two-pass loop, dropping the per-province recount, removing either half of the bar
  exemption, removing the pressure exemption.
- 6 existing checks now declare which court they want. They were reading the stub's `{}` default
  and calling the exemption a broken bar. The pressure block declares human once and hands it back.
- The shared `plot_court` fixture was made human and **reverted** - it leaked into three unrelated
  checks. The declaration belongs in the two checks that need it.

### Deployed

`py tools/deploy_iron_court.py` - 8,512,170 bytes, 1705 files verified, SHA-256 identical in
`Modpacks/` and `data/`: `ffdccd52467d1631...`. All four changes read back out of the saved pack.

## Still open

1. **None of the AI work has been seen in a live campaign.** It is measured against the model
   under harness stubs, which is not the same as a running game. The thing to watch for is an AI
   Chaos Dwarf court holding together past turn 30 and no `IRON COURT: secession` lines for AI
   factions in the first twenty turns.
2. **Neither Ambition nor Military Doctrine has been verified in a live campaign.** Both SDD plans
   stopped at PARTIAL PASS with deployment pending; deployment is now done, the campaign checks are
   not. See `.superpowers/sdd/2026-09-20-iron-court-ambition/progress.md` and
   `.superpowers/sdd/2026-09-20-iron-court-edict-loyalty/progress.md` for the exact check lists.
3. **Docs from those two plans were never written** - `docs/IRON_COURT_VS_ROME2.md`, the two
   feature handoffs, and their `SESSION_INDEX.md` lines.
4. **`Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua.bak_pre_listenerfix_20260922`**
   is sitting in the pack mirror. It cannot ship - `deploy_iron_court.py` works off an explicit
   two-file `SCRIPTS` list - but it does not belong there.
5. The 7 stale mutation anchors still need re-aiming or retiring.

### Closed 2026-09-23

- **5 - re-aimed, none retired.** All seven had gone stale because the 2026-09-21 comment pass
  deleted comment lines that sat inside the anchors; the code under them had not moved. The
  tooltip one also had its sentence reworded and still called the pre-Ambition
  `IC.share(court, slug)`, now `IC.share(faction, slug)`, so a crash would not be what catches
  it. `py tools/mutate_iron_court.py`: **207 mutants, 0 unexplained**; `--selftest` ok. Both
  member-count mutants are caught first by a fixture guard (`the fixture seats N men`), so they
  were re-run with `IC_TEST_ALL=1`: the dedicated "a bigger party walks out with more lords,
  heroes counted" check fails under both. The runner now says to anchor on code lines only.
- **4 - moved**, along with three August ToZ backups from the same folder, to
  `Modding Files/Backup/pack_mirror_bak/script/campaign/mod/`. `pack/script/campaign/mod/` now
  holds no `.bak` files.
- **1 - checked against the live saves: PARTLY FIXED.** `tools/read_save_values.py` (new; reads
  the court out of a `.save` with the game shut) over the Azeros turn 19-22 saves:
  - **Worked.** At the end of turn 19 no AI court had a governor and none had more than one
    office filled. One fixed turn later they were filling everywhere, and unsnubbed parties
    hold or rise.
  - **The three post-deploy secessions were the old code's damage.** Horns `hearth`,
    Astragoth `temple` and Slaves `chain` all went into the first fixed turn at 5-6 loyalty.
  - **Still broken: every party still falling is snubbed.** They fall at -6 to -8/turn:
    Conclave `legion` 36->29->21, qb3 `hearth` 39->33->27, Black Kraken and Bzaark `chain` ->31.
  - **Why.** Pass 2 of `ai_fill_offices` gives a claimed seat to an outsider, almost always a
    Crown man already at or near 100, when the claimant cannot seat its own man.
  - **Two reasons it cannot:** (a) the party has **no members**. `IC.roll_court` rolls parties
    at random and `IC.roll_background` deals backgrounds evenly across them, so a small AI faction
    carries empty parties; Astragoth's `temple` seceded as "a party of 0". (b) Its men fail the
    **rank bar**, which the AI still observes (Baal `hearth` has two governors and no office).
  - **The sim missed both.** It rejected "never seat an outsider" with neither case in it.
  - Expect a second wave of AI secessions around turns 25-28 in this campaign.
- **3 - partly done.** `docs/IRON_COURT_VS_ROME2.md` §2.7, §2.11 and §5 now say built, deployed
  2026-09-22, not yet seen live. The two feature handoffs and their index lines are still unwritten.
  Both plans gate them on the live checks (items 1-2), so they wait for those.

## Logs at the time of writing

`script_log_220926_2011.txt` carries three script errors, none from this mod: VCO's
`vco-disable-ca-wincons.lua` indexing a nil `victory_objectives_ie`, CA's
`wh3_campaign_bonus_values.lua` spawning into `cr_oldworld_region_bay_of_quietude` which is not on
this map, and two of CA's own duplicate-listener warnings from `lib_campaign_intervention.lua`.
No `bad_mods_report.txt`, no crash dumps.
