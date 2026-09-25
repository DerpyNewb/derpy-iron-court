# The Iron Court panel scales with the screen - design

2026-09-24. Approved in conversation section by section; the author said "approve then build it".

## 1. The complaint and what the engine does

The author, playing in a window, saw the panel clipped on all four sides. The log showed the
panel at `-160,-90`: a 1920x1080 layout centred on a 1600x900 UI area.

- The screen a script sees is the window divided by UI Scale, floored at 1600x900
  (`HANDOFF_20260924_GUILDS_UI_SCALE.md` section 1, measured on this machine: a 1280x720 window
  reports 1600x900). So a script never sees less than 1600x900, and a 4K player at 100% sees
  3840x2160.
- `PANEL_W, PANEL_H = 1920, 1080` in `tools/gen_ic_ui.py` (hand-mirrored in
  `zzz_derpy_iron_court_ui.lua`). `ICUI.open` grows the panel on a bigger screen and centres the
  content, but a smaller screen gets negative offsets and loses 160px each side.
- There is no script call that sets a font size or a UI scale (`DevSetUiScale` is dev-only).
  Text size is fixed by each cell's `fontcat_name` in the `.twui.xml`.
- Measured with the generator's own `check()` at 1600x900, edge cells already anchored: 64
  failures. They sit in the office cards, the party cards, the move cards and the list
  columns. The court tab's dial and Crown's box fit.

## 2. The rule

Today's 1920x1080 layout is the single source, the BASE, and is not edited. At open:

- **Box.** `BW = clamp(floor(min(sw, sh * 16 / 9)), 1600, 2560)`, `BH = floor(BW * 9 / 16)`,
  from the root's `Dimensions()`. The panel is resized to `max(sw, BW) x max(sh, BH)`, so the
  backdrop still covers the screen, and the box is centred in it (`ICUI.OX`, `ICUI.OY`).
- **Scale, in integers.** Game Lua is float32, so there is no float factor:
  `sc(v) = floor((v * BW + 960) / 1920)`. Every product stays under 2^24.
- **What scales.** Every layout number:
  - positions, sizes and pads in every frame (panel, row, office card, party card, move card);
  - the dial's centre, radius, crest and share rings;
  - the row pitch and the per-view column widths;
  - the portrait and crest cell sizes.

  A box `(x, y, w, h)` in a frame becomes `(sc(x), sc(y), sc(x + w) - sc(x), sc(y + h) - sc(y))`,
  so cells that touch at the base still touch. A lone scalar becomes `sc(v)`.
- **What does not scale.** Counts: slices, houses, rows in the pool, tiers, blurb lines. Also
  the HUD opener and the influence-bar plate beside CA's character panel, and source-art
  sizes such as the porthole's 300x164.
- **Rows.** The pool stays `MAX_ROWS` (12); rows grow taller rather than more numerous. The
  author accepted this trade.
- **Text below 1920 (`BW < 1920`, called compact).** The panel is created from compact copies of
  the five in-panel files (panel, row, card, party, plot). They are identical except every text
  cell is one CA size step down:

  | Base | Compact |
  |---|---|
  | header_24_bold | header_20_bold |
  | header_20_bold | header_18_bold |
  | header_18_bold | header_16_bold |
  | header_18 | header_16 |
  | header_16 | header_14 |
  | body_12 | body_10 |

  `font_m_size` follows the category. From `BW >= 1920` the base files and text are used
  unchanged. So a 1080p player sees exactly today's panel, and above 1080p only the boxes grow.
- **Overrides at the small end.** Text shrinks about 11% and boxes 17%, so a few cells may still
  fail at 1600x900. `COMPACT_OVERRIDES` holds, per cell, a delta `(dx, dy, dw, dh)` in screen
  pixels at `BW = 1600`. It is applied as `floor((d * (1920 - BW) + 160) / 320)`: full at 1600,
  zero at 1920, and never above 1920. Each entry carries a comment naming the string that forced
  it. The table starts empty and only the small-end check may add to it.
- **Why the two ends are enough.** Each scaled edge is a monotone function of BW, and each
  overridden edge a straight line in BW. So a gap that is open at 1600 and at 1920 (or at 1920
  and 2560) is open between. Text that fits at both ends of a range fits between, because the
  font is fixed within each range and widths only move one way. A sweep in Python over every
  BW, one pixel at a time, backs this up against rounding.

## 3. Where it lives

- **`tools/gen_ic_ui.py`**
  - `BOX_W` (default 1920) is injected by `at_box(bw)`, which executes a fresh copy of the
    module. After the layout section, a scale pass rewrites every layout global by the rule
    above and applies the faded overrides.
  - `COMPACT = BOX_W < 1920` switches `style()`'s font map.
  - A completeness rule: every int-valued or int-container global the layout section defines
    is either in `SCALED` or in `NOT_GEOMETRY`, or the scale pass refuses.
  - `check()` runs at `BOX_W = 1920` as today and again at 1600. Checks of the art on disk run
    at 1920 only, because the art is not redrawn.
  - A new `check_scale_sweep()` walks BW 1600..2560 and checks every cell inside the box,
    no new overlaps, and every card child clear of its card's band.
  - `build_xml` emits the five compact files with their own GUID prefixes.
- **`zzz_derpy_iron_court_ui.lua`**
  - The layout tables become `{x, y, w, h}`. The loop-built entries (wedges, dividers, crests,
    shares, move-category headings, the three card grids) gain their sizes from the same
    constants.
  - `ICUI.BASE` is a snapshot of every scaled value, taken at load. `ICUI.apply_scale(bw)`
    rebuilds the scaled values from `BASE` at every open, so opening at 2560 and then at 1600
    never compounds. `ICUI.layout()` resizes each cell it moves.
  - `ICUI.resize` passes `Resize(w, h, false)`, because CA's default resizes children too, and
    every child is now sized explicitly.
  - `ICUI.open` computes the box and chooses the compact paths.
  - One log line per open: `layout box=BWxBH k=... compact=true|false card_1=WxH`, with the
    card size read back from the engine.
  - A completeness rule in the harness: every number-valued `ICUI` field is in `ICUI.SCALED`
    or `ICUI.NOT_SCALED`, and every table of number tuples in `ICUI.SCALED_TABLES` or
    `ICUI.NOT_SCALED`.
- **`tools/import_iron_court.py`**
  - Gate 8b compares all four numbers per entry.
  - It runs the Lua's `apply_scale` under lua.exe at BW 1600, 1760 and 2560 and compares every
    scaled table entry and pinned constant to the generator's `at_box(bw)`.
  - It compares `COMPACT_OVERRIDES` and the compact font map.
  - It packs the five compact files.
- **`tools/preview_iron_court.py`** draws each view at 1600x900, 1920x1080 and 2560x1440.
- **`tools/make_ic_backdrop.py`** measures contrast at BW 1600 as well. On a 16:9 screen the
  backdrop and the box scale together, so the other sizes sit over the same pixels.
- **`tools/_iron_court_harness.lua`**
  - The box at 1280x720, 1600x900, 1920x1080, 1920x1200, 2560x1080, 2560x1440, 3840x2160
    and 5120x1440.
  - `sc` against hand values.
  - `apply_scale` twice in a row at two sizes, landing exactly on the second.
  - The overrides' weight at 1600, 1760 and 1920.
  - `layout()` at 1600 resizing every cell it moves with `false` as the third argument.
  - The compact paths chosen below 1920 only.
  - The completeness rule.
- **`tools/mutate_iron_court.py`** gains mutants for the new rules: box off the width alone,
  no clamp, float factor, overrides not faded, compact at 1920, children resized, and
  `apply_scale` compounding.

## 4. Edge cases

- **A screen reported below 1600x900** (a bad early read): the box clamps to 1600x900 and is
  centred, as today.
- **16:10 and ultrawide screens:** the box follows the shorter side. The backdrop stretches as
  it does today, and contrast is only measured for 16:9.
- **UI Scale or resolution changed with the panel open:** the next open picks it up. No listener.
- **Art** (wedges, rim, plates, portholes) stays at its current size and the engine scales it:
  slightly soft at 2560, fine at 1600.
- **Live-measured text** (sort arrows, name cuts) is already correct at any size.
- **`apply_scale` failing:** it runs inside `open`'s pcall. The panel opens at the base, as
  today, and logs the error.

## 5. In-game checks owed

1. The author's 1600x900 window: all five tabs, nothing clipped, text one size smaller, log
   `k=0.833 compact=true`.
2. 1080p fullscreen at 100%: identical to today, log `k=1.000 compact=false`.
3. 1080p at UI Scale below 100% (reports up to 3840x2160): the box grows to 2560x1440, centred.
4. The logged `card_1` size is about 303x153 at 1600 (k times 364x184, plus any override). If it
   reads k squared times that, the engine is still resizing children.

## 6. Not done

- Text never grows above the base size; a big screen gets bigger boxes with CA-size text.
- No listener for UI Scale changes.
- Art is not redrawn at 2560.
