"""The Iron Court - UI generator.

Writes the four .twui.xml files the panel is created from at runtime, built to
docs/mockups/politics_panel.png.

    py tools/gen_ic_ui.py --check
    py tools/gen_ic_ui.py
    py tools/gen_ic_ui.py --selftest

Read docs/CUSTOM_UI.md before editing. Every rule it records was measured in game,
most of them after shipping the wrong thing first.
"""
import io
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_iron_court_emitter as EU      # noqa: E402  - our own copy, deliberately
import gen_iron_court as IC              # noqa: E402  - OFFICES / HOUSES, for counts

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# THE BOX THIS COPY OF THE MODULE DESCRIBES. 1920 is the base layout, and every
# number below is typed for it. at_box() executes a fresh copy of this file with
# another width injected, and _scale_pass() at the end of the layout section
# rewrites every layout global the way ICUI.apply_scale does in game - so check()
# run on that copy is check() run on what a 1600x900 player sees.
#
# THE SCREEN A SCRIPT SEES IS THE WINDOW DIVIDED BY UI SCALE, FLOORED AT 1600x900
# (HANDOFF_20260924_GUILDS_UI_SCALE.md section 1). The panel was a fixed 1920x1080
# and a 1600x900 player lost 160px off each side. Text cannot be sized by script,
# so below 1920 the panel is created from compact copies one CA size step down.
BOX_W = globals().get("_BOX_W", 1920)
COMPACT = BOX_W < 1920


def sc(v, bw):
    """One layout number at box width bw. Integers only: game Lua is float32."""
    return (v * bw + 960) // 1920


def sc_box(box, bw):
    """A box by its EDGES, so two cells that touch at 1920 still touch.

    A SQUARE STAYS SQUARE, at the smaller of its two rounded sides. Rounding
    the edges separately made the office card's 16px crest 14x13 at 1600, and a
    house flag in a non-square cell is a stretched flag; the larger side would
    have run it into the button under it.
    """
    x, y, w, h = box
    w2 = sc(x + w, bw) - sc(x, bw)
    h2 = sc(y + h, bw) - sc(y, bw)
    if w == h:
        w2 = h2 = min(w2, h2)
    return (sc(x, bw), sc(y, bw), w2, h2)


def box_for(sw, sh):
    """The largest 16:9 box on the screen, clamped to 1600x900 .. 2560x1440."""
    bw = max(1600, min(2560, int(min(sw, sh * 16 / 9.0))))
    return bw, bw * 9 // 16


def at_box(bw):
    """A fresh copy of this module with every layout number scaled to box bw."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("gen_ic_ui_at_%d" % bw,
                                                  os.path.abspath(__file__))
    mod = importlib.util.module_from_spec(spec)
    mod.__dict__["_BOX_W"] = bw
    spec.loader.exec_module(mod)
    return mod

# ONE PREFIX PER FILE, not per mod. EU.assign restarts its counter for every file
# it is given, so four files sharing a prefix mint four identical GUID sets - and
# a GUID that collides with another file's is a silent non-draw. The Exchange's
# registry in docs/CUSTOM_UI.md is per file for exactly this reason: DE16 panel,
# DE17 row, DE18 button. DE14-DE18 are the Exchange and rites panels, GG21 is the
# Great Guilds, DE15 is RETIRED and must never be reused.
GUID_PREFIXES = {
    "derpy_ic_panel.twui.xml":  "IC30",
    "derpy_ic_card.twui.xml":   "IC31",
    "derpy_ic_row.twui.xml":    "IC32",
    "derpy_ic_opener.twui.xml": "IC33",
    "derpy_ic_standing.twui.xml": "IC34",
    "derpy_ic_party.twui.xml":  "IC35",
    # IC36 - the intrigue tab's move card. Its own file rather than a second
    # pool off derpy_ic_card, because a move needs THREE blurb line cells and
    # the office card has none to spare: twui text never wraps, so more lines
    # means more components. See PLOT_LAYOUT.
    "derpy_ic_plot.twui.xml":   "IC36",
    "derpy_ic_fire.twui.xml":   "IC37",
    # IC38 - the claim burst, created into a card or row per claim.
    "derpy_ic_burst.twui.xml":  "IC38",
    # IC39 - why a province's edicts are grey, beside CA's edict stack.
    "derpy_ic_edict_note.twui.xml": "IC39",
    # IC40-IC44 - THE COMPACT COPIES, the same components one CA font size
    # down for a box under 1920. Their own prefixes: a copy that reused its
    # base file's would collide with it GUID for GUID.
    "derpy_ic_panel_compact.twui.xml": "IC40",
    "derpy_ic_card_compact.twui.xml":  "IC41",
    "derpy_ic_row_compact.twui.xml":   "IC42",
    "derpy_ic_party_compact.twui.xml": "IC43",
    "derpy_ic_plot_compact.twui.xml":  "IC44",
    # IC45 and IC46 were the old party map's, retired 2026-09-30. Never reuse a prefix: a stale file in a player's data/ would collide.
    # IC47-IC51 - THE GOVERNORS VIEW (spec 2026-09-30): the pin, the face, the
    # two plates and the party badge, made once each per province into the
    # panel's first child. Never scaled.
    "derpy_ic_gm_pin.twui.xml":     "IC47",
    "derpy_ic_gm_face.twui.xml":    "IC48",
    "derpy_ic_gm_name.twui.xml":    "IC49",
    "derpy_ic_gm_loyal.twui.xml":   "IC50",
    "derpy_ic_gm_badge.twui.xml":   "IC51",
    # IC52-IC53 - THE GOVERNORS VIEW'S COLUMN ROW and its compact copy.
    "derpy_ic_gm_row.twui.xml":         "IC52",
    "derpy_ic_gm_row_compact.twui.xml": "IC53",
    # IC54-IC55 - THE COLUMN'S SCROLLING LIST and the empty row that gives it
    # its length (author, 2026-10-01: "no scrollbar for selecting a governor").
    "derpy_ic_gm_list.twui.xml":        "IC54",
    "derpy_ic_gm_sp.twui.xml":          "IC55",
    # IC56-IC59 - THE LAWS TAB (spec 2026-10-02 laws): the law card, the party
    # block on a vote, and their compact copies.
    "derpy_ic_law.twui.xml":                "IC56",
    "derpy_ic_lawblock.twui.xml":           "IC57",
    "derpy_ic_law_compact.twui.xml":        "IC58",
    "derpy_ic_lawblock_compact.twui.xml":   "IC59",
}

# Base file -> its compact copy. The opener and the influence plate are HUD
# pieces beside CA's own UI and are never scaled, so they have none.
COMPACT_FILES = dict(
    (f, f.replace(".twui.xml", "_compact.twui.xml"))
    for f in ("derpy_ic_panel.twui.xml", "derpy_ic_card.twui.xml",
              "derpy_ic_row.twui.xml", "derpy_ic_party.twui.xml",
              "derpy_ic_plot.twui.xml", "derpy_ic_gm_row.twui.xml",
              "derpy_ic_law.twui.xml", "derpy_ic_lawblock.twui.xml"))

# The Zharr Exchange's footprint, which is proven to fit at every supported
# resolution. The mockup is drawn to it.
# The porthole source, MEASURED rather than guessed: 1,204 of the 1,209 images
# under ui/portraits/portholes/ in ui.pack are exactly this, and CA's own panels
# draw them landscape (44x28 in cathay_caravans, 41x26 in army_banner). A cell
# that does not share this aspect distorts every face in it, silently, because
# SetImagePath makes the incoming image TAKE the cell's size rather than fit
# inside it. check_portrait_aspect() below refuses a cell that drifts.
PORTHOLE_W, PORTHOLE_H = 300, 164
PORTHOLE_ASPECT = PORTHOLE_W / float(PORTHOLE_H)        # 1.829
PORTHOLE_TOLERANCE = 0.06                               # 6 per cent

# The two shapes the ROW cell alternates between at runtime. The Lua declares
# the same four numbers and import_iron_court.py refuses on any drift.
PORT_BOX = (104, 57)      # a porthole, at the row's full height
CREST_BOX = (36, 36)     # a house flag; mon_64.png is square

# HELL-FORGE SIZED. CA's hellforge_panel_main is a 1600x900 backdrop under a
# 1612x912 frame; this matches that shape so the court is a screen rather than
# a window. 15 rows now fit, so the court view never scrolls.
PANEL_W, PANEL_H = 1920, 1080
CONTENT_W = PANEL_W - 36

# THE NINE INTERESTS PLUS EVERY FACTION THAT COULD BE ABSORBED. A confederated
# faction takes a seat of its own in the court, so the bar needs a segment it
# can never create later - the components are built once, when the panel is.
# The model's IC.MAX_SEATS is the same arithmetic over the same two lists, and
# import_iron_court.py compares the lists themselves.
CONFED_SEATS = [h[0] for h in IC.ORIGINS if h[1]]
MAX_HOUSES = len(IC.PARTIES) + len(CONFED_SEATS)
OFFICE_COUNT = len(IC.OFFICES)

# ---------------------------------------------------------------------------
# Layout. name -> (x, y, w, h). ABSOLUTE OFFSETS ONLY: dockpoint is ignored on a
# runtime-created component, and MoveTo is the only thing that positions one.
#
# Every component in the XML must be named by one of these tables. A component no
# table names cannot draw at all once the hide pass walks their union - the fault
# flips from "draws in the wrong place forever" to "never draws", which is
# quieter still.
# ---------------------------------------------------------------------------
# 192, which is where it was before the dial existed. ROWS_Y is shared by every
# view that draws a list - governors, intrigue, record - and the court is not one
# of them any more: it is a dial and a grid of cards, in two columns, and it
# hides the pool outright. So nothing here pays anything for the dial.
ROWS_X, ROWS_Y = 18, 192
ROW_PITCH = 64
# THE HEADER STRIP RIDES WITH THE ROWS, 30px above whichever row is first. Both
# numbers are here because check 20 has to know the COURT one: off that view the
# strip sits above the pie's box and nothing is drawn in it, but on the court
# view a strip in the same place would be behind an opaque disc.
# BACK TO 30. It was widened to 48 to stack the sort arrow UNDER its label;
# the arrow sits BESIDE the label now and the strip needs no second row.
HDR_GAP = 30
# 30px above whichever row is first, and derived from it: a header strip and
# the list it labels are one decision.
HDR_Y = ROWS_Y - HDR_GAP

PANEL_LAYOUT = {
    # FAR LEFT, and named for the god the court answers to. The middle of the
    # top strip is the pie's column now, and a panel's own name belongs where a
    # reader starts rather than over the thing it is naming.
    # ON THE CHAOS DWARF TITLE BANNER (2026-09-26), whose arrow ends take 165px
    # a side - so 600 wide, which leaves the name 270 between them.
    "ic_title": (18, 4, 600, 56),
    # TOP RIGHT and 48px, where a close button belongs and where the cursor
    # goes looking for it. It was 22px at the top left: wrong corner, and
    # under half the size of any round button CA ships.
    "ic_close": (1854, 12, 48, 48),
    # THE HELP BUTTON, beside the title (author, 2026-09-28). This is its place
    # when the plate fills its 600px box; the panel Lua moves it to the plate's
    # real end with the same 8px gap, because the plate is sized to its words.
    # Vertically centred on the 56px title.
    "ic_help": (626, 8, 48, 48),
    # RIGHT-ANCHORED: its right edge is PANEL_W - 18, so it moved with the panel
    # rather than staying at the 1600-wide x it was authored for.
    # Ends at 1840, so it no longer runs under the close button at 1854.
    # 300 WIDE since it gained a plate (2026-09-25): "99 of 99 seats filled"
    # has to fit inside the frame, SEATS_PAD clear of each end.
    "ic_influence": (1540, 20, 300, 26),
    # THE GOVERNORS VIEW'S PINS' HOLDER (spec 2026-09-30), the panel's FIRST
    # child (check_gm): pins made in it draw under everything this file
    # declares. Moved to the screen's corner and sized to the screen at every
    # draw, as the party map's layer was: a pin is placed in screen space.
    "ic_gm_pins": (0, 0, 1920, 1080),
    # THE GOVERNORS VIEW'S PLATES AND COLUMN (spec 2026-09-30 section 6). Text
    # on a live map has no reliable contrast, so every line this view keeps sits
    # on one of the three plates (check_gm_plates). The column is CA's
    # Hell-Forge side panel at its own 503x1080, opaque 0-443 then its fade,
    # from the screen's top (the strip draws over it) to its foot, so the map
    # never shows under it when the footer is hidden. Its title at its own 90.
    "ic_gm_top": (0, 0, 1920, 128),
    "ic_gm_foot": (0, 1014, 1920, 66),
    "ic_gm_col": (0, 0, 503, 1080),
    "ic_gm_head": (10, 128, 425, 90),
    # OVER THE TITLE'S BOTTOM SPIKE TIPS, which the toggles draw after.
    "ic_gm_tog_1": (76, 214, 56, 56),
    "ic_gm_tog_2": (312, 214, 56, 56),
    # AT THE ART'S OWN 30, its dark field rows 4-22 (GM_PLATE_RAIL).
    "ic_gm_tog_lbl_1": (44, 270, 120, 30),
    "ic_gm_tog_lbl_2": (280, 270, 120, 30),
    "ic_gm_hint": (16, 302, 412, 26),
    # THE PROVINCES PAGE'S SORT, in the hint's slot: the hint is the Parties
    # page's and these are the Provinces page's, never both on screen.
    "ic_gm_sort_1": (16, 302, 132, 26),
    "ic_gm_sort_2": (156, 302, 132, 26),
    "ic_gm_sort_3": (296, 302, 132, 26),
    # CA'S ACCEPT AND CANCEL on the Hell-Forge's own button plate.
    "ic_gm_btns": (0, 922, 444, 90),
    "ic_gm_ok": (150, 939, 56, 56),
    "ic_gm_no": (238, 939, 56, 56),
    # THE COURT'S PAGER, same sizes, under the seventh row (330 + 6 * 80 + 76 = 886).
    # THE SORT CONTROL, on the tab row's far right and ending where the close
    # button ends (1902). The row is free from 784 to 1596, but the control is
    # right-aligned instead: it belongs to the list below it rather than to the
    # tabs beside it, and the panel's other two right-hand cells - ic_close and
    # ic_influence - already set that edge.
    # 240 WIDE since they wear CA's skull-capped tab (2026-09-26): its caps
    # take 45px a side, so a 150 tab left "Governors" 60px of bar.
    "ic_tab_court": (18, 62, 240, 32),
    "ic_tab_offices": (262, 62, 240, 32),
    "ic_tab_govs": (506, 62, 240, 32),
    "ic_tab_intrigue": (750, 62, 240, 32),
    # WHAT THE PARTIES ASK OF YOU, on a tab of its own (author, 2026-09-24).
    # Offers were answered from a party's favour list and demands from nowhere
    # at all - the player had to find the seat and fill it by hand.
    "ic_tab_petitions": (994, 62, 240, 32),
    # The RECORD, on its own tab, and LAST (author, 2026-09-24): it is the one
    # tab with nothing to act on. It shared the Intrigue list with the live
    # secession clocks, and a page of history pushed the one thing a player
    # can still act on off the screen.
    "ic_tab_log": (1238, 62, 240, 32),
    "ic_tab_laws": (1482, 62, 240, 32),
    # THE ATTENTION MARKERS (spec 2026-09-28 section 4.4): a heat glow over
    # each tab's right-hand skull, the cap's centre 20px in from the end
    # (TAB_CAP 40), shown by ICUI.draw_marks while that tab has business.
    "ic_mark_court": (18 + 240 - 34, 64, 28, 28),
    "ic_mark_offices": (262 + 240 - 34, 64, 28, 28),
    "ic_mark_govs": (506 + 240 - 34, 64, 28, 28),
    "ic_mark_petitions": (994 + 240 - 34, 64, 28, 28),
    "ic_mark_laws": (1482 + 240 - 34, 64, 28, 28),
    # ITS BOTTOM EDGE CAPS THE PIE, not its width: the pie may not rise above
    # this line, so it grows DOWNWARD and the list pays for it in rows.
    #
    # THE WIDTH IS THE PANEL'S. It was 900 for the 874px the longest picker
    # question measured, and 20e caught that question at 897px the moment a
    # cost inside it gained an icon - three pixels, on a heuristic that is a
    # desktop face standing in for the game's. Nothing else is on this row:
    # ic_close and ic_influence are both above it and the pie starts 16px
    # below, so the honest width is the one the frame band leaves, and a
    # reworded title never has to come back here again.
    "ic_lbl_section": (18, 98, 1884, 22),
    # y 302 and 24 tall: header_16 needs the height, and the block has to
    # finish above the first row AND start below the pie, whose flat side is
    # at DIAL_CY. 222 put the middle three headers underneath it.
    # 502 AND 35px LEFT OF WHERE THEY WERE. See check 20k: the Rank heading
    # and the arrow beside it ran 24px into the Influence heading, because the
    # arrow is MoveTo'd past the caption and a 45px column cannot hold a
    # four-letter word. Character is the only column with room to give - 468
    # measured against 537 - and Party moves without narrowing.
    "ic_hdr_a": (146, HDR_Y, 502, 24),
    "ic_hdr_b": (708, HDR_Y, 360, 24),
    "ic_hdr_c": (1088, HDR_Y, 45, 24),
    "ic_hdr_d": (1188, HDR_Y, 490, 24),
    "ic_hdr_e": (1698, HDR_Y, 170, 24),
    # ONE UNDER EACH HEADER, at CA's own 17x18 - the native size of
    # parchment_sort_arrow_down.png, measured out of ui2.pack rather than
    # guessed. They share their column's x so the arrow reads as belonging to
    # the label above it and not to the one beside it.
    #
    # ALL FIVE ARE DECLARED EVEN THOUGH ONLY THE CHARACTER PICKER SORTS. The
    # Lua hides the ones whose view has no mode for that column, which is the
    # same rule the header cells themselves follow; a component that exists
    # only on some views cannot be positioned by a loop over the layout.
    # THE X HERE IS A PLACEHOLDER AND THE Y IS NOT. ICUI.refresh MoveTo's
    # each arrow to its header's x plus that header's MEASURED text width,
    # because the caption in one cell differs per view - "Character" on the
    # picker, "Province" on the governors - and a fixed x would leave a gap
    # under one of them. The y is real: 3 centres an 18px arrow in a 24px
    # strip, and nothing moves it.
    "ic_hsort_a": (146, HDR_Y + 3, 17, 18),
    "ic_hsort_b": (708, HDR_Y + 3, 17, 18),
    "ic_hsort_c": (1088, HDR_Y + 3, 17, 18),
    "ic_hsort_d": (1188, HDR_Y + 3, 17, 18),
    "ic_hsort_e": (1698, HDR_Y + 3, 17, 18),
    # The scroll column is the last 18px of the content width. At 1600 wide this
    # sat at 1564, which on a centred panel is screen x 1724 - under the campaign
    # HUD's event feed, where it could not be clicked. That is the whole of "the
    # scroll does not work".
    # The pager sits BELOW the last row and above the alert bar. A scrollbar
    # needed a drag CA does not expose to Lua; two buttons and a caption need
    # only the click event that exists.
    # Six pixels lower than they were, which is what the row pool needed to
    # keep ten rows under a pie that starts 80px further down the panel.
    # SIZED TO THEIR LABELS (2026-09-24), not 150 apiece: "NEXT" does not
    # need 150px, and the party action bar shares this row on the court tab.
    # PREVIOUS is 107px at BODY and 96 at the compact size, plus the plate's
    # two 8px caps, so 136 holds it at 1600; the caption holds "Page 99 of 99".
    "ic_page_prev": (1454, 978, 136, 34),
    "ic_page_lbl": (1600, 982, 164, 26),
    "ic_page_next": (1774, 978, 136, 34),
    "ic_alert": (18, 1018, 1884, 44),
}

# ---------------------------------------------------------------------------
# THE COURT TAB IS TWO COLUMNS. Nothing else on the panel is.
#
# It used to be stacked: the dial across the top of the panel, the party cards
# in a band underneath it. That wasted the whole right-hand half of the dial's
# row - 590px of backdrop with nothing on it - and paid for the waste twice
# over, because the cards then had to fit five across and a party's name got a
# 280px cell it could not hold. Side by side, each half gets the panel's full
# height and the cards get half its width instead of a fifth.
#
# ONLY THIS TAB. The offices tab is a card grid, the other three are lists, and
# all four still use the full width - so every component declared here is
# court-only and the dispatcher hides it elsewhere, exactly as it already does
# for the dial.
# THE TITLE PLATE'S HEIGHT - see HEADER_LAYERS. Here because the columns use it.
HEADING_H = 44
COL_TOP = 102                          # clear of the tabs, which end at 94
# THE DIVIDER LIVES IN THE GUTTER, so the gutter has to be wider than it: a
# rule drawn in a 4px gap has no air on either side and reads as a seam.
COL_GUTTER = 32
DIVIDER_W = 4
COL_W = (CONTENT_W - COL_GUTTER) // 2
COL_L_X = 18
COL_R_X = COL_L_X + COL_W + COL_GUTTER
COL_HDR_H = HEADING_H
# NO GAP: the plate's lower spikes are the gap, and they end where the body starts.
COL_BODY_Y = COL_TOP + COL_HDR_H
# WHERE BOTH COLUMNS STOP: the alert bar is full width and sits under them, so
# neither column may reach it.
COL_BOTTOM = PANEL_LAYOUT["ic_alert"][1] - 8

PANEL_LAYOUT["ic_col_left"] = (COL_L_X, COL_TOP, COL_W, COL_HDR_H)
PANEL_LAYOUT["ic_col_right"] = (COL_R_X, COL_TOP, COL_W, COL_HDR_H)

# THE HELP PAGE (author, 2026-09-28: "doesnt look very user friendly", then chose
# a topic list and a page). The first build borrowed the list rows: 64px apart,
# a portrait's height, and a pager to reach topic eight. This is its own page -
# one card under all of it, the topics down the left in the tabs' own plates,
# a rule, and the chosen topic's heading and lines at 34px. HELP_SLOTS topic
# buttons and as many lines; the harness fails a topic or a line past them.
# The card is NOT one of _panel_order's tier -1 plates: make_ic_backdrop drops a
# cell from its contrast measurement once a tier -1 plate covers it, and this
# card covers the header strip every list view draws bare. It sorts first among
# its own cells by name (ic_help_box < ic_help_head < _line_ < _rule < _topic_),
# which is what puts it under them.
HELP_SLOTS = 12


def help_layout():
    """Every help-page cell and its box, at 1920. ICUI.PANEL_XY mirrors it."""
    out = {"ic_help_box": (18, 124, 1884, 540),
           "ic_help_rule": (352, 144, 2, 472),
           "ic_help_head": (372, 140, 900, 44)}
    for _i in range(HELP_SLOTS):
        out["ic_help_topic_%d" % (_i + 1)] = (36, 144 + 40 * _i, 300, 32)
        out["ic_help_line_%d" % (_i + 1)] = (384, 196 + 34 * _i, 1500, 28)
    return out


PANEL_LAYOUT.update(help_layout())

# THE LAWS TAB (spec 2026-10-02 laws section 4; the approved pictures are
# .skilltree_cache/ui_preview/ic_law_board.png and ic_law_vote.png). The board:
# four column heads over LAW_GRID's twenty cards, and the chosen law's pane.
LAW_W, LAW_H = 306, 150
LAWS_X, LAWS_Y = 18, 186
LAW_GAP_X, LAW_GAP_Y = 12, 8
LAW_COLS, LAW_ROWS = 4, 5
LAW_LINES = 5
LAW_PBAR_H = 14
# THE PANE BAR'S SIDES: green for, red against, through plate_pixels' own
# gradient, which darkens each to about two thirds at the top.
LAW_PBAR_COLOUR = {"aye": "#5FB04AFF", "nay": "#D2412FFF"}


def law_pbar_path(side):
    return "%s/law_bar_%s.png" % (PLATE_DIR, side)
# THE PANE BAR'S BORDER (author, 2026-10-03: "add borders to the bar"): the
# portrait frame's bronze thinned to two pixels between two dark lines, drawn
# over both sides. LAW_PBAR_RIM_OUT of it lies outside the bar, so only the
# inner dark line covers the bar's own 14px.
LAW_PBAR_RIM_BAND = [(26, 14, 6, 255), (190, 128, 66, 255), (130, 78, 36, 255),
                     (20, 10, 4, 255)]
LAW_PBAR_RIM_OUT = 3
LAW_PBAR_RIM_PX = 16
# SIZED BY 20k, not by eye (Task 10). The first cut put the effect lines beside
# the picture at 204px, and the engine's face needs 274 for the longest: the
# picture now sits beside the NAME, which ICUI.fit_two splits over two lines,
# and the effects run the card's width. The vote marker moved to the foot row,
# where it no longer narrows the name.
LAW_LAYOUT = {
    "ic_law_icon": (12, 10, 44, 44),
    "ic_law_name": (60, 8, 240, 22),
    "ic_law_name2": (60, 30, 240, 22),
    # 14 IN, NOT 10 (2026-10-04): at 10 the lines sat 3px off the frame's
    # inner edge. The width stays 290 because 20k needs it at 1600x900, where
    # the longest line measures 234px; left-aligned, only that line reaches.
    "ic_law_fx1": (14, 56, 290, 18),
    "ic_law_fx2": (14, 74, 290, 18),
    "ic_law_fx3": (14, 92, 290, 18),
    # CLEAR OF THE IN-FORCE FRAME, whose bottom band covers the card's last
    # ~12px (seen on the preview, 2026-10-02).
    "ic_law_foot": (14, 114, 238, 20),
    "ic_law_mark": (266, 110, 28, 28),
}


def law_grid():
    """Column-major, so card i is category ceil(i/5): ICUI.law_at reads it so."""
    return [(LAWS_X + c * (LAW_W + LAW_GAP_X), LAWS_Y + r * (LAW_H + LAW_GAP_Y))
            for c in range(LAW_COLS) for r in range(LAW_ROWS)]


LAW_GRID = law_grid()


def law_board_cells():
    """The column heads and the pane, right of the four columns."""
    out = {}
    for i in range(LAW_COLS):
        x = LAWS_X + i * (LAW_W + LAW_GAP_X)
        # A TITLE ON THE HEADING PLATE (author, 2026-10-03), as the Intrigue
        # tab's move groups are: the cell is the most room, fit_plate centres it.
        out["ic_law_head_%d" % (i + 1)] = (x, 133, LAW_W, HEADING_H)
    px = LAWS_X + LAW_COLS * (LAW_W + LAW_GAP_X) + 6
    pw = 1902 - px
    out.update({
        "ic_law_pane": (px, 132, pw, 836),
        "ic_law_p_icon": (px + 24, 156, 72, 72),     # the art's own 72px
        "ic_law_p_name": (px + 128, 160, pw - 150, 30),
        "ic_law_p_sub": (px + 128, 198, pw - 150, 26),
        "ic_law_p_fxh": (px + 24, 244, pw - 48, 26),
        "ic_law_p_forh": (px + 24, 440, pw - 48, 26),
        "ic_law_p_for": (px + 24, 466, pw - 48, 26),
        "ic_law_p_conh": (px + 24, 500, pw - 48, 26),
        "ic_law_p_con": (px + 24, 526, pw - 48, 26),
        "ic_law_p_nowh": (px + 24, 562, pw - 48, 26),
        "ic_law_p_now": (px + 24, 588, pw - 48, 26),
        # THE PROJECTION AS A BAR (author, 2026-10-03): the vote bar's idiom,
        # aye from the left and nay from the right over a grey ground. The two
        # sides are MoveTo'd and resized by ICUI.draw_law_pbar.
        "ic_law_p_bar": (px + 24, 618, pw - 48, LAW_PBAR_H),
        "ic_law_p_baraye": (px + 24, 618, pw - 48, LAW_PBAR_H),
        "ic_law_p_barnay": (px + 24, 618, pw - 48, LAW_PBAR_H),
        "ic_law_p_barrim": (px + 24, 618, pw - 48, LAW_PBAR_H),   # sorts last: drawn over
        "ic_law_p_price": (px + 24, 852, pw - 48, 26),
        "ic_law_p_btn": (px + (pw - 240) // 2, 896, 240, 34),
    })
    # TWO ROWS AN EFFECT: CA's own line runs to 850px against a 552 pane, so
    # ICUI.fit_lines spills each over fx(2k-1) and fx(2k).
    for i in range(6):
        out["ic_law_p_fx%d" % (i + 1)] = (px + 24, 272 + 26 * i, pw - 48, 26)
    for i in range(LAW_LINES):
        out["ic_law_p_line%d" % (i + 1)] = (px + 24, 642 + 30 * i, pw - 48, 26)
    return out


# THE VOTE: the top plate, the support bar (twelve segments and their crests,
# placed at draw time), two sides of LB_GRID's party blocks, and the hand.
LAW_SEGS = 12
LB_W, LB_H = 880, 104
LB_X, LB_Y, LB_SIDE_DX, LB_GAP = 38, 396, 950, 4
# THREE MEN A BLOCK, not four (Task 10, 20k): "Mulagunnar - 9999" is 201px
# against a 116px cell. A man is his forename over his influence, or over the
# Win button that would buy him - the two share a line.
LB_PER_SIDE, LB_MEN = 4, 3


def lb_layout():
    slot = 266          # one man's face, name and Win line
    out = {"ic_lb_crest": (0, 0, 52, 52), "ic_lb_name": (64, 2, 480, 22),
           "ic_lb_level": (64, 28, 640, 20), "ic_lb_more": (720, 28, 160, 20),
           "ic_lb_total": (800, 4, 80, 22)}
    for i in range(3):
        out["ic_lb_pip_%d" % (i + 1)] = (700 + 30 * i, 8, 24, 14)
    for i in range(LB_MEN):
        out["ic_lb_face_%d" % (i + 1)] = (64 + slot * i, 54, 70, 38)
        out["ic_lb_man_%d" % (i + 1)] = (138 + slot * i, 54, 186, 18)
        out["ic_lb_inf_%d" % (i + 1)] = (138 + slot * i, 76, 186, 24)
        out["ic_lb_win_%d" % (i + 1)] = (138 + slot * i, 76, 186, 24)
    return out


LB_LAYOUT = lb_layout()


def lb_grid():
    """Aye side first, then nay; ICUI.LB_XY reads it so."""
    return [(LB_X + s * LB_SIDE_DX, LB_Y + k * (LB_H + LB_GAP))
            for s in range(2) for k in range(LB_PER_SIDE)]


LB_GRID = lb_grid()


def law_vote_cells():
    out = {
        "ic_lv_top": (18, 132, 1884, 94),
        "ic_lv_icon": (36, 141, 76, 76),
        "ic_lv_name": (128, 144, 900, 30),
        "ic_lv_fx": (128, 182, 1000, 26),
        "ic_lv_by": (1140, 148, 530, 26),
        "ic_lv_turns": (1140, 182, 530, 26),
        "ic_lv_back": (1682, 162, 210, 34),
        "ic_lv_aye": (18, 236, 600, 26),
        "ic_lv_abs": (760, 236, 400, 26),
        "ic_lv_nay": (1296, 236, 600, 26),        # right-aligned: ends where the bar does
        "ic_lv_bar": (18, 266, 1884, 34),
        "ic_lv_barrim": (18, 266, 1884, 34),     # _panel_order: over the segments
        "ic_lv_abstain": (18, 870, 1884, 26),
        "ic_lv_hand": (18, 906, 1884, 96),
        # TWO ROWS, EACH HEADING ON ITS LEFT (author, 2026-10-03: "texts are going
        # out of the UI buttons"). The tab art's skull caps take 46px a side, so
        # the eight buttons with their prices need about 2040px and one row has
        # 1848: the side and the overrule on the first row, the support below.
        "ic_lv_sideh": (36, 918, 164, 26),
        "ic_lv_supph": (36, 962, 164, 26),
        "ic_lv_overh": (1266, 918, 164, 26),
        "ic_lv_over_1": (1436, 914, 220, 34),
        "ic_lv_over_2": (1664, 914, 220, 34),
    }
    for i in range(LAW_SEGS):
        out["ic_lv_seg_%d" % (i + 1)] = (18, 266, 34, 34)
        out["ic_lv_segc_%d" % (i + 1)] = (18, 268, 30, 30)
    for i in range(2):
        sx = 18 + 950 * i
        out["ic_lv_side_%d" % (i + 1)] = (sx, 312, 934, 548)
        out["ic_lv_sicon_%d" % (i + 1)] = (sx + 20, 326, 52, 52)
        out["ic_lv_shead_%d" % (i + 1)] = (sx + 86, 332, 590, 30)
        out["ic_lv_stag_%d" % (i + 1)] = (sx + 662, 336, 200, 20)
        out["ic_lv_screst_%d" % (i + 1)] = (sx + 870, 324, 44, 44)
        out["ic_lv_smore_%d" % (i + 1)] = (sx + 20, 830, 880, 24)
    for i in range(3):
        # SIZED FOR 1600, where the box shrinks and the 46px caps do not.
        out["ic_lv_st_%d" % (i + 1)] = (210 + 210 * i, 914, 204, 34)
        out["ic_lv_lvl_%d" % (i + 1)] = (210 + 380 * i, 958, 372, 34)
    return out


PANEL_LAYOUT.update(law_board_cells())
PANEL_LAYOUT.update(law_vote_cells())

# THE GOVERNMENT CHOOSER (author, 2026-10-03, design A of three previews): five
# cards in one centred row instead of the picker's list, each a picture, its
# name over two lines, its rule over GC_RULE_LINES, its effect, who it pleases
# or angers in this court (at most three lines: the Convoy Concern has two
# parties) and a Choose button. Over them, the government in force on a heading
# plate and its rule. ICUI.draw_gov_cards fills them.
GOV_CARDS, GC_RULE_LINES, GC_LOY_LINES = 5, 4, 3


def gov_card_cells():
    # CENTRED DOWN THE PAGE (2026-10-04): the block ran 134..850 and left
    # 230px of bare backdrop over the footer. DY puts the same space above
    # the heading as below the cards' foot.
    w, gap, h, dy = 340, 22, 600, 84
    y = 250 + dy
    x0 = (PANEL_W - (GOV_CARDS * w + (GOV_CARDS - 1) * gap)) // 2
    out = {"ic_gc_now": (360, 134 + dy, PANEL_W - 720, HEADING_H),
           "ic_gc_nowrule": (160, 184 + dy, PANEL_W - 320, 26)}
    for i in range(GOV_CARDS):
        x, n = x0 + i * (w + gap), i + 1
        out["ic_gc_card_%d" % n] = (x, y, w, h)
        out["ic_gc_icon_%d" % n] = (x + (w - 112) // 2, y + 26, 112, 112)
        out["ic_gc_name_%d" % n] = (x + 16, y + 154, w - 32, 30)
        out["ic_gc_name2_%d" % n] = (x + 16, y + 184, w - 32, 30)
        out["ic_gc_ruleh_%d" % n] = (x + 20, y + 224, w - 40, 26)
        for k in range(GC_RULE_LINES):
            out["ic_gc_rule_%d_%d" % (n, k + 1)] = (x + 20, y + 250 + 26 * k, w - 40, 26)
        out["ic_gc_fxh_%d" % n] = (x + 20, y + 360, w - 40, 26)
        out["ic_gc_fx_%d" % n] = (x + 20, y + 386, w - 40, 26)
        out["ic_gc_loyh_%d" % n] = (x + 20, y + 420, w - 40, 26)
        for k in range(GC_LOY_LINES):
            out["ic_gc_loy_%d_%d" % (n, k + 1)] = (x + 20, y + 446 + 26 * k, w - 40, 26)
        out["ic_gc_btn_%d" % n] = (x + 50, y + h - 56, w - 100, 38)
    return out


PANEL_LAYOUT.update(gov_card_cells())
# THE PLATES, declared first so what they hold draws over them (_panel_order).
LAW_PLATES = tuple("ic_gc_card_%d" % (_i + 1) for _i in range(GOV_CARDS)) + ("ic_law_pane", "ic_lv_top", "ic_lv_side_1", "ic_lv_side_2", "ic_lv_hand")
# LIT LIKE A TAB (ICUI.TAB_PLATE, both slots): the Crown's stance and support.
LAW_TAB_BUTTONS = ("ic_lv_st_1", "ic_lv_st_2", "ic_lv_st_3",
                   "ic_lv_lvl_1", "ic_lv_lvl_2", "ic_lv_lvl_3")
# ON THE PAGER'S PLATE, as ic_gov_btn is: never lit.
LAW_PAGE_BUTTONS = ("ic_law_p_btn", "ic_lv_back", "ic_lv_over_1", "ic_lv_over_2") + tuple(
    "ic_gc_btn_%d" % (_i + 1) for _i in range(GOV_CARDS))
# CENTRED IN THE GUTTER rather than at the panel's midpoint: the two columns
# are the same width but the left one starts at 18, so the true middle of the
# panel is not the middle of the gap between them.
PANEL_LAYOUT["ic_divider"] = (COL_L_X + COL_W + (COL_GUTTER - DIVIDER_W) // 2,
                              COL_TOP, DIVIDER_W, COL_BOTTOM - COL_TOP)

# THE PARTY ACTION BAR, under the cards (author, 2026-09-24): click a party,
# then act on it here. It rides the pager's row, so the card grid keeps its
# height and a confederate court can still page. Each width is its label
# measured at BODY plus the plate's two 8px end caps, with a few pixels over;
# check 20g holds them to it.
#
# TWO HOMES. CENTRED UNDER THE GRID, which is where it almost always is: the
# court pages only when confederates push it past the grid's slots, and a bar
# hugging the left edge to leave room for a pager that was not there read as
# misaligned (author, "why is the three buttons not center aligned?").
#
# AND CENTRED UNDER THE CROWN'S BOX - ACT_PAGED - while the pager is on screen.
# It sat beside the pager until SEND A GIFT came back as a fourth button
# (author, 2026-09-25): four buttons are 630px and the pager 456, and the grid
# column is 926. The left column's bottom row is empty on the court tab, level
# with the pager, and nothing else ever draws there. ICUI.draw_actions moves all
# five between the two homes; check 9c holds each one where it belongs.
#
# THE TWO FAVOURS SIDE BY SIDE, between the two plots: both are paid in gold out
# of the treasury, and PURGE, the move with no way back, stays at the end.
ACT_GAP = 6
ACT_BUTTONS = (("ic_act_provoke", 132), ("ic_act_gift", 164),
               ("ic_act_secure", 216), ("ic_act_purge", 100))
ACT_PAGED = {}
_bar_w = (sum(_w for _n, _w in ACT_BUTTONS)
          + ACT_GAP * (len(ACT_BUTTONS) - 1))
_ax = COL_L_X + (COL_W - _bar_w) // 2
_cx = COL_R_X + (COL_W - _bar_w) // 2
for _name, _w in ACT_BUTTONS:
    ACT_PAGED[_name] = (_ax, PANEL_LAYOUT["ic_page_prev"][1], _w,
                        PANEL_LAYOUT["ic_page_prev"][3])
    PANEL_LAYOUT[_name] = (_cx, PANEL_LAYOUT["ic_page_prev"][1], _w,
                           PANEL_LAYOUT["ic_page_prev"][3])
    _ax += _w + ACT_GAP
    _cx += _w + ACT_GAP
del _ax, _cx, _name, _w, _bar_w
# WHAT TO DO FIRST, in the same row, while no rival party is chosen. It and
# the buttons are never on screen together. Centred text across whichever
# column the bar is in.
PANEL_LAYOUT["ic_act_hint"] = (COL_R_X, PANEL_LAYOUT["ic_page_lbl"][1], COL_W,
                               PANEL_LAYOUT["ic_page_lbl"][3])
ACT_PAGED["ic_act_hint"] = (COL_L_X, PANEL_LAYOUT["ic_page_lbl"][1], COL_W,
                            PANEL_LAYOUT["ic_page_lbl"][3])

# THE PIE: a FILLED half disc, one court's worth of it, in the middle of the
# panel. It replaced a ring of pips, which replaced a 1884px bar of per-party
# segments, and neither replacement is decoration - the engine has no rotation
# and no runtime colour, so a shape has to be built out of rectangles PLACED
# inside it, and a rectangle that is placed can also be handed any party's
# picture. The segments could not: their colour was baked into this file by
# index, which is why a party had to keep the same segment for the life of a
# campaign.
#
# A RING IS ONE RADIUS AND A PIE IS AN AREA. The Lua rasterises it in
# horizontal STRIPS - the only way an axis-aligned rectangle can carry a
# straight radial boundary - and cuts each strip where the boundaries cross it.
# So this side builds a POOL of identical cells and the Lua moves, resizes and
# colours as many of them as the court needs. Every number here is in the Lua
# too and import_iron_court.py refuses to pack when they disagree.
DIAL_SLICES = 60     # three degrees each - the quantum AND the picture count
# 340, not 210. The dial is the court: it is the one thing on the panel that
# answers "who holds this faction" without reading a word, and at 420px across
# it was a diagram beside a list rather than the subject of the tab.
#
# WHAT THE SIZE COSTS, and where. The pie is opaque, so nothing may share its
# box - but it has a COLUMN of its own now rather than a band across the panel,
# so what it costs is paid in that column alone: the Crown's block goes under it
# instead of beside it. Nothing outside the left column pays anything.
# THE DEPTH OF THE FIRE, on all four sides. This is the one number in the dial
# that is chosen rather than derived, because it is the only one that is about
# how the thing should look: sixteen pixels of ember round the metal.
#
# IT USED TO BE DERIVED and DIAL_R chosen, which worked while the fire burned
# on three sides only - the pad was whatever happened to be left between the
# pie and the label above it. The flat side has no such gap to inherit: under
# it is the court's header strip, six pixels down. So the dependency is the
# other way round now and DIAL_R takes what is left.
RIM_PAD = 16
# THE MIDDLE OF THE LEFT COLUMN, not of the panel. It was 960 while the dial
# spanned the whole width; the column is what it spans now, and every crest and
# figure on the pie is placed by trigonometry off this, so it is the one number
# that has to move for the dial to move at all.
DIAL_CX = COL_L_X + COL_W // 2
# WHAT THE COLUMN LEAVES, on the WIDTH. This used to be derived downward from
# the section label above the dial, because height was the scarce thing on a
# panel-wide dial. In a column the scarce thing is width: the plate is
# 2R + 2 RIM_PAD + 2 DIAL_PAD_X across and may not leave the column, so R takes
# what that allows and the Crown's box below gets the height that is left.
DIAL_PAD_X, DIAL_PAD_TOP, DIAL_PAD_BOT = 16, 0, 10
DIAL_R = (COL_W - 2 * RIM_PAD - 2 * DIAL_PAD_X) // 2
# The BASELINE, the flat side, not the middle of its box. Derived from where the
# plate starts, so the whole dial hangs off COL_BODY_Y and moves with it.
DIAL_CY = COL_BODY_Y + DIAL_PAD_TOP + RIM_PAD + DIAL_R
# HELD TO THE PROPORTIONS THEY HAD AT R=324, where both were set by eye against
# a 40px crest and a "100%" figure. They are rings inside the fill, so a radius
# that changes and two rings that do not would put the crests through the rim.
CREST_R = int(round(DIAL_R * 232 / 324.0))
# Each party's crest is its OWN component (ic_barc_NN) rather than a layer on a
# wedge: a wedge belongs to a party only for the length of one draw, and there
# are fewer crests than wedges because the smallest have no room for one.
CREST_PX = 40
# EVERY WEDGE IS THE WHOLE PIE BOX, and every one of them is at the same place.
# Cropping each picture to its own corner would save a third of the bytes and
# would put a piece of trigonometry in two files that have to agree to the
# pixel; an uncropped sprite has no geometry in it at all.
# EACH PARTY'S SHARE IN FIGURES, on the same ray as its crest and inside it.
# The colour says who is biggest and the crest says who they are; neither says
# whether a rival is on 31 or 38, which is the number a player is actually
# deciding on. 186 leaves 14px between the label's outer edge and the crest's
# inner one, so a run that is wide enough for both never draws them touching.
SHARE_R = int(round(DIAL_R * 186 / 324.0))
SHARE_W, SHARE_H = 72, 24

PIE_BOX = (DIAL_CX - DIAL_R, DIAL_CY - DIAL_R, 2 * DIAL_R, DIAL_R)
# THE RIM IS THE ONE THING BIGGER THAN THE PIE. Its fire burns outward now, and
# outward is off the edge of a picture that was exactly the pie box - so the
# rim gets RIM_PAD of margin on the arc's three sides and keeps its baseline
# exactly where the pie's is. Nothing else in the dial moves.
# RIM_PAD ON ALL FOUR SIDES, so the box is two pads taller than the pie and two
# pads wider. It was one pad taller while the baseline burned nothing, and the
# fire under the flat side was drawn off the bottom of its own picture - which
# clips to nothing with no error, the same way a wall with no image slot draws
# nothing with no error.
RIM_BOX = (DIAL_CX - DIAL_R - RIM_PAD, DIAL_CY - DIAL_R - RIM_PAD,
           2 * DIAL_R + 2 * RIM_PAD, DIAL_R + 2 * RIM_PAD)
for _i in range(DIAL_SLICES):
    PANEL_LAYOUT["ic_wedge_%02d" % _i] = PIE_BOX
# THE RIM, in the same box as every wedge and drawn after all of them. CA's own
# frame is a NINE-SLICE of straight rails - see BORDER_TEXTURE below - and a
# nine-slice has no way to bend round an arc, so the dial's border is a picture
# for exactly the reason the wedges are.
PANEL_LAYOUT["ic_dial_rim"] = RIM_BOX
# ONE DIVIDER PER PARTY, not per slice. A run of slices is one party and the
# wall goes where the next one starts, so a court of four parties draws three
# of these and the other sixteen stay hidden. They share the pie's own box -
# the line is drawn from the centre, and the picture decides the angle.
for _i in range(MAX_HOUSES):
    PANEL_LAYOUT["ic_div_%02d" % _i] = PIE_BOX
for _i in range(MAX_HOUSES):
    PANEL_LAYOUT["ic_barc_%02d" % _i] = (DIAL_CX - CREST_PX // 2,
                                         DIAL_CY - CREST_R - CREST_PX // 2,
                                         CREST_PX, CREST_PX)
    # ONE PER SEAT, like the crests, and for the same reason: a component
    # cannot be created after the panel is, so every party that could ever sit
    # in this court needs its cell built whether it turns up or not. This is
    # only where they wait - every draw places them on their own party's ray.
    PANEL_LAYOUT["ic_barp_%02d" % _i] = (DIAL_CX - SHARE_W // 2,
                                         DIAL_CY - SHARE_R - SHARE_H // 2,
                                         SHARE_W, SHARE_H)
# WHAT THE PIE MEANS, IN WORDS, in the column the title starts: the band the
# faction is wearing and the effects that come with it. LEFT of the pie rather
# than under it - under it is the header strip, and what the vertical budget is
# actually for is the list below that.
# 600 WIDE, not 700. The pie box now starts at x=620 and these two lines sit
# beside it; at 700 they ran 98px under it, which is a sentence whose end is
# behind an opaque disc. Check 20 refuses that, and it is the reason this
# number is not free to be whatever reads best.
# DERIVED FROM WHATEVER THE DIAL REACHES, not counted by hand. This was 600
# with a note reading "600 not 700: pie box starts at x=620" - correct on the
# day it was written and eight pixels too wide the moment the rim grew a
# margin to burn into.
# THE PLATE BEHIND THE DIAL - Rome 2's Government Overview box, which is a
# framed rectangle with the half-disc sitting inside it. The dial has been
# floating on the panel's background art since it shipped; a frame is what makes
# it read as a readout rather than as decoration painted on the wall.
#
# ITS TOP IS THE RIM'S TOP, with no padding at all: the plate begins exactly at
# COL_BODY_Y and the column header sits above that, so top padding would only
# push the dial down for nothing. The other three sides get room, because the
# rim's fire burns OUTWARD and a frame drawn tight against it clips the ember.
# The three pads are declared up beside DIAL_R, which is derived from them.
DIAL_BOX = (RIM_BOX[0] - DIAL_PAD_X, RIM_BOX[1] - DIAL_PAD_TOP,
            RIM_BOX[2] + 2 * DIAL_PAD_X,
            RIM_BOX[3] + DIAL_PAD_TOP + DIAL_PAD_BOT)
PANEL_LAYOUT["ic_dial_box"] = DIAL_BOX

# ---------------------------------------------------------------------------
# THE CROWN'S BOX, under the dial in the same column.
#
# These lines used to sit BESIDE the dial, in the strip of panel the pie did not
# cover, and their width was whatever the dial left - DIAL_BOX[0] - 18 - 2. The
# dial fills its column now and leaves nothing beside it, so the block moved
# under it and took the column's full width instead. It is a framed box rather
# than loose text because it is the one part of this tab that is about YOU
# rather than about the court, and on a backdrop the frame is what says so.
# ---------------------------------------------------------------------------
CROWN_Y = DIAL_BOX[1] + DIAL_BOX[3] + 16
# The same 9-slice band the cards wear, because it is the same frame texture -
# see PARTY_BAND, and check 18, which holds every use of it to the corner it
# has to clear.
CROWN_BAND = 30
_CROWN_X = COL_L_X + CROWN_BAND
_CONTROL_W = COL_W - 2 * CROWN_BAND
_CROWN_Y0 = CROWN_Y + CROWN_BAND
# THE SECTION LABEL LIVES IN HERE ON THIS TAB ONLY. ic_lbl_section is shared by
# all five views and keeps its full-width home at the top of the panel for the
# other four; the dispatcher moves it here when the court is up, the same way it
# already moves the row pool's own furniture between views.
# THE BOX IS TWO HALVES AGAIN (author, 2026-09-24): "the Crown panel should
# display the character portrait, traits and party trait on the right side, and
# the left side the faction effects of getting the influence".
#
# IT WAS SPLIT ONCE AND STACKED WHEN THE FONTS GREW, because each half was asked
# for a one-line sentence it could not hold: "100% of the court - An Iron Grip on
# the Court" (475px at BODY) on the left, and the Crown's party name beside a
# 183px portrait on the right. Neither is asked of a half now. The left half
# breaks the band into its share, its name and one line per effect; the right
# half puts the name and the party ABOVE the portrait at the half's full width,
# and only the traits - 213px at most, icon and all - go beside it.
_CROWN_GAP = 24
# THE LEFT HALF IS SIZED OFF ITS WIDEST LINE: the band name, 275px at BODY, and
# the section label, 249 at TITLE, plus the cell inset and headroom. Everything
# else it holds is shorter, and 20g measures every line against it.
# 322, NOT 316 (2026-09-28): the band line wears an icon now, and at 1600x900
# "An Iron Grip on the Court" behind it measured 260px in a 257px cell.
_CROWN_LEFT_W = 322
_CROWN_RIGHT_X = _CROWN_X + _CROWN_LEFT_W + _CROWN_GAP
_CROWN_RIGHT_W = _CONTROL_W - _CROWN_LEFT_W - _CROWN_GAP

COURT_SECTION_XY = (_CROWN_X, _CROWN_Y0, _CROWN_LEFT_W, 26)

# ---- the left half: what holding the court is worth -------------------------
# The share, the band it lands in, then the band's effects one to a line - four
# at most (IC.CONTROL_BANDS); a band with fewer leaves the rest empty.
_CTL_H = 26
_CTL_Y = _CROWN_Y0 + 32
PANEL_LAYOUT["ic_control"] = (_CROWN_X, _CTL_Y, _CROWN_LEFT_W, _CTL_H)
PANEL_LAYOUT["ic_control_band"] = (_CROWN_X, _CTL_Y + 28, _CROWN_LEFT_W, _CTL_H)
# NAMED, NOT COUNTED OUT OF A LOOP IN THE LUA: ICUI.FX_KEYS is this list and the
# packing gate compares the cells name by name.
FX_KEYS = ("ic_control_fx", "ic_control_fx2", "ic_control_fx3", "ic_control_fx4")
_FX_Y = _CTL_Y + 62
for _i, _name in enumerate(FX_KEYS):
    PANEL_LAYOUT[_name] = (_CROWN_X, _FX_Y + _i * _CTL_H, _CROWN_LEFT_W, _CTL_H)
del _i, _name
_LEFT_BOTTOM = _FX_Y + len(FX_KEYS) * _CTL_H

# ---- the right half: who sits on the throne ------------------------------------
# THE CROWN, WITH A FACE ON IT. Everything else on this tab is a party; the one
# party the player IS had nothing but a wedge and a row like any other.
#
# 183x100 and not 180x100: the porthole is 300x164 and check 8c refuses a cell
# that drifts more than 6% off that aspect, because SetImagePath makes the image
# take the CELL's shape rather than fit inside it.
_LEADER_Y = _CROWN_Y0
_PORT_W, _PORT_H = 183, 100
PANEL_LAYOUT["ic_leader_lbl"] = (_CROWN_RIGHT_X, _LEADER_Y, _CROWN_RIGHT_W, 26)
PANEL_LAYOUT["ic_leader_name"] = (_CROWN_RIGHT_X, _LEADER_Y + 32, _CROWN_RIGHT_W, 28)
PANEL_LAYOUT["ic_leader_party"] = (_CROWN_RIGHT_X, _LEADER_Y + 64, _CROWN_RIGHT_W, 26)
_LEADER_ROW_Y = _LEADER_Y + 98
PANEL_LAYOUT["ic_leader_port"] = (_CROWN_RIGHT_X, _LEADER_ROW_Y, _PORT_W, _PORT_H)
_LEADER_TX = _CROWN_RIGHT_X + _PORT_W + 14
_LEADER_TW = _CROWN_RIGHT_W - _PORT_W - 14
# HIS TRAIT BESIDE HIS FACE, then a gap, then the party's two - the party card's
# order, where his sits under his name and theirs below the portrait.
PANEL_LAYOUT["ic_leader_trait"] = (_LEADER_TX, _LEADER_ROW_Y + 4, _LEADER_TW, 26)
PANEL_LAYOUT["ic_leader_t1"] = (_LEADER_TX, _LEADER_ROW_Y + 42, _LEADER_TW, 26)
PANEL_LAYOUT["ic_leader_t2"] = (_LEADER_TX, _LEADER_ROW_Y + 68, _LEADER_TW, 26)
_LEADER_BOTTOM = _LEADER_ROW_Y + _PORT_H

# THE CROWN'S THREE RULES (author, 2026-09-28: "no icons or separation in the
# crown panel, use lines or icons to show what they mean"): a line under each
# half's heading, in the 6px between the heading and the first line under it,
# and one down the gap between the halves. The column divider's own flat fill.
CROWN_RULE_W = 2
PANEL_LAYOUT["ic_crown_rule_l"] = (_CROWN_X, _CROWN_Y0 + 28, _CROWN_LEFT_W, CROWN_RULE_W)
PANEL_LAYOUT["ic_crown_rule_r"] = (_CROWN_RIGHT_X, _LEADER_Y + 28, _CROWN_RIGHT_W,
                                   CROWN_RULE_W)
PANEL_LAYOUT["ic_crown_rule_v"] = (_CROWN_X + _CROWN_LEFT_W
                                   + (_CROWN_GAP - CROWN_RULE_W) // 2, _CROWN_Y0,
                                   CROWN_RULE_W,
                                   max(_LEFT_BOTTOM, _LEADER_BOTTOM) - _CROWN_Y0)

# THE GOVERNMENT (spec 2026-10-02 section 8): one row under both halves -
# "Government: <name>" from the box's left edge to a gap short of Change
# Doctrine, which sits at the right half's right end. The label is the
# author's (2026-10-02): a bare "The Conclave" read as one more party name.
_GOV_Y = max(_LEFT_BOTTOM, _LEADER_BOTTOM) + 8
GOV_BTN_W = 220
PANEL_LAYOUT["ic_gov"] = (_CROWN_X, _GOV_Y + 4,
                          _CROWN_RIGHT_X + _CROWN_RIGHT_W - GOV_BTN_W - _CROWN_GAP
                          - _CROWN_X, _CTL_H)
PANEL_LAYOUT["ic_gov_btn"] = (_CROWN_RIGHT_X + _CROWN_RIGHT_W - GOV_BTN_W, _GOV_Y,
                              GOV_BTN_W, 34)
# THE GOVERNMENT IN FORCE BREATHES (2026-10-04): CA's Hell-Forge heat glow under
# the government's own picture, which is the first thing ic_gov writes - the
# look of the Hell-Forge's active category block (MARK_LAYERS, glow_pulse_t0 at
# 0.80,1.50,0.80). 48px square, centred 6px of LABEL_TX plus the 18px icon's
# half in from the line's left, and on the line's middle. A picture under a
# picture, so it is not one of CROWN_CELLS, whose 20b2 forbids any crossing;
# check_gov_glow holds it on the icon and under the line instead.
PANEL_LAYOUT["ic_gov_glow"] = (_CROWN_X + 6 + 9 - 24, _GOV_Y + 4 + _CTL_H // 2 - 24,
                               48, 48)
_GOV_BOTTOM = _GOV_Y + 34

# EVERY CELL IN THE BOX, by name, for the three checks that hold it together:
# 16b (its column), 18 (inside the frame band) and 20b2 (no two cross). One list,
# so a cell added to the box cannot be left out of one of them.
CROWN_CELLS = (("ic_control", "ic_control_band") + FX_KEYS
               + ("ic_leader_lbl", "ic_leader_name", "ic_leader_party",
                  "ic_leader_port", "ic_leader_trait", "ic_leader_t1",
                  "ic_leader_t2", "ic_crown_rule_l", "ic_crown_rule_r",
                  "ic_crown_rule_v", "ic_gov", "ic_gov_btn"))

# AND THE BOX IS AS TALL AS WHAT IS IN IT: the deeper of the two halves and the
# government's row, then the frame band. An empty framed box reads as a draw
# that failed.
CROWN_H = max(_LEFT_BOTTOM, _LEADER_BOTTOM, _GOV_BOTTOM) + CROWN_BAND - CROWN_Y
PANEL_LAYOUT["ic_crown_box"] = (COL_L_X, CROWN_Y, COL_W, CROWN_H)

# 1542 not 1560: the last 18px of the list area is the scrollbar column.
# 61 tall, not 40, to carry a 104x57 face instead of a 66x36 one. Every text
# cell's y is recentred on the new height rather than left where it was - a
# 20-tall cell at y=10 was centred in a 40 row and sits near the top of a 61.
ROW_W, ROW_H = 1866, 61
ROW_LAYOUT = {
    "ic_row_port": (12, 2, 104, 57),
    "ic_row_e": (1680, 15, 170, 32),
    # 382 wide, not 420: the portrait cell now ends at 116 rather than 78, so the
    # name column starts 38px later and keeps its right edge where it was. Widening
    # the cell without narrowing this one runs it into the House column, which is
    # check 9 and would have refused the build.
    # REBALANCED. These widths were set while the panel was drawing 12px text
    # by accident: Standing and Loyalty had 300px each to hold "14%" and
    # "54", while the Effect column had 340 for a whole sentence and the
    # engine clipped it ("...the province kno..."). twui text never wraps, so
    # a column either fits its content or loses the end of it.
    # The candidate's HOUSE CREST, beside the House column. A name in the
    # panel's one text colour is not a faction colour; the faction's own flag
    # is. Square, and fed per line so the Court tab - whose main row icon is
    # already this same crest - does not draw the flag twice.
    "ic_row_crest": (638, 12, 36, 36),
    # 380, not 420: the 40px buys the crest cell its slot without moving the
    # House column off 568.
    # 537, AND IT WAS 380. It carries a position name in front of the man now
    # - "General Zaul Zhufbarden, Overseer" - and it was ALREADY too narrow
    # without one: "Amarudz Grimtidesson, Daemonsmith" measures 406 and nothing
    # had ever measured this cell, so it has been cutting mid-word in silence.
    # See CUT_CELLS: even 537 does not reach the worst case, so it is cut.
    "ic_row_a": (128, 18, 502, 26),
    # RANK GAVE PARTY 180px AND HOLDS GAVE IT ANOTHER. Sized by MEASUREMENT
    # and not by character count: all 672 names IC.party_name can build,
    # rendered at BODY's 18px and scaled by GAME_FONT_WIDER, top out at 342px
    # ("Assembly of the Closed Account"). 260 was chosen against a 16px
    # estimate and clipped 82 of them.
    #
    # RANK KEEPS 120 rather than the 52 its own header needs, because the
    # General / Lord / Hero cell measures 81px and that column is where it goes.
    # 360 AND UNCHANGED. Its widest rolled party name is 342 - it has 12px to
    # spare and no more, which is why the rebalance took nothing from here. The
    # 2026-09-16 build took 40, and that is what made every party name clip.
    "ic_row_b": (690, 18, 360, 26),
    # 45. It held "General 40" for one build and holds "40" again - the kind is
    # a position name in front of the man now, not a statistic beside his rank.
    # "88" measures 26 and this leaves the same 6px on each side of it that
    # every other cell on this row is held to.
    "ic_row_c": (1070, 18, 45, 26),
    # 490, and the 30 went to the Character column. Its widest string is
    # "1722 influence - Grand Overseer of the Forge" at 475, so this is the same
    # 6px margin as everything else here rather than a cell kept wide by habit.
    "ic_row_d": (1170, 18, 490, 26),
    # A SECOND BUTTON, for the one list whose rows are a yes-or-no: the
    # Petitions tab's REFUSE, beside its ACCEPT. It sits over column four's
    # tail, so fill_rows hides it on every line that does not name it and the
    # petitions view narrows nothing it does not use.
    "ic_row_f": (1520, 15, 156, 32),
}

# THE GOVERNORS VIEW'S COLUMN ROW (spec 2026-09-30 section 6): ONE pool for the
# column's three pages, as the Intrigue views share one. The body is CA's
# Hell-Forge unit block, which stretches between 16px caps. Must match
# ICUI.GM_ROW_* and ICUI.GM_ROW_CHILD_XY in the panel Lua (import_iron_court).
GM_ROW_FILE = "derpy_ic_gm_row.twui.xml"
# 392 WIDE, not the column's 412: the slider takes the last 20 (GM_SLIDER_*).
GM_ROW_X, GM_ROW_Y, GM_ROW_W, GM_ROW_H, GM_ROW_PITCH = 16, 330, 392, 76, 80
GM_ROWS = 7
GM_ROW_LAYOUT = {
    "ic_gr_face": (10, 9, 104, 57),     # a porthole, PORT_BOX's own shape
    "ic_gr_crest": (10, 20, 36, 36),    # a party's crest, square
    "ic_gr_badge": (90, 46, 24, 24),    # his party's crest on the face's corner
    # THE THREE LINES INSIDE THE FRAME'S RAILS (GM_ROW_RAIL), at the box
    # heights the office card's own lines ship at: 16px text in 20, 12px in 16.
    "ic_gr_l1": (124, 12, 254, 20),
    "ic_gr_l2": (124, 31, 254, 16),
    "ic_gr_icon": (124, 47, 16, 16),    # CA's loyalty icon
    "ic_gr_l3": (144, 47, 234, 16),
}
# THE COLUMN SCROLLS (author, 2026-10-01: "no scrollbar for selecting a
# governor"; the wheel and a slider, the pager gone). CA's own list, the Great
# Guilds' proven shape (docs/CUSTOM_UI.md, "Scrolling lists"): listview >
# list_clip > list_box, and vslider > handle. The cards are made INTO
# list_clip, over list_box: a card is a parent of six cells and a row inside a
# list must have none, so list_box holds GM_ROWS-pitch EMPTY rows (GM_SP_FILE)
# that give the list its length, and the engine scrolls those. DRAWN WHOLE
# (2026-10-02, docs/CUSTOM_UI.md): every entry's card is made once under one
# holder in list_clip - made from GM_SP_FILE too, the empty one-component shape -
# and ICUI.gm_scroll_poll moves the holder to list_box; nothing is redrawn.
GM_LIST_FILE = "derpy_ic_gm_list.twui.xml"
GM_SP_FILE = "derpy_ic_gm_sp.twui.xml"
GM_SLIDER_W, GM_SLIDER_GAP, GM_HANDLE_H = 16, 4, 40
GM_LIST_SILENT = ("listview", "list_clip", "list_box", "vslider")
GM_LIST_W = GM_ROW_W + GM_SLIDER_GAP + GM_SLIDER_W
GM_LIST_H = GM_ROWS * GM_ROW_PITCH
GM_HF = "ui/skins/default/dlc23_chd_hell_forge/"
GM_ROW_ART = GM_HF + "button_square_extra_large_%s.png"
# ITS RAILS, measured off CA's art (122x82, every state): the frame holds rows
# 0-11 and 69-81 and columns 0-10 and 111-121. The art stretches vertically with
# no caps (margin (0, 16)), so the top and bottom rails scale with the row; the
# side ones sit in the 16px caps and never do. A line or the loyalty icon laid
# over one has the frame - and the chosen row's gold edge - run through it
# (final review, 2026-10-01: the third line sat on the bottom rail).
GM_ROW_ART_H = 82
GM_ROW_RAIL = (12, 11, 13, 11)      # top, right, bottom, left, in the art's pixels
GM_ROW_CLEAR = ("ic_gr_l1", "ic_gr_l2", "ic_gr_l3", "ic_gr_icon")
GM_COL_ART = GM_HF + "side_panerl_bg.png"          # CA's spelling
GM_HEAD_ART = GM_HF + "side_panel_title.png"
# THEIR OWN SIZES, measured off CA's art: the column is a whole 1920x1080
# screen's side, and the title is 90 tall with its spikes. check_gm_plates.
GM_COL_ART_W, GM_COL_ART_H = 503, 1080
GM_HEAD_ART_H = 90
GM_TOG_LABEL_ART = "ui/skins/default/dlc23_tower_of_zharr/tab_sub_title.png"
GM_ROUND = "ui/skins/default/button_round_medium_%s.png"
GM_TOG_ICONS = {
    "ic_gm_tog_1": "ui/skins/default/dlc23_tower_of_zharr/icon_button_seat_effects.png",
    "ic_gm_tog_2": "ui/skins/default/icon_provinces.png",
}
GM_PLATES = ["ic_gm_top", "ic_gm_foot", "ic_gm_col"]

# 230 TALL, not 200. The frame 9-slice margin went from 18 to 30 (see
# CARD_LAYERS), because 18 cut through panel_back_border.png own corner
# ornament - measured 27px across and 28 down on the 256x256 source. The
# thicker band eats 60px of height between the rails, so the card has to give
# it back or the name line draws on top of the rail.
#
# THE ZIGGURAT. Fourteen seats in four bands of 2 / 3 / 4 / 5, each band
# CENTRED, so the tab draws the shape of the court rather than a list of it.
#
# BOTH NUMBERS ARE DERIVED, and that is the whole reason they are not the
# numbers they used to be. The widest band is the bottom one, so the card width
# is whatever five of them plus their gaps make of the content width; the four
# bands have to finish above the pager, so the height is whatever four of them
# plus their gaps make of the room between the first row and it. Retuning the
# ziggurat is now a change to IC.OFFICES and nothing else.
CARDS_X, CARDS_Y = 18, 192
CARD_GAP_X, CARD_GAP_Y = 16, 14
CARD_TIERS = sorted(set(o["tier"] for o in IC.OFFICES))
CARD_WIDEST = max(IC.TIER_SEATS.values())
CARD_W = (CONTENT_W - (CARD_WIDEST - 1) * CARD_GAP_X) // CARD_WIDEST
CARD_H = ((PANEL_LAYOUT["ic_page_prev"][1] - 6 - CARDS_Y
           - (len(CARD_TIERS) - 1) * CARD_GAP_Y) // len(CARD_TIERS))
# Top to bottom, in IC.OFFICES' own order - which is why the model requires its
# tiers to be contiguous. A band's x is whatever centres it under the one below.
# BUILT ONCE, AT 1920. The scale pass then scales each point on its own, as
# ICUI.apply_scale does in game: rebuilding the grid from a card width rounded
# down once and multiplied by five ran a tier 2-4px past its column at some
# widths. The packing gate compares the two sides point by point.
def card_grid():
    out = []
    for row, tier in enumerate(CARD_TIERS):
        n = IC.TIER_SEATS[tier]
        band = n * CARD_W + (n - 1) * CARD_GAP_X
        for col in range(n):
            out.append((CARDS_X + (CONTENT_W - band) // 2
                        + col * (CARD_W + CARD_GAP_X),
                        CARDS_Y + row * (CARD_H + CARD_GAP_Y)))
    return out


CARD_GRID = card_grid()

# THE FILL BUTTON, on the offices tab (author, 2026-09-25): the pager's row,
# which that tab never uses - fourteen seats never page - centred under the
# ziggurat, on the pager's plate like the court tab's action bar. Its width is
# its label at BODY plus the plate's end caps and some over; check 20g2 holds
# the label to it.
FILL_W = 220
PANEL_LAYOUT["ic_fill"] = (CARDS_X + (CONTENT_W - FILL_W) // 2,
                           PANEL_LAYOUT["ic_page_prev"][1], FILL_W,
                           PANEL_LAYOUT["ic_page_prev"][3])
# THE ZIGGURAT THE SEATS STAND ON (author, 2026-10-01: "the silhouette im
# talking about is the background ziggurat"). A tier behind each row of cards,
# reaching ZIG_PAD past them, and a two-step shrine above the top one, up to
# just under the section line. The cards cover its middle; what shows is its
# stepped outline, which is the point. check_ziggurat.
ZIG_PAD_X, ZIG_PAD_Y = CARDS_X, CARD_GAP_Y // 2
PANEL_LAYOUT["ic_zig_bg"] = (
    0, PANEL_LAYOUT["ic_lbl_section"][1] + PANEL_LAYOUT["ic_lbl_section"][3] + 4, PANEL_W,
    CARD_GRID[-1][1] + CARD_H + ZIG_PAD_Y
    - (PANEL_LAYOUT["ic_lbl_section"][1] + PANEL_LAYOUT["ic_lbl_section"][3] + 4))
# ---------------------------------------------------------------------------
# THE INTRIGUE TAB: ONE COLUMN PER CATEGORY OF MOVE.
#
# The moves used to be rows in a five-column list this view used three of, with
# the name and the blurb concatenated into a cell widened to 1102 for this tab
# alone. The content is a name, a paragraph, a price and a button; the table was
# fighting it.
#
# A COLUMN PER CATEGORY, read top to bottom. Nine cards in undifferentiated
# bands said nothing about which moves are alternatives to each other; a column
# per category says "these four do the same kind of thing to a man" without a
# word of explanation.
#
# THE DEEPEST CATEGORY SETS THE CARD HEIGHT, so moving a move between categories
# is a layout change - which is why both the categories and the counts are read
# out of the model rather than typed here.
def _model_src():
    return io.open(os.path.join(
        ROOT, "Modding Files", "pack", "script", "campaign", "mod",
        "zzz_derpy_iron_court.lua"), encoding="utf-8").read()


def plot_cats():
    """[(key, display name)] from IC.PLOT_CATS, in its own order."""
    src = _model_src()
    blk = src[src.index("IC.PLOT_CATS = {"):]
    blk = blk[:blk.index(chr(10) + "}")]
    return re.findall(r'key\s*=\s*"(\w+)"\s*,\s*name\s*=\s*"([^"]+)"', blk)


def plot_counts():
    """How many moves each category holds, in plot_cats() order.

    Read out of IC.PLOTS' own `cat` fields. A category with no moves counts 0 and
    draws no column, which is what keeps this honest when one is emptied.
    """
    src = _model_src()
    blk = src[src.index("IC.PLOTS = {"):]
    blk = blk[:blk.index(chr(10) + "}")]
    cats = [c for c, _n in plot_cats()]
    got = re.findall(r'cat\s*=\s*"(\w+)"', blk)
    return [got.count(c) for c in cats]


PLOT_CATS = plot_cats()
PLOT_COUNTS = plot_counts()
PLOT_COLS = len(PLOT_CATS)
PLOT_DEPTH = max(PLOT_COUNTS)
# THE HEADER STRIP IS THE CATEGORY NAMES. It sits where the row list's headers
# sat, so nothing else on the panel moved to make room for it.
PLOTS_X = CARDS_X
# 20 ABOVE THE ROWS, so the taller plate costs the cards nothing.
PLOTS_HDR_Y = ROWS_Y - 20
PLOTS_HDR_H = HEADING_H
PLOTS_Y = PLOTS_HDR_Y + PLOTS_HDR_H + 10
# BOTH DERIVED. Four columns of the content width, and whatever height the
# deepest column leaves between the first card and the pager.
PLOT_W = (CONTENT_W - (PLOT_COLS - 1) * CARD_GAP_X) // PLOT_COLS
PLOT_H = ((PANEL_LAYOUT["ic_page_prev"][1] - 6 - PLOTS_Y
           - (PLOT_DEPTH - 1) * CARD_GAP_Y) // PLOT_DEPTH)


def plot_col_x(col):
    return PLOTS_X + col * (PLOT_W + CARD_GAP_X)


def plot_grid(counts=None):
    """Top-left of every move card, column by column, in plot_cats() order.

    ICUI.PLOT_XY is this list and import_iron_court.py compares them position by
    position: a grid built twice from one rule is a grid built twice.
    """
    counts = PLOT_COUNTS if counts is None else counts
    out = []
    for col, n in enumerate(counts):
        for row in range(n):
            out.append((plot_col_x(col), PLOTS_Y + row * (PLOT_H + CARD_GAP_Y)))
    return out


# ONE HEADER PER COLUMN, a panel child like every other: the cards are their own
# components and cannot carry the name of the column they sit in.
for _i in range(PLOT_COLS):
    PANEL_LAYOUT["ic_plotcat_%d" % (_i + 1)] = (plot_col_x(_i), PLOTS_HDR_Y,
                                                PLOT_W, PLOTS_HDR_H)

# THE BLURB IS THREE CELLS, NOT ONE, and that is not a style choice.
# gen_iron_court_emitter writes texthbehaviour="Never split" on every cell it
# emits, deliberately: of the three values twui has, none WRAPS - "Resize" breaks
# to one word per line and draws outside the height the component declares, which
# was measured on screen. So a string too long for its cell is cut mid-word, and
# more lines means more components. ICUI.fit_lines measures the split with the
# engine's own TextDimensionsForText, the way ICUI.fit_two already does for a
# rolled party name.
# FOUR LINES, NOT THREE. Six of the nine blurbs want a fourth at the panel's one
# content size, measured against the engine's width rather than the desktop
# face's - see GAME_FONT_WIDER, which is the correction that surfaced them. The
# line is paid for out of the foot pad and the four pixels between the icon and
# the first line, not out of the card, which is derived from the deepest column
# and cannot grow.
PLOT_BLURB_LINES = 4
PLOT_PAD = 30
PLOT_INNER_W = PLOT_W - 2 * PLOT_PAD
# AN ICON PER MOVE, left of its name. The tab is nine cards of similar shape and
# a reader picks the one they want by silhouette long before they read a title.
# The art is CA's own Chaos Dwarf and Chaos icons - see PLOT_ICON.
PLOT_ICON_PX = 40
PLOT_LAYOUT = {
    "ic_plot_icon": (PLOT_PAD, 26, PLOT_ICON_PX, PLOT_ICON_PX),
    "ic_plot_name": (PLOT_PAD + PLOT_ICON_PX + 8, 30,
                     PLOT_INNER_W - PLOT_ICON_PX - 8, 20),
}
for _i in range(PLOT_BLURB_LINES):
    PLOT_LAYOUT["ic_plot_b%d" % (_i + 1)] = (PLOT_PAD, 68 + _i * 18,
                                             PLOT_INNER_W, 18)
# THE PRICE AND THE BUTTON SHARE THE LAST LINE, the price where a reader starts
# and the button where a thumb goes. Bottom-anchored off PLOT_H so the blurb
# above can grow a line without moving either by hand.
# A SMALLER PAD AT THE FOOT than at the sides: at PLOT_PAD the price row started
# at y=122 and the third blurb line ends at 126, so the two overlapped by four
# pixels - which draws as a price through a sentence and errors nowhere.
# check_plot_cells() below refuses any overlap now, so this cannot come back.
PLOT_FOOT_PAD = 10
PLOT_LAYOUT["ic_plot_cost"] = (PLOT_PAD, PLOT_H - PLOT_FOOT_PAD - 22, 110, 22)
PLOT_LAYOUT["ic_plot_go"] = (PLOT_W - PLOT_PAD - 90,
                             PLOT_H - PLOT_FOOT_PAD - 22, 90, 22)


# Cells that are MEANT to sit on top of each other, and why. A pair here is a
# decision somebody wrote down; a pair not here is the silent kind - twui draws
# overlapping cells without complaint and the later one simply wins.
CELL_OVERLAP_OK = frozenset([
    # The portrait is a picture and the porthole frame that sits over it is a
    # second picture; the frame is supposed to be on top of the face.
] + [
    # A PARTY BLOCK MAN'S SECOND LINE is his influence or the Win button that
    # would buy him, never both: ICUI.fill_law_block shows exactly one, and the
    # harness's "LB_MEN men at most" check holds it to that.
    frozenset(("ic_lb_inf_%d" % (i + 1), "ic_lb_win_%d" % (i + 1))) for i in range(LB_MEN)
])


def check_card_cells(layout, w, h, what):
    """No two cells of a card may share a pixel, and none may leave it.

    THE OFFICE CARD IS IN THIS NOW, and was the reason for widening it. Its
    term line was moved to the card's full width on 2026-09-14 to fit the
    panel's one content size, which put it straight through the portrait beside
    it - and the only checks the office card had were the frame-band ones, which
    an overlap in the middle of the card passes cleanly.

    A card's cells are all derived from its height, which is derived from the
    shape of the thing it draws - the ziggurat's tiers, the deepest move
    category, the party grid - so reshaping the model reshapes every card, and
    this is the failure mode that reshaping has.
    """
    out = []
    boxes = sorted(layout.items(), key=lambda kv: (kv[1][1], kv[1][0]))
    for i, (n1, (x1, y1, w1, h1)) in enumerate(boxes):
        if x1 < 0 or y1 < 0 or x1 + w1 > w or y1 + h1 > h:
            out.append("%s leaves the %s: %d,%d %dx%d in %dx%d"
                       % (n1, what, x1, y1, w1, h1, w, h))
        for n2, (x2, y2, w2, h2) in boxes[i + 1:]:
            if (x1 < x2 + w2 and x2 < x1 + w1
                    and y1 < y2 + h2 and y2 < y1 + h1
                    and frozenset((n1, n2)) not in CELL_OVERLAP_OK):
                out.append("%s and %s overlap on the %s" % (n1, n2, what))
    return out


def check_plot_cells():
    """Kept as a name, because the comment above PLOT_FOOT_PAD cites it."""
    return check_card_cells(PLOT_LAYOUT, PLOT_W, PLOT_H, "move card")

# WHAT STANDING LOOKS LIKE IN A STRING. CA's own inline image markup, and
# BOTH HALVES OF WHAT THIS DOES ARE VANILLA - measured 2026-09-13 over every
# .loc in every pack in the game's data folder, and over CA's shipped Lua:
#
#   - 5001 loc rows use [[img:]], naming 503 distinct registry keys and 156
#     distinct FULL PATHS. The path form is not a trick: it is how CA draws
#     ui/skins/default/icon_stat_armour.png, in 61 rows on its own.
#   - script/campaign/wh3_dlc26_ogre_camps.lua CONCATENATES the markup into a
#     string in Lua, at runtime, exactly as ICUI.cost does.
#
# The loc rows alone would only prove the renderer takes a path; that one CA
# script is what proves it takes the markup from Lua. Neither half was worth
# guessing at when both read offline.
#
# The panel Lua declares the same path as ICUI.COST_ICON and check 23 holds the
# two against each other, because 20c measures the string this constant builds
# and the Lua draws the string that one does: two copies of one picture.
COST_ICON = "ui/skins/default/icon_secure_loyalty.png"
COST_MARKUP = "[[img:%s]][[/img]]" % COST_ICON

# AND THE EFFECT ICON THE THREE TRAIT CELLS WEAR. A party's two traits and its
# leader's one are terms in IC.loyalty_terms - they move the drift every turn -
# and they drew as bare words among other bare words.
#
# THE SAME FILE AS gen_iron_court.BUNDLE_ICON, which every effect bundle this mod
# mints already wears, and 24x24 at full bleed - a line box exactly. NOT named
# by importing it: these two generators are read independently and a build that
# silently followed a change made for the Faction Effects panel would move a
# picture on the court card for a reason nobody looking at the card could see.
#
# THE MARKUP IS HERE BECAUSE THE MEASUREMENT NEEDS IT. _measure charges a line
# box per [[img:]], and these are the narrowest cells on the card - measuring
# the bare name would be measuring a string the panel does not draw.
TRAIT_ICON = "ui/campaign ui/effect_bundles/chd_conclave_influence.png"
TRAIT_MARKUP = "[[img:%s]][[/img]]" % TRAIT_ICON
# The cells that wear it, and the panel helper that puts it there.
TRAIT_CELLS = ("ic_party_ltrait", "ic_party_t1", "ic_party_t2")
TRAIT_FN = "ICUI.trait_line"

CARD_LAYOUT = {
    # THE CARD THAT CANNOT GROW, and everything below follows from that.
    #
    # 364x184, and both numbers are the ziggurat's: fourteen seats whose widest
    # band is five sets the width, four bands set the height. Reshaping the
    # court to fit a font was put to the author on 2026-09-14 and declined, so
    # this card carries the panel's content size nowhere - it is the one tab
    # that keeps a smaller pair, and the cells are dealt to make the most of
    # 298x124 rather than to match the other four tabs.
    #
    # WHAT THE MEASUREMENT CHANGED. Under GAME_FONT_WIDER the old deal clipped
    # in two places nobody had seen: the term line wanted 201px of the 184 the
    # column beside the face leaves, and the price wanted 102 of its 90. Both
    # were passing only because the check measured a desktop face at face value.
    #
    # THREE CELLS NEED THE FULL WIDTH and the card has exactly three rows that
    # can give it - the name at the top, the strip under the face, and the
    # effect line at the floor. The name and the effect already had theirs. The
    # strip under the face is the one that was empty, and the term is what goes
    # in it, because the term is the string with no other home: at 190px it does
    # not fit at any size a player can read.
    #
    # THE PRICE AND ITS BUTTON take the term's old place beside the face, split
    # 74/112 rather than 90/96 - "APPOINT" wants 66px and the price, icon and
    # all, wants 102, so the wide half goes to the price. That is the opposite
    # of the old split and the old split is why the price clipped.
    "ic_card_name": (30, 30, 304, 20),
    # THE FACE PAYS FOR IT, being the only cell on this card with room to give:
    # 106x58 is a portrait drawn half again as wide as it is tall, and this is
    # nearer the shape a porthole is. Everything right of it moves 26px left.
    "ic_card_port": (30, 54, 86, 47),
    "ic_card_holder": (124, 52, 210, 20),
    "ic_card_crest": (124, 74, 16, 16),
    "ic_card_house": (144, 74, 190, 16),
    # 106 AND NOT 74, because 74 was never the label's to spend. The plate is a
    # 9-slice with an 8px cap at each end, so "APPOINT" had 58px of flat middle
    # and measures 67 - it drew across both corners of its own frame, which is
    # the 2026-09-17 screenshot. See BTN_CELLS: the rule that says so is now a
    # check, and it fails on the old number.
    "ic_card_button": (124, 90, 100, 22),
    "ic_card_need": (228, 90, 106, 22),
    "ic_card_term": (30, 114, 304, 18),
    "ic_card_effect": (30, 136, 304, 18),
}

# Rows are created into the PANEL itself - that is what both shipped mods do, and
# a holder buys nothing when every child has to be MoveTo'd by hand anyway. These
# are the row origin, panel-relative, and the Lua declares the same two numbers.
# 332, not 252: the pie is 144px tall where the ring of pips was 94, and the
# rows start under it and under the header strip. The list loses one of its
# eleven rows to that and the pager moves down six pixels - check 15 and check
# 16 are what decide which of those gives.
# ROW_PITCH and VISIBLE_ROWS are ONE decision, not two. ROWS_Y is 192 and
# ic_alert's top is 838, so the pool has 646px whatever it does with them: 15 rows
# spends that at pitch 43, which caps the face at 36px tall, and 10 rows at pitch
# 64 buys a 57px one. Check 15 below re-derives the arithmetic and refuses if a
# future edit overruns the alert bar.
# How many row components exist. The list scrolls an offset through this fixed
# pool rather than creating and destroying components, because neither shipped
# mod destroys a component at all and re-creating one that exists is how you get
# two. Fifteen is the house count, so the court view never needs to scroll; the
# governors view does, because a large empire holds far more provinces than this.
# NOT MAX_HOUSES. The court view lists 15 houses in a 10-row pool and therefore
# SCROLLS; that is the price of a face big enough to recognise, and the scrollbar
# it needs was built and mutation-tested when the rows first grew.
VISIBLE_ROWS = 12

# ---------------------------------------------------------------------------
# The party card
# ---------------------------------------------------------------------------
# ONE CARD PER PARTY, where the court's list used to be. A party now has to show
# its name, its leader's face, its leader's name, his trait and its own two
# traits - six lines and a picture - and a row has five text cells shared with
# every other view in the panel.
#
# TWO ACROSS, IN THE RIGHT COLUMN. It was five across the whole panel, which is
# what a band under the dial could hold; a column half the panel's width holds
# two, and each card is a hundred pixels wider for it - the name cell went from
# 280 to 371, which is most of the reason a rolled name needed two lines.
#
# DERIVED FROM COL_W, exactly as the five were derived from CONTENT_W. The
# office card's grid is still the panel-wide sum and the two no longer agree,
# because they are no longer the same question.
PARTY_COLS = 2
PARTY_GAP_X, PARTY_GAP_Y = CARD_GAP_X, CARD_GAP_Y
PARTY_W = (COL_W - (PARTY_COLS - 1) * PARTY_GAP_X) // PARTY_COLS
# THE TOP OF THE COLUMN'S BODY. The grid no longer waits for the dial: the dial
# is beside it, not above it, so the only thing overhead is the column header.
PARTIES_X = COL_R_X
PARTIES_Y = COL_BODY_Y
# ABOVE THE PAGER, not above the alert bar: a court can hold more parties than
# the grid and the pager is what the next one needs, so the grid may not use the
# room the pager sits in even on the pages where it is hidden.
PARTY_ROWS = 3
PARTY_H = ((PANEL_LAYOUT["ic_page_prev"][1] - 6 - PARTIES_Y
            - (PARTY_ROWS - 1) * PARTY_GAP_Y) // PARTY_ROWS)
# SIX, NOT TEN. Two columns in this height is three rows, and the biggest court
# a difficulty rolls - Ruthless, the Crown plus five rivals - is exactly six, so
# every rolled court fits one page and only confederates reach a second.
PARTY_SLOTS = PARTY_COLS * PARTY_ROWS
def party_grid():
    return [(PARTIES_X + col * (PARTY_W + PARTY_GAP_X),
             PARTIES_Y + row * (PARTY_H + PARTY_GAP_Y))
            for row in range(PARTY_ROWS) for col in range(PARTY_COLS)]


PARTY_GRID = party_grid()

# The same 9-slice band the office card wears, because it is the same frame
# texture: panel_back_border.png own corner ornament measures 27x28 on the
# 256x256 source and a margin under 30 cuts through it.
PARTY_BAND = 30
_PIW = PARTY_W - 2 * PARTY_BAND
_PB = PARTY_BAND
# THE FACE'S SIZE, AND THE TEXT COLUMN DERIVED FROM IT. The column was a typed
# 114 and 20g caught the result at ONE PIXEL over: the longest character name
# the game can hand this cell measured 185px in the 184 that left. A typed
# offset cannot follow the picture it sits beside, so it does not stay typed.
#
# 120x66 is the porthole's 300x164 to within 0.6%, which is inside what check 8c
# allows before SetImagePath starts visibly stretching a face.
#
# IT GREW WITH THE TEXT. The card is 455x266 and its contents used to stop at
# y=162 with the footer pinned at 214 - fifty-two pixels of nothing across the
# middle of six cards, with 12px text either side of it. Every line on this card
# is BODY now (16, the largest body size the game has) and the face grew to match,
# because a 98px porthole beside 16px text reads as a thumbnail rather than a man.
# 100x55, not 120x66. Same aspect - check 8c refuses a portrait cell more than
# 6% off 300x164, because SetImagePath makes the image take the CELL's shape -
# and the 20px it gives back go to the three text cells beside it, where
# "Drazhoath the Ashen of Hashut" wants 278px of the 261 it had at the panel's
# one content size.
_PPW, _PPH = 100, 55
_PTX = _PB + _PPW + 8
_PTW = _PIW - (_PTX - _PB)
# THE LOWER HALF IS TWO COLUMNS (author, 2026-09-24: "add more party
# statistics"). The traits keep the left one at a width their longest name and
# its icon fit; the right one takes the three counts that had no cell at all.
# 225 is "Zealots of Hashut" (188 at BODY) plus the icon's line box plus the
# label inset, and the right column is whatever is left after an 8px gutter.
_PLW = 236
_PRX = _PB + _PLW + 4
_PRW = _PB + _PIW - _PRX
# THE MOOD, AS WORDS, beside the second name line. It was the label on the
# card's one button, and that button opened the favour list; the author asked
# for the reading and the control to be separate, so the word stays on the card
# and the control became clicking the card itself.
_PSW = 166
PARTY_LAYOUT = {
    # THE NAME GETS TWO LINES because it has to. The longest rolled name
    # measures 278px at header_14 in a 298px cell - it fits - but the Crown and
    # every confederated party wear a FACTION's display name instead, and that
    # is a string this mod does not write and cannot bound. So the Lua measures
    # with the engine's own TextDimensionsForText and spills what will not fit
    # onto the second line; a card whose name is short simply leaves it empty.
    # THE SECOND LINE SHARES ITS ROW WITH THE MOOD now, so it is the name's
    # tail and not a whole second line. What spills is a word or two.
    "ic_party_crest": (_PB, _PB, 24, 24),
    "ic_party_name": (_PB + 30, _PB, _PIW - 30, 24),
    "ic_party_name2": (_PB, _PB + 28, _PIW - _PSW - 8, 24),
    "ic_party_state": (_PB + _PIW - _PSW, _PB + 28, _PSW, 24),
    # THE MAN WHO SPEAKS FOR THEM. Same cell shape as the office card's, which
    # is the porthole's own 300x164 scaled down - check 8c holds both to it.
    "ic_party_port": (_PB, _PB + 58, _PPW, _PPH),
    "ic_party_leader": (_PTX, _PB + 58, _PTW, 22),
    # HIS TRAIT, BESIDE HIM AND NOT WITH THE PARTY'S TWO. It is derived from
    # whoever currently leads rather than stored, so it dies with him - and a
    # player who cannot see which of the three is his cannot see that killing
    # him changes one of them.
    "ic_party_ltrait": (_PTX, _PB + 82, _PTW, 22),
    "ic_party_nums": (_PTX, _PB + 106, _PTW, 22),
    "ic_party_t1": (_PB, _PB + 132, _PLW, 22),
    "ic_party_t2": (_PB, _PB + 156, _PLW, 22),
    # WHICH WAY LOYALTY IS GOING, under the traits that move it. The number is
    # IC.loyalty_net over IC.loyalty_terms - the sum the turn applies - and the
    # breakdown behind it is the same tooltip ic_party_nums carries.
    "ic_party_trend": (_PB, _PB + 180, _PLW, 22),
    # THE THREE COUNTS: its men, the seats they hold, the provinces they
    # oversee. "N seats at court" was the only one of them the card showed.
    "ic_party_members": (_PRX, _PB + 132, _PRW, 22),
    "ic_party_offices": (_PRX, _PB + 156, _PRW, 22),
    "ic_party_govs": (_PRX, _PB + 180, _PRW, 22),
}

OPENER_W, OPENER_H = 44, 44

PLATE = "ui/skins/default/button_round_medium_%s.png"
OPENER_SOUND = "UI_GBL_TMP_Round_Medium_Button"

# Body then border: the border draws over the body's edge, so filling the whole
# component cannot leave a bare strip. Both tile - a stretched plate is a smear.
# CA's own Hell-Forge backdrop, measured at exactly 1920x1080 in ui2.pack - the
# design size, so it neither stretches nor tiles. ONE layer and no frame: the
# Tower of Zharr has no outer border either, and a frame around a full-bleed
# background just draws a box round the screen.
#
# margin 0 with tile OFF. It is a PICTURE, not a 9-slice: tiling it would repeat
# the furnace across the panel, which is exactly what a frame at margin 0 did on
# 2026-09-11.
# Literal, not "%s/panel_bg.png" % PLATE_DIR: PLATE_DIR is declared 150 lines
# below this, with the plate builders that use it.
PANEL_BG = "ui/derpy_ic/panel_bg.png"
PANEL_LAYERS = [
    # OUR OWN BACKDROP, not CA's Hell-Forge one. Built from
    # Modding Files/reference/morgan-ketelaar-jarass-wh3-winmovie-shot04.jpg -
    # the Chaos Dwarf win-movie keyframe, a throne room, which is what this
    # panel is a picture of.
    #
    # THE SOURCE IS 1920x1140 AND THE BOTTOM 140 ARE NOT ART: the TOTAL WAR
    # WARHAMMER III logo and, under it, a flat bar with the artist's credit and
    # the GW/SEGA/CA marks. Both were measured off the image and cut; left in,
    # they would draw across the card grid and the alert bar. What is left is
    # scaled to fill 1920x1080 and centre-cropped 77px a side, which the
    # composition survives because it is symmetric about the throne.
    #
    # margin 0 with tile OFF, exactly as CA's was. It is a PICTURE, not a
    # 9-slice: tiling it would repeat the throne room across the panel.
    {"path": PANEL_BG,
     "offset": (0, 0), "dw": 0, "dh": 0, "margin": 0, "dock": None},
]

ROW_LAYERS = [
    {"path": "ui/skins/default/1x1_blank_white.png",
     "offset": (0, 0), "dw": 0, "dh": 0, "margin": 0, "colour": "#00000055",
     "dock": None},
]

CARD_LAYERS = [
    # MARGIN 4, not 2. panel_back_tile.png is a 4px TRANSPARENT ring round an
    # rgb(11,11,11) field; sliced at 2 the tiled centre carried that ring and
    # repeated it every 252px across the card - visible vertical banding.
    # AND STRETCHED, NOT TILED. At 4 the centre is one flat colour, which tiles
    # cleanly only at 1:1: on a scaled UI a seam can sample the alpha-0 ring.
    # A flat colour stretched has no seam. See FLAT_CENTRE.
    {"path": "ui/skins/default/panel_back_tile.png",
     "offset": (0, 0), "dw": 0, "dh": 0, "margin": 4, "dock": None},
    # MARGIN 30, not 18. A 9-slice margin has to clear the ornament in the
    # SOURCE texture, which is a different question from whether it fits the
    # box - and the box question was the only one being asked. Measured on the
    # 256x256 panel_back_border.png: the corner runs 27px in from the left and
    # 28 down from the top, so an 18 slice halves the corner and stretches the
    # offcut along the rails. Corners that do not meet their own edges.
    #
    # THE CHAOS DWARF FRAME SINCE 2026-09-26 (author: "use more of the chaos
    # dwarf ui borders and elements"): the Hell-Forge's own name holder, a
    # bronze rim round a dark field, trimmed out of CA's 144x51
    # cap_group_name_holder.png to its 114x51 alpha box (CHD_CUTS). STRETCHED:
    # its field is not flat, and a tiled one repeats. It was CA's generic
    # panel_back_border.png at margin 30, tiled.
    {"path": "ui/derpy_ic/chd_frame.png",
     "offset": (0, 0), "dw": 0, "dh": 0, "margin": 8, "dock": None},
]
# The smallest 9-slice margin that keeps the frame's rim and its rounded
# corners whole, measured off the trimmed source: the bronze is 3px and the
# corners round off inside 6. Check 18 holds every use of that texture to it.
BORDER_TEXTURE = "ui/derpy_ic/chd_frame.png"   # literal: PLATE_DIR is below
BORDER_CORNER = 6

# The smallest 9-slice margin each CA texture can take, MEASURED off the
# source rather than chosen. Below it the slice cuts an edge feature and then
# stretches or repeats the offcut across the component - silently, and looking
# like the art is broken rather than like a number is wrong.
#
#   panel_back_border.png  256x256, corner ornament 27 across and 28 down
#   panel_back_tile.png    256x256, a 4px pure-black border round rgb(11,11,11)
#
# margin 0 is NOT in scope: that is the no-9-slice mode, a different thing.
# THE SEATS COUNTER'S PLATE (author, 2026-09-25: "add background ui for the
# number of seats present"). CA's frame_text.png out of ui2.pack - a dark field
# inside a thin gold rule, 27px tall at native size, which is the counter's own
# height, so it draws near 1:1. Its text is centred and kept SEATS_PAD clear of
# each end, and check 20g measures it there.
# THE HELL-FORGE'S OWN SUBTITLE PLATE SINCE 2026-09-26, the same idea in the
# race's bronze: dlc23_chd_hell_forge/sub_title.png, 113x30, a 3px rim round a
# near-black field whose corners round off by 6.
SEATS_FRAME = "ui/skins/default/dlc23_chd_hell_forge/sub_title.png"
SEATS_PAD = 10
SEATS_LAYERS = [{"path": SEATS_FRAME, "offset": (0, 0), "dw": 0, "dh": 0,
                 "margin": 6, "dock": None}]

# THE TITLES SIT ON THE HELL-FORGE'S SECTION TITLE (author, 2026-09-26:
# "parties of the court and control of the court doesnt have any background").
# side_panel_title.png, the spiked bar with arrow ends, SHRUNK to HEADING_H by
# cut_chd_art rather than squashed by the engine: its dark field is rows 17-66
# of 90, so at 44px the field is 24px and a 20px heading sits INSIDE it.
#
# NOT sub_title, which this was for one build: a 3px rim round a field as dark
# as the backdrop reads as an outline, and in a 24px cell the 20px text covered
# both rims, so every heading looked struck through (author: "it looks poorly
# implemented"). And NOT on every heading: the list's column headings and the
# sentence under the tabs stay bare - a plate per table column, or one 1884px
# wide under a sentence, is a row of boxes, not a title.
HEADING_ART = "ui/derpy_ic/chd_heading.png"
# The arrow and its bracket end at column 68 of 90 rows: 68 * 44 / 90, rounded up.
HEADING_CAP = 34
HEADING_TY = "0.00,4.00"
HEADER_LAYERS = [{"path": HEADING_ART, "offset": (0, 0), "dw": 0, "dh": 0,
                  "margin": (0, HEADING_CAP), "dock": None}]

TEXTURE_MIN_MARGIN = {
    BORDER_TEXTURE: BORDER_CORNER,
    "ui/skins/default/panel_back_tile.png": 4,
    # 113x30: a 3px bronze rim with corners that round off by 6.
    SEATS_FRAME: 6,
}

# CA textures whose 9-slice CENTRE is one flat colour, measured off the source.
# Such a centre STRETCHES rather than tiles: stretched it is the same picture,
# and tiled, a repeat drawn at anything but 1:1 samples the alpha-0 ring round
# panel_back_tile's field. A bilinear model at 0.8 puts a faint seam at some
# repeats. NOT the light lines seen in game 2026-09-24 - those crossed opaque
# frames and bare backdrop, which a fill seam cannot - so this is hygiene, not
# the fix for them.
FLAT_CENTRE = {"ui/skins/default/panel_back_tile.png"}

# SetImagePath(path, 0) REPLACES an existing image layer; it does not create one.
# A component with no images has no index 0, so the call quietly does nothing and
# the crest never appears. White, so the flag draws in its own colours instead of
# being tinted by whatever placeholder sat underneath it.
PORT_LAYERS = [
    {"path": "ui/skins/default/1x1_blank_white.png",
     "offset": (0, 0), "dw": 0, "dh": 0, "margin": 0, "colour": "#FFFFFFFF",
     "dock": None},
]

# The office card's portrait, same idea one size up: a blank plate at index 0 for
# the face to replace, and the frame at index 1 so it survives the swap. The card
# cell cannot reuse CARD_LAYERS, whose index 0 is panel_back_tile at
# 9-slice margin 4 - a portrait written over that gets 9-sliced, which stretches
# the middle of a face and leaves its edges at native scale.
# ONE LAYER, not two. The second was panel_back_border at 9-slice margin 18 -
# the SAME ornate frame the card itself already draws, redrawn 12px inside it. On
# a vacant card you see one border; the moment an officer is appointed a second
# nested border appears around the face, which is what "the portrait is doubled
# when assigned" is. The card's own frame is the frame; the portrait needs none.
CARD_PORT_LAYERS = [
    {"path": "ui/skins/default/1x1_blank_white.png",
     "offset": (0, 0), "dw": 0, "dh": 0, "margin": 0, "colour": "#FFFFFFFF",
     "dock": None},
]


# One colour per house, INDEXED BY HOUSE, not by position in the court. All ten
# segments shipped the same red on 2026-09-11, so the bar read as one solid block
# and told the player nothing. There is no runtime colour API - nothing in CA's
# docs, nothing in either shipped mod - so the colour is baked per component here,
# and the Lua must address a segment by HOUSE index so a house keeps its colour
# when a house ahead of it leaves the court.
#
# KEYED BY SLUG, not ordered. This was a list of fifteen colours whose pairing
# with IC.HOUSES lived in the comment at the end of each line, and the only thing
# checked was that the two were the same LENGTH - so adding a house anywhere but
# the bottom would have moved every colour below it onto the wrong house, with
# nothing to say so. A missing slug is now a KeyError at import.
HOUSE_COLOUR = {
    "crown":  "#8C2F26FF",   # bull-cult red - the player's own
    "temple": "#B8862BFF",   # brass
    "forge":  "#C4541EFF",   # burnt orange
    "chain":  "#57575FFF",   # iron grey
    "legion": "#3F4A8CFF",   # indigo
    "ledger": "#1F6B57FF",   # deep green
    "tower":  "#6B3A8CFF",   # sorcerous purple
    "road":   "#8C6A2FFF",   # dust
    "hearth": "#2F5D6BFF",   # sea teal
}
# A COLOUR PER ABSORBED FACTION. Distinct from the nine and from each other:
# check 14 refuses a repeat, because two identical segments on the bar read as
# one party with twice the weight.
CONFED_COLOUR = {
    "khorakk":    "#A33A3AFF",   # bull red, lighter than the crown's
    "uzkulak":    "#1E5B8CFF",   # sea blue
    "artificers": "#7A7A2FFF",   # brass olive
    "fists":      "#B0482FFF",   # rust
    "horns":      "#8C3A6BFF",   # temple magenta
    "baal":       "#6B2F2FFF",   # dried blood
    "azeros":     "#2F8C7AFF",   # jade
    "bzaark":     "#8C1E1EFF",   # fresh blood
    "blackdwarf": "#3A3A3AFF",   # near black
    "kraken":     "#1E3A6BFF",   # deep navy
    "conclave":   "#C49A2FFF",   # gold
    "astragoth":  "#6B5B8CFF",   # dull violet
    "azgorh":     "#A35B1EFF",   # ember
    "zhatan":     "#4A6B2FFF",   # campaign olive
    "skullstack": "#8C8C8CFF",   # bone
    "zharrduk":   "#5B3A1EFF",   # plain earth
}
# IN SEAT ORDER: the nine interests first, then the factions in IC.ORIGINS
# order. bar_layers() indexes this list by SEGMENT, and the model hands each
# confederate party the segment its origin owns - so a colour out of order here
# is a bloc drawn in another faction's colour.
BAR_COLOURS = ([HOUSE_COLOUR[p[0]] for p in IC.PARTIES]
               + [CONFED_COLOUR[slug] for slug in CONFED_SEATS])

# ---------------------------------------------------------------------------
# The house plate: what is BEHIND the character's face.
# ---------------------------------------------------------------------------
# A porthole is a CUT-OUT - measured across the shipped art, 27% to 54% of every
# one is fully transparent with a soft 1-3% edge - so whatever sits under it
# shows through, and that is the only way a house colour can reach a portrait.
# There is no runtime colour or tint call on a uicomponent: SetColour, SetColor,
# SetCurrentStateColour, SetImageColour and SetImageTint are all NOT DOCUMENTED
# in CA's reference. SetImagePath is, so the colour has to arrive as a picture.
#
# It is generated rather than drawn by hand so that the plate behind a house's
# officer and that house's segment on the standing bar are the same colour BY
# CONSTRUCTION.
#
# THE GRADIENT IS TOP-WEIGHTED because that is the part of the plate a porthole
# does not cover: the body fills the bottom of the frame and the head the middle,
# leaving the top edge and the upper corners. A bottom-weighted gradient - the
# first thing tried - put the colour exactly where the shoulders are and read as
# a plain black box.
GAME_DATA = os.path.join("F:" + os.sep, "SteamLibrary", "steamapps",
                         "common", "Total War WARHAMMER III", "data")
PLATE_DIR = "ui/derpy_ic"
PLATE_W, PLATE_H = 300, 164        # the porthole's own size and aspect
PLATE_BASE = (14, 12, 11)          # near-black, warm, the panel's own ground
# No house: a plate, not a hole. A portrait with no house behind it still wants
# something to sit on, or the cell reads as a missing image.
PLATE_NONE_COLOUR = "#2A2622FF"


def plate_path(slug):
    return "%s/house_plate_%s.png" % (PLATE_DIR, slug or "none")


def wedge_path(i, slug):
    """One slice of the pie, in one party's colour."""
    return "%s/wedge_%02d_%s.png" % (PLATE_DIR, i, slug or "none")


def sigil_path(slug):
    return "%s/party_sigil_%s.png" % (PLATE_DIR, slug)


# A PARTY NOT AT COURT (author, 2026-10-03): its sigil in grey, dimmed, for the
# laws tab's For/Against crests. An inline [[img:]] cannot be tinted at runtime,
# so the grey is a picture. ICUI.ABSENT_SIGIL names the same pattern.
ABSENT_DIM = 0.6


def absent_sigil_path(slug):
    return "%s/party_sigil_%s_absent.png" % (PLATE_DIR, slug)


# THE GOVERNMENT CARDS' PICTURES, UPSCALED (author, 2026-10-03, route A). CA ships
# its Chaos Dwarf tech icons at 72px only, and the card draws them at 112 (149 at
# 2560), where the engine's own scaling is soft. Each is written at GOV_ART_PX in
# two Lanczos steps with an unsharp pass between. The source names are the panel
# Lua's ICUI.GOV_ART, so the two cannot disagree on which picture a card wears.
GOV_ART_PX = 224


def gov_art_path(slug):
    return "%s/gov_%s.png" % (PLATE_DIR, slug)


def gov_art_sources(lua=None):
    """{our path: CA's path} for every ICUI.GOV_ART entry."""
    if lua is None:
        lua = open(os.path.join(ROOT, "Modding Files", "pack", "script", "campaign", "mod",
                                "zzz_derpy_iron_court_ui.lua"), encoding="utf-8").read()
    d = re.search(r'ICUI\.LAW_ART_DIR = "([^"]+)"', lua).group(1)
    g = re.search(r"ICUI\.GOV_ART = \{([^}]*)\}", lua)
    return dict((gov_art_path(k), d + v + ".png")
                for k, v in re.findall(r'(\w+) = "(\w+)"', g.group(1) if g else ""))


def upscale_art(img, px):
    """Twice the size by Lanczos, an unsharp pass, then down to px: the edges stay
    hard where one straight resize from 72 leaves them soft."""
    from PIL import Image, ImageFilter
    mid = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    mid = mid.filter(ImageFilter.UnsharpMask(radius=1.2, percent=90, threshold=2))
    return mid.resize((px, px), Image.LANCZOS)


def grey_rows(rows):
    """RGBA rows to luminance times ABSENT_DIM, alpha kept."""
    out = []
    for row in rows:
        buf = bytearray(row)
        for i in range(0, len(buf), 4):
            lum = int((buf[i] * 299 + buf[i + 1] * 587 + buf[i + 2] * 114) / 1000 * ABSENT_DIM)
            buf[i] = buf[i + 1] = buf[i + 2] = lum
        out.append(bytes(buf))
    return out


def div_path(i):
    """The wall between two parties, at the angle slice i begins on."""
    return "%s/div_%02d.png" % (PLATE_DIR, i)


# A PARTY HAS NO FLAG TO BORROW.
#
# A house was a faction and its crest was that faction's own mon_64.png, read
# off flag_path at runtime. A party is an interest inside one faction, so there
# is nothing to ask - and the crest column is how a player tells two parties
# apart at a glance on the bar, on a card and on every row.
#
# NO PIL. The plate above is a pure function of a colour and this is a pure
# function of a shape, for the same reason: check() compares what is on disk to
# what this file says, so the generator has to answer identically on a machine
# where Pillow is not installed, or the gate turns into an import error.
#
# Each emblem is a predicate over normalised coordinates - u and v both run -1
# to 1 - which is a rasteriser small enough to read and exact enough to compare
# byte for byte.
# 128, not 64. An emblem is drawn inside a FLAG now - see FLAG_SRC - and the
# frame's rails and corner studs are what a downscale eats first: measured at
# row size, a 64px source loses them and a 128px one keeps them. Nothing on this
# panel draws a crest above 40px, so 256 buys nothing but aliasing.
SIGIL = 128
# CA'S OWN FLAG FRAME, prepared once to SIGIL by scratchpad/prep_frame.py off
# the 256px master in Modding Files/source/flags/. THE FIELD IS PAINTED WHITE in
# that file and that is the whole contract: white is the field this generator
# fills, opaque-and-not-white is the frame it must not touch, and transparent is
# outside the flag. The frame could not be lifted out of the shipped Chaos Dwarf
# flags instead - measured 2026-09-13, ZERO pixels are identical across the
# seven of them, because the metal is painted per faction.
FLAG_SRC = os.path.join(ROOT, "Modding Files", "source", "ic_frame",
                        "flag_frame_%d.png" % SIGIL)
FLAG_WHITE = 232                   # a field pixel is at least this in all three
FLAG_CLEAR = 24                    # below this alpha it is outside the flag
# THREE SAMPLES PER PIXEL PER AXIS, so an edge that is not axis-aligned is a
# ramp and not a staircase. The first set of emblems was one sample per pixel
# and a hard boolean: every diagonal in them - the crown's spires, the wheel's
# spokes - came out as a flight of steps, and then the engine scaled that 64px
# staircase down to a 36px cell and to a 28px crest on the dial.
SIGIL_FINE = 3
# The outline, in FINE cells: a bit over one finished pixel. It is what lets a
# bronze emblem sit on a plate of any colour - including the pale ones, where
# bronze on its own would wash out.
SIGIL_HALO = 4
SIGIL_EDGE = (10, 9, 8)            # the outline, one pixel of the panel ground
# BRONZE, NOT THE PARTY'S OWN COLOUR. Every place an emblem is drawn - the row
# crest, the office card, the crest ring on the dial - the ground behind it is
# already that party's colour, so painting the emblem in it too left a shape
# picked out by nothing but a one-pixel dark line. These two are CA's own: the
# outer pixel of panel_back_border.png's top rail and of its bottom rail, so an
# emblem is lit from above in the same metal as the dial's rim.
SIGIL_LIT = (181, 152, 107)
SIGIL_SHADE = (119, 73, 43)


def _ring(u, v, r, w, cx=0.0, cy=0.0):
    d = ((u - cx) ** 2 + (v - cy) ** 2) ** 0.5
    return abs(d - r) < w


def _disc(u, v, r, cx=0.0, cy=0.0):
    return ((u - cx) ** 2 + (v - cy) ** 2) < r * r


def _box(u, v, u0, u1, v0, v1):
    return u0 <= u <= u1 and v0 <= v <= v1


def _seg(u, v, x0, y0, x1, y1, w):
    """Within w of the segment: a thick line with round caps.

    The one primitive the first set did not have, and the reason its chain was
    two circles side by side and its hammer a capital T.
    """
    dx, dy = x1 - x0, y1 - y0
    span = dx * dx + dy * dy
    t = 0.0 if span < 1e-12 else ((u - x0) * dx + (v - y0) * dy) / span
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    px, py = x0 + t * dx - u, y0 + t * dy - v
    return px * px + py * py < w * w


def _link(u, v, cx, cy, w=0.24, t=0.085):
    """One link of a chain: a stadium ring, tilted."""
    x0, y0 = cx - 0.16, cy - 0.22
    x1, y1 = cx + 0.16, cy + 0.22
    return (_seg(u, v, x0, y0, x1, y1, w)
            and not _seg(u, v, x0, y0, x1, y1, w - t))


# v IS NEGATIVE UPWARDS in every one of these: the rasteriser walks image rows,
# so row 0 - the top of the picture - is v = -1.
def _sigil_crown(u, v):
    """A banded crown: three spires with finials, two low points between."""
    if _box(u, v, -0.74, 0.74, 0.24, 0.50):
        return True                                   # the band
    if _box(u, v, -0.84, 0.84, 0.50, 0.64):
        return True                                   # the rim under it
    for c, top in ((-0.54, -0.58), (0.0, -0.76), (0.54, -0.58)):
        if top <= v <= 0.24 and abs(u - c) < 0.19 * ((v - top) / (0.24 - top)):
            return True                               # a spire
        if _disc(u, v, 0.10, c, top):
            return True                               # its finial
    for c in (-0.27, 0.27):
        if -0.14 <= v <= 0.24 and abs(u - c) < 0.14 * ((v + 0.14) / 0.38):
            return True                               # a low point
    return False


def _sigil_temple(u, v):
    """A flame: an ogive that leans, notched at the foot, with a second tongue."""
    if -0.84 <= v <= 0.70:
        t = (v + 0.84) / 1.54                         # 0 at the tip, 1 at the foot
        # THE LEAN IS AT THE TIP. A flame that leans all the way down is a
        # comma; one that leans only where it is thin is a flame.
        w = 0.44 * (t ** 0.62) * (1.0 - 0.30 * t ** 5)
        if abs(u - 0.16 * (1.0 - t) ** 2 - 0.06) < w:
            if not (v > 0.34 and abs(u - 0.06) < 0.22 * (v - 0.34) / 0.36):
                return True                           # minus the foot notch
    if -0.30 <= v <= 0.66:
        t = (v + 0.30) / 0.96
        if abs(u + 0.48 - 0.10 * (1.0 - t) ** 2) < 0.17 * (t ** 0.6):
            return True                               # the tongue beside it
    return False


def _sigil_forge(u, v):
    """An anvil: face, horn, waist and base."""
    if _box(u, v, -0.40, 0.52, -0.48, -0.14):
        return True                                   # the face
    if -0.44 <= v <= -0.16 and u <= -0.40:
        # THE HORN TAPERS TO A POINT off the left of the face, which is the
        # only line on an anvil nothing else has.
        t = abs(v + 0.30) / 0.14
        if u >= -0.40 - 0.44 * (1.0 - t):
            return True
    if _box(u, v, -0.16, 0.20, -0.14, 0.42):
        return True                                   # the waist
    if 0.42 <= v <= 0.68:
        t = (v - 0.42) / 0.26
        if abs(u - 0.04) < 0.36 + 0.18 * t:
            return True                               # the base, splaying out
    return False


def _sigil_chain(u, v):
    """Two links, interlocked. Two rings side by side read as a pair of goggles."""
    return _link(u, v, -0.26, -0.16) or _link(u, v, 0.26, 0.16)


def _sigil_legion(u, v):
    """Three chevrons, pointing up."""
    for k in (-0.46, -0.06, 0.34):
        if (_seg(u, v, -0.68, k + 0.32, 0.0, k, 0.10)
                or _seg(u, v, 0.0, k, 0.68, k + 0.32, 0.10)):
            return True
    return False


def _sigil_ledger(u, v):
    """A ruled tablet: a block with its lines cut out of it."""
    if not _box(u, v, -0.56, 0.56, -0.66, 0.66):
        return False
    if abs(u) < 0.05:
        return True                                   # the spine
    for k in (-0.36, -0.10, 0.16, 0.42):
        if abs(v - k) < 0.055 and 0.11 < abs(u) < 0.45:
            return False                              # a ruled line
    return True


def _sigil_tower(u, v):
    """A ziggurat: four tiers, a doorway and a shrine on the top."""
    if abs(u) < 0.09 and v > 0.54:
        return False                                  # the doorway
    if _box(u, v, -0.07, 0.07, -0.72, -0.56):
        return True                                   # the shrine
    for half, v0, v1 in ((0.84, 0.44, 0.70), (0.64, 0.18, 0.44),
                         (0.44, -0.10, 0.18), (0.24, -0.40, -0.10)):
        if _box(u, v, -half, half, v0, v1):
            return True
    return False


def _sigil_road(u, v):
    """A cart wheel: rim, hub and six spokes."""
    if _ring(u, v, 0.68, 0.11) or _disc(u, v, 0.16):
        return True
    for k in range(6):
        a = math.pi * k / 6.0
        c, sn = math.cos(a), math.sin(a)
        if _seg(u, v, -0.64 * c, -0.64 * sn, 0.64 * c, 0.64 * sn, 0.05):
            return True
    return False


def _sigil_hearth(u, v):
    """A hammer: a struck face, a tapered peen, a haft and a pommel."""
    if _box(u, v, -0.08, 0.08, -0.26, 0.62):
        return True                                   # the haft
    if _box(u, v, -0.34, 0.20, -0.70, -0.26):
        return True                                   # the head
    if -0.64 <= v <= -0.32 and u >= 0.20:
        # THE PEEN, tapering off the far side: without it a square head on a
        # straight haft is a capital T, which is what the first set drew.
        t = abs(v + 0.48) / 0.16
        if u <= 0.20 + 0.40 * (1.0 - t):
            return True
    if _disc(u, v, 0.14, 0.0, 0.62):
        return True                                   # the pommel
    return False


SIGIL_SHAPE = {
    "crown": _sigil_crown, "temple": _sigil_temple, "forge": _sigil_forge,
    "chain": _sigil_chain, "legion": _sigil_legion, "ledger": _sigil_ledger,
    "tower": _sigil_tower, "road": _sigil_road, "hearth": _sigil_hearth,
}


def _dilate_rows(grid, n, r):
    """A max filter along each row. Separable, so the other axis is a transpose."""
    out = []
    for row in grid:
        o = bytearray(n)
        for x in range(n):
            if any(row[x - r if x > r else 0:x + r + 1]):
                o[x] = 1
        out.append(o)
    return out


def _dilate(grid, n, r):
    """Grow the shape by r cells, which is where the outline gets drawn."""
    g = _dilate_rows(grid, n, r)
    g = _dilate_rows([bytearray(col) for col in zip(*g)], n, r)
    return [bytearray(col) for col in zip(*g)]


_FLAG = []


def flag_frame():
    """(rows, field, box) for the flag frame: its pixels, its field, its middle.

    THE BOX IS THE LARGEST CENTRED SQUARE THAT IS FIELD ALL THE WAY ROUND. The
    flag is not a rectangle - two corners are cut and the bottom-left runs in -
    so an emblem drawn to the white bounding box would be behind the frame at
    those corners, which is the kind of wrong that looks deliberate.
    """
    if _FLAG:
        return _FLAG
    rows = _read_png_rows(FLAG_SRC)
    if rows is None or len(rows) != SIGIL:
        raise IOError("the flag frame at %s is missing or is not a %dpx RGBA png "
                      "this generator can read - run scratchpad/prep_frame.py"
                      % (FLAG_SRC, SIGIL))
    field = []
    for r in rows:
        m = bytearray(SIGIL)
        for x in range(SIGIL):
            a = r[4 * x + 3]
            if a >= FLAG_CLEAR and min(r[4 * x], r[4 * x + 1], r[4 * x + 2]) > FLAG_WHITE:
                m[x] = a
        field.append(bytes(m))
    half, c = 0, (SIGIL - 1) // 2
    while True:
        k = half + 1
        if c - k < 0 or c + k >= SIGIL:
            break
        edge = [(x, c - k) for x in range(c - k, c + k + 1)]
        edge += [(x, c + k) for x in range(c - k, c + k + 1)]
        edge += [(c - k, y) for y in range(c - k, c + k + 1)]
        edge += [(c + k, y) for y in range(c - k, c + k + 1)]
        if any(field[y][x] < 200 for x, y in edge):
            break
        half = k
    _FLAG.append((rows, field, (c - half, c - half, 2 * half + 1)))
    return _FLAG


def glyph_pixels(slug, size):
    """RGBA rows for one party emblem at `size`: antialiased bronze on a dark
    outline, on transparent ground.

    NO PIL. The plate above is a pure function of a colour and this is a pure
    function of a shape, for the same reason: check() compares what is on disk
    to what this file says, so the generator has to answer identically on a
    machine where Pillow is not installed, or the gate turns into an import
    error.
    """
    shape = SIGIL_SHAPE[slug]
    n = size * SIGIL_FINE
    half = (n - 1) / 2.0
    fine = []
    for y in range(n):
        v = (y - half) / half
        row = bytearray(n)
        for x in range(n):
            if shape((x - half) / half, v):
                row[x] = 1
        fine.append(row)
    halo = _dilate(fine, n, SIGIL_HALO)

    cells = SIGIL_FINE * SIGIL_FINE
    rows = []
    for py in range(size):
        band = fine[py * SIGIL_FINE:(py + 1) * SIGIL_FINE]
        hband = halo[py * SIGIL_FINE:(py + 1) * SIGIL_FINE]
        # LIT FROM ABOVE, by the row and not by the pixel: the light on CA's
        # frame runs down the rail, and an emblem is small enough that anything
        # cleverer than a vertical ramp is invisible at 28 pixels.
        t = py / float(size - 1)
        lit = tuple(int(SIGIL_LIT[i] + (SIGIL_SHADE[i] - SIGIL_LIT[i]) * t)
                    for i in range(3))
        buf = bytearray(size * 4)
        for px in range(size):
            lo, hi = px * SIGIL_FINE, (px + 1) * SIGIL_FINE
            fill = sum(sum(r[lo:hi]) for r in band)
            edge = sum(sum(r[lo:hi]) for r in hband)
            if not edge:
                continue
            k = fill / float(cells)
            buf[4 * px + 0] = int(SIGIL_EDGE[0] + (lit[0] - SIGIL_EDGE[0]) * k)
            buf[4 * px + 1] = int(SIGIL_EDGE[1] + (lit[1] - SIGIL_EDGE[1]) * k)
            buf[4 * px + 2] = int(SIGIL_EDGE[2] + (lit[2] - SIGIL_EDGE[2]) * k)
            buf[4 * px + 3] = 255 * edge // cells
        rows.append(bytes(buf))
    return rows


def sigil_pixels(slug, hexcol=None):
    """RGBA bytes for one party's FLAG: field, emblem, and CA's frame over both.

    A PARTY FLIES A FLAG LIKE A FACTION DOES. The court list draws a real
    faction's mon_64 beside these - a bare glyph next to a framed banner reads
    as a missing picture, not as a different kind of thing.
    """
    hexcol = hexcol or HOUSE_COLOUR[slug]
    r = int(hexcol[1:3], 16)
    g = int(hexcol[3:5], 16)
    b = int(hexcol[5:7], 16)
    frame, field, (bx, by, bs) = flag_frame()[0]
    glyph = glyph_pixels(slug, bs)
    rows = []
    for y in range(SIGIL):
        # THE FIELD IS LIT FROM ABOVE, like the house plate behind a portrait -
        # a flat rectangle of colour reads as a placeholder.
        k = 0.55 + 0.45 * (1.0 - y / float(SIGIL - 1)) ** 1.2
        buf = bytearray(SIGIL * 4)
        fr, fl = frame[y], field[y]
        gy = y - by
        for x in range(SIGIL):
            a = fl[x]
            if a:
                buf[4 * x + 0] = int(r * k)
                buf[4 * x + 1] = int(g * k)
                buf[4 * x + 2] = int(b * k)
                buf[4 * x + 3] = a
        if 0 <= gy < bs:
            grow = glyph[gy]
            for gx in range(bs):
                ga = grow[4 * gx + 3]
                if not ga:
                    continue
                x = bx + gx
                base = buf[4 * x + 3]
                # OVER, not INSTEAD OF: the emblem is antialiased, so its edge
                # pixels have to blend into the field rather than punch through
                # it to whatever is behind the flag.
                out = ga + base * (255 - ga) // 255
                for i in range(3):
                    buf[4 * x + i] = (grow[4 * gx + i] * ga
                                      + buf[4 * x + i] * base * (255 - ga) // 255) // max(1, out)
                buf[4 * x + 3] = out
        for x in range(SIGIL):
            fa = fr[4 * x + 3]
            if fa >= FLAG_CLEAR and fl[x] == 0:
                buf[4 * x + 0] = fr[4 * x + 0]
                buf[4 * x + 1] = fr[4 * x + 1]
                buf[4 * x + 2] = fr[4 * x + 2]
                buf[4 * x + 3] = fa
        rows.append(bytes(buf))
    return rows


# THE MAN WHO IS NOT THERE. Proportions as fractions of the plate rather than
# pixels, so the figure keeps its shape if the porthole size ever moves.
SIL_PATH = PLATE_DIR + "/portrait_silhouette.png"
# A DARK FILL WITH A LIGHT RIM, and it needs both.
#
# THE FILL ALONE WAS ENOUGH while the figure only ever sat on house_plate_none -
# an opaque brown box built to go behind it. A vacant seat's plate is transparent
# now, so it lands on whatever is under the cell: the office card's own art,
# measured at (11, 11, 10) in the rendered preview against an ink of (18, 14, 11).
# Seven levels. The offices tab drew fourteen cards and half of them were empty.
#
# A FLAT LIGHTER INK CANNOT FIX IT. The silhouette still draws on a HOUSE PLATE
# in two places - the Crown's block and a party card whose leader is dead - and
# those run luminance 88 to 138 at the top, so any grey chosen to stand off a
# near-black card lands inside that range and vanishes on half the houses.
#
# SO THE FIGURE CARRIES ITS OWN EDGE. The dark fill reads on a lit plate, the
# light rim reads on a dark one, and check 21c asks only that ONE of the two
# clears each ground - which is what an outlined shape actually promises.
SIL_INK = (18, 14, 11)
SIL_RIM = (150, 138, 122)
SIL_RIM_PX = 2
SIL_ALPHA = 210
# THE SMALLEST LUMINANCE STEP THAT READS. The figure is a shape and not text, so
# this is not a 4.5:1 contrast bar - it is the distance at which an edge is an
# edge. 24 is what the 2026-09-17 preview pass showed; below it the head stops
# separating from the bottom of a house plate, which fades to PLATE_BASE.
SIL_MIN_STEP = 24
# Head: centre and radius. Shoulders: an ellipse whose centre is BELOW the
# picture, so only its top cap is drawn and it leaves the frame at full width.
SIL_HEAD_CY, SIL_HEAD_R = 0.37, 0.22
SIL_NECK_HW, SIL_NECK_TOP = 0.05, 0.50
# RX IS A FRACTION OF THE WIDTH and the shoulders have to leave the frame, not
# float in the middle of it: at 0.27 they reached half the picture and read as a
# small figure standing far back rather than as a portrait.
SIL_SHOULDER_CY, SIL_SHOULDER_RX, SIL_SHOULDER_RY = 1.14, 0.42, 0.62


def silhouette_pixels():
    """RGBA rows for the head-and-shoulders figure. No PIL, like everything else here."""
    hcy = SIL_HEAD_CY * PLATE_H
    hr = SIL_HEAD_R * PLATE_H * (PLATE_H / float(PLATE_W)) ** 0
    hrx = SIL_HEAD_R * PLATE_H          # a head is round in PIXELS, not in
    hry = SIL_HEAD_R * PLATE_H          # fractions of a non-square picture
    cx = (PLATE_W - 1) / 2.0
    scy = SIL_SHOULDER_CY * PLATE_H
    srx = SIL_SHOULDER_RX * PLATE_W
    sry = SIL_SHOULDER_RY * PLATE_H
    nhw = SIL_NECK_HW * PLATE_W
    ntop = SIL_NECK_TOP * PLATE_H

    def inside(px, py):
        if ((px - cx) / hrx) ** 2 + ((py - hcy) / hry) ** 2 <= 1.0:
            return True
        if py >= ntop and abs(px - cx) <= nhw and py <= scy:
            return True
        if py >= hcy and ((px - cx) / srx) ** 2 + ((py - scy) / sry) ** 2 <= 1.0:
            return True
        return False

    # COVERAGE FIRST, THEN INK. The rim is "a covered pixel with an uncovered
    # one near it", which cannot be answered while the rows are being written -
    # it needs the pixels below this one, and they do not exist yet.
    #
    # OFF THE EDGE OF THE PICTURE COUNTS AS COVERED. The shoulders are an
    # ellipse centred below the frame and they leave it at full width; treating
    # the border as empty would draw a rim along the bottom of the cell, which
    # is a line under the figure and not an outline of it.
    # SUPERSAMPLED 3x3. A hard edge on a circle at this size reads as a cog,
    # and there is no blur to hide it behind - the cell is drawn at 98x54 and
    # the engine's downscale is not kind to a stair-stepped outline.
    cover = []
    for y in range(PLATE_H):
        line = []
        for x in range(PLATE_W):
            hits = 0
            for sy in range(3):
                for sx in range(3):
                    if inside(x + (sx + 0.5) / 3.0, y + (sy + 0.5) / 3.0):
                        hits += 1
            line.append(hits)
        cover.append(line)

    def covered(x, y):
        # OFF THE PICTURE IS COVERED. The shoulders leave the frame at full
        # width, so a border treated as empty draws a rim along the bottom of
        # the cell - a line under the figure rather than an outline of it.
        if x < 0 or y < 0 or x >= PLATE_W or y >= PLATE_H:
            return True
        return cover[y][x] > 0

    rows = []
    for y in range(PLATE_H):
        buf = bytearray(PLATE_W * 4)
        for x in range(PLATE_W):
            hits = cover[y][x]
            if not hits:
                continue
            rim = False
            for dy in range(-SIL_RIM_PX, SIL_RIM_PX + 1):
                for dx in range(-SIL_RIM_PX, SIL_RIM_PX + 1):
                    if not covered(x + dx, y + dy):
                        rim = True
                        break
                if rim:
                    break
            ink = SIL_RIM if rim else SIL_INK
            a = SIL_ALPHA * hits // 9
            buf[4 * x + 0] = ink[0]
            buf[4 * x + 1] = ink[1]
            buf[4 * x + 2] = ink[2]
            buf[4 * x + 3] = a
        rows.append(bytes(buf))
    return rows


ZIG_PATH = PLATE_DIR + "/offices_ziggurat.png"
ZIG_FILL = (16, 10, 7, 170)             # dark, and the backdrop shows through it
ZIG_RIM = (150, 96, 50, 230)            # bronze, the cards' own frame
ZIG_RIM_PX = 3
# THE SHRINE: (half-width as a fraction of the top tier's, height as a fraction
# of the room between the top tier and the box's top).
ZIG_SHRINE = ((0.33, 0.55), (0.15, 1.0))


def ziggurat_boxes():
    """The tower as (x0, y0, x1, y1) in panel pixels: a tier per card row, then the shrine."""
    out = []
    for ry in sorted(set(y for _x, y in CARD_GRID)):
        xs = [x for x, y in CARD_GRID if y == ry]
        out.append((max(0, min(xs) - ZIG_PAD_X), ry - ZIG_PAD_Y,
                    min(PANEL_W, max(xs) + CARD_W + ZIG_PAD_X), ry + CARD_H + ZIG_PAD_Y))
    top, room = out[0], out[0][1] - PANEL_LAYOUT["ic_zig_bg"][1]
    mid = (top[0] + top[2]) // 2
    for fw, fh in ZIG_SHRINE:
        half = int((top[2] - top[0]) * fw)
        out.append((mid - half, top[1] - int(room * fh), mid + half, top[1]))
    return out


# THE ZIGGURAT'S TITLE (author, 2026-10-03: "a title on top of the ziggurat on
# the office panel"), on the shrine: the cell is the shrine's lower step, the
# heading plate hugs its words inside it (FIT_PLATES), lifted 4px off the top.
def off_title_box():
    zb = ziggurat_boxes()
    return (zb[-2][0], zb[-1][1] + 4, zb[-2][2] - zb[-2][0], HEADING_H)


PANEL_LAYOUT["ic_off_title"] = off_title_box()


def ziggurat_pixels():
    """RGBA rows for the box: the tower filled dark, its outline in bronze.

    Each row is a bitmask, so the rim is a 3px erosion done with shifts and
    ANDs rather than a per-pixel walk over 1.6 million pixels.
    """
    import itertools
    x0, y0, w, h = PANEL_LAYOUT["ic_zig_bg"]
    full = (1 << w) - 1
    masks = [0] * h
    for a, b, c, d in ziggurat_boxes():
        a, c = max(0, a - x0), min(w, c - x0)
        span = ((1 << (c - a)) - 1) << (w - c)      # bit w-1-x is pixel x
        for y in range(max(0, b - y0), min(h, d - y0)):
            masks[y] |= span
    clear, fill, rim = bytes(4), bytes(ZIG_FILL), bytes(ZIG_RIM)
    rows = []
    for y, m in enumerate(masks):
        core = m
        for dy in range(1, ZIG_RIM_PX + 1):
            core &= (masks[y - dy] if y >= dy else 0) & (masks[y + dy] if y + dy < h else 0)
        for _ in range(ZIG_RIM_PX):
            core &= (core << 1) & (core >> 1) & full
        runs = itertools.groupby(zip(format(m, "0%db" % w), format(m & ~core, "0%db" % w)))
        rows.append(b"".join((rim if r == "1" else fill if i == "1" else clear) * len(list(g))
                             for (i, r), g in runs))
    return rows


def check_ziggurat(rows=None, layout=None):
    """The tower sits between the section line and the fill button, and every
    card stands on it: the pixel just past each card corner is part of it."""
    lay = layout or PANEL_LAYOUT
    rows = ziggurat_pixels() if rows is None else rows
    out = []
    x0, y0, w, h = lay["ic_zig_bg"]
    if (len(rows[0]) // 4, len(rows)) != (w, h):
        out.append("ic_zig_bg: the art is %dx%d in a %dx%d box, so it stretches"
                   % (len(rows[0]) // 4, len(rows), w, h))
    sec, fill = lay["ic_lbl_section"], lay["ic_fill"]
    if y0 < sec[1] + sec[3]:
        out.append("ic_zig_bg starts at %d, over the section line ending at %d" % (y0, sec[1] + sec[3]))
    if y0 + h > fill[1]:
        out.append("ic_zig_bg ends at %d, under the fill button at %d" % (y0 + h, fill[1]))
    for cx, cy in CARD_GRID:
        for px, py in ((cx - 1, cy - 1), (cx + CARD_W, cy - 1),
                       (cx - 1, cy + CARD_H), (cx + CARD_W, cy + CARD_H)):
            u, v = px - x0, py - y0
            if not (0 <= v < len(rows) and 0 <= u < len(rows[v]) // 4) or rows[v][4 * u + 3] == 0:
                out.append("the card at (%d, %d) hangs off the ziggurat at (%d, %d)" % (cx, cy, px, py))
    if rows[0][3] or rows[0][-1]:
        out.append("ic_zig_bg's top corners are filled: a block, not a ziggurat")
    return out


def plate_pixels(hexcol):
    """RGBA bytes for one plate. Pure function of the colour - no PIL needed."""
    r = int(hexcol[1:3], 16)
    g = int(hexcol[3:5], 16)
    b = int(hexcol[5:7], 16)
    cx = (PLATE_W - 1) / 2.0
    rows = []
    for y in range(PLATE_H):
        t = y / float(PLATE_H - 1)
        top = 0.12 + 0.52 * ((1.0 - t) ** 1.3)
        row = bytearray()
        for x in range(PLATE_W):
            d = abs(x - cx) / cx
            k = top * (1.0 - 0.25 * (d ** 2.0))
            row += bytes(bytearray((
                int(PLATE_BASE[0] + (r - PLATE_BASE[0]) * k),
                int(PLATE_BASE[1] + (g - PLATE_BASE[1]) * k),
                int(PLATE_BASE[2] + (b - PLATE_BASE[2]) * k),
                255)))
        rows.append(bytes(row))
    return rows


# THE HOUSE COLOUR ON THE PORTRAIT ITSELF, done the way CA does it.
#
# CA DOES NOT TINT THE ART. Beside every generic porthole they ship a second png -
# <porthole>_mask1.png, same pixel size, ~82% fully transparent - whose opaque
# region is the heraldry cloth: the hat band and the beard cover. That cloth is
# painted neutral light grey in the base art on purpose, so a colour reads true
# on it. Measured 2026-09-12: the mask has exactly ONE distinct opaque colour,
# pure white, which is what makes a multiply give the colour back unchanged.
#
# The colour arrives through a ContextColourSetter declared on the cell (see
# colour_from in gen_iron_court_emitter.py) and a cco handed to it at runtime.
# That is the ONLY mechanism by which a colour can vary per row: there is no
# colour or tint setter on a uicomponent anywhere in CA's reference.
#
# WHICH CHARACTERS HAVE ONE: 627 of CA's 1,524 portholes, and pointedly NOT the
# legendary lords - Astragoth, Drazhoath, Gorduz and Zhatan have none, and
# neither do this mod's own portraits. Those cells fall back to MASK_NONE and
# carry no cloth colour, which is the only safe outcome: a missing imagepath
# draws a BLANK WHITE SQUARE over the face, silently, so a path is named only
# when this generator has seen the file in an installed pack.
MASK_DIR = PLATE_DIR
MASK_NONE = "%s/mask_none.png" % MASK_DIR

# THE SEAT'S RIM (spec 2026-09-28 section 4.1). CA's completed-district glow off
# the Tower of Zharr, 9-sliced at 40 - the Great Guilds' measured value, and it
# fits MASK_NONE (300x164) as well as the rim (299x877), so no layer can sample
# outside its texture whichever of the two it holds.
#
# ONE LAYER PER LOOK, each shipping MASK_NONE. ICUI.set_rim writes the rim into
# the look's layer and MASK_NONE into the others. A layer's colour multiplies
# its image, so the dim and red looks are the same CA art under another colour
# rather than derived files (ruling 1 of the 2026-09-28 plan).
# OUR OWN TEXTURE, NOT CA'S FILE (author, 2026-09-28, of CA's rim in game: "the
# corners are not filled"). CA's district_complete_glow_02.png is a ROUNDED
# rectangle - its glow peaks 10px in along an edge and 20px in along the
# diagonal, a corner radius near 30px - so no margin can take it into a square
# card's corner, and pushing the layer out past the card to hide the curve
# spills ~25px of glow into the 20px gaps between cards. seat_rim_pixels()
# draws CA's own measured colour and edge profile with SQUARE corners instead.
RIM_ART = "%s/seat_rim.png" % PLATE_DIR
RIM_MARGIN = 40
RIM_PX = 128
# Measured off CA's rim at x=150, every 2px in from the edge: its colour holds
# near (176, 5, 5) and only the alpha changes.
RIM_RGB = (176, 5, 5)
# A FAILED PLOT'S RIM, in ash (leftover M5 of the 2026-09-28 review). The fail
# look used to be RIM_ART under a red colour, and a layer colour multiplies:
# over a picture that is already pure red it can only draw a darker red, so a
# failure looked like a success bar the flicker. Same edge profile, own colour.
RIM_FAIL_ART = "%s/seat_rim_fail.png" % PLATE_DIR
RIM_FAIL_RGB = (200, 196, 188)
RIM_ALPHA = [2, 8, 21, 37, 50, 55, 53, 48, 42, 37, 32, 28, 24, 21, 18, 16, 14,
             13, 12, 11]
RIM_LOOKS = {
    # CA's ToZ furnace glow_01 values.
    "lit": {"shader": "glow_pulse_t0", "shader_vars": "1.00,1.30,0.80,0.00"},
    "dim": {"colour": "#FFFFFF66"},
    # A fast flicker: a failure is short and sharp, not a slow breath. Drawn
    # over RIM_FAIL_ART, so no tint.
    "fail": {"colour": "#FFFFFFFF", "shader": "glow_pulse_t0",
             "shader_vars": "0.60,1.60,0.25,0.00"},
}


def rim_layers(looks, margin=RIM_MARGIN):
    out = []
    for look in looks:
        lay = {"path": MASK_NONE, "offset": (0, 0), "dw": 0, "dh": 0,
               "margin": margin, "dock": None}
        lay.update(RIM_LOOKS[look])
        out.append(lay)
    return out


OFFICE_CARD_LAYERS = CARD_LAYERS + rim_layers(["lit", "dim"])
# Which layer holds each look, per component kind. Must match ICUI.RIMS;
# check_rim_slots() holds the two together.
CARD_RIM = {"lit": len(CARD_LAYERS), "dim": len(CARD_LAYERS) + 1}
# The tab marker: CA's Hell-Forge heat glow, breathing at the Hell-Forge
# category block's own values.
MARK_LAYERS = [{"path": "ui/skins/default/dlc23_chd_hell_forge/heat_glow.png",
                "offset": (0, 0), "dw": 0, "dh": 0, "margin": 0, "dock": None,
                "colour": "#FFFFFFD0", "shader": "glow_pulse_t0",
                "shader_vars": "0.80,1.50,0.80,0.00"}]
# Only portraits under this prefix can turn up in a Chaos Dwarf court.
MASK_PREFIX = "chd_"
MASK_SUFFIX = "_mask1.png"


def seat_rim_alpha(d, margin=RIM_MARGIN):
    """CA's edge profile at distance d from the nearest edge, gone by RIM_MARGIN.

    Faded to nothing at the margin, where CA's own tail is still at 10: past
    the margin is the 9-slice's stretched centre, and anything left there is a
    red wash across the whole card."""
    i = d // 2
    a = RIM_ALPHA[i] if i < len(RIM_ALPHA) else 0
    if d >= margin:
        return 0
    fade = margin - 10
    if d > fade:
        a = a * (margin - d) // 10
    return a


def seat_rim_pixels(margin=RIM_MARGIN, px=RIM_PX, rgb=RIM_RGB):
    """The distance is to the NEAREST edge, so a corner pixel takes the brighter
    of its two edges: the glow meets itself in a square corner."""
    rows = []
    for y in range(px):
        row = bytearray()
        for x in range(px):
            d = min(x, y, px - 1 - x, px - 1 - y)
            row += bytearray((rgb[0], rgb[1], rgb[2],
                              seat_rim_alpha(d, margin)))
        rows.append(bytes(row))
    return rows


def frame_pixels(px=None, band=None):
    """Square corners: a pixel takes the band of its NEAREST edge."""
    px, band = px or FRAME_PX, band or FRAME_BAND
    rows = []
    for y in range(px):
        row = bytearray()
        for x in range(px):
            d = min(x, y, px - 1 - x, px - 1 - y)
            row += bytearray(band[d] if d < len(band) else (0, 0, 0, 0))
        rows.append(bytes(row))
    return rows


def check_portrait_frame(rows=None, layer=None):
    """Opaque from its first pixel, FRAME_BRONZE px of bronze, a clear middle,
    and drawn FRAME_OUT px past the cell - the two faults the author saw."""
    rows = rows or frame_pixels()
    layer = layer or FACE_LAYERS[FRAME_INDEX]
    out = []
    mid = 4 * (len(rows[0]) // 8)
    col = [rows[y][4 * (len(rows[0]) // 8):4 * (len(rows[0]) // 8) + 4]
           for y in range(len(rows))]
    if any(rows[0][i + 3] < 255 for i in range(0, len(rows[0]), 4)) or col[0][3] < 255:
        out.append("portrait frame: its outer edge is not opaque - the portrait "
                   "shows round it")
    bronze = 0
    for px in col[1:]:
        if px[3] == 255 and px[0] >= 90:
            bronze += 1
        else:
            break
    if bronze < FRAME_BRONZE:
        out.append("portrait frame: %dpx of bronze, not %d" % (bronze, FRAME_BRONZE))
    if rows[len(rows) // 2][mid + 3]:
        out.append("portrait frame: its middle is not clear - it covers the face")
    if (tuple(layer["offset"]) != (-FRAME_OUT, -FRAME_OUT)
            or layer["dw"] != 2 * FRAME_OUT or layer["dh"] != 2 * FRAME_OUT):
        out.append("portrait frame: the layer is not pushed %dpx past the cell, so "
                   "the portrait's edge is beside the frame and not under it"
                   % FRAME_OUT)
    return out


def check_seat_rim(rows=None, margin=RIM_MARGIN, px=RIM_PX):
    """The rim's corner must be as bright as its edge, and its centre empty."""
    rows = rows or seat_rim_pixels(margin, px)
    out = []
    if len(rows) < 2 * margin or len(rows[0]) // 4 < 2 * margin:
        out.append("seat rim: %dpx cannot hold a %d margin on both sides"
                   % (len(rows), margin))
        return out
    peak = max(range(margin), key=lambda d: seat_rim_alpha(d, margin))
    edge = rows[peak][4 * (px // 2) + 3]
    corner = rows[peak][4 * peak + 3]
    if corner < edge:
        out.append("seat rim: the corner's glow is %d where the edge's is %d - "
                   "the corners are not filled" % (corner, edge))
    centre = rows[px // 2][4 * (px // 2) + 3]
    if centre:
        out.append("seat rim: the centre is %d, a wash over the whole card" % centre)
    return out


def mask_pixels():
    """Fully transparent. Not "no call at all": rows are recycled, so a cell has
    to have the last man's mask actively taken off it."""
    return [bytes(bytearray((0, 0, 0, 0))) * PLATE_W] * PLATE_H


_DISC_ALPHA = []
_WEDGE_MASKS = {}
_WEDGE_SPANS = {}


def _disc_alpha():
    """Alpha for every pixel of the pie box: 255 inside, a ramp on the rim.

    THE RIM IS THE ONLY CURVE, so it is the only thing worth sampling. Nine
    samples on the pixels the rim actually crosses and a flat 255 everywhere
    else - supersampling all eighty thousand would be sixty times the work for
    an answer that is 255.

    NO PIL, deliberately - the same reason the plates are hand-rasterised. This
    file's --check has to give the same answer on a machine without Pillow, or
    the art it refuses to rebuild is art nobody can rebuild.
    """
    if _DISC_ALPHA:
        return _DISC_ALPHA
    r = DIAL_R
    inner, outer = (r - 1.5) ** 2, (r + 1.5) ** 2
    for py in range(r):
        row = bytearray(2 * r)
        dy = r - (py + 0.5)
        for px in range(2 * r):
            dx = (px + 0.5) - r
            d2 = dx * dx + dy * dy
            if d2 <= inner:
                row[px] = 255
            elif d2 <= outer:
                hits = 0
                for sy in range(3):
                    yy = r - (py + (sy + 0.5) / 3.0)
                    for sx in range(3):
                        xx = (px + (sx + 0.5) / 3.0) - r
                        if xx * xx + yy * yy <= r * r and yy >= 0:
                            hits += 1
                row[px] = 255 * hits // 9
        _DISC_ALPHA.append(bytes(row))
    return _DISC_ALPHA


def _wedge_edge(a, dy):
    """Where the straight edge at angle a crosses a row dy above the baseline.

    THE TWO ENDS HAVE NO COTANGENT - the baseline itself is the edge - so they
    are answered as the far side of the box rather than as an infinity, and
    everything is clamped to the box either way.
    """
    sin = math.sin(a)
    if abs(sin) <= 1e-9:
        x = -2.0 * DIAL_R if math.cos(a) < 0 else 2.0 * DIAL_R
    else:
        x = dy * math.cos(a) / sin
    return max(0, min(2 * DIAL_R, int(math.floor(DIAL_R + x + 0.5))))


def wedge_spans(i):
    """[x0, x1) per row: the columns slice i owns, and nothing else does.

    The mask is cut with these and so is the colour - a wedge is a narrow
    thing in a wide box, and three bytes of party colour in every transparent
    pixel is six times the file for a picture of nothing.
    """
    if i in _WEDGE_SPANS:
        return _WEDGE_SPANS[i]
    a0 = math.pi * (1 - i / float(DIAL_SLICES))
    a1 = math.pi * (1 - (i + 1) / float(DIAL_SLICES))
    out = []
    for py in range(DIAL_R):
        dy = DIAL_R - (py + 0.5)
        out.append((_wedge_edge(a0, dy), _wedge_edge(a1, dy)))
    _WEDGE_SPANS[i] = out
    return out


def wedge_mask(i):
    """Alpha rows for slice i: the disc, with everything outside the slice cut.

    A PARTITION, not an overlap. Slice i ends where slice i+1 begins, on the
    same rounded pixel, so two neighbours never draw the same pixel - which is
    what would leave a faint line of background down every boundary, sixty of
    them, when two antialiased edges are alpha-blended over each other.
    """
    if i in _WEDGE_MASKS:
        return _WEDGE_MASKS[i]
    alpha = _disc_alpha()
    rows = []
    for py, (x0, x1) in enumerate(wedge_spans(i)):
        row = bytearray(2 * DIAL_R)
        if x1 > x0:
            row[x0:x1] = alpha[py][x0:x1]
        rows.append(bytes(row))
    _WEDGE_MASKS[i] = rows
    return rows


def wedge_pixels(i, hexcol):
    """The mask in a party's colour. The shape is shared; only the RGB moves."""
    r = int(hexcol[1:3], 16)
    g = int(hexcol[3:5], 16)
    b = int(hexcol[5:7], 16)
    w = 2 * DIAL_R
    # PER ROW, BY SLICE ASSIGNMENT, and the colour only inside the slice's own
    # columns. Building this a pixel at a time is a second of Python per
    # colour; painting the colour across the whole row is six times the file.
    mask = wedge_mask(i)
    rows = []
    for py, (x0, x1) in enumerate(wedge_spans(i)):
        buf = bytearray(w * 4)
        n = x1 - x0
        if n > 0:
            buf[4 * x0 + 0:4 * x1:4] = bytes(bytearray([r] * n))
            buf[4 * x0 + 1:4 * x1:4] = bytes(bytearray([g] * n))
            buf[4 * x0 + 2:4 * x1:4] = bytes(bytearray([b] * n))
        buf[3::4] = mask[py]
        rows.append(bytes(buf))
    return rows


# THE DIAL'S BORDER, measured off CA's own frame rather than picked.
#
# ui/skins/default/panel_back_border.png is the texture every panel in this mod
# already wears, and its rail is the same six pixels on all four sides: one of
# soft edge at alpha 25, THREE of bronze, then alpha 172 and 54 of inner shadow.
# The bronze is lit from ABOVE - the top rail's outer pixel is (181,152,107) and
# the bottom rail's is (76,44,19) - which is why this interpolates by the
# normal's up-component instead of painting one flat colour round the arc.
#
# FIVE PIXELS OF BRONZE, not CA's three. The rail is three because it frames a
# panel edge at 1:1; the same three round a 210px radius is a hairline. The ramp
# is resampled rather than padded, so the bevel is CA's shape at a new width.
RIM_TOP = ((181, 152, 107), (122, 83, 55), (115, 70, 41))
RIM_SIDE = ((109, 75, 49), (95, 61, 35), (97, 64, 38))
RIM_BOTTOM = ((76, 44, 19), (90, 55, 28), (119, 73, 43))
RIM_EDGE_A = 25                 # the soft pixel outside the bronze
RIM_SHADOW = (172, 54)          # the two inside it, black at these alphas
RIM_W = 5                       # bronze pixels
RIM_SS = 3                      # samples per axis - the whole picture is edge
# THE EDGE RUNS HOT. An ember glow immediately inside the rim's shadow, dying
# inward - the court sits over a furnace and the dial is the one thing on the
# panel big enough to catch the light.
#
# TEN PIXELS, NOT TWENTY. The glow is drawn over the party colours, so its depth
# is paid for in their legibility: at 20px the outer band of every wedge reads
# as orange and the smallest parties lose their colour entirely. At 10 it reads
# as heat on the metal and the shares are untouched.
#
# UNDER THE BRONZE, not over it: the rim's own branches are tested first below,
# so the fire licks out from beneath a frame that stays crisp.
EMBER = ((255, 236, 196), (255, 146, 40), (168, 38, 6))
# AS DEEP AS THE RIM PICTURE HAS ROOM FOR - see RIM_PAD, which is itself the
# gap between the pie and the label above it. Deriving it means the fire cannot
# be drawn deeper than the picture that holds it, which would clip it flat at
# the edge with nothing to say so.
EMBER_DEPTH = RIM_PAD
EMBER_PEAK = 0.85
# 1.8, not 2.6. The steep falloff was chosen when the glow lay over the party
# colours, where anything gentler washed them out; over the panel it puts the
# whole glow in the first three pixels and draws a bright line round the rim
# instead of a heat haze coming off it.
EMBER_FALLOFF = 1.8


# THE WALL BETWEEN TWO PARTIES. Thinner than the rail - there can be eighteen
# of these and one rail - but the same metal, lit by the same rule, so the pie
# reads as one frame with spokes rather than as a rail with lines drawn on it.
# 4, NOT 3, AND THE DARK EDGE CARRIES IT. The bronze core tops out at
# (169,138,96), which is most of the way to the gold party's own fill - so at
# three pixels with a 60-alpha edge the wall read on the red boundary and
# vanished on the gold one. What reads on ANY colour is the dark line either
# side of the metal, and four with a firm edge matches the rim's own weight;
# five was heavier than the frame, which makes the divisions louder than the
# thing they divide.
DIV_W = 4                       # bronze pixels across
DIV_EDGE_A = 150                 # the dark edge either side, out of 255
DIV_SS = 3                      # samples per axis, as the rim


def div_pixels(i):
    """RGBA rows for one radial wall, at the angle slice i begins on.

    THE PIE'S OWN BOX, not the rim's: this is drawn among the wedges and has to
    line up with them to the pixel. It runs the full radius and the rail is
    declared after it, so the tip tucks under the frame instead of crossing it.
    """
    r = DIAL_R
    w, h = 2 * r, r
    a = math.pi * (1 - i / float(DIAL_SLICES))
    sin_a, cos_a = math.sin(a), math.cos(a)
    half = DIV_W / 2.0
    # THE WINDOW THE LINE CAN BE IN, per row. Scanning the whole box is a
    # hundred and twenty million samples across the set for a three-pixel line.
    # A row's crossing is at r + dy*cot(a); the bar is (half + 1) wide across
    # its own axis, which is that over |sin a| wide across the row, and the
    # crossing itself moves |cot a| per row. Everything is padded by two and
    # clamped, so a window that is wrong is wrong by being too big.
    if abs(sin_a) < 1e-9:
        # A wall lying along the baseline. Slice 0 and slice DIAL_SLICES are
        # the two ends of it and neither is ever generated, so this is only
        # here so a caller that asks cannot get a divide by zero instead of an
        # answer.
        return [bytes(w * 4) for _ in range(h)]
    cot = cos_a / sin_a
    pad = (half + 1.0) / abs(sin_a) + abs(cot) + 2.0
    rows = []
    for py in range(h):
        buf = bytearray(w * 4)
        centre = r + (r - (py + 0.5)) * cot
        lo = max(0, int(centre - pad))
        hi = min(w, int(centre + pad) + 1)
        for px in range(lo, hi):
            acc_r = acc_g = acc_b = acc_a = 0.0
            for sy in range(DIV_SS):
                yy = py + (sy + 0.5) / DIV_SS
                dy = r - yy
                for sx in range(DIV_SS):
                    xx = px + (sx + 0.5) / DIV_SS
                    dx = xx - r
                    if dy < 0:
                        continue
                    # ALONG the ray and ACROSS it. A point behind the centre or
                    # past the arc is not on the wall however near the line it
                    # is - an infinite line would draw a spoke out of the other
                    # side of the pie.
                    along = dx * cos_a + dy * sin_a
                    if along < 0.0 or along > r:
                        continue
                    off = abs(dx * sin_a - dy * cos_a)
                    if off < half:
                        # ONE METAL FOR EVERY WALL. Lighting each by its own
                        # angle is the rim's rule, and the rim earns it: every
                        # point of an arc faces somewhere different. A spoke
                        # does not, and by-angle lighting made the upright wall
                        # gold and the diagonals nearly black - three different
                        # things where the eye wants one frame. The band still
                        # runs across the bar, so it keeps its roundness.
                        c = rim_colour(1.0, int(off * len(RIM_TOP) / half))
                        col = (c[0], c[1], c[2], 1.0)
                    elif off < half + 1.0:
                        col = (0.0, 0.0, 0.0, DIV_EDGE_A / 255.0)
                    else:
                        continue
                    acc_r += col[0] * col[3]
                    acc_g += col[1] * col[3]
                    acc_b += col[2] * col[3]
                    acc_a += col[3]
            if acc_a > 0:
                buf[4 * px + 0] = int(acc_r / acc_a)
                buf[4 * px + 1] = int(acc_g / acc_a)
                buf[4 * px + 2] = int(acc_b / acc_a)
                buf[4 * px + 3] = int(255 * acc_a / (DIV_SS * DIV_SS))
        rows.append(bytes(buf))
    return rows


def rim_path():
    return "%s/dial_rim.png" % PLATE_DIR


def _lerp3(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t,
            a[2] + (b[2] - a[2]) * t)


def _rim_ramp(rail, band):
    """CA measured three pixels; a wider rim resamples that ramp, not pads it."""
    t = (band + 0.5) / RIM_W * (len(rail) - 1)
    i = min(len(rail) - 2, int(t))
    return _lerp3(rail[i], rail[i + 1], t - i)


def ember_colour(t):
    """t is 0 at the rim and 1 at the inner end of the glow."""
    if t < 0.35:
        return _lerp3(EMBER[0], EMBER[1], t / 0.35)
    return _lerp3(EMBER[1], EMBER[2], (t - 0.35) / 0.65)


def rim_colour(k, band):
    """band 0 outermost; k is the outward normal's up-component, 1 top, -1 down."""
    side = _rim_ramp(RIM_SIDE, band)
    if k >= 0:
        return _lerp3(side, _rim_ramp(RIM_TOP, band), k)
    return _lerp3(side, _rim_ramp(RIM_BOTTOM, band), -k)


def rim_pixels():
    """RGBA rows for the rim box: the arc, the flat baseline, and the fire.

    The BASELINE IS AN EDGE TOO. A half disc has two of them, and a rim that
    stops at the arc leaves the pie sitting on nothing - which is what the
    panel drew before, and what the border was asked for.

    RIM_PAD BIGGER THAN THE PIE, on all four sides. The fire burns outward and
    a half disc has a flat side, so "outward" includes straight down - the
    court's header strip was moved out of the way by bringing the baseline up
    to it rather than by leaving the flat side unlit.
    """
    r = DIAL_R
    # RIM_BOX's OWN SIZE, not a second copy of the arithmetic. The ember below
    # the baseline was written before this line was, and the picture stayed one
    # pad tall instead of two - so the fire under the flat side was drawn off
    # the bottom edge of its own canvas, which clips silently. Reading the box
    # the layout declares means the picture and the component that shows it
    # cannot disagree about how big it is.
    w, h = RIM_BOX[2], RIM_BOX[3]
    assert (w, h) == (2 * r + 2 * RIM_PAD, r + 2 * RIM_PAD), (w, h)
    rows = []
    for py in range(h):
        buf = bytearray(w * 4)
        for px in range(w):
            acc_r = acc_g = acc_b = acc_a = 0.0
            for sy in range(RIM_SS):
                yy = py + (sy + 0.5) / RIM_SS
                dy = (r + RIM_PAD) - yy            # up is positive, 0 at the base
                for sx in range(RIM_SS):
                    xx = px + (sx + 0.5) / RIM_SS
                    dx = xx - (r + RIM_PAD)
                    d = math.sqrt(dx * dx + dy * dy)
                    # HOW FAR OUTSIDE THE HALF DISC, which is not the same as
                    # how far from the centre. Above the baseline the shape is
                    # the arc and the answer is d - r; below it the nearest
                    # point of the shape is straight up on the flat side, or
                    # the corner where the two edges meet if we are already
                    # past the end of it. Negative means inside.
                    if dy >= 0:
                        outside = d - r
                    elif abs(dx) <= r:
                        outside = -dy
                    else:
                        outside = math.sqrt((abs(dx) - r) ** 2 + dy * dy)
                    if outside > 0:
                        # THE FIRE, burning away from the pie instead of into
                        # it. Nothing else is drawn out here, so there is no
                        # mitre to keep and no rail to respect: the only
                        # question is how far from the metal it is.
                        t = outside / float(EMBER_DEPTH)
                        if t >= 1.0:
                            continue
                        c = ember_colour(t)
                        col = (c[0], c[1], c[2],
                               EMBER_PEAK * (1.0 - t) ** EMBER_FALLOFF)
                        acc_r += col[0] * col[3]
                        acc_g += col[1] * col[3]
                        acc_b += col[2] * col[3]
                        acc_a += col[3]
                        continue
                    # WHICHEVER EDGE IS NEARER owns the pixel, so the two rails
                    # meet in a mitre at the ends instead of overpainting.
                    if dy < r - d:
                        e, k = dy, -1.0            # the flat side, lit from below
                    else:
                        e, k = r - d, (dy / d if d > 1e-9 else 1.0)
                    if e < 1.0:
                        col = (0.0, 0.0, 0.0, RIM_EDGE_A / 255.0)
                    elif e < 1.0 + RIM_W:
                        c = rim_colour(k, int(e - 1.0))
                        col = (c[0], c[1], c[2], 1.0)
                    elif e < 1.0 + RIM_W + len(RIM_SHADOW):
                        col = (0.0, 0.0, 0.0,
                               RIM_SHADOW[int(e - 1.0 - RIM_W)] / 255.0)
                    else:
                        continue
                    acc_r += col[0] * col[3]
                    acc_g += col[1] * col[3]
                    acc_b += col[2] * col[3]
                    acc_a += col[3]
            if acc_a > 0:
                buf[4 * px + 0] = int(acc_r / acc_a)
                buf[4 * px + 1] = int(acc_g / acc_a)
                buf[4 * px + 2] = int(acc_b / acc_a)
                buf[4 * px + 3] = int(255 * acc_a / (RIM_SS * RIM_SS))
        rows.append(bytes(buf))
    return rows


def wedge_colours():
    """slug -> colour, for every party that can ever hold a slice."""
    out = {None: PLATE_NONE_COLOUR}
    for p in IC.PARTIES:
        out[p[0]] = HOUSE_COLOUR[p[0]]
    for slug in CONFED_SEATS:
        out[slug] = CONFED_COLOUR[slug]
    return out


def wedge_art():
    """(path, rows) for every wedge, ONE AT A TIME.

    A dict of all of them is sixty slices by twenty-six colours by 320KB, which
    is half a gigabyte of Python bytes objects. The check and the write both
    walk this instead.
    """
    for slug, hexcol in sorted(wedge_colours().items(),
                               key=lambda kv: kv[0] or ""):
        for i in range(DIAL_SLICES):
            yield wedge_path(i, slug), wedge_pixels(i, hexcol)


def art_paths():
    """Every png this pack owns under ui/derpy_ic, without rasterising any of it.

    OWNS, not GENERATES. Three things walk this set and all three want the same
    answer: deploy_iron_court.py ships it, write_plates() prunes anything under
    the folder that is NOT in it, and check 3 proves every imagepath resolves.
    """
    out = set(build_plates())
    # THE BACKDROP IS OURS AND IS NOT GENERATED. It is cut once from the
    # reference keyframe rather than rasterised from numbers, so build_plates -
    # which returns pixel rows, and would hold two million of them for this one
    # file - is the wrong home for it. Left out of here it would be pruned by
    # the next --write and would never reach the pack at all: a blank square
    # behind the whole panel, with nothing in the log.
    out.add(PANEL_BG)
    # CA's Chaos Dwarf art, trimmed: cut from the game, not rasterised. See CHD_CUTS.
    out.update(CHD_CUTS)
    out.update(gov_art_sources())
    # The commission's ember sprite, copied: see FIRE_FILE.
    out.add(EMBER_SPRITE)
    for slug in wedge_colours():
        for i in range(DIAL_SLICES):
            out.add(wedge_path(i, slug))
    return out


# CA'S CHAOS DWARF ART, TRIMMED TO ITS OWN ALPHA BOX (2026-09-26). our path ->
# (CA's path in ui2.pack, crop box). Each box is the art's alpha > 8 bounding
# box, measured, so a trimmed picture fills its component exactly and no layer
# has to be larger than its box. The selected tab loses the glow under its bar;
# the bar itself is the whole of the picture that says "this one".
CHD_CUTS = {
    PLATE_DIR + "/chd_tab_active.png": ("ui/skins/default/tab_square_large_text_active.png", (1, 7, 354, 45)),
    PLATE_DIR + "/chd_tab_hover.png": ("ui/skins/default/tab_square_large_text_hover.png", (1, 7, 354, 45)),
    PLATE_DIR + "/chd_tab_selected.png": ("ui/skins/default/tab_square_large_text_selected.png", (1, 7, 354, 45)),
    PLATE_DIR + "/chd_tab_selected_hover.png": ("ui/skins/default/tab_square_large_text_selected_hover.png",
                                 (1, 7, 354, 45)),
    PLATE_DIR + "/chd_title.png": ("ui/skins/wh3_dlc23_chd_chaos_dwarfs/panel_title.png", (54, 3, 491, 59)),
    BORDER_TEXTURE: ("ui/skins/default/dlc23_chd_hell_forge/cap_group_name_holder.png",
                     (15, 0, 129, 51)),
    # THE THIRD VALUE SHRINKS IT to that height, aspect kept: see HEADING_H.
    HEADING_ART: ("ui/skins/default/dlc23_chd_hell_forge/side_panel_title.png",
                  (0, 0, 454, 90), HEADING_H),
}


def cut_chd_art(quiet=False):
    """Write every CHD_CUTS picture that is missing or differs. Needs the game."""
    import io as _io
    import read_pack_index as RPI
    from read_vanilla_loc import _decompress
    from PIL import Image
    pack = os.path.join(GAME_DATA, "ui2.pack")
    if not os.path.isfile(pack):
        if not quiet:
            print("  (no game install at %s - Chaos Dwarf art not cut)" % GAME_DATA)
        return []
    written = []
    for ours, (theirs, box, *height) in sorted(CHD_CUTS.items()):
        data = None
        for path, comp, blob in RPI.read(pack, theirs):
            if path == theirs:
                data = _decompress(blob) if comp else blob
        assert data and data[:4] == b"\x89PNG", "%s is not in ui2.pack" % theirs
        img = Image.open(_io.BytesIO(data)).convert("RGBA").crop(box)
        if height:
            img = img.resize((round(img.width * height[0] / img.height), height[0]),
                             Image.LANCZOS)
        disk = os.path.join(ROOT, "Modding Files", "pack", *ours.split("/"))
        buf = _io.BytesIO()
        img.save(buf, "PNG")
        if not os.path.isfile(disk) or open(disk, "rb").read() != buf.getvalue():
            os.makedirs(os.path.dirname(disk), exist_ok=True)
            open(disk, "wb").write(buf.getvalue())
            written.append(disk)
    ui = os.path.join(GAME_DATA, "ui.pack")
    for ours, theirs in sorted(gov_art_sources().items()):
        data = None
        for path, comp, blob in RPI.read(ui, theirs):
            if path == theirs:
                data = _decompress(blob) if comp else blob
        assert data and data[:4] == b"\x89PNG", "%s is not in ui.pack" % theirs
        img = upscale_art(Image.open(_io.BytesIO(data)).convert("RGBA"), GOV_ART_PX)
        disk = os.path.join(ROOT, "Modding Files", "pack", *ours.split("/"))
        buf = _io.BytesIO()
        img.save(buf, "PNG")
        if not os.path.isfile(disk) or open(disk, "rb").read() != buf.getvalue():
            open(disk, "wb").write(buf.getvalue())
            written.append(disk)
    return written


def build_plates():
    """in-pack path -> RGBA rows, for every png this generator writes.

    One dict deliberately: the drift check, the packing gate and the deploy list
    all walk it, so a new piece of art is covered by all three at once.
    """
    out = {plate_path(None): plate_pixels(PLATE_NONE_COLOUR),
           rim_path(): rim_pixels()}
    # NOT SLICE ZERO. A run beginning at the first slice begins at the left end
    # of the baseline, where the rail already is - a wall there would be a line
    # drawn along the frame. Generating it anyway would ship a picture nothing
    # can ever draw, which check 3 cannot see and nobody would ever notice.
    for _d in range(1, DIAL_SLICES):
        out[div_path(_d)] = div_pixels(_d)
    for p in IC.PARTIES:
        out[plate_path(p[0])] = plate_pixels(HOUSE_COLOUR[p[0]])
        out[sigil_path(p[0])] = sigil_pixels(p[0])
        if p[0] != IC.CROWN:
            out[absent_sigil_path(p[0])] = grey_rows(out[sigil_path(p[0])])
    # A PLATE PER ABSORBED FACTION AND NO SIGIL: its crest is that faction's
    # own flag, which ships with the faction and is resolved at runtime. The
    # plate cannot be - it is the colour behind its men's portraits and under
    # its segment on the bar, and both are picture paths.
    for slug in CONFED_SEATS:
        out[plate_path(slug)] = plate_pixels(CONFED_COLOUR[slug])
    for side, colour in LAW_PBAR_COLOUR.items():
        out[law_pbar_path(side)] = plate_pixels(colour)
    out[law_pbar_path("rim")] = frame_pixels(LAW_PBAR_RIM_PX, LAW_PBAR_RIM_BAND)
    # THE WEDGES ARE NOT HERE. There are 1560 of them at 320KB apiece and this
    # function returns a dict; wedge_art() yields them one at a time instead,
    # and art_paths() is what anything needing only the NAMES should ask.
    # THE PINS' CAPITAL AND OUTLINE RINGS (spec 2026-09-29).
    out[MAP_RING_CAPITAL] = map_ring_pixels(MAP_RING_CAPITAL_COLOUR)
    out[MAP_RING_OUTLINE] = map_ring_pixels(MAP_RING_OUTLINE_COLOUR)
    # THE GOVERNORS VIEW'S PARTY RINGS AND THE FACE'S GROUND (plan ruling 6):
    # one ring per party and per absorbed faction, painted by SetImagePath.
    for p in IC.PARTIES:
        out[gm_ring_path(p[0])] = map_ring_pixels(HOUSE_COLOUR[p[0]], GM_RING, 4)
    for slug in CONFED_SEATS:
        out[gm_ring_path(slug)] = map_ring_pixels(CONFED_COLOUR[slug], GM_RING, 4)
    # AND ITS COLOUR ACROSS THE NAME PLATE (author, 2026-09-30).
    for slug, hexcol in gm_wash_colours().items():
        out[gm_wash_path(slug)] = gm_wash_pixels(hexcol)
    out[GM_FACE_GROUND] = map_disc_pixels(GM_FACE_GROUND_COLOUR, GM_HEAD[2])
    out[MASK_NONE] = mask_pixels()
    out[RIM_ART] = seat_rim_pixels()
    out[RIM_FAIL_ART] = seat_rim_pixels(rgb=RIM_FAIL_RGB)
    out[FRAME_ART] = frame_pixels()
    out[SIL_PATH] = silhouette_pixels()
    out[ZIG_PATH] = ziggurat_pixels()
    return out


def masked_portraits(quiet=False):
    """Porthole stems that really do have a _mask1 beside them, read from the
    INSTALLED packs - never from a list typed out by hand.

    This is the whole safety story for the mask layer. The panel derives a mask
    path from a portrait path it is handed at runtime, and a derived path that
    resolves to nothing is a blank white square over a man's face with no log
    line. So the stems the panel may derive from are exactly the set verified
    here, and import_iron_court.py refuses to pack when the two disagree.
    """
    import read_pack_index as RPI
    ports, masks = set(), set()
    found = False
    for name in ("ui.pack", "ui2.pack", "ui3.pack", "ui_3.pack"):
        p = os.path.join(GAME_DATA, name)
        if not os.path.isfile(p):
            continue
        found = True
        for path in RPI.paths(p):
            if not path.startswith("ui/portraits/portholes/"):
                continue
            stem = path.rsplit("/", 1)[1]
            if not stem.startswith(MASK_PREFIX):
                continue
            if stem.endswith(MASK_SUFFIX):
                masks.add(stem[:-len(MASK_SUFFIX)])
            elif stem.endswith(".png"):
                ports.add(stem[:-4])
    if not found:
        if not quiet:
            print("  (no game install at %s - mask set not verified)" % GAME_DATA)
        return None
    return sorted(ports & masks)

# THE FACE CELLS, both sizes. Three layers, and the ORDER is the whole point:
# layers draw in list order, so 0 is behind 1 is behind 2.
#
#   0  the house plate - swapped per house by SetImagePath(path, 0)
#   1  the face        - swapped per character by SetImagePath(path, 1)
#   2  the house cloth - CA's own _mask1, swapped per character, and COLOURED by
#                        the ContextColourSetter below from whichever faction cco
#                        the panel sets on this cell
#
# The mask sits ON TOP of the face because it marks pixels OF the face.
# Underneath, it would be hidden by the very art it is there to colour.
#
# Every layer's own colour attribute is #FFFFFFFF - WHITE MEANS NO MODULATION. A
# layer colour multiplies, so a dark one here would drag the plate towards black
# and make every house look the same. Layer 2's colour is the one thing NOT
# fixed here: the callback overwrites it per cell at runtime.
#
# Index 0 ships pointing at the vacant plate rather than at 1x1_blank_white,
# because a cell that has never had its plate set must not flash white.
#
#   3  the frame (author, 2026-09-28: "add portrait borders") - never swapped,
#      on top of all three so nothing the Lua writes can cover it. NOT the
#      card's panel_back_border, which is what "the portrait is doubled when
#      assigned" was.
#
# OUR OWN ART IN CA's BRONZE, not CA's file (author, same day, of CA's
# Hell-Forge unit_card_frame in game: "make the borders thicker, the character
# portrait permeates thru the border"). CA's frame is 2px of bronze, and its
# outermost pixel is TRANSPARENT and the next a near-black line at 65% - so the
# visible bronze began 2px inside the cell, and the portrait's own outer 2px
# showed round it. This one is opaque from its first pixel, carries 4px of
# bronze (CA's measured 161,102,52 -> 102,57,23, lit one step brighter at the
# outside), and is pushed FRAME_OUT px past the cell on every side so the
# portrait's edge is under the frame and not beside it.
FRAME_ART = "%s/portrait_frame.png" % PLATE_DIR
FRAME_MARGIN = 8
FRAME_OUT = 2
FRAME_PX = 32
# By distance in from the frame's outer edge. Past the list: clear.
FRAME_BAND = [(26, 14, 6, 255), (190, 128, 66, 255), (161, 102, 52, 255),
              (130, 78, 36, 255), (102, 57, 23, 255), (20, 10, 4, 255),
              (0, 0, 0, 110), (0, 0, 0, 40)]
FRAME_BRONZE = 4
FACE_LAYERS = [
    {"path": plate_path(None),
     "offset": (0, 0), "dw": 0, "dh": 0, "margin": 0, "colour": "#FFFFFFFF",
     "dock": None},
    {"path": "ui/skins/default/1x1_blank_white.png",
     "offset": (0, 0), "dw": 0, "dh": 0, "margin": 0, "colour": "#FFFFFFFF",
     "dock": None},
    {"path": MASK_NONE,
     "offset": (0, 0), "dw": 0, "dh": 0, "margin": 0, "colour": "#FFFFFFFF",
     "dock": None},
    {"path": FRAME_ART,
     "offset": (-FRAME_OUT, -FRAME_OUT), "dw": 2 * FRAME_OUT,
     "dh": 2 * FRAME_OUT, "margin": FRAME_MARGIN,
     "colour": "#FFFFFFFF", "dock": None},
]
# The Lua addresses layers by these numbers; import_iron_court.py compares them
# against ICUI.PLATE_INDEX / ICUI.FACE_INDEX / ICUI.MASK_INDEX. Written out
# rather than derived from the list, because a derived index quietly follows a
# layer inserted in the wrong place instead of failing.
PLATE_INDEX = 0
FACE_INDEX = 1
MASK_INDEX = 2
FRAME_INDEX = 3

# PrimaryColour and not BannerPrimaryColour: a house's identity here is the
# faction colour the rest of the campaign already shows for it. CA binds both -
# ui/campaign ui/waaagh_top_bar.twui.xml uses FactionContext.PrimaryColour and
# ui/frontend ui/custom_battle.twui.xml uses BannerPrimaryColour.
FACE_COLOUR_FROM = {"object": "CcoCampaignFaction", "function": "PrimaryColour",
                    "index": MASK_INDEX}


def wedge_layers(i):
    """One layer, replaced at draw time by SetImagePath.

    THIS SLICE'S OWN empty-colour picture, not slice zero's: the layer is the
    shape as well as the colour, so a wedge that has never been drawn still has
    to be the right wedge or the pie is sixty copies of its first slice until
    the first refresh.
    """
    return [{"path": wedge_path(i, None), "offset": (0, 0), "dw": 0, "dh": 0,
             "margin": 0, "colour": None, "dock": None}]

# The Hashut bull mask, CA's own at ui/skins/default/icon_wh_main_lore_hashut.png
# - 56x56, the plate's own size, and gold against the plate's dark brown. It is
# free: button_toz wears icon_tower_of_zharr.png and button_hellforge
# icon_hellforge.png (both read out of hud_campaign.twui.xml), so the bull is not
# already spoken for by another Chaos Dwarf button.
#
# WHY IT IS NOT OPTIONAL. Without it the opener is two generic plates and nothing
# else - a featureless disc, measured 56.7% opaque at rgb(68,26,15). Both
# neighbours on the strip carry a glyph, and after the revert all three sit in a
# row; the unmarked one is the one nobody finds.
# The opener had no tooltip at all - hovering it said nothing about what it
# opened. Both neighbours on the strip carry one.
OPENER_TIP = ("The Iron Court||The great houses, the offices of state and "
              "the governors of your provinces.")
OPENER_ICON = "ui/skins/default/icon_wh_main_lore_hashut.png"
# Inset 7 on a 44px button, so a 30x30 glyph - the Great Guilds' proportion at
# this exact size. dw/dh are deltas from the component box, not absolutes.
OPENER_ICON_INSET = 7

OPENER_LAYERS = [
    {"path": PLATE % "underlay", "offset": (0, 0), "dw": 0, "dh": 0, "margin": 0,
     "dock": None},
    {"path": PLATE % "active", "offset": (0, 0), "dw": 0, "dh": 0, "margin": 0,
     "dock": None},
    {"path": OPENER_ICON,
     "offset": (OPENER_ICON_INSET, OPENER_ICON_INSET),
     "dw": -2 * OPENER_ICON_INSET, "dh": -2 * OPENER_ICON_INSET,
     "margin": 0, "dock": "Center"},
]
# A state with no transitionmap edge pointing at it is never entered, so a hover
# authored without one is dead art.
# The close button is NOT the opener. The two shared OPENER_LAYERS, which was
# harmless while both were bare plates and became wrong the moment the opener
# gained the Hashut bull: the close button would have worn the same face as
# the button that opens the panel. CA icon_cross.png is a 56x56 gold X on the
# same plate size.
CLOSE_ICON = "ui/skins/default/icon_cross.png"
CLOSE_INSET = 12                      # a 48px button, so a 24px X


def plated(icon, inset, state):
    """A round button: plate, state plate, then an inset glyph."""
    return [
        {"path": PLATE % "underlay", "offset": (0, 0), "dw": 0, "dh": 0,
         "margin": 0, "dock": None},
        {"path": PLATE % state, "offset": (0, 0), "dw": 0, "dh": 0,
         "margin": 0, "dock": None},
        {"path": icon, "offset": (inset, inset), "dw": -2 * inset,
         "dh": -2 * inset, "margin": 0, "dock": "Center"},
    ]


CLOSE_LAYERS = plated(CLOSE_ICON, CLOSE_INSET, "active")
CLOSE_HOVER = plated(CLOSE_ICON, CLOSE_INSET, "hover")

# THE HELP BUTTON WEARS THE CLOSE BUTTON'S PLATE and CA's gold question mark.
# The Tower of Zharr's bronze "i" came first and was a dark mark on a dark
# plate that nobody saw (author, 2026-09-28). icon_question_mark.png is 38x38,
# so a 6px inset draws it at 36 - near native, not stretched.
HELP_ICON = "ui/skins/default/icon_question_mark.png"
HELP_LAYERS = plated(HELP_ICON, 6, "active")
HELP_HOVER = plated(HELP_ICON, 6, "hover")

OPENER_HOVER = [
    {"path": PLATE % "underlay", "offset": (0, 0), "dw": 0, "dh": 0, "margin": 0,
     "dock": None},
    {"path": PLATE % "hover", "offset": (0, 0), "dw": 0, "dh": 0, "margin": 0,
     "dock": None},
    # The glyph has to be on BOTH states. A hover state that drops it makes the
    # icon blink out exactly when the player puts the cursor on it.
    {"path": OPENER_ICON,
     "offset": (OPENER_ICON_INSET, OPENER_ICON_INSET),
     "dw": -2 * OPENER_ICON_INSET, "dh": -2 * OPENER_ICON_INSET,
     "margin": 0, "dock": "Center"},
]

# Tabs and text buttons are tiled plate plus border, NOT a stretched button
# Tabs wear CA's own button plate, 9-sliced, exactly as the Great Guilds' tabs do.
# The first draft dressed them in panel_back_tile + panel_back_border instead, on
# the theory that stretched button art is a smear - but a 9-SLICED plate does not
# stretch its ends, and a panel FRAME at margin 0 tiled four little frames onto
# every tab. button_square_medium_text_*.png is verified present in ui2.pack;
# button_square_medium_*.png (no _text_) is the one that does not exist.
BTN_PLATE = "ui/skins/default/button_square_medium_text_%s.png"
PLATE_TOP, PLATE_BOT, PLATE_PX = 3.0, 33.0, 46.0     # measured alpha rows
_PLATE_SPAN = (PLATE_BOT - PLATE_TOP) / PLATE_PX


def plate(h, state):
    """Layers making the plate's visible pill exactly fill a box h tall."""
    img_h = h / _PLATE_SPAN
    dh = int(round(img_h - h))
    dy = int(round(-PLATE_TOP / PLATE_PX * img_h))
    return [{"path": BTN_PLATE % state, "offset": (0, dy), "dw": 0, "dh": dh,
             "margin": 8, "dock": None}]


TAB_H = PANEL_LAYOUT["ic_tab_court"][3]
BTN_LAYERS = plate(TAB_H, "active")
BTN_HOVER = plate(TAB_H, "hover")

# THE TABS WEAR CA'S SKULL-CAPPED TAB (author, 2026-09-26: "use more of the
# chaos dwarf ui borders and elements", pointing at the Hell-Forge's Armoury
# tab), and the panel's name sits on the Chaos Dwarf title banner.
#
# TRIMMED COPIES, NOT CA'S FILES. tab_square_large_text_*.png is 354x103 with
# the bar in rows 8-43 and the selected glow under it; fitted to a 32px tab
# that needs a layer larger than its box, and a runtime component's layers are
# sized to the box - preview_iron_court draws them that way, and the engine
# resizes them with it. Trimmed to the art's own alpha box, each picture fills
# its component exactly, with no offset for anything to disagree about. See
# CHD_CUTS; cut_chd_art() makes them from the installed packs.
TAB_ART = PLATE_DIR + "/chd_tab_%s.png"
# THE CAPS, MEASURED ON THE TRIMMED ART: the skull and its bronze bezel end at
# column 38 and the bar's rounded end at 45. CA slices this art at 65
# ("0,65,0,65" in hellforge_panel_main.twui.xml), which is generous on a 334px
# tab and left "Petitions" 72px of a 200px tab at 1600 - 40 keeps the whole
# skull in the corner, and a label clears the rounded end at 46.
TAB_CAP = 40
TAB_TEXT_INSET = 46


def tab_plate(state):
    return [{"path": TAB_ART % state, "offset": (0, 0), "dw": 0, "dh": 0,
             "margin": (0, TAB_CAP), "dock": None}]


TAB_LAYERS = tab_plate("active")
assert all(TAB_ART % st in CHD_CUTS for st in ("active", "hover", "selected", "selected_hover"))
TAB_HOVER = tab_plate("hover")

# The race skin's panel_title.png, 544x59, trimmed to 437x56. Its arrow ends
# are CA's margin of 165 ("0,165,0,165" in the same file), less the 54 columns
# the trim takes off.
TITLE_ART = PLATE_DIR + "/chd_title.png"
TITLE_CAP = 111
# THE BANNER'S FIELD IS ROWS 12-40 OF 56, so it is drawn at 56 - squashed to 44
# the field was 22px and the game's 24px title ran over both rims - and the
# words are lifted 2px onto the field's middle (row 26, not the box's 28).
TITLE_TY = "0.00,4.00"

# A PLATE HUGS ITS WORDS (author, 2026-09-26, on the column titles: "why is it all
# stretched to the corners?"). The cell is the most room a plate may take, not its
# size: ICUI.fit_plate shrinks each of these to its text's width plus a cap and
# PLATE_GAP either side, measured by the engine, and centres it in the cell - or,
# for the banner, keeps its left end where the panel's corner is. fit_plate() is
# that rule once, for the preview; the Lua is the other copy.
PLATE_GAP = 14
FIT_PLATES = {"ic_title": (TITLE_CAP, True), "ic_col_left": (HEADING_CAP, False),
              "ic_col_right": (HEADING_CAP, False),
              # THE HELP TOPIC'S NAME, on the heading plate, sized to it and
              # held to the page's left edge.
              "ic_help_head": (HEADING_CAP, True)}
for _i in range(PLOT_COLS):
    FIT_PLATES["ic_plotcat_%d" % (_i + 1)] = (HEADING_CAP, False)
for _i in range(LAW_COLS):
    FIT_PLATES["ic_law_head_%d" % (_i + 1)] = (HEADING_CAP, False)
FIT_PLATES["ic_off_title"] = (HEADING_CAP, False)
FIT_PLATES["ic_gc_now"] = (HEADING_CAP, False)


def fit_plate(name, x, w, text_w):
    """(x, w) of a FIT_PLATES cell once its plate is sized to text_w."""
    cap, left = FIT_PLATES[name]
    want = min(w, int(-(-text_w // 1)) + 2 * (cap + PLATE_GAP))
    return (x if left else x + (w - want) // 2), want
TITLE_LAYERS = [{"path": TITLE_ART, "offset": (0, 0), "dw": 0, "dh": 0,
                 "margin": (0, TITLE_CAP), "dock": None}]

LABEL_TX, LABEL_TY = "6.00,0.00", "4.00,0.00"

# THE PLATE'S END CAPS, which a centred label has to clear on both sides.
#
# A 9-slice draws its left and right margins at their native width and stretches
# only what is between them, so the flat middle of a button is its width less
# twice this - and a label wider than that middle lies across a corner of the
# frame. Read off the layer rather than typed, because plate() sets it and a
# button built from another texture would carry another one.
BTN_PLATE_MARGIN = max([ly["margin"] for ly in BTN_LAYERS] or [0])

# THE CELLS THAT WEAR ONE. Each is built with layers=BTN_LAYERS and centred text
# at tx="0.00,0.00" - no inset at all - so LABEL_TX is the wrong allowance for
# them in both directions: it takes off 6px they do not spend and leaves on the
# 16px they do. "APPOINT" fit ic_card_button's 74px box by 7px and drew over both
# ends of the plate, which is the 2026-09-17 report.
# WHICH ROW BUTTON EACH PETITION LABEL GOES ON (check 20k): the answer a row
# asks for on the main button, the other on the second.
PETITION_BTN_CELL = {"accept": "ic_row_e", "back": "ic_row_e",
                     "refuse": "ic_row_f", "peace": "ic_row_f",
                     "hold": "ic_row_f"}

BTN_CELLS = {"ic_card_button", "ic_row_e", "ic_row_f", "ic_plot_go",
             "ic_act_provoke", "ic_act_gift", "ic_act_secure", "ic_act_purge",
             "ic_fill", "ic_gov_btn",
             "ic_law_p_btn", "ic_lv_back", "ic_lv_over_1", "ic_lv_over_2",
             } | set("ic_lb_win_%d" % (i + 1) for i in range(LB_MEN))


def usable_w(box_w, name):
    """How much of a cell a string may actually occupy."""
    if name in BTN_CELLS:
        return box_w - 2 * BTN_PLATE_MARGIN
    if name in LAW_TAB_BUTTONS:
        # THE SKULL CAPS (author, 2026-10-03): LABEL_TX let "Strongly favour 250"
        # pass in a 270px tab whose bar between the caps is 178.
        return box_w - 2 * TAB_TEXT_INSET
    if name == "ic_influence":
        return box_w - 2 * SEATS_PAD
    if name.startswith("ic_law_head_"):
        # THE PLATE'S ARROW ENDS AND GAP, both sides (FIT_PLATES).
        return box_w - 2 * (HEADING_CAP + PLATE_GAP)
    return box_w - int(float(LABEL_TX.split(",")[0]))

# FONT CATEGORY IS THE UNIT, NOT PIXELS. EU.fontcat() rounds a requested size
# to the nearest category the game HAS, and the body family is only (10, 12,
# 16). Every label here asked for 14 - equidistant from 12 and 16, so min()
# took 12 - and the whole panel shipped at body_12 on a 1920x1080 screen.
# That is the "fonts are small and barely readable" report, and check 6 could
# not see it because body_12 is a perfectly real category; it just was not the
# one anyone chose.
#
# So the category is NAMED, and the size beside it is the one that category
# actually is. Nothing rounds any more.
# TWO SIZES FOR THE WHOLE PANEL, and everything else is derived from them.
#
# It used to be five: 24, 18, 16, 14 and 12, chosen cell by cell as each one was
# built, so an office card's detail was body_12 while a party card's was body_16
# and a move card's blurb defaulted to something nobody had picked. Read from
# across a desk that is not a hierarchy, it is noise - and the smallest of them
# was unreadable at 1080p.
#
# CONTENT IS header_18 AND NOT A BODY FACE, because it cannot be: the engine's
# body family is 10, 12 and 16 and stops there (see FONTCATS in the emitter), so
# 16 was already the ceiling on three of the five tabs. Anything larger has to
# come from the header family, and header_18 is the largest face in it that is
# not bold.
# HOW MUCH WIDER THE ENGINE DRAWS THAN THE DESKTOP FACE THIS MEASURES WITH.
#
# Measured from a screenshot of the shipped panel on 2026-09-13: the game wrapped
# a name that PIL's DEFAULT face calls 210px inside a 280px cell, so the engine is
# about 1.33x that face. The checks below measure with Segoe UI Black instead,
# which is itself 1.115x the default face - so against seguibl the engine is
# 1.33 / 1.115 = 1.19, and a check that applied no factor at all was measuring
# 19% narrow. That is the dangerous direction: it passes a string the engine then
# cuts, which is how a clip reaches a player's screen with a green build behind
# it.
#
# ONE NUMBER, HERE. preview_iron_court.py imports it rather than keeping its own,
# so the picture and the check cannot disagree about where a line ends - they did
# on 2026-09-14, and the picture was the one telling the truth.
#
# STILL A PROXY. The engine's own figure is TextDimensionsForText and needs the
# game running; this is the best a shut-game instrument can do, and it is
# deliberately the pessimistic side of it.
GAME_FONT_WIDER = 1.19

TITLE = (20, "header_20_bold")         # every heading and every card's name
BODY = (18, "header_18")               # every line of content, everywhere
PANEL_TITLE = (24, "header_24_bold")   # the panel's own name, once

# CELLS THE PANEL CUTS RATHER THAN FITS, and the only ones 20g may let past.
#
# A cell is here when its content is a CHARACTER's name, it has his picture
# beside it, and the card has no second line to spill onto. That is one cell:
# the party card's leader line, 281px beside a 100px face on a card packed to
# its own floor, against a 331px worst-case name at the panel's content size.
# The choice was put to the author on 2026-09-14 - cut it, shrink that one cell
# to 14, or take a fit with zero pixels to spare - and cutting won, so the panel
# keeps one content size everywhere.
#
# THIS IS A WEAKENING OF 20g AND IT IS PAID FOR. Check 20h asserts the panel Lua
# declares the named helper and calls it on this cell; an exemption that only
# silences a check is how a clip ships with a green build behind it.
#
# THE OFFICE CARD'S TWO JOINED IT ON 2026-09-17, and for a stronger reason than
# the party card's: ic_card_holder draws a character's name off the campaign and
# ic_card_house a party name rolled at run time, so neither string exists when
# this file runs and there is nothing here to measure even in principle. 20c's
# list of measured cells covers five of the card's seven and these are the two
# it leaves out.
#
# THE OFFICES PREVIEW IS WHAT FOUND THEM. ic_card_house is 170px against a name
# that reaches about 285 at the size it was drawing, and the picture showed
# "Covenant of the Ninth Furnace" leaving its card through the side and crossing
# the card beside it. Nothing else here had ever looked.
#
# AND THE PICKER'S NAME CELL JOINED THEM ON 2026-09-17. It is the oldest of the
# three faults and the one nothing had ever looked at: a man's name has carried
# his TRADE behind it since the backgrounds arrived, so the cell has been drawing
# "Amarudz Grimtidesson, Daemonsmith" - 406px - into 380 and cutting it mid-word
# in silence. It takes a position name in front of that now, and 20j holds the
# NAME half to the width while the cut takes the trade.
CUT_CELLS = {"ic_party_leader": "ICUI.fit_cut",
             "ic_card_holder": "ICUI.fit_cut",
             "ic_card_house": "ICUI.fit_cut",
             "ic_row_a": "ICUI.fit_cut"}
TEXT_STYLE = {
    # THE PANEL'S OWN NAME, the one thing above the two sizes.
    "ic_title": PANEL_TITLE,

    # HEADINGS. The column headers of every tab, the section label, the standing
    # figure, and the name at the top of every card - office, party and move.
    # ic_plotcat_* is in this list now and was in NO list before: it fell through
    # to the default and drew the intrigue tab's four column headers at the
    # content size, which is why they read as captions rather than as headings.
    "ic_influence": TITLE,
    "derpy_ic_gm_name": (12, "body_12"),
    "derpy_ic_gm_loyal": (12, "body_12"),
    # THE GOVERNORS VIEW'S COLUMN ROW: a name, then two small lines.
    "ic_gr_l1": (16, "header_16"),
    "ic_gr_l2": (12, "body_12"),
    "ic_gr_l3": (12, "body_12"),
    "ic_lbl_section": TITLE,
    "ic_hdr_a": TITLE,
    "ic_hdr_b": TITLE,
    "ic_hdr_c": TITLE,
    "ic_hdr_d": TITLE,
    "ic_hdr_e": TITLE,
    "ic_col_left": TITLE,
    "ic_col_right": TITLE,
    "ic_plotcat_1": TITLE,
    "ic_plotcat_2": TITLE,
    "ic_plotcat_3": TITLE,
    "ic_plotcat_4": TITLE,
    "ic_law_head_1": TITLE,
    "ic_law_head_2": TITLE,
    "ic_law_head_3": TITLE,
    "ic_law_head_4": TITLE,
    "ic_off_title": TITLE,
    "ic_gc_now": TITLE,
    "ic_card_name": TITLE,
    "ic_party_name": TITLE,
    "ic_party_name2": TITLE,
    "ic_plot_name": TITLE,
    "ic_leader_lbl": TITLE,
    "ic_leader_name": TITLE,
    # THE SAME NUMBER IN THE SAME WORDS as ic_influence - "137 standing" - read
    # off the character panel instead of this one. Two sizes for one figure
    # reads as two different figures.
    "derpy_ic_standing": TITLE,

    # THE OFFICE CARD IS THE EXCEPTION, whole. Every other cell on this panel
    # draws at TITLE or BODY; these five cannot, because the card is 298px wide
    # and 124px tall and neither number is ours - see CARD_LAYOUT.
    #
    # EACH ONE IS THE LARGEST FACE THAT FITS ITS OWN CELL, measured rather than
    # picked, against the widest string the model can put in it:
    #
    #   ic_card_name    "Warden of the Caravan Roads"          276 of 298
    #   ic_card_term    "4000 standing - 99 turns left"        268 of 298
    #   ic_card_effect  "Armaments +15%, Raw Materials +12%"   277 of 298
    #   ic_card_need    "[icon]400 / lvl 30"                    94 of 100
    #   ic_card_button  "APPOINT"                               67 of  84
    #
    # THE BUTTON'S FIGURE IS NOT ITS CELL. It is a centred label on a 9-sliced
    # plate, so what it may occupy is the width less the two 8px end caps - see
    # usable_w. Measured against the box instead, 67 of 68 read as a fit and drew
    # over both corners of the frame.
    #
    # THE TWO 12s ARE THE TIGHT ONES, and they are tight because they sit beside
    # the face rather than across the card. Anything larger clips; the next step
    # down is body_10, which is the size this whole pass set out to get rid of.
    "ic_card_name": (16, "header_16"),
    # THE HOLDER AT THE CARD'S OWN SIZE. It was in no list at all, so it fell
    # through to BODY - 18px, LARGER than the 16 of the card title above it, in
    # a 190px box beside a portrait. Even cut, that read as three words and an
    # ellipsis; at 16 most Chaos Dwarf names fit whole.
    "ic_card_holder": (16, "header_16"),
    # AND THE PARTY AT THE EFFECT LINE'S. 170px is the widest this cell can ever
    # be - it runs from the crest beside it to the card's frame band - and a
    # rolled name reaches 30 characters. 12 is the size at which the ordinary
    # ones fit and only the longest few take the cut, and it is a size this card
    # already uses one row down.
    "ic_card_house": (12, "body_12"),
    "ic_card_term": (16, "header_16"),
    "ic_card_effect": (12, "body_12"),
    "ic_card_need": (12, "body_12"),
    "ic_card_button": (12, "body_12"),

    # EVERYTHING ELSE IS BODY, and is not listed. style() falls through to it,
    # so a cell added later is content unless somebody says otherwise - which is
    # the right default and was not the old one.
}
# THE GOVERNMENT CARDS' NAME AND HEADINGS take the panel's title size.
for _i in range(GOV_CARDS):
    for _k in ("name", "name2", "ruleh", "fxh", "loyh"):
        TEXT_STYLE["ic_gc_%s_%d" % (_k, _i + 1)] = TITLE


def style(name, **extra):
    """The text kwargs for one component: a named category, never a guess."""
    size, cat = TEXT_STYLE.get(name, BODY)
    out = {"text": True, "size": size, "fontcat": cat}
    out.update(extra)
    return out

# The two court column headings. A named pair rather than two literals in the
# builder, so the scale pass can step it down with every other font.
COL_HDR_FONT = (18, "header_18_bold")

TAB_TEXT = {"text": True, "size": BODY[0], "fontcat": BODY[1], "align": "Center", "valign": "Center",
            "tx": "0.00,0.00", "ty": "0.00,0.00", "leading": 0}


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------
# The scroll track is a recessed well, the thumb a lit plate, so the thumb reads
# as the thing that moves. Both are flat fills: a frame texture at this width has
# nowhere to put its corners.
PAGE_LAYERS = plate(PANEL_LAYOUT["ic_page_prev"][3], "active")
PAGE_HOVER = plate(PANEL_LAYOUT["ic_page_prev"][3], "hover")

# CA'S OWN SORT ARROW, both halves of it. Read out of ui2.pack and measured
# at 17x18, which is why the components are 17x18 - a sort arrow scaled to a
# box somebody chose is the blurriest thing on a panel.
#
# TWO LAYERS AND NOT TWO STATES. The down arrow is the standard layer and the
# up arrow the hover one, and ICUI.light_sorts rewrites BOTH with
# SetImagePath when the direction flips - the same trick ICUI.light_tabs
# already uses on the tab plates, and for the same reason: a third state
# costs a GUID slot in the emitter and every check that counts them, for a
# picture one call can supply.
SORT_ARROW_DOWN = "ui/skins/default/parchment_sort_arrow_down.png"
SORT_ARROW_UP = "ui/skins/default/parchment_sort_arrow_up.png"


def _arrow(path):
    return [{"path": path, "offset": (0, 0), "dw": 0, "dh": 0,
             "margin": 0, "dock": None}]


SORT_LAYERS = _arrow(SORT_ARROW_DOWN)
SORT_HOVER = _arrow(SORT_ARROW_UP)
# CA's own category for this control, read off the donor rather than reused
# from the tab row: a sort arrow is a slider arrow and it clicks like one.
SORT_SOUND = "UI_GBL_TMP_Slider_Arrows"


def _panel_order(name):
    """THE CRESTS ARE DECLARED LAST, and that is the whole of their z-order.

    Children draw in declaration order and the panel propagates ONE priority
    over the whole tree at runtime, so a priority attribute cannot lift a crest
    above the cells it labels - only its place in the panel can. It did not
    matter while the dial was a ring of pips at radius 84 and the crests a ring
    at 62: the two never touched. A FILLED pie touches everything inside it.

    Sorted by name otherwise, because a GUID is derived from the name and its
    position and an unstable order is a file that differs from itself.
    """
    if name == "ic_zig_bg":
        # SECOND, after the Governors pins that must be first (check_gm) and
        # never share a view with it: the offices tab's cards and every line
        # stand over it.
        return (-3, name)
    if name == "ic_gm_pins":
        # FIRST OF ALL (check_gm), and under tier -1 on purpose: make_ic_backdrop
        # takes every tier -1 name for an opaque plate on every view.
        return (-3, name)
    if name in ("ic_gm_top", "ic_gm_foot", "ic_gm_col"):
        # UNDER EVERYTHING THEY HOLD, and not tier -1: see ic_gm_pins.
        return (-2, name)
    if name in ("ic_dial_box", "ic_crown_box") or name in LAW_PLATES:
        # THE TWO PLATES, under everything they hold. And the laws tab's. A plate is opaque, so a
        # plate declared after its contents is a plate drawn over them - which
        # is the same fault as a crest declared before the pie, in reverse.
        tier = -1
    elif name == "ic_gov_glow":
        # UNDER ic_gov, whose icon it lights, and over the Crown's plate. Not
        # -1: make_ic_backdrop takes every tier -1 name for an opaque plate.
        tier = -0.5
    elif name.startswith("ic_barc_") or name.startswith("ic_barp_"):
        tier = 3
    elif name == "ic_dial_rim":
        tier = 2                # over the walls, so their tips tuck under it
    elif name.startswith("ic_div_") or name == "ic_lv_barrim":
        tier = 1                # over every wedge, under the frame; and over the vote bar's segments
    elif name.startswith("ic_mark_"):
        tier = 4                # over the tab whose skull it lights
    else:
        tier = 0
    return (tier, name)


def _panel():
    root = EU.C("root", PANEL_W, PANEL_H)
    panel = root.add(EU.C("derpy_ic_panel", PANEL_W, PANEL_H, layers=PANEL_LAYERS))
    for name in sorted(PANEL_LAYOUT, key=_panel_order):
        _x, _y, w, h = PANEL_LAYOUT[name]
        if name == "ic_zig_bg":
            # A PICTURE AND NOTHING ELSE: not interactive, or it eats the cards' gaps.
            panel.add(EU.C(name, w, h, layers=[
                {"path": ZIG_PATH, "offset": (0, 0), "dw": 0, "dh": 0,
                 "margin": 0, "colour": None, "dock": None}]))
            continue
        if name == "ic_gm_pins":
            # NO ART AND NO CLICKS: the bare map beside a pin must take the click.
            panel.add(EU.C(name, w, h))
            continue
        if name in ("ic_gm_top", "ic_gm_foot", "ic_gm_col"):
            # OPAQUE, AND IT TAKES THE CLICK: over the live map a click on its
            # blank must not fall through and select what stands under it.
            art, margin = ((GM_COL_ART, 0) if name == "ic_gm_col" else (GM_PLATE, GM_PLATE_MARGIN))
            panel.add(EU.C(name, w, h, interactive=True, sound=OPENER_SOUND,
                           layers=[_gm_full(art, margin)]))
            continue
        if name == "ic_gm_head":
            panel.add(EU.C(name, w, h, layers=[_gm_full(GM_HEAD_ART, (0, 80))],
                           **dict(TAB_TEXT, size=TITLE[0], fontcat=TITLE[1])))
            continue
        if name in GM_TOG_ICONS:
            # CA'S ROUND TOGGLE, lit by swapping its art into layers 0 and 2
            # (ICUI.GM_TOG_ART), as the court's tabs are lit.
            panel.add(EU.C(name, w, h, interactive=True, sound=OPENER_SOUND,
                           layers=[_gm_full(GM_ROUND % "active"), _gm_inset(GM_TOG_ICONS[name], 12)],
                           hover=[_gm_full(GM_ROUND % "hover"), _gm_inset(GM_TOG_ICONS[name], 12)]))
            continue
        if name.startswith("ic_gm_tog_lbl_"):
            # THE WORD IN THE FIELD: (top, bottom) padding of the art's rails.
            panel.add(EU.C(name, w, h, layers=[_gm_full(GM_TOG_LABEL_ART, GM_PLATE_MARGIN)],
                           **dict(TAB_TEXT, ty="%.2f,%.2f" % GM_PLATE_RAIL)))
            continue
        if name == "ic_gm_hint":
            panel.add(EU.C(name, w, h, **style(name, valign="Center")))
            continue
        if name.startswith("ic_gm_sort_"):
            # THE COURT'S ARROW AT THE END OF ITS LABEL; the label is lit from
            # Lua while its column sorts, as the court's headers are.
            panel.add(EU.C(name, w, h, interactive=True, sound=SORT_SOUND,
                           layers=[{"path": SORT_ARROW_DOWN, "offset": (w - 21, (h - 18) / 2.0),
                                    "dw": 17 - w, "dh": 18 - h, "margin": 0, "dock": None}],
                           **style(name, valign="Center")))
            continue
        if name == "ic_gm_btns":
            panel.add(EU.C(name, w, h, layers=[_gm_full(GM_HF + "button_holder_back.png")]))
            continue
        if name in ("ic_gm_ok", "ic_gm_no"):
            icon = ("ui/skins/default/icon_check.png" if name == "ic_gm_ok"
                    else "ui/skins/default/icon_cross.png")
            # THE TOOLTIP IS WRITTEN FROM LUA, per page; the round button's own
            # states are CA's, and the disabled look is ICUI.grey_look.
            panel.add(EU.C(name, w, h, interactive=True, sound=OPENER_SOUND,
                           layers=[_gm_full(GM_ROUND % "active"), _gm_inset(icon, 12)],
                           hover=[_gm_full(GM_ROUND % "hover"), _gm_inset(icon, 12)]))
            continue
        if name in LAW_PLATES:
            # THE LAWS TAB'S PLATES, the Crown's box's layers. Not interactive.
            panel.add(EU.C(name, w, h, layers=CARD_LAYERS))
            continue
        if name in ("ic_law_p_icon", "ic_lv_icon") or name.startswith(
                ("ic_lv_sicon_", "ic_lv_seg_", "ic_lv_segc_", "ic_gc_icon_")):
            # ONE PICTURE, set from Lua: a law's icon, a party's plate or crest.
            panel.add(EU.C(name, w, h, layers=PORT_LAYERS))
            continue
        if name.startswith("ic_lv_screst_"):
            panel.add(EU.C(name, w, h, layers=FACE_LAYERS, colour_from=FACE_COLOUR_FROM))
            continue
        if name.startswith("ic_law_p_bar") or name == "ic_lv_barrim":
            # THE PANE BAR: the grey ground (abstaining), and each side its plate.
            side = name[len("ic_law_p_bar"):]
            if side == "rim" or name == "ic_lv_barrim":
                o = LAW_PBAR_RIM_OUT
                panel.add(EU.C(name, w, h, layers=[
                    {"path": law_pbar_path("rim"), "offset": (-o, -o), "dw": 2 * o, "dh": 2 * o,
                     "margin": len(LAW_PBAR_RIM_BAND), "colour": None, "dock": None}]))
                continue
            panel.add(EU.C(name, w, h, layers=[
                {"path": law_pbar_path(side) if side else plate_path(None), "offset": (0, 0),
                 "dw": 0, "dh": 0, "margin": 0, "colour": None, "dock": None}]))
            continue
        if name == "ic_lv_bar":
            # THE BAR'S GROUND, the grey plate: the abstaining share between sides.
            panel.add(EU.C(name, w, h, layers=[
                {"path": plate_path(None), "offset": (0, 0), "dw": 0, "dh": 0,
                 "margin": 0, "colour": None, "dock": None}]))
            continue
        if name in LAW_TAB_BUTTONS:
            panel.add(EU.C(name, w, h, interactive=True, sound=OPENER_SOUND,
                           layers=TAB_LAYERS, hover=TAB_HOVER, **TAB_TEXT))
            continue
        if name in LAW_PAGE_BUTTONS:
            panel.add(EU.C(name, w, h, interactive=True, sound=OPENER_SOUND,
                           layers=PAGE_LAYERS, hover=PAGE_HOVER, **TAB_TEXT))
            continue
        if name.startswith("ic_gc_") and name != "ic_gc_now":
            # THE GOVERNMENT CARDS' WORDS, centred on their card (design A).
            panel.add(EU.C(name, w, h, align="Center", valign="Center",
                           tx="0.00,0.00", ty=LABEL_TY, **style(name)))
            continue
        if name.startswith("ic_mark_") or name == "ic_gov_glow":
            panel.add(EU.C(name, w, h, layers=MARK_LAYERS))
        elif name.startswith("ic_barc_"):
            # The crest plate. Blank white at index 0 so SetImagePath has a layer
            # to replace, and no text - it is a picture cell.
            # INTERACTIVE, because a tooltip can only be reached on an
            # interactive component, and this is the only thing on the dial a
            # player can hover to find out whose colour that is.
            panel.add(EU.C(name, w, h, interactive=True, sound=OPENER_SOUND,
                           layers=PORT_LAYERS))
        elif name in ("ic_col_left", "ic_col_right", "ic_help_head"):
            # CENTRED OVER ITS OWN COLUMN, which is what makes the two columns
            # read as two columns rather than as one wide tab with a rule in it.
            # ON A PLATE since 2026-09-26: see HEADER_LAYERS. HEADING_TY lifts
            # the words onto the field, which sits 2px above the art's middle.
            panel.add(EU.C(name, w, h, layers=HEADER_LAYERS,
                           **dict(TAB_TEXT, size=COL_HDR_FONT[0],
                                  fontcat=COL_HDR_FONT[1], ty=HEADING_TY)))
        elif name.startswith(("ic_plotcat_", "ic_law_head_", "ic_off_title", "ic_gc_now"))                 and name != "ic_gc_nowrule":
            # THE MOVE GROUPS, on the same plate and centred on it like the
            # column titles: a left-aligned word would sit on the arrow.
            panel.add(EU.C(name, w, h, layers=HEADER_LAYERS, align="Center",
                           valign="Center", tx="0.00,0.00", ty=HEADING_TY,
                           **style(name)))
        elif name.startswith("ic_barp_"):
            # A PICTURE-FREE TEXT CELL, centred on its own box: it is placed on
            # its party's ray every draw, so the text has to sit in the middle
            # of the cell rather than at its left edge like a column does.
            panel.add(EU.C(name, w, h, **dict(TAB_TEXT)))
        elif name == "ic_help_box":
            # THE HELP PAGE'S CARD, the dial's own layers. Not interactive: it
            # lies under the topic buttons and would eat their clicks.
            panel.add(EU.C(name, w, h, layers=CARD_LAYERS))
        elif name == "ic_dial_box":
            # THE CARD'S OWN LAYERS: a tiled body and a 9-sliced frame over it,
            # which is what every other framed thing in this panel is made of.
            # NOT INTERACTIVE - it covers the whole dial, and an interactive
            # plate there would eat every crest's hover.
            panel.add(EU.C(name, w, h, layers=CARD_LAYERS))
        elif name == "ic_dial_rim":
            # NOT INTERACTIVE. It is a frame, and an interactive frame over the
            # whole pie box would eat the crests' hovers.
            panel.add(EU.C(name, w, h, layers=[
                {"path": rim_path(), "offset": (0, 0), "dw": 0, "dh": 0,
                 "margin": 0, "colour": None, "dock": None}]))
        elif name == "ic_crown_box":
            # THE SAME TILED BODY AND 9-SLICED FRAME the cards wear, and the
            # dial's plate. NOT INTERACTIVE: it covers the control lines, the
            # leader's trait and his porthole, and an interactive plate over
            # them would eat every one of their hovers.
            panel.add(EU.C(name, w, h, layers=CARD_LAYERS))
        elif (name == "ic_divider" or name.startswith("ic_crown_rule_")
              or name == "ic_help_rule"):
            # A FLAT FILL, not a frame texture. It is 4px wide and a 9-slice
            # needs room for two corners and a rail; at this width there is
            # nothing left to stretch, which is check 13.
            panel.add(EU.C(name, w, h, layers=[
                {"path": "ui/skins/default/1x1_blank_white.png",
                 "offset": (0, 0), "dw": 0, "dh": 0, "margin": 0,
                 "colour": "#6A5A3CFF", "dock": None}]))
        elif name == "ic_leader_port":
            # A FACE, NOT A LABEL. Without this branch it fell through to the
            # text cell at the bottom of the chain, which carries no
            # <componentimages> - so there is no image slot zero, SetImagePath
            # writes into nothing, and the pcall around it eats the error. The
            # cell then draws NOTHING, with every path correct and every other
            # check green. Check 24 below is what stops that being a branch
            # somebody has to remember.
            panel.add(EU.C(name, w, h, layers=FACE_LAYERS,
                           colour_from=FACE_COLOUR_FROM))
        elif name.startswith("ic_wedge_"):
            # NOT INTERACTIVE. A wedge belongs to nobody for longer than one
            # draw; the crest on it carries the tooltip.
            panel.add(EU.C(name, w, h,
                           layers=wedge_layers(int(name[-2:]))))
        elif name.startswith("ic_div_"):
            # IT NEEDS A PICTURE EVEN THOUGH EVERY DRAW REPLACES IT. This
            # branch did not exist and the walls fell through to the text cell
            # at the bottom of this chain, which carries no <componentimages> -
            # so there was no image slot zero, SetImagePath(path, 0) had
            # nothing to write into, and the pcall the draw wraps it in ate the
            # error. Twenty-five walls were created, moved and made visible
            # with nothing on them, and no check here could see it because
            # every check here was about the pictures, which were all present
            # and correct and unreachable.
            #
            # SLICE ONE'S PICTURE, arbitrarily: a wall is re-pointed before it
            # is ever shown. Slice zero has no picture at all, because a wall
            # on the baseline is the frame.
            panel.add(EU.C(name, w, h, layers=[
                {"path": div_path(1), "offset": (0, 0), "dw": 0, "dh": 0,
                 "margin": 0, "colour": None, "dock": None}]))
        elif name.startswith("ic_hsort_"):
            # NO TEXT BLOCK AT ALL. The label above it is the caption; a second
            # one inside a 17x18 box would be a character and a half of clipped
            # font, and EU.C only writes a text block when one is asked for.
            panel.add(EU.C(name, w, h, interactive=True, sound=SORT_SOUND,
                           layers=SORT_LAYERS, hover=SORT_HOVER))
        elif name.startswith("ic_tab_") or name.startswith("ic_help_topic_"):
            # THE SAME TREATMENT AS A TAB, deliberately: it sits on the tab row
            # and it is a button, so it must read as one. A cell that changes the
            # list when clicked but is drawn as a caption is a control nobody
            # finds - the same fault in reverse as a dead button drawn live.
            panel.add(EU.C(name, w, h, interactive=True, sound=OPENER_SOUND,
                           layers=TAB_LAYERS, hover=TAB_HOVER, **TAB_TEXT))
        elif name == "ic_title":
            # ON ITS BANNER, and centred there: the banner's middle is the only
            # part of it with room for a word. See TITLE_ART.
            panel.add(EU.C(name, w, h, layers=TITLE_LAYERS, align="Center",
                           valign="Center", tx="0.00,0.00", ty=TITLE_TY,
                           **style(name)))
        elif name == "ic_influence":
            # ON ITS OWN PLATE, centred. See SEATS_FRAME.
            panel.add(EU.C(name, w, h, layers=SEATS_LAYERS, align="Center",
                           valign="Center", tx="0.00,0.00", ty=LABEL_TY,
                           **style(name)))
        elif name == "ic_close":
            panel.add(EU.C(name, w, h, interactive=True, sound=OPENER_SOUND,
                           layers=CLOSE_LAYERS, hover=CLOSE_HOVER,
                           tooltip="Close"))
        elif name == "ic_help":
            panel.add(EU.C(name, w, h, interactive=True, sound=OPENER_SOUND,
                           layers=HELP_LAYERS, hover=HELP_HOVER,
                           tooltip="How the court works"))
        elif name in ("ic_page_prev", "ic_page_next", "ic_fill", "ic_gov_btn") \
                or name.startswith("ic_act_") and name != "ic_act_hint":
            # THE ACTION BAR WEARS THE PAGER'S PLATE: same row, same height,
            # and a button beside a button of another shape reads as two bars.
            panel.add(EU.C(name, w, h, interactive=True, sound=OPENER_SOUND,
                           layers=PAGE_LAYERS, hover=PAGE_HOVER, **TAB_TEXT))
        elif name in ("ic_lv_abs", "ic_lv_nay"):
            # OVER ITS OWN PART OF THE BAR (author, 2026-10-03): nay ends where the
            # bar ends; abstaining is centred, and ICUI.draw_law_bar moves it over
            # the abstaining gap.
            panel.add(EU.C(name, w, h, align="Right" if name == "ic_lv_nay" else "Center",
                           valign="Center", tx="0.00,0.00", ty=LABEL_TY, **style(name)))
        elif name == "ic_act_hint":
            # CENTRED, like the buttons it stands in for: across the grid, or
            # across what the pager leaves when draw_actions moves it there.
            panel.add(EU.C(name, w, h, align="Center", valign="Center",
                           tx="0.00,0.00", ty=LABEL_TY, **style(name)))
        else:
            panel.add(EU.C(name, w, h, align="Left", valign="Center",
                           tx=LABEL_TX, ty=LABEL_TY, **style(name)))
    return root


def _row():
    root = EU.C("root", ROW_W, ROW_H)
    row = root.add(EU.C("derpy_ic_row", ROW_W, ROW_H, layers=ROW_LAYERS))
    for name in sorted(ROW_LAYOUT):
        _x, _y, w, h = ROW_LAYOUT[name]
        # The last cell is the one a player clicks (Assign, Appoint), so it is
        # interactive - and a tooltip can only be reached on an interactive
        # component, which is why it carries a soundcategory too.
        if name in ("ic_row_e", "ic_row_f"):
            row.add(EU.C(name, w, h, interactive=True, sound=OPENER_SOUND,
                         layers=BTN_LAYERS, hover=BTN_HOVER,
                         align="Center", valign="Center",
                         tx="0.00,0.00", ty="0.00,0.00", leading=0,
                         **style(name)))
        elif name == "ic_row_port":
            # Plate behind, face in front. No text: a text block on an image cell
            # draws an empty label over the picture.
            row.add(EU.C(name, w, h, layers=FACE_LAYERS, colour_from=FACE_COLOUR_FROM))
        elif name == "ic_row_crest":
            # ONE layer. The crest is a flag on a row that already has a plate
            # behind its main icon; a second plate here would be a coloured block
            # behind a coloured flag.
            row.add(EU.C(name, w, h, layers=PORT_LAYERS))
        else:
            row.add(EU.C(name, w, h, align="Left", valign="Center",
                         tx=LABEL_TX, ty=LABEL_TY, **style(name)))
    return root


def _gm_full(path, margin=0):
    """One layer filling its component."""
    return {"path": path, "offset": (0, 0), "dw": 0, "dh": 0, "margin": margin, "dock": None}


def _gm_inset(path, px):
    """One layer `px` in from every edge."""
    return {"path": path, "offset": (px, px), "dw": -2 * px, "dh": -2 * px,
            "margin": 0, "dock": None}


def _gm_row():
    root = EU.C("root", GM_ROW_W, GM_ROW_H)
    # THE ROW TAKES THE CLICK AND THE TOOLTIP; its cells take neither, so a
    # click anywhere on it reports the row. Its look is CA's art in layers 0
    # (standard) and 1 (hover), swapped by ICUI.gm_fill_row (plan ruling 6).
    row = root.add(EU.C("derpy_ic_gm_row", GM_ROW_W, GM_ROW_H, interactive=True,
                        sound=OPENER_SOUND,
                        layers=[_gm_full(GM_ROW_ART % "active", (0, 16))],
                        hover=[_gm_full(GM_ROW_ART % "hover", (0, 16))]))
    # IN GM_ROW_LAYOUT'S OWN ORDER, NOT SORTED: children draw as declared, and
    # the crest and badge lie over the face (check_gm_plates).
    for name in GM_ROW_LAYOUT:
        _x, _y, w, h = GM_ROW_LAYOUT[name]
        if name == "ic_gr_face":
            # THE COURT'S OWN FACE STACK (plan ruling 14): plate, face, mask, frame.
            row.add(EU.C(name, w, h, layers=FACE_LAYERS, colour_from=FACE_COLOUR_FROM))
        elif name in ("ic_gr_crest", "ic_gr_badge", "ic_gr_icon"):
            row.add(EU.C(name, w, h, layers=PORT_LAYERS))
        else:
            row.add(EU.C(name, w, h, **style(name, valign="Center")))
    return root


def gm_list_xml():
    """THE CALLBACKS ARE THE WHOLE THING: Listview on the container binds the
    other three, List stacks the box, VSlider and VSliderHandle drag. The names
    are reserved too. gen_guilds_ui.check_scroll_parts() is run over this file.

    EMITTED BY THE GREAT GUILDS' EMITTER, which has shipped this exact list: this
    module's has no clipchildren, layout engine, slider properties or moveable."""
    import gen_guilds_ui as GG
    GE = GG.EU
    root = GE.C("root", GM_LIST_W, GM_LIST_H)
    lst = root.add(GE.C("listview", GM_LIST_W, GM_LIST_H, interactive=True,
                        callbacks=["Listview"]))
    clip = lst.add(GE.C("list_clip", GM_ROW_W, GM_LIST_H, clipchildren=True,
                        relativeresize=True, interactive=True))
    clip.add(GE.C("list_box", GM_ROW_W, 1, interactive=True, callbacks=["List"],
                  docking="Top Left",
                  layoutengine={"type": "List", "sizetocontent": True,
                                "margins": "0.00,0.00", "columns": [GM_ROW_W]}))
    vs = lst.add(GE.C("vslider", GM_SLIDER_W, GM_LIST_H, interactive=True,
                      callbacks=["VSlider"], allowhresize=False,
                      props={"Value": 0, "minValue": 0, "maxValue": GM_LIST_H - GM_HANDLE_H},
                      layers=[{"path": GG.SLIDER_TRACK, "offset": (0, 0), "dw": 0, "dh": 0,
                               "margin": 0, "tile": True, "dock": None}]))
    vs.add(GE.C("handle", GM_SLIDER_W, GM_HANDLE_H, interactive=True,
                callbacks=["VSliderHandle"], allowhresize=False, moveable="Movable XP",
                sound=OPENER_SOUND,
                props={"max_height": GM_LIST_H - GM_HANDLE_H, "min_size": 10},
                layers=[{"path": GG.SLIDER_HANDLE_UNDER, "offset": (0, 0), "dw": 0,
                         "dh": 0, "margin": 0, "dock": None},
                        {"path": GG.SLIDER_HANDLE, "offset": (0, 0), "dw": 0, "dh": 0,
                         "margin": 0, "dock": None}]))
    GE.assign(root, GUID_PREFIXES[GM_LIST_FILE])
    return GE.layout(root, "The Iron Court - the Governors column's scrolling list")


def _gm_sp():
    """ONE EMPTY ROW: no image, no text, no children, and not interactive, so the
    mouse goes through it to the card above (docs/CUSTOM_UI.md: a row in a list
    must have no children)."""
    root = EU.C("root", GM_ROW_W, GM_ROW_PITCH)
    root.add(EU.C("derpy_ic_gm_sp", GM_ROW_W, GM_ROW_PITCH))
    return root


def _plot():
    root = EU.C("root", PLOT_W, PLOT_H)
    card = root.add(EU.C("derpy_ic_plot", PLOT_W, PLOT_H, layers=CARD_LAYERS))
    for name in sorted(PLOT_LAYOUT):
        _x, _y, w, h = PLOT_LAYOUT[name]
        if name == "ic_plot_icon":
            # ONE IMAGE LAYER, and it must exist in the file: a component with no
            # componentimages has no image slot at all, so SetImagePath writes
            # nowhere and the pcall around it hides that - it draws NOTHING, not
            # even a blank square. The path here is only the default; the Lua
            # sets each card's own from IC.PLOTS[i].icon.
            card.add(EU.C(name, w, h, layers=PORT_LAYERS))
        elif name == "ic_plot_go":
            # The one cell a player clicks, so interactive - and a tooltip can
            # only be reached on an interactive component, which is why it
            # carries a soundcategory too. Same shape as ic_row_e.
            card.add(EU.C(name, w, h, interactive=True, sound=OPENER_SOUND,
                          layers=BTN_LAYERS, hover=BTN_HOVER,
                          align="Center", valign="Center",
                          tx="0.00,0.00", ty="0.00,0.00", leading=0,
                          **style(name)))
        else:
            card.add(EU.C(name, w, h, align="Left", valign="Center",
                          tx=LABEL_TX, ty=LABEL_TY, **style(name)))
    return root


def _card():
    root = EU.C("root", CARD_W, CARD_H)
    card = root.add(EU.C("derpy_ic_card", CARD_W, CARD_H, layers=OFFICE_CARD_LAYERS))
    for name in sorted(CARD_LAYOUT):
        _x, _y, w, h = CARD_LAYOUT[name]
        if name == "ic_card_button":
            card.add(EU.C(name, w, h, interactive=True, sound=OPENER_SOUND,
                          layers=BTN_LAYERS, hover=BTN_HOVER,
                          align="Center", valign="Center",
                          tx="0.00,0.00", ty="0.00,0.00", leading=0,
                          **style(name)))
        elif name == "ic_card_port":
            card.add(EU.C(name, w, h, layers=FACE_LAYERS, colour_from=FACE_COLOUR_FROM))
        elif name == "ic_card_crest":
            card.add(EU.C(name, w, h, layers=PORT_LAYERS))
        else:
            # NEVER SPLIT, which is the default and the only one of CA's three
            # values that keeps a label on one line. "Resize" was tried and it
            # WRAPS - a 27-character name in a component declaring width="304"
            # came out one word per line, drawing down across every cell under
            # it. Fitting is the layout's job, not the engine's: check 20c
            # below measures every string this card can draw.
            card.add(EU.C(name, w, h, align="Left", valign="Center",
                          tx=LABEL_TX, ty=LABEL_TY, **style(name)))
    return root


# THE CHOSEN PARTY WEARS A GOLD FRAME. CA's own selected unit card frame from
# the gunnery school, read out of ui2.pack: 100x185, 9px rails, and corner
# ornaments that reach 24px in - so 24 is the margin, measured, the way
# TEXTURE_MIN_MARGIN's other two were.
#
# A THIRD LAYER, SWAPPED, and not a state. ICUI.fill_party writes the frame into
# slot PARTY_SEL_INDEX on the chosen card and MASK_NONE - our own transparent
# png - into it on every other, the same trick set_vacant_plate plays on a face.
# The file ships the transparent one, so a card nobody has chosen draws as it
# always did.
PARTY_SELECTED = "ui/skins/default/dlc25_gunnery_school/frame_unit_card_selected.png"
TEXTURE_MIN_MARGIN[PARTY_SELECTED] = 24
PARTY_SEL_INDEX = 2
# THE CHOSEN CARD BREATHES (2026-10-04): CA puts glow_pulse_t0 on what a panel
# has selected - the Skull Throne's chosen ritual plate, the Hell-Forge's lit
# torch - and the seat rim's ToZ furnace values are already this panel's breath.
SELECTED_PULSE = {"shader": "glow_pulse_t0", "shader_vars": RIM_LOOKS["lit"]["shader_vars"]}
PARTY_LAYERS = CARD_LAYERS + [
    dict({"path": MASK_NONE, "offset": (0, 0), "dw": 0, "dh": 0,
          "margin": TEXTURE_MIN_MARGIN[PARTY_SELECTED], "dock": None}, **SELECTED_PULSE)
] + rim_layers(["lit", "fail"])
# The flash's two looks, after the chosen frame. Must match ICUI.RIMS.party.
PARTY_RIM = {"lit": PARTY_SEL_INDEX + 1, "fail": PARTY_SEL_INDEX + 2}
# THE WHOLE CARD IS THE CONTROL NOW, so it says what a click does. Static text
# in the file rather than a SetTooltipText, because it never changes.
PARTY_TIP = ("Choose this party||Click once to act on it with the buttons "
             "under the cards. Click it again to see who belongs to it.")


def _party():
    root = EU.C("root", PARTY_W, PARTY_H)
    card = root.add(EU.C("derpy_ic_party", PARTY_W, PARTY_H, layers=PARTY_LAYERS,
                         interactive=True, sound=OPENER_SOUND,
                         tooltip=PARTY_TIP))
    for name in sorted(PARTY_LAYOUT):
        _x, _y, w, h = PARTY_LAYOUT[name]
        if name in ("ic_party_state", "ic_party_members", "ic_party_offices",
                    "ic_party_govs"):
            # RIGHT-ALIGNED, so the word ends where the card's content ends
            # and a short name's second line leaves a gap, not a collision.
            # THE THREE COUNTS TOO: left-aligned they began 3px after the
            # longest trait at 1600 and read as one run of words.
            card.add(EU.C(name, w, h, align="Right", valign="Center",
                          tx="0.00,0.00", ty=LABEL_TY, **style(name)))
        elif name == "ic_party_port":
            card.add(EU.C(name, w, h, layers=FACE_LAYERS,
                          colour_from=FACE_COLOUR_FROM))
        elif name == "ic_party_crest":
            # ONE layer, as the row's crest is: a flag over a plate is a
            # coloured block behind a coloured flag.
            card.add(EU.C(name, w, h, layers=PORT_LAYERS))
        else:
            card.add(EU.C(name, w, h, align="Left", valign="Center",
                          tx=LABEL_TX, ty=LABEL_TY, **style(name)))
    return root


# THE LAW CARD (spec 2026-10-02 laws section 4.1): the card plate, then two
# swapped slots - LAW_GLOW_INDEX the chosen card's red row art, LAW_SEL_INDEX
# the gold frame on the law in force - each MASK_NONE until the Lua paints it,
# the trick PARTY_LAYERS plays with PARTY_SELECTED.
LAW_GLOW = GM_ROW_ART % "selected"
LAW_GLOW_INDEX = len(CARD_LAYERS)
LAW_SEL_INDEX = LAW_GLOW_INDEX + 1
LAW_LAYERS = CARD_LAYERS + [
    # THE CHOSEN CARD BREATHES; THE LAW IN FORCE DOES NOT. Four laws are always
    # in force, and four frames breathing at once is noise, not a signal.
    dict({"path": MASK_NONE, "offset": (0, 0), "dw": 0, "dh": 0, "margin": (0, 16),
          "dock": None}, **SELECTED_PULSE),
    {"path": MASK_NONE, "offset": (0, 0), "dw": 0, "dh": 0,
     "margin": TEXTURE_MIN_MARGIN[PARTY_SELECTED], "dock": None}]
LAW_TIP = ("Choose this law||Click to read it on the right, and to propose it "
           "or go to its vote.")


def _law():
    root = EU.C("root", LAW_W, LAW_H)
    card = root.add(EU.C("derpy_ic_law", LAW_W, LAW_H, layers=LAW_LAYERS,
                         interactive=True, sound=OPENER_SOUND, tooltip=LAW_TIP))
    for name in sorted(LAW_LAYOUT):
        _x, _y, w, h = LAW_LAYOUT[name]
        if name == "ic_law_icon":
            card.add(EU.C(name, w, h, layers=PORT_LAYERS))
        elif name == "ic_law_mark":
            card.add(EU.C(name, w, h, layers=MARK_LAYERS))
        else:
            card.add(EU.C(name, w, h, align="Left", valign="Center",
                          tx=LABEL_TX, ty=LABEL_TY, **style(name)))
    return root


# THE PARTY BLOCK (spec section 4.2): no plate of its own, it sits on its side.
def _lawblock():
    root = EU.C("root", LB_W, LB_H)
    block = root.add(EU.C("derpy_ic_lawblock", LB_W, LB_H))
    for name in sorted(LB_LAYOUT):
        _x, _y, w, h = LB_LAYOUT[name]
        if name == "ic_lb_crest" or name.startswith("ic_lb_face_"):
            block.add(EU.C(name, w, h, layers=FACE_LAYERS, colour_from=FACE_COLOUR_FROM))
        elif name.startswith("ic_lb_pip_"):
            block.add(EU.C(name, w, h, layers=PORT_LAYERS))
        elif name.startswith("ic_lb_win_"):
            block.add(EU.C(name, w, h, interactive=True, sound=OPENER_SOUND,
                           layers=plate(h, "active"), hover=plate(h, "hover"),
                           align="Center", valign="Center", tx="0.00,0.00",
                           ty="0.00,0.00", leading=0, **style(name)))
        elif name in ("ic_lb_total",):
            block.add(EU.C(name, w, h, align="Right", valign="Center",
                           tx="0.00,0.00", ty=LABEL_TY, **style(name)))
        else:
            block.add(EU.C(name, w, h, align="Left", valign="Center",
                           tx=LABEL_TX, ty=LABEL_TY, **style(name)))
    return root


def _opener():
    root = EU.C("root", OPENER_W, OPENER_H)
    # STATIC TOOLTIP, not a runtime SetTooltipText. place_opener is re-entered
    # from FactionTurnStart, and resolving a localised string inside a turn
    # handler is a turn-1 CTD that pcall does not catch - so the one route
    # that costs no call at all is the right one. CA Title||Body split,
    # literal text on both sides because a bare loc key draws the pipes.
    root.add(EU.C("derpy_ic_opener", OPENER_W, OPENER_H, interactive=True,
                  sound=OPENER_SOUND, layers=OPENER_LAYERS, hover=OPENER_HOVER,
                  tooltip=OPENER_TIP))
    return root


# THE STANDING PLATE, which rides on CA's character details panel.
#
# CREATED ON THE UI ROOT, never parented into CA's panel: a layout group owns its
# children's positions and MoveTo never gets to have the fight - the same lesson
# the opener is built around. It is anchored by READING a CA component's settled
# position at runtime rather than by any offset written down here, so nothing in
# this file has to know what CA's panel looks like.
#
# ON THE HELL-FORGE PLATE the court panel's own "137 influence" sits on
# (SEATS_LAYERS), 26 tall like ic_influence: one figure, one look. It was CA's
# ROUND button underlay pulled to 190x22 - a squashed ellipse (author,
# 2026-09-28: "the influence in the character has the background stretched
# out"). Text LEFT: ICUI.fit_words sizes the plate to its words at runtime and
# holds them in with SetTextXOffset. STANDING_W is only the widest it gets.
STANDING_W, STANDING_H = 190, 26
STANDING_LAYERS = SEATS_LAYERS


def _standing():
    root = EU.C("root", STANDING_W, STANDING_H)
    # NOT interactive. It is a readout sitting over somebody else's panel, and an
    # interactive component there would eat clicks meant for CA's own buttons.
    root.add(EU.C("derpy_ic_standing", STANDING_W, STANDING_H,
                  layers=STANDING_LAYERS,
                  **style("derpy_ic_standing", align="Left", valign="Center",
                          tx="0.00,0.00", ty=LABEL_TY)))
    return root


# THE EDICT NOTE (author, 2026-09-28: "no warning or feedback that it needs a
# governor", then "the ui is not good" of the first one, which borrowed the
# standing plate and drew bare letters on the HUD's trim). The seats counter's
# own plate, the Hell-Forge's sub_title.png at its native 30px height, text
# LEFT: ICUI.edict_note sizes it to its words' WidthOfTextLine plus a tenth and
# holds them that far in with SetTextXOffset, so centring never moves them. It
# makes it a child of CA's edict stack and MoveTo's it against the frame.
EDICT_NOTE_W, EDICT_NOTE_H = 190, 30


def _edict_note():
    root = EU.C("root", EDICT_NOTE_W, EDICT_NOTE_H)
    # NOT interactive, like the standing plate: it sits in CA's HUD and must
    # not eat a click meant for an edict.
    root.add(EU.C("derpy_ic_edict_note", EDICT_NOTE_W, EDICT_NOTE_H,
                  layers=SEATS_LAYERS,
                  **style("derpy_ic_edict_note", align="Left", valign="Center",
                          tx="0.00,0.00", ty=LABEL_TY)))
    return root


FILES = [
    ("derpy_ic_panel.twui.xml", _panel, "The Iron Court - panel frame, tabs, standing bar"),
    ("derpy_ic_card.twui.xml", _card, "The Iron Court - one office slot"),
    ("derpy_ic_row.twui.xml", _row, "The Iron Court - one house, province or feed row"),
    ("derpy_ic_party.twui.xml", _party,
     "The Iron Court - one party: its name, its leader's face and its traits"),
    ("derpy_ic_plot.twui.xml", _plot,
     "The Iron Court - one intrigue move: its name, what it does, its price"),
    ("derpy_ic_opener.twui.xml", _opener, "The Iron Court - HUD opener button"),
    ("derpy_ic_standing.twui.xml", _standing,
     "The Iron Court - a courtier's standing, over CA's character panel"),
    ("derpy_ic_edict_note.twui.xml", _edict_note,
     "The Iron Court - why a province's edicts are grey, beside CA's edict stack"),
    (GM_ROW_FILE, _gm_row, "The Iron Court - one row of the Governors view's column"),
    (GM_SP_FILE, _gm_sp, "The Iron Court - an empty row that gives the list its length"),
    ("derpy_ic_law.twui.xml", _law, "The Iron Court - one law card"),
    ("derpy_ic_lawblock.twui.xml", _lawblock, "The Iron Court - one party on a vote"),
]

LAYOUT_TABLES = {
    "derpy_ic_panel.twui.xml": PANEL_LAYOUT,
    "derpy_ic_card.twui.xml": CARD_LAYOUT,
    "derpy_ic_row.twui.xml": ROW_LAYOUT,
    "derpy_ic_party.twui.xml": PARTY_LAYOUT,
    "derpy_ic_plot.twui.xml": PLOT_LAYOUT,
    "derpy_ic_law.twui.xml": LAW_LAYOUT,
    "derpy_ic_lawblock.twui.xml": LB_LAYOUT,
    "derpy_ic_opener.twui.xml": {"derpy_ic_opener": (0, 0, OPENER_W, OPENER_H)},
    "derpy_ic_standing.twui.xml": {
        "derpy_ic_standing": (0, 0, STANDING_W, STANDING_H)},
    "derpy_ic_edict_note.twui.xml": {
        "derpy_ic_edict_note": (0, 0, EDICT_NOTE_W, EDICT_NOTE_H)},
    # PLACED BY ICUI.card_fire, not by a layout table: the emitter is MoveTo'd
    # to its card's bottom edge on every draw. Named here so check 7 knows it.
    "derpy_ic_fire.twui.xml": {"derpy_ic_fire": (0, 0, 0, 0), "embers": (0, 0, 0, 0),
                               "template_particle": (0, 0, 0, 0)},
    # PLACED BY ICUI.burst over its card or row, and destroyed after it plays.
    "derpy_ic_burst.twui.xml": {"derpy_ic_burst": (0, 0, 0, 0)},
}
LAYOUT_TABLES[GM_ROW_FILE] = dict(GM_ROW_LAYOUT, derpy_ic_gm_row=(0, 0, GM_ROW_W, GM_ROW_H))
# list_box and handle are NOT here: the List and VSlider callbacks own where
# those sit, and gen_guilds_ui refuses either name in a placement table.
LAYOUT_TABLES[GM_LIST_FILE] = {
    "listview": (0, 0, GM_LIST_W, GM_LIST_H),
    "list_clip": (0, 0, GM_ROW_W, GM_LIST_H),
    "vslider": (GM_ROW_W + GM_SLIDER_GAP, 0, GM_SLIDER_W, GM_LIST_H),
}
LAYOUT_TABLES[GM_SP_FILE] = {"derpy_ic_gm_sp": (0, 0, GM_ROW_W, GM_ROW_PITCH)}


# ---------------------------------------------------------------------------
# THE SCALE PASS. Everything above is typed for a 1920 box; at_box(bw) runs it
# again with every layout number rewritten the way ICUI.apply_scale rewrites the
# Lua's copy at open. The two sides must land on the same pixels, and
# import_iron_court.py runs the Lua to prove it:
#   * a lone number is sc(v);
#   * a box is scaled by its EDGES (sc_box), so cells that touch still touch;
#   * the three card grids scale PER POINT (SCALED_GRIDS, and plot_grid's
#     base points), because that is what ICUI.apply_scale does - never rebuilt
#     from the scaled card size;
#   * below 1920 every font steps down one CA size - the compact copies of the
#     panel files are built from this module at 1600.
# ---------------------------------------------------------------------------
COMPACT_FONTS = {
    "header_24_bold": (20, "header_20_bold"),
    "header_20_bold": (18, "header_18_bold"),
    "header_18_bold": (16, "header_16_bold"),
    "header_18": (16, "header_16"),
    "header_16": (14, "header_14"),
    "body_12": (10, "body_10"),
}

# PER-CELL CORRECTIONS AT THE SMALL END, in screen pixels at a 1600 box: text
# shrinks by one size step (about 11%) while boxes shrink 17%, so a cell that fit
# at 1920 with little slack can clip at 1600. Faded by _override(): all of it at
# 1600, none at 1920 and above. Every entry names the string that forced it.
# A cell takes (dx, dy, dw, dh); a scaled number takes one delta. A delta on a
# card size (CARD_W) resizes the cards and does NOT move them - the grid points
# scale on their own - so widening one needs its gap narrowed to match, or the
# cards overlap. Measured 2026-09-24 with check() at 1600.
COMPACT_OVERRIDES = {
    # THE GOVERNORS STRIP AND FOOT keep CA's 4px top rail at its own size while
    # their boxes shrink, so the title and the footer line, 4px in at 1920, round
    # onto it at 1600 (check_gm_plates).
    "ic_title": (0, 1, 0, -1),
    "ic_alert": (0, 1, 0, -1),
    # THE OFFICE CARD. "Warden of the Caravan Roads" measures 248px at 14px and
    # needs 254 with its 6px inset; the name had 253. It takes a pixel of the
    # frame band on each side - 24 in from the edge, where the frame's ink
    # stops at 10.
    "ic_card_name": (-1, 0, 2, 0),
    # THE MOVE CARD'S PAD GOES FROM 25 TO 20. Three blurbs need a 337px line
    # to fit four lines at 16px ("-90 influence for him. -8 influence from his
    # party..." is the widest) and the card had 327. The frame's ink reaches
    # at most 10px in from an edge, so 20 is still 10px clear of it. The
    # icon, the name, the price and the button move with the blurbs so the card
    # keeps one left edge and one right edge.
    "ic_plot_icon": (-5, 0, 0, 0),
    "ic_plot_name": (-5, 0, 10, 0),
    "ic_plot_b1": (-5, 0, 10, 0),
    "ic_plot_b2": (-5, 0, 10, 0),
    "ic_plot_b3": (-5, 0, 10, 0),
    "ic_plot_b4": (-5, 0, 10, 0),
    "ic_plot_cost": (-5, 0, 0, 0),
    "ic_plot_go": (5, 0, 0, 0),
    # THE LIST ROW, re-dealt as one. The character column: "Retainer Sisuthrus
    # Burrdrik, Temple Acolyte" measures 412px and needs 424 with its inset
    # both sides; it had 418. The crest after it starts 1px past the new edge.
    "ic_row_a": (0, 0, 6, 0),
    # The influence column: "1722 influence - Grand Overseer of the Forge"
    # measures 419px and needs 432; it had 408. It can start only 4px earlier,
    # because the Rank heading's sort arrow ends at 985 and this column's
    # heading must sit over it; the rest comes from the 17px gap before the
    # button column, which moves 7px right to leave 4.
    "ic_row_d": (-4, 0, 24, 0),
    "ic_hdr_d": (-4, 0, 0, 0),
    "ic_hsort_d": (-4, 0, 0, 0),
    # The button column. "Available" and its arrow ran 1px past the row's
    # right edge, so it is 2px wider as well as 7px further right; it still
    # ends 4px inside the row.
    "ic_row_e": (7, 0, 2, 0),
    "ic_hdr_e": (7, 0, 0, 0),
    "ic_hsort_e": (7, 0, 0, 0),
}

# How far above a card's bottom edge the embers start (see
# FIRE_FILE). Here, not with it, because the scale pass below runs first. ICUI.FIRE_LIFT is the
# same number; import_iron_court compares the two at every box width.
FIRE_LIFT = 10

SCALED_SCALARS = [
    "PANEL_W", "PANEL_H", "CONTENT_W", "ROWS_X", "ROWS_Y", "ROW_PITCH", "HDR_GAP",
    "HDR_Y", "COL_TOP", "COL_GUTTER", "DIVIDER_W", "CROWN_RULE_W", "COL_W", "COL_L_X", "COL_R_X",
    "COL_HDR_H", "COL_BODY_Y", "COL_BOTTOM", "RIM_PAD", "DIAL_CX", "DIAL_PAD_X",
    "DIAL_PAD_TOP", "DIAL_PAD_BOT", "DIAL_R", "DIAL_CY", "CREST_R", "CREST_PX",
    "SHARE_R", "SHARE_W", "SHARE_H", "CROWN_Y", "CROWN_BAND", "_CROWN_X",
    "_CONTROL_W", "_CROWN_Y0", "_CROWN_GAP", "_CROWN_LEFT_W", "_CROWN_RIGHT_X",
    "_CROWN_RIGHT_W", "_LEADER_Y", "_PORT_W", "_PORT_H", "_LEADER_ROW_Y",
    "_LEADER_TX", "_LEADER_TW", "_LEADER_BOTTOM", "_FX_Y", "_CTL_H", "CROWN_H",
    "_CTL_Y", "_LEFT_BOTTOM", "_GOV_Y", "GOV_BTN_W", "_GOV_BOTTOM",
    "ROW_W", "ROW_H", "CARDS_X", "CARDS_Y", "CARD_GAP_X", "CARD_GAP_Y", "CARD_W",
    "CARD_H", "PLOTS_X", "PLOTS_HDR_Y", "PLOTS_HDR_H", "PLOTS_Y", "PLOT_W", "PLOT_H",
    "PLOT_PAD", "PLOT_INNER_W", "PLOT_ICON_PX", "PLOT_FOOT_PAD", "PARTY_GAP_X",
    "PARTY_GAP_Y", "PARTY_W", "PARTIES_X", "PARTIES_Y", "PARTY_H", "PARTY_BAND",
    "_PIW", "_PB", "_PPW", "_PPH", "_PTX", "_PTW", "_PLW", "_PRX", "_PRW", "_PSW",
    "ACT_GAP", "FIRE_LIFT",
    "GM_ROW_X", "GM_ROW_Y", "GM_ROW_W", "GM_ROW_H", "GM_ROW_PITCH",
    "GM_SLIDER_W", "GM_SLIDER_GAP", "GM_HANDLE_H", "GM_LIST_W", "GM_LIST_H",
    "LAW_W", "LAW_H", "LAWS_X", "LAWS_Y", "LAW_GAP_X", "LAW_GAP_Y", "LAW_PBAR_H",
    "LB_W", "LB_H", "LB_X", "LB_Y", "LB_SIDE_DX", "LB_GAP",
]
SCALED_PAIRS = ["PORT_BOX", "CREST_BOX"]
SCALED_BOXES = ["PIE_BOX", "RIM_BOX", "DIAL_BOX", "COURT_SECTION_XY"]
SCALED_BOX_TABLES = ["PANEL_LAYOUT", "ROW_LAYOUT", "PLOT_LAYOUT", "CARD_LAYOUT",
                     "PARTY_LAYOUT", "ACT_PAGED", "GM_ROW_LAYOUT", "LAW_LAYOUT",
                     "LB_LAYOUT"]
# PER POINT, not rebuilt from the scaled card size: a card size rounded down
# once and multiplied by five ran a tier 2-4px past its column at some widths.
SCALED_GRIDS = ["CARD_GRID", "PARTY_GRID", "LAW_GRID", "LB_GRID"]
FONT_GLOBALS = ["TITLE", "BODY", "PANEL_TITLE", "COL_HDR_FONT", "TEXT_STYLE",
                "TAB_TEXT"]
# NOT GEOMETRY: counts, source-art sizes, the art generators' own numbers, the
# image layers INSIDE a component (the engine stretches those with their box),
# the HUD opener and the influence plate, and LAYOUT_TABLES, which only names
# tables scaled under their own names.
NOT_GEOMETRY = [
    "PORTHOLE_W", "PORTHOLE_H", "MAX_HOUSES", "OFFICE_COUNT", "DIAL_SLICES",
    "CARD_TIERS", "CARD_WIDEST", "PLOT_COUNTS", "PLOT_COLS", "PLOT_DEPTH",
    "PLOT_BLURB_LINES", "VISIBLE_ROWS", "PARTY_COLS", "PARTY_ROWS", "PARTY_SLOTS",
    "OPENER_W", "OPENER_H", "STANDING_W", "STANDING_H", "EDICT_NOTE_W", "EDICT_NOTE_H", "LAYOUT_TABLES",
    "FX_KEYS", "CROWN_CELLS", "GM_ROW_ART_H", "GM_COL_ART_W", "GM_COL_ART_H", "GM_HEAD_ART_H", "GM_ROW_RAIL", "GM_PLATE_RAIL", "GM_PLATE_MARGIN",
    "PANEL_LAYERS", "ROW_LAYERS", "CARD_LAYERS", "PORT_LAYERS", "CARD_PORT_LAYERS",
    "FACE_LAYERS", "OPENER_LAYERS", "CLOSE_LAYERS", "CLOSE_HOVER", "HELP_LAYERS", "HELP_HOVER", "HELP_ICON", "HELP_SLOTS", "OPENER_HOVER",
    "BTN_LAYERS", "BTN_HOVER", "PAGE_LAYERS", "PAGE_HOVER", "SORT_LAYERS",
    "SORT_HOVER", "STANDING_LAYERS", "BORDER_CORNER", "TEXTURE_MIN_MARGIN",
    "PLATE_W", "PLATE_H", "PLATE_BASE", "SIGIL", "FLAG_WHITE", "FLAG_CLEAR",
    "SIGIL_FINE", "SIGIL_HALO", "SIGIL_EDGE", "SIGIL_LIT", "SIGIL_SHADE", "SIL_INK",
    "SIL_RIM", "SIL_RIM_PX", "SIL_ALPHA", "SIL_MIN_STEP", "RIM_TOP", "RIM_SIDE",
    "RIM_BOTTOM", "RIM_EDGE_A", "RIM_SHADOW", "RIM_W", "RIM_SS", "EMBER",
    "EMBER_DEPTH", "DIV_W", "DIV_EDGE_A", "DIV_SS", "PLATE_INDEX", "FACE_INDEX",
    "MASK_INDEX", "FRAME_INDEX", "FRAME_ART", "FRAME_MARGIN", "FRAME_OUT", "FRAME_PX",
    "FRAME_BAND", "FRAME_BRONZE", "FACE_COLOUR_FROM", "OPENER_ICON_INSET", "CLOSE_INSET", "TAB_H",
    "TAB_LAYERS", "TAB_HOVER", "TAB_CAP", "TAB_TEXT_INSET", "TITLE_LAYERS",
    "TITLE_CAP", "TITLE_TY", "PLATE_GAP", "FIT_PLATES", "HEADER_LAYERS", "HEADING_ART", "HEADING_CAP", "HEADING_TY", "HEADING_H",
    # Crop boxes in CA's source pixels, not layout.
    "CHD_CUTS",
    "BTN_PLATE_MARGIN", "PARTY_LAYERS", "PARTY_SEL_INDEX", "SEATS_LAYERS",
    "PETITION_BTN_CELL",
    "RIM_ART", "RIM_MARGIN", "RIM_FAIL_ART", "RIM_FAIL_RGB", "RIM_LOOKS", "RIM_PX", "RIM_RGB", "RIM_ALPHA", "PARTY_RIM", "MARK_LAYERS", "OFFICE_CARD_LAYERS", "CARD_RIM",
    "BURST_FILE", "BURST_FRAMES", "BURST_LAST", "BURST_MS", "BURST_SIZE",
    "MAP_RING", "MAP_RING_CAPITAL",
    "MAP_RING_OUTLINE", "MAP_RING_CAPITAL_COLOUR", "MAP_RING_OUTLINE_COLOUR",
    "MAP_PIN",
    "SEATS_PAD",
    "GM_PIN_FILE", "GM_FACE_FILE", "GM_PIN_W", "GM_PIN_H", "GM_PIN_ART", "GM_PIN_ART_BOX",
    "GM_HEAD", "GM_RING", "GM_RING_OUTER", "GM_PLATE", "GM_PORT_BOX",
    "GM_FACE_GROUND", "GM_FACE_GROUND_COLOUR", "GM_MASK", "GM_PIN_LAYERS", "GM_FACE_LAYERS",
    "GM_PLATE_CAP", "GM_NAME_W", "GM_ANCHOR", "_GM_CX",
    "GM_NAME_FILE", "GM_LOYAL_FILE", "GM_PLATE_H", "GM_PLATE_GAP", "GM_LOYAL_W",
    "GM_LOYAL_H", "GM_NAME_PLATE_Y", "GM_NAME_H", "GM_NAME_PLATE_BOX", "GM_WASH_BOX",
    "GM_WASH_LUM", "GM_INK", "GM_NAME_LAYERS", "GM_BADGE_FILE", "GM_BADGE_BOX",
    "GM_BADGE_LAYERS",
    "GM_ROW_FILE", "GM_ROWS", "GM_HF", "GM_ROW_ART", "GM_COL_ART", "GM_HEAD_ART",
    "GM_TOG_LABEL_ART", "GM_ROUND", "GM_TOG_ICONS", "GM_PLATES",
    # The action bar's 1920 widths. PANEL_LAYOUT is what scales; these only
    # built it.
    "ACT_BUTTONS",
    # The fill button's 1920 width, the same: it built PANEL_LAYOUT["ic_fill"].
    "FILL_W",
    # The ziggurat's art: ziggurat_pixels builds it at 1920, and its box scales.
    "ZIG_PAD_X", "ZIG_PAD_Y", "ZIG_FILL", "ZIG_RIM", "ZIG_RIM_PX", "ZIG_SHRINE",
    "_i",       # the move-category heading loop's counter, left behind by it
    # THE LAWS TAB: counts, and the card's swapped slots.
    "LAW_COLS", "LAW_ROWS", "LAW_LINES", "LAW_SEGS", "LB_PER_SIDE", "LB_MEN",
    "GOV_CARDS", "GC_RULE_LINES", "GC_LOY_LINES", "GOV_ART_PX", "LAW_PBAR_COLOUR",
    "LAW_PBAR_RIM_BAND", "LAW_PBAR_RIM_OUT", "LAW_PBAR_RIM_PX",
    "LAW_LAYERS", "LAW_GLOW_INDEX", "LAW_SEL_INDEX",
    "FRAME_INK",
]


def _intish(v, depth=0):
    if isinstance(v, bool):
        return False
    if isinstance(v, int):
        return True
    if depth > 3:
        return False
    if isinstance(v, (list, tuple, set, frozenset)):
        return any(_intish(e, depth + 1) for e in v)
    if isinstance(v, dict):
        return any(_intish(e, depth + 1) for e in v.values())
    return False


def _classify(g):
    """Refuse on a layout number the scale pass does not know about.

    A value missing from every list keeps its 1920 size on a 1600 screen, with
    every check green, because every check reads the same unscaled number.
    """
    known = set(SCALED_SCALARS + SCALED_PAIRS + SCALED_BOXES + SCALED_BOX_TABLES
                + list(SCALED_GRIDS) + FONT_GLOBALS + NOT_GEOMETRY
                + ["BOX_W", "_BOX_W", "COMPACT", "COMPACT_FONTS",
                   "COMPACT_OVERRIDES"])
    loose = sorted(n for n, v in g.items()
                   if not n.startswith("__") and n not in known and _intish(v)
                   and not callable(v) and not isinstance(v, type(os)))
    assert not loose, ("layout numbers neither scaled nor declared NOT_GEOMETRY: %s"
                       % ", ".join(loose))


def _override(d, bw):
    """An override's share at box bw: all of it at 1600, none from 1920."""
    return (d * (1920 - bw) + 160) // 320 if bw < 1920 else 0


def _font(pair):
    return COMPACT_FONTS[pair[1]]


def _scale_pass(g, bw):
    _classify(g)
    # AN OVERRIDE FOR A NAME THAT DOES NOT EXIST IS A REFUSAL, not a no-op: a
    # cell renamed after its override was written would silently lose it.
    cells = set()
    for n in SCALED_BOX_TABLES:
        cells.update(g[n])
    for name, d in COMPACT_OVERRIDES.items():
        if name in SCALED_SCALARS:
            assert isinstance(d, int), "%s: a number takes one delta" % name
        else:
            assert name in cells, "override for %s, which no layout table holds" % name
            assert len(d) == 4, "%s: a cell takes (dx, dy, dw, dh)" % name
    # BEFORE any number is scaled: plot_grid() reads PLOTS_X and PLOT_W live.
    base_plots = g["plot_grid"]()
    for n in SCALED_SCALARS:
        g[n] = sc(g[n], bw) + _override(COMPACT_OVERRIDES.get(n, 0), bw)
    for n in SCALED_PAIRS:
        g[n] = tuple(sc(v, bw) for v in g[n])
    for n in SCALED_BOXES:
        g[n] = sc_box(g[n], bw)
    for n in SCALED_BOX_TABLES:
        table = g[n]
        for name in list(table):
            x, y, w, h = sc_box(table[name], bw)
            d = COMPACT_OVERRIDES.get(name, (0, 0, 0, 0))
            table[name] = (x + _override(d[0], bw), y + _override(d[1], bw),
                           w + _override(d[2], bw), h + _override(d[3], bw))
    for n in SCALED_GRIDS:
        g[n][:] = [(sc(x, bw), sc(y, bw)) for x, y in g[n]]
    # plot_grid() derives the move cards from PLOTS_X and PLOT_W, so a copy at
    # another box answers with the base grid scaled per point instead, which is
    # what ICUI.PLOT_XY holds in game.
    _plots = [(sc(x, bw), sc(y, bw)) for x, y in base_plots]

    def _scaled_plot_grid(counts=None):
        assert counts is None, "a scaled copy has only its own court's grid"
        return list(_plots)
    g["plot_grid"] = _scaled_plot_grid
    if bw < 1920:
        for n in ("TITLE", "BODY", "PANEL_TITLE", "COL_HDR_FONT"):
            g[n] = _font(g[n])
        for name in list(g["TEXT_STYLE"]):
            g["TEXT_STYLE"][name] = _font(g["TEXT_STYLE"][name])
        g["TAB_TEXT"]["size"], g["TAB_TEXT"]["fontcat"] = _font(
            (g["TAB_TEXT"]["size"], g["TAB_TEXT"]["fontcat"]))


# HOW FAR THE CARD FRAME'S INK REACHES IN FROM AN EDGE, measured 2026-09-24 off
# panel_back_border.png: 10px, at the corner curl. The sweep holds every card
# cell 2px clear of it at every box width; check() holds the design band at the
# three sizes it runs at.
FRAME_INK = 10


def check_scale_sweep():
    """Geometry at EVERY box width from 1600 to 2560, one pixel at a time.

    check() runs at 1600, 1920 and 2560. Between them the scaled edges are
    monotone and the overrides fade in a straight line, but integer rounding is
    not a straight line, so this walks every width rather than trusting that. It
    reports the first width each rule fails at, and allows the one pixel that
    rounding a scaled edge can move.
    """
    assert BOX_W == 1920, "the sweep reads the base layout"
    out, seen = [], set()

    def fail(rule, bw, msg):
        if rule not in seen:
            seen.add(rule)
            out.append("at box %d: %s" % (bw, msg))

    def num(n, bw):
        return sc(globals()[n], bw) + _override(COMPACT_OVERRIDES.get(n, 0), bw)

    def cells(table, bw):
        got = {}
        for name, box in table.items():
            x, y, w, h = sc_box(box, bw)
            d = COMPACT_OVERRIDES.get(name, (0, 0, 0, 0))
            got[name] = (x + _override(d[0], bw), y + _override(d[1], bw),
                         w + _override(d[2], bw), h + _override(d[3], bw))
        return got

    def apart(a, b):
        return (a[0] + a[2] <= b[0] or b[0] + b[2] <= a[0]
                or a[1] + a[3] <= b[1] or b[1] + b[3] <= a[1])

    def margins(box, fw, fh):
        x, y, w, h = box
        return (x, y, fw - x - w, fh - y - h)

    looped = ("ic_wedge_", "ic_div_", "ic_barc_", "ic_barp_")
    frames = [("panel", {n: b for n, b in PANEL_LAYOUT.items()
                         if not n.startswith(looped)}, None),
              ("row", ROW_LAYOUT, ("ROW_W", "ROW_H")),
              ("office card", CARD_LAYOUT, ("CARD_W", "CARD_H")),
              ("party card", PARTY_LAYOUT, ("PARTY_W", "PARTY_H")),
              ("move card", PLOT_LAYOUT, ("PLOT_W", "PLOT_H"))]

    def frame_size(frame, bw):
        if frame is None:
            return bw, bw * 9 // 16
        return num(frame[0], bw), num(frame[1], bw)

    # THE FLOOR FOR A CELL'S DISTANCE TO ITS FRAME'S EDGE is the smaller of its
    # distances at the two sizes check() has measured, less a pixel. Nothing
    # between them may come closer to the edge than either end does.
    floors, pairs = {}, {}
    for what, table, frame in frames:
        ends = []
        for bw in (1600, 1920):
            fw, fh = frame_size(frame, bw)
            got = cells(table, bw)
            ends.append(dict((n, margins(got[n], fw, fh)) for n in got))
        floors[what] = dict((n, tuple(min(a, b) - 1 for a, b in
                                      zip(ends[0][n], ends[1][n])))
                            for n in table)
        names = sorted(table)
        pairs[what] = [(a, b) for i, a in enumerate(names) for b in names[i + 1:]
                       if apart(table[a], table[b])]

    def span(points, w, h, bw):
        return (min(x for x, _y in points), max(x for x, _y in points) + w,
                max(y for _x, y in points) + h)

    for bw in range(1600, 2561):
        for what, table, frame in frames:
            fw, fh = frame_size(frame, bw)
            got = cells(table, bw)
            for name, box in got.items():
                if any(m < f for m, f in zip(margins(box, fw, fh),
                                             floors[what][name])):
                    fail((what, name), bw,
                         "%s comes nearer its %s's edge than at 1600 or 1920 "
                         "(the band): %s in %dx%d" % (name, what, box, fw, fh))
            for a, b in pairs[what]:
                if not apart(got[a], got[b]):
                    fail((what, a, b), bw, "%s and %s overlap on the %s"
                         % (a, b, what))
        pager_y = cells({"p": PANEL_LAYOUT["ic_page_prev"]}, bw)["p"][1]
        pool = (num("ROWS_Y", bw) + (VISIBLE_ROWS - 1) * num("ROW_PITCH", bw)
                + num("ROW_H", bw))
        if pool > pager_y:
            fail("pool", bw, "the row pool ends at %d, under the pager at %d"
                 % (pool, pager_y))
        # THE GRIDS, per point as the Lua places them, each card at its size.
        left = num("COL_L_X", bw)
        content = left + num("CONTENT_W", bw)
        for grid, points, w, h, right in (
                ("office", CARD_GRID, "CARD_W", "CARD_H", content),
                ("party", PARTY_GRID, "PARTY_W", "PARTY_H",
                 num("COL_R_X", bw) + num("COL_W", bw)),
                ("move", plot_grid(), "PLOT_W", "PLOT_H", content)):
            pts = [(sc(x, bw), sc(y, bw)) for x, y in points]
            x0, x1, y1 = span(pts, num(w, bw), num(h, bw), bw)
            if x0 < left - 1 or x1 > right + 1:
                fail(grid + " wide", bw, "the %s cards span x %d..%d, outside "
                     "%d..%d" % (grid, x0, x1, left, right))
            if y1 > pager_y:
                fail(grid, bw, "the %s cards end at %d, under the pager at %d"
                     % (grid, y1, pager_y))
            boxes = [(x, y, num(w, bw), num(h, bw)) for x, y in pts]
            for i in range(len(boxes)):
                for j in range(i + 1, len(boxes)):
                    if not apart(boxes[i], boxes[j]):
                        fail(grid + " overlap", bw, "two %s cards overlap: %s "
                             "and %s" % (grid, boxes[i], boxes[j]))
    return out

if BOX_W != 1920:
    _scale_pass(globals(), BOX_W)


_SMALL = []


def _small():
    """The module at a 1600 box, built once a run: the compact copies' source."""
    if not _SMALL:
        _SMALL.append(at_box(1600))
    return _SMALL[0]


def ui_file_names():
    """Every .twui.xml this generator writes, base files and compact copies."""
    return ([f for f, _b, _c in FILES] + [FIRE_FILE, BURST_FILE,
                                              GM_PIN_FILE, GM_FACE_FILE,
                                              GM_NAME_FILE, GM_LOYAL_FILE, GM_BADGE_FILE,
                                              GM_LIST_FILE]
            + sorted(COMPACT_FILES.values()))


# FIRE ON A HELD SEAT (author, 2026-09-26: "active seats should also have the
# background have effects, similar to the commission mod"). The commission's own
# ember drift - derpy_chd_rite_fire.twui.xml's `embers` emitter, which the author
# has seen running - cloned under this mod's own prefix and sprite, so the court
# never depends on the commission pack being loaded.
#
# A TEMPLATE, NOT AN EU.C TREE: the emitter needs the ParticleEmitter and Particle
# callbacks, a userproperties block and a three-frame particle_move animation, and
# the emitter library writes none of them. Every number below is the commission's
# except the SPREAD and the COUNT, which are sized to an office card rather than
# its 310px icon: the embers rise along the card's whole bottom edge.
#
# THE PARTICLE IS NAMED template_particle AND NOTHING ELSE. The emitter resolves it
# by that literal name; any other is a null the game dereferences on panel open,
# with no Lua error first (memory: wh3-particle-child-must-be-template-particle).
# check_fire() holds that.
#
# #RRGGBBAA, not ARGB: settled against CA's own particle_blood_red.png. And
# interpolationtime is a DURATION per frame, so the life is 900 + 500 ms.
EMBER_SPRITE = PLATE_DIR + "/ember.png"
EMBER_SOURCE = os.path.join(ROOT, "Modding Files", "pack", "ui", "skins", "default",
                            "derpy_chd_commission", "ember.png")
FIRE_FILE = "derpy_ic_fire.twui.xml"
FIRE_SPREAD = 300          # the emitter's width, a little inside the card's
FIRE_PARTICLES = 40
FIRE_SPAWN_MS = 120

_FIRE_TEMPLATE = """<?xml version="1.0"?>
<layout
	version="142"
	comment="derpy: embers over a held seat on the Iron Court's offices tab. Created at runtime into each office card by ICUI.card_fire; generated by tools/gen_ic_ui.py - do not edit by hand."
	precache_condition="">
	<hierarchy>
		<root this="@0">
			<derpy_ic_fire this="@1">
				<embers this="@2">
					<template_particle this="@3"/>
				</embers>
			</derpy_ic_fire>
		</root>
	</hierarchy>
	<components>
		<root
			this="@0"
			id="root"
			tooltipslocalised="true"
			uniqueguid="@0"
			currentstate="@4"
			defaultstate="@4">
			<states>
				<standard
					this="@4"
					name="standard"
					width="@W"
					height="@H"
					uniqueguid="@4"/>
			</states>
		</root>
		<derpy_ic_fire
			this="@1"
			id="derpy_ic_fire"
			priority="50"
			tooltipslocalised="true"
			uniqueguid="@1"
			currentstate="@5"
			defaultstate="@5">
			<states>
				<standard
					this="@5"
					name="standard"
					width="@W"
					height="@H"
					uniqueguid="@5"/>
			</states>
		</derpy_ic_fire>
		<embers
			this="@2"
			id="embers"
			priority="50"
			tooltipslocalised="true"
			uniqueguid="@2"
			currentstate="@6"
			defaultstate="@6">
			<callbackwithcontextlist>
				<callback_with_context callback_id="ParticleEmitter"/>
			</callbackwithcontextlist>
			<userproperties>
				<property
					name="angular_spread"
					value="30"/>
				<property
					name="loops"
					value="-1"/>
				<property
					name="max_speed_f"
					value="2"/>
				<property
					name="min_speed_f"
					value="1"/>
				<property
					name="spawn_interval"
					value="@SPAWN"/>
				<property
					name="spread"
					value="@SPREAD"/>
				<property
					name="total_particles"
					value="@COUNT"/>
			</userproperties>
			<states>
				<newstate
					this="@6"
					name="NewState"
					uniqueguid="@6"/>
			</states>
		</embers>
		<template_particle
			this="@3"
			id="template_particle"
			priority="50"
			tooltipslocalised="true"
			uniqueguid="@3"
			currentstate="@7"
			defaultstate="@7">
			<callbackwithcontextlist>
				<callback_with_context callback_id="Particle"/>
			</callbackwithcontextlist>
			<componentimages>
				<component_image
					this="@8"
					uniqueguid="@8"
					imagepath="@EMBER"/>
			</componentimages>
			<states>
				<newstate
					this="@7"
					name="NewState"
					width="9"
					height="9"
					shader_name="brighten_t0"
					uniqueguid="@7">
					<imagemetrics>
						<image
							this="@9"
							uniqueguid="@9"
							componentimage="@8"
							width="9"
							height="9"/>
					</imagemetrics>
				</newstate>
			</states>
			<animations>
				<particle_move
					id="particle_move"
					propagate="true">
					<frames>
						<frame
							interpolationtime="0"
							interpolationpropertymask="95"
							targetmetrics_m_colour="#FFC46630"
							targetmetrics_m_height="9"
							targetmetrics_m_width="9"
							targetmetrics_m_shadervars="1.00,0.00,0.00,0.00"/>
						<frame
							interpolationtime="900"
							interpolationpropertymask="91"
							targetmetrics_m_colour="#FF8A2EE8"
							targetmetrics_m_height="13"
							targetmetrics_m_width="13"
							targetmetrics_m_offset="0.00,-40.00"
							targetmetrics_m_rotation_angle="0.523599029"/>
						<frame
							interpolationtime="500"
							interpolationpropertymask="83"
							targetmetrics_m_colour="#8C2A0800"
							targetmetrics_m_height="7"
							targetmetrics_m_width="7"
							targetmetrics_m_offset="0.00,-58.00"
							targetmetrics_m_rotation_angle="0.523599029"/>
					</frames>
				</particle_move>
			</animations>
		</template_particle>
	</components>
</layout>
"""


def fire_xml():
    g = GUID_PREFIXES[FIRE_FILE]
    text = _FIRE_TEMPLATE
    for key, value in (("@W", CARD_W), ("@H", CARD_H), ("@SPAWN", FIRE_SPAWN_MS),
                       ("@SPREAD", FIRE_SPREAD), ("@COUNT", FIRE_PARTICLES),
                       ("@EMBER", EMBER_SPRITE)):
        text = text.replace(key, str(value))
    for n in range(9, -1, -1):          # @9 before @0..., so "@1" never eats "@10"
        text = text.replace("@%d" % n, "%s%04X-D000-4000-B%015X" % (g, n, n))
    return text


def check_fire(text):
    """The emitter's two rules that crash or blank the panel in silence."""
    out = []
    if text.count('callback_id="ParticleEmitter"') != text.count('callback_id="Particle"'):
        out.append("%s: every emitter needs exactly one particle" % FIRE_FILE)
    for m in re.finditer(r'<(\w+)\s+this="[^"]+"\s+id="(\w+)"[^<]*?<callbackwithcontextlist>\s*'
                         r'<callback_with_context callback_id="Particle"/>', text):
        if m.group(1) != "template_particle" or m.group(2) != "template_particle":
            out.append("%s: particle %s is not named template_particle - the emitter "
                       "resolves a null and the game dies on panel open"
                       % (FIRE_FILE, m.group(1)))
    if 'callback_id="Particle"' not in text:
        out.append("%s: no particle at all" % FIRE_FILE)
    return out


# THE CLAIM BURST (spec 2026-09-28 section 4.1). CA's own seat-claimed starburst,
# in the SHAPE of the Hell-Forge's unlock burst (hellforge_panel_unit_caps_tab,
# sprite_progression_celebration): SpriteAnimation with no `paused`, one blank
# image slot, hidden in the file. ICUI.burst creates it into the card, shows it,
# and destroys it after ICUI.BURST_SECONDS - a new one per claim, so whether a
# finished sprite replays when shown again never arises (ruling 2).
BURST_FILE = "derpy_ic_burst.twui.xml"
BURST_FRAMES = "UI/sprite_anims/warband_upgrade_starburst/starburst_"
BURST_LAST = 19
BURST_MS = 60
BURST_SIZE = 200            # CA's frames are 200x200

_BURST_TEMPLATE = """<?xml version="1.0"?>
<layout
	version="142"
	comment="derpy: CA's seat-claimed starburst for the Iron Court. Created at runtime into a card or row by ICUI.burst; generated by tools/gen_ic_ui.py - do not edit by hand."
	precache_condition="">
	<hierarchy>
		<root this="@0">
			<derpy_ic_burst this="@1"/>
		</root>
	</hierarchy>
	<components>
		<root
			this="@0"
			id="root"
			tooltipslocalised="true"
			uniqueguid="@0"
			currentstate="@2"
			defaultstate="@2">
			<states>
				<standard
					this="@2"
					name="standard"
					width="@S"
					height="@S"
					uniqueguid="@2"/>
			</states>
		</root>
		<derpy_ic_burst
			this="@1"
			id="derpy_ic_burst"
			visible="false"
			priority="60"
			tooltipslocalised="true"
			uniqueguid="@1"
			currentstate="@3"
			defaultstate="@3">
			<callbackwithcontextlist>
				<callback_with_context callback_id="SpriteAnimation">
					<child_m_user_properties>
						<property
							name="frame_name"
							value="@FRAMES"/>
						<property
							name="last_frame"
							value="@LAST"/>
						<property
							name="loops"
							value="0"/>
						<property
							name="time_per_frame"
							value="@MS"/>
					</child_m_user_properties>
				</callback_with_context>
			</callbackwithcontextlist>
			<componentimages>
				<component_image
					this="@4"
					uniqueguid="@4"/>
			</componentimages>
			<states>
				<default
					this="@3"
					name="default"
					width="@S"
					height="@S"
					uniqueguid="@3">
					<imagemetrics>
						<image
							this="@5"
							uniqueguid="@5"
							componentimage="@4"
							width="@S"
							height="@S"/>
					</imagemetrics>
				</default>
			</states>
		</derpy_ic_burst>
	</components>
</layout>
"""


def burst_xml():
    g = GUID_PREFIXES[BURST_FILE]
    text = _BURST_TEMPLATE
    for key, value in (("@FRAMES", BURST_FRAMES), ("@LAST", BURST_LAST),
                       ("@MS", BURST_MS), ("@S", BURST_SIZE)):
        text = text.replace(key, str(value))
    for n in range(5, -1, -1):
        text = text.replace("@%d" % n, "%s%04X-D000-4000-B%015X" % (g, n, n))
    return text


def check_burst(text, assets=None):
    """The burst's frames must exist: a wrong frame name draws nothing, silently."""
    out = []
    if 'callback_id="SpriteAnimation"' not in text:
        out.append("%s: no SpriteAnimation callback" % BURST_FILE)
    if 'name="paused"' in text:
        out.append("%s: paused - nothing in Lua can start a paused sprite" % BURST_FILE)
    # READ OFF THE FILE, not off BURST_FRAMES: the file is what the engine reads.
    stem = re.search(r'name="frame_name"\s+value="([^"]*)"', text)
    last = re.search(r'name="last_frame"\s+value="(\d+)"', text)
    if not stem or not last:
        out.append("%s: no frame_name or last_frame" % BURST_FILE)
    elif assets is not None:
        for n in range(int(last.group(1)) + 1):
            p = (stem.group(1).replace("\\", "/") + "%d.png" % n).lower()
            if p not in assets:
                out.append("%s: frame %s is in no pack" % (BURST_FILE, p))
    return out


# ---------------------------------------------------------------------------
# WHAT THE GOVERNORS MAP BORROWED FROM THE PARTY MAP IT REPLACED (plan
# 2026-09-30 Task 6): CA's world-space pin, and the two rings the pins wear.
MAP_RING = 60                       # both rings' default size
MAP_RING_CAPITAL = PLATE_DIR + "/map_ring_capital.png"
MAP_RING_OUTLINE = PLATE_DIR + "/map_ring_outline.png"
MAP_RING_CAPITAL_COLOUR = "#C9A45AFF"
MAP_RING_OUTLINE_COLOUR = "#D0342AFF"
# CA'S PIN, VERBATIM from dlc25_black_towers.twui.xml's template_black_tower_slot.
# check_gm() holds the emitted files to it. CA's slot also carries a fade; ours
# must not (check_gm says why).
MAP_PIN = {"id": "ContextWorldSpaceComponent", "object": "CcoCampaignSettlement",
           "function": "Position", "props": [("depth_disabled", "1")]}
def _map_supersample(size, inside_fn):
    """Coverage of each pixel by a shape, 4x4 supersampled: 0..16."""
    rows = []
    for y in range(size):
        row = []
        for x in range(size):
            n = 0
            for sy in range(4):
                for sx in range(4):
                    if inside_fn(x + (sx + 0.5) / 4.0, y + (sy + 0.5) / 4.0):
                        n += 1
            row.append(n)
        rows.append(row)
    return rows


def map_disc_pixels(hexcol, size):
    """A round plate in one colour with a darker 3px rim."""
    r, g, b = int(hexcol[1:3], 16), int(hexcol[3:5], 16), int(hexcol[5:7], 16)
    c = size / 2.0
    rad = size / 2.0 - 0.5
    cover = _map_supersample(size, lambda x, y: ((x - c) ** 2 + (y - c) ** 2) ** 0.5 <= rad)
    rim = _map_supersample(size, lambda x, y: rad - 3 < ((x - c) ** 2 + (y - c) ** 2) ** 0.5 <= rad)
    out = []
    for y in range(size):
        row = bytearray()
        for x in range(size):
            k = 0.55 if rim[y][x] * 2 > cover[y][x] > 0 else 1.0
            row += bytearray((int(r * k), int(g * k), int(b * k), cover[y][x] * 255 // 16))
        out.append(bytes(row))
    return out


def map_ring_pixels(hexcol, size=MAP_RING, width=4):
    """A ring of `width` px at the edge of a `size` square, transparent inside."""
    r, g, b = int(hexcol[1:3], 16), int(hexcol[3:5], 16), int(hexcol[5:7], 16)
    c = size / 2.0
    outer = size / 2.0 - 0.5
    cover = _map_supersample(
        size, lambda x, y: outer - width < ((x - c) ** 2 + (y - c) ** 2) ** 0.5 <= outer)
    return [bytes(bytearray(v for n in row for v in (r, g, b, n * 255 // 16)))
            for row in cover]


def _lua_map_tables():
    ui = os.path.join(ROOT, "Modding Files", "pack", "script", "campaign", "mod",
                      "zzz_derpy_iron_court_ui_map.lua")
    return io.open(ui, encoding="utf-8").read()


# ---------------------------------------------------------------------------
# THE GOVERNORS VIEW'S PINS (spec 2026-09-30 sections 1 and 6). Four files, made
# at runtime into the panel's first child and never scaled (plan ruling 1):
# a PIN - CA's Chaos Dwarf map pin, the party ring, the capital and outline
# rings; it takes the click and carries the tooltip - a FACE - the governor's
# portrait or his party's crest, masked round in the pin's head - and two
# PLATES, the province's name and its loyalty, one line each on CA's own plate.
# One settlement context and one anchor, the box's bottom centre, for all four,
# so the engine stands each on the settlement's point: a box's height is what
# sets how far above the point its art draws.
GM_PIN_FILE = "derpy_ic_gm_pin.twui.xml"
GM_FACE_FILE = "derpy_ic_gm_face.twui.xml"
GM_NAME_FILE = "derpy_ic_gm_name.twui.xml"
GM_LOYAL_FILE = "derpy_ic_gm_loyal.twui.xml"
GM_BADGE_FILE = "derpy_ic_gm_badge.twui.xml"
GM_PIN_W = 180
_GM_CX = GM_PIN_W // 2
GM_PIN_ART = "ui/skins/default/dlc23_chd_narrative_panel/chd_narrative_panel_map_pin.png"
GM_PIN_ART_BOX = (_GM_CX - 25, 4, 50, 80)   # CA's 50x80, centred
GM_HEAD = (_GM_CX - 19, 9, 38, 38)          # its head: CA's 38x38 image at 6,5
GM_RING = 46                                # the party ring, 4px, round the head
GM_RING_OUTER = 54                          # the capital and outline rings
GM_PORT_BOX = (_GM_CX - 35, 9, 70, 38)      # a porthole at its own aspect across the head
# THE GOVERNOR'S PARTY FLAG (author, 2026-09-30: "no flag or indication what
# the governer party is"): his party's crest over the head's lower right, the
# way CA badges a portrait. Its own component, the pin's box, made after the
# face: in the face it would be cut round by the face's mask.
GM_BADGE_BOX = (_GM_CX + 8, 28, 26, 26)
# CA'S PLATE AT ITS OWN HEIGHT (author, 2026-09-30: "the ui is stretched, use
# the default borders"). sub_title.png is 113x30: a bronze rim at rows 2-3 and
# 23-24, a flat #141414 face between them from x 5, a shadow under. Only its
# middle stretches sideways, between the two caps its margin keeps whole.
GM_PLATE = "ui/skins/default/dlc23_chd_hell_forge/sub_title.png"
# ITS RAILS, and the toggle labels' tab_sub_title.png has the same profile: both
# are 113x30, frame in rows 0-3, a dark field in rows 4-22, frame and shadow in
# rows 23-29 (measured off CA's art). Sliced with no vertical margin they SCALE:
# at 124px the strip's bottom rail and shadow ran 29px and the section line sat
# on them, and at 26px a toggle's field was 15px under an 18px word (author,
# 2026-10-01: "the ui is stretched and the ui is cut off"). check_gm_plates.
GM_PLATE_RAIL = (4, 7)                  # top, bottom, in the art's own pixels
GM_PLATE_MARGIN = (8, 12)               # vertical, horizontal
GM_PLATE_H = 30
GM_PLATE_CAP = 12
GM_PLATE_GAP = 2
# THE LOYALTY PLATE, at the point: CA's plate at its native 113x30, whole.
GM_LOYAL_W, GM_LOYAL_H = 113, GM_PLATE_H
# THE NAME PLATE, on it. Its box is as far below the plate as above it, so text
# centred in the box - no padding, which the engine does not honour the way the
# second build assumed - lands on the plate's own centre.
GM_NAME_PLATE_Y = GM_LOYAL_H + GM_PLATE_GAP         # the plate's bottom, above the point
GM_NAME_H = 2 * GM_NAME_PLATE_Y + GM_PLATE_H
GM_NAME_PLATE_BOX = (0, GM_NAME_PLATE_Y, GM_PIN_W, GM_PLATE_H)
# THE PARTY'S COLOUR, over the plate's dark face and nothing else, so CA's rim
# stays CA's (author, 2026-09-30: "the map doesnt show the political influence
# colors of each party").
GM_WASH_BOX = (5, GM_NAME_PLATE_Y + 4, GM_PIN_W - 10, 19)
# DARKENED TO KEEP THE TEXT READABLE: the brightest ground under which GM_INK
# keeps 4.5:1 by make_ic_backdrop's own measure (Rec.709 on the stored values),
# which is 45. A party colour brighter than that keeps its hue and loses light.
GM_INK = (0xFF, 0xF8, 0xD7)
GM_WASH_LUM = 44
# THE PIN, above both: its point ends where the name plate begins.
GM_PIN_H = GM_PIN_ART_BOX[1] + GM_PIN_ART_BOX[3] + GM_NAME_PLATE_Y + GM_PLATE_H
GM_FACE_GROUND = PLATE_DIR + "/gm_face_ground.png"
GM_FACE_GROUND_COLOUR = "#1A1410FF"
GM_MASK = "ui/skins/default/porthole_mask.png"
# THE PLATE'S INSIDE, between its caps: the name is cut to it (author,
# 2026-09-30: "the text are going out of the ui"). Must match ICUI.GM_NAME_W in
# zzz_derpy_iron_court_ui_map.lua (check_gm).
GM_NAME_W = GM_PIN_W - 2 * GM_PLATE_CAP
# CA'S MAP-PIN ANCHOR, the box's bottom centre (worldroots_forest and
# dlc27_nor_seafang_overlay, the two CA overlays that stand a pin on a place).
GM_ANCHOR = (0.5, 1.0)
# THE LAYERS THE LUA PAINTS, IN ORDER. Must match ICUI.GP_*, ICUI.GF_* and
# ICUI.GN_* in zzz_derpy_iron_court_ui_map.lua (check_gm).
GM_PIN_LAYERS = ["art", "party", "capital", "outline"]
GM_FACE_LAYERS = ["ground", "port", "crest", "mask"]
GM_NAME_LAYERS = ["plate", "wash"]
GM_BADGE_LAYERS = ["crest"]
LAYOUT_TABLES[GM_PIN_FILE] = {"derpy_ic_gm_pin": (0, 0, GM_PIN_W, GM_PIN_H)}
LAYOUT_TABLES[GM_FACE_FILE] = {"derpy_ic_gm_face": (0, 0, GM_PIN_W, GM_PIN_H)}
LAYOUT_TABLES[GM_NAME_FILE] = {"derpy_ic_gm_name": (0, 0, GM_PIN_W, GM_NAME_H)}
LAYOUT_TABLES[GM_LOYAL_FILE] = {"derpy_ic_gm_loyal": (0, 0, GM_LOYAL_W, GM_LOYAL_H)}
LAYOUT_TABLES[GM_BADGE_FILE] = {"derpy_ic_gm_badge": (0, 0, GM_PIN_W, GM_PIN_H)}


def gm_ring_path(slug):
    return "%s/gm_ring_%s.png" % (PLATE_DIR, slug)


def gm_wash_path(slug):
    return "%s/gm_wash_%s.png" % (PLATE_DIR, slug)


def gm_wash_colours():
    """slug -> colour, every party and absorbed faction a governor can serve."""
    out = dict((p[0], HOUSE_COLOUR[p[0]]) for p in IC.PARTIES)
    out.update((slug, CONFED_COLOUR[slug]) for slug in CONFED_SEATS)
    return out


def _rec709(rgb):
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def gm_wash_pixels(hexcol):
    """The party's colour over the plate's face, dimmed to GM_WASH_LUM at most."""
    rgb = (int(hexcol[1:3], 16), int(hexcol[3:5], 16), int(hexcol[5:7], 16))
    k = min(1.0, GM_WASH_LUM / max(_rec709(rgb), 1.0))
    px = bytes(bytearray([int(v * k) for v in rgb] + [255]))
    return [px * GM_WASH_BOX[2]] * GM_WASH_BOX[3]


def _gm_layer(box, path=None, margin=0, size=(GM_PIN_W, GM_PIN_H)):
    """An image layer at `box` inside a component of `size`."""
    x, y, w, h = box
    return {"path": path or MASK_NONE, "offset": (x, y), "dw": w - size[0],
            "dh": h - size[1], "margin": margin, "dock": None}


def _gm_ring(size):
    """A `size` square centred on the pin's head."""
    hx, hy, hw, hh = GM_HEAD
    return _gm_layer((hx + (hw - size) / 2.0, hy + (hh - size) / 2.0, size, size))


def _gm_pin():
    root = EU.C("root", GM_PIN_W, GM_PIN_H)
    # NO TEXT: the plates carry it.
    root.add(EU.C(
        "derpy_ic_gm_pin", GM_PIN_W, GM_PIN_H, interactive=True,
        sound=OPENER_SOUND, callbacks=[MAP_PIN], anchor=GM_ANCHOR,
        layers=[_gm_layer(GM_PIN_ART_BOX, GM_PIN_ART), _gm_ring(GM_RING),
                _gm_ring(GM_RING_OUTER), _gm_ring(GM_RING_OUTER)]))
    return root


def _gm_face():
    root = EU.C("root", GM_PIN_W, GM_PIN_H)
    # NOT INTERACTIVE: the pin under it takes the click and the tooltip.
    root.add(EU.C(
        "derpy_ic_gm_face", GM_PIN_W, GM_PIN_H, callbacks=[MAP_PIN], anchor=GM_ANCHOR,
        layers=[_gm_layer(GM_HEAD, GM_FACE_GROUND), _gm_layer(GM_PORT_BOX),
                _gm_layer(GM_HEAD), _gm_layer(GM_HEAD, GM_MASK)],
        mask=GM_FACE_LAYERS.index("mask")))
    return root


# ONE LINE, CENTRED, NO PADDING: the box puts it on the plate (check_gm).
_GM_TEXT = dict(align="Center", valign="Center", tx="0.00,0.00", ty="0.00,0.00", leading=0)


def _gm_name():
    root = EU.C("root", GM_PIN_W, GM_NAME_H)
    size = (GM_PIN_W, GM_NAME_H)
    # NOT INTERACTIVE, like the face: a click on a plate is the pin's.
    root.add(EU.C(
        "derpy_ic_gm_name", GM_PIN_W, GM_NAME_H, callbacks=[MAP_PIN], anchor=GM_ANCHOR,
        layers=[_gm_layer(GM_NAME_PLATE_BOX, GM_PLATE, (0, GM_PLATE_CAP), size),
                _gm_layer(GM_WASH_BOX, None, 0, size)],
        **style("derpy_ic_gm_name", **_GM_TEXT)))
    return root


def _gm_loyal():
    root = EU.C("root", GM_LOYAL_W, GM_LOYAL_H)
    root.add(EU.C(
        "derpy_ic_gm_loyal", GM_LOYAL_W, GM_LOYAL_H, callbacks=[MAP_PIN], anchor=GM_ANCHOR,
        layers=[_gm_layer((0, 0, GM_LOYAL_W, GM_LOYAL_H), GM_PLATE, (0, GM_PLATE_CAP),
                          (GM_LOYAL_W, GM_LOYAL_H))],
        **style("derpy_ic_gm_loyal", **_GM_TEXT)))
    return root


def _gm_badge():
    root = EU.C("root", GM_PIN_W, GM_PIN_H)
    # NOT INTERACTIVE and NO TEXT: the pin under it takes the click.
    root.add(EU.C(
        "derpy_ic_gm_badge", GM_PIN_W, GM_PIN_H, callbacks=[MAP_PIN], anchor=GM_ANCHOR,
        layers=[_gm_layer(GM_BADGE_BOX)]))
    return root


def gm_badge_xml():
    return EU.layout(EU.assign(_gm_badge(), GUID_PREFIXES[GM_BADGE_FILE]),
                     "derpy: one Iron Court governor pin's party badge, pinned over its "
                     "pin's head; generated by tools/gen_ic_ui.py.")


def gm_pin_xml():
    return EU.layout(EU.assign(_gm_pin(), GUID_PREFIXES[GM_PIN_FILE]),
                     "derpy: one Iron Court governor pin, pinned to a settlement by "
                     "CA's ContextWorldSpaceComponent; generated by tools/gen_ic_ui.py.")


def gm_face_xml():
    return EU.layout(EU.assign(_gm_face(), GUID_PREFIXES[GM_FACE_FILE]),
                     "derpy: one Iron Court governor's masked face, pinned beside its "
                     "pin; generated by tools/gen_ic_ui.py.")


def gm_name_xml():
    return EU.layout(EU.assign(_gm_name(), GUID_PREFIXES[GM_NAME_FILE]),
                     "derpy: one Iron Court governor pin's name plate, pinned under its "
                     "pin; generated by tools/gen_ic_ui.py.")


def gm_loyal_xml():
    return EU.layout(EU.assign(_gm_loyal(), GUID_PREFIXES[GM_LOYAL_FILE]),
                     "derpy: one Iron Court governor pin's loyalty plate, pinned at its "
                     "settlement; generated by tools/gen_ic_ui.py.")


def check_gm_plates(layout=None, panel_text=None, row_text=None, row_layout=None):
    """Every text cell the Governors view shows lies inside one of its plates.

    Shown: every ic_gm_ cell, the footer line, and every cell of the top strip,
    which is whatever ends above ic_gm_top's bottom edge - derived, so a cell
    added to the strip later is held here without an edit. The rows are held
    by their pool: the pool must lie inside the column.

    AND A ROW'S BADGE AND CREST DRAW OVER ITS FACE. Children draw in the order
    the hierarchy declares them, and the face is opaque: declared first, as a
    sorted walk put it, the badge on the face's corner never showed (preview,
    2026-09-30).
    """
    lay = layout or PANEL_LAYOUT
    text = panel_text if panel_text is not None else EU.layout(
        EU.assign(_panel(), GUID_PREFIXES["derpy_ic_panel.twui.xml"]), "")
    has_text = set(n for n, b in _component_blocks(text).items() if "<component_text" in b)
    plates = [lay[n] for n in GM_PLATES]

    def inside(b, p):
        return (b[0] >= p[0] and b[1] >= p[1] and b[0] + b[2] <= p[0] + p[2]
                and b[1] + b[3] <= p[1] + p[3])
    top = lay["ic_gm_top"]
    out = []
    for name, box in sorted(lay.items()):
        shown = (name.startswith("ic_gm_") or name == "ic_alert"
                 or box[1] + box[3] <= top[1] + top[3])
        if shown and name in has_text and not any(inside(box, p) for p in plates):
            out.append("%s %r reads over the bare map in the Governors view: no plate "
                       "of %s contains it" % (name, box, ", ".join(GM_PLATES)))
    col = lay["ic_gm_col"]
    pool = (GM_ROW_X, GM_ROW_Y, GM_LIST_W, GM_LIST_H)
    if not inside(pool, col):
        out.append("the column's list %r runs outside the column %r" % (pool, col))
    # CA'S ART AT ITS OWN SIZE (author, 2026-10-01: "the left panel is still
    # cutting off on the top and bottom"). The column art is a whole screen's
    # side: ended at the footer's top, the map showed under it whenever the
    # footer was hidden. The title squeezed to 60 had its spikes flattened
    # against the strip.
    s = PANEL_H / float(GM_COL_ART_H)       # the art's scale on this screen
    if (col[1], col[3]) != (0, PANEL_H) or abs(col[2] - GM_COL_ART_W * s) > 1:
        out.append("ic_gm_col %r is not CA's %dx%d column from the screen's top to its "
                   "foot: cut short, the map shows under it" % (col, GM_COL_ART_W * s, PANEL_H))
    if abs(lay["ic_gm_head"][3] - GM_HEAD_ART_H * s) > 1:
        out.append("ic_gm_head is %dpx tall, not the title art's %d: its spikes squash"
                   % (lay["ic_gm_head"][3], GM_HEAD_ART_H * s))
    # AND THE COLUMN'S STACK, top to bottom, with nothing over the next.
    stack = [("ic_gm_head", lay["ic_gm_head"]), ("ic_gm_tog_lbl_1", lay["ic_gm_tog_lbl_1"]),
             ("ic_gm_hint", lay["ic_gm_hint"]), ("the list", pool),
             ("ic_gm_btns", lay["ic_gm_btns"]),
             ("ic_gm_foot", lay["ic_gm_foot"])]
    for (a, ab), (b, bb) in zip(stack, stack[1:]):
        if ab[1] + ab[3] > bb[1]:
            out.append("%s ends at %d, under %s at %d" % (a, ab[1] + ab[3], b, bb[1]))
    rt = row_text if row_text is not None else EU.layout(
        EU.assign(_gm_row(), GUID_PREFIXES[GM_ROW_FILE]), "")
    order = re.findall(r"<(ic_gr_\w+) this=", rt.split("<hierarchy>", 1)[-1])
    for over in ("ic_gr_crest", "ic_gr_badge"):
        if over not in order or "ic_gr_face" not in order \
                or order.index(over) < order.index("ic_gr_face"):
            out.append("%s: %s is declared before ic_gr_face, so the face draws over "
                       "it" % (GM_ROW_FILE, over))
    # THE SUB-TITLE PLATES: rails at the art's own thickness, and every word on
    # one inside its dark field (GM_PLATE_RAIL).
    blocks = _component_blocks(text)
    rt_, rb_ = GM_PLATE_RAIL
    for name in ["ic_gm_top", "ic_gm_foot"] + sorted(n for n in lay if n.startswith("ic_gm_tog_lbl_")):
        blk = blocks.get(name, "")
        m = re.search(r'margin="([\d.]+),[\d.]+,([\d.]+),', blk)
        if not m or float(m.group(1)) < max(GM_PLATE_RAIL) or float(m.group(2)) < max(GM_PLATE_RAIL):
            out.append("%s: its plate slices with vertical margin %s, under the %dpx rails, "
                       "so the rails stretch with it" % (name, m and m.groups(), max(GM_PLATE_RAIL)))
        px, py, pw, ph = lay[name]
        field = (py + rt_, py + ph - rb_)
        if name.startswith("ic_gm_tog_lbl_"):
            # ITS OWN WORD: the text area is the box less its (top, bottom) padding.
            ty = re.search(r'textyoffset="([-\d.]+),([-\d.]+)"', blk)
            top, bot = (float(ty.group(1)), float(ty.group(2))) if ty else (0.0, 0.0)
            if py + top < field[0] or py + ph - bot > field[1]:
                out.append("%s: its word's area %d..%d is not inside the plate's field %d..%d"
                           % (name, py + top, py + ph - bot, field[0], field[1]))
        else:
            # THE LINES IT HOLDS: every text cell inside the plate's box.
            for cell, box in sorted(lay.items()):
                if cell in has_text and cell not in GM_PLATES and inside(box, lay[name]) \
                        and (box[1] < field[0] or box[1] + box[3] > field[1]):
                    out.append("%s %r crosses %s's rails: its field is %d..%d"
                               % (cell, box, name, field[0], field[1]))
    # EVERY LINE AND THE ICON CLEAR THE ROW'S OWN RAILS.
    rl = row_layout or GM_ROW_LAYOUT
    s = GM_ROW_H / float(GM_ROW_ART_H)
    t, r, b, l = GM_ROW_RAIL
    for name in GM_ROW_CLEAR:
        x, y, w, h = rl[name]
        if x < l or x + w > GM_ROW_W - r or y < t * s or y + h > GM_ROW_H - b * s:
            out.append("%s %r crosses the row frame's rails %r (art pixels; top and "
                       "bottom scaled to a %dpx row): the frame runs through it"
                       % (name, (x, y, w, h), GM_ROW_RAIL, GM_ROW_H))
    return out


def _component_blocks(text):
    """name -> its <components> block, for every component of a file."""
    body = text.split("<components>", 1)[-1]
    out = {}
    for block in re.split(r"(?m)^\t\t<(?=\w)", body)[1:]:
        out[re.match(r"(\w+)", block).group(1)] = block
    return out


def check_masks(files):
    """Every maskimage names a component_image of its own component."""
    out = []
    for fname, text in sorted(files.items()):
        for name, block in sorted(_component_blocks(text).items()):
            m = re.search(r'maskimage="([^"]+)"', block)
            if m and ('<component_image\n\t\t\t\t\tthis="%s"' % m.group(1)) not in block:
                out.append("%s: %s's maskimage %s names no component_image of its "
                           "own, so it masks nothing" % (fname, name, m.group(1)))
    return out


def _gm_images(text, name):
    """[(imagepath, x, y, w, h)] for each layer of `name`'s standard state, in order."""
    block = _component_blocks(text).get(name, "")
    paths = dict(re.findall(r'<component_image\n\t+this="([^"]+)"\n\t+uniqueguid="[^"]+"'
                            r'\n\t+imagepath="([^"]*)"', block))
    out = []
    for cig, x, y, w, h in re.findall(
            r'componentimage="([^"]+)"\n\t+offset="([-\d.]+),([-\d.]+)"\n\t+'
            r'width="(\d+)"\n\t+height="(\d+)"', block):
        out.append((paths.get(cig), float(x), float(y), int(w), int(h)))
    return out


def _gm_box(text, name):
    m = re.search(r'width="(\d+)"\n\t\t\t\t\theight="(\d+)"',
                  _component_blocks(text).get(name, ""))
    return m and (int(m.group(1)), int(m.group(2)))


def check_gm(pin_text=None, face_text=None, panel_text=None, lua_text=None,
             name_text=None, loyal_text=None, wash=None, badge_text=None):
    """The pins' holder first and inert; CA's pin, a face and two plates on one
    settlement; CA's plate at its own height; the Lua's numbers ours."""
    out = []
    pt = pin_text if pin_text is not None else gm_pin_xml()
    ft = face_text if face_text is not None else gm_face_xml()
    nt = name_text if name_text is not None else gm_name_xml()
    lt = loyal_text if loyal_text is not None else gm_loyal_xml()
    bt = badge_text if badge_text is not None else gm_badge_xml()
    wash = wash or gm_wash_pixels
    if panel_text is None:
        panel_text = EU.layout(EU.assign(_panel(), GUID_PREFIXES["derpy_ic_panel.twui.xml"]), "")
    tree = panel_text.split("<hierarchy>", 1)[-1].split("</hierarchy>", 1)[0]
    first = re.search(r"<derpy_ic_panel [^>]*>\s*<(\w+)", tree)
    if not first or first.group(1) != "ic_gm_pins":
        out.append("derpy_ic_panel.twui.xml: ic_gm_pins is not the panel's first child, "
                   "so a pin draws over the court")
    holder = _component_blocks(panel_text).get("ic_gm_pins", "")
    if not holder or 'interactive="true"' in holder:
        out.append("derpy_ic_panel.twui.xml: ic_gm_pins is missing or takes clicks, so "
                   "the bare map beside a pin would not")
    files = ((GM_PIN_FILE, pt), (GM_FACE_FILE, ft), (GM_NAME_FILE, nt), (GM_LOYAL_FILE, lt),
             (GM_BADGE_FILE, bt))
    for fname, t in files:
        if 'callback_id="%s"' % MAP_PIN["id"] not in t:
            out.append("%s: no %s callback" % (fname, MAP_PIN["id"]))
        if 'context_function_id="%s"' % MAP_PIN["function"] not in t:
            out.append("%s: %s's function is not CA's" % (fname, MAP_PIN["id"]))
        if 'context_object_id="CcoCampaignSettlement"' not in t:
            out.append("%s: not pinned on CcoCampaignSettlement" % fname)
        if 'name="depth_disabled"' not in t:
            out.append("%s: the pin lost depth_disabled" % fname)
        # NO FADE. In game on 2026-09-29 (build A06C68A6) the old party map's
        # marker tracked its settlement and took clicks but drew nothing. CA's
        # fade reads the component's OWN screen y, and one made from Lua starts
        # at its parent's corner, y = 0: 0/50 = 0, fully transparent. 26 of CA's
        # 28 pinned layouts carry no fade.
        if 'callback_id="ContextOpacitySetter"' in t:
            out.append("%s: carries a ContextOpacitySetter - it drew nothing in game" % fname)
        # ROOT AND ONE COMPONENT (plan ruling 1): a child would draw at the corner.
        ids = re.findall(r'\n\t\t\tid="([^"]+)"', t)
        want = ["root", fname.replace(".twui.xml", "")]
        if ids != want:
            out.append("%s: components %r - a pin may have no children" % (fname, ids))
        # ABOVE ITS SETTLEMENT (author, 2026-09-30: "make it higher"): every one
        # of the four stands its bottom centre on the point.
        if 'component_anchor_point="%.2f,%.2f"' % GM_ANCHOR not in t:
            out.append("%s: not anchored at its bottom centre, so the pin does not "
                       "stand above its settlement" % fname)
    # ONE BOX FOR PIN AND FACE, or the engine anchors them apart: read off the
    # two emitted components, not off the constant both were built from.
    if not _gm_box(pt, "derpy_ic_gm_pin") or _gm_box(pt, "derpy_ic_gm_pin") != _gm_box(ft, "derpy_ic_gm_face"):
        out.append("the pin is %r and the face %r, so the engine anchors them apart"
                   % (_gm_box(pt, "derpy_ic_gm_pin"), _gm_box(ft, "derpy_ic_gm_face")))
    if 'interactive="true"' not in pt:
        out.append("%s: the pin takes no click" % GM_PIN_FILE)
    for fname, t in files[1:]:
        if 'interactive="true"' in t:
            out.append("%s: takes clicks, so the pin under it never gets one" % fname)
    if 'maskimage="' not in ft:
        out.append("%s: the face has no maskimage, so it draws square" % GM_FACE_FILE)
    # THE PIN CARRIES NO TEXT. Padded down to its plate, the third build's drew
    # above the plate and cut every name, however short (author, 2026-09-30:
    # "no text", "theres '...'").
    if "<component_text" in pt:
        out.append("%s: the pin carries text again - padded, it drew off its plate "
                   "and measured every name too long" % GM_PIN_FILE)
    # ONE LINE, CENTRED, NO PADDING, on each plate: the box places it.
    for fname, t in ((GM_NAME_FILE, nt), (GM_LOYAL_FILE, lt)):
        m = re.search(r'texthalign="(\w+)"\s+textvalign="(\w+)"\s+textxoffset="([^"]+)"'
                      r'\s+textyoffset="([^"]+)"', t)
        if not m or m.groups() != ("Center", "Center", "0.00,0.00", "0.00,0.00"):
            out.append("%s: the text is not centred with no padding (%s) - padding "
                       "moves it off its plate" % (fname, m and m.groups()))
    # CA'S PLATE AT ITS OWN HEIGHT (author, 2026-09-30: "the ui is stretched,
    # use the default borders").
    name_box = _gm_box(nt, "derpy_ic_gm_name") or (0, 0)
    loyal_box = _gm_box(lt, "derpy_ic_gm_loyal") or (0, 0)
    name_layers = _gm_images(nt, "derpy_ic_gm_name")
    loyal_layers = _gm_images(lt, "derpy_ic_gm_loyal")
    for fname, layers in ((GM_NAME_FILE, name_layers), (GM_LOYAL_FILE, loyal_layers)):
        plates = [lay for lay in layers if lay[0] == GM_PLATE]
        if len(plates) != 1 or plates[0][4] != GM_PLATE_H:
            out.append("%s: CA's plate is not drawn once at its own %dpx: %r - "
                       "stretched, its rims thicken" % (fname, GM_PLATE_H, plates))
    if [lay[0] == GM_PLATE for lay in name_layers] != [n == "plate" for n in GM_NAME_LAYERS]:
        out.append("%s: the layers are not %r in order" % (GM_NAME_FILE, GM_NAME_LAYERS))
    if loyal_layers[:1] != [(GM_PLATE, 0.0, 0.0, loyal_box[0], loyal_box[1])]:
        out.append("%s: the plate is not the whole box, so its text is off it" % GM_LOYAL_FILE)
    plate = ([lay for lay in name_layers if lay[0] == GM_PLATE] or [(None, 0, 0, 0, 0)])[0]
    # CENTRED TEXT LANDS ON THE PLATE only when the plate is the box's middle.
    if plate[2] + plate[4] / 2.0 != name_box[1] / 2.0:
        out.append("%s: the plate's middle is %.1f and the box's %.1f, so the name "
                   "draws off it" % (GM_NAME_FILE, plate[2] + plate[4] / 2.0, name_box[1] / 2.0))
    # ON THE LOYALTY PLATE, NOT OVER IT: the name box's bottom is the point too.
    up = name_box[1] - plate[2] - plate[4]
    if up < loyal_box[1]:
        out.append("%s: the name plate ends %dpx above the point, inside the loyalty "
                   "plate's %d" % (GM_NAME_FILE, up, loyal_box[1]))
    # THE PORTRAIT ON TOP: the pin's point ends where the name plate begins.
    art = ([lay for lay in _gm_images(pt, "derpy_ic_gm_pin") if lay[0] == GM_PIN_ART]
           or [(None, 0, 0, 0, 0)])[0]
    pin_box = _gm_box(pt, "derpy_ic_gm_pin") or (0, 0)
    if pin_box[1] - (art[2] + art[4]) < up + plate[4]:
        out.append("the pin reaches into the name plate under it, so the portrait is "
                   "not on top of the text")
    # THE BADGE: the pin's box, so the two anchor as one; no text; one crest
    # over the head's edge and above the plates.
    if _gm_box(bt, "derpy_ic_gm_badge") != _gm_box(pt, "derpy_ic_gm_pin"):
        out.append("the badge is %r and the pin %r, so the engine anchors them apart"
                   % (_gm_box(bt, "derpy_ic_gm_badge"), _gm_box(pt, "derpy_ic_gm_pin")))
    if "<component_text" in bt:
        out.append("%s: the badge carries text" % GM_BADGE_FILE)
    _bl = _gm_images(bt, "derpy_ic_gm_badge")
    _hx, _hy, _hw, _hh = GM_HEAD
    if len(_bl) != len(GM_BADGE_LAYERS) or not (
            _bl[0][1] < _hx + _hw and _bl[0][1] + _bl[0][3] > _hx
            and _bl[0][2] < _hy + _hh and _bl[0][2] + _bl[0][4] > _hy
            and _bl[0][2] + _bl[0][4] <= GM_PIN_ART_BOX[1] + GM_PIN_ART_BOX[3]):
        out.append("%s: the crest is not one image on the head, above the plates: %r"
                   % (GM_BADGE_FILE, _bl))
    m = re.search(r"ICUI\.GB_CREST\s*=\s*(\d+)", lua_text if lua_text is not None
                  else _lua_map_tables())
    if not m or int(m.group(1)) != GM_BADGE_LAYERS.index("crest"):
        out.append("ICUI.GB_CREST does not name the badge's crest layer")
    # THE WASH ON THE PLATE'S FACE, NOT ITS RIM.
    washes = [lay for lay in name_layers if lay[0] != GM_PLATE]
    if not washes or not (washes[0][1] >= 5 and washes[0][1] + washes[0][3] <= name_box[0] - 5
                          and washes[0][2] >= plate[2] + 4
                          and washes[0][2] + washes[0][4] <= plate[2] + 23):
        out.append("%s: the party's colour is not on the plate's face alone: %r"
                   % (GM_NAME_FILE, washes))
    # READABLE ON EVERY PARTY'S COLOUR, measured on the pixels that ship.
    ink = _rec709(GM_INK)
    for slug, hexcol in sorted(gm_wash_colours().items()):
        px = bytearray(wash(hexcol)[0][:3])
        ratio = (ink / 255.0 + 0.05) / (_rec709(px) / 255.0 + 0.05)
        if ratio < 4.5:
            out.append("%s's name plate: the text is %.2f:1 on its colour, under 4.5"
                       % (slug, ratio))
    lua = lua_text if lua_text is not None else _lua_map_tables()
    m = re.search(r"ICUI\.GM_PIN_W,\s*ICUI\.GM_PIN_H\s*=\s*(\d+),\s*(\d+)", lua)
    if not m or (int(m.group(1)), int(m.group(2))) != (GM_PIN_W, GM_PIN_H):
        out.append("ICUI.GM_PIN_W/H are not the generator's %dx%d" % (GM_PIN_W, GM_PIN_H))
    m = re.search(r"ICUI\.GM_NAME_H\s*=\s*(\d+)", lua)
    if not m or int(m.group(1)) != GM_NAME_H:
        out.append("ICUI.GM_NAME_H is not the generator's %d" % GM_NAME_H)
    m = re.search(r"ICUI\.GM_LOYAL_W,\s*ICUI\.GM_LOYAL_H\s*=\s*(\d+),\s*(\d+)", lua)
    if not m or (int(m.group(1)), int(m.group(2))) != (GM_LOYAL_W, GM_LOYAL_H):
        out.append("ICUI.GM_LOYAL_W/H are not the generator's %dx%d" % (GM_LOYAL_W, GM_LOYAL_H))
    m = re.search(r"ICUI\.GP_ART,\s*ICUI\.GP_PARTY,\s*ICUI\.GP_CAPITAL,\s*ICUI\.GP_OUTLINE"
                  r"\s*=\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)", lua)
    if not m or [int(v) for v in m.groups()] != list(range(len(GM_PIN_LAYERS))):
        out.append("ICUI.GP_* do not name the pin's layers 0..3 in order")
    m = re.search(r"ICUI\.GF_PORT,\s*ICUI\.GF_CREST\s*=\s*(\d+),\s*(\d+)", lua)
    if not m or (int(m.group(1)), int(m.group(2))) != (
            GM_FACE_LAYERS.index("port"), GM_FACE_LAYERS.index("crest")):
        out.append("ICUI.GF_PORT/GF_CREST do not name the face's port and crest layers")
    m = re.search(r"ICUI\.GN_PLATE,\s*ICUI\.GN_WASH\s*=\s*(\d+),\s*(\d+)", lua)
    if not m or [int(v) for v in m.groups()] != list(range(len(GM_NAME_LAYERS))):
        out.append("ICUI.GN_PLATE/GN_WASH do not name the name plate's layers")
    if ('"%s/gm_wash_" .. slug .. ".png"' % PLATE_DIR) not in lua:
        out.append("ICUI.gm_wash_path does not build gm_wash_path's names, so a "
                   "plate's colour draws blank")
    m = re.search(r"ICUI\.GM_NAME_W\s*=\s*(\d+)", lua)
    if not m or int(m.group(1)) != GM_NAME_W:
        out.append("ICUI.GM_NAME_W is not the plate's inside, %d: a name cut to "
                   "anything wider runs off it" % GM_NAME_W)
    m = re.search(r'ICUI\.GM_BACKDROP\s*=\s*"([^"]+)"', lua)
    if not m or m.group(1) != PANEL_BG:
        out.append("ICUI.GM_BACKDROP is not PANEL_BG, %s: leaving the view would "
                   "put the wrong ground back" % PANEL_BG)
    return out


def check_rim_slots():
    """ICUI.RIMS in the panel Lua must name the layers this file emits."""
    ui = os.path.join(ROOT, "Modding Files", "pack", "script", "campaign", "mod",
                      "zzz_derpy_iron_court_ui.lua")
    text = io.open(ui, encoding="utf-8").read()
    at = text.find("ICUI.RIMS = {")
    if at < 0:
        return ["the panel Lua has no ICUI.RIMS table"]
    block = text[at:text.find("\n}", at)]
    want = {"card": CARD_RIM}
    for kind in ("party",):
        if ("%s_RIM" % kind.upper()) in globals():
            want[kind] = globals()["%s_RIM" % kind.upper()]
    out = []
    if ('ICUI.RIM_ART = "%s"' % RIM_ART) not in text:
        out.append("ICUI.RIM_ART is not %s, the art this file writes" % RIM_ART)
    if ('ICUI.RIM_ART_FAIL = "%s"' % RIM_FAIL_ART) not in text:
        out.append("ICUI.RIM_ART_FAIL is not %s, the art this file writes"
                   % RIM_FAIL_ART)
    # AND THE FAIL LOOK IS NOT RED, measured off the picture it ships: its
    # peak pixel, 10px in, with no channel far below the brightest.
    peak = seat_rim_pixels(rgb=RIM_FAIL_RGB)[RIM_PX // 2][40:43]
    if min(peak) < max(peak) // 2:
        out.append("the fail rim art is %r at its peak, a hue a failure shares "
                   "with the lit rim" % (tuple(peak),))
    for kind, looks in sorted(want.items()):
        m = re.search(r"\b%s\s*=\s*\{([^}]*)\}" % kind, block)
        if not m:
            out.append("ICUI.RIMS has no %s entry" % kind)
            continue
        got = dict((k, int(v)) for k, v in re.findall(r"(\w+)\s*=\s*(\d+)", m.group(1)))
        if got != looks:
            out.append("ICUI.RIMS.%s is %r and the file emits %r" % (kind, got, looks))
    return out


def build_xml():
    out = {}
    for fname, builder, comment in FILES:
        root = EU.assign(builder(), GUID_PREFIXES[fname])
        out[fname] = EU.layout(root, comment)
    out[FIRE_FILE] = fire_xml()
    out[BURST_FILE] = burst_xml()
    out[GM_PIN_FILE] = gm_pin_xml()
    out[GM_FACE_FILE] = gm_face_xml()
    out[GM_NAME_FILE] = gm_name_xml()
    out[GM_LOYAL_FILE] = gm_loyal_xml()
    out[GM_BADGE_FILE] = gm_badge_xml()
    out[GM_LIST_FILE] = gm_list_xml()
    # THE COMPACT COPIES are built by the copy of this module at a 1600 box,
    # whose fonts are already one size down and whose cells are already the
    # sizes a 1600x900 player gets. Only the base module writes them: a copy
    # asked for its own files returns its seven, which is what its check() reads.
    # BUILT ONCE A RUN: they come from a module no fault injected here can reach,
    # and check() - which the selftest calls dozens of times - builds every file.
    if BOX_W == 1920:
        if len(_SMALL) < 2:
            small = _small()
            builders = dict((f, (b, c)) for f, b, c in small.FILES)
            texts = {}
            for base, compact in sorted(COMPACT_FILES.items()):
                builder, comment = builders[base]
                root = EU.assign(builder(), GUID_PREFIXES[compact])
                texts[compact] = EU.layout(
                    root, comment + " - compact, for a box under 1920")
            _SMALL.append(texts)
        out.update(_SMALL[1])
    return out


def xml_component_names(text):
    body = text.split("<components>", 1)[1]
    return sorted(set(re.findall(r"(?m)^\t\t<(\w+)", body)))


def xml_layer_counts(files):
    """cell name -> how many <component_image> layers it declares.

    The emitted XML and not the layer constants, because the constants are what
    a cell is BUILT from and this is the question of what it ENDED UP with -
    the same reason check 7 walks the file rather than the layout tables.
    """
    out = {}
    for text in files.values():
        body = text.split("<components>", 1)[1]
        for m in re.finditer(r"(?m)^\t\t<(\w+)\n(.*?)(?=(?m:^\t\t<)|\Z)", body, re.S):
            out[m.group(1)] = m.group(2).count("<component_image")
    return out


# Which layer each picture helper writes, read out of its own body rather than
# listed: a helper repointed at a different index has to fail here, and a list
# would just agree with whatever it was changed to.
_SLOT_CONSTS = {"ICUI.PLATE_INDEX": lambda: PLATE_INDEX,
                "ICUI.FACE_INDEX": lambda: FACE_INDEX,
                "ICUI.MASK_INDEX": lambda: MASK_INDEX}


def paint_helpers(utext):
    """helper name -> the set of layer indices its body writes with SetImagePath.

    A helper whose slot is an expression this cannot resolve is reported by the
    caller rather than skipped: an unresolved slot means the pairing below is
    not being made, and a check that quietly measures nothing is the fault it
    exists to catch.
    """
    out, unresolved = {}, []
    for m in re.finditer(r"\nfunction ICUI\.(set_\w+)\(.*?\n(.*?)\nend\n", utext, re.S):
        name, body = m.group(1), m.group(2)
        # set_rim's slots are ICUI.RIMS, read out of a table and not written as
        # a constant: check_rim_slots (1d) pairs every one of them with the
        # layers the files emit, which is this check's question asked directly.
        if name == "set_rim":
            continue
        slots = set()
        for call in re.findall(r"SetImagePath\([^,]+,\s*([^)]+?)\s*\)", body):
            call = call.strip()
            if call.isdigit():
                slots.add(int(call))
            elif call in _SLOT_CONSTS:
                slots.add(_SLOT_CONSTS[call]())
            else:
                unresolved.append((name, call))
        if slots:
            out[name] = slots
    return out, unresolved


# A PNG of our own making, read and written without PIL. Only the one shape
# this file emits is supported: 8-bit RGBA, no interlace, one IDAT. Anything else
# returns None and the check reports it rather than guessing.
def _read_png_rows(path):
    import struct
    import zlib
    raw = io.open(path, "rb").read()
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    pos, w, h, idat = 8, 0, 0, b""
    while pos + 8 <= len(raw):
        (n,) = struct.unpack(">I", raw[pos:pos + 4])
        kind = raw[pos + 4:pos + 8]
        body = raw[pos + 8:pos + 8 + n]
        if kind == b"IHDR":
            w, h, depth, colour, _c, _f, interlace = struct.unpack(">IIBBBBB", body)
            if depth != 8 or colour != 6 or interlace != 0:
                return None
        elif kind == b"IDAT":
            idat += body
        pos += 12 + n
    data = zlib.decompress(idat)
    stride = w * 4
    rows, prev = [], bytearray(stride)
    at = 0
    for _y in range(h):
        f = data[at]
        if not isinstance(f, int):
            f = ord(f)
        line = bytearray(data[at + 1:at + 1 + stride])
        at += 1 + stride
        # Only the filters this writer emits (0) and the ones a re-encoder might
        # pick are honoured; anything else is a file we did not write.
        if f == 0:
            pass
        elif f == 1:
            for i in range(4, stride):
                line[i] = (line[i] + line[i - 4]) & 0xFF
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        else:
            return None
        rows.append(bytes(line))
        prev = line
    return rows


def _write_png(path, rows):
    import struct
    import zlib
    w, h = len(rows[0]) // 4, len(rows)
    raw = b"".join(b"\x00" + r for r in rows)

    def chunk(kind, body):
        return (struct.pack(">I", len(body)) + kind + body
                + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF))

    blob = (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    io.open(path, "wb").write(blob)


def _assets():
    paths = set(EU._game_assets())
    base = os.path.join(ROOT, "Modding Files", "pack")
    for dirpath, _dirs, names in os.walk(base):
        for name in names:
            if name.lower().endswith(".png"):
                rel = os.path.relpath(os.path.join(dirpath, name), base)
                paths.add(rel.replace("\\", "/"))
    return paths


# ---------------------------------------------------------------------------
# check - each of these is a silent non-draw, not an error
# ---------------------------------------------------------------------------
def check_paint_layers(files):
    """Check 21b: every (helper, cell) pair the panel writes must have that layer."""
    out = []
    ui = os.path.join(ROOT, "Modding Files", "pack", "script", "campaign", "mod",
                      "zzz_derpy_iron_court_ui.lua")
    try:
        utext = io.open(ui, encoding="utf-8").read()
    except Exception as exc:
        return ["cannot read the panel Lua to pair its picture calls: %r" % (exc,)]

    layers = xml_layer_counts(files)
    helpers, unresolved = paint_helpers(utext)
    for name, call in unresolved:
        out.append("ICUI.%s paints a layer this cannot resolve (%s), so nothing "
                   "holds it against the cell's layer count" % (name, call))
    if not helpers:
        out.append("no picture helpers found in the panel Lua - 21b measured "
                   "nothing, which is not the same as finding nothing wrong")

    # THE CALL SITES, by cell name. Only a literal cell name can be paired -
    # a call that names its cell through a variable is counted and reported, so
    # the number of pairs this check actually made is never silently zero.
    pairs, by_var = 0, []
    for helper, slots in sorted(helpers.items()):
        for m in re.finditer(r"ICUI\.%s\(\s*[^,]+,\s*(.+?)\s*[,)]" % helper, utext):
            cell = m.group(1)
            if not (cell.startswith('"') and cell.endswith('"')):
                by_var.append((helper, cell))
                continue
            cell = cell[1:-1]
            if cell not in layers:
                out.append("ICUI.%s paints %s and no emitted file declares it"
                           % (helper, cell))
                continue
            pairs += 1
            worst = max(slots)
            if worst >= layers[cell]:
                out.append("ICUI.%s writes layer %d and %s declares %d layer(s) - "
                           "SetImagePath to a layer that is not there writes "
                           "nowhere, the pcall hides it, and the cell keeps the "
                           "default image the .twui.xml gave it"
                           % (helper, worst, cell, layers[cell]))
    if not pairs:
        out.append("21b paired no call with a cell at all - every picture call "
                   "now names its cell through a variable (%s), so this check is "
                   "measuring nothing" % (by_var[:3],))
    return out


def check():
    out = []
    # EVERY FILE for the two GUID checks, which are about files colliding with
    # each other; the BASE SEVEN for everything after them. A compact copy is
    # checked in full as the 1600 module's own file, by at_box(1600).check().
    all_files = build_xml()
    files = dict((f, t) for f, t in all_files.items()
                 if f not in COMPACT_FILES.values())

    # 1. Every GUID unique across ALL files, and paired between the two sections.
    #    A collision, or a node in <components> with no match in <hierarchy>, is a
    #    silent non-draw: no error, no log line, the widget is simply absent.
    seen = {}
    for fname, text in all_files.items():
        for guid in re.findall(r'"([0-9A-Za-z]{4}[0-9A-F]{4}-D000-4000-B[0-9A-F]{15})"', text):
            if guid in seen and seen[guid] != fname:
                out.append("GUID %s appears in %s and %s" % (guid, seen[guid], fname))
            seen[guid] = fname
        counts = {}
        for guid in re.findall(r'this="([^"]+)"', text) + re.findall(r'uniqueguid="([^"]+)"', text):
            counts[guid] = counts.get(guid, 0) + 1
        for guid, n in counts.items():
            if n < 2:
                out.append("%s: GUID %s appears once, so it is half-declared" % (fname, guid))

    # 1b. The ember emitter's particle rules. See check_fire.
    out.extend(check_fire(all_files.get(FIRE_FILE, "")))
    # 1c. The claim burst: its sprite frames exist and nothing pauses it.
    out.extend(check_burst(all_files.get(BURST_FILE, ""),
                           set(p.lower() for p in _assets())))
    # 1c2. The Governors view's pins, the holder they stand in, and every mask.
    out.extend(check_gm(all_files.get(GM_PIN_FILE, ""), all_files.get(GM_FACE_FILE, ""),
                        all_files.get("derpy_ic_panel.twui.xml", ""),
                        name_text=all_files.get(GM_NAME_FILE, ""),
                        loyal_text=all_files.get(GM_LOYAL_FILE, ""),
                        badge_text=all_files.get(GM_BADGE_FILE, "")))
    out.extend(check_masks(all_files))
    # 1c3. Every line the Governors view keeps sits on one of its plates.
    out.extend(check_gm_plates())
    # 1d. The rim layers the Lua writes are the ones the files emit.
    out.extend(check_rim_slots())
    # 1e. The rim's corners are as bright as its edges (author, 2026-09-28:
    # "the corners are not filled" on CA's rounded one).
    out.extend(check_seat_rim())
    out.extend(check_portrait_frame())
    out.extend(check_ziggurat())

    # 2. The prefix is ours, and DE15 is retired.
    for fname, text in all_files.items():
        want = GUID_PREFIXES[fname]
        for guid in re.findall(r'this="([0-9A-Za-z]{8}-)', text):
            if not guid.startswith(want):
                out.append("%s: GUID %s is outside that file's %s range"
                           % (fname, guid, want))
            if guid.startswith("DE15"):
                out.append("%s: DE15 is RETIRED and must not be reused" % fname)

    # 3. Every imagepath must exist, or it draws a blank square, silently.
    assets = _assets()
    for fname, text in files.items():
        for path in sorted(set(re.findall(r'imagepath="([^"]+)"', text))):
            if path not in assets:
                out.append("%s: imagepath not in any pack: %s" % (fname, path))

    # 4. Every interactive component needs a soundcategory, or the panel is
    #    silent. NOTE THE SHAPE: soundcategory is an attribute of the COMPONENT,
    #    while interactive="true" sits on its STATES. Testing the element that
    #    carries interactive finds <standard> and <hover> every time and reports
    #    a fault on every button in the file.
    for fname, text in files.items():
        body = text.split("<components>", 1)[1].split("</components>", 1)[0]
        blocks = re.split(r"(?m)^		(?=<\w)", body)
        for block in blocks:
            name = re.match(r"<(\w+)", block.strip())
            if not name:
                continue
            head = block.split(">", 1)[0]
            # THE LIST'S RESERVED PARTS are silent in CA's own listview template;
            # a click on one is a drag or a wheel, not a choice.
            if fname == GM_LIST_FILE and name.group(1) in GM_LIST_SILENT:
                continue
            if 'interactive="true"' in block and "soundcategory=" not in head:
                out.append("%s: %s is interactive with no soundcategory"
                           % (fname, name.group(1)))

    # 5. Text alignment must be in the engine's vocabulary. texthalign is the
    #    horizontal one and its value is "Center" - an unknown value is not an
    #    error, the label just sits somewhere nobody chose.
    legal_h = {"Left", "Centre", "Center", "Right"}
    legal_v = {"Top", "Centre", "Center", "Bottom"}
    for fname, text in files.items():
        for value in re.findall(r'texthalign="([^"]+)"', text):
            if value not in legal_h:
                out.append("%s: texthalign %r is not in the engine's vocabulary"
                           % (fname, value))
        for value in re.findall(r'textvalign="([^"]+)"', text):
            if value not in legal_v:
                out.append("%s: textvalign %r is not in the engine's vocabulary"
                           % (fname, value))

    # 6. fontcat_name must be a real category. An unknown one is not an error and
    #    not a blank: the engine falls back and every label draws at a size nobody
    #    chose. This shipped across two mods before it was noticed.
    for fname, text in files.items():
        for value in sorted(set(re.findall(r'fontcat_name="([^"]+)"', text))):
            if value not in EU.FONTCATS:
                out.append("%s: fontcat_name %r is not one the game has"
                           % (fname, value))

    # 7. Every component in the XML must be named by some layout table, or it can
    #    never draw once the hide pass walks their union.
    for fname, text in files.items():
        named = set(LAYOUT_TABLES[fname])
        roots = {"root", fname.replace(".twui.xml", "")}
        if fname == GM_LIST_FILE:
            roots |= {"list_box", "handle"}     # the List and VSlider callbacks place these
        for comp in xml_component_names(text):
            if comp not in named and comp not in roots:
                out.append("%s: component %s is named by no layout table"
                           % (fname, comp))

    # 7b. THE COLUMN'S LIST SCROLLS ONLY IF IT IS SPELLED THE WAY THE ENGINE READS:
    #     the Great Guilds' check, which caught that list shipping inert, over ours.
    if GM_LIST_FILE in files:
        import gen_guilds_ui as GG
        out += ["%s: %s" % (GM_LIST_FILE, p) for p in GG.check_scroll_parts(
            {"derpy_gg_list.twui.xml": files[GM_LIST_FILE]})]

    # 8. Headers must sit over their columns: a header x equals the row column x
    #    plus the rows_holder inset, or they float a column-width away.
    inset = ROWS_X
    pairs = [("ic_hdr_a", "ic_row_a"), ("ic_hdr_b", "ic_row_b"),
             ("ic_hdr_c", "ic_row_c"), ("ic_hdr_d", "ic_row_d"),
             ("ic_hdr_e", "ic_row_e")]
    for hdr, row in pairs:
        want = ROW_LAYOUT[row][0] + inset
        got = PANEL_LAYOUT[hdr][0]
        if got != want:
            out.append("header %s at x=%d but its column %s sits at x=%d"
                       % (hdr, got, row, want))

    # 8b. The crest cell has no header of its own, but it must not run into the
    #     first text column either - check 9 covers that below, and it now has one
    #     more column to walk.

    # 8c. Every cell that draws a PORTHOLE must share the porthole's aspect.
    #     SetImagePath gives the incoming image the CELL's size, so a mismatched
    #     box does not letterbox - it stretches the face, silently. Both cells
    #     were wrong when this check was written: the card was portrait-shaped
    #     (56x72) for a landscape source and the row was square.
    #     Each cell is checked against the art IT actually draws, which is not
    #     the same art in both places: the rows draw a PORTHOLE (landscape) and
    #     the office cards draw a UNIT CARD (tall). Checking both against one
    #     constant is how the card came to be portrait-shaped for a landscape
    #     source in the first place.
    #     Both cells draw a PORTHOLE now. ic_card_port was measured against the
    #     unit card's aspect while it drew a unit card; leaving that entry alone
    #     would have passed a 238x130 landscape cell against a 0.462 target and
    #     reported a fault on the correct layout.
    for name, box, want, what in (
            ("ic_row_port", PORT_BOX, PORTHOLE_ASPECT, "porthole"),
            ("PORT_BOX", PORT_BOX, PORTHOLE_ASPECT, "porthole"),
            ("ic_card_port", CARD_LAYOUT["ic_card_port"][2:], PORTHOLE_ASPECT,
             "porthole"),
            ("ic_party_port", PARTY_LAYOUT["ic_party_port"][2:], PORTHOLE_ASPECT,
             "porthole"),
            ("ic_leader_port", PANEL_LAYOUT["ic_leader_port"][2:],
             PORTHOLE_ASPECT, "porthole"),
            ("ic_gr_face", GM_ROW_LAYOUT["ic_gr_face"][2:], PORTHOLE_ASPECT, "porthole")):
        aspect = box[0] / float(box[1])
        drift = abs(aspect - want) / want
        if drift > PORTHOLE_TOLERANCE:
            out.append("%s is %dx%d, aspect %.3f - the %s is %.3f "
                       "(%.0f%% off, limit %.0f%%); the art will be stretched"
                       % (name, box[0], box[1], aspect, what, want,
                          drift * 100, PORTHOLE_TOLERANCE * 100))
    #     And the crest box must stay SQUARE, or the Court tab - which is nothing
    #     but crests - stretches every flag in it.
    #     The row's own crest cell is a flag as well, and a flag in a
    #     non-square box is a stretched flag.
    _cc = CARD_LAYOUT.get("ic_card_crest")
    if _cc and _cc[2] != _cc[3]:
        out.append("ic_card_crest is %dx%d; a house flag in a non-square "
                   "cell is a stretched flag" % (_cc[2], _cc[3]))
    _pc = PARTY_LAYOUT.get("ic_party_crest")
    if _pc and _pc[2] != _pc[3]:
        out.append("ic_party_crest is %dx%d; a house flag in a non-square "
                   "cell is a stretched flag" % (_pc[2], _pc[3]))
    _rc = ROW_LAYOUT.get("ic_row_crest")
    if _rc and _rc[2] != _rc[3]:
        out.append("ic_row_crest is %dx%d; a house flag in a non-square cell "
                   "is a stretched flag" % (_rc[2], _rc[3]))
    if _rc and _rc[1] + _rc[3] > ROW_H:
        out.append("ic_row_crest overruns the row: y=%d + %d > %d"
                   % (_rc[1], _rc[3], ROW_H))
    if CREST_BOX[0] != CREST_BOX[1]:
        out.append("CREST_BOX is %dx%d; mon_64.png is square and a non-square "
                   "box stretches every crest in the Court tab" % CREST_BOX)
    #     The row cell's static size is the porthole shape, because the cell is
    #     resized at runtime and this is only its resting state; but it must never
    #     be TALLER than the row it lives in.
    if ROW_LAYOUT["ic_row_port"][1] + PORT_BOX[1] > ROW_H:
        out.append("the portrait cell overruns the row: y=%d + %d > %d"
                   % (ROW_LAYOUT["ic_row_port"][1], PORT_BOX[1], ROW_H))
    if CREST_BOX[1] > ROW_H:
        out.append("the crest box is taller than the row: %d > %d"
                   % (CREST_BOX[1], ROW_H))

    # 9. No column may reach the next column's x.
    #    ic_row_f IS NOT A COLUMN. It is the Petitions tab's second button and
    #    sits over column four's tail, which that tab leaves empty and every
    #    other tab draws with ic_row_f hidden. 9b holds it to the view it is in.
    ordered = sorted(((n, v) for n, v in ROW_LAYOUT.items() if n != "ic_row_f"),
                     key=lambda kv: kv[1][0])
    for (name, (x, _y, w, _h)), (_nn, (nx, _ny, _nw, _nh)) in zip(ordered, ordered[1:]):
        if x + w > nx:
            out.append("row column %s runs from %d to %d, into the next at %d"
                       % (name, x, x + w, nx))
    # 9b. REFUSE BETWEEN THE PETITION AND ACCEPT. It must end before ACCEPT
    #     starts, and the petition column - widened on that view by ICUI.COL_W -
    #     must end before it. The width is read out of the panel Lua, at the one
    #     box it is typed for.
    _rf, _re_, _rb = ROW_LAYOUT["ic_row_f"], ROW_LAYOUT["ic_row_e"], ROW_LAYOUT["ic_row_b"]
    if _rf[0] + _rf[2] > _re_[0]:
        out.append("ic_row_f runs from %d to %d, into ACCEPT at %d"
                   % (_rf[0], _rf[0] + _rf[2], _re_[0]))
    if BOX_W == 1920:
        _m = re.search(r"petitions\s*=\s*\{\[2\]\s*=\s*(\d+)\}", io.open(os.path.join(
            ROOT, "Modding Files", "pack", "script", "campaign", "mod",
            "zzz_derpy_iron_court_ui.lua"), encoding="utf-8").read())
        if not _m:
            out.append("cannot read the petitions view's column two width out "
                       "of ICUI.COL_W")
        elif _rb[0] + int(_m.group(1)) > _rf[0]:
            out.append("the petitions view's column two runs from %d to %d, "
                       "into REFUSE at %d" % (_rb[0], _rb[0] + int(_m.group(1)),
                                              _rf[0]))

    # 9c. THE ACTION BAR'S TWO HOMES. Centred it stays under the card grid; with
    #     the pager up it moves to the left column, under the Crown's box and
    #     clear of both the box and the pager - the pager's three cells are the
    #     ones it was moved to get out of the way of.
    _pager = [PANEL_LAYOUT[n] for n in ("ic_page_prev", "ic_page_lbl", "ic_page_next")]
    _crown_bottom = PANEL_LAYOUT["ic_crown_box"][1] + PANEL_LAYOUT["ic_crown_box"][3]
    for _an in [n for n, _w in ACT_BUTTONS] + ["ic_act_hint"]:
        _ax, _ay, _aw, _ah = PANEL_LAYOUT[_an]
        if _ax < COL_R_X or _ax + _aw > COL_R_X + COL_W:
            out.append("%s spans x %d..%d, outside the card grid's %d..%d"
                       % (_an, _ax, _ax + _aw, COL_R_X, COL_R_X + COL_W))
        _px_, _py_, _pw_, _ph_ = ACT_PAGED[_an]
        if _px_ < COL_L_X or _px_ + _pw_ > COL_L_X + COL_W:
            out.append("%s with the pager up spans x %d..%d, outside the left "
                       "column's %d..%d" % (_an, _px_, _px_ + _pw_, COL_L_X,
                                            COL_L_X + COL_W))
        if _py_ < _crown_bottom:
            out.append("%s with the pager up starts at y %d, inside the Crown's "
                       "box, which ends at %d" % (_an, _py_, _crown_bottom))
        for _qx, _qy, _qw, _qh in _pager:
            if (_px_ < _qx + _qw and _qx < _px_ + _pw_
                    and _py_ < _qy + _qh and _qy < _py_ + _ph_):
                out.append("%s beside the pager spans x %d..%d and crosses the "
                           "pager at %d..%d" % (_an, _px_, _px_ + _pw_, _qx, _qx + _qw))
                break
    # AND IT IS CENTRED, to the pixel the integer arithmetic allows: the author
    # asked for exactly this, and a bar a few pixels off reads as a mistake.
    _al = PANEL_LAYOUT[ACT_BUTTONS[0][0]][0]
    _ar = PANEL_LAYOUT[ACT_BUTTONS[-1][0]][0] + PANEL_LAYOUT[ACT_BUTTONS[-1][0]][2]
    if abs((_al - COL_R_X) - (COL_R_X + COL_W - _ar)) > 1:
        out.append("the action bar spans x %d..%d and is not centred under the "
                   "grid's %d..%d" % (_al, _ar, COL_R_X, COL_R_X + COL_W))
    _pl = ACT_PAGED[ACT_BUTTONS[0][0]][0]
    _pr = ACT_PAGED[ACT_BUTTONS[-1][0]][0] + ACT_PAGED[ACT_BUTTONS[-1][0]][2]
    if abs((_pl - COL_L_X) - (COL_L_X + COL_W - _pr)) > 1:
        out.append("the action bar with the pager up spans x %d..%d and is not "
                   "centred under the Crown's box's %d..%d"
                   % (_pl, _pr, COL_L_X, COL_L_X + COL_W))

    # 10. Nothing may overflow its parent.
    last = ordered[-1]
    if last[1][0] + last[1][2] > ROW_W:
        out.append("the last row column overruns the row width")
    for name, (x, y, w, h) in PANEL_LAYOUT.items():
        if x + w > PANEL_W or y + h > PANEL_H:
            out.append("%s overflows the panel at %d,%d %dx%d" % (name, x, y, w, h))

    # 11. A component per SLICE and a crest per seat, or a party has nowhere
    #     to draw. The Lua walks 0..DIAL_SLICES-1 and 0..MAX_HOUSES-1 by name;
    #     a component short is a MoveTo on nil, which pcall swallows.
    pips = [k for k in PANEL_LAYOUT if k.startswith("ic_wedge_")]
    if len(pips) != DIAL_SLICES:
        out.append("%d wedges for a pie of %d slices" % (len(pips), DIAL_SLICES))
    #     AND EVERY WEDGE IS THE WHOLE PIE BOX. They are pictures of a shape,
    #     not of a rectangle: one declared at a size of its own is that slice
    #     squashed into a corner, with the rest of the pie perfectly correct
    #     around it.
    for name in pips:
        if PANEL_LAYOUT[name] != PIE_BOX:
            out.append("%s is %s and the pie box is %s"
                       % (name, PANEL_LAYOUT[name], PIE_BOX))
    crests = [k for k in PANEL_LAYOUT if k.startswith("ic_barc_")]
    if len(crests) != MAX_HOUSES:
        out.append("%d dial crests for %d seats" % (len(crests), MAX_HOUSES))
    #     AND EVERY CREST IS DECLARED AFTER EVERY CELL. The pie is filled now,
    #     so a crest declared first is a crest painted over by the wedge it is
    #     naming - which draws, logs nothing, and simply is not there.
    #     IN THE HIERARCHY, which is the section that says what contains what
    #     and therefore what draws over what; <components> below it is a flat
    #     list of definitions and its order means nothing.
    panel_xml = files["derpy_ic_panel.twui.xml"]
    tree = panel_xml[:panel_xml.find("</hierarchy>")]
    last_cell = tree.rfind("<ic_wedge_")
    first_crest = tree.find("<ic_barc_")
    if last_cell < 0 or first_crest < 0:
        out.append("the panel declares no pie cells or no crests at all")
    elif first_crest < last_cell:
        out.append("a crest is declared before the last pie cell, so the pie "
                   "is painted over it")
    #     AND THE RIM IS BETWEEN THEM. It is the same box as every wedge, so
    #     declared before the last of them it is painted over and the dial has
    #     no border at all - which looks exactly like art that was never
    #     written, not like a number in the wrong place.
    rim = tree.find("<ic_dial_rim")
    if rim < 0:
        out.append("the panel declares no rim, so the dial has no border")
    elif rim < last_cell:
        out.append("the rim is declared before the last pie cell, so the "
                   "wedges are painted over it")
    elif first_crest >= 0 and rim > first_crest:
        out.append("the rim is declared after a crest, so it draws over the "
                   "crests it is meant to frame")
    #     AND THE SHARE LABELS, which are on the pie exactly as the crests are.
    #     "ic_barp_00" does not start with "ic_barc_", so a check written for
    #     the crests says nothing about them.
    first_share = tree.find("<ic_barp_")
    if first_share < 0:
        out.append("the panel declares no share labels at all")
    elif first_share < last_cell:
        out.append("a share label is declared before the last pie cell, so the "
                   "pie is painted over it")
    #     AND THE PIE SITS ON NOTHING ELSE. It is 400x200 in the middle of the
    #     panel and it is opaque, so anything whose box it covers is a label
    #     nobody can read - and BOXES, not text: a 900-wide label with a short
    #     line in it is still a component reaching into the pie, and the next
    #     view to write a long line into the same cell is the one that draws
    #     under it. The rows are exempt because they are hidden on every view
    #     the pie is drawn on.
    px0, py0, pw, ph = PIE_BOX
    for name, (x, y, w, h) in sorted(PANEL_LAYOUT.items()):
        if name.startswith("ic_gm_"):
            # THE GOVERNORS VIEW'S OWN, shown on that view only: the harness
            # holds them gone on every other ("...leaving it puts both back").
            continue
        if (name.startswith("ic_wedge_") or name.startswith("ic_barc_")
                or name.startswith("ic_barp_")):
            continue
        if name.startswith("ic_div_"):
            # The walls BETWEEN the wedges, drawn among them and over them, so
            # sharing the pie's box is the whole point of where they are.
            continue
        if name == "ic_dial_rim":
            continue            # the border OF the pie, drawn over it, not under
        if name == "ic_dial_box":
            # THE PLATE THE PIE SITS ON. Sharing the pie's box is the whole of
            # what it is for, and it carries no text to be hidden. It is held
            # to its own rule in 16b instead: it must CONTAIN the rim, not
            # merely touch it.
            continue
        if name.startswith("ic_hdr_"):
            # THE STRIP IS THE ROW POOL'S, and the court has no pool - so its
            # resting place is above the pie on views that draw no pie. The
            # position that has to clear the disc is the court one, and that is
            # checked below rather than here.
            continue
        if name.startswith("ic_hsort_"):
            # ONE UNDER EACH HEADER CELL, so they live and die with the strip -
            # the same exemption as ic_hdr_ above and for the same reason: the
            # court draws no row list, so neither a label nor its arrow is on
            # screen when the pie is.
            continue
        if name.startswith("ic_plotcat_"):
            # THE INTRIGUE TAB'S COLUMN HEADERS, hidden on every view that draws
            # a pie - the same exemption and the same reason as ic_hdr_ above.
            # They sit where the row strip sits because that is where a heading
            # belongs, and the court is not one of the views they draw on.
            continue
        if name in ("ic_zig_bg", "ic_off_title"):
            # THE OFFICES TAB'S, behind its cards, and the title on its shrine.
            # The harness holds both hidden on every other view ("...no other
            # view shows it", "...on the offices tab alone").
            continue
        if name.startswith("ic_help_") and name != "ic_help":
            # THE HELP PAGE, which is a view of its own and draws no pie. The
            # harness holds every one of these hidden on the Court tab
            # ("...a second press or a tab leaves it"), which is the fact this
            # exemption rests on.
            continue
        if name.startswith(("ic_law_", "ic_lv_", "ic_gc_")):
            # THE LAWS TAB (spec 2026-10-02 laws), a view of its own that draws
            # no pie. The harness holds every one hidden off the laws view. And
            # the government cards, the doctrine picker's, which hides the pie.
            continue
        if x < px0 + pw and x + w > px0 and y < py0 + ph and y + h > py0:
            out.append("%s at %d,%d %dx%d is under the pie at %d,%d %dx%d"
                       % (name, x, y, w, h, px0, py0, pw, ph))

    # 12. A FRAME texture with no 9-slice margin repeats the whole frame across
    #     the component instead of stretching its edges. Nothing errors - it just
    #     draws a grid of little frames, which is exactly what shipped.
    for label, layers in (("panel", PANEL_LAYERS), ("card", CARD_LAYERS),
                          ("row", ROW_LAYERS), ("tab", BTN_LAYERS),
                          ("tab hover", BTN_HOVER)):
        for layer in layers:
            # BY PATH AS WELL AS BY NAME: the card frame is the Hell-Forge's
            # name holder now, and its filename says nothing about borders.
            if "border" not in layer["path"] and layer["path"] != BORDER_TEXTURE:
                continue
            if not layer.get("margin"):
                out.append("%s: frame %s has margin 0, so it repeats rather than "
                           "stretching" % (label, layer["path"]))

    # 13. Nothing may 9-slice a margin wider than half the box it fills, or the
    #     opposing corners overlap and there is no middle left to stretch.
    #     AND EVERY RIM, on the component it is drawn on (author, 2026-09-28,
    #     of the Governors tab: "there's glitches ... if there is someone in
    #     position"). The seat rim's 40px margin went onto a 61px list row, so
    #     its top and bottom slices overlapped: a red wash over the whole row
    #     and a full-strength corner block at each end. This loop only knew
    #     the panel, the card and the tabs.
    for name, layers, box in (
            ("panel", PANEL_LAYERS, (PANEL_W, PANEL_H)),
            ("card", CARD_LAYERS, (CARD_W, CARD_H)),
            ("tab", BTN_LAYERS, (132, TAB_H)),
            ("tab hover", BTN_HOVER, (132, TAB_H)),
            ("office card", OFFICE_CARD_LAYERS, (CARD_W, CARD_H)),
            ("list row", ROW_LAYERS, (ROW_W, ROW_H)),
            ("party card", PARTY_LAYERS, (PARTY_W, PARTY_H))):
        for layer in layers:
            m = layer.get("margin") or 0
            if m * 2 > min(box):
                out.append("%s: margin %d exceeds half of %dx%d"
                           % (name, m, box[0], box[1]))

    # 14. One bar colour per house, all distinct. Ten identical segments render as
    #     one undifferentiated block - it draws, and it says nothing.
    # 21. Every house has a plate on disk and it is the colour this file says.
    #     A missing plate is an imagepath that resolves to nothing, which draws a
    #     blank square and logs nothing; a STALE one is worse, because it draws
    #     the colour a house used to have.
    def _compare(path, want):
        disk = os.path.join(ROOT, "Modding Files", "pack", *path.split("/"))
        if not os.path.isfile(disk):
            out.append("missing generated art %s - run gen_ic_ui.py --write" % path)
            return
        got = _read_png_rows(disk)
        if got is None:
            out.append("%s is not a png this generator can read back" % path)
        elif got != want:
            out.append("%s on disk is not the colour gen_ic_ui.py says it is - "
                       "re-run gen_ic_ui.py --write" % path)

    # THE ART IS DRAWN AT THE BASE BOX ONLY, and the engine stretches it with
    # its component. A copy of this module at another box would redraw every
    # wedge at a scaled radius and call the shipped files stale.
    if BOX_W == 1920:
        for path, want in sorted(build_plates().items()):
            _compare(path, want)
        #     AND EVERY WEDGE, which is where a stale file actually hurts: the
        #     pie is the only thing on this panel whose SHAPE lives in a png, so
        #     one left behind from a different radius draws a smaller pie inside
        #     the right one, in the right colours, with nothing else wrong.
        for path, want in wedge_art():
            _compare(path, want)
    order = [PLATE_INDEX, FACE_INDEX, MASK_INDEX, FRAME_INDEX]
    if sorted(order) != list(range(len(FACE_LAYERS))):
        out.append("the plate/face/mask/frame layer numbers %s are not the %d "
                   "layers a face cell actually carries - a call to a layer that "
                   "is not there does nothing, silently"
                   % (order, len(FACE_LAYERS)))
    elif order != sorted(order):
        out.append("layers draw in list order, so the plate must sit under the "
                   "face, the mask over it and the frame over all - %s is not "
                   "that order" % (order,))
    elif (FACE_LAYERS[FRAME_INDEX]["path"] != FRAME_ART
          or FACE_LAYERS[FRAME_INDEX]["margin"] != FRAME_MARGIN):
        out.append("a face cell's top layer is not the portrait frame")
    # 13b. THE FRAME'S NINE-SLICE MUST FIT THE SMALLEST CELL IT LANDS ON: a
    #     list row's crest, which the Lua resizes that same cell to.
    _smallest = min(PORT_BOX + CARD_LAYOUT["ic_card_port"][2:]
                    + PARTY_LAYOUT["ic_party_port"][2:] + (36,))
    if FRAME_MARGIN * 2 > _smallest:
        out.append("the portrait frame's margin %d is over half the %dpx of the "
                   "smallest face cell" % (FRAME_MARGIN, _smallest))
    # 21c. THE SILHOUETTE MUST BE VISIBLE ON EVERY GROUND IT NOW LANDS ON.
    #     It used to have one ground - house_plate_none, an opaque box built to
    #     go behind it - and a vacant seat clears its plate to a TRANSPARENT png
    #     now, so the figure sits on whatever is behind the cell. That is two
    #     ends at once: the darkest is PLATE_BASE, which every plate fades to at
    #     its foot and which is within three levels of the office card's own
    #     art; the brightest is a house plate's lit top, where the Crown's block
    #     and a leaderless party card still draw it.
    #
    #     A SHAPE, NOT TEXT, so this is a luminance STEP and not a contrast
    #     ratio - but it is measured, and an ink chosen for one ground and
    #     silently wrong on the other is exactly what this caught.
    def _lum(rgb):
        return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]

    #     ONE OF THE TWO, NOT BOTH. An outlined figure promises that SOMETHING
    #     on it stands off the ground - the fill on a lit plate, the rim on a
    #     dark one. Demanding both would be unsatisfiable: the houses run from
    #     luminance 88 to 138 at the top and fade to 12 at the foot, and no pair
    #     of inks clears every point of that range twice over.
    _fill, _rim = _lum(SIL_INK), _lum(SIL_RIM)
    if abs(_fill - _rim) < SIL_MIN_STEP:
        out.append("the silhouette's fill %s and rim %s are %d luminance apart, "
                   "under the %d that makes an outline an outline - the figure "
                   "has no edge of its own on any ground"
                   % (SIL_INK, SIL_RIM, round(abs(_fill - _rim)), SIL_MIN_STEP))
    #     THE OFFICE CARD'S OWN ART IS NOT MEASURED HERE and is why PLATE_BASE
    #     stands in for it: it comes out of CA's ui pack, not this generator, and
    #     it read (11, 11, 10) under the 2026-09-17 preview - within three levels
    #     of PLATE_BASE, which is the darkest ground this file can produce.
    _grounds = [("the foot of every plate", PLATE_BASE)]
    for _slug, _hex in sorted(HOUSE_COLOUR.items()):
        _grounds.append(("the top of %s's plate" % _slug,
                         (int(_hex[1:3], 16), int(_hex[3:5], 16),
                          int(_hex[5:7], 16))))
    for _what, _rgb in _grounds:
        _g = _lum(_rgb)
        _step = max(abs(_fill - _g), abs(_rim - _g))
        if _step < SIL_MIN_STEP:
            out.append("neither the silhouette's fill %s nor its rim %s is more "
                       "than %d luminance from %s, under the %d a shape needs to "
                       "have an edge - an empty seat draws a figure nobody can see"
                       % (SIL_INK, SIL_RIM, round(_step), _what, SIL_MIN_STEP))

    # 21b. AND THE CELL BEING PAINTED MUST HAVE THAT LAYER. 21 holds the three
    #     indices against the layer count of a FACE cell; it says nothing about
    #     the cell any given call is aimed at, and that gap shipped: all sixteen
    #     move cards drew a white square for a whole build because
    #     ICUI.set_face - which writes layer 1, right for a porthole's
    #     plate/face/mask stack - was called on ic_plot_icon, which carries ONE
    #     layer because an icon needs neither a plate nor a mask. SetImagePath to
    #     a layer that is not there writes nowhere, the pcall swallows it, and
    #     the .twui.xml's own 1x1_blank_white default stays on screen.
    #
    #     BOTH HALVES ARE READ, neither typed: which layer each helper writes
    #     comes out of the helper's own body, and how many layers each cell has
    #     comes out of the emitted XML. A helper pointed at a new index, or a
    #     cell given fewer layers, fails here rather than on a player's screen.
    out += check_paint_layers(files)
    # 22. THE MASK SET. Every stem the panel may derive a path from has to name a
    #     file that really exists, because a derived path resolving to nothing
    #     draws a blank WHITE SQUARE over the portrait and logs nothing.
    stems = masked_portraits(quiet=True)
    if stems is None:
        out.append("the game is not installed at %s, so the mask set cannot be "
                   "verified - this check is the only thing between a derived "
                   "path and a white square on a man's face" % GAME_DATA)
    elif not stems:
        out.append("no masked portraits found at all - either the prefix %r is "
                   "wrong or the portrait folders moved" % MASK_PREFIX)
    if len(set(BAR_COLOURS)) != len(BAR_COLOURS):
        out.append("standing bar colours are not all distinct")

    # 23. EVERY INLINE ICON THE PANEL WRITES INTO A STRING. Check 3 walks the
    #     twui's imagepath attributes and check 21 the paths the Lua hands to
    #     SetImagePath; neither sees a picture named inside [[img:...]][[/img]],
    #     which is the third way this panel asks for one. A path that resolves
    #     to nothing draws nothing - the number keeps its place and loses the
    #     unit in front of it, with no error anywhere.
    _uip = os.path.join(ROOT, "Modding Files", "pack", "script", "campaign",
                        "mod", "zzz_derpy_iron_court_ui.lua")
    if not os.path.isfile(_uip):
        out.append("the panel Lua is missing, so no inline icon was checked")
    else:
        _uisrc = io.open(_uip, encoding="utf-8").read()
        # COMMENTS ARE NOT DRAWN. The block that explains the markup writes it
        # out to explain it, and a comment is the one place in this file where
        # the panel's own notation is quoted rather than used. A line-start
        # test rather than a real Lua strip: an inline icon is written by the
        # code that draws it, never trailing a statement.
        _code = [_ln for _ln in _uisrc.splitlines()
                 if not _ln.lstrip().startswith("--")]
        # EVERY ICON THE PANEL DECLARES, by the shape of its name rather than
        # one at a time. This knew about ICUI.COST_ICON alone and refused the
        # build the moment a second currency arrived: gold needed its own
        # picture, because quoting it under the standing icon is worse than
        # quoting it bare.
        _icons = dict(re.findall(r'ICUI\.(\w+_ICON)\s*=\s*"([^"]+)"', _uisrc))
        # AND EVERY ICON TABLE, one path per entry (ICUI.FX_ICONS, 2026-09-28:
        # an effect's icon is chosen by its label at draw time). Each path is
        # held to a pack like a single declaration; a line naming the table or
        # the house crest is an indirection like one naming a declared icon.
        for _t, _body in re.findall(r'ICUI\.(\w+_ICONS)\s*=\s*\{(.*?)\n\}', _uisrc, re.S):
            for _k, _p in enumerate(re.findall(r'"([^"]+\.png)"', _body)):
                _icons["%s[%d]" % (_t, _k)] = _p
        _via = ["ICUI." + _n for _n in _icons if "[" not in _n] + [
            "ICUI." + _t for _t in re.findall(r'ICUI\.(\w+_ICONS)\s*=', _uisrc)] + [
            "ICUI.crest(", "ICUI.help_icon(",
            # A government's picture is IC.GOVS[slug].icon, which its faction
            # bundle also wears: gen_iron_court's check 4b holds that path to a
            # pack and check_governments holds the two to one picture.
            "ICUI.gov_icon(",
            # A law's party crest: ICUI.crest, or the grey sigil whose pattern
            # check_law_art holds to absent_sigil_path and build_plates writes.
            "ICUI.law_crest("]
        _inline = set()
        for _ln in _code:
            for _p in re.findall(r"\[\[img:([^\]]+)\]\]", _ln):
                if _p == "%s" and any(_v in _ln for _v in _via):
                    # AN INDIRECTION, not a path. The helper wraps the markup
                    # round a path declared elsewhere in the file, so the hole
                    # is nothing to resolve - the declaration is, and it is
                    # resolved below rather than twice.
                    continue
                _inline.add(_p)
        # AND EVERY DECLARED ICON IS IN A PACK. The markup above hides these
        # from the sweep entirely, so without this an icon could be declared,
        # wrapped, drawn and absent.
        if not _icons:
            out.append("the panel Lua declares no *_ICON at all, so check 23 "
                       "is resolving nothing")
        for _n, _p in sorted(_icons.items()):
            if _p not in assets:
                out.append("ICUI.%s is in no pack: %s" % (_n, _p))
        for _p in sorted(_inline):
            if "%" in _p or not _p.lower().endswith(".png"):
                # A REGISTRY KEY or a format hole, not a path. CA has 659 keys
                # and this generator can resolve none of them, so it must not
                # pass one silently.
                out.append("inline icon %r is not a .png path this build can "
                           "verify - name the file, the way 61 vanilla rows do"
                           % _p)
            elif _p not in assets:
                out.append("inline icon is in no pack: %s" % _p)
        # AND THE TRAIT CELLS ARE ACTUALLY DECORATED. Measuring the icon into
        # those three cells above is worth nothing if the panel stopped putting
        # it there - the measurement would simply be of a wider string than the
        # one drawn, which no check would ever notice. Same shape as the
        # CUT_CELLS guard: the helper must be DECLARED and CALLED on each cell.
        if TRAIT_ICON not in assets:
            out.append("the trait icon is in no pack: %s" % TRAIT_ICON)
        _tdecl = re.search(r'ICUI\.TRAIT_ICON\s*=\s*\n?\s*"([^"]+)"', _uisrc)
        if not _tdecl:
            out.append("the panel Lua declares no ICUI.TRAIT_ICON, so the "
                       "trait cells are measured with a picture they do not "
                       "draw")
        elif _tdecl.group(1) != TRAIT_ICON:
            out.append("the trait icon here is %s and the panel Lua says %s"
                       % (TRAIT_ICON, _tdecl.group(1)))
        if not re.search(r"function\s+" + re.escape(TRAIT_FN) + r"\s*\(",
                         _uisrc):
            out.append("%s is what decorates the trait cells and the panel Lua "
                       "declares no such function" % TRAIT_FN)
        else:
            for _cell in TRAIT_CELLS:
                # THE CELL'S OWN set_text LINE has to route through the helper.
                # A substring test for the cell name alone would pass on the
                # layout table, which names all three.
                if not re.search(
                        r"set_text\([^\n]*" + re.escape(TRAIT_FN), _uisrc):
                    out.append("nothing writes a decorated trait into any cell")
                    break
            _writes = len(re.findall(
                r"set_text\([^\n]*" + re.escape(TRAIT_FN), _uisrc))
            # TWO CALL SITES, NOT THREE: t1 and t2 are written by one loop.
            if _writes < 2:
                out.append("%d trait cell(s) are written through %s and the "
                           "card has two writers for three cells"
                           % (_writes, TRAIT_FN))
        # AND THE PATH 20c MEASURES IS THE PATH THE PANEL DRAWS. 20c builds the
        # card's cost string from COST_MARKUP above; if the Lua names a
        # different file the measurement is of a string nothing draws.
        # WHETHER THE PANEL STILL DRAWS A PRICE WITH A PICTURE is not asked
        # here. The harness runs the panel and reads the string that comes
        # out, which is a stronger answer than any grep of the source, and a
        # second guard over one fact means neither of them can be seen to
        # fail. This file keeps only the part the harness cannot see.
        _decl = re.search(r'ICUI\.COST_ICON\s*=\s*"([^"]+)"', _uisrc)
        if COST_ICON not in assets:
            out.append("the cost icon is in no pack: %s" % COST_ICON)
        if not _decl:
            out.append("the panel Lua declares no ICUI.COST_ICON, so the cost "
                       "strings 20c measures are not the ones it draws")
        elif _decl.group(1) != COST_ICON:
            out.append("the cost icon differs: gen_ic_ui says %s and the panel "
                       "Lua says %s" % (COST_ICON, _decl.group(1)))
        # AND SOMETHING MUST CALL IT. A cost helper nothing reaches is the
        # request unimplemented, with every other clause here still passing.
        if not re.search(r"ICUI\.cost\(", "\n".join(
                _ln for _ln in _code if "function ICUI.cost" not in _ln)):
            out.append("no cost string calls ICUI.cost - the icon is built by "
                       "a helper the panel never asks")

    # 24. THE RIM IS A RAIL WITH FIRE INSIDE IT, and both halves are counted
    #     rather than assumed. The bound is the pie's own perimeter - one
    #     pixel of each, the whole way round - which is derived from DIAL_R
    #     rather than read off a good build, so it cannot drift into agreeing
    #     with whatever the art happens to be.
    #
    #     IT DOES NOT PROVE THE FIRE IS EVEN. A band of hot pixels bunched in
    #     one place would pass this; what it catches is the fire going out -
    #     a peak of zero, a depth of zero, a ramp cooled below the rail.
    # The rim is art, drawn at the base box only - see the drift check above.
    if BOX_W == 1920:
        _rim = rim_pixels()
        _rim_w = len(_rim[0]) // 4
        _hot = _lit = 0
        for _r in _rim:
            for _x in range(_rim_w):
                if _r[4 * _x + 3] < 40:
                    continue
                if _r[4 * _x] >= 200:
                    # Above anything on the bronze ramp, whose brightest rail is
                    # RIM_TOP at red 181 - so this counts ember and only ember.
                    _hot += 1
                elif _r[4 * _x] >= 60:
                    _lit += 1
        _perimeter = int(math.pi * DIAL_R + 2 * DIAL_R)
        if _lit < _perimeter:
            out.append("the dial has no rail: %d bronze pixels for a %d pixel edge"
                       % (_lit, _perimeter))
        if _hot < _perimeter:
            out.append("the dial carries no fire: %d ember pixels for a %d pixel "
                       "edge" % (_hot, _perimeter))

    # 25. EVERY COMPONENT THE PANEL RE-POINTS MUST OWN THE SLOT IT WRITES TO.
    #     SetImagePath(path, n) writes into image slot n of the component, and
    #     a component built with no <componentimages> has no slot at all. The
    #     call fails, the pcall every draw wraps it in eats the failure, and
    #     the component is created, moved and made visible with nothing on it.
    #
    #     THIS IS THE CHECK THE WALLS NEEDED. ic_div_* had no branch in
    #     build_xml and fell through to the text cell at the end of the chain;
    #     every other check passed, because all fifty-nine pictures were
    #     generated, packed and byte-correct - and unreachable.
    #
    #     WHAT IT CANNOT SEE: a receiver whose name is a PARAMETER, such as
    #     ICUI.set_plate(parent, name, ...), where the caller decides the
    #     component. Those are covered by check 21, which resolves the paths
    #     rather than the components.
    if os.path.isfile(_uip):
        # Blocks by component id, across every file: a card or row child is
        # re-pointed by the same call shape as a panel child.
        _blocks = {}
        for _fn, _tx in files.items():
            for _bm in re.finditer(r"(?ms)^\t\t<(\w+)\n.*?^\t\t</\1>", _tx):
                _blocks[_bm.group(1)] = _bm.group(0)

        # ICUI.<NAME>_INDEX = n, so a slot named by constant resolves too.
        _slots = dict((_m.group(1), int(_m.group(2))) for _m in
                      re.finditer(r"ICUI\.(\w+_INDEX)\s*=\s*(\d+)", _uisrc))

        # local <var> = comp("literal" | string.format("pattern", ...), parent)
        # KEPT WITH ITS POSITION, because a local belongs to the function it is
        # in and not to the file. "ic" is what three separate helpers call
        # their component - the card crest, the card portrait and the row
        # crest - and merging them held a component written at slot zero to the
        # widest slot any namesake elsewhere writes.
        #
        # AND A PARAMETERISED ASSIGNMENT POISONS THE NAME rather than
        # being invisible. The comment above has said since it was written
        # that a receiver named by a parameter is out of reach here - but
        # the pattern only matched LITERALS, so `local ic = comp(name,
        # parent)` recorded nothing at all and the nearest preceding
        # literal somewhere else in the file answered for it. ICUI.set_face
        # is that helper, and it reported ic_row_crest - a component it
        # never touches - as re-pointed at a slot it does not have.
        _codesrc = "\n".join(_code)
        _made = []
        for _m in re.finditer(r"local\s+(\w+)\s*=\s*comp\(", _codesrc):
            _lit = re.match(r'\s*(?:string\.format\(\s*)?"([^"]+)"',
                            _codesrc[_m.end():_m.end() + 160])
            _made.append((_m.start(), _m.group(1),
                          _lit.group(1) if _lit else None))

        # <var>:SetImagePath(<path>, <slot>) - the argument list is walked with
        # a depth counter rather than a regex, because ICUI.div_path(slot.from)
        # puts a bracket inside it and [^)]* stops at the wrong one.
        _src = "\n".join(_code)
        for _m in re.finditer(r"(\w+)\s*:\s*SetImagePath\(", _src):
            _var = _m.group(1)
            _i, _depth, _args, _start = _m.end(), 1, [], _m.end()
            while _i < len(_src) and _depth:
                _ch = _src[_i]
                if _ch in "([":
                    _depth += 1
                elif _ch in ")]":
                    _depth -= 1
                    if not _depth:
                        _args.append(_src[_start:_i])
                        break
                elif _ch == "," and _depth == 1:
                    _args.append(_src[_start:_i])
                    _start = _i + 1
                _i += 1
            _tail = _args[-1].strip() if len(_args) > 1 else "0"
            if _tail.isdigit():
                _slot = int(_tail)
            elif _tail.startswith("ICUI.") and _tail[5:] in _slots:
                _slot = _slots[_tail[5:]]
            else:
                # A slot this build cannot resolve. Zero is the weakest claim
                # and still catches a component carrying no pictures at all.
                _slot = 0
            # THE NEAREST PRECEDING ASSIGNMENT, which is the one in scope.
            _pat = None
            for _pos, _v, _name in _made:
                if _v == _var and _pos < _m.start():
                    _pat = _name
            if _pat is None:
                # The component came in as a parameter, so the caller decides
                # which one it is. Check 21 covers those by resolving the paths
                # instead of the components.
                continue
            _hits = ([_n for _n in _blocks if _n.startswith(_pat.split("%")[0])]
                     if "%" in _pat else
                     [_n for _n in _blocks if _n == _pat])
            if not _hits:
                out.append("the panel re-points %r and this build creates no "
                           "such component" % _pat)
            for _n in sorted(_hits):
                _have = _blocks[_n].count("<component_image")
                if _have <= _slot:
                    out.append(
                        "%s is re-pointed at image slot %d and carries %d "
                        "picture(s), so SetImagePath has nothing to write into "
                        "and the component draws nothing" % (_n, _slot, _have))

    # 24b. AND EVERY PARTY FLIES A FRAMED FLAG. The frame is CA's, laid over
    #      the field wherever the source file is not white, so the count is
    #      exact rather than a threshold: every pixel the source frames, the
    #      flag must draw. A glyph on a bare square of colour is what this
    #      panel drew before, and it reads as a missing picture beside the
    #      real faction mons the court list draws next to it.
    _frame, _field, _fbox = flag_frame()[0]
    _framed = sum(1 for _y in range(SIGIL) for _x in range(SIGIL)
                  if _field[_y][_x] == 0
                  and _frame[_y][4 * _x + 3] >= FLAG_CLEAR)
    if not _framed:
        out.append("the flag frame at %s has no frame in it - every pixel is "
                   "field or nothing" % FLAG_SRC)
    for _slug in sorted(SIGIL_SHAPE):
        _flag = sigil_pixels(_slug)
        _drawn = sum(1 for _y in range(SIGIL) for _x in range(SIGIL)
                     if _field[_y][_x] == 0
                     and _flag[_y][4 * _x + 3] >= FLAG_CLEAR)
        if _drawn != _framed:
            out.append("the %s flag draws %d of its frame's %d pixels"
                       % (_slug, _drawn, _framed))

    # 15. The whole row pool must fit between the header strip and the alert bar.
    #     These are four numbers multiplied together and it was done on paper once;
    #     a row pool that overruns draws its tail underneath the alert, where it is
    #     still interactive and still reads as part of the list.
    last_row_bottom = ROWS_Y + (VISIBLE_ROWS - 1) * ROW_PITCH + ROW_H
    alert_top = PANEL_LAYOUT["ic_alert"][1]
    if last_row_bottom > alert_top:
        out.append("%d rows at pitch %d end at %d, past the alert bar at %d"
                   % (VISIBLE_ROWS, ROW_PITCH, last_row_bottom, alert_top))
    if ROW_PITCH < ROW_H:
        out.append("row pitch %d is less than row height %d, so rows overlap"
                   % (ROW_PITCH, ROW_H))

    # 16. The pager must sit BELOW the last row and ABOVE the alert bar, and
    #     inside the panel. Overlapping the rows would put a button on top of the
    #     list's own action column; overlapping the alert would bury the line that
    #     explains why a click was refused.
    last_row_bottom_16 = ROWS_Y + (VISIBLE_ROWS - 1) * ROW_PITCH + ROW_H
    alert_top_16 = PANEL_LAYOUT["ic_alert"][1]
    for name in ("ic_page_prev", "ic_page_lbl", "ic_page_next"):
        if name not in PANEL_LAYOUT:
            out.append("no %s: the list cannot be paged" % name)
            continue
        x, y, w, h = PANEL_LAYOUT[name]
        if y < last_row_bottom_16:
            out.append("%s starts at y=%d, on top of the rows which end at %d"
                       % (name, y, last_row_bottom_16))
        if y + h > alert_top_16:
            out.append("%s runs to y=%d, into the alert bar at %d"
                       % (name, y + h, alert_top_16))
        if x + w > PANEL_W:
            out.append("%s overflows the panel" % name)
    #     And the three must not sit on each other.
    pager = sorted((PANEL_LAYOUT[n][0], PANEL_LAYOUT[n][2], n)
                   for n in ("ic_page_prev", "ic_page_lbl", "ic_page_next")
                   if n in PANEL_LAYOUT)
    for (x, w, n), (nx, _nw, _nn) in zip(pager, pager[1:]):
        if x + w > nx:
            out.append("pager %s runs from %d to %d, into the next at %d"
                       % (n, x, x + w, nx))

    # 18. A 9-slice margin must clear the ornament in the SOURCE texture, not
    #     merely fit the box. panel_back_border.png is 256x256 with a corner
    #     28px deep; sliced at 18 each corner drew a fragment and the offcut
    #     was stretched along the rails, which is a frame whose corners do not
    #     meet their own edges. Check 8 asked only about the box, so it passed
    #     this for as long as it shipped.
    #     EVERY layer list, not a hand-written three. A list left out of the
    #     tuple is a list nothing checks, and the fault this catches is not a
    #     property of any particular one of them.
    lists = sorted((n, v) for n, v in globals().items()
                   if (n.endswith("_LAYERS") or n.endswith("_HOVER"))
                   and isinstance(v, list)
                   and all(isinstance(e, dict) and "margin" in e for e in v))
    for tag, layers in lists:
        for ly in layers:
            floor = TEXTURE_MIN_MARGIN.get(ly["path"])
            if floor and 0 < ly["margin"] < floor:
                out.append("%s 9-slices %s at margin %d, inside its own %dpx "
                           "edge - the slice cuts the art and repeats the offcut"
                           % (tag, ly["path"].rsplit("/", 1)[-1],
                              ly["margin"], floor))
            # 18b. A flat centre tiled draws a seam line at every repeat.
            if ly["path"] in FLAT_CENTRE and ly.get("tile"):
                out.append("%s tiles %s, whose centre is one flat colour - "
                           "stretch it, a scaled seam samples its alpha-0 ring"
                           % (tag, ly["path"].rsplit("/", 1)[-1]))

    # 16b. THE TWO COLUMNS, and that nothing leaves the one it belongs to.
    #
    #      THIS USED TO BE A STACK, and its two rules were "the grid starts
    #      below the dial" and "the Crown's block ends above the grid". Side by
    #      side those are not merely wrong, they are INVERTED - and a check that
    #      is the opposite of the layout fails forever on correct data until
    #      somebody deletes it. What is being asked has not changed: nothing may
    #      draw on top of anything else. Only the direction has.
    _COLS = {"left": (COL_L_X, COL_L_X + COL_W),
             "right": (COL_R_X, COL_R_X + COL_W)}
    _IN_COLUMN = [
        ("ic_dial_box", "left"), ("ic_crown_box", "left"),
        ("ic_col_left", "left"), ("ic_col_right", "right"),
    ] + [(_n, "left") for _n in CROWN_CELLS]
    for _cn, _side in _IN_COLUMN:
        _cx, _cy, _cw, _ch = PANEL_LAYOUT[_cn]
        _lo, _hi = _COLS[_side]
        if _cx < _lo or _cx + _cw > _hi:
            out.append("%s spans x %d..%d and the %s column is %d..%d"
                       % (_cn, _cx, _cx + _cw, _side, _lo, _hi))
        if _cy < COL_TOP or _cy + _ch > COL_BOTTOM:
            out.append("%s spans y %d..%d and the columns run %d..%d"
                       % (_cn, _cy, _cy + _ch, COL_TOP, COL_BOTTOM))
    # AND THE DIVIDER BETWEEN THEM, touching neither: a rule that overlaps a
    # column is a rule drawn through whatever that column holds.
    _dx, _dy, _dw, _dh = PANEL_LAYOUT["ic_divider"]
    if _dx < COL_L_X + COL_W or _dx + _dw > COL_R_X:
        out.append("the divider spans x %d..%d and the gap between the columns "
                   "is %d..%d" % (_dx, _dx + _dw, COL_L_X + COL_W, COL_R_X))
    # THE COLUMNS THEMSELVES, which is the one thing the per-component loop
    # cannot see: every component could sit correctly inside a column box and
    # the two boxes still cross.
    if COL_L_X + COL_W > COL_R_X:
        out.append("the left column ends at %d and the right starts at %d"
                   % (COL_L_X + COL_W, COL_R_X))
    # COL_L_X AND NOT 18: at a 2560 box the margin is 24, and a literal read the
    # right column as running 6px past a content edge it ends exactly on.
    if COL_R_X + COL_W > COL_L_X + CONTENT_W:
        out.append("the right column ends at %d, past the content width's %d"
                   % (COL_R_X + COL_W, COL_L_X + CONTENT_W))

    _last_row_bottom = PARTIES_Y + PARTY_ROWS * PARTY_H + (PARTY_ROWS - 1) * PARTY_GAP_Y
    if _last_row_bottom > PANEL_LAYOUT["ic_page_prev"][1]:
        out.append("the party grid ends at %d and the pager starts at %d"
                   % (_last_row_bottom, PANEL_LAYOUT["ic_page_prev"][1]))
    # EVERY CARD IN THE RIGHT COLUMN. The grid is built from PARTIES_X, so this
    # is what catches an origin that has stopped agreeing with the column it is
    # meant to fill - which would put half the cards over the divider and the
    # dial, with every other number here still correct.
    for _i, (_gx, _gy) in enumerate(PARTY_GRID):
        if _gx < COL_R_X or _gx + PARTY_W > COL_R_X + COL_W:
            out.append("party card %d spans x %d..%d and the right column is "
                       "%d..%d" % (_i + 1, _gx, _gx + PARTY_W,
                                   COL_R_X, COL_R_X + COL_W))
            break
    # AND THE PLATE MUST CONTAIN THE DIAL IT IS A PLATE FOR. A box that clips
    # the rim is a frame drawn through the fire, which reads as a broken frame.
    _bx, _by, _bw, _bh = PANEL_LAYOUT["ic_dial_box"]
    if (_bx > RIM_BOX[0] or _by > RIM_BOX[1]
            or _bx + _bw < RIM_BOX[0] + RIM_BOX[2]
            or _by + _bh < RIM_BOX[1] + RIM_BOX[3]):
        out.append("ic_dial_box at %d,%d %dx%d does not contain the rim at "
                   "%d,%d %dx%d" % ((_bx, _by, _bw, _bh) + tuple(RIM_BOX)))
    # AND IT MAY NOT REACH THE CROWN'S BOX BELOW IT. The two plates are the
    # only opaque things in the left column and they are stacked, so the single
    # thing that can go wrong between them is that they touch.
    _kx, _ky, _kw, _kh = PANEL_LAYOUT["ic_crown_box"]
    if _ky < _by + _bh:
        out.append("the Crown's box starts at y=%d and the dial's plate ends "
                   "at %d" % (_ky, _by + _bh))
    if len(PARTY_GRID) != PARTY_SLOTS:
        out.append("the party grid has %d slots and PARTY_SLOTS says %d"
                   % (len(PARTY_GRID), PARTY_SLOTS))
    # EVERY CELL OF THE CROWN'S BLOCK INSIDE THE BOX THAT FRAMES IT. This
    # replaces "the leader lines must not reach the dial": they are UNDER the
    # dial now, and what they have to stay inside is the frame band of their own
    # plate - the same rule check 20f gives the party card's cells.
    for _ln in CROWN_CELLS:
        _lx, _ly, _lw, _lh = PANEL_LAYOUT[_ln]
        if (_lx < _kx + CROWN_BAND or _lx + _lw > _kx + _kw - CROWN_BAND
                or _ly < _ky + CROWN_BAND or _ly + _lh > _ky + _kh - CROWN_BAND):
            out.append("%s at %d,%d %dx%d is outside the Crown's box, or "
                       "inside its %dpx frame band"
                       % (_ln, _lx, _ly, _lw, _lh, CROWN_BAND))
    # AND THE SECTION LABEL'S COURT POSITION. It is not in PANEL_LAYOUT under
    # that name - the dispatcher moves the shared component there - so nothing
    # above reaches it, and it is the first line in the box.
    _sx, _sy, _sw, _sh = COURT_SECTION_XY
    if (_sx < _kx + CROWN_BAND or _sx + _sw > _kx + _kw - CROWN_BAND
            or _sy < _ky + CROWN_BAND or _sy + _sh > _ky + _kh - CROWN_BAND):
        out.append("the court's section label at %d,%d %dx%d is outside the "
                   "Crown's box, or inside its %dpx frame band"
                   % (_sx, _sy, _sw, _sh, CROWN_BAND))

    # 19. No text may ask for a body size the game does not have. EU.fontcat()
    #     silently rounds to the nearest real one, so a request for 14 becomes
    #     body_12 with no error anywhere - which is how a full-screen panel
    #     came to be written in 12px. Check 6 cannot see it: the category it
    #     lands on is real, just not the one asked for.
    #
    #     NOT "does this category exist" - the emitter asserts on an unknown
    #     one while building, and check() builds on its first line, so that
    #     branch could never be reached here. The reachable fault, and the
    #     one that shipped, is a size that DISAGREES with a category that is
    #     perfectly real: nothing asserts, and the engine draws the category
    #     while the layout was measured for the number.
    # OVER LAYOUT_TABLES, not over three named tables. Naming them one by one
    # meant a fifth file's styles were checked against the other four's cells
    # and reported as orphans - the check failing on correct data, which is the
    # fastest way to get a check deleted.
    _known = set()
    for _table in LAYOUT_TABLES.values():
        _known.update(_table)
    for name, (_size, _cat) in TEXT_STYLE.items():
        if name not in _known:
            out.append("TEXT_STYLE names %s, which no layout table has" % name)
    for tag, kw in ([("body", BODY), ("tabs", (TAB_TEXT["size"],
                                              TAB_TEXT["fontcat"]))]
                    + sorted(TEXT_STYLE.items())):
        size, cat = kw
        if cat.startswith("body_") and size not in EU._BODY_SIZES:
            out.append("%s text asks for size %d, which is not one of %s - "
                       "the engine will round it and draw a size nobody chose"
                       % (tag, size, EU._BODY_SIZES))
        if cat.startswith("body_") and cat != "body_%d" % size:
            out.append("%s text is size %d under category %r; they disagree"
                       % (tag, size, cat))

    # 19z. NO TWO CELLS OF A CARD MAY SHARE A PIXEL. check_plot_cells() has
    #      existed since the move card was built and the comment above
    #      PLOT_FOOT_PAD says it "refuses any overlap now, so this cannot come
    #      back" - and nothing in this file, or any other, ever called it. It
    #      could refuse nothing. This is the call, and it covers the office and
    #      party cards too, neither of which ever had one.
    out.extend(check_card_cells(CARD_LAYOUT, CARD_W, CARD_H, "office card"))
    out.extend(check_card_cells(LAW_LAYOUT, LAW_W, LAW_H, "law card"))
    out.extend(check_card_cells(LB_LAYOUT, LB_W, LB_H, "party block"))
    out.extend(check_card_cells(PARTY_LAYOUT, PARTY_W, PARTY_H, "party card"))
    out.extend(check_plot_cells())

    # 20. No card child may sit under the card's own frame band. The band is
    #     the frame layer's 9-slice margin, on all four sides, and a label
    #     drawn across it reads as a broken frame rather than as a misplaced
    #     label. This was hand-arithmetic when the margin went 18 -> 30, which
    #     is precisely why it is not hand-arithmetic any more.
    band = max([ly["margin"] for ly in CARD_LAYERS
                if ly["path"] == BORDER_TEXTURE] or [0])
    # SCALED WITH THE BOX, although the 9-slice margin itself is not. The band
    # is spacing, not a collision: measured 2026-09-24, panel_back_border.png's
    # ink reaches at most 10px in from any edge (the corner curl), so a cell 25px
    # in on a 1600 box is still 15px clear of the frame.
    # LESS ONE PIXEL: the office name spends one on each side at 1600 (see
    # COMPACT_OVERRIDES), and scaled edges round by up to one.
    if BOX_W != 1920:
        band = sc(band, BOX_W) - 1
    for name in sorted(CARD_LAYOUT):
        x, y, w, h = CARD_LAYOUT[name]
        if x < band or y < band:
            out.append("%s starts at %d,%d, inside the card's %dpx frame band"
                       % (name, x, y, band))
        if x + w > CARD_W - band or y + h > CARD_H - band:
            out.append("%s ends at %d,%d, inside the card's %dpx frame band "
                       "on a %dx%d card"
                       % (name, x + w, y + h, band, CARD_W, CARD_H))

    # 20f. THE SAME BAND ON THE PARTY CARD. It wears CARD_LAYERS, so it wears
    #      the same 9-slice margin, and a cell across it reads as a broken frame
    #      rather than as a misplaced label.
    for name in sorted(PARTY_LAYOUT):
        x, y, w, h = PARTY_LAYOUT[name]
        if x < band or y < band:
            out.append("%s starts at %d,%d, inside the party card's %dpx "
                       "frame band" % (name, x, y, band))
        if x + w > PARTY_W - band or y + h > PARTY_H - band:
            out.append("%s ends at %d,%d, inside the party card's %dpx frame "
                       "band on a %dx%d card"
                       % (name, x + w, y + h, band, PARTY_W, PARTY_H))
    #      AND NO TWO CELLS MAY OVERLAP. The office card was laid out by hand
    #      and its cells were checked against the band and against nothing else;
    #      two labels in one place is a cell drawing over a cell, which looks
    #      exactly like a cell that failed to draw.
    _cells = sorted(PARTY_LAYOUT.items())
    for _i in range(len(_cells)):
        _n1, (_x1, _y1, _w1, _h1) = _cells[_i]
        for _j in range(_i + 1, len(_cells)):
            _n2, (_x2, _y2, _w2, _h2) = _cells[_j]
            if (_x1 < _x2 + _w2 and _x2 < _x1 + _w1
                    and _y1 < _y2 + _h2 and _y2 < _y1 + _h1):
                out.append("%s and %s overlap on the party card" % (_n1, _n2))

    # 20b2. AND THE CROWN'S BOX, for the same reason and it is a newer one. Every
    #       cell on this panel used to be a full-width band at its own y, so two
    #       of them could not cross. The box has a left half and a right half now
    #       and they share every row, which is a way to be wrong that the panel
    #       has never had before.
    _kcells = sorted((n, PANEL_LAYOUT[n]) for n in CROWN_CELLS)
    _kcells.append(("ic_lbl_section", tuple(COURT_SECTION_XY)))
    for _i in range(len(_kcells)):
        _n1, (_x1, _y1, _w1, _h1) = _kcells[_i]
        for _j in range(_i + 1, len(_kcells)):
            _n2, (_x2, _y2, _w2, _h2) = _kcells[_j]
            if (_x1 < _x2 + _w2 and _x2 < _x1 + _w1
                    and _y1 < _y2 + _h2 and _y2 < _y1 + _h1):
                out.append("%s and %s overlap in the Crown's box" % (_n1, _n2))

    # 20c. EVERY STRING THIS CARD CAN DRAW MUST FIT ITS CELL. The card is a
    #      quarter of the width it was, the office names and buff lines are
    #      generated, and "Never split" clips silently - so the fit is measured
    #      here rather than eyeballed.
    #
    #      THIS IS A HEURISTIC AND IT SAYS SO: the engine's own metric is
    #      TextDimensionsForText and that needs the game running. A desktop face
    #      at the same pixel size is close but not equal - Segoe UI Black read
    #      340px where Segoe UI regular read 289px for one 50-character string -
    #      so the margin is deliberately generous and the font used is the
    #      heavier of the two.
    try:
        from PIL import Image, ImageDraw, ImageFont
        import gen_iron_court as _G
    except Exception as exc:
        out.append("cannot measure card text: %r" % (exc,))
    else:
        _fonts = {}

        def _measure(text, px):
            if px not in _fonts:
                path = None
                for cand in ("seguibl.ttf", "segoeui.ttf", "arial.ttf"):
                    p = os.path.join(os.environ.get("WINDIR", ""), "Fonts", cand)
                    if os.path.isfile(p):
                        path = p
                        break
                _fonts[px] = ImageFont.truetype(path, px) if path else None
            font = _fonts[px]
            if font is None:
                return 0
            # AN INLINE IMAGE IS A SQUARE OF THE LINE BOX, and the markup that
            # asks for it measures nothing at all. Charging the markup's own
            # characters would read ~50px for a picture that draws ~17, and
            # charging nothing would let a cost cell clip the moment it gained
            # an icon - which is exactly the change that brought this branch.
            # ascent + descent is the line box, and it is charged whole
            # because the engine's real figure is TextDimensionsForText and
            # that needs the game running.
            shown = re.sub(r"\[\[/?img[^\]]*\]\]", "", text)
            # A COLOUR TAG DRAWS NOTHING: it tints the characters between its
            # two halves and takes no width of its own (the change figures,
            # spec 2026-09-28 section 4.5, were measured as 819px of markup).
            shown = re.sub(r"\[\[/?col[^\]]*\]\]", "", shown)
            pics = len(re.findall(r"\[\[img:", text))
            width = ImageDraw.Draw(Image.new("RGB", (8, 8))).textlength(
                shown, font=font)
            # SCALED TO THE ENGINE. See GAME_FONT_WIDER: the desktop face is
            # narrower than the game's and an unscaled measurement passes strings
            # the engine then cuts. The inline picture is a line box either way.
            return width * GAME_FONT_WIDER + pics * sum(font.getmetrics())

        # 20c-help. EVERY HELP LINE FITS ITS ROW (2026-09-28). The row cuts a
        #      long line to an ellipsis, which on a help page is a rule the
        #      player never reads the end of. A {name} is a number filled at
        #      draw time and is measured as four digits, wider than any the
        #      model holds. The column's help width is read out of ICUI.COL_W,
        #      where it is typed at 1920, and scaled the way ICUI.apply_scale
        #      scales it: by its two edges. AT EVERY BOX, because the fonts step
        #      down below 1920 and the column narrows with the box.
        if True:
            _ui_src = io.open(os.path.join(
                ROOT, "Modding Files", "pack", "script", "campaign", "mod",
                "zzz_derpy_iron_court_ui.lua"), encoding="utf-8").read()
            _hm = re.search(r"^ICUI\.HELP = \{\n(.*?)^\}", _ui_src, re.S | re.M)
            if not _hm:
                out.append("cannot read ICUI.HELP out of the panel Lua, so no "
                           "help line is measured")
            else:
                _room = usable_w(PANEL_LAYOUT["ic_help_line_1"][2], "ic_help_line_1")
                _px = style("ic_help_line_1")["size"]
                _help_lines = re.findall(r'^\s*"((?:[^"\\]|\\.)*)",\s*$',
                                         _hm.group(1), re.M)
                # A PATTERN THAT MATCHES NOTHING PASSES EVERY LINE.
                if not _help_lines:
                    out.append("ICUI.HELP holds no line this check can read, so "
                               "no help line is measured")
                for _line in _help_lines:
                    # A {@name} IS A PICTURE (2026-09-29), one line box wide
                    # like any other [[img:]], and never a number.
                    _shown = re.sub(r"\{@\w+\}", "[[img:x]][[/img]]", _line)
                    _shown = re.sub(r"\{\w+\}", "9999", _shown)
                    _got = _measure(_shown, _px)
                    if _got > _room:
                        out.append("at %d: help line measures %dpx in a %dpx row: %s"
                                   % (BOX_W, _got, _room, _line[:60]))
        _built = _G.build()
        _loc = {r["key"]: r["text"] for r in _built["loc"]}
        # FIVE CELLS OF SEVEN, AND THE OTHER TWO SAY WHY. ic_card_holder and
        # ic_card_house draw a character's name off the campaign and a party
        # name rolled at run time - neither is generated here, so there is no
        # set of candidates to measure and a sample would be a guess.
        #
        # THEY ARE NOT UNCHECKED, THEY ARE CUT. ICUI.draw_offices runs both
        # through ICUI.fit_cut, which asks the engine for the real width and
        # ends on an ellipsis; check 25b below holds that call in place, because
        # a cell dropped back to set_text overflows its card silently and the
        # 2026-09-17 preview is the only thing that has ever caught it.
        _strings = {"ic_card_name": [], "ic_card_effect": [], "ic_card_need": [],
                    "ic_card_term": [], "ic_card_button": []}
        for _o in _G.OFFICES:
            _strings["ic_card_name"].append(_o["name"])
            for _w in ("office", "vacant"):
                _strings["ic_card_effect"].append(
                    _loc["derpy_ic_effects_" + _G.bundle_key(_w, _o["slug"])])
        # THE STRINGS THE PANEL DRAWS, not samples of them. These three cells
        # carried a hand-written list - "400", "Vacant", "Term ends now" - and
        # the Lua emits "400 / lvl 30", "Seat is vacant" and "Term ends this
        # turn". A sample list is a second copy of the panel's text and it had
        # drifted from the first in three cells out of five, which is the exact
        # failure this check exists to catch, one level up.
        #
        # The tier tables come out of IC.TUNE in the model Lua, because that is
        # where they live: a copy of them here would be the same drift again.
        _model = io.open(os.path.join(
            ROOT, "Modding Files", "pack", "script", "campaign", "mod",
            "zzz_derpy_iron_court.lua"), encoding="utf-8").read()

        def _tune_list(name):
            _m = re.search(name + r"\s*=\s*\{([0-9,\s]*)\}", _model)
            return [int(n) for n in re.findall(r"\d+", _m.group(1))] if _m else []

        _bars, _levels = _tune_list("tier_influence"), _tune_list("tier_rank")
        if not _bars or len(_bars) != len(_levels):
            out.append("cannot read the tier ladders out of the model Lua, so "
                       "the card's bars are unmeasured")
        # WEARING ITS ICON, because that is what the Lua draws. ICUI.cost puts
        # the same markup in front of the same number, and check 23 pins the
        # path in both files to one value.
        _strings["ic_card_need"] = [COST_MARKUP + "%d / lvl %d" % (b, r)
                                    for b, r in zip(_bars, _levels)]
        # THE OLD HOLDER'S WAIT, at its longest - read out of the model, the
        # number being IC.TUNE.renew_wait there and nowhere else.
        _wait = re.search(r"renew_wait\s*=\s*(\d+)", _model)
        if not _wait:
            out.append("cannot read renew_wait out of the model Lua, so the "
                       "card's waiting line is unmeasured")
        _strings["ic_card_term"] = [
            "Seat is vacant", "Term ends this turn",
            "%d influence - 1 turn left" % (max(_bars or [0]) * 10),
            "%d influence - %d turns left" % (max(_bars or [0]) * 10, 99),
            "Vacant - holder waits %d turns" % int(_wait.group(1) if _wait else 99),
            "Vacant - holder waits 1 turn"]
        _strings["ic_card_button"] = ["Appoint", "Dismiss"]
        for _name, _texts in sorted(_strings.items()):
            _w = usable_w(CARD_LAYOUT[_name][2], _name)
            _px = TEXT_STYLE.get(_name, BODY)[0]
            for _t in _texts:
                _got = _measure(_t, _px)
                if _got > _w:
                    out.append("%s would clip: %r measures %.0fpx at %dpx in a "
                               "%dpx cell" % (_name, _t, _got, _px, _w))

        # 20k. EVERY PETITION BUTTON'S LABEL FITS ITS BUTTON (author,
        #      2026-09-30: "button size doesnt accomodate 'make peace'"). The
        #      labels are ICUI.PETITION_BTN, read out of the panel Lua; which
        #      button each goes on is typed here, and a label this does not
        #      place is a failure rather than a label nobody measured.
        _ptext = io.open(os.path.join(
            ROOT, "Modding Files", "pack", "script", "campaign", "mod",
            "zzz_derpy_iron_court_ui.lua"), encoding="utf-8").read()
        _pblk = re.search(r"ICUI\.PETITION_BTN\s*=\s*\{(.*?)\}", _ptext, re.S)
        _pbtn = dict(re.findall(r'(\w+)\s*=\s*"([^"]+)"', _pblk.group(1))) if _pblk else {}
        if not _pbtn:
            out.append("cannot read ICUI.PETITION_BTN, so no petition button is measured")
        for _key, _label in sorted(_pbtn.items()):
            _cell = PETITION_BTN_CELL.get(_key)
            if not _cell:
                out.append("ICUI.PETITION_BTN.%s is on no known button, so %r is "
                           "unmeasured" % (_key, _label))
                continue
            _w = usable_w(ROW_LAYOUT[_cell][2], _cell)
            _px = TEXT_STYLE.get(_cell, BODY)[0]
            _got = _measure(_label, _px)
            if _got > _w:
                out.append("%s would clip: %r measures %.0fpx at %dpx on a %dpx "
                           "button" % (_cell, _label, _got, _px, _w))

        # 20g. THE PARTY CARD AND THE CROWN'S BLOCK. Every string here comes
        #      out of the model's own tables; the only two that cannot are a
        #      character's name and a faction's, which are the game's loc and
        #      not ours, so both get the same deliberately long stand-in the
        #      row check uses.
        _pmodel = io.open(os.path.join(
            ROOT, "Modding Files", "pack", "script", "campaign", "mod",
            "zzz_derpy_iron_court.lua"), encoding="utf-8").read()

        def _names_in(table_name):
            _blk = re.search(table_name + r"\s*=\s*\{(.*?)\n\}", _pmodel, re.S)
            if not _blk:
                return []
            return re.findall(r'name = "([^"]+)"', _blk.group(1))

        _party_traits = _names_in("IC.PARTY_TRAITS")
        _leader_traits = _names_in("IC.LEADER_TRAITS")
        if not _party_traits or not _leader_traits:
            out.append("cannot read the trait tables out of the model, so the "
                       "party card's trait cells are unmeasured")
        _LONG_PERSON = "Drazhoath the Ashen of Hashut"
        # THE LONGEST ROLLED NAME, built the way the model builds one. A card
        # name is spilled onto a second line at runtime by the engine's own
        # metric, so what has to fit ONE line is the longest single WORD - a
        # word cannot be split - and what has to fit TWO is the whole string.
        _heads = re.findall(r'"([^"]+)"', re.search(
            r"IC\.NAME_HEADS\s*=\s*\{(.*?)\}", _pmodel, re.S).group(1))
        _tails = re.findall(r'"([^"]+)"', re.search(
            r"IC\.NAME_TAILS\s*=\s*\{(.*?)\n\}", _pmodel, re.S).group(1))
        _rolled = ["The %s of %s" % (_h, _t) for _h in _heads for _t in _tails]
        _party_strings = {
            "ic_party_leader": [_LONG_PERSON, "No one speaks for them"],
            # DECORATED, because that is what the panel writes into them.
            "ic_party_ltrait": [TRAIT_MARKUP + _t for _t in _leader_traits],
            "ic_party_t1": [TRAIT_MARKUP + _t for _t in _party_traits],
            "ic_party_t2": [TRAIT_MARKUP + _t for _t in _party_traits],
            # THE LONGEST IT DRAWS, both figures coloured as they are after a
            # change (spec 2026-09-28 section 4.5). The old sample, "100% -
            # 100 loyalty", was shorter than the "of the court" line the panel
            # really wrote, which measured 322px in this 281px cell.
            "ic_party_nums": ["[[col:green]]100%[[/col]] share - "
                              "[[col:red]]100[[/col]] loyalty"],
            # EVERY WORD ICUI.card_mood CAN ANSWER, the Crown's three included.
            "ic_party_state": ["SECEDES 99", "SPLITS 99", "SPLINTERING",
                               "PLOTTING", "RESTLESS", "LOYAL", "SCHEMING",
                               "FEUDING", "DEMANDING", "OFFERING"],
            # THE COUNTS AT TWO DIGITS, which no court reaches for offices
            # (fourteen seats) and few reach for men or provinces.
            "ic_party_members": ["No members", "1 member", "99 members"],
            "ic_party_offices": ["No office", "1 office", "14 offices"],
            "ic_party_govs": ["No overseer", "1 overseer", "99 overseers"],
            "ic_party_trend": ["Loyalty -99 a turn", "Loyalty +99 a turn",
                               "Loyalty steady"],
        }
        for _name, _texts in sorted(_party_strings.items()):
            _w = usable_w(PARTY_LAYOUT[_name][2], _name)
            _px = TEXT_STYLE.get(_name, BODY)[0]
            for _t in _texts:
                _got = _measure(_t, _px)
                # A CUT CELL MAY OVERRUN, because the panel cuts it with the
                # engine's own metric before it draws. See CUT_CELLS, and 20h
                # below, which is what makes this exemption cost something.
                if _got > _w and _name not in CUT_CELLS:
                    out.append("%s would clip: %r measures %.0fpx at %dpx in a "
                               "%dpx cell" % (_name, _t, _got, _px, _w))
        # 20g2. THE ACTION BAR AND THE PETITIONS TAB, whose labels nothing
        #      measured: the tabs were sized by eye when they were five. The
        #      bar's labels and its hints are read out of the panel Lua, so a
        #      reworded one is measured here and not a copy of it.
        def _block_of(src, name):
            return re.search(r"%s = \{(.*?)\n\}" % re.escape(name), src,
                             re.S).group(1)

        try:
            _uisrc = io.open(os.path.join(
                ROOT, "Modding Files", "pack", "script", "campaign", "mod",
                "zzz_derpy_iron_court_ui.lua"), encoding="utf-8").read()
            _act = dict(re.findall(r'(ic_act_\w+)\s*=\s*"([^"]+)"',
                                   _block_of(_uisrc, "ICUI.ACT_LABEL")))
            _hints = re.findall(r'"([^"]+)"', _block_of(_uisrc, "ICUI.ACT_HINT"))
            _fill = re.search(r'ICUI\.FILL_LABEL\s*=\s*"([^"]+)"', _uisrc)
        except Exception as exc:
            out.append("cannot read the action bar's words out of the panel "
                       "Lua: %r" % (exc,))
        else:
            _bar = dict((_k, [_v]) for _k, _v in _act.items())
            _bar["ic_act_hint"] = _hints
            _bar["ic_tab_petitions"] = ["Petitions"]
            _bar["ic_tab_laws"] = ["Laws"]
            _bar["ic_fill"] = [_fill.group(1)] if _fill else []
            if not _fill:
                out.append("the panel Lua declares no ICUI.FILL_LABEL, so the "
                           "fill button's label is unmeasured")
            for _name in [n for n, _w in ACT_BUTTONS] + ["ic_act_hint"]:
                if not _bar.get(_name):
                    out.append("the panel Lua gives %s no words to draw" % _name)
            for _name, _texts in sorted(_bar.items()):
                # THE NARROWER OF ITS TWO HOMES: beside the pager it has less.
                _box = min(PANEL_LAYOUT[_name][2],
                           ACT_PAGED.get(_name, PANEL_LAYOUT[_name])[2])
                _w = (_box - 2 * TAB_TEXT_INSET if _name.startswith("ic_tab_")
                      else usable_w(_box, _name))
                for _t in _texts:
                    _got = _measure(_t, BODY[0])
                    if _got > _w:
                        out.append("%s would clip: %r measures %.0fpx at %dpx "
                                   "in a %dpx cell" % (_name, _t, _got,
                                                       BODY[0], _w))
        # 20h. EVERY CUT CELL IS ACTUALLY CUT. CUT_CELLS lets a cell past the
        #      measurement above, so this is the half that keeps it honest: the
        #      panel Lua has to declare the named helper AND call it on that
        #      cell. Either half alone is a green build over a clipped string.
        try:
            _cutsrc = io.open(os.path.join(
                ROOT, "Modding Files", "pack", "script", "campaign", "mod",
                "zzz_derpy_iron_court_ui.lua"), encoding="utf-8").read()
        except Exception as exc:
            out.append("cannot read the panel Lua to check its cut cells: %r"
                       % (exc,))
        else:
            for _cell, _fn in sorted(CUT_CELLS.items()):
                # A SUBSTRING TEST IS NOT A DECLARATION TEST: renaming the
                # helper to ICUI.fit_cutx still contains "function ICUI.fit_cut"
                # and the mutant survived on 2026-09-14. The open bracket is the
                # boundary.
                if not re.search(r"function\s+" + re.escape(_fn) + r"\s*\(",
                                 _cutsrc):
                    out.append("%s is exempt from 20g because %s cuts it, and "
                               "the panel Lua declares no such function"
                               % (_cell, _fn))
                elif not re.search(re.escape(_fn) + r'\(\s*comp\(\s*"'
                                   + re.escape(_cell) + r'"', _cutsrc):
                    out.append("%s is exempt from 20g because %s cuts it, and "
                               "nothing calls %s on that cell"
                               % (_cell, _fn, _fn))

        # THE NAME, ON ITS TWO LINES. Line one is narrower than line two -
        # the crest sits in front of it - so the word test uses line one's
        # width and the whole-string test uses both.
        _n1 = PARTY_LAYOUT["ic_party_name"][2] - int(float(LABEL_TX.split(",")[0]))
        _n2 = PARTY_LAYOUT["ic_party_name2"][2] - int(float(LABEL_TX.split(",")[0]))
        _npx = TEXT_STYLE["ic_party_name"][0]
        for _t in _rolled + [_LONG_PERSON]:
            for _word in _t.split(" "):
                if _measure(_word, _npx) > _n1:
                    out.append("ic_party_name cannot fit the word %r at %dpx "
                               "in %dpx, and a word cannot be split"
                               % (_word, _npx, _n1))
            if _measure(_t, _npx) > _n1 + _n2:
                out.append("ic_party_name would clip even over two lines: %r "
                           "measures %.0fpx at %dpx in %d + %d"
                           % (_t, _measure(_t, _npx), _npx, _n1, _n2))
        # AND THE TWO CONTROL LINES, which were measured by NOTHING until the
        # Crown's block moved beside them and took half the box. At full width
        # they could not clip; at 372 they can, and twui text does not wrap - it
        # stops. Both strings are built the way the panel builds them, off
        # IC.CONTROL_BANDS, so a band renamed in the model is measured here.
        _bands = getattr(_G, "CONTROL_BANDS", None)
        if not _bands:
            out.append("cannot read IC.CONTROL_BANDS, so the control lines are "
                       "unmeasured - and they are no longer full width")
        # ONE EFFECT A LINE since 2026-09-24, so every effect of every band is
        # a candidate for every effect line; and the traits wear their icon,
        # because ICUI.trait_line is what draw_leader writes now.
        _effects = [_G.effect_short(_e, _m, _i)
                    for _b in (_bands or ()) for _e, _m, _i in _b[4]]
        # EVERY LINE WEARS AN ICON NOW (2026-09-28), measured as the trait's:
        # every inline icon is drawn at the line's own height.
        _leader_strings = {
            "ic_control": [TRAIT_MARKUP + "100% of the court"],
            "ic_control_band": [TRAIT_MARKUP + _b[2] for _b in (_bands or ())],
            "ic_leader_lbl": ["The Crown"],
            "ic_leader_name": [_LONG_PERSON],
            "ic_leader_party": [TRAIT_MARKUP + _p for _p in [_LONG_PERSON] + _rolled],
            "ic_leader_trait": [TRAIT_MARKUP + _t for _t in _leader_traits],
            "ic_leader_t1": [TRAIT_MARKUP + _t for _t in _party_traits],
            "ic_leader_t2": [TRAIT_MARKUP + _t for _t in _party_traits],
        }
        for _fx in FX_KEYS:
            _leader_strings[_fx] = [TRAIT_MARKUP + _e for _e in _effects]
        # AND A BAND WITH MORE EFFECTS THAN THERE ARE LINES would drop its last
        # ones silently - the Lua writes FX_KEYS and no further.
        for _b in (_bands or ()):
            if len(_b[4]) > len(FX_KEYS):
                out.append("the band %r has %d effects and the Crown's box has "
                           "%d lines for them" % (_b[2], len(_b[4]), len(FX_KEYS)))
        # AND NO EFFECT HOLDS ", ". The loc string is the effects joined with
        # one, and the Lua splits it back on that - an effect with a comma in
        # its own text would land on two lines and push the last one off.
        for _fx_text in _effects:
            if ", " in _fx_text:
                out.append("the effect %r holds ', ', which is what the Crown's "
                           "box splits a band's effects on" % _fx_text)
        for _name, _texts in sorted(_leader_strings.items()):
            _w = PANEL_LAYOUT[_name][2] - int(float(LABEL_TX.split(",")[0]))
            _px = TEXT_STYLE.get(_name, BODY)[0]
            for _t in _texts:
                _got = _measure(_t, _px)
                if _got > _w:
                    out.append("%s would clip: %r measures %.0fpx at %dpx in a "
                               "%dpx cell" % (_name, _t, _got, _px, _w))

        # 20g3. THE SEATS COUNTER, INSIDE ITS PLATE. The format is read out of
        #       the panel Lua and filled with two-digit numbers, the widest it
        #       can draw; the room is the plate less SEATS_PAD at each end.
        try:
            _seat_fmt = re.search(
                r'comp\("ic_influence", panel\),\s*string\.format\("([^"]+)"',
                io.open(os.path.join(ROOT, "Modding Files", "pack", "script",
                                     "campaign", "mod", "zzz_derpy_iron_court_ui.lua"),
                        encoding="utf-8").read()).group(1)
        except Exception as exc:
            out.append("cannot read the seats counter's words out of the panel "
                       "Lua: %r" % (exc,))
        else:
            _t = _seat_fmt.replace("%d", "99")
            _w = usable_w(PANEL_LAYOUT["ic_influence"][2], "ic_influence")
            _px = TEXT_STYLE.get("ic_influence", BODY)[0]
            _got = _measure(_t, _px)
            if _got > _w:
                out.append("ic_influence would clip: %r measures %.0fpx at %dpx "
                           "inside a %dpx plate" % (_t, _got, _px, _w))

        # 20d. AND THE ROW CELLS, which draw the longest strings in the panel.
        #      The intrigue tab builds a line out of a plot name, a character's
        #      full name and a line of prose, and puts it in ONE cell whose width
        #      is a per-view override in the panel Lua - so the width comes from
        #      there and the strings come from the model, and neither is typed
        #      out here to be got wrong.
        _lua = os.path.join(ROOT, "Modding Files", "pack", "script", "campaign",
                            "mod", "zzz_derpy_iron_court.lua")
        _ui = os.path.join(ROOT, "Modding Files", "pack", "script", "campaign",
                           "mod", "zzz_derpy_iron_court_ui.lua")
        try:
            _mtext = io.open(_lua, encoding="utf-8").read()
            _utext = io.open(_ui, encoding="utf-8").read()
        except Exception as exc:
            out.append("cannot read the panel Lua to measure its rows: %r"
                       % (exc,))
        else:
            # THE MOVES ARE CARDS NOW, so this measures a card's cells and not
            # a row's. It used to read ICUI.COL_W's intrigue override - column
            # two widened to 1102 to hold "name - blurb" in one cell - and both
            # that override and the row are gone.
            #
            # THE NAME AND THE BLURB ARE SEPARATE CELLS, so they are separate
            # measurements: a name must fit ic_plot_name on ONE line beside its
            # icon, and a blurb must fit PLOT_BLURB_LINES lines of ic_plot_b*.
            # A blurb that needs a fourth line loses its tail silently, because
            # fit_lines has nowhere to put it - which is the fault this catches.
            # IC.TUNE, so the effect lines can be RESOLVED rather than measured
            # with their placeholders still in. "%d gold" is nine characters
            # narrower than "2500 gold", which is the difference between a card
            # that fits here and one that loses its last line in game.
            _tune = {}
            _tb = _mtext[_mtext.index("IC.TUNE = {"):]
            _tb = _tb[:_tb.index(chr(10) + "}")]
            for _k, _v in re.findall(r"(\w+)\s*=\s*(-?[\d.]+)", _tb):
                _tune[_k] = _v

            def _resolve(_expr):
                """string.format("lit" .. "lit", IC.TUNE.a, ...) -> the string.

                Deliberately not a Lua interpreter: it handles the one shape
                the moves use, and RAISES on anything else so a new shape is a
                build failure rather than a silently unmeasured card.
                """
                _lit = "".join(re.findall(r'"([^"]*)"', _expr.split(",\n")[0]
                                          if ",\n" in _expr else _expr))
                _args = re.findall(r"IC\.TUNE\.(\w+)", _expr)
                for _a in _args:
                    if _a not in _tune:
                        raise KeyError("IC.TUNE has no " + _a)
                _lit = _lit.replace("%%", "\0")
                for _a in _args:
                    _lit = _lit.replace("%d", _tune[_a], 1)
                if "%d" in _lit:
                    raise ValueError("more %d than IC.TUNE arguments: " + _lit)
                return _lit.replace("\0", "%")

            _pb = _mtext[_mtext.index("IC.PLOTS = {"):]
            _pb = _pb[:_pb.index(chr(10) + "}")]
            _plots = []
            for _chunk in re.split(chr(10) + r"    \{", _pb)[1:]:
                _n = re.search(r'name = "([^"]+)"', _chunk)
                _b = _chunk[_chunk.index("blurb"):]
                # WHAT THE CARD ACTUALLY DRAWS is the effect line and the blurb
                # in one string - fill_plot concatenates them before it calls
                # fit_lines - so that is what has to fit the four cells. Measuring
                # the blurb alone was correct until 2026-09-16 and is now an
                # under-measurement of the whole mechanical half.
                if "effect = " not in _chunk:
                    out.append("move %r has no effect line, so its card says "
                               "what it feels like and never what it does"
                               % _n.group(1))
                    _eff = ""
                else:
                    _ex = _chunk[_chunk.index("effect = "):_chunk.index("blurb")]
                    try:
                        _eff = _resolve(_ex)
                    except (KeyError, ValueError) as _exc:
                        out.append("move %r has an effect line this check "
                                   "cannot resolve (%s), so nothing measures it"
                                   % (_n.group(1), _exc))
                        _eff = ""
                _plots.append((_n.group(1),
                               (_eff + " "
                                + "".join(re.findall(r'"([^"]*)"', _b))).strip()))
            if not _plots:
                out.append("no plots found in the model - 20d measured nothing")

            _pad = int(float(LABEL_TX.split(",")[0]))
            _px = BODY[0]
            _name_w = PLOT_LAYOUT["ic_plot_name"][2] - _pad
            _line_w = PLOT_LAYOUT["ic_plot_b1"][2] - _pad
            for _n, _b in _plots:
                _got = _measure(_n, TEXT_STYLE.get("ic_plot_name", BODY)[0])
                if _got > _name_w:
                    out.append("ic_plot_name would clip: %r measures %.0fpx in "
                               "a %dpx cell" % (_n, _got, _name_w))
                # GREEDY, WHOLE WORDS - the same split ICUI.fit_lines makes.
                _lines, _cur = 1, ""
                for _w2 in _b.split():
                    _try = (_cur + " " + _w2).strip()
                    if _cur and _measure(_try, _px) > _line_w:
                        _lines, _cur = _lines + 1, _w2
                    else:
                        _cur = _try
                if _lines > PLOT_BLURB_LINES:
                    out.append("a move's blurb needs %d lines of %dpx and the "
                               "card has %d: %r"
                               % (_lines, _line_w, PLOT_BLURB_LINES, _b))
                if _measure(_cur, _px) > _line_w:
                    out.append("a word in a blurb is wider than the cell: %r"
                               % (_cur,))

            # The longest target a label can name. A house name comes out of
            # the generator; a character name cannot - CA's names are in the
            # game's own loc and a legendary lord's is the longest thing that
            # can land here, so this is a deliberately generous stand-in.
            # Read by 20e below, which measures the picker's title line.
            # CA'S LONGEST CHAOS DWARF NAME, and a deliberately generous
            # stand-in: a character's name is the game's own loc and not this
            # build's, so there is no list here to take a maximum of. Read by
            # 20j, which holds the character cell to it, and by 20e below.
            _person = "Drazhoath the Ashen of Hashut"
            _house = max([r["text"] for r in _built["loc"]
                          if r["key"].startswith("derpy_ic_house_name_")]
                         or [""], key=len)
            # 20j. THE CHARACTER CELL, WHICH NOTHING HAD EVER MEASURED.
            #      It is the widest cell on the row and the one most likely to
            #      clip since a man's TRADE was appended to his name - "Amarudz
            #      Grimtidesson, Daemonsmith" measures 406 in what was a 380px
            #      cell - and no check here ever looked at it. It carries a
            #      position name in front of all that now.
            #
            #      RE-AIMED 2026-09-17 from ic_row_c, where the kind label lived
            #      for exactly one build before it became a title.
            #
            #      FOUR CELLS, because the rebalance that made room for the
            #      title moved width BETWEEN them: what each one gave up is only
            #      defensible if something says it still fits.
            _kinds = re.findall(r'\w+ = "([^"]+)"',
                                re.search(r"ICUI\.KIND_NAME = \{([^}]*)\}",
                                          _utext).group(1))
            if not _kinds:
                out.append("cannot read ICUI.KIND_NAME out of the panel Lua, "
                           "so the character cell's titles are unmeasured")
            _title = max(_kinds or [""], key=len)
            #      A NAME MAY NEVER BE CUT, and this is the half that says so.
            #      _person is the same generous stand-in 20g uses - CA's longest
            #      Chaos Dwarf name - and the title goes in front of it because
            #      a position name is part of how the man is addressed.
            _name_w = ROW_LAYOUT["ic_row_a"][2] - _pad
            _titled = "%s %s" % (_title, _person)
            _got = _measure(_titled, _px)
            if _got + _pad > _name_w:
                out.append("the character cell would cut a man's NAME: %r "
                           "measures %.0fpx in a %dpx cell. The trade after it "
                           "is what the cut is for; the name is not"
                           % (_titled, _got, _name_w))
            #      HIS TRADE MAY BE, and only an ORDINARY row is held to the
            #      width. The longest name with the longest trade is 670px and
            #      no arrangement of this row reaches it, so asking for it would
            #      be a check that fails forever or a number tuned until it did
            #      not. The trade comes out of the model's own loc and the
            #      middle one is taken by MEASURE, not by letter count.
            _trades = sorted(
                [_r["text"] for _r in _built["loc"]
                 if _r["key"].startswith("derpy_ic_bg_name_")],
                key=lambda _s: _measure(_s, _px))
            if not _trades:
                out.append("no background names in the loc, so the character "
                           "cell's trade half is unmeasured")
            else:
                #  A COURT-SIZED NAME. Read off the author's own court in the
                #  2026-09-17 screenshot - Ghorth the Cruel, Zaul Zhufbarden,
                #  Sisuthrus Burrdrik, Tordrek Hackhart - and the longest of
                #  those is taken, so this is an ordinary row at its worst and
                #  not an average of one.
                _ord = "%s Sisuthrus Burrdrik, %s" % (
                    _title, _trades[len(_trades) // 2])
                _got = _measure(_ord, _px)
                if _got + _pad > _name_w:
                    out.append("the character cell cuts an ORDINARY row: %r "
                               "measures %.0fpx in a %dpx cell. The cut is for "
                               "the extremes; a picker that ellipsises every "
                               "row is one the player cannot choose from"
                               % (_ord, _got, _name_w))
            #      THE RANK CELL, a number again. "88" and not "99" because this
            #      face draws 8 wider than 9.
            _rank_w = ROW_LAYOUT["ic_row_c"][2] - _pad
            _got = _measure("88", _px)
            if _got + _pad > _rank_w:
                out.append("the rank cell has no room to spare: '88' measures "
                           "%.0fpx in a %dpx cell, inside the %dpx margin a "
                           "string needs behind it" % (_got, _rank_w, _pad))
            #      THE INFLUENCE CELL, whose widest string is a seat's full name
            #      behind a four-figure bar. It gave 30px to the character
            #      column and this is what says it had them to give.
            _inf = "1722 influence - %s" % max(
                [_o3["name"] for _o3 in _G.OFFICES], key=len)
            _inf_w = ROW_LAYOUT["ic_row_d"][2] - _pad
            _got = _measure(_inf, _px)
            if _got + _pad > _inf_w:
                out.append("the influence cell would clip: %r measures %.0fpx "
                           "in a %dpx cell" % (_inf, _got, _inf_w))
            #      AND THE PARTY CELL, which gave NOTHING and is the reason: the
            #      2026-09-16 rebalance funded itself out of this column and
            #      clipped every rolled party name on screen.
            _party_w = ROW_LAYOUT["ic_row_b"][2] - _pad
            _got = _measure(_house, _px)
            if _got + _pad > _party_w:
                out.append("the party cell would clip: %r measures %.0fpx in a "
                           "%dpx cell" % (_house, _got, _party_w))

            #      AND THE OFFICE CARD'S SECOND LINE, which carries a
            #      POSITION now rather than a party name. It is in CUT_CELLS and
            #      therefore exempt from 20g, which was right while it held a
            #      rolled party name that does not exist at build time - a
            #      position is one word out of ICUI.KIND_NAME and can be
            #      measured, so it is, and a kind renamed to something long is
            #      exactly the edit this is here to stop.
            _house_w = CARD_LAYOUT["ic_card_house"][2] - _pad
            _px_house = TEXT_STYLE.get("ic_card_house", BODY)[0]
            for _k in _kinds:
                _got = _measure(_k, _px_house)
                if _got + _pad > _house_w:
                    out.append("the office card's position line cannot hold %r: "
                               "%.0fpx in a %dpx cell"
                               % (_k, _got, _house_w))

            # 20k. A HEADING PLUS THE ARROW BESIDE IT, which is a different
            #      question from 20g and is why 20g did not catch it.
            #
            #      THE ARROW IS NOT TEXT. ICUI.refresh MoveTo's it to its
            #      header's x plus the MEASURED width of that header's caption,
            #      so it leaves its own cell whenever the caption is wider than
            #      the column - and the Rank column is 45px wide holding a
            #      two-digit number under a four-letter word. On 2026-09-17 that
            #      put the picker's rank arrow on top of the "I" of "Influence /
            #      Holds", with every check in this file green.
            #
            #      EVERY VIEW, because the captions differ per view: "Character"
            #      on the picker and "Province" on the governors sit in the same
            #      cell and measure differently, and it is the LONGEST of them
            #      that decides whether the arrow clears the column beside it.
            _gap = int(re.search(r"ICUI\.HSORT_GAP = (\d+)", _utext).group(1))
            _arrow_w = PANEL_LAYOUT["ic_hsort_a"][2]
            # WHICH COLUMNS SORT, off ICUI.SORTS' own `col` fields rather than
            # listed here - a column that gains a sort gains this measurement.
            _sorts = {}
            for _m in re.finditer(r"(\w+)\s*=\s*\{\s*\n(.*?)\n    \},",
                                  re.search(r"ICUI\.SORTS = \{(.*?)\n\}",
                                            _utext, re.S).group(1) or "",
                                  re.S):
                _sorts[_m.group(1)] = set(
                    int(_c) for _c in re.findall(r"col = (\d+)", _m.group(2)))
            # AND WHAT EACH VIEW WRITES IN THEM. PICK_HEADERS is a table of its
            # own - ICUI.HEADERS has no "pick" row at all - and every character
            # list shares it, which is why it is read beside the rest.
            _rows = {}
            for _tbl, _view in ((r"ICUI\.HEADERS = \{(.*?)\n\}", None),
                                (r"ICUI\.PICK_HEADERS = \{([^}]*)\}", "pick")):
                _m = re.search(_tbl, _utext, re.S)
                if not _m:
                    continue
                if _view:
                    _rows[_view] = re.findall(r'"([^"]*)"', _m.group(1))
                else:
                    for _vm in re.finditer(
                            r"(\w+)\s*=\s*\{([^}]*)\}", _m.group(1)):
                        _rows[_vm.group(1)] = re.findall(
                            r'"([^"]*)"', _vm.group(2))
            if not _rows:
                out.append("no header rows could be read out of the panel Lua, "
                           "so no heading was measured against its arrow")
            _hx = [PANEL_LAYOUT["ic_hdr_%s" % _c][0] for _c in "abcde"]
            # THE RIGHT-HAND WALL for the last column is where the row strip
            # ends, which is the action button's own right edge.
            _wall = ROW_LAYOUT["ic_row_e"][0] + ROW_LAYOUT["ic_row_e"][2]
            for _view, _caps in sorted(_rows.items()):
                # A LIST WITH NO SORT OF ITS OWN takes the picker's, which is
                # what ICUI.live_view answers for every character list.
                _cols = _sorts.get(_view, _sorts.get("pick", set()))
                for _i, _cap in enumerate(_caps[:5]):
                    # AN EMPTY CAPTION DRAWS NO ARROW - the Lua hides both - so
                    # a blank column is not a collision, it is a gap.
                    if not _cap or (_i + 1) not in _cols:
                        continue
                    _end = (_hx[_i] + _gap + _measure(_cap, TITLE[0]) + _gap
                            + _arrow_w)
                    # THE NEXT HEADING THAT SAYS ANYTHING. A blank column
                    # between two written ones is room the arrow may use, which
                    # is how the governors list gets away with a wide Loyalty
                    # heading where the picker does not.
                    _next = _wall
                    for _j in range(_i + 1, 5):
                        if _j < len(_caps) and _caps[_j]:
                            _next = _hx[_j]
                            break
                    if _end > _next:
                        out.append(
                            "the %s view's %r heading and its sort arrow run to "
                            "x=%.0f, past x=%d where the next heading starts - "
                            "the arrow is MoveTo'd past the caption, so a narrow "
                            "column cannot hold a wide word"
                            % (_view, _cap, _end, _next))

            # AND THE CATEGORY HEADINGS, which are drawn upper-case.
            for _k, _nm in PLOT_CATS:
                _got = _measure(_nm.upper(), BODY[0])
                if _got > PANEL_LAYOUT["ic_plotcat_1"][2] - _pad:
                    out.append("the column heading %r measures %.0fpx in a "
                               "%dpx column" % (_nm, _got,
                                                PANEL_LAYOUT["ic_plotcat_1"][2]))

            _office = max([_o2["name"] for _o2 in _G.OFFICES], key=len)

            # 20e. AND THE TITLE LINE, which is where the victim's name went.
            #      It is a different component from the rows and a third of
            #      their width, and it now carries the longest string the panel
            #      composes: a move, a legendary lord's full name and a price.
            _tw = PANEL_LAYOUT["ic_lbl_section"][2] \
                - int(float(LABEL_TX.split(",")[0]))
            #      READ OUT OF ICUI.pick_title, not retyped: a fit check that
            #      carries its own copy of the string measures whatever it was
            #      last told, and a reworded title is then measured in its old
            #      words - which is this very failure mode, one level up.
            #
            #      Every %s gets the longest thing that can land in one and
            #      every %d four digits, so the figure is an over-estimate on
            #      purpose. The move+victim label is itself a %s, so it is in
            #      the pool of substitutions.
            _pt = _utext[_utext.index("function ICUI.pick_title"):]
            _pt = _pt[:_pt.index("\nfunction ")]
            _widest = max([_house, _person, _office]
                          + ["%s: %s" % (_n, _person) for _n, _b in _plots],
                          key=len)

            def _fmt_calls(body):
                """(format, [argument text]) for every string.format in body.

                EVERY HOLE PAIRED WITH WHAT FILLS IT. Substituting the longest
                name in the panel for every %s was a fair over-estimate while
                every %s held a name; a cost is a %s now, and a price is not a
                long name badly guessed - it is four digits and a picture.
                """
                calls, i = [], 0
                while True:
                    j = body.find("string.format(", i)
                    if j < 0:
                        return calls
                    k = j + len("string.format(")
                    m = re.match(r'\s*"((?:[^"\\]|\\.)*)"', body[k:])
                    if not m:
                        i = k
                        continue
                    p, depth, args, cur = k + m.end(), 1, [], ""
                    while p < len(body) and depth:
                        c = body[p]
                        if c in "([{":
                            depth += 1
                        elif c in ")]}":
                            depth -= 1
                            if not depth:
                                break
                        if depth == 1 and c == ",":
                            args.append(cur)
                            cur = ""
                        else:
                            cur += c
                        p += 1
                    args.append(cur)
                    calls.append((m.group(1),
                                  [a.strip() for a in args if a.strip()]))
                    i = p + 1

            def _fill(fmt, args):
                got, n = [], 0
                for piece in re.split(r"(%[sd])", fmt):
                    if piece not in ("%s", "%d"):
                        got.append(piece)
                        continue
                    arg = args[n] if n < len(args) else ""
                    n += 1
                    if "ICUI.cost(" in arg:
                        # Four digits and the icon, which is what a price is.
                        got.append(COST_MARKUP + "9999")
                    elif piece == "%d":
                        got.append("9999")
                    else:
                        got.append(_widest)
                return "".join(got)

            _titles = [_fill(_f, _a) for _f, _a in _fmt_calls(_pt)]
            # A title with no format at all is a plain return; those are short
            # by construction, but an empty list would mean this measured
            # nothing and said so by passing.
            if not _titles:
                out.append("20e found no title strings in ICUI.pick_title")
            for _t in _titles:
                _got = _measure(_t, TEXT_STYLE.get("ic_lbl_section", BODY)[0])
                if _got > _tw:
                    out.append("ic_lbl_section would clip: %r measures %.0fpx "
                               "in a %dpx cell" % (_t, _got, _tw))

            # 20e2. AND THE PETITIONS TAB'S LABEL, which states the terms once
            #       for every row (2026-09-24). A function builds it, so no
            #       table above ever sees it; its literals are joined here and
            #       every %d is two digits, which is what the T.party_* terms
            #       it prints are.
            _pl = _utext[_utext.index("function ICUI.petitions_label"):]
            _pl = _pl[:_pl.index("\nend")]
            _plt = "".join(re.findall(r'"((?:[^"\\]|\\.)*)"', _pl))
            if "%d" not in _plt:
                out.append("20e2 found no format in ICUI.petitions_label")
            _plt = _plt.replace("%d", "99")
            _got = _measure(_plt, TEXT_STYLE.get("ic_lbl_section", BODY)[0])
            if _got > _tw:
                out.append("ic_lbl_section would clip on the Petitions tab: %r "
                           "measures %.0fpx in a %dpx cell" % (_plt, _got, _tw))

    # 24. EVERY CELL THE PANEL PAINTS AT RUNTIME MUST HAVE AN IMAGE SLOT.
    #
    #     A component with no <componentimages> has no layer zero. SetImagePath
    #     against it writes into nothing, the pcall every call site wraps it in
    #     eats the error, and the cell draws NOTHING - not a blank square, not a
    #     wrong picture, nothing at all - while every path resolves, every
    #     position is right and every other check here passes. Twenty-five
    #     dividing walls shipped that way, and the Crown's portrait was about to.
    #
    #     The three helpers that paint a cell all take its name as a LITERAL at
    #     every call site, so the set of painted names is readable off the Lua
    #     without running it.
    try:
        _uisrc2 = io.open(os.path.join(
            ROOT, "Modding Files", "pack", "script", "campaign", "mod",
            "zzz_derpy_iron_court_ui.lua"), encoding="utf-8").read()
    except Exception as exc:
        out.append("cannot read the panel Lua to check its image cells: %r"
                   % (exc,))
    else:
        # A LOOPED NAME - "ic_lb_face_" .. k, or string.format("ic_x_%d", i) -
        # is a FAMILY: every declared cell with that prefix and a number after
        # it is painted, and a prefix that declares none is the fault itself.
        _painted = set()
        _families = set()
        for _pm in re.finditer(
                r'ICUI\.set_(?:face|crest|plate)\(\s*[\w.]+\s*,\s*'
                r'(?:string\.format\(\s*)?"([^"]+)"(\s*\.\.)?', _uisrc2):
            if _pm.group(2) or "%" in _pm.group(1):
                _families.add(_pm.group(1).split("%")[0])
            else:
                _painted.add(_pm.group(1))
        if not _painted:
            out.append("check 24 found no painted cells at all, so it is "
                       "checking nothing")
        # THE BASE SEVEN, as every check after the GUID ones reads. The compact
        # copies come from a separate module that an injected fault here does
        # not reach, so reading them too hid the fault this check exists for.
        _built_xml = files
        _has_images = {}
        for _fname, _text in _built_xml.items():
            _body = _text.split("<components>", 1)[1]
            # One block per component, opened by a tab-tab tag at the top level.
            for _chunk in re.split(r"(?m)^\t\t<", _body)[1:]:
                _cname = re.match(r"(\w+)", _chunk)
                if _cname:
                    _has_images[_cname.group(1)] = ("<componentimages"
                                                    in _chunk)
        for _fam in sorted(_families):
            _kin = [_n for _n in _has_images
                    if _n.startswith(_fam) and _n[len(_fam):].isdigit()]
            if not _kin:
                out.append("the panel paints %s<n> and no built file declares "
                           "one" % _fam)
            _painted.update(_kin)
        for _name in sorted(_painted):
            if _name not in _has_images:
                out.append("the panel paints %s and no built file declares it"
                           % _name)
            elif not _has_images[_name]:
                out.append("the panel paints %s but it has no "
                           "<componentimages> - SetImagePath writes nowhere "
                           "and the pcall hides it" % _name)

    # 17. The opener must carry a glyph, on EVERY state it has. Two generic
    #     plates and nothing else is a featureless disc: correct, drawn, the
    #     right size, every path resolving - and unfindable on a strip where both
    #     neighbours are marked. A glyph present on standard but not on hover is
    #     worse than none, because it vanishes under the cursor.
    plates = {PLATE % s for s in ("underlay", "active", "hover", "inactive")}
    for state, layers in (("standard", OPENER_LAYERS), ("hover", OPENER_HOVER)):
        glyphs = [ly["path"] for ly in layers if ly["path"] not in plates]
        if not glyphs:
            out.append("the opener's %s state is bare plate with no icon, so "
                       "nothing on the strip identifies it" % state)
            continue
        #     And it must be inset, not stretched over the whole button: a glyph
        #     at full size covers the plate it is meant to sit on.
        for ly in layers:
            if ly["path"] in glyphs and (ly["dw"] >= 0 or ly["dh"] >= 0):
                out.append("the opener's %s glyph %s is not inset (dw=%s dh=%s), "
                           "so it covers the button plate"
                           % (state, ly["path"].rsplit("/", 1)[-1],
                              ly["dw"], ly["dh"]))

    # 21. And every image path the PANEL sets at runtime. Check 3 walks the
    #     .twui.xml, which is every layer authored at build time and nothing the
    #     Lua swaps in later - the lit tab, the masks, the plates. A path that
    #     does not resolve draws a blank square with no error and no log line,
    #     so a typo in a CA texture name is invisible until somebody looks at
    #     the panel.
    try:
        _utext = io.open(os.path.join(
            ROOT, "Modding Files", "pack", "script", "campaign", "mod",
            "zzz_derpy_iron_court_ui.lua"), encoding="utf-8").read()
    except Exception as exc:
        out.append("cannot read the panel Lua to check its image paths: %r"
                   % (exc,))
    else:
        for path in sorted(set(re.findall(r'"(ui/[^"]*\.png)"', _utext))):
            # A FORMAT STRING IS NOT A PATH. The wedges are named
            # "ui/derpy_ic/wedge_%02d_%s.png" and filled in at draw time; the
            # 1560 paths that come out of it are checked one by one by
            # import_iron_court.py, against art_paths(), which is the list this
            # file actually writes.
            if "%" in path:
                continue
            if path not in assets:
                out.append("the panel Lua sets an imagepath not in any pack: %s"
                           % path)

    # 22. THE TWO HOUSE LISTS ARE ONE LIST, and nothing made them agree. This
    #     file's HOUSES comes from gen_iron_court.py and the model's comes from
    #     the Lua, and every colour, bar segment and loc key here is positional:
    #     a house added to one list and not the other shifts every colour after
    #     it and leaves a house with no rows at all. Neither generator reads the
    #     other's list, so the drift is silent in both.
    try:
        _mtext2 = io.open(os.path.join(
            ROOT, "Modding Files", "pack", "script", "campaign", "mod",
            "zzz_derpy_iron_court.lua"), encoding="utf-8").read()
    except Exception as exc:
        out.append("cannot read the model Lua to check its house list: %r"
                   % (exc,))
    else:
        _m = re.search(r"IC\.PARTIES\s*=\s*\{(.*?)\n\}", _mtext2, re.S)
        if not _m:
            out.append("cannot find IC.PARTIES in the model Lua")
        else:
            _lua_parties = re.findall(r'"([a-z0-9_]+)"', _m.group(1))
            _py_parties = [p[0] for p in IC.PARTIES]
            if _lua_parties != _py_parties:
                out.append("the party lists disagree - the model Lua has %r "
                           "and the generator %r; every bar colour is "
                           "positional" % (_lua_parties, _py_parties))
        _m = re.search(r"IC\.ORIGINS\s*=\s*\{(.*?)\n\}", _mtext2, re.S)
        if not _m:
            out.append("cannot find IC.ORIGINS in the model Lua")
        else:
            _lua_origins = re.findall(r'slug\s*=\s*"([a-z0-9_]+)"', _m.group(1))
            _py_origins = [h[0] for h in IC.ORIGINS]
            if _lua_origins != _py_origins:
                for _s in sorted(set(_py_origins) - set(_lua_origins)):
                    out.append("the generator has an origin the model Lua does "
                               "not: %s" % _s)
                for _s in sorted(set(_lua_origins) - set(_py_origins)):
                    out.append("the model Lua has an origin the generator does "
                               "not: %s" % _s)
        # THE ONE THAT ACTUALLY DRIFTED. Both files carry the office list, and
        # only the generator's affinities were repointed at the parties - so the
        # model went on paying the doubled appointment to a house that no longer
        # existed, which is a rule silently not applying rather than an error.
        _m = re.search(r"IC\.OFFICES\s*=\s*\{(.*?)\n\}", _mtext2, re.S)
        if not _m:
            out.append("cannot find IC.OFFICES in the model Lua")
        else:
            _lua_aff = dict(re.findall(
                r'slug\s*=\s*"([a-z_]+)"\s*,\s*affinity\s*=\s*"([a-z_]+)"',
                _m.group(1)))
            _py_aff = dict((o["slug"], o["affinity"]) for o in IC.OFFICES)
            for _k in sorted(set(_py_aff) | set(_lua_aff)):
                if _lua_aff.get(_k) != _py_aff.get(_k):
                    out.append("office %s is owed to %s in the model Lua and to "
                               "%s here" % (_k, _lua_aff.get(_k), _py_aff.get(_k)))
            _lua_tier = dict((a, int(b)) for a, b in re.findall(
                r'slug\s*=\s*"([a-z_]+)"[^}]*tier\s*=\s*(\d)', _m.group(1)))
            _py_tier = dict((o["slug"], o["tier"]) for o in IC.OFFICES)
            for _k in sorted(set(_py_tier) | set(_lua_tier)):
                if _lua_tier.get(_k) != _py_tier.get(_k):
                    out.append("office %s is tier %s in the model Lua and %s "
                               "here" % (_k, _lua_tier.get(_k), _py_tier.get(_k)))

        _m = re.search(r"IC\.BACKGROUNDS\s*=\s*\{(.*?)\n\}", _mtext2, re.S)
        if not _m:
            out.append("cannot find IC.BACKGROUNDS in the model Lua")
        else:
            _lua_bg = set(re.findall(r'"([a-z0-9_]+)"', _m.group(1)))
            _lua_bg -= set(_py_parties)
            _py_bg = set(b for _p, b, _d in IC.backgrounds())
            for _s in sorted(_py_bg - _lua_bg):
                out.append("the generator has a background the model Lua does "
                           "not: %s" % _s)
            for _s in sorted(_lua_bg - _py_bg):
                out.append("the model Lua has a background with no trait "
                           "behind it: %s" % _s)

    out += check_law_text()
    return out


_MEASURE_FONTS = {}


def measure_text(text, px):
    """20c's measure, for checks outside check(): Segoe UI Black at px, markup
    charged as it draws (an inline picture a line box square, a colour tag
    nothing), scaled by GAME_FONT_WIDER to the engine."""
    from PIL import Image, ImageDraw, ImageFont
    if px not in _MEASURE_FONTS:
        path = None
        for cand in ("seguibl.ttf", "segoeui.ttf", "arial.ttf"):
            p = os.path.join(os.environ.get("WINDIR", ""), "Fonts", cand)
            if os.path.isfile(p):
                path = p
                break
        _MEASURE_FONTS[px] = ImageFont.truetype(path, px) if path else None
    font = _MEASURE_FONTS[px]
    if font is None:
        return 0
    shown = re.sub(r"\[\[/?(img|col)[^\]]*\]\]", "", text)
    pics = len(re.findall(r"\[\[img:", text))
    width = ImageDraw.Draw(Image.new("RGB", (8, 8))).textlength(shown, font=font)
    asc, desc = font.getmetrics()
    return (width + pics * (asc + desc)) * GAME_FONT_WIDER


# 20k. EVERY STRING THE LAWS TAB CAN DRAW FITS ITS CELL (plan 2026-10-02 laws,
#      Task 10). The preview drew the card's effect lines leaving the card and a
#      man's name running into the next face, and nothing here had measured
#      either. The words come out of the generator's own loc and the model's
#      own tables; the panel's format strings are copied, so each copy is first
#      asserted to be IN the panel Lua - a reworded one fails here rather than
#      being measured stale. The one string with no source is a man's forename,
#      which is the game's loc: _LONG_FORE is the longest in the demo roster.
_LONG_FORE = "Mulagunnar"


def check_law_text():
    out = []
    mod = os.path.join(ROOT, "Modding Files", "pack", "script", "campaign", "mod")
    ui = io.open(os.path.join(mod, "zzz_derpy_iron_court_ui.lua"), encoding="utf-8").read()
    model = io.open(os.path.join(mod, "zzz_derpy_iron_court.lua"), encoding="utf-8").read()

    def need(*fmts):
        for f in fmts:
            if f not in ui:
                out.append("20k measures %r and the panel Lua no longer writes it" % f)

    # NO FONT, NO MEASURE: measure_text answers 0 and every string would "fit".
    if measure_text("M", 18) == 0:
        out.append("20k cannot measure: no Segoe UI Black, Segoe UI or Arial in the Windows fonts")
    loc = dict((r["key"], r["text"]) for r in IC.build()["loc"])
    pic = "[[img:x]][[/img]]"
    names, cats = {}, {}
    for cat, _n, _i, options in IC.LAWS:
        cats[cat] = loc["derpy_ic_law_cat_" + cat]
        for o in options:
            names[(cat, o[0])] = loc["derpy_ic_law_name_%s_%s" % (cat, o[0])]
    shorts = dict((k, [p.strip() for p in loc.get("derpy_ic_effects_derpy_ic_law_%s_%s" % k,
                                                       "").split(",") if p.strip()])
                  for k in names)
    fx = [loc.get("derpy_ic_law_fx%d_%s_%s" % (i, c, o), "") for (c, o) in names
          for i in (1, 2, 3)]
    heads = re.findall(r'"([^"]+)"', re.search(r"IC\.NAME_HEADS\s*=\s*\{(.*?)\}",
                                                model, re.S).group(1))
    tails = re.findall(r'"([^"]+)"', re.search(r"IC\.NAME_TAILS\s*=\s*\{(.*?)\n\}",
                                                model, re.S).group(1))
    party = max(("%s of %s" % (h, t) for h in heads for t in tails), key=len)
    verdicts = re.findall(r'\] = "([^"]+)"', re.search(r"ICUI\.LAW_VERDICT = \{(.*?)\n\}",
                                                       ui, re.S).group(1))
    levels = re.findall(r'"([^"]+)"', re.search(r"ICUI\.LAW_LEVEL = \{([^}]*)\}",
                                                 ui).group(1))
    tune = dict((k, int(v)) for k, v in re.findall(
        r"(law_\w+_cost|law_vote_turns)\s*=\s*(\d+)", model))
    push = [int(n) for n in re.findall(r"\d+", re.search(
        r"law_push_cost\s*=\s*\{([^}]*)\}", model).group(1))]
    big = max(push + [tune["law_overrule_cost"], tune["law_propose_cost"]])

    need("Vote open: %d turn%s", "The old way", "For [[img:%s]][[/img]]   Against [[img:%s]][[/img]]",
         "In force: %s.", "None. This is the old way.", " (absent)",
         "[[img:%s]][[/img]]%s: %s", "and %d more parties",
         "Aye %d%%  -  Nay %d%%  -  %d%% would abstain", "Nobody at court has influence to vote.",
         "Vote open: %s.",
         "Proposing costs [[img:%s]][[/img]]%d of your men's influence.",
         "Go to the vote", "Proposed by ", "%d turn%s left", "Back to the laws",
         "Aye %d%%  (%d)", "Abstaining %d%%", "Nay %d%%  (%d)", "The Crown's side",
         "and %d more parties, %d influence", "Won over by you", "Votes for ",
         "enacting it", "keeping the law in force", "%d influence", "Win: [[img:%s]][[/img]]%d",
         "+%d more", " (paid)", "%s [[img:%s]][[/img]]%d", "Pass now", "Fail now",
         "%d parties, %d influence", ". A party with no stake votes with you only from ")
    every = list(names.values())
    # SPLIT OVER TWO CELLS by ICUI.fit_two / fit_lines: as much as the first
    # holds, the rest on the second, which must hold it.
    two = {"ic_law_name": every,
           "ic_law_p_fx1": fx + ["None. This is the old way."]}
    strings = {
        "ic_law_fx1": [s for v in shorts.values() for s in v] + ["No effects"],
        "ic_law_foot": ["In force", "The old way", "Vote open: 99 turns",
                        "For %s   Against %s" % (pic, pic)],
        "ic_law_head_1": [c.upper() for c in cats.values()],
        "ic_law_p_name": every,
        "ic_law_p_sub": ["In force: %s." % n for n in every],
        "ic_law_p_for": [pic + party + " (absent)"],
        "ic_law_p_now": ["Aye 100%  -  Nay 100%  -  100% would abstain",
                         "Nobody at court has influence to vote."],
        "ic_law_p_line1": ["%s%s: %s" % (pic, party, v) for v in verdicts]
                          + ["and 99 more parties"],
        "ic_law_p_price": ["Vote open: %s." % n for n in every]
                          + ["Proposing costs %s%d of your men's influence."
                             % (pic, tune["law_propose_cost"])],
        "ic_law_p_btn": ["Propose", "Go to the vote", "Short %d" % big, "Take a side",
                         "Laws are off", "Vote open", "In force", "Not now"],
        "ic_lv_name": every,
        "ic_lv_fx": [", ".join(v) for v in shorts.values()],
        "ic_lv_by": ["Proposed by " + party, "Proposed by you"],
        "ic_lv_turns": ["99 turns left"],
        "ic_lv_back": ["Back to the laws"],
        "ic_lv_aye": ["Aye 100%  (99999)"], "ic_lv_abs": ["Abstaining 100%"],
        "ic_lv_nay": ["Nay 100%  (99999)"],
        "ic_lv_shead_1": ["Enact " + n for n in every], "ic_lv_shead_2": ["Keep " + n for n in every],
        "ic_lv_stag_1": ["The Crown's side"],
        "ic_lv_smore_1": ["and 9 more parties, 99999 influence"],
        "ic_lv_abstain": ["Abstaining: %s. A party with no stake votes with you only from %d loyalty."
                          % (w, 100) for w in ("%s (99999), %s (99999)" % (party, party),
                                               "9 parties, 99999 influence")],
        "ic_lv_st_1": ["Support", "Oppose", "Abstain"],
        "ic_lv_sideh": ["Your side"], "ic_lv_supph": ["Your support"],
        "ic_lv_overh": ["Decide it now"],
        "ic_lv_lvl_1": ["%s (paid)" % b for b in ("Slightly favour", "Strongly favour", "Fully push")]
                       + ["%s %s%d" % (b, pic, big) for b in ("Slightly favour", "Strongly favour",
                                                              "Fully push")],
        "ic_lv_over_1": ["%s %s%d" % (w, pic, tune["law_overrule_cost"]) for w in ("Pass now", "Fail now")],
        "ic_lb_name": [party],
        "ic_lb_level": ["Won over by you", "Votes for enacting it",
                        "Votes for keeping the law in force"]
                       + ["%s %s  x9.9" % (l[0].upper() + l[1:], what) for l in levels
                          for what in ("enacting it", "keeping the law in force")],
        "ic_lb_man_1": [_LONG_FORE],
        "ic_lb_inf_1": ["9999 influence"],
        "ic_lb_win_1": ["Win: %s%d" % (pic, 9999)],
        "ic_lb_more": ["+99 more"], "ic_lb_total": ["99999"],
    }
    # THE GOVERNMENT CARDS (2026-10-03, design A): every government's words in
    # its card's cells, and the refusals the button can wear.
    govs = re.findall(r'"(\w+)"', re.search(r"IC\.GOV_ORDER = \{([^}]*)\}", model).group(1))
    gname = [loc["derpy_ic_doctrine_name_" + g] for g in govs]
    grule = [loc["derpy_ic_doctrine_rule_" + g] for g in govs]
    gfx = [loc["derpy_ic_effects_derpy_ic_doctrine_" + g] for g in govs]
    gtune = dict((k, int(v)) for k, v in re.findall(r"(gov_force_\w+)\s*=\s*(-?\d+)", model))
    need("Choose  [[img:%s]][[/img]]%d", 'string.format("%+d  ", h[2])', "Nobody at court",
         "ICUI.cut_text(c, name, room)",
         '"NOW: "', '"Its rule"', '"Effect"', '"Loyalty"')
    strings.update({
        # THE OFFICES TAB'S TITLE ON THE ZIGGURAT, the panel's own words.
        "ic_off_title": [re.search(r'ICUI\.OFFICES_TITLE = "([^"]+)"', ui).group(1)],
        "ic_gc_now": ["NOW: " + n.upper() for n in gname],
        "ic_gc_nowrule": ["%s  %s" % (r, f) for r, f in zip(grule, gfx)],
        "ic_gc_ruleh_1": ["Its rule"], "ic_gc_fxh_1": ["Effect"], "ic_gc_loyh_1": ["Loyalty"],
        "ic_gc_fx_1": gfx + ["None"],
        # THE NAME IS CUT (ICUI.cut_text), never the number: what must fit is
        # the number, the crest and the first word with its three dots.
        "ic_gc_loy_1_1": ["%+d  %s%s..." % (gtune[k], pic, party.split()[0])
                          for k in ("gov_force_gain", "gov_force_loss")] + ["Nobody at court"],
        "ic_gc_btn_1": ["Choose  %s%d" % (pic, gtune["gov_force_cost"]), "Running 99", "Rest 99",
                        "Rebel", "Player", "Wait 99", "Short", "No"],
    })
    two["ic_gc_name_1"] = gname
    # SPLIT OVER GC_RULE_LINES CELLS by ICUI.fit_lines: greedy, as the Lua does.
    name = "ic_gc_rule_1_1"
    w, px = usable_w(PANEL_LAYOUT[name][2], name), TEXT_STYLE.get(name, BODY)[0]
    for t in grule:
        words, lines = t.split(), 0
        while words:
            i = len(words)
            while i > 1 and measure_text(" ".join(words[:i]), px) > w:
                i -= 1
            words, lines = words[i:], lines + 1
        if lines > GC_RULE_LINES:
            out.append("%s would clip: %r needs %d lines at %dpx in %dpx, it has %d"
                       % (name, t, lines, px, w, GC_RULE_LINES))
    for name, texts in sorted(strings.items()):
        box = PANEL_LAYOUT.get(name) or LAW_LAYOUT.get(name) or LB_LAYOUT.get(name)
        if not box:
            out.append("20k measures %s and no layout holds it" % name)
            continue
        w = usable_w(box[2], name)
        px = TEXT_STYLE.get(name, BODY)[0]
        for t in texts:
            got = measure_text(t, px)
            if got > w:
                out.append("%s would clip: %r measures %.0fpx at %dpx in a %dpx cell"
                           % (name, t, got, px, w))
    for name, texts in sorted(two.items()):
        box = PANEL_LAYOUT.get(name) or LAW_LAYOUT.get(name)
        w = usable_w(box[2], name)
        px = TEXT_STYLE.get(name, BODY)[0]
        for t in texts:
            words = t.split()
            fits = not words
            for i in range(len(words), 0, -1):
                if measure_text(" ".join(words[:i]), px) <= w:
                    fits = measure_text(" ".join(words[i:]), px) <= w
                    break
            if not fits:
                out.append("%s would clip over its two lines: %r at %dpx in %dpx"
                           % (name, t, px, w))
    return out


def write_ui(outdir=None):
    outdir = outdir or os.path.join(ROOT, "Modding Files", "pack", "ui", "campaign ui")
    if not os.path.isdir(outdir):
        os.makedirs(outdir)
    written = []
    for fname, text in build_xml().items():
        path = os.path.join(outdir, fname)
        with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        written.append(path)
    return written


def write_plates():
    """The plates are a BUILD PRODUCT of this file, like the .twui.xml is.

    IT ALSO PRUNES. A png that stops being generated does not stop existing: the
    sixteen flat tint washes sat in this folder after the mask layer replaced
    them. deploy_iron_court.py ships off build_plates() so a stray file could
    never reach the pack, but _assets() walks this FOLDER to prove that every
    imagepath resolves - so a dead file left here can bless a path that would
    draw a blank white square in game.
    """
    written = cut_chd_art()
    _ember = os.path.join(ROOT, "Modding Files", "pack", *EMBER_SPRITE.split("/"))
    _want = open(EMBER_SOURCE, "rb").read()
    if not os.path.isfile(_ember) or open(_ember, "rb").read() != _want:
        open(_ember, "wb").write(_want)
        written.append(_ember)
    for path, rows in sorted(build_plates().items()):
        disk = os.path.join(ROOT, "Modding Files", "pack", *path.split("/"))
        _write_png(disk, rows)
        written.append(disk)
    for path, rows in wedge_art():
        disk = os.path.join(ROOT, "Modding Files", "pack", *path.split("/"))
        _write_png(disk, rows)
        written.append(disk)
    folder = os.path.join(ROOT, "Modding Files", "pack", *PLATE_DIR.split("/"))
    keep = set(os.path.basename(p) for p in art_paths())
    for name in sorted(os.listdir(folder)):
        if name.endswith(".png") and name not in keep:
            os.remove(os.path.join(folder, name))
            print("  pruned %s/%s - no longer generated" % (PLATE_DIR, name))
    return written


def selftest_scale():
    # THE SCALE MODEL. The Lua does the same arithmetic in integers and
    # import_iron_court.py runs it to prove the two agree.
    assert sc(1854, 1600) == 1545 and sc(1854, 1920) == 1854 and sc(1854, 2560) == 2472
    assert sc_box((18, 1018, 1884, 44), 1600) == (15, 848, 1570, 37)
    assert box_for(1600, 900) == (1600, 900) and box_for(1280, 720) == (1600, 900)
    assert box_for(1920, 1200) == (1920, 1080) and box_for(5120, 1440) == (2560, 1440)
    assert box_for(3840, 2160) == (2560, 1440) and box_for(2560, 1080) == (1920, 1080)
    assert box_for(0, 0) == (1600, 900)
    small = at_box(1600)
    assert small.COMPACT and not COMPACT and small.BOX_W == 1600
    assert small.PANEL_LAYOUT["ic_close"] == sc_box(PANEL_LAYOUT["ic_close"], 1600)
    assert small.ROW_PITCH == sc(ROW_PITCH, 1600)
    assert small.VISIBLE_ROWS == VISIBLE_ROWS, "a count must not scale"
    assert small.TEXT_STYLE["ic_card_name"] == (14, "header_14")
    assert small.BODY == (16, "header_16")
    assert at_box(1920).PANEL_LAYOUT == PANEL_LAYOUT
    big = at_box(2560)
    assert big.TEXT_STYLE == TEXT_STYLE, "text never grows above the base"
    assert big.CARD_W == sc(CARD_W, 2560)
    assert big.CARD_GRID == [(sc(x, 2560), sc(y, 2560)) for x, y in CARD_GRID]
    assert big.PARTY_GRID == [(sc(x, 2560), sc(y, 2560)) for x, y in PARTY_GRID]
    assert big.plot_grid() == [(sc(x, 2560), sc(y, 2560)) for x, y in plot_grid()]
    # AN UNCLASSIFIED LAYOUT NUMBER IS A REFUSAL. A value the scale pass does
    # not know about keeps its 1920 size on a 1600 screen with every check green.
    probe = {"BRAND_NEW_GAP": 12}
    try:
        _classify(probe)
    except AssertionError as exc:
        assert "BRAND_NEW_GAP" in str(exc)
    else:
        raise AssertionError("an unclassified layout number passed the scale pass")
    # THE SWEEP: every box width from 1600 to 2560. Clean on the real layout,
    # and it must see a fault that only exists part of the way along.
    assert check_scale_sweep() == [], check_scale_sweep()
    saved = dict(COMPACT_OVERRIDES)
    try:
        COMPACT_OVERRIDES["ic_row_d"] = (0, 0, 60, 0)      # into the button column
        assert any("ic_row_d" in p and "ic_row_e" in p for p in check_scale_sweep())
        COMPACT_OVERRIDES.clear()
        COMPACT_OVERRIDES.update(saved)
        COMPACT_OVERRIDES["ROW_PITCH"] = 3                  # the pool under the pager
        assert any("row pool" in p for p in check_scale_sweep())
        COMPACT_OVERRIDES.clear()
        COMPACT_OVERRIDES.update(saved)
        COMPACT_OVERRIDES["CARD_W"] = 12                    # cards into each other
        assert any("office" in p for p in check_scale_sweep())
    finally:
        COMPACT_OVERRIDES.clear()
        COMPACT_OVERRIDES.update(saved)


def _fonts_by_component(text):
    """component id -> (font_m_size, fontcat_name), for every text cell."""
    out = {}
    for m in re.finditer(r"(?ms)^\t\t<(\w+)\n.*?^\t\t</\1>", text):
        size = re.search(r'font_m_size="(\d+)"', m.group(0))
        cat = re.search(r'fontcat_name="([^"]+)"', m.group(0))
        if size and cat:
            out[m.group(1)] = (int(size.group(1)), cat.group(1))
    return out


def selftest_compact():
    # THE COMPACT COPIES: one per in-panel file, none for the two HUD pieces,
    # and every text cell exactly one CA size step below its base twin.
    files = build_xml()
    assert set(files) == set(ui_file_names()), "build_xml and ui_file_names disagree"
    # +7: FIRE_FILE and BURST_FILE, which hold no text and so have no compact
    # twin, and the Governors view's pin, face, two plates and badge, never
    # scaled (2026-09-30 ruling 1). +8: and the column's list, whose size the
    # Lua sets (ICUI.gm_list).
    assert len(files) == len(FILES) + len(COMPACT_FILES) + 8
    assert GM_LIST_FILE not in COMPACT_FILES
    assert FIRE_FILE not in COMPACT_FILES and BURST_FILE not in COMPACT_FILES
    assert GM_PIN_FILE not in COMPACT_FILES and GM_FACE_FILE not in COMPACT_FILES
    assert GM_NAME_FILE not in COMPACT_FILES and GM_LOYAL_FILE not in COMPACT_FILES
    assert GM_BADGE_FILE not in COMPACT_FILES
    assert "derpy_ic_opener_compact.twui.xml" not in files
    assert "derpy_ic_standing_compact.twui.xml" not in files
    for base, compact in COMPACT_FILES.items():
        want = _fonts_by_component(files[base])
        got = _fonts_by_component(files[compact])
        assert want and set(want) == set(got),             "%s does not hold the same text cells as %s" % (compact, base)
        for name, (_size, cat) in want.items():
            assert got[name] == COMPACT_FONTS[cat],                 "%s: %s is %s, not one step below %s" % (compact, name, got[name], cat)


def selftest():
    selftest_scale()
    selftest_compact()
    # THE LAW CHECKS SAY SO WHEN THEY MEASURED NOTHING, and the bar check fires.
    _fonts = dict(_MEASURE_FONTS)
    _MEASURE_FONTS.update((px, None) for px in range(8, 40))
    _got = check_law_text()
    _MEASURE_FONTS.clear()
    _MEASURE_FONTS.update(_fonts)
    assert any("cannot measure" in e for e in _got), "20k passed with no font"
    global GAME_DATA, LAW_SEGS
    _data, GAME_DATA = GAME_DATA, os.path.join("Z:" + os.sep, "nowhere")
    _got = check_law_art()
    GAME_DATA = _data
    assert any("no ui pack" in e for e in _got), "the law art check passed with no ui pack"
    _ui = open(os.path.join(ROOT, "Modding Files", "pack", "script", "campaign", "mod",
                            "zzz_derpy_iron_court_ui.lua"), encoding="utf-8").read()
    _got = check_law_art(_ui.replace('legion = "military_24", ', ''))
    assert any("government legion" in e for e in _got), "a government with no card picture went unreported"
    _got = check_law_art(_ui.replace('ICUI.GOV_ART_FILE = "ui/derpy_ic/gov_%s.png"',
                                     'ICUI.GOV_ART_FILE = "ui/derpy_ic/gov_%s_x.png"'))
    assert any("GOV_ART_FILE" in e for e in _got), "a card picture path the generator never writes went unreported"
    _segs, LAW_SEGS = LAW_SEGS, 10
    _got = check_law_bar()
    LAW_SEGS = _segs
    assert _got, "a support bar too short for the largest court went unreported"
    assert not check_law_bar(), check_law_bar()
    _order = sorted(PANEL_LAYOUT, key=_panel_order)
    _order.remove("ic_gov_glow")
    _order.append("ic_gov_glow")
    assert any("draws over" in e for e in check_gov_glow(_order)), "a glow over its icon went unreported"
    _box = PANEL_LAYOUT["ic_gov_glow"]
    PANEL_LAYOUT["ic_gov_glow"] = (_box[0] + 4,) + tuple(_box[1:])
    _got = check_gov_glow()
    PANEL_LAYOUT["ic_gov_glow"] = _box
    assert any("centred" in e for e in _got), "a glow off its icon went unreported"
    _lay = LAW_LAYERS[LAW_GLOW_INDEX]
    LAW_LAYERS[LAW_GLOW_INDEX] = dict(_lay, shader=None)
    _got = check_gov_glow()
    LAW_LAYERS[LAW_GLOW_INDEX] = _lay
    assert any("law card's glow does not breathe" in e for e in _got), "a still chosen law went unreported"
    assert not check_gov_glow(), check_gov_glow()
    # THE EMBER RULE FIRES. A particle named anything but template_particle is a
    # null the emitter dereferences on panel open, so the check has to be seen
    # catching one, and seen passing the shipped file.
    assert not check_burst(burst_xml()), check_burst(burst_xml())
    assert not check_gm(), check_gm()
    assert not check_masks({GM_FACE_FILE: gm_face_xml()}), check_masks({GM_FACE_FILE: gm_face_xml()})
    assert any("names no component_image" in e for e in check_masks(
        {GM_FACE_FILE: gm_face_xml().replace('maskimage="IC48', 'maskimage="IC99')})), \
        "a maskimage naming another component went unreported"
    # THE PLATES RULE FIRES. (16, 1040) would land in the footer's plate, so the
    # line goes to the bare map at (700, 600).
    assert not check_gm_plates(), check_gm_plates()
    _sorted_row = EU.layout(EU.assign(_gm_row(), GUID_PREFIXES[GM_ROW_FILE]), "")
    _h = _sorted_row.split("<hierarchy>", 1)
    _face = re.search(r"\n\t*<ic_gr_face this=\"[^\"]*\"/>", _h[1]).group(0)
    _under = _h[0] + "<hierarchy>" + _h[1].replace(_face, "").replace(
        "\n\t\t\t\t<ic_gr_l1 ", _face + "\n\t\t\t\t<ic_gr_l1 ", 1)
    assert any("ic_gr_badge is declared before ic_gr_face" in e
               for e in check_gm_plates(row_text=_under)), \
        "a row whose face draws over its badge went unreported"
    # THE PLATE RAILS RULE FIRES: the section line on the strip's rail.
    assert any("ic_lbl_section" in e and "rails" in e for e in check_gm_plates(
        dict(PANEL_LAYOUT, ic_lbl_section=(18, PANEL_LAYOUT["ic_gm_top"][3] - 14, 1884, 12)))), \
        "a line on the strip's bottom rail went unreported"
    # THE RAILS RULE FIRES, on the third line as it shipped in 73806344.
    assert any("ic_gr_l3" in e and "rails" in e for e in check_gm_plates(
        row_layout=dict(GM_ROW_LAYOUT, ic_gr_l3=(148, 52, 256, 20)))), \
        "a row line on the frame's bottom rail went unreported"
    _moved = dict(PANEL_LAYOUT, ic_gm_hint=(700, 600, 412, 26))
    assert any("ic_gm_hint" in e for e in check_gm_plates(_moved)), \
        "a column line off every plate went unreported"
    assert any("runs outside the column" in e for e in check_gm_plates(
        dict(PANEL_LAYOUT, ic_gm_col=(0, 124, 300, 890)))), \
        "a list wider than its column went unreported"
    # THE FULL-HEIGHT RULE FIRES, on the column and the title as 5D2C688C shipped them.
    assert any("cut short" in e for e in check_gm_plates(
        dict(PANEL_LAYOUT, ic_gm_col=(0, 128, 503, 886)))), \
        "a column that stops at the footer went unreported"
    assert any("spikes squash" in e for e in check_gm_plates(
        dict(PANEL_LAYOUT, ic_gm_head=(10, 128, 425, 60)))), \
        "a squashed column title went unreported"
    assert any("under ic_gm_foot" in e for e in check_gm_plates(
        dict(PANEL_LAYOUT, ic_gm_btns=(0, 1000, 444, 90)))), \
        "the button plate over the footer went unreported"
    _pn = EU.layout(EU.assign(_panel(), GUID_PREFIXES["derpy_ic_panel.twui.xml"]), "")
    assert any("first child" in e for e in check_gm(
        panel_text=_pn.replace("<ic_gm_pins ", "<ic_gm_pinz ", 1))), \
        "a holder that is not the first child went unreported"
    assert any("takes clicks" in e for e in check_gm(face_text=gm_face_xml().replace(
        'name="standard"', 'name="standard"\n\t\t\t\t\tinteractive="true"', 1))), \
        "a face that takes clicks went unreported"
    assert any("no maskimage" in e for e in check_gm(face_text=re.sub(
        r'\n\t\t\tmaskimage="[^"]+"', "", gm_face_xml()))), \
        "a face with no mask went unreported"
    assert any("GM_BACKDROP" in e for e in check_gm(lua_text=_lua_map_tables().replace(
        "panel_bg.png", "panel_bgx.png"))), "a wrong backdrop path went unreported"
    assert any("anchors them apart" in e for e in check_gm(badge_text=gm_badge_xml().replace(
        'height="%d"' % GM_PIN_H, 'height="%d"' % (GM_PIN_H - 2)))), \
        "a badge boxed apart from its pin went unreported"
    assert any("not one image on the head" in e for e in check_gm(badge_text=gm_badge_xml().replace(
        'offset="%.2f,%.2f"' % GM_BADGE_BOX[:2], 'offset="%.2f,%.2f"' % (GM_BADGE_BOX[0], 120.0)))), \
        "a badge off the head went unreported"
    assert any("takes clicks" in e for e in check_gm(badge_text=gm_badge_xml().replace(
        'name="standard"', 'name="standard"\n\t\t\t\t\tinteractive="true"', 1))), \
        "a badge that takes clicks went unreported"
    assert any("GB_CREST" in e for e in check_gm(lua_text=re.sub(
        r"ICUI\.GB_CREST\s*=\s*\d+", "ICUI.GB_CREST = 3", _lua_map_tables()))), \
        "a Lua badge layer apart from the file's went unreported"
    assert any("carries text again" in e for e in check_gm(
        pin_text=gm_pin_xml() + "<component_text")), "a pin carrying text went unreported"
    assert any("no padding" in e for e in check_gm(name_text=re.sub(
        r'textyoffset="[^"]+"', 'textyoffset="32.00,0.00"', gm_name_xml()))), \
        "a name plate's padded text went unreported"
    assert any("own 30px" in e for e in check_gm(loyal_text=gm_loyal_xml().replace(
        'height="30"', 'height="44"'))), "a stretched plate went unreported"
    assert any("draws off it" in e for e in check_gm(name_text=gm_name_xml().replace(
        'offset="0.00,%.2f"' % GM_NAME_PLATE_Y, 'offset="0.00,%.2f"' % (GM_NAME_PLATE_Y + 8)))), \
        "a name plate off its box's middle went unreported"
    assert any("takes clicks" in e for e in check_gm(name_text=gm_name_xml().replace(
        'name="standard"', 'name="standard"\n\t\t\t\t\tinteractive="true"', 1))), \
        "a name plate that takes clicks went unreported"
    assert any("under 4.5" in e for e in check_gm(
        wash=lambda c: [bytes(bytearray((255, 255, 255, 255)))])), \
        "a wash too bright for the text went unreported"
    assert any("GM_NAME_H" in e for e in check_gm(lua_text=re.sub(
        r"ICUI\.GM_NAME_H\s*=\s*\d+", "ICUI.GM_NAME_H = 1", _lua_map_tables()))), \
        "a Lua name box apart from the file's went unreported"
    assert any("gm_wash_path" in e for e in check_gm(lua_text=_lua_map_tables().replace(
        "gm_wash_", "gm_wosh_"))), "a Lua wash path apart from the art's went unreported"
    assert any("reaches into the name plate" in e for e in check_gm(pin_text=gm_pin_xml().replace(
        'height="%d"' % GM_PIN_H, 'height="%d"' % (GM_PIN_H - 8)))), \
        "a pin reaching into its name plate went unreported"
    assert any("bottom centre" in e for e in check_gm(pin_text=gm_pin_xml().replace(
        'component_anchor_point="0.50,1.00"', ""))), "a pin anchored elsewhere went unreported"
    assert any("plate's inside" in e for e in check_gm(lua_text=re.sub(
        r"ICUI\.GM_NAME_W\s*=\s*\d+", "ICUI.GM_NAME_W = %d" % GM_PIN_W,
        _lua_map_tables()))), "a name cut to the whole pin went unreported"
    assert any("no ContextWorldSpaceComponent" in e for e in check_gm(
        pin_text=gm_pin_xml().replace("ContextWorldSpaceComponent", "ContextX"))), \
        "check_gm passed a pin with no world-space callback"
    assert any("ContextOpacitySetter" in e for e in check_gm(
        pin_text=gm_pin_xml() + 'callback_id="ContextOpacitySetter"')), \
        "check_gm passed a pin that carries CA's fade"
    assert any("anchors them apart" in e for e in check_gm(face_text=gm_face_xml().replace(
        'height="%d"' % GM_PIN_H, 'height="%d"' % (GM_PIN_H - 2)))), \
        "a face boxed apart from its pin went unreported"
    _rim = [bytearray(r) for r in seat_rim_pixels()]
    for _y in range(RIM_MARGIN):
        for _x in range(RIM_MARGIN):
            if _x + _y < RIM_MARGIN:        # a rounded corner, cut away
                _rim[_y][4 * _x + 3] = 0
    assert not check_seat_rim(), check_seat_rim()
    assert check_seat_rim([bytes(r) for r in _rim]),         "check_seat_rim passed a rim whose corners are cut away"
    assert not check_portrait_frame(), check_portrait_frame()
    # THE ZIGGURAT RULE FIRES: a tower with nothing drawn, and one over the section line.
    assert not check_ziggurat(), check_ziggurat()
    _zw, _zh = PANEL_LAYOUT["ic_zig_bg"][2:]
    assert any("hangs off" in e for e in check_ziggurat(rows=[bytes(4 * _zw)] * _zh)), \
        "cards standing on nothing went unreported"
    assert any("section line" in e for e in check_ziggurat(
        layout=dict(PANEL_LAYOUT, ic_zig_bg=(0, 100, _zw, _zh)))), \
        "a ziggurat over the section line went unreported"
    _fr = [bytearray(r) for r in frame_pixels()]
    for _r in (_fr[0], _fr[-1]):
        for _i in range(3, len(_r), 4):
            _r[_i] = 0
    for _r in _fr:
        _r[3] = 0
        _r[-1] = 0
    assert check_portrait_frame([bytes(r) for r in _fr]), \
        "check_portrait_frame passed a frame with a clear outer edge"
    _flat = dict(FACE_LAYERS[FRAME_INDEX], offset=(0, 0), dw=0, dh=0)
    assert check_portrait_frame(layer=_flat), \
        "check_portrait_frame passed a frame drawn inside the cell"
    assert check_burst(burst_xml().replace(
        'name="loops"', 'name="paused"')), "check_burst passed a paused sprite"
    _fire = fire_xml()
    assert not check_fire(_fire), check_fire(_fire)
    assert any("not named template_particle" in m for m in
               check_fire(_fire.replace("template_particle", "ember_particle"))), \
        "check_fire passed a particle that is not named template_particle"
    assert check_fire(_fire.replace('callback_id="Particle"', 'callback_id="Nothing"')), \
        "check_fire passed an emitter with no particle"
    files = build_xml()
    # DERIVED, not a literal. A pinned count is a number to bump every time a
    # file is added, which teaches nothing; what matters is that every declared
    # file was actually built and given its own GUID prefix.
    assert len(files) == len(ui_file_names()), "every declared file must be built"
    assert set(files) == set(ui_file_names()),         "build_xml produced a different set of files than FILES declares"
    assert len(set(GUID_PREFIXES[f] for f in ui_file_names())) == len(files),         "two files share a GUID prefix - a collision is a silent non-draw"
    assert not check(), "the real layout must pass before faults are injected"

    def injected(what, restore, needle):
        problems = check()
        restore()
        assert any(needle in p for p in problems), \
            "check() did not catch %s (said: %s)" % (what, problems)

    saved = PANEL_LAYOUT["ic_hdr_b"]
    PANEL_LAYOUT["ic_hdr_b"] = (saved[0] + 40, saved[1], saved[2], saved[3])
    injected("a header floated off its column",
             lambda: PANEL_LAYOUT.__setitem__("ic_hdr_b", saved), "but its column")

    saved_row = ROW_LAYOUT["ic_row_a"]
    ROW_LAYOUT["ic_row_a"] = (14, 8, 600, 22)
    injected("a column running into the next",
             lambda: ROW_LAYOUT.__setitem__("ic_row_a", saved_row), "into the next")

    # 21b, THE PAIRING. A picture cell with fewer layers than the helper aimed at
    # it draws its .twui.xml default and reports nothing - which is exactly how
    # sixteen move cards shipped showing a white square. The generator half is
    # injected here; the Lua half (set_face on a one-layer cell, and a helper
    # repointed at a layer nothing has) was watched to fail by hand, since
    # check() reads that file off disk rather than out of a global.
    saved_pl = PORT_LAYERS[:]
    del PORT_LAYERS[:]
    injected("a picture cell built with no layer for the panel to paint into",
             lambda: PORT_LAYERS.extend(saved_pl), "declares 0 layer(s)")

    # ---- the party card, the Crown's block and the dial's plate --------
    saved_pc = PARTY_LAYOUT["ic_party_name"]
    PARTY_LAYOUT["ic_party_name"] = (2, 2) + saved_pc[2:]
    injected("a party cell drawn across the card's frame band",
             lambda: PARTY_LAYOUT.__setitem__("ic_party_name", saved_pc),
             "inside the party card's")

    saved_pc2 = PARTY_LAYOUT["ic_party_t2"]
    PARTY_LAYOUT["ic_party_t2"] = PARTY_LAYOUT["ic_party_t1"]
    injected("two party cells in the same place",
             lambda: PARTY_LAYOUT.__setitem__("ic_party_t2", saved_pc2),
             "overlap on the party card")

    # NARROWED TO NOTHING, not lengthened by a made-up string: the strings 20g
    # measures come out of the model, and a fault injected into the model would
    # be testing the wrong file.
    saved_pt = PARTY_LAYOUT["ic_party_t1"]
    PARTY_LAYOUT["ic_party_t1"] = saved_pt[:2] + (24, saved_pt[3])
    injected("a trait name wider than the cell it is drawn in",
             lambda: PARTY_LAYOUT.__setitem__("ic_party_t1", saved_pt),
             "ic_party_t1 would clip")

    saved_pn = PARTY_LAYOUT["ic_party_name"]
    PARTY_LAYOUT["ic_party_name"] = saved_pn[:2] + (40, saved_pn[3])
    injected("a name cell too narrow for the widest word in it",
             lambda: PARTY_LAYOUT.__setitem__("ic_party_name", saved_pn),
             "and a word cannot be split")

    # THE BAND LINE NARROWED. The left half is sized off the widest band name,
    # so this is the fault most likely to arrive for real - a band renamed one
    # word longer.
    saved_ctl = PANEL_LAYOUT["ic_control_band"]
    PANEL_LAYOUT["ic_control_band"] = saved_ctl[:2] + (120, saved_ctl[3])
    injected("a band line too narrow for the widest band's name",
             lambda: PANEL_LAYOUT.__setitem__("ic_control_band", saved_ctl),
             "ic_control_band would clip")

    # AND THE LEFT HALF WIDENED UNDER THE RIGHT ONE. The box is two halves
    # again and they share rows, so a width can collide now as well as a height.
    saved_band = PANEL_LAYOUT["ic_control_band"]
    PANEL_LAYOUT["ic_control_band"] = saved_band[:2] + (
        _CROWN_RIGHT_X - saved_band[0] + 8, saved_band[3])
    injected("the Crown's left half reaching under the right half",
             lambda: PANEL_LAYOUT.__setitem__("ic_control_band", saved_band),
             "overlap in the Crown's box")

    # AND THE BAR'S PAGED HOME RUN INTO THE PAGER it exists to make room for.
    saved_paged = ACT_PAGED["ic_act_purge"]
    ACT_PAGED["ic_act_purge"] = (PANEL_LAYOUT["ic_page_prev"][0] - 20,) + saved_paged[1:]
    injected("the action bar with the pager up crossing the pager",
             lambda: ACT_PAGED.__setitem__("ic_act_purge", saved_paged),
             "crosses the pager")

    # OR UP INTO THE CROWN'S BOX, which is the other thing in that column.
    ACT_PAGED["ic_act_purge"] = saved_paged[:1] + (
        PANEL_LAYOUT["ic_crown_box"][1] + PANEL_LAYOUT["ic_crown_box"][3] - 10,) \
        + saved_paged[2:]
    injected("the action bar with the pager up inside the Crown's box",
             lambda: ACT_PAGED.__setitem__("ic_act_purge", saved_paged),
             "inside the Crown's box")

    # AND TWO ROWS OF THE BOX CROSSING. RE-AIMED, not deleted: this used to widen
    # the left half until it reached under the Crown's portrait, and the box has
    # no halves any more - it is four stacked rows, so a width can no longer
    # collide with anything and the injection had quietly stopped being one. The
    # overlap a stacked box actually gets is a row whose HEIGHT eats the row
    # under it, which is what a line given a taller face does.
    saved_ctl2 = PANEL_LAYOUT["ic_control"]
    PANEL_LAYOUT["ic_control"] = saved_ctl2[:3] + (
        PANEL_LAYOUT["ic_control_fx"][1] - saved_ctl2[1] + 8,)
    injected("a row of the Crown's box growing down into the row under it",
             lambda: PANEL_LAYOUT.__setitem__("ic_control", saved_ctl2),
             "overlap in the Crown's box")

    saved_leader = PANEL_LAYOUT["ic_leader_name"]
    PANEL_LAYOUT["ic_leader_name"] = saved_leader[:2] + (30, saved_leader[3])
    injected("the Crown's name cell too narrow for a lord's name",
             lambda: PANEL_LAYOUT.__setitem__("ic_leader_name", saved_leader),
             "ic_leader_name would clip")

    saved_py = globals()["PARTIES_Y"]
    globals()["PARTIES_Y"] = PANEL_LAYOUT["ic_page_prev"][1] - PARTY_H
    injected("a party grid running under the pager",
             lambda: globals().__setitem__("PARTIES_Y", saved_py),
             "the party grid ends at")

    # THE GRID ITSELF, not PARTIES_X. PARTY_GRID is built at import, so moving
    # the origin afterwards moves no card - and the cards are what 16b reads.
    # One gutter to the left puts the first column over the divider and onto
    # the dial, with every other number on the panel still correct.
    saved_grid = list(PARTY_GRID)
    PARTY_GRID[:] = [(_gx - PARTY_W - PARTY_GAP_X, _gy) for _gx, _gy in saved_grid]
    injected("a party grid shifted off its column onto the dial",
             lambda: PARTY_GRID.__setitem__(slice(None), saved_grid),
             "and the right column is")

    saved_box = PANEL_LAYOUT["ic_dial_box"]
    PANEL_LAYOUT["ic_dial_box"] = (RIM_BOX[0] + 20, RIM_BOX[1] + 20,
                                   RIM_BOX[2] - 40, RIM_BOX[3] - 40)
    injected("a plate too small to hold the dial it frames",
             lambda: PANEL_LAYOUT.__setitem__("ic_dial_box", saved_box),
             "does not contain the rim")

    saved_box2 = PANEL_LAYOUT["ic_dial_box"]
    PANEL_LAYOUT["ic_dial_box"] = saved_box2[:2] + (COL_W + COL_GUTTER,
                                                   saved_box2[3])
    injected("a plate wider than the column it sits in",
             lambda: PANEL_LAYOUT.__setitem__("ic_dial_box", saved_box2),
             "and the left column is")

    saved_crest = PARTY_LAYOUT["ic_party_crest"]
    PARTY_LAYOUT["ic_party_crest"] = saved_crest[:3] + (saved_crest[3] + 8,)
    injected("a party crest in a box that stretches it",
             lambda: PARTY_LAYOUT.__setitem__("ic_party_crest", saved_crest),
             "ic_party_crest is")

    saved_port = PARTY_LAYOUT["ic_party_port"]
    PARTY_LAYOUT["ic_party_port"] = saved_port[:2] + (60, 60)
    injected("a party portrait in a box the porthole does not fit",
             lambda: PARTY_LAYOUT.__setitem__("ic_party_port", saved_port),
             "ic_party_port is")

    saved_lport = PANEL_LAYOUT["ic_leader_port"]
    PANEL_LAYOUT["ic_leader_port"] = saved_lport[:2] + (100, 100)
    injected("the Crown's portrait in a square box",
             lambda: PANEL_LAYOUT.__setitem__("ic_leader_port", saved_lport),
             "ic_leader_port is")

    # CHECK 24: a cell the Lua paints with no image slot to paint into. The
    # branch that gives ic_leader_port its layers is removed by renaming what it
    # matches, which is what "somebody forgot the branch" actually looks like.
    _saved_builder = globals()["_panel"]

    def _panel_without_face_branch():
        _keep = PANEL_LAYOUT.pop("ic_leader_port")
        try:
            _root = _saved_builder()
        finally:
            PANEL_LAYOUT["ic_leader_port"] = _keep
        return _root

    globals()["_panel"] = _panel_without_face_branch
    globals()["FILES"] = [(f, _panel_without_face_branch if f == FILES[0][0] else b, c)
                          for f, b, c in FILES]
    injected("a painted cell that no built file declares",
             lambda: (globals().__setitem__("_panel", _saved_builder),
                      globals().__setitem__(
                          "FILES", [(f, _saved_builder if f == FILES[0][0] else b, c)
                                    for f, b, c in FILES])),
             "and no built file declares it")

    saved_panel = PANEL_LAYOUT["ic_alert"]
    # PANEL_H past its bottom edge, derived rather than typed: at 736 tall a
    # literal 720 overflowed, and at 900 the same number is a legal position
    # that trips a DIFFERENT check instead - the injection stopped testing
    # what it names.
    PANEL_LAYOUT["ic_alert"] = (18, PANEL_H - 20, CONTENT_W, 44)
    injected("a component overflowing the panel",
             lambda: PANEL_LAYOUT.__setitem__("ic_alert", saved_panel), "overflows the panel")

    # THE COST ICON IS NAMED TWICE, once here and once in the panel Lua, and
    # nothing but this makes the two agree. Aimed at a path that EXISTS, so the
    # only thing wrong with it is that it is not the one the panel draws - a
    # missing path would trip the clause below as well and neither would have
    # been seen to fail alone.
    saved_cost = COST_ICON
    globals()["COST_ICON"] = rim_path()
    injected("a generator that measures a different icon from the one drawn",
             lambda: globals().__setitem__("COST_ICON", saved_cost),
             "the cost icon differs")

    globals()["COST_ICON"] = "ui/derpy_ic/no_such_icon.png"
    injected("a cost icon in no pack at all",
             lambda: globals().__setitem__("COST_ICON", saved_cost),
             "is in no pack")

    # THE PICTURE COSTS WIDTH. Three of them rather than a hand-measured cell:
    # a literal width stops testing the moment a tier bar gains a digit, and
    # charging nothing for an inline image is precisely the arithmetic that
    # would let the cost cell clip the day it gained one. If 20c ever stops
    # measuring the markup, three pictures measure nothing and this goes quiet.
    # ENOUGH PICTURES TO OVERRUN THE CELL, DERIVED rather than three of them.
    # Three was enough while the cost cell was 96px wide; the cell is 206 now and
    # the injection had quietly stopped overflowing - a check nobody can watch
    # fail. The count comes off the cell's own width and the content size, so a
    # future resize cannot retire it a second time.
    saved_markup = COST_MARKUP
    _need_w = CARD_LAYOUT["ic_card_need"][2]
    _need_px = TEXT_STYLE.get("ic_card_need", BODY)[0]
    globals()["COST_MARKUP"] = saved_markup * (_need_w // _need_px + 2)
    injected("a cost string carrying more picture than its cell can hold",
             lambda: globals().__setitem__("COST_MARKUP", saved_markup),
             "ic_card_need would clip")

    # THE FIRE GOES OUT. A peak of nothing leaves the ramp, the depth and
    # every other number in place, and leaves the rim a bare rail - which is
    # the shape this fault would really take, someone turning it down until it
    # was not there rather than deleting the branch.
    saved_peak = EMBER_PEAK
    globals()["EMBER_PEAK"] = 0.0
    injected("a dial whose edge stopped burning",
             lambda: globals().__setitem__("EMBER_PEAK", saved_peak),
             "carries no fire")

    # AND THE FRAME COMES OFF. The cached frame is emptied rather than the
    # loop that draws it deleted, because the cache is what every flag is
    # built from - a frame file that read as blank would do exactly this.
    flag_frame()
    saved_flag = list(_FLAG)
    _FLAG[:] = [([b"\0" * (SIGIL * 4)] * SIGIL,
                 saved_flag[0][1], saved_flag[0][2])]
    injected("party flags that lost their frame",
             lambda: _FLAG.__setitem__(slice(None), saved_flag),
             "has no frame in it")

    saved_layers = ROW_LAYERS[0]["path"]
    ROW_LAYERS[0]["path"] = "ui/skins/default/no_such_image.png"
    injected("an imagepath that resolves to nothing",
             lambda: ROW_LAYERS[0].__setitem__("path", saved_layers), "not in any pack")

    saved_crest = ROW_LAYOUT["ic_row_crest"]
    ROW_LAYOUT["ic_row_crest"] = (saved_crest[0], saved_crest[1],
                                  saved_crest[2] + 14, saved_crest[3])
    injected("a house flag in a non-square cell",
             lambda: ROW_LAYOUT.__setitem__("ic_row_crest", saved_crest),
             "stretched flag")

    saved_name_xy = CARD_LAYOUT["ic_card_name"]
    # ONE INSIDE THE BAND, derived: a typed 18 stopped being inside it the day
    # the frame became the 8px Hell-Forge holder.
    _band = max(ly["margin"] for ly in CARD_LAYERS if ly["path"] == BORDER_TEXTURE)
    CARD_LAYOUT["ic_card_name"] = (saved_name_xy[0], _band - 1) + saved_name_xy[2:]
    injected("a card label drawn under the card's own frame rail",
             lambda: CARD_LAYOUT.__setitem__("ic_card_name", saved_name_xy),
             "frame band")

    saved_margin_18 = CARD_LAYERS[1]["margin"]
    # ONE UNDER THE FLOOR, derived: a typed 18 stopped being inside the corner
    # the day the frame became the 6px Hell-Forge rim.
    CARD_LAYERS[1]["margin"] = BORDER_CORNER - 1
    injected("a frame 9-sliced inside its own corner ornament",
             lambda: CARD_LAYERS[1].__setitem__("margin", saved_margin_18),
             "its own %dpx edge" % BORDER_CORNER)

    # The OTHER texture in the same list, and the one that shipped: a tile
    # sliced inside its own black border repeats that border across the card.
    saved_tile = CARD_LAYERS[0]["margin"]
    CARD_LAYERS[0]["margin"] = 2
    injected("a tile 9-sliced inside its own border, which bands the card",
             lambda: CARD_LAYERS[0].__setitem__("margin", saved_tile),
             "its own 4px edge")

    # ...and the same texture at the right margin but TILED.
    CARD_LAYERS[0]["tile"] = True
    injected("a flat centre tiled",
             lambda: CARD_LAYERS[0].pop("tile"),
             "whose centre is one flat colour")

    # The size and the category disagreeing, which is the shape the panel
    # actually shipped: a real category drawn, a different number laid out.
    saved_body = globals()["BODY"]
    globals()["BODY"] = (14, "body_16")
    injected("a body size that disagrees with its own category",
             lambda: globals().__setitem__("BODY", saved_body),
             "the engine will round it")

    saved_style = dict(TEXT_STYLE)
    TEXT_STYLE["ic_nonesuch"] = (16, "body_16")
    injected("a style entry naming a component that does not exist",
             lambda: (TEXT_STYLE.clear(), TEXT_STYLE.update(saved_style)),
             "which no layout table has")

    saved_opener = list(OPENER_LAYERS)
    del OPENER_LAYERS[2:]
    injected("an opener with no icon on it, which is a blank disc on the strip",
             lambda: OPENER_LAYERS.__setitem__(slice(None), saved_opener),
             "bare plate with no icon")

    saved_inset = OPENER_HOVER[2]["dw"]
    OPENER_HOVER[2]["dw"] = 0
    injected("an opener glyph stretched over its own plate",
             lambda: OPENER_HOVER[2].__setitem__("dw", saved_inset),
             "is not inset")

    saved_order = _panel_order
    globals()["_panel_order"] = lambda n: (False, n)
    injected("the crests declared among the cells instead of over them",
             lambda: globals().__setitem__("_panel_order", saved_order),
             "painted over it")

    saved_rim_order = _panel_order
    globals()["_panel_order"] = lambda n: (n.startswith("ic_barc_"), n)
    injected("the rim declared among the wedges instead of over them",
             lambda: globals().__setitem__("_panel_order", saved_rim_order),
             "painted over it")

    saved_rim = PANEL_LAYOUT.pop("ic_dial_rim")
    injected("no rim on the dial at all",
             lambda: PANEL_LAYOUT.__setitem__("ic_dial_rim", saved_rim),
             "no border")

    saved_bar = PANEL_LAYOUT.pop("ic_wedge_00")
    injected("one fewer wedge than the pie has slices",
             lambda: PANEL_LAYOUT.__setitem__("ic_wedge_00", saved_bar),
             "wedges for a pie")

    PANEL_LAYOUT["ic_wedge_01"] = (PIE_BOX[0], PIE_BOX[1], 40, 40)
    injected("a wedge declared at some size of its own",
             lambda: PANEL_LAYOUT.__setitem__("ic_wedge_01", PIE_BOX),
             "and the pie box is")

    # TALLER, BY AS MUCH AS IT TAKES. The label already spans the full panel
    # width and sits above the pie, so the only way into the pie's box is down -
    # and how far down is PIE_BOX's business, not a number typed here. It was
    # 1200x60, which crossed the old pie's band and now stops four pixels above
    # the new one: a mutation landing just short of its target reports a live
    # check as unproven, which is the same lie as a check aimed at nothing.
    saved_label = PANEL_LAYOUT["ic_lbl_section"]
    PANEL_LAYOUT["ic_lbl_section"] = (saved_label[0], saved_label[1],
                                      saved_label[2],
                                      PIE_BOX[1] + 10 - saved_label[1])
    injected("a label whose box reaches in under the pie",
             lambda: PANEL_LAYOUT.__setitem__("ic_lbl_section", saved_label),
             "is under the pie")

    # This one is injected because check 4 was WRONG first: it tested the element
    # carrying interactive="true", which is the <standard>/<hover> state, not the
    # component that carries soundcategory - so it reported a fault on every
    # button in every file. Fixing it flipped the check from firing on everything
    # to firing on nothing, and only an injected fault tells those apart.
    # The three faults that shipped on 2026-09-11 and drew a grid of frames over
    # the panel, the cards and all four tabs.
    # Re-aimed at the CARD's frame: the panel is full bleed now and has no frame
    # layer left to break, so the injection was about to test nothing.
    saved_margin = CARD_LAYERS[1]["margin"]
    CARD_LAYERS[1]["margin"] = 0
    injected("a frame texture with no 9-slice margin, which tiles the whole frame",
             lambda: CARD_LAYERS[1].__setitem__("margin", saved_margin),
             "repeats rather than stretching")

    # DERIVED from the box, not typed. A literal 90 exceeded half of a 150-tall
    # card and stopped exceeding half of a 200-tall one the moment the cards grew
    # - the injection went quiet and the check looked green for the wrong reason.
    # RESTORED TO THE SAVED VALUE, not to a literal. This said 18 - correct on
    # the day it was written and silently WRONG the moment the shipped margin
    # became 30: the injection quietly reset the real layout to the old number
    # and left the build with the very fault check 18 exists to catch.
    saved_margin_half = CARD_LAYERS[1]["margin"]
    CARD_LAYERS[1]["margin"] = min(CARD_W, CARD_H) // 2 + 10
    injected("a 9-slice margin wider than half the box it fills",
             lambda: CARD_LAYERS[1].__setitem__("margin", saved_margin_half),
             "exceeds half of")

    global ROW_PITCH
    saved_pitch = ROW_PITCH
    # DERIVED, not typed. A literal 60 was past the alert bar when the pool was
    # 15 rows in a 736-tall panel; at 10 rows in a 900-tall one it is SMALLER than
    # the real pitch, so the injection would have stopped injecting anything and
    # the check would have looked green for the wrong reason. One pitch of the
    # whole available height overruns for any pool of two or more rows.
    ROW_PITCH = PANEL_LAYOUT["ic_alert"][1] - ROWS_Y
    injected("a row pool that overruns the alert bar",
             lambda: globals().__setitem__("ROW_PITCH", saved_pitch),
             "past the alert bar")

    # DERIVED: put the pager back up among the rows, wherever those now end.
    saved_pager = PANEL_LAYOUT["ic_page_prev"]
    PANEL_LAYOUT["ic_page_prev"] = (saved_pager[0], ROWS_Y, saved_pager[2],
                                    saved_pager[3])
    injected("a pager sitting on top of the rows",
             lambda: PANEL_LAYOUT.__setitem__("ic_page_prev", saved_pager),
             "on top of the rows")

    global BAR_COLOURS
    saved_colours = list(BAR_COLOURS)
    BAR_COLOURS = [saved_colours[0]] * MAX_HOUSES
    injected("ten identical bar colours, which read as one solid block",
             lambda: globals().__setitem__("BAR_COLOURS", saved_colours),
             "not all distinct")

    global OPENER_SOUND
    saved_sound = OPENER_SOUND
    OPENER_SOUND = None
    injected("an interactive component with no soundcategory",
             lambda: globals().__setitem__("OPENER_SOUND", saved_sound),
             "no soundcategory")

    # A GUID collision across files is a silent non-draw, and it is what a single
    # mod-wide prefix produces: EU.assign restarts its counter per file.
    saved_prefix = GUID_PREFIXES["derpy_ic_row.twui.xml"]
    GUID_PREFIXES["derpy_ic_row.twui.xml"] = GUID_PREFIXES["derpy_ic_panel.twui.xml"]
    injected("two files sharing a GUID prefix",
             lambda: GUID_PREFIXES.__setitem__("derpy_ic_row.twui.xml", saved_prefix),
             "appears in")

    PANEL_LAYOUT["ic_orphan"] = (0, 0, 10, 10)
    orphan_problems = check()
    del PANEL_LAYOUT["ic_orphan"]
    assert not any("named by no layout table" in p for p in orphan_problems), \
        "a table entry with no component is not the fault this check is for"

    assert not check(), "all injected faults must have been restored"

    guids = set()
    for text in files.values():
        guids |= set(re.findall(r'this="([^"]+)"', text))
    print("selftest: ok (%d files, %d components, %d guids)"
          % (len(files),
             sum(len(xml_component_names(t)) for t in files.values()),
             len(guids)))


def check_law_art(lua=None):
    """ICUI.LAW_ART names one picture for every law category and option, no
    stale key, and every picture is in CA's installed ui packs - a path that
    resolves to nothing draws a blank card with no log line."""
    import read_pack_index as RPI
    if lua is None:
        lua = open(os.path.join(ROOT, "Modding Files", "pack", "script", "campaign", "mod",
                                "zzz_derpy_iron_court_ui.lua"), encoding="utf-8").read()
    out = []
    d = re.search(r'ICUI\.LAW_ART_DIR = "([^"]+)"', lua)
    t = re.search(r"ICUI\.LAW_ART = \{(.*?)\n\}", lua, re.S)
    if not d or not t:
        return ["no ICUI.LAW_ART_DIR / ICUI.LAW_ART in the panel Lua"]
    _gaf = re.search(r'ICUI\.GOV_ART_FILE = "([^"]+)"', lua)
    if not _gaf or _gaf.group(1) != gov_art_path("%s"):
        out.append("ICUI.GOV_ART_FILE is %r, not the %r the upscaled pictures are written to"
                   % (_gaf and _gaf.group(1), gov_art_path("%s")))
    _abs = re.search(r'ICUI\.ABSENT_SIGIL = "([^"]+)"', lua)
    if not _abs or _abs.group(1) != absent_sigil_path("%s"):
        out.append("ICUI.ABSENT_SIGIL is %r, not the %r the grey sigils are written to"
                   % (_abs and _abs.group(1), absent_sigil_path("%s")))
    art = dict(re.findall(r'\[?"?([\w.]+)"?\]? = "(\w+)"', t.group(1)))
    want = set()
    for cat, _name, _icon, options in IC.LAWS:
        want.update("%s.%s" % (cat, o[0]) for o in options)
    out += ["no panel picture for law %s" % k for k in sorted(want - set(art))]
    out += ["ICUI.LAW_ART names %s, which is no law" % k for k in sorted(set(art) - want)]
    # THE GOVERNMENT CARDS' PICTURES, out of the same folder (2026-10-03).
    model = open(os.path.join(ROOT, "Modding Files", "pack", "script", "campaign", "mod",
                              "zzz_derpy_iron_court.lua"), encoding="utf-8").read()
    govs = set(re.findall(r'"(\w+)"', re.search(r"IC\.GOV_ORDER = \{([^}]*)\}", model).group(1)))
    g = re.search(r"ICUI\.GOV_ART = \{([^}]*)\}", lua)
    gart = dict(re.findall(r'(\w+) = "(\w+)"', g.group(1))) if g else {}
    out += ["no card picture for government %s" % k for k in sorted(govs - set(gart))]
    out += ["ICUI.GOV_ART names %s, which is no government" % k for k in sorted(set(gart) - govs)]
    art.update(("gov." + k, v) for k, v in gart.items())
    have, found = set(), False
    for name in ("ui.pack", "ui2.pack", "ui3.pack", "ui_3.pack"):
        p = os.path.join(GAME_DATA, name)
        if os.path.isfile(p):
            found = True
            have.update(RPI.paths(p))
    if not found:
        return out + ["cannot check the law pictures: no ui pack in %s" % GAME_DATA]
    out += ["law picture %s is in no ui pack" % (d.group(1) + v + ".png")
            for k, v in sorted(art.items()) if d.group(1) + v + ".png" not in have]
    return out


def check_law_bar():
    """The support bar has a slot for every group the largest court can field:
    the Crown's men on one side, and each rival party's line plus the men won
    away from it. A group past the last slot is not drawn and the bar comes up
    short with no log line."""
    model = open(os.path.join(ROOT, "Modding Files", "pack", "script", "campaign", "mod",
                              "zzz_derpy_iron_court.lua"), encoding="utf-8").read()
    mct = open(os.path.join(ROOT, "Modding Files", "pack", "script", "mct", "settings",
                            "derpy_iron_court.lua"), encoding="utf-8").read()
    most = [int(v) for v in re.findall(r"rivals_max\s*=\s*(\d+)", model)]
    slider = re.search(r'\{"rivals_max", "[^"]*", \d+, \d+, (\d+),', mct)
    if not most or not slider:
        return ["cannot read the largest rivals_max out of the model and the MCT slider"]
    rivals = max(most + [int(slider.group(1))])
    order = sorted(PANEL_LAYOUT, key=_panel_order)
    if order.index("ic_law_p_barrim") < max(order.index("ic_law_p_baraye"),
                                             order.index("ic_law_p_barnay")):
        return ["the support bar's border is declared before a side, which draws over it"]
    segs = [n for n in order if n.startswith(("ic_lv_seg_", "ic_lv_segc_"))]
    if order.index("ic_lv_barrim") < max(order.index(n) for n in segs):
        return ["the vote bar's border is declared before a segment, which draws over it"]
    if LAW_SEGS < 1 + 2 * rivals:
        return ["the support bar has %d slots and a court of %d rivals can field %d groups"
                % (LAW_SEGS, rivals, 1 + 2 * rivals)]
    return []


def check_gov_glow(order=None):
    """The government's glow sits on its icon, under its line, and breathes; the
    chosen party and law cards breathe and the law in force does not."""
    out = []
    order = order or sorted(PANEL_LAYOUT, key=_panel_order)
    if order.index("ic_gov_glow") > order.index("ic_gov"):
        out.append("ic_gov_glow is declared after ic_gov, so it draws over the icon it lights")
    gx, gy, gw, gh = PANEL_LAYOUT["ic_gov_glow"]
    lx, ly, _lw, lh = PANEL_LAYOUT["ic_gov"]
    tx = int(float(LABEL_TX.split(",")[0]))
    # the icon is the line's first glyph: its middle is LABEL_TX plus half an 18px icon in
    if (gx + gw // 2, gy + gh // 2) != (lx + tx + 9, ly + lh // 2):
        out.append("ic_gov_glow is centred at %d,%d and the government's icon at %d,%d"
                   % (gx + gw // 2, gy + gh // 2, lx + tx + 9, ly + lh // 2))
    for what, lay in (("the chosen party card's frame", PARTY_LAYERS[PARTY_SEL_INDEX]),
                      ("the chosen law card's glow", LAW_LAYERS[LAW_GLOW_INDEX])):
        if lay.get("shader") != "glow_pulse_t0":
            out.append("%s does not breathe" % what)
    if LAW_LAYERS[LAW_SEL_INDEX].get("shader"):
        out.append("the law in force breathes, and four of them always are")
    return out


def main(argv):
    if "--selftest" in argv:
        selftest()
        return 0
    # THE PLATES ARE WRITTEN BEFORE THE CHECK, not after. They are generated
    # art: on a normal run this file is their source of truth, so writing then
    # checking is the same order the .twui.xml already gets. --check writes
    # nothing, which is what makes the drift check mean something to the packing
    # gate, where the on-disk copy is the one that ships.
    if "--check" not in argv:
        wedges = 0
        for path in write_plates():
            if os.path.basename(path).startswith("wedge_"):
                wedges += 1
            else:
                print("wrote %s" % path)
        print("wrote %d wedge pictures - %d slices in %d colours"
              % (wedges, DIAL_SLICES, len(wedge_colours())))
    problems = check()
    # AND AGAIN AT THE SMALL END. A 1600x900 player gets this layout scaled by
    # five sixths with every font one size down; the sweep covers the sizes in
    # between, where the rule is a straight line between these two.
    problems += ["at 1600x900: " + p for p in at_box(1600).check()]
    problems += ["at 2560x1440: " + p for p in at_box(2560).check()]
    problems += check_scale_sweep()
    problems += check_law_art()
    problems += check_law_bar()
    problems += check_gov_glow()
    for problem in problems:
        sys.stderr.write("FAIL %s\n" % problem)
    if problems:
        return 1
    files = build_xml()
    print("ok: %d files, %d components"
          % (len(files), sum(len(xml_component_names(t)) for t in files.values())))
    if "--check" in argv:
        return 0
    for path in write_ui():
        print("wrote %s" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
