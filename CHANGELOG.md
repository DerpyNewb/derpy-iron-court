# Changelog

Builds of `derpy_iron_court.pack`, newest first. The detail behind each entry is in
`docs/history/`. The pack has only ever been deployed to the game's `data/` folder; none of
these builds is on the Steam Workshop. Early builds recorded a SHA-256 or only a size, not
an MD5.

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
