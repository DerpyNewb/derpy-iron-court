# Iron Court prose rewrite - partial handoff

**Date:** 2026-09-21  
**Status:** Source rewrite complete; mutation repair, review, build, and deployment still pending.

## Closed 2026-09-23

- The 13 stale anchors were repaired across 2026-09-22 and 2026-09-23, alongside the AI-loyalty
  and party-leader work; the suite is now 227 mutants, 0 unexplained, and the harness 472 checks.
  The rewritten source has shipped in every `deploy_iron_court.py` run since 2026-09-22, so the
  SHA table below is history.
- **The last player-facing "standing" is gone.** The author saw it in the intrigue panel. The
  man's number is called **influence** everywhere else on screen (`ICUI.standing_text`, the
  INFLUENCE column, the term line), so six intrigue effects (`+%d standing for him...`), the
  ambition tooltip (now `%d influence x 1.25 = 5 for his party`), the five rank-band trait
  descriptions, the three ambition-band descriptions and the trait event line were reworded.
  `gen_ic_ui.py`'s term-line measurement fixture measured the shorter word and now measures the
  real one. Identifiers, keys and `IC.TUNE` names keep `standing`. "An army standing on that land"
  is a different word and stays.
- Deployed 11:0x: 8,524,021 bytes, 1705 files, SHA-256 `2166ab422c67662f...` in both copies.
  Not yet seen in game.
- `check_lua_undeclared.py` on the UI file **alone** reports 13 names (`BUTTON_GAP`, `TUNE`...);
  they are `EX.`/`IC.` field reads and the whole-tree scan reports 0. Pre-existing, not a finding.

## Goal and subsystem

Rewrite the Iron Court runtime scripts so their comments and visible text read like normal English
instead of generated technical narration. The requested scope includes comments, tooltips, event
records, warnings, button feedback, and other player-facing Lua strings. The user also explicitly
requested a final RPFM build and deployment to the WARHAMMER III `data` folder.

The runtime behavior, identifiers, database keys, format-placeholder order, tuning values, and UI
component paths are not meant to change.

## Decisions and wording

- Runtime comments now keep engine traps, save compatibility, generator parity, UI measurements,
  and non-obvious political rules. Shouted headings, syntax narration, session history, and
  repeated explanations were removed.
- Player text consistently uses **party**, **influence**, **office**, **overseer**, and **leaves the
  court**. It avoids the old mixture of house/bloc/weight/seat/secedes terminology.
- The voice is short, blunt, and industrial. It avoids both technical jargon and fantasy prose.
- The rewrite is limited to the Iron Court runtime and the tests/tools that quote its text. It
  does not attempt a workspace-wide documentation cleanup.

## Changed files

### Maintained source

- `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua`
  - 6,380 lines became 3,727.
  - Standalone comments are now 44 focused lines.
  - Party/leader blurbs, loyalty labels, intrigue effects, and favour text were rewritten.
  - Current SHA-256:
    `908F2D630B6D2765BEC5D15DB099A5F12DA332327321D0C519C908FC6C7B14AF`.
- `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua`
  - 4,892 lines became 3,021.
  - Standalone comments fell from 2,058 to 191.
  - Tooltips, event records, warnings, empty states, error messages, and picker text were rewritten.
  - Current SHA-256:
    `C702310F27F89DC1EBCCDDAF1A4EB9552847FF1B2ABF07475B14FD041E0F3557`.
- `tools/_iron_court_harness.lua`
  - Exact wording expectations were updated without removing behavioral assertions.
  - Current SHA-256:
    `17C761140C4B91A242B26F76A97FBCE39F9C213CCE64A0CE060943FAECC90F18`.
- `tools/mutate_iron_court.py`
  - The secession-tooltip mutant now quotes `If this party leaves...` instead of the old
    `walks out` line.
  - This is only the first mutation-anchor repair. Thirteen other anchors are still stale.
  - Current SHA-256:
    `DAB77340500A23353FE316EDFA32A891223328F86C45AE0D3F0110B64F01A785`.

### Checkpoints and reports

- `.superpowers/sdd/2026-09-21-iron-court-humanize/baseline/`
- `.superpowers/sdd/2026-09-21-iron-court-humanize/model-report.md`
- `.superpowers/sdd/2026-09-21-iron-court-humanize/ui-report.md`
- `.superpowers/sdd/2026-09-21-iron-court-humanize/harness-report.md`
- `.superpowers/sdd/2026-09-21-iron-court-humanize/review-report.md`

The last review report is deliberately **SPEC FAIL / QUALITY FAIL** until mutation coverage is
repaired. Its other checks passed.

## Validation completed

The stable rewritten source passed:

```text
luac -p zzz_derpy_iron_court.lua             PASS
luac -p zzz_derpy_iron_court_ui.lua          PASS
lua tools/_iron_court_harness.lua             459 checks PASS
py tools/gen_iron_court.py --selftest          PASS
py tools/gen_iron_court.py --check             43 bundles, 56 junctions,
                                                73 traits, 563 loc rows
py tools/gen_ic_ui.py --check                  7 files, 224 components
import_iron_court.verify()                     PASS
py tools/check_lua_api.py <both runtime Lua>   0 suspect calls
py tools/check_lua_undeclared.py               15 files, 0 undeclared names
py tools/mutate_iron_court.py ambition edict   14 mutants, 0 unexplained
```

The UI line-measurement gate initially found four overlong intrigue cards. Their final compact
wording passes `gen_ic_ui.py --check`.

An unsupported `py tools/gen_iron_court.py --help` call was accidentally run during review. That
generator treats unknown arguments as a normal generation request, so it refreshed timestamps on
the eleven owned TSVs under `Modding Files/source/iron_court/`. Subsequent generator and importer
checks pass. The four ambition TSVs also compare byte-for-byte with the reviewed Task 2 snapshot;
no generated content drift has been found.

## Blocking mutation work

The prose cleanup removed comments and changed visible text that several mutants used inside their
literal anchors. A read-only scan currently reports **13 zero-match anchors**:

1. `the player's own card threatening him with his own provinces`
2. `the Crown's split count taken off its own card`
3. `a party sized by its lords when the author asked for its members`
4. `an absorbed legend seated with the house he came from`
5. `a legend refused for where he sits rather than for what he is`
6. `a hold set before the panel is known to exist`
7. `a court that closes and leaves the feed held forever`
8. `an oath that holds a party at zero after all`
9. `a roster row wired to a man, on a list that offers nothing`
10. `a party judged on the turn it was born`
11. `a house falling back to the thrall it just refused`
12. `a trait cell that never says what it is worth today`
13. `the player's own card calling his house a plotter again`

Repair each anchor against the smallest unique executable block in the current model/UI. Preserve
the behavioral fault each mutant introduces; do not delete, rename, or weaken mutants just to make
the self-test pass. The interrupted `humanize_mutations` subagent made no additional maintained
changes before this handoff.

After repairing the anchors, require:

```powershell
py tools\mutate_iron_court.py --selftest
py tools\mutate_iron_court.py ambition edict
py tools\mutate_iron_court.py
```

Expected final result: 202 anchored mutants and `202 mutants, 0 unexplained`, followed by a clean
459-check harness and an independent review changing the handoff review verdict to PASS.

## Pack and deployment state

No humanized pack has been built or deployed.

Both current pack copies are still the earlier combined Ambition/Military Doctrine build:

| Copy | Size | SHA-256 |
|---|---:|---|
| `Modding Files/Modpacks/derpy_iron_court.pack` | 8,681,404 bytes | `EB54EFA2FC5357407B10B9EB7C7D870714545287EEA599B5AB366DA537FD2677` |
| `F:/SteamLibrary/steamapps/common/Total War WARHAMMER III/data/derpy_iron_court.pack` | 8,681,404 bytes | `EB54EFA2FC5357407B10B9EB7C7D870714545287EEA599B5AB366DA537FD2677` |

The user reported RPFM open, but the last process query during handoff did not return RPFM or
WARHAMMER III. Check both again rather than relying on either observation.

Once the mutation and review gates pass:

1. Inspect `tools/deploy_iron_court.py` again and confirm WARHAMMER III is closed.
2. Start or confirm RPFM and its MCP port `45127`.
3. Run `py tools/deploy_iron_court.py --no-copy` and verify the saved index.
4. Record the new workspace pack size and SHA-256.
5. Run `py tools/deploy_iron_court.py`. The user explicitly authorized deployment to `data`.
6. Confirm workspace and game-data copies have identical size and SHA-256.
7. Run a final harness and pack-index self-test. Do not claim in-game verification unless the game
   is actually launched and its logs are inspected.

## Resume point

Start with the 13-anchor repair in `tools/mutate_iron_court.py`. Do not rebuild from the current
tree until mutation self-test, the full 202-mutant suite, and the fresh review all pass.
