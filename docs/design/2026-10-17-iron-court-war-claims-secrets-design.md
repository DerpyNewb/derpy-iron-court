# Iron Court: war council, claims and secrets, design (2026-10-17)

Status: built and deployed to data/ on 2026-10-19 (build 58D5347C). Seen in game on 2026-10-19 (`docs/sessions/LIVE_TEST_20261019_IRON_COURT_WAR_CLAIMS_SECRETS.md`); the ticked checklist is in the plan's ledger, `docs/superpowers/plans/2026-10-17-iron-court-war-claims-secrets.ledger.md`.

Three mechanics borrowed from Bannerlord and Crusader Kings III, picked from the gap analysis of
2026-10-17 ("implement 1-3"):

1. **The war council.** Parties put wars to a court vote. A passed war is declared a few turns
   later, so the armies can get ready.
2. **Claims on conquered land.** Taking a new province makes parties claim its governorship.
3. **Secrets.** An Intrigue move digs up leverage on a party, which the player spends once.

Both races (Chaos Dwarf and Dwarf). Player courts only, as the laws are.

---

## 1. What the author decided

The author answered three questions about the war council, then said "continue without my output,
ill judge the final design after you are done". Their answers:

| Question | Answer |
|---|---|
| What should the court do when you go to war? | "it will get proposed but voting still happens" |
| Does a yes vote start the war? | "war should start after confirming the votes, but war should be declared in a few turns for preparing the armies" |
| Can you overrule the vote? | "yes, at a price of gold or influence" |

Everything else in this document is the designer's call, and section 9 lists those calls for the
author to check. The question left unanswered was what happens when the player declares war from
the diplomacy screen without asking the court (section 2.7 is the call).

---

## 2. The war council

### 2.1 What it is

- A war is a vote, run by the law vote engine (`IC.law_tally` and the functions around it,
  `zzz_derpy_iron_court.lua`). Every man votes with his influence, the Crown's men vote the
  player's side, the player can push, win men, or overrule.
- **One council vote at a time**, kept in `court.votes.council` (`IC.COUNCIL = "council"`). The
  key is not a law category: `IC.LAW_ORDER` already has a category called `war`.
- The vote record is the law record: `{option, proposer, ends, stance, won, push, answered}`,
  with `option` the target's faction key.
- **A passed vote plans the war.** It is declared `war_prep_turns` (3) turns later.
- **One planned war at a time**, `court.war = {target, at, proposer}`. No council vote opens
  while a war is planned.

### 2.2 Who wants war on whom: the facts

Each party's line on a target comes from facts about the target that CA's 9.0 API exposes.
All are read from the court's own faction (`own`) and the target (`them`).

| Fact | Test | API |
|---|---|---|
| `trade` | You have a trade agreement with them. | `own:trade_agreement_with(them)` |
| `near` | They hold a region adjacent to one of yours. | `region:adjacent_region_list()`, `region:owning_faction()` |
| `weak` | They field fewer armies than you. | `military_force_list(true):num_items()` on both |
| `strong` | They field more armies than you. | the same |
| `kin` | They are your own race. | `them:subculture() == R.subculture` |
| `foe` | They are one of your race's old enemies (`R.WAR_FOES`). | `them:subculture()` |
| `book` | Dwarf courts: the Book of Grudges names them. | `IC.in_book(faction_key, them)` |

`R.WAR_FOES`, every key checked against CA's scripts (each subculture appears in 18 to 49 files):

- Chaos Dwarfs: `wh_main_sc_dwf_dwarfs`, `wh_main_sc_grn_greenskins`, `wh_main_sc_grn_savage_orcs`.
- Dwarfs: `wh_main_sc_grn_greenskins`, `wh_main_sc_grn_savage_orcs`, `wh2_main_sc_skv_skaven`,
  `wh3_dlc23_sc_chd_chaos_dwarfs`.

`near` is computed once per turn per court on the turn path and cached, in memory and unsaved, the
way `IC._book` is. The panel reads the cache and fills it only when it is empty.

**The turn's snapshot (designer's call, from the builder check).** Declaring war ends a trade
agreement, probably before the declaration's event reaches the court, so a reaction that read
`trade` live would never hear the Ledger and the Road object to a war on a customer. The same cache
therefore holds the turn's `trade` set, taken at turn start, and `PositiveDiplomaticEvent` with
`is_trade_agreement()` adds a partner signed during the turn. The reactions in 2.7 read `trade` and
`near` from this snapshot. A vote's tally and the panel read every fact live: no war has started
while a vote runs.

### 2.3 The party lines

A new race field, `R.WAR_LINES`: per party slug, an ordered list of `{fact, side}`. The first
fact that holds gives the party's line, and the fact is the reason the panel shows. A party with
no matching fact has no stance and votes on loyalty, the way a law vote's no-stance party does
(`law_loyal_line`, `law_disloyal_line`).

Chaos Dwarfs:

| Party | Lines, in order | Reading |
|---|---|---|
| temple (The Priesthood) | foe aye, kin nay | Hashut's war on the Dwarfs and the greenskins. No war between the houses of Zharr. |
| forge (The Forge) | weak aye | A quick war keeps the furnaces busy. |
| chain (The Chain) | near aye | Border raids bring in slaves. |
| legion (The Legion) | foe aye, weak aye | The army wants the old enemies, and wars it can win. |
| ledger (The Ledger) | trade nay, strong nay | No war on a customer, and none it may lose. |
| tower (The Tower) | none | Votes on loyalty. |
| road (The Road) | trade nay, near nay | War at the border closes the convoy roads. |
| hearth (The Hearth) | kin nay, strong nay | No war on kin, and none that reaches the home kilns. |

Dwarfs:

| Party | Lines, in order | Reading |
|---|---|---|
| temple (The Ancestor Priesthood) | book aye, kin nay | Grudges must be settled. Dwarf does not fight Dwarf. |
| forge (The Forgewrights) | weak aye | A quick war sells weapons. |
| chain (The Deepdelvers) | foe aye | Greenskins and skaven infest the deeps. |
| legion (The Clan Warriors) | book aye, weak aye | "settle grudges with axes" (their member flavour line). |
| ledger (The Reckoners) | trade nay, strong nay | |
| tower (The Runesmiths) | none | |
| road (The Underway Wardens) | trade nay, near nay | |
| hearth (The Hearth Clans) | kin nay, strong nay | |

The Crown has no line: its men vote the player's stance, as on a law. Confederate houses have no
line. Cultures take no stance on wars; the culture stances stay on laws.

### 2.4 Who may be named

A **candidate** is a faction that is all of these:

- alive, met (`own:is_known_faction(them)`), not human, not rebel, not a quest battle faction, and
  not in `R.REBEL_POOL`;
- not at war with you;
- not your ally, vassal, overlord, or a non-aggression pact partner
  (`is_ally_vassal_or_client_state_of` both ways, `non_aggression_pact_with`). A trade partner may
  be named, and the Ledger and the Road vote against it;
- `near`, or (Dwarf courts) `book`.

### 2.5 Proposing

- **A party** proposes through a new `IC.PARTY_ACTS` entry, `council`, when all of these hold:
  - the court has no council vote open and no war planned;
  - its share is at least `war_party_share` (15%);
  - no party has proposed a war for `war_party_rest` (8) turns (`court.council_rest`);
  - some candidate is one its line is aye on. `cm:random_number` picks among them.

  Its motive is `war_party_motive` (14), the laws' own. A party proposal opens with the stance
  `abstain` and is unanswered until the player sets a stance.
- **The player** proposes through a new Intrigue move, **Call the War Council**
  (`council`), in the Missions column. It is a faction-target move like Send Diplomats (it opens
  the faction picker), sure (it never rolls), and costs the acting man `plot_council_cost` (150)
  influence. Unlike the other missions, a man leading an army may make it. Its picker lists every
  faction you have met; a faction that is not a candidate is drawn with its refusal, as Send
  Diplomats does. The vote opens with the stance `aye`.
- A vote runs `law_vote_turns` (2) turns.
- **No council vote opens**, by a party or by the player, during the court's grace period
  (`IC.grace_left() > 0`) or while the author's start-of-campaign truce holds
  (`derpy_no_early_wars.lua`: its saved value `derpy_no_early_wars_turns` is set and
  `derpy_no_early_wars_released` is not). The truce locks war with `cm:force_diplomacy`, and
  `cm:force_declare_war` would declare straight through it. Without that mod the two saved values
  are nil and nothing waits. A planned war whose turn comes while the truce holds waits a turn.

### 2.6 Resolution

At the player court's turn start, after `IC.law_turn`, in a new `IC.council_turn`:

- **A vote whose target changed (designer's call, from the builder check).** Checked first, every
  turn the vote is open:
  - the target is dead, no longer met, or declared war on you: the vote is void. It closes with a
    Record line and no loyalty change;
  - you signed a treaty with it (ally, vassal, overlord, pact): the vote is void, and every party
    whose line is aye loses `war_bypass_loyalty` (10). You settled it without the council, the same
    as a war you start without it (2.7);
  - it no longer borders you: nothing. `near` decides who may be named, not whether a vote stands.
- **Votes.** An open vote at its end resolves by the tally; one not at its end is pushed by the
  parties with a stake, exactly as `IC.law_party_push` pushes a law.
- **Passed:** `court.war` is planned for `now + war_prep_turns`. Parties move loyalty by
  `IC.law_swing` against the parties for and against, as a law does. Feed card `war_passed`.
- **Failed:** a party that proposed it loses `law_fail_loss` (5). Feed card `war_failed`.
- **A planned war at its turn:**
  - the target is dead or no longer met: dropped, Record line only;
  - you are already at war with it: done, nothing more (you started it early, which is allowed
    and costs nothing);
  - you now have a treaty with it (ally, vassal, overlord, pact): **broken by treaty**. Every
    party whose line is aye loses `war_broken_loyalty` (15). Feed card `war_broken`;
  - otherwise the court declares it: `court.war_free[target] = turn`, then
    `cm:force_declare_war(faction_key, target, false, false)`, the arguments CA's own invasions
    pass. Feed card `war_begins`.

### 2.7 Wars and peace you make yourself (designer's call)

The diplomacy screen is not blocked. Blocking it (`cm:force_diplomacy`) would also stop the player
answering allies, and it fights every other mod that touches war diplomacy. Instead the court
reacts, the way CA's own Empire politics does: an elector count's loyalty falls by 2 when a human
Empire declares war on it, with a "free war" exemption (`wh2_dlc13_empire_politics.lua`,
`empire_war_declared`).

- **A war you declare.** `NegativeDiplomaticEvent` with `is_war()`, `proposer()` your human court
  and `recipient()` the target (CA uses this event in 10 files; `FactionLeaderDeclaresWar` names
  only the declaring leader, so it cannot say on whom):
  - the court's own declaration (`court.war_free[target]` set this turn): nothing;
  - a planned war on that target: done, as in 2.6;
  - an open council vote on that target: the vote closes as passed. Parties whose line is nay lose
    `war_bypass_loyalty` (10). No war is planned;
  - otherwise **a war the court was not asked about**: parties whose line is nay lose
    `war_bypass_loyalty` (10), parties whose line is aye gain `war_bypass_gain` (3). Feed card
    `war_unasked`.
- **Peace you make.** `PositiveDiplomaticEvent` with `is_peace_treaty()` and your court on either
  side: parties whose line on the other side is aye lose `war_peace_loyalty` (3); parties whose
  line is nay gain 3. A Dwarf party whose aye line is `book` is skipped: `IC.book_peace` already
  writes that wrong as a grudge.
- **At most one war reaction per party per turn**, in memory (`IC._war_reacted`). Declaring on one
  faction can pull its allies into the war in the same moment, and the court counts that as one
  war.
- Only lines from facts (aye or nay) count here, never loyalty votes.

### 2.8 Overruling and calling off

- **During the vote:** Pass now and Fail now, for `law_overrule_cost` (500) of the Crown men's
  influence, as on a law, **or** for `war_overrule_gold` (2500) gold from the treasury. The gold
  buttons appear on a war vote only. Either way the losing parties lose `law_overrule_loyalty`
  (10). A war passed by overrule still waits its preparation turns.
- **During the preparation turns:** the planned war's Petitions row offers **Call Off** for the
  same two prices. Every party whose line is aye loses `law_overrule_loyalty` (10). Feed: none
  (the player did it); Record line.

### 2.9 Numbers

New `IC.TUNE` constants, not on the MCT page, in the laws' own block:

| Key | Value |
|---|---|
| `war_prep_turns` | 3 |
| `war_party_share` | 15 |
| `war_party_rest` | 8 |
| `war_party_motive` | 14 |
| `plot_council_cost` | 150 |
| `war_overrule_gold` | 2500 |
| `war_broken_loyalty` | -15 |
| `war_bypass_loyalty` | -10 |
| `war_bypass_gain` | 3 |
| `war_peace_loyalty` | 3 |

Signs follow the laws' convention: a key whose name says loss or loyalty-hit is stored negative and
added. The plan fixes each sign against its call site and the harness asserts the direction.

---

## 3. Claims on conquered land

### 3.1 When

`GarrisonOccupiedEvent`, which the court already listens to (`ic_took`). CA's rites read
`faction:region_list()` at this event and count the taken region, so ownership is already the
new owner's. A claim is raised when:

- the occupier's faction runs a player court;
- the region's province holds no other region of the court (it is a **new** province);
- the `claims` switch is on.

Provinces gained another way (confederation, a gift, a treaty) raise no claims.

### 3.2 Who claims

Up to `claim_max` (3) claims, one per party, rival parties only, in this order:

1. **By conquest:** the occupier's party. Its man is the occupier if he holds no post, else the
   party's richest free man.
2. **By home:** on the Old World map, the main party of the culture whose home list holds the
   province (`R.HOME_OF`), with its richest free man. Every home key is an Old World key, so on
   any other map this step never claims.
3. **By weight:** the rival parties not yet claiming, largest share first, each with its richest
   free man, **until the claims number `claim_max`** (designer's call, from the builder check). A
   party with no free man is passed and the next one asked, so a Crown occupier on Immortal
   Empires still meets up to three claimants when the court has three rivals with free men.

A party with no free man makes no claim. "Free" is `IC.candidates`' `busy` flag, as demands use
it. Ties in share go to `IC.present_houses` order, the same on every machine. No claimant, no
claims.

### 3.3 The record

`court.claims[province] = {ends, list = {{slug, cqi, why}, ...}}`, `why` one of `conquest`,
`home`, `weight`. `ends = now + claim_turns` (3). Several provinces may have claims open.

### 3.4 Answering

On the Petitions tab, one row per claim: the man's porthole and his party's crest, "Claims
<province>: N turns", **Grant** and **Refuse**. The tooltip says why he claims it and what each
answer costs.

- **Grant:** `IC.assign_governor(province, cqi)`. The claimant gains `claim_granted` (8); every
  other claimant on that province loses `claim_passed` (4). The province's claims close.
- **Refuse:** that claimant loses `claim_refused` (6), and on a Dwarf court a `demand` grudge is
  written (a claim refused is a demand refused). The other claims stay open.
- **Any governor you appoint there** (the Governors tab, the map picker, a granted demand) is
  answered through one hook in `IC.assign_governor`: a claimant appointed is a grant, anyone else
  passes every claimant over (`claim_passed`). One place, so every route to a governor is covered.
- **Unanswered at its end:** the court decides. The remaining claim whose party has the largest
  share is granted, by the same path as Grant. This follows the governments' precedent, where an
  unanswered choice is accepted (`IC.gov_expire`).
- **Void:** a claimant who died, left the court or took another post is dropped. A province no
  longer held drops all its claims.
- **Demands stay off a claimed province (designer's call, from the builder check).**
  `IC.demand_target` picks any held province with no governor, so a fresh conquest would be a
  demand target at the next turn start, and answering the claims would then settle that demand as
  refused, a second penalty for one decision, and in the lapse case one the court made itself.
  `IC.demand_target` therefore skips a province with open claims. Once its claims close, the
  province is an ordinary demand target again.

### 3.5 Numbers

| Key | Value |
|---|---|
| `claims` | true (the live switch) |
| `claim_max` | 3 |
| `claim_turns` | 3 |
| `claim_granted` | 8 |
| `claim_passed` | -4 |
| `claim_refused` | -6 |

### 3.6 Cards

- `claims_laid`: raised once per province, its province name as the subtitle.
- `claim_taken`: the court granted an unanswered claim.

---

## 4. Secrets

### 4.1 Digging

A new Intrigue move, **Dig for Secrets** (`dig`), in the On a Party column. That column holds two
Chaos Dwarf moves and three Dwarf ones, so neither grid gets deeper than its four-move columns.

- Aimed at a man of a rival party, like Strike Their Seats. The secret is on **his party**.
- Costs `plot_dig_cost` (120) of the actor's influence; chance `plot_chance_dig` (55), with the
  usual influence edge and bounds.
- Refused when you already hold a secret on that party (`held`).
- Success: `court.secrets[slug] = turn`. Failure: the usual `plot_fail_loyalty` hit.
- One secret per party. It does not expire. It is lost when the party leaves the court.

### 4.2 Using

A fifth button on the Court tab's action bar, **Use a Secret**, opens a picker for the chosen
party. Each use spends the secret. The rows that apply are listed; the rest are not drawn.

| Use | When it is listed | Effect |
|---|---|---|
| Their men vote your way on <vote> | per open vote (laws and council) on which you have taken a side | every man of the party is won to your side for that vote, free |
| Drop their demand | the live demand is theirs | the demand ends as void: no grant, no refusal, no cost |
| Call off their scheme | the warned plot is theirs | the plot is dropped, as `IC.drop_party_business` drops one |
| Stop their countdown | their secession count is running | the count stops (`clock = 0`) |
| Expose them | always | their strength falls by `secret_expose_weight` (10), their loyalty by `secret_expose_loyalty` (10); on a Dwarf court an `insult` grudge is written |

Every use but Expose costs the party `secret_use_loyalty` (5) loyalty: they know they were
blackmailed.

With no secret held, the button is drawn refused, and its tooltip points at Dig for Secrets.

### 4.3 Numbers

| Key | Value |
|---|---|
| `plot_dig_cost` | 120 |
| `plot_chance_dig` | 55 |
| `secret_use_loyalty` | -5 |
| `secret_expose_weight` | 10 |
| `secret_expose_loyalty` | -10 |

---

## 5. The panel

No new tab: the tab row is full (seven tabs end at x 1722 of 1920).

| Where | What |
|---|---|
| Petitions | A council vote row ("<proposer> proposes war on <faction>: N turns", **Vote** opens the vote screen); a planned war row ("War on <faction> in N turns", **Call Off** twice, priced in influence and in gold); one row per claim. |
| Petitions marker | Also lit by an unanswered council vote and by any open claim. |
| The vote screen (Laws tab) | Draws a council vote: the target's flag (`flag_path() .. "/mon_64.png"`, as `IC.house_icon` reads it), "War on <faction>", "Declared N turns after it passes", sides "Declare war" and "Keep the peace", each party's line with its fact in a few words ("for it: an old foe"). Back returns to Petitions. Two new buttons, `ic_lv_over_3` and `ic_lv_over_4`, under Pass now and Fail now, priced in gold, shown on a war vote only. |
| Intrigue | Call the War Council (Missions) and Dig for Secrets (On a Party). |
| Court tab action bar | Use a Secret, the fifth button. Four buttons are 650px of the 926px column now. |
| Picker | A `secret` kind: the uses for the chosen party. The council move reuses the faction picker. |
| Record | Lines for every new event (section 6). |
| Help | `ICUI.HELP_SLOTS` from 12 to 14, the box grown to hold them. A new topic, **The War Council**; three lines on claims in Petitions; two lines on secrets in Intrigue. |

Every new string follows the player-text rules: plain words, no dashes, no "guild" or Chaos Dwarf
words on a Dwarf court. A faction's name is CA's own loc key `factions_screen_name_<key>`, which CA
itself passes to `cm:show_message_event`; a province's is `provinces_onscreen_<key>`, as the
demands already read it.

Rendered with `tools/preview_iron_court.py` for both races at 1600, 1920 and 2560 before it is
called done: the Petitions list with all three new row kinds, the war vote screen, the secret
picker, the Court tab with five buttons, and the new Help topic.

---

## 6. Model plumbing

- **The vote engine, generalised by one helper.** `IC.vote_stance(faction_key, category, option,
  party, culture)` returns a side and a reason: for `IC.COUNCIL` it is the war line (2.3), for a
  law it is `IC.man_stance`'s. Its callers: `IC.law_line`, `IC.law_win_price` (the doubled
  price), `IC.law_party_push`. `IC.law_vote_of` checks the `council` switch for a council vote and
  `laws` for a law. `IC.law_overrule` takes a fourth argument, `gold`, and for a council vote
  settles through the council's own settle function, not `IC.law_settle`.
- **Record kinds:** `council_propose` is the law kinds' `law_propose` with key
  `council.<faction key>`; the panel's `ICUI.law_title` learns that key. New kinds: `war_planned`,
  `war_begins`, `war_called`, `war_broken`, `war_unasked`, `war_peace`, `claim`, `claim_granted`,
  `claim_refused`, `claim_passed`, `claim_taken`, `dig`, `secret_used`.
- **Feed cards**, appended to `IC.EVENTS` and the generator's `EVENTS` in the same order:
  `war_proposed`, `war_passed`, `war_failed`, `war_begins`, `war_broken`, `war_unasked`,
  `claims_laid`, `claim_taken`. The war cards take the target's name as their subtitle and the
  claim cards the province's (third field false). The two Dig results are move results, as every
  move's are.
- **Save:**
  - field 18 also carries the council vote, with category `council` and the faction key as its
    option;
  - field 21: `target,at,proposer` for the planned war, then `rest,<turn>`;
  - field 22: claims, `province,ends,slug:cqi:why/...` per province;
  - field 23: secrets, `slug,turn` per party.

  All optional: an older save loads with none.
- **Multiplayer:** court ops through `ICUI.send` and `IC.mp_receive`, each re-checked by the
  model: the law ops with category `council`, `law_overrule` with the gold flag, `war_calloff`
  (influence or gold), `claim_grant`, `claim_refuse`, `secret_use`. Party proposals, resolution,
  claims raised on capture and the war reactions all run on model events, the same on every
  machine.
- **Switches:** `council` ("War council") and `claims` ("Claims on conquest") appended to the end
  of `IC.TUNE_ORDER`, to `IC.LIVE_TUNE`, the MCT page and the harness `LIVE` list. Off, `council`
  drops the open vote and the planned war and stops the reactions; `claims` drops open claims and
  raises none. Dig for Secrets has no switch.
- **Race fields:** `WAR_LINES` and `WAR_FOES` join `IC.RACE_FIELDS`, so a race without them is
  refused at registration. `DWF.PLOT_KEYS` gains `council` and `dig`, `DWF.PLOT_TEXT` their Dwarf
  words.
- **Party departure:** `IC.drop_party_business` also drops the party's claims and its secret.

---

## 7. Tests

Harness checks (`tools/_iron_court_harness.lua`), each watched failing first:

- every fact (2.2) on a stubbed world, including `near` from adjacency and its turn cache;
- each party's first-match line, a party with no fact voting on loyalty, the Crown on the
  player's stance;
- candidates: each exclusion in 2.4, and Dwarf `book` reaching past `near`;
- the party proposal's conditions and rest, and the random pick;
- the council move: sure, faction target, a general allowed, its price, its refusals;
- a passed vote plans the war at `now + war_prep_turns`; a failed one charges the proposer;
- a planned war's four outcomes at its turn, and the free-war flag set before the declaration;
- overrule both ways for influence and for gold, the gold buttons' prices, call-off both ways;
- the reactions: an unasked war, a war on an open vote's target, a war on the planned target,
  peace, the Dwarf `book` skip, and one reaction per party per turn;
- claims: a new province only, the three claimants in order with dedupe and no-free-man skips,
  grant, refuse (with the Dwarf grudge), every route to a governor through the one hook, lapse by
  share, void cases;
- secrets: dig success, failure, `held`; each use's conditions and effect; loss when the party
  leaves;
- the save round trip of fields 18, 21, 22 and 23, and an older save;
- both switches off and on;
- AI courts untouched;
- each MP op re-checked;
- the panel: the Petitions rows, the war vote screen's texts and gold buttons, the secret picker,
  the fifth action button, the Help topic and its slots.

Mutants under `war:`, `claim:` and `secret:` prefixes in `tools/mutate_iron_court.py`.

Gates: `gen_iron_court --check` (the new loc, events, and move rows), `gen_ic_ui --check` (every new
cell fits at 1600, 1920 and 2560), `preview_iron_court.py` (the pictures in section 5),
`check_ic_release.py --pack` (re-pinned only after reading every moved line), `luac`,
`check_lua_api.py`, `check_lua_literal_left.py`, `check_lua_undeclared.py`, the import gate.

**Owed in game** (none of these can be seen offline):

- `NegativeDiplomaticEvent` on a declaration: who is the proposer when allies are pulled in;
- whether the trade agreement is already gone when that event reaches the court (the snapshot in
  2.2 covers either answer, and the check says whether it was needed);
- `cm:force_declare_war` raising the same event, and the free-war flag holding;
- `cm:force_declare_war` against the truce's `cm:force_diplomacy` lock, which 2.5 assumes it would
  break through;
- `GarrisonOccupiedEvent` on Occupy, against Raze and Sack, and the region already owned;
- `factions_screen_name_<key>` resolving for a modded faction (the `cr_` houses);
- the new Help box and buttons at all three resolutions.

---

## 8. Out of scope

- Peace votes. A peace is a reaction (2.7), never a vote.
- AI courts voting on war, claiming land or digging secrets.
- Rival parties digging secrets on the Crown or on each other.
- A secret on one man rather than his party.
- A multi-candidate governor vote. A claim is a petition, decided by the player or, unanswered,
  by share.
- Claims on provinces gained without a capture.
- Blocking war declarations on the diplomacy screen.
- MCT sliders for any new number.

---

## 9. The designer's calls, for the author to check

1. The diplomacy screen stays open; the court reacts to wars and peace you make (2.7).
2. The facts and party lines in 2.2 and 2.3, including the two parties with no war stance (the
   Tower and the Runesmiths).
3. A party may only name a faction on your border, or one the Book names (2.4).
4. The player's proposal is an Intrigue move with an actor who pays, not a button on the Laws tab
   (2.5): the tab row is full and the faction picker already exists.
5. A planned war you start early from the diplomacy screen is free (2.6), and a treaty during the
   preparation breaks it for loyalty alone (2.6).
6. The gold overrule exists on war votes only, not on laws (2.8).
7. Claims are petitions and not a vote; unanswered, the court grants the claim of the party with
   the largest share (3.4).
8. A refused claim is a Dwarf grudge, written as a refused demand (3.4).
9. A secret is on a party, has five uses, never expires, and the blackmail uses cost the party 5
   loyalty (4.2).
10. Every number in 2.9, 3.5 and 4.3.
11. From the builder check: the reactions read the turn's `trade` and `near` snapshot (2.2); no
    council vote opens in the grace period or under the start-of-campaign truce (2.5); a vote
    whose target signs a treaty with you is void and costs the aye parties 10 (2.6); claims by
    weight fill every slot up to `claim_max` (3.2); demands skip a claimed province (3.4).
