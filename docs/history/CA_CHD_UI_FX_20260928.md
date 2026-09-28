# What CA uses for Chaos Dwarf UI effects, and how to drive them on a runtime-created panel

Research date 2026-09-28, game data as installed (9.0). Read-only; nothing in the workspace was edited.

Source of every twui fact below: the 952 `.xml` files under `ui/` in
`F:\SteamLibrary\steamapps\common\Total War WARHAMMER III\data\ui3.pack` (the only ui pack that
holds layouts; they are stored UNCOMPRESSED, compression flag 0), extracted by
`scratchpad/ui_fx/extract.py` into `scratchpad/ui_fx/twui/ui3.pack/ui/...`. Art existence was
checked against the index of `ui.pack` / `ui2.pack` (`scratchpad/ui_fx/ui_index.tsv`); art in
those packs is `u32 length + zstd` (the `read_vanilla_loc._decompress` wrapper).
`scratchpad/ui_fx/survey.txt` is the full per-file dump (animations, frames, SpriteAnimation /
particle / VFX callbacks, glow images, shaders) for every CHD-related layout.

Legend: **PROVEN** = read in CA's shipped files/docs or already observed in game in this workspace.
**INFERRED** = strongly suggested by CA's files but not observed. **UNKNOWN** = no evidence either way.

---

## 1. Which CA Chaos Dwarf panels carry effects

| Panel (ui3.pack) | Effects found |
|---|---|
| `ui/templates/tower_of_zharr_seat.twui.xml` (one seat) | `seat` states layer a hexagonal **edge light** over the slot: `active` = `seat_active_highlight.png`, `hover` = `seat_hover_highlight.png`, `selected` = `seat_selected_highlight.png`; hidden `sprite_claim_effect` (SpriteAnimation starburst) fired when the Claim button is clicked; `flash_update` animations on the influence/turn counters |
| `ui/campaign ui/tower_of_zharr.twui.xml` | same seat block inlined twice; `template_tower_district` state machine with a `complete` state that adds the rectangular rim glow `district_complete_glow_02.png` (9-slice) plus lava; `sprite_lava_start_left/right` SpriteAnimation (lava drip); four `torch_0N` + two `distrct_torch_0N` = `heat_glow.png` under `glow_pulse_t0` + a `VfxRendererCallback` (`wh3_dlc23_2d_ui_torchsmoke`); `glow_01..04` furnace glows under `glow_pulse_t0`; `particle_smoke` ParticleEmitter + `template_particle`; chimney smoke VFX |
| `ui/campaign ui/hellforge_panel_category_tab.twui.xml` | the richest: 10 `VfxRendererCallback` components (furnace fire, purple cooldown fire, white daemon burst, small fires, torch fire, embers, sparks); `template_category_block` states each with `heat_glow` + `furnace_light_inside_bull` under `glow_pulse_t0`; **`OnEnterState_<state>` animations**; skull-torch rune lights under `glow_pulse_t0`; `sprite_cooldown_effect_*` SpriteAnimation (looping skull cooldown) |
| `ui/campaign ui/hellforge_panel_unit_caps_tab.twui.xml` | hidden `sprite_progression_celebration` (SpriteAnimation `hellforge/starburst_unlock_effect/effect_burst_full_`, 0..22) made visible when a cap becomes affordable; `flash_update` on costs |
| `ui/campaign ui/hellforge_panel_main.twui.xml` / `_unit_tab` | `button_flame` (magic_flame material, show/hide/OnCreate), `flash_update` on treasury/dread, `alert_icon` `glow_pulse_t0` |
| `ui/campaign ui/labour_economy.twui.xml` | `icon_public_order` state `unhappy` = `glow_pulse_t0` vars `1,2,1,0`; show/hide/escape panel anims |
| `ui/campaign ui/military_convoys.twui.xml` (convoys) | `template_master_card` `selected*` states add `fe_flat_button_selected_glow.png` (428x138 over a 400x110 card, margin 24); cargo arrows `glow_pulse_t0` on hover; many `flash_update`; 52 `magic_flame` button flames |
| `ui/campaign ui/chd_narrative_panel.twui.xml` (Drill relics) | `panel_rune_vfx` / `drill_vfx_top_smoke` under `glow_pulse_t0`; `smoke` under `smoke_overlay_t0` with `chd_narrative_panel_rune_smoke_mask.png`; `relic_icons_map_selected_state_glow.png` |
| `ui/campaign ui/rituals_panel.twui.xml` (rites) | `smoke_particle_emitter` + `template_particle` (`particle_star.png`, `particle_move`); show/hide; list fade_in/fade_out |
| `ui/campaign ui/chd_end_game_teleport.twui.xml` | show/hide/escape panel slides; `selected_overlay` `OnCreate` looping anim |

`dlc25_don_armoury.twui.xml` is the Dwarf armoury, not Chaos Dwarf. There is no CHD-specific
"armoury" panel beyond the convoys.

---

## 2. The effect mechanisms CA uses, with exact names and paths

There are **six** distinct mechanisms. Only the first two are needed for "edges light up".

### 2a. A state (or image layer) that adds an edge-light image - CA's actual seat/district look

This is how CA lights a Tower of Zharr seat and a completed district. **No animation at all**:
the light is an extra image in the lit state.

- Seat (hexagon, 135x161 art, drawn at offset -19,-32 over a 96x96 component, every state):
  - `ui/skins/default/dlc23_tower_of_zharr/seat_slot.png` (base, all states)
  - `ui/skins/default/dlc23_tower_of_zharr/seat_active_highlight.png` (state `active`; dark red thin hex rim)
  - `ui/skins/default/dlc23_tower_of_zharr/seat_hover_highlight.png` (state `hover`)
  - `ui/skins/default/dlc23_tower_of_zharr/seat_selected_highlight.png` (state `selected`; bright orange double hex rim - the "lit" look)
  - `ui/skins/default/dlc23_tower_of_zharr/seat_flag_holder.png` (top layer)
  - state `hover` -> `active` transition 200 ms (`transition_m_transition_time="200"`)
  - Also per-house variants `seat_slot_{active,hover,selected,locked}_{astragoth,azgorth,conclave,zharr}.png`
    set by `ContextImageSetter` "`dlc23_tower_of_zharr/seat_slot_%s.png`".
- District rim (the rectangular one, fits cards):
  `ui/skins/default/dlc23_tower_of_zharr/district_complete_glow_02.png` - **299x877**, opaque
  alpha to the edge, drawn by CA at 299x367 with `tile="true" margin="90,90,90,90"`, only in
  states `complete` / `complete_animation` of `template_tower_district`, chosen by
  `ContextStateSetterConditional` (`complete`: `IsDistrictComplete && sprite_animation_holder
  not visible`; `complete_animation`: while it is visible; `fallback_state` `active`).
- Convoys equivalent: `ui/skins/default/fe_flat_button_selected_glow.png` (64x64, margin 24,
  drawn 14 px larger than the card on every side) in the `selected*` states.
- Hell-Forge "hot" glow: `ui/skins/default/dlc23_chd_hell_forge/heat_glow.png` (500x500 radial
  red, alpha box 41..469) and `heat_glow_cooldown.png` (purple); `furnace_light_inside_bull.png`,
  `furnace_light_gate_glints.png` (403x520), `lava_tunnel_glow.png` (54x123),
  `cap_unlock_bar_fill_glow.png` (20x280).

Contact sheet: `scratchpad/ui_fx/contact.png` (seat_slot, seat_active_highlight,
seat_selected_highlight, district_complete_glow_02, heat_glow, starburst frame 8). Extracted
PNGs in `scratchpad/ui_fx/art/`.

### 2b. `glow_pulse_t0` - CA's continuous pulse (a shader, not an animation)

The single most-used CHD effect: **876** uses across 165 layouts; in CHD panels on every torch,
furnace, rune and glint. It is set **per image** inside a state:

```xml
<image componentimage="..." width="82" height="299" colour="#FFFFFFB4"
       shadertechnique_vars="1.00,1.30,0.80,0.00" shader_name="glow_pulse_t0"/>
```

or per state (`<unhappy ... shader_name="glow_pulse_t0" shadervars="1.00,2.00,1.00,0.00">`,
labour_economy `icon_public_order`). It pulses on its own every frame the image is visible - no
trigger.

CA's own definition (`Modding Files/reference/ca_script_docs_wh3/campaign/uicomponent.html`,
"Shader Techniques" table) - PROVEN:
`glow_pulse_t0` "Glowing Pulse - Pulsing saturation. [1] 0 to unlimited, lowest intensity.
[2] 0 to unlimited, highest intensity. [3] Greater than 0 to unlimited, pulse interval.
[4] Time offset, pass in current real time to make it start from 0 intensity and blend in."

CHD values in use (min, max, interval):
- ToZ torches `0.80,1.00,0.50` (heat_glow at colour `#FFFFFF28`)
- ToZ furnace `glow_01` `1.00,1.30,0.80`, `glow_02` `1.00,1.20,1.00` (colour `#FFFFFFB4`)
- Hell-Forge `heat_glow` in `template_category_block` `0.80,1.50,0.80`; bull light `1.00,0.50,0.70`
- Hell-Forge gate glints `2.00,0.50,0.70`; locked door star glints `5.00,0.80,0.80`
- Drill rune `0.50,2.00,5.00`; drill smoke `0.20,1.50,3.00`
- Most common value anywhere: `0.85,0.10,1.35,0.00` (77 uses)

Same table, also relevant: `highlight_edge_t0` "Edge Highlight - Black/White selection edge
highlight effect. Additional Requirements: Single image in state whose dimensions must match that
of the image" (**0 uses in any CA layout**); `magic_aura_t0` "Uses mask image to make a glowing
border" (**0 uses**); `red_pulse_t0` (34 uses); `brighten_t0` (7,263 uses - what the `glow`
animations drive).

### 2c. One-shot sprite burst - CA's actual "seat claimed" effect

`tower_of_zharr_seat.twui.xml`, component `sprite_claim_effect` (hidden, 200x200, sibling of the
seat, `docking="Center" dock_offset="0,51" priority="45"`, blank component_image):

```xml
<callback_with_context callback_id="SpriteAnimation">
  <child_m_user_properties>
    <property name="frame_name" value="UI\sprite_anims\warband_upgrade_starburst\starburst_"/>
    <property name="last_frame" value="19"/>
    <property name="last_frame_delay" value="1"/>
    <property name="loops" value="0"/>
    <property name="paused" value="1"/>
    <property name="time_per_frame" value="60"/>
  </child_m_user_properties>
</callback_with_context>
<userproperties><property name="disable_override0" value="callbacks"/></userproperties>
```

Trigger (on `claim_seat_button`): `ContextCommandLeftClick` with
`(c = self.ParentContext.ChildContext("sprite_claim_effect")) => Do(c.SetVisible(true), c.StartAnimation)`.

Frames: `ui/sprite_anims/warband_upgrade_starburst/starburst_0.png` .. `starburst_19.png`
(20 files in ui.pack, 200x200; frame 0 is empty, frame 8 is an orange fire ring). 20 x 60 ms = 1.2 s.

Hell-Forge twin: `hellforge_panel_unit_caps_tab.twui.xml` `sprite_progression_celebration`
(100x75, hidden) - `frame_name` `UI/sprite_anims/hellforge/starburst_unlock_effect/effect_burst_full_`,
`last_frame 22`, `loops 0`, `time_per_frame 60`, **no `paused`**; triggered only by
`self.ChildContext("sprite_progression_celebration").SetVisible(true)`. Frames are 1296x971
(26 files). Other CHD sprites: `ui/sprite_anims/tower_of_zharr/district lava effect/lava_drip_start_0..31`,
`ui/sprite_anims/hellforge/skull_cooldown/skull_cooldown_0..14` (loops -1).

SpriteAnimation doc (`ui_callback_documentation.html`) - PROVEN: path without index and `.png`;
`show_final_frame_when_finished` ("instead of becoming invisible"), `reverse`, `pre_cache`,
`randomise_start_frame`, `ping_pong`; functions `IsPlaying`, `StartAnimation` ("Used to call
StartAnimation through the context system").

### 2d. twui `<animations>` - flash / glow / OnEnterState / OnCreate

Format (PROVEN): inside a component, after `<states>`:
`<animations><flash_update id="flash_update" propagate="true"><frames><frame .../></frames></flash_update></animations>`
- the element tag is the id (lower-cased for `OnEnterState_*`, e.g. `<onenterstate_selected id="OnEnterState_selected">`).
Frame attributes seen: `interpolationtime` (per-frame DURATION, ms - memory
`wh3-twui-particle-colour-is-rgba`), `interpolationpropertymask`, `targetmetrics_m_colour`
(`#RRGGBBAA`), `targetmetrics_m_width/height`, `targetmetrics_m_offset`,
`targetmetrics_m_shadervars`, `targetmetrics_m_rotation_angle`, `targetmetrics_m_imageindexN`,
`targetmetrics_m_font_scale`, `material_param_id`, `easing_curve_type` ("Quadratic In & Out",
"Circular Out"...), `is_movement_absolute`, and on a frame even `soundcategory`
(`dlc27_hef_asur_domination` `shine_glow`). Animation attrs: `propagate`, `totalloops="-1"` (loop).
Mask bits are not documented anywhere found; by co-occurrence (INFERRED) 1 = size, 2 = offset,
8 = shader vars, 16 = rotation, 64 = colour, 512 = font_scale, 1024 = material param.

CHD animation names and shapes (exact):
- `flash_update` (392 uses, 78 files; ToZ seat counters, Hell-Forge costs, convoys):
  f0 `0ms` size 64x37; f1 `200ms` colour `#FFFF00FF`, offset `0,-4`; f2 `200ms` colour
  `#FFF8D7FF`, offset `0,4`. Nothing in any layout or script triggers it by name - INFERRED
  to be fired by the engine when a text label's value changes.
- `OnEnterState_active / _selected / _cooldown / _cooldown_selected` (Hell-Forge
  `template_category_block`, `vfx_large_flames_active`, `vfx_large_flames_cooldown`): e.g.
  `vfx_large_flames_active.OnEnterState_active` = one frame, `500ms`, mask 2, offset `3,80`,
  `Quadratic In & Out`, absolute. **Zero** references to any `OnEnterState_*` name in any layout
  expression or any of CA's 7,540 scripts -> INFERRED: the engine plays `OnEnterState_<state>`
  automatically on `SetState(<state>)`. Same for `OnCreate` (925 uses, 0 triggers).
- `button_flame` `show` (2 frames, 300ms, `material_param_id="heat_percent"`, shadervars 0.7),
  `hide`, `OnCreate`.
- Generic `glow` (158 uses; 108 identical copies): mask 8; f0 0ms; f1 200ms shadervars `10,0,0,0`;
  f2 500ms back - i.e. a brighten flash on a `brighten_t0` state. `ritual_chain.twui.xml`
  `template_ritual` uses the same shape at 350/350ms, shadervars 5.

### 2e. `VfxRendererCallback` - real 2D particle VFX (almost all of it is DLC23)

All eleven VFX any CA layout renders; nine are Chaos Dwarf, authored for DLC23:

| vfx | used by |
|---|---|
| `wh3_dlc23_2d_ui_furnace_fire` | Hell-Forge `vfx_large_flames_active` (380x332) |
| `wh3_dlc23_2d_ui_furnace_fire_purple` | Hell-Forge `vfx_large_flames_cooldown` |
| `wh3_dlc23_2d_ui_furnace_fire_daemon_burst_white` | Hell-Forge `vfx_large_flames_burst` (hidden; shown by a click's `SetVisible(true)`) |
| `wh3_dlc23_2d_ui_small_fire` | Hell-Forge `vfx_flame_left/right` (56x110); dlc29 vampire lair popup |
| `wh3_dlc23_2d_ui_torchfire_white` | Hell-Forge cooldown flames |
| `wh3_dlc23_2d_ui_torchembers` | Hell-Forge `vfx_embers_left/right`; dlc29 lair popup |
| `wh3_dlc23_2d_ui_sparks` | Hell-Forge `vfx_sparks` (`vfx_rot_z -45`, `vfx_spawn_rate_scale 0`, `vfx_spawn_speed 10`; `SetVfxSpawnRateScaleFactor` driven by a cog's movement) |
| `wh3_dlc23_2d_ui_torchsmoke` | ToZ `vfx_torch_fire` x6, `vfx_chimney_smoke` |
| `wh3_dlc23_2d_ui_large_fire` | dev layout only |

Files: `vfx/wh3_dlc23_2d_ui_*.xml` in `data/vfx_desc.pack`. Setup: a component with a blank
image, `<callback_with_context callback_id="VfxRendererCallback">` + user property `vfx`, and
`userproperties instance_id`. CCO functions on such a component (cco/documentation.html):
`PlayVfx`, `StopVfx`, `SetVfxSpawnRateScaleFactor`, `SetVfxScale`, `SetVfxColourTint`,
`SetVfxColourAlpha`, `SetVfxOrientation`, `SetVfxPosition`, `SetVfxVelocity`, `SetVfxSpawnSpeed`.

**The trap** (doc, PROVEN): "The vfx must be pre-registered in a `.warscape_req.xml` file that gets
exported automatically when exporting a layout that has a VfxRendererCallback ... up to 16 unique
entries". CA ships one beside each layout, e.g. `ui/campaign ui/tower_of_zharr.warscape_req.xml`:

```xml
<?xml version="1.0"?>
<warscape_requirements version="1">
	<vfx name="wh3_dlc23_2d_ui_torchsmoke"/>
</warscape_requirements>
```

### 2f. ParticleEmitter + `template_particle` (the rites panel), and the magic_flame material

Already in use by the Iron Court (`derpy_ic_fire.twui.xml`, embers on a held office card) and
the commission mod. `magic_flame` = `material_name="ui/effects/materials/magic_flame.xml.material"`
on a state (1,155 uses; CA's button hover flame, `button_flame` child, texture slots such as
`t_xml_general_mask = ui\effects\textures\magic_flame_mask_text_button.dds`).

---

## 3. How CA triggers them, and what our Lua can call

### CA's own triggers (grep of `Modding Files/reference/ca_scripts_wh3/`)
- `TriggerAnimation`: 11 files, 38 lines - all tutorials/libs (`tut_show`, `show`, `shrink`,
  `destroy`, `hide`) plus `wh2_dlc12_ikit_workshop.lua:689` `cores_icon:TriggerAnimation("play")`.
  **Zero** Chaos Dwarf script calls it. CA's CHD panels trigger everything from the layout (CCO).
- `StartPulseHighlight` / `StopPulseHighlight`: only through `pulse_uicomponent` (`lib_common.lua:662`), help-page links.
- `:Highlight(` 51 lines / `highlight_component` 134 lines - tutorial "flashing ring". Only CHD
  use: `wh3_dlc23_narrative_chaos_dwarfs.lua:501` `highlight_component(true, false, "button_chd_narrative_panel")`, off at 251.
- `ShaderTechniqueSet`: `lib_campaign_ui.lua:2324` (restore), `wh2_intro_ui_highlighting.lua:154`,
  `wh2_dlc17_bloodgrounds.lua:741` `devastation_counter:ShaderTechniqueSet("red_pulse_t0", true, true)`
  **on a component the script just made with `CopyComponent`** (a debug UI).
  `lib_generated_battle.lua:1359` `TextShaderTechniqueSet("glow_pulse_t0")` + `TextShaderVarsSet(0, 3, 1.5, 0)`.
- `StartAnimation` (sprite): 0 script hits; 58 layout CCO hits (`c.StartAnimation`).
- **Runtime-created + TriggerAnimation is CA practice** (PROVEN in CA code):
  `lib_topic_leader.lua:272` `core:get_or_create_component(..., "UI/Common UI/scripted_topic_leader.twui.xml")`,
  then `SetAnimationFrameProperty("show", ...)` and `TriggerAnimation("show")` (346), `"shrink"` (429/437);
  `lib_battle_script_unit.lua:1871` `CreateComponent(..., "ui/battle ui/unit_ping_indicator.twui.xml")`
  then `TriggerAnimation("destroy")` (1897).

### Signatures (`py tools/check_lua_api.py --explain`, campaign/uicomponent.html)
- `uic:TriggerAnimation(string name)` -> nil. "Starts an animation on the uicomponent by name."
- `uic:AnimationExists(name)` -> boolean; `uic:GetAnimationNames()`; `uic:CurrentAnimationId()` -> "" when none.
- `uic:SetAnimationFrameProperty(anim, frame0based, type, v1, [v2..v4])`; types "colour",
  "position", "scale", "shader_values", "rotation", "image", "opacity", "text",
  "interpolation_time", "font_scale", "material_params".
- `uic:ShaderTechniqueSet(shader, [all_states=false], [include_text=true])`;
  `uic:ShaderVarsSet([a],[b],[c],[d],[all_states=false],[include_text=true])`;
  `ShaderTechniqueGet`, `ShaderVarsGet`.
- `uic:StartPulseHighlight([strength], [state])` "unobtrusively highlighting ... buttons and
  panels"; `StopPulseHighlight([state])`.
- `uic:Highlight(bool, [square=false], [priority_lock=0])` "flashing ring".
- `uic:SetState(name)` -> boolean; `SetVisible(bool)`; `SetImagePath(path, [index])`;
  `SetCurrentStateImageOpacity(index, 0..255)`; `SetOpacity(0..255, [all_states])`.
- `common.call_context_command([object_id="CcoScriptObject"], function_id)` - the Lua route to a
  CCO call; no CA script uses it on a `CcoComponent`, so calling `StartAnimation`/`PlayVfx` on
  one of our components from Lua this way is UNKNOWN.
- Lua UIComponent has **no** `StartAnimation`, `PlayVfx` or `SetVfx*` member (not in the 141
  documented members); those are CCO-only.

### Our own runtime-created components - what is already known in this workspace
- PROVEN in game: an animation defined in OUR shipped twui runs on a component we create at
  runtime - the commission mod's `derpy_chd_rite_fire.twui.xml` `particle_move` drew (reported
  "its sparkles not embers"), `docs/sessions/HANDOFF_20260828_PANEL_CLOCK_AND_DROP_LEAK.md` s.3.
  That is engine-played (ParticleEmitter), not Lua-triggered.
- PROVEN in game: image layers swapped by `SetImagePath` on our runtime card draw (the Guilds'
  streak bug proved the layer draws; `HANDOFF_20260925_GUILDS_QOL.md` s.8-9) - the Guilds already
  light a running service's card with `heat_glow.png` + `district_complete_glow_02.png` (margin 40).
- NOT MEASURED: `TriggerAnimation` from Lua on our component (Guilds `derpy_gg_scale` font_scale,
  `HANDOFF_20260924_GUILDS_UI_SCALE.md` s.4 check 3 still owed; no `text measures` line in any
  script log on disk). `ShaderTechniqueSet` on our components (`EX.set_off`) - "still unconfirmed"
  (`HANDOFF_20260926_EXCHANGE_TEXT_PASS.md`).
- The Iron Court Lua contains no `TriggerAnimation`, pulse or shader call today
  (`HANDOFF_20260916_IRON_COURT_SIX_LIVE_BUGS.md` s.2 grep; re-checked).
- Verdict: TriggerAnimation on an animation in our own twui on our runtime component is
  **INFERRED to work** (CA does exactly this with its own layouts; our layout animations are
  demonstrably parsed), **not yet observed**.

---

## 4. UI sounds

- No CA Chaos Dwarf script plays a UI sound (grep of CHD/dlc23 campaign scripts for `sound`: 0).
  CHD panels get sound from the layout: `soundcategory` on the panel root -
  `UI_CAM_HUD_DLC23_CHD_Tower_Of_Zharr_Panel`, `..._Hell_Forge_Panel`, `..._Labour_Economy`,
  `..._Military_Convoys_Panel`, `..._Relics_Panel`, `UI_CAM_HUD_DLC23_Panel_End_Game_Portal`;
  buttons use generic `UI_GBL_TMP_*` categories (ToZ seat `UI_GBL_TMP_MODULAR_Medium_Button`).
- The Wwise event names present in `data/audio_base_bnk.pack` are the category plus a suffix:
  `UI_CAM_HUD_DLC23_CHD_Tower_Of_Zharr_Panel_Open` / `_Close`, `..._Hell_Forge_Panel_Open/_Close`,
  `..._Labour_Economy_Open/_Close`, `..._Military_Convoys_Panel_Open/_Close`,
  `..._Relics_Panel_Open/_Close`, `UI_CAM_HUD_DLC23_CHD_End_Game_Portal_Panel_Open/_Closed/_Traverse`.
  Generic candidates for "seat taken": `UI_CLICK_Begin_Ritual`, `UI_CAM_EMP_CollegeOfMagic_Unlocks`,
  `UI_GBL_HUD_Purchase`, `UI_CAM_HUD_WoC_DLC20_Chaos_Gifts_Khorne_Flame_Oneshot`. Full list of
  1,642 `UI_*` names: `scratchpad/ui_fx/ui_sound_events.txt`.
- Script calls (PROVEN signatures): `cm:trigger_2d_ui_sound(event, delay_ms)`,
  `common.trigger_soundevent(event)` (CA uses both, e.g. `wh3_realm_slaanesh.lua:360`).
  Whether these event names play from them is INFERRED (names exist; CA uses the same naming
  in `trigger_2d_ui_sound("UI_CAM_PRO_Story_Stinger", 0)`), not tested. A layout can also set
  `soundcategory` on a component or on an animation frame, or use `ContextSoundTrigger`.

---

## 5. Existing workspace notes

- Memory `wh3-twui-particle-colour-is-rgba`, `wh3-particle-child-must-be-template-particle`,
  `wh3-nine-slice-margin-past-texture-reads-atlas`, `wh3-ui-root-is-window-over-ui-scale`
  (font_scale via TriggerAnimation, unmeasured).
- `docs/sessions/HANDOFF_20260925_GUILDS_QOL.md` s.8 (card glow by image index), s.9 (atlas streaks).
- `docs/sessions/HANDOFF_20260925_IRON_COURT_MCT_MULTIPLAYER.md` s.17 (IC embers,
  `ICUI.card_fire`, `derpy_ic_fire.twui.xml`, not previewable).
- `docs/sessions/HANDOFF_20260828_PANEL_CLOCK_AND_DROP_LEAK.md` "Do not re-derive" + s.3.
- `docs/CUSTOM_UI.md` has no section on animations, pulses, shaders or VFX.

---

## 6. Recommendation for "a seat is taken -> its edges light up"

**Layer 1 - the lit rim (CA's ToZ district look, zero Lua beyond a state/image change).**
Give the office card a lit state (or an extra image layer, the Guilds route) that adds
`ui/skins/default/dlc23_tower_of_zharr/district_complete_glow_02.png` as a 9-slice rim
(`tile="true"`, margin <= 90 and < half the card; texture is 299x877 so 90 is safe), and put
`shader_name="glow_pulse_t0" shadertechnique_vars="0.80,1.20,0.80,0.00"` on that image so it
breathes like CA's furnaces. Light it with `uic:SetState("lit")` (CA pattern) or
`SetImagePath(path, index)` from the "off" 128px clear image (Guilds pattern, already proven).
Optionally `heat_glow.png` behind it at colour `#FFFFFF28`-`#FFFFFF64` like the ToZ torches.
If the card is hexagonal, the seat art itself (`seat_selected_highlight.png` over `seat_slot.png`)
is the exact CA look but it is a fixed 135x161 hexagon.

**Layer 2 - the moment of taking (CA's ToZ claim burst).** A hidden 200x200 child with CA's
`sprite_claim_effect` SpriteAnimation block (starburst 0..19, 60 ms, loops 0). Omit `paused`
(the Hell-Forge celebration pattern) so Lua `SetVisible(true)` alone plays it; to replay,
recreate the child or toggle visibility (restart-on-reshow is UNKNOWN). Optionally a one-shot
twui animation (`glow`/`flash_update` shape) fired with `TriggerAnimation` after an
`AnimationExists` guard, and `common.trigger_soundevent("UI_CLICK_Begin_Ritual")`-class sound.
Name the lit state's animation `OnEnterState_lit` if an entry flourish is wanted - INFERRED
automatic.

**Not recommended for the first pass:** `VfxRendererCallback` (the true CHD fire) - it needs a
hand-written `<our layout>.warscape_req.xml` beside our runtime layout, and nothing shows a mod
or a runtime-created component using one; `highlight_edge_t0` / `magic_aura_t0` (CA never uses
them); `Highlight()` (tutorial ring, not CHD-styled); `StartPulseHighlight` (generic brighten).

### Risks / silent failures
- 9-slice margin past the TEXTURE reads the atlas (streaks) - check every texture a layer can
  hold (`gen_guilds_ui.check_margins_fit_textures()` is the existing check).
- A wrong `imagepath` or sprite `frame_name` draws nothing / a white square with no error. The
  sprite path is `frame_name + N + ".png"` with N = 0..last_frame inclusive; pack paths are
  lower-case (`district lava effect`), CA's XML writes mixed case with backslashes - write
  lower-case forward-slash in ours (6.1 lowercase rule for our own files).
- `SetState` to a state name the layout lacks returns false and changes nothing.
- `TriggerAnimation` on a missing name: silent (UNKNOWN whether it logs); guard with `AnimationExists`.
- `ShaderTechniqueSet` replaces the state's shader: it can clobber a `set_greyscale_t0` "off"
  look, and CA notes highlight/unhighlight "inadvertently clears active shaders"
  (`lib_campaign_ui.lua` `pulse_and_unpulse_uicomponent`). Prefer shader on the image in the
  twui over setting it from Lua.
- A resized runtime component sizes every layer to its box (IC s.16 note); a glow meant to
  overhang the card (CA draws convoy glow 14 px outside) needs its own larger child.
- `glow_pulse_t0`'s 4th var "time offset" base is undocumented; CA always ships 0.
- ParticleEmitter child must be named `template_particle` or the panel crashes (known).
- None of this can be previewed: TWUI Studio draws no shaders, pulses, sprites or VFX. In-game
  look is owed for every layer.
- UI effects are local-only; keep them behind the local-faction guard the IC UI already uses.
