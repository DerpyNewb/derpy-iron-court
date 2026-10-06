# Iron Court for Dwarfs - Phase 3: Dwarf UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Dwarf player opens a court that looks like a Dwarf hall and not like the Ziggurat of Zharr: the Book of Grudges kit (blue ribbon tabs with a gold lit tab, the knotwork frame, the stone lintel, the knot rule under the headings) on a dimmed Dwarf loading-screen painting, the fourteen seats in layout E's 5x4 grid with the throne in the middle of the top row, the title "The Council of <faction>", the offices heading "THE GREAT HALL", and the throne naming the faction and its king. The Chaos Dwarf court stays byte for byte what it is today.

**Architecture:** The generator becomes race-aware the way it is already box-aware: `at_box(bw, race)` re-executes `tools/gen_ic_ui.py` with `_RACE` injected beside `_BOX_W`, so a Dwarf copy has its own layout, layer lists and checks. The panel-level art differs in geometry (the title and heading caps are twui margins, 111 -> 150 and 34 -> 80), so the Dwarf panel is its own file pair, `derpy_ic_panel_dwf.twui.xml` (GUID IC60) and `derpy_ic_panel_dwf_compact.twui.xml` (IC61), carrying every panel-level Dwarf picture baked to size. The pooled files (card, party, plot, law) keep their geometry, so their frame (layer index 1) is swapped at runtime by `ICUI.skin`; the lit tab, lit help topic and lit law button swap their plate and ink at runtime; the opener swaps its glyph. In Lua, `ICUI.use_race(r)` writes the race's 1920 cells into `ICUI.BASE` before `ICUI.apply_scale`, and puts the Chaos Dwarf values back for a Chaos Dwarf court. Every Dwarf picture is baked by the generator from CA's own art read offline (`read_pack_index` + `read_vanilla_loc._decompress`) and listed in `art_paths()`. The preview draws a Dwarf court from a harness dump of the real `ICUI.open` and `ICUI.refresh`, never from a Python copy of the Lua.

**Tech Stack:** Lua 5.1, Python 3 + Pillow, texconv only if a .dds is needed, RPFM MCP
**Spec:** docs/superpowers/specs/2026-10-04-iron-court-dwarfs-design.md (and the CONTRACT file)

## Global Constraints

- Carried from phase 1's final review (2026-10-04): the panel's art tables are still the
  Chaos Dwarfs' - `ICUI.LAW_ART_DIR` / `ICUI.LAW_ART` (a `wh3_dlc23_tech_chd_` path) and
  `ICUI.GOV_ART`. This phase reads them through the player's race (`R.art` or race fields)
  and shows the Dwarf versions in its preview. The ziggurat grid at load (`ICUI.CARD_XY`,
  allow-listed in the harness race scan) is this phase's; the allow entry must be removed
  when it moves, or the scan reports it stale.

- Read first: `docs/superpowers/plans/2026-10-04-iron-court-dwarfs-CONTRACT.md` (names), spec sections 2.5, 2.6, 9.6 and 10, handoff `docs/sessions/HANDOFF_20261004_IRON_COURT_DWARFS_DESIGN.md` sections 3 and 3b, `docs/CUSTOM_UI.md` (runtime components, `MoveTo`, nine-slice and texture traps, build-time checks). Phases 1 and 2 are done per the contract; Task 1 proves it before anything is edited.
- No emojis anywhere. Never the word "rung". Player text in plain words: "The Council of Karak Kadrin", "THE GREAT HALL", "THE THRONE OF", "The throne stands empty". No "cap", "standing", "AI" in anything a player reads.
- Run every tool from the workspace root `G:\Modding for resources`. Not a git repo: every "checkpoint" runs THE GATES instead of committing.
- Patch scripts and any file holding a backslash or a regex go through the Write or Edit tool, never a heredoc; never `sed -i` (it strips CRLF).
- Lua: in a function with over 255 constants no number literal on the LEFT of an arithmetic operator (`x * 2`, never `2 * x`); `py tools\check_lua_literal_left.py` finds them.
- The Chaos Dwarf court must not change. Its `.twui.xml`, its art and its preview pictures are fingerprinted in Task 1 and every checkpoint verifies the fingerprint. Every Dwarf branch is `if RACE == "dwf"` (Python) or reads `ICUI.ART` / `ICUI.RACE_XY` (Lua); none edits a Chaos Dwarf value in place.
- The 9-slice margin lives in the twui. `SetImagePath(path, index)` replaces the picture only - CA: "If this is not set, the incoming image will take the size of the old" - never the margin, offset or size. A runtime swap is therefore only used where the new picture has the old one's geometry. `SetCurrentStateImageMargins` exists in CA's docs and has no use in CA's scripts or ours; it is NOT used.
- Every picture is either at its component's exact 1920 size or nine-sliced across a middle whose columns are identical. Nothing is stretched (spec 2.6).
- Contrast: cream `#FFF8D7` (luminance 245, Rec.709) at 4.5:1 or better, p95 of the ground per text cell, measured the way `tools/make_ic_backdrop.py` measures; dark ink on the gold ribbon at 4.5:1 or better against the p5 of the ground.
- Every key used is verified against CA's data before it is written: faction keys by `read_vanilla_loc.load("factions")`, art paths by `read_pack_index.paths()` of `ui.pack` / `ui2.pack`, the `[[col:black]]` name by `db/ui_colours_tables` (`black` = `000000`).
- Deploy only with `py tools\deploy_iron_court.py` (RPFM open; it backs up to `Modding Files/Backup/`, never into `data/` or a Workshop folder; it writes to `data/` only while `Warhammer3.exe` is not running, `--wait` otherwise).
- Every touched view is rendered by `tools/preview_iron_court.py` from the shipped Lua and approved by the author before it ships. Approval is recorded by `phase3_approvals.py` (Task 12) against the exact pixels approved, so any later change to an approved view voids its approval.

**THE GATES** (PowerShell, from the workspace root). A checkpoint step means: run all of these; each must end green.

```powershell
$lua = "C:\Program Files (x86)\Lua\5.1"
Get-ChildItem "Modding Files\pack\script\campaign\mod\zzz_derpy_iron_court*.lua" | ForEach-Object { & "$lua\luac.exe" -p $_.FullName; if ($LASTEXITCODE -ne 0) { "LUAC FAIL " + $_.Name } }
& "$lua\lua.exe" tools\_iron_court_harness.lua
py tools\check_lua_api.py
py tools\check_lua_literal_left.py
py tools\check_lua_undeclared.py
py tools\gen_ic_ui.py --check
py tools\gen_ic_ui.py --selftest
py tools\gen_iron_court.py --check
py tools\make_ic_backdrop.py --check
py tools\import_iron_court.py
py "Modding Files\source\iron_court_preview\phase3_probe.py" --verify
```

Expected: no `LUAC FAIL` line; `iron court harness: ok (N checks)`; the three Lua checkers exit 0; `gen_ic_ui.py --check` ends `ok: N files, M components`; `--selftest` ends without a traceback; `gen_iron_court.py --check` exits 0; `make_ic_backdrop.py --check` prints no `PROBLEM:`; `import_iron_court.py` reports no problem; the probe prints `chd court unchanged: N files`. (`make_ic_backdrop.py --check` checks both races from Task 6 on; before Task 6 it checks the Chaos Dwarf one only.)

## Review Focus

1. **The Chaos Dwarf court is byte-identical.** Task 1 fingerprints its twui files, its art and its preview pictures; every checkpoint verifies the twui and art, Task 11 re-renders and verifies the pictures. A Dwarf branch that leaks into the base module shows up there and nowhere else.
2. **Switching race restores everything.** `ICUI.use_race` rewrites `ICUI.BASE` in place; a Chaos Dwarf court opened after a Dwarf one must get back its card grid, its `PANEL_XY` cells (the Dwarf-only throne cells removed from both `BASE` and the live table, since `apply_scale` only writes keys the base holds), its caps (111/34), its panel file and its tab plates. Pinned in Task 7 ("a Chaos Dwarf court opened after a Dwarf court ...").
3. **Ink and dim are measured, not chosen.** The Dwarf backdrop dims to 0.27 (the largest hundredth where every bare cell clears 4.5:1 at 1600, 1920 and 2560; the mockup's 0.42 left `ic_row_crest[10]` at 3.2:1). The blue ribbon is dimmed to 0.72 (active) and 0.52 (hover) for cream; the gold lit ribbon cannot carry cream at all (p95 ~140) and takes black ink through `[[col:black]]`. Each check also asserts the value is the LARGEST that passes, so a dim nobody needs fails too.
4. **Forced deviations from the approved mockup**, each for a measured reason: the throne is three lines (`ic_throne_of` "THE THRONE OF", `ic_throne_name` the faction, `ic_throne_leader` the king), because "Masters of Innovation" at 18px does not fit one line with the prefix at 1600; the title box is 1100 wide, not 900, because "The Council of Masters of Innovation" at 20px is 442px against 422 usable at 1600; the knot rule runs full only under THE GREAT HALL (the hall art carries it; the heading plate on `ic_off_title` is the bare marks), the other headings carry the short rule; the Fill Empty Seats button, the pager and the action buttons stay on CA's red plate ("Fill Empty Seats" is 169px against the ribbon's 148); the lit tab's words are dark on gold.
5. **`DWF_KEEPS`**, the Chaos Dwarf art still reachable from a Dwarf court (the Governors column's Hell-Forge plates, the tab marker's heat glow, the Tower of Zharr toggle art, the trait, band and Conclave Influence icons, the Chaos Dwarf technology paintings on law cards). Every entry is the author's to rule on in Task 15; until then the build lists them rather than hiding them.
6. **No runtime margin change.** The pooled card frames are baked at each pool's exact 1920 size so the twui's margin 8 draws them 1:1; at 1600 the whole frame scales by about 0.83 on both axes. This is the cost of not using `SetCurrentStateImageMargins`.
7. **Later phases' preview edits land on the Chaos Dwarf path.** Phase 4's `plot_cards(G, race)` and phase 5's `STRINGS["ic_book"]` are written into `render()`'s Chaos Dwarf branch; a Dwarf picture comes from the dump, so whatever their Lua draws appears there without those lines. Phase 6 Task 4 Step 1 expects the Dwarf picture count to EQUAL the Chaos Dwarf one; the Dwarf set has two more views (Record and Help, which the Chaos Dwarf preview has never drawn), so that count is 39 against 33 and the step must read "at least".

---

### Task 1: Preconditions and the Chaos Dwarf fingerprint

**Files:**
- Create: `Modding Files/source/iron_court_preview/phase3_probe.py` (not packed, not synced)
- Create (by the probe): `Modding Files/source/iron_court_preview/phase3_chd_ui_baseline.json`

**Interfaces:**
- Consumes: phase 1 (`IC.RACES`, `IC.R`, `IC.register_race` in `zzz_derpy_iron_court.lua`), phase 2 (`zzz_derpy_iron_court_dwarf.lua` with the dwf race table carrying `layout = "grid"`, `grid = {cols = 5, rows = 4, throne = {2, 0}, cells = {...}}`, `art = {}`; `gen_iron_court.RACES["dwf"]["OFFICES"]` with a `tier` per office).
- Produces: `phase3_probe.py` with no flag (preconditions), `--record` (fingerprint), `--verify` (compare); the baseline JSON. Every checkpoint in this plan runs `--verify`.

- [ ] **Step 1: Write the probe.** Create `Modding Files/source/iron_court_preview/phase3_probe.py` with the Write tool:

```python
"""Phase 3 (Dwarf UI) of the Iron Court for Dwarfs: preconditions, and the Chaos
Dwarf court's fingerprint that every checkpoint compares against.

    py "Modding Files/source/iron_court_preview/phase3_probe.py"            # preconditions
    py "Modding Files/source/iron_court_preview/phase3_probe.py" --record   # once, before any edit
    py "Modding Files/source/iron_court_preview/phase3_probe.py" --verify   # every checkpoint

The fingerprint is every Chaos Dwarf .twui.xml, every Chaos Dwarf picture under
ui/derpy_ic and every Chaos Dwarf preview picture. Phase 3 adds a race; it must not
move one byte of the race that is already shipped.
"""
import hashlib
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
BASELINE = os.path.join(HERE, "phase3_chd_ui_baseline.json")
MOD = os.path.join(ROOT, "Modding Files", "pack", "script", "campaign", "mod")
PACK = os.path.join(ROOT, "Modding Files", "pack")
PREVIEW = os.path.join(ROOT, ".skilltree_cache", "ui_preview")
GAME = os.path.join("F:" + os.sep, "SteamLibrary", "steamapps", "common",
                    "Total War WARHAMMER III", "data")
# Spec 2.5, layout E: the tier of each hall cell. (column, row) on the 5x4 grid.
SPEC_TIERS = {1: {(1, 0), (3, 0)},
              2: {(0, 0), (4, 0), (1, 1), (3, 1)},
              3: {(0, 1), (4, 1), (1, 2), (3, 2)},
              4: {(0, 2), (4, 2), (1, 3), (3, 3)}}
CA_ART = {
    "ui2.pack": ["ui/skins/default/dlc25_book_of_grudges/" + n for n in (
        "tab_button_unit_pack_active.png", "tab_button_unit_pack_selected.png",
        "tab_button_legendary_grudges_selected.png",
        "book_of_grudges_confederation_frame.png",
        "book_of_grudges_confederation_decor_2.png",
        "book_of_grudges_legendary_grudges_decor_2.png",
        "book_of_grudges_unit_pack_decor.png", "decor_units_header.png",
        "rune_1_panel.png", "rune_2_panel.png", "rune_3_panel.png",
        "rune_4_panel.png", "rune_5_panel.png")]
    + ["ui/skins/default/icon_book_grudges.png"],
    "ui.pack": ["ui/loading_ui/load_images/campaign_dwarfs1.png"],
}


def read(path):
    return io.open(path, encoding="utf-8").read() if os.path.isfile(path) else None


def grid_cells(src):
    """The dwf race table's grid, scraped the way gen_ic_ui.race_grid will."""
    at = src.find("grid = {")
    if at < 0:
        return None
    i = src.index("{", at)
    depth = 0
    for j in range(i, len(src)):
        depth += {"{": 1, "}": -1}.get(src[j], 0)
        if depth == 0:
            break
    body = src[i:j + 1]
    throne = re.search(r"throne\s*=\s*\{(\d+),\s*(\d+)\}", body)
    cells = [(int(c), int(r)) for c, r in
             re.findall(r"\{(\d+),\s*(\d+)\}", body[body.index("cells"):])]
    return (int(throne.group(1)), int(throne.group(2))) if throne else None, cells


def preconditions():
    out = []
    model = read(os.path.join(MOD, "zzz_derpy_iron_court.lua")) or ""
    for needle in ("IC.RACES", "function IC.R(", "function IC.register_race("):
        if needle not in model:
            out.append("the model has no %s: phase 1 is not done" % needle)
    dwarf = read(os.path.join(MOD, "zzz_derpy_iron_court_dwarf.lua"))
    if dwarf is None:
        out.append("zzz_derpy_iron_court_dwarf.lua is missing: phase 2 is not done")
        return out
    for needle in ('layout = "grid"', "grid = {", "art = {"):
        if needle not in dwarf:
            out.append("the dwf race table has no `%s`" % needle)
    throne, cells = grid_cells(dwarf) or (None, [])
    if throne != (2, 0):
        out.append("the dwf grid's throne is %r, not (2, 0)" % (throne,))
    import gen_iron_court as GIC
    races = getattr(GIC, "RACES", {})
    if "dwf" not in races:
        out.append("gen_iron_court.RACES has no dwf: phase 2 is not done")
    else:
        tiers = [o["tier"] for o in races["dwf"]["OFFICES"]]
        if len(cells) != len(tiers):
            out.append("the dwf grid places %d seats for %d offices" % (len(cells), len(tiers)))
        for t, want in sorted(SPEC_TIERS.items()):
            have = set(c for c, tier in zip(cells, tiers) if tier == t)
            if have != want:
                out.append("tier %d sits at %s, the spec says %s" % (t, sorted(have), sorted(want)))
    ui = read(os.path.join(MOD, "zzz_derpy_iron_court_ui.lua")) or ""
    if "function ICUI.race(" not in ui:
        print("note: ICUI.race is not declared yet - Task 7 adds it")
    import read_pack_index as RPI
    for pack, want in sorted(CA_ART.items()):
        have = set(p.lower() for p in RPI.paths(os.path.join(GAME, pack)))
        for p in want:
            if p not in have:
                out.append("%s is not in %s" % (p, pack))
    import read_vanilla_loc as L
    name = L.load("factions").get("factions_screen_name_wh_main_dwf_karak_kadrin")
    if name != "Karak Kadrin":
        out.append("CA's loc names wh_main_dwf_karak_kadrin %r, not Karak Kadrin" % name)
    gen = read(os.path.join(ROOT, "tools", "gen_ic_ui.py")) or ""
    for prefix in ("IC60", "IC61"):
        m = re.search(r'"([^"]+)":\s*"%s"' % prefix, gen)
        if m and "derpy_ic_panel_dwf" not in m.group(1):
            out.append("GUID prefix %s is already %s" % (prefix, m.group(1)))
    return out


def _md5(path):
    return hashlib.md5(open(path, "rb").read()).hexdigest()


def _dwarf_name(name):
    base = os.path.basename(name)
    return "_dwf" in base or base.startswith("dwf_")


def fingerprint():
    import gen_ic_ui as U
    out = {}
    for name in U.ui_file_names():
        if not _dwarf_name(name):
            p = os.path.join(PACK, "ui", "campaign ui", name)
            out["twui/" + name] = _md5(p) if os.path.isfile(p) else "MISSING"
    for path in sorted(U.art_paths()):
        if not _dwarf_name(path):
            p = os.path.join(PACK, *path.split("/"))
            out["art/" + path] = _md5(p) if os.path.isfile(p) else "MISSING"
    if os.path.isdir(PREVIEW):
        for name in sorted(os.listdir(PREVIEW)):
            if name.startswith("ic_") and name.endswith(".png") and not _dwarf_name(name):
                out["preview/" + name] = _md5(os.path.join(PREVIEW, name))
    return out


def main(argv):
    if "--record" in argv:
        problems = preconditions()
        for p in problems:
            print("PRECONDITION: " + p)
        if problems:
            return 1
        fp = fingerprint()
        with io.open(BASELINE, "w", encoding="utf-8", newline="\n") as f:
            json.dump(fp, f, indent=1, sort_keys=True)
        print("recorded %d Chaos Dwarf files to %s" % (len(fp), BASELINE))
        return 0
    if "--verify" in argv:
        if not os.path.isfile(BASELINE):
            print("FAIL no baseline at %s - run --record before any phase 3 edit" % BASELINE)
            return 1
        want = json.load(io.open(BASELINE, encoding="utf-8"))
        have = fingerprint()
        bad = []
        for k, v in sorted(want.items()):
            if k.startswith("preview/") and "--previews" not in argv:
                continue
            if have.get(k) != v:
                bad.append("%s changed (%s -> %s)" % (k, v, have.get(k, "MISSING")))
        for b in bad:
            print("FAIL " + b)
        if bad:
            return 1
        print("chd court unchanged: %d files" % sum(
            1 for k in want if "--previews" in argv or not k.startswith("preview/")))
        return 0
    problems = preconditions()
    for p in problems:
        print("PRECONDITION: " + p)
    print("preconditions ok" if not problems else "%d precondition(s) failed" % len(problems))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 2: Run the verify and see it fail.**

Run: `py "Modding Files\source\iron_court_preview\phase3_probe.py" --verify`
Expected: `FAIL no baseline at ...phase3_chd_ui_baseline.json - run --record before any phase 3 edit`, exit 1.

- [ ] **Step 3: Draw the Chaos Dwarf previews as they are today, then record.**

Run: `py tools\preview_iron_court.py`
Expected: one `wrote ...ic_*.png` line per view per size (33), no `PROBLEM:`.

Run: `py "Modding Files\source\iron_court_preview\phase3_probe.py"`
Expected: `preconditions ok` (and the note that Task 7 adds `ICUI.race` if phase 1 did not). Any `PRECONDITION:` line: STOP and tell the author which phase is not done; do not work around it here.

Run: `py "Modding Files\source\iron_court_preview\phase3_probe.py" --record`
Expected: `recorded N Chaos Dwarf files to ...phase3_chd_ui_baseline.json`, N above 300 (the twui files, the plates and wedges, 33 previews).

- [ ] **Step 4: Run the verify and see it pass.**

Run: `py "Modding Files\source\iron_court_preview\phase3_probe.py" --verify --previews`
Expected: `chd court unchanged: N files` (the same N).

- [ ] **Step 5: Checkpoint.** Run THE GATES. Expected: all green (nothing has been edited yet; this proves the gates are green before phase 3 starts).

---

### Task 2: Race copies of the generator and the Dwarf panel file pair

**Files:**
- Modify: `tools/gen_ic_ui.py` (top constants after `BOX_W = ...` line 35; `at_box` line 66; `GUID_PREFIXES`; `COMPACT_FILES` line 133; the literal `"derpy_ic_panel.twui.xml"` at its other uses; `ui_file_names`; `write_ui`; `main`; `selftest`)
- Modify: `tools/import_iron_court.py` (gate 9, `built_xml = U2.build_xml()`)

**Interfaces:**
- Produces (Python, added to the contract): `RACE` (`"chd"` | `"dwf"`), `PANEL_SUFFIX`, `PANEL_FILE`, `RACE_PANEL_FILES`, `at_box(bw, race=None)` (None = this copy's race, so the base module's default is the contract's `"chd"`), `_dwf()` (the cached Dwarf copy at 1920), `race_xml()`, `check_race_files(files=None)`. GUID prefixes IC60 and IC61.
- Consumed by: Tasks 3-6, 9, 11; phase 6 (`at_box(bw, race=race).check()`).

- [ ] **Step 1: The failing check.** In `tools/gen_ic_ui.py`, directly above `def selftest():`, add:

```python
def selftest_race():
    """THE RACE COPIES (plan 2026-10-04 phase 3, Task 2)."""
    d = at_box(1920, "dwf")
    assert d.RACE == "dwf" and d.PANEL_FILE == "derpy_ic_panel_dwf.twui.xml", d.PANEL_FILE
    assert d._small().RACE == "dwf", "a Dwarf copy's compact source is not Dwarf"
    assert at_box(1600).RACE == RACE, "at_box() forgot this copy's race"
    files = race_xml()
    for f in RACE_PANEL_FILES:
        assert f in files and f in ui_file_names(), "%s is not built or not listed" % f
        assert 'this="%s' % GUID_PREFIXES[f] in files[f], "%s is not on its own prefix" % f
    assert not check_race_files(), check_race_files()
    # A PLANTED COLLISION: the Dwarf panel carrying the Chaos Dwarf panel's GUIDs.
    bad = dict(files)
    bad["derpy_ic_panel_dwf.twui.xml"] = files[PANEL_FILE]
    assert any("GUID" in p for p in check_race_files(bad)), "a GUID collision passed"
```

and make `selftest()` call it first: add `selftest_race()` as the first statement of `selftest()`.

- [ ] **Step 2: Run it and see it fail.**

Run: `py tools\gen_ic_ui.py --selftest`
Expected: `TypeError: at_box() takes 1 positional argument but 2 were given`.

- [ ] **Step 3: Implement.**

3a. Directly after `BOX_W = globals().get("_BOX_W", 1920)` (line 35):

```python
# THE RACE THIS COPY DRAWS (plan 2026-10-04 phase 3). The base module is the Chaos
# Dwarfs'; at_box(bw, "dwf") re-executes this file with _RACE injected beside
# _BOX_W, so every layout number, layer list and check below is the race's own.
RACE = globals().get("_RACE", "chd")
PANEL_SUFFIX = {"chd": "", "dwf": "_dwf"}[RACE]
PANEL_FILE = "derpy_ic_panel%s.twui.xml" % PANEL_SUFFIX
# The other race's panel pair, which only the base module writes (race_xml).
RACE_PANEL_FILES = ("derpy_ic_panel_dwf.twui.xml", "derpy_ic_panel_dwf_compact.twui.xml")
```

3b. Replace `def at_box(bw):` and its body with:

```python
def at_box(bw, race=None):
    """A fresh copy of this module with every layout number scaled to box bw, for
    `race` - by default this copy's own, so a Dwarf copy's _small() is Dwarf too."""
    import importlib.util
    race = race or RACE
    spec = importlib.util.spec_from_file_location("gen_ic_ui_at_%d_%s" % (bw, race),
                                                  os.path.abspath(__file__))
    mod = importlib.util.module_from_spec(spec)
    mod.__dict__["_BOX_W"] = bw
    mod.__dict__["_RACE"] = race
    spec.loader.exec_module(mod)
    return mod


_DWF = []


def _dwf():
    """The Dwarf copy at 1920, built once a run: its panel pair and its art."""
    if not _DWF:
        _DWF.append(at_box(1920, "dwf"))
    return _DWF[0]
```

3c. In `GUID_PREFIXES`, after the `"derpy_ic_lawblock_compact.twui.xml": "IC59",` line:

```python
    # IC60-IC61 - THE DWARF PANEL (plan 2026-10-04 phase 3) and its compact copy.
    # Its own file because the title's and the headings' end caps are twui
    # margins (111 -> 150, 34 -> 80), and SetImagePath cannot change a margin.
    "derpy_ic_panel_dwf.twui.xml":         "IC60",
    "derpy_ic_panel_dwf_compact.twui.xml": "IC61",
```

3d. In `COMPACT_FILES`, replace the literal `"derpy_ic_panel.twui.xml"` in the `for f in (...)` tuple with `PANEL_FILE`. Then replace every OTHER occurrence of the literal `"derpy_ic_panel.twui.xml"` in the file with `PANEL_FILE`, except the `GUID_PREFIXES` key (find them with `Select-String -Path tools\gen_ic_ui.py -Pattern '"derpy_ic_panel.twui.xml"'`; today they are the `FILES` entry, the `check_gm(all_files.get(...))` call and five more). After the edit the same search returns exactly one line, the `GUID_PREFIXES` key.

3e. Add, directly after `build_xml()`:

```python
def race_xml():
    """build_xml() plus the other race's panel pair: what write_ui writes, what the
    packing gate compares, what ships. Only the base module adds the pair; a copy
    returns its own files, which is what its own check() reads."""
    out = build_xml()
    if RACE == "chd" and BOX_W == 1920:
        theirs = _dwf().build_xml()
        for f in RACE_PANEL_FILES:
            out[f] = theirs[f]
    return out


def check_race_files(files=None):
    """Check 1's GUID rules over EVERY file the pack ships. check() sees only its own
    copy's files, so a collision between the two races' panels is invisible to it."""
    files = race_xml() if files is None else files
    out, seen = [], {}
    for fname, text in sorted(files.items()):
        want = GUID_PREFIXES.get(fname)
        if not want:
            out.append("%s has no GUID prefix" % fname)
            continue
        for guid in re.findall(r'this="([0-9A-Za-z]{8}-[^"]+)"', text):
            if guid in seen and seen[guid] != fname:
                out.append("GUID %s appears in %s and %s" % (guid, seen[guid], fname))
            seen[guid] = fname
            if not guid.startswith(want):
                out.append("%s: GUID %s is outside that file's %s range" % (fname, guid, want))
    return out
```

3f. In `ui_file_names()`, change the final `+ sorted(COMPACT_FILES.values()))` to `+ sorted(COMPACT_FILES.values()) + (list(RACE_PANEL_FILES) if RACE == "chd" else []))`.

3g. In `write_ui()`, change `for fname, text in build_xml().items():` to `for fname, text in race_xml().items():`.

3h. In `main()`, directly after `problems += check_gov_glow()`:

```python
    problems += check_race_files()
    for _bw in (1920, 1600, 2560):
        problems += ["dwf at %d: %s" % (_bw, p) for p in at_box(_bw, "dwf").check()]
```

3i. In `tools/import_iron_court.py` gate 9, change `built_xml = U2.build_xml()` to:

```python
        built_xml = U2.race_xml()
        problems += U2.check_race_files()
```

- [ ] **Step 4: Run it and see it pass.**

Run: `py tools\gen_ic_ui.py --selftest`
Expected: exit 0, no traceback.

Run: `py tools\gen_ic_ui.py`
Expected: the usual `wrote ...` lines plus `wrote ...derpy_ic_panel_dwf.twui.xml` and `wrote ...derpy_ic_panel_dwf_compact.twui.xml`; no `FAIL` line. (The Dwarf panel is still the Chaos Dwarf panel on its own prefix: Tasks 3-5 make it Dwarf.)

- [ ] **Step 5: Checkpoint.** Run THE GATES. Expected: all green; the probe still says `chd court unchanged` (the Chaos Dwarf files are byte-identical; only two files were added).

---

### Task 3: The hall grid, the throne and the Dwarf layout

**Files:**
- Modify: `tools/gen_ic_ui.py` (the `DWF` dict after the 3a block; `race_grid`, `_lua_block`, `_grid_xy`, `card_grid`, `throne_box`, `CARD_WIDEST`; the Dwarf layout block after `PANEL_LAYOUT["ic_off_title"] = off_title_box()`; `_panel_order`; `hall_boxes`, `hall_runner`, `hall_doors`, `hall_pillars`, `check_hall`; `check()`'s `check_ziggurat()` line; the snapshot before `_scale_pass`; `NOT_GEOMETRY`)

**Interfaces:**
- Produces (Python): `DWF` (the one generator dict for every Dwarf colour, size and offset), `DWARF_LUA`, `_lua_block(src, opener)`, `race_grid(race) -> (cols, rows, throne, cells)`, `card_grid(race=None)` (contract), `throne_box()` (contract), `HALL_TIER_CELLS`, `DWF_CELLS`, `hall_boxes()`, `hall_runner()`, `hall_doors()`, `hall_pillars()`, `check_hall(cells=None)`, `PANEL_LAYOUT_1920`, `POOL_1920`. New panel cells `ic_throne` (contract), `ic_throne_name` (contract), `ic_throne_leader` (contract) and `ic_throne_of` (ADDED to the contract: "THE THRONE OF" on its own line; consumed by Task 8's `ICUI.draw_throne` and phase 6's fit matrix).
- The Dwarf cells at 1920: `ic_title` (18, 4, 1100, 56), `ic_help` (1126, 8, 48, 48), `ic_off_title` (703, 120, 514, 44), `ic_throne` (778, 192, 364, 184), `ic_throne_of` (794, 288, 332, 18), `ic_throne_name` (794, 306, 332, 26), `ic_throne_leader` (794, 334, 332, 22). Task 7 mirrors them in `ICUI.RACE_XY.dwf`; Task 9 compares.

- [ ] **Step 1: The failing check.** Above `def selftest():` add:

```python
def selftest_hall():
    """THE HALL (spec 2.5 layout E; plan 2026-10-04 phase 3, Task 3)."""
    d = _dwf()
    # Measured against the spec's picture, not re-derived: cell (1, 0) and the throne.
    assert d.CARD_GRID[0] == (398, 192), d.CARD_GRID[0]
    assert d.throne_box() == (778, 192, 364, 184), d.throne_box()
    assert d.PANEL_LAYOUT["ic_throne_name"] == (794, 306, 332, 26)
    assert d.CARD_W == CARD_W == 364, "a Dwarf card is not a Chaos Dwarf card's size"
    assert not d.check_hall(), d.check_hall()
    cells = list(d.race_grid("dwf")[3])
    # THREE PLANTED FAULTS: a seat on the throne, a seat off the hall's foot, a seat on the runner.
    on_throne = [(2, 0)] + cells[1:]
    assert any("throne" in p for p in d.check_hall(on_throne)), "a seat on the throne passed"
    off_foot = cells[:-1] + [(0, 3)]
    assert any("off the hall" in p for p in d.check_hall(off_foot)), "a seat off the hall passed"
    on_runner = cells[:-1] + [(2, 2)]
    assert any("runner" in p for p in d.check_hall(on_runner)), "a seat on the runner passed"
```

and call `selftest_hall()` in `selftest()` right after `selftest_race()`.

- [ ] **Step 2: Run it and see it fail.**

Run: `py tools\gen_ic_ui.py --selftest`
Expected: `AssertionError: (18, 192)` (the Dwarf copy still lays the ziggurat's first card).

- [ ] **Step 3: Implement.**

3a. Directly after the `RACE_PANEL_FILES` line (Task 2, 3a):

```python
# THE DWARF SKIN, ONE DICT (spec 2.5, 2.6; approved mockups dwf_skin_mockup2.py and
# dwf_seat_mockups2.py layout E). Every colour, size and offset the Dwarf panel and
# its art use, at 1920. Nothing Dwarf is typed anywhere else.
DWF = {
    # Cells, (x, y, w, h). The title is 1100 wide, not the mockup's 900: "The Council
    # of Masters of Innovation" at the compact 20px is 442px against 422 usable at 1600.
    "title_box": (18, 4, 1100, 56),
    "help_box": (1126, 8, 48, 48),
    "off_title_box": (703, 120, 514, 44),
    # Relative to the throne's cell. Three lines: the longest playable name does not
    # fit one line with "THE THRONE OF" in front of it at 1600.
    "throne_cells": {"ic_throne_of": (16, 96, 332, 18),
                     "ic_throne_name": (16, 114, 332, 26),
                     "ic_throne_leader": (16, 142, 332, 22)},
    # The hall (mockup shape_hall, round 3), in px off the card grid.
    "hall_pad": 18, "hall_top": 12, "hall_neck": 10, "hall_foot": 7,
    "runner_in": 70, "runner_top": 6, "runner_foot": 4,
    "door_in": 40, "door_h": 70, "door_inset": 8, "knob": 4,
    "pillar_half": 6, "rune_px": 28, "rune_step": 70, "rune_top": 24, "rune_clear": 40,
    "hall_rule_y": 152, "hall_rim": 3,
    # Caps and text.
    "title_cap": 150, "heading_cap": 80, "ribbon_cap": 34, "tab_text_inset": 36,
    "tab_lift": 2, "tab_grow": 6, "tab_ty": "0.00,5.00",
    "ribbon_dim": {"active": 0.72, "hover": 0.52, "selected": 1.0},
    "lintel_chamfer": 10, "seats_chamfer": 8,
    "mark_x": 12, "mark_mid": 20, "rule_y": 37, "diamond": 10,
    "throne_face": 0.5, "throne_face_top": 22,
    # CA's knotwork frame, in its source pixels: corner box, top ornament columns,
    # the straight run sampled for tiling, the side rows sampled for tiling.
    "frame_corner": 48, "frame_orn": (200, 322), "frame_run": (120, 160),
    "frame_side": (100, 140),
    # Colours, RGBA.
    "gold": (198, 156, 74, 235), "gold_dim": (150, 116, 56, 200),
    "stone": (24, 27, 33, 200), "runner": (22, 36, 64, 200),
    "pillar": (60, 56, 50, 230), "door": (92, 62, 34, 245),
    "lintel": (20, 18, 16, 235), "throne_field": (26, 20, 14, 245),
    "seats_field": (20, 18, 16, 235),
}
# The cells the Dwarf layout sets; ICUI.RACE_XY.dwf mirrors exactly these.
DWF_CELLS = ("ic_title", "ic_help", "ic_off_title", "ic_throne") + tuple(sorted(DWF["throne_cells"]))
# Spec 2.5, layout E: the tier of each hall cell, (column, row).
HALL_TIER_CELLS = {1: {(1, 0), (3, 0)},
                   2: {(0, 0), (4, 0), (1, 1), (3, 1)},
                   3: {(0, 1), (4, 1), (1, 2), (3, 2)},
                   4: {(0, 2), (4, 2), (1, 3), (3, 3)}}
DWARF_LUA = os.path.join(ROOT, "Modding Files", "pack", "script", "campaign", "mod",
                         "zzz_derpy_iron_court_dwarf.lua")


def _lua_block(src, opener):
    """The balanced { ... } that follows `opener` in a Lua source, or None."""
    at = src.find(opener)
    if at < 0:
        return None
    i = src.index("{", at)
    depth = 0
    for j in range(i, len(src)):
        depth += {"{": 1, "}": -1}.get(src[j], 0)
        if depth == 0:
            return src[i:j + 1]
    return None


def race_grid(race):
    """(cols, rows, throne, cells) out of the race table the panel itself reads. The
    Lua is the one copy; a Python list here would be a second one to drift."""
    assert race == "dwf", "only the Dwarf race lays a grid"
    body = _lua_block(io.open(DWARF_LUA, encoding="utf-8").read(), "grid = {")
    if not body:
        raise SystemExit("%s has no grid = {...}: phase 2's race table is not there" % DWARF_LUA)

    def num(key):
        return int(re.search(r"\b%s\s*=\s*(\d+)" % key, body).group(1))
    throne = tuple(int(v) for v in re.search(r"throne\s*=\s*\{(\d+),\s*(\d+)\}", body).groups())
    cells = [(int(c), int(r)) for c, r in
             re.findall(r"\{(\d+),\s*(\d+)\}", body[body.index("cells"):])]
    return num("cols"), num("rows"), throne, cells
```

Check that `import io` is already at the top of the file (`write_ui` uses `io.open`); it is.

3b. `CARD_WIDEST` (line 1083): the card width of a grid race is its grid's, so a Dwarf card is a Chaos Dwarf card. Replace the right-hand side so the line reads (whatever phase 1 left on the right-hand side stays as the Chaos Dwarf branch):

```python
CARD_WIDEST = max(IC.TIER_SEATS.values()) if RACE == "chd" else race_grid(RACE)[0]
```

3c. Replace `def card_grid():` with:

```python
def _grid_xy(cols, c, r):
    """(x, y) of grid cell (c, r): the band of `cols` cards centred in the content."""
    band = cols * CARD_W + (cols - 1) * CARD_GAP_X
    return (CARDS_X + (CONTENT_W - band) // 2 + c * (CARD_W + CARD_GAP_X),
            CARDS_Y + r * (CARD_H + CARD_GAP_Y))


def card_grid(race=None):
    race = race or RACE
    if race != "chd":
        # A GRID RACE (spec 2.5): one card per office, in IC.OFFICES order, at the
        # cell its race table names. ICUI.grid_xy is the Lua copy; the packing gate
        # runs it and compares.
        cols, _rows, _throne, cells = race_grid(race)
        return [_grid_xy(cols, c, r) for c, r in cells]
    out = []
```

keeping the existing Chaos Dwarf body (from `for row, tier in enumerate(CARD_TIERS):` to `return out`) as the rest of the function. `CARD_GRID = card_grid()` below it is unchanged and now follows the copy's race.

3d. Directly after `card_grid`:

```python
def throne_box():
    """The throne's cell at this copy's grid: (x, y, w, h)."""
    cols, _rows, (c, r), _cells = race_grid("dwf")
    x, y = _grid_xy(cols, c, r)
    return (x, y, CARD_W, CARD_H)
```

3e. Directly after `PANEL_LAYOUT["ic_off_title"] = off_title_box()` (line 2364):

```python
# THE DWARF LAYOUT (plan 2026-10-04 phase 3): the lintel and its help button, the
# hall's title, the throne and its three lines. Everything else is the Chaos Dwarf
# panel's own cell. The hall picture takes ic_zig_bg's box, from the section line
# to the lowest card's foot.
if RACE == "dwf":
    PANEL_LAYOUT["ic_title"] = DWF["title_box"]
    PANEL_LAYOUT["ic_help"] = DWF["help_box"]
    PANEL_LAYOUT["ic_off_title"] = DWF["off_title_box"]
    PANEL_LAYOUT["ic_throne"] = throne_box()
    for _n, _b in DWF["throne_cells"].items():
        PANEL_LAYOUT[_n] = (PANEL_LAYOUT["ic_throne"][0] + _b[0],
                            PANEL_LAYOUT["ic_throne"][1] + _b[1], _b[2], _b[3])
    PANEL_LAYOUT["ic_zig_bg"] = (0, PANEL_LAYOUT["ic_zig_bg"][1], PANEL_W,
                                 max(y for _x, y in CARD_GRID) + CARD_H + ZIG_PAD_Y
                                 - PANEL_LAYOUT["ic_zig_bg"][1])
    del _n, _b
```

3f. In `_panel_order`, change `if name in ("ic_dial_box", "ic_crown_box") or name in LAW_PLATES:` to `if name in ("ic_dial_box", "ic_crown_box", "ic_throne") or name in LAW_PLATES:` (the throne is an opaque plate under its three lines; `make_ic_backdrop` takes every tier -1 cell for one).

3g. Directly after `check_ziggurat`:

```python
def _hall_px(key):
    return sc(DWF[key], BOX_W)


def _cx(c):
    return CARDS_X + c * (CARD_W + CARD_GAP_X)


def _ry(r):
    return CARDS_Y + r * (CARD_H + CARD_GAP_Y)


def hall_boxes():
    """The hall's stone as (x0, y0, x1, y1): the nave over rows 0-2 across the
    whole grid, and its foot under columns 1-3 of row 3 (mockup shape_hall)."""
    pad, top, neck, foot = (_hall_px(k) for k in ("hall_pad", "hall_top", "hall_neck", "hall_foot"))
    return [(_cx(0) - pad, _ry(0) - top, _cx(4) + CARD_W + pad, _ry(3) - neck),
            (_cx(1) - pad, _ry(3) - neck, _cx(3) + CARD_W + pad, _ry(3) + CARD_H + foot)]


def hall_runner():
    """The blue runner down the aisle from the throne to the doors."""
    bottom = hall_boxes()[1][3]
    return (_cx(2) + _hall_px("runner_in"), _ry(1) - _hall_px("runner_top"),
            _cx(2) + CARD_W - _hall_px("runner_in"), bottom - _hall_px("runner_foot"))


def hall_doors():
    bottom = hall_boxes()[1][3]
    return (_cx(2) + _hall_px("door_in"), bottom - _hall_px("door_h"),
            _cx(2) + CARD_W - _hall_px("door_in"), bottom)


def hall_pillars():
    """The two pillars flanking the aisle, in the gaps either side of column 2."""
    top, bottom = hall_boxes()[0][1], hall_boxes()[1][3]
    half, inset = _hall_px("pillar_half"), _hall_px("runner_foot")
    out = []
    for x in (_cx(2) - CARD_GAP_X // 2, _cx(2) + CARD_W + CARD_GAP_X // 2):
        out.append((x - half, top + inset, x + half, bottom - inset))
    return out


def check_hall(cells=None):
    """THE GREAT HALL (spec 2.5, layout E): the fourteen seats in their tiers' cells,
    the throne's cell free, every card on the hall's stone, the runner, the doors and
    the pillars clear of every card, and the hall between its title and the fill
    button. The picture's half is check_dwf_art."""
    out = []
    cols, rows, throne, got = race_grid("dwf")
    planted = cells is not None
    cells = got if cells is None else cells
    tiers = [o["tier"] for o in IC.RACES["dwf"]["OFFICES"]]
    if len(cells) != len(tiers):
        out.append("the race table places %d seats and the Dwarf court has %d offices"
                   % (len(cells), len(tiers)))
    for t, want in sorted(HALL_TIER_CELLS.items()):
        have = set(c for c, tier in zip(cells, tiers) if tier == t)
        if have != want:
            out.append("tier %d sits at %s, not the spec's %s" % (t, sorted(have), sorted(want)))
    if len(set(cells)) != len(cells):
        out.append("two seats share a hall cell")
    if throne in cells:
        out.append("a seat stands on the throne's cell %s" % (throne,))
    for c, r in cells:
        if not (0 <= c < cols and 0 <= r < rows):
            out.append("cell %s is outside the %dx%d grid" % ((c, r), cols, rows))
    boxes = hall_boxes()
    grid = [_grid_xy(cols, c, r) for c, r in cells] if planted else list(CARD_GRID)
    clear = [("runner", hall_runner()), ("doors", hall_doors())] + [
        ("pillar", p) for p in hall_pillars()]
    for (x, y), cell in zip(grid, cells):
        if not any(a <= x and b <= y and x + CARD_W <= c and y + CARD_H <= d
                   for a, b, c, d in boxes):
            out.append("the card at cell %s stands off the hall's stone" % (cell,))
        for what, (a, b, c, d) in clear:
            if x < c and a < x + CARD_W and y < d and b < y + CARD_H:
                out.append("the card at cell %s covers the hall's %s" % (cell, what))
    zx, zy, zw, zh = PANEL_LAYOUT["ic_zig_bg"]
    if max(d for _a, _b, _c, d in boxes) > zy + zh:
        out.append("the hall runs past its picture's box (bottom %d)" % (zy + zh))
    if zy + zh > PANEL_LAYOUT["ic_fill"][1]:
        out.append("the hall ends at %d, under the fill button at %d"
                   % (zy + zh, PANEL_LAYOUT["ic_fill"][1]))
    ot = PANEL_LAYOUT["ic_off_title"]
    if ot[1] + ot[3] > min(b for _a, b, _c, _d in boxes):
        out.append("THE GREAT HALL's title runs onto the hall")
    return out
```

3h. In `check()`, replace `out.extend(check_ziggurat())` with:

```python
    out.extend(check_ziggurat() if RACE == "chd" else check_hall())
```

3i. Directly above `if BOX_W != 1920:` / `_scale_pass(globals(), BOX_W)` (line ~4805):

```python
# THE 1920 SIZES, taken before the scale pass. The Dwarf art is baked once, at 1920,
# and a copy at another box still names each picture by these numbers - which is
# also how ICUI.skin and ICUI.tab_art name them, from ICUI.BASE.
PANEL_LAYOUT_1920 = dict(PANEL_LAYOUT)
POOL_1920 = {"card": (CARD_W, CARD_H), "party": (PARTY_W, PARTY_H),
             "plot": (PLOT_W, PLOT_H), "law": (LAW_W, LAW_H)}
```

3j. Add `"DWF", "DWF_CELLS", "HALL_TIER_CELLS", "PANEL_LAYOUT_1920", "POOL_1920",` to `NOT_GEOMETRY` (line 4539): they are 1920 art and spec numbers, never scaled, and `_classify` refuses any layout number it does not know.

- [ ] **Step 4: Run it and see it pass.**

Run: `py tools\gen_ic_ui.py --selftest`
Expected: exit 0.

Run: `py tools\gen_ic_ui.py`
Expected: no `FAIL` line. If the existing crossing check reports `ic_throne` against one of its own three lines, find the exemption the Crown's box has (`Select-String -Path tools\gen_ic_ui.py -Pattern '"ic_crown_box"'` inside `check()`) and add `"ic_throne"` beside it; if it reports `ic_title` against `ic_help`, the help button's cell is wrong - it must start 8px after the title box ends (1118 + 8 = 1126).

- [ ] **Step 5: Checkpoint.** Run THE GATES. Expected: all green; `chd court unchanged`.

---

### Task 4: Bake the Dwarf plates

**Files:**
- Modify: `tools/gen_ic_ui.py` (path constants and bakers after `CHD_CUTS` / `cut_chd_art`; `art_paths`; `write_plates`; three checks; `NOT_GEOMETRY`)
- Writes (generated, packed): `Modding Files/pack/ui/derpy_ic/dwf_*.png`

**Interfaces:**
- Produces (Python): `DWF_SRC`, `DWF_TAB`, `DWF_FRAME`, `DWF_LINTEL`, `DWF_HEADING`, `DWF_HEADING_BARE`, `DWF_HALL`, `DWF_THRONE`, `DWF_SEATS`, `DWF_PANEL_BG`, `DWF_OPENER_ICON`, `DWF_BACKDROP_SRC`, `DWF_RIBBON`, `DWF_RIBBON_CUTS`, `DWF_FRAMED`, `DWF_TAB_STATES`, `_ca_png(pack, path)`, `dwf_ribbon(state, w, h, dim=None)`, `dwf_knot_frame(w, h, k=1.0)`, `dwf_knot_scale(w, h, cells=None)`, `dwf_frame_cells(w, h)`, `dwf_lintel()`, `dwf_heading(bare=False)`, `dwf_hall()`, `dwf_throne()`, `dwf_seats()`, `dwf_tab_sizes()`, `dwf_frame_sizes()`, `dwf_art_paths()`, `dwf_plates()`, `check_dwf_art()`, `check_dwf_contrast(images=None)` (the ribbon contrast phase 6 Task 3 Step 3 looks for), `check_dwf_frame_ink(images=None)`.
- Picture names (all under `ui/derpy_ic/`): `dwf_tab_<active|hover|selected>_<w>x<h>.png` for each tab cell size (240x32, 300x32, 204x34, 372x34; baked `tab_grow` = 6px taller), `dwf_frame_<w>x<h>.png` for the four pools (364x184, 455x266, 364x176, 306x150) and every panel plate that wears `CARD_LAYERS`, `dwf_title.png`, `dwf_heading.png`, `dwf_heading_bare.png`, `dwf_hall.png` (`ic_zig_bg`'s box), `dwf_throne.png` (364x184), `dwf_seats.png` (`ic_influence`'s box), `dwf_panel_bg.png` (Task 6).

- [ ] **Step 1: The failing check.** Above `def selftest():` add:

```python
def selftest_dwf_art():
    """THE DWARF PLATES (plan 2026-10-04 phase 3, Task 4). Needs the game installed:
    every Dwarf picture is cut from CA's own."""
    if _ca_png("ui2.pack", DWF_SRC + "decor_units_header.png") is None:
        print("  (no game install - the Dwarf art selftest is skipped)")
        return
    d = _dwf()
    plates = d.dwf_plates()
    assert set(plates) | {DWF_PANEL_BG} == d.dwf_art_paths(), \
        sorted(set(plates) ^ (d.dwf_art_paths() - {DWF_PANEL_BG}))
    for path, img in plates.items():
        want = d._dwf_size(path)
        assert img.size == want, "%s is %s, named for %s" % (path, img.size, want)
    # FLAT MIDDLES: the lintel and the headings are nine-sliced across their middles.
    assert d._flat_middle(plates[DWF_LINTEL], d.DWF["title_cap"])
    bad = plates[DWF_LINTEL].copy()
    bad.putpixel((bad.width // 2, bad.height // 2), (255, 0, 0, 255))
    assert not d._flat_middle(bad, d.DWF["title_cap"]), "a spotted middle passed as flat"
    # CONTRAST: the shipped ribbons pass; an undimmed blue one does not.
    assert not d.check_dwf_contrast(plates), d.check_dwf_contrast(plates)
    loud = dict(plates)
    loud[DWF_TAB % ("active", 240, 32)] = d.dwf_ribbon("active", 240, 32, dim=1.0)
    assert any("active" in p for p in d.check_dwf_contrast(loud)), "an undimmed ribbon passed"
    # INK: a frame at full scale over a cell in its corner is caught.
    assert d._ink_in(d.dwf_knot_frame(364, 184, 1.0), [(0, 0, 30, 30)])
    assert not d.check_dwf_frame_ink(plates), d.check_dwf_frame_ink(plates)
```

and call `selftest_dwf_art()` in `selftest()` after `selftest_hall()`.

- [ ] **Step 2: Run it and see it fail.**

Run: `py tools\gen_ic_ui.py --selftest`
Expected: `NameError: name '_ca_png' is not defined`.

- [ ] **Step 3: Implement.**

3a. Directly after `cut_chd_art` (and before `build_plates`), add the names, the reader and the bakers:

```python
# ---------------------------------------------------------------------------
# THE DWARF PLATES (plan 2026-10-04 phase 3; spec 2.6). Cut from CA's Book of
# Grudges kit and baked to their components' exact 1920 sizes, the way the approved
# mockup dwf_skin_mockup2.py builds them: caps and corners at a UNIFORM scale, runs
# mirror-tiled, nothing stretched. The game's own art, read offline.
DWF_SRC = "ui/skins/default/dlc25_book_of_grudges/"
DWF_BACKDROP_SRC = "ui/loading_ui/load_images/campaign_dwarfs1.png"
DWF_OPENER_ICON = "ui/skins/default/icon_book_grudges.png"
DWF_TAB = PLATE_DIR + "/dwf_tab_%s_%dx%d.png"
DWF_FRAME = PLATE_DIR + "/dwf_frame_%dx%d.png"
DWF_LINTEL = PLATE_DIR + "/dwf_title.png"
DWF_HEADING = PLATE_DIR + "/dwf_heading.png"
DWF_HEADING_BARE = PLATE_DIR + "/dwf_heading_bare.png"
DWF_HALL = PLATE_DIR + "/dwf_hall.png"
DWF_THRONE = PLATE_DIR + "/dwf_throne.png"
DWF_SEATS = PLATE_DIR + "/dwf_seats.png"
DWF_PANEL_BG = PLATE_DIR + "/dwf_panel_bg.png"
DWF_TAB_STATES = ("active", "hover", "selected")
# The lit plate is the gold one in both image slots; the unlit tab is blue, a shade
# lighter under the cursor.
DWF_RIBBON = {"active": "tab_button_unit_pack_active.png",
              "hover": "tab_button_unit_pack_selected.png",
              "selected": "tab_button_legendary_grudges_selected.png"}
# (left cap, middle start, middle end, right cap) in CA's source pixels, measured.
DWF_RIBBON_CUTS = {"tab_button_unit_pack_active.png": (34, 34, 144, 34),
                   "tab_button_unit_pack_selected.png": (34, 34, 151, 62),
                   "tab_button_legendary_grudges_selected.png": (34, 34, 151, 62)}
# Every panel plate _panel() gives CARD_LAYERS: each gets a knot frame baked to it.
DWF_FRAMED = tuple(LAW_PLATES) + ("ic_help_box", "ic_dial_box", "ic_crown_box")
INK = 245.0          # cream #FFF8D7, Rec.709 luminance
MIN_RATIO = 4.5

_CA_PNG = {}


def _ca_png(pack, path):
    """CA's picture out of the installed pack as RGBA, or None with no game."""
    if (pack, path) not in _CA_PNG:
        import io as _io
        import read_pack_index as RPI
        from read_vanilla_loc import _decompress
        from PIL import Image
        full, data = os.path.join(GAME_DATA, pack), None
        if os.path.isfile(full):
            for p, comp, blob in RPI.read(full, path):
                if p.lower() == path:
                    data = _decompress(blob) if comp else blob
        _CA_PNG[(pack, path)] = (Image.open(_io.BytesIO(data)).convert("RGBA")
                                 if data and data[:4] == b"\x89PNG" else None)
    return _CA_PNG[(pack, path)]


def _bog(name):
    img = _ca_png("ui2.pack", DWF_SRC + name)
    assert img is not None, "%s%s is not in ui2.pack" % (DWF_SRC, name)
    return img


def _scale_h(im, h):
    """A UNIFORM scale to height h: the art keeps its proportions."""
    from PIL import Image
    return im.resize((max(1, round(im.width * h / im.height)), h), Image.LANCZOS)


def _scale(im, k):
    from PIL import Image
    return im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)


def _tile_x(seg, w, mirror=False):
    """seg repeated across w; mirror flips every other copy so no join shows a seam."""
    from PIL import Image
    out = Image.new("RGBA", (max(1, w), seg.height), (0, 0, 0, 0))
    flip = seg.transpose(Image.FLIP_LEFT_RIGHT)
    x, k = 0, 0
    while x < w:
        piece = flip if (mirror and k % 2) else seg
        out.alpha_composite(piece.crop((0, 0, min(piece.width, w - x), piece.height)), (x, 0))
        x += seg.width
        k += 1
    return out


def _tile_y(seg, h):
    from PIL import Image
    out = Image.new("RGBA", (seg.width, max(1, h)), (0, 0, 0, 0))
    y = 0
    while y < h:
        out.alpha_composite(seg.crop((0, 0, seg.width, min(seg.height, h - y))), (0, y))
        y += seg.height
    return out


def _gold(im, colour=None):
    """CA's art as a silhouette in our gold: its alpha, one colour."""
    from PIL import Image
    g = Image.new("RGBA", im.size, (colour or DWF["gold"])[:3] + (255,))
    g.putalpha(im.split()[3])
    return g


def _chamfer(x0, y0, x1, y1, c):
    return [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c),
            (x1 - c, y1), (x0 + c, y1), (x0, y1 - c), (x0, y0 + c)]


def _dim(im, k):
    from PIL import Image
    if k == 1.0:
        return im
    r, g, b, a = im.split()
    rgb = Image.merge("RGB", (r, g, b)).point(lambda v: int(v * k))
    return Image.merge("RGBA", rgb.split() + (a,))


def dwf_ribbon(state, w, h, dim=None):
    """A tab ribbon for a w x h tab, baked tab_grow taller (its layer is lifted
    tab_lift and grown tab_grow, so the field centres on the cell). The blue field is
    dimmed so cream reads at 4.5:1; check_dwf_contrast holds both halves."""
    from PIL import Image
    name = DWF_RIBBON[state]
    src = _bog(name)
    H = h + DWF["tab_grow"]
    lc, m0, m1, rc = DWF_RIBBON_CUTS[name]
    left = _scale_h(src.crop((0, 0, lc, src.height)), H)
    right = _scale_h(src.crop((src.width - rc, 0, src.width, src.height)), H)
    mid = _scale_h(src.crop((m0, 0, m1, src.height)), H)
    out = Image.new("RGBA", (w, H), (0, 0, 0, 0))
    out.alpha_composite(_tile_x(mid, w - left.width - right.width, mirror=True), (left.width, 0))
    out.alpha_composite(left, (0, 0))
    out.alpha_composite(right, (w - right.width, 0))
    return _dim(out, DWF["ribbon_dim"][state] if dim is None else dim)


def dwf_knot_frame(w, h, k=1.0):
    """CA's confederation knotwork frame built to w x h at scale k: corners and the
    top ornament at k, the straight runs and sides tiled (mockup frame_img)."""
    from PIL import Image
    src = _bog("book_of_grudges_confederation_frame.png")
    if k != 1.0:
        src = _scale(src, k)
    sw, sh = src.size

    def s(v):
        return round(v * k)
    c = s(DWF["frame_corner"])
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    top, bot = src.crop((0, 0, sw, c)), src.crop((0, sh - c, sw, sh))
    orn = top.crop((s(DWF["frame_orn"][0]), 0, s(DWF["frame_orn"][1]), c))
    run_t = top.crop((s(DWF["frame_run"][0]), 0, s(DWF["frame_run"][1]), c))
    run_b = bot.crop((s(DWF["frame_run"][0]), 0, s(DWF["frame_run"][1]), c))
    side_l = src.crop((0, s(DWF["frame_side"][0]), c, s(DWF["frame_side"][1])))
    side_r = src.crop((sw - c, s(DWF["frame_side"][0]), sw, s(DWF["frame_side"][1])))
    out.alpha_composite(_tile_y(side_l, h - c * 2), (0, c))
    out.alpha_composite(_tile_y(side_r, h - c * 2), (w - c, c))
    out.alpha_composite(_tile_x(run_t, w - c * 2), (c, 0))
    out.alpha_composite(_tile_x(run_b, w - c * 2), (c, h - c))
    if orn.width <= w - c * 2:
        out.alpha_composite(orn, ((w - orn.width) // 2, 0))
    for sx, sy, dx, dy in ((0, 0, 0, 0), (sw - c, 0, w - c, 0),
                           (0, sh - c, 0, h - c), (sw - c, sh - c, w - c, h - c)):
        out.alpha_composite(src.crop((sx, sy, sx + c, sy + c)), (dx, dy))
    return out


def _ink_in(img, cells, alpha=32):
    """True when the picture's ink (alpha over `alpha`) reaches into any cell."""
    a = img.split()[3]
    for x, y, cw, ch in cells:
        box = (max(0, x), max(0, y), min(img.width, x + cw), min(img.height, y + ch))
        if box[2] > box[0] and box[3] > box[1] and a.crop(box).getextrema()[1] > alpha:
            return True
    return False


def dwf_frame_cells(w, h):
    """Every cell drawn inside a box of this 1920 size, relative to the box: the
    pooled card's own cells, or the panel cells a framed panel plate holds."""
    out = []
    for pool, layout in (("card", CARD_LAYOUT), ("party", PARTY_LAYOUT),
                         ("plot", PLOT_LAYOUT), ("law", LAW_LAYOUT)):
        if POOL_1920[pool] == (w, h):
            out += list(layout.values())
    for n in DWF_FRAMED:
        x, y, bw, bh = PANEL_LAYOUT_1920[n]
        if (bw, bh) != (w, h):
            continue
        for m, (cx, cy, cw, ch) in PANEL_LAYOUT_1920.items():
            if m == n or m in DWF_FRAMED:
                continue
            if x <= cx and y <= cy and cx + cw <= x + bw and cy + ch <= y + bh:
                out.append((cx - x, cy - y, cw, ch))
    return out


def dwf_knot_scale(w, h, cells=None):
    """The largest twentieth from 1.0 down to 0.4 at which the knot frame's ink
    stays out of every cell inside the box. Measured, never typed per box."""
    cells = dwf_frame_cells(w, h) if cells is None else cells
    for i in range(20, 7, -1):
        k = i / 20.0
        if round(DWF["frame_corner"] * k) * 2 >= min(w, h):
            continue
        if not _ink_in(dwf_knot_frame(w, h, k), cells):
            return k
    raise SystemExit("no knot frame from 1.0 down to 0.4 leaves the cells of a %dx%d box clear"
                     % (w, h))


def dwf_lintel():
    """THE TITLE'S LINTEL (spec 2.6, title A): dark stone, a gold rule, the gold Dwarf
    face in the left cap. 2*title_cap + 16 wide; its middle columns are identical."""
    from PIL import Image, ImageDraw
    cap, h = DWF["title_cap"], DWF["title_box"][3]
    w = cap * 2 + 16
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    poly = _chamfer(0, 0, w - 1, h - 1, DWF["lintel_chamfer"])
    d.polygon(poly, fill=DWF["lintel"])
    d.line(poly + [poly[0]], fill=DWF["gold"], width=3)
    inner = _chamfer(6, 6, w - 7, h - 7, DWF["lintel_chamfer"] - 3)
    d.line(inner + [inner[0]], fill=DWF["gold_dim"], width=1)
    face = _gold(_scale_h(_bog("book_of_grudges_legendary_grudges_decor_2.png"), h - 10))
    assert face.width + 8 <= cap, "the face (%dpx) overruns the %dpx cap" % (face.width, cap)
    im.alpha_composite(face, (8, 5))
    return im


def dwf_heading(bare=False):
    """THE HEADING PLATE (spec 2.6, headings B): CA's units-header mark in gold at
    each end and, unless bare, a 2px gold rule under the words ending in the knot
    rule's diamonds. Transparent between: the words stand on the backdrop, which
    make_ic_backdrop measures them against. 2*heading_cap + 16 wide; flat middle."""
    from PIL import Image, ImageDraw
    cap, h = DWF["heading_cap"], HEADING_H
    w = cap * 2 + 16
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    mark = _gold(_bog("decor_units_header.png"))
    assert DWF["mark_x"] + mark.width <= cap, "the heading mark overruns the cap"
    y = DWF["mark_mid"] - mark.height // 2
    im.alpha_composite(mark, (DWF["mark_x"], y))
    im.alpha_composite(mark.transpose(Image.FLIP_LEFT_RIGHT),
                       (w - DWF["mark_x"] - mark.width, y))
    if not bare:
        ry = DWF["rule_y"]
        ImageDraw.Draw(im).rectangle((0, ry, w - 1, ry + 1), fill=DWF["gold"])
        rule = _bog("book_of_grudges_confederation_decor_2.png")
        dia = _gold(_scale_h(rule.crop((0, 0, rule.height, rule.height)), DWF["diamond"]))
        dy = ry + 1 - dia.height // 2
        im.alpha_composite(dia, (0, dy))
        im.alpha_composite(dia.transpose(Image.FLIP_LEFT_RIGHT), (w - dia.width, dy))
    return im


def dwf_hall():
    """THE GREAT HALL in ic_zig_bg's box (mockup shape_hall, round 3): stone with a
    gold rim, the blue runner from the throne to the doors, two pillars, the doors
    with their runes, runes down the runner, and CA's knot rule under the title."""
    from PIL import Image, ImageDraw
    x0, y0, w, h = PANEL_LAYOUT_1920["ic_zig_bg"]
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    def rel(b):
        return (b[0] - x0, b[1] - y0, b[2] - x0 - 1, b[3] - y0 - 1)
    nave, foot = hall_boxes()
    for b in (nave, foot):
        d.rectangle(rel(b), fill=DWF["stone"])
    a, b, c, e = rel(nave)
    fa, _fb, fc, fe = rel(foot)
    rim = [(a, b), (c, b), (c, e), (fc, e), (fc, fe), (fa, fe), (fa, e), (a, e), (a, b)]
    d.line(rim, fill=DWF["gold"], width=DWF["hall_rim"])
    d.rectangle(rel(hall_runner()), fill=DWF["runner"])
    for p in hall_pillars():
        d.rectangle(rel(p), fill=DWF["pillar"], outline=DWF["gold_dim"])
    da, db, dc, de = rel(hall_doors())
    d.rectangle((da, db, dc, de), fill=DWF["door"], outline=DWF["gold_dim"])
    i = DWF["door_inset"]
    d.rectangle((da + i, db + i, dc - i, de), outline=DWF["gold_dim"])
    mid = (da + dc) // 2
    d.line([(mid, db + i), (mid, de)], fill=DWF["gold_dim"])
    k = DWF["knob"]
    for kx in (mid - k * 3, mid + k * 3):
        d.ellipse((kx - k, (db + de) // 2 - k, kx + k, (db + de) // 2 + k), fill=DWF["gold"])

    def rune(n):
        return _gold(_scale_h(_bog("rune_%d_panel.png" % n), DWF["rune_px"]), DWF["gold_dim"])
    for n, cx in ((1, (da + mid) // 2), (3, (mid + dc) // 2)):
        g = rune(n)
        im.alpha_composite(g, (cx - g.width // 2, (db + de) // 2 - g.height // 2))
    ra, rb, rc, _re = rel(hall_runner())
    y, n = rb + DWF["runner_top"] + DWF["rune_top"], 0
    while y + DWF["rune_px"] <= db - DWF["rune_clear"]:
        g = rune(n % 5 + 1)
        im.alpha_composite(g, ((ra + rc) // 2 - g.width // 2, y))
        y += DWF["rune_step"]
        n += 1
    rule = _gold(_bog("book_of_grudges_confederation_decor_2.png"))
    im.alpha_composite(rule, (w // 2 - rule.width // 2, DWF["hall_rule_y"] - y0))
    return im


def dwf_throne():
    """THE THRONE (spec 2.5): a dark field in the knot frame, CA's Dwarf-face
    ornament in gold at half size above the three lines."""
    from PIL import Image, ImageDraw
    _x, _y, w, h = PANEL_LAYOUT_1920["ic_throne"]
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rectangle((0, 0, w - 1, h - 1), fill=DWF["throne_field"])
    cells = list(DWF["throne_cells"].values())
    im.alpha_composite(dwf_knot_frame(w, h, dwf_knot_scale(w, h, cells)))
    face = _gold(_scale(_bog("book_of_grudges_unit_pack_decor.png"), DWF["throne_face"]))
    im.alpha_composite(face, ((w - face.width) // 2, DWF["throne_face_top"]))
    return im


def dwf_seats():
    """The seats counter's plate: a chamfered dark field in a gold rule."""
    from PIL import Image, ImageDraw
    _x, _y, w, h = PANEL_LAYOUT_1920["ic_influence"]
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    poly = _chamfer(0, 0, w - 1, h - 1, DWF["seats_chamfer"])
    d.polygon(poly, fill=DWF["seats_field"])
    d.line(poly + [poly[0]], fill=DWF["gold"], width=2)
    return im


def dwf_tab_sizes():
    """Every tab-shaped cell's 1920 size: the tabs, the help topics, the law buttons."""
    return sorted(set(tuple(PANEL_LAYOUT_1920[n][2:]) for n in PANEL_LAYOUT_1920
                      if n.startswith(("ic_tab_", "ic_help_topic_")) or n in LAW_TAB_BUTTONS))


def dwf_frame_sizes():
    sizes = set(POOL_1920.values())
    sizes.update(tuple(PANEL_LAYOUT_1920[n][2:]) for n in DWF_FRAMED)
    return sorted(sizes)


def dwf_art_paths():
    """Every Dwarf picture this pack owns, named without rasterising any of it."""
    out = {DWF_LINTEL, DWF_HEADING, DWF_HEADING_BARE, DWF_HALL, DWF_THRONE, DWF_SEATS,
           DWF_PANEL_BG}
    for w, h in dwf_tab_sizes():
        for st in DWF_TAB_STATES:
            out.add(DWF_TAB % (st, w, h))
    for w, h in dwf_frame_sizes():
        out.add(DWF_FRAME % (w, h))
    return out


def _dwf_size(path):
    """The size a Dwarf picture's name promises."""
    m = re.search(r"_(\d+)x(\d+)\.png$", path)
    if m:
        w, h = int(m.group(1)), int(m.group(2))
        return (w, h + DWF["tab_grow"]) if "/dwf_tab_" in path else (w, h)
    return {DWF_LINTEL: (DWF["title_cap"] * 2 + 16, DWF["title_box"][3]),
            DWF_HEADING: (DWF["heading_cap"] * 2 + 16, HEADING_H),
            DWF_HEADING_BARE: (DWF["heading_cap"] * 2 + 16, HEADING_H),
            DWF_HALL: tuple(PANEL_LAYOUT_1920["ic_zig_bg"][2:]),
            DWF_THRONE: tuple(PANEL_LAYOUT_1920["ic_throne"][2:]),
            DWF_SEATS: tuple(PANEL_LAYOUT_1920["ic_influence"][2:]),
            DWF_PANEL_BG: (PANEL_W, PANEL_H)}[path]


_PLATES = []


def dwf_plates():
    """{in-pack path: PIL image} for every Dwarf plate but the backdrop. Only the
    Dwarf copy at 1920 bakes: the throne's and the hall's boxes are its cells."""
    assert RACE == "dwf" and BOX_W == 1920, "bake the Dwarf plates from _dwf()"
    if _PLATES:
        return _PLATES[0]
    out = {DWF_LINTEL: dwf_lintel(), DWF_HEADING: dwf_heading(),
           DWF_HEADING_BARE: dwf_heading(bare=True), DWF_HALL: dwf_hall(),
           DWF_THRONE: dwf_throne(), DWF_SEATS: dwf_seats()}
    for w, h in dwf_tab_sizes():
        for st in DWF_TAB_STATES:
            out[DWF_TAB % (st, w, h)] = dwf_ribbon(st, w, h)
    for w, h in dwf_frame_sizes():
        out[DWF_FRAME % (w, h)] = dwf_knot_frame(w, h, dwf_knot_scale(w, h))
    _PLATES.append(out)
    return out
```

3b. In `art_paths()`, directly after `out.add(PANEL_BG)`:

```python
    # The Chaos Dwarf backdrop and every Dwarf picture, whichever race this copy is:
    # the pack ships both, and write_plates() prunes anything not named here.
    out.add("ui/derpy_ic/panel_bg.png")
    out.update(dwf_art_paths())
```

3c. In `write_plates()`, directly after the `for path, rows in wedge_art():` loop and before `folder = ...`:

```python
    if _ca_png("ui2.pack", DWF_SRC + "decor_units_header.png") is not None:
        import io as _io
        for path, img in sorted(_dwf().dwf_plates().items()):
            disk = os.path.join(ROOT, "Modding Files", "pack", *path.split("/"))
            buf = _io.BytesIO()
            img.save(buf, "PNG")
            if not os.path.isfile(disk) or open(disk, "rb").read() != buf.getvalue():
                open(disk, "wb").write(buf.getvalue())
                written.append(disk)
    else:
        print("  (no game install at %s - Dwarf plates not baked)" % GAME_DATA)
```

3d. The three checks, after `dwf_plates`:

```python
def _flat_middle(img, cap):
    """True when every column between the caps is the same column."""
    mid = img.crop((cap, 0, img.width - cap, img.height))
    first = mid.crop((0, 0, 1, mid.height)).tobytes()
    return all(mid.crop((x, 0, x + 1, mid.height)).tobytes() == first for x in range(mid.width))


def _disk_plates():
    from PIL import Image
    out = {}
    for path in sorted(dwf_art_paths() - {DWF_PANEL_BG}):
        disk = os.path.join(ROOT, "Modding Files", "pack", *path.split("/"))
        if os.path.isfile(disk):
            out[path] = Image.open(disk).convert("RGBA")
    return out


def check_dwf_art():
    """Every Dwarf picture is on disk, listed in art_paths(), the size its component
    draws it at, what this generator bakes today, and flat where it is nine-sliced;
    and every card stands on the hall's stone in the picture, not only in the boxes."""
    from PIL import Image, ImageChops
    out = []
    disk = _disk_plates()
    listed = art_paths()
    for path in sorted(dwf_art_paths()):
        if path not in listed:
            out.append("%s is not in art_paths(): write_plates() prunes it" % path)
        if path == DWF_PANEL_BG:
            continue
        if path not in disk:
            out.append("%s is not written: run py tools/gen_ic_ui.py" % path)
            continue
        if disk[path].size != _dwf_size(path):
            out.append("%s is %dx%d, its component draws %dx%d"
                       % ((path,) + disk[path].size + _dwf_size(path)))
    # THE DRIFT CHECK, in the Dwarf copy at 1920 only: that copy bakes the plates
    # itself, and a copy at another box would bake a second set to compare with.
    if disk and BOX_W == 1920 and _ca_png("ui2.pack", DWF_SRC + "decor_units_header.png") is not None:
        for path, img in sorted(dwf_plates().items()):
            have = disk.get(path)
            if have is not None and ImageChops.difference(have, img).getbbox():
                out.append("%s on disk differs from what this generator bakes" % path)
    for path, cap in ((DWF_LINTEL, DWF["title_cap"]), (DWF_HEADING, DWF["heading_cap"]),
                      (DWF_HEADING_BARE, DWF["heading_cap"])):
        if path in disk and not _flat_middle(disk[path], cap):
            out.append("%s is not flat between its caps: the 9-slice would stretch a picture"
                       % path)
    hall = disk.get(DWF_HALL)
    if hall is not None and RACE == "dwf":
        x0, y0, w, h = PANEL_LAYOUT["ic_zig_bg"]
        a = hall.split()[3].resize((w, h))
        for cx, cy in CARD_GRID:
            for px, py in ((cx - 1, cy - 1), (cx + CARD_W, cy - 1),
                           (cx - 1, cy + CARD_H), (cx + CARD_W, cy + CARD_H)):
                u, v = px - x0, py - y0
                if not (0 <= u < w and 0 <= v < h) or a.getpixel((u, v)) == 0:
                    out.append("the card at (%d, %d) hangs off the hall's picture at (%d, %d)"
                               % (cx, cy, px, py))
    return out


def _lum_q(img, box, q):
    """Luminance quantile q (Rec.709 of the stored values, composited on black)."""
    from PIL import Image
    ground = Image.new("RGBA", img.size, (0, 0, 0, 255))
    ground.alpha_composite(img)
    raw = ground.convert("RGB").crop(box).tobytes()
    lum = sorted(0.2126 * raw[i] + 0.7152 * raw[i + 1] + 0.0722 * raw[i + 2]
                 for i in range(0, len(raw), 3))
    return lum[min(len(lum) - 1, int(len(lum) * q))]


def _cream(p95):
    return (INK / 255.0 + 0.05) / (p95 / 255.0 + 0.05)


def _dark(p5):
    return (p5 / 255.0 + 0.05) / 0.05


def _ribbon_field(img, inset):
    """(top, bottom) rows of the ribbon's flat field: the rows whose median luminance
    is within 12 of the middle row's, grown out from the middle."""
    def med(y):
        return _lum_q(img, (inset, y, img.width - inset, y + 1), 0.5)
    rows = [med(y) for y in range(img.height)]
    m = img.height // 2
    a = b = m
    while a > 0 and abs(rows[a - 1] - rows[m]) <= 12:
        a -= 1
    while b < img.height - 1 and abs(rows[b + 1] - rows[m]) <= 12:
        b += 1
    return a, b + 1


def check_dwf_contrast(images=None):
    """THE RIBBONS AND THE PLATES, against their own ground (spec section 10): cream
    at 4.5:1 on the blue ribbon (active and hover), dark ink at 4.5:1 on the gold
    lit ribbon, cream on the lintel, the throne's three lines and the seats plate.
    And each blue dim is the LARGEST hundredth that passes: a ribbon darker than it
    needs is a fault too."""
    out = []
    plates = _disk_plates() if images is None else images
    inset = DWF["tab_text_inset"]
    for w, h in dwf_tab_sizes():
        for st in DWF_TAB_STATES:
            img = plates.get(DWF_TAB % (st, w, h))
            if img is None:
                out.append("no %s ribbon at %dx%d to measure" % (st, w, h))
                continue
            top, bot = _ribbon_field(img, inset)
            if bot - top < BODY[0]:
                out.append("the %s ribbon's field is %dpx, under one line of %dpx text"
                           % (st, bot - top, BODY[0]))
            box = (inset, top, w - inset, bot)
            if st == "selected":
                r = _dark(_lum_q(img, box, 0.05))
                if r < MIN_RATIO:
                    out.append("dark ink on the gold %dx%d ribbon reads %.1f:1" % (w, h, r))
                continue
            r = _cream(_lum_q(img, box, 0.95))
            if r < MIN_RATIO:
                out.append("cream on the %s %dx%d ribbon reads %.1f:1" % (st, w, h, r))
            k = DWF["ribbon_dim"][st]
            if images is None and k < 1.0:
                up = dwf_ribbon(st, w, h, dim=round(k + 0.01, 2))
                if _cream(_lum_q(up, box, 0.95)) >= MIN_RATIO:
                    out.append("the %s ribbon is dimmed to %.2f and %.2f would pass: dim it less"
                               % (st, k, k + 0.01))
    lintel = plates.get(DWF_LINTEL)
    if lintel is not None:
        cap = DWF["title_cap"]
        r = _cream(_lum_q(lintel, (cap, 6, lintel.width - cap, lintel.height - 6), 0.95))
        if r < MIN_RATIO:
            out.append("cream on the title's lintel reads %.1f:1" % r)
    throne = plates.get(DWF_THRONE)
    if throne is not None:
        for n, (x, y, cw, ch) in sorted(DWF["throne_cells"].items()):
            r = _cream(_lum_q(throne, (x, y, x + cw, y + ch), 0.95))
            if r < MIN_RATIO:
                out.append("%s reads %.1f:1 on the throne" % (n, r))
    seats = plates.get(DWF_SEATS)
    if seats is not None:
        r = _cream(_lum_q(seats, (SEATS_PAD, 4, seats.width - SEATS_PAD, seats.height - 4), 0.95))
        if r < MIN_RATIO:
            out.append("the seats count reads %.1f:1 on its plate" % r)
    return out


def check_dwf_frame_ink(images=None):
    """No knot frame's ink reaches into a cell it holds (alpha over 32). At 1920
    only: the frames are baked at 1920 and the cells compared are 1920 cells."""
    out = []
    if BOX_W != 1920:
        return out
    plates = _disk_plates() if images is None else images
    for w, h in dwf_frame_sizes():
        img = plates.get(DWF_FRAME % (w, h))
        if img is not None and _ink_in(img, dwf_frame_cells(w, h)):
            out.append("the %dx%d knot frame draws over a cell it holds" % (w, h))
    throne = plates.get(DWF_THRONE)
    if throne is not None and RACE == "dwf":
        frame_only = dwf_knot_frame(throne.width, throne.height,
                                    dwf_knot_scale(throne.width, throne.height,
                                                   list(DWF["throne_cells"].values())))
        if _ink_in(frame_only, list(DWF["throne_cells"].values())):
            out.append("the throne's frame draws over its lines")
    return out
```

3e. Call the three from `check()` for the Dwarf copy: directly after the line `out.extend(check_ziggurat() if RACE == "chd" else check_hall())` add:

```python
    if RACE == "dwf":
        out.extend(check_dwf_art())
        out.extend(check_dwf_contrast())
        out.extend(check_dwf_frame_ink())
```

3f. Add `"DWF_RIBBON_CUTS", "INK", "MIN_RATIO", "_CA_PNG", "_PLATES",` to `NOT_GEOMETRY`.

- [ ] **Step 4: Run it and see it pass.**

Run: `py tools\gen_ic_ui.py`
Expected: `wrote ...ui\derpy_ic\dwf_*.png` for the 12 ribbons, the frames, the title, both headings, the hall, the throne and the seats plate; no `FAIL` line (the backdrop is Task 6's, and nothing draws it yet).

Run: `py tools\gen_ic_ui.py --selftest`
Expected: exit 0.

If `check_dwf_contrast` reports a blue dim that passes one hundredth higher, or one that fails: find the largest passing hundredth (`py -c "import sys; sys.path.insert(0,'tools'); import gen_ic_ui as U; d=U._dwf(); [print(st, k/100.0) for st in ('active','hover') for k in range(100,30,-1) if not [p for p in d.check_dwf_contrast({d.DWF_TAB % (st,240,32): d.dwf_ribbon(st,240,32,dim=k/100.0)}) if st in p and 'reads' in p]][:2]"` prints candidates; take the first per state) and put it in `DWF["ribbon_dim"]`, then re-run this step.

Open three pictures and look at them before going on: `Modding Files\pack\ui\derpy_ic\dwf_tab_selected_240x32.png`, `dwf_frame_364x184.png`, `dwf_hall.png`. They must match the approved mockup `Modding Files\source\iron_court_preview\dwf_skin_E_offices_v2.png`; any visible seam, squashed ornament or misplaced rune is a fault here, not at the preview.

- [ ] **Step 5: Checkpoint.** Run THE GATES. Expected: all green; `chd court unchanged`.

---

### Task 5: The Dwarf panel's layers, its text cells and its race-art check

**Files:**
- Modify: `tools/gen_ic_ui.py` (the skin block after `TITLE_LAYERS`; the text block after `TEXT_STYLE`; `_panel()` branches; `check_dwf_text`; `DWF_KEEPS`, `chd_art`, `check_race_art`; `check()`)

**Interfaces:**
- Produces (Python): `ribbon_kw(name)`, `framed(name)`, `RIBBON_TEXT`, `DWF_SEATS_LAYERS`, `DWF_BARE_LAYERS`, `DWF_KEEPS`, `DWF_KEEP_PREFIXES`, `CHD_ART`, `chd_art(path)`, `check_race_art(text=None)`. The Dwarf panel file now carries every panel-level Dwarf picture.
- Consumed by: Task 9 (import gate), Task 11 (the preview's race-art problem lines), Task 15 (the author's `DWF_KEEPS` ruling).

- [ ] **Step 1: The failing check.** Above `def selftest():` add:

```python
def selftest_dwf_panel():
    """THE DWARF PANEL FILE (plan 2026-10-04 phase 3, Task 5)."""
    d = _dwf()
    text = d.build_xml()[d.PANEL_FILE]
    for path in (DWF_LINTEL, DWF_HEADING, DWF_HEADING_BARE, DWF_HALL, DWF_THRONE,
                 DWF_SEATS, DWF_PANEL_BG, DWF_TAB % ("active", 240, 32),
                 DWF_TAB % ("hover", 240, 32), DWF_FRAME % d.PANEL_LAYOUT_1920["ic_dial_box"][2:]):
        assert 'imagepath="%s"' % path in text, "the Dwarf panel never draws %s" % path
    for path in ("ui/derpy_ic/chd_title.png", "ui/derpy_ic/chd_heading.png",
                 "ui/derpy_ic/chd_tab_active.png", "ui/derpy_ic/offices_ziggurat.png",
                 "ui/derpy_ic/panel_bg.png", "ui/derpy_ic/chd_frame.png"):
        assert path not in text, "the Dwarf panel still draws %s" % path
    assert not d.check_race_art(text), d.check_race_art(text)
    planted = text + '<x imagepath="ui/skins/default/dlc23_chd_hell_forge/forge_fire.png"/>'
    assert d.check_race_art(planted), "Chaos Dwarf art outside DWF_KEEPS passed"
    # The Chaos Dwarf panel file is untouched by any of it.
    assert 'imagepath="ui/derpy_ic/chd_title.png"' in build_xml()[PANEL_FILE]
```

and call `selftest_dwf_panel()` in `selftest()` after `selftest_dwf_art()`.

- [ ] **Step 2: Run it and see it fail.**

Run: `py tools\gen_ic_ui.py --selftest`
Expected: `AssertionError: the Dwarf panel never draws ui/derpy_ic/dwf_title.png`.

- [ ] **Step 3: Implement.**

3a. Directly after the `TITLE_LAYERS = [...]` definition (the line after `fit_plate`):

```python
# THE DWARF SKIN'S PANEL LAYERS (plan 2026-10-04 phase 3; spec 2.6). Rebound here,
# in the Dwarf copy only, after every Chaos Dwarf value they replace is defined.
# Every picture is baked to its 1920 cell (Task 4), named by that size even in a
# compact copy, whose cells are smaller and whose pictures scale with them.
if RACE == "dwf":
    _old = {TITLE_CAP: DWF["title_cap"], HEADING_CAP: DWF["heading_cap"]}
    TITLE_CAP, HEADING_CAP = DWF["title_cap"], DWF["heading_cap"]
    FIT_PLATES = dict((k, (_old.get(cap, cap), left)) for k, (cap, left) in FIT_PLATES.items())
    del _old
    TAB_TEXT_INSET = DWF["tab_text_inset"]
    TITLE_ART, TITLE_TY = DWF_LINTEL, "0.00,0.00"
    TITLE_LAYERS = [{"path": DWF_LINTEL, "offset": (0, 0), "dw": 0, "dh": 0,
                     "margin": (0, TITLE_CAP), "dock": None}]
    HEADING_ART = DWF_HEADING
    HEADER_LAYERS = [{"path": DWF_HEADING, "offset": (0, 0), "dw": 0, "dh": 0,
                      "margin": (0, HEADING_CAP), "dock": None}]
    PANEL_BG = DWF_PANEL_BG
    PANEL_LAYERS = [dict(PANEL_LAYERS[0], path=DWF_PANEL_BG)]
# The hall's own title wears the marks without the rule: the hall picture carries
# the full knot rule under it.
DWF_BARE_LAYERS = [{"path": DWF_HEADING_BARE, "offset": (0, 0), "dw": 0, "dh": 0,
                    "margin": (0, DWF["heading_cap"]), "dock": None}]
DWF_SEATS_LAYERS = [{"path": DWF_SEATS, "offset": (0, 0), "dw": 0, "dh": 0,
                     "margin": DWF["seats_chamfer"], "dock": None}]


def ribbon_kw(name):
    """The plate a tab-shaped button wears: CA's skull tab, or the Dwarf ribbon baked
    to this cell's 1920 size, lifted tab_lift and grown tab_grow so its field centres
    on the cell. Margin ribbon_cap: the caps never scale, the mirror-tiled middle does."""
    if RACE != "dwf":
        return {"layers": TAB_LAYERS, "hover": TAB_HOVER}
    w, h = PANEL_LAYOUT_1920[name][2:]

    def lay(state):
        return [{"path": DWF_TAB % (state, w, h), "offset": (0, -DWF["tab_lift"]),
                 "dw": 0, "dh": DWF["tab_grow"], "margin": (0, DWF["ribbon_cap"]),
                 "dock": None}]
    return {"layers": lay("active"), "hover": lay("hover")}


def framed(name):
    """CARD_LAYERS for a panel plate: the tiled body, and the frame - CA's in the
    Chaos Dwarf panel, the knot frame baked to this plate's 1920 size in the Dwarf's
    (margin 0: it is exactly the plate)."""
    if RACE != "dwf":
        return CARD_LAYERS
    w, h = PANEL_LAYOUT_1920[name][2:]
    return [CARD_LAYERS[0], dict(CARD_LAYERS[1], path=DWF_FRAME % (w, h), margin=0)]
```

Note `PANEL_LAYOUT_1920` is assigned later in the file (Task 3, 3i); `ribbon_kw` and `framed` read it at call time, inside `_panel()`, which runs after the whole module has loaded.

3b. Directly after `TAB_TEXT = {...}` (line ~3698):

```python
# The tab caption on a Dwarf ribbon sits on the ribbon's field, which the lift and
# the grow put 2.5px above the cell's middle.
RIBBON_TEXT = dict(TAB_TEXT, ty=DWF["tab_ty"]) if RACE == "dwf" else TAB_TEXT
```

3c. Directly after the closing `}` of `TEXT_STYLE = {`:

```python
if RACE == "dwf":
    # THE THRONE'S THREE LINES: its prefix and its king at 16, the faction at the
    # headings' 20. (Task 8 makes the name and the king cut cells, with the Lua
    # that cuts them.)
    TEXT_STYLE["ic_throne_of"] = (16, "header_16")
    TEXT_STYLE["ic_throne_name"] = TITLE
    TEXT_STYLE["ic_throne_leader"] = (16, "header_16")
```

3d. In `_panel()`:
- In the `if name == "ic_zig_bg":` branch, change `{"path": ZIG_PATH, ...` to `{"path": ZIG_PATH if RACE == "chd" else DWF_HALL, ...`.
- Directly before `if name in LAW_PLATES:` add:

```python
        if name == "ic_throne":
            # THE THRONE (spec 2.5): one baked picture, not interactive, under its
            # three lines (tier -1 in _panel_order).
            panel.add(EU.C(name, w, h, layers=[
                {"path": DWF_THRONE, "offset": (0, 0), "dw": 0, "dh": 0,
                 "margin": 0, "colour": None, "dock": None}]))
            continue
        if name in ("ic_throne_of", "ic_throne_name", "ic_throne_leader"):
            panel.add(EU.C(name, w, h, align="Center", valign="Center",
                           tx="0.00,0.00", ty=LABEL_TY, **style(name)))
            continue
```

- In the `if name in LAW_PLATES:` branch change `layers=CARD_LAYERS` to `layers=framed(name)`; the same in the `ic_help_box`, `ic_dial_box` and `ic_crown_box` branches.
- In the `if name in LAW_TAB_BUTTONS:` branch change `layers=TAB_LAYERS, hover=TAB_HOVER, **TAB_TEXT))` to `**dict(ribbon_kw(name), **RIBBON_TEXT)))`; the same change in the `elif name.startswith("ic_tab_") or name.startswith("ic_help_topic_"):` branch.
- In the `elif name.startswith(("ic_plotcat_", "ic_law_head_", "ic_off_title", "ic_gc_now"))` branch change `layers=HEADER_LAYERS,` to `layers=(DWF_BARE_LAYERS if RACE == "dwf" and name == "ic_off_title" else HEADER_LAYERS),`.
- In the `elif name == "ic_influence":` branch change `layers=SEATS_LAYERS,` to `layers=(DWF_SEATS_LAYERS if RACE == "dwf" else SEATS_LAYERS),`.

3e. After `check_dwf_frame_ink`:

```python
# CHAOS DWARF ART STILL REACHABLE FROM A DWARF COURT - each one the author's to rule
# on at the preview (Task 15). Anything Chaos Dwarf outside these is a fault.
DWF_KEEPS = {
    # The Governors column, its rows and its list (the Hell-Forge's plates).
    "ui/skins/default/dlc23_chd_hell_forge/button_holder_back.png",
    "ui/skins/default/dlc23_chd_hell_forge/side_panel_title.png",
    "ui/skins/default/dlc23_chd_hell_forge/side_panerl_bg.png",
    "ui/skins/default/dlc23_chd_hell_forge/sub_title.png",
    # The tab marker's glow.
    "ui/skins/default/dlc23_chd_hell_forge/heat_glow.png",
    # The Governors toggle and its effects button.
    "ui/skins/default/dlc23_tower_of_zharr/icon_button_seat_effects.png",
    "ui/skins/default/dlc23_tower_of_zharr/tab_sub_title.png",
    # The trait, band and Conclave Influence icons.
    "ui/campaign ui/effect_bundles/chd_conclave_influence.png",
    "ui/campaign ui/effect_bundles/chd_toz_tier.png",
    # The narrative map pin.
    "ui/frontend ui/faction_bullets/bullet_chd_tower_of_zharr.png",
}
DWF_KEEP_PREFIXES = (
    "ui/skins/default/dlc23_chd_hell_forge/button_square_extra_large_",
    # The law cards' paintings: CA's Chaos Dwarf technology art.
    "ui/campaign ui/technologies/wh3_dlc23_tech_chd_",
)
CHD_ART = re.compile(r"chd|dlc23|hell_forge|hashut|zharr|ziggurat")


def chd_art(path):
    """True for Chaos Dwarf art a Dwarf court should not draw."""
    p = path.lower().replace("\\", "/")
    return bool(CHD_ART.search(p)) and p not in DWF_KEEPS and not p.startswith(DWF_KEEP_PREFIXES)


def check_race_art(text=None):
    """No Chaos Dwarf picture in the Dwarf panel file outside DWF_KEEPS. The pooled
    files are shared and are skinned at runtime; the preview checks what the shipped
    Lua actually draws (preview_iron_court.py --race dwf)."""
    text = build_xml()[PANEL_FILE] if text is None else text
    return ["the Dwarf panel draws Chaos Dwarf art %s" % p
            for p in sorted(set(re.findall(r'imagepath="([^"]+)"', text))) if chd_art(p)]
```

3f. In `check()`, extend the `if RACE == "dwf":` block of Task 4 (3e):

```python
        out.extend(check_race_art())
```

3g. In `make_ic_backdrop`'s view, the throne's three lines are text on the panel and `check()` there asks every TITLE-styled cell to be measured; Task 6 adds them to `text_cells`.

- [ ] **Step 4: Run it and see it pass.**

Run: `py tools\gen_ic_ui.py --selftest`
Expected: exit 0.

Run: `py tools\gen_ic_ui.py`
Expected: `wrote ...derpy_ic_panel_dwf.twui.xml` and its compact copy; no `FAIL` line other than check 3's `dwf_panel_bg.png` imagepath that resolves to nothing, which Task 6 writes. The existing 20k text checks now run in the Dwarf copies with a 36px ribbon inset; any tab caption they report is a real overflow - widen nothing, report it to the author.

Run: `py tools\preview_iron_court.py --check`
Expected: `N file(s) checked by TWUI Studio's reader`, no `PROBLEM:` (TWUI Studio's reader, which has never heard of this generator, links the Dwarf panel's GUIDs).

- [ ] **Step 5: Checkpoint.** Run THE GATES. Expected: all green except the backdrop line; `chd court unchanged`.

---

### Task 6: The Dwarf backdrop

**Files:**
- Modify: `tools/make_ic_backdrop.py`
- Writes (packed): `Modding Files/pack/ui/derpy_ic/dwf_panel_bg.png`

**Interfaces:**
- Produces: `make_ic_backdrop.py --race dwf` (and no `--race`: both races), `DIM_DWF`, `text_cells(G)` covering the throne's lines, `check(race)`, `contrast(img, G)` unchanged in shape. Phase 6's `grounds()` finds the Dwarf backdrop as the one other 1920x1080 picture in `art_paths()`.

- [ ] **Step 1: The failing check.** `check_dwf_art` (Task 4) skips the backdrop. Make it hold the backdrop too: in `tools/gen_ic_ui.py`, inside `check_dwf_art`, replace

```python
        if path == DWF_PANEL_BG:
            continue
```

with

```python
        if path == DWF_PANEL_BG:
            # NOT BAKED HERE: make_ic_backdrop.py cuts and dims it (it measures every
            # text cell against it). Here only that it is there and the panel's size.
            bg = os.path.join(ROOT, "Modding Files", "pack", *path.split("/"))
            if not os.path.isfile(bg):
                out.append("%s is not written: run py tools/make_ic_backdrop.py --race dwf" % path)
            elif Image.open(bg).size != (PANEL_W, PANEL_H):
                out.append("%s is %dx%d, not the panel's %dx%d"
                           % ((path,) + Image.open(bg).size + (PANEL_W, PANEL_H)))
            continue
```

- [ ] **Step 2: Run it and see it fail.**

Run: `py tools\gen_ic_ui.py --check`
Expected: `FAIL dwf at 1920: ui/derpy_ic/dwf_panel_bg.png is not written: run py tools/make_ic_backdrop.py --race dwf` (and the same at 1600 and 2560), exit 1.

- [ ] **Step 3: Implement.**

3a. In `tools/make_ic_backdrop.py`, after `MIN_RATIO = 4.5`:

```python
# THE DWARF GROUND (plan 2026-10-04 phase 3): CA's own Dwarf loading screen, 1920x1200,
# cover-cropped to the panel, dimmed to the largest hundredth at which every bare text
# cell clears 4.5:1 at 1600, 1920 and 2560. Measured: 0.27 passes, 0.28 does not
# (ic_row_crest[10] is the bound). check() asserts both halves.
DIM_DWF = 0.27
RACES = ("chd", "dwf")
```

Replace `_gen()` with:

```python
def _gen(race="chd"):
    spec = importlib.util.spec_from_file_location(
        "gen_ic_ui", os.path.join(ROOT, "tools", "gen_ic_ui.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("gen_ic_ui", mod)
    spec.loader.exec_module(mod)
    return mod if race == "chd" else mod.at_box(1920, race)


def dst(G):
    return os.path.join(ROOT, "Modding Files", "pack", *G.PANEL_BG.split("/"))
```

In `text_cells(G)`, append to the returned tuple:

```python
            + tuple(n for n in ("ic_throne_of", "ic_throne_name", "ic_throne_leader")
                    if n in G.PANEL_LAYOUT))
```

(the throne's lines are covered by its tier -1 plate, so `bare_boxes` drops them; listing them is what satisfies the "every heading is measured" guard for `ic_throne_name`).

3b. Add after `build()`:

```python
def build_dwf(dim=None):
    """CA's Dwarf loading screen, cover-cropped to the panel and dimmed."""
    from PIL import Image
    G = _gen("dwf")
    src = G._ca_png("ui.pack", G.DWF_BACKDROP_SRC)
    if src is None:
        raise SystemExit("no game install: %s cannot be read" % G.DWF_BACKDROP_SRC)
    if src.size != (1920, 1200):
        raise SystemExit("%s is %dx%d, not 1920x1200 - re-measure before trusting the crop"
                         % ((G.DWF_BACKDROP_SRC,) + src.size))
    w, h = G.PANEL_W, G.PANEL_H
    k = max(w / float(src.width), h / float(src.height))
    big = src.convert("RGB").resize((round(src.width * k), round(src.height * k)), Image.LANCZOS)
    x0, y0 = (big.width - w) // 2, (big.height - h) // 2
    out = big.crop((x0, y0, x0 + w, y0 + h))
    d = DIM_DWF if dim is None else dim
    return out.point(lambda v: int(v * d)).convert("RGBA")


def _fails(img, G):
    """Cells under 4.5:1 at 1920, and at 1600 and 2560 with the picture scaled."""
    from PIL import Image
    bad = [r for r in contrast(img, G) if r[3] < MIN_RATIO]
    for bw in (1600, 2560):
        g = G.at_box(bw)
        scaled = img.convert("RGB").resize((g.PANEL_W, g.PANEL_H), Image.LANCZOS)
        bad += [r for r in contrast(scaled, g) if r[3] < MIN_RATIO]
    return bad
```

3c. Change `contrast(img=None, G=None)` so its defaults are `G = G or _gen()` and `img = img or Image.open(dst(G)).convert("RGB")` (the image after G, since the path is G's). Change `def check():` to `def check(race="chd"):`, set `G = _gen(race)` at its top, read `dst(G)` wherever it read `DST`, and make its missing-file message `"the backdrop is not written: run py tools/make_ic_backdrop.py --race %s" % race`. Its `small = G.at_box(1600)` line already follows the copy's race. At its end, before `return out`, add:

```python
    if race == "dwf":
        try:
            up = build_dwf(round(DIM_DWF + 0.01, 2))
        except SystemExit:
            up = None
        if up is not None and not _fails(up, G):
            out.append("the Dwarf backdrop is dimmed to %.2f and %.2f would pass: dim it less"
                       % (DIM_DWF, DIM_DWF + 0.01))
```

3d. Replace the `if __name__ == "__main__":` block with:

```python
if __name__ == "__main__":
    races = ([sys.argv[sys.argv.index("--race") + 1]] if "--race" in sys.argv else list(RACES))
    if "--search" in sys.argv:
        G = _gen("dwf")
        for k in range(60, 15, -1):
            if not _fails(build_dwf(k / 100.0), G):
                print("largest passing Dwarf dim: %.2f" % (k / 100.0))
                break
        sys.exit(0)
    problems = []
    for race in races:
        G = _gen(race)
        if "--check" not in sys.argv:
            img = build() if race == "chd" else build_dwf()
            os.makedirs(os.path.dirname(dst(G)), exist_ok=True)
            img.save(dst(G), optimize=True)
            print("wrote %s  %dx%d  %.2f MB  (dimmed to %.0f%%)"
                  % (dst(G), img.width, img.height, os.path.getsize(dst(G)) / 1048576.0,
                     (DIM if race == "chd" else DIM_DWF) * 100))
        if os.path.isfile(dst(G)):
            measured = contrast(None, G)
            print("  %s: %d cells measured, worst ten:" % (race, len(measured)))
            for name, mean, p95, ratio in measured[-10:]:
                print("  %-18s mean %5.1f  p95 %5.1f  %4.1f:1" % (name, mean, p95, ratio))
        problems += ["%s: %s" % (race, p) for p in check(race)]
    for p in problems:
        print("PROBLEM: " + p)
    sys.exit(1 if problems else 0)
```

(The Chaos Dwarf `build()` and its output are unchanged; `DST` stays as the Chaos Dwarf path for anything else that imports it.)

- [ ] **Step 4: Run it and see it pass.**

Run: `py tools\make_ic_backdrop.py --race dwf --search`
Expected: `largest passing Dwarf dim: 0.27`. A different value: set `DIM_DWF` to it and say so in the handoff.

Run: `py tools\make_ic_backdrop.py --race dwf`
Expected: `wrote ...ui\derpy_ic\dwf_panel_bg.png  1920x1080 ...  (dimmed to 27%)`, the worst ten at or above 4.5:1, no `PROBLEM:`.

Run: `py tools\make_ic_backdrop.py --check`
Expected: both races measured, no `PROBLEM:`; the Chaos Dwarf worst ten identical to before this task.

Run: `py tools\gen_ic_ui.py --check`
Expected: `ok: N files, M components`, no `FAIL`.

- [ ] **Step 5: Checkpoint.** Run THE GATES. Expected: all green; `chd court unchanged`.

---

### Task 7: The Lua race layout and the runtime skin

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_dwarf.lua` (the dwf race table's `art = {}`)
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua` (after `ICUI.PATH_OPENER` ~line 40; `ICUI.TAB_PLATE` / `ICUI.light_tabs` ~2628; `law_light` ~4619 and its two callers; `draw_help`'s topic loop ~6449; `ICUI.refresh`'s tab captions ~7636; `ICUI.open` ~7994; `place_opener` ~1849; after `ICUI.apply_scale` ~9010)
- Test: `tools/_iron_court_harness.lua` (`build_fake_panel`, `with_fake_root`, `with_fake_govmap`; new checks before the `IC_DUMP` block)

**Interfaces:**
- Produces (Lua, added to the contract): `R.art` for dwf = `{suffix, tab, frame, lit_ink, title_cap, heading_cap, opener_icon}`; `ICUI.race()` (contract, if phase 1 did not add it); `ICUI.ART`, `ICUI.SUFFIX`; `ICUI.RACE_XY` (`dwf` = the seven cells of Task 3); `ICUI.CHD_BASE`; `ICUI.grid_xy(grid)`; `ICUI.use_race(r)`; `ICUI.CARD_FRAME_INDEX = 1`; `ICUI.SKIN_POOLS`; `ICUI.skin(panel)` (contract); `ICUI.TAB_WORD`; `ICUI.tab_art(c, lit, index)`; `ICUI.lit_word(word, lit)`; `ICUI.light_plate(c, lit, word)`; `ICUI.OPENER_ICON_SLOTS = {2, 5}`; `ICUI.skin_opener(button)`. Harness: `build_fake_panel(race)`, `with_fake_root(fn, break, screen, race)`, `with_fake_govmap(fn, screen, race)`, `DW` (`DW.KK`, `DW.court(leader)`, `DW.chd_again()`, `DW.check(name, fn)`).
- `ICUI.BASE.CARD_XY` is set from the race before `ICUI.apply_scale` (contract).

- [ ] **Step 1: The failing checks.** In `tools/_iron_court_harness.lua`:

1a. `build_fake_panel`: change `local function build_fake_panel()` to `local function build_fake_panel(race)` and directly after `for name in pairs(ICUI.PANEL_XY) do child(panel, name) end` add:

```lua
    -- A RACE'S OWN CELLS (plan 2026-10-04 phase 3), which the real panel file of that
    -- race declares and the Chaos Dwarf one does not.
    for name in pairs((race and ICUI.RACE_XY and ICUI.RACE_XY[race]) or {}) do
        if not panel.children[name] then child(panel, name) end
    end
```

1b. `with_fake_root`: change its signature to `local function with_fake_root(fn, break_creation, screen, race)`, its first `build_fake_panel()` call to `build_fake_panel(race)`, and `if _path == ICUI.PATH_PANEL .. "_compact" then` to `if string.find(_path, "_compact$") then` (the Dwarf compact file is `derpy_ic_panel_dwf_compact`).

1c. `with_fake_govmap`: change its signature to `local function with_fake_govmap(fn, screen, race)` and pass `race` as the fourth argument of the `with_fake_root(...)` call that closes it (its last line reads `end, nil, screen)`; make it `end, nil, screen, race)`).

1d. Directly before the comment block `-- THE PREVIEW'S DEMO (plan 2026-10-02 laws, Task 10)`:

```lua
-- THE DWARF COURT ON THE FAKE ROOT (plan 2026-10-04 phase 3). Karak Kadrin, Ungrim
-- Ironfist on the throne. Every check here goes back to the Chaos Dwarf layout at
-- 1920 whether it passes or not: ICUI.open of a Dwarf court rewrote ICUI.BASE and the
-- scaled tables in place, and every later check expects the Chaos Dwarf ones.
-- ONE LOCAL, a table: the main chunk is past 140 locals and Lua stops at 200.
local DW = {KK = "wh_main_dwf_karak_kadrin"}
function DW.court(leader)
    IC.state = {}
    IC._race_cache = {}
    turn = IC.TUNE.grace_turns + 5
    local king = make_character(9900, ANY_SEAT, IC.CROWN, nil)
    king._forename, king._surname = "derpy_test_dwf_fore", "derpy_test_dwf_sur"
    IC_TEST_LOC.derpy_test_dwf_fore, IC_TEST_LOC.derpy_test_dwf_sur = "Ungrim", "Ironfist"
    IC_TEST_LOC["factions_screen_name_" .. DW.KK] = "Karak Kadrin"
    local f = make_faction(DW.KK, "wh_main_sc_dwf_dwarfs", {king}, {})
    if leader then f._leader = king end
    cm.get_human_factions = function() return {DW.KK} end
    for _, slug in ipairs(IC.R(DW.KK).PARTIES) do IC.add_house(DW.KK, slug) end
    return IC.court(DW.KK)
end
function DW.chd_again()
    ICUI.use_race(IC.RACES.chd)
    ICUI.apply_scale(1920)
    ICUI.pick = nil
    cm.get_human_factions = function() return {F} end
    IC._race_cache = {}
end
function DW.check(name, fn)
    check(name, function()
        local ok, err = pcall(fn)
        DW.chd_again()
        if not ok then error(err, 0) end
    end)
end

DW.check("a Dwarf court opens the Dwarf panel file, its seats on the hall grid", function()
    DW.court(true)
    with_fake_root(function(hud, panel, extra)
        ICUI.open()
        assert(extra.paths[ICUI.PANEL] == ICUI.PATH_PANEL .. "_dwf",
            "built from " .. tostring(extra.paths[ICUI.PANEL]))
        -- THE SPEC'S PICTURE, not grid_xy's arithmetic again: Tier I's first seat is
        -- cell (1, 0) and the throne is cell (2, 0).
        local c1 = panel.children[ICUI.CARD .. "_1"]
        assert(c1.x == 398 and c1.y == 192, "seat 1 at " .. c1.x .. "," .. c1.y)
        local t = panel.children.ic_throne
        assert(t.x == 778 and t.y == 192, "the throne at " .. t.x .. "," .. t.y)
        local grid = ICUI.grid_xy(IC.R(DW.KK).grid)
        for i = 1, #grid do
            local c = panel.children[ICUI.CARD .. "_" .. i]
            assert(c.x == grid[i][1] and c.y == grid[i][2], "seat " .. i .. " is off its cell")
        end
        assert(ICUI.TITLE_CAP == 150 and ICUI.HEADING_CAP == 80, "the Dwarf caps are not in force")
        assert(ICUI.PANEL_XY.ic_title[3] == 1100, "the Dwarf title cell is not in force")
        ICUI.close(true)
    end, nil, {1920, 1080}, "dwf")
end)

DW.check("a Dwarf court's pooled cards wear the knot frame baked to their size", function()
    DW.court(true)
    with_fake_root(function(hud, panel)
        ICUI.open()
        for _, p in ipairs({{ICUI.CARD, "364x184"}, {ICUI.PARTY, "455x266"},
                            {ICUI.PLOT, "364x176"}, {ICUI.LAW, "306x150"}}) do
            local c = panel.children[p[1] .. "_1"]
            local got = c and c.images and c.images[ICUI.CARD_FRAME_INDEX]
            assert(got == "ui/derpy_ic/dwf_frame_" .. p[2] .. ".png",
                p[1] .. " wears " .. tostring(got))
        end
        ICUI.close(true)
    end, nil, {1920, 1080}, "dwf")
end)

DW.check("a Dwarf court at 1600x900 opens the Dwarf compact file, frames named by their 1920 size", function()
    DW.court(true)
    with_fake_root(function(hud, panel, extra)
        ICUI.open()
        assert(extra.paths[ICUI.PANEL] == ICUI.PATH_PANEL .. "_dwf_compact",
            "built from " .. tostring(extra.paths[ICUI.PANEL]))
        local c1 = panel.children[ICUI.CARD .. "_1"]
        assert(c1.x == ICUI.sc(398) and c1.y == ICUI.sc(192), "seat 1 at " .. c1.x .. "," .. c1.y)
        assert(c1.images[ICUI.CARD_FRAME_INDEX] == "ui/derpy_ic/dwf_frame_364x184.png",
            "the compact card asked for " .. tostring(c1.images[ICUI.CARD_FRAME_INDEX]))
        ICUI.close(true)
    end, nil, {1600, 900}, "dwf")
end)

DW.check("a Chaos Dwarf court opened after a Dwarf court is the Chaos Dwarf court", function()
    DW.court(true)
    with_fake_root(function() ICUI.open() ICUI.close(true) end, nil, {1920, 1080}, "dwf")
    gov_court({crown = 10, legion = 10})
    with_fake_root(function(hud, panel, extra)
        ICUI.open()
        assert(extra.paths[ICUI.PANEL] == ICUI.PATH_PANEL, "built from " .. tostring(extra.paths[ICUI.PANEL]))
        assert(ICUI.PANEL_XY.ic_throne == nil and ICUI.BASE.PANEL_XY.ic_throne == nil,
            "the throne's cell outlived the Dwarf court")
        assert(ICUI.PANEL_XY.ic_title[3] == 600, "the title cell is " .. ICUI.PANEL_XY.ic_title[3])
        assert(ICUI.TITLE_CAP == 111 and ICUI.HEADING_CAP == 34, "the Dwarf caps outlived it")
        for i, xy in ipairs(ICUI.CHD_BASE.CARD_XY) do
            assert(ICUI.CARD_XY[i][1] == xy[1] and ICUI.CARD_XY[i][2] == xy[2],
                "card " .. i .. " is still on the hall grid")
        end
        local card = panel.children[ICUI.CARD .. "_1"]
        assert(not (card.images and card.images[ICUI.CARD_FRAME_INDEX]), "a Chaos Dwarf card was re-skinned")
        local tab = panel.children.ic_tab_court
        assert(tab.images[0] == ICUI.TAB_PLATE[0].on or tab.images[0] == ICUI.TAB_PLATE[0].off,
            "the Chaos Dwarf tab wears " .. tostring(tab.images[0]))
        ICUI.close(true)
    end, nil, {1920, 1080})
    gov_done()
end)

DW.check("a Dwarf court's lit tab wears the gold ribbon in dark ink, the others the blue", function()
    DW.court(true)
    with_fake_root(function(hud, panel)
        ICUI.open()
        ICUI.view = "offices"
        ICUI.refresh()
        local lit, off = panel.children.ic_tab_offices, panel.children.ic_tab_court
        assert(lit.images[0] == "ui/derpy_ic/dwf_tab_selected_240x32.png"
               and lit.images[1] == "ui/derpy_ic/dwf_tab_selected_240x32.png",
            "the lit tab wears " .. tostring(lit.images[0]) .. " / " .. tostring(lit.images[1]))
        assert(lit.text == "[[col:black]]Offices[[/col]]", "the lit tab reads " .. lit.text)
        assert(off.images[0] == "ui/derpy_ic/dwf_tab_active_240x32.png"
               and off.images[1] == "ui/derpy_ic/dwf_tab_hover_240x32.png",
            "an unlit tab wears " .. tostring(off.images[0]) .. " / " .. tostring(off.images[1]))
        assert(off.text == "Court", "an unlit tab reads " .. off.text)
        ICUI.close(true)
    end, nil, {1920, 1080}, "dwf")
end)

DW.check("a Dwarf court's opener shows the Book of Grudges, a Chaos Dwarf court's the Hashut glyph", function()
    DW.court(true)
    local b = fake_component("opener")
    ICUI.skin_opener(b)
    local imgs = b.images or {}
    assert(imgs[2] == "ui/skins/default/icon_book_grudges.png"
           and imgs[5] == "ui/skins/default/icon_book_grudges.png",
        "the Dwarf opener wears " .. tostring(imgs[2]) .. " / " .. tostring(imgs[5]))
    DW.chd_again()
    local c = fake_component("opener")
    ICUI.skin_opener(c)
    assert(not (c.images and next(c.images)), "the Chaos Dwarf opener was re-skinned")
end)
```

- [ ] **Step 2: Run them and see them fail.**

Run: `$env:IC_ONLY = "Dwarf court"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: the first check fails with `attempt to call field 'use_race' (a nil value)` (from `chd_again`) or `built from ui/campaign ui/derpy_ic_panel`; `6 failing`.

- [ ] **Step 3: Implement.**

3a. `zzz_derpy_iron_court_dwarf.lua`: in the dwf race table replace `art = {},` with:

```lua
    -- THE DWARF SKIN (plan 2026-10-04 phase 3). The panel is its own file pair (the
    -- caps are twui margins); the pooled cards' frame, the lit plates and the opener
    -- glyph are swapped at runtime. Must match gen_ic_ui.py: DWF_TAB, DWF_FRAME,
    -- DWF["title_cap"], DWF["heading_cap"], DWF_OPENER_ICON (import_iron_court checks).
    art = {
        suffix = "_dwf",
        tab = "ui/derpy_ic/dwf_tab_%s_%dx%d.png",
        frame = "ui/derpy_ic/dwf_frame_%dx%d.png",
        lit_ink = "black",
        title_cap = 150,
        heading_cap = 80,
        opener_icon = "ui/skins/default/icon_book_grudges.png",
    },
```

3b. `zzz_derpy_iron_court_ui.lua`, directly after `ICUI.PATH_OPENER = "ui/campaign ui/derpy_ic_opener"`:

```lua
-- THE RACE'S SKIN (plan 2026-10-04 phase 3), set by ICUI.use_race at open. The
-- Chaos Dwarf court's is empty: the twui as shipped.
ICUI.ART = {}
ICUI.SUFFIX = ""

-- A RACE'S OWN PANEL CELLS at 1920. Must match gen_ic_ui.py's Dwarf layout (DWF,
-- DWF_CELLS); import_iron_court.py compares them. The closer stays in column 0.
ICUI.RACE_XY = {
    dwf = {
        ic_title = {18, 4, 1100, 56},
        ic_help = {1126, 8, 48, 48},
        ic_off_title = {703, 120, 514, 44},
        ic_throne = {778, 192, 364, 184},
        ic_throne_of = {794, 288, 332, 18},
        ic_throne_name = {794, 306, 332, 26},
        ic_throne_leader = {794, 334, 332, 22},
    },
}
```

3c. If `function ICUI.race(` is not in the file (Task 1's probe said so), add directly after `function ICUI.player()`'s `end`:

```lua
-- THE PLAYER'S RACE TABLE (contract): IC.R of this machine's faction; the Chaos
-- Dwarfs' when no player is known yet, as court_player() allows.
function ICUI.race()
    local me = ICUI.player()
    if not me then return IC.RACES.chd end
    return IC.R(me)
end
```

3d. Replace `function ICUI.light_tabs(panel)` and its body with:

```lua
-- THE TAB CAPTIONS, in one table: a lit Dwarf tab's word is inked dark on the gold
-- ribbon, so whatever lights the plate writes the word with it.
ICUI.TAB_WORD = {
    ic_tab_court = "Court", ic_tab_offices = "Offices", ic_tab_govs = "Governors",
    ic_tab_intrigue = "Intrigue", ic_tab_log = "Record", ic_tab_petitions = "Petitions",
    ic_tab_laws = "Laws",
}

-- THE PLATE A TAB-SHAPED BUTTON WEARS in slot `index` (0 standard, 1 hover). The
-- Chaos Dwarf court's is ICUI.TAB_PLATE; a race with art.tab has a ribbon baked to
-- each cell's 1920 size, named by that size (gen_ic_ui.py DWF_TAB).
function ICUI.tab_art(c, lit, index)
    local art = ICUI.ART or {}
    if not art.tab then
        local plate = ICUI.TAB_PLATE[index]
        return lit and plate.on or plate.off
    end
    local ok, id = pcall(function() return c:Id() end)
    local xy = ok and ICUI.BASE.PANEL_XY[id]
    if not xy then return nil end
    local state = "active"
    if lit then state = "selected" elseif index == 1 then state = "hover" end
    return string.format(art.tab, state, xy[3], xy[4])
end

-- THE WORD ON A LIT PLATE: dark ink where the race's lit plate is too bright for
-- cream (the gold ribbon, check_dwf_contrast). [[col:black]] is db/ui_colours_tables'
-- black, 000000.
function ICUI.lit_word(word, lit)
    local ink = (ICUI.ART or {}).lit_ink
    if lit and ink then return "[[col:" .. ink .. "]]" .. word .. "[[/col]]" end
    return word
end

-- LIGHT ONE TAB-SHAPED BUTTON: both image slots, and its word when given.
function ICUI.light_plate(c, lit, word)
    if not c then return end
    for index = 0, 1 do
        local path = ICUI.tab_art(c, lit, index)
        if path then pcall(function() c:SetImagePath(path, index) end) end
    end
    if word then set_text(c, ICUI.lit_word(word, lit)) end
end

function ICUI.light_tabs(panel)
    for name, view in pairs(ICUI.TAB_VIEW) do
        ICUI.light_plate(comp(name, panel), view == ICUI.view, ICUI.TAB_WORD[name])
    end
end
```

3e. In `ICUI.refresh`, delete the seven lines from `set_text(comp("ic_tab_court", panel), "Court")` to `set_text(comp("ic_tab_laws", panel), "Laws")` (the comment block above them about title case stays, and now sits over `ICUI.light_tabs(panel)`, which writes the captions).

3f. Replace `local function law_light(c, lit)` and its body with:

```lua
local function law_light(c, lit, text)
    ICUI.light_plate(c, lit, text)
end
```

and its two callers: replace

```lua
        set_text(b, ICUI.LAW_STANCE_BTN[i])
        law_light(b, vote.stance == ICUI.LAW_STANCES[i])
```

with `        law_light(b, vote.stance == ICUI.LAW_STANCES[i], ICUI.LAW_STANCE_BTN[i])`, and

```lua
        set_text(b, label)
        law_light(b, l <= cur)
```

with `        law_light(b, l <= cur, label)`.

3g. In `ICUI.draw_help`'s topic loop replace

```lua
            set_text(c, topic and (ICUI.help_fill("{@" .. tostring(topic.icon) .. "}", {}) .. topic.title) or "")
            show(c, topic ~= nil)
            -- LIT LIKE A TAB, with the tab's own two plates.
            for index = 0, 1 do
                local art = ICUI.TAB_PLATE[index]
                pcall(function() c:SetImagePath(i == page and art.on or art.off, index) end)
            end
```

with

```lua
            show(c, topic ~= nil)
            -- LIT LIKE A TAB, with the tab's own two plates and ink.
            ICUI.light_plate(c, i == page, topic and (ICUI.help_fill("{@" .. tostring(topic.icon)
                .. "}", {}) .. topic.title) or "")
```

3h. Directly after `function ICUI.apply_scale(bw)`'s closing `end`:

```lua
-- THE CHAOS DWARF 1920 VALUES a race may override, taken once at load from BASE.
ICUI.CHD_BASE = {CARD_XY = copy_table(ICUI.BASE.CARD_XY), PANEL_XY = {},
                 TITLE_CAP = ICUI.TITLE_CAP, HEADING_CAP = ICUI.HEADING_CAP}
for _, cells in pairs(ICUI.RACE_XY) do
    for k in pairs(cells) do
        if ICUI.BASE.PANEL_XY[k] then
            ICUI.CHD_BASE.PANEL_XY[k] = copy_table(ICUI.BASE.PANEL_XY[k])
        end
    end
end

-- A GRID RACE'S CARDS (spec 2.5): one per office in IC.OFFICES order, at the cell
-- the race table names, at 1920. Must match gen_ic_ui.card_grid; the packing gate
-- runs this function and compares.
function ICUI.grid_xy(grid)
    local B = ICUI.BASE
    local band = grid.cols * B.CARD_W + (grid.cols - 1) * B.CARD_GAP_X
    local x0 = B.CARDS_X + math.floor((B.CONTENT_W - band) / 2)
    local out = {}
    for i, cr in ipairs(grid.cells) do
        out[i] = {x0 + cr[1] * (B.CARD_W + B.CARD_GAP_X),
                  B.CARDS_Y + cr[2] * (B.CARD_H + B.CARD_GAP_Y)}
    end
    return out
end

-- THE RACE INTO THE BASE, before apply_scale (contract). Every value it can change
-- is written for every race, the Chaos Dwarf one from CHD_BASE, so a court opened
-- after another race's is its own. A race-only cell is removed from the live table
-- too: apply_scale only writes the keys BASE holds and would leave it standing.
function ICUI.use_race(r)
    local B, C = ICUI.BASE, ICUI.CHD_BASE
    local mine = ICUI.RACE_XY[r.key] or {}
    for _, cells in pairs(ICUI.RACE_XY) do
        for k in pairs(cells) do
            local want = mine[k] or C.PANEL_XY[k]
            if want then
                B.PANEL_XY[k] = copy_table(want)
            else
                B.PANEL_XY[k] = nil
                ICUI.PANEL_XY[k] = nil
            end
        end
    end
    if r.layout == "grid" and r.grid then
        B.CARD_XY = ICUI.grid_xy(r.grid)
    else
        B.CARD_XY = copy_table(C.CARD_XY)
    end
    ICUI.ART = r.art or {}
    ICUI.SUFFIX = ICUI.ART.suffix or ""
    ICUI.TITLE_CAP = ICUI.ART.title_cap or C.TITLE_CAP
    ICUI.HEADING_CAP = ICUI.ART.heading_cap or C.HEADING_CAP
end

-- THE POOLED CARDS' FRAME: CARD_LAYERS[1] in gen_ic_ui.py, the 9-sliced frame over
-- the tiled body, in the card, party, move and law files alike.
ICUI.CARD_FRAME_INDEX = 1
ICUI.SKIN_POOLS = {
    {"CARD", "CARD_XY", "CARD_W", "CARD_H"},
    {"PARTY", "PARTY_XY", "PARTY_W", "PARTY_H"},
    {"PLOT", "PLOT_XY", "PLOT_W", "PLOT_H"},
    {"LAW", "LAW_XY", "LAW_W", "LAW_H"},
}

-- THE RACE'S ART ON WHAT ITS PANEL FILE CANNOT CARRY (contract): the pooled files
-- are shared by every race, so their frame is re-pointed after CreateComponent, at
-- each pool's 1920 size - the size it was baked at, and the geometry the twui's
-- margin was set for. A race with no art.frame is left exactly as created.
function ICUI.skin(panel)
    local frame = (ICUI.ART or {}).frame
    if not (panel and frame) then return end
    for _, p in ipairs(ICUI.SKIN_POOLS) do
        local path = string.format(frame, ICUI.BASE[p[3]], ICUI.BASE[p[4]])
        for i = 1, #ICUI[p[2]] do
            local c = comp(ICUI[p[1]] .. "_" .. i, panel)
            if c then pcall(function() c:SetImagePath(path, ICUI.CARD_FRAME_INDEX) end) end
        end
    end
end

-- THE OPENER'S GLYPH: slots 2 and 5 of derpy_ic_opener.twui.xml (standard and hover).
ICUI.OPENER_ICON_SLOTS = {2, 5}
function ICUI.skin_opener(button)
    local icon = (ICUI.race().art or {}).opener_icon
    if not (button and icon) then return end
    for _, i in ipairs(ICUI.OPENER_ICON_SLOTS) do
        pcall(function() button:SetImagePath(icon, i) end)
    end
end
```

3i. `ICUI.path`: replace its body with

```lua
function ICUI.path(p)
    local base = p
    if p == ICUI.PATH_PANEL then p = p .. (ICUI.SUFFIX or "") end
    if ICUI.COMPACT and ICUI.HAS_COMPACT[base] then return p .. "_compact" end
    return p
end
```

3j. In `ICUI.open`, directly above `local scaled, why = pcall(ICUI.apply_scale, bw)` (keep that line byte for byte: `mutate_iron_court.py` anchors on it):

```lua
        -- THE RACE BEFORE THE SCALE (plan 2026-10-04 phase 3): use_race writes the
        -- race's 1920 cells and grid into ICUI.BASE, which apply_scale then scales,
        -- and picks the panel file ICUI.path names below.
        ICUI.use_race(ICUI.race())
```

and directly above `ICUI.layout()` (after the `for i = 1, ICUI.MAX_ROWS do` creation loop):

```lua
        ICUI.skin(panel)
```

3k. In `ICUI.place_opener`, directly after the line `button = comp(ICUI.BTN)` that follows the opener's `CreateComponent`, add `ICUI.skin_opener(button)`.

- [ ] **Step 4: Run them and see them pass.**

Run: `$env:IC_ONLY = "Dwarf court"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: `iron court harness: ok (6 checks)`.

Run: `& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua`
Expected: `iron court harness: ok (N checks)`, N = the count before this task plus 6. Every existing tab, law-button and help-topic check still passes (the Chaos Dwarf `ICUI.ART` has no `tab`, so `tab_art` returns `ICUI.TAB_PLATE`'s paths and `lit_word` the bare word).

- [ ] **Step 5: Checkpoint.** Run THE GATES. Expected: all green; `chd court unchanged`.

---

### Task 8: The Dwarf words and the throne

**Files:**
- Modify: `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua` (`ICUI.RACE_WORDS` after `ICUI.RACE_XY`; `ICUI.faction_words`, `ICUI.race_words`, `ICUI.offices_title`, `ICUI.THRONE_KEYS`, `ICUI.draw_throne` after `ICUI.draw_offices`; `draw_offices` lines 5250-5251; `ICUI.refresh`'s title; the dispatcher's `show(comp("ic_off_title", panel), ...)`)
- Modify: `tools/gen_ic_ui.py` (`CUT_CELLS` in the Dwarf text block of Task 5; `DWF_PLAYABLE`, `_race_words`, `check_dwf_text` after `check_race_art`; `check()`'s Dwarf block; `selftest`)
- Test: `tools/_iron_court_harness.lua` (after Task 7's checks)

**Interfaces:**
- Produces (Lua, added to the contract): `ICUI.RACE_WORDS` (`dwf = {title, hall, throne_of, no_leader}`), `ICUI.race_words()`, `ICUI.faction_words(faction_key)`, `ICUI.offices_title()`, `ICUI.THRONE_KEYS`, `ICUI.draw_throne(panel, faction_key)`.
- Produces (Python): `DWF_PLAYABLE` (the six playable keys and kings, spec section 3), `_race_words()`, `check_dwf_text(words=None)`; `ic_throne_name` and `ic_throne_leader` in `CUT_CELLS` (check 20h then requires the Lua to cut them).
- The calls, each read with `py tools\check_lua_api.py --explain <member>`:
  - `common.get_localised_string(key)` - "Retrieves a localised string from the database by its full localisation key. This is in the form [table]_[field]_[record_key]. If the lookup fails, an empty string is returned." Reached through the panel's existing `loc(key, fallback)`, which returns the fallback on that empty string: `loc("factions_screen_name_" .. faction_key, faction_key)`, as the panel already names a faction in six places.
  - `faction:faction_leader()` - "The character that leads the faction. Return: CHARACTER_SCRIPT_INTERFACE (or NULL_SCRIPT_INTERFACE if the faction has no faction leader)". Tested with `is_null_interface()`, under `pcall`.
  - `character:get_forename()` / `get_surname()` - "Returns the character forename / surname. Return: string". Resolved through the existing `ICUI.character_name(character)`, the one every portrait row in the panel already uses.

- [ ] **Step 1: The failing checks.** After Task 7's checks:

```lua
DW.check("a Dwarf court's title, hall and throne name its faction and its king", function()
    DW.court(true)
    with_fake_root(function(hud, panel)
        ICUI.open()
        ICUI.view = "offices"
        ICUI.refresh()
        local ch = panel.children
        assert(ch.ic_title.text == "The Council of Karak Kadrin", "title: " .. ch.ic_title.text)
        assert(ch.ic_off_title.text == "THE GREAT HALL", "hall: " .. ch.ic_off_title.text)
        assert(ch.ic_throne_of.text == "THE THRONE OF", "prefix: " .. ch.ic_throne_of.text)
        assert(ch.ic_throne_name.text == "Karak Kadrin", "throne: " .. ch.ic_throne_name.text)
        assert(ch.ic_throne_leader.text == "Ungrim Ironfist", "king: " .. ch.ic_throne_leader.text)
        assert(ch.ic_zig_bg.visible, "the hall is hidden on the offices tab")
        for _, k in ipairs(ICUI.THRONE_KEYS) do
            assert(ch[k].visible, k .. " is hidden on the offices tab")
        end
        ICUI.view = "court"
        ICUI.refresh()
        for _, k in ipairs(ICUI.THRONE_KEYS) do
            assert(not ch[k].visible, k .. " shows on the court tab")
        end
        ICUI.close(true)
    end, nil, {1920, 1080}, "dwf")
end)

DW.check("a Dwarf court with no king says the throne stands empty", function()
    DW.court(false)
    with_fake_root(function(hud, panel)
        ICUI.open()
        ICUI.view = "offices"
        ICUI.refresh()
        assert(panel.children.ic_throne_leader.text == "The throne stands empty",
            "king: " .. panel.children.ic_throne_leader.text)
        ICUI.close(true)
    end, nil, {1920, 1080}, "dwf")
end)

DW.check("a Chaos Dwarf court after a Dwarf court keeps its own words", function()
    DW.court(true)
    with_fake_root(function() ICUI.open() ICUI.close(true) end, nil, {1920, 1080}, "dwf")
    gov_court({crown = 10, legion = 10})
    with_fake_root(function(hud, panel)
        ICUI.open()
        ICUI.view = "offices"
        ICUI.refresh()
        assert(panel.children.ic_off_title.text == ICUI.OFFICES_TITLE,
            "the ziggurat reads " .. panel.children.ic_off_title.text)
        assert(not string.find(panel.children.ic_title.text, "Council", 1, true),
            "the Chaos Dwarf title reads " .. panel.children.ic_title.text)
        ICUI.close(true)
    end, nil, {1920, 1080})
    gov_done()
end)
```

And in `tools/gen_ic_ui.py`, above `def selftest():`, with a call to it in `selftest()` after `selftest_dwf_panel()`:

```python
def selftest_dwf_text():
    """THE DWARF WORDS FIT (plan 2026-10-04 phase 3, Task 8)."""
    d = _dwf()
    words = d._race_words()
    assert set(words) >= {"title", "hall", "throne_of", "no_leader"}, words
    assert not d.check_dwf_text(), d.check_dwf_text()
    long_prefix = dict(words, throne_of="THE ANCIENT AND UNBROKEN THRONE OF")
    assert any("ic_throne_of" in p for p in d.check_dwf_text(long_prefix)), \
        "a prefix too long for its line passed"
```

- [ ] **Step 2: Run them and see them fail.**

Run: `$env:IC_ONLY = "Dwarf court"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: `title: Hashut's Court` (or the race-aware title phase 1 left) on the first new check; `2 failing` or `3 failing`, 6 passing.

Run: `py tools\gen_ic_ui.py --selftest`
Expected: `AttributeError: module 'gen_ic_ui_at_1920_dwf' has no attribute '_race_words'`.

Run, and read each entry before writing the code: `py tools\check_lua_api.py --explain get_localised_string; py tools\check_lua_api.py --explain faction_leader; py tools\check_lua_api.py --explain get_forename`
Expected: the three entries quoted in this task's Interfaces.

- [ ] **Step 3: Implement.**

3a. Directly after `ICUI.RACE_XY = { ... }` (Task 7, 3b):

```lua
-- A RACE'S OWN WORDS (plan 2026-10-04 phase 3; spec 2.6). The faction's name is
-- read at runtime. gen_ic_ui.check_dwf_text measures every one against its cell.
ICUI.RACE_WORDS = {
    dwf = {
        title = "The Council of %s",
        hall = "THE GREAT HALL",
        throne_of = "THE THRONE OF",
        no_leader = "The throne stands empty",
    },
}
```

3b. Directly after `ICUI.draw_offices`'s closing `end`:

```lua
function ICUI.race_words()
    return ICUI.RACE_WORDS[ICUI.race().key] or {}
end

-- THE FACTION'S NAME AS CA WRITES IT: factions_screen_name_<key>, through loc(),
-- which answers the key itself if CA has no row (get_localised_string gives "").
function ICUI.faction_words(faction_key)
    return loc("factions_screen_name_" .. tostring(faction_key), tostring(faction_key))
end

function ICUI.offices_title()
    return ICUI.race_words().hall or ICUI.OFFICES_TITLE
end

-- THE THRONE (spec 2.5): the plate and its three lines, offices tab only.
ICUI.THRONE_KEYS = {"ic_throne", "ic_throne_of", "ic_throne_name", "ic_throne_leader"}
function ICUI.draw_throne(panel, faction_key)
    local words = ICUI.race_words()
    if not words.throne_of then return end
    set_text(comp("ic_throne_of", panel), words.throne_of)
    ICUI.fit_cut(comp("ic_throne_name", panel), ICUI.faction_words(faction_key))
    local king = words.no_leader
    local ok, leader = pcall(function() return cm:get_faction(faction_key):faction_leader() end)
    if ok and leader and not leader:is_null_interface() then
        king = ICUI.character_name(leader)
    end
    ICUI.fit_cut(comp("ic_throne_leader", panel), king)
end
```

3c. In `ICUI.draw_offices`, replace its first two lines

```lua
    set_text(comp("ic_off_title", panel), ICUI.OFFICES_TITLE)
    ICUI.fit_plate(comp("ic_off_title", panel), "ic_off_title", ICUI.OFFICES_TITLE, ICUI.HEADING_CAP, false)
```

with

```lua
    local hall = ICUI.offices_title()
    set_text(comp("ic_off_title", panel), hall)
    ICUI.fit_plate(comp("ic_off_title", panel), "ic_off_title", hall, ICUI.HEADING_CAP, false)
    ICUI.draw_throne(panel, faction)
```

(`ICUI.OFFICES_TITLE = "THE ZIGGURAT OF ZHARR"` stays as it is: `gen_ic_ui.py` and the preview read it by that exact line.)

3d. In `ICUI.refresh`, replace `local title = loc("derpy_ic_title", "Hashut's Court")` with:

```lua
    local words = ICUI.race_words()
    local title = words.title and string.format(words.title, ICUI.faction_words(faction))
                  or loc("derpy_ic_title", "Hashut's Court")
```

(If phase 1 already changed this line, keep its Chaos Dwarf expression as the `or` branch.)

3e. In the dispatcher, directly after `show(comp("ic_off_title", panel), view == "offices")`:

```lua
    -- AND THE THRONE, with the hall: a Dwarf court's only; the Chaos Dwarf panel
    -- declares none of the four, so comp() finds nothing there.
    for _, key in ipairs(ICUI.THRONE_KEYS) do
        local c = comp(key, panel)
        if c then show(c, view == "offices") end
    end
```

3f. `tools/gen_ic_ui.py`: in the Dwarf text block after `TEXT_STYLE` (Task 5, 3c), add under the three `TEXT_STYLE` lines:

```python
    # The name and the king are cut by ICUI.fit_cut, as a long party leader's line is.
    CUT_CELLS["ic_throne_name"] = "ICUI.fit_cut"
    CUT_CELLS["ic_throne_leader"] = "ICUI.fit_cut"
```

After `check_race_art`:

```python
# THE SIX PLAYABLE DWARF FACTIONS AND THEIR KINGS (spec section 3), keys verified
# against CA's loc (factions_screen_name_*). The throne's lines must fit them uncut.
DWF_PLAYABLE = {"wh_main_dwf_dwarfs": "Thorgrim Grudgebearer",
                "wh_main_dwf_karak_kadrin": "Ungrim Ironfist",
                "wh_main_dwf_karak_izor": "Belegar Ironhammer",
                "wh3_main_dwf_the_ancestral_throng": "Grombrindal",
                "wh2_dlc17_dwf_thorek_ironbrow": "Thorek Ironbrow",
                "wh3_dlc25_dwf_malakai": "Malakai Makaisson"}


def _race_words():
    """ICUI.RACE_WORDS.dwf out of the panel Lua: the words are the Lua's, measured here."""
    ui = io.open(os.path.join(ROOT, "Modding Files", "pack", "script", "campaign", "mod",
                              "zzz_derpy_iron_court_ui.lua"), encoding="utf-8").read()
    blk = _lua_block(ui, "ICUI.RACE_WORDS = {")
    dwf = _lua_block(blk, "dwf = {") if blk else None
    return dict(re.findall(r'(\w+)\s*=\s*"([^"]*)"', dwf)) if dwf else {}


def check_dwf_text(words=None):
    """EVERY DWARF STRING FITS ITS CELL at this copy's fonts and boxes: the title for
    every Dwarf faction CA names, the throne's name and king for the six playable
    ones, the empty throne's line, the hall's heading and the throne's prefix."""
    out = []
    words = _race_words() if words is None else words
    for key in ("title", "hall", "throne_of", "no_leader"):
        if key not in words:
            out.append("ICUI.RACE_WORDS.dwf has no %s, so nothing measures it" % key)
    if out:
        return out
    try:
        import read_vanilla_loc as L
        names = L.load("factions")
    except Exception as exc:
        return ["cannot read CA's faction names to measure the Dwarf title: %r" % (exc,)]
    every = sorted(set(v for k, v in names.items() if k.startswith("factions_screen_name_")
                       and "_dwf_" in k and "rebels" not in k))
    for key in DWF_PLAYABLE:
        if not names.get("factions_screen_name_" + key):
            out.append("CA's loc has no screen name for %s" % key)

    def room(cell, cap=None):
        w = PANEL_LAYOUT[cell][2]
        return w - (cap + PLATE_GAP) * 2 if cap is not None else w

    def fits(cell, s, cap=None):
        px = TEXT_STYLE.get(cell, BODY)[0]
        if measure_text(s, px) > room(cell, cap):
            out.append("%s: %r is %dpx at %dpx, the cell has %d"
                       % (cell, s, measure_text(s, px), px, room(cell, cap)))
    for name in every:
        fits("ic_title", words["title"] % name, TITLE_CAP)
    for key, king in sorted(DWF_PLAYABLE.items()):
        fits("ic_throne_name", names.get("factions_screen_name_" + key, key))
        fits("ic_throne_leader", king)
    fits("ic_throne_leader", words["no_leader"])
    fits("ic_throne_of", words["throne_of"])
    fits("ic_off_title", words["hall"], HEADING_CAP)
    return out
```

and in `check()`'s `if RACE == "dwf":` block add `out.extend(check_dwf_text())`. Add `"DWF_PLAYABLE",` to `NOT_GEOMETRY` if `_classify` asks (it holds strings only, so it should not).

- [ ] **Step 4: Run them and see them pass.**

Run: `$env:IC_ONLY = "Dwarf court"; & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua; Remove-Item Env:IC_ONLY`
Expected: `iron court harness: ok (9 checks)`.

Run: `py tools\gen_ic_ui.py --selftest; py tools\gen_ic_ui.py --check`
Expected: the selftest exits 0; `--check` ends `ok: ...` - check 20h now finds `ICUI.fit_cut(comp("ic_throne_name"` and `ICUI.fit_cut(comp("ic_throne_leader"` in the Lua, and `check_dwf_text` measures every Dwarf faction's title at 1600, 1920 and 2560. A title or throne line it reports at one size is a real overflow: tell the author, with the string and the numbers; never drop a font below CA's sizes.

- [ ] **Step 5: Checkpoint.** Run THE GATES. Expected: all green; `chd court unchanged`.

---

### Task 9: The packing gate learns the Dwarf panel

**Files:**
- Modify: `tools/import_iron_court.py` (a new `run_lua_grid_xy()` beside `run_lua_card_grid()` ~line 103; new checks in gate 9 after Task 2's `check_race_files` line; the 9b index loop)
- Modify: `tools/gen_ic_ui.py` (`CARD_FRAME_INDEX = 1` after `CARD_LAYERS`; `NOT_GEOMETRY`)

**Interfaces:**
- Produces: `gen_ic_ui.CARD_FRAME_INDEX`; `import_iron_court.run_lua_grid_xy()`; gate 9c (the Dwarf cells, grid, art fields, opener slots and every runtime path against `art_paths()`).

- [ ] **Step 1: The failing check.** In `tools/import_iron_court.py`, gate 9's index loop: change `for name in ("PLATE_INDEX", "FACE_INDEX", "MASK_INDEX"):` to `for name in ("PLATE_INDEX", "FACE_INDEX", "MASK_INDEX", "CARD_FRAME_INDEX"):`.

- [ ] **Step 2: Run it and see it fail.**

Run: `py tools\import_iron_court.py`
Expected: a problem line naming `CARD_FRAME_INDEX` (`AttributeError: module 'gen_ic_ui' has no attribute 'CARD_FRAME_INDEX'` inside the gate's catch: `the panel layout cross-check could not run` or the gate 9 equivalent).

- [ ] **Step 3: Implement.**

3a. `tools/gen_ic_ui.py`, directly after the closing `]` of `CARD_LAYERS = [`:

```python
# THE FRAME'S LAYER in every file built on CARD_LAYERS: ICUI.skin re-points it for a
# race whose art has a frame. import_iron_court.py holds the Lua's number to this.
CARD_FRAME_INDEX = 1
assert "frame" in CARD_LAYERS[CARD_FRAME_INDEX]["path"]
```

and add `"CARD_FRAME_INDEX",` to `NOT_GEOMETRY`.

3b. `tools/import_iron_court.py`, directly after `run_lua_card_grid()`:

```python
def run_lua_grid_xy():
    """ICUI.grid_xy cut out of the panel and run under lua.exe on the Dwarf race
    table's own grid, so the comparison is against what the panel builds."""
    if not os.path.isfile(LUA_EXE):
        return None
    import gen_ic_ui as U
    ui = io.open(UI_LUA, encoding="utf-8").read()
    m = re.search(r"^function ICUI\.grid_xy\(grid\)\n(.*?)^end\n", ui, re.S | re.M)
    if not m:
        return "ICUI.grid_xy is not in the panel"
    consts = re.findall(r"^ICUI\.(CARDS?_\w+|CONTENT_W)\s*=\s*(-?\d+)$", ui, re.M)
    cols, _rows, _throne, cells = U.race_grid("dwf")
    src = ["ICUI = {BASE = {}}"] + ["ICUI.BASE.%s = %s" % (k, v) for k, v in consts]
    src += ["function ICUI.grid_xy(grid)", m.group(1), "end",
            "local g = ICUI.grid_xy({cols = %d, cells = {%s}})"
            % (cols, ", ".join("{%d, %d}" % c for c in cells)),
            'for i = 1, #g do print(g[i][1] .. "," .. g[i][2]) end']
    path = os.path.join(tempfile.gettempdir(), "ic_grid_xy.lua")
    io.open(path, "w", encoding="utf-8", newline="\n").write("\n".join(src))
    try:
        proc = subprocess.run([LUA_EXE, path], capture_output=True, text=True)
    finally:
        os.remove(path)
    if proc.returncode != 0:
        return "ICUI.grid_xy failed under lua.exe: " + proc.stderr.strip()
    return [tuple(int(v) for v in line.split(",")) for line in proc.stdout.split()]
```

3c. In gate 9, directly after `problems += U2.check_race_files()`:

```python
        # 9c. THE DWARF PANEL (plan 2026-10-04 phase 3). The Lua's copy of every number
        #     the Dwarf court shares with the generator, and every picture the Lua can
        #     name at runtime, because a SetImagePath to a path nothing ships draws a
        #     blank square and says nothing.
        D = U2._dwf()
        blk = U2._lua_block(ui, "ICUI.RACE_XY = {")
        dblk = U2._lua_block(blk or "", "dwf = {")
        lua_cells = dict((n, tuple(int(v) for v in vals)) for n, *vals in re.findall(
            r"(\w+) = \{(\d+), (\d+), (\d+), (\d+)\}", dblk or ""))
        for n in D.DWF_CELLS:
            if lua_cells.get(n) != tuple(D.PANEL_LAYOUT_1920[n]):
                problems.append("ICUI.RACE_XY.dwf.%s is %s and gen_ic_ui says %s"
                                % (n, lua_cells.get(n), D.PANEL_LAYOUT_1920[n]))
        for n in sorted(set(lua_cells) - set(D.DWF_CELLS)):
            problems.append("ICUI.RACE_XY.dwf.%s is no Dwarf cell of gen_ic_ui" % n)
        got = run_lua_grid_xy()
        if isinstance(got, str):
            problems.append(got)
        elif got is not None and got != [tuple(p) for p in D.CARD_GRID]:
            problems.append("ICUI.grid_xy builds %s and gen_ic_ui.card_grid('dwf') %s"
                            % (got, D.CARD_GRID))
        dsrc = io.open(U2.DWARF_LUA, encoding="utf-8").read()
        art = dict(re.findall(r'(\w+)\s*=\s*"?([^",\n]+)"?,',
                              U2._lua_block(dsrc, "art = {") or ""))
        for key, want in (("suffix", D.PANEL_SUFFIX), ("tab", D.DWF_TAB),
                          ("frame", D.DWF_FRAME), ("lit_ink", "black"),
                          ("title_cap", str(D.TITLE_CAP)), ("heading_cap", str(D.HEADING_CAP)),
                          ("opener_icon", D.DWF_OPENER_ICON)):
            if art.get(key) != want:
                problems.append("the dwf race's art.%s is %r and gen_ic_ui says %r"
                                % (key, art.get(key), want))
        path_panel = re.search(r'ICUI\.PATH_PANEL\s*=\s*"([^"]+)"', ui).group(1)
        if path_panel + art.get("suffix", "") != "ui/campaign ui/" + D.PANEL_FILE[:-len(".twui.xml")]:
            problems.append("PATH_PANEL plus the dwf suffix does not name %s" % D.PANEL_FILE)
        shipped = U2.art_paths()
        for w, h in D.dwf_tab_sizes():
            for st in D.DWF_TAB_STATES:
                if (art.get("tab", "") % (st, w, h)) not in shipped:
                    problems.append("the Lua can draw %s and nothing ships it"
                                    % (art.get("tab", "") % (st, w, h)))
        for w, h in D.POOL_1920.values():
            if (art.get("frame", "") % (w, h)) not in shipped:
                problems.append("ICUI.skin can draw %s and nothing ships it"
                                % (art.get("frame", "") % (w, h)))
        opener = io.open(os.path.join(os.path.dirname(UI_FILES[0]), "derpy_ic_opener.twui.xml"),
                         encoding="utf-8").read()
        oblk = re.search(r"<componentimages>(.*?)</componentimages>", opener, re.S)
        slots = [i for i, p in enumerate(re.findall(r'imagepath="([^"]+)"', oblk.group(1) if oblk else ""))
                 if "icon_wh_main_lore_hashut" in p]
        lua_slots = [int(v) for v in re.findall(r"\d+", re.search(
            r"ICUI\.OPENER_ICON_SLOTS\s*=\s*\{([^}]*)\}", ui).group(1))]
        if slots != lua_slots:
            problems.append("the opener's glyph is in slots %s and ICUI.OPENER_ICON_SLOTS says %s"
                            % (slots, lua_slots))
```

(`UI_FILES` entries are `"Modding Files/pack/ui/campaign ui/" + name`, relative to the workspace root every tool here runs from; the opener file is one of them.)

- [ ] **Step 4: Run it and see it pass.**

Run: `py tools\import_iron_court.py`
Expected: no problem line. Then prove 9c can fail: in `zzz_derpy_iron_court_ui.lua` change `ic_throne_name = {794, 306, 332, 26},` to `ic_throne_name = {795, 306, 332, 26},` with the Edit tool, run `py tools\import_iron_court.py`, see `ICUI.RACE_XY.dwf.ic_throne_name is (795, 306, 332, 26) and gen_ic_ui says (794, 306, 332, 26)`, and put the 794 back with the Edit tool.

- [ ] **Step 5: Checkpoint.** Run THE GATES. Expected: all green; `chd court unchanged`.

---

### Task 10: The harness dumps a Dwarf court for the preview

**Files:**
- Modify: `tools/_iron_court_harness.lua` (a new block directly after the `IC_DUMP` block, before the `no parties' turn failed` check)

**Interfaces:**
- Produces: with `IC_DUMP_RACE=dwf`, `IC_DUMP_RACE_OUT=<file>` and `IC_DUMP_LOC=<lua file>`, the harness writes one TSV line per component per screen: `screen  path  visible  x  y  w  h  text  images  file  resized` (11 columns; `screen` is `<view>@<box width>`; `file` is the path the component was created from, empty for a child; `resized` is 1 when the Lua sized it). Views: `court`, `intrigue`, `pick`, `pick_ready`, `offices`, `petitions`, `gm_provinces`, `gm_picker`, `law_board`, `law_vote`, `gov_cards`, `log`, `help`, at boxes 1920, 1600 and 2560. Loc keys it reads: `factions_screen_name_wh_main_dwf_karak_kadrin`, `derpy_demo_dwf_fore`, `derpy_demo_dwf_sur`, `derpy_demo_dwf_face_king`, `derpy_demo_fore_<i>`, `derpy_demo_dwf_face_<i>` (1-6).
- Consumed by: Task 11 (`preview_iron_court.race_dump`).

- [ ] **Step 1: The failing check.** The dump is driven from the preview, so its check is the preview's: add to `tools/preview_iron_court.py`, directly after `law_dump`:

```python
DumpNode = collections.namedtuple(
    "DumpNode", "path name visible x y w h text images file resized")
DWF_VIEWS = ("log", "help")          # drawn for the Dwarf court only (Review Focus 7)
DWF_DEMO_FACES = [
    "ui/portraits/portholes/no_culture/dwf_lord_campaign_01_0.png",
    "ui/portraits/portholes/no_culture/dwf_ch_runelord_campaign_01_0.png",
    "ui/portraits/portholes/no_culture/dwf_master_engineer_campaign_01_0.png",
    "ui/portraits/portholes/no_culture/dwf_runesmith_campaign_01_0.png",
    "ui/portraits/portholes/no_culture/dwf_lord_campaign_02_0.png",
    "ui/portraits/portholes/no_culture/dwf_ch_runelord_campaign_02_0.png",
]
DWF_DEMO_KING_FACE = "ui/portraits/portholes/no_culture/dwf_ch_ungrim_0.png"
DWF_DEMO_FORE = ["Kazador", "Hargrim", "Thorgard", "Durgnar", "Bronnir", "Grimbok",
                 "Ulfgrim", "Snorvald", "Morgrim", "Hakkin"]


def race_dump(race, _cache={}):
    """{"view@bw": [DumpNode, ...]} - a race's court drawn by the SHIPPED Lua: the
    harness's IC_DUMP_RACE block opens it through the real ICUI.open on the fake root
    at each box and walks every view. The text is the Lua's; its cuts measure with
    the harness's linear stub, so the picture lets a long string overflow."""
    if race in _cache:
        return _cache[race]
    import subprocess
    import tempfile
    import gen_iron_court as GIC
    import read_vanilla_loc as L
    loc = dict((r["key"], r["text"]) for r in GIC.build()["loc"])
    names = L.load("factions")
    loc["factions_screen_name_wh_main_dwf_karak_kadrin"] = names[
        "factions_screen_name_wh_main_dwf_karak_kadrin"]
    loc["derpy_demo_dwf_fore"], loc["derpy_demo_dwf_sur"] = "Ungrim", "Ironfist"
    loc["derpy_demo_dwf_face_king"] = DWF_DEMO_KING_FACE
    for i, fore in enumerate(DWF_DEMO_FORE):
        loc["derpy_demo_fore_%d" % (i + 1)] = fore
    for i, face in enumerate(DWF_DEMO_FACES):
        loc["derpy_demo_dwf_face_%d" % (i + 1)] = face

    def q(v):
        return '"%s"' % v.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    tmp = tempfile.mkdtemp(prefix="ic_race_dump_")
    loc_path, out_path = os.path.join(tmp, "loc.lua"), os.path.join(tmp, "dump.tsv")
    with io.open(loc_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("return {\n" + "".join("[%s] = %s,\n" % (q(k), q(v))
                                       for k, v in sorted(loc.items())) + "}\n")
    env = dict(os.environ, IC_ONLY="no check is named this", IC_DUMP_RACE=race,
               IC_DUMP_RACE_OUT=out_path, IC_DUMP_LOC=loc_path)
    env.pop("IC_TEST_ALL", None)
    env.pop("IC_DUMP", None)
    r = subprocess.run([LUA_EXE, os.path.join("tools", "_iron_court_harness.lua")],
                       cwd=ROOT, env=env, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.isfile(out_path):
        raise SystemExit("the harness's %s dump failed:\n%s%s" % (race, r.stdout, r.stderr))

    def unesc(t):
        return re.sub(r"\\(.)", lambda m: {"t": "\t", "n": "\n"}.get(m.group(1), m.group(1)), t)
    out = {}
    for line in io.open(out_path, encoding="utf-8").read().split("\n"):
        if not line:
            continue
        screen, path, vis, x, y, w, h, text, imgs, fname, resized = line.split("\t")
        images = {}
        for pair in unesc(imgs).split("|"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                images[int(k)] = v.replace("\\", "/")
        out.setdefault(screen, []).append(DumpNode(
            path, path.rsplit("/", 1)[-1], vis == "1", float(x), float(y), float(w),
            float(h), unesc(text), images, unesc(fname), resized == "1"))
    _cache[race] = out
    return out
```

and in `selftest()`, at its end:

```python
    # THE DWARF COURT'S DUMP (plan 2026-10-04 phase 3, Task 10).
    D = race_dump("dwf")
    for bw in SIZES:
        for v in VIEWS + DWF_VIEWS:
            key = "%s@%d" % (v, bw)
            assert key in D, "the harness dumped no %s" % key
            want = "derpy_ic_panel_dwf" + ("_compact" if bw < 1920 else "")
            assert D[key][0].file.endswith(want), "%s was built from %s" % (key, D[key][0].file)
    off = dict((n.name, n) for n in D["offices@1920"])
    assert off["ic_off_title"].text == "THE GREAT HALL", off["ic_off_title"].text
    assert off["ic_throne_name"].text == "Karak Kadrin", off["ic_throne_name"].text
    assert off["ic_throne_leader"].text == "Ungrim Ironfist", off["ic_throne_leader"].text
    assert off["derpy_ic_card_1"].images.get(1) == "ui/derpy_ic/dwf_frame_364x184.png"
    assert off["ic_tab_offices"].text == "[[col:black]]Offices[[/col]]"
```

- [ ] **Step 2: Run it and see it fail.**

Run: `py tools\preview_iron_court.py --selftest`
Expected: `SystemExit: the harness's dwf dump failed:` followed by `iron court harness: ok (...)` - the harness ran its checks (none, under `IC_ONLY`) and wrote no dump file.

- [ ] **Step 3: Implement.** In `tools/_iron_court_harness.lua`, directly after the `IC_DUMP` block's final `end` (the one after `gov_done()`):

```lua
-- THE DWARF COURT'S DUMP (plan 2026-10-04 phase 3, Task 10): with IC_DUMP_RACE=dwf,
-- open Karak Kadrin's court through the REAL ICUI.open on the fake root at each box
-- and walk every view, writing every component with the file it was created from,
-- so preview_iron_court.py --race dwf draws only what the shipped Lua did. Not a
-- check: it adds nothing to the count.
if os.getenv("IC_DUMP_RACE") == "dwf" then
    IC_TEST_LOC = dofile(os.getenv("IC_DUMP_LOC"))
    IC_TEST_PORTRAITS = {}
    local KK_DUMP = "wh_main_dwf_karak_kadrin"
    local out = assert(io.open(os.getenv("IC_DUMP_RACE_OUT"), "w"))
    local function esc(s)
        return (string.gsub(tostring(s or ""), "[\t\n\\]",
            {["\t"] = "\\t", ["\n"] = "\\n", ["\\"] = "\\\\"}))
    end
    local function longest_roll(R, slug)
        local best, bh, bt = "", 1, 1
        for h, head in ipairs(R.NAME_HEADS) do
            for t, tail in ipairs(R.NAME_TAILS[slug] or {}) do
                local s = head .. " of " .. tail
                if #s > #best then best, bh, bt = s, h, t end
            end
        end
        return bh, bt
    end
    -- THE HARD CASE: every party, each wearing its longest name; a king; two governors.
    IC.state = {}
    IC._race_cache = {}
    IC_GOVS_ON = true
    turn = IC.TUNE.grace_turns + 5
    local king = make_character(9900, ANY_SEAT, IC.CROWN, nil)
    king._forename, king._surname = "derpy_demo_dwf_fore", "derpy_demo_dwf_sur"
    IC_TEST_PORTRAITS["9900"] = IC_TEST_LOC.derpy_demo_dwf_face_king
    local chars = {king}
    local f = make_faction(KK_DUMP, "wh_main_sc_dwf_dwarfs", chars,
                           {"prov_a", "prov_b", "prov_c", "prov_d"})
    f._leader = king
    cm.get_human_factions = function() return {KK_DUMP} end
    local R = IC.R(KK_DUMP)
    assert(R.key == "dwf", "Karak Kadrin is not a Dwarf court: " .. tostring(R.key))
    local court = IC.court(KK_DUMP)
    for i, slug in ipairs(R.PARTIES) do
        IC.add_house(KK_DUMP, slug)
        if slug ~= IC.CROWN then
            court.houses[slug].head, court.houses[slug].tail = longest_roll(R, slug)
        end
        local c = make_character(9900 + i, ANY_SEAT, slug, nil)
        c._forename = "derpy_demo_fore_" .. i
        c._faction = f
        chars[#chars + 1] = c
        IC_TEST_PORTRAITS[tostring(9900 + i)] = IC_TEST_LOC["derpy_demo_dwf_face_" .. ((i - 1) % 6 + 1)]
        court.standing[9900 + i] = 420 - i * 30
    end
    court.govs.prov_a, court.govs.prov_b = 9901, 9902
    IC.log(KK_DUMP, "appoint", R.PARTIES[2], R.OFFICES[1].slug, 0)
    IC.log(KK_DUMP, "warn", R.PARTIES[3], nil, 3)
    local cat = R.LAW_ORDER[1]
    court.laws = {}
    for _, k in ipairs(R.LAW_ORDER) do court.laws[k] = R.LAWS[k].order[1] end
    court.votes = {[cat] = {option = R.LAWS[cat].order[5], proposer = R.PARTIES[2],
                            ends = turn + IC.TUNE.law_vote_turns, stance = "aye",
                            won = {}, push = {}}}
    local VIEWS = {
        {"court", function() ICUI.view = "court" end},
        {"intrigue", function() ICUI.view = "intrigue" end},
        {"pick", function() ICUI.view = "offices"; ICUI.sort.pick = 1
            ICUI.pick = {kind = "office", key = R.OFFICES[1].slug} end},
        {"pick_ready", function() ICUI.view = "offices"; ICUI.sort.pick = 2
            ICUI.pick = {kind = "office", key = R.OFFICES[1].slug} end},
        {"offices", function() ICUI.view = "offices" end},
        {"petitions", function() ICUI.view = "petitions" end},
        {"gm_provinces", function() ICUI.view = "govs"; ICUI.gm_page = "provinces" end},
        {"gm_picker", function() ICUI.view = "govs"; ICUI.gm_page = "provinces"
            ICUI.pick = {kind = "gov", key = "prov_a"} end},
        {"law_board", function() ICUI.view = "laws"; ICUI.law_cat = nil
            ICUI.law_sel = {cat, R.LAWS[cat].order[2]} end},
        {"law_vote", function() ICUI.view = "laws"; ICUI.law_cat = cat end},
        {"gov_cards", function() ICUI.view = "court"; ICUI.pick = {kind = "doctrine"} end},
        {"log", function() ICUI.view = "log" end},
        {"help", function() ICUI.view = "help"; ICUI.help_page = 1 end},
    }
    for _, screen in ipairs({{1920, 1080}, {1600, 900}, {2560, 1440}}) do
        with_fake_govmap(function(hud, panel, extra)
            local function walk(name, c, path)
                local imgs = {}
                for i, p in pairs(c.images or {}) do imgs[#imgs + 1] = i .. "=" .. tostring(p) end
                table.sort(imgs)
                out:write(table.concat({name, path, c.visible and "1" or "0", c.x, c.y, c.w, c.h,
                    esc(c.text), esc(table.concat(imgs, "|")), esc(extra.paths[c.name] or ""),
                    c.resized and "1" or "0"}, "\t"), "\n")
                for _, k in ipairs(c.order) do walk(name, k, path .. "/" .. k.name) end
            end
            ICUI.open()
            for _, v in ipairs(VIEWS) do
                ICUI.pick, ICUI.law_cat = nil, nil
                v[2]()
                ICUI.refresh()
                walk(v[1] .. "@" .. screen[1], panel, panel.name)
            end
            ICUI.pick = nil
            ICUI.close(true)
        end, screen, "dwf")
    end
    out:close()
    ICUI.use_race(IC.RACES.chd)
    ICUI.apply_scale(1920)
    cm.get_human_factions = function() return {F} end
    gov_done()
end
```

- [ ] **Step 4: Run it and see it pass.**

Run: `py tools\preview_iron_court.py --selftest`
Expected: exit 0, no traceback (the dump has all 39 screens, the Dwarf words, the skinned frame and the dark-inked lit tab).

Run: `& "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua`
Expected: `iron court harness: ok (N checks)`, the same N as after Task 8 (the dump only runs with `IC_DUMP_RACE` set).

- [ ] **Step 5: Checkpoint.** Run THE GATES. Expected: all green; `chd court unchanged`.

---

### Task 11: `preview_iron_court.py --race dwf` draws the Dwarf court

**Files:**
- Modify: `tools/preview_iron_court.py` (`_gen_at`; `raced`; `VIEW_OUT`; `INK_OF` and `text()`'s fill; `render()`'s signature, its generator and doc loading, its art extraction, and the dump branch after the `text` closure; `selftest`; the `__main__` block)

**Interfaces:**
- Produces: `render(path=None, view="court", box_w=1920, race="chd")` (phases 4 and 5 consume `race` in the Chaos Dwarf branch), `_gen_at(bw, race="chd")`, `raced(path, race)`, `VIEW_OUT`, `INK_OF`, `--race chd|dwf` (no flag: both races). Pictures: the Chaos Dwarf ones keep their names (`ic_court.png`, `ic_court_1600.png`, ...); the Dwarf ones are `ic_<view>_dwf.png`, `ic_<view>_dwf_1600.png`, `ic_<view>_dwf_2560.png` in `.skilltree_cache/ui_preview/` for the 11 shared views plus `log` and `help`.

- [ ] **Step 1: The failing check.** At the end of `selftest()`, after Task 10's block:

```python
    # THE DWARF PICTURES (plan 2026-10-04 phase 3, Task 11).
    assert INK_OF["black"] == (0, 0, 0, 255)
    assert segments("[[col:black]]Offices[[/col]]") == [("text", "Offices", "black")]
    assert raced(OUT_OFFICES, "dwf").endswith("ic_offices_dwf.png")
    assert sized(raced(OUT_OFFICES, "dwf"), 1600).endswith("ic_offices_dwf_1600.png")
    out, _n, problems, drawn = render(view="offices", box_w=1920, race="dwf")
    assert not problems, problems
    assert drawn > 100, "the Dwarf offices picture drew %d components" % drawn
    if _rows:
        assert by_key.get("black") == "000000", "db/ui_colours_tables has no black 000000"
```

(`_rows` and `by_key` are the `ui_colours` reads already in `selftest()`; this block goes after them.)

- [ ] **Step 2: Run it and see it fail.**

Run: `py tools\preview_iron_court.py --selftest`
Expected: `NameError: name 'INK_OF' is not defined`.

- [ ] **Step 3: Implement.**

3a. After `RED_INK = (0xFF, 0x2D, 0x2D, 255)`:

```python
# THE NAMED INKS the panel writes through [[col:]]: CA's red for a refusal, and black
# for a lit Dwarf tab's word on the gold ribbon (db/ui_colours_tables, 000000).
INK_OF = {"red": RED_INK, "black": (0, 0, 0, 255)}
```

and in the `text` closure inside `render`, change `fill=(RED_INK if tint == "red" else colour)` to `fill=INK_OF.get(tint, colour)`.

3b. Replace `_gen_at` with:

```python
def _gen_at(bw, race="chd", _cache={}):
    """The generator as the panel is at a box bw wide, for a race. Cached: at_box
    re-executes the whole generator, and a picture drawn from one copy with the
    numbers of another describes neither."""
    if bw == 1920 and race == "chd":
        return _gen()
    if (bw, race) not in _cache:
        _cache[(bw, race)] = _gen().at_box(bw, race)
    return _cache[(bw, race)]


def raced(path, race):
    """ic_court.png for the Chaos Dwarfs (every existing reference), ic_court_dwf.png
    for the Dwarfs."""
    if race == "chd":
        return path
    stem, ext = os.path.splitext(path)
    return "%s_%s%s" % (stem, race, ext)


VIEW_OUT = {"court": OUT, "intrigue": OUT_INTRIGUE, "pick": OUT_PICK,
            "pick_ready": OUT_PICK_READY, "offices": OUT_OFFICES,
            "petitions": OUT_PETITIONS, "gm_provinces": OUT_GM, "gm_picker": OUT_GM_PICK,
            "law_board": OUT_LAW_BOARD, "law_vote": OUT_LAW_VOTE, "gov_cards": OUT_GOV_CARDS,
            "log": os.path.join(PG.CACHE, "ic_log.png"),
            "help": os.path.join(PG.CACHE, "ic_help.png")}
```

3c. In `render`: change the signature to `def render(path=None, view="court", box_w=1920, race="chd"):` and `G = _gen_at(box_w)` to `G = _gen_at(box_w, race)`. In the `PG.extract_art(...)` call's `extra=` list, append `+ (sorted(set(p for nodes in race_dump(race).values() for nd in nodes for p in nd.images.values() if p.startswith("ui/"))) if race != "chd" else [])`. Change `panel, party = doc_of("derpy_ic_panel.twui.xml"), ...` to `panel, party = doc_of(G.PANEL_FILE), ...` (the Dwarf copy's `COMPACT_FILES` maps its panel to its compact copy).

3d. In `render`, directly after the `text` closure ends and before the comment line `# ---- the panel, then the tab's own furniture`:

```python
    # ---- A RACE OTHER THAN THE CHAOS DWARFS IS DRAWN FROM THE DUMP -----------
    #
    # Every visible component the shipped Lua left on the fake tree, at its MoveTo
    # position, with the pictures and words it set, painted with its own file's
    # layers - and nothing typed here. Siblings in engine order: a file's components
    # in declaration order, the pools after them in creation order.
    if race != "chd":
        nodes = race_dump(race)["%s@%d" % (view, box_w)]
        by_path = dict((nd.path, (i, nd)) for i, nd in enumerate(nodes))
        kids = collections.defaultdict(list)
        for nd in nodes:
            if "/" in nd.path:
                kids[nd.path.rsplit("/", 1)[0]].append(nd)
        docs = {}

        def creation_doc(nd):
            p = nd.path
            while True:
                f = by_path[p][1].file
                if f:
                    name = os.path.basename(f) + ".twui.xml"
                    if name not in docs:
                        docs[name] = model.Document(io.open(
                            os.path.join(PG.OURS, name), encoding="utf-8").read())
                    return docs[name]
                if "/" not in p:
                    return None
                p = p.rsplit("/", 1)[0]

        def comp_of(nd):
            doc = creation_doc(nd)
            for c in (doc.components if doc else []):
                if c.get("id", c.tag) == nd.name:
                    return doc, c
            return doc, None
        pools = ("derpy_ic_card_", "derpy_ic_party_", "derpy_ic_plot_", "derpy_ic_law_",
                 "derpy_ic_lawblock_", "derpy_ic_row_")

        def order(parent, nd):
            doc, _c = comp_of(parent)
            declared = [c.get("id", c.tag) for c in (doc.components if doc else [])]
            if nd.name in declared:
                return (0, declared.index(nd.name), 0)
            for k, pre in enumerate(pools):
                if nd.name.startswith(pre) and nd.name[len(pre):].isdigit():
                    return (1, k, int(nd.name[len(pre):]))
            return (2, by_path[nd.path][0], 0)
        unknown, seen_art, drawn = [], set(), [0]

        def draw_node(nd):
            if not nd.visible:
                return
            doc, c = comp_of(nd)
            if c is None:
                unknown.append(nd.path)
            else:
                st = doc.state(c)
                # THE LUA'S SIZE where it sized the component; the file's otherwise
                # (the fake tree's 10x10 default is nobody's size).
                w = nd.w if nd.resized else model.number(st.get("width"), 0) if st is not None else 0
                h = nd.h if nd.resized else model.number(st.get("height"), 0) if st is not None else 0
                w, h, x = int(round(w)), int(round(h)), nd.x
                plain = "".join(b for k, b, _t in segments(nd.text) if k == "text")
                if nd.name in G.FIT_PLATES and plain and nd.name in G.PANEL_LAYOUT:
                    x, w = G.fit_plate(nd.name, G.PANEL_LAYOUT[nd.name][0],
                                       G.PANEL_LAYOUT[nd.name][2], measure(doc, c, plain))
                paste(doc, c, x, nd.y, w, h, repaint=nd.images or None)
                if nd.text:
                    text(doc, c, nd.text, x, nd.y, w, h)
                seen_art.update(nd.images.values())
                drawn[0] += 1
            for k in sorted(kids[nd.path], key=lambda k: order(nd, k)):
                draw_node(k)
        draw_node(nodes[0])
        out = sized(raced(path or VIEW_OUT[view], race), box_w)
        canvas.save(out)
        problems = ["%s@%d: %s is in no twui file it was created from" % (view, box_w, p)
                    for p in unknown]
        problems += ["%s@%d: draws Chaos Dwarf art %s, not in gen_ic_ui.DWF_KEEPS"
                     % (view, box_w, p) for p in sorted(seen_art) if p and G.chd_art(p)]
        return out, n_art, missing + problems, drawn[0]
```

3e. Replace the `else:` branch of the `__main__` block with:

```python
    else:
        problems = validate()
        for p in problems:
            print("PROBLEM: " + p)
        races = ([sys.argv[sys.argv.index("--race") + 1]] if "--race" in sys.argv
                 else ["chd", "dwf"])
        for race in races:
            views = VIEWS + (DWF_VIEWS if race != "chd" else ())
            for bw in SIZES:
                for view in views:
                    out, n_art, missing, drawn = render(view=view, box_w=bw, race=race)
                    for m in missing:
                        if m.startswith(view + "@"):
                            print("PROBLEM: " + m)
                            problems.append(m)
                        else:
                            print("  art not found in any ui pack: " + m)
                    print("wrote %s  (%d art files, %d %s)"
                          % (out, n_art, drawn,
                             "components" if race != "chd" else
                             "of %d card slots filled" % len(_gen_at(bw).PARTY_GRID)
                             if view == "court" else "rows"))
        sys.exit(1 if problems else 0)
```

- [ ] **Step 4: Run it and see it pass.**

Run: `py tools\preview_iron_court.py --selftest`
Expected: exit 0.

Run: `py tools\preview_iron_court.py --race chd`
Expected: 33 `wrote` lines, no `PROBLEM:`.

Run: `py "Modding Files\source\iron_court_preview\phase3_probe.py" --verify --previews`
Expected: `chd court unchanged: N files` - every Chaos Dwarf picture byte-identical to Task 1's.

Run: `py tools\preview_iron_court.py --race dwf`
Expected: 39 `wrote ...ic_<view>_dwf*.png` lines; `PROBLEM:` lines only of the form `draws Chaos Dwarf art ...` for art the author has not ruled on (those are Task 15's list; there must be none for `chd_title`, `chd_heading`, `chd_tab_*`, `chd_frame`, `offices_ziggurat` or `panel_bg`).

- [ ] **Step 5: Checkpoint.** Run THE GATES. Expected: all green; `chd court unchanged`.

---

### Task 12: The Offices tab and its picker, approved

**Files:**
- Create: `Modding Files/source/iron_court_preview/phase3_approvals.py` (not packed, not synced)
- Create (by it): `Modding Files/source/iron_court_preview/phase3_approved/` (the approved pictures and `approvals.json`)

**Interfaces:**
- Produces: `phase3_approvals.py --verify GROUP`, `--record GROUP "<the author's words>"`, `--verify-all`. Groups: `offices` (offices, pick, pick_ready), `court` (court, log, petitions, help), `intrigue_laws` (intrigue, law_board, law_vote, gov_cards), `governors` (gm_provinces, gm_picker). Each at 1600, 1920 and 2560.
- Consumed by: Tasks 13-16 (Task 16 refuses to deploy unless `--verify-all` passes).

- [ ] **Step 1: The failing check.** Create `Modding Files/source/iron_court_preview/phase3_approvals.py` with the Write tool:

```python
"""The author's approval of each Dwarf court preview, held to the pixels approved.

    py phase3_approvals.py --verify offices
    py phase3_approvals.py --record offices "the author's words, quoted"
    py phase3_approvals.py --verify-all

An approval is the md5 of every picture in its group at the moment the author said
yes, plus a copy of each picture. A picture that changes after that is no longer
approved, and --verify says which.
"""
import hashlib
import io
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
PREVIEW = os.path.join(ROOT, ".skilltree_cache", "ui_preview")
KEEP = os.path.join(HERE, "phase3_approved")
RECORD = os.path.join(KEEP, "approvals.json")
GROUPS = {"offices": ("offices", "pick", "pick_ready"),
          "court": ("court", "log", "petitions", "help"),
          "intrigue_laws": ("intrigue", "law_board", "law_vote", "gov_cards"),
          "governors": ("gm_provinces", "gm_picker")}
SIZES = (1600, 1920, 2560)


def pictures(group):
    out = []
    for view in GROUPS[group]:
        for bw in SIZES:
            out.append("ic_%s_dwf%s.png" % (view, "" if bw == 1920 else "_%d" % bw))
    return out


def md5(path):
    return hashlib.md5(open(path, "rb").read()).hexdigest()


def load():
    return json.load(io.open(RECORD, encoding="utf-8")) if os.path.isfile(RECORD) else {}


def verify(group):
    rec = load().get(group)
    if not rec:
        return ["%s: not approved yet" % group]
    out = []
    for name in pictures(group):
        p = os.path.join(PREVIEW, name)
        if not os.path.isfile(p):
            out.append("%s: %s is not drawn" % (group, name))
        elif md5(p) != rec["md5"].get(name):
            out.append("%s: %s changed since the author approved it" % (group, name))
    return out


def main(argv):
    if argv[:1] == ["--record"]:
        group, words = argv[1], argv[2]
        os.makedirs(KEEP, exist_ok=True)
        rec = load()
        rec[group] = {"words": words, "md5": {}}
        for name in pictures(group):
            src = os.path.join(PREVIEW, name)
            shutil.copyfile(src, os.path.join(KEEP, name))
            rec[group]["md5"][name] = md5(src)
        with io.open(RECORD, "w", encoding="utf-8", newline="\n") as f:
            json.dump(rec, f, indent=1, sort_keys=True)
        print("recorded %s: %d pictures" % (group, len(pictures(group))))
        return 0
    groups = sorted(GROUPS) if argv[:1] == ["--verify-all"] else [argv[1]]
    bad = [p for g in groups for p in verify(g)]
    for b in bad:
        print("FAIL " + b)
    if not bad:
        print("approved: " + ", ".join(groups))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 2: Run it and see it fail.**

Run: `py "Modding Files\source\iron_court_preview\phase3_approvals.py" --verify offices`
Expected: `FAIL offices: not approved yet`, exit 1.

- [ ] **Step 3: Render, compare, show, wait.**

Run: `py tools\preview_iron_court.py --race dwf`
Expected: as Task 11 Step 4.

Open and compare each against the approved mockup `Modding Files\source\iron_court_preview\dwf_skin_E_offices_v2.png` and CA's Book of Grudges (spec 2.6): the fourteen seats on layout E's cells with the throne in the middle of the top row, the hall's stone, runner, pillars, doors and runes behind them, THE GREAT HALL over the knot rule, the lintel title "The Council of Karak Kadrin", the blue ribbons with Offices lit gold in dark ink, the knot frame on every card. Fix anything that differs from the mockup in `gen_ic_ui.py` (`DWF`) or the Lua, re-render, compare again. The first pass is never done.

Show the author these paths and wait for approval:
- `.skilltree_cache\ui_preview\ic_offices_dwf.png`, `ic_offices_dwf_1600.png`, `ic_offices_dwf_2560.png`
- `.skilltree_cache\ui_preview\ic_pick_dwf.png`, `ic_pick_dwf_1600.png`, `ic_pick_dwf_2560.png`
- `.skilltree_cache\ui_preview\ic_pick_ready_dwf.png`, `ic_pick_ready_dwf_1600.png`, `ic_pick_ready_dwf_2560.png`

On the author's yes, record it with their words:
Run: `py "Modding Files\source\iron_court_preview\phase3_approvals.py" --record offices "<the author's words>"`
Expected: `recorded offices: 9 pictures`.

- [ ] **Step 4: Run it and see it pass.**

Run: `py "Modding Files\source\iron_court_preview\phase3_approvals.py" --verify offices`
Expected: `approved: offices`.

- [ ] **Step 5: Checkpoint.** Run THE GATES. Expected: all green; `chd court unchanged`. Show the PNG paths above to the author and wait for approval before Task 13.

---

### Task 13: The Court, Record, Petitions and Help tabs, approved

**Files:**
- Modify (only if the review finds a fault): `tools/gen_ic_ui.py` (`DWF`), `zzz_derpy_iron_court_ui.lua`
- Writes: `Modding Files/source/iron_court_preview/phase3_approved/` (group `court`)

**Interfaces:**
- Consumes: Task 11's pictures; Task 12's `phase3_approvals.py`.

- [ ] **Step 1: The failing check.**

Run: `py "Modding Files\source\iron_court_preview\phase3_approvals.py" --verify court`

- [ ] **Step 2: See it fail.** Expected: `FAIL court: not approved yet`, exit 1.

- [ ] **Step 3: Render, compare, show, wait.**

Run: `py tools\preview_iron_court.py --race dwf`
Expected: as Task 11 Step 4. If Task 12's review changed anything, re-run `--verify offices` too: a change that touched the offices pictures voids that approval and Task 12 Step 3 is repeated.

Compare each against CA's Book of Grudges and the Chaos Dwarf court's approved pictures of the same tabs: the dial and the Crown's box on knot-framed plates, the party cards' frames, the Record and Petitions rows on the dimmed Dwarf ground (every row readable), the Help page's topics as blue ribbons with the open one gold in dark ink. Fix, re-render, compare again.

Show the author these paths and wait for approval:
- `.skilltree_cache\ui_preview\ic_court_dwf.png`, `ic_court_dwf_1600.png`, `ic_court_dwf_2560.png`
- `.skilltree_cache\ui_preview\ic_log_dwf.png`, `ic_log_dwf_1600.png`, `ic_log_dwf_2560.png`
- `.skilltree_cache\ui_preview\ic_petitions_dwf.png`, `ic_petitions_dwf_1600.png`, `ic_petitions_dwf_2560.png`
- `.skilltree_cache\ui_preview\ic_help_dwf.png`, `ic_help_dwf_1600.png`, `ic_help_dwf_2560.png`

On the author's yes: `py "Modding Files\source\iron_court_preview\phase3_approvals.py" --record court "<the author's words>"`
Expected: `recorded court: 12 pictures`.

- [ ] **Step 4: Run it and see it pass.**

Run: `py "Modding Files\source\iron_court_preview\phase3_approvals.py" --verify court`
Expected: `approved: court`.

- [ ] **Step 5: Checkpoint.** Run THE GATES. Expected: all green. Show the PNG paths above to the author and wait for approval before Task 14.

---

### Task 14: Intrigue, the Laws board and vote, and the government chooser, approved

**Files:**
- Modify (only if the review finds a fault): `tools/gen_ic_ui.py` (`DWF`), `zzz_derpy_iron_court_ui.lua`
- Writes: `Modding Files/source/iron_court_preview/phase3_approved/` (group `intrigue_laws`)

**Interfaces:**
- Consumes: Task 11's pictures; Task 12's `phase3_approvals.py`.

- [ ] **Step 1: The failing check.**

Run: `py "Modding Files\source\iron_court_preview\phase3_approvals.py" --verify intrigue_laws`

- [ ] **Step 2: See it fail.** Expected: `FAIL intrigue_laws: not approved yet`, exit 1.

- [ ] **Step 3: Render, compare, show, wait.**

Run: `py tools\preview_iron_court.py --race dwf`, then `py "Modding Files\source\iron_court_preview\phase3_approvals.py" --verify-all` for the groups already approved (any `changed since` line: that group's task is repeated before this one).

Compare: the move cards' knot frames clear of their three blurb lines and their icon, the law cards' frames clear of their name, effects and mark, the law tab buttons as ribbons (the stance and the paid levels lit gold in dark ink; an unaffordable price is CA's red on the blue ribbon - say so to the author with its measured ratio from `check_dwf_contrast`'s method if it reads poorly), the vote's party blocks, the five government cards on knot-framed plates. Fix, re-render, compare again.

Show the author these paths and wait for approval:
- `.skilltree_cache\ui_preview\ic_intrigue_dwf.png`, `ic_intrigue_dwf_1600.png`, `ic_intrigue_dwf_2560.png`
- `.skilltree_cache\ui_preview\ic_law_board_dwf.png`, `ic_law_board_dwf_1600.png`, `ic_law_board_dwf_2560.png`
- `.skilltree_cache\ui_preview\ic_law_vote_dwf.png`, `ic_law_vote_dwf_1600.png`, `ic_law_vote_dwf_2560.png`
- `.skilltree_cache\ui_preview\ic_gov_cards_dwf.png`, `ic_gov_cards_dwf_1600.png`, `ic_gov_cards_dwf_2560.png`

On the author's yes: `py "Modding Files\source\iron_court_preview\phase3_approvals.py" --record intrigue_laws "<the author's words>"`
Expected: `recorded intrigue_laws: 12 pictures`.

- [ ] **Step 4: Run it and see it pass.**

Run: `py "Modding Files\source\iron_court_preview\phase3_approvals.py" --verify intrigue_laws`
Expected: `approved: intrigue_laws`.

- [ ] **Step 5: Checkpoint.** Run THE GATES. Expected: all green. Show the PNG paths above to the author and wait for approval before Task 15.

---

### Task 15: The Governors view, and the author's ruling on `DWF_KEEPS`

**Files:**
- Modify: `tools/gen_ic_ui.py` (`DWF_KEEPS`, `DWF_KEEP_PREFIXES`; and, for each entry the author rules out, the Dwarf branch that replaces it)
- Writes: `Modding Files/source/iron_court_preview/phase3_approved/` (group `governors`)

**Interfaces:**
- Produces: `DWF_KEEPS` as the author ruled it, and the ruling quoted in `approvals.json` under `governors`.

- [ ] **Step 1: The failing check.**

Run: `py "Modding Files\source\iron_court_preview\phase3_approvals.py" --verify governors`

- [ ] **Step 2: See it fail.** Expected: `FAIL governors: not approved yet`, exit 1.

- [ ] **Step 3: Render, list the Chaos Dwarf art, show, wait.**

Run: `py tools\preview_iron_court.py --race dwf`
Then list every Chaos Dwarf picture the Dwarf court draws, from the dump:
Run: `py -c "import sys; sys.path.insert(0, 'tools'); import preview_iron_court as P, gen_ic_ui as U; D = P.race_dump('dwf'); print('\n'.join(sorted(set(p for ns in D.values() for n in ns if n.visible for p in n.images.values() if p and U.CHD_ART.search(p.lower())))))"`
Expected: a short list, each line inside `DWF_KEEPS` or `DWF_KEEP_PREFIXES`.

Show the author these paths and the list above, entry by entry with what it is (the Governors column's Hell-Forge plates, the tab marker's heat glow, the Governors toggle art, the trait, band and Conclave Influence icons, the map pin, the Chaos Dwarf technology paintings on the law cards - CA ships 75 Dwarf technology paintings that could replace the last), and wait for approval and a ruling on each:
- `.skilltree_cache\ui_preview\ic_gm_provinces_dwf.png`, `ic_gm_provinces_dwf_1600.png`, `ic_gm_provinces_dwf_2560.png`
- `.skilltree_cache\ui_preview\ic_gm_picker_dwf.png`, `ic_gm_picker_dwf_1600.png`, `ic_gm_picker_dwf_2560.png`

For each entry the author rules out: remove it from `DWF_KEEPS`, run `py tools\gen_ic_ui.py --check` and `py tools\preview_iron_court.py --race dwf` (both now name it as a fault), give it the Dwarf art the author named the way Task 5 gave the panel its art (a Dwarf branch under `if RACE == "dwf"` for twui art; an `R.art` field read by the Lua for runtime art, mirrored in Task 9's 9c), and re-render. Any re-render that changes an approved group's picture repeats that group's task.

On the author's yes: `py "Modding Files\source\iron_court_preview\phase3_approvals.py" --record governors "<the author's words, including the DWF_KEEPS ruling>"`
Expected: `recorded governors: 6 pictures`.

- [ ] **Step 4: Run it and see it pass.**

Run: `py "Modding Files\source\iron_court_preview\phase3_approvals.py" --verify-all`
Expected: `approved: court, governors, intrigue_laws, offices`.

- [ ] **Step 5: Checkpoint.** Run THE GATES. Expected: all green. Show the PNG paths above to the author and wait for approval before Task 16.

---

### Task 16: Gates, deploy, handoff

**Files:**
- Create: `docs/sessions/HANDOFF_20261004_IRON_COURT_DWARFS_PHASE3_UI.md`
- Modify: `docs/SESSION_INDEX.md` (one line)
- Copy: the 33 Chaos Dwarf preview pictures into `Modding Files/source/iron_court_preview/phase3_approved/chd/` (phase 4 compares its intrigue picture against this copy)

**Interfaces:**
- Consumes: everything above. Produces: the deployed pack and the handoff.

- [ ] **Step 1: The failing check.** The deploy's precondition is every approval still holding:

Run: `py "Modding Files\source\iron_court_preview\phase3_approvals.py" --verify-all; py "Modding Files\source\iron_court_preview\phase3_probe.py" --verify --previews`

- [ ] **Step 2: See it pass or fail for a reason.** Expected: `approved: court, governors, intrigue_laws, offices` and `chd court unchanged: N files`. Any `FAIL`: the named picture changed after approval (repeat its task) or a Chaos Dwarf file moved (find the Dwarf branch that leaked and fix it); do not deploy.

- [ ] **Step 3: Deploy and write up.**

Run THE GATES. Expected: all green.

Check RPFM is open: `Invoke-WebRequest http://127.0.0.1:45127/sessions -TimeoutSec 4 -UseBasicParsing`. Connection refused: tell the author RPFM is closed and stop here.

Run: `Get-Process Warhammer3 -ErrorAction SilentlyContinue` - if it prints a process, run `py tools\deploy_iron_court.py --wait` in the background; otherwise `py tools\deploy_iron_court.py`.
Expected: the deploy's own report - the backup under `Modding Files/Backup/`, the importer green, the pack saved and verified from disk, the copy to `data/` and the Workshop folder. The pack's file list must include `ui/campaign ui/derpy_ic_panel_dwf.twui.xml`, `ui/campaign ui/derpy_ic_panel_dwf_compact.twui.xml` and every `ui/derpy_ic/dwf_*.png` (the deploy ships `UI_FILES` and `art_paths()`).

Copy the Chaos Dwarf previews: `New-Item -ItemType Directory -Force "Modding Files\source\iron_court_preview\phase3_approved\chd"; Copy-Item ".skilltree_cache\ui_preview\ic_*.png" "Modding Files\source\iron_court_preview\phase3_approved\chd\" -Exclude "*_dwf*"`.

Write `docs/sessions/HANDOFF_20261004_IRON_COURT_DWARFS_PHASE3_UI.md`: what shipped (the two twui files, the Dwarf plates and their sizes, the runtime swaps), the measured numbers (backdrop dim, ribbon dims, each knot-frame scale `dwf_knot_scale` chose, the worst cell per race per screen), the author's four approvals quoted from `approvals.json`, the `DWF_KEEPS` ruling, the contract additions (this plan's Interfaces blocks: `ic_throne_of`, `ICUI.RACE_XY`, `ICUI.use_race`, `ICUI.grid_xy`, `ICUI.skin_opener`, `ICUI.tab_art`, `ICUI.light_plate`, `ICUI.lit_word`, `ICUI.TAB_WORD`, `ICUI.RACE_WORDS`, `ICUI.draw_throne`, `ICUI.CARD_FRAME_INDEX`, the `R.art` fields; Python `RACE`, `PANEL_FILE`, `race_xml`, `DWF`, the Dwarf checks, `DWF_KEEPS`; harness `IC_DUMP_RACE`; preview `--race`), and Review Focus 7 for phases 4-6. No emojis, never "rung".

Add ONE line to `docs/SESSION_INDEX.md` in its Iron Court section: `- 2026-10-04 Iron Court Dwarfs phase 3 (Dwarf UI): HANDOFF_20261004_IRON_COURT_DWARFS_PHASE3_UI.md - Dwarf panel pair IC60/IC61, Book of Grudges skin, hall grid, throne; current.`

- [ ] **Step 4: Verify the saved pack, not the plan.** Run: `py tools\read_pack_index.py "<the deployed pack path the deploy printed>" | Select-String "derpy_ic_panel_dwf|derpy_ic/dwf_"`
Expected: the two twui files and every `dwf_*.png` name from `py -c "import sys; sys.path.insert(0,'tools'); import gen_ic_ui as U; print(len(U.dwf_art_paths()))"`'s count.

- [ ] **Step 5: Checkpoint.** Run THE GATES one last time. Expected: all green. Tell the author the court is deployed, with the handoff's path; they confirm it in game (a Dwarf campaign as Karak Kadrin, every tab, then a Chaos Dwarf campaign to see it unchanged).
