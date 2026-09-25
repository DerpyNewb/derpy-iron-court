# Iron Court UI scale - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** the Iron Court panel fits every UI area from 1600x900 to 2560x1440 by scaling today's
1920x1080 layout by an integer rule, with compact-font copies of the panel files below 1920.

**Architecture:** today's layout stays the BASE in both `tools/gen_ic_ui.py` and
`zzz_derpy_iron_court_ui.lua`. The generator gains `at_box(bw)`, a fresh copy of itself with
every layout global scaled, which it checks at 1600 as well as 1920. The Lua gains
`ICUI.apply_scale(bw)`, which rebuilds every scaled value from a load-time snapshot at each open.
`import_iron_court.py` proves the two agree by running the Lua under lua.exe.

**Tech Stack:** WH3 campaign Lua 5.1 (float32 numbers), Python 3 generator and gates, stock Lua
5.1.5 harness, RPFM MCP for packing.

**Spec:** `docs/superpowers/specs/2026-09-24-iron-court-ui-scale-design.md`

## Global Constraints

- Box: `BW = clamp(floor(min(sw, sh * 16 / 9)), 1600, 2560)`, `BH = floor(BW * 9 / 16)`.
- Scale: `sc(v) = floor((v * BW + 960) / 1920)`. No float factor anywhere in the Lua.
- A box `(x, y, w, h)` becomes `(sc(x), sc(y), sc(x + w) - sc(x), sc(y + h) - sc(y))`; a lone
  scalar becomes `sc(v)`.
- Compact iff `BW < 1920`. Font map: header_24_bold to header_20_bold, header_20_bold to
  header_18_bold, header_18_bold to header_16_bold, header_18 to header_16, header_16 to
  header_14, body_12 to body_10; the size follows the category.
- Overrides: `(dx, dy, dw, dh)` in screen pixels at 1600, applied as
  `floor((d * (1920 - BW) + 160) / 320)` when `BW < 1920`, else 0.
- Not scaled: counts, the HUD opener, the influence-bar plate (`derpy_ic_standing`), source-art
  sizes.
- Every file edited here is CRLF: edit with the Edit tool only, never a rewrite via a shell.
- No emojis. Never say "rung". Player text never says "governor" or "standing".
- Never diff, build or deploy while `tools/mutate_iron_court.py` runs.
- Deploy only with the game closed and RPFM open. The workspace is not a git repo, so "commit"
  steps are "run the gates".

## Review Focus

- A root that reads 1280x720 or 0x0 on an early open: box clamps to 1600x900 and the panel
  still opens (harness box table, Task 4).
- Opening at 2560 and then at 1600 in one session: every value is exactly the 1600 one, not
  1600-of-2560 (harness "apply_scale twice", Task 4).
- A cell whose base value is added after this change and never classified: the completeness
  rules refuse on both sides (Task 1 selftest, Task 4 harness).
- 16:10 1920x1200 and ultrawide 5120x1440: height-led box, centred (harness box table, Task 4).
- The row pool on the governors view at 1600: rows stay above the pager (Task 3's small-end
  check, check 15 at 1600).

---

### Task 1: The scale model in the generator

**Files:**
- Modify: `tools/gen_ic_ui.py` (top: `BOX_W`; after `LAYOUT_TABLES`: the scale pass; `main()`;
  `selftest()`)

**Interfaces:**
- Produces: `sc(v, bw)`, `sc_box(box, bw)`, `box_for(sw, sh)` returning `(bw, bh)`,
  `at_box(bw)` returning a module object, `SCALED_SCALARS`, `SCALED_TABLES`, `NOT_GEOMETRY`,
  `COMPACT_FONTS`, `COMPACT_OVERRIDES` (empty in this task), `COMPACT` (bool), `BOX_W` (int).

- [ ] **Step 1: Selftest assertions first**

```python
    # THE SCALE MODEL. The Lua does the same arithmetic in integers and
    # import_iron_court.py runs it to prove the two agree.
    assert sc(1854, 1600) == 1545 and sc(1854, 1920) == 1854 and sc(1854, 2560) == 2472
    assert sc_box((18, 1018, 1884, 44), 1600) == (15, 848, 1570, 37)
    assert box_for(1600, 900) == (1600, 900) and box_for(1280, 720) == (1600, 900)
    assert box_for(1920, 1200) == (1920, 1080) and box_for(5120, 1440) == (2560, 1440)
    assert box_for(3840, 2160) == (2560, 1440) and box_for(2560, 1080) == (1920, 1080)
    _s = at_box(1600)
    assert _s.COMPACT and not COMPACT
    assert _s.PANEL_LAYOUT["ic_close"] == sc_box(PANEL_LAYOUT["ic_close"], 1600)
    assert _s.ROW_PITCH == sc(ROW_PITCH, 1600) and _s.VISIBLE_ROWS == VISIBLE_ROWS
    assert _s.TEXT_STYLE["ic_card_name"] == (14, "header_14")
    assert at_box(1920).PANEL_LAYOUT == PANEL_LAYOUT
```

(`sc_box((18,1018,1884,44),1600)`: sc(18)=15, sc(1018)=848, sc(1902)=1585 so w=1570,
sc(1062)=885 so h=37.)

- [ ] **Step 2: Run `py tools/gen_ic_ui.py --selftest`**, expect NameError on `sc`.

- [ ] **Step 3: Implement.** Near the top, after the imports:

```python
# THE BOX THIS COPY OF THE MODULE DESCRIBES. 1920 is the base layout - every
# number below is typed for it. at_box() executes a fresh copy with another
# width injected, and the scale pass at the end of the layout section rewrites
# every layout global the way ICUI.apply_scale does in game.
BOX_W = globals().get("_BOX_W", 1920)
COMPACT = BOX_W < 1920


def sc(v, bw):
    """One layout number at box width bw. Integers only: game Lua is float32."""
    return (v * bw + 960) // 1920


def sc_box(box, bw):
    x, y, w, h = box
    return (sc(x, bw), sc(y, bw), sc(x + w, bw) - sc(x, bw), sc(y + h, bw) - sc(y, bw))


def box_for(sw, sh):
    bw = max(1600, min(2560, int(min(sw, sh * 16 / 9.0))))
    return bw, bw * 9 // 16


def at_box(bw):
    import importlib.util
    spec = importlib.util.spec_from_file_location("gen_ic_ui_at_%d" % bw, __file__)
    mod = importlib.util.module_from_spec(spec)
    mod.__dict__["_BOX_W"] = bw
    spec.loader.exec_module(mod)
    return mod
```

After `LAYOUT_TABLES` (the last module-level layout definition), the scale pass. The lists are
filled by reading every module global the layout section defines; the pass refuses on any
int or int container in neither list.

```python
COMPACT_FONTS = {
    "header_24_bold": (20, "header_20_bold"), "header_20_bold": (18, "header_18_bold"),
    "header_18_bold": (16, "header_16_bold"), "header_18": (16, "header_16"),
    "header_16": (14, "header_14"), "body_12": (10, "body_10"),
}
COMPACT_OVERRIDES = {}      # name -> (dx, dy, dw, dh) in screen px at BW 1600
SCALED_SCALARS = [...]      # every scalar layout global, found in Step 3b
SCALED_TABLES = [...]       # every dict of name -> box, and every list of boxes / points
NOT_GEOMETRY = [...]        # counts, source-art sizes, tolerances, the opener and plate


def _override(d, bw):
    return (d * (1920 - bw) + 160) // 320 if bw < 1920 else 0


def _scale_pass(g, bw):
    ...   # scalars -> sc(); dict tables -> sc_box per entry, then overrides;
          # list tables -> sc per element; text styles -> COMPACT_FONTS when bw < 1920;
          # refuse on an unclassified int or int container.

if BOX_W != 1920:
    _scale_pass(globals(), BOX_W)
```

Step 3b: list every module-level name in the layout section (lines 45-1000 and the text-style
block) whose value is an int or holds ints, and put each in exactly one of the three lists.
Point lists (`CARD_GRID`, the party and plot grids) scale per coordinate with `sc`; box tables
scale per entry with `sc_box`.

- [ ] **Step 4: `check()` at the small end.** In `main()`, after `problems = check()`, add
  `problems += ["at 1600x900: " + p for p in at_box(1600).check()]`. Inside `check()`, guard
  every check that reads art on disk (the wedge drift, the plate files, check 21b/21c) with
  `if BOX_W == 1920:`. Run `py tools/gen_ic_ui.py --check` and save the list of 1600 failures
  to the scratchpad. It is Task 3's input.

- [ ] **Step 5: Run `--selftest`.** Expect PASS. `--check` fails only with `at 1600x900:` lines.

### Task 2: Compact copies of the five in-panel files

**Files:**
- Modify: `tools/gen_iron_court_emitter.py:195-224` (the text block), `tools/gen_ic_ui.py`
  (`GUID_PREFIXES`, `FILES` consumers, `build_xml`, `write_ui`), `tools/import_iron_court.py:40`

**Interfaces:**
- Consumes: `COMPACT_FONTS`, `at_box` (Task 1).
- Produces: `COMPACT_FILES` (the five names with `_compact` before `.twui.xml`),
  `ui_file_names()` (all twelve), `build_xml()` returning base and compact texts, and
  `EU.FONT_MAP` (None, or a map category -> (size, category)).

- [ ] **Step 1: Selftest assertions**

```python
    _x = build_xml()
    assert "derpy_ic_panel_compact.twui.xml" in _x and len(_x) == 12
    assert 'fontcat_name="header_18"' not in _x["derpy_ic_row_compact.twui.xml"]
    assert 'fontcat_name="header_16"' in _x["derpy_ic_row_compact.twui.xml"]
    assert "derpy_ic_opener_compact.twui.xml" not in _x
```

- [ ] **Step 2: Emitter.** In the text block, replace the size and category arguments:

```python
                   _font(kw)[0],
                   kw.get("colour", "#FFF8D7FF"), kw.get("leading", 3),
                   _font(kw)[1]))
```

with, above the function:

```python
# SET BY THE CALLER for one build: the compact copies of a panel are the same
# components one CA size step down. None is the base. An unmapped category is
# a refusal, never a fallback - a category left at its base size in a compact
# file is text that clips at 1600x900 with every check green.
FONT_MAP = None


def _font(kw):
    cat = fontcat(kw)
    if FONT_MAP is None:
        return kw.get("size", 12), cat
    assert cat in FONT_MAP, "no compact size for %r" % cat
    return FONT_MAP[cat]
```

- [ ] **Step 3: Generator.** Compact prefixes `IC40`..`IC44` for panel, card, row, party, plot.
  `build_xml()` builds `FILES` as today, then for the five in-panel builders it runs
  `at_box(1600)`'s builders with `EU.FONT_MAP = COMPACT_FONTS` (reset to None in a `finally`) and
  names the result `<name>_compact.twui.xml`. `write_ui()` writes all twelve.
  `ui_file_names()` returns the twelve names. `import_iron_court.UI_FILES` reads
  `_U.ui_file_names()`.

- [ ] **Step 4: Run** `py tools/gen_ic_ui.py --selftest` and `--check`. The 1600 failures from
  Task 1 remain; nothing new.

### Task 3: Make the small end pass, and the sweep

**Files:**
- Modify: `tools/gen_ic_ui.py` (`COMPACT_OVERRIDES`, a new `check_scale_sweep()`, called from
  `main()`)

**Interfaces:**
- Produces: `COMPACT_OVERRIDES` populated; `check_scale_sweep()` returning a list of problems.

- [ ] **Step 1: The sweep, failing first.** `check_scale_sweep()` walks `bw` from 1600 to 2560
  in steps of 1. It builds the scaled boxes with the Task 1 rule plus faded overrides (plain
  arithmetic, not `at_box`), in every table of `LAYOUT_TABLES` except opener and standing.
  It asserts:
  - every panel cell is inside `(0, 0, bw, bw * 9 // 16)`;
  - every child is inside its parent's scaled size;
  - two cells in one frame that do not overlap at the base do not overlap at `bw`;
  - every office, party and move card child ends at least `sc(30, bw) - 1` inside its card's
    edge.

  It stops at the first failing `bw` per rule, so the output stays short.
- [ ] **Step 2: Overrides.** For each `at 1600x900:` failure from Task 1, choose the smallest
  delta that clears it without breaking a neighbour, add it to `COMPACT_OVERRIDES` with a
  comment naming the string or the rule that forced it, and re-run `--check`. Order:
  1. list columns (widths only, taken from a neighbour's slack);
  2. party-card rows (y deltas);
  3. office-card cells;
  4. move-card blurbs and names.

  If a card's content cannot fit its 1600 box by overrides alone, the override may also change
  the card size and the grid's y. Record the decision in the comment.
- [ ] **Step 3:** `py tools/gen_ic_ui.py --check` exits 0 with no `at 1600x900:` lines, and the
  sweep reports nothing.

### Task 4: The Lua scales at open

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua` (layout block
  lines 180-620, `ICUI.resize` ~1977, `ICUI.layout` ~1138, `ICUI.open` ~4744)
- Test: `tools/_iron_court_harness.lua` (new checks beside the existing layout-offset checks)

**Interfaces:**
- Consumes: the generator's tables (mirrored by hand, compared by Task 5).
- Produces: `ICUI.sc(v)`, `ICUI.box_for(sw, sh)` -> `bw, bh`, `ICUI.apply_scale(bw)`,
  `ICUI.BW`, `ICUI.COMPACT`, `ICUI.BASE`, `ICUI.SCALED`, `ICUI.SCALED_TABLES`,
  `ICUI.NOT_SCALED`, `ICUI.COMPACT_OVERRIDES`, and `ICUI.path(base_path)`, which returns the
  compact path when `ICUI.COMPACT`.

- [ ] **Step 1: Harness checks, failing first**

```lua
check("the box follows the screen and clamps to 1600..2560", function()
    local cases = {{1280, 720, 1600, 900}, {1600, 900, 1600, 900}, {1920, 1080, 1920, 1080},
                   {1920, 1200, 1920, 1080}, {2560, 1080, 1920, 1080},
                   {2560, 1440, 2560, 1440}, {3840, 2160, 2560, 1440},
                   {5120, 1440, 2560, 1440}, {0, 0, 1600, 900}}
    for _, c in ipairs(cases) do
        local bw, bh = ICUI.box_for(c[1], c[2])
        assert(bw == c[3] and bh == c[4], c[1] .. "x" .. c[2] .. " gave " .. bw .. "x" .. bh)
    end
end)

check("sc is the generator's integer rule", function()
    ICUI.BW = 1600
    assert(ICUI.sc(1854) == 1545 and ICUI.sc(18) == 15 and ICUI.sc(1902) == 1585)
    ICUI.BW = 2560
    assert(ICUI.sc(1854) == 2472)
    ICUI.apply_scale(1920)
end)

check("apply_scale twice lands exactly on the second size", function()
    ICUI.apply_scale(2560)
    ICUI.apply_scale(1600)
    local want = ICUI.BASE.PANEL_XY.ic_close
    local got = ICUI.PANEL_XY.ic_close
    assert(got[1] == ICUI.sc(want[1]) and got[3] == ICUI.sc(want[1] + want[3]) - ICUI.sc(want[1]),
        "compounded: " .. got[1] .. "," .. got[3])
    assert(ICUI.ROW_PITCH == ICUI.sc(ICUI.BASE.ROW_PITCH))
    ICUI.apply_scale(1920)
    assert(ICUI.PANEL_XY.ic_close[1] == 1854 and ICUI.ROW_PITCH == 64)
end)

check("overrides fade from full at 1600 to nothing at 1920", function()
    local saved = ICUI.COMPACT_OVERRIDES
    ICUI.COMPACT_OVERRIDES = {ic_alert = {0, 0, -32, 0}}
    ICUI.apply_scale(1600)
    local full = ICUI.PANEL_XY.ic_alert[3]
    ICUI.COMPACT_OVERRIDES = {}
    ICUI.apply_scale(1600)
    assert(full == ICUI.PANEL_XY.ic_alert[3] - 32, "not full at 1600")
    ICUI.COMPACT_OVERRIDES = {ic_alert = {0, 0, -32, 0}}
    ICUI.apply_scale(1920)
    assert(ICUI.PANEL_XY.ic_alert[3] == 1884, "not zero at 1920")
    ICUI.COMPACT_OVERRIDES = saved
    ICUI.apply_scale(1920)
end)

check("every number in ICUI is classified as scaled or not", function()
    local known = {}
    for _, n in ipairs(ICUI.SCALED) do known[n] = true end
    for _, n in ipairs(ICUI.SCALED_TABLES) do known[n] = true end
    for _, n in ipairs(ICUI.NOT_SCALED) do known[n] = true end
    for k, v in pairs(ICUI) do
        local numeric = type(v) == "number"
        if type(v) == "table" then
            for _, e in pairs(v) do
                if type(e) == "table" and type(e[1]) == "number" then numeric = true end
            end
        end
        assert(not numeric or known[k], "ICUI." .. k .. " is neither scaled nor declared not")
    end
end)

check("the compact files are used below 1920 and only there", function()
    ICUI.apply_scale(1600)
    assert(ICUI.path(ICUI.PATH_ROW) == ICUI.PATH_ROW .. "_compact")
    ICUI.apply_scale(1920)
    assert(ICUI.path(ICUI.PATH_ROW) == ICUI.PATH_ROW)
end)

check("resize never resizes children", function()
    local c = fake_component("x")
    local third = "unset"
    c.Resize = function(self, w, h, children) third = children end
    ICUI.resize(c, 10, 10)
    assert(third == false, "Resize was called with children " .. tostring(third))
end)
```

Also extend the existing fake-panel open check to a 1600x900 root. It asserts that the panel is
created from `derpy_ic_panel_compact`, that every child `layout()` moves is also resized, and
that the log line carries `box=1600x900`.

- [ ] **Step 2: Run** `& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua`
  and expect the new checks to fail on `ICUI.box_for`.

- [ ] **Step 3: Implement.**
  1. The tables become `{x, y, w, h}`, sizes copied from the generator's tables, and the loop
     entries get their sizes from the constants (a wedge or divider is
     `{DIAL_CX - DIAL_R, DIAL_CY - DIAL_R, 2 * DIAL_R, DIAL_R}`, a crest
     `{x, y, CREST_PX, CREST_PX}`, a share `{sx, sy, SHARE_W, SHARE_H}`, a heading
     `{x, PLOTS_HDR_Y, PLOT_W, PLOTS_HDR_H}`).
  2. At the end of the block:

```lua
-- THE SCREEN'S SHARE OF THE LAYOUT. Everything above is typed for a 1920 box.
-- apply_scale rebuilds every scaled value from BASE at each open, so a second
-- open at another size never scales an already scaled number.
ICUI.BW = 1920
ICUI.COMPACT = false
function ICUI.sc(v)
    return math.floor((v * ICUI.BW + 960) / 1920)
end
function ICUI.box_for(sw, sh)
    local bw = math.floor(math.min(sw or 0, (sh or 0) * 16 / 9))
    if bw < 1600 then bw = 1600 elseif bw > 2560 then bw = 2560 end
    return bw, math.floor(bw * 9 / 16)
end
ICUI.SCALED = {...}          -- scalar names
ICUI.SCALED_TABLES = {...}   -- box tables and point lists
ICUI.NOT_SCALED = {...}
ICUI.COMPACT_OVERRIDES = {}
ICUI.BASE = {}
for _, n in ipairs(ICUI.SCALED) do ICUI.BASE[n] = ICUI[n] end
for _, n in ipairs(ICUI.SCALED_TABLES) do ICUI.BASE[n] = ICUI.copy_table(ICUI[n]) end
```

  3. `ICUI.apply_scale(bw)` sets `BW` and `COMPACT`, restores each scalar as `sc(BASE[n])`, and
     rebuilds each table from `BASE` by the box rule with the faded override added to x, y, w
     and h. Point lists scale per coordinate. It refreshes `ICUI.SHARE_MIN_SLICES`, which is
     derived.
  4. `ICUI.resize` calls `c:Resize(w, h, false)`.
  5. `ICUI.layout()` resizes each cell it moves, from entries 3 and 4.
  6. `ICUI.open()`:
     - `local bw, bh = ICUI.box_for(sw, sh)`, then `ICUI.apply_scale(bw)` inside the existing
       pcall;
     - resize the panel to `max(sw, bw) x max(sh, bh)` and move it to `0, 0` when the screen is
       at least the box, or centre it otherwise;
     - `ICUI.OX = floor((pw - bw) / 2)`, `ICUI.OY = floor((ph - bh) / 2)`;
     - create every component from `ICUI.path(...)`;
     - log `layout box=%dx%d k=%.3f compact=%s card_1=%dx%d`, with the card size read back
       from `Dimensions()`.
  7. Classify every remaining `ICUI` number and tuple table, as the completeness check demands.
     Then audit the 19 `MoveTo` sites and every `ICUI.resize` call site for a bare layout
     literal (a gap such as `+ 8` is fine; a position or size is not): each one found either
     moves into a scaled constant or gets a comment saying why it stays.

- [ ] **Step 4: Run** the harness, expect all checks green. Run
  `& "C:\Program Files (x86)\Lua\5.1\luac.exe" -p` on the file, `py tools\check_lua_api.py` and
  `py tools\check_lua_undeclared.py`.

### Task 5: The packing gate proves the two sides agree

**Files:**
- Modify: `tools/import_iron_court.py` (8b at ~865, the constant list at ~1076, 8c, a new 8d)

- [ ] **Step 1:** 8b reads `{x, y, w, h}`: extend the regex to four integers and compare the
  full tuple.
- [ ] **Step 2:** New 8d. Under lua.exe, load the model, the UI Lua and a stub `IC` as 8c does,
  call `ICUI.apply_scale(bw)` for `bw` in 1600, 1760 and 2560, and print every entry of every
  table in `ICUI.SCALED_TABLES` plus the pinned constants. Then compare against
  `U3.at_box(bw)`'s tables entry by entry and refuse on any difference. Also compare
  `ICUI.COMPACT_OVERRIDES` to `U3.COMPACT_OVERRIDES`, and the Lua's `ICUI.path` suffix to the
  compact file names.
- [ ] **Step 3:** Break one number in the Lua's `COMPACT_OVERRIDES` in memory (a string replace
  on the text 8d reads, not on disk), confirm 8d refuses, and put it back. Run
  `py tools\import_iron_court.py --verify-only` (or the script's existing no-pack mode), which
  must exit 0.

### Task 6: Preview and backdrop at three sizes

**Files:**
- Modify: `tools/preview_iron_court.py` (canvas from the module passed in; a `--size` loop),
  `tools/make_ic_backdrop.py` (contrast at 1600 too)

- [ ] **Step 1:** The preview takes the module to draw from (`G = gen_ic_ui.at_box(bw)` for
  1600 and 2560, the base for 1920). It reads fonts from that module's XML, compact at 1600.
  It writes `ic_court_<bw>.png` and `ic_intrigue_<bw>.png`, and keeps `ic_court.png` and
  `ic_intrigue.png` as the 1920 pair so existing references hold. `--check` and `--selftest`
  run all three sizes.
- [ ] **Step 2:** `make_ic_backdrop.check()` also measures every text cell of `at_box(1600)`
  against the backdrop resized to 1600x900 with the same resampling, at the same 4.5:1.
- [ ] **Step 3:** Run both with `--check` and `--selftest`, and open the three court PNGs to
  look for dead space, a clipped heading or a card that reads badly.

### Task 7: Mutants, full gates, deploy, write-up

**Files:**
- Modify: `tools/mutate_iron_court.py` (new mutants, target U), `docs/sessions/HANDOFF_20260924_IRON_COURT_UI_SCALE.md` (new),
  `docs/SESSION_INDEX.md` (one line)

- [ ] **Step 1: Mutants** (each anchored on a code line):
  1. the box read off the width alone;
  2. no clamp at 1600;
  3. `sc` without the `+ 960`;
  4. overrides not faded (full at every size);
  5. compact at 1920;
  6. `Resize(w, h)` without `false`;
  7. `apply_scale` reading the live value instead of `BASE`.

  Run `py tools\mutate_iron_court.py --selftest`, then
  `py tools\mutate_iron_court.py "box" "clamp" "compact" "fade" "compound" "children" "half"`.
  Expect 0 unexplained.
- [ ] **Step 2: Full gates.**
  - `gen_ic_ui --check/--selftest`
  - harness
  - `check_lua_api`
  - `check_lua_undeclared`
  - `preview_iron_court --check/--selftest`
  - `make_ic_backdrop --check`
  - `import_iron_court` verify

  All green, with the outputs saved to the scratchpad.
- [ ] **Step 3: Deploy.** Confirm the game is closed and RPFM is up, then run `py tools\gen_ic_ui.py`,
  `py tools\gen_iron_court.py` and `py tools\deploy_iron_court.py`. Read back the SHA-256 of both
  copies, the tick in `used_mods.txt`, and every script and UI file EQUAL.
- [ ] **Step 4: Write-up.**
  - The handoff: what was measured, the rule, the overrides with their reasons, the gates,
    and the four in-game checks from spec section 5.
  - One line in `SESSION_INDEX.md`.
  - A memory if something new about the engine was learned.
