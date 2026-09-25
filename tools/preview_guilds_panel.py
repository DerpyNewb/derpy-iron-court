# -*- coding: utf-8 -*-
"""Render the Great Guilds panel to a PNG with the game shut, and validate its XML.

WHY THIS EXISTS. Every UI bug this mod has shipped was a SILENT one - a GUID with no
hierarchy node, a component with no image, a clickable thing that was not interactive, a
list that drew and would not scroll - and the only way to see any of them was to start a
campaign and look. That is a slow loop, and the last one shipped because the contract was
checked and the picture never was.

TWO INDEPENDENT THINGS HAPPEN HERE:

  1. VALIDATE. TWUI Studio's own document reader links <hierarchy> to <components> the way
     the engine does and reports every mismatch - a reader written by another modder from
     CA's files, with no knowledge of our generator. An independent second opinion on the
     GUID discipline that gen_guilds_ui.py enforces from the inside.

  2. DRAW. Its rasteriser decodes and nine-slice scales CA's art the way the game does, so
     the panel can be looked at without launching anything.

WHY IT DOES NOT JUST OPEN THE FILE IN TWUI STUDIO. Our .twui.xml files carry NO offsets.
The engine ignores them on a runtime-created component, so zzz_derpy_guilds_ui.lua MoveTo's
every piece instead - meaning a faithful preview of the file alone draws the whole panel
stacked in one corner. The coordinates live in gen_guilds_ui.py, and this reads them from
there. It also honours the per-tab visibility the Lua applies, because a preview that draws
every declared component is a preview of the FILE and not of the TAB.

WHAT IT IS NOT. Text is PIL's own font, not the game's, so glyph widths and wrapping are
approximate and this cannot answer a "does that label fit" question - gen_great_guilds.py's
help-fit check and the game itself own that. Everything positional is exact. It does not
run Lua, so it draws a plausible set of contents, not your save's.

    py tools/preview_guilds_panel.py            # render to .skilltree_cache/ui_preview/
    py tools/preview_guilds_panel.py slavers    # ... with that guild's baked ground
    py tools/preview_guilds_panel.py --check    # validate the XML only, no PNG
    py tools/preview_guilds_panel.py --selftest

Vendored source: TWUI_Studio/src (non-commercial licence, see its LICENSE.txt).
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STUDIO = os.path.join(ROOT, "TWUI_Studio", "src")
OURS = os.path.join(ROOT, "Modding Files", "pack", "ui", "campaign ui")
CACHE = os.path.join(ROOT, ".skilltree_cache", "ui_preview")
UI = os.path.join(CACHE, "ui")
GAME = r"F:\SteamLibrary\steamapps\common\Total War WARHAMMER III\data"
PACKS = ("ui.pack", "ui2.pack", "ui3.pack")


def _studio():
    """Import TWUI Studio's model and renderer. It reads its catalogs from its own cwd."""
    if not os.path.isdir(STUDIO):
        raise SystemExit("TWUI_Studio/src is not present - vendor the 0.22.2 source there")
    here = os.getcwd()
    sys.path.insert(0, STUDIO)
    os.chdir(STUDIO)
    try:
        import model
        import rendering
    finally:
        os.chdir(here)
    return model, rendering


def _gen():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "gen_guilds_ui", os.path.join(ROOT, "tools", "gen_guilds_ui.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("gen_guilds_ui", mod)
    spec.loader.exec_module(mod)
    return mod


# WHICH PANEL. The three reusable halves below - the file list, the validator and
# the art extractor - are about a PREFIX and not about the guilds, so the Iron
# Court's preview imports them rather than owning a second copy that can drift.
GG = "derpy_gg_"


def our_files(prefix=GG):
    return sorted(f for f in os.listdir(OURS)
                  if f.startswith(prefix) and f.endswith(".twui.xml"))


def validate(prefix=GG):
    """Every hierarchy node must resolve to exactly one component definition.

    A GUID in <components> with no <hierarchy> node is a silent non-draw, and the reverse is
    a node the engine cannot build. gen_guilds_ui.py checks this from inside the generator;
    this checks the FILES, with a reader that has never heard of the generator.
    """
    model, _r = _studio()
    out = []
    for name in our_files(prefix):
        src = io.open(os.path.join(OURS, name), encoding="utf-8").read()
        try:
            doc = model.Document(src)
        except Exception as exc:                                   # noqa: BLE001
            out.append("%s: TWUI Studio cannot parse it: %r" % (name, exc))
            continue
        for i in getattr(doc, "issues", []):
            tags = ", ".join(sorted({n.tag for n in i.nodes})) or "-"
            out.append("%s: [%s] %s (%s) %s" % (name, i.severity, i.code, tags, i.message))
        for keys, what in ((getattr(doc, "unsafe_keys", ()), "duplicate guid"),
                           (getattr(doc, "missing_keys", ()), "missing definition"),
                           (getattr(doc, "unlinked_keys", ()), "unlinked node")):
            for k in sorted(keys):
                tag = doc.by_guid[k].tag if k in doc.by_guid else k
                out.append("%s: %s on %s" % (name, what, tag))
    return out


def extract_art(prefix=GG, extra=()):
    """Pull only the art our files reference out of CA's packs, once, into the cache.

    TWUI Studio wants an extracted top-level `ui` folder and will not read .pack files. The
    whole library is over 40,000 assets; this panel touches eighteen. CA's ui png is zstd
    behind a u32 length prefix - the wrapper tools/read_vanilla_loc.py already strips.
    """
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    from read_pack_index import paths, read
    from read_vanilla_loc import _decompress

    want = set(extra)
    for f in our_files(prefix):
        t = io.open(os.path.join(OURS, f), encoding="utf-8").read()
        want |= set(re.findall(r'imagepath="([^"]+)"', t))

    def dest(p):
        return os.path.join(UI, os.path.relpath(p, "ui").replace("/", os.sep))

    todo = [p for p in sorted(want) if not os.path.isfile(dest(p))]
    if not todo:
        return len(want), []

    local = os.path.join(ROOT, "Modding Files", "pack")
    missing, still = [], []
    for p in todo:
        src = os.path.join(local, p.replace("/", os.sep))
        if os.path.isfile(src):                      # this mod's own art
            os.makedirs(os.path.dirname(dest(p)), exist_ok=True)
            io.open(dest(p), "wb").write(io.open(src, "rb").read())
        else:
            still.append(p)

    if still:
        index = {}
        for pk in PACKS:
            fp = os.path.join(GAME, pk)
            if os.path.isfile(fp):
                for e in paths(fp):
                    index.setdefault(e, pk)
        for p in still:
            pk = index.get(p)
            if not pk:
                missing.append(p)
                continue
            data = b""
            for _path, comp, blob in read(os.path.join(GAME, pk), p):
                data = _decompress(blob) if comp else blob
            if not data or data[:4] != b"\x89PNG":
                missing.append(p)
                continue
            os.makedirs(os.path.dirname(dest(p)), exist_ok=True)
            io.open(dest(p), "wb").write(data)
    return len(want), missing


# The tab this renders. Standings is the one with the faction list on it.
HIDDEN_ON_STANDINGS = ("gg_prev", "gg_next", "gg_rep_bar", "gg_bar_track")

DEMO_FACTIONS = ("You", "Uzkul Mingol Company", "Slaves of the Black Dwarf",
                 "Labourfleet of Uzkulak", "Disciples of Hashut",
                 "The Legion of Azgorh", "Sentinels of Zharr", "Drazhoath's Host")


def render(path=None, guild=None, tag=""):
    """Draw the panel. `guild` swaps the ground for that guild's baked background.

    THE GROUND IS NOT IN THE .twui.xml. The file names CA's tier_01 background and the
    campaign Lua replaces image index 1 at runtime as the player pages from guild to
    guild, so a preview that only reads the file draws the one ground nobody with the
    mod installed ever sees.
    """
    from PIL import Image, ImageDraw
    from pathlib import Path
    model, rendering = _studio()
    G = _gen()
    n_art, missing = extract_art()
    ground = None
    if guild:
        ground = Path(os.path.join(OURS, "derpy_gg_bg", guild + tag + ".png"))
        if not ground.is_file():
            raise SystemExit("no baked ground for %r: %s (py tools/"
                             "make_guild_backgrounds.py writes them)" % (guild, ground))

    def doc_of(name):
        return model.Document(io.open(os.path.join(OURS, name), encoding="utf-8").read())

    panel, row, lst = (doc_of("derpy_gg_panel.twui.xml"), doc_of("derpy_gg_row.twui.xml"),
                       doc_of("derpy_gg_list.twui.xml"))
    named = {}
    for d, kind in ((panel, "panel"), (row, "row"), (lst, "list")):
        for c in d.components:
            named[(kind, c.get("id", c.tag))] = c

    canvas = Image.new("RGBA", (G.PANEL_W, G.PANEL_H), (0, 0, 0, 255))

    def paste(doc, comp, x, y, w=None, h=None):
        images = {}
        box = comp.child("componentimages")
        if box is not None:
            for n in box.children:
                if n.get("this"):
                    images[n.get("this")] = n.get("imagepath")
        st = doc.state(comp)
        metrics = st.child("imagemetrics") if st is not None else None
        if metrics is None:
            return
        for n in metrics.children:
            p = images.get(n.get("componentimage"))
            if not p:
                continue
            asset = Path(os.path.join(UI, os.path.relpath(p, "ui").replace("/", os.sep)))
            if ground is not None and p == G.PANEL_ART:
                asset = ground
            # OUR OWN ART is not in CA's packs, so it is read where it is staged, in the
            # flavour asked for - the Lua appends the same tag at runtime (GGUI.art).
            if p.startswith("ui/campaign ui/derpy_gg_"):
                stem, ext = os.path.splitext(os.path.relpath(p, "ui/campaign ui"))
                asset = Path(os.path.join(OURS, stem + tag + ext))
            if not asset.is_file():
                continue
            iw = int(model.number(n.get("width"), w or 0)) or (w or 1)
            ih = int(model.number(n.get("height"), h or 0)) or (h or 1)
            ox, oy = model.pair(n.get("offset"), (0, 0))
            canvas.alpha_composite(rendering.raster(asset, iw, ih, n),
                                   (int(x + ox), int(y + oy)))

    paste(panel, named[("panel", "derpy_gg_panel")], 0, 0, G.PANEL_W, G.PANEL_H)
    for name, (x, y, w, h) in sorted(G.PANEL_LAYOUT.items()):
        if name.startswith(("gg_help_", "gg_card_")) or name in HIDDEN_ON_STANDINGS:
            continue
        c = named.get(("panel", name))
        if c is not None:
            paste(panel, c, x, y, w, h)

    draw = ImageDraw.Draw(canvas)
    pale, gold = (235, 225, 200, 255), (255, 211, 122, 255)
    draw.text((58, 18), "The Great Guilds", fill=pale)
    # Pitch read off the generator's own TABS, so a re-pitched strip draws where it is.
    for i, lbl in enumerate(("Guilds", "Leaderboard", "Bounties", "Court", "Log", "Help")):
        draw.text((20 + i * G.TAB_W + 40, 68), lbl, fill=gold if i == 1 else pale)
    draw.text((24, 110), "Hover a row for the full table.   Rivals last turn: 0 services "
                         "bought, 0 demands paid, 0 patrons afield", fill=pale)

    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import gen_great_guilds as GEN
    low = GEN.FLAVOURS[tag]["ranks"][0]          # the flavour's own lowest rank
    for i, g in enumerate(GEN.FLAVOURS[tag]["guilds"][k] for k in GEN.GUILDS):
        ry = 170 + i * 44
        paste(row, named[("row", "derpy_gg_row")], 20, ry, G.ROW_W, G.ROW_H)
        sel = (i == 0)
        for dx, s in ((14, g),
                      (212, "You: %s (%d)  %d/8" % (low, 9 if sel else 0, 1 if sel else 5)),
                      (416, "Leader: " + ("You" if sel else "Nobody yet"))):
            draw.text((20 + dx, ry + 14), s, fill=gold if sel and dx == 14 else pale)

    lx, ly = G.LIST_XY
    cx, cy, cw, ch = G.LIST_LAYOUT["list_clip"]
    vx, vy, vw, vh = G.LIST_LAYOUT["vslider"]
    paste(lst, named[("list", "vslider")], lx + vx, ly + vy, vw, vh)
    paste(lst, named[("list", "handle")], lx + vx, ly + vy, G.SLIDER_W, G.HANDLE_H)

    clip = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    cd = ImageDraw.Draw(clip)
    for i, f in enumerate(DEMO_FACTIONS):
        ry = i * G.FROW_H
        if ry >= ch:
            break
        cd.rectangle([2, ry + 2, 22, ry + 22], outline=(120, 100, 70, 255))
        cd.text((28, ry + 6), "%d.  %s   %d   %s" % (i + 1, f, 9 if i == 0 else 0, low),
                fill=gold if i == 0 else pale)
    canvas.alpha_composite(clip, (lx + cx, ly + cy))
    draw.rectangle([lx + cx, ly + cy, lx + cx + cw, ly + cy + ch], outline=(90, 80, 60, 255))
    draw.text((24, 646), "Favour: 9", fill=pale)

    out = path or os.path.join(CACHE, "gg_standings%s%s.png"
                               % (guild and "_" + guild or "", tag))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    canvas.convert("RGB").save(out)
    return out, n_art, missing, (ch // G.FROW_H, len(DEMO_FACTIONS))


def selftest():
    model, rendering = _studio()
    G = _gen()

    # The reader must actually read ours - a parse that silently returns nothing would make
    # validate() pass on anything.
    doc = model.Document(io.open(os.path.join(OURS, "derpy_gg_list.twui.xml"),
                                 encoding="utf-8").read())
    assert len(doc.components) >= 5, "the list file has a container, clip, box, slider, handle"
    names = {c.get("id", c.tag) for c in doc.components}
    for want in ("listview", "list_clip", "list_box", "vslider", "handle"):
        assert want in names, "TWUI Studio does not see %s in our list file" % want

    # And it must be capable of REPORTING a fault, or a clean run means nothing. Break the
    # link between a hierarchy node and its definition, the way a bad GUID does.
    src = io.open(os.path.join(OURS, "derpy_gg_row.twui.xml"), encoding="utf-8").read()
    broken = src.replace('this="GG21', 'this="ZZ99', 1)
    assert broken != src, "could not break a guid for the negative test"
    assert model.Document(broken).issues, (
        "TWUI Studio reported nothing on a broken GUID link, so a clean report from it "
        "proves nothing")

    assert not validate(), "our shipped files do not validate: %r" % (validate(),)

    # The generator's coordinates have to be readable from here, since they are what this
    # draws with. A rename there would otherwise silently draw a panel of the wrong shape.
    for attr in ("PANEL_W", "PANEL_H", "PANEL_LAYOUT", "LIST_XY", "LIST_LAYOUT",
                 "ROW_W", "ROW_H", "FROW_H", "SLIDER_W", "HANDLE_H"):
        assert hasattr(G, attr), "gen_guilds_ui.py no longer exposes %s" % attr
    print("selftest ok: %d files validate, the reader catches a broken link"
          % len(our_files()))


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    elif "--check" in sys.argv:
        problems = validate()
        for p in problems:
            print("PROBLEM: " + p)
        print("%d file(s) checked by TWUI Studio's reader" % len(our_files()))
        sys.exit(1 if problems else 0)
    else:
        problems = validate()
        for p in problems:
            print("PROBLEM: " + p)
        args = sys.argv[1:]
        tag = ""
        if "--flavour" in args:
            at = args.index("--flavour")
            tag = "_" + args[at + 1]
            del args[at:at + 2]
        want = [a for a in args if not a.startswith("--")]
        out, n_art, missing, (shown, total) = render(guild=want[0] if want else None,
                                                     tag=tag)
        for m in missing:
            print("  art not found in any ui pack: " + m)
        print("wrote %s  (%d art files, %d of %d faction rows visible)"
              % (out, n_art, shown, total))
        sys.exit(1 if problems else 0)
