# Iron Court governments - design (2026-10-02)

Status: **spec, approved section by section in chat 2026-10-02; awaiting the author's review of
this file.** No code yet. Next step after approval: `superpowers:writing-plans`.

## 1. What the author asked for

"Brainstorm for adding types of government in the mod." Answers given in chat, in order:

| Question | Answer |
|---|---|
| What is a government in play? | **A mix**: starts from the faction's own, drifts with who holds power, and the player can force a change ("change doctrine") at a cost. (First answered "fixed per faction"; corrected mid-brainstorm.) |
| What does it change? | **One signature court rule each**, plus a small faction bonus |
| What does it belong to? | **The faction** (the house), whoever leads it |
| Which factions start with one? | **Only lore-backed ones** (the author's standing rule: lore over coverage) |
| How does drift behave? | **Pressure, then a choice**: never a surprise |
| AI courts? | **Yes, but fixed**: AI courts keep their starting government |
| Cost of a forced change? | **Influence, loyalty and a cooldown** |
| How are the rules built? | **Tuning overrides** of numbers the court already uses |

Success: each Chaos Dwarf house plays a recognisably different court from turn 1, the player can
read why the court is pulling toward another government and answer it, and nothing about the
court's existing balance moves for a player who keeps the starting government.

## 2. Lore basis

Researched 2026-10-02 from CA's own text (`local_en.pack`, `wh3_dlc23_campaign_chd_tower_of_zharr.lua`),
the workspace's lore scrape `Modding Files/reference/lore/chaos_dwarfs_wiki.md` (5th-edition army
book pp.4-7, *Tamurkhan* pp.164-175), and the author's own loc for the `cr_` houses.

- Chaos Dwarfs have **no king**: the Sorcerer-Prophets rule as an oligarchy in the Temple of
  Hashut, "the strongest voice belongs to the oldest and most powerful", and each rules his own
  dominion of the city - workshops, forges, slaves, warriors (wiki). CA: Sorcerer Lords contest
  seats on the "Conclave of Evil" in the Tower of Zharr.
- Daemonsmiths are "both the priest and artificers ... ruling over Zharr-Naggrund" (CA).
- Politics is exile: Drazhoath was exiled after his intrigues failed (CA); the Black Fortress is
  "purely military" and a place of internal exile (wiki).
- Slaves and overseers, the Black Orc revolt (CA, wiki); convoys and Astragoth's convoy pact (CA).

So **no autocrat government** (it contradicts "no central figurehead"), and **no Hearth
government** (no lore support found).

## 3. The six governments

Each is a row of `IC.GOVS`: slug, party, name, rule text, bundle, overrides. Every signature rule
cuts both ways. Numbers are first drafts, tuned in the plan; each lives in `IC.TUNE` so the
difficulty presets and the MCT Custom page can reach them.

| Slug | Name | Party | Signature rule (overrides) | Cost of it | Bundle (faction) |
|---|---|---|---|---|---|
| `conclave` | The Conclave | tower | Seats rotate: `term_turns` 10 -> 6, `renew_wait` 3 -> 1 | more churn; a seat you want held keeps coming due | `E_RESEARCH` +5 |
| `priest` | Rule of the High Priest | temple | The eldest voice: `rank_influence` 3 -> 6 | `battle_influence` x0.75 | `E_LAW_INFLUENCE` +10% (was growth; author 2026-10-03) |
| `forge` | Rule of the Daemonsmiths | forge | The forges answer to their masters: `governor_income` 5 -> 8, `gov_rank_income_per` 2 -> 1 | `influence_trickle` 5 -> 3 | `E_ARMAMENTS` +10 |
| `legion` | Command of the Legion | legion | Standing is won in the field: `battle_influence` x1.5, `loyalty_battle_won` 3 -> 5 | `influence_trickle` 5 -> 0 | `E_UPKEEP` -5 |
| `chain` | Rule of the Slave-Lords | chain | Fear rules: `plot_murder_cost`, `plot_purge_cost`, `plot_provoke_cost` x0.65 | `plot_fail_loyalty` 10 -> 20 | `E_PB_LABOUR` +10 |
| `convoy` | The Convoy Concern | road, ledger | Everything has a price: `favour_gift_cost` 600 -> 400, `favour_secure_cost` 2500 -> 1700 | `plot_embezzle_loyalty` 6 -> 12 | `E_GDP` +5 |

**A government with two parties** (`convoy`: road and ledger) counts either as its leader for
drift, and applies every loyalty effect in sections 6 and 7 to each of its parties present.

The `E_*` effects are the generator's existing constants, already held to the effect-exists,
scope and `is_positive_value_good` checks. A multiplier in this table is applied to the base value
and rounded, and the result stored as the override, so an override is always a whole number in
the same unit as the `IC.TUNE` key it replaces.

## 4. Starting governments

`IC.START_GOV`, by faction key. AI courts keep this all campaign; player courts start here.

| Faction | Start | Basis |
|---|---|---|
| `wh3_dlc23_chd_astragoth` | priest | CA: High Priest, most senior Sorcerer-Prophet |
| `wh3_dlc23_chd_conclave` | conclave | CA: Servants of the Conclave; the author's "Master of the Conclave" |
| `wh3_dlc23_chd_legion_of_azgorh` | legion | CA: exile lord of the Black Fortress, Infernal Guard |
| `wh3_dlc23_chd_zhatan` | legion | CA: Commander of the Tower of Zharr |
| `cr_chd_house_of_khorakk` | chain | author: "Slave Drivers", the Chainlord |
| `cr_chd_house_of_azeros` | forge | author: "Forge Tyrants" |
| `cr_chd_house_of_bzaark` | forge | author: "Mad Engineers", a Daemonsmith |
| `cr_chd_snakebeards_artificers` | forge | author: master artificer, "Perfectionists" |
| `cr_chd_fists_of_hashut` | legion | author: warlord, "Unholy Legion" |
| `cr_chd_slaves_of_the_black_dwarf` | legion | author: "Granite Legion" |
| `cr_chd_house_of_baal` | priest | author: Sorcerer-Prophet, "Daemonbinders" |
| `cr_chd_horns_of_hashut` | priest | CA: Bull Centaurs guard Hashut's fanes; the house fields the Temple Guard |
| `cr_chd_warfleet_of_uzkulak` | convoy | **inference**: admiral, "chaining every port to the forges" |
| `cr_chd_black_kraken_armada` | convoy | **inference**: a renegade engineer's fleet |
| `cr_chd_skullstack`, `wh3_dlc23_chd_minor_faction`, any other court | derived | no lore basis found |

**Derived start:** at the court's first turn, the government of the rival party with the largest
share, if it has a government (not Crown, not Hearth); otherwise `conclave`, lore's own picture of
Chaos Dwarf rule with no one leading.

## 5. Drift (player courts only)

Run once per court turn, after shares are computed, and only while the Governments switch and the
drift switch are on.

- The **leader** is the rival party with the largest share. Pressure builds only if the leader
  holds at least `gov_drift_share` (30) of the court, has a government, and that government is
  not the current one. Then `gov_pressure` +1 toward the leader's government.
- A different leader **restarts** the count toward its own government.
- **The Crown or the Hearth leading builds no pressure** and does not reset it.
- **A balanced court** - no rival at `gov_drift_share` - builds pressure toward `conclave` at one
  point per `gov_balance_turns` (2) turns, unless the government already is the Conclave.
- No pressure during the court's grace period (`grace_turns`) or a forced change's cooldown.
- At `gov_pressure_line` (6) the choice is offered.

## 6. The choice

A card on the Petitions tab, made with the court's existing petition machinery, plus an event
message. It names the government it would bring and both outcomes.

- **Accept:** the government changes. The new government's party gains `gov_accept_gain` (+10)
  loyalty; the old government's party `gov_accept_loss` (-10). Pressure to 0.
- **Hold:** paid in influence from the Crown's men, `gov_hold_cost` (300) x (1 + holds so far) -
  the price rises each time. Pressure to half the line, rounded down. The leading party loses
  `gov_hold_loyalty` (-8).
- **Ignored** for `gov_choice_turns` (3) turns: the court decides - Accept.
- A choice the leader can no longer back (its government changed, it left the lead) lapses with
  no effect.

## 7. Forcing a doctrine

From the Court tab, any time, through the court's multiplayer-safe send path.

- Five tall cards centred on the screen (author, 2026-10-03, design A; this replaced a six-row
  picker list). The current government is not offered; it is named in a title above the cards
  with its rule and effect. Each card shows the government's picture, name, rule, effect, who
  it pleases and angers in this court (number first, the name cut with "..." if it is too long,
  the whole name in the tooltip), and a button with the price, or in red why it is refused
  (cooldown, cannot pay).
- **Cost:** `gov_force_cost` (400) influence from the Crown's men. The dropped government's party
  loses `gov_force_loss` (-15); the new government's party gains `gov_force_gain` (+5) if it sits
  in this court.
- **Cooldown:** `gov_force_cooldown` (15) turns before another forced change; drift is frozen for
  the same turns.
- A government whose party is not in the court can be forced; it pleases nobody.

## 8. Build

**Model** (`zzz_derpy_iron_court.lua`):
- `IC.GOVS`, `IC.START_GOV`, the new `IC.TUNE` keys above.
- `IC.tune(faction_key, key)`: the court's government override, else `IC.TUNE[key]`. Only the
  call sites reading an overridden key switch to it, about fifteen. A harness check reads the
  shipped Lua and fails if any key named in an override is still read as `IC.TUNE.<key>`.
- Court fields `gov`, `gov_pressure`, `gov_toward`, `gov_cool`, `gov_holds` in a new save section;
  an older save gets its start derived on load. The bundle is applied and removed with the
  government, as the Crown's bands are.
- `IC.gov_turn(faction_key)` (drift), `IC.gov_accept`, `IC.gov_hold`, `IC.gov_force`, each a
  court op through `ICUI.send` / `IC.after_op` like the existing moves.

**Data** (`gen_iron_court.py`): six effect bundles and their loc, the event-feed rows for
"government changed" and "pressure", the petition text. MCT: a **Governments** system switch (on;
off means no government, no bundle, no override), a **drift** switch, and the new numbers in the
difficulty presets and the Custom page.

**Panel** (`zzz_derpy_iron_court_ui.lua`, `gen_ic_ui.py`): the government's name in the Crown's
box with a tooltip (rule, bundle, pressure and what it is heading for); a Change Doctrine button
and its picker; the petition card; a Help paragraph. The layout additions go through the
generator's existing checks and the previews.

**AI:** start government and bundle only.

## 9. Testing

Harness checks, each watched failing first, with mutants:
- every `IC.START_GOV` row, and the derived start (leader with a government, Crown or Hearth
  leading, nobody leading);
- an override reaching only its own court; with the switch off, nothing overridden;
- pressure: builds, restarts on a new leader, ignores Crown and Hearth, balanced pull, frozen in
  grace and cooldown;
- the choice: accept, hold with its rising price, the 3-turn default, a lapsed choice;
- forced change: cost, refusals, both loyalty effects, cooldown;
- save round-trip and an older save;
- multiplayer: every op goes through the send path.

Generator: bundle effects and signs, loc for every bundle, every `IC.TUNE` key in the presets.

## 10. Out of scope

AI drift and AI forced changes; a government per legendary lord; an autocrat or Hearth government;
governments for non-Chaos-Dwarf factions; any government changing the Crown's bands, the office
list or the secession rules.

## 11. Open, for the author

- Khorakk: the court's flavour line calls it a "bull-cult"; the author's loc says slave drivers.
  This spec follows the loc (`chain`).
- The two `convoy` starts are inference; say if either house should start elsewhere.
