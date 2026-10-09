# -*- coding: utf-8 -*-
"""Cut the Iron Court's backdrops and prove the panel's text still reads on them.

The Chaos Dwarf ground is the win-movie keyframe with its bottom 140 rows (the logo and
the credit bar) cut; the Dwarf ground is CA's Dwarf loading screen. Each is cover-cropped
to the panel and dimmed. It lives outside gen_ic_ui.py because it needs PIL;
gen_ic_ui.art_paths() still lists the output, so the packer ships it and write_plates()
does not prune it.

check() measures every text cell no opaque plate covers, and every list-row text cell at
every row position, against every ink the panel draws there (INKS), with WCAG relative
luminance at the cell's p95. Which cells count is derived: the opaque plates are whatever
_panel_order sorts to tier -1, and image and button cells are skipped by name.

    py tools/make_ic_backdrop.py            # write both, then measure
    py tools/make_ic_backdrop.py --check    # measure only
    py tools/make_ic_backdrop.py --search   # the largest passing dim for each race
"""
import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "Modding Files", "reference", "Chaos Dwarf",
                   "morgan-ketelaar-jarass-wh3-winmovie-shot04.jpg")

# The source is 1920x1140; below this row is the logo and the credit bar.
ART_BOTTOM = 1000
# Each the largest hundredth at which every measured cell clears MIN_RATIO for every
# ink; check() asserts that one hundredth more fails.
DIM = 0.42
DIM_DWF = 0.32
MIN_RATIO = 4.5
RACES = ("chd", "dwf")

# Every ink the panel draws on the backdrop or a row: the twui's cream, and the
# db/ui_colours_tables colours the Lua writes with [[col:]]. Black is only ever
# drawn on the opaque lit plate.
INKS = {"cream": "FFF8D7", "red": "FF2D2D", "yellow": "FFB900", "green": "A0FF37"}


def _lin(v):
    v /= 255.0
    return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4


_LIN = [_lin(v) for v in range(256)]


def luminance(rgb):
    """WCAG 2.x relative luminance of an (r, g, b) in 0-255."""
    r, g, b = (int(round(c)) for c in rgb)
    return 0.2126 * _LIN[r] + 0.7152 * _LIN[g] + 0.0722 * _LIN[b]


INK_LUM = {k: luminance((int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)))
           for k, h in INKS.items()}


def ratio(a, b):
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


# Text cells with no plate of their own. bare_boxes() still drops any an opaque
# plate covers, so a cell that moves onto a plate drops out by itself.
TEXT_CELLS = ("ic_title", "ic_lbl_section", "ic_influence", "ic_control",
              "ic_control_fx", "ic_leader_lbl", "ic_leader_name", "ic_leader_party",
              "ic_leader_trait", "ic_page_lbl", "ic_alert",
              "ic_col_left", "ic_col_right",
              "ic_hdr_a", "ic_hdr_b", "ic_hdr_c", "ic_hdr_d", "ic_hdr_e",
              "ic_book")


def text_cells(G):
    """Every panel cell whose text is drawn straight onto the backdrop: the typed
    list plus the loop-built headings, which no typed list ever kept up with."""
    return (TEXT_CELLS + tuple("ic_plotcat_%d" % (i + 1) for i in range(G.PLOT_COLS))
            + tuple("ic_law_head_%d" % (i + 1) for i in range(G.LAW_COLS)) + ("ic_off_title",)
            + tuple(sorted(k for k in G.TEXT_STYLE if k.startswith("ic_gc_")))
            + tuple(n for n in ("ic_throne_of", "ic_throne_name", "ic_throne_leader")
                    if n in G.PANEL_LAYOUT))


def _row_wash(G):
    """How much of the backdrop survives the row's one flat black wash."""
    colour = G.ROW_LAYERS[0]["colour"]
    if len(G.ROW_LAYERS) != 1 or not colour.lower().startswith("#000000"):
        raise SystemExit("the row's cover is no longer one flat black wash (%r x%d)"
                         " - re-measure what shows through before trusting this"
                         % (colour, len(G.ROW_LAYERS)))
    return 1.0 - int(colour[7:9], 16) / 255.0


def bare_boxes(G):
    """(name, box) for every text cell no opaque plate covers."""
    plates = [G.PANEL_LAYOUT[n] for n in sorted(G.PANEL_LAYOUT)
              if G._panel_order(n)[0] == -1]

    def covered(box):
        x, y, w, h = box
        return any(px <= x and py <= y and px + pw >= x + w and py + ph >= y + h
                   for px, py, pw, ph in plates)

    out = []
    for name in text_cells(G):
        # ic_lbl_section has a second home, inside the Crown's box on the court.
        boxes = [G.PANEL_LAYOUT[name]]
        if name == "ic_lbl_section":
            boxes.append(tuple(G.COURT_SECTION_XY))
        for box in boxes:
            # The one plate over ic_book's box is the Laws vote's, never up on the
            # Court tab where the line is drawn.
            if name == "ic_book" or not covered(box):
                out.append((name, box))
    return out


# Row cells that carry no text on the backdrop: two pictures, and the buttons,
# whose words sit on their own plate.
def _row_skip(G):
    return {"ic_row_port", "ic_row_crest"} | set(G.BTN_CELLS)


def row_boxes(G):
    """(name, box) for every list-row text cell, at every row position."""
    skip = _row_skip(G)
    out = []
    for i in range(G.VISIBLE_ROWS):
        top = G.ROWS_Y + i * G.ROW_PITCH
        for name, (cx, cy, cw, ch) in sorted(G.ROW_LAYOUT.items()):
            if name not in skip:
                out.append(("%s[%d]" % (name, i + 1),
                            (G.ROWS_X + cx, top + cy, cw, ch)))
    return out


def _gen(race="chd"):
    spec = importlib.util.spec_from_file_location(
        "gen_ic_ui", os.path.join(ROOT, "tools", "gen_ic_ui.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("gen_ic_ui", mod)
    spec.loader.exec_module(mod)
    return mod if race == "chd" else mod.at_box(1920, race)


def dst(G):
    return os.path.join(ROOT, "Modding Files", "pack", *G.PANEL_BG.split("/"))


def build(dim=None):
    """The cropped, dimmed Chaos Dwarf backdrop at the panel's exact size."""
    from PIL import Image
    im = Image.open(SRC).convert("RGB")
    if im.size != (1920, 1140):
        raise SystemExit("the source keyframe is %dx%d, not 1920x1140 - re-measure "
                         "where the credit bar starts before trusting ART_BOTTOM"
                         % im.size)
    G = _gen()
    w, h = G.PANEL_W, G.PANEL_H
    art = im.crop((0, 0, im.width, ART_BOTTOM))
    # Scale to fill, then centre-crop: the composition is symmetric about the throne.
    wide = art.resize((int(round(art.width * h / float(art.height))), h),
                      Image.LANCZOS)
    left = (wide.width - w) // 2
    out = wide.crop((left, 0, left + w, h))
    d = DIM if dim is None else dim
    return out.point(lambda v: int(v * d)).convert("RGBA")


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


def _fails(img, G, race="chd"):
    """Cells under MIN_RATIO at 1920, and at 1600 and 2560 with the picture scaled."""
    from PIL import Image
    bad = [r for r in contrast(img, G) if r[3] < MIN_RATIO]
    for bw in (1600, 2560):
        g = G.at_box(bw, race)
        scaled = img.convert("RGB").resize((g.PANEL_W, g.PANEL_H), Image.LANCZOS)
        bad += [r for r in contrast(scaled, g) if r[3] < MIN_RATIO]
    return bad


def contrast(img=None, G=None):
    """(cell, mean, p95, ratio, ink) for every measured cell, worst last.

    Luminance is WCAG's, of the pixel as drawn: the row wash scales the stored
    value before it is linearised, as a black layer over it does. p95 and not the
    mean, because one bright ember through a dark cell is what the eye complains
    about. ratio is the worst over INKS, and ink names it. G is the generator at
    the box img is drawn for.
    """
    from PIL import Image
    G = G or _gen()
    img = img or Image.open(dst(G)).convert("RGB")
    rows = []
    rgb = img.convert("RGB")
    for name, (x, y, w, h), wash in (
            [(n, b, 1.0) for n, b in bare_boxes(G)]
            + [(n, b, _row_wash(G)) for n, b in row_boxes(G)]):
        raw = rgb.crop((x, y, x + w, y + h)).tobytes()
        lum = sorted(0.2126 * _LIN[int(raw[i] * wash)] + 0.7152 * _LIN[int(raw[i + 1] * wash)]
                     + 0.0722 * _LIN[int(raw[i + 2] * wash)]
                     for i in range(0, len(raw), 3))
        p95 = lum[int(len(lum) * 0.95)]
        ink, worst = min(((k, ratio(v, p95)) for k, v in INK_LUM.items()),
                         key=lambda kv: kv[1])
        rows.append((name, sum(lum) / len(lum), p95, worst, ink))
    return sorted(rows, key=lambda r: -r[3])


def check(race="chd"):
    out = []
    G = _gen(race)
    if not os.path.isfile(dst(G)):
        return ["the backdrop is not written: run py tools/make_ic_backdrop.py --race %s" % race]
    from PIL import Image
    img = Image.open(dst(G))
    if img.size != (G.PANEL_W, G.PANEL_H):
        out.append("the backdrop is %dx%d and the panel is %dx%d"
                   % (img.size + (G.PANEL_W, G.PANEL_H)))
    if G.PANEL_BG not in G.art_paths():
        out.append("gen_ic_ui.art_paths() no longer lists %s, so the packer will not "
                   "ship it and write_plates() will prune it" % G.PANEL_BG)
    # Every heading gen_ic_ui styles must be measured; this is what stops the typed
    # half of text_cells() going stale.
    measured = set(text_cells(G))
    for name, pair in sorted(G.TEXT_STYLE.items()):
        if pair not in (G.TITLE, G.SECTION) or name not in G.PANEL_LAYOUT:
            continue
        if name not in measured:
            out.append("%s is a heading drawn on the panel and nothing measures it "
                       "against the backdrop - add it to TEXT_CELLS, or derive it "
                       "in text_cells()" % name)
    for name, _mean, p95, r, ink in contrast(img.convert("RGB"), G):
        if r < MIN_RATIO:
            out.append("%s reads at %.2f:1 in %s against the backdrop (p95 luminance "
                       "%.4f) - under the %.1f:1 this panel needs"
                       % (name, r, ink, p95, MIN_RATIO))
    # And at 1600x900, the same picture shrunk with build()'s filter: each cell lands
    # on its pixels by its own rounding.
    small = G.at_box(1600, race)
    shrunk = img.convert("RGB").resize((small.PANEL_W, small.PANEL_H), Image.LANCZOS)
    for name, _mean, p95, r, ink in contrast(shrunk, small):
        if r < MIN_RATIO:
            out.append("at 1600x900, %s reads at %.2f:1 in %s against the backdrop "
                       "(p95 luminance %.4f) - under the %.1f:1 this panel needs"
                       % (name, r, ink, p95, MIN_RATIO))
    # The dim is the largest that passes, so one hundredth more must fail.
    try:
        up = (build if race == "chd" else build_dwf)(
            round((DIM if race == "chd" else DIM_DWF) + 0.01, 2))
    except SystemExit:
        up = None
    if up is not None and not _fails(up, G, race):
        d = DIM if race == "chd" else DIM_DWF
        out.append("the %s backdrop is dimmed to %.2f and %.2f would pass: dim it less"
                   % (race, d, d + 0.01))
    return out


def search(race):
    """The largest hundredth that passes, or None."""
    G = _gen(race)
    make = build if race == "chd" else build_dwf
    for k in range(90, 15, -1):
        if not _fails(make(k / 100.0), G, race):
            return k / 100.0
    return None


if __name__ == "__main__":
    races = ([sys.argv[sys.argv.index("--race") + 1]] if "--race" in sys.argv else list(RACES))
    if "--search" in sys.argv:
        for race in races:
            print("largest passing %s dim: %s" % (race, search(race)))
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
            for name, mean, p95, r, ink in measured[-10:]:
                print("  %-18s mean %.4f  p95 %.4f  %5.2f:1 (%s)" % (name, mean, p95, r, ink))
        problems += ["%s: %s" % (race, p) for p in check(race)]
    for p in problems:
        print("PROBLEM: " + p)
    sys.exit(1 if problems else 0)
