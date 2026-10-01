# Iron Court Governors on the live map - Tasks 1-7, build 780A41C5 (2026-09-30)

Plan `docs/superpowers/plans/2026-09-30-iron-court-governors-map.md`, spec
`docs/superpowers/specs/2026-09-30-iron-court-governors-map-design.md`, ledger
`.superpowers/sdd/2026-09-30-iron-court-governors-map/progress.md` (every ruling, every gate
figure, and the author's four in-game looks are there). Build `780A41C5`, MD5 `780a41c5e6826840a6e261564ecc2313`, deployed byte-identical to data/ (backup `.bak_pre_auto_20261001_082030`). The fix pass built `AE791478`; `780A41C5` adds
the cleanup in section 2. It supersedes the party map (`HANDOFF_20260930_IRON_COURT_PARTY_MAP.md`):
its Map tab, layer and legend are gone.

## 1. What the Governors view does now

- **The tab opens onto the live map.** On Governors the court clears its backdrop and stops
  taking clicks, so the campaign map shows through and the camera drags, edge-scrolls, zooms and
  answers its keys with the court open. Every other tab, Help, close, the turn ending and a
  selection through the court put the backdrop back or close the court.
- **Every held province wears a pin** on its settlement: CA's Chaos Dwarf map pin, ringed in the
  governor's party colour (and in gold on the capital), his portrait masked round in its head or
  his party's crest, his party's flag on the head's corner, and two of CA's plates under it - the
  province's name washed in the party colour, and "Loyalty N%". Its tooltip names the province,
  the governor and his rank, "+N weight from this province (L settlement levels), P% of the court"
  (with ", growing to +M" while he earns it), the loyalty, any party it would go with, and what a
  click does. A click opens the governor picker in the column.
- **The column** on the left, CA's Hell-Forge side panel, has two round toggles:
  - **Parties**: each party with what it governs and would take; choosing one rings in red the
    provinces it would take if it walked out, and the hint says why a party rings nothing (the
    Crown, the quiet start, secession off).
  - **Provinces**: one card per province - face or silhouette, name, governor ("(away)" when he
    is), CA's loyalty icon, "L%, +N weight" (or "+n of N weight" while growing). Sorts by
    Province, Governor and Loyalty; pages past seven; choosing one rings its pin and moves the
    camera to it; the check opens its picker, the cross releases its governor.
  - **Candidates** (the picker, in the column, over the map): the court's own governor picker as
    cards; a man the court would refuse is drawn inactive with the refusal first on his tooltip
    and a refusal sound on the click; the check appoints the chosen man, the cross goes back.
- **Weight from a developed province**: a governorship gives its party max(1, ceil(levels / 2)),
  earned one step a turn from nothing (`IC.gov_grown_weight`, `IC.grow_governors`); an older
  save's governors count in full.
- **Also this session**: on turn 1 a leaderless party gets a lord in the recruitment pool, not an
  army, and a lord hired into a party holding one starts at the court's recruit rank; Make Peace
  fits its button and has its own tooltip; Escape closes the court first; the Help has a line on
  the map.

## 2. Found while executing (not in the plan)

- **The column row's party badge drew under its face in game.** `_gm_row` declared the row's cells
  in sorted order, so `ic_gr_badge` and `ic_gr_crest` came before the opaque `ic_gr_face`. Nothing
  in the harness can see draw order; the preview drew it only once it walked the file's order.
  `check_gm_plates` now refuses a crest or badge declared before the face (seen failing on the
  shipped file at 1600 and 2560), and the row is declared in `GM_ROW_LAYOUT`'s own order.
- **Every preview picture had the Help card under it, and the Fill button on every tab.** The
  preview never mirrored `ICUI.refresh`'s two gates for them; the Governors picture's map
  stand-in is what showed it. The preview now reads both conditions off the Lua and refuses to
  draw if they change.
- **A test-order leak**: the prefs check left `ICUI.prefs_loaded` nil, so the next `open()`
  anywhere reloaded a saved "court" over the view its check had set. The deleted "Map tab opens
  the party map" check had been that next open and hid it for weeks.
- **Four mutants aimed at the old Governors list became equivalent** once the list went (its
  vacant plate, `HEADERS.govs`, and the row rim): nothing in the court's row pool sets
  `line.vacant` or `line.rim` any more. Deleted and ruled.
- **The cleanup (2026-10-01, at the author's word, build `780A41C5`).** The dead code those
  four were aimed at is removed: the list row's rim (`ICUI.RIMS.row`, `ICUI.RIM_ART_ROW`, the
  row file's two rim layers, `seat_rim_row.png` - the generator prunes it), `fill_rows`'s
  empty-seat branch, and `ICUI.HEADERS.govs`, whose strip the Governors view hides anyway.
  The tab-switch check that pinned that header now asserts the strip is not drawn there; one
  mutant re-aimed (`set_rim` names `ICUI.RIM_ART` directly); all 309 panel-Lua mutants
  caught; gen --selftest 2531 guids (8 fewer: the two rim layers).
- **Final review: every Governors refresh froze a large realm.** `ICUI.map_tip` asked
  `IC.defecting_provinces` for every party, on every pin and every Provinces row, and each of
  those walks the whole court through `IC.share`. The reviewer measured 7.1M `has_trait` calls
  (2.1s in pure Lua; in game each is an engine call) per click at 30 provinces, 60 men and 6
  parties. `ICUI.map_memo` now asks once a refresh, `gm_sync` hands it down, and the harness
  proves the count is the same at 2 provinces as at 6 (it was 8 against 24).
- **Final review: the column row's lines crossed its frame.** The third line and the loyalty icon
  sat on the bottom rail at every screen size, and the chosen row's gold edge ran through the
  loyalty and weight figures. The old party map's rail check went with it and had no successor.
  `check_gm_plates` now measures the rails off CA's row art (`GM_ROW_RAIL`, scaled to the row
  top and bottom, fixed at the sides) and the three lines sit inside them at the office card's
  own box heights.

## 3. Rulings

Every `Ruling:` line in the ledger, in the order made, with what it costs if wrong.

1. Setup: Ruling: the workspace is not git, so task-start/task-done cannot cut a BASE or run - the harness is run by hand and each ledger line written by hand; snapshots (`*_before_govmap_t<N>.*` in the session scratchpad) stand in for BASE - cost if wrong: none, the snapshots are the diff base.
2. Task 1: Ruling: two of the plan's turn checks seated their governor by writing court.govs directly, and IC.turn reloads the court from the save, so the governor was gone before the rule ran (they failed on "the fixture lost its governor") - seated them with IC.assign_governor, which saves, as "a reload keeps the governors in the court's shares" does - cost if wrong: none, the model is untouched.
3. Task 1: Ruling: the away-governor check passed before the rule existed (5 levels give 3 under the flat rule too) - gave it a minor settlement at 3, 8 levels, 4 weight - cost if wrong: none.
4. Task 2: Ruling: Task 1's new Help line measured 1298px in a 1244px row at 1600x900 (gen_ic_ui --check, check 20c-help; Task 1's gates never ran --check) - reworded to "one per {levels_per_weight} settlement levels you hold in his province, never less than one", 18 characters shorter, same rule - cost if wrong: none, the harness pins only the {levels_per_weight} token.
5. Task 2: Ruling: the pin check reset IC_TEST_PORTRAITS to nil, and the get_context_value stub indexes it bare - reset to {} as every other portrait check does and IC_TEST_LOC to {} likewise (nil broke the marker cut check after it, which indexes the table; the six existing nil resets are each followed by a fresh assignment) - cost if wrong: none.
6. Task 2: Ruling: TEXT_STYLE["ic_gm_pin"] failed gen_ic_ui's own check (a TEXT_STYLE name must be a layout-table name) - keyed it and the style() call on the component's name, derpy_ic_gm_pin, which LAYOUT_TABLES[GM_PIN_FILE] carries; size and category unchanged (12, body_12) - cost if wrong: none.
7. Task 2: Ruling: "an empty cell says so in words" failed on its only case, the old Governors list's cells - retired with the ten; its successor is Task 4's row check, which asserts "None assigned" on an empty seat - cost if wrong: the empty-seat wording goes unpinned until Task 4.
8. Task 2: Ruling: "every panel, row and card cell has a layout offset" names every PANEL_XY cell and failed on the new ic_gm_pins - added it to the named list - cost if wrong: none.
9. Task 2: Ruling: "a marker cuts a province name too long for it..." indexed IC_TEST_LOC bare and only passed because a retired check put {} back after an earlier check left it nil - gave it its own table - cost if wrong: none.
10. Task 2: Ruling: the row burst on assigning or releasing a governor is not carried to the Governors view (plan table): it was a row-pool effect, the view has no pool row, and ICUI.confirm still plays the sound - cost if wrong: the author misses the flash on an appointment, one line in Task 4's row draw to add back.
11. Task 2: Ruling: gen_ic_ui --selftest's selftest_compact counts the base files that have no compact twin (+4) and failed on the two new ones - +6, with GM_PIN_FILE/GM_FACE_FILE asserted absent from COMPACT_FILES beside the map's - cost if wrong: none.
12. Task 2: Ruling: answer 6 - not the plan's offset_y (CA's values 0.2/6/20/-40 give no unit to reason from) but CA's own map-pin anchor, component_anchor_point="0.50,1.00" (worldroots_forest, dlc27_nor_seafang_overlay), with the pin's point moved to the box's bottom and the plate ABOVE the head; the spec said "under it" - the author's "make it higher" and answer 3 (the plate covered the settlement) override it - cost if wrong: the engine may ignore the attribute on a runtime-made component and pin some other point; the author's next look shows it, and offset_y is the fallback.
13. Task 2: Ruling: the text is centred in the pin's box and moved onto the plate by textyoffset -41 (CA ships negative offsets; textvalign="Top" appears nowhere in CA's 24,000 text blocks) and a name is cut to the plate's inside (GM_NAME_W 126, the 150 box less two 12px caps), through a new optional third argument to ICUI.cut_text - cost if wrong: the text sits off the plate's centre by a few px.
14. Task 2: Ruling: Escape - ICUI.hold_esc/drop_esc, the Great Guilds' GGUI pattern: held on a successful open, released first thing in ICUI.close, the callback clears its mark before closing; the held mark records whether the steal SUCCEEDED (the harness caught a mark set ahead of a failed steal refusing every later one) - cost if wrong: none; Escape with a picker open closes the whole court, as the author asked.
15. Task 2: Ruling: the pin-cut check's name cut the same at the plate's 126 and the pin's 150, so 'a pin's name cut to the whole pin' and 'a cut that ignores the room' survived - the fixture name now breaks between the two widths ("The Ash Plain...", 128px) - cost if wrong: none. Mutants: 6 new + 3 re-aimed ('a hold set before the panel...', 'a court that closes and leaves the feed held forever', 'a pin's long name not cut'), all caught; selftest 907 anchored.
16. Task 2: Ruling: textyoffset is (top, bottom) PADDING, not a shift - CA sets both figures in 2,236 text blocks ("4.00,8.00", "0.00,12.00") and our "-41.00,0.00" was clamped to nothing (the two lines drew centred on the whole box, over the face); the pin's text is now centred below a top padding of the plate's top edge, and check_gm reads it off the emitted file - cost if wrong: the text misses the plate again, visible on the next look.
17. Task 2: Ruling: "make the portrait on top" - the pin and its face back above the plate (build 1's order), the plate's bottom edge the anchored edge (0.50,1.00), so the whole pin stands above its settlement and covers none of it; the plate 56 tall (two lines need ~36 of its ~32px dark face at 44) and the pin 180 wide, GM_NAME_W 156, so "The Plain of Zharr" is no longer cut - cost if wrong: a wider pin crowds neighbouring settlements when zoomed out.
18. Task 2: Ruling: gradual governorship weight - IC.TUNE.gov_weight_per_turn = 1; a NEW governor starts at 0 and IC.grow_governors (IC.turn, after tick_provinces) adds a step a turn up to what his province is worth; the sitting man reappointed keeps his growth; a replacement starts again; a province that loses levels loses the weight at once (both grow and the sum clamp), one that gains levels is climbed a step a turn; saved as "province,cqi,grown" - cost if wrong: a swap of governors now costs the party its whole governorship weight for several turns, which is the point, but may feel slow on a rich province (worth 6 takes 6 turns).
19. Task 2: Ruling: an older save's governors (no third field) count IN FULL, not from 0 - they have served, and an update must not strip every party's governorship weight in one turn and fire secessions off the drop - cost if wrong: an old save's parties keep weight a new game would make them earn.
20. Task 2: Ruling: AI courts grow like the player's ("an AI court's governorship follows its levels" renamed and now expects one step) - the rule is the court's, not the player's - cost if wrong: AI parties' governorship weight lags the player's reading of the map by a few turns.
21. Task 2: Ruling: 'the same weight on turn twenty' now grows its one-village province for a turn before measuring and compares to 1e-9 - after a turn the man's standing has decayed to 15.9 and 26.9 - 15.9 is 10.999999999999998 in a double; the release half the same - cost if wrong: none, the fixture-governs-nothing guard still stops a constant.
22. Task 2: Ruling: the pin's text moves onto two plates of their own - derpy_ic_gm_name (IC49, 180x94) and derpy_ic_gm_loyal (IC50, 113x30), non-interactive, made after the pin and face on the same settlement context, anchored 0.50,1.00; each is one line centred with NO padding, because the third build's top padding drew the text above its plate (centred on the whole box) and cut every name however short; the name box is as far below its plate as above it (plate at 32-62) so centred text lands on the plate, and its bottom 32px are the loyalty plate's - cost if wrong: the name draws a few px off its plate's middle, visible on the next look.
23. Task 2: Ruling: "use the default borders" read as CA's sub_title.png at its native 30px height, only its middle stretched sideways between the 12px caps; the loyalty plate is the art at its native 113x30, whole - cost if wrong: the author meant a different CA frame, and a plate swap is one constant.
24. Task 2: Ruling: "the map doesnt show the political influence colors of each party" - no script call tints a map region (CA's docs and 7,540 scripts searched: highlight_* only, no colour), and the spec's section 8 put region tinting out of scope; the party's colour goes on the name plate's dark face (x 5..175, rows 4-22 of the plate) as gm_wash_<slug>.png, one per party and absorbed faction, none on an empty seat - cost if wrong: the author wanted the provinces themselves coloured, which the engine does not offer to script.
25. Task 2: Ruling: each wash is the party's hue darkened until the plate's ink keeps 4.5:1 by make_ic_backdrop's own measure (Rec.709 on stored values, ground luminance <= 44), checked on the generated pixels for all 25 colours - brass and gold read as bronze-brown, grey as dark grey - cost if wrong: the paler parties are harder to tell apart on the plate than on the ring.
26. Task 2: Ruling: GM_PIN_H 146 = pin art 84 + the name plate's top 62 above the point, so the pin's tip ends where the name plate begins; the pin carries no text and check_gm refuses one that does - cost if wrong: none.
27. Aside: Ruling: on turn 1 a player's leaderless party gets a pool lord, never the field (now > 1 on the field branch), and that pool lord spends the party's one field gift (house.fielded = 1), so no army follows him on turn 2 while he waits and a later leaderless spell is the pool's too - cost if wrong: a party whose turn-1 lord is never hired waits on the pool for good, which is the AI's rule already.
28. Aside: Ruling: a lord hired (CharacterRecruited, 0.5s later so an engine rank lands first) into a party with a lord in store is raised to AT LEAST 1 + IC.recruit_rank at the region he stands in; a man already there, a hero, and a hire for a party storing nobody are left alone - because the engine's rank for a script-pooled lord hired by the player is unmeasured (the 2026-09-25 measure covered create_force_with_general only) - cost if wrong: if the engine applies its rank AFTER 0.5s, such a lord lands up to twice the bonus above rank 1.
29. Task 2: Ruling: MAKE PEACE - ic_row_f 110 -> 156 at x 1520 (the 1600 box needed 156: 'Make Peace' 111px on 109), the petitions' column two 860 -> 830; the four petition labels move into ICUI.PETITION_BTN and new check 20k measures each against the button PETITION_BTN_CELL puts it on (it failed first at 110 and at 150); the second button gets its own line.tip2 - the feud's peace price - because the demand row's first tip is why ACCEPT is refused, which REFUSE must not wear - cost if wrong: the petition sentence loses 30px before it clips.
30. Task 2: Ruling: the party flag on the pin - a fifth component, derpy_ic_gm_badge (IC51): the pin's box, one crest image at the head's lower right (GM_BADGE_BOX), made after the face because the face's mask would cut it round; ICUI.crest(slug) or nothing on an empty seat - cost if wrong: a 26px crest is small at far zoom; the Parties page legend (Task 3) names it.
31. Task 3: Ruling: the column row's files take IC52/IC53, not the plan's IC49/IC50 - Task 2's redesign gave IC49-IC51 to the name plate, loyalty plate and badge - cost if wrong: none, check 1 refuses any collision.
32. Task 3: Ruling: ic_gr_l1 at (16, "header_16"), not the plan's (16, "body_16") - COMPACT_FONTS has no body_16 step, so at_box(1600)'s _font() would raise KeyError and no compact file could be built; header_16 is the court's card-line face and steps to header_14 - cost if wrong: the name line wears the header face rather than the body face.
33. Task 3: Ruling: the fixture's row maker checks ICUI.PATH_GM_ROW before comparing paths - during RED, ICUI.path(nil) == nil matched any pathless CreateComponent and reached pairs(nil), which would have failed unrelated checks - cost if wrong: none.
34. Task 3: Ruling: "the column shows on the Governors view only" asserts the always-shown cells visible, not every GM_KEYS name - the plan's own Lua hides ic_gm_hint on the Provinces page and the pager on one page, so the plan's check could never pass; both hides have their own checks (Parties page, paging) - cost if wrong: none.
35. Task 3: Ruling: "every panel, row and card cell has a layout offset" gains the twelve ic_gm_* cells, typed by name as its comment requires (a plan gap: it refused PANEL_XY's new names) - cost if wrong: none.
36. Task 3: Ruling: check_gm_plates' selftest negative uses the plan's fallback (700, 600) - (16, 1040) lands inside ic_gm_foot and reports nothing - plus a second negative, a 300px column, so the pool rule is seen firing too - cost if wrong: none.
37. Task 3: Ruling: the survivor "the column's rows placed at the screen's corner, not the box's" (the plan's predicted one) - the text-on-plate check now runs at 2560x1080 (OX 320) as well AND walks the Parties page, asserting a row drew there: in Task 3 the Provinces page lists nothing, so at 2560 alone the rows were all hidden and the check still could not see them - cost if wrong: none.
38. Task 4: Ruling: the weight on the pin's tooltip and the Provinces row is what the province adds NOW, IC.gov_grown_weight, not the plan's IC.gov_weight_of - Task 2 made a governorship earned a step a turn after the plan was written; while it grows the tooltip adds ", growing to +N" inside its parenthesis and the row reads "+n of N weight"; a governorship grown in full, or an older save's, reads exactly the plan's strings - cost if wrong: two longer lines while a governor is new.
39. Task 4: Ruling: ICUI.GM_SORTS joins ICUI.NOT_SCALED (a plan gap: "every layout number in ICUI is classified" refused it) - it holds labels and column numbers, not geometry - cost if wrong: none.
40. Task 4: Ruling: with_fake_govmap sets ICUI.gm_was_on = false - each call builds a new panel, which is a court opened afresh, but no check closes its court, so the last check's choice (gm_sel) carried into the next and "the check opens the governor picker" clicked its own row off; product code unchanged, the game always closes the court (ICUI.close's wrap) before it opens again - cost if wrong: a real open-without-close path would keep a choice, which no caller has.
41. Task 4: Ruling: two of the plan's mutants dropped as EQUIVALENT - "the cross live for an empty province" (no_shown hides the cross then, so its liveness can neither be seen nor clicked, and gm_no refuses an ungoverned province anyway) and "a disabled check still opens a picker" (with nothing chosen gm_held(faction, nil) is false, so gm_ok returns before the picker either way) - cost if wrong: a later change that shows the cross for an empty province leaves its liveness unguarded.
42. Task 4: Ruling: "a lost province stays chosen" survived because the check button's own guard also clears the choice; the lost-province check now redraws first and asserts the choice and the live check go, then re-chooses to exercise the button's guard - cost if wrong: none.
43. Task 4: Ruling: "the sort lands mid-list after a re-sort" (the plan's predicted survivor) gets its own check - nine provinces, page two, a sort, page one - not the plan's suggested nine-province sorted check, where a descending sort puts Ash on page two and breaks that check's own row-3 assertion - cost if wrong: none.
44. Task 5: Ruling: ICUI.gm_on drops its "ICUI.pick == nil" test (plan ruling 16, applied): on the Governors view every picker is the governor's, drawn in the column, and a tab clears ICUI.pick; the mutant "the Governors view drawn under a picker" deleted, its rule gone - cost if wrong: a non-governor picker opened on this view would draw as the Candidates page; none opens there today.
45. Task 5: Ruling: the text-on-plate check also walks the picker page (via GM_PIN_1) at all three screens, so the cards' text is measured against the column like the other two pages' - cost if wrong: none.
46. Task 5: Ruling: "the chosen province's pin not ringed" re-aimed at gm_ring's new local (page == "provinces") - the line it anchored moved - cost if wrong: none.
47. Task 5: Ruling: two survivors that masked each other - "a refused man choosable" (the redraw's pick_still_free cleared the refused man) now caught by the refused sound, asserted after the busy man's click; "a stale choice drawn as chosen" (gm_ok's own guard caught it) now caught by a redraw before the click asserting the choice and the live check go, then re-choosing so "the check appoints a man no longer free" stays exercised - cost if wrong: none.
48. Task 6: Ruling: map_disc_pixels KEPT, not deleted as the plan lists - Task 2's face ground (GM_FACE_GROUND) is painted with it; its MAP_DISC default goes (size is now required), and MAP_RING stays as map_ring_pixels' default - cost if wrong: none, the generator fails to import on a missing name.
49. Task 6: Ruling: check_map's two pin negatives (no ContextWorldSpaceComponent, CA's fade) moved onto check_gm's pin file rather than deleted - check_gm enforces the same two rules over the five pin files and had no negative for either, so deleting check_map would have left both rules never seen firing; the NO FADE reason (build A06C68A6) moved into check_gm's comment, which had said "see check_map" - cost if wrong: none.
50. Task 6: Ruling: selftest_compact's "+9" becomes "+7" (a plan gap: the two map files were counted there) - cost if wrong: none.
51. Task 6: Ruling: the Help's new Governors line fits by joining two, not dropping one - the topic already held 12 lines (Task 1 added the weight pair after the plan's count), so the seat-loyalty point joins the party-bonus line above it; and the new line is shortened to "The Governors tab opens onto the map. Click a province's pin ..., or pick it in the list and click the check." after 20c-help measured the plan's wording at 1322px in a 1244px row at 1600 - cost if wrong: the party-bonus line is the topic's longest point now.
52. Task 6: Ruling: "a draw that throws puts the error ON SCREEN" stubs ICUI.draw_log on the Record view, not the deleted draw_govs (a plan gap: the table missed it), and asserts "Panel error in log:" - cost if wrong: none.
53. Task 6: Ruling: the multiplayer panel-clicks check loses its release_governor case as the table rules and is renamed "each of the court panel's clicks ..." with a comment naming the check that drives the twelfth (the column's cross) - cost if wrong: none.
54. Task 6: Ruling: the prefs check ("the tab and the sorts survive a reload") now ends with ICUI.prefs_loaded = true - it left nil, so the next ICUI.open() anywhere loaded a saved "court" over the view its check set; the deleted "Map tab opens the party map" had been that next open and hid it, and the replaced pin-tooltip check inherited it and failed; product code unchanged - cost if wrong: none.
55. Task 6: Ruling: sync_iron_court_repo publishes all five pin files (pin, face, name, loyalty, badge) and gm_row with its compact copy, not the plan's two - the plan's list predates Task 2's redesign - cost if wrong: none, the repo is not synced until Task 7.
56. Task 7: Ruling: the preview's pins are drawn as the five siblings Task 2 made them (pin, face, name plate, loyalty plate, badge), each standing its bottom centre on one point, not the plan's single pin with GM_PLATE_BOX text - the plan's Step 3 code predates Task 2's redesign - and the sheet is spaced to the canvas, since pins are never scaled and at 1600 the 1920 spacing ran the fourth off the edge - cost if wrong: none, a picture.
57. Task 7: Ruling: the preview now hides the Help page's cells (ic_help_*) on every picture and ic_fill off the Offices tab, reading ICUI.refresh's own two conditions and refusing to draw if they change - the new selftest's backdrop pixel found the Help card drawn over the Governors map, and it has lain under every other picture since the Help page shipped (pre-existing preview fault; the panel itself was right) - and the footer's plate shows when the demo's footer line does (the demo sits at 16% of the court, under the 20% line) - cost if wrong: none.
58. Task 7: Ruling: the four are EQUIVALENT and deleted, not held by restored checks - their code serves only the old Governors list: nothing in the court's row pool sets line.vacant or line.rim any more (the Provinces page's rows carry their own vacant through gm_fill_row), so fill_rows' vacant branch and its set_rim(row, "row", ...) are unreachable, set_rim's "row" art is chosen for a rim no row wears, and ICUI.HEADERS.govs is drawn and hidden again by gm_sync in the same refresh; the checks that held them were Task 2's ten retired Governors-list checks, whose view no longer exists. The dead code itself is left in place (RIMS.row, RIM_ART_ROW, the row file's ROW_RIM layers and seat_rim_row.png, fill_rows' vacant branch, HEADERS.govs), a cleanup across the generator, the panel Lua and the harness for another session - cost if wrong: a future list that sets line.rim or line.vacant on the row pool has no mutant guarding the draw until one is written for it.
59. Final: Ruling: Important 2 (Phase 0 question 4 - CA's own region and army tooltips do not show over the map with the court open, against spec section 2) is not fixed in code - its cause is unprobed (the court's show_hud(false) hides every visible root child, and CA's world-space UI lives under root > 3d_ui_parent, but nothing has shown that is where the tooltips live), and exempting a root child on a guess could put CA's HUD back over the court; it goes to the handoff's owed list by name, with question 3 (does a settlement click select it through the pin's 180x146 box) asked explicitly this time - cost if wrong: the player gets no region or army tooltip on the Governors view until the author's next look.
60. Final: Ruling: the Court tab's own refresh cost (1.1M has_trait at 30 provinces, 0.4s pure Lua) is not this plan's finding - it predates the plan, and ICUI.map_memo serves only the Governors view - cost if wrong: the Court tab keeps its hitch in a large realm until a pass over IC.share's callers caches it.
61. Final: Ruling: IC.assign_governor and MP_OPS.gov not checking the province is held stands - a model contract from before this plan; every sender in the panel asks gm_held first and a redraw drops a stale choice - cost if wrong: a future sender that skips the guard can appoint to a lost province.
62. Final: Ruling: the four pre-plan survivors ruled equivalent, with their dead code left, stand (the reviewer agrees) - cost if wrong: as ruled in Task 7.
63. Final: Ruling: the column's candidates following the full-screen picker's saved order with no sort control of their own stands - spec section 3 makes them the court's existing picker - cost if wrong: a player wanting another order sorts in the full picker first.
64. Final: Ruling: a pin and row showing the province's live weight while the court's share moves at the next recompute stands - spec section 4 says the next recompute - cost if wrong: a settlement upgraded mid-turn shows its new weight on the pin before the party's share catches up.
65. Final: Ruling: Kislev's switch to the tactical view is not copied - the spec rests nothing on it - cost if wrong: none measured.
66. Final: Ruling: the pin's click box covering its two plates stands - a click on the province's name opening its picker is what a player expects of it - cost if wrong: a click meant for the settlement under a plate opens the picker (question 3, now asked).
67. Final: Ruling: the raise_hired 0.5s timing stands as ruled in the aside - cost if wrong: as ruled.

## 4. Phase 0 answers (the author's first look, build 6D8BE636)

1. Pins track their settlements as the camera moves, at the usual and a smaller UI scale.
2. Drag, edge-scroll, zoom and keys all work through the court.
3. Clicking the settlement first opened the picker - the plate covered it; the pin now stands
   above its settlement (CA's anchor `0.50,1.00`, build 7F0D1A29) and covers none of it.
4. **Open:** the game's own map tooltips do not appear over bare map with the court open. The
   court's `show_hud(false)` hides every visible root child, and CA's world-space UI lives under
   `root > 3d_ui_parent`; unprobed, and not guessed at in code (final ruling).
5. The face draws round in the head (`maskimage`).
6. "Make it higher and fit" - answered by the anchor and the two plates.
7. Two lines, the province then its loyalty - now on two plates.

## 5. Gates

After the final review's fix pass:

| Gate | Result |
|---|---|
| `_iron_court_harness.lua` (`IC_TEST_ALL=1`) | ok, 852 checks |
| `mutate_iron_court.py`, full run (Task 7) | 957 run, 953 caught; the 4 left are equivalent (ruled) and deleted |
| `mutate_iron_court.py`, the fix pass | 2 re-aimed onto the memo, 1 new, then all 92 map and row mutants re-run: all caught; 954 anchored, 0 stale |
| `gen_ic_ui.py --check` | ok, 22 files, 624 components (the new rail rule seen RED at 1920, 1600 and 2560 first) |
| `gen_ic_ui.py --selftest` | ok, 2539 guids; 2531 after the cleanup |
| `preview_iron_court.py --check` / `--selftest` | ok |
| `make_ic_backdrop.py --check` | ok |
| `luac -p` on the model, parties, panel and map Lua | exit 0 |
| `check_lua_api.py` / `check_lua_literal_left.py` | 0 / 0 |
| `import_iron_court.py` verify | gates green; 1791 files verified in the saved pack; 22 Iron Court `.twui.xml` read back out of the live one |
| `sync_iron_court_repo.py --selftest` | ok, 102 files (the repo itself is not synced) |

## 6. Owed in game

1. The column at a second UI scale, and the pins on a screen wider than 16:9.
2. The camera move when a province is chosen on the Provinces page.
3. The round buttons' grey look when they cannot act (nothing chosen, an empty province's cross).
4. The picker's inactive cards: a refused man greyed, his refusal first on the tooltip.
5. The row's party badge on the face's corner, and its three lines inside the frame (both
   fixed after the author's last look).
6. Phase 0 question 4: CA's own region and army tooltips over the map with the court open. The
   spec wants them; they did not show at the first look, and the cause is unprobed.
7. Phase 0 question 3, asked outright this time: does a click on a settlement select it, or does
   the pin's 180x146 box take it and open the picker?
8. A click in a large realm: the memo should make it instant; nothing has timed it in game.
9. Multiplayer is untested.

## 7. Build

`780A41C5` - see the head of this file. The pictures are `ic_gm_provinces.png` and
`ic_gm_picker.png` (and `_1600`, `_2560`) in `.skilltree_cache/ui_preview/`.

## 8. Pushed

Pushed to GitHub on 2026-10-01 as 48e294a (build `780A41C5`), together with `1C3AEB24`
(the party map, `HANDOFF_20260930_IRON_COURT_PARTY_MAP.md`). The repo README, DEVELOPMENT.md
(852 checks, 954 mutants, six tabs) and CHANGELOG were updated with it, and the two old Map tab
files were deleted from the repo, which the sync does not do on its own.
