# -*- coding: utf-8 -*-
"""Cut the Iron Court's backdrop out of the win-movie keyframe, and prove the panel
still reads on top of it.

WHY IT IS NOT IN gen_ic_ui.py. That generator writes every png it owns by hand, with
zlib and struct and no PIL at all, because everything it draws is made of numbers -
flat plates, wedges, a rim. This one is a photograph being cropped and dimmed, which
is PIL's job, and a dependency the generator has managed without is not worth taking
on for one file. gen_ic_ui.art_paths() still LISTS the output, so the packer ships it
and write_plates() does not prune it.

TWO THINGS HAPPEN TO THE SOURCE:

  1. THE BOTTOM 140 ROWS ARE CUT. They are not art - they are the TOTAL WAR
     WARHAMMER III logo and, under it, a flat bar carrying the artist's credit and
     the GW/SEGA/CA marks. Measured off the image. Left in, both would draw across
     the card grid and the alert bar.

  2. IT IS DIMMED TO DIM. The keyframe is lit by a furnace and the panel's ink is
     #FFF8D7, so at full brightness the text cells with nothing opaque behind them
     fall below a 4.5:1 contrast ratio - measured, not judged by eye. check()
     below re-measures every one of them, so a backdrop swapped for a brighter one
     fails here instead of in game.

     WHICH CELLS THOSE ARE IS DERIVED, not listed. A cell is measured unless an
     opaque plate contains it, and the opaque plates are whatever _panel_order
     sorts to tier -1 - so a cell that moves onto a plate drops out by itself,
     and one that moves off is picked up. A typed list went stale the first time
     the layout moved and reported unreadable text that had a box behind it.

     AND THE ROW POOL IS IN IT. A row is not a plate: ROW_LAYERS is one flat
     #00000055 wash, so two thirds of the art shows through under every line of
     every list. That is the thinnest cover on the panel and it was the only one
     never measured; it is what moved DIM from 0.45 to 0.42.

    py tools/make_ic_backdrop.py            # write it
    py tools/make_ic_backdrop.py --check    # measure contrast only, write nothing
"""
import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "Modding Files", "reference",
                   "morgan-ketelaar-jarass-wh3-winmovie-shot04.jpg")
DST = os.path.join(ROOT, "Modding Files", "pack", "ui", "derpy_ic", "panel_bg.png")

# The source is 1920x1140; below this row is the logo and the credit bar.
ART_BOTTOM = 1000
# Chosen off the measurement, not by eye: the largest hundredth that clears
# MIN_RATIO on EVERY measured cell, so the art stays as bright as the text
# allows. 0.43 reads 4.489:1 and is already under it.
#
# It was 0.45 while the measurement was the court tab's eleven cells. The row
# pool - four of the five views - was never in it, and a row is not a plate:
# ROW_LAYERS is a single #00000055 wash, so two thirds of the furnace comes
# through under every line of every list. Measured, two row cells sat at 4.34:1
# and 4.50:1.
DIM = 0.42
# #FFF8D7, the panel's ink, as relative luminance.
INK = 245.0
# The ordinary "readable body text" bar. The worst cell reached 2.8 undimmed.
MIN_RATIO = 4.5

# Text cells with no plate OF THEIR OWN. The five tabs and the two pager buttons
# wear one, the cards and the two big plates are opaque, and the Crown's porthole
# has a house plate under it - none of those can be unreadable because of the
# backdrop, so measuring them would only dilute this.
#
# Being on this list does not mean a cell is measured: bare_boxes() drops the ones
# an opaque plate covers. That distinction was typed in until the two-column
# rebuild slid seven of these inside the Crown's box and the check went on
# measuring them against a photograph they no longer touch.
TEXT_CELLS = ("ic_title", "ic_lbl_section", "ic_influence", "ic_control",
              "ic_control_fx", "ic_leader_lbl", "ic_leader_name", "ic_leader_party",
              "ic_leader_trait", "ic_page_lbl", "ic_alert",
              "ic_col_left", "ic_col_right",
              # THE HEADER STRIP. Hidden on the court, bare on the four views that
              # do show it, and never on this list before the columns - a gap the
              # rebuild did not open but did make obvious.
              "ic_hdr_a", "ic_hdr_b", "ic_hdr_c", "ic_hdr_d", "ic_hdr_e")


def text_cells(G):
    """Every panel cell whose text is drawn straight onto the backdrop.

    TYPED PLUS DERIVED, and the derived half is the half that was missing. The
    intrigue tab's four column headings are ic_plotcat_1..4, built in a loop off
    PLOT_COLS, and no typed list ever had them - so for the whole life of that
    tab its headings drew on bare backdrop and were never measured. A fifth
    category would have repeated it.

    check() below asserts the result covers every heading gen_ic_ui styles, which
    is what stops the typed half going stale a third time.
    """
    return TEXT_CELLS + tuple("ic_plotcat_%d" % (i + 1) for i in range(G.PLOT_COLS))


# The row pool's own cover. ROW_LAYERS is a single 1x1_blank_white at #00000055 -
# a wash, not a plate - so this much of the backdrop survives under list text.
# Read off the layer rather than typed, because a darker wash chosen later would
# otherwise leave this number quietly wrong in the safe direction's opposite.
def _row_wash(G):
    colour = G.ROW_LAYERS[0]["colour"]
    if len(G.ROW_LAYERS) != 1 or not colour.lower().startswith("#000000"):
        raise SystemExit("the row's cover is no longer one flat black wash (%r x%d)"
                         " - re-measure what shows through before trusting this"
                         % (colour, len(G.ROW_LAYERS)))
    return 1.0 - int(colour[7:9], 16) / 255.0


def bare_boxes(G):
    """(name, box) for every text cell no opaque plate covers."""
    # THE SAME BRANCH _panel_order USES, not a second copy of the two names: a
    # third plate added there has to be a third plate here, and a list would not
    # know about it.
    plates = [G.PANEL_LAYOUT[n] for n in sorted(G.PANEL_LAYOUT)
              if G._panel_order(n)[0] == -1]

    def covered(box):
        x, y, w, h = box
        return any(px <= x and py <= y and px + pw >= x + w and py + ph >= y + h
                   for px, py, pw, ph in plates)

    out = []
    for name in text_cells(G):
        # ic_lbl_section HAS TWO HOMES and only one of them is bare - covered
        # inside the Crown's box on the court, on the backdrop everywhere else.
        boxes = [G.PANEL_LAYOUT[name]]
        if name == "ic_lbl_section":
            boxes.append(tuple(G.COURT_SECTION_XY))
        for box in boxes:
            if not covered(box):
                out.append((name, box))
    return out


def row_boxes(G):
    """(name, box) for every list-row text cell, at every row position."""
    # EVERY POSITION, not one row. The backdrop is a photograph; the furnace is
    # bright across the middle of it and the pool runs the height of the panel,
    # so which row a cell is in is most of the answer.
    out = []
    for i in range(G.VISIBLE_ROWS):
        top = G.ROWS_Y + i * G.ROW_PITCH
        for name, (cx, cy, cw, ch) in sorted(G.ROW_LAYOUT.items()):
            if name == "ic_row_port":
                continue        # a porthole, and it wears a house plate
            out.append(("%s[%d]" % (name, i + 1),
                        (G.ROWS_X + cx, top + cy, cw, ch)))
    return out


def _gen():
    spec = importlib.util.spec_from_file_location(
        "gen_ic_ui", os.path.join(ROOT, "tools", "gen_ic_ui.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("gen_ic_ui", mod)
    spec.loader.exec_module(mod)
    return mod


def build():
    """The cropped, dimmed backdrop at the panel's exact size."""
    from PIL import Image
    im = Image.open(SRC).convert("RGB")
    if im.size != (1920, 1140):
        raise SystemExit("the source keyframe is %dx%d, not 1920x1140 - re-measure "
                         "where the credit bar starts before trusting ART_BOTTOM"
                         % im.size)
    G = _gen()
    w, h = G.PANEL_W, G.PANEL_H

    art = im.crop((0, 0, im.width, ART_BOTTOM))
    # SCALE TO FILL, then centre-crop. The composition is symmetric about the
    # throne, so taking the same slice off each side costs nothing; letterboxing
    # instead would put bars where the panel has no frame to hide them.
    wide = art.resize((int(round(art.width * h / float(art.height))), h),
                      Image.LANCZOS)
    left = (wide.width - w) // 2
    out = wide.crop((left, 0, left + w, h))
    return out.point(lambda v: int(v * DIM)).convert("RGBA")


def contrast(img=None, G=None):
    """(cell, mean, p95, ratio) for every bare text cell, worst last.

    G is the generator at the box img is drawn for - at_box(1600) against the
    picture shrunk to 1600x900, or the base module against the file itself.
    """
    from PIL import Image
    img = img or Image.open(DST).convert("RGB")
    G = G or _gen()
    rows = []
    rgb = img.convert("RGB")
    for name, (x, y, w, h), wash in (
            [(n, b, 1.0) for n, b in bare_boxes(G)]
            + [(n, b, _row_wash(G)) for n, b in row_boxes(G)]):
        crop = rgb.crop((x, y, x + w, y + h))
        # tobytes and not getdata: getdata is deprecated in Pillow 14, and the
        # weights are Rec.709's - PIL's own "L" conversion uses 601-2 and would
        # quietly answer a slightly different question.
        raw = crop.tobytes()
        lum = sorted(wash * (0.2126 * raw[i] + 0.7152 * raw[i + 1]
                             + 0.0722 * raw[i + 2])
                     for i in range(0, len(raw), 3))
        # p95 AND NOT THE MEAN. A cell that is dark on average with a bright ember
        # through the middle of it is exactly the case the eye complains about, and
        # a mean hides it.
        p95 = lum[int(len(lum) * 0.95)]
        ratio = (INK / 255.0 + 0.05) / (p95 / 255.0 + 0.05)
        rows.append((name, sum(lum) / len(lum), p95, ratio))
    return sorted(rows, key=lambda r: -r[3])


def check():
    out = []
    if not os.path.isfile(DST):
        return ["the backdrop is not written: run py tools/make_ic_backdrop.py"]
    from PIL import Image
    img = Image.open(DST)
    G = _gen()
    if img.size != (G.PANEL_W, G.PANEL_H):
        out.append("the backdrop is %dx%d and the panel is %dx%d"
                   % (img.size + (G.PANEL_W, G.PANEL_H)))
    if G.PANEL_BG not in G.art_paths():
        out.append("gen_ic_ui.art_paths() no longer lists %s, so the packer will not "
                   "ship it and write_plates() will prune it" % G.PANEL_BG)
    # THE LIST ITSELF, checked before what is on it. Every heading gen_ic_ui
    # styles is a cell somebody chose to make prominent, so a heading that is not
    # measured here is a heading nobody has read against the art. This is the
    # guard the ic_plotcat_* gap needed and did not have.
    measured = set(text_cells(G))
    for name, pair in sorted(G.TEXT_STYLE.items()):
        if pair is not G.TITLE or name not in G.PANEL_LAYOUT:
            continue
        if name not in measured:
            out.append("%s is a heading drawn on the panel and nothing measures it "
                       "against the backdrop - add it to TEXT_CELLS, or derive it "
                       "in text_cells()" % name)
    for name, _mean, p95, ratio in contrast(img):
        if ratio < MIN_RATIO:
            out.append("%s reads at %.1f:1 against the backdrop (p95 luminance %.0f) "
                       "- under the %.1f:1 this panel needs"
                       % (name, ratio, p95, MIN_RATIO))
    # AND AT THE SMALL END. A 1600x900 screen stretches this same picture over a
    # 1600x900 panel and puts every cell at at_box(1600)'s numbers. The cells
    # move with the art, but each one lands on its pixels by its own rounding,
    # and a cell one pixel onto an ember is a different measurement. Shrunk
    # with the filter build() uses, because the engine's own is unknown.
    small = G.at_box(1600)
    shrunk = img.convert("RGB").resize((small.PANEL_W, small.PANEL_H), Image.LANCZOS)
    for name, _mean, p95, ratio in contrast(shrunk, small):
        if ratio < MIN_RATIO:
            out.append("at 1600x900, %s reads at %.1f:1 against the backdrop (p95 "
                       "luminance %.0f) - under the %.1f:1 this panel needs"
                       % (name, ratio, p95, MIN_RATIO))
    return out


if __name__ == "__main__":
    if "--check" not in sys.argv:
        img = build()
        os.makedirs(os.path.dirname(DST), exist_ok=True)
        img.save(DST, optimize=True)
        print("wrote %s  %dx%d  %.2f MB  (cut %d rows of logo and credits, dimmed to "
              "%.0f%%)" % (DST, img.width, img.height,
                           os.path.getsize(DST) / 1048576.0, 1140 - ART_BOTTOM,
                           DIM * 100))
    measured = contrast()
    print("  %d cells measured, worst ten:" % len(measured))
    for name, mean, p95, ratio in measured[-10:]:
        print("  %-18s mean %5.1f  p95 %5.1f  %4.1f:1" % (name, mean, p95, ratio))
    problems = check()
    for p in problems:
        print("PROBLEM: " + p)
    sys.exit(1 if problems else 0)
