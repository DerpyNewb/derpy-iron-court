# The Iron Court for Dwarfs - design (2026-10-04)

Status: BUILT in six phases and released as build `F4CF5CA4` (2026-10-06), pushed to GitHub as
d163830; not yet seen in game. Write-up: `docs/sessions/HANDOFF_20261006_IRON_COURT_DWARFS_RELEASE.md`.

Original status: SPEC, written after a brainstorm in which the author approved every section below
marked APPROVED. Sections marked PROPOSED are the spec's own proposals, presented here for
the first time; the author reviews them in this document. Handoff:
`docs/sessions/HANDOFF_20261004_IRON_COURT_DWARFS_DESIGN.md`. Previews:
`Modding Files/source/iron_court_preview/dwf_*`.

## 1. Goal

`derpy_iron_court.pack` gives a court to **Dwarf** factions as well as Chaos Dwarf ones, in the
same pack. The Chaos Dwarf court does not change. A Dwarf court runs the same machinery with
Dwarf names, effects, art and seat layout, and adds two Dwarf-only mechanics: **grudges** inside
the court and the court's reading of CA's **Book of Grudges**.

Success: a Dwarf campaign (any of the six majors or the minors) opens a court that reads as
Dwarf on every tab, plays by the same rules plus kinship and grudges, never shows a Chaos Dwarf
word, picture or effect, and leaves every Chaos Dwarf behaviour, save and check exactly as it was.

## 2. Decisions (APPROVED)

- One pack, two races; the race comes from the faction's subculture: `wh3_dlc23_sc_chd_chaos_dwarfs`
  or `wh_main_sc_dwf_dwarfs` (culture `wh_main_dwf_dwarfs`).
- Same skeleton: 9 parties, 14 offices, 6 governments, 4 law categories x 5, the same intrigue
  moves. Dwarf office tiers are **2/4/4/4**.
- Growth effects are allowed for Dwarfs (banned only for Chaos Dwarfs).
- No Dwarf name may contain "Guild" or equal a Great Guilds Dwarf name (Merchant Clans,
  Engineers' Guild, Hammerers, Rangers, Miners' Guild, Grudge-Settlers).
- Every UI piece is previewed and approved before it is built (author's rule).

### 2.1 Parties (slot -> Dwarf)

crown -> **The Throne-Sworn**; temple -> **The Ancestor Priesthood**; forge -> **The
Forgewrights**; chain -> **The Deepdelvers**; legion -> **The Clan Warriors**; ledger -> **The
Reckoners**; tower -> **The Runesmiths**; road -> **The Underway Wardens**; hearth -> **The Hearth
Clans**. No Slayer party.

### 2.2 Offices (affinity unchanged)

| Tier | Office | Party |
|---|---|---|
| I | High Priest of the Ancestors | temple |
| I | Master Forgewright | forge |
| II | Keeper of the Reckoning | ledger |
| II | Warden of the Gate | legion |
| II | Keeper of the Grudge-Book | tower |
| II | Warden of the Underway | road |
| III | Overseer of the Mines | chain |
| III | Master of the Delvings | chain |
| III | Master of the Stonecutters | forge |
| III | Thane of the Muster | legion |
| IV | Brewmaster of the Hold | hearth |
| IV | Steward of the Holdfarms | hearth |
| IV | Keeper of the Lore | tower |
| IV | Keeper of the Clan Banners | legion |

### 2.3 Governments

conclave -> **The Council of Elders**, priest -> **The Ancestors' Writ**, forge -> **The
Forge-Throne**, legion -> **The War-King**, convoy -> **The Reckoning-Throne** (each keeps its
slot's rule). chain -> **The Iron Law**, rule CHANGED: Swear on the Ancestors, Oath on the Anvil
and Stand His Patron cost a third less, and a broken oath costs extra loyalty.

### 2.4 Intrigue moves (mechanics unchanged)

Gift of Gold, Question His Work, Whispers in the Halls, **Drive Him to the Slayer Oath** (the
murder slot: he leaves the court for good, his party knows who drove him), An Insult to the Clan,
Cast Out the Clan, Bar Them from the Hall, Recall Governors, Swear on the Ancestors, Stand His
Patron, Name Him Kinsman, Oath on the Anvil, Skim the Tally, Host a Feast, Hold Court in the Great
Hall, Walk the Holds, Send an Envoy, Send Diplomats; favours Send a Gift and Secure Loyalty.
Dwarf-only: **Pay the Weregild** (section 5).

### 2.5 Seat layout E, "The Great Hall"

A 5x4 grid at the court's card size. The throne plate at column 2, row 0 is the faction leader,
not an office. Two wings face each other down an aisle runner; doors at the foot above Fill
Empty Seats; (c0,r3) and (c4,r3) empty. Rank falls with distance from the throne:
Tier I (c1,r0)(c3,r0); II (c0,r0)(c4,r0)(c1,r1)(c3,r1); III (c0,r1)(c4,r1)(c1,r2)(c3,r2);
IV (c0,r2)(c4,r2)(c1,r3)(c3,r3). The ziggurat and its title are Chaos Dwarf only.

### 2.6 Skin

CA's Book of Grudges kit, `ui2.pack` `ui/skins/default/dlc25_book_of_grudges/`: blue ribbon tabs
(`tab_button_unit_pack_active`), the selected tab gold (`tab_button_legendary_grudges_selected`),
card frames `book_of_grudges_confederation_frame` (red-ink knotwork), the throne's Dwarf face
`book_of_grudges_unit_pack_decor` inked gold, CA rune glyphs `rune_N_panel` on the runner and
doors, backdrop CA's `ui/loading_ui/load_images/campaign_dwarfs1.png` dimmed like the court's.
Panel title design **A "Lintel"** (dark stone bar, gold double rule, `..._legendary_grudges_decor_2`
gold-inked at its left end); section headings **B "Knot rule"** (`..._confederation_decor_2`
under the words, `decor_units_header` marks).

**Nothing stretched**: every textured plate is BAKED to size by the generator - end caps and
corners at native scale, ribbon middles MIRROR-tiled (CA's ribbon paper does not tile; a straight
repeat seams), the frame's straight runs tiled and its top ornament (source columns 200-322)
whole. The engine then only scales the panel uniformly with `ICUI.apply_scale`, which keeps
proportions.

**Wording is per faction, at runtime**: "The Council of (faction)", "The Throne of (faction)"
over the faction leader's name, section heading "The Great Hall". Never one karak's name.

## 3. Factions

Verified out of `db.pack` (`factions_tables` v6, `frontend_faction_leaders`, `agent_subtypes`):

| Faction | Name | Leader | Start government (PROPOSED; inference) |
|---|---|---|---|
| `wh_main_dwf_dwarfs` | Karaz-a-Karak | Thorgrim Grudgebearer | The Ancestors' Writ (the Book's keeper) |
| `wh_main_dwf_karak_kadrin` | Karak Kadrin | Ungrim Ironfist | The War-King (the Slayer King) |
| `wh_main_dwf_karak_izor` | Clan Angrund | Belegar Ironhammer | The Iron Law (an oath to retake Eight Peaks) |
| `wh3_main_dwf_the_ancestral_throng` | The Ancestral Throng | Grombrindal | The Ancestors' Writ |
| `wh2_dlc17_dwf_thorek_ironbrow` | Ironbrow's Expedition | Thorek Ironbrow | The Council of Elders (a Runelord's council) |
| `wh3_dlc25_dwf_malakai` | Masters of Innovation | Malakai Makaisson | The Forge-Throne |
| `wh_main_dwf_barak_varr` | Barak Varr | (minor) | The Reckoning-Throne (the sea-port of trade) |
| `wh_main_dwf_zhufbar` | Zhufbar | (minor) | The Forge-Throne (the engineers' hold) |
| other Dwarf minors | | | The Council of Elders (default) |

**Origins (houses)** PROPOSED: the six majors and the eight Immortal Empires minors (Barak Varr,
Zhufbar, Kraka Drak, Karak Azorn, Karak Norn, Karak Hirn, Karak Azul, Karak Ziflin) as faction
origins, plus four non-faction origins: the Ranger clans, the Deeps, the Grey Mountains, the Black
Mountains. `wh2_dlc15_dwf_clan_helhein`, `wh2_main_dwf_karak_zorn`,
`wh2_main_dwf_greybeards_prospectors` and `wh2_main_dwf_spine_of_sotek_dwarfs` are in the DB but
unconfirmed on the map: an origin only if a faction interface for them answers in game.

**Names**: party leaders and members roll from CA's own `names_dwf_dwarfs` (129 male and 7
both-gender forenames, 182 family names); the court's own `NAME_HEADS`/`NAME_TAILS` get a Dwarf
set.

**Rebels**: `wh_main_dwf_dwarfs_qb2`-`qb4` and `wh_main_dwf_dwarfs_seperatists_qb1`-`qb4` (CA's
spelling), seven factions that no CA script touches. NOT `wh_main_dwf_dwarfs_qb1` (CA convoy
ambushes, Worldroots, Sayl) nor `wh3_dlc26_dwf_dwarfs_invasion` (Arbaal's challenge) nor
`wh_main_dwf_dwarf_rebels` (the engine's rebels). Their flags are CA's two shared crests; custom
crests are a later, separate question. Rebel generals, heroes and draft units are Dwarf keys,
verified in the build.

## 4. Effects (PROPOSED)

Rule: each Chaos Dwarf effect that means nothing to Dwarfs gets a Dwarf effect that vanilla
Dwarf content already uses, at the same tier magnitude and under the same sign rule
(`check_effect_signs.py`). Measured (2026-10-04, `db.pack` via `read_vanilla_db.py`):

- **Raw materials, armaments, workload, labour, Hobgoblin, Hell-Forge, Tower of Zharr, Conclave
  Influence, convoy and refinery effects do nothing for Dwarfs** (their pooled-resource factors
  are all `wh3_dlc23_chd_*`). So Send an Envoy's tasks become **control, Oathgold, growth,
  recruitment cost** (not raw materials).
- **Oathgold**: `wh2_dlc17_pooled_resource_oathgold_buildings_mod` (gain), and
  `wh3_dlc29_pooled_resource_oathgold_all_crafting_mod` / `wh2_dlc17_pooled_resource_oathgold_runecrafting_mod`
  (costs, lower is better).
- **Grudges**: no effect raises grudge-point gain (CA's script adds them directly). The Keeper of
  the Grudge-Book gets `wh3_dlc25_effect_dwf_book_of_grudges_increase_requirements` at a
  NEGATIVE value: each Age of Reckoning needs fewer Settled Grudges. CA's script reads it for
  human factions only and only when an Age's target is set, so it pays from the NEXT Age; the
  office text says so. `wh_main_effect_public_order_grudges` replaces the slaves control effect
  (its Control line is labelled as grudges).
- **Growth**: `wh_main_effect_province_growth_tech` / `_building` / `_commandment`.

Replacements, by slot (values are the court's tier-4 magnitudes, tier multipliers unchanged):

| Chaos Dwarf effect | Dwarf effect | Scope |
|---|---|---|
| armaments (offices, governor, government, envoy) | `oathgold_buildings_mod` | faction / region own unseen |
| raw-material efficiency | `oathgold_all_crafting_mod` (cost) | faction own unseen |
| workload (chain slot: Overseer of the Mines) | `technology_economy_gdp_mod_mining_dwarfs` | faction to region own unseen |
| (tower slot: Keeper of the Grudge-Book, whatever the Hand of the Tower carries) | grudge `increase_requirements` (cost, negative) | faction own unseen |
| post-battle labour | `force_all_campaign_post_battle_loot_mod` | faction own unseen |
| raw materials (quarries) | `technology_economy_gdp_mod_mining_dwarfs` | faction to region own unseen |
| Hobgoblin upkeep (ash fields) | `province_growth_tech` | faction to province own unseen |
| governor base workload | `province_growth_building` | faction to province own |
| slaves control (temple governor) | `public_order_grudges` | faction to province own |
| envoy raw / labour | `province_growth_commandment` / `recruitment_cost_all` (cost) | province own unseen |
| rush construction | `building_construction_cost_mod_all` | faction to region own unseen |
| convoys, tariffs, cargo | `economy_trade_tariff_mod` | faction own unseen |
| refinery | `technology_economy_gdp_mod_culture_dwarfs` | faction to region own unseen |
| Chaos Dwarf diplomacy | `wh_main_faction_political_diplomacy_mod_dwarfs` | faction own unseen |
| Hell-Forge cost / cap | grudge-settler recruitment cost / source | force own unseen / faction own |
| Chaos Dwarf artillery upkeep, damage, range | Dwarf war-machine upkeep, grudge-thrower missile damage, thunderer range | force own |
| infantry cost | `force_army_campaign_recruitment_cost_infantry` | force own unseen |
| Lore law malus `character_stat_miscast` | replaced: Dwarfs have no casters, so it costs nothing | - |

UNVERIFIED and checked in the build before use (dropped if no vanilla row confirms the scope):
the Dwarf melee-infantry rank and leadership effects, the Dwarf xp-against-Chaos-Dwarfs effect,
any Dwarf faction-scope corruption effect. Every effect row is read back by
`check_effect_signs.py` and `check_effect_bundle_loc.py` as today.

## 5. Grudges inside the court (APPROVED)

- Dwarf courts only. A wrong does its usual one-off loyalty hit **and** writes a grudge into the
  wronged party's book: **-1 loyalty per turn per grudge, never fading, at most 4 per party**.
  Each is its own line in the party's loyalty breakdown ("Grudge: Cast Out, turn 34") and the
  Record logs it written and settled.
- Written by: their man driven to the Slayer Oath; Cast Out the Clan, An Insult to the Clan or
  Bar Them from the Hall aimed at them; recalling their governors; dismissing their man before
  his term; an oath with them that breaks; refusing a demand they made; and (section 6) peace,
  trade or alliance with a faction the Book names above 1,000.
- Settled by **Pay the Weregild** (new Bonds move: gold, settles that party's oldest grudge,
  small loyalty gain) or by appointing their man to an office their party claims (settles one).
- **Kinship**: "Kin of the Karak" +1 loyalty per turn for every party; the secession countdown
  runs x1.5 (a race layer in `IC.tune`, below the government layer).
- AI Dwarf courts pay weregild in their rotation when their gold allows.
- Save: a per-house grudge list in a new field; old saves read it as empty.

## 6. The Book of Grudges (APPROVED)

- Each turn, for a Dwarf court, sum CA's grudge points on every met faction's armies and
  settlements (`wh3_dlc25_dwf_grudge_points_enemy_armies` / `_enemy_settlements`, read through
  `pooled_resource_manager():resource(key)` as CA's own `wh3_campaign_grudges.lua` does). The
  Court tab shows **"The Book names:"** with the top three.
- Crossing **500 / 1,000 / 2,000** applies `cm:apply_dilemma_diplomatic_bonus(own, them,
  -1 / -2 / -3)` ONCE per band, never reversed (CA doc entry checked: -6..+6, "as if it had come
  from a dilemma"). Bands crossed are saved per faction pair.
- Peace, trade or alliance with a faction above 1,000 writes a grudge in the Clan Warriors' and
  the Ancestor Priesthood's books.
- A rise in the faction's own `wh3_dlc25_dwf_grudge_points` (CA awards them on settling a grudge)
  is a **deed** for the Clan Warriors and the Ancestor Priesthood.
- OUT: reacting to CA's 15-turn Age of Reckoning score - it lives in CA's saved values with no
  event; added only if the build finds a readable signal.

## 7. Laws (PROPOSED)

Same 4 x 5 board, the first option of each category is its start and has no effects, every other
option a boon and a malus as now, with the effect swaps of section 4.

| Category | Start | Options (pro / con party) |
|---|---|---|
| **Craft** (replaces Labour) | The Old Ways | Deep Seams - mining income (chain / hearth); Hearth and Holdfarm - growth (hearth / chain); The Master's Mark - Oathgold crafting cheaper (forge / hearth); Raise the Halls - construction cheaper (legion / ledger) |
| **Tribute** | The King's Tithe | Open Underways - trade (road / crown); The Reckoners' Tariff (ledger / road); The Oathgold Hoard - Oathgold (forge / road); Hold Charters - Dwarf culture income (road / legion) |
| **Ancestors** (Worship) | The Ancestors' Rites | Valaya's Hearth - control from grudges and growth (temple / tower); Rune-Lore - runecrafting cheaper (tower / temple); The Lore of the Book - research (tower / hearth); The Anvil's Licence - crafting cheaper (forge / temple) |
| **War** | The Muster | Grudge Settlers - grudge-settler cost and cap (legion / ledger); Batteries of the Hold - war-machine upkeep and damage (forge / legion); Clan Hosts - infantry cheaper (legion / forge); Thunder and Iron - thunderer range (forge / hearth) |

## 8. Deeds (PROPOSED)

| Deed | Dwarf party | Event |
|---|---|---|
| battle | Clan Warriors | `CharacterCompletedBattle` (as now) |
| grudge settled | Clan Warriors + Ancestor Priesthood | the faction's `wh3_dlc25_dwf_grudge_points` rises (`PooledResourceChanged`) |
| temple | Ancestor Priesthood | `BuildingCompleted` on a Dwarf temple chain (keys verified in the build) |
| research | Runesmiths | `ResearchCompleted` (as now) |
| raze, slaves, convoy, Hell-Forge, Tower rite | none | Chaos Dwarf only |

A deed whose event cannot be verified in the build is dropped, not guessed.

## 9. Architecture

From the code map (2026-10-04), smallest change that holds:

1. **`IC.RACES`** with `chd` and `dwf` entries; the Chaos Dwarf tables stay where and as they are
   (same names, same column-0 closers, so every scraper and the harness's 304 references still
   match) and `IC.RACES.chd` points at them. The Dwarf tables live in a new
   `zzz_derpy_iron_court_dwarf.lua`, loaded after the model and before the parties file.
   `build_race(r)` derives `TIERS`, `TIER_SEATS`, `PARTY_OF_BG`, `MAX_SEATS` per race.
2. **Accessors**: `IC.race_of(faction)` (subculture -> race or nil), `IC.has_court` replaces
   `IC.is_chd` at its ~9 sites, `IC.R(faction_key)` (cached, unsaved). `IC.tune(fk, key)` gains the
   race layer under the government layer (kinship secession).
3. **~190 reading sites** switch from `IC.X` to the race table of the faction in hand. Load-time
   derivations size for the larger race. Key-only helpers (`office_by_slug`, `law_opt`,
   `rolled_name`, `is_party`) take a race.
4. **Keys get a race segment for Dwarfs**: `derpy_ic_office_dwf_<slug>`, `derpy_ic_law_dwf_...`,
   traits likewise, in Python `bundle_key(kind, slug, race)` and the Lua mirrors. Chaos Dwarf keys
   do not change (saves and loc unchanged).
5. **Save**: race is never saved (derived from subculture), so no migration; Dwarf-only data
   (grudges, Book bands) in new fields, read as empty by old saves.
6. **UI**: the panel is created per open, so the skin is a runtime pass - `R.art` holds the tab,
   backdrop, frame, heading and title paths, applied with `SetImagePath`; separate `.twui.xml`
   only where a layer's geometry differs (via `ICUI.path()`'s suffix, as `_compact` works). The
   Dwarf card grid is `R.layout = "grid"` with its cells; `ICUI.BASE.CARD_XY` is set from the race
   before `apply_scale`; the throne plate is one new component. New Dwarf art must be listed in
   `gen_ic_ui.art_paths()` or `write_plates()` prunes it.
7. **Python**: `RACES` in `gen_iron_court.py` / `gen_ic_ui.py`; `CARD_GRID`, `ziggurat_*`,
   `ic_zig_bg`, `ic_off_title` become functions of the race (the Dwarf grid has no ziggurat);
   `TIER_SEATS` stops being hard-coded; scraper regexes take the table prefix; every check runs
   per race.
8. **MCT**: one new switch, "Dwarf courts" (on). AI Dwarf courts follow the existing AI-courts
   switch.

## 10. Testing

- The harness loads the Dwarf file and runs its fixture set once per race (its `make_faction`
  already takes a subculture), plus Dwarf-only checks: grudge written/settled/capped, weregild,
  kinship term, secession x1.5, Book band fires once and never twice, peace with a named faction
  writes a grudge, no Chaos Dwarf word in any Dwarf string.
- `mutate_iron_court.py` gains Dwarf mutants (the guard forgotten, the cap removed, the band fired
  every turn).
- `gen_ic_ui.py` checks (text fit 20k, contrast, crossings) run for both races; contrast measured
  per cell against the Dwarf backdrop and on the gold and blue ribbons (4.5:1).
- A check that no Dwarf party name equals a Great Guilds Dwarf name.
- `preview_iron_court.py` draws every tab for a Dwarf court (demo faction Karak Kadrin); each tab
  is shown to the author and approved before it ships.
- In game: one Dwarf campaign and one Chaos Dwarf campaign, opener anchored on the Dwarf top bar
  (it has the grudge bar), a Book band firing, a grudge written and settled.

## 11. Phases

Each phase gets its own plan and is deployed and checked before the next.

1. **Race plumbing, Chaos Dwarf only** - `IC.RACES`, accessors, keys, Python `RACES`. Zero
   behaviour change: harness 974 green, every generator check unchanged, the pack's Chaos Dwarf
   rows byte-identical.
2. **Dwarf content** - tables, names, loc, bundles, effects, rebels, start governments; Dwarf
   courts run headless in the harness.
3. **Dwarf UI** - layout E, skin, title, baked plates; previews of every tab approved.
4. **Grudges inside the court** - section 5.
5. **The Book of Grudges** - section 6.
6. **Release pass** - mutation run, contrast, in-game checks, patch notes, repo sync.

## 12. Out of scope

Custom rebel crests for the Dwarf rebels; reacting to the Age of Reckoning score; any race other
than Chaos Dwarfs and Dwarfs; changing the Chaos Dwarf court.
