# Iron Court for Dwarfs - phase 3, the Dwarf UI (handoff)

Plan: `docs/superpowers/plans/2026-10-04-iron-court-dwarfs-phase3-dwarf-ui.md` (16 tasks).
Spec: `docs/superpowers/specs/2026-10-04-iron-court-dwarfs-design.md`. Ledger with every ruling:
`.superpowers/sdd/iron-court-dwarfs-phase3/progress.md`. Finished 2026-10-05.

**Now superseded in data/ by `F4CF5CA4`, the Dwarf release of 2026-10-06 (`HANDOFF_20261006_IRON_COURT_DWARFS_RELEASE.md`).**

**State:** built, packed (`Modding Files/Modpacks/derpy_iron_court.pack`, md5 `8BF4E96D`, 1867
files, verified from disk) and copied byte-identical to `data/`. The pack is unpublished, so
there is no Workshop folder to copy to. **Not yet seen in game.** The author has approved all
four preview groups.

## 1. What shipped

**Two panel files for the Dwarfs**: `ui/campaign ui/derpy_ic_panel_dwf.twui.xml` and
`derpy_ic_panel_dwf_compact.twui.xml` (GUID prefixes IC60/IC61). Both are built by
`gen_ic_ui.py` running the module a second time with `_RACE = "dwf"` (`_dwf()`, `race_xml()`).
The Chaos Dwarf panel pair is byte-identical to before. `phase3_probe.py --verify` re-checks
1768 files, or 1813 with `--previews`.

**The Dwarf art: 40 files under `ui/derpy_ic/dwf_*.png`**, every one baked from CA art at its
cell's exact 1920 size:

| Art | Sizes | Source |
|---|---|---|
| Tab ribbons | 204x34, 240x32, 300x32, 372x34 | CA's `tab_button_unit_pack_active` / `_selected` and `tab_button_legendary_grudges_selected`. Corners kept whole (cuts 34/34/144/34) and runs mirror-tiled |
| Knot frames | 13 boxes, scale chosen by `dwf_knot_scale` (below) | CA's Dwarf knot frame |
| Leather strip (Governors bands and labels, button holder, the map pin's name and loyalty plates) | 113x30, 120x30, 180x30, 444x90, 1920x66, 1920x128 | `wh_main_dwf_dwarfs/mortuary_cult_top_strip.png`, knot corners 36x14 kept whole |
| Readout plate (the influence plate and the governor note, phase 3 review) | 190x30, chamfer 6 (`dwf_note.png`) | The seats counter's chamfered gold rule |
| Tab and law-vote marker | 128x128 (`dwf_mark.png`) | The Hell-Forge heat glow, hue turned to (70,160,255) |
| Other bakes | | Lintel, heading plates, seats plate, hall and throne, panel backdrop |

**Knot-frame scales** (the largest twentieth whose ink stays out of every cell). Where a cell
lies on the rim, the box gets a 2px chamfered gold rule instead:

| Box | Treatment |
|---|---|
| 364x184, 455x266 | Knot frame at x1.00 |
| 364x176 | Knot frame at x0.70 |
| 1884x96 | Knot frame at x0.50 |
| 306x150, 340x600, 503x1080, 606x836, 926x300, 926x473, 934x548, 1884x94, 1884x540 | Gold rule (a cell on the rim) |

**Runtime swaps.** The pooled files are shared with the Chaos Dwarfs, so the Lua re-points
them when the court is Dwarf. All of these are read from `DWF.art` through `ICUI.use_race`:
- **Card text:** move names and icons go through `ICUI.plot_of` / `favour_of` (the overlay of
  `IC.plot_text`, which now returns the icon as its fifth value).
- **Paintings:** government pictures use `ICUI.gov_art` (`DWF.art.gov_art`, six paintings).
  Law paintings use `ICUI.law_icon` (`tech_dir` + `law_art`, 20 paintings).
- **Buttons:** shared buttons use `ICUI.skin_buttons`. A refused button takes the theme's grey
  plate with dark ink (`ICUI.grey_refused`, hooked into `set_text`). The chosen law's glow uses
  `ICUI.law_glow`.
- **Any CA default-skin path:** `ICUI.themed(path)` maps it onto the race's colour theme
  (`ui/skins/wh3_main_theme_caledor_sky/`, the same file names, so geometry is unchanged). The
  sort arrows, Governors rows and toggles go through it.
- **Scrollbars:** both lists' handles use `ICUI.skin_handle` (the track has no blue twin and is
  neutral).
- **Governors map pin:** the pin, name plate and loyalty plate use `DWF.art.gm_pin` /
  `gm_name` / `gm_loyal`.
- **Law card vote mark:** `DWF.art.mark`.
- **Trait and band icons:** `trait_dwarf` / `thane`, also used by the Help topics.

A Chaos Dwarf court has none of these `art` fields, and every swap leaves it untouched. The
harness pins that for each swap.

## 2. Measured numbers

**Backdrop dim.**
- Chaos Dwarfs: 0.42.
- Dwarfs: **0.27**, the largest hundredth where every bare cell clears 4.5:1 at 1600, 1920 and
  2560. The mockup's 0.42 left `ic_row_crest[10]` at 3.2:1.

**Worst cell at 1920** (`make_ic_backdrop.py --check`, 93 cells per race):
- Chaos Dwarfs: `ic_row_b[6]`, 4.6:1.
- Dwarfs: `ic_row_crest[10]`, 4.6:1 (p95 43.8).

**Ribbon dims for cream ink** (`DWF["ribbon_dim"]`; the plan's 0.72 and 0.52 were re-measured in
Task 4):
- Active: 0.65.
- Hover: 0.51.
- The gold lit ribbon cannot carry cream (p95 about 140), so its words are dark (`[[col:black]]`).

**Refused buttons:**
- Red on the blue plate: 2.4:1 (p50).
- Red on the grey plate: 1.5:1.
- Dark ink on the grey plate: 5.5:1 (p50) and 9.3:1 (p95). This is why a refused label turns dark.

**Known shortfall, reported and not fixed:** a red price on a blue ribbon ("Fully push 500")
measures 1.84:1. The ribbons have no grey art.

## 3. The author's approvals (`Modding Files/source/iron_court_preview/phase3_approved/approvals.json`)

- **governors:** "change it to dwarf themed, then approved (author, 2026-10-05); DWF_KEEPS ruled
  empty: every Chaos Dwarf picture replaced by CA's Dwarf skin, its blue theme, or a bake"
- **court:** "approved (author, 2026-10-05, after the Governors view went Dwarf: blue tab and
  vote markers, Dwarf trait and thane icons, blue sort arrows and scrollbar handles)"
- **offices:** the same words as court.
- **intrigue_laws:** the same words as court.

`phase3_approvals.py --verify-all` prints `approved: court, governors, intrigue_laws, offices`.
The 45 Chaos Dwarf preview pictures are copied to `phase3_approved/chd/` for phase 4 to compare
against. That is 45 rather than the plan's 33, because the laws, government and Help views were
added after the plan was written.

## 4. The DWF_KEEPS ruling

`DWF_KEEPS = set()` and `DWF_KEEP_PREFIXES = ()` in `gen_ic_ui.py`. Every Chaos Dwarf picture a
Dwarf court drew is replaced: the Governors column's Hell-Forge plates, the heat glow, the Tower
of Zharr toggle art, the trait, band and Conclave Influence icons, and the Chaos Dwarf technology
paintings. The set stays in place so a deliberate keep can be ruled back one at a time.
`check_race_art` fails CA's red plates (`RED_PLATES`, including `parchment_sort_arrow_`) on the
Dwarf panel.

Review Focus 4 said the action buttons, the pager and Fill Empty Seats stay on CA's red plate.
That no longer holds: the author asked for blue buttons, so they take the theme.

## 5. Contract additions

**Lua:**
- **Throne and layout:** `ic_throne_of`, `ICUI.RACE_XY`, `ICUI.use_race`, `ICUI.grid_xy`,
  `ICUI.draw_throne`, `ICUI.CARD_FRAME_INDEX`.
- **Tabs, plates and words:** `ICUI.skin_opener`, `ICUI.tab_art`, `ICUI.light_plate`,
  `ICUI.lit_word`, `ICUI.TAB_WORD`, `ICUI.RACE_WORDS`.
- **Added in tasks 14-15:** `ICUI.plot_of`, `ICUI.favour_of`, `ICUI.themed`,
  `ICUI.DEFAULT_SKIN`, `ICUI.skin_buttons`, `ICUI.BTN_FILES`, `ICUI.plate_button`,
  `ICUI.grey_refused`, `ICUI.skin_handle`, `ICUI.SLIDER_HANDLE`, `ICUI.CHD_TRAIT_ICON`,
  `ICUI.CHD_BAND_ICON`.

**`R.art` fields** (Dwarfs):
- `suffix`, `tab`, `frame`, `lit_ink`, `title_cap`, `heading_cap`, `opener_icon`, `bullet`
- `theme`, `tech_dir`, `gov_art`, `law_art`
- `gm_pin`, `gm_name`, `gm_loyal`, `mark`, `trait_icon`, `band_icon`

The importer checks `suffix` through `theme`, plus `mark`, `gm_name` and `gm_loyal`, against
`gen_ic_ui`.

**Python** (`gen_ic_ui.py`):
- **Race build:** `RACE`, `PANEL_FILE`, `race_xml`, `DWF`, `DWF_THEME`.
- **The keep list:** `DWF_KEEPS`, `RED_PLATES`.
- **Strip and mark bakes:** `DWF_STRIP` / `dwf_strip` / `dwf_strip_sizes` / `dwf_strip_rails`,
  `DWF_MARK` / `dwf_mark`.
- **Dwarf checks:** `check_race_art`, `check_law_art` (Dwarf government, law and move icons), check
  20d (measures `DWF.PLOT_TEXT`), and `check_gm_plates`. For Dwarfs, `check_gm_plates` measures
  the strip's own field (rows 2-38 of 46, scaled from the 1920 bake and rounded up to the
  hundredth a `ty` is written in) instead of the Chaos Dwarf slice margin.

**Harness and preview:** harness `IC_DUMP_RACE`; preview `--race`.

## 6. Gates at the finish

All green:

| Gate | Result |
|---|---|
| `luac` | Clean |
| Harness | **1026 checks** |
| `check_lua_api` | 0 suspect calls |
| Literal-left | 0 sites |
| Undeclared names | 1 (pre-existing) |
| `gen_ic_ui` | 30 files, 1910 components; selftest 7203 GUIDs |
| `gen_iron_court --check` | OK |
| Backdrop | 0 problems |
| Importer verify | 1785 generated PNGs |
| Chaos Dwarf court | Unchanged |
| Mutation runner | **1140 mutants anchored**; the Dwarf subset of 33 is all caught after one fix |
| Preview selftest | OK |

`check_lua_api` caught `string.find` with `^` in `ICUI.plate_button`. That pattern returns
nothing in WH3, so the stock-Lua harness passed while in game the buttons would never have
greyed. It now uses `string.match`.

## 7. For phases 4-6 (Review Focus 7)

Later phases' preview edits land on the Chaos Dwarf path. Phase 4's `plot_cards(G, race)` and
phase 5's `STRINGS["ic_book"]` are written into `render()`'s Chaos Dwarf branch. A Dwarf picture
comes from the dump, so whatever their Lua draws appears there without those lines.

Phase 6 Task 4 Step 1 expects the Dwarf picture count to EQUAL the Chaos Dwarf one. It is now 39
Dwarf against 45 Chaos Dwarf previews, so that step must compare per view, not by count.

Any new pooled component that carries CA default-skin art must go through `ICUI.themed`, or
appear in `ICUI.skin_buttons`, or the Dwarf court shows it red. `check_race_art` sees only the
Dwarf panel files, not the shared ones. The harness's Dwarf checks are what catch a shared file.

## 8. Owed in game

- **Dwarf campaign:** play as Karak Kadrin and open every tab.
- **Chaos Dwarf campaign:** check it looks unchanged.
- **Long candidate names:** "Lord Kazador, Household Warrior" runs about 4px past the governor
  picker's row in the preview. PIL's glyph widths are approximate, so look in game.
- **Map pin:** the Dwarf pin and its plates appear in no preview, only in the harness.
