# Development guide

How The Iron Court works inside, how it is built and checked, and the engine behaviour that
shaped the code. For what the mod does from a player's side, see the
[README](../README.md).

This repo is mirrored from a larger modding workspace. The notes in `docs/history/` link
to reference docs in that workspace (`docs/CUSTOM_UI.md`, `docs/MISSIONS.md`, the session
index and others), and to session scratch folders, none of which are included here.

## 1. Shape

All the logic is Lua. The DB rows exist only because the engine needs a row to show
something: an effect bundle to apply, a trait to stamp, a mission to issue, an event-feed
entry to raise, a banner for a rebellion.

| File | Global | Role |
|---|---|---|
| `zzz_derpy_iron_court.lua` | `IC` | The model: parties, backgrounds, influence, offices, overseers, loyalty, the five control bands, intrigue, favours, secession, splintering, the record, save state. |
| `zzz_derpy_iron_court_parties.lua` | `IC` (extends it) | The rival parties' own acts: intrigue against the Crown, feuds, demands, offers, and overseer experience. Loads after the model (`.` sorts before `_`) and changes nothing in the campaign at load. |
| `zzz_derpy_iron_court_ui.lua` | `ICUI` | The panel, its six tabs, the character picker, the HUD opener and the influence plate on CA's character details panel. Every action it takes goes through `IC.mp_send`; it never calls a model mutator or writes court state directly. |
| `script/mct/settings/derpy_iron_court.lua` | none (MCT's own environment) | The MCT page: a difficulty dropdown, seven switches and fourteen Custom numbers. Runs only when MCT is installed and calls nothing in the mod. |

Every tunable is in `IC.TUNE` (the model) or at the top of the parties file, which appends
its own keys to the same table. **The MCT settings are frozen into the save at the first
tick** (`IC.freeze_tune`, saved value `derpy_ic_tuned`), because MCT gates nothing in a
campaign by itself. A difficulty other than Custom sets all fourteen numbers
(`IC.PRESETS`). Six switches stay live (`IC.LIVE_TUNE`: `parties_act`, `secession`,
`pressure`, `crown_split`, `all_cards`, `detailed_log`). They are read again at every load
and on MCT's `MctFinalized`, and a countdown switched off ends at once. `ai_courts`, the
difficulty and the numbers stay frozen. A new setting is appended to `IC.TUNE_ORDER`, never
inserted. In multiplayer MCT is not read at all, because each machine's MCT is its own.

**Multiplayer.** Every panel action (appoint, dismiss, overseer, release, plot, favour,
hire, grant, refuse, accept, decline, fill) goes through `IC.mp_send(faction_key, op, arg)`.
In single player that runs the action at once. In multiplayer it sends `ic1|op|arg`
through `CampaignUI.TriggerCampaignScriptEvent`, and the `ic_mp` listener runs it on every
machine. The model answers through `IC.after_op`, which the panel shows only to the player
who clicked. One action is in flight at a time. None of this has been tried on two machines
yet.

**Coverage is the Chaos Dwarf subculture** (`IC.is_chd`, `wh3_dlc23_sc_chd_chaos_dwarfs`).
Every such faction, human or AI, runs `IC.turn` at its turn start. The panel, event cards,
the rival parties' acts, overseer experience and pressure are for human factions only.

**Membership is derived, never stored.** A man's party is read off his background trait
(`IC.house_of_character`); a background whose party is not in this court falls through to
the Crown. A confederated Chaos Dwarf faction listed in `IC.ORIGINS` joins as a party of its
own (`confed`). `IC.ORIGINS` names the five vanilla Chaos Dwarf factions and eleven houses
that other mods add (the `cr_chd_*` keys), by key; a key that is not loaded never matches,
so no other mod is required.

## 2. The turn, and where the numbers come from

`IC.turn`, per Chaos Dwarf faction, in this order: roll the court if it is new, stamp
backgrounds, reconcile parties, find leaders, reconcile overseers, tick province loyalty,
pay influence, expire terms, warn of terms ending next turn (human only), enforce the
office bars (human only), let an AI court fill its
offices and provinces, restamp the influence traits, drift loyalty, apply the office,
overseer and control bundles, roll pressure, flush the feed, run the parties' turn (human
only), tick secession, check the Crown for a split, save.

| Listener | Event | Does |
|---|---|---|
| `ic_turn` | `FactionTurnStart` | `IC.turn`, above. |
| `ic_mp` | `UITrigger` | Runs a panel action sent through `IC.mp_send`, on every machine. |
| `ic_live_tune` | `MctFinalized` | Re-reads the six live switches (single player only). |
| `ic_confed` | `FactionJoinsConfederation` | Stamps the arriving men and seats their faction as a party. |
| `ic_born` | `CharacterCreated` | Stamps a new man's origin and background; completes a hire. |
| `ic_battle` | `CharacterCompletedBattle` | Influence for the winner, loyalty for his party. |
| `ic_took` | `GarrisonOccupiedEvent` | Influence for taking a settlement. |
| `ic_rank` | `CharacterRankUp` | Influence per rank gained. |
| `ic_dead` | `CharacterConvalescedOrKilled` | For a dead man only (`is_alive()`): vacates his seats and provinces, costs his party loyalty, breaks his oaths. |
| `ic_demand_*` | `MissionSucceeded`, `MissionFailed`, `MissionCancelled` | A backstop for demand missions; the Lua settles every outcome itself. |
| `ic_click` and five more | UI events | The panel, the opener, and the influence plate's three triggers. |

Default influence, all in `IC.TUNE`:

| Source | Default |
|---|---|
| Battle won | 50 heroic, 30 decisive, 16 close, 8 pyrrhic |
| Settlement taken | 24 |
| Rank gained | 3 a rank |
| Trickle | 5 a turn; 0 for a lord leading an army, but a garrison commander earns it |
| Office wage | 20, 15, 10, 5 a turn, tiers 1 to 4 |
| Overseer wage | 5 a turn; paid twice to an overseer who cannot gain rank |

A party's **weight** is 10 on entering the court, plus 6 per office (double for its own
claimed office), plus 3 per overseer, plus each member's influence / 100 scaled by his
ambition (75, 100 or 125%). Its **share** is its weight over the court's total. The Crown's
share picks one of `IC.CONTROL`'s five bands (75, 60, 40, 10, 0).

Offices ask a rank of 30, 20, 12 or 5 by tier and, for the player only, influence of 400,
300, 200 or 100. Terms are 10 turns. The man whose term ended cannot take that seat again
for 3 turns, and his party gets no +8 when he does. **Loyalty** starts at 55 and has exactly one writer,
`IC.move_loyalty`. Its per-turn terms (`IC.loyalty_terms`, which the tooltip draws) are +2
per seat and per province held, -1 with no seat, -2 while an outsider holds a claimed
office, +2 per province under Military Doctrine, the party's traits, its leader's trait and
a blood-oath. Events move it too: +3 battle won, -8 member died, +8 appointed, -6 snubbed,
-12 dismissed early.

Secession: share at least 25 and loyalty at most 20 start a 5-turn clock, with cards at 5
and 3; loyalty 0 goes at once. Pressure: below 10% Crown share, 8% a point below, capped at
60%. The Crown splinters at loyalty 25 after 3 turns. The rival parties' lines are in the
parties file: intrigue at 55, unseat and recall at 25, murder at 10, demands from 26 to 74,
offers from 75.

## 3. Save state

All keys are `cm:set_saved_value` strings.

| Key | Holds |
|---|---|
| `derpy_ic_<faction>` | the court, one per Chaos Dwarf faction: ten sections split by `\|` (parties, offices, overseers, terms, influence, record, province loyalty, ambition, the rolled marker, each seat's last holder). The last two are optional, so an older save still reads |
| `derpy_ic_tuned` | the settings the campaign plays on, in `IC.TUNE_ORDER` order |
| `derpy_ic_ui_prefs` | the panel's last tab and sorts (single player only) |
| `derpy_ic_agenda_<faction>` | the human court's agenda: a warned move, feuds, feud rest, the live demand, open offers |
| `derpy_ic_risen_<rebel faction>` | the name a rebellion took, re-applied on every load |

A party is 16 comma fields: slug, weight, loyalty, secession clock, name head, name tail,
confederated, pressed, protected-until, trait 1, trait 2, oath (ours), oath (theirs),
snubbed, split count, a lord made for it in the recruitment pool. The record holds 40
entries and writes `-` for an empty field, because `split` drops empty values.

The court is read with `string.gmatch(packed .. "|", "([^|]*)|")`, the star form, because
`+` would drop an empty section and shift every later one. Section 7 says why it is not
`string.find`. Bundles are not
tracked in the save; each turn removes and re-applies them from the court.

## 4. Keys the engine reads

| Kind | Key |
|---|---|
| Office and vacancy bundles | `derpy_ic_office_<office>`, `derpy_ic_vacant_<office>` |
| Control bands | `derpy_ic_control_<band>` |
| Overseer bundles | `derpy_ic_gov_base`, `derpy_ic_gov_house_<party>`, applied to the faction's part of the province |
| Traits | `derpy_ic_bg_*` (27 backgrounds), `derpy_ic_house_*` (24 origins), `derpy_ic_standing_*` (5 influence bands), `derpy_ic_title_*` (14 offices), `derpy_ic_ambition_*` (3) |
| Demand missions | `derpy_ic_demand_office`, `derpy_ic_demand_province`, issued with `cm:trigger_custom_mission_from_string` and a `SCRIPTED` objective |
| Feed events | `derpy_ic_event_<name>`, indexes 2600 to 2621, derived from position in the generator's list, so new ones are appended |
| Rebel banners | `factions` rows for the four pool factions, `flags_path` pointed at `ui/flags/derpy_ic_rising_0N` |
| Panel text | resolved by the panel at draw time; the model stores keys and numbers only |

The DB side is twelve tables plus the loc: `effect_bundles`,
`effect_bundles_to_effects_junctions`, `character_traits`, `character_trait_levels`,
`trait_info`, `missions`, `campaign_payload_ui_details`, `event_feed_message_events`,
`campaign_groups`, `campaign_group_members`, `campaign_group_member_criteria_values` and
`factions`.

## 5. The panel

The panel is **our own `.twui.xml`, created at runtime**. No CA layout is overridden.

- `tools/gen_ic_ui.py` writes seven layouts (panel, card, row, party, plot, opener,
  standing) and a `_compact` copy of five of them. **One GUID prefix per file**: `IC30` to
  `IC36`, and `IC40` to `IC44` for the compact copies.
- The engine ignores offsets on a runtime-created component, so the files carry none and
  `ICUI` places everything with `MoveTo`. Every layout number is typed at 1920x1080.
- **Scale.** The box is the widest 16:9 fit, clamped to 1600..2560 wide. `ICUI.apply_scale`
  rebuilds every table from `ICUI.BASE` with integer edge scaling; below 1920 it opens the
  compact files, one CA font size down. The gate runs the Lua's scaling and compares it to
  the generator's at 1600, 1760, 1920 and 2560.
- Rows, cards and move cards are pools created once and shown or hidden. A second click on a
  chosen party card opens its members; the chosen card wears CA's gold unit-card frame.
- The generator also writes the panel's own pictures from numbers: plates per party, the
  party flags, the dial's 1,560 wedge pictures, its dividers and rim, a mask and a
  silhouette. `art_paths()` is the one list the packer, the prune and the checks all walk.
- The opener sits on the top resource strip, left of the Great Guilds' button and the Zharr
  Exchange's when present (`ICUI.btn_anchor`), and is re-placed every turn in case the HUD
  was still building at first tick.
- While the panel is open, `IC.hold_feed` holds event cards (up to 10) and releases them on
  close.

## 6. Build pipeline

Run everything from the repo root. Several tools hard-code the game at
`F:\SteamLibrary\steamapps\common\Total War WARHAMMER III` and Lua at
`C:\Program Files (x86)\Lua\5.1\`; edit those constants for your machine.

| Step | Command | Notes |
|---|---|---|
| Vanilla dump | `py tools/fetch_vanilla_tables.py <tables>` | Once. Needs RPFM open. Writes RPFM's JSON export into `.skilltree_cache/`, which is CA's data and not in this repo. The README lists the tables. |
| Donor rows | export from `db.pack` in RPFM | `Modding Files/source/iron_court/_donor_factions.tsv`, four CA rows (see the README). |
| Parse | `luac -p <file>` for the three scripts | Lua 5.1.5 |
| Test | `lua tools/_iron_court_harness.lua` | Loads all three shipped scripts against a stubbed campaign and a fake component tree. Prints `iron court harness: ok (648 checks)`. |
| Mutation | `py tools/mutate_iron_court.py [name ...]` | 476 mutants, each a plausible implementation mistake written into the shipped Lua, the harness run, the file restored. A survivor or a stale anchor fails. One run at a time. |
| Data | `py tools/gen_iron_court.py --check`, then `--write` | Builds every DB row and loc line and refuses on a broken rule (below). |
| Layouts | `py tools/gen_ic_ui.py --write`, then `--check` | Writes the layouts and generated pictures; `--check` writes nothing and reports `ok: 12 files, 478 components`. |
| Art | `py tools/make_ic_backdrop.py --write`, `py tools/make_ic_rebel_flags.py --write` | The backdrop and the four banners. `--check` re-measures what ships. Inputs and outputs are CA-derived and not in this repo. |
| Look | `py tools/preview_iron_court.py` | Renders the tabs to PNGs in `.skilltree_cache/ui_preview/` with the game shut, through TWUI Studio's vendored source (not included). Positions are exact; glyph widths are not. |
| Gate | `py tools/import_iron_court.py` | Every offline check below. Writes nothing in the repo. |
| Pack | `py tools/deploy_iron_court.py --no-copy` | Needs RPFM's MCP server. Runs the gate, refuses duplicate keys, creates the pack, imports every table the generator declares, adds scripts, layouts and art, saves to `Modding Files/Modpacks/`, then re-reads the saved pack and refuses if any expected file is missing. |
| Deploy | `py tools/deploy_iron_court.py` | The same, then copies into `data/`. Refuses while `Warhammer3` is running. |

The generators, the preview, the mutation runner and the rebel-flag tool take
`--selftest`, which breaks something on purpose and proves the check still reports it. Do
not run two selftests or mutation runs at once: they write and restore shipped files.

What `gen_iron_court.py --check` refuses on, among others: an effect key vanilla does not
have, or a scope vanilla never pairs it with; an `is_positive_value_good` that disagrees
with vanilla (rows declare a magnitude and an intent, and the sign is derived); a duplicate
bundle key; a bundle or trait missing loc; a column left empty that vanilla never leaves
empty; a faction key that is not a Chaos Dwarf faction; a rebel general, hero or unit the DB
does not allow; a hire whose agent type and subtype are not a real pair; a `factions` row
that changes anything but `flags_path`; a feed index that collides with vanilla or with
itself, or an event missing a loc key; a move with no result lines.

What `import_iron_court.py` adds: each random roll has one caller; no harness stub offers a
method CA's `scripting_doc.html` does not document; loyalty has one writer; every TSV
matches `build()`; the Lua's copies of origins, offices, tiers, ambition, control bands and
hires match the generator's; `SetStateText`, `:Parent()` and `Resize` are used safely;
`luac` and the harness pass; the panel calls no model mutator directly, only `IC.mp_send`; every MCT setting has a reader; no undeclared ALL_CAPS global (`check_lua_undeclared.py`); no
number literal on the left of an arithmetic operator (`check_lua_literal_left.py`); every
layout offset in the Lua equals the generator's; the layouts on disk match the generator;
the portrait mask list matches the installed packs. Run `py tools/check_lua_api.py`
separately: it checks every `cm:` and `core:` call against CA's docs.

`tools/probe_ic_*.lua` are not checks. They are Lua chunks for the author's live-game bridge
(not included): two of them found the string-library break in build 7EF8F281, and the third
reads the court's live state.

**Deploying:** copy with the game closed. The game holds its packs open. Keep the previous
pack as a backup. A pack is not byte-reproducible (every DB table carries a per-save GUID),
so compare the saved and deployed copies with each other, not with an older build. A pack
new to `data/` starts disabled.

## 7. Engine behaviour that shaped the code

Each of these cost a bug or a build to learn. Most fail silently.

- **WH3's `string.find` is not stock.** Its third argument (the start position) makes it
  return nil, and its fourth (plain) breaks the string library for the whole session. The
  first save format was read with the third, so every section after the first came back
  empty on every load, and offices, overseers and influence vanished a turn after being
  set. The harness runs stock Lua and could not see it; `check_lua_api.py` now flags it.
- **Handing an engine setter `nil` breaks the string library too.** `SetVisible(rival)` with
  `rival` built from an `and` chain received nil when nothing was chosen, and CA's own UI
  scripts then failed. The harness's fake setters now record any non-boolean.
- **The game's Lua compiler is not stock 5.1.5.** In a function with over 255 constants, a
  number literal on the left of an arithmetic operator is miscompiled: `2 * T.x` ran as
  `T.x * T.x`. The fix is the literal on the right or a local.
- **One listener can silence every other mod.** CA's callback wrapper catches the error, but
  its failure handler is unprotected, so the rest of that event's listeners never run. The
  panel's listener called `context:string()`, which is a field and not a method, on every
  panel open and close, and stopped 31 of 40 `PanelOpenedCampaign` listeners from all mods.
- **One world change per frame.** A secession that woke a faction, placed armies, moved
  twenty regions and declared war in one turn-start frame returned cleanly and crashed the
  game about a second later. `IC.secede` runs its steps one `cm:callback` apart.
- **Rebel factions cannot hold land.** `cm:get_faction` answers false for an `is_rebel`
  faction, so secessions wake the four dormant Chaos Dwarf quest-battle factions instead.
- **A banner cannot be set at runtime.** `flags_path` is a DB column and no script call
  writes it; `cm:change_custom_faction_name` is the only lever over a rebellion's name, and
  it must run after the army that wakes the faction. Hence four banners, and `rivals_max` 4.
- **`is_unique()` is false for modded legendary lords.** A legend is known by subtype.
- **There is no `CharacterKilled`.** `CharacterConvalescedOrKilled` fires for wounds too, so
  the handler tests `is_alive()`. `is_dead` is a faction method; the harness stub once
  offered it on characters and the real handler raised every time an officer died.
- **An agent subtype's race is only readable from its voice-over group,** and the key lies:
  `gorduz_backstabber` is a hobgoblin. `IC.NOT_DWARF` keeps him off a party card.
- **An event-feed index needs four tables behind it,** and the log says the card was shown
  whether or not it drew. The deploy once packed five of the generator's nine tables for a
  month, so it now derives its list from the generator.
- **A required column left empty rejects the whole pack at load, naming the wrong row.**
  Every junction row needs `advancement_stage = start_turn_completed`. The generator now
  compares every empty column against vanilla.
- **A trait needs a `trait_info` row** as well as its two trait tables, and its loc is keyed
  off the level key in `character_trait_levels`.
- **The screen a script sees is the window divided by UI Scale, floored at 1600x900.** No
  script can set a font size, so the small end is a second set of layouts. `Resize` scales
  children by default; the panel passes `false`.
- **Text is wider in game than any desktop font.** About 19% wider (`GAME_FONT_WIDER`), and
  capitals 12 to 20% wider again, which is why button labels are title case.
- **Hiding the HUD to clear the screen floods every other mod with UI errors.** The panel
  draws above the HUD with `PropagatePriority` instead.
- **The recruitment pool cannot be read.** A lord made there for a leaderless party is not
  in `character_list`, so a save field stops one being made every turn. A garrison
  commander or a pooled lord never gains rank from `add_agent_experience`, and says nothing.
- **No loc calls from turn handlers.** One can crash turn 1 inside a `pcall`. The model
  stores keys; the panel resolves them. `cm:get_faction` returns `false`, not nil.
- **A crash dump is in `%APPDATA%\The Creative Assembly\Warhammer3\crash_report\`,** not the
  game folder; the script log is in the game folder.

## 8. Where the design lives

- [docs/design/2026-09-11-iron-court-design.md](design/2026-09-11-iron-court-design.md): the
  original design. Much is superseded: the parties were the ten houses and are now nine
  interests, "standing" is now influence, and secession raises armies.
- [docs/design/IRON_COURT_VS_ROME2.md](design/IRON_COURT_VS_ROME2.md): the gap analysis
  against Rome II's politics, and what was built from it.
- The 2026-09-20 specs (ambition, Military Doctrine loyalty), the 2026-09-23 spec (rival
  parties that act on their own) and the 2026-09-24 spec (screen scaling), with their plans
  in `docs/plans/`.
- `docs/history/`: dated handoffs, the most recent last. When a handoff and the code
  disagree, the code wins.

Still owed in game, as of the last build: a card taking a click through its children, the
gold frame's nine-slice, the Petitions label fitting at 1600x900, and Send a Gift charging
and turning red at 100 loyalty. Thin light lines over the dial and move cards were seen at
1600x900 on 2026-09-24; their cause was not found.
