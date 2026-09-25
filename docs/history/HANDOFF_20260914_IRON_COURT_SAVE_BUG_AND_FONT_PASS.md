# Iron Court — the save-load bug, and the panel's font pass

2026-09-14, continued 2026-09-15. Two pieces of work, **both now packed and deployed**.

The first found and fixed the reason **offices, governors and standing vanished one turn
after they were set**. The second unified the panel's text sizes and, in verifying it, found
that the build gate had been measuring text ~19% narrower than the engine draws it for as
long as it has existed.

---

## 0. Read this first

- **The deployed pack contains both halves.** `data/derpy_iron_court.pack`, 2026-09-15
  08:00, 1676 files, sha256 `04EA554B8842C628...`, and `used_mods.txt` has it ticked.
  `Modding Files/Modpacks/derpy_iron_court.pack` is the same bytes.
- **Nothing here has been seen in game.** Every claim below is from an offline instrument
  or from the game's own `script_log` written before the fix. The font work in particular
  has never been drawn by the engine — only by `preview_iron_court.py`, which measures with
  a desktop face and a proxy factor.
- **The Iron Court is not a published Workshop item**, so `data/` is the load route rather
  than a working copy. The usual "Workshop is the live copy" rule does not bite here yet.
- The author's two design decisions in §5 are recorded verbatim in that section. They were
  put to them with measurements, not opinions, and they chose the option that keeps the
  court unchanged.

---

## 1. The bug: `string.find`'s third argument silently returns nil in WH3

`IC.unpack` walked the save string like this:

```lua
local at = string.find(packed, "%|", from)
```

**In WH3 that call finds nothing.** It is the same engine-modified `string` subsystem whose
fourth (`plain`) argument corrupts strings process-wide — the third (`init`) argument does
not error, does not warn, and returns nil. So `find` never matched, the whole packed string
became field 1, and every section after the first `|` came back empty. **Every load. Every
faction. Since the save format shipped.**

Treat WH3's `string.find` as **two-argument only.**

The fix is the field-walk idiom that has no init argument at all:

```lua
for field in string.gmatch(packed .. "|", "([^|]*)|") do
    fields[#fields + 1] = field
end
```

`([^|]*)` and not `([^|]+)`: the plus form **eats empty fields** and shifts every section
after the first gap. The trailing `.. "|"` is what makes the last field terminate.

### How it was diagnosed, with the game shut

From the save strings in `script_log_140926_2057.txt` and `_2213.txt`, cross-read against
the shipped Lua. Four independent tells, all of which only the truncation explains:

| Tell | What it means |
|---|---|
| Houses parsed and drifted; nothing after them ever did | the break is at the first `\|` |
| Standing sat at exactly one trickle (`1693,2`) forever | the standing section was never read back |
| Province loyalty stuck at `prov_loyalty_start - 1` = 59 turn after turn | ditto |
| The record was empty after a turn that had logged to it | ditto |
| The legion's 13th field came back `0` | the junk tail `0\|\|\|\|1693` lands exactly where `tonumber` drops it |

The round trip was proven correct in a probe, the deployed pack was diffed against the
staged file, and there were no duplicate packs. The only remaining difference between the
harness (which passed) and the game (which did not) was **the Lua implementation itself** —
which is what pointed at `string.find`.

**The existing save is compatible.** Its four real strings were run through the fixed
`unpack`. Offices and the governor are simply *absent* from it, because they were never
written back — they need re-appointing once.

### Why the harness could not have caught it

`tools/_iron_court_harness.lua` runs under stock Lua 5.1.5, where `string.find`'s init
argument works. A harness check written for this bug **passed on the broken code**. That is
not a harness fault; it is the boundary of what a stock-Lua harness can see.

The instrument that *can* see it is a static one:

**`tools/check_lua_api.py` gained a `find-init` rule.** `_has_init()` mirrors the existing
`_plain_flag()` with `want = 3 if dotted else 2`. Verified against the broken copy
(reports `deployed_model.lua:920`) and the fix (clean). Selftest cases 5/6/7 flipped from
clean to findings; case 8 (`string.find(s, "%|")`) added as clean.

Both traps are now in memory: `wh3-string-find-init-finds-nothing.md` and
`wh3-string-find-plain-flag-corrupts-strings.md`, cross-linked.

---

## 2. Two more model faults found in the same pass

**A record entry aimed at nobody was written as an empty field.** `IC.log` passed
`against or ""`, and `pack`'s `split` on `","` **drops empty pieces** — so the entry came
back four fields long and was discarded on load. Fixed to `nil`, which makes `pack` write
`-`. This is why an absent field is `-` and never `""` anywhere in the save format.

**`IC.stamp_incoming` branded every unstamped man in the faction, not just arrivals.**
`force_confederation` is asynchronous (the absorbed faction's characters appear ~10s later),
so the poll re-walks `faction:character_list()` — which is *all* characters, including ones
not on the map. It now takes a `before` snapshot of `command_queue_index()` in the
`ic_confed` listener and skips anyone already present.

Both are pinned by new harness checks and by three new mutants. **36 mutants, 0 unexplained.**

---

## 3. The font pass: two sizes for the whole panel

The author's words were *"texts are also too small, make a unified title size and content
size"* and *"theres no proper scaling of fonts"*. They chose **Title 20 bold / content 18**.

```python
TITLE = (20, "header_20_bold")         # every heading and every card's name
BODY  = (18, "header_18")              # every line of content, everywhere
PANEL_TITLE = (24, "header_24_bold")   # the panel's own name, once
```

It used to be five sizes — 24, 18, 16, 14, 12 — picked cell by cell as each was built.

**`TEXT_STYLE` now lists only headings**, and everything else falls through to `BODY`. That
is the right default and was not the old one: `ic_plotcat_1..4` were in *no* list and drew
the intrigue tab's four column headings at content size.

**Content is `header_18` and not a body face because it cannot be one.** The engine's body
family is 10, 12 and 16 and **stops there**. Anything larger must come from the header
family; `header_18` is the largest non-bold face in it. The real vocabulary is:

```
body_10 body_12 body_16 body_12_bold body_12_italic body_alternative_12
header_12 header_14 header_16 header_18 header_20_bold header_24_bold
header_16_bold header_18_bold header_alternative_18
```

An unknown fontcat is **not an error** — the engine falls back silently.

The Crown's box was **stacked** rather than split into two halves side by side: at the new
content size the control sentence wanted 399px of the 372 the left half had, and the Crown's
party name wanted 350 of the 275 beside his portrait. Neither half could grow without taking
it from the other.

---

## 4. The finding that came out of verifying it: the gate under-measured the engine by 19%

The preview cut several move blurbs mid-sentence **while `gen_ic_ui.py --check` passed**.
Chasing that turned up two separate faults and then a third that matters much more:

1. The preview drew with `ImageFont.load_default()` while the generator measured with
   `seguibl.ttf`. Fixed — the preview now resolves the same face.
2. `GAME_FONT_WIDER = 1.33` in the preview had been measured against PIL's **default** face,
   so once the face changed it double-counted.
3. **`gen_ic_ui._measure` applied no factor at all.**

Measured against one string: PIL default 834px, `seguibl.ttf` 930 (1.115x), `segoeui.ttf`
816, `arial.ttf` 821. The engine, from the 2026-09-13 screenshot measurement, is ~1.33x PIL
default = 1109 → **~1.19x seguibl**.

So the build gate had been measuring **19% narrow**, in the dangerous direction: it passes a
string the engine then cuts. There is now **one constant**, in the generator, and the preview
imports it:

```python
GAME_FONT_WIDER = 1.19
```

It is a proxy and is documented as one — the engine's own figure is
`TextDimensionsForText` and needs the game running. It is deliberately the pessimistic side.

### What the corrected measurement reported

**17 clips the old measurement passed.** Ten were fixable in layout and are fixed:

| Cell | Was | Now |
|---|---|---|
| six move blurbs | needed a 4th line, had 3 | `PLOT_BLURB_LINES = 4`, paid for out of `PLOT_FOOT_PAD` 16 -> 10 and the blurb start 72 -> 68. The card is derived from the deepest column and cannot grow. |
| `ic_card_button` | "APPOINT" 100px in 84 | row re-split; the price was using 159 of its 200 |
| `ic_party_off` | "14 seats at court" 173 in 164 | widened out of the mood button's slack |

The other seven needed a decision — §5.

---

## 5. The two decisions the author made

### The office card: **"Leave the court alone"**

The office card is **364x184, and neither number is ours**: fourteen seats whose widest band
is five sets the width, four bands set the height. At 20/18 it needed roughly 393x190.

| | needs | has |
|---|---|---|
| "Warden of the Caravan Roads" @20 | 352px | 298px |
| "4000 standing - 99 turns left" @18 | 304px | 298px |
| "Armaments +15%, Raw Materials +12%" @18 | 416px | 298px |
| the five rows of cells @18 | ~160px | 124px |

Three alternatives were offered with those numbers — 3 bands of 4/5/5 (364x250), 4 bands of
2/4/4/4 (459x184), or 12 seats in 3 bands of 4 (459x250). **All three reshape the court**,
and the author declined. So:

**The office card is the panel's one exception, whole.** Each of its five text cells now
carries the largest face that fits *its own cell*, measured against the widest string the
model can put in it:

```
ic_card_name    "Warden of the Caravan Roads"          276 of 298   header_16
ic_card_term    "4000 standing - 99 turns left"        268 of 298   header_16
ic_card_effect  "Armaments +15%, Raw Materials +12%"   277 of 298   body_12
ic_card_need    "[icon]4000 / lvl 30"                  102 of 106   body_12
ic_card_button  "APPOINT"                               66 of  68   body_12
```

To get there the card's rows were **re-dealt**. Three cells need the full width and the card
has exactly three rows that can give it — the name at the top, the strip under the face, and
the effect line at the floor. The strip under the face was empty; **the term goes in it**,
because the term is the string with no other home (at 190px it fits at no readable size).
The price and its button take the term's old place beside the face, split **74/112** rather
than 90/96 — the wide half goes to the price, which is the opposite of the old split and is
why the price was clipping.

The two `body_12` cells beside the face are tight because they are beside the face. The next
step down is `body_10`, which is the size this whole pass set out to remove.

### The party card's leader line: **"Cut it with an ellipsis"**

`ic_party_leader` is 281px beside a 100px face on a card packed to its own floor, against a
331px worst-case rolled name. The alternatives were that one cell at 14, or a fit with zero
pixels to spare. Cutting won, so **the panel keeps one content size everywhere.**

New `ICUI.fit_cut(c, text)` — the third of the family beside `fit_two` and `fit_lines`, and
the only one that loses text on purpose. Measured with `TextDimensionsForText`, words first,
**and the ellipsis is measured before the test**, not appended after, or the three dots are
exactly what overruns.

**It parts company with `fit_two` on one rule and has to.** `fit_two` keeps a first word too
wide for line one because there is a line two behind it; this cell has nothing behind it, so
keeping the word would put the overrun straight back — the thing the cut exists to prevent.
When no whole word fits, `fit_cut` falls back to characters, always keeping at least one.

---

## 6. Two checks that could not have failed

Both were found by running the instruments, not by reading them.

### `check_plot_cells()` was never called by anything

It has existed since the move card was built. The comment above `PLOT_FOOT_PAD` says it
*"refuses any overlap now, so this cannot come back"*. **Nothing in any file ever called it.**
It could refuse nothing.

It is now `check_card_cells(layout, w, h, what)` and runs as **check 19z** against all three
card shapes — office, party and move; none of the other two ever had one. It immediately
caught a fault introduced earlier in this same session: moving the term line to full width
had put it **straight through the portrait**, which every frame-band check passes cleanly.

`CELL_OVERLAP_OK` is there for pairs that are *meant* to stack. It is currently empty, by
design: a pair in it is a decision somebody wrote down.

### The `CUT_CELLS` exemption is paid for

`CUT_CELLS = {"ic_party_leader": "ICUI.fit_cut"}` lets one cell past the clip measurement.
An exemption that only silences a check is how a clip ships with a green build behind it, so
**check 20h** asserts the panel Lua both declares that helper and calls it on that cell.

**Its first version was too weak and a mutant proved it.** `"function " + _fn not in src` is
a substring test, and renaming the helper to `ICUI.fit_cutx` still contains
`function ICUI.fit_cut` — the mutant survived. It is now a regex with the open bracket as the
boundary, and both mutants (call site removed, helper renamed) are caught.

### And one fixture that was faking a mechanism

The harness's fake component tree gives every cell `w = 10`, so `fit_cut` cut every name on
every card to its first word and an existing check failed. **The fixture, not the
assertion.** `ic_party_leader` now gets its real width in the fake tree — the same idiom the
plot blurb cells already use — derived from two numbers the panel already declares rather
than typed as a third copy of 287:

```lua
c.w = ICUI.PARTY_W - ICUI.PARTY_CHILD_XY.ic_party_leader[1]
      - ICUI.PARTY_CHILD_XY.ic_party_crest[1]
```

The crest's x **is** the card's frame band, which is why that works.

`make_ic_backdrop.py` closed a related gap: which cells get measured for contrast is now
**derived**, not typed — `ic_plotcat_1..4` are built in a loop off `PLOT_COLS` and no typed
list ever had them, so for the whole life of the intrigue tab its headings drew on bare
backdrop unmeasured. A guard now asserts every `TITLE`-styled cell is measured. 82 -> 85
cells, worst ratio 4.6:1 against a 4.5:1 threshold.

---

## 7. Verification state

Run at the end of the session, on the staged files.

| Instrument | Result |
|---|---|
| `gen_ic_ui.py --check` | **ok: 7 files, 219 components** |
| `gen_ic_ui.py --selftest` | **ok (7 files, 219 components, 801 guids)** |
| `_iron_court_harness.lua` | **ok (327 checks)** |
| `mutate_iron_court.py` | **36 mutants, 0 unexplained** |
| `preview_iron_court.py --selftest` | **ok**, repaired 2026-09-15 - see section 7b |
| `import_iron_court.py --check` | **exit 0** |
| `make_ic_backdrop.py --check` | **exit 0**, worst 4.6:1 |
| `check_lua_api.py` | 0 suspect calls on the panel Lua |
| `check_lua_undeclared.py` | 12 files, 0 undeclared |
| `luac -p` | both Lua files parse |

Every instrument above has now seen this exact state. The mutation table was re-run on
2026-09-15 and all 36 are caught.

**Two `gen_ic_ui.py --selftest` runs at once produce exit 4 and NO output.** That happened
here and was briefly mistaken for a failure. The selftest writes files and injects faults
into them, so two instances fight over the same tree — the same hazard already written down
for `mutate_iron_court.py`, and it applies to the generator selftest too. Run it alone. It
takes over two minutes, so the temptation to background it and start something else is
exactly the trap.

---

## 7b. The preview harness, repaired (2026-09-15)

`tools/preview_iron_court.py --selftest` had been broken for some time and is the instrument
that would have said so. It took **four** failures to get it green, and every one was the
same fault wearing a different hat: **a thing grew and its readers went on reading the old
shape.**

1. `GAME_FONT_WIDER = G.GAME_FONT_WIDER` at module level, where `G` is a local built inside
   `draw()`. It could never have run. `_gen()` is now cached and the constant resolves at
   import — caching matters because `module_from_spec` builds a **new** module every call,
   so an uncached second call re-executes the generator and hands back different layout
   tables.
2. `read_plots()` returns seven fields and the selftest unpacked five. It is a
   **`collections.namedtuple`** now (`Move`), so it still indexes for `p[0]` and the next
   field cannot break a reader that spells the arity out.
3. `plot_cards()` had the identical fault one function over — four fields in its docstring,
   six returned. Also a namedtuple now (`Card`).
4. Three assertions written when Intrigue was a **row list**. It is four columns of cards;
   `ICUI.rows_shown("intrigue")` has returned 0 since. `intrigue_lines()` was correctly
   repurposed to feed the alert bar and its docstring still claimed "three warnings plus
   nine moves is exactly ICUI.MAX_ROWS".

**Re-aimed, not deleted.** The price-markup check moved to where the prices moved — the
cards' third cell — because the property it guards is real: `segments()` must split
`[[img:]]` and `[[col:red]]` apart or the panel prints the tags.

### The purses, re-picked

`DEMO_PURSE, DEMO_PURSE_CIVIL` were **250 and 90**, chosen when the tab held nine moves and
Errands held two. Errands is four now, so 90 bought **one** of them and that column drew
almost uniformly red — which says as little as no red at all. The aimed half had drifted the
other way: 250 refused only the purge, one row in twelve.

They are **155 and 105**, each about the middle of their own list:

```
aimed   80 90 120 130 140 150 | 160 180 200 220 250 400     6 of 12 refused
errand  60 100 | 110 140                                    2 of 4  refused
```

**They stay literals deliberately.** Deriving them from the price list — the median, say —
would make the straddle assertion true by construction, and a check that cannot fail is the
thing this file exists to avoid.

The two stale count-assertions are now stated as invariants that cannot go stale again:

- the unaimed moves are **exactly one category**, and that category holds nothing else
  (it counted to two before);
- each purse **straddles** its own list — at least one refused and at least one affordable
  (it asserted "fewer than two red errands" before, which was an accident of there being two).

Both pictures were rendered and read: the Intrigue tab now shows a real mix of affordable
and refused, and every blurb lands complete inside its card at the new content size.

---

## 8. Open

**Packed and deployed, 2026-09-15 08:00.** See §8c for how, and for the two things
that cost time.

**What has never been done: play a turn.** Everything in this document is an offline claim.
The first thing to check in game is the one the save bug was about — appoint an officeholder
and a governor, end the turn, and confirm they are still there. They will need re-appointing
once regardless, because the old save never wrote them back.

### 8b. Unresolved, and it needs the running game

Two characters the author assigned as governors — **Kullani Growlish (cqi 3083)** and
**Jarthrazz Oathkiller (cqi 2233)** — appear nowhere in their army list. What is established:

- both are in the player's `faction:character_list()`, which is *"All characters in this
  faction"* and **includes characters not on the map**;
- neither ever receives a stance trait, and CA applies those via
  `cm:char_is_general_with_army` — so neither commands an army;
- both read `(away)` permanently, meaning `has_region()` is false;
- compare **Warrhak Skullcrusher (3084)**, the one *not* away, who picks up
  `wh2_main_trait_stance_recruiting` three times.

Most likely they are **recruitment-pool characters**. A wounded lord would look identical
from script, and **the recruitment pool cannot be read** — there is no CCO and no faction
accessor; `cm:spawn_character_to_pool` only writes.

**The wh3 MCP bridge was not connected in that session**, so the live game could not be
asked. It is the way to settle this.

A filter was **proposed and not approved, so not implemented**: a man with **neither**
`has_region()` nor `has_military_force()` is not on the map and can never govern. That
excludes pool and wounded characters while still allowing a general at sea and a courtier
sitting in a settlement.

### 8c. How it was packed, 2026-09-15

**The registered `mcp__rpfm__*` tools were NOT available**, and opening RPFM did not bring
them back: the MCP client binds at session start, and RPFM was launched after. `ToolSearch`
kept answering "no match" while `/sessions` answered HTTP 200. The route is the documented
fallback - raw JSON-RPC against `http://127.0.0.1:45127/mcp`, one `mcp-session-id` reused
across calls. Three things it has to get right, all of them already in the
`rpfm-mcp-over-raw-http` memory: responses are **SSE**, so take the LAST `data: {` line;
state is **per-MCP-session**, so the whole job runs in one process or the unsaved adds are
lost; and pack paths take forward slashes.

`add_packed_files` wants `destination_paths` as a **JSON string** holding a `Vec<ContainerPath>`
- `[{"File": "ui/campaign ui/derpy_ic_card.twui.xml"}]` - positionally matched to
`source_paths`. It replaces in place: the path stays, the timestamp moves, the file count
does not.

**Only seven files actually differed**, and they were found by byte-comparing every file the
generator owns against the pack with `read_pack_index.py` rather than by trusting mtimes.
That mattered twice:

- `zzz_derpy_iron_court.lua` had a **newer mtime and identical bytes** - `mutate_iron_court.py`
  rewrites the shipped Lua and restores it in a `finally`, which moves the timestamp. Packing
  by mtime would have added 1,667 files to say nothing.
- `zzz_derpy_guilds.lua` sits in the same staged tree and belongs to **a different mod**. A
  folder-level add would have pulled it in.

The seven: `zzz_derpy_iron_court_ui.lua` and six of the seven `.twui.xml` files.
`derpy_ic_opener.twui.xml` was unchanged - the opener button carries no text this pass
touched.

**The save was verified by re-reading the file off disk** with `read_pack_index.py`, which
has never spoken to RPFM: 1676 files before and after, 0 still differing. A save that
reports OK and writes the old content is a real failure mode, and RPFM's own answer cannot
rule it out.

---

---

## 9. Things worth carrying to other work

- **WH3's `string.find` is not stock Lua's.** Its 4th argument corrupts the string subsystem
  process-wide; its 3rd **silently returns nil**. Two-argument only.
- **A stock-Lua harness cannot see an engine-modified stdlib.** When a check passes on code
  the game is demonstrably breaking on, that gap is the finding.
- **twui text never wraps.** More lines means more *components*. `texthbehaviour="Never
  split"` is on every emitted cell deliberately: of the three values twui has, "Resize"
  breaks to one word per line and draws outside the declared height.
- **Font categories are a fixed vocabulary, and the body family stops at 16.** An unknown
  fontcat falls back silently.
- **A measurement proxy must state which face it was measured against.** 1.33 against PIL's
  default and 1.19 against Segoe UI Black are the same measurement, and keeping both as
  separate constants is how they drift.
- **`SetImagePath(path, slot)` makes the image take the CELL's shape**, so a portrait cell
  more than ~6% off `300/164` visibly stretches a face (check 8c).
- **Our `.twui.xml` files carry no offsets.** The engine ignores them on a runtime-created
  component, so the Lua `MoveTo`s everything. Coordinates live in `gen_ic_ui.py` and are
  mirrored in the Lua; `import_iron_court.py --check` compares them position by position and
  refuses on drift. It did, twice, during this session.
