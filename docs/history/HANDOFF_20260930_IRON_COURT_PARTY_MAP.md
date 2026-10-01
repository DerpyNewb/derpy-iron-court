# Iron Court party map - Tasks 2-5, build 1C3AEB24 (2026-09-30)

Plan `docs/superpowers/plans/2026-09-29-iron-court-party-map.md`, spec
`docs/superpowers/specs/2026-09-29-iron-court-party-map-design.md`, ledger
`.superpowers/sdd/2026-09-29-iron-court-party-map/progress.md` (every ruling is there). Task 1 and
both in-game probes are in `HANDOFF_20260929_IRON_COURT_FULL_SWEEP.md` section 9: the first probe
found the markers tracking but fully transparent (CA's fade, removed in `0982F260`), the second
found them drawn on the capital. This build finishes the plan and its final review: `1C3AEB24`, MD5
`1C3AEB245BBED7A1F29C397C8C8E735A`, 1761 files, deployed byte-identical to data/ (backup
`.bak_pre_auto_20260930_110051` holds `8E7AC185`, the pre-review build), **not pushed**.

## 1. What the map does now

- **The legend** lists the court's parties in court order, then "No governor". Each row has the
  party's disc and crest, its name, "Governs N" and "Would take N". Past seven rows it pages with
  the court's own Previous / "Page N of M" / Next, hidden on one page.
- **Choosing a party** frames its row and rings, in red, every province it would take if it
  walked out; a second click clears it. The Crown, the first ten turns and secession switched off
  ring nothing, and the hint line says which. "No governor" rings the ungoverned.
- **A marker's tooltip** names the province, its governor and his rank, his party, the province's
  loyalty, any party it would go with, and what a click does.
- **Clicking a marker** opens the court on Governors with that province's picker. An appointment
  returns to the map; the court's close button returns to the map; a tab click stays in the court;
  the Map tab or the court's opener leave without the court's later closes remembering the map.
  A province lost since the map drew redraws the map instead of reaching the picker.
- **Replacing a governor now writes the one who left to the Record** (`IC.assign_governor`). The
  Governors tab never replaced a sitting man, so this only shows through the map.
- **Selecting an army or a settlement, or ending the turn,** closes the map and gives the game's
  screen back.

## 2. Found while executing (not in the plan)

- **The chosen row's frame ran through its text.** The frame is the party card's, with 9px rails;
  56px rows cannot hold two lines inside them. Rows are 66px and the legend 626px tall, and
  `check_map` now refuses any row cell that crosses the rails (seen failing on the old numbers).
- **Long province names overran the marker.** 81 of the map's 317 province names are wider than
  its 200px, measured with the generator's font; the widest, "Southlands World's Edge Mountains",
  is a Chaos Dwarf province. The marker now cuts them with "..." through `ICUI.fit_cut`, the rule
  the court chose for long names on 2026-09-14, and the tooltip keeps the whole name.
  `ICUI.MARKER_W` shares the width with the generator through `check_map`. Fewer cuts is one number
  (`MARKER_W`): the 90th-percentile name is 230px wide.
- **`preview_iron_court.py --selftest` had been failing since `CCF16A5E`** on two assertions the
  civil missions outgrew: a four-word minimum on a card's text (Purge's is "The court watches.")
  and "unaimed moves are one column" (Errands and Missions are two). Both rewritten to the property
  they stood for: every literal of a card's text was read, and no column mixes aimed and unaimed
  moves.
- **Three of the plan's mutants never ran** under its filter words; run by name, all caught. Two
  anchors were retargeted: the layer is sized through `ICUI.resize`, and the marker name through
  `ICUI.fit_cut`.

## 3. The final review, and what it changed

A fresh reviewer read the whole plan's diff. No crash. What was fixed, each with a check seen
failing first:

- **The way back to the map went stale.** A marker's court keeps a "return to the map" flag.
  Leaving that court by the Map tab, or by the court's own opener, kept it, and the next ordinary
  close of any court opened the map. The flag now lives as long as the court a marker opened:
  `ICUI.open` clears it, and the marker sets it only once the court is up.
- **Markers drew over the legend** and took its clicks when a settlement was panned under it.
  They are now made inside `ic_map_pins`, the layer's first child, which takes no clicks;
  `check_map` refuses a layer file without it.
- **Nine behaviours had no check** (each survived all 818): the court close spending the flag,
  another faction's turn end, the reopened map's choice, the "why nothing is ringed" hint and
  tooltip, both crests, a failed court open, and "Would go with". Nine checks, nine mutants.

Deferred, each small: `map_tip` recomputes what each party would take for every marker (about
48,000 calls at 40 provinces); the opener's tooltip is stale after a map-made appointment until
the turn starts; a governor who dies mid-turn draws "No governor" but is not counted as one;
in multiplayer, an answer that arrives after the player went back to the map is not drawn until
it reopens.

## 4. Gates

Harness 828 checks (804 before Task 2: six for the legend, five for the click round trip, two for
leaving the map, one for the name cut, ten from the review). Mutants 878, 43 of them aimed at
the map's Lua, full run 0 unexplained; the generator re-run after it moved no UI file.
`gen_ic_ui.py --check` and `--selftest`, `import_iron_court.py` verify, `preview_iron_court.py
--check` and `--selftest`, `sync_iron_court_repo.py --selftest`, `luac -p`, `check_lua_api.py`
and `check_lua_literal_left.py` all clean. `ic_map.png` in `.skilltree_cache/ui_preview/` is the
legend and a sheet of every party's marker.

## 5. Owed in game

1. The legend fills, one row per party, and "Would take" matches what the red rings show.
2. A marker's tooltip, and whether names like "The Howling Wastes" fit or cut in the game's font.
3. The round trip: click a marker, appoint a governor, and the map comes back with the marker in
   the new party's colour; the court's close button also comes back to the map.
4. Selecting an army, and ending the turn, each close the map with the game's screen back.
5. A marker panned under the legend draws beneath it, and the legend's rows still take the click.
6. Whether clicking a marker also selects the settlement under it (which would close the map
   before the click lands).
7. Still open from the probe: a camera drag beside a marker, and the screen coming back after the
   court closes.
8. Multiplayer is untested.
