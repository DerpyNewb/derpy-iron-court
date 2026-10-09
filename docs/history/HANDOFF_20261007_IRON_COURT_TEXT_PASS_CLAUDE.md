# Handover to Claude: Iron Court player text

2026-10-07. Workspace: `G:\Modding for resources`. Run tools from the workspace root.

## State

Completed, packed and deployed to data/. The deployed pack is byte-identical to the verified build. Not yet checked in game; no Workshop upload or GitHub sync.

Read [the report](CODEX_IRON_COURT_TEXT_REPORT_20261007.md) and [the original brief](HANDOFF_20261007_IRON_COURT_TEXT_PASS.md).
The report gives before/after examples, changed files, verification and the author decisions retained.

## What changed

- 480 of 2,062 generated loc rows; 82,022 to 74,680 characters.
- 236 Lua/MCT literal edits across the model, Dwarf race, UI, governor map and MCT file.
- Shorter events, Record lines, Help and tooltips; Dwarf-specific trait and move flavour;
  tighter laws and governments; quieter move-result wording.
- Seven shared Help replacements paired with their exact Dwarf swap keys, plus seven Dwarf values.
- Wording expectations, mutation anchors and preview readers updated without dropping assertions or faults.

Keys, numbers, placeholders, markup and mechanics are unchanged. No turn-handler loc calls,
layout edits, art changes or garrison-notification changes. The parties script is unchanged.

## Source, output, pack and game copy

The maintained sources are `tools/gen_iron_court.py`, the four text-bearing Iron Court campaign
Lua files and `Modding Files/pack/script/mct/settings/derpy_iron_court.lua`.
The generator owns `Modding Files/source/iron_court/`; changed outputs are `loc.tsv`,
`effect_bundles.tsv` and `missions.tsv`. Other TSVs are unchanged. Never hand-edit them.

The destination is `Modding Files/Modpacks/derpy_iron_court.pack`; the game copy is
`F:\SteamLibrary\steamapps\common\Total War WARHAMMER III\data\derpy_iron_court.pack`.
Both baseline packs were C0A47D98 and all six staged scripts matched the saved pack before editing.
Baseline pack copies are under `Modding Files/Backup/iron_court_text_20261007/`.

## Verification

Generator, UI width gate and 1,088-check Lua harness pass. Fit and contrast pass for both races
at 1600, 1920 and 2560. All previews rendered; every rendered view was inspected in contact sheets,
with full-size checks of the two Intrigue views, Dwarf Record and Dwarf Help.

The mutation runner's self-test passes with 1,218 anchors. Full-run result:
1218 caught, exit 0; guarded files restored byte-for-byte: True.

Guards: `Modding Files/Backup/mutation_guard_20261007_text_pass_lf/`.
After the full run, one Help sentence was clarified. The self-test and all 17 Help mutants
passed again, with final files restored byte-for-byte. The final guard is
`Modding Files/Backup/mutation_guard_20261007_text_pass_final/`.
Do not edit Lua while a mutation run is active. The first self-test exposed a line-ending change;
LF was restored before the successful run. Baselines and full logs are in
`.skilltree_cache/iron_court_text_20261007/`.

## Author decisions retained

1. Keep “weight”, or replace it with “strength” while “share” remains the percentage.
2. Keep the 140 member-trait flavour lines, or give them party-specific prose.

Both questions were sent during the pass and had no reply at writing. Existing flavour was kept. No blank flavour was introduced. The shared mechanical explanation
was shortened; the pending choice concerns flavour, not the membership rule.

Routine event pointers were trimmed; cards needing an answer retain directions.
The garrison-captain Trait Gained messages remain: changing them would exceed a text pass.

## Factual questions

- Dutiful says “+1 with one” office but grants +1 for one or more offices.
- The Reckoners' Tariff flavour implies a higher charge at the gate, while its tariff-income
  effect is negative. Confirm whether the wording describes income or charges.

No factual or balance correction was applied to those lines.

## Next steps

Review the two author choices and factual questions. Check the new text in game, especially
Help, Dwarf move cards, event cards and trait flavour. Offline previews do not establish live fit.
Do not suppress trait notifications or rename parties as part of a wording follow-up.

If the author asks for GitHub sync, use `tools/sync_iron_court_repo.py`; this pass does not sync
or upload. Patch notes are in `docs/sessions/PATCH_NOTES_20261006_IRON_COURT_DWARFS.md`.

## Saved-pack baseline

The F4C63911 snapshot remains in Backup. This pass intentionally changes its wording, so tools/check_ic_release.py now pins the reviewed 2026-10-07 text baseline, 57ba1a8f5cad16246b1577a35738fce5, 15104619 bytes, saved as Backup/iron_court_text_20261007/derpy_iron_court.pack.text_baseline_57ba1a8f. Before resetting that expectation, audit_pack.py compared all 1,867 saved paths and decoded tables with the C0A47D98 pack: no path, non-text cell, schema or row-count change; all scripts matched maintained source and all tables/loc matched the generator. Eleven otherwise identical DB fragments differ only in their regenerated GUID header. The comparator logic is unchanged, still checking every existing row and loc line exactly. Only pinned snapshot metadata and explanatory strings changed; its planted-fault self-test passed.

Build MD5: `57ba1a8f5cad16246b1577a35738fce5`.

## Follow-up by Claude, same day: the author's five (build `91703079`, deployed)

Author: "apply the two fix and 1. strength, 2. one per party 3. silent traits".

- **Dutiful**, both races: the rule reads "+2 with no seat, +1 with any". The code gives +1 for one office or more.
- **The Reckoners' Tariff**: "Traders pay at the gate and come less often." The law cuts tariff income 10% and adds 5% GDP; the old text implied more tariff money.
- **weight -> strength** in the eleven player lines: six Help lines, the two event bodies (`party_joined`, `party_drawn`), the Governors column and tooltip, and the MCT label and tooltip. Keys, identifiers, `IC.TUNE` names and the `{levels_per_weight}` token are unchanged. The Dwarf move text already said "influence" and was not touched.
- **One member flavour per party**: `MEMBER_FLAVOUR` and `DWF_MEMBER_FLAVOUR` in `gen_iron_court.py`, ten lines each (the Crown, a confederate house, eight parties), shared by a party's six rolled names.
- **Garrison captains stamped quietly**: `ic_born` passes `IC.is_colonel(character)` as the quiet flag. A recruited lord still shows his two cards.

Gates:
- harness 1088 checks, OK: six expected strings now say strength, and the Trait Gained check now also births a colonel and asserts 0 cards;
- one new mutant (the colonel stamped loudly), caught; two Governors-row anchors re-aimed; runner self-test: 1219 anchored;
- `gen_iron_court --check`, `gen_ic_ui --check` and `check_ic_release` fit and contrast are clean; Help and Governors previews looked at;
- `tools/preview_iron_court.py` retypes the Governors row's `l3` text rather than reading it from the Lua, so it is updated by hand. It is the one preview string that can drift from the shipped text;
- built `91703079`, deployed byte-identical to data/;
- the read-back diff from `57BA1A8F` was exactly 144 loc lines and the Tariff's bundle row; `check_ic_release.py` was re-pinned to `91703079` (copy in `Backup/iron_court_text_20261007/`);
- full mutation run (`mutation_guard_20261007h/`): **1219 mutants, 0 unexplained**, exit 0. All Lua files, the MCT file and the harness are byte-identical to the guards afterwards.

**Line endings:** every Iron Court Lua file and tool is LF. Git Bash's `grep -c $'$'` reports every line as CRLF on these files and is not a test; count `b"
"` in Python.
