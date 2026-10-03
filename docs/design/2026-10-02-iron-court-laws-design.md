# Iron Court: laws and votes - design (2026-10-02)

The author asked: "is there still space for a tab for enacting laws, e.g politicking", then "yes,
it is similar how Bannerlords do it, if its possible parties can have voting on other parts of the
mod such as seats and governors for later". Their choices:

1. Both the player and the parties propose laws.
2. One choice per category.
3. You win votes, or overrule.
4. Five options per category.
5. **The men vote, not the parties** (author: "character have their influence trait right? what
   if the vote is by character"). Each man votes his party's line with his own influence, and the
   player can win individual men.
6. **Support levels, as in Bannerlord**, for the Crown ("can the crown party spend influence in
   three tiers just like bannerlord?") and then for the parties too ("parties push too").

They reviewed the effect catalogue three times:

- "effects are too broad check other effects that can be done";
- they asked for five options per category;
- they swapped the Ogre Compact, the Daemonsmith hero capacity, and the siege effects ("implemented
  on the tower of zharr", "+2 siege towers is pretty useless").

They then approved sections 1 to 4.

**Section 4 was redrawn after a preview** (author: "try a different design similar to bannerlord
in propose and vote, Main view should be a different design not a list system again"). The list
mockups were replaced by a policy board and a decision screen, drawn from the panel's own art
(`.skilltree_cache/ui_preview/ic_law_board.png`, `ic_law_vote.png`), and approved ("good with
thy design").

This is **sub-project 1 of 2**. Votes on seats and governors are sub-project 2. They get their own
spec, and reuse the vote engine here unchanged.

## 1. What it is

- **The court passes laws.** There are four categories, Labour, Tribute, Worship and War, with
  five options each. Exactly one option per category is in force.
- **A vote decides each change.** Every man of the court votes with his own influence, the number
  his standing trait shows. He votes as his party does: for or against by its interests, or by
  its loyalty. The Crown's men vote as the player chooses.
- **Who proposes.** The player can propose any option. Parties propose the options they favour.
- **What the player can pay for.** They can push the Crown's side through three support levels,
  win individual men, or overrule the whole vote. Parties with a stake push their side the same
  way.

Governments shape the court's own rules; laws shape the realm. Every law effect is a Chaos Dwarf
mechanic, or one CA applies to Chaos Dwarf content.

## 2. The laws

Each option is a faction effect bundle, `derpy_ic_law_<category>_<option>`. Each category's
**start** option has no effects, so a new campaign and an old save lose nothing.

Every effect key below comes from CA's 9.0 `db.pack`. CA applies each one from the faction-level
scope given here, in a bundle or a technology (the source is named). In the "good" column, F means
a cost-type effect: a negative value is the boon and a positive value is the cost. "For" and
"Against" are the party stances.

### 2.1 Labour (`labour`), start: The Measure (`measure`)

| Option | Effect key | Scope | Value | good | For | Against |
|---|---|---|---|---|---|---|
| The Lash (`lash`) | wh_main_effect_force_all_campaign_captives | faction_to_force_own_unseen | +15 | T | chain | hearth |
| | wh3_dlc23_effect_rush_construction_cost | faction_to_province_own | -30 | F | | |
| | wh3_dlc23_effect_force_stat_leadership_chd_labourers | faction_to_force_own | -4 | T | | |
| The Kept Stock (`kept`) | wh3_dlc23_effect_upkeep_chd_labourers | faction_to_force_own | -50 | F | hearth | chain |
| | wh3_dlc23_effect_recruitment_rank_chd_labourers | faction_to_force_own | +2 | T | | |
| | wh_main_effect_force_all_campaign_captives | faction_to_force_own_unseen | -10 | T | | |
| The Furnace Quota (`quota`) | wh3_dlc23_pooled_resource_chd_workload_modifier | faction_to_province_own | -15 | F | forge | hearth |
| | wh3_dlc23_pooled_resources_chd_raw_materials_consumed_mod | faction_to_province_own | -15 | F | | |
| | wh3_dlc23_effect_upkeep_chd_labourers | faction_to_force_own | +25 | F | | |
| The Ash Harvest (`ash`) | wh_main_effect_force_all_campaign_razing_income | faction_to_faction_own_unseen | +25 | T | legion | ledger |
| | wh_main_effect_force_all_campaign_sacking_income | faction_to_faction_own_unseen | +15 | T | | |
| | wh_main_effect_force_all_campaign_captives | faction_to_force_own_unseen | -10 | T | | |

### 2.2 Tribute (`tribute`), start: The Crown's Tithe (`tithe`)

| Option | Effect key | Scope | Value | good | For | Against |
|---|---|---|---|---|---|---|
| Open Roads (`roads`) | wh3_dlc23_effect_technology_chd_convoy_mod_active_convoys | faction_to_faction_own_unseen | +1 | T | road | crown |
| | wh3_main_effect_caravan_scouts (scripted: CA's convoy events read it) | faction_to_character_own_unseen | -25 | F | | |
| | wh_main_effect_modify_vassal_income | faction_to_faction_own_unseen | -20 | T | | |
| The Ledger's Tariff (`tariff`) | wh3_dlc23_effect_chd_convoy_trade_tariff_scripted (scripted) | faction_to_faction_own_unseen | +5 | T | ledger | road |
| | wh3_dlc23_effect_economy_gpd_manufacture | faction_to_region_own_unseen | +10 | T | | |
| | wh3_main_effect_caravan_cargo_value | faction_to_character_own_unseen | -10 | T | | |
| The Mines Before All (`mines`) | wh_main_effect_technology_economy_gdp_mod_mining_dwarfs | faction_to_region_own_unseen | +15 | T | forge | road |
| | wh_main_effect_economy_trade_good_commodity_mod | faction_to_faction_own_unseen | +10 | T | | |
| | wh3_main_effect_caravan_cargo_capacity | faction_to_character_own_unseen | -15 | T | | |
| The Overseers' Charter (`charter`) | wh3_dlc23_faction_xp_increase_generals_chd_convoy_overseers | faction_to_faction_own | +3 | T | road | legion |
| | wh3_dlc23_effect_force_army_campaign_experience_chd_convoy_overseer_per_turn | faction_to_character_own_unseen | +100 | T | | |
| | wh3_dlc23_faction_political_diplomacy_mod_chaos_dwarfs | faction_to_faction_own_unseen | -10 | T | | |

### 2.3 Worship (`worship`), start: The Rites Kept (`rites`)

| Option | Effect key | Scope | Value | good | For | Against |
|---|---|---|---|---|---|---|
| The Fires Fed (`fires`) | wh3_dlc23_effect_pooled_resource_conclave_influence_mod_all_sources | faction_to_faction_own_unseen | +10 | T | temple | tower |
| | wh3_main_effect_corruption_chaos_adjacent_provinces | faction_to_province_own | +1 | T | | |
| | wh3_dlc23_effect_rush_construction_cost | faction_to_province_own | +15 | F | | |
| Seats Bought in the Tower (`seats`) | wh3_dlc23_effect_toz_chd_conclave_influence_spent_slot_claimed_mod | faction_to_faction_own_unseen | -25 | F | tower | temple |
| | wh3_dlc23_effect_pooled_resource_conclave_influence_mod_all_sources | faction_to_faction_own_unseen | -10 | T | | |
| The Lore Taught (`lore`) | wh3_dlc23_effect_ability_wom_cost_pct_lore_of_hashut_spells | faction_to_force_own | -10 | F | tower | hearth |
| | wh3_dlc23_effect_ability_cooldown_lore_of_hashut | faction_to_force_own | -10 | F | | |
| | wh_main_effect_character_stat_miscast | faction_to_character_own | +15 | F | | |
| The Daemonsmiths' Licence (`licence`) | wh3_dlc23_effect_physical_resist_chd_kdaai | faction_to_force_own_unseen | +10 | T | forge | temple |
| | wh3_dlc23_effect_building_construction_time_mod_chd_temple_of_hashut | faction_to_region_own_unseen | -1 | F | | |
| | wh3_dlc23_effect_pooled_resource_conclave_influence_mod_all_sources | faction_to_faction_own_unseen | -10 | T | | |

### 2.4 War (`war`), start: The Levy (`levy`)

| Option | Effect key | Scope | Value | good | For | Against |
|---|---|---|---|---|---|---|
| The Hell-Forge Unbound (`hellforge`) | wh3_dlc23_chd_ritual_unit_cap_cost_mod_all_toz | faction_to_faction_own_unseen | -10 | F | forge | legion |
| | wh3_dlc23_effect_chd_hellforge_cap_mod_all | faction_to_faction_own_unseen | +1 | T | | |
| | wh3_dlc23_effect_force_recruit_cost_chd_chaos_dwarf_infantry | faction_to_force_own_unseen | +10 | F | | |
| Standing Legions (`legions`) | wh3_dlc23_effect_force_recruit_rank_chd_chaos_dwarf_infantry | faction_to_force_own_unseen | +1 | T | legion | forge |
| | wh3_dlc23_effect_force_recruit_cost_chd_chaos_dwarf_infantry | faction_to_force_own_unseen | -10 | F | | |
| | wh3_dlc23_effect_upkeep_chd_artillery_warmachines | faction_to_force_own | +10 | F | | |
| The Old Grudge (`grudge`) | wh3_dlc23_effect_xp_gain_increase_dwarfs | faction_to_force_own | +100 | T | legion | ledger |
| | wh3_dlc23_effect_upkeep_cost_reduction_chd_labourer_hobgoblin_infantry | faction_to_force_own_unseen | +10 | F | | |
| The Gunnery Doctrine (`gunnery`) | wh3_dlc23_effect_force_stat_explosive_damage_chd_artillery | faction_to_force_own_unseen | +10 | T | forge | hearth |
| | wh3_dlc23_effect_force_stat_range_chd_artillery | faction_to_force_own_unseen | +5 | T | | |
| | wh3_dlc23_effect_recruitment_cost_chd_ranged | faction_to_province_own | +15 | F | | |

### 2.5 Rules for the catalogue

- **A value against CA's usual sign.** Values CA never uses with that sign need checking in game:
  the Tower seat cost at -25 (CA only ever uses -9999), and captives at -10. The build's effect-sign
  report (`tools/check_effect_signs.py`) must list every cost row, so each one can be read against
  its law.
- **The Hell-Forge cost effect.** `wh3_dlc23_chd_ritual_unit_cap_cost_mod_all_toz` stacks with the
  author's Hell-Forge caps pack, which builds its own `<ritual>_cost_mod` keys. That works, but
  the two packs interact.
- **Party coverage.** Every rival party is for at least one option and against at least one. The
  Crown is against Open Roads and otherwise holds the deciding share.
- **Icons.** Each option wears a CA effect-bundle icon, by reference, as the governments do. The
  plan picks them by viewing them, and the bundle's `ui_icon` and the panel read one table.

## 3. Votes

### 3.1 The record

A vote is `{subject, proposer, opened, ends, stance, won, push, answered}`:

- **subject:** `{kind = "law", category, option}`. Sub-project 2 adds `kind = "office"` and
  `kind = "governor"`, with no change to the engine.
- **proposer:** a party slug, or the Crown for the player.
- **stance:** the Crown's side, one of `aye`, `nay` or `abstain`.
- **won:** `[cqi] = side`, the men the player has paid.
- **push:** `[party] = level`, from 0 to 3, the support level each party has bought, the Crown
  included.
- **answered:** set when the player chooses a stance. A party's proposal lights the tab's marker
  until it is set.

Each category has at most one open vote.

### 3.2 Proposing

- **The player** proposes any option of a category that has no open vote. It costs
  `law_propose_cost` (150) influence, paid by `IC.spend_crown` from the Crown men's influence above
  their seat bars. The stance is set to `aye`.
- **A party** proposes on its turn, through a new `IC.PARTY_ACTS` entry, when all of these hold:
  - the option is one it is **for**, and is not in force;
  - its category has no open vote;
  - its share is at least `law_party_share` (15%);
  - the court has had no party proposal for `law_party_rest` (6) turns.

  When several options qualify, `cm:random_number` picks one, so every multiplayer machine picks
  the same. A party proposal opens with the stance `abstain` and lights the tab's marker until
  the player answers.
- **Duration.** A vote runs `law_vote_turns` (2) turns. Proposing raises `law_proposed`.

### 3.3 How the men vote

**The voters** are every living man of the court with influence above 0, counted when the vote is
tallied. That means lords and heroes, through `IC.standing(faction_key, cqi)`. Each man's party is
`IC.house_of_character`, so a legend counts with the Crown. A man with no influence casts no
vote.

**A man's weight is his influence.**

**His vote is his party's line:**

| His party | Vote |
|---|---|
| for the option | aye |
| against the option | nay |
| no stance, party loyalty >= `law_loyal_line` (60) | the Crown's side |
| no stance, party loyalty < `law_disloyal_line` (40) | against the Crown's side (nothing if the Crown abstains) |
| no stance, loyalty in between | abstains |
| the Crown | the player's stance |

A man the player won votes the side he was won to, whatever his party's line.

**The tally** multiplies each man's weight by his party's push level (section 3.4) when he votes
his party's line. A man won away from his party is not multiplied.

- **The result:** aye influence against nay influence. Abstentions don't count. A tie fails.
- **Answering a party's proposal.** The player sets the Crown's stance (Support, Oppose or
  Abstain) for free.
- **Spending costs votes.** Every price below comes out of the Crown men's influence, so buying
  votes lowers the Crown's own vote. That is deliberate, and the vote view shows the Crown's
  weight after each purchase.

### 3.4 Paying

**Support levels** (Bannerlord's "slightly favour, strongly favour, fully push"):

| Level | Cost (`law_push_cost`) | Weight of the party's men voting its line (`law_push_mult`) |
|---|---|---|
| 0 - votes | free | x1 |
| 1 - slightly favours | 100 | x1.5 |
| 2 - strongly favours | 250 | x2 |
| 3 - fully pushes | 500 | x3 |

- **Raising a level** costs the difference: 1 to 2 costs 150. A level never drops, and nothing is
  refunded.
- **The payer.** A party's men pay, from their influence above their own seat bars, richest
  first. `IC.crown_purse` and `IC.spend_crown` generalise to `IC.party_purse(faction_key, slug)`
  and `IC.spend_party(faction_key, slug, n)`; the Crown's pair stays as a thin call into them.
  The cost lowers those men's own weight before the multiplier applies. Pushing is worth most to a
  party that is already strong.
- **The Crown** pushes its stance when the player chooses. It cannot push while abstaining.
- **A party** pushes only when it has a stance on the subject (for or against). A party voting on
  loyalty has no stake. On each of its turns while the vote is open, it raises its level by one
  step when all of these hold:
  - its side is losing, or within `law_push_margin` (10% of all voting influence) of losing;
  - the next step costs no more than its purse;
  - it is below level 3.

  This is decided inside the turn, so every multiplayer machine agrees. The Record logs it.

- **Win a man.** He votes on the player's side for this vote only.
  - The price is his influence x `law_win_rate` (50%), scaled by his ambition through
    `law_win_ambition`: cautious 150%, steady 100%, ambitious 75%.
  - The price doubles when his party is against the player's side.
  - A man is won once per vote. Crown men cannot be won, because they already vote the player's
    way.
- **Overrule.** For `law_overrule_cost` (500), the player decides the vote now, either way. Every
  party on the losing side loses `law_overrule_loyalty` (10) loyalty.
- **Who pays.** Both come out of `IC.spend_crown`, which refuses rather than unseat anyone, the
  same as Change Doctrine.

### 3.5 Resolution

Resolution happens at the player court's turn start once `ends` is reached, inside `IC.turn`
before the government step.

- **Passed:**
  - the category's bundle is swapped, so the old option's bundle comes off and the new one goes on;
  - parties for the option gain `law_pass_gain` (5) loyalty, and parties against it lose
    `law_pass_loss` (5);
  - `law_passed` is raised.
- **Failed:**
  - a party that proposed it loses `law_fail_loss` (5) loyalty;
  - the player's proposal fee is spent either way;
  - `law_failed` is raised.
- **Men who leave.** A man who dies or leaves the court while a vote is open just stops voting,
  and so do the men of a party that is removed. Loyalty changes on pass and fail stay per party.
- **A proposer who left.** The vote still resolves.

### 3.6 Scope

Player courts only. AI courts keep their start options, never vote, and wear no law bundle.

## 4. The Laws tab

A seventh tab, **Laws**: `ic_tab_laws` at (1482, 62, 240, 32), with an attention marker
`ic_mark_laws`. Nothing else is on that row past x 1478. The compact layout scales it with the
row. The tab has two screens, both drawn in their own components rather than in the shared row
pool. The approved pictures are the reference for both.

### 4.1 The law board (the tab's main screen)

Modelled on Bannerlord's policy screen.

- **Four columns**, one per category, each under a title: the category's name in capitals on
  the heading plate the Intrigue tab's move groups use, sized to its words and centred on the
  column (author, 2026-10-03; it replaced a full-width card plate with an icon).
- **Five law cards per column**, one per option, from a new card file `derpy_ic_law.twui.xml`
  (20 instances). Each card shows:
  - the law's icon, with its name beside it over up to two lines;
  - its effects, one short line each (up to three), the card's full width;
  - a footer line: **In force**, **Vote open: N turns**, **The old way** for an effectless start
    option, or **For** and **Against** with one party crest each.
- **Card states:**
  - the law in force wears the gold selected frame;
  - the chosen card wears the red selected row art;
  - a law under vote carries the heat marker.
- **Choosing a card** fills the detail pane. The board opens on the first law not in force in the
  first category with no open vote, or on the first card.
- **The detail pane** (right of the columns) shows the chosen law:
  - icon, name, and "In force: <law>.";
  - its effects in CA's own words, each over up to two lines;
  - **Favoured by** and **Opposed by**: each party with its crest and its name in this court, or
    "(absent)";
  - **If it went to the court now:** the aye, nay and abstaining shares the tally would give
    today, and one line per party with its likely vote in a few words ("for it", "aye, loyal",
    "undecided"). This is the same tally
    the vote uses (section 3.3), run with the Crown voting aye and nobody won or pushing;
  - the price, and **Propose** or why not.
  - With a vote open in that category, the pane says so and its button is **Go to the vote**.

### 4.2 The vote (a decision screen)

Modelled on Bannerlord's kingdom decision. Opened by **Vote** on an open vote's card, by **Go to
the vote**, or from the marker.

- **The top plate:** the law's icon, name and effects; who proposed it; the turns left.
- **The support bar,** across the panel: the aye parties' plates and crests from the left and the
  nay parties' from the right, each sized by its weighted influence, the abstaining share between
  them. Above it: "Aye N% (influence)", "Abstaining N%", "Nay N% (influence)".
- **Two sides,** "Enact <law>" and "Keep <law in force>". The side the Crown backs carries the
  Crown's crest and "The Crown's side".
  - Each side lists its parties, heaviest first, as **party blocks** from a new file
    `derpy_ic_lawblock.twui.xml` (up to four per side). A block shows the party's crest, its
    name, its support level in words with its multiplier ("Strongly favours it x2"), three pips
    lit to its level, and its weighted total.
  - Under the heading, the block shows its **three richest voting men**: porthole and forename,
    over either his influence or, for a man on the side the Crown opposes, **Win (price)**. More
    men than three are summed in a "+N more" line; they still vote.
  - A side with more than four parties sums the rest in a line under the last block.
- **Abstaining** parties are one line under the sides: named up to two, counted past that.
  - Their men are not drawn, so no Win button reaches them, though `IC.law_win_price` prices an
    abstaining man too (section 3.4). Winning the undecided from this screen
    would need blocks for the abstaining line; it is left out of this version.
- **The Crown's hand,** a bar along the bottom:
  - **Support / Oppose / Abstain**, the current one lit;
  - **Slightly favour / Strongly favour / Fully push**, each with the price of reaching it, the
    reached levels lit and marked paid, all refused while abstaining;
  - **Pass now** and **Fail now**, the overrule, each with its price.
- **Back to the laws** on the top plate returns to the board, as does the Laws tab.

### 4.3 Everything else

- **Record kinds:** `law_propose`, `law_pass`, `law_fail`, `law_win`, `law_push`, `law_overrule`.
- **Help:** a **Laws** topic.
- **Events:** `law_proposed`, `law_passed` and `law_failed`, appended to `IC.EVENTS` and to the
  generator's `EVENTS` in the same order.
- **Player text** follows the plain-words rule.
- **Sized by measurement (2026-10-02, build).** The first layout clipped against the engine's
  face (check 20k in `gen_ic_ui.py`, 83 strings at 1920); the wordings and counts above are the
  ones that fit at 1600, 1920 and 2560.

## 5. Settings, save, multiplayer

- **The live switch** "Laws" (`laws`). It is appended to `IC.TUNE_ORDER`, `IC.LIVE_TUNE`, the MCT
  page and the harness `LIVE` list.
  - Off: every law bundle comes off and open votes drop. The options in force stay in the save.
  - On: their bundles go back on.
- **Constants.** All prices, lines and timings are `IC.TUNE` constants and stay off the MCT page.
- **Save:**
  - Field 17: `category,option` per category.
  - Field 18: open votes, as `category,option,proposer,ends,stance,won,push,answered`, with
    `won` as `cqi:side` pairs and `push` as `party:level` pairs.
  - Both are optional, and an old save loads on the start options with no votes.
- **Multiplayer.** These are court ops through `ICUI.send` and `IC.mp_receive`, and the model
  re-checks every one:
  - `law_propose`;
  - `law_stance`;
  - `law_win`;
  - `law_push`;
  - `law_overrule`.

  The MP routing check counts them. Party proposals and resolution run inside the turn.

## 6. Out of scope

- Votes on seats and governors (sub-project 2).
- AI courts passing laws.
- Laws changing court rules, which is the governments' job.
- More than one open vote per category.
- MCT sliders for the prices.

## 7. Tests

- **Harness checks**, each watched failing first:
  - each stance rule applied to a party's men;
  - a man's weight is his influence;
  - a man with no influence does not vote, and a legend votes with the Crown;
  - abstentions left out, and a tie failing;
  - win prices by ambition, the double price against his party, one win per man per vote, no
    win on a Crown man;
  - buying a man lowers the Crown's own weight by exactly what was spent;
  - each support level's price and multiplier, paying the difference on a raise, no lowering, no
    push while abstaining;
  - a party pushes only with a stance, only when losing or within the margin, only when it can
    afford it, and one step per turn;
  - the multiplier covers a party's line-voting men and not men won away;
  - the purse never takes a man below his seat bar;
  - a man who dies mid-vote stops counting;
  - overrule, both ways, and its loyalty hits;
  - pass and fail loyalty;
  - the bundle swap, with exactly one law bundle per category on the faction;
  - party proposal conditions and rest;
  - the save round trip, and an old save;
  - the switch off and on;
  - AI courts untouched;
  - each MP op re-checked;
  - the board's cards, states and pane, the projection matching the tally, and the vote
    screen's bar, sides, blocks, men cap and hand;
  - the marker lit only while a party proposal waits.
- **Mutants** under a `law:` prefix.
- **Gates:**
  - `gen_iron_court`: every law bundle's effects exist, with these scopes and its loc;
  - `gen_ic_ui`: the new tab, the two new files and every new cell fit at 1920 and 1600;
  - `preview_iron_court`: the board and the vote screen drawn at 1920 and 1600;
  - `check_effect_signs` read against the catalogue;
  - the import gate.
- **Owed in game:**
  - the Tower seat cost at -25;
  - captives at -10;
  - the two scripted convoy effects;
  - the Hell-Forge cost effect beside the caps pack.
