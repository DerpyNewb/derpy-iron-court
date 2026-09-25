# The Iron Court: MCT settings and multiplayer - design

Approved in conversation 2026-09-25. Author: "add mct and multiplayer support first then", then,
on the design, "go ahead". Two answers settled the open choices:

- **MCT scope:** a difficulty preset, on/off switches, and a Custom preset exposing about a
  dozen key numbers as sliders.
- **MCT in multiplayer:** ignored. Every machine uses the shipped defaults, as The Great Guilds
  and the Zharr Exchange already do.

**Amended 2026-09-25, while planning.** Three corrections, each measured in the code:

- **The freeze happens at first tick, not at the first turn start (section 3.4).** A new
  campaign rolls the player's court at first tick (`IC.seed`), and a new game fires no
  `FactionTurnStart` until turn 1 ends: the Guilds' 2026-09-23 new-game logs have none. So a
  freeze at the first turn start rolled every player's court on the defaults and played
  turn 1 on them. The reason the first draft avoided first tick does not hold: MCT reads the
  player's settings in its own `LoadingGame` callback, which runs before any first tick
  (`groovy_mct.pack`, `script/groovy/modules/mct/systems/registry/main.lua`, `Registry:load`).
- **The answer hook carries the op's argument** (section 2.3):
  `IC.after_op(faction_key, op, arg, done, why, spare)`. The dismissal's confirmation needs the
  office's card and the appointment's needs the seat it filled. In multiplayer the picker
  that sent the op may have closed by the time the answer arrives.
- **Labels follow the player-text rules** (sections 3.2 and 3.3): no "AI", and "office" rather
  than "seat".

Pack: `derpy_iron_court.pack`. Scripts: `zzz_derpy_iron_court.lua` (model, `IC`),
`zzz_derpy_iron_court_parties.lua` (rival parties, extends `IC`), `zzz_derpy_iron_court_ui.lua`
(panel, `ICUI`). New: `script/mct/settings/derpy_iron_court.lua`.

## 1. What is wrong today

Measured in the code on 2026-09-25:

1. **Eleven panel actions change the campaign straight off a click**, on the clicking machine
   only. In multiplayer each is a desync. Call sites in `zzz_derpy_iron_court_ui.lua`:
   `IC.appoint`, `IC.dismiss`, `IC.assign_governor`, `IC.release_governor`, `IC.plot`,
   `IC.favour`, `IC.hire`, `IC.grant_demand`, `IC.refuse_demand`, `IC.accept_offer`,
   `IC.decline_offer`.
2. **`ICUI.player()` is `cm:get_human_factions()[1]`.** In a two-player campaign the second
   player's panel shows, and acts on, the first player's court.
3. **The event-card hold is per machine.** `ICUI.open` calls `IC.hold_feed(true)` and close
   releases it; `IC.turn` skips `IC.flush_feed()` while held. One machine holding and the
   other not is a divergence in model-side event calls.
4. **No MCT page.** Every number is a constant in `IC.TUNE`.

Already safe: the panel makes no `cm:random_number` call and no local-faction read; `IC.turn`
runs for every Chaos Dwarf faction on `FactionTurnStart` on every machine; the first-tick
callback loads every human faction's court on every machine.

## 2. Multiplayer

### 2.1 The transport

One entry point, copied in shape from `GG.mp_send` (The Great Guilds) but self-contained, so
the Iron Court depends on no other mod:

```lua
IC.MP_TAG = "ic1"
IC.MP_OPS = {}                      -- op name -> function(faction_key, arg)
function IC.is_mp() ... end         -- pcall(cm:is_multiplayer); an error reads as single player
function IC.faction_by_cqi(cqi) ... end   -- walks cm:get_human_factions(), <= 8 compares
function IC.mp_send(faction_key, op, arg) ... end
function IC.mp_receive(id, cqi) ... end   -- returns the faction it acted for, or nil
```

- **Single player:** `IC.mp_send` calls `IC.MP_OPS[op](faction_key, arg)` directly. Every op
  therefore runs in ordinary play and only the round trip is multiplayer-only.
- **Multiplayer:** it resolves the faction's `command_queue_index()` and calls
  `CampaignUI.TriggerCampaignScriptEvent(cqi, "ic1|" .. op .. "|" .. arg)`. A listener
  `ic_mp` on `UITrigger` (condition `true`, work in a `pcall`'d handler) passes
  `context:trigger()` and `context:faction_cqi()` to `IC.mp_receive`, which runs the op on
  every machine.
- **Refuse, never fall back.** No cqi, an unknown op, or a string over 100 characters (the only
  committed limit, MCT's `MultiplayerCommunicator`) is logged and dropped. Applying locally
  instead would change one machine only.
- **Not another mod's trigger.** `IC.mp_receive` ignores any id not starting `ic1|`.

### 2.2 The eleven ops

Wire argument (`|`-separated) and the model call each makes. None reloads the court first: the
first tick loads every human court on every machine, and `IC.load` replaces the court from the
save, which would discard anything not yet saved.

| Op | Arg | Calls |
|---|---|---|
| `appoint` | `office\|cqi` | `IC.appoint` |
| `dismiss` | `office` | `IC.dismiss` |
| `gov` | `province\|cqi` | `IC.assign_governor` |
| `ungov` | `province` | `IC.release_governor` |
| `plot` | `plot\|actor_cqi\|target` | `IC.plot` |
| `favour` | `key\|slug` | `IC.favour` |
| `hire` | `office\|index` | `IC.hire` |
| `grant` | (empty) | `IC.grant_demand` |
| `refuse` | (empty) | `IC.refuse_demand` |
| `accept` | `slug` | `IC.accept_offer` |
| `decline` | `slug` | `IC.decline_offer` |

Numbers travel as decimal strings and are `tonumber`'d back where the model expects a number
(cqi, hire index; a plot target keeps the type `IC.plot` is given today). The longest real
message is a plot aimed at a province, about 70 characters.

### 2.3 The panel's side

- Each of the eleven call sites becomes an `IC.mp_send`. What the site does with the result
  today (the refusal notice, closing the picker, the refresh) moves into a hook: each op ends
  with `if IC.after_op then IC.after_op(faction_key, op, arg, done, why, spare) end`, and the
  panel script sets `IC.after_op` (the model never names `ICUI`). In multiplayer the panel's
  hook acts only when `faction_key` is this machine's player, so the other machine applies the
  change and draws nothing, and it refreshes the panel itself. In single player it always
  acts, inside the click, and the click's own refresh follows.
- **The red buttons stay as they are.** The pre-checks (`IC.can_appoint`, `IC.can_favour`,
  `ICUI.act_check` ...) only read.
- **UI-only state stays local:** the chosen party (`ICUI.sel`), tab, page, picker, sort.
- **`ICUI.player()`** becomes `cm:get_local_faction_name(true)` (the forced form: the unforced
  one throws in multiplayer and kills every first-tick callback behind it), with the first
  human faction as the fallback when that read fails.
- **`IC.hold_feed` does nothing in multiplayer**: cards show when raised.

### 2.4 Status

It will be tested with a fake transport in the harness and in single player in game. No
two-machine campaign is available, so the README and DEVELOPMENT guide say "not yet tried in a
two-player campaign", as the Guilds' do.

## 3. MCT

### 3.1 The page

`script/mct/settings/derpy_iron_court.lua`, in the Guilds file's shape: `register_mod`,
title "The Iron Court", plain-text labels and tooltips (no loc keys), four sections
(Difficulty, Systems, Custom numbers, Debug), and every option `set_locked` with a reason while
in a campaign (`__game_mode == __lib_type_campaign`), because MCT's own campaign gating is dead
code. The description says the values are read once, at the first turn of a campaign, fixed for
that save, and **not used in multiplayer**.

### 3.2 Difficulty preset

A dropdown `preset`: `gentle`, `default` (the default), `harsh`, `ruthless`, `custom`. Resolved
when the game reads it: under any preset but Custom, the preset table supplies the numbers and
the sliders are not read. The switches are read on every preset.

| Key | Slider label | Gentle | Default | Harsh | Ruthless | Slider range |
|---|---|---|---|---|---|---|
| `loyalty_start` | Starting loyalty | 65 | 55 | 50 | 45 | 30 to 80 |
| `loyalty_drift_none` | Loyalty change each turn for a party with no office | 0 | -1 | -2 | -3 | -5 to 0 |
| `secede_loyalty` | Loyalty at which a party threatens to leave | 15 | 20 | 25 | 30 | 0 to 40 |
| `secede_share` | Share of the court a party needs to leave | 30 | 25 | 20 | 15 | 5 to 50 |
| `secede_turns` | Turns of warning before a party leaves | 7 | 5 | 4 | 3 | 1 to 10 |
| `pressure_below` | Crown share below which rivals are pushed out | 5 | 10 | 15 | 20 | 0 to 30 |
| `influence_trickle` | Influence a man earns each turn | 7 | 5 | 4 | 3 | 0 to 20 |
| `settlement_influence` | Influence for taking a settlement | 30 | 24 | 20 | 16 | 0 to 60 |
| `favour_gift_cost` | Price of Send a Gift | 400 | 600 | 800 | 1000 | 100 to 3000 |
| `favour_secure_cost` | Price of Secure Loyalty | 1800 | 2500 | 3200 | 4000 | 500 to 10000 |
| `party_intrigue_line` | Loyalty at which parties start scheming | 45 | 55 | 60 | 65 | 20 to 80 |
| `rivals_min` | Fewest rival parties | 2 | 2 | 3 | 3 | 1 to 4 |
| `rivals_max` | Most rival parties | 3 | 4 | 4 | 4 | 1 to 4 |
| `term_turns` | Office term, in turns | 5 | 5 | 5 | 5 | 2 to 10 |

Default is today's value for every key (`pressure_below` is today
`IC.CONTROL[#IC.CONTROL - 1].floor`, which is 10). The Gentle, Harsh and Ruthless numbers are a
first proposal for the author to tune. `rivals_max` stops at 4 because there are four rebel
banners; a `rivals_min` above `rivals_max` is clamped down to it when read.

### 3.3 Switches

All checkboxes, all on by default, so a campaign without MCT plays exactly as today.

| Key | Label | Off means |
|---|---|---|
| `parties_act` | Rival parties act on their own | no new schemes, feuds, demands or offers; `IC.party_turn` still gives overseers their experience and settles anything already open |
| `ai_courts` | Other Chaos Dwarf factions have courts | an AI faction's court is never rolled or run, and the event listeners (battles, settlements, ranks, deaths, confederation) skip it, so AI empires never split; a human faction's court is unaffected |
| `secession` | Parties can secede | no countdowns, no warning cards, no secession |
| `pressure` | A weak Crown pushes rivals out | `IC.tick_pressure` does nothing |
| `crown_split` | Your own party can split | `IC.splinter` does nothing |
| `detailed_log` | Detailed log | routine "IRON COURT:" lines stop; failures are always written |

The detailed log needs a split: `IC.say` (routine, switchable) and `IC.warn` (failures, always
written). The harness's failure collector watches both.

### 3.4 Freezing the settings into the save

- `IC.TUNE_DEFAULTS`: the fourteen numbers and six switches above, with today's values.
- `IC.TUNE_ORDER`: their keys in a fixed order. **New keys are only ever appended**; an older
  save's shorter string leaves a new key on its default.
- `IC.PRESETS`: the table above. `IC.read_mct_or_defaults()`: returns the defaults when
  `IC.is_mp()` or MCT is absent; otherwise reads the preset, then the switches, then (Custom
  only) the sliders, **type-checking each against its default** (a slider answering a boolean
  is a mis-registered option and falls back to the default).
- `IC.pack_tune(t)` / `IC.unpack_tune(s)`: a `|`-joined string, booleans as 1/0, a missing key
  written as its default and never as 0.
- `IC.apply_tune(t)`: writes each value over `IC.TUNE[key]`, so every existing
  `IC.TUNE.x` read is unchanged. It also re-derives the one load-time copy: the `line` of the
  `discredit` and `rumour` entries in `IC.PARTY_MOVES`, which are copied from
  `T.party_intrigue_line` when the parties file loads.
- **When:** first thing at every first tick, before the player's court is rolled
  (`IC.freeze_tune`). A save holding `derpy_ic_tuned` plays on it. A save without one (a new
  campaign, or a save from before this build) reads MCT, or takes the defaults, then applies
  and saves the result, once. MCT has already read the player's settings by then: it does so
  in its `LoadingGame` callback. The model's first-tick body becomes the named
  `IC.first_tick()` so the harness can drive it (its `cm` stub keeps only the last first-tick
  callback, which is the panel's).

### 3.5 Registration rule

Every option is registered three times: in the MCT file, in `IC.TUNE_DEFAULTS` and in
`IC.TUNE_ORDER`, and read by name at its use site. The packing gate refuses a pack where any
MCT option key is missing from one of the three.

## 4. Checks

**Harness** (`tools/_iron_court_harness.lua`), each watched failing first:

- `pack_tune` / `unpack_tune` round trip, including an older save one field short, and a
  partial table packing defaults rather than zeros.
- `read_mct_or_defaults` against a stubbed MCT: each preset, Custom sliders, switches read on
  every preset, a wrongly typed value falling back, no MCT at all.
- Multiplayer never reads MCT, even when a stubbed MCT holds other values.
- The freeze happens once, at first tick and before the court is rolled (a new campaign's
  court is rolled on the frozen rival count); a reload keeps the frozen values whatever MCT
  now says.
- Each switch turns its system off, driven through a real frozen `derpy_ic_tuned` string and
  never by replacing an accessor.
- `apply_tune` moves the discredit and rumour lines.
- In multiplayer, each of the eleven panel actions changes nothing until its `UITrigger` is
  delivered, then changes the court exactly as the single-player path does; a trigger from an
  unknown cqi and another mod's trigger change nothing; a message over 100 characters is
  refused.
- `ICUI.player()` reads the local faction with the forced flag (the stub throws without it).
- `IC.hold_feed` holds nothing in multiplayer.

**Packing gate** (`tools/import_iron_court.py`):

- The UI script calls none of the eleven actions directly.
- Every MCT option key appears in the MCT file, `IC.TUNE_DEFAULTS`, `IC.TUNE_ORDER`, and a
  read site.
- `tools/deploy_iron_court.py` packs the MCT file; the post-save check lists it.

**Mutation runner:** a mutant per new guard (the MP refusal, the forced flag, the MP-ignores-MCT
guard, the append-only unpack, each switch, the apply re-derivation), then the full run.

## 5. Not in this design

- Any change to how the Guilds reads its settings after a mid-turn load (it has the same
  defaults-until-next-turn gap; noted for its own fix).
- The host's settings in multiplayer (the author chose defaults).
- Sliders for the other ~135 numbers in `IC.TUNE`.
- A two-machine test run.
