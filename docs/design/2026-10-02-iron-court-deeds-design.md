# Iron Court: deeds move the court - design (2026-10-02)

The author asked: "what else is missing, how do we engage the player into using the system".
Their choices, in order:

1. Governments should be "a mirror of play".
2. Deeds should work "through the parties".
3. A party that is absent should come to the court.

They then approved sections 1 to 4 below as written.

The governments themselves are in `2026-10-02-iron-court-governments-design.md`, and what was
built is in `docs/sessions/HANDOFF_20261002_IRON_COURT_GOVERNMENTS.md`.

## 1. The problem

The governments work, but nothing pulls the player into them:

- Only the parties' shares build pressure, so nothing the player does moves the government.
- The pressure is visible only in a tooltip.
- There is no introduction.

To most players a government is weather that happens to them. Governments should instead follow
how the player plays, through the court's own parties, and the player should be able to see that
happening.

## 2. Renown

- **Renown.** Every party in a player court has a renown number. Deeds raise it, and it fades
  every turn.
- **It counts as party weight.** `IC.house_weight` adds renown, so renown raises the party's
  share. The existing drift does the rest: a rival party at `gov_drift_share` that leads with a
  government of its own builds pressure toward it. No drift code changes.
- **Saved separately.** Renown is its own saved field per court, `court.renown[party]`. It never
  touches `house.weight`, because that number is office bookkeeping: an office's exact weight is
  added on appointment and subtracted on loss.
- **The deeds**, all as `IC.TUNE` constants:

| Party | Deed | Event and test | Renown |
|---|---|---|---|
| legion | a battle won | `CharacterCompletedBattle`, already hooked; once per battle, de-duplicated on the pending battle (it fires once per character) | `deed_battle` 3 |
| forge | a Hell-Forge unit-cap ritual | `RitualCompletedEvent`, `ritual_category():find("HELLFORGE_CAPS")` | `deed_hellforge` 4 |
| temple | a Tower of Zharr rite | `RitualCompletedEvent`, category `DISTRICTS_*` or `TOZ_TIER_4` | `deed_rite` 4 |
| temple | a temple of Hashut built | `BuildingCompleted`, `building():name()` is `wh3_dlc23_chd_tower_temple_of_hashut_1` or `wh3_dlc23_special_great_temple_of_hashut_chd` (both read from CA's `building_levels_tables`; the `tower_temple_guardhouse` chain is military and excluded) | `deed_temple` 2 |
| chain | captives enslaved | `CharacterPostBattleCaptureOption`, outcome key confirmed in game (`CharacterPostBattleEnslave` as the fallback) | `deed_slaves` 3 |
| chain | a settlement razed | `CharacterRazedSettlement` | `deed_raze` 3 |
| road (else ledger) | a convoy completed | `CaravanCompleted` on the Chaos Dwarf culture. Not also `ScriptEventCaravanCompleted`: CA re-raises the same context, so listening to both counts every convoy twice | `deed_convoy` 5 |
| tower | a technology researched | `ResearchCompleted` | `deed_research` 2 |

- **Fading.** At each turn start, renown loses `renown_fade_pct` (10%), and at least 1.
- **Per-turn limit.** A party gains at most `renown_turn_cap` (8) in one turn, counted from turn
  start.
- **Player courts only.** This matches drift (`IC.gov_drift_on`). AI court politics are
  unchanged. The Crown and the Hearth have no deeds.
- **Tower rites the player did not click.** On confederation, CA re-performs Tower seats with
  `cm:perform_ritual`. Those rites score nothing: the confederation listener stamps
  `court.confed_turn`, and ritual deeds on that turn are ignored.
- **Old saves** start at 0 renown and need no migration. The new save field is optional: a save
  without it loads as empty.

> **Amended at the final review (2026-10-02):** fade 25%, per-turn limit 6, join line 15
> (was 10%, 8 and 20). The first numbers settled at 80-89 renown per party against a starting
> weight of 10, which cut the Crown's control. A party that leaves also loses its renown, so it
> cannot be drawn straight back. See the handoff section 8.

## 3. The party that comes to you

- **Absent parties bank renown too.** Deeds for a party that is not in the court are kept in
  `court.renown` under that party, and fade the same way.
- **The line.** At `renown_join_line` (20), the absent party wants in.
- **How it arrives.** The next lord recruited joins it.
  - `IC.background_for` gives him a background of that party, instead of the "fewest men" pick.
  - The party is added (`IC.add_house`) and he is stamped with its origin in the same step. A
    party with no character carrying its origin is removed by the existing orphan sweep, so it
    can never arrive empty.
  - It arrives at the loyalty a confederation brings, with its banked renown.
  - A legend, or a lord with a fixed history, is not eligible. The next ordinary lord takes the
    place.
- **A full court.** If the court already holds `rivals_max` rival parties, nothing arrives.
  The absent party's renown stops at the line and fades if the deeds stop. The usual ways a seat
  frees up still apply: a party leaves, splinters or dissolves.
- **Two parties at the line.** The one with more renown arrives first.
- **The card.** A new event `party_drawn` (2632) says why the party came, e.g. "Your victories
  have drawn the Legion to your court." `party_joined` stays as it is, for confederation.

## 4. What the player sees

- **The government line** shows the drift only while the court is moving:
  `[icon] Government: <name>  ->  [icon of the government it is moving toward] <pressure>/<line>`.
  - It must fit the 622px cell at 1920 and at 1600 with the longest name, "Rule of the
    Daemonsmiths". The preview checks it.
  - If it does not fit at 1600, the compact layout drops the "Government: " label.
- **The government tooltip** gains a "What moves your court" block.
  - One line per party in the court: its deed and its renown, e.g. "Legion - your victories -
    renown 12".
  - Then the absent parties with banked renown: "would come at 20", or "would come, but your
    court is full".
- **Party tooltips.** The dial and the party cards each gain one line: "Renown from your
  deeds: N".
- **The Record** gains a log kind `deed`: one entry per party per turn, summed, e.g. "Victories in
  the field: the Legion +6". Deeds raise no card of their own.
- **The introduction card.** A new event `gov_intro` (2631) fires once per human court, when its
  first government is set. That includes an old save that takes its start government. The card
  names the government and the six deeds. It is held by a saved flag, so it fires only once.
- **Help.** The "Governments" topic gains a paragraph on deeds, renown and parties arriving.
- **Player text** follows the plain-words rule: "Reputation", never "standing", and no jargon
  such as cap, accrue or AI.

## 5. Settings

- **One live switch:** "Your deeds move the court" (`deeds`). It is appended to `IC.TUNE_ORDER`,
  the MCT page, `PRESET_VALUES` and the harness `LIVE` list.
  - Off: no renown is gained, renown already held keeps fading, and no party is drawn in.
  - With governments off, renown still moves the parties' weight. Deeds are court politics, and
    the parties exist with or without governments.
- **The renown values, the fade, the per-turn limit and the join line** are `IC.TUNE` constants
  and stay off the Custom page. `gov_drift_share` is the precedent.

## 6. Out of scope

- Mandates (a goal per government) and tenure growth.
- Stronger campaign-wide effects for each government.
- Showing rival courts' governments.

Each one is a separate pass, if the mirror lands well in game.

## 7. Tests

- **Harness checks**, each watched failing first:
  - every deed adds its renown to the right party, and the Ledger takes the convoy when there is
    no Road;
  - a battle with two winning generals scores once;
  - the per-turn limit and the fade;
  - renown raises the share and carries the drift;
  - an absent party at the line takes the next ordinary lord, and refuses a legend;
  - a full court holds the absent party at the line;
  - two parties waiting: the larger arrives first;
  - the switch off stops gains and joins, and renown keeps fading;
  - AI courts score nothing;
  - the introduction fires once, including on an old save;
  - the save round-trips renown and the intro flag;
  - the line's drift segment appears only while moving;
  - the tooltip block and the "court is full" text;
  - Tower rites raised by a confederation score nothing.
- **Mutants** under a `deed:` prefix for each guard.
- **Gates:** `gen_iron_court`, `gen_ic_ui`, `preview_iron_court` at 1600 and 1920, and the
  `import_iron_court` gate.
- **Owed in game:** the capture-option outcome key, `ResearchCompleted` firing for the player,
  and the convoy counting once.
