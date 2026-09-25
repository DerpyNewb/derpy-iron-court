# The Iron Court

A campaign mod for **Total War: WARHAMMER III** that gives the Chaos Dwarfs a court. Your
lords and heroes belong to parties: the Crown, which is yours, and two to four rival parties
rolled at the start of each campaign. You seat men in fourteen offices and make them
overseers of provinces, and every seat you hand out moves a party's share of the court and
its loyalty. Hold enough of the court and the whole empire runs better. Let a party's
loyalty run out and it secedes, taking provinces and lords with it and going to war under
its own name.

It is script-driven. It overrides no CA file, and every DB row it adds has its own key,
with one exception: four of CA's `factions` rows, the dormant Chaos Dwarf rebel factions a
secession wakes, are overridden to give each its own banner. Only the banner column
changes, but a mod that edits those same four rows will conflict with this one.

**Status:** playable, and tested live in Chaos Dwarf campaigns. It is not on the Steam
Workshop yet. It needs no other mod and has no MCT settings. Only Chaos Dwarf factions have
a court.

## The parties

Each rival party draws its men from one walk of Chaos Dwarf life, claims certain offices,
and improves any province its man governs.

| Party | Claims | Its overseer's province gets |
|---|---|---|
| The Crown | nothing: it is you | public order |
| The Priesthood | High Priest of Hashut | growth |
| The Forge | Grand Overseer of the Forge, Master of the Quarries | armaments |
| The Chain | Keeper of the Chains, Master of the Pits | labour taken after battles |
| The Legion | Warden of the Marches, Warden of the Muster, Keeper of the Banners | lower upkeep |
| The Ledger | Keeper of the Black Ledger | income |
| The Tower | Hand of the Tower, Master of the Scribes | research rate |
| The Road | Warden of the Caravan Roads | movement range |
| The Hearth | Keeper of the Kilns, Steward of the Ash Fields | replenishment |

A rolled party takes a Chaos Dwarf name such as *Covenant of the Iron Oath*. It gets two
traits for life and a leader, whose own trait is its third. A man belongs to a party by his
background, a trait on his character; a man whose party is not in this court sits with the
Crown. A Chaos Dwarf faction that confederates into yours brings its men in as a party of
their own.

## How it plays

- **Influence.** Every man has influence of his own. He earns it by winning battles (8 to
  50, by how well), taking settlements, gaining ranks, holding an office or a province, and
  a small amount each turn while he is not leading an army. Your moves at court are paid
  for out of it.
- **The court's share.** A party's share of the court comes from the offices and provinces
  its men hold and the influence they carry. Each man is Cautious, Steady or Ambitious,
  which scales what his influence adds.
- **Five bands for the Crown.** Your own share sets a faction-wide effect: An Iron Grip
  (75% and up), Master of the Court (60%), In Command (40%), A Contested Court (10%) and The
  Court Is Not Yours (below 10%). The top bands add public order, income, growth and
  cheaper upkeep; the bottom ones take them away.
- **Fourteen offices in four tiers.** Each gives the faction a bonus, and an empty one costs
  a little. A seat asks for rank and influence, is held for a five-turn term, and is lost if
  its holder's influence falls below the bar. Giving a party's claimed office to an outsider
  angers the party every turn he sits there. An empty lowest-tier seat can be filled by
  hiring a new hero straight into it.
- **Overseers.** Any of your men can govern a province. A lord leading an army governs only
  while he stands in it. Overseers gain experience every turn, and a party whose overseer
  runs a province under the Military Doctrine commandment gains loyalty.
- **Loyalty.** Each party's loyalty, 0 to 100, moves every turn with its seats, its
  provinces, its traits and its leader's. Battles its men win raise it; a member's death, a
  dismissal and a snub lower it. The loyalty tooltip lists every term.
- **Secession.** A rival holding at least a quarter of the court with loyalty at 20 or less
  starts a five-turn countdown, with a warning card at the start and again three turns
  out. At zero it goes at once. It takes provinces (never your capital), up to three of its
  lords as generals and two of its heroes, and goes to war with you under its own name and
  one of four rebel banners. A party with no men and no province dissolves instead.
- **Pressure.** While the Crown holds under 10% of the court, the strongest rival may be
  pushed onto that countdown whatever its loyalty. If the Crown's own loyalty falls to 25,
  your own men split off into a new party after a three-turn warning.
- **Intrigue.** Fourteen moves in four columns: Against a Man, Against a House, Bonds and
  Errands. Bribes, rumours, a forge accident, a blood-oath, a feast of ash and more. Each is
  paid from the acting man's influence and each can fail; a failed move against a party
  costs loyalty with it.
- **The party bar.** Choose a rival's card and four buttons act on that party: Provoke and
  Purge the House (moves aimed at its leader), Send a Gift (600 gold, +2 loyalty) and Secure
  Loyalty (2,500 gold, no countdown for five turns). A button the court will not allow is
  red and says why.
- **The rivals act on their own.** In your court, one party does one thing a turn. It
  schemes against you (rumours and discredit, then unseating your men or recalling your
  overseers, then murder; the serious moves are warned a turn ahead), feuds with another
  party, demands an office or a province for one of its men as a five-turn mission, or
  offers gold, backing, calm or troops when it is content.
- **Petitions.** The live demand and every offer, each with Accept and Refuse. Accepting a
  demand seats the man in the post he asked for.
- **The AI has courts too.** Every Chaos Dwarf faction runs the same offices, overseers,
  loyalty and secession, so an AI Chaos Dwarf empire can split into a war on the map. The
  scheming rivals, the overseers' experience, the pressure and the event cards are the
  player's only.

The panel opens from a round button on the top resource strip, beside the buttons of The
Great Guilds and the Zharr Exchange when those mods are present. It has six tabs: Court,
Offices, Governors, Intrigue, Petitions and Record. It is sized to the screen, from 1600x900
up to 2560x1440; below 1920 wide it uses a compact layout one font size down. A man's exact
influence also shows beside his rank on the character details panel. Event cards raised
while the panel is open wait until it closes.

**Multiplayer:** not supported. Panel actions change the campaign on the machine that
clicks and are not sent through the multiplayer transport, so a two-player campaign would
fall out of sync. It has not been tried.

## Installing

1. Put `derpy_iron_court.pack` in `Total War WARHAMMER III/data/`.
2. Enable it in the launcher or in the WH3 Mod Manager.

It can be added to a campaign already in progress: your court is rolled and your men are
given backgrounds the first time the save loads. AI Chaos Dwarf courts roll on their next
turn.

## This repository

The repo holds the mod's source and the tools that generate, check and pack it. The layout
mirrors the in-pack paths, so the tools run from the repo root unchanged.

| Path | What it is |
|---|---|
| `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court.lua` | the model: parties, influence, offices, overseers, loyalty, intrigue, secession, save state |
| `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_parties.lua` | the rival parties' own acts, demands and offers |
| `Modding Files/pack/script/campaign/mod/zzz_derpy_iron_court_ui.lua` | the panel, the HUD opener and the influence plate |
| `Modding Files/pack/ui/campaign ui/` | the twelve `derpy_ic_*.twui.xml` layouts (generated): seven layouts, five of them with a `_compact` copy |
| `Modding Files/source/iron_court/` | the DB rows and loc as TSV (generated), except the `factions` override (see below) |
| `tools/` | generators, checks, the Lua test harness, the mutation runner, the preview renderer, the art tools and the packer |
| `docs/design/` | design specs, and the gap analysis against Rome II's politics |
| `docs/plans/` | the implementation plans the later features were built from |
| `docs/history/` | dated handoff notes: what was built, measured and fixed, and why |

**[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)** covers how the mod works inside, the build
pipeline, every check, and the engine behaviour that shaped the code.
**[CHANGELOG.md](CHANGELOG.md)** lists the builds.

## Building from source

You need:

- Python 3 with Pillow and zstandard
- Lua 5.1.5 (the game's version). The packing gate calls it at
  `C:\Program Files (x86)\Lua\5.1\`
- [RPFM](https://github.com/Frodo45127/rpfm) with its MCP server running, for the vanilla
  table dump and for packing
- A WH3 install. Several tools hard-code it as
  `F:\SteamLibrary\steamapps\common\Total War WARHAMMER III`; edit that constant to match yours
- Microsoft's `texconv.exe` in `texconv/`, for the rebel banners' battle flag

```sh
lua tools/_iron_court_harness.lua          # model, parties and panel against a stubbed campaign
py tools/fetch_vanilla_tables.py agent_subtypes agents campaign_group_member_criteria_values campaign_payload_ui_details character_skill_node_sets character_traits effect_bundles_to_effects_junctions effects event_feed_message_events faction_agent_permitted_subtypes factions main_units missions
py tools/gen_iron_court.py --check         # DB rows, loc and every design rule
py tools/gen_iron_court.py --write         # regenerate the TSVs
py tools/gen_ic_ui.py --write              # regenerate the layouts and the generated pictures
py tools/import_iron_court.py              # the packing gate: refuses on any drift
py tools/deploy_iron_court.py --no-copy    # pack, save and verify the saved pack
py tools/deploy_iron_court.py              # the same, then copy into data/ (game closed)
```

The harness needs nothing else and passes from a fresh copy of this repo. Everything after
it needs the files below.

**No art is included.** Every picture ships inside the `.pack` only:

- The panel backdrop is cut from a still of the Chaos Dwarf victory movie.
  `tools/make_ic_backdrop.py --write` rebuilds it from a 1920x1140 still you save as
  `Modding Files/reference/morgan-ketelaar-jarass-wh3-winmovie-shot04.jpg`.
- The party flags are drawn inside CA's own flag frame, and `gen_ic_ui.py` reads that frame
  from `Modding Files/source/ic_frame/flag_frame_128.png`, a 128px copy of CA's frame with
  its field painted white. The plates, dial pictures and silhouette beside them are drawn
  from numbers by the same run.
- The four rebel banners put new devices on CA's Chaos Dwarf rebel banner.
  `tools/make_ic_rebel_flags.py --write` reads CA's banner out of your installed game itself,
  and takes the devices from `rising_01.png` to `rising_04.png` in
  `Modding Files/source/ic_crests/`.

Without them the scripts still run, but `gen_ic_ui.py` stops at the missing flag frame,
its `--check` reports every missing picture, and the deploy refuses to pack.

**CA's own data is not included either.** `factions.tsv` and `_donor_factions.tsv` are four
of CA's `factions` rows, so they are left out. Open the game's `db.pack` in RPFM, export
`db/factions_tables/data__` to TSV, and keep the header, the `#factions_tables;6;` line and
the rows for `wh3_dlc23_chd_chaos_dwarfs_qb1`, `_qb2`, `_qb3` and
`wh3_dlc25_chd_chaos_dwarfs_invasion`. Save that as
`Modding Files/source/iron_court/_donor_factions.tsv`; `gen_iron_court.py --write` then
writes `factions.tsv` from it, changing only `flags_path`. Until the donor exists,
`gen_iron_court.py` refuses to check or write. Also not included: `.skilltree_cache/` (the
vanilla table dump that `fetch_vanilla_tables.py` builds from your install), CA's scripting
reference under `Modding Files/reference/ca_script_docs_wh3/` (the packing gate refuses
without it), and `TWUI_Studio/src`, a third-party, non-commercial tool that
`preview_iron_court.py` drives.

## Licence and legal

The code and documentation in this repository are released under the
[MIT License](LICENSE).

This is an unofficial, fan-made mod. It is not made, endorsed or supported by Games
Workshop, Creative Assembly or SEGA.

- **No game files or assets are included.** The repository contains no art, models,
  sounds or game data files from Total War: WARHAMMER III. The mod references the game's own
  data by key at runtime, and you need your own copy of the game to use or build it.
- Warhammer, the Chaos Dwarfs, Hashut and the names, places and characters of the Warhammer
  world are trademarks and/or copyright of Games Workshop Limited. Total War and Total War:
  WARHAMMER are trademarks and/or copyright of The Creative Assembly Limited and SEGA.
  All are used here for identification only.
- The MIT License covers only the original work in this repository. It grants no rights
  in any Games Workshop, Creative Assembly or SEGA property.
