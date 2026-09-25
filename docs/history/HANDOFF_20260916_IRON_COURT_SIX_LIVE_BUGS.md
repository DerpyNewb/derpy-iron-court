# The Iron Court - six bugs reported from play, all six fixed

2026-09-16. Six reports off a live session, diagnosed against the script log and the shipped
Lua, fixed, and gated. One was a real layout defect with a provable cause; four were the same
missing feature seen from four angles; one was a text problem.

---

## 0. Read first

- **The script log is clean.** `script_log_150926_2148.txt`, the 21:48-23:31 session, 5MB,
  **zero `SCRIPT ERROR` blocks and zero errors naming the court**. Nothing threw. The save fix
  from 2026-09-14 is holding. So none of the six was a script fault.
- **Nothing here has been seen in game.** Every claim below comes from an offline instrument.
- **The one thing that cannot be checked offline** is whether the two Wwise sound event names
  in `ICUI.SOUND_OK` / `ICUI.SOUND_BAD` are triggerable from script. They are lifted from
  vanilla's own `event_feed_message_events.sound_event` column, so they are real event names;
  if the engine refuses them from `common.trigger_soundevent` the result is silence, and the
  pulse still plays. It cannot fail worse than that.

---

## 1. The vacancy line that drew outside its own card (report 5)

**"seat vacant is permeating through the card when assigning and kicking out officers."**

Real, and the cause is arithmetic rather than opinion.

`ICUI.CARD_TEXT_KEYS` lists the cells `reflow_card` shifts left when an office has no portrait
to shift around. The font pass of 2026-09-14 re-dealt the office card and **did not update that
list**. The rule it encodes is the portrait's y band - the face occupies y 54..112, so a cell
shifts exactly when its own band overlaps that:

| cell | y band | beside the face | was on the list |
|---|---|---|---|
| ic_card_holder | 52-72 | yes | yes |
| ic_card_crest | 74-90 | yes | yes |
| ic_card_house | 74-90 | yes | yes |
| ic_card_button | 90-112 | yes | yes |
| **ic_card_need** | 90-112 | yes | **no - missing** |
| **ic_card_term** | 114-132 | **no, below it** | **yes - wrong** |
| ic_card_effect | 136-154 | no | no |

`reflow_card` shifts by `CARD_BARE_X - CARD_CHILD_XY.ic_card_holder[1]` = `30 - 144` = **-114**.
`ic_card_term` already sits at x=30, so a vacant seat moved it to **x = -84**: eighty-four
pixels off the left edge of its own card, across the card beside it. On a vacant seat
`ic_card_term` holds the string **"Seat is vacant"**. That is the text the player watched bleed
through, and it appeared and vanished exactly when a seat changed hands.

The other half: `ic_card_need` - the influence and level requirement, the cell that matters most
on an empty seat and the one painted red when it is out of reach - was **not** on the list, so it
stranded at x=222 while the APPOINT button beside it jumped to 30.

**Why nothing caught it.** 8b compares where a cell SITS, position by position, in both files.
Check 19z refuses overlaps in the static layout. **Neither knows `reflow_card` exists.** The
reflowed positions had never been measured by anything - the same shape as `check_plot_cells`
being defined, self-documented and called by nothing.

**Fixed** in `zzz_derpy_iron_court_ui.lua`, and **check 8b2** in `import_iron_court.py` now
derives the shift set from `CARD_LAYOUT`'s portrait band and refuses on any difference, reading
`ICUI.CARD_BARE_X` out of the Lua rather than assuming 30. Watched failing on the shipped list:
it reports both halves and names x=-84.

---

## 2. The court ran in silence (reports 1, 3, 4 and 6)

Four reports, one root cause:

```
grep -c show_message_event  ->  0   (both files)
grep PlaySound|TriggerAnimation|pulse  ->  no hits
```

`IC.log` writes into a **40-entry ring buffer inside the save**, drawn only on the panel's
RECORD tab. A player who did not open the panel and change tabs was told nothing - not that a
term had run out, not that a plot had missed, not that an entire party had walked into his
court.

Report 4 deserves its own note: a party joins through `IC.stamp_incoming`, which is a **delayed
poll** because `force_confederation` is asynchronous and the characters transfer about ten
seconds after the deal. So the party appeared well after the diplomacy screen closed, with
nothing anywhere saying why.

### 2a. What the event feed needed, and the trap in it

`cm:show_message_event`'s last argument is not a free number. It resolves

```
event_feed_message_events.group
  -> campaign_groups.id
  -> campaign_group_members (group -> id)
  -> campaign_group_member_criteria_values.value    <- the number
```

An index with no record behind it makes the engine log *"showing event for faction"* and then
draw **nothing**. This chain was followed end to end through a real vanilla row
(`wh3_dlc27_event_group_old_gods_curse` -> 887) rather than taken on trust.

**The event type is not a free choice, and this is the part that would have shipped broken.**
Reading the table alone points at `scripted_persistent_located_event`: it is the only scripted
type vanilla ships with `instant_open` false, i.e. saved to the event history without stealing
the screen - exactly what a court bulletin wants. But grepping **all 5,778 of CA's shipped Lua
files** for what they pass to the plain `cm:show_message_event` gives ten distinct indices, and
every one resolves to `scripted_persistent_event` (persistent=true, instant_open true) or
`scripted_transient_event` (persistent=false). **The located variants are for
`cm:show_message_event_located` and are never used with the plain call.** So the choice was
between two proven shapes, and the attractive one would have been a silent non-draw.

Six events, indices **2600-2605** (vanilla's highest measured criteria value is 1960):

| event | type | image | sound | what raises it |
|---|---|---|---|---|
| plot_ok | persistent | chd/diplomacy | Positive | a move lands |
| plot_fail | persistent | chd/army_morale_down | Negative | a move misses |
| office_lost | persistent | chd/civilisation_down | Neutral | a term runs out |
| party_joined | persistent | chd/faction | Positive | a bloc enters the court |
| secede_warn | persistent | chd/settlement_lost | Negative | a countdown starts |
| snub | **transient** | chd/army_morale_down | Negative | a grievance begins |

The snub is the only transient one **because it is the only one that can fire for several houses
in a single turn**; six cards in a row is an obstacle, not information.

**No dynamic text, and that is also why none of this trips the turn-handler rule.** All three
text arguments are loc keys the ENGINE resolves at draw time - we never call
`common.get_localised_string`, which from a turn handler is a turn-1 CTD. CA builds keys by
concatenation (`"pooled_resources_display_name_" .. key`, `wh2_dlc17_thorek.lua:209`), so the
SECONDARY key names the specific seat by reusing the office bundle's own title key, which
`gen_iron_court.py` already emits. One card per turn for expired terms, not one per seat, and the
seat is named only when exactly one emptied.

### 2b. Feedback for a click the player made (report 6)

Appointing and dismissing changed the card and nothing else - one name in the middle of a
ziggurat of fourteen. `ICUI.confirm` now plays a sound and pulses the card that changed.

Two things worth keeping: the **dismissal plays the negative sound on purpose** (sacking a man
empties a seat you were being paid for and insults his party - the confirmation should not
congratulate the player), and **the pulse is explicitly stopped** after `ICUI.PULSE_SECONDS`.
`pulse_uicomponent` has no duration; without the stop, every seat the player had ever touched
would flash for the rest of the session. That is the half the mutation table pins.

---

## 3. "Just ai slop jargon" (report 2)

The sixteen move blurbs were **all flavour and no mechanism**. "Gold, slaves and a promise. He
rises, and his house remembers who paid." is true, evocative, and does not tell the player he is
buying 60 standing and 20 loyalty - the only thing he can actually decide on.

### The odds do NOT belong here, and briefly did

The first version of this line opened with the move's base chance - `"%d%% odds. ..."` - and that
was a mistake caught by the author on sight. **The odds were already on screen.**
`ICUI.draw_pick` writes `CHOOSE %d%%` on every candidate's own button from
`IC.plot_chance(faction, plot, cand.cqi, target)`, and that call returns the **live** figure:

```
base + floor((mine - theirs) / 10) * plot_chance_per_10,  clamped to 5..95
```

A card can only ever carry the **base**, so for every aimed move the two numbers disagree by the
actor's standing edge - a card reading "65% odds" beside a button reading "CHOOSE 83%". A second
and less accurate copy of a figure that already had a correct home. The panel's own comment had
already settled the design: *"A plot is a hero action: the chance is shown at the moment of
committing, not in a tooltip and not afterwards."*

**This is invisible to every instrument.** The card and the picker are never on screen together,
so no screenshot shows it and no positional check can; and nobody can tell 65% from 83% by
playing. It is now an **inverted** assertion - the harness refuses an effect line containing
"odds", the preview selftest refuses it too, and a mutant puts it back - so it cannot return
quietly. The general lesson is in the `audit-existing-before-adding` memory: grep for what the
mod already shows before adding anything.

The flavour on all sixteen cards had been trimmed to make room for the odds; with them gone the
budget rose from 46-92 characters to 58-107 and the flavour was **put back**, three of the
sixteen (rumour, murder, circuit) to exactly what they shipped with. Collateral damage from a
reverted addition gets reverted with it.

Every move now carries an `effect` line built with `string.format` **from `IC.TUNE`**, so the
card and the code cannot disagree, and it is drawn FIRST. Each line was written against
`IC.plot()`'s own branch rather than inferred from the tuning key's name - which matters:
**`pledge` COSTS the Crown weight and `feast` COOLS the court**, and both read the other way
from `plot_pledge_weight` / `plot_feast_loyalty` alone.

**The card cannot grow.** Four columns by four rows inside the content area puts `PLOT_H` at 176,
with the four blurb cells running 68..144 and the price and button beneath. Effect plus the old
flavour wanted five and six lines, and check 20d said so for fourteen of the sixteen. The flavour
was cut to the budget `plot_budget.py` measured per move at the same font and the same
`GAME_FONT_WIDER` the gate uses - 46 to 92 characters depending on the move. The effect keeps its
room because it is the half that was asked for; if anything ever goes over the edge it is the
atmosphere.

Check 20d now **resolves** each `string.format` against a parsed `IC.TUNE` and measures
`effect .. " " .. blurb`, because `"%d gold"` is nine characters narrower than `"2500 gold"` -
and it raises rather than skipping when it meets a shape it cannot resolve, so a new one is a
build failure and not a silently unmeasured card.

---

## 4. The snub written down every turn (found 2026-09-15, fixed now)

`drift_loyalty` logs `snub_on`/`snub_off` on the TRANSITION, comparing against `house.snubbed` -
and `house.snubbed` was **not one of the thirteen packed fields**. `IC.turn` opens with
`IC.load`, which builds a fresh court table, so the comparison ran against nil every turn and a
grievance that merely CONTINUED was recorded as if it had just started. The live save shows
`legion,warden` at turns 26, 27, 28 and `legion,muster` at 29, 30, 31 - **six of the last
twenty-two entries** spent restating one grievance in a record that holds forty.

Now a **fourteenth house field**, following the established migration idiom: an older save has
thirteen and every house reads as not-yet-snubbed, which costs at most one restated line on the
first turn after the update. `snubbed = (tonumber(bits[14]) == 1)` rather than `or nil`, because
the transition test compares with `== true` and wants a real false.

This fix is also what makes the new `snub` feed event tolerable: behind the repaired gate it
fires once per grievance instead of once per house per turn, forever.

---

## 5. Sorting the character picker (asked for after the fixes)

**The first pass built the wrong thing and it is worth recording why.** "Add sorting option to
house and intrigue" was read as the two TABS - the court's party cards and the intrigue grid -
and built, gated and previewed that way. It was the wrong reading: the ask was the list you read
when **assigning a governor or an office**. The intrigue half is withdrawn; the court half is
kept, because the court tab is the house tab and that half of the ask stands.

**The audit came first**, per the memory written in section 3. There was no sorting anywhere in
the panel, so nothing was being duplicated - and the picker is the list with the real problem.
`IC.candidates` walks `faction:character_list()` and hands back whatever order the engine gave
it: not alphabetical, not by rank, not by anything a player can predict. That is the list he
reads to fill fourteen seats and every province, it is twenty or thirty men deep by the mid
game, and finding the one he wants is hunting rather than choosing.

One new component, `ic_sort` at `(1596, 62, 306, 32)`, right-aligned on the tab row under
`ic_influence` and wearing the tab plate. 306px is sized for the longest label it can carry;
a control that resized itself per setting would jump about the top right of the panel on every
click. It is hidden wherever `ICUI.SORTS` has no entry, which is the same test `ICUI.refresh`
makes - a control that is present and inert is the dead-button fault.

| view | settings |
|---|---|
| `pick` - the office picker, the governor picker, both plot lists and a house roster | ROSTER ORDER / **AVAILABLE** / STANDING / RANK / NAME |
| `court` | COURT ORDER / SHARE / LOYALTY / NAME |
| offices, governors, record, intrigue | no control |

**Why those four have none.** Offices is a fixed ziggurat whose SHAPE is the information,
governors is one row per province in map order, the record is chronological, and the intrigue
grid is sixteen cards in four named columns that all fit on screen at once with nothing to
scroll past or hunt for.

**One entry answers all five character lists.** `ICUI.live_view` already returns `"pick"` for
every one of them - they share the view's headers, column widths and scroll offset - so they
share its sort for the same reason: they are one list of men asked five different questions.
The favour picker answers `"favour"`, has no entry and draws no control; it is two rows of
moves.

### AVAILABLE, and why it reads `pick_rows`

The setting the control exists for. Choosable men first, then most standing, then the name.
The refused men stay on the list underneath - `IC.candidates` lists them deliberately, because
"already Keeper of the Chains" is an answer and an omission reads as a bug - but they stop
standing between the player and the men he can have.

`sort.ready` is taken **off `ICUI.pick_rows`**, not from a second copy of the rules, for the
same reason the red refusal text is: `pick_rows` is what the CLICK reads. Four separate things
decide whether the button will take a man (his rank, his standing, a seat he already holds, and
the model's own plot gates), so an AVAILABLE order built from `affordable` alone lifts a rich
officer who is already seated to the top of the list and the button then refuses him. That is a
mutant.

It is also written out as a two-level comparator rather than folded into one number. The obvious
form is `(ready and 0 or 1) * BIG - standing`, and it is correct only while standing stays under
`BIG`: standing accrues every turn and has no ceiling in the model, so a late campaign would
silently start sorting a rich refused man above a poor available one.

### The permutation

`lines` and `ICUI.pick_rows` are **parallel by index** and `on_pick_click` reads
`pick_rows[row + scroll]` and nothing else. So `ICUI.sort_picker` takes both tables and sorts an
index list, then rewrites both from copies - writing back in place overwrites an entry the
permutation has not read yet, and men are duplicated and men are lost. Both are mutants.

It is called **after** every candidate is on the list and **before** the hire rows are appended.
The hires are not candidates: "I have nobody for this" is answered under the men, not shuffled
in among them.

### The rules the court half still carries

1. **`IC.present_houses`' order is load-bearing.** `ICUI.bar_widths` addresses standing-bar
   segments by POSITION, and that function's own comment says confederates are appended rather
   than interleaved so that seating one does not move a colour already on screen. So
   `ICUI.sorted_parties` returns a COPY and `draw_court` uses it only from the card loop down;
   the dial, the walls, the crests and the secession warning stay on `slugs`. The mutant puts
   the sort inside `ICUI.court_slugs`, which is the tidier-looking edit and the whole fault.
2. **The click keys must be the list the draw used.** `ICUI.court_keys` is assigned from the
   sorted list in the same loop that fills the cards.

### The rest

**The first entry of every list is the order the list already had** (ROSTER ORDER, COURT ORDER).
A sort control whose every setting is a sort gives the player no way back to the arrangement he
has learnt.

**The setting is session state, not save state.** It is how the player is reading the panel right
now, not a fact about his court, so there is no fifteenth packed field and no migration.

**Cycling resets the page offset.** The offset addresses a position, and after a re-sort position
N is a different man.

**Every comparator ends on a total tiebreak** - the name then the cqi for a man, the slug for a
party. `table.sort` is not stable in Lua, and this was measured rather than assumed: five equal
elements under an always-false comparator sort to `a,d,c,b,e` from one end and `e,b,c,d,a` from
the other. Without the tiebreak the list reshuffles on every refresh of one unchanged save. The
check feeds each sort the same list from both ends and the mutant strips the tiebreak out.

### Two things the new preview shape found

`tools/preview_iron_court.py` grew two shapes for this - `ic_pick.png` as the panel opens and
`ic_pick_ready.png` under AVAILABLE - and drawing the row pool for the first time surfaced two
faults that had nothing to do with sorting:

- **`draw_picker` read an undeclared global.** `ICUI.house_name(cand.slug, faction_key)` - there
  is no `faction_key` local in that function and there never was. It resolved to nil, and
  `house_name`'s own default (`ICUI.player()`) happened to be the same faction, so the cell has
  been drawing correctly by accident since the picker was written. Fixed to `faction`.
  `check_lua_undeclared.py` cannot see it: it finds ALL_CAPS names only.
- **The Party column clips every party name there is.** `ic_row_b` is 180px and **588 of 588
  rollable names overflow it** - measured at the cell's own font size with `GAME_FONT_WIDER`.
  The narrowest possible roll ("The Bloc of the Slag") needs 234px and the widest ("The
  Brotherhood of the Unbroken Rank") needs 471px; the median is 351px. twui never wraps and
  never shrinks, so every one of them has been truncating in game on the picker and on the
  governors view since the panel was written. **NOT FIXED** - see section 7.

---

## 5b. The currency renamed: standing -> influence

Asked for after the sort landed, and a display change only.

**What moved:** 38 string literals in the two shipped Lua files, the five band
explanations and the four removal lines in `gen_iron_court.py`, `gen_ic_ui.py`'s
measured card samples, and two typed-in mirrors in `preview_iron_court.py`. The
picker header is now `Influence / Holds`, the court's section label
`Influence in the court`, the sort setting `INFLUENCE`.

**What did NOT move, and why each one is a decision rather than an oversight:**

| kept | what it is |
|---|---|
| `court.standing` | a PACKED SAVE FIELD - renaming it either breaks every existing save or buys a migration for a word nobody reads |
| `"standing"` | the refusal CODE `can_appoint` / `can_governor` / `can_plot` return and the panel matches on. An enum, not a noun |
| `derpy_ic_standing` | a component id, a `.twui.xml` filename, an art path and the four character-trait keys - all four in the DB or on disk |
| `{key = "standing"}` | the sort setting's own key; only its `name` reaches a screen |
| `"the Standing Debt"` | a party name TAIL. "The Bloc of the Standing Debt" is a proper noun that happens to share the word |
| `"standing plate: ..."` | log lines, which go to the script log and not to a player |

The rewrite was written as an EXCLUSION list over every string literal rather
than an inclusion list of the sentences to change. The failure mode of the
other direction is a sentence quietly left in the old word, and a sentence
added later would inherit it; this way a new sentence is renamed by default and
only the six identifier shapes above are spared.

**Two things the gates caught, both watched failing first:**

- **The sort label was skipped on the first pass.** The exclusion test was
  `lit.lower() == "standing"`, and `{key = "standing", name = "STANDING"}` puts
  two literals on one line that lowercase to the same thing - so the label was
  spared along with the key. Caught by reading the diff, not by a check.
- **Four harness assertions read the word off the screen** and were RE-AIMED,
  not deleted: the refusal line naming the currency, the hire row quoting what a
  bought officer arrives with, the character plate's `137 standing`, and the
  sorted picker's descending order parsed back out of `ic_row_d`. Each still
  asserts exactly what it asserted before. The `pair()` fixture's row-d cell
  went with them, because a fixture that says something the panel no longer
  draws is a lie waiting to be believed.

**The word is one character longer**, which is why `gen_ic_ui.py`'s measured
samples were rewritten rather than left: check 20f measures the office card's
term line against its own 298px cell and would otherwise have been measuring a
string the panel no longer draws. Re-measured, `"4000 influence - 99 turns
left"` is **274 of 298** (it was 269), and the sort control's longest label is
still `SORT: ROSTER ORDER` at 231 of 306 - `SORT: INFLUENCE` is 188.

**The loc had to be fixed in the GENERATOR, not the TSV.**
`Modding Files/source/iron_court/loc.tsv` is an EXPORT of
`gen_iron_court.build()`, so a hand edit there survives exactly until the next
generator run. Both were done and the regenerated TSV diffs clean against the
hand edit, which is the only reason the hand edit is known to have been right.

---

## 5c. PARTY added to the picker's sort settings

Asked for off a screenshot of the governor picker: the Party column was there
and no setting grouped by it.

ROSTER ORDER / AVAILABLE / INFLUENCE / RANK / **PARTY** / NAME. It sits beside
NAME because those two are the grouping orders and the numeric ones stay
together.

**The comparator carries three rules, and each one has a mutant:**

1. **House name ascending**, so the column the player is reading is the column
   the list is grouped by.
2. **Influence descending inside a house.** Grouping alone leaves the choice the
   player opened the picker to make - *which* of this house's men - unmade. Same
   secondary key AVAILABLE uses, and for the same reason: it is the bar every
   one of these lists is gated on.
3. **The unaligned under everyone.** "None" is an answer rather than a house,
   and almost every rolled name begins "The", so plain alphabetical order floats
   every man of no party to the TOP - the opposite of where a grouping order
   wants him. `unaligned` is a BOOLEAN off `cand.slug`, not a second comparison
   against the string "None", so that literal stays in one place.

**The key is the drawn cell.** The party name was computed inline in the row
constructor; it is now hoisted into a `party_name` local used for both the cell
and `sort.party`. Two computations could disagree, which is the same fault
`sort.ready` avoids by reading `ICUI.pick_rows` instead of re-testing the rules.
Nothing in the model changed - `IC` never learns about this.

### The fixture that could not tell two sorts apart

The mutant *"a PARTY key taken from the slug instead of the drawn cell"*
**SURVIVED** the first version of the check. The three houses the fixture seated
happened to sort the same way by slug as by rolled name, so grouping on either
produced the same screen and the check was proving nothing about which string
the sort reads.

**Fixed in the FIXTURE, not the assertion.** A rolled name is
`"The <head> of <tail>"` held in the save as a pair of indices, so the fixture
now SETS them - heads 7 / 1 / 11 are Assembly, Brotherhood and Council - to put
the by-name order deliberately out of step with the by-slug order. And it
asserts that the two disagree, so a later edit to `IC.PARTIES` cannot quietly
put them back in step and re-open the hole.

The check asserts about its own fixture twice, in fact: the other is that at
least one rolled name sorts **after** `"None"`, because if every one sorted
before it the unaligned would land at the bottom under plain alphabetical order
too and rule 3 would be untestable.

Harness 336 -> 337, mutants 50 -> 53, 0 unexplained. `SORT: PARTY` measures
**142px of the control's 306** - `SORT: ROSTER ORDER` at 231 is still the one
that sized it.

---

## 6. Verification

| instrument | result |
|---|---|
| `_iron_court_harness.lua` | **337 checks, ok** (336 after the rename, 331 after the bug fixes, 327 before) |
| `mutate_iron_court.py` | **53 mutants, 0 unexplained** (50 after the rename, 42 after the bug fixes, 36 before) |
| `gen_iron_court.py --check` | ok - 43 bundles, 56 junctions, 70 traits, 500 loc |
| `import_iron_court.py --check` | verify ok, 7 ui files, 2 scripts |
| `gen_ic_ui.py --check` / `--selftest` | ok - 7 files, **220 components** |
| `preview_iron_court.py --selftest` | ok - 7 files validate, 16 moves read 3 rows |
| `luac -p`, `check_lua_api.py`, `check_lua_undeclared.py` | clean |
| `read_pack_index.py` against the BUILT pack | 1680 paths; 1658 of 1658 plates, 0 nested, 0 stray; the 2 scripts and 7 `.twui.xml` byte-identical to the staged files; 0 player-facing `standing` literals left |

**Every new check was watched failing before it was kept:**

- check 8b2 - the shipped card list restored: reports both halves, names x=-84.
- check 8b1 - three index drifts: a number the DB has no record for, a persistent flag that
  disagrees with its record, an event the model raises with no record at all.
- the six event-feed checks in `gen_iron_court.check()` - a bad image key, a bad sound event, a
  persistent row that does not open, an index colliding with vanilla, two events on one index,
  and the located variant CA never raises with the plain call.
- five new mutants: the snub field dropped, the vacancy that tells nobody, the feed without its
  human guard, a pulse that never stops, one sound for both outcomes, and a move card quoting
  odds the picker already shows live.
- the four sorting checks, and the eight mutants aimed at them: the sort pushed down where the
  standing bar reads it too, a comparator with nothing to break a tie on, a card grid drawn from
  the list the clicks are not, a picker that never sorts, one reordered on screen but not where
  the click reads, a permutation written over the rows it has not read yet, an AVAILABLE order
  that answers a different question than the click, and a control with no setting for the list's
  own order.

**Two of the sorting checks assert about their own fixture first**, because a sort that did
nothing would otherwise pass both - and one of them caught itself. The picker fixture seeded
standing DESCENDING in roster order against a DESCENDING sort, so the sort was a no-op and the
fixture assertion is what said so. Fixed the fixture. The other refuses to run against a court
whose default order is already sorted by loyalty, and the AVAILABLE check refuses to run against
a list that opens with an available man at the top.

**One fixture deliberately holds a rich man who is refused anyway.** Without him "can he pay for
it" and "will the click take him" are the same boolean, and the mutant that builds AVAILABLE out
of `affordable` survives.

**One fixture fault, recorded rather than hidden.** The first version of the event-feed check set
a local `humans` table and the base stub ignored it - the harness's house idiom is to override
`cm.get_human_factions` and restore it, and one check above leaves it overridden. The check was
testing its own fixture. Fixed the fixture.

**One check re-aimed, not deleted.** "the blurb was not written whole" compared the drawn cells
against `plot.blurb`, which stopped being what the card draws the moment the effect line went in
front of it. The property it guards is unchanged - `fit_lines` silently drops a line that will
not fit - so it now compares against `effect .. " " .. blurb`.

---

## 7. Open

- **The Party column truncates every party name there is.** `ic_row_b` is 180px and all 588
  rollable names need between 234px and 471px (median 351px) at the cell's own font size with
  `GAME_FONT_WIDER`. twui never wraps and never shrinks, so the picker and the governors view have
  both been clipping since the panel was written. The fix is a rebalance of `ROW_LAYOUT` - the
  Rank column holds a one- or two-digit number in 180px and Influence / Holds has 620px for a
  sentence that measures around 320px, so the room exists - but it moves the shared row pool under
  three views, the `ic_hdr_*` strip and the `ICUI.COL_WH` mirror the packing gate compares, so it
  is its own change with its own verification. **Not attempted here.** Nothing measures row-cell
  overflow today: check 9 refuses column COLLISIONS (positions) and check 20d measures the move
  card's blurb, and neither looks at what a row cell is asked to hold - so the fix wants a check
  of its own as much as it wants the widths.
- **No turn has been played with any of this in.** The first thing to check in game is that the
  six event cards actually draw; an index or type fault is a silent non-draw and the offline
  checks can only prove the rows are internally consistent and vanilla-shaped.
- The two sound event names (see section 0).
- **The two unidentified governors** from the previous handoff, Kullani Growlish (cqi 3083) and
  Jarthrazz Oathkiller (cqi 2233), are untouched and still need the running game.
- The event cards name a seat but never a **party** - parties are named at runtime from rolled
  index pairs and have no loc key to point at. Naming one would mean minting a loc key per party
  name part, which is a bigger change than it looks.

---

## 10. Four features off one screenshot (2026-09-16, later still)

Asked for against a Rome 2 politics screenshot. Three of the four already had
model verbs to stand on, which the audit found before anything was designed:
`IC.PLOTS` carries `provoke` and `purge` (both `cat = "house"`), `IC.FAVOURS`
carries `secure`, and `ICUI.pick = {kind = "house"}` already drew a roster and
already filtered it by `pick.slug`.

### 10a. General / Lord / Hero

`IC.kind_of_character`, carried on every candidate, drawn in the Rank cell -
now headed **Kind / Rank**.

**The split is CA's and the ORDER is the correctness.** `character_type` takes a
key from the AGENTS table, so `character_type("general")` is true for a lord
whether or not he commands anything and false for every hero.
`has_military_force` is asked SECOND, because CA documents it true for an
EMBEDDED hero as well as for the lord commanding - so asking it first calls a
wizard riding in a stack a General. That is a mutant.

**The Rank cell was chosen by measurement, not taste:** 180px carrying a one- or
two-digit number is the widest dead space on the row, and the Party cell beside
it is the one already overflowing. `General 50` measures 126 of 180.

**The harness stub had no `character_type` at all**, so the first green run had
the feature entirely untested - `kind_of_character`'s pcall failed on every
fixture and every man came back unlabelled. Exactly the fault the `is_dead`
comment fifteen lines above it warns about. Stub added, defaulting to
`"general"`, which `check_character_stub` holds against CA's member index.

### 10b and 10c. The party screen

Every card opens **its own roster** now, with a three-button strip beneath it:
**SECURE LOYALTY / PROVOKE / PURGE**. It used to be the Crown's card opening a
roster and every other card opening the favour list, which meant the one thing a
player wants off a rival - who is in it, what each has earned, what each holds -
was the one thing no tab showed.

Four components at the pager's own line, left of it: `ic_act_lbl` at
`(18, 982, 300, 26)` and three 340px buttons from x=330 ending at 1382 against
the pager's 1420. That row is empty on every view, which is also where Rome 2
puts its strip.

**A `cat="house"` move is still aimed at a MAN.** `IC.may_target` takes a victim
cqi and the effect lands on that man's house - which is why the record reads "X
pays N influence to make Y an enemy" with Y a house name. So PROVOKE and PURGE
cannot skip the victim picker; what they do instead is open it **filtered to
that house**, which is `pick.house`, one more term on the filter the roster
already used.

**The button's state is asked of the model.** `slug == IC.CROWN` would be a
second copy of a rule `IC.may_target` and `IC.can_favour` already own, so the
strip tries the house's own men through `may_target` and takes the first answer.
That also gets right a case the slug test would have missed: **a house seated at
court with nobody left in it** has nobody to aim at, and the button says so
rather than opening a picker with no rows. That case is in the fixture, because
without it the two implementations are indistinguishable - the same hole the
PARTY sort's fixture had, found the same way.

On your own house all three draw RED rather than hiding. Note that includes
SECURE LOYALTY: `IC.can_favour` refuses the Crown outright.

### 10d. A party helping itself to a seat

`IC.party_seize` - the mirror of `IC.ai_fill_offices`, gated on the opposite
half of the same `IC.is_human` call. That one fills an AI FACTION'S OWN court;
this is the rival parties inside the PLAYER'S court.

Four conditions, three of which the player controls: the seat must be VACANT (an
appointment of his is never overturned), the house must be at or under
`IC.TUNE.seize_loyalty` = **25**, which is the PLOTTING band's ceiling and
therefore a warning the panel has already been giving him; the house must have a
man who clears the seat's own bars, which `IC.appoint` decides; and it must not
be his own house. **One seat per house per turn** - a court with three angry
parties and eight empty seats should feel like it is slipping, not like it
changed hands overnight.

**The affinity seat first**, then any other. A house taking its own office reads
as a grievance answered; the same house taking the Keeper of the Kilns reads as
a bug.

**`IC.appoint` is the only way in**, exactly as `ai_fill_offices` does it, so the
rank bar, the influence bar, the term, the weight, the loyalty bookkeeping and
the snub when an outsider takes a house's own seat all hold by construction.

**The lock binds the player and not the model, and that falls out of the
existing `quiet` flag rather than a new one.** Every internal `IC.dismiss` - the
re-appointment inside `IC.appoint`, an expiring term, a man who fell under his
bar - passes `quiet=true`, and the panel's dismissal is the one call that does
not. So `not quiet` IS "the player asked for this", and a locked seat still
empties when the rules require it.

**One event, one line.** `IC.appoint` writes its own `appoint` entry, so the
seizure re-KINDS that entry rather than adding a second - which would have been
the snub bug's exact shape.

**An eighth save section**, holding the absolute unlock turn rather than a
countdown, so nothing has to tick it. A save written before it has seven fields,
`unpack`'s `([^|]*)` walk reads the eighth as empty and `new_court`'s `{}`
stands - the migration is that there is no migration, and a check asserts it by
truncating a packed court and loading it.

The comment on `on_office_click`'s empty branch said there was no lock to test
because the seat is empty. That was true until a party could take one: a seized
seat's holder can still fall under his bar, which empties it quietly while the
lock has a turn to run. Re-aimed rather than left to mislead.

### Verification

| instrument | result |
|---|---|
| `_iron_court_harness.lua` | **343 checks, ok** (339 after the PARTY sort) |
| `mutate_iron_court.py` | **65 mutants, 0 unexplained** (59 after the PARTY sort) |
| `gen_ic_ui.py --check` / `--selftest` | ok - **224 components** (was 220) |
| `preview_iron_court.py --selftest` | ok, and a fifth shape: `ic_house.png` |
| `gen_iron_court.py --selftest`, `import_iron_court.py` | ok |
| `luac -p`, `check_lua_api.py`, `check_lua_undeclared.py` | clean |

**Two stale anchors, both re-aimed rather than dropped** - each was a fault that
still exists at a new address. "A favour your own party cannot be given" moved
from `on_party_click` to the strip's own state; "the roster listing every
house's men" moved by a few characters when the filter line grew its second
term. **Three checks asserted the old card behaviour** and were re-aimed; one
got stronger for it, walking card -> strip -> list instead of one handler.

**The preview found one fault of its own**: `pick_title`'s house branch is one
sentence written as two Lua literals with `..` between them, and the first
regex matched only up to the first closing quote - so the picture drew
"...and what" with the rest missing. A truncation the panel does not have.

---

## 8. Packed and deployed (2026-09-16)

`Modding Files/Modpacks/derpy_iron_court.pack` rebuilt and copied to
`F:\SteamLibrary\steamapps\common\Total War WARHAMMER III\data\`, byte-identical.
7,683,204 bytes, 1680 paths, against the 2026-09-15 build's 7,646,430. The game was shut.
Everything in this handoff was staged-only until now: the six bug fixes, the event feed, the
picker sort and the rename all shipped in this one build. **The Workshop copy is untouched.**

**RPFM's MCP tools never registered this session** although the server answered 200, so the
whole build went over raw JSON-RPC to `/mcp` - see the `rpfm-mcp-over-raw-http` memory. Two
things that cost a run:

- **`import_tsv` refuses a table the pack has not got.** The four event-feed tables
  (`campaign_groups`, `campaign_group_members`, `campaign_group_member_criteria_values`,
  `event_feed_message_events`) are new since the last build, so each needs
  `new_packed_file` with `{"DB": [name, table, version]}` first. The version is taken from the
  TSV's own second line (`#<table>_tables;<version>;<path>`) rather than typed beside it - it
  has to match the FIELD SHAPE, and a number written in two places can disagree with itself.
- **`add_packed_files` nests a folder.** A destination of `{"Folder": "ui/derpy_ic"}` means
  "the folder this source goes INSIDE", so `...\pack\ui\derpy_ic` landed at
  `ui/derpy_ic/derpy_ic/*.png` - 3316 plates in the pack, half of them at a path nothing reads,
  and the pack at 14.5MB. The destination has to be the PARENT: `{"Folder": "ui"}`. Nothing in
  the save call said so; it was found by reading the built pack's index back.

Which is the point of the last gate: the pack is verified with `read_pack_index.py`, a reader
that has never heard of RPFM, rather than on the strength of `save_packfile` returning ok.

**Still not played.** Everything in section 7 stands.

---

## 9. The PARTY sort is built but NOT deployed (2026-09-16, later)

`Modding Files/Modpacks/derpy_iron_court.pack` carries it and is verified;
`data/` does **not**. The game was running when the copy was attempted, so the
deployed pack is one revision behind - it has the rename and everything in
sections 1-5b, and not section 5c.

Only `zzz_derpy_iron_court_ui.lua` changed, so the push was that one file: no DB
row, no `.twui.xml`, no plate, and the model Lua untouched. **A File destination
is the full path; a Folder destination is the PARENT** - see section 8 for the
build that learned the difference the expensive way.

Also worth knowing for next time: **the raw-HTTP MCP session expired between the
two builds** and every call answered HTTP 404. Re-`initialize`, re-
`set_game_selected` and re-`open_packfiles`; state is per session and none of it
survives.

---

## 11. The row pool rebalanced, and the check that should have caught it

The Party column had been overflowing since the picker shipped. It only became
visible when the Kind label put WORDS in the cell beside it - until then the
overflow ran into a column holding one digit and mostly whitespace.

### 11a. Nothing measured a row cell

Check 9 refuses column COLLISIONS - positions against each other - and says
nothing about what goes IN one. 20f and 20g measure the office and party CARDS.
**20d measured this pool until the moves became cards**, at which point the row
lost its last measurement silently; its own comment records the change and
nobody noticed what it took with it.

So **check 20i**: every string the model and this generator compose, measured
against the cell it lands in, plus the four column headings over them. Numbered
20i because 20h was taken - that is the half that makes 20g's `CUT_CELLS`
exemption cost something.

### 11b. The widths, measured by the check rather than apportioned

Narrow every cell to 1px and 20i reports the width it wanted. Content, then
heading, then the larger of the two:

| cell | content | heading | set to |
|---|---|---|---|
| `ic_row_a` Character | 306 | 118 | **360** |
| `ic_row_b` Party | 422 | 68 | **432** |
| `ic_row_c` Kind / Rank | 119 | **146** | **150** |
| `ic_row_d` Influence / Holds | 483 | 212 | **528** |
| `ic_row_e` action | 162 | - | 170, unchanged |

**"Kind / Rank" is the first heading in this panel wider than anything the
column under it draws**, which is what the first pass at this got wrong: it set
c to 140 from the content alone and the heading clipped itself. Both halves are
in the selftest now.

**The by-hand figures in the old section 11 were wrong** - 470px for the widest
party name and a 292px shortfall. The check's own measurer says 422 and the
shortfall was smaller. Two measurers disagreeing is worth the line: the one
that ships is the one every other check in this file already uses.

### 11c. What the game's own loc forced

A character's name, a province's and a confederate party's faction name are
**CA's loc, not ours**. They cannot be measured from anything in this repo and
no width can be proved sufficient for them, so a check that held those cells to
a width could only ever fail over a string nobody can shorten.

So `fill_rows` **cuts** every cell but the last, through the `ICUI.fit_cut` the
party card already used. 20i measures what IS ours and holds it to the width;
the cut is the other half of that bargain, and 20i fails the build if the call
goes missing.

**The cut ate its own markup, and the harness found it.** The favour list puts a
gold price in cell one - `[[img:...icon_treasury.png]][[/img]]2500`. That is 52
characters with no spaces in it, so it is ONE word, no prefix of it fits, and
fit_cut falls through to its per-character branch and truncates inside the tag;
the panel then draws the raw text of half an image path. The guard went into
`fit_cut` and not into `fill_rows`, because the trap belongs to the helper -
`ic_party_leader` is a plain name today and the next caller need not be. CA's
own art folder is `campaign ui`, with a space in it, so a markup string can be
split BETWEEN words and lose the tag that way too.

### 11d. Four mirrors of one geometry, and two of them caught me

The row layout lives in `ROW_LAYOUT` (the generator) and is mirrored in the
panel Lua three times: `ICUI.ROW_CHILD_XY` (where each cell is moved to),
`ICUI.COL_WH` (what each is resized to) and `ICUI.PANEL_XY` (the header strip).
All four are policed - `import_iron_court.py` compares the first and third
pairs, and the harness's own column-collision check reads `ROW_CHILD_XY` - and
**two of the three mirrors were caught disagreeing during this change**, one by
each instrument.

### Verification

| instrument | result |
|---|---|
| `_iron_court_harness.lua` | **344 checks, ok** (343 before) |
| `mutate_iron_court.py` | **67 mutants, 0 unexplained** (65 before) |
| `gen_ic_ui.py --check` / `--selftest` | ok, 224 components, 831 guids |
| `preview_iron_court.py --selftest`, all five renders | ok |
| `gen_iron_court.py --selftest`, `import_iron_court.py --verify-only` | ok |
| `luac -p`, `check_lua_api.py`, `check_lua_undeclared.py` | clean |

Two new mutants, both plausible rather than typos: **the row cells set rather
than cut** (the change somebody makes to tidy an extra call out of a loop that
runs MAX_ROWS x 5 per redraw) and **the cut with no guard for its own markup**
(the branch that reads redundant because a price is short - it is not short
until the engine has resolved it).

---

## 12. Packed and deployed (2026-09-16, the four features and the rebalance)

Game closed and checked before the copy. RPFM open; the raw-HTTP MCP session
had expired again, so a fresh `initialize` / `set_game_selected` /
`open_packfiles`.

**`open_packfiles` takes `paths`, not `pack_paths`.** A wrong argument name is
accepted, returns an empty body and leaves the pack shut, and the next call
fails with "Pack not found" rather than naming the real fault.

**The plate step is corrected and now conditional.** Its destination was still
`ui/derpy_ic`, which nests - the fault that put 1658 plates at a path nothing
reads on the previous build. It is the parent, `ui`, and it only runs when the
packed set differs from `art_paths()`. The plates are keyed by size and state,
not by position, so a layout change does not touch one: **1658 files left
alone**, and the slow half of the deploy that has also been its only corrupting
half did not run at all.

| | |
|---|---|
| `Modpacks/derpy_iron_court.pack` | **7,714,099 bytes, 1680 paths** |
| pushed | 10 tables, the loc, 2 scripts, 7 `.twui.xml` |
| read back with `read_pack_index.py` | both Lua files byte-identical to the staged copies; the row XML carries 360/432/150/528 |
| `data/derpy_iron_court.pack` | replaced, MD5 identical, read back at 1680 paths |

Still unverified offline and still open: whether the two Wwise sound names fire
from `common.trigger_soundevent`, and the two unidentified governors (Kullani
Growlish cqi 3083, Jarthrazz Oathkiller cqi 2233). **Still not played.**

---

## 13. The 18:19 build wedged the game, and the action strip is withdrawn

**It shipped green and broke the game on the first open of the panel.** 344
harness checks, 67 mutants, every generator gate, five clean renders - and
1957 script errors in fourteen seconds.

### 13a. What the log says

The first script error of the session is ours, at `ICUI.refresh:4155` -
`comp("ic_alert", panel)` - reporting that its parent is not a uicomponent.
From that instant:

- `find_uicomponent` starting at the ui root failed for **every mod on the
  machine**. Another mod's `edict_tooltip.lua` is in the tracebacks; 1951 of
  the 1957 errors have no Iron Court frame at all.
- **CA's own `output_uicomponent` stopped working**, so not one `[ui]` block
  was written after 134.7s. That is why `derpy_ic_panel` appears zero times in
  the log - a *consequence* of the break, not evidence the panel was missing.
- The panel could not be closed: `ICUI.close` is reachable only through the
  click listener, whose `comp(ICUI.PANEL)` is one of the failing calls, and
  `ICUI.show_hud(false)` had already hidden the campaign HUD.

**`script_error` does not throw.** It logs and calls
`common.show_error_with_callstack`. Nothing raised; `comp()` simply returned
nil, `fill_party` skipped its cells, and ~2000 error boxes wedged the game.
That is the whole mechanism of "blank cards and nothing clickable".

### 13b. What the logs isolate it to

| session | `ic_sort` | `ic_act_*` | panel opened | errors |
|---|---|---|---|---|
| 15:19 | 0 | 0 | 11 | 0 |
| 15:58 | 22 | 0 | 45 | 0 |
| 16:13 | 6 | 0 | 37 | 0 |
| 16:32 | 2 | 0 | 14 | 0 |
| **18:25** | - | present | - | **1957** |
| 18:48 (rolled back) | 0 | 0 | 13 | 0 |

The sort control was clicked 22 times in one clean session, so **house sorting
is proven good** - the first rollback went further back than the evidence
required, and was corrected.

Against `bak2/zzz_derpy_iron_court_ui.lua` (16:02, proven in two clean
sessions) the **court tab's entire delta is two things**: the strip's draw
block in `refresh`, and one `string.find(text, "[[", 1, true)` in
`ICUI.fit_cut`. `draw_court` and `fill_party` are byte-identical. A plain
`string.find` on a string cannot throw.

### 13c. What was eliminated, and what was not

Eliminated: no pack in `data/` (all 264 checked) redefines `is_uicomponent`,
`tostring`, `string` or `find_single_uicomponent`; CA's `lib_common.lua` line
numbers match the shipped file exactly; the panel XML is well formed with 177
components and 662 GUIDs unique under every normalisation tried, including
hex-only; `ICUI.layout` is nil-guarded on every new entry; the save migration
is correct; the four new components are the same XML shape as the tab buttons,
with the same art, inside the panel's extent, and **narrower than `ic_sort`,
which works**.

**The mechanism was never identified.** `is_uicomponent` is
`string.sub(tostring(v), 1, 12) == "UIComponent "`, and the value it rejected
prints as `UIComponent (00000001C23B7180)` - which satisfies that test. Nothing
in this repo explains it.

### 13d. Withdrawn rather than fixed

A fix for a mechanism nobody has identified is a guess that gets deployed, so
the strip comes out and everything else ships:

- **Kept:** the Kind / Rank label, the party seizure, the row rebalance and
  check 20i, the `fit_cut` markup guard and the `fill_rows` cut.
- **Withdrawn:** the three-button strip and "every card opens its own roster".
  `on_party_click` is back to the 16:02 split - your own party opens its
  roster, a rival opens the favour list.
- **No capability is lost**, which is what makes this a withdrawal of a
  presentation. The strip's three moves are one `IC.FAVOURS` entry and two
  `IC.PLOTS` entries of `cat = "house"`; the favour list is on a rival's card
  and the two moves are on the intrigue tab, exactly as before.

`ICUI.pick.house` went with it - `on_action_click` was its only writer, so the
second term on `draw_picker`'s filter could no longer be true, and a guard that
cannot fail reads as a rule the panel enforces.

### 13e. The absence is a check, not an omission

The strip's own harness check is **inverted, not deleted**: it now asserts that
`ICUI.PANEL_XY` lays out none of the four components, that the tables and
handlers are gone, and that all three moves are still in the model. Its comment
carries the evidence above, so anyone about to add components to
`derpy_ic_panel.twui.xml` meets it first.

**And that check is watched to fail.** A new mutant puts `ic_act_1` back into
the layout mirror - the route any re-addition must take. Both stale anchors the
withdrawal created were **re-aimed rather than dropped**; one of them has now
been re-aimed twice and is back where it started.

| instrument | result |
|---|---|
| `_iron_court_harness.lua` | **344 checks, ok** |
| `mutate_iron_court.py` | **64 mutants, 0 unexplained** |
| `gen_ic_ui.py --check` | ok - **220 components** (was 224) |
| `preview_iron_court.py`, five renders | ok |
| `gen_iron_court.py --selftest`, `import_iron_court.py --verify-only` | ok |
| `luac -p`, `check_lua_api.py`, `check_lua_undeclared.py` | clean |

### 13f. What this says about the gate

The offline gate passed a build that made the game unplayable. It has **no
coverage of engine-side component creation or lookup at all** - the preview
parses the XML with TWUI Studio's reader and the harness runs against a Lua
fake panel, and neither calls `CreateComponent`. Every check in `gen_ic_ui.py`
measures a file; none of them can see what the engine does with it. That gap is
the real finding of the day, and it is still open.

---

## 14. The strip was not it, and the panel could not say what was

**Section 13 withdrew the action strip and the next build failed identically.**
The four components are exonerated: same first error, same line, same unplayable
screen. §13d called the withdrawal "a fix for a mechanism nobody has identified
is a guess that gets deployed" and then deployed one anyway. That was wrong.

### 14a. Read the error again - it does not name the parent you passed

    ERROR: find_single_uicomponent() called but supplied parent
    [UIComponent (00000001C3D5C010)] is not a ui component

`find_uicomponent` (`lib_common.lua:411-422`) tests `arg[1]` with
`is_uicomponent` and, when that fails, substitutes `core:get_ui_root()` **and
does not test the substitute**. `find_single_uicomponent` (`:386`) tests it and
reports. So the pointer printed is the **ui root**.

The proof is three lines further down the same log: an unrelated mod's
`edict_tooltip.lua`, which passes the root, is handed **the same pointer**. This
was read for two days as "our panel handle is bad", and it is really "our panel
handle failed the test, so CA swapped in the root, which fails it too".

**Which of the two turns is still the open question**, but the ordering settles
one thing: `comp(ICUI.PANEL)` at the top of `refresh` **succeeded** - it is not
in the log and the first error is 70 lines later - so the panel handle passed
`is_uicomponent` and then failed it inside the same function call. A bad root
alone cannot produce this: every call from there down passes the panel, so the
root is never consulted while the panel is good.

And the contradiction is unchanged. `is_uicomponent` is
`string.sub(tostring(value), 1, 12) == "UIComponent "`, the message is built
with `tostring(parent)` in the same expression, and it prints
`UIComponent (00000001C3D5C010)`. Both cannot be true.

### 14b. The reason two launches taught nothing

`refresh` wraps every draw in a `pcall` and puts the error in `warn`. **`warn`
reaches exactly one place: `ic_alert`.** `ic_alert` is a component. When the
fault is in the ui layer, `comp("ic_alert", panel)` is one of the failing calls -
so the single line saying what `draw_court` threw is the single line nothing on
the machine can print. Two builds were shipped, launched and diagnosed without
it.

That is now a defect fixed rather than instrumentation added: the caught error
goes to the log as well as the screen, and a mutant takes the line back out.

### 14c. The probe

`probe_layer` prints every piece of the broken test at once, so one launch ends
the guessing:

| reading | meaning |
|---|---|
| `literal_ok=false` | the string library itself is damaged |
| `literal_ok=true`, `root_ok=false` | `tostring` is not returning what the error message prints |
| `root_ok=true`, `panel_ok=false` | the panel handle is the bad one |

It also prints the identities of `string.sub`, `tostring` and `is_uicomponent`,
the first twelve characters of the root as a bracketed literal, and its length.
It fires only when the panel handle has already failed, so a healthy refresh
pays two boolean calls.

### 14d. The half that had nothing to do with the cause

All of the *damage* was the panel's reaction, and none of it needed the mystery
solved. Three separate faults turned a broken feature into an unplayable
campaign, and all three are fixed:

- **`each_root_child` filtered the HUD-restore walk on `is_uicomponent`** - the
  exact test that is broken - so `ICUI.close`, which puts `show_hud(true)` first
  and unconditionally, still gave nothing back. The filter bought nothing either:
  `fn` is called inside a `pcall`, and that is what makes the walk safe.
- **`ICUI.close` looked its own panel up** through the call that has failed.
  `ICUI.last_panel` is now written once at creation and read by the teardown
  alone - a deliberate exception to this panel's "never cache a handle" rule,
  because here the LOOKUP is the thing that is broken.
- **`refresh` could not tell a shut panel from an unfindable one.** Both ended at
  `if not panel then return end`, so an open panel whose lookup had stopped
  working returned quietly, every time, with the HUD hidden behind it forever.
  `ICUI.hidden` separates them: hidden-with-no-panel is a state that should not
  exist, and the answer to it is to give the campaign back.

And then it stops drawing. Every further cell was another `script_error`, each
calling `common.show_error_with_callstack` - which is what actually wedged the
game, not the fault itself.

### 14e. Watched to fail

The new check stubs `is_uicomponent` to return false for everything - the
failure as the log describes it, machine-wide - and asserts the HUD comes back,
the root siblings with it, something already hidden stays hidden, the panel is
destroyed, and the log says why.

It failed three times while being written, and each failure was real:

1. The first bail-out condition also tested the root, which fires in the
   harness. The harness was right - the panel is what turns - and the condition
   narrowed.
2. It then found a **second route into the same unplayable screen** that needs
   no mystery at all: `refresh`'s opening `if not panel then return end`.
3. `panel.destroyed` could not pass because the fake component's `Destroy` was a
   no-op. **The fixture was fixed, not the assertion** - a stub that swallows a
   teardown cannot tell a panel that removed itself from one still sitting on the
   player's screen.

One mutant **survived**: deleting the teardown from `bail_out`. It was right to -
`ICUI.close` already reads `comp(ICUI.PANEL) or ICUI.last_panel`, so the line was
dead. **The code went, not the check.** One anchor went stale from that edit and
was re-aimed.

| instrument | result |
|---|---|
| `_iron_court_harness.lua` | **346 checks, ok** |
| `mutate_iron_court.py` | **68 mutants, 0 unexplained** |
| `gen_ic_ui.py --check` | ok, 220 components |
| `preview_iron_court.py`, five renders | ok |
| `luac -p`, `check_lua_api.py`, `check_lua_undeclared.py` | clean |
| pack | 7,706,027 bytes, deployed, probe confirmed **inside the binary** |

### 14f. What the next launch settles

Either the panel opens - in which case the strip withdrawal plus something else
was the whole of it - or it does not, and `XXX derpy_ic BAD UI LAYER ... XXX`
in the script log names the fault in one line. Either way the campaign is
playable: the HUD comes back, the panel removes itself, and the flood stops at
one error instead of 27,346.

**The strip stays withdrawn for this launch only.** It is exonerated and it
should come back - but not in the same build as the probe, or the launch answers
nothing.

---

## 15. Reverted, and what eight instrumented builds actually established

`data/derpy_iron_court.pack` is back to the 2026-09-15 build (7,646,430 bytes,
hash-verified, none of the instrumentation in it). The last broken build is kept
as `scratchpad/broken_20260916_2248.pack`.

### 15a. Three theories, all killed by measurement

**The action strip.** Withdrawn; the next build failed identically. Exonerated.

**Hiding the campaign HUD.** `show_hud(false)` walks the ui ROOT and switched 13
of the game's own children off, and three sessions put the first error 200ms
after it. It was replaced by `PropagatePriority(150)` - measured against the
game's own `[ui]` dumps, where the highest priority anywhere in the campaign HUD
is 100. **The panel then opened and stayed open with the HUD intact, and the
cards were still empty.** Worth keeping on its own merits; not the cause.

**A lookup ceiling.** The strongest-looking one, and wrong. Two sessions died on
the 841st `find_uicomponent` of the frame (`layout cost 626` + `lookups=214`),
always on `comp("ic_party_leader", card)` with the card passing `is_uicomponent`
on the line before. Indexing the panel with one `ChildCount()`/`Find(i)` walk took
it to `layout cost 3` and `lookups=1` - **about 5 lookups instead of 841** - and
it failed in exactly the same place. There is no ceiling.

### 15b. What the instruments cost, and the four that could not work

Four instruments in a row wrote nothing, because **CA's entire script-logging
subsystem stops when the error flood starts**: the 21:53 log has zero `[out]`
lines from ANY mod after 154.5s in a session that ran to 184.6s. The comp-miss
line, `draw done`, `probe_layer` and a watchdog-flushed trace all tried to speak
AT or AFTER the failure. Only announcing each lookup BEFORE making it worked, and
that is the shape any future instrument here has to take.

Two Lua traps cost a build each. `UIComponent(address)` **mints a new userdata
every call**, and Lua keys userdata by identity - so a cache keyed on handles can
never be read by a caller holding a handle from `find_uicomponent`, though both
describe one component. It looked correct in the harness because fake components
are tables, and a table passed around is the same table. And `open()` finishes by
calling `refresh`, which zeroes the lookup counter, so a check reading it after
`open()` measured the draw and could not see its own mutant.

### 15c. Where it actually is, and it is checkable offline

`layout()` found nearly everything from the index (3 real lookups), so the walk
saw the card's children. `comp("ic_party_leader", card)` still had to search,
which means **that component was not in the index - the walk never saw it.** The
walk does not search; it enumerates. So the engine creates only SOME of what
`derpy_ic_party.twui.xml` declares - crest, name, name2, port, mood - and drops
`leader`, `ltrait`, `nums`, `t1`, `t2`, `off` silently.

That is a file fault, not a script one, and **no launch is needed to pursue it**:
compare the six that survive against the six that do not, in the packed XML, for
whatever the engine is rejecting.

### 15d. Worth keeping from this session regardless

- A caught draw error goes to the LOG, not only to `ic_alert` - a component,
  unfindable in exactly the failure where the message matters.
- `close()` can reach its panel through `ICUI.last_panel` when the lookup fails.
- `refresh` tells a shut panel from an unfindable one instead of returning
  quietly forever with the HUD hidden.
- A short HUD restore switches every root child back on, deliberately
  over-restoring: one stray HUD element beats a campaign with no interface.
- `each_root_child` does not filter on `is_uicomponent` - the exact test that
  goes wrong in this failure.
- The panel does not tear itself down over a failed string comparison. That
  regression made the button do nothing for three builds.

351 checks, 77 mutants, 0 unexplained.
