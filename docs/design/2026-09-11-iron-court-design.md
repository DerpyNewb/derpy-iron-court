# The Iron Court - design

Approved in conversation 2026-09-11. A new mod, not an extension of any existing pack:
`derpy_iron_court.pack`. A Rome 2-style political system for the Chaos Dwarfs - houses as
parties, offices held by characters, Overseers as governors, and intrigue that runs whether
or not the player touches it.

Implementation plan: not yet written.

UI reference: `docs/mockups/politics_panel.html` / `.png` - four views, approved 2026-09-11,
and the layout the panel is built to.

---

## 1. The gap this fills

The mod set manages finance (the Zharr Exchange), items (430 house ancillaries), progression
(skill trees, victory routes), armies (units, naval hordes), and institutions (the Great
Guilds). Territory-and-politics is covered only by the Tower of Zharr, which is an
*external* contest: which house holds which seat in a shared tower.

Nothing models the politics of the faction you actually run. Ten houses exist as factions
with art, units, ancillaries and lords, and the only thing that happens when you absorb one
is that its regions change colour.

This mod makes absorbing a house the *beginning* of a relationship rather than the end of
one.

**It is not the Great Guilds.** Guilds are professional and institutional; they sell
services for standing earned by play. Houses are dynastic and political; they want office,
they resent each other, and they can leave. If a player reads this panel and thinks "guilds
again", the mod has failed.

---

## 2. Decisions taken 2026-09-11

| Question | Answer | Why |
|---|---|---|
| Political actors | **The ten modded houses** | They already exist with art, units, ancillaries and lords. Inventing court cliques would overlap the Guilds. |
| Stakes | **Secession / civil war** | Rome 2's politics mattered because it could bite. Unrest-only is ignorable. |
| Venue | **Your own court**; houses join by conquest | Starts small and grows with the campaign. An empire-wide council gives the player almost no control and puts all the work in the AI half. |
| Officeholder | **A character**, whose house gains by it | Rome 2's exact shape. Makes lords into careers rather than stat blocks. |
| Governors | **A new Overseer agent**, cloned from Kislev's Ataman | Engine-native governor, `province_governors_tables`. Chosen over reusing existing lords with eyes open - see the risk in section 9. |
| Intrigue | **Two-way, plus AI-vs-AI, plus crises** | The court must have a pulse when the player is not looking at it. |
| AI scope | **Every Chaos Dwarf faction runs a court** | Requested explicitly 2026-09-11. Same model, no UI. |
| Currency | **Court Influence**, in Lua save state | Chosen over CA's `wh3_dlc23_chd_conclave_influence` so politics never competes with Tower of Zharr seat claims for the same pool. |
| Where state lives | **Lua save state** | Same reasoning as the Guilds: no `campaign_group_pooled_resources` row per group to miss, and modded factions are covered free. |
| Packaging | **Standalone pack**, two phases after a spike phase | Keeps a politics bug out of the 14.8 MB published lords pack. |

---

## 3. Verified this session, and where

Everything below was read out of CA's own docs in
`Modding Files/reference/ca_script_docs_wh3/` or out of the vanilla table cache, not recalled.

| Claim | Source |
|---|---|
| `province_governors_tables` exists, **one vanilla row** (`wh3_main_ksl_ataman`) | `.skilltree_cache/province_governors.json` |
| `character:is_governor()` | `scripting_doc.html`, CHARACTER_SCRIPT_INTERFACE |
| `character:loyalty()`, `personal_loyalty_factor` | `scripting_doc.html` |
| `faction:character_list()`, `character:is_dead()`, `is_wounded()`, `has_trait()`, `rank()`, `command_queue_index()` | `scripting_doc.html` |
| `faction:provinces()`, `province:regions()`, `province:capital_region()`, `province:faction_province_for_faction()` | `scripting_doc.html` |
| `cm:apply_effect_bundle_to_faction_province(bundle, region, turns)` - applies to **the portion of the province owned by the owner of that region**; `-1` = indefinite | `campaign/episodic_scripting.html` |
| `cm:create_new_custom_effect_bundle(base)` + `apply_custom_effect_bundle_to_faction_province` | same |
| `cm:transfer_region_to_faction(region_key, faction_key)` - immediate | same |
| `cm:force_rebellion_with_faction(region, faction_key, max_units, full_strength, [suppress_po])` - returns the force | same |
| `cm:force_declare_war(attacker, target, invite_attacker_allies, invite_defender_allies)` | same |
| `cm:force_add_trait` / `force_remove_trait`, `cm:kill_character` | same |
| `cm:show_message_event(faction, title_loc, primary_loc, secondary_loc, persistent, index)` | same |
| `cm:set_saved_value` / `get_saved_value` / `random_number` | `campaign/campaign_manager.html`; already used 44 / 22 / 45 times in shipped pack Lua |
| Event names: `FactionJoinsConfederation`, `FactionBecomesVassal`, `FactionTurnStart`, `CharacterTurnStart`, `CharacterConvalescedOrKilled`, `CharacterRankUp`, `CharacterCapturedSettlement`, `CharacterRazedSettlement`, `RegionFactionChangeEvent`, `GarrisonOccupiedEvent`, `RegionRebels` | `scripting_doc.html` |
| Ten house factions | `docs/MOD_STRUCTURE.md`, `factions_tables/!!_cr_oldworld_new_factions` |
| Tower of Zharr seats cost 300 Conclave Influence | `docs/TOWER_OF_ZHARR_CUSTOM_SEATS.md` line 31 |
| GUID prefixes in use: `DE14`-`DE18` (Exchange, rites), `GG21` (Guilds); `DE15` retired | `docs/CUSTOM_UI.md`, `tools/gen_guilds_ui.py` |

**There is no `CharacterKilled` event.** It is `CharacterConvalescedOrKilled`, and it fires
for wounding as well as death. Every handler on it must test `is_dead()` or an office empties
each time its holder takes a scratch.

---

## 4. The court

### 4.1 Who is in it

The player's own house, always. Others join on `FactionJoinsConfederation` and
`FactionBecomesVassal`. The Tower of Zharr annex seats already fire confederation reliably
(measured 2026-08-18, two `FactionJoinsConfederation` events).

Cast: the ten modded houses plus CA's four Chaos Dwarf factions.

At campaign start the player gets their own house plus **two client houses seeded by
script**, so the panel is populated from turn 1 instead of empty for thirty turns.

**`force_confederation` is asynchronous** - an absorbed house's characters appear about ten
seconds later. Stamping incoming characters with their house trait therefore cannot happen
inside the confederation handler; it polls until they exist.

### 4.2 The three numbers

| Number | Whose | Range | Moves |
|---|---|---|---|
| **Standing** | each house in court | a share of 100% | Up with offices, governorships and its own victories; every other house's share falls when one rises |
| **Loyalty** | each house in court | 0-100 | Down when starved of office, up when appointed, bribed or honoured |
| **Court Influence** | the faction | a stockpile | Earned per turn from filled offices and court stability; spent on appointments, governor assignments and intrigue |

**Standing is a share, not a stockpile.** Promoting one house demotes every other by
arithmetic rather than by a decay rule, and the panel gets one honest picture: a bar of
coloured segments that always sums to the whole court.

Court Influence income: base 20/turn, plus per filled office, plus 30 from the Master of the
Black Ledger, minus 15/turn while that office is vacant.

### 4.3 The two failure edges

- The player's own house **below 20% standing**: they rule on sufferance. Warning, then
  crises.
- A rival at **standing >= 25% and loyalty <= 20**: a five-turn secession countdown with a
  warning each turn. See section 8.

### 4.4 Characters carry a house as a trait

Legendary lords are their own house. Generic lords and heroes get a house stamped at
recruitment, weighted by current standing, via `cm:force_add_trait`.

A trait rather than save state because it survives on its own, shows on the character panel
where a player will look for it, and can carry effects. Save state remains the source of
truth; the trait is derived, and a reconcile pass at first tick re-adds any that went missing.

---

## 5. Offices

Six, each wired to a Chaos Dwarf system that already exists. No invented economies.

| Office | Gives | Vacant costs | House affinity |
|---|---|---|---|
| Grand Overseer of the Forge | +15% Armaments, Hell-Forge cost -10% | -5% Armaments | Snakebeard's Artificers |
| Keeper of the Chains | -15% Workload | +5% Workload | House of Khorakk |
| High Priest of Hashut | +4 public order, +1 Conclave Influence | -3 public order | Fists of Hashut |
| Master of the Black Ledger | +12% income, +30 Court Influence/turn | -15 Court Influence/turn | Warfleet of Uzkulak |
| Warden of the Deeps | -10% army upkeep, +10% replenishment | -3 public order | Horns of Hashut |
| Lord of the Slave Pits | +25% post-battle Labour | -10% post-battle Labour | House of Baal |

**Chaos Dwarfs have no "slaves" pooled resource.** The vanilla set is `labour`,
`armaments`, `raw_materials`, `workload`, `efficiency` and `conclave_influence` (read from
`pooled_resources.json`, 2026-09-11). Slaves are flavour; every slave-shaped mechanic here is
Labour or Workload underneath.

**Affinity is the friction.** Appoint the affine house's man and that house gets double
standing and a loyalty bonus. Appoint an outsider and the affine house *loses* loyalty. A
court where every office goes to the ruling house is a court that hates its ruler - the Rome
2 squeeze, delivered by one column in a table rather than a rule engine.

**Appointment.** Any lord or hero of the faction at rank 3 or above is a candidate. Costs 250
Court Influence. Once changed, the office locks for 5 turns.

The lock is not decoration: without it, appointment churn farms standing, and that is the
first degeneracy a player will find.

**The title is a trait.** `cm:force_add_trait` puts the office on the holder, carrying the
personal effect, so the office reads on his own character panel and the game state itself
records who holds what.

**Losing a holder.** `CharacterConvalescedOrKilled` with `is_dead()` true empties the office
and costs his house standing. Wounded, he keeps it.

---

## 6. Governors

### 6.1 Seats are derived, never stored

`faction:provinces()` is the seat list. The panel reads it fresh on every open. Capture a
region in a new province and a row appears; lose the last region there and the row is gone.
There is no seat table, nothing to keep in sync, and no way for the list to drift from the
map.

**Partial provinces work**, which Rome 2 could not do.
`cm:apply_effect_bundle_to_faction_province` applies to "the portion of the province owned by
the owner of the specified region", so one region is enough to seat a governor and the bundle
only touches the player's share.

**The only stored thing is the assignment**: province key -> Overseer CQI. At each
`FactionTurnStart` that list is reconciled against reality and an assignment pruned when the
province is no longer held, the Overseer is dead, or he has walked out. One code path, once a
turn, covers capture, loss, razing, death and desertion alike.

No `RegionFactionChangeEvent` hook in phase 1 - turn start is soon enough, and it is one path
instead of five.

### 6.2 What a governor gives

| Source | Effect |
|---|---|
| Base | +2 public order, +8 growth |
| Per rank | +1 order and +1.5% provincial output per rank, via `create_new_custom_effect_bundle` so it scales at runtime |
| His house | Artificers +Armaments; Khorakk +order through fear; Baal -corruption; Uzkulak +income |

Recomputed each turn start - removed and re-applied - so a rank-up or a house change needs no
special case. Five provinces is ten calls a turn.

### 6.3 He must be inside it

That is the cost, and the reason governorship is a decision rather than free buffs: an
Overseer governing is an agent doing nothing else. March him out and the province gets
nothing until he returns. No penalty, just the absence.

His house gains standing for every turn he serves.

---

## 7. Intrigue

### 7.1 No dilemmas, at all

A `DilemmaChoiceMadeEvent` listener that matches a custom dilemma is a hard CTD here -
measured seven times, byte-identical, `0xc0000005` at `Warhammer3.exe+0x236C1CF`, with an
empty handler body. It bricks saves, because a fired dilemma cannot be dismissed without
answering it.

Every ask in this system uses the proven shape instead: `cm:show_message_event` raises it in
the feed, the deadline goes in `cm:set_saved_value`, and the answer is a button on the
Intrigue tab. Inaction reads as refusal.

`show_message_event`'s last argument indexes `event_feed_message_events`; index 0 draws
nothing, so the mod ships its own rows.

**No loc calls from turn handlers** - that is a turn-1 CTD that pcall does not catch. The
feed stores keys and numbers; the panel resolves display names at draw time.

### 7.2 The player's four actions

| Action | Cost | Effect | Risk |
|---|---|---|---|
| Buy their silence | 120 | +12 loyalty | none, but they remember needing to be paid |
| Whisper against them | 200 | -4% standing, moved to a named house | traceable: caught is -9 loyalty and a trust penalty with every house |
| Hold their kin hostage | 260 | loyalty frozen 10 turns | on lapse it falls twice as far |
| Purge the house | 400 | their officeholder dies, standing to the player | every *other* house loses 8 loyalty |

Purge deliberately hurts the room, not just the target. Without that, purging dominates and
the system collapses into a kill list.

### 7.3 The houses act back

Once per `FactionTurnStart`. Each house rolls against its grievance (`100 - loyalty`)
weighted by its standing: an angry weak house grumbles, an angry strong house moves.

Outcomes: bribe one of the player's officeholders away; demand an office, raising a crisis;
withhold their contribution for a few turns; or conspire, advancing the secession clock.

### 7.4 House against house

A house's target is not always the player. It is often whoever holds the office it has
affinity for, or whoever outranks it.

- **Denounce** moves standing between two houses.
- **Sabotage** suppresses a rival's office effect for a few turns.
- **Feud** drops both houses' loyalty and raises an arbitration crisis, where picking a side
  is the point.

This runs whether or not the player opens the panel. It is what gives the court a pulse.

### 7.5 Crises

Raised with `cm:show_message_event`, carried on the Intrigue tab with a turn counter, and
answered by panel buttons. Unanswered at the deadline, the refusal branch fires at turn start.

---

## 8. Secession

Trigger: the countdown starts on the first `FactionTurnStart` at which a house holds
**standing >= 25% and loyalty <= 20** together, and runs five turns with a warning each turn.
If either condition lapses before it expires the countdown is **cancelled, not paused** - a
house talked back from the brink starts again from five if it returns.

At zero:

1. The regions that house brought into the court - **recorded when it joined** - are returned
   with `cm:transfer_region_to_faction`.
2. `cm:force_rebellion_with_faction` spawns its army in one of them.
3. `cm:force_declare_war` sets the war.

**The open question**, and a phase-0 blocker: whether transferring a region actually revives a
faction that was confederated away. Every other call on this path is documented; this one is
an inference. It is load-bearing for the AI half as well as the player's, so it is proven
before anything is built on it.

---

## 9. AI courts

**One model, two fidelities.** Standing, loyalty, offices and governors run for *every*
Chaos Dwarf faction. It is a table of numbers keyed by faction; the arithmetic does not care
who reads it. Player-only: the panel, the crisis cards, the character traits.

**AI decisions are a policy, not an interface.** Fill the most valuable vacant office with
the highest-standing loyal house. Bribe a house about to secede if it can afford it. Favour
its own house too hard and earn the same resentment the player would.

### 9.1 What the player observes

1. **News in the court feed** - "House of Baal has broken with the Tower of Uzkul". Filtered
   to factions met, and to events that matter.
2. **A real war on the map.** A house seceding from an AI faction takes its regions, spawns
   an army and declares war.
3. **Inherited courts.** Confederate or conquer an AI Chaos Dwarf faction and its court comes
   with it. Houses it starved arrive resentful; houses it favoured arrive loyal.
4. **Weakened rivals** - a faction mid-secession is one to hit while it is split.

### 9.2 Cost control

Fourteen Chaos Dwarf factions holding four or five houses each is about sixty house records,
trivial to iterate. The cap that matters is on *actions*: at most **three** AI political
events resolve worldwide per turn, chosen by weight.

The pattern is `zzz_derpy_toz_ai_seats.lua`'s - a per-faction turn hook with
`CLAIMS_PER_TURN` / `PROBES_PER_TURN` budget caps, `cm:random_number` rolls, pcall guards and
prefixed logging. The Zharr Exchange already runs per-faction AI books every turn, so the
per-turn budget precedent exists and works.

---

## 10. The panel

Built to `docs/mockups/politics_panel.png`. Four views: Court, Offices, Governors, Intrigue.

### 10.1 Three files, created at runtime, overriding nothing

| File | Created into | Instances |
|---|---|---|
| `derpy_ic_panel` | the UI root | one |
| `derpy_ic_row` | the panel's rows holder | one per house, province or feed line |
| `derpy_ic_button` | beside CA's rites button | one, the HUD opener |

**One row file for all four views.** Each view names its own layout table; the layout pass
places what that table names and hides everything it does not. A house row and a governor row
are the same component with different columns showing.

Every component in the XML must be named by *some* layout table, or it can never draw at all.

### 10.2 GUID prefix `IC30`

Assigned from a counter by the generator. The selftest asserts uniqueness across all three
files and that each GUID appears in both the `<components>` and `<hierarchy>` sections. A
collision or a half-declared node is a silent non-draw.

`DE15` is retired and must never be reused.

### 10.3 Layout notes

- **The standing bar is six components resized at runtime**, not text. Colour on the
  component, so the thing the eye reads first does not depend on `[[col:]]` markup. Status
  words do use markup, where a typo silently drops the colour and costs nothing.
- **Portraits are free** - office slots show characters that already have art sets. This mod
  mints no `campaign_character_art_sets` id, so `portrait_settings` work does not arise.
- **The opener button has neighbours.** The Exchange already places a button beside
  `button_rituals` and the Guilds adds another. This one places relative to what is actually
  there at creation time. `MoveTo` positions it; `dockpoint` is ignored on a runtime
  component and a layout group beats `MoveTo` outright.
- **Title "THE IRON COURT" is 14 characters**, under the roughly 19 where a header plate
  clips silently.
- Interactive flag follows visibility, or a dead zone is left on the map after close.
- Every interactive component gets a `soundcategory`.
- Tooltips only reach interactive components.
- Never cache a `UIComponent` handle: a destroyed one still passes `is_uicomponent()`.

---

## 11. Data

| Rows | What |
|---|---|
| **23** `effect_bundles` | 6 office, 6 vacancy, 1 governor base, 10 house-governor flavour - 25 effect junctions and 62 loc rows. Built and passing as of 2026-09-11 (`tools/gen_iron_court.py`). There are no per-rank bundles: the governor scales off the base with `create_new_custom_effect_bundle`. |
| 16 traits | 10 house allegiance, 6 office titles |
| 1 agent subtype | the Overseer, cloned from `wh3_main_ksl_ataman`, plus its `province_governors` row |
| a few `event_feed_message_events` | so `show_message_event` has a real index |

An effect bundle's description must **not** carry a value placeholder, while an effect
description must. `is_global_effect = false` hides a live bundle from Faction Effects.

---

## 12. Tooling

Mirrors the Guilds and Exchange:

| Tool | Job |
|---|---|
| `tools/gen_iron_court.py` | the TSVs, the loc and the MCT settings file |
| `tools/gen_ic_ui.py` | the three `.twui.xml` |
| `tools/check_ic_ui.py` | the sixteen build-time checks already written down in `CUSTOM_UI.md` |
| `tools/import_iron_court.py` | packs it; refuses on a TSV-versus-`build()` row mismatch |

Each carries `--check` and `--selftest`. `tools/check_lua_undeclared.py` gates packing, as it
does for the ancillaries - an undeclared Lua global is nil, not an error, so `luac -p` and
`check_lua_api.py` both pass over it.

---

## 13. Phasing

**Phase 0 - the spikes.** Two things could reshape the design, so they run before anything is
built on them:

1. **The Ataman clone keeps its skill tree and its actions fire.** This workspace has twice
   had cloned hero subtypes come back with `SkillList 0` and silently dead agent actions.
2. **A region transfer revives a confederated-away faction.** Load-bearing for both the
   player's secession and every AI court's.

Plus a measurement: the AI pass at sixty house records with a three-action cap costs nothing
per turn.

**Phase 1 - the court.** The model for all factions, offices, governors, the panel, MCT
settings. Deterministic, and playable on its own.

**Phase 2 - the politics.** Intrigue, AI courts, inherited court state, crises, secession.

---

## 14. What this does not do

- **AI courts get no UI.** The player never opens another faction's court, and building one
  would be work nobody can see.
- **No dilemmas.** Section 7.1.
- **No new pooled resource.** Court Influence lives in save state; Conclave Influence is left
  to the Tower of Zharr.
- **Not culture-agnostic.** Unlike the Great Guilds, this is Chaos Dwarf only. The houses are
  the design; there is no generic fallback worth shipping.
