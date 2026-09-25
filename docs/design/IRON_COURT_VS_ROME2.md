# The Iron Court against Rome 2's politics

Audited 2026-09-13 against `rome 2 politics.md` (HappyCompyTW's 2021 guide, transcribed with
screenshots) and the shipped `derpy_iron_court.pack`.

**Built 2026-09-13, same day: 2.1, 2.2, 2.3, 2.4, 2.5 and 2.6 — the whole of the suggested
order in §5.** Each is marked BUILT below with what shipped. The other five followed by
2026-09-20, so every §2 item is now built; 2.7 and 2.11 have not yet been seen live (see §5).

The question this answers: **which of Rome 2's politics mechanics does the Iron Court already
have, which are missing, and of the missing ones, which can actually be built in WH3.**

Read `docs/CUSTOM_UI.md` before touching the panel half and `docs/RITUALS.md` before building
anything that needs a rite.

---

## 1. What is already there

Mapped section by section against the guide. Nothing in this table is a gap.

| Rome 2 | Iron Court | Where |
|---|---|---|
| Influence = share of the senate, from summed gravitas | `IC.share(court, slug)` off house weight; the radial dial | model `IC.share`, panel `draw_court` |
| Influence tiers with faction-wide effects | `IC.CONTROL` — five bands (lost / contested / command / mastery / grip) against Rome 2's four, each an effect bundle | `IC.CONTROL`, `CONTROL_BANDS` in `gen_iron_court.py` |
| Party loyalty; positive loyalty = no civil war | `court.houses[slug].loyalty`, 0-100 | `IC.drift_loyalty` |
| Civil war / secession of a disloyal party | secession clock, rebellion raised as `IC.REBEL_FACTION` | `IC.tick_secession`, `IC.secede`, `IC.raise_rebellion` |
| Parties hold territory; it secedes with them | per-province loyalty, party-by-province, defection at a floor | `court.prov`, `IC.province_party`, `IC.defecting_provinces` |
| Loyal parties buff the provinces they hold | `derpy_ic_gov_house_*` bundles | `IC.apply_governor_bundles` |
| Promote their characters: +loyalty, +their influence | appointing a rival's man to an office: `+8` loyalty and `weight_per_office` to his party | `IC.appoint` |
| Gravitas per character | `court.standing[cqi]` | `IC.standing`, `IC.add_standing` |
| Gravitas from battles, settlements, rank, and a trickle | `battle_influence`, `settlement_influence`, `rank_influence`, `influence_trickle` | the `ic_battle` / `ic_took` / `ic_rank` listeners |
| Hire politicians for gravitas | `IC.HIRE`, bought into the lowest band at `hire_standing` | `IC.hire`, `IC.hired` |
| Intrigues | four plots: Bribe, Discredit, Spread Rumours, A Forge Accident | `IC.PLOTS`, `IC.plot` |
| Gravitas is the only thing that moves influence | weight moves on offices, governorships and plots only | `IC.house_weight` |
| Loyalty breakdown: every term, and what it nets to | the Loyalty cell's tooltip, term by term with the seat each is about | `IC.loyalty_terms`, `ICUI.loyalty_tip` |
| Three party traits, the third belonging to the leader | two rolled per party and kept forever; the third derived from the highest-standing member, so a knife rerolls it | `IC.PARTY_TRAITS`, `IC.LEADER_TRAITS`, `IC.party_leader` |
| Secure Loyalty: no rebellion for N turns, expensive, reusable | an oath sworn on the anvil - stops the clock, outranks the pressure, lapses | `IC.favour("secure")`, `IC.protected_for` |
| Gifts: cheap short-term loyalty | 600 gold for +2, Rome 2's own figures | `IC.favour("gift")` |
| Politicians earn gravitas, generals earn none | `has_military_force()` gates the trickle, except a garrison commander (`IC.is_colonel`), whose garrison is a force though he never leaves home; the seat's wage is untouched | `IC.trickle_for` |
| Battles and deaths move party loyalty | a victory pleases the winner's party, a death costs the dead man's | the `ic_battle` and `ic_dead` listeners |

Two things the Iron Court has that Rome 2 does not: **fixed terms** (a seat empties itself after
`term_turns`, so a court is a standing decision rather than a turn-3 setup) and **standing bars
per tier** (a seat is a bar a man has to clear, not just a title you hand out).

---

## 2. Missing, and implementable

Ordered by value for the work. Every route below was checked against CA's own docs or the
existing code, not assumed.

### 2.1 The loyalty breakdown (guide §5, image 07)

**BUILT 2026-09-13.** `IC.loyalty_terms(faction_key, slug)` returns the terms as a list and `IC.loyalty_net` sums them; `IC.drift_loyalty` is now that sum and nothing else, so the tooltip cannot show a breakdown the turn did not apply. The panel resolves the labels at draw time (`ICUI.loyalty_tip`) and hangs them on the Loyalty cell. The terms carry the office each is about, so a snub names the seat.

**The single cheapest high-value gap.** Rome 2's readability comes almost entirely from one
tooltip: `Bigot -7, Xenophobe -10, Promoted characters +2, Government Type +15` netting to `0`.
The player can see exactly which lever to pull.

The Iron Court shows a **number and a mood word** — `22%, 54 loyalty - RESTLESS` — and nothing
about why.

`IC.drift_loyalty` **already computes every term** (offices held, governorships held, the
affinity snub) and then throws them away, writing only the net. The work is to accumulate them
into a list and draw it on the Loyalty cell's tooltip.

- Route: return a `{{label, n}, ...}` list from `drift_loyalty`, store it on the house, resolve
  the labels at draw time (never in a turn handler — a loc call there is a turn-1 CTD).
- Cost: small. No DB, no art.

### 2.2 Party traits, and the leader trait (guide §4)

**BUILT 2026-09-13.** Eight party traits, two rolled per party and stored as indices in the save exactly as the rolled name is; six leader traits derived from the highest-standing member's cqi, so nothing is stored and killing him rerolls it. Most negatives are conditional on something the player can act on - Grasping wants a province, Zealots want the Crown to hold its own court, Traditionalists want their own seat. `IC.TUNE.party_trait_scale` moves the whole system's weight at once.

**The values are RATES, not levels.** Rome 2's -7 and -10 are terms in a standing loyalty; the Iron Court's loyalty drifts, so these run every turn. The first cut used Rome 2's magnitudes and the harness caught it immediately: a party with a bad roll lost ground while holding a seat. Rescaled so the worst pair is -4 and the leader -2.

The biggest *systemic* gap. Rome 2 gives each party three traits: two belong to the party
forever, the third belongs to its **leader** — so assassinating the leader rerolls it. That one
rule is what makes Rome 2's murder intrigue a political instrument rather than a spite button.

The Iron Court has **no party traits and no notion of a party leader**. Its "A Forge Accident"
plot kills a man and angers his house, and that is all it does.

- Route: two rolled trait indices per party in the save (exactly how the party *name* is already
  stored — two indices, `IC.NAME_HEADS` / `IC.NAME_TAILS`), plus a third derived from the party's
  current leader. Leader = highest-standing member of that party, recomputed each turn; the crown's
  is `faction:faction_leader()` (documented). Traits are loyalty modifiers, so they drop straight
  into the breakdown from 2.1.
- Cost: moderate. Pure Lua plus loc rows. No new DB tables.
- Note: this makes `murder` do what Rome 2's assassination does, using machinery that already exists.

### 2.3 Secure Loyalty (guide §9)

**BUILT 2026-09-13.** 2500 gold buys `favour_secure_turns` turns in which the party cannot leave. Stored as the turn it ENDS rather than a countdown, so nothing ticks it and a save that skips turns cannot leave it running. It outranks the secession pressure as well as the anger - a version that cleared only the loyalty branch would have sold a guarantee a strong rival walked through.

The panic button: expensive, guarantees no rebellion for 5 turns, reusable.

The secession clock already exists (`court.houses[slug].clock`), so this is "clear the clock and
block it for N turns" plus a gold cost. **The icon is already in the pack** — `icon_secure_loyalty.png`
is what the panel currently uses to mark every price.

- Route: a court action + `cm:treasury_mod`; a `protected_until` turn on the house.
- Cost: small.

### 2.4 Gifts (guide §6)

**BUILT 2026-09-13.** 600 gold for +2 loyalty, Rome 2's own figures. Refused at 100 loyalty rather than sold as a no-op.

`+2 loyalty for 600 gold` in the guide. Cheap, short-term headroom against a surprise.

- Route: same shape as 2.3, smaller numbers.
- Cost: small.

### 2.5 Generals earn no gravitas; politicians do (guide §11)

**BUILT 2026-09-13.** `IC.trickle_for` gates `influence_trickle` on `character:has_military_force()`, which is true for an embedded hero as well as the lord commanding. The seat's wage, battle standing, settlements and ranks are untouched: the gate is on the idle trickle alone. `influence_trickle_general` is a knob rather than a hard zero, because nearly every Chaos Dwarf character is in a force and whether the trickle survives at all is a question about a campaign.

This is the mechanic that turns army command into a political tool — park a rival's man in a
trash stack far from the front and he stops gaining influence; strip your own family of command
in peacetime and they farm it.

The Iron Court pays `influence_trickle` **flat to everyone**, so command is politically free.

- Route: `character:has_military_force()` — documented, returns bool. Gate the trickle on it.
- Cost: one line in `IC.income`, plus a check and a mutant.
- This is the highest gameplay-per-line item on the list.

### 2.6 Battles and deaths move party loyalty (guide §12)

**BUILT 2026-09-13.** Both listeners already resolved the house to pay the man and used it for nothing else. A murder now costs two separate terms - `plot_murder_loyalty` for who arranged it and `loyalty_member_died` for losing him at all - with the harness pinning both by name.

Rome 2: a party member dying in battle tanks that party's loyalty; winning with them raises it.

The Iron Court's `ic_battle` listener pays the **character standing** and touches loyalty not at
all; `ic_dead` removes the man's office and docks his party's weight, but again leaves loyalty
alone.

- Route: both listeners already exist and already resolve the character's house. Three lines each.
- Cost: trivial.

### 2.7 Ambition as a gravitas multiplier (guide §8)

Rome 2 shows a lightning bolt; ambition multiplies how much a character's gravitas contributes to
their party's influence. The rule it creates — *stack gravitas on your own ambitious men, keep it
off ambitious rivals* — is real decision-making the Iron Court currently lacks.

**BUILT 2026-09-20, DEPLOYED 2026-09-22, NOT YET SEEN LIVE.** Harness, mutants and the pack
read-back are green; the six old-save and new-campaign checks in the plan's Task 5 Step 5 have
not been run. `IC.AMBITION` and `IC.TUNE.ambition_standing_per_weight` hold the values below.

Three permanent bands (75% / 100% / 125%, rolled
25 / 50 / 25) modify a new derived member-weight term. At Steady, 100 personal standing is one
party weight; saved office/plot weight and derived governor weight keep their existing meanings.
The band is stored in trailing save field 8 and mirrored by a visible character trait.

- Design: `docs/superpowers/specs/2026-09-20-iron-court-ambition-design.md`
- Plan: `docs/superpowers/plans/2026-09-20-iron-court-ambition.md`
- Cost: moderate. Model/save refactor plus three generated trait rows and existing-plate tooltip.

### 2.8 Provoke and Purge (guide §9)

**BUILT 2026-09-13.** Both are plots, so both roll and both cost the courtier his standing. See
§8.1 and §8.2.

### 2.9 A political marriage equivalent (guide §6)

The guide calls this the strongest lever in the system: cheap, permanent while both live, no
downside after the upfront cost, and **gated on the party already being at positive loyalty**.

WH3 has no marriage system, so this needs a Chaos Dwarf reskin — a hostage taken into the Tower,
or a blood-oath sworn on the anvil. The mechanic is what matters: a permanent per-house loyalty
floor tied to two named characters, lost if either dies.

**BUILT 2026-09-13** as the Blood-Oath on the Anvil. See §8.3 — including the one thing the
first pass got wrong about where to put it.

### 2.10 "What a secession would cost me" (guide §10)

Rome 2 answers this with the strategic map's political-affiliation filter. Its exact form is out
of reach and a one-party-at-a-time map highlight is not (see §3), but either way the **question**
is answerable in the panel with no engine call at all, and the model already computes the answer:
`IC.defecting_provinces(faction_key, slug)`.

- Route: a column or a hover on the court list — how many provinces, and which, would go with this
  party if it walked.
- Cost: small. Pure panel.

**BUILT 2026-09-18** as a tooltip on the **mood cell** — the cell that already reads
`SECEDES 3`, which is the one a player hovers to ask what three turns are protecting. It was
already interactive and carried no tooltip, so this needed no new component, no layout change
and no generator run. `ICUI.secession_tip` names the count and the first `ICUI.TIP_PROVINCES`
provinces, then "and N more".

Three things it must do that "a sentence comes back" does not cover, each with its own check
and mutant:

- **The count is the model's.** `IC.defecting_provinces` floors its answer at what the party
  already governs and at what has rotted past `prov_defect_floor`, so a tooltip that recomputes
  it from the share is a second owner of the rule that agrees until it does not.
- **Provinces are named, not keyed.** `provinces_onscreen_<key>`, never
  `region:province_name()`, which CA documents as returning a KEY. Proved by seeding a display
  name that is not the key — printing the key would otherwise be indistinguishable, because the
  panel's `loc()` falls back to the key it was given.
- **The cap trims the END.** `defecting_provinces` returns its answer in the order the land is
  actually taken, so the names that survive must be the first ones. This had no test at all
  until a nine-province fixture was written for it: every existing fixture had fewer provinces
  than the cap, so the trim branch never ran.

The Crown gets a different sentence, because `IC.splinter` moves weight and men and never
touches a province — a province count on the player's own card would be a threat the model does
not make.

### 2.11 Dignitaries and edicts (guide §12)

Rome 2 has an advisor skill (`+2 loyalty for the party the parent general belongs to`) and edicts
that do the same.

**BUILT 2026-09-20, DEPLOYED 2026-09-22, NOT YET SEEN LIVE.** Harness, mutants and the pack
read-back are green; the seven in-campaign checks in the plan's Task 5 Step 3 have not been run.
`IC.MILITARY_DOCTRINE` and `IC.TUNE.loyalty_military_doctrine` hold the key and the +2.

Uses the existing Chaos Dwarf **Military Doctrine**
commandment (`wh3_dlc23_edict_chd_armaments`). Each actively governed province under it gives
+2 loyalty per turn to its governor's party. `region:get_active_edict_key()` is documented and
used by CA's Vampire Coast loyalty script; the term is derived inside the existing shared loyalty
breakdown.

- Design: `docs/superpowers/specs/2026-09-20-iron-court-edict-loyalty-design.md`
- Plan: `docs/superpowers/plans/2026-09-20-iron-court-edict-loyalty.md`
- Cost: small. Lua and harness/mutation coverage only; no DB, ancillary, skill or rite work.

---

## 3. Missing, and out of reach in the form Rome 2 uses

**Rome 2's political-affiliation filter as Rome 2 draws it (guide §10, image 12) — three parties
in three colours at once.** Corrected 2026-09-13: the first pass here said no overlay route
existed at all, which was wrong. `CampaignUI.SetOverlayMode(mode, mask, ...region_keys)` and
`CampaignUI.SetOverlayVisible(bool)` are both documented in
`reference/ca_script_docs_wh3/campaign/campaignui.html`, and the region list is **arbitrary** —
any number of region keys, ours included.

What is fixed is the **mode**: 15 engine ids (0 DIPLOMACY_STATUS through 14
ATTRITION_FOR_SELECTED_CHARACTER), none political, and no table mints a sixteenth. One call
paints one set of regions in one mode, so three parties in three colours simultaneously is what
stays out of reach.

**What that leaves open is worth more than the thing it closes.** Mode 13 is
TUTORIAL_REGION_HIGHLIGHT — a plain "light these regions up" with no data semantics of its own —
so one party's block at a time IS paintable, off `IC.defecting_provinces(faction_key, slug)`,
which the model already computes. That is Rome 2's question answered on the map rather than in a
tooltip, one party per click instead of all three at once.

**Untested, and CA does not use it.** A grep of all 5,778 shipped Lua files finds **zero** calls
to either function — documented but never exercised by CA, which in this codebase has meant dead
before (`random_subpayload` returns false for every shape it documents). Prove it with a
throwaway `SetOverlayMode(13, 0, <a known region key>)` before designing anything on top of it.

§2.10 — the same question answered in the panel — stands either way, and needs no engine call.

**Rome 2's family tree.** The Iron Court's courtiers are the faction's actual lords and heroes,
not a separate dynastic roster, so there is no tree to draw. This is a deliberate difference in
design rather than a gap.

---

## 4. Two things the audit turned up on its own

Neither is a Rome 2 gap; both are worth fixing.

**A dead officer leaves a stale term behind — STILL OPEN, re-confirmed 2026-09-18.** Dated so
the next reader can tell a finding that has been looked at again from one nobody has touched
since it was written. The `ic_dead` listener clears
`court.offices[office_slug]` and the man's governorships, but not `court.terms[office_slug]`.
Nothing reads a term for an empty seat — `IC.term_left` and `IC.expire_terms` both key off
`court.offices` first, and `IC.appoint` overwrites it — so this is save cruft rather than a live
fault. `IC.expire_terms` and `IC.enforce_bars` both clear the term explicitly; this path should too.

---

## 4b. What a second audit turned up, 2026-09-18

A mechanical sweep for things declared and read by nothing — the shape
`IC.TUNE.sufferance_share` had, a knob that did nothing and was invisible because a threshold
that never fires looks exactly like one that is never crossed. Full write-up and the false
positives it produced in `docs/sessions/HANDOFF_20260918_IRON_COURT_WARNINGS_AND_AUDIT.md`.

**Fixed the same day:**

- **`pressed` and `dissolve` never reached the Record.** Neither was in `IC.LOG_KINDS`, and
  `IC.log` drops an unwhitelisted kind at its first line — so both were written by the model,
  eaten by the whitelist, and each had a finished sentence in `ICUI.intrigue_text` that could
  never draw. `pressed` is the one that mattered: it is the moment the strongest bloc stops
  waiting for a reason, the start of the pressure route to secession and the only thing the
  court does with no input from the player at all. The real fix is the **gate** — a check that
  lifts the renderer's `elseif` branches out of the UI source and compares the two sets both
  ways. This had been half-known since the splinter shipped: the `LOG_KINDS` comment named both
  as dead renderers and a check asserted `IC.LOG_KINDS.splinter` "so splinter is not a third",
  which stopped exactly one name from joining two.
- **The split could roll an interest nobody belonged to.** A man joins a party when his
  background maps to it — `house_of_character` keeps him with the Crown while his party is
  unseated and moves him the moment it is seated, which is how a breakaway gets its men without
  anybody re-homing them. The pool was every unseated interest, rolled uniformly, so it could
  seat a party with weight, a name, traits and a card and **nobody in it**, under a card saying
  the men who will not answer to you any more have organised. Invisible from inside
  `IC.splinter`, which never looks at a character. Legends are excluded from the eligibility
  count: `house_of_character` answers the Crown for a legend first and whatever else is true of
  him, so his background can never move him.

**Still open**, in the order worth taking them: the stale term above; **2.7** and **2.11**;
three functions defined and called by nothing (`ICUI.origin_name`, whose own comment says it is
drawn on the office card, so a man's origin never appears there; `ICUI.gov_effect`, superseded
on purpose when the Effect column became province loyalty; `IC.house_in_court`); and, outside
this pack, `cm:force_non_aggression_pact` — **undocumented** and called eight times across the
four Ghorth start scripts in the lords pack.

**Loyalty had six writers.** Corrected and fixed 2026-09-13. The first pass said two and named
the wrong problem: the bribe and the murder each clamped the end they happened to move, so the
ceiling was not actually breached. The real fault was bigger - `IC.appoint` wrote `+8`,
the snub beside it `-6` and `IC.dismiss` `-12`, all three inline, so the three biggest levers a
player has were the only loyalty values `IC.TUNE` did not name and the breakdown could not
explain. All six now go through `IC.move_loyalty`, the numbers are named knobs, and
`import_iron_court.check_loyalty_writers` refuses to pack if a seventh writer appears.

---

## 5. Suggested order — DONE 2026-09-13

All five were built in the order below, each with checks and mutants before the next began.

1. **2.5** generals earn no gravitas — DONE
2. **2.6** battles and deaths move loyalty — DONE
3. **2.1** the loyalty breakdown — DONE
4. **2.3** Secure Loyalty and **2.4** gifts — DONE
5. **2.2** party traits and the leader trait — DONE

### What remains

**Rewritten 2026-09-18, and the rewrite is the point.** This list said five items for five days
while two of them — **2.8** Provoke and Purge and **2.9** the marriage equivalent — were marked
**BUILT 2026-09-13** in their own sections a hundred lines above it, built the same day the list
was written. A list of what to do next that names work already finished is worse than no list.
Both were confirmed against the shipped Lua before this edit, not against the sections claiming
them.

**2.10** is built too, on 2026-09-18. **2.7** ambition and **2.11** Military Doctrine were built
2026-09-20 and deployed 2026-09-22, so nothing implementable is left in §2. What is left is the
live check of those two, listed in each plan's Task 5, and §3's political-affiliation map filter,
which stays out of reach.

### What the build turned up

Four things the harness found that no amount of reading would have:

- **The trait values could not be Rome 2's.** Its numbers are terms in a standing loyalty; these
  are per-turn rates. At Rome 2's magnitudes an officeholder's party lost ground.
- **Two absolute invariants stopped being true** once parties had opinions: "a seated party's
  loyalty goes up" and "an unseated party's goes down". Both were re-expressed as comparisons -
  the same party with the seat and without - which is what they had always been a proxy for.
- **A governorship can be worth more than the governorship term**, because Grasping is an opinion
  about provinces and flips on the same assignment.
- **The court row's last cell had drawn as a button since the panel shipped and done nothing**:
  `ICUI.on_row_action` returned early for every view but govs and intrigue. That inert control is
  where the favours went, so 2.3 and 2.4 needed no new column and no generator change.

---

## 6. The court tab after 2.2 — cards, a plate, and an offline picture

Built 2026-09-13 after §5, from two requests made against screenshots of the shipped panel.

### 6.1 The court is a grid of cards, not a table

2.2 gave every party three traits and a leader. A row has five text cells shared with every
other list view in the panel, and there was nowhere to put a face. So the court view's list
became a grid of cards, and the row pool it used to share is hidden on that tab. It was ten
cards five across and two down until the two-column rebuild in 6.4; it is **six, two across and
three down**, in the right-hand column.

One card carries, in this order down its column: the party's crest and name (two lines, split
on a word by the engine's own `TextDimensionsForText` — a character budget is a guess, and a
guess is what shipped "Shaken: Gemsto…"), its leader's porthole, his name, **his** trait, the
share and loyalty figures with the §2.1 breakdown on them, the party's **own** two traits, its
seat count, and a mood plate that opens the favours — the same control the row's last cell was.

Geometry, all derived rather than typed: `PARTY_W` is `COL_W` less one gap over two columns;
`PARTIES_X` and `PARTIES_Y` are the right column's own origin, so the grid clears the dial
**beside** it rather than above it; `PARTY_H` finishes above the pager, not above the alert bar,
because a court with more than six parties pages. The text column beside the face is derived
from the face's width — typed at 114 it put the longest character name at 185px in the 184 that
was left, and check 20g caught that before anything drew.

Under the dial, in the same column, is **the Crown's box**, and it has two halves. The left one
is what the court is worth to you — the standing heading and the band line; the right one is who
you are — the faction leader's porthole, his name, his party and his trait.
`IC.faction_leader_cqi` reads that off `faction:faction_leader()`, not off the highest bidder in
the court. Stacked, those two used a third of the box and left the rest black.

**The split is sized off the strings, not off the middle**: 372px is the widest `ic_control`
("100% of the court - An Iron Grip on the Court", 359px) plus headroom, and the rest goes right,
where a 183px portrait and a 253px name have to fit beside each other.

**The effects line does not fit in either half.** At 472px it is the longest string the tab
draws, so it takes a full-width row under both of them. That is also the change that made the
two control lines measurable at all: at full width nothing could clip them and nothing measured
them, and narrowed they can — twui text does not wrap, it stops. Check 20g builds both strings
out of `IC.CONTROL_BANDS` and `IC.effect_short` the way the panel does.

Two halves sharing every row is also a new way for the panel to be wrong. Every cell on it used
to be a full-width band at its own y, so two of them could not cross; the Crown's box now gets
the same all-pairs overlap check the party card has had since 2.2.

The box's height is derived from the deepest cell in it and not from the column's, which is a
distinction worth making: the column's foot is set by the last card row in the OTHER column, and
measuring against that left a third of the box black.

The section label `ic_lbl_section` is the one component with two homes. It keeps its full-width
place at the top of the panel for the other four views and the dispatcher moves it to
`COURT_SECTION_XY`, the first line inside the Crown's box, when the court is up. The half of
that worth checking is that it comes back.

### 6.2 A plate behind the dial

`ic_dial_box` — the same tiled body and 9-sliced border every card in the panel wears, sorted
**below** every wedge by a `tier = -1` branch in `_panel_order`, which `ic_crown_box` now shares:
two opaque plates, and a plate declared after its contents is a plate drawn over them.

It must contain the rim, stay inside its column, and stop above the Crown's box; check 16b
holds it to that. Two of those three rules are the INVERSE of what 16b said when the dial was a
band across the top ("the grid starts below the plate", "the plate starts left of the Crown's
block"), which is the failure mode worth naming: a check that is the opposite of the layout
fails forever on correct data until somebody deletes it, and a deleted check is a rule nobody
is enforcing. They were re-aimed, not resynced.

### 6.3 Looking at it without launching the game

`tools/preview_iron_court.py` renders this tab to
`.skilltree_cache/ui_preview/ic_court.png` with the game shut, out of TWUI Studio's vendored
parser and rasteriser and `gen_ic_ui.py`'s own coordinates. It also runs TWUI Studio's
diagnostics over all six `derpy_ic_*.twui.xml` files — an independent reader, which is worth
having because every check in the generator was written by the same hand as the files it checks.

It draws in `_panel_order`'s order, not alphabetically, because that is the order the engine
declares and therefore draws in — alphabetical was harmless until a second opaque plate arrived
and `ic_crown_box` sorted after the lines it frames.

Positions and sizes in the picture are exact. The contents are a demo court, and the glyphs are
PIL's, so it cannot answer "does that label fit" — check 20g owns that, with the engine's own
measurement. What the preview is for is DESIGN review; it is not a second correctness check,
and everything it could assert about the files the generator already asserts.

### 6.4 Two columns, and a backdrop

Requested 2026-09-13 against a mockup, after the stacked version shipped and was looked at.

The panel is 1920 wide and the stacked layout used about a third of it: a dial band across the
top, a strip of loose text beside it, and the cards underneath. Split in two — `COL_W` is
`CONTENT_W` less one gutter over two — the dial gets a column to fill at radius 431 instead of
324, and the cards get one of their own. Everything on the tab derives from `COL_W`; the two
headers the columns carry are **Control of the Court** and **Parties of the Court**, and a
4px rule sits in the gutter between them, touching neither column.

The backdrop is `ui/derpy_ic/panel_bg.png`, built by `tools/make_ic_backdrop.py` out of a WH3
key-art still. Two things about it are not obvious:

- It is dimmed to **42%**, the largest hundredth that clears 4.5:1 against `#FFF8D7` on all 82
  measured cells; undimmed, 57 of them fail. Which cells are measured is derived rather than
  listed — a cell counts unless an opaque plate contains it, and the opaque plates are whatever
  `_panel_order` sorts to tier -1 — because a typed list went stale the moment the columns moved
  the Crown's block onto a plate, and then reported unreadable text that had a box behind it.

  The factor was 45% while only the court tab was measured. **The row pool is the reason it is
  not.** A list row is not a plate: `ROW_LAYERS` is a single `#00000055` wash, so two thirds of
  the furnace comes through under every line of the governors, record, intrigue and offices
  views. That is the thinnest cover on the panel and the only one nobody had ever measured; two
  row cells read 4.3:1 and 4.5:1 at 45%.
- It is in `art_paths()`, which is not decoration. Three things walk that set:
  `deploy_iron_court.py` ships it, `write_plates()` **prunes** anything under `ui/derpy_ic/`
  that is not in it, and check 3 proves every imagepath resolves. Left out, the file would have
  been deleted by the next generator run and never packed.

## 7. Plots can miss, and the panel says what you cannot have

Asked for 2026-09-13, against a screenshot of a party card. Three things, and one question.

### 7.1 The question: no, nothing pops up

There was no dilemma and no event feed, and there still is not. `IC.plot` was **deterministic**:
`IC.can_plot` either refused it up front — with the reason written into the panel as a sentence
— or it landed, always. Both scripts contain zero `show_message_event`, `trigger_dilemma` and
`trigger_incident`, and the mod ships no dilemmas at all. The only record was the line `IC.log`
writes to the RECORD tab.

A dilemma is also the wrong instrument here. A custom dilemma paired with a choice listener is a
**hard CTD that bricks saves** (see the memory note; the match is fatal and an empty handler
still crashes), and `cm:show_message_event` needs a four-table index chain for what is, in this
panel, a line the player is already looking at.

### 7.2 What replaced it: the hero-action shape

Not a dilemma — the shape CA uses for an agent action, which is three things and all three matter:

1. **You are shown the odds before you commit.** `IC.plot_chance` is a **pure** function —
   no roll, no state, no side effect — so the picker draws the same number `IC.plot` is about to
   roll against. Two functions, one to show and one to resolve, is exactly how a UI ends up
   promising 70% and rolling 55. The picker's button reads `CHOOSE 72%`.
2. **The odds are your man against theirs.** Standing is what a courtier has earned, so the
   difference between plotter and victim is the whole skill term, on top of a base per move:
   whispering is 75 and arranging an accident in the Tower is 40. Integer arithmetic
   throughout — WH3's Lua is float32 and a `.5` boundary on a number the player is *shown* falls
   the wrong way often enough to matter. Clamped to 5..95: never a certainty, never a dead
   button wearing a percentage.
3. **Losing costs.** The standing is charged before the roll, as it always was, and the house
   you moved against works out who tried — `plot_fail_loyalty` off their loyalty. Without that,
   a 75% rumour is a button you hold down until it lands.

A failed roll returns **`true`**, not `false`. A refusal means the move never happened and the
picker stays open on it; a miss happened and did not work, so the picker closes and the alert
line says so. The second return carries `"landed"` or `"failed"` in the slot a refusal uses for
its reason — which the caller only reads when the first is false, so nothing existing changed.

`plot_failed` is its own log kind rather than a flag on the four moves: the record renders one
sentence per kind, and "X bribes Y" with "(failed)" bolted on is not the sentence that happened.

### 7.3 Red means you cannot have it

`[[col:red]]…[[/col]]` is markup the engine reads out of the string, so it needs no component
and no state. **`red` is the name** — 1,649 uses across CA's own loc, out of 43 distinct names
— and an unknown name is dropped *silently*, leaving ordinary ink and no error, which is why it
is written once in `ICUI.red` and never spelled out again. It **wraps** rather than rebuilds, so
a string already carrying an `[[img:]]` icon keeps it.

Three places, because the player meets the refusal at three moments:

| Where | Red when |
|---|---|
| the picker's action cell | `ICUI.pick_rows[n] == nil` — the same value the click reads, so the colour cannot disagree with the button |
| the office card's bars | nobody you have can take the seat **and** it cannot be bought into, asked through `IC.can_appoint` and `IC.can_hire` |
| the plot's price | no courtier has the standing for it |

The harness reads cells through a new `plain()` that strips the markup, so twelve existing
assertions still ask what a cell *says*; `is_red()` asks the other half. Both, because `plain()`
alone would pass just as happily if the colouring silently stopped working, and colouring
*everything* red would satisfy any one-sided assertion.

### 7.4 A silhouette for a party with nobody at its head

The card fell back to the party's **crest**. That is the *row's* rule and right there — a row has
one picture and a flag beats a blank. A card is not a row: it already draws that crest in its
top-left corner beside the name, so the fallback put the same picture on the card twice and
called one of them a face. The Crown's portrait was worse — it fell back to nothing, and
`set_face` hides the cell, leaving a bare coloured rectangle that reads as art that failed to load.

CA ships nothing usable: `0_placeholder_mission_issuer.png` is a hot-pink "missing image"
developer icon and `0_placeholder_agent.png` is 29x29. So it is drawn — head, neck and shoulders
at `PLATE_W x PLATE_H`, which is already the porthole's own size and aspect, supersampled 3x3
because the cell draws at 98x54 and a stair-stepped circle reads as a cog. **Transparent around
the figure**, not a plate of its own: the house plate behind it carries the party's colour, and
an opaque ground would make every leaderless party the same grey box.

It lives in `build_plates()`, which is the point — one dict is walked by the drift check, the
packing gate and the deploy list, so it is covered by all three and `write_plates()` will not
prune it.

## 8. Five more moves, off the guide's own list

Asked for 2026-09-13. The intrigue tab went from four moves to nine, and gained a second
**shape** of move, which is the part that mattered.

### 8.1 Provoke (guide §9)

The thing nothing else in the system does: it takes the **timing** away from them. A house that
was going to break with you in eleven turns breaks in three, while your armies are home and
theirs are not. -25 loyalty and a three-turn clock.

**It never lengthens a clock.** A house already two turns from the door is not talked back to
three by being insulted — that would make provoking a house the cheapest way to *save* yourself
from it, which is the opposite of what the move is for.

**And it burns any oath you have with them.** You cannot swear on the anvil with a house and then
provoke it; the record says which of the two ways an oath ended.

### 8.2 Purge the House (guide §9)

`IC.remove_house` already existed, so the move is one call — the house leaves the court and its
seats and provinces go with it. What makes it a decision rather than a button is the second half:
**every other house watched you do it**, -15 loyalty each. Your own party is not a witness,
because it is you.

At 400 standing it is the most expensive thing a courtier can do, and at a 45% base it is the
least likely to work. **A purge that misses is the worst outcome in the system** — the ordinary
`plot_fail_loyalty` *plus* `plot_purge_backfire`, because they know you tried to end them.

### 8.3 The Blood-Oath on the Anvil (guide §6)

Rome 2's political marriage, which the guide calls possibly the best tool in the system: cheap,
permanent while both live, no downside after the cost — and **gated on the party already being at
positive loyalty**. "So do not antagonise a party you intend to marry into." That gate is the
whole of its design and it is `plot_oath_min_loyalty`, above `loyalty_start` rather than above
zero, because this system's loyalty runs 0-100 with 55 as the starting point.

**It is a term, not a floor.** §2.9 proposed a bond record and a permanent loyalty floor. A floor
would be a second mechanism sitting beside a breakdown that already explains every other point of
drift; a **term** is +4 every turn while it stands, saturating against `move_loyalty`'s own clamp
at 100 — permanent in effect, visible in the tooltip, and arithmetic the player can already read.

**It lives on the house record**, two fields on the end of its line. That is the migration idiom
this save format already documents four times over: `unpack` takes `>= 3` fields, so a save
written before the anvil could bind two names has eleven and nobody in it is sworn. It needed no
new top-level section.

**One per house**, or the term would stack. **Broken when either man dies** — the guide's rule —
in `ic_dead`, which is the only listener that sees every death there is. The sweep looks at
*every* house and not the dead man's own, because half of every oath is one of **your** men.

### 8.4 The civil missions (guide §7), and the shape they brought

The guide's verdict on Rome 2's 24 intrigues is that about half have no use case and the other
half are strong — and the strong half is the **mission** intrigues, which **pay twice**: the
courtier gains gravitas *and* something happens in the world.

| | What it does |
|---|---|
| **Embezzle from the Vaults** | +2500 gold, and -6 loyalty with every house but your own |
| **A Feast of Ash** | +140 influence to the man who holds it, -3 loyalty with everybody else |

The Feast is Organize Games, whose tooltip in the guide reads "+8 gravitas for this character,
-2 loyalty for all other parties for 5 turns". It is the reason a courtier with no seat and no
province still has something to do.

**These are the first moves in the system that aim at nobody**, and that is a second shape rather
than two more rows. `IC.may_target`, `IC.can_plot` and `IC.plot_chance` all took a victim and all
three now have a nil path — `may_target` returns early rather than asking a question about nil,
because `IC.house_of_character(nil)` answers nil, reads as "no house", and would refuse an errand
with a sentence about parties.

**The odds of an unaimed move are its base and nothing else.** The edge term is the actor measured
against the victim; with no victim, `theirs` would be 0 and every errand would sit on the 95%
ceiling the moment a courtier had 900 standing — odds that look measured and are not.

**And a general cannot be sent.** The guide's own gate, off that same tooltip: "This character
commands a force and cannot be sent on civil missions." `IC.trickle_for` already asks the same
question about the same men, so this is that test in a second place rather than a second rule.
The intrigue tab's red therefore needs **two** purses — the richest courtier, and the richest
courtier *not commanding an army* — because a court whose only rich man is in the field can pay
for a knife and not for an errand, and one number could not say both.

### 8.5 Two refusal codes that were already wrong

Found while adding five more:

- **`sworn`** already meant Secure Loyalty — "they are already sworn for another N turns". The
  oath's own "you already have one" would have drawn that sentence with N=0. Its code is `oathed`.
- **`your own house`** has two branches in `ICUI.reason_text` and **the second is dead.** The
  first is the favour's sentence and shadows it, so moving against your own party answered a knife
  with a line about gold: "you do not buy the goodwill of your own party." `IC.may_target` returns
  `own party` now, which is what the second branch was always for.

### 8.6 `cm:treasury_mod` can only give

CA's own entry: *"This value must be positive."* So the embezzlement can pay the treasury and
nothing in this system can ever take gold away through that call. Recorded at the call site and
asserted in the harness, because the parameter is named `amount` and the constraint is nowhere in
the signature.
