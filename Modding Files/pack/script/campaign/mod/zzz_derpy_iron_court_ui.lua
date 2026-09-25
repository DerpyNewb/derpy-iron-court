-- The Iron Court - the panel and its HUD opener.
--
-- See docs/superpowers/specs/2026-09-11-iron-court-design.md and
-- docs/mockups/politics_panel.png. Read docs/CUSTOM_UI.md before editing.
--
-- THIS FILE IS BUILT ON THE GREAT GUILDS' AND THE ZHARR EXCHANGE'S PROVEN SHAPE.
-- Every structural choice below exists because one of those two measured it in a
-- running campaign; the comments name what each one costs when it is got wrong.
--
-- Loc calls ARE allowed here and nowhere near a turn handler: this file resolves
-- names at DRAW time, which is the whole reason zzz_derpy_iron_court.lua stores
-- keys and numbers and never a display string.

ICUI = ICUI or {}

ICUI.PANEL  = "derpy_ic_panel"
ICUI.ROW    = "derpy_ic_row"
ICUI.CARD   = "derpy_ic_card"
-- ONE PER PARTY, on the court tab, where the house list used to be.
ICUI.PARTY  = "derpy_ic_party"
-- ONE PER MOVE, on the intrigue tab. SAME FILE as the office card and so
-- the same GUID set - a pool is instances, and only a second .twui.xml would
-- need a prefix of its own. It is a second POOL rather than the offices one
-- reused because ICUI.layout runs once: sharing would mean moving cards on
-- every tab switch, which is how six of them ended up under the court rows.
ICUI.PLOT   = "derpy_ic_plot"
ICUI.BTN    = "derpy_ic_opener"

ICUI.PATH_PANEL  = "ui/campaign ui/derpy_ic_panel"
ICUI.PATH_ROW    = "ui/campaign ui/derpy_ic_row"
ICUI.PATH_CARD   = "ui/campaign ui/derpy_ic_card"
ICUI.PATH_PARTY  = "ui/campaign ui/derpy_ic_party"
ICUI.PATH_PLOT   = "ui/campaign ui/derpy_ic_plot"
ICUI.PATH_OPENER = "ui/campaign ui/derpy_ic_opener"

ICUI.BTN_SIZE = 44          -- must match OPENER_W/H in tools/gen_ic_ui.py
ICUI.BTN_GAP  = 4
ICUI.BTN_TRIES = 12

-- Row origin and pitch, panel-relative. tools/gen_ic_ui.py declares the same two
-- numbers as ROWS_X / ROWS_Y / ROW_PITCH and import_iron_court.py refuses to pack
-- if they drift apart.
ICUI.ROWS_X = 18
-- 192, where the list started before there was a dial. Every view that draws a
-- list shares this, and while it was pushed down to clear the pie the three
-- views with no pie on them paid about three rows for a dial they never draw.
-- The COURT view draws no list at all, so it pays nothing here.
ICUI.ROWS_Y = 192
ICUI.ROW_PITCH = 64
-- THE ROW COMPONENT'S OWN SIZE. layout() gives every component its size as
-- well as its place, because the box scales with the screen. ROW_W / ROW_H
-- in tools/gen_ic_ui.py.
ICUI.ROW_W = 1866
ICUI.ROW_H = 61
-- The header strip rides above whichever row is first, so it moves when the
-- list does. Both positions are named because the dispatcher picks one.
--
-- BACK TO 30. It was widened to 48 to stack the sort arrow UNDER its label;
-- the arrow sits BESIDE the label now and the strip needs no second row.
ICUI.HDR_GAP = 30
-- A LITERAL, AND NOT ROWS_Y - HDR_GAP. The generator derives it that way and
-- this file cannot: import_iron_court.py reads these constants out of the Lua
-- by regex to compare them against gen_ic_ui.py, and an expression is not a
-- number it can read. The comparison is what makes the duplication safe -
-- widening HDR_GAP and forgetting this line is exactly the drift it caught on
-- 2026-09-17, and it refused to pack rather than shipping a strip 18px out.
ICUI.HDR_Y = 162
-- The strip's other position. On the court view the list starts below the pie,
-- so its headers do too; left at HDR_Y they would be behind an opaque disc.
-- One name per line: check_lua_undeclared does not register every target of a
-- multiple assignment, and a name it thinks nothing declares is a refusal to pack.
-- THE PIE. A FILLED half disc, centred on (DIAL_CX, DIAL_CY) - which is the
-- BASELINE, the flat side, not the middle of the box - sweeping from due west
-- round to due east. A party's share of the sweep is its share of the court.
--
-- IT IS SIXTY PICTURES, one per slice, and that is not a shortcut - it is the
-- only smooth option there is. A component is an axis-aligned rectangle and
-- the engine has no rotation, so a pie assembled out of components is a
-- staircase whose step is the component: the strips that came before this were
-- six pixels tall and a player called it blocky the day it shipped. No
-- arrangement of rectangles does better than their own height. A PICTURE can
-- hold a curve, so the geometry moved into the art.
--
-- DIAL_SLICES is therefore two things at once: the angular quantum a party's
-- share is rounded to - three degrees, and the smallest seated party is
-- guaranteed one of them - and the number of components. gen_ic_ui.py carries
-- the same numbers, rasterises a wedge per slice per party colour, and
-- import_iron_court.py refuses to pack when the two disagree: the generator
-- BUILDS the pictures and this file only ever says which one to show.
ICUI.DIAL_SLICES = 60
-- 324, not 340, and 460 rather than 476. The rim's fire burns on all four
-- sides now, and the flat side had nothing under it to burn but the court's
-- column headings. The headings are on the row pitch and cannot move without
-- costing the list a whole row, so the dial gave up sixteen pixels of radius
-- instead and came down to meet them. gen_ic_ui.py derives both from the line
-- above the dial and the fire's depth; import_iron_court.py refuses to pack
-- when this file and that one disagree.
ICUI.DIAL_R = 431
ICUI.DIAL_CX = 481           -- the middle of a 1920 panel
-- The baseline, and 460 puts the top of the rim's box at 120 - which is
-- exactly the bottom of the line of section text above it.
ICUI.DIAL_CY = 593
ICUI.CREST_R = 309           -- the crest ring, inside the fill
-- EACH PARTY'S SHARE IN FIGURES, on the same ray as its crest and inside it.
-- The colour says who is biggest and the crest says who they are; neither says
-- whether a rival is on 31 or 38.
ICUI.SHARE_R = 247
ICUI.SHARE_W = 72
ICUI.SHARE_H = 24
-- HOW WIDE THE NUMBER ACTUALLY DRAWS, which is not how wide its cell is: the
-- cell is 72 so that a centred figure has slack on both sides, and the ink is
-- about 40 at the widest ("100%").
ICUI.SHARE_INK = 40

-- HOW NARROW A RUN MAY BE AND STILL CARRY ITS MARK, derived from the ring the
-- mark sits on rather than typed. One slice is pi / DIAL_SLICES of arc, so a
-- run of n slices has n * radius * pi / DIAL_SLICES pixels to draw in. Typed,
-- these two stayed where a 210px dial put them and a 340px one kept the small
-- dial's blanks: a party with room for its crest went unmarked.
function ICUI.min_slices(radius, width)
    return math.ceil(width / (radius * math.pi / ICUI.DIAL_SLICES))
end
ICUI.SHARE_MIN_SLICES = ICUI.min_slices(ICUI.SHARE_R, ICUI.SHARE_INK)
-- One row component per house. The court view therefore never scrolls; the
-- governors view does, because an empire holds more provinces than there are
-- houses. MAX_ROWS is the SIZE OF THE POOL, not the length of the list.
ICUI.MAX_ROWS = 12
-- WHERE THE COURT'S LIST STARTS IN THAT POOL. The pie is opaque and ends at
-- DIAL_CY, so the rows above this one would be behind it; the court view skips
-- them and pages through what is left. gen_ic_ui.py derives the same number
-- from the same geometry and import_iron_court.py refuses to pack on a drift.
-- SEPARATE FROM MAX_ROWS, and the whole reason the standing bar broke. The bar
-- has one segment per HOUSE and the row pool is a different number entirely; they
-- were equal at 15 until the pool shrank to carry taller portraits, and every
-- loop that had been written against MAX_ROWS quietly stopped covering five
-- segments - which are then never hidden either, because a component is visible
-- from the moment it is created.
-- DERIVED. A literal 15 beside a layout loop that already counted IC.HOUSES
-- is the same drift this comment warns about one line up: adding a
-- sixteenth house laid out sixteen segments and drew fifteen, and the
-- sixteenth was then never hidden either.
-- THE NINE INTERESTS PLUS EVERY FACTION THAT COULD BE ABSORBED. The model
-- does the arithmetic; this is a component count, and a court that seats more
-- parties than there are segments draws the overflow nowhere at all.
ICUI.MAX_HOUSES = IC.MAX_SEATS
-- A WHOLE PAGE per click, not three rows. The buttons say PREVIOUS and NEXT and
-- the caption counts pages, so a step of anything other than a page would put the
-- caption and the movement out of step with each other.
ICUI.SCROLL_STEP = nil
-- The row's picture cell is DUAL-USE and its two sources disagree: porthole art
-- is 300x164 (landscape) and a house crest is 24x24 (square). SetImagePath gives
-- the incoming image the CELL's size rather than fitting it inside, so one fixed
-- box has to distort one of them. The cell is resized per image instead.
-- One per line: check_lua_undeclared does not resolve TABLE.FIELD, and it reads a
-- MULTIPLE assignment's later targets as undeclared globals. ICUI.TRACK_W below
-- is single-assigned and passes, so these match it rather than arguing with it.
ICUI.PORT_W = 104
ICUI.PORT_H = 57
-- WHICH IMAGE LAYER IS WHICH, on the two cells that draw a face. Layers draw
-- in order, so 0 is behind 1:
--
--   0  the house plate - a flat PNG in that house's colour
--   1  the porthole    - a CUT-OUT, 27% to 54% fully transparent, measured
--                        across the shipped art
--
-- which is why the plate reaches the screen at all: the face does not cover it.
-- That is also the only way a house colour can get onto a portrait. There is no
-- runtime colour call on a uicomponent - SetColour, SetColor,
-- SetCurrentStateColour, SetImageColour and SetImageTint are every spelling
-- tried and all five are NOT DOCUMENTED in CA's reference - so the colour has to
-- arrive as a picture, and SetImagePath is the call that delivers one.
--
-- Must match PLATE_INDEX / FACE_INDEX in tools/gen_ic_ui.py; the packing gate
-- compares them. A face written to layer 0 would paint over the plate instead of
-- onto it, and nothing would look broken - just colourless, which is the state
-- this replaces.
ICUI.PLATE_INDEX = 0
ICUI.FACE_INDEX = 1
-- 2 is CA's OWN HERALDRY MASK, over the face.
--
-- CA does not tint a portrait. Beside each generic porthole they ship
-- <porthole>_mask1.png, same size, ~82% transparent, whose opaque region is the
-- cloth on the hat and under the beard - painted neutral light grey in the base
-- art so a colour reads true on it. The mask is pure white where it marks, and a
-- layer colour MULTIPLIES, so white times the faction colour is the colour.
--
-- THE COLOUR IS NOT SET FROM HERE. There is no colour or tint setter on a
-- uicomponent in the whole of CA's reference. The cell carries a
-- ContextColourSetter declared in the .twui.xml, bound to
-- CcoCampaignFaction.PrimaryColour with colour_index0 = 2, and set_plate hands
-- it the house's faction with SetContextObject. That callback is the only way a
-- colour varies per row.
ICUI.MASK_INDEX = 2
ICUI.CREST_W = 36
ICUI.CREST_H = 36


-- How far the CONTENT is pushed in from the panel's own origin. Zero at the
-- design resolution, which is the common case: a 1920x1080 panel centred on a
-- 1920x1080 screen is already at 0,0. On a bigger screen the panel is stretched
-- so its background reaches the edges, and the content is pushed back to the
-- middle of it - without this, layout() would pin the whole court to the
-- top-left corner of a 2560-wide black rectangle.
-- One per line: check_lua_undeclared reads a multiple assignment's later targets
-- as undeclared globals.
ICUI.OX = 0
ICUI.OY = 0

-- EVERY CHILD OFFSET, panel-relative. The .twui.xml offsets do NOT position a
-- runtime-created component - layout() below places every one of them by hand,
-- and a name missing from these tables is a cell that draws at the screen origin
-- over the campaign map. Mirrors PANEL_LAYOUT / ROW_LAYOUT / CARD_LAYOUT in
-- tools/gen_ic_ui.py; the packing gate compares them.
ICUI.PANEL_XY = {
    -- FAR LEFT. The panel's own name belongs where a reader starts, and the
    -- middle of the top strip is now the pie's column.
    ic_title         = {18, 12, 520, 36},
    -- TOP RIGHT, and 48px rather than 22. A close button at the top LEFT at
    -- half CA size is one nobody finds and nobody can hit.
    ic_close         = {1854, 12, 48, 48},
    -- Moved left so it ends at 1840 and stops short of the close button.
    ic_influence     = {1540, 20, 300, 26},
    ic_tab_court     = {18, 62, 150, 32},
    ic_tab_offices   = {172, 62, 150, 32},
    ic_tab_govs      = {326, 62, 150, 32},
    ic_tab_intrigue  = {480, 62, 150, 32},
    -- THE RECORD LAST: the one tab with nothing to act on (author, 2026-09-24).
    ic_tab_petitions = {634, 62, 150, 32},
    ic_tab_log       = {788, 62, 150, 32},
    -- ITS HOME ON THE OTHER FOUR TABS. On the court it moves into the
    -- Crown's box, to ICUI.COURT_SECTION_XY below - the same trick the header
    -- reason a component gets two homes at all: one component, five views, and
    -- only one of them wants it here.
    ic_lbl_section   = {18, 98, 1884, 22},
    -- THE TWO COLUMN HEADERS AND THE RULE BETWEEN THEM. The court tab is a
    -- dial and a grid of cards side by side now; these three are what say so,
    -- and they are court-only - the dispatcher hides them everywhere else.
    ic_col_left      = {18, 110, 926, 26},
    ic_col_right     = {976, 110, 926, 26},
    ic_divider       = {958, 110, 4, 900},
    -- THE CROWN'S BOX, under the dial, in two halves (author, 2026-09-24).
    -- LEFT: what holding the court is worth - the share, the band it lands in,
    -- then the band's effects one to a line. RIGHT: who sits on the throne -
    -- the name and the party at the half's full width, then the portrait with
    -- his trait and the party's two beside it. 30px in from the column edge:
    -- they sit inside ic_crown_box's frame band. tools/gen_ic_ui.py derives
    -- every one of these and the gate compares the two tables entry by entry.
    ic_crown_box     = {18, 635, 926, 258},
    ic_control       = {48, 697, 316, 26},
    ic_control_band  = {48, 725, 316, 26},
    ic_control_fx    = {48, 759, 316, 26},
    ic_control_fx2   = {48, 785, 316, 26},
    ic_control_fx3   = {48, 811, 316, 26},
    ic_control_fx4   = {48, 837, 316, 26},
    ic_leader_lbl    = {388, 665, 526, 26},
    ic_leader_name   = {388, 697, 526, 28},
    ic_leader_party  = {388, 729, 526, 26},
    ic_leader_port   = {388, 763, 183, 100},
    ic_leader_trait  = {585, 767, 329, 26},
    ic_leader_t1     = {585, 805, 329, 26},
    ic_leader_t2     = {585, 831, 329, 26},
    -- THE PIE'S OWN BORDER, in the pie's box. A picture, not a nine-slice:
    -- CA's frame is four straight rails and none of them bends round an arc.
    -- TEN PIXELS OUT AND TEN UP from the pie box it used to match exactly.
    -- The fire burns outward now and had nowhere to burn; the picture grew on
    -- the arc's three sides and kept its baseline, so the box moved with it.
    -- See RIM_BOX in tools/gen_ic_ui.py, which the packing gate compares.
    -- THE PLATE THE WHOLE DIAL SITS ON - Rome 2's Government Overview box. It
    -- is declared FIRST among the dial's parts on the generator's side, because
    -- children draw in declaration order and the panel propagates one priority
    -- over the whole tree: nothing but its position can put it underneath.
    ic_dial_box      = {18, 146, 926, 473},
    ic_dial_rim      = {34, 146, 894, 463},
    -- THE Y IS ICUI.HDR_Y, and the layout pass reads it from there rather than
    -- from here - which is why these five sat at 144 for the whole of the
    -- stacked-arrow experiment and drew correctly anyway. import_iron_court.py
    -- compares this table to the generator's cell for cell, so the drift had
    -- one place left to show and this is it.
    ic_hdr_a         = {146, 162, 502, 24},
    -- 35px LEFT, 2026-09-17. Check 20k: the Rank heading's arrow is MoveTo'd
    -- past its caption and ran into the Influence heading beside it.
    ic_hdr_b         = {708, 162, 360, 24},
    ic_hdr_c         = {1088, 162, 45, 24},
    ic_hdr_d         = {1188, 162, 490, 24},
    ic_hdr_e         = {1698, 162, 170, 24},
    -- ONE BESIDE EACH HEADER, sharing its column's x. 17x18 is the native size
    -- of CA's parchment_sort_arrow art; see tools/gen_ic_ui.py. The x here is
    -- the COLUMN's, not the arrow's: ICUI.refresh adds the header's measured
    -- text width to it, because the caption differs per view.
    ic_hsort_a       = {146, 165, 17, 18},
    ic_hsort_b       = {708, 165, 17, 18},
    ic_hsort_c       = {1088, 165, 17, 18},
    ic_hsort_d       = {1188, 165, 17, 18},
    ic_hsort_e       = {1698, 165, 17, 18},
    ic_page_prev     = {1454, 978, 136, 34},
    ic_page_lbl      = {1600, 982, 164, 26},
    ic_page_next     = {1774, 978, 136, 34},
    -- THE PARTY ACTION BAR, in the pager's row, CENTRED under the grid. Court
    -- only; ICUI.draw_actions moves it to ICUI.ACT_PAGED_XY while the pager
    -- shows. ACT_BUTTONS in tools/gen_ic_ui.py derives the four.
    ic_act_provoke   = {1124, 978, 132, 34},
    ic_act_gift      = {1262, 978, 164, 34},
    ic_act_secure    = {1432, 978, 216, 34},
    ic_act_purge     = {1654, 978, 100, 34},
    ic_act_hint      = {976, 982, 926, 26},
    ic_alert         = {18, 1018, 1884, 44},
}
-- Segment width is derived from the house count in BOTH files. It was a literal
-- 88 here and in the generator, which put the tenth segment at the panel edge and
-- would have run the fifteenth 330px past it.
ICUI.CREST_PX = 40
-- WHO HOLDS SLICE i. The runs are counted in slices, so this is a walk of the
-- seating order and not arithmetic - and a slice nobody holds cannot happen,
-- because the runs always tile the sweep exactly.
function ICUI.slice_owner(slots, i)
    for k = 1, #slots do
        if i < slots[k].from + slots[k].n then return slots[k].slug end
    end
    return nil
end

-- ONE SLICE OF THE PIE, in one party's colour. Must match wedge_path() in
-- tools/gen_ic_ui.py. A missing imagepath draws a blank square and logs
-- nothing, so the slice number is padded the same way on both sides.
function ICUI.wedge_path(i, slug)
    return string.format("ui/derpy_ic/wedge_%02d_%s.png", i, slug or "none")
end

-- ANYTHING PLACED ON THE PIE BY ANGLE rather than by rectangle: the crests,
-- which ride a ring inside the fill at the middle of their own wedge. Returns
-- the TOP-LEFT, because that is what MoveTo takes - a centre handed to MoveTo
-- puts every crest half its own width down and to the right, which is the kind
-- of wrong that looks deliberate. Screen y grows downward, so the sine is
-- subtracted and the ring rises above the baseline.
function ICUI.arc_xy(radius, f, size)
    return ICUI.arc_box(radius, f, size, size)
end

-- The same thing for a cell that is not square - a share label is wide and
-- short - because centring a 72x24 box with one "size" puts it 24px left of
-- where it belongs and nothing says so.
function ICUI.arc_box(radius, f, w, h)
    local a = math.pi * (1 - f)
    return math.floor(ICUI.DIAL_CX + radius * math.cos(a) - w / 2 + 0.5),
           math.floor(ICUI.DIAL_CY - radius * math.sin(a) - h / 2 + 0.5)
end

-- EVERY WEDGE IS THE WHOLE PIE BOX and every one of them is at the same place.
-- The picture carries the shape, so there is nothing per-slice to place.
for i = 0, ICUI.DIAL_SLICES - 1 do
    ICUI.PANEL_XY[string.format("ic_wedge_%02d", i)] =
        {ICUI.DIAL_CX - ICUI.DIAL_R, ICUI.DIAL_CY - ICUI.DIAL_R,
         2 * ICUI.DIAL_R, ICUI.DIAL_R}
end
-- ONE WALL PER PARTY, sharing the pie's box exactly as the wedges do - the
-- line is drawn from the centre and the PICTURE carries the angle, because the
-- engine cannot turn a component and sixty angles is sixty pictures. Which one
-- a wall wears is decided at every draw; this is only where they wait.
for i = 0, ICUI.MAX_HOUSES - 1 do
    ICUI.PANEL_XY[string.format("ic_div_%02d", i)] =
        {ICUI.DIAL_CX - ICUI.DIAL_R, ICUI.DIAL_CY - ICUI.DIAL_R,
         2 * ICUI.DIAL_R, ICUI.DIAL_R}
end
-- ONE CREST PER SEAT, not per cell: it rides the inner ring at the middle of
-- its own party's wedge. They are placed properly at every draw; this is only
-- where they wait.
for i = 0, IC.MAX_SEATS - 1 do
    local x, y = ICUI.arc_xy(ICUI.CREST_R, 0.5, ICUI.CREST_PX)
    ICUI.PANEL_XY[string.format("ic_barc_%02d", i)] =
        {x, y, ICUI.CREST_PX, ICUI.CREST_PX}
    -- ONE SHARE LABEL PER SEAT, on the same ring rule as the crest and inside
    -- it. Same reason there is one per seat and not one per party: a component
    -- cannot be created after the panel is.
    local sx, sy = ICUI.arc_box(ICUI.SHARE_R, 0.5, ICUI.SHARE_W, ICUI.SHARE_H)
    ICUI.PANEL_XY[string.format("ic_barp_%02d", i)] =
        {sx, sy, ICUI.SHARE_W, ICUI.SHARE_H}
end

-- Recentred on a 61-tall row, not left at the offsets that centred them in a
-- 40-tall one. The portrait keeps y=2 because it fills the row rather than
-- sitting inside it; every text cell is (ROW_H - its height) / 2.
-- Text cells are 26 tall now rather than 20, because the panel draws in
-- body_16 instead of the body_12 it was silently getting; each is still
-- (ROW_H - its height) / 2 from the top.
ICUI.ROW_CHILD_XY = {
    ic_row_port      = {12, 2, 104, 57},
    ic_row_e         = {1680, 15, 170, 32},
    -- The house crest, beside the House column: the faction's own flag, which
    -- is the only thing on a row that carries its colours.
    ic_row_crest     = {638, 12, 36, 36},
    ic_row_a         = {128, 18, 502, 26},
    ic_row_b         = {690, 18, 360, 26},
    -- RANK GAVE PARTY 80px. It holds one or two digits and has held 180 since
    -- the list was written; a rolled party name is up to 30 characters.
    ic_row_c         = {1070, 18, 45, 26},
    ic_row_d         = {1170, 18, 490, 26},
    -- THE SECOND BUTTON: REFUSE on the Petitions tab, hidden everywhere else.
    ic_row_f         = {1560, 15, 110, 32},
}

-- The text columns are indented past a 238-wide porthole rather than a 60-wide
-- unit card, and still end up wider than they were before either, because the
-- card itself went from 434 to 760.
-- Every cell moved inside the card 30px frame band. At margin 18 the frame
-- was sliced through its own corner ornament and the text sat on the rail;
-- at 30 the band is real estate the children have to stay out of.
-- The name and the effect run the card's full width; only the short cells
-- share the middle with the face. See CARD_LAYOUT in tools/gen_ic_ui.py.
ICUI.CARD_CHILD_XY = {
    ic_card_name     = {30, 30, 304, 20},
    ic_card_port     = {30, 54, 86, 47},
    ic_card_holder   = {124, 52, 210, 20},
    ic_card_crest    = {124, 74, 16, 16},
    ic_card_house    = {144, 74, 190, 16},
    ic_card_button   = {124, 90, 100, 22},
    ic_card_need     = {228, 90, 106, 22},
    ic_card_term     = {30, 114, 304, 18},
    ic_card_effect   = {30, 136, 304, 18},
}

-- THE ZIGGURAT. One card per office, in four centred bands of 2 / 3 / 4 / 5.
-- Every number below is also in tools/gen_ic_ui.py and the gate compares the
-- two grids position by position, because a pyramid built twice from the same
-- arithmetic is a pyramid built twice.
ICUI.CARDS_X = 18
ICUI.CARDS_Y = 192
ICUI.CARD_GAP_X = 16
ICUI.CARD_GAP_Y = 14
ICUI.CARD_W = 364
ICUI.CARD_H = 184
ICUI.CONTENT_W = 1884
ICUI.CARD_XY = {}
for row = 1, #IC.TIERS do
    local n = IC.TIER_SEATS[IC.TIERS[row]]
    local band = n * ICUI.CARD_W + (n - 1) * ICUI.CARD_GAP_X
    local x0 = ICUI.CARDS_X + math.floor((ICUI.CONTENT_W - band) / 2)
    for col = 0, n - 1 do
        ICUI.CARD_XY[#ICUI.CARD_XY + 1] = {
            x0 + col * (ICUI.CARD_W + ICUI.CARD_GAP_X),
            ICUI.CARDS_Y + (row - 1) * (ICUI.CARD_H + ICUI.CARD_GAP_Y),
        }
    end
end

-- THE INTRIGUE TAB: ONE COLUMN PER CATEGORY OF MOVE.
--
-- Nine cards in undifferentiated bands said nothing about which moves are
-- alternatives to each other. A column per category says "these four do the same
-- kind of thing to a man" without a word of explanation.
--
-- THE DEEPEST CATEGORY SETS THE CARD HEIGHT, so moving a move between categories
-- reshapes the card - which is why the columns and their depths are read off
-- IC.PLOT_CATS and IC.PLOTS rather than typed here. gen_ic_ui.py derives the same
-- grid from the same two tables and import_iron_court.py compares them.
--
-- WHAT THE COLUMNS COST: the warning band. Four cards deep leaves no room for a
-- row strip above the grid, so the clocks and snubs ride ic_alert instead - one
-- line, with a count of the rest. See ICUI.draw_intrigue.
ICUI.PLOTS_X = ICUI.CARDS_X
ICUI.PLOTS_HDR_Y = ICUI.ROWS_Y
ICUI.PLOTS_HDR_H = 24
ICUI.PLOTS_Y = ICUI.PLOTS_HDR_Y + ICUI.PLOTS_HDR_H + 10
ICUI.PLOT_COLS = #IC.PLOT_CATS
ICUI.PLOT_COUNTS = {}
ICUI.PLOT_DEPTH = 0
for i = 1, ICUI.PLOT_COLS do
    local n = #IC.plots_in(IC.PLOT_CATS[i].key)
    ICUI.PLOT_COUNTS[i] = n
    if n > ICUI.PLOT_DEPTH then ICUI.PLOT_DEPTH = n end
end
ICUI.PLOT_W = math.floor((ICUI.CONTENT_W
    - (ICUI.PLOT_COLS - 1) * ICUI.CARD_GAP_X) / ICUI.PLOT_COLS)
-- 978 IS ic_page_prev's y, which is where the pager sits and the lowest a card
-- may reach. It is the panel layout's number and gen_ic_ui.py reads it from
-- PANEL_LAYOUT; the gate compares the heights the two arrive at.
--
-- NO NUMBER ON THE LEFT OF AN OPERATOR IN THIS CHUNK. It holds over 255
-- constants, and past that the game's compiler loads a left-hand literal into a
-- register the right operand then lands on: `978 - 6 - ICUI.PLOTS_Y` ran as
-- 226 - 226, PLOT_H came out -11 and every move card in a column stacked 3px
-- below the last. Stock Lua gets it right, so only tools/check_lua_literal_left.py
-- sees it.
local plot_floor = 978 - 6
ICUI.PLOT_H = math.floor((plot_floor - ICUI.PLOTS_Y
    - (ICUI.PLOT_DEPTH - 1) * ICUI.CARD_GAP_Y) / ICUI.PLOT_DEPTH)

function ICUI.plot_col_x(col)          -- col is 0-based, as the grid builds it
    return ICUI.PLOTS_X + col * (ICUI.PLOT_W + ICUI.CARD_GAP_X)
end

-- Column by column, in IC.PLOT_CATS' order. ICUI.plot_at[i] is the move card i
-- draws, so a click needs no arithmetic to get back to it.
ICUI.PLOT_XY = {}
ICUI.plot_at = {}
for col = 1, ICUI.PLOT_COLS do
    local moves = IC.plots_in(IC.PLOT_CATS[col].key)
    for row = 1, #moves do
        ICUI.PLOT_XY[#ICUI.PLOT_XY + 1] = {
            ICUI.plot_col_x(col - 1),
            ICUI.PLOTS_Y + (row - 1) * (ICUI.PLOT_H + ICUI.CARD_GAP_Y),
        }
        ICUI.plot_at[#ICUI.PLOT_XY] = moves[row]
    end
end

-- THE BLURB IS THREE CELLS, NOT ONE. twui text never wraps - the emitter writes
-- texthbehaviour="Never split" on every cell deliberately, because of the three
-- values the engine has, "Resize" breaks to one word per line and draws outside
-- the height the component declares. More lines means more components, and
-- ICUI.fit_lines measures the split with the engine's own metric.
ICUI.PLOT_BLURB_LINES = 4
ICUI.PLOT_PAD = 30
ICUI.PLOT_FOOT_PAD = 10
ICUI.PLOT_ICON_PX = 40
ICUI.PLOT_INNER_W = ICUI.PLOT_W - ICUI.PLOT_PAD * 2
ICUI.PLOT_CHILD_XY = {
    ic_plot_icon = {ICUI.PLOT_PAD, 26, ICUI.PLOT_ICON_PX, ICUI.PLOT_ICON_PX},
    ic_plot_name = {ICUI.PLOT_PAD + ICUI.PLOT_ICON_PX + 8, 30,
                    ICUI.PLOT_W - ICUI.PLOT_PAD * 2 - ICUI.PLOT_ICON_PX - 8, 20},
    ic_plot_cost = {ICUI.PLOT_PAD, ICUI.PLOT_H - ICUI.PLOT_FOOT_PAD - 22, 110, 22},
    ic_plot_go   = {ICUI.PLOT_W - ICUI.PLOT_PAD - 90,
                    ICUI.PLOT_H - ICUI.PLOT_FOOT_PAD - 22, 90, 22},
}
ICUI.PLOT_BLURB_KEYS = {}
for i = 1, ICUI.PLOT_BLURB_LINES do
    local key = "ic_plot_b" .. i
    ICUI.PLOT_BLURB_KEYS[i] = key
    ICUI.PLOT_CHILD_XY[key] = {ICUI.PLOT_PAD, (i - 1) * 18 + 68,
                               ICUI.PLOT_INNER_W, 18}
end

-- ONE HEADER PER CATEGORY COLUMN, appended to PANEL_XY rather than typed into
-- it: the columns are derived from IC.PLOT_CATS, so the cells that name them
-- have to be. gen_ic_ui.py adds the same names to PANEL_LAYOUT from the same
-- table, and a component NO layout table names cannot draw at all.
--
-- HERE AND NOT BESIDE THE REST OF PANEL_XY, because it reads PLOT_COLS and
-- plot_col_x, and both are declared in this block - up there the loop limit was
-- nil and the file would not load.
for _i = 1, ICUI.PLOT_COLS do
    ICUI.PANEL_XY["ic_plotcat_" .. _i] = {ICUI.plot_col_x(_i - 1),
                                          ICUI.PLOTS_HDR_Y,
                                          ICUI.PLOT_W, ICUI.PLOTS_HDR_H}
end

-- ONE CARD PER PARTY. Five across, because CONTENT_W is 1884 and five 364s
-- with four 16px gaps is 1884 exactly - the same sum that gives the office
-- card its width, not a copy of the number it produced.
--
-- TWO ACROSS, THREE DOWN, IN THE RIGHT COLUMN. It was five across the whole
-- panel, which is what a band underneath the dial could hold. The dial is
-- beside the grid now rather than above it, so the grid has half the width and
-- all of the height: two cards of 455 instead of five of 364, and three rows
-- instead of two. The name cell went from 280px to 371 in the trade, which is
-- most of the reason a rolled name needed two lines.
--
-- SIX SLOTS, NOT TEN. A court opens with the Crown and two to four rivals, so
-- five is the common case and it still fits one page; only confederates reach a
-- second, and the pager is what they reach it by.
ICUI.PARTY_COLS = 2
ICUI.PARTY_ROWS = 3
ICUI.PARTY_GAP_X = 16
ICUI.PARTY_GAP_Y = 14
ICUI.PARTY_W = 455
ICUI.PARTY_H = 266
-- THE TOP OF THE RIGHT COLUMN'S BODY, under its header. The grid no longer
-- waits for the dial to finish: the dial is in the other column.
ICUI.PARTIES_X = 976
ICUI.PARTIES_Y = 146
ICUI.PARTY_SLOTS = ICUI.PARTY_COLS * ICUI.PARTY_ROWS
ICUI.PARTY_XY = {}
for row = 1, ICUI.PARTY_ROWS do
    for col = 0, ICUI.PARTY_COLS - 1 do
        ICUI.PARTY_XY[#ICUI.PARTY_XY + 1] = {
            ICUI.PARTIES_X + col * (ICUI.PARTY_W + ICUI.PARTY_GAP_X),
            ICUI.PARTIES_Y + (row - 1) * (ICUI.PARTY_H + ICUI.PARTY_GAP_Y),
        }
    end
end

-- WHERE ic_lbl_section GOES ON THE COURT TAB, which is inside the Crown's box
-- rather than across the top of the panel. The component is shared by all five
-- views, so it cannot simply be moved - refresh() puts it here when the court
-- is up and back at ICUI.PANEL_XY.ic_lbl_section otherwise.
ICUI.COURT_SECTION_XY = {48, 665, 316, 26}

-- THE ACTION BAR WHILE THE COURT PAGES. Its home in PANEL_XY is centred under
-- the grid, which is where it almost always is: the court pages only when
-- confederates push it past the grid's slots. With the pager up the four
-- buttons and the pager do not fit one row of the grid's column, so the bar
-- moves to the left column's bottom row, centred under the Crown's box, level
-- with the pager. ACT_PAGED in tools/gen_ic_ui.py; the gate compares the two
-- entry by entry.
ICUI.ACT_PAGED_XY = {
    ic_act_provoke = {166, 978, 132, 34},
    ic_act_gift    = {304, 978, 164, 34},
    ic_act_secure  = {474, 978, 216, 34},
    ic_act_purge   = {696, 978, 100, 34},
    ic_act_hint    = {18, 982, 926, 26},
}

-- The party card's own children, panel-relative to the CARD. Must match
-- PARTY_LAYOUT in tools/gen_ic_ui.py; the gate compares them entry by entry.
-- THE CROWN'S BLOCK, as one list. It is shown by draw_leader and hidden by the
-- dispatcher, and a name in one of those and not the other is a label that never
-- leaves the screen.
-- THE COURT TAB'S OWN FURNITURE: the two column headers, the rule between
-- them and the plate the Crown's block sits on. Listed rather than named one by
-- one at each of the two call sites, because the fault when the two lists drift
-- is invisible on the court tab and only shows up on a different one.
ICUI.COLUMN_KEYS = {"ic_col_left", "ic_col_right", "ic_divider", "ic_crown_box"}

ICUI.LEADER_KEYS = {"ic_leader_lbl", "ic_leader_port", "ic_leader_name",
                    "ic_leader_party", "ic_leader_trait", "ic_leader_t1",
                    "ic_leader_t2"}

-- THE LEFT HALF OF THE CROWN'S BOX: the share, the band, and one line per
-- effect. Named rather than counted out of a loop: FX_KEYS in gen_ic_ui.py is
-- this list, and it refuses a band with more effects than there are lines.
ICUI.FX_KEYS = {"ic_control_fx", "ic_control_fx2", "ic_control_fx3",
                "ic_control_fx4"}
ICUI.CONTROL_KEYS = {"ic_control", "ic_control_band", "ic_control_fx",
                     "ic_control_fx2", "ic_control_fx3", "ic_control_fx4"}

-- NO BUTTON ON THE CARD ANY MORE (author, 2026-09-24). The mood was the label
-- of the one control, which opened the favour list; the word stays, as
-- ic_party_state, and the control is the card itself - click to choose the
-- party, click again for its members.
ICUI.PARTY_CHILD_XY = {
    ic_party_crest   = {30, 30, 24, 24},
    ic_party_name    = {60, 30, 365, 24},
    ic_party_name2   = {30, 58, 221, 24},
    ic_party_state   = {259, 58, 166, 24},
    ic_party_port    = {30, 88, 100, 55},
    ic_party_leader  = {138, 88, 287, 22},
    ic_party_ltrait  = {138, 112, 287, 22},
    ic_party_nums    = {138, 136, 287, 22},
    ic_party_t1      = {30, 162, 236, 22},
    ic_party_t2      = {30, 186, 236, 22},
    ic_party_trend   = {30, 210, 236, 22},
    ic_party_members = {270, 162, 155, 22},
    ic_party_offices = {270, 186, 155, 22},
    ic_party_govs    = {270, 210, 155, 22},
}
-- THE CHOSEN CARD'S FRAME, and the slot it goes in. The slot must match
-- PARTY_SEL_INDEX in tools/gen_ic_ui.py: slots 0 and 1 are the plate and the
-- border every card wears, so the frame is the third.
ICUI.PARTY_SEL_INDEX = 2
ICUI.PARTY_SELECTED =
    "ui/skins/default/dlc25_gunnery_school/frame_unit_card_selected.png"

ICUI.btn_at = nil
ICUI.view = "court"
-- Scroll offset PER VIEW. Shared state would jump the court list when the player
-- scrolled the governors list and came back.
ICUI.scroll = {court = 0, offices = 0, govs = 0, intrigue = 0, log = 0,
               petitions = 0,
               pick = 0}
-- THE CHOSEN PARTY, by slug and not by card: a card is a slot the pager
-- recycles, and a choice that followed the slot would jump to whichever party
-- the next page put there. Nil until the player clicks one; cleared on close.
ICUI.sel = nil
-- THE PETITIONS AS THEY WERE LAST DRAWN, one entry per row - {kind = "offer",
-- slug = ...} or {kind = "demand"} - so a click answers the petition the
-- player saw rather than a list re-derived after it changed.
ICUI.petition_rows = {}
-- How many lines the last draw had, so the scroll buttons know their own limit.
ICUI.line_count = 0
-- When set, the panel is choosing a character for something instead of showing a
-- view: {kind = "office", key = <office slug>} or {kind = "gov", key = <province>}.
-- It is its own mode rather than a fifth tab because it is modal - you are
-- answering a question, and the tabs are how you abandon it.
ICUI.pick = nil
-- The character cqi drawn on each row of the LAST picker draw, so a click on a
-- row resolves to a man without re-deriving the list and risking a different order.
ICUI.pick_rows = {}
-- A sentence explaining why the last click did nothing. Without it, an action the
-- rules refuse is indistinguishable from a dead button - which is exactly what
-- "the assign button does nothing" turned out to mean the first time.
ICUI.notice = nil
-- The province keys behind the governors list as it was last DRAWN, so a click
-- resolves against what the player actually saw rather than a freshly derived
-- list that may have changed between the draw and the click.
ICUI.gov_keys = {}

local function log(text)
    -- `out` IS A TABLE, NOT A FUNCTION. CA builds it in all_scripted.lua as
    -- `local out = {}` with one entry per channel (out.ui, out.design, ...) and
    -- then makes it callable with a `__call` metamethod. So out("x") works while
    -- type(out) == "table" - and the guard here was `type(out) == "function"`,
    -- which is never true. Every diagnostic this panel logged, including the
    -- whole opener-placement retry chain, was discarded silently from the day it
    -- was written; the script log for 2026-09-11 contains not one line of it.
    --
    -- pcall, because a callable table is still not guaranteed callable.
    if out then pcall(function() out("XXX derpy_ic " .. tostring(text) .. " XXX") end) end
end

local function root()
    return core:get_ui_root()
end

-- find_uicomponent returns FALSE, not nil. is_uicomponent is a TYPE test and a
-- DESTROYED component still passes it, which is why nothing here is ever cached.
local function comp(name, parent)
    local c = find_uicomponent(parent or root(), name)
    if is_uicomponent(c) then return c end
    return nil
end

-- core:get_screen_resolution() is literally ui_root:Dimensions(). It is
-- Dimensions() and NOT Bounds(): Bounds() is the extent INCLUDING children, so
-- while some HUD component is transiently oversized the root's bounds balloon
-- past the real display - and a guard asking that same inflated question passes a
-- button that is off screen.
local function screen()
    return root():Dimensions()
end

-- SetText writes EVERY state. SetStateText writes only the CURRENT one and takes
-- a stringtable KEY as its second argument, not a state name. Getting that wrong
-- cost the Great Guilds its Buy caption, and then cost this panel twice on
-- 2026-09-11 - with no script error either time:
--   * a tab caption blanked the instant the cursor arrived, because the string
--     had been written to `standard` and `hover` never got it;
--   * the GOVERNORS tab kept showing the INTRIGUE row, because the redraw
--     happened while the cursor was still over the component, so the new text
--     went to `hover` and `standard` kept the previous view's string.
-- The second one does not look like a text bug at all - it reads as a view that
-- failed to switch.
local function set_text(c, text)
    if not c then return end
    pcall(function() c:SetText(tostring(text), "") end)
end

local function loc(key, fallback)
    local ok, text = pcall(common.get_localised_string, key)
    if ok and text and text ~= "" then return text end
    return fallback or key
end

-- ---------------------------------------------------------------------------
-- The opener.
--
-- Asked for 2026-09-11: on the top resource strip, to the LEFT of the Great
-- Guilds' button, so the row reads Iron Court, Guilds, Exchange.
--
-- resources_bar IS THE ART. resources_bar_holder overhangs it by 133px left and
-- 94px right and describes nothing that is drawn, which is what once put a button
-- on open terrain. The strip is read as a RULER ONLY - this button is created on
-- the UI ROOT and never parented to anything, because a layout group owns its
-- children's positions and MoveTo never gets to have the fight. That is how the
-- rites ring ate two earlier anchors: button_rituals is one member of a
-- RadialList of radius 95.
--
-- Positions are DERIVED FROM THE STRIP, never read off the neighbouring buttons.
-- The Exchange's button teleported 133px because a fallback resolved to different
-- geometry while the real anchor was still loading. Two formulas over one anchor
-- cannot disagree; a read of a component that is still moving can.
-- ---------------------------------------------------------------------------
function ICUI.neighbours()
    -- EX and GGUI are globals in this same Lua state from the moment those
    -- scripts load, long before any HUD placement, so they are stable install
    -- tests with no race - unlike asking whether their button components exist
    -- yet, which is false for the first few seconds of every campaign either way.
    return (EX ~= nil and EX.BUTTON ~= nil), (GGUI ~= nil and GGUI.BTN_SIZE ~= nil)
end

function ICUI.btn_anchor()
    -- The ring first. It is where this button belongs; the resources strip below
    -- is the fallback for a HUD that has no Chaos Dwarf feature buttons in it.

    local bar = comp("resources_bar")
    if not bar then return nil, nil, "no resources_bar" end
    local bx, by = bar:Position()
    local bw, bh = bar:Dimensions()     -- Dimensions, not Bounds: full of children

    -- REFUSE AN UNSETTLED STRIP. resources_bar is animated - it slides in at load
    -- and leaves the top of the screen for cutscenes and end turn, reporting a far
    -- negative y while away. Read mid-slide it answers by = -64 with bh = 60, and a
    -- button placed from that lands ON the strip at a position that is still on
    -- screen, so every guard downstream passes it. Settled, by is -4. An off-screen
    -- READ is not an off-screen RESULT, and here is the only place it is catchable.
    if by < -ICUI.BTN_SIZE then return nil, nil, "unsettled" end

    -- Logged so the next run says exactly what geometry it worked from, rather
    -- than leaving the position to be inferred from a screenshot.
    local _have_ex, _have_gg = ICUI.neighbours()
    log(string.format("strip at %d,%d %dx%d; exchange=%s guilds=%s",
                      bx, by, bw, bh, tostring(_have_ex), tostring(_have_gg)))
    local ex_size = (EX and EX.BUTTON_SIZE) or 48
    local ex_gap = (EX and EX.BUTTON_GAP) or 4
    local gg_size = (GGUI and GGUI.BTN_SIZE) or 44

    local slot_x = bx + bw + ex_gap                 -- the Exchange's slot
    local have_ex, have_gg = ICUI.neighbours()

    -- The left edge of the leftmost button already on the row.
    local left_edge = slot_x
    if have_ex and have_gg then
        left_edge = slot_x - gg_size - ex_gap       -- the Guilds sits left of it
    end

    -- Centred on the STRIP, not on a neighbour's box: the Exchange's button is
    -- 48px and ours is 44, and centring on its box would leave the row 2px out of
    -- line. All three centre on the same strip, which is what makes them read as
    -- one row.
    local row_y = by + math.floor((bh - ICUI.BTN_SIZE) / 2)

    if have_ex or have_gg then
        -- Left means OUR right edge stops one gap short of their left edge, so
        -- the offset is our own width, not theirs - taking theirs is the easy way
        -- to overlap.
        return left_edge - ICUI.BTN_SIZE - ex_gap, row_y,
               string.format("left of %s, bar %d,%d %dx%d",
                             have_gg and "the guilds button" or "the exchange button",
                             bx, by, bw, bh)
    end
    local _ = ex_size
    return slot_x, row_y,
           string.format("in the exchange slot, bar %d,%d %dx%d", bx, by, bw, bh)
end

-- ---------------------------------------------------------------------------
-- THE STANDING PLATE, on CA's character details panel.
--
-- The banded trait already puts a man's standing in CA's own trait list. This is
-- the exact figure beside it, because a band answers "which tier" and a player
-- climbing towards one wants to know how far off he is.
--
-- CREATED ON THE UI ROOT, exactly like the opener and for the same reason: a
-- layout group owns its children's positions and MoveTo never gets to have the
-- fight. CA's panel is read as a RULER ONLY.
--
-- ONE ANCHOR, READ AT RUNTIME. dy_rank is CA's own rank readout on that panel -
-- every character has a rank, so it is always there when the panel is. Its
-- SETTLED position is asked for rather than any offset written down here, so
-- nothing in this file has to know what CA's panel looks like, and a CA layout
-- change moves the plate instead of orphaning it. No fallback anchor: two
-- formulas over one position cannot disagree, a second one can.
-- ---------------------------------------------------------------------------
ICUI.STANDING       = "derpy_ic_standing"
ICUI.PATH_STANDING  = "ui/campaign ui/derpy_ic_standing"
ICUI.STANDING_PANEL = "character_details_panel"
ICUI.STANDING_ANCHOR = "dy_rank"
ICUI.STANDING_W = 190
ICUI.STANDING_H = 22
-- Where the plate sits relative to the anchor's top-left. Nudge these two if it
-- lands somewhere CA is already drawing; nothing else needs to change.
ICUI.STANDING_DX = 0
ICUI.STANDING_DY = 26

-- Whose panel is open. CharacterSelected is the only thing that says so - the
-- panel itself carries a CCO context, and a parameterised CCO call null-derefs
-- the UI, so it is not asked.
ICUI.selected_cqi = nil

-- WHAT A SEAT COSTS, wearing the game's own loyalty icon.
--
-- [[img:<path>]][[/img]] is CA's inline image markup, not ours, and both
-- halves of what this line does are vanilla. Measured 2026-09-13 over every
-- .loc in the game's data folder: 5001 rows use it, naming 503 registry keys
-- and 156 full PATHS - ui/skins/default/icon_stat_armour.png in 61 rows by
-- itself - so naming a file needs no ui_text_replacements row of its own. And
-- CA builds the same markup into a string in Lua at runtime, in
-- script/campaign/wh3_dlc26_ogre_camps.lua, which is the half the loc rows
-- cannot speak to.
--
-- The picture goes INSIDE the string, so the card, the three picker titles,
-- both shortfalls and the hire line all carry it without a component between
-- them.
--
-- IN FRONT OF THE NUMBER, and nothing else about the line changes. The words
-- around it are left alone on purpose: if the picture ever fails to resolve,
-- every one of these reads exactly as it read before it had one.
--
-- gen_ic_ui.py check 23 holds this path against the same asset index every
-- imagepath in the panel is held against, and against its own copy of it,
-- which is what check 20c measures the cost cell with.
ICUI.COST_ICON = "ui/skins/default/icon_secure_loyalty.png"

-- AND WHAT A TRAIT DOES, MARKED AS AN EFFECT.
--
-- A party's two traits and its leader's one are effects on the court:
-- IC.loyalty_terms puts every one of them into the per-turn drift, scaled by
-- party_trait_scale. They were drawn as bare words in a stack of other bare
-- words, so nothing on the card said which lines were doing anything.
--
-- THE PICTURE THIS MOD'S OWN EFFECT BUNDLES ALREADY WEAR.
-- gen_iron_court.BUNDLE_ICON is this same file, so every bundle the Iron Court
-- mints carries it in the Faction Effects panel - a trait marked with it reads
-- as the same system rather than introducing a second glyph for one idea.
--
-- 24x24 AT FULL BLEED, which is a line box exactly. That is the half a name
-- cannot tell you and the preview can: the first pick here was the Tower of
-- Zharr's seat-effects glyph, which sounds ideal and is 56x56 with its opaque
-- content in a 28x38 box - a tall narrow mark that scaled into a line box as a
-- sliver. Measured, not judged by eye: fill 0.29 against this one's 1.00.
--
-- check 23 in gen_ic_ui.py holds this against the same asset index every
-- imagepath in the panel is held against, by the shape of the name rather than
-- one icon at a time - so declaring it here is the whole of what it needs.
ICUI.TRAIT_ICON = "ui/campaign ui/effect_bundles/chd_conclave_influence.png"


-- ONE TRAIT LINE, decorated. Nil and "" both come back empty and NOT as a bare
-- icon: both trait cells are written on every draw because the card pool
-- recycles, so a party with one trait instead of two - or one whose leader has
-- just died - would otherwise carry a picture of nothing.
-- WHAT ONE TRAIT IS WORTH, AND WHEN, for the cell the player points at.
--
-- FOUR PARTS IN ONE ORDER: the name, what it is doing RIGHT NOW, the rule that
-- produced that number, and the flavour last. The number first because it is
-- the question; the flavour last because it is the answer to a different one.
--
-- `n` IS PASSED IN, not computed. It comes from IC.loyalty_terms - the same
-- list the drift applies and the loyalty tooltip prints - so a trait cannot be
-- worth one thing on its own cell and another in the breakdown above it.
-- nil means the trait is not currently a term at all, and then the line is
-- simply left out rather than guessed at.
function ICUI.trait_tip(trait, n)
    if not trait then return "" end
    local lines = {trait.name}
    if n then
        lines[#lines + 1] = string.format("%s loyalty per turn, as it stands",
                                          ICUI.signed(n))
    end
    local rule = IC.trait_rule(trait)
    if rule then lines[#lines + 1] = rule end
    if trait.blurb and trait.blurb ~= "" then
        lines[#lines + 1] = ""
        lines[#lines + 1] = trait.blurb
    end
    return table.concat(lines, "\n")
end


-- EVERY TRAIT'S CURRENT VALUE, keyed by its own key. One walk of the breakdown
-- rather than one per cell: IC.loyalty_terms rebuilds the whole list on each
-- call and the card draws three trait cells.
function ICUI.trait_values(faction, slug)
    local by_key = {}
    local ok, terms = pcall(function()
        return IC.loyalty_terms(faction, slug)
    end)
    if not ok or not terms then return by_key end
    for i = 1, #terms do
        if terms[i].trait then by_key[terms[i].trait] = terms[i].n end
    end
    return by_key
end


function ICUI.trait_line(name)
    if not name or name == "" then return "" end
    return string.format("[[img:%s]][[/img]]%s", ICUI.TRAIT_ICON, name)
end


function ICUI.cost(n)
    return string.format("[[img:%s]][[/img]]%d", ICUI.COST_ICON, n)
end

-- WHAT THE PLAYER CANNOT HAVE, IN RED. Written once because the colour NAME is
-- the fragile part: the engine drops an unknown one silently, leaving ordinary
-- ink and no error, and "red" is the one CA uses 1,649 times.
--
-- It wraps rather than replaces, so a string that already carries an [[img:]]
-- keeps it - the plot price is an icon and a number, and colouring it by
-- rebuilding it would have dropped the icon.
ICUI.RED = "red"

function ICUI.red(text)
    return string.format("[[col:%s]]%s[[/col]]", ICUI.RED, tostring(text))
end

-- GOLD IS A SECOND CURRENCY IN THIS PANEL, and it was not until the favours
-- arrived: a plot spends a courtier's own standing, a favour spends the
-- treasury. Quoting 2500 gold under the standing icon would be worse than
-- quoting it bare, because the wrong unit reads as a fact rather than as a
-- missing one.
--
-- READ OUT OF CA'S ui2.pack, not guessed. A path the game does not ship draws a
-- blank white square and reports nothing at all.
ICUI.GOLD_ICON = "ui/skins/default/icon_treasury.png"

function ICUI.gold(n)
    return string.format("[[img:%s]][[/img]]%d", ICUI.GOLD_ICON, n)
end


function ICUI.standing_text(faction_key, cqi)
    return string.format("%d influence", IC.standing(faction_key, cqi))
end

function ICUI.ambition_tip(faction_key, cqi)
    if not faction_key or not cqi then return "" end
    local character = IC.character_by_cqi(faction_key, cqi)
    if not character then return "" end
    local court = IC.court(faction_key)
    local slug = IC.ambition_slug(faction_key, cqi)
    local house = IC.house_of_character(character, faction_key)
    if not slug or not house or not court.houses[house] then return "" end

    local name = loc("character_trait_levels_onscreen_name_derpy_ic_ambition_" .. slug, "")
    if name == "" then return "" end
    local factor = IC.ambition_factor(faction_key, cqi) / 100
    local contribution = IC.standing(faction_key, cqi) * factor
        / IC.TUNE.ambition_standing_per_weight
    contribution = string.format("%.2f", contribution):gsub("%.?0+$", "")
    return string.format("%s: %d influence x %.2f = %s for his party",
                         name, IC.standing(faction_key, cqi), factor, contribution)
end

-- Returns the plate's screen position, or nil and why not.
function ICUI.standing_anchor()
    local panel = comp(ICUI.STANDING_PANEL)
    if not panel then return nil, nil, "the character panel is not open" end
    local shown = true
    pcall(function() shown = panel:Visible() end)
    if not shown then return nil, nil, "the character panel is hidden" end
    local anchor = comp(ICUI.STANDING_ANCHOR, panel)
    if not anchor then return nil, nil, "no " .. ICUI.STANDING_ANCHOR end
    local ax, ay = anchor:Position()
    return ax + ICUI.STANDING_DX, ay + ICUI.STANDING_DY
end

-- Draw it, move it, or put it away. Called on every event that could change any
-- of the three, and safe to call when none of them did.
function ICUI.show_standing()
    local plate = comp(ICUI.STANDING)

    local function hide()
        if plate then
            pcall(function() plate:SetTooltipText("", "", true) end)
            pcall(function() plate:SetInteractive(false) end)
            pcall(function() plate:SetVisible(false) end)
        end
        return false
    end

    local cqi = ICUI.selected_cqi
    local faction = ICUI.player()
    if not faction then return hide() end
    -- ONLY A MAN OF OUR OWN COURT, and this ONE test covers both "nobody is
    -- selected" and "the selected man is somebody else's". There used to be a
    -- `not cqi` early-out above it, which could never be seen to fail: a nil cqi
    -- reads out of standing[] as nil and matches nothing in character_by_cqi, so
    -- it already lands here. Two guards covering each other means neither is
    -- observable, and the observable one is the one that matters - every
    -- listener in this file is global, and drawing "0 standing" on a Bretonnian
    -- lord is a mod advertising itself on a panel it has nothing to do with.
    if not IC.court(faction).standing[cqi]
            and not IC.character_by_cqi(faction, cqi) then
        return hide()
    end

    local x, y, why = ICUI.standing_anchor()
    if not x then
        if why and why ~= ICUI.standing_why then
            ICUI.standing_why = why
            log("standing plate: " .. why)
        end
        return hide()
    end
    ICUI.standing_why = nil

    -- A position off screen is a bad read, not a bad panel: refuse it rather
    -- than parking the plate in a corner.
    local sw, sh = screen()
    if x < 0 or y < 0 or x + ICUI.STANDING_W > sw or y + ICUI.STANDING_H > sh then
        log(string.format("standing plate: anchor put it at %d,%d on %dx%d",
                          x, y, sw, sh))
        return hide()
    end

    if not plate then
        pcall(function()
            root():CreateComponent(ICUI.STANDING, ICUI.PATH_STANDING)
        end)
        plate = comp(ICUI.STANDING)
        if not plate then return hide() end
    end
    plate:MoveTo(x, y)
    -- SetStateText and not SetText would write the current state only; this
    -- plate has one state, but set_text is what every other label here uses and
    -- a second idiom is a second thing to get wrong.
    set_text(plate, ICUI.standing_text(faction, cqi))
    local tip = ICUI.ambition_tip(faction, cqi)
    plate:SetTooltipText(tip, "", true)
    plate:SetInteractive(tip ~= "")
    pcall(function() plate:SetVisible(true) end)
    -- Created on the ui root, the plate is a SIBLING of the panel rather than a
    -- child, and siblings draw in hierarchy order - so CA's panel would paint
    -- straight over it. Same lesson as the opener.
    pcall(function() plate:RegisterTopMost() end)
    return true
end

function ICUI.place_opener(attempt)
    attempt = attempt or 1

    -- Every "not ready" branch routes through here so the chain cannot be given
    -- up on in one place and kept alive in another.
    local function retry(why)
        if ICUI.btn_at or attempt >= ICUI.BTN_TRIES then
            if not ICUI.btn_at then log("GAVE UP placing the opener: " .. tostring(why)) end
            return false
        end
        cm:callback(function() ICUI.place_opener(attempt + 1) end, 1)
        return true
    end

    -- The HUD is NOT laid out at first tick, so CREATION has to retry too, not
    -- just placement.
    local button = comp(ICUI.BTN)
    if not button then
        pcall(function() root():CreateComponent(ICUI.BTN, ICUI.PATH_OPENER) end)
        button = comp(ICUI.BTN)
        if not button then return retry("could not create the button") end
    end

    local x, y, why = ICUI.btn_anchor()
    if not x then return retry(why) end

    local sw, sh = screen()
    -- A SMALL OVERSHOOT IS CLAMPED, A WILD ONE IS RETRIED. The strip is animated,
    -- yet some cultures settle at y = -5, so a flat "y < 0 is wrong" refusal is
    -- also wrong.
    local tol = 120
    if x < -tol or y < -tol or x + ICUI.BTN_SIZE > sw + tol
            or y + ICUI.BTN_SIZE > sh + tol then
        return retry(string.format("anchor put it at %d,%d on a %dx%d screen",
                                   x, y, sw, sh))
    end
    if x < 0 then x = 0 end
    if y < 0 then y = 0 end
    if x + ICUI.BTN_SIZE > sw then x = sw - ICUI.BTN_SIZE end
    if y + ICUI.BTN_SIZE > sh then y = sh - ICUI.BTN_SIZE end

    button:MoveTo(x, y)
    pcall(function() button:SetVisible(true) end)
    -- AND THIS IS WHAT MAKES IT VISIBLE. Created on the ui root, the button is a
    -- SIBLING of hud_campaign rather than a child, and siblings draw in hierarchy
    -- order - so the HUD paints straight over it. The 2026-09-11 log has the
    -- button correctly created, anchored and moved ("opener placed at 1799,866")
    -- with nothing on screen, which is that and nothing else.
    --
    -- CA's doc entry, not the signature: "Registers this uicomponent to be drawn
    -- topmost. Topmost uicomponents are drawn outside of the normal hierarchy on
    -- the top of all other uicomponents."
    --
    -- BELT AND BRACES, NOT THE FIX, and an earlier comment here got that wrong.
    -- It claimed the Zharr Exchange was not installed and so proved nothing. It
    -- is installed - WH3 loads the STEAM WORKSHOP folder as well as data/, and
    -- the Exchange is live at workshop/content/1142710/3798516851/, enabled at
    -- used_mods.txt line 94. Its live script has no topmost and no priority call,
    -- and the same log shows the player clicking its button twice. A root-created
    -- button therefore DOES draw on the resources strip unaided.
    --
    -- The call stays because the Great Guilds ships it on this same HUD with no
    -- ill effect, and it retires the draw-order question rather than leaving it
    -- to be re-argued. The real fault was the position: the ring at 1799,866,
    -- where this button had no business being.
    --
    -- It does not fight our own panel: show_hud(false) hides every root child
    -- except the panel, and this button is one of them.
    pcall(function() button:RegisterTopMost() end)

    -- READ BACK. A layout group silently overriding MoveTo reports nothing at
    -- all, and this is the only thing in the engine that catches it.
    local gx, gy = button:Position()
    if gx ~= x or gy ~= y then
        log(string.format("layout override: asked for %d,%d and got %d,%d", x, y, gx, gy))
    end
    local moved = not (ICUI.btn_at and ICUI.btn_at[1] == gx and ICUI.btn_at[2] == gy)
    ICUI.btn_at = {gx, gy}
    -- READ BACK WHAT THE COMPONENT SAYS ABOUT ITSELF, not what we asked for. A
    -- button can report the right position and still not be on screen: drawn
    -- under the HUD, or sized to nothing. Logging its own visible flag, size and
    -- priority is the difference between knowing and inferring from a screenshot.
    local vis, bw2, bh2, prio = "?", "?", "?", "?"
    pcall(function() vis = tostring(button:Visible()) end)
    pcall(function()
        local a, b = button:Dimensions()
        bw2, bh2 = a, b
    end)
    pcall(function() prio = tostring(button:Priority()) end)
    -- ONLY WHEN IT MOVED. This runs again at every turn start, and a line a turn
    -- forever buries the one that matters.
    if moved then
        log(string.format("opener placed at %d,%d (%s) visible=%s %sx%s priority=%s",
                          gx, gy, tostring(why), vis, tostring(bw2), tostring(bh2),
                          tostring(prio)))
    end
    return true
end

-- ---------------------------------------------------------------------------
-- The panel.
-- ---------------------------------------------------------------------------
-- A PARTY'S EMBLEM. The crown's is the player's own faction flag, which needs
-- the faction key - and the draw functions below do not carry one, so it is
-- resolved here rather than added to nine signatures for the sake of one branch.
function ICUI.crest(slug)
    if not slug then return nil end
    return IC.house_icon(slug, ICUI.player())
end

function ICUI.player()
    local human = cm:get_human_factions()
    return human and human[1] or nil
end

-- PLACES EVERY COMPONENT, including the panel's own children, which the .twui.xml
-- offsets do not. MoveTo takes ABSOLUTE SCREEN COORDINATES even for a child:
-- being a child of the panel does NOT make it relative to the panel, so the
-- panel's own origin is added back on to every panel-relative offset here.
function ICUI.layout()
    local panel = comp(ICUI.PANEL)
    if not panel then return end
    local px, py = panel:Position()
    -- The content offset is added ONCE, here, so every child of every kind picks
    -- it up: the panel's own children, the cards and their children, and the rows
    -- and theirs all derive from px,py below.
    px = px + ICUI.OX
    py = py + ICUI.OY

    -- EVERY COMPONENT IS SIZED AS WELL AS PLACED. The box scales with the
    -- screen, and a component keeps the size its .twui.xml gave it until
    -- something resizes it - which below 1920 is a 1600 file in a 1760 box.
    for name, xy in pairs(ICUI.PANEL_XY) do
        local c = comp(name, panel)
        if c then
            c:MoveTo(px + xy[1], py + xy[2])
            ICUI.resize(c, xy[3], xy[4])
        end
    end

    -- A POOL: one component per point, each the pool's size, with its children
    -- placed from its own origin.
    local function pool(prefix, points, w, h, children)
        for i = 1, #points do
            local card = comp(prefix .. "_" .. i, panel)
            if card then
                card:MoveTo(px + points[i][1], py + points[i][2])
                ICUI.resize(card, w, h)
                local cx, cy = card:Position()
                for name, xy in pairs(children) do
                    local c = comp(name, card)
                    if c then
                        c:MoveTo(cx + xy[1], cy + xy[2])
                        ICUI.resize(c, xy[3], xy[4])
                    end
                end
            end
        end
    end
    pool(ICUI.CARD, ICUI.CARD_XY, ICUI.CARD_W, ICUI.CARD_H, ICUI.CARD_CHILD_XY)
    pool(ICUI.PARTY, ICUI.PARTY_XY, ICUI.PARTY_W, ICUI.PARTY_H, ICUI.PARTY_CHILD_XY)
    pool(ICUI.PLOT, ICUI.PLOT_XY, ICUI.PLOT_W, ICUI.PLOT_H, ICUI.PLOT_CHILD_XY)
    -- The rows are a pool on the pitch rather than on a grid.
    local rows = {}
    for i = 1, ICUI.MAX_ROWS do
        rows[i] = {ICUI.ROWS_X, ICUI.ROWS_Y + (i - 1) * ICUI.ROW_PITCH}
    end
    pool(ICUI.ROW, rows, ICUI.ROW_W, ICUI.ROW_H, ICUI.ROW_CHILD_XY)
end

-- Houses in a stable order. pairs() draws a different order every redraw and the
-- bar would shuffle under the player's cursor.
-- IN THE MODEL'S ORDER, and derived there. This used to walk IC.PARTIES itself,
-- which is two derivations of one rule - who is seated, and where each seat's
-- crest lands - and a disagreement between them puts one party's crest on
-- another party's colour.
function ICUI.court_slugs(faction_key)
    return IC.present_houses(faction_key)
end

-- THE CROWN CANNOT DO EITHER OF THE FIRST TWO. It never counts down -
-- tick_secession skips it and at_breaking_point refuses it by name - and no
-- plot in the system can be aimed at it, because can_plot answers "own party"
-- for a Crown victim. So the player's own card was drawing a countdown it could
-- not reach and a threat it could not make, and the author asked what happens
-- if it hits zero. What happens is IC.splinter, and that is what it says now.
--
-- THE SLUG IS PASSED IN rather than read off the house, because a house table
-- does not carry its own key and giving it one would be a second place for the
-- same fact to go wrong.
function ICUI.mood(house, slug)
    if slug == IC.CROWN then
        -- THE COUNT, WHEN THERE IS ONE. A rival on the way out reads
        -- "SECEDES 3" and the Crown read a bare "SPLINTERING" - the same
        -- situation stated two ways, one of them with the number the player
        -- needs. The count only exists once IC.splinter has started it, so the
        -- word is still the right answer on the turn the line is crossed and
        -- before the turn has run.
        if (house.split or 0) > 0 then
            return string.format("SPLITS %d", house.split)
        end
        if house.loyalty <= IC.TUNE.splinter_loyalty then return "SPLINTERING" end
    elseif (house.clock or 0) > 0 then
        return string.format("SECEDES %d", house.clock)
    elseif house.loyalty <= 25 then
        return "PLOTTING"
    end
    if house.loyalty <= 55 then return "RESTLESS" end
    return "LOYAL"
end

-- A countdown outranks the agenda: SECEDES 3 is the number the player acts on.
-- Then the most urgent thing the party is doing: a move landing next turn, a
-- demand with a deadline, a feud, an offer.
function ICUI.card_mood(faction, house, slug)
    local word = ICUI.mood(house, slug)
    if slug == IC.CROWN or not IC.agenda or (house.clock or 0) > 0 then
        return word
    end
    local a = IC.agenda(faction)
    if a.plot and a.plot.slug == slug then return "SCHEMING" end
    if a.demand and a.demand.slug == slug then return "DEMANDING" end
    if a.feuds[slug] then return "FEUDING" end
    if a.offers[slug] then return "OFFERING" end
    return word
end

local function turns_left(n)
    return string.format("%d turn%s left", n, n == 1 and "" or "s")
end

-- What a warned move will do, with the victim named.
function ICUI.plot_what(faction, p)
    local man = IC.character_by_cqi(faction, p.target)
    local who = man and ICUI.character_name(man) or "one of your men"
    if p.move == "unseat" then
        return string.format("%s struck from his seat as %s", who,
                             ICUI.office_name(p.key))
    elseif p.move == "recall" then
        return string.format("%s recalled from %s", who,
                             loc("provinces_onscreen_" .. tostring(p.key),
                                 tostring(p.key)))
    end
    return string.format("an accident at the forge for %s", who)
end

-- What an offer gives, with the man, party or army named. `row` is the
-- Petitions tab's terse form, which has one 860px line; the tooltip says the rest.
function ICUI.offer_what(faction, slug, o, row)
    if o.kind == "gold" then
        return string.format("%d gold", o.n)
    elseif o.kind == "backing" then
        local man = IC.character_by_cqi(faction, tonumber(o.target))
        return string.format("%d influence for %s", o.n,
                             man and ICUI.character_name(man) or "one of your men")
    elseif o.kind == "calm" then
        if row then
            return string.format("calm %s (+%d loyalty)",
                                 ICUI.house_name(o.target, faction), o.n)
        end
        return string.format("to calm %s. Their countdown stops and their "
            .. "loyalty rises by %d", ICUI.house_name(o.target, faction), o.n)
    end
    local units = loc("land_units_onscreen_name_" .. IC.troop_key(slug), "warriors")
    if row then return string.format("%d %s", o.n, units) end
    local lord = IC.character_by_cqi(faction, tonumber(o.target))
    return string.format("%d %s for %s's army", o.n, units,
        lord and ICUI.character_name(lord) or "one of your lords")
end

-- The event cards cannot name anyone; this tooltip is where names go. One
-- paragraph per thing the party is doing, most urgent first.
function ICUI.agenda_tip(faction, slug)
    if slug == IC.CROWN or not IC.agenda then return "" end
    local a = IC.agenda(faction)
    local now = cm:model():turn_number()
    local parts = {}
    local p = a.plot
    if p and p.slug == slug then
        local move = IC.party_move_by_key(p.move)
        local plotter = IC.character_by_cqi(faction, p.actor)
        parts[#parts + 1] = string.format("MOVING AGAINST YOU: %s, next turn. "
            .. "Raise their loyalty above %d, or deal with %s, to stop it.",
            ICUI.plot_what(faction, p), move and move.line or 0,
            plotter and ICUI.character_name(plotter) or "their plotter")
    end
    local d = a.demand
    if d and d.slug == slug then
        local man = IC.character_by_cqi(faction, d.cqi)
        local who = man and ICUI.character_name(man) or "their man"
        local what
        if d.kind == "office" then
            what = string.format("seat %s as %s", who, ICUI.office_name(d.key))
        else
            what = string.format("make %s overseer of %s", who,
                loc("provinces_onscreen_" .. tostring(d.key), tostring(d.key)))
        end
        parts[#parts + 1] = string.format("DEMANDS: %s, %s. Grant it and their "
            .. "loyalty rises by %d; refuse it, or let it run out, and it falls "
            .. "by %d. Answer it on the Petitions tab.", what, turns_left(d.ends - now),
            IC.TUNE.party_demand_met, IC.TUNE.party_demand_refused)
    end
    local rec = a.feuds[slug]
    if rec then
        local enemy = rec.a == slug and rec.b or rec.a
        parts[#parts + 1] = string.format("FEUDING with %s (%s) until turn %d. "
            .. "While it lasts they strike at each other, not at you.",
            ICUI.house_name(enemy, faction),
            rec.cause == "seat" and "a stolen seat" or "rivals of equal size",
            rec.ends)
    end
    local o = a.offers[slug]
    if o then
        parts[#parts + 1] = string.format("OFFERS: %s. %s. Answer it on the "
            .. "Petitions tab. Accepting costs %d loyalty with every other party.",
            ICUI.offer_what(faction, slug, o), turns_left(o.ends - now),
            IC.TUNE.party_offer_envy)
    end
    return table.concat(parts, "\n\n")
end

-- The warned move, for the Intrigue tab's one alert line.
function ICUI.plot_alert(faction)
    if not IC.agenda then return nil end
    local p = IC.agenda(faction).plot
    if not p then return nil end
    return string.format("%s moves against you next turn: %s.",
                         ICUI.house_name(p.slug, faction), ICUI.plot_what(faction, p))
end

-- Segment widths for the standing bar. Returned as a list so the arithmetic can
-- be checked without a running game: the parts must sum to exactly the total, or
-- bar visibly under- or over-fills.
function ICUI.bar_widths(faction_key, slugs, total_w)
    total_w = total_w or ICUI.DIAL_SLICES
    local n = #slugs
    local widths, order, used = {}, {}, 0
    for i = 1, n do
        local exact = total_w * IC.share(faction_key, slugs[i]) / 100
        local floor = math.floor(exact)
        -- A SEATED PARTY IS ALWAYS ON THE DIAL. A party rounded to nothing is
        -- one the player cannot see is there, and the smallest party in the
        -- court is usually the one about to matter.
        widths[i] = (floor < 1) and 1 or floor
        used = used + widths[i]
        order[i] = {i = i, rem = exact - floor}
    end
    -- LARGEST REMAINDER FIRST, and the index breaks the tie: table.sort is not
    -- stable, and a comparator that answers false both ways leaves the order to
    -- the sort - which would draw a different dial on two loads of one save.
    table.sort(order, function(a, b)
        if a.rem ~= b.rem then return a.rem > b.rem end
        return a.i < b.i
    end)
    local k = 1
    while used < total_w and n > 0 do
        widths[order[k].i] = widths[order[k].i] + 1
        used = used + 1
        k = k + 1
        if k > n then k = 1 end
    end
    -- AND IF THE FLOOR OF ONE OVERSPENT IT, take it back from the biggest run,
    -- which is the one that can least notice. The guard is for a court with
    -- more parties than the dial has pips: impossible while IC.MAX_SEATS is
    -- under DIAL_SLICES, and an infinite loop rather than a wrong dial if that
    -- ever stops being true.
    while used > total_w do
        local big, bw = nil, 1
        for i = 1, n do
            if widths[i] > bw then big, bw = i, widths[i] end
        end
        if not big then break end
        widths[big] = widths[big] - 1
        used = used - 1
    end
    return widths
end

-- THE COURT AS A RUN OF PIPS, in seating order and with no gaps. A pip belongs
-- to nobody until it is handed a picture, so - unlike the segments this
-- replaced - there is no per-party index to keep and nothing a secession can
-- recolour.
-- THE WALL AT THE ANGLE SLICE i BEGINS ON. Slice zero has none: a run that
-- starts there starts at the left end of the baseline, where the rail already
-- is, so gen_ic_ui.py generates div_01 upward and nothing asks for div_00.
function ICUI.div_path(i)
    return string.format("ui/derpy_ic/div_%02d.png", i)
end


function ICUI.dial_slots(faction_key, court)
    local slugs = ICUI.court_slugs(faction_key)
    local counts = ICUI.bar_widths(faction_key, slugs, ICUI.DIAL_SLICES)
    local slots, used = {}, 0
    for i = 1, #slugs do
        slots[i] = {slug = slugs[i], from = used, n = counts[i]}
        used = used + counts[i]
    end
    return slots
end

-- Which tab selects which view. The four tabs were created, drawn and clickable
-- from the first build but nothing ever read the click: ICUI.view was assigned
-- once and never again, so every tab redrew the court. Reported from play
-- 2026-09-11 as "the buttons are not moving tabs".
ICUI.TAB_VIEW = {
    ic_tab_court    = "court",
    ic_tab_offices  = "offices",
    ic_tab_govs     = "govs",
    ic_tab_intrigue = "intrigue",
    ic_tab_log      = "log",
    ic_tab_petitions = "petitions",
}

-- ---------------------------------------------------------------------------
-- SORTING, on the two views that have something to sort.
--
-- THE CHARACTER PICKER FIRST, because that is the list with a real problem.
-- IC.candidates walks faction:character_list() and hands back whatever order the
-- engine gave it - not alphabetical, not by rank, not by anything a player can
-- predict - and that is the list he reads to fill fourteen seats and every
-- province. By the mid game it is twenty or thirty men deep and finding the one
-- he wants is hunting rather than choosing.
--
-- ONE ENTRY PER COLUMN, and `col` is the whole of the binding between a mode and
-- the arrow that chooses it. Offices is a fixed ziggurat whose SHAPE is the
-- information, governors is one row per province in map order, and the record is
-- chronological - reordering any of the three destroys what it says. The
-- intrigue grid is sixteen cards in four named columns that all fit on screen at
-- once, so it has nothing to hunt through either.
--
-- THE COURT IS NOT HERE ANY MORE. It draws party cards rather than a row list,
-- so it has no header strip to hang an arrow under, and what it had instead was
-- one wide SORT button living alone on one tab - which is the control this
-- replaced. Its cards draw in court order and nothing reorders them.
--
-- ENTRY ONE IS THE ORDER THE LIST ALREADY HAD and carries no `col`, so no arrow
-- selects it: it is what the third click on a column returns to. A sort whose
-- every setting is a sort gives the player no way back to the arrangement he
-- has learnt.
ICUI.SORTS = {
    -- "pick" is what ICUI.live_view answers for EVERY character list: the office
    -- picker, the governor picker, both plot lists and a house's roster. They
    -- share this view's headers, column widths and scroll offset, and they share
    -- its sort for the same reason - they are one list of men asked five
    -- different questions.
    pick = {
        {key = "default",  name = "ROSTER ORDER"},
        {key = "name",     name = "NAME",      col = 1},
        {key = "party",    name = "PARTY",     col = 2},
        {key = "rank",     name = "RANK",      col = 3},
        {key = "standing", name = "INFLUENCE", col = 4},
        {key = "ready",    name = "AVAILABLE", col = 5},
    },
    -- THE GOVERNORS LIST, which is one row per province in map order. Map order
    -- is worth keeping as entry one - it is the order the player's own eye
    -- learns off the campaign map - but a court of thirty provinces is a list he
    -- hunts through, and that is what the other three are for.
    --
    -- COLUMN 3 IS NOT HERE. It held the overseer's party and now holds nothing:
    -- the crest beside his name says the same thing, and the column was a second
    -- copy of one fact clipping itself at 120px.
    govs = {
        {key = "default",  name = "MAP ORDER"},
        {key = "province", name = "PROVINCE", col = 1},
        {key = "overseer", name = "OVERSEER", col = 2},
        {key = "loyalty",  name = "LOYALTY",  col = 4},
    },
}

-- Which entry each view is on, and which way round. SESSION STATE, like
-- ICUI.view and ICUI.scroll: it is not packed and it is not saved. A sort order
-- is how the player is reading the panel right now, not a fact about his court,
-- and keeping it out of the save means no fifteenth field and no migration.
ICUI.sort = {pick = 1, govs = 1}
ICUI.sort_desc = {pick = false, govs = false}

function ICUI.sort_mode(view)
    local list = ICUI.SORTS[view]
    if not list then return nil end
    return list[ICUI.sort[view] or 1] or list[1]
end

-- WHICH COLUMN THAT ARROW SORTS, or nil when this view does not sort that one.
function ICUI.sort_for_column(view, col)
    local list = ICUI.SORTS[view]
    if not list then return nil end
    for i = 1, #list do
        if list[i].col == col then return i, list[i] end
    end
    return nil
end

-- CLICKING A COLUMN'S ARROW. Three steps and not two, which is one more than
-- CA's own control has: a first click sorts the column the way the comparator
-- is written, a second reverses it, and a THIRD hands the list back in roster
-- order. CA's arrows have no way back because CA's lists have no meaningful
-- starting order; this one does - it is the order the faction's character list
-- came in, which is the order the player has been reading all campaign.
--
-- Returns false when the column does not sort on this view, so the caller can
-- leave the panel alone rather than redrawing it for nothing.
function ICUI.click_column(view, col)
    local index = ICUI.sort_for_column(view, col)
    if not index then return false end
    if ICUI.sort[view] ~= index then
        ICUI.sort[view] = index
        ICUI.sort_desc[view] = false
    elseif not ICUI.sort_desc[view] then
        ICUI.sort_desc[view] = true
    else
        -- BACK TO THE TOP OF THE LIST, entry one, which carries no column.
        ICUI.sort[view] = 1
        ICUI.sort_desc[view] = false
    end
    -- BACK TO THE TOP OF THE PAGE TOO. The page offset addresses a position, and
    -- after a re-sort position N is a different man - so a player on page two
    -- would be looking at a page he never asked for.
    ICUI.scroll[view] = 0
    return true
end

-- table.sort IS NOT STABLE and a comparator that can answer "equal" both ways
-- will happily produce a different order for the same court on two draws of one
-- save. Every comparator below therefore ends on a total tiebreak - the slug or
-- the move key, which are unique by construction - exactly as IC.candidates and
-- ICUI.bar_widths already do.
local function by(cmp, tie)
    return function(a, b)
        local x, y = cmp(a), cmp(b)
        if x ~= y then return x < y end
        return tie(a) < tie(b)
    end
end


-- REORDER A CHARACTER PICKER, both halves of it together.
--
-- `lines` and `ICUI.pick_rows` are PARALLEL BY INDEX - on_pick_click reads
-- pick_rows[row + scroll] and nothing else connects a drawn row back to a man -
-- so the two are permuted by the same permutation or the panel offers one
-- candidate and appoints another. That is why this takes both tables and why it
-- sorts an index list rather than either of them.
--
-- THE HIRE ROWS ARE NOT CANDIDATES AND STAY WHERE THEY ARE. They are appended
-- after the men on the office picker and they are the bottom of the list by
-- design: "I have nobody for this" is answered under the men, not among them.
-- `n` is how many of the rows are real candidates.
--
-- Each candidate line carries its own `sort` keys, written in the loop that
-- built it, because the two that matter cannot be recovered afterwards: `ready`
-- is whether the click will accept him, which lives in pick_rows, and `standing`
-- is a number the cell has already wrapped in words.
function ICUI.sort_rows(view, lines, rows, n)
    local mode = ICUI.sort_mode(view)
    if not mode or mode.key == "default" then return end
    local order = {}
    for i = 1, n do order[i] = i end
    local function k(i) return lines[i] and lines[i].sort or {} end
    -- ONE TIEBREAK FOR ALL OF THEM: the name, then the cqi. table.sort is not
    -- stable in Lua, and a picker that reshuffles between two refreshes of one
    -- unchanged court is a picker the player cannot learn.
    local function tie(i)
        return (k(i).name or "") .. "\1" .. string.format("%012d", k(i).cqi or 0)
    end
    local cmp
    if mode.key == "ready" then
        -- WHO YOU CAN ACTUALLY APPOINT, AND THE BEST OF THEM FIRST. The refused
        -- men stay on the list underneath - IC.candidates lists them on purpose,
        -- because "already Keeper of the Chains" is an answer and an omission is
        -- not - but they stop standing between the player and the men he can
        -- have. Standing is the secondary key because it is the bar every one of
        -- these lists is gated on.
        --
        -- WRITTEN OUT RATHER THAN FOLDED INTO ONE NUMBER. The obvious form is
        -- `(ready and 0 or 1) * BIG - standing`, and it is correct only while
        -- standing stays under BIG: standing accrues every turn and has no
        -- ceiling in the model, so a late campaign would silently start sorting
        -- a rich refused man above a poor available one.
        cmp = function(a, b)
            local ra, rb = k(a).ready and 1 or 0, k(b).ready and 1 or 0
            if ra ~= rb then return ra > rb end
            local sa, sb = k(a).standing or 0, k(b).standing or 0
            if sa ~= sb then return sa > sb end
            return tie(a) < tie(b)
        end
    elseif mode.key == "standing" then
        cmp = by(function(i) return -(k(i).standing or 0) end, tie)
    elseif mode.key == "rank" then
        cmp = by(function(i) return -(k(i).rank or 0) end, tie)
    elseif mode.key == "province" or mode.key == "overseer" then
        -- A TO Z, because a province list is something the player HUNTS
        -- through: he knows the name and wants the row, which is the one
        -- question an alphabetical order answers and no other order does.
        cmp = by(function(i) return k(i)[mode.key] or "" end, tie)
    elseif mode.key == "loyalty" then
        -- LOWEST FIRST, the same choice the court's loyalty sort made and for
        -- the same reason: the province worth finding is the one about to turn,
        -- not the one that is content.
        cmp = by(function(i) return k(i).loyalty or 0 end, tie)
    elseif mode.key == "party" then
        -- GROUPED BY HOUSE, BEST MAN OF EACH FIRST. Grouping alone would
        -- put the houses in a readable order and leave the choice inside
        -- each one unmade; influence is the bar every one of these lists
        -- is gated on, so it is the same secondary key AVAILABLE uses and
        -- for the same reason.
        --
        -- THE UNALIGNED GO UNDER ALL OF THEM. "None" is an answer rather
        -- than a house, and almost every rolled party name begins "The",
        -- so a plain alphabetical order would float every man of no party
        -- to the TOP of the list - the opposite of where a grouping order
        -- wants him.
        cmp = function(a, b)
            local ua = k(a).unaligned and 1 or 0
            local ub = k(b).unaligned and 1 or 0
            if ua ~= ub then return ua < ub end
            local pa, pb = k(a).party or "", k(b).party or ""
            if pa ~= pb then return pa < pb end
            local sa, sb = k(a).standing or 0, k(b).standing or 0
            if sa ~= sb then return sa > sb end
            return tie(a) < tie(b)
        end
    elseif mode.key == "name" then
        cmp = by(function(i) return k(i).name or "" end, tie)
    else
        return
    end
    -- AND THE OTHER WAY ROUND ON THE SECOND CLICK. Swapping the arguments
    -- reverses the tiebreak along with the key, which is what keeps the reversed
    -- order as total as the forward one: two men equal on the key still cannot
    -- compare equal both ways.
    if ICUI.sort_desc[view] then
        local forward = cmp
        cmp = function(a, b) return forward(b, a) end
    end
    table.sort(order, cmp)
    -- REWRITTEN FROM COPIES. Writing straight back into `lines` would overwrite
    -- an entry the permutation has not read yet.
    local was_lines, was_rows = {}, {}
    for i = 1, n do was_lines[i], was_rows[i] = lines[i], rows[i] end
    for i = 1, n do
        lines[i] = was_lines[order[i]]
        rows[i] = was_rows[order[i]]
    end
end

-- THE ARROWS, AND WHICH COLUMN IS ACTUALLY SORTING.
--
-- CA's own panel draws an identical arrow under every column and says nothing
-- about which one is in force - see ui/campaign ui/labour_economy.twui.xml,
-- which is where this control comes from. That is a fault worth not copying: on
-- a list the player has just reordered, "by what?" is the only question.
--
-- SO THE HEADER SAYS IT, not the arrow. Every column keeps its arrow, because an
-- arrow is the affordance that says the column CAN be sorted; the active one is
-- named by tinting its label, which costs one SetText the strip already makes.
ICUI.SORT_LIT = "yellow"

-- INDEX 0 IS THE STANDARD STATE'S LAYER AND 1 THE HOVER STATE'S - the emitter
-- writes every standard layer into <componentimages> and then every hover layer,
-- and an arrow has one of each. Both are set, or an arrow flipped to "up" would
-- drop back to "down" under the cursor.
ICUI.SORT_ARROW = {
    down = "ui/skins/default/parchment_sort_arrow_down.png",
    up   = "ui/skins/default/parchment_sort_arrow_up.png",
}

-- 3 centres an 18px arrow in the 24px header strip, and 6 is the gap the
-- caption already has in front of it - LABEL_TX in tools/gen_ic_ui.py - so the
-- arrow sits as far past the text as the text sits past its own cell edge.
ICUI.HSORT_DY = 3
ICUI.HSORT_GAP = 6

-- HOW FAR ALONG ITS CELL A HEADER'S CAPTION REACHES.
--
-- A CELL THE ENGINE HAS NOT LAID OUT YET MEASURES ZERO, which would stack every
-- arrow on its column's left edge, on top of the first letter. The estimate
-- behind it is deliberately generous - an arrow a few pixels too far right reads
-- as a gap, one too far left reads as a fault.
function ICUI.hdr_text_w(c, text)
    text = tostring(text or "")
    if text == "" then return ICUI.HSORT_GAP end
    local got = nil
    if c then pcall(function() got = c:TextDimensionsForText(text) end) end
    if not got or got <= 0 then got = #text * 11 end
    return ICUI.HSORT_GAP + got + ICUI.HSORT_GAP
end

function ICUI.sort_arrow_path(view, col)
    local index = ICUI.sort_for_column(view, col)
    -- NOT THE ACTIVE COLUMN: it points down, which is what an unpressed arrow
    -- looks like in every CA panel that has one.
    if not index or ICUI.sort[view] ~= index then return ICUI.SORT_ARROW.down end
    return ICUI.sort_desc[view] and ICUI.SORT_ARROW.up or ICUI.SORT_ARROW.down
end

-- WHICH TAB YOU ARE ON. Five identical plates said nothing about which one
-- was showing, so the panel read as five buttons beside a list that changed for
-- no visible reason.
--
-- CA's own selected plate, swapped into the layer the tab already has. A third
-- <state> would be the tidier answer and costs a third GUID slot in the emitter
-- plus every check that counts them; this is the same picture for one call.
--
-- INDEX 0 IS THE STANDARD STATE'S LAYER AND 1 THE HOVER STATE'S - the emitter
-- writes every standard layer into <componentimages> and then every hover
-- layer, and a tab has one of each. Both are set, or the lit tab would drop
-- back to the unlit plate under the cursor.
ICUI.TAB_PLATE = {
    [0] = {on  = "ui/skins/default/button_square_medium_text_selected.png",
           off = "ui/skins/default/button_square_medium_text_active.png"},
    [1] = {on  = "ui/skins/default/button_square_medium_text__selected_hover.png",
           off = "ui/skins/default/button_square_medium_text_hover.png"},
}

-- ICUI.view, not ICUI.live_view(): the picker is modal, and the tab behind it
-- stays lit because that is where closing it puts you back.
function ICUI.light_tabs(panel)
    for name, view in pairs(ICUI.TAB_VIEW) do
        local c = comp(name, panel)
        if c then
            local lit = (view == ICUI.view)
            for index = 0, 1 do
                local art = ICUI.TAB_PLATE[index]
                pcall(function()
                    c:SetImagePath(lit and art.on or art.off, index)
                end)
            end
        end
    end
end

ICUI.SECTION = {
    court    = "Influence in the court",
    offices  = nil,   -- built from the court itself; see ICUI.section_text
    govs     = "Provinces and their overseers - an overseer governs only while he stands in his own province",
    intrigue = "Who is moving against you, and what you can spend to answer it",
    log      = "The court's record, newest first",
    -- NO petitions ENTRY: its label quotes three numbers out of IC.TUNE, so
    -- ICUI.petitions_label builds it, the way section_text builds the offices'.
}

-- The label above the list. DERIVED for the offices tab, because the court's
-- shape is a thing the player can read off the screen and a sentence that
-- counts the seats in prose goes stale the moment a tier gains one.
function ICUI.section_text(view)
    if view == "petitions" then return ICUI.petitions_label() end
    if view ~= "offices" then return ICUI.SECTION[view] or "" end
    local widths = {}
    for i = 1, #IC.TIERS do
        widths[#widths + 1] = tostring(IC.TIER_SEATS[IC.TIERS[i]])
    end
    return string.format(
        "%d seats in %d tiers (%s) - a seat needs the influence beside it, and is held for %d turns",
        #IC.OFFICES, #IC.TIERS, table.concat(widths, "/"), IC.TUNE.term_turns)
end

-- Column headers per view, or nil for a view that draws cards instead of a list.
-- The five row columns are shared by every list view, so the headers have to be
-- rewritten on each switch rather than set once at open.
ICUI.HEADERS = {
    -- NIL, like the offices tab's and for the same reason: the court draws
    -- cards now, and a header strip over a card grid labels nothing. The
    -- dispatcher hides the strip whenever this is nil, so removing the row is
    -- the whole of the change.
    court    = nil,
    offices  = nil,
    -- COLUMN THREE IS BLANK ON PURPOSE. It said "Party", and the crest drawn
    -- beside the overseer's name already says which one - two copies of one
    -- fact, and the narrower of the two was clipping every row to
    -- "Servants of the ...". Loyalty keeps column four rather than sliding
    -- left, so the row reads the same as it did minus one cell.
    govs     = {"Province", "Overseer", "", "Loyalty", ""},
    -- INTRIGUE IS nil LIKE THE COURT, and for the same reason: it draws no row
    -- list at all. Its moves are a grid of cards with their own column headings
    -- (ic_plotcat_N), and a "Cost / Move" strip left behind sat across the top of
    -- them naming columns that are not there.
    intrigue = nil,
    -- The Event text moves to column TWO on this view, because that is the
    -- column ICUI.COL_W widens. A header left in column three would sit over an
    -- empty cell.
    log      = {"Turn", "Event", "", "", ""},
    -- COLUMN FIVE HAS NO CAPTION because it is not one column: ACCEPT and
    -- REFUSE sit in it side by side, and each says what it does.
    petitions = {"From", "Petition", "", "", ""},
}

ICUI.HDR_KEYS = {"ic_hdr_a", "ic_hdr_b", "ic_hdr_c", "ic_hdr_d", "ic_hdr_e"}
-- PARALLEL BY INDEX TO HDR_KEYS, which is what makes arrow i column i. The
-- two are walked by one loop in ICUI.refresh for exactly that reason.
ICUI.HSORT_KEYS = {"ic_hsort_a", "ic_hsort_b", "ic_hsort_c", "ic_hsort_d",
                   "ic_hsort_e"}
ICUI.HSORT_INDEX = {}
for _i = 1, #ICUI.HSORT_KEYS do ICUI.HSORT_INDEX[ICUI.HSORT_KEYS[_i]] = _i end
ICUI.ROW_KEYS = {"ic_row_a", "ic_row_b", "ic_row_c", "ic_row_d", "ic_row_e",
                 "ic_row_f"}
-- THE TWO BUTTON CELLS, by column. A button with no label is still a plate,
-- so fill_rows hides each one on a line that leaves it empty - which is every
-- line but a petition's, for the sixth.
ICUI.ROW_BUTTONS = {[5] = true, [6] = true}
-- THE COLUMNS ARE SHARED BY EVERY LIST, and their widths are not. A Loyalty
-- value is two digits and an event is a sentence; one static set of widths has
-- to clip one or waste space on the other, and it clipped - "A house takes
-- Keeper of the ..." is column three at 180px, which twui will not wrap.
--
-- Defaults MUST match the w of each entry in ROW_LAYOUT in tools/gen_ic_ui.py;
-- the packing gate compares them.
-- THE ROW REBALANCED BY MEASUREMENT, 2026-09-17. Character carries a position
-- name in front of the man now and was already too narrow without one, so it
-- went 380 -> 537. The 157 came from Rank (130 -> 45, because the kind left it
-- and a two-digit number measures 26), from Influence's own slack (520 -> 490
-- against a 475 worst case) and from the 72px gutter in front of the button.
--
-- PARTY IS UNTOUCHED AT 360 ON PURPOSE. Its widest rolled name is 342. The
-- 2026-09-16 build funded this column out of that one and clipped every party
-- name on screen; this one does not.
ICUI.COL_WH = {{502, 26}, {360, 26}, {45, 26}, {490, 26}, {170, 32}, {110, 32}}
-- Per-view width overrides, by column index. Only the Event column moves: it
-- runs from column two's x to just short of the action button.
--
-- 970, AND IT HAS BEEN 1102 AND 935 TODAY. Column two's x is the left edge of
-- this measurement and it has moved twice: 157px right in the morning's
-- rebalance, then 35px back left when check 20k found the Rank arrow standing
-- on the Influence heading. Leaving it alone either time would run the Event
-- text under the action button on every row of the record.
ICUI.COL_W = {
    log      = {[2] = 970},
    -- NO intrigue ENTRY. That tab widened column two to hold "name - blurb" in
    -- one cell; the moves are cards now and it draws no rows at all, so an
    -- override here would be a width nothing reads.
    -- THE PETITION RUNS TO REFUSE. Column two's x to 10px short of ic_row_f,
    -- over the two cells this view leaves empty.
    petitions = {[2] = 860},
}
-- Set form, so a check can ask "is this cell one fill_rows writes?" without a
-- linear scan. The crest cell is deliberately NOT in here: it is set by
-- ICUI.set_row_icon, not by the text loop.
ICUI.ROW_KEYS_SET = {}
for _, k in ipairs(ICUI.ROW_KEYS) do ICUI.ROW_KEYS_SET[k] = true end

local function show(c, on)
    if c then c:SetVisible(on and true or false) end
end

-- get_forename/get_surname return LOC KEYS, not text. Printing one raw puts
-- "names_name_2147493104" on the card. Resolved at draw time, never in a turn
-- handler - a loc call from one of those is a turn-1 CTD that pcall misses.
function ICUI.character_name(character)
    if not character or character:is_null_interface() then return "" end
    local ok, fore = pcall(function() return loc(character:get_forename(), "") end)
    local ok2, sur = pcall(function() return loc(character:get_surname(), "") end)
    fore = (ok and fore) or ""
    sur = (ok2 and sur) or ""
    local name = fore
    if sur ~= "" then
        if name ~= "" then name = name .. " " .. sur else name = sur end
    end
    if name == "" then return "Unnamed" end
    return name
end

-- The largest first-line index that still fills the window, so scrolling can
-- never strand the list on a screen of blanks. Pure arithmetic, checked offline.
function ICUI.max_scroll(total, visible)
    local max = total - visible
    if max < 0 then max = 0 end
    return max
end

-- WHICH ROW OF THE POOL A VIEW STARTS AT. All of them start at the top now.
-- The court used to start lower, to clear a pie drawn above the list; the pie
-- is in the left column and the court draws no list at all, so the exception
-- and the constant behind it are both gone.
function ICUI.first_row(view)
    return 1
end

-- HOW MANY ROWS THAT LEAVES, which is the page size as well as the window: a
-- pager that pages by the pool would skip the rows the court cannot draw.
function ICUI.rows_shown(view)
    -- THE COURT TAB IS A CARD GRID. Its page is ten cards, and a pager still
    -- measuring the row pool would page in sevens through a grid of ten and
    -- leave three parties nobody can reach.
    if view == "court" then return ICUI.PARTY_SLOTS end
    -- AND THE INTRIGUE TAB DRAWS NO ROWS AT ALL. It is four columns of cards
    -- with their own headers; the warnings that used to sit above them ride
    -- ic_alert now, because four cards deep leaves no band to put them in.
    if view == "intrigue" then return 0 end
    return ICUI.MAX_ROWS - ICUI.first_row(view) + 1
end

-- Clamp and store this view's offset. Called on every draw, so a list that
-- SHRINKS under a parked offset (a province lost, a house seceding) pulls the
-- window back up instead of showing nothing.
function ICUI.clamp_scroll(view, total)
    local max = ICUI.max_scroll(total, ICUI.rows_shown(view))
    local at = ICUI.scroll[view] or 0
    if at > max then at = max end
    if at < 0 then at = 0 end
    ICUI.scroll[view] = at
    return at
end

-- Thumb geometry for a track of `track_h`: proportional height, floored so it
-- stays grabbable, positioned by how far through the list we are.

-- Fill the shared row pool from five-column lines, windowed by this view's scroll
-- offset, and hide the tail. Every list view goes through this, so no view can
-- forget to hide the rows the previous one left behind.
-- THE REAL PORTHOLE - the same image the lord recruitment panel draws.
--
-- CcoCampaignCharacter.PortraitPath is the property CA's own panels read;
-- cco/documentation.html describes it as "Returns portrait image path used on
-- portholes". Three traps, every one of them already paid for:
--
--   1. Its Arguments column says Void, and that is what makes it SAFE to read
--      from script. A PARAMETERISED CCO call - AgentSubtypeCap(key) and friends -
--      hard-crashes the game with a null deref at Warhammer3.exe+0x1F368AC that
--      pcall cannot catch. Only bare property paths may go through here.
--   2. get_context_value returns ZERO VALUES, not nil, when the expression does
--      not resolve, so tostring() around it throws "value expected". Assigning
--      through a local first collapses that to a plain nil.
--   3. An absent context id reads back as "", which is TRUTHY in Lua, so the
--      empty-string test is load-bearing rather than tidy-up.
--
-- nil when it does not resolve, so the caller falls back to the house crest
-- instead of passing a wrong path - a bad imagepath draws a blank square and
-- logs nothing at all.
function ICUI.portrait_path(cqi)
    if not cqi then return nil end
    local ok, path = pcall(function()
        local v = common.get_context_value("CcoCampaignCharacter",
                                           tostring(cqi), "PortraitPath")
        return v
    end)
    if not ok then return nil end
    if type(path) ~= "string" or path == "" then return nil end
    return path
end

-- A row's crest. The line carries an `icon` field (a house flag path) or nothing;
-- an absent icon HIDES the cell rather than leaving the previous row's crest
-- behind, which is the same stale-cell bug the text columns already had.
-- EVERY resize goes through here.
--
-- CA: "The uicomponent may be need to set to be resizeable before calling this -
-- this can be done with uicomponent:SetCanResizeHeight and
-- uicomponent:SetCanResizeWidth." Two of this file's three Resize call sites had
-- neither: the scrollbar thumb and the standing-bar segments. Both fail SILENTLY
-- - the component keeps its authored size and nothing errors - which is what a
-- uniform-looking standing bar and a full-length scroll thumb look like.
--
-- Found by the harness refusing a Resize that skips the permissions, not by
-- looking at either widget.
function ICUI.resize(c, w, h)
    if not c then return end
    pcall(function()
        c:SetCanResizeWidth(true)
        c:SetCanResizeHeight(true)
        -- FALSE, NOT THE DEFAULT. CA's third argument is "also resize children"
        -- and defaults to true, which scales every child by the same factor on
        -- top of the size layout() is about to give each of them.
        c:Resize(w, h, false)
    end)
end

-- The plate behind a face. Must match plate_path() in tools/gen_ic_ui.py.
--
-- A HOUSE WITH NO PLATE FALLS BACK TO THE VACANT ONE rather than to no call at
-- all: rows are recycled, so a cell left alone keeps whatever house was drawn
-- there on the previous page, and a courtier of no house would inherit the
-- colours of whoever happened to be scrolled past.
function ICUI.plate_path(slug)
    -- `slug or "none"` is WRONG here: "" is truthy in Lua, so an empty house
    -- would build house_plate_.png - a path that resolves to nothing and draws a
    -- blank square, silently.
    if not slug or slug == "" then slug = "none" end
    return "ui/derpy_ic/house_plate_" .. slug .. ".png"
end

-- A fully transparent png, not "no call": rows are recycled, so a cell with no
-- mask has to have the last man's actively taken off it. Must match MASK_NONE in
-- tools/gen_ic_ui.py.
ICUI.MASK_NONE = "ui/derpy_ic/mask_none.png"

-- NOBODY. Drawn by gen_ic_ui.silhouette_pixels at the porthole's own 300x164,
-- with a transparent ground so the house plate behind it keeps the party's
-- colour - a silhouette with a background of its own would paint over the one
-- thing that still distinguishes one leaderless party from another.
--
-- CA SHIPS NOTHING FOR THIS. Its 0_placeholder_mission_issuer.png is a hot-pink
-- "missing image" developer icon and 0_placeholder_agent.png is 29x29.
ICUI.SILHOUETTE = "ui/derpy_ic/portrait_silhouette.png"

-- WHICH PORTRAITS REALLY HAVE A MASK, and nothing else may be guessed at.
--
-- A SetImagePath to a path that resolves to nothing draws a BLANK WHITE SQUARE,
-- silently - over a man's face, in this cell. So the panel never derives a mask
-- path unless the stem is in this set, and this set is not typed by hand: it is
-- generated from the installed packs by gen_ic_ui.py::masked_portraits(), and
-- import_iron_court.py refuses to pack when the two disagree.
--
-- 627 of CA's 1,524 portholes carry a mask and these are the Chaos Dwarf ones.
-- LEGENDARY LORDS HAVE NONE - not Astragoth, Drazhoath, Gorduz or Zhatan - and
-- neither do this mod's own portraits, so those cells stay uncoloured. That is
-- the honest outcome rather than a wrong one.
ICUI.MASKED = {
    ["chd_bull_centaur_taurruk_campaign_01_0"] = true,
    ["chd_bull_centaur_taurruk_campaign_02_0"] = true,
    ["chd_bull_centaur_taurruk_campaign_03_0"] = true,
    ["chd_bull_centaur_taurruk_campaign_04_0"] = true,
    ["chd_bull_centaur_taurruk_campaign_05_0"] = true,
    ["chd_daemonsmith_sorcerer_campaign_01_0"] = true,
    ["chd_daemonsmith_sorcerer_campaign_02_0"] = true,
    ["chd_daemonsmith_sorcerer_campaign_03_0"] = true,
    ["chd_daemonsmith_sorcerer_campaign_04_0"] = true,
    ["chd_daemonsmith_sorcerer_campaign_05_0"] = true,
    ["chd_infernal_castellan_campaign_01_0"] = true,
    ["chd_infernal_castellan_campaign_02_0"] = true,
    ["chd_infernal_castellan_campaign_03_0"] = true,
    ["chd_infernal_castellan_campaign_04_0"] = true,
    ["chd_infernal_castellan_campaign_05_0"] = true,
    ["chd_overseer_campaign_01_0"] = true,
    ["chd_overseer_campaign_02_0"] = true,
    ["chd_overseer_campaign_03_0"] = true,
    ["chd_overseer_campaign_04_0"] = true,
    ["chd_overseer_campaign_05_0"] = true,
    ["chd_sorcerer_prophet_campaign_01_0"] = true,
    ["chd_sorcerer_prophet_campaign_02_0"] = true,
    ["chd_sorcerer_prophet_campaign_03_0"] = true,
    ["chd_sorcerer_prophet_campaign_04_0"] = true,
    ["chd_sorcerer_prophet_campaign_05_0"] = true,
}

-- CA's mask for a portrait, or nil when there is not one.
function ICUI.mask_path(portrait)
    if type(portrait) ~= "string" then return nil end
    local stem = string.match(portrait, "([^/]+)%.png$")
    if not stem or not ICUI.MASKED[stem] then return nil end
    return string.sub(portrait, 1, -5) .. "_mask1.png"
end

-- Sets the plate on a named face cell. It does NOT touch visibility: the plate
-- and the face are two layers of one component, so the face's own setter decides
-- whether the cell is on screen, and a vacant seat hides both together.
--
-- `face` is the portrait path this cell is about to draw, or nil. It is not
-- always a portrait: set_row_icon falls back to the house crest when a character
-- has no porthole, and a crest has no heraldry mask to colour.
--
-- EVERY FAILURE LANDS ON THE TRANSPARENT MASK. Three things have to hold before
-- this cell may name a derived path - the line has a house, that house resolves
-- to a faction, and the portrait is one the build verified has a mask - and the
-- cco call has to survive. If any of that gives way the layer is set back to
-- MASK_NONE, because the alternative is a blank white square on a face.
function ICUI.set_plate(parent, name, slug, face)
    local ic = comp(name, parent)
    if not ic then return end
    pcall(function() ic:SetImagePath(ICUI.plate_path(slug), ICUI.PLATE_INDEX) end)

    -- THE MASK IS THE CROWN'S ALONE. It tints a portrait through
    -- CcoCampaignFaction, which needs a real faction - and a party is not one.
    -- The crown IS your faction, so its men wear your colour; a rival party has
    -- no faction colour to wear and gets the plate behind him instead, which
    -- carries the party colour anyway.
    local key = (slug == IC.CROWN) and ICUI.player() or nil
    local mask = key and ICUI.mask_path(face) or nil
    if mask then
        -- THE IMAGE FIRST, THE CONTEXT LAST. SetContextObject is what fires the
        -- ContextColourSetter, so it runs after the layer is holding the art it
        -- is meant to colour.
        local ok = pcall(function()
            ic:SetImagePath(mask, ICUI.MASK_INDEX)
            ic:SetContextObject(cco("CcoCampaignFaction", key))
        end)
        if ok then return end
    end
    pcall(function() ic:SetImagePath(ICUI.MASK_NONE, ICUI.MASK_INDEX) end)
end

function ICUI.set_row_icon(row, path, kind)
    local ic = comp("ic_row_port", row)
    if not ic then return end
    if path and path ~= "" then
        -- Size the cell to what it is about to draw. CA: "The uicomponent may be
        -- need to set to be resizeable before calling this" - so the two
        -- permissions come first, and they are idempotent.
        local w, h = ICUI.CREST_W, ICUI.CREST_H
        if kind == "porthole" then w, h = ICUI.PORT_W, ICUI.PORT_H end
        ICUI.resize(ic, w, h)
        -- NO THIRD ARGUMENT, and that is the whole point. CA's own words for it:
        -- "Resize the image metric to the size of the image being specified. If
        -- this is not set, the incoming image will take the size of the old."
        -- So resize=true blows the CELL up to the porthole's native size - which
        -- is how a 24px row cell came to draw a face across half the panel. The
        -- default is what fits the image to the cell.
        pcall(function() ic:SetImagePath(path, ICUI.FACE_INDEX) end)
        ic:SetVisible(true)
    else
        ic:SetVisible(false)
    end
end

-- THE CARD'S TEXT USED TO MOVE, and does not any more.
--
-- A vacant office hid its portrait, so reflow_card shuffled the cells beside the
-- face left into the 300x164 gap and back again when the seat was filled. It was
-- a live source of faults in its own right - the 2026-09-14 re-deal moved
-- ic_card_term below the face and left it on the shift list, throwing "Seat is
-- vacant" to x = -84, off the left edge of its own card and across the card
-- beside it - and import_iron_court.py grew a check deriving the shift list from
-- the portrait's y band because of it.
--
-- EVERY SEAT DRAWS A PORTRAIT NOW, a face or ICUI.SILHOUETTE, so there is no gap
-- to close and ICUI.layout's own pass over CARD_CHILD_XY is the only thing that
-- positions a card's children. The check was re-aimed at what replaced the
-- hazard: a recycled card keeping the last holder's colours. See 8b2.

-- Must match ic_card_crest in tools/gen_ic_ui.py.
ICUI.CARD_CREST = 16

-- A TRANSPARENT GROUND, and the mask taken off with it. Rows and cards are
-- both recycled, so a vacant seat has to actively clear what the last holder
-- left on the cell - "no call" leaves his colour behind.
function ICUI.set_vacant_plate(parent, name)
    local ic = comp(name, parent)
    if not ic then return end
    pcall(function()
        ic:SetImagePath(ICUI.MASK_NONE, ICUI.PLATE_INDEX)
        ic:SetImagePath(ICUI.MASK_NONE, ICUI.MASK_INDEX)
    end)
end

-- ---------------------------------------------------------------------------
-- FEEDBACK FOR A CLICK THE PLAYER MADE.
--
-- Appointing and dismissing changed the card and nothing else: no sound, no
-- movement, no confirmation of any kind. The 2026-09-15 session asked for "more
-- player feedback soundfx or visual effect on assigning or kicking", and the
-- reason it is needed is that the card's own change is easy to miss - the seat's
-- name does not move, the effect line does not move, and the one cell that did
-- change is a name in the middle of a ziggurat of fourteen.
--
-- NOT AN EVENT CARD. The feed is for things that happen TO the court; this is
-- the answer to a button the player just pressed, and an event card for your own
-- click is the feed shouting your own decisions back at you.
--
-- THE SOUND NAMES ARE VANILLA'S OWN, lifted from event_feed_message_events'
-- sound_event column rather than invented - they are real Wwise events the game
-- ships. This is the one thing here that cannot be proven offline: sound events
-- live in the .bnk banks, not in any table a check can read, so a name the
-- engine does not know fails as silence. It cannot fail as anything worse.
ICUI.SOUND_OK = "UI_CAM_POPUP_Message_Event_Positive"
ICUI.SOUND_BAD = "UI_CAM_POPUP_Message_Event_Negative"
-- How long the card keeps pulsing. Long enough to catch the eye on a panel the
-- player is already looking at, short enough not to still be going when he
-- clicks the next seat.
ICUI.PULSE_SECONDS = 1.5
ICUI.PULSE_STRENGTH = 5

-- The office card for a seat, by slug. IC.OFFICES' order IS the card order -
-- draw_offices walks the two together - so the index is the whole lookup.
function ICUI.office_card(office_slug)
    local panel = comp(ICUI.PANEL)
    if not panel then return nil end
    for i = 1, #IC.OFFICES do
        if IC.OFFICES[i].slug == office_slug then
            return comp(ICUI.CARD .. "_" .. i, panel)
        end
    end
    return nil
end

-- Confirm a click on `c`. `good` picks the sound; nil `c` still plays it, so a
-- card that has scrolled away does not swallow the confirmation.
function ICUI.confirm(c, good)
    pcall(function()
        common.trigger_soundevent(good and ICUI.SOUND_OK or ICUI.SOUND_BAD)
    end)
    if not c then return end
    -- PROPAGATE FALSE. CA's own warning: the effect stacks through children, and
    -- a card is nine cells deep - propagating would light every one of them
    -- separately and read as a fault rather than as a confirmation.
    pcall(function() pulse_uicomponent(c, true, ICUI.PULSE_STRENGTH, false) end)
    -- AND STOP. A pulse nothing turns off runs until the panel is destroyed, so
    -- every seat the player has ever touched would still be flashing.
    cm:callback(function()
        pcall(function() pulse_uicomponent(c, false, 0, false) end)
    end, ICUI.PULSE_SECONDS)
end

-- The office card's portrait. Same contract as a row's, at index 0 so the frame
-- sitting at index 1 survives the swap.
-- The card's house crest. Same contract as the row's: a path shows it, nothing
-- hides it. A vacant office has no house, so the cell goes dark with the rest.
function ICUI.set_card_crest(card, path)
    local ic = comp("ic_card_crest", card)
    if not ic then return end
    if path and path ~= "" then
        ICUI.resize(ic, ICUI.CARD_CREST, ICUI.CARD_CREST)
        pcall(function() ic:SetImagePath(path, 0) end)
        ic:SetVisible(true)
    else
        ic:SetVisible(false)
    end
end

function ICUI.set_card_icon(card, path)
    ICUI.set_face(card, "ic_card_port", path)
end

-- The house crest cell. Its own function rather than a second branch inside
-- set_row_icon, because the two cells answer different questions: that one draws
-- whatever the row is ABOUT (a face, or a flag on the Court tab), this one draws
-- whose house the man belongs to. A line that supplies no crest hides it, which
-- is what stops the Court tab - where the main icon is already this same flag -
-- from drawing it twice on one row.
function ICUI.set_row_crest(row, path)
    local ic = comp("ic_row_crest", row)
    if not ic then return end
    if path and path ~= "" then
        ICUI.resize(ic, ICUI.CREST_W, ICUI.CREST_H)
        -- No third argument: it fits the flag to the cell. resize=true would
        -- blow the cell up to mon_64.png's native 64px and shove the row about.
        pcall(function() ic:SetImagePath(path, 0) end)
        ic:SetVisible(true)
    else
        ic:SetVisible(false)
    end
end

-- A SIGNED NUMBER, because a breakdown of terms that can go either way is
-- unreadable when the plus signs are missing.
function ICUI.signed(n)
    return string.format("%+d", n or 0)
end

-- WHY A PARTY FEELS THE WAY IT DOES. Rome 2's whole readability is this one
-- tooltip: Bigot -7, Xenophobe -10, Promoted characters +2, Government Type
-- +15, netting to 0 - the player can see exactly which lever to pull. The Iron
-- Court showed "22%, 54 loyalty - RESTLESS" and nothing at all about why, while
-- drift_loyalty computed every term and threw them away.
--
-- RESOLVED HERE, AT DRAW TIME. The model's labels are plain English and its
-- office references are slugs, because IC.loyalty_terms is reachable from a
-- turn handler and a loc call in one of those is a turn-1 CTD that pcall does
-- not catch. This is the only place a name is resolved.
function ICUI.loyalty_tip(faction, court, slug)
    local house = court.houses[slug]
    if not house then return nil end
    local terms = IC.loyalty_terms(faction, slug)
    local net = IC.loyalty_net(terms)
    local out = {string.format("%s\n%d loyalty - %s\nPer turn: %s",
                               ICUI.house_name(slug), house.loyalty or 0,
                               ICUI.mood(house, slug), ICUI.signed(net)), ""}
    local notes = {}
    for i = 1, #terms do
        local label = terms[i].label
        -- The seat the term is ABOUT, where it is about one. A party insulted
        -- over two different offices gets two lines naming two seats.
        if terms[i].key then
            label = string.format("%s (%s)", label, ICUI.office_name(terms[i].key))
        end
        -- A TRAIT SAYS WHOSE IT IS. Two of the three belong to the party
        -- forever and the third to whoever currently speaks for it, and the
        -- difference is the whole point: the leader's is the one a knife can
        -- change.
        if terms[i].leader then
            label = label .. " (their leader)"
        end
        out[#out + 1] = string.format("%s: %s", label, ICUI.signed(terms[i].n))
        if terms[i].note then
            notes[#notes + 1] = string.format("%s - %s", terms[i].label,
                                              terms[i].note)
        end
    end
    -- THE BLURBS LAST, in a block of their own. Interleaved with the numbers
    -- they turn a breakdown into prose, and the numbers are what the player
    -- came for; underneath, they are what the numbers MEAN.
    if #notes > 0 then
        out[#out + 1] = ""
        for i = 1, #notes do out[#out + 1] = notes[i] end
    end
    return table.concat(out, "\n")
end

function ICUI.fill_rows(panel, lines, view)
    view = view or ICUI.view
    local total = #lines
    ICUI.line_count = total
    local at = ICUI.clamp_scroll(view, total)
    -- THE WHOLE POOL IS WALKED, not the window. A row this view does not own -
    -- the ones behind the pie on the court view - still has to be hidden, or it
    -- keeps whatever the last view wrote into it.
    local first = ICUI.first_row(view)
    for i = 1, ICUI.MAX_ROWS do
        local row = comp(ICUI.ROW .. "_" .. i, panel)
        if row then
            local line = i >= first and lines[(i - first + 1) + at] or nil
            if line then
                local over = ICUI.COL_W[view] or {}
                for j = 1, #ICUI.ROW_KEYS do
                    local c = comp(ICUI.ROW_KEYS[j], row)
                    if c then
                        -- SIZE BEFORE TEXT. A cell still carrying the previous
                        -- view's width clips the new view's line, which is the
                        -- bug this exists to stop.
                        local wh = ICUI.COL_WH[j]
                        if wh then
                            ICUI.resize(c, over[j] or wh[1], wh[2])
                        end
                        set_text(c, line[j] or "")
                        -- NO PER-CELL TOOLTIP HERE ANY MORE. This pool carried
                        -- one for the court view's Loyalty column and the court
                        -- view is a grid of cards now: `line.tips` had one
                        -- reader and no writer at all. It is on the card
                        -- instead, where ICUI.fill_party hangs the breakdown on
                        -- ic_party_nums - so the rule is alive and the dead
                        -- twenty lines that no mutant could kill are gone.
                        -- THE LAST TWO CELLS ARE BUTTONS, and a button with no
                        -- label is still a button - a bare plate on the right of
                        -- a row that has nothing to click. Set every pass rather
                        -- than only when empty, because the row pool recycles.
                        if ICUI.ROW_BUTTONS[j] then
                            c:SetVisible((line[j] or "") ~= "")
                        end
                    end
                end
                -- AND THE FIRST CELL CUT TO FIT, last of all.
                --
                -- IT HAS BEEN CLIPPING SINCE THE TRADE WAS APPENDED TO A NAME:
                -- "Amarudz Grimtidesson, Daemonsmith" measures 406px and the
                -- cell was 380, and nothing in the build ever measured it. It
                -- carries a position name in front of that now, and even at 537
                -- the longest thing it can be handed is 670.
                --
                -- WHAT THE CUT MAY EAT IS THE TRADE. Check 20j holds the title
                -- and the NAME to the width, because a picker whose names end
                -- in an ellipsis is one the player cannot choose from.
                --
                -- AFTER THE LOOP, because the loop resizes each cell to this
                -- view's width before writing to it and fit_cut measures
                -- against Dimensions(). Cut inside the loop, it would measure
                -- the width the previous view left behind.
                ICUI.fit_cut(comp("ic_row_a", row), line[1] or "")
                ICUI.set_row_icon(row, line.icon, line.icon_kind)
                -- UNCONDITIONAL. Setting it only when the line names a house
                -- would leave the previous occupant's colours on a recycled row.
                -- THE ICON AS IT IS, crest or face. Testing icon_kind here
                -- first was dead code: a crest path is ui/flags/<faction>/
                -- mon_64.png, whose stem is never in ICUI.MASKED, so mask_path
                -- already refuses it. Two guards for one fact meant neither
                -- could be seen to fail.
                -- AN EMPTY SEAT WEARS NO PLATE AT ALL, and an unaligned MAN
                -- still wears the plain one. Both cells have no house, so the
                -- two cannot be told apart by line.plate - the line says which
                -- it is. plate_path(nil) is house_plate_none, an opaque brown
                -- box: right behind a courtier who belongs to nobody, wrong
                -- behind a silhouette, where it reads as a party with no name.
                if line.vacant then
                    ICUI.set_vacant_plate(row, "ic_row_port")
                else
                    ICUI.set_plate(row, "ic_row_port", line.plate, line.icon)
                end
                ICUI.set_row_crest(row, line.crest)
                row:SetVisible(true)
            else
                row:SetVisible(false)
            end
        end
    end
    ICUI.draw_pager(panel, total, at)
end

-- The pager hides itself when the list fits on one page: two buttons that cannot
-- move anything read as broken rather than unnecessary.
--
-- A SCROLLBAR WAS THE WRONG CONTROL. Its thumb is a drag target, and the only
-- input events CA gives Lua are ComponentLClickUp, ComponentMouseOn and
-- ComponentMouseOff - there is no drag and no wheel - so the thumb could never
-- have been dragged. The buttons need only the click that exists.
function ICUI.pages(total, view)
    local n = ICUI.rows_shown(view or ICUI.live_view())
    if total <= n then return 1 end
    return math.ceil(total / n)
end

function ICUI.draw_pager(panel, total, at)
    local prev = comp("ic_page_prev", panel)
    local nxt = comp("ic_page_next", panel)
    local lbl = comp("ic_page_lbl", panel)
    local view = ICUI.live_view()
    local pages = ICUI.pages(total, view)
    local on = pages > 1
    -- Integer division on the offset: `at` is a ROW offset, and the page it lands
    -- on is what the caption must agree with or the buttons look like they are
    -- lying about where they took you.
    local page = math.floor(at / ICUI.rows_shown(view)) + 1
    if prev then
        prev:SetVisible(on)
        set_text(prev, "Previous")
    end
    if nxt then
        nxt:SetVisible(on)
        set_text(nxt, "Next")
    end
    if lbl then
        lbl:SetVisible(on)
        set_text(lbl, string.format("Page %d of %d", page, pages))
    end
end

-- WHICH VIEW IS ON SCREEN. The picker is modal and owns the list whichever tab is
-- lit behind it, so "the current view" is not ICUI.view while it is up.
--
-- This existed twice, as two locals: refresh() applied the pick override and
-- scroll_by did not. The draw therefore read ICUI.scroll.pick while the arrows
-- wrote ICUI.scroll.offices, and the scrollbar was inert in the one list long
-- enough to need it. One function, both callers.
function ICUI.live_view()
    -- THE HOUSE ROSTER IS A CHARACTER LIST, so it takes "pick" - the same
    -- headers, the same column widths and the same scroll offset. It is the one
    -- picker that chooses nothing; that is a property of its rows, not of its
    -- shape.
    if ICUI.pick then return "pick" end
    return ICUI.view
end

-- Move this view's window. Returns true if anything actually moved, so a click at
-- the end of the list is not reported as a redraw.
function ICUI.scroll_by(delta)
    local view = ICUI.live_view()
    local before = ICUI.scroll[view] or 0
    -- THE PAGE, not the pool. These were the same number for every view that
    -- windows the row pool from its top, and they stopped being the same when
    -- the court became a grid of ten: clamping a ten-card page against a
    -- twelve-row pool leaves the last two parties unreachable.
    local max = ICUI.max_scroll(ICUI.line_count, ICUI.rows_shown(view))
    local at = before + delta
    if at > max then at = max end
    if at < 0 then at = 0 end
    ICUI.scroll[view] = at
    return at ~= before
end

-- A segment's own identity. Returns nothing; everything it does is to the two
-- components it is handed.
--
-- WIDTH IS THE CONSTRAINT. Segment width is the house's standing, so a minor
-- house gets a sliver: the crest needs room for itself plus a margin, and the
-- percentage needs room beside the crest. Below each threshold that element is
-- hidden rather than drawn over its neighbour - the colour still carries the
-- share, and the tooltip still names the house.
-- A CREST NEEDS A WEDGE TO SIT IN THE MIDDLE OF, and below that it would cover
-- its neighbours on both sides - so the smallest parties are named by the list
-- below the pie and not on it. Derived off the crest ring by ICUI.min_slices
-- for the reason given there: the number that is right for one radius is wrong
-- for the next one, silently.
ICUI.CREST_MIN_SLICES = ICUI.min_slices(ICUI.CREST_R, ICUI.CREST_PX)

-- THE CREST IS THE ONLY THING ON THE PIE A PLAYER CAN HOVER. A cell is one
-- rectangle of one strip and belongs to a party only for as long as this draw
-- lasts, so the tooltip that used to live on a segment lives here.
function ICUI.label_crest(crest, slot, faction, court, px, py)
    if not crest then return end
    local slug = slot.slug
    local house = court.houses[slug]
    local path = slug and ICUI.crest(slug) or nil
    if not path or path == "" or slot.n < ICUI.CREST_MIN_SLICES then
        crest:SetVisible(false)
        return
    end
    -- THE MIDDLE OF ITS OWN WEDGE, as a fraction of the sweep rather than as a
    -- slice: from + n/2 is the half-way angle whether the run is odd or even.
    local x, y = ICUI.arc_xy(ICUI.CREST_R,
                             (slot.from + slot.n / 2) / ICUI.DIAL_SLICES,
                             ICUI.CREST_PX)
    pcall(function() crest:SetImagePath(path, 0) end)
    crest:MoveTo(px + x, py + y)
    crest:SetVisible(true)

    -- THE THIRD ARGUMENT IS "set all states". Without it the tooltip is written
    -- to whichever state the component happens to be in, and disappears on the
    -- hover that was meant to show it - the same shape as SetText vs
    -- SetStateText, which cost this panel twice already.
    if house then
        local name = ICUI.house_name(slug)
        local share = IC.share(faction, slug)
        pcall(function()
            crest:SetTooltipText(string.format("%s\n%d%% influence, %d loyalty - %s",
                                               name, math.floor(share + 0.5),
                                               house.loyalty or 0,
                                               ICUI.mood(house, slug)),
                                 "", true)
        end)
    end
end

-- THE PARTY'S SHARE, IN FIGURES, under its crest. Placed by the same ray as
-- the crest so the two read as one mark, and hidden on the same terms: a run
-- with no arc to write in would draw its number over its neighbour's.
function ICUI.label_share(cell, slot, faction, court, px, py)
    if not cell then return end
    local slug = slot.slug
    if not slug or slot.n < ICUI.SHARE_MIN_SLICES then
        cell:SetVisible(false)
        return
    end
    local x, y = ICUI.arc_box(ICUI.SHARE_R,
                              (slot.from + slot.n / 2) / ICUI.DIAL_SLICES,
                              ICUI.SHARE_W, ICUI.SHARE_H)
    -- THE SHARE THE MODEL HOLDS, not the slice count. The sweep is rounded to
    -- three-degree slices and a 2% party still gets one, so counting slices
    -- back into a percentage would print a number the court does not have.
    set_text(cell, string.format("%d%%",
                                 math.floor(IC.share(faction, slug) + 0.5)))
    cell:MoveTo(px + x, py + y)
    cell:SetVisible(true)
end

-- WHAT THE BAND IS CALLED, and what it is doing to you. Both are loc rows the
-- generator writes from the same table it builds the bundles from, so the
-- panel cannot name a band the faction is not actually wearing.
function ICUI.band_name(slug)
    return loc("derpy_ic_control_name_" .. slug, slug)
end

function ICUI.band_effects(slug)
    return loc("derpy_ic_effects_derpy_ic_control_" .. slug, "")
end

-- HOW WIDE A CELL REALLY IS. Dimensions and NOT Bounds: Bounds is the component
-- plus its children, and a text cell has none - but the rule is the rule, and
-- the one pass that used the wrong one put three widgets in the wrong place.
function ICUI.cell_w(c)
    if not c then return 0 end
    local w = 0
    pcall(function() w = c:Dimensions() end)
    return w or 0
end

-- ONE STRING ACROSS TWO CELLS, measured by the engine rather than counted.
--
-- twui text NEVER WRAPS. texthbehaviour has exactly three values in ui3.pack -
-- "Never split", "Resize" and "Slip by character" - none of them wraps, and
-- textvbehaviour does not exist at all, so a string too long for its cell is
-- silently cut mid-word. More lines means more components, which is why there
-- are two cells here.
--
-- AND THE SPLIT IS MEASURED, not counted. A character budget is the guess that
-- put "Shaken: Gemsto..." on a player's screen, and this cell's content is
-- unbounded in a way the rolled names are not: the Crown and every confederated
-- party wear a FACTION's display name, which is the game's loc and not ours.
-- TextDimensionsForText is the engine's own metric and the only honest answer.
--
-- WORDS, NEVER CHARACTERS: a word cut in half is worse than a short line. The
-- first word stays on line one whatever it measures, because there is nowhere
-- else for it to go - and check 20g in tools/gen_ic_ui.py refuses the build if
-- the model can roll a word too wide for the cell.
function ICUI.fit_two(c1, c2, text)
    text = tostring(text or "")
    if not c1 then return end
    local words = {}
    for word in string.gmatch(text, "%S+") do words[#words + 1] = word end
    if not c2 or #words <= 1 then
        set_text(c1, text)
        if c2 then set_text(c2, "") end
        return
    end
    local w1 = ICUI.cell_w(c1)
    local split = #words + 1
    -- A CELL THE ENGINE HAS NOT LAID OUT YET MEASURES ZERO, and a zero-width
    -- test would send every word after the first to line two and leave the card
    -- reading "The" over "Covenant of the Ninth Stair".
    if w1 > 0 then
        for i = 2, #words do
            local got = nil
            pcall(function()
                got = c1:TextDimensionsForText(table.concat(words, " ", 1, i))
            end)
            if got and got > w1 then
                split = i
                break
            end
        end
    end
    set_text(c1, table.concat(words, " ", 1, split - 1))
    set_text(c2, (split > #words) and "" or table.concat(words, " ", split))
end

-- ONE CELL, CUT RATHER THAN SPILLED. The third of the family, and the only one
-- that loses text on purpose.
--
-- It exists for ICUI.CUT_CELLS - cells whose content is a CHARACTER's name and
-- which have a picture of him beside them, so the cell is 281px and there is no
-- second line to spill onto: the party card is packed to its own floor and the
-- three rows beside the face are the height of the face. The longest name the
-- model can roll measures 331px at the panel's content size, and the choice put
-- to the author on 2026-09-14 was between cutting it, shrinking that one cell
-- to 14, and a fit with zero pixels to spare. Cutting won, so the panel keeps
-- one content size and a very long name ends in a full stop the reader can see.
--
-- MEASURED, AND BY WORDS. Same metric and same rule as fit_two: a character
-- budget is a guess and a word cut in half is worse than a short line. The
-- first word always stays, because there is nowhere else for it to go.
--
-- THE ELLIPSIS IS MEASURED TOO. It is appended before the test, not after, or
-- the three dots are exactly what overruns the cell.
function ICUI.fit_cut(c, text)
    text = tostring(text or "")
    if not c then return end
    local w = ICUI.cell_w(c)
    local function fits(s)
        local got = nil
        pcall(function() got = c:TextDimensionsForText(s) end)
        return not got or got <= w
    end
    -- A CELL THE ENGINE HAS NOT LAID OUT YET MEASURES ZERO. Same guard as
    -- fit_two's: a zero-width test would cut every name to its first word.
    if w <= 0 or fits(text) then
        set_text(c, text)
        return
    end
    local words = {}
    for word in string.gmatch(text, "%S+") do words[#words + 1] = word end
    local kept = 0
    for i = 1, #words do
        if not fits(table.concat(words, " ", 1, i) .. "...") then break end
        kept = i
    end
    if kept > 0 then
        set_text(c, table.concat(words, " ", 1, kept) .. "...")
        return
    end
    -- CHARACTERS, BUT ONLY WHEN A WHOLE WORD WILL NOT GO. This is where
    -- fit_cut parts company with fit_two, and it has to: fit_two keeps a first
    -- word too wide for line one because there is a line two behind it, and
    -- this cell has nothing behind it. Keeping the word here would put the
    -- overrun back - the exact thing the cut exists to prevent - and 20g would
    -- be exempting a cell that still clips.
    --
    -- AT LEAST ONE CHARACTER, whatever the cell measures. A cell too narrow for
    -- "X..." is a layout fault to see rather than an empty cell to wonder at.
    local n = 1
    for i = 1, string.len(text) do
        if not fits(string.sub(text, 1, i) .. "...") then break end
        n = i
    end
    set_text(c, string.sub(text, 1, n) .. "...")
end

-- THE SAME SPLIT ACROSS ANY NUMBER OF CELLS. fit_two is this with n = 2 and is
-- left alone: it is called on a party name in three places and its two-cell shape
-- is pinned by checks of its own.
--
-- THE LAST CELL TAKES WHAT IS LEFT whether it fits or not. Running out of lines
-- is a layout fault to see, not one to hide - the alternative is dropping the end
-- of a sentence silently, which is what a clipped single cell already did.
function ICUI.fit_lines(cells, text)
    text = tostring(text or "")
    local words = {}
    for word in string.gmatch(text, "%S+") do words[#words + 1] = word end
    local at = 1
    for i = 1, #cells do
        local c = cells[i]
        if not c then break end
        if at > #words then
            set_text(c, "")
        elseif i == #cells then
            set_text(c, table.concat(words, " ", at))
            at = #words + 1
        else
            local w = ICUI.cell_w(c)
            local last = at
            -- A CELL THE ENGINE HAS NOT LAID OUT YET MEASURES ZERO, and a
            -- zero-width test would put one word on every line. Same guard as
            -- fit_two's, and the same reason.
            if w > 0 then
                for k = at, #words do
                    local got = nil
                    pcall(function()
                        got = c:TextDimensionsForText(
                            table.concat(words, " ", at, k))
                    end)
                    if got and got > w then break end
                    last = k
                end
            else
                last = #words
            end
            set_text(c, table.concat(words, " ", at, last))
            at = last + 1
        end
    end
end

-- A FACE CELL BY NAME, which is what set_card_icon was for one cell. Three cells
-- draw a portrait now - the office card's, the party card's and the Crown's -
-- and three copies of the same four lines is three places for the index to
-- drift from ICUI.FACE_INDEX.
function ICUI.set_face(parent, name, path)
    local ic = comp(name, parent)
    if not ic then return end
    if path and path ~= "" then
        -- NO THIRD ARGUMENT. CA: "Resize the image metric to the size of the
        -- image being specified. If this is not set, the incoming image will
        -- take the size of the old." resize=true blows the CELL up to the
        -- porthole's native 300x164.
        pcall(function() ic:SetImagePath(path, ICUI.FACE_INDEX) end)
        ic:SetVisible(true)
    else
        ic:SetVisible(false)
    end
end

-- A CREST CELL BY NAME, the same way, and square: mon_64.png is 64x64 and a
-- flag drawn into a non-square cell is a stretched flag.
function ICUI.set_crest(parent, name, path, px)
    local ic = comp(name, parent)
    if not ic then return end
    if path and path ~= "" then
        ICUI.resize(ic, px, px)
        pcall(function() ic:SetImagePath(path, 0) end)
        ic:SetVisible(true)
    else
        ic:SetVisible(false)
    end
end

-- Must match ic_party_crest in tools/gen_ic_ui.py.
ICUI.PARTY_CREST = 24

-- THE CROWN, WITH A FACE ON IT.
--
-- The FACTION LEADER and not IC.party_leader(crown): the Crown is a party and
-- party_leader answers for it by standing like any other, but the man at the top
-- of a panel called Hashut's Court is the one who actually rules. They are
-- usually the same man and they do not have to be.
--
-- HIS TRAIT IS THE CROWN'S LEADER TRAIT, which is the party's and therefore
-- already in the loyalty breakdown - so this is not a new number, it is the
-- existing one given the face it belongs to.
function ICUI.draw_leader(panel, faction, court)
    set_text(comp("ic_leader_lbl", panel), "The Crown")
    -- THE SAME CALL THE CROWN'S CARD MAKES, and that is the point of it. This
    -- read IC.faction_leader_cqi while the card read IC.party_leader, so the two
    -- named different men for the same party on the same screen - and the trait
    -- drawn under the name here came through IC.leader_trait, which has always
    -- gone to party_leader, so the block was already showing one man's name over
    -- another man's trait. One source, and they cannot disagree.
    local cqi = IC.party_leader(faction, IC.CROWN)
    local man = cqi and IC.character_by_cqi(faction, cqi) or nil
    local face = cqi and ICUI.portrait_path(cqi) or nil
    -- THE PLATE FIRST, THEN THE FACE. set_plate writes the house colour behind
    -- the portrait and the heraldry mask over it; the face itself is a third
    -- layer and set_face is what puts it there.
    ICUI.set_plate(panel, "ic_leader_port", IC.CROWN, face)
    -- THE SAME RULE FOR THE CROWN. Without a fallback set_face hides the cell
    -- outright and leaves the bare house plate, which reads as art that failed
    -- to load rather than as a man whose portrait the game has not got.
    ICUI.set_face(panel, "ic_leader_port", face or ICUI.SILHOUETTE)
    set_text(comp("ic_leader_name", panel),
             man and ICUI.character_name(man) or "The throne stands empty")
    set_text(comp("ic_leader_party", panel), ICUI.house_name(IC.CROWN, faction))
    -- HIS TRAIT AND THE PARTY'S TWO, beside the portrait, drawn exactly as
    -- the party card draws them - icon, name, and the tooltip with what each
    -- is worth this turn - because the Crown's card in the grid shows the same
    -- three and the two must not read differently.
    local lead = IC.leader_trait(faction, IC.CROWN)
    local traits = IC.party_traits(faction, IC.CROWN)
    local trait_n = ICUI.trait_values(faction, IC.CROWN)
    for _, row in ipairs({{"ic_leader_trait", lead}, {"ic_leader_t1", traits[1]},
                          {"ic_leader_t2", traits[2]}}) do
        local c, trait = comp(row[1], panel), row[2]
        set_text(c, ICUI.trait_line(trait and trait.name))
        if c then
            pcall(function()
                c:SetTooltipText(
                    trait and ICUI.trait_tip(trait, trait_n[trait.key]) or "",
                    "", true)
                c:SetInteractive(trait ~= nil)
            end)
        end
    end
    for _, name in ipairs(ICUI.LEADER_KEYS) do
        local c = comp(name, panel)
        if c and name ~= "ic_leader_port" then c:SetVisible(true) end
    end
end

-- ONE PARTY'S CARD. Everything the court row carried, plus the three things a
-- row had no cell for: who leads them, what he is, and what they are.
function ICUI.fill_party(card, faction, court, slug)
    local house = court.houses[slug]
    if not house then return end
    ICUI.set_crest(card, "ic_party_crest", ICUI.crest(slug), ICUI.PARTY_CREST)
    ICUI.fit_two(comp("ic_party_name", card), comp("ic_party_name2", card),
                 ICUI.house_name(slug, faction))

    -- WHO SPEAKS FOR THEM, and his face. A party whose every member is dead or
    -- gone has none, and that is a sentence rather than an empty cell: the card
    -- is the same size either way and a blank half of it reads as a bug.
    local cqi = IC.party_leader(faction, slug)
    local man = cqi and IC.character_by_cqi(faction, cqi) or nil
    local face = cqi and ICUI.portrait_path(cqi) or nil
    ICUI.set_plate(card, "ic_party_port", slug, face)
    -- A SILHOUETTE WHEN THERE IS NO FACE, and NOT the crest. The crest is the
    -- ROW's fallback and right there - a row has one picture, and a flag beats
    -- a blank. This card already draws that crest in its own top-left corner
    -- beside the name, so falling back to it put the same picture on the card
    -- twice and called one of them a face.
    ICUI.set_face(card, "ic_party_port", face or ICUI.SILHOUETTE)
    ICUI.fit_cut(comp("ic_party_leader", card),
                 man and ICUI.character_name(man) or "No one speaks for them")

    -- HIS TRAIT, BESIDE HIM. Derived from his cqi and never stored, so killing
    -- him rerolls it - which is the whole reason it is drawn under his name
    -- instead of with the party's two.
    local lead = IC.leader_trait(faction, slug)
    -- ONE WALK FOR ALL THREE CELLS, and it has to happen before the first of
    -- them is written.
    local trait_n = ICUI.trait_values(faction, slug)
    local lt = comp("ic_party_ltrait", card)
    set_text(lt, ICUI.trait_line(lead and lead.name))
    if lt then
        pcall(function()
            lt:SetTooltipText(
                lead and ICUI.trait_tip(lead, trait_n[lead.key]) or "",
                "", true)
            lt:SetInteractive(lead ~= nil)
        end)
    end

    -- THE TWO NUMBERS THE ROW USED TO CARRY, and the breakdown that explains the
    -- second of them. The tooltip moved off the Loyalty cell with the cell.
    local nums = comp("ic_party_nums", card)
    set_text(nums, string.format("%d%% of the court - %d loyalty",
                                 math.floor(IC.share(faction, slug) + 0.5),
                                 house.loyalty or 0))
    if nums then
        pcall(function()
            nums:SetTooltipText(ICUI.loyalty_tip(faction, court, slug), "", true)
            nums:SetInteractive(true)
        end)
    end

    -- THE PARTY'S OWN TWO. Written to both cells every draw, because the card
    -- pool recycles and a party with one trait would otherwise inherit the
    -- second of whoever was drawn in this slot before it.
    local traits = IC.party_traits(faction, slug)
    for i, name in ipairs({"ic_party_t1", "ic_party_t2"}) do
        local c = comp(name, card)
        local trait = traits[i]
        set_text(c, ICUI.trait_line(trait and trait.name))
        if c then
            pcall(function()
                c:SetTooltipText(
                    trait and ICUI.trait_tip(trait, trait_n[trait.key]) or "",
                    "", true)
                c:SetInteractive(trait ~= nil)
            end)
        end
    end

    -- THE MOOD, AS A WORD AND NOTHING ELSE. It was the label on the card's one
    -- button; the author asked for the reading and the control to be apart, so
    -- this cell only reads and the card itself is the control. RED when the
    -- word is a threat, which is the one thing the plate used to say by
    -- colour that a bare word does not.
    local word = ICUI.card_mood(faction, house, slug)
    local state = comp("ic_party_state", card)
    set_text(state, ICUI.MOOD_RED[string.match(word, "^%a+")] and ICUI.red(word)
                    or word)
    if state then
        pcall(function()
            -- The tooltip carries the party's agenda first, if it has one, then
            -- what the countdown is protecting.
            local agenda = ICUI.agenda_tip(faction, slug)
            local tip = ICUI.secession_tip(faction, court, slug)
            state:SetTooltipText(agenda ~= "" and (agenda .. "\n\n" .. tip) or tip,
                                 "", true)
            state:SetInteractive(true)
        end)
    end

    -- WHICH WAY IT IS GOING, and the breakdown that says why - the same one the
    -- figure above carries, because it is the same sum.
    local net = IC.loyalty_net(IC.loyalty_terms(faction, slug))
    local trend = comp("ic_party_trend", card)
    set_text(trend, net == 0 and "Loyalty steady"
                    or string.format("Loyalty %s a turn", ICUI.signed(net)))
    if trend then
        pcall(function()
            trend:SetTooltipText(ICUI.loyalty_tip(faction, court, slug), "", true)
            trend:SetInteractive(true)
        end)
    end

    -- THE THREE COUNTS, each naming what it counts in its tooltip. Members are
    -- every character of the faction the model files under this party -
    -- IC.party_lords' second answer, the number a rising takes with it.
    local _lords, members = IC.party_lords(faction, slug)
    local offices = IC.offices_of_house(faction, slug)
    local govs = IC.provinces_of_house(faction, slug)
    local function count(n, one, many, none)
        if n == 0 then return none end
        return string.format("%d %s", n, n == 1 and one or many)
    end
    local seats = {}
    for i = 1, #offices do seats[i] = ICUI.office_name(offices[i]) end
    local lands = {}
    for i = 1, #govs do
        lands[i] = loc("provinces_onscreen_" .. govs[i], govs[i])
    end
    ICUI.set_count(card, "ic_party_members",
        count(members or 0, "member", "members", "No members"),
        "The lords and heroes of your faction who belong to this party.")
    ICUI.set_count(card, "ic_party_offices",
        count(#offices, "office", "offices", "No office"),
        #seats > 0 and ("Seats they hold: " .. table.concat(seats, ", ") .. ".")
        or "They hold no seat at court.")
    ICUI.set_count(card, "ic_party_govs",
        count(#govs, "overseer", "overseers", "No overseer"),
        #lands > 0 and ("Provinces their men oversee: "
                        .. table.concat(lands, ", ") .. ".")
        or "None of their men oversees a province.")

    -- AND THE FRAME, on the chosen card only. Written to every card on every
    -- draw, because the pool recycles and a frame left on a slot would follow
    -- the slot to whichever party the next page put in it.
    pcall(function()
        card:SetImagePath(ICUI.sel == slug and ICUI.PARTY_SELECTED
                          or ICUI.MASK_NONE, ICUI.PARTY_SEL_INDEX)
    end)
end

-- THE WORDS A PLAYER HAS TO ACT ON, which the card draws red. Keyed by the
-- word's first run of letters, because SECEDES and SPLITS carry a count.
ICUI.MOOD_RED = {SECEDES = true, SPLITS = true, SPLINTERING = true,
                 PLOTTING = true, SCHEMING = true}

-- ONE COUNT CELL: the figure, and what it counts on hover.
function ICUI.set_count(card, name, text, tip)
    local c = comp(name, card)
    set_text(c, text)
    if c then
        pcall(function()
            c:SetTooltipText(tip, "", true)
            c:SetInteractive(true)
        end)
    end
end

-- HOW MANY OF THE NAMES TO PRINT before falling back to a count. Six fills
-- about three lines at the tooltip's width; a court can lose more than that in
-- one secession and naming all of them is a wall of text nobody reads.
ICUI.TIP_PROVINCES = 6

-- WHAT WALKING OUT WOULD ACTUALLY COST, asked before it happens.
--
-- The province NAMES come from provinces_onscreen_<key>, not from
-- region:province_name(), which CA documents as returning a KEY - the same trap
-- the governors tab already carries a comment about. Resolved here, at draw
-- time, and never from a turn handler.
function ICUI.secession_tip(faction, court, slug)
    if slug == IC.CROWN then
        -- YOUR OWN HOUSE TAKES NO LAND. IC.splinter moves weight and men and
        -- never touches a province, so a province count here would be a threat
        -- the model does not make.
        return string.format(
            "Your own house does not secede. If its loyalty runs out, a piece "
            .. "of it breaks away as a party of its own and takes %d%% of the "
            .. "court off your share.", IC.TUNE.splinter_weight)
    end
    local doomed = IC.defecting_provinces(faction, slug) or {}
    local seats = IC.seats(faction) or {}
    if #doomed == 0 then
        return "If this party walks out it takes no province with it."
    end
    local names = {}
    for i = 1, math.min(#doomed, ICUI.TIP_PROVINCES) do
        names[i] = loc("provinces_onscreen_" .. doomed[i], doomed[i])
    end
    local more = ""
    if #doomed > ICUI.TIP_PROVINCES then
        more = string.format(" and %d more", #doomed - ICUI.TIP_PROVINCES)
    end
    -- IN THE ORDER THEY WOULD ACTUALLY BE TAKEN. defecting_provinces sorts its
    -- answer - what the party governs, then what has soured, then worst-first -
    -- so the first names printed are the ones most certainly gone, and the cap
    -- drops the least certain rather than an arbitrary slice.
    return string.format(
        "If this party walks out it takes %d of your %d provinces: %s%s.",
        #doomed, #seats, table.concat(names, ", "), more)
end

-- THE PARTY ACTION BAR (author, 2026-09-24): choose a party on its card, then
-- act on it here. Provoke and Purge were two of the Intrigue tab's moves and
-- Secure Loyalty and Send a Gift the favour list's two; all four answer the
-- question "what do I do about THIS party", so they sit under the cards that
-- ask it. Send a Gift came back on 2026-09-25 - the list went and left it with
-- no button at all.
--
-- THE LABELS AND HINTS ARE MEASURED BY tools/gen_ic_ui.py (check 20g2), which
-- reads them out of these two tables - keep them one string per line.
ICUI.ACT_KEYS = {"ic_act_provoke", "ic_act_gift", "ic_act_secure", "ic_act_purge"}
ICUI.ACT_LABEL = {
    ic_act_provoke = "Provoke",
    ic_act_gift = "Send a Gift",
    ic_act_secure = "Secure Loyalty",
    ic_act_purge = "Purge",
}
ICUI.ACT_HINT = {
    "Click a party to act on it.",
    "Your house: click again for its men.",
}
-- WHAT EACH BUTTON DOES. The two plots are aimed at the man who speaks for the
-- party - the one its card shows - and securing loyalty is a favour, paid for
-- out of the treasury rather than out of a courtier's influence.
ICUI.ACT_MOVE = {
    ic_act_provoke = {plot = "provoke"},
    ic_act_gift = {favour = "gift"},
    ic_act_secure = {favour = "secure"},
    ic_act_purge = {plot = "purge"},
}

-- CAN THIS BUTTON ACT ON THAT PARTY? Asked of the model, never re-derived, and
-- asked about the PARTY only: who carries a plot out is the picker's question,
-- which it answers per man exactly as it always has. Returns may, a sentence
-- when it may not, and the plot's target cqi.
function ICUI.act_check(faction, key, slug)
    local move = ICUI.ACT_MOVE[key]
    local name = ICUI.house_name(slug, faction)
    if move.favour then
        local may, why, spare = IC.can_favour(faction, move.favour, slug)
        if may then return true end
        -- THE FLOOR OUTRANKS THE OATH. The model asks "already sworn?" first,
        -- and at zero loyalty "sworn for another 3 turns" is the promise the
        -- turn will not keep - so the refusal names the floor instead.
        if why == "sworn" and IC.at_breaking_point(faction, slug) then
            why, spare = "breaking", nil
        end
        return false, ICUI.reason_text(why, spare)
    end
    local target = IC.party_leader(faction, slug)
    if not target then
        return false, string.format("No one speaks for %s, so there is no one "
                                    .. "to aim it at.", name)
    end
    local may, why = IC.may_target(faction, move.plot, target)
    if not may then return false, ICUI.reason_text(why) end
    return true, nil, target
end

-- WHAT IS ALREADY TRUE OF THE OATH, before what can be bought. It was the
-- favour list's first line; the list is gone and Secure Loyalty's tooltip is
-- where a player now goes when a party is about to leave, so it says it here.
--
-- THE FLOOR FIRST, because it outranks the oath in the model and a line that
-- said otherwise would sell a guarantee the turn does not honour.
-- IC.at_breaking_point, not a loyalty test written again: the countdown reads
-- that function and this has to read the same one. Nil when nothing is true
-- yet.
function ICUI.oath_status(faction, slug)
    local name = ICUI.house_name(slug)
    if IC.at_breaking_point(faction, slug) then
        return string.format("%s has nothing left to lose. They break with you on "
            .. "the next turn, and no oath will hold them - only their loyalty will.",
            name)
    end
    local sworn = IC.protected_for(faction, slug)
    if sworn > 0 then
        return string.format("%s is sworn on the anvil: they cannot break with you "
            .. "for another %d turn%s.", name, sworn, sworn == 1 and "" or "s")
    end
    local house = IC.court(faction).houses[slug]
    if house and (house.clock or 0) > 0 then
        return string.format("%s breaks with you in %d turn%s unless placated.",
            name, house.clock, house.clock == 1 and "" or "s")
    end
    return nil
end

-- WHAT THE BUTTON WILL DO, on hover: the move's own effect line and price out
-- of the model's tables, and the refusal under them when there is one.
function ICUI.act_tip(faction, key, slug)
    local move = ICUI.ACT_MOVE[key]
    local name = ICUI.house_name(slug, faction)
    local lines = {}
    if move.favour then
        local favour = IC.favour_by_key(move.favour)
        lines[1] = string.format("%s: %s - %s gold", favour.name, name,
                                 IC.favour_cost(move.favour))
        lines[2] = favour.blurb
        if move.favour == "gift" then
            -- WHAT IT BUYS, off the model's own number, and their loyalty
            -- now, so the player can see how far +2 goes before paying for it.
            local house = IC.court(faction).houses[slug]
            lines[#lines + 1] = string.format("+%d loyalty (now %d).",
                IC.TUNE.favour_gift_loyalty, house and house.loyalty or 0)
        else
            -- THE PROMISE ONLY WHERE IT HOLDS. At the floor no oath keeps a
            -- party, and a party already sworn is not sworn twice, so in both
            -- cases the line says what is TRUE instead - see oath_status.
            local status = ICUI.oath_status(faction, slug)
            if not IC.at_breaking_point(faction, slug)
                    and IC.protected_for(faction, slug) == 0 then
                lines[#lines + 1] = string.format("They cannot break with you for "
                    .. "%d turns, and any countdown stops.", IC.TUNE.favour_secure_turns)
            end
            if status then lines[#lines + 1] = status end
        end
    else
        local plot = IC.plot_by_key(move.plot)
        local leader = IC.party_leader(faction, slug)
        local man = leader and IC.character_by_cqi(faction, leader) or nil
        lines[1] = string.format("%s: %s", plot.name, name)
        lines[2] = plot.effect
        lines[3] = string.format("The man you send spends %d influence. "
            .. "Aimed at %s, who speaks for them.", IC.plot_cost(move.plot),
            man and ICUI.character_name(man) or "their leader")
    end
    local may, why = ICUI.act_check(faction, key, slug)
    if not may then lines[#lines + 1] = "\n" .. ICUI.red(why) end
    return table.concat(lines, "\n")
end

-- THE BAR ITSELF. Three buttons for a chosen rival; one line of help for no
-- choice or for your own house, which none of the three can touch. A refused
-- action is drawn red and still answers a click - with the reason - because a
-- button that does nothing and says nothing is the fault this panel has
-- removed four times.
function ICUI.draw_actions(panel, faction, court, px, py)
    local slug = ICUI.sel
    -- A BOOLEAN, NEVER NIL. `slug and ...` is nil when nothing is chosen, and
    -- c:SetVisible(nil) broke the game's string library on the spot - every
    -- component lookup after it failed, CA's own included, and the panel could
    -- not be closed (proven live 2026-09-25). `slug ~= nil` starts the chain
    -- with a boolean, so every value it can produce is one.
    local rival = slug ~= nil and slug ~= IC.CROWN and court.houses[slug] ~= nil
    -- CENTRED UNDER THE GRID, or beside the pager while it shows. Read off the
    -- pager itself, which draw_pager has just set, so the two cannot disagree.
    local nxt = comp("ic_page_next", panel)
    local paged = nxt ~= nil and nxt:Visible()
    local keys = {"ic_act_hint"}
    for _, key in ipairs(ICUI.ACT_KEYS) do keys[#keys + 1] = key end
    for _, key in ipairs(keys) do
        local c = comp(key, panel)
        local home = paged and ICUI.ACT_PAGED_XY[key] or ICUI.PANEL_XY[key]
        if c and home then
            c:MoveTo(px + home[1], py + home[2])
            ICUI.resize(c, home[3], home[4])
        end
    end
    for _, key in ipairs(ICUI.ACT_KEYS) do
        local c = comp(key, panel)
        if c then
            if rival then
                local may = ICUI.act_check(faction, key, slug)
                set_text(c, may and ICUI.ACT_LABEL[key] or ICUI.red(ICUI.ACT_LABEL[key]))
                pcall(function()
                    c:SetTooltipText(ICUI.act_tip(faction, key, slug), "", true)
                end)
            end
            c:SetVisible(rival)
        end
    end
    local hint = comp("ic_act_hint", panel)
    set_text(hint, slug == IC.CROWN and ICUI.ACT_HINT[2] or ICUI.ACT_HINT[1])
    if hint then hint:SetVisible(not rival) end
end

function ICUI.draw_court(panel, faction, court, px, py)
    local slugs = ICUI.court_slugs(faction)
    local slots = ICUI.dial_slots(faction, court)
    -- A CHOICE THAT OUTLIVED ITS PARTY IS DROPPED before a card is drawn: a
    -- purge that landed leaves the slug pointing at nobody, and the bar would
    -- offer three moves against a party that is gone.
    if ICUI.sel and not court.houses[ICUI.sel] then ICUI.sel = nil end

    -- THE WHOLE PIE: one picture per slice, and the only thing a draw decides
    -- is which. Every wedge is the same size at the same place, so there is
    -- nothing to move and nothing to resize - MoveTo is here because layout()
    -- runs when the panel is built and this is what keeps the pie with the
    -- panel if it is ever rebuilt somewhere else.
    --
    -- THE WEDGE'S OWN CELL, not DIAL_CX - DIAL_R: the two are scaled apart and
    -- can land a pixel from each other, and layout() sized the wedge by the cell.
    local wx, wy = ICUI.PANEL_XY.ic_wedge_00[1], ICUI.PANEL_XY.ic_wedge_00[2]
    for i = 0, ICUI.DIAL_SLICES - 1 do
        local wedge = comp(string.format("ic_wedge_%02d", i), panel)
        if wedge then
            wedge:MoveTo(px + wx, py + wy)
            pcall(function()
                wedge:SetImagePath(
                    ICUI.wedge_path(i, ICUI.slice_owner(slots, i)), 0)
            end)
            wedge:SetVisible(true)
        end
    end
    -- THE WALLS, one per party after the first. A boundary is where a run
    -- BEGINS, so the party in slot one never draws one - its run begins at
    -- slice zero, which is the baseline's left end and already framed.
    --
    -- A run of no slices has no boundary either: a party too small to be given
    -- a slice would otherwise put a wall exactly where the next party's is.
    for i = 1, ICUI.MAX_HOUSES do
        local wall = comp(string.format("ic_div_%02d", i - 1), panel)
        if wall then
            local slot = slots[i]
            if slot and slot.n > 0 and slot.from > 0 then
                wall:MoveTo(px + wx, py + wy)
                pcall(function()
                    wall:SetImagePath(ICUI.div_path(slot.from), 0)
                end)
                wall:SetVisible(true)
            else
                wall:SetVisible(false)
            end
        end
    end
    for i = 1, ICUI.MAX_HOUSES do
        local crest = comp(string.format("ic_barc_%02d", i - 1), panel)
        if crest then
            if slots[i] then
                ICUI.label_crest(crest, slots[i], faction, court, px, py)
            else
                crest:SetVisible(false)
            end
        end
        local share = comp(string.format("ic_barp_%02d", i - 1), panel)
        if share then
            if slots[i] then
                ICUI.label_share(share, slots[i], faction, court, px, py)
            else
                share:SetVisible(false)
            end
        end
    end

    -- AND WHAT IT ALL MEANS, in words, beside the dial: the band the faction is
    -- actually wearing and the effects that come with it. A player should not
    -- have to open Faction Effects to find out what holding the court is worth.
    --
    -- THE SHARE, THE BAND, THEN ONE EFFECT A LINE. The loc string is the
    -- effects joined with ", " and none of them holds one (gen_ic_ui.py check
    -- 20g), so a gmatch walk gets them back. Every line is written every draw:
    -- a band with fewer effects than the last one would otherwise keep its tail.
    local band = IC.control_band(faction)
    set_text(comp("ic_control", panel),
             string.format("%d%% of the court", IC.control(faction)))
    set_text(comp("ic_control_band", panel), ICUI.band_name(band))
    local fx = {}
    for part in string.gmatch(ICUI.band_effects(band) .. ", ", "(.-), ") do
        if part ~= "" then fx[#fx + 1] = part end
    end
    for i, key in ipairs(ICUI.FX_KEYS) do
        set_text(comp(key, panel), fx[i] or "")
    end

    -- AND THE CROWN, WITH A FACE, in the block the dial leaves beside it.
    set_text(comp("ic_col_left", panel), "Control of the Court")
    set_text(comp("ic_col_right", panel), "Parties of the Court")
    ICUI.draw_leader(panel, faction, court)

    -- WHAT THE CARDS ACTUALLY ARE is recorded further down, once the sort has
    -- been applied - it has to be the list the cards were DRAWN from or a click
    -- acts on a different party. This used to assign `slugs` here; the
    -- assignment moved rather than being duplicated, because two of them is one
    -- that will be forgotten.
    local warn = ""
    for i = 1, #slugs do
        local slug = slugs[i]
        local house = court.houses[slug]
        if (house.clock or 0) > 0 then
            warn = string.format("%s will break with you in %d turns.",
                                 ICUI.house_name(slug), house.clock)
        end
    end
    -- Sufferance outranks a rival's countdown: it is the player's own position,
    -- and it is the one a player cannot read off the bar without doing the sum.
    local own_share = IC.sufferance(faction)
    if own_share then
        warn = string.format(
            "Your own house holds %d%% of the court. Below %d%% you rule on sufferance.",
            math.floor(own_share + 0.5), IC.TUNE.sufferance_share)
    end
    -- ONE CARD PER PARTY, windowed by this view's own page. The grid holds ten
    -- and a court can hold more, so the offset and the pager are the same pair
    -- every other view uses - and the keys recorded for the click are the ones
    -- THIS draw used, offset included, or a paged grid acts on the wrong party.
    -- HOW LONG THE LIST IS, which fill_rows used to record and the court no
    -- longer calls. Without it scroll_by clamps against a line_count left over
    -- from whichever tab the player was on last - zero, on a fresh panel - and
    -- the pager moves nothing at all while looking perfectly correct.
    -- THE CARDS' OWN ORDER, which is not the dial's. Everything above this line
    -- has already been drawn from `slugs` and must stay on it; from here down
    -- the cards, the pager and the click keys all use the sorted copy, and they
    -- have to agree with each other or a click acts on the wrong party.
    -- THE CARDS' OWN ORDER IS THE COURT'S, and there is only one list now.
    -- It was sortable once, through a wide SORT button that lived alone on this
    -- tab; the per-column arrows that replaced it need a header strip to sit
    -- under, and the court draws cards. court_keys stays because on_party_click
    -- reads it and must keep reading the list the cards were drawn from.
    ICUI.court_keys = slugs
    ICUI.line_count = #slugs
    local at = ICUI.clamp_scroll("court", #slugs)
    for i = 1, ICUI.PARTY_SLOTS do
        local card = comp(ICUI.PARTY .. "_" .. i, panel)
        if card then
            local slug = slugs[i + at]
            if slug then
                ICUI.fill_party(card, faction, court, slug)
                card:SetVisible(true)
            else
                card:SetVisible(false)
            end
        end
    end
    ICUI.draw_pager(panel, #slugs, at)
    ICUI.draw_actions(panel, faction, court, px, py)
    return warn
end

-- CAN ANYBODY TAKE THIS SEAT AT ALL? Asked through the model's own two gates
-- rather than re-derived from the bars: IC.can_appoint knows the rank and
-- standing rules and IC.can_hire knows that a bought officer arrives in the
-- lowest band and can only fill a seat that band clears. Re-deriving either here
-- is how a card ends up stricter than the button it sits above.
--
-- BOTH HALVES. A seat nobody you have can fill but which you can BUY into is
-- not out of reach, and colouring it red would be telling the player a lie
-- about a thing they can do this turn.
function ICUI.seat_reachable(faction, office_slug)
    for _, cand in ipairs(IC.candidates(faction)) do
        if not cand.busy and IC.can_appoint(faction, office_slug, cand.cqi) then
            return true
        end
    end
    for index = 1, #IC.HIRE do
        if IC.can_hire(faction, office_slug, index) then return true end
    end
    return false
end

function ICUI.draw_offices(panel, faction, court)
    for i = 1, #ICUI.CARD_XY do
        local card = comp(ICUI.CARD .. "_" .. i, panel)
        local office = IC.OFFICES[i]
        if card and office then
            local cqi = court.offices[office.slug]
            local holder = nil
            if cqi then holder = IC.character_by_cqi(faction, cqi) end
            local bundle = IC.office_bundle(office.slug)
            local slug = cqi and IC.house_of_cqi(faction, cqi) or nil
            set_text(comp("ic_card_name", card),
                     loc("effect_bundles_localised_title_"
                         .. IC.office_bundle(office.slug), office.slug))
            -- WHAT THE SEAT ASKS. The tier's bar, on the card, because a
            -- ziggurat whose upper tiers grant more but ask nothing more is a
            -- shape and not a ladder - and the player cannot plan a climb
            -- against a number that only appears inside the picker.
            -- BOTH BARS. A gate the player only meets inside the picker is the
            -- dead-button fault wearing a different label: he picks the seat,
            -- opens the list and finds every man he has greyed out, with
            -- nothing on the card that said so.
            -- RED WHEN NOBODY CAN TAKE IT. The bars are the requirement; the
            -- colour is whether you meet it. An occupied seat is not out of
            -- reach - it is simply taken - so only a vacant one is asked.
            local need = string.format("%s / lvl %d",
                                       ICUI.cost(IC.office_influence(office.slug)),
                                       IC.office_rank(office.slug))
            if not cqi and not ICUI.seat_reachable(faction, office.slug) then
                need = ICUI.red(need)
            end
            set_text(comp("ic_card_need", card), need)
            -- HOW LONG HE HAS. A term is the thing that will empty this seat
            -- without the player doing anything, so it belongs where they can
            -- see it coming rather than as a surprise at turn start.
            local left = IC.term_left(faction, office.slug)
            local term_text = "Seat is vacant"
            if cqi and left then
                if left <= 0 then
                    term_text = "Term ends this turn"
                elseif left == 1 then
                    term_text = string.format("%d influence - 1 turn left",
                                              IC.standing(faction, cqi))
                else
                    term_text = string.format("%d influence - %d turns left",
                                              IC.standing(faction, cqi), left)
                end
            elseif cqi then
                term_text = string.format("%d influence",
                                          IC.standing(faction, cqi))
            end
            set_text(comp("ic_card_term", card), term_text)
            -- AN EMPTY SEAT COSTS NOTHING, so the cell says nothing rather
            -- than the penalty it used to carry.
            set_text(comp("ic_card_effect", card),
                     cqi and loc("derpy_ic_effects_" .. bundle, "")
                         or "Nothing while it stands empty.")
            set_text(comp("ic_card_button", card), cqi and "Dismiss" or "Appoint")
            -- A vacant office has nobody to show, so the plate hides rather than
            -- keeping the last holder's face next to the word "Vacant".
            -- The character's own porthole, the same face the row list and
            -- the lord panel draw. The cell is 238x130 - landscape, at the
            -- porthole's own proportions - so there is nothing left to fall back
            -- to: a unit card stretched across it would be worse than the empty
            -- plate a vacant office already shows.
            -- WHOSE MAN HE IS. The affinity rule is the whole squeeze and
            -- the card said nothing about which house held the seat.
            --
            -- IT SAYS WHAT THE MAN IS NOW, and the crest beside it says whose
            -- party he belongs to. Ruled 2026-09-17, on the measurements: the
            -- holder line above is 190px and a titled name wants 233 to 295, so
            -- the title cannot go in front of his name; this line can take it,
            -- and what this line used to say was already being cut off at
            -- "Covenant of the ..." for every party the model can roll. The
            -- crest carries that fact whole, and in colour.
            --
            -- NOTHING WHEN THE SEAT IS EMPTY. Cards are RECYCLED: the component
            -- that drew the last officer draws the vacancy, and a title left
            -- behind on it names a man who is no longer there.
            --
            -- AND NOTHING WHEN THE ENGINE WILL NOT SAY. Same ruling as
            -- ICUI.titled's - a made-up word under a man's name tells the
            -- player something about his officer that is not true.
            --
            -- STILL CUT. A word cannot outrun 170px today, but the cut is what
            -- check 20h reads to know this cell may skip the fit measurement,
            -- and a renamed kind is exactly the edit that would test it.
            local kind = holder and IC.kind_of_character(holder) or nil
            ICUI.fit_cut(comp("ic_card_house", card),
                         (kind and ICUI.KIND_NAME[kind]) or "")
            -- A CHARACTER'S NAME IS NOT THIS BUILD'S EITHER. It comes off the
            -- campaign, so no list of candidates exists to measure at build
            -- time, and CA's own are long enough to need this: 190px holds
            -- about 20 characters and "Drazhoath the Ashen" is 19.
            --
            -- HIS NAME AND NOTHING ELSE. It carried his position for one
            -- build and could not: 190px against a titled name wanting 233 to
            -- 295, and fit_cut keeps whole words from the FRONT, so the cell
            -- came back reading "Retainer..." - a kind and no man. The word
            -- moved to the line below, where it fits.
            ICUI.fit_cut(comp("ic_card_holder", card),
                         holder and ICUI.character_name(holder) or "Vacant")
            -- AND THE CREST, which is now the ONLY thing on this card naming
            -- the party the man belongs to. It was one of two; the line beside
            -- it carries his position instead.
            ICUI.set_card_crest(card, slug and ICUI.crest(slug) or nil)
            -- And the house's colours BEHIND his face, through the
            -- porthole's own transparency.
            -- The house's colours behind his face through the porthole's own
            -- transparency, and over it as a tint. RESOLVED ONCE: asking for the
            -- portrait twice could answer differently between the two calls and
            -- leave a tint on a cell with no face under it.
            local face = cqi and ICUI.portrait_path(cqi) or nil
            -- THE FACE FIRST. set_plate ends by setting this cell's context
            -- object, which is what fires the colour callback, so it has to be
            -- the last thing done to the cell.
            -- A VACANT SEAT WEARS NOBODY'S FACE AND NOBODY'S COLOUR. It used
            -- to hide the portrait outright and shuffle the text left into the
            -- gap; it shows the silhouette now, over a transparent plate rather
            -- than house_plate_none, which is an opaque brown box and would read
            -- as a party that has no name.
            ICUI.set_card_icon(card, face or ICUI.SILHOUETTE)
            if cqi then
                ICUI.set_plate(card, "ic_card_port", slug, face)
            else
                ICUI.set_vacant_plate(card, "ic_card_port")
            end
        end
    end
    ICUI.fill_rows(panel, {}, "offices")
    return ""
end

-- The Overseer column. A name alone reads as a seat that is working, so an
-- overseer who is not standing in his province is marked in the column that is
-- read first, not only in the Effect column beside it.
function ICUI.gov_holder_text(faction, province_key, holder, cqi)
    if not holder then return "None assigned" end
    local name = ICUI.character_name(holder)
    if IC.governor_active(faction, province_key) then return name end
    return name .. " (away)"
end

-- What the Effect column says for one province.
function ICUI.gov_effect(faction, province_key, cqi)
    if not cqi then return "None" end
    if not IC.governor_active(faction, province_key) then
        -- What it COSTS, not just where he is. "Away from the province" named
        -- the state without saying it had switched the effect off.
        return "None - he must stand in the province to govern it"
    end
    local text = loc("effect_bundles_localised_description_" .. IC.gov_bundle_base(), "")
    if text == "" then return "Governing" end
    return text
end

function ICUI.draw_govs(panel, faction, court)
    local lines = {}
    -- NO CAP. The list is built in full and the row pool windows it; capping here
    -- would silently hide every province past the fifteenth with no scrollbar to
    -- say so.
    local seats = IC.seats_named(faction)
    for i = 1, #seats do
        local province_key = seats[i].key
        local cqi = court.govs[province_key]
        local face = cqi and ICUI.portrait_path(cqi) or nil
        local holder = nil
        if cqi then holder = IC.character_by_cqi(faction, cqi) end
        local slug = nil
        if cqi then slug = IC.house_of_cqi(faction, cqi) end
        lines[i] = {
            -- CA's docs for region:province_name() say "KEY of the province
            -- containing the region" - it is not a display name, and trusting the
            -- method's name over its documentation is what put
            -- "wh3_main_combi_province_gash_kadrak" on screen. The display name
            -- lives in provinces__.loc under provinces_onscreen_<key>, verified
            -- against all 316 vanilla entries offline.
            loc("provinces_onscreen_" .. province_key, seats[i].name),
            -- "None", not "-": a dash reads as a cell that failed to draw,
            -- which is exactly what the blank columns were taken for.
            -- The NAME carries it too. "Away from the province" in the Effect
            -- column alone was not an indication: the eye reads the Overseer
            -- column first and saw a name, which says the seat is working.
            ICUI.gov_holder_text(faction, province_key, holder, cqi),
            -- WHERE THE PARTY NAME WAS. The crest in ic_row_crest is the same
            -- answer in less room, so this column is empty rather than removed:
            -- the cells are positional and Loyalty reads better where the eye
            -- has already learnt to find it.
            "",
            -- WHAT THE PROVINCE THINKS OF YOU, which is the column that used to
            -- carry the governor's effect. A province has an opinion now and it
            -- decides which way it goes when a party walks out - that is worth
            -- a column and the effect, which follows from the party in the cell
            -- beside it, is not.
            string.format("%d%%", IC.province_loyalty(faction, province_key)),
            cqi and "Release" or "Assign",
            -- The overseer's own porthole, or their house crest if it does not
            -- resolve, or nothing at all when the seat is empty. icon_kind tells
            -- the cell which SHAPE it is drawing - the two sources differ.
            -- AN EMPTY SEAT IS DRAWN AS AN EMPTY SEAT. It used to supply no
            -- icon at all, which hides the cell - so an ungoverned province
            -- read as a row that had failed to draw rather than a seat waiting
            -- to be filled, and that is the same mistake "-" made in the
            -- Overseer column. The silhouette has a transparent ground of its
            -- own, so the row's wash shows through it.
            icon = face or (slug and ICUI.crest(slug)) or ICUI.SILHOUETTE,
            icon_kind = (face or not slug) and "porthole" or "crest",
            crest = face and slug and ICUI.crest(slug) or nil,
            plate = slug,
            -- AND NOTHING BEHIND THE SILHOUETTE. Without this the cell falls
            -- back to house_plate_none, which is opaque - see fill_rows.
            vacant = (cqi == nil),
            -- WHAT ICUI.sort_rows ORDERS ON. The province name is the CELL's
            -- text and not the key: the key is wh3_main_combi_province_gash_kadrak
            -- and sorting on it would order the list by a string nobody is shown.
            sort = {
                province = loc("provinces_onscreen_" .. province_key,
                               seats[i].name),
                overseer = ICUI.gov_holder_text(faction, province_key, holder,
                                                cqi),
                loyalty = IC.province_loyalty(faction, province_key),
                cqi = cqi or 0,
                name = province_key,
            },
        }
    end
    if #seats == 0 then
        lines[1] = {"No provinces held.", "", "", "", ""}
    end
    ICUI.gov_keys = {}
    for i = 1, #seats do ICUI.gov_keys[i] = seats[i].key end
    -- THE ORDER THE PLAYER ASKED FOR, applied to the rows and to the province
    -- keys together. on_gov_click reads gov_keys[row + scroll] and nothing else
    -- connects a drawn row back to a province, so the two are permuted by one
    -- permutation or the panel offers one province and assigns another.
    ICUI.sort_rows("govs", lines, ICUI.gov_keys, #seats)
    ICUI.fill_rows(panel, lines, "govs")
    return ""
end

-- A house's display name, from its slug.
-- WHAT A PARTY IS CALLED.
--
-- THE CROWN IS YOUR FACTION and takes that faction's own screen name, which is
-- the one the rest of the game uses: a display name typed into the generator is
-- a name that can disagree with itself, and one did -
-- cr_chd_warfleet_of_uzkulak draws as "Labourfleet of Uzkulak" on the diplomacy
-- screen while this panel called it the Warfleet.
--
-- EVERY OTHER PARTY WAS ROLLED ONE and it lives in the save as two indices, so
-- there is no loc key to miss and nothing for a translation to go stale on. The
-- generated generic - "The Forge", "The Chain" - is the fallback, for a party
-- in a save made before the roll existed and for the turn before reconcile has
-- given it a name.
function ICUI.house_name(slug, faction_key)
    if not slug then return "A party" end
    faction_key = faction_key or ICUI.player()
    if slug == IC.CROWN then
        if faction_key then
            local name = loc("factions_screen_name_" .. faction_key, "")
            if name ~= "" then return name end
        end
    elseif faction_key then
        -- A CONFEDERATE PARTY IS A FACTION, and it keeps that faction's name.
        -- Rolling it one would seat "The Covenant of the Deep Furnace" where
        -- the player had just absorbed the Warhost of Zharr, and nothing on
        -- screen would connect the two.
        local came_from = IC.party_faction(faction_key, slug)
        if came_from then
            local name = loc("factions_screen_name_" .. came_from, "")
            if name ~= "" then return name end
            -- The faction's own name is a CA or lords-pack loc key and may not
            -- be there at all; the origin's display always is, and reads the
            -- same way.
            return loc("derpy_ic_origin_name_" .. slug, slug)
        end
        local rolled = IC.party_name(faction_key, slug)
        if rolled then return rolled end
    end
    return loc("derpy_ic_party_name_" .. slug, slug)
end

-- WHAT HE IS, out of the trait he carries. Nil for a man not yet stamped,
-- which is a man recruited since the last turn start and not an error.
function ICUI.bg_name(character)
    local bg = IC.bg_of_character(character)
    if not bg then return nil end
    return loc("derpy_ic_bg_name_" .. bg, bg)
end

-- AND WHERE HE CAME FROM. Drawn on the office card, where there is room for it,
-- and not in a row cell, where it would be the third thing competing for one
-- line of text.
function ICUI.origin_name(character)
    local origin = IC.origin_of_character(character)
    if not origin then return nil end
    return loc("derpy_ic_origin_name_" .. origin, origin)
end

-- His name and his trade. Two facts in one cell because the picker has five
-- columns and all five are spoken for.
function ICUI.man_line(character)
    local name = ICUI.character_name(character)
    local bg = ICUI.bg_name(character)
    if not bg then return name end
    return name .. ", " .. bg
end

-- WHAT HE IS, READ AS A POSITION RATHER THAN AS A STATISTIC.
--
-- IT SPENT ONE BUILD IN THE RANK CELL, as "General 4", and was moved in front of
-- the name on 2026-09-17: a kind is not a measurement of a man, it is what he is
-- called, and "General Zaul Zhufbarden" is how anybody would say it out loud.
-- The Rank cell went back to the number it held for the life of the panel.
ICUI.KIND_NAME = {general = "General", lord = "Lord",
                  retainer = "Retainer", hero = "Hero"}

-- A MAN'S POSITION IN FRONT OF HIS NAME.
--
-- NO TITLE RATHER THAN A WRONG ONE. kind_of_character answers nil when the
-- engine refuses the question, and a made-up word in front of a man's name
-- tells the player something about his officer that is not true.
function ICUI.titled(kind, name)
    name = name or ""
    local title = kind and ICUI.KIND_NAME[kind]
    if not title or name == "" then return name end
    return title .. " " .. name
end

-- An office's display name, from its slug.
function ICUI.office_name(key)
    if not key then return "an office" end
    return loc("effect_bundles_localised_title_" .. IC.office_bundle(key), key)
end

-- A SNUB IS EITHER, AND THE KEY SAYS WHICH. A house is insulted by its own seat
-- in another man's hands or by its own province under another man's overseer,
-- and both grievances travel as one field - in the court, in the save and in the
-- log. Which kind it is is DERIVED from the key rather than stored beside it:
-- an office slug is one of fourteen the model already knows, and anything else
-- is a province. Storing a second field would have meant a sixth column in the
-- packed court and a save format that older builds could not read.
function ICUI.snub_name(key)
    if not key then return "an office" end
    if IC.office_by_slug(key) then return ICUI.office_name(key) end
    return loc("provinces_onscreen_" .. tostring(key), key)
end

-- "held" is right for a seat and wrong for a province; "in another house's
-- hands" is right for both, which is what a shared field needs.
function ICUI.snub_line(name, key)
    return string.format("%s is insulted: %s is in another house's hands.",
                         name, ICUI.snub_name(key))
end

-- ONE ENTRY, RESOLVED AT DRAW TIME. The log stores slugs and keys and no names
-- at all: it is written from inside IC.turn, and resolving a localised string in
-- a turn handler is a turn-1 CTD that pcall cannot catch. Everything readable is
-- assembled here, where the panel is provably up.
--
-- An unknown kind returns nil and the row is skipped rather than drawn blank - a
-- log written by a newer build and read by an older one should lose the line it
-- cannot describe, not print an empty one.
function ICUI.intrigue_text(e)
    local house = ICUI.house_name(e.slug)
    if e.kind == "appoint" then
        return string.format("%s takes %s.", house, ICUI.office_name(e.key))
    elseif e.kind == "dismiss" then
        return string.format("%s is put out of %s.", house,
                             ICUI.office_name(e.key))
    elseif e.kind == "gov_on" then
        return string.format("%s is given %s to govern.", house,
                             loc("provinces_onscreen_" .. tostring(e.key), e.key))
    elseif e.kind == "gov_off" then
        return string.format("%s loses the governorship of %s.", house,
                             loc("provinces_onscreen_" .. tostring(e.key), e.key))
    elseif e.kind == "snub_on" then
        return ICUI.snub_line(house, e.key)
    elseif e.kind == "snub_off" then
        return string.format("%s is placated.", house)
    elseif e.kind == "warn" then
        return string.format("%s begins preparing to break with you.", house)
    elseif e.kind == "secede" then
        return string.format("%s HAS BROKEN WITH YOU and left the court.", house)
    elseif e.kind == "join" then
        return string.format("%s takes a seat in the court.", house)
    elseif e.kind == "splinter" then
        -- NEITHER A JOIN NOR A SECESSION. Nobody arrived from outside and
        -- nobody left the faction: the player's own house came apart, and the
        -- piece that broke off now sits in his court as an interest of its own.
        return string.format("%s breaks away from your own house.", house)
    elseif e.kind == "pressed" then
        -- NOT A SNUB. Nothing was done to them: the court has slipped far
        -- enough that the biggest bloc in it has stopped waiting for a reason.
        return string.format("%s sees the Crown weak and begins to move.", house)
    elseif e.kind == "dissolve" then
        -- NOT A SECESSION. Nobody broke with you: the last man who served that
        -- faction is dead, and a bloc is the men in it.
        return string.format("%s has no one left to speak for it.", house)
    elseif e.kind == "term" then
        -- NOT A DISMISSAL. He served his full term and stepped down; a house
        -- reading "is put out of" in the record would think it had been
        -- slighted when nothing of the kind happened.
        return string.format("%s completes a term as %s and stands down.",
                             house, ICUI.office_name(e.key))
    elseif e.kind == "hire" then
        -- The court BOUGHT this one. Worth a line of its own: an officer who
        -- appeared because you paid for him reads very differently from one who
        -- was promoted, and the appoint line beside it says nothing about money.
        return string.format("%s buys an officer into %s.", house,
                             ICUI.office_name(e.key))
    -- THE FAVOURS. e.slug is who it was done FOR - there is no actor, because
    -- the treasury pays rather than a courtier - and e.n is the gold.
    elseif e.kind == "gift" then
        return string.format("%s is sent a gift worth %d gold.", house, e.n or 0)
    elseif e.kind == "secure" then
        return string.format(
            "%s swears on the anvil: they will not break with you for %d turns. "
            .. "%d gold.", house, IC.TUNE.favour_secure_turns, e.n or 0)
    -- THE PLOTS. e.slug is who ACTED, e.key is who it was done to, and e.n is
    -- what it cost him - the one place in the record where standing goes down.
    elseif e.kind == "bribe" then
        return string.format("%s buys the goodwill of %s for %d influence.",
                             house, ICUI.house_name(e.key), e.n or 0)
    elseif e.kind == "discredit" then
        return string.format("%s spends %d influence tearing down %s.",
                             house, e.n or 0, ICUI.house_name(e.key))
    elseif e.kind == "rumour" then
        return string.format("%s spends %d influence on whispers, and somebody "
                             .. "in %s is worth less for it.",
                             house, e.n or 0, ICUI.house_name(e.key))
    elseif e.kind == "murder" then
        return string.format("%s pays %d influence, and %s has an accident at "
                             .. "the forge.", house, e.n or 0,
                             ICUI.house_name(e.key))
    -- A PLOT THAT MISSED. Its own sentence, not a suffix on the four above: the
    -- standing went, the house worked out who tried, and nothing else happened.
    elseif e.kind == "plot_failed" then
        return string.format("%s moves against %s, and is found out. %d "
                             .. "influence spent, and nothing to show for it.",
                             house, ICUI.house_name(e.key), e.n or 0)
    -- THE FIVE NEW MOVES, one sentence each.
    elseif e.kind == "provoke" then
        return string.format("%s pays %d influence to make %s an enemy on a day "
                             .. "of your choosing.", house, e.n or 0,
                             ICUI.house_name(e.key))
    elseif e.kind == "purge" then
        return string.format("%s spends %d influence, and %s is struck from the "
                             .. "rolls. The court watched.", house, e.n or 0,
                             ICUI.house_name(e.key))
    elseif e.kind == "oath" then
        return string.format("%s and %s put two names on the hot iron for %d "
                             .. "influence.", house, ICUI.house_name(e.key),
                             e.n or 0)
    elseif e.kind == "oath_broken" then
        -- e.key IS THE CAUSE, not a house: an oath ends two ways and they read
        -- differently. "died" is the guide's own rule - it lasts while both
        -- live - and "provoked" is you ending it yourself.
        if e.key == "provoked" then
            return string.format("The oath with %s is ash. You provoked them.",
                                 house)
        end
        return string.format("The oath with %s is broken. One of the two names "
                             .. "on the iron is dead.", house)
    elseif e.kind == "embezzle" then
        return string.format("%s spends %d influence quietly moving %d gold, "
                             .. "and the court smells it.", house, e.n or 0,
                             IC.TUNE.plot_embezzle_gold)
    elseif e.kind == "feast" then
        return string.format("%s spends %d influence on fire and slaves, and "
                             .. "comes away the greater for it.", house,
                             e.n or 0)
    elseif e.kind == "party_warn" then
        return string.format("%s is preparing to move against the Crown.", house)
    elseif e.kind == "party_dropped" then
        return string.format("%s's move against the Crown comes to nothing.", house)
    elseif e.kind == "party_unseat" then
        return string.format("%s spends %d influence, and a Crown officer loses "
                             .. "his seat.", house, e.n or 0)
    elseif e.kind == "party_recall" then
        return string.format("%s spends %d influence to have a Crown overseer "
                             .. "called home.", house, e.n or 0)
    elseif e.kind == "feud" then
        return string.format("%s begins a feud with %s.", house,
                             ICUI.house_name(e.key))
    elseif e.kind == "feud_end" then
        return string.format("The feud between %s and %s is over.", house,
                             ICUI.house_name(e.key))
    elseif e.kind == "demand" then
        return string.format("%s demands a post for one of their men.", house)
    elseif e.kind == "demand_met" then
        return string.format("The Crown grants %s's demand.", house)
    elseif e.kind == "demand_refused" then
        return string.format("%s's demand goes unmet, and they will remember it.",
                             house)
    elseif e.kind == "demand_void" then
        return string.format("%s's demand lapses: the man or the party is gone.",
                             house)
    elseif e.kind == "offer" then
        return string.format("%s offers the Crown a favour.", house)
    elseif e.kind == "offer_taken" then
        return string.format("The Crown accepts %s's offer, and the other "
                             .. "parties notice.", house)
    -- AND THE SEVEN THAT FILLED THE COLUMNS. The two errands name no second
    -- house because they are aimed at nobody - e.key is empty for both, and
    -- house_name would resolve it to nothing in the middle of a sentence.
    elseif e.kind == "unseat" then
        return string.format("%s spends %d influence, and every seat %s held "
                             .. "is empty by evening.", house, e.n or 0,
                             ICUI.house_name(e.key))
    elseif e.kind == "recall" then
        return string.format("%s pays %d influence to call the overseers of "
                             .. "%s home. The provinces answer to the Tower.",
                             house, e.n or 0, ICUI.house_name(e.key))
    elseif e.kind == "patron" then
        return string.format("%s spends %d influence raising a man of %s, and "
                             .. "everybody saw whose name did it.", house,
                             e.n or 0, ICUI.house_name(e.key))
    elseif e.kind == "kinsman" then
        return string.format("%s pays %d influence, and a man of %s stands "
                             .. "under your standard now.", house, e.n or 0,
                             ICUI.house_name(e.key))
    elseif e.kind == "pledge" then
        return string.format("%s pledges the forge to %s for %d influence. "
                             .. "The court heard you promise it.", house,
                             ICUI.house_name(e.key), e.n or 0)
    elseif e.kind == "audience" then
        return string.format("%s spends %d influence holding the ash court, "
                             .. "and the whole room is heard out.", house,
                             e.n or 0)
    elseif e.kind == "circuit" then
        return string.format("%s spends %d influence riding the provinces, "
                             .. "ledger in hand. They are steadier for it.",
                             house, e.n or 0)
    elseif e.kind == "fell" then
        -- NOT A DISMISSAL AND NOT A TERM. He no longer holds what the seat asks
        -- for, which is a third way out of an office and reads as neither.
        return string.format("%s no longer has the influence for %s, and is out "
                             .. "of it.", house, ICUI.office_name(e.key))
    end
    return nil
end

-- WHAT IS MOVING AGAINST YOU RIGHT NOW. Live state only - things a player can
-- still do something about. The record moved to its own tab: a page of history
-- in this list pushed the one actionable line off the screen.
-- The name of a move, and who it is aimed at once somebody has been named.
function ICUI.plot_label(plot_key, target)
    local plot = IC.plot_by_key(plot_key)
    if not plot then return tostring(plot_key) end
    if not target then return plot.name end
    local victim = IC.character_by_cqi(ICUI.player(), tonumber(target))
    return string.format("%s: %s", plot.name,
                         victim and ICUI.character_name(victim) or "?")
end

-- WHAT IS MOVING AGAINST YOU, AND WHAT YOU CAN DO ABOUT IT.
--
-- The warnings come FIRST and always: a plot list that pushed "House of Baal
-- breaks with you in 2 turns" off the top of the screen would be a tab that
-- stopped doing the job it already had.
--
-- THE OFFERED PLOTS ARE BUILT FROM IC.PLOTS, never listed here, so a plot added
-- to the model appears on this tab with no second edit - and one that is removed
-- cannot leave a dead row behind.
function ICUI.draw_intrigue(panel, faction, court)
    ICUI.plot_keys = {}
    local slugs = ICUI.court_slugs(faction)

    -- THE WARNINGS RIDE ic_alert NOW, not a band of rows above the grid. Four
    -- cards deep leaves no room for a strip, and a clock counting down to a
    -- secession is not a move: it has no price and nothing to click.
    --
    -- THE MOST URGENT ONE, AND A COUNT OF THE REST. One line cannot hold four
    -- houses, and saying only the first would hide the other three - so the
    -- shortest clock speaks and the count says how much else is moving.
    local urgent, soonest, speaker, clocked = nil, nil, nil, {}
    for i = 1, #slugs do
        local house = court.houses[slugs[i]]
        local name = ICUI.house_name(slugs[i])
        if (house.clock or 0) > 0 then
            clocked[#clocked + 1] = slugs[i]
            if not soonest or house.clock < soonest then
                soonest, speaker = house.clock, slugs[i]
                urgent = string.format(
                    "%s breaks with you in %d turn%s unless placated.",
                    name, house.clock, house.clock == 1 and "" or "s")
            end
        elseif house.snubbed then
            -- A snub is the pressure BEFORE a clock starts. It never outranks a
            -- clock, so it only speaks when nothing is counting down, and it is
            -- not counted as moving.
            if not urgent then
                urgent = ICUI.snub_line(name, house.snub_key)
            end
        end
    end

    -- THE COLUMN HEADINGS, from the model's own category list.
    for col = 1, ICUI.PLOT_COLS do
        set_text(comp("ic_plotcat_" .. col, panel),
                 string.upper(IC.PLOT_CATS[col].name))
    end

    -- THE BEST MAN YOU HAVE, once rather than per card. A move's price is paid in
    -- one courtier's standing, so the question every card is silently asking is
    -- whether anybody the player may SEND could pay it.
    local richest, richest_civil = 0, 0
    for _, cand in ipairs(IC.candidates(faction)) do
        -- THE SAME MEN THE MODEL WILL ACCEPT, asked through the model. A rival
        -- house's man cannot carry out a move, so his standing is not money this
        -- tab may price against - counting it drew a move in black that every
        -- man in the picker was then refused for.
      if IC.may_plot_as(faction, cand.cqi) then
        local has = IC.standing(faction, cand.cqi) or 0
        if has > richest then richest = has end
        -- AND THE BEST MAN WHO IS NOT COMMANDING AN ARMY, separately. A civil
        -- mission is refused to a general outright, so a court whose only rich
        -- courtier is in the field can pay for a knife and not for an errand -
        -- and one number could not say both.
        local ch = cand.character
        local general = false
        pcall(function() general = ch:has_military_force() == true end)
        if not general and has > richest_civil then richest_civil = has end
      end
    end

    for i = 1, #ICUI.PLOT_XY do
        local card = comp(ICUI.PLOT .. "_" .. i, panel)
        local plot = ICUI.plot_at[i]
        if card and plot then
            local price = ICUI.cost(IC.plot_cost(plot.key))
            local purse = IC.is_civil_mission(plot.key) and richest_civil
                          or richest
            local afford = purse >= IC.plot_cost(plot.key)
            -- CA'S OWN ART, at the path the move carries, INTO LAYER 0.
            --
            -- set_face was the wrong call and drew a white square in every one
            -- of the sixteen cards, on screen, for a whole build. It writes
            -- ICUI.FACE_INDEX, which is 1 - right for a porthole cell, which
            -- carries a plate under the face and a mask over it - and this cell
            -- carries ONE layer, because an icon needs neither. SetImagePath to
            -- a layer that is not there writes nowhere, the pcall around it
            -- swallows that, and the default 1x1_blank_white declared in the
            -- .twui.xml stays exactly where it was.
            --
            -- The comment that used to sit here argued the shared call kept the
            -- index from drifting. It is the shared call that drifted it: every
            -- OTHER cell set_face touches has three layers. set_crest is the
            -- one-layer square-icon helper and writes layer 0. Check 21b now
            -- pairs each helper's layer against each cell's layer count.
            ICUI.set_crest(card, "ic_plot_icon", plot.icon, ICUI.PLOT_ICON_PX)
            set_text(comp("ic_plot_name", card), plot.name)
            -- THE BLURB ACROSS ITS THREE CELLS, measured. twui never wraps.
            local cells = {}
            for k = 1, ICUI.PLOT_BLURB_LINES do
                cells[k] = comp(ICUI.PLOT_BLURB_KEYS[k], card)
            end
            -- WHAT IT DOES, THEN WHAT IT IS. The blurbs were all flavour and no
            -- mechanism - "Gold, slaves and a promise" does not tell a player he
            -- is buying 60 standing at 65% odds, which is the only thing he can
            -- actually decide on. The effect line goes FIRST so that if anything
            -- is lost off the bottom of the card it is the atmosphere and not
            -- the numbers; check 20d measures the pair together for exactly
            -- that reason.
            ICUI.fit_lines(cells, plot.effect .. " " .. plot.blurb)
            -- RED WHEN NOBODY YOU MAY SEND CAN PAY IT. Wrapped rather than
            -- rebuilt, so the standing icon inside the price survives the colour.
            set_text(comp("ic_plot_cost", card),
                     afford and price or ICUI.red(price))
            set_text(comp("ic_plot_go", card),
                     afford and "Plot" or ICUI.red("Plot"))
            -- Indexed by CARD, so a click needs no scroll offset and there is no
            -- way for a paged list to open the wrong move.
            ICUI.plot_keys[i] = {plot = plot.key}
        end
    end

    -- A WARNED MOVE LANDS NEXT TURN, sooner than any clock can run out, so it
    -- speaks first and the clocks join the count.
    local plot_line = ICUI.plot_alert(faction)
    if plot_line then
        urgent = plot_line
        speaker = IC.agenda(faction).plot.slug
    end
    -- PARTIES, NOT LINES: every other party with a clock running. The one
    -- speaking is not "more", whether it speaks with its clock or its plot.
    local others = 0
    for _, slug in ipairs(clocked) do
        if slug ~= speaker then others = others + 1 end
    end

    ICUI.fill_rows(panel, {}, "intrigue")
    if urgent and others > 0 then
        return string.format("%s (%d more %s moving.)", urgent, others,
                             others == 1 and "house is" or "houses are")
    end
    return urgent or ""
end


-- THE RECORD, on its own tab. A different question from Intrigue: not what is
-- happening, but what has happened.
function ICUI.draw_log(panel, faction, court)
    local lines = {}
    local log = court.log or {}
    -- NEWEST FIRST. Oldest-first puts the thing that just happened at the bottom
    -- of a full page, where the player has to go looking for it.
    for i = #log, 1, -1 do
        local text = ICUI.intrigue_text(log[i])
        if text then
            lines[#lines + 1] = {tostring(log[i].turn or 0), text, "", "", ""}
        end
    end
    if #lines == 0 then
        lines[1] = {"-", "The court has no record yet. Fill an office and "
                    .. "the houses will begin to take notice.", "", "", ""}
    end
    ICUI.fill_rows(panel, lines, "log")
    return ""
end

-- Which component a click landed on, as a name and a row index.
--
-- UIComponent TWICE, and that is not a typo: :Parent() hands back a component
-- ADDRESS, not a uicomponent, so calling :Id() straight off it throws. Inside a
-- pcall it throws SILENTLY, leaving the index nil and every button in the panel
-- dead while the click itself registers perfectly. The Great Guilds and the Zharr
-- Exchange both pay for this same two-step walk; see GGUI.on_buy_click.
function ICUI.clicked_index(context)
    if not context or not context.component then return nil end
    local ok, parent_name = pcall(function()
        return UIComponent(UIComponent(context.component):Parent()):Id()
    end)
    if not ok or not parent_name then return nil end
    -- AND THE PARENT'S NAME BESIDE THE INDEX. Two pools are instances of one
    -- .twui.xml, so an office card and a plot card have the SAME child names and
    -- a click on either reports ic_card_button. The index alone cannot tell them
    -- apart; the parent is derpy_ic_card_N or derpy_ic_plot_N and can.
    -- Every existing caller takes one value and is untouched by the second.
    return tonumber(string.match(parent_name, "_(%d+)$")), parent_name
end

-- "PARTY". Every man this picker lists is one of the player's own lords or
-- heroes - IC.candidates walks ONE faction's character list and there is no
-- second faction anywhere in that path - and now that the column names an
-- interest inside the faction rather than a house descended from another one,
-- the word is finally the true one. It was "Court House" for exactly as long as
-- a house was a faction, because "House" alone, showing "The Legion of Azgorh"
-- beside the Legion's own flag, read as another faction's lord.
-- COLUMN FIVE IS NAMED NOW, and it was blank for as long as it held nothing
-- but a button. It sorts - AVAILABLE is "who will the click actually accept"
-- - and an arrow under an empty caption is a control pointing at nothing.
ICUI.PICK_HEADERS = {"Character", "Party", "Rank", "Influence / Holds",
                     "Available"}

-- The refusal codes IC.can_appoint and IC.assign_governor return, as sentences.
-- An unmapped code still says something rather than vanishing.
function ICUI.reason_text(why, spare)
    if why == "gold" then
        return string.format("The treasury is %d gold short of that.", spare or 0)
    elseif why == "content" then
        return "They could not be more content than they already are."
    elseif why == "sworn" then
        return string.format(
            "They are already sworn for another %d turns.", spare or 0)
    elseif why == "breaking" then
        return "They have nothing left to lose. No oath holds a party at zero "
            .. "loyalty - raise it, or let them go."
    elseif why == "your own house" then
        return "You do not buy the goodwill of your own party."
    elseif why == "no such house" then
        return "That party holds no seat in your court."
    elseif why == "standing" then
        return string.format(
            "He has not the influence for that seat - %d short.",
            spare or 0)
    elseif why == "rank" then
        -- THE SHORTFALL, not the bar. can_appoint returns how many levels short
        -- he is, and the bar itself is already on the row he just clicked. This
        -- read IC.TUNE.office_rank, which stopped existing when one flat bar
        -- became a ladder, and has been drawing the word "nil" since.
        return string.format("That character is %d level%s short of that seat.",
                             spare or 0, (spare == 1) and "" or "s")
    elseif why == "term" then
        return string.format(
            "That seat is held for another %d turns. Dismiss him, or wait.",
            spare or 0)
    elseif why == "too high" then
        return "A bought officer starts on the lowest tier and climbs from there."
    elseif why == "no settlement" then
        return "You hold no settlement to hire him at."
    elseif why == "commands" then
        return "He commands a force. Generals do not run errands."
    elseif why == "cold" then
        return string.format(
            "They will not swear to you at %d loyalty. Warm them up first.",
            IC.TUNE.plot_oath_min_loyalty)
    elseif why == "oathed" then
        return "You are already bound to that house. Once is the whole of it."
    elseif why == "no seats" then
        return "They hold no office. There is nothing there to strike."
    elseif why == "no provinces" then
        return "They govern nothing. There is nobody to call home."
    elseif why == "kin cold" then
        -- ITS OWN SENTENCE AND ITS OWN NUMBER. The oath's `cold` reads off
        -- plot_oath_min_loyalty, and a shared code would print that threshold
        -- under a move gated on a different one.
        return string.format(
            "They will not give up one of their own at %d loyalty.",
            IC.TUNE.plot_kinsman_min_loyalty)
    elseif why == "spent" then
        return "There is not enough left of that house to take a man from."
    elseif why == "crown spent" then
        return "You have pledged away as much of the court as you hold."
    elseif why == "no house" then
        return "He speaks for no party your court would miss."
    elseif why == "own party" then
        return "That is your own house. Move against a rival."
    elseif why == "his own house" then
        return "A house does not move against its own. Send somebody else."
    elseif why == "your own house" then
        return "That is your own house. Move against a rival."
    elseif why == "himself" then
        return "He will not plot against himself."
    elseif why == "unique" then
        return "He is too well known to have an accident."
    elseif why == "no such plot" then
        return "No such move."
    elseif why == "no such target" then
        return "That character is no longer available."
    elseif why == "no such character" then
        return "That character is no longer available."
    elseif why == "no such office" then
        return "No such office."
    elseif why == "no offer" then
        return "That offer is no longer open."
    elseif why == "lapsed" then
        return "That offer has lapsed."
    elseif why == "room" then
        return "That army has no room for more troops."
    elseif why == "gone" then
        return "The man or party that offer named is gone."
    elseif why == "busy" then
        -- A DEMANDED MAN WHO HAS SINCE TAKEN ANOTHER POST. One post per man is
        -- the pickers' rule, and granting the demand would break it.
        return "He already holds a post, and a man holds one at a time."
    elseif why == "no demand" then
        return "That demand is no longer open."
    end
    return "That cannot be done right now."
end

-- WHAT THE OPEN PICKER ASKS OF A MAN. Not a price - nothing is deducted - but
-- the standing he has to hold, which for an office depends on which office. One
-- place, so the picker's label, its per-row test and the model cannot disagree
-- about the number on screen.
-- OFFICES AND PROVINCES ONLY. Both plot lists ask the model directly - what a
-- move costs is IC.can_plot's business and what it says on the title line is
-- IC.plot_cost's - so a third copy of the price here would be a number with
-- nothing reading it, which is exactly how it was found: a mutant that broke it
-- changed nothing on screen.
function ICUI.pick_cost(kind, key)
    if kind == "office" then return IC.office_influence(key) end
    -- ZERO, AND THAT IS THE TRUTH RATHER THAN A CONVENIENCE - the same reason
    -- the two plot lists carry a zero. A province asks nothing of a man now;
    -- IC.assign_governor has no standing test left to disagree with.
    return 0
end

function ICUI.pick_title()
    if not ICUI.pick then return "" end
    if ICUI.pick.kind == "office" then
        return string.format("Choose who takes %s - needs %s influence, held for %d turns",
            loc("effect_bundles_localised_title_" .. IC.office_bundle(ICUI.pick.key),
                ICUI.pick.key), ICUI.cost(IC.office_influence(ICUI.pick.key)),
            IC.TUNE.term_turns)
    end
    if ICUI.pick.kind == "house" then
        -- NOT A QUESTION. Every other picker title asks one, because every other
        -- picker is a choice; this one is a roster and its rows do nothing when
        -- clicked, so a title phrased as a question would be the dead button
        -- again in words.
        -- ANY PARTY'S, since 2026-09-24: clicking a chosen card again opens its
        -- members, and a rival's men are as much the question as your own.
        if ICUI.pick.slug == IC.CROWN then
            return string.format("%s - the men of your own house, and what each "
                                 .. "has earned", ICUI.house_name(ICUI.pick.slug))
        end
        return string.format("%s - its members, and what each has earned",
                             ICUI.house_name(ICUI.pick.slug))
    end
    if ICUI.pick.kind == "plot_target" then
        return string.format("%s - who is it aimed at?",
            ICUI.plot_label(ICUI.pick.plot))
    end
    if ICUI.pick.kind == "plot" then
        -- SPENDS, not needs. Every other line in this panel is about a bar a man
        -- has to clear and keep; this is the one thing that takes it off him,
        -- and the word has to say so before he clicks.
        return string.format("Who carries this out? %s - spends %s influence",
            ICUI.plot_label(ICUI.pick.plot, ICUI.pick.key),
            ICUI.cost(IC.plot_cost(ICUI.pick.plot)))
    end
    -- NO PRICE ON THE LINE, because there is none to quote. Every other picker
    -- title names the bar it asks; this one asks none, and a "needs 0
    -- influence" would be the shape of a rule with the rule taken out.
    return string.format("Choose an overseer for %s",
        loc("provinces_onscreen_" .. ICUI.pick.key, ICUI.pick.key))
end

-- WHAT THE PARTIES ASK OF YOU, on a tab of its own (author, 2026-09-24).
--
-- Offers were answered from a party's favour list, which only a click on its
-- mood opened, and a demand could be answered nowhere at all: the player had to
-- find the seat and fill it with the right man by hand, inside the turn limit.
-- One row per petition now, ACCEPT and REFUSE on it.
--
-- A DEMAND IS ALWAYS A SEAT, so accepting one seats the man it names in the post
-- it names - IC.grant_demand, through the same calls the Offices and Governors
-- tabs make, so no rule of theirs is skipped.
--
-- WHAT EACH ANSWER COSTS is in the section label rather than on every row: the
-- terms are the same for every demand and every offer, and a row that carried
-- them could not also carry the longest man's name and the longest seat.
--
-- MEASURED BY tools/gen_ic_ui.py (check 20e2): it has the whole panel width and
-- at 1600 it needs most of it, which is why it does not open by restating the
-- tab's name.
function ICUI.petitions_label()
    return string.format("A demand granted is worth +%d loyalty and a refused "
        .. "one costs %d. An accepted offer costs %d with every other party.",
        IC.TUNE.party_demand_met, IC.TUNE.party_demand_refused,
        IC.TUNE.party_offer_envy)
end

local function turns(n)
    return string.format("%d turn%s", n, n == 1 and "" or "s")
end

function ICUI.draw_petitions(panel, faction, court)
    local lines = {}
    ICUI.petition_rows = {}
    local a = IC.agenda(faction)
    local now = cm:model():turn_number()

    -- THE DEMAND FIRST: there is only ever one, and it is the one with a
    -- penalty for doing nothing.
    local d = a.demand
    if d and court.houses[d.slug] then
        local man = IC.character_by_cqi(faction, d.cqi)
        -- THE MAN IN THE FIRST COLUMN, not his party. "Make <the longest CA
        -- name> overseer of Southlands World's Edge Mountains - 5 turns" is
        -- 1007px in an 860px column; with the name moved out it is 712. The
        -- party is still on the row twice - the plate behind his face and the
        -- crest beside his name - and its card on the Court tab says DEMANDING.
        local who = man and ICUI.character_name(man) or ICUI.house_name(d.slug, faction)
        local ask
        if d.kind == "office" then
            ask = string.format("Demands the seat of %s", ICUI.office_name(d.key))
        else
            ask = string.format("Demands to oversee %s",
                loc("provinces_onscreen_" .. tostring(d.key), tostring(d.key)))
        end
        -- RED ON EXACTLY THE ROWS THE CLICK WOULD REFUSE, off the model's own
        -- question rather than a second copy of its rules.
        local may = IC.can_grant_demand(faction)
        local face = ICUI.portrait_path(d.cqi)
        lines[#lines + 1] = {
            who,
            string.format("%s - %s", ask, turns(math.max(0, d.ends - now))),
            "", "", may and "Accept" or ICUI.red("Accept"), "Refuse",
            icon = face or ICUI.crest(d.slug),
            icon_kind = face and "porthole" or "crest",
            crest = face and ICUI.crest(d.slug) or nil,
            plate = d.slug,
        }
        ICUI.petition_rows[#lines] = {kind = "demand"}
    end

    -- THE OFFERS, in the court's own order, so the list does not reshuffle
    -- between two draws of the same court.
    for _, slug in ipairs(ICUI.court_slugs(faction)) do
        local o = a.offers[slug]
        if o then
            local may = IC.can_accept_offer(faction, slug)
            lines[#lines + 1] = {
                ICUI.house_name(slug, faction),
                string.format("Offers %s - %s", ICUI.offer_what(faction, slug, o, true),
                              turns(math.max(0, o.ends - now))),
                "", "", may and "Accept" or ICUI.red("Accept"), "Refuse",
                icon = ICUI.crest(slug), icon_kind = "crest", plate = slug,
            }
            ICUI.petition_rows[#lines] = {kind = "offer", slug = slug}
        end
    end
    if #lines == 0 then
        lines[1] = {"", "No party is asking anything of you.", "", "", ""}
    end
    ICUI.fill_rows(panel, lines, "petitions")
    return ""
end

-- ANSWERING ONE. `yes` is ACCEPT, otherwise REFUSE. The row index is a WINDOW
-- index, so the page offset goes back on before it means anything.
function ICUI.on_petition_click(context, yes)
    local faction = ICUI.player()
    if not faction then return end
    local row = ICUI.clicked_index(context)
    if not row then return end
    local p = ICUI.petition_rows[row + (ICUI.scroll.petitions or 0)]
    if not p then return end
    local done, why, spare
    if p.kind == "demand" then
        if yes then
            done, why, spare = IC.grant_demand(faction)
        else
            done, why, spare = IC.refuse_demand(faction)
        end
        -- A DEMAND THE TURN HAD ALREADY DECIDED, and reason_text's "gone" is
        -- worded for an offer.
        if why == "gone" then why = "no demand" end
    elseif yes then
        done, why, spare = IC.accept_offer(faction, p.slug)
    else
        done, why, spare = IC.decline_offer(faction, p.slug)
    end
    if done then
        ICUI.notice = nil
        -- THE GOOD SOUND FOR A YES and the bad one for a no, which is what a
        -- refusal is to the party that asked.
        ICUI.confirm(nil, yes)
    else
        ICUI.notice = ICUI.reason_text(why, spare)
    end
    ICUI.refresh()
end

function ICUI.draw_picker(panel, faction, court)
    local lines = {}
    ICUI.pick_rows = {}
    -- NEITHER PLOT LIST IS PRICED HERE. Choosing a victim costs nothing - he is
    -- not the one paying - and the man who IS paying is priced by IC.can_plot,
    -- which is also the thing that will refuse him. `cost` below is the office
    -- and province bar, and both plot branches step over it.
    local targeting = (ICUI.pick.kind == "plot_target")
    local plotting = (ICUI.pick.kind == "plot")
    -- THE ONE PICKER THAT PICKS NOTHING. Opened from your own party's card, it
    -- lists that house's men and their standing and posts; no row is wired to
    -- anything, and the action cell is left EMPTY so fill_rows hides the button
    -- rather than drawing a plate with no label on it.
    local roster = (ICUI.pick.kind == "house")
    -- ZERO FOR BOTH PLOT LISTS, and that is the truthful value rather than a
    -- convenience: `cost` means "the standing bar this list asks of a man", and
    -- a plot list asks none - the model decides, per man, and hands back the
    -- shortfall itself. Letting the office bar leak in here prices a victim at
    -- the governor's 150, which is a number from another question entirely.
    local cost = 0
    if not (targeting or plotting or roster) then
        cost = ICUI.pick_cost(ICUI.pick.kind, ICUI.pick.key)
    end
    -- THE SEAT'S BAR, and 0 for anything that is not a seat.
    --
    -- The rank bar is an OFFICE rule: IC.can_appoint enforces it and
    -- IC.assign_governor does not. Applying it to both would make the picker
    -- stricter than the model, which reads as a bug in the rules rather than in
    -- the panel - the player is refused a man the game would have allowed.
    -- That used to be a separate `needs_rank` flag beside this line, which was
    -- the same fact written twice: a governor picker's key is a province and a
    -- plot picker's is a cqi, and IC.office_rank answers 0 for both. The flag
    -- could be forced true and change nothing, which is what a guard that
    -- cannot fail looks like.
    --
    -- NOT ONE NUMBER FOR ALL FOURTEEN SEATS EITHER. IC.candidates used to carry
    -- a `ranked` boolean, measurable only against a single flat bar and
    -- meaningless once the apex asks 30 and the base 5.
    local rank_bar = IC.office_rank(ICUI.pick.key)
    for _, cand in ipairs(IC.candidates(faction)) do
      -- THE ROSTER IS ONE HOUSE'S, so everyone else is skipped before a row is
      -- built rather than drawn and greyed: a man of another party is not a
      -- refused choice here, he is simply not in this house.
      if not roster or cand.slug == ICUI.pick.slug then
        -- An idle candidate holds nothing; say so rather than leaving the cell
        -- empty, which reads as a column that failed.
        local holds = "None"
        if cand.busy then
            if cand.busy.kind == "office" then
                holds = loc("effect_bundles_localised_title_"
                            .. IC.office_bundle(cand.busy.key), cand.busy.key)
            else
                holds = loc("provinces_onscreen_" .. cand.busy.key, cand.busy.key)
            end
        end
        -- HIS OWN STANDING, not the court's. Every row is priced separately
        -- now, which is the whole point of the change: the question is no
        -- longer "can the court afford this" but "which of these men has
        -- earned it".
        local has = IC.standing(faction, cand.cqi)
        local affordable = has >= cost
        local action = "Choose"
        -- BOTH PLOT LISTS ASK THE MODEL, not a second copy of its rules. Who may
        -- be moved against and who may do the moving are decided by IC.may_target
        -- and IC.can_plot, and the click is about to ask the same two functions -
        -- so a rule written there cannot go missing here, and no row can be drawn
        -- that the click would then refuse.
        --
        -- That matters most for the men this used to draw anyway: the victim is
        -- on his own actor list and his kin are on it beside him, and both are
        -- refused - "himself" and "his own house". They were drawn CHOOSE, or
        -- SHORT if they happened to be poor, and did nothing when clicked.
        local may, why_not, short_by
        if targeting then
            may, why_not = IC.may_target(faction, ICUI.pick.plot, cand.cqi)
            if not may then
                action = (why_not == "unique") and "Legend" or "Yours"
            end
        elseif plotting then
            may, why_not, short_by =
                IC.can_plot(faction, ICUI.pick.plot, cand.cqi, ICUI.pick.key)
            if not may then
                if why_not == "standing" then
                    action = string.format("Short %s",
                                           ICUI.cost(short_by or 0))
                elseif why_not == "himself" then
                    action = "Himself"
                elseif why_not == "his own house" then
                    action = "His Kin"
                elseif why_not == "not yours" then
                    -- NOT "YOURS": the targeting branch already spends that word
                    -- on the opposite meaning - a man of your own house you may
                    -- not aim at. Two labels one letter apart meaning opposite
                    -- things on the same picker is worse than either.
                    action = "Rival"
                else
                    action = "No"
                end
            end
        end
        -- NO HOUSE TEST. A province asks exactly what an office asks, and every
        -- man on this list is already one of the player's own lords or heroes -
        -- his house says who he speaks for at court, not who he serves.
        if roster then
            -- NOTHING TO CLICK. An empty last cell is what fill_rows reads to
            -- hide the button, so this is the difference between a row that
            -- says nothing and a plate that promises something.
            action = ""
        elseif targeting or plotting then
            -- Decided above, out of the model's own answer.
        elseif cand.rank < rank_bar then
            action = string.format("Rank %d", rank_bar)
        elseif cand.busy then
            -- A SEAT DOES NOT STOP HIM PLOTTING - that is why the plot branch
            -- above never reaches this one. BUSY is about taking a second post,
            -- and an officer is exactly who a player would send; greying him out
            -- would make the best men in the court the ones who can do nothing.
            action = "Busy"
        elseif not affordable then
            -- Say the shortfall BEFORE the click. Drawing CHOOSE on a row the
            -- model is going to refuse is the dead-button bug wearing a label.
            action = string.format("Short %s", ICUI.cost(cost - has))
        end
        -- THE ODDS, ON THE BUTTON. A plot is a hero action: the chance is
        -- shown at the moment of committing, not in a tooltip and not
        -- afterwards. IC.plot_chance is the same call IC.plot rolls against,
        -- so what is drawn here cannot drift from what is rolled.
        if plotting and may then
            local odds = IC.plot_chance(faction, ICUI.pick.plot, cand.cqi,
                                        ICUI.pick.key)
            if odds then action = string.format("Choose %d%%", odds) end
        end
        local face = ICUI.portrait_path(cand.cqi)
        local man = ICUI.man_line(cand.character)
        -- RESOLVED ONCE, because the cell draws it and the sort orders
        -- on it. Two calls could not disagree today, but the cell is what
        -- the player reads and the sort is the order he reads it in, and
        -- a list sorted on a name it is not showing is the worst of both.
        local party_name = cand.slug and ICUI.house_name(cand.slug, faction)
                           or "None"
        lines[#lines + 1] = {
            -- HIS TRADE TRAVELS WITH HIS NAME. It is the reason he sits
            -- where he sits - his background names his party - so a player
            -- reading a row can see why rather than only what.
            -- HIS POSITION, HIS NAME, HIS TRADE. The cell is CUT rather
            -- than clipped - see ICUI.fit_cut below and CUT_CELLS in
            -- tools/gen_ic_ui.py: even at 537px this cell cannot hold the
            -- longest thing it can be handed, and it never could. It was
            -- clipping "Amarudz Grimtidesson, Daemonsmith" mid-word before the
            -- title existed, because nothing had ever measured it.
            ICUI.titled(cand.kind, man),
            -- `faction`, NOT `faction_key`. There is no such local in this
            -- function and there never was: the name resolved to an undeclared
            -- global, which is nil, and house_name's own default - ICUI.player()
            -- - happened to be the same faction, so the cell has been drawing
            -- correctly by accident since the picker was written.
            party_name,
            -- THE NUMBER, AND ONLY THE NUMBER. The kind moved to the front
            -- of his name; this column is what it always was.
            tostring(cand.rank),
            string.format("%d influence - %s", has, holds),
            action,
            -- The character's own porthole, the same image the lord recruitment
            -- panel draws, falling back to the house crest when it does not
            -- resolve. CHARACTER_SCRIPT_INTERFACE has no portrait member at all -
            -- all 114 of them checked - so this goes through the CCO instead.
            icon = face or (cand.slug and ICUI.crest(cand.slug)) or nil,
            icon_kind = face and "porthole" or "crest",
            -- Only when the main cell is a FACE. When it has already fallen
            -- back to the crest, this would be the same flag twice.
            crest = face and cand.slug and ICUI.crest(cand.slug) or nil,
            plate = cand.slug,
            -- WHAT ICUI.sort_picker ORDERS ON, recorded here because two of the
            -- four cannot be recovered from the finished row: `ready` is
            -- decided a few lines below, in pick_rows, and `standing` has
            -- already been folded into a sentence by the time the cell is
            -- written. fill_rows reads the numbered cells and four named fields
            -- and ignores everything else, so this rides along untouched.
            sort = {name = man, standing = has, rank = cand.rank,
                    cqi = cand.cqi, party = party_name,
                    unaligned = cand.slug == nil},
        }
        -- Parallel to `lines`, so row N of the drawn window maps back to a man.
        if roster then
            -- NIL, DELIBERATELY. Every row of the roster is unwired: it reports
            -- rather than offers, and on_pick_click reads this table.
            ICUI.pick_rows[#lines] = nil
        elseif targeting or plotting then
            ICUI.pick_rows[#lines] = may and cand.cqi or nil
        else
            ICUI.pick_rows[#lines] =
                (cand.rank >= rank_bar and not cand.busy and affordable)
                and cand.cqi or nil
        end
        -- AND RED ON EXACTLY THE ROWS THE CLICK WOULD REFUSE. Read off
        -- pick_rows rather than re-testing the rules, because pick_rows is what
        -- the click itself reads - a second copy of the condition here could
        -- colour a row the button would accept, or worse, the other way round.
        --
        -- NOT ON THE ROSTER. Red means "you asked for this and cannot have it";
        -- every roster row is unwired by design, and reddening all of them would
        -- say the whole list was refused.
        -- AND THE SAME ANSWER THE SORT USES. Read off pick_rows for the same
        -- reason the red below is: pick_rows is what the CLICK reads, so an
        -- AVAILABLE sort built from a second copy of the rules could lift a man
        -- to the top of the list that the button would then refuse.
        lines[#lines].sort.ready = ICUI.pick_rows[#lines] ~= nil
        if not roster and not ICUI.pick_rows[#lines] then
            lines[#lines][5] = ICUI.red(lines[#lines][5])
        end
      end
    end
    -- THE ORDER THE PLAYER ASKED FOR, applied to the men and to the click keys
    -- together, and applied HERE - after every candidate is on the list and
    -- before the hires are appended under them. Sorting after the hires would
    -- shuffle three rows that are not candidates in among the men.
    ICUI.sort_rows("pick", lines, ICUI.pick_rows, #lines)

    -- AND THE MEN WHO DO NOT EXIST YET, on the end of the same list.
    -- OFFICE PICKER ONLY: a bought officer arrives to take a seat, and there is
    -- nothing to buy a man for when the question is who carries out a plot.
    --
    -- ONE LIST, not a second panel: with fourteen seats to fill and a bar on
    -- every one of them, "I have nobody for this" is the ordinary state of an
    -- early court, and the answer to it belongs where the player is already
    -- looking. They cost more than an appointment because the court is
    -- paying for the man as well as the seat.
    --
    -- OFFICES ONLY. A governorship is a job for somebody who is already yours;
    -- buying a stranger to hand him a province is the opposite of the rule the
    -- Governors tab just started enforcing.
    if ICUI.pick.kind == "office" then
        local own = IC.CROWN
        local hire_cost = IC.hire_cost()
        for index = 1, #IC.HIRE do
            local ok, why, spare = IC.can_hire(faction, ICUI.pick.key, index)
            local action = "Hire"
            if not ok then
                if why == "term" then
                    action = string.format("Term %d", spare or 0)
                elseif why == "too high" then
                    action = "Too High"
                else
                    action = "No"
                end
            end
            lines[#lines + 1] = {
                "Hire: " .. IC.HIRE[index].name,
                own and ICUI.house_name(own) or "None",
                -- WHAT HE ARRIVES AT, which is this seat's bar and not one
                -- number for all fourteen. Same deletion as the refusal text
                -- above: this cell has been drawing "nil".
                tostring(IC.office_rank(ICUI.pick.key)),
                string.format("arrives with %s influence",
                              ICUI.cost(hire_cost)),
                action,
                -- No face: he does not exist, and CA's portrait for a subtype
                -- is chosen when the character is made, not before. The house
                -- crest says whose man he will be, which is the part that is
                -- already decided.
                icon = own and ICUI.crest(own) or nil,
                icon_kind = "crest",
                plate = own,
            }
            -- A TABLE, not a cqi. There is no character to point at yet, so the
            -- click has to carry which shape was chosen instead.
            ICUI.pick_rows[#lines] = ok and {hire = index} or nil
        end
    end
    if #lines == 0 then
        lines[1] = {"No characters in this faction.", "", "", "", ""}
    end
    ICUI.fill_rows(panel, lines, "pick")
    return ""
end

-- A click on a picker row. The row index is a WINDOW index, so the scroll offset
-- has to be added back on before it means anything - forgetting that picks the
-- wrong man, quietly, and only once the list is scrolled.
function ICUI.on_pick_click(context, faction)
    local row = ICUI.clicked_index(context)
    if not row then return false end
    local at = ICUI.scroll.pick or 0
    local chosen = ICUI.pick_rows[row + at]
    if not chosen then return false end     -- unranked, already busy, or refused
    local done, why, spare
    if type(chosen) == "table" then
        -- A man who does not exist yet. Only the office picker offers these.
        done, why, spare = IC.hire(faction, ICUI.pick.key, chosen.hire)
    elseif ICUI.pick.kind == "office" then
        done, why, spare = IC.appoint(faction, ICUI.pick.key, chosen)
    elseif ICUI.pick.kind == "plot_target" then
        -- NOT A REFUSAL AND NOT A DONE MOVE: the first of two questions. The
        -- second picker opens on the same panel with the victim now named.
        ICUI.pick = {kind = "plot", plot = ICUI.pick.plot,
                     key = tostring(chosen)}
        ICUI.scroll.pick = 0
        ICUI.notice = nil
        return true
    elseif ICUI.pick.kind == "plot" then
        done, why, spare = IC.plot(faction, ICUI.pick.plot, chosen, ICUI.pick.key)
    else
        done, why, spare = IC.assign_governor(faction, ICUI.pick.key, chosen)
    end
    if done then
        -- THE SEAT THIS FILLED, read BEFORE the picker is cleared: once
        -- ICUI.pick is nil there is nothing left saying which card to light.
        local filled = (ICUI.pick.kind == "office") and ICUI.pick.key or nil
        ICUI.pick = nil
        ICUI.scroll.pick = 0
        -- A PLOT THAT RESOLVED IS STILL OWED AN ANSWER. `done` means the move
        -- happened; it does not mean it worked. IC.plot hands back "landed" or
        -- "failed" in the slot a refusal uses for its reason, and a miss that
        -- said nothing would read as a button that did nothing.
        if why == "failed" then
            ICUI.notice = "It did not work. The influence is spent, and they "
                          .. "know perfectly well who tried."
            ICUI.confirm(nil, false)
        else
            ICUI.notice = nil
            -- THE CARD THAT JUST CHANGED, when a seat is what changed. The
            -- panel is about to redraw the whole ziggurat and the only
            -- difference will be one name in the middle of fourteen cards.
            ICUI.confirm(filled and ICUI.office_card(filled) or nil, true)
        end
    else
        -- The picker stays OPEN on a refusal. Closing it would drop the player
        -- back on a list with no idea why nothing changed.
        ICUI.notice = ICUI.reason_text(why, spare)
    end
    return true
end

function ICUI.refresh()
    local panel = comp(ICUI.PANEL)
    if not panel then return end
    local faction = ICUI.player()
    if not faction then return end
    local court = IC.court(faction)
    -- THE BOX'S ORIGIN, not the panel's: the content offset, added once here as
    -- layout() adds it, because everything below that moves a component - the
    -- pie, the header strip, the arrows - is placed from these two. They drew
    -- at the screen's corner on any screen the box did not fill.
    local px, py = panel:Position()
    px = px + ICUI.OX
    py = py + ICUI.OY
    -- The picker is modal: while it is up it owns the list, the headers and the
    -- section label, whichever tab is lit behind it.
    local view = ICUI.live_view()

    set_text(comp("ic_title", panel), loc("derpy_ic_title", "Hashut's Court"))
    set_text(comp("ic_influence", panel),
             string.format("%d of %d seats filled",
                           IC.filled_offices(faction), #IC.OFFICES))
    -- TITLE CASE ON EVERY BUTTON, not capitals (author, 2026-09-25): the
    -- engine's brand_header face draws capitals 12-20% wider than the width
    -- check's stand-in font, and GOVERNORS and PETITIONS ran over their plates.
    set_text(comp("ic_tab_court", panel), "Court")
    set_text(comp("ic_tab_offices", panel), "Offices")
    set_text(comp("ic_tab_govs", panel), "Governors")
    set_text(comp("ic_tab_intrigue", panel), "Intrigue")
    set_text(comp("ic_tab_log", panel), "Record")
    set_text(comp("ic_tab_petitions", panel), "Petitions")
    ICUI.light_tabs(panel)
    if ICUI.pick then
        set_text(comp("ic_lbl_section", panel), ICUI.pick_title())
    else
        set_text(comp("ic_lbl_section", panel), ICUI.section_text(view))
    end
    -- AND IT SITS IN TWO DIFFERENT PLACES. On the court it is the first line
    -- inside the Crown's box; on every other view it is the full-width line
    -- under the tabs. One component, so it is MOVED rather than duplicated -
    -- and moved on every refresh, because a label left in the Crown's box after
    -- a tab change is a sentence floating in the middle of a list.
    --
    -- NOT WHILE THE PICKER IS UP. The picker is modal and owns the whole width
    -- for its question, whichever tab is lit behind it.
    local sec = comp("ic_lbl_section", panel)
    if sec then
        local home = ICUI.PANEL_XY.ic_lbl_section
        if view == "court" and not ICUI.pick then
            home = ICUI.COURT_SECTION_XY
        end
        sec:MoveTo(px + home[1], py + home[2])
        -- AND SIZED FOR IT: the Crown's box on the court, the full content
        -- width everywhere else. gen_ic_ui.py checks the court home at its own
        -- width, so a label left at the other one is not the label it checked.
        ICUI.resize(sec, home[3], home[4])
    end

    local headers = ICUI.HEADERS[view]
    -- PICK_HEADERS IS THE CHARACTER LIST'S, and every picker is one now: the
    -- favour list that had its own row in HEADERS is gone (2026-09-24).
    if ICUI.pick then headers = ICUI.HEADERS[view] or ICUI.PICK_HEADERS end
    -- ONE HOME FOR THE STRIP. It used to have a second, lower one for the
    -- court, whose list started below the pie; the court has no list and the
    -- pie is not above one.
    local hdr_y = ICUI.HDR_Y
    for i = 1, #ICUI.HDR_KEYS do
        local c = comp(ICUI.HDR_KEYS[i], panel)
        -- THE ACTIVE COLUMN NAMES ITSELF. The arrows are identical to each
        -- other by design - see ICUI.SORT_LIT - so without this the player can
        -- see that the list is sorted and not by what.
        local active = ICUI.sort_for_column(view, i)
                       and ICUI.sort[view] == ICUI.sort_for_column(view, i)
        if c then
            local xy = ICUI.PANEL_XY[ICUI.HDR_KEYS[i]]
            if xy then c:MoveTo(px + xy[1], py + hdr_y) end
            if headers then
                local text = headers[i] or ""
                if active and text ~= "" then
                    text = string.format("[[col:%s]]%s[[/col]]",
                                         ICUI.SORT_LIT, text)
                end
                set_text(c, text)
            end
            show(c, headers ~= nil)
        end
        -- AND ITS ARROW UNDER IT. Shown only where this view has a mode for
        -- that column AND the column has a caption: an arrow under a blank
        -- header is a control pointing at nothing, and an arrow on a view that
        -- cannot sort is the dead-button fault.
        local a = comp(ICUI.HSORT_KEYS[i], panel)
        if a then
            local sortable = headers ~= nil
                             and (headers[i] or "") ~= ""
                             and ICUI.sort_for_column(view, i) ~= nil
            if sortable then
                local ax = ICUI.PANEL_XY[ICUI.HSORT_KEYS[i]]
                -- BESIDE THE CAPTION, WHEREVER THE CAPTION ENDS. Measured with
                -- the engine's own call on the header cell, the same one
                -- ICUI.fit_cut uses - and measured on the PLAIN text, before
                -- the active column's colour markup goes on, because a tag is
                -- not glyphs and would push the arrow out by its own length.
                if ax then
                    a:MoveTo(px + ax[1] + ICUI.hdr_text_w(c, headers[i]),
                             py + hdr_y + ICUI.HSORT_DY)
                end
                local path = ICUI.sort_arrow_path(view, i)
                for index = 0, 1 do
                    pcall(function() a:SetImagePath(path, index) end)
                end
            end
            show(a, sortable)
        end
    end

    -- Cards belong to the offices view, the standing bar to the court view.
    -- Anything a view does not use is hidden HERE, by the dispatcher: a component
    -- left over from the previous view draws on top of the new one, and on
    -- 2026-09-11 all six cards drew underneath the court's house rows.
    for i = 1, #ICUI.CARD_XY do
        -- `view` is already "pick" while the picker is up, so testing ICUI.pick
        -- again here would be dead code.
        show(comp(ICUI.CARD .. "_" .. i, panel), view == "offices")
    end
    -- The move cards belong to the intrigue view and to nothing else. Same rule,
    -- same reason: CreateComponent makes a VISIBLE component, so one this loop
    -- does not reach has never been hidden since the panel was built.
    for i = 1, #ICUI.PLOT_XY do
        show(comp(ICUI.PLOT .. "_" .. i, panel), view == "intrigue")
    end
    -- AND THE COLUMN HEADERS WITH THEM. They are panel children, so the loop
    -- above does not reach them and nothing else would ever hide them.
    for i = 1, ICUI.PLOT_COLS do
        show(comp("ic_plotcat_" .. i, panel), view == "intrigue")
    end
    -- EVERY pip and EVERY crest, not MAX_ROWS of them. One this loop does not
    -- reach has never been hidden since the panel was built, because
    -- CreateComponent makes a VISIBLE component and nothing else touches it.
    if view ~= "court" then
        for i = 0, ICUI.DIAL_SLICES - 1 do
            show(comp(string.format("ic_wedge_%02d", i), panel), false)
        end
        -- The crest is a SEPARATE component from the cells it sits among, so
        -- hiding them does not hide it. One left behind is a crest floating
        -- over another tab's list.
        for i = 1, ICUI.MAX_HOUSES do
            show(comp(string.format("ic_barc_%02d", i - 1), panel), false)
            show(comp(string.format("ic_barp_%02d", i - 1), panel), false)
            -- A WALL IS ITS OWN COMPONENT too, and the wedge loop above does
            -- not reach it. One left behind is a bronze spoke across whatever
            -- the next tab draws, pointing at nothing.
            show(comp(string.format("ic_div_%02d", i - 1), panel), false)
        end
        for _, name in ipairs(ICUI.CONTROL_KEYS) do
            show(comp(name, panel), false)
        end
        -- THE PARTY GRID AND THE CROWN'S BLOCK. Nothing else hides these: the
        -- row pool is hidden by fill_rows, which the court view no longer
        -- calls, and a card left behind draws over the list of whatever tab
        -- the player just opened. Hidden HERE and shown by draw_court, so a
        -- draw that throws leaves an empty tab rather than a stale one.
        for i = 1, ICUI.PARTY_SLOTS do
            show(comp(ICUI.PARTY .. "_" .. i, panel), false)
        end
        for _, name in ipairs(ICUI.LEADER_KEYS) do
            show(comp(name, panel), false)
        end
        -- THE BORDER IS A SEPARATE COMPONENT from the wedges it frames, so the
        -- loop above does not reach it. Left behind it is a gold arc across the
        -- top of whatever the next tab draws.
        show(comp("ic_dial_rim", panel), false)
        -- AND THE PLATE UNDER IT. It is the largest single thing on the tab, so
        -- one left behind is an opaque black box over the whole of whatever the
        -- next tab draws - not a stray label, the entire list.
        show(comp("ic_dial_box", panel), false)
        -- THE COLUMN FURNITURE. The court is the only two-column tab; the other
        -- four use the full width, so a header, a rule and an opaque plate left
        -- behind would all draw straight across their lists.
        for _, name in ipairs(ICUI.COLUMN_KEYS) do
            show(comp(name, panel), false)
        end
        -- AND THE ACTION BAR, which draw_actions shows. It sits in the pager's
        -- row, so one left behind is three buttons beside another list's pager.
        for _, name in ipairs(ICUI.ACT_KEYS) do
            show(comp(name, panel), false)
        end
        show(comp("ic_act_hint", panel), false)
    else
        for _, name in ipairs(ICUI.CONTROL_KEYS) do
            show(comp(name, panel), true)
        end
        show(comp("ic_dial_rim", panel), true)
        show(comp("ic_dial_box", panel), true)
        for _, name in ipairs(ICUI.COLUMN_KEYS) do
            show(comp(name, panel), true)
        end
        -- AND THE ROW POOL IS NOT THE COURT'S ANY MORE. Every other list view
        -- fills it and fill_rows hides the tail; the court draws cards, so
        -- without this the rows the last tab left behind stay on screen
        -- underneath them.
        for i = 1, ICUI.MAX_ROWS do
            show(comp(ICUI.ROW .. "_" .. i, panel), false)
        end
    end

    -- EVERY DRAW IS WRAPPED, and this is not defensive padding. A draw that
    -- throws used to abort refresh() halfway: the headers had already been
    -- rewritten, the rows kept whatever the PREVIOUS view left in them, and the
    -- error died inside the click listener without reaching the log. That is
    -- exactly how the governors tab came to show an empty list with correct
    -- headers and nothing at all to say why. Now the panel reports its own
    -- failure on screen, where it cannot be missed.
    local warn = ""
    local ok, err = pcall(function()
        if ICUI.pick then
            warn = ICUI.draw_picker(panel, faction, court)
        elseif view == "offices" then
            warn = ICUI.draw_offices(panel, faction, court)
        elseif view == "govs" then
            warn = ICUI.draw_govs(panel, faction, court)
        elseif view == "intrigue" then
            warn = ICUI.draw_intrigue(panel, faction, court)
        elseif view == "log" then
            warn = ICUI.draw_log(panel, faction, court)
        elseif view == "petitions" then
            warn = ICUI.draw_petitions(panel, faction, court)
        else
            warn = ICUI.draw_court(panel, faction, court, px, py)
        end
    end)
    if not ok then
        warn = "Panel error in " .. tostring(view) .. ": " .. tostring(err)
        -- And clear the stale list, so what is on screen is never the last
        -- view's data wearing this view's headers.
        --
        -- NOT ON THE COURT. That view hides the whole row pool before it draws,
        -- so there is no stale list to clear - and putting a line into the pool
        -- would draw it straight through the dial's plate and the card grid,
        -- which are what is actually on screen. The error still reaches the
        -- player: it is in `warn`, and ic_alert is the one strip nothing covers.
        if view ~= "court" then
            pcall(function()
                ICUI.fill_rows(panel,
                               {{"(this list failed to draw)", "", "", "", ""}},
                               view)
            end)
        end
    end

    -- A notice about the player's last click outranks the standing secession
    -- warning: they just did something and are owed an answer about it.
    local alert = comp("ic_alert", panel)
    local text = ICUI.notice or warn or ""
    if alert then
        set_text(alert, text)
        alert:SetVisible(text ~= "")
    end
end

-- The campaign HUD is NOT one component. hud_campaign is the big one, but the
-- button cluster at the top left and the icons at the top right are its SIBLINGS
-- at the ui root - hiding hud_campaign alone left both on screen over the court.
--
-- So every child of the root is hidden except our own panel. That beats naming
-- them: a hardcoded list of CA component names is a list that rots at the next
-- patch, silently, into a HUD that half reappears.
--
-- BY ID, NOT BY HANDLE. A destroyed uicomponent still passes is_uicomponent, so a
-- cached handle is a trap; what is recorded is the set of ids actually hidden,
-- and the restore walks the root again and matches on Id(). Anything already
-- hidden when we arrived is not recorded, so it is not switched on afterwards.
local function each_root_child(fn)
    local r = root()
    if not r then return end
    local n = 0
    if not pcall(function() n = r:ChildCount() end) then return end
    for i = 0, n - 1 do
        local child
        -- CA's own idiom: Find(index) returns an ADDRESS and UIComponent casts
        -- it. See lib_battle_ui.lua, which walks children exactly this way.
        if pcall(function() child = UIComponent(r:Find(i)) end)
                and is_uicomponent(child) then
            pcall(function() fn(child) end)
        end
    end
end

-- Which ids we switched off, or nil when the screen is not ours.
ICUI.hidden = nil

function ICUI.show_hud(on)
    if not on then
        local hidden = {}
        each_root_child(function(c)
            local id = c:Id()
            if id and id ~= ICUI.PANEL then
                local vis = true
                pcall(function() vis = c:Visible() end)
                if vis then
                    c:SetVisible(false)
                    hidden[id] = true
                end
            end
        end)
        ICUI.hidden = hidden
        return
    end
    local hidden = ICUI.hidden
    ICUI.hidden = nil
    if not hidden then return end
    each_root_child(function(c)
        if hidden[c:Id()] then c:SetVisible(true) end
    end)
end

function ICUI.open()
    if comp(ICUI.PANEL) then ICUI.refresh() return end
    local ok, err = pcall(function()
        local r = root()
        -- THE BOX FIRST, because it decides which file the panel is built
        -- from. Dimensions(), never Bounds(): Bounds() includes children, and a
        -- panel centred against an inflated screen is what "it opens at the
        -- side" was.
        local sw, sh = r:Dimensions()
        local bw, bh = ICUI.box_for(sw, sh)
        -- A SCALE THAT FAILS OPENS THE PANEL AT THE BASE, the way every panel
        -- opened before it could scale, and says why. A court that will not
        -- open at all is worse than a 1920 court clipped on a small screen.
        local scaled, why = pcall(ICUI.apply_scale, bw)
        if not scaled then
            log("scaling to a " .. tostring(bw) .. " box failed, opening at 1920: "
                .. tostring(why))
            bw, bh = 1920, 1080
            ICUI.apply_scale(bw)
        end
        r:CreateComponent(ICUI.PANEL, ICUI.path(ICUI.PATH_PANEL))
        local panel = comp(ICUI.PANEL)
        if not panel then return end

        -- COVER THE SCREEN. The panel is the screen or the box, whichever is
        -- bigger, so its ground reaches the edges of a screen that is not
        -- 16:9 - otherwise the campaign map shows around a letterbox with the
        -- HUD hidden, which is worse than either. The content offset puts the
        -- box in the middle of it.
        local pw, ph = math.max(sw, bw), math.max(sh, bh)
        ICUI.resize(panel, pw, ph)
        ICUI.OX = math.floor((pw - bw) / 2)
        ICUI.OY = math.floor((ph - bh) / 2)
        -- Zero, except on a screen under 1600x900: that one is smaller than the
        -- box and still centres, both offsets negative.
        panel:MoveTo(math.floor((sw - pw) / 2), math.floor((sh - ph) / 2))
        panel:PropagatePriority(60)

        -- AND IT EATS THE MOUSE WHILE IT IS UP. Without this the panel is
        -- scenery: the cursor reaches the campaign map straight through 1600x900
        -- of background, so hovering raises the region and army tooltips of
        -- whatever is behind it and a click lands on the map as well as on us. An
        -- interactive CONTAINER is CA's norm and no risk to its children.
        --
        -- A LITERAL true IS SAFE HERE ONLY BECAUSE ICUI.close DESTROYS THE PANEL.
        -- If close() is ever changed to hide instead, this flag must be written
        -- from the same variable as the visibility - interactive-while-hidden is a
        -- dead zone in the middle of the map that nothing on screen explains.
        panel:SetInteractive(true)

        for i = 1, #ICUI.CARD_XY do
            panel:CreateComponent(ICUI.CARD .. "_" .. i, ICUI.path(ICUI.PATH_CARD))
        end
        for i = 1, #ICUI.PARTY_XY do
            panel:CreateComponent(ICUI.PARTY .. "_" .. i, ICUI.path(ICUI.PATH_PARTY))
        end
        for i = 1, #ICUI.PLOT_XY do
            panel:CreateComponent(ICUI.PLOT .. "_" .. i, ICUI.path(ICUI.PATH_PLOT))
        end
        for i = 1, ICUI.MAX_ROWS do
            panel:CreateComponent(ICUI.ROW .. "_" .. i, ICUI.path(ICUI.PATH_ROW))
        end
        -- Creation only above. layout() places and sizes every component,
        -- including the panel's own children, which the .twui.xml offsets do not.
        ICUI.layout()
        -- WHAT THIS SCREEN GOT, read back off a card rather than off the
        -- tables: the one line in a player's log that says which box and which
        -- files their panel was built at.
        local cw, ch = 0, 0
        local card = comp(ICUI.CARD .. "_1", panel)
        if card then cw, ch = card:Dimensions() end
        log(string.format("layout box=%dx%d k=%.3f compact=%s card_1=%dx%d",
                          bw, bh, bw / 1920, tostring(ICUI.COMPACT), cw, ch))
    end)
    if ok and comp(ICUI.PANEL) then
        -- AFTER creation, never before: a failed CreateComponent must not be able
        -- to leave the player with a hidden HUD and no panel to close.
        ICUI.show_hud(false)
        -- AND THE FEED WAITS, under the same guard and for the same reason. This
        -- panel is priority 60 and covers the screen while CA's events layout is
        -- 50, so a card raised from a click inside it opens underneath it and is
        -- never seen. A hold set on a panel that failed to open would be a hold
        -- nothing ever releases.
        IC.hold_feed(true)
        ICUI.refresh()
    else
        ICUI.show_hud(true)
        log("the panel failed to open: " .. tostring(err or "CreateComponent made no panel"))
    end
end

function ICUI.close()
    -- FIRST, and unconditionally. Everything below can be a no-op - the panel may
    -- already be gone - but a campaign HUD left hidden is an unplayable screen
    -- with nothing on it to explain itself, so the restore never sits behind a
    -- condition that could skip it.
    ICUI.show_hud(true)
    -- AND THE CARDS THIS PANEL HELD BACK, for the same reason and in the same
    -- place: a feed left held is a card the player never sees at all, which is
    -- worse than the covered card the hold exists to prevent. Released before
    -- the panel is destroyed, so nothing below can skip it either.
    IC.hold_feed(false)
    -- Drop the modal state with the panel. Otherwise the next open lands straight
    -- back in a picker for an office the player has long since forgotten asking
    -- about, sitting over whichever tab is lit.
    ICUI.pick = nil
    ICUI.scroll.pick = 0
    ICUI.notice = nil
    -- AND THE CHOSEN PARTY, for the same reason: the next open starts on the
    -- court with nothing chosen, not on a bar aimed at last week's rival.
    ICUI.sel = nil
    local panel = comp(ICUI.PANEL)
    if panel then pcall(function() panel:DestroyChildren() panel:Destroy() end) end
end

-- The office card's one button, which is two verbs: a filled office dismisses,
-- an empty one opens the picker.
-- ONE CHILD NAME, TWO POOLS. Both are instances of derpy_ic_card, so the
-- button reports the same id on an office card and on a move; the PARENT is what
-- differs. Dispatching on ICUI.view instead would be a guess that goes wrong the
-- moment one view draws both.
--
-- A NAMED FUNCTION AND NOT A BRANCH INSIDE THE LISTENER, because the listener is
-- registered against the real UI and a check cannot reach into it. Left inline,
-- ROUTING BY ID, WHICH IS WHERE IT BELONGS. There used to be an
-- ICUI.on_card_button here that read the clicked component's PARENT name and
-- sent derpy_ic_plot_N one way and derpy_ic_card_N the other. That existed for a
-- plan that was abandoned: the move card was going to be a second pool of
-- instances off derpy_ic_card.twui.xml, sharing its child names, so the id could
-- not have told them apart. It got its own file instead - the button is
-- ic_plot_go and the office card's is ic_card_button - and the listener's own id
-- test answers the question the parent name was invented to answer.
--
-- Keeping it would have been two derivations of one fact with the SECOND one
-- unreachable, which is the shape this file has been bitten by before: neither
-- copy can be seen to fail.

-- A MOVE, PICKED OFF ITS CARD. The body is what the intrigue row's last column
-- used to do; what changed is where the index comes from - the card's own
-- position in the pool, with no scroll offset, because a grid does not scroll.
function ICUI.on_plot_click(context)
    local faction = ICUI.player()
    if not faction then return end
    if ICUI.pick then return end
    local slot = ICUI.clicked_index(context)
    if not slot then return end
    local move = (ICUI.plot_keys or {})[slot]
    if not move then return end
    -- THE VICTIM FIRST, then who carries it out. on_pick_click chains the
    -- second picker off the first.
    --
    -- UNLESS THERE IS NO VICTIM. A civil mission aims at nobody, so asking
    -- who it is aimed at would be a list of men none of whom is the answer.
    -- It opens the second picker directly, with a nil key - which
    -- may_target, can_plot, plot_chance and pick_title all already take.
    if IC.plot_is_aimed(move.plot) then
        ICUI.pick = {kind = "plot_target", plot = move.plot}
    else
        ICUI.pick = {kind = "plot", plot = move.plot, key = nil}
    end
    ICUI.scroll.pick = 0
    ICUI.notice = nil
    ICUI.refresh()
end

function ICUI.on_office_click(context)
    local faction = ICUI.player()
    if not faction then return end
    local slot = ICUI.clicked_index(context)
    if not slot then return end
    local office = IC.OFFICES[slot]
    if not office then return end
    local court = IC.court(faction)
    if court.offices[office.slug] then
        IC.dismiss(faction, office.slug)
        -- THE BAD SOUND, deliberately. Sacking a man is not a win: it empties a
        -- seat you were getting something from and insults the party he came
        -- from. The confirmation should not congratulate the player for it.
        ICUI.confirm(comp(ICUI.CARD .. "_" .. slot, comp(ICUI.PANEL)), false)
        ICUI.notice = nil
    else
        -- NO LOCK TO TEST. The seat is empty, which is the only way this
        -- branch is reached: a term keeps a man in his seat, it does not keep
        -- an empty seat shut.
        ICUI.pick = {kind = "office", key = office.slug}
        ICUI.scroll.pick = 0
        ICUI.notice = nil
    end
    ICUI.refresh()
end

-- The last column of a row, which means something different on every list: it is
-- CHOOSE in the picker, ASSIGN or RELEASE on governors, and nothing at all on the
-- court and intrigue lists.
function ICUI.on_row_action(context)
    local faction = ICUI.player()
    if not faction then return end
    if ICUI.pick then
        if ICUI.on_pick_click(context, faction) then ICUI.refresh() end
        return
    end
    -- NOTHING FOR INTRIGUE HERE ANY MORE. The moves are cards and are clicked
    -- through ICUI.on_plot_click; the rows this view still draws are the warning
    -- band, which has no last column and nothing to act on. Leaving the old
    -- branch would have been worse than dead code: it indexed plot_keys by DRAWN
    -- ROW, and plot_keys is now indexed by card, so a click on the first warning
    -- would have opened a picker for the first move.
    -- ACCEPT, on the Petitions tab.
    if ICUI.view == "petitions" then
        ICUI.on_petition_click(context, true)
        return
    end
    if ICUI.view ~= "govs" then return end
    local row = ICUI.clicked_index(context)
    if not row then return end
    -- The keys the LAST DRAW used, not a fresh IC.seats() call: re-deriving here
    -- would act on a different list if the empire changed between draw and click.
    -- WINDOW index plus the scroll offset - without the offset this releases the
    -- wrong province the moment the list is scrolled, and looks fine until then.
    local province_key = (ICUI.gov_keys or {})[row + (ICUI.scroll.govs or 0)]
    if not province_key then return end
    local court = IC.court(faction)
    if court.govs[province_key] then
        IC.release_governor(faction, province_key)
    else
        ICUI.pick = {kind = "gov", key = province_key}
        ICUI.scroll.pick = 0
    end
    ICUI.refresh()
end

-- A CLICK ON A PARTY CARD, anywhere on it (author, 2026-09-24). The first
-- click chooses the party - the action bar under the cards acts on the chosen
-- one - and a click on the party already chosen opens its members.
--
-- ANYWHERE ON IT: the card is the control, and the cells that carry a tooltip
-- are interactive and report their own id, so the listener routes both here.
-- The card's own id names its slot; a cell's slot is its parent's.
function ICUI.party_slot(context)
    local slot = tonumber(string.match(context and context.string or "",
                                       "^" .. ICUI.PARTY .. "_(%d+)$"))
    if slot then return slot end
    return ICUI.clicked_index(context)
end

function ICUI.on_party_click(context)
    local faction = ICUI.player()
    if not faction or ICUI.pick then return end
    if ICUI.live_view() ~= "court" then return end
    local slot = ICUI.party_slot(context)
    if not slot then return end
    -- THE KEYS THE LAST DRAW USED, plus that draw's page offset. Re-deriving
    -- the party list here would act on a different court if it changed between
    -- draw and click, and dropping the offset acts on the wrong party the
    -- moment the grid is paged.
    local slug = (ICUI.court_keys or {})[slot + (ICUI.scroll.court or 0)]
    if not slug then return end
    ICUI.notice = nil
    if ICUI.sel == slug then
        -- THE SECOND CLICK: who is in it. The roster is the one picker that
        -- chooses nothing - its rows report rather than offer - and it was
        -- your own house's alone until the card became the control.
        ICUI.pick = {kind = "house", slug = slug}
        ICUI.scroll.pick = 0
    else
        ICUI.sel = slug
    end
    ICUI.refresh()
end

-- ONE OF THE THREE ACTIONS, against the chosen party. A refused one answers
-- with its reason instead of doing nothing - see draw_actions.
function ICUI.on_act_click(key)
    local faction = ICUI.player()
    if not faction or ICUI.pick then return end
    local slug = ICUI.sel
    local court = IC.court(faction)
    if not slug or slug == IC.CROWN or not court.houses[slug] then return end
    local may, why, target = ICUI.act_check(faction, key, slug)
    if not may then
        ICUI.notice = why
        ICUI.refresh()
        return
    end
    local move = ICUI.ACT_MOVE[key]
    if move.plot then
        -- STRAIGHT TO THE SECOND QUESTION. The party is chosen and the man it
        -- is aimed at is the one who speaks for it, so the only thing left to
        -- ask is who carries it out - the same picker, odds and refusals the
        -- Intrigue tab's moves open.
        ICUI.pick = {kind = "plot", plot = move.plot, key = tostring(target)}
        ICUI.scroll.pick = 0
        ICUI.notice = nil
    else
        local done, reason, spare = IC.favour(faction, move.favour, slug)
        if done then
            ICUI.notice = nil
            ICUI.confirm(nil, true)
        else
            ICUI.notice = ICUI.reason_text(reason, spare)
        end
    end
    ICUI.refresh()
end

function ICUI.toggle()
    if comp(ICUI.PANEL) then ICUI.close() else ICUI.open() end
end

function ICUI.register()
    core:add_listener("ic_click", "ComponentLClickUp", true, function(context)
        local id = context.string
        if id == ICUI.BTN then
            ICUI.toggle()
        elseif id == "ic_close" then
            ICUI.close()
        elseif ICUI.TAB_VIEW[id] and comp(ICUI.PANEL) then
            -- A tab is also how you abandon the picker: it is modal, and a modal
            -- with no way out is worse than no modal.
            ICUI.pick = nil
            ICUI.scroll.pick = 0
            ICUI.notice = nil
            ICUI.view = ICUI.TAB_VIEW[id]
            ICUI.refresh()
        -- A COLUMN'S ARROW. The arrows are hidden on the views and columns
        -- that do not sort, but a hidden component still reports a click if
        -- something else ever shows it - so the guard is in click_column, which
        -- answers false for a column this view has no mode for, rather than in
        -- whether the branch was reached.
        elseif ICUI.HSORT_INDEX[id] and comp(ICUI.PANEL) then
            if ICUI.click_column(ICUI.live_view(), ICUI.HSORT_INDEX[id]) then
                ICUI.refresh()
            end
        elseif id == "ic_page_prev" and comp(ICUI.PANEL) then
            if ICUI.scroll_by(-ICUI.rows_shown(ICUI.live_view())) then ICUI.refresh() end
        elseif id == "ic_page_next" and comp(ICUI.PANEL) then
            if ICUI.scroll_by(ICUI.rows_shown(ICUI.live_view())) then ICUI.refresh() end
        elseif id == "ic_card_button" and comp(ICUI.PANEL) then
            ICUI.on_office_click(context)
        -- THE MOVE CARD'S OWN BUTTON, and it had no branch at all: PLOT did
        -- nothing on screen for a whole build. The plot card began life as a
        -- second pool of instances off derpy_ic_card.twui.xml, where both pools
        -- really would have reported ic_card_button - and then it was given its
        -- own file with its own child names, and this list was never told. The
        -- ui log shows the click arriving at
        -- root > derpy_ic_panel > derpy_ic_plot_10 > ic_plot_go, with no error
        -- and nothing listening.
        elseif id == "ic_plot_go" and comp(ICUI.PANEL) then
            ICUI.on_plot_click(context)
        -- THE PARTY CARD, WHOLE: its own id, or any cell on it that is
        -- interactive for a tooltip and so reports itself instead.
        elseif (ICUI.PARTY_CHILD_XY[id]
                or string.match(id or "", "^" .. ICUI.PARTY .. "_%d+$"))
                and comp(ICUI.PANEL) then
            ICUI.on_party_click(context)
        elseif ICUI.ACT_MOVE[id] and comp(ICUI.PANEL) then
            ICUI.on_act_click(id)
        elseif id == "ic_row_e" and comp(ICUI.PANEL) then
            ICUI.on_row_action(context)
        -- THE SECOND BUTTON EXISTS ONLY ON THE PETITIONS TAB. fill_rows hides it
        -- everywhere else, and a hidden button cannot be clicked.
        elseif id == "ic_row_f" and comp(ICUI.PANEL) then
            if ICUI.live_view() == "petitions" then
                ICUI.on_petition_click(context, false)
            end
        end
    end, true)
end

cm:add_first_tick_callback(function()
    ICUI.register()
    ICUI.place_opener(1)
end)

-- A SECOND CHANCE, EVERY TURN. BTN_TRIES x the 1s delay is a 12 second window
-- after first tick, and nothing re-opened it - so a HUD that was still building
-- (intro cutscene, slow load) left the campaign with no way into the court at
-- all. The Great Guilds, the precedent whose button is on screen, re-enters its
-- chain here for exactly this reason. place_opener is idempotent: it reuses the
-- existing component, recomputes the anchor, and now only logs when the button
-- actually moves.
core:add_listener("ic_opener_place", "FactionTurnStart", true, function()
    ICUI.place_opener(1)
end, true)

-- ---------------------------------------------------------------------------
-- The standing plate's three triggers.
--
-- WHO, then WHERE, then HOW MUCH - and all three can move without the other two
-- doing anything, so each gets its own.
-- ---------------------------------------------------------------------------

-- WHO. The only thing that says whose panel is about to open. It fires BEFORE
-- the panel exists, so this records the man and does not try to draw: the panel
-- event below is what draws.
core:add_listener("ic_char_selected", "CharacterSelected", true, function(context)
    local character = context:character()
    if not character or character:is_null_interface() then
        ICUI.selected_cqi = nil
        return
    end
    ICUI.selected_cqi = character:command_queue_index()
end, true)

-- WHERE. PanelOpenedCampaign fires for EVERY panel, so the name test is not
-- optional - without it this runs on the settlement panel, the diplomacy screen
-- and everything else, looking for an anchor that is not there.
--
-- ONE TICK LATER. The panel exists when this fires but its children have not
-- settled, so dy_rank's position is read mid-layout - the same fault that once
-- put the opener 133px off its slot. A callback of 0 puts the read after the
-- layout pass rather than inside it.
core:add_listener("ic_char_panel", "PanelOpenedCampaign", true, function(context)
    if context.string ~= ICUI.STANDING_PANEL then return end
    cm:callback(function() ICUI.show_standing() end, 0)
end, true)

core:add_listener("ic_char_panel_shut", "PanelClosedCampaign", true, function(context)
    if context.string ~= ICUI.STANDING_PANEL then return end
    ICUI.selected_cqi = nil
    ICUI.show_standing()
end, true)

-- HOW MUCH. A man's standing moves at every turn start - income, and whatever he
-- won in the field - so a plate left up across one would keep showing last
-- turn's figure.
core:add_listener("ic_standing_refresh", "FactionTurnStart", true, function()
    ICUI.show_standing()
end, true)

-- ---------------------------------------------------------------------------
-- THE SCREEN'S SHARE OF THE LAYOUT.
--
-- Every layout number in this file is typed for a 1920x1080 box. ICUI.open fits
-- the box to the screen - the widest 16:9 rectangle it holds, 1600 to 2560 -
-- and apply_scale rebuilds every scaled value from BASE for that box, so a
-- second open at another size never scales an already scaled number. Below
-- 1920 the panel is also built from the compact copies of its five files, one
-- font size down, because text shrinks by a font step while boxes shrink by
-- the box.
--
-- THE RULE IS sc() AND sc_box() IN tools/gen_ic_ui.py, in integers, and the
-- packing gate runs this apply_scale against the generator's at_box() at three
-- widths. Game Lua is float32; every product here is under 2^24, so each one
-- is exact and the floor lands where Python's // does. A cell scales by its
-- EDGES rather than its size, so two cells that touch at 1920 still touch at
-- every width. See docs/superpowers/specs/2026-09-24-iron-court-ui-scale-design.md.
-- ---------------------------------------------------------------------------
ICUI.BW = 1920
ICUI.COMPACT = false

function ICUI.sc(v)
    return math.floor((v * ICUI.BW + 960) / 1920)
end

-- THE BOX FOR A SCREEN. CA floors the screen a script sees at 1600x900, so the
-- bottom clamp is theirs; the top one is ours - past 2560 the rows would only
-- get taller, and the ground either side is the better use of the width.
function ICUI.box_for(sw, sh)
    local bw = math.floor(math.min(sw or 0, (sh or 0) * 16 / 9))
    if bw < 1600 then bw = 1600 elseif bw > 2560 then bw = 2560 end
    return bw, math.floor(bw * 9 / 16)
end

-- AN OVERRIDE'S SHARE at the current box: all of it at 1600, none from 1920.
function ICUI.fade(d)
    if ICUI.BW >= 1920 then return 0 end
    return math.floor((d * (1920 - ICUI.BW) + 160) / 320)
end

-- ONE CELL, BY ITS EDGES, plus its faded override. A square cell stays square:
-- a flag drawn into a 14x13 cell is a squashed flag.
function ICUI.sc_box(b, over)
    local x, y = ICUI.sc(b[1]), ICUI.sc(b[2])
    local w = ICUI.sc(b[1] + b[3]) - x
    local h = ICUI.sc(b[2] + b[4]) - y
    if b[3] == b[4] then
        w = math.min(w, h)
        h = w
    end
    if over then
        x = x + ICUI.fade(over[1])
        y = y + ICUI.fade(over[2])
        w = w + ICUI.fade(over[3])
        h = h + ICUI.fade(over[4])
    end
    return {x, y, w, h}
end

-- WHAT apply_scale REBUILDS, and what it leaves alone on purpose. A layout
-- number in none of these lists keeps its 1920 size on a 1600 screen with
-- every check green, which is why the harness refuses one.
ICUI.SCALED = {
    "ROWS_X", "ROWS_Y", "ROW_PITCH", "ROW_W", "ROW_H", "HDR_GAP", "HDR_Y",
    "DIAL_R", "DIAL_CX", "DIAL_CY", "CREST_R", "CREST_PX", "SHARE_R", "SHARE_W",
    "SHARE_H", "PORT_W", "PORT_H", "CREST_W", "CREST_H",
    "CARDS_X", "CARDS_Y", "CARD_GAP_X", "CARD_GAP_Y", "CARD_W", "CARD_H", "CONTENT_W",
    "PLOTS_X", "PLOTS_HDR_Y", "PLOTS_HDR_H", "PLOTS_Y", "PLOT_W", "PLOT_H",
    "PLOT_PAD", "PLOT_FOOT_PAD", "PLOT_ICON_PX", "PLOT_INNER_W",
    "PARTY_GAP_X", "PARTY_GAP_Y", "PARTY_W", "PARTY_H", "PARTIES_X", "PARTIES_Y",
}
-- A cell by name is {x, y, w, h} and scales by its edges. A grid point is
-- {x, y} and scales per coordinate: a card width rounded down once and
-- multiplied by five ran a tier past its column at some widths.
ICUI.SCALED_TABLES = {
    "PANEL_XY", "ROW_CHILD_XY", "CARD_CHILD_XY", "PARTY_CHILD_XY", "PLOT_CHILD_XY",
    "CARD_XY", "PARTY_XY", "PLOT_XY", "COURT_SECTION_XY", "ACT_PAGED_XY",
}
-- Rebuilt from the scaled cells rather than scaled on their own, so they cannot
-- disagree with the cells they describe.
ICUI.DERIVED = {
    "COL_WH", "COL_W", "CARD_CREST", "PARTY_CREST", "HSORT_DY",
    "SHARE_MIN_SLICES", "CREST_MIN_SLICES",
}
-- Counts and indices, SORTS' column numbers among them; the opener and the
-- standing line, which are not in the box; this block's own state; SHARE_INK,
-- which is how wide a figure DRAWS - the font decides that, and no font grows
-- past 1920; and HSORT_GAP, which mirrors the twui text inset LABEL_TX, the
-- same at every size.
ICUI.NOT_SCALED = {
    "BTN_SIZE", "BTN_GAP", "BTN_TRIES", "DIAL_SLICES", "MAX_ROWS", "MAX_HOUSES",
    "PLATE_INDEX", "FACE_INDEX", "MASK_INDEX", "OX", "OY", "PLOT_COLS",
    "PLOT_COUNTS", "PLOT_DEPTH", "PLOT_BLURB_LINES", "PARTY_COLS", "PARTY_ROWS",
    "PARTY_SLOTS", "STANDING_W", "STANDING_H", "STANDING_DX", "STANDING_DY",
    "SHARE_INK", "HSORT_GAP", "HSORT_INDEX", "PULSE_SECONDS", "PULSE_STRENGTH",
    "TIP_PROVINCES", "SORTS", "BW", "BASE", "COMPACT_OVERRIDES",
    "PARTY_SEL_INDEX",
}

-- PER-CELL CORRECTIONS AT THE SMALL END, in pixels at a 1600 box, faded to
-- nothing at 1920. Must match COMPACT_OVERRIDES in tools/gen_ic_ui.py, which
-- names the string that forced each one; the packing gate compares them.
ICUI.COMPACT_OVERRIDES = {
    ic_card_name = {-1, 0, 2, 0},
    ic_plot_icon = {-5, 0, 0, 0},
    ic_plot_name = {-5, 0, 10, 0},
    ic_plot_b1   = {-5, 0, 10, 0},
    ic_plot_b2   = {-5, 0, 10, 0},
    ic_plot_b3   = {-5, 0, 10, 0},
    ic_plot_b4   = {-5, 0, 10, 0},
    ic_plot_cost = {-5, 0, 0, 0},
    ic_plot_go   = {5, 0, 0, 0},
    ic_row_a     = {0, 0, 6, 0},
    ic_row_d     = {-4, 0, 24, 0},
    ic_hdr_d     = {-4, 0, 0, 0},
    ic_hsort_d   = {-4, 0, 0, 0},
    ic_row_e     = {7, 0, 2, 0},
    ic_hdr_e     = {7, 0, 0, 0},
    ic_hsort_e   = {7, 0, 0, 0},
}

-- THE FILES THAT HAVE A COMPACT COPY: the five in the box.
ICUI.HAS_COMPACT = {
    [ICUI.PATH_PANEL] = true, [ICUI.PATH_ROW] = true, [ICUI.PATH_CARD] = true,
    [ICUI.PATH_PARTY] = true, [ICUI.PATH_PLOT] = true,
}
function ICUI.path(p)
    if ICUI.COMPACT and ICUI.HAS_COMPACT[p] then return p .. "_compact" end
    return p
end

-- THE 1920 LAYOUT, as typed, taken once at load. Everything apply_scale writes
-- is computed from here and never from its own last answer.
local function copy_table(t)
    local out = {}
    for k, v in pairs(t) do
        if type(v) == "table" then out[k] = copy_table(v) else out[k] = v end
    end
    return out
end
ICUI.BASE = {}
for _, list in ipairs({ICUI.SCALED, ICUI.SCALED_TABLES, ICUI.DERIVED}) do
    for _, n in ipairs(list) do
        local v = ICUI[n]
        if type(v) == "table" then v = copy_table(v) end
        ICUI.BASE[n] = v
    end
end

function ICUI.apply_scale(bw)
    ICUI.BW = bw
    ICUI.COMPACT = bw < 1920
    local over = ICUI.COMPACT_OVERRIDES
    for _, n in ipairs(ICUI.SCALED) do
        local d = over[n]
        ICUI[n] = ICUI.sc(ICUI.BASE[n]) + (type(d) == "number" and ICUI.fade(d) or 0)
    end
    for _, n in ipairs(ICUI.SCALED_TABLES) do
        local base = ICUI.BASE[n]
        if type(base[1]) == "number" then
            ICUI[n] = ICUI.sc_box(base, nil)
        else
            -- IN PLACE, so nothing holding the table holds a stale one.
            local t = ICUI[n]
            for k, b in pairs(base) do
                if #b == 4 then
                    t[k] = ICUI.sc_box(b, over[k])
                else
                    t[k] = {ICUI.sc(b[1]), ICUI.sc(b[2])}
                end
            end
        end
    end
    -- THE DERIVED ONES. A column's default size is its cell's; a per-view width
    -- ends where it ended at 1920, scaled by the same edge rule as a cell.
    for j, key in ipairs(ICUI.ROW_KEYS) do
        local cell = ICUI.ROW_CHILD_XY[key]
        ICUI.COL_WH[j] = {cell[3], cell[4]}
    end
    for view, widths in pairs(ICUI.BASE.COL_W) do
        for j, w in pairs(widths) do
            local x = ICUI.BASE.ROW_CHILD_XY[ICUI.ROW_KEYS[j]][1]
            ICUI.COL_W[view][j] = ICUI.sc(x + w) - ICUI.sc(x)
        end
    end
    ICUI.CARD_CREST = ICUI.CARD_CHILD_XY.ic_card_crest[3]
    ICUI.PARTY_CREST = ICUI.PARTY_CHILD_XY.ic_party_crest[3]
    ICUI.HSORT_DY = ICUI.PANEL_XY.ic_hsort_a[2] - ICUI.PANEL_XY.ic_hdr_a[2]
    ICUI.SHARE_MIN_SLICES = ICUI.min_slices(ICUI.SHARE_R, ICUI.SHARE_INK)
    ICUI.CREST_MIN_SLICES = ICUI.min_slices(ICUI.CREST_R, ICUI.CREST_PX)
end
