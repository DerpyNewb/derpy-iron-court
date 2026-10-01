# Handoff 2026-10-01: one HUD button for the three Derpy openers - spec and plan

**BUILT AND DEPLOYED the same day (see §5).** It started as design and planning; the author
approved the plan and chose native execution, and all seven tasks plus a final review ran in
this session.

## 1. What exists

| Thing | Where |
|---|---|
| Spec (approved in chat) | `docs/superpowers/specs/2026-10-01-derpy-hud-hub-design.md` |
| Implementation plan, 7 tasks | `docs/superpowers/plans/2026-10-01-derpy-hud-hub.md` |

The idea: with two or three of the Iron Court (`derpy_ic_opener`, 44px), the Great Guilds
(`gg_opener`, 44px) and the Zharr Exchange (`derpy_chd_exchange_button`, 48px) installed, one
48px hub button takes the slot beside `resources_bar`, and hovering it shows the mods' own
buttons in a row. With one mod installed, nothing changes. **There is no library mod**: the
same hub Lua ships in each pack under its own path (`derpy_hub_ic/_gg/_ex.lua`), and the
highest `HUB_VERSION` serves all of them.

## 2. Facts read off the code (do not re-derive)

- **Today's slots:** the Exchange is at `bx + bw + 4` (off the strip's RIGHT end). The Guilds
  sit left of it (`slot_x - 44 - 4`), and the Iron Court left of the Guilds. So the row order is
  ic(1), gg(2), ex(3). The hub takes the Exchange's slot and the row runs RIGHT of it, flipping
  left when it would leave the screen (the flip is a plan addition the author has not
  objected to).
- **Placement code:** `ICUI.btn_anchor`/`place_opener` (`zzz_derpy_iron_court_ui.lua` ~904,
  ~1530; no follow poll), `GGUI.btn_anchor`/`follow_bar`/`place_opener`
  (`zzz_derpy_guilds_ui.lua` ~3213-3405), `EX.button_anchor`/`follow_bar`/`place_button`
  (`zzz_derpy_chd_exchange.lua` ~13948-14169). Follow polls: `gg_follow_bar`,
  `zharr_follow_bar`, both 300ms `cm:repeat_real_callback`.
- **Grey/pulse sites:** `ICUI.gate_opener(waiting, live)` / `ICUI.pulse_opener(on)` (strength
  `ICUI.PULSE_STRENGTH = 5`, both states by name), `GGUI.gate_opener(on)`,
  `EX.gate_button(on)` -> `EX.set_off`. The plan has each mod record what it last drew
  (`ICUI.opener_live`, `ICUI.pulsing`, `GGUI.opener_live`, `EX.button_live`) for the hub to read.
- **`ICUI.show_hud` still hides and restores every visible root child** (`:6672`). So the hub's
  poll must only ever HIDE row buttons, never show them.
- **Tests per mod:** court `tools/_iron_court_harness.lua` (`check(name, fn)`, stubs at ~3840,
  opener checks ~3959-4095) + `tools/mutate_iron_court.py` (`U` = UI file). Guilds
  `tools/_guilds_harness.lua` (IIFE + assert, opener blocks ~6455-6628) +
  `tools/mutate_guilds.py` (`U` is **CRLF**, two-line anchors need `\r\n`). Exchange:
  `LUA_BUTTON_HARNESS` / `check_lua_button()` inside `tools/gen_zharr_exchange.py`
  (~11179, ~12646). It is a Python `%` string, so no literal `%` in added Lua. **The Exchange has
  no mutation runner.**
- **Packing:** the court packs through `tools/deploy_iron_court.py` (tuples
  `(workspace-relative src, in-pack dest)`, `SCRIPTS + UI + ART`). `import_iron_court.py` is the
  check side, and its check 9 compares `UI_FILES` against `gen_ic_ui.build_xml()`, so the hub
  `.twui.xml` must NOT go in `UI_FILES`. The Guilds' `UI_FILES` is cross-checked against
  `gen_guilds_ui.FILES` too, so the hub goes in `_pack_files()` instead. The Exchange's
  `import_zharr_exchange.SCRIPTS` holds in-pack relative paths.
- **Live copies:** `data/derpy_iron_court.pack`, `data/derpy_great_guilds.pack`, Workshop
  `3798516851/derpy_zharr_exchange.pack`.
- **GUID prefixes DH01-DH03 are free.** The plan registers them in `docs/CUSTOM_UI.md`.
- **API checked against CA's docs:** `cm:real_callback` / `remove_real_callback` /
  `repeat_real_callback` exist on campaign_manager. `pulse_uicomponent(c, on, brightness,
  propagate, state)`. `ComponentMouseOff` is real (`events.lua:166`, used at
  `wh2_dlc11_vampire_coast.lua:386`).
- **Icon candidates:** 439 CA paths under `ui/skins/` and `ui/campaign ui/` matching
  chd/chaos_dwarf/hashut. The plan's sheet filter also drops technologies and
  settlement-capture art. The court already uses `icon_wh_main_lore_hashut.png`.

## 3. Rulings this session

- The hub's pointer for write-ups goes in `docs/SESSION_INDEX.md`, not CLAUDE.md (CLAUDE.md's
  own rule overrides a hook that asked otherwise).
- The Guilds register no `wants`: their count badge is not a pulse.
- The hub is not `RegisterTopMost`'d: the Exchange's root-created button draws on the strip
  without it.

## 4. Open - next steps

1. Run plan Task 1 (`tools/hub_icon_sheet.py`) and get the author's icon pick. Task 3's `ICON`
   waits on it.
2. Tasks 2-7 as written. Each mod task starts by confirming that the staged Lua equals the live
   pack's copy (memory `pack-lua-carves-out-of-binary`).
3. Another session is editing the Great Guilds files: targeted Edits only.
4. Exchange Steam upload only when the author asks. The in-game checklist is plan Task 7 Step 8.

## 5. Built, 2026-10-01 evening

- **Icon:** the author picked #212, `ui/skins/default/tech_tree_tab_chd_sorcery.png` (the gold
  bull mask), off `tools/hub_icon_sheet.py`'s sheets.
- **Hub:** `Modding Files/source/derpy_hub/derpy_hud_hub.lua`, HUB_VERSION 1. Copies and
  `.twui.xml` (GUIDs DH01/DH02/DH03) written by `tools/sync_derpy_hub.py` (`--check`,
  `--selftest`). `tools/_hub_harness.lua` has 25 checks, all green.
- **Deployed:** Exchange `1f2e4765` to Workshop folder 3798516851 (backup
  `.bak_pre_hud_hub_20261001`, **not uploaded to Steam**). Guilds `31843355` to `data/` (backup
  `.bak_hud_hub_20261001`). Court `df5d67fb` to `data/` (backups `.bak_pre_auto_20261001_*`).
  Each pack's delta against the pre-hub copy is exactly the two hub files plus that mod's UI Lua.
- **Repos:** the Guilds, court and `zharr-exchange` working trees are synced. **Nothing is
  committed or pushed.**
- **Final review** (opus) found one Important bug, and two Minors were re-graded Important. All
  three were fixed, each with a test that failed first:
  1. While the hub managed it, the court's `place_opener` returned before
     `update_opener_tip`, so the button had no tooltip and no pulse, and the hub never pulsed,
     for the whole first turn of a load.
  2. With no `resources_bar`, the hub hid every button and could never show itself. It now
     releases them.
  3. **CA's `remove_real_callback` leaks:** `lib_timer_manager.lua:590` clears
     `real_timer[id]`, not `real_timers[id]`. The hub uses a generation counter instead and
     never removes a timer. **Do not use `cm:remove_real_callback` for frequent timers.**
- **Deferred minors:**
  - The row can flash for up to 300ms when the court closes after being opened from the row.
  - `release()` shows a handed-back button wherever it sits. No mod destroys its button, so this
    path is close to dead.

## 5b. Version 2, same evening: a column, and hover that works

The author, after playing v1: "hover doesnt work still need to click and it goes sideways ,
make it by column instead".

- **HUB_VERSION 2.** The buttons hang in a COLUMN under the hub, each centred on its 48px, 4px
  apart. There is no left flip any more: a column cannot leave the side of the screen.
- **Hover is polled.** `ComponentMouseOn`/`MouseOff` never kept the row open in game. The 100ms
  poll asks `IsMouseOverChildren()` (CA-documented, used by Workshop mods on CA's panels) on
  the hub and, while open, on each column button. A hidden component never counts. The 500ms
  grace is a counter on the poll, so there are no timers at all. One listener is left: a click
  on the hub opens the column at once.
- `tools/_hub_harness.lua` was rewritten for this: 24 checks, failing 12 against v1 and green on
  v2. Five of six hand mutants were caught; the sixth (hide unconditionally rather than only
  when visible) is equivalent code.
- **Same build, Iron Court fix:** zooming the camera dropped the Governors view's party
  highlight (CA's overlay mode 13), and nothing re-lit it because `ICUI.gm_lit` still held the
  set. The engine raises no event and has no getter. The new `ic_gm_zoom` poll (300ms) re-lights
  once the camera's distance has settled at a value other than the one it was lit at. Court
  harness check "a zoom that drops the party's highlight..." failed first; 858 green; 5 of 5
  mutants caught. **Unproven in game:** whether the engine also drops the overlay on a pan,
  which this would not catch.
- Deployed: the Exchange to Workshop 3798516851 (backup `.bak_hub_column_20261001`, not
  uploaded). The court and Guilds go to `data/` (backups `.bak_pre_auto_20261001_200700` and
  `.bak_hub_column_20261001`). The deltas against the live packs are only the hub copy in each,
  plus the court's `zzz_derpy_iron_court_ui_map.lua`. DB tables differ only in RPFM's per-save
  header GUID.

## 5c. Version 3: a plate, an unfold, no close delay

The author, on v2's column: "no animation and no background ui", then "thers also a delay
when hovering out of the ui".

- **HUB_VERSION 3.** A plate, CA's `ui/skins/default/panel_stack.png` (the HUD's
  leather-in-bronze), hangs from the hub's middle to 14px under the last button, 14px either
  side. Its outer ~9px are transparent, which is why the pad is 14 and not 6. Nine-slice
  margins 36,36,16,16, measured off the file: the top-right ornament reaches 36px in, and the
  bottom band sits inside 16. The height is floored at 56 so the slices never overlap. New
  files: `derpy_hub_plate_<ic|gg|ex>.twui.xml`, GUID prefixes DH04-DH06.
- **Draw order:** the root draws its children in list order, so the hub `Adopt`s the plate at
  the index of the first of the hub and its buttons. Ids are compared, not wrappers.
  **Unproven in game:** if the plate draws OVER the buttons, this is the line to look at.
- **Unfold:** five one-shot `cm:real_callback` frames, 25ms apart. Each button slides out of
  the hub with ease-out and fades in with `SetOpacity(a, true)`. A generation counter voids
  late frames. Shut is instant and restores alpha 255, and so does release.
- **No close delay:** `GRACE_MS` went from 500 to 100, so the column shuts on the first poll
  that finds the mouse off the hub, the buttons and the plate. The plate fills the gaps, so
  nothing needs crossing.
- `tools/_hub_harness.lua`: its root stub keeps a child list (Find/Adopt/ChildCount), and its
  `Resize` stub refuses a call without both permissions or without `false`. 27 checks; 6
  failed first. Of 15 mutants, 14 were caught. The survivor was a redundant plate hide in
  `show_row(false)`, which was deleted.
- `import_iron_court.py` check 6d (no direct `:Resize`) now skips the hub copy, which cannot
  call `ICUI.resize`.
- Built and diffed: each pack changes only by its hub Lua plus the new plate file. The game
  was running, so all three wait on background copies that run on exit. The Exchange's
  Workshop copy was refused while the game held it open.

## 5d. Version 4: a fold, and a baked plate

In game, v3's plate drew BEHIND the buttons (the `Adopt` draw order works). The author:
"theres a blurred part on top and bottom of the ui, there should also be a hovering out
animation".

- **Blur:** a nine-slice squeezes a margin-to-margin edge the way any image is squeezed.
  panel_stack's top and bottom frame, 204px between the margins, went into 24px. That 8:1 is
  what blurred. The sides were stretched only 1.5:1 and stayed sharp. `bake_plate()` cuts the
  file into quadrants and joins them at 76x128 (`ui/derpy_hub/plate.png`, no CA art in any
  repo). `check_assets()` re-bakes and compares bytes.
- **Fold:** shutting now runs the unfold backwards: five frames that slide the buttons up into
  the hub and fade them out, and the last frame hides them at alpha 255. `HUB.folding` keeps
  the poll from hiding the column mid-fold. Either animation turns round from wherever the
  column got to. Mid-fold, only the hub reopens it, because the column is shrinking out from
  under the mouse.
- Harness: 30 checks. 4 failed first, and 2 more came from mutants that survived: a check that
  never ran the fold's frames, and a release mid-fold that left `folding` set, so the poll
  never hid a re-hubbed column. 14 of 14 mutants are now caught.
- Deployed: the Iron Court and Great Guilds to `data/` (backups `.bak_pre_auto_20261001_205017`
  and `.bak_hub_fold_20261001`). The Exchange was deployed at 20:50 by the More Resources session,
  which was building the same pack. Its four hub files are byte-identical to the source (v4).

## 6. Faults found that are NOT the hub's

- `tools/_guilds_harness.lua:6253` fails: `gg_title at 2x, got 210,50`, against the deployed
  Guilds UI. So `mutate_guilds.py` cannot run (it needs a green baseline), and the three Guilds
  hub mutants were proven by hand against a copy with only that assert removed.
- `mutate_iron_court.py` has two stale anchors in `zzz_derpy_iron_court_ui_map.lua` ("another
  tab leaves the pins up", "a closed court remembers the view"). They are stale against the
  live pack too.
- `check_lua_api.py`: `ai_test_tower_of_zharr.lua:35` calls an unknown `cm:ritual_is_locked()`.

## 7. Owed in game

**Confirmed by the author, 2026-10-01 21:01, on v4:** hover opens it, the plate draws behind
the column, and the column unfolds on the way in and folds on the way out ("works, theres
animation in and out"). Still unchecked: each mod alone, and the court opened from the column.

Plan Task 7 Step 8. In short: all three installed shows hub then row; crossing the gaps keeps
the row open; each row button keeps its tooltip, grey and pulse; the court opened from the row
closes back cleanly; each mod alone looks unchanged; any pair works. Watch whether the hub draws
under the HUD (it is not RegisterTopMost'd).
