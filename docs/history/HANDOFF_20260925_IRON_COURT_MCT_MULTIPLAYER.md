# The Iron Court: MCT settings and multiplayer support (2026-09-25)

Spec: `docs/superpowers/specs/2026-09-25-iron-court-mct-multiplayer-design.md` (amended while
planning; see its "Amended 2026-09-25" block). Plan:
`docs/superpowers/plans/2026-09-25-iron-court-mct-multiplayer.md`. Pre-change copies of every
edited file: `Modding Files/source/iron_court_bak_pre_mctmp_20260925/`.

BUILT and deployed to `data/derpy_iron_court.pack` (9,163,798 bytes, MD5 `e9d6e2f0`, after the
review fix pass in section 7, the party counts in section 8, Ruthless's pressure line and the two
Purge fixes in section 9, the office terms in section 10, the seven QoL features in section 11, the six live switches in section 12, the load-crash fix in section 13 and the even deal and field leaders in section 14, the demand rest in section 15 and the Chaos Dwarf reskin in section 16, the heading plates and embers in section 17). Not uploaded. The pack from before this change is
`data/derpy_iron_court.pack.bak_pre_mctmp_20260925`.

## 1. What shipped

- **An MCT page, `derpy_iron_court`** (`script/mct/settings/derpy_iron_court.lua`), in four
  sections:
  - Difficulty: one dropdown, Gentle / Default / Harsh / Ruthless / Custom. It owns the
    fourteen numbers. Anything but Custom greys them.
  - Systems: five switches, all on by default. They are Rival parties act on their own, Other
    Chaos Dwarf factions have courts, Parties can secede, A weak Crown pushes rivals out, and
    Your own party can split.
  - Custom numbers: fourteen sliders.
  - Debug: Detailed log. Failures are always written, whatever this says.
- **Every setting is registered in four places**: the MCT page, `IC.TUNE`, `IC.TUNE_ORDER`, and
  one read site. The harness holds the first three against each other: key, kind, default,
  section, and every preset value inside its slider's range and step. Gate 0e
  (`check_tune_reads`) refuses a setting that nothing reads.
- **Presets are resolved at read time** (`IC.read_mct_or_defaults`), because MCT's
  `set_selected_setting` is a no-op with the panel shut. Switches are read under every
  difficulty; numbers are read only under Custom. Each value is type-checked against its
  default. `rivals_min` is clamped to `rivals_max`.
- **The freeze.** `IC.freeze_tune()` is the first thing `IC.first_tick()` does, before
  `IC.register()` and before any court is rolled. On the first load it reads MCT, packs the
  result into the saved value `derpy_ic_tuned` (`|`-separated, in `IC.TUNE_ORDER` order,
  booleans as 1/0), and applies it. Every later load unpacks that string and never reads MCT
  again. A field that will not read, or a key an older string lacks, keeps its default.
- **In multiplayer MCT is not read at all.** `IC.is_mp()` is a pcall of `cm:is_multiplayer()`,
  and an error reads as single player. Every machine gets `IC.TUNE`'s defaults.
- **The multiplayer transport.** All eleven panel actions go through
  `IC.mp_send(faction_key, op, arg)`: `appoint`, `dismiss`, `gov`, `ungov`, `plot`, `favour`,
  `hire`, `grant`, `refuse`, `accept`, `decline`.
  - Single player runs the op at once.
  - Multiplayer sends `ic1|op|arg` through `CampaignUI.TriggerCampaignScriptEvent(cqi, id)`.
    The `ic_mp` `UITrigger` listener runs the same op on every machine.
  - A trigger over 100 characters, or for a faction with no command queue index, is refused
    and logged. It is never applied locally instead.
  - A trigger that is not `ic1|`, an unknown op, and an unknown cqi are all ignored.
  - Numbers cross the wire as strings and come back through `tonumber`. A garbled one reaches
    the model as nil, and the model refuses it; it does not raise.
- **The answer hook.** The model calls `IC.after_op(faction_key, op, arg, done, why, spare)`
  at the end of every op. The panel sets it to `ICUI.after_op`, which dispatches to
  `ICUI.ANSWERS[op]` (notice, sound, picker closed). In multiplayer it answers only this
  machine's own player, and redraws for itself because no click is waiting to.
- **`ICUI.player()` reads `cm:get_local_faction_name(true)`**, the forced form (the unforced
  one throws in multiplayer). The first human is the fallback.
- **No feed hold in multiplayer.** The panel is open on one machine and not the other, so a
  hold would raise the event calls at two different times.
- **Gate 0d, `check_mp_routing`**: the panel may not call any of the eleven model functions
  directly. Comments and strings are blanked first.
- Harness: 587 checks at the start, 630 now. Mutants: 367 at the start, 411 now (the plan's
  22 `mct:` and 15 `mp:`, 3 re-aimed, and 7 from the fix pass), with 0 unexplained.

## 2. What single player sees

With MCT absent or left on Default, nothing changes: the numbers are the ones `IC.TUNE`
already held. The panel's actions run exactly as before. They go through `IC.mp_send`, which
runs them at once, and the answer (notice, sound, picker) is the same code moved into
`ICUI.ANSWERS`. The older click checks are the single-player regression suite, and they pass
unchanged.

A save from before this build has no `derpy_ic_tuned`. The first time it is loaded, it takes
the player's MCT settings and keeps them from then on.

## 3. The timing correction

The spec first froze the settings at the first `FactionTurnStart`, which is what the MCT
memory advised. That is wrong for two reasons:

- **A new campaign fires no `FactionTurnStart` until turn 1 ends.** So turn 1 would play on
  the defaults. Worse, `IC.seed` rolls the court at first tick, so the court would have been
  rolled on the defaults for good.
- **MCT reads the player's settings in its own `LoadingGame` callback**:
  `groovy_mct.pack`, `script/groovy/modules/mct/systems/registry/main.lua`, `Registry:load`.
  `LoadingGame` runs before any first tick, so the values are already there at first tick.

The freeze therefore moved to first tick, ahead of `IC.register()`. Mutant "mct: the court
rolled before the freeze" pins that order.

**The Great Guilds has the same gap.** It freezes at the first `FactionTurnStart`, so its turn
1 plays on the defaults. That is noted here for its own fix, which is not made in this build.
The memory `wh3-mct-has-no-campaign-gating.md` is corrected.

## 4. Not tried in a two-player campaign

Everything above is proven in the harness only. The round trip goes through `with_mp` and
`deliver`, which stand in for the engine's broadcast. A first two-machine run must check:

- Each of the eleven actions, clicked from each machine, lands on both machines. The court
  reads the same afterwards: the same offices, governors, loyalty and gold.
- The machine that did not click stays quiet: no sound, and its own picker and notice are
  left alone.
- `script_log.txt` on both machines has no `UITrigger failed` and no `not sent`.
- The MCT page makes no difference: both players get the defaults whatever each has set.
- A second click while an action is in flight does nothing, and the next click after the
  answer goes out (section 7).
- A player who is not a Chaos Dwarf gets no court button.
- **The panel's three UI timers stay on `cm:callback`**, which CA documents as a model-time
  timer: the opener retry, the pulse stop after a click, and the standing plate's one-tick
  delay. See the section 7 ruling. If the two machines desync after a click or after opening
  a character panel, these are the first suspects, and `cm:real_callback` (milliseconds; an
  interval of 0 or less runs the callback at once) is the replacement.

## 5. In game, single player, to check

1. Load the current save. Appoint, dismiss, plot, send a gift, and answer a petition. Each
   should confirm and redraw exactly as before.
2. If MCT is installed, the Iron Court page shows four sections. In a campaign every control
   is locked, and the lock gives its reason.
3. A new campaign on Harsh rolls three or four rival parties at loyalty 50.

## 6. Rulings made during execution

- There is no git here, so there is no worktree and there are no commits. The backup folder
  above is the diff base, and each task was closed on a harness run recorded by hand.
- `sync_iron_court_repo.py --selftest` failed only on this file's absence until it was
  written. The repo was NOT synced.
- The end of `MUTANTS` in the runner did not read the way the plan's copy did. The new mutants
  were appended after the real text.
- The plan's mutant "mct: AI courts run with ai_courts off" replaced the guard with a bare
  `return true`. That leaves a statement after a `return`, which is a Lua 5.1 parse error, so
  the runner reported an ERROR rather than a catch. The replacement is now
  `if true then return true end`, and "with ai_courts off an AI court is never rolled or run"
  catches it.

## 7. The final review and its fix pass

A fresh reviewer read the whole change. It found no critical issues and four important ones.
Three were fixed, each with a check that failed first. The fourth was ruled against. One of
its minors was also re-graded and fixed, because it was a check that could not fail.

- **An empty field in the saved settings slid every later value onto the wrong key.**
  `IC.unpack_tune` split on `[^|]+`, which steps over an empty field. With field 2 empty,
  `loyalty_drift_none` read 20, so every party with no office gained 20 loyalty a turn. It now
  splits on `([^|]*)|`. Check: "an empty saved field keeps its default and moves nothing after
  it".
- **In multiplayer a second click before the answer sent the action again**, and both copies
  landed on every machine: loyalty paid twice, or the first man unseated by the second.
  - `ICUI.send` now holds one action in flight. It sets `ICUI.waiting` before sending, so an
    answer that arrives inside the send still clears it, and clears it again on a refusal.
  - The answer ends the wait, and so does closing the panel, so a lost trigger cannot leave
    the court dead.
  - `IC.mp_send` now returns whether the action ran or went out.
  - Check: "in multiplayer a second click before the answer sends nothing".
- **A player who was not a Chaos Dwarf got a working court.** They saw the button and an
  empty court that still hired Chaos Dwarf officers into their own faction. This was already
  true in single player. `ICUI.court_player()` now gates `ICUI.place_opener` and `ICUI.open`.
  It refuses only a player known to be something else: when no player can be read, it lets
  the panel open, which is how every harness opener check runs. Check: "a player who is not a
  Chaos Dwarf gets no court button and no panel".
- **Review focus 3's check could not fail.** It called `IC.freeze_tune` alone, and that
  touches no court. It now saves the court, drops it from memory and reloads it through
  `IC.first_tick`.
  - The reviewer's first mutant for it, seeding a court that was already loaded, survived.
    That mutant is equivalent code: `IC.roll_court` refuses a court already rolled, so seeding
    one changes no loyalty.
  - Its replacement, "an old save's court not read back on its first load", is caught by the
    rewritten check and could not have been caught by the old one.
- **Ruled against: moving the panel's timers to `cm:real_callback`.** The reviewer's evidence
  was a CA guard on a dev button that changes the model straight off a click, not a timer.
  - CA's own multiplayer-capable campaign scripts use `cm:callback` in 20 click listeners and
    16 panel-open listeners, including the Sword of Khaine, the Worldroots and Thanquol's
    plans. None of them uses `real_callback`.
  - `real_callback` with an interval of 0 or less runs its callback synchronously
    (`lib_timer_manager.lua`), which would drop the standing plate's one-tick delay.
  - This is on the two-machine checklist in section 4.
- **Deferred minors:**
  - `crown_split` off still lets the Crown's card say "SPLINTERING" or "SPLITS n".
  - `secession` off still lets Provoke start a countdown and raise the "secede soon" card, at
    the full influence price, until the next turn start zeroes it.
  - `ai_courts` off on an older save leaves the AI courts' office bundles and traits in place
    for good.
  - When `secede_turns` is at or below 3, the "secede soon" card never fires; Ruthless is 3.
  - The Harsh tooltip says influence costs more, when it actually comes in more slowly.
  - The page description does not mention the first load of an older save.
  - Greyed sliders show numbers the chosen difficulty does not use.
  - `check_tune_reads` accepts any quoted key as a read.
  - A comment wrongly says `random_number` does "no roll" when min is above max; CA swaps them.
  - `IC.unpack_tune` applies no range clamp to a garbled save.

## 8. The court's size is the difficulty (author, 2026-09-25, same day)

Asked after seeing leaderless parties at Ghorth's start. Each difficulty now seats a FIXED
number of rival parties instead of rolling between two numbers. Counted with the Crown, as
the grid's six cards are:

| | Gentle | Default | Harsh | Ruthless |
|---|---|---|---|---|
| Rival parties | 1 | 3 | 4 | 5 |
| Cards on the court | 2 | 4 | 5 | 6 (grid full) |

- `IC.TUNE` is now `rivals_min = rivals_max = 3`, and each preset sets both to its one number.
- Custom keeps both sliders, now ranging 1 to 5 with a default of 3.
- The tooltips give each difficulty's count. The Harsh tooltip's "influence costs more" (a
  deferred minor above) was corrected while the line was being rewritten.
- **Five rivals, four rebel factions.** Only four rebel factions exist for the whole map. A
  party that leaves after they are all in play joins one already risen (`IC.rebel_faction`'s
  fallback). It is not crowned there, because `crown = waking and i == 1`. This path already
  existed, since every court shares the pool.
- The difficulty applies to AI courts too.
- **Tools that read `rivals_max` now take the LARGEST value in the model, not the first**,
  which is only Default's: `gen_iron_court.py` check 10c and `preview_iron_court.py`. The
  preview's demo court is now six cards and fills the grid; it gained a sixth demo party
  (RESTLESS, 38 loyalty).
- Check: "each difficulty seats exactly its number of rival parties", through the real first
  tick, four attempts each. It failed first (Gentle seated 2). Mutants: "Ruthless seating one
  party short of a full court" and "Default rolling a range again". 631 checks, 413 mutants,
  0 unexplained.
- Why parties start leaderless at all is unchanged. Only lords, or failing those a garrison
  commander, can lead a party. When a party has none and your party has no spare lord, a lord
  is made in the recruitment pool, and the card reads "No one speaks for them" until he is
  recruited. More rivals means more of these on a thin start such as Ghorth's.
- Ruthless pressure on turn 1: resolved in section 9.

## 9. Ruthless's pressure line lowered to 15 (author, 2026-09-25, same day)

- Six equal starting weights left the Crown 17 of the court. At `pressure_below` 20 a fresh
  Ruthless court was pressed from turn 1 at `(20 - 17) * 8` = 24 in a hundred, before the
  player had moved. Ruthless now uses 15, the same as Harsh.
- Check: "a full Ruthless court is not pushing a rival out on its first turn" (through the real
  first tick). It failed first, "a fresh court at 17 is pressed at 24 in a hundred". Mutant:
  "Ruthless pressing a fresh full court from turn 1". 632 checks, 414 mutants, 0 unexplained
  (`mutants_full_pressure15.txt` in the backup folder).
- **Two faults found while answering "what does a turn-1 Purge cost?", both FIXED the same
  day (author: "fix the bugs, the party rules alone as long as loyalty is kept"):**
  - **A move could not fail unless its actor held twice its price.** `IC.plot` took the price
    first and then asked `IC.plot_chance`, which begins with `IC.can_plot`, which refuses once
    the actor holds less than the price. A refused chance is nil, and a nil chance skipped the
    failure branch. Measured with a forced roll of 100: a purge by a man holding 400 or 799
    landed while the panel showed 85% and 95%. The harness's "a purge that misses" gave the
    actor 5000, so it never saw this. Fix: the odds are read before the price is taken, which
    also puts the edge (+1 per 10 influence over the target) back on what the panel showed.
    Check: "a move is rolled at the odds the panel showed, whatever the price leaves" (the
    actor holds exactly the price; the shown chance + 1 must miss, the shown chance must land).
  - **A court with no rivals left was rolled again on the next turn, at full size.**
    `IC.court_rolled` meant "more than one party is seated", so once the last rival was purged
    or seceded, the next `IC.turn` called `IC.roll_court`: Gentle got 1 new party, Default 3,
    Harsh 4, Ruthless 5, each at starting loyalty. Fix: `court.rolled`, set by `IC.roll_court`
    and saved as an OPTIONAL 9th field of the court string. A save from before it is marked
    by `IC.court_rolled` the first time it is seen with a rival, which is before it can lose
    its last one; a save whose court is already Crown-only is re-rolled once, as before. The
    Crown now rules alone until its own loyalty runs out and it splits (`IC.splinter`, which
    can bring the purged party back through its men's backgrounds), or a confederation brings
    parties in. Measured: a Crown-only court runs six turns and both turn halves clean, reads
    control 100 (band "grip", no pressure), and draws every tab. Check: "a court whose last
    rival is gone rules alone, and is never rolled again" (a new court, then an eight-field
    save, each through a turn and a save reload).
- Mutants: "plot: the odds read after the price is taken", and four on the marker (never set
  by a roll, an old save never marked, never saved, never read back). "ambition omitted from
  field 8 of IC.pack" was re-aimed at the new line. 634 checks, 419 mutants, 0 unexplained
  (`mutants_full_purgefix.txt`).

## 10. Office terms: ten turns, a three-turn wait to renew, and no weight leak (author, 2026-09-25)

Asked "is 5 turns too short for a term?". Measured first: one claimed seat re-given to the same
man at every term's end took its party from weight 10 / loyalty 50 to 34 / 82 in four terms.
Author: "do the three, add also that the seat cannot be renewed for 3 turns".

- **The weight leak (a bug).** `IC.appoint` gave a claimed seat's own party
  `weight_per_office * weight_affinity_mult` (12); `IC.dismiss` and the death listener took back
  `weight_per_office` (6). Every term leaked 6 into the party for good, and only rivals claim
  seats, so it wore down the Crown's share. Now `IC.office_weight(office_slug, slug)` is what all
  three add and take back. Weight already leaked into a running save stays.
- **Renewal.** `IC.expire_terms` records the man whose term ended in `court.last[office]`
  (`{cqi, turn}`), until someone else takes that seat. He cannot take the same seat again for
  `renew_wait` = 3 turns (`IC.can_appoint` refuses `"renew"` with the turns left; the picker row
  reads "Wait N"; the refusal reads "His term in that seat has just ended. He may take it again
  in N turns, or another man may take it now."). When he does, it is a renewal: his party gets no
  `loyalty_appointed` (+8). Another man may take the seat at once, and is welcomed as ever.
  `renew_wait` is in `IC.TUNE` but not `IC.TUNE_ORDER`, so it is not an MCT setting. Saved as an
  OPTIONAL 10th field of the court string (`office,cqi,turn;...`).
- **`term_turns` is 10 on every difficulty** (was 5). The MCT slider defaults to 10 and runs
  2 to 20, and its tooltip states the renewal rule. **A campaign started since the MCT build keeps
  the 5 it froze at its first tick**; saves from before the MCT build freeze 10 on their first load.
- AI courts: the same rules bind them. Measured over 60 turns (9 men, 5 parties) against the old
  rules rebuilt by override: the same 9 seats filled on average, every party at 100 loyalty with
  the same lows, no secession countdown. A waiting man moves to another seat. A claimed seat
  whose party has no other eligible man stays empty for the wait, because the AI never gives a
  claimed seat to an outsider.
- Checks: "losing a claimed seat takes back exactly what taking it gave" (an ended term, a
  dismissal, a death), "a man whose term ended waits three turns for that seat, and comes back
  unwelcomed" (a save reload every turn of the wait; another man at once; the old holder not kept
  waiting once another man has held it; the picker row; the refusal text), "a seat is held for
  ten turns on every difficulty". All three failed first. 12 new mutants; "Ruthless seating one
  party short" and "the rolled marker never saved" re-aimed. 637 checks, 431 mutants, 0
  unexplained (`mutants_full_terms.txt`).

## 11. Seven quality-of-life features (author: "implement all", 2026-09-25)

1. **A card the turn before a term ends.** `IC.terms_ending` (the seats whose term ends at the
   next turn start, in `IC.OFFICES` order) and `IC.warn_terms`, called in `IC.turn` right after
   `IC.expire_terms`. New event `term_soon`, index **2622**, appended last in both
   `gen_iron_court.EVENTS` and `IC.EVENTS` (the index is derived from position). It names the
   seat when only one is ending; otherwise it shows the default secondary, "TERMS END".
2. **A summary on the court button's tooltip** (`ICUI.opener_tip`): the Crown's share and control
   band, empty seats out of 14, terms ending next turn, parties counting down to leave, and old
   holders whose wait is over. A line is left out when there's nothing to report; the empty-seats
   line is always shown. `ICUI.update_opener_tip` runs on first placement, on `ICUI.close`, and on
   the PLAYER'S turn start **one tick late** (`ic_opener_tip`, `cm:callback(.., 0)`): this file's
   listeners are registered before the model's, so read at once it would show last turn's court.
3. **An empty seat's card names the wait:** "Vacant - holder waits N turns" (the longest wording
   that fits the 1600x900 cell; gen_ic_ui 20f measures it, reading `renew_wait` out of the model).
   His name rides the Appoint button's tooltip, because a name does not fit the cell.
4. **Fill Empty Seats** (`ic_fill`, 850,978 220x34, the pager's row on the offices tab, which
   never pages). `IC.fill_plan` is the AI's old seat loop turned into a plan that seats nobody:
   a claimed seat goes to its own party's man, or to nobody while that party sits in court, and
   any other seat goes to the best man left, highest seat first. `IC.fill_offices` seats the plan,
   and `IC.ai_fill_offices` is now that. The tooltip IS the plan. The label is red with nothing to
   do, and a click then says why without sending. The 12th panel action goes through the
   transport as `ic1|fill|`; the plan is re-read on every machine. It is in `DIRECT_ACTION`.
   The one open
   question the author did not rule on: the fill never snubs, so a seat claimed by a seated party
   with no eligible man stays empty for the player to fill by hand.
5. **Find** on a house roster (click a chosen party card again): a man on the map gets a
   Find button, which closes the court and moves the camera (`cm:scroll_camera_from_current(true,
   1, {x, y, 14.7, 0, 12})`, CA's own numbers for looking at a character). It is camera only, so
   nothing is sent. A wounded man, or one at 0,0, gets no button.
6. **The tab and the two sorts survive a reload:** `derpy_ic_ui_prefs` is written on close and
   read on the first open after a load. **Single player only**, because a saved value that one
   machine writes and the other does not makes the two saves differ. A tab or sort that no longer
   exists is ignored. (Within one session they already outlived a close.)
7. **`all_cards`** (MCT Systems, "Show routine event messages", default on), appended LAST to
   `IC.TUNE_ORDER`. Off, `IC.ROUTINE_EVENTS` (office_lost, party_joined, snub, party_feud,
   party_feud_end, dissolved, party_plot_dropped - each already logged where it is raised) go to
   the Log tab only. Warnings, demands, offers and the player's own results always show a card.

Checks: one per feature, each failing first, plus the existing MP checks widened to twelve
actions. The fake character gained `display_position_x/y` and `is_wounded`, which
`check_character_stub` holds against CA's index. 30 new mutants (29 after dropping one that
duplicated "the AI handing a claimed seat to an outsider again"); three older ones re-aimed:
"a roster row wired to a man the camera cannot go to" (it was "...on a list that offers nothing",
which Find deliberately changed), "the AI back to filling seats on standing alone" (now
`IC.can_appoint` in `IC.fill_plan`) and "mp: a court opened for a player who is not a Chaos
Dwarf". 645 checks, 460 mutants.

## 12. Six switches changeable mid-campaign (author: "make some settings be changeable mid campaign", 2026-09-25)

**Live now:** `parties_act`, `secession`, `pressure`, `crown_split`, `all_cards`,
`detailed_log` (`IC.LIVE_TUNE`). **Still frozen:** the difficulty, all fourteen numbers, and
`ai_courts` - off mid-game it would leave the other courts' office bundles on their men (the
review minor already on file), and on mid-game it would roll courts for every Chaos Dwarf AI at
once.

Each live switch was checked for what it leaves behind when flipped off:
- `parties_act` - its off path already lets open business settle and starts nothing new.
- `secession` - its off path sets every clock to 0.
- `pressure` - its off path clears `pressed`.
- `crown_split` - **its off path left a running `crown.split` alone**, so the Crown's card
  would have read "SPLITS 2" for good. It now clears it.
- `all_cards` and `detailed_log` change display only.

Switched back on, each one starts from nothing at the next turn, with its warning.

How it works:
- `IC.refresh_live_tune()` reads the six from MCT and writes any change into IC.TUNE **and**
  into the frozen `derpy_ic_tuned`, so a save keeps the change if MCT is later removed.
- It runs at the end of `IC.freeze_tune` (every load) and on MCT's `MctFinalized`, through
  listener `ic_live_tune`. MCT fires that event in single player when the player presses
  Finalize (`mct:finalize`, groovy_mct.pack).
- It is never run in multiplayer.
- A countdown switched off ends AT ONCE, not at the next turn. For every court in `IC.state`
  it calls that switch's own tick; with the switch off, each tick only clears. It then saves,
  because the panel reads every countdown (the card's "SECEDES N" and "SPLITS N", the opener
  tooltip, the log and the intrigue lists).
- One known limit: a house that was counting down only because it was pressed keeps its
  "SECEDES N" until the next turn's secession tick, which then stops it. Recomputing "angry
  without the press" in the refresh would duplicate `tick_secession`'s rule.

**The MCT page:**
- In a single-player campaign, only the six are unlocked. `ai_courts`, the difficulty and the
  numbers keep the "Fixed for the life of a campaign" lock.
- In multiplayer everything is locked with "Not used in multiplayer".
- **The trap:** MCT's `Registry:load_game` puts back every `is_locked` a save was written with,
  after this file has run. Every save made before this build locked all seven switches, so an
  old save would have loaded with the six still greyed out. `relock` now also runs on
  `MctInitialized` (listener `derpy_ic_mct_loaded`), which MCT fires once `load_game` is done.
- Each live switch's tooltip ends "You can change this during a campaign." The page
  description now says which settings are fixed and which are not.

**Checks and mutants.** 648 checks. The four new checks, each watched failing first:
- the six follow MCT at load, while `ai_courts` and the numbers do not, and the change is saved;
- a switch turned off at Finalize clears the clock, the press and the split at once, and saves
  them;
- in multiplayer, neither the load nor Finalize moves a switch;
- on the page, the six are unlocked in a campaign even after every lock is restored, all are
  locked in multiplayer, and the page's live set equals `IC.LIVE_TUNE`.

The harness names the six itself, so a key dropped from `IC.LIVE_TUNE` fails a check. 16 new
mutants; two re-aimed ("the Crown splitting with crown_split off", and "the switches editable
mid-campaign", now "the frozen switches editable mid-campaign"). 476 mutants, all caught
(`mutants_full_live.txt`). The full run found one survivor, "the cleared countdowns never saved": the
check's fixture had never saved the running countdown, so a reload read 0 whether the flip saved
or not. The fixture now saves first and checks that it did.

## 13. Build 226121E7 crashed every new campaign; fixed in D4CC1CE1 (2026-09-25)

**Symptom.** Four crashes at a new campaign's load (20:54 to 21:22), all the same null read at
`Warhammer3.exe+0x281FE44`. The campaign loaded with the pack unticked.

**Cause.** Section 12's `derpy_ic_mct_loaded` listener (on `MctInitialized`) ran `relock`,
which called `is_mp()`, which called `cm:is_multiplayer()`. That goes through `cm:model()` to
`game_interface:model():is_ready_for_script_access()`. MCT fires `MctInitialized` synchronously
from inside its own `LoadingGame` callback, before the model exists. The crashed script log
proves it: it stops after the last `Loading value` and before the `LoadingGame` footer that CA
prints once every loading callback has returned, and this listener was the only new code in
that window. The same `is_mp()` call at the file's own load, earlier still, only logged two
script errors ("model() before the model was created"). `pcall` catches neither kind of fault.

**Fix.** The settings file makes no `cm:` call at all:
- `in_mp` starts false and is set from `context:is_multiplayer()` on `MctInitialized`. MCT works
  that value out itself, in `Registry:load`, before the load starts.
- `relock` reads `in_mp`, so the file's own load treats the campaign as single player until
  MCT answers.
- The model is untouched: `IC.is_mp()` runs from the first tick onward, when the model exists.

**Check.** "the MCT page never asks the campaign anything while the game loads" runs the page's
load, its `MctInitialized` listener and its `MctFinalized` listener against a `cm` that records
every access. It failed first ("called cm:is_multiplayer, cm:is_multiplayer, cm:is_multiplayer
while loading"). The multiplayer half of the page check now passes MCT's context instead of
stubbing `cm`. Mutants:
- "crash: the MCT page asking the game about multiplayer while it loads" (new);
- "live: MCT's multiplayer answer ignored" (new);
- "live: the switches open in multiplayer" and "live: an old save's locks never lifted"
  (re-aimed).

Every `mct:`, `live:` and `crash:` mutant is caught (46). The full run was not repeated: only
the settings file and two harness checks changed. 649 checks, 478 mutants.

**Deployed** to `data/` after the game was closed: 8,991,481 bytes, MD5
`D4CC1CE112ABDE5256C024D538D60D8E`, the same in Modpacks. (A first build, `49C7AEB2`, went into
Modpacks while the game was running. Packs are not byte-reproducible, so the deploy's rebuild
has a different MD5.) Not yet loaded in game.

## 14. Parties dealt evenly; a leaderless party of the player's gets a lord on the map (author: "fix and build both", 2026-09-25)

**Why.** The author's Conclave start showed the Chain with 7 members and two rivals with none,
and their own party with Ghorth alone: "how did one party get 7 members while the other party
gets none?" Ghorth is the Crown's by fixed history, and the one lord went to an empty lead. The
two heroes and four garrison commanders each got an independent roll among the four seated
parties, and all six rolled the Chain (1 in 4,096). The random roll tested fair live, and three
earlier Ghorth starts that day dealt a mix. So it was bad luck, but nothing stopped it. Before
that, the author asked for a leaderless party's lord to be "spawn[ed] on the map but without all
the event logs that will show, the lord should also have the recruitement effects just like
recruiting one newly": the pool lord it replaces cannot be seen until hired, so the card read
"no leader".

**The deal** (`IC.fill_tally`, `IC.fewest`, `IC.roll_background`, `IC.background_for`,
`IC.leaderless_bg`, `IC.can_lead`, `IC.stamp_court`):
- Each man goes to the seated party with the fewest members, the Crown included, ties rolled.
- A man who can lead (a lord, or since today a garrison commander; never a legend or a
  greenskin) goes first to a party with nobody to speak for it, the fewest-member one of those.
- `stamp_court` deals lords, then garrison commanders, then everyone else, whatever order
  `character_list` gives. Origin and ambition are still rolled man by man in list order, so
  their draws are unchanged.
- One tally per pass is read off the traits once and then kept by hand, so a pass never waits
  on `has_trait` for a trait it just added. It is filled on first use, so a turn with nobody new
  counts nothing.
- It applies at a new court and to every man who joins later (`ic_born`, a hire, a
  confederation). It does not reshuffle men who already have a party: the author's current save
  keeps its 7 / 0 / 0.

**The field spawn** (`IC.field_leader`, `IC.recruit_rank`, `IC.hire_region`, `IC.ensure_leaders`):
- A leaderless party first takes an idle Crown lord, as before. Failing that, a player's party
  gets one lord alone at the capital, once per party per campaign. After that, and always for
  the AI, a lord goes to the recruitment pool as before.
- The spawn uses `cm:create_force_with_general` with an empty unit list at
  `find_valid_spawn_location_for_character_from_settlement(..., false, true, 5)`. With nowhere
  to stand (-1, -1), the pool gets the lord that turn.
- It is quiet: `wh_event_category_character`, `_agent` and `_traits_ancillaries` are shut before
  the spawn and reopened by a one-second `cm:callback`. That is CA's own pattern from the
  Mortarch spawn (`wh3_dlc29_nag_mortarchs.lua`), since the spawn's messages arrive after the
  frame.
- The callback sets the party's background. The man's own `CharacterCreated` fires first, and
  `ic_born` deals him to whichever party is empty first, which need not be his.
- **Recruit rank.** Measured live: a script-spawned lord arrives at rank 1 even under a +10
  lord recruit rank bundle. So the callback raises him by `IC.recruit_rank` at the capital, which
  is the sum of `IC.RECRUIT_RANK`. That table is every source in CA's DB, 151 rows as of 9.0: 87
  buildings, 33 bundles, 29 technologies, 12 skills.
  - No race filter: a Chaos Dwarf can hold a captured landmark's `_other` variant, and the slot
    walk costs the same either way.
  - A "province" source (the Tower's living quarters 1-3) counts only in the capital's province.
  - Every other source counts from anywhere, once per building standing.
  - Bundles count whether the faction or a region holds them.
  - Left out: `_hidden` twins (same value, would count twice), force/army/foreign/preview
    scopes, skill levels above 1, and the 10 building rows gated by a `context_requirement` (none
    of them Chaos Dwarf).
  - Chaos Dwarf sources: gold resource +1/+1/+2 and living quarters 4 +2 (everywhere), living
    quarters 1-3 +1/+2/+2 (their province), Sorcery 5 +2, the Grimnir relic +5, Astragoth's
    Infernal Lord +3.
  - `gen_iron_court.check_recruit_rank` re-derives the table from db.pack on every `--check`
    and prints the block to paste when a patch moves a source.
- **By, not to.** CA's `add_agent_experience(lookup, n, true)` calls `level_up_agent_rank`, so
  it raises by n. The harness stub sets the rank to n. The older callers (hire, rebels) were
  written for the stub, so a hired officer lands one rank over his office bar. That is harmless
  and was left alone.
- **Saved** as a 17th house field, `fielded` = the turn the army was asked for (0 or absent in
  older saves). The same turn, the party waits for the army rather than pooling a lord. A later
  turn with the party still leaderless goes to the pool. That also covers a spawn the engine
  accepted and never delivered.

**What the author's current save does on its next load.** The Ledger and the Forge are
leaderless, with lords waiting in the pool (`stored`). The Crown has no idle lord (Ghorth is a
legend). So each gets a lord on the map at Zharr-Naggrund on the first tick, at the rank a lord
hired there would have. The pool lords stay in the pool; hiring one adds a second member to that party.

**Checks** (656; six failed first, and the seventh passes on the old code by design):
- "a new court deals its men evenly, the Crown included" (Crown 7 of 8 before);
- "a lord, then a garrison commander, leads a party with nobody to speak for it";
- "a man who joins mid-campaign goes to the party with the fewest members";
- "a lord put in the field is given the recruit rank the engine would give him";
- "a human party with no leader gets a lord on the map, quietly, at his recruit rank";
- "an army still on its way is not sent twice, and nobody waits in the pool for it";
- "an AI party with no leader keeps the pool" (passes on the old code; it guards the rule).

The harness wrapper stub now finds a faction on the map, fires `ic_born` and then the
callback, and with `cm._force_async` holds back the whole landing. The first version held back
only the callback, and the mutant "a lord pooled while the army is on its way" survived it.
Stubs added: `has_skill`, `has_technology`, faction and region `has_effect_bundle`,
`slot_list`, `find_valid_spawn_location_for_character_from_settlement` and
`disable_event_feed_events`. The stub check held them against CA's member index.

**Mutants:** 26 new (`deal:`, `field:`, `rank:`), all caught. Three re-aimed: "a lord dealt
anywhere while a party has nobody to lead it" (its anchor was the old `leaderless_bg` call)
"the lord in store forgotten by the save" (the pack line now ends in a comma), and "a moved lord
keeping his old trade too" (the full run reported its anchor matching twice, the second time inside
the field callback, which now has its own mutant). Full run: 501 mutants, 0 unexplained.

**Deployed** to `data/` with the game closed: 9,011,926 bytes, MD5
`86E7E6119FE2BA8775DA6D4CD730728E`, the same in Modpacks; all four scripts read back out of the
deployed pack byte-identical to the workspace. The previous build is
`data/derpy_iron_court.pack.bak_pre_fairdeal_20260925`. Not yet loaded in game.

## 15. A refused party waits five turns before it demands again (author: "yes do the fix of the multiple demand", 2026-09-26)

**Found in the log** of the first campaign on 86E7E611 (`script_log_250926_2255.txt`,
Conclave). On turn 1 the Road demanded the Plain of Zharr for cqi 1446 and the author refused.
On turn 2 the Road demanded the same province for the same man again. The demand act's `can` only
blocked while a demand was open; `settle_demand` cleared it and nothing remembered the refusal.
A player who kept refusing lost the party 10 loyalty every turn and walked it towards secession.
This was older code, not the new deal.

**The rule.** A refusal (the REFUSE button, the turn limit, the post given to another man, or
the engine failing the mission) sets `rest[slug]` = this turn + `T.party_demand_rest` (5). That
party makes no demand until then. Other parties may still demand, and a met or void demand rests
nobody. The rest is per party, not per target, so a refused party cannot switch to a different
post the next turn either.

**Saved** as a sixth `|` field of `derpy_ic_agenda_<faction>`, `slug,turn;...`, read and written
exactly like the feud rest `calm`. Older saves have five fields and load with nobody resting. So
the author's current save will see the Road demand once more, and after a refusal it will wait.

**Checks** (658): "a refused party asks again only after its rest, and a reload keeps it"
(failed first), and "a met or void demand leaves its party free to ask again", which passes on
the old code; it guards against the rest over-reaching.

**Mutants:** six new (the guard removed, off by one, no rest set, met and void resting too, the
rest not saved, the rest not read back), all caught. "the one-live-demand guard removed" was
re-aimed, because its anchor included the line the rest check now follows. Full run: 507
mutants, 0 unexplained.

**Deployed** to `data/` with the game closed: 9,012,777 bytes, MD5
`773446188810092A83D5F68018B564D2`, the same in Modpacks; all four scripts read back out of the
deployed pack byte-identical to the workspace. The previous build (86E7E611) is
`data/derpy_iron_court.pack.bak_pre_demandrest_20260926`. Not yet loaded in game.

## 16. The panel wears the Hell-Forge's art (author: "use more of the chaos dwarf ui borders and elements", 2026-09-26)

The author pointed at the Hell-Forge panel. Its pieces live in `ui/skins/default/dlc23_chd_hell_forge/`
and the race skin `ui/skins/wh3_dlc23_chd_chaos_dwarfs/` (ui2.pack); CA's layouts are
`ui/campaign ui/hellforge_panel_*.twui.xml` in ui3.pack. Four swaps, no layout change except the
tab row and the title:

- **Tabs:** CA's skull-capped `tab_square_large_text_*` (the Armoury tab), 240 wide instead of
  150, pitch 244 from x 18. `ICUI.TAB_PLATE` lights them the same way.
- **Title:** the race skin's arrow-ended `panel_title.png`, name centred; `ic_title` is now
  (18, 8, 600, 44).
- **Cards** (office, party, move, the dial and Crown plates): the Hell-Forge's
  `cap_group_name_holder.png`, a bronze rim round a dark field, at margin 8. It was
  `panel_back_border.png` at 30.
- **Seats counter:** the Hell-Forge's `sub_title.png`, margin 6.

**Trimmed copies, not CA's files.** The tab art is 354x103 with the bar in rows 8-43 and the
selected glow below; fitting it needed a layer bigger than its box, and the preview (like a
resized runtime component) sizes every layer to the box, which drew the tabs 20px left and
every card with a dark strip down one side. `CHD_CUTS` in `gen_ic_ui.py` names each piece and
its measured alpha box; `cut_chd_art()` cuts them out of the installed ui2.pack into
`ui/derpy_ic/chd_*.png` on every write, and `art_paths()` owns them so the pruner keeps them
and the deploy ships them. Every layer now fills its box with no offset. These are CA art: the
GitHub sync must keep excluding images.

**Margins are measured.** The emitter now takes a `(vertical, horizontal)` margin tuple,
symmetric only, because no CA file says which horizontal value is the left one. The tab's
skull and bezel end at column 38 of the trimmed art and its bar rounds off by 45, so it is
sliced at 40 and a label keeps 46 clear (CA slices at 65, which left "Petitions" 72px at
1600 and check 20g refused it). The banner is sliced at 111, CA's 165 less the 54 columns the
trim takes off.

**Checks:** check 12 finds the frame by path as well as by "border" in its name; the
corner self-test injects `BORDER_CORNER - 1` instead of a typed 18, which the new 6px floor
would have let pass; the new globals are declared `NOT_GEOMETRY`, which the scale pass
refused to build without. `--check`, `--selftest` (1789 GUIDs), the harness (658), the
backdrop contrast check and the packing verify all pass.

**Deployed** with the game closed: 9,129,242 bytes, MD5 `9C190A4334A4A5EEBBA28AC9C699776E`,
the same in Modpacks; the four scripts, twelve layouts and six new pictures read back
byte-identical. The previous build (77344618) is
`data/derpy_iron_court.pack.bak_pre_chdskin_20260926`; pre-change sources are in
`Modding Files/source/iron_court_bak_pre_chdskin_20260926/`. **Not yet seen in game:** the
preview is TWUI Studio's approximate rasteriser, so the tab caps, the banner and the frame
corners need a look on a real screen, at 1600 as well as 1920.

## 17. Heading plates, and embers on a held seat (author, 2026-09-26: "parties of the court and control of the court doesnt have any background" / "active seats should also have the background have effects, similar to the commission mod")

**Heading plates - rebuilt the same day.** The first try put every bare heading on the Hell-Forge's
`sub_title.png` in its 22-26px cell. In game (author: "it looks poorly implemented") that read as a
line through the words: the plate's field is as dark as the backdrop so only its 3px rim shows,
and the 20px text covered both rims. It also plated the list's column headings and the 1884px
sentence under the tabs. Now: only the two column titles and the four Intrigue move groups are
plated, on the Hell-Forge's spiked `side_panel_title.png`, cut and SHRUNK to `HEADING_H` 44 by
`cut_chd_art` (a `CHD_CUTS` entry may carry a third value, a height) into `ui/derpy_ic/chd_heading.png`,
sliced `(0, 34)`, text centred with `HEADING_TY` lifting it onto the field (rows 17-66 of 90). Room:
`COL_TOP` 110 -> 102 and `COL_HDR_H` 44 with no gap, so the column bodies stay at 146 (the divider
rises 8px); `PLOTS_HDR_Y` = `ROWS_Y - 20`, so the move cards stay put. Lua `PANEL_XY` and
`ICUI.PLOTS_HDR_*` match. **The preview now honours `textyoffset` and centres each line on the
glyphs' middle** (PIL anchor `lm`): it had drawn text ~5px lower than the game, measured against
the author's in-game shot of the same cell.

**Embers.** A held office card carries the commission's ember drift. `derpy_ic_fire.twui.xml`
(prefix IC37) is the commission's `embers` emitter from `derpy_chd_rite_fire.twui.xml`,
re-emitted by `gen_ic_ui.fire_xml()` from a template with only the spread (300) and the count
(40) changed, and its own copy of the sprite at `ui/derpy_ic/ember.png`, so the court does not
depend on the commission pack. `ICUI.card_fire(card, lit)` creates it into the card on first
need, MoveTo's the root to the card and the emitter to the card's bottom centre less
`ICUI.FIRE_LIFT` (10, scaled), and hides it when the seat empties; `draw_offices` calls it
per card, pcall-wrapped. `check_fire()` (check 1b) refuses a particle not named
`template_particle` (a crash on panel open) and an emitter without exactly one particle.

**Checks:** the harness gains "a held seat carries embers on its own card, and an empty one
none" (659), seen failing with the call forced off. Two gen_ic_ui self-tests had gone stale
with section 16 and are fixed: the compact-copy count now allows `FIRE_FILE` (no text, so no
compact twin), and the frame-band injection derives `band - 1` instead of a typed 18, which
the new 8px band no longer contained. **The embers cannot be previewed** - TWUI Studio draws no
particles - so their look, density and the lift need a look in game.

**Deployed** with the game closed: 9,149,733 bytes, MD5 `D2610F37C8DC66777BEE87DFFAC2107A`, the
same in Modpacks; the fire layout, `ember.png`, the panel Lua and layout read back byte-identical.
The gate refused the first try: `ICUI.FIRE_LIFT` is scaled, so `import_iron_court` wants the
generator's own `FIRE_LIFT` (now in `SCALED_SCALARS`, defined above the scale pass). The previous
build (9C190A43) is `data/derpy_iron_court.pack.bak_pre_embers_20260926`.

**Redeployed** with the rebuilt headings: 9,159,696 bytes, MD5 `8100AB1AD3A72C87C97108E0569539BB`, the
same in Modpacks, five files read back byte-identical. D2610F37 is
`data/derpy_iron_court.pack.bak_pre_headings_20260926`.

**Plates fitted to their words (author: "why is it all stretched to the corners? the title is even not
fitted properly, double check your logic").** Two faults, one root: each plate was sized to its CELL.
The column titles drew 926px of bar with the arrows at the far corners; the banner was squashed from
its native 56px to 44, which shrank its field (rows 12-40) to 22px under a 24px title, and the title's
`ty` was `LABEL_TY`, a 4px push DOWN. Now `ICUI.fit_plate(c, key, text, cap, left)` runs after each
`set_text` on `ic_title`, `ic_col_left/right` and `ic_plotcat_1-4`: width = the engine's
`TextDimensionsForText` + 2 x (cap + `PLATE_GAP` 14), capped at the cell, centred in it (the banner
keeps its left end). Caps: `HEADING_CAP` 34, `TITLE_CAP` 111, all `NOT_SCALED`. `ic_title` is
(18, 4, 600, 56) with `TITLE_TY` lifting the words 2px onto the field. `gen_ic_ui.fit_plate` +
`FIT_PLATES` are the same rule for the preview; the preview also stopped drawing `ic_plotcat_*` twice
(a full-width copy had hidden behind the fitted one). Harness check "a title plate hugs its words"
(660), seen failing with the fit disabled. Deployed to data/ on 2026-09-27 (backup
`derpy_iron_court.pack.bak_pre_fitplates_20260926` holds 8100AB1A): MD5 `81506DDF59EBF65024206823E3B8E91F`,
9,161,430 bytes, the plate, the UI Lua and all 13 twui files byte-verified against source.

## 18. One gift a turn, the victim list's labels, a seceded province's governor (author, 2026-09-27: "the blood oath on an anvil says mine is all \"yours\". send a gift should only be once per turn, per party. check logs for inconsistency")

**Send a Gift: once per party per turn.** The log showed two gift clicks one second apart
(354.5s, 355.5s), both taken. `IC.can_favour` now refuses a second gift to the same party in the
same turn with `"given"` (checked after `"content"`); `IC.favour` stamps `house.gifted` with the
turn. It is house save field 18 (`h.gifted or 0`); older saves read nil. `ICUI.reason_text("given")`
is the button's tooltip and the click's notice. Another party, or Secure Loyalty, is not barred.

**The victim list said YOURS for every refusal.** `draw_picker`'s targeting branch drew
`"Legend"` for `"unique"` and `"Yours"` for every other code `IC.may_target` returns. Every party
starts at 55 loyalty (`loyalty_start`) and the Blood-Oath asks 60 (`plot_oath_min_loyalty`), so
every rival on that list was refused as `"cold"` and read YOURS. `ICUI.TARGET_REFUSAL` now maps each
code to one word: YOURS (own party, and nothing else), COLD, SWORN, NO SEATS, NO LANDS, SPENT, NO
PARTY, LEGEND; an unmapped code reads NO.

**The log's one inconsistency: a seceded province kept its governor for a turn.** At 251.7s the
Circle of the Tithe seceded and took Gash Kadrak, which Ghorth (a Crown man) governed.
`IC.turn` runs `reconcile_governors` before `tick_pressure`, where secessions happen, so nothing
cleared him until the next turn. The last step of `IC.secede` now runs `reconcile_governors` and
`apply_governor_bundles` after the hand-over. The screenshot itself was consistent: the
Blood-Oath is move card 7, clicked at 173.8s, before the secession, and it shows the party of 3
the secession logged.

Three checks, each seen failing first: "one gift per party per turn, and the save remembers it",
"the victim list names the refusal it was given, not always Yours" (fails on the old line), and a
governor assertion added to "a province that has stopped caring goes with them". Harness 662.
Deployed to data/ on 2026-09-27 (backup `derpy_iron_court.pack.bak_pre_gift_20260927` holds
81506DDF): MD5 `1260D08A9BE13D1DBDFC6B87E3052AFC`, 9,162,934 bytes, the three Iron Court Lua files
byte-verified against source.

**Plain words on both plot lists (author, 2026-09-27: "what the fuck does cold mean, use easily
understandable terms").** Victim list: Your Party, Low Loyalty, Oath Taken, No Offices, No Governor,
Too Small, No Influence, No Party, Too Famous. Actor list: Other Party (was Rival), The Target (was
Himself), Target's Kin (was His Kin). Each refused row's button now carries `ICUI.reason_text` as its
tooltip (`line.tip`, set every pass in `fill_rows` so a recycled row loses it), and `"not yours"`
has a sentence of its own. Labels were kept at or under 114px measured in Segoe UI Black 18: the
game draws `header_18` about 1.4x that ("Yours" is 51 there and about 72 on screen), and the
button is 170px. The victim-list check now runs all three states on ONE fake panel, so the
cleared-tooltip assertion can fail. Harness 662. Deployed to data/ on 2026-09-27 (backup `derpy_iron_court.pack.bak_pre_plainwords_20260927`
holds 1260D08A): MD5 `E9D6E2F0C4481F3F1F48AA9652C403C7`, 9,163,798 bytes, the three Iron Court Lua
files byte-verified against source.

## 19. Living courts (author, 2026-09-27: "do all"; spec `docs/superpowers/specs/2026-09-27-iron-court-living-courts-design.md`, plan `docs/superpowers/plans/2026-09-27-iron-court-living-courts.md`)

Every confirmed-missing Iron Court feature, built in eleven tasks, each check seen failing first.
Harness 662 -> 690. Deployed to data/ on 2026-09-27 (backup `derpy_iron_court.pack.bak_pre_livingcourts_20260927`
holds E9D6E2F0): MD5 `6B33E4642978E666B6C240D212780F39`, 9,199,754 bytes, 1,723 files, the three Lua
files byte-verified against source. (An earlier Modpacks-only build of the same source was 182F6812.)

**What was built**
1. **Stalled offices.** `IC.stall_office` / `IC.stalled_for` / `IC.end_stalls`; court save field 11
   (`office,ends,of,by,cause`). `IC.apply_office_bundles` ends stalls (turn reached, or the seat no
   longer `of`'s) and skips stalled seats. The office card draws "Stalled - N turns" in red with
   the reason as the button tooltip.
2. **Sabotage** - a feud move only (`feud_move` order sabotage, discredit, rumour; murder first
   once the feud is old). 200 influence, 50%, 3 turns. Card `party_sabotage` (2623).
3. **Withhold** - a party at or under 30 loyalty with 40 motive stalls its own seats for 3 turns;
   Secure Loyalty ends it. Card `party_withhold` (2624).
4. **Settle a feud** on the Petitions tab: Back Them (+10 to one side) or Make Peace (+3 both,
   costs). MP op `arbit`, arg `slug|back` or `slug|peace` (op count 13).
5. **AI courts act.** `IC.party_turn_due` rotates over sorted `IC.ORIGINS` keys, 3 courts a round;
   AI courts answer demands at once (grant under loyalty 50), `IC.ai_placate` gifts a party
   counting down through `IC.can_favour` (so a poor ruler does nothing). Offers and governor
   wages stay human-only.
6. **News of AI courts** - `IC.news` into court save field 12 (`turn,kind,faction,a,b`, max 30),
   only for humans who have met the source; the Log tab merges it with the court's own log. A
   secession raises located card `realm_secede` (2625, `scripted_transient_located_event`,
   `cm:show_message_event_located`); `gen_iron_court --check` 16d/16d2 hold the located set.
7. **Governor rank** - the base bundle is built at runtime (`IC.apply_gov_base`,
   `cm:create_new_custom_effect_bundle`, `set_duration(0)`): order 2 + rank/5, income +rank/2 %
   scoped `province_to_region_own`. `check_gov_rank_constants` holds the Lua constants to the
   generator. The Governors row tooltip gives the figures.
8. **Confederation carries loyalty** - `IC.inherited_loyalty` (weight-weighted, clamped 25-75),
   then `IC.forget_court` wipes the absorbed court's save; `IC.stamp_incoming` takes it as a
   fifth parameter across its retries.
9. **A Chaos Dwarf vassal is one party** - house save field 19 (`vassal` faction key), no men, no
   share, weight 0, no "No seat at court" drift. `IC.reconcile_vassals` each turn plus listener
   `ic_vassal` (`FactionBecomesVassal`, `context:vassal()`, master read off it). At the end of
   its countdown `IC.vassal_break`: `cm:force_break_vassalage`, rebel souring, card
   `vassal_broke` (2626). Confederated later, the vassal party becomes the confederated house
   and keeps its loyalty.
10. **Other Chaos Dwarf factions sour on rebels** by at most 2 steps each (`IC.chd_factions`,
    `rebel_relation_others_max`), the parent and humans as before.
11. Eleven new mutants plus nine re-aimed ones; every one caught.

**Fixed after the final review** (each with a check that failed first): the governor income
effect was scoped `faction_to_region_own` (realm-wide bundles' scope); the governor bundles were
removed with the FACTION call and never came off a province - now
`cm:remove_effect_bundle_from_faction_province` once per province (this was older than the plan,
but the plan made the value rank-scaled); every vassal drifted -1 a turn for a seat it cannot
hold; the `ic_vassal` listener could save an empty court over an AI master not yet loaded.

**Rulings** (full text in `.superpowers/sdd/2026-09-27-iron-court-living-courts/progress.md`)
- each task adds its own log kinds; `(court.stalled or {})` guards; checks search `ALL_ACTS`
  because the harness narrows `IC.PARTY_ACTS`;
- the custom-apply stub also counts into `province_applied`; no `is_null_interface` on a custom
  bundle (CA's `corruption_swing.lua` notes it is broken);
- a Secured vassal does not count down; `IC.chd_factions` reads each faction in a pcall;
- the order effect keeps `faction_to_province_own` - vanilla uses `public_order_faction` only
  with `faction_to_*` scopes;
- **left as found:** the older `ic_dead` / `ic_rank` / `ic_took` / battle listeners can still
  save an empty court over an AI court that has not been loaded since the save was loaded. The
  root fix is in `IC.court`, and it changes load semantics under every check - a follow-up.

**Deferred minors:** the `party_sabotage` card can never fire (feuds never involve the Crown);
the rotation counts dead courts; a vassal breaking under a human master sends no news; news
reaches non-Chaos-Dwarf humans; `ai_placate` skipped on plot turns and with parties off; a failed
`force_break_vassalage` still drops the party; `ic_vassal` reads `master()` outside a pcall; a
confederated vassal nobody stamps keeps its flag; the governor tooltip ignores an absent governor.

**Needs an in-game look:** a stalled office card; a feud on the Petitions tab and both buttons; a
Log tab news line; a governor's tooltip and the province's income/order at two ranks, and a
province with NO governor unchanged when one ranks up; a governor leaving a province takes the
bonus with him; a vassal party card; one AI secession card with its camera button.

**Vassal parties CUT (author, 2026-09-27, on seeing one in game: "cut vassal creating parties for
the main faction, they have their own vassal tab").** Task 9 is gone: no `ic_vassal` listener, no
`IC.add_vassal` / `reconcile_vassals` / `vassal_break`, no house save field 19, no `vassal_broke`
event (2626 is unused again), no Vassal card. A house a 6B33E464 save carries for a vassal loads
without the flag and `IC.reconcile_houses` drops it on the next turn (check "a vassal is no party
of its master's court - the game has a vassal tab"). The four fix-pass items that existed only for
vassals went with it. Seven vassal checks removed, one added: harness 684. Deployed to data/ on
2026-09-27 (backup `derpy_iron_court.pack.bak_pre_vassalcut_20260927` holds 6B33E464): MD5
`5034253630317D3D81C5F9F71840D6BF`, 9,193,089 bytes, 1,723 files, the three Lua files byte-verified.

**A rising is a Hashut army, not a copy of the ruler's (author, 2026-09-27: "why do rebel party
faction copy the leader's units? i thought it will be randomly generated" / "the composition of
the army should be proper and logical, maybe base it one of the crisis events of hashut").** The
log (`script_log_270926_1300.txt`, 283.8s) had `0 of 0 lord(s) able to leave` and `cqi nil`: with
nobody leaving, `IC.rebel_kit` walked the faction's own `military_force_list` and the first army
was the ruler's, so the rebels were his stack again. `IC.REBEL_ROSTER` (a fixed list read in
order) is gone. `IC.REBEL_POOLS` holds six roles - line, missile, screen, cavalry, monster,
war_machine - with the keys and weights of CA's Will of Hashut crisis
(`crisis/crisis_will_of_hashut.lua`, `unit_list`), plus four war machines the crisis leaves out
(magma cannon, deathshrieker, dreadquake mortar, bolt thrower, weight 2). `IC.REBEL_DRAFT` is 19
roles in an interleaved order (6 line, 4 missile, 3 cavalry, 2 screen, 2 monster, 2 war machine)
so any first N slots are a balanced army; `IC.rebel_draw(n)` rolls each slot from its role's pool
by weight with `cm:random_number` (multiplayer-safe), at most `IC.REBEL_UNIT_CAP` = 2 of one key.
A departing lord still brings his own army first (the route a unit mod's units reach the rebels);
it is now filled out off the draft instead of with repeats of his stack. CA's crisis draws all 19
from one weighted bag, which can come out all hobgoblins - the roles are ours.
`gen_iron_court.check_rebel_roster` now holds every pool key to `main_units`, no key in two pools,
every draft role to a pool, and the draft to `rebel_units` (shown to report a misspelt key and an
unknown role). Three checks added, three rewritten (the garrison check now makes the LEAVING man a
garrison commander, since the faction walk that used to reach garrisons is gone - its mutant
survived until then); four mutants added, one removed (padding with his own stack is no longer the
rule). Harness 687; 45 army mutants caught. Deployed to data/ on 2026-09-27
(backup `derpy_iron_court.pack.bak_pre_hashutdraft_20260927` holds 50342536): MD5
`5B0F8999BEEB2FEF03DA6087FA8C41D5`, 9,195,929 bytes, 1,723 files, Lua byte-verified.

**Bug-fix pass (2026-09-28, author: "fix the bugs").** Ten faults from the "what else is missing"
review, each with a check that failed first and a mutant that the check kills (18 mutants in the
filtered run: the ten new, eight older ones re-aimed at lines these fixes moved; 529 in the file).
- **AI court wiped after a load.** Listeners (`ic_confed` host, `ic_born`, `ic_battle`, `ic_took`,
  `ic_rank`, `ic_dead`) and `IC.dismantle` call `IC.loaded(key)`, which loads a court not yet in
  `IC.state`. Not done inside `IC.court`: the harness's `saved` table outlives `IC.state = {}`, and
  a lazy load there broke every check that means "fresh court".
- **Ruthless never saw the soon card**: it fires at `min(warn_turns, secede_turns - 1)`.
- **Dead courts padded the rotation**: `party_turn_due` counts living AI courts only.
- **Sabotage card never fired**: it was gated on the Crown as target, which a feud never is.
- **News to non-Chaos-Dwarf humans**: `IC.hears` = met AND runs a court; used by `IC.news` and the
  `realm_secede` card loop.
- **Switches not fully off**: Provoke starts no clock with `secession` off; `ICUI.mood` drops
  SPLITS/SPLINTERING with `crown_split` off; a Chaos Dwarf faction whose court the settings switch
  off but whose save still holds one is `IC.dismantle`d at its turn start (office, vacancy and
  control bundles, office title traits, governor bundles, the saved court).
- **`IC.ai_placate` skipped on plot turns and with parties_act off**: moved up to right after
  `IC.expire_offers`, before both early returns.
- **Governor tooltip ignored absence**: `ICUI.gov_rank_tip` says he adds nothing while away
  (`apply_governor_bundles` skips an absent governor, so the old text overstated).
- Found already fixed: the Harsh preset tooltip. Deferred: greyed MCT sliders showing numbers the
  preset does not use (needs MCT's value setter, not verifiable offline).
Harness 697. Built into Modpacks only (MD5 `160A02AE...`, 9,200,379 bytes, 1,723 files, Lua
byte-verified); not deployed to data/, not pushed.

**UI feedback and effects (2026-09-28).** Spec `docs/superpowers/specs/2026-09-28-iron-court-ui-feedback-design.md`,
plan `docs/superpowers/plans/2026-09-28-iron-court-ui-feedback.md`; the engine lessons are in
`docs/CUSTOM_UI.md` "Effects on a runtime panel".
- **What shipped:** a square-cornered glowing rim (`ui/derpy_ic/seat_rim.png`, our own art in CA's
  measured red, `glow_pulse_t0` on the layer) on held office cards, dim on a stalled seat;
  governor rows lit / dim while away; a one-shot starburst (`derpy_ic_burst.twui.xml`, created
  and destroyed per claim) plus the ritual sound on filling a seat or assigning a governor; an
  answer for releasing a governor (was silent); answer sentences for grant / accept / arbit /
  gift / secure with a lit flash on the party card; a red flash on a failed plot's target party;
  Hell-Forge heat-glow markers on tabs with business waiting; the HUD button pulses for offices,
  court and petitions (not for ungoverned provinces) and its tooltip words every reason; party
  share and loyalty coloured by change since the turn began, with the figure on hover. The
  Steward of the Ash Fields now gives -15% hobgoblin upkeep (+5% vacant) instead of Growth.
- **Probe (in game, author):** the rim draws and breathes, the burst plays, `pulse_uicomponent`
  is visible but faint. CA's own district rim has rounded corners, hence our own art.
- **Final review** (fresh reviewer) found five faults the harness was green over, all fixed
  with a check that failed first: the failed-plot flash keyed by the man's cqi rather than his
  party; the demand row carrying no party, so a grant named nobody; the button pulsing for
  petitions and ungoverned provinces its tooltip never mentioned; the pulse stopped only in the
  button's current state; the turn-start baseline creating an empty court (a save write) for a
  non-Chaos-Dwarf player. Deferred minors are in the ledger
  (`.superpowers/sdd/2026-09-28-iron-court-ui-feedback/progress.md`).
Harness 713; 559 mutants, all anchored, every new one caught. Built into Modpacks only: MD5
`A54792C5F50A7A5B1646F6323845D8BA`, 9,235,460 bytes, 1,725 files, the three Lua files, the burst
file and the rim art byte-verified. Deployed to data/ on 2026-09-28 (backup `derpy_iron_court.pack.bak_pre_uifeedback_20260928` holds 6406707F), MD5-matched; not pushed. Still unseen in game: the
stop of the button pulse after the panel is closed from its hover state.

**Portrait frames and the row rim (2026-09-28).** Every face cell carries a fourth, fixed layer:
CA's Hell-Forge `dlc23_chd_hell_forge/unit_card_frame.png` nine-sliced at 8
(`gen_ic_ui.FRAME_ART` / `FRAME_INDEX` / `FRAME_MARGIN`); check 13b holds its margin to the
smallest face cell, and the layer-order check now expects plate < face < mask < frame. The
author's "glitches to the governor tab if there is someone in position" was the row rim: the
card rim's 40px nine-slice margin on a 61px row overlapped itself into a red wash with corner
blocks. Rows now wear `ui/derpy_ic/seat_rim_row.png` (same colour and profile, faded by 20px,
margin 20; `ICUI.RIM_ART_ROW`), and check 13 measures every rim layer against the component it
sits on (it failed on the row first). Script log `script_log_280926_1540.txt` on A54792C5: all
three files loaded, the court ran, no script errors, `event_error_logs` empty. Build
`7B34D7270FFCE04271B2142FB99A756F`, 9,240,059 bytes, 1,726 files, byte-verified; deployed to
data/ (backup `derpy_iron_court.pack.bak_pre_frames_20260928` holds A54792C5); pushed to GitHub.

**Thicker frames, recruitment, the Crown block (2026-09-28).** Author, on build 7B34D727:
"make the borders thicker, the character portrait permeates thru the border"; "no icons or
separation in the crown panel"; "remove also hiring heroes from the assigning part ... influence
adjusted to their level".
- **Frame:** our own `ui/derpy_ic/portrait_frame.png` (`gen_ic_ui.frame_pixels`, CA's measured
  bronze, opaque from the first pixel, 4px of bronze) replaces CA's unit_card_frame, whose
  outermost pixel is transparent and next one a 65% black line, so the portrait's outer 2px showed
  round the bronze. The layer is pushed `FRAME_OUT` = 2px past the cell (offset -2, +4 size).
  `check_portrait_frame` holds the opaque edge, the 4px band, the clear middle and the push; its
  selftest breaks each. The preview had been forcing every layer to its cell's size - it now keeps
  a layer's own size delta, which also drew buttons squashed before.
- **Hiring removed.** IC.HIRE, IC.hiring, IC.hire_cost, IC.can_hire, IC.hired, IC.hire, the `hire`
  MP op, TUNE.hire_standing, the picker's Hire rows and the importer's IC.HIRE check are gone
  (the `hire` log kind stays, for old saves). `IC.price_recruit` on CharacterCreated gives a man
  born into a rolled court, once, `IC.recruit_influence(rank)`: the SEAT LADDER read off
  TUNE.tier_rank / tier_influence, evenly in between, clamped at both ends (5 -> 100, 12 -> 200,
  20 -> 300, 30 -> 400). Before, a recruited man started at 0.
- **Crown block.** Icons on the share (ICUI.COST_ICON), band (ICUI.BAND_ICON, CA's
  chd_toz_tier.png) and effect lines (ICUI.FX_ICONS by short label: public_order, income,
  military_spending, growth - CA's own icons for those effects), the Crown's crest on its party
  line, and three flat-fill rules (ic_crown_rule_l/r/v) in ICUI.COLUMN_KEYS. The left half is
  322 wide, not 316: the band line with its icon measured 260px in a 257px compact cell.
  `import_iron_court.check_fx_icons` holds FX_ICONS against the bands' EFFECT_SHORT labels and
  CA's effects.icon; gen_ic_ui check 23 now verifies an `ICUI.*_ICONS` table's paths too.
Harness 711; 569 mutants all anchored (new: 4 recruit, 5 Crown; 2 re-aimed). Build
`9588EE3E7E707FD6C06D28C7D5D5836F`, 9,243,255 bytes, 1,727 files, byte-verified. Deployed to data/
(backup `derpy_iron_court.pack.bak_pre_crown_20260928` holds 7B34D727); not pushed.

**Aggressive rebels, the help page (2026-09-28).** Author: "make the rebel faction aggresive"; "add a
help button besides the hashut's court with all the information the player needed" (chose a Help page over a tooltip).
- **Rebels:** `IC.secede` now calls `cm:force_change_cai_faction_personality(rebels, IC.REBEL_PERSONALITY)` after the war,
  `wh3_combi_chaos_dwarf_endgame` - the row CA's Will of Hashut crisis forces on its invaders (strategic component
  `chaos_aggressive`, endgame task generators; verified present in db.pack). The qb pool factions kept their startpos
  personality and sat still. On an own-origin rising it changes that house's faction for good, which is the point.
- **Help page:** `ic_help` (CA's Tower of Zharr `icon_button_help.png` on the close button's plate) is MoveTo'd to the
  fitted title plate's end plus the layout's own gap (`ICUI.fit_plate` now returns x, w). It toggles a `help` view
  that is not a tab: `ICUI.help_back` is where it returns, close() never leaves the panel on it. `ICUI.HELP` is ten
  topics drawn through the row pool with `COL_W.help = {[1] = 1528}`, each padded to a page so the pager turns
  topics (padding rows `blank`, hidden). `{name}` in a line is filled from `ICUI.help_vars` - every number in IC.TUNE
  plus seats, tiers and the ladder's ends - and a missing name stays on screen braces and all. gen_ic_ui check
  20c-help measures every line (names as four digits) against the row; the harness fails an unresolved name.
- **Edicts need a governor** (author: "grey out the button"). No script call locks an edict: they are
  `provincial_initiative_records`, not initiatives, so `toggle_initiative_script_locked` cannot reach them. UI only:
  on `SettlementSelected` (+0.1s and +0.5s) and on `ICUI.close`, `ICUI.apply_edict_lock` greys CA's
  `hud_campaign > bl_parent > stack_incentives` children (read from hud_campaign.twui.xml: states active / inactive /
  selected / selected_inactive; the stack's open_message is `commandment_available`) with SetState + SetDisabled when
  `court.govs[province]` is nil. It relights only what it greyed, only in a province the player wholly holds
  (`ICUI.edict_verdict` returns nil anywhere else, so the engine's own lock is never lifted). Tooltip untouched:
  GetTooltipText hard-crashes on a HUD button, so a written reason could never be restored. UNVERIFIED IN GAME:
  whether the engine keeps the state or re-sets it on its own refresh - the live probe was sent after the game closed.
Harness 717; 585 mutants (full run 576/0 before the edict lock; its 9 run and caught). Build
`52BCA382E018400A091AFC863D7A3981`, 9,272,475 bytes, 1,727 files, byte-verified. Deployed to data/ (backup `derpy_iron_court.pack.bak_pre_help_20260928` holds 9588EE3E); not pushed.

**Build 52BCA382 in play (2026-09-28).** Author: the help page "doesnt look very user friendly" and "i can
also issue edicts without a governor still". Both fixed; walked live through the bridge.
- **Edicts found nothing.** The runtime HUD id is `BL_parent` (hud_campaign.twui.xml says `bl_parent`), and the
  buttons are not the stack's children: the running edict's is, every choice is two levels down in
  `clip_parent > stack_background`. And WH3's `string.find(s, "^...")` returns NO values - found probing the
  walk. `ICUI.edict_buttons` now walks the whole stack for `button_*` by `string.sub`; `check_lua_api.py` flags an
  anchored find (`find-anchor`). Proven live by hot-patching the running game: five buttons `inactive` and
  disabled for the Plain of Zharr, strings healthy after. Whether the state holds through the engine's own
  refreshes is still for the author to see.
- **Help page rebuilt** (author chose a topic list and a page): `ic_help_box` (CARD_LAYERS, deliberately NOT a
  tier -1 plate - make_ic_backdrop drops cells a tier -1 plate covers and this card covers the header strip),
  `ic_help_rule`, `ic_help_head` (fit plate), `ic_help_topic_1..12` (tab plates, lit like tabs) and
  `ic_help_line_1..12` at 34px; `gen_ic_ui.help_layout()` deals them, ICUI.PANEL_XY mirrors them literally.
  Numbers filled from IC.TUNE are `[[col:yellow]]`. The button is CA's gold `icon_question_mark.png`. The row
  pool, `COL_W.help`, the page padding and the importer exemption are gone. The 27 new cells pushed the UI
  file's main chunk past 255 constants: `2 * ICUI.DIAL_R` in the wedge and wall loops is `ICUI.DIAL_R * 2` now.
Harness 717; 593 mutants, 0 unexplained; gen_ic_ui selftest ok (554 components). Build
`2BA85110434AD5B5F6A189FBEF7E0217`, 9,370,796 bytes, 1,727 files, byte-verified. Deployed to data/ (backup
`derpy_iron_court.pack.bak_pre_helppage_20260928` holds 52BCA382); not pushed.

**Build 2BA85110 in play (2026-09-28).** Author: "the buttons are not greyed out consistently only at the
start", then "its greyed out but no warning or feedback that it needs a governor".
- **The grey did not hold.** The engine drives these buttons' states itself and put them back to `active`,
  disabled still. `ICUI.edict_look` sets CA's `set_greyscale_t0` shader on every state and the text, the
  Exchange's `EX.set_off` technique; the author saw it hold.
- **And only at the start**: `ic_edicts` was registered WITHOUT `add_listener`'s persist argument, so the engine
  dropped it after the first settlement selected. The harness's `core.add_listener` stub now drops a one-shot the
  way the engine does, which is how the old stub hid it; the edict check selects twice.
- **No reason shown.** `SetTooltipText` on an edict button is ignored - the engine draws CA's edict tooltip
  layout (tried live, "still the same"). `ICUI.edict_note` puts the standing plate
  (`ui/campaign ui/derpy_ic_standing`) as `derpy_ic_edict_note`, a CHILD of `stack_incentives` so it goes when
  the stack does, right of the stack and centred on it, sized by `TextDimensionsForText`: "Appoint a governor to
  issue edicts". Shown on "grey", hidden on "live" and nil; found again every call, since the engine owns the
  stack's children. Measured live at 1920x1080: stack 71x62 at 245,1020, nothing drawn right of it; note
  322,1040, 399x22.
Harness 718; 7 new mutants caught (persist, note missing / left up / never shown / made twice / mis-sized).
Hot-patched live; the author saw the grey follow each selection and the note beside it. The note's resize goes through `ICUI.resize` (the packer refuses a bare `:Resize`). Build `4CB01AE88E79E513A6857171B3C2FEFB`, 9,373,392 bytes, 1,727 files, Lua byte-verified; deployed to data/ (backup `derpy_iron_court.pack.bak_pre_edictnote_20260928` holds 2BA85110), byte-verified; not pushed.

**Build 4CB01AE8 in play (2026-09-28).** Author, of the note: "the ui is not good, improve this". The standing
plate's underlay drew nothing beside the HUD - bare letters over the trim. The note now has its own file,
`ui/campaign ui/derpy_ic_edict_note.twui.xml` (GUID prefix IC39, `gen_ic_ui._edict_note`): the seats counter's
plate, the Hell-Forge's `sub_title.png` at its native 30px, margin 6, text centred, not interactive; the text
leads with CA's `ui/skins/default/icon_governor.png` inline. `ICUI.EDICT_NOTE_PAD` 56 = caps 2x6 + 2x10 air +
the icon's 24, because whether `TextDimensionsForText` counts an inline `[[img:]]` is unmeasured. Previewed off
the author's screenshot with the real art before building. Harness 718; 2 more mutants caught (back on the
standing plate, at its height). Build `A431EEF16A620AE5F7BECB65F6C9EBB8`, 9,376,243 bytes, 1,728 files, the
three scripts and the new layout byte-verified. Deployed to data/ (backup
`derpy_iron_court.pack.bak_pre_noteplate_20260928` holds 4CB01AE8), byte-identical; not pushed.

**Build A431EEF1 in play (2026-09-28).** Author: "edges are too long, make it closer to the edict buttons and
make the text fit with 0.1 borders". Measured live on the note: `TextDimensionsForText` reports 376 for the
words and 409 with the icon, `WidthOfTextLine` 327 and 356 - and the author's screenshot draws ~326 and ~360.
TDFT overstates by ~15% on this face, so the plate built from it carried ~50px of nothing each side. Now:
`tw = WidthOfTextLine(text)`, `side = ceil(tw * EDICT_NOTE_BORDER / 2)` with `EDICT_NOTE_BORDER = 0.1`, width
`tw + 2*side`, text LEFT with `SetTextXOffset(side, side)` (the engine's centring had put the words 40px from
one end and 59 from the other), and `EDICT_NOTE_GAP = -2` because `button_edicts_frame.png`'s art ends at x 69
of 71. Live at 1920x1080: 314,1036, 392x30. The layout file is `align="Left"` to match. Harness 718; 12 note
mutants caught. Build `9633088965F31352DBEDECA4F1BE6639`, 9,376,790 bytes, 1,728 files, byte-verified; game
running, so not deployed then - the author: "didnt i say always deploy it or automate if the game
is not running then deploy it". Deployed on close (backup `.bak_pre_notefit_20260928` holds A431EEF1).
`deploy_iron_court.py` now has `deploy()` (back up the live pack as `.bak_pre_auto_<stamp>`, copy,
byte-compare; no-op when identical), `--wait` (poll every 15s until Warhammer3 exits, then deploy - run it in
the background), `--deploy-only` and `--selftest`, and REFUSES an unknown argument: a `--selftest` passed
while the edit adding it had not applied built and deployed twice. The live pack is that rebuild,
`F29A1A113FC5A400EFFD30AD518BC568`, same source as 96330889 (scripts and note layout byte-verified).
Author, of F29A1A11: "does it scale with higher or lower reso?" Yes, as CA's HUD does: position and size are
read off the live stack and `WidthOfTextLine` at every draw, in the root's units (window / UI Scale, see memory
`wh3-ui-root-is-window-over-ui-scale`); the panel's box factor is deliberately not applied. The note check now
also moves the stack (180,790, 142x124) and a mutant that pins the note at 314,1036 is caught. Test-only change.

**The court button between turns (2026-09-28).** Author: "buttons should be greyed out durign a turn, do that for
the iron court" - with a screenshot of the Exchange's opener grey beside the court's lit one. Mirrors the Exchange
(`EX.player_turn` / `EX.gate_button`): `ICUI.player_turn()` asks `world():is_factions_turn_by_key(player)` and
FAILS OPEN; `ICUI.gate_opener(waiting, live)` sets SetDisabled + the greyscale shader (`ICUI.grey_look`, renamed
from `edict_look`, which the edicts share) and stops the pulse BEFORE the grey goes on; `update_opener_tip` drives
it, so every existing refresh point (placement after a load, the player's turn start, close) asks afresh. New
`ic_turn_end` (FactionTurnEnd, player only, persistent) closes an open court and greys with `live=false`, since the
model still calls it his turn while that event runs. The opener click opens only on his turn but still shuts an
open court. Harness 719; 10 new mutants caught. Build `02D9C71061F4072DEBE0A00B84E04DDC`, 9,379,118 bytes,
byte-verified; hot-patched live; `--deploy-only --wait` deploys it when the game closes.

**The influence plate on the character panel (2026-09-28).** Author: "the influence in the character has the
background stretched out" and "doesnt also change when changing characters". (1) It wore CA's ROUND
`button_round_medium_underlay.png` pulled to 190x22 - a squashed ellipse. Now `STANDING_LAYERS = SEATS_LAYERS`
(the Hell-Forge `sub_title.png`, margin 6), 26 tall like the panel's own `ic_influence`, text left and fitted by
the new shared `ICUI.fit_words(c, text, h)` - the edict note's rule (WidthOfTextLine + `WORDS_BORDER` 0.1, half
each end, `SetTextXOffset`), which the note now also calls. (2) Picking another man inside the open panel raised
nothing the plate listened for. `ICUI.standing_cqi()` asks `character_context_parent:GetContextObjectId(
"CcoCampaignCharacter")` (a plain id read, as CA's prologue script does) and falls back to the map's selection;
`ic_char_switch` (ComponentLClickUp while the panel is open, +0.1s and +0.5s) redraws. Harness 720; 5 new plate
mutants caught (one survived first - the switch test fired once - and the test now switches twice); the edict
note's 4 retargeted onto `fit_words`. Build `B6E693757B1E83F2D9A88BAC946EE3B6`, 9,381,355 bytes, byte-verified;
deployed by the `--deploy-only --wait` watcher when the game closed (22:32; backup
`.bak_pre_auto_20260928_223247` holds F29A1A11), byte-identical. It carries the turn gate (02D9C710 never
deployed on its own). Not pushed.
Pushed to GitHub 2026-09-28 as b99387f (build B6E69375, with every build since 7B34D727); the sync manifest now
lists `derpy_ic_edict_note.twui.xml`.

**Why the button pulses (2026-09-28).** Author: "the button is pulsating, but no info why thats shown". Every
reason was already in `ICUI.opener_tip`, but as status lines among the rest. The tip now opens with
`[[col:yellow]]Waiting for you:[[/col]]` and exactly the pulse's reasons (empty seats, terms ending, parties
leaving, petitions - `ICUI.attention`'s `any`, off the same `court_state`), each naming its tab, then a blank line
and the summary; an ungoverned province stays in the summary with "(Governors tab)" because it marks its tab
without pulsing. Harness 721; 4 new mutants caught. Build `62C28B4D5021B576D0772EEFA4B16A07`, 9,382,303 bytes,
deployed (backup `.bak_pre_auto_20260928_225141` holds B6E69375), byte-verified. Not pushed.

**Only a seat somebody can take pulses (2026-09-28).** Author: "only available empty seats should make the button
pulse since every seat is empty". `court_state` now carries `s.fillable = #IC.fill_plan(faction)` - the Fill
button's own plan: one post per man, the claimed-seat rule, and for a PLAYER's man the seat's tier influence
(`IC.can_appoint`), which is why every seat of a young court sits empty. `attention.offices` = fillable > 0 or a
term ending; the tooltip's waiting line is "Seats you can fill now: N (Offices tab)." and the summary always
counts "Empty seats: X of Y.". Found on the way: "the markers are drawn on their tabs" had passed only because
no seat-holder influence was needed outside the player path - its man now has the influence. Harness 722; 3 new
mutants caught, 10 related re-run and caught. Build `3DFB28D14E443B25615B8C703993D221`, 9,382,627 bytes,
deployed (backup `.bak_pre_auto_20260928_230134` holds 62C28B4D), byte-verified. Not pushed.
Full mutation run on 3DFB28D1: 629 mutants, 627 caught, 2 STALE ANCHORS - "the Offices tab not marked" and "the
button's pulse never stops" aimed at lines this session rewrote (`attention.offices` now reads `s.fillable`; the
pulse call moved into `ICUI.gate_opener`). Both retargeted and caught. Generated files regenerated after the run;
the scripts, MCT settings and all 15 layouts match the deployed pack byte for byte.
Pushed to GitHub 2026-09-28 with build 3DFB28D1 (62C28B4D and 3DFB28D1 together).

**Three silent events carded, a party trait, a sound per answer (2026-09-29).** Author, choosing from a list
of gaps: "add event cards to the three, instead of the birth of origin place trait, do #4, do 5 as well", then
"there is no place indicating the character's party".
- Cards, appended so the index-by-position rule holds: `officer_died` 2626 (names the seat when he held one;
  not routine), `threat_over` 2627 (a party's secession count stopping AND the Crown's split count stopping -
  the split's reset was as silent as the secession's; the Crown's now logs `snub_off` too), `stall_end` 2628
  (only when the stall ran its turns with its man still seated; a stall ended by the man leaving is not "back
  at work"). The last two are routine and both log. New log kinds `died` (n = 1 is a province) and `stall_end`.
- `IC.arranged_deaths[cqi]`: the two murder sites (the player's plot, a party's strike) mark the victim before
  `cm:kill_character`, and `ic_dead` reads and clears the mark, so a murder raises its own card and not a second
  one. The secession's kill sites are NOT marked, on the belief that their posts are cleared before the kill.
  **WRONG - withdrawn the same day by the 2026-09-29 audit:** `IC.remove_house` deletes the house before its
  own clean-up loops ask `house_of_cqi(...) == slug`, which can then never match, so a seceding party's men
  keep their posts; and every man the secession kills reads as a Crown death in `ic_dead` (-8 Crown loyalty
  each, and an `officer_died` card for a post). Open; see the audit list in the session.
- Party trait `derpy_ic_member_<crown | origin | interest_N>`, 73 rows. A rolled name lives in the save and a
  trait's text in the DB, so there is one trait per TAIL ("Party: The Cold Anvil" for "Covenant of the Cold
  Anvil"), N wrapped exactly as `IC.party_name` wraps it; a confederate party uses the origin's display, as
  `ICUI.house_name` does. `tools/gen_iron_court.py model_tails()` reads `IC.NAME_TAILS` out of the shipped Lua,
  and a harness check reads the generated loc to prove key N names tail N. Stamped by `IC.stamp_members` at the
  END of `IC.turn` (after secession and split). Stateless: a man already wearing the right trait costs one
  `has_trait`; only a man missing it is swept for the rest. A confederation mid-turn shows on the next turn.
- `ICUI.SOUNDS`, 14 distinct Wwise names from `audio_base_bnk.pack`'s list, and every refused click now plays
  `UI_CLICK_Cancel_Decline` (the Fill button's own refusal had no sound at all). Whether each name plays from
  `common.trigger_soundevent` is not yet heard in game; an unknown name is silence.
Harness 732 (10 new checks, two old sound assertions moved to `ICUI.SOUNDS`). Full mutation run: 663 mutants,
660 caught, 3 STALE ANCHORS on lines this change moved ("a split count that pauses", "your own house coming
apart on no turn at all", "a stall outliving the man") - retargeted and caught; "a filled seat back to the
generic chime" and "a party murder that kills nobody" retargeted before the run. Generated files regenerated
after. Build `C0E394F5B749138276C09B6471C4E5E6`, 9,467,424 bytes, deployed (backup
`.bak_pre_auto_20260929_090123` holds 3DFB28D1), byte-verified. Not pushed; not yet seen in game.

**The 2026-09-29 audit, and its first four fixes.** Author: "what bugs and logic errors are in the mod?", then
"go ahead". Five read-only reviewers (model 1-2800, model 2800-end, parties + MCT, UI 1-3600, UI 3600-end), each
finding reproduced against the harness stubs where it could be; the game's script logs and the bridge's error log
were clean for the Iron Court, so none of these announces itself. The four fixed, each with a check watched to
fail first:
1. `IC.remove_house` asked `house_of_cqi(...) == slug` AFTER deleting the house, so it never matched: a leaving
   party's men kept their seats and provinces as Crown men, and a term ending took the seat's weight off a Crown
   that never had it. Now collected first; terms cleared; office and governor bundles redrawn when anything moved.
2. The secession's two kill sites (a defecting lord, a departing hero) now mark `IC.arranged_deaths[cqi] = "left"`,
   and `ic_dead` charges `loyalty_member_died` to nobody for a man who left (a murder, marked `true`, still costs
   his party it). Measured before: 60 -> 28 Crown loyalty from one secession, past the split line.
3. `apply_governor_bundles` asked where the man STOOD; `governor_active` (and the panel) say only a lord leading an
   army can be away. The bonus now goes on `IC.held_region(faction, province)` whenever `governor_active` says so.
   The check meant to hold the two together had been inert: its loop rebuilt `govs` from the previous pass's
   filtered table, so its "away" case ran on an empty province. Repaired, with a third case (a hero elsewhere) and
   an assertion that the bonus lands on the governed province's own region. The older "a governor outside his
   province applies nothing" check now uses a lord in the field, which is what it always meant.
4. `house.gov_weight` is derived and was not saved, and `IC.turn` reloads the court before its drift: `IC.load` now
   rebuilds it (`pcall(IC.refresh_gov_weight)`).
Harness 736; 12 new mutants caught. Full mutation run: 674 mutants, 673 caught, 1 STALE ANCHOR ("a hero who
changes sides and stays on yours as well", aimed at the kill step the mark now opens) - retargeted and caught.
Build `D3924CECF45C8DB11E82D6971FBC6A80`, 9,469,789 bytes, deployed (backup `.bak_pre_auto_20260929_094906` holds
C0E394F5), byte-verified. Not pushed; not yet seen in game.

**The audit's second round.** Author: "update stale docs, then do another round of findings". The eight medium
items of the open list below, each with a check watched to fail first:
1. Provoke: a saved `house.provoked` (house field 19; older saves read none) keeps `angry` true in
   `tick_secession`, so a content party still runs out the count. It lasts exactly as long as its count: the tick
   clears it whenever the clock is 0, so a bribe, Secure Loyalty, a calm offer or the switch ends it with no
   other code. Before, the next tick called the count off and raised `threat_over`.
2. `IC.secede` calls `IC.forget_court(rebels)` when it wakes a dead faction. A living rising a party joins keeps
   its court (checked both ways).
3. `IC.settle_switches(faction)` runs the off path of each switch that is off; `refresh_live_tune` loops it over
   `IC.state`, and `IC.load` runs it on every court it reads, which covers the courts still on disk at a load.
   The save after a mid-turn flip is still load-bearing (off, then on again before anything saved, brought the
   old count back); the mid-turn check now reads back with the switches on, since a load with them off clears
   the counts itself and would pass on an unsaved flip.
4. `IC.drop_party_business(faction, slug)` (parties file), called by `IC.remove_house` after the delete - the one
   place a party is ever deleted, so purge, dissolve and secession all go through it: the party's demand is
   voided (mission cancelled), its plot dropped with the upkeep's own log and card, then `expire_offers` and
   `end_feuds`, which already handle a missing house. The three older checks that proved that upkeep now delete
   the house behind `remove_house`'s back, since a save from before this build still needs it; `can_arbitrate`
   was left alone because no feud can outlive its party now.
5. `IC.plot_costs_seat(faction, plot, actor)`: the office the price would leave him under the bar of. The picker
   draws that row's influence cell red and puts the sentence on its button; the move itself is unchanged
   (`enforce_bars` still unseats him at once, as the check proves). Price alone, since a move can fail and pay
   nothing back - the feast's refund is not counted. Help: the seat-loss line says at once for his own move and
   next turn for a rival's plot; the false vacancy-penalty and card-odds lines are gone; the Governors line that
   said every governor must stand in his province (untrue since fix 3 of the first round) now names the lord
   leading an army. `gen_ic_ui.py --check` measured the first wording 19px over the row.
6. `ICUI.mood` RESTLESS reads `IC.TUNE.party_intrigue_line`. PLOTTING stays 25: that is the unseat and recall
   line in `IC.PARTY_MOVES`, which no difficulty moves.
7. Log entries carry `sw` / `kw` (fields 6 and 7; older five-field lines read none): `IC.who_was` gives a rolled
   party's `head.tail`, `"c"` for a confederate one, nil for the Crown. A line written after its party has gone
   (a secession's own line runs in the last step; the drop in 4 ends feuds after the delete) reads
   `IC.departed`, which `remove_house` fills before the delete - in memory only, since every such line is written
   in the same session. `ICUI.logged_name` resolves them; `IC.party_name` now wraps a new `IC.rolled_name`.
8. `ICUI.show_standing` returns before anything asks for a court unless `ICUI.court_player()`.
Also: the patch-note draft's Steward line claimed an empty office raises Hobgoblin upkeep 5%; no vacancy bundle
is ever applied (only removed), so the sentence is gone.
Harness 745 (9 new checks; three older ones that proved the upkeep now delete the party behind `remove_house`,
and the mid-turn switch check reads back with the switches on). Full mutation run: 702 mutants, 698 caught, 4
STALE ANCHORS on lines this round moved or duplicated (the name wrap now in `IC.rolled_name`, the house pack's
new last field, a second `expire_offers` call, a second `if not IC.TUNE.secession`) - retargeted and caught; the
live-switch set was retargeted onto `settle_switches` before the run. Generated files regenerated after.
Build `607ABD91BC60B22F7D690B1FF7AAE605`, 9,475,880 bytes, deployed (backup `.bak_pre_auto_20260929_104441` holds
D3924CEC), byte-verified. Not pushed; not yet seen in game.

**The audit's low items.** Author: "continue on the low priority issues". All eighteen, each with a check watched
to fail first:
1. `IC.dismiss` (not the quiet path) writes `court.last[office] = {cqi, turn}`, so the same man re-seated waits
   `renew_wait` like a lapsed term. The old appointment check re-seated a sacked man; it now advances the turn.
2. House field 20 is `snub_key` (`"-"` for none; older saves read none).
3. Bribe and Pledge reset only `house.clock`. They used to clear `snubbed` / `snub_key` too, so the next check
   announced the same insult again; `house.snubbed` drives only the announcement and the alert, and the per-turn
   snub cost comes from the seat, so keeping it costs nothing. Two older checks asserted the clearing and now
   assert the opposite.
4. `ic_dead` re-applies the governor bundles when the dead man governed.
5. The Court tab's warning names the soonest countdown and says "turn" for one.
6. A demand in the `refused` state (its post given to someone else this turn) greys Accept: `can_grant_demand`
   returns `false, "taken"`, and the row's tooltip tells the player to free the post that turn. Ruling: not
   settling the demand at appointment time - that changed seven checks and closed the same-turn window in which
   the player can still free the post.
7. The calm offer keeps the spec's +7 net. The row and tooltip now print the net (`o.n - party_offer_envy`) and
   say the countdown starts again next turn if the party is still angry.
8. MCT: a greyed slider's lock reason names the preset's value, from `PRESET_VALUES` in the settings file, a copy
   of `IC.PRESETS`' fourteen numbers (the check reads `IC.PRESETS` itself, so a drifted copy fails). Ruling:
   reasons, not values - `set_selected_setting` no-ops on a locked option, and writing values would overwrite a
   Custom player's own.
9. A failed plot that aims at nobody logs its plot key; the Log line reads "<errand> comes to nothing for X" and
   the notice "It did not work. The influence is spent." It used to read "moves against A party".
10. The picker's influence refusal reads "He is N influence short." It named a seat.
11. Provoke carries `effect_no_secession`; `ICUI.act_tip` shows it when secession is off.
12. `demand_state` returns `"void"` with `gone` / `lost` / `short`; `settle_demand` logs it through
    `IC.VOID_REASONS` into the entry's number, and the Log gives each its own sentence.
13. `answer()` - where every player move lands, single player and MP alike - applies the control bundle when
    the move succeeded, so the worn band is the one the panel names.
14. A party at the breaking point with no count yet is listed as leaving in one turn, and its card reads
    SECEDES 1 (both gated on the secession switch). A party dropped there mid-turn used to show nothing.
15. The Crown's split tooltip promises no share: `splinter_weight` is a weight, not a percent.
16. "Free to take their old seat" skips a man who holds another office or governs.
17. `IC.party_turn_due` adds `IC.REBEL_POOL` to the rotation's candidates, so risings take turns like origins.
    Ruling: the pool rather than a walk of the world's factions, which the mod never does and the harness cannot
    stub.
18. `party_placate` sets `placated` fresh each turn, nil when the party is not calmed.
Left alone: the MCT file's `derpy_ic_mct_ready` one-shot listener. Its effect has never been measured, and
nothing in this round depends on it.
Harness 762 (17 new checks; five older ones changed: the appointment check advances past the wait, bribe and
pledge now assert the insult stays, and the calm-offer and Crown-split checks read the new sentences). Full
mutation run: 732 mutants, 725 caught. Six STALE ANCHORS - five in `demand_state` / `settle_demand`, whose void
returns now carry a reason, and the leaving party's governor line, which fix 4 copied into `ic_dead` - retargeted
and caught. One SURVIVOR, "a new man leaves the old one's renewal standing": the renewal check reached the empty
seat through a player's dismissal, which since fix 1 makes the second man the one who waits and hid the first
man's leftover claim; it now seats the first man straight over the second, and catches it. Generated files
regenerated after.
Build `3E2F85705C0A33D74DD4C16879064B43`, 9,483,013 bytes, deployed (backup `.bak_pre_auto_20260929_112111` holds
607ABD91), byte-verified. Not pushed; not yet seen in game.

The audit's list is now empty.

**The UI-effects round's four deferred minors, and two dead functions.** Author: "fix the leftovers and cleanup
code". Each with a check watched to fail first:
- M2: `ICUI.burst` and `ICUI.flash` number every call per host / per party (`ICUI.burst_n`, `ICUI.flash_n`), and a
  timer that is not the newest returns. The older burst check had asserted the fault (the first burst's timer
  taking the second burst away) and now asserts the opposite.
- M3: the governor answer redraws before it looks the row up (`ICUI.refresh()`, then `ICUI.gov_row`). One extra
  redraw on that click, and no held state. The check sorts by overseer so the province moves rows, and asserts
  that it moved, since a fixture that stays put proves nothing.
- M5: `ui/derpy_ic/seat_rim_fail.png`, the rim's edge profile in ash (200, 196, 188), under the look renamed
  `fail` (it was `red`); the layer carries no tint. A layer colour multiplies, so over CA's pure-red art it could
  only ever draw a darker red. `check_rim_slots` now checks `ICUI.RIM_ART_FAIL` and measures that the art's peak
  pixel is not red.
- M6: `ICUI.flash` holds nothing for a card that is not drawn, which is the spec's "when it is on screen". The
  flash waited out its 1.5 s and went off if the Court tab was opened inside it. Ruling: no new effect for the
  Petitions tab - answering removes the row and the tab draws no party card, so a petition's answer stays its
  sound and its sentence, as it always was in practice.
- Cleanup: `IC.house_in_court` and `ICUI.gov_effect` deleted. The one check that called `gov_effect` keeps its
  overseer "(away)" assertions and is renamed.
Harness 765 (3 new checks; the burst and fail-flash checks changed, and the `gov_effect` one lost its two
assertions). Full mutation run: 738 mutants, 737 caught, 1 STALE ANCHOR ("an assigned governor draws no burst",
on the line M3 rewrote) - retargeted and caught. Generated files regenerated after.
Build `EE3EF1D5703EC0CABD1BA559CB4CBD39`, 9,484,204 bytes, deployed (backup `.bak_pre_auto_20260929_120407` holds
3E2F8570), byte-verified. Not pushed; not yet seen in game.

**Pictures on the panel's figures and help page, a picture per trait kind, and the stuck influence plate.**
Author: "add markers and icons whenever possible" (the help page), then "not only help pages, check if there
are applicable text where it needs to have an icon"; "traits gain also defaults to chaos dwarf warrior"; "influence
panel stayed after closing character ui".
- The plate: `PanelClosedCampaign` fires while `character_details_panel` is still found and still reads visible,
  so the close handler redrew the plate from it; and the close button's own `ComponentLClickUp` had already
  queued `ic_char_switch`'s two redraws (`STANDING_DELAYS`, 0.1 s and 0.5 s), which land after the close. Now
  `ic_char_panel_shut` sets `ICUI.standing_shut`, `show_standing` hides and returns while it is set, and
  `ic_char_panel` (the next open) clears it. The check runs the queued callbacks after the close and asserts the
  plate stays down, then that the next open draws it.
- Traits: every trait the pack mints used CA's `chaos_dwarfs` category, and `character_traits.icon` is a
  `trait_categories` key, so every card wore CA's Chaos Dwarf helmet. `gen_iron_court.py` now ships
  `trait_categories` (v0, `category` + `icon_path`) with one category per kind: `derpy_ic_cat_origin` (CA's
  settlement bundle icon), `_confed` (CA's confederation icon), `_office` (`icon_offices.png`), `_standing`
  (`icon_secure_loyalty.png`), `_ambition` (CA's Conclave influence icon), and `derpy_ic_cat_party_<slug>` for
  each of the nine parties, pointing at that party's own sigil. A background trait and a member trait wear their
  party's sigil; a confederate's member trait wears the confederation icon. Check 13 now asserts each category is
  ours or vanilla's, flags any trait still wearing a vanilla category, and holds each of our paths to a picture
  this pack or CA ships. **Not seen in game.** If the Trait Gained card still shows the helmet, its medallion is
  not the category icon but a portrait fallback, and this change only reaches the character panel's trait list.
- The selftest had failed since C0E394F5: its trait count never learned the member traits (expected 73 against
  146). It now counts one per party a man can sit with, and asserts every trait wears a category the pack ships
  and every category is worn.
- Help page: each topic has an `icon`, drawn in front of its button and heading; every point starts with a
  `{@name}` marker and names the picture of the move, tab or figure it talks about (`ICUI.HELP_ICONS`, or a
  move's own card picture by its key via `IC.plot_by_key`). `ICUI.help_fill` turns a `{@name}` into CA's
  `[[img:]]` markup before it fills numbers, and leaves a name it lacks on screen as written. `fit_plate` gained a
  `pics` count, charged the line box each, because the heading is measured without its markup.
- Figures: `ICUI.units` puts the influence, gold, loyalty or hourglass picture in front of "N influence / gold /
  loyalty / turn(s)", once - a figure straight after `]` (already marked) is skipped, so a second pass changes
  nothing. Applied to the Record, the notice bar, the Petitions tab's second column, a row button's tooltip, and
  the opener, agenda, move and loyalty tooltips; a trait named in a loyalty breakdown wears the trait picture its
  card cell does; the character plate and the opener's share use `ICUI.cost`.
- Ruling - left bare: party cards, office cards and picker cells (measured to the pixel by `gen_ic_ui.py`, or
  fitted and cut on spaces - a path with a space in it would be cut in half), the MCT settings, and event cards.
- `gen_ic_ui.py`: the 20c-help measurer charges a `{@name}` as one picture (it had measured the marker's own
  characters), and check 23 accepts `ICUI.help_icon(` as an indirection. It found one help line 15px over at
  1600 (the Leaving the court countdown line, reworded) and the opener's share line, whose icon argument sat on
  the next line where the check cannot see it (now `ICUI.cost`).
Harness 771 (6 new checks; about twenty older ones now read a cell's words without its pictures through `bare()`,
count a picture as two characters of a row, or expect the picture in front of a figure). One restated assertion
was replaced: the petition check had marked an offer by calling `ICUI.units` itself, so it now reads the drawn
demand row and the Back Them button's tooltip off the panel. Full mutation run: 760 mutants (22 new), 759
caught, 1 STALE ANCHOR ("the reasons listed after the summary", which quoted the opener's share line) -
retargeted and caught. The first runs of the new mutants found four anchors whose `\n` had become a real
newline and one SURVIVOR, the loyalty breakdown's `ICUI.units`: no check read its headline figure. Both fixed.
Generated files regenerated after.
Build `1BE494B489E18A1E4F42B7601B66331B`, 9,493,022 bytes, deployed (backup `.bak_pre_auto_20260929_132240` holds
EE3EF1D5), byte-verified; `db/trait_categories_tables/derpy_iron_court` is in it. Not pushed; not yet seen in game.
Not changed, and could be: on turn 1 `stamp_origin` and `stamp_bg` give every man his traits with
`show_message` on, so a new campaign opens on a run of Trait Gained cards.
