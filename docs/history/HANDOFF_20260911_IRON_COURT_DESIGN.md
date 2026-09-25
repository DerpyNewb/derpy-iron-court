# Handoff — The Iron Court: a Chaos Dwarf political system designed, and its DB half built (2026-09-11)

**Designed, specced, mocked up, and PHASE 1 BUILT: DB, traits, the court model, the four UI
files and the packing gate, every offline check green. Nothing packed, nothing deployed,
nothing run in a campaign.**

A new mod: `derpy_iron_court.pack`. A Rome 2-style political system for the Chaos Dwarfs —
houses as parties, offices held by characters, Overseers as governors, intrigue that runs
whether or not the player opens the panel, and every Chaos Dwarf faction running the same
court model.

Files produced:

    docs/superpowers/specs/2026-09-11-iron-court-design.md
    docs/mockups/politics_panel.html
    docs/mockups/politics_panel.png
    tools/gen_iron_court.py
    tools/gen_iron_court_emitter.py
    tools/gen_ic_ui.py
    tools/import_iron_court.py
    tools/_iron_court_harness.lua
    Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua
    Modding Files/pack/ui/campaign ui/derpy_ic_{panel,card,row,opener}.twui.xml
    Modding Files/source/iron_court/*.tsv   (5 tables + loc)

Read the spec before writing any more code. The implementation plan is **not yet written** —
the build so far followed the spec directly.

---

## 1. What was decided

| Question | Answer | Why |
|---|---|---|
| Political actors | The ten modded houses | They already exist with art, units, ancillaries and lords. Inventing court cliques would overlap the Great Guilds. |
| Stakes | Secession / civil war | Rome 2's politics mattered because it could bite. Unrest-only is ignorable. |
| Venue | The player's own court; houses join by conquest | Starts small, grows with the campaign. An empire-wide council gives the player little control and puts all the work in the AI half. |
| Officeholder | A character, whose house gains by it | Rome 2's exact shape. Makes lords into careers. |
| Governors | A new Overseer agent cloned from Kislev's Ataman | Chosen **against** the recommendation — see section 5. |
| Intrigue | Two-way, plus house-vs-house, plus crises | The court must have a pulse when nobody is looking at it. |
| AI scope | **Every** Chaos Dwarf faction runs a court | Requested explicitly. Same model, no UI. |
| Currency | Court Influence, in Lua save state | So politics never competes with Tower of Zharr seat claims for `wh3_dlc23_chd_conclave_influence` at 300 per seat. |
| Packaging | Standalone pack, phase 0 spikes then two phases | Keeps a politics bug out of the 14.8 MB published lords pack. |

**Standing is a share of 100%, not a stockpile.** Promoting one house demotes every other by
arithmetic rather than by a decay rule, and the panel gets one honest picture. This is the
single most load-bearing choice in the design.

**Affinity is the friction.** Each office is one house's by tradition; appointing that house's
man doubles its standing gain, appointing an outsider costs the affine house loyalty. The
whole Rome 2 squeeze is one column in a table, not a rule engine.

---

## 2. Verified this session, and how

Everything below was read out of `Modding Files/reference/ca_script_docs_wh3/` or
`.skilltree_cache/` this session, not recalled.

| Claim | Source |
|---|---|
| `province_governors_tables` exists with **exactly one vanilla row**, `wh3_main_ksl_ataman` | `.skilltree_cache/province_governors.json` |
| `character:is_governor()`, `character:loyalty()`, `personal_loyalty_factor` | `scripting_doc.html` |
| `faction:provinces()`, `province:regions()`, `capital_region()`, `faction_province_for_faction()` | `scripting_doc.html` |
| `faction:character_list()`, `character:is_dead()`, `is_wounded()`, `has_trait()`, `rank()`, `command_queue_index()` | `scripting_doc.html` |
| `cm:apply_effect_bundle_to_faction_province(bundle, region, turns)` applies to **"the portion of the province owned by the owner of the specified region"**; `-1` is indefinite | `campaign/episodic_scripting.html` |
| `cm:create_new_custom_effect_bundle(base)` + `apply_custom_effect_bundle_to_faction_province` | same |
| `cm:transfer_region_to_faction(region_key, faction_key)` — immediate | same |
| `cm:force_rebellion_with_faction(region, faction_key, max_units, full_strength, [suppress_po])` — returns the force | same |
| `cm:force_declare_war(attacker, target, invite_attacker_allies, invite_defender_allies)` | same |
| `cm:show_message_event(faction, title_loc, primary_loc, secondary_loc, persistent, index)` | same |
| `cm:set_saved_value` / `get_saved_value` / `random_number` | `campaign/campaign_manager.html`, **not** `episodic_scripting.html` |
| Events: `FactionJoinsConfederation`, `FactionBecomesVassal`, `FactionTurnStart`, `CharacterTurnStart`, `CharacterConvalescedOrKilled`, `CharacterRankUp`, `CharacterCapturedSettlement`, `CharacterRazedSettlement`, `RegionFactionChangeEvent`, `GarrisonOccupiedEvent`, `RegionRebels` | `scripting_doc.html` |
| Ten house faction keys | `docs/MOD_STRUCTURE.md` |
| ToZ seats cost 300 Conclave Influence | `docs/TOWER_OF_ZHARR_CUSTOM_SEATS.md:31` |
| GUID prefixes taken: `DE14`–`DE18` (Exchange, rites), `GG21` (Guilds), `DE15` retired | `docs/CUSTOM_UI.md`, `tools/gen_guilds_ui.py:36` |

**Nine (effect, scope) pairs verified against vanilla's own
`effect_bundles_to_effects_junctions`**, with `is_positive_value_good` read from `effects.json`
the same day. Two of the nine are `False`. All nine are re-checked by `gen_iron_court.py`'s
`check()` at every run, so drift after a game patch is caught rather than shipped.

---

## 3. Corrections found the hard way

**There is no `CharacterKilled` event.** It is `CharacterConvalescedOrKilled`, and it fires for
**wounding as well as death**. A handler without an `is_dead()` test empties an office every
time its holder takes a scratch. This was found by grepping for the event name that seemed
obvious and getting nothing.

**Chaos Dwarfs have no "slaves" pooled resource.** The set is `labour`, `armaments`,
`raw_materials`, `workload`, `efficiency`, `conclave_influence` — read from
`pooled_resources.json`. The design's "slave upkeep" and "post-battle slaves" were written
before this was checked and are now Workload and Labour. Slaves are flavour; the mechanics are
Labour or Workload underneath.

**There is no labour *production* modifier CA ships in a bundle.** The nearest usable pairs are
`wh3_dlc23_pooled_resource_chd_workload_modifier` (`faction_to_province_own`, seen, values
−15/−5) and `wh3_dlc23_pooled_resource_chd_increased_labour_loss` (unseen). The Keeper of the
Chains office therefore reduces Workload rather than adding Labour.

**A bash heredoc could not write the mockup HTML.** `cat > file <<'EOF'` came back with
`unexpected EOF while looking for matching '` at the first line containing a quoted CSS font
name — the quoted-heredoc form did not survive the tool wrapper. The Write tool did it in one
call. This is the **second** time this workspace has recorded that finding (the Great Guilds
spec hit it at 430 lines). **Do not write large files through a heredoc here.**

**Playwright refuses `file:` URLs** and its filename root is case-sensitive on the drive
letter: `G:\...` was rejected as "outside allowed roots" while `g:\...` was accepted. Serving
the folder with `py -m http.server` and screenshotting over `http://127.0.0.1` worked.

**The RPFM MCP tools were absent this session but RPFM itself was up.** The session banner
reported `rpfm (ConnectionRefused)`, yet `curl http://127.0.0.1:45127/sessions` answered. The
server had started after Claude Code, which is the known case for the raw-HTTP fallback. **A
failed MCP registration is not evidence RPFM is closed** — probe the port before believing the
banner.

---

## 4. What was built

`tools/gen_iron_court.py` — 23 effect bundles, 25 junctions, 62 loc rows. `--check` and
`--selftest` both green; TSVs written in RPFM's format (header row, then
`#<table>_tables;<version>;<container path>` tab-padded to the column count).

Bundles: 6 office, 6 vacancy, 1 governor base, 10 house-governor flavour. **No per-rank
bundles** — the governor scales off `derpy_ic_gov_base` with `create_new_custom_effect_bundle`,
which still resolves against a real `effect_bundles` record, so that row must exist.

Two properties of the generator are the reusable part:

**The sign trap is designed out rather than commented about.** No data row carries a raw sign.
Each effect entry is a positive **magnitude** plus an **intent** (`BOON` / `MALUS`), and
`signed_value()` derives the sign from vanilla's `is_positive_value_good`:

```python
positive_is_wanted = (good == (intent == BOON))
return magnitude if positive_is_wanted else -magnitude
```

So `wh3_dlc23_pooled_resource_chd_workload_modifier` and
`wh_main_effect_force_all_campaign_upkeep` (both `good=False`) emit **−15** and **−10** as the
player's benefit automatically, and their vacancy penalties emit **+5**. This is the inversion
that shipped two Great Guilds tracks as red penalties past every check, and it cannot recur by
inattention here. `signed_value()` also **refuses a pre-signed magnitude**, so the old habit
fails loudly.

**The selftest injects five faults and asserts `check()` names each**, then restores and
asserts the data passes again:

1. an invented effect key
2. a scope CA never pairs with that effect
3. a wrong `is_positive_value_good`
4. a typo'd faction key (checked back against `MOD_STRUCTURE.md`)
5. an office pointing at a house that does not exist

`check()` also refuses on duplicate bundle keys, junctions for undefined bundles, missing or
duplicated loc, empty loc text, `||` in a loc value, and an uppercase pack name.

---

## 4b. Phase 1, built the same session

Four more pieces, every offline gate green:

| Tool | What it does | Gate |
|---|---|---|
| `gen_iron_court.py` | 23 bundles, 25 junctions, **16 traits**, 126 loc | `--check`, `--selftest` with **7 injected faults** |
| `gen_iron_court_emitter.py` | this mod's own copy of the XML emitter | imported by the UI generator |
| `gen_ic_ui.py` | 4 `.twui.xml`, 43 components, 204 GUIDs | `--check`, `--selftest` with **7 injected faults** |
| `zzz_derpy_iron_court.lua` | the court model, ~560 lines | `luac -p`, `check_lua_api`, `check_lua_undeclared` |
| `_iron_court_harness.lua` | **18 runnable checks** under Lua 5.1.5 | 4 mutants, all caught |
| `import_iron_court.py` | the packing gate | refuses on any generator/TSV/Lua/UI drift |

### The trait chain is FOUR tables, not two

`character_traits` (v3), `character_trait_levels` (v0), **`trait_info` (v1)** and optionally
`trait_level_effects` (v0). `trait_info` is a single-column table with one row per trait —
vanilla has **744 of each** — and it is exactly the kind of table a trace outward never
reaches. `check()` refuses on a trait missing from any of the three.

Two more facts read this session: **all trait loc lives in `character_trait_levels__.loc`**
(there is no `character_traits__.loc` at all), keyed off the **level** key, four keys per
level — `onscreen_name`, `colour_text`, `explanation_text`, `removal_text`, 979 of each. And
**178 of vanilla's 979 trait levels carry zero effects**, so a marker trait with no
`trait_level_effects` rows is legal and ordinary. `chaos_dwarfs` is a real `trait_categories`
key.

### The sign trap is designed out, not commented about

No data row carries a raw sign. Each effect entry is a positive **magnitude** plus an
**intent** (`BOON`/`MALUS`), and `signed_value()` derives the sign from vanilla's
`is_positive_value_good`. So `chd_workload_modifier` and `force_all_campaign_upkeep` (both
`good=False`) emit **−15** and **−10** as the player's benefit automatically, with their
vacancy penalties at **+5**. `signed_value()` also refuses a pre-signed magnitude, so the old
habit fails loudly. This is the inversion that shipped two Great Guilds tracks as red
penalties past every check.

### Standing is stored as a WEIGHT and the share derived

The spec calls standing "a share of 100%". The Lua stores a raw weight per house and computes
the share at read time, which makes that property **true** rather than maintained: shares
cannot drift off 100 because they are never stored, and "raising one house lowers every other"
needs no decay rule and no renormalise pass to forget to call.

### Findings that cost a run each

**`string.find`'s `plain` flag corrupts the string subsystem process-wide for the rest of the
game session.** `check_lua_api.py` caught it in the save-state unpacker. `|` is not a magic
character, so `"%|"` without the flag is the fix. The packing gate now refuses on it too.

**`FactionBecomesVassal`'s context exposes `vassal()`, NOT `faction()`**, and carries no master
accessor — read it off the vassal with **`faction:master()`**. `factions_master()` does not
exist (0 hits). Both would have thrown and killed the listener silently.
`FactionJoinsConfederation` is the pair that *does* have `faction()` (the absorbed faction) plus
`confederation()` ("the confederations owning faction").

**ONE GUID PREFIX PER FILE, not per mod.** `EU.assign` restarts its counter for every file it
is given, so four files sharing a prefix mint four *identical* GUID sets — and a cross-file
GUID collision is a silent non-draw. The check caught it on its first run. The Exchange's
registry is per file for exactly this reason (`DE16` panel, `DE17` row, `DE18` button). The
Iron Court uses `IC30`/`IC31`/`IC32`/`IC33`.
**`tools/gen_guilds_ui.py` uses a single `GG21` for all four of its files** and its own check
does not compare across files — worth a look before the Guilds' next build, though its panel
is reported working in game so the collision may be benign in practice.

**Two checks were written wrong and passed anyway** — both worth carrying, because both are the
"gate that guards nothing" shape:

1. The soundcategory check tested the element carrying `interactive="true"`, which is the
   `<standard>`/`<hover>` **state**, not the component that carries `soundcategory`. It fired
   on every button in every file. Fixing it flipped the check from firing on everything to
   firing on **nothing**, and only an injected fault distinguishes those two — so there is now
   one for it.
2. `check_lua_undeclared.undeclared()` takes the **source text, not a path**. The packing gate
   passed it a filename, so it scanned the filename, found nothing and passed vacuously. Fixed
   and then proven by injecting `SOME_UNDECLARED_CONSTANT`, which it now refuses on.

Also: the Lua bundle-key check must skip string literals ending in `_` — those are
concatenation **prefixes** (`"derpy_ic_office_" .. slug`), and testing them as whole keys is a
false refusal on correct code.

---

## 4c. The panel and its opener — and six ways the first draft was wrong

`zzz_derpy_iron_court_ui.lua`. The opener sits on the top resource strip **left of the Great
Guilds' button**, so the row reads Iron Court, Guilds, Exchange.

The first draft passed `luac -p`, `check_lua_api` and `check_lua_undeclared` and would still
have been broken in six ways. Every one was found by **reading the two shipped mods** rather
than by testing:

1. **Children are never positioned by the `.twui.xml`.** The Guilds' own comment: *"layout()
   places every component, including the panel's own children, which the .twui.xml offsets do
   not."* The draft set each cell's text and never moved it, so every panel label and every row
   cell would have drawn at the screen origin over the campaign map.
2. **`DestroyComponent` does not exist** in either shipped mod — 0 uses. The calls are
   `DestroyChildren()` and `Destroy()`.
3. **Rows are created into the PANEL**, not a sub-holder, and created **once** with a fixed
   count, then shown or hidden. The draft re-created them every redraw behind a destroy that
   would have thrown. `ic_rows_holder` is gone from the layout entirely — a holder buys nothing
   when every child must be `MoveTo`'d by hand anyway.
4. **`PropagatePriority(60)` was missing**, so the panel could draw under other HUD components.
5. **An interactive panel eats the mouse.** Without it the panel is scenery: the cursor reaches
   the campaign map through 920x736 of background, so hovering raises the region and army
   tooltips of whatever is behind it and a click lands on the map as well. A literal
   `SetInteractive(true)` is safe **only because `close()` destroys the panel**; if it is ever
   changed to hide, the flag must be written from the same variable as the visibility.
6. **Panel size comes from `panel:Dimensions()`**, not from a constant that can drift from the
   XML.

### Two more checks that were guarding nothing

**`check_lua_undeclared` does not resolve `TABLE.FIELD`.** A UI file that reads `EX.BUTTON_SIZE`,
`GGUI.BTN_SIZE` and `IC.HOUSES` trips on `BUTTON_SIZE`, `BTN_SIZE`, `HOUSES` — and the shipped
`zzz_derpy_guilds_ui.lua` trips the same way for the same reason. That is what the function's
`elsewhere` parameter is for; the gate now passes the union of what the pack **and its optional
neighbours** declare. It also **does not register every target of a multiple assignment**, so
`ICUI.BAR_X, ICUI.BAR_Y, ... = ...` reported half those names as undeclared. One name per line.

**A scan for a call must strip Lua comments first.** The new gate's `DestroyComponent` check
fired on a *comment* saying the shipped mods never call it — the same fault `CUSTOM_UI.md`
records, where a file documenting a past mistake in prose reads as a live reference.

### What the harness now proves without a campaign

31 checks, and the placement half is the point: the opener lands left of the Guilds with both
neighbours installed, takes the Guilds' slot with only the Exchange, takes the Exchange's slot
with neither, refuses an unsettled strip instead of clamping, and refuses a missing one instead
of guessing. The neighbours' slots are computed **in the harness from their own published
formulas**, so an arithmetic slip in `ICUI` cannot agree with itself.

**One mutant survived and taught something.** Swapping "offset by our width" for "offset by the
neighbour's" changed nothing, because the Guilds' button is 44px and so is ours — the two
formulas are the same number today. The test could not tell them apart. It now gives the
neighbour a 60px width so they separate, which is what would happen the day either mod changes
a size. A surviving mutant is a weak test, not a safe one.

---

## 4d. Deployed

`tools/deploy_iron_court.py` builds and deploys in one run — the gates, then RPFM, then the
copy. **Create, import and save must be one run**: pack state lives only as long as one MCP
session, so there is no resuming half way.

    Modding Files/Modpacks/derpy_iron_court.pack                     147,353 bytes
    F:\...\Total War WARHAMMER III\data\derpy_iron_court.pack        147,353 bytes

12 content files: 5 DB fragments, 1 loc, 2 scripts, 4 `.twui.xml`.

**Verified by reading the bytes back out of the DEPLOYED pack**, not the built one — a file
being present proves nothing about whether it decodes:

- both scripts decode as real source, 28,585 and 19,004 bytes, with 11 expected symbols
  present between them (including `context:vassal()` and the `"%|"` find, the two fixes that
  would be invisible in a size check)
- the four UI files carry **one GUID prefix each** with no cross-file leakage — the collision
  that the check caught on its first run
- `effect_bundles` carries the office, vacancy and governor keys; `trait_info` carries both
  trait kinds; the loc decodes as UTF-16 with the bundle, trait and panel keys present
- every file is **uncompressed** (`compression == 0`), which is why the strings read as text

**No basename collision** — `derpy_iron_court.pack` exists nowhere else in `data/` or the
Workshop folder. A duplicate basename is the "Failed to load mod" case.

**It is not enabled.** A new pack in `data/` is listed but unticked, and this one is not in
`used_mods.txt`. Tick it in the launcher or the mod manager before anything happens.

**Not published.** The Workshop is a separate step and this has never run in a campaign.

---

## 5. The risk taken with eyes open

**Governors are a new agent subtype cloned from Kislev's Ataman.** The recommendation was to
reuse existing lords and heroes and skip the clone entirely, on the grounds that this workspace
has twice had cloned hero subtypes come back with `SkillList 0` and silently dead agent actions
(`[[wh3-cloned-hero-subtype-loses-skill-tree]]`,
`[[wh3-foreign-hero-needs-vo-culture-override]]`). The risk was stated in the question and the
Ataman route was chosen anyway.

That is a legitimate call — the Ataman is the only engine-native governor in the game and it
gets CA's own machinery — but it means **the clone must be proven before anything else is built
on it**. That is phase-0 spike 1.

---

## 6. Do not re-derive

- **`cm:set_saved_value` / `get_saved_value` / `random_number` are in
  `campaign/campaign_manager.html`, not `episodic_scripting.html`.** Grepping the latter returns
  zero and reads like absence. All three are already used 44 / 22 / 45 times in shipped pack Lua.
- **`effect_bundles` is version 4 (9 fields); `effect_bundles_to_effects_junctions` is version 3
  (5 fields); Loc is version 1.**
- **Ship BOTH the DB row text and the loc entries** for a bundle:
  `effect_bundles_localised_title_<key>` and `effect_bundles_localised_description_<key>`.
  Row text alone draws an icon with no text in Faction Effects — 27 bundles measured that way
  2026-09-05. Generate both from one string so they cannot drift.
- **A bundle description takes no `%+n`.** The placeholder works on an *effect* description
  because the engine substitutes that effect's value; a bundle has no single value and renders
  it literally. 1 of 5,855 vanilla bundle descriptions has one.
- **`is_global_effect = false` hides a live bundle from Faction Effects.** All 23 here are
  `true`.
- **`_unseen` scopes hide the effect from the player.** 3,107 junction rows use
  `faction_to_faction_own_unseen`; only 40 distinct effect keys appear at plain
  `faction_to_faction_own`. Check which you have before wondering why nothing shows.
- **Seats do not need storing.** `faction:provinces()` *is* the governor seat list. Capture and
  loss need no bookkeeping at all, and a partial province governs fine because
  `apply_effect_bundle_to_faction_province` targets the owner's portion.
- **`force_confederation` is asynchronous** — an absorbed house's characters appear about ten
  seconds later, so stamping them with a house trait cannot happen in the confederation handler.
- **No `DilemmaChoiceMadeEvent` listener may match a custom dilemma.** Hard CTD, seven
  measurements, bricks saves. Every ask in this design uses `cm:show_message_event` + a deadline
  in `set_saved_value` + a panel button.
- **No loc calls from turn handlers** — turn-1 CTD that pcall does not catch. The feed stores
  keys and numbers; the panel resolves names at draw time.
- **GUID prefix for this mod is `IC30`.** `DE15` is retired and must never be reused.

---

## 7. Still open

**Phase 0 — the two spikes, and they gate everything:**

1. **A cloned Ataman keeps its skill tree and its agent actions fire.** Section 5.
2. **`cm:transfer_region_to_faction` revives a confederated-away faction.** Every other call on
   the secession path is documented; this one is an inference, and it is now load-bearing for
   the AI half as well as the player's.

Plus a measurement: the AI pass at ~60 house records with a three-action-per-turn cap costs
nothing per turn.

**Phase 1 — the court. DONE offline**, all four items: traits, the core Lua, the UI generator
and the packing gate. `character_traits`, `character_trait_levels`, `trait_level_effects` and
`trait_info` are now cached. What phase 1 still lacks:

1. **The panel's own Lua** — `zzz_derpy_iron_court_ui.lua`. The four `.twui.xml` files exist
   and pass every check, but nothing creates them into the UI yet, so there is no panel in
   game. This is the single biggest remaining piece of phase 1.
2. **The opener button's placement.** Create on the **UI root** and read `resources_bar` as a
   *ruler* only, never as a parent — a layout group owns its children's positions and `MoveTo`
   never gets to have the fight. The Exchange parks its opener off the RIGHT end and the Guilds
   off the LEFT, so this one needs a third slot and must tolerate both being present.
3. **MCT settings**, so `IC.TUNE` is tunable without a rebuild.
4. **The `event_feed_message_events` rows** `cm:show_message_event` needs — index 0 draws
   nothing.
5. **Actually packing it.** `import_iron_court.py` is a verify gate that prints the destination
   map, exactly as `import_great_guilds.py` is; the RPFM import itself is still a separate step,
   and remember `import_tsv` cannot create a table (`new_packed_file` first, in the same MCP
   session).

**Phase 2 — the politics.** Intrigue, AI courts, inherited court state, crises, secession.

**Not started:** the agent subtype and its `province_governors` row, the
`event_feed_message_events` rows `show_message_event` needs (index 0 draws nothing), MCT
settings, and the implementation plan document.

**One design question already answered and not to be reopened:** AI Chaos Dwarf factions get
**no UI**. The player never opens another faction's court. What they see is feed news, a real
war on the map when an AI house secedes, and an inherited court when they conquer that faction.

## 8. The first deploy was rejected at database load, and why the dialog lied

The 2026-09-11 build packed and deployed clean, and the game refused it before the main menu:

```
The following mods cause a crash to the Database: derpy_iron_court.pack
The first invalid database record is
derpy_ic_gov_house_baalwh3_dlc23_pooled_resource_chd_raw_material_efficiency
in table effect_bundles_to_effects_junctions_tables
```

**The named row was not the faulty one.** `effect_bundles_to_effects_junctions.advancement_stage`
is a foreign key into `effect_bundle_advancement_stages` (8 rows) with column default
`start_turn_completed`, and vanilla fills it on **all 16,430** of its rows — zero empty. The
generator emitted `""` on **all 25** of ours, so every row was invalid and the engine named the
one that sorts first: `gov` before `office` before `vacant`, and `baal` before the other nine
houses. Time was lost looking for what was special about House of Baal and about
`raw_material_efficiency`. There was nothing; see the memory note now attached to
`wh3-bad-mods-report-names-the-row`.

**Why check() passed it.** Check 2 verified the (effect, scope) pair is one CA ships, which it
is — that check was answering a different question. Nothing looked at the other three columns.

**The check that now exists (check 14) is derived, not a column list.** For every table the
generator emits, any column it leaves empty is compared against the cached vanilla rows: if
vanilla leaves it empty **zero** times, it is a required reference and the run fails. Run over
all five tables it flags exactly one thing and clears `character_traits.pre_battle_speech_parameter`,
which 744 vanilla rows legitimately leave blank — a hardcoded list would have got that wrong.
`selftest()` sets `ADVANCEMENT_STAGE = ""` and asserts check 14 names it.

Redeployed at 147,853 bytes and verified by reading the **deployed** file back: 25 occurrences
of `start_turn_completed`, one per junction row.
