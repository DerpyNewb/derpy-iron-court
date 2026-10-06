# Iron Court for Dwarfs - phase 5, the Book of Grudges (handoff)

Plan: `docs/superpowers/plans/2026-10-04-iron-court-dwarfs-phase5-book-of-grudges.md` (6 tasks).
Spec: `docs/superpowers/specs/2026-10-04-iron-court-dwarfs-design.md`, section 6. Ledger with every
ruling: `.superpowers/sdd/iron-court-dwarfs-phase5/progress.md`. Finished 2026-10-06.

**State:** built after the final review's fix and copied byte-identical to `data/` on 2026-10-06 (`derpy_iron_court.pack`, md5 `500C7AB0`). See section 5. **Not yet seen in game.** The author approved
the Court tab picture with the Book line ("continue", 2026-10-06).

## 1. What shipped

A Dwarf court reads CA's Book of Grudges. A Chaos Dwarf court reads none of it.

**Weighing.** CA keeps grudge points on the offender's armies and settlements, in two pooled
resources: `wh3_dlc25_dwf_grudge_points_enemy_armies` and `..._enemy_settlements`. They are not
kept per Dwarf faction, so a faction's weight is the same number for every Dwarf court.

- `IC.book_weight`, `IC.book_list` and `IC.book_names` sum those two pools for every faction the court has met.
- They skip garrisons (`military_force_list(true)`), dead factions and Dwarfs.
- One sum per faction per turn is cached in the unsaved `IC._book`. Only the turn path fills it (`IC.book_list(fk, true)`); the panel only reads it.

**Bands.** `IC.book_tick` runs at the end of `IC.turn`, caught like the parties' turn.

- Reaching 500, 1000 and 2000 calls `cm:apply_dilemma_diplomatic_bonus(own, them, -1 / -2 / -3)`.
- Each band fires once, in order, and is never reversed.
- `court.book[faction] = bands crossed` is saved as field 20, so a load never fires a band again. A 19-field save loads with no bands crossed.

**Treaties.** Listener `ic_book_peace` on `PositiveDiplomaticEvent`.

- It fires on peace, trade or any alliance with a faction whose saved bands reach `book_named` (1000), whichever side proposed.
- It writes a `peace` grudge in the Clan Warriors' and the Ancestor Priesthood's books, at most once each per turn, then saves.
- It reads the saved bands, not the live weight, because CA's own listener on the same event wipes an ally's points.

**Deeds.** Listener `ic_deed_grudge` on `PooledResourceChanged`, through `on_deed`.

- When CA pays the faction's own `wh3_dlc25_dwf_grudge_points`, the new `grudge` deed gives `deed_grudge = 3` renown to legion and, through the new DEEDS field `also`, to temple.
- Only a rise counts, so spending points on a ritual is no deed.

**Panel.** A new cell, `ic_book` at `{48, 943, 866, 26}`, sits under the Crown's box on the Court tab, on a Dwarf court only.

- It reads "The Book names: ..." with the top three names, cut to fit, or "The Book names no enemy yet."
- Its tooltip gives each name's grudge points, the three band lines, and which two parties a treaty wrongs.

## 2. Rulings (executor's; the plan's seven stand as written)

- **The tests:** this phase's checks are one `do ... end` block, closed by `end -- BOOK (plan 2026-10-04 phase 5)` and sitting above the run's last check. The Dwarf court local is `BK` because `DW` is phase 2's helper table. The turn, treaty and deed checks call `IC.register()` first.
- **Dwarf deed text:** none existed. The shared `ICUI.DEED_TEXT` is Chaos Dwarf-worded, so a Dwarf court's deeds tooltip offered "the Tower's rites and temples of Hashut".
  - Added `ICUI.RACE_DEED_TEXT.dwf`, read through `ICUI.deed_text`, with only the parties `DWF.DEEDS` names: legion "your victories and grudges settled", temple "grudges settled", tower "research".
  - The plan's "temples to the Ancestors" was dropped because the Dwarfs have no temple deed.
- **Book cell plumbing:**
  - The check sizes `ic_book` from `PANEL_XY`, because the fake tree's cells are 10px.
  - The layout-offset check declares `ic_book`.
  - `BOOK_GAP` joins `SCALED_SCALARS`.
  - `draw_book` writes `ICUI.fit_cut(comp("ic_book", panel), ...)` literally, because check 20g reads that call.
- **Backdrop check:** `make_ic_backdrop.TEXT_CELLS` gains `ic_book`, and it is measured even though `ic_lv_hand` (the Laws vote's plate, never up on the Court tab) covers its box. p95 contrast: 10.3:1 on the Dwarf backdrop, 6.9:1 on the Chaos Dwarf one.
- **The Dwarf preview is the shipped Lua's dump.**
  - The hard case, CA's three longest faction names, goes in through `race_dump` and `IC_DUMP_BOOK`.
  - The race path now re-cuts every `CUT_CELLS` cell with PIL's measure. The dump's own cut uses the harness's 8px-a-letter stub and drew the line through the column divider.

## 3. Gates

- Harness: 1064 checks.
- `check_lua_api`: 0.
- literal-left: 0.
- undeclared: pre-existing only.
- `gen_ic_ui`: ok, 1914 components (`ic_book` in all four panel files), plus selftest.
- `gen_iron_court --check`: ok.
- Backdrop: 94 cells measured.
- Chaos Dwarf court: unchanged, 1768 files, after re-recording `phase3_probe`'s baseline.
  - The two Chaos Dwarf panel files differ from the deployed copy only by the hidden `ic_book` cell and the GUIDs renumbered after it. This was diffed with every GUID blanked out.
  - The old baseline is in `Modding Files/Backup/`.
- The eleven `book:` mutants: 11 caught, 0 unexplained. One older mutant, "a turn ending on a band it does not wear", went stale when the Book's call landed before `IC.save`. It was re-aimed and is caught.
- Mutation selftest: 1170 mutants, all anchored.

The gate script returned exit 0 while its log held both failures, so read the log, not the exit code.

## 5. Build and deploy

- Pack: `derpy_iron_court.pack`, md5 `500C7AB0`, 15,087,079 bytes, 1867 files.
- Where: byte-identical in `data/` and `Modding Files/Modpacks/`. Built 2026-10-06 after the final review's fix.
- Backup of the pack it replaced (`90518DE4`): `Modding Files/Backup/deployed_auto/derpy_iron_court.pack.bak_pre_auto_20261006_103554`.
- Read back from `data/`: `IC.book_tick`, `ic_book_peace`, `ic_deed_grudge`, `ICUI.draw_book`, `ICUI.BOOK_REMEMBERED`, and `ic_book` in both Chaos Dwarf panel files are all present.
- Gates at this build: harness 1065, mutation selftest 1172 anchored, Chaos Dwarf court unchanged at 1768 files.
- The pack is unpublished, so there is no Workshop folder.

## 4. Owed in game (phase 6)

- **A band firing:** check the named faction's attitude line on the diplomacy screen, and whether the regard moved on their side, ours or both. `(own, them)` follows CA's actor-then-affected order, which should move theirs.
- **A treaty with a faction named at 1000 or more:** one `peace` grudge each in the Clan Warriors' and the Priesthood's books.
- **A grudge settled through CA's own Book:** both parties gain renown.
- **The Book line at 1600x900 and 2560x1440:** check the cut.
- **Whether a band's regard penalty fades** over the turns: if it does, "never reversed" is weaker than written.
- **Confederating a Dwarf faction:** whether it raises the host's own grudge points. If it does, that is a free grudge deed, the same kind `confed_turn` already blocks for rites.
- **The Book's tooltip after a victory:** beat a faction named at 1000 or more down below 1000. It must still be listed under "Remembered:".

## 6. Final review (opus) and its fix

The review found 0 Critical, 2 Important and 5 Minor.

| Finding | What a player would have seen | Outcome |
|---|---|---|
| I1 | The player beats a named faction below 1000 points, or off the line, then makes peace. Two parties take a grudge that never fades, and nothing on screen said so. | **Fixed.** The tooltip now ends "Remembered: <every faction the Book has ever named at 1000>". Its sentence says "ever named ... even after its points fall". Check: "book: the tooltip names every faction the Book remembers, whatever it carries now", RED then GREEN. Two new mutants, both caught. |
| I2 | A band moves only the named faction's regard for the Dwarfs. An AI Dwarf court's own regard never moves. | **Kept** as the spec's single call. The direction check is owed in game (section 4). If the engine applies the call one way only, the fix is a mirrored `(them, own)` call. |

**Deferred (minor):**

- `book_tick` saves a faction's bands after its loop, under one `pcall` for every faction. So a throw on band 2 re-applies band 1 each turn and skips the factions after it. Fix: write per band and `pcall` per faction.
- No mutant guards `book_list`'s `if fill` against the panel filling the turn's cache after the turn path has run.
- A battle that settles a grudge pays the Clan Warriors both the battle deed and the grudge deed, which reaches the turn cap from one fight. This matches the spec's section 8.
- `make_ic_backdrop`'s `covered()` does not know which view a plate is on. `ic_book` is special-cased by name.
- `book_peace`'s once-a-turn limit also merges treaties with two different named factions into one grudge.
- Field 20 accepts a non-integer band count from a corrupted save. Fix: `math.floor` it.
