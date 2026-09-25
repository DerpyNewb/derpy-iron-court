# The Iron Court panel scales with the screen - 2026-09-24

Spec: `docs/superpowers/specs/2026-09-24-iron-court-ui-scale-design.md`.
Plan: `docs/superpowers/plans/2026-09-24-iron-court-ui-scale.md`.

## 1. The complaint, and what the engine does

The author's screenshot showed the court clipped. The panel was one 1920x1080 block, and the
screen a script sees was smaller than that. Three things were measured or read, and together
they decide the design:

- **The screen a script sees is the window divided by UI Scale, floored at 1600x900.** The
  author's window, about 1280x720, reported 1600x900.
- **Nothing sets a font size or the UI Scale from script.** Text can only change by opening a
  different `.twui.xml`.
- **`uicomponent:Resize(w, h, [children])` resizes the children by default.** CA's own entry
  says `optional, default value=true`. That default scales every child by the parent's factor,
  and then `layout()` sizes each child a second time on top of it.

## 2. The rule

- **The box** is the widest 16:9 rectangle the screen holds:
  `BW = clamp(floor(min(sw, sh * 16 / 9)), 1600, 2560)` and `BH = BW * 9 // 16`. Below 1600 is
  CA's floor. Above 2560 the rows would only get taller, so the extra width goes to the ground
  either side.
- **Every layout number is typed for 1920.** It is scaled by `sc(v) = (v * BW + 960) // 1920`,
  which is integer arithmetic, rounds half up, and is exact under float32 because every product
  is under 2^24.
- **A cell scales by its edges**: `(sc(x), sc(y), sc(x+w) - sc(x), sc(y+h) - sc(y))`. Two cells
  that touch at 1920 still touch at every width. A square cell stays square, at the smaller of
  the two sides.
- **Grid points scale per coordinate.** They are not rebuilt from the scaled card size. A card
  width rounded down once and multiplied by five ran a tier 2-4px past its column at some
  widths.
- **Below 1920 the panel opens compact copies** of its five in-box files, each one font size
  down (the opener and the standing line are outside the box and have none):

  | Base | Compact |
  |---|---|
  | header_24_bold | header_20_bold |
  | header_20_bold | header_18_bold |
  | header_18_bold | header_16_bold |
  | header_18 | header_16 |
  | header_16 | header_14 |
  | body_12 | body_10 |

  The compact files are `derpy_ic_{panel,card,row,party,plot}_compact.twui.xml`, GUID prefixes
  IC40-IC44, built from `at_box(1600)`.
- **Text shrinks about 11% a step while boxes shrink 17%**, so some cells that fit at 1920 clip
  at 1600. `COMPACT_OVERRIDES` corrects them in screen pixels at 1600. Each correction fades as
  `(d * (1920 - BW) + 160) // 320`: all of it at 1600, none of it from 1920 up. Every entry
  names the string that forced it:

  | Cell | Override | Forced by |
  |---|---|---|
  | `ic_card_name` | (-1, 0, 2, 0) | "Warden of the Caravan Roads", 248px, needs 254 |
  | `ic_party_off` | (0, 0, 5, 0) | "14 seats at court", 154px, needs 160 |
  | `ic_plot_*` | pad 25 to 20, blurbs +10 wide | three blurbs need a 337px line for four lines |
  | `ic_row_a` | (0, 0, 6, 0) | "Retainer Sisuthrus Burrdrik, Temple Acolyte", 412px |
  | `ic_row_d` / `ic_hdr_d` / `ic_hsort_d` | (-4, 0, 24, 0) / -4 | "1722 influence - Grand Overseer of the Forge", 419px |
  | `ic_row_e` / `ic_hdr_e` / `ic_hsort_e` | (7, 0, 2, 0) / +7 | "Available" and its arrow, 1px past the row |

## 3. Where it lives

- **`tools/gen_ic_ui.py`**:
  - the rule: `sc`, `sc_box`, `box_for`, and `at_box(bw)`, which re-executes the generator at
    another width;
  - `_scale_pass` with a completeness rule: `_classify` refuses any layout number that is
    neither scaled nor declared `NOT_GEOMETRY`;
  - `COMPACT_FONTS`, `COMPACT_OVERRIDES` and the compact XML;
  - `check()` runs exactly at 1600, 1920 and 2560. `check_scale_sweep()` walks every width from
    1600 to 2560 for geometry only: cells inside their frames, no new overlaps, the row pool
    above the pager, and the grids.
- **`zzz_derpy_iron_court_ui.lua`**:
  - every layout table is now `{x, y, w, h}`;
  - at the end of the file are `ICUI.sc`, `box_for`, `fade`, `sc_box` and `path`, plus the
    lists `SCALED`, `SCALED_TABLES`, `DERIVED` and `NOT_SCALED`, the `COMPACT_OVERRIDES`
    mirror, `BASE` (taken once at load) and `apply_scale(bw)`, which rebuilds everything from
    `BASE`;
  - `open()` computes the box first, then:
    - builds from the compact paths below 1920;
    - resizes the panel to `max(screen, box)` and centres the box with `OX`/`OY`;
    - logs `layout box=WxH k= compact= card_1=WxH`.
  - `layout()` sizes every component as well as placing it, and `ICUI.resize` passes
    `children = false`.
- **`tools/import_iron_court.py`**:
  - 8b compares all four numbers per cell, and the pie box too;
  - **the new 8d** loads the whole panel Lua under lua.exe, with the engine stubbed to no-ops
    and `IC` stubbed from the generator. It runs `apply_scale` at 1600, 1760, 1920 and 2560 and
    compares every scalar, every cell and every grid point against `at_box`. It also compares
    the overrides and the compact paths.
- **`tools/preview_iron_court.py`** draws the court and intrigue shapes at 1600, 1920 and 2560:
  `ic_court_1600.png`, `ic_court_2560.png`, the intrigue pair, and the unsuffixed 1920 names as
  before.
- **`tools/make_ic_backdrop.py`** also measures every bare text cell of `at_box(1600)` against
  the backdrop shrunk to 1600x900. The worst cell is 4.63:1 against the 4.5:1 bar.

## 4. A bug this found, already shipping

`ICUI.refresh()` read `panel:Position()` without the content offset. Everything a redraw moves
was placed as if the box sat at the screen's corner: the sixty pie wedges and their walls, the
crests, the share figures, the header strip and the sort arrows. `layout()` had the offset; only
the section label added it by hand. At 1080p the offset is zero, so nothing showed. It was
already wrong on any screen larger than 1920x1080 before today, and at 4K the box is now centred
at `OX = 640`. `refresh()` now adds the offset once, as `layout()` does. The harness check
`the content offset reaches what a redraw moves` failed first (the pie drew at 50,162, not
370,342), and a mutant pins it.

## 5. Rulings made on the way

- **Fonts are remapped at the source constants**, inside `at_box(<1920)`'s scale pass, not by
  an emitter font map. The 1600 module's own `build_xml` then IS the compact XML, and its
  `check()` measures the fonts it emits. An emitter map applied to already-compact styles would
  map twice.
- **The plan's "every file is CRLF" was wrong.** All the files are LF, measured with Python.
  Git Bash's `grep -c $'\r$'` matches every line and is not evidence of anything.
- **The card frame band is checked at `sc(band) - 1`, not the 30px 9-slice margin.** The frame
  art's ink reaches 10px in from an edge (`FRAME_INK`). The 30 was spacing, not a collision.
- **`check()` runs exactly at 1600, 1920 and 2560; the sweep covers the widths between.** At
  those in-between widths `check()`'s exact equalities, such as a heading's x equalling its
  column's, miss by 1px: a sum of separately scaled numbers rounds differently from the scaled
  sum. That pixel is inherent to integer scaling.
- **`SHARE_INK` and `HSORT_GAP` do not scale.** The first is how wide "100%" draws, which the
  font decides, and no font grows above 1920. The second mirrors `LABEL_TX`, a fixed
  "6.00,0.00" inset in the twui.
- **Seven values are derived, not scaled:** `COL_WH`, `COL_W`, `CARD_CREST`, `PARTY_CREST`,
  `HSORT_DY` and the two `*_MIN_SLICES` are rebuilt from the scaled cells in `apply_scale`. The
  harness asserts each derivation reproduces its typed value at 1920.
- **The pie is drawn at the wedge's own cell** (`PANEL_XY.ic_wedge_00`), not at
  `DIAL_CX - DIAL_R`. The two scale apart and can differ by a pixel.
- **The section label is resized at each of its two homes.** The generator always checked it at
  372px in the Crown's box, but the Lua never resized it.
- **`ICUI.CREST_INSET` is deleted.** It was defined and never read.
- **8d runs at 1920 too.** The loop-built entries and `PLOT_CHILD_XY` are excused from 8b's
  literal comparison, so before 8d nothing compared their widths and heights.
- **A failed `apply_scale` opens the panel at 1920 and logs why** (spec §4). `open()`'s outer
  pcall now logs its error text instead of dropping it.
- **The generator selftest takes about 13 minutes**, even with the compact XML cached per run.
  `--check` takes 15 seconds.

## 6. Gates, and the final review

| Gate | Result |
|---|---|
| `gen_ic_ui --check` | ok: 12 files, 444 components |
| `gen_ic_ui --selftest` | ok (12 files, 444 components, 1649 guids) |
| harness | ok (574 checks), each new one watched failing first or killing a mutant |
| `check_lua_api` | 0 findings on the three Iron Court scripts. The 9 in the whole pack are all in the Ghorth start scripts and `ai_test_tower_of_zharr.lua`, untouched here |
| `check_lua_undeclared` | clean over the whole pack |
| `preview_iron_court --check` / `--selftest` | pass. All six views are drawn at all three sizes |
| `make_ic_backdrop --check` | pass |
| `import_iron_court` | verify ok, 12 ui files |
| mutants | all 340 caught, 0 unexplained. 12 are new; see below |

**Two mutants survived when first written.**

- `sc` rounding down survived because every value the harness pinned is an exact multiple at
  its width. The harness now also pins `sc(20) = 17` at 1600 and `sc(2) = 3` at 2560.
- Vertical centring (`OY = 0`) survived because every `open()` the harness ran was 16:9 or
  wider. It now also opens at 1920x1200.

The seven 1080p `.twui.xml` files are byte-identical to before the change.

**A fresh reviewer (the strongest model available) read the whole change.**

- **What it tested:** it ran 8d's comparison at all 961 widths from 1600 to 2560, in mixed
  order, and found zero differences. It simulated `sc`, `fade` and `box_for` in float32 and
  found zero mismatches.
- **Its one Important finding:** 8d compared only the names the Lua *said* it scaled, so a
  layout value filed under `NOT_SCALED` passed every gate. Moving `ROW_H` there, for example,
  gave 61px rows on a 53px pitch at 1600. 8d now also checks:
  - that every name the generator scales is scaled or derived in the Lua;
  - every derived value, at every width, against the cells it comes from;
  - that no per-view width sits on a column that carries an override.
- **Four of its Minors were re-graded Important and fixed:**
  - the failed-scale fallback, which spec §4 requires;
  - the missing centring checks, which the plan's Review Focus names;
  - the previews covering every view, which spec §3 requires;
  - two comments stating the reversed grid rule, one of which would have led a maintainer to
    overlapping cards.
- **Deferred, not fixed:**
  - A 0x0 read opens the panel centred mostly off screen. That is "as today" per the spec.
  - Four draw-time resizes use scaled scalars and land up to 1px from the generator's cells.
  - 8d truncates a fractional Lua number instead of refusing it.
  - The sweep does not assert that no width dips below its measured end. Nothing dips today.

## 6b. Deployed

Built and deployed locally on 2026-09-24, with the game closed and RPFM open. It has **not** been
uploaded to the Workshop.

- `deploy_iron_court.py` re-ran every offline gate first and reported them green. It then
  saved the pack and verified all 1713 files in it.
- `derpy_iron_court.pack` is 8,859,564 bytes. Both copies have SHA-256 `b5ac9c81...14d479`:
  `Modding Files/Modpacks/` and the game's `data/`. This is the second deploy, with the two
  fixes in section 7b. The first build, `803336f8`, is superseded.
- The pack is ticked in `used_mods.txt`.
- Read back out of the deployed pack, all 15 script and UI files are byte-EQUAL to the
  workspace. That is the three scripts, the seven 1080p `.twui.xml` files and the five compact
  ones.

## 7. In-game checks owed

1. The author's 1600x900 window: all five tabs, nothing clipped, text one size smaller, and the
   log shows `k=0.833 compact=true`.
2. 1080p fullscreen at 100% looks exactly as it did before, and the log shows
   `k=1.000 compact=false`.
3. 1080p with UI Scale below 100% (reports up to 3840x2160): the box grows to 2560x1440,
   centred, **and the pie, the headers and the arrows sit inside it**. That is the section 4
   fix.
4. The logged `card_1` is about 303x153 at 1600. If it reads k squared times 364x184, the
   engine is still resizing children.
5. **Hover a tab, the close button and a card's APPOINT button at 1760 and at 2560.** Each
   button declares a width and height per state in its file. CA does not say whether `Resize`
   resizes every state or only the current one. If a button snaps to another size on hover,
   the fix is to resize again on the hover transition.
6. **The card frames and plates fill their cells at 1760 and 2560.** The frame and plate art
   is expected to stretch with a resized component. If it draws at the file's size instead,
   frames sit short of their card's edges.

## 7b. Two bugs the first in-game run found

The author opened the deployed build at 1600x900. Check 1's log line was right
(`box=1600x900 k=0.833 compact=true card_1=303x153`), so check 4 passed. Two faults showed.
Both were diagnosed live through the wh3 bridge.

**The Intrigue tab showed one move card per column, with its price and PLOT button in the
column header.** At runtime `ICUI.PLOT_H` was -9, and the load-time snapshot held -11. That
spaced the rows 3px apart and put the foot 36px above each card. Evaluated in game, line 459
`978 - 6 - ICUI.PLOTS_Y` ran as 226 - 226.

- **Cause:** the game's Lua compiler is not stock 5.1.5. In a function with over 255
  constants, a number literal on the left of an arithmetic operator is loaded into a
  register that the right operand then overwrites. Measured: `2 * ICUI.PLOT_PAD` gave 900,
  `ICUI.PLOT_PAD * 2` gave 60, and `2 * pad` with a local was correct. Stock `lua.exe` gets
  every case right, which is why the harness and 8d were green.
- **Why it appeared now:** the `{x, y, w, h}` tables pushed the panel's main chunk past 255
  constants.
- **Fix:**
  - the four literal-left sites in the panel Lua are rewritten;
  - the new `tools/check_lua_literal_left.py` reads stock `luac -l` bytecode for the shape,
    `LOADK` then an arithmetic op using it as its LEFT operand. It excludes a `LOADK` right
    after a `JMP`, which is the `(x or 0)` fallback and correct code;
  - `import_iron_court` gate 8a refuses on a hit.

  Across all 16 shipped campaign scripts, the only sites were these four.

**Thin light lines crossed the dial and Crown boxes and ran down every move card. CAUSE NOT
FOUND.** They are light grey, 1px, and measured at 1600:

- **Court view:** a vertical line at x≈263, from the dial box top to the Crown box bottom, and
  a horizontal line at y≈374 across the whole left column, including over the frame border.
- **Intrigue view:** vertical lines at x≈266, 667 and 1067. The first two run past the move
  cards and over bare backdrop.

The first theory was seams in the plates' tiled fill. CA's `panel_back_tile.png` is a 4px
alpha-0 ring round a flat rgb(11,11,11) field, nine-sliced at margin 4 with `tile="true"`. That
theory predicts lines at plate edge + 252px, which is close to what was seen. **The evidence
refutes it:**

- a fill seam cannot cross an opaque frame or appear over bare backdrop;
- a bilinear model of the engine at 0.8 scale (`seam_model.py`, scratch) draws the seam
  DARKER, 8.5 against 11, not lighter.

The fill now stretches instead of tiling anyway, since that is the same picture with no seams.
Check 18b holds it, so it is hygiene, not a fix. The preview cannot find the cause either: at
1600 it draws no lines, so whatever draws them is runtime-only.

**Next step:** with the game running and the court open, enumerate every visible component
through the bridge. Keep any whose box has an edge on x≈263 or y≈374 in the court view, and on
x≈266 or 667 in the intrigue view.

## 8. Not done

- Text never grows above its base size, so a 2560 box is CA-size text in bigger boxes and reads
  airy. A "large" font set above about 2240 would be a second copy of each file, built the way
  the compact copies are.
- There is no listener for a UI Scale change while the panel is open. It rescales on the next
  open.
- The art is not redrawn at 2560; it is stretched by the engine.
- Two tight spots are identical at 1920 and 1600, so they predate this change: a party card's
  second trait line on the mood plate's top edge, and a four-line blurb touching the PLOT plate.
