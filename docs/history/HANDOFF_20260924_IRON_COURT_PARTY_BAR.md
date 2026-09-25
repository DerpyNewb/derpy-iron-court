# Iron Court: party select, action bar, Petitions tab (2026-09-24, late)

**BUILT and deployed locally to `data/derpy_iron_court.pack`, not uploaded** (the pack is
not on the Workshop). MD5 `b5c21ff4b9fc4b6f38ce1a0562582381`, 8,909,544 bytes, 1,713 files;
the three scripts and twelve `.twui.xml` in the saved pack compared byte for byte against the
workspace. Previous live copy kept as `data/derpy_iron_court.pack.bak_pre_partybar_20260924`.
Deployed after WH3 9.0 (build 25507028) landed; the import gate ran green against the 9.0 packs.

## 1. What the author asked for

- The party card's mood button and its reading apart: the card itself is the control.
- Click a party to choose it; a bar under the cards acts on it: Provoke, Secure Loyalty, Purge.
- Provoke and Purge off the Intrigue tab.
- A second click on the chosen card opens that party's members (any party, not only yours).
- More party statistics on the card.
- Offers and demands on a tab of their own, ACCEPT and REFUSE per row; accepting a demand
  seats the man in the office or overseer post it names.
- Mid-turn: RECORD moved to the last tab.
- A preview before deploying (shown and approved by the author opening RPFM).

## 2. What changed

**Model** (`zzz_derpy_iron_court.lua`): the `provoke` and `purge` entries in `IC.PLOTS` are
`cat = "party"`, which `IC.PLOT_CATS` does not list, so the grid no longer draws them. The house
column holds two moves (unseat, recall) and the other three hold four.

**Parties** (`zzz_derpy_iron_court_parties.lua`): `IC.can_grant_demand`, `IC.grant_demand`,
`IC.refuse_demand`. Granting seats the man through `IC.appoint` / `IC.assign_governor` - the
calls the Offices and Governors tabs make - then `IC.check_demand` settles it as met at once.
The party gets `loyalty_appointed` (the seat's own thanks) plus `party_demand_met`, the same
total the manual route gives. A man already in a post refuses as `"busy"`.

**Panel** (`zzz_derpy_iron_court_ui.lua`, `tools/gen_ic_ui.py`):

- Party card 455x266 unchanged; cells now: crest, name, name2, state (right-aligned word, red
  for SECEDES/SPLITS/SPLINTERING/PLOTTING/SCHEMING), portrait, leader, his trait, share and
  loyalty, two traits, loyalty a turn, and three right-aligned counts (members, offices,
  overseers) whose tooltips name the seats and provinces. `ic_party_mood` and `ic_party_off`
  are gone.
- The card root is interactive; `ICUI.on_party_click` chooses on the first click and opens
  `pick = {kind = "house"}` on the second. The listener routes the card's own id and every
  `PARTY_CHILD_XY` cell to it. Chosen card: CA's
  `dlc25_gunnery_school/frame_unit_card_selected.png` in image slot 2 (nine-slice margin 24);
  every other card gets `MASK_NONE` there, every draw, because the pool recycles.
- Action bar `ic_act_provoke/secure/purge` plus `ic_act_hint`, in the pager's row left of the
  pager (pager resized to 136/164/136 at x 1454/1600/1774). Buttons show only for a chosen
  rival; `ICUI.act_check` asks the model (`IC.can_favour`, `IC.may_target` on
  `IC.party_leader`) and a refused button is red with the reason in its tooltip and the notice.
  Plots open the actor picker `{kind = "plot", plot, key = tostring(leader)}`.
- `ICUI.oath_status` carries the favour screen's old status line (at zero / sworn / countdown)
  into Secure Loyalty's tooltip, and at the floor a "sworn" refusal is reported as "breaking" -
  the floor outranks the oath, as in the model.
- Petitions tab `ic_tab_petitions`, view `"petitions"`, second row button `ic_row_f` (REFUSE)
  at x 1560 w 110, column two 860px. Demand row first, then offers in court order.
- Tabs: COURT OFFICES GOVERNORS INTRIGUE PETITIONS RECORD.
- The favour list (`draw_favours`, pick kind `"favour"`) is deleted. **Send a Gift has no UI
  route any more**; `IC.favour(..., "gift", ...)` still exists. Author to decide: restore as a
  fourth button, or delete.

## 3. Rulings

- **The demand row leads with the MAN, not his party.** "Make Drazhoath the Ashen of Hashut overseer of
  Southlands World's Edge Mountains - 5 turns" measured 1007px in 860. Now column one is his
  name (face on his house's plate, his party's crest beside it) and column two reads "Demands
  the seat of X" / "Demands to oversee Y" - worst case 712px. Header "From".
- **The petitions terms are on the section label**, once, not on every row; the label dropped
  "What the parties ask of you." to leave room at 1600 (measured by gen check 20e2).
- **The Intrigue grid is ragged on purpose.** The harness's "every category the same depth" is
  now "the deepest column is never alone" plus "every move reachable from the grid or the bar,
  not both" - a lone deep column shrinks every card; a short one is blank space.
- The three counts are right-aligned: left-aligned they began 3px after the longest trait at 1600.

## 4. Gates

- Harness 576 checks green. Rewritten: card select/reselect/frame/cell routing, the action bar
  (hint states, other tabs, plots aimed at the leader, picker title), Secure refused in red,
  Secure lands and refuses a second oath, the oath promise at the floor, Petitions accept /
  REFUSE / demand seats / busy / lapsed / refused demand cost, row widths (offers and the
  longest province demand), intrigue grid counts via `grid_plots()`.
- Generator: 9b (REFUSE clears column two), 20g2 (bar labels, hints, PETITIONS tab), 20e2
  (petitions label - watched fail with a lengthened label).
- Mutation: full run 346, three re-aimed (check_demand anchor now paired with its neighbour,
  REFUSE-to-accept, the depth rule) and all caught; 11 new mutants for this change, all caught.
- Preview: `ic_petitions*.png` added; the court picture draws the new cells, the chosen frame
  and the bar. `DEMO_STATE`, `DEMO_TREND`, `DEMO_SEL`; counts derived from the demo tables.

## 4b. Follow-up: bar centred, Crown's box in two halves (deployed 2026-09-25)

Deployed to `data/derpy_iron_court.pack`: MD5 `7ef8f281ced2c232be1a5d455ae52859`, 8,922,887
bytes, 1,713 files; the three scripts and twelve `.twui.xml` compared byte for byte against
the workspace. Previous live copy kept as `data/derpy_iron_court.pack.bak_pre_crownsplit_20260925`
(the `b5c21ff4` build above).

Author: "why is the three buttons not center aligned? The Crown panel should display the
character portrait, traits and party trait on the right side, and the left side the faction
effects of getting the influence".

- **Two homes for the action bar.** `PANEL_XY` is now centred under the card grid (x 1209 /
  1347 / 1569 at 1920; hint spans the grid). `ICUI.ACT_PAGED_XY` (gen `ACT_PAGED`) is the old
  left-hugging home, used only while `ic_page_next` is visible; `ICUI.draw_actions(panel,
  faction, court, px, py)` moves and resizes all four each draw. Gen check 9c holds the paged
  home clear of the pager and the default home centred within 1px.
- **Crown's box, 926x258.** Left half (316 wide): `ic_control` "N% of the court",
  `ic_control_band` the band name, then `ICUI.FX_KEYS` (`ic_control_fx`..`fx4`), one effect a
  line, split out of the `derpy_ic_effects_*` loc string on ", " (gen 20g refuses an effect
  that contains one, and a band with more than four effects). Right half (526 wide): "The
  Crown", his name and party at full width, then the portrait with `ic_leader_trait`,
  `ic_leader_t1`, `ic_leader_t2` beside it, drawn with the party card's icon markup and tooltip.
  `ICUI.CONTROL_KEYS` is the hide/show list for the left half.
- Gates: harness 577 green (new: bar centred / beside pager / back to centre, measured off drawn
  positions; the block's t1/t2 equal the Crown card's; effect lines one per line and blanked when
  the band shrinks; all six control cells hidden off the court). 8 new mutants, all caught; all
  355 anchors unique. Preview reads the court section label out of `ICUI.SECTION` (it had a
  stale "Standing in the court" typed in).

## 4c. Send a Gift back as a fourth bar button (deployed 2026-09-25 with 4e)

Author: "bring it back as a fourth button". `ic_act_gift` (164 wide) between PROVOKE and
SECURE LOYALTY, so the two gold favours sit together and PURGE stays last; routes through
`ICUI.ACT_MOVE` to `IC.favour(..., "gift", ...)` like Secure Loyalty. Tooltip: name, price,
blurb, "+2 loyalty (now N)"; at 100 loyalty it is red with `reason_text("content")`.

**The paged home moved.** Four buttons (630px) and the pager (456px) do not fit the 926px grid
column, so `ACT_PAGED` is now the LEFT column's bottom row, centred under the Crown's box
(x 166..796 at 1920), level with the pager. Gen 9c checks it stays in that column, below the
box, centred; a new selftest injection pushes it into the box. Harness 578 green (new: the gift
through the listener, price, +2, no oath, refused at 100 and not charged; paged bar centred
under the box). Mutants 357, anchors all unique; two new ones for the gift, both caught.

## 4d. The close button that did not close: SetVisible(nil) (fixed, deployed 2026-09-25 with 4e)

First in-game open of the `7ef8f281` build: the panel would not close, the bar showed three
blank plates, and the script log carried 387 "is not a ui component" errors - CA's own
`wh_campaign_setup.lua`, the Exchange and the help pages as well as ours. That is the string
library breaking process-wide (see memory `wh3-string-find-plain-flag-corrupts-strings`), but no
plain-flag `find` exists in any Iron Court script.

**Found by bisecting in the live game through the wh3 bridge's `eval`** (two restarts):
`tools/probe_ic_string_break.lua` wrapped all 338 ICUI/IC functions with a
`("abc"):sub(2,2)=="b"` tripwire and opened the court - 14,894 calls, broken inside
`ICUI.draw_actions` and in none of its callees. `tools/probe_ic_draw_actions_steps.lua` then
stepped that body: every lookup, `Visible()`, `MoveTo` and `Resize` healthy, the first
`c:SetVisible(rival)` BROKEN. `rival = slug and ...` is **nil** with nothing chosen.

Fix: `local rival = slug ~= nil and ...`, so the chain can only yield a boolean. The harness's
fake `SetVisible` / `SetInteractive` / `SetCanResize*` used to coerce (`on and true or false`),
which is what hid it; they now record any non-boolean with its call site and a last check,
"no engine setter was ever handed anything but a boolean", lists them. Watched fail on the old
line (one site, `ui.lua:3259`), green after (579 checks). Mutant "the bar's visibility built from
an and-chain that can be nil" caught. Every other boolean setter in the three scripts was read by
hand: comparisons, literals or already coerced.

## 4e. Title-case labels and a plate behind the seats counter (deployed 2026-09-25)

Deployed to `data/derpy_iron_court.pack` together with 4c and 4d: MD5
`272c876bfec4a5d4f1affd3d79ba48be`, 8,930,970 bytes, 1,713 files; the three scripts and twelve
`.twui.xml` read back out of the deployed pack and compared byte for byte against the workspace.
Previous live copy (the broken `7ef8f281`) kept as
`data/derpy_iron_court.pack.bak_pre_titlecase_20260925`.

Author, on two screenshots: "texts edging out the buttons, use first letter Capital format. add
background ui for the number of seats present".

- **Every button label is title case now** - tabs (Court ... Record), Previous/Next, the bar
  (Provoke / Send a Gift / Secure Loyalty / Purge), Dismiss/Appoint, Release/Assign, Plot,
  Accept/Refuse and the picker words (Choose, Busy, Hire, Rank 3, Short 45, ...). The engine's
  `brand_header` face draws capitals 12-20% wider than the width check's proxy (seguibl x
  `GAME_FONT_WIDER`), measured off the screenshot at 1:1; that is why GOVERNORS and PETITIONS
  ran over their plates while the check passed them. Party-card state words (LOYAL, SECEDES ...)
  are not buttons and stay capitals.
- **`ic_influence` sits on CA's `ui/skins/default/frame_text.png`** (dark field in a thin gold
  rule, nine-slice margin 4), centred, box 1540,20,300,26 in both gen and Lua. New gen check
  20g3 reads the counter's format out of the panel Lua, fills it with 99s and measures it inside
  the plate less `SEATS_PAD` (10) each end; watched fail with a 200px box.
- Gates: harness 579 green; gen selftest and `--check` ok (12 files, 476 components); mutation
  selftest 358 anchored - one mutant ("the action bar drawn for your own house") had gone stale on
  the 4d line and was re-aimed, caught; the 15 mutants for 4b-4d re-run, all caught. Preview
  labels title-cased and re-rendered at 1600/1920: every tab label inside its plate at 1600, the
  plate drawn behind the counter.
- **Checked live through the wh3 bridge, 2026-09-25 09:15** (`tools/probe_ic_live_state.lua`,
  every read pcall'd; `IC_PROBE_ACTION` = open / court / choose / close_x, clicks by
  `SimulateLClick`): the new Lua is loaded; the string library is healthy after open, tab change,
  choose and close; the X closes the panel twice running; the seats counter reads "0 of 14 seats
  filled" at 1540,20 300x26; with nothing chosen the bar is hidden and the hint shows, and a rival
  card chosen shows all four buttons, labelled, at their centred homes. No script log this session
  (`derpy_debug_script_log.pack` unticked), so the error count was not read.
- **The width proxy is still wrong for capitals.** Recalibrating it against the engine's
  `TextDimensionsForText` through the bridge would let 20g catch this class; not done.

## 4f. Five bugs from the open lists, fixed (deployed 2026-09-25)

Deployed to `data/derpy_iron_court.pack`: MD5 `a1224d0dc9a8579b7c1c365ae0bb1aea`, 8,933,745
bytes, 1,713 files; the three scripts and twelve `.twui.xml` read back out of the deployed pack
and compared byte for byte. Previous live copy (272C876B) kept as
`data/derpy_iron_court.pack.bak_pre_bugfix_20260925`.

Author: "what else is missing in the mod", then "Fix the bugs first". Each was found by reading
the code against the handoffs' open lists, pinned by a harness check watched failing for its
own reason, then fixed.

1. **A full rebel pool renamed a running rising, or picked the seceding court itself.** With
   qb1-qb3 and invasion all alive, `IC.rebel_faction()` fell back to the first living key.
   Joining a running rising is the design (a fifth party joins one of the four), but the
   secession then renamed it after the newcomer, and a court run BY a rising (it is a Chaos
   Dwarf faction) could get its own key back. Now `IC.rebel_faction(exclude)` never returns the
   seceding faction, and `IC.secede` renames only a woken faction or one with no
   `derpy_ic_risen_` name yet.
2. **`IC.turn` called `IC.party_turn` bare**, so one error there skipped the secession clocks,
   the Crown split and the save. Now `pcall`'d and said ("the parties' turn failed in ...").
   The harness wraps `IC.say`, collects every such line, and a last-but-one check fails on
   any, so the catch cannot hide a fault from the run.
3. **Placated was read after the drift.** A party lifted one above its line on the player's
   turn drifted back onto it and the warned move landed. `IC.party_placate` now runs right
   after `IC.load` at the top of `IC.turn` and marks the plot; `IC.plot_void` honours the mark.
   (The first version of the test set loyalty in memory only; `IC.turn`'s `IC.load` read the
   saved court back and undid it. The test now placates through `IC.move_loyalty` and saves,
   as a gift does.)
4. **An office demand nobody could grant still cost -10 when it ran out.** ACCEPT is red
   while the man is short of the office's influence, yet expiry settled "refused". Now at
   expiry an office demand whose man fails `IC.can_appoint` is "void" (no loyalty, no card),
   by both roads: `IC.demand_state` and the engine's `MissionFailed` listener. A man the player
   put in another post is still a refusal. **Ruling:** a player who spends the man's influence
   on intrigue can dodge the -10 this way; accepted as minor.
5. **A dead officer's term stayed in the save.** `ic_dead` vacated the seat and left
   `court.terms[office]`; `expire_terms` walks held offices only. Cleared with the seat.

Not changed: the Great Guilds paying +10 to all six guilds when an Iron Court demand
completes (its `gg_mission` pays on every non-bounty `MissionSucceeded`). That is the Guilds'
own "any mission" rule and a decision for the author, not a bug fix. The thin light lines at
1600x900 need the bridge at that resolution.

Gates: harness 587 green (seven new checks plus "no parties' turn failed anywhere in the run").
Nine new mutants (each fix undone, plus "every office demand lapses", which is the void rule
made too wide), all caught; four older mutants re-aimed at the rewritten lines ("the parties
given no turn", "a placated party striking anyway", "demand_state with no expiry", "the
engine's expiry refusing a demand the player met"), all caught; 367 anchored.

**The demand, read out of the script log first** (author: "check logs first about the
demand"; `script_log_250926_1302.txt`, a new Conclave campaign on the 272C876B build):

- Turn 1, 65.6s: `forge demands gov wh3_main_combi_province_the_plain_of_zharr for cqi 1451`.
  At 122.0s the click was `ic_row_f` in `derpy_ic_row_1` on the Petitions tab - the Refuse
  button (`ICUI.on_petition_click(context, false)`) - and it settled `refused` in that click;
  the refusal card waited for the panel to close (130.7s), as `IC.hold_feed` does. The autosave
  at 447.6s has an empty agenda (`||||`) and forge at 43 loyalty against 50-58 for the others:
  the -10 plus drift.
- 503.3s: `temple demands office kilns for cqi 1501`. At 525.8s the click was `ic_row_e`
  (Accept): `derpy_ic_title_kilns` added to cqi 1501 and the demand settled `met`.
- **0 "is not a ui component" lines** in the whole session: the 4d fix holds with logging on.
  The two SCRIPT ERRORs are CA's (Conclave has no `main_warhammer` faction intro; Vampire
  Lairs finds a faction with no home region).
- NOT answerable from the log: whether the engine closed the two demand MISSIONS.
  `cm:complete_scripted_mission_objective` is an engine call with no CA Lua wrapper and logs
  nothing, and our mission raises no MissionManager line. Look at the objectives panel.

## 5. Owed in game

1. The card root takes a click through its children (only the tooltip cells are interactive).
2. The gold frame draws in slot 2 and nine-slices at the card's size.
3. The section label on Petitions fits at 1600x900 (the proxy says 1535 of 1564px, tight).
4. The X closes the panel and the script log has no "is not a ui component" lines (4d).
5. The bar hides with nothing chosen and shows four buttons for a chosen rival; Send a Gift
   charges, adds loyalty and goes red at 100 (4c).
6. Tab and button labels sit inside their plates; the seats counter draws on its plate (4e).

A province demand needs no in-game check of its own: `IC.assign_governor` refuses only a man
who no longer exists, and `IC.demand_state` voids that demand before ACCEPT is reached.
