# Iron Court live test: war council, claims and secrets (2026-10-19)

Build 58D5347C from `data/`. Three campaigns through the wh3 MCP bridge with the test settings on (reverted after, the
player's file put back byte for byte): Astragoth, a Chaos Dwarf court, turns 1 to 8; Thorgrim, a Dwarf court, turn 1, twice.
No save written. Test changes, in memory only: `IC.TUNE.grace_turns = 0`, influence grants so a man could pay a move, and in
the Astragoth game chain loyalty -40 on turn 6 to get a party with a countdown. The plan's in-game checklist is ticked in
`docs/superpowers/plans/2026-10-17-iron-court-war-claims-secrets.ledger.md`.

No SCRIPT ERROR from the Iron Court in any of the three logs. Each game's baseline was CA's Nurgle-initiative warnings, plus
one Tabletop Caps error (`tabletopcaps.lua:945`) in two of the three. Three `find_single_uicomponent [false]` errors at 6523.8 s in the
Astragoth log came from a probe of mine (stack `wh3_mcp_eval:4`).

## For the author to decide

1. **A secret's own cost can break the party it is spent on.** No secret use checks the breaking point. "Stop their
   countdown" on the Cult of the Iron Collar at 5 loyalty took it to 0, which is `secede_break`. Protection cancels the angry
   state only, not `IC.at_breaking_point`, and the party's card already read "breaks with you next turn... an oath will not
   hold". It survived only because a claim lapse (+8) ran before the secession tick. Any blackmail use on a party at 5 or
   less does this. Options: refuse or warn when the cost reaches the break, waive the cost for that use, or let the
   protection hold off the break too.
2. **Two lines claim losses that did not happen.** The overrule notice "Vote overruled. The losing parties resent it." and
   the bypass Record line "...The parties against it lost 10 loyalty." both print when no party was on the losing side.
3. **An overrule writes three Record lines**, and the first and third both say it passed ("You overruled ... it passed",
   "The court will declare war on X on turn N", "The vote on war with X passed").
4. Edge, seen in the code and not tested: a planned war started early on a turn the court already declared its own war takes
   the free branch, so no `war_early` line is written and `court.war` waits for its turn (then clears silently). Harmless.

## Passed

- War council, Chaos Dwarf court: the move refuses on influence and names the shortfall. Its Petitions row, vote screen
  (titles, heads, back button, the four decide buttons, the faction flag, the abstain line) and gold Pass all work. Pass
  costs 2500 from the treasury and plans the war 3 turns out. The planned-war row shows both Call Off prices.
- The planned war fires at turn start with the free-war flag set first. There is one diplomatic event, a `war_begins`
  line, and nobody is charged (turns 4 and 8). Starting it early is free and clears the plan. A bypass ends the vote.
  Call Off for influence is refused with the shortfall; Call Off for gold works and charges the party that wanted it.
- Unasked war: the party against loses 10, the party for gains 3, one card. A second war the same turn moves nobody.
- Live war facts move with the map: a "strong" line on turn 1 became "torn" by turn 4 as the armies evened out.
- Claims: raised on Occupy of a province new to the court, ordered by weight, with rows and tooltips as written. Grant
  (+8, -4 to the other claimant, governor appointed, notice) and Refuse (-6, no notice, by design) work, and a claim lapses
  to the strongest party at its turn.
- Secrets: Dig is 55% and a failed dig costs loyalty. The refused Use button is grey with a tooltip pointing at Dig for
  Secrets. Demand use: demand gone, rest 5 turns, -5. Vote use: six men flipped, tally 778/0/730 became 1508/0/0. Countdown
  use: clock 0, protected 5 turns. Each use has its notice and spends the secret.
- Dwarf court: the council card's flavour line ("The clans weigh the war."), the vote screen and Petitions all read in
  Dwarf words. Help, The War Council: 14 lines at the 1600x900 UI, with both Dwarf swaps ("a name in the Book of Grudges",
  "or a grudge") and the grudge bullet. A faction with no border is refused as "far" until the Book names it (band 1000+),
  then it is a candidate with the `book` fact. Refusing a claim writes a "demand" grudge. The loyalty tooltip shows
  "Grudge: A Demand Refused, turn 1: -1" with its way out, and "Kinship: +1". The shared claims card text is race-neutral.
- Help, The War Council (Chaos Dwarf): 14 lines, the last ending at y 555 of 900.
- `factions_screen_name_cr_*` resolve offline. None of those six houses is in this campaign. Of 228 factions with no
  `mon_64.png` in any loaded pack, none was alive in the Astragoth game.

## Engine facts measured

- `cm:force_declare_war` raises `NegativeDiplomaticEvent` synchronously, with the player as proposer and the target as
  recipient. With `invite_b_allies` set, the AI ally broke its alliance (a war=false event first) rather than joining, so
  the pull-in case can only be reached from the diplomacy screen.
- A trade agreement is already gone when the declaration's event fires, so the snapshot is needed. A scripted trade
  agreement raises no `PositiveDiplomaticEvent`.
- `cm:force_make_peace` raises no `PositiveDiplomaticEvent`, so the peace reaction cannot be tested by script.
- `cm:force_declare_war` breaks a `cm:force_diplomacy` war lock.
- `GarrisonOccupiedEvent`: the owner is already the occupier when it fires (78 of 78 AI captures). Occupy fires it; Sack
  and Raze do not.
- While the court panel is open, `IC.feed` queues its cards and raises them when the panel closes.

## Not tested

The peace reaction and a defensive ally pull-in (both need the diplomacy screen by hand); 1920 and 2560 (the test window
only gives the 1600x900 UI); Call off their scheme; Expose; a planned war started early on a turn the court declared its
own; whether "sworn on the anvil" reads right after a blackmailed countdown.

## Two crashes in the Dwarf campaign, not traced to the Iron Court

Both happened in CA's capture flow after a rigged autoresolve of a Bloody Spearz siege in Deadrock Gap:

- `D2026-10-19_T10-47-24`: EXECUTE at 0x233e557f0, in no module, just after Occupy of The High Place. The caller was
  `Warhammer3.exe+0x2314bae`, a grid draw with inner and outer radius and angle tests (a radial fill bar). Under it,
  `+0x22b8097` repeats eight times: the UI draw recursion, with clip push and pop. This is a call through a freed object.
- `D2026-10-19_T11-20-02`: EXECUTE at 0x0, a null call, just after the battle results closed at Worlds Edge Archway. The
  court panel was closed; Deadrock Gap was already held, so no claims were raised.

The same capture of The High Place in the second game did not crash. Neither log has an Iron Court line, error or card
near the crash. The only court activity in crash 1 was quiet traits on the new garrison captain. None of the five
earlier dumps on this machine shares either signature.

Leads, none proven:

- The lords pack's `army_banner.twui.xml` override (next section).
- Tabletop Caps removing six duplicate `TTCArmyCardListeners` in one call before crash 2. CA's library warns that this
  "may cause instability". Not present before crash 1.
- The bridge's rigged autoresolve.

## Side finding: the army banner override is stale

`ui/campaign ui/army_banner.twui.xml` in `!aa_derpy_hashut_legendary_lords.pack` (Workshop 3432966208) is 466,378 bytes.
`tools/patch_army_banner.py` rebuilt from the live game file comes to 468,797 bytes, and the staged copy is the stale one too.
The shipped file therefore removes three things CA added in a patch:

- the `MilitaryForceFactionChangeAny` refresh on the banner's faction flag;
- a concealment `ContextTextLabel`;
- three `agent` states.

Fix: re-run `py tools/patch_army_banner.py`, then pack it with RPFM. Not done here, because RPFM was closed and the pack is
on the Workshop. Resource Overhaul's `city_info_bar.twui.xml` override matches a fresh rebuild byte for byte.
