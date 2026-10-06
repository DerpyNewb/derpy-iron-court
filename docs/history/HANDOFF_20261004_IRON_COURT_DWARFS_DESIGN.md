# Iron Court - upload check, GitHub push, and Dwarf support design started (2026-10-04)

Continues `HANDOFF_20261004_IRON_COURT_UI_POLISH.md`. Nothing was built or deployed this session;
the pack is still `F4C63911`. The Dwarf work is in BRAINSTORMING (architectural path): decisions
below are the author's, the spec is not written yet.

## 1. Upload check ("is the Iron Court mod ready to upload?")

Answer given: the pack is technically ready, the release is not.

Verified 2026-10-04 ~11:30:
- data/ == Modpacks == MD5 `f4c6391183a7aa76309558640068318b` (10,914,962 bytes).
- No Iron Court source newer than the pack (`find -newer` over tools, source/iron_court, pack).
- Harness `ok (974 checks)`; `gen_ic_ui.py --check` ok (28 files, 1054 components); luac on the
  five court Lua files; `check_lua_literal_left` 0; `check_effect_bundle_loc` 73 bundles / 1116
  loc / 0 findings (needs an ABSOLUTE pack path - a relative one fails inside RPFM's open);
  `read_pack_index` 1818 paths, 0 with uppercase. `check_lua_api` flags one call, in
  `ai_test_tower_of_zharr.lua`, not the court.

Not ready: no Workshop item exists (no title, description or preview image drafted anywhere);
`PATCH_NOTES_20260925_IRON_COURT.md` stops at `D3712F85`; laws, most of governments/deeds, civil
missions and the 10-04 polish are unseen in game; the known-unfixed list in the UI_POLISH
handoff section 1 stands. After a first publish, the `data/` copy must move to
`Modding Files/Backup/` or the game sees two `derpy_iron_court.pack`.

## 2. GitHub push

- `sync_iron_court_repo.py` did not list today's handoff: added
  `HANDOFF_20261004_IRON_COURT_UI_POLISH.md` to its `docs/sessions` -> `docs/history` list.
- Synced 16 files, 0 drift after; CHANGELOG entry "2026-10-04 - build F4C63911" (covers
  E64B290E and 6DE3D85C) written in the repo.
- Pushed `c97f25b` (builds E64B290E to F4C63911) and `4440021` (history: record the push).
  Staged set checked for png/dds/pack/bin/loc/factions.tsv first: none.

## 3. Dwarf support - decisions so far (author)

- **Same pack.** `derpy_iron_court.pack` serves both Chaos Dwarfs and Dwarfs; the Chaos Dwarf
  court is unchanged.
- **Same skeleton**: 9 parties, 14 offices, 6 governments, 4 law categories x 5, with Dwarf
  names, icons and effects per slot.
- **Grudges: both readings.** (a) inside the court: a wronged party records a grudge that does
  not fade like loyalty does, until settled by a favour or a deed; (b) against other factions:
  read CA's Book of Grudges and let it drive party demands and loyalty.
- **Kinship loyalty** for Dwarfs (more loyal to fellow Dwarfs) - proposed as a standing
  `IC.loyalty_terms` entry plus rarer secession; not yet confirmed in detail.
- **Seat layout: E, "The Hall of the King"** (author 2026-10-04: "E looks good"). Not a
  pyramid: a 5x4 grid of the court's own card size; the THRONE OF THE KARAK plate at row 0,
  column 2 (the faction leader, not an office); the seats in two wings facing each other down a
  red aisle runner with pillars, the hall doors at the foot above Fill Empty Seats. Rank falls
  with distance from the throne:
  - Tier I: (c1,r0) (c3,r0)
  - Tier II: (c0,r0) (c4,r0) (c1,r1) (c3,r1)
  - Tier III: (c0,r1) (c4,r1) (c1,r2) (c3,r2)
  - Tier IV: (c0,r2) (c4,r2) (c1,r3) (c3,r3)
  - (c0,r3) and (c4,r3) empty: the hall narrows to its entrance.
- **Dwarf tiers are 2/4/4/4**, not 2/3/4/5 (symmetry). So `IC.OFFICES` becomes per race, and
  everything derived from `IC.TIER_SEATS` (card grid, ziggurat, header "14 seats in 4 tiers
  (2/3/4/5)") must read the race's.
- **Author's rule for this work: every UI piece gets a preview picture for approval before it is
  built.**

Mockups (throwaway; card text is the Chaos Dwarf court's): `Modding Files/source/iron_court_preview/`
`dwf_seats_A_deep_hold.png` (inverted ziggurat), `_B_hold_gate`, `_C_mountain` (all rejected:
still pyramids), `_D_great_stair` (stair-shaft cross-section, rejected), `_E_throne_hall`
(chosen). Scripts beside them: `dwf_seat_mockups.py` (A-C, and the helpers: Dwarf backdrop,
lifting UI off the render by diffing it against `panel_bg.png`) and `dwf_seat_mockups2.py`
(D, E). They read `.skilltree_cache/ui_preview/ic_offices.png`, so run
`py tools/preview_iron_court.py` first.

## 3b. Decisions approved after the handoff was first written (author: "continue" to each)

- **Growth effects are allowed for Dwarf courts** (author 2026-10-04: "Growth effect is already
  applicable to Dwarfs, just not the chaos dwarfs"). The CHD court's no-growth rule is per race.
- **No "Guild" in any Dwarf name** - the Great Guilds' Dwarf layer already uses Merchant Clans,
  Engineers' Guild, Hammerers, Rangers, Miners' Guild, Grudge-Settlers. The spec carries a check
  that no Dwarf party name equals a Great Guilds Dwarf name.
- **Parties** (slot -> Dwarf): crown -> The Throne-Sworn; temple -> The Ancestor Priesthood;
  forge -> The Forgewrights; chain -> The Deepdelvers; legion -> The Clan Warriors; ledger ->
  The Reckoners; tower -> The Runesmiths; road -> The Underway Wardens; hearth -> The Hearth Clans.
  No Slayer party (forsworn of clan and court).
- **Offices** (affinity unchanged; tiers 2/4/4/4): I High Priest of the Ancestors (temple),
  Master Forgewright (forge); II Keeper of the Reckoning (ledger), Warden of the Gate (legion),
  Keeper of the Grudge-Book (tower), Warden of the Underway (road, up from III); III Overseer of
  the Mines (chain), Master of the Delvings (chain), Master of the Stonecutters (forge), Thane of
  the Muster (legion, up from IV); IV Brewmaster of the Hold (hearth), Steward of the Holdfarms
  (hearth), Keeper of the Lore (tower), Keeper of the Clan Banners (legion). Effects: Dwarf-legal,
  same strength, listed in the spec.
- **Governments**: conclave -> The Council of Elders; priest -> The Ancestors' Writ; forge -> The
  Forge-Throne; legion -> The War-King; convoy -> The Reckoning-Throne (same rules as their slot);
  chain -> **The Iron Law**, rule CHANGED: the three oath moves cost a third less and a broken oath
  costs extra loyalty (not cheap murder/purge). Start government per Dwarf faction in the spec,
  faction keys verified, not recalled.
- **Intrigue moves** (mechanics unchanged, names/blurbs Dwarf): Gift of Gold, Question His Work,
  Whispers in the Halls, **Drive Him to the Slayer Oath** (the murder slot: he leaves for good,
  his party knows), An Insult to the Clan, Cast Out the Clan, Bar Them from the Hall, Recall
  Governors, Swear on the Ancestors, Stand His Patron, Name Him Kinsman, Oath on the Anvil, Skim
  the Tally, Host a Feast, Hold Court in the Great Hall, Walk the Holds, Send an Envoy (tasks:
  control, growth, raw materials, income), Send Diplomats.
- **Grudges inside the court**: Dwarf courts only; a wrong does its usual one-off hit AND writes a
  grudge: -1 loyalty/turn each, never fades, max 4 per party, own line in the loyalty breakdown,
  logged in the Record. Written by: Slayer Oath on their man, Cast Out / Insult / Bar Them aimed at
  them, recalling their governors, early dismissal, a broken oath with them, a refused demand.
  Settled by **Pay the Weregild** (new Bonds move: gold, oldest grudge, small loyalty gain) or by
  appointing their man to an office their party claims. AI Dwarf courts pay weregild when gold
  allows. **Kinship**: "Kin of the Karak" +1 loyalty/turn per party; secession countdown x1.5.
- **Grudges against factions**: per turn, sum CA's grudge points on each met faction's armies and
  settlements (`wh3_dlc25_dwf_grudge_points_enemy_armies` / `_enemy_settlements`); Court tab shows
  "The Book names:" top three. Crossing 500 / 1,000 / 2,000 applies
  `cm:apply_dilemma_diplomatic_bonus(own, them, -1/-2/-3)` ONCE per band, never reversed (CA doc
  entry checked with `check_lua_api.py --explain`: -6..+6, "as if it had come from a dilemma").
  Peace/trade/alliance with a faction above 1,000 writes an internal grudge in the Clan Warriors'
  and Ancestor Priesthood's books. A rise in the faction's own `wh3_dlc25_dwf_grudge_points` is a
  deed for those two parties (replaces CHD deeds Dwarfs lack). Keeper of the Grudge-Book gets a
  grudge-points effect only if CA's effects table has one. CA's 15-turn grudge-cycle score is OUT
  unless the spec finds a readable signal.
- **Skin APPROVED (2026-10-04, "A, and the looks good")** as `dwf_skin_E_offices_v2.png`, drawn by
  `dwf_skin_mockup2.py`. Round 3 was rejected for STRETCHED art: never resize a textured piece
  whole. Ribbons: uniform scale to height, end caps whole, the middle MIRROR-tiled (a straight
  tile shows a seam every repeat - CA's ribbon paper does not tile). Knotwork frame: corners and
  the top ornament (source columns 200..322, corner 48) at native scale, straight runs tiled. In
  the build these plates are BAKED to size as PNGs like the court's other generated plates.
  Title design **A "Lintel"** (dark stone bar, gold double rule, CA's Dwarf-face knot
  `book_of_grudges_legendary_grudges_decor_2` gold-inked at the left; options in
  `dwf_title_options.png`); section headings use **B "Knot rule"**
  (`book_of_grudges_confederation_decor_2` under the words, `decor_units_header` marks).
  **Wording is per faction at runtime, never one karak**: "The Council of (faction)", "The Throne
  of (faction)" over the faction leader's name; the hall heading is generic "THE GREAT HALL" (not
  every Dwarf leader is a king). The selected tab is the gold ribbon; the others blue.
- Earlier round (superseded): `dwf_skin_E_offices.png` - CA's Book of
  Grudges kit (ui2.pack `ui/skins/default/dlc25_book_of_grudges/`, all 68 files extracted to
  `Modding Files/source/iron_court_preview/bog/`): blue ribbon tabs
  (`tab_button_unit_pack_active`), the selected tab gold (`tab_button_legendary_grudges_selected`),
  title and headings on the blue selected ribbon, card frames
  `book_of_grudges_confederation_frame` (red-ink knotwork), the throne on `panel_back` (bronze
  octagon) with `book_of_grudges_unit_pack_decor` (Dwarf face) re-inked gold, CA rune glyphs
  (`rune_N_panel`) down a dark blue runner and on the doors. Script `dwf_skin_mockup.py`. Not
  measured: text contrast on the gold selected tab and on the blue ribbons.

## 4. Do not re-derive

- **The court gate is one function**: `IC.is_chd` (`zzz_derpy_iron_court.lua` ~2271, subculture
  `wh3_dlc23_sc_chd_chaos_dwarfs`), 9 call sites incl. one in the UI file. `IC.runs_court` wraps it.
- **Every content table is one global CHD table**: `IC.ORIGINS` (16 houses -> faction keys plus 8
  non-faction origins), `IC.PARTIES` (crown temple forge chain legion ledger tower road hearth),
  `IC.OFFICES` (tiers 1-4), `IC.GOVS`/`IC.START_GOV`, `IC.LAWS` (labour category is all slaves -
  needs replacing for Dwarfs), `IC.DEEDS` (battle hellforge rite temple slaves raze convoy
  research), `IC.REBEL_POOL`, `IC.BACKGROUNDS`, `IC.NAME_HEADS/TAILS`, `IC.PARTY_TRAITS`,
  `IC.LORD_HISTORY`, `IC.LEGEND_SUBTYPES`, `IC.REBEL_HEROES`, `IC.TEMPLE_BUILDINGS`. Reference
  counts across the four court files: OFFICES 42, ORIGINS 31, PARTIES 30, BACKGROUNDS 15,
  GOVS 14, PLOTS 12, LAWS 11, REBEL_POOL 10.
- **Loc goes through one helper**: `loc(key, fallback)` in `zzz_derpy_iron_court_ui.lua` ~1154;
  keys built by prefix (`derpy_ic_party_name_`, `_origin_name_`, `_law_name_`, `_doctrine_name_`,
  `_bg_name_`, ...) in about ten places - a race segment with a CHD fallback covers them.
- **Dwarf rebel factions exist in vanilla**: `wh_main_dwf_dwarfs_qb1`-`qb4`,
  `wh_main_dwf_dwarfs_seperatists_qb1`-`qb4` (CA's spelling), `wh3_dlc26_dwf_dwarfs_invasion`
  (from `.skilltree_cache/factions.json`). Their flags are unverified.
- **CA's grudges are pooled resources on enemy armies and settlements**:
  `wh3_campaign_grudges.lua` (`book_of_grudges`, culture `wh_main_dwf_dwarfs`, factors
  `wh3_dlc25_dwf_grudge_points*`), plus `wh3_dlc25_grudge_cycles.lua`, `wh_grudges.lua` (Oathgold
  `dwf_oathgold` payloads), `wh3_campaign_grudges_legendary.lua`. A diplomacy-attitude call for a
  pairwise grudge is NOT yet checked against CA's docs - check with `check_lua_api.py --explain`
  before promising it.
- **Backdrop art**: CA's `ui/loading_ui/load_images/campaign_dwarfs1.png` (ui.pack) is landscape and
  works dimmed at 0.42; `Modding Files/reference/Dwarf/` is mostly portrait-shaped and crops badly
  to 1920x1080. Contrast against it is NOT measured yet (`make_ic_backdrop.py` measures per cell).
- The ziggurat is `gen_ic_ui.py` `card_grid()` (~1093) + `ziggurat_boxes()`/`ziggurat_pixels()`
  (~2341) + `check_ziggurat`; the shape is drawn from `CARD_GRID`, so a per-race grid drives it.

## 5. Open (next steps, in order)

1. Brainstorming continues, one question at a time: the Dwarf skin (tabs, heading plates,
   colours from CA's Dwarf UI, backdrop) - PREVIEW first; Dwarf names for parties, offices,
   governments, laws, deeds, houses (lore-backed, flag inferences); the two grudge designs in
   detail; kinship loyalty numbers; which Dwarf factions get a court (houses = karaks/clans).
2. Spec WRITTEN: `docs/superpowers/specs/2026-10-04-iron-court-dwarfs-design.md` (factions, effects and the code map researched by three agents and folded in; Send an Envoy's Dwarf tasks are control, Oathgold, growth, recruitment cost - NOT raw materials). Awaiting the author's review.
3. Plans WRITTEN for all six phases (`docs/superpowers/plans/2026-10-04-iron-court-dwarfs-phase1..6-*.md`, contract `...-CONTRACT.md` with an Amendments section). Cross-checked: DWF defined in phase 2 and used by 1-4, field 19 phase 4, field 20 phase 5, grudge_write signature, `--race dwf` everywhere; fixed phase 6's picture count (at least, 39 vs 33) and gave phase 5 the grudge deed's text. Open decisions for the author: the Book's attitude call one-way or both ways (phase 5 Review Focus 1); phase 3 keeps Fill Empty Seats / pager / action buttons on CA's red plate and widens the title box to 1100 (measured) - shown at its preview stops.
4. Unrelated but still owed: the in-game looks from UI_POLISH section 6; the Workshop page.
