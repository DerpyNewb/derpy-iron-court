# Iron Court for Dwarfs - interface contract shared by the six phase plans

Spec: `docs/superpowers/specs/2026-10-04-iron-court-dwarfs-design.md` (approved 2026-10-04).
Every phase plan uses EXACTLY these names. A plan that needs a name not listed here adds it to
its own Interfaces block and says which later phase consumes it.

## Files

- `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua` - model; keeps the Chaos
  Dwarf tables where and as they are (same names, same column-0 `}` closers: the generators'
  regex scrapers `IC\.X = \{(.*?)\n\}` and the harness's 304 references depend on it).
- `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_dwarf.lua` - NEW (phase 2): the
  Dwarf race table. Loads after the model (`.` sorts before `_`) and before `_parties` (`d` < `p`).
- `zzz_derpy_iron_court_parties.lua`, `zzz_derpy_iron_court_ui.lua`, `zzz_derpy_iron_court_ui_map.lua`.
- Python: `tools/gen_iron_court.py`, `tools/gen_ic_ui.py`, `tools/import_iron_court.py`,
  `tools/deploy_iron_court.py`, `tools/preview_iron_court.py`, `tools/mutate_iron_court.py`,
  harness `tools/_iron_court_harness.lua`.

## Lua (phase 1 creates all of these with the Chaos Dwarf race only)

```lua
IC.RACES = {}                 -- race key -> race table; phase 1 registers chd, phase 2 dwf
IC.RACE_ORDER = {"chd"}       -- phase 2 appends "dwf"
-- A race table:
-- { key = "chd" | "dwf", subculture = "...", infix = "" | "dwf_",
--   ORIGINS, PARTIES, OFFICES, GOVS, GOV_ORDER, START_GOV, LAWS, LAW_ORDER, DEEDS,
--   REBEL_POOL, REBEL_POOLS, REBEL_GENERALS, REBEL_HEROES, REBEL_DRAFT, BACKGROUNDS,
--   NAME_HEADS, NAME_TAILS, PARTY_TRAITS, LEADER_TRAITS, LEGEND_SUBTYPES,
--   TEMPLE_BUILDINGS, MILITARY_DOCTRINE, PLOT_KEYS (nil = every IC.PLOTS entry),
--   tune = {},                -- overrides layered UNDER the government layer
--   layout = "ziggurat" | "grid",
--   grid = nil | {cols = 5, rows = 4, throne = {2, 0}, cells = {{c, r}, ... 14, IC.OFFICES order}},
--   art = {} ,                -- phase 3 fills it for dwf; chd = {} means "the twui as shipped"
--   -- derived by IC.build_race:
--   TIERS, TIER_SEATS, PARTY_OF_BG, MAX_SEATS }
function IC.register_race(r)          -- build_race(r); IC.RACES[r.key] = r
function IC.build_race(r)             -- derives TIERS, TIER_SEATS, PARTY_OF_BG, MAX_SEATS
function IC.race_of(faction)          -- faction interface -> race table or nil (subculture)
function IC.race_key(faction_key)     -- "chd" | "dwf" | nil
function IC.R(faction_key)            -- race table; IC.RACES.chd when the faction has none
                                      -- (only court factions call it). Cached in IC._race_cache,
                                      -- never saved.
function IC.has_court(faction)        -- race_of(faction) ~= nil and the race is switched on
function IC.is_chd(faction)           -- KEPT: true only for the chd race (Chaos Dwarf-only code)
function IC.runs_court(faction)       -- unchanged meaning, now via has_court
function IC.tune(faction_key, key)    -- EXISTING; layers TUNE -> race.tune -> government
function IC.office_by_slug(slug, faction_key)   -- faction_key added (race lookup)
function IC.law_opt(cat, opt, faction_key)      -- faction_key added
function IC.is_party(slug, faction_key)         -- faction_key added
function IC.rolled_name(slug, head, tail, faction_key) -- faction_key added (shipped takes slug first; phase 1 plan)
-- Keys: every bundle/trait/loc key builder takes faction_key and inserts R.infix after
-- "derpy_ic_" + kind + "_": chd infix "" (keys byte-identical to today), dwf "dwf_".
function IC.key(kind, slug, faction_key)  -- "derpy_ic_" .. kind .. "_" .. R.infix .. slug
```

UI (`zzz_derpy_iron_court_ui.lua`): `ICUI.race()` -> `IC.R(ICUI.player())`. Phase 3 adds
`ICUI.skin(panel)` (applies `R.art` with `SetImagePath` after `CreateComponent`) and the throne
component `ic_throne` with text children `ic_throne_name` and `ic_throne_leader`;
`ICUI.BASE.CARD_XY` is set from the race before `ICUI.apply_scale`.

## Save (`IC.pack` / `IC.unpack`; today 18 `|` fields, houses 20 `,` fields)

- Race is NEVER saved; it is derived from the subculture.
- Field 19 (phase 4): grudges, per house `slug:code.turn;code.turn` joined by `/`. Old saves -> empty.
- Field 20 (phase 5): Book bands crossed, `other_faction_key:n` joined by `/`. Old saves -> empty.
- `unpack` already tolerates short field lists; each phase adds a harness check that an 18-field
  (and for phase 5 a 19-field) save string loads with the new field empty.

## TUNE keys (added to `IC.TUNE`, `IC.TUNE_DEFAULTS`, MCT where marked)

- phase 2: `dwarf_courts = true` (MCT switch "Dwarf courts", live).
- phase 4: `grudge_loyalty = -1`, `grudge_max = 4`, `kin_loyalty = 1`,
  `plot_weregild_cost` (gold), `plot_weregild_loyalty = 4`; the dwf race's `tune` scales every
  secession countdown knob by 1.5 (phase 4 names the exact `secede_*` keys it scales).
- phase 5: `book_bands = {500, 1000, 2000}`, `book_penalty = {-1, -2, -3}`, `book_named = 1000`,
  `book_top = 3`.

## Grudges (phase 4)

```lua
IC.GRUDGE_CODES = {"slayer", "castout", "insult", "bar", "recall", "dismiss", "oath", "demand", "peace"}
function IC.grudges(faction_key, slug)            -- list of {code = , turn = }
function IC.grudge_write(faction_key, slug, code) -- no-op unless dwf race; caps at grudge_max
function IC.grudge_settle(faction_key, slug, how) -- how = "weregild" | "seat"; settles the oldest
```
Plot key `weregild` (category `bond`, `race = "dwf"`).

## Book of Grudges (phase 5)

```lua
function IC.book_weight(faction_key, other_faction_key) -- CA grudge points on other's armies+settlements
function IC.book_names(faction_key, n)                  -- top n {key = , weight = }
function IC.book_tick(faction_key)                      -- bands, once each, never reversed
```
Deed code `grudge` -> parties `{"legion", "temple"}` (dwf race).

## Python

- `gen_iron_court.py`: `RACES = {"chd": {...}, "dwf": {...}}` holding each race's ORIGINS,
  PARTIES, BACKGROUNDS, OFFICES, GOVERNMENTS, LAWS and `infix`; `tier_seats(race)` replaces the
  hard-coded `TIER_SEATS`; `bundle_key(kind, slug, race="chd")`.
- `gen_ic_ui.py`: `card_grid(race="chd")`, `ziggurat_boxes(race="chd")` (chd only),
  `throne_box()` (dwf), `at_box(bw, race="chd")`; every check function takes `race`.
- `import_iron_court.py`: scrapers take the table prefix (`IC.X` or `DWF.X`).

## Rules every phase keeps

- Not a git repo: a "checkpoint" step runs the gates instead of committing. Gates: `luac -p` on
  every court Lua file; `"C:\Program Files (x86)\Lua\5.1\lua.exe" tools\_iron_court_harness.lua`;
  `py tools\check_lua_api.py`; `py tools\check_lua_literal_left.py`;
  `py tools\check_lua_undeclared.py` (over the set, as the importer runs it);
  `py tools\gen_ic_ui.py --check` and `--selftest`; `py tools\gen_iron_court.py --check`.
- Build and deploy only with `py tools\deploy_iron_court.py` (needs RPFM open; backs up to
  `Modding Files/Backup/`, never into data/ or Workshop folders; deploys to data/ only when
  Warhammer3.exe is not running; `--wait` otherwise).
- After `mutate_iron_court.py`, re-run the generators: the runner restores the source, not what
  that source wrote.
- No emojis; never the word "rung"; player text in plain words (no "standing", "cap", "AI").
- Every key (faction, unit, effect, building, subtype) verified against `db.pack`
  (`tools/read_vanilla_db.py`) before it is written.
- Every touched UI view rendered with `tools/preview_iron_court.py` from the shipped Lua and
  shown to the author for approval before it ships.

## Amendments from the phase plans (2026-10-04)

- Phase 1: `IC.rolled_name(slug, head, tail, faction_key)`; also `IC.RACE_FIELDS`, race field `switch`,
  `IC.rkey`, `IC.origin_trait`, `IC.bg_trait`, and a trailing `faction_key` on `law_stance`, `gov_for_party`,
  `office_influence`, `office_rank`, `office_weight`, `office_title_key`, `recruit_influence`, `rebel_draw`,
  `roll_origin`, `origin_for`, `chd_factions`, `member_trait_keys` and every bundle/trait builder.
- Phase 4: Pay the Weregild is in the party column (`cat = "house"`), not Bonds (a fifth Bonds card
  shrinks every card to 138px and fails the layout check); `IC.plots_in(cat, race_key)`, `IC.tune_layer`,
  TUNE `oath_broken_loyalty`; scaled secession keys `secede_turns` and `plot_provoke_clock` (`{mul = 1.5}`).
- Phase 5: `IC.book_list`, `IC.in_book`, `IC.book_peace`, TUNE `deed_grudge = 3`, DEEDS field `also`.
- Phase 2: governments and laws KEEP the Chaos Dwarf slot slugs (conclave, priest, forge, legion, chain,
  convoy; labour/tribute/worship/war and their option slugs) - only names, effects and icons change.
  Dwarf rebel pool is `wh_main_dwf_dwarfs_qb2`-`qb4` only (the separatists' only general is a Slayer);
  NO Dwarf temple deed (no Dwarf temple chain in db.pack). Race fields `switch`, `ENVOY_TASKS`,
  `STORE_LORDS`, `REBEL_LORD`, `REBEL_PERSONALITY`, `MILITARY_DOCTRINE_NAME`, `PLOT_TEXT`, `FAVOUR_TEXT`,
  `EVENT_LOC`; envoy knobs `envoy_oath = 20`, `envoy_grow = 5`, `envoy_rec = 15`. The Iron Law's oath
  discount is phase 2; its broken-oath loyalty is phase 4. Phase 1 checks expecting `IC.RACE_ORDER ==
  {"chd"}` become `{"chd", "dwf"}` in phase 2.
- Phase 1 pre-flight: `IC.register_race` appends its key to `IC.RACE_ORDER` itself - phase 2 must NOT
  append "dwf" by hand. In phase 1 only `card_grid`, `ziggurat_boxes` and `at_box` in `gen_ic_ui.py` take
  `race`; the rest of its checks become per-race in phase 3.
- Phase 1 final review (2026-10-04):
  - Python: `RACES[race]` carries `"prefix"`; `LUA_OF_PREFIX[prefix]` names the file. `race_lua(prefix)` and `lua_table(name, prefix, src)` (column-0 anchored) are the only scrapers - a phase never adds its own regex for a race table.
  - `IC.register_race` appends to `IC.RACE_ORDER`, raises `IC.MAX_SEATS` and refuses a race table missing a required field (`key`, `subculture`, `infix`, `tune` and every `IC.RACE_FIELDS` name); `switch`, `layout`, `art` are optional.
  - `IC.rkey(kind, slug, R)` takes a race TABLE (`nil` = chd); `IC.key(kind, slug, faction_key)` a key.
  - Keys with the infix after phase 1: house, bg, title, member, office, vacant, doctrine, gov_house, law, control, standing, ambition, gov base, and the loc kinds. Event, secession and demand keys do not take it (phase 2 decides per key).
  - Argument convention: helpers that were faction-first stay faction-first (`law_in_force(fk, cat)`, `member_trait(fk, slug)`, `party_name(fk, slug)`, `rebel_kit(fk, cqi)`); helpers that gained the faction in this plan take it LAST. Read the definition, never infer.
  - `PARTY_TROOPS` / `TROOPS_DEFAULT` are race fields. Still Chaos Dwarf-only and owned later: `ICUI.DEED_TEXT`, `ICUI.HELP` (phase 2); `ICUI.LAW_ART_DIR`, `ICUI.LAW_ART`, `ICUI.GOV_ART`, `ICUI.CARD_XY` (phase 3).
