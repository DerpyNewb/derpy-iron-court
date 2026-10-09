# Iron Court: humanize and de-slop the player text (handover)

**Date:** 2026-10-07
**For:** the session that rewrites the Iron Court's player-facing text
**Build at handover:** `C0A47D98`, deployed to data/; harness 1088 checks; mutation suite 1218, 0 unexplained
**Status:** completed by Codex on 2026-10-07. Build `57BA1A8F` is packed and deployed to data/. See [the editing report](CODEX_IRON_COURT_TEXT_REPORT_20261007.md) and [the handover to Claude](HANDOFF_20261007_IRON_COURT_TEXT_PASS_CLAUDE.md). The inventory and baseline below describe the original brief.

## 1. The job

Rewrite what the player reads so it sounds like a person wrote it for a player. Keep every
behaviour, key, placeholder and number. Player text only: code comments are out of scope unless
the author asks.

The 2026-09-21 pass (`HANDOFF_20260921_IRON_COURT_HUMANIZE_PARTIAL.md`) did the model and UI Lua
and set the voice. Since then the mod has gained:
- the Dwarf courts;
- laws, governments and deeds;
- the Book of Grudges;
- the Record and Petitions rework;
- starting members.

The generated loc has grown from 563 rows to 2,062. The 09-21 pass never reviewed the loc at all.

## 2. The voice (already agreed; do not reinvent it)

From the 09-21 pass, confirmed by the author since:

- **Short, blunt, industrial.** No technical jargon and no fantasy purple prose.
- **Fixed terms:** party, influence, office, overseer, leaves the court, renown, the Crown.
  Dwarf courts use their own words, for example "The Throne-Sworn" for the Crown.
- **Plain words** (memory `player-text-plain-words`): no cap, accrue, rep, tick, AI, HUD,
  "standing" or "by default". Rivals are "rivals". Agents are "heroes".
- **Never** "rung". No emojis anywhere.
- **Lore over coverage:** a Dwarf line is written in Dwarf words, or the line is dropped for
  Dwarfs. It is never the Chaos Dwarf line with the nouns swapped.

Lines already in the mod that hit the voice. Use these as the bar:

- "A garrison town under a soldier costs less to keep than it should."
- "He can tell you what a barrel will do before it does it."
- "The marches keep themselves, badly and at their own expense."

## 3. Where the text lives

| Source | What | Roughly | Notes |
|---|---|---:|---|
| `tools/gen_iron_court.py` | All loc: event cards (`EVENTS`, line 1089), traits (backgrounds ~427, origins ~959, Dwarf ~1593), bundles, laws (`LAWS` 1476, Dwarf ~1801), governments (1446), offices, doctrines, party names | 2,062 loc rows | Writes `Modding Files/source/iron_court/*.tsv`. **Edit the generator, never the TSV.** |
| `zzz_derpy_iron_court_ui.lua` | Panel text: Record lines (`ICUI.intrigue_text`, `ICUI.news_text`), help pages (`ICUI.HELP`, ~6553), tooltips, headers, pickers, warnings | ~435 sentence literals | Plain English literals, not loc. |
| `zzz_derpy_iron_court.lua` | Party and leader traits (`IC.PARTY_TRAITS`: name, blurb, rule), intrigue move text, favour text | ~112 | |
| `zzz_derpy_iron_court_dwarf.lua` | Dwarf twins: `DWF.HELP_SWAP`, `DWF.PLOT_TEXT`, `DWF.FAVOUR_TEXT`, `DWF.PARTY_TRAITS`, names | ~82 | See trap 4a. |
| `zzz_derpy_iron_court_ui_map.lua` | Governors map column | ~17 | |
| `script/mct/settings/derpy_iron_court.lua` | MCT page: labels and tooltips | ~113 | Hand-written. The harness cross-checks keys, not words. |

These counts come from a heuristic scan of string literals with three or more words. Use them as
a size estimate, not as a checklist.

## 4. The traps (each has bitten before)

**a. `DWF.HELP_SWAP` is keyed by the exact Chaos Dwarf help line.**
- Reword a shared line in `ICUI.HELP` and its Dwarf twin silently stops applying.
- The harness fails a key that no shared line still reads. Move the key with the line.

**b. Format strings.**
- Keep every `%s` and `%d` in the same order.
- Keep `turn%s`-style plurals working.
- Keep the `{@icon}` and `{name}` tokens in help lines; a token no picture answers prints as written.
- Keep `[[img:...]]` and `[[col:red]]` markup.
- `ICUI.units()` decorates figures; do not hand-add icons it already adds.

**c. Width.** twui text never wraps; a line that is too long is clipped mid-word.
- `py tools/gen_ic_ui.py --check` measures help lines at their widest and the row cells.
- `py tools/check_ic_release.py` measures fit at 1600, 1920 and 2560 for both races.
- Text is measured at 1.19x PIL's font width (`GAME_FONT_WIDER`). A line that "looks fine" in an
  editor can still fail.

**d. Exact wording is asserted.**
- About 176 harness asserts pin wording: 109 `string.find(..., "literal", 1, true)` and 67
  equality checks.
- Update the expected text, but keep what each assert proves. Do not loosen a check to make it
  pass (memory `test-must-measure-not-restate`).

**e. Mutation anchors quote text.**
- After the 09-21 pass, 13 anchors went stale.
- A stale anchor is a finding. Re-aim it at the new line and keep the fault it injects. Never
  delete a mutant to go green.

**f. Generated loc must be regenerated.**
- Run `py tools/gen_iron_court.py` (no flag) after editing it.
- `deploy_iron_court.py` refuses when a TSV row count disagrees with `build()`.
- **These tools have no `--help`.** An unknown flag on the generator runs a full write, and on
  some importers a build (memory `sync-guilds-repo-has-no-help-flag`). Read the docstring.

**g. Event loc per race.**
- `IC.event_stem` gives Dwarf courts their own loc for the events in `DWF.EVENT_LOC`.
- The record is per race too (offset 200, `RACE_EVENT_OFFSET`).
- A rewritten Chaos Dwarf event body may need its `_dwf_` twin rewritten to match.

**h. No loc lookups in turn handlers.**
- Record lines are stored as slugs and resolved at draw time; a loc call inside a turn handler is
  a turn-1 crash that pcall cannot catch.
- Rewording does not touch this. **Moving text from a literal into loc might**, so do not.

**i. Binary rule.**
- `.loc` and `.pack` are never text-edited. The only routes are the TSV through the generator and
  RPFM through the deploy script.

## 5. What reads as slop here (measured 2026-10-07)

These are starting targets, not a rule list. Read the lines in context, in game or in the
previews, before changing them.

1. **Copy-paste filler on 140 trait flavour lines.**
   - Every "Party:" member trait's flavour text is "Counted with them at the Iron Court."
   - Its explanation text is the same 140 times: "The party he sits with at the Iron Court. It
     changes when a party forms, breaks away or dissolves."
   - Either write one line per party, or ask the author whether an empty flavour line is better.
   - **Not measured:** whether the trait panel draws an empty `colour_text` cleanly. Check it in
     game before shipping any blank.
2. **49 lines end in "!".**
   - Examples: "Bribe - Success!", "Secession Pending!", and "Your move has succeeded, and the
     court has taken note!"
   - The house voice is blunt; it does not cheer.
3. **Event cards that narrate the UI.**
   - 11 of 38 card bodies end in directions such as "The Record tab names both sides." or "Open
     the Iron Court: its card names the man...".
   - Keep a pointer only where the player has to act. A card that ends in a tab name on every
     event reads like a manual.
4. **"weight" in player text.**
   - The 09-21 pass retired it, but it is back in 6 help lines and 2 event bodies
     (`party_joined`, `party_drawn`).
   - **Author decision:** what the player-facing word is ("share" is already used for the
     percentage).
5. **Template closers.**
   - 62 trait flavour lines end ", and ...", for example "Loud and cheerful, and entirely without
     mercy."
   - "As it always has" appears 7 times across the law descriptions, in both races.
   - Vary the rhythm. Not every line needs a twist at the end.
6. **Spaced hyphen as a dash** in pickers and headers.
   - Example: "Choose who takes %s - needs %s influence, held for %d turns".
   - Use a colon or two sentences. The em dash is not a fix.
7. **Parenthetical tab pointers in warnings.**
   - Examples: "Seats you can fill now: %d (Offices tab)." and "(Court tab)", "(Petitions tab)",
     "(Laws tab)".
   - One shape repeated down the notice list. Consider whether the tab glow already says it.
8. **Mirror-image race lines.**
   - "Born underground and never entirely comfortable above it." (Chaos Dwarf) and "Born deep
     underground and never entirely comfortable above it." (Dwarf) are one line with a word added.
   - Lore over coverage: write the Dwarf one as a Dwarf, or drop it.

General tells to watch for anywhere:
- "not X, but Y";
- tricolons used for rhythm;
- intensifiers such as "entirely", "truly", "simply";
- "It/This" openers that refer back to nothing;
- second person in third-person flavour text;
- explaining a mechanic twice on one screen.

If a humanizer or anti-slop skill is installed in the session, run it as a checklist over each
batch. It does not replace reading the lines in context.

## 6. Suggested order

Work in batches small enough to review, and render each one before moving on.

1. **Event cards** (`EVENTS` in the generator, plus `_dwf_` twins). Fewest lines and most seen.
2. **Record lines** (`ICUI.intrigue_text`, `ICUI.news_text`). Just reworked today; check the
   Crown and "not yet at court" lines still read well.
3. **Help pages** (`ICUI.HELP`, then `DWF.HELP_SWAP` keys and values together).
4. **Trait flavour** (backgrounds, origins, the 140 member traits: author decision first).
5. **Laws and governments**, both races.
6. **Party and leader traits, intrigue moves, favours** (`IC.PARTY_TRAITS`, `DWF.PLOT_TEXT`, ...).
7. **MCT page** last. Its tooltips are read once and are the least seen.

## 7. Gates, per batch and at the end

```powershell
py tools\gen_iron_court.py                 # rewrite TSVs after generator edits
py tools\gen_iron_court.py --check
py tools\gen_ic_ui.py --check              # widths
& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua
py tools\mutate_iron_court.py <names>      # the mutants near what you touched
py tools\preview_iron_court.py             # then LOOK at the PNGs for every touched view
py tools\check_ic_release.py               # fit and contrast, both races, three screens
```

At the end:
- the full `py tools\mutate_iron_court.py`, guarded: copy the six Lua files and the harness to
  `Modding Files/Backup/mutation_guard_<date>/` first;
- **never edit the Lua while a mutation run is going.** Its restore writes back the copy it read
  at the start, and it wiped edits twice on 2026-10-07;
- `py tools\deploy_iron_court.py` with RPFM open. It deploys to data/ itself when the game is shut;
  otherwise use `--deploy-only --wait`;
- `py tools\check_ic_release.py --pack`, which compares every loc line in the saved pack with
  `build()`.

Then:
- **Patch notes:** one short phrase per change in
  `docs/sessions/PATCH_NOTES_20261006_IRON_COURT_DWARFS.md`, for example "Reworded event cards".
  No reasons.
- **GitHub:** the public Iron Court repo (memory `iron-court-github-repo`) mirrors this text.
  Sync with `tools/sync_iron_court_repo.py` **only when the author asks**.

## 8. Open questions for the author

- **"weight":** what is the player-facing word, or is it fine as defined on the help page?
- **The 140 "Counted with them" member-trait lines:** one flavour line per party, or none?
- **Event cards:** keep a "where to look" pointer at all, or only on cards that need an action?
- **Garrison captains:** their house and background traits currently show two Trait Gained
  messages per captured settlement (`HANDOFF_20261007_IRON_COURT_LIVE_BRIDGE_CHECKS.md` §13).
  This is not text, but it is noise the player reads. Quiet or not?
