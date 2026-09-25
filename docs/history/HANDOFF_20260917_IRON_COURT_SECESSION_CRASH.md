# Iron Court — the secession crash, and what five dumps taught

2026-09-17. The Iron Court's secession was made to actually bite: a party that
hits zero loyalty leaves, takes provinces, puts armies on the map and goes to
war. Getting there cost **five identical CTDs**, four of which were "fixed" by
changes that were each a real defect and none of which were the crash.

This is the record of what was measured, what was inferred wrongly, and the
three offline instruments that now make each class of fault impossible to ship
again.

---

## 1. The crash

```
0xc0000005   Warhammer3.exe+0x268CE1F   reading 0xa0  /  0xffffffffffffffff
```

**Identical across all five dumps.** Access violation, null object dereferenced
at a member offset; the two read addresses are "an object that is gone" and "a
lookup answering not-found and being used anyway".

### 1a. Minidumps are NOT in the game folder

```
C:\Users\<user>\AppData\Roaming\The Creative Assembly\Warhammer3\crash_report\
    D2026-09-17_T21-31-31.mdmp
    D2026-09-17_T21-31-31.stack.txt      <- symbol-stripped, useless
```

A recursive search of `F:\SteamLibrary\...\Total War WARHAMMER III` finds
nothing and reports "no dumps", which is what happened here for three rounds.
`tools/read_minidump.py` parses the `.mdmp`; the `.stack.txt` beside it is
stripped and says nothing.

**A repeated fault at the SAME address across builds is the single most
valuable signal available.** It says the thing you just changed was not the
cause — four times over, before that was believed.

### 1b. The actual cause: everything in one frame

Every call the secession made **returned**. The trace walked all the way
through — three armies, three deaths, eight provinces, a war, the summary line
— and the game died **1.0-1.5 seconds later**, inside the UI and turn
processing that followed.

All of it ran inside a single `FactionTurnStart` listener, in one frame:

- wake a dormant faction
- place three armies
- kill three of the player's generals
- move twenty-odd regions between factions
- declare a war

The fix was the **shape**, not the content: every army, every death, every
province and the war now gets its own frame through `cm:callback`, one step per
frame (`IC.TUNE.secede_step = 0.1`). CA's own scripts hand work to `cm:callback`
for exactly this reason.

> **Rule.** A campaign script may not perform a large batch of world mutation
> inside a turn-start listener. Spread it over frames. The symptom is not a Lua
> error and not a failed call — every call succeeds and the engine dies about a
> second later.

---

## 2. The four wrong fixes (each a real defect)

Each of these was found, fixed, verified offline and shipped — and the address
did not move. They are recorded because they are all genuine, and because the
pattern of "plausible, verified, and not the bug" is the expensive part.

### 2a. `is_rebel` factions do not exist on the campaign map

`cm:get_faction("wh3_dlc23_chd_chaos_dwarfs_rebels")` returns **false** in a
live campaign. Every `is_rebel` faction does — the engine instantiates them per
rebellion. A region transferred to one goes nowhere and an army created for one
is never made, both silently.

Four dormant CHD factions ARE on the list and work:
`wh3_dlc23_chd_chaos_dwarfs_qb1/qb2/qb3`, `wh3_dlc25_chd_chaos_dwarfs_invasion`.

Also: `cm:force_rebellion_in_region` has **no faction argument** — the engine
picks from the REGION, which is why a Chaos Dwarf secession at Nagashizzar
raised skaven. It can never produce Chaos Dwarf rebels.

### 2b. "Permitted" answered a different question than the one being asked

`faction_agent_permitted_subtypes` lists `wh3_dlc23_chd_infernal_castellan` for
all four pool factions — **as an `engineer`**. Each pool faction may field 15
subtypes and exactly **7** carry `agent = "general"`. The Castellan is a hero,
and it had been the fallback handed to `create_force_with_general` every time.

This is the CLAUDE.md rule — *read the doc ENTRY, not the fact that a row
exists* — missed anyway. "Permitted" was true and meant something else.

The 7 permitted generals, intersected across all four pool factions:

```
wh3_dlc23_chd_lord_convoy_overseer          wh3_dlc23_chd_sorcerer_prophet_death
wh3_dlc23_chd_overseer                      wh3_dlc23_chd_sorcerer_prophet_fire
wh3_dlc23_chd_overseer_hobgoblin_spawned_army  wh3_dlc23_chd_sorcerer_prophet_hashut
                                            wh3_dlc23_chd_sorcerer_prophet_metal
```

`create_force_with_general` does **not** refuse a subtype the faction cannot
field. It takes it.

### 2c. `is_unique()` is false for modded legendary lords

```
IC.is_unique(<derpy_bzaark, live campaign>)  ->  false
```

It is a `character_details` flag **CA's startpos characters carry**. A
legendary lord a mod brings into the world does not necessarily have it. Every
rule leaning on it — the legend seating, the murder guard, the defection bar —
was leaning on nothing for precisely the lords the pack adds.

**Recognise a legend by SUBTYPE.** Read from `agent_subtypes`:

- vanilla CHD legends = `auto_generate = false` **AND** `recruitable = true`
  (both halves needed: `overseer_hobgoblin_spawned_army` is `auto_generate =
  false` too and is a script-spawned army lord, not a legend)
- the pack's own = its `agent_subtypes` table, read straight out of the pack
  with `tools/read_pack_index.py` (mod packs are uncompressed)

### 2d. `make_faction_leader` on every army

The raw `cm.game_interface:create_force_with_general` signature puts an `id`
between `other_name` and `make_faction_leader`:

```
faction, units, region, x, y, character_type, character_subtype,
forename, clanname, surname, other_name, id,
make_faction_leader, force_diplomatic_discovery, no_background_trait
```

It was hardcoded `true`. A three-army secession made three different characters
the faction leader of the same faction inside one tick, each deposing the last.
Now only the army that **wakes** a dormant faction crowns its general — false
on a faction with nobody on the throne has a leader *invented* for it, which is
the orc shaman that turned up at the head of a Chaos Dwarf rebellion.

---

## 3. Things that were suspected and are NOT true

Recorded so nobody re-derives them:

- **`get_forename()` does return a `names_name_` key.** CA's own
  `wh_pro01_grombrindal.lua:143` compares it to `"names_name_2147358917"`.
  Passing it back into a spawn is fine.
- **`cm:kill_character` accepts a bare numeric cqi.** Documented: *"Alternatively,
  a number may be supplied, which specifies a character cqi."*
- **The event card was not the cause.** `secede_done`'s rows in all four
  event-chain tables are structurally identical to `secede_warn` and
  `office_lost`, and `office_lost` draws 1.6s earlier in every crashing run
  without harm.
- **`destroy_force` was not the cause** (though it is now `false`: the
  rebellion's army is the one spawned separately, and deleting the player's was
  a flourish). `false` produces CA's `appoint_new_general` "Duty Calls" panel,
  which is correct behaviour.

---

## 4. The confounded variable that cost the most time

Every log contains two secessions:

```
tower  secedes from wh3_dlc23_chd_legion_of_azgorh   1 army, 1 province   -> SURVIVED
legion secedes from wh3_dlc23_chd_conclave           3 armies, 8 provinces -> CRASHED
```

These differ in **two** ways at once — the amount of work, and **AI faction vs
the player's faction**. Four rounds of inference treated it as one. Nothing in
five logs separates them.

> **Rule.** When the safe case and the failing case differ in more than one
> dimension, say so out loud before reasoning from it.

---

## 5. What the log has to carry

The secession wrote **one line, at the very end**. For three crashes that line
recorded what the code *intended* and nothing about how far it got. The trace
added on the fourth round is what made the "every call returns" finding
possible at all:

```
IRON COURT: secession of legion from <faction> begins - rebels qb2,
            8 province(s), 3 of 4 lord(s) able to leave, 3 leaving
IRON COURT: rising 1 of 3 at <region> under <subtype> (cqi 4763)
IRON COURT: rising 1 spawned and took the throne
IRON COURT: cqi 4763 taken off the board, his army left standing
IRON COURT: handing over <province> (1 of 8)
IRON COURT: declaring war on qb2
IRON COURT: war declared
```

> **Rule.** A once-per-campaign event that mutates the world logs **per call**,
> not per event. A dozen lines is free and it is the difference between a
> location and a hypothesis.

---

## 6. The three offline instruments added

### 6a. `gen_iron_court.check_rebel_generals()`

Re-derives the permitted-general whitelist from the cached
`faction_agent_permitted_subtypes` on every build and refuses on drift. Watched
failing three ways rather than trusted green:

```
IC.REBEL_LORD is wh3_dlc23_chd_infernal_castellan, which no faction in
    REBEL_POOL may field as a general
IC.REBEL_GENERALS lists derpy_bzaark, which not every faction in REBEL_POOL
    may field as a general
IC.REBEL_GENERALS is missing wh3_dlc23_chd_sorcerer_prophet_metal, which all
    four pool factions permit
```

A subtype key normally fails **silently**. Here a wrong one is a CTD with no
Lua error and no script-log line, so it has to fail the build instead.

### 6b. The harness stub records what it is given

`cm.kill_character` now records `destroy_force` instead of asserting it, and
`cm.callback` runs its function **and records the delay**. The
`make_faction_leader` flag had been recorded since the stub was written and
**nothing ever asserted on it** — which is exactly how 2d shipped. The data was
sitting there.

> **Rule.** A stub that records a parameter no check reads is a fault waiting
> to happen. Assert on every recorded field or stop recording it.

### 6c. `watch_one.py` — watching one check fail alone

`mutate_iron_court.py` reports the **first** check a mutant breaks, so a later
check aimed at the same rule is never seen to fail even though it would.
`watch_one.py` runs a single named check against a single mutation, with
nothing shadowing it, and asserts it fails mutated and passes clean.

This found two assertions that could not fail:

- a check whose two fixtures both landed on exact multiples of
  `rebel_lords_per`, where `ceil` and `floor` agree — so the rounding mutant
  survived a check written to be about that division
- `assert(deferred[i] == IC.TUNE.secede_step)` — the knob agreeing with itself.
  Setting the knob to `0` left it green, and a zero-delay callback runs in the
  same frame, so zero **is** the bug

And one piece of genuinely dead code: `if want_lords < 1 then want_lords = 1
end`, unreachable because `members` counts the lords too.

---

## 7. The secession as it now stands

| | rule |
|---|---|
| when | instantly at zero loyalty, no countdown |
| how much land | `ceil(#pool * share / 100)`, floored by what the party governs or what has rotted past `prov_defect_floor`; never the capital |
| who leaves | `min(#defectors, ceil(members / rebel_lords_per), rebel_lords_max)` |
| members | every man of the party, **heroes and retainers included** |
| defectors | lords only, not a legend, and **subtype on `IC.REBEL_GENERALS`** |
| the general | the departing lord's own subtype and name; fallback `wh3_dlc23_chd_overseer` |
| the crown | only the army that wakes a dormant faction |
| the army | `destroy_force = false`; the host survives leaderless |
| the shape | one world change per frame via `cm:callback` |

**Verification:** 378 harness checks, 113 mutants, 0 unexplained.

---

## 8. Who a rebellion IS — the four things the fix left wrong

The crash fix worked and the secession ran. Looking at the result, the author
raised five things. Four were defects; one was correct behaviour that read as a
bug. All of this was measured through the live bridge before any of it was
written.

```
player = wh3_dlc23_chd_conclave
qb1: dead=false regions=2  forces=3  war_with_player=false
qb2: dead=false regions=12 forces=15 war_with_player=true
qb1 name = wh3_dlc23_chd_chaos_dwarfs_qb1
qb1 flag = ui\flags\wh3_dlc23_chd_chaos_dwarfs_rebels
faction:attitude_towards()               -> nil, no such method
faction:strength_of_diplomatic_relation  -> nil, no such method
```

### 8a. "2 rebel factions emerged" — correct, and not a bug

Two *separate* secessions, in the same turn, from two different courts: the
`tower` party from the AI Legion of Azgorh (→ qb1) and the `legion` party from
the player's Conclave (→ qb2). The pool exists so that two rebellions are two
factions on the map rather than one blob. The 12-vs-2 region split and the
15-vs-3 force counts are the same two events (`military_force_list` counts
garrisons — qb2's 15 is 3 spawned plus 12 garrisons).

### 8b. The name — fixable at runtime, and only by one call

`cm:change_custom_faction_name(faction_key, name)` takes a **plain string**,
which is the shape a rolled party name already has: no loc key, no DB row,
nothing to ship. It is the only lever.

**CA never calls it** — zero hits across all 5,778 shipped scripts — so the two
things that would have bitten were checked by hand instead:

- `campaign_manager` defines **no wrapper** for it (542 wrappers, none of these
  three). It forwards through `set_object_class(self, game_interface)` straight
  to episodic scripting. This is the exact trap `create_force_with_general`
  fell into: *that* one has a wrapper, and the wrapper `script_error`s when the
  rebels are not on the map yet.
- A dormant faction is **dead** until `create_force_with_general` wakes it, and
  whether the rename takes on a faction that is not on the map cannot be
  answered offline. So the naming step runs **after** the armies, not before.

It is also **remembered** (`cm:set_saved_value("derpy_ic_risen_" .. key, name)`)
and re-applied at first tick: the call is not documented as persistent, and a
name that reverts on the next load is worse than one that never existed.

### 8c. The crest — not fixable at runtime, fixable in the DB

There is no setter. `flags_path` is a `factions_tables` column and nothing in
CA's whole scripting reference writes one — searched, not assumed. So a crest
cannot track the party that secedes: the column is read before the campaign
rolls which parties it seats.

**Two things were done about it.**

First, a confederated house secedes into **its own faction**.
`IC.rebel_faction_for(faction_key, slug)` prefers the party's own faction where
it has one — azgorh is the Legion of Azgorh, bzaark is the House of Bzaark —
which gets the name and the crest together, because they are that faction's own.
And `own ~= faction_key`, because `faction_for_origin("conclave")` answers
`wh3_dlc23_chd_conclave`: a Conclave party in a Conclave campaign would
otherwise be handed the player's own provinces and declare war on him on his own
behalf.

Second — the nine interests are not factions and have nothing of their own to
be, and **all four pool factions shared one `flags_path`**, which is why two
rebellions drew one green banner:

```
wh3_dlc23_chd_chaos_dwarfs_qb1/qb2/qb3, wh3_dlc25_chd_chaos_dwarfs_invasion
    -> ui\flags\wh3_dlc23_chd_chaos_dwarfs_rebels      (all four)
```

`tools/make_ic_rebel_flags.py` gives each one its own, recoloured out of CA's
banner — the frame, rivets and wear stay CA's, only the sigil's hue moves, and
the band is measured (`--report`: the sigil is hue 0.30, the bronze frame 0.05)
rather than masked by hand. `IC.TUNE.rivals_max` is 4 and the pool is 4, so a
campaign can never seat a party that wants a fifth.

> **The ceiling stands:** four crests, assigned in secession order. Nothing about
> them can track which party actually left.

**Three traps in doing it:**

- **The cached table cannot be used to clone the rows.** RPFM's dump of
  `factions_tables` carries a definition of **61 fields with 34 patched
  `unused: true`** against rows of **45 cells**, so `_cache_table`'s zip of names
  to values is right for nine columns and wrong after. A row override replaces
  all 45 columns and a wrong one is a load-time rejection naming an arbitrary
  faction. The donor rows are RPFM's own `export_tsv` out of **`db.pack`** (not
  `data.pack`), kept in `Modding Files/source/iron_court/_donor_factions.tsv`,
  and `check_factions()` holds every column of every row against them so the
  override can only ever touch `flags_path`.
- **That mismatch broke check 14**, which had indexed cached tables by name for a
  month and only ever met aligned ones. It now detects the mismatch and **says
  so** instead of skipping — a check that quietly stops checking is the fault
  this file exists to refuse.
- **The MCP session is per process.** `open_packfiles` in one script and
  `export_tsv` in the next answers *Pack not found*: `_session()` caches the id
  in a module global. Everything that must see an open pack happens in one run.

`mon_banner.dds` is **BC3_UNORM with 9 mips** (texdiag on CA's), so texconv does
both directions — Pillow silently writes something that is not one.

### 8d. The hostility — a threat score, not an attitude

`force_attitude` is **NOT DOCUMENTED**, and neither `attitude_towards` nor
`strength_of_diplomatic_relation` exists on the faction script interface (both
measured live, both `nil`).

`cm:set_base_strategic_threat_score(faction_interface, score)` is documented, is
what the Coalition Supervisor already uses, and drives the attitude every
faction holds toward this one. `IC.TUNE.rebel_threat = 30`, set on the rebels in
the same frame as the war.

The war alone could never fix this: it is declared against the court the party
left, which is the right target and is **not the player** when an AI faction
loses a party.

### 8e. Embedded heroes — they defect now

`cm:spawn_agent_at_position(faction, x, y, agent_type, subtype)` — faction
**interface**, and the type and subtype are a **pair** in
`faction_agent_permitted_subtypes`. A wrong pairing is not the usual silent
no-op; the wrong half of exactly this table is what made the Castellan the
rebellion's fallback *general* and killed the game with no Lua error (§2b).

So `IC.REBEL_HEROES` maps subtype → agent type, derived from the DB and
re-derived on every build by `gen_iron_court.check_rebel_heroes()`:

```
champion  wh3_dlc23_chd_bull_centaur_taurruk
engineer  wh3_dlc23_chd_infernal_castellan
wizard    wh3_dlc23_chd_daemonsmith_sorcerer_{death,fire,hashut,metal}
```

Two permitted pairs are excluded on purpose and `REBEL_HERO_EXCLUDED` says why:
`colonel`/`wh3_dlc23_chd_overseer` is a lord's subtype wearing a hero's agent
type, and `spy`/`wh3_dlc23_chd_gorduz_backstabber` is a legendary lord.

`IC.can_defect_hero` mirrors `IC.can_defect` with one extra bar — he must **not**
be lordly, or a lord whose subtype happens to be on the hero list is spawned as
an agent and his twenty-stack handed to nobody. Capped at
`IC.TUNE.rebel_heroes_max = 2`. One spawn and one kill per frame, in the same
step list as everything else: §1b is the rule this work was most at risk of
breaking back.

### 8f. Two checks that could not fail, found by `watch_one.py`

Both are findings, not gaps, and both were fixed the way §6c says:

- *"a rebellion nobody has a name for is still raised"* — broke the step's
  `if rebels and flying` guard and the check stayed **green**: `IC.rebel_rename`
  refuses a nil name itself and the step is `pcall`'d on top of that. Two guards
  where either suffices. Re-aimed onto the one thing the step guard alone
  decides — whether a **frame** is spent — which `cm.callback`'s delay recorder
  can count.
- *"a hero the rebels cannot field is never taken off the board"* — used
  `derpy_bzaark`, and `IC.is_legend` refuses him one line **above** the
  whitelist, so breaking the whitelist changed nothing. The **fixture** was
  wrong: `wh3_dlc23_chd_overseer` is a real key, a lord's subtype, permitted by
  no pool faction as an agent, and nothing else in `can_defect_hero` has an
  opinion about him.

And one piece of dead code removed rather than left green: an overlap test
between `REBEL_HEROES` and `REBEL_GENERALS` that `REBEL_HERO_EXCLUDED` makes
unreachable.

**Verification after all of it:** 389 harness checks, 124 mutants, 0
unexplained, and each new build-time check watched failing four ways.

---

### 8g. The number on the diplomacy screen — a fourth layer nobody had touched

**The war is not the attitude.** On 2026-09-18 the author photographed two seceded
parties on his own diplomacy list at **+76 and +67**, one of them at war with him.
Attitude, stance and behaviour are three separate layers
(`docs/CAMPAIGN_AI.md` §3) and `force_declare_war` moves the last of them.
`set_base_strategic_threat_score`, added the day before, moves targeting. Neither
moves the number the player reads.

`diplomatic_relations_attitudes` is the whole scale, seven rows: `hostile -230`,
`very_unfriendly -70`, `unfriendly -30`, `neutral 0`, `friendly 30`,
`very_friendly 70`, `best_friends 230`. **+76 is "very friendly"** — and it is a
sum of factors of which `CULTURAL_SIMILARITIES` is one, so a Chaos Dwarf party
breaking from a Chaos Dwarf court begins liked and the war does not subtract
enough to notice.

**`cm:apply_dilemma_diplomatic_bonus(a, b, n)` is the lever**, `n` in `[-6, +6]`,
faction **key strings** — the opposite receiver convention to
`set_base_strategic_threat_score` beside it. CA: *"carries a diplomatic attitude
modifier that is actually applied."*

**It accumulates, and that is CA's usage rather than an inference.**
`wh3_campaign_bonus_values.lua`'s `alter_attitude_each_turn_from_foreign_slot`
listener applies it to the same pair on every `FactionTurnStart` for as long as
the building stands.

**The count cannot be written down.** The magnitude of one `PENALTY_XXXLARGE`
lives in `diplomatic_factor_dilemma_events`, not in the call, and the attitude it
has to cross differs per pair. So `IC.rebel_sour` reads it back:
`faction:diplomatic_standing_with(other_faction_interface)` is documented, returns
an `int32`, and CA's caravan code is its one vanilla consumer. The loop applies,
re-reads, and stops on the number.

> **The cap is the termination proof, not a tuning knob.** Nothing says the engine
> settles an attitude inside the frame that changed it. If the read is stale the
> loop never sees its target and runs to `rebel_relation_max` — a deeper grudge,
> not a hang. This is the property `IC.rebel_kit`'s padding loop had to be
> rewritten to get after it took the mutation runner down on 2026-09-17, and it is
> why the mutant aimed at the cap is an **off-by-one** rather than a removal:
> removing it does not fail, it hangs.

**And what `REBELLED_AGAINST` is.** `cai_personality_diplomatic_events` has a row
for exactly this fiction, on factor group `diplomatic_factor_rebellion`, and it is
**transitive** — it would spread the grudge to third parties. It is not used:
**zero hits across all 5,778 shipped CA scripts**, and CA's own three
`cai_add_diplomatic_event` calls all pass a generic `PAST_EVENT_*` under the
comment `-- CHANGE THIS TO A NEW EVENT`. Unproven as a scripted call, and the
pairs that matter are named explicitly instead. It is the upgrade path if a
rebellion should ever sour the whole map.

### 8h. A party could rot to the floor without a single card

`secede_warn` fires from `tick_secession`, which needs `share >= secede_share`
**as well as** low loyalty. A party too small to be worth counting down got
nothing — and since 2026-09-17 a party at zero loyalty leaves **on the turn it
lands**, so the first notice was the army.

`loyalty_warn` (index 2607) is raised from **`IC.move_loyalty`**, which is the one
funnel every loyalty write already goes through. That is what makes it free: the
crossing is computed from `was` and the new value, so nothing new goes into the
save and there is no second sweep of the court to keep in step.

- **On the transition, not the state.** `drift_loyalty` moves every house every
  turn, so a card keyed on the state is a card a turn for the rest of the
  campaign.
- **Not the Crown.** The player's own house sits in the same table as the rivals;
  without the guard he is warned that he is turning against himself.
- **Above `secede_loyalty` and below `loyalty_start`**, both asserted — at or
  below the first it arrives with the countdown instead of in front of it, and at
  or above the second every party is born already warned about.

### 8i. The rolled names were English committee-speak

The author, seeing `High Window Front` and `Red Line Council`: *"pretty funny and
not good... make it more chaos dwarf oriented and loreful"*.

**Both halves were wrong at once.** Five of the nine suffix heads — `Front`,
`Bloc`, `Council`, `League`, `Assembly` — are twentieth-century politics and read
as a parliament wherever they land; and the blandest tails (`the Red Line`, `the
High Window`, `the Quiet Page`, `the Open Road`, `the Crossing`) are English
idioms with nothing of the Dark Lands in them. Either alone survives. Rolled
together they produce `High Window Front`.

The shapes are unchanged, because they are what keeps the roll grammatical:
`1..IC.NAME_SUFFIX` read as a body of men standing **after** what they are named
for (`Black Standard Throng`), the rest as a line **in front of** what it is bound
to (`Hand of the Iron Mask`). Every replacement was read in both.

Where the lore comes from, per list: the Infernal Guard are disgraced Chaos Dwarfs
sworn to atone, **masked and silent** (`the Silent Vow`, `the Iron Mask`); a
Sorcerer-Prophet slowly **turns to stone, hands first** (`the Stone Tongue`, `the
Grey Hand`); blackshard is their own armour plate; Zharr-Naggrund is the first
hold.

> **A save holds the INDEX, not the string.** A campaign already running re-reads
> its roll against the new lists, so every party renames itself once on load. A
> faction that has **already seceded** keeps its old name, because
> `IC.rebel_rename` saved the string rather than the roll.

`gen_ic_ui.py` check 20 measures all 672 rolled names in pixels, single-word and
whole-string, and passed unchanged — the longest name is still
`The Brotherhood of the Black Standard` at 37 characters, exactly what it was
before.

### 8j. The Crown's loyalty was a dead number, and the card said otherwise

The author, 2026-09-18: *"what happens if the players party went to 0?"*

**Nothing happened, and every path said so deliberately.** The Crown sits in the
same table as the rivals, and each consumer refuses it *before* it reads the
number: `tick_secession` skips it (`slug ~= own`), `at_breaking_point` returns
false for it, the favours answer `"your own house"`, every plot answers
`"own party"`, and `mood_of_the_court` passes it over. Meanwhile `drift_loyalty`
walks `pairs(court.houses)` with no Crown guard at all, so the number was
**written every turn and read by nothing** — and reachable: with no seat, the
Crown drifts `loyalty_drift_none` a turn from 55.

**And the card drew a threat it could not make.** The Crown is card one of the
party grid, `ICUI.mood` had no Crown branch, so the player's own party read
**"PLOTTING"** — the one house in the system no plot can be aimed at.

**`IC.splinter` is what the number costs now.** At `splinter_loyalty` the men who
will not answer any more organise as an interest of their own.

> **SUPERSEDED 2026-09-18** on two counts, see
> `HANDOFF_20260918_IRON_COURT_WARNINGS_AND_AUDIT.md` SS4 and SS6. It no longer
> happens on the turn the line is crossed: there is a `warn_turns` count and a
> card in front of it, cancelled if the Crown recovers. And the interest is no
> longer rolled freely over the unseated ones - only one somebody in the faction
> has the background for, or the court seats a party with weight and nobody in
> it.

> **It needed almost no machinery, and that is why this shape was chosen.**
> Membership is **derived, not stored**: `IC.house_of_character` reads a man's
> rolled background, and a background whose party is not seated **falls through
> to the Crown**. So seating one of the unseated interests re-homes every man who
> already belonged to it — they were the player's only because nobody was
> speaking for them. No character is moved and nothing new goes into the save.

Four rules, each with a check and a mutant:

- **The share is moved, not minted.** `add_house` hands out `weight_start`;
  minting it would move every *other* party's share, because share is weight over
  **total** weight. Floored at 1, as the `kinsman` and `pledge` moves are.
- **The Crown recovers to `loyalty_start`** — a *termination proof*, not a
  kindness. Without it the Crown stays below the line and splits again next turn,
  and every turn after, until the interest pool is empty.
- **The breakaway opens at the loyalty the Crown left at.** Seated at the neutral
  number it would be a party with no opinion about the thing it just did.
- **It runs after `tick_secession`**, so a party born this turn is not judged on
  the turn it was born.

**The build gate caught the one real mistake.** `check_loyalty_writers` refused
the pack: *"loyalty is written directly in IC.splinter"*. Loyalty has exactly one
writer because it used to have six, and `IC.splinter` had quietly become the
seventh. The fix was not an exemption — an **opening** loyalty is not a move, and
`add_house` has always written one (the regex does not see it because a table
constructor's field has no receiver), so `add_house` took an optional fourth
argument and clamps it.

**And the fixture fought the turn.** The ordering check went red on its first run
because `IC.ai_fill_offices` seats a Crown man on the way past, worth
`loyalty_appointed` (+8) plus a weight bump — so a Crown set at the secession line
arrived at 28, above the splinter line, and nothing split. Both of that check's
preconditions are asserted out loud now: a check that silently needs its subject
in a particular state passes forever the day the fixture drifts.

> **One check was re-aimed rather than kept.** *"your own house splitting is not a
> secession"* asserted that no army rises and no province moves — which no
> plausible mutation could break, since nothing in `IC.splinter` calls anything
> that could. It was replaced by the ordering check above, which can.

---

---

## 9. Open, reported, not fixed

- A rebellion's crest still cannot be the seceding party's own sigil. Four
  crests, assigned in secession order, is the engine's ceiling (§8c).
- The `factions_tables` override touches four of CA's rows, so it conflicts with
  any other mod that edits `wh3_dlc23_chd_chaos_dwarfs_qb1/qb2/qb3` or
  `wh3_dlc25_chd_chaos_dwarfs_invasion`. They are quest-battle factions, so the
  surface is small, but it is not nil.
- ~~**`dissolve` is a second dead renderer.**~~ **FIXED 2026-09-18.** Both it and
  `pressed` are in `IC.LOG_KINDS` now, and the name-by-name guard that let this
  happen — a check asserting `IC.LOG_KINDS.splinter` "so splinter is not a third"
  — is replaced by a gate comparing the renderer's branches against the whitelist
  both ways.
- ~~`IC.log(faction_key, "pressed", ...)` writes nothing.~~ **FIXED 2026-09-18**,
  and it was the one that mattered: `pressed` is the moment the strongest bloc
  stops waiting for a reason, the start of the pressure route to secession and
  the only thing the court does with no input from the player at all.
- `ic_card_holder` wraps a long party name over the portrait. UNCHANGED by the
  2026-09-18 name rewrite and re-confirmed in `ic_court.png`: the longest rolled
  name is the same 37 characters it was, and `Covenant of the Bound Hundred`
  spills its second line across the top of the portrait.
- **A rebellion sours only against the court it left and the human players.** A
  third-party AI still reads it as friendly. `REBELLED_AGAINST` is the transitive
  event that would fix that and it has zero CA precedent as a scripted call
  (§8g).
- The two Wwise sound names cannot be proven offline.
