# HANDOFF 2026-09-21 - one line in the Iron Court kills 31 panel listeners across every mod

A diagnosis session. **Nothing was packed and no file in `Modding Files/` was changed.** The
report that started it was "the Workshop mod `!starting_units` does nothing". The mod is
blameless. The fault is two lines in **our own** `zzz_derpy_iron_court_ui.lua`, and it has been
silently starving panel listeners belonging to the Zharr Exchange, the commissions, the Tower of
Zharr, MBXP and the Old World mod for as long as the Iron Court has shipped.

---

## 1. The fault

Live pack `data/derpy_iron_court.pack`, file `script/campaign/mod/zzz_derpy_iron_court_ui.lua`,
**lines 4877 and 4882**:

```lua
core:add_listener("ic_char_panel", "PanelOpenedCampaign", true, function(context)
    if context.string and context:string() ~= ICUI.STANDING_PANEL then return end
    cm:callback(function() ICUI.show_standing() end, 0)
end, true)

core:add_listener("ic_char_panel_shut", "PanelClosedCampaign", true, function(context)
    if context.string and context:string() ~= ICUI.STANDING_PANEL then return end
    ...
```

`context.string` on a panel event is a **plain string field**, not a method. The guard reads it
(truthy), then calls it - `context.string(context)` - and throws
`attempt to call method 'string' (a string value)` on **every panel open and every panel close**.

The fix is `context:string()` -> `context.string`, twice. Nothing else.

### Why it takes 31 other listeners with it

CA's dispatch (`ca_scripts_wh3/_lib/lib_core.lua`, `core_object:event_callback`) is two passes.
Pass one walks every listener and evaluates conditions, collecting winners into
`callbacks_to_call`. Pass two calls them:

```lua
for i = 1, #callbacks_to_call do
    event_protected_callback(eventname, callbacks_to_call[i], context, false);
end;
```

`event_protected_callback` **does** `xpcall` the callback - but only the call itself. When the
xpcall reports failure it falls through to `cm:log_event_error(...)`,
`cm:set_script_state("SCRIPT_FAILED_THIS_SESSION", true)`, `cm:draw_2d_text(...)` and finally
`script_error(error_str .. ..., -1)` - and **that error path is not itself protected**. The
throw escapes `event_callback` and every remaining entry in `callbacks_to_call` is abandoned.

`ic_char_panel` is the third entry in the call order, so everything after it dies:

| Event | Its index | Listeners starved |
|---|---|---|
| `PanelOpenedCampaign` | 9 of 40 | **31** |
| `PanelClosedCampaign` | 5 of 14 | **9** |

Measured starvation on a `units_panel` open (listeners whose conditions pass and which never
ran): `zharr_finance_colour` (#11), `Norsca_Settlement_Captured` (#24),
`better_recruit_filter_panel_opened` (#28), **`add_unit_PanelOpenedCampaign` (#29)**,
`derpy_commission_brand_panel` (#34). On other panels it also reaches `MBXP_UI_Inject` (#31),
`OldWorldSchemesPanel` (#36) and `derpy_toz_panel_opened` (#39). Because `ic_char_panel`'s
condition is the boolean `true`, it is collected for **every** panel, so every dispatch truncates.

---

## 2. The proof

In-memory containment only - the throwing callback wrapped in `pcall` so the error cannot escape:

```lua
local orig = L9.callback
L9.callback = function(ctx) pcall(orig, ctx) end
```

Then the hand-made button was destroyed, the trace table cleared, and the player opened the army
panel once.

| | Callbacks fired on one `units_panel` open |
|---|---|
| **Before** | 3 - `2:campaign_selection_listener, 4:intro_ui_highlighting, 9:ic_char_panel` |
| **After** | **9** - `2, 4, 9, 11:zharr_finance_colour, 24, 28, 29:add_unit_PanelOpenedCampaign, 34:derpy_commission_brand_panel, 40:probe` |

`xz_unit_button exists=true`, created by the mod's own callback with no hand-holding. The
Workshop mod was never broken.

---

## 3. How it was found - the instrument, not the guess

Every static check passed and every plausible theory was wrong. What settled it was tracing CA's
dispatch from inside, in a live campaign, with RPFM shut.

`core.event_listeners[<event>]` is a plain array. Each entry carries `name`, `event`, `condition`,
`callback`, `persistent`, `to_remove` **and `callstack`** - the registration traceback, which
names the file that added it. Both fields are writable, so:

1. Wrap every `callback` with a shim that records `index:name` then calls the original.
   -> showed dispatch firing 2, 4, 9 and stopping, with `#listeners == 40` read at fire time.
2. Wrap every function `condition` the same way.
   -> showed the **collection pass reaching all the way to 39**. So collection was fine and the
   break was in the call pass. This is the step that turned the question around.
3. Wrap listener 29's condition to record `tostring(ctx.string)`, its `type`, and the result.
   -> `string=[units_panel] type=string eq=true cond=true/true` on the **real** event. Its
   condition passes; it is in `callbacks_to_call`; it is simply never called.
4. `pcall` each earlier callback in turn to find which throws.

The whole sequence ran through the game-side bridge - see §5.

---

## 4. Corrections found the hard way

**4a. A listener error CAN break the chain - the `xpcall` is not enough.** CA wraps the callback
call, but the failure handler that runs afterwards is unprotected and `script_error` escapes it.
This session first concluded the opposite from reading `event_protected_callback` lines 1917-1931
and stopped investigating a correct hypothesis because of it. **Read to the end of the function.**

**4b. The retraction was the error, not the finding.** An early sweep called
`p[9].callback({string="units_panel"})` and got the exact throw that turned out to be the root
cause. It was dismissed as an artifact of a hand-built context. It was not: the real context has
the same shape (`type=string`, proven in step 3 above). **When a probe with a synthetic input
reproduces a throw, check whether the real input has the same shape before discarding it.**

**4c. Mod-script globals read `nil` through the bridge and prove nothing.** `_G.vco`,
`_G.victory_objectives_ie` and `_G.ICUI` all read `nil`. CA gives each mod script its own
environment and `wh3_eval` runs in `wh3_mcp.lua`'s. Three conclusions were nearly filed on this.

**4d. A hand-built context manufactures fake errors.** `condition` is frequently the boolean
`true`; CA guards with `if current_listener.condition == true or ...` before ever calling it, so
probing it directly throws "attempt to call a boolean value". **Test `type(condition)` first.**

**4e. `cm:get_saved_value("SCRIPT_FAILED_THIS_SESSION")` returned `nil` the whole time** despite
`cm:set_script_state` being called on every dispatch. It is not a usable read-back for that flag.
Likewise nothing resembling `ERROR - SCRIPT HAS FAILED` ever reached the script log. **Absence of
an error in the log is not absence of an error.**

**4f. The absence of a component name in a script log means nothing.** `xz_unit_button` appears
in exactly one log on this machine because that is the only time anyone hovered it with a UI
debug tool. `[ui] uicomponent X / path from root:` lines are cursor dumps, not an inventory.

**4g. `[ui] Panel opened <name>` comes from CA's own Lua listener** (`lib_campaign_ui.lua:352-354`,
`out.ui("Panel opened " .. panel)`). Its presence proves the event dispatched **at least as far as
index 2** - and, because it concatenates `context.string` into a string, proves that field is a
string. That single log line is what makes 4b provable.

---

## 5. The method: driving a running campaign with RPFM shut

`wh3-mcp/`'s MCP tools were not registered this session and were not needed. The game-side bridge
is a **file handshake in the game root**:

- write `wh3_mcp_command.json` - `{"command":"eval","params":{"code":"<lua>"}}`
- poll for `wh3_mcp_result.json`, read it, delete it

`wh3-mcp/tools/send-eval.mjs` does this but hardcodes `C:\Program Files (x86)\Steam\...`, which is
not this install - the same wrong-drive assumption the server half has. A 30-line Python
equivalent taking the correct path was used instead.

- `eval` already `pcall`s the chunk, so a Lua mistake returns `{"status":"error",...}` as data.
  Still avoid the known hard-crashers (`GetTooltipText` / `GetImagePath` on HUD buttons,
  parameterised CCO calls) - those kill the process, not the chunk.
- `setfenv` puts the chunk in `wh3_mcp.lua`'s environment, so `cm`, `core`, `find_uicomponent`,
  `UIComponent` and `CampaignUI` are reachable. Other mods' globals are not (4c).
- Set `PYTHONIOENCODING=utf-8` or the read dies on cp1252 when a mod ships non-ASCII strings.

---

## 6. RESOLVED 2026-09-22 - fixed, packed and verified

**6a. FIXED.** `data/derpy_iron_court.pack` now ships the corrected file. Both guards read
`if context.string ~= ICUI.STANDING_PANEL then return end`. Pushed with
`add_packed_files` + `save_packfile` into the existing pack - one file, no rebuild: all 1705
paths identical before and after, pack 42 bytes smaller (2 x the 21 chars of
` and context:string()`), and all ten DB fragments re-decoded in a fresh MCP session.
Backups: `derpy_iron_court.pack.bak_pre_listenerfix_20260922` beside the pack, and
`.bak_pre_listenerfix_20260922` beside the staged Lua and the harness.

**6b. RESOLVED - the pack was authoritative, and the corrected file already existed.**
The staged 3021-line copy was an ANCESTOR, not a later edit: its strings are the earlier
wording ("Court record, newest first" against the shipped "The court's record, newest
first"), despite a newer mtime. The shipped 4892-line file is byte-identical to
`.superpowers/sdd/2026-09-20-iron-court-ambition/task-04/after-fix1/`, and
`.superpowers/sdd/2026-09-21-iron-court-humanize/baseline/` holds **that same file with
exactly this two-line fix already applied and nothing else different**. Both were installed:

| | was | now |
|---|---|---|
| `Modding Files/pack/.../zzz_derpy_iron_court_ui.lua` | 3021 lines, old wording | 4892, shipped + fix |
| `tools/_iron_court_harness.lua` | 16782 lines, old wording | 16778, same 459 checks |

The harness had to move with it: its expectations still read `LEAVES IN` / `BREAKING APART`
where the shipped panel says `SECEDES` / `SPLINTERING`. `ICUI.mood`'s LOGIC is identical in
both - only the strings were reworded - so this was a stale expectation, not a behaviour
change. All 58 diff lines between the two harnesses are wording and both carry **459**
`check(` assertions, so no check was traded away.

`import_iron_court.verify()` is **0 findings** with the matched pair, and
`tools/mutate_iron_court.py` goes from **13 stale anchors to 7** - the swap introduced none
and retired six. The seven that remain are pre-existing debt and are listed in that run.

**6c. RESOLVED - nowhere else, and the idiom is now gated.** All 268 packs in `data/` were
swept: `context:string()` appears in exactly one file, the two lines above. CA never writes
it either - across the 831 Lua files in `reference/ca_scripts_wh3` there are **690
`context.string` field reads and zero `:string()` calls of any kind**, so `.string` is a
plain field with no legitimate method spelling. `tools/check_lua_api.py` now carries a
`field-call` rule for it (regex `FIELD_CALL`, with a `--selftest` case that was watched to
fail with the rule neutered). The full scan is 107 files, 0 field-call findings - the 9
pre-existing `unknown cm:` findings are unrelated and unchanged.

**6d. Still open - unchanged.** Whether `!starting_units`'s roster populates. Never reached;
the button has not been clicked. Nothing in this session touched it, and per §2 the mod's own
callback now runs.

## 7. What was still open (original text below, kept for the record)

**6a. The fix is not applied anywhere on disk.** The containment was in-memory and died with the
game session. Two characters in two lines.

**6b. The shipped Iron Court UI Lua is not in the workspace.** `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua`
is **3021 lines**; the copy inside the live `data/derpy_iron_court.pack` is **4893**. The string
`context:string()` appears **nowhere** in `tools/` and **nowhere** in `Modding Files/pack/`, and
neither `ic_char_panel` nor `STANDING_PANEL` appears in `gen_ic_ui.py`. So the shipped file was
not produced by the generator as it currently stands, and **a re-deploy from staging would revert
1,872 lines of shipped behaviour.** Resolve which copy is authoritative before touching it.
This is the `pack-lua-carves-out-of-binary` memory at its worst - **resolve runtime line numbers
against the pack, never the staging tree.**

**6c. Whether other mods of ours share the idiom.** A grep of `Modding Files/pack/` for
`context:string()` is clean, but that tree is demonstrably stale (6b), so the packs must be
grepped directly.

**6d. Whether `!starting_units`'s roster populates.** Never reached - the button has not been
clicked. `CcoCultureRecord` is keyed by the player's **culture**, so a stock culture should be
fine, but if the list draws empty that is a separate fault.

---

## 8. `!starting_units` reference - do not re-derive

Workshop id 3290280611. Three files, **no DB rows**: `script/campaign/mod/customize_units.lua`
(151 lines), `script/mct/settings/customize_units_mct.lua` (one slider, 0-10000 step 1000,
default 5000), `ui/frontend ui/unit_list.twui.xml`.

- Gated on `cm:is_new_game()`. **Loaded save = the mod does not exist.**
- The button is **one-shot** - a `local aaa` latch destroys it on every panel open after the
  first click.
- It is **not** in the recruitment panel. It is a 55x55 button in the army button row, fourth
  visible, drawn with the template's default `icon_movespeed.png` because the mod never calls
  `SetImagePath`. Measured at `1021,1019` next to `button_recruitment`@844,
  `mercenary_recruitment_button_container`@903, `button_allied_recruitment`@962.
- Clicking it **deletes the lord's entire army** and pays the MCT gold. That is the design.
- The roster is
  `DatabaseRecordContext("CcoCultureRecord", PlayersFaction.CultureContext.Key).GroupedUnitList`
  filtered by `UnitContext.IsOwned` and `IsRenown == false` - **culture-keyed, not faction-keyed**.
- Its HUD path is exactly vanilla; `ui/templates/square_medium_button_toggle.twui.xml` lives in
  **ui3.pack** (checking only `ui.pack` yields a false "the template is gone"); a survey of all
  **71 enabled packs** found no override of the HUD file, the template or its `unit_list.twui.xml`,
  and no Lua path collision. `luac -p` parses it and `check_lua_api.py` reports 0 suspect calls.
  **None of this needs checking again.**
- A runtime child added to `button_group_army` is positioned correctly by the group's layout -
  no `MoveTo` needed and none present.

Unrelated but real in every recent log, and **not** the cause of anything here: `vco.lua` fails to
load, `vco-disable-ca-wincons.lua` throws on `victory_objectives_ie`, and
`wh3_dlc23_campaign_chd_tower_of_zharr.lua` fails to load. `bad_mods_report.txt` does not exist on
this install, so there are no load-time DB rejects to find.
