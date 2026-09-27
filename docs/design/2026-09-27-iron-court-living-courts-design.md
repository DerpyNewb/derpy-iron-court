# The Iron Court - living courts: design

2026-09-27. Author's request: "do all" - build every item confirmed missing from the 2026-09-11
design, checked against the shipped Lua the same day. The design itself was approved in chat
("continue") after one question, answered: a vassal becomes ONE PARTY in its master's court.

Out of scope, by decision: the Overseer agent (governors stay ordinary lords, a deliberate
change); offers made by AI parties; event cards for AI news other than secessions; new MCT
sliders (every new number is an internal `IC.TUNE` value).

The court is PARTIES INSIDE ONE FACTION, not the 2026-09-11 design's houses-as-factions. Where
that design says "house", this one means a party (`court.houses[slug]`).

---

## 1. One new mechanism: a stalled office

An office whose faction-wide bonus is switched off until a turn.

- State: `court.stalled[office_slug] = {until = turn, of = party slug, by = party slug,
  cause = "sabotage" | "withhold"}`. `of` is the party whose man holds the office; `by` is
  the party that caused it.
- `IC.apply_office_bundles` applies neither the office bundle nor its vacancy bundle for a
  stalled office.
- A stall ENDS when `turn >= until`, or when the office's holder is no longer of party `of`
  (dismissed, died, replaced). Checked in `IC.turn` before `apply_office_bundles`, and again
  wherever an office changes hands, so a stall never outlives the man it was aimed at.
- Saved as a new court field 11: `office,until,of,by,cause` joined by `;`. Older saves have
  no field 11 and load with no stalls.
- Panel: the Offices tab card of a stalled office says `Stalled - N turns` in red, and its
  tooltip names who did it and why ("The Circle of the Tithe's men are withholding their
  service." / "Sabotaged by the Legion of Azgorh.").

## 2. Sabotage (party against party)

A new feud move. `IC.PARTY_ACTS.feud_move` tries, in order, `murder` (only once the feud is
`party_feud_murder_age` old, as now), then `sabotage`, `discredit`, `rumour`.

- Target: an office held by the enemy party's man that is not already stalled
  (`IC.party_target(..., "sabotage", enemy)` returns the holder cqi and the office slug).
- Cost and odds: through `IC.party_strike`, like every other party move. New tune values
  `plot_sabotage_cost = 200`, `plot_chance_sabotage = 50`.
- On success: stall the office for `sabotage_turns = 3`, `cause = "sabotage"`. Log kind
  `sabotage` (slug = the saboteur, key = the office). Card `party_sabotage` only when the
  office's party is the human's own Crown; otherwise log only.

## 3. Withhold (an angry party)

A new party act, `withhold`.

- Can: the party's loyalty `<= withhold_line = 30`, it holds at least one office, and none
  of its offices is already stalled.
- Motive: `withhold_motive = 40`, plus 1 per loyalty point below the line.
- Act: stall EVERY office its men hold for `withhold_turns = 3`, `cause = "withhold"`. Log
  kind `withhold`; card `party_withhold` for a human court.
- Secure Loyalty on that party ends its withholding at once (clears the stalls with
  `by == slug` and `cause == "withhold"`).

## 4. Settle a feud (arbitration)

A running feud appears on the Petitions tab as TWO rows, one per party in it:

- Row text: `<Party> - feuding with <other party> over <the office / their equal standing>`.
- Button E: `Back Them` - this party gains `arbit_side_loyalty = 10`, the other loses 10,
  the feud ends.
- Button F: `Make Peace` (same action on both rows) - costs `favour_gift_cost` gold (so the
  difficulty scales it), both parties gain `arbit_peace_loyalty = 3`, the feud ends.
- Refused as the gift is: `gold` when the treasury is short; the tooltip carries the price
  and what it buys.
- A feud ended here sets the same calm rest as a feud that ends on its own
  (`party_feud_rest`), logs `arbit_side` or `arbit_peace`, and shows no card.
- Model: `IC.arbitrate(faction_key, slug, side)` where `side` is `"back"` or `"peace"`,
  and `slug` is either party in the feud. Returns `ok, why, spare` like `IC.favour`.
- Multiplayer: a new transport op `arbit` (`party|side`), answered through
  `IC.after_op` like the other eleven.

## 5. AI courts act

`IC.party_turn` runs for AI courts too (it returns early today for any non-human).

- **Rotation, for cost.** Only `ai_party_courts = 3` AI courts take a party turn per
  round. Every AI court whose court this campaign runs is put in key order; court number
  `i` of `n` takes its party turn when `(turn + i) % ceil(n / 3) == 0`. Deterministic, so
  both machines of a multiplayer game agree.
- **What an AI party does:** everything a human court's party does - schemes against its
  ruler's party (`intrigue`), feuds and feud moves (now with Sabotage), Withhold, demands -
  EXCEPT offers, which stay human-only. The same `IC.PARTY_ACTS` table and the same one act
  per party turn.
- **AI demands resolve at once.** No mission is issued for an AI court. The AI ruler grants
  when `IC.can_grant_demand` allows it and the party's loyalty is below `ai_grant_line = 50`;
  otherwise it refuses, with the loyalty cost a human refusal has, and the refused party
  rests `party_demand_rest` turns as it does for a human.
- **The AI ruler keeps a party from leaving.** After the party act, once per AI party turn:
  for the party with the lowest loyalty among those whose secession clock is running, buy
  Secure Loyalty if `IC.can_favour` allows it; failing that, a Gift. Paid from the AI
  faction's treasury through `IC.favour`, so the one-gift-per-turn rule holds for AI too.
- The `parties_act` MCT switch governs AI courts as it governs the human's; `ai_courts` off
  still means no AI court at all.
- Cards: `IC.feed` stays human-only; AI courts produce news instead (section 6).

## 6. News of AI courts

- **Where:** the Log tab. The panel's own text can name anything; event cards cannot, since
  their text is loc-keyed. News lines are interleaved with the court's own entries, newest
  first, and start with the other faction's name, e.g. `Turn 34 - The Legion of Azgorh:
  the Circle of the Tithe broke away and rose in rebellion.`
- **What:** secession, dissolution, the Crown splitting, a feud starting, a feud murder that
  lands, a vassal breaking away (section 8), a party's demand granted or refused.
- **Who hears:** every human faction that has met the AI faction
  (`faction:factions_met()`), and not the AI faction itself.
- **Stored** in each human court as `court.news`, capped at `news_max = 30`, as
  `{turn, text}`. The text is composed when the event happens, because a seceded party's
  name is gone afterwards. Saved as a new court field 12; `|`, `;` and `,` in the text are
  replaced before saving so they cannot break the format. Older saves load with no news.
- **One card:** an AI court's secession also raises the new event `realm_secede`, located at
  the region where the rebels rise, so its camera button goes to the war. It is not a
  routine event, so switching `all_cards` off does not hide it.

## 7. Governors grow with rank

`IC.apply_governor_bundles` builds the base governor bundle per province at runtime:

- `cm:create_new_custom_effect_bundle("derpy_ic_gov_base")`, keep its own effects, then
  `add_effect` two more:
  - public order: `+1` per `gov_rank_order_per = 5` ranks (rank 40: +8);
  - province income: `+1%` per `gov_rank_income_per = 2` ranks (rank 40: +20%).
- Applied with `cm:apply_custom_effect_bundle_to_faction_province`, which replaces the
  record's previous instance, so a rank-up, a new governor or a lost province needs no
  special case. Removal stays as today (`remove_effect_bundle` of the base key).
- The two effect keys and their scopes are taken from vanilla governor/commandment bundles
  and checked against the DB before use (the plan names them); a key that does not exist
  fails silently, so `import_iron_court.verify` asserts both.
- The party's own governor bundle (`derpy_ic_gov_house_<slug>`) is unchanged.
- The Governors tab's tooltip for a governor lists the two rank bonuses with their numbers.

## 8. Joining and leaving

**Confederation carries loyalty.** On `FactionJoinsConfederation`, before the absorbed
faction's court state is dropped, the incoming party's loyalty is the absorbed court's
average party loyalty weighted by each party's weight, clamped to `[25, 75]`. With no court
state for it (AI courts off), `loyalty_start` as now. The absorbed court's countdowns, feuds,
plot and demand are discarded with it. If the absorbed faction was already this court's
vassal party (below), that party's own loyalty carries over instead.

**A vassal is one party.** Chaos Dwarf factions only.

- On `FactionBecomesVassal` (`context:vassal()`, master read as `vassal:master()`), and at
  every turn start for vassals that existed before this build, the master's court gains a
  party: the vassal's origin slug (as confederation uses), with `vassal = <faction key>` on
  the house record. A vassal that is no longer one (`is_vassal_of` false) loses its party.
- It has no men, so it holds no office, governs nothing, and cannot plot or be plotted
  against; the moves that need a party's man already refuse it ("No one speaks for...").
- It takes NO share of the court: weight 0, and excluded wherever the share is summed.
- Loyalty moves as any party's does: drift, Send a Gift, Secure Loyalty, Hold the Ash Court.
- Its countdown starts when its loyalty is at or below `secede_loyalty`, whatever its share,
  and runs `secede_turns` as a secession clock does. Secure Loyalty holds it, as for any party.
- At zero: `cm:force_break_vassalage(vassal key)`, the party leaves the court, relations
  sour between the two as for rebels (`IC.rebel_sour`), log `vassal_broke`, card
  `vassal_broke` for a human master, news for everyone else who has met them.
- The party card says `Vassal` where a party's member count would be.
- Saved as house field 19: the vassal's faction key, or `-`. Older saves read none.

**Other factions dislike rebels.** `IC.rebel_sour_all` also sours every other living Chaos
Dwarf faction on the rebels, by at most `rebel_relation_others_max = 2` steps each (the
faction they left and the human players keep the existing, larger amount).

---

## 9. What the player sees, in short

- Offices go dark for a few turns when a feuding party sabotages them or an angry party
  withholds its men's service, and the Offices tab says so.
- Feuds can be ended on the Petitions tab: back one side, or pay to make peace.
- AI courts scheme, feud, demand and break apart on their own, and the Log tab reports it;
  a rising in an AI court gets a card that shows where.
- Governors grow more useful as they rank up.
- A confederated faction arrives as loyal or as resentful as its own court was.
- A Chaos Dwarf vassal is a party with a loyalty bar; neglect it and it breaks free.
- A rebellion anywhere makes the other Chaos Dwarf factions think less of the rebels.

## 10. Testing

- Every section gets harness checks, each watched failing before its code exists.
- Save compatibility: a check loads a court packed in today's format (no fields 11-12, house
  fields ending at 18) and asserts nothing shifts.
- Determinism: a check runs the AI rotation over several turns and asserts the same courts
  take their party turn for the same inputs.
- The new moves and the stall mechanism get mutation anchors in `tools/mutate_iron_court.py`.
- Gates as for every build: harness, `luac`, `check_lua_api`, `check_lua_literal_left`,
  `gen_ic_ui --check` and `--selftest`, `gen_iron_court --check` (new event rows and loc),
  `import_iron_court.verify()`, the preview.
- In game, after deploy: a stalled office card, a feud on the Petitions tab and both
  buttons, a Log tab news line, a governor's bonus at two ranks, a vassal party, and one
  AI secession card.
