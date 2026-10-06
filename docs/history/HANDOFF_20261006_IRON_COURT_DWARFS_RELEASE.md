# Iron Court for Dwarfs - phase 6, the release pass (handoff)

Plan: `docs/superpowers/plans/2026-10-04-iron-court-dwarfs-phase6-release.md` (9 tasks).
Spec: `docs/superpowers/specs/2026-10-04-iron-court-dwarfs-design.md`. Ledger with every ruling:
`.superpowers/sdd/iron-court-dwarfs-phase6/progress.md`. Phases 1-5 are each in their own handoff;
this one ships them together.

## 1. What shipped

- Build `F4CF5CA4`: MD5 `f4cf5ca4dfa28c4ff9638e42b8be3ea3`, 15,087,079 bytes, 1867 files.
- Where: byte-identical in `data/` and `Modding Files/Modpacks/`, built and deployed 2026-10-06.
- Backup of the pack it replaced: `Modding Files/Backup/deployed_auto/derpy_iron_court.pack.bak_pre_auto_20261006_130017`.
- **Pushed to GitHub** as `d163830` (2026-10-06). There is no Workshop entry.
- **Not yet seen in game.** Section 7 is the checklist.

## 2. Gates

The harness has **1070 checks**. That is 1065 at the start of the phase, plus these five:

- "both races: a Dwarf player beside a Chaos Dwarf court, fifty turns, no cross-talk"
- "both races: a Chaos Dwarf player beside a Dwarf court, fifty turns, no cross-talk"
- "both races: Dwarf courts switched off mid-campaign, the Chaos Dwarf court runs on"
- "with no scrolling list, the help page hides the rows the last tab drew into the panel" (section 3)
- "with no scrolling list, the Governors view hides the rows the last tab drew into the panel" (section 3)

The other gates:

| Gate | Result |
|---|---|
| `check_lua_api` | 0 |
| literal-left | 0 |
| undeclared | the pre-existing UI names only |
| `gen_ic_ui --check` | ok, 30 files, 1914 components |
| `gen_ic_ui --selftest` | ok |
| `gen_iron_court --check` | ok, 2062 loc rows |
| backdrop | 0 problems |
| importer verify | ok |
| Chaos Dwarf court | unchanged, 1768 files |
| preview selftest | ok |
| deploy | "gates green" |

**One ruling on the fifty-turn scenarios.** The plan's fixture stubbed `IC.book_weight` both to feed the greenskins' points and to count who asked. But `IC.book_tick` weighs through `IC.book_list` and `book_sum`, never through `IC.book_weight`, so the stub fed nothing. The shipped code is unchanged. Instead:

- the fixture puts the points on a real greenskin army, rising 45 a turn;
- a read is counted against whichever court's turn is running.

## 3. Mutation run

The run had **1179 mutants**, and two survived. Both are now caught, so **0 are unexplained**.

The guard copies and the hash lists are in `Modding Files/Backup/mutation_guard_20261006/`.

- All six shipped Lua files came back byte-identical to the guards.
- 1837 generated files were regenerated, and their hashes match the "before" list exactly.
- The run was orphaned when a session ended about 45 minutes in, but it kept running. It was waited out by its process ID, not restored mid-run.

**The seven "both races" mutants** are all caught. Run again against only the new checks, each is still caught:

- the Dwarf-player scenario catches six of them: the race cache keyed by nothing, the race read off the player, one grudge book for every court, a grudge written into a Chaos Dwarf court, the Book kept for every court, and a key built without its race;
- the switch-off check catches "the Dwarf courts switch ignored".

**The two survivors**, "the last tab's list left under the help page" and "the Governors view shows the last tab's rows":

- **Why they looked equivalent:** normally refresh's `list_drop` destroys the scrolling list and the rows inside it.
- **Why they are not:** when the list cannot be created, `ICUI.list_items` draws one window of rows straight into the panel. Then only the help page's and the Governors view's own hides clear them.
- **The fix:** the two checks named in section 2. They refuse the list's creation and assert the Record really drew rows into the panel. Both mutants are now caught.

## 4. Fit and contrast

`tools/check_ic_release.py`, written this phase, checks both races at three screen sizes:

| Race | Screen | Fit findings | Cells measured | Worst cell (contrast) |
|---|---|---|---|---|
| chd | 1600 | 0 | 94 | `ic_row_b[6]` 4.63:1 |
| chd | 1920 | 0 | 94 | `ic_row_b[6]` 4.61:1 |
| chd | 2560 | 0 | 94 | `ic_row_c[6]` 4.60:1 |
| dwf | 1600 | 0 | 94 | `ic_row_crest[10]` 4.56:1 |
| dwf | 1920 | 0 | 94 | `ic_row_crest[10]` 4.56:1 |
| dwf | 2560 | 0 | 94 | `ic_row_crest[10]` 4.55:1 |

No dim or cell change was needed. The Dwarf tab ribbons are phase 3's gate: `gen_ic_ui.check_dwf_contrast`, called from `check()`.

## 5. The saved pack

`check_ic_release.py --pack` reads the saved pack with RPFM shut. Result:

- **0 findings.** Every table matches `gen_iron_court.build()` cell for cell.
- **The Chaos Dwarf court did not move.** Every F4C63911 row and loc line is unchanged. The snapshot was found by MD5 at `Modding Files/Backup/deployed_auto/derpy_iron_court.pack.bak_pre_auto_20261004_215550`.
- **Not compared:** the eight `*_colour_hex` columns, which RPFM derives and the binary does not store.

| Table | Rows | F4C63911 |
|---|---|---|
| effect_bundles | 146 | 73 |
| effect_bundles_to_effects_junctions | 216 | 112 |
| character_traits, character_trait_levels, trait_info | 280 each | 146 each |
| loc | 2062 | 1116 |
| campaign_groups, _members, _member_criteria_values, event_feed_message_events | 36 each | 36 each |
| trait_categories | 14 | 14 |
| factions | 4 | 4 |
| missions | 2 | 2 |
| campaign_payload_ui_details | 1 | 1 |

The other read-back checks:

- **`check_effect_bundle_loc`:** 0 findings over 146 bundles.
- **`check_effect_signs`:** exit 0. Every `_dwf_` row it prints is a deliberate penalty:
  - the 14 vacant-seat costs;
  - the contested and lost control bands;
  - one per Dwarf law, 16 in all.
- **Paths:** 1867 paths, none in upper case.
- **Staged Lua:** byte-identical to the files staged.

## 6. Previews

All 72 pictures were rendered from the shipped Lua: 11 Chaos Dwarf views and 13 Dwarf views, each at three sizes. The Dwarf set also draws the Record and Help tabs.

The sheets are `Modding Files/source/iron_court_preview/release_sheet_chd.png` and `release_sheet_dwf.png`.

The author approved them: "approved" (2026-10-06).

## 7. In-game checklist (build F4CF5CA4) - tick each, note what you saw

Settings: MCT on, Default difficulty, UI scale 100%. Check the opener at 1600x900,
1920x1080 and 2560x1440 (Options > Graphics > resolution).

**A. Dwarfs, Karak Kadrin (Ungrim Ironfist), Immortal Empires**
- [ ] Turn 1: the court button sits on the Dwarf top bar beside the Book of Grudges bar, not over it, at all three resolutions.
- [ ] The panel opens in the Book of Grudges look: blue ribbon tabs, the open tab gold, red-ink knotwork card frames, the dimmed Dwarf backdrop. No Hell-Forge art anywhere.
- [ ] Title reads "The Council of Karak Kadrin". The throne plate reads "The Throne of Karak Kadrin" over Ungrim's name, and the words fit the plate.
- [ ] Offices tab: the Great Hall, two wings of seats facing the throne, no ziggurat; 2/4/4/4 seats; Fill Empty Seats under the doors.
- [ ] Court tab: the government is The War-King. Every party, office, law and move name is a Dwarf one; no Chaos Dwarf word on any tab, tooltip or message.
- [ ] Laws tab: Craft, Tribute, Ancestors, War, each starting on its first law.
- [ ] A grudge written: use Cast Out the Clan on a party. Its loyalty breakdown gains a line "Grudge: Cast Out, turn N" costing 1 a turn; the Record logs it written.
- [ ] Settled by weregild: Pay the Weregild on that party. Gold is spent, the grudge line leaves the breakdown, loyalty rises a little, the Record logs it settled.
- [ ] Kin of the Karak: every party's breakdown shows +1 a turn.
- [ ] Secession countdown: push one party to the bottom of its loyalty after turn 10. Its countdown shows 8 turns (a Chaos Dwarf party shows 5 on Default).
- [ ] The Book: once you have met a few factions, the Court tab shows "The Book names:" with three factions and their figures.
- [ ] A Book band firing: the turn a named faction's figure passes 500, its attitude toward you drops (diplomacy screen, its attitude breakdown, before and after). It does not drop again the next turn.
- [ ] The Book's tooltip after a victory: a faction once named at 1000 or more and since beaten below it is still listed under "Remembered:".
- [ ] Save, quit to menu, load: grudges, the Book list and the court are as they were; no band fires again on the first turn after the load.

**B. Dwarfs, Clan Angrund (Belegar Ironhammer)**
- [ ] The court opens with Clan Angrund's own title and throne caption; the government is The Iron Law.
- [ ] Ancestor Oath, Oath on the Anvil and Stand His Patron each cost a third less than in Karak Kadrin.

**C. Chaos Dwarfs (any Chaos Dwarf lord)**
- [ ] The court looks exactly as before this release: Hell-Forge tabs, the ziggurat, the court's own backdrop. No Dwarf word, picture or rule anywhere; no grudge lines; no "The Book names:".
- [ ] The MCT page has a "Dwarf courts" switch. Turn it off mid-campaign and end turn: nothing in your own court changes.

**D. The throne caption on a minor faction**
- [ ] With a mod that makes Dwarf minor factions playable, start as Barak Varr or Zhufbar: the throne plate reads "The Throne of" that faction over its leader's name and fits. Without such a mod, mark this "not checked".

The in-game checks owed by phases 3, 4 and 5 are in their own handoffs (phase 4 section 5, phase 5 section 4).

## 8. Open

- **The checklist:** every unticked item in section 7, and the in-game checks owed by phases 3-5.
- **The Workshop upload:** the author's separate decision. After a first publish, the `data/` copy moves to `Modding Files/Backup/`, or the game sees two packs.
- **Out of scope** (spec section 12): custom Dwarf rebel crests, and the Age of Reckoning score.
- **Still open from the UI_POLISH handoff** (sections 1 and 6):
  - Not built: votes on seats and governors, which is laws sub-project 2.
  - Unfixed:
    - Black Kraken's wholesale party change between the turn-19 and turn-20 saves;
    - the rebel pool running out;
    - the Hold/leader minor and the one-turn-old-rules government minor;
    - the deeds minors.
  - Owed in game: the shader-effect looks.
- **Deferred minors:** phases 4 and 5 list them in their final-review sections.
