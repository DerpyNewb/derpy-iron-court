# -*- coding: utf-8 -*-
"""Render every Iron Court view to PNGs with the game shut, and validate the XML.

Every view in VIEWS (plus DWF_VIEWS for the Dwarfs), at every size in SIZES, for both
races, into .skilltree_cache/ui_preview/. A Chaos Dwarf view is drawn from gen_ic_ui.py's
coordinates with its words parsed out of the shipped Lua; the laws views and every Dwarf
view are what the shipped Lua itself left on the harness's fake tree (IC_DUMP and
IC_DUMP_RACE, run under lua.exe). Our .twui.xml carries no offsets, because the Lua
MoveTo's every piece, so the file alone would stack the panel in one corner.

It reuses tools/preview_guilds_panel.py's two halves: TWUI Studio's reader validates the
<hierarchy>/<components> links the way the engine does, and its rasteriser nine-slices
CA's art. The demo court is the hardest one the model can roll: the Crown plus rivals_max
rivals, each wearing the longest name its tail list allows. Text is PIL's font widened by
GAME_FONT_WIDER, so wraps are faithful; whether a label fits is gen_ic_ui.py check 20g's
question, not this one's.

    py tools/preview_iron_court.py                 # every view, both races
    py tools/preview_iron_court.py --race dwf      # one race
    py tools/preview_iron_court.py --check         # validate the XML only, no PNG
    py tools/preview_iron_court.py --selftest

Vendored source: TWUI_Studio/pyc, else TWUI_Studio/src (non-commercial licence, see its
LICENSE.txt).
"""
import collections
import io
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import preview_guilds_panel as PG               # noqa: E402  - the reusable half

PREFIX = "derpy_ic_"
LOCAL = os.path.join(ROOT, "Modding Files", "pack")
OUT = os.path.join(PG.CACHE, "ic_court.png")
OUT_INTRIGUE = os.path.join(PG.CACHE, "ic_intrigue.png")
# THE CHARACTER PICKER, TWICE. It is the one list in the panel long enough to
# have to be hunted through - IC.candidates hands back whatever order
# faction:character_list() gave it, which is not alphabetical and not by anything
# a player can predict - so the sort control was built for it, and a single
# picture of a button says nothing about what the button does. The first is the
# panel as it opens; the second is the same twelve men under AVAILABLE.
OUT_PICK = os.path.join(PG.CACHE, "ic_pick.png")
OUT_PICK_READY = os.path.join(PG.CACHE, "ic_pick_ready.png")
# THE ZIGGURAT, the tab the panel opens on. Fourteen cards in four bands, half
# of them empty.
OUT_OFFICES = os.path.join(PG.CACHE, "ic_offices.png")
# THE PETITIONS TAB: the one list with two buttons on a row. Its worst line is
# the longest name demanding the longest province.
OUT_PETITIONS = os.path.join(PG.CACHE, "ic_petitions.png")
# THE GOVERNORS VIEW: the column over the live map, as two
# pictures, one per page shape. The map is a flat stand-in - a shut game has no
# campaign map to draw - and the pins stand on it in a sheet, not on
# settlements, which is the engine's job.
OUT_GM = os.path.join(PG.CACHE, "ic_gm_provinces.png")
OUT_GM_PICK = os.path.join(PG.CACHE, "ic_gm_picker.png")
GM_MAP_FILL = (46, 52, 38, 255)
# THE LAWS TAB: the board of twenty laws with the chosen
# one read out on the right, and a vote's two sides of party blocks.
OUT_LAW_BOARD = os.path.join(PG.CACHE, "ic_law_board.png")
OUT_LAW_VOTE = os.path.join(PG.CACHE, "ic_law_vote.png")
# THE GOVERNMENT CHOOSER: five cards, off the same dump.
OUT_GOV_CARDS = os.path.join(PG.CACHE, "ic_gov_cards.png")
VIEWS = ("court", "intrigue", "pick", "pick_ready", "offices", "petitions",
         "gm_provinces", "gm_picker", "law_board", "law_vote", "gov_cards")
LUA_EXE = os.path.join("C:" + os.sep, "Program Files (x86)", "Lua", "5.1", "lua.exe")

_LUA = {}


def lua(which):
    """The shipped model ("model") or panel ("ui") script, as text.

    Cached, because four readers want it now: the demo court's names, the
    sufferance threshold, the nine moves and their prices, and the panel's own
    per-view strings. Every one of them is a thing that lives in the Lua and
    nowhere else - gen_iron_court.py builds the DB and has never heard of a plot -
    so reading it is the only route that cannot drift from what ships.
    """
    if which not in _LUA:
        # THE PARTIES FILE TOO: the petitions' terms are its T.party_* values.
        name = "zzz_derpy_iron_court%s.lua" % {"ui": "_ui", "parties": "_parties",
                                                "ui_map": "_ui_map"}.get(
            which, "")
        _LUA[which] = io.open(os.path.join(LOCAL, "script", "campaign", "mod", name),
                              encoding="utf-8").read()
    return _LUA[which]


def bare(src):
    """Lua source with whole-line comments removed.

    Load-bearing rather than tidy-up: everything below hunts for quoted strings,
    and both of these files comment in prose that QUOTES the strings beside it -
    the warning row's sentence is written out in the comment above the code that
    formats it, two lines above the format string itself. A hunt that did not
    strip comments found the example and not the thing.
    """
    return "\n".join(l for l in src.split("\n") if not l.strip().startswith("--"))


def _block(src, name):
    """The body of a top-level Lua table, comment lines stripped."""
    return bare(re.search(r"%s = \{(.*?)\n\}" % re.escape(name), src, re.S).group(1))


def _sort_label(ui, view, mode=1):
    """What the sort control reads on `view`, or None if the view has none.

    Two of the five tabs sort and so does the character picker. The offices tab
    is a fixed ziggurat whose shape is the information, the governors tab is map
    order, the record is chronological and the intrigue grid is sixteen cards all
    on screen at once - a control on any of those would be a button that does
    nothing, so this returns None and the caller hides it, which is the same test
    ICUI.refresh makes.

    `mode` is which setting to show, 1-based, exactly as ICUI.sort indexes
    ICUI.SORTS - so the picture can be of a panel the player has clicked.
    """
    m = re.search(r"\n    %s = \{(.*?)\n    \}" % re.escape(view),
                  _block(ui, "ICUI.SORTS"), re.S)
    if not m:
        return None
    names = re.findall(r'name = "([^"]*)"', m.group(1))
    return names[mode - 1]


def _sortable_columns(ui, view):
    """The 1-based column numbers this view has a sort mode for.

    Read off `col =` in ICUI.SORTS rather than listed, so a mode moved to a
    different column moves its arrow in the picture too.
    """
    m = re.search(r"\n    %s = \{(.*?)\n    \}" % re.escape(view),
                  _block(ui, "ICUI.SORTS"), re.S)
    if not m:
        return set()
    return set(int(c) for c in re.findall(r"col = (\d+)", m.group(1)))


def _header_row(ui, view):
    """The five column captions this view draws, or None when it draws none."""
    base = "pick" if view.startswith("pick") else view
    if base == "pick":
        return lua_words(ui, "ICUI.PICK_HEADERS")
    m = re.search(r"\n    %s\s*=\s*\{(.*?)\}" % re.escape(base),
                  _block(ui, "ICUI.HEADERS"), re.S)
    if not m:
        return None
    return re.findall(r'"([^"]*)"', m.group(1))


def _pick_d_fmt(ui):
    """The picker's fourth cell, read off ICUI.draw_picker's own format string."""
    return re.search(r'string\.format\("(%d [a-z]+: %s)"', ui).group(1)


def lua_words(src, name):
    """The quoted strings of a flat Lua list, in order.

    Up to the FIRST closing brace, not the one at a line start, because these
    lists are written on one or two lines and hold no nested table.
    """
    return re.findall(r'"([^"]*)"',
                      re.search(r"%s = \{(.*?)\}" % re.escape(name), src, re.S).group(1))


# A MOVE, BY NAME AND NOT BY POSITION. A namedtuple still indexes, so p[0] and p[4] keep working; what it stops is
# the next field silently breaking a reader that spells the arity out.
Move = collections.namedtuple(
    "Move", "key name blurb cost aimed icon cat effect race gold",
    defaults=(None, False))


def _tune(src):
    """IC.TUNE as a {name: literal} dict, for resolving the effect lines."""
    blk = _block(src, "IC.TUNE")
    return dict(re.findall(r"(\w+)\s*=\s*(-?[\d.]+)", blk))


def _resolve_effect(expr, tune):
    """string.format("lit" .. "lit", IC.TUNE.a, ...) -> the string it produces.

    Not a Lua interpreter: it handles the one shape the moves use and RAISES on
    anything else, because a picture drawn from an unresolved "%d gold" is nine
    characters narrower than the one the panel draws and would quietly pass a
    card that clips in game.
    """
    head = expr.split(",\n")[0] if ",\n" in expr else expr
    lit = "".join(re.findall(r'"([^"]*)"', head))
    args = re.findall(r"IC\.TUNE\.(\w+)", expr)
    lit = lit.replace("%%", "\0")
    for a in args:
        if a not in tune:
            raise KeyError("IC.TUNE has no " + a)
        lit = lit.replace("%d", tune[a], 1)
    if "%d" in lit:
        raise ValueError("more %d than IC.TUNE arguments: " + lit)
    return lit.replace("\0", "%")


def read_plots():
    """One Move per entry, in IC.PLOTS' order.

    The moves live in the model Lua and nowhere else, so this is the same route
    demo_court already takes to NAME_HEADS rather than a second, typed list that
    could disagree with the tab it is drawing. A move added to the model appears
    in this picture with no edit here, which is the property ICUI.draw_intrigue
    was built for in the first place.
    """
    src = lua("model")
    out = []
    for chunk in re.split(r"\n    \{", _block(src, "IC.PLOTS"))[1:]:
        key = re.search(r'key = "(\w+)"', chunk).group(1)
        name = re.search(r'name = "([^"]+)"', chunk).group(1)
        cost_key = re.search(r'cost = "(\w+)"', chunk).group(1)
        # The price is a TUNE entry, matched at its own line start so a number
        # inside a comment cannot be read as one.
        cost = int(re.search(r"^\s+%s\s*=\s*(\d+)" % cost_key, src, re.M).group(1))
        # The blurb is the last field and is written as concatenated literals.
        blurb = "".join(re.findall(r'"([^"]*)"', chunk.split("blurb =")[1]))
        icon = re.search(r'icon = "([^"]+)"', chunk).group(1)
        cat = re.search(r'cat = "(\w+)"', chunk).group(1)
        # WHAT THE MOVE DOES, resolved. fill_plot draws effect .. " " .. blurb,
        # so drawing the blurb alone would misdraw the panel.
        effect = _resolve_effect(
            chunk[chunk.index("effect = "):chunk.index("blurb =")], _tune(src))
        # A RACE'S OWN MOVE, and one paid in gold.
        race = re.search(r'race = "(\w+)"', chunk)
        out.append(Move(key, name, blurb, cost, "aimed = false" not in chunk,
                        icon, cat, effect, race.group(1) if race else None,
                        "gold = true" in chunk))
    return out


def plot_cats():
    """(key, display name) per column, out of IC.PLOT_CATS."""
    src = lua("model")
    blk = src[src.index("IC.PLOT_CATS = {"):]
    blk = blk[:blk.index(chr(10) + "}")]
    return re.findall(r'key\s*=\s*"(\w+)"\s*,\s*name\s*=\s*"([^"]+)"', blk)


def _gen(_cache=[]):
    """The generator module, loaded once.

    CACHED because it is now read at module level too - GAME_FONT_WIDER comes
    from it - and module_from_spec builds a NEW module every call, so an
    uncached second call re-executes the whole generator and hands back a
    different object with different layout tables. One copy, or the picture and
    the numbers can disagree about which build they are describing.
    """
    if _cache:
        return _cache[0]
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "gen_ic_ui", os.path.join(ROOT, "tools", "gen_ic_ui.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("gen_ic_ui", mod)
    spec.loader.exec_module(mod)
    _cache.append(mod)
    return mod


# THE THREE BOX WIDTHS the court and intrigue shapes are drawn at: the small
# end, the design size and the cap. 1600 draws from the compact files, one font
# size down, because that is what a small screen opens.
SIZES = (1600, 1920, 2560)


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


def sized(path, bw):
    """ic_court.png at 1920, ic_court_1600.png at 1600 - the 1920 names stay
    what every existing reference already points at."""
    if bw == 1920:
        return path
    stem, ext = os.path.splitext(path)
    return "%s_%d%s" % (stem, bw, ext)


def validate():
    problems = PG.validate(PREFIX)
    # THE COMPACT COPIES MUST BE THERE TO BE VALIDATED: the reader checks what
    # is on disk, and a small screen opens a file this would otherwise never see.
    ours = set(os.path.basename(p) for p in PG.our_files(PREFIX))
    for name in sorted(_gen().COMPACT_FILES.values()):
        if name not in ours:
            problems.append("%s is not on disk - run tools/gen_ic_ui.py" % name)
    return problems


# THE WORST COURT THE MODEL CAN ROLL, not a comfortable one. A real court's
# names are ROLLED out of IC.NAME_HEADS and IC.NAME_TAILS ("The League of the
# Ninth Furnace"), and an easier demo hides the case the card's two-line name
# exists for.
#
# So the court is derived: the Crown plus the LARGEST rivals_max in the model
# (Ruthless's five, the most the roller ever seats, which fills the grid), each
# wearing the LONGEST name its own tail list can produce, and the Crown wearing
# a faction display name, which this mod does not write and cannot bound.
# One loyalty in each mood band: the plate is the only cell whose text turns on a
# threshold, so a demo where they all read LOYAL never draws the other two.
DEMO_LOYALTY = (100, 57, 52, 21, 54, 38)
DEMO_LEADERS = ("Drazkarh Hackhand", "Amarudz Grimtidesson", None,
                "Mulagunnar Growlish", "Dazminus Deathdealer", "Zhargul Ashbeard")
DEMO_LTRAITS = ("Schemer", "Shrewd", "", "Steady", "Steady", "Shrewd")
# The longest Chaos Dwarf faction name on the map, for the Crown's card.
DEMO_CROWN_NAME = "Slaves of the Black Dwarf"

# WHAT EACH CARD'S STATE WORD SAYS. ICUI.card_mood puts a demand, a feud and an
# offer ahead of the loyalty band, so the demo court carries one demand and two
# offers - the same three the Petitions picture lists - and one party plotting,
# which is a word the card draws RED. The Crown reads its band.
DEMO_STATE = ("LOYAL", "DEMANDING", "OFFERING", "PLOTTING", "OFFERING", "RESTLESS")
# Loyalty a turn, per card: rising, falling, flat, and the steepest fall.
DEMO_TREND = (1, -2, 0, -4, 3, -1)
# THE CARD THE DEMO HAS CHOSEN. A rival, so the action bar draws its three
# buttons rather than the hint - the hint is one line of text, the bar is what
# the change is for.
DEMO_SEL = 1


LawCell = collections.namedtuple("LawCell", "vis x y w h text images")


def law_dump(_cache={}):
    """{screen: {component path: LawCell}} for "law_board" and "law_vote".

    DRAWN BY THE SHIPPED LUA, not restated here. The harness's IC_DUMP block
    builds the demo court, runs ICUI.refresh on its fake tree for each screen
    and writes every component's visibility, box, text and image slots; this
    runs it and reads the file back. The vote screen's every figure is the
    model's tally - a Python copy of IC.law_tally could only say what this file
    believes the Lua does. The text is the 1920 draw's at every width: the Lua's
    cuts measure with the harness's linear stub, not the engine's face, so the
    picture shows the string and lets it overflow if it does.

    The loc it reads is the generator's own rows plus the demo's names and
    faces, handed over as a Lua file.
    """
    if _cache:
        return _cache
    import subprocess
    import tempfile
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import gen_iron_court as GIC
    loc = dict((r["key"], r["text"]) for r in GIC.build()["loc"])
    # THE LONGEST FORENAMES FIRST: the man cell holds a first name and his
    # influence, and the first block drawn is the heaviest.
    # Longest first, then by name: a tie left in set order made the law vote's
    # picture differ run to run (Python seeds its string hash per process).
    fores = sorted(set(r[0].split()[0] for r in DEMO_PICK), key=lambda s: (-len(s), s))
    for i in range(1, 41):
        loc["derpy_demo_fore_%d" % i] = fores[(i - 1) % len(fores)]
        loc["derpy_demo_face_%d" % i] = DEMO_FACES[(i - 1) % len(DEMO_FACES)]
    loc["derpy_demo_crown"] = DEMO_CROWN_NAME

    def q(v):
        return '"%s"' % v.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    tmp = tempfile.mkdtemp(prefix="ic_law_dump_")
    loc_path, out_path = os.path.join(tmp, "loc.lua"), os.path.join(tmp, "dump.tsv")
    with io.open(loc_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("return {\n" + "".join("[%s] = %s,\n" % (q(k), q(v))
                                       for k, v in sorted(loc.items())) + "}\n")
    env = dict(os.environ, IC_ONLY="no check is named this", IC_DUMP=out_path, IC_DUMP_LOC=loc_path)
    env.pop("IC_TEST_ALL", None)
    r = subprocess.run([LUA_EXE, os.path.join("tools", "_iron_court_harness.lua")],
                       cwd=ROOT, env=env, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.isfile(out_path):
        raise SystemExit("the harness's law dump failed:\n" + r.stdout + r.stderr)

    def unesc(t):
        return re.sub(r"\\(.)", lambda m: {"t": "\t", "n": "\n"}.get(m.group(1), m.group(1)), t)
    for line in io.open(out_path, encoding="utf-8").read().split("\n"):
        if not line:
            continue
        screen, path, vis, x, y, w, h, text, imgs = line.split("\t")
        images = {}
        for pair in unesc(imgs).split("|"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                images[int(k)] = v.replace("\\", "/")
        _cache.setdefault(screen, {})[path] = LawCell(
            vis == "1", float(x), float(y), float(w), float(h), unesc(text), images)
    return _cache



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
    # THE BOOK'S HARD CASE: CA's three longest faction
    # screen names, met and weighed by the dump's court - a picture of three short
    # names answers nothing about a cut cell.
    book = sorted(((k[len("factions_screen_name_"):], t) for k, t in names.items()
                   if k.startswith("factions_screen_name_")
                   and not k.startswith("factions_screen_name_when_rebels_")
                   and not t.startswith("{{")), key=lambda kt: (-len(kt[1]), kt[0]))[:3]
    for key, text in book:
        loc["factions_screen_name_" + key] = text
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
               IC_DUMP_BOOK=",".join(k for k, _t in book),
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

def demo_court(G):
    """(slug, title, share, loyalty, leader, his trait) per card.

    NAME_HEADS, NAME_TAILS and rivals_max live in the model Lua, not in the
    Python generator, so they are read from there.
    """
    src = lua("model")
    heads = re.findall(r'"([^"]+)"',
                       re.search(r"IC\.NAME_HEADS = \{(.*?)\}", src, re.S).group(1))
    block = re.search(r"IC\.NAME_TAILS = \{(.*?)\n\}", src, re.S).group(1)
    tails = dict((m.group(1), re.findall(r'"([^"]+)"', m.group(2)))
                 for m in re.finditer(r"(\w+)\s*=\s*\{(.*?)\}", block, re.S))
    # THE LONGEST NAME THE MODEL CAN ROLL, in IC.party_name's one shape.
    def longest_name(slug):
        return max(("%s of %s" % (h, t) for h in heads for t in tails[slug]),
                   key=len)

    # THE LARGEST, not the first: the first rivals_max in the file is Default's.
    rivals = max(int(v) for v in re.findall(r"rivals_max\s*=\s*(\d+)", src))

    slugs = [p[0] for p in G.IC.PARTIES][:rivals + 1]
    share = 100 // len(slugs)
    out = []
    for i, slug in enumerate(slugs):
        title = (DEMO_CROWN_NAME if slug == G.IC.CROWN
                 else longest_name(slug))
        out.append((slug, title, share, DEMO_LOYALTY[i], DEMO_LEADERS[i],
                    DEMO_LTRAITS[i]))
    return out


DEMO_TRAITS = {
    "crown":  ("Ancient Right", "Hard Bargainers"),
    "temple": ("Zealots", "Slave-Hungry"),
    "forge":  ("Well Armed", "Jealous of the Hammer"),
    "chain":  ("Cruel Overseers", "Feared"),
    "legion": ("Veterans", "Costly"),
    "ledger": ("Deep Coffers", "Venal"),
    "tower":  ("Patient", "Secretive"),
    "road":   ("Swift", "Few"),
    "hearth": ("Well Fed", "Homebound"),
}
# THE LIT TAB'S PLATE. ICUI.light_tabs swaps the tab's image slots rather than
# recolouring its text, and the selected art is named only in the Lua - it appears
# in no .twui.xml, so the extractor has to be told about it or the lit tab draws
# exactly like the four unlit ones.
TAB_SELECTED = "ui/derpy_ic/chd_tab_selected.png"

# HOW MUCH WIDER THE GAME'S FACE IS THAN PIL'S, measured off a screenshot of the
# shipped panel rather than guessed. The game split "The League of the Ninth
# Furnace" after "Ninth" in the 280px name cell, so in game that whole string is
# over 280 and "The League of the Ninth" is under it. PIL at the same nominal 14px
# calls them 210 and 155, which brackets the ratio between 1.33 and 1.80.
#
# The LOW end is used, so the preview errs towards showing two lines where the game
# might manage one - a preview that draws a name on one line when the panel draws
# two is showing a layout that never happens.
#
# ponytail: one ratio for one font at one size, measured from a single screenshot.
# The real fix is the engine's TextDimensionsForText, which only runs in game -
# gen_ic_ui.py check 20g already asks it, and that check owns the fit question.
# THE GENERATOR'S NUMBER, not a second copy of it. This file draws with Segoe UI
# Black, the face gen_ic_ui measures with, so the factor is expressed against
# that face; a figure taken against PIL's default face would double-count.
GAME_FONT_WIDER = _gen().GAME_FONT_WIDER

# CA portholes, so the faces are real art at the real aspect rather than grey boxes.
DEMO_FACES = [
    "ui/portraits/portholes/no_culture/chd_astragoth_ironhand_0.png",
    "ui/portraits/portholes/no_culture/chd_daemonsmith_sorcerer_campaign_01_0.png",
    "ui/portraits/portholes/no_culture/chd_daemonsmith_sorcerer_campaign_02_0.png",
    "ui/portraits/portholes/no_culture/chd_daemonsmith_sorcerer_campaign_03_0.png",
    "ui/portraits/portholes/no_culture/chd_daemonsmith_sorcerer_campaign_04_0.png",
    "ui/portraits/portholes/no_culture/chd_daemonsmith_sorcerer_campaign_05_0.png",
    "ui/portraits/portholes/no_culture/chd_bull_centaur_taurruk_campaign_01_0.png",
    "ui/portraits/portholes/no_culture/chd_bull_centaur_taurruk_campaign_02_0.png",
    "ui/portraits/portholes/no_culture/chd_bull_centaur_taurruk_campaign_03_0.png",
]


# CA'S OWN RED, read out of db/ui_colours_tables rather than picked by eye. The
# [[col:<name>]] tag resolves against that table - 163 rows - and its `red` row is
# FF2D2D, described "Negative. Generic colour used by UI for text tags, fonts,
# images, etc." A preview that invented a red would be guessing at the single
# thing the red rows exist to show. selftest() re-reads the cached table and
# fails if CA ever moves it.
RED_INK = (0xFF, 0x2D, 0x2D, 255)
# THE NAMED INKS the panel writes through [[col:]]: CA's red for a refusal, and black
# for a lit Dwarf tab's word on the gold ribbon (db/ui_colours_tables, 000000).
INK_OF = {"red": RED_INK, "black": (0, 0, 0, 255)}

# [[col:name]] ... [[/col]] and [[img:path]][[/img]], the two markups this panel
# writes through SetText.
MARKUP = re.compile(r"\[\[(/?)(col|img)(?::([^\]]*))?\]\]")


class _PlainMetrics(dict):
    """Image metrics for an inline icon: no 9-slice, no tile, no tint.

    rendering.raster keys its cache on metrics.attrs, so a bare dict will not do -
    and an icon has no appearance to vary, so one empty attrs for all of them is
    the right cache key rather than a shortcut.
    """
    attrs = {}


def segments(s):
    """(kind, body, colour) pieces of a string carrying twui markup.

    THE TAGS ARE NOT TEXT. Both of these reach the panel through SetText, which is
    how every price and every refusal in this mod is written, so a preview that
    printed "[[img:ui/skins/default/icon_secure_loyalty.png]][[/img]]180" would be
    showing a string no player ever sees.

    An unknown colour name is dropped SILENTLY by the engine, leaving ordinary
    ink, so an unrecognised name here leaves the cell's own colour too.
    """
    out, colour, at = [], None, 0
    for m in MARKUP.finditer(s):
        if m.start() > at:
            out.append(("text", s[at:m.start()], colour))
        at = m.end()
        if m.group(2) == "col":
            colour = None if m.group(1) else m.group(3)
        elif not m.group(1):
            out.append(("img", m.group(3), colour))
    if at < len(s):
        out.append(("text", s[at:], colour))
    return out


# WHAT THE DEMO COURT CAN AFFORD, and it is two numbers rather than one because
# ICUI.draw_intrigue reads two: a plot is paid for by the richest courtier there
# is, an errand by the richest who is not commanding an army. A court whose one
# rich man is in the field can buy a knife and not a feast, and a single purse
# could not draw that.
#
# Chosen to straddle the price list rather than to be comfortable: a column that
# draws all red, or none, says nothing. Re-pick them when the prices move.
# 155 and 105 are each about the middle of their own list, so both columns draw
# roughly half affordable and half refused:
#
#   aimed   80 90 120 130 140 150 | 160 180 200 220 250 400     6 of 12 refused
#   errand  60 100 | 110 140                                    2 of 4  refused
#
# STILL LITERALS, DELIBERATELY. Deriving them from the price list - the median,
# say - would make the straddle assertion in selftest() true by construction,
# and a check that cannot fail is the thing this file exists to avoid. A literal
# that a check constrains is worth more than a formula that checks itself.
DEMO_PURSE, DEMO_PURSE_CIVIL = 155, 105


def red(s):
    """ICUI.red: wraps, so a price keeps the icon inside it."""
    return "[[col:red]]%s[[/col]]" % s


def intrigue_lines(G, court):
    """The intrigue tab's WARNINGS, in ICUI.draw_intrigue's order and shape.

    NOT ROWS, despite the name. The tab is four columns of cards and
    ICUI.rows_shown("intrigue") is 0; what these feed is the alert bar, which
    takes the most urgent sentence and a count of the rest. The moves are
    plot_cards().

    Both warning sentences are lifted out of the panel Lua rather than retyped.
    Lua's string.format and Python's % take the same %s and %d, so the format
    string can be used exactly as it is found.
    """
    ui = bare(lua("ui"))
    clock_fmt = re.search(r'"([^"]*breaks with you in[^"]*)"', ui).group(1)
    snub_fmt = re.search(r'"([^"]*is insulted:[^"]*)"', ui).group(1)
    cost_icon = re.search(r'ICUI\.COST_ICON = "([^"]+)"', ui).group(1)

    lines = []
    # Two clocks and a snub: one plural, one singular, and the pressure that comes
    # before a clock starts. The Crown is never among them - it is the player.
    lines.append(["", clock_fmt % (court[1][1], 2, "s"), "", "", ""])
    lines.append(["", clock_fmt % (court[2][1], 1, ""), "", "", ""])
    lines.append(["", snub_fmt % (court[3][1], G.IC.OFFICES[0]["name"]), "", "", ""])

    # The moves are a grid of cards below this band, drawn by plot_cards(); the
    # row pool carries only the warnings on this tab.
    return lines


# A DRAWN MOVE CARD, a namedtuple for the same reason Move is.
Card = collections.namedtuple("Card", "name blurb price afford icon cat")


def plot_cards(G, race="chd"):
    """One Card per move of this race's grid, in ICUI.draw_intrigue's order.

    The same read_plots() source as before - a move added to the model draws here
    with no edit - split into the four cells a card has rather than concatenated
    into one widened column. A gold move (the weregild) is priced with the
    treasury's icon; the demo court's treasury is not modelled, so it draws
    affordable.
    """
    ui = bare(lua("ui"))
    cost_icon = re.search(r'ICUI\.COST_ICON = "([^"]+)"', ui).group(1)
    gold_icon = re.search(r'ICUI\.GOLD_ICON = "([^"]+)"', ui).group(1)
    out = []
    for p in read_plots():
        if p.race and p.race != race:
            continue
        purse = DEMO_PURSE if p.aimed else DEMO_PURSE_CIVIL
        afford = p.gold or purse >= p.cost
        price = "[[img:%s]][[/img]]%d" % (gold_icon if p.gold else cost_icon, p.cost)
        # THE SAME CONCATENATION fill_plot makes, in the same order: what the
        # move does first, what it feels like second.
        out.append(Card(p.name, p.effect + " " + p.blurb,
                        price if afford else red(price), afford,
                        p.icon, p.cat))
    return out


def _party_tune():
    """The parties file's T.party_* values, {name: int}."""
    return dict((k, int(v)) for k, v in re.findall(
        r"^T\.(\w+)\s*=\s*(-?\d+)", lua("parties"), re.M))


def petitions_label():
    """ICUI.petitions_label, resolved: its literals, then its three T values."""
    body = lua("ui").split("function ICUI.petitions_label()")[1].split("\nend")[0]
    lit = "".join(re.findall(r'"([^"]*)"', body.split(", IC.TUNE.")[0]))
    tune = _party_tune()
    for name in re.findall(r"IC\.TUNE\.(\w+)", body):
        lit = lit.replace("%d", str(tune[name]), 1)
    if "%" in lit:
        raise ValueError("petitions_label did not resolve: " + lit)
    return lit


# THE LONGEST NAME CA GIVES A CHAOS DWARF and the longest province name the game
# ships - the pair the demand row was measured against and rearranged for.
DEMO_LONG_MAN = "Drazhoath the Ashen of Hashut"
DEMO_LONG_PROVINCE = "Southlands World's Edge Mountains"


def petition_rows(G, court):
    """ICUI.draw_petitions' rows for the demo court: the demand, then the offers.

    THE HARD CASE: the demand is the longest man for the longest province, and
    the first offer calms the party with the longest name. The last offer is
    refused - a troop offer to a court with no army to take it - so the red
    ACCEPT is on the picture. The formats are lifted out of the Lua.
    """
    ui = bare(lua("ui"))
    tune = _party_tune()
    body = ui.split("function ICUI.draw_petitions(")[1].split("\nend")[0]
    oversee = re.search(r'"(Demands to oversee %s)"', body).group(1)
    offers = re.search('"(Offers %s: %s)"', body).group(1)
    what = ui.split("function ICUI.offer_what(")[1].split("\nend")[0]
    calm = re.search(r'"(calm %s \(\+%d loyalty\))"', what).group(1)
    troops = re.search(r'if row then return string\.format\("(%d %s)"', what).group(1)

    def turns(n):
        return "%d turn%s" % (n, "" if n == 1 else "s")

    longest = max(court[1:], key=lambda row: len(row[1]))
    rows = [dict(slug=court[1][0], face=DEMO_FACES[1], may=True, a=DEMO_LONG_MAN,
                 b="%s - %s" % (oversee % DEMO_LONG_PROVINCE,
                                turns(tune["party_demand_turns"])))]
    rows.append(dict(slug=court[2][0], face=None, may=True, a=court[2][1],
                     b=offers % (calm % (longest[1], tune["party_offer_calm"]),
                                 turns(tune["party_offer_turns"]))))
    rows.append(dict(slug=court[4][0], face=None, may=False, a=court[4][1],
                     b=offers % (troops % (tune["party_offer_units"],
                                           "Chaos Dwarf Warriors (Great Weapons)"),
                                 turns(1))))
    return rows


def slice_counts(total, court):
    """Largest remainder, so the parts sum to exactly `total` and none is dropped.

    NOT ICUI.bar_widths. That one guarantees a slice to a party too small to earn one and
    takes it off the largest; this is the preview's own arithmetic and is only here to put
    a believable pie on the picture. The Lua's version is checked by the harness.
    """
    raw = [(row[2] * total) / 100.0 for row in court]
    out = [int(r) for r in raw]
    order = sorted(range(len(raw)), key=lambda i: raw[i] - out[i], reverse=True)
    for i in order[:total - sum(out)]:
        out[i] += 1
    return out


def _asset(path):
    """A file on disk for an in-pack path: this mod's own art first, then the cache.

    A pathlib.Path, because TWUI Studio's rasteriser stats what it is handed.
    """
    from pathlib import Path
    if not path:
        return None
    own = os.path.join(LOCAL, path.replace("/", os.sep))
    if os.path.isfile(own):
        return Path(own)
    cached = os.path.join(PG.UI, os.path.relpath(path, "ui").replace("/", os.sep))
    return Path(cached) if os.path.isfile(cached) else None


# The demo roster for the picker.
#
# TWELVE MEN, WHICH IS EXACTLY ICUI.MAX_ROWS, so the pool is full and the picture
# is of a screen a player actually has to read rather than four rows with white
# space under them. Twelve also keeps the pager out of it, the same way both
# other shapes do - ICUI.draw_pager hides all three of its cells whenever the
# list fits one page.
#
# THE REFUSALS ARE SCATTERED THROUGH IT, not grouped, because that is what an
# engine-ordered list looks like and it is the whole reason the AVAILABLE setting
# exists. Each row is (name, trade, party slug, rank, standing, what he holds,
# the refusal or None) and an empty `holds` draws "None", which is what
# ICUI.draw_picker writes rather than leaving the cell blank.
#
# EVERY SLUG IS ONE THE DEMO COURT SEATS. A man belongs to a party that is at
# court, and using the same five keeps the crests and the party names coming out
# of demo_court rather than out of a second copy of the name roll.
#
# THE LAST FIELD IS AN INDEX INTO ICUI.KIND_NAME, not a word: the panel owns the
# four words and _kind_words reads them, so a renamed kind reaches the picture.
#
# ALL FOUR APPEAR, and they are MIXED THROUGH the list rather than grouped. The
# question this picture has to answer is whether a name with a position name in
# front of it still reads at a glance and still fits its column, and the answer
# depends on which word it is - "Retainer Amarudz Grimtidesson - Shrewd" is the
# long end and "Lord Vraznak Dreadhorn - Bull" the short one, so a demo missing
# a kind is a demo that has not asked the question.
DEMO_PICK = (
    ("Drazkarh Hackhand",    "Schemer",     0, 4, 210, "", None, 1),
    ("Ghorzag Ironjaw",      "Slaver",      3, 2,  40, "", "Rank 3", 0),
    ("Amarudz Grimtidesson", "Shrewd",      2, 5, 380, "Master of the Anvil",
     "Busy", 2),
    ("Zhatan Blacksoul",     "Veteran",     4, 6, 140, "", None, 0),
    ("Mulagunnar Growlish",  "Steady",      1, 3,  55, "", "Short 45", 1),
    ("Dazminus Deathdealer", "Zealot",      1, 4, 190, "", None, 2),
    ("Rykarth Ashencrown",   "Overseer",    3, 1,  20, "", "Rank 3", 1),
    ("Khazrak Emberhand",    "Engineer",    2, 3, 260, "", None, 3),
    ("Uzkhar Slagbeard",     "Taskmaster",  4, 2,  95, "Ostmark", "Busy", 0),
    ("Thagrosh Coalgut",     "Daemonsmith", 2, 5, 150, "", None, 3),
    ("Vraznak Dreadhorn",    "Bull",        4, 4,  70, "", "Short 30", 0),
    ("Astragoth Ironhand",   "Hierarch",    1, 6, 420, "", None, 1),
)


# THE PROVINCES THE DEMO GOVERNORS LIST HOLDS.
#
# (name, overseer or None, house, away, loyalty). Six of them, and the mix is
# the point rather than the count: a province with an overseer standing in it, a
# province whose overseer has marched off, three houses so the crest column has
# something to say (the row has no party column), and two provinces with
# nobody at all, the row this tab exists to flag.
#
# THE LOYALTIES STRADDLE THE MOOD BANDS on purpose. A list where every number is
# comfortable says nothing about whether the column reads at a glance, which is
# the one question a picture can answer and a check cannot.
DEMO_GOVS = (
    ("Zharr Naggrund",    "Astragoth Ironhand",  "crown",  False, 88),
    ("Gash Kadrak",       "Khazrak Emberhand",   "forge",  True,  41),
    ("The Howling Wastes", None,                 None,     False, 55),
    ("Uzkulak",           "Thagrosh Coalgut",    "ledger", False, 12),
    ("Plain of Zharr",    None,                  None,     False, 63),
    ("Black Fortress",    "Uzkhar Slagbeard",    "forge",  False, 70),
)


# WHICH SEATS THE DEMO COURT HAS FILLED, by index into IC.OFFICES, and what
# each holder is worth: (overseer, house, influence, turns left).
#
# SEVEN OF FOURTEEN. A card the player will spend most of the campaign looking at
# is a card with nobody on it, so half the grid is empty on purpose - and the
# seven that are taken are spread over all four bands, because the top band's
# cards are the ones whose text is longest and the bottom band's the ones that
# clip first.
#
# A TERM RUNNING OUT AND A TERM ON ITS LAST TURN are both here: the card says
# "1 turn left" rather than "1 turns left" and that singular has exactly one
# place it can be seen.
DEMO_OFFICES = {
    0:  ("Astragoth Ironhand",  "crown",  420, 7),
    1:  ("Khazrak Emberhand",   "forge",  260, 1),
    3:  ("Thagrosh Coalgut",    "ledger", 150, 4),
    5:  ("Drazkarh Hackhand",   "crown",  210, 12),
    8:  ("Zhatan Blacksoul",    "tower",  140, 3),
    10: ("Uzkhar Slagbeard",    "forge",   95, 9),
    12: ("Dazminus Deathdealer", "temple", 190, 2),
}


def DEMO_SEAT(G):
    """The seat the demo picker is filling.

    A TIER-2 OFFICE, off the generator's own table rather than named here: high
    enough that its bar refuses somebody - a picture of a list where every row
    reads CHOOSE shows neither the red refusals nor the reason the AVAILABLE
    setting exists - and not the apex, which only two men in a campaign can ever
    reach.
    """
    for office in G.IC.OFFICES:
        if office["tier"] == 2:
            return office
    return G.IC.OFFICES[0]


def cut_words(width_of, s, cw):
    """ICUI.fit_cut's shape: whole words, then an ellipsis.

    MIRRORED, NOT SHARED. The panel asks the ENGINE for the real width and this
    asks PIL, which is the same stand-in fit_two uses here and is OPTIMISTIC -
    a string that just fits in the picture may still be cut on screen. The
    mirror catches the opposite error: a cell drawn with no cut at all, straight
    out through the side of its card.

    ONE FUNCTION FOR TWO CALLERS, the offices card's two unmeasurable cells and
    the picker's first cell, so the two cannot drift.
    """
    s = s or ""
    if not s or width_of(s) <= cw:
        return s
    words = s.split()
    kept = 0
    for i in range(1, len(words) + 1):
        if width_of(" ".join(words[:i]) + "...") > cw:
            break
        kept = i
    return (" ".join(words[:kept]) + "...") if kept else ""


def _kind_words(ui):
    """ICUI.KIND_NAME's three words, in the panel's own order of declaration.

    Read rather than typed for the usual reason - a renamed kind reaches the
    picture - and it is the reason the demo roster below carries an INDEX into
    this list rather than a word of its own.
    """
    m = re.search(r"ICUI\.KIND_NAME = \{([^}]*)\}", ui)
    if not m:
        return []
    return [w for _k, w in re.findall(r'(\w+) = "([^"]+)"', m.group(1))]


def pick_lines(ready_first):
    """The twelve rows in the order the picker would draw them.

    `ready_first` is ICUI.sort_picker's AVAILABLE rule MIRRORED IN PYTHON:
    choosable men first, then most standing, then the name. A mirror and not a
    shared implementation, on purpose - this file draws pictures, and what proves
    the Lua is the harness, which carries two checks and five mutants aimed at
    exactly this ordering. A picture cannot assert.
    """
    rows = list(DEMO_PICK)
    if ready_first:
        rows.sort(key=lambda r: (r[6] is not None, -r[4], r[0]))
    return rows


def gm_hidden(G, view, n_rows):
    """The ic_gm_ cells this picture leaves undrawn, as the Lua leaves them.

    Off the Governors view, all of them (ICUI.gm_show_column). On it: the footer's
    plate, which shows with the footer line and the demo has none; the hint,
    which the Provinces page hides and the picker shows only for an empty list;
    and the sort on a picker with nobody in it, where the hint takes its place.
    The list's slider is not a PANEL_LAYOUT cell and is not drawn here.
    """
    gm = set(n for n in G.PANEL_LAYOUT if n.startswith("ic_gm_"))
    if view not in ("gm_provinces", "gm_picker"):
        return gm
    out = {"ic_gm_foot", "ic_gm_hint"}
    if view == "gm_picker" and n_rows == 0:
        out |= {"ic_gm_sort_1", "ic_gm_sort_2", "ic_gm_sort_3"}
    return out


# THE PROVINCES PAGE'S DEMO: DEMO_GOVS, plus the worst row the page can be
# handed - the longest province, governed by a long name who is away - and the
# settlement levels each province holds, so "+N weight" is the model's figure.
GM_DEMO_LEVELS = (9, 4, 0, 6, 2, 5, 3)


def gm_province_rows():
    return list(DEMO_GOVS) + [(DEMO_LONG_PROVINCE, "Dazminus Deathdealer", "temple", True, 25)]


def render(path=None, view="court", box_w=1920, race="chd"):
    from PIL import Image, ImageDraw, ImageFont
    model, rendering = PG._studio()
    G = _gen_at(box_w, race)
    ui = lua("ui")
    gm = view.startswith("gm_")
    # THE COST ICON IS NAMED IN THE LUA AND IN NO .twui.xml, so the extractor has
    # to be told about it the way it is told about the lit tab's plate - otherwise
    # every price on the intrigue tab draws its number and no icon.
    cost_icon = re.search(r'ICUI\.COST_ICON = "([^"]+)"', ui).group(1)
    gold_icon = re.search(r'ICUI\.GOLD_ICON = "([^"]+)"', ui).group(1)
    # THE MOVE ICONS ARE CA'S OWN, set at runtime and so named nowhere in our
    # .twui.xml - extract_art reads imagepath attributes, which never mention
    # them. They come out of IC.PLOTS here, the same place the panel reads them.
    icons = [p.icon for p in read_plots()]
    # AND THE TRAIT CELLS' EFFECT ICON, read out of the panel Lua the same way
    # and for the same reason. Its declaration wraps onto its own line, which is
    # why the newline is in the pattern.
    trait_icon = re.search(r'ICUI\.TRAIT_ICON\s*=\s*"([^"]+)"',
                           ui).group(1)
    # AND THE CROWN BLOCK'S LINE ICONS, the band's and each
    # effect's, named only in the Lua for the same reason.
    band_icon = re.search(r'ICUI\.BAND_ICON\s*=\s*"([^"]+)"', ui).group(1)
    # AND EACH GOVERNMENT'S PICTURE, out of IC.GOVS the way the
    # generator reads it for the bundles.
    gov_icons = {k: "ui/campaign ui/effect_bundles/" + v
                 for k, v in G.IC.model_gov_icons().items()}
    longest_gov = max(G.IC.GOVERNMENTS, key=lambda g: len(g[1]))
    fx_icons = dict(re.findall(r'\["([^"]+)"\]\s*=\s*"([^"]+)"',
                               _block(ui, "ICUI.FX_ICONS")))
    # THE LAWS TAB'S PICTURES are whatever its draw set, read off the dump.
    law = view.startswith("law_") or view == "gov_cards"
    LD = law_dump()[view] if law else {}
    law_art = sorted(set(p for c in LD.values() for p in c.images.values()
                         if p and p.startswith("ui/")))
    # AND THE CHOSEN CARD'S FRAME, which is CA art named only in the Lua and
    # the generator's layer list - never an imagepath in a .twui.xml.
    n_art, missing = PG.extract_art(
        PREFIX,
        extra=DEMO_FACES + [TAB_SELECTED, cost_icon, gold_icon, trait_icon, G.PARTY_SELECTED,
                            band_icon] + sorted(fx_icons.values())
        + sorted(gov_icons.values())
        + law_art
        + icons
        + [G.GM_ROW_ART % s for s in ("active", "hover", "selected", "selected_hover", "inactive")]
        + [G.GM_ROUND % s for s in ("active", "hover", "selected", "selected_hover")]
        + re.findall(r'"(ui/skins/default/icon_fealty_\w+\.png)"', lua("ui_map"))
        + (sorted(set(p for nodes in race_dump(race).values() for nd in nodes
                      for p in list(nd.images.values())
                      # A PICTURE IN THE TEXT: the government line's [[img:]] is the
                      # race's own icon, which no Chaos Dwarf list above holds.
                      + re.findall(r"\[\[img:([^\]]+)\]\]", nd.text)
                      if p.startswith("ui/"))) if race != "chd" else []))

    def doc_of(name):
        # BELOW 1920 THE PANEL OPENS THE COMPACT COPY, and the fonts this
        # reads off each cell are the compact ones.
        if box_w < 1920:
            name = G.COMPACT_FILES.get(name, name)
        return model.Document(io.open(os.path.join(PG.OURS, name),
                                      encoding="utf-8").read())

    panel, party = doc_of(G.PANEL_FILE), doc_of("derpy_ic_party.twui.xml")
    row_doc = doc_of("derpy_ic_row.twui.xml")
    office_doc = doc_of("derpy_ic_card.twui.xml")
    # THE MOVE CARDS ARE INSTANCES OF THE OFFICE CARD, so the intrigue view needs
    # that file even though the offices tab is not one of the shapes drawn here.
    card_doc = doc_of("derpy_ic_plot.twui.xml")
    gm_pin_doc, gm_face_doc = doc_of(G.GM_PIN_FILE), doc_of(G.GM_FACE_FILE)
    gm_name_doc, gm_loyal_doc = doc_of(G.GM_NAME_FILE), doc_of(G.GM_LOYAL_FILE)
    gm_badge_doc, gm_row_doc = doc_of(G.GM_BADGE_FILE), doc_of(G.GM_ROW_FILE)
    law_doc, lb_doc = doc_of("derpy_ic_law.twui.xml"), doc_of("derpy_ic_lawblock.twui.xml")
    named = {}
    for d, tag in ((panel, "panel"), (party, "party"), (row_doc, "row"),
                   (card_doc, "card"), (office_doc, "office"),
                   (gm_pin_doc, "gmpin"), (gm_face_doc, "gmface"), (gm_name_doc, "gmname"),
                   (gm_loyal_doc, "gmloyal"), (gm_badge_doc, "gmbadge"), (gm_row_doc, "gmrow"),
                   (law_doc, "law"), (lb_doc, "lawblock")):
        for c in d.components:
            named[(tag, c.get("id", c.tag))] = c

    canvas = Image.new("RGBA", (G.PANEL_W, G.PANEL_H), GM_MAP_FILL if gm else (0, 0, 0, 255))

    def paste(doc, comp, x, y, w=None, h=None, repaint=None):
        """One component's art, at absolute panel coordinates.

        `repaint` is what the Lua's SetImagePath does at draw time, keyed by IMAGE SLOT -
        the second argument to SetImagePath, which is the order of the <componentimages>
        children. A slot mapped to None is left undrawn, which is how set_face's hidden
        branch and set_plate's crown-only mask read on a card.
        """
        if comp is None:
            return
        slots, images = [], {}
        box = comp.child("componentimages")
        if box is not None:
            for n in box.children:
                if n.get("this"):
                    slots.append(n.get("this"))
                    images[n.get("this")] = n.get("imagepath")
        if repaint:
            for i, new in repaint.items():
                if i < len(slots):
                    images[slots[i]] = new
        st = doc.state(comp)
        metrics = st.child("imagemetrics") if st is not None else None
        if metrics is None:
            return
        for n in metrics.children:
            p = images.get(n.get("componentimage"))
            asset = _asset(p)
            if not asset:
                continue
            iw = int(model.number(n.get("width"), w or 0)) or (w or 1)
            ih = int(model.number(n.get("height"), h or 0)) or (h or 1)
            # A LAYER KEEPS ITS OWN SIZE AGAINST ITS COMPONENT'S. Forcing every
            # layer to the cell drew the portrait frame - 2*FRAME_OUT wider than
            # its cell, pushed out by FRAME_OUT - at the cell's size and 2px up
            # and left, with the face poking out of its other two sides.
            cw = model.number(st.get("width"), 0)
            ch = model.number(st.get("height"), 0)
            if w:
                iw = w + (iw - int(cw) if cw else 0)
            if h:
                ih = h + (ih - int(ch) if ch else 0)
            ox, oy = model.pair(n.get("offset"), (0, 0))
            canvas.alpha_composite(rendering.raster(asset, iw, ih, n),
                                   (int(x + ox), int(y + oy)))

    draw = ImageDraw.Draw(canvas)
    fonts = {}

    # THE SAME FACE gen_ic_ui MEASURES WITH, and not PIL's default.
    #
    # The default is a wide bitmap face that breaks lines where the engine will
    # not (five of sixteen move blurbs cut mid-sentence), while the generator's
    # check measures with Segoe UI Black, the heaviest desktop face on the
    # machine and the conservative proxy. A preview that disagrees with the check
    # about where a line ends cannot answer a layout question.
    #
    # Still a PROXY. The engine's figure is TextDimensionsForText and needs the
    # game running; this only makes the picture agree with the check that refuses
    # the build, which is the most a shut-game instrument can promise.
    def font(px):
        if px not in fonts:
            path = None
            for cand in ("seguibl.ttf", "segoeui.ttf", "arial.ttf"):
                p = os.path.join(os.environ.get("WINDIR", ""), "Fonts", cand)
                if os.path.isfile(p):
                    path = p
                    break
            if path:
                fonts[px] = ImageFont.truetype(path, px)
            else:
                try:
                    fonts[px] = ImageFont.load_default(size=px)
                except TypeError:                               # Pillow before 10.1
                    fonts[px] = ImageFont.load_default()
        return fonts[px]

    def style(doc, comp):
        """Size, colour and alignment as THE FILE declares them.

        NOT gen_ic_ui.TEXT_STYLE. That dict holds the cells whose size was chosen and
        leaves every other one to the emitter's defaults, so reading it drew the share
        figures on the pie at 12px in a colour nobody had asked for - a preview
        disagreeing with the panel about the one thing it exists to show. The
        <component_text> node under each state is what the engine reads.
        """
        st = doc.state(comp) if comp is not None else None
        t = st.child("component_text") if st is not None else None
        if t is None:
            return 12, (255, 248, 215, 255), "Left"
        px = int(model.number(t.get("font_m_size"), 12))
        c = (t.get("font_m_colour") or "#FFF8D7FF").lstrip("#")
        rgba = tuple(int(c[i:i + 2], 16) for i in range(0, 8, 2))
        return px, rgba, t.get("texthalign") or "Left"

    def fit_two(doc, comp, s, w1, w2):
        """ICUI.fit_two's shape: as much as line one holds, the rest on line two.

        PIL's face is narrower than the game's, so every width here is scaled by
        GAME_FONT_WIDER before it is compared - see the constant for where that
        number was measured. It is still a stand-in: the engine's own
        TextDimensionsForText is the only honest answer, and check 20g asks it.
        """
        px, _colour, _halign = style(doc, comp)
        f = font(px)

        def wide(t):
            return draw.textlength(t, font=f) * GAME_FONT_WIDER

        if wide(s) <= w1:
            return s, ""
        words = s.split(" ")
        for i in range(len(words) - 1, 0, -1):
            if wide(" ".join(words[:i])) <= w1:
                rest = " ".join(words[i:])
                # Line two overflowing is the card's problem, not the split's: the
                # Lua has nowhere else to put it either.
                return " ".join(words[:i]), rest
        return s, ""          # one word wider than the cell; nothing to split on

    def measure(doc, comp, s):
        """How wide `s` draws in that cell, scaled the way fit_two scales.

        Same stand-in and same caveat: PIL's face is narrower than the game's, so
        this is OPTIMISTIC and a blurb that just fits here may take a line more on
        screen. ICUI.fit_lines asks the engine, which is the honest answer.
        """
        px, _colour, _halign = style(doc, comp)
        return draw.textlength(s, font=font(px)) * GAME_FONT_WIDER

    def text(doc, comp, s, x, y, w, h):
        """One cell's string, with the panel's two markups honoured.

        An [[img:]] icon costs a line box of width, so it is measured and drawn at
        the cell's own font size - approximate in the same way the font is, and
        for the same reason: the engine's box is not PIL's.
        """
        px, colour, halign = style(doc, comp)
        f = font(px)
        parts = segments(s)
        width = sum(draw.textlength(body, font=f) if kind == "text" else px
                    for kind, body, _tint in parts)
        # RIGHT TOO, since the party card's state word is right-aligned.
        tx = (x + (w - width) / 2 if halign == "Center"
              else x + w - width if halign == "Right" else x)
        # textyoffset is (top, bottom) padding: the engine centres the line in
        # what is left of the box, so a plate's lift shows here as it does there.
        st = doc.state(comp) if comp is not None else None
        tc = st.child("component_text") if st is not None else None
        top, bot = model.pair(tc.get("textyoffset") if tc is not None else None, (0, 0))
        # CENTRED ON THE GLYPHS' MIDDLE (anchor "lm"), not on PIL's line box, which
        # sits them ~5px low: measured against an in-game shot, where the column
        # title's letters centre on their cell.
        mid = y + top + (h - top - bot) / 2
        ty = mid - px / 2
        for kind, body, tint in parts:
            if kind == "img":
                art = _asset(body)
                if art:
                    canvas.alpha_composite(
                        rendering.raster(art, px, px, _PlainMetrics()), (int(tx), int(ty)))
                tx += px
                continue
            draw.text((tx, mid), body, fill=INK_OF.get(tint, colour), font=f,
                      anchor="lm")
            tx += draw.textlength(body, font=f)

    # A RACE OTHER THAN THE CHAOS DWARFS IS DRAWN FROM THE DUMP.
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
            # A CREATED ROOT is named by its CreateComponent call (derpy_ic_card_3),
            # and its file declares it under the file's own root name.
            names = [nd.name]
            if nd.file:
                names.append(re.sub(r"(_dwf)?(_compact)?$", "", os.path.basename(nd.file)))
            for want in names:
                for c in (doc.components if doc else []):
                    if c.get("id", c.tag) == want:
                        return doc, c
            # A ROOT CREATED UNDER ANOTHER NAME (ic_list from the Governors list
            # file, whose root is "listview") is its file's root component.
            if nd.file and doc is not None and doc.components and by_path[nd.path][1].file:
                return doc, doc.components[0]
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
        unknown, seen_art, drawn, fitted = [], set(), [0], {}

        def draw_node(nd, clip=None):
            if not nd.visible:
                return
            # A LIST'S ITEMS ARE CLIPPED TO ITS WINDOW (ICUI.list_build): an item
            # wholly below or above list_clip is not drawn, nor anything in it.
            # ponytail: whole items only - the dump is the list at its top, where
            # every item is wholly in or out; a scrolled dump would need pixel clips.
            if clip and (nd.y >= clip[1] or nd.y + (nd.h if nd.resized else 0) <= clip[0]):
                return
            if nd.name == "list_clip":
                clip = (nd.y, nd.y + nd.h)
            doc, c = comp_of(nd)
            if c is None:
                unknown.append(nd.path)
            else:
                st = doc.state(c)
                # THE LUA'S SIZE where it sized the component; the file's otherwise
                # (the fake tree's 10x10 default is nobody's size).
                w = nd.w if nd.resized else model.number(st.get("width"), 0) if st is not None else 0
                h = nd.h if nd.resized else model.number(st.get("height"), 0) if st is not None else 0
                w, h, x, y = int(round(w)), int(round(h)), nd.x, nd.y
                # THE SLIDER'S HANDLE IS THE ENGINE'S: docked at the top of its
                # track at a list's top, and never MoveTo'd by the Lua.
                if nd.name == "handle" and "/" in nd.path:
                    track = by_path[nd.path.rsplit("/", 1)[0]][1]
                    x, y, w = track.x, track.y, track.w
                plain = "".join(b for k, b, _t in segments(nd.text) if k == "text")
                if nd.name in G.FIT_PLATES and plain and nd.name in G.PANEL_LAYOUT:
                    x, w = G.fit_plate(nd.name, G.PANEL_LAYOUT[nd.name][0],
                                       G.PANEL_LAYOUT[nd.name][2], measure(doc, c, plain))
                    fitted[nd.name] = (x, w)
                # THE HELP BUTTON AT THE TITLE PLATE'S END, as ICUI.refresh puts it:
                # the Lua placed it after the harness's stub-measured plate, and the
                # plate drawn here is measured with the real face.
                # A SORT ARROW AT ITS CAPTION'S END, as ICUI.hdr_text_w puts it with
                # the engine's measure; the dump's x is the harness stub's.
                if nd.name.startswith("ic_hsort_"):
                    hn = [n for n in nodes if n.name == "ic_hdr_" + nd.name[-1]]
                    if hn:
                        hdoc, hc = comp_of(hn[0])
                        cap = "".join(b for k, b, _t in segments(hn[0].text) if k == "text")
                        gap = int(re.search(r"ICUI\.HSORT_GAP = (\d+)", lua("ui")).group(1))
                        x = hn[0].x + gap * 2 + (measure(hdoc, hc, cap) if cap and hc is not None else 0)
                if nd.name == "ic_help" and "ic_title" not in fitted:
                    tn = [n for n in nodes if n.name == "ic_title"]
                    tdoc, tc = comp_of(tn[0]) if tn else (None, None)
                    tplain = "".join(b for k, b, _t in segments(tn[0].text) if k == "text") if tn else ""
                    if tc is not None and tplain:
                        fitted["ic_title"] = G.fit_plate("ic_title", G.PANEL_LAYOUT["ic_title"][0],
                                                         G.PANEL_LAYOUT["ic_title"][2],
                                                         measure(tdoc, tc, tplain))
                if nd.name == "ic_help" and "ic_title" in fitted:
                    t, hb = G.PANEL_LAYOUT["ic_title"], G.PANEL_LAYOUT["ic_help"]
                    x = fitted["ic_title"][0] + fitted["ic_title"][1] + hb[0] - (t[0] + t[2])
                paste(doc, c, x, y, w, h, repaint=nd.images or None)
                if nd.text:
                    s_ = nd.text
                    # A CUT CELL DRAWS CUT, as ICUI.fit_cut cuts it in game: the
                    # dump's own cut measured with the harness's 8px-a-letter stub.
                    if nd.name in G.CUT_CELLS and "[[" not in s_:
                        s_ = s_[:-3] if s_.endswith("...") else s_
                        s_ = cut_words(lambda _s, _d=doc, _c=c: measure(_d, _c, _s), s_, w)
                    text(doc, c, s_, x, y, w, h)
                seen_art.update(nd.images.values())
                drawn[0] += 1
            for k in sorted(kids[nd.path], key=lambda k: order(nd, k)):
                draw_node(k, clip)
        draw_node(nodes[0])
        out = sized(raced(path or VIEW_OUT[view], race), box_w)
        canvas.save(out)
        problems = ["%s@%d: %s is in no twui file it was created from" % (view, box_w, p)
                    for p in unknown]
        problems += ["%s@%d: draws Chaos Dwarf art %s, not in gen_ic_ui.DWF_KEEPS"
                     % (view, box_w, p) for p in sorted(seen_art) if p and G.chd_art(p)]
        return out, n_art, missing + problems, drawn[0]

    # The panel, then the tab's own furniture.
    # ON THE GOVERNORS VIEW THE BACKDROP IS CLEARED (ICUI.gm_sync), so the
    # panel's own image 0 is left undrawn and the map shows through.
    paste(panel, named[("panel", "derpy_ic_panel")], 0, 0, G.PANEL_W, G.PANEL_H,
          repaint={0: None} if gm else None)

    court = demo_court(G)
    counts = slice_counts(G.DIAL_SLICES, court)

    if view == "court":
        # THE PLATE FIRST. It is declared before every wedge in the generated file and
        # the engine draws children in declaration order, so this is the z-order the
        # game uses - get it wrong here and the preview hides the fault it exists to
        # show.
        paste(panel, named[("panel", "ic_dial_box")], *G.DIAL_BOX)

        owner = []
        for row, n in zip(court, counts):
            owner += [row[0]] * n
        for i in range(G.DIAL_SLICES):
            paste(panel, named[("panel", "ic_wedge_%02d" % i)], *G.PIE_BOX,
                  repaint={0: G.wedge_path(i, owner[i] if i < len(owner) else None)})

        # ONE WALL PER PARTY AFTER THE FIRST, at the slice its run begins on.
        begins = []
        at = 0
        for n in counts:
            begins.append(at)
            at += n
        for i, start in enumerate(begins):
            if i == 0 or counts[i] == 0:
                continue
            paste(panel, named[("panel", "ic_div_%02d" % i)], *G.PIE_BOX,
                  repaint={0: G.div_path(start)})

        paste(panel, named[("panel", "ic_dial_rim")], *G.RIM_BOX)

        # The crests and the figures on the pie.
        def arc_box(radius, f, w, h):
            a = math.pi * (1 - f)
            return (int(math.floor(G.DIAL_CX + radius * math.cos(a) - w / 2.0 + 0.5)),
                    int(math.floor(G.DIAL_CY - radius * math.sin(a) - h / 2.0 + 0.5)))

        def min_slices(radius, ink):
            return math.ceil(ink / (radius * math.pi / G.DIAL_SLICES))

        crest_min = min_slices(G.CREST_R, G.CREST_PX)
        share_min = min_slices(G.SHARE_R, 40)
        for i, ((slug, _title, share, _l, _n, _t), n) in enumerate(zip(court, counts)):
            f = (begins[i] + n / 2.0) / G.DIAL_SLICES
            if n >= crest_min:
                cx, cy = arc_box(G.CREST_R, f, G.CREST_PX, G.CREST_PX)
                paste(panel, named[("panel", "ic_barc_%02d" % i)],
                      cx, cy, G.CREST_PX, G.CREST_PX, repaint={0: G.sigil_path(slug)})
            if n >= share_min:
                sx, sy = arc_box(G.SHARE_R, f, G.SHARE_W, G.SHARE_H)
                text(panel, named[("panel", "ic_barp_%02d" % i)], "%d%%" % share,
                     sx, sy, G.SHARE_W, G.SHARE_H)

    # Every static cell the court view shows.
    # THE BAND THE DEMO SHARE ACTUALLY LANDS IN, off the model's own table. Typed,
    # it said "Contested" beside effects belonging to a different band.
    # WHICH VIEW'S CHROME THIS PICTURE WEARS. A picker is a MODAL: ICUI.live_view
    # answers "pick" for it whatever tab is lit behind, and the tab that stays
    # lit is the one it was opened from. "pick_ready" is not a view the panel has
    # - it is the same picker with the sort clicked once - so it resolves to
    # "pick" everywhere except which setting the control reads.
    _base = "pick" if view.startswith("pick") else view
    _sort_view = _base
    _sort_mode = 2 if view == "pick_ready" else 1
    # The offices tab is what a seat's picker is opened from, so that is the tab
    # that stays lit under it.
    _lit_tab = "offices" if _base == "pick" else ("govs" if gm else view)
    if law:
        # The government cards open from the Court tab's New Government button.
        _lit_tab = "court" if view == "gov_cards" else "laws"
    _band = [b for b in G.IC.CONTROL_BANDS if court[0][2] >= b[1]][0]
    _sufferance = int(re.search(r"sufferance_share\s*=\s*(\d+)", lua("model")).group(1))
    STRINGS = {
        "ic_title": "Hashut's Court",
        # The demo court's own count, so the header and the ziggurat agree.
        "ic_influence": "%d of %d seats filled" % (len(DEMO_OFFICES), len(G.IC.OFFICES)),
        # ICUI.draw_fill's label, read out of the Lua; without it the Offices
        # picture showed an empty red bar under the ziggurat.
        "ic_fill": re.search(r'ICUI\.FILL_LABEL = "([^"]*)"', ui).group(1),
        "ic_tab_court": "Court",
        "ic_tab_offices": "Offices",
        "ic_tab_govs": "Governors",
        "ic_tab_intrigue": "Intrigue",
        "ic_tab_petitions": "Petitions",
        "ic_tab_log": "Record",
        "ic_tab_laws": "Laws",
        # OFF ICUI.SECTION.court, not typed: a typed copy here read "Standing"
        # for as long as the panel had said "Influence".
        "ic_lbl_section": re.search(r'court\s*=\s*"([^"]*)"',
                                    _block(ui, "ICUI.SECTION")).group(1),
        "ic_col_left": "Control of the Court",
        "ic_col_right": "Parties of the Court",
        # THE LEFT HALF OF THE CROWN'S BOX: the share, the band, then the
        # band's effects one to a line - what draw_court writes.
        "ic_control": "[[img:%s]][[/img]]%d%% of the court" % (cost_icon, court[0][2]),
        "ic_control_band": "[[img:%s]][[/img]]%s" % (band_icon, _band[2]),
        # THE GOVERNMENT'S ROW: the LONGEST name, as draw_gov
        # writes it, since a picture of the easy case answers nothing.
        "ic_gov": ("[[img:%s]][[/img]]Government: %s [[img:%s]][[/img]]%d of %d"
                   % (gov_icons[longest_gov[0]], longest_gov[1],
                      gov_icons["conclave"], 5, 6)),
        "ic_gov_btn": "New Government",
        "ic_leader_lbl": "The Crown",
        "ic_leader_name": DEMO_LEADERS[0],
        "ic_leader_party": "[[img:%s]][[/img]]%s" % (G.sigil_path("crown"), court[0][1]),
        # HIS TRAIT AND THE PARTY'S TWO, decorated as ICUI.trait_line does -
        # the same three the Crown's card draws.
        "ic_leader_trait": "[[img:%s]][[/img]]%s" % (trait_icon, DEMO_LTRAITS[0]),
        "ic_leader_t1": "[[img:%s]][[/img]]%s" % (trait_icon, DEMO_TRAITS["crown"][0]),
        "ic_leader_t2": "[[img:%s]][[/img]]%s" % (trait_icon, DEMO_TRAITS["crown"][1]),
        # NO PAGER. ICUI.draw_pager hides all three whenever the list fits on one
        # page, and both demos do - five parties in ten card slots, twelve rows in
        # a pool of twelve. Drawing them regardless put two buttons and a caption
        # on a picture the panel leaves empty.
        # THE SUFFERANCE WARNING ONLY WHEN IT WOULD REALLY FIRE. IC.sufferance
        # returns nil at exactly the threshold, and the demo court sits on 20 - the
        # threshold itself - so drawing it unconditionally put a line on the picture
        # that the panel would not draw.
        "ic_alert": ("Your own party holds %d%% of the court. Below %d%% you rule "
                     "on sufferance." % (court[0][2], _sufferance)
                     if court[0][2] < _sufferance
                     # ONE STRING IN GAME: on Intrigue the dispatcher's `warn` is
                     # draw_intrigue's sentence, which the intrigue branch below
                     # writes - drawing this too printed two lines over each other.
                     and not (view == "intrigue" and intrigue_lines(G, court))
                     else ""),
    }
    # THE EFFECTS, NOT THE BLURB. ICUI.band_effects reads
    # derpy_ic_effects_derpy_ic_control_<slug>, which gen_iron_court builds by
    # joining effect_short over the band's own rows; draw_court splits it back
    # into ICUI.FX_KEYS, one to a line, and blanks the rest.
    _fx = [G.IC.effect_short(e, m, i) for e, m, i in _band[4]]
    for _k, _key in enumerate(lua_words(ui, "ICUI.FX_KEYS")):
        _line = _fx[_k] if _k < len(_fx) else ""
        _label = re.match(r"^(.*?)\s*[+-]\d", _line)
        _icon = _label and fx_icons.get(_label.group(1))
        STRINGS[_key] = ("[[img:%s]][[/img]]%s" % (_icon, _line)) if _icon else _line
    # WHAT THIS VIEW DOES NOT DRAW, off the dispatcher's OWN lists. ICUI.refresh
    # hides the two-column furniture, the Crown's block and the dial on every view
    # but the court, and a component left behind draws over the list of whatever
    # tab the player just opened - which is a fault the preview has to be able to
    # show rather than one it quietly avoids. Read out of the Lua, so a key added
    # to either list is hidden here too.
    hidden = set(("ic_page_prev", "ic_page_lbl", "ic_page_next"))    # see STRINGS
    # THE BOOK'S LINE is a Dwarf court's only, and this
    # path draws the Chaos Dwarf court; the Dwarf one is the shipped Lua's dump.
    if not re.search(r'show\(comp\("ic_book", panel\), false\)', ui):
        raise SystemExit("ICUI.refresh no longer hides ic_book by name on a "
                         "tab switch - re-read it before trusting this picture")
    hidden.add("ic_book")
    _gm_n = (len(gm_province_rows()) if view == "gm_provinces"
             else len(pick_lines(False)) if view == "gm_picker" else 0)
    hidden |= gm_hidden(G, view, _gm_n)
    # THE FOOTER'S PLATE shows while the footer line does (ICUI.gm_sync).
    if gm and STRINGS.get("ic_alert"):
        hidden.discard("ic_gm_foot")
    # THE HELP PAGE'S CELLS ARE THE HELP VIEW'S, and no picture here is of it;
    # THE FILL BUTTON IS THE OFFICES TAB'S. Both off ICUI.refresh's own tests;
    # drawn anyway, the help card covers the Governors view's map.
    if not re.search(r'show\(comp\(name, panel\), view == "help" and not ICUI\.pick\)', ui) \
            or not re.search(r'show\(comp\("ic_fill", panel\), ICUI\.pick == nil and '
                             r'ICUI\.view == "offices"\)', ui):
        raise SystemExit("ICUI.refresh no longer gates the help cells or ic_fill as "
                         "this reads it - re-read it before trusting this picture")
    hidden |= set(k for k in G.PANEL_LAYOUT if k.startswith("ic_help_"))
    if view != "offices":
        hidden.add("ic_fill")
    # THE ZIGGURAT IS THE OFFICES TAB'S, with its cards.
    if not re.search(r'show\(comp\("ic_zig_bg", panel\), view == "offices"\)', ui):
        raise SystemExit("ICUI.refresh no longer gates ic_zig_bg as this reads it")
    if view != "offices":
        hidden.add("ic_zig_bg")
    # AND THE TITLE ON ITS SHRINE, its words the Lua's own.
    if not re.search(r'show\(comp\("ic_off_title", panel\), view == "offices"\)', ui):
        raise SystemExit("ICUI.refresh no longer gates ic_off_title as this reads it")
    if view != "offices":
        hidden.add("ic_off_title")
    STRINGS["ic_off_title"] = re.search(r'ICUI\.OFFICES_TITLE = "([^"]+)"', ui).group(1)
    # THE LAWS TAB'S CELLS: off ICUI.refresh's own gate on every other view, and
    # on the two law screens whatever the draw left showing - the board's cells
    # on the board, the vote's on the vote, the blocks it filled.
    if not re.search(r'for _, name in ipairs\(ICUI\.LAW_BOARD_KEYS\) do show\(comp\(name, '
                     r'panel\), laws_view and not on_vote\) end', ui) \
            or not re.search(r'for _, name in ipairs\(ICUI\.LAW_VOTE_KEYS\) do show\(comp\('
                             r'name, panel\), on_vote\) end', ui):
        raise SystemExit("ICUI.refresh no longer gates the law cells as this reads it")
    if not re.search(r'for _, name in ipairs\(ICUI\.GC_KEYS\) do show\(comp\(name, panel\), '
                     r'gov_pick\) end', ui):
        raise SystemExit("ICUI.refresh no longer gates the government cards as this reads it")
    if not law:
        hidden |= set(k for k in G.PANEL_LAYOUT if k.startswith(("ic_law_", "ic_lv_", "ic_gc_")))
    else:
        for k in G.PANEL_LAYOUT:
            c = LD.get("derpy_ic_panel/" + k)
            if c and not c.vis:
                hidden.add(k)
            elif c and k.startswith(("ic_law_", "ic_lv_", "ic_gc_")):
                STRINGS[k] = c.text
    # THE COLUMN'S WORDS, off the map Lua, so a reworded label reaches the picture.
    _titles = dict(re.findall(r'(\w+) = "([^"]+)"', re.search(
        r'ICUI\.GM_PAGE_TITLE = \{([^}]*)\}', lua("ui_map")).group(1)))
    STRINGS.update({
        "ic_gm_head": _titles["picker" if view == "gm_picker" else "provinces"],
        "ic_gm_tog_lbl_1": _titles["parties"],
        "ic_gm_tog_lbl_2": _titles["provinces"],
    })
    # THE SORT BUTTONS' WORDS, off the map Lua: the picker's are its own.
    _sorts = re.search(r'ICUI\.%s = \{(.*)\}$' % (
        "GM_PICK_SORTS" if view == "gm_picker" else "GM_SORTS"), lua("ui_map"), re.M).group(1)
    for i, word in enumerate(re.findall(r'\{"([^"]+)", \d+\}', _sorts)):
        STRINGS["ic_gm_sort_%d" % (i + 1)] = word
    # THE ACTION BAR, off the panel's own tables. ICUI.draw_actions shows the
    # three buttons for a chosen rival and the hint otherwise, and ICUI.refresh
    # hides all four on every other view.
    _act_keys = lua_words(ui, "ICUI.ACT_KEYS")
    _act_label = dict(re.findall(r'(ic_act_\w+) = "([^"]+)"',
                                 _block(ui, "ICUI.ACT_LABEL")))
    if view == "court" and DEMO_SEL != 0:
        hidden.add("ic_act_hint")
        STRINGS.update(_act_label)
    else:
        hidden |= set(_act_keys)
        if view == "court":
            STRINGS["ic_act_hint"] = lua_words(ui, "ICUI.ACT_HINT")[0]
        else:
            hidden.add("ic_act_hint")
    # AND EVERY COLUMN ARROW THE PANEL WOULD NOT DRAW. ICUI.refresh shows one
    # only where the view has a mode for that column AND the column has a
    # caption, so a preview that drew all five regardless would be a preview of
    # the layout file rather than of the panel. The sortable columns are read
    # out of the Lua's own SORTS table by their `col`, never listed here.
    _cols = _sortable_columns(ui, _sort_view)
    _heads = _header_row(ui, view)
    # THE GAP IN FRONT OF AN ARROW, off the panel's own constant rather than
    # typed - it is the same 6 the caption has in front of it, and moving one
    # without the other is the drift this reads it to avoid.
    _HSORT_GAP = int(re.search(r"ICUI\.HSORT_GAP = (\d+)", ui).group(1))
    for _i, _key in enumerate(("ic_hsort_a", "ic_hsort_b", "ic_hsort_c",
                               "ic_hsort_d", "ic_hsort_e"), start=1):
        if _i not in _cols or not (_heads or [""] * 5)[_i - 1]:
            hidden.add(_key)
    # THE MOVE GROUPS' HEADINGS ARE THE INTRIGUE TAB'S ALONE: ICUI.refresh shows
    # each ic_plotcat_N only when view == "intrigue". On their plates, drawn
    # elsewhere, they are four empty bars across the pie. Read off the Lua's own
    # condition.
    if not re.search(r'show\(comp\("ic_plotcat_" \.\. i, panel\), view == "intrigue"\)', ui):
        raise SystemExit("ICUI.refresh no longer shows ic_plotcat_N on intrigue "
                         "alone - re-read it before trusting this picture")
    if view != "intrigue":
        hidden |= set(k for k in G.PANEL_LAYOUT if k.startswith("ic_plotcat_"))
    if view != "court":
        hidden |= set(lua_words(ui, "ICUI.COLUMN_KEYS"))
        hidden |= set(lua_words(ui, "ICUI.LEADER_KEYS"))
        hidden |= set(lua_words(ui, "ICUI.CONTROL_KEYS"))
        # THE GOVERNMENT'S ROW is not on CONTROL_KEYS (draw_gov shows it), but
        # the tab switch hides it by name - so must this, or every tab wears it.
        if not re.search(r'show\(comp\("ic_gov", panel\), false\)', ui):
            raise SystemExit("ICUI.refresh no longer hides ic_gov by name on a "
                             "tab switch - re-read it before trusting this picture")
        hidden |= {"ic_gov", "ic_gov_btn", "ic_gov_glow"}
        if _base == "pick":
            # THE PICKER'S OWN QUESTION, not a tab's standing label. The format
            # string is read out of ICUI.pick_title and the two numbers out of
            # IC.TUNE, so a reworded title or a retuned bar reaches the picture -
            # and the seat is a REAL one off the generator's office table.
            fmt = re.search(
                r'return string\.format\(\s*\n?\s*"(Choose who takes [^"]*)"',
                ui).group(1)
            # NOT `model`. That name is TWUI Studio's parser module in this
            # function and shadowing it turns every later paste() into an
            # AttributeError on a string - which is what happened.
            mlua = lua("model")
            bars = [int(n) for n in re.findall(
                r"\d+", re.search(r"tier_influence\s*=\s*\{([^}]*)\}",
                                  mlua).group(1))]
            turns = int(re.search(r"term_turns\s*=\s*(\d+)", mlua).group(1))
            seat = DEMO_SEAT(G)
            STRINGS["ic_lbl_section"] = (fmt
                .replace("%s", seat["name"], 1)
                .replace("%s", str(bars[seat["tier"] - 1]), 1)
                .replace("%d", str(turns), 1))
        elif view == "offices":
            # THE OFFICES TAB'S LABEL IS DERIVED, not stored: ICUI.SECTION has no
            # entry for it at all, because a sentence counting the seats in prose
            # goes stale the moment a tier gains one. ICUI.section_text builds it,
            # and this reads that same format string and fills it from the same
            # three places - IC.OFFICES, tier_seats() and IC.TUNE.
            _fmt = re.search(r'"(%d seats in %d tiers [^"]*)"', ui).group(1)
            _tiers = sorted(set(o["tier"] for o in G.IC.OFFICES))
            _widths = "/".join(str(G.IC.tier_seats()[t]) for t in _tiers)
            _turns = re.search(r"term_turns\s*=\s*(\d+)", lua("model")).group(1)
            STRINGS["ic_lbl_section"] = (_fmt
                .replace("%d", str(len(G.IC.OFFICES)), 1)
                .replace("%d", str(len(_tiers)), 1)
                .replace("%s", _widths, 1)
                .replace("%d", _turns, 1))
        elif view == "petitions":
            STRINGS["ic_lbl_section"] = petitions_label()
        elif law:
            STRINGS["ic_lbl_section"] = LD["derpy_ic_panel/ic_lbl_section"].text
        elif view == "gm_provinces":
            STRINGS["ic_lbl_section"] = re.search(
                r'govs\s*=\s*"([^"]*)"', _block(ui, "ICUI.SECTION")).group(1)
        elif view == "gm_picker":
            # ICUI.pick_title's governor line, for the province being chosen for.
            STRINGS["ic_lbl_section"] = re.search(
                r'"(Choose who governs )%s"', ui).group(1) + DEMO_GOVS[2][0]
        else:
            STRINGS["ic_lbl_section"] = re.search(
                r'%s\s*=\s*"([^"]*)"' % view, _block(ui, "ICUI.SECTION")).group(1)

    # THE HEADER STRIP IS NOT ON THE COURT TAB. ICUI.HEADERS.court is nil, so the
    # dispatcher hides all five there - a preview that drew them would be a
    # preview of the FILE. The list views set them below.
    #
    # AND IN THE GENERATOR'S OWN DECLARATION ORDER, not alphabetical. Children
    # draw in the order they are declared and _panel_order is what declares
    # them, so this is the z-order the engine uses. Alphabetical was harmless
    # until a second opaque plate arrived: "ic_crown_box" sorts after
    # "ic_control", so the plate went on top of the lines it frames - the
    # preview drawing a fault that is not in the file.
    for name in sorted(G.PANEL_LAYOUT, key=G._panel_order):
        # ic_plotcat_ TOO: the intrigue block below draws them, fitted to their
        # words. Drawn here as well, the full-width plate showed behind the fitted one.
        if name.startswith(("ic_wedge_", "ic_barc_", "ic_barp_", "ic_div_", "ic_hdr_",
                            "ic_plotcat_")):
            continue
        if name in ("ic_dial_box", "ic_dial_rim") or name in hidden:
            continue
        # THE RIMS ARE DRAWN AFTER THE SEGMENTS, below, as the panel declares them.
        if name.startswith(("ic_lv_seg_", "ic_lv_segc_", "ic_law_p_baraye", "ic_law_p_barnay",
                            "ic_law_p_barrim", "ic_lv_barrim")):
            continue
        x, y, w, h = G.PANEL_LAYOUT[name]
        # MOVED AT RUNTIME: ICUI.draw_law_bar centres the abstaining label over
        # its gap, so the layout's x is only where it starts.
        if law and name == "ic_lv_abs" and LD.get("derpy_ic_panel/" + name):
            x = G.sc(int(LD["derpy_ic_panel/" + name].x), box_w)
        # ONE COMPONENT, TWO HOMES. The court moves the section label into the
        # Crown's box and PANEL_LAYOUT holds the position of the other four
        # views, so reading it here draws the label where that tab never puts
        # it. ICUI.refresh does the same swap against the same constant.
        if name == "ic_lbl_section" and view == "court":
            x, y, w, h = G.COURT_SECTION_XY
        if name == "ic_leader_port":
            paste(panel, named[("panel", name)], x, y, w, h,
                  repaint={0: G.plate_path("crown"), 1: DEMO_FACES[0], 2: None})
            continue
        # THE LIT TAB IS LIT BY ITS PLATE. light_tabs repaints slots 0 and 1; slot 1
        # is the hover art, which a still picture never shows.
        # THE ARROW SITS PAST ITS CAPTION, not on its column's x. The x in
        # PANEL_LAYOUT is a placeholder - ICUI.refresh MoveTo's each arrow to
        # its header's x plus ICUI.hdr_text_w, which measures the caption with
        # the engine's own TextDimensionsForText - so a picture drawn from the
        # layout file alone puts every arrow on top of a heading's first letter.
        # PIL's measure is the same stand-in fit_two uses and is optimistic in
        # the same direction: an arrow drawn a few pixels LEFT of where the
        # engine will put it.
        if name.startswith("ic_hsort_"):
            _i = ord(name[-1]) - ord("a")
            _cap = (_heads or [""] * 5)[_i]
            x += int(round(_HSORT_GAP * 2
                           + measure(panel, named[("panel", "ic_hdr_" + name[-1])],
                                     _cap)))
        # A FITTED PLATE is sized to its words, as ICUI.fit_plate sizes it.
        if name in G.FIT_PLATES and STRINGS.get(name):
            x, w = G.fit_plate(name, x, w, measure(panel, named[("panel", name)],
                                                   STRINGS[name]))
        lit = {0: TAB_SELECTED} if name == "ic_tab_" + _lit_tab else None
        if name == "ic_gm_tog_2" and view == "gm_provinces":
            lit = {0: G.GM_ROUND % "selected"}
        if law and name.startswith(("ic_law_", "ic_lv_", "ic_gc_")):
            lit = LD["derpy_ic_panel/" + name].images or None
        paste(panel, named[("panel", name)], x, y, w, h, repaint=lit)
        s = STRINGS.get(name)
        if s:
            text(panel, named[("panel", name)], s, x, y, w, h)

    # The list views: the header strip, then the shared row pool.
    #
    # A VIEW WITH NO ENTRY IN ICUI.HEADERS DRAWS NO STRIP. There are two: the court has no row list, and intrigue has its own column
    # headings over a grid of cards. Testing the table rather than naming the
    # views is what the dispatcher does - `ICUI.HEADERS[view]` nil hides all five.
    # AND A PICKER TAKES PICK_HEADERS, which is a separate table - ICUI.HEADERS
    # has no "pick" row at all, and refresh falls through to ICUI.PICK_HEADERS
    # for exactly that reason.
    # ONE READER FOR THE CAPTIONS, which is _header_row - the same one the arrow
    # visibility above is decided by. ICUI.HEADERS pads its keys into a column
    # (`govs     = {`), so a second regex expecting one space before the "="
    # would miss rows and draw arrows over headings that are not there.
    if _heads:
        for i, key in enumerate(lua_words(ui, "ICUI.HDR_KEYS")):
            if not _heads[i]:
                continue
            hx, hy, hw, hh = G.PANEL_LAYOUT[key]
            paste(panel, named[("panel", key)], hx, hy, hw, hh)
            text(panel, named[("panel", key)], _heads[i], hx, hy, hw, hh)

    # The Governors view: the column's rows, then pins on the map.
    if gm:
        def grow(i, r):
            """One row of the column's pool, as ICUI.gm_fill_row fills it."""
            rx, ry = G.GM_ROW_X, G.GM_ROW_Y + i * G.GM_ROW_PITCH
            paste(gm_row_doc, named[("gmrow", "derpy_ic_gm_row")], rx, ry,
                  G.GM_ROW_W, G.GM_ROW_H, repaint={0: G.GM_ROW_ART % r["look"]})
            # IN THE FILE'S DECLARATION ORDER, which is the order the engine draws
            # in: sorted, the face was painted over the badge on its corner.
            for key in [c.get("id") for c in gm_row_doc.components
                        if c.get("id") in G.GM_ROW_LAYOUT]:
                cx, cy, cw, ch = G.GM_ROW_LAYOUT[key]
                comp = named[("gmrow", key)]
                x, y = rx + cx, ry + cy
                if key == "ic_gr_face":
                    if r.get("face"):
                        paste(gm_row_doc, comp, x, y, cw, ch, repaint={
                            0: G.MASK_NONE if r.get("vacant") else G.plate_path(r.get("plate")),
                            1: r["face"], 2: None})
                elif key in ("ic_gr_crest", "ic_gr_badge", "ic_gr_icon"):
                    art = {"ic_gr_crest": r.get("crest"), "ic_gr_badge": r.get("badge"),
                           "ic_gr_icon": r.get("fealty")}[key]
                    if art:
                        paste(gm_row_doc, comp, x, y, cw, ch, repaint={0: art})
                else:
                    s = r.get(key[len("ic_gr_"):])
                    if s:
                        s = cut_words(lambda _s: measure(gm_row_doc, comp, _s), s, cw)
                        text(gm_row_doc, comp, s, x, y, cw, ch)

        fealty = dict(re.findall(r'(high|medium|low) = "(ui/skins/default/icon_fealty_\w+\.png)"',
                                 lua("ui_map")))
        tune = _tune(lua("model"))
        rate = 1.0 / float(tune["gov_levels_per_weight"])
        floor, start = int(tune["prov_defect_floor"]), int(tune["prov_loyalty_start"])

        def band(loyal):
            return fealty["low" if loyal <= floor else "high" if loyal > start else "medium"]

        drawn = 0
        if view == "gm_provinces":
            rows = gm_province_rows()
            for i, (prov, who, slug, away, loyal) in enumerate(rows[:G.GM_ROWS]):
                levels = GM_DEMO_LEVELS[i % len(GM_DEMO_LEVELS)]
                weight = max(1, -(-int(levels * rate * 100) // 100))
                grow(i, {
                    "look": "selected" if i == 1 else "active",
                    "l1": prov,
                    "l2": (who + " (away)") if (who and away) else (who or "None assigned"),
                    "l3": ("%d%%, +%d strength" % (loyal, weight)) if who else "%d%%" % loyal,
                    "face": DEMO_FACES[i % len(DEMO_FACES)] if who else G.SIL_PATH,
                    "vacant": who is None, "plate": slug,
                    "badge": G.sigil_path(slug) if who else None,
                    "fealty": band(loyal)})
                drawn += 1
        else:
            rows = pick_lines(False)
            _kw = _kind_words(ui)
            for i, (name, trade, house, rank, standing, holds, refusal, kind) in \
                    enumerate(rows[:G.GM_ROWS]):
                slug, party_name = court[house][0], court[house][1]
                grow(i, {
                    "look": "inactive" if refusal else ("selected" if i == 0 else "active"),
                    "l1": "%s%s - %s" % ((_kw[kind] + " ") if _kw else "", name, trade),
                    "l2": party_name,
                    "l3": "Rank %d, %d influence" % (rank, standing),
                    "face": DEMO_FACES[i % len(DEMO_FACES)], "plate": slug,
                    "badge": G.sigil_path(slug)})
                drawn += 1

        # THE PINS, in a sheet right of the column: one per demo province, the
        # first a capital, the second ringed as chosen. Five components each,
        # every one standing its bottom centre on the settlement's point
        # (GM_ANCHOR) and drawn in the order gm_draw_pins makes them. THE FACE
        # IS SQUARE HERE: TWUI Studio's rasteriser has no maskimage, so the
        # porthole_mask layer is left undrawn rather than drawn as a white disc
        # over the face. In game it is round.
        pin = named[("gmpin", "derpy_ic_gm_pin")]
        face = named[("gmface", "derpy_ic_gm_face")]
        plate = named[("gmname", "derpy_ic_gm_name")]
        loyal_c = named[("gmloyal", "derpy_ic_gm_loyal")]
        badge = named[("gmbadge", "derpy_ic_gm_badge")]
        px0 = G.GM_ROW_X + G.GM_ROW_W + 120 + G.GM_PIN_W // 2
        # FOUR TO A LINE, spaced to the canvas: pins are never scaled, so at
        # 1600 the 1920 spacing ran the fourth off the edge.
        step = min(G.GM_PIN_W + 150, (G.PANEL_W - 20 - G.GM_PIN_W // 2 - px0) // 3)
        for i, (prov, who, slug, away, loyal) in enumerate(gm_province_rows()):
            sx = px0 + (i % 4) * step
            sy = 180 + G.GM_PIN_H + (i // 4) * (G.GM_PIN_H + 90)
            box = (sx - G.GM_PIN_W // 2, sy - G.GM_PIN_H, G.GM_PIN_W, G.GM_PIN_H)
            paste(gm_pin_doc, pin, *box, repaint={
                G.GM_PIN_LAYERS.index("party"): G.gm_ring_path(slug) if slug else None,
                G.GM_PIN_LAYERS.index("capital"): G.MAP_RING_CAPITAL if i == 0 else None,
                G.GM_PIN_LAYERS.index("outline"): G.MAP_RING_OUTLINE if i == 1 else None})
            # AN EMPTY SEAT IS THE DARK GROUND ALONE: gm_draw_pins clears both the
            # port and the crest layer for it.
            paste(gm_face_doc, face, *box, repaint={
                G.GM_FACE_LAYERS.index("port"): DEMO_FACES[i % len(DEMO_FACES)] if who else None,
                G.GM_FACE_LAYERS.index("crest"): None,
                G.GM_FACE_LAYERS.index("mask"): None})
            nx, ny = sx - G.GM_PIN_W // 2, sy - G.GM_NAME_H
            paste(gm_name_doc, plate, nx, ny, G.GM_PIN_W, G.GM_NAME_H, repaint={
                G.GM_NAME_LAYERS.index("wash"): G.gm_wash_path(slug) if slug else None})
            name = cut_words(lambda _s: measure(gm_name_doc, plate, _s), prov, G.GM_NAME_W)
            text(gm_name_doc, plate, name, nx, ny, G.GM_PIN_W, G.GM_NAME_H)
            lx, ly = sx - G.GM_LOYAL_W // 2, sy - G.GM_LOYAL_H
            paste(gm_loyal_doc, loyal_c, lx, ly, G.GM_LOYAL_W, G.GM_LOYAL_H)
            text(gm_loyal_doc, loyal_c, "Loyalty %d%%" % loyal, lx, ly, G.GM_LOYAL_W, G.GM_LOYAL_H)
            paste(gm_badge_doc, badge, *box, repaint={
                G.GM_BADGE_LAYERS.index("crest"): G.sigil_path(slug) if (who and slug) else None})
        draw.text((px0 - G.GM_PIN_W // 2, G.PANEL_H - 100), "Map stand-in. Faces are square here "
                  "and round in game: the preview cannot draw a maskimage.",
                  fill=(255, 248, 215, 255), font=font(14))

        out = path or sized(OUT_GM_PICK if view == "gm_picker" else OUT_GM, box_w)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        canvas.convert("RGB").save(out)
        return out, n_art, missing, drawn

    # The character picker: the shared row pool, twelve men deep.
    if view in ("pick", "pick_ready"):
        rows = pick_lines(view == "pick_ready")
        _kw = _kind_words(ui)
        for i, (name, trade, house, rank, standing, holds, refusal, kind) in \
                enumerate(rows):
            slug, party_name = court[house][0], court[house][1]
            rx = G.ROWS_X
            ry = G.ROWS_Y + i * G.ROW_PITCH
            paste(row_doc, named[("row", "derpy_ic_row")], rx, ry,
                  G.ROW_W, G.ROW_H)

            def rcell(key, s=None, repaint=None, _x=rx, _y=ry):
                cx, cy, cw, ch = G.ROW_LAYOUT[key]
                comp = named[("row", key)]
                paste(row_doc, comp, _x + cx, _y + cy, cw, ch, repaint=repaint)
                if s:
                    text(row_doc, comp, s, _x + cx, _y + cy, cw, ch)

            def rcut(key, s, _x=rx, _y=ry):
                cx, cy, cw, ch = G.ROW_LAYOUT[key]
                comp = named[("row", key)]
                paste(row_doc, comp, _x + cx, _y + cy, cw, ch)
                s = cut_words(lambda _s: measure(row_doc, comp, _s), s, cw)
                if s:
                    text(row_doc, comp, s, _x + cx, _y + cy, cw, ch)

            # HIS OWN PORTHOLE ON HIS HOUSE'S PLATE, which is what
            # ICUI.set_row_icon draws when portrait_path resolves. Slot 2 is the
            # Crown's mask and ICUI.set_plate is handed a FACTION, so it is
            # undrawn on every other row - the same rule the party card follows.
            rcell("ic_row_port",
                  repaint={0: G.plate_path(slug),
                           1: DEMO_FACES[i % len(DEMO_FACES)],
                           2: DEMO_FACES[0] if slug == "crown" else None})
            # AND THE HOUSE CREST BESIDE THE PARTY COLUMN. It is a separate cell
            # from the porthole and is fed only when the main icon is a FACE -
            # otherwise it would be the same flag twice on one row.
            rcell("ic_row_crest", repaint={0: G.sigil_path(slug)})
            # HIS POSITION IN FRONT OF HIS NAME - "Retainer Amarudz
            # Grimtidesson - Shrewd". The word comes out of the panel's own
            # table and the fallback, a bare name for a man the engine would not
            # classify, is what the cell drew before the title existed.
            #
            # AND CUT, because the shipped Lua cuts this cell. It is the widest
            # cell on the row and still cannot hold its own worst case, so what
            # the cut is allowed to eat is the trade on the end - which is a
            # thing a picture can show and an assertion cannot.
            rcut("ic_row_a", "%s%s - %s"
                 % ((_kw[kind] + " ") if _kw else "", name, trade))
            rcell("ic_row_b", party_name)
            # THE RANK CELL IS A NUMBER: 45px of column has no room for a word
            # before it, which would run into the influence heading.
            rcell("ic_row_c", str(rank))
            # THE PANEL'S OWN FORMAT, not a copy of it, so a renamed word in the
            # panel reaches the picture.
            rcell("ic_row_d", _pick_d_fmt(ui)
                  % (standing, holds if holds else "None"))
            # RED ON EXACTLY THE ROWS THE CLICK WOULD REFUSE, which is the rule
            # ICUI.draw_picker follows: it reads ICUI.pick_rows rather than
            # re-testing the conditions, so the colour and the button cannot
            # disagree.
            rcell("ic_row_e", red(refusal) if refusal else "Choose")

        out = path or sized(OUT_PICK_READY if view == "pick_ready" else OUT_PICK,
                             box_w)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        canvas.convert("RGB").save(out)
        return out, n_art, missing, len(rows)

    # The laws tab: the bar's pieces, then the two pools.
    if law:
        # THE SUPPORT BAR'S PIECES, where draw_law_bar MoveTo'd them on the
        # 1920 tree, scaled the way every layout number is.
        for name in sorted(G.PANEL_LAYOUT, key=G._panel_order):
            c = LD.get("derpy_ic_panel/" + name)
            if not name.startswith(("ic_lv_seg_", "ic_lv_segc_", "ic_law_p_baraye",
                                    "ic_law_p_barnay")) or not c or not c.vis:
                continue
            x0, x1 = G.sc(int(c.x), box_w), G.sc(int(c.x + c.w), box_w)
            y0, y1 = G.sc(int(c.y), box_w), G.sc(int(c.y + c.h), box_w)
            paste(panel, named[("panel", name)], x0, y0, x1 - x0, y1 - y0, repaint=c.images)
        for name in ("ic_law_p_barrim", "ic_lv_barrim"):
            c = LD.get("derpy_ic_panel/" + name)
            if c and c.vis:
                x, y, w, h = G.PANEL_LAYOUT[name]
                paste(panel, named[("panel", name)], x, y, w, h)
        drawn = 0

        def pool(doc, tag, root, grid, layout, cw, ch, n):
            """Every instance the draw showed, at its slot, its cells in the
            file's declaration order - the order the engine draws them in."""
            count = 0
            for i in range(1, n + 1):
                path = "derpy_ic_panel/%s_%d" % (root, i)
                c = LD.get(path)
                if not c or not c.vis:
                    continue
                count += 1
                x, y = grid[i - 1]
                paste(doc, named[(tag, root)], x, y, cw, ch, repaint=c.images or None)
                for key in [k.get("id") for k in doc.components if k.get("id") in layout]:
                    k = LD.get(path + "/" + key)
                    if not k or not k.vis:
                        continue
                    kx, ky, kw, kh = layout[key]
                    comp = named[(tag, key)]
                    paste(doc, comp, x + kx, y + ky, kw, kh, repaint=k.images or None)
                    if k.text:
                        text(doc, comp, k.text, x + kx, y + ky, kw, kh)
            return count

        drawn += pool(law_doc, "law", "derpy_ic_law", G.LAW_GRID, G.LAW_LAYOUT,
                      G.LAW_W, G.LAW_H, len(G.LAW_GRID))
        drawn += pool(lb_doc, "lawblock", "derpy_ic_lawblock", G.LB_GRID, G.LB_LAYOUT,
                      G.LB_W, G.LB_H, len(G.LB_GRID))
        out = path or sized({"law_vote": OUT_LAW_VOTE, "gov_cards": OUT_GOV_CARDS}.get(
            view, OUT_LAW_BOARD), box_w)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        canvas.convert("RGB").save(out)
        return out, n_art, missing, drawn

    # The petitions: a demand, then the offers.
    if view == "petitions":
        rows = petition_rows(G, court)
        # COLUMN TWO RUNS TO REFUSE on this view, and the Lua scales that width
        # by its edges the way every other width is scaled.
        _pw = int(re.search(r"petitions = \{\[2\] = (\d+)\}", ui).group(1))
        _bx = _gen().ROW_LAYOUT["ic_row_b"][0]
        _bw = _gen().sc(_bx + _pw, box_w) - _gen().sc(_bx, box_w)
        for i, r in enumerate(rows):
            rx = G.ROWS_X
            ry = G.ROWS_Y + i * G.ROW_PITCH
            paste(row_doc, named[("row", "derpy_ic_row")], rx, ry, G.ROW_W, G.ROW_H)

            def rcell(key, s=None, repaint=None, w=None, _x=rx, _y=ry):
                cx, cy, cw, ch = G.ROW_LAYOUT[key]
                comp = named[("row", key)]
                paste(row_doc, comp, _x + cx, _y + cy, w or cw, ch, repaint=repaint)
                if s:
                    text(row_doc, comp, s, _x + cx, _y + cy, w or cw, ch)

            if r["face"]:
                # HIS FACE ON HIS HOUSE'S PLATE and the crest beside his name,
                # which is what says whose demand it is, since the party's
                # name is not on the row.
                rcell("ic_row_port", repaint={0: G.plate_path(r["slug"]),
                                              1: r["face"], 2: None})
                rcell("ic_row_crest", repaint={0: G.sigil_path(r["slug"])})
            else:
                # A CREST AS THE ROW'S PICTURE, on its house's plate and at the
                # crest's size: set_row_icon resizes the cell to CREST_W x CREST_H
                # and set_plate still writes the plate under it.
                cx, cy, _cw, _ch = G.ROW_LAYOUT["ic_row_port"]
                paste(row_doc, named[("row", "ic_row_port")], rx + cx, ry + cy,
                      *G.CREST_BOX,
                      repaint={0: G.plate_path(r["slug"]),
                               1: G.sigil_path(r["slug"]), 2: None})
            rcell("ic_row_a", r["a"])
            rcell("ic_row_b", r["b"], w=_bw)
            rcell("ic_row_f", "Refuse")
            rcell("ic_row_e", "Accept" if r["may"] else red("Accept"))

        out = path or sized(OUT_PETITIONS, box_w)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        canvas.convert("RGB").save(out)
        return out, n_art, missing, len(rows)

    # THE KIND OF EACH MAN, BY NAME. The office cards name the same men the
    # picker lists, and reading their kind back out of that one table is what
    # keeps the two pictures saying the same thing about the same officer.
    _demo_kind = dict((r[0], r[7]) for r in DEMO_PICK)
    _kw = _kind_words(ui)

    # The offices: fourteen seats in four bands, half of them empty.
    if view == "offices":
        # THE TWO LADDERS, off the model's own TUNE rather than typed here - a
        # retuned tier reaches the picture the way a renamed column does.
        _mlua = lua("model")
        _bars = [int(n) for n in re.findall(
            r"\d+", re.search(r"tier_influence\s*=\s*\{([^}]*)\}",
                              _mlua).group(1))]
        _ranks = [int(n) for n in re.findall(
            r"\d+", re.search(r"tier_rank\s*=\s*\{([^}]*)\}",
                              _mlua).group(1))]
        for i, office in enumerate(G.IC.OFFICES):
            cx0, cy0 = G.CARD_GRID[i]
            paste(office_doc, named[("office", "derpy_ic_card")],
                  cx0, cy0, G.CARD_W, G.CARD_H)
            held = DEMO_OFFICES.get(i)

            def ccell(key, s=None, repaint=None, _x=cx0, _y=cy0):
                cx, cy, cw, ch = G.CARD_LAYOUT[key]
                comp = named[("office", key)]
                paste(office_doc, comp, _x + cx, _y + cy, cw, ch, repaint=repaint)
                if s:
                    text(office_doc, comp, s, _x + cx, _y + cy, cw, ch)

            if held:
                who, slug, influence, left = held
                ccell("ic_card_port",
                      repaint={0: G.plate_path(slug),
                               1: DEMO_FACES[i % len(DEMO_FACES)],
                               2: DEMO_FACES[0] if slug == "crown" else None})
                ccell("ic_card_crest", repaint={0: G.sigil_path(slug)})
            else:
                # NOBODY, AND NOTHING BEHIND HIM. ICUI.set_vacant_plate writes a
                # transparent png to the plate AND to the mask; the plain plate
                # is an opaque brown box and behind a silhouette it reads as a
                # party whose name nobody wrote down.
                ccell("ic_card_port",
                      repaint={0: G.MASK_NONE, 1: G.SIL_PATH, 2: None})
            def ccut(key, s, _x=cx0, _y=cy0):
                cx, cy, cw, ch = G.CARD_LAYOUT[key]
                comp = named[("office", key)]
                paste(office_doc, comp, _x + cx, _y + cy, cw, ch)
                s = cut_words(lambda _s: measure(office_doc, comp, _s), s, cw)
                if s:
                    text(office_doc, comp, s, _x + cx, _y + cy, cw, ch)

            ccell("ic_card_name", office["name"])
            ccut("ic_card_holder", held[0] if held else "Vacant")
            # THE LINE UNDER HIM IS HIS POSITION, and the crest beside it is his
            # party. The holder cell is 190px and a titled name wants 233 to
            # 295, so the title cannot go in front of the name, and this line is
            # too narrow for a rolled party name anyway.
            #
            # The kind is looked up from the demo roster by NAME rather than
            # carried a second time here, so the two pictures cannot disagree
            # about what a man is.
            ccut("ic_card_house",
                 _kw[_demo_kind[held[0]]]
                 if held and _kw and held[0] in _demo_kind else "")
            # THE BAR THE SEAT ASKS, off the model's own ladder rather than
            # typed - a retuned tier reaches the picture.
            _need = "%s%d rank %d" % (G.COST_MARKUP,
                                       _bars[office["tier"] - 1],
                                       _ranks[office["tier"] - 1])
            ccell("ic_card_need", _need)
            if held:
                _who, _slug, _influence, _left = held
                ccell("ic_card_term", "%d influence; %d turn%s left"
                      % (_influence, _left, "" if _left == 1 else "s"))
                ccell("ic_card_effect",
                      ", ".join(G.IC.effect_short(e, m, t)
                                for e, m, t in office["effects"]))
            else:
                ccell("ic_card_term", "If filled:")
                ccell("ic_card_effect", ", ".join(
                    G.IC.effect_short(e, m, t) for e, m, t in office["effects"]))
            ccell("ic_card_button", "Dismiss" if held else "Appoint")

        out = path or sized(OUT_OFFICES, box_w)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        canvas.convert("RGB").save(out)
        return out, n_art, missing, len(G.IC.OFFICES)

    # The intrigue tab: four columns of move cards.
    if view == "intrigue":
        # The warning, on the bar.
        # draw_intrigue returns the most urgent sentence and the dispatcher
        # writes it to ic_alert. The tab has no band of rows: four cards deep
        # leaves nothing to put it in.
        lines = intrigue_lines(G, court)
        if lines:
            ax, ay, aw, ah = G.PANEL_LAYOUT["ic_alert"]
            bar = named[("panel", "ic_alert")]
            paste(panel, bar, ax, ay, aw, ah)
            warn = lines[0][1]
            # The panel counts other parties with a clock running, never a snub.
            more = sum(1 for l in lines[1:] if "breaks with you in" in l[1])
            if more:
                warn += " (%d more %s moving.)" % (
                    more, "house is" if more == 1 else "houses are")
            text(panel, bar, warn, ax, ay, aw, ah)

        # The column headings.
        cats = plot_cats()
        for col, (_key, title) in enumerate(cats):
            hx, hy, hw, hh = G.PANEL_LAYOUT["ic_plotcat_%d" % (col + 1)]
            hc = named[("panel", "ic_plotcat_%d" % (col + 1))]
            hx, hw = G.fit_plate("ic_plotcat_%d" % (col + 1), hx, hw,
                                 measure(panel, hc, title.upper()))
            paste(panel, hc, hx, hy, hw, hh)
            text(panel, hc, title.upper(), hx, hy, hw, hh)

        # The move cards, one column per category.
        moves = plot_cards(G, race)
        by_cat = {}
        for m in moves:
            by_cat.setdefault(m.cat, []).append(m)
        for col, (key, _title) in enumerate(cats):
            for row, (name, blurb, price, afford, icon, _c) in enumerate(
                    by_cat.get(key, [])):
                gx = G.plot_col_x(col)
                gy = G.PLOTS_Y + row * (G.PLOT_H + G.CARD_GAP_Y)
                paste(card_doc, named[("card", "derpy_ic_plot")],
                      gx, gy, G.PLOT_W, G.PLOT_H)

                def cell(k, txt=None, repaint=None):
                    cx, cy, cw, ch = G.PLOT_LAYOUT[k]
                    c = named[("card", k)]
                    paste(card_doc, c, gx + cx, gy + cy, cw, ch, repaint=repaint)
                    if txt:
                        text(card_doc, c, txt, gx + cx, gy + cy, cw, ch)

                cell("ic_plot_icon", repaint={0: icon})
                cell("ic_plot_name", name)
                # THE BLURB ACROSS ITS THREE CELLS, split the way ICUI.fit_lines
                # splits it - greedily, on whole words, against the cell's width.
                # PIL's font is narrower than the game's, so this is OPTIMISTIC:
                # a blurb that just fits here may take a line more in game.
                bc = named[("card", "ic_plot_b1")]
                bw = G.PLOT_LAYOUT["ic_plot_b1"][2]
                words, li = blurb.split(), 1
                cur = ""
                for w in words:
                    trial = (cur + " " + w).strip()
                    if cur and measure(card_doc, bc, trial) > bw:
                        if li <= G.PLOT_BLURB_LINES:
                            cell("ic_plot_b%d" % li, cur)
                        li, cur = li + 1, w
                    else:
                        cur = trial
                if cur and li <= G.PLOT_BLURB_LINES:
                    cell("ic_plot_b%d" % li, cur)
                cell("ic_plot_cost", price)
                cell("ic_plot_go", "Plot" if afford else red("Plot"))

        out = path or sized(OUT_INTRIGUE, box_w)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        canvas.convert("RGB").save(out)
        return out, n_art, missing, len(lines) + len(moves)

    # The party cards.
    # ICUI.trait_line's own rule: an empty cell stays empty rather than
    # carrying a picture of nothing.
    def trait_markup(name):
        if not name:
            return name
        return "[[img:%s]][[/img]]%s" % (trait_icon, name)

    # THE WORDS THE CARD DRAWS RED and the three counts' wording, off the Lua.
    _mood_red = set(re.findall(r"(\w+) = true", re.search(
        r"ICUI\.MOOD_RED = \{(.*?)\}", ui, re.S).group(1)))
    _counts = dict((m.group(1), m.group(2, 3, 4)) for m in re.finditer(
        r'"ic_party_(\w+)",\s*count\([^,]+,\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)"\)',
        ui))
    _steady = re.search(r'"(Loyalty steady)"', ui).group(1)
    _moving = re.search(r'"(Loyalty %s a turn)"', ui).group(1)

    def count_text(key, n):
        one, many, none = _counts[key]
        return none if n == 0 else "%d %s" % (n, one if n == 1 else many)

    for i, (slug, title, share, loyalty, leader, ltrait) in enumerate(court):
        gx, gy = G.PARTY_GRID[i]
        # THE CHOSEN CARD WEARS CA'S GOLD FRAME in image slot 2; every other
        # card has the transparent png there, which is what fill_party writes.
        paste(party, named[("party", "derpy_ic_party")], gx, gy, G.PARTY_W, G.PARTY_H,
              repaint={G.PARTY_SEL_INDEX: (G.PARTY_SELECTED if i == DEMO_SEL
                                           else G.MASK_NONE)})

        def cell(name, s=None, repaint=None):
            cx, cy, cw, ch = G.PARTY_LAYOUT[name]
            comp = named[("party", name)]
            paste(party, comp, gx + cx, gy + cy, cw, ch, repaint=repaint)
            if s:
                text(party, comp, s, gx + cx, gy + cy, cw, ch)

        cell("ic_party_crest", repaint={0: G.sigil_path(slug)})
        # THE TWO-LINE SPLIT, which is the whole reason the card has a second name
        # cell. The Lua splits on a word with the engine's own measurement; PIL's
        # font is narrower than the game's, so this splits at the widest word that
        # still fits by PIL and is therefore OPTIMISTIC - a name that only just
        # fits here may take two lines in game.
        line1, line2 = fit_two(party, named[("party", "ic_party_name")], title,
                               G.PARTY_LAYOUT["ic_party_name"][2],
                               G.PARTY_LAYOUT["ic_party_name2"][2])
        cell("ic_party_name", line1)
        cell("ic_party_name2", line2)
        # THE MASK IS THE CROWN'S ALONE - set_plate hands it a faction and a party is not
        # one - so slot 2 stays undrawn on the other eight cards.
        #
        # AND A PARTY WITH NOBODY AT ITS HEAD GETS THE SILHOUETTE, which is what
        # ICUI.fill_party does. Drawing a face here regardless made the preview
        # lie about the one cell it was asked to show: the demo's third party
        # has no leader and the picture said it had.
        cell("ic_party_port", repaint={0: G.plate_path(slug),
                                       1: (DEMO_FACES[i % len(DEMO_FACES)]
                                           if leader else G.SIL_PATH),
                                       2: DEMO_FACES[0] if slug == "crown" else None})
        cell("ic_party_leader", leader or "No one speaks for them")
        # DECORATED, because ICUI.trait_line is what the panel writes into
        # these three. Drawing the bare name here would hide the decoration in
        # the one place it gets reviewed.
        cell("ic_party_ltrait", trait_markup(ltrait))
        cell("ic_party_nums", "%d%% share - %d loyalty" % (share, loyalty))
        cell("ic_party_t1", trait_markup(DEMO_TRAITS[slug][0]))
        cell("ic_party_t2", trait_markup(DEMO_TRAITS[slug][1]))
        # THE STATE WORD, red where the panel draws it red.
        word = DEMO_STATE[i]
        cell("ic_party_state", red(word) if word.split()[0] in _mood_red else word)
        cell("ic_party_trend", _steady if DEMO_TREND[i] == 0
             else _moving % ("%+d" % DEMO_TREND[i]))
        # THE THREE COUNTS, off the demo's own tables so the court and the
        # other pictures describe one court: its seats on the offices picture,
        # its provinces on the governors picture, and as members every man
        # either of those or the picker's roster files under it. A party nobody
        # leads has no men, so it holds nothing - an office with no member
        # behind it is a state the model cannot reach.
        seats = [o[0] for o in DEMO_OFFICES.values() if o[1] == slug] if leader else []
        lands = [g[1] for g in DEMO_GOVS if g[2] == slug] if leader else []
        men = set(seats + lands + [r[0] for r in DEMO_PICK if r[2] == i]) if leader else ()
        cell("ic_party_members", count_text("members", len(men)))
        cell("ic_party_offices", count_text("offices", len(seats)))
        cell("ic_party_govs", count_text("govs", len(lands)))

    out = path or sized(OUT, box_w)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    canvas.convert("RGB").save(out)
    return out, n_art, missing, len(court)


def selftest():
    model, _r = PG._studio()
    G = _gen()

    # The reader must actually read OURS. A parse that silently returned nothing would
    # make validate() pass on any file at all.
    # AND IT MUST READ THE COMPACT COPY TOO: a small screen opens that file.
    for _name in ("derpy_ic_party.twui.xml", G.COMPACT_FILES["derpy_ic_party.twui.xml"]):
        doc = model.Document(io.open(os.path.join(PG.OURS, _name),
                                     encoding="utf-8").read())
        names = {c.get("id", c.tag) for c in doc.components}
        for want in sorted(G.PARTY_LAYOUT):
            assert want in names, "TWUI Studio does not see %s in %s" % (want, _name)
        assert "derpy_ic_party" in names, "%s has no root component" % _name
    # THE SIZES ARE THE GENERATOR'S, and the canvas is the box: a preview
    # drawn at one width from another width's numbers is a picture of nothing.
    for _bw in SIZES:
        assert _gen_at(_bw).PANEL_W == _bw, "the %d preview is %d wide" % (
            _bw, _gen_at(_bw).PANEL_W)
    assert sized(OUT, 1600).endswith("ic_court_1600.png") and sized(OUT, 1920) == OUT

    # And it must be capable of REPORTING a fault, or a clean run proves nothing. Break a
    # hierarchy node's link to its definition, the way a bad GUID does.
    src = io.open(os.path.join(PG.OURS, "derpy_ic_party.twui.xml"),
                  encoding="utf-8").read()
    broken = src.replace('this="IC35', 'this="ZZ99', 1)
    assert broken != src, "could not break a guid for the negative test"
    assert model.Document(broken).issues, (
        "TWUI Studio reported nothing on a broken GUID link, so a clean report from it "
        "proves nothing")

    assert not validate(), "our shipped files do not validate: %r" % (validate(),)

    # The coordinates this draws with have to be readable from here. A rename in the
    # generator would otherwise silently preview a panel of the wrong shape.
    for attr in ("PANEL_W", "PANEL_H", "PANEL_LAYOUT", "PARTY_LAYOUT", "PARTY_GRID",
                 "PARTY_W", "PARTY_H", "DIAL_BOX", "RIM_BOX", "PIE_BOX", "DIAL_SLICES",
                 "DIAL_CX", "DIAL_CY", "CREST_R", "CREST_PX", "SHARE_R", "SHARE_W",
                 "SHARE_H", "TEXT_STYLE", "wedge_path", "div_path", "sigil_path",
                 "plate_path"):
        assert hasattr(G, attr), "gen_ic_ui.py no longer exposes %s" % attr

    # The split has to fill the dial exactly. A preview that drew 59 of 60 slices would
    # leave a sliver of bare plate that reads as a rendering fault in the panel.
    court = demo_court(G)
    counts = slice_counts(G.DIAL_SLICES, court)
    assert sum(counts) == G.DIAL_SLICES, "the demo court fills %d of %d slices" % (
        sum(counts), G.DIAL_SLICES)
    assert len(counts) == len(court) and min(counts) > 0, "a demo party got no slices"
    # THE DEMO MUST BE THE HARD CASE. A court that fits the grid comfortably, or
    # names short enough never to need the second line, is a picture of nothing.
    assert len(court) >= 6, "the demo court shrank below a full grid of six"
    assert max(len(row[1]) for row in court) >= 30, (
        "the demo names are too short to exercise the card's two-line split")

    # Every picture the COURT TAB paints at runtime has to be on disk, which is a
    # different question from whether the .twui.xml's declared art is: the wedges, the
    # sigils and the plates are named by string in the Lua and appear in no file the
    # validator reads. A missing one draws nothing at all, silently.
    for slug, _title, _s, _l, _n, _t in court:
        for p in (G.sigil_path(slug), G.plate_path(slug), G.wedge_path(0, slug)):
            assert _asset(p), "the court tab paints %s and it is not on disk" % p
    assert _asset(G.div_path(1)), "the dial's walls are not on disk"

    # The intrigue view.
    # THE MOVES MUST COME OUT OF THE MODEL, all of them and priced. A parse that
    # silently returned four of nine, or a cost of zero, would draw a list that
    # looked right and was a picture of a different panel.
    plots = read_plots()
    # Counted a second way, off a different cut of the file: everything before
    # IC.FAVOURS, which is the only other table in the model written in this
    # shape. A chunk splitter that swallowed an entry would agree with itself.
    declared = re.findall(
        r'\{key = "(\w+)"',
        lua("model").split("IC.PLOTS = {")[1].split("IC.FAVOURS")[0])
    assert [p.key for p in plots] == declared, (
        "read_plots found %r and the model declares %r" % ([p.key for p in plots],
                                                           declared))
    assert len(plots) >= 9, "the move list shrank to %d" % len(plots)
    assert all(p.cost > 0 for p in plots), "a move parsed at no price"
    # A BLURB MUST PARSE WHOLE, which is not the same as being long ("He comes
    # under your standard." is a deliberate 29 characters). What this guards is
    # the regex picking up only the FIRST literal of a blurb written as several
    # concatenated ones, and a truncated parse ends mid-sentence with no full stop.
    for p in plots:
        assert p.blurb.strip().endswith("."), (
            "%s's blurb does not end in a full stop, so it parsed truncated: %r"
            % (p.key, p.blurb))
    # AND EVERY LITERAL OF IT WAS READ: n literals joined by n - 1 "..". Not a
    # word count: "The court watches." is three deliberate words.
    for chunk in re.split(r"\n    \{", _block(lua("model"), "IC.PLOTS"))[1:]:
        tail = chunk.split("blurb =")[1].split("}")[0]
        assert len(re.findall(r'"([^"]*)"', tail)) == tail.count("..") + 1, (
            "a blurb has literals the parser did not read: %r" % tail)
    # AND THE EFFECT LINE RESOLVED. An unresolved "%d" on the card is a number
    # the player never sees and a measurement nine characters short of the truth.
    for p in plots:
        assert p.effect and "%d" not in p.effect, (
            "%s's effect line did not resolve: %r" % (p.key, p.effect))
        # NOT THE ODDS. draw_pick already writes them on each candidate's own
        # button, live, from IC.plot_chance; a card can only carry the base, and
        # the two differ by the actor's standing edge on every aimed move.
        assert "odds" not in p.effect, (
            "%s's card states odds the picker already shows: %r"
            % (p.key, p.effect))
    # A CIVIL MISSION IS EXACTLY ONE COLUMN, which is the property the tab's
    # layout rests on: a move with nobody to aim at goes straight to the actor
    # picker, and the reader is told which those are by the column they sit in.
    #
    # NOT A COUNT, AND NOT ONE COLUMN: Missions and Errands both hold unaimed
    # moves, one naming a place or a faction instead. What the reader relies on
    # is that no column MIXES the two kinds.
    _unaimed = [p for p in plots if not p.aimed]
    assert _unaimed, "no move is unaimed, so the actor-only route is undrawn"
    for _civil_cat in sorted(set(p.cat for p in _unaimed)):
        assert all(not p.aimed for p in plots if p.cat == _civil_cat), (
            "%r holds an aimed move as well as the civil ones - the tab cannot "
            "say which moves have no victim" % (_civil_cat,))

    # AND THE DEMO PURSES MUST STRADDLE THE PRICES, or the red the tab was asked
    # to show is not on the picture at all - or is on every row, which says as
    # little. One of each, on each purse.
    aimed_red = [p.name for p in plots if p.aimed and p.cost > DEMO_PURSE]
    civil_red = [p.name for p in plots
                 if not p.aimed and p.cost > DEMO_PURSE_CIVIL]
    # ONE OF EACH, ON EACH PURSE - stated as a straddle rather than as a count.
    # "fewer than two red errands" was the old second half, which was a straddle
    # while Errands held two moves and an accident afterwards: it passed only
    # because the purse happened to refuse one, and it would have gone on passing
    # with a purse that afforded every single one.
    _n_aimed = sum(1 for p in plots if p.aimed)
    _n_civil = len(plots) - _n_aimed
    for _what, _red, _n in (("aimed", aimed_red, _n_aimed),
                            ("civil", civil_red, _n_civil)):
        assert _red, ("the demo court affords every %s move, so the tab's "
                      "refusal colour is not on the picture at all" % _what)
        assert len(_red) < _n, ("the demo court affords no %s move, so every "
                                "row of that column is red and says as little"
                                % _what)

    # THE WARNINGS FEED THE ALERT BAR and nothing else (ICUI.rows_shown("intrigue")
    # is 0). The bar draws lines[0] and counts the rest, so an empty list draws no
    # bar and a warning carrying a price or a button would draw a control the bar
    # has no room for.
    lines = intrigue_lines(G, demo_court(G))
    assert lines, "the demo court raises no warning, so the alert bar is undrawn"
    assert all(l[1].strip() for l in lines), "a warning has no sentence to draw"
    assert all(not l[0] and not l[4] for l in lines), (
        "a warning was given a price or a button, and the alert bar draws neither")

    # THE MARKUP MUST COME APART. A price is an icon and a number, and a refused
    # one is that wrapped in a colour: if segments() returned the string whole the
    # preview would print the tags, and if it dropped the image the red rows would
    # quietly lose their icon - which is the exact fault ICUI.red was written to
    # avoid.
    # ON THE CARDS NOW, not the rows. Same check, same reason - it reads the
    # price strings wherever the price strings are, and after the tab became
    # columns they are the cards' third cell.
    priced = [c.price for c in plot_cards(G)]
    plain = [s for s in priced if not s.startswith("[[col:")]
    refused = [s for s in priced if s.startswith("[[col:")]
    assert plain and refused, "the demo list has no priced card of one of the kinds"
    for s, want_red in [(plain[0], False), (refused[0], True)]:
        parts = segments(s)
        assert [k for k, _b, _c in parts] == ["img", "text"], (
            "a price came apart as %r" % ([k for k, _b, _c in parts],))
        assert all((c == "red") == want_red for _k, _b, c in parts), (
            "the colour of %r did not survive the split" % s)
    assert segments("plain") == [("text", "plain", None)], "unmarked text was mangled"

    # AND THE COST ICON HAS TO EXIST IN CA'S PACKS. It is named in the Lua and in
    # no .twui.xml, so the validator never sees it and a missing imagepath draws a
    # blank square while reporting nothing at all.
    icon = segments(plain[0])[0][1]
    assert icon not in PG.extract_art(PREFIX, extra=[icon])[1], (
        "the cost icon %s is in no ui pack" % icon)

    # CA'S RED, still where it was read from - and the panel's colour NAME still a
    # name CA ships. The engine drops an unknown one SILENTLY, leaving ordinary
    # ink and no error, so nothing else in this mod could ever notice ICUI.RED
    # being typed wrong: the harness builds its own needle out of that same
    # constant, which is exactly the shape of check that cannot fail.
    #
    # The cache is optional - it needs RPFM to create, and a game patch deletes
    # .skilltree_cache - so this is skipped when it is absent rather than
    # asserted vacuously.
    try:
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import read_vanilla_cache as _V
        _rows = _V.load("ui_colours")[0]
    except (ImportError, FileNotFoundError, IndexError, ValueError):
        _rows = []
    if _rows:
        # The cached definition's field NAMES are shifted against its data - the
        # key is under "blue" and the hex under "description" - so both are taken
        # positionally the way they read, and the lookup below fails loudly
        # rather than quietly finding nothing if that ever changes.
        by_key = dict((r["blue"], r["description"].upper()) for r in _rows)
        assert by_key.get("black") == "000000", "db/ui_colours_tables has no black 000000"
        assert by_key.get("red") == "%02X%02X%02X" % RED_INK[:3], (
            "db/ui_colours_tables calls red %s, not %s"
            % (by_key.get("red"), "%02X%02X%02X" % RED_INK[:3]))
        name = re.search(r'ICUI\.RED = "([^"]+)"', lua("ui")).group(1)
        assert name in by_key, (
            "the panel colours its refusals [[col:%s]] and db/ui_colours_tables "
            "has no such row - the engine drops an unknown name silently" % name)

    # THE PETITIONS PICTURE READS ITS WORDS OUT OF THE LUA, so a reworded row
    # must fail here rather than draw a sentence the panel no longer writes.
    _label = petitions_label()
    assert "%" not in _label and str(_party_tune()["party_demand_met"]) in _label, (
        "the petitions label resolved to %r" % _label)
    _rows = petition_rows(G, court)
    assert _rows[0]["a"] == DEMO_LONG_MAN and DEMO_LONG_PROVINCE in _rows[0]["b"], (
        "the demand row is not the hard case: %r" % (_rows[0],))
    assert any(not r["may"] for r in _rows) and any(r["may"] for r in _rows), (
        "the petitions picture needs one refused ACCEPT and one that is not")
    # AND THE CARD'S NEW CELLS ARE IN THE FILE THE PICTURE DRAWS.
    for _cell in ("ic_party_state", "ic_party_trend", "ic_party_members",
                  "ic_party_offices", "ic_party_govs"):
        assert _cell in G.PARTY_LAYOUT, "the party card has no %s" % _cell

    # THE GOVERNORS VIEW'S COLUMN IS ITS OWN. Every other picture hides every
    # ic_gm_ cell - PANEL_LAYOUT carries them for all views, and the static pass
    # draws whatever is not hidden - and the Governors pictures hide only what
    # ICUI.gm_draw_column hides on that page.
    _G = _gen()
    _gm = set(n for n in _G.PANEL_LAYOUT if n.startswith("ic_gm_"))
    assert _gm, "PANEL_LAYOUT has no ic_gm_ cells: Task 3 is not in"
    for _v in VIEWS:
        if not _v.startswith("gm_"):
            assert gm_hidden(_G, _v, 0) >= _gm, "%s draws the Governors column" % _v
    _prov = gm_hidden(_G, "gm_provinces", _G.GM_ROWS)
    assert "ic_gm_col" not in _prov and "ic_gm_sort_1" not in _prov and "ic_gm_hint" in _prov
    assert "ic_gm_sort_1" not in gm_hidden(_G, "gm_picker", 1), "a picker with men draws no sorts"
    assert "ic_gm_sort_1" in gm_hidden(_G, "gm_picker", 0), "an empty picker draws sorts over its hint"
    # AND THE MAP SHOWS THROUGH: the court's backdrop is not drawn on this view.
    _out = os.path.join(PG.CACHE, "selftest_gm.png")
    render(path=_out, view="gm_provinces")
    from PIL import Image
    assert Image.open(_out).convert("RGBA").getpixel((1800, 600)) == GM_MAP_FILL, (
        "the Governors picture drew the backdrop over the map")

    # The Dwarf court's dump.
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

    # The Dwarf pictures.
    assert INK_OF["black"] == (0, 0, 0, 255)
    assert segments("[[col:black]]Offices[[/col]]") == [("text", "Offices", "black")]
    assert raced(OUT_OFFICES, "dwf").endswith("ic_offices_dwf.png")
    assert sized(raced(OUT_OFFICES, "dwf"), 1600).endswith("ic_offices_dwf_1600.png")
    out, _n, problems, drawn = render(view="offices", box_w=1920, race="dwf")
    assert not problems, problems
    assert drawn > 100, "the Dwarf offices picture drew %d components" % drawn

    print("selftest ok: %d files validate, the card's %d cells are all seen, the "
          "%d moves read %d rows, the reader catches a broken link"
          % (len(PG.our_files(PREFIX)), len(G.PARTY_LAYOUT), len(plots), len(lines)))


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    elif "--check" in sys.argv:
        problems = validate()
        for p in problems:
            print("PROBLEM: " + p)
        print("%d file(s) checked by TWUI Studio's reader" % len(PG.our_files(PREFIX)))
        sys.exit(1 if problems else 0)
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
