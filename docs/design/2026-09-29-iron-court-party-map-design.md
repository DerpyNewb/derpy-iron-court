# Iron Court - the party map (on the live campaign map)

Date: 2026-09-29. Author request, after the Rome 2 comparison: "political infuence map as a new
tab can be added". Choices made in chat, in order:

- Purpose: **who holds where** - each province in its governing party's colour; choosing a party
  outlines what it would take if it walked out.
- Form: first "schematic in the tab"; then, after the author asked whether Elspeth's Gardens of
  Morr mechanic applied, **"Gardens way, on the live map"**. The first choice was made on a false
  premise of mine - that an on-map overlay needed nine or more new 3D composite scene assets. CA's
  Gardens view needs none (section 1).
- Clicking a province: **pick its governor** (the Governors tab's overseer picker).
- Sections 1-5 of this design were each presented in chat and answered "continue"; the author
  then asked for the implementation plan.

## 1. Evidence: how CA's Gardens of Morr view is built

Read from `ui3.pack`, `ui/campaign ui/dlc25_black_towers.twui.xml` (dumped with
`tools/read_pack_index.py`), and `campaign/wh3_dlc25_gardens_of_morr.lua`:

- The root `dlc25_black_towers` is screen-sized (`ScreenSizedComponent`) and hides the HUD
  (`CampaignHUDHiderPanelCallback`, `hide_floating_ui`). It lies over the LIVE campaign map; the
  camera stays free.
- `list_black_tower_overlay` is a `ContextList` over the player's settlements (a CCO expression:
  `Join(PlayersFaction.ProvinceList, PlayersFaction.DiscoveredProvinceList).Distinct
  .Transform(SettlementList).Filter(...)`).
- Each `template_black_tower_slot` carries `ContextWorldSpaceComponent`, context
  `CcoCampaignSettlement`, function `Position`, user property `depth_disabled = 1` - the engine
  keeps the slot on its settlement as the camera moves - and a `ContextOpacitySetter`,
  `(pos = self.Position.y) => {pos | CampaignRoot.IsTacticalViewActive => 1 | pos < 0 => 0 |
  pos < 50 => pos/50.0 | 1}`, `propagate`, `update_constant`, which fades a slot in the band at
  the screen's top edge.
- `holder_city_name` draws the settlement's name and the owner's banner (`mon_24`) with a
  `capital_icon`. `elspeth_map_pin_holder` does the same for a CHARACTER (`CcoCampaignCharacter`,
  `Position`).
- The Gardens' own rules (foreign slots in allies' settlements, trespass, teleport rituals) are
  NOT applicable to the court and are not copied.

The id for a script-made settlement context: `cco("CcoCampaignSettlement",
region:settlement():cqi())`, attested in Fortified Camps (`aafortcamps.pack`, Workshop
3617600622) - the only installed pack of a 2026-09-29 byte scan of `data/` and the Workshop
folder that builds one from Lua. `uicomponent:SetContextObject(cco)` is documented
(`campaign/uicomponent.html`); `docs/CUSTOM_UI.md` "What you cannot do" names it as the one way
to give a runtime component a context.

**Unproven, and therefore Phase 0:** that a component made with `CreateComponent` and given its
settlement by `SetContextObject` tracks the camera the way CA's engine-instanced list slots do.

## 2. Phase 0 - the in-game probe (gates everything else)

`tools/probe_ic_map_pin.lua`, run through the WH3 bridge (`mcp__wh3__*`), throwaway, not shipped.
Every call inside `pcall`: one Lua error inside `wh3_eval` wedges the bridge for the rest of the
game session.

1. `CreateComponent` one marker from a minimal `.twui.xml`: a plate carrying CA's
   `ContextWorldSpaceComponent` block (section 1) verbatim.
2. `SetContextObject(cco("CcoCampaignSettlement", capital:settlement():cqi()))`.
3. Read the marker's screen position; move the camera twice (`cm:scroll_camera_from_current` or
   `cm:set_camera_position`); read it after each.
4. Click-through: read whether a click on bare map beside the marker still reaches the map (the
   layer's root must not swallow it).

**Pass**: the position follows the settlement both times and the map takes the click. **Fail**:
the design falls back to the schematic tab (section 10), and nothing else here is built.

## 3. Getting in and out

- **The Map tab**, a seventh tab placed right after Governors: `ic_tab_map` at Governors' old
  neighbour slot, with Intrigue, Petitions and Record each moving one slot right (Record stays
  LAST - the author's 2026-09-24 ruling: the one tab with nothing to act on). The attention
  markers move with their tabs; the Map tab has none of its own.
- Clicking it: the court panel closes (`ICUI.close`), the HUD stays hidden, and the party map is
  laid over the live campaign map. The camera stays the player's.
- **The HUD hide is the court's own, `ICUI.show_hud(false)`**, proven in game, not CA's
  `CampaignHUDHiderPanelCallback` - one unknown fewer. It hides every root child but the court
  panel's id, so the map's root components are added to that exemption.
- **Out**: the legend's close button, or Esc, returns to the court on the Governors tab. Ending
  the turn closes the map, as `ic_turn_end` already closes the court.
- The map is never saved; loading a game starts without it.

## 4. The markers

- **One marker per province you hold** (`IC.seats`, so the map and the Governors tab list the same
  set), on the province's CAPITAL settlement (`region:is_province_capital()`) if held, else the
  first held settlement. A new helper; `IC.held_region` keeps its own choice (the governor bundle
  code uses it and a faction-province bundle does not care which region it is given).
- **Layers**, one small component, the same pixel size at every zoom:
  - the **plate**: a disc about 48 px, in the governing party's colour (`gen_ic_ui.HOUSE_COLOUR`
    and the absorbed factions' colours, the same the dial uses), with that party's crest in the
    middle; an ungoverned province gets a plain bronze plate and no crest;
  - the **capital ring**: brass, on the realm capital's province only;
  - the **outline ring**: red, hidden until a party is chosen (section 5);
  - the **name**: the province's on-screen name on a small dark plate under the disc, written
    from Lua (`SetStateText`), never a live `ContextTextLabel` - a live label re-renders over the
    written text.
- **Hover**: province name; governor and rank, or "No governor"; party; the court's loyalty there
  (`IC.province_loyalty`); and, if a party would take it on walking out, "Would go with {party}
  if they walked out". Written when the map opens, never in a turn handler.
- **Fading**: CA's `ContextOpacitySetter` (section 1), copied verbatim.
- **Shroud**: none needed; your own settlements are never under it.
- **No ceiling**: the camera deals with density.

## 5. The legend, and choosing a party

- A panel docked on the LEFT edge under the top bar (where CA's Gardens view docks its side
  panel), 455 wide - a party card's width.
- Header "The realm - who governs where"; one row per party in court (six at most): colour swatch
  and crest, name, "Governs N" (`#IC.provinces_of_house`), "Would take M"
  (`#IC.defecting_provinces`); a last row "No governor" with its count and a bronze swatch; one hint
  line, "Click a party to see what it would take. Click a province to choose its governor."; and
  the close button.
- **Choosing a party** (click its row): the row wears the party cards' gold "chosen" frame, and
  every province in `IC.defecting_provinces` for it shows the red outline ring. Clicking it again,
  or another row, moves or clears the choice. Hovering a row shows `ICUI.secession_tip` for it.
- **Rows that outline nothing say why**: your own house ("Your own house does not secede", the
  existing sentence); any row while `not IC.secession_on()` (switched off, or the grace period -
  "No party can break with you for N more turns"). **"No governor"** outlines the ungoverned
  provinces.
- **No dimming** of the other markers: CA's opacity setter rewrites opacity every frame, so a dim
  set from Lua is overwritten. The red ring alone carries the choice.
- The choice is local session state, not saved; a reopened map starts with none chosen.

## 6. Clicks, the round trip, multiplayer

- **Clicking a marker**: the map closes and the court opens straight into that province's overseer
  picker, `ICUI.pick = {kind = "gov", key = province_key}` - the Governors tab's own picker, rules
  and refusals.
- **Back to the map afterwards**: when the appointment is answered, the court closes and the map
  reopens with the marker in its new colour; cancelling the picker also returns to the map; a
  refusal stays in the picker with its notice, as today. In multiplayer the `gov` action is
  answered asynchronously and the map reopens from `ICUI.after_op` when the answer arrives; with no
  answer the player is simply left in the court.
- **Any other click** passes through to the campaign (Phase 0 checks it). Selecting an army or a
  settlement (`CharacterSelected`, `SettlementSelected`) closes the map and restores the HUD, so the
  player can act on what they saw. Nothing is blocked; a map that swallowed every click is how a
  panel wedges the UI.
- **Multiplayer in sum**: the map is local display; the one change it can make, a governor, already
  travels as the `gov` action.

## 7. What gets built, in order

0. The probe (section 2). Pass, or stop and take section 10.
1. **Layouts** from `tools/gen_ic_ui.py`: `derpy_ic_map_marker.twui.xml` (plate, crest, capital
   ring, outline ring, name plate; CA's two callbacks copied verbatim) and
   `derpy_ic_map_legend.twui.xml` (header, seven row slots, hint, close), under the same GUID and
   name checks as the panel's other files; the `ic_tab_map` tab and the moved tab slots in the
   panel layout.
2. **Art**: round party plates in the existing colours from the same generator that writes the
   dial's plates; the rings and the bronze empty plate point at CA's own paths in the game files
   (never copied into the public repo).
3. **Lua**: a new `zzz_derpy_iron_court_map.lua` (the panel file is ~7,000 lines), loaded after
   `zzz_derpy_iron_court_ui.lua` and calling into it: open/close, marker placement, the legend and
   party choice, the click round trip, the turn-end and selection listeners, and the
   `ICUI.show_hud` exemption. `tools/import_iron_court.py`'s `SCRIPTS`, the harness loader and
   `tools/sync_iron_court_repo.py`'s manifest gain the file.

## 8. Testing

Each check watched failing before its code goes in (`tools/_iron_court_harness.lua`):

- one marker per held province, on the capital settlement if held, else the first held; each given
  `cco("CcoCampaignSettlement", <that settlement's cqi>)`;
- plate colour and crest per governor's party; bronze for none; the capital ring on the realm
  capital only;
- legend counts equal `#IC.provinces_of_house` and `#IC.defecting_provinces`; choosing a party
  rings exactly its defecting provinces; own house, secession off and the grace period ring
  nothing and say so; "No governor" rings the ungoverned;
- a marker click opens that province's overseer picker; an answered appointment reopens the map, a
  cancel reopens it, and in multiplayer it waits for the answer;
- a selection event closes the map and restores the HUD; so does turn end; no tooltip is written
  from a turn handler;
- the HUD hide leaves the map's own root components visible.

Stubs the harness gains: `region:is_province_capital()`, `region:settlement():cqi()`, a recording
`cco()` global and `SetContextObject`, and the two selection events. Mutants
(`tools/mutate_iron_court.py`) for every branch, each caught. Then `gen_ic_ui.py --check` and
`--selftest`, `import_iron_court.py`, the full mutation run, deploy.

`tools/preview_iron_court.py` draws the legend and a sheet of every party's marker for design
review; nothing offline can draw them on the map.

**Only the game can confirm** (the handoff lists them): markers follow the camera and fade under
the top bar; bare map still takes clicks and drags; selecting an army closes the map; the round
trip lands back on the map in the new colour; two-player multiplayer (untested).

## 9. Out of scope

- A marker on every settlement (the province is the model's unit).
- Colouring by loyalty (the author chose "who holds where").
- Dimming unchosen markers (section 5).
- Camera jumps from the legend.
- Using the map as the civil missions' province picker - possible later, since both are "click a
  province you hold"; `2026-09-29-iron-court-civil-missions-design.md` keeps its list picker.

## 10. Fallback if Phase 0 fails: the schematic tab

As designed in chat before the switch: the Map tab's body holds a fixed pool of 64 markers
declared in the panel's own layout, placed by `MoveTo` at the settlements' `logical_position_x/y`
scaled into a ~1400x770 area, with the same legend (455 wide) on the right, the same colours,
rings, hover and click. Plates never overlap (a marker that would is pushed just clear, placed
capital first, then governed, then map order); a name whose box would cross a drawn one is hidden;
past 64, "and N more provinces - see the Governors tab". Fully checkable offline.
