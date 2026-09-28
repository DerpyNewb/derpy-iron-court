# Changelog

Builds of `derpy_iron_court.pack`, newest first. The detail behind each entry is in
`docs/history/`. The pack has only ever been deployed to the game's `data/` folder; none of
these builds is on the Steam Workshop. Early builds recorded a SHA-256 or only a size, not
an MD5.

## 2026-09-28 - build 3DFB28D1

Deployed 2026-09-28. MD5 `3DFB28D14E443B25615B8C703993D221`, 9,382,627 bytes. It gathers
62C28B4D; the detail is in the last addenda of
`docs/history/HANDOFF_20260925_IRON_COURT_MCT_MULTIPLAYER.md`.

- **The court button says why it is glowing.** Its tooltip opens with "Waiting for you:"
  and each reason with the tab to open, then the summary.
- **Empty seats glow only when someone can take them.** The button and the Offices tab
  follow the Fill button's own plan (rank, one post per man, the claimed-seat rule, and for
  the player's men the seat's influence), so a young court whose every seat is empty for
  want of influence no longer glows every turn. The summary still counts every empty seat.
- **Tests.** A full mutation run (629 mutants) caught everything but two stale anchors,
  both retargeted onto the rewritten lines and caught.

## 2026-09-28 - build B6E69375

Deployed 2026-09-28. MD5 `B6E693757B1E83F2D9A88BAC946EE3B6`, 9,381,355 bytes. It gathers the
builds since 7B34D727 (9588EE3E, 52BCA382, 2BA85110, 4CB01AE8, A431EEF1, F29A1A11); the detail
is in the addenda at the end of `docs/history/HANDOFF_20260925_IRON_COURT_MCT_MULTIPLAYER.md`.

- **Help page.** A gold question mark beside the court's name opens a topic list and a page:
  parties, influence, loyalty, offices, governors, the Crown, intrigue, petitions, leaving
  the court and settings. Its numbers are read from the campaign's own settings.
- **Edicts need a governor.** A province with no governor has its edict buttons greyed out
  until one is appointed, and a note beside them says so. An edict already running is not
  cancelled; no script call can cancel one.
- **The court button rests between turns.** Greyed and shut while other factions move, like
  the Exchange's; ending the turn closes the court.
- **The character panel's influence plate** sits on the Hell-Forge plate the court uses for
  the same figure, sized to its words, and follows the character picked inside the panel.
- **Rebels fight,** with the Chaos Dwarf endgame invasion's war plan.
- **Recruit officers from the recruitment panel.** Hiring left the office list; a recruit
  joins with influence by level (100 to level 5, 200 at 12, 300 at 20, 400 at 30).
- **The Crown's block** has an icon on every line and rules between them; portrait frames
  are thicker.
- **Tools.** `deploy_iron_court.py` backs the live pack up, byte-compares the copy, can wait
  for the game to close (`--wait`), ships the last build (`--deploy-only`), has a
  `--selftest`, and refuses an unknown argument. `check_lua_api.py` flags an anchored
  `string.find` pattern, which returns nothing at all in WH3's Lua. The harness's
  `core:add_listener` stub now drops a listener registered without its persist flag, the way
  the engine does; that is what let the edict lock grey only the first settlement selected.

## 2026-09-28 - build 7B34D727

Deployed 2026-09-28. MD5 `7B34D7270FFCE04271B2142FB99A756F`, 9,240,059 bytes. It gathers the
builds since 5B0F8999 (160A02AE, 67CB2EC7, 6406707F, A54792C5); the detail is in the last
three addenda of `docs/history/HANDOFF_20260925_IRON_COURT_MCT_MULTIPLAYER.md`, and the
feedback design and plan are in `docs/design/` and `docs/plans/`, argued from
`docs/history/CA_CHD_UI_FX_20260928.md` and `IC_FEEDBACK_AUDIT_20260928.md`.

- **Seats glow.** A held office wears a slowly breathing red edge (CA's Tower of Zharr glow,
  redrawn with square corners), dim while the seat is stalled. A governed province's row is
  lit, and dim while its governor is away.
- **Filling a seat is felt.** Appointing an officer or a governor plays CA's warband-upgrade
  starburst over it with the ritual sound. Releasing a governor is answered at last.
- **Answers in words.** Granting a demand, accepting an offer, settling a feud, a gift and an
  oath each say what happened, and the party's card lights up. A failed plot flashes its
  target party red.
- **Tabs show what is waiting,** with the Hell-Forge's heat glow on the tab's skull. The court
  button pulses while the court needs an answer, and its tooltip lists every reason.
- **What moved this turn.** A party's share and loyalty turn green or red since the turn
  began; the figure is on the hover.
- **Portrait frames:** the Hell-Forge's bronze unit-card frame on every portrait.
- **The Steward of the Ash Fields** now cuts Hobgoblin upkeep by 15% (5% dearer while
  vacant) instead of adding Growth.
- **Ten bug fixes** from the "what else is missing" review: AI courts wiped after a load,
  Ruthless never showing the last warning, dead courts padding the rotation, the sabotage
  message never firing, Chaos Dwarf news reaching other races, switches not fully off, the
  AI ruler skipping its gift on plot turns, and the governor tooltip ignoring absence.
- **Tests:** harness 713 checks, 560 mutants all anchored. A fresh final review found five
  faults the harness had been green over - each now has a check that failed first.

## 2026-09-27 - build 5B0F8999

Deployed 2026-09-27. MD5 `5B0F8999BEEB2FEF03DA6087FA8C41D5`, 9,195,929 bytes. It gathers the
builds in `data/` since D4CC1CE1 (86E7E611, 77344618, 9C190A43, 81506DDF, 1260D08A,
E9D6E2F0, 6B33E464, 50342536); the detail is in
`docs/history/HANDOFF_20260925_IRON_COURT_MCT_MULTIPLAYER.md` sections 14-19, and the living
courts design and plan are in `docs/design/` and `docs/plans/`.

- **The AI's courts act.** Their rival parties scheme, feud and make demands too, three AI
  courts a round in a fixed rotation so both machines of a multiplayer game agree. An AI
  ruler answers a demand at once and sends a gift to a party counting down, if the treasury
  allows. Offers and overseers' wages stay the player's.
- **News from other courts.** The Record tab lists what happens in the courts of Chaos Dwarf
  factions you have met, and a card with a camera button shows where one has split.
- **Sabotage and withholding.** A feuding party can switch off an office its enemy holds for
  three turns; an angry party can stop its men's offices working until it calms down or you
  Secure its loyalty. The office card says so in red and names who did it.
- **Settle a feud** on the Petitions tab: Back Them or Make Peace.
- **An overseer's bonus grows with his rank:** +1 public order per five ranks, +1% income
  per two, in his province. The bonus now also comes off a province when he leaves it; it
  used to stay.
- **A confederated court brings its loyalty,** weighted by its parties' weight and held to
  25-75.
- **Rebel armies are Chaos Dwarf armies.** A party that leaves with no lord of its own no
  longer rises as a copy of the ruler's stack. The host is rolled role by role - line,
  missile troops, hobgoblin screen, cavalry, beasts, war machines - with the units and
  weights of CA's Will of Hashut crisis, no more than two of one unit. A lord who leaves
  brings his own army, filled out the same way. Every other Chaos Dwarf faction now thinks
  less of the rebels too.
- **Parties are dealt evenly,** and a party of yours with no leader gets a lord on the map
  once.
- **A refused party waits five turns** before it demands again.
- **The panel wears the Hell-Forge's art,** with the Hell-Forge's title bar on each section
  and embers on every held office.
- **Send a Gift once per party per turn.** The victim list names why a man cannot be chosen
  in plain words, with the full reason in its tooltip, instead of reading Yours for all.
- Fixed: a province taken by a seceding party kept its old governor until the next turn.
- Built and then cut the same day: Chaos Dwarf vassals as a party of their own. The game has
  a vassal tab; a save that has one loses it on its next turn.

## 2026-09-25 - build D4CC1CE1

Deployed 2026-09-25, the last of several builds that day after 272C876B. MD5
`D4CC1CE112ABDE5256C024D538D60D8E`, 8,991,481 bytes.

- **Fixed: build 226121E7 crashed the game on every new campaign.** The settings page asked
  the game whether it was multiplayer while the campaign was still loading, before the game
  had built it. It now takes that answer from MCT, which works it out before the load starts.
  226121E7 was only ever in the author's `data/` folder.

- **An MCT settings page.** Difficulty (Gentle, Default, Harsh, Ruthless, Custom), seven
  switches and fourteen Custom numbers. The settings are fixed into the save when a campaign
  starts, except six switches that can be changed at any time in single player: rival
  parties acting, secession, pressure, your own party splitting, routine event messages and
  the detailed log. Switching one off stops any countdown it had running.
- **The difficulty sets the size of the court:** 1, 3, 4 or 5 rival parties. Ruthless fills
  the grid.
- **Multiplayer support.** Every panel action goes through the game's multiplayer channel
  and lands on both machines. MCT is not read in multiplayer. Not yet tried on two machines.
- **Offices are held for ten turns,** up from five. A man whose term ended cannot take the
  same seat for three turns, and his party gets no loyalty for the renewal.
- **Fill Empty Seats** on the Offices tab fills every empty seat by the court's own rules,
  and its tooltip lists each choice first.
- **Find** on a party's roster moves the camera to a man on the map.
- A card warns you the turn before a term ends. The court button's tooltip sums up the
  court. An empty seat's card says how long its last holder must wait. In single player the
  panel reopens on the tab you left it on.
- Fixed: a move could not fail unless the man making it held twice its price, so a purge
  landed while the panel showed 85%.
- Fixed: a court whose last rival was purged or seceded was rolled again at full size the
  next turn. The Crown now rules alone until it splits.
- Fixed: every ended term leaked six weight into the party that held the seat.
- Fixed: a fresh Ruthless court pushed a rival out from turn 1. Its pressure line is now 15.

## 2026-09-25 - build 272C876B

Deployed 2026-09-25. MD5 `272C876BFEC4A5D4F1AFFD3D79BA48BE`, 8,930,970 bytes.

- **Fixed: build 7EF8F281 broke the game's text handling the first time the court was
  opened.** The close button did nothing, the action bar showed blank plates, and CA's own
  UI scripts and other mods logged hundreds of errors. The action bar's visibility was
  handed `nil` instead of `false` when no party was chosen. The test harness now refuses
  any engine setter given something other than true or false.
- **Send a Gift is back,** as a fourth button on the party bar between Provoke and Secure
  Loyalty. It is red at 100 loyalty. With the pager showing, the bar now sits under the
  Crown's box.
- **Button and tab labels are title case.** The game draws capitals wider than the build
  check measured, so GOVERNORS and PETITIONS ran over their plates.
- The seats counter ("0 of 14 seats filled") sits on a plate of its own.
- Checked in a running game: the panel opens and closes, the text handling stays healthy,
  and the bar hides with nothing chosen and shows four buttons for a chosen rival.

## 2026-09-25 - build 7EF8F281

Deployed 2026-09-25 and replaced the same day by 272C876B (see above). MD5
`7EF8F281CED2C232BE1A5D455AE52859`, 8,922,887 bytes.

- The party bar is centred under the party cards, and moves beside the pager when there is
  one.
- The Crown's box is split in two: on the left, your share of the court, its band and the
  band's effects one to a line; on the right, the Crown's portrait, name, party and three
  traits.

## 2026-09-24 - build B5C21FF4

Deployed 2026-09-24. MD5 `B5C21FF4B9FC4B6F38CE1A0562582381`, 8,909,544 bytes. The first
build after game patch 9.0; the packing gate ran against the 9.0 packs.

- **Party cards are the control.** Click a card to choose it (it takes a gold frame), click
  again to see its members. A bar under the cards acts on the chosen rival: Provoke, Secure
  Loyalty and Purge the House, with the two moves aimed at its leader. A button the court
  will not allow is red and its tooltip says why.
- Provoke and Purge left the Intrigue tab for the bar.
- **The Petitions tab.** The live demand and every offer, each with Accept and Refuse.
  Accepting a demand seats the man in the office or province he asked for.
- More on each party card: its state, its leader and his trait, share, loyalty, loyalty a
  turn, and how many members, offices and overseers it has.
- Tabs are now Court, Offices, Governors, Intrigue, Petitions, Record.
- The favour list was removed, which left Send a Gift with no button until 272C876B.

## 2026-09-24 - panel scaling

Deployed 2026-09-24. 8,859,564 bytes, SHA-256 beginning `b5ac9c81`.

- **The panel is sized to the screen,** from 1600x900 up to 2560x1440. Below 1920 wide it
  uses a compact layout one font size down, since no script can change a font size.
- Fixed: on screens over 1080p a redraw dropped the panel's content offset.
- Fixed after the first run at 1600x900: the Intrigue tab stacked its move cards. The
  game's Lua compiler miscompiles a number on the left of an arithmetic operator in a large
  function; a new build check finds that shape.
- Thin light lines over the dial and the move cards were seen at 1600x900. Their cause was
  not found.

## 2026-09-23 - eight builds

The last deployed 2026-09-23. 8,588,591 bytes, SHA-256 beginning `9171c143`.

New:

- **The rival parties act on their own,** in the player's court, one thing a turn. They
  scheme against the Crown (rumours and discredit from loyalty 55 down, unseating your men
  or recalling your overseers from 25, murder from 10; the serious moves are warned a turn
  ahead), feud with each other over a stolen seat or an even share, demand an office or a
  province for one of their men as a five-turn mission, or offer gold, backing, calm or
  troops when content.
- Overseers gain 750 experience a turn. One who cannot gain rank, such as a garrison
  commander, is paid influence instead.

Fixed:

- **Every AI rival party was born empty,** because backgrounds were dealt before the court
  was rolled. A party with no leader now takes an idle lord, or has one made for it.
- A party with no men and no province dissolves with a card instead of seceding into an
  empty war.
- Party names take one Chaos Dwarf shape, such as *Keepers of the Black Ledger*.
- Influence came in too slowly (2 of 14 seats filled at turn 32). Earnings were raised, and
  garrison commanders now earn the turn trickle.
- An AI court no longer gives a party's claimed seat to an outsider while that party sits
  in court.
- Only a lord in the field can be away from the province he governs.
- Saves from earlier builds are repaired on load.
- The last "standing" in the panel's text is now "influence".

## 2026-09-20 to 2026-09-22

Several builds. The last deployed 2026-09-22: 8,512,170 bytes, SHA-256 beginning `ffdccd52`.

- **Ambition.** Every courtier is Cautious, Steady or Ambitious, which scales how much his
  influence adds to his party's share.
- **Military Doctrine.** A party whose overseer runs a province under that commandment
  gains 2 loyalty a turn.
- **Fixed: the panel was breaking other mods.** Its listener threw an error on every panel
  open and close, which stopped most other mods' panel listeners from running (31 of 40 on
  opening). Reported as another Workshop mod doing nothing; that mod was blameless.
- A province no longer asks any influence of its overseer.
- The AI can run its court: it fills offices from the claiming party first, fills its
  provinces, and is exempt from the player's influence bar and from pressure. In a measured
  120-turn run, AI courts went from keeping 3 or 4 of 9 parties to keeping 7.
- The player-facing text was rewritten in plain English.

## 2026-09-16 to 2026-09-18

The last deployed 2026-09-18, 8,672,151 bytes.

- **Six bugs from the first long live session.** Among them: the court ran in silence, so
  it now raises event cards (offices lost, plots, parties joining, secession warnings) and
  panel clicks answer with a sound; a vacant seat's line drew outside its card; a snub was
  written to the record every turn; the panel's wording was cut down to plain sentences.
- The currency was renamed from standing to influence. The character picker can be sorted,
  by party among others, and says whether each man is a general, a lord or a hero.
- **Secession bites.** A party at zero loyalty leaves with provinces, up to three lords at
  the head of armies and two heroes, takes its own name and goes to war. Getting there cost
  five crashes, fixed by making one world change per frame.
- **Four rebel banners,** so two rebellions no longer share one green flag.
- **Three turns of warning** before a secession, which had one card five turns out, and
  before your own party splits, which had none.
- If the Crown's own loyalty falls far enough, your men split off into a party of their own.
- The panel no longer hides the game's HUD to clear the screen; hiding it flooded every
  other mod with UI errors. One build on 2026-09-16 broke the panel on first open and the
  game went back to the 2026-09-15 build until it was fixed.

## 2026-09-12 to 2026-09-15

Added over several builds. The 2026-09-15 build was 7,646,430 bytes, SHA-256 beginning
`04ea554b`.

- **Fixed: offices, overseers and influence vanished a turn after being set,** on every
  load, since the save format first shipped. The game's `string.find` returns nothing when
  given a start position, so the whole save was read as one field.
- From Rome II's politics: a loyalty tooltip that lists every term, party traits and a
  party leader, Secure Loyalty, gifts, generals leading armies earn no influence, and
  battles and deaths move party loyalty.
- The Court tab became a grid of party cards beside the dial.
- **Intrigue became four columns of move cards with icons,** and grew from four moves to
  sixteen, including Provoke and Purge. Moves can fail, and the panel says why a move is
  refused.
- Two text sizes across the whole panel. The build check had been measuring text about 19%
  narrower than the game draws it; measured properly, seventeen labels that had passed were
  clipped, and each was fixed or cut to fit.

## 2026-09-11 - first build

Designed, built and packed in one session: the court model (the ten Chaos Dwarf houses as
parties, six offices held by characters, overseers as governors, influence (then called
standing) and loyalty) and
a four-view panel with its opener, 147,353 bytes. The game refused it at database load: every effect
junction row left a required column empty, and the error named an unrelated row. Fixed and
redeployed the same day at 147,853 bytes.
