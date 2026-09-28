# Iron Court — player-action / state-change feedback audit

Read-only audit, 2026-09-28. Files (abbreviated below):
- `UI` = `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua`
- `MODEL` = `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua`
- `PARTIES` = `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_parties.lua`

## How the panel's feedback machinery works (read once, applies to every row below)

- **Sound**: `ICUI.confirm(c, good)` (`UI:2429-2443`) plays `ICUI.SOUND_OK` =
  `"UI_CAM_POPUP_Message_Event_Positive"` or `ICUI.SOUND_BAD` =
  `"UI_CAM_POPUP_Message_Event_Negative"` (`UI:2406-2407`) via
  `common.trigger_soundevent`. This is the **only** sound in the whole panel — every
  successful action shares one "good" chime and every refusal/negative shares one "bad"
  chime; no action has its own distinct sound.
- **Pulse ("light up")**: the same `confirm()` call, if given a component `c`, calls
  `pulse_uicomponent(c, true, ICUI.PULSE_STRENGTH=5, false)` then turns it off after
  `ICUI.PULSE_SECONDS=1.5` (`UI:2437-2442`). Per CA's own doc entry (`check_lua_api.py
  --explain pulse_uicomponent`) this is a generic **brightness pulse of the whole
  component**, not a per-edge glow — so "edges light up" is not literally what fires;
  the closest analogue that already exists is the ember effect below. The pulse is
  fired identically for a good or a bad outcome — only the sound differs, the visual
  pulse itself carries no colour/good-bad distinction.
- **Ember "lit seat" effect**: `ICUI.card_fire(card, lit)` (`UI:3665-3686`) creates/shows
  `derpy_ic_fire.twui.xml` under a filled office card and hides it on a vacant one, redrawn
  every `draw_offices` (`UI:3699-3861`, call at `UI:3707`). This **already is** a persistent
  "this seat is taken" visual (comment at `UI:3651-3653` cites the author's own 2026-09-26
  request "active seats should also have background effects, similar to the commission
  mod"). It exists **only for the Offices tab's cards** — Governors, Petitions and Court
  party cards have no equivalent persistent marker.
- **Text strip**: one shared label, `ic_alert` (`UI:5485-5490`), shows `ICUI.notice` (an
  action's own refusal/result text) if set, else a per-view `warn` string (secession/plot
  countdown), else nothing. A success clears `ICUI.notice` to `nil` (e.g. `UI:5868`,
  `5907`, `5934`, `5979`) — so on success this strip usually reads blank, and whatever it
  said about a countdown is what re-appears in its place.
- **Popup event cards**: `IC.feed(faction_key, slug, secondary)` (`MODEL:952-965`) queues
  `IC.raise_feed` -> `cm:show_message_event` (`MODEL:967-983`), an `IC.EVENTS`-keyed
  catalogue (`MODEL:883-913`) of two-line cards with sound and icon per CA's event-feed
  system. This is the flashiest feedback in the mod, but only ~20 of the many state
  changes below are wired to it.
- **Record tab**: `IC.log(...)` (`MODEL:871-881`) appends to `court.log`, read back by
  `ICUI.draw_log`/`ICUI.intrigue_text` (`UI:4489-4522`, `4113-4307`). Every logged action
  is retrievable, but only if the player opens the Record tab later — it is never pushed.
- **Refresh**: `ICUI.refresh()` (`UI:5229-5491`) redraws the whole panel. In single player
  `ICUI.send` (`UI:5942-5951`) calls the model synchronously, so the click handler's own
  `ICUI.refresh()` call shows the new state immediately; in multiplayer the redraw instead
  waits for `IC.after_op` (`UI:5953-5961`) to arrive over the wire.

Legend for the "Immediate feedback" column: **Strong** = sound + pulse/ember + popup card
or distinct on-screen text; **Weak** = sound only, or list-refresh only; **None** = no
mod-authored feedback at all.

| # | Player action / state change | Where it is invoked | What fires now | Evidence (file:line) | Immediate feedback? |
|---|---|---|---|---|---|
| 1 | Appoint to a vacant office (pick a candidate) | `ICUI.on_office_click` -> picker -> `ICUI.on_pick_click` -> `IC.MP_OPS.appoint` | Sound (good) + pulse on that office's card (`ICUI.confirm(office_card, true)`) + picker closes + on next `draw_offices` the ember (`card_fire`) lights on that card | `UI:5721-5741` (open), `UI:5896,5909` (`picked("appoint")`), `UI:3707` (ember) | Strong |
| 2 | Hire a bought officer into a vacant seat | Same picker, `index` arg | Same as #1 (`picked("hire")` shares the same answer fn) | `UI:5913` (`for _, op in ipairs({"appoint","hire","plot","gov"})`) | Strong |
| 3 | Dismiss a seated officer | `ICUI.on_office_click` when seat filled -> `ICUI.send(faction,"dismiss",...)` | Sound (**bad**) + the **same generic pulse** on that office's card (not a distinctly "bad-looking" pulse — brightness only, no red tint) + ember disappears once the seat redraws vacant | `UI:5721-5731`, `UI:5928-5935` | Strong (sound+pulse) but pulse is visually identical to a success pulse |
| 4 | Term expires automatically at turn start (not a click) | `IC.expire_terms` | `IC.feed(faction_key,"office_lost", ...)` popup card if `#done>0`; logged to Record tab | `MODEL:2900-2923` | Strong (popup) |
| 5 | Term ending **next** turn (warning, not a click) | `IC.warn_terms` | `IC.feed(faction_key,"term_soon",...)` popup card | `MODEL:2942-2949` | Strong (popup) |
| 6 | Fill all empty seats in bulk ("Fill Empty Seats" button) | `ICUI.on_fill_click` -> `IC.MP_OPS.fill` | Sound (good) + notice text `"%d seats filled."`; **no per-card pulse/ember refresh call beyond the normal redraw** — the cards that got filled do light their embers on redraw, but none of them pulse | `UI:3461-3473`, `5916-5924` | Strong text, weak per-card highlight |
| 7 | Assign a governor to a province | `ICUI.on_row_action` (govs view) -> picker -> `IC.MP_OPS.gov` | Sound (good) only — `picked("gov")`'s `filled` var is set **only** for `op=="appoint"` or `"hire"` (see row above), so a governor assignment never gets the card/row pulse; list simply repaints on refresh | `UI:5764-5780`, `5885-5896` (note the `if op=="appoint" or op=="hire"` guard) | Weak (sound only, no highlight of which row changed) |
| 8 | **Release a governor** ("ungov") | `ICUI.on_row_action` -> `ICUI.send(faction,"ungov",...)` | **Nothing.** `IC.MP_OPS.ungov` exists in the model and calls `answer()`, which calls `IC.after_op`, which looks up `ICUI.ANSWERS["ungov"]` — **there is no such key**, only `grant, refuse, accept, decline, favour, arbit, appoint, hire, plot, gov, fill, dismiss` are registered. `if answer then answer(...) end` silently no-ops. No sound, no notice, no pulse; only the list re-drawing (because the click handler calls `ICUI.refresh()` right after `ICUI.send`) shows anything happened | `UI:5774-5776` (call site), `MODEL:5260-5261` (`IC.MP_OPS.ungov`), `UI:5877-5882` + `5913` (the registered `ANSWERS` keys — `ungov` is absent) | **None** |
| 9 | A move/plot picked from the Intrigue grid or the party action bar (provoke, purge, bribe, murder, sabotage, discredit, rumour…) | `ICUI.on_plot_click` / `ICUI.on_act_click` -> picker (shows odds %) -> `IC.MP_OPS.plot` | Sound (good/bad depending on `why=="failed"`) + red refusal/"It did not work" text on failure + pulse on the office card **only if the move filled a seat** + popup card `plot_ok`/`plot_fail` via `IC.feed(...,IC.move_result_key(...))` | `UI:5696-5719` (open), `5899-5910` (`picked("plot")`), `MODEL:4503-4504`, `4624-4625` (feed calls) | Strong |
| 10 | Send a Gift / Secure Loyalty (a "favour" on the chosen party) | `ICUI.on_act_click` -> `ICUI.send(faction,"favour",...)` | Sound only (`confirmed(true,false)`); no card pulse (`c` is `nil`); **no `IC.feed` call exists for `gift`/`secure` anywhere in MODEL** — only `IC.log` for the Record tab. The +loyalty is only visible if the player re-opens that party's card | `UI:5824-5850`, `5877-5882` (`ANSWERS.favour = confirmed(true,false)`) | Weak |
| 11 | Grant a party's demand (Petitions tab, Accept) | `ICUI.on_petition_click(ctx,true)` for `p.kind=="demand"` -> `IC.MP_OPS.grant` | Sound only; `ICUI.notice` cleared to `nil` on success (no "Demand granted" text); row disappears next refresh. **No `IC.feed` for a granted demand** — only `IC.log`/`IC.news` (Record tab, own-court only) | `UI:4855-4874`, `MODEL(parties):807-822` (`settle_demand`, outcome=="met") | Weak |
| 12 | Refuse a party's demand | Same picker, Refuse button | Sound (bad) + **`IC.feed(faction_key,"party_demand_refused")`** popup card — the refusal, unlike the grant, gets a card | `UI:4855-4874`, `PARTIES:823-827` | Strong (asymmetric vs. #11 — see gap list) |
| 13 | Accept an offer from a party (gold/backing/troops/calming a rival) | `ICUI.on_petition_click(ctx,true)` else-branch -> `IC.MP_OPS.accept` | Sound only (`confirmed(true,false)`); the actual reward (treasury/standing/unit/loyalty change) has **no on-panel confirmation at all** — no card, no notice text, no highlighted number | `UI:4870-4874`, `PARTIES:1105-1135` (`accept_offer`, no `IC.feed` call) | Weak |
| 14 | Decline an offer | Same, Refuse button | Sound only, no card, no notice | `UI:4870-4874`, `PARTIES:1137-1143` | Weak |
| 15 | A party makes an offer (state change, not a click) | `IC.PARTY_ACTS["offer"].act` | `IC.feed(faction_key,"party_offer")` popup card + appears on Petitions tab | `PARTIES:1073-1080` | Strong |
| 16 | A party issues a demand (state change) | `IC.issue_demand` | `IC.feed(faction_key,"party_demand")` popup card + a real `cm:trigger_custom_mission_from_string` mission objective + Petitions row | `PARTIES:709-745` | Strong |
| 17 | Arbitrate a feud — Back one side | `ICUI.on_petition_click(ctx,true)` for `p.kind=="feud"` -> `IC.MP_OPS.arbit` "back" | Sound only (`ANSWERS.arbit = confirmed(true,false)`); no pulse, **no `IC.feed` call exists anywhere for `arbit_side`/`arbit_peace`** — only `IC.log` | `UI:4868-4874,5882`, `PARTIES:526-542` | Weak |
| 18 | Arbitrate a feud — Make Peace (pay gold) | Same, Refuse button (`"peace"`) | Same as #17 — sound only, gold spent with no on-screen confirmation of the cost/effect beyond the row vanishing | `UI:4868-4874`, `PARTIES:536-542` | Weak |
| 19 | A feud starts between two parties (state change) | `IC.PARTY_ACTS["feud"].act` | `IC.feed(faction_key,"party_feud")` popup card | `PARTIES:463-479` | Strong |
| 20 | A feud ends on its own (upkeep, not a click) | `IC.end_feuds` | `IC.feed(faction_key,"party_feud_end")` popup card | `PARTIES:604-610` | Strong |
| 21 | A feud escalates to murder | `IC.party_strike` (feud_move act) | `IC.feed(faction_key,"party_feud_murder")` popup card | `PARTIES:266-318` (feed call around 318 per grep) | Strong |
| 22 | A party withholds service (loyalty at/under the withhold line) | `IC.PARTY_ACTS["withhold"].act` | `IC.feed(faction_key,"party_withhold")` popup card + affected office cards show red **"Stalled - N turns"** text and a tooltip explaining why (`ICUI.stall_reason`) | `PARTIES:567-580`, `UI:3689-3697`, `3779-3782` | Strong |
| 23 | A party sabotages an office (plot outcome) | `IC.party_strike` | `IC.feed(faction_key,"party_sabotage")` popup card + same red "Stalled" card text/tooltip as #22 | `PARTIES:281-330` | Strong |
| 24 | Office stall ends (turns run out) | `IC.end_stalls` (model) | Card reverts to normal effect text on next redraw; **no card/notice announces the stall lifting** — only silence + the card looking normal again | `MODEL:4930-4947` (function exists, no `IC.feed` call inside; not in the earlier `IC.feed` grep) | None |
| 25 | A rival house's secession clock **starts** (loyalty crossed the line) | `IC.tick_secession` | `IC.feed(faction_key,"secede_warn")` popup card + Court tab's party word turns red (`SECEDES N`) + Intrigue tab's `ic_alert` names the soonest one | `MODEL:3823-3827`, `UI:1386-1387` (mood word), `UI:4442-4459` (intrigue alert) | Strong |
| 26 | Secession clock reaches the "soon" threshold | `IC.tick_secession` | `IC.feed(faction_key,"secede_soon")` popup card | `MODEL:3834-3836` | Strong |
| 27 | Secession completes (party breaks away) | `IC.secede` | `IC.feed(faction_key,"secede_done")` popup card | `MODEL:3712` (per grep) | Strong |
| 28 | A party with nothing to take dissolves instead of seceding | `IC.dissolve` | `IC.feed(faction_key,"dissolved")` popup card + `IC.say` debug log | `MODEL:3867-3874` | Strong |
| 29 | A secession clock is **defused** (party calms back down) | `IC.tick_secession`, `angry==false` branch | **No popup at all** — only `IC.log(faction_key,"snub_off",...)` (Record tab). The player learns of it only by noticing the Court card's word is no longer red on a later look | `MODEL:3840-3843` | None (silent) |
| 30 | Your own house's party splinters off (Crown loyalty too low) | `IC.splinter` | `IC.feed(faction_key,"splinter")` popup card; a pre-warning `IC.feed(...,"splinter_warn")` fires earlier | `MODEL:3765,3785` (per grep) | Strong |
| 31 | A house's own weight/share crosses into a house-vs-house feud, or a party is snubbed by a rival holding "their" office | `IC.loyalty_terms` detects `snub_key`; logged via `snub_on`/`snub_off` | `IC.feed(faction_key,"snub", office_title_key)` (only on the "on" transition, combined same-turn) — snub-off is silent (`IC.log` only, see #29's sibling) | `MODEL:3075-3078` (per grep, `snub` feed) | Strong for onset, none for clearing |
| 32 | Loyalty crosses the low-loyalty warning threshold | `IC.move_loyalty` | `IC.feed(faction_key,"loyalty_warn")` popup card, fired once on the crossing | `MODEL:2959-2971` | Strong (one-shot; no further nagging, which is reasonable) |
| 33 | Ordinary per-turn loyalty drift (every house, every turn) | `IC.drift_loyalty` | **No feedback at all** beyond the stored number — by design, only the threshold crossing (#32) is announced. The party card shows a **trend** line ("Loyalty +2 a turn") computed fresh each draw, but never a "since you last looked" delta | `MODEL:3068-3088`, `UI:3145-3156` (`ic_party_trend`) | None (deliberate, but no delta anywhere) |
| 34 | A party joins the court (confederation/new house) | `IC.add_house` / reconcile path | `IC.feed(faction_key,"party_joined")` popup card | `MODEL:5128` (per grep) | Strong |
| 35 | Governor's edict/effect changes (e.g. loses Military Doctrine because he left his province) | `IC.governor_active`, `IC.province_edict` | Governors tab's **Overseer column text itself** says "Away from the province" style state (`ICUI.gov_holder_text`); no popup, no Record entry found for this specific transition | `UI:3865-3867`, `3931` | Weak (visible only if the tab is open) |
| 36 | Fill Empty Seats has nothing to fill / a demand can't be granted / any other refused click | Any `on_*_click` when the model refuses | `ICUI.notice = ICUI.reason_text(why,spare)` — red-ish text in `ic_alert`, **no sound at all** on a plain refusal path that isn't routed through `confirm()` (e.g. `on_fill_click`'s own early-return at `UI:3464-3468` never calls `ICUI.confirm`) | `UI:3461-3473`, `5824-5835` | Weak (text only, no audio cue that the click was rejected) |
| 37 | Tab needing attention (pending petition, plot landing next turn, vacant seat, term ending) | — | **No tab badge of any kind.** `ICUI.light_tabs` only swaps the selected tab's art between an "on" and "off" plate — every other tab looks identical whether or not something on it needs the player's attention | `UI:1944-1957` (`light_tabs`, only reads `ICUI.TAB_VIEW`/`ICUI.view`) | None |
| 38 | HUD button (closed-panel state) reflects empty seats / expiring terms / a party about to leave | `ICUI.update_opener_tip` | Rich **tooltip text only** (hover-to-read); the button's own art/icon never changes regardless of urgency — a player who never hovers the button gets zero signal that the court needs attention | `UI:1106-1160` | Weak (hover-only) |
| 39 | Party card mood word (LOYAL/RESTLESS/PLOTTING/SECEDES N/SPLITS N/SPLINTERING/SCHEMING) | `ICUI.card_mood`/`ICUI.mood` | Colour-coded: alarming words are wrapped red (`ICUI.MOOD_RED` lookup), calm ones are plain text | `UI:3129-3132`, `1371-1393`, `3196-3199` | Strong (this one is good) |
| 40 | Party share % / loyalty number changing turn to turn | `ICUI.fill_party` | Shows the **current** value and a computed **trend** ("+2 a turn"), never a highlighted "this just changed from X" delta on the number itself | `UI:3093-3104`, `3145-3156` | Weak (no delta, by design) |

## General polish issues found (not tied to one action)

- **One shared sound pair for everything.** `SOUND_OK`/`SOUND_BAD` (`UI:2406-2407`) are the
  entire audio vocabulary — appointing a Chancellor, granting a demand, and filling ten
  empty seats at once all make the identical "ding". No action has a sound of its own.
- **The pulse doesn't distinguish good from bad.** `ICUI.confirm` (`UI:2429-2443`) always
  calls `pulse_uicomponent(c, true, PULSE_STRENGTH, false)` — the only per-call variable is
  the sound; a dismissal's card pulses exactly the same brightness as a successful
  appointment.
- **The ember "lit seat" effect (the thing closest to "edges light up when a seat is
  taken") exists only on the Offices tab.** Governors tab rows, Petitions rows and Court
  party cards have no equivalent persistent "this is occupied / active" visual — an
  assigned governor's row looks identical in kind to before, just with new text.
- **`ic_alert` is a single shared strip** (`UI:5485-5490`) that a success clears to blank —
  so the moment after a successful click, the panel typically shows *nothing* where a
  countdown warning was a second ago, and the only positive confirmation is the one-shot
  sound (and pulse, where wired).
- **No tab attention markers** (`UI:1944-1957`) and **no HUD-button attention marker**
  (`UI:1106-1160`, tooltip only) — both explicitly named in the brief as open questions.
  A player who doesn't hover the button or click into every tab each turn can miss a
  pending demand, an expiring term, or a plot landing next turn.
- **No delta indicators anywhere.** Every number the panel draws (loyalty, share %,
  standing/influence, control %) is the current value only; nothing marks "this changed
  since you last looked here", even though `IC.move_loyalty` (`MODEL:2959-2971`) already
  knows the before/after every time it runs.
- **Asymmetric petition feedback.** Compare rows 11-18: refusing a demand, a feud
  "escalation", an offer being *made* — all get a popup card; granting a demand, accepting
  an offer, and both arbitration outcomes do not. The negative/appearing events are showy;
  the positive/resolving clicks the player actually makes are the quietest thing in the
  panel.
- **`ungov` (row 8) is a genuine dead branch on the feedback path** — not a design choice
  like the others, but a missing table entry (`ICUI.ANSWERS` lists 12 of the 13 `IC.MP_OPS`
  keys). Worth an actual one-line fix: add `ICUI.ANSWERS.ungov = confirmed(true, false)`
  alongside `arbit` (`UI:5882`) — outside this audit's read-only scope, but flagged since it
  is unambiguous, not a judgement call.
- **A plain refusal plays no sound** when the click never reaches `ICUI.confirm` (e.g.
  `on_fill_click`'s "nothing to fill" branch, `UI:3464-3468`) — every other refusal in the
  table above that goes through `picked()`/`confirmed()` at least gets the bad chime; this
  one is silent-but-for-text, which is inconsistent with the rest of the refusal handling.
