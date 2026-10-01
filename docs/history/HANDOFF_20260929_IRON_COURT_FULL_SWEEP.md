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

## 8. The grace period (evening, build D3712F85)

Asked for after the Rome 2 comparison: "Grace periods for 10 turns". Designed in chat and approved
("Yes, build it", which the author chose over "Yes, but allow Provoke").

- `IC.TUNE.grace_turns = 10`, a fixed value, NOT an MCT setting and NOT in `TUNE_ORDER` (so no save
  string changes). `IC.grace_left()` is the turns left counting this one: 10 on turn 1, 1 on turn
  10, 0 from turn 11. `IC.secession_on()` is the switch AND no grace.
- **One gate for the floor.** `IC.at_breaking_point` now returns false unless `secession_on()`, so
  every caller agrees: `tick_secession`, the Secure Loyalty refusal, the Court summary and the oath
  tooltip. Side effect, deliberate: with secession switched off, Secure Loyalty is no longer refused
  at 0 loyalty and the tooltip no longer says they leave next turn (both were wrong before).
- `tick_secession` and `splinter` take the off path in grace (clocks and split counts zeroed, no
  card); `tick_pressure` presses nobody. Plots, demands, feuds, offers and purges run as normal.
- **Provoke is refused** in grace, in `IC.may_target` (why = `"grace"`), which both `can_plot` and the
  Court card's `act_check` already ask - and only the player ever reaches Provoke. With secession
  switched OFF it stays the loyalty cost it always was. `IC.plot`'s Provoke branch is unchanged: a
  first pass gated it and changed the no-secession text, both reverted once the refusal was in.
- Panel: no SECEDES / SPLITS / SPLINTERING in grace (`ICUI.mood`), nobody in the summary's leaving
  list, and the Court tab's line reads "The court is protected: no party can break with you for N
  more turns." (not with the switch off; sufferance still outranks it).
- **The harness sets `grace_turns = 0` where it loads the model**: nearly every check runs on turn
  1. The three grace checks set it to 10 through `in_grace()`. A new secession check that forgets
  this is testing nothing on turns 1-10.
- 789 checks; mutants: 810 (21 grace ones, 11 stale anchors retargeted onto the new gate lines).
- **Deployed** to data/ at 19:19, 9,500,274 bytes, byte-identical to the build; backup `derpy_iron_court.pack.bak_pre_auto_20260929_191940` holds B4BC1409. Full mutation run 810 mutants, 0 unexplained; `gen_ic_ui.py --selftest` ok. Not pushed, not seen in game.

## 9. The party map, Phase 0 (night, build A06C68A6)

Plan `docs/superpowers/plans/2026-09-29-iron-court-party-map.md`, Task 1 only, executed inline
("go native"). Task 1 is the spec's Phase 0 probe built as a real slice: a **Map** tab that closes
the court, hides the HUD and pins one party-coloured disc with the governor's party name to every
province capital you hold, through CA's Gardens of Morr callbacks copied verbatim from
`template_black_tower_slot` (`ContextWorldSpaceComponent` on `CcoCampaignSettlement.Position`,
cco id `settlement:cqi()`, and the `ContextOpacitySetter` that fades a marker near the screen top).
A legend in the top-left corner carries the close button. Tasks 2-5 (choosing a party, the marker
click, paging, docs) wait on the author's look.

- New files: `zzz_derpy_iron_court_ui_map.lua` (sorts after `_ui.lua`, so `ICUI` exists),
  `derpy_ic_map.twui.xml` (IC45), `derpy_ic_map_marker.twui.xml` (IC46), 26 generated discs and
  2 rings. Tabs moved: map 750, intrigue 994, petitions 1238, log 1482.
- A marker is ONE component with image layers, no children - the engine ignores offsets on
  runtime children and nothing can `MoveTo` a child of something the engine moves every frame.
- Rulings made while executing (ledger `.superpowers/sdd/2026-09-29-iron-court-party-map/progress.md`):
  `selftest_compact` counts +4 uncompacted files, not +2; the two map layouts got
  `LAYOUT_TABLES` entries; the legend is interactive (so a click on its blank plate does not reach
  the map) and so carries the court's click sound; the harness's tab list names `ic_tab_map`; the
  map's twelve layout numbers are declared never-scaled; the layer is sized through `ICUI.resize`
  (which passes `false` for CA's resize-children default) instead of a raw `Resize`; and
  **`check_lua_undeclared.py` now declares every target of a statement-start multi-assignment**
  (`ICUI.MK_PLATE, ICUI.MK_CREST, ... = 0, 1, ...` read as undeclared), fixed at the root with a
  selftest case watched to fail first.
- Harness 789 -> 792. Deployed 22:04, 1761 files byte-identical in data/ (the prior pack held
  1730; the difference is exactly the 31 new files). Backup `.bak_pre_auto_20260929_220400`.
- **Owed by the author, in game** (the plan's Step 14): load a Chaos Dwarf campaign, open the
  court, click Map. (1) Does each disc sit ON its capital, not beside it? (2) Do the markers stay
  on their settlements while the camera pans and zooms? (3) Do markers fade near the top of the
  screen? (4) Can you still drag the camera and click an army or settlement beside a marker?
  (5) Does the close button bring the court back, and the HUD back after the court closes?
  1 or 2 failing sends the map to the spec's section 10 (schematic in the tab); 1 landing offset
  but tracking is a one-attribute fix (`component_anchor_point`, the plan spells it out).
- **First probe, 2026-09-30 (the author's screenshot and `script_log_290926_2340.txt`)**: no disc
  and no name drew, but the log shows `ic_map_mk_1` clicked at [897,391] and later at [861,634],
  200x84, visible and interactive. So the marker exists and tracks the camera, which was the
  probe's real question, and it is fully transparent. The cause is CA's fade: `self` in CA's
  expressions is the component (2,541 `self.ParentContext` uses), so the fade reads the marker's
  own screen y, and a marker made from Lua starts at the layer's corner, where 0/50 = 0.
  `update_constant` is not a documented `ContextOpacitySetter` property, so nothing reads it again.
  26 of CA's 28 pinned layouts carry no fade. Removed; `check_map` now refuses one (watched to fail
  on the shipped file first). Build **`0982F260`**, 1761 files byte-identical in data/, backup
  `.bak_pre_auto_20260930_083035`. The empty legend and its two captionless pager plates are
  Task 2's, not a fault. Second probe owed: questions 1, 2, 4 and 5 again.
- **Second probe, 2026-09-30 08:58 (`0982F260`)**: the disc draws on the Plain of Zharr, with the
  name on its plate under it. A bridge read of the live layer gives opacity 255, the Tower disc,
  sigil and capital ring, and it tracks the camera. The log has zero SCRIPT ERRORs, and CA's region
  tooltip still shows through beside the legend. No anchor change is needed. Still unreported: a
  camera drag beside a marker, and the HUD coming back after the court closes. Tasks 2-5 may start.

## 10. Civil missions (night, build C334A61D, then CCF16A5E after the final review)

Plan `docs/superpowers/plans/2026-09-29-iron-court-civil-missions.md`, all five tasks, run while
the map probe waits. A fifth Intrigue column, **Missions**, with two moves:

- **Send an Envoy** (120 influence, 80%): pick one of your provinces, then one of four works for
  `mission_turns` = 5 turns - control +6, armaments +20%, raw materials +20%, labourers lost -15%.
  Each is a DB effect bundle (`derpy_ic_envoy_ctl/arm/raw/lab`) applied with
  `cm:apply_effect_bundle_to_faction_province`. The values live ONCE, in `IC.TUNE.envoy_*`;
  `gen_iron_court.py` reads them out of the shipped Lua, so card text and effect cannot disagree.
  The same work in the same province again is refused with its turns left, before the price.
- **Send Diplomats** (100 influence, 75%): pick a faction you have met; +4 on CA's own -6..+6
  diplomatic bonus, and that faction rests for `diplomats_rest` = 5 turns. The rest is the one new
  saved field (field 13 of the court string, `key,turn;...`); a save from before this build loads
  with nobody resting. Dead factions are left off the list.
- A lost province or dead faction at click time is refused `lost`. A failed send pays, applies
  nothing and rests nobody, and logs `plot_key:target` so the Record says where it failed.
- The ten planning rulings stand as written in the plan (refusal `lost`; the Record names the
  party; values in `IC.TUNE`; raw materials keeps its borrowed scope
  `province_to_province_own_unseen` by an exact one-pair exemption in check 2; bundle icons
  checked to exist, new check 4b; the two card icons are CA's veteran overseer and Cathay
  diplomat ancillary art; mission pickers do not sort; dead factions left off; the help page has
  its own Missions line). Execution rulings (ledger
  `.superpowers/sdd/2026-09-29-iron-court-civil-missions/progress.md`): `diplomats` joined
  `LOG_KINDS` in Task 2 beside its sentence, not Task 1; the generator selftest's bundle count
  adds one per envoy task; the two built-pack checks ran after the build.
- **The cards were rewritten to fit five columns.** At 364px cards the text check (20d) failed
  17 of 18 cards, not the few the spec foresaw. Every effect sentence and number is kept; each
  flavour line was cut to one short sentence and three names were shortened. Bribe is
  unchanged. The originals are in the pre-change snapshot
  `.superpowers/sdd/2026-09-29-iron-court-party-map/base/zzz_derpy_iron_court.lua`. For the
  author to review:

  | Move | Was | Now |
  |---|---|---|
  | Discredit | His ore comes up short and his contracts are challenged. His party falls with him. | His ore comes up short. |
  | Spread Rumours | A few paid tongues can ruin one name without starting a feud. | Paid tongues ruin one name. |
  | A Forge Accident | The Tower claims another victim. His party will know who arranged it. | His party will know who arranged it. |
  | Provoke | Give them an insult they cannot ignore, then choose when the reckoning begins. | An insult they cannot ignore. |
  | Purge the House | Erase their name. The court remembers. | The court watches. |
  | Strike Their Seats | Strip every title from them in one sitting. They keep only their name. | They keep only their name. |
  | Recall Their Governors -> **Recall Governors** | Call their overseers home. The provinces answer to the Tower again. | The Tower takes back its provinces. |
  | Blood-Oath on the Anvil -> **Blood-Oath** | Score two names into hot iron. They must trust you before they swear. | Two names in hot iron. |
  | Stand His Patron | Put your name behind his and an office within reach. He will remember. | He will remember. |
  | Name Him Kinsman | Take him under your standard. His party loses influence. | His party loses influence. |
  | Pledge of the Forge | Promise them the next work of the forge. | Forge-sworn. |
  | Embezzle from the Vaults -> **Embezzle** | The ledgers will balance before the audit. The court will still smell theft. | The court will still smell theft. |
  | A Feast of Ash | Labourers, fire, and a long feast. The court learns his name. | The court learns his name. |
  | Hold the Ash Court | Hear every grievance through a day of smoke. The court leaves less bitter. | A day of smoke and grievances. |
  | Ride the Circuit | Inspect the provinces with a ledger and an armed escort. Order improves. | A ledger and an armed escort. |

- Harness 792 -> 804 (twelve checks, each watched to fail first). Mutants 810 -> 833 (23
  missions mutants); the filtered run found one stale anchor on an OLD mutant (the plot click's
  `if` became an `elseif`), retargeted, caught. Full run: 833 mutants, 0 unexplained after a second stale anchor on an old mutant (the failed-plot log call, split for the mission key) was retargeted and caught.
- **Five looks only the game can answer** (spec section 8): (1) the bundle shows in the province's
  effects with its turns; (2) the control breakdown's label - if it names an edict, the control
  row moves to `wh_main_effect_public_order_faction` and its bundle to the governor's faction
  target; (3) armaments and raw materials move (raw materials rides the borrowed scope); (4) the
  labour figure moves; (5) the diplomacy screen shows the +4 - on THEIR attitude towards you.
- **Final review** (one fresh reviewer over both plans' whole diff; every Review Focus item held).
  Two fixes, each with a check watched to fail first, deployed as **CCF16A5E** (23:34, backup
  `.bak_pre_auto_20260929_233414` holds C334A61D, which never left data/):
  - **The Diplomats bonus was the wrong way round.** The spec wrote
    `apply_dilemma_diplomatic_bonus(target, player, n)`. CA's doc names the arguments only "first"
    and "second", but all five of CA's calls put the one who ACTS first and the faction whose regard
    MOVES second - Neferata's treasury theft is `(neferata, victim, -3)`, the Intrigue at the Court
    slot penalty `(new occupier, displaced, n)`. So the old order moved the player's regard for
    the target and left the target's where it was: 100 influence for nothing. Now
    `(player, target, n)`; inferred from CA's usage, not measured - look 5 above is the check.
  - `check_lua_undeclared.py`'s multi-assignment pattern (section 9) used `\s`, so a target list
    could run down the lines of a table constructor and declare every positional ALL_CAPS read
    before a `key =`. Now `[ \t]`, selftest case added.
  - Deferred: `IC.may_send_diplomats` scans `factions_met()` to the end, once per met faction.
  - **Open, not this plan's code:** `IC.rebel_sour` calls the bonus as `(rebels, other, step)`. By
    CA's order that moves OTHER's regard for the rebels, while its loop stops on the REBELS'
    `diplomatic_standing_with(other)` - if the two disagree, every souring runs all its steps.
    Which direction the secession meant is the author's call.
- **Pushed** to GitHub on 2026-09-29 as c189ff7 (build CCF16A5E), together with D3712F85 and
  A06C68A6. The repo README, DEVELOPMENT.md (804 checks, 833 mutants, thirteen save sections)
  and CHANGELOG were updated with it.
