"""Packs The Iron Court. Refuses on any drift between the generator, the TSVs,
the Lua and the UI.

Run this before touching RPFM. If it exits non-zero, nothing is packable and the
fault is here, not in the pack.

    py tools/import_iron_court.py
"""
import io
import math
import os
import re
import subprocess
import tempfile
import sys

sys.path.insert(0, "tools")
import gen_iron_court as G            # noqa: E402

SRC = "Modding Files/source/iron_court"
MODEL_LUA = "Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua"
UI_LUA = "Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua"
PARTIES_LUA = "Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_parties.lua"
MCT_LUA = "Modding Files/pack/script/mct/settings/derpy_iron_court.lua"
SCRIPTS = [MODEL_LUA, UI_LUA, PARTIES_LUA, MCT_LUA]
# The UI file legitimately reads other mods' globals (EX.BUTTON_SIZE,
# GGUI.BTN_SIZE) and our own model's (IC.HOUSES). check_lua_undeclared does not
# resolve TABLE.FIELD, so the union of what the whole pack AND its optional
# neighbours declare is passed as `elsewhere` - that is what the parameter is for.
# The shipped zzz_derpy_guilds_ui.lua trips the same names for the same reason.
NEIGHBOUR_LUA = [
    "Modding Files/pack/script/campaign/mod/zzz_derpy_chd_exchange.lua",
    "Modding Files/pack/script/campaign/mod/zzz_derpy_guilds_ui.lua",
]
import gen_ic_ui as _U                  # noqa: E402
import check_lua_undeclared as _CLU     # noqa: E402
import check_lua_literal_left as _CLL   # noqa: E402

# DERIVED FROM THE GENERATOR, never listed by hand. This was four paths written
# out, and adding a fifth file to gen_ic_ui.py left it generated on disk, checked
# by the generator's own selftest, and silently NOT PACKED - the one failure mode
# where every gate passes and the feature is simply absent in game.
# ui_file_names() and not FILES: the compact copies (a box under 1920) are
# written by the same build and are not in FILES, which lists builders.
UI_FILES = ["Modding Files/pack/ui/campaign ui/" + _f for _f in _U.ui_file_names()]
HARNESS = "tools/_iron_court_harness.lua"

# In-pack destination for each generated TSV, and for the loc. DERIVED from the
# generator's own container_path(), not typed out beside it: a table the
# generator emits and this map does not name makes verify() refuse, which is
# the point, and a literal copy of the map could only ever refuse on the tables
# somebody remembered to add to both.
DB_DEST = {_t: G.container_path(_t) for _t in G.TSV_META if _t != "loc"}
LOC_DEST = G.container_path("loc")
LUA_EXE = r"C:\Program Files (x86)\Lua\5.1\lua.exe"
LUAC_EXE = r"C:\Program Files (x86)\Lua\5.1\luac.exe"


def run_lua_pie_box():
    """The panel's OWN wedge loop, lifted out and run under lua.exe.

    Returns the (x, y, w, h) it gives every wedge, or None when lua.exe is
    not installed or the loop has been renamed out from under this.
    """
    if not os.path.isfile(LUA_EXE):
        return None
    ui = io.open(UI_LUA, encoding="utf-8").read()
    m = re.search(r"^for i = 0, ICUI\.DIAL_SLICES - 1 do\n"
                  r'\s*ICUI\.PANEL_XY\[string\.format\("ic_wedge_%02d", i\)\] =\n'
                  r"(.*?)^end\n", ui, re.S | re.M)
    if not m:
        return None
    consts = re.findall(r"^ICUI\.(DIAL_\w+)\s*=\s*(-?\d+)", ui, re.M)
    src = ["ICUI = {PANEL_XY = {}}"]
    src += ["ICUI.%s = %s" % (k, v) for k, v in consts]
    src += ["for i = 0, ICUI.DIAL_SLICES - 1 do",
            '    ICUI.PANEL_XY[string.format("ic_wedge_%02d", i)] =',
            m.group(1).rstrip("\n"), "end",
            'local a = ICUI.PANEL_XY["ic_wedge_00"]',
            'local b = ICUI.PANEL_XY[string.format("ic_wedge_%02d",',
            "                                     ICUI.DIAL_SLICES - 1)]",
            'print(a[1] .. "," .. a[2] .. "," .. a[3] .. "," .. a[4])',
            'print(b[1] .. "," .. b[2] .. "," .. b[3] .. "," .. b[4])']
    path = os.path.join(tempfile.gettempdir(), "ic_pie_box.lua")
    io.open(path, "w", encoding="utf-8", newline="\n").write("\n".join(src))
    try:
        proc = subprocess.run([LUA_EXE, path], capture_output=True, text=True)
    finally:
        os.remove(path)
    if proc.returncode != 0:
        return None
    lines = [ln for ln in proc.stdout.split() if "," in ln]
    if len(lines) != 2 or lines[0] != lines[1]:
        return None
    return tuple(int(n) for n in lines[0].split(","))


def run_lua_card_grid():
    """The panel's OWN card-grid loop, lifted out and run under lua.exe.

    Re-deriving the grid in Python here would compare the generator against a
    second Python implementation of it and prove nothing about the Lua. This
    cuts the real loop out of the real file and executes it, with IC stubbed
    from the generator's offices, so what comes back is what the panel builds.

    Returns None when lua.exe is not installed - a machine without it loses
    this check, and the tier comparison above still covers the inputs.
    """
    if not os.path.isfile(LUA_EXE):
        return None
    ui = io.open(UI_LUA, encoding="utf-8").read()
    m = re.search(r"^ICUI\.CARD_XY = \{\}\n(.*?^end\n)", ui, re.S | re.M)
    if not m:
        return None
    consts = re.findall(r"^ICUI\.(CARDS?_\w+|CONTENT_W)\s*=\s*(-?\d+)$", ui, re.M)
    seats, tiers = {}, []
    for office in G.OFFICES:
        if office["tier"] not in seats:
            tiers.append(office["tier"])
            seats[office["tier"]] = 0
        seats[office["tier"]] += 1
    src = ["ICUI = {}",
           "IC = {TIERS = {%s}, TIER_SEATS = {%s}}"
           % (", ".join(str(t) for t in tiers),
              ", ".join("[%d] = %d" % (t, seats[t]) for t in tiers))]
    src += ["ICUI.%s = %s" % (k, v) for k, v in consts]
    src += ["ICUI.CARD_XY = {}", m.group(1),
            "for i = 1, #ICUI.CARD_XY do",
            '    print(ICUI.CARD_XY[i][1] .. "," .. ICUI.CARD_XY[i][2])',
            "end"]
    path = os.path.join(tempfile.gettempdir(), "ic_card_grid.lua")
    io.open(path, "w", encoding="utf-8", newline="\n").write("\n".join(src))
    try:
        proc = subprocess.run([LUA_EXE, path], capture_output=True, text=True)
    finally:
        os.remove(path)
    if proc.returncode != 0:
        return None
    return [[int(n) for n in line.split(",")]
            for line in proc.stdout.split() if line.strip()]


def run_lua_party_grid():
    """The panel's OWN party-grid loop, lifted out and run under lua.exe.

    Re-deriving the grid in Python would compare the generator against a second
    Python implementation of it and prove nothing about the Lua. Returns None
    when lua.exe is not installed, or when the loop has been renamed out from
    under this - in which case the constant comparison above still covers the
    inputs.
    """
    if not os.path.isfile(LUA_EXE):
        return None
    ui = io.open(UI_LUA, encoding="utf-8").read()
    m = re.search(r"^ICUI\.PARTY_XY = \{\}\n(.*?^end\n)", ui, re.S | re.M)
    if not m:
        return None
    consts = re.findall(
        r"^ICUI\.(PARTY_\w+|PARTIES_[XY]|CARDS_X|CONTENT_W)\s*=\s*(-?\d+)$",
        ui, re.M)
    src = ["ICUI = {}"]
    src += ["ICUI.%s = %s" % (k, v) for k, v in consts]
    src += ["ICUI.PARTY_XY = {}", m.group(1),
            "for i = 1, #ICUI.PARTY_XY do",
            '    print(ICUI.PARTY_XY[i][1] .. "," .. ICUI.PARTY_XY[i][2])',
            "end"]
    path = os.path.join(tempfile.gettempdir(), "ic_party_grid.lua")
    io.open(path, "w", encoding="utf-8", newline="\n").write("\n".join(src))
    try:
        proc = subprocess.run([LUA_EXE, path], capture_output=True, text=True)
    finally:
        os.remove(path)
    if proc.returncode != 0:
        return None
    return [[int(n) for n in line.split(",")]
            for line in proc.stdout.split() if line.strip()]


def run_lua_plot_grid():
    """The panel's OWN move-grid derivation, lifted out and run under lua.exe.

    THIS IS THE CHECK gen_ic_ui.py's plot_grid() docstring says exists. It did
    not: the sixteen card positions and the four column headings are derived
    once in Python and once in Lua from the same rule, and nothing compared
    them - so a formula changed on one side drew every card of the Intrigue tab
    somewhere the other side never heard of, with every other gate green.

    Re-deriving the grid in Python here would compare the generator against a
    second Python implementation of it and prove nothing about the Lua, so this
    cuts the real block out of the real file and executes it, with IC stubbed
    from the generator's own categories and counts.

    Returns (cards, headings) as lists of [x, y], or None when lua.exe is not
    installed or the block has been renamed out from under this.
    """
    if not os.path.isfile(LUA_EXE):
        return None
    ui = io.open(UI_LUA, encoding="utf-8").read()
    # FROM PLOTS_X, not from PLOT_COLS: PLOTS_X, PLOTS_HDR_Y and PLOTS_Y are
    # derived in the four lines above the counts loop and the whole block needs
    # them. Ending at the headings loop takes the card grid with it.
    m = re.search(r"^ICUI\.PLOTS_X = ICUI\.CARDS_X$\n"
                  r'(.*?^\s*ICUI\.PANEL_XY\["ic_plotcat_" \.\. _i\] = .*?^end$\n)',
                  ui, re.S | re.M)
    if not m:
        return None
    import gen_ic_ui as _G2
    cats = _G2.plot_cats()
    counts = _G2.plot_counts()
    consts = re.findall(r"^ICUI\.(CARDS?_\w+|CONTENT_W|ROWS_Y)\s*=\s*(-?\d+)$",
                        ui, re.M)
    src = ["ICUI = {PANEL_XY = {}}"]
    src += ["ICUI.%s = %s" % (k, v) for k, v in consts]
    # THE MOVES THEMSELVES DO NOT MATTER, only how many sit in each category:
    # the grid is arithmetic on the counts and nothing in the block reads a
    # move's own fields.
    src += ["IC = {PLOT_CATS = {%s}}"
            % ", ".join('{key = "%s"}' % c for c, _n in cats),
            "IC.COUNTS = {%s}" % ", ".join(str(n) for n in counts),
            "function IC.plots_in(key)",
            "    for i = 1, #IC.PLOT_CATS do",
            "        if IC.PLOT_CATS[i].key == key then",
            "            local out = {}",
            "            for j = 1, IC.COUNTS[i] do out[j] = {key = key} end",
            "            return out",
            "        end",
            "    end",
            "    return {}",
            "end",
            "ICUI.PLOTS_X = ICUI.CARDS_X",
            m.group(1).rstrip("\n"),
            "for i = 1, #ICUI.PLOT_XY do",
            '    print(ICUI.PLOT_XY[i][1] .. "," .. ICUI.PLOT_XY[i][2])',
            "end",
            'print("--")',
            "for i = 1, ICUI.PLOT_COLS do",
            '    local c = ICUI.PANEL_XY["ic_plotcat_" .. i]',
            '    print(c[1] .. "," .. c[2])',
            "end"]
    path = os.path.join(tempfile.gettempdir(), "ic_plot_grid.lua")
    io.open(path, "w", encoding="utf-8", newline="\n").write("\n".join(src))
    try:
        proc = subprocess.run([LUA_EXE, path], capture_output=True, text=True)
    finally:
        os.remove(path)
    if proc.returncode != 0:
        return None
    cards, heads, seen = [], [], False
    for line in proc.stdout.split():
        line = line.strip()
        if line == "--":
            seen = True
        elif "," in line:
            (heads if seen else cards).append([int(n) for n in line.split(",")])
    return cards, heads


# THE WIDTHS 8d RUNS THE PANEL AT: both ends, the middle of the compact range,
# and 1920 itself, which is the only width the per-name comparison in 8b cannot
# reach for the tables the Lua derives in a loop.
SCALE_WIDTHS = (1600, 1760, 1920, 2560)


def run_lua_scaled(ui_text=None, widths=SCALE_WIDTHS):
    """ICUI.apply_scale itself, in the panel's own file, at each box width.

    The WHOLE file is loaded under lua.exe - the engine stubbed to nothing and
    IC to the generator's offices and moves, as the grid checks above stub it -
    so what comes back is the real tables run through the real apply_scale.
    A second implementation of the rule in Python would compare the generator
    against itself.

    ui_text replaces the file's contents, so a check can be proved against a
    broken copy without writing one to disk. Returns
    {"S": {bw: {name: n}}, "T": {bw: {table: {key: tuple}}}, "O": {name: v},
    "P": {path: path at 1600}}, or None when lua.exe is missing or the file
    will not load.
    """
    if not os.path.isfile(LUA_EXE):
        return None
    if ui_text is None:
        ui_text = io.open(UI_LUA, encoding="utf-8").read()
    import gen_ic_ui as _G2
    seats, tiers = {}, []
    for office in G.OFFICES:
        if office["tier"] not in seats:
            tiers.append(office["tier"])
            seats[office["tier"]] = 0
        seats[office["tier"]] += 1
    cats = _G2.plot_cats()
    counts = _G2.plot_counts()
    src = [
        "local function noop() end",
        "local engine = setmetatable({}, {__index = function() return noop end})",
        "core = engine",
        "cm = engine",
        "IC = {TIERS = {%s}, TIER_SEATS = {%s}, MAX_SEATS = %d}"
        % (", ".join(str(t) for t in tiers),
           ", ".join("[%d] = %d" % (t, seats[t]) for t in tiers), _G2.MAX_HOUSES),
        "IC.PLOT_CATS = {%s}" % ", ".join('{key = "%s"}' % c for c, _n in cats),
        "IC.COUNTS = {%s}" % ", ".join(str(n) for n in counts),
        "function IC.plots_in(key)",
        "    for i = 1, #IC.PLOT_CATS do",
        "        if IC.PLOT_CATS[i].key == key then",
        "            local out = {}",
        "            for j = 1, IC.COUNTS[i] do out[j] = {key = key} end",
        "            return out",
        "        end",
        "    end",
        "    return {}",
        "end",
        "assert(loadfile(arg[1]))()",
        "local function csv(t)",
        "    local o = {}",
        "    for i = 1, #t do o[i] = tostring(t[i]) end",
        "    return table.concat(o, ',')",
        "end",
        # WHAT EACH NAME IS DECLARED AS, and the per-view widths as typed -
        # read at load, before any apply_scale, so a width taken out of the
        # derivation is still compared against the number it started from.
        "for _, list in ipairs({'SCALED', 'DERIVED', 'NOT_SCALED', 'SCALED_TABLES'}) do",
        "    for _, n in ipairs(ICUI[list]) do print('C\t' .. n .. '\t' .. list) end",
        "end",
        "for view, t in pairs(ICUI.COL_W) do",
        "    for j, w in pairs(t) do",
        "        print('B\t' .. view .. '\t' .. ICUI.ROW_KEYS[j] .. '\t' .. w)",
        "    end",
        "end",
        "for _, bw in ipairs({%s}) do" % ", ".join(str(w) for w in widths),
        "    ICUI.apply_scale(bw)",
        "    for _, n in ipairs(ICUI.SCALED) do",
        "        print('S\t' .. bw .. '\t' .. n .. '\t' .. tostring(ICUI[n]))",
        "    end",
        "    for _, n in ipairs(ICUI.SCALED_TABLES) do",
        "        local t = ICUI[n]",
        "        if type(t[1]) == 'number' then",
        "            print('T\t' .. bw .. '\t' .. n .. '\t-\t' .. csv(t))",
        "        else",
        "            for k, v in pairs(t) do",
        "                print('T\t' .. bw .. '\t' .. n .. '\t' .. tostring(k)",
        "                      .. '\t' .. csv(v))",
        "            end",
        "        end",
        "    end",
        # THE DERIVED VALUES BY NAME, not by list: a name taken out of
        # ICUI.DERIVED still prints here, at the value it no longer rescales.
        "    for _, n in ipairs({'CARD_CREST', 'PARTY_CREST', 'HSORT_DY',",
        "                        'SHARE_MIN_SLICES', 'CREST_MIN_SLICES', 'SHARE_INK'}) do",
        "        print('D\t' .. bw .. '\t' .. n .. '\t' .. tostring(ICUI[n]))",
        "    end",
        "    for j = 1, #ICUI.COL_WH do",
        "        print('W\t' .. bw .. '\t' .. ICUI.ROW_KEYS[j] .. '\t' .. csv(ICUI.COL_WH[j]))",
        "    end",
        "    for view, t in pairs(ICUI.COL_W) do",
        "        for j, w in pairs(t) do",
        "            print('V\t' .. bw .. '\t' .. view .. '\t' .. ICUI.ROW_KEYS[j] .. '\t' .. w)",
        "        end",
        "    end",
        "    if bw == 1600 then",
        "        for k, v in pairs(ICUI) do",
        "            if type(k) == 'string' and k:match('^PATH_') then",
        "                print('P\t' .. v .. '\t' .. ICUI.path(v))",
        "            end",
        "        end",
        "    end",
        "end",
        "for k, v in pairs(ICUI.COMPACT_OVERRIDES) do",
        "    print('O\t' .. k .. '\t' .. (type(v) == 'table' and csv(v) or tostring(v)))",
        "end",
    ]
    tmp = tempfile.gettempdir()
    driver = os.path.join(tmp, "ic_scaled_driver.lua")
    panel = os.path.join(tmp, "ic_scaled_panel.lua")
    io.open(driver, "w", encoding="utf-8", newline="\n").write("\n".join(src))
    io.open(panel, "w", encoding="utf-8", newline="\n").write(ui_text)
    try:
        proc = subprocess.run([LUA_EXE, driver, panel], capture_output=True, text=True)
    finally:
        os.remove(driver)
        os.remove(panel)
    if proc.returncode != 0:
        return None
    out = {"S": {}, "T": {}, "O": {}, "P": {}, "C": {}, "B": {}, "D": {},
           "W": {}, "V": {}}
    for line in proc.stdout.splitlines():
        f = line.split("\t")
        if f[0] == "C":
            out["C"][f[1]] = f[2]
        elif f[0] == "B":
            out["B"][(f[1], f[2])] = int(float(f[3]))
        elif f[0] == "D":
            out["D"].setdefault(int(f[1]), {})[f[2]] = int(float(f[3]))
        elif f[0] == "W":
            out["W"].setdefault(int(f[1]), {})[f[2]] = tuple(
                int(float(n)) for n in f[3].split(","))
        elif f[0] == "V":
            out["V"].setdefault(int(f[1]), {})[(f[2], f[3])] = int(float(f[4]))
        elif f[0] == "S":
            out["S"].setdefault(int(f[1]), {})[f[2]] = int(float(f[3]))
        elif f[0] == "T":
            tables = out["T"].setdefault(int(f[1]), {})
            tables.setdefault(f[2], {})[f[3]] = tuple(int(float(n))
                                                      for n in f[4].split(","))
        elif f[0] == "O":
            v = tuple(int(n) for n in f[2].split(","))
            out["O"][f[1]] = v if len(v) > 1 else v[0]
        elif f[0] == "P":
            out["P"][f[1]] = f[2]
    return out


def check_scaled(ui_text=None):
    """8d: the panel's scaled layout equals the generator's at every width.

    The compact files and every check the generator makes at a width are built
    from at_box(width); the panel scales its own copy of the tables at open. A
    difference is a cell the checks measured somewhere the panel does not put
    it, which no screenshot at 1080p would ever show.
    """
    import gen_ic_ui as U3
    got = run_lua_scaled(ui_text)
    if got is None:
        if os.path.isfile(LUA_EXE):
            return ["the panel Lua would not load under lua.exe, so its scaled "
                    "layout is compared by nothing"]
        return []
    problems = []
    for bw in SCALE_WIDTHS:
        g = U3 if bw == 1920 else U3.at_box(bw)
        found = []
        pairs = {"PORT_W": g.PORT_BOX[0], "PORT_H": g.PORT_BOX[1],
                 "CREST_W": g.CREST_BOX[0], "CREST_H": g.CREST_BOX[1]}
        for name, v in sorted(got["S"].get(bw, {}).items()):
            want = pairs.get(name, getattr(g, name, None))
            if want is None:
                found.append("ICUI.%s is scaled and the generator has no %s"
                             % (name, name))
            elif v != want:
                found.append("ICUI.%s is %d, the generator's %d" % (name, v, want))
        gen_tables = {
            "PANEL_XY": g.PANEL_LAYOUT, "ROW_CHILD_XY": g.ROW_LAYOUT,
            "CARD_CHILD_XY": g.CARD_LAYOUT, "PARTY_CHILD_XY": g.PARTY_LAYOUT,
            "PLOT_CHILD_XY": g.PLOT_LAYOUT,
            "CARD_XY": {str(i + 1): p for i, p in enumerate(g.CARD_GRID)},
            "PARTY_XY": {str(i + 1): p for i, p in enumerate(g.PARTY_GRID)},
            "PLOT_XY": {str(i + 1): p for i, p in enumerate(g.plot_grid())},
            "COURT_SECTION_XY": {"-": g.COURT_SECTION_XY},
            "ACT_PAGED_XY": g.ACT_PAGED,
        }
        lua_tables = got["T"].get(bw, {})
        for table in sorted(set(lua_tables) | set(gen_tables)):
            if table not in gen_tables:
                found.append("ICUI.%s is scaled and nothing in the generator "
                             "answers for it" % table)
                continue
            if table not in lua_tables:
                found.append("ICUI.%s is not in ICUI.SCALED_TABLES" % table)
                continue
            lua_t, gen_t = lua_tables[table], gen_tables[table]
            for key in sorted(set(lua_t) | set(gen_t)):
                if key not in gen_t:
                    found.append("%s.%s is in the Lua and not the generator"
                                 % (table, key))
                elif key not in lua_t:
                    found.append("%s.%s is in the generator and not the Lua"
                                 % (table, key))
                elif lua_t[key] != tuple(gen_t[key]):
                    found.append("%s.%s is %s in the Lua and %s in the generator"
                                 % (table, key, lua_t[key], tuple(gen_t[key])))
        # THE DERIVED VALUES, against the cells they are derived from. The
        # generator has no copy of these, so an ICUI.DERIVED entry dropped from
        # apply_scale kept its 1920 value at every width with 8d green.
        d = got["D"].get(bw, {})
        want_d = {
            "CARD_CREST": g.CARD_LAYOUT["ic_card_crest"][2],
            "PARTY_CREST": g.PARTY_LAYOUT["ic_party_crest"][2],
            "HSORT_DY": g.PANEL_LAYOUT["ic_hsort_a"][1] - g.PANEL_LAYOUT["ic_hdr_a"][1],
            # ICUI.min_slices, with the generator's radii and the Lua's ink.
            "SHARE_MIN_SLICES": int(math.ceil(
                d.get("SHARE_INK", 0) / (g.SHARE_R * math.pi / g.DIAL_SLICES))),
            "CREST_MIN_SLICES": int(math.ceil(
                g.CREST_PX / (g.CREST_R * math.pi / g.DIAL_SLICES))),
        }
        for name, want in sorted(want_d.items()):
            if d.get(name) != want:
                found.append("ICUI.%s is %s, and the cells it derives from make it %d"
                             % (name, d.get(name), want))
        for key, wh in sorted(got["W"].get(bw, {}).items()):
            if wh != tuple(g.ROW_LAYOUT[key][2:4]):
                found.append("ICUI.COL_WH for %s is %s and the row cell is %s"
                             % (key, wh, tuple(g.ROW_LAYOUT[key][2:4])))
        for (view, key), w in sorted(got["V"].get(bw, {}).items()):
            bx = U3.ROW_LAYOUT[key][0]
            want = U3.sc(bx + got["B"][(view, key)], bw) - U3.sc(bx, bw)
            if w != want:
                found.append("ICUI.COL_W.%s for %s is %d; its 1920 edge scales to %d"
                             % (view, key, w, want))
        for line in found[:8]:
            problems.append("at a %d box: %s" % (bw, line))
        if len(found) > 8:
            problems.append("at a %d box: and %d more" % (bw, len(found) - 8))
    # WHAT EACH NAME IS DECLARED AS. A name the generator scales and the Lua
    # files under NOT_SCALED is compared by nothing above - 8d reads only the
    # names the Lua lists as scaled - so ROW_H moved there left 61px rows on a
    # 53px pitch at 1600 with every gate green.
    gen_scaled = set(U3.SCALED_SCALARS) | {"PORT_W", "PORT_H", "CREST_W", "CREST_H"}
    for name, cls in sorted(got["C"].items()):
        if name in gen_scaled and cls not in ("SCALED", "DERIVED"):
            problems.append("ICUI.%s is declared %s and the generator scales it"
                            % (name, cls))
    # A PER-VIEW WIDTH ON A COLUMN WITH AN OVERRIDE: the derivation scales the
    # 1920 edge and never applies the override, so the two would disagree.
    for view, key in sorted(got["B"]):
        if key in U3.COMPACT_OVERRIDES:
            problems.append("ICUI.COL_W.%s widens %s, which carries a compact "
                            "override the width derivation does not apply"
                            % (view, key))
    want_over = {k: (tuple(v) if isinstance(v, (tuple, list)) else v)
                 for k, v in U3.COMPACT_OVERRIDES.items()}
    if got["O"] != want_over:
        for name in sorted(set(got["O"]) | set(want_over)):
            if got["O"].get(name) != want_over.get(name):
                problems.append("ICUI.COMPACT_OVERRIDES.%s is %s and the "
                                "generator's is %s"
                                % (name, got["O"].get(name), want_over.get(name)))
    # WHICH FILE EACH PATH OPENS BELOW 1920. A compact path that names no file
    # the generator writes is a panel that never opens on a small screen.
    seen = set()
    for path, small in sorted(got["P"].items()):
        base = os.path.basename(path) + ".twui.xml"
        seen.add(base)
        want = U3.COMPACT_FILES.get(base, base)
        if os.path.basename(small) + ".twui.xml" != want:
            problems.append("below 1920 the panel opens %s for %s, and the "
                            "generator writes %s" % (small, path, want))
    for base in sorted(set(U3.COMPACT_FILES) - seen):
        problems.append("the generator writes a compact %s and no ICUI.PATH_ "
                        "names its base file" % U3.COMPACT_FILES[base])
    return problems


def _roller_callers(src, roller):
    """Every function in the model that calls `roller`, by name.

    A flat scan: Lua has no nesting this file uses inside a function body, so
    the enclosing function is simply the last `function IC.x(` seen above the
    call. Good enough to answer "who calls this", which is the whole question.
    """
    here, out = None, []
    for line in src.splitlines():
        m = re.match(r"function (IC\.\w+)\(", line)
        if m:
            here = m.group(1)
        if roller in line and not line.lstrip().startswith("--"):
            # THE DEFINITION IS NOT A CALL. "IC.roll_origin()" appears in its
            # own `function` line, and rstrip("(") does not take the "()" off a
            # roller written with its brackets - so split on the first bracket.
            if not re.match(r"function %s\(" % re.escape(roller.split("(")[0]),
                            line):
                out.append(here)
    return out


def check_rollers(src):
    """The rollers may be reached from one place each, and it is the place that
    asks whether the man is a legend first.

    FOUR STAMPING SITES were found one at a time - stamp_court, IC.hired, the
    CharacterCreated listener and stamp_incoming - and each was fixed by
    grepping for the next. A legend dealt a random childhood is silent: he just
    has the wrong two lines on his card forever. This is what makes the grep
    unnecessary, because a fifth site cannot be added without failing here.
    """
    out = []
    for roller, gate in (("IC.roll_origin()", "IC.origin_for"),
                         ("IC.roll_background(", "IC.background_for")):
        callers = sorted(set(_roller_callers(src, roller)))
        if callers != [gate]:
            out.append("%s is called from %s and may only be called from %s - "
                       "every other caller rolls a legendary lord a past he "
                       "already has"
                       % (roller, ", ".join(callers) or "nowhere", gate))
    return out


# CA's own member index, off the anchors in its doc: every member of every
# script interface is listed as href="#<INTERFACE><member>", so this needs no
# HTML parsing and cannot drift from what the doc actually says.
DOC_HTML = os.path.join("Modding Files", "reference", "ca_script_docs_wh3",
                        "scripting_doc.html")
DOC_ANCHOR = re.compile(r'#([A-Z_]+_SCRIPT_INTERFACE)(\w+)"')

# WHICH STUB STANDS FOR WHICH INTERFACE. Only the constructor's own top-level
# keys are checked - a nested table inside one of these is a DIFFERENT
# interface (a region, a list, character_details) and pinning those means
# naming what every accessor returns, which is bookkeeping this does not buy.
STUBS = (("make_character", "CHARACTER_SCRIPT_INTERFACE"),
         ("make_faction", "FACTION_SCRIPT_INTERFACE"))

# Members CA does not document that the harness may stub anyway. An entry here
# is a claim about the ENGINE, so it must cite CA's own shipped scripts - not
# "the harness needs it", which is exactly the reasoning that put is_dead on a
# character in the first place.
STUB_UNDOCUMENTED = {
    ("CHARACTER_SCRIPT_INTERFACE", "is_alive"):
        "undocumented, but CA calls it on characters in 8 shipped files - "
        "including inside a CharacterConvalescedOrKilled handler, which is "
        "this exact use (campaign/wh3_dlc27_intrigue_at_the_court.lua)",
}


def _doc_members(path=DOC_HTML):
    """interface -> {member}, read off CA's doc index."""
    out = {}
    if not os.path.isfile(path):
        return out
    with io.open(path, encoding="utf-8", errors="replace") as fh:
        for iface, member in DOC_ANCHOR.findall(fh.read()):
            out.setdefault(iface, set()).add(member)
    return out


def _stub_members(src, ctor):
    """The TOP-LEVEL keys of the table `ctor` builds, by brace depth.

    Strings and comments go out through check_lua_undeclared._blank first, so
    a brace inside either cannot move the depth. Returns None when the
    constructor or its table has been renamed out from under this, which the
    caller reports rather than passing vacuously.
    """
    code = _CLU._blank(src)
    at = code.find("local function " + ctor)
    if at < 0:
        return None
    i = code.find("{", at)
    if i < 0:
        return None
    keys, depth, prev, n = set(), 0, "", len(code)
    while i < n:
        ch = code[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return keys
        elif depth == 1 and not ch.isspace() and prev in "{,;":
            # A table KEY is the first token after the brace or a separator.
            # Anything else at this depth is a statement inside one of the
            # stub's own function bodies, and `local x =` is not a member.
            m = re.match(r"([a-zA-Z_]\w*)\s*=(?!=)", code[i:])
            if m:
                keys.add(m.group(1))
        if not ch.isspace():
            prev = ch
        i += 1
    return None


def check_character_stub(harness_src, docs=None):
    """A stub may not invent a method the engine does not have.

    THE BUG THIS EXISTS FOR: the character stub carried `is_dead`, which is a
    FACTION member - CA documents it once, under FACTION_SCRIPT_INTERFACE, and
    the character's list carries is_wounded and no is_dead at all. So the
    shipped ic_dead handler raised on its fourth line every time an officer
    died, and 259 checks stayed green because the harness answered a question
    the engine would have thrown on.

    check_lua_api.py cannot catch this class AT ALL: it resolves cm:, core:,
    bm: and common. - singletons - and every receiver in the court model is a
    character, a faction or a region. The harness is the only thing that makes
    those calls succeed offline, so pinning what it may stub is what closes it.
    This is the same shape as the note already in the harness about is_unique
    being on CHARACTER_DETAILS_SCRIPT_INTERFACE and not on the character.
    """
    if docs is None:
        docs = _doc_members()
    out = []
    if not docs:
        return ["CA's scripting_doc.html is missing, so no stub was checked "
                "against it"]
    for ctor, iface in STUBS:
        members = _stub_members(harness_src, ctor)
        if members is None:
            out.append("the harness stub %s was not found, so nothing held it "
                       "against %s" % (ctor, iface))
            continue
        known = docs.get(iface)
        if not known:
            out.append("%s is not in CA's doc index, so %s went unchecked"
                       % (iface, ctor))
            continue
        for key in sorted(members):
            # _foo is the fixture's own state, not a member of the interface.
            if key.startswith("_") or key in known:
                continue
            if (iface, key) in STUB_UNDOCUMENTED:
                continue
            out.append("the %s stub answers :%s(), which is not a member of %s "
                       "- the model can then call a method the engine does not "
                       "have and every check here passes" % (ctor, key, iface))
    return out


# A dotted write to a loyalty field: `house.loyalty =`, `h.loyalty =`,
# `court.houses[slug].loyalty =`. NOT a table-constructor key (`loyalty  = 55`
# in unpack and new_court), which has no dot in front of it and is how a house
# is born rather than how its mood moves.
LOYALTY_WRITE = re.compile(r"[\w%s]\.loyalty\s*=(?!=)" % re.escape("]"))
LOYALTY_OWNER = "IC.move_loyalty"


def check_loyalty_writers(src):
    """Loyalty has exactly one writer, and the breakdown depends on it.

    THE BUG THIS EXISTS FOR: there were six. drift clamped both ends, the bribe
    clamped its ceiling and the murder its floor, and the appointment, the snub
    and the sacking each wrote an inline number - +8, -6, -12 - that IC.TUNE did
    not name and no tooltip could ever explain. "Loyalty is a percentage" was a
    rule with six owners and no place to read it off.

    The same shape as check_rollers: a seventh writer cannot be added without
    failing here, which is what makes grepping for the next one unnecessary.
    """
    out = []
    here, writers = None, {}
    for line in src.splitlines():
        m = re.match(r"function (IC\.\w+)\(", line)
        if m:
            here = m.group(1)
        if line.lstrip().startswith("--"):
            continue
        if LOYALTY_WRITE.search(line):
            writers.setdefault(here, 0)
            writers[here] += 1
    names = sorted(k for k in writers if k != LOYALTY_OWNER)
    if names:
        out.append("loyalty is written directly in %s - every move goes through "
                   "%s, which is the only place that clamps it and the only "
                   "place the breakdown can name"
                   % (", ".join(str(n) for n in names), LOYALTY_OWNER))
    if LOYALTY_OWNER not in writers:
        out.append("%s writes no loyalty at all, so either it was renamed or "
                   "the check below it is guarding nothing" % LOYALTY_OWNER)
    return out


# THE ELEVEN PANEL ACTIONS. Called straight off a click they change the campaign
# on the clicking machine only, which in multiplayer is a desync.
DIRECT_ACTION = re.compile(
    r"\bIC\.(appoint|dismiss|assign_governor|release_governor|plot|favour|hire|"
    r"grant_demand|refuse_demand|accept_offer|decline_offer|fill_offices)\s*\(")


def check_mp_routing(ui_src):
    """The panel changes the campaign only through IC.mp_send.

    A model change made on one machine and not the others is a desync, so every
    panel action is sent as a UITrigger and applied on every machine when it
    comes back. One call site left calling the model directly plays perfectly in
    single player and desyncs the first time it is clicked in multiplayer - a
    campaign nobody here can run, so nothing in play would ever show it.
    Comments and strings are blanked first: the panel describes the calls it no
    longer makes.
    """
    body = _CLU._blank(ui_src)
    hits = sorted(set(m.group(1) for m in DIRECT_ACTION.finditer(body)))
    if not hits:
        return []
    return ["the panel calls %s directly - in multiplayer that changes one machine "
            "only; send it through IC.mp_send" % ", ".join("IC." + h for h in hits)]


TUNE_ORDER_BLOCK = re.compile(r"IC\.TUNE_ORDER\s*=\s*\{(.*?)\n\}", re.S)
REGISTRATION_BLOCKS = re.compile(r"IC\.(TUNE_ORDER|PRESETS)\s*=\s*\{.*?\n\}", re.S)


def check_tune_reads(model_src, sources):
    """Every setting on the MCT page is read by name somewhere it does something.

    A setting is registered three times - the MCT page, IC.TUNE, IC.TUNE_ORDER -
    and the court harness holds those against each other. This is the fourth
    hit: a read. Without one the control renders, toggles, freezes into the save
    and changes nothing, which is how the Great Guilds shipped one (2026-09-12).
    `sources` are the campaign scripts' texts, the model's included; the two
    registration blocks are cut out first, since they name every key.
    """
    m = TUNE_ORDER_BLOCK.search(model_src)
    if not m:
        return ["the model declares no IC.TUNE_ORDER, so no setting was checked"]
    keys = re.findall(r'"(\w+)"', m.group(1))
    if not keys:
        return ["IC.TUNE_ORDER names no setting, so no setting was checked"]
    text = "\n".join(re.sub(r"--[^\n]*", "", REGISTRATION_BLOCKS.sub("", s))
                     for s in sources)
    out = []
    for key in keys:
        if not re.search(r'\bTUNE\.%s\b|\bT\.%s\b|"%s"' % (key, key, key), text):
            out.append("the setting %s is on the MCT page and read nowhere - its "
                       "control would change nothing" % key)
    return out


def _selftest():
    """Each check added for MCT and multiplayer reports a planted fault and
    passes the clean shape. A check nobody has watched fail proves nothing."""
    assert check_mp_routing('IC.mp_send(faction, "appoint", k)') == []
    assert check_mp_routing('-- IC.appoint(faction, k, cqi)\nlocal s = "IC.plot("') == []
    assert check_mp_routing("IC.plot_chance(f, k) IC.favour_cost(k) IC.hire_settlement(f)") == []
    bad = check_mp_routing("IC.appoint(faction, k, cqi)\nIC.decline_offer(f, s)")
    assert len(bad) == 1 and "IC.appoint" in bad[0] and "IC.decline_offer" in bad[0], bad
    model = 'IC.TUNE_ORDER = {\n    "alpha", "beta", "gamma",\n}\nlocal x = IC.TUNE.alpha\n'
    parties = "local y = T.beta -- IC.TUNE.gamma is only mentioned here\n"
    bad = check_tune_reads(model, [model, parties])
    assert len(bad) == 1 and "gamma" in bad[0], bad
    quoted = model + 'local z = "gamma"\n'
    assert check_tune_reads(quoted, [quoted, parties]) == []
    assert check_tune_reads("local nothing = 1", []) != []
    print("import_iron_court selftest: ok")


def verify():
    problems = G.check()
    built = G.build()

    # 0. THE ROLLERS HAVE ONE CALLER EACH. See check_rollers: a legendary lord
    #    dealt a random birthplace is silent, and the four sites that could deal
    #    him one were found by grepping after each fix rather than by anything
    #    refusing to pack.
    if os.path.isfile(MODEL_LUA):
        problems.extend(check_rollers(io.open(MODEL_LUA, encoding="utf-8").read()))
    else:
        problems.append("the court model is missing, so no roller was checked")

    # 0b. NO STUB INVENTS A METHOD. See check_character_stub: the harness is
    #     the only thing that makes this model's character and faction calls
    #     succeed offline, and for the life of the file it answered is_dead on
    #     a character - a faction member - so the death handler raised in game
    #     while every check here was green.
    if os.path.isfile(HARNESS):
        problems.extend(check_character_stub(
            io.open(HARNESS, encoding="utf-8").read()))
    else:
        problems.append("the court harness is missing, so no stub was checked")

    # 0c. LOYALTY HAS ONE WRITER. See check_loyalty_writers: it had six, three
    #     of them with the number written inline, so the biggest levers in the
    #     system were the only ones IC.TUNE did not name and the breakdown could
    #     not explain.
    if os.path.isfile(MODEL_LUA):
        problems.extend(check_loyalty_writers(
            io.open(MODEL_LUA, encoding="utf-8").read()))

    # 0d. THE PANEL CHANGES THE CAMPAIGN ONLY THROUGH IC.mp_send. See
    #     check_mp_routing: a direct call is a multiplayer desync nothing in
    #     single-player play would ever show.
    if os.path.isfile(UI_LUA):
        problems.extend(check_mp_routing(io.open(UI_LUA, encoding="utf-8").read()))

    # 0e. EVERY SETTING IS READ, and the page that offers them ships. See
    #     check_tune_reads.
    if not os.path.isfile(MCT_LUA):
        problems.append("the MCT settings file is missing, so the pack would ship "
                        "with no settings page")
    if os.path.isfile(MODEL_LUA):
        srcs = [io.open(p, encoding="utf-8").read()
                for p in (MODEL_LUA, PARTIES_LUA, UI_LUA) if os.path.isfile(p)]
        problems.extend(check_tune_reads(srcs[0], srcs))

    # 1. Every generated table has a destination, and its on-disk TSV matches
    #    build() row for row. A stale TSV is how a removed feature nearly ships.
    for table, rows in built.items():
        if table == "loc":
            continue
        if table not in DB_DEST:
            problems.append("table %s has no in-pack destination" % table)
        path = os.path.join(SRC, table + ".tsv")
        if not os.path.isfile(path):
            problems.append("missing TSV: " + path)
            continue
        with io.open(path, encoding="utf-8") as fh:
            fh.readline()                      # header
            meta = fh.readline()
            n = sum(1 for _ in fh)
        if n != len(rows):
            problems.append("%s.tsv has %d rows, build() says %d" % (table, n, len(rows)))
        # Row 2 must be RPFM's metadata line or the import is refused outright
        # with "invalid version value at line 1" while importing nothing.
        want = "#%s;%d;" % (G.TSV_META[table][0], G.TSV_META[table][1])
        if not meta.startswith(want):
            problems.append("%s.tsv metadata line is %r, expected to start %r"
                            % (table, meta.strip()[:60], want))

    loc_path = os.path.join(SRC, "loc.tsv")
    if os.path.isfile(loc_path):
        with io.open(loc_path, encoding="utf-8") as fh:
            fh.readline()
            fh.readline()
            n = sum(1 for _ in fh)
        if n != len(built["loc"]):
            problems.append("loc.tsv has %d rows, build() says %d" % (n, len(built["loc"])))
    else:
        problems.append("missing TSV: " + loc_path)

    # 2. The Lua's own copies of HOUSES and OFFICES must agree with the
    #    generator's. Both files declare them, and a drift means a house with
    #    bundles and no model, or an office the model fills and nothing buffs.
    if not os.path.isfile(MODEL_LUA):
        problems.append("missing script: " + MODEL_LUA)
    else:
        lua = io.open(MODEL_LUA, encoding="utf-8").read()

        # THE FACTION BESIDE EACH ORIGIN, which is the half nothing else
        # looks at: gen_ic_ui's check 22 compares the two slug lists and stops
        # there. A confederated faction is matched to an origin by this key
        # alone, and a key that names no faction never matches anything - so
        # every lord of an absorbed house is stamped with a birthplace instead,
        # silently, and the record of where he came from is gone.
        block = re.search(r"IC\.ORIGINS\s*=\s*\{(.*?)\n\}", lua, re.S)
        if not block:
            problems.append("the Lua has no IC.ORIGINS table")
        else:
            pairs = dict(re.findall(r'slug\s*=\s*"(\w+)"\s*,\s*faction\s*=\s*"([\w]+)"',
                                    block.group(1)))
            for slug, faction, _d in G.ORIGINS:
                if faction is None:
                    # A PLACE. It must carry no faction at all, or a man raised
                    # at home reads as a confederate out of a faction that is
                    # very likely still alive on the map under its own name.
                    if slug in pairs:
                        problems.append("origin %s is a place and the Lua gives "
                                        "it faction %s" % (slug, pairs[slug]))
                elif slug not in pairs:
                    problems.append("origin %s has no faction in the Lua" % slug)
                elif pairs[slug] != faction:
                    problems.append("origin %s: Lua faction %s, generator %s"
                                    % (slug, pairs[slug], faction))
            for slug in pairs:
                if slug not in G.origin_slugs():
                    problems.append("origin %s is in the Lua and not the generator"
                                    % slug)

        block = re.search(r"IC\.OFFICES\s*=\s*\{(.*?)\n\}", lua, re.S)
        if not block:
            problems.append("the Lua has no IC.OFFICES table")
        else:
            pairs = dict(re.findall(r'slug\s*=\s*"(\w+)"\s*,\s*affinity\s*=\s*"(\w+)"',
                                    block.group(1)))
            for office in G.OFFICES:
                if office["slug"] not in pairs:
                    problems.append("office %s is in the generator and not the Lua"
                                    % office["slug"])
                elif pairs[office["slug"]] != office["affinity"]:
                    problems.append("office %s: Lua affinity %s, generator %s"
                                    % (office["slug"], pairs[office["slug"]],
                                       office["affinity"]))
            for slug in pairs:
                if not G.office_by_slug(slug):
                    problems.append("office %s is in the Lua and not the generator" % slug)

            # THE TIER, which is what the office GRANTS as well as where it is
            # drawn: the generator multiplies every magnitude by it. A tier that
            # disagrees is a card in the wrong band buffing by the wrong amount.
            # A LIST, IN THE LUA'S ORDER, not a dict. The order is half of what
            # is being checked: the panel walks IC.OFFICES top to bottom and
            # fills the bands in that order, so a shuffled table draws a band
            # with a hole in it - and re-deriving the order from G.OFFICES
            # instead would make it the generator's order, which is never the
            # one at fault.
            seq = [(slug, int(t)) for slug, t in re.findall(
                r'slug\s*=\s*"(\w+)"\s*,\s*affinity\s*=\s*"\w+"\s*,\s*tier\s*=\s*(\d+)',
                block.group(1))]
            tiers = dict(seq)
            for office in G.OFFICES:
                if tiers.get(office["slug"]) != office["tier"]:
                    problems.append("office %s: Lua tier %r, generator %d"
                                    % (office["slug"], tiers.get(office["slug"]),
                                       office["tier"]))
            order = [t for _slug, t in seq]
            if order != sorted(order):
                problems.append("the Lua's offices are not grouped by tier: %s" % order)

        block = re.search(r"IC\.AMBITION\s*=\s*\{(.*?)\n\}", lua, re.S)
        if not block:
            problems.append("the Lua has no IC.AMBITION table")
        else:
            lua_traits = re.findall(r'trait\s*=\s*"([^"]+)"', block.group(1))
            generator_traits = ["derpy_ic_ambition_" + slug
                                for slug in G.AMBITION_BANDS]
            if lua_traits != generator_traits:
                problems.append("ambition traits disagree: Lua %r, generator %r"
                                % (lua_traits, generator_traits))

        # 2a. THE CONTROL BANDS. The model decides which band the player is in
        #     and the generator ships the bundle that band applies - and they
        #     are in different files, keyed by the same slug, with the floors
        #     written out twice. A floor that disagrees moves the boundary for
        #     one half only; a slug that disagrees is a band whose effects do
        #     not exist, applied silently, every turn, for the rest of the
        #     campaign.
        block = re.search(r"IC\.CONTROL\s*=\s*\{(.*?)\n\}", lua, re.S)
        if not block:
            problems.append("the Lua has no IC.CONTROL table")
        else:
            got = [(a, int(b)) for a, b in re.findall(
                r'slug\s*=\s*"(\w+)"\s*,\s*floor\s*=\s*(\d+)', block.group(1))]
            want = [(b[0], b[1]) for b in G.CONTROL_BANDS]
            if got != want:
                problems.append(
                    "the control bands disagree: the Lua has %r and the "
                    "generator %r. They are walked top down, so the ORDER is "
                    "half of what is being compared." % (got, want))
            elif want and want[-1][1] != 0:
                problems.append(
                    "the lowest control band starts at %d, so a court below "
                    "that lands in no band at all" % want[-1][1])

        # 2b. THE HIRE LIST IS THREE UNVALIDATED STRINGS. An agent subtype key
        #     that does not exist does not error - cm:spawn_agent_at_settlement
        #     takes it as a string and makes nothing, forever, with the court's
        #     influence already spent. Both halves are checked against vanilla:
        #     the subtype exists, and the agent type beside it is the one that
        #     subtype actually belongs to.
        hires = re.search(r"IC\.HIRE\s*=\s*\{(.*?)\n\}", lua, re.S)
        if not hires:
            problems.append("the Lua has no IC.HIRE table")
        else:
            pairs = re.findall(
                r'subtype\s*=\s*"([\w]+)"\s*,\s*\n?\s*agent\s*=\s*"([\w]+)"',
                hires.group(1))
            try:
                import read_vanilla_cache as _V
                subtypes = {r["key"] for r in _V.load("agent_subtypes")[0]}
                agents = {r["key"] for r in _V.load("agents")[0]}
                owner = {}
                for row in _V.load("character_skill_node_sets")[0]:
                    owner.setdefault(row["agent_subtype_key"], row["agent_key"])
            except Exception as exc:
                problems.append("the vanilla agent tables are unreadable, so "
                                "IC.HIRE cannot be checked: %r" % (exc,))
            else:
                for subtype, agent in pairs:
                    if subtype not in subtypes:
                        problems.append("IC.HIRE names agent subtype %s, which "
                                        "is in no vanilla table" % subtype)
                    if agent not in agents:
                        problems.append("IC.HIRE names agent type %s, which is "
                                        "in no vanilla table" % agent)
                    elif subtype in owner and owner[subtype] != agent:
                        problems.append("IC.HIRE pairs %s with agent type %s; "
                                        "vanilla says it is a %s"
                                        % (subtype, agent, owner[subtype]))

        # 2c. THE STANDING BANDS ARE BUILT BY CONCATENATION, so no literal in
        #     the Lua names them and check 3's grep cannot reach them. A
        #     force_add_trait against a key with no character_traits row fails
        #     SILENTLY - the trait simply never appears - so a band the
        #     generator does not emit is a character panel that says nothing
        #     about a man's standing for the whole campaign.
        #
        #     THE TIER LIST COMES FROM THE LUA (check 2's own parse, reused),
        #     not from the generator: deriving both sides from G.OFFICES would
        #     make this a comparison of one number with itself.
        prefix = re.search(
            'function IC[.]standing_trait[(]tier[)]'
            r'\s*return\s*"(\w+?)"\s*[.][.]\s*tier', lua)
        if not prefix:
            problems.append("the Lua has no IC.standing_trait to derive band "
                            "keys from")
        elif not seq:
            problems.append("no office tiers were read out of the Lua, so the "
                            "standing bands cannot be checked")
        else:
            stem = prefix.group(1)
            declared = set(r["key"] for r in built["character_traits"])
            want = set()
            # Tier 0 is the man who clears nothing - a real band, and the one a
            # fresh campaign stamps on everybody.
            for tier in [0] + sorted(set(t for _slug, t in seq)):
                key = "%s%d" % (stem, tier)
                want.add(key)
                if key not in declared:
                    problems.append("the Lua stamps standing band %s, which no "
                                    "character_traits row declares" % key)
            # And the other way: a band the generator emits that the Lua can
            # never build is a trait row nothing ever stamps.
            for key in sorted(declared):
                if key.startswith(stem) and key not in want:
                    problems.append("the generator emits standing band %s, "
                                    "which the Lua can never stamp" % key)

        # 3. Every bundle the Lua names must be one the generator emits. A typo
        #    here is an effect bundle that never applies, with no error.
        defined = set(r["key"] for r in built["effect_bundles"])
        for key in sorted(set(re.findall(r'"(derpy_ic_(?:office|vacant|gov)_\w+)"', lua))):
            # A literal ending in "_" is a concatenation PREFIX, not a key - the
            # Lua builds "derpy_ic_office_" .. slug. Testing those as keys is a
            # false refusal on correct code.
            if key.endswith("_"):
                continue
            if key not in defined:
                problems.append("the Lua applies %s, which the generator does not emit" % key)
        # Both halves build their bundle keys by concatenation, so check the
        # prefixes the same way.
        for prefix in ('"derpy_ic_office_"', '"derpy_ic_vacant_"',
                       '"derpy_ic_gov_house_"'):
            if prefix not in lua:
                problems.append("the Lua no longer builds %s keys" % prefix)

        # 4. Every trait the Lua names must exist.
        traits = set(r["key"] for r in built["character_traits"])
        for key in sorted(set(re.findall(r'"(derpy_ic_(?:house|title)_\w+)"', lua))):
            if key.endswith("_"):
                continue
            if key not in traits:
                problems.append("the Lua uses trait %s, which the generator does not emit"
                                % key)

        # 5. string.find's plain flag corrupts the string subsystem process-wide
        #    for the rest of the game session. check_lua_api catches it too; it is
        #    repeated here because this is the gate that refuses to pack.
        if re.search(r"string\.find\([^)]*,\s*true\s*\)", lua):
            problems.append("string.find's plain flag is present, which corrupts "
                            "the string subsystem process-wide")

        # 6. No loc call in the model file. A loc call from a turn handler is a
        #    CTD at turn 1 that pcall does not catch.
        for call in ("effect_text", "common.get_localised_string", "get_localised_string"):
            if call in lua:
                problems.append("the model file makes a loc call (%s) - that is a "
                                "turn-1 CTD" % call)

    # 6b. SetStateText writes the CURRENT STATE ONLY, and its second argument is a
    #     stringtable key rather than a state name. It produced two separate
    #     player-visible faults on 2026-09-11 and neither logged a script error:
    #     tab captions that blanked on mouseover, and a GOVERNORS tab that kept
    #     drawing the INTRIGUE row, because the redraw landed while the cursor was
    #     still over the component so the new string went to `hover` while
    #     `standard` kept the old one. SetText writes every state. The Great
    #     Guilds documents this in its own file header and it still got copied
    #     wrong here, so the gate refuses it rather than trusting a comment.
    #
    #     Comments are stripped first: this very file describes the call it bans,
    #     and a scan that skips that step fires on its own prose.
    for script in SCRIPTS:
        if not os.path.isfile(script):
            continue
        # _blank, NOT _strip: _strip returns a (code, declared, used) TUPLE
        # and `"SetStateText" in <tuple>` is vacuously false forever. _blank
        # is the one that returns the comment- and string-blanked source.
        body = _CLU._blank(io.open(script, encoding="utf-8").read())
        if "SetStateText" in body:
            problems.append(
                "%s calls SetStateText, which writes only the current state - "
                "use SetText(text, \"\"), which writes all of them"
                % os.path.basename(script))

    # 6c. :Parent() returns a component ADDRESS, not a uicomponent, so reading an
    #     id off it needs UIComponent TWICE. A single wrap throws, and because the
    #     walk lives inside a pcall it throws SILENTLY - leaving the row index nil
    #     and every button in the panel dead while the clicks register perfectly.
    #     The Great Guilds and the Zharr Exchange each shipped this once.
    #
    #     The harness cannot catch it: its fake :Parent() returns the component
    #     itself, so one wrap and two behave identically there. Only the source
    #     shape distinguishes them, so it is checked here.
    for script in SCRIPTS:
        if not os.path.isfile(script):
            continue
        body = io.open(script, encoding="utf-8").read()
        for m in re.finditer(r"UIComponent\s*\([^)]*?\)\s*:Parent\s*\(\s*\)\s*:",
                             body):
            problems.append(
                "%s reads straight off :Parent(), which returns an ADDRESS - wrap "
                "it: UIComponent(UIComponent(x):Parent()):Id()"
                % os.path.basename(script))

    # 6d. Every Resize must go through ICUI.resize, which sets the two resizeable
    #     permissions first. CA: "The uicomponent may be need to set to be
    #     resizeable before calling this - this can be done with
    #     uicomponent:SetCanResizeHeight and uicomponent:SetCanResizeWidth."
    #     Without them the engine may keep the component's authored size and
    #     report nothing, which looks exactly like a standing bar whose segments
    #     are all one width and a scroll thumb that never shortens. Both shipped.
    #
    #     The harness asserts the permissions inside its Resize stub, but only on
    #     paths a check drives; this catches an unexercised call site too.
    for script in SCRIPTS:
        if not os.path.isfile(script):
            continue
        body = _CLU._blank(io.open(script, encoding="utf-8").read())
        for m in re.finditer(r"(\w+)\s*:\s*Resize\s*\(", body):
            # The one legal site is the helper's own call, on its local `c`.
            line_start = body.rfind("\n", 0, m.start()) + 1
            line = body[line_start:body.find("\n", m.start())]
            if m.group(1) == "c" and "ICUI.resize" in body[max(0, m.start() - 400):m.start()]:
                continue
            problems.append(
                "%s calls %s:Resize directly (%s) - route it through ICUI.resize, "
                "which sets SetCanResizeWidth/Height first"
                % (os.path.basename(script), m.group(1), line.strip()[:60]))

    # 7. The Lua parses, and the model behaves. luac catches syntax; the harness
    #    drives the branches no static check reaches.
    if os.path.isfile(LUAC_EXE):
        for script in SCRIPTS:
            r = subprocess.call([LUAC_EXE, "-p", script],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if r != 0:
                problems.append("luac -p failed on " + script)
    if os.path.isfile(LUA_EXE) and os.path.isfile(HARNESS):
        proc = subprocess.Popen([LUA_EXE, HARNESS],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out = proc.communicate()[0].decode("utf-8", "replace")
        if proc.returncode != 0:
            problems.append("the court harness failed: " + out.strip().splitlines()[0])

    # 8. Undeclared ALL_CAPS globals. An undeclared Lua global is nil, not an
    #    error, so luac -p and check_lua_api both pass over it.
    #    undeclared() takes the SOURCE TEXT, not a path. Passing a filename makes
    #    it scan the filename, find nothing, and pass vacuously - which is how a
    #    gate ends up guarding nothing at all.
    try:
        srcs = {}
        for path in SCRIPTS + NEIGHBOUR_LUA:
            if os.path.isfile(path):
                srcs[path] = io.open(path, encoding="utf-8").read()
        for script in SCRIPTS:
            if script not in srcs:
                continue
            elsewhere = set()
            for path, src in srcs.items():
                if path != script:
                    elsewhere |= set(_CLU.declared_in(src))
            for name in _CLU.undeclared(srcs[script], elsewhere):
                problems.append("%s reads undeclared global %s"
                                % (os.path.basename(script), name))
    except Exception as exc:
        problems.append("the undeclared-global check could not run: %r" % (exc,))

    # 8a. NO NUMBER ON THE LEFT OF AN ARITHMETIC OPERATOR in a function over 255
    #     constants. The game's compiler loads that literal into a register the
    #     right operand then overwrites: PLOT_H shipped as -11 and stacked every
    #     move card, while stock lua.exe - the harness, 8d - computed 176.
    for script in SCRIPTS:
        if not os.path.isfile(script):
            continue
        try:
            for line, op in _CLL.findings(script):
                problems.append("%s:%d %s has a number literal on its left - the "
                                "game computes it wrong"
                                % (os.path.basename(script), line, op))
        except SystemExit as exc:
            problems.append("the literal-left check could not run: %s" % (exc,))

    # 8b. The panel Lua's own copy of every layout offset must equal the
    #     generator's. The .twui.xml offsets do NOT position a runtime component -
    #     layout() moves every child by hand - so a drift here is a cell drawn at
    #     the wrong place with every other check green.
    try:
        import gen_ic_ui as U3
        if os.path.isfile(UI_LUA):
            ui = io.open(UI_LUA, encoding="utf-8").read()

            def lua_xy(table_name):
                m = re.search(r"ICUI\.%s\s*=\s*\{(.*?)\n\}" % table_name, ui, re.S)
                if not m:
                    return None
                # FOUR NUMBERS, x, y, w, h: layout() SIZES every cell as
                # well as placing it now, so a width that drifts is a cell
                # that clips on screen with every position still agreeing.
                found = {}
                for name, x, y, w, h in re.findall(
                        r"(\w+)\s*=\s*\{\s*(-?\d+)\s*,\s*(-?\d+)\s*,"
                        r"\s*(-?\d+)\s*,\s*(-?\d+)\s*\}", m.group(1)):
                    found[name] = (int(x), int(y), int(w), int(h))
                return found

            for lua_name, gen_table in (("PANEL_XY", U3.PANEL_LAYOUT),
                                        ("ROW_CHILD_XY", U3.ROW_LAYOUT),
                                        ("CARD_CHILD_XY", U3.CARD_LAYOUT),
                                        ("PARTY_CHILD_XY", U3.PARTY_LAYOUT)):
                found = lua_xy(lua_name)
                if found is None:
                    problems.append("the panel Lua has no ICUI.%s table" % lua_name)
                    continue
                # BOTH loop families. "ic_barc_00" does not start with
                # "ic_bar_" - the underscore is in the way - so the crest plates
                # were being demanded as literal entries in a table that builds
                # them in a loop, exactly like the segments beside them.
                def _looped(n):
                    # lua_xy() reads the table LITERAL, and all three of these
                    # families are added to it by a loop underneath. The crests
                    # are covered by CREST_R and CREST_PX below; the wedges are
                    # covered by run_lua_pie_box(), which runs the loop; and the
                    # category headings by 8c below, which runs theirs. NOTHING
                    # may be added to this list without a check that executes
                    # the loop it excuses - the list is where a cell goes to
                    # stop being checked at all.
                    return (n.startswith("ic_bar_")
                            or n.startswith("ic_barc_")
                            or n.startswith("ic_barp_")
                            or n.startswith("ic_div_")
                            or n.startswith("ic_plotcat_")
                            or n.startswith("ic_wedge_"))

                for name, box in gen_table.items():
                    if _looped(name):
                        continue            # generated by a loop in both files
                    if name not in found:
                        problems.append("%s: %s is in the generator and not the Lua"
                                        % (lua_name, name))
                    elif found[name] != tuple(box):
                        problems.append("%s: %s is %s in the Lua and %s in the generator"
                                        % (lua_name, name, found[name], tuple(box)))
                for name in found:
                    if name not in gen_table and not _looped(name):
                        problems.append("%s: %s is in the Lua and not the generator"
                                        % (lua_name, name))

            # 8b1. THE EVENT FEED'S INDICES, on both sides of the same fence.
            #      The number the script passes and the number the DB record
            #      answers to are written in two different files, and if they
            #      disagree the engine logs that it showed an event and draws
            #      nothing at all - no error, no feed entry, nothing to see in
            #      game. The persistent flag is the same kind of trap: it must
            #      agree with the record's event type or the message is dropped.
            _model_src = (io.open(MODEL_LUA, encoding="utf-8").read()
                          if os.path.isfile(MODEL_LUA) else "")
            mev = re.search(r"IC\.EVENTS\s*=\s*\{(.*?)\n\}", _model_src, re.S)
            if not mev:
                problems.append("the model Lua declares no IC.EVENTS, so nothing "
                                "the court does reaches the event feed")
            else:
                lua_ev = {}
                # THREE FIELDS. The third says whether the event has a
                # secondary line of its own, and it is the same class of
                # trap as the other two: a model that names a
                # _secondary loc key the generator never emitted draws
                # an empty plate, which is the fault this column fixed.
                for _slug, _idx, _per, _sec in re.findall(
                        r"(\w+)\s*=\s*\{\s*(\d+)\s*,\s*(true|false)\s*,\s*(true|false)\s*\}",
                        mev.group(1)):
                    lua_ev[_slug] = (int(_idx), _per == "true",
                                     _sec == "true")
                gen_ev = {e[0]: (G.event_index(e[0]), e[1],
                                 e[6] is not None) for e in G.EVENTS}
                for _slug in sorted(set(gen_ev) | set(lua_ev)):
                    if _slug not in lua_ev:
                        problems.append(
                            "event %s has DB rows and the model never raises it"
                            % _slug)
                    elif _slug not in gen_ev:
                        problems.append(
                            "the model raises event %s, which has no DB record - "
                            "it draws nothing, silently" % _slug)
                    elif lua_ev[_slug] != gen_ev[_slug]:
                        problems.append(
                            "event %s is %s in the model and %s in the "
                            "generator (index, persistent, secondary)"
                            % (_slug, lua_ev[_slug], gen_ev[_slug]))

            # 8b2. WHAT A VACANT CARD TAKES OFF ITSELF.
            #
            #      RE-AIMED 2026-09-17. It used to derive which cells a vacant
            #      card SHIFTS, from the portrait's own y band, because a vacant
            #      seat hid its face and the text moved into the gap. No seat
            #      hides its face now - a vacant one wears ICUI.SILHOUETTE - so
            #      there is no shift and nothing to derive.
            #
            #      THE HAZARD THAT REPLACED IT is the one this panel has been
            #      bitten by before: cards are RECYCLED, so a seat that just
            #      emptied is drawn on the component that held the last officer,
            #      and a layer nobody actively clears keeps HIS art. The
            #      silhouette covers the face; the house plate and the colour
            #      mask are two more layers behind it, and a vacant seat wearing
            #      the last holder's party colour reads as a seat that party
            #      still holds.
            _vac = re.search(r"function ICUI\.set_vacant_plate\(.*?\nend",
                             ui, re.S)
            if not _vac:
                problems.append(
                    "the panel Lua declares no ICUI.set_vacant_plate, so a "
                    "vacant office card keeps the last holder's house plate "
                    "behind its silhouette")
            else:
                for _layer in ("PLATE_INDEX", "MASK_INDEX"):
                    if _layer not in _vac.group(0):
                        problems.append(
                            "ICUI.set_vacant_plate never clears ICUI.%s, so a "
                            "recycled card keeps the last holder's art on that "
                            "layer" % _layer)
                if "MASK_NONE" not in _vac.group(0):
                    problems.append(
                        "ICUI.set_vacant_plate clears its layers with something "
                        "other than ICUI.MASK_NONE - a path that resolves to "
                        "nothing draws a blank white square, silently")

            # 8c. THE MOVE GRID AND ITS COLUMN HEADINGS. Both are derived
            #     from IC.PLOTS twice - once in gen_ic_ui.py and once in the
            #     panel - and until this check they were never compared. The
            #     headings are excused from the literal comparison above
            #     BECAUSE of this, so if this stops running they are unchecked.
            grid = run_lua_plot_grid()
            if grid is None:
                if os.path.isfile(LUA_EXE):
                    problems.append(
                        "the panel's move-grid block could not be run - it has "
                        "been renamed, and the sixteen card positions and four "
                        "column headings are now compared by nothing")
            else:
                cards, heads = grid
                want = U3.plot_grid()
                if len(cards) != len(want):
                    problems.append(
                        "the panel builds %d move cards and the generator %d - "
                        "a card with no coordinates never draws"
                        % (len(cards), len(want)))
                else:
                    for i, (gx, gy) in enumerate(want):
                        if cards[i] != [gx, gy]:
                            problems.append(
                                "move card %d is at %s in the panel and %s in "
                                "the generator" % (i + 1, tuple(cards[i]),
                                                   (gx, gy)))
                if len(heads) != U3.PLOT_COLS:
                    problems.append(
                        "the panel names %d category columns and the generator "
                        "%d" % (len(heads), U3.PLOT_COLS))
                for i, xy in enumerate(heads):
                    name = "ic_plotcat_%d" % (i + 1)
                    if name not in U3.PANEL_LAYOUT:
                        problems.append("%s is in the panel and not the "
                                        "generator" % name)
                        continue
                    gx, gy, _w, _h = U3.PANEL_LAYOUT[name]
                    if xy != [gx, gy]:
                        problems.append(
                            "%s is at %s in the panel and %s in the generator"
                            % (name, tuple(xy), (gx, gy)))

            # THE COLUMN WIDTHS, which the Lua now resizes per view. The
            # defaults in ICUI.COL_WH have to be the twui's own widths or the
            # first draw of any view without an override RESIZES every cell to
            # a number nobody chose - and a text cell that is 180px when the
            # layout says 620 clips silently, which is the bug this pair exists
            # to stop repeating.
            m = re.search("ICUI\\.COL_WH\\s*=\\s*\\{(.*?)\\}\\n", ui, re.S)
            if not m:
                problems.append("the panel Lua has no ICUI.COL_WH table")
            else:
                got = [(int(a), int(b)) for a, b in
                       re.findall(r"\{\s*(\d+)\s*,\s*(\d+)\s*\}", m.group(1))]
                want = [U3.ROW_LAYOUT[k][2:] for k in
                        ("ic_row_a", "ic_row_b", "ic_row_c", "ic_row_d",
                         "ic_row_e", "ic_row_f")]
                if got != want:
                    problems.append(
                        "ICUI.COL_WH is %s and the generator's columns are %s"
                        % (got, want))

            # The row origin, the row pitch and the standing bar geometry are
            # declared as bare numbers in both files. ONE NAME PER LINE in the Lua,
            # because check_lua_undeclared does not register every target of a
            # multiple assignment and would refuse to pack on the combined form.
            # BAR_W was compared against ROW_W, which was only ever right because
            # the bar and the rows happened to share a width. They do not any
            # more: the bar spans the panel and the rows stop 18px short to leave
            # the scrollbar its column. A cross-check that passes by coincidence
            # stops being a cross-check the moment the coincidence ends.
            for name, want in (("ROWS_X", U3.ROWS_X), ("ROWS_Y", U3.ROWS_Y),
                               ("ROW_PITCH", U3.ROW_PITCH),
                               # THE PIE. The generator builds the pool of
                               # cells and the Lua rasterises the half disc
                               # into them, so these are the whole of what
                               # holds the two halves together - the per-name
                               # offset check exempts ic_pip_* precisely
                               # because only one side does the geometry.
                               # DIAL_SLICES is the component count AND the
                               # number of pictures per colour: the panel asks
                               # for wedge_NN and the generator wrote wedge_NN.
                               ("DIAL_SLICES", U3.DIAL_SLICES),
                               ("DIAL_R", U3.DIAL_R),
                               ("DIAL_CX", U3.DIAL_CX),
                               ("DIAL_CY", U3.DIAL_CY),
                               ("CREST_R", U3.CREST_R),
                               # The exemption above stops comparing the crest
                               # offsets name by name, so the constants the two
                               # loops derive them from are compared instead.
                               ("CREST_PX", U3.CREST_PX),
                               # The share labels ride the same rays and are
                               # placed by the same loop, so they are pinned the
                               # same way the crests are.
                               ("SHARE_R", U3.SHARE_R),
                               ("SHARE_W", U3.SHARE_W),
                               ("SHARE_H", U3.SHARE_H),
                               ("MAX_ROWS", U3.VISIBLE_ROWS),
                               # WHERE EACH VIEW PUTS ITS LIST. The pool is one
                               # set of positions and the court starts partway
                               # down it, so both files have to agree on where
                               # the strip goes and which row is first or the
                               # court's headers label the wrong columns.
                               ("HDR_GAP", U3.HDR_GAP),
                               ("HDR_Y", U3.HDR_Y),
                               # NOT MAX_HOUSES. It reads #IC.PARTIES now, so
                               # there are no digits here to compare - and
                               # gen_ic_ui's check 22 compares the two party
                               # lists in order, which pins the count as a
                               # consequence.
                               # The opener's size lives in both files and was
                               # checked by nothing - it is only a comment in the
                               # Lua that says it must match.
                               ("BTN_SIZE", U3.OPENER_W),
                               # The ziggurat's own arithmetic. Both files
                               # derive fourteen positions from these seven
                               # numbers, so a drift in one of them moves every
                               # card on the tab.
                               ("CARDS_X", U3.CARDS_X),
                               ("CARDS_Y", U3.CARDS_Y),
                               ("CARD_GAP_X", U3.CARD_GAP_X),
                               ("CARD_GAP_Y", U3.CARD_GAP_Y),
                               ("CARD_W", U3.CARD_W),
                               ("CARD_H", U3.CARD_H),
                               ("CONTENT_W", U3.CONTENT_W)):
                m = re.search(r"ICUI\.%s\s*=\s*(-?\d+)" % name, ui)
                if not m:
                    problems.append("the panel Lua does not declare ICUI.%s" % name)
                elif int(m.group(1)) != want:
                    problems.append("ICUI.%s is %s in the Lua and %s in the generator"
                                    % (name, m.group(1), want))

            # WHERE THE PANEL ACTUALLY PUTS A WEDGE. Every one of them is the
            # whole pie box, so one entry answers for all sixty - and it is the
            # only thing left that the constants above cannot pin, because the
            # Lua could read them and still write the box down wrong.
            got_box = run_lua_pie_box()
            if got_box is None:
                problems.append("the panel Lua's wedge loop would not run")
            elif got_box != tuple(U3.PIE_BOX):
                problems.append(
                    "the panel gives its wedges %s and the generator draws "
                    "the pie box at %s" % (got_box, tuple(U3.PIE_BOX)))

            # EVERY WEDGE THE PANEL CAN ASK FOR, and the generator wrote it.
            # The pie's SHAPE is in the png now, so a path is the only thing
            # left that can be wrong - and it fails the way every wrong path
            # fails here, as a blank square with nothing in the log.
            art = U3.art_paths()
            m = re.search(r'function ICUI\.wedge_path\(i, slug\)\s*\n'
                          r'\s*return string\.format\("([^"]+)"', ui)
            if not m:
                problems.append("the panel Lua has no ICUI.wedge_path")
            else:
                fmt = m.group(1).replace("%02d", "%02d").replace("%s", "%s")
                seats = [p[0] for p in G.PARTIES]
                seats += [h[0] for h in G.ORIGINS if h[1]]
                seats.append(None)
                missing = []
                for i in range(U3.DIAL_SLICES):
                    for slug in seats:
                        want = fmt % (i, slug or "none")
                        if want not in art:
                            missing.append(want)
                if missing:
                    problems.append(
                        "the panel can ask for %d wedge pictures the generator "
                        "does not write, starting with %s"
                        % (len(missing), missing[0]))

            # THE GRID ITSELF, position by position. The constants above are
            # the inputs; this is the output, and a Lua loop that rounds the
            # centring the other way puts every band a pixel off with every
            # input still agreeing.
            got = run_lua_card_grid()
            if got is None:
                problems.append("could not evaluate ICUI.CARD_XY")
            elif got != [list(xy) for xy in U3.CARD_GRID]:
                problems.append("the card grid differs: the Lua builds %s and "
                                "the generator %s"
                                % (got[:3], [list(x) for x in U3.CARD_GRID[:3]]))

            # THE PARTY GRID, the same way and for the same reason. The Lua
            # DECLARES what the generator DERIVES - five columns exactly
            # filling the content width, two rows finishing above the pager -
            # so every one of these is a number written twice.
            for lua_name, want in (("PARTY_W", U3.PARTY_W),
                                   ("PARTY_H", U3.PARTY_H),
                                   ("PARTY_COLS", U3.PARTY_COLS),
                                   ("PARTY_ROWS", U3.PARTY_ROWS),
                                   ("PARTY_GAP_X", U3.PARTY_GAP_X),
                                   ("PARTY_GAP_Y", U3.PARTY_GAP_Y),
                                   ("PARTIES_Y", U3.PARTIES_Y)):
                m = re.search(r"ICUI\.%s\s*=\s*(-?\d+)" % lua_name, ui)
                if not m:
                    problems.append("the panel Lua does not declare ICUI.%s"
                                    % lua_name)
                elif int(m.group(1)) != want:
                    problems.append(
                        "ICUI.%s is %s in the Lua and %s in the generator"
                        % (lua_name, m.group(1), want))
            got = run_lua_party_grid()
            if got is None:
                problems.append("could not evaluate ICUI.PARTY_XY")
            elif got != [list(xy) for xy in U3.PARTY_GRID]:
                problems.append("the party grid differs: the Lua builds %s and "
                                "the generator %s"
                                % (got[:3], [list(x) for x in U3.PARTY_GRID[:3]]))

            # 8d. THE SCALED LAYOUT, at four box widths. Everything above
            #     compares the 1920 numbers; the panel scales its own copy at
            #     open, and the compact files and the generator's checks at a
            #     width are built from at_box(width).
            problems.extend(check_scaled(ui))

            # SCAN THE CODE, NOT THE COMMENTS. This file documents in prose that
            # the shipped mods never call DestroyComponent, and a raw scan reads
            # that sentence as a live call - the same fault the Guilds' UI checker
            # hit when this file's own comments named button_rituals.
            ui_code = re.sub(r"--\[\[.*?\]\]", "", ui, flags=re.S)
            ui_code = re.sub(r"(?m)--.*$", "", ui_code)
            if "DestroyComponent" in ui_code:
                problems.append("the panel Lua calls DestroyComponent, which neither "
                                "shipped mod uses - the calls are DestroyChildren/Destroy")
            # A panel that does not eat the mouse is scenery: hovering raises the
            # map's tooltips straight through it.
            if "SetInteractive" not in ui_code:
                problems.append("the panel never calls SetInteractive - it will not "
                                "consume mouse input and the map shows through it")
            if "PropagatePriority" not in ui_code:
                problems.append("the panel never calls PropagatePriority - it can draw "
                                "under other HUD components")
    except Exception as exc:
        problems.append("the panel layout cross-check could not run: %r" % (exc,))

    # 9. The UI files exist and the UI generator agrees with what is on disk.
    try:
        import gen_ic_ui as U2
        problems += U2.check()
        built_xml = U2.build_xml()
        for path in UI_FILES:
            name = os.path.basename(path)
            if not os.path.isfile(path):
                problems.append("missing UI file: " + path)
            elif io.open(path, encoding="utf-8").read() != built_xml[name]:
                problems.append("%s on disk differs from the generator - re-run "
                                "gen_ic_ui.py" % name)
        # 9b. THE LAYER NUMBERS. The plate and the face are two layers of one
        #     component and the two files address them by index. If they drift
        #     apart nothing errors: the face is written to the plate's layer, the
        #     plate is never seen, and the portrait simply has no house colour
        #     behind it - which is indistinguishable from the bug this replaced.
        for name in ("PLATE_INDEX", "FACE_INDEX", "MASK_INDEX"):
            m = re.search(r"ICUI\.%s\s*=\s*(\d+)" % name, ui)
            if not m:
                problems.append("the panel declares no ICUI.%s" % name)
            elif int(m.group(1)) != getattr(U2, name):
                problems.append("ICUI.%s is %s and gen_ic_ui.py says %d"
                                % (name, m.group(1), getattr(U2, name)))
        # 9c. And the path they name. A plate the panel asks for under a name the
        #     generator never wrote is a blank square, silently.
        probe = U2.plate_path("PROBE")
        head, tail = probe.split("PROBE")
        if head not in ui or tail not in ui:
            problems.append("ICUI.plate_path does not build %s - the panel would "
                            "ask for art that was never written" % probe)
        # 9d. THE MASK SET. The panel derives <portrait>_mask1.png at runtime, and
        #     a derived path that is in no pack draws a BLANK WHITE SQUARE over a
        #     man's face with nothing in the log. The only thing standing between
        #     those two facts is that the panel refuses to derive a path for any
        #     stem outside ICUI.MASKED - so that table must be exactly what
        #     gen_ic_ui.py just read out of the installed packs, never a list
        #     someone typed.
        if 'ICUI.MASK_NONE = "%s"' % U2.MASK_NONE not in ui:
            problems.append("the panel's ICUI.MASK_NONE is not %s, so an unmasked "
                            "portrait falls back to a path nothing wrote"
                            % U2.MASK_NONE)
        want = U2.masked_portraits(quiet=True)
        if want is None:
            problems.append("the game is not installed, so the panel's mask set "
                            "cannot be checked against the packs")
        else:
            block = re.search(r"ICUI\.MASKED\s*=\s*\{(.*?)\n\}", ui, re.S)
            got = sorted(re.findall(r'\["([^"]+)"\]\s*=\s*true',
                                    block.group(1))) if block else []
            if got != sorted(want):
                missing = sorted(set(want) - set(got))
                extra = sorted(set(got) - set(want))
                problems.append(
                    "ICUI.MASKED is not what the installed packs say: %d entries "
                    "against %d. Missing %s; not in any pack %s - re-run the "
                    "generator. An entry with no file behind it is a white square "
                    "on a portrait."
                    % (len(got), len(want), missing[:4] or "none", extra[:4] or "none"))
    except Exception as exc:
        problems.append("UI checks could not run: %r" % (exc,))

    return problems


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        _selftest()
        sys.exit(0)
    bad = verify()
    for problem in bad:
        print("REFUSING: " + problem)
    if bad:
        sys.exit(1)
    built = G.build()
    print("verify ok - %d bundles, %d junctions, %d traits, %d loc, %d script(s), "
          "%d ui file(s), %d generated png(s)" % (
              len(built["effect_bundles"]),
              len(built["effect_bundles_to_effects_junctions"]),
              len(built["character_traits"]),
              len(built["loc"]), len(SCRIPTS), len(UI_FILES),
              len(_U.art_paths())))
    for table, dest in sorted(DB_DEST.items()):
        print("  %-42s -> %s" % (table + ".tsv", dest))
    print("  %-42s -> %s" % ("loc.tsv", LOC_DEST))
    for path in SCRIPTS:
        print("  %-42s -> %s" % (os.path.basename(path),
                                 path.split("Modding Files/pack/", 1)[1]))
    for path in UI_FILES:
        print("  %-42s -> ui/campaign ui/%s"
              % (os.path.basename(path), os.path.basename(path)))
