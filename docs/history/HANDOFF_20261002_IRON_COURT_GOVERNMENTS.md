# Iron Court governments - built (2026-10-02)

Spec `docs/superpowers/specs/2026-10-02-iron-court-governments-design.md`; plan
`docs/superpowers/plans/2026-10-02-iron-court-governments.md`, executed natively, with one fresh
review at the end. The author asked to "brainstorm for adding types of government". Then: "type of
government should be mixed and not fixed, the player can change doctrine". Then: "then do native
driven".

## 1. Build and deploy

- `FEA1936D` (MD5 `FEA1936DC34023ABE1131A10F99F3A40`, 9,786,842 bytes, 1797 files verified in the
  saved pack), deployed to data/ byte-identical at 13:18. Backup
  `.bak_pre_auto_20261002_131804` holds `9A66C3C8`. The live pack was read back: the model,
  panel, twui, both DB tables and the loc all carry the new keys.
- **Not pushed.** `tools/sync_iron_court_repo.py` now lists the spec, the plan and this handoff.
  Sync, update CHANGELOG and DEVELOPMENT (892 checks, 1030 mutants), then commit when the author
  asks.

## 2. What it does

- **Six governments** (`IC.GOVS`, in `IC.GOV_ORDER` order):
  - the Conclave (tower);
  - Rule of the High Priest (temple);
  - Rule of the Daemonsmiths (forge);
  - Command of the Legion (legion);
  - Rule of the Slave-Lords (chain);
  - the Convoy Concern (road and ledger).

  Each one bends one court rule through `over` (a number, or `{mul = x}` against the base) and
  carries a faction bundle `derpy_ic_doctrine_<slug>`. There is no Crown or Hearth government:
  neither has a lore basis.
- **`IC.tune(faction_key, key)`** returns the court's override, or `IC.TUNE[key]`. Every read of
  an overridden key goes through it. A harness check scans the four court files for a literal
  `IC.TUNE.<key>` read; it skips the `IC.PLOTS` catalogue, whose embezzle line the panel
  rewords through `ICUI.plot_effect`.
  - `IC.plot_cost`, `IC.favour_cost`, `IC.gov_rank_bonus` and `IC.trickle_for` gained an
    optional faction argument.
  - The battle and rank listeners read the faction before they price anything.
- **Starts.**
  - `IC.START_GOV` covers 14 houses; Uzkulak and the Kraken are inference.
  - Any other court derives its start: its strongest rival's government, else the Conclave.
  - The start is set at the court's first turn. A save from before governments gets one at its
    next turn, and no pressure builds on that turn.
- **Drift** (`IC.gov_turn`) runs on player courts only, through `IC.gov_step` before
  `tick_pressure` in `IC.turn`.
  - A rival party at `gov_drift_share` (30%) or more that leads with a government of its own
    builds +1 pressure toward that government.
  - A different leader restarts the count. So does the current government's own party leading.
  - A leader with no government (the Crown, the Hearth, a confederate origin) builds nothing
    and resets nothing, at any share.
  - If no rival is at the share, the court pulls toward the Conclave one point every 2 turns.
  - Drift is frozen in the grace period, during a cooldown, and while a choice waits.
- **The choice** comes when pressure reaches `gov_pressure_line`: a Petitions row (the first
  row) and a `gov_pressure` event.
  - **Accept:** +10 loyalty for the new government's party, -10 for the old one's.
  - **Hold:** 300 x (1 + holds so far) influence; pressure drops to half the line; the party that
    asked loses 8 loyalty.
  - **No answer for 3 turns:** the court accepts. This is decided inside the turn, so every
    machine settles it the same way.
  - **Lapse:** a choice the court no longer pulls toward lapses, at the turn and also at the click
    (`IC.gov_ask_live`). A party that leaves during the turn cannot be paid off.
- **Change Doctrine** is a button in the Crown's box that opens a picker of the other five, each
  with its price, its loyalty effects in this court, and its faction effect in the tooltip.
  - Cost: 400 influence. The dropped government's party loses 15 loyalty; the new one's party
    gains 5 if it sits in the court. Then a 15-turn cooldown.
  - **Paying, for Hold and Change Doctrine alike, spends only the Crown men's influence above
    their own seat's bar**, richest first (`IC.crown_purse` / `IC.spend_crown`). It refuses
    rather than unseat anyone.
- **Save.** Field 14 holds `gov, pressure, toward, cool, holds, askgov, askends, askparty`, with
  `-` for none.
- **Settings.** Two live switches, "Governments" and "Governments change with the court".
  - Governments off removes the bundle and the overrides and drops any waiting choice.
  - Drift off drops a waiting choice.
  - Both settle on the MCT flip.
  - Three new numbers are on the presets and the Custom page: the pressure line and the Hold and
    Change prices.
- **Panel and data.**
  - Panel: the government row `ic_gov` and the `ic_gov_btn` button in the Crown's box, which
    grew from 258 to 300 tall. Its tooltip gives the rule, the effect, and a turn count only
    while the court is moving.
  - Help: a "Governments" topic, and Help figures now come through `IC.tune`.
  - Record: five log kinds, `doctrine*` (because `gov_on` and `gov_off` are the governors').
  - Data: events `gov_changed` (2629) and `gov_pressure` (2630).
- **AI courts** get the start government, its bundle and its rule. They do not drift and do not
  choose.

## 3. Verified, and how

- Harness `_iron_court_harness.lua`: 892 checks, green, each new one watched failing first. The
  harness runs with governments **off** by default (`IC_GOVS_ON`), because its test faction is
  Uzkulak, whose Convoy start would move every favour price the older checks pin.
- Mutants: 1030.
  - All 34 `gov:` mutants are caught.
  - A full run found 7 anchors that this pass had made stale; all are re-aimed and caught.
  - It also found **3 survivors that predate this pass** (see section 5).
- Gates pass:
  - `gen_iron_court` `--check` and `--selftest` (53 bundles, 968 loc rows);
  - `gen_ic_ui` `--check` and `--selftest` (632 components, 2547 guids);
  - `preview_iron_court --check`;
  - the `import_iron_court` gate;
  - luac, `check_lua_api` and `check_lua_literal_left` are clean; `check_lua_undeclared` is
    unchanged from before the pass.
- The preview was drawn at 1920 and 1600. The longest name, "Rule of the Daemonsmiths", and
  "Change Doctrine" both fit.
- **Final review** (fresh reviewer, opus) found 0 Critical and 4 Important issues; three Minors
  were regraded to Important. All seven are fixed, each through a check that failed first: Help
  numbers; a choice its party left mid-turn; drift off leaving a waiting choice; the government's
  own party not resetting the count; the tooltip counting points as turns; text for a choice no
  party asked for; the faction effect shown nowhere. "Standing" was also removed from the Legion
  bundle text.

## 4. Do not re-derive

- `derpy_ic_gov_*` is the **governors'** bundle stem (`derpy_ic_gov_base`,
  `derpy_ic_gov_house_*`). Governments use `derpy_ic_doctrine_*`, and
  `gen_iron_court.check_governments()` holds the model's stem and order to the generator's.
- `IC.TUNE_ORDER` is checked against the MCT page by the harness and the gate, so a new setting
  is three edits: `IC.TUNE`, `IC.TUNE_ORDER` (append only) and the MCT file, plus
  `PRESET_VALUES` and the harness `LIVE` list for a live switch.
- `IC.turn` reloads the court from the save first. A check that sets court state and then calls
  `IC.turn` has to `IC.save(F)` first, or it tests a court that never existed.
- The compact layout pass refuses a layout constant that is neither in `SCALED_SCALARS` nor
  `NOT_GEOMETRY`.
- `preview_iron_court.py` supplies demo text per cell and does not run the Lua. A new cell draws
  empty until it is given text there.

## 5. Still open

- **In game, owed:**
  - the government row and its tooltip;
  - Change Doctrine and its picker, with the event card;
  - a choice building to the line and appearing on Petitions;
  - Hold paid from the Crown men's influence;
  - an older save taking its start government;
  - the bundle in Faction Effects;
  - the two switches flipped mid-campaign.
- **Pre-existing mutant survivors** (they survive on the pre-change files too; from the known-bug
  pass): "buttons the engine greyed lit by the court" (edict relight), "a spare row left showing"
  (Governors column), "the line memo kept across a new list". Each needs a check that the
  mutation breaks.
- **Deferred minors from the review:**
  - Hold angers the party that first asked, not the current leader. With the Convoy, if Road has
    gone and the Ledger leads, Hold costs no loyalty.
  - Income and governor bundles run before `gov_step`, so a start or a turn-start Accept pays
    under the old rules for one turn.
  - The scan misses `local T = IC.TUNE` aliases.
  - A stale "THE DEMAND FIRST" comment remains.
- **Open from the spec:** Khorakk follows the loc (slave drivers, `chain`) rather than the
  court's "bull-cult" line; the two Convoy starts are inference.

## 6. The government line labelled (2026-10-02, later)

The author's first look in game (Ghorth, a Conclave court): "theres no indication in the court
what type of government is currently". The row was drawn, but it read "The Conclave" with no
label, next to party names such as "Servants of the Conclave" and "Conclave of the Bull's
Horn". It now reads "Government: <name>" and runs from the box's left edge to 24px short of
Change Doctrine (622px at 1920). The longest name fits at 1600. One harness assertion and one
mutant cover it. The script log for that session showed normal court activity and no errors.
The WH3 bridge tools were not registered in this session.

## 7. A picture per government (2026-10-02, later)

The author: "add or generate icons for the types of government". CA's own 24px Chaos Dwarf
effect-bundle art covers all six, so none was generated and none ships: the pack names CA's
paths only.

| Government | `IC.GOVS[slug].icon` (under `ui/campaign ui/effect_bundles/`) |
|---|---|
| Conclave | `dlc23_region_action_gift_zhar.png` (the bull's head) |
| High Priest | `chd_toz_district_sorcery.png` |
| Daemonsmiths | `chd_hellforge.png` |
| Legion | `chd_toz_district_military.png` |
| Slave-Lords | `chd_labour.png` (the shackle) |
| Convoy Concern | `dlc23_region_action_sell_labour.png` (the coins) |

- **One source.** The `icon` field in `IC.GOVS` feeds three places:
  - `ICUI.gov_icon(slug)` turns it into the full path. The government line and the
    Change Doctrine picker rows both draw it, the rows as `icon_kind = "crest"`, as the envoy
    tasks do.
  - `gen_iron_court.model_gov_icons()` reads it into each `derpy_ic_doctrine_*` bundle's
    `ui_icon`, so Faction Effects shows the same picture.
  - `check_governments()` fails a bundle that wears any other picture, and check 4b holds the
    file to a pack.
- **Two pictures kept off on purpose.** `chd_toz_tier` is the band and Crown icon
  (`ICUI.BAND_ICON`). `chd_conclave_influence` is the trait icon and the default bundle icon.
  A harness check fails a government that shares either, or that shares a picture with another
  government.
- The Petitions row keeps the crest of the party asking, because it says who asks.
- `gen_ic_ui`'s inline-icon sweep reads one line at a time. `ICUI.gov_icon(` is on its list of
  indirections, and it has to share a line with the `[[img:%s]]` it fills.
- Harness: 893 checks. Mutants: two new ones (the band's picture back on the line, and picker
  rows without one), and two re-aimed after the line moved. All 37 `gov:` mutants are caught.

## 8. Deeds move the court (2026-10-02, later)

The author asked: "what else is missing, how do we engage the player into using the system".
They chose governments as "a mirror of play", deeds working through the parties, and absent
parties coming to the court.

- Spec: `docs/superpowers/specs/2026-10-02-iron-court-deeds-design.md`.
- Plan: `docs/superpowers/plans/2026-10-02-iron-court-deeds.md`, executed natively.
- Ledger: `.superpowers/sdd/2026-10-02-iron-court-deeds/progress.md`. It holds every ruling, and
  `base/` holds the pre-change files.

### Renown

- **What it is.** A player court's parties hold `court.renown[party]`. `IC.house_weight` adds it,
  so a party's share rises with its renown, and the existing drift carries that to the
  government.
- **The deeds** (`IC.DEEDS`, `IC.deed(faction_key, code)`):

| Deed | Party | Renown |
|---|---|---|
| battle won (once per battle, keyed on the two commanders) | Legion | 3 |
| Hell-Forge cap ritual | Forge | 4 |
| Tower rite (`DISTRICTS_*`, `TOZ_TIER_4`) | Priesthood | 4 |
| temple of Hashut built | Priesthood | 2 |
| captives enslaved (`enslave_slaves_only`) | Chain | 3 |
| settlement razed | Chain | 3 |
| convoy completed | Road, else Ledger | 5 |
| technology researched | Tower | 2 |

- **Fade and limit.** Renown fades 25% a turn, at least 1. A party gains at most 6 in one turn,
  and the limit is saved, so a mid-turn reload does not reset it.
- **Player courts only.** AI courts score nothing.
- **Leaving.** A party that leaves (purge, secession, dissolve) loses its renown.

### A party drawn in

- At 15 renown, an absent party waits. The next lord created who can lead and has no fixed
  history joins it, through `IC.deed_join` in `ic_born`.
- It needs room: fewer than `rivals_max` rivals. Of two waiting parties, the one with more renown
  comes first.
- It raises `party_drawn` (2632), with a secondary line per party.

### What the player sees

- **The introduction card** `gov_intro` (2631) fires once per player court, including a court
  that already had a government.
- **The government line** gains `-> [icon] n/6` only while the court is moving.
- **The government tooltip** lists what moves the court, with each party's renown, and the absent
  parties: "would come at 15", "joins with the next lord you recruit", or "your court is full".
- **Party card and crest tooltips** show renown.
- **The Record** gains log kinds `deed` (summed per party, deed and turn) and `drawn`.
- **Help** gains five lines in the Governments topic.
- **The live switch** "Your deeds move the court" (`deeds`). Off, nothing new is earned, nobody is
  drawn in, and held renown fades away.

### Save

- Field 15: `party,renown,got` entries.
- Field 16: `intro,confed_turn`.
- Both are optional, and old saves load empty.

### Verified

- Harness: 925 checks, each new one watched failing first.
- Mutants: 19 `deed:` and 37 `gov:`, all caught.
- Gates: `gen_iron_court` `--check`/`--selftest` (981 loc rows), `gen_ic_ui` `--check`/`--selftest`,
  `preview_iron_court --check`, the import gate, luac, `check_lua_api` and
  `check_lua_literal_left` are all clean. `check_lua_undeclared` is unchanged.
- The drift segment was rendered at 1920 and 1600 with the longest government name, and fits.
- A fresh reviewer (opus) found 0 Critical and 3 Important issues. Three Minors were regraded to
  Important. All six are fixed, each through a check that failed first:
  - a purged party being drawn straight back;
  - renown at about 80 per party, which cut the Crown's control; retuned from 10%/8/20 to
    25%/6/15, and **the author should confirm the feel in play**;
  - the Record summing only the last entry;
  - cards naming the Daemonsmiths and the Slave-Lords instead of the Forge and the Chain;
  - the waiting-party tooltip;
  - empty courts built for factions with none.

### Owed in game

- the captive outcome key;
- `ResearchCompleted` firing for the player;
- a convoy counting once;
- the introduction card;
- a party drawn in by a recruit;
- the drift segment on the line;
- the switch flipped mid-campaign;
- the confederation guard against CA's tier-4 re-perform order;
- whether `CharacterCreated` fires for a garrison commander (`IC.can_lead` accepts colonels).

### Deferred minors

- `ICUI.DEED_TEXT` splits `intrigue_text`'s doc comment.
- With governments off, the deeds block has nowhere to show.
- The intro text describes deeds even with deeds off.
- `confed_turn` is unsaved when a confederation has no mapped origin (it only matters within the
  turn).

## 9. Laws and votes (2026-10-02, later)

Sub-project 1 of 2: Bannerlord-style laws. The second, votes on seats and governors, is not built.

- Spec: `docs/superpowers/specs/2026-10-02-iron-court-laws-design.md`. Its section 4 was brought
  in line with the shipped layout.
- Plan: `docs/superpowers/plans/2026-10-02-iron-court-laws.md`, executed natively.
- Ledger: `.superpowers/sdd/2026-10-02-iron-court-laws/progress.md`. It holds every ruling, and
  `base/` holds the pre-change files.
- Built as `85582182` (10,240,710 bytes, 1,801 files) after the final review's fixes. The game
  was running, so `deploy_iron_court.py --deploy-only --wait` copies it to `data/` when the game
  closes; `data/` held the pre-fix `E105D925` until then. No Workshop entry exists. Not pushed.

### What it does

- **Four categories, five options each** (`IC.LAWS`, `IC.LAW_ORDER`): Labour, Tribute, Worship,
  War. Each category starts on an option with no effects. Every other option has two upsides
  and one downside, as a `derpy_ic_law_<cat>_<opt>` bundle (20 bundles). One law per category
  is in force, and AI courts wear none.
- **A vote** lasts 2 turns. Each man votes with his own influence on his party's line:
  - for or against, where the law names the party;
  - with the Crown at loyalty 60+;
  - against it below 40;
  - otherwise he abstains.
  
  Ties fail.
- **The Crown** can:
  - propose (150 from its men's spare influence);
  - take a side;
  - push its support (100/250/500 for x1.5/x2/x3);
  - win single men (half their influence, scaled by ambition, doubled if they are against you);
  - overrule (500, and -10 loyalty to the losing parties).
- **Parties** propose laws they are for, at 15% of the court, with a 6-turn rest. A party with a
  stake pushes one step a turn when losing or close.
- **The Laws tab:**
  - a board of 20 cards, each wearing CA's 72px Chaos Dwarf tech painting (`ICUI.LAW_ART`);
  - a detail pane with the projected vote;
  - a vote screen with the support bar, party blocks, and the Crown's hand.
- **Plumbing:**
  - the live switch `laws`;
  - save fields 17/18;
  - events 2633-2635;
  - six Record kinds;
  - five multiplayer ops;
  - a Help topic.

### Found at the end, fixed

- **The layout clipped.** The preview drew every law screen from the shipped Lua through a new
  harness dump (`IC_DUMP`) and showed the card effect lines leaving the card. New check 20k in
  `gen_ic_ui.py` measures every string the tab draws against its cell. It found 83 clipped at
  1920 and 105 at 1600; there are now 0 at 1600, 1920 and 2560.
  - The relayout: names over two lines beside the icon, effects across the full card, pane
    effects over two rows each, and three men per block with an influence-or-Win line.
  - The wording: short verdicts on the pane, "(absent)", and "XP vs Dwarfs".
- **The abstain line** named every abstaining party. It now names up to two and counts past that.
- **Blurry icons** (author): the panel uses CA's 72px tech art. The bundles keep their 24px icons.

### Verified

- Harness: 964 checks.
- A fresh reviewer (opus) found 0 Critical issues and 1 Important one, and two Minors were
  regraded to Important. All three are fixed, each through a check that failed first:
  - the Laws tab now opens a party's vote that waits for an answer (spec 4.2, "from the marker");
  - a party's push margin is 10% of the votes cast, without the abstainers;
  - "Forge cap cost" became "Forge upgrade cost", and a new plain-words check covers the law text.
- The five deferred minors, closed 2026-10-03:
  - a won man keeps his side if the Crown switches. That is the spec (3.3), so the behaviour
    stands: a new harness check pins it, and an 11th Laws Help line tells the player;
  - 20k and the art check now FAIL when there is no font or ui pack, as `cannot measure card
    text` already did, and the `gen_ic_ui` selftest proves both;
  - the bar cannot overflow: the slider allows at most 5 rivals, which makes 11 groups for 12
    slots. New `check_law_bar()` fails the build if `LAW_SEGS < 1 + 2 * rivals_max`;
  - undecided men: a spec note in 4.2 says the screen does not reach them in this version;
  - `law_settle` walks the law's own for and against lists instead of `pairs(court.houses)`.
    A new check runs all 20 laws; it was RED on `labour.kept`.
- Found on the way: the Laws topic filled the 12th Help slot, so "spare topic buttons hidden"
  had no spare left to test. The check now drops a topic so a spare exists. Three mutants
  (`an AI court rolled after its men were dealt`, `live: the log switch dropped from the live
  set`, `the rest not saved`) had been stale since the deeds work; all three are re-aimed and
  caught.
- The full run (1083 mutants) then left three survivors. None was in law code, and the map
  panel file has not changed since before the laws work:
  - `the line memo kept across a new list`: under the mutant, an earlier check's memo
    suppressed even the first write, so the check compared "" with "". It now asserts the line
    was drawn first.
  - `a spare row left showing`: spare cards exist only in the no-list fallback, which nothing
    exercised. New check: "with no list the cards fall back onto the panel...".
  - `buttons the engine greyed lit by the court`: equivalent since the by-id rewrite, because a
    false memo throws inside the pcall. Re-aimed at the per-button `mine[c:Id()]` rule.
  - All three are caught; harness 967; the runner selftest has all 1083 anchored.
- **Category heads as titles** (author, 2026-10-03): "Labour", "Tribute", "Worship" and "War"
  were full-width card plates with an icon and left-aligned words. Each is now one cell on
  the heading plate the Intrigue move groups use. The name is in capitals, and `fit_plate`
  sizes the plate to its words and centres it on the column. The icon cells and the four
  category pictures in `LAW_ART` are gone; nothing else drew them. `make_ic_backdrop` now
  measures the heads.
- A full mutation run cut off by a session end left one mutant live in the shipped model (the
  legend murder guard deleted). It was restored by hand and every anchor rechecked. **Back up
  the shipped Lua before a full mutation run:** the runner's `finally` does not survive a
  killed process.
- Mutants: 25 `law:` plus the re-aimed pulse mutant, all caught. Two survived at first, and
  both checks were strengthened.
- Gates, all clean:
  - `gen_iron_court` `--check`/`--selftest` (73 bundles, 112 junctions, 1116 loc);
  - `gen_ic_ui` `--check`/`--selftest`;
  - `preview_iron_court` `--check`/`--selftest`;
  - the import gate;
  - luac on all five files;
  - the three Lua linters (baseline unchanged);
  - `check_effect_bundle_loc` (0 findings).
- `check_effect_signs` lists 16 penalty rows, one per law with effects, and each is that law's
  designed downside.

### Owed in game

- the Tower seat cost at -25%;
- captives at -10%;
- the two scripted convoy effects;
- the Hell-Forge cost effect beside the caps pack;
- the gold frame's offset on a law card;
- the support bar at a court of nine parties;
- `fit_two` splitting the longest law names on the card (the preview cannot, because the harness
  measures with a linear stub).

## 10. Government cards, grey absent parties, the Offices title (2026-10-03)

Three author requests, all built in one pass, then four more the same afternoon. Build IDs
here are the MD5's first eight digits, as the repo CHANGELOG uses (earlier sections mix in other
hashes). Deployed in turn: `A08AC983` (the cards), `5B9242D2` (upscaled pictures, the Ziggurat
title, the pane bar), `74A26316` (no growth) and `47E345D7` (the rival counts; 10,905,484
bytes, 1,817 files, byte-identical in `data/`, the previous pack backed up as
`derpy_iron_court.pack.bak_pre_auto_20261003_143444`). Not pushed.

- **Change Doctrine opens five cards, not a list** (author chose design A of three mockups).
  - `ICUI.gov_choices` lists every government except the current one, with its refusal and
    its loyalty hits in this court. `ICUI.draw_gov_cards` draws them.
  - Each card has CA's 72px tech picture (`ICUI.GOV_ART`), the name over two cells, the rule
    over `GC_RULE_LINES` cells via `fit_lines`, the effect, up to `GC_LOY_LINES` loyalty lines,
    and a Choose button with the price, or the refusal in red.
  - A title above the cards ("NOW: ...") names the government in force, with its rule and
    effect under it.
  - Clicking a card sends the same `doctrine` message the old rows did.
  - The cells are `ic_gc_*` in `PANEL_LAYOUT` (`gov_card_cells()`), shown only while the
    doctrine pick is up. The picker's doctrine rows, its header strip and its
    `MISSION_PICKS` entry are gone.
- **The card pictures are upscaled** (author, 2026-10-03, route A of two mockups). CA ships its
  Chaos Dwarf tech icons at 72px only. `gen_ic_ui.cut_chd_art` writes each `ICUI.GOV_ART` source
  at 224px to `ui/derpy_ic/gov_<slug>.png` (two Lanczos steps with an unsharp pass between), and
  the panel draws those (`ICUI.GOV_ART_FILE`). Route B, medallions from CA's larger art, was
  turned down: the only big, crisp CHD art is mostly faction banners.
- **The loyalty line leads with its number.** 20k caught the longest rolled party name
  running off the card at every size. The line is now `+5  [crest]Name`, and only the name is
  cut (`ICUI.cut_text` with the room left after the number and crest). The whole name is in
  the tooltip. A confederate party wears a faction's name, which can be any length.
- **Absent parties on the laws tab are greyed:** `ICUI.law_crest` draws a grey sigil
  (`party_sigil_<slug>_absent.png`, `ABSENT_DIM` 0.6, written by `build_plates`) for any party
  not seated in this court.
- **"THE ZIGGURAT OF ZHARR"** is a fitted title plate (`ic_off_title`) on the ziggurat's top
  step, shown on the Offices tab only. It first read "THE SEATS OF OFFICE"; the author picked
  this from four thematic choices. 20k now measures it.
- **No growth anywhere in the court** (author: "growth is useless for chaos dwarf"). The five uses
  are replaced with effects CA ships at the same scope, picked by the author:
  - the High Priest government: Conclave Influence +10% (CA's own Astragoth effect);
  - a Priesthood governor: CA's slave-driven Control +3 (`wh3_dlc23_effect_public_order_slaves`);
  - every governor's base: Workload -5% (Control +2 stays);
  - the Iron Grip and Court Is Not Yours bands: Conclave Influence +5% and -5%.
  `E_GROWTH` is gone from `gen_iron_court.py`, and the Crown block's icon for "Growth" is now
  "Conclave Influence".
- **Fewer rivals by default** (author, 2026-10-03): Gentle 1, Default 2 (was 3), Harsh 3
  (was 4), and Ruthless renamed "Political Chaos" with 5. The preset keys are unchanged
  (`ruthless` still), so saved MCT settings carry over. Both copies, `IC.TUNE_DEFAULTS`/`IC.PRESETS`
  and the MCT file's sliders/`PRESET_VALUES`, moved together, and the Help line names the new
  preset. Only new courts roll the new size; a running campaign keeps its court.
- **The laws pane's projection has a bar** (author, 2026-10-03). Under "If it went to the court
  now", aye fills from the left in green and nay from the right in red. The grey ground between
  is the share that would abstain. `ICUI.draw_law_pbar` moves and sizes the two sides. The cells
  are `ic_law_p_bar`, `_baraye` and `_barnay`; the plates are `law_bar_aye`/`_nay.png`. The
  five party lines sit 20px lower to make room.

### Verified

- Harness 971 checks. New: the card loyalty line (number first, long name cut, tooltip), the
  five cards opening and sending, the refused card's red button doing nothing, the absent grey
  crest, and the Offices title.
- `gen_ic_ui`: 20k measures every card string at 1600, 1920 and 2560, including a greedy wrap
  of each rule into its four cells. `check_law_art` covers `GOV_ART`. The selftest proves both
  checks fail on a missing government picture.
- `make_ic_backdrop` measures the card headings. The import gate is clean. luac and the three
  linters are clean (same baseline as before).
- Full mutation run: 1087 mutants, 4 survivors, all in the new card code and all from harness
  gaps. A refused click was only checked for "nothing changed" (the model refuses too), a card
  naming an unseated party was never looked at, the button tooltip was never read, and a sixth
  choice fell off the fifth card uncounted. Each test was strengthened and all four are now
  caught. Two more mutants cover the loyalty cut, so the total is 1089, all caught. Three stale
  ones were re-aimed.
- `preview_iron_court` draws `ic_gov_cards.png` from the harness dump. Its rule lines are split
  by the harness's linear stub, so they overrun the cards in the picture. In game `fit_lines`
  measures with the engine.

### Owed in game

- the rule lines wrapping inside the card;
- the loyalty cut on a confederate party's faction name;
- the grey sigils reading as absent rather than as disabled.
- ~~the support bar's border~~ - seen working in game 2026-10-03 (section 11).

## 11. A border on the laws pane's support bar (2026-10-03)

Author: "add borders to the bar"; **seen working in game the same day**. Build `65333E8C`, deployed to data/ (backup
`.bak_pre_auto_20261003_153741` holds `47E345D7`), not pushed. One new cell, `ic_law_p_barrim`, on
the bar's box: `law_bar_rim.png`, the portrait frame's bronze thinned to two pixels between two dark
lines (`LAW_PBAR_RIM_BAND`), drawn 3px outside the bar so only its inner dark line covers the 14px.
It sorts after `ic_law_p_barnay`, so it draws over both sides; `check_law_bar` now refuses the
opposite order, and the harness check on the pane bar asserts it is shown on the bar's box (both
seen failing). Harness 972. The vote screen's `ic_lv_bar` has no border yet.
