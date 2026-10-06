-- Iron Court: the Dwarf race (plan 2026-10-04 phase 2; spec
-- docs/superpowers/specs/2026-10-04-iron-court-dwarfs-design.md sections 2-4,
-- 7, 8). Loaded after zzz_derpy_iron_court.lua ("." sorts before "_") and
-- before the parties file ("d" before "p").
--
-- SLOTS, NOT NEW SLUGS: a Dwarf party, office, government and law keeps the
-- Chaos Dwarf slot's slug, so every rule the model keys on them holds and only
-- the words and the effects change. Keys carry the "dwf_" infix (IC.key), so no
-- Dwarf row can collide with a Chaos Dwarf one.
--
-- EVERY "DWF.X = {" CLOSES WITH A COLUMN-0 "}": tools/gen_iron_court.py and
-- tools/import_iron_court.py read these tables with DWF\.X = \{(.*?)\n\}.
-- Plain English only: no localisation call anywhere in this file.

if not IC or not IC.register_race then return end

local DWF = {}
DWF.key = "dwf"
DWF.subculture = "wh_main_sc_dwf_dwarfs"
DWF.infix = "dwf_"
-- THE MCT SWITCH THAT TURNS THE RACE ON AND OFF; IC.has_court reads it.
DWF.switch = "dwarf_courts"
DWF.layout = "grid"
-- KINSHIP (spec 2026-10-04 section 5): a Dwarf party is slow to leave its
-- karak. Exactly the two countdowns; plan 2026-10-04 phase 4 ruling 7 names
-- what is not scaled and why.
DWF.tune = {
    secede_turns       = {mul = 1.5},
    plot_provoke_clock = {mul = 1.5},
}
-- THE DWARF SKIN (plan 2026-10-04 phase 3). The panel is its own file pair (the
-- caps are twui margins); the pooled cards' frame, the lit plates and the opener
-- glyph are swapped at runtime. Must match gen_ic_ui.py: DWF_TAB, DWF_FRAME,
-- DWF["title_cap"], DWF["heading_cap"], DWF_OPENER_ICON (import_iron_court checks).
DWF.art = {
    suffix = "_dwf",
    tab = "ui/derpy_ic/dwf_tab_%s_%dx%d.png",
    frame = "ui/derpy_ic/dwf_frame_%dx%d.png",
    lit_ink = "black",
    title_cap = 150,
    heading_cap = 44,
    opener_icon = "ui/skins/default/icon_book_grudges.png",
    -- The panel's ground, which ICUI.gm_sync puts back after the Governors view.
    panel_bg = "ui/derpy_ic/dwf_panel_bg.png",
    -- The Help page's marker: CA's own Dwarf faction-select bullet.
    bullet = "ui/frontend ui/faction_bullets/bullet_dwf_grudges.png",
    -- The government and law cards' pictures: CA's Dwarf technology paintings.
    -- tools/gen_ic_ui.py upscales the governments' to ui/derpy_ic/gov_<slug>_dwf.png;
    -- the law cards draw CA's 72px files as the Chaos Dwarf ones do.
    -- The buttons: CA's own blue colour theme, the same files as its red default
    -- (must match gen_ic_ui.py DWF_THEME). The panel file is built with it; the
    -- files both races share are re-pointed by ICUI.skin_buttons.
    theme = "ui/skins/wh3_main_theme_caledor_sky/",
    -- The Governors view's map (author, 2026-10-05: "change it to dwarf themed"):
    -- CA's Dwarf skin pin, and the name and loyalty plates baked by
    -- tools/gen_ic_ui.py out of that skin's strip at their 1920 boxes (DWF_STRIP).
    gm_pin = "ui/skins/wh_main_dwf_dwarfs/location_pin.png",
    gm_name = "ui/derpy_ic/dwf_strip_180x30.png",
    gm_loyal = "ui/derpy_ic/dwf_strip_113x30.png",
    -- A law card's vote mark: the Hell-Forge heat glow turned blue (DWF_MARK).
    mark = "ui/derpy_ic/dwf_mark.png",
    -- The influence readout on the character panel and the governor note by the
    -- edicts: the seats counter's Dwarf plate (DWF_NOTE).
    note = "ui/derpy_ic/dwf_note.png",
    -- A man's traits and a court's band, as CA marks Dwarf traits and thanes.
    trait_icon = "ui/campaign ui/effect_bundles/trait_dwarf.png",
    band_icon = "ui/campaign ui/effect_bundles/thane.png",
    tech_dir = "ui/campaign ui/technologies/wh_main_dwf_",
    gov_art = {conclave = "thanes_authority", priest = "ancestral_tombs",
               forge = "clans_proud_legacy", legion = "high_kings_authority",
               chain = "oath_stones", convoy = "dwarf_treasuries"},
    law_art = {
        ["labour.measure"] = "call_upon_oaths_of_old", ["labour.lash"] = "deep_resource_extraction",
        ["labour.kept"] = "include_related_families", ["labour.quota"] = "runic_seals_of_quality",
        ["labour.ash"] = "carve_throne_rooms",
        ["tribute.tithe"] = "the_kings_share", ["tribute.roads"] = "underway_trade_caravans",
        ["tribute.tariff"] = "tool_market", ["tribute.mines"] = "storage_vaults",
        ["tribute.charter"] = "hall_of_great_guilds",
        ["worship.rites"] = "sacred_duty", ["worship.fires"] = "valaya_protection",
        ["worship.seats"] = "rune_bearing_relics", ["worship.lore"] = "recite_ancient_grudges",
        ["worship.licence"] = "grungnis_blessing",
        ["war.levy"] = "gather_the_throngs", ["war.grudge"] = "slayers_grudge",
        ["war.hellforge"] = "artillery_entrenchment", ["war.legions"] = "dwarf_shieldwall",
        ["war.gunnery"] = "volley_fire",
    },
}

-- THE GREAT HALL (spec 2.5): rank falls with distance from the throne at
-- column 2, row 0. One cell per office, in DWF.OFFICES order.
DWF.grid = {cols = 5, rows = 4, throne = {2, 0}, cells = {
    {1, 0}, {3, 0},
    {0, 0}, {4, 0}, {1, 1}, {3, 1},
    {0, 1}, {4, 1}, {1, 2}, {3, 2},
    {0, 2}, {4, 2}, {1, 3}, {3, 3},
}}

-- THE HOLDS (spec section 3): the six majors and the eight Immortal Empires
-- minors, every key read out of db.pack factions_tables, plus four places.
-- Clan Helhein, Karak Zorn, the Greybeards' Prospectors and the Spine of Sotek
-- Dwarfs are in the DB but unconfirmed on the map, so they are no origin.
DWF.ORIGINS = {
    {slug = "karaz",     faction = "wh_main_dwf_dwarfs"},
    {slug = "kadrin",    faction = "wh_main_dwf_karak_kadrin"},
    {slug = "angrund",   faction = "wh_main_dwf_karak_izor"},
    {slug = "throng",    faction = "wh3_main_dwf_the_ancestral_throng"},
    {slug = "ironbrow",  faction = "wh2_dlc17_dwf_thorek_ironbrow"},
    {slug = "malakai",   faction = "wh3_dlc25_dwf_malakai"},
    {slug = "barakvarr", faction = "wh_main_dwf_barak_varr"},
    {slug = "zhufbar",   faction = "wh_main_dwf_zhufbar"},
    {slug = "krakadrak", faction = "wh_main_dwf_kraka_drak"},
    {slug = "azorn",     faction = "wh3_main_dwf_karak_azorn"},
    {slug = "norn",      faction = "wh_main_dwf_karak_norn"},
    {slug = "hirn",      faction = "wh_main_dwf_karak_hirn"},
    {slug = "azul",      faction = "wh_main_dwf_karak_azul"},
    {slug = "ziflin",    faction = "wh_main_dwf_karak_ziflin"},
    {slug = "rangers"},
    {slug = "deeps"},
    {slug = "grey"},
    {slug = "black"},
}

DWF.PARTIES = {
    "crown", "temple", "forge", "chain", "legion",
    "ledger", "tower", "road", "hearth",
}

-- THE FOURTEEN SEATS (spec 2.2): affinity unchanged, tiers 2/4/4/4.
DWF.OFFICES = {
    {slug = "priest",    affinity = "temple",    tier = 1},
    {slug = "forge",     affinity = "forge",     tier = 1},

    {slug = "ledger",    affinity = "ledger",    tier = 2},
    {slug = "warden",    affinity = "legion",    tier = 2},
    {slug = "hand",      affinity = "tower",     tier = 2},
    {slug = "roads",     affinity = "road",      tier = 2},

    {slug = "chains",    affinity = "chain",     tier = 3},
    {slug = "pits",      affinity = "chain",     tier = 3},
    {slug = "quarry",    affinity = "forge",     tier = 3},
    {slug = "muster",    affinity = "legion",    tier = 3},

    {slug = "kilns",     affinity = "hearth",    tier = 4},
    {slug = "fields",    affinity = "hearth",    tier = 4},
    {slug = "scribes",   affinity = "tower",     tier = 4},
    {slug = "banners",   affinity = "legion",    tier = 4},
}

DWF.BACKGROUNDS = {
    crown  = {"kinguard", "lineblood", "oathsworn"},
    temple = {"shrinekeeper", "valayan", "tombwarden"},
    forge  = {"smith", "engineer", "foundry"},
    chain  = {"miner", "prospector", "tunneller"},
    legion = {"longbeard", "ironbreaker", "thane"},
    ledger = {"reckoner", "trader", "goldsmith"},
    tower  = {"runesmith", "loremaster", "scribe"},
    road   = {"ranger", "wayfinder", "underwarden"},
    hearth = {"farmer", "brewer", "clanelder"},
}

-- Always "<Head> of <tail>". A head repeats no word of any tail, a tail is at
-- most 18 characters and head + " of " + tail at most 30.
DWF.NAME_HEADS = {
    "Clan", "Brethren", "Kin", "Sons", "Oath-Kin",
    "Keepers", "Line", "Guard",
}

DWF.NAME_TAILS = {
    crown  = {"the Throne"},
    temple = {"the Ancestors", "Valaya's Hearth", "Grungni's Anvil",
              "the Old Shrine", "the Long Memory", "the Stone Altar"},
    forge  = {"the Gromril Anvil", "the Runic Forge", "the Master's Mark",
              "the Cold Hammer", "the Deep Furnace", "the Bright Steel"},
    chain  = {"the Deep Seam", "the Candle Shaft", "the Gold Vein",
              "the Lower Shafts", "the Pick", "the Iron Seam"},
    legion = {"the Shield Wall", "the Unbroken Gate", "the War Banner",
              "the Iron Muster", "the First Rank", "the Bearded Axe"},
    ledger = {"the Reckoning", "the Weighed Coin", "the Sealed Vault",
              "the Tithe", "the Gold Scale", "the Counted Debt"},
    tower  = {"the Rune", "the Grudge-Book", "the Sealed Lore",
              "the Anvil of Doom", "the Master Rune", "the Old Script"},
    road   = {"the Underway", "the Old Road", "the Deep Ways",
              "the Silver Road", "the High Pass", "the Lantern Road"},
    hearth = {"the First Hold", "the Hearthstone", "the Holdfarm",
              "the Brewhouse", "the Long Table", "the Barley Field"},
}

-- THE SAME EIGHT RULES as the Chaos Dwarf traits, keyed alike, in Dwarf words.
DWF.PARTY_TRAITS = {
    {key = "proud", name = "Proud",
     blurb = "No reward ever satisfies them.",
     rule = "-1 a turn",
     n = function() return -1 end},
    {key = "patient", name = "Patient",
     blurb = "They have waited a hundred years before. They can wait again.",
     rule = "+1 a turn",
     n = function() return 1 end},
    {key = "grasping", name = "Grasping",
     blurb = "They demand holds and resent every province denied them.",
     rule = "+1 while they govern a province, -2 when they do not",
     n = function(ctx) return ctx.govs > 0 and 1 or -2 end},
    {key = "zealots", name = "Keepers of the Old Ways",
     blurb = "They serve strength. A weak throne earns only contempt.",
     rule = "+1 while your own party holds half the court, -2 below it",
     n = function(ctx) return ctx.control >= 50 and 1 or -2 end},
    {key = "ambitious", name = "Ambitious",
     blurb = "Each office sharpens their appetite for the next.",
     rule = "0 with no seat, -1 with one, -2 with two or more",
     n = function(ctx) return -math.min(ctx.held, 2) end},
    {key = "dutiful", name = "Dutiful",
     blurb = "They serve where ordered and ask for little.",
     rule = "+2 with no seat, +1 with one",
     n = function(ctx) return ctx.held == 0 and 2 or 1 end},
    {key = "traditionalists", name = "Traditionalists",
     blurb = "Their ancestral office belongs in their own hands.",
     rule = "+1, or -2 while an outsider holds their seat",
     n = function(ctx) return ctx.snubbed and -2 or 1 end},
    {key = "venal", name = "Gold-Hungry",
     blurb = "Gold is the only argument they respect.",
     rule = "+2 while secured, -1 otherwise",
     n = function(ctx) return ctx.sworn > 0 and 2 or -1 end},
}

DWF.LEADER_TRAITS = {
    {key = "thirst", name = "Thirst for the Throne",
     blurb = "He wants the throne, and makes no secret of it."},
    {key = "schemer", name = "Schemer",
     blurb = "Every promise hides another bargain."},
    {key = "brute", name = "Hard-Headed",
     blurb = "He settles disputes with threats and iron."},
    {key = "steady", name = "Steady",
     blurb = "Threats do not move him. Flattery fares no better."},
    {key = "shrewd", name = "Shrewd",
     blurb = "He sees which bargains will pay before others do."},
    {key = "faithful", name = "Ancestor-Sworn",
     blurb = "The Ancestors set the throne where it is. That settles it."},
}

-- THE GOVERNMENTS (spec 2.3): the six slots, each keeping its slot's rule but
-- the Iron Law's. `icon` is a bare name under ui/campaign ui/effect_bundles/,
-- read by gen_iron_court. The Iron Law's broken-oath half is phase 4's.
DWF.GOV_ORDER = {"conclave", "priest", "forge", "legion", "chain", "convoy"}
DWF.GOVS = {
    conclave = {icon = "thane.png",
                parties = {"tower"},
                over = {term_turns = {mul = 0.6}, renew_wait = 1}},
    priest   = {icon = "edict_venerate_the_ancestors.png",
                parties = {"temple"},
                over = {rank_influence = 6, battle_influence = {mul = 0.75}}},
    forge    = {icon = "wh_main_hero_passive_forgefire.png",
                parties = {"forge"},
                over = {governor_income = 8, gov_rank_income_per = 1,
                        influence_trickle = {mul = 0.6}}},
    legion   = {icon = "army_morale.png",
                parties = {"legion"},
                over = {battle_influence = {mul = 1.5}, loyalty_battle_won = 5,
                        influence_trickle = 0}},
    chain    = {icon = "dwf_malakai_oaths_upgrades.png",
                parties = {"chain"},
                over = {plot_oath_cost = {mul = 0.67}, plot_patron_cost = {mul = 0.67},
                        plot_pledge_cost = {mul = 0.67}, oath_broken_loyalty = -10}},
    convoy   = {icon = "edict_high_kings_tribute.png",
                parties = {"road", "ledger"},
                over = {favour_gift_cost = {mul = 0.67}, favour_secure_cost = {mul = 0.67},
                        plot_embezzle_loyalty = 12}},
}

-- WHERE EACH HOLD STARTS (spec section 3; inference, as the Chaos Dwarfs').
DWF.START_GOV = {
    wh_main_dwf_dwarfs = "priest",
    wh_main_dwf_karak_kadrin = "legion",
    wh_main_dwf_karak_izor = "chain",
    wh3_main_dwf_the_ancestral_throng = "priest",
    wh2_dlc17_dwf_thorek_ironbrow = "conclave",
    wh3_dlc25_dwf_malakai = "forge",
    wh_main_dwf_barak_varr = "convoy",
    wh_main_dwf_zhufbar = "forge",
    wh_main_dwf_kraka_drak = "conclave",
    wh3_main_dwf_karak_azorn = "conclave",
    wh_main_dwf_karak_norn = "conclave",
    wh_main_dwf_karak_hirn = "conclave",
    wh_main_dwf_karak_azul = "conclave",
    wh_main_dwf_karak_ziflin = "conclave",
}

-- THE LAWS (spec section 7): the four slot categories (Craft, Tribute,
-- Ancestors, War), each option keeping its slot's pro and con parties. The
-- first of each `order` is its start and has no effects.
DWF.LAW_ORDER = {"labour", "tribute", "worship", "war"}
DWF.LAWS = {
    labour = {icon = "edict_masters_of_steel_and_stone.png",
              order = {"measure", "lash", "kept", "quota", "ash"},
              opts = {
        measure = {icon = "angrund_ancestors.png"},
        lash    = {icon = "resource_gold.png", pro = {"chain"}, con = {"hearth"}},
        kept    = {icon = "growth.png", pro = {"hearth"}, con = {"chain"}},
        quota   = {icon = "oathgold.png", pro = {"forge"}, con = {"hearth"}},
        ash     = {icon = "construction.png", pro = {"legion"}, con = {"ledger"}},
    }},
    tribute = {icon = "edict_collect_tribute.png",
               order = {"tithe", "roads", "tariff", "mines", "charter"},
               opts = {
        tithe   = {icon = "edict_collect_tribute.png"},
        roads   = {icon = "icon_underway_network.png", pro = {"road"}, con = {"crown"}},
        tariff  = {icon = "trade_agreement.png", pro = {"ledger"}, con = {"road"}},
        mines   = {icon = "oathgold_bundle.png", pro = {"forge"}, con = {"road"}},
        charter = {icon = "resource_gemstones.png", pro = {"road"}, con = {"legion"}},
    }},
    worship = {icon = "edict_venerate_the_ancestors.png",
               order = {"rites", "fires", "seats", "lore", "licence"},
               opts = {
        rites   = {icon = "edict_venerate_the_ancestors.png"},
        fires   = {icon = "god_effect_valaya.png", pro = {"temple"}, con = {"tower"}},
        seats   = {icon = "runesmith.png", pro = {"tower"}, con = {"temple"}},
        lore    = {icon = "loremaster.png", pro = {"tower"}, con = {"hearth"}},
        licence = {icon = "god_effect_grungni.png", pro = {"forge"}, con = {"temple"}},
    }},
    war = {icon = "edict_levy_conscripts.png",
           order = {"levy", "grudge", "hellforge", "legions", "gunnery"},
           opts = {
        levy      = {icon = "edict_levy_conscripts.png"},
        grudge    = {icon = "grudges.png", pro = {"legion"}, con = {"ledger"}},
        hellforge = {icon = "artillery.png", pro = {"forge"}, con = {"legion"}},
        legions   = {icon = "waaagh_reward_dwarfs.png", pro = {"legion"}, con = {"forge"}},
        gunnery   = {icon = "engineer.png", pro = {"forge"}, con = {"hearth"}},
    }},
}

-- THE DEEDS (spec section 8). No temple deed: db.pack has no Dwarf temple
-- chain (plan ruling 3). Phase 5 adds the grudge deed.
DWF.DEEDS = {
    battle    = {party = "legion", tune = "deed_battle"},
    research  = {party = "tower",  tune = "deed_research"},
    -- A GRUDGE SETTLED (spec 2026-10-04 section 8), for two parties.
    grudge    = {party = "legion", also = "temple", tune = "deed_grudge"},
}
DWF.TEMPLE_BUILDINGS = {}

-- THE RISINGS (spec section 3). Three dormant quest-battle factions no CA
-- script touches; the four separatist factions permit only a Slayer general
-- (plan ruling 4). gen_iron_court --check holds every key below to the DB.
DWF.REBEL_POOL = {
    "wh_main_dwf_dwarfs_qb2",
    "wh_main_dwf_dwarfs_qb3",
    "wh_main_dwf_dwarfs_qb4",
}

DWF.REBEL_LORD = "wh_main_dwf_lord"
-- CA's own Grudge Too Far crisis forces this row on its invading Dwarfs.
DWF.REBEL_PERSONALITY = "wh3_combi_dwarf_endgame"

DWF.REBEL_GENERALS = {
    ["wh_main_dwf_lord"] = true,
    ["wh_dlc06_dwf_runelord"] = true,
}

-- A DWARF RISING IS A HOLD'S ARMY: the keys and weights are CA's own Grudge Too
-- Far crisis (Dwarf Warriors and Quarrellers added), rolled by role. No Slayers:
-- a Slayer has forsworn his hold.
DWF.REBEL_POOLS = {
    line = {
        {"wh_main_dwf_inf_dwarf_warrior_0", 8},
        {"wh_main_dwf_inf_dwarf_warrior_1", 6},
        {"wh_main_dwf_inf_longbeards", 4},
        {"wh_main_dwf_inf_longbeards_1", 8},
        {"wh_main_dwf_inf_ironbreakers", 8},
        {"wh_main_dwf_inf_hammerers", 8},
    },
    missile = {
        {"wh_main_dwf_inf_thunderers_0", 8},
        {"wh_main_dwf_inf_quarrellers_0", 6},
        {"wh_main_dwf_inf_irondrakes_0", 4},
        {"wh_main_dwf_inf_irondrakes_2", 6},
    },
    screen = {
        {"wh_main_dwf_inf_miners_1", 6},
        {"wh_dlc06_dwf_inf_rangers_0", 2},
        {"wh_dlc06_dwf_inf_rangers_1", 4},
        {"wh_dlc06_dwf_inf_bugmans_rangers_0", 2},
    },
    flyer = {
        {"wh_main_dwf_veh_gyrocopter_0", 1},
        {"wh_main_dwf_veh_gyrocopter_1", 1},
        {"wh_main_dwf_veh_gyrobomber", 1},
    },
    war_machine = {
        {"wh_main_dwf_art_grudge_thrower", 1},
        {"wh_main_dwf_art_cannon", 4},
        {"wh_main_dwf_art_organ_gun", 4},
        {"wh_main_dwf_art_flame_cannon", 2},
    },
}
-- Nineteen slots: seven of line, four missile, three each of screen and guns,
-- two flyers. Interleaved so any prefix of it is a balanced army.
DWF.REBEL_DRAFT = {
    "line", "missile", "line", "screen", "line", "war_machine", "missile",
    "flyer", "line", "screen", "line", "missile", "war_machine", "line",
    "flyer", "line", "missile", "war_machine", "screen",
}

DWF.REBEL_HEROES = {
    ["wh_main_dwf_thane"] = "champion",
    ["wh_main_dwf_master_engineer"] = "engineer",
    ["wh_main_dwf_runesmith"] = "runesmith",
}

-- The lords a leaderless Dwarf party may be given.
DWF.STORE_LORDS = {
    "wh_main_dwf_lord",
    "wh_dlc06_dwf_runelord",
}

DWF.LEGEND_SUBTYPES = {
    ["wh_main_dwf_thorgrim_grudgebearer"] = true,
    ["wh_main_dwf_ungrim_ironfist"] = true,
    ["wh_dlc06_dwf_belegar"] = true,
    ["wh_pro01_dwf_grombrindal"] = true,
    ["wh2_dlc17_dwf_thorek"] = true,
    ["wh3_dlc25_dwf_malakai_makaisson"] = true,
    ["wh3_dlc25_dwf_garagrim_ironfist"] = true,
    ["wh3_dlc25_dwf_lord_mikael_leadstrong"] = true,
    ["wh2_dlc17_dwf_thane_ghost_artifact"] = true,
    ["wh_dlc06_dwf_master_engineer_ghost"] = true,
    ["wh_dlc06_dwf_runesmith_ghost"] = true,
    ["wh_dlc06_dwf_thane_ghost_1"] = true,
    ["wh_dlc06_dwf_thane_ghost_2"] = true,
}

-- THE COMMANDMENT A MILITARY GOVERNOR'S PARTY LIKES, and what its loyalty line
-- calls it (provincial_initiatives_to_subculture_junctions, db.pack).
DWF.MILITARY_DOCTRINE = "wh_main_edict_dwf_masters_of_steel_and_stone"
DWF.MILITARY_DOCTRINE_NAME = "Masters of Steel and Stone"

-- EVERY MOVE IN IC.PLOTS, by key. Phase 4 appends "weregild".
DWF.PLOT_KEYS = {
    "bribe", "discredit", "rumour", "murder", "provoke", "purge",
    "unseat", "recall", "oath", "patron", "kinsman", "pledge",
    "embezzle", "feast", "audience", "circuit", "envoy", "diplomats",
    "weregild",
}

-- WHAT A DWARF PARTY OFFERS THE CROWN: one unit each, in the party's own
-- trade. Every key read out of db.pack main_units 2026-10-04.
DWF.PARTY_TROOPS = {
    temple = "wh_main_dwf_inf_hammerers",
    forge  = "wh_main_dwf_inf_thunderers_0",
    chain  = "wh_main_dwf_inf_miners_0",
    legion = "wh_main_dwf_inf_dwarf_warrior_0",
    ledger = "wh_main_dwf_inf_quarrellers_0",
    tower  = "wh_main_dwf_inf_ironbreakers",
    road   = "wh_dlc06_dwf_inf_rangers_0",
    hearth = "wh_main_dwf_inf_longbeards",
}
-- A confederated house's slug is not one of the eight.
DWF.TROOPS_DEFAULT = "wh_main_dwf_inf_dwarf_warrior_0"

-- THE ENVOY'S FOUR (spec section 4): Chaos Dwarf armaments, raw materials and
-- labour do nothing for Dwarfs. The value is IC.TUNE[knob]; gen_iron_court
-- reads both out of this table. `icon` is the bundle's.
DWF.ENVOY_TASKS = {
    {code = "ctl", name = "Control", knob = "envoy_ctl", fmt = "+%d control",
     bundle = "derpy_ic_envoy_dwf_ctl", icon = "morale.png"},
    {code = "oath", name = "Oathgold", knob = "envoy_oath", fmt = "+%d%% Oathgold from buildings",
     bundle = "derpy_ic_envoy_dwf_oath", icon = "oathgold.png"},
    {code = "grow", name = "Growth", knob = "envoy_grow", fmt = "+%d growth",
     bundle = "derpy_ic_envoy_dwf_grow", icon = "growth.png"},
    {code = "rec", name = "Recruitment", knob = "envoy_rec", fmt = "-%d%% recruitment cost",
     bundle = "derpy_ic_envoy_dwf_rec", icon = "edict_state_troop_levy.png"},
}

-- THE MOVES IN DWARF WORDS (spec 2.4): mechanics unchanged, so every number is
-- the model's own knob, read at load as IC.PLOTS reads it.
-- A move's icon, where the shared one is Chaos Dwarf (or Cathay) art: CA's
-- Dwarf technology paintings, as the law cards use.
DWF.PLOT_TEXT = {
    bribe = {name = "Gift of Gold",
     blurb = "Gold and good ale buy favour.",
     effect = string.format(
         "+%d influence for him. +%d party loyalty. Stops their secession countdown.",
         IC.TUNE.plot_bribe_standing,
         IC.TUNE.plot_bribe_loyalty)},
    discredit = {name = "Question His Work",
     blurb = "His work is found wanting.",
     effect = string.format(
         "-%d influence for him. -%d influence from his party.",
         IC.TUNE.plot_discredit_standing,
         IC.TUNE.plot_discredit_weight)},
    rumour = {name = "Hall Whispers",
     blurb = "Talk in the halls ruins one name.",
     effect = string.format(
         "-%d influence for him. His party is unaffected.",
         IC.TUNE.plot_rumour_damage)},
    murder = {name = "The Slayer Oath",
     icon = "ui/campaign ui/technologies/wh_main_dwf_slayers_onslaught.png",
     blurb = "His party will know.",
     effect = string.format(
         "He takes the Slayer Oath and leaves the court for good. -%d loyalty from his party.",
         IC.TUNE.plot_murder_loyalty - IC.TUNE.loyalty_member_died)},
    provoke = {name = "An Insult to the Clan",
     icon = "ui/campaign ui/technologies/wh_main_dwf_tales_of_many_wars.png",
     blurb = "An insult they cannot ignore.",
     effect = string.format(
         "-%d loyalty. Sets their secession countdown to %d turns.",
         IC.TUNE.plot_provoke_loyalty,
         IC.TUNE.plot_provoke_clock),
     effect_no_secession = string.format(
         "-%d loyalty. With secession switched off, no countdown starts.",
         IC.TUNE.plot_provoke_loyalty)},
    purge = {name = "Cast Out the Clan",
     icon = "ui/campaign ui/technologies/wh_main_dwf_iron_price.png",
     blurb = "The court watches.",
     effect = string.format(
         "Removes the party. -%d loyalty to all others. Failure: another -%d to the target.",
         IC.TUNE.plot_purge_witness,
         IC.TUNE.plot_purge_backfire)},
    unseat = {name = "Bar the Doors",
     blurb = "They keep only their name.",
     effect = string.format(
         "Empties every office they hold. -%d loyalty.",
         IC.TUNE.plot_unseat_loyalty)},
    recall = {name = "Recall Governors",
     blurb = "The throne takes back its provinces.",
     effect = string.format(
         "Recalls every governor from their party. -%d loyalty.",
         IC.TUNE.plot_recall_loyalty)},
    oath = {name = "Ancestor Oath",
     icon = "ui/campaign ui/technologies/wh_main_dwf_oaths_of_loyalty.png",
     blurb = "Two names before the Ancestors.",
     effect = string.format(
         "+%d loyalty each turn while both men live. Requires %d loyalty.",
         IC.TUNE.plot_oath_loyalty,
         IC.TUNE.plot_oath_min_loyalty)},
    patron = {name = "Stand His Patron",
     blurb = "He will remember.",
     effect = string.format(
         "+%d influence for him. +%d loyalty for his party.",
         IC.TUNE.plot_patron_standing,
         IC.TUNE.plot_patron_loyalty)},
    kinsman = {name = "Name Him Kinsman",
     icon = "ui/campaign ui/technologies/wh_main_dwf_retainers_vows.png",
     blurb = "His party loses influence.",
     effect = string.format(
         "Moves up to %d influence to your own party. Requires %d loyalty.",
         IC.TUNE.plot_kinsman_weight,
         IC.TUNE.plot_kinsman_min_loyalty)},
    pledge = {name = "Oath on the Anvil",
     blurb = "Anvil-sworn.",
     effect = string.format(
         "+%d loyalty. Stops their secession countdown. Costs your own party %d influence.",
         IC.TUNE.plot_pledge_loyalty,
         IC.TUNE.plot_pledge_weight)},
    embezzle = {name = "Skim the Tally",
     blurb = "The court will still smell theft.",
     effect = string.format(
         "+%d gold. -%d loyalty across the whole court.",
         IC.TUNE.plot_embezzle_gold,
         IC.TUNE.plot_embezzle_loyalty)},
    feast = {name = "Host a Feast",
     blurb = "The court learns his name.",
     effect = string.format(
         "+%d influence to the man you send. -%d loyalty across the court.",
         IC.TUNE.plot_feast_standing,
         IC.TUNE.plot_feast_loyalty)},
    audience = {name = "Hold Court",
     blurb = "A day of ale and grievances.",
     effect = string.format(
         "+%d loyalty to every party in the court.",
         IC.TUNE.plot_audience_loyalty)},
    circuit = {name = "Walk the Holds",
     icon = "ui/campaign ui/technologies/wh_main_dwf_marching_songs.png",
     blurb = "A ledger and an armed escort.",
     effect = string.format(
         "+%d control in every province you hold.",
         IC.TUNE.plot_circuit_prov)},
    envoy = {name = "Send an Envoy",
     icon = "ui/campaign ui/technologies/wh_main_dwf_dwarven_emissaries.png",
     blurb = "He sees it done.",
     effect = string.format(
         "One of your provinces, for %d turns: control, Oathgold, growth or "
         .. "recruitment cost.", IC.TUNE.mission_turns)},
    diplomats = {name = "Send Diplomats",
     icon = "ui/campaign ui/technologies/wh_main_dwf_dwarven_diplomats.png",
     blurb = "Gifts and a long table.",
     effect = string.format(
         "Improves relations with a faction you have met. Each faction once per %d turns.",
         IC.TUNE.diplomats_rest)},
}

DWF.FAVOUR_TEXT = {
    gift = {name = "Send a Gift",
     blurb = "Send gold, good ale and fine work. A small payment buys a little patience."},
    secure = {name = "Secure Loyalty",
     blurb = "Take oaths before the Ancestors and bind the party by them. This delays rebellion but cannot save loyalty at zero."},
}

-- THE EVENTS THE DWARFS WORD THEIR OWN WAY: their loc carries the infix
-- (IC.event_stem); the record and its index are shared.
DWF.EVENT_LOC = {
    gov_intro = true,
    realm_secede = true,
}

-- THE HELP LINES THAT NAME CHAOS DWARF THINGS, in Dwarf words (phase 3, Task 13):
-- keyed by the shared line exactly as ICUI.HELP holds it; false drops the line.
-- The harness fails a key no shared line still reads. The deeds line names only
-- battle and research, the Dwarfs' two deeds - phase 5's grudge deed rewrites it.
DWF.HELP_SWAP = {
    ["{@confed}A Chaos Dwarf house you confederate joins your court as a party of its own, keeping roughly the loyalty it had."] =
        "{@confed}A Dwarf hold you confederate joins your court as a party of its own, keeping roughly the loyalty it had.",
    ["{@crown}Your capital's province never leaves. {@circuit}Ride the Circuit, on the Intrigue tab, raises every province's loyalty at once."] =
        "{@crown}Your capital's province never leaves. {@circuit}Walk the Holds, on the Intrigue tab, raises every province's loyalty at once.",
    ["{@bullet}A court that no rival leads leans slowly toward the Conclave. While the Crown leads, nothing moves."] =
        "{@bullet}A court that no rival leads leans slowly toward the Council of Elders. While the Crown leads, nothing moves.",
    ["{@party}What you do moves your parties. Victories raise the Legion and the Hell-Forge the Forge."] =
        "{@party}What you do moves your parties. Victories raise the warriors' party, and research the runesmiths'.",
    ["{@bullet}The Tower's rites and temples raise the Priesthood, slaves and razing the Chain."] = false,
    ["{@bullet}Convoys raise the Road, and research the Tower."] = false,
    ["{@bullet}Moves on a man: {@bribe}bribe him, {@discredit}discredit him, {@rumour}spread rumours, or {@murder}arrange an accident at the forge."] =
        "{@bullet}Moves on a man: {@bribe}a gift of gold, {@discredit}question his work, {@rumour}whispers in the halls, or {@murder}drive him to the Slayer Oath.",
    ["{@bullet}Moves on a party: {@provoke}provoke it, or {@purge}purge it. Moves on its posts: {@unseat}strike its seats, or {@recall}recall its governors."] =
        "{@bullet}Moves on a party: {@provoke}insult it, or {@purge}cast it out. Moves on its posts: {@unseat}bar it from the hall, or {@recall}recall its governors.",
    ["{@bullet}Bonds: {@oath}swear a blood-oath, {@patron}stand as a man's patron, {@kinsman}name him kinsman, or {@pledge}pledge the forge to his party."] =
        "{@bullet}Bonds: {@oath}swear on the ancestors, {@patron}stand as a man's patron, {@kinsman}name him kinsman, or {@pledge}swear on the anvil to his party.",
    ["{@bullet}Errands: {@embezzle}embezzle from the vaults, {@feast}hold a feast, {@audience}hold court, or {@circuit}ride the circuit of your provinces."] =
        "{@bullet}Errands: {@embezzle}skim the tally, {@feast}host a feast, {@audience}hold court in the great hall, or {@circuit}walk the holds.",
    ["{@rebel}The rebels declare war on you at once and march like an invading host. Every Chaos Dwarf court distrusts them."] =
        "{@rebel}The rebels declare war on you at once and march like an invading host. Every Dwarf hold distrusts them.",
    ["{@bullet}A bribe, the Pledge of the Forge, or another party's offer of calm stops a countdown. A purge ends the party, if it works."] =
        "{@bullet}A Gift of Gold, an Oath on the Anvil, or another party's offer of calm stops a countdown. Casting it out ends the party, if it works.",
}

-- REGISTERED LAST, once: IC.build_race derives TIERS, TIER_SEATS, PARTY_OF_BG
-- and MAX_SEATS from the tables above, and register_race appends "dwf" to
-- IC.RACE_ORDER itself (phase 1) - never append it by hand.
IC.register_race(DWF)
