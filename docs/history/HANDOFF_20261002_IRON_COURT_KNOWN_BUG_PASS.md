# Iron Court known-bug pass - build DE2E446C (2026-10-02)

Follows `HANDOFF_20260930_IRON_COURT_GOVERNORS_MAP.md` (its section 14 is the short form of this
file). The author asked "what else is missing in the iron court mod", then "double check bugs
known, it couldve been fixed", then "fix the bugs, for 4. can it be a different rebel faction?"

## 1. Build and deploy

- `DE2E446C` (9,738,989 bytes, 1797 files verified in the saved pack), deployed to data/ at
  09:48 by `deploy_iron_court.py --deploy-only --wait` once the game closed. Backup
  `.bak_pre_auto_20261002_094811` holds `24F2E575`, the first build of this pass (everything
  but the edict fix), which itself replaced `3FBD2B1A` (backup `.bak_pre_auto_20261002_094135`).
- **Not pushed.** `repos/derpy-iron-court` was already one build behind before this pass
  (last commit a507fd8, build 92AF83D6; 3FBD2B1A synced but uncommitted). Sync with
  `tools/sync_iron_court_repo.py`, then commit, when the author asks.

## 2. The re-check: what was already fixed

Every item was read against the Lua carved out of the LIVE pack, which was byte-identical to
`Modding Files/pack/script/campaign/mod/`. Four items on the old handoffs' open lists were not
open:

| Item | State |
|---|---|
| MP answer arriving after the panel closed | fixed - `ICUI.after_op` returns when `comp(ICUI.PANEL)` is gone |
| `party_sabotage` card never fires | fixed in the 2026-09-28 bug-fix pass (MCT handoff) |
| news reaching non-Chaos-Dwarf humans | fixed, same pass (`IC.hears`) |
| AI court wiped after a load | fixed, same pass (`IC.loaded`) |
| no news when a vassal breaks | moot - vassal parties were CUT 2026-09-27; "vassal" has zero hits in the Lua |

## 3. What was fixed

1. **Three silent sounds.** `ICUI.SOUNDS.gov / ungov / dismiss` were `sound_settings.xml` hook
   keys (`UI_CAMPAIGN_EDICT_ISSUED`, `_RECRUITMENT_CANCEL`, `_UNIT_DISBAND`); two of those hooks
   map to nothing. Now `UI_CAM_Click_Kislev_Select_Available_Atamans` (the Governors view is
   modelled on Kislev's Atamans), `UI_CLICK_Recruitment_Cancel` (what the hook pointed at) and
   `UI_CLICK_Custom_Battle_Remove_Unit`. New `gen_iron_court.check_sound_names()` (in
   `check()`) holds every quoted `UI_`/`ui_` literal in the court's Lua files to
   `audio/wwise/event_data__core.dat` in `audio_base_bnk.pack`; it reported exactly the three
   old names against the old Lua. Selftest pins a hook key failing and a real event passing in
   another case.
2. **A full rebel pool wakes a dead house.** `IC.rebel_faction(exclude)`: dead pool faction
   first, then a dead `IC.ORIGINS` house faction (never `exclude`), and only then join the first
   live pool faction. The join fallback is captured BEFORE the origins loop, so a live house is
   never joined. A woken house is renamed by the existing `IC.secede` rename, restored on load
   by `IC.rebel_rename_all` (which already walks ORIGINS), takes court turns via
   `party_turn_due` (also walks ORIGINS), and has its old court cleared by `IC.forget_court`.
3. **`IC.rebel_sour` sours both ways.** It read `rebels:diplomatic_standing_with(other)` and
   applied `apply_dilemma_diplomatic_bonus(rebels, other, step)`, which by CA's argument order
   moves OTHER's regard - so the read never moved and every souring ran all 30 steps. Each step
   now applies `(other, rebels)` and `(rebels, other)`. Ruling (made by me, not the author; he
   was asked and said "fix the bugs"): the 2026-09-18 complaint was the rebels' attitude on the
   player's diplomacy screen, the 09-27 spec says the others dislike the rebels, so both; and
   the read now moves whichever way CA's order really runs.
4. **Edict relight by id.** `ICUI.apply_edict_lock`: the grey pass skips a button whose state
   is not in `ICUI.EDICT_GREY` unless it is already one of ours, records the ids it greys in
   `ICUI.edicts_greyed` (a set, or `false`), adding up across the 0.1s and 0.5s passes; the
   relight gives back only those ids. Before, one boolean lit every inactive button.
5. **`ICUI.confirm`** keeps `c:Id()` and re-finds the card inside `ICUI.PANEL` when it stops the
   pulse, instead of calling `pulse_uicomponent` on a handle the court may have destroyed (not
   an error a pcall catches). Only one caller passes a real card (`ICUI.CARD .. "_" .. slot`).
6. **`IC.may_send_diplomats`** breaks out of the `factions_met()` scan on a match.

## 4. Verified, and how

- Harness `_iron_court_harness.lua`: 861 checks, green. New or changed: "a fifth rising wakes a
  dead house rather than joining a running one" (new), the join check now under
  `every_faction_risen()`, the three souring checks assert both directions and two penalties a
  step, the confirm check stubs a findable panel and adds a court-shut-before-the-stop case, the
  edict check adds an engine-locked button that must survive the relight.
- Mutants: 994 anchored. The 24 touched by this pass (five re-aimed, six new) and all 22 edict
  mutants (two new) caught. The full run was NOT repeated.
- luac, `check_lua_api`, `check_lua_literal_left`, `check_lua_undeclared` clean;
  `gen_iron_court --selftest` ok; `import_iron_court.py` gate green.
- The deployed pack was read back with `read_pack_index.read` and every fix's marker string
  found in it (24F2E575 round; DE2E446C is the deploy tool's byte-compare of the same build
  plus the edict change).

## 5. Found the hard way

- **The harness's regard model was symmetric** (`pair_key`, "in either direction"), which is why
  a read of one side and a write of the other passed every check. `standing_of(a, b)` is now
  a's regard for b, moved by bonuses whose SECOND argument is a. `pair_key` is deleted.
- **Run `mutate_iron_court.py` from the workspace root.** From `tools/` the harness cannot
  resolve its paths and the runner reports "the harness itself - not green before anything was
  broken", which looks like a broken harness and is not.
- **A full pool no longer reaches the join fallback** while any house is dead, and the harness's
  `cm:get_faction` answers every ORIGINS house as present and dead unless `rebel_alive` says
  otherwise. So any check about JOINING a rising must call `every_faction_risen()`; one that
  only filled the pool let the "seceding court itself" mutant survive.
- **`read_pack_index.read(path, substring)` takes a path, not a file object, and returns
  `(path, compression, bytes)` triples.**
- The game was started mid-pass; `deploy_iron_court.py` then builds into Modpacks only. Use
  `--deploy-only --wait` in the background rather than leaving it.

## 6. Do not re-derive

- `is_rebel` factions (`wh3_dlc23_chd_chaos_dwarfs_rebels`) do not exist on the campaign map:
  `cm:get_faction` answers false (`HANDOFF_20260917_IRON_COURT_SECESSION_CRASH.md` 2a). A
  rising can only use a faction already on the map.
- Vanilla's Chaos Dwarf factions (db.pack, read with `read_vanilla_db.py`): astragoth,
  `wh3_dlc23_chd_chaos_dwarfs`, qb1-3, rebels (is_rebel), conclave, legion_of_azgorh,
  minor_faction, zhatan, dlc25 invasion. **`wh3_dlc23_chd_chaos_dwarfs` is the one dormant
  faction not used by the court** - whether it is on the map is unprobed (game was up only
  after the code was done). It was deliberately not added: it has no crest/name override and
  `gen_iron_court.check_factions` and `make_ic_rebel_flags.py` both hold REBEL_POOL to exactly
  the four overridden rows.
- All of those factions permit all seven `IC.REBEL_GENERALS` as `general`
  (`faction_agent_permitted_subtypes`).
- `ICUI.SOUNDS` other ten names, and `SOUND_OK`/`SOUND_BAD`/`UI_CLICK_Begin_Ritual`/
  `UI_CLICK_Cancel_Decline`, are all in the registry.

## 7. Still open

- In game: a party rising under a house that is not its own (name, crest, war, court); the
  three new sounds; an edict the engine locks itself in a governed province (does it reuse the
  button id the court greyed elsewhere?); everything in the governors handoff sections 6 and 13.
- `IC.rebel_faction` may wake a house whose own party is seated in some court; if that party
  later secedes it joins the unrelated rising under its own faction. Accepted, not handled.
- The author may want only one direction of souring - say so in the reply, it is one line.
- Push to GitHub (two builds behind).
- Not done here, still on the earlier lists: Workshop entry and refreshed patch notes, the
  Ambition / Military Doctrine handoffs, Black Kraken's unexplained party change.

## 8. The Governors column drawn whole (2026-10-02, later)

Build `9A66C3C8`, deployed to data/ (backup `.bak_pre_auto_20261002_103700` holds `DE2E446C`),
not pushed. The author: "check the updated custom ui and how scrollable list should work, apply
it in the iron court mod". `docs/CUSTOM_UI.md` "Drawn whole" (confirmed in game on the Exchange
the same day) names the court's column as the last windowed list.

- **What changed** (`zzz_derpy_iron_court_ui_map.lua`): `ICUI.gm_list` also creates a holder
  `ic_gm_rows` (from `derpy_ic_gm_sp`, the empty one-component file) straight into `list_clip`,
  at the window's top, `max(GM_ROWS, n) * pitch` tall. `gm_make_rows` makes a card for EVERY
  entry under it, at its own index, placed once when made. `gm_follow` moves the holder to
  `list_box`'s y; `gm_scroll_poll` (now 16ms, registered once) only follows and never
  redraws. `ICUI.gm_scroll` is gone: a click names the entry directly, and `gm_party` is the
  entry index. `ICUI.close` clears `gm_list_key` so the poll returns at once. `gm_fill_row`
  memoises each card line (`ICUI.gm_drawn`, text plus the line's shift, emptied on every
  rebuild). With no holder the first `GM_ROWS` cards go into the panel unscrolled, as before
  the list.
- **Created, not adopted** - the doc's steps 4 and 8 (Adopt in, hand back before Destroy)
  exist because the Exchange's holder belongs to its panel file. The court's cards exist only
  for the list, so the holder and cards go with each rebuild.
- **Harness 862.** The fake holder's `MoveTo` carries its descendants, as the engine's does,
  so the checks measure where cards ARE (`gm_scrolled`, `gm_on_screen`) instead of a counter.
  New assertions: a scroll causes zero `ICUI.refresh`; a card's line moves with its card; a
  redraw rewrites no unchanged line; a rebuilt list writes every card; backing out of a picker
  the same length as the Provinces page opens it at the top (this one was missing - the
  "picker shares the Provinces page's list" mutant survived until it was added).
- **Mutants: 996**, 111 column mutants all caught. Two deleted with nothing left to aim at
  (the slot offset, and the clamp the engine now does); twelve re-aimed; four new (holder one
  screen tall, one screen of cards, no memo, memo kept across a rebuild).
- Gates: gen_ic_ui `--check` / `--selftest` (24 files, 628 components, 2529 guids), preview
  `--check`, luac, API, literal-left, undeclared clean.
- **Owed in game:** the wheel and the slider move every card smoothly (and the wheel over a
  card reaches the list through the holder - not yet confirmed even on the Exchange); a click
  on a scrolled card picks that entry; a large picker (many characters) opens without a hitch,
  since every card is made at once.

## 9. Pushed

Pushed to GitHub on 2026-10-02 as 343c5fa (builds 3FBD2B1A, DE2E446C and 9A66C3C8 together),
with CHANGELOG entries for all three and DEVELOPMENT.md at 862 checks and 996 mutants. This
handoff was added to `sync_iron_court_repo.py`'s history list.
