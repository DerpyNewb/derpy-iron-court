# Iron Court - Governors on the live map, and weight from developed provinces

Date: 2026-09-30. Author request, after playing build `1C3AEB24`: "can governor tab and map be
merged, so that clicking governors shows the map, political influence and loyalty per province,
and the one who rules", then "add a mechanic where the more advanced the province is, the more
influence the governing party gain", then "add UI design as well as part 6, should be what CA
uses". Choices made in chat, in order:

- Political influence per province: **the governing party's pull** - its crest and colour, what
  this province adds to it and its share of the court. No new per-province figure. In the
  court's own words that pull is **weight** (Help: "A party's weight comes from the seats it
  holds, the provinces it governs and the influence of its men"); "influence" stays a man's own
  figure, as in the picker's "210 influence".
- The province list: **moves into the legend** as a Provinces page beside Parties.
- Markers: **the governor's face in the disc**, ringed in his party's colour; the plate reads the
  province and its loyalty. (Section 6 makes the disc the head of CA's Chaos Dwarf map pin.)
- Build: **the map inside the court panel** - the court stays open, its backdrop clears and the
  live campaign map shows through; the tabs stay on screen.
- The governor picker: **in the left column**, so the map stays visible while choosing.
- "More advanced": **settlement levels** - the levels of every settlement held in the province.
- UI: **CA's way, in Chaos Dwarf art** - the pattern of CA's own governor screen (Kislev's
  Atamans: select, then a round check or cross button acts; an unavailable man greyed with his
  reason on hover; two small plates under a pinned portrait), drawn with CA's Chaos Dwarf art
  wherever CA ships a counterpart (section 6).
- Parts 1-5 were each presented in chat and answered "yes" / "continue"; Part 6 is section 6.

This supersedes the Map tab of `2026-09-29-iron-court-party-map-design.md` (built as `1C3AEB24`):
its legend, markers, rings and tooltips move here, and its separate layer, its tab and its
round-trip machinery go.

## 1. What the Governors tab shows

- **Kept:** the court's top strip (title, help, "seats filled", close, the tab row), the section
  line under it and the footer line. Each sits on an opaque plate in this view: text on a live
  map has no reliable contrast.
- **Gone, on this tab only:** the throne-room backdrop (and every other panel-level image
  layer) and the content box. The live campaign map fills the rest of the screen.
- **The left column**, full height under the tab strip. Two toggles at its top switch between
  Parties and Provinces; the picker is not a toggle - it replaces the page while a governor is
  being chosen:
  - **Parties** - the party map's legend as built: court order then "No governor", each row
    its crest, name, "Governs N", "Would take N"; choosing a row rings in red what that party
    would take, a second click clears it; paged past the rows that fit.
  - **Provinces** - one row per held province: the governor's portrait (his party's crest when
    his portrait does not resolve, the empty-seat silhouette when there is none), the province,
    the governor ("None", or his name with "(away)"), loyalty with CA's loyalty icon, and
    "+N weight". Sorts on Map order, Province, Governor and Loyalty, as the tab does today. The
    row is selected by a click; the actions are the column's round buttons (section 2).
  - **Picker** - section 3.
- **Markers** on each held province's capital, pinned as built, with a new face (section 6):
  CA's Chaos Dwarf map pin, the governor's portrait masked round in its head inside a ring of his
  party's colour (a dark head and no ring when the seat is empty), and under it two small opaque
  plates - the province name, then "Loyalty 62%".
- **The Map tab is removed.** The tab row loses one tab.

## 2. Clicking

- **The camera** moves with the game's own controls - drag, edge scroll, keys, zoom - because
  in this view the panel stops taking clicks outside its plates. Hovering the map raises the
  game's own region and army tooltips; over a marker, the marker's tooltip.
- **A party row** rings what that party would take; again clears it.
- **A province row** is selected by a click: the camera moves to that province's capital and
  its marker is ringed. Two round buttons under the list then act on it: the check opens the
  picker for it (`gov`), the cross releases its governor (`ungov`; shown only when it has one).
  A second click on the selected row clears the selection. With no row selected both buttons
  are disabled, and on the Parties page they are hidden.
- **A marker** opens the picker for its province (section 3).
- **Selecting a settlement or an army through the map** closes the court and leaves the player
  on what they clicked, as the Map tab does now. The court's own turn-end close is unchanged.
- **Another tab** puts the backdrop and the click-blocking back and removes the markers.

## 3. The picker in the column

- Opened from a marker or from the check button on a selected province row. The column's page
  becomes the picker: a heading "Choose who governs <province>", one card per candidate -
  portrait, name, party crest, rank - and the round check and cross buttons under the list.
  The province's marker is ringed while it is open.
- The candidates, their order and the refusals are the court's existing `gov` picker: the model
  is unchanged. **An unavailable man's card is greyscale** (CA's `inactive` state) and the
  reason the picker already computes ("Busy", "Rank 3") is the first line of his tooltip; the
  tooltip also carries his influence and what he holds. He cannot be selected.
- A click selects a card; **the check sends `gov`** for the selected man and is disabled while
  none is selected; **the cross cancels** without sending. The answer returns the column to the
  page it came from, with the marker redrawn in the new party's colour. Another tab closes the
  picker the way a tab abandons the court's pickers today.
- The markers' round trip through the court - `ICUI.map_return`, the `ICUI.open` wrapper, the
  `ANSWERS.gov` wrapper, `map_close` - is deleted: the court never closes.

## 4. The rule: weight from a developed province

- A governorship gives its party **one weight for every two settlement levels held in that
  province, rounded up, and never less than 1** - replacing the flat
  `IC.TUNE.weight_per_governor = 3` with `IC.TUNE.weight_per_gov_level = 0.5`.
- A settlement's level is `settlement:primary_slot():building():building_level() + 1` (CA's own
  scripts read it this way; the value counts from 0). A settlement with no primary building (a
  ruin) counts 0. Only settlements the faction holds in the province count.

  | Province | Levels | Weight |
  |---|---|---|
  | lone level-1 village | 1 | 1 |
  | Ghorth-style start: capital 3, two minors at 2 | 7 | 4 (today 3) |
  | built up: capital 5, two minors at 3 | 11 | 6 (one office) |
  | four settlements, all maxed | 20 | 10 |

- It is recomputed wherever governor weight already is (`IC.refresh_gov_weight`, at turn start
  and after an appointment), so an upgrade, a loss or a razing shows at the next recompute. The
  weight is derived and not saved: no save field, no migration.
- Every court runs it, the AI Chaos Dwarf courts included. An away governor still earns his
  party the weight, as today; away only stops his province bonuses.
- Shown on the marker's tooltip ("Slaves of the Black Dwarf: +4 weight from this province
  (7 settlement levels), 34% of the court") and in the Provinces row. The Help page's Governors
  topic states the rule in one line, replacing "A governorship counts toward his party's weight
  and loyalty the way a seat does". Not on the settings page.

## 5. Build order, the probe, the fallback

1. **The weight rule** (section 4) - model only, testable offline, shippable alone.
2. **Phase 0, a real slice, then STOP for the author's in-game look.** On the Governors tab only:
   the panel's image layers clear, the panel stops taking clicks, and bare markers stand in a
   holder that is the court panel's FIRST child. Questions only the game answers:
   1. Markers inside the court panel track their capitals as the camera moves - at 1920x1080
      and at a compact layout (a smaller UI scale), where the court's box is scaled.
   2. The camera drags, edge-scrolls, zooms and answers the keys through the court.
   3. A click on a settlement through the court selects it (so the court can close on it).
   4. The game's own map tooltips appear.
   5. The masked portrait draws round inside the pin's head (section 6).
   6. The pin's point sits on its settlement at a sensible camera height (section 6).
3. **The rest** once Phase 0 passes: the column's three pages on one shared row pool (as the
   Intrigue views share one), the portrait pins, the tooltips, the camera move from a row,
   the per-view plates, and the removal of the Map tab and its layer file.

**If Phase 0 fails** - markers inside the court do not track, or the camera cannot be moved
through it - the fallback is the build that is proven in game: the Governors tab closes the court
and opens the map layer we have, carrying the same column. Sections 1, 2, 4 and 6 carry over;
section 3's "the court never closes" does not, and the round trip stays.

## 6. UI design - CA's way, in Chaos Dwarf art

Two surveys of CA's 907 shipped layouts (all in `ui3.pack`; art in `ui2.pack`), read with
`tools/read_pack_index.py`. The contact sheets are `.skilltree_cache/ui_preview/govmap_chd_art.png`
(the Chaos Dwarf pieces) and `govmap_default_art.png` (the default-skin pieces).

**The pattern is CA's own governor screen.** Kislev's Atamans are CA's province governors:
`ui/campaign ui/kislev_atamans.twui.xml` is a candidate column over the live map
(`candidate_panel`, 450x540, left edge) and a portrait pinned to each settlement
(`template_settlement_overlay`, `ContextWorldSpaceComponent(CcoCampaignSettlement:Position)`,
`depth_disabled=1`, with `offset_x/y/z` properties); `city_info_bar.twui.xml` `ksl_ataman_holder`
draws the governor's masked portrait on the settlement bar. From it this design takes:
select, then a round check or cross button acts; an unavailable candidate is shown by state, with
the reason in the tooltip and no red label; two small plates under a pinned, masked portrait.

**The look is CA's Chaos Dwarf side panels** - the Hell-Forge (`hellforge_panel_category_tab`,
`hellforge_panel_unit_tab`) and the Tower of Zharr. The Chaos Dwarf skin
(`ui/skins/wh3_dlc23_chd_chaos_dwarfs/`, 36 files) overrides none of the default pieces below, so
where CA ships no Chaos Dwarf counterpart its own Chaos Dwarf panels use the default piece, and so
does this design.

| Piece | Art | CA's use of it |
|---|---|---|
| Column body | `ui/skins/default/dlc23_chd_hell_forge/side_panerl_bg.png` (503x1080; opaque x 0-443; CA's spelling) | Hell-Forge `customisation_panel_container`, drawn 506x1080 at x -61 |
| Column title | `dlc23_chd_hell_forge/side_panel_title.png` (454x90, drawn 445x64, margin 0,80) | same panel |
| Button plate | `dlc23_chd_hell_forge/button_holder_back.png` (444x136) | Hell-Forge cost area |
| Page switch | `round_medium_button_toggle` (56x56) with a Chaos Dwarf icon, over a label on `dlc23_tower_of_zharr/tab_sub_title.png` (113x30, margin 0,12), `body_12` | Tower of Zharr `tabs_holder` (three pages at the top of its column) |
| Row body (all three pages) | `button_square_extra_large_{active,hover,selected,inactive}.png` (122x82, margin 0,16,0,16 - stretches to the column's width) | Hell-Forge `template_unit_customization_block`, 353x77 |
| Row portrait frame | `dlc23_chd_hell_forge/unit_card_frame.png` (35x65, thin bronze outline) | Hell-Forge `unit_card` |
| Unavailable candidate | the row body's `inactive` state (grey art); the reason first in the tooltip | Hell-Forge rows (no greyscale shader) |
| Map marker | `dlc23_chd_narrative_panel/chd_narrative_panel_map_pin.png` (50x80: a round bronze head on a point); a 38x38 image in the head at 6,5 | `chd_narrative_panel` `target` (on its parchment minimap) |
| Portrait mask | `porthole_mask.png` through the component's `maskimage` attribute (the GUID of its own mask componentimage) | Kislev `ataman_portrait`, `intrigue_panel` `portrait_clip` |
| Party ring | one white ring image, one state per party with `colour=` - CA's tint idiom (`kislev_court_orthodoxy` tints `grey_circle.png` by state); set with `SetState` | - |
| Plates under the marker, section line, footer | `dlc23_chd_hell_forge/sub_title.png` (113x30, margin 0,12, opaque), `body_10` / `body_12` in `#FFF8D7` | Hell-Forge `dy_name_armaments`; `character_information` turns display |
| Check / cross | default `round_medium_button` (56x56) with `icon_check` / `icon_cross` | CA's accept / cancel in 47 / 32 layouts; the Tower of Zharr closes with the same button |
| Sort headers | default `ui/templates/parchment_sort_arrow` (17x18) with a label above it; states set from Lua | 19 layouts; the Tower of Zharr's list carries it |
| Loyalty | default `icon_fealty_{high,medium,low}.png` (26x26) beside the % | `dropdown_units`, `army_banner` |
| Tooltips | plain text through `SetTooltipText` | the Gardens of Morr pins |

Rules that follow from the survey:

- **Every Chaos Dwarf path is referenced directly**, as `gen_ic_ui.py` already does for
  `panel_title`: CA's own layouts reach the Chaos Dwarf art by skin swap, and a component made at
  runtime is not known to get that swap.
- **`button_square_extra_large` and `sub_title` stretch; the Hell-Forge's `entry_*` bars do
  not** (428x100, no margins) - they are not used.
- **CA's sort and page callbacks are not used.** `ContextListSortButton` and `RadarListHeader`
  sort CCO lists and do nothing to a list Lua fills; `ButtonGroupPanelSelector` is engine
  behaviour. The art is taken and the states are set from Lua, as the court's own sort does.
- **`maskimage` is new to this tooling** - absent from TWUI Studio's catalogs and from
  `docs/CUSTOM_UI.md`. A wrong GUID link fails silently like the others; the generator gains a
  check that it names a componentimage of the same component, and Phase 0 answers whether the
  mask draws. The headless preview may not draw it; the preview then says so rather than
  drawing an unmasked square.
- **The pin's point must land on the settlement.** CA drew this pin only on a flat minimap; the
  world-space callback's `offset_x/y/z` properties (Kislev's template) are how it is placed, and
  Phase 0 measures it.
- **Kislev's screen also switches to the zoomed-out tactical view** (`TacticalViewHUDPanel` on its
  root). Whether a script can do that is unconfirmed; Phase 0 may ask, and nothing depends on it.

Phase 0 (section 5) carries these as its questions 5 and 6.

## 7. Testing

- Harness checks for every behaviour: each page, the picker (opened from a marker and from a
  row's check; select, check, cross; an unavailable man who cannot be selected; the check
  disabled with nothing selected), a row's release, the sort, the rings, the pin's portrait or
  dark head and its party state, the camera move, the close on a selection, another tab
  restoring the backdrop and the click-blocking; the weight at 1, 7, 11 and 20 levels, a ruin,
  a lost settlement, an AI court, an away governor.
- A mutant for every branch, and the full run at 0 unexplained.
- Generator rules: the markers' holder is the panel's first child and not interactive; every
  `maskimage` names a componentimage of its own component; in the
  Governors view every visible text cell lies inside an opaque plate (the backdrop contrast
  measurement cannot speak for a live map); the column has compact twins like the rest of the
  court.
- Preview pictures of the Governors view with a flat stand-in for the map, and of the picker page.
- Deploy after each build; the in-game looks are listed in the handoff.

## 8. Out of scope

- A per-province figure of each party's roots (declined in chat).
- A settings slider for the weight per level.
- Tinting CA's own region overlay by party.
