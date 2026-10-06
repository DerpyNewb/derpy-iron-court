# Iron Court for Dwarfs - phase 4, grudges inside the court (handoff)

Plan: `docs/superpowers/plans/2026-10-04-iron-court-dwarfs-phase4-court-grudges.md` (8 tasks).
Spec: `docs/superpowers/specs/2026-10-04-iron-court-dwarfs-design.md`. Ledger with every ruling:
`.superpowers/sdd/iron-court-dwarfs-phase4/progress.md`. Finished 2026-10-05.

**State:** built after the final review's fixes and copied byte-identical to `data/` on
2026-10-05 (`derpy_iron_court.pack`, md5 `90518DE4`, 1867 files, verified from disk). The
backup is `Modding Files/Backup/deployed_auto/derpy_iron_court.pack.bak_pre_auto_20261005_232610`.
The pack is unpublished, so there is no Workshop folder to copy to. **Not yet seen in game.** The
author approved the Task 7 previews ("continue", 2026-10-05).

## 1. What shipped

**The book.** `court.grudges[slug] = {{code, turn}, ...}`, kept per party slot, and it
outlives the party. A Dwarf court only: `IC.grudge_write` does nothing for any other race.

| Rule | Value |
|---|---|
| Loyalty per grudge per turn | `grudge_loyalty = -1`, never fades |
| Grudges per party | `grudge_max = 4`; a full book takes no more |
| Kin of the Karak, every Dwarf party | `kin_loyalty = +1` |
| Secession and Insult countdowns | x1.5 (`DWF.tune`: `secede_turns`, `plot_provoke_clock`) |
| Save | field 19; an 18-field save loads with empty books |

**The writers.** Each wrong writes its grudge where it already took its one-off loyalty hit,
and only when the move lands:

- the Slayer Oath (murder) and Cast Out the Clan (purge, written before `remove_house`);
- An Insult to the Clan (provoke), plus a second `oath` grudge when it breaks a Blood-Oath;
- Bar Them from the Hall (unseat) and Recall Governors;
- an early dismissal (`IC.dismiss`) and a refused demand (`settle_demand`).

The words are in `IC.GRUDGE_WORDS`. The loyalty tooltip shows them as
`Grudge: Cast Out, turn 34: -1`, with a note saying how to settle one.

**Settlement.**

- **Pay the Weregild:** an `IC.PLOTS` row with `race = "dwf"`, `gold`, `sure` and `cat = "house"`. It costs 1000 gold from the treasury, settles the oldest grudge and gives +4 loyalty. It is refused on a Chaos Dwarf court and against a party with no grudge.
- **A claimed seat:** an appointment that pays `loyalty_appointed` into the office's affinity party settles one grudge.
- **AI Dwarf rulers:** `IC.ai_weregild` runs right after `IC.ai_placate`.

**The Iron Law** (Dwarf `chain`): its rule line now ends "A broken oath costs 10 more
loyalty." (`oath_broken_loyalty = -10`).

**The panel.** `ICUI.PLOT_GRIDS` builds one move grid per race, and `ICUI.use_plot_grid` picks
one when the panel opens. The Chaos Dwarf grid keeps its 16 cards; the Dwarf grid has 17.

- The weregild card prices with the treasury icon (`ICUI.gold`).
- The picker title reads "pays N gold from the treasury", and a court short of gold sees `Short <gold>`.
- A target refusal reads "No Grudge".

## 2. Rulings

Rulings 1 to 11 are in the plan's own header and stand as written. Ruling 1 is the one the
author was shown: the weregild sits in the party column, because a fifth Bonds card breaks the
card height for every race.

Execution rulings, all in the ledger:

- The Iron Law line uses phase 3's Dwarf move names.
- Phase 2's "every move has its Dwarf name" check accepts a `race = "dwf"` row as its own text.
- `PLOT_GRIDS` is in `ICUI.NOT_SCALED`.
- Check 20e in `gen_ic_ui` reads `ICUI.gold(` as a price.
- The harness builds the race grid's card count and asserts every card is drawn. The 17th Dwarf card drew blank in the preview while every check was green.
- `import_iron_court.py`'s two `lua.exe` stubs (8c, 8d) carry `RACE_ORDER` and per-race counts through `plot_stub()`. Check 8c now also compares each race's grid with `gen_ic_ui.plot_grid(plot_counts(race))`. Both checks refused once `PLOT_GRIDS` existed; the plan never touched the importer.
- The harness's Dwarf demo court holds 4000 gold, so the preview draws the weregild card affordable.
- **The author's "avoid black texts in dark background" (Task 7):** a refused plate button on a themed court keeps CA's grey inactive plate, but its label is now the plate's own cream, not `ICUI.lit_word`'s black. Measured on the drawn grey face (p5/p50/p95):
  - black: 1.3 / 1.9 / 3.8:1 (the phase 3 comment's 5.5:1 did not hold);
  - cream: 14.9 / 10.2 / 5.2:1.

  The lit gold tab keeps its black word, which `gen_ic_ui` measures at 4.5:1 on gold.

## 3. Approvals

Recorded in `Modding Files/source/iron_court_preview/phase3_approved/approvals.json`:

- **intrigue_laws**, re-approved after Task 7: the weregild card and the Iron Law line.
- **offices**, re-recorded under the author's black-text instruction. Its only change is the cream refused labels in the office picker, confirmed by re-rendering with the old ink and matching the approved hash.

The Chaos Dwarf previews are pixel-identical to phase 3's approved copies.

## 4. Gates at the finish

| Gate | Result |
|---|---|
| luac | silent |
| Harness | 1053 checks |
| `check_lua_api` | 0 |
| literal-left | 0 |
| undeclared | 1 file, pre-existing: `GGUI`, `DERPY_HUB`, `BUTTON*` |
| `gen_ic_ui` | ok, 30 files, 1910 components, plus selftest |
| `gen_iron_court --check` | 2062 loc rows |
| backdrop | 0 problems |
| importer verify | ok, 1786 pngs |
| `phase3_probe` | chd court unchanged, 1768 files |
| Mutation selftest | 1157 mutants anchored |
| Preview selftest | ok |

The six `grudge:` mutants: 6 caught, 0 unexplained.

## 5. Owed in game

A Dwarf campaign:

- An Insult to the Clan writes a grudge line in that party's loyalty tooltip.
- Pay the Weregild settles it and takes 1000 gold from the treasury.
- A claimed seat settles one.
- A Dwarf party's countdown reads the longer count.
- The refused buttons read in cream on the grey plate.

A Chaos Dwarf campaign shows none of it. An older save loads.

## 6. Final review (opus) and its fixes

The review found no Critical or Important issues and seven Minors. I re-graded three of them
to Important by what a player gets, and fixed each one test-first: the test failed before the
fix and passed after it. Each fix also has a new mutant, and both are caught.

| What a player would have seen | Fix | Check |
|---|---|---|
| An AI Dwarf court stops paying weregild when its worst party's man cannot be reached | `IC.ai_weregild` ranks every party with a grudge and tries each in turn | "an AI ruler that cannot reach its worst party's man pays the next party's weregild" |
| Putting out a man whose card reads "Term ends this turn" writes a grudge that never fades | `IC.dismiss` writes no grudge when `IC.term_left` is 0 | "putting a man out on his term's last turn writes no grudge" |
| The Record says a party paid the weregild, when the treasury paid | A gold move is logged with `IC.CROWN` as payer | "the Record says the treasury paid the weregild, not the man sent" |

The grudges checks depend on the order they run in: the existing "dismiss writes its grudge"
fails when run alone. So the before and after runs used the whole `grudges:` group with
`IC_TEST_ALL`.

**Gates after the fixes:**

- harness: 1056 checks;
- mutation selftest: 1159 mutants, all aimed at live code;
- `grudge:` mutants: 8 caught;
- Chaos Dwarf court: unchanged, 1768 files;
- importer verify: ok.

**Deferred (minor):**

- No check covers re-seating the same man in his claimed seat; a renewal must not settle a grudge.
- `6 + #ICUI.RED` in `ICUI.grey_refused` puts a number on the left of an operator.
- The grid checks list the races `("chd", "dwf")` by hand instead of reading `IC.RACE_ORDER`.
- `IC.unpack` does not cap a loaded book at the maximum or check its party.
