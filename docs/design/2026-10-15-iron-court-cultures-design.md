# Iron Court: cultures, design (2026-10-15)

Status: built and copied to data/ (see docs/superpowers/plans/2026-10-15-iron-court-cultures.md). Nothing in this
file has been run in game until the plan's Task 10 checklist is ticked. Section 12 lists what is still open.

Replaces the rolled "place" origin traits with a culture trait that decides how well a lord governs and
which party he sits in. Touches both races (Chaos Dwarf and Dwarf), the governor bundles, the law vote and
the governor picker.

---

## 1. What the author asked for

From the request:

> in the iron court mod, i want to add culture, scrap the traits where they are born and use a culture
> system. The culture traits will be given to them at spawn or at the start of the campaign without any
> event panel. Culture dictates their ability to Govern, for an example, a lord thats born in the industry
> district will have benefits of factory buffs. Culture should also define each party composition. provided
> md file should is a basis but not the truth since it doesnt have any context

Later in the conversation the author added three rulings:

- Immortal Empires regions come out. Only the divided regions of the Old World mod (TOW, by ChaosRobie)
  are used, because the Plain of Zharr "encompasses too many things".
- Karak Kadrin is a Slayer hold.
- The scope is the core plus home and foreign provinces plus culture stances on laws.

The source document is `regional_culture_design_document.md`, supplied in the conversation and not stored
in the workspace. Section 13 says what became of each part of it.

### Success

The work is done when all of these hold in a running campaign:

1. Every lord in every court carries one culture trait, stamped with no event card.
2. A governor's province bonuses and penalties come from his culture, not from his party.
3. A governor in a province his culture calls home gets stronger boons. In another culture's home he pays
   a public order penalty. Anywhere else he governs as usual.
4. A party's membership is a mix of cultures, and the mix follows the table in section 4.
5. A man votes on a law with his culture's line where it has one, and a party's loyalty swing follows the
   mix of its men.
6. An old save loads, converts its lords quietly, and keeps every lord's party.

---

## 2. Decisions taken on 2026-10-15

| Question | Answer | Why |
|---|---|---|
| How does culture relate to party? | Many-to-one. Each culture has a main party and a side party. A party is a mix of cultures. | One-to-one would make governing skill identical to today's party flavour under new names. |
| How is culture assigned? | Always rolled at spawn. No table from recruitment region to culture. | The author's choice. The roll still keeps every seated party populated (section 4.3). |
| Notification | Culture is always stamped quietly. | The author's brief. |
| Scope | Core, home and foreign province effects, culture stances on laws. Mirror of Spite is out. | The author ticked those three in the scope question. |
| Trade trait | Kept as the stored party seat, drawn from culture and party. | A culture feeds two parties, so the seat cannot be worked out from culture alone. Retiring the trait needs a second store and a migration of every saved lord's party. |
| Origins | The place origins are replaced. A conquered house's origin trait stays. | A house origin is what makes a confederated house a court member (`IC.present_houses`, `IC.prune_confed`, `IC.house_of_character`). |
| Home provinces | Old World map only. Immortal Empires, IEE and Realm of Chaos give no home or friction. | The author: use the divided regions TOW draws. |
| Effects | Vanilla effects at province scope only. | A new effect row has no engine behaviour behind it and would do nothing. |
| Cultures per race | Eight. | Eight rival parties per race, so every party can be one culture's main and another's side. |

---

## 3. What exists today

Read from the live files on 2026-10-15. Line numbers drift, so functions are named.

| Piece | Where | What it does now |
|---|---|---|
| Three traits per lord | `zzz_derpy_iron_court.lua` | Origin, background (a trade) and ambition. Stamped by `IC.stamp_court` at campaign start, by the `ic_born` listener on `CharacterCreated`, and by `IC.stamp_incoming` on confederation. |
| Origin | `IC.roll_origin`, `IC.stamp_origin`, `IC.ORIGINS` | A lord not confederated in gets one of eight places, picked uniformly at random. The generator comment says it has "no mechanical weight at all". |
| House origin | `IC.house_of_character`, `IC.present_houses`, `IC.prune_confed` | A confederated man carries his old faction as his origin. That faction becomes a court member and its men sit in it, not in a party. |
| Background (trade) | `IC.BACKGROUNDS`, `IC.background_for`, `IC.roll_background`, `IC.leaderless_bg` | Three trades per party, 27 per race. The trade seats the man: `IC.house_of_character` reads it. A man is dealt to the seated party with the fewest members (`IC.fewest`), after an empty leadership is filled. |
| Quiet stamping | `ic_born` | Starting lords and garrison captains are stamped quietly. A new recruit still shows two Trait Gained cards. |
| Governor flavour | `IC.apply_governor_bundles`, `IC.gov_bundle_house`, `PARTIES` in `gen_iron_court.py` | Each governor gets the base bundle, then one bundle for his party: one effect per party (Forge gives armaments, Chain gives labour, and so on). |
| Law vote | `IC.LAWS`, `IC.law_stance`, `IC.law_line`, `IC.law_tally`, `IC.law_win_price` | Each option lists the parties for it (`pro`) and against it (`con`). A man votes his party's line. The tally caches that line per party. |
| Legends | `IC.LORD_HISTORY` | Fixed origin and trade per legendary lord. |
| Dwarf side | `zzz_derpy_iron_court_dwarf.lua` | The same party slugs with Dwarf words. `DWF.ORIGINS` has 14 hold factions and four places (rangers, deeps, grey, black). |

---

## 4. The model

### 4.1 The culture trait

- One trait per man, a new trait family `cult` beside `house` (origin), `bg` (trade) and ambition.
- It has no effect of its own. It applies when its holder governs (section 5).
- Its text is built by the generator from the same table that builds the bundles, so the numbers on the
  trait and the numbers in the bundle cannot differ.
- A confederated man carries a house trait and a culture trait.
- New trait category `derpy_ic_cat_culture`. Key names are proposed and the plan may adjust them.

### 4.2 The eight cultures

The Chaos Dwarf slugs are the old place slugs, so a saved lord converts by slug (section 8). Three
display names change because the old names were too broad: the author asked for the divided Old World
regions, and the Plain of Zharr is one province on the Immortal Empires map.

| Slug | Culture | Archetype | Main party | Side party |
|---|---|---|---|---|
| `zharr` | Heart of Zharrduk (was Zharr-Naggrund) | Hierophant | temple | tower |
| `stump` | Foundry Districts (was Daemon's Stump) | Foundry Baron | forge | legion |
| `gorgoth` | Tower of Gorgoth | Labour Master | chain | ledger |
| `zornuzkul` | Zorn Uzkul | Infernal Warden | legion | road |
| `plain` | Market District (was Plain of Zharr) | Clerk | tower | chain |
| `mines` | Mines of Mingol | Deep-Hearth | hearth | forge |
| `wastes` | Howling Wastes | Pathfinder | road | ledger |
| `gash` | Gash Kadrak | Tribute-taker | ledger | legion |

Dwarf cultures are new. Their slugs `karaz`, `kadrin` and `barakvarr` match Dwarf house-origin slugs,
which is safe because the trait family is part of the key.

| Slug | Culture | Archetype | Main party | Side party |
|---|---|---|---|---|
| `karaz` | Karaz-a-Karak | Royal Traditionalist | temple | tower |
| `black` | The Black Holds (Zhufbar, Karak Hirn) | Guild Innovator | forge | ledger |
| `barakvarr` | Barak Varr | Merchant Lord | ledger | road |
| `kadrin` | Karak Kadrin | Slayer | legion | temple |
| `azul` | Karak Azul | Runesmith | tower | forge |
| `deeps` | The Deeps | Deep-Miner | chain | forge |
| `grey` | Grey Mountains | Hold-Keeper | hearth | legion |
| `passkeeps` | The Pass-Keeps | Pass-Warden | road | legion |

Where the archetypes come from. The Chaos Dwarf Hierophant, Foundry Baron, Labour Master and Infernal
Warden are the source document's four. The other four are named for the mod's existing place list. CA's
and TOW's loc support most of them:

| Culture | Text it rests on |
|---|---|
| Hierophant | "the Great Temple of Hashut" atop the Mingol-Zharr-Naggrund tower |
| Foundry Baron | "vast factory forges" and "broiling-hot machine shops of Zharr-Naggrund" |
| Labour Master | "The mining colony set up around the imposing Tower of Gorgoth" |
| Infernal Warden | the Black Fortress "border guards"; Uzkulak as "a heavily-garrisoned tomb" |
| Slayer | "Karak Kadrin - the Slayer Keep"; "the greatest Slayer Shrine ... to Grimnir" |
| Runesmith | Karak Azul "renowned for producing powerful weapons of unrivalled quality" |
| Guild Innovator | "Cannons were first made by the Dwarfs of Zhufbar"; Zhufbar's toolmakers and gyro hangars |
| Merchant Lord | Barak Varr, "the sea-gate of the Karaz Ankor" |
| Royal Traditionalist | Karaz-a-Karak's gold mines and the Master Rune of Spite in its gates |
| Deep-Miner | Kraka Drak "famous for its gemstone and silver mines"; Karak Eight Peaks' wealth "deep underground" |
| Hold-Keeper | Grey Mountain holds "struggling to keep their numbers up" |
| Pass-Warden | keeps "that stand guard over entrances to the Underway" and mountain passes |

Market District, Mines of Mingol, Howling Wastes and Gash Kadrak rest on place and district names only
(12.3). TOW's loc has names for its districts and no lore text.

### 4.3 The roll

For every lord who is not a legend and has no culture:

1. Pick the party exactly as today: a seated party with no leader first (`IC.leaderless_bg`), otherwise
   the seated party with the fewest men, ties rolled (`IC.fewest`). Both functions already choose the
   party before the trade, so the plan splits them at that point.
2. Pick the culture from those that list that party as main or side. The main culture gets 70% and the
   side cultures share 30%. A party with no side culture gives the main one 100%. The 70 is a Lua
   constant, `IC.TUNE.culture_main_pct`.
3. A man dealt to the Crown party has no feeding culture. He draws one of the eight uniformly.
4. Pick the trade from the party's trades as today. The one exception is the Dwarf Legion, which gets a
   fourth trade, Slayer, dealt to a Kadrin-born man seated in Legion (section 4.4).
5. Stamp culture and trade. The culture is always quiet. The trade keeps today's behaviour: a new
   recruit still shows its card.

`cm:random_number` is the only random source, as in the current deal, so the roll adds nothing new to
multiplayer.

Legends take a fixed culture from `IC.LORD_HISTORY`, the way they take a fixed origin and trade. The plan
proposes the assignments for the 17 Chaos Dwarf legends and the Dwarf ones, and the author reviews them
(12.2).

AI courts are stamped by the same path, with no interface.

### 4.4 Which cultures feed which party

Derived from the tables in 4.2. "(m)" marks the party's main culture and "(s)" a side culture.

| Party | Chaos Dwarf sources | Dwarf sources |
|---|---|---|
| temple | zharr (m) | karaz (m), kadrin (s) |
| tower | plain (m), zharr (s) | azul (m), karaz (s) |
| forge | stump (m), mines (s) | black (m), azul (s), deeps (s) |
| legion | zornuzkul (m), stump (s), gash (s) | kadrin (m), grey (s), passkeeps (s) |
| chain | gorgoth (m), plain (s) | deeps (m) |
| ledger | gash (m), gorgoth (s), wastes (s) | barakvarr (m), black (s) |
| road | wastes (m), zornuzkul (s) | passkeeps (m), barakvarr (s) |
| hearth | mines (m) | grey (m) |

Every party has exactly one main culture and at least one source. Chaos Dwarf Temple and Hearth, and
Dwarf Chain and Hearth, draw from one culture only.

The Slayer trade: the Dwarf Legion has Longbeard, Ironbreaker and Thane. A Slayer is none of them. The
design adds a fourth Legion trade, Slayer, as one trait row and one loc line on the Dwarf side. Slayers
renounce their holds, so Kadrin's side party is Temple (the Shrine of Grimnir) and not Hearth.

---

## 5. Governing

### 5.1 The effect pool

A bundle that does nothing is the failure this section guards against, so every pair below was read from
CA's `effect_bundles_to_effects_junctions` in the vanilla cache on 2026-10-15. There are 277 distinct
effects at `province_to_*` scopes. The pairs used are listed here. "Seen" is the range of values CA ships
for that exact pair. Effects at `*_factionwide` scopes are not used, because they would leave the province.

| Name in tables | Effect key | Scope | Seen | Better when |
|---|---|---|---|---|
| Wind of Magic | `wh3_main_effect_winds_of_magic_increase_chance_mod` | `province_to_region_own_unseen` | -30 to 30 | higher |
| Public order | `wh_main_effect_public_order_edict` | `province_to_province_own_unseen` | -6 to 10 | higher |
| Labour lost | `wh3_dlc23_pooled_resource_chd_increased_labour_loss` | `province_to_province_own_unseen` | 3 to 20 | lower |
| Armaments | `wh3_dlc23_pooled_resource_chd_armaments_modifier` | `province_to_province_own_unseen` | 10 | higher |
| Construction time | `wh3_main_effect_building_construction_time_add_mod_all` | `province_to_region_own` | -2, -1, 1 | lower |
| Labour cost of rushing builds | `wh3_dlc23_effect_rush_construction_slave_cost` | `province_to_region_own_unseen` | -10 | lower |
| Siege attrition | `wh_main_effect_force_army_campaign_siege_defend_attrition` | `province_to_force_own_provincewide_unseen` | -30 to -5 | lower |
| Leadership | `wh_main_effect_force_stat_leadership` | `province_to_force_own_provincewide` | 2 to 10 | higher |
| Income | `wh_main_effect_economy_gdp_mod_all` | `province_to_region_own_unseen` | -33 to 20 | higher |
| Construction cost | `wh_main_effect_building_construction_cost_mod` | `province_to_region_own` | -50 to 20 | lower |
| Recruitment cost | `wh_main_effect_force_all_campaign_recruitment_cost_all` | `province_to_force_own_provincewide` | -30 to 30 | lower |
| Replenishment (boon) | `wh_main_effect_force_all_campaign_replenishment_rate` | `province_to_province_own_unseen` | 1 to 5 | higher |
| Replenishment (drawback) | the same key | `province_to_force_own_provincewide` | -200 to 20 | higher |
| Army upkeep | `wh_main_effect_force_all_campaign_upkeep` | `province_to_force_own_provincewide` | -25 to -10 | lower |
| Movement range | `wh2_dlc09_effect_force_own_campaign_movement_range_province` | `province_to_force_own_provincewide_unseen` | 10 to 20 | higher |
| Ambush success | `wh_main_effect_force_army_campaign_ambush_attack_success_chance` | `province_to_force_own_provincewide_unseen` | 10 to 20 | higher |
| Post-battle loot | `wh_main_effect_force_all_campaign_post_battle_loot_mod` | `province_to_character_own_text` | 15 to 20 | higher |
| Sea trade income | `wh_main_effect_economy_gdp_mod_trade_sea` | `province_to_region_own_unseen` | 25 | higher |
| Research rate | `wh_main_effect_technology_research_rate_mod` | `province_to_faction_unseen` | 5 to 10 | higher |
| Melee defence | `wh_main_effect_force_stat_melee_defence` | `province_to_force_own_provincewide` | 5 | higher |
| Melee attack | `wh_main_effect_force_stat_melee_attack` | `province_to_force_own_provincewide` | 5 | higher |

Not available at province scope, so not used: Conclave Influence, Raid income, post-battle Labour, and
anything Oathgold except `wh2_dlc17_pooled_resource_oathgold_buildings_mod` (+10 at
`province_to_region_own_unseen`), which matters only to a faction that holds Oathgold.

### 5.2 What each culture gives

Numbers are the values written to the bundle. The generator takes a magnitude and an intent (boon or
drawback) and works the sign out from CA's good-or-bad flag, as `signed_value` does today. For the four
cultures the source document covers, the drawback is its main drawback for that region. The other four
are the author's to adjust.

Chaos Dwarf:

| Culture | Boons | Drawback |
|---|---|---|
| Heart of Zharrduk | Wind of Magic +20, Public order +3 | Labour lost +10 |
| Foundry Districts | Armaments +10, Construction time -1 | Public order -4 |
| Tower of Gorgoth | Labour lost -8, Labour cost of rushing builds -10 | Public order -4 |
| Zorn Uzkul | Siege attrition -20, Leadership +6 | Income -10 |
| Market District | Income +8, Construction cost -10 | Recruitment cost +10 |
| Mines of Mingol | Replenishment (boon) +4, Army upkeep -10 | Construction time +1 |
| Howling Wastes | Movement range +10, Ambush success +10 | Replenishment (drawback) -10 |
| Gash Kadrak | Post-battle loot +15, Income +6 | Public order -4 |

Dwarf:

| Culture | Boons | Drawback |
|---|---|---|
| Karaz-a-Karak | Income +8, Public order +3 | Construction time +1 |
| The Black Holds | Recruitment cost -10, Construction time -1 | Public order -4 |
| Barak Varr | Sea trade income +25, Income +6 | Recruitment cost +10 |
| Karak Kadrin | Melee attack +5, Replenishment (boon) +4 | Income -15 |
| Karak Azul | Research rate +5, Melee defence +5 | Construction cost +10 |
| The Deeps | Income +8, Construction cost -10 | Public order -3 |
| Grey Mountains | Siege attrition -20, Army upkeep -10 | Replenishment (drawback) -10 |
| The Pass-Keeps | Movement range +10, Ambush success +10 | Income -8 |

Choices worth reading again:

- The Hierophant's Conclave Influence from the source document has no province-scoped effect, so Wind of
  Magic carries that strength.
- The Labour Master's reduced slave decline is Labour lost -8. CA ships that pair only with positive
  values (12.5).
- Grey Mountains boons are siege and upkeep, and its drawback is slow replenishment, because the loc says
  those holds struggle to keep their numbers up.

### 5.3 Home, away and foreign

Three cases, decided by the governor's province key and his culture:

| Case | Test | Bundles applied |
|---|---|---|
| Home | The province is on his culture's home list. | The culture's home bundle: boons x1.5, drawback unchanged. |
| Foreign | The province is on another culture's home list and not on his. | The culture's away bundle, plus the shared friction bundle (Public order -4). |
| Away | The province is on no culture's list, or the map is not the Old World map. | The culture's away bundle. |

Home values round to the nearest whole number, halves rounding up. The generator check lists any home
value outside the range CA ships for its pair (for example Replenishment +4 becomes +6 against a seen
maximum of 5, and Post-battle loot +15 becomes +23 against 20). The plan decides, pair by pair, whether
to cap the value or keep it.

Bundles are province-kind (the Envoy bundles are the model), applied with
`cm:apply_effect_bundle_to_faction_province` to a region of the province, as the party flavour is now.
Proposed keys: `gov_cult` and `gov_cult_home` per culture, and one `gov_friction` per race.

`IC.apply_governor_bundles` changes in one place. After `IC.apply_gov_base` it looks up the governor's
culture and picks one of the three cases, where today it applies `IC.gov_bundle_house` for his party. The
nine party bundles stay in the pack unused, so a bundle an old save still wears can be taken off.

Culture bundles ride on `IC.apply_governor_bundles`, so whatever gates governors gates them. There is no
new MCT setting.

---

## 6. Home provinces (Old World map)

Every key is `cr_oldworld_province_` plus the suffix shown. They were read from
`region_to_province_junctions_tables` in `!cr_oldworld_campaign.pack` (Workshop id 3081800026): 1,317
regions in 522 provinces. `!cr_oldworld_campaign_devastate.pack` (3813271876) ships the same map under
another campaign row with the same keys. The display names are from the pack's own
`!cr_oldworld_provinces__.loc`.

Chaos Dwarf:

| Culture | Province (key suffix) |
|---|---|
| Heart of Zharrduk | Heart of Zharrduk (`heart_of_zharrduk`), Skull Cliffs (`skull_cliffs`) |
| Foundry Districts | Foundry District (`foundry_district`), Manufactory District (`manufactory_district`), River District (`river_district`), Daemon's Ruin (`daemons_ruin`), Foundry of Rage (`foundry_of_rage`), Putrid Stump (`putrid_stump`) |
| Tower of Gorgoth | Pits District (`pits_district`), Mount Azgorh (`mount_azgorh`), The Crossroads (`the_crossroads`) |
| Zorn Uzkul | Gate District (`gate_district`), Zorn Uzkul (`zorn_uzkul`), Death's Side (`deaths_side`), Lower River Ruin (`river_ruin_lower`), Upper River Ruin (`river_ruin_upper`), Skull Road (`skull_road`) |
| Market District | Market District (`market_district`) |
| Mines of Mingol | Zandri Road (`zandri_road`), Belyerovota (`belyerovota`), West Death Pass (`west_death_pass`) |
| Howling Wastes | Howling District (`howling_district`), Causeway of Zharr (`causeway_of_zharr`), North Howling Wastes (`howling_wastes_north`), South Howling Wastes (`howling_wastes_south`), The Black Field (`the_black_field`) |
| Gash Kadrak | Gash Kadrak (`gash_kadrak`) |

Left neutral: Falls District, Blasted District, Desolation of Azgorh and the orc-held Darklands provinces.

Dwarf:

| Culture | Province (key suffix) |
|---|---|
| Karaz-a-Karak | Agrildrin (`agrildrin`), Middle Mountains (`middle_mountains`) |
| The Black Holds | Black Water (`north_black_water`), Black Mountains (`black_mountains`) |
| Barak Varr | Varenka Hills (`varenka_hills`) |
| Karak Kadrin | Peak Pass (`peak_pass`), Grim Kadrin (`grim_kadrin`) |
| Karak Azul | Iron Peaks (`karak_azul`) |
| The Deeps | Shattered Teeth (`shattered_teeth`), The Vaults (`the_vaults`), Delved Heights (`delved_heights`), East Gianthome Mountains (`gianthome_mountains`), Dragon Crag (`karak_azgal`) |
| Grey Mountains | North Grey Mountains (`north_grey_mountains`), South Grey Mountains (`south_grey_mountains`), Crooked Corridor (`crooked_corridor`), West Gate (`west_gate`) |
| The Pass-Keeps | Black Blood Pass (`black_blood_pass`), Black Fire Pass (`black_fire_pass`), High Pass (`high_pass`), Mondidier Pass (`mondidier_pass`), Eagle's Peak (`eagles_peak`), West Gianthome Mountains (`west_gianthome_mountains`), East Helspire Mountains (`helspire_mounts_east`) |

`faction:provinces()` already gives province keys, and the keys are unique per map family, so the model
needs no check for which campaign is running. A province key not in the table is neutral.

On the Immortal Empires map, IEE (which adds 79 provinces under `cr_combi_province_*`) and Realm of Chaos,
no province matches, so every governor is in the "away" case. The boons and drawback still apply.

---

## 7. Laws

### 7.1 Data

Each option in `IC.LAWS` and `DWF.LAWS` keeps its `pro` and `con` party lists and gains `cpro` and `ccon`
culture lists. Only the four non-start options in each category carry stances, as now.

Chaos Dwarf (option names as the player sees them):

| Culture | For | Against |
|---|---|---|
| Heart of Zharrduk | The Fires Fed, The Lore Taught | The Furnace Quota, The Kept Stock |
| Foundry Districts | The Furnace Quota, The Hell-Forge Unbound | The Fires Fed |
| Tower of Gorgoth | The Lash, Open Roads | The Kept Stock |
| Zorn Uzkul | Standing Legions, The Old Grudge | The Ledger's Tariff, Seats Bought in the Tower |
| Market District | Seats Bought in the Tower, The Overseers' Charter | The Lash |
| Mines of Mingol | The Mines Before All, The Kept Stock | The Ash Harvest |
| Howling Wastes | Open Roads, The Ledger's Tariff | The Mines Before All |
| Gash Kadrak | The Ash Harvest, The Old Grudge | Open Roads |

Dwarf:

| Culture | For | Against |
|---|---|---|
| Karaz-a-Karak | Valaya's Hearth, Hold Charters | Thunder and Iron |
| The Black Holds | Batteries of the Hold, Thunder and Iron | The Master's Mark |
| Barak Varr | Open Underways, Hold Charters | The Oathgold Hoard |
| Karak Kadrin | Grudge Settlers, Clan Hosts | The Reckoners' Tariff |
| Karak Azul | Rune-Lore, The Master's Mark | Thunder and Iron |
| The Deeps | Deep Seams, The Oathgold Hoard | Hearth and Holdfarm |
| Grey Mountains | Hearth and Holdfarm, Clan Hosts | Deep Seams |
| The Pass-Keeps | Open Underways, Clan Hosts | The Oathgold Hoard |

### 7.2 Behaviour

- A man's line is his culture's stance on the option when it has one, and his party's line otherwise.
  The loyalty fallback in `IC.law_line` is unchanged for men with no stance either way.
- `IC.law_tally` caches one line per party. It now caches per party and culture.
- `IC.law_win_price` doubles the price when the man has a stance that differs from the Crown's. Today
  that stance is his party's. It becomes his own line, so a Slayer in the Temple party is priced by the
  Slayer's stance.
- On a pass, a party's loyalty moves by 5 times (aye influence share minus nay influence share) among its
  voting men. A party that votes as one still moves 5. A split party moves less. The 2026-10-02 laws
  spec (section 3.5) has it moving a flat 5 up for a party that is for the option and 5 down for a party
  that is against it.
- The Crown's men vote as the player chooses, as now.

---

## 8. Saves and conversion

- A lord holding a place origin trait and no culture trait is converted the next time the court is
  stamped. Chaos Dwarf place slugs map to the culture with the same slug. The four Dwarf places map as
  rangers to `passkeeps`, deeps to `deeps`, grey to `grey` and black to `black`. The old trait is
  removed, the culture added, both quietly.
- A lord with neither gets a culture rolled for his current party (section 4.3).
- Parties and trades never change in conversion. A converted lord's culture may not feed his party,
  because the old place was rolled with no link to party. Nothing in the model depends on the two
  agreeing, so this is accepted (12.1).
- The eight Chaos Dwarf and four Dwarf place trait rows stay in the pack so the removal resolves. They
  are never granted again.
- The nine `gov_house` bundles stay in the pack for the same reason.
- A save made before this change loads on the new rules with no migration step beyond the above.

---

## 9. Interface

No new panel. Three touch points:

1. The culture trait on the character panel, with the numbers drawn from the same table as the bundle.
2. One line on each candidate card in the governor picker: the culture, and whether the province is home,
   away or foreign for him, with the figures.
3. One paragraph on the Help page.

The picker is in `zzz_derpy_iron_court_ui.lua`. The plan reads it before choosing where the line goes.
Both races are drawn with `tools/preview_iron_court.py` at 1600 and 1920 before the change is called
done.

---

## 10. Checks and tests

Generator (`tools/gen_iron_court.py --check`):

- Every (effect, scope) pair in section 5.1 exists in CA's junction table, and its good-or-bad flag
  matches what the generator assumes.
- Home values outside the range CA ships for their pair are listed.
- Every province key in section 6 exists in `region_to_province_junctions_tables` of the Old World pack.
- Every party has exactly one main culture and at least one feeding culture.
- No culture is both for and against one option, and every option named exists.
- Trait and bundle text is built from the table, and a mismatch fails.

Harness (`tools/_iron_court_harness.lua`):

- Over a large number of rolls, parties stay balanced by the fewest-men rule and the main/side split
  lands near 70/30.
- Stamping a culture raises no feed event.
- A saved lord with a place origin converts and keeps his party.
- The three governor cases pick the right bundle, including a province in no list and a map with no keys.
- A culture stance beats a party stance in a vote, and a party's loyalty swing follows its mix.

Mutation (`tools/mutate_iron_court.py`): the new rules get mutants, each aimed at a plausible mistake
(home and foreign swapped, party line used where culture applies, a missed rounding, a missing quiet
flag). The runner restores the source and the generated files, per the existing rule.

Release (`tools/check_ic_release.py --pack`): the saved pack is read back and compared with the
generator's rows and loc.

Files expected to change: `tools/gen_iron_court.py`, `tools/import_iron_court.py`,
`tools/gen_ic_ui.py` (if the picker line needs art), `tools/_iron_court_harness.lua`,
`tools/mutate_iron_court.py`, `tools/preview_iron_court.py`, `zzz_derpy_iron_court.lua`,
`zzz_derpy_iron_court_dwarf.lua`, `zzz_derpy_iron_court_ui.lua`.

---

## 11. Out of scope

- Mirror of Spite (the source document's section 5).
- Recruiting in a district to tilt the roll. The author chose a plain roll. The Old World districts make
  it cheap to add later.
- Home provinces on Immortal Empires, IEE and Realm of Chaos.
- Scaling culture effects with the governor's rank. The party bundles did not scale either.
- An MCT switch for cultures.

---

## 12. Open items and risks

1. **Converted lords.** A converted lord's place may disagree with his party. The alternative is to
   re-roll every lord's culture for his party, which loses the birthplace the player has seen. The design
   keeps the place. The author can overrule.
2. **Legend cultures.** The plan proposes a culture for each legendary lord for the author to review.
   Nothing is assigned yet.
3. **Readings from names.** Market District as Clerks, Mines of Mingol as Deep-Hearth, Howling Wastes as
   Pathfinders and Gash Kadrak as Tribute-takers come from place names and CA's party trades (the Tower
   party has a "Clerk of the Tower", the Chain party a "Hobgoblin Wrangler"). Skull Cliffs under Heart of
   Zharrduk is a guess from the name of the Crater of the Hammer of Hashut. TOW's loc has no lore for its
   districts.
4. **Confederated lords.** Proposed and not confirmed: a lord from a conquered hold takes that hold's
   culture, so a Karak Kadrin lord is a Slayer. Dwarf holds map almost one to one, and a few Chaos Dwarf
   houses do too (Uzkulak, the Conclave, Azgorh). Without this rule they roll like everyone else. The plan
   needs the author's answer before it writes the table.
5. **Labour lost -8.** CA ships `chd_increased_labour_loss` only with positive values. A negative value
   is mechanically allowed and has not been seen in game. It is the only boon with a sign CA never uses.
   Check it in game.
6. **Research rate.** The only research pair CA ships at province scope reaches the whole faction while
   the governor serves. Two Karak Azul governors stack.
7. **Post-battle loot.** The scope is `province_to_character_own_text`. Whether it reaches only the
   governor or every own character in the province is unverified.
8. **Wind of Magic.** The Hierophant's boon is a vanilla effect that has not been checked on a Chaos
   Dwarf province in game.
9. **Out-of-range home values.** Section 5.3 lists them. Each needs a decision in the plan.
10. **Quiet trade card.** The author asked for culture to be quiet. A new recruit still shows a Trait
    Gained card for his trade. Say if the trade should be quiet too. The cost is losing the only
    notice of which party a recruit joined.
11. **Slayer trade.** One new Dwarf Legion trade (section 4.4). Say if you would rather reuse an
    existing trade.

---

## 13. Where the source document went

| Source document | Disposition |
|---|---|
| Chaos Dwarf regions 1 to 4 (Tower of Zharr, Smelting Basin, Gorgoth Pits, Ash Border Bastions) | Used as four of the eight Chaos Dwarf cultures. Four more are added from the mod's place list. |
| Dwarf regions 1 to 4 (Karaz-a-Karak, Zhufbar and Karak Hirn, Barak Varr, Karak Kadrin) | Used as four of the eight Dwarf cultures. Karak Kadrin's archetype is Slayer, not Pass-Warden. Four more are added. |
| Governor strengths and drawbacks | Used, limited to effects CA ships at province scope (section 5). |
| Court and law stance, favoured and opposed laws | Used as culture stances on the existing laws (section 7). |
| "Provincial Resonance" and administrative friction | Used as home and foreign bundles (section 5.3), on the Old World map. |
| "Dynamic Court Demographics" | Already provided by parties: party share follows who holds seats. No new system. |
| Tax strikes, bribery demands, provincial crises from opposed laws | Not built. The loyalty swing in section 7.2 is the whole response. |
| Mirror of Spite (section 5) | Out of scope. |
