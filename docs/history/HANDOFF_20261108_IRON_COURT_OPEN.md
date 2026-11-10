# Iron Court: what is still open, 2026-11-08

**Current for the Iron Court.** It follows
[WORKSHOP_REPORTS_20261108_IRON_COURT.md](WORKSHOP_REPORTS_20261108_IRON_COURT.md) and
[HANDOFF_20261102_IRON_COURT_AI_WARS_DISLOYAL_ARMIES.md](HANDOFF_20261102_IRON_COURT_AI_WARS_DISLOYAL_ARMIES.md).
No code changed in this session.

## State

- **Live build:** `205EE2345C77D67FB52FF734833AA964`. Workshop item 3832328087, uploaded 2026-11-08 17:20,
  manifest 90993284009659620 (governor scope fix, section 0). Before it: 14D3A767 at 13:47, 3E6601FF at 08:46.
- **Where it lives:** in the Workshop folder only. Never put a copy in `data/`, because it would hide the Workshop
  copy. `tools/deploy_iron_court.py` deploys there.
- **GitHub:** synced to `4a5ee39` (build 205EE234), pushed 11-08.
- **Tests (before 11-08's change):** harness 1247 checks and release gate 0 findings. The full mutant run was last done on 11-02 (1,450, none
  stale) and was not repeated for the last two fixes. Those fixes each gained their own mutants (2 for 3E6601FF).

## 0. Done 11-08 (evening): governor bonuses stacked across the realm - build 205EE234

Lingongrova (11-08) and Nerberius (11-05) reported -100% Workload and +34/+60 Control "from faction". **Ours**,
not Drill of Hashut: the governor base bundle goes on one province but its Control and Workload (Dwarfs: growth)
were `faction_to_province_own`, which on a province bundle reaches EVERY province of the faction, so each governor
stacked his bonus on the whole realm. Measured in game (Dwarf staged fixture, +50 Control custom bundle on
Karaz-a-Karak's province only): Karak Kadrin, no bundle, Control 0 -> 48 in one turn. Memory
`faction-scope-on-province-bundle-is-realm-wide`.

Fix: `GOVERNOR_BASE` is CA's edict Control plus Labour loss -5% (author's choice: CA ships no province-scoped
Workload); Dwarfs edict Control plus commandment growth; all `province_to_province_own_unseen`. `IC.GOV_ORDER_EFFECT`
is the edict key. `check_gov_rank_constants` refuses a non-`province_to_*` governor effect (proven on both races).
Harness 1248, 58 governor mutants caught (full run not repeated), release gate 0 findings, snapshot re-pinned to
205EE234. An old save's custom bundle keeps the old effects until the next turn's reapply.
Not yet seen in game: the new bundle's Labour loss line, and Control staying in one province with the real bundle.

## 1. Done 11-08: the war council's numbers are on the MCT page

Build `14D3A767777FE01C82D825A0C20DA576` (Modpacks; deployed to the Workshop folder by `deploy_iron_court.py
--deploy-only --wait` once the game closed). **Uploaded 2026-11-08 13:47**, manifest 1987420861875332493 (Steam's
workshop_log: OK), with patch notes; upload config in `Modding Files/Backup/iron_court_upload_20261108b/`.

- `war_prep_turns` (1 to 10, default 3) and `plot_council_cost` (0 to 500 in steps of 25, default 150) appended to
  `IC.TUNE_ORDER` and added to `IC.TUNE_START`, so no difficulty sets them and every difficulty reads the slider. The
  MCT page files them under a new **War Council** section, from the `STARTS` table (its rows now take an optional
  section). Prep turns starts at 1, not 0: a vote passed with Pass now would be declared next turn, so "0 turns
  later" would be untrue.
- The move's effect text ("declared 3 turns later") is built at load, before the save's numbers apply, so
  `ICUI.plot_effect` rewrites it from `IC.TUNE.war_prep_turns`, as it does for provoke and embezzle.
- An older save is two fields short and reads both defaults (harness checks it).
- Full mutant run 11-08: 1,458, 2 unexplained, both settled. "a growing row says nothing" was a stale anchor
  (5DA3DF5E's "strength N of M" wording), re-aimed and caught. "gov fx: the glow drawn with governments off" is
  equivalent code (`ICUI.gov_moving` already reads `IC.governments_on` through `IC.gov_drift_on`) and was removed
  with a note; it survived the pre-change harness too. Now 1,457 mutants, selftest clean.
- Harness 1248 checks (new: "the war council's two numbers are read on every difficulty, and the move says the
  wait"), 3 new mutants all caught, release gate `--pack` 0 findings (snapshot unmoved: Lua only), `check_mp_sim
  --staged ic` no desyncs. Nitefog's draft reply updated.

## 2. Owed in game: shipped, never seen

These shipped in 7BEF2B95 or 5DA3DF5E and were only verified offline. The 11-08 live test looked at the Allied Warband
crash alone.

| What | How to see it |
|---|---|
| The court's trait removals no longer raise CA's "Trait Removed" card | Load `derpy_ic_oldbuild_t2.23883710723.save`. The old builds showed 8 to 14 cards on load; expect 0. |
| The court button on turn 1 of a new campaign (`ic_opener_intro`, on `ScriptEventCampaignIntroComplete`) | New campaign. The button should be there as soon as CA's intro ends, not from turn 2. |
| Office card: two-digit ranks fit (button 84, cell 122) | Any office with "rank 30" or more. The text must not be cut. |
| Names in office cells cut by `WidthOfTextLine` | A long two-word name, such as Thorgrim's. Check at 720p and at 1080p. |
| "strength 0 of 1" wording | Any office card with a strength line. |

The kin-war fix (Dwarf courts naming Dwarf holds) was seen in game on 75D3F280 and is closed.

Use the minimal list from `docs/LIVE_TESTING.md` (intro skip, bridge, MCT, the pack), the test prefs and the player
shield. Quit the game afterwards.

## 3. Replies not posted

Drafts are in [WORKSHOP_REPORTS_20261108_IRON_COURT.md](WORKSHOP_REPORTS_20261108_IRON_COURT.md) for zsmasher (Allied
Warband, fixed), Nitefog (war council) and Nerberius (-100% workload: that draft is WRONG, it was ours - section 0). If item 1 ships
first, change Nitefog's last sentence.

## 4. Known, not ours

- **Bridge drift.** `wh3_select_campaign` and `wh3_select_race` no longer find CA's frontend lists. The 11-08 report
  gives the new paths. `wh3_select_army` only hovers, so select with a real click (`probes/tp_mouse.ps1`).
- **Steam validation** can put the published build back over an unuploaded Workshop deploy. Hash it before trusting
  it (memory `steam-validation-reverts-workshop-deploys`).
