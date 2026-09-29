# The Iron Court: full sweep (2026-09-29, afternoon)

Author: "do a full sweep of the iron court mod". Read this after section 19's last addendum
("The four leftovers") of `HANDOFF_20260925_IRON_COURT_MCT_MULTIPLAYER.md`. The starting build is
16E76FC3 (deployed 15:05).

**RESULT: build `B4BC14091DDAF79F835B5796FE46F8CB`, 9,498,698 bytes, 1,730 files, deployed to data/ at 16:50 (backup `derpy_iron_court.pack.bak_pre_auto_20260929_165035` holds 16E76FC3), all 1,709 Lua/XML/PNG byte-identical to `Modding Files/pack/`. Harness 786 checks; full mutation run 798 mutants, 0 unexplained. Pushed to GitHub 2026-09-29 as 260ee76, with 16E76FC3; not seen in game.** Twenty faults fixed (sections 2, 3, 4b and 6); two findings ruled not to fix and two left open (section 7).

## 1. Every gate, run against 16E76FC3's source, before any change

All green. Commands from the workspace root; timings where they matter.

| Gate | Result |
|---|---|
| `lua tools/_iron_court_harness.lua` | ok (775 checks), 2 s |
| `py tools/gen_iron_court.py --check` / `--selftest` | ok - 43 bundles, 56 junctions, 146 traits, 916 loc |
| `py tools/gen_ic_ui.py --check` / `--selftest` | ok - 15 files, 556 components, 2205 GUIDs. **The selftest takes 11 minutes**; run it in the background |
| `py tools/import_iron_court.py` (no flag = verify only, packs nothing) / `--selftest` | ok; verify includes `check_lua_undeclared` |
| `py tools/preview_iron_court.py --check` / `--selftest` | ok, 15 files through TWUI Studio's reader |
| `py tools/make_ic_backdrop.py --check` | ok; worst cell `ic_row_b[6]` at 4.6:1 |
| `py tools/make_ic_rebel_flags.py --selftest` | ok (a Pillow `getdata` deprecation warning, due 2027-10) |
| `py tools/deploy_iron_court.py --selftest`, `py tools/sync_iron_court_repo.py --selftest` | ok |
| `luac -p`, `check_lua_api.py`, `check_lua_literal_left.py` on the four Lua files | clean |
| `check_effect_signs.py` on the pack | 20 of 56 rows read as penalties: the 13 `derpy_ic_vacant_*` and the two control bands, all by design |
| `check_effect_bundle_loc.py` on the pack | 0 findings |
| Duplicate combined keys (`import_house_ancillaries.check_keys` over the 14 tables `deploy_iron_court.TABLES` names, RPFM open) | clean |
| `py tools/mutate_iron_court.py` (full) | 776 mutants, 0 unexplained, ~10 min. Lua files byte-identical afterwards (md5 against a snapshot) |
| Deployed pack vs staged source | `data/` = `Modpacks/` = 16E76FC3; all 1,709 Lua/XML/PNG byte-identical to `Modding Files/pack/`; 0 uppercase paths; nothing staged under the pack's folders left out |
| Plain-words and emoji scan (loc + MCT + Lua strings) | clean: every "standing" is an internal key, comment, or plain English |

`sync_iron_court_repo.py --check` reports 7 files of drift - expected, the repo was last pushed at
1BE494B4. The repo's README still says "public order" at lines 27, 56, 68 (the game says
"control") and DEVELOPMENT.md says 771 checks / 760 mutants. Both are repo-only files.

`data/` holds 37 `derpy_iron_court.pack.bak_*` files, 325 MB (and 44 other `.bak_` files). The game
loads only `*.pack`, so they are clutter, not a fault.

## 2. The script log finding (fixed)

Every launch's script log (`script_log_290926_1244` through `_1335`) carries **24 SCRIPT ERRORs from
the Iron Court**: 8 clicks x 3 errors, at 31-36 s, before the campaign UI exists.
`ic_char_switch` (a `ComponentLClickUp` listener) calls `comp()`, which called `core:get_ui_root()`
on the loading screen: "get_ui_root() called on the core object but the ui has not been created
yet" twice, and "find_single_uicomponent() called but supplied parent [false]" once. CA's
`script_error` logs and does not throw, so nothing broke - but it was the only mod-owned noise in
those logs besides CA's own. Every other SCRIPT ERROR there is CA's (the Conclave faction intro,
a narrative query with a nil faction).

Fix: `comp()` returns nil when it was given no parent and `core:is_ui_created()` is false (CA:
"Useful if client scripts are running so early in the load sequence that the ui may not have been
set up yet"). Harness `core` stub gained `is_ui_created` (reads `core.ui_ready`, default built).

## 3. Five read-only reviewers (the audit's split: model 1-2850, model 2850-end, parties + MCT, UI 1-3700, UI 3700-end)

They read a snapshot in the session scratchpad, not the shipped files, because the mutation run
was writing mutants into those. Their repro scripts are in that scratchpad (gone with it).

### Fixed, each with a check watched to fail first and a mutant caught

1. **A Crown split kept its men's seats' weight** (model-a #1 = model-b #3). `appoint` credits the
   party a man answers to at seating, `dismiss` debits the one he answers to at unseating, and
   `IC.splinter` is the one thing that moves a seated man between them. Measured: Crown 101 where
   95 was right. Fix: `splinter` moves each such seat's `office_weight` from the Crown to the new
   party. Check: "a seat a split carries into the new party carries its weight with it" (round
   trip: seat, split, unseat).
2. **`IC.remove_house` left the office title trait on a man it unseated** (purge, or a secession's
   stayer). Fix: `force_remove_trait(office_trait)` in its seat loop, as `dismiss` does.
3. **`IC.release_governor` logged `gov_off` before its guard**, so a release of an ungoverned
   province (two queued clicks, a recall at a gone governor) saved a phantom Record line. Log moved
   below the guard.
4. The script-log fix of section 2.

Harness 779 after these; the five new mutants (4 model, 1 UI) all caught.

### Checks written, fixes NOT yet applied (the harness currently fails on these on purpose)

From UI 1-3700 (all verified in the code):
- **mood / court_state read the count before the breaking point.** The model's `tick_secession`
  tests the breaking point first, so a counting party that falls to `secede_break` (a Provoke:
  -25 and a count of 3) leaves next turn while its card says SECEDES 3. Fix: in `ICUI.mood` move
  the breaking-point branch above the clock; in `ICUI.court_state` test breaking first.
- **card_mood hides SECEDES 1 behind the party's business** (only `clock > 0` returned early).
  Fix: return early when the word matches `^SECEDES` (string.match, not find).
- **The pager caption never reaches the last page**: `scroll_by` clamps to `total - page`, so
  2n+1 rows run 0, n, n+1 and read 1, 2, 2 of 3. Fix in `draw_pager`:
  `page = (at >= ICUI.max_scroll(total, n)) and pages or math.floor(at / n) + 1`.
- **PLOTTING drawn where nobody can act.** Hard-coded `<= 25` and no `parties_act` gate; the
  Custom `party_intrigue_line` slider goes down to 20 and the intrigue act refuses above it.
  Ruling taken here: gate only PLOTTING (`parties_act ~= false` and `<= math.min(25, line)`);
  RESTLESS is a mood and stays.

## 4. Do not re-derive

- `import_iron_court.py` with no flag verifies and prints the plan; it packs nothing.
  `deploy_iron_court.py` builds (RPFM open) and deploys when the game is shut.
- The harness writes no files. A mutation run touches only the four shipped Lua files, and its
  `finally` restores them - verified by md5 against a snapshot this session.
- Do not run the harness, the importer's verify or `gen_ic_ui.py` while a mutation run is going:
  they read the shipped Lua, which holds a mutant at that moment.
- `IC.agenda(F)` is cached in `IC.agenda_state`; writing to `IC.agenda(F).offers` in a check
  persists until cleared.
- `secede_break` defaults to 0.

## 4b. Progress since section 5 was written (16:20)

FIXED, each with a check seen failing and a mutant caught (harness 784):
- The four UI items of section 3 (mood/court_state order, card_mood, pager, PLOTTING). Two older
  mutants on `court_state` went stale (the `elseif` became `if`) and were retargeted.
- Section 5 item 1 (HIGH): `stamp_incoming` swaps an AI court's rolled origin trait for the
  arriving hall's unless the man has a fixed history, and counts a man who already had it.
- Item 4: the murder card prints `plot_murder_loyalty - loyalty_member_died` (38).
- Item 6: `party_strike` reads the odds before the price. The two feud-murder checks had been
  built around pay-first ("once he has paid he stands level"); their fixture now has both men
  at 1000 before the price and the paid assertions subtract the cost.
- Items 7 and 8: `expire_offers` also drops an offer `can_accept_offer` calls "gone";
  `refuse_demand` lets the `"refused"` state fall through to a successful refusal.
- From the fifth reviewer (UI 3700-end): (a) loc lookups inside turn handlers -
  `ic_opener_place` (every faction's turn start) wrote the button tooltip when the button moved,
  and `ic_turn_end` did through `close()`. Now `place_opener(attempt, quiet)` and `close(quiet)`;
  both turn listeners pass `true`; `ic_opener_tip` still writes it one tick into the player's
  turn. Not deferred, because a deferred close would run `update_opener_tip` -> `gate_opener`
  after the between-turns grey. (b) `plot_party` returns nil for a Crown result (a landed purge
  burst the player's own card). (c) `ICUI.news_text` names a confederate party by its hall
  (`news_party`).

STILL OPEN from the fifth reviewer: the edict relight restores every `inactive` edict, not only
the ones it greyed (one global `edicts_greyed` flag; untested whether the game locks an edict in
a fully held province); and in multiplayer an answer arriving after the panel closed still sets
`ICUI.notice` / clears `ICUI.pick` (reasoning only; suggested: `after_op` returns once `waiting`
is cleared when the panel is gone). Also noted, not in its slice: `ICUI.confirm` reuses a card
handle 1.5 s later (inside a pcall).

## 5. Still open (as first written; see 4b for what has since been fixed)

Verify each in the code before fixing; the reviewers' severity is theirs.

From model 2850-end:
1. **HIGH - `IC.stamp_incoming` never adds a confederate house when the absorbed faction is an AI
   Chaos Dwarf court that has run a turn**: it counts a man only when `stamp_origin` returns true,
   which refuses a man who already wears an origin trait, and every AI court stamps its men at
   turn start. Suggested fix: count every man not in `before`, swapping his origin trait for
   `derpy_ic_house_<slug>` when he has no fixed history (`prune_confed` keys on that trait).
2. MEDIUM - two secessions in one turn both wake the same dormant rebel faction (the spawn lands
   after the frame, so `rebel_faction` still reads the first as dead). Suggested: an
   `IC.waking_now[rebels]` mark that `rebel_faction` treats as alive, cleared in the final step.
3. LOW - `IC.turn` applies the control bundle before `party_turn` / `tick_secession` /
   `splinter` change weights; same gap in `ic_dead` and the secession's final step.
4. LOW - the murder card promises -30 loyalty, the party loses 38 (`loyalty_member_died` -8 on
   top, deliberately charged; only the printed number is wrong).
5. LOW, reasoning only - `IC.rebel_sour` passes a faction interface to `diplomatic_standing_with`;
   `docs/MOD_RESOURCES.md` records CA passing a key. Check `--explain` before touching.

From parties + MCT (MCT came out clean):
6. MEDIUM - `IC.party_strike` pays the price before reading the edge, so every party plot rolls at
   worse odds than the player's (unseat 50% -> 28%, murder 40% -> 15%; a feud murder hits the 5%
   floor). `IC.plot` reads the odds first since 2026-09-25.
7. LOW - `IC.expire_offers` drops an offer only when its maker has gone, never its target: a calm
   offer on a party that then secedes stays listed, pulses the button and blocks the maker's next
   offer for up to 3 turns.
8. LOW - `IC.refuse_demand` in the `"refused"` state charges the refusal and then returns
   `false, "gone"`, so the panel says the demand was no longer open.

The fifth reviewer (UI 3700-end) had not reported when this was written.

After the fixes: full harness, full mutation run (watch for stale anchors on the moved lines), both
generators' `--check`, the importer's verify, then `py tools/deploy_iron_court.py` (the game was
shut all session) and a byte check of the deployed Lua. Not pushed; the repo README/DEVELOPMENT.md
items in section 1 go with the next push.

## 6. Closing the sweep (16:20-16:50)

Also fixed after 4b, each with a check seen failing and a mutant caught:
- **`IC.rebel_sour` passed a faction interface to `diplomatic_standing_with`.** CA passes a KEY
  (`wh3_campaign_caravans_core.lua`: `self_faction` is handed to `cm:get_faction` two lines
  earlier), and `docs/MOD_RESOURCES.md` already said so. The harness stub asserted an interface
  and its comment misread CA's code - the "convenient stub" trap. Stub now demands a key; the
  existing souring check then failed (30 steps where 25 reach the target) until the model passed
  `other`.
- **`IC.turn` put the control band on before the parties' turn, `tick_secession` and `splinter`.**
  Now applied again last, after `stamp_members`. The first check passed with the bug present:
  `IC.share` counts members as well as house weight, so setting the Crown's weight to 1 moved no
  band. The check's splinter wrapper now swamps every rival instead.
- **Multiplayer: an answer arriving after the court shut wrote its notice for the next open.**
  `after_op` returns once `waiting` is cleared when the panel is gone. The older "picker waits for
  the answer" check had a picker open with no panel (impossible in game) and was moved under
  `with_fake_panel`; the "other machine draws nothing" check likewise, or the new guard masked
  its sender test (the one survivor of the first post-fix run).
- `expire_offers` lost its `not court.houses[slug]` test: `can_accept_offer` answers "gone" for a
  missing maker, so it was redundant and its mutant equivalent. The two offer mutants merged.

Mutation bookkeeping: twelve older mutants went stale on lines this sweep rewrote; all retargeted
and caught. Run history: 776 (baseline, clean) -> 799 with 13 unexplained (12 stale + 1 survivor)
-> 798, 0 unexplained.

## 7. Ruled on, not fixed

- **Two secessions in one turn waking the same dormant faction** (model-b #2): NOT REAL as far as
  the evidence goes. Step 1 of a secession (`steps[1]`, run synchronously by `secede_step`) spawns
  the first army, and the harness stub records a measurement that the faction flips
  `dead=true -> dead=false` on that `create_force_with_general` call - so the second secession
  sees it alive and wakes the next pool faction. The reviewer assumed the flip lands after the
  frame. If a live log ever shows two "took the throne" lines for one faction in one turn, this
  is wrong.
- **A confederate party's purge bursting a rival card** (the tail of UI-b #3): the Crown case is
  fixed; a purged CONFEDERATE party's men fall back to their background party, which is a real
  card, and it bursts. Rare and cosmetic; left.

Still OPEN, needs an in-game look:
- **The edict relight** lights every `inactive` edict button in a wholly held, governed province
  once `ICUI.edicts_greyed` was set by an earlier ungoverned selection, not only the buttons it
  greyed. Harmful only if the engine itself marks an edict `inactive` there (a pending edict, a
  locked commandment); CA's scripts show no such lock either way. Test: select an ungoverned
  province, then a governed one with an edict pending or unavailable, and see whether it lights.
- `ICUI.confirm` reuses a card handle 1.5 s later (inside a pcall; noted by the UI reviewer, not
  in its slice).
- (Closed at the push: the repo README's three "public order" lines now say control, and
  DEVELOPMENT.md reads 786 checks and 798 mutants. The sync manifest now lists this handoff.)
