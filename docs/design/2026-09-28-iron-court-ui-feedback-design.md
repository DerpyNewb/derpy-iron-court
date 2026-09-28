# Iron Court - UI feedback and effects

Date: 2026-09-28. Author request: "add ui effects when seat is taken, (edges light up)...etc
what CA uses for their effects for the Chaos dwarf. what else needs player visual feedback or
ui polishing?" Scope chosen by the author: the seat effect plus all four extras (governor
feedback, attention markers, petition answers, change numbers and the fail look). Design
approved in chat ("go ahead").

Evidence this spec argues from:
- `docs/sessions/CA_CHD_UI_FX_20260928.md` - what CA's Chaos Dwarf panels use, read out of
  `ui3.pack`, with proven / inferred / unknown marked per claim.
- `docs/sessions/IC_FEEDBACK_AUDIT_20260928.md` - every action and state change the panel shows
  and what feedback it gets today, with file:line evidence.

## 1. What exists today

- Filling an office: `ICUI.confirm(card, true)` plays `UI_CAM_POPUP_Message_Event_Positive` and
  runs `pulse_uicomponent` on the office card for 1.5 s (`zzz_derpy_iron_court_ui.lua`,
  `ICUI.confirm`). A held office card also carries the commission's ember emitter
  (`ICUI.card_fire`, `derpy_ic_fire.twui.xml`).
- Everything else answers with a sound at most. `ungov` (release a governor) has no entry in
  `ICUI.ANSWERS`, so it answers with nothing at all.
- The party card already uses the SWAPPED-LAYER trick this spec reuses for the rim: layer
  `PARTY_SEL_INDEX` ships `MASK_NONE` (our own transparent png) and `ICUI.fill_party` writes
  CA's gold frame into it on the chosen card (`gen_ic_ui.py`, `PARTY_LAYERS`).
- The Great Guilds draw CA's district rim through the same trick, proven in game
  (`gen_guilds_ui.py`, `CARD_RIM`, `CARD_RIM_INDEX`).

## 2. The CA effects used

| Effect | CA source | How it is driven |
|---|---|---|
| Edge light (rim) | `ui/skins/default/dlc23_tower_of_zharr/district_complete_glow_02.png`, 299x877, 9-slice | Image layer swapped from `MASK_NONE` by `SetImagePath(path, index)` |
| Breathing | shader `glow_pulse_t0` on the image, `shadertechnique_vars` min,max,interval,offset | Declared in the twui on the layer; runs on its own while visible |
| Claim burst | `ui/sprite_anims/warband_upgrade_starburst/starburst_0..19`, 60 ms/frame, 1.2 s | Hidden child with CA's `SpriteAnimation` callback; `SetVisible(true)` to play |
| Attention glow | `ui/skins/default/dlc23_chd_hell_forge/heat_glow.png`, 500x500 radial red | Hidden child image with `glow_pulse_t0`; `SetVisible` |
| Sound | `UI_CLICK_Begin_Ritual` (seat taken); existing `SOUND_OK` / `SOUND_BAD` otherwise | `common.trigger_soundevent` |

Rejected: `VfxRendererCallback` 2D fire (needs a `.warscape_req.xml`, no evidence it works on a
runtime-created panel); setting shaders from Lua with `ShaderTechniqueSet` (replaces the
component's own technique and can wipe the disabled look).

## 3. Phase 0 - the in-game probe (gates everything else)

Two behaviours are unknown on OUR runtime-created components, and the rest of the design
depends on them:

1. Does a layer carrying `glow_pulse_t0` in our twui actually breathe?
2. Does the `SpriteAnimation` burst replay when hidden and shown again? CA's seat uses
   `paused="1"` plus a `StartAnimation` context command we cannot call from Lua; the
   Hell-Forge twin has no `paused` and plays on `SetVisible(true)`. We take the Hell-Forge
   shape, and after 1.3 s hide it again.

Probe build: the office-card rim (section 4.1) and the burst only. Checked in game with the
panel open: fill a seat, dismiss it, fill it again. Pass = the rim breathes while held, and the
burst plays on BOTH fills. If the burst does not replay, the fallback is to destroy and
re-create the burst child on each claim (`CreateComponent` from its own twui, the way
`ICUI.card_fire` creates the embers). If the shader does not draw, the rim ships static and
breathing is dropped everywhere; nothing else in this spec depends on it.

## 4. Design

### 4.1 Seat effects - Offices cards

- **Rim.** `derpy_ic_card` gains a layer after `CARD_LAYERS`: `MASK_NONE` placeholder, 9-slice
  margin 40 (the Guilds' measured value, which fits both `district_complete_glow_02.png` and
  `MASK_NONE`; `check_margins` must hold it to both), `glow_pulse_t0` with CA's ToZ furnace
  values `1.00,1.30,0.80,0.00`. The Lua writes the rim into it on every draw while the office
  is held and `MASK_NONE` when it is vacant. Cards are recycled, so the write happens on every
  draw, like the party frame.
- **Stalled seat.** A held office that is stalled (sabotage or withhold) shows the rim at
  reduced alpha. One layer holds one image, so the stalled case writes a dimmed copy into the
  same layer: generate
  `ui/derpy_ic/rim_dim.png` from CA's rim at build time (alpha x0.45) into our own folder, the
  way `make_ic_backdrop.py` derives art - it must go through `gen_ic_ui.art_paths()` or the
  generator prunes it. The dimmed copy is our derived file from CA art, so it ships in the pack
  and never goes to GitHub (the sync tool already refuses images).
- **Claim burst.** `derpy_ic_card` gains a hidden child `ic_card_burst` with CA's starburst
  `SpriteAnimation` block (loops 0, 60 ms, last frame 19, no `paused`). The claim answer shows
  it, MoveTo's it over the card centre (runtime components ignore twui offsets), and a
  `cm:callback` hides it again after 1.3 s.
- **Sound.** A seat filled plays `UI_CLICK_Begin_Ritual` instead of `SOUND_OK`.
- **Dismissal.** The rim goes out on the redraw; `SOUND_BAD` as today.

### 4.2 Governors

- `ICUI.ANSWERS.ungov` is added: `SOUND_BAD` on success, `ICUI.reason_text` on a refusal.
- `picked("gov")` sets `filled` to the province key, so the governor row gets the burst.
- The row pool (`derpy_ic_row`) gains the same rim layer and burst child. The rim is written
  only on a Governors-tab row whose province has a governor; every other view writes
  `MASK_NONE`, because the pool is shared by all five list views. A governor who is away
  shows the dimmed rim (he gives nothing while away - the same fact the tooltip states).

### 4.3 Petition answers

`confirmed(yes, demand)` gains a sentence per op instead of clearing `ICUI.notice`:

| Op | Notice on success |
|---|---|
| grant | "Granted. %s is pleased (+%d loyalty)." |
| accept | "Accepted. %s keeps its word." |
| arbit | "Settled. %s and %s stand down." / "You backed %s against %s." |
| favour | "Sent. %s is pleased (+%d loyalty)." |

Party names come from `ICUI.house_name`; amounts come from the same tuning values the model
applies, never retyped. The benefiting party's card gets a 1.5 s rim flash (rim written, then
`MASK_NONE` after the callback) when it is on screen. No `IC.feed` cards: the event feed stays
for things the player did not click.

### 4.4 Attention markers

- One hidden child `ic_tab_mark` per tab button, `heat_glow.png` at 28x28 with
  `glow_pulse_t0`, MoveTo'd to the tab's right end on each draw.
- Conditions, computed in one function `ICUI.attention(faction)` that `ICUI.opener_tip` is
  refactored to share so the two can never disagree:
  - Petitions: an open demand, an offer not yet answered, or a live feud.
  - Offices: an empty seat, or a term ending next turn.
  - Governors: a province with no governor. NOT a governor away: a lord in the field is away
    most turns, and a marker that is nearly always lit tells the player nothing.
  - Court: any party with a secession countdown running.
- The HUD opener gains a hidden `ic_opener_glow` child (same art, sized to the button) shown
  while any tab is marked. Markers are redrawn on panel refresh and on `FactionTurnStart` for
  the local human, never from a listener that runs for other factions.

### 4.5 Change numbers

- At the local human's `FactionTurnStart`, snapshot each party's loyalty and share into
  `ICUI.baseline` (UI memory only, not saved: after a load no changes show until the next
  turn, which is honest).
- `ICUI.fill_party` appends the change since the baseline to the loyalty and share cells,
  " +5" in green and " -10" in red, through `[[col:...]]` markup. The colour keys are read out
  of `db/ui_colours_tables` at build time, the way `preview_iron_court.py` resolves `red`; no
  change, no suffix.
- Every cell that grows a suffix must still fit: `gen_ic_ui.py` check 20c measures the longest
  string a cell can draw and must include the suffix.

### 4.6 The fail look

A plot that resolves `failed` flashes the target party card's rim with a red-tinted copy
(`ui/derpy_ic/rim_red.png`, generated as in 4.1) for 1.5 s and keeps the existing red-text
notice and `SOUND_BAD`. A plot that lands keeps the success burst on the target's card.

## 5. Multiplayer

All effects are drawn inside `ICUI.ANSWERS` handlers or on refresh, which already run only
for this machine's player. Nothing here changes model state, so nothing needs the MP wire.
`ICUI.baseline` is per machine and never read by the model.

## 6. Testing

- **Harness** (`tools/_iron_court_harness.lua`), each check written first and watched fail:
  the rim path written into the card's layer when held, `MASK_NONE` when vacant, the dimmed
  copy when stalled; `ungov` answers; `filled` set for `gov`; each petition sentence; the
  attention conditions per tab and that the opener tooltip and markers agree; the change
  suffix and its absence; the failed plot's red flash.
- **Mutants** in `tools/mutate_iron_court.py` for each of the above.
- **Generator** (`gen_ic_ui.py --check`): every new art path exists in CA's packs or in
  `art_paths()`; 9-slice margins fit every texture the layer can hold (placeholder, rim, dim,
  red); new GUIDs pair; the suffix fits (20c).
- **Preview** draws the rim on held cards.
- **In game**, which nothing above replaces: the Phase 0 probe, then one pass over every
  effect in the panel. Shaders, sprites and particles are invisible to the preview.

## 7. Out of scope

The event feed; any change to what the model does; the Great Guilds panel; real 2D fire VFX.
