# Iron Court: rival courts' wars and claims, disloyal armies (2026-11-02)

Build `69AB38E7` (15,562,366 bytes), deployed to `data/` on 2026-11-02 over an unrecorded
10-29 build `71CF7C2E` (backup in `Modding Files/Backup/deployed_auto/`; its tables, loc and
Lua are all contained in this build, diffed row by row). Not uploaded, repo not synced or
committed. Seen in game the same afternoon (below); that run found the kin-war bug, fixed after
it, and the author then asked for a whole-mod text pass, which follows this build.

The internals are written up in the repo's `docs/DEVELOPMENT.md`, section "Rival courts' wars
and disloyal armies (2026-11-02)". This note covers the design calls and what is still owed.

## What it does

1. **AI courts hold war councils.** `IC.council_for` is the one gate: `council` on, and in an AI
   court `ai_council` on too; a faction in the race's `REBEL_POOL` never holds one. Only the
   parties open a vote (the `council` party act); the Crown abstains and nobody overrules, so it
   settles on the tally. A passed war is declared by `IC.council_turn` and reported through
   `IC.news` as kind `"war"`. `IC.war_candidate` still refuses a human target.
2. **AI courts grant claims at once.** `IC.claim_raise` now runs for every court. An AI court
   calls `IC.ai_grant_claim` straight away: the least loyal claimant gets the governorship
   through `IC.claim_grant`, conquest first on a tie. Left open, the governor filler would seat
   somebody else before the claims step next turn.
3. **Disloyal armies.** `IC.apply_army_bundles` puts `derpy_ic_army_<infix>restless` (-4
   leadership) on a rival lord's field army while his party is at or under `secede_loyalty`,
   and `..._wavering` (-8) while its clock runs. The ruler and legends count as the Crown's and
   are exempt, and so are heroes and garrisons. Bundles go on with `cm:apply_effect_bundle_to_force(key, cqi, 0)`.
   It runs at the end of `IC.turn`, after every panel action, in `IC.settle_switches`, and
   clears in `IC.dismantle`.

## Design calls made without asking (the user said to skip the questions)

- The AI picks the **least** loyal claimant: a grant is the ruler buying a party off.
- 4 and 8 leadership, inside CA's own -10 to -1 range for this effect on force bundles.
  Fixed numbers, not MCT sliders; only the two switches are on the MCT page.
- The army penalty applies in AI courts too, so a rival's disloyal lords fight worse.
- An AI court's war gets a Record line for players who met it; its proposer is not named.

## Checks run (all offline)

Harness 1243 ok; 1,443 mutants, every anchor matching once, the 27 new war/claim/army mutants
caught; `gen_iron_court.py --check` and `--selftest`; `check_ic_release.py --pack` 0 findings
(snapshot re-pinned to `1BB222C5`, the only loc and row moves being the 4 bundles and the two
countdown cards); `check_mp_sim.py --staged ic` no desync, planted fault caught; luac,
`check_lua_api`, `check_lua_literal_left` clean; `check_lua_undeclared` unchanged from before.
An antislop pass (during mode) trimmed the new comments and fixed one MCT tooltip.

## Live test, 2026-11-02 (build 69AB38E7)

Mod list `used_mods_derpy_ic_aiwars.txt` (intro skip, bridge, MCT, the Iron Court), fixture
`derpy_ic_oldbuild_t2.23883710723.save` (Legion of Azgorh, turn 2), player shield on.

- [x] A Legion lord given a field army (cqi 1076, force 1120): no bundle at loyalty 49; at 20,
      `derpy_ic_army_restless` on the force, and CA's own UI list (`CcoCampaignCharacter` ->
      `MilitaryForceContext.EffectBundleList`) shows "Divided Loyalties", its description and
      "Leadership: -4" in red. A second refresh moved nothing. The ruler's army wore none.
- [x] Clock started: `IC.settle_switches` swapped it for "A Party Preparing to Leave", -8.
- [x] Secure Loyalty sent through the panel's own transport (`IC.mp_send` -> UITrigger ->
      `answer()`): countdown stopped, the army back to -4 at once, no end turn.
- [x] MCT "Disloyal armies" off then Finalize (`MctFinalized`): bundle off; on again: back on.
- [x] Unit leadership in the campaign readout (`StatList` `stat_morale` `Value`) did not move,
      and neither did it for CA's own `wh3_dlc20_bundle_muddled_mind` (same effect and scope,
      -8): the campaign readout leaves force effects out. Not checked in a battle.
- [x] AI council, forced past the grace: Astragoth's Forge opened a vote, the tally passed it,
      the war was planned 3 turns on and `cm:force_declare_war` declared it on its turn. With
      the Conclave, which the player has met, the Record line read "Servants of the Conclave:
      the court voted for war on Drippin Fangs."
- [x] AI claim: Drakenmoor transferred to the Conclave, `IC.claim_raise` raised 2 claims and
      granted the Hearth Clans (loyalty 41, against the Temple's 58) at once; claims closed.
- [x] 8-turn soak with the grace cut to 2 for the session: Astragoth declared on Arbaal
      unforced, Zhatan planned a war on Sayl, Karak Hirn opened a vote on Argwylon; army
      bundles on in Astragoth's and Karak Azul's courts; an AI rising seceded cleanly. No Iron
      Court script error (the only errors are CA's Nurgle-initiative listener warnings).
- [ ] **Bug found and fixed after the run:** Dwarf courts named fellow Dwarf holds. Thorgrim's
      court picked Zhufbar and Karak Kadrin's passed a war on it in the soak. `IC.war_candidate`
      now refuses a target of an AI court's own subculture (`kin`); harness check and mutant
      added. Not yet re-seen in game.

## Whole-mod text pass (build CB7E4918)

The author, mid-test: a trait tooltip's "unless he is a legendary character or your faction
leader" is immersion breaking, and "i can see sloppy AI texts format and wording in the mod".
The earlier antislop pass had covered only this session's new lines. Four agents rewrote the
rest to one brief (scratchpad copy not kept; the rules are in memory `player-text-plain-words`):

- In-world text (traits, bundles, party, office and culture text): no exception clauses, no
  game-system words, no fourth-wall quips. Instruction text (cards, Help, tooltips, MCT) may
  name a tab, never a setting or a turn number, and softens an exception with "can".
- One sentence a line, no clause-joining comma, no semicolons, no em dashes.
- Rules dropped from flavour text now live in Help: the ruler and legends sit with the Crown, a
  man whose party is not at court sits with the Crown, no party leaves in the first
  `{grace_turns}` turns, home-province bonuses apply on the Old World map only.
- Check 16g2 in `gen_iron_court.py` used to pin "From turn 11," in `loyalty_warn`; it now fails
  any card body naming a turn number, a switch, MCT, a setting or "unless" (seen to fail on a
  planted line).
- Move blurbs are capped by their cards (`gen_ic_ui.py --check`): the pledge cards fit about 12
  characters, so "Forge-sworn." and "Anvil-sworn." stay.
- Three pinned lines changed with their pins (harness and `gen_ic_ui.py`): "...stop them. An oath
  will not hold.", "...follows your side. You have not taken one.", " and write a grudge
  against you". Three mutants re-aimed at the new wording, all caught.

## Tooltip pass and retest (build 75D3F280, deployed and seen in game)

The author, during the retest: "tooltips should also be better formatted" (a governor picker
row reading "Mines of Mingol. Governing: a, b. Drawback: c. 5 influence. Holds: None.") and
"check for other tooltips that are not formatted properly". The text pass had not touched
`zzz_derpy_iron_court_ui_map.lua` at all: its agents were given four Lua files, not five.

- **Layout, one rule:** the subject first, then one fact a line as "Label: value", effects one a
  line (boons `[[col:green]]`, drawbacks `[[col:red]]`, CA's own tags), a blank line between
  blocks, instructions last. Applied to the picker, pins and Provinces rows, the pie crests,
  the loyalty breakdown, trait tips (the conditional rules in `IC.PARTY_TRAITS` are now
  newline lists in both races), the ambition plate, the agenda block, action buttons, the
  government tip and cards, claims, government petitions, the Book, a governor's rank.
  `ICUI.mood_phrase` says the card's capitals as words ("leaves in 3 turns").
- **Generated loc can carry line breaks.** `write_tsvs` writes a newline as `\\n`, RPFM's
  escape, which its import turns back into one; a lone `\n` stays literal. Measured on a
  throwaway pack before relying on it. The old comment saying TSV has no escape was wrong.
  Used by the 48 picker lines, the 16 culture traits and the 28 office title traits.
- The picker's first line says "Culture: ..." so a culture does not read as a province.
- Gates: harness 1243; 11 stale mutant anchors re-aimed, all 1,444 matching; the 25 mutants on
  the changed lines all caught; gate re-pinned twice after reading every moved line (92, then
  48, figures unchanged); `check_mp_sim --staged ic` no desync.

**Seen in game (same fixture, turn 2 to 6):**

- [x] The tooltips above, read back through `GetTooltipText` and a desktop capture of a
      hovered picker row (`common.take_screenshot` draws no UI; the capture copies the window).
- [x] `loyalty_warn` and `secede_warn` cards: new text, no turn number or setting.
- [x] Help tab: the Crown, former-trade and culture lines.
- [x] Kin fix: 303 AI courts, 640 candidate targets, none of their own subculture; Thorgrim's and
      Karak Kadrin's courts refuse Zhufbar with `kin`. Over four AI turns, 8 recorded war picks,
      none kin (Karak Kadrin, which voted on Zhufbar before, picked Drycha and Drippin Fangs).
- [x] **Army leadership in battle.** A lord of the counting-down party given an army
      (force 1523, `derpy_ic_army_wavering`) attacked an orc warband; in battle CA's own
      leadership breakdown on his Chaos Dwarf Warriors read "Base value: 70, Difficulty
      modifier: -4, Other: -8" (58), the orcs had no such line, and that bundle is the only one
      on the army or the faction with a leadership effect. Decisive victory.
- [x] No Iron Court script error; only CA's Nurgle-initiative listener warning.

**Found in that run:** `force_remove_trait` has no quiet flag, so every trait the mod takes off a
player's man raised a "Trait Removed" popup. On this pre-release fixture that was 8 to 14 cards
on load (`IC.stamp_culture` converting retired birthplaces) and one per corrected party trait at
a turn start; its popup has no accept button, which stalled `wh3_soak_turns` twice. A party
leaving or splitting moves several men's party traits at once.

## Trait Removed cards silenced (build 7BEF2B95, built, deploy queued)

All 15 removals now go through `IC.remove_trait`: it shuts `character_trait_lost` (that one
event, not the category, so CA's other trait cards still show), removes, and opens it again
from a named 1-second `cm:callback`. A counter lets only the LAST removal's callback open it,
and it stays shut while `IC._seeding` is running, since `seed_finish` opens it itself.

- Harness 1245: the stub records any removal made with the event open (the late check
  "no trait was taken off a man with the card open" needs at least one removal to pass), and a
  direct check drives the timing, including the seeding case. The base `cm.callback` stub no
  longer counts the named re-open as a "deferred pass".
- Mutants 1,450, none stale. The six new ones (card left open, never reopened, first
  opening running over a later card, opened mid-seeding, an office and a birthplace removed
  past the helper) and the eight re-aimed at the old `cm:force_remove_trait` anchors all caught.
- Release gate 0 findings (no table or loc moved), MP sim no desync, Lua API clean.
- **Not seen in game.** The game was in use when it was built; `deploy_iron_court.py
  --deploy-only --wait` was left to copy it in when the game closes. To see it: load
  `derpy_ic_oldbuild_t2.23883710723.save` and count "Trait Removed" cards on load (was 8 to 14).
