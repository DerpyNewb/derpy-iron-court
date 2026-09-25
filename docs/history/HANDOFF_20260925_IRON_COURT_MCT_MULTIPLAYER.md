# The Iron Court: MCT settings and multiplayer support (2026-09-25)

Spec: `docs/superpowers/specs/2026-09-25-iron-court-mct-multiplayer-design.md` (amended while
planning; see its "Amended 2026-09-25" block). Plan:
`docs/superpowers/plans/2026-09-25-iron-court-mct-multiplayer.md`. Pre-change copies of every
edited file: `Modding Files/source/iron_court_bak_pre_mctmp_20260925/`.

BUILT and deployed to `data/derpy_iron_court.pack` (8,991,087 bytes, MD5 `226121e7`, after the
review fix pass in section 7, the party counts in section 8, Ruthless's pressure line and the two
Purge fixes in section 9, the office terms in section 10, the seven QoL features in section 11 and the six live switches in section 12). Not uploaded. The pack from before this change is
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
